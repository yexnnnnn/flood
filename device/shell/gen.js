#!/usr/bin/env node
// 观察器外壳生成器 · shell generator for the ATOM Echo + TailBat observation button.
// Pure Node, no dependencies:  node device/shell/gen.js  [A|B|C ...]
// Writes, per design:
//   out/<id>.3mf          base + lid + button cap laid out on one plate, drag into Bambu Studio
//   out/view/<id>_*.bin   light meshes for view.html (rotatable preview)
// Shapes are signed distance functions (mm, z up) meshed with surface nets.
//
// Electronics frame: the ATOM sits on the cavity floor (z = 0) with its button face up (+z).
// The TailBat is plugged into the ATOM's USB-C side and sticks out along +x.
'use strict';
const fs = require('fs'), path = require('path'), zlib = require('zlib');

// ============================================================ hardware: measure the real parts, then edit these
const HW = {
  atom: 24, atomH: 17,      // ATOM Echo body (official 24 x 24 x 17 mm)
  batL: 31,                 // TailBat length sticking out beyond the ATOM   <-- NOT VERIFIED, measure it
  batW: 24, batH: 14,       // TailBat width and height (listed as 24 x 14)  <-- check
  cl: .3,                   // clearance around the electronics
  usbZ: 7,                  // height of the TailBat's own USB-C (charging) port centre <-- check
};
const PRINT = { tol: .2 };  // sliding fit between printed parts

// ------------------------------------------------------------ derived layout
const L = HW.atom + HW.batL, X0 = -L / 2;               // stack centred on x = 0
const AX = X0 + HW.atom / 2;                             // ATOM centre x (button axis)
const AH = HW.atom / 2 + HW.cl, TOP = HW.atomH + HW.cl;  // cavity half-width, cavity ceiling over the ATOM
const BX0 = X0 + HW.atom - 1, BX1 = X0 + L + HW.cl;      // TailBat cavity x range (1 mm overlap)
const BH = HW.batH + HW.cl, BW = HW.batW / 2 + HW.cl;
let ZS = 9;                                            // split plane between base and lid
const CAP_R = 12.5, HOLE_R = CAP_R + PRINT.tol + .1;     // button cap and its hole
const FL_R = CAP_R + 1.2, FL_Z0 = HW.atomH + .15, FL_Z1 = FL_Z0 + 1.2;   // cap flange (keeps the cap from falling out)
const PK_R = FL_R + .4, PK_Z0 = HW.atomH, PK_Z1 = FL_Z1 + .35;    // pocket in the lid for the flange

// ============================================================ SDF toolkit
const { sqrt, abs, min, max, cos, sin, atan2, exp, PI, hypot } = Math;
const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
const smin = (a, b, k) => { const h = clamp(.5 + .5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h); };
const smax = (a, b, k) => -smin(-a, -b, k);
function box(x, y, z, cx, cy, cz, hx, hy, hz, r) {
  const qx = abs(x - cx) - hx + r, qy = abs(y - cy) - hy + r, qz = abs(z - cz) - hz + r;
  return hypot(max(qx, 0), max(qy, 0), max(qz, 0)) + min(max(qx, qy, qz), 0) - r; }
function ell(x, y, z, cx, cy, cz, rx, ry, rz) {           // ellipsoid (good-enough distance)
  const px = (x - cx) / rx, py = (y - cy) / ry, pz = (z - cz) / rz, k0 = hypot(px, py, pz);
  const k1 = hypot(px / rx, py / ry, pz / rz); return k1 < 1e-9 ? -min(rx, ry, rz) : k0 * (k0 - 1) / k1; }
const cylZ = (x, y, cx, cy, r) => hypot(x - cx, y - cy) - r;
// superellipse |x/a|^n + |y/b|^n = 1, distance from a first-order (gradient-normalised) estimate
function sup(x, y, a, b, n) { const px = abs(x) / a + 1e-9, py = abs(y) / b + 1e-9, f = (px ** n + py ** n) ** (1 / n);
  const k = f ** (1 - n), gx = k * px ** (n - 1) / a, gy = k * py ** (n - 1) / b; return (f - 1) / hypot(gx, gy); }
