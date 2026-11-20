"""Dex_Lips local/private Gradio studio for the deterministic lip-sync route.

Start with `python3 app.py`; binds only to 127.0.0.1, not a public Space.
An installed Rhubarb binary enables genuine speech-derived cues; without it,
manual, explicitly authored cues are supported and labeled honestly.
"""
from __future__ import annotations

import json
import subprocess
import zipfile
from PIL import UnidentifiedImageError, Image
from pathlib import Path
import sys
from fractions import Fraction

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

from dex_lips.proof_render import ProofError, duration, load_cues, media_probe, render
from dex_lips.jobs import (ALLOWED_MEDIA, ALLOWED_AUDIO, MAX_SOURCE_BYTES,
                           MAX_AUDIO_BYTES, atomic_job_directory, prune_expired,
                           stage_upload, unpack_user_rig)
from dex_lips.speech import analyze, rhubarb_available
from dex_lips.mouth_asset_generator import create_draft_mouth_rig, MouthAssetError


def input_report(source_path, audio_path):
    if not source_path or not audio_path:
        return 'Upload an image or video AND the actual speech audio.'
    try:
        src = Path(source_path)
        audio = Path(audio_path)
        if src.stat().st_size > MAX_SOURCE_BYTES or audio.stat().st_size > MAX_AUDIO_BYTES:
            raise ProofError('File too large for this limited renderer')
        ap = media_probe(audio)
        if not ap['audio']:
            raise ProofError('Audio file contains no audio stream')
        seconds = duration(ap)
        if not .15 <= seconds <= 30.:
            raise ProofError('Audio duration must be 0.15-30s')
        return f'Source: {src.name} ({src.stat().st_size:,} bytes). Speech audio: {seconds:.2f}s. Automatic recognition available: {rhubarb_available()}. '
    except (ProofError, OSError, ValueError) as exc:
        return f'Input error: {exc}'


def analyze_uploaded(audio_path, dialog, recognizer):
    if not audio_path:
        return '', 'Attach a speech recording first.'
    prune_expired()
    job = atomic_job_directory()
    try:
        audio = stage_upload(Path(audio_path), job, 'speech', ALLOWED_AUDIO, MAX_AUDIO_BYTES)
        result = analyze(audio, job / 'mouthCues.json', dialog=dialog or '', recognizer=recognizer)
        return (job / 'mouthCues.json').read_text(encoding='utf-8'), f'Rhubarb analyzed the actual audio: {result["cue_count"]} cues. Review and adjust the timings below.'
    except (ProofError, OSError, ValueError, json.JSONDecodeError) as exc:
        return '', f'Automatic analysis unavailable: {exc}. You may instead paste reviewed Rhubarb-style JSON below.'


def render_uploaded(source_path, audio_path, archive_path, cues_text, keyframe_text,
                    xpos, ypos, size, angle, fps, approved, source_video_neutral):
    if not source_path or not audio_path or not archive_path:
        return None, None, None, 'Required: source image/video, speech audio, and ZIP of separately authored mouth sprites.'
    if not cues_text or not cues_text.strip():
        return None, None, None, 'Provide real Rhubarb-generated cues or edited manual mouthCues JSON. No fabricated auto-synchronization.'
    if not approved:
        return None, None, None, 'Confirm that you have permission to use your mouth artwork and footage for this job.'
    prune_expired()
    job = atomic_job_directory()
    try:
        source = stage_upload(Path(source_path), job, 'source', ALLOWED_MEDIA, MAX_SOURCE_BYTES)
        audio = stage_upload(Path(audio_path), job, 'speech', ALLOWED_AUDIO, MAX_AUDIO_BYTES)
        is_video = source.suffix.lower() in {'.mp4', '.mov', '.webm', '.mkv'}
        if is_video and not source_video_neutral:
            raise ProofError('Existing video may contain a moving mouth. Confirm it is neutral or masked; this renderer does not remove existing lip motion automatically.')
        anchor = {'x': float(xpos), 'y': float(ypos),
                  'scale': float(size), 'rotation_deg': float(angle)}
        rig = unpack_user_rig(Path(archive_path), source, job, anchor, user_approved=bool(approved))
        cues = job / 'mouthCues.json'
        if len(cues_text) > 240000:
            raise ProofError('Mouth cue JSON exceeds size limit')
        cues.write_text(cues_text, encoding='utf-8')
        secs = duration(media_probe(audio))
        used = load_cues(cues, secs)
        keys = None
        if keyframe_text and keyframe_text.strip():
            if len(keyframe_text) > 100000:
                raise ProofError('Keyframe JSON too large')
            keys = job / 'keyframes.json'
            keys.write_text(keyframe_text, encoding='utf-8')
        requested_fps = int(fps)
        if is_video:
            v = media_probe(source)['video']
            if not v:
                raise ProofError('Input video has no video stream')
            source_fps = float(Fraction(v['avg_frame_rate']))
            if abs(source_fps - round(source_fps)) > 0.01:
                raise ProofError(f'Variable/fractional FPS {source_fps:.3f} not supported; transcode to integer CFR before import.')
            requested_fps = round(source_fps)
        output = job / 'lip_synced.mp4'
        receipt = render(source, audio, rig, cues, output, keyframes_path=keys, fps=requested_fps)
        receipt['mouth_cue_provenance'] = 'USER_REVIEWED_JSON_OR_RHUBARB_OUTPUT_NOT_INDEPENDENTLY_PROVEN'
        receipt['source_video_original_mouth'] = 'USER_CONFIRMED_NEUTRAL_OR_MASKED' if is_video else 'NOT_APPLICABLE'
        receipt['provider'] = 'LOCAL_PROCESSING_ONLY_NO_CLOUD_UPLOAD'
        receipt['spend_usd'] = 0
        receipt['user_art_canon_status'] = 'UNVERIFIED_BY_APPLICATION'
        result = job / 'receipt.json'
        result.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        return str(output), str(output), str(result), ('Rendered and verified H.264/AAC MP4. Mouth timing follows supplied cues; accurate recognition only when cues actually came from Rhubarb. '
                                                        f'{len(used)} cues used. Source art unchanged.')
    except (ProofError, OSError, ValueError, json.JSONDecodeError, KeyError,
            ZeroDivisionError, zipfile.BadZipFile, UnidentifiedImageError,
            Image.DecompressionBombError, subprocess.TimeoutExpired) as exc:
        import shutil
        shutil.rmtree(job, ignore_errors=True)
        return None, None, None, f'Render blocked: {exc}'


