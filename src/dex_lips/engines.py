"""Engine selection for automatic mouth cues: real Rhubarb CLI and/or the
wav2vec2 phoneme recognizer. If neither engine can run, analysis is BLOCKED
and no cues are produced.

CLI:
  python -m dex_lips.engines --status
  python -m dex_lips.engines --fetch-model          # explicit one-time model download
  python -m dex_lips.engines --engine wav2vec2 --audio in.wav --output cues.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from .proof_render import ProofError
from . import speech, phoneme_engine

ENGINES = ('rhubarb', 'wav2vec2')


def engine_status(rhubarb_executable: str = 'rhubarb') -> dict[str, dict]:
    rb_path = shutil.which(rhubarb_executable)
    w_ok, w_reason = phoneme_engine.phoneme_engine_status()
    return {
        'rhubarb': {'available': bool(rb_path),
                    'reason': f'found at {rb_path}' if rb_path else 'Rhubarb binary not on PATH'},
        'wav2vec2': {'available': w_ok, 'reason': w_reason},
    }


def available_engines(rhubarb_executable: str = 'rhubarb') -> list[str]:
    return [name for name, s in engine_status(rhubarb_executable).items() if s['available']]


def analyze(audio: Path, output: Path, *, engine: str = 'auto', dialog: str = '',
            recognizer: str = 'pocketSphinx', rhubarb_executable: str = 'rhubarb',
            allow_download: bool = False) -> dict:
    """Run one real engine on real audio. 'auto' prefers Rhubarb, then wav2vec2.

    Raises ProofError containing 'BLOCKED' when no engine is available.
    """
    if engine not in ('auto',) + ENGINES:
        raise ProofError(f'Unknown engine {engine!r}')
    status = engine_status(rhubarb_executable)
    if engine == 'auto':
        choice = next((e for e in ENGINES if status[e]['available'] or
                       (e == 'wav2vec2' and allow_download and
                        phoneme_engine.phoneme_engine_status(allow_download=True)[0])), None)
        if choice is None:
            raise ProofError('Automatic recognition BLOCKED: neither Rhubarb nor the wav2vec2 '
                             'phoneme engine is available (' + '; '.join(
                                 f"{k}: {v['reason']}" for k, v in status.items()) +
                             '). Provide reviewed manual mouthCues JSON instead.')
        engine = choice
    if engine == 'rhubarb':
        if not status['rhubarb']['available']:
            raise ProofError('Rhubarb BLOCKED: ' + status['rhubarb']['reason'])
        result = speech.analyze(audio, output, dialog=dialog, recognizer=recognizer,
                                executable=rhubarb_executable)
    else:
        result = phoneme_engine.analyze(audio, output, allow_download=allow_download)
    result['engine'] = engine
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--status', action='store_true')
    p.add_argument('--fetch-model', action='store_true', help='explicitly download the wav2vec2 phoneme model')
    p.add_argument('--engine', default='auto', choices=('auto',) + ENGINES)
    p.add_argument('--audio', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--dialog', default='')
    a = p.parse_args()
    if a.fetch_model:
        from huggingface_hub import snapshot_download
        path = snapshot_download(phoneme_engine.MODEL_ID, revision=phoneme_engine.MODEL_REVISION,
                                 allow_patterns=['*.json', 'pytorch_model.bin'])
        print(json.dumps({'model': phoneme_engine.MODEL_ID, 'path': path}))
        return
    if a.status or not a.audio:
        print(json.dumps(engine_status(), indent=2))
        return
    try:
        print(json.dumps(analyze(a.audio, a.output, engine=a.engine, dialog=a.dialog), indent=2))
    except ProofError as e:
        p.error(str(e))


if __name__ == '__main__':
    main()
