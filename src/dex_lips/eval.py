"""Reproducible accuracy evaluation of the automatic mouth-cue engines.

One command (from the repository root):

    PYTHONPATH=src python -m dex_lips.eval        # or: make accuracy

It runs every *available* engine on the real audio in eval/clips/, scores the
output against the reviewer-judgment reference tracks in eval/reference/,
writes per-engine cue files to eval/results/ and rewrites ACCURACY.md.
Engines that cannot run are reported as BLOCKED; no numbers are invented.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import platform
import statistics
import tempfile
import time

from .proof_render import ProofError
from . import speech, phoneme_engine
from .visemes import mapping_table_markdown

ROOT = Path(__file__).resolve().parents[2]
SHAPES = 'XABCDEFGH'
FPS = 100  # 10 ms scoring frames
GROUPS = {'X': 'closed', 'A': 'closed', 'B': 'narrow', 'G': 'narrow', 'H': 'narrow',
          'C': 'open', 'D': 'open', 'E': 'round', 'F': 'round'}

CONFIGS = [
    {'key': 'rhubarb-pocketsphinx', 'label': 'Rhubarb 1.14.0, pocketSphinx recognizer, audio only',
     'kind': 'rhubarb', 'recognizer': 'pocketSphinx', 'dialog': False},
    {'key': 'rhubarb-phonetic', 'label': 'Rhubarb 1.14.0, phonetic recognizer, audio only',
     'kind': 'rhubarb', 'recognizer': 'phonetic', 'dialog': False},
    {'key': 'rhubarb-pocketsphinx-dialog', 'label': 'Rhubarb 1.14.0, pocketSphinx + transcript (--dialogFile)',
     'kind': 'rhubarb', 'recognizer': 'pocketSphinx', 'dialog': True},
    {'key': 'wav2vec2-phoneme', 'label': 'wav2vec2 phoneme CTC (facebook/wav2vec2-lv-60-espeak-cv-ft), audio only',
     'kind': 'wav2vec2'},
]


def frames(cues: list[dict], total: float) -> list[str]:
    n = int(round(total * FPS))
    out = ['X'] * n
    for c in cues:
        a, b = int(round(float(c['start']) * FPS)), int(round(float(c['end']) * FPS))
        for i in range(max(0, a), min(n, b)):
            out[i] = c['value']
    return out


def boundaries(cues: list[dict]) -> list[float]:
    out = []
    for prev, cur in zip(cues, cues[1:]):
        if prev['value'] != cur['value']:
            out.append(float(cur['start']))
    return out


def score_clip(ref: list[dict], hyp: list[dict], total: float) -> dict:
    rf, hf = frames(ref, total), frames(hyp, total)
    n = min(len(rf), len(hf))
    exact = sum(1 for i in range(n) if rf[i] == hf[i])
    grouped = sum(1 for i in range(n) if GROUPS[rf[i]] == GROUPS[hf[i]])
    rb, hb = boundaries(ref), boundaries(hyp)
    offsets = []
    signed = []
    for t in rb:
        if hb:
            nearest = min(hb, key=lambda h: abs(h - t))
            offsets.append(abs(nearest - t))
            signed.append(nearest - t)
    confusion = Counter((rf[i], hf[i]) for i in range(n))
    return {'frames': n, 'exact': exact, 'grouped': grouped, 'offsets': offsets, 'signed': signed,
            'confusion': confusion, 'ref_boundaries': len(rb), 'hyp_boundaries': len(hb)}


def run_engine(cfg: dict, clip: Path, transcript: str, out: Path) -> list[dict]:
    if out.exists():
        out.unlink()
    if cfg['kind'] == 'rhubarb':
        speech.analyze(clip, out, recognizer=cfg['recognizer'],
                       dialog=transcript.lower() if cfg['dialog'] else '')
    else:
        phoneme_engine.analyze(clip, out)
    return json.loads(out.read_text(encoding='utf-8'))['mouthCues']


def _pct(a: int, b: int) -> str:
    return f'{100 * a / b:.1f}%' if b else 'n/a'


def _ms(values: list[float], fn) -> str:
    return f'{1000 * fn(values):.0f} ms' if values else 'n/a'


def confusion_table(conf: Counter) -> str:
    head = '| ref \\ engine | ' + ' | '.join(SHAPES) + ' | frames | recall |'
    rows = [head, '|' + '---|' * (len(SHAPES) + 3)]
    for r in SHAPES:
        total = sum(conf[(r, h)] for h in SHAPES)
        cells = [str(conf[(r, h)]) if conf[(r, h)] else '·' for h in SHAPES]
        rows.append(f'| **{r}** | ' + ' | '.join(cells) + f' | {total} | {_pct(conf[(r, r)], total)} |')
    prec = []
    for h in SHAPES:
        col = sum(conf[(r, h)] for r in SHAPES)
        prec.append(_pct(conf[(h, h)], col))
    rows.append('| precision | ' + ' | '.join(prec) + ' | | |')
    return '\n'.join(rows)


def evaluate(write: bool = True) -> dict:
    manifest = json.loads((ROOT / 'eval/manifest.json').read_text(encoding='utf-8'))
    results_dir = ROOT / 'eval/results'
    summary = {'engines': {}, 'clips': [c['id'] for c in manifest['clips']]}
    rb_ok = speech.rhubarb_available()
    w_ok, w_reason = phoneme_engine.phoneme_engine_status()
    for cfg in CONFIGS:
        if cfg['kind'] == 'rhubarb' and not rb_ok:
            summary['engines'][cfg['key']] = {'label': cfg['label'], 'status': 'BLOCKED',
                                              'reason': 'Rhubarb binary not on PATH'}
            continue
        if cfg['kind'] == 'wav2vec2' and not w_ok:
            summary['engines'][cfg['key']] = {'label': cfg['label'], 'status': 'BLOCKED', 'reason': w_reason}
            continue
        agg = {'frames': 0, 'exact': 0, 'grouped': 0, 'offsets': [], 'signed': [],
               'confusion': Counter(), 'per_clip': [], 'seconds': 0.0}
        for clip in manifest['clips']:
            ref_doc = json.loads((ROOT / 'eval/reference' / f"{clip['id']}.json").read_text(encoding='utf-8'))
            out = results_dir / cfg['key'] / f"{clip['id']}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            t0 = time.perf_counter()
            try:
                hyp = run_engine(cfg, ROOT / clip['file'], clip['transcript'], out)
            except ProofError as exc:
                agg['per_clip'].append({'clip': clip['id'], 'error': str(exc)})
                continue
            agg['seconds'] += time.perf_counter() - t0
            s = score_clip(ref_doc['mouthCues'], hyp, clip['duration_sec'])
            for k in ('frames', 'exact', 'grouped'):
                agg[k] += s[k]
            agg['offsets'] += s['offsets']
            agg['signed'] += s['signed']
            agg['confusion'] += s['confusion']
            agg['per_clip'].append({'clip': clip['id'], 'exact': _pct(s['exact'], s['frames']),
                                    'grouped': _pct(s['grouped'], s['frames']),
                                    'median_offset': _ms(s['offsets'], statistics.median),
                                    'cues': len(hyp)})
        summary['engines'][cfg['key']] = {
            'label': cfg['label'], 'status': 'RAN',
            'frame_accuracy': agg['exact'] / agg['frames'] if agg['frames'] else None,
            'grouped_accuracy': agg['grouped'] / agg['frames'] if agg['frames'] else None,
            'mean_offset_ms': 1000 * statistics.mean(agg['offsets']) if agg['offsets'] else None,
            'median_offset_ms': 1000 * statistics.median(agg['offsets']) if agg['offsets'] else None,
            'mean_signed_offset_ms': 1000 * statistics.mean(agg['signed']) if agg['signed'] else None,
            'frames': agg['frames'], 'boundaries': len(agg['offsets']),
            'per_clip': agg['per_clip'], 'confusion': {f'{r}>{h}': v for (r, h), v in sorted(agg['confusion'].items())},
            '_confusion': agg['confusion'], 'runtime_sec': round(agg['seconds'], 1)}
    if write:
        (ROOT / 'ACCURACY.md').write_text(render_markdown(manifest, summary), encoding='utf-8')
        clean = {k: {kk: vv for kk, vv in v.items() if not kk.startswith('_')} for k, v in summary['engines'].items()}
        results_dir.mkdir(parents=True, exist_ok=True)
        (results_dir / 'summary.json').write_text(json.dumps({'engines': clean, 'clips': summary['clips']},
                                                             indent=1), encoding='utf-8')
    return summary


def render_markdown(manifest: dict, summary: dict) -> str:
    total_sec = sum(c['duration_sec'] for c in manifest['clips'])
    L = ['# Dex_Lips automatic mouth-cue accuracy', '',
         '> **Generated file.** Rewritten by `make accuracy` (`PYTHONPATH=src python -m dex_lips.eval`). '
         'Do not hand-edit numbers.', '',
         '## Read this first', '',
         '- **The reference cue tracks are the reviewer\'s own judgment, not ground truth.** They were drafted '
         'semi-automatically (transcript forced alignment + dictionary pronunciations + the documented '
         'phoneme→shape table) and then checked by eye against spectrograms. See `eval/README.md`.',
         '- **Bias disclosure.** The references use the same phoneme→shape table as the wav2vec2 engine, so that '
         'engine is favoured on *which* shape is chosen for a given sound. Rhubarb uses its own context-dependent '
         'rules (tweening, anticipation), so lower exact-match numbers for Rhubarb partly measure disagreement '
         'in style, not just error. The grouped score (closed / narrow / open / round) and the boundary offsets '
         'are less sensitive to that bias.',
         f'- **Small set:** {len(manifest["clips"])} LibriSpeech test-clean utterances, {len(manifest["clips"])} '
         f'speakers, {total_sec:.1f} s of speech in total. Read audiobook English only; numbers will not transfer '
         'to noisy, emotional, cartoon or non-English voices.',
         f'- Scoring: {FPS} frames/s. *Frame accuracy* = share of 10 ms frames whose shape exactly matches the '
         'reference. *Boundary offset* = for every reference shape change, distance to the nearest engine shape '
         'change (signed mean: negative = engine changes shape earlier).', '',
         '## Headline results', '',
         '| Engine | Status | Frame accuracy (exact) | Grouped accuracy | Mean boundary offset | Median boundary offset | Signed mean | Runtime (all clips) |',
         '|---|---|---|---|---|---|---|---|']
    for key, e in summary['engines'].items():
        if e['status'] != 'RAN':
            L.append(f"| {e['label']} | **BLOCKED**: {e['reason']} | – | – | – | – | – | – |")
            continue
        L.append(f"| {e['label']} | ran | **{100 * e['frame_accuracy']:.1f}%** | {100 * e['grouped_accuracy']:.1f}% | "
                 f"{e['mean_offset_ms']:.0f} ms | **{e['median_offset_ms']:.0f} ms** | {e['mean_signed_offset_ms']:+.0f} ms | "
                 f"{e['runtime_sec']} s |")
    L += ['', '## Per-clip results', '']
    for key, e in summary['engines'].items():
        if e['status'] != 'RAN':
            continue
        L += [f"### {e['label']}", '', '| Clip | Exact | Grouped | Median offset | Cues |', '|---|---|---|---|---|']
        for c in e['per_clip']:
            if 'error' in c:
                L.append(f"| {c['clip']} | ERROR: {c['error']} | | | |")
            else:
                L.append(f"| {c['clip']} | {c['exact']} | {c['grouped']} | {c['median_offset']} | {c['cues']} |")
        L.append('')
    L += ['## Per-shape confusion (frames)', '',
          'Rows are the reference shape, columns the engine output. `·` = 0.', '']
    for key, e in summary['engines'].items():
        if e['status'] != 'RAN':
            continue
        L += [f"### {e['label']}", '', confusion_table(e['_confusion']), '']
    L += ['## Phoneme → shape table (wav2vec2 engine and reference drafts)', '', mapping_table_markdown(), '',
          '## Evaluation set', '',
          f"Source: {manifest['dataset']}. {manifest['dataset_citation']} License: {manifest['license']}. "
          f"{manifest['retrieved_via']}", '',
          '| Clip | Speaker | Duration | Transcript | sha256 (first 12) |', '|---|---|---|---|---|']
    for c in manifest['clips']:
        L.append(f"| {c['id']} | {c['speaker_id']} | {c['duration_sec']:.2f} s | {c['transcript']} | `{c['sha256'][:12]}` |")
    L += ['', '## Environment of the last run', '',
          f'- Python {platform.python_version()} on {platform.system()} {platform.machine()}',
          f'- Rhubarb available: {speech.rhubarb_available()}',
          f'- wav2vec2 model: {phoneme_engine.MODEL_ID} @ {phoneme_engine.MODEL_REVISION} ({phoneme_engine.MODEL_LICENSE})',
          '- Engine outputs for every clip are in `eval/results/<engine>/`; machine-readable totals in `eval/results/summary.json`.',
          '']
    return '\n'.join(L)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--no-write', action='store_true', help='print totals without rewriting ACCURACY.md')
    a = p.parse_args()
    s = evaluate(write=not a.no_write)
    for key, e in s['engines'].items():
        if e['status'] == 'RAN':
            print(f"{key}: frame {100 * e['frame_accuracy']:.1f}%  grouped {100 * e['grouped_accuracy']:.1f}%  "
                  f"offset mean {e['mean_offset_ms']:.0f} ms median {e['median_offset_ms']:.0f} ms")
        else:
            print(f"{key}: BLOCKED ({e['reason']})")


if __name__ == '__main__':
    main()
