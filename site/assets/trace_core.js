'use strict';
// Dex_Lips shared tracing core. Pure functions only (no DOM), so the exact same
// code runs in the browser and under Node for the Python/JS parity test
// (tests/test_trace_parity.py). Mirrors src/dex_lips/source_geometry.py.
(function (root) {
  const RATIOS = {A:[.66,.10],B:[.54,.30],C:[.76,.50],D:[.83,.82],E:[.46,.80],F:[.39,.54],G:[.75,.24],H:[.70,.15]};
  // Construction modes; nonhuman modes pin the top edge (lower jaw drops).
  const JAW_MODES = {
    'human': {anchor:'center', ratios:RATIOS},
    'muzzle': {anchor:'top', ratios:{A:[.70,.10],B:[.68,.26],C:[.70,.48],D:[.72,.80],E:[.58,.62],F:[.50,.46],G:[.70,.20],H:[.68,.32]}},
    'beak': {anchor:'top', ratios:{A:[.80,.08],B:[.80,.22],C:[.80,.42],D:[.80,.70],E:[.74,.50],F:[.70,.38],G:[.80,.18],H:[.80,.30]}},
    'wide-jaw': {anchor:'top', ratios:{A:[.90,.10],B:[.86,.30],C:[.92,.52],D:[.96,.86],E:[.80,.66],F:[.70,.50],G:[.90,.24],H:[.88,.36]}},
  };
  const roundHalfUp = (v) => Math.floor(v + 0.5);
  // Same integer arithmetic as Python's _luma.
  const luma = (r, g, b) => (r * 299 + g * 587 + b * 114) / 1000;
  function medianUpper(values) { if (!values.length) return 0; const a = Array.from(values).sort((x, y) => x - y); return a[Math.floor(a.length / 2)]; }
  function findComponents(mark, w, h) {
    const visited = new Uint8Array(w * h); const groups = [];
    for (let seed = 0; seed < mark.length; seed++) {
      if (!mark[seed] || visited[seed]) continue;
      const stack = [seed], component = []; visited[seed] = 1;
      while (stack.length) {
        const current = stack.pop(); component.push(current);
        const y = Math.floor(current / w), x = current % w;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          const xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue;
          const i = yy * w + xx; if (mark[i] && !visited[i]) { visited[i] = 1; stack.push(i); }
        }
      }
      groups.push(component);
    }
    return groups;
  }
  function fillHoles(selected, w, h) {
    const out = new Uint8Array(w * h), exterior = new Uint8Array(w * h), q = [];
    const enqueue = (i) => { if (!selected[i] && !exterior[i]) { exterior[i] = 1; q.push(i); } };
    for (let x = 0; x < w; x++) { enqueue(x); enqueue((h - 1) * w + x); }
    for (let y = 0; y < h; y++) { enqueue(y * w); enqueue(y * w + w - 1); }
    for (let p = 0; p < q.length; p++) { const i = q[p], x = i % w, y = Math.floor(i / w); if (x > 0) enqueue(i - 1); if (x < w - 1) enqueue(i + 1); if (y > 0) enqueue(i - w); if (y < h - 1) enqueue(i + w); }
    for (let i = 0; i < out.length; i++) out[i] = exterior[i] ? 0 : 1;
    return out;
  }
  // lum: Float64Array/Array of luminance on the search grid (sw x sh).
  function selectComponent(lum, sw, sh, contrast) {
    const rim = Math.max(1, roundHalfUp(Math.min(sw, sh) * .12)), border = [];
    for (let i = 0; i < lum.length; i++) { const x = i % sw, y = Math.floor(i / sw); if (x < rim || y < rim || x >= sw - rim || y >= sh - rim) border.push(lum[i]); }
    const background = medianUpper(border), result = [];
    for (const polarity of (contrast === 'auto' ? ['dark', 'light'] : [contrast])) {
      const differences = new Float64Array(lum.length); let strength = -Infinity;
      for (let i = 0; i < lum.length; i++) { const d = polarity === 'dark' ? background - lum[i] : lum[i] - background; differences[i] = d; if (d > strength) strength = d; }
      if (strength < 25) continue;
      const threshold = Math.max(23, .40 * strength), candidate = new Uint8Array(lum.length);
      for (let i = 0; i < candidate.length; i++) candidate[i] = differences[i] >= threshold ? 1 : 0;
      for (const component of findComponents(candidate, sw, sh)) {
        const area = component.length; if (area < Math.max(4, sw * sh * .002) || area > sw * sh * .42) continue;
        let x0 = sw, y0 = sh, x1 = 0, y1 = 0, xsum = 0, ysum = 0, diffs = 0;
        for (const index of component) { const x = index % sw, y = Math.floor(index / sw); x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); xsum += x; ysum += y; diffs += differences[index]; }
        const bw = x1 - x0 + 1, bh = y1 - y0 + 1;
        if (x0 < 1 || y0 < 1 || x1 >= sw - 1 || y1 >= sh - 1 || bw / sw < .14 || bh / sh < .045 || bw / sw > .93 || bh / sh > .91) continue;
        const distance = ((xsum / area - sw * .5) / sw) ** 2 + ((ysum / area - sh * .5) / sh) ** 2; if (distance > .115) continue;
        const clarity = Math.min(1, diffs / area / 90), central = Math.max(0, 1 - distance / .115), coverage = Math.min(1, (bw / sw) / .4), score = .4 * clarity + .4 * central + .2 * coverage;
        if (score < .57) continue;
        result.push({score, component: component.slice().sort((a, b) => a - b), polarity, bbox: [x0, y0, x1 + 1, y1 + 1], mean: diffs / area});
      }
    }
    result.sort((a, b) => b.score - a.score);
    if (!result.length) throw Error('No isolated mouth silhouette in this region. Reposition or tighten the box, or explicitly select Graphic mode. No replacement anatomy was invented.');
    if (result[1] && result[1].polarity !== result[0].polarity && result[1].score >= result[0].score - .035) throw Error('Mouth contrast ambiguous. Select Dark or Light and regenerate.');
    return result[0];
  }
  const upsampleIndex = (x, y, regionW, regionH, sw, sh) => Math.min(sh - 1, Math.floor(y * sh / regionH)) * sw + Math.min(sw - 1, Math.floor(x * sw / regionW));
  function poseBox(outW, outH, label, jaw) {
    const mode = JAW_MODES[jaw || 'human']; const [wr, hr] = mode.ratios[label];
    const tw = Math.min(outW, Math.max(2, roundHalfUp(outW * wr * .9))), th = Math.min(outH, Math.max(1, roundHalfUp(outH * hr * .9)));
    const left = Math.floor((outW - tw) / 2);
    const top = mode.anchor === 'top' ? Math.min(Math.max(0, roundHalfUp(outH * .05)), outH - th) : Math.floor((outH - th) / 2);
    return [left, top, tw, th];
  }
  function regionBox(w, h, pos, dim) {
    const regionW = Math.max(8, roundHalfUp(dim.w * w)), regionH = Math.max(8, roundHalfUp(dim.h * h));
    const left = Math.min(w - regionW, Math.max(0, roundHalfUp(pos.x * w - regionW / 2))), top = Math.min(h - regionH, Math.max(0, roundHalfUp(pos.y * h - regionH / 2)));
    const searchScale = Math.min(1, 180 / regionW, 180 / regionH);
    return {regionW, regionH, left, top, sw: Math.max(8, roundHalfUp(regionW * searchScale)), sh: Math.max(8, roundHalfUp(regionH * searchScale))};
  }
  const api = {RATIOS, JAW_MODES, roundHalfUp, luma, medianUpper, findComponents, fillHoles, selectComponent, upsampleIndex, poseBox, regionBox};
  if (typeof module === 'object' && module.exports) module.exports = api; else root.DexTraceCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
