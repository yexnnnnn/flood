#!/usr/bin/env python3
"""Map component, several looks. Each style returns one <g> in map units (0..1000), same placement as design.map_layers.

M0 现状   the current map (for comparison)
M1 白模   white model: soft hillshade, white roofs with a hairline and a cast shadow
M2 体块   massing: oblique extruded blocks, side walls, ground shadow
M3 线稿   line drawing: no shading, contour hierarchy, outlined footprints, double-line roads, hatched water
M4 点阵   halftone: terrain as a dot screen, buildings on a regular 6 m grid
M5 色带   terraced tint: 25 m elevation bands, white footprints

Footprints are regularised for every style except M0: each house takes the dominant orientation of its
neighbourhood (area-weighted, 90°-periodic mean within ~45 m) and sizes snap to 1.5 m.
"""
import os, math, array
import design as D

BW, B = D.BW, D.B
HERE, INK, PAPER = D.HERE, D.INK, D.PAPER
X, Y, V, pts_d, chaikin, G = BW.X, BW.Y, BW.V, BW.pts_d, BW.chaikin, BW.G

# ----------------------------------------------------------------------------- terrain fields (cached)
def _cache(name, build):
    p = os.path.join(HERE, name)
    if os.path.exists(p):
        a = array.array('f'); a.frombytes(open(p, 'rb').read()); return a
    a = array.array('f', build()); open(p, 'wb').write(a.tobytes()); return a

U = _cache('_U6.bin', lambda: BW.upsample(BW.ELEV, BW.N, 6)[0]); M = int(round(math.sqrt(len(U))))
def _shade():
    cs, zf, m = 2 * BW.HALF / M, 2.2, M
    L = []
    for az, wt in [(315, .55), (260, .25), (10, .2)]:
        a, el = math.radians(az), math.radians(42)
        L.append((math.sin(a) * math.cos(el), -math.cos(a) * math.cos(el), math.sin(el), wt))
    flat = math.sin(math.radians(42)); out = []
    for j in range(m):
        jm, jp, row = max(0, j - 1) * m, min(m - 1, j + 1) * m, j * m
        for i in range(m):
            dx = (U[row + min(m - 1, i + 1)] - U[row + max(0, i - 1)]) / (2 * cs) * zf
            dy = (U[jp + i] - U[jm + i]) / (2 * cs) * zf
            ln = math.sqrt(dx * dx + dy * dy + 1); nx, ny, nz = -dx / ln, -dy / ln, 1 / ln
            s = sum(wt * max(0.0, nx * lx + ny * ly + nz * lz) for lx, ly, lz, wt in L)
            out += [max(-1.0, min(1.0, (s - flat) * 2.4)), min(1.0, math.hypot(dx, dy) / zf / 1.1)]
    return out
SH = _cache('_shade6.bin', _shade)       # interleaved (d, slope); d < 0 = shadow side
def bed(i, j):
    b = BW.BED[(j * BW.N // M) * BW.N + (i * BW.N // M)]
    return b > 0 and U[j * M + i] < b / 10

def raster(name, pix):
    cache = os.path.join(HERE, f'_ras_{name}.png')
    if not os.path.exists(cache):
        rows = []
        for j in range(M):
            r = bytearray()
            for i in range(M):
                k = j * M + i; r += bytes(max(0, min(255, int(v))) for v in pix(i, j, U[k], SH[2 * k], SH[2 * k + 1]))
            rows.append(r)
        open(cache, 'wb').write(D.png_rgb(M, M, rows))
    import base64
    return 'data:image/png;base64,' + base64.b64encode(open(cache, 'rb').read()).decode()

mix = lambda a, b, t: [a[q] + (b[q] - a[q]) * t for q in range(3)]
P0 = (245, 243, 239)
def pix_soft(i, j, h, d, sl):
    c = mix(P0, (196, 192, 186), max(0.0, -d) * .62 + sl * .05) if d < 0 else mix(P0, (251, 250, 248), min(1, d) * .5)
    if bed(i, j): c = mix(c, (214, 227, 235), .8)
    return c
LO, HI = min(U), max(U)
def pix_tint(i, j, h, d, sl):
    band = int((h - LO) // 25); nb = int((HI - LO) // 25) + 1; t = (band / max(1, nb - 1)) ** .8
    c = mix((246, 244, 240), (172, 165, 154), t)
    c = mix(c, (140, 135, 128), max(0.0, -d) * .12) if d < 0 else mix(c, (252, 251, 249), min(1, d) * .12)
    if bed(i, j): c = mix(c, (210, 225, 234), .85)
    return c

# ----------------------------------------------------------------------------- footprints
def corners(x, y, w, d, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); hw, hd = w / 2, d / 2
    return [(x + c * u - s * v, y + s * u + c * v) for u, v in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))]
def hull(P):
    P = sorted(set((round(x, 2), round(y, 2)) for x, y in P))
    if len(P) < 3: return P
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]
poly = lambda P: 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in P) + 'Z'