const slab = (z, z0, z1) => max(z0 - z, z - z1);
// arc slots of radius R and width w, broken by n bridges of width bw
function arcs(x, y, R, w, n, bw, a0) {
  const r = hypot(x, y), d = abs(r - R) - w / 2; let db = 1e9;
  for (let k = 0; k < n; k++) { const a = a0 + 2 * PI * k / n, ux = cos(a), uy = sin(a);
    if (x * ux + y * uy > 0) db = min(db, abs(-x * uy + y * ux)); }
  return max(d, bw / 2 - db); }

// smooth pebble: superellipse-ish plan outline with low harmonics, rounder top / flatter bottom profile.
// The implicit F is turned into a distance by dividing by its (numerical) gradient.
let PB = { cx: 0, a: 45, b: 31, zc: 7, tTop: 17, tBot: 13.5, p: 2.4, qTop: 2.1, qBot: 1.9, bend: .07, zb: -5.8, flatR: 3 };
function pebbleF(x, y, z) {
  const u = x - PB.cx, s = u / PB.a, yb = y + PB.bend * PB.b * (s * s - .4);            // bean: fingers wrap the concave side (-y)
  const th = atan2(yb / PB.b, s);
  const wob = 1 + .035 * cos(2 * th + 1.1) + .025 * cos(3 * th - .5) - .03 * cos(th) + .01 * sin(5 * th + .3);
  const rho = hypot(s, yb / PB.b) / wob;
  const dz = z - PB.zc + .6 * s;                                                          // crest a little toward the button end
  const T = dz > 0 ? PB.tTop * (1 - .06 * s) : PB.tBot, q = dz > 0 ? PB.qTop : PB.qBot;
  return (rho ** PB.p + abs(dz / T) ** q) ** (1 / PB.p) - 1; }
function pebble(x, y, z) {
  const f = pebbleF(x, y, z), e = .05;
  const gx = (pebbleF(x + e, y, z) - pebbleF(x - e, y, z)) / (2 * e), gy = (pebbleF(x, y + e, z) - pebbleF(x, y - e, z)) / (2 * e), gz = (pebbleF(x, y, z + e) - pebbleF(x, y, z - e)) / (2 * e);
  return f / max(hypot(gx, gy, gz), 1e-4); }
// a crescent of n holes on radius R facing +x, largest in the middle, spanning +-span rad
function crescent(u, v, R, r, n, span) { let d = 1e9;
  for (let k = 0; k < n; k++) { const t = n > 1 ? k / (n - 1) * 2 - 1 : 0, a = t * span, rr = r * (.62 + .38 * cos(t * PI / 2));
    d = min(d, hypot(u - R * cos(a), v - R * sin(a)) - rr); } return d; }
// round through-holes on a hex grid (spacing s, radius r) inside radius R
function dots(u, v, s, r, R) { const h = s * sqrt(3) / 2; let d = 1e9;
  const j0 = Math.round(v / h); for (let j = j0 - 1; j <= j0 + 1; j++) { const off = (j & 1) ? s / 2 : 0, i0 = Math.round((u - off) / s);
    for (let i = i0 - 1; i <= i0 + 1; i++) { const px = i * s + off, py = j * h; if (hypot(px, py) > R) continue; d = min(d, hypot(u - px, v - py) - r); } }
  return d; }

// electronics cavity (+ USB-C slot at the TailBat end)
function cav(x, y, z) {
  const a = box(x, y, z, AX, 0, TOP / 2, AH, AH, TOP / 2, 1.5);
  const b = box(x, y, z, (BX0 + BX1) / 2, 0, BH / 2, (BX1 - BX0) / 2, BW, BH / 2, 1.5);
  const u = box(x, y, z, BX1 + 4, 0, HW.usbZ, 6, 5.5, 3.6, 1.5);
  return min(a, b, u); }
const cavCore = (x, y, z) => min(box(x, y, z, AX, 0, TOP / 2, AH, AH, TOP / 2, 1.5), box(x, y, z, (BX0 + BX1) / 2, 0, BH / 2, (BX1 - BX0) / 2, BW, BH / 2, 1.5));

