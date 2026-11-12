#!/usr/bin/env python3
"""沈家庵村 · 《水记得路》 山洪泥石流征兆卡 v0.2  ->  card/index.html

Idea: elders say water always takes the same paths. GIS can show those paths: HAND (Height Above Nearest
Drainage, computed from the DEM's flow directions) is a standard flood-mapping index. Wherever HAND is small,
water and debris can reach. That field is drawn as light on a black map (additive, pure colours).
Back side: four steps as small multiples of the 杜龙沟 catchment; the light moves sky -> slopes -> creek -> village.

Data: ../shenjia_embed.js (Copernicus GLO-30 DEM, OSM roads, DEM gullies, houses from satellite screenshots)
      + EAST_BANK below: buildings east of the 拒马河 digitised by eye from the same satellite mosaic.
"""
import json, math, heapq, html, os, base64, struct, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', 'shenjia_embed.js'), encoding='utf-8').read()
G = json.loads(src[src.index('{'):src.rindex('}') + 1])
N, HALF = G['N'], G['half']; CELL = 2 * HALF / N
ELEV = [v / 10 for v in struct.unpack(f'<{N * N}H', base64.b64decode(G['elev']))]
ACC = struct.unpack(f'<{N * N}H', base64.b64decode(G['acc']))
DOWN = base64.b64decode(G['down'])
GID = base64.b64decode(G['gid'])
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]   # (dj, di)
cx = lambda i: -HALF + (i + .5) * CELL
cell = lambda x, z: (min(N - 1, max(0, int((z + HALF) / CELL))) * N + min(N - 1, max(0, int((x + HALF) / CELL))))

# ------------------------------------------------------------ east bank houses (digitised)
# mosaic pixel centres (x, y, w, h, angle deg) read off full-resolution crops; 1 px = 0.4504 m
GR = json.load(open(os.path.join(HERE, '..', '_analysis', 'georef.json')))
A0, B0 = (2127, 520), (2527, 1200)
EAST_PX = [(A0, p) for p in [(135, 42, 40, 40, 0), (108, 162, 50, 20, -30), (150, 148, 20, 15, 0), (300, 50, 30, 25, 0), (345, 45, 25, 20, 0), (330, 95, 50, 25, 0),
                             (335, 135, 20, 20, 0), (112, 260, 45, 35, 0), (148, 250, 30, 30, 0), (200, 262, 25, 40, 0), (258, 240, 35, 30, 0), (172, 295, 25, 35, 0),
                             (258, 312, 40, 25, 0), (255, 345, 45, 25, 0), (155, 380, 70, 30, 0), (180, 455, 85, 35, -25), (460, 445, 45, 30, 0), (310, 555, 55, 30, 0),
                             (230, 590, 25, 70, -30), (175, 520, 20, 20, 0), (300, 690, 25, 60, -30), (360, 740, 90, 60, -30), (320, 780, 45, 70, -30), (510, 790, 40, 35, 0),
                             (425, 830, 55, 45, -30), (460, 880, 70, 45, -30), (520, 860, 45, 45, 0), (600, 600, 30, 30, 0), (620, 645, 45, 30, 0), (705, 605, 40, 30, 0),
                             (745, 655, 45, 35, 0), (720, 695, 45, 30, -20), (590, 700, 40, 30, 0), (700, 740, 30, 25, 0), (575, 495, 60, 25, -15), (395, 600, 30, 25, 0),
                             (470, 660, 20, 20, 0), (620, 820, 40, 30, 0)]] + \
          [(B0, p) for p in [(150, 330, 90, 40, -25), (195, 315, 40, 30, -25), (225, 425, 70, 50, -25), (290, 430, 40, 35, -25), (185, 490, 50, 40, -25),
                             (280, 520, 50, 40, -25), (270, 610, 100, 55, -25), (295, 745, 70, 55, -25), (430, 75, 35, 25, 0), (230, 165, 25, 20, 0),
                             (900, 775, 30, 30, 0), (615, 1275, 55, 35, 0), (665, 1270, 30, 60, -30), (615, 1305, 30, 25, 0)]]
def px2m(o, p):
    X, Y = o[0] + p[0], o[1] + p[1]
    lon = GR['lonO'] + X * GR['mpp'] / GR['KX']; lat = GR['latO'] - Y * GR['mpp'] / GR['KY']
    return (lon - G['center'][0]) * GR['KX'], -(lat - G['center'][1]) * GR['KY']