def regular():
    H, out = B.HOUSES, []
    for h in H:
        sx = sy = 0.0
        for g in H:
            dd = (g['x'] - h['x']) ** 2 + (g['z'] - h['z']) ** 2
            if dd < 2025:
                wt = g['w'] * g['d'] * math.exp(-dd / 1250); t = math.radians(g['a']) * 4
                sx += wt * math.cos(t); sy += wt * math.sin(t)
        a = math.degrees(math.atan2(sy, sx)) / 4; a += 90 * round((h['a'] - a) / 90)
        w, d = max(6.0, round(h['w'] / 1.5) * 1.5), max(4.5, round(h['d'] / 1.5) * 1.5)
        out.append(dict(x=X(h['x']), y=Y(h['z']), w=w * V, d=d * V, a=a, m2=w * d, raw=h))
    return out
REG = regular()

# ----------------------------------------------------------------------------- shared layers
def L_contours(minor=(.3, .12, '#3a3530'), index=(.55, .28, '#3a3530')):
    s = ['<g id="等高线" fill="none">']
    for lv, d in D.CONTOURS:
        w, o, c = index if lv % 50 == 0 else minor
        if o > 0: s.append(f'<path d="{d}" stroke="{c}" stroke-width="{w}" stroke-opacity="{o}"/>')
    return ''.join(s) + '</g>'

