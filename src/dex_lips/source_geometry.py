"""Conservative source-mouth tracing for nonhuman and stylized 2-D artwork.

Pixel geometry and colors originate in a user-selected image region. This is
NOT a face detector, segmentation model, source repair, anatomy inference or
canonical approval. Reject ambiguous regions instead of silently falling back.
"""
from __future__ import annotations

from collections import deque
from statistics import median
from PIL import Image, ImageDraw, ImageFilter


class GeometryTraceError(ValueError):
    """No sufficiently isolated mouth silhouette was found at the selected point."""


SHAPE_SIZE = {
    'A': (.66, .10), 'B': (.54, .30), 'C': (.76, .50),
    'D': (.83, .82), 'E': (.46, .80), 'F': (.39, .54),
    'G': (.75, .24), 'H': (.70, .15),
}


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
                style: str = 'soft', contrast: str = 'auto') -> tuple[dict[str, Image.Image], Image.Image, dict]:
    """Create nine source-derived pose sprites and a trace diagnostic.

    Uses ROI relative to displayed frame (video frames may be downscaled).
    Every expression rescales the same detected asymmetric silhouette instead
    of replacing it with a human-like shape. No contour means no invented rig.
    """
    if style not in ('soft', 'faceted') or contrast not in ('auto', 'dark', 'light'):
        raise GeometryTraceError('Unknown style or contrast selection')
    full_w, full_h = frame.size
    if full_w < 2 or full_h < 2 or full_w * full_h > 35_000_000:
        raise GeometryTraceError('Frame outside geometry safety budget')
    frame = frame.convert('RGB')
    region_w = max(8, round(full_w * width_fraction))
    region_h = max(8, round(full_h * height_fraction))
    cx, cy = round(x * full_w), round(y * full_h)
    left = max(0, min(full_w - region_w, cx - region_w // 2))
    top = max(0, min(full_h - region_h, cy - region_h // 2))
    crop = frame.crop((left, top, left + region_w, top + region_h))
    downscale = min(1., 180 / region_w, 180 / region_h)
    sw, sh = max(8, round(region_w * downscale)), max(8, round(region_h * downscale))
    search = crop.resize((sw, sh), Image.Resampling.BOX) if (sw, sh) != crop.size else crop
    colors = list(search.getdata())
    lights = [_luma(p) for p in colors]
    rim = max(1, round(min(sw, sh) * .12))
    border = [lights[r * sw + c] for r in range(sh) for c in range(sw)
              if r < rim or r >= sh - rim or c < rim or c >= sw - rim]
    background = median(border)
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
                found.append((confidence, comp, polarity, (x0, y0, x1 + 1, y1 + 1), mean_contrast))
    if not found:
        raise GeometryTraceError('Cannot isolate the actual mouth in this region. Reposition/tighten the box or choose explicit graphic mode; no anatomy was invented.')
    found.sort(key=lambda v: v[0], reverse=True)
    confidence, component, polarity, bbox, mean_contrast = found[0]
    if len(found) > 1 and found[1][0] >= confidence - .035 and found[1][2] != polarity:
        raise GeometryTraceError('Mouth contrast is ambiguous; choose Dark or Light to constrain tracing.')
    mask_set = _fill_holes(set(component), sw, sh)
    traced_mask = Image.new('L', (sw, sh), 0)
    traced_mask.putdata([255 if index in mask_set else 0 for index in range(sw * sh)])
    traced_mask = traced_mask.resize((region_w, region_h), Image.Resampling.NEAREST)
    if style == 'soft':
        traced_mask = traced_mask.filter(ImageFilter.GaussianBlur(radius=.4))
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
    for label, (wr, hr) in SHAPE_SIZE.items():
        target_w = max(2, round(out_w * wr * .9))
        target_h = max(1, round(out_h * hr * .9))
        target_w = min(target_w, out_w)
        target_h = min(target_h, out_h)
        resampler = Image.Resampling.NEAREST if style == 'faceted' else Image.Resampling.LANCZOS
        warped = observed.resize((target_w, target_h), resampler)
        pose = Image.new('RGBA', (out_w, out_h), (0, 0, 0, 0))
        pose.alpha_composite(warped, ((out_w - target_w)//2, (out_h - target_h)//2))
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
        'review_required': True,
    }