// ============================================================ the three designs
// Each design gives: outer(x,y,z) body, lidDeco(x,y,z,d) surface detail on the lid, capTop(x,y,z) the cap's top,
// capSlots(x,y) sound/light slots through the cap (local coords around the button axis), hole: lanyard hole.
const ZB = -2.4;                                          // flat bottom (2.4 mm floor)
const DESIGNS = {
  // A · 河卵石: a palm stone. Bean-shaped plan (fingers curl round the concave side), crest under the palm, convex
  // underside that only sits on a small flat, a holed-stone lanyard hole at the round end. Button: flush, glows through.
  A: {
    name: '河卵石 Pebble', color: [.80, .79, .76], cap: [.86, .85, .82], zs: 7, hollow: true,
    outer(x, y, z) { return smax(pebble(x, y, z), PB.zb - z, PB.flatR); },
    hole: { x: -38.5, y: 0, r: 2.3, round: 1.6 },
    capTop(x, y, z, d) {                                   // flush with the stone, a soft thumb dish
      const dish = 70 - hypot(x - AX + 1, y, z - (this._top + 70 - .9));
      return smax(max(d, dish), hypot(x - AX, y) - CAP_R, .9); },
    capSlots: (u, v) => crescent(u, v, 9.2, .62, 7, .9),  // one arc of fine holes on the far side from the thumb
  },
  // B · 竹节: a section of bamboo (竹报平安, "bamboo brings word of safety"), nodes as ridges, flat underside.
  B: {
    name: '竹节 Bamboo', color: [.60, .68, .48], cap: [.78, .82, .66],
    outer(x, y, z) {
      const zc = 8.65; let R = 18.6;
      for (const n of [-31.5, 3]) { const u = x - n; R += 1.3 * exp(-(u * u) / (2 * .75 ** 2)) + .5 * exp(-((u - 2.2) ** 2) / (2 * 1.6 ** 2)) - .45 * exp(-((u + 1.9) ** 2) / (2 * .8 ** 2)); }
      R += .35 * sin((x + 38) / 72 * PI);                // segments swell slightly between nodes
      const r = hypot(y, z - zc) - R;
      const e = max(-38 - x, x - 34.5);                    // cut ends, rounded
      const qr = r + 2.5, qe = e + 2.5, d = hypot(max(qr, 0), max(qe, 0)) + min(max(qr, qe), 0) - 2.5;
      return smax(d, ZB - z, 2); },
    hole: { x: -35, y: 0, r: 2.4 },
    capTop(x, y, z, d) { return smax(d - .7, hypot(x - AX, y) - CAP_R, 1.4); },   // proud of the stalk by .7
    capSlots(u, v) {                                       // slots that follow the fibres
      let g = 1e9; for (const k of [-7.5, -4.5, -1.5, 1.5, 4.5, 7.5]) g = min(g, abs(v - k) - .6);
      return max(g, hypot(u, v) - 10.2, 4.2 - hypot(u, v)); },
  },
  // C · 平安牌: a flat jade-tag pendant worn on a cord, framed border, raised round button like a 平安扣.
  C: {
    name: '平安牌 Tag', color: [.80, .87, .82], cap: [.90, .94, .90],
    outer(x, y, z) {
      const cx = -3.5, a = 38.5, b = 21, n = 3.4, rr = 5.5;
      const px = abs(x - cx) / a, py = abs(y) / b, d2 = sup(x - cx, y, a, b, n);
      const zTop = 20.9 + 1.1 * (1 - min(1, px * px + py * py));   // gently domed face
      const zm = (ZB + zTop) / 2, hz = (zTop - ZB) / 2;
      const qx = d2 + rr, qz = abs(z - zm) - hz + rr;
      return smax(hypot(max(qx, 0), max(qz, 0)) + min(max(qx, qz), 0) - rr, ZB - z, .8); },
    hole: { x: -34.3, y: 0, r: 2.7 },
    lidDeco(x, y, z, d) {                                  // engraved frame 3.2 mm inside the edge
      return max(abs(sup(x + 3.5, y, 38.5 - 3.6, 21 - 3.6, 3.4)) - .45, -d - .5, 17 - z); },
    capTop(x, y, z, d) {                                   // raised 1.6 mm disc with a soft ring like a 平安扣
      const r = hypot(x - AX, y);
      const ring = .45 * exp(-((r - 8.2) ** 2) / (2 * 1.1 ** 2));
      return smax(d - 1.6 - ring, r - CAP_R, 1.6); },
    capSlots: (u, v) => min(arcs(u, v, 4.6, 1.2, 3, 1.6, PI / 2), arcs(u, v, 11.3, 1.1, 4, 1.8, PI / 4)),
  },
};

