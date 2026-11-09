import fs from 'fs';
import zlib from 'zlib';
// Minimal PNG decode (8-bit, colour type 2/6, non-interlaced) and RGB encode.
export function decodePNG(path) {
  const b = fs.readFileSync(path); let p = 8, W = 0, H = 0, ct = 0; const idat = [];
  while (p < b.length) { const len = b.readUInt32BE(p), type = b.toString('ascii', p + 4, p + 8), d = b.subarray(p + 8, p + 8 + len);
    if (type === 'IHDR') { W = d.readUInt32BE(0); H = d.readUInt32BE(4); ct = d[9]; if (d[8] !== 8 || d[12]) throw new Error('unsupported png'); }
    else if (type === 'IDAT') idat.push(d); else if (type === 'IEND') break; p += 12 + len; }
  const bpp = ct === 6 ? 4 : ct === 2 ? 3 : (() => { throw new Error('ct ' + ct); })(), raw = zlib.inflateSync(Buffer.concat(idat)), stride = W * bpp;
  const out = Buffer.alloc(H * stride); let prev = Buffer.alloc(stride);
  for (let y = 0; y < H; y++) { const f = raw[y * (stride + 1)], row = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1)), cur = out.subarray(y * stride, (y + 1) * stride);
    for (let x = 0; x < stride; x++) { const a = x >= bpp ? cur[x - bpp] : 0, up = prev[x], c = x >= bpp ? prev[x - bpp] : 0; let v = row[x];
      if (f === 1) v += a; else if (f === 2) v += up; else if (f === 3) v += (a + up) >> 1; else if (f === 4) { const pp = a + up - c, pa = Math.abs(pp - a), pb = Math.abs(pp - up), pc = Math.abs(pp - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? up : c; }
      cur[x] = v & 255; }
    prev = cur; }
  const rgb = new Uint8Array(W * H * 3); for (let i = 0; i < W * H; i++) { rgb[i * 3] = out[i * bpp]; rgb[i * 3 + 1] = out[i * bpp + 1]; rgb[i * 3 + 2] = out[i * bpp + 2]; }
  return { W, H, rgb };
}
export function encodePNG(path, W, H, rgb) {
  const raw = Buffer.alloc(H * (W * 3 + 1)); for (let y = 0; y < H; y++) { raw[y * (W * 3 + 1)] = 0; Buffer.from(rgb.buffer, rgb.byteOffset + y * W * 3, W * 3).copy(raw, y * (W * 3 + 1) + 1); }
  const crcT = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; crcT[n] = c >>> 0; }
  const crc = buf => { let c = 0xffffffff; for (const v of buf) c = crcT[(c ^ v) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
  const chunk = (t, d) => { const len = Buffer.alloc(4); len.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([len, td, c]); };
  const ih = Buffer.alloc(13); ih.writeUInt32BE(W, 0); ih.writeUInt32BE(H, 4); ih[8] = 8; ih[9] = 2;
  fs.writeFileSync(path, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ih), chunk('IDAT', zlib.deflateSync(raw, { level: 6 })), chunk('IEND', Buffer.alloc(0))]));
}
export const SHOTS = ['截屏2026-11-09 下午4.28.34.png', '截屏2026-11-09 下午4.28.44.png', '截屏2026-11-09 下午4.28.58.png', '截屏2026-11-09 下午4.29.11.png', '截屏2026-11-09 下午4.29.19.png', '截屏2026-11-09 下午4.30.01.png', '截屏2026-11-09 下午4.30.11.png'];
// UI overlays to ignore (info banner, search box, zoom buttons, logo, scale bar, info button)
export function uiMask(x, y, W, H) {
  return y < 90 || (x > W - 430 && y < 100) || (x < 100 && y > 990) || (x < 200 && y > H - 70) || (x > W - 480 && y > H - 80) || x < 6 || y > H - 6 || x > W - 6;
}
