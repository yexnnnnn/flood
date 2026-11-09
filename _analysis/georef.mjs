import fs from 'fs';
import { encodePNG } from './png.mjs';
const dir = new URL('../', import.meta.url).pathname;
const { MW, MH, mpp } = JSON.parse(fs.readFileSync(dir + '_analysis/mosaic.json')), R = fs.readFileSync(dir + '_analysis/mosaic.rgb');
const LAT = 39.594, KX = 111320 * Math.cos(LAT * Math.PI / 180), KY = 110540;
const g = JSON.parse(fs.readFileSync(dir + 'shenjia_an_4km_osm.geojson'));
// imagery feature: brightness above local mean and low saturation  ->  roads, lanes (and roofs)
const F = 8, w = Math.floor(MW / F), h = Math.floor(MH / F), feat = new Float32Array(w * h), valid = new Uint8Array(w * h);
for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { let L = 0, Sx = 0, n = 0;
  for (let dy = 0; dy < F; dy += 2) for (let dx = 0; dx < F; dx += 2) { const i = ((y * F + dy) * MW + x * F + dx) * 3, r = R[i], gg = R[i + 1], b = R[i + 2]; if (r + gg + b === 0) continue; L += (r + gg + b) / 3; Sx += Math.max(r, gg, b) - Math.min(r, gg, b); n++; }
  if (n > 8) { valid[y * w + x] = 1; feat[y * w + x] = L / n - 0.8 * Sx / n; } }
const hp = new Float32Array(w * h); for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { if (!valid[y * w + x]) continue; let a = 0, n = 0;
  for (let dy = -6; dy <= 6; dy += 2) for (let dx = -6; dx <= 6; dx += 2) { const X = x + dx, Y = y + dy; if (X >= 0 && Y >= 0 && X < w && Y < h && valid[Y * w + X]) { a += feat[Y * w + X]; n++; } } hp[y * w + x] = feat[y * w + x] - a / n; }
// sample points along OSM roads, plus negative samples along the river centreline (water is dark)
const roadPts = [], riverPts = [];
for (const f of g.features) { const p = f.properties, gt = f.geometry.type, co = f.geometry.coordinates, lines = gt === 'LineString' ? [co] : gt === 'MultiLineString' ? co : [];
  const tgt = p.highway && !['path', 'steps', 'footway', 'construction'].includes(p.highway) ? roadPts : p.waterway === 'river' && p.name === '拒马河' ? riverPts : null; if (!tgt) continue;
  for (const L of lines) for (let k = 1; k < L.length; k++) { const [a0, b0] = L[k - 1], [a1, b1] = L[k], d = Math.hypot((a1 - a0) * KX, (b1 - b0) * KY), n = Math.ceil(d / 6);
    for (let s = 0; s < n; s++) tgt.push([a0 + (a1 - a0) * s / n, b0 + (b1 - b0) * s / n]); } }
function score(lonO, latO) { let s = 0, n = 0, r = 0, m = 0;
  for (const [lon, lat] of roadPts) { const x = Math.round((lon - lonO) * KX / mpp / F), y = Math.round((latO - lat) * KY / mpp / F); if (x < 0 || y < 0 || x >= w || y >= h || !valid[y * w + x]) continue; s += hp[y * w + x]; n++; }
  for (const [lon, lat] of riverPts) { const x = Math.round((lon - lonO) * KX / mpp / F), y = Math.round((latO - lat) * KY / mpp / F); if (x < 0 || y < 0 || x >= w || y >= h || !valid[y * w + x]) continue; r += feat[y * w + x]; m++; }
  return n > 300 ? { v: s / n - (m > 30 ? 0.15 * r / m : 0), n, m } : { v: -1e9, n, m }; }
// initial guess: west end of the river bridge near the north end of 渡外云居 at mosaic (1748,1272)
const lon0 = 115.682329 - 1748 * mpp / KX, lat0 = 39.5965632 + 1272 * mpp / KY;
let best = { v: -1e9 };
for (let dy = -450; dy <= 450; dy += 6) for (let dx = -450; dx <= 450; dx += 6) { const r = score(lon0 + dx / KX, lat0 + dy / KY); if (r.v > best.v) best = { ...r, dx, dy }; }
for (let dy = best.dy - 6; dy <= best.dy + 6; dy += 1) for (let dx = best.dx - 6; dx <= best.dx + 6; dx += 1) { const r = score(lon0 + dx / KX, lat0 + dy / KY); if (r.v > best.v) best = { ...r, dx, dy }; }
const lonO = lon0 + best.dx / KX, latO = lat0 + best.dy / KY;
// how peaked is it? second best farther than 40 m
let second = -1e9; for (let dy = -450; dy <= 450; dy += 6) for (let dx = -450; dx <= 450; dx += 6) { if (Math.hypot(dx - best.dx, dy - best.dy) < 40) continue; second = Math.max(second, score(lon0 + dx / KX, lat0 + dy / KY).v); }
console.log('shift from guess (m)', best.dx, best.dy, 'score', best.v.toFixed(2), 'second-best', second.toFixed(2), 'road samples', best.n, 'river', best.m);
console.log('mosaic origin lon', lonO.toFixed(7), 'lat', latO.toFixed(7), 'mpp', mpp.toFixed(4));
fs.writeFileSync(dir + '_analysis/georef.json', JSON.stringify({ lonO, latO, mpp, KX, KY, MW, MH }));
// overlay preview (1/4): OSM roads red, river blue, buildings yellow outline
const s = 4, W2 = Math.floor(MW / s), H2 = Math.floor(MH / s), o = new Uint8Array(W2 * H2 * 3);
for (let y = 0; y < H2; y++) for (let x = 0; x < W2; x++) for (let c = 0; c < 3; c++) o[(y * W2 + x) * 3 + c] = R[((y * s) * MW + x * s) * 3 + c] * 0.8;
const put = (lon, lat, col) => { const x = Math.round((lon - lonO) * KX / mpp / s), y = Math.round((latO - lat) * KY / mpp / s); if (x >= 0 && y >= 0 && x < W2 && y < H2) o.set(col, (y * W2 + x) * 3); };
for (const f of g.features) { const p = f.properties, gt = f.geometry.type, co = f.geometry.coordinates;
  const col = p.highway ? (['path', 'steps', 'footway'].includes(p.highway) ? [255, 120, 200] : [255, 40, 40]) : p.waterway ? [60, 140, 255] : p.building ? [255, 230, 0] : p.landuse || p.place ? [0, 255, 255] : p.natural === 'water' ? [60, 140, 255] : null; if (!col) continue;
  const lines = gt === 'LineString' ? [co] : gt === 'MultiLineString' ? co : gt === 'Polygon' ? co : gt === 'MultiPolygon' ? co.flat() : [];
  if (gt === 'Point') { for (let k = -3; k <= 3; k++) { put(co[0] + k * 2 / KX, co[1], col); put(co[0], co[1] + k * 2 / KY, col); } continue; }
  for (const L of lines) for (let k = 1; k < L.length; k++) { const [a0, b0] = L[k - 1], [a1, b1] = L[k], n = Math.ceil(Math.hypot((a1 - a0) * KX, (b1 - b0) * KY) / 1.5); for (let t = 0; t <= n; t++) put(a0 + (a1 - a0) * t / n, b0 + (b1 - b0) * t / n, col); } }
encodePNG(dir + '_analysis/overlay.png', W2, H2, o);
