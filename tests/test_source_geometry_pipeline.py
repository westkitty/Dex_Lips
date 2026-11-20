"""Identity-preserving mouth tracing and generated-rig to actual MP4 integration.

Synthetic noncanonical sources, actual recorded spoken WAV and historically
captured real Rhubarb mouth cues. No synthetic cues are called speech analysis.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dex_lips.mouth_asset_generator import create_draft_mouth_rig, MouthAssetError
from dex_lips.jobs import unpack_user_rig
from dex_lips.proof_render import render, media_probe


class SourceGeometryTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.work = Path(self.scratch.name)

    def source(self, name='dark.png', invert=False):
        img = Image.new('RGB', (320, 240), (19, 33, 61) if invert else (181, 156, 120))
        draw = ImageDraw.Draw(img)
        # An asymmetric faceted NONHUMAN mouth; deliberately no lips/teeth.
        draw.polygon([(132, 148), (143, 132), (160, 140), (182, 133),
                      (189, 153), (163, 161), (141, 158)],
                     fill=(16, 232, 244) if invert else (20, 28, 46))
        path = self.work / name
        img.save(path)
        return path

    def test_asymmetric_source_mouth_colors_are_preserved(self):
        source = self.source()
        original = hashlib.sha256(source.read_bytes()).hexdigest()
        result = create_draft_mouth_rig(source, self.work / 'traced',
                    mouth_x=.5, mouth_y=.61, width_fraction=.29,
                    height_fraction=.20, preset='source-faceted')
        self.assertEqual(original, hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(result['preset'], 'source-faceted')
        self.assertIsNotNone(result['trace_diagnostic'])
        self.assertGreaterEqual(result['trace_report']['confidence'], .57)
        self.assertEqual(result['trace_report']['contrast'], 'dark')
        with Image.open(self.work / 'traced' / 'D.png') as src:
            self.assertIsNotNone(src.getbbox())
            colors = {p[:3] for p in src.getdata() if p[3] == 255}
            self.assertIn((20, 28, 46), colors)
            self.assertNotIn((0, 0, 0), colors)
        with Image.open(self.work / 'traced' / 'X.png') as rest:
            self.assertIsNone(rest.getbbox())
        with open(self.work / 'traced' / 'rig.json', encoding='utf-8') as f:
            rig = json.load(f)
        self.assertFalse(rig['approved'])
        self.assertEqual(rig['authority'], 'generated_draft')
        self.assertIn('source-faceted', rig['notes'])

    def test_bright_cyan_mouth_on_dark_fur_is_traced(self):
        source = self.source('bright.png', invert=True)
        result = create_draft_mouth_rig(source, self.work/'bright',
                    mouth_x=.5, mouth_y=.61,width_fraction=.29,
                    height_fraction=.20,preset='source-soft',contrast='light')
        self.assertEqual(result['trace_report']['contrast'], 'light')
        with Image.open(self.work / 'bright' / 'D.png') as sprite:
            colors = [p[:3] for p in sprite.getdata() if p[3] >= 245]
            self.assertIn((16, 232, 244), colors)

    def test_ambiguous_source_does_not_fabricate_character_mouth(self):
        blank = self.work / 'no-mouth.png'
        Image.new('RGB', (320,240), (99,99,99)).save(blank)
        with self.assertRaisesRegex(MouthAssetError, 'Cannot isolate'):
            create_draft_mouth_rig(blank,self.work/'refused',
                mouth_x=.5,mouth_y=.6,width_fraction=.29,height_fraction=.2,
                preset='source-faceted')
        self.assertFalse((self.work/'refused').exists())
        # Historic explicit graphic mode remains usable with the same source.
        result = create_draft_mouth_rig(blank,self.work/'graphic',
                mouth_x=.5,mouth_y=.6,width_fraction=.29,height_fraction=.2,
                preset='faceted')
        self.assertIsNone(result['trace_diagnostic'])

    def test_still_and_video_real_speech_cues_to_mp4(self):
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            self.skipTest('ffmpeg and ffprobe required for MP4 integration')
        audio = ROOT / 'experiments/browser-wasm/fixtures/spoken_2s.wav'
        cues = ROOT / 'experiments/browser-wasm/evidence/actual_rhubarb_mouthCues.json'
        if not audio.is_file() or not cues.is_file():
            self.fail('Real recorded speech/cues fixture missing')
        # Real Rhubarb cues were captured in a separate prior experiment;
        # this proves their reuse with generated mouth art, not new analysis.
        for kind in ('still', 'video'):
            with self.subTest(kind=kind):
                source = self.source(f'{kind}.png')
                if kind == 'video':
                    video = self.work / 'moving.mp4'
                    subprocess.run(['ffmpeg','-nostdin','-v','error','-loop','1','-framerate','24',
                        '-i',str(source),'-t','2','-c:v','libx264','-pix_fmt','yuv420p',
                        '-r','24','-an',str(video)],check=True,timeout=30)
                    source = video
                sha_before = hashlib.sha256(source.read_bytes()).hexdigest()
                output_dir = self.work / f'{kind}_assets'
                result = create_draft_mouth_rig(source,output_dir,
                     mouth_x=.5,mouth_y=.61,width_fraction=.29,height_fraction=.2,
                     preset='source-faceted',frame_time=0)
                rig = unpack_user_rig(Path(result['zip']),source,
                    self.work/f'{kind}_import',
                    {'x':.5,'y':.61,'scale':1.,'rotation_deg':0.},
                    user_approved=True)
                job_output = self.work / f'{kind}_rendered.mp4'
                receipt = render(source,audio,rig,cues,job_output,fps=24)
                probe = media_probe(job_output)
                self.assertEqual(probe['video']['codec_name'],'h264')
                self.assertEqual(probe['audio']['codec_name'],'aac')
                self.assertAlmostEqual(float(probe['format']['duration']),2,delta=.15)
                subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',
                                str(job_output),'-f','null','-'],check=True,timeout=30)
                self.assertEqual(sha_before,hashlib.sha256(source.read_bytes()).hexdigest())
                self.assertTrue(job_output.stat().st_size > 1000)
                self.assertIsInstance(receipt,dict)

    def test_gradio_generated_zip_to_existing_render_callback(self):
        """Real UI callback chain, not just direct internal renderer calls."""
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            self.skipTest('ffmpeg missing')
        from app import generate_mouth_assets, render_uploaded
        source = self.source('ui-source.png')
        audio = ROOT / 'experiments/browser-wasm/fixtures/spoken_2s.wav'
        cues = (ROOT / 'experiments/browser-wasm/evidence/actual_rhubarb_mouthCues.json').read_text()
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        preview, diagnostic, archive, imported, status = generate_mouth_assets(
            str(source), .5, .61, .29, .20, 'source-faceted', 0, 'dark')
        self.assertTrue(Path(preview).is_file())
        self.assertTrue(Path(diagnostic).is_file())
        self.assertEqual(archive, imported)
        self.assertIn('silhouette traced', status)
        mp4, download, receipt_path, status = render_uploaded(
            str(source), str(audio), archive, cues,
            '', .5, .61, 1, 0, 24, True, False)
        self.assertIn('Rendered and verified', status)
        self.assertEqual(mp4, download)
        self.assertTrue(Path(mp4).is_file())
        receipt = json.loads(Path(receipt_path).read_text())
        self.assertEqual(receipt['provider'], 'LOCAL_PROCESSING_ONLY_NO_CLOUD_UPLOAD')
        probe = media_probe(Path(mp4))
        self.assertEqual(probe['video']['codec_name'], 'h264')
        self.assertEqual(probe['audio']['codec_name'], 'aac')
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', mp4,
                        '-f', 'null', '-'], check=True, timeout=30)
        self.assertEqual(before, hashlib.sha256(source.read_bytes()).hexdigest())

    def test_exact_bundled_canonical_source_is_not_auto_approved(self):
        from unittest.mock import patch
        source = self.source()
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        with patch('dex_lips.mouth_asset_generator._protected_hashes',return_value={digest}):
            with self.assertRaisesRegex(MouthAssetError, 'Protected canonical'):
                create_draft_mouth_rig(source,self.work/'no-canon',
                    mouth_x=.5,mouth_y=.61,width_fraction=.29,
                    height_fraction=.20,preset='source-faceted')
        self.assertFalse((self.work/'no-canon').exists())


if __name__ == '__main__':
    unittest.main()