// ============================================================ parts
function parts(D) {
  const outer = (x, y, z) => { let d = D.outer(x, y, z);
    if (D.hole) d = smax(d, -(cylZ(x, y, D.hole.x, D.hole.y, D.hole.r)), D.hole.round || .8); return d; };
  // top height of the body over the button axis (for the dish)
  let t = 40; while (D.outer(AX, 0, t) > 0 && t > 0) t -= .05; D._top = t;
  if (D.hollow) { let lo = 99; for (let a = 0; a < 2 * PI; a += .2) for (const r of [0, 4, 8, CAP_R - 1.5]) { let z = 40;
      const x = AX + r * cos(a), y = r * sin(a); while (D.capTop.call(D, x, y, z, D.outer(x, y, z)) > 0 && z > 0) z -= .05; lo = min(lo, z); }
    D._ceil = lo - 1.2; }
  const tongue = (x, y, z) => max(max(-cavCore(x, y, z), cavCore(x, y, z) - 1.1), slab(z, ZS - .01, ZS + 2), outer(x, y, z) + 1.5);
  const rabbet = (x, y, z) => max(cavCore(x, y, z) - 1.1 - PRINT.tol / 2 - .05, z - (ZS + 2 + .2), outer(x, y, z) + 1.5 - PRINT.tol / 2 - .05);
  const base = (x, y, z) => max(min(smax(outer(x, y, z), z - ZS, .7), tongue(x, y, z)), -cav(x, y, z));   // .7 mm round-over hides the seam
  const lid = (x, y, z) => { const d = outer(x, y, z); let v = max(smax(d, ZS - z, .7), -cav(x, y, z), -rabbet(x, y, z));
    v = max(v, -max(cylZ(x, y, AX, 0, PK_R), slab(z, PK_Z0, PK_Z1)));            // flange pocket
    v = smax(v, -max(cylZ(x, y, AX, 0, HOLE_R), PK_Z0 - z), D.hollow ? .5 : 0.001);   // button hole (soft lip)
    if (D.lidDeco) v = max(v, -D.lidDeco(x, y, z, d));
    return v; };
  const cap = (x, y, z) => { const d = outer(x, y, z);
    let v = max(cylZ(x, y, AX, 0, CAP_R), z > FL_Z1 ? D.capTop(x, y, z, d) : -1, FL_Z0 - z);
    v = min(v, max(cylZ(x, y, AX, 0, FL_R), slab(z, FL_Z0, FL_Z1)));
    v = max(v, -D.capSlots(x - AX, y));
    if (D.hollow) v = max(v, -max(cylZ(x, y, AX, 0, CAP_R - 1.5), z - D._ceil));   // hollow: ~1.2 mm skin lets the LED glow through
    return v; };
  return { outer, base, lid, cap };
}

