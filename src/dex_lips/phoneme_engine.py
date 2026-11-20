"""Second, independent automatic cue engine: wav2vec2 phoneme CTC recognizer.

Model: facebook/wav2vec2-lv-60-espeak-cv-ft (Apache-2.0, pinned revision below).
It recognizes IPA phonemes directly from the audio waveform (no transcript),
which are mapped to the nine Rhubarb mouth shapes with ``visemes.PHONEME_TO_SHAPE``.

Honesty rules (same as the Rhubarb adapter):
- No implicit network access. Model weights are loaded from the local Hugging
  Face cache unless the caller passes ``allow_download=True`` (or sets
  ``DEX_LIPS_ALLOW_MODEL_DOWNLOAD=1``).
- If torch/transformers/the weights are missing, analysis raises ProofError
  (BLOCKED) instead of inventing cues.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import wave

from .proof_render import ProofError, duration, load_cues, media_probe, need_tools
from .visemes import phoneme_to_shape

MODEL_ID = 'facebook/wav2vec2-lv-60-espeak-cv-ft'
MODEL_REVISION = 'ae45363bf3413b374fecd9dc8bc1df0e24c3b7f4'
MODEL_LICENSE = 'apache-2.0'
FRAME_SEC = 0.02  # wav2vec2 conv stack stride: 320 samples at 16 kHz
ENGINE_NAME = 'wav2vec2-phoneme'

_MODEL_CACHE: dict[tuple[str, str], tuple[object, object]] = {}


def _download_allowed(allow_download: bool) -> bool:
    return allow_download or os.environ.get('DEX_LIPS_ALLOW_MODEL_DOWNLOAD') == '1'


def phoneme_engine_status(model_id: str = MODEL_ID, revision: str = MODEL_REVISION,
                          allow_download: bool = False) -> tuple[bool, str]:
    """Return (available, reason) without loading the network or weights."""
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        from huggingface_hub import try_to_load_from_cache
    except ImportError as exc:
        return False, f'Python packages missing ({exc.name}); install requirements-engines.txt'
    if _download_allowed(allow_download):
        return True, 'model may be downloaded on first use (explicitly allowed)'
    for name in ('config.json', 'pytorch_model.bin', 'vocab.json'):
        hit = try_to_load_from_cache(model_id, name, revision=revision)
        if not isinstance(hit, str):
            return False, (f'model weights for {model_id}@{revision[:8]} are not in the local cache; '
                           'run `python -m dex_lips.engines --fetch-model` once (explicit download)')
    return True, 'model found in local cache'


def phoneme_engine_available(**kwargs) -> bool:
    return phoneme_engine_status(**kwargs)[0]


def _load(model_id: str, revision: str, allow_download: bool):
    key = (model_id, revision)
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]
    ok, reason = phoneme_engine_status(model_id, revision, allow_download)
    if not ok:
        raise ProofError(f'Phoneme engine BLOCKED: {reason}')
    local_only = not _download_allowed(allow_download)
    if local_only:
        os.environ['HF_HUB_OFFLINE'] = '1'  # guarantee no implicit network access
    import torch
    from transformers import Wav2Vec2ForCTC, Wav2Vec2PhonemeCTCTokenizer
    torch.manual_seed(0)
    try:
        tokenizer = Wav2Vec2PhonemeCTCTokenizer.from_pretrained(
            model_id, revision=revision, local_files_only=local_only, do_phonemize=False)
        model = Wav2Vec2ForCTC.from_pretrained(model_id, revision=revision,
                                               local_files_only=local_only).eval()
    except OSError as exc:
        raise ProofError(f'Phoneme engine BLOCKED: could not load {model_id}: {exc}') from exc
    _MODEL_CACHE[key] = (tokenizer, model)
    return tokenizer, model


def _read_wav16k(path: Path):
    import numpy as np
    with wave.open(str(path)) as w:
        if w.getframerate() != 16000 or w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ProofError('Internal error: expected 16 kHz mono PCM')
        data = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype('float32') / 32768.0
    return data


def recognize_phonemes(samples, *, model_id: str = MODEL_ID, revision: str = MODEL_REVISION,
                       allow_download: bool = False) -> list[dict]:
    """Greedy CTC decode with frame timing: [{'phoneme','start_frame','end_frame','prob'}]."""
    import numpy as np
    import torch
    tokenizer, model = _load(model_id, revision, allow_download)
    x = (samples - samples.mean()) / (samples.std() + 1e-7)  # processor's zero-mean/unit-var
    with torch.inference_mode():
        logits = model(torch.from_numpy(x.astype('float32'))[None]).logits[0]
    probs = torch.softmax(logits, dim=-1)
    best = probs.argmax(-1).tolist()
    blank = tokenizer.pad_token_id
    events: list[dict] = []
    prev = None
    for i, tok in enumerate(best):
        if tok != prev and tok != blank:
            events.append({'phoneme': tokenizer.convert_ids_to_tokens(tok), 'start_frame': i,
                           'end_frame': i, 'prob': float(probs[i, tok])})
        elif tok == prev and tok != blank and events:
            events[-1]['end_frame'] = i
        prev = tok
    return events


def _frame_energy_db(samples, frames: int):
    import numpy as np
    hop = 320
    out = []
    for i in range(frames):
        seg = samples[i * hop:(i + 1) * hop]
        rms = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0
        out.append(20 * math.log10(rms + 1e-9))
    return out


def phonemes_to_cues(events: list[dict], energy_db: list[float], total_sec: float, *,
                     min_cue: float = 0.04, silence_gap: float = 0.20) -> list[dict]:
    """Deterministically convert timed phoneme spikes into Rhubarb-style cues."""
    if not energy_db:
        return [{'start': 0.0, 'end': round(total_sec, 2), 'value': 'X'}]
    peak = max(energy_db)
    floor = sorted(energy_db)[len(energy_db) // 10]
    threshold = max(floor + 8.0, peak - 38.0)
    silent = [e < threshold for e in energy_db]
    centres = [(ev['start_frame'] + ev['end_frame'] + 1) / 2 * FRAME_SEC for ev in events]
    segs: list[tuple[float, float, str]] = []
    lead, tail = 0.06, 0.08
    for i, ev in enumerate(events):
        c = centres[i]
        start = c - lead if i == 0 else None
        end = c + tail if i == len(events) - 1 else None
        if i > 0:
            gap = c - centres[i - 1]
            f0, f1 = int(centres[i - 1] / FRAME_SEC), int(c / FRAME_SEC)
            quiet = sum(silent[f0:f1]) / max(1, f1 - f0)
            if gap > silence_gap and quiet > 0.5:
                start = c - lead
            else:
                start = (centres[i - 1] + c) / 2
        if i < len(events) - 1:
            gap = centres[i + 1] - c
            f0, f1 = int(c / FRAME_SEC), int(centres[i + 1] / FRAME_SEC)
            quiet = sum(silent[f0:f1]) / max(1, f1 - f0)
            end = c + tail if (gap > silence_gap and quiet > 0.5) else (c + centres[i + 1]) / 2
        segs.append((max(0.0, start), min(total_sec, end), phoneme_to_shape(ev['phoneme'])))
    # Fill holes with silence X, round to centiseconds.
    cues: list[dict] = []
    t = 0.0
    for start, end, shape in segs:
        start, end = round(start, 2), round(end, 2)
        if start > t + 1e-9:
            cues.append({'start': round(t, 2), 'end': start, 'value': 'X'})
        start = max(start, t)
        if end > start:
            cues.append({'start': start, 'end': end, 'value': shape})
            t = end
    total = round(total_sec, 2)
    if t < total:
        cues.append({'start': round(t, 2), 'end': total, 'value': 'X'})
    # Absorb too-short cues into the previous cue, then merge equal neighbours.
    merged: list[dict] = []
    for cue in cues:
        if merged and (cue['value'] == merged[-1]['value'] or cue['end'] - cue['start'] < min_cue - 1e-9):
            merged[-1]['end'] = cue['end']
        else:
            merged.append(dict(cue))
    return merged


def analyze(audio: Path, output: Path, *, model_id: str = MODEL_ID, revision: str = MODEL_REVISION,
            allow_download: bool = False) -> dict:
    """Analyze real audio with the phoneme recognizer and write validated cue JSON."""
    audio, output = Path(audio), Path(output)
    if not audio.is_file():
        raise ProofError('Speech audio file is missing')
    if output.exists():
        raise ProofError('Phoneme-engine output path already exists; refusing overwrite')
    if audio.stat().st_size > 40 * 1024 * 1024:
        raise ProofError('Speech audio exceeds the 40 MiB limit')
    ok, reason = phoneme_engine_status(model_id, revision, allow_download)
    if not ok:
        raise ProofError(f'Phoneme engine BLOCKED: {reason}')
    need_tools()
    probe = media_probe(audio)
    if not probe.get('audio'):
        raise ProofError('Input does not contain an audio track')
    seconds = duration(probe)
    if not .15 <= seconds <= 30.:
        raise ProofError('Audio for the phoneme engine must be 0.15 to 30 seconds')
    with tempfile.TemporaryDirectory(prefix='dex_lips_w2v_') as working:
        wav = Path(working) / 'speech.wav'
        p = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(audio), '-map', '0:a:0',
                            '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(wav)],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=35, check=False)
        if p.returncode or not wav.is_file():
            raise ProofError('FFmpeg audio normalization failed: ' + p.stderr.decode(errors='replace')[-300:])
        samples = _read_wav16k(wav)
        events = recognize_phonemes(samples, model_id=model_id, revision=revision,
                                    allow_download=allow_download)
        frames = max(1, len(samples) // 320)
        cues = phonemes_to_cues(events, _frame_energy_db(samples, frames), seconds)
        doc = {'metadata': {'duration': round(seconds, 3), 'analysis': ENGINE_NAME,
                            'model': model_id, 'revision': revision, 'license': MODEL_LICENSE,
                            'phonemes': ' '.join(e['phoneme'] for e in events),
                            'cue_count': len(cues)},
               'mouthCues': cues}
        check = Path(working) / 'check.json'
        check.write_text(json.dumps(doc), encoding='utf-8')
        load_cues(check, seconds)  # validate exactly what we will publish
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(doc, indent=2), encoding='utf-8')
    return {'analysis': 'wav2vec2 phoneme recognizer from actual audio', 'cue_count': len(cues),
            'phoneme_count': len(events), 'output': str(output), 'model': model_id}
