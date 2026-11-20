"""Source-conditioned, zero-cost draft mouth sprites for arbitrary 2D characters.

This is a deterministic artwork *proposal*, not automatic anatomical recognition,
identity verification, canonical approval, or mouth removal/tracking in video.
Source files are read-only. The ZIP is compatible with unpack_user_rig after the
user visually reviews it and explicitly confirms permission.
"""
from __future__ import annotations

from collections import Counter
from io import BytesIO
import hashlib
import json
import math
from pathlib import Path
import subprocess
import zipfile

from PIL import Image, ImageDraw, UnidentifiedImageError
from .source_geometry import trace_mouth, GeometryTraceError


class MouthAssetError(ValueError):
    """Unsafe source, unsupported frame, or invalid draft rig settings."""


IMAGE_EXTS = frozenset({'.png', '.jpg', '.jpeg', '.webp'})
VIDEO_EXTS = frozenset({'.mp4', '.mov', '.webm', '.mkv'})
MOUTH_SHAPES = 'XABCDEFGH'
PRESETS = frozenset({'soft', 'faceted', 'source-soft', 'source-faceted'})
MAX_SOURCE_BYTES = 40 * 1024 * 1024
MAX_PIXELS = 35_000_000
MAX_SPRITE_SIDE = 1024


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _protected_hashes() -> set[str]:
    manifest = Path(__file__).resolve().parents[2] / 'assets/references/SOURCE_MANIFEST.json'
    if not manifest.is_file():
        return set()
    try:
        obj = json.loads(manifest.read_text(encoding='utf-8'))
        return {entry['sha256'] for entry in obj['assets']}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise MouthAssetError('Canonical source manifest is unreadable; generation blocked') from exc


def _frame(source: Path, video_time: float) -> tuple[Image.Image, int, int]:
    if source.suffix.lower() in IMAGE_EXTS:
        try:
            with Image.open(source) as file:
                if file.width < 2 or file.height < 2 or file.width * file.height > MAX_PIXELS:
                    raise MouthAssetError('Source image dimensions exceed safety limits')
                image = file.convert('RGB')
                return image, image.width, image.height
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise MouthAssetError(f'Cannot decode source image: {exc}') from exc

    if source.suffix.lower() not in VIDEO_EXTS:
        raise MouthAssetError('Source must be an image or video')
    try:
        proc = subprocess.run(
            ['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{video_time:.3f}',
             '-i', str(source), '-map', '0:v:0', '-frames:v', '1',
             '-vf', "scale=w='min(960,iw)':h='min(720,ih)':force_original_aspect_ratio=decrease",
             '-f', 'image2pipe', '-vcodec', 'png', 'pipe:1'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25, check=False)
        if proc.returncode or not proc.stdout or len(proc.stdout) > 16 * 1024 * 1024:
            raise MouthAssetError('Could not extract a bounded reference frame from video')
        probe = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height', '-of', 'json', str(source)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12, check=False)
        if probe.returncode:
            raise MouthAssetError('Could not inspect video dimensions')
        streams = json.loads(probe.stdout)['streams']
        width, height = int(streams[0]['width']), int(streams[0]['height'])
        if width < 2 or height < 2 or width * height > MAX_PIXELS:
            raise MouthAssetError('Video frame dimensions exceed safety limits')
        with Image.open(BytesIO(proc.stdout)) as file:
            frame = file.convert('RGB')
        return frame, width, height
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError,
            KeyError, IndexError, ValueError, UnidentifiedImageError) as exc:
        if isinstance(exc, MouthAssetError):
            raise
        raise MouthAssetError('FFmpeg/ffprobe and a decodable video are required to sample video mouth art') from exc


