import fs from 'fs';
import { encodePNG } from './png.mjs';
const dir = new URL('../', import.meta.url).pathname;
const { MW, MH } = JSON.parse(fs.readFileSync(dir + '_analysis/mosaic.json')), R = fs.readFileSync(dir + '_analysis/mosaic.rgb');
// per-pixel class: 0 none, 1 light/flat roof, 2 blue steel, 3 red/orange tile, 4 dark villa roof, 5 salmon villa roof, 6 vegetation, 7 shadow
export function cls(r, g, b) {
  const L = (r + g + b) / 3, mx = Math.max(r, g, b), mn = Math.min(r, g, b), S = mx - mn;
  if (r + g + b === 0) return 0;
  if (b > r + 28 && b > g + 8 && b > 110) return 2;
  if (r > g + 40 && r > b + 50 && r > 140) return 3;
  if (r > 150 && r > g + 18 && g > b + 4 && r - b > 35 && L > 130) return 5;
  if (g > r + 6 && g >= b && S > 14) return 6;
  if (L < 62) return 7;
  if (L > 158 && S < 34) return 1;
  if (L > 72 && L < 112 && S < 18) return 4;
  return 0;
}
const COL = [[0, 0, 0], [255, 255, 255], [40, 90, 255], [255, 40, 30], [150, 0, 200], [255, 150, 60], [0, 120, 0], [20, 20, 20]];
if (process.argv[2] === 'crops') for (const [name, x0, y0, cw, ch] of [['village', 1100, 1300, 700, 520], ['villaDark', 1500, 1450, 500, 420], ['villaPink', 1100, 2700, 600, 440], ['north', 700, 400, 600, 440]]) {
  const o = new Uint8Array(cw * 2 * ch * 3);
  for (let y = 0; y < ch; y++) for (let x = 0; x < cw; x++) { const i = ((y0 + y) * MW + x0 + x) * 3, c = cls(R[i], R[i + 1], R[i + 2]);
    o.set([R[i], R[i + 1], R[i + 2]], (y * cw * 2 + x) * 3); o.set(COL[c], (y * cw * 2 + cw + x) * 3); }
  encodePNG(dir + `_analysis/crop_${name}.png`, cw * 2, ch, o);
}
