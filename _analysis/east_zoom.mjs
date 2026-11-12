import fs from 'fs';
import { encodePNG } from './png.mjs';
const M = JSON.parse(fs.readFileSync('mosaic.json')), Gr = JSON.parse(fs.readFileSync('georef.json')), rgb = fs.readFileSync('mosaic.rgb');
const X0 = Math.round((115.6785 + 330 / Gr.KX - Gr.lonO) * Gr.KX / Gr.mpp);
const [name, ax, ay, bx, by] = process.argv.slice(2); const x0 = X0 + 2 * +ax, y0 = 2 * +ay, w = 2 * (+bx - +ax), h = 2 * (+by - +ay);
const o = new Uint8Array(w * h * 3);
for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const k = ((y0 + y) * M.MW + x0 + x) * 3; for (let c = 0; c < 3; c++) o[(y * w + x) * 3 + c] = rgb[k + c] || 0; }
for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const gx = (x0 + x) % 50 === 0, gy = (y0 + y) % 50 === 0; if (gx || gy) { const big = ((x0 + x) % 250 === 0 && gx) || ((y0 + y) % 250 === 0 && gy); const i = (y * w + x) * 3; o[i] = big ? 255 : 0; o[i + 1] = big ? 255 : 255; o[i + 2] = big ? 0 : 255; } }
encodePNG('ez_' + name + '.png', w, h, o); console.log(name, 'mosaic origin', x0, y0, 'size', w, h, 'X0', X0);
