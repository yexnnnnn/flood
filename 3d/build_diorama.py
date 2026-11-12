#!/usr/bin/env python3
"""3D diorama of 沈家庵村 -> 3d/real.html (写实) and 3d/model.html (模型).

A clean, interaction-only model meant to be embedded (Figma Sites embed / iframe / WKWebView): drag to rotate,
pinch or scroll to zoom, two fingers or right-drag to pan. No UI, no warning logic. One self-contained file each.

Terrain: the 2.4 km crop, the 2.5 m grid v2 painted from (map_styles.U), sampled to a 5 m mesh, with a little
ridge detail on steep ground. Ground texture and land-cover mask are baked by 3d/build_tex.py (3d/_tex/).
Houses: v2 REG footprints. River level: from the bed heights along the Juma centreline, monotone downstream.

usage: python3 3d/build_diorama.py
"""
import os, sys, json, math, base64, struct, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'v2'))
with contextlib.redirect_stdout(io.StringIO()):
    import map_styles as S
BW, M, U = S.BW, S.M, S.U
HALF = BW.HALF                     # 1200 m
STEP = 5
N = int(2 * HALF / STEP) + 1       # 481
UC = 2 * HALF / M

def crop(x, z):
    fx, fz = (x + HALF) / UC - .5, (z + HALF) / UC - .5
    i, j = max(0, min(M - 2, int(math.floor(fx)))), max(0, min(M - 2, int(math.floor(fz))))
    tx, tz = min(1, max(0, fx - i)), min(1, max(0, fz - j))
    a, b, c, d = U[j * M + i], U[j * M + i + 1], U[(j + 1) * M + i], U[(j + 1) * M + i + 1]
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz

def hsh(i, j):
    n = (i * 374761393 + j * 668265263) & 0xffffffff
    n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
    return ((n ^ (n >> 16)) & 0xffff) / 65535.0
def vnoise(x, z):
    i, j = math.floor(x), math.floor(z); fx, fz = x - i, z - j
    fx, fz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a, b, c, d = hsh(i, j), hsh(i + 1, j), hsh(i, j + 1), hsh(i + 1, j + 1)
    return (a * (1 - fx) + b * fx) * (1 - fz) + (c * (1 - fx) + d * fx) * fz
def ridged(x, z):
    s, a, f = 0.0, 1.0, 1 / 120
    for _ in range(4):
        n = 1 - abs(vnoise(x * f, z * f) * 2 - 1); s += a * n * n; a *= .5; f *= 2.1
    return s / 1.875 - .45
def sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

base = [crop(-HALF + i * STEP, -HALF + j * STEP) for j in range(N) for i in range(N)]
H = []
for j in range(N):
    for i in range(N):
        k = j * N + i
        hx = (base[k + 1] - base[k - 1]) / (2 * STEP) if 0 < i < N - 1 else 0
        hz = (base[k + N] - base[k - N]) / (2 * STEP) if 0 < j < N - 1 else 0
        H.append(base[k] + sstep(.2, .8, math.hypot(hx, hz)) * 3.5 * ridged(-HALF + i * STEP, -HALF + j * STEP))
HMIN, HMAX = min(H), max(H)
Q = struct.pack(f'<{len(H)}H', *[max(0, min(65535, round((h - HMIN) * 10))) for h in H])

# river surface: lowest ground within 30 m of each centreline point + 0.7 m, then monotone downstream
riv = [(float(x), float(z)) for x, z in BW.RIV]
lv = []
for x, z in riv:
    m = 1e9
    for dz in range(-30, 31, 5):
        for dx in range(-30, 31, 5):
            if abs(x + dx) < HALF and abs(z + dz) < HALF: m = min(m, crop(x + dx, z + dz))
    lv.append(m + .7 if m < 1e8 else None)
known = [v for v in lv if v is not None]
lv = [v if v is not None else (known[0] if k < len(lv) / 2 else known[-1]) for k, v in enumerate(lv)]
if lv[0] < lv[-1]: lv.reverse(); riv.reverse()
for k in range(1, len(lv)): lv[k] = min(lv[k], lv[k - 1])
rivlo = [[round(x, 1), round(z, 1), round(v, 2)] for (x, z), v in zip(riv, lv)]

V = 1000 / (2 * HALF)
houses = [[round(h['x'] / V - HALF, 2), round(h['y'] / V - HALF, 2), round(h['w'] / V, 2), round(h['d'] / V, 2), round(math.radians(h['a']), 4)] for h in S.REG]

DATA = dict(half=HALF, n=N, step=STEP, hmin=round(HMIN, 2), hmax=round(HMAX, 2), rivlo=rivlo, houses=houses)
b64 = lambda p: base64.b64encode(open(p, 'rb').read()).decode()
TEX = os.path.join(HERE, '_tex')
tpl = open(os.path.join(HERE, 'diorama.html'), encoding='utf-8').read()
for style, name, title in (('real', 'real.html', '沈家庵村 · 写实'), ('model', 'model.html', '沈家庵村 · 模型')):
    html = (tpl.replace('__STYLE__', style).replace('__TITLE__', title)
               .replace('__DATA__', json.dumps(DATA, separators=(',', ':')))
               .replace('__HEIGHTS__', base64.b64encode(Q).decode())
               .replace('__MASK__', 'data:image/jpeg;base64,' + b64(os.path.join(TEX, 'mask.jpg')))
               .replace('__GROUND__', 'data:image/jpeg;base64,' + b64(os.path.join(TEX, 'ground.jpg')) if style == 'real' else ''))
    out = os.path.join(HERE, name); open(out, 'w', encoding='utf-8').write(html)
    print('wrote', out, len(html) // 1024, 'KB')
print('mesh', N, 'x', N, '| h', round(HMIN), '..', round(HMAX), '| houses', len(houses), '| river', rivlo[0][2], '->', rivlo[-1][2])
