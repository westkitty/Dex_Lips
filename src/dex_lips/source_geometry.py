"""Conservative source-mouth tracing for nonhuman and stylized 2-D artwork.

Pixel geometry and colors originate in a user-selected image region. This is
NOT a face detector, segmentation model, source repair, anatomy inference or
canonical approval. Reject ambiguous regions instead of silently falling back.
"""
from __future__ import annotations

from collections import deque
import math
from PIL import Image, ImageDraw


class GeometryTraceError(ValueError):
    """No sufficiently isolated mouth silhouette was found at the selected point."""


SHAPE_SIZE = {
    'A': (.66, .10), 'B': (.54, .30), 'C': (.76, .50),
    'D': (.83, .82), 'E': (.46, .80), 'F': (.39, .54),
    'G': (.75, .24), 'H': (.70, .15),
}

# Construction modes: width/height ratio of each pose relative to the sprite
# box, plus where the pose is pinned. 'human' is the original centred table.
# Nonhuman modes pin the TOP edge (upper jaw / upper beak stays put and the
# lower jaw drops), which reads better on snouts than a centred human mouth.
# These are drawing conventions for a reviewed draft, not anatomy claims.
# Mirrored exactly in site/assets/trace_core.js (parity-tested).
JAW_MODES: dict[str, dict] = {
    'human': {'anchor': 'center', 'ratios': SHAPE_SIZE},
    'muzzle': {'anchor': 'top', 'ratios': {
        'A': (.70, .10), 'B': (.68, .26), 'C': (.70, .48), 'D': (.72, .80),
        'E': (.58, .62), 'F': (.50, .46), 'G': (.70, .20), 'H': (.68, .32)}},
    'beak': {'anchor': 'top', 'ratios': {
        'A': (.80, .08), 'B': (.80, .22), 'C': (.80, .42), 'D': (.80, .70),
        'E': (.74, .50), 'F': (.70, .38), 'G': (.80, .18), 'H': (.80, .30)}},
    'wide-jaw': {'anchor': 'top', 'ratios': {
        'A': (.90, .10), 'B': (.86, .30), 'C': (.92, .52), 'D': (.96, .86),
        'E': (.80, .66), 'F': (.70, .50), 'G': (.90, .24), 'H': (.88, .36)}},
}


def round_half_up(value: float) -> int:
    """JavaScript Math.round semantics (Python's round() is banker's rounding)."""
    return math.floor(value + 0.5)


def pose_box(out_w: int, out_h: int, label: str, jaw: str = 'human') -> tuple[int, int, int, int]:
    """(left, top, width, height) of pose `label` inside an out_w x out_h sprite."""
    mode = JAW_MODES[jaw]
    wr, hr = mode['ratios'][label]
    tw = min(out_w, max(2, round_half_up(out_w * wr * .9)))
    th = min(out_h, max(1, round_half_up(out_h * hr * .9)))
    left = (out_w - tw) // 2
    if mode['anchor'] == 'top':
        top = max(0, round_half_up(out_h * .05))
        top = min(top, out_h - th)
    else:
        top = (out_h - th) // 2
    return left, top, tw, th


