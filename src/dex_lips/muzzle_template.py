"""Generic, procedural muzzle mouth set (nine Rhubarb states) — NOT any real
character. It is drawn from simple geometric primitives so it can be shipped
in a public repo without using or imitating anyone's character art.

Conventions:
- Sprites are top-anchored: the nose/upper-lip line stays put and the lower
  jaw drops, the usual way a dog-like muzzle opens in 2-D animation.
- X is a closed resting mouth line (this template is stand-alone art; an
  in-app *source-traced* rig instead leaves X transparent).
- Deterministic: 4x supersampled PIL drawing, then LANCZOS downsample.

Run: PYTHONPATH=src python -m dex_lips.muzzle_template --out assets/mouth_sets/generic_muzzle
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

SHAPES = 'XABCDEFGH'
DEFAULT_PALETTE = {
    'line': (34, 30, 36, 255),      # outline / lip line
    'cavity': (58, 20, 28, 255),    # inside of mouth
    'tongue': (212, 106, 120, 255),
    'teeth': (244, 239, 230, 255),
    'gum': (150, 60, 72, 255),
}
DESCRIPTIONS = {
    'X': 'rest: closed muzzle line',
    'A': 'closed, lips pressed (P B M)',
    'B': 'slightly open, teeth nearly together (most consonants, EE)',
    'C': 'open, lower jaw dropped, tongue low (EH AE)',
    'D': 'wide open, canines and tongue visible (AA)',
    'E': 'slightly rounded opening (AO ER)',
    'F': 'puckered small round opening (OO OW W)',
    'G': 'upper teeth resting on lower lip (F V)',
    'H': 'open with tongue tip raised (L)',
}
# (opening width fraction, jaw drop fraction) of the sprite box.
OPENING = {'X': (0, 0), 'A': (0, 0), 'B': (.50, .14), 'C': (.56, .42), 'D': (.62, .70),
           'E': (.42, .40), 'F': (.24, .26), 'G': (.46, .10), 'H': (.54, .46)}


def draw_pose(label: str, width: int = 256, height: int = 160, palette: dict | None = None) -> Image.Image:
    if label not in SHAPES:
        raise ValueError('Unknown mouth shape')
    pal = dict(DEFAULT_PALETTE, **(palette or {}))
    s = 4
    W, H = width * s, height * s
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lw = max(2, int(W * .022))
    cx = W // 2
    top = int(H * .06)               # philtrum start (just under the nose)
    lip_y = int(H * .26)             # upper-lip line height
    jowl = int(W * .40)              # half-width of the upper lip curve
    ow, drop = OPENING[label]
    half = int(W * ow / 2)
    jaw = lip_y + int(H * drop)
    # Open cavity (drawn first so the lip line sits on top).
    if label not in 'XAG':
        if label in 'EF':
            box = (cx - half, lip_y - int(H * .03), cx + half, jaw)
            d.ellipse(box, fill=pal['cavity'], outline=pal['line'], width=lw)
        else:
            d.chord((cx - half, lip_y - (jaw - lip_y), cx + half, jaw), 0, 180,
                    fill=pal['cavity'], outline=pal['line'], width=lw)
        if label in 'CDH':
            tw = int(half * .62)
            if label == 'H':  # tongue tip raised toward the upper teeth
                d.ellipse((cx - tw // 2, lip_y, cx + tw // 2, lip_y + int((jaw - lip_y) * .55)), fill=pal['tongue'])
            else:
                d.chord((cx - tw, jaw - int((jaw - lip_y) * .55), cx + tw, jaw + int((jaw - lip_y) * .25)),
                        180, 360, fill=pal['tongue'])
        if label in 'BD':
            # Small upper teeth row; D also shows two canines.
            ty = lip_y + max(2, int(H * .015))
            d.rectangle((cx - int(half * .7), lip_y, cx + int(half * .7), ty + int(H * .03)), fill=pal['teeth'])
            if label == 'D':
                for sx in (-1, 1):
                    x = cx + sx * int(half * .62)
                    d.polygon([(x - int(W * .025), lip_y), (x + int(W * .025), lip_y), (x, lip_y + int(H * .17))],
                              fill=pal['teeth'])
            if label == 'B':
                d.rectangle((cx - int(half * .7), jaw - int(H * .03), cx + int(half * .7), jaw - lw // 2), fill=pal['teeth'])
    # Philtrum (vertical line from the nose) and the two upper-lip curves.
    d.line((cx, top, cx, lip_y), fill=pal['line'], width=lw)
    pressed = label == 'A'
    sag = int(H * (.05 if pressed else .09))
    d.arc((cx - jowl, lip_y - sag, cx, lip_y + sag), 0, 180, fill=pal['line'], width=lw + (lw // 2 if pressed else 0))
    d.arc((cx, lip_y - sag, cx + jowl, lip_y + sag), 0, 180, fill=pal['line'], width=lw + (lw // 2 if pressed else 0))
    if label == 'G':
        # Upper teeth resting on the lower lip.
        d.rectangle((cx - half, lip_y + sag - lw, cx + half, lip_y + sag + int(H * .05)), fill=pal['teeth'], outline=pal['line'], width=max(1, lw // 2))
        d.arc((cx - half, lip_y + sag, cx + half, lip_y + sag + int(H * .12)), 0, 180, fill=pal['line'], width=lw)
    elif label in 'XA':
        d.arc((cx - int(W * .12), lip_y + sag - int(H * .02), cx + int(W * .12), lip_y + sag + int(H * .08)), 20, 160,
              fill=pal['line'], width=max(1, lw // 2))
    return img.resize((width, height), Image.Resampling.LANCZOS)


def build_set(dest: Path, width: int = 256, height: int = 160, palette: dict | None = None) -> dict:
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    shapes = {}
    sheet = Image.new('RGBA', (width * 3 + 40, (height + 28) * 3 + 10), (236, 232, 222, 255))
    sd = ImageDraw.Draw(sheet)
    for i, label in enumerate(SHAPES):
        sprite = draw_pose(label, width, height, palette)
        sprite.save(dest / f'{label}.png', 'PNG')
        shapes[label] = f'{label}.png'
        x, y = 10 + (i % 3) * (width + 10), 10 + (i // 3) * (height + 28)
        sheet.alpha_composite(sprite, (x, y))
        sd.text((x + 4, y + height + 4), f'{label}: {DESCRIPTIONS[label]}'[:44], fill=(30, 30, 30, 255))
    sheet.convert('RGB').save(dest / 'contact_sheet.png')
    rig = {'schema_version': 1, 'character_id': 'generic-muzzle-template-not-a-character',
           'authority': 'synthetic_demo', 'approved': True,
           'mouth_anchor': {'x': .5, 'y': .6, 'scale': 1.0, 'rotation_deg': 0},
           'anchor_note': 'Sprites are top-anchored: place the anchor so the top-centre (philtrum) sits just under the nose.',
           'shapes': shapes, 'descriptions': DESCRIPTIONS,
           'notes': ('Procedurally drawn generic muzzle template. Not derived from, and not a likeness of, '
                     'any specific character (including Dexter or Tiger). Reviewed draft, not canon.')}
    (dest / 'rig.template.json').write_text(json.dumps(rig, indent=2), encoding='utf-8')
    return rig


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--width', type=int, default=256)
    p.add_argument('--height', type=int, default=160)
    a = p.parse_args()
    build_set(a.out, a.width, a.height)
    print(a.out)


if __name__ == '__main__':
    main()