def generate_mouth_assets(source_path, x, y, width, height, style, frame_time):
    if not source_path:
        return None, None, None, 'Upload a still image or existing video first.'
    prune_expired()
    job = atomic_job_directory()
    try:
        source = stage_upload(Path(source_path), job, 'source', ALLOWED_MEDIA, MAX_SOURCE_BYTES)
        generated = create_draft_mouth_rig(
            source, job / 'generated_mouth_assets',
            mouth_x=float(x), mouth_y=float(y),
            width_fraction=float(width), height_fraction=float(height),
            preset=str(style), frame_time=float(frame_time),
        )
        return (str(generated['preview']), str(generated['zip']),
                str(generated['zip']),
                'Generated X/A-F/G/H transparent draft sprites, preview and rig ZIP. '
                'X is transparent to retain the existing rest face. Review the preview, '
                'adjust placement or style, and explicitly approve artwork for this job '
                'before rendering. This is NOT anatomical recognition, automatic mouth removal, '
                'or canonical character-art approval.')
    except (MouthAssetError, ProofError, OSError, ValueError, subprocess.TimeoutExpired,
            UnidentifiedImageError, Image.DecompressionBombError) as exc:
        import shutil
        shutil.rmtree(job, ignore_errors=True)
        return None, None, None, f'Mouth asset generation blocked: {exc}'



def demo_render():
    from scripts.proof_smoke import run_smoke
    prune_expired()
    job = atomic_job_directory()
    try:
        result = run_smoke(job)
        return (str(job / 't3_still_proof.mp4'), str(job / 't4_moving_proof.mp4'),
                str(job / 'proof_receipt.json'),
                'Synthetic compositor tests passed. This is NOT real speech recognition or a canonical character animation.')
    except (ProofError, OSError, ValueError) as exc:
        return None, None, None, f'Self-test failed: {exc}'


