#!/usr/bin/env python3
"""Run two small synthetic media render checks, storing outputs only if requested.

This proves cue-driven composite + MP4/AAC. It does NOT prove Rhubarb audio
recognition, production tracking, neural models, UI, or Tiger mouth-art approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import wave
from math import pi, sin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dex_lips.proof_render import render, run, ProofError, media_probe
from PIL import Image, ImageDraw


def make_demo(where: Path) -> dict:
    where.mkdir(parents=True, exist_ok=True)
    W, H, fps, seconds = 320, 240, 24, 2
    audio = where / 'voice_fixture.wav'
    with wave.open(str(audio), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        # Artificial modulated tone, intentionally NOT claimed to be speech.
        data = bytearray()
        for n in range(16000 * seconds):
            t = n / 16000
            active = (0.32 <= t < 0.84) or (1.08 <= t < 1.66)
            value = int(8500 * (1 if active else 0) * sin(2*pi * (170 + 20*t)*t))
            data += int(value).to_bytes(2, 'little', signed=True)
        f.writeframes(data)
    cues = where / 'cues.json'
    cues.write_text(json.dumps({'metadata': {'duration': seconds, 'soundFile': audio.name},'mouthCues':[
        {'start':0.,'end':0.32,'value':'X'},
        {'start':0.32,'end':0.84,'value':'D'},
        {'start':0.84,'end':1.08,'value':'X'},
        {'start':1.08,'end':1.66,'value':'B'},
        {'start':1.66,'end':2.,'value':'X'}
    ]}, indent=2),encoding='utf-8')
    for kind, stroke in [('X',4),('D',18),('B',9)]:
        img = Image.new('RGBA', (46, 24), (0,0,0,0)); d=ImageDraw.Draw(img)
        d.ellipse((2,12-stroke//2,44,12+stroke//2), fill=(12,28,35,255), outline=(65,240,225,255), width=2)
        img.save(where / f'{kind}.png')

    def frame(center_x: float) -> Image.Image:
        img=Image.new('RGB',(W,H),(13,24,47));d=ImageDraw.Draw(img)
        d.ellipse((center_x-54,56,center_x+54,190), fill=(38,52,87), outline=(85,225,211), width=3)
        d.ellipse((center_x-24,92,center_x-14,102), fill=(102,235,238))
        d.ellipse((center_x+14,92,center_x+24,102), fill=(102,235,238))
        return img

    still=where/'synthetic_character.png'; frame(160).save(still)
    frames=where/'frames.rgb'
    with frames.open('wb') as f:
        for i in range(fps*seconds):
            f.write(frame(128 + 64 * i/(fps*seconds-1)).tobytes())
    moving=where/'synthetic_moving_video.mp4'
    run('ffmpeg','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}', '-framerate',str(fps),'-i',str(frames),'-c:v','libx264','-pix_fmt','yuv420p',str(moving))

    def rig_for(src: Path, stem: str, anchor_x:float) -> Path:
        sha=hashlib.sha256(src.read_bytes()).hexdigest()
        p=where / f'{stem}_rig.json'
        obj={'schema_version':1,'character_id':'proof-only-synthetic','source_path':src.name,'source_sha256':sha,'authority':'synthetic_demo','approved':True,'mouth_anchor':{'x':anchor_x,'y':.61,'scale':1.,'rotation_deg':0.},'shapes':{v:f'{v}.png' for v in 'XDB'},'notes':'Original synthetic proof geometry, not canon artwork'}
        p.write_text(json.dumps(obj,indent=2),encoding='utf-8')
        return p

    still_rig=rig_for(still,'still',.5)
    moving_rig=rig_for(moving,'moving',.4)
    track=where/'moving_keyframes.json'
    track.write_text(json.dumps([{'time':0.,'x':.4,'y':.61,'scale':1.}, {'time':2.,'x':.6,'y':.61,'scale':1.}],indent=2),encoding='utf-8')
    return {'still':still,'moving':moving,'still_rig':still_rig,'moving_rig':moving_rig,'cues':cues,'audio':audio,'track':track}


def run_smoke(where: Path) -> dict:
    source=make_demo(where)
    a=render(source['still'],source['audio'],source['still_rig'],source['cues'],where/'t3_still_proof.mp4',fps=24)
    b=render(source['moving'],source['audio'],source['moving_rig'],source['cues'],where/'t4_moving_proof.mp4',keyframes_path=source['track'],fps=24)
    # FFmpeg full stream decode, not just ffprobe header:
    for name in ['t3_still_proof.mp4','t4_moving_proof.mp4']:
        run('ffmpeg','-v','error','-xerror','-i',str(where/name),'-f','null','-')
    receipt={'status':'PROOF_PASSED_WITH_LIMITATIONS','T3_synthetic_cue_compositor':a,'T4_synthetic_keyframe_video_compositor':b,'not_proven':['Rhubarb speech detection','actual speech-to-mouth alignment','moving nonhuman face tracking','full user interface','hosted $0 availability','Tiger mouth approval','user video preservation beyond test fixture']}
    (where/'proof_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,help='Preserve outputs; default uses disposable temporary directory')
    a=p.parse_args()
    if a.output_dir:
        if a.output_dir.exists() and any(a.output_dir.iterdir()):
            p.error('Output directory must be empty to avoid overwriting user files')
        print(json.dumps(run_smoke(a.output_dir),indent=2))
    else:
        with tempfile.TemporaryDirectory(prefix='dex_lips_smoke_') as d:
            print(json.dumps(run_smoke(Path(d)),indent=2))

if __name__=='__main__':main()
