// 写实底图 canvas renderer. Inputs (inlined by real_base.py): F1 = PNG (shade, slope, elevation), F2 = PNG (riverbed),
// G = geometry in map units (0..1000). Output: the canvas, PX x PX, 1 px = 1 m. Sun from the NW, shadows fall SE.
(async () => {
try {
const S = G.PX, K = S / 1000, N = S * S;
const cv = document.getElementById('c'), cx = cv.getContext('2d');
const mk = () => { const c = document.createElement('canvas'); c.width = c.height = S; return [c, c.getContext('2d', { willReadFrequently: true })]; };
const load = u => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = u; });
const field = async u => { const [c, x] = mk(); x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high'; x.drawImage(await load(u), 0, 0, S, S); return x.getImageData(0, 0, S, S).data; };
const sst = (a, b, v) => { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
const mix = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
let seed = 7; const rnd = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
const hash = (i, j) => { let h = Math.imul(i, 374761393) + Math.imul(j, 668265263); h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
const vn = (x, y) => { const i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j, u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
  const a = hash(i, j), b = hash(i + 1, j), c = hash(i, j + 1), d = hash(i + 1, j + 1); return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v; };
const fbm = (x, y) => (vn(x, y) * .5 + vn(x * 2.03, y * 2.03) * .25 + vn(x * 4.1, y * 4.1) * .125 + vn(x * 8.3, y * 8.3) * .0625) / .9375;
const P = d => new Path2D(d);

// ---------------------------------------------------------------- inputs
const A = await field(F1), B = await field(F2);
const maskOf = draw => { const [c, x] = mk(); x.setTransform(K, 0, 0, K, 0, 0); draw(x); return [c, x.getImageData(0, 0, S, S).data]; };
// house density -> village ground
const [, VIL] = maskOf(x => { x.filter = 'blur(14px)'; x.fillStyle = '#fff';
  for (const [hx, hy, w] of G.houses) { x.beginPath(); x.arc(hx, hy, 7 + w * .4, 0, 7); x.fill(); } });
const ROADW = { main: 3.2, lane: 2.0, track: .9, path: .6 };
const [, RD] = maskOf(x => { x.strokeStyle = '#fff'; x.lineCap = 'round'; for (const r of G.roads) { x.lineWidth = (ROADW[r.k] || .6) + 1.2; x.stroke(P(r.d)); } });

// water: river channel kept inside the riverbed, plus the mapped water bodies
const [bedC] = mk(); { const x = bedC.getContext('2d'); const im = x.createImageData(S, S); for (let p = 0; p < N; p++) { im.data[p * 4 + 3] = Math.min(255, B[p * 4] * 1.6); } x.putImageData(im, 0, 0); }
const [wC, wX] = mk();
wX.setTransform(K, 0, 0, K, 0, 0); wX.lineCap = wX.lineJoin = 'round';
const riv = P(G.river);
wX.filter = 'blur(5px)';
wX.strokeStyle = 'rgba(112,118,96,.5)'; wX.lineWidth = 26; wX.stroke(riv);              // wet margin
wX.strokeStyle = 'rgb(46,74,58)'; wX.lineWidth = 18; wX.stroke(riv);
wX.save(); wX.translate(3, 1.5); wX.lineWidth = 12; wX.stroke(riv); wX.restore();
wX.filter = 'blur(9px)'; wX.strokeStyle = 'rgba(30,54,44,.8)'; wX.lineWidth = 7; wX.stroke(riv);   // deep thalweg
wX.filter = 'none';
wX.setTransform(1, 0, 0, 1, 0, 0); wX.globalCompositeOperation = 'destination-in'; wX.filter = 'blur(1.5px)'; wX.drawImage(bedC, 0, 0); wX.filter = 'none';
wX.globalCompositeOperation = 'source-over'; wX.setTransform(K, 0, 0, K, 0, 0);
wX.filter = 'blur(3px)'; for (const d of G.water) { wX.fillStyle = 'rgb(48,76,62)'; wX.fill(P(d)); } wX.filter = 'none';
for (const d of G.ditch) { wX.strokeStyle = 'rgba(52,78,70,.9)'; wX.lineWidth = .9; wX.stroke(P(d)); }
const WA = wX.getImageData(0, 0, S, S).data;

// ---------------------------------------------------------------- 1. ground
const im = cx.createImageData(S, S), O = im.data;
const FOR = new Float32Array(N), FLD = new Uint8ClampedArray(N * 4);
for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
  const p = y * S + x, q = p * 4;
  const sl = A[q + 1] / 255, e = G.LO + A[q + 2] / 255 * (G.HI - G.LO), bed = B[q] / 255, vil = VIL[q + 3] / 255;
  const n1 = fbm(x / 110, y / 110), n2 = fbm(x / 16 + 40, y / 16), n3 = fbm(x / 5, y / 5 + 9);
  let fw = Math.max(sst(.11, .24, sl + (n1 - .5) * .16), sst(170, 240, e + (n1 - .5) * 60) * .9);
  fw *= (1 - bed) * (1 - vil * .9);
  FOR[p] = fw;
  const meadow = mix(mix([134, 124, 84], [158, 140, 100], n2 * .8 + n3 * .2), [102, 116, 68], sst(.45, .68, n1) * .65);
  const scrub = mix([92, 102, 62], [128, 120, 84], n2);
  const floor = mix([44, 64, 36], [64, 84, 46], n3);
  let c = mix(meadow, scrub, sst(.06, .14, sl));
  c = mix(c, floor, fw);
  c = mix(c, mix([166, 160, 146], [146, 142, 130], n3), vil * .92);
  if (bed > 0) {
    let gr = mix([206, 196, 176], [176, 166, 146], n2 * .7 + n3 * .3);
    gr = mix(gr, [222, 214, 196], sst(.55, .8, fbm(x / 7, y / 40)) * .35);          // flood streaks
    gr = mix(gr, [118, 130, 88], sst(.62, .74, n1 + n2 * .25) * .8);                // vegetated bars
    c = mix(c, gr, bed);
  }
  O[q] = c[0]; O[q + 1] = c[1]; O[q + 2] = c[2]; O[q + 3] = 255;
  FLD[q + 3] = 255 * (1 - fw) * (1 - bed) * (1 - vil) * sst(.12, .06, sl) * sst(230, 190, e) * sst(.42, .5, fbm(x / 260 + 7, y / 260)) * .92;
}
cx.putImageData(im, 0, 0);

// ---------------------------------------------------------------- 2. fields (plots on a rotated grid, masked to flat open ground)
{
  const [fc, fx] = mk(); const ang = -0.52, pal = [[96, 118, 62], [84, 108, 56], [150, 136, 98], [164, 148, 108], [110, 124, 70], [138, 128, 90], [78, 100, 52]];
  fx.translate(S / 2, S / 2); fx.rotate(ang); fx.translate(-S, -S);
  for (let u = 0; u < 2 * S; ) {
    const w = 14 + rnd() * 26;
    for (let v = 0; v < 2 * S; ) {
      const h = 30 + rnd() * 80, c = pal[(rnd() * pal.length) | 0], j = (rnd() - .5) * 14;
      fx.fillStyle = `rgb(${c[0] + j},${c[1] + j},${c[2] + j})`; fx.fillRect(u + 1, v + 1, w - 2, h - 2);
      const kind = rnd();
      if (kind < .3) {                                                                   // orchard rows
        for (let a = u + 3; a < u + w - 2; a += 4.5) for (let b = v + 3; b < v + h - 2; b += 4.5) {
          fx.fillStyle = 'rgba(40,64,36,.55)'; fx.beginPath(); fx.arc(a + 1, b + 1, 1.7, 0, 7); fx.fill();
          fx.fillStyle = 'rgba(78,108,56,.9)'; fx.beginPath(); fx.arc(a, b, 1.5, 0, 7); fx.fill(); }
      } else if (kind < .8) {                                                            // furrows
        fx.fillStyle = 'rgba(30,40,20,.10)'; for (let a = u + 2; a < u + w - 1; a += 2.2) fx.fillRect(a, v + 1, .9, h - 2);
      }
      v += h;
    }
    u += w;
  }
  fx.setTransform(1, 0, 0, 1, 0, 0);
  const [mc] = mk(); { const m = mc.getContext('2d'), d = m.createImageData(S, S); d.data.set(FLD); m.putImageData(d, 0, 0); }
  fx.globalCompositeOperation = 'destination-in'; fx.drawImage(mc, 0, 0);
  cx.drawImage(fc, 0, 0);
}

// ---------------------------------------------------------------- 3. gullies (dry debris channels, pale gravel), water
cx.setTransform(K, 0, 0, K, 0, 0); cx.lineCap = cx.lineJoin = 'round';
for (const d of G.gully) { const g = P(d);
  cx.strokeStyle = 'rgba(90,96,70,.35)'; cx.lineWidth = 3.4; cx.stroke(g);
  cx.strokeStyle = 'rgb(200,194,178)'; cx.lineWidth = 2.2; cx.stroke(g);
  cx.strokeStyle = 'rgba(232,228,216,.7)'; cx.lineWidth = .8; cx.stroke(g); }
cx.setTransform(1, 0, 0, 1, 0, 0); cx.drawImage(wC, 0, 0);

// ---------------------------------------------------------------- 3b. road surfaces, then house compounds (courtyard + roof + cast shadow)
cx.setTransform(K, 0, 0, K, 0, 0); cx.lineCap = cx.lineJoin = 'round';
const RS = { main: ['rgb(178,176,170)', 3.2], lane: ['rgb(168,162,148)', 2.0], track: ['rgba(164,146,112,.8)', .8], path: ['rgba(160,142,108,.55)', .45] };
for (const k of ['path', 'track', 'lane', 'main']) for (const r of G.roads) if (r.k === k) {
  const [c, w] = RS[k] || RS.path, g = P(r.d);
  if (k === 'main' || k === 'lane') { cx.strokeStyle = 'rgba(60,62,50,.28)'; cx.lineWidth = w + .7; cx.stroke(g); }
  cx.strokeStyle = c; cx.lineWidth = w; cx.stroke(g); }
const [hmC, hmX] = mk(); hmX.setTransform(K, 0, 0, K, 0, 0); hmX.fillStyle = '#fff';
const ROOF = [[[158, 156, 150], 40], [[196, 194, 188], 20], [[114, 114, 112], 14], [[178, 168, 150], 10], [[92, 112, 150], 6], [[158, 94, 80], 3], [[108, 138, 136], 3]];
const pick = () => { let t = rnd() * 100; for (const [c, w] of ROOF) { if ((t -= w) < 0) return c; } return ROOF[0][0]; };
const Hs = G.houses.map(([x, y, , w, d, a]) => ({ x, y, w, d, a: a * Math.PI / 180, c: pick(), j: (rnd() - .5) * 16, ridge: rnd() < .55 }));
const box = (x, h, dx, dy, ex, ey, fy) => { x.save(); x.translate(h.x + dx, h.y + dy); x.rotate(h.a); x.fillRect(-h.w / 2 - ex, -h.d / 2 - ey, h.w + 2 * ex, h.d + 2 * ey + fy); x.restore(); };
for (const h of Hs) { const j = h.j * .5;                                                  // courtyard + wall
  cx.fillStyle = `rgb(${148 + j},${144 + j},${134 + j})`; box(cx, h, 0, 0, .35, .25, h.d * 1.3);
  cx.strokeStyle = 'rgba(92,88,78,.55)'; cx.lineWidth = .22; cx.save(); cx.translate(h.x, h.y); cx.rotate(h.a);
  cx.strokeRect(-h.w / 2 - .35, -h.d / 2 - .25, h.w + .7, h.d + .5 + h.d * 1.3); cx.restore(); }
cx.fillStyle = 'rgba(22,26,20,.5)'; for (const h of Hs) box(cx, h, .55, .55, 0, 0, 0);   // cast shadow to the SE
for (const h of Hs) { const [r, g, b] = h.c, j = h.j;
  cx.fillStyle = `rgb(${r + j},${g + j},${b + j})`; box(cx, h, 0, 0, 0, 0, 0); box(hmX, h, 0, 0, 0, 0, 0);
  cx.save(); cx.translate(h.x, h.y); cx.rotate(h.a);
  if (h.ridge) { cx.fillStyle = 'rgba(255,255,255,.14)'; cx.fillRect(-h.w / 2, -h.d / 2, h.w, h.d / 2);   // lit north slope
    cx.fillStyle = 'rgba(0,0,0,.10)'; cx.fillRect(-h.w / 2, 0, h.w, h.d / 2); }
  else { cx.strokeStyle = 'rgba(255,255,255,.22)'; cx.lineWidth = .18; cx.strokeRect(-h.w / 2 + .15, -h.d / 2 + .15, h.w - .3, h.d - .3); }
  cx.restore(); }
cx.setTransform(1, 0, 0, 1, 0, 0);
const HM = hmX.getImageData(0, 0, S, S).data;

// ---------------------------------------------------------------- 4. trees (sprites: shadow pass, then crowns)
const R0 = 10, spr = (draw) => { const c = document.createElement('canvas'); c.width = c.height = R0 * 2 + 2; draw(c.getContext('2d')); return c; };
const TONES = [[42, 68, 38], [52, 80, 44], [64, 92, 50], [78, 104, 56], [36, 58, 34], [92, 114, 60], [58, 74, 40]];
const crowns = TONES.map(t => spr(x => { const g = x.createRadialGradient(R0 * .62, R0 * .62, 0, R0 + 1, R0 + 1, R0);
  g.addColorStop(0, `rgb(${t[0] * 1.55},${t[1] * 1.45},${t[2] * 1.4})`); g.addColorStop(.55, `rgb(${t[0]},${t[1]},${t[2]})`);
  g.addColorStop(1, `rgb(${t[0] * .62},${t[1] * .66},${t[2] * .62})`); x.fillStyle = g; x.beginPath(); x.arc(R0 + 1, R0 + 1, R0, 0, 7); x.fill(); }));
const shadow = spr(x => { const g = x.createRadialGradient(R0 + 1, R0 + 1, 0, R0 + 1, R0 + 1, R0);
  g.addColorStop(0, 'rgba(10,20,8,.6)'); g.addColorStop(.7, 'rgba(10,20,8,.35)'); g.addColorStop(1, 'rgba(10,20,8,0)'); x.fillStyle = g; x.fillRect(0, 0, 99, 99); });
const T = [], step = 4.2;
for (let y = 0; y < S; y += step) for (let x = 0; x < S; x += step) {
  const px = x + rnd() * step, py = y + rnd() * step, p = (py | 0) * S + (px | 0), q = p * 4; if (p >= N) continue;
  if (WA[q + 3] > 40 || RD[q + 3] > 30 || HM[q + 3] > 60) continue;
  const fw = FOR[p], bed = B[q] / 255, vil = VIL[q + 3] / 255;
  const pr = fw * .78 + (1 - fw) * (vil * .09 + (1 - bed) * .035 + bed * .012);
  if (rnd() > pr) continue;
  const big = fw > .5;
  const r = big ? 2.4 + rnd() * 2.6 : 1.8 + rnd() * 2.4;
  const tone = big ? [0, 1, 4, 2, 6][(rnd() * 5) | 0] : [2, 3, 5, 1][(rnd() * 4) | 0];
  T.push([px, py, r, tone]);
}
for (const [x, y, r] of T) cx.drawImage(shadow, x + r * .55 - r * 1.25, y + r * .55 - r * 1.25, r * 2.5, r * 2.5);
for (const [x, y, r, t] of T) cx.drawImage(crowns[t], x - r, y - r, r * 2, r * 2);

// ---------------------------------------------------------------- 5. hillshade over everything + grade
{
  const d = cx.getImageData(0, 0, S, S), o = d.data;
  for (let p = 0; p < N; p++) {
    const q = p * 4, wa = 1 - WA[q + 3] / 255 * .85, s = (A[q] / 127.5 - 1) * wa, f = s < 0 ? 1 + s * .44 : 1 + s * .16;
    let r = o[q] * f, g = o[q + 1] * f, b = o[q + 2] * (f + (s < 0 ? -s * .1 : 0));
    const l = .3 * r + .59 * g + .11 * b;                          // saturation +12 %, contrast +6 %
    r = l + (r - l) * 1.12; g = l + (g - l) * 1.12; b = l + (b - l) * 1.12;
    o[q] = (r - 118) * 1.06 + 118; o[q + 1] = (g - 118) * 1.06 + 118; o[q + 2] = (b - 118) * 1.06 + 118;
  }
  cx.putImageData(d, 0, 0);
}
window.DONE = T.length;
} catch (e) { console.log('ERR ' + e.stack); window.FAIL = 1; }
})();
