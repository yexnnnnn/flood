import fs from 'fs';
import { encodePNG } from './png.mjs';
const dir = new URL('../', import.meta.url).pathname;
const { MW, MH } = JSON.parse(fs.readFileSync(dir + '_analysis/mosaic.json')), R = fs.readFileSync(dir + '_analysis/mosaic.rgb');
const { lonO, latO, mpp, KX, KY } = JSON.parse(fs.readFileSync(dir + '_analysis/georef.json'));
const g = JSON.parse(fs.readFileSync(dir + 'shenjia_an_4km_osm.geojson')), raw = JSON.parse(fs.readFileSync(dir + '_analysis/houses_raw.json'));
const m = (lon, lat) => [(lon - 115.678) * KX, (lat - 39.596) * KY];          // local metres (east, north)
const pip = (p, ring) => { let c = false; for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) { const a = ring[i], b = ring[j]; if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; };
const polys = {}, river = [];
for (const f of g.features) { const p = f.properties, gt = f.geometry.type, co = f.geometry.coordinates;
  if (p.landuse === 'residential' && p.name && gt === 'Polygon') polys[p.name] = co[0].map(q => m(...q));
  if (p.waterway === 'river' && p.name === '拒马河') for (let k = 1; k < co.length; k++) { const a = m(...co[k - 1]), b = m(...co[k]), n = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 5); for (let s = 0; s <= n; s++) river.push([a[0] + (b[0] - a[0]) * s / n, a[1] + (b[1] - a[1]) * s / n]); } }
const P = raw.map(h => ({ ...h, p: m(h.lon, h.lat) }));
const inPoly = (pt, name) => polys[name] && pip(pt, polys[name]);
const riverD = pt => Math.min(...river.map(r => Math.hypot(r[0] - pt[0], r[1] - pt[1])));
const near = (pt, r) => P.filter(q => Math.hypot(q.p[0] - pt[0], q.p[1] - pt[1]) < r).length - 1;
const VILLA = ['渡外云居', '一渡新新小镇', '一渡青青小镇'];
let out = [];
for (const h of P) {
  const villa = VILLA.find(n => inPoly(h.p, n));
  if (h.p[1] > 600) continue;                                       // north edge of crop area is farmland
  if (riverD(h.p) < 70 && !villa) continue;                         // riverbed / gravel bars
  if (h.p[0] > riverD(h.p) * 0 + 300 && !villa && h.p[0] > 330) { if (near(h.p, 35) < 4) continue; }   // east bank: only real clusters
  if (!villa && near(h.p, 32) < 3) continue;                        // isolated = probably a field / bare patch
  out.push({ ...h, zone: villa || '沈家庵老村' });
}
// 渡外云居: dark villa roofs are hard to segment; fill the OSM polygon with detached villas on its internal lanes
const dw = polys['渡外云居'], bb = [Math.min(...dw.map(q => q[0])), Math.max(...dw.map(q => q[0])), Math.min(...dw.map(q => q[1])), Math.max(...dw.map(q => q[1]))];
out = out.filter(h => h.zone !== '渡外云居');
for (let y = bb[2] + 14; y < bb[3] - 10; y += 26) for (let x = bb[0] + 14; x < bb[1] - 10; x += 34) { const pt = [x + ((y / 26) % 2) * 6, y]; if (pip(pt, dw) && riverD(pt) > 45) out.push({ p: pt, m2: 170, ang: 0, kind: 'villaD', zone: '渡外云居', big: false }); }
const cnt = {}; for (const h of out) cnt[h.zone + '/' + h.kind] = (cnt[h.zone + '/' + h.kind] || 0) + 1;
console.log('kept', out.length, JSON.stringify(cnt, null, 0));
const res = out.map(h => ({ x: Math.round(h.p[0] * 10) / 10, z: Math.round(-h.p[1] * 10) / 10, m2: h.m2, ang: h.ang, kind: h.kind, zone: h.zone, big: h.big }));
fs.writeFileSync(dir + 'shenjia_an_houses.json', JSON.stringify({ origin: { lon: 115.678, lat: 39.596, note: 'x = metres east, z = metres south of origin' }, source: 'roofs detected in user satellite screenshots (mapbox), georeferenced to OSM; 渡外云居 filled from its OSM outline', houses: res }));
// comparison image: imagery left, imagery + detected houses + OSM outlines right
const s = 3, W2 = Math.floor(MW / s), H2 = Math.floor(MH / s), o = new Uint8Array(W2 * 2 * H2 * 3);
for (let y = 0; y < H2; y++) for (let x = 0; x < W2; x++) { const i = ((y * s) * MW + x * s) * 3; o.set([R[i], R[i + 1], R[i + 2]], (y * W2 * 2 + x) * 3); o.set([R[i] * 0.55, R[i + 1] * 0.55, R[i + 2] * 0.55], (y * W2 * 2 + W2 + x) * 3); }
const toPx = pt => [((pt[0] / KX + 115.678) - lonO) * KX / mpp / s, (latO - (pt[1] / KY + 39.596)) * KY / mpp / s];
const dot = (pt, r, col) => { const [cx, cy] = toPx(pt); for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { const X = Math.round(cx + dx), Y = Math.round(cy + dy); if (X >= 0 && Y >= 0 && X < W2 && Y < H2) o.set(col, (Y * W2 * 2 + W2 + X) * 3); } };
for (const ring of Object.values(polys)) for (let k = 1; k < ring.length; k++) { const a = ring[k - 1], b = ring[k], n = 60; for (let t = 0; t <= n; t++) dot([a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n], 0, [0, 230, 230]); }
for (const r of river) dot(r, 0, [80, 150, 255]);
const ZC = { '沈家庵老村': [255, 235, 0], '渡外云居': [230, 60, 255], '一渡新新小镇': [255, 140, 0], '一渡青青小镇': [255, 90, 90] };
for (const h of out) dot(h.p, 3, ZC[h.zone]);
encodePNG(dir + '_analysis/houses_check.png', W2 * 2, H2, o);