def L_water(fill='#d6e3eb', edge='#7d9db0', river='#5f87a0', rw=1.1, hatch=False, gully=True):
    s = ['<g id="水系">']
    for d in BW.WATER: s.append(f'<path d="{d}" fill="{"url(#hatchW)" if hatch else fill}" stroke="{edge}" stroke-width=".4"/>')
    for d in BW.DITCH: s.append(f'<path d="{d}" fill="none" stroke="{river}" stroke-width=".45" stroke-opacity=".6"/>')
    if gully:
        for g in BW.gs:
            pts = chaikin(g['path'] + g.get('run', []), 2); n = len(pts)
            for a in range(0, n - 1, max(1, n // 6)):
                s.append(f'<path d="{pts_d(pts[a: a + n // 6 + 2])}" fill="none" stroke="{river}" stroke-width="{.45 + 1.2 * a / n:.2f}" stroke-linecap="round" stroke-opacity=".8"/>')
    s.append(f'<path d="{pts_d(chaikin(BW.RIV, 3))}" fill="none" stroke="{river}" stroke-width="{rw}" stroke-opacity=".8"/>')
    return ''.join(s) + '</g>'

RW = {'main': 2.9, 'lane': 1.7}
def L_roads(kind='white', casing='#cdc7bd', fill='#ffffff', ink=INK):
    s = ['<g id="道路" fill="none" stroke-linecap="round" stroke-linejoin="round">']
    R = [(r, pts_d(chaikin(r['p'], 1))) for r in G['roads']]
    if kind == 'white':
        s += [f'<path d="{d}" stroke="{casing}" stroke-width="{RW[r["k"]] + 1:.1f}"/>' for r, d in R if r['k'] in RW]
        s += [f'<path d="{d}" stroke="{fill}" stroke-width="{RW[r["k"]]}"/>' for r, d in R if r['k'] in RW]
    elif kind == 'double':
        s += [f'<path d="{d}" stroke="{ink}" stroke-opacity=".6" stroke-width="{RW[r["k"]] + .7:.1f}"/>' for r, d in R if r['k'] in RW]
        s += [f'<path d="{d}" stroke="{PAPER}" stroke-width="{RW[r["k"]]}"/>' for r, d in R if r['k'] in RW]
    elif kind == 'hair':
        s += [f'<path d="{d}" stroke="{ink}" stroke-opacity=".45" stroke-width="{.9 if r["k"] == "main" else .5}"/>' for r, d in R if r['k'] in RW]
    for r, d in R:
        if r['k'] == 'track': s.append(f'<path d="{pts_d(r["p"])}" stroke="#8f877c" stroke-width=".6" stroke-dasharray="3 2"/>')
        elif r['k'] not in RW: s.append(f'<path d="{pts_d(r["p"])}" stroke="#8f877c" stroke-width=".5" stroke-dasharray=".2 2"/>')
    return ''.join(s) + '</g>'

def L_labels(c=INK):
    s = ['<g id="地名">']
    RIV = BW.RIV; k = min(range(1, len(RIV)), key=lambda k: abs(RIV[k][1] - 120) + abs(RIV[k][0] - 360) * .3)
    a, b = RIV[k - 1], RIV[k]; ang = math.degrees(math.atan2(Y(b[1]) - Y(a[1]), X(b[0]) - X(a[0])))
    ang = ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang
    mx, my = (X(a[0]) + X(b[0])) / 2 + 24, (Y(a[1]) + Y(b[1])) / 2
    s.append(D.T(mx, my, '拒 马 河', 14, '#4f7690', w=500, anchor='middle', ls=3, extra=f'transform="rotate({ang:.0f} {mx:.1f} {my:.1f})"'))
    s.append(D.T(X(BW.VILLAGE[0]) - 70, Y(BW.VILLAGE[1]) - 92, '沈家庵村', 16, c, w=700, ls=2))
    s.append(D.T(X(-815) - 4, Y(5) + 34, '杜龙沟', 12, c, w=600, ls=2, op=.85))
    for name, d, cx_, cz_, zmax in BW.RES: s.append(D.T(X(cx_), Y(zmax) + 14, name, 9, c, w=500, anchor='middle', ls=1, op=.65))
    return ''.join(s) + '</g>'

def L_fade():
    return ('<g id="边缘渐隐"><rect x="0" y="0" width="140" height="1000" fill="url(#fadeL)"/><rect x="860" y="0" width="140" height="1000" fill="url(#fadeR)"/>'
            '<rect x="0" y="0" width="1000" height="140" fill="url(#fadeT)"/><rect x="0" y="860" width="1000" height="140" fill="url(#fadeB)"/></g>')

def img(uri, op=1): return f'<image id="地形" x="0" y="0" width="1000" height="1000" preserveAspectRatio="none" opacity="{op}" href="{uri}"/>'

# ----------------------------------------------------------------------------- houses per style
def H_model():
    sh, roof = [], []
    for h in REG:
        c = corners(h['x'], h['y'], h['w'], h['d'], h['a']); o = 1.0 + h['d'] * .12
        sh.append(poly(hull(c + [(x + o, y + o) for x, y in c])))
        roof.append(poly(c))
    return (f'<g id="房屋"><path id="房屋-投影" d="{"".join(sh)}" fill="#7d776e" fill-opacity=".32"/>'
            f'<path id="房屋-屋顶" d="{"".join(roof)}" fill="#ffffff" stroke="#2c2926" stroke-opacity=".55" stroke-width=".3" stroke-linejoin="round"/></g>')

def H_block():
    s = ['<g id="房屋">']; shadows = []
    items = sorted(REG, key=lambda h: h['y'])
    for h in REG:
        hm = 6.5 if h['m2'] < 140 else 9.5; hv = hm * V * 1.7
        c = corners(h['x'], h['y'], h['w'], h['d'], h['a'])
        shadows.append(poly(hull(c + [(x + hv * .9, y + hv * .55) for x, y in c])))
    s.append(f'<path id="房屋-地面阴影" d="{"".join(shadows)}" fill="#6f6a62" fill-opacity=".22"/>')
    walls, roofs = [], []
    for h in items:
        hm = 6.5 if h['m2'] < 140 else 9.5; hv = hm * V * 1.7; ox, oy = hv * .35, -hv * .8
        c = corners(h['x'], h['y'], h['w'], h['d'], h['a']); top = [(x + ox, y + oy) for x, y in c]
        s.append(f'<path d="{poly(hull(c + top))}" fill="#d3cec6" stroke="#2c2926" stroke-opacity=".4" stroke-width=".22"/>'
                 f'<path d="{poly(top)}" fill="#ffffff" stroke="#2c2926" stroke-opacity=".5" stroke-width=".25"/>')
    return ''.join(s) + '</g>'

def H_outline(fill=PAPER, op=.75, w=.32):
    return f'<g id="房屋"><path d="{"".join(poly(corners(h["x"], h["y"], h["w"], h["d"], h["a"])) for h in REG)}" fill="{fill}" stroke="{INK}" stroke-opacity="{op}" stroke-width="{w}" stroke-linejoin="round"/></g>'

def H_grid(cell=3.0, sq=2.4, color='#2b2927'):
    occ = set()
    for h in REG:
        c, s_ = math.cos(math.radians(h['a'])), math.sin(math.radians(h['a']))
        nu, nv = max(1, int(h['w'] / .6)), max(1, int(h['d'] / .6))
        for a in range(nu + 1):
            for b in range(nv + 1):
                u, v = -h['w'] / 2 + h['w'] * a / nu, -h['d'] / 2 + h['d'] * b / nv
                occ.add((int((h['x'] + c * u - s_ * v) // cell), int((h['y'] + s_ * u + c * v) // cell)))
    o = (cell - sq) / 2
    d = ''.join(f'M{i * cell + o:.1f} {j * cell + o:.1f}h{sq}v{sq}h-{sq}z' for i, j in sorted(occ))
    return f'<g id="房屋"><path id="房屋-栅格" d="{d}" fill="{color}"/></g>', len(occ)

def T_dots(step=6.0, color='#3b3733'):
    """terrain as a dot screen: radius follows shadow and slope"""
    out = []; f = M / 1000
    n = int(1000 / step)
    for j in range(n):
        for i in range(n):
            x, y = (i + .5) * step + (step / 2 if j % 2 else 0), (j + .5) * step
            if x >= 1000: continue
            pi, pj = min(M - 1, int(x * f)), min(M - 1, int(y * f)); k = pj * M + pi
            d, sl = SH[2 * k], SH[2 * k + 1]
            if bed(pi, pj): continue
            t = max(0.0, -d) * .95 + sl * .35
            r = .32 + 1.9 * min(1, t) ** 1.1
            if r < .42 and (i + j) % 2: continue
            out.append(f'M{x - r:.1f} {y:.1f}a{r:.2f} {r:.2f} 0 1 0 {2 * r:.2f} 0a{r:.2f} {r:.2f} 0 1 0 {-2 * r:.2f} 0')
    return f'<g id="地形-点阵"><path d="{"".join(out)}" fill="{color}" fill-opacity=".5"/></g>'

# ----------------------------------------------------------------------------- styles
STYLES = [
    ('M0', '现状', 'Current', '目前用的版本：真实轮廓、黑色实心，角度和大小都不统一。', None),
    ('M1', '白模', 'White Model', '像俯拍一个白色建筑模型：柔和晕渲，白色屋顶加一根细线，投影统一朝东南。', 'model'),
    ('M2', '体块', 'Massing', '斜投影体块：屋顶、墙面、地面阴影三层，房子有了高度，村子的形状更大气。', 'block'),
    ('M3', '线稿', 'Line Drawing', '只有线：等高线分主次，房屋只描边，道路双线，水面排线。最接近建筑学图纸。', 'line'),
    ('M4', '点阵', 'Halftone Grid', '地形变成点阵网屏，房屋落到 6 米网格上，统一用灰色方点。最规整，最有科技感。', 'grid'),
    ('M5', '色带', 'Terraced Tint', '每 25 米一级高程色带，像梯田一样一层层退后，白色房屋浮在谷底。', 'tint'),
]
EXTRA_DEFS = ('<pattern id="hatchW" width="2.2" height="2.2" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">'
              '<rect width="2.2" height="2.2" fill="#e4edf2"/><line x1="0" y1="0" x2="0" y2="2.2" stroke="#6f93a8" stroke-width=".35"/></pattern>')

def style_svg(key):
    if key == 'M0': return D.map_layers('', D.hillshade_uri())
    s = [f'<g id="地图-{key}"><rect id="纸" width="1000" height="1000" fill="{PAPER}"/>']
    if key == 'M1':
        s += [img(raster('soft', pix_soft)), L_contours((.28, .1, '#4a443d'), (.5, .22, '#4a443d')), L_water(), L_roads('white', '#d4cec4'), H_model()]
    elif key == 'M2':
        s += [img(raster('soft', pix_soft)), L_contours((.28, .08, '#4a443d'), (.5, .2, '#4a443d')), L_water(), L_roads('white', '#d4cec4'), H_block()]
    elif key == 'M3':
        s += [img(raster('soft', pix_soft), .22), L_contours((.3, .3, INK), (.62, .62, INK)), L_water(hatch=True, edge='#5f87a0'), L_roads('double'), H_outline()]
    elif key == 'M4':
        g, n = H_grid(2.5, 1.9, '#6b665f')
        s += [T_dots(7.0, '#8a847b'), L_contours((.3, 0, INK), (.4, .14, INK)), L_water(fill='#dce8ef', edge='none', river='#3f7fa6', rw=1.3), L_roads('hair'), g]
    elif key == 'M5':
        s += [img(raster('tint', pix_tint)), L_contours((.25, .1, '#3a3530'), (.5, .35, '#3a3530')), L_water(), L_roads('white', '#bfb8ad'), H_outline('#ffffff', .6, .3)]
    s += [L_labels(), L_fade(), '</g>']
    return ''.join(s)
