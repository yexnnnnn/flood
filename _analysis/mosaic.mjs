import fs from 'fs';
import { decodePNG, encodePNG, SHOTS, uiMask } from './png.mjs';
const dir = new URL('../', import.meta.url).pathname;
const { shots, pairs } = JSON.parse(fs.readFileSync(dir + '_analysis/pairs.json'));
// least-squares global offsets (Gauss-Seidel), shot 0 fixed
const good = pairs.filter(p => p.c > 0.8), n = shots.length, P = Array.from({ length: n }, () => [0, 0]);
for (let it = 0; it < 2000; it++) for (let s = 1; s < n; s++) { let sx = 0, sy = 0, w = 0;
  for (const p of good) { const wt = p.c * Math.sqrt(p.n); if (p.b === s) { sx += (P[p.a][0] + p.ox) * wt; sy += (P[p.a][1] + p.oy) * wt; w += wt; } if (p.a === s) { sx += (P[p.b][0] - p.ox) * wt; sy += (P[p.b][1] - p.oy) * wt; w += wt; } }
  if (w) P[s] = [sx / w, sy / w]; }
for (const p of good) console.log('residual', p.a, p.b, (P[p.b][0] - P[p.a][0] - p.ox).toFixed(1), (P[p.b][1] - P[p.a][1] - p.oy).toFixed(1));
const minX = Math.min(...P.map((p, i) => p[0])), minY = Math.min(...P.map(p => p[1]));
const pos = P.map(p => [Math.round(p[0] - minX), Math.round(p[1] - minY)]);
const MW = Math.max(...pos.map((p, i) => p[0] + shots[i].W)), MH = Math.max(...pos.map((p, i) => p[1] + shots[i].H));
console.log('mosaic', MW, 'x', MH, 'positions', JSON.stringify(pos));
// full-res mosaic: for each pixel take the shot where it is farthest from that shot's edges (feathering not needed)
const R = new Uint8Array(MW * MH * 3), best = new Float32Array(MW * MH).fill(-1);
SHOTS.forEach((name, si) => { const { W, H, rgb } = decodePNG(dir + name), [px, py] = pos[si];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { if (uiMask(x, y, W, H)) continue; const d = Math.min(x, y - 90, W - x, H - y), k = (y + py) * MW + x + px;
    if (d > best[k]) { best[k] = d; const i = (y * W + x) * 3; R[k * 3] = rgb[i]; R[k * 3 + 1] = rgb[i + 1]; R[k * 3 + 2] = rgb[i + 2]; } } });
fs.writeFileSync(dir + '_analysis/mosaic.rgb', R); fs.writeFileSync(dir + '_analysis/mosaic.json', JSON.stringify({ MW, MH, pos, mpp: 91.44 / shots[0].bar }));
// preview at 1/4
const s = 4, w = Math.floor(MW / s), h = Math.floor(MH / s), o = new Uint8Array(w * h * 3);
for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) for (let c = 0; c < 3; c++) o[(y * w + x) * 3 + c] = R[((y * s) * MW + x * s) * 3 + c];
encodePNG(dir + '_analysis/mosaic_small.png', w, h, o);
