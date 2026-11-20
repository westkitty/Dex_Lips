"""Audio-driven Rhubarb adapter. No guesses, paid APIs or model weights.

Requires a user-installed Rhubarb executable (not vendored or fetched).
The output is generated from the audio, never from timing text alone.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from .proof_render import ProofError, duration, load_cues, media_probe, need_tools

ALLOWED_RECOGNIZERS = frozenset({'pocketSphinx', 'phonetic'})


def rhubarb_available(executable: str = 'rhubarb') -> bool:
    return bool(shutil.which(executable))


def analyze(audio: Path, output: Path, *, dialog: str = '', recognizer: str = 'pocketSphinx',
            executable: str = 'rhubarb', timeout: int = 90, extended_shapes: str = 'GHX') -> dict:
    """Analyze actual WAV/MP3/M4A/etc audio, writing validated Rhubarb JSON.

    The caller owns the destination and any temporary job folder. No implicit
    downloading or network access. An existing output is NEVER overwritten.
    """
    audio, output = Path(audio), Path(output)
    if not audio.is_file():
        raise ProofError('Speech audio file is missing')
    if output.exists():
        raise ProofError('Rhubarb output path already exists; refusing overwrite')
    if audio.stat().st_size > 40 * 1024 * 1024:
        raise ProofError('Speech audio exceeds the 40 MiB limit')
    if recognizer not in ALLOWED_RECOGNIZERS:
        raise ProofError('Unknown Rhubarb recognizer')
    if not isinstance(dialog, str) or len(dialog) > 10000:
        raise ProofError('Dialog text must be under 10000 characters')
    if any(c not in 'GHX' for c in extended_shapes) or len(set(extended_shapes)) != len(extended_shapes):
        raise ProofError('Invalid Rhubarb extended mouth shape list')
    executable_path = shutil.which(executable)
    if not executable_path:
        raise ProofError('Rhubarb binary is not installed. Automatic audio-to-mouth analysis is unavailable; provide reviewed manual mouthCues JSON instead.')
    need_tools()
    probe = media_probe(audio)
    if not probe.get('audio'):
        raise ProofError('Input does not contain an audio track')
    seconds = duration(probe)
    if not .15 <= seconds <= 30.:
        raise ProofError('Audio for Rhubarb must be 0.15 to 30 seconds')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='dex_lips_rhubarb_') as working:
        working = Path(working)
        wav = working / 'speech.wav'
        cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-i', str(audio), '-map', '0:a:0',
               '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(wav)]
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               check=False, timeout=35)
        except subprocess.TimeoutExpired as ex:
            raise ProofError('Audio normalization timed out') from ex
        if p.returncode or not wav.is_file():
            raise ProofError('FFmpeg audio normalization failed: ' + p.stderr.decode(errors='replace')[-300:])
        result_path = working / 'rhubarb.json'
        rhubarb = [executable_path, '--quiet', '--recognizer', recognizer,
                   '--exportFormat', 'json', '--extendedShapes', extended_shapes,
                   '--output', str(result_path)]
        if dialog.strip():
            dialog_path = working / 'dialog.txt'
            dialog_path.write_text(dialog, encoding='utf-8')
            rhubarb.extend(['--dialogFile', str(dialog_path)])
        rhubarb.append(str(wav))  # MUST be the final positional argument.
        try:
            p = subprocess.run(rhubarb, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               check=False, timeout=timeout)
        except subprocess.TimeoutExpired as ex:
            raise ProofError('Rhubarb speech analysis timed out') from ex
        if p.returncode or not result_path.is_file():
            raise ProofError('Rhubarb failed: ' + p.stderr.decode(errors='replace')[-400:])
        # Validate before making the output visible to the user.
        cues = load_cues(result_path, seconds)
        if len(cues) > 10000:
            raise ProofError('Rhubarb returned too many mouth cues')
        doc = json.loads(result_path.read_text(encoding='utf-8'))
        doc['metadata'] = {'duration': seconds, 'analysis': 'rhubarb',
                           'recognizer': recognizer, 'cue_count': len(cues)}
        output.write_text(json.dumps(doc, indent=2), encoding='utf-8')
    return {'analysis': 'Rhubarb from actual audio', 'cue_count': len(cues),
            'recognizer': recognizer, 'output': str(output)}
