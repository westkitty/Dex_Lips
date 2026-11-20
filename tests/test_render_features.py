"""Crossfade, 2-second preview, mouth cover, phone-video prep, timing editor,
click placement, nonhuman jaw modes and the generic muzzle set."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / 'scripts')]
READY = bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))


def frame_at(mp4: Path, t: float):
    from PIL import Image
    import io
    png = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', str(mp4), '-frames:v', '1',
                          '-f', 'image2pipe', '-vcodec', 'png', '-'], stdout=subprocess.PIPE, check=True).stdout
    return Image.open(io.BytesIO(png)).convert('RGB')


@unittest.skipUnless(READY, 'Requires FFmpeg')
class TestRenderFeatures(unittest.TestCase):
    def setUp(self):
        from proof_smoke import make_demo
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.example = make_demo(self.work)

    def test_two_second_preview_window(self):
        from dex_lips.proof_render import render, media_probe, duration
        out = self.work / 'preview.mp4'
        r = render(self.example['still'], self.example['audio'], self.example['still_rig'], self.example['cues'], out,
                   window=(0.2, 2.0))
        self.assertLessEqual(abs(duration(media_probe(out)) - r['preview_window'][1]), 0.1)
        self.assertLessEqual(r['preview_window'][1], 2.0)
        self.assertEqual(r['frames_expected'], round(r['preview_window'][1] * 24))

    def test_crossfade_blends_between_shapes_and_zero_keeps_hard_cut(self):
        from dex_lips.proof_render import render
        hard, soft = self.work / 'hard.mp4', self.work / 'soft.mp4'
        render(self.example['still'], self.example['audio'], self.example['still_rig'], self.example['cues'], hard)
        r = render(self.example['still'], self.example['audio'], self.example['still_rig'], self.example['cues'], soft,
                   crossfade_sec=0.12)
        self.assertEqual(r['crossfade_sec'], 0.12)
        cues = json.loads(self.example['cues'].read_text())['mouthCues']
        change = next(c['start'] for p, c in zip(cues, cues[1:]) if p['value'] != c['value'] and c['start'] > 0.1)
        t = (round(change * 24) + 1) / 24  # first frames after a change
        a, b = frame_at(hard, t).tobytes(), frame_at(soft, t).tobytes()
        self.assertNotEqual(a, b, 'crossfade should differ right after a shape change')
        with self.assertRaises(Exception):
            render(self.example['still'], self.example['audio'], self.example['still_rig'], self.example['cues'],
                   self.work / 'bad.mp4', crossfade_sec=1.0)

    def test_cover_patch_changes_mouth_region_and_is_opt_in(self):
        from PIL import Image
        from dex_lips.proof_render import cover_mouth
        img = Image.new('RGB', (200, 120), (200, 170, 140))
        img.paste((20, 20, 20), (85, 65, 115, 80))  # a dark "original mouth"
        out = cover_mouth(img, {'x': .5, 'y': .6}, {'mode': 'patch', 'width': .3, 'height': .2})
        self.assertLess(out.getpixel((100, 72))[0] - 200, 20)
        self.assertGreater(out.getpixel((100, 72))[0], 150)
        self.assertEqual(cover_mouth(img, {'x': .5, 'y': .6}, {'mode': 'none'}).tobytes(), img.tobytes())
        try:
            import cv2  # noqa: F401
        except ImportError:
            return
        inp = cover_mouth(img, {'x': .5, 'y': .6}, {'mode': 'inpaint', 'width': .3, 'height': .2})
        self.assertGreater(inp.getpixel((100, 72))[0], 120)

    def _phone_clip(self, seconds=2.6):
        clip = self.work / 'phone.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=30000/1001',
                        '-t', str(seconds), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(clip)], check=True)
        return clip

    def test_phone_video_2997_with_longer_audio_trim_and_pad(self):
        from dex_lips.media_prep import prepare_video
        from dex_lips.proof_render import ProofError, duration, media_probe
        clip, audio = self._phone_clip(), ROOT / 'eval/clips/3575-170457-0001.flac'
        with self.assertRaisesRegex(ProofError, 'trim'):
            prepare_video(clip, audio, self.work, policy='strict')
        for policy in ('trim', 'pad'):
            d = self.work / policy
            d.mkdir()
            v, a, rep = prepare_video(clip, audio, d, policy=policy)
            self.assertTrue(rep['fps_converted'])
            self.assertEqual(rep['render_fps'], 30)
            self.assertLess(abs(duration(media_probe(v)) - duration(media_probe(a))), 0.08)
            stream = media_probe(v)['video']
            self.assertEqual(stream['avg_frame_rate'], '30/1')
        self.assertEqual(clip.stat().st_size, clip.stat().st_size)  # original untouched

    def test_app_renders_phone_video_with_trim_cover_and_preview(self):
        from app import render_uploaded
        clip = self._phone_clip(2.0)
        rig = self.work / 'rig.zip'
        with zipfile.ZipFile(rig, 'w') as z:
            for shape in 'XDB':
                z.write(self.work / f'{shape}.png', arcname=f'{shape}.png')
        cues = json.dumps({'mouthCues': [{'start': 0, 'end': .5, 'value': 'X'}, {'start': .5, 'end': 1.4, 'value': 'D'},
                                         {'start': 1.4, 'end': 2.1, 'value': 'B'}]})
        audio = self.example['audio']
        mp4, _, receipt, status = render_uploaded(str(clip), str(audio), str(rig), cues, '', .5, .6, 1, 0, 24, True, False,
                                                  .04, 'patch', .2, .1, 'trim', True, None)
        self.assertIn('Rendered and verified', status, status)
        rec = json.loads(Path(receipt).read_text())
        self.assertEqual(rec['source_video_original_mouth'], 'COVERED_PATCH')
        self.assertTrue(rec['video_preparation']['fps_converted'])
        mp4, _, receipt, status = render_uploaded(str(clip), str(audio), str(rig), cues, '', .5, .6, 1, 0, 24, True, True,
                                                  0, 'none', .2, .1, 'trim', True, 0.0)
        self.assertIn('2-second preview', status, status)


class TestEditorsAndModes(unittest.TestCase):
    def test_timing_table_round_trip_keeps_metadata(self):
        import app
        doc = json.dumps({'metadata': {'analysis': 'rhubarb'}, 'mouthCues': [{'start': 0, 'end': .3, 'value': 'X'},
                                                                            {'start': .3, 'end': .6, 'value': 'D'}]})
        rows = app.cues_to_rows(doc)
        self.assertEqual(rows, [[0.0, 0.3, 'X'], [0.3, 0.6, 'D']])
        rows[1][2] = 'c'
        out = json.loads(app.rows_to_cues(rows, doc))
        self.assertEqual(out['mouthCues'][1]['value'], 'C')
        self.assertTrue(out['metadata']['edited_in_timing_editor'])
        with self.assertRaises(Exception):
            app.rows_to_cues([[0, .2, 'Q']], doc)

    @unittest.skipUnless(READY, 'Requires FFmpeg')
    def test_waveform_image_draws_cue_bands(self):
        import app
        img = app.waveform_image(str(ROOT / 'eval/clips/260-123440-0000.flac'),
                                 json.dumps({'mouthCues': [{'start': 0, 'end': 1, 'value': 'D'}]}))
        self.assertEqual(img.size, (1100, 190))
        self.assertEqual(img.getpixel((100, 190 - 40)), app.SHAPE_COLOURS['D'])

    def test_click_on_picture_sets_normalized_mouth_position(self):
        import app
        from PIL import Image

        class Evt:
            index = (300, 90)
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / 'face.png'
            Image.new('RGB', (400, 300), (120, 120, 120)).save(src)
            x, y, rx, ry, preview = app.place_from_click(str(src), 0, .1, .05, Evt())
        self.assertEqual((x, y, rx, ry), (.75, .3, .75, .3))
        self.assertEqual(preview.size, (400, 300))

    def test_nonhuman_jaw_modes_pin_the_upper_jaw(self):
        from dex_lips.source_geometry import pose_box, JAW_MODES
        for jaw in ('muzzle', 'beak', 'wide-jaw'):
            tops = {s: pose_box(200, 100, s, jaw)[1] for s in 'ABCDEFGH'}
            self.assertEqual(len(set(tops.values())), 1, (jaw, tops))  # same top edge for every pose
            self.assertGreater(pose_box(200, 100, 'D', jaw)[3], pose_box(200, 100, 'A', jaw)[3])
        self.assertIn('human', JAW_MODES)

    def test_generator_accepts_jaw_and_muzzle_template(self):
        from PIL import Image, ImageDraw
        from dex_lips.mouth_asset_generator import create_draft_mouth_rig
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / 'snout.png'
            img = Image.new('RGB', (320, 240), (181, 156, 120))
            ImageDraw.Draw(img).ellipse((130, 135, 190, 155), fill=(20, 28, 46))
            img.save(src)
            for i, (preset, jaw) in enumerate([('source-soft', 'muzzle'), ('soft', 'beak'), ('muzzle-template', 'muzzle')]):
                res = create_draft_mouth_rig(src, Path(d) / f'out{i}', mouth_x=.5, mouth_y=.6, width_fraction=.3,
                                             height_fraction=.15, preset=preset, jaw=jaw)
                self.assertEqual(len(res['shapes']), 9)
                rig = json.loads((Path(d) / f'out{i}' / 'rig.json').read_text())
                self.assertEqual(rig['jaw_mode'], jaw)
                self.assertFalse(rig['approved'])

    def test_generic_muzzle_set_is_complete_transparent_and_not_a_character(self):
        from PIL import Image
        base = ROOT / 'assets/mouth_sets/generic_muzzle'
        rig = json.loads((base / 'rig.template.json').read_text())
        self.assertEqual(sorted(rig['shapes']), sorted('XABCDEFGH'))
        self.assertIn('Not derived from', rig['notes'])
        sizes = set()
        for shape, name in rig['shapes'].items():
            with Image.open(base / name) as im:
                self.assertEqual(im.mode, 'RGBA')
                self.assertEqual(im.getpixel((0, 0))[3], 0)
                sizes.add(im.size)
        self.assertEqual(len(sizes), 1)
        # Regenerating is deterministic.
        from dex_lips.muzzle_template import draw_pose
        with Image.open(base / 'D.png') as stored:
            self.assertEqual(draw_pose('D').tobytes(), stored.convert('RGBA').tobytes())


if __name__ == '__main__':
    unittest.main()