// ============================================================ surface nets mesher
function mesh(f, b, h) {                                    // b = [x0,y0,z0,x1,y1,z1]
  // "manifold" surface nets: one vertex per connected surface patch inside a cell, face saddles resolved by the
  // face-centre value, so neighbouring cells always agree and every edge ends up shared by exactly two triangles.
  const nx = Math.ceil((b[3] - b[0]) / h) + 3, ny = Math.ceil((b[4] - b[1]) / h) + 3, nz = Math.ceil((b[5] - b[2]) / h) + 3;
  const ox = b[0] - h, oy = b[1] - h, oz = b[2] - h, sxy = nx * ny;
  const V = new Float32Array(nx * ny * nz);
  for (let k = 0; k < nz; k++) { const z = oz + k * h;
    for (let j = 0; j < ny; j++) { const y = oy + j * h, o = k * sxy + j * nx;
      for (let i = 0; i < nx; i++) V[o + i] = (i && j && k && i < nx - 1 && j < ny - 1 && k < nz - 1) ? f(ox + i * h, y, z) : 1; } }
  const co = [[0,0,0],[1,0,0],[0,1,0],[1,1,0],[0,0,1],[1,0,1],[0,1,1],[1,1,1]];
  const E = [[0,1],[2,3],[4,5],[6,7],[0,2],[1,3],[4,6],[5,7],[0,4],[1,5],[2,6],[3,7]];
  const eid = {}; E.forEach(([a, c], n) => { eid[a * 8 + c] = n; eid[c * 8 + a] = n; });
  const FACES = [[0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5]].map(q => ({ q, e: q.map((c, m) => eid[c * 8 + q[(m + 1) % 4]]) }));
  const C = new Int32Array(sxy * nz).fill(-1); let EV = new Int32Array(1 << 16), ns = 0;   // per surface cell: vertex id of each of its 12 edges
  const P = [], g = new Float32Array(8), par = new Int8Array(12), acc = new Float64Array(48), cnt = new Int32Array(12), vid = new Int32Array(12);
  const find = a => { while (par[a] !== a) a = par[a] = par[par[a]]; return a; };
  const e = h * .1;
  for (let k = 0; k < nz - 1; k++) for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) {
    const o = k * sxy + j * nx + i; let m = 0;
    for (let c = 0; c < 8; c++) { g[c] = V[o + co[c][0] + co[c][1] * nx + co[c][2] * sxy]; if (g[c] < 0) m |= 1 << c; }
    if (m === 0 || m === 255) continue;
    for (let n = 0; n < 12; n++) { par[n] = n; cnt[n] = 0; vid[n] = -1; }
    const X = n => (g[E[n][0]] < 0) !== (g[E[n][1]] < 0);
    for (const F of FACES) {
      const xs = F.e.filter(X);
      if (xs.length === 2) { par[find(xs[0])] = find(xs[1]); }
      else if (xs.length === 4) {
        const cen = (g[F.q[0]] + g[F.q[1]] + g[F.q[2]] + g[F.q[3]]) / 4, inside = cen < 0;
        for (let mm = 0; mm < 4; mm++) { const cIn = g[F.q[mm]] < 0; if (cIn === inside) continue;  // corners on the other side of the centre are cut off
          par[find(F.e[(mm + 3) % 4])] = find(F.e[mm]); } } }
    if (ns + 1 > EV.length / 12) { const t = new Int32Array(EV.length * 2); t.set(EV); EV = t; }
    const slot = ns++; C[o] = slot;
    for (let n = 0; n < 48; n++) acc[n] = 0;
    for (let n = 0; n < 12; n++) { EV[slot * 12 + n] = -1; if (!X(n)) continue; const r = find(n), [a, c] = E[n], t = g[a] / (g[a] - g[c]);
      acc[r * 4] += co[a][0] + t * (co[c][0] - co[a][0]); acc[r * 4 + 1] += co[a][1] + t * (co[c][1] - co[a][1]); acc[r * 4 + 2] += co[a][2] + t * (co[c][2] - co[a][2]); cnt[r]++; }
    for (let n = 0; n < 12; n++) { if (!X(n)) continue; const r = find(n);
      if (vid[r] < 0) {
        let x = ox + (i + acc[r * 4] / cnt[r]) * h, y = oy + (j + acc[r * 4 + 1] / cnt[r]) * h, z = oz + (k + acc[r * 4 + 2] / cnt[r]) * h;
        for (let it = 0; it < 2; it++) {
        const d = f(x, y, z), gx = (f(x + e, y, z) - f(x - e, y, z)) / (2 * e), gy = (f(x, y + e, z) - f(x, y - e, z)) / (2 * e), gz = (f(x, y, z + e) - f(x, y, z - e)) / (2 * e), gg = gx * gx + gy * gy + gz * gz;
        if (gg > 1e-6) { const lim = h * .5 / sqrt(gg), s2 = clamp(d / gg, -lim, lim), x0 = ox + i * h, y0 = oy + j * h, z0 = oz + k * h;
          x = clamp(x - gx * s2, x0, x0 + h); y = clamp(y - gy * s2, y0, y0 + h); z = clamp(z - gz * s2, z0, z0 + h); } }
        vid[r] = P.length / 3; P.push(x, y, z); }
      EV[slot * 12 + n] = vid[r]; }
  }
  const T = [];
  const at = (cell, n) => { const s2 = C[cell]; return s2 < 0 ? -1 : EV[s2 * 12 + n]; };
  const quad = (a, b2, c, d, flip) => { if (a < 0 || b2 < 0 || c < 0 || d < 0) return;
    if (flip) T.push(a, c, b2, a, d, c); else T.push(a, b2, c, a, c, d); };
  for (let k = 1; k < nz - 1; k++) for (let j = 1; j < ny - 1; j++) for (let i = 1; i < nx - 1; i++) {
    const o = k * sxy + j * nx + i, v0 = V[o] < 0;
    if (v0 !== (V[o + 1] < 0)) quad(at(o - nx - sxy, 3), at(o - sxy, 2), at(o, 0), at(o - nx, 1), !v0);           // x edge
    if (v0 !== (V[o + nx] < 0)) quad(at(o - 1 - sxy, 7), at(o - 1, 5), at(o, 4), at(o - sxy, 6), !v0);            // y edge
    if (v0 !== (V[o + sxy] < 0)) quad(at(o - 1 - nx, 11), at(o - nx, 10), at(o, 8), at(o - 1, 9), !v0);           // z edge
  }
  const p = new Float32Array(P), t = new Uint32Array(T);
  let vol = 0; for (let q = 0; q < t.length; q += 3) { const a = t[q] * 3, b2 = t[q + 1] * 3, c = t[q + 2] * 3;
    vol += p[a] * (p[b2 + 1] * p[c + 2] - p[b2 + 2] * p[c + 1]) - p[a + 1] * (p[b2] * p[c + 2] - p[b2 + 2] * p[c]) + p[a + 2] * (p[b2] * p[c + 1] - p[b2 + 1] * p[c]); }
  if (vol < 0) for (let q = 0; q < t.length; q += 3) { const s2 = t[q + 1]; t[q + 1] = t[q + 2]; t[q + 2] = s2; }
  return { p, t, vol: abs(vol) / 6 };
}
function bounds(m) { const b = [1e9, 1e9, 1e9, -1e9, -1e9, -1e9];
  for (let i = 0; i < m.p.length; i += 3) for (let a = 0; a < 3; a++) { b[a] = min(b[a], m.p[i + a]); b[a + 3] = max(b[a + 3], m.p[i + a]); } return b; }
