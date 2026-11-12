import fs from 'fs';
import { encodePNG } from './png.mjs';
const M = JSON.parse(fs.readFileSync('mosaic.json')), Gr = JSON.parse(fs.readFileSync('georef.json')), rgb = fs.readFileSync('mosaic.rgb');
const raw = JSON.parse(fs.readFileSync('houses_raw.json')), kept = JSON.parse(fs.readFileSync('../shenjia_an_houses.json')).houses;
// pixel of lon/lat in mosaic
const px = (lon, lat) => [(lon - Gr.lonO) * Gr.KX / Gr.mpp, (Gr.latO - lat) * Gr.KY / Gr.mpp];
// crop: mosaic pixels covering the east bank (x > ~350 m east of 115.6785)
const lonA = 115.6785 + 330 / Gr.KX, [X0] = px(lonA, 0), X1 = M.MW, Y0 = 0, Y1 = M.MH, S = 2;
const w = Math.floor((X1 - X0) / S), h = Math.floor((Y1 - Y0) / S), o = new Uint8Array(w * h * 3);
for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const sx = Math.floor(X0) + x * S, sy = y * S, k = (sy * M.MW + sx) * 3; o[(y * w + x) * 3] = rgb[k]; o[(y * w + x) * 3 + 1] = rgb[k + 1]; o[(y * w + x) * 3 + 2] = rgb[k + 2]; }
const dot = (X, Y, c, r) => { for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { if (Math.abs(dx) < r - 1 && Math.abs(dy) < r - 1) continue; const xx = Math.round((X - X0) / S + dx), yy = Math.round(Y / S + dy); if (xx >= 0 && yy >= 0 && xx < w && yy < h) o.set(c, (yy * w + xx) * 3); } };
let nr = 0; for (const r of raw) { const [X, Y] = px(r.lon, r.lat); if (X > X0) { dot(X, Y, [255, 0, 0], 5); nr++; } }
let nk = 0; for (const k of kept) { const lon = 115.678 + k.x / Gr.KX, lat = 39.596 - k.z / Gr.KY, [X, Y] = px(lon, lat); if (X > X0) { dot(X, Y, [0, 255, 0], 8); nk++; } }
encodePNG('east_check.png', w, h, o); console.log('crop', w, h, 'raw east', nr, 'kept east', nk);