def _median_upper(values: list[float]) -> float:
    """Upper median, identical to the browser implementation."""
    ordered = sorted(values)
    return ordered[len(ordered) // 2] if ordered else 0.0


def select_component(lights: list[float], sw: int, sh: int, contrast: str = 'auto'):
    """Pure tracing core shared (by parity test) with site/assets/trace_core.js.

    Returns (confidence, component_indices, polarity, bbox, mean_contrast) for
    the best candidate, or raises GeometryTraceError.
    """
    rim = max(1, round_half_up(min(sw, sh) * .12))
    border = [lights[r * sw + c] for r in range(sh) for c in range(sw)
              if r < rim or r >= sh - rim or c < rim or c >= sw - rim]
    background = _median_upper(border)
    found = []
    polarities = ('dark', 'light') if contrast == 'auto' else (contrast,)
    for polarity in polarities:
        diff = [background - n if polarity == 'dark' else n - background for n in lights]
        strength = max(diff)
        if strength < 25:
            continue
        threshold = max(23, .40 * strength)
        candidate = [v >= threshold for v in diff]
        for comp in _components(candidate, sw, sh):
            area = len(comp)
            if not max(4, sw * sh * .002) <= area <= sw * sh * .42:
                continue
            rows = [index // sw for index in comp]
            cols = [index % sw for index in comp]
            x0, x1, y0, y1 = min(cols), max(cols), min(rows), max(rows)
            bw, bh = x1 - x0 + 1, y1 - y0 + 1
            if x0 < 1 or x1 >= sw - 1 or y0 < 1 or y1 >= sh - 1:
                continue
            if bw / sw < .14 or bh / sh < .045 or bw / sw > .93 or bh / sh > .91:
                continue
            centre_x = sum(cols) / area
            centre_y = sum(rows) / area
            distance = ((centre_x - sw * .5) / sw) ** 2 + ((centre_y - sh * .5) / sh) ** 2
            if distance > .115:
                continue
            mean_contrast = sum(diff[i] for i in comp) / area
            clarity = min(1., mean_contrast / 90.)
            central = max(0., 1. - distance / .115)
            coverage = min(1., (bw / sw) / .4)
            confidence = .40 * clarity + .40 * central + .20 * coverage
            if confidence >= .57:
                found.append((confidence, sorted(comp), polarity, (x0, y0, x1 + 1, y1 + 1), mean_contrast))
    if not found:
        raise GeometryTraceError('Cannot isolate the actual mouth in this region. Reposition/tighten the box or choose explicit graphic mode; no anatomy was invented.')
    found.sort(key=lambda v: v[0], reverse=True)  # stable, like Array.prototype.sort
    if len(found) > 1 and found[1][0] >= found[0][0] - .035 and found[1][2] != found[0][2]:
        raise GeometryTraceError('Mouth contrast is ambiguous; choose Dark or Light to constrain tracing.')
    return found[0]


def upsample_index(x: int, y: int, region_w: int, region_h: int, sw: int, sh: int) -> int:
    """Search-grid index for region pixel (x, y); identical to the browser."""
    return min(sh - 1, (y * sh) // region_h) * sw + min(sw - 1, (x * sw) // region_w)


def _luma(pixel: tuple[int, int, int]) -> float:
    return (pixel[0] * 299 + pixel[1] * 587 + pixel[2] * 114) / 1000


def _components(candidates: list[bool], w: int, h: int):
    """Return bounded 8-connected components (including jagged diagonal lines)."""
    seen = bytearray(w * h)
    for start in range(w * h):
        if not candidates[start] or seen[start]:
            continue
        seen[start] = 1
        pending = deque([start])
        component = []
        while pending:
            index = pending.pop()
            component.append(index)
            row, col = divmod(index, w)
            for rr in (row - 1, row, row + 1):
                if rr < 0 or rr >= h:
                    continue
                for cc in (col - 1, col, col + 1):
                    if cc < 0 or cc >= w:
                        continue
                    j = rr * w + cc
                    if candidates[j] and not seen[j]:
                        seen[j] = 1
                        pending.append(j)
        yield component


def _fill_holes(pixels: set[int], w: int, h: int) -> set[int]:
    """Keep enclosed highlights/teeth within a detected cavity if present."""
    exterior = set()
    pending = deque()
    for col in range(w):
        for i in (col, (h - 1) * w + col):
            if i not in pixels and i not in exterior:
                exterior.add(i); pending.append(i)
    for row in range(h):
        for i in (row * w, row * w + w - 1):
            if i not in pixels and i not in exterior:
                exterior.add(i); pending.append(i)
    while pending:
        current = pending.popleft()
        row, col = divmod(current, w)
        for rr, cc in ((row-1,col), (row+1,col), (row,col-1), (row,col+1)):
            if 0 <= rr < h and 0 <= cc < w:
                j = rr * w + cc
                if j not in pixels and j not in exterior:
                    exterior.add(j); pending.append(j)
    return set(range(w * h)).difference(exterior)


def trace_mouth(frame: Image.Image, *, x: float, y: float, width_fraction: float,
                height_fraction: float, output_size: tuple[int, int],
                style: str = 'soft', contrast: str = 'auto',
                jaw: str = 'human') -> tuple[dict[str, Image.Image], Image.Image, dict]:
    """Create nine source-derived pose sprites and a trace diagnostic.

    Uses ROI relative to displayed frame (video frames may be downscaled).
    Every expression rescales the same detected asymmetric silhouette instead
    of replacing it with a human-like shape. No contour means no invented rig.
    """
    if style not in ('soft', 'faceted') or contrast not in ('auto', 'dark', 'light') or jaw not in JAW_MODES:
        raise GeometryTraceError('Unknown style or contrast selection')
    full_w, full_h = frame.size
    if full_w < 2 or full_h < 2 or full_w * full_h > 35_000_000:
        raise GeometryTraceError('Frame outside geometry safety budget')
    frame = frame.convert('RGB')
    region_w = max(8, round_half_up(full_w * width_fraction))
    region_h = max(8, round_half_up(full_h * height_fraction))
    left = max(0, min(full_w - region_w, round_half_up(x * full_w - region_w / 2)))
    top = max(0, min(full_h - region_h, round_half_up(y * full_h - region_h / 2)))
    crop = frame.crop((left, top, left + region_w, top + region_h))
    downscale = min(1., 180 / region_w, 180 / region_h)
    sw, sh = max(8, round_half_up(region_w * downscale)), max(8, round_half_up(region_h * downscale))
    search = crop.resize((sw, sh), Image.Resampling.BOX) if (sw, sh) != crop.size else crop
    lights = [_luma(p) for p in search.getdata()]
    confidence, component, polarity, bbox, mean_contrast = select_component(lights, sw, sh, contrast)
    mask_set = _fill_holes(set(component), sw, sh)
    # Same nearest-neighbour mapping as the browser (no extra blur: the former
    # GaussianBlur(0.4) existed only in Python and caused visible drift).
    traced_mask = Image.new('L', (region_w, region_h), 0)
    traced_mask.putdata([255 if upsample_index(xx, yy, region_w, region_h, sw, sh) in mask_set else 0
                         for yy in range(region_h) for xx in range(region_w)])
    source_alpha = crop.convert('RGBA')
    source_alpha.putalpha(traced_mask)
    rect = traced_mask.getbbox()
    if not rect:
        raise GeometryTraceError('No mouth pixels survived tracing')
    observed = source_alpha.crop(rect)
    out_w, out_h = output_size
    if out_w < 8 or out_h < 8 or out_w * out_h > 1024 * 1024:
        raise GeometryTraceError('Requested output dimensions exceed sprite safety budget')
    sprites = {'X': Image.new('RGBA', (out_w, out_h), (0, 0, 0, 0))}
    for label in SHAPE_SIZE:
        px, py, target_w, target_h = pose_box(out_w, out_h, label, jaw)
        resampler = Image.Resampling.NEAREST if style == 'faceted' else Image.Resampling.LANCZOS
        warped = observed.resize((target_w, target_h), resampler)
        pose = Image.new('RGBA', (out_w, out_h), (0, 0, 0, 0))
        pose.alpha_composite(warped, (px, py))
        sprites[label] = pose
    diagnostic = frame.copy().convert('RGBA')
    overlay = Image.new('RGBA', (region_w, region_h), (0, 0, 0, 0))
    overlay.paste((0, 255, 188, 150), (0, 0, region_w, region_h), traced_mask)
    diagnostic.alpha_composite(overlay, (left, top))
    ImageDraw.Draw(diagnostic).rectangle((left, top, left + region_w - 1, top + region_h - 1),
                                        outline=(255, 210, 0, 220), width=1)
    return sprites, diagnostic, {
        'mode': 'source-trace', 'confidence': round(confidence, 3),
        'contrast': polarity, 'source_bbox': [left, top, region_w, region_h],
        'mouth_bbox_in_roi': list(bbox), 'mean_contrast': round(mean_contrast, 1),
        'review_required': True, 'jaw_mode': jaw,
    }