function moved(m, dx, dy, dz) { const p = new Float32Array(m.p); for (let i = 0; i < p.length; i += 3) { p[i] += dx; p[i + 1] += dy; p[i + 2] += dz; } return { p, t: m.t }; }
// manifold check: every edge used exactly twice, once each way
function edgeCheck(m) { const E = new Map(); let bad = 0; const t = m.t;
  for (let q = 0; q < t.length; q += 3) for (let e = 0; e < 3; e++) { const a = t[q + e], b = t[q + (e + 1) % 3], k = a < b ? a * 4294967296 + b : b * 4294967296 + a;
    E.set(k, (E.get(k) || 0) + (a < b ? 1 : 1000)); }
  for (const v of E.values()) if (v !== 1001) bad++; return bad; }

// ============================================================ 3MF writer (zip, deflate)
function zip(files) {
  const chunks = [], cd = []; let off = 0;
  for (const [name, data] of files) {
    const nm = Buffer.from(name), raw = Buffer.isBuffer(data) ? data : Buffer.from(data), def = zlib.deflateRawSync(raw, { level: 9 }), crc = zlib.crc32(raw);
    const lh = Buffer.alloc(30); lh.writeUInt32LE(0x04034b50, 0); lh.writeUInt16LE(20, 4); lh.writeUInt16LE(0x0800, 6); lh.writeUInt16LE(8, 8);
    lh.writeUInt32LE(0, 10); lh.writeUInt32LE(crc >>> 0, 14); lh.writeUInt32LE(def.length, 18); lh.writeUInt32LE(raw.length, 22); lh.writeUInt16LE(nm.length, 26); lh.writeUInt16LE(0, 28);
    chunks.push(lh, nm, def);
    const ch = Buffer.alloc(46); ch.writeUInt32LE(0x02014b50, 0); ch.writeUInt16LE(20, 4); ch.writeUInt16LE(20, 6); ch.writeUInt16LE(0x0800, 8); ch.writeUInt16LE(8, 10);
    ch.writeUInt32LE(0, 12); ch.writeUInt32LE(crc >>> 0, 16); ch.writeUInt32LE(def.length, 20); ch.writeUInt32LE(raw.length, 24); ch.writeUInt16LE(nm.length, 28);
    ch.writeUInt32LE(off, 42); cd.push(ch, nm); off += 30 + nm.length + def.length;
  }
  const cdb = Buffer.concat(cd), end = Buffer.alloc(22); end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(files.length, 8); end.writeUInt16LE(files.length, 10);
  end.writeUInt32LE(cdb.length, 12); end.writeUInt32LE(off, 16); return Buffer.concat([...chunks, cdb, end]);
}
function write3mf(file, objs) {                              // objs: [{name, m}] already placed on the plate
  let x = '<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n<metadata name="Title">观察器外壳</metadata>\n<resources>\n';
  const parts = [x];
  objs.forEach((o, n) => { const s = [`<object id="${n + 1}" name="${o.name}" type="model"><mesh><vertices>`];
    const p = o.m.p; for (let i = 0; i < p.length; i += 3) s.push(`<vertex x="${p[i].toFixed(3)}" y="${p[i + 1].toFixed(3)}" z="${p[i + 2].toFixed(3)}"/>`);
    s.push('</vertices><triangles>'); const t = o.m.t; for (let i = 0; i < t.length; i += 3) s.push(`<triangle v1="${t[i]}" v2="${t[i + 1]}" v3="${t[i + 2]}"/>`);
    s.push('</triangles></mesh></object>\n'); parts.push(s.join('')); });
  parts.push('</resources>\n<build>\n' + objs.map((o, n) => `<item objectid="${n + 1}"/>`).join('\n') + '\n</build>\n</model>\n');
  fs.writeFileSync(file, zip([
    ['[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'],
    ['_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'],
    ['3D/3dmodel.model', parts.join('')]]));
}
// light mesh for the web preview: int16 positions (0.01 mm) + uint32 indices
// layout: [nv, nt] uint32 | positions int16 x3 | normals int8 x3 (from the SDF gradient, so shading is smooth) | pad | indices uint32 x3
function writeBin(file, m, f) {
  const nv = m.p.length / 3, head = new Uint32Array([nv, m.t.length / 3]), q = new Int16Array(m.p.length), n = new Int8Array(m.p.length), e = .03;
  for (let i = 0; i < m.p.length; i++) q[i] = Math.round(m.p[i] * 100);
  for (let i = 0; i < m.p.length; i += 3) { const x = m.p[i], y = m.p[i + 1], z = m.p[i + 2];
    const gx = f(x + e, y, z) - f(x - e, y, z), gy = f(x, y + e, z) - f(x, y - e, z), gz = f(x, y, z + e) - f(x, y, z - e), l = hypot(gx, gy, gz) || 1;
    n[i] = Math.round(gx / l * 127); n[i + 1] = Math.round(gy / l * 127); n[i + 2] = Math.round(gz / l * 127); }
  const used = q.byteLength + n.byteLength;
  fs.writeFileSync(file, Buffer.concat([Buffer.from(head.buffer), Buffer.from(q.buffer), Buffer.from(n.buffer), Buffer.alloc((4 - (used % 4)) % 4), Buffer.from(m.t.buffer)]));
}

