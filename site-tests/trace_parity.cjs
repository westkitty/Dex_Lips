// Reads a JSON fixture on stdin and prints the browser tracing core's answers.
// Used by tests/test_trace_parity.py to compare against the Python core.
'use strict';
const core = require('../site/assets/trace_core.js');
let input = '';
process.stdin.on('data', (c) => { input += c; });
process.stdin.on('end', () => {
  const fx = JSON.parse(input);
  const cases = fx.cases.map((c) => {
    const lum = Float64Array.from(c.rgb, (p) => core.luma(p[0], p[1], p[2]));
    try {
      const r = core.selectComponent(lum, c.sw, c.sh, c.contrast);
      const mark = new Uint8Array(c.sw * c.sh); for (const i of r.component) mark[i] = 1;
      const holes = core.fillHoles(mark, c.sw, c.sh);
      const up = [];
      for (let y = 0; y < c.rh; y++) for (let x = 0; x < c.rw; x++) up.push(holes[core.upsampleIndex(x, y, c.rw, c.rh, c.sw, c.sh)]);
      return {ok: true, score: r.score, mean: r.mean, polarity: r.polarity, bbox: r.bbox, component: r.component, holes: Array.from(holes), upsampled: up};
    } catch (e) { return {ok: false, error: String(e.message).slice(0, 40)}; }
  });
  const poses = [];
  for (const [w, h] of fx.poses) for (const jaw of Object.keys(core.JAW_MODES)) for (const s of 'ABCDEFGH') poses.push([w, h, jaw, s, core.poseBox(w, h, s, jaw)]);
  const regions = fx.regions.map(([w, h, x, y, dw, dh]) => core.regionBox(w, h, {x, y}, {w: dw, h: dh}));
  process.stdout.write(JSON.stringify({cases, poses, regions, jaws: core.JAW_MODES}));
});
