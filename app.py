"""Dex_Lips local/private Gradio studio for the deterministic lip-sync route.

Start with `python3 app.py`; binds only to 127.0.0.1, not a public Space.
Automatic cues come from a real engine that actually ran on the audio: the
Rhubarb Lip Sync CLI and/or the wav2vec2 phoneme recognizer. If neither is
available, automatic recognition is BLOCKED; manual, explicitly authored cues
are still supported and labeled honestly.
"""
from __future__ import annotations

import json
import subprocess
import zipfile
from PIL import UnidentifiedImageError, Image, ImageDraw
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

from dex_lips.proof_render import ProofError, duration, load_cues, media_probe, render, SHAPES
from dex_lips.jobs import (ALLOWED_MEDIA, ALLOWED_AUDIO, MAX_SOURCE_BYTES,
                           MAX_AUDIO_BYTES, atomic_job_directory, prune_expired,
                           stage_upload, unpack_user_rig)
from dex_lips import engines
from dex_lips.media_prep import prepare_video, LENGTH_POLICIES
from dex_lips.mouth_asset_generator import create_draft_mouth_rig, MouthAssetError, _frame
from dex_lips.source_geometry import JAW_MODES

VIDEO_EXTS = {'.mp4', '.mov', '.webm', '.mkv'}
SHAPE_COLOURS = {'X': (90, 90, 90), 'A': (40, 70, 200), 'B': (40, 160, 200), 'C': (240, 160, 40),
                 'D': (230, 70, 50), 'E': (170, 80, 200), 'F': (200, 60, 150), 'G': (60, 170, 90),
                 'H': (150, 150, 40)}


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
        avail = engines.available_engines()
        note = ''
        if src.suffix.lower() in VIDEO_EXTS:
            v = media_probe(src)
            if v.get('video'):
                note = (f" Video: {v['video'].get('avg_frame_rate')} fps, {duration(v):.2f}s"
                        f"{' (length differs from audio: choose trim or pad below)' if abs(duration(v) - seconds) > .08 else ''}.")
        return (f'Source: {src.name} ({src.stat().st_size:,} bytes). Speech audio: {seconds:.2f}s.{note} '
                f"Automatic engines available: {', '.join(avail) if avail else 'NONE (automatic recognition BLOCKED)'}.")
    except (ProofError, OSError, ValueError) as exc:
        return f'Input error: {exc}'


# ---------------------------------------------------------------- timing editor
def cues_to_rows(cues_text):
    try:
        cues = json.loads(cues_text or '{}').get('mouthCues', [])
        return [[round(float(c['start']), 3), round(float(c['end']), 3), str(c['value'])] for c in cues]
    except (ValueError, TypeError, KeyError, AttributeError):
        return []


def rows_to_cues(rows, previous_text=''):
    """Table rows -> validated-shape cue JSON (keeps metadata of the previous JSON)."""
    if hasattr(rows, 'values'):  # pandas DataFrame from gr.Dataframe
        rows = rows.values.tolist()
    cues = []
    for row in rows or []:
        if not row or all(v in (None, '') for v in row):
            continue
        start, end, value = float(row[0]), float(row[1]), str(row[2]).strip().upper()
        if value not in SHAPES:
            raise ProofError(f'Unknown mouth shape {value!r}; use one of X A B C D E F G H')
        cues.append({'start': round(start, 3), 'end': round(end, 3), 'value': value})
    cues.sort(key=lambda c: c['start'])
    doc = {}
    try:
        doc = json.loads(previous_text or '{}')
    except ValueError:
        doc = {}
    meta = dict(doc.get('metadata', {}))
    if meta:
        meta['edited_in_timing_editor'] = True
    out = ({'metadata': meta} if meta else {}) | {'mouthCues': cues}
    return json.dumps(out, indent=2)