HOUSES = [dict(x=h[0], z=h[1], w=math.sqrt(max(h[2], 30)) * 1.25, d=math.sqrt(max(h[2], 30)) / 1.25, a=-math.degrees(h[3]), east=False) for h in G['houses']]
n_east_new = 0
for o, p in EAST_PX:
    x, z = px2m(o, p)
    if any(abs(h['x'] - x) < 9 and abs(h['z'] - z) < 9 for h in HOUSES): continue
    HOUSES.append(dict(x=x, z=z, w=p[2] * GR['mpp'], d=p[3] * GR['mpp'], a=p[4], east=True)); n_east_new += 1

# ------------------------------------------------------------ HAND (height above nearest drainage)
RIV = G['river']
def segd(x, z, pts):
    best = 1e9
    for a, b in zip(pts, pts[1:]):
        dx, dz = b[0] - a[0], b[1] - a[1]; L = dx * dx + dz * dz or 1; t = max(0, min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / L))
        best = min(best, math.hypot(x - a[0] - dx * t, z - a[1] - dz * t))
    return best
RD = [segd(cx(k % N), cx(k // N), RIV) for k in range(N * N)]
CH_RIVER = [RD[k] < 45 for k in range(N * N)]
GPTS = [g['path'] + g.get('run', []) for g in G['gullies']]
CH_GULLY = [False] * (N * N)
for pts in GPTS:
    for k in range(N * N):
        if not CH_GULLY[k] and segd(cx(k % N), cx(k // N), pts) < 16: CH_GULLY[k] = True
CH = [CH_RIVER[k] or CH_GULLY[k] for k in range(N * N)]
def down(k):
    d = DOWN[k]
    if d == 255: return -1
    dj, di = N8[d]; i, j = k % N + di, k // N + dj
    return j * N + i if 0 <= i < N and 0 <= j < N else -1
HAND = [99.0] * (N * N); KIND = [0] * (N * N)    # KIND: 1 = drains to the Juma, 2 = to a gully
for k in range(N * N):
    q, n = k, 0
    while q >= 0 and not CH[q] and n < 400: q = down(q); n += 1
    if q >= 0 and CH[q]:
        HAND[k] = max(0.0, ELEV[k] - ELEV[q]); KIND[k] = 1 if CH_RIVER[q] else 2
def hand_at(x, z): return HAND[cell(x, z)], KIND[cell(x, z)]
for h in HOUSES: h['hand'], h['kind'] = hand_at(h['x'], h['z']); h['drun'] = segd(h['x'], h['z'], G['gullies'][0].get('run', []) or [(1e6, 1e6), (1e6, 1e6)])
LOW = 5.0
n_low = sum(1 for h in HOUSES if h['hand'] < LOW)
n_low_r = sum(1 for h in HOUSES if h['hand'] < LOW and h['kind'] == 1); n_low_g = n_low - n_low_r

# ------------------------------------------------------------ raster helpers
def png(w, h, rows):   # rows: list of bytearrays RGBA
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return 'data:image/png;base64,' + base64.b64encode(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b'')).decode()
def bil(F, x, z):
    gx, gz = (x + HALF) / CELL - .5, (z + HALF) / CELL - .5; i, j = int(math.floor(gx)), int(math.floor(gz)); u, v = gx - i, gz - j
    f = lambda a, b: F[min(N - 1, max(0, b)) * N + min(N - 1, max(0, a))]
    return (f(i, j) * (1 - u) + f(i + 1, j) * u) * (1 - v) + (f(i, j + 1) * (1 - u) + f(i + 1, j + 1) * u) * v
def raster(ext, w, h, fn):
    x0, x1, z0, z1 = ext; rows = []
    for py in range(h):
        z = z0 + (py + .5) / h * (z1 - z0); r = bytearray()
        for px_ in range(w):
            x = x0 + (px_ + .5) / w * (x1 - x0); c = fn(x, z); r += bytes(max(0, min(255, int(v))) for v in c)
        rows.append(r)
    return png(w, h, rows)
def hillshade(x, z):
    e = 12; dzdx = (bil(ELEV, x + e, z) - bil(ELEV, x - e, z)) / (2 * e); dzdz = (bil(ELEV, x, z + e) - bil(ELEV, x, z - e)) / (2 * e)
    nx, ny, nz = -dzdx * 1.6, 1, -dzdz * 1.6; l = math.sqrt(nx * nx + ny * ny + nz * nz)
    s = max(0, (-0.55 * nx + 0.75 * ny - 0.38 * nz) / l)
    v = 255 * (s ** 2.2) * 0.5
    return (v * .86, v * .92, v, 255 * min(1, .25 + s))

# light per field: (r, g, b, alpha) on black, combined additively ("screen")
BLUE, CYAN, MAG, ORANGE, LIME, WHITE = (40, 90, 255), (0, 229, 255), (255, 31, 180), (255, 90, 20), (200, 255, 0), (255, 255, 255)
def mixc(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def hand_light(x, z):
    k = cell(x, z); hd = bil(HAND, x, z); kind = KIND[k]
    if hd > 10 or kind == 0: return (0, 0, 0, 0)
    t = max(0.0, 1 - hd / 10) ** 1.8
    c = mixc(BLUE, CYAN, t ** 2) if kind == 1 else mixc(ORANGE, MAG, 1 - t)
    if kind == 2: t *= min(1, 0.45 + math.log10(1 + ACC[k]) / 3.2)
    return (*c, 255 * t)

# ------------------------------------------------------------ svg helpers
INK, BG = '#f5f5f2', '#050506'
SANS = '"PingFang SC","Noto Sans SC","Source Han Sans SC","Helvetica Neue",Arial,sans-serif'
MONO = '"JetBrains Mono","SF Mono",ui-monospace,Menlo,Consolas,monospace'
esc = html.escape
def text(x, y, s, size, weight=400, fill=INK, family=SANS, anchor='start', ls=0, op=1):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{family}\' font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'fill-opacity="{op}" text-anchor="{anchor}" letter-spacing="{ls}">{esc(s)}</text>')
DEFS = ('<defs><filter id="g1" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter>'
        '<filter id="g2" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4"/></filter>'
        '<filter id="g3" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="22"/></filter></defs>')

class Map:
    def __init__(s, ext, box): s.ext, s.box = ext, box
    def P(s, x, z):
        x0, x1, z0, z1 = s.ext; X, Y, W, H = s.box
        return X + (x - x0) / (x1 - x0) * W, Y + (z - z0) / (z1 - z0) * H
    def d(s, pts): return 'M' + ' L'.join('%.1f %.1f' % s.P(*p) for p in pts)
    def img(s, uri, extra=''):
        X, Y, W, H = s.box
        return f'<image href="{uri}" x="{X}" y="{Y}" width="{W}" height="{H}" preserveAspectRatio="none" {extra}/>'
    def contours(s, step, op_minor, op_major, major=100):
        x0, x1, z0, z1 = s.ext; out = []
        lo, hi = min(ELEV), max(ELEV)
        for lv in range(int(lo // step + 1) * step, int(hi), step):
            segs = []
            for j in range(N - 1):
                zz = cx(j)
                if zz < z0 - CELL or zz > z1: continue
                for i in range(N - 1):
                    xx = cx(i)
                    if xx < x0 - CELL or xx > x1: continue
                    v = [ELEV[j * N + i], ELEV[j * N + i + 1], ELEV[(j + 1) * N + i + 1], ELEV[(j + 1) * N + i]]
                    c = [(cx(i), cx(j)), (cx(i + 1), cx(j)), (cx(i + 1), cx(j + 1)), (cx(i), cx(j + 1))]; pts = []
                    for a in range(4):
                        b = (a + 1) % 4
                        if (v[a] < lv) != (v[b] < lv): t = (lv - v[a]) / (v[b] - v[a]); pts.append((c[a][0] + (c[b][0] - c[a][0]) * t, c[a][1] + (c[b][1] - c[a][1]) * t))
                    for q in range(0, len(pts) - 1, 2):
                        a0, b0 = s.P(*pts[q]); a1, b1 = s.P(*pts[q + 1]); segs.append(f'M{a0:.1f} {b0:.1f}L{a1:.1f} {b1:.1f}')
            if segs:
                mj = lv % major == 0
                out.append(f'<path d="{"".join(segs)}" fill="none" stroke="#ffffff" stroke-width="{1.0 if mj else .6}" stroke-opacity="{op_major if mj else op_minor}"/>')
        return ''.join(out)
    def houses(s, scale, colour=None):
        out = {}
        for h in s.houses_in():
            X, Y = s.P(h['x'], h['z']); w, d = max(3.2, h['w'] * scale), max(2.4, h['d'] * scale)
            c = colour(h) if colour else '#ffffff'
            out.setdefault(c, []).append(f'<rect x="{X - w / 2:.1f}" y="{Y - d / 2:.1f}" width="{w:.1f}" height="{d:.1f}" transform="rotate({h["a"]:.0f} {X:.1f} {Y:.1f})"/>')
        return ''.join(f'<g fill="{c}">{"".join(v)}</g>' for c, v in out.items())
    def houses_in(s):
        x0, x1, z0, z1 = s.ext
        return [h for h in HOUSES if x0 < h['x'] < x1 and z0 < h['z'] < z1]
    def clip(s, cid):
        X, Y, W, H = s.box
        return f'<clipPath id="{cid}"><rect x="{X}" y="{Y}" width="{W}" height="{H}"/></clipPath>'

# road graph route (for the shelter lines)
def route(start, goal):
    nodes, adj = [], {}
    def nid(p):
        for k, q in enumerate(nodes):
            if abs(q[0] - p[0]) < 4 and abs(q[1] - p[1]) < 4: return k
        nodes.append(p); return len(nodes) - 1
    for r in G['roads']:
        prev = None
        for p in r['p']:
            k = nid(tuple(p))
            if prev is not None and prev != k:
                dd = math.dist(nodes[prev], nodes[k]); adj.setdefault(prev, []).append((k, dd)); adj.setdefault(k, []).append((prev, dd))
            prev = k
    s0 = min(range(len(nodes)), key=lambda k: math.dist(nodes[k], start)); dist = {s0: 0}; prv = {}; pq = [(0, s0)]
    while pq:
        dd, u = heapq.heappop(pq)
        if dd > dist[u]: continue
        for v, w in adj.get(u, []):
            if dd + w < dist.get(v, 1e18): dist[v] = dd + w; prv[v] = u; heapq.heappush(pq, (dd + w, v))
    t = min(dist, key=lambda k: math.dist(nodes[k], goal) * 3 + dist[k] * .2); p = [goal]
    while True:
        p.append(nodes[t])
        if t == s0: break
        t = prv[t]
    return p[::-1]

W, H = 1480, 2100
HOME = (-60, -60)
SHELTERS = [(-682, -262), (-232, 698)]
village_e = sorted(bil(ELEV, h['x'], h['z']) for h in HOUSES if not h['east'] and abs(h['x'] + 50) < 450 and abs(h['z'] + 80) < 450)[len(HOUSES) // 6]

# ------------------------------------------------------------ front
def front():
    M = Map((-1200, 1200, -1015, 1045), (0, 470, W, 1290))
    hill = M.img(raster(M.ext, 400, 215, hillshade), 'opacity=".55"')
    glow = raster(M.ext, 400, 215, hand_light)
    s = [DEFS, f'<rect width="{W}" height="{H}" fill="{BG}"/>', M.clip('mf'), '<g clip-path="url(#mf)">', hill, M.contours(20, .05, .13)]
    s.append('<g style="mix-blend-mode:screen">' + M.img(glow, 'filter="url(#g1)" opacity=".95"') + M.img(glow, 'filter="url(#g2)" opacity=".8"') + '</g>')
    RW = {'main': 1.6, 'lane': 1.0, 'track': .8, 'path': .6}
    s.append('<g fill="none" stroke="#ffffff">' + ''.join(f'<path d="{M.d(r["p"])}" stroke-width="{RW.get(r["k"], .8)}" stroke-opacity="{.5 if r["k"] in ("main", "lane") else .28}"/>' for r in G['roads']) + '</g>')
    col = lambda h: ('#7fe9ff' if h['kind'] == 1 else '#ff6fd2') if h['hand'] < LOW else '#ffffff'
    s.append(M.houses(M.box[2] / (M.ext[1] - M.ext[0]), col))
    # shelters: lime light + route hairline
    for g in SHELTERS:
        X, Y = M.P(*g)
        s.append(f'<path d="{M.d(route(HOME, g))}" fill="none" stroke="#c8ff00" stroke-width="2.2" stroke-dasharray="1 7" stroke-linecap="round"/>')
        s.append(f'<g style="mix-blend-mode:screen"><circle cx="{X:.1f}" cy="{Y:.1f}" r="46" fill="#c8ff00" fill-opacity=".55" filter="url(#g3)"/></g>')
        s.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="9" fill="#c8ff00"/><circle cx="{X:.1f}" cy="{Y:.1f}" r="20" fill="none" stroke="#c8ff00" stroke-width="1.4"/>')
        up = bil(ELEV, *g) - village_e
        s.append(text(X + 30, Y - 4, '安置点', 22, 600, '#c8ff00') + text(X + 30, Y + 22, f'+{up:.0f} m', 18, family=MONO, fill='#c8ff00', op=.85))
    X, Y = M.P(*HOME); s.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="7" fill="#fff"/>' + text(X + 16, Y + 7, '你家', 20, 600))
    for nm, (x, z), a in [('拒马河', (520, -620), 'start'), ('杜龙沟', (-1000, -330), 'start'), ('沈家庵', (-330, -260), 'start'), ('一渡', (40, 520), 'start')]:
        X, Y = M.P(x, z); s.append(text(X, Y, nm, 20, 500, op=.75, ls=4))
    s.append('</g>')
    # type
    s.append(text(70, 108, 'SHENJIA’AN · JUMA VALLEY · 39.595N 115.679E', 17, family=MONO, ls=2, op=.6))
    s.append(text(1410, 108, '01 / 02', 17, family=MONO, anchor='end', ls=2, op=.6))
    s.append(text(62, 300, '水记得路。', 150, 700, ls=-4))
    s.append(text(70, 380, '暴雨里，水和泥总是走同一些低处。', 32, op=.72))
    s.append(text(70, 424, '发光的地方，就是它们会经过的地方。', 32, op=.72))
    # numbers
    y = 1870
    s.append(text(62, y, f'{n_low}', 150, 700, '#ff4fd8', ls=-5))
    nw = len(str(n_low)) * 84 + 18
    s.append(text(62 + nw, y, '户', 60, 700, '#ff4fd8'))
    s.append(text(70, y + 44, f'住在比最近的水道高不到 {LOW:.0f} 米的地方', 24, op=.75))
    s.append(text(760, y - 62, f'{n_low_g} 户 · 沟道', 26, 600, '#ff6fd2') + text(800, y - 18, f'{n_low_r} 户 · 拒马河', 26, 600, '#7fe9ff'))
    s.append(text(1160, y - 62, f'2 处', 26, 600, '#c8ff00') + text(1160, y - 18, '安置点', 26, 600, '#c8ff00'))
    s.append(f'<line x1="70" y1="1940" x2="1410" y2="1940" stroke="#fff" stroke-opacity=".18"/>')
    s.append(text(70, 1985, f'HAND（离最近水道的高差）· Copernicus DEM 30 m · OpenStreetMap · 卫星影像识别 {len(HOUSES)} 栋房屋', 15, family=MONO, op=.5))
    s.append(text(70, 2015, '安置点与路线为示意，需村委确认 · 非官方预警，以政府发布为准', 15, family=MONO, op=.5))
    return f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">{"".join(s)}</svg>'

# ------------------------------------------------------------ back: four steps as small multiples
MAIN = G['gullies'][0]
EXT_S = (-1290, 180, -830, 270)
def step_light(lv):
    path = MAIN['path']; run = MAIN.get('run', [])
    hi = sorted(ELEV[k] for k in range(N * N) if EXT_S[0] < cx(k % N) < EXT_S[1] and EXT_S[2] < cx(k // N) < EXT_S[3])
    ridge = hi[int(len(hi) * .7)] if hi else 9e9
    def f(x, z):
        k = cell(x, z)
        if lv == 0:   # cloud cap on the ridge
            e = bil(ELEV, x, z); t = max(0, min(1, (e - ridge) / 140)) ** .8; return (*mixc((70, 120, 255), (200, 225, 255), t), 255 * t * .6)
        if lv == 1:   # the whole catchment soaking up
            if GID[k] != 1: return (0, 0, 0, 0)
            hd = HAND[k]; t = .35 + .45 * max(0, 1 - hd / 60); return (*mixc(BLUE, (150, 60, 255), 1 - hd / 120 if hd < 120 else 0), 255 * t)
        dc = segd(x, z, path); dr = segd(x, z, run) if run else 1e9
        if lv == 2:   # creek turns muddy
            t = max(0, 1 - dc / 55) ** 1.3; c = (0, 0, 0, 0)
            if GID[k] == 1: c = (*BLUE, 40)
            return (*MAG, 255 * t) if t > .02 else c
        t1 = max(0, 1 - dc / 50) ** 1.3; t2 = max(0, 1 - dr / 120) ** 1.1    # debris reaches the village
        if t2 > t1: return (*mixc(ORANGE, (255, 230, 160), t2 ** 2), 255 * t2)
        return (*MAG, 255 * t1)
    return f
STEPS = [('01', '留意', '山戴帽 · 雷声远', '看天，把院里的东西收好', (110, 160, 255)),
         ('02', '准备', '雨下透了 · 雨量桶到 10 cm', '证件和药装好，老人孩子先走', (140, 90, 255)),
         ('03', '转移', '溪水变黄 · 带着树枝 · 桶到 20 cm', '去安置点，不用等通知', (255, 60, 190)),
         ('04', '快跑', '水声突然停 · 沟里轰响', '往沟两侧高处跑，别顺着沟跑', (255, 110, 40))]
def back():
    s = [DEFS, f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    s.append(text(70, 108, 'FOUR STEPS · 杜龙沟 → 沈家庵', 17, family=MONO, ls=2, op=.6))
    s.append(text(1410, 108, '02 / 02', 17, family=MONO, anchor='end', ls=2, op=.6))
    s.append(text(62, 270, '看见什么，', 110, 700, ls=-3))
    s.append(text(62, 395, '就做什么。', 110, 700, ls=-3))
    gw, gh, gx0, gy0, gapx, gapy = 650, 430, 70, 500, 40, 230
    hill = raster(EXT_S, 220, 160, hillshade)
    for i, (no, name, sign, act, c) in enumerate(STEPS):
        X, Y = gx0 + (i % 2) * (gw + gapx), gy0 + (i // 2) * (gh + gapy)
        M = Map(EXT_S, (X, Y, gw, gh)); L = raster(EXT_S, 220, 160, step_light(i))
        s += [M.clip(f'c{i}'), f'<g clip-path="url(#c{i})">', f'<rect x="{X}" y="{Y}" width="{gw}" height="{gh}" fill="#0b0b0d"/>', M.img(hill, 'opacity=".5"'), M.contours(40, .05, .1, 200)]
        s.append('<g style="mix-blend-mode:screen">' + M.img(L, 'filter="url(#g1)"') + M.img(L, 'filter="url(#g2)" opacity=".7"') + '</g>')
        s.append(M.houses(gw / (EXT_S[1] - EXT_S[0]), lambda h, i=i: '#ffc48a' if i == 3 and h['drun'] < 110 else '#6f6f74'))
        s.append(f'<path d="{M.d(MAIN["path"] + MAIN.get("run", []))}" fill="none" stroke="#fff" stroke-width=".8" stroke-opacity=".35"/></g>')
        cc = '#%02x%02x%02x' % c
        s.append(text(X, Y + gh + 64, no, 20, family=MONO, fill=cc, ls=2))
        s.append(text(X + 48, Y + gh + 72, name, 54, 700, cc))
        s.append(text(X, Y + gh + 122, sign, 25, 500, op=.9))
        s.append(text(X, Y + gh + 160, '→ ' + act, 25, op=.62))
    s.append(f'<line x1="70" y1="1940" x2="1410" y2="1940" stroke="#fff" stroke-opacity=".18"/>')
    s.append(text(70, 1985, '雨量桶：直筒桶放空地，水深 1 cm = 雨量 10 mm · 10 / 20 cm 为示意值，需按本沟标定', 15, family=MONO, op=.5))
    s.append(text(70, 2015, '口诀含新编句（现象有官方资料：中国天气网 · 国家应急广播 · 应急管理部门）· 非官方预警', 15, family=MONO, op=.5))
    return f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">{"".join(s)}</svg>'

page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>水记得路 · 沈家庵山洪泥石流征兆卡 v0.2</title>
<style>
@page {{ size: 148mm 210mm; margin: 0 }}
html,body {{ margin:0; background:#000; font-family:{SANS} }}
.wrap {{ display:flex; flex-wrap:wrap; gap:40px; justify-content:center; padding:40px 24px 60px }}
.side {{ width:min(46vw, 640px); aspect-ratio:148/210; box-shadow:0 0 0 1px rgba(255,255,255,.08) }}
.side svg {{ width:100%; height:100%; display:block }}
@media (max-width:900px) {{ .side {{ width:92vw }} }}
@media print {{ .wrap {{ display:block; padding:0 }} .side {{ width:148mm; height:210mm; box-shadow:none; break-after:page }} }}
</style></head><body><div class="wrap"><div class="side">{front()}</div><div class="side">{back()}</div></div></body></html>'''
open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(page)
print(f'houses {len(HOUSES)} (east bank added {n_east_new}) · low (HAND<{LOW:.0f} m) {n_low}: gully {n_low_g}, river {n_low_r} · village elev {village_e:.0f} m · {len(page) // 1024} KB')