// ============================================================ checks: wall thickness around the electronics
function wallReport(D, P) {
  // sample the real (rounded) cavity surface and measure how much body is left outside it
  const r = { side: 1e9, end: 1e9, top: 1e9, bot: 1e9, pocketCover: 1e9, seamSkin: 1e9 }, st = .35;
  const usb = (x, y, z) => x > BX1 - 1.5 && abs(y) < 7 && abs(z - HW.usbZ) < 5;
  for (let x = X0 - 1; x <= BX1 + 1; x += st) for (let y = -AH - 1; y <= AH + 1; y += st) for (let z = -1; z <= TOP + 1; z += st) {
    const c = cavCore(x, y, z); if (abs(c) > .18 || usb(x, y, z)) continue;
    if (hypot(x - AX, y) < PK_R + .3 && z > HW.atomH - .5) continue;          // under the button: covered by the cap
    const w = -P.outer(x, y, z), k = z < .4 ? 'bot' : z > BH - .4 && (x > X0 + HW.atom || z > TOP - .4) ? 'top' : abs(y) > AH - 1.6 ? 'side' : 'end';
    if (w < r[k]) { r[k] = w; (r.at = r.at || {})[k] = [x, y, z].map(v => +v.toFixed(1)); } }
  for (let a = 0; a < 2 * PI; a += .05) for (let q = 0; q <= PK_R; q += .5) r.pocketCover = min(r.pocketCover, -P.outer(AX + q * cos(a), q * sin(a), PK_Z1));
  for (let x = X0 - 3; x <= BX1 + 3; x += st) for (let y = -AH - 4; y <= AH + 4; y += st) {
    const c = cavCore(x, y, ZS + .5); if (c > 1.1 && c < 1.5 && !usb(x, y, ZS)) { const w = -P.outer(x, y, ZS + .5) - 1.35; if (w < r.seamSkin) { r.seamSkin = w; (r.at = r.at || {}).seam = [x, y].map(v => +v.toFixed(1)); } } }
  return r;
}