def build():
    import gradio as gr
    with gr.Blocks(title='Dex_Lips — Private Lip-Sync Studio', delete_cache=(3600, 3600)) as app:
        gr.Markdown('# Dex_Lips  ·  Private Lip-Sync Studio\n'
                    'No AI model downloads. No paid processing. This server is bound to your own machine. '
                    'Automatic audio recognition requires an installed Rhubarb binary. '
                    '**Generate editable draft mouth sprites inside the app, or import your own approved sprite ZIP. Generated artwork requires visual review and is never automatic canon approval.**')
        with gr.Tab('Render'):
            with gr.Row():
                source = gr.File(label='Source image OR existing video', file_types=['.png','.jpg','.jpeg','.webp','.mp4','.mov','.webm','.mkv'])
                audio = gr.Audio(label='Actual spoken audio (30s max)', sources=['upload'], type='filepath')
            report = gr.Markdown('Import both source and audio to inspect input.')
            source.change(input_report, [source,audio], [report])
            audio.change(input_report, [source,audio], [report])
            gr.Markdown('### Make mouth assets here (no separate sprites required)\n'
                        'Select an approximate mouth center and dimensions, choose a source-matched graphic style, '
                        'then generate nine editable transparent PNGs and a ZIP. Review the open-mouth preview before use. '
                        'No facial anatomy, teeth or lips are inferred; the result is a proposed overlay, not approval.')
            with gr.Row():
                g_x = gr.Slider(.03,.97,value=.5,step=.005,label='Mouth center X')
                g_y = gr.Slider(.03,.97,value=.6,step=.005,label='Mouth center Y')
            with gr.Row():
                g_width = gr.Slider(.02,.35,value=.13,step=.005,label='Mouth width / frame width')
                g_height = gr.Slider(.015,.25,value=.065,step=.005,label='Mouth height / frame height')
                g_style = gr.Radio(['soft','faceted'],value='soft',label='Mouth graphic style')
                g_time = gr.Slider(0,30,value=0,step=.1,label='Reference frame second (video only)')
            gen_btn = gr.Button('Generate draft mouth assets from source',variant='secondary')
            with gr.Row():
                gen_preview = gr.Image(label='Source preview with generated open mouth',interactive=False)
                gen_download = gr.File(label='Download generated mouth rig ZIP')
            gen_status = gr.Markdown()
            sprite_zip = gr.File(label='Mouth rig ZIP: use generated ZIP or upload your own transparent PNGs', file_types=['.zip'])
            gen_btn.click(generate_mouth_assets,
                          [source,g_x,g_y,g_width,g_height,g_style,g_time],
                          [gen_preview,gen_download,sprite_zip,gen_status],concurrency_limit=1)
            with gr.Row():
                recognizer = gr.Radio(['pocketSphinx','phonetic'], value='pocketSphinx', label='Rhubarb recognizer', info='English / language-independent')
                dialog = gr.Textbox(label='Optional spoken transcript', lines=2, max_lines=4)
            analyze_btn = gr.Button('Analyze the actual audio with Rhubarb (if available)', variant='secondary')
            cues = gr.Code(language='json', label='Editable mouthCues JSON (generated or manual)', lines=10)
            analyze_result = gr.Markdown()
            analyze_btn.click(analyze_uploaded, [audio,dialog,recognizer],[cues,analyze_result])
            gr.Markdown('### Mouth placement (normalized to the source frame)')
            with gr.Row():
                x = gr.Slider(0,1,value=.5,step=.005,label='Mouth center X')
                y = gr.Slider(0,1,value=.6,step=.005,label='Mouth center Y')
                scale = gr.Slider(.05,4,value=1,step=.05,label='Mouth scale')
                angle = gr.Slider(-180,180,value=0,step=1,label='Rotation in degrees')
            keyframes = gr.Code(language='json', lines=5, label='Optional moving-video mouth-anchor keyframes JSON (for head motion)')
            fps = gr.Slider(12,30,step=1,value=24,label='Still-image output FPS; existing video uses its own integer FPS')
            granted = gr.Checkbox(label='I have permission to use these source files and have reviewed and approved the mouth sprites (generated or imported) FOR THIS JOB only. This does not grant canon approval.')
            neutral = gr.Checkbox(label='If the source is a video, its existing mouth is neutral/removed/masked; overlay will not duplicate a moving mouth.')
            submit = gr.Button('Render verified MP4', variant='primary')
            status = gr.Markdown()
            video = gr.Video(label='Rendered result', interactive=False)
            result_file = gr.File(label='Download MP4')
            receipt = gr.File(label='Download proof/limits receipt')
            submit.click(render_uploaded,[source,audio,sprite_zip,cues,keyframes,x,y,scale,angle,fps,granted,neutral],
                         [video,result_file,receipt,status], concurrency_limit=1)
        with gr.Tab('Offline synthetic self-test'):
            gr.Markdown('The self-test does not analyze speech: it proves two deterministic MP4 compositions from externally authored cues. No uploaded personal media used.')
            btn = gr.Button('Run synthetic test (still and moving-video)', variant='secondary')
            demo_still = gr.Video(label='Synthetic still → MP4')
            demo_move = gr.Video(label='Synthetic moving video → MP4')
            demo_receipt = gr.File(label='Proof receipt')
            demo_status = gr.Markdown()
            btn.click(demo_render,outputs=[demo_still,demo_move,demo_receipt,demo_status],concurrency_limit=1)
        gr.Markdown('**Limits:** Maximum 1280×720; 30-second audio; videos need integer constant frame rate and matched audio length. '
                    'The draft generator does not find or remove a mouth, recognize anatomy, produce approved Tiger shapes, or provide AI face generation/free hosted inference. Existing mouth animation still needs neutral/masked source art. '
                    'Scratch output is eligible for pruning after one hour on subsequent jobs and is removed at process exit; original uploads are never deleted.')
    return app


if __name__ == '__main__':
    build().launch(server_name='127.0.0.1', server_port=7860, share=False, inbrowser=False,
                   show_error=True)
