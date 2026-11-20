"""AID ONLY: draft a reference cue track for manual review.

This is how the first draft of each eval/reference/*.json was produced before
manual review. It is NOT part of scoring and NOT ground truth.

1. Word boundaries: CTC forced alignment of the published LibriSpeech
   transcript with facebook/wav2vec2-base-960h (character model, Apache-2.0;
   a different model and vocabulary from the phoneme engine under test).
2. Phonemes per word: espeak-ng dictionary pronunciation (en-us).
3. Phoneme durations inside a word: fixed weights (vowels longer than stops).
4. Shapes: dex_lips.visemes.PHONEME_TO_SHAPE (the same documented table the
   wav2vec2 engine uses; this favours that engine on shape *choice*, which
   ACCURACY.md discloses).
5. A spectrogram PNG with word boundaries and cue overlay is written for the
   human-style visual timing review. Edits made in review are recorded in each
   reference JSON under "review".

Usage: PYTHONPATH=src python eval/tools/draft_reference.py CLIP.flac "TRANSCRIPT" OUT_PREFIX
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from dex_lips.visemes import phoneme_to_shape  # noqa: E402

ALIGN_MODEL = 'facebook/wav2vec2-base-960h'
ALIGN_REVISION = '22aad52d435eb6dbaf354bdad9b0da84ce7d6156'
VOWELS = set('aeiouɑɐɒæɛɜəɪɔʊʌᵻɚɝ')


def load_audio(path: Path) -> np.ndarray:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', '16000',
                          '-f', 's16le', '-'], stdout=subprocess.PIPE, check=True).stdout
    return np.frombuffer(raw, '<i2').astype('float32') / 32768


def forced_align(emission: np.ndarray, tokens: list[int], blank: int = 0) -> list[tuple[int, int]]:
    """Viterbi CTC alignment; returns (first_frame, last_frame) per target token."""
    T, S = emission.shape[0], len(tokens)
    ext = [blank]
    for t in tokens:
        ext += [t, blank]
    L = len(ext)
    NEG = -1e18
    dp = np.full((T, L), NEG)
    bp = np.zeros((T, L), dtype=np.int64)
    dp[0, 0] = emission[0, ext[0]]
    dp[0, 1] = emission[0, ext[1]]
    for t in range(1, T):
        for s in range(L):
            cands = [(dp[t - 1, s], s)]
            if s >= 1:
                cands.append((dp[t - 1, s - 1], s - 1))
            if s >= 2 and ext[s] != blank and ext[s] != ext[s - 2]:
                cands.append((dp[t - 1, s - 2], s - 2))
            v, arg = max(cands)
            dp[t, s] = v + emission[t, ext[s]]
            bp[t, s] = arg
    s = L - 1 if dp[T - 1, L - 1] >= dp[T - 1, L - 2] else L - 2
    path = [s]
    for t in range(T - 1, 0, -1):
        s = bp[t, s]
        path.append(s)
    path.reverse()
    spans: list[list[int]] = [[-1, -1] for _ in range(S)]
    for t, s in enumerate(path):
        if s % 2 == 1:
            k = s // 2
            if spans[k][0] < 0:
                spans[k][0] = t
            spans[k][1] = t
    return [tuple(x) for x in spans]


def word_spans(audio: np.ndarray, transcript: str):
    import torch
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
    proc = Wav2Vec2Processor.from_pretrained(ALIGN_MODEL, revision=ALIGN_REVISION)
    model = Wav2Vec2ForCTC.from_pretrained(ALIGN_MODEL, revision=ALIGN_REVISION).eval()
    x = proc(audio, sampling_rate=16000, return_tensors='pt').input_values
    with torch.inference_mode():
        em = torch.log_softmax(model(x).logits[0], -1).numpy()
    vocab = proc.tokenizer.get_vocab()
    text = transcript.upper().replace(' ', '|')
    tokens = [vocab[c] for c in text if c in vocab]
    chars = [c for c in text if c in vocab]
    spans = forced_align(em, tokens, blank=proc.tokenizer.pad_token_id)
    words, cur = [], []
    for c, sp in zip(chars, spans):
        if c == '|':
            if cur:
                words.append(cur)
            cur = []
        else:
            cur.append(sp)
    if cur:
        words.append(cur)
    raw = [(w[0][0] * .02, (w[-1][1] + 1) * .02) for w in words]
    return refine_with_energy(audio, raw)


def refine_with_energy(audio: np.ndarray, spans):
    """CTC spikes mark onsets early and ends early; extend each word end (and
    the first onset) while 10 ms frame energy stays above the speech threshold,
    bounded by the next word and 150 ms."""
    hop = 160
    e = np.array([20 * np.log10(np.sqrt(np.mean(audio[i:i + hop] ** 2)) + 1e-9)
                  for i in range(0, len(audio), hop)])
    thr = max(np.percentile(e, 10) + 10, e.max() - 38)
    out = []
    for k, (a, b) in enumerate(spans):
        nxt = spans[k + 1][0] if k + 1 < len(spans) else len(audio) / 16000
        f = int(b * 100)
        limit = min(int(nxt * 100), f + 15)
        while f < limit and f < len(e) and e[f] > thr:
            f += 1
        b2 = max(b, f / 100)
        prev = out[-1][1] if out else 0.0
        g = int(a * 100)
        while g > max(int(prev * 100), int(a * 100) - 6) and e[g - 1] > thr:
            g -= 1
        out.append((g / 100, b2))
    return out


def phonemes(word: str) -> list[str]:
    out = subprocess.run(['espeak-ng', '-q', '--ipa=1', '--sep=_', '-v', 'en-us', word],
                         stdout=subprocess.PIPE, check=True, text=True).stdout.strip()
    return [p.replace('ˈ', '').replace('ˌ', '') for p in out.replace(' ', '_').split('_') if p.strip('ˈˌ')]


def draft(clip: Path, transcript: str):
    audio = load_audio(clip)
    total = len(audio) / 16000
    words = transcript.lower().split()
    spans = word_spans(audio, transcript)
    segs = []
    for w, (a, b) in zip(words, spans):
        ph = phonemes(w)
        weights = [1.6 if any(ch in VOWELS for ch in p) else (0.8 if p in 'ptkbdg' else 1.0) for p in ph]
        t = a
        for p, wt in zip(ph, weights):
            d = (b - a) * wt / sum(weights)
            segs.append((t, t + d, phoneme_to_shape(p), p, w))
            t += d
    cues, t = [], 0.0
    for a, b, shape, *_ in segs:
        a, b = round(a, 2), round(b, 2)
        if a - t >= 0.12:
            cues.append({'start': round(t, 2), 'end': a, 'value': 'X'})
        elif cues:
            cues[-1]['end'] = a
        start = cues[-1]['end'] if cues else 0.0
        if cues and cues[-1]['value'] == shape:
            cues[-1]['end'] = b
        else:
            cues.append({'start': start if start < a else a, 'end': b, 'value': shape})
        t = b
    if cues and cues[0]['start'] > 0:
        cues.insert(0, {'start': 0.0, 'end': cues[0]['start'], 'value': 'X'})
    cues.append({'start': round(t, 2), 'end': round(total, 2), 'value': 'X'})
    cues = [c for c in cues if c['end'] > c['start']]
    return audio, total, spans, segs, cues


def spectrogram_png(audio, total, spans, words, cues, out: Path):
    from PIL import Image, ImageDraw
    n, hop = 512, 160
    frames = [audio[i:i + n] * np.hanning(n) for i in range(0, len(audio) - n, hop)]
    spec = np.log10(np.abs(np.fft.rfft(np.array(frames), axis=1))[:, :200] + 1e-6).T[::-1]
    spec = (255 * (spec - spec.min()) / (np.ptp(spec) + 1e-9)).astype('uint8')
    px_per_s = 400
    W = int(total * px_per_s)
    img = Image.fromarray(spec).resize((W, 200)).convert('RGB')
    canvas = Image.new('RGB', (W, 300), 'white')
    canvas.paste(img, (0, 0))
    d = ImageDraw.Draw(canvas)
    for (a, b), w in zip(spans, words):
        d.line([(a * px_per_s, 0), (a * px_per_s, 200)], fill='lime')
        d.line([(b * px_per_s, 0), (b * px_per_s, 200)], fill='red')
        d.text((a * px_per_s + 2, 205), w, fill='black')
    for c in cues:
        x0 = c['start'] * px_per_s
        d.line([(x0, 225), (x0, 260)], fill='blue')
        d.text((x0 + 2, 235), c['value'], fill='blue')
    for s in range(int(total * 10) + 1):
        d.line([(s * 40, 280), (s * 40, 290 if s % 10 else 300)], fill='black')
    canvas.save(out)


if __name__ == '__main__':
    clip, transcript, prefix = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    audio, total, spans, segs, cues = draft(clip, transcript)
    words = transcript.lower().split()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    Path(str(prefix) + '.draft.json').write_text(json.dumps({
        'word_spans': [[w, round(a, 2), round(b, 2)] for w, (a, b) in zip(words, spans)],
        'phones': [[p, round(a, 3), round(b, 3), s] for a, b, s, p, _ in segs],
        'mouthCues': cues}, indent=1, ensure_ascii=False))
    spectrogram_png(audio, total, spans, words, cues, Path(str(prefix) + '.png'))
    print(prefix)
