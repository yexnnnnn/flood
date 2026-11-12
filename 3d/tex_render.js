// Ground texture for the 3D diorama (写实). Same inputs as v2/real_render.js (F1 shade/slope/elevation, F2 riverbed,
// G geometry in map units 0..1000) but painted for a lit 3D model: no hillshade, no painted trees or roofs
// (the 3D scene has its own sun, shadows, trees and houses), and a fresher, golf-course-like palette.
// Output 1 (window.DONE): the colour ground in the canvas.  window.MASK() then repaints the canvas with
// R = water, G = obstacle (roads, houses, courtyards: no trees), B = forest weight.
(async () => {
try {
const S = G.PX, K = S / 1000, N = S * S;
const cv = document.getElementById('c'), cx = cv.getContext('2d');
const mk = () => { const c = document.createElement('canvas'); c.width = c.height = S; return [c, c.getContext('2d', { willReadFrequently: true })]; };
const load = u => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = u; });
const field = async (u, blur) => { const [c, x] = mk(); x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high'; if (blur) x.filter = `blur(${blur}px)`; x.drawImage(await load(u), 0, 0, S, S); return x.getImageData(0, 0, S, S).data; };
const sst = (a, b, v) => { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
const mix = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
let seed = 11; const rnd = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
const hash = (i, j) => { let h = Math.imul(i, 374761393) + Math.imul(j, 668265263); h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
const vn = (x, y) => { const i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j, u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
  const a = hash(i, j), b = hash(i + 1, j), c = hash(i, j + 1), d = hash(i + 1, j + 1); return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v; };
const fbm = (x, y) => (vn(x, y) * .5 + vn(x * 2.03, y * 2.03) * .25 + vn(x * 4.1, y * 4.1) * .125 + vn(x * 8.3, y * 8.3) * .0625) / .9375;
const P = d => new Path2D(d);

const A = await field(F1), B = await field(F2, 9);               // the bed raster is 15 m cells: soften its stair steps
const maskOf = draw => { const [c, x] = mk(); x.setTransform(K, 0, 0, K, 0, 0); draw(x); return [c, x.getImageData(0, 0, S, S).data]; };
const [, VIL] = maskOf(x => { x.filter = 'blur(14px)'; x.fillStyle = '#fff';
  for (const [hx, hy, w] of G.houses) { x.beginPath(); x.arc(hx, hy, 7 + w * .4, 0, 7); x.fill(); } });
const box = (x, h, ex, ey, fy) => { x.save(); x.translate(h.x, h.y); x.rotate(h.a); x.fillRect(-h.w / 2 - ex, -h.d / 2 - ey, h.w + 2 * ex, h.d + 2 * ey + fy); x.restore(); };
const Hs = G.houses.map(([x, y, , w, d, a]) => ({ x, y, w, d, a: a * Math.PI / 180, j: (rnd() - .5) * 10 }));
const [, OB] = maskOf(x => { x.strokeStyle = x.fillStyle = '#fff'; x.lineCap = 'round';
  const W = { main: 3.2, lane: 2.0, track: .9, path: .6 }; for (const r of G.roads) { x.lineWidth = (W[r.k] || .6) + 1.0; x.stroke(P(r.d)); }
  for (const h of Hs) box(x, h, .6, .5, h.d * 1.3); });

// water channel inside the riverbed, plus mapped water bodies (alpha = wet)
const [bedC] = mk(); { const x = bedC.getContext('2d'); const im = x.createImageData(S, S); for (let p = 0; p < N; p++) im.data[p * 4 + 3] = Math.min(255, B[p * 4] * 1.6); x.putImageData(im, 0, 0); }
const [wC, wX] = mk();
wX.setTransform(K, 0, 0, K, 0, 0); wX.lineCap = wX.lineJoin = 'round';
const riv = P(G.river);
wX.filter = 'blur(4px)'; wX.strokeStyle = '#fff'; wX.lineWidth = 18; wX.stroke(riv);
wX.save(); wX.translate(3, 1.5); wX.lineWidth = 12; wX.stroke(riv); wX.restore(); wX.filter = 'none';
wX.setTransform(1, 0, 0, 1, 0, 0); wX.globalCompositeOperation = 'destination-in'; wX.filter = 'blur(1.5px)'; wX.drawImage(bedC, 0, 0); wX.filter = 'none';
wX.globalCompositeOperation = 'source-over'; wX.setTransform(K, 0, 0, K, 0, 0);
wX.filter = 'blur(2px)'; wX.fillStyle = '#fff'; for (const d of G.water) wX.fill(P(d)); wX.filter = 'none';
const WA = wX.getImageData(0, 0, S, S).data;

// ---------------------------------------------------------------- ground
const im = cx.createImageData(S, S), O = im.data;
const FOR = new Float32Array(N), FLD = new Uint8ClampedArray(N * 4);
for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
  const p = y * S + x, q = p * 4;
  const sl = A[q + 1] / 255, e = G.LO + A[q + 2] / 255 * (G.HI - G.LO), bed = B[q] / 255, vil = VIL[q + 3] / 255, wa = WA[q + 3] / 255;
  const n1 = fbm(x / 110, y / 110), n2 = fbm(x / 16 + 40, y / 16), n3 = fbm(x / 5, y / 5 + 9);
  let fw = Math.max(sst(.11, .24, sl + (n1 - .5) * .16), sst(170, 240, e + (n1 - .5) * 60) * .9);
  fw *= (1 - bed) * (1 - vil * .9);
  FOR[p] = fw;
  const meadow = mix(mix([128, 166, 64], [150, 176, 80], n2 * .8 + n3 * .2), [104, 150, 56], sst(.45, .68, n1) * .7);
  const scrub = mix([98, 136, 58], [124, 150, 70], n2);
  const floor = mix([38, 76, 34], [56, 94, 42], n3);
  let c = mix(meadow, scrub, sst(.06, .14, sl));
  c = mix(c, floor, fw);
  c = mix(c, mix([178, 172, 154], [164, 160, 140], n3), vil * .7);
  if (bed > 0) {
    let gr = mix([234, 222, 192], [216, 202, 170], n2 * .7 + n3 * .3);
    gr = mix(gr, [244, 236, 214], sst(.55, .8, fbm(x / 7, y / 40)) * .4);
    gr = mix(gr, [128, 164, 72], sst(.62, .74, n1 + n2 * .25) * .85);
    c = mix(c, gr, bed);
  }
  if (wa > 0) c = mix(c, mix([150, 156, 120], [104, 120, 96], sst(.4, 1, wa)), wa);      // river bed under the water sheet
  O[q] = c[0]; O[q + 1] = c[1]; O[q + 2] = c[2]; O[q + 3] = 255;
  FLD[q + 3] = 255 * (1 - fw) * (1 - bed) * (1 - vil) * sst(.12, .06, sl) * sst(230, 190, e) * sst(.42, .5, fbm(x / 260 + 7, y / 260)) * .92;
}
cx.putImageData(im, 0, 0);

// fields: plots on a rotated grid, masked to flat open ground; mowing-stripe furrows
{
  const [fc, fx] = mk(); const ang = -0.52;
  const pal = [[112, 160, 58], [98, 148, 52], [136, 172, 70], [152, 180, 84], [196, 184, 104], [178, 170, 92], [164, 190, 98], [120, 150, 60]];
  fx.translate(S / 2, S / 2); fx.rotate(ang); fx.translate(-S, -S);
  for (let u = 0; u < 2 * S; ) {
    const w = 14 + rnd() * 26;
    for (let v = 0; v < 2 * S; ) {
      const h = 30 + rnd() * 80, c = pal[(rnd() * pal.length) | 0], j = (rnd() - .5) * 10;
      fx.fillStyle = `rgb(${c[0] + j},${c[1] + j},${c[2] + j})`; fx.fillRect(u + .8, v + .8, w - 1.6, h - 1.6);
      if (rnd() < .75) { fx.fillStyle = 'rgba(255,255,255,.07)'; for (let a = u + 1; a < u + w - 1; a += 3.2) fx.fillRect(a, v + 1, 1.6, h - 2); }
      v += h;
    }
    u += w;
  }
  fx.setTransform(1, 0, 0, 1, 0, 0);
  const [mc] = mk(); { const m = mc.getContext('2d'), d = m.createImageData(S, S); d.data.set(FLD); m.putImageData(d, 0, 0); }
  fx.globalCompositeOperation = 'destination-in'; fx.drawImage(mc, 0, 0);
  cx.drawImage(fc, 0, 0);
}

// gullies, roads (paths and tracks kept faint), courtyards
cx.setTransform(K, 0, 0, K, 0, 0); cx.lineCap = cx.lineJoin = 'round';
for (const d of G.gully) { const g = P(d); cx.strokeStyle = 'rgb(222,214,194)'; cx.lineWidth = 2.0; cx.stroke(g); }
const RS = { main: ['rgb(232,228,218)', 3.0], lane: ['rgb(216,210,192)', 1.7], track: ['rgba(214,204,176,.55)', .7], path: ['rgba(214,204,176,.35)', .4] };
for (const k of ['path', 'track', 'lane', 'main']) for (const r of G.roads) if (r.k === k) {
  const [c, w] = RS[k] || RS.path, g = P(r.d);
  if (k === 'main' || k === 'lane') { cx.strokeStyle = 'rgba(70,80,50,.22)'; cx.lineWidth = w + .6; cx.stroke(g); }
  cx.strokeStyle = c; cx.lineWidth = w; cx.stroke(g); }
for (const h of Hs) { const j = h.j; cx.fillStyle = `rgb(${190 + j},${184 + j},${170 + j})`; box(cx, h, .35, .25, h.d * 1.3); }
cx.setTransform(1, 0, 0, 1, 0, 0);
{ const d = cx.getImageData(0, 0, S, S), o = d.data;                      // grade: +8 % saturation
  for (let p = 0; p < N; p++) { const q = p * 4, l = .3 * o[q] + .59 * o[q + 1] + .11 * o[q + 2];
    for (let c = 0; c < 3; c++) o[q + c] = l + (o[q + c] - l) * 1.08; }
  cx.putImageData(d, 0, 0); }

window.MASK = () => {
  const d = cx.createImageData(S, S), o = d.data;
  for (let p = 0; p < N; p++) { const q = p * 4; o[q] = WA[q + 3]; o[q + 1] = OB[q + 3]; o[q + 2] = FOR[p] * 255; o[q + 3] = 255; }
  cx.putImageData(d, 0, 0); return 1;
};
window.DONE = 1;
} catch (e) { console.log('ERR ' + e.stack); window.FAIL = 1; }
})();
