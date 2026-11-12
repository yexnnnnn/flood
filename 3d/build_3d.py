#!/usr/bin/env python3
"""3D map of 沈家庵村 -> 3d/index.html (one self-contained file: WebGL2, works in iOS Safari and in a WKWebView)

Terrain: inside the 2.4 km crop the 2.5 m upsampled grid the M7 base was painted from (v2/map_styles.U),
outside it the raw 1" DEM (output_hh.asc, about 4 x 4 km), Catmull-Rom resampled to a 10 m mesh, blended
over the last 120 m of the crop, plus slope-weighted ridge noise so 30 m DEM slopes do not look smooth.
Surface: the M7 写实 raster inside the crop, a procedural forest / rock / gravel-bar shader outside.
Houses (v2 REG footprints), trees (placed at runtime from M7 pixels), water, labels and the warning
logic (same SIG / RULES / LV as v2) are built in the page.

usage: python3 3d/build_3d.py
"""
import os, sys, json, math, base64, struct

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V2 = os.path.join(ROOT, 'v2')
sys.path.insert(0, V2)
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):          # importing design rebuilds web/index.html and prints about it
    import design as D
    import map_styles as S
BW = S.BW

# ---------------------------------------------------------------- mesh extent (metres, x east, z south of the crop centre)
X0, X1, Z0, Z1, STEP = -1950, 1850, -2050, 1850, 10
NX, NZ = (X1 - X0) // STEP + 1, (Z1 - Z0) // STEP + 1
HALF = BW.HALF
lon0, lat0 = D.BW.G['center'] if hasattr(D.BW, 'G') else json.load(open(os.path.join(ROOT, 'shenjia_data.json')))['center']
KX, KY = 85780.96, 110540.0

# ---------------------------------------------------------------- raw DEM
L = open(os.path.join(ROOT, 'output_hh.asc')).read().split('\n')
hd = {}
for l in L[:5]:
    k, v = l.split(); hd[k] = float(v)
nc, nr, cs, xll, yll = int(hd['ncols']), int(hd['nrows']), hd['cellsize'], hd['xllcorner'], hd['yllcorner']
A = [list(map(float, l.split())) for l in L[5:] if l.strip()]

def cr(p0, p1, p2, p3, t):
    return p1 + .5 * t * (p2 - p0 + t * (2 * p0 - 5 * p1 + 4 * p2 - p3 + t * (3 * (p1 - p2) + p3 - p0)))

def dem(x, z):
    lon, lat = lon0 + x / KX, lat0 - z / KY
    c, r = (lon - xll) / cs - .5, (yll + nr * cs - lat) / cs - .5
    ci, ri = math.floor(c), math.floor(r); tc, tr = c - ci, r - ri
    g = lambda rr, cc: A[min(nr - 1, max(0, rr))][min(nc - 1, max(0, cc))]
    rows = [cr(g(ri + k, ci - 1), g(ri + k, ci), g(ri + k, ci + 1), g(ri + k, ci + 2), tc) for k in (-1, 0, 1, 2)]
    return cr(*rows, tr)

M, U = S.M, S.U
UC = 2 * HALF / M
def crop(x, z):
    fx, fz = (x + HALF) / UC - .5, (z + HALF) / UC - .5
    i, j = max(0, min(M - 2, int(math.floor(fx)))), max(0, min(M - 2, int(math.floor(fz))))
    tx, tz = min(1, max(0, fx - i)), min(1, max(0, fz - j))
    a, b, c, d = U[j * M + i], U[j * M + i + 1], U[(j + 1) * M + i], U[(j + 1) * M + i + 1]
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz

def sstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

base = []
for j in range(NZ):
    z = Z0 + j * STEP
    for i in range(NX):
        x = X0 + i * STEP
        e = max(abs(x), abs(z)); w = sstep(HALF, HALF - 120, e)
        base.append(w * crop(x, z) + (1 - w) * dem(x, z) if w > 0 else dem(x, z))

