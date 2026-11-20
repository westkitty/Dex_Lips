"""Regressions for the in-product source-conditioned draft mouth asset creator."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import json

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from dex_lips.mouth_asset_generator import create_draft_mouth_rig, MouthAssetError


class MouthAssetGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'creature.png'
        art = Image.new('RGB', (400, 400), (67, 115, 136))
        d = ImageDraw.Draw(art)
        d.ellipse((150, 100, 250, 240), fill=(170, 190, 206))
        d.line((176, 192, 222, 192), fill=(23, 33, 48), width=3)
        art.save(self.source)

    def test_nine_distinct_source_bound_transparent_pngs_draft_only(self):
        before = hashlib.sha256(self.source.read_bytes()).hexdigest()
        result = create_draft_mouth_rig(self.source, self.root/'sprites', mouth_x=.5, mouth_y=.48, preset='faceted')
        self.assertEqual(before, hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(len(result['shapes']), 9)
        self.assertTrue(result['draft_only'])
        self.assertTrue(Path(result['preview']).is_file())
        with zipfile.ZipFile(result['zip']) as zf:
            self.assertEqual(set(zf.namelist()), set(f'{x}.png' for x in 'XABCDEFGH') | {'rig.json'})
            cfg = json.loads(zf.read('rig.json'))
            self.assertEqual(cfg['source_sha256'], before)
            self.assertEqual(cfg['authority'], 'generated_draft')
            self.assertFalse(cfg['approved'])
        digests = []
        for file in result['shapes']:
            with Image.open(file) as sprite:
                self.assertEqual(sprite.format, 'PNG')
                self.assertEqual(sprite.mode, 'RGBA')
                digests.append(hashlib.sha256(sprite.tobytes()).hexdigest())
        self.assertEqual(len(set(digests)), 9)
        with Image.open(self.root/'sprites'/'X.png') as closed:
            self.assertEqual(closed.getbbox(), None)

    def test_no_overwrite_even_when_regenerating(self):
        create_draft_mouth_rig(self.source, self.root/'sprites', mouth_x=.5, mouth_y=.5)
        with self.assertRaisesRegex(MouthAssetError, 'exists'):
            create_draft_mouth_rig(self.source, self.root/'sprites', mouth_x=.5, mouth_y=.5)

    def test_protected_reference_cannot_be_rigged(self):
        digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        with patch('dex_lips.mouth_asset_generator._protected_hashes', return_value={digest}):
            with self.assertRaisesRegex(MouthAssetError, 'Protected'):
                create_draft_mouth_rig(self.source, self.root/'blocked', mouth_x=.5, mouth_y=.5)
        self.assertFalse((self.root/'blocked').exists())

    def test_reject_bad_dimensions_before_write(self):
        for kwargs in [dict(mouth_x=-1, mouth_y=.5), dict(mouth_x=.5, mouth_y=.5, width_fraction=.90),
                       dict(mouth_x=float('nan'), mouth_y=.5)]:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(MouthAssetError):
                    create_draft_mouth_rig(self.source, self.root/'invalid', **kwargs)
                self.assertFalse((self.root/'invalid').exists())

    def test_video_extracts_actual_frame_when_ffmpeg_present(self):
        import shutil
        if not (shutil.which('ffmpeg') and shutil.which('ffprobe')):
            self.skipTest('ffmpeg unavailable')
        source = self.root / 'moving.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=320x240:r=24:d=1',
                        '-c:v','libx264','-pix_fmt','yuv420p',str(source)],check=True)
        result = create_draft_mouth_rig(source, self.root/'video', mouth_x=.5,mouth_y=.6, frame_time=.2)
        self.assertEqual(result['sprite_dimensions'], [42, 16])
        with Image.open(result['preview']) as image:
            self.assertEqual(image.size, (320, 240))


if __name__ == '__main__':
    unittest.main()
