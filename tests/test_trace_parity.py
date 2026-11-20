"""Python <-> browser parity for source mouth tracing (improvement 7).

Runs the real site/assets/trace_core.js under Node on shared fixtures and
compares, exactly, the selected component, filled mask, upsampled mask,
region/search boxes and the per-jaw pose boxes against the Python core.
Pixel-level downsampling (PIL BOX vs browser canvas) is NOT compared: canvas
resampling is browser-defined, so both sides are fed the same search grid.
"""
from __future__ import annotations

import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def fixtures():
    rng = random.Random(7)
    cases = []
    for k in range(14):
        sw, sh = rng.choice([(40, 24), (60, 30), (33, 17), (90, 45), (24, 24)])
        bg = (rng.randrange(120, 220), rng.randrange(100, 200), rng.randrange(80, 180))
        if k % 2:  # graded background: distinct border values make the median choice matter
            rgb = [[min(255, bg[0] + (i * 37) % 61), bg[1], bg[2]] for i in range(sw * sh)]
        else:
            rgb = [list(bg) for _ in range(sw * sh)]
        dark = k % 3 != 2
        colour = [rng.randrange(0, 50)] * 3 if dark else [rng.randrange(230, 256)] * 3
        if k % 3 == 2:
            for p in rgb:
                p[:] = [v // 4 for v in p]
        cx, cy = sw // 2 + rng.randrange(-2, 3), sh // 2 + rng.randrange(-2, 3)
        rx, ry = max(3, sw // 4 + rng.randrange(-2, 3)), max(2, sh // 6 + rng.randrange(0, 3))
        for y in range(sh):
            for x in range(sw):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    rgb[y * sw + x] = list(colour)
                elif rng.random() < .08:
                    rgb[y * sw + x] = [min(255, v + rng.randrange(-40, 40)) % 256 for v in bg]
        if k % 4 == 0:  # a highlight "tooth" inside the cavity (hole filling)
            rgb[cy * sw + cx] = list(bg)
        if k == 13:     # nothing to find -> both must refuse
            rgb = [list(bg) for _ in range(sw * sh)]
        cases.append({'rgb': rgb, 'sw': sw, 'sh': sh, 'rw': sw * 3 + 1, 'rh': sh * 2 + 3,
                      'contrast': ['auto', 'dark', 'light'][k % 3] if k % 3 != 2 else 'auto'})
    poses = [[96, 48], [101, 37], [256, 160], [17, 9]]
    regions = [[640, 480, .5, .6, .13, .065], [1024, 1536, .41, .23, .2, .05], [333, 211, .97, .03, .35, .25]]
    return {'cases': cases, 'poses': poses, 'regions': regions}


@unittest.skipUnless(shutil.which('node'), 'Node.js needed for the browser-core parity test')
class TestTraceParity(unittest.TestCase):
    def test_python_and_browser_cores_agree_exactly(self):
        from dex_lips import source_geometry as sg
        fx = fixtures()
        out = subprocess.run(['node', str(ROOT / 'site-tests/trace_parity.cjs')], input=json.dumps(fx).encode(),
                             stdout=subprocess.PIPE, check=True, timeout=60).stdout
        js = json.loads(out)
        found = 0
        for case, j in zip(fx['cases'], js['cases']):
            lum = [sg._luma(tuple(p)) for p in case['rgb']]
            try:
                conf, comp, pol, bbox, mean = sg.select_component(lum, case['sw'], case['sh'], case['contrast'])
            except sg.GeometryTraceError:
                self.assertFalse(j['ok'], 'browser traced where Python refused')
                continue
            self.assertTrue(j['ok'], f"Python traced where browser refused: {j.get('error')}")
            found += 1
            self.assertEqual(pol, j['polarity'])
            self.assertEqual(list(bbox), j['bbox'])
            self.assertEqual(comp, j['component'])
            self.assertAlmostEqual(conf, j['score'], places=9)
            self.assertAlmostEqual(mean, j['mean'], places=9)  # depends on the border median
            filled = sg._fill_holes(set(comp), case['sw'], case['sh'])
            self.assertEqual([1 if i in filled else 0 for i in range(case['sw'] * case['sh'])], j['holes'])
            up = [1 if sg.upsample_index(x, y, case['rw'], case['rh'], case['sw'], case['sh']) in filled else 0
                  for y in range(case['rh']) for x in range(case['rw'])]
            self.assertEqual(up, j['upsampled'])
        self.assertGreaterEqual(found, 8, 'fixtures should exercise successful traces')
        self.assertTrue(any(not c['ok'] for c in js['cases']), 'fixtures should exercise refusals')
        for w, h, jaw, shape, box in js['poses']:
            self.assertEqual(list(sg.pose_box(w, h, shape, jaw)), box, (w, h, jaw, shape))
        for (w, h, x, y, dw, dh), r in zip(fx['regions'], js['regions']):
            rw, rh = max(8, sg.round_half_up(w * dw)), max(8, sg.round_half_up(h * dh))
            left = max(0, min(w - rw, sg.round_half_up(x * w - rw / 2)))
            top = max(0, min(h - rh, sg.round_half_up(y * h - rh / 2)))
            self.assertEqual([rw, rh, left, top], [r['regionW'], r['regionH'], r['left'], r['top']])
        for jaw, mode in sg.JAW_MODES.items():
            self.assertEqual(mode['anchor'], js['jaws'][jaw]['anchor'])
            self.assertEqual({k: list(v) for k, v in mode['ratios'].items()}, js['jaws'][jaw]['ratios'])


if __name__ == '__main__':
    unittest.main()
