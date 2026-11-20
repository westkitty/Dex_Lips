"""Minimal, tested image/video + authored mouth sprites + timed cues -> H.264 MP4.

Scope: deterministic video/audio compositing proof. Does NOT generate cues from speech,
track faces automatically, make canonical mouth art, or provide the complete UI.
External tools: Pillow, FFmpeg (libx264 + AAC), ffprobe. No model weights or paid services.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
from fractions import Fraction
from PIL import Image

SHAPES = set('ABCDEFGHX')
IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp'}
VIDEO_SUFFIXES = {'.mp4', '.mov', '.webm', '.mkv'}


class ProofError(ValueError):
    """Invalid user input or unavailable proof-render capability."""


def run(*args: str, input: bytes | None = None) -> bytes:
    p = subprocess.run(list(args), input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
    if p.returncode:
        raise ProofError(f'{Path(args[0]).name} exit {p.returncode}: {p.stderr.decode(errors="replace")[-500:]}')
    return p.stdout


def need_tools() -> None:
    for name in ('ffmpeg', 'ffprobe'):
        if not shutil.which(name):
            raise ProofError(f'{name} required for MP4 export; source files unchanged')


def media_probe(path: Path) -> dict:
    raw = run('ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path))
    result = json.loads(raw)
    result['video'] = next((s for s in result.get('streams', []) if s['codec_type'] == 'video'), None)
    result['audio'] = next((s for s in result.get('streams', []) if s['codec_type'] == 'audio'), None)
    return result


def duration(probe: dict) -> float:
    try:
        return float(probe['format']['duration'])
    except (KeyError, TypeError, ValueError) as e:
        raise ProofError('Cannot determine media duration') from e


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_cues(path: Path, audio_duration: float) -> list[dict]:
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ProofError('Mouth-cue JSON file exceeds 2 MiB')
    obj = json.loads(path.read_text(encoding='utf-8'))
    cues = obj.get('mouthCues')
    if not isinstance(cues, list) or not cues or len(cues) > 10000:
        raise ProofError('Missing Rhubarb-style mouthCues; cannot infer speech from audio without an analyzer')
    end = 0.
    out = []
    for cue in cues:
        if not isinstance(cue, dict) or cue.get('value') not in SHAPES:
            raise ProofError('Unexpected cue value or structure')
        try:
            start, stop = float(cue['start']), float(cue['end'])
        except (ValueError, TypeError, KeyError) as e:
            raise ProofError('Invalid cue time') from e
        if not all(map(math.isfinite, (start, stop))) or start < 0 or stop <= start or start < end - 1e-6:
            raise ProofError('Overlapping, nonpositive or unordered mouth cues')
        if stop > audio_duration + 0.06:
            raise ProofError('Mouth cues exceed audio duration')
        out.append({'start': start, 'end': stop, 'value': cue['value']})
        end = stop
    return out


def cue_at(cues: list[dict], time: float) -> str:
    for cue in cues:
        if cue['start'] <= time < cue['end']:
            return cue['value']
    return 'X'


def load_rig(rig_path: Path, source: Path) -> tuple[dict, dict[str, Image.Image]]:
    if rig_path.stat().st_size > 256 * 1024:
        raise ProofError('Rig JSON exceeds 256 KiB')
    rig = json.loads(rig_path.read_text(encoding='utf-8'))
    if rig.get('source_sha256') != sha256(source):
        raise ProofError('Rig source SHA-256 differs from input; refusing to alter unrelated reference')
    manifest_path = Path(__file__).resolve().parents[2] / 'assets/references/SOURCE_MANIFEST.json'
    if manifest_path.is_file():
        known = json.loads(manifest_path.read_text(encoding='utf-8'))
        if sha256(source) in {v['sha256'] for v in known['assets']}:
            raise ProofError('Bundled reference artwork is not permitted in synthetic proof renderer')
    if rig.get('authority') not in ('synthetic_demo', 'approved_user_rig') or not rig.get('approved'):
        raise ProofError('Only synthetic or explicitly user-approved noncanonical mouth rigs are renderable')
    shapes = rig.get('shapes', {})
    if 'X' not in shapes:
        raise ProofError('Rig requires X (rest) mouth shape')
    anchor = rig.get('mouth_anchor', {})
    if not 0 <= float(anchor.get('x', -1)) <= 1 or not 0 <= float(anchor.get('y', -1)) <= 1:
        raise ProofError('Normalized mouth anchor must be in [0,1]')
    imgs = {}
    root = rig_path.parent.resolve()
    for shape, relative in shapes.items():
        if shape not in SHAPES or not isinstance(relative, str):
            raise ProofError('Invalid sprite mapping')
        dest = (root / relative).resolve()
        if root not in dest.parents:
            raise ProofError('Sprite path escapes rig folder')
        with Image.open(dest) as raw:
            if raw.format != 'PNG' or ('A' not in raw.getbands() and 'transparency' not in raw.info):
                raise ProofError('Mouth sprites must be transparent PNG images')
            if raw.width * raw.height > 1024 * 1024:
                raise ProofError('Mouth sprite exceeds 1024x1024 pixel budget')
            imgs[shape] = raw.convert('RGBA')
    return rig, imgs


def load_keyframes(path: Path | None, fallback: dict) -> list[dict]:
    if path is None:
        return [fallback | {'time': 0}]
    if path.stat().st_size > 256 * 1024:
        raise ProofError('Keyframe file exceeds 256 KiB')
    obj = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj, list) or not obj or len(obj) > 10000:
        raise ProofError('Keyframes must be a nonempty bounded list')
    last = -1.
    for k in obj:
        t = float(k['time'])
        if not math.isfinite(t) or t < 0 or t <= last:
            raise ProofError('Keyframes out of order')
        last = t
        for n in ('x', 'y'):
            if not 0 <= float(k[n]) <= 1:
                raise ProofError(f'Keyframe {n} outside normalized bounds')
    return obj


def interpolate(keyframes: list[dict], time: float) -> dict:
    if time <= float(keyframes[0]['time']):
        return keyframes[0]
    if time >= float(keyframes[-1]['time']):
        return keyframes[-1]
    for a, b in zip(keyframes, keyframes[1:]):
        if float(a['time']) <= time <= float(b['time']):
            alpha = (time - float(a['time'])) / (float(b['time']) - float(a['time']))
            return {n: float(a.get(n, 1 if n == 'scale' else 0)) + alpha * (float(b.get(n, 1 if n == 'scale' else 0)) - float(a.get(n, 1 if n == 'scale' else 0))) for n in ('x','y','scale','rotation_deg')}
    raise AssertionError('Unreachable interpolation state')


def composite(frame: Image.Image, sprite: Image.Image, anchor: dict) -> Image.Image:
    base = frame.copy()
    scale = float(anchor.get('scale', 1))
    if not 0.05 <= scale <= 10.:
        raise ProofError('Mouth scale out of supported range')
    width, height = max(1, int(sprite.width * scale)), max(1, int(sprite.height * scale))
    mouth = sprite.resize((width, height), Image.Resampling.LANCZOS)
    mouth = mouth.rotate(float(anchor.get('rotation_deg', 0)), resample=Image.Resampling.BICUBIC, expand=True)
    x = round(float(anchor['x']) * frame.width - mouth.width / 2)
    y = round(float(anchor['y']) * frame.height - mouth.height / 2)
    if base.mode != 'RGB':
        base = base.convert('RGB')
    base.paste(mouth, (x, y), mouth)
    return base


def output_dimensions(source_w: int, source_h: int) -> tuple[int, int, float]:
    """Fit arbitrary portrait/landscape source within 1280x720, retaining original bytes.

    H.264 yuv420p requires even dimensions. Return source-pixel to output-pixel
    scale to preserve authored mouth-sprite proportions after resampling.
    """
    if source_w < 2 or source_h < 2 or source_w * source_h > 35_000_000:
        raise ProofError('Input dimensions outside safety budget')
    factor = min(1.0, 1280 / source_w, 720 / source_h)
    width = max(2, int(source_w * factor) // 2 * 2)
    height = max(2, int(source_h * factor) // 2 * 2)
    return width, height, min(width / source_w, height / source_h)


COVER_MODES = ('none', 'patch', 'inpaint')


def _cover_box(anchor: dict, sw: int, sh: int, cover: dict) -> tuple[int, int, int, int]:
    cw = max(2, int(float(cover.get('width', .12)) * sw))
    ch = max(2, int(float(cover.get('height', .06)) * sh))
    cx = float(anchor['x']) * sw + float(cover.get('offset_x', 0)) * sw
    cy = float(anchor['y']) * sh + float(cover.get('offset_y', 0)) * sh
    x0 = max(0, int(cx - cw / 2)); y0 = max(0, int(cy - ch / 2))
    return x0, y0, min(sw, x0 + cw), min(sh, y0 + ch)


def cover_mouth(frame: Image.Image, anchor: dict, cover: dict) -> Image.Image:
    """Opt-in: hide the source's original mouth before the overlay.

    'patch' fills a feathered ellipse with the median colour of a ring around
    it (deterministic, no dependencies). 'inpaint' uses OpenCV Telea inpainting
    when opencv-python(-headless) is installed; otherwise it is BLOCKED.
    This is a cosmetic cover, not mouth detection or tracking: the region
    follows the same anchor/keyframes as the overlay.
    """
    mode = cover.get('mode', 'none')
    if mode == 'none':
        return frame
    if mode not in COVER_MODES:
        raise ProofError('Unknown mouth cover mode')
    from PIL import ImageDraw, ImageFilter
    sw, sh = frame.size
    x0, y0, x1, y1 = _cover_box(anchor, sw, sh, cover)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return frame
    mask = Image.new('L', (sw, sh), 0)
    ImageDraw.Draw(mask).ellipse((x0, y0, x1 - 1, y1 - 1), fill=255)
    if mode == 'inpaint':
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise ProofError('Inpaint cover BLOCKED: install opencv-python-headless, or choose the patch cover') from exc
        arr = np.asarray(frame.convert('RGB'))
        out = cv2.inpaint(arr, np.asarray(mask), max(3, (y1 - y0) // 3), cv2.INPAINT_TELEA)
        return Image.fromarray(out)
    pad_x, pad_y = max(2, (x1 - x0) // 4), max(2, (y1 - y0) // 4)
    ring = []
    rgb = frame.convert('RGB')
    for x in range(max(0, x0 - pad_x), min(sw, x1 + pad_x), max(1, (x1 - x0) // 16)):
        for y in (max(0, y0 - pad_y), min(sh - 1, y1 + pad_y - 1)):
            ring.append(rgb.getpixel((x, y)))
    for y in range(max(0, y0 - pad_y), min(sh, y1 + pad_y), max(1, (y1 - y0) // 8)):
        for x in (max(0, x0 - pad_x), min(sw - 1, x1 + pad_x - 1)):
            ring.append(rgb.getpixel((x, y)))
    colour = tuple(sorted(c[i] for c in ring)[len(ring) // 2] for i in range(3))
    feather = mask.filter(ImageFilter.GaussianBlur(max(1, (y1 - y0) / 8)))
    out = rgb.copy()
    out.paste(Image.new('RGB', (sw, sh), colour), (0, 0), feather)
    return out


def render(source: Path, audio: Path, rig_path: Path, cues_path: Path, output: Path, keyframes_path: Path | None = None, fps: int = 24,
           *, crossfade_sec: float = 0.0, cover: dict | None = None,
           window: tuple[float, float] | None = None) -> dict:
    """Render an MP4. Optional, deterministic extras:

    crossfade_sec: blend the previous and next mouth sprite over this many
        seconds after each shape change (0 = hard cuts, the original behaviour).
    cover: {'mode': 'patch'|'inpaint', 'width': frac, 'height': frac} hides the
        original mouth region under the overlay (opt-in).
    window: (start_sec, length_sec) renders only that slice (preview).
    """
    need_tools()
    cover = cover or {'mode': 'none'}
    if cover.get('mode', 'none') not in COVER_MODES:
        raise ProofError('Unknown mouth cover mode')
    if not 0 <= float(crossfade_sec) <= 0.25:
        raise ProofError('Crossfade must be between 0 and 0.25 seconds')
    if output.exists():
        raise ProofError('Destination exists; output will not be overwritten')
    if not 1 <= fps <= 60:
        raise ProofError('FPS out of range 1..60')
    if not all(p.is_file() for p in (source, audio, rig_path, cues_path)):
        raise ProofError('Required input missing')
    for name, file in [('source', source), ('audio', audio)]:
        if file.stat().st_size > 40 * 1024 * 1024:
            raise ProofError(f'{name} file exceeds 40 MiB')
    audio_info = media_probe(audio)
    if not audio_info['audio']:
        raise ProofError('Audio input has no audio stream')
    seconds = duration(audio_info)
    if not 0.15 <= seconds <= 30.:
        raise ProofError('Proof renderer supports 0.15-30s audio')
    is_video = source.suffix.lower() in VIDEO_SUFFIXES
    if not is_video and source.suffix.lower() not in IMAGE_SUFFIXES:
        raise ProofError('Unsupported source type')
    rig, sprites = load_rig(rig_path, source)
    cues = load_cues(cues_path, seconds)
    if any(c['value'] not in sprites for c in cues):
        raise ProofError('Missing mouth sprite used by cues; cannot silently substitute')
    keyframes = load_keyframes(keyframes_path, rig['mouth_anchor'])
    offset = 0.0
    span = seconds
    if window is not None:
        offset, length = float(window[0]), float(window[1])
        if not (math.isfinite(offset) and math.isfinite(length)) or offset < 0 or length <= 0:
            raise ProofError('Invalid preview window')
        offset = min(offset, max(0.0, seconds - 0.15))
        span = min(length, seconds - offset)
    frame_count = max(1, round(span * fps))
    decoder = None
    still = None
    if is_video:
        probe = media_probe(source)
        if not probe['video']:
            raise ProofError('Video input missing video stream')
        stream = probe['video']
        input_w, input_h = int(stream['width']), int(stream['height'])
        sw, sh, sprite_scale = output_dimensions(input_w, input_h)
        src_fps = float(Fraction(stream['avg_frame_rate']))
        nominal_fps = float(Fraction(stream['r_frame_rate']))
        if abs(src_fps - nominal_fps) > 0.05:
            raise ProofError('Variable frame-rate source not supported in proof renderer')
        if abs(src_fps - fps) > 0.05:
            raise ProofError(f'Source FPS is {src_fps}; supply matching --fps; no silent frame-rate conversion')
        if abs(duration(probe) - seconds) > max(0.08, 2 / fps):
            raise ProofError('Video/audio duration mismatch; correct timing before rendering')
        decode_cmd = ['ffmpeg','-v','error'] + (['-ss', f'{offset:.3f}'] if offset else []) + ['-i',str(source),'-an']
        if (input_w, input_h) != (sw, sh):
            decode_cmd += ['-vf', f'scale={sw}:{sh}:flags=lanczos']
        decode_cmd += ['-f','rawvideo','-pix_fmt','rgb24','pipe:1']
        decoder = subprocess.Popen(decode_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    else:
        with Image.open(source) as image:
            input_w, input_h = image.size
            sw, sh, sprite_scale = output_dimensions(input_w, input_h)
            if (input_w, input_h) != (sw, sh):
                still = image.convert('RGB').resize((sw, sh), Image.Resampling.LANCZOS)
            else:
                still = image.convert('RGB')
    if sw % 2 or sh % 2:
        raise ProofError('H.264 proof renderer requires even dimensions')
    # Fast lookup avoids the former O(frames * cues) timing scan. Cache only
    # transformed mouth sprites, never full video frames, for bounded memory.
    cue_ends = [cue['end'] for cue in cues]
    frame_anchor_index = 0

    @lru_cache(maxsize=64)
    def transformed(shape: str, scale: float, rotation: float) -> Image.Image:
        if not 0.05 <= scale <= 10.0 or not math.isfinite(rotation):
            raise ProofError('Invalid mouth scale or rotation')
        sprite = sprites[shape]
        target = (max(1, int(sprite.width * scale * sprite_scale)),
                  max(1, int(sprite.height * scale * sprite_scale)))
        mouth = sprite.resize(target, Image.Resampling.LANCZOS)
        return mouth.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)

    def frame_anchor(t: float) -> dict:
        nonlocal frame_anchor_index
        while frame_anchor_index + 1 < len(keyframes) and t > float(keyframes[frame_anchor_index + 1]['time']):
            frame_anchor_index += 1
        if frame_anchor_index + 1 == len(keyframes):
            return keyframes[-1]
        a, b = keyframes[frame_anchor_index:frame_anchor_index + 2]
        start, end = float(a['time']), float(b['time'])
        alpha = min(1.0, max(0.0, (t - start) / (end - start)))
        return {n: float(a.get(n, 1 if n == 'scale' else 0)) +
                alpha * (float(b.get(n, 1 if n == 'scale' else 0)) - float(a.get(n, 1 if n == 'scale' else 0)))
                for n in ('x', 'y', 'scale', 'rotation_deg')}

    try:
        # One FFmpeg encode/mux process rather than creating and reading a
        # second silent MP4. The temporary stderr file prevents pipe deadlocks.
        with tempfile.TemporaryFile() as errors:
            encoder = subprocess.Popen([
                'ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                '-s', f'{sw}x{sh}', '-r', str(fps), '-i', 'pipe:0'] +
                (['-ss', f'{offset:.3f}', '-t', f'{span:.3f}'] if window is not None else []) + [
                '-i', str(audio), '-map', '0:v:0', '-map', '1:a:0',
                '-frames:v', str(frame_count), '-c:v', 'libx264',
                '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                # apad: the last video frame can end a few ms after the audio
                # (e.g. 2.99 s audio at 24 fps = 72 frames); pad the audio with
                # silence so -shortest no longer drops that final frame.
                '-af', 'apad', '-c:a', 'aac', '-shortest', '-movflags', '+faststart',
                '-n', str(output)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=errors)
            try:
                for index in range(frame_count):
                    if decoder is None:
                        frame = still
                    else:
                        data = decoder.stdout.read(sw * sh * 3)
                        if len(data) != sw * sh * 3:
                            raise ProofError(f'Source video ended prematurely at frame {index}')
                        frame = Image.frombytes('RGB', (sw, sh), data)
                    t = offset + index / fps
                    cue_index = bisect_right(cue_ends, t)
                    in_cue = cue_index < len(cues) and cues[cue_index]['start'] <= t
                    shape = cues[cue_index]['value'] if in_cue else 'X'
                    anchor = frame_anchor(t)
                    out_frame = frame.copy()
                    if out_frame.mode != 'RGB':
                        out_frame = out_frame.convert('RGB')
                    out_frame = cover_mouth(out_frame, anchor, cover)
                    scale_r = (float(anchor.get('scale', 1)), float(anchor.get('rotation_deg', 0)))

                    def overlay(base: Image.Image, which: str) -> Image.Image:
                        if which not in sprites:
                            which = 'X'
                        mouth = transformed(which, *scale_r)
                        x = round(float(anchor['x']) * sw - mouth.width / 2)
                        y = round(float(anchor['y']) * sh - mouth.height / 2)
                        result = base.copy()
                        result.paste(mouth, (x, y), mouth)
                        return result

                    blend_from = None
                    if crossfade_sec > 0 and in_cue and cue_index > 0:
                        since = t - cues[cue_index]['start']
                        prev = cues[cue_index - 1]
                        if since < crossfade_sec and prev['value'] != shape and abs(prev['end'] - cues[cue_index]['start']) < 1e-6:
                            blend_from = (prev['value'], since / crossfade_sec)
                    if blend_from is None:
                        out_frame = overlay(out_frame, shape)
                    else:
                        out_frame = Image.blend(overlay(out_frame, blend_from[0]), overlay(out_frame, shape), blend_from[1])
                    try:
                        encoder.stdin.write(out_frame.tobytes())
                    except BrokenPipeError as error:
                        raise ProofError('FFmpeg encoder stopped accepting video frames') from error
            finally:
                if encoder.stdin and not encoder.stdin.closed:
                    encoder.stdin.close()
                try:
                    rc = encoder.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    encoder.kill()
                    encoder.wait()
                    raise ProofError('Encoder timed out')
            if rc:
                errors.seek(0)
                raise ProofError(f'Encoder failed: {errors.read().decode(errors="replace")[-500:]}')
        output_info = media_probe(output)
        if not output_info['video'] or not output_info['audio']:
            raise ProofError('Output does not contain both video and audio')
        out_duration = duration(output_info)
        if abs(out_duration - span) > (2 / fps):
            raise ProofError('Output A/V duration drift exceeds two frames')
        observed_frames = output_info['video'].get('nb_frames')
        if observed_frames is not None and int(observed_frames) != frame_count:
            raise ProofError('Output frame count differs from source/timing contract')
        return {'mode':'video' if is_video else 'still','output_size':[sw,sh],
                'source_size':[input_w,input_h], 'output_scale':round(sprite_scale,6),
                'source_sha256':sha256(source),'output_sha256':sha256(output),'fps':fps,'frames_expected':frame_count,'frames_observed':int(observed_frames) if observed_frames is not None else None,'audio_duration_sec':round(seconds,3),'preview_window':[round(offset,3),round(span,3)] if window is not None else None,'crossfade_sec':float(crossfade_sec),'mouth_cover':cover.get('mode','none'),'output_duration_sec':round(out_duration,3),'video_codec':output_info['video']['codec_name'],'audio_codec':output_info['audio']['codec_name'],'cue_source':'EXTERNAL_JSON_UNVERIFIED_AUDIO_ALIGNMENT','claims':'COMPOSITING_PROVEN_NOT_AUTOMATIC_SPEECH_SYNC'}
    except Exception:
        # The destination was proved absent before this invocation; remove only
        # an incomplete file created by our own failed render.
        if output.exists():
            output.unlink()
        raise
    finally:
        if decoder is not None:
            if decoder.poll() is None:
                decoder.terminate()
            decoder.wait(timeout=10)
            if decoder.stdout is not None:
                decoder.stdout.close()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'audio', 'rig', 'cues', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--keyframes', type=Path)
    p.add_argument('--fps', type=int, default=24)
    a = p.parse_args()
    try:
        print(json.dumps(render(a.source, a.audio, a.rig, a.cues, a.output, a.keyframes, a.fps),indent=2))
    except (ProofError, FileNotFoundError, OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        p.error(str(e))

if __name__ == '__main__':
    main()
