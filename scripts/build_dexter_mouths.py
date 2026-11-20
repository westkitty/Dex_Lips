"""Build the Dexter muzzle mouth set ONLY from the owner-approved reference sheet.

    python scripts/build_dexter_mouths.py   (needs Pillow, numpy, opencv-python)

Every pixel comes from assets/reference/dexter/dexter_reference_sheet.png
(sha256 ed81548c...c12c41, supplied and approved by the owner 2026-11-20).
Nothing is drawn freehand. Cells used (row/column on the sheet, header label):

  base still + X   row 1 col 3 "Left-Proflle"  front-facing head, relaxed closed mouth
  A                row 1 col 1 "Front-01"      front-facing head, pressed/downturned mouth
  B, G             row 2 col 4 "Determinted"   front-facing head, teeth showing
  C, D, E, F, H    row 1 col 4 "Profile"       front-facing head, open mouth, teeth + tongue

Edits (documented per shape in rig.template.json): the base mouth line is
removed by OpenCV inpainting so open shapes do not double up, and the borrowed
mouth pixels are scaled (D taller, E/F narrower and rounder, G flatter, H
taller) about the upper lip. The three borrowed cells share the base cell's
scale: their noses measure 18-19 px wide on the sheet, so no resizing is
needed to line them up; they are aligned on the bottom-centre of the nose.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / 'assets/reference/dexter/dexter_reference_sheet.png'
SHEET_SHA256 = 'ed81548c07c3e3b47a189a0aa2a502fe171146a1f2a96060d790e22091c12c41'
OUT = ROOT / 'assets/mouth_sets/dexter_muzzle'
STILL = ROOT / 'assets/reference/dexter/dexter_front_still.png'
UP = 4  # sheet pixels -> output pixels (LANCZOS)

# Nose bottom-centre (x, y) of each cell on the sheet, measured as the darkest
# connected blob in the muzzle (nose bboxes: 19x13, 18x14, 18x14, 19x14 px).
CELLS = {
    'left_profile_r1c3': {'label': 'row 1 col 3 "Left-Proflle"', 'nose': (517, 159)},
    'front01_r1c1': {'label': 'row 1 col 1 "Front-01"', 'nose': (123, 163)},
    'profile_r1c4': {'label': 'row 1 col 4 "Profile"', 'nose': (729, 159)},
    'determined_r2c4': {'label': 'row 2 col 4 "Determinted"', 'nose': (698, 406)},
}
BASE = 'left_profile_r1c3'
# Mouth patch relative to nose bottom-centre, in sheet pixels.
PX0, PX1, PY0, PY1 = -18, 18, 1, 23
# Still crop on the sheet (4:3), base cell head and chest.
STILL_BOX = (437, 80, 597, 200)

SHAPES = {
    #       cell,              sx,   sy,   description
    'X': (BASE,               1.00, 1.00, 'rest: base cell mouth unchanged'),
    'A': ('front01_r1c1',     1.00, 1.00, 'closed, lips pressed (P B M): Front-01 mouth unchanged'),
    'B': ('determined_r2c4',  1.00, 1.00, 'teeth nearly together (consonants, EE): Determined mouth unchanged'),
    'C': ('profile_r1c4',     1.00, 1.00, 'open, tongue low (EH AE): Profile mouth unchanged'),
    'D': ('profile_r1c4',     1.00, 1.40, 'wide open (AA): Profile mouth stretched 1.4x down'),
    'E': ('profile_r1c4',     0.74, 1.15, 'rounded (AO ER): Profile mouth 0.74x wide, 1.15x tall'),
    'F': ('profile_r1c4',     0.52, 0.85, 'puckered small opening (OO W): Profile mouth 0.52x wide, 0.85x tall'),
    'G': ('determined_r2c4',  0.88, 0.70, 'teeth on lower lip (F V): Determined mouth 0.88x wide, 0.70x tall'),
    'H': ('profile_r1c4',     0.92, 1.20, 'open, tongue showing (L): Profile mouth 0.92x wide, 1.20x tall'),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch(sheet: np.ndarray, cell: str) -> np.ndarray:
    nx, ny = CELLS[cell]['nose']
    p = sheet[ny + PY0:ny + PY1, nx + PX0:nx + PX1 + 1]
    return cv2.resize(p, (p.shape[1] * UP, p.shape[0] * UP), interpolation=cv2.INTER_LANCZOS4)


def cream_of(p: np.ndarray) -> np.ndarray:
    """Typical muzzle fur colour of a patch (the brightest third, median)."""
    flat = p.reshape(-1, 3).astype(float)
    lum = flat.mean(1)
    return np.median(flat[lum >= np.percentile(lum, 66)], axis=0)


def mouth_mask(p: np.ndarray) -> np.ndarray:
    """Pixels that belong to the mouth drawing (line, lips, teeth, tongue)."""
    h, w = p.shape[:2]
    diff = np.abs(p.astype(float) - cream_of(p)).sum(2)
    m = (diff > 70).astype(np.uint8)
    # keep only the central mouth zone (excludes chin outline and side fur strokes)
    zone = np.zeros_like(m)
    cv2.ellipse(zone, (w // 2, int(h * 0.30)), (int(w * 0.44), int(h * 0.26)), 0, 0, 360, 1, -1)
    m &= zone
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= 6 * UP * UP:
            keep[lab == i] = 1
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((3 * UP, 3 * UP), np.uint8))
    return cv2.dilate(keep, np.ones((UP + 1, UP + 1), np.uint8))


def scaled_about_lip(img: np.ndarray, sx: float, sy: float, top: int) -> np.ndarray:
    h, w = img.shape[:2]
    M = np.float32([[sx, 0, (1 - sx) * w / 2], [0, sy, (1 - sy) * top]])
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def build() -> dict:
    if sha256(SHEET) != SHEET_SHA256:
        raise SystemExit('Reference sheet hash mismatch; refusing to build from unapproved art.')
    sheet = cv2.cvtColor(cv2.imread(str(SHEET)), cv2.COLOR_BGR2RGB)
    OUT.mkdir(parents=True, exist_ok=True)

    # Source still: base cell, upscaled.
    x0, y0, x1, y1 = STILL_BOX
    still = cv2.resize(sheet[y0:y1, x0:x1], ((x1 - x0) * UP, (y1 - y0) * UP), interpolation=cv2.INTER_LANCZOS4)
    Image.fromarray(still).save(STILL)

    base = patch(sheet, BASE)
    blank = cv2.inpaint(base, mouth_mask(base) * 255, 5, cv2.INPAINT_TELEA)
    h, w = base.shape[:2]
    # Feathered ellipse: opaque over the mouth zone, fading to the (identical) base fur.
    alpha = np.zeros((h, w), np.float32)
    cv2.ellipse(alpha, (w // 2, int(h * 0.40)), (int(w * 0.46), int(h * 0.50)), 0, 0, 360, 1.0, -1)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 2.2 * UP)
    alpha[: UP, :] = 0  # leave the nose edge untouched

    out = {}
    for shape, (cell, sx, sy, desc) in SHAPES.items():
        src = patch(sheet, cell)
        m = mouth_mask(src).astype(np.float32)
        # colour-match the borrowed cell's muzzle fur to the base cell
        src = np.clip(src.astype(float) + (cream_of(base) - cream_of(src)), 0, 255).astype(np.uint8)
        top = int(np.argmax(m.any(1))) if m.any() else 0
        src_s = scaled_about_lip(src, sx, sy, top)
        m_s = cv2.GaussianBlur(scaled_about_lip(m, sx, sy, top), (0, 0), 0.6 * UP)[..., None]
        canvas = (blank.astype(float) * (1 - m_s) + src_s.astype(float) * m_s).astype(np.uint8)
        rgba = np.dstack([canvas, (alpha * 255).astype(np.uint8)])
        Image.fromarray(rgba, 'RGBA').save(OUT / f'{shape}.png')
        out[shape] = {'file': f'{shape}.png', 'cell': CELLS[cell]['label'], 'scale_x': sx, 'scale_y': sy, 'description': desc}

    nx, ny = CELLS[BASE]['nose']
    cx = (nx - x0) * UP + 0.5 * UP
    cy = (ny + PY0 - y0) * UP + h / 2
    sw, sh = still.shape[1], still.shape[0]
    rig = {
        'schema_version': 1,
        'character_id': 'dexter',
        'authority': 'approved_user_rig',
        'approved': True,
        'approval': 'Reference sheet supplied and approved by the owner on 2026-11-20; see docs/RIGHTS.md.',
        'reference_sheet': 'assets/reference/dexter/dexter_reference_sheet.png',
        'reference_sheet_sha256': SHEET_SHA256,
        'intended_source': 'assets/reference/dexter/dexter_front_still.png',
        'mouth_anchor': {'x': round(cx / sw, 6), 'y': round(cy / sh, 6), 'scale': 1.0, 'rotation_deg': 0},
        'anchor_note': 'Sprites are muzzle patches cut from the sheet; on dexter_front_still.png the anchor puts their top edge just under the nose. On other pictures, scale so the patch width matches the muzzle.',
        'shapes': {k: v['file'] for k, v in out.items()},
        'descriptions': {k: v['description'] for k, v in out.items()},
        'provenance': {k: {'cell': v['cell'], 'scale_x': v['scale_x'], 'scale_y': v['scale_y']} for k, v in out.items()},
        'notes': 'Built only from the owner-approved Dexter reference sheet by scripts/build_dexter_mouths.py. Base mouth line removed by inpainting; borrowed mouths colour-matched to the base fur. The sheet is low resolution (each mouth is about 30x12 px), so sprites are 4x upscales and look soft. E, F, G, D and H are edits (scaled) of sheet mouths, not separate drawings on the sheet.',
    }
    (OUT / 'rig.template.json').write_text(json.dumps(rig, indent=2) + '\n')
    contact_sheet(still, rig)
    return rig


def contact_sheet(still: np.ndarray, rig: dict) -> None:
    sw, sh = still.shape[1], still.shape[0]
    a = rig['mouth_anchor']
    tile_w, tile_h = 300, 203
    sheet = Image.new('RGB', (tile_w * 3 + 40, (tile_h + 34) * 3 + 50), (236, 232, 222))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), 'Dexter muzzle set - cut only from the owner-approved reference sheet (sha256 ed81548c...)', fill=(30, 30, 30))
    for i, shape in enumerate('XABCDEFGH'):
        frame = Image.fromarray(still).convert('RGBA')
        sp = Image.open(OUT / f'{shape}.png')
        frame.alpha_composite(sp, (int(a['x'] * sw - sp.width / 2), int(a['y'] * sh - sp.height / 2)))
        # crop to the head so the mouth is readable
        head = frame.crop((int(sw * 0.25), int(sh * 0.40), int(sw * 0.75), int(sh * 0.85))).resize((tile_w, tile_h), Image.LANCZOS)
        x, y = 10 + (i % 3) * (tile_w + 10), 34 + (i // 3) * (tile_h + 34)
        sheet.paste(head.convert('RGB'), (x, y))
        d.text((x, y + tile_h + 4), f"{shape}: {rig['descriptions'][shape]}"[:52], fill=(30, 30, 30))
        d.text((x, y + tile_h + 17), f"from {rig['provenance'][shape]['cell']}", fill=(90, 90, 90))
    sheet.save(OUT / 'contact_sheet.png')


if __name__ == '__main__':
    r = build()
    print(json.dumps({'anchor': r['mouth_anchor'], 'shapes': list(r['shapes'])}, indent=2))
