"""Make ordinary phone videos renderable without silently changing timing.

Phones record variable frame rate (VFR) or 29.97/59.94 fps, and the replacement
speech is rarely exactly as long as the clip. ``prepare_video`` produces a NEW
constant-frame-rate working copy (the upload is never modified) and reconciles
the lengths using the user's explicit choice:

- 'strict': no change; mismatched lengths are an error (original behaviour)
- 'trim':   cut the longer of video/audio to the shorter one
- 'pad':    extend the shorter one (hold the last video frame / add silence)

Every change is listed in the returned report so the receipt can show it.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import subprocess

from .proof_render import ProofError, duration, media_probe, need_tools

LENGTH_POLICIES = ('strict', 'trim', 'pad')


def _run(cmd: list[str], timeout: int = 300) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    if p.returncode:
        raise ProofError(f'FFmpeg preparation failed: {p.stderr.decode(errors="replace")[-400:]}')


def choose_fps(stream: dict) -> tuple[int, bool]:
    """Return (integer CFR target, needs_conversion)."""
    try:
        avg = float(Fraction(stream.get('avg_frame_rate', '0/1')))
        nominal = float(Fraction(stream.get('r_frame_rate', '0/1')))
    except (ZeroDivisionError, ValueError):
        avg = nominal = 0.0
    rate = avg or nominal
    if rate <= 0:
        raise ProofError('Cannot determine the video frame rate')
    target = max(1, min(60, round(rate)))
    vfr = abs(avg - nominal) > 0.05
    fractional = abs(rate - round(rate)) > 0.01
    return target, (vfr or fractional or target != rate)


def prepare_video(source: Path, audio: Path, workdir: Path, *, policy: str = 'strict',
                  normalize_fps: bool = True) -> tuple[Path, Path, dict]:
    """Return (video_for_render, audio_for_render, report). Never edits inputs."""
    if policy not in LENGTH_POLICIES:
        raise ProofError('Unknown length policy')
    need_tools()
    probe = media_probe(source)
    stream = probe.get('video')
    if not stream:
        raise ProofError('Input video has no video stream')
    a_probe = media_probe(audio)
    if not a_probe.get('audio'):
        raise ProofError('Audio file contains no audio stream')
    v_len, a_len = duration(probe), duration(a_probe)
    fps, convert = choose_fps(stream)
    report = {'source_fps': stream.get('avg_frame_rate'), 'render_fps': fps,
              'fps_converted': False, 'video_sec_in': round(v_len, 3), 'audio_sec_in': round(a_len, 3),
              'length_policy': policy, 'changes': []}
    tolerance = max(0.08, 2 / fps)
    mismatch = abs(v_len - a_len) > tolerance
    if convert and not normalize_fps:
        raise ProofError(f'Variable/fractional FPS ({stream.get("avg_frame_rate")}) needs conversion; '
                         'enable constant-frame-rate normalization')
    if mismatch and policy == 'strict':
        raise ProofError(f'Video is {v_len:.2f}s but audio is {a_len:.2f}s. Choose "trim" or "pad" '
                         'to reconcile, or edit the media first.')
    if not convert and not mismatch:
        return source, audio, report
    target = a_len
    out_audio = audio
    if mismatch and policy == 'trim':
        target = min(v_len, a_len)
        if a_len > target + 1e-3:
            out_audio = workdir / 'speech_trimmed.wav'
            _run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(audio), '-map', '0:a:0', '-t', f'{target:.3f}',
                  '-c:a', 'pcm_s16le', '-n', str(out_audio)])
            report['changes'].append(f'audio trimmed from {a_len:.2f}s to {target:.2f}s')
        if v_len > target + 1e-3:
            report['changes'].append(f'video trimmed from {v_len:.2f}s to {target:.2f}s')
    elif mismatch and policy == 'pad':
        target = max(v_len, a_len)
        if a_len < target - 1e-3:
            out_audio = workdir / 'speech_padded.wav'
            _run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(audio), '-map', '0:a:0',
                  '-af', f'apad=whole_dur={target:.3f}', '-c:a', 'pcm_s16le', '-n', str(out_audio)])
            report['changes'].append(f'audio padded with silence from {a_len:.2f}s to {target:.2f}s')
        if v_len < target - 1e-3:
            report['changes'].append(f'video extended by holding the last frame from {v_len:.2f}s to {target:.2f}s')
    vf = [f'fps={fps}']
    if mismatch and policy == 'pad' and v_len < target:
        vf.append(f'tpad=stop_mode=clone:stop_duration={target - v_len + 0.2:.3f}')
    out_video = workdir / 'source_cfr.mp4'
    _run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(source), '-map', '0:v:0', '-an',
          '-vf', ','.join(vf), '-t', f'{target:.3f}', '-r', str(fps), '-fps_mode', 'cfr',
          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', '-n', str(out_video)])
    if convert:
        report['fps_converted'] = True
        report['changes'].append(f'frame rate normalized from {stream.get("avg_frame_rate")} to constant {fps} fps')
    report['video_sec_out'] = round(duration(media_probe(out_video)), 3)
    report['audio_sec_out'] = round(duration(media_probe(out_audio)), 3)
    return out_video, out_audio, report
