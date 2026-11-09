import fs from 'fs';
import { decodePNG, SHOTS, uiMask } from './png.mjs';
const dir = new URL('../', import.meta.url).pathname, F = 4;
const shots = SHOTS.map((name, si) => {
  const t0 = Date.now(), { W, H, rgb } = decodePNG(dir + name);
  // scale bar: blue (#3f7fff-ish) horizontal line near the bottom right
  let bx0 = 1e9, bx1 = -1, by = 0;
  for (let y = H - 80; y < H - 20; y++) for (let x = W - 520; x < W - 150; x++) { const i = (y * W + x) * 3, r = rgb[i], g = rgb[i + 1], b = rgb[i + 2];
    if (b > 180 && r < 110 && g > 80 && g < 170) { if (x < bx0) bx0 = x; if (x > bx1) bx1 = x; by = y; } }
  const w = Math.floor(W / F), h = Math.floor(H / F), gray = new Float32Array(w * h), mask = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { let s = 0, bad = 0;
    for (let dy = 0; dy < F; dy++) for (let dx = 0; dx < F; dx++) { const X = x * F + dx, Y = y * F + dy, i = (Y * W + X) * 3; s += rgb[i] * 0.3 + rgb[i + 1] * 0.59 + rgb[i + 2] * 0.11; if (uiMask(X, Y, W, H)) bad = 1; }
    gray[y * w + x] = s / (F * F); mask[y * w + x] = bad ? 0 : 1; }
  fs.writeFileSync(dir + `_analysis/g${si}.bin`, Buffer.from(gray.buffer)); fs.writeFileSync(dir + `_analysis/m${si}.bin`, Buffer.from(mask.buffer));
  console.log(si, name, W, H, 'scalebar px', bx1 - bx0 + 1, 'at y', by, 'decode ms', Date.now() - t0);
  return { W, H, w, h, gray, mask, bar: bx1 - bx0 + 1 };
});
// high-pass (remove illumination differences) then normalized cross-correlation over integer offsets
function hp(s) { const { w, h, gray } = s, o = new Float32Array(w * h), r = 6;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { let a = 0, n = 0; for (let dy = -r; dy <= r; dy += 3) for (let dx = -r; dx <= r; dx += 3) { const X = x + dx, Y = y + dy; if (X >= 0 && Y >= 0 && X < w && Y < h) { a += gray[Y * w + X]; n++; } } o[y * w + x] = gray[y * w + x] - a / n; }
  return o; }
const HP = shots.map(hp);
function ncc(a, b, ox, oy, step) { // b placed at (ox,oy) relative to a, in downsampled px
  const A = shots[a], B = shots[b]; let sa = 0, sb = 0, saa = 0, sbb = 0, sab = 0, n = 0;
  const x0 = Math.max(0, ox), y0 = Math.max(0, oy), x1 = Math.min(A.w, B.w + ox), y1 = Math.min(A.h, B.h + oy);
  for (let y = y0; y < y1; y += step) for (let x = x0; x < x1; x += step) { const ia = y * A.w + x, ib = (y - oy) * B.w + (x - ox); if (!A.mask[ia] || !B.mask[ib]) continue;
    const u = HP[a][ia], v = HP[b][ib]; sa += u; sb += v; saa += u * u; sbb += v * v; sab += u * v; n++; }
  if (n < 1500 / (step * step)) return { c: -1, n };
  const cov = sab - sa * sb / n, va = saa - sa * sa / n, vb = sbb - sb * sb / n; return { c: cov / Math.sqrt(va * vb + 1e-9), n: n * step * step };
}
const pairs = [];
for (let a = 0; a < shots.length; a++) for (let b = a + 1; b < shots.length; b++) {
  const A = shots[a], B = shots[b]; let best = { c: -1 };
  for (let oy = -B.h + 40; oy < A.h - 40; oy += 3) for (let ox = -B.w + 40; ox < A.w - 40; ox += 3) { const r = ncc(a, b, ox, oy, 3); if (r.c > best.c) best = { ...r, ox, oy }; }
  for (let k = 0; k < 2; k++) { const c0 = best; for (let oy = c0.oy - 3; oy <= c0.oy + 3; oy++) for (let ox = c0.ox - 3; ox <= c0.ox + 3; ox++) { const r = ncc(a, b, ox, oy, 1); if (r.c > best.c || best === c0) if (r.c > (best === c0 ? -1 : best.c)) best = { ...r, ox, oy }; } }
  console.log('pair', a, b, 'offset(full px)', best.ox * F, best.oy * F, 'ncc', best.c.toFixed(3), 'overlap px', best.n);
  pairs.push({ a, b, ox: best.ox * F, oy: best.oy * F, c: best.c, n: best.n });
}
fs.writeFileSync(dir + '_analysis/pairs.json', JSON.stringify({ shots: shots.map(s => ({ W: s.W, H: s.H, bar: s.bar })), pairs }, null, 1));