# ---------------------------------------------------------------- ridge detail on steep ground
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
    s, a, f = 0.0, 1.0, 1 / 140
    for _ in range(4):
        n = 1 - abs(vnoise(x * f, z * f) * 2 - 1); s += a * n * n; a *= .5; f *= 2.1
    return s / 1.875 - .45

H = []
for j in range(NZ):
    for i in range(NX):
        k = j * NX + i
        hx = (base[k + 1] - base[k - 1]) / (2 * STEP) if 0 < i < NX - 1 else 0
        hz = (base[k + NX] - base[k - NX]) / (2 * STEP) if 0 < j < NZ - 1 else 0
        sl = math.hypot(hx, hz)
        x, z = X0 + i * STEP, Z0 + j * STEP
        inside = sstep(HALF, HALF - 120, max(abs(x), abs(z)))
        amp = sstep(.18, .75, sl) * 9 * (1 - .65 * inside)
        H.append(base[k] + amp * ridged(x, z))
HMIN = min(H)
Q = struct.pack(f'<{len(H)}H', *[max(0, min(65535, round((h - HMIN) * 10))) for h in H])

# ---------------------------------------------------------------- vectors
gj = json.load(open(os.path.join(ROOT, 'shenjia_an_4km_osm.geojson'), encoding='utf-8'))
mxz = lambda c: (round((c[0] - lon0) * KX, 1), round(-(c[1] - lat0) * KY, 1))
rivers, places = [], []
for f in gj['features']:
    p, g = f['properties'], f['geometry']
    if p.get('waterway') == 'river' and p.get('name') == '拒马河':
        segs = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        for sgm in segs: rivers.append([mxz(c) for c in sgm])
    if ('place' in p or p.get('natural') == 'peak') and g['type'] == 'Point' and p.get('name'):
        x, z = mxz(g['coordinates'])
        places.append(dict(n=p['name'], t=p.get('place') or p.get('natural'), x=x, z=z))
riv_lo = [[round(x, 1), round(z, 1), round(v, 2)] for (x, z), v in zip(BW.RIV, BW.lo)]

V = 1000 / (2 * HALF)
houses = []
for k, h in enumerate(S.REG):
    houses.append([round(h['x'] / V - HALF, 2), round(h['y'] / V - HALF, 2), round(h['w'] / V, 2), round(h['d'] / V, 2),
                   round(math.radians(h['a']), 4)])

sig = []
for k, v in D.SIG.items():
    if v.get('x') is None or v.get('type') not in ('pt', 'reach'): pin = None
    else: pin = [round(v['x'] / V - HALF, 1), round(v['y'] / V - HALF, 1)]
    sig.append(dict(id=k, g=v['g'], s=v['s'], f=v['f'], why=v.get('why'), src=v.get('src'), at=v.get('at'), pin=pin))

DATA = dict(grid=dict(x0=X0, z0=Z0, nx=NX, nz=NZ, step=STEP, hmin=round(HMIN, 2), half=HALF),
            rivers=rivers, rivlo=riv_lo, houses=houses, places=places, sig=sig, rules=D.RULES,
            lv=[{q: L_[q] for q in ('k', 'no', 'name', 'mid', 'halo', 'act')} for L_ in D.LV], grp=D.GRP)

JPG = os.path.join(V2, 'figma', '地图组件', 'M7 写实底图.jpg')
tex = base64.b64encode(open(JPG, 'rb').read()).decode()
hb = base64.b64encode(Q).decode()

tpl = open(os.path.join(HERE, 'viewer.html'), encoding='utf-8').read()
html = (tpl.replace('__DATA__', json.dumps(DATA, ensure_ascii=False, separators=(',', ':')))
           .replace('__HEIGHTS__', hb).replace('__TEX__', tex))
out = os.path.join(HERE, 'index.html')
open(out, 'w', encoding='utf-8').write(html)
print('wrote', out, len(html) // 1024, 'KB', '| mesh', NX, 'x', NZ, '| h', round(HMIN), '..', round(max(H)),
      '| houses', len(houses), '| rivers', len(rivers), '| places', [p['n'] for p in places])
