import fs from 'fs';
import { encodePNG } from './png.mjs';
const dir = new URL('../', import.meta.url).pathname, D = JSON.parse(fs.readFileSync(dir + 'shenjia_data.json'));
const N = D.N, cs = D.cell_m, S = 5, W = N * S, o = new Uint8Array(W * W * 3), E = D.elev;
const e = (i, j) => E[Math.min(N - 1, Math.max(0, j)) * N + Math.min(N - 1, Math.max(0, i))];
for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
  const dx = (e(i + 1, j) - e(i - 1, j)) / (2 * cs), dz = (e(i, j + 1) - e(i, j - 1)) / (2 * cs), n = [-dx, 1, -dz], l = Math.hypot(...n), hs = Math.max(0, (-n[0] * 0.6 + n[1] * 0.7 - n[2] * 0.4) / l);
  const t = (e(i, j) - D.elev_min) / (D.elev_max - D.elev_min), a = D.acc[j * N + i], wet = a > 30 ? Math.min(1, Math.log(a / 30) / 4) : 0;
  let c = [140 + 60 * t, 158 + 30 * t, 128 + 20 * t].map(v => v * (0.45 + 0.75 * hs)); c = c.map((v, k) => v * (1 - wet * 0.6) + [40, 110, 200][k] * wet * 0.6);
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) o.set(c.map(v => Math.min(255, v)), ((j * S + y) * W + i * S + x) * 3);
}
const P = (x, z) => [(x + D.half_m) / cs * S, (z + D.half_m) / cs * S];
const put = (x, z, col, r = 0) => { const [px, py] = P(x, z); for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { const X = Math.round(px + dx), Y = Math.round(py + dy); if (X >= 0 && Y >= 0 && X < W && Y < W) o.set(col, (Y * W + X) * 3); } };
const line = (pts, col, r = 0) => { for (let k = 1; k < pts.length; k++) { const [a, b] = [pts[k - 1], pts[k]], n = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 2); for (let t = 0; t <= n; t++) put(a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n, col, r); } };
for (const r of D.roads) line(r.pts, r.b ? [255, 0, 255] : r.k === 'main' ? [255, 255, 255] : r.k === 'lane' ? [255, 230, 170] : [200, 120, 80]);
line(D.river, [0, 40, 220], 1);
D.gullies.forEach((gg, k) => { line(gg.path, [255, 60, 0], 1); line(gg.run, [255, 0, 160], 1); put(gg.outlet[0], gg.outlet[1], [255, 0, 0], 5); });
for (const h of D.houses) put(h.x, h.z, h.zone === '沈家庵老村' ? [255, 255, 0] : [255, 140, 0], 1);
for (const p of D.places) put(p.x, p.z, [0, 255, 255], 4);
encodePNG(dir + '_analysis/crop_' + (process.argv[2] || 'v') + '.png', W, W, o);