def _color_sample(image: Image.Image, x: float, y: float, width_frac: float, height_frac: float) -> tuple[int, int, int]:
    """Sample surrounding paint, excluding the mouth interior; avoid guessing anatomy."""
    w, h = image.size
    cx, cy = int(x * w), int(y * h)
    rw = max(2, int(width_frac * w / 2))
    rh = max(2, int(height_frac * h / 2))
    candidates = []
    for dx, dy in ((-1.3, -1), (0, -1.35), (1.3, -1),
                   (-1.45, 0), (1.45, 0), (-1.3, 1), (0, 1.35), (1.3, 1)):
        xx = min(w - 1, max(0, cx + int(dx * rw)))
        yy = min(h - 1, max(0, cy + int(dy * rh)))
        candidates.append(image.getpixel((xx, yy)))
    # Quantized modal sample tolerates outlines and high-contrast stylized linework.
    bins = Counter(tuple((channel // 24) * 24 for channel in rgb) for rgb in candidates)
    best = bins.most_common(1)[0][0]
    matching = [rgb for rgb in candidates if all(abs(a - b) < 24 for a, b in zip(rgb, best))]
    values = matching or candidates
    return tuple(sorted(c[i] for c in values)[len(values) // 2] for i in range(3))


def _opening(shape: str) -> tuple[float, float]:
    # Width/height ratios of a bounded graphic area, not claims about anatomy.
    return {
        'A': (.66, .10), 'B': (.54, .30), 'C': (.76, .50),
        'D': (.83, .82), 'E': (.46, .80), 'F': (.39, .54),
        'G': (.75, .24), 'H': (.70, .15),
    }[shape]


def _draw_sprite(w: int, h: int, shape: str, preset: str, surround: tuple[int, int, int]) -> Image.Image:
    picture = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if shape == 'X':  # Show the original neutral mouth exactly; don't invent a rest face.
        return picture
    draw = ImageDraw.Draw(picture)
    mw, mh = _opening(shape)
    cx, cy = w // 2, h // 2
    half_w, half_h = max(2, int(w * mw * .46)), max(1, int(h * mh * .43))
    # Automatically chosen dark cavity and edge avoid human lips, teeth and tongue.
    cavity = tuple(max(0, min(255, int(v * .18))) for v in surround) + (255,)
    edge = tuple(max(4, min(255, int(v * .48))) for v in surround) + (255,)
    stroke = max(1, min(5, round(min(w, h) * .035)))
    if preset == 'faceted':
        pts = [(cx-half_w,cy), (cx-int(.70*half_w),cy-half_h),
               (cx,cy-int(.92*half_h)), (cx+int(.75*half_w),cy-half_h),
               (cx+half_w,cy), (cx+int(.65*half_w),cy+half_h),
               (cx,cy+int(.84*half_h)), (cx-int(.75*half_w),cy+half_h)]
        draw.polygon(pts, fill=cavity)
        draw.line(pts+[pts[0]], fill=edge, width=stroke, joint='curve')
    elif preset == 'soft':
        bbox = (cx-half_w, cy-half_h, cx+half_w, cy+half_h)
        draw.ellipse(bbox, fill=cavity, outline=edge, width=stroke)
    else:
        raise MouthAssetError('Unknown mouth style')
    return picture


def create_draft_mouth_rig(
    source: str | Path, destination: str | Path, *,
    mouth_x: float, mouth_y: float, width_fraction: float = .13,
    height_fraction: float = .065, preset: str = 'soft', frame_time: float = 0.0,
    contrast: str = 'auto',
) -> dict:
    """Create individual editable PNGs + review ZIP, with zero canonical approval.

    User selects mouth location and relative size. Source modes conservatively
    trace and warp existing mouth pixels; explicit graphic modes preserve
    the older colored-polygon/oval route. No model, fee, uploads or face detector.
    """
    source, destination = Path(source), Path(destination)
    if not source.is_file() or source.is_symlink() or not 1 <= source.stat().st_size <= MAX_SOURCE_BYTES:
        raise MouthAssetError('Source must be a real non-symlink file of at most 40 MiB')
    if source.suffix.lower() not in IMAGE_EXTS | VIDEO_EXTS:
        raise MouthAssetError('Unsupported image/video format')
    source_hash = _digest(source)
    if source_hash in _protected_hashes():
        raise MouthAssetError('Protected canonical/provisional reference: automated rig art requires separate visual approval')
    settings = (mouth_x, mouth_y, width_fraction, height_fraction, frame_time)
    if not all(isinstance(n, (int, float)) and math.isfinite(n) for n in settings):
        raise MouthAssetError('Mouth position and size must be finite')
    if not .03 <= mouth_x <= .97 or not .03 <= mouth_y <= .97:
        raise MouthAssetError('Mouth center too close to image boundary')
    if not .02 <= width_fraction <= .35 or not .015 <= height_fraction <= .25:
        raise MouthAssetError('Mouth region must use supported size fractions')
    if not 0 <= frame_time <= 30:
        raise MouthAssetError('Frame time must be between 0 and 30 seconds')
    if mouth_x - width_fraction / 2 < 0 or mouth_x + width_fraction / 2 > 1 or mouth_y - height_fraction / 2 < 0 or mouth_y + height_fraction / 2 > 1:
        raise MouthAssetError('Mouth region must fit within source frame')
    if preset not in PRESETS:
        raise MouthAssetError('Mouth style must be soft, faceted, source-soft or source-faceted')
    if contrast not in ('auto', 'dark', 'light'):
        raise MouthAssetError('Mouth contrast must be auto, dark or light')
    if destination.exists():
        raise MouthAssetError('Output folder exists; refusing to overwrite prior assets')
    frame, original_w, original_h = _frame(source, frame_time)
    width = max(8, round(width_fraction * original_w))
    height = max(8, round(height_fraction * original_h))
    if width > MAX_SPRITE_SIDE or height > MAX_SPRITE_SIDE or width * height > 1024 * 1024:
        raise MouthAssetError('Requested mouth asset exceeds 1024px limit; reduce width/height')
    diagnostic = None
    trace_report = None
    if preset.startswith('source-'):
        try:
            sprites, diagnostic, trace_report = trace_mouth(
                frame, x=mouth_x, y=mouth_y,
                width_fraction=width_fraction, height_fraction=height_fraction,
                output_size=(width, height), style=preset.removeprefix('source-'),
                contrast=contrast)
        except GeometryTraceError as exc:
            raise MouthAssetError(f'Source-traced mouth unavailable: {exc}') from exc
    else:
        palette = _color_sample(frame, mouth_x, mouth_y, width_fraction, height_fraction)
        sprites = {label: _draw_sprite(width, height, label, preset, palette)
                   for label in MOUTH_SHAPES}
    destination.mkdir(mode=0o700, parents=False)
    try:
        shapes = {}
        for label in MOUTH_SHAPES:
            path = destination / f'{label}.png'
            sprites[label].save(path, 'PNG')
            shapes[label] = path.name
        rig = {
            'schema_version': 1, 'character_id': 'generated-draft-review-required',
            'source_path': source.name, 'source_sha256': source_hash,
            'authority': 'generated_draft', 'approved': False,
            'mouth_anchor': {'x': mouth_x, 'y': mouth_y, 'scale': 1.0, 'rotation_deg': 0},
            'shapes': shapes,
            'notes': ('Draft mode: ' + preset + '; actual source-traced silhouette only when source-* selected. '
                      'No anatomy recognition or canonical approval. Visual review is mandatory. '
                      + (json.dumps(trace_report, sort_keys=True) if trace_report else 'Graphic shapes only.')),
        }
        rig_path = destination / 'rig.json'
        rig_path.write_text(json.dumps(rig, indent=2), encoding='utf-8')
        preview_frame = frame.copy().convert('RGBA')
        # Show a representative open shape in the uploaded source without altering it.
        patch = Image.open(destination / 'D.png').convert('RGBA')
        scaled = (max(1, round(width * frame.width / original_w)),
                  max(1, round(height * frame.height / original_h)))
        patch = patch.resize(scaled, Image.Resampling.LANCZOS)
        at = (round(mouth_x * frame.width - patch.width/2),
              round(mouth_y * frame.height - patch.height/2))
        preview_frame.alpha_composite(patch, dest=at)
        preview_path = destination / 'review_open_D.png'
        preview_frame.save(preview_path, 'PNG')
        trace_path = None
        if diagnostic is not None:
            trace_path = destination / 'review_traced_mouth.png'
            diagnostic.save(trace_path, 'PNG')
        archive_path = destination.parent / f'{destination.name}_draft_rig.zip'
        if archive_path.exists():
            raise MouthAssetError('Draft rig archive destination already exists')
        with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for label in MOUTH_SHAPES:
                archive.write(destination / f'{label}.png', f'{label}.png')
            archive.write(rig_path, 'rig.json')
        return {
            'zip': str(archive_path), 'preview': str(preview_path),
            'shapes': [str(destination / f'{letter}.png') for letter in MOUTH_SHAPES],
            'source_sha256': source_hash, 'draft_only': True,
            'sprite_dimensions': [width, height], 'preset': preset,
            'trace_diagnostic': str(trace_path) if trace_path else None,
            'trace_report': trace_report,
        }
    except Exception:
        # Caller owns bounded job cleanup; never delete the user's source.
        raise