if (process.env.LIB) { module.exports = { setZS: v => { ZS = v; }, DESIGNS, parts, mesh, AX, ZS, FL_Z0, FL_Z1, FL_R, ZB, wallReport, setPB: o => Object.assign(PB, o) }; return; }
// ============================================================ run
const OUT = path.join(__dirname, 'out'), VIEW = path.join(OUT, 'view');
fs.mkdirSync(VIEW, { recursive: true });
const want = process.argv.slice(2).filter(a => DESIGNS[a]); const ids = want.length ? want : Object.keys(DESIGNS);
const H = +(process.env.H || .32), HV = +(process.env.HV || .6), CHECK_ONLY = !!process.env.CHECK;
const summary = {};
for (const id of ids) {
  const D = DESIGNS[id]; ZS = D.zs || 9; const P = parts(D), t0 = Date.now();
  const w = wallReport(D, P); const at = w.at; delete w.at; console.log(id, D.name, 'walls mm', JSON.stringify(Object.fromEntries(Object.entries(w).map(([k, v]) => [k, +v.toFixed(2)]))), 'at', JSON.stringify(at));
  if (CHECK_ONLY) continue;
  const BB = [-52, -38, -9, 52, 38, 34];
  const out = {}, info = {};
  for (const [k, f, bb] of [['base', P.base, [BB[0], BB[1], BB[2], BB[3], BB[4], ZS + 2.5]], ['lid', P.lid, [BB[0], BB[1], ZS - .5, BB[3], BB[4], BB[5]]],
                            ['cap', P.cap, [AX - FL_R - 1, -FL_R - 1, FL_Z0 - .5, AX + FL_R + 1, FL_R + 1, BB[5]]]]) {
    const m = mesh(f, bb, k === 'cap' ? H * .7 : H), b = bounds(m), bad = edgeCheck(m);
    out[k] = m; info[k] = { tris: m.t.length / 3, size: [b[3] - b[0], b[4] - b[1], b[5] - b[2]].map(v => +v.toFixed(1)), vol_cm3: +(m.vol / 1000).toFixed(1), badEdges: bad };
    const mv = mesh(f, bb, k === 'cap' ? HV * .6 : HV); writeBin(path.join(VIEW, `${id}_${k}.bin`), mv, f);
  }
  // plate layout (fits a 180 x 180 A1 mini plate): base front, lid behind, cap at the side, each sitting on z = 0
  const place = (m, cx, cy) => { const b = bounds(m); return moved(m, cx - (b[0] + b[3]) / 2, cy - (b[1] + b[4]) / 2, -b[2]); };
  write3mf(path.join(OUT, `${id}.3mf`), [
    { name: `${id} base 底座`, m: place(out.base, 80, 40) }, { name: `${id} lid 上盖`, m: place(out.lid, 80, 113) }, { name: `${id} button 按键`, m: place(out.cap, 156, 76) }]);
  summary[id] = { name: D.name, ...info, ms: Date.now() - t0 };
  console.log(id, JSON.stringify(info), (Date.now() - t0) + 'ms');
}
if (!CHECK_ONLY) {
  const meta = { hw: HW, ax: AX, zs: ZS, fl: [FL_Z0, FL_Z1], designs: Object.fromEntries(Object.keys(DESIGNS).map(i => [i, { name: DESIGNS[i].name, color: DESIGNS[i].color, cap: DESIGNS[i].cap }])) };
  fs.writeFileSync(path.join(VIEW, 'meta.json'), JSON.stringify(meta));
}
