import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / 'assets/reference/dexter/dexter_reference_sheet.png'
SET = ROOT / 'assets/mouth_sets/dexter_muzzle'
APPROVED_SHA = 'ed81548c07c3e3b47a189a0aa2a502fe171146a1f2a96060d790e22091c12c41'
ALLOWED_CELLS = {'row 1 col 3 "Left-Proflle"', 'row 1 col 1 "Front-01"',
                 'row 1 col 4 "Profile"', 'row 2 col 4 "Determinted"'}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class DexterSetTests(unittest.TestCase):
    def test_sheet_is_the_approved_file(self):
        self.assertEqual(sha(SHEET), APPROVED_SHA)
        self.assertEqual(Image.open(SHEET).size, (1056, 992))

    def test_nine_states_from_allowed_front_facing_cells_only(self):
        rig = json.loads((SET / 'rig.template.json').read_text())
        self.assertEqual(rig['reference_sheet_sha256'], APPROVED_SHA)
        self.assertEqual(rig['authority'], 'approved_user_rig')
        self.assertTrue(rig['approved'])
        self.assertEqual(sorted(rig['shapes']), sorted('XABCDEFGH'))
        for shape, file in rig['shapes'].items():
            im = Image.open(SET / file)
            self.assertEqual(im.mode, 'RGBA')
            self.assertEqual(im.size, (148, 88))
            self.assertIn(rig['provenance'][shape]['cell'], ALLOWED_CELLS)
        self.assertTrue((SET / 'contact_sheet.png').is_file())

    def test_shapes_are_distinct(self):
        hashes = {sha(SET / f'{s}.png') for s in 'XABCDEFGH'}
        self.assertEqual(len(hashes), 9)

    @unittest.skipUnless(importlib.util.find_spec('cv2') and importlib.util.find_spec('numpy'), 'opencv not installed')
    def test_build_is_reproducible_from_the_sheet(self):
        spec = importlib.util.spec_from_file_location('bdm', ROOT / 'scripts/build_dexter_mouths.py')
        bdm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bdm)
        with tempfile.TemporaryDirectory() as tmp:
            bdm.OUT = Path(tmp) / 'set'
            bdm.STILL = Path(tmp) / 'still.png'
            bdm.build()
            # Pixel comparison (not file hashes) so PNG encoder / OpenCV patch versions don't matter.
            import numpy as np
            def close(a: Path, b: Path) -> bool:
                x = np.asarray(Image.open(a), dtype=int)
                y = np.asarray(Image.open(b), dtype=int)
                return x.shape == y.shape and np.abs(x - y).mean() < 1.0 and np.abs(x - y).max() <= 40
            self.assertTrue(close(bdm.STILL, ROOT / 'assets/reference/dexter/dexter_front_still.png'))
            for s in 'XABCDEFGH':
                self.assertTrue(close(bdm.OUT / f'{s}.png', SET / f'{s}.png'), s)

    def test_refuses_a_different_sheet(self):
        if not (importlib.util.find_spec('cv2') and importlib.util.find_spec('numpy')):
            self.skipTest('opencv not installed')
        spec = importlib.util.spec_from_file_location('bdm2', ROOT / 'scripts/build_dexter_mouths.py')
        bdm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bdm)
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / 'fake.png'
            Image.new('RGB', (1056, 992), 'white').save(fake)
            bdm.SHEET = fake
            bdm.OUT = Path(tmp) / 'set'
            with self.assertRaises(SystemExit):
                bdm.build()
            self.assertFalse(bdm.OUT.exists())


if __name__ == '__main__':
    unittest.main()
