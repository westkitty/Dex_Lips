"""Render the two engine demo MP4s (same picture, same audio, two real engines).

    PATH=/path/to/rhubarb:$PATH PYTHONPATH=src python scripts/make_demos.py

- Picture: a procedurally drawn generic cartoon dog head (NOT Dexter, NOT
  Tiger), generated here so no character art is needed.
- Mouth art: assets/mouth_sets/generic_muzzle (procedural template).
- Dexter demos (demo_dexter_*.mp4): a front-facing still cut from the
  owner-approved Dexter reference sheet (assets/reference/dexter/
  dexter_front_still.png, made by scripts/build_dexter_mouths.py) with the
  assets/mouth_sets/dexter_muzzle mouths, same audio and same cues.
- Audio: LibriSpeech test-clean 3575-170457-0001 (CC BY 4.0), see eval/manifest.json.
- Cues: produced by actually running each engine on that audio; the cue
  files are saved next to the MP4s. Refuses to run (BLOCKED) if an engine is
  missing rather than substituting cues.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from PIL import Image, ImageDraw  # noqa: E402

from dex_lips import engines  # noqa: E402
from dex_lips.proof_render import render, sha256  # noqa: E402

OUT = ROOT / 'demos'
AUDIO = ROOT / 'eval/clips/3575-170457-0001.flac'
SET = ROOT / 'assets/mouth_sets/generic_muzzle'
NOSE_BOTTOM = (320, 292)


def character(caption: str) -> Image.Image:
    W, H = 640, 480
    img = Image.new('RGB', (W, H), (226, 232, 238))
    d = ImageDraw.Draw(img)
    fur, light, dark = (112, 128, 150), (196, 205, 216), (40, 44, 54)
    d.polygon([(170, 190), (215, 60), (275, 160)], fill=fur, outline=dark, width=4)   # ears
    d.polygon([(470, 190), (425, 60), (365, 160)], fill=fur, outline=dark, width=4)
    d.ellipse((160, 110, 480, 420), fill=fur, outline=dark, width=4)                  # head
    d.ellipse((225, 230, 415, 410), fill=light, outline=dark, width=3)                 # snout
    d.ellipse((248, 190, 282, 224), fill=dark); d.ellipse((358, 190, 392, 224), fill=dark)  # eyes
    d.ellipse((259, 197, 268, 206), fill=(250, 250, 250)); d.ellipse((369, 197, 378, 206), fill=(250, 250, 250))
    d.ellipse((292, 250, 348, 292), fill=dark)                                         # nose
    d.text((16, 14), caption, fill=dark)
    d.text((16, H - 26), 'Generic procedural demo character - not Dexter, not Tiger', fill=dark)
    return img


DEXTER_SET = ROOT / 'assets/mouth_sets/dexter_muzzle'
DEXTER_STILL = ROOT / 'assets/reference/dexter/dexter_front_still.png'
ENGINES = (('rhubarb', 'Engine: Rhubarb Lip Sync 1.14.0 (pocketSphinx, audio only)'),
           ('wav2vec2', 'Engine: wav2vec2 phoneme recognizer (audio only)'))


def generic_setup(label: str, work: Path) -> tuple[Path, dict, dict]:
    tpl = json.loads((SET / 'rig.template.json').read_text())
    scale = 0.62
    sprite_h = Image.open(SET / 'X.png').height * scale
    anchor = {'x': NOSE_BOTTOM[0] / 640, 'y': (NOSE_BOTTOM[1] - 6 + sprite_h / 2) / 480,
              'scale': scale, 'rotation_deg': 0}
    src = work / 'character.png'
    character(label).save(src)
    return src, tpl, anchor


def dexter_setup(label: str, work: Path) -> tuple[Path, dict, dict]:
    """Front-facing Dexter still cut from the owner-approved sheet, with a caption bar."""
    tpl = json.loads((DEXTER_SET / 'rig.template.json').read_text())
    img = Image.open(DEXTER_STILL).convert('RGB')
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, img.width, 22), fill=(236, 232, 222))
    d.text((8, 5), label + ' | mouths: dexter_muzzle (from approved sheet)', fill=(30, 30, 30))
    src = work / 'character.png'
    img.save(src)
    return src, tpl, dict(tpl['mouth_anchor'])


SETS = {
    'generic': {'dir': SET, 'setup': generic_setup, 'prefix': 'demo_', 'source': 'source_'},
    'dexter': {'dir': DEXTER_SET, 'setup': dexter_setup, 'prefix': 'demo_dexter_', 'source': 'source_dexter_'},
}


def main() -> None:
    status = engines.engine_status()
    missing = [k for k, v in status.items() if not v['available']]
    if missing:
        raise SystemExit(f'BLOCKED: engines unavailable: {missing}. No demo cues were invented.')
    OUT.mkdir(exist_ok=True)
    receipts: dict = {}
    cue_results: dict = {}
    # Cues depend only on the audio and the engine: each engine runs once and both sets share its cues.
    for key, _ in ENGINES:
        cues = OUT / f'cues_{key}.json'
        cues.unlink(missing_ok=True)
        cue_results[key] = engines.analyze(AUDIO, cues, engine=key)
    for set_name, cfg in SETS.items():
        receipts[set_name] = {}
        for key, label in ENGINES:
            work = OUT / f'.work_{set_name}_{key}'
            shutil.rmtree(work, ignore_errors=True)
            work.mkdir()
            src, tpl, anchor = cfg['setup'](label, work)
            for shape in tpl['shapes'].values():
                shutil.copy(cfg['dir'] / shape, work / shape)
            rig = dict(tpl, source_path=src.name, source_sha256=sha256(src), mouth_anchor=anchor)
            (work / 'rig.json').write_text(json.dumps(rig, indent=2))
            mp4 = OUT / f"{cfg['prefix']}{key}.mp4"
            mp4.unlink(missing_ok=True)
            r = render(src, AUDIO, work / 'rig.json', OUT / f'cues_{key}.json', mp4, fps=24, crossfade_sec=0.04)
            r['cue_engine'] = cue_results[key]
            r['mouth_set'] = str(cfg['dir'].relative_to(ROOT))
            receipts[set_name][key] = r
            shutil.copy(src, OUT / f"{cfg['source']}{key}.png")
            shutil.rmtree(work)
        side = OUT / f"{cfg['prefix']}side_by_side.mp4"
        side.unlink(missing_ok=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(OUT / f"{cfg['prefix']}rhubarb.mp4"),
                        '-i', str(OUT / f"{cfg['prefix']}wav2vec2.mp4"),
                        '-filter_complex', '[0:v]scale=480:-2[a];[1:v]scale=480:-2[b];[a][b]hstack[v]',
                        '-map', '[v]', '-map', '0:a', '-c:v', 'libx264', '-crf', '23', '-preset', 'veryfast',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', str(side)], check=True)
    (OUT / 'receipts.json').write_text(json.dumps(receipts, indent=2))
    print(json.dumps({s: {k: {'output_sha256': v['output_sha256'], 'cues': v['cue_engine']['cue_count']}
                          for k, v in r.items()} for s, r in receipts.items()}, indent=2))


if __name__ == '__main__':
    main()