def waveform_image(audio_path, cues_text, width=1100, height=190):
    """Waveform with coloured cue bands and 0.1 s ticks (play/seek with the audio player)."""
    if not audio_path:
        return None
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(audio_path), '-ac', '1', '-ar', '8000',
                          '-f', 's16le', '-'], stdout=subprocess.PIPE, timeout=30, check=False).stdout
    data = np.frombuffer(raw, '<i2').astype('float32') / 32768 if raw else np.zeros(8000, 'float32')
    total = max(len(data) / 8000, 1e-3)
    img = Image.new('RGB', (width, height), (250, 250, 247))
    d = ImageDraw.Draw(img)
    band_top, band_h = height - 46, 24
    for c in cues_to_rows(cues_text):
        x0, x1 = int(c[0] / total * width), int(c[1] / total * width)
        col = SHAPE_COLOURS.get(c[2], (0, 0, 0))
        d.rectangle((x0, band_top, max(x0 + 1, x1 - 1), band_top + band_h), fill=col)
        if x1 - x0 > 9:
            d.text((x0 + 2, band_top + 6), c[2], fill=(255, 255, 255))
        d.line((x0, 0, x0, band_top), fill=col + (0,), width=1)
    mid = (band_top - 4) // 2
    step = max(1, len(data) // width)
    for x in range(width):
        seg = data[x * step:(x + 1) * step]
        if len(seg):
            a = float(np.abs(seg).max())
            d.line((x, mid - a * mid, x, mid + a * mid), fill=(30, 40, 60))
    for k in range(int(total * 10) + 1):
        x = int(k / 10 / total * width)
        d.line((x, height - 20, x, height - (12 if k % 10 else 4)), fill=(0, 0, 0))
        if k % 5 == 0:
            d.text((x + 2, height - 16), f'{k / 10:.1f}', fill=(0, 0, 0))
    return img


def refresh_timeline(audio_path, cues_text):
    return waveform_image(audio_path, cues_text), cues_to_rows(cues_text)


def apply_table(audio_path, rows, cues_text):
    try:
        text = rows_to_cues(rows, cues_text)
        if audio_path:
            tmp = atomic_job_directory() / 'check.json'
            tmp.write_text(text, encoding='utf-8')
            load_cues(tmp, duration(media_probe(Path(audio_path))))
        return text, waveform_image(audio_path, text), 'Table applied and validated.'
    except (ProofError, ValueError, TypeError, OSError) as exc:
        return cues_text, waveform_image(audio_path, cues_text), f'Table not applied: {exc}'


# ---------------------------------------------------------------- analysis
def analyze_uploaded(audio_path, dialog, recognizer, engine='auto'):
    if not audio_path:
        return '', 'Attach a speech recording first.'
    prune_expired()
    job = atomic_job_directory()
    try:
        audio = stage_upload(Path(audio_path), job, 'speech', ALLOWED_AUDIO, MAX_AUDIO_BYTES)
        result = engines.analyze(audio, job / 'mouthCues.json', engine=engine, dialog=dialog or '',
                                 recognizer=recognizer)
        name = 'Rhubarb' if result['engine'] == 'rhubarb' else 'The wav2vec2 phoneme recognizer'
        return ((job / 'mouthCues.json').read_text(encoding='utf-8'),
                f'{name} analyzed the actual audio: {result["cue_count"]} cues. Review and adjust the timings below.')
    except (ProofError, OSError, ValueError, json.JSONDecodeError) as exc:
        return '', f'Automatic analysis unavailable: {exc}. You may instead paste reviewed Rhubarb-style JSON below.'


# ---------------------------------------------------------------- placement
def source_preview(source_path, frame_time=0.0, x=.5, y=.6, w=.13, h=.065):
    """Reference frame with the current mouth box drawn; click it to place the mouth."""
    if not source_path:
        return None
    try:
        frame, _, _ = _frame(Path(source_path), float(frame_time or 0))
    except (MouthAssetError, OSError, ValueError):
        return None
    img = frame.convert('RGB')
    d = ImageDraw.Draw(img)
    W, H = img.size
    bw, bh = w * W, h * H
    d.rectangle((x * W - bw / 2, y * H - bh / 2, x * W + bw / 2, y * H + bh / 2), outline=(0, 255, 160), width=max(1, W // 300))
    r = max(2, W // 160)
    d.ellipse((x * W - r, y * H - r, x * W + r, y * H + r), fill=(255, 210, 0))
    return img


def place_from_click(source_path, frame_time, w, h, evt=None):
    """Convert a click on the reference frame into normalized mouth coordinates."""
    if evt is None or not source_path:
        return .5, .6, .5, .6, source_preview(source_path, frame_time, .5, .6, w, h)
    frame, _, _ = _frame(Path(source_path), float(frame_time or 0))
    W, H = frame.size
    px, py = evt.index if isinstance(evt.index, (list, tuple)) else (evt.index, 0)
    x = min(.97, max(.03, round(px / W, 3)))
    y = min(.97, max(.03, round(py / H, 3)))
    return x, y, x, y, source_preview(source_path, frame_time, x, y, w, h)


# ---------------------------------------------------------------- render
def _truncate_cues_text(cues_text: str, seconds: float) -> str:
    doc = json.loads(cues_text)
    out = []
    for c in doc.get('mouthCues', []):
        if float(c['start']) >= seconds - 1e-3:
            break
        out.append(dict(c, end=min(float(c['end']), round(seconds, 3))))
    doc['mouthCues'] = out
    return json.dumps(doc)


def render_uploaded(source_path, audio_path, archive_path, cues_text, keyframe_text,
                    xpos, ypos, size, angle, fps, approved, source_video_neutral,
                    crossfade=0.0, cover_mode='none', cover_w=.12, cover_h=.06,
                    length_policy='strict', normalize_fps=True, preview_start=None):
    if not source_path or not audio_path or not archive_path:
        return None, None, None, 'Required: source image/video, speech audio, and ZIP of separately authored mouth sprites.'
    if not cues_text or not cues_text.strip():
        return None, None, None, 'Provide real engine-generated cues or edited manual mouthCues JSON. No fabricated auto-synchronization.'
    if not approved:
        return None, None, None, 'Confirm that you have permission to use your mouth artwork and footage for this job.'
    prune_expired()
    job = atomic_job_directory()
    try:
        source = stage_upload(Path(source_path), job, 'source', ALLOWED_MEDIA, MAX_SOURCE_BYTES)
        audio = stage_upload(Path(audio_path), job, 'speech', ALLOWED_AUDIO, MAX_AUDIO_BYTES)
        is_video = source.suffix.lower() in VIDEO_EXTS
        cover = {'mode': cover_mode or 'none', 'width': float(cover_w), 'height': float(cover_h)}
        if is_video and not source_video_neutral and cover['mode'] == 'none':
            raise ProofError('Existing video may contain a moving mouth. Confirm it is neutral or masked, or choose a mouth cover (patch/inpaint); this renderer does not track or remove lip motion automatically.')
        if len(cues_text) > 240000:
            raise ProofError('Mouth cue JSON exceeds size limit')
        prep_report = None
        requested_fps = int(fps)
        if is_video:
            source, audio, prep_report = prepare_video(source, audio, job, policy=length_policy,
                                                       normalize_fps=bool(normalize_fps))
            requested_fps = prep_report['render_fps']
        anchor = {'x': float(xpos), 'y': float(ypos),
                  'scale': float(size), 'rotation_deg': float(angle)}
        rig = unpack_user_rig(Path(archive_path), source, job, anchor, user_approved=bool(approved))
        secs = duration(media_probe(audio))
        if prep_report and prep_report['changes']:
            cues_text = _truncate_cues_text(cues_text, secs)
        cues = job / 'mouthCues.json'
        cues.write_text(cues_text, encoding='utf-8')
        used = load_cues(cues, secs)
        keys = None
        if keyframe_text and keyframe_text.strip():
            if len(keyframe_text) > 100000:
                raise ProofError('Keyframe JSON too large')
            keys = job / 'keyframes.json'
            keys.write_text(keyframe_text, encoding='utf-8')
        window = None if preview_start is None else (float(preview_start), 2.0)
        output = job / ('preview_2s.mp4' if window else 'lip_synced.mp4')
        receipt = render(source, audio, rig, cues, output, keyframes_path=keys, fps=requested_fps,
                         crossfade_sec=float(crossfade or 0), cover=cover, window=window)
        meta = json.loads(cues_text).get('metadata', {})
        engine = meta.get('analysis')
        receipt['mouth_cue_provenance'] = ('USER_REVIEWED_JSON' + (f'_STARTED_FROM_{str(engine).upper()}_ENGINE_OUTPUT'
                                                                  if engine in ('rhubarb', 'wav2vec2-phoneme') else '_OR_MANUAL'))
        receipt['source_video_original_mouth'] = (('COVERED_' + cover['mode'].upper()) if is_video and cover['mode'] != 'none'
                                                  else 'USER_CONFIRMED_NEUTRAL_OR_MASKED' if is_video else 'NOT_APPLICABLE')
        receipt['video_preparation'] = prep_report
        receipt['provider'] = 'LOCAL_PROCESSING_ONLY_NO_CLOUD_UPLOAD'
        receipt['spend_usd'] = 0
        receipt['user_art_canon_status'] = 'UNVERIFIED_BY_APPLICATION'
        result = job / 'receipt.json'
        result.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        changes = f" Media changes: {'; '.join(prep_report['changes'])}." if prep_report and prep_report['changes'] else ''
        what = '2-second preview' if window else 'H.264/AAC MP4'
        return str(output), str(output), str(result), (f'Rendered and verified {what}. Mouth timing follows supplied cues; recognition accuracy applies only when cues actually came from an engine (see ACCURACY.md). '
                                                        f'{len(used)} cues used. Source art unchanged.{changes}')
    except (ProofError, OSError, ValueError, json.JSONDecodeError, KeyError,
            ZeroDivisionError, zipfile.BadZipFile, UnidentifiedImageError,
            Image.DecompressionBombError, subprocess.TimeoutExpired) as exc:
        import shutil
        shutil.rmtree(job, ignore_errors=True)
        return None, None, None, f'Render blocked: {exc}'


def generate_mouth_assets(source_path, x, y, width, height, style, frame_time, contrast, jaw='human'):
    if not source_path:
        return None, None, None, None, 'Upload a still image or existing video first.'
    prune_expired()
    job = atomic_job_directory()
    try:
        source = stage_upload(Path(source_path), job, 'source', ALLOWED_MEDIA, MAX_SOURCE_BYTES)
        generated = create_draft_mouth_rig(
            source, job / 'generated_mouth_assets',
            mouth_x=float(x), mouth_y=float(y),
            width_fraction=float(width), height_fraction=float(height),
            preset=str(style), frame_time=float(frame_time), contrast=str(contrast), jaw=str(jaw),
        )
        traced = generated.get('trace_report')
        trace_description = (
            f"Source mouth silhouette traced ({traced['contrast']}, diagnostic score {traced['confidence']:.3f}, jaw mode {jaw}). "
            "Inspect green traced region and the rendered open-mouth preview. "
            if traced else
            f"Explicit graphic geometry was used ({style}, jaw mode {jaw}); no source-mouth contour was detected. "
        )
        return (str(generated['preview']), generated.get('trace_diagnostic'),
                str(generated['zip']), str(generated['zip']),
                trace_description
                + 'Generated X/A-F/G/H transparent draft sprites. X retains the original rest face. '
                'Review and approve these sprites FOR THIS JOB ONLY. '
                'No anatomical certainty, original-mouth removal, or canonical approval is implied.')
    except (MouthAssetError, ProofError, OSError, ValueError, subprocess.TimeoutExpired,
            UnidentifiedImageError, Image.DecompressionBombError) as exc:
        import shutil
        shutil.rmtree(job, ignore_errors=True)
        return None, None, None, None, f'Mouth asset generation blocked: {exc}'


def demo_render():
    from scripts.proof_smoke import run_smoke
    prune_expired()
    job = atomic_job_directory()
    try:
        run_smoke(job)
        return (str(job / 't3_still_proof.mp4'), str(job / 't4_moving_proof.mp4'),
                str(job / 'proof_receipt.json'),
                'Synthetic compositor tests passed. This is NOT real speech recognition or a canonical character animation.')
    except (ProofError, OSError, ValueError) as exc:
        return None, None, None, f'Self-test failed: {exc}'


def engine_status_markdown():
    rows = engines.engine_status()
    return ' · '.join(f"**{k}**: {'available' if v['available'] else 'BLOCKED'} ({v['reason']})" for k, v in rows.items())


def build():
    import gradio as gr
    with gr.Blocks(title='Dex_Lips — Private Lip-Sync Studio', delete_cache=(3600, 3600)) as app:
        gr.Markdown('# Dex_Lips  ·  Private Lip-Sync Studio\n'
                    'No paid processing. This server is bound to your own machine. '
                    'Automatic cues come only from an engine that actually ran: Rhubarb (installed binary) or the '
                    'wav2vec2 phoneme recognizer (local model cache). See START_HERE.md. '
                    '**Generated artwork requires visual review and is never automatic canon approval.**')
        gr.Markdown(engine_status_markdown())
        with gr.Tab('Render'):
            with gr.Row():
                source = gr.File(label='Source image OR existing video', file_types=['.png','.jpg','.jpeg','.webp','.mp4','.mov','.webm','.mkv'])
                audio = gr.Audio(label='Actual spoken audio (30s max) — play/seek here', sources=['upload'], type='filepath')
            report = gr.Markdown('Import both source and audio to inspect input.')
            source.change(input_report, [source,audio], [report])
            audio.change(input_report, [source,audio], [report])
            gr.Markdown('### 1 · Place the mouth — click it on the picture\n'
                        'Click the mouth on the reference frame. The click sets both the tracing box centre and the render anchor; '
                        'sliders remain for fine adjustment.')
            with gr.Row():
                pick = gr.Image(label='Reference frame — click the mouth', interactive=False, type='pil')
                with gr.Column():
                    g_x = gr.Slider(.03,.97,value=.5,step=.005,label='Mouth center X')
                    g_y = gr.Slider(.03,.97,value=.6,step=.005,label='Mouth center Y')
                    g_width = gr.Slider(.02,.35,value=.13,step=.005,label='Mouth width / frame width')
                    g_height = gr.Slider(.015,.25,value=.065,step=.005,label='Mouth height / frame height')
                    g_time = gr.Slider(0,30,value=0,step=.1,label='Reference frame second (video only)')
            gr.Markdown('### 2 · Make mouth assets (or upload your own ZIP)')
            with gr.Row():
                g_style = gr.Radio(['source-soft','source-faceted','soft','faceted','muzzle-template'],
                                   value='source-soft',label='Mouth construction',
                                   info='Source modes trace original mouth pixels; plain modes draw graphic shapes; muzzle-template draws a generic dog-like muzzle')
                g_jaw = gr.Radio(list(JAW_MODES), value='human', label='Jaw mode',
                                 info='Nonhuman modes pin the upper jaw and drop the lower jaw (muzzle, beak, wide jaw)')
                g_contrast = gr.Radio(['auto','dark','light'],value='auto',
                                      label='Source mouth contrast',info='Constrains source tracing; ignored in graphic modes')
            gen_btn = gr.Button('Generate draft mouth assets from source',variant='secondary')
            with gr.Row():
                gen_preview = gr.Image(label='Open-mouth pose on source (review)',interactive=False)
                gen_trace = gr.Image(label='Source pixels selected as mouth (green; source mode)',interactive=False)
            gen_download = gr.File(label='Download nine-sprite rig ZIP')
            gen_status = gr.Markdown()
            sprite_zip = gr.File(label='Mouth rig ZIP: use generated ZIP or upload your own transparent PNGs', file_types=['.zip'])
            gen_btn.click(generate_mouth_assets,
                          [source,g_x,g_y,g_width,g_height,g_style,g_time,g_contrast,g_jaw],
                          [gen_preview,gen_trace,gen_download,sprite_zip,gen_status],concurrency_limit=1)
            gr.Markdown('### 3 · Mouth timing')
            with gr.Row():
                engine = gr.Radio(['auto','rhubarb','wav2vec2'], value='auto', label='Automatic engine',
                                  info='auto = Rhubarb if installed, else wav2vec2; BLOCKED if neither')
                recognizer = gr.Radio(['pocketSphinx','phonetic'], value='pocketSphinx', label='Rhubarb recognizer', info='English / language-independent')
                dialog = gr.Textbox(label='Optional spoken transcript (Rhubarb only)', lines=2, max_lines=4)
            analyze_btn = gr.Button('Analyze the actual audio', variant='secondary')
            analyze_result = gr.Markdown()
            timeline = gr.Image(label='Timing editor: waveform with cue bands (0.1 s ticks). Play/seek with the audio player above.',
                                interactive=False, type='pil')
            cue_table = gr.Dataframe(headers=['start','end','shape'], datatype=['number','number','str'],
                                     col_count=(3, 'fixed'), label='Editable cues (seconds, shape X/A–H)', interactive=True)
            with gr.Row():
                apply_btn = gr.Button('Apply table edits → JSON + waveform', variant='secondary')
                redraw_btn = gr.Button('Reload table + waveform from JSON', variant='secondary')
            table_status = gr.Markdown()
            with gr.Accordion('Raw mouthCues JSON (advanced)', open=False):
                cues = gr.Code(language='json', label='Editable mouthCues JSON (generated or manual)', lines=10)
            analyze_btn.click(analyze_uploaded, [audio,dialog,recognizer,engine],[cues,analyze_result]).then(
                refresh_timeline, [audio,cues], [timeline,cue_table])
            apply_btn.click(apply_table, [audio,cue_table,cues], [cues,timeline,table_status])
            redraw_btn.click(refresh_timeline, [audio,cues], [timeline,cue_table])
            gr.Markdown('### 4 · Render settings')
            with gr.Row():
                x = gr.Slider(0,1,value=.5,step=.005,label='Render anchor X')
                y = gr.Slider(0,1,value=.6,step=.005,label='Render anchor Y')
                scale = gr.Slider(.05,4,value=1,step=.05,label='Mouth scale')
                angle = gr.Slider(-180,180,value=0,step=1,label='Rotation in degrees')
            with gr.Row():
                crossfade = gr.Slider(0,.12,value=.04,step=.01,label='Crossfade between mouth shapes (seconds, 0 = hard cuts)')
                fps = gr.Slider(12,30,step=1,value=24,label='Still-image output FPS; video uses its own (normalized) rate')
            with gr.Accordion('Video options (phone clips, original mouth)', open=False):
                with gr.Row():
                    length_policy = gr.Radio(list(LENGTH_POLICIES), value='trim', label='If video and audio lengths differ',
                                             info='trim = cut the longer one; pad = hold last frame / add silence; strict = refuse')
                    normalize = gr.Checkbox(value=True, label='Convert variable / 29.97 fps video to constant integer fps (working copy only)')
                with gr.Row():
                    cover_mode = gr.Radio(['none','patch','inpaint'], value='none', label='Hide the original mouth',
                                          info='patch = skin-colour cover; inpaint = OpenCV fill. Follows the anchor/keyframes.')
                    cover_w = gr.Slider(.02,.4,value=.12,step=.005,label='Cover width / frame width')
                    cover_h = gr.Slider(.01,.3,value=.06,step=.005,label='Cover height / frame height')
                keyframes = gr.Code(language='json', lines=5, label='Optional moving-video mouth-anchor keyframes JSON (for head motion)')
            granted = gr.Checkbox(label='I have permission to use these source files and have reviewed and approved the mouth sprites (generated or imported) FOR THIS JOB only. This does not grant canon approval.')
            neutral = gr.Checkbox(label='If the source is a video, its existing mouth is neutral/removed/masked (or I chose a cover above).')
            with gr.Row():
                preview_start = gr.Slider(0,28,value=0,step=.1,label='Preview start (seconds)')
                preview_btn = gr.Button('Render 2-second preview', variant='secondary')
                submit = gr.Button('Render verified MP4', variant='primary')
            status = gr.Markdown()
            video = gr.Video(label='Rendered result', interactive=False)
            result_file = gr.File(label='Download MP4')
            receipt = gr.File(label='Download proof/limits receipt')
            render_inputs = [source,audio,sprite_zip,cues,keyframes,x,y,scale,angle,fps,granted,neutral,
                             crossfade,cover_mode,cover_w,cover_h,length_policy,normalize]

            def _full(*args):
                return render_uploaded(*args, preview_start=None)

            def _preview(*args):
                *rest, start = args
                return render_uploaded(*rest, preview_start=float(start))

            submit.click(_full, render_inputs, [video,result_file,receipt,status], concurrency_limit=1)
            preview_btn.click(_preview, render_inputs + [preview_start], [video,result_file,receipt,status], concurrency_limit=1)

            def _on_click(src, t, w, h, evt):
                return place_from_click(src, t, w, h, evt)
            _on_click.__annotations__['evt'] = gr.SelectData  # real class (module uses postponed annotations)

            pick.select(_on_click, [source,g_time,g_width,g_height], [g_x,g_y,x,y,pick])
            for trigger in (source.change, g_time.release, g_width.release, g_height.release, g_x.release, g_y.release):
                trigger(source_preview, [source,g_time,g_x,g_y,g_width,g_height], [pick])
        with gr.Tab('Offline synthetic self-test'):
            gr.Markdown('The self-test does not analyze speech: it proves two deterministic MP4 compositions from externally authored cues. No uploaded personal media used.')
            btn = gr.Button('Run synthetic test (still and moving-video)', variant='secondary')
            demo_still = gr.Video(label='Synthetic still → MP4')
            demo_move = gr.Video(label='Synthetic moving video → MP4')
            demo_receipt = gr.File(label='Proof receipt')
            demo_status = gr.Markdown()
            btn.click(demo_render,outputs=[demo_still,demo_move,demo_receipt,demo_status],concurrency_limit=1)
        gr.Markdown('**Limits:** Maximum 1280×720 output; 30-second audio. Phone videos are converted to a constant-frame-rate working copy; trim/pad changes are listed in the receipt. '
                    'Source tracing segments pixels inside the chosen mouth box; it does not identify anatomy or track the mouth. The optional mouth cover follows your anchor/keyframes, not detection. '
                    'Scratch output is eligible for pruning after one hour on subsequent jobs and is removed at process exit; original uploads are never deleted.')
    return app


if __name__ == '__main__':
    build().launch(server_name='127.0.0.1', server_port=7860, share=False, inbrowser=False,
                   show_error=True)
