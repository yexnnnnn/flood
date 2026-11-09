import fs from 'fs';
import { encodePNG } from './png.mjs';
import { cls } from './roofs.mjs';
const dir = new URL('../', import.meta.url).pathname;
const { MW, MH } = JSON.parse(fs.readFileSync(dir + '_analysis/mosaic.json')), R = fs.readFileSync(dir + '_analysis/mosaic.rgb');
const G = JSON.parse(fs.readFileSync(dir + '_analysis/georef.json')), { lonO, latO, mpp, KX, KY } = G;
const toLL = (x, y) => [lonO + x * mpp / KX, latO - y * mpp / KY];
const C = new Uint8Array(MW * MH); for (let k = 0; k < MW * MH; k++) C[k] = cls(R[k * 3], R[k * 3 + 1], R[k * 3 + 2]);
// map labels / UI text in the imagery: white text with dark outline -> ignore the label boxes we can see
// group roof classes: A = flat/light/blue/red (old village), V = salmon villa, D = dark villa
const groupOf = c => c === 1 || c === 2 || c === 3 ? 1 : c === 5 ? 2 : c === 4 ? 3 : 0;
// 1-px erosion to separate roofs touching through thin bridges
const M = new Uint8Array(MW * MH);
for (let y = 1; y < MH - 1; y++) for (let x = 1; x < MW - 1; x++) { const k = y * MW + x, g = groupOf(C[k]); if (!g) continue;
  if (groupOf(C[k - 1]) === g && groupOf(C[k + 1]) === g && groupOf(C[k - MW]) === g && groupOf(C[k + MW]) === g) M[k] = g; }
const lab = new Int32Array(MW * MH), comps = [], stack = [];
for (let s = 0; s < MW * MH; s++) { if (!M[s] || lab[s]) continue; const g = M[s], id = comps.length + 1; let n = 0, sx = 0, sy = 0, sxx = 0, syy = 0, sxy = 0, x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1, red = 0, blue = 0;
  stack.push(s); lab[s] = id;
  while (stack.length) { const k = stack.pop(), x = k % MW, y = (k / MW) | 0; n++; sx += x; sy += y; sxx += x * x; syy += y * y; sxy += x * y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; if (C[k] === 3) red++; if (C[k] === 2) blue++;
    for (const d of [1, -1, MW, -MW]) { const q = k + d; if (q >= 0 && q < MW * MH && M[q] === g && !lab[q]) { lab[q] = id; stack.push(q); } } }
  const mx = sx / n, my = sy / n, cxx = sxx / n - mx * mx, cyy = syy / n - my * my, cxy = sxy / n - mx * my;
  const tr = cxx + cyy, det = cxx * cyy - cxy * cxy, l1 = tr / 2 + Math.sqrt(Math.max(0, tr * tr / 4 - det)), l2 = tr / 2 - Math.sqrt(Math.max(0, tr * tr / 4 - det));
  comps.push({ id, g, n, mx, my, ang: 0.5 * Math.atan2(2 * cxy, cxx - cyy), elong: Math.sqrt(l1 / Math.max(l2, 1e-6)), fill: n / ((x1 - x0 + 1) * (y1 - y0 + 1)), bw: x1 - x0 + 1, bh: y1 - y0 + 1, red, blue }); }
const A_M2 = mpp * mpp, houses = [];
for (const c of comps) {
  const m2 = c.n * A_M2;
  if (c.g === 1) { // flat roofs: 25-400 m2 single houses; larger blobs = several houses in a row
    if (m2 < 22 || c.elong > 6 || c.fill < 0.3) continue;
    const k = m2 > 260 ? Math.min(12, Math.round(m2 / 140)) : 1;
    if (k === 1) houses.push({ x: c.mx, y: c.my, m2, ang: c.ang, kind: c.red > c.n * 0.3 ? 'red' : c.blue > c.n * 0.3 ? 'blue' : 'flat', big: m2 > 1500 });
    else { // spread k points along the long axis of the blob
      const ux = Math.cos(c.ang), uy = Math.sin(c.ang), L = Math.sqrt(c.n) * Math.min(c.elong, 4) * 0.5;
      for (let i = 0; i < k; i++) { const t = (i + 0.5) / k - 0.5; houses.push({ x: c.mx + ux * t * L * 1.6, y: c.my + uy * t * L * 1.6, m2: m2 / k, ang: c.ang, kind: 'flat', big: false }); } } }
  else if (c.g === 2) { if (m2 < 40 || c.fill < 0.35) continue; const k = m2 > 420 ? Math.min(6, Math.round(m2 / 200)) : 1; // terraced rows split
    const ux = Math.cos(c.ang), uy = Math.sin(c.ang), L = Math.sqrt(c.n) * Math.min(c.elong, 4) * 0.5;
    for (let i = 0; i < k; i++) { const t = k > 1 ? (i + 0.5) / k - 0.5 : 0; houses.push({ x: c.mx + ux * t * L * 1.6, y: c.my + uy * t * L * 1.6, m2: m2 / k, ang: c.ang, kind: 'villaS', big: false }); } }
  else if (c.g === 3) { if (m2 < 60 || m2 > 420 || c.fill < 0.5 || c.elong > 2.2) continue; houses.push({ x: c.mx, y: c.my, m2, ang: c.ang, kind: 'villaD', big: false }); }
}
// de-duplicate points closer than 4 m
houses.sort((a, b) => a.y - b.y); const keep = [];
for (const h of houses) { if (keep.some(q => Math.abs(q.y - h.y) < 9 && Math.hypot(q.x - h.x, q.y - h.y) < 4 / mpp)) continue; keep.push(h); }
const out = keep.map(h => { const [lon, lat] = toLL(h.x, h.y); return { lon: +lon.toFixed(7), lat: +lat.toFixed(7), m2: Math.round(h.m2), ang: +h.ang.toFixed(2), kind: h.kind, big: h.big }; });
const cnt = {}; for (const h of out) cnt[h.kind] = (cnt[h.kind] || 0) + 1;
console.log('components', comps.length, 'houses', out.length, JSON.stringify(cnt));
fs.writeFileSync(dir + '_analysis/houses_raw.json', JSON.stringify(out));
// preview 1/3 with dots
const s = 3, W2 = Math.floor(MW / s), H2 = Math.floor(MH / s), o = new Uint8Array(W2 * H2 * 3);
for (let y = 0; y < H2; y++) for (let x = 0; x < W2; x++) for (let c = 0; c < 3; c++) o[(y * W2 + x) * 3 + c] = R[((y * s) * MW + x * s) * 3 + c] * 0.75;
const KC = { flat: [255, 255, 0], red: [255, 60, 60], blue: [80, 160, 255], villaS: [255, 140, 0], villaD: [230, 0, 255] };
for (const h of keep) { const cx = Math.round(h.x / s), cy = Math.round(h.y / s), r = h.big ? 5 : 2; for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { const X = cx + dx, Y = cy + dy; if (X >= 0 && Y >= 0 && X < W2 && Y < H2) o.set(KC[h.kind], (Y * W2 + X) * 3); } }
encodePNG(dir + '_analysis/houses_preview.png', W2, H2, o);
