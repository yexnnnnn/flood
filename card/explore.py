#!/usr/bin/env python3
"""Three visual directions for the hero map, same data, light paper -> card/explore.html"""
import os, math
import build_card as B   # reuses data, HAND field, raster + svg helpers (also rebuilds index.html)

PAPER, INK = '#f6f4f0', '#111111'
EXT = (-1000, 900, -900, 1000)
S = 1000
MONO, SANS, text = B.MONO, B.SANS, B.text

def smooth(a, b, x): t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
def lerp3(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

# A · thermal: HAND as concentric spectral bands (outer orange -> blue -> pink -> yellow core)
RAMP = [(0.0, (255, 122, 60)), (.38, (255, 122, 60)), (.55, (64, 128, 255)), (.75, (255, 170, 215)), (1.0, (255, 238, 60))]
def ramp(t):
    for (a, ca), (b, cb) in zip(RAMP, RAMP[1:]):
        if t <= b: return lerp3(ca, cb, (t - a) / (b - a))
    return RAMP[-1][1]
def thermal(x, z):
    hd = B.bil(B.HAND, x, z); k = B.cell(x, z)
    if B.KIND[k] == 0 or hd > 12: return (0, 0, 0, 0)
    t = 1 - hd / 12
    return (*ramp(t), 255 * smooth(0, .25, t) * .95)

# C · one colour: only how far water reaches, electric blue
def blue(x, z):
    hd = B.bil(B.HAND, x, z); k = B.cell(x, z)
    if B.KIND[k] == 0 or hd > 10: return (0, 0, 0, 0)
    t = (1 - hd / 10) ** 1.4
    return (*lerp3((120, 160, 255), (20, 60, 255), t), 255 * t * .85)

def base(M, contour_op=(.09, .2), roads=.45):
    s = [M.contours(20, contour_op[0], contour_op[1])]
    RW = {'main': 1.6, 'lane': 1.0, 'track': .8, 'path': .6}
    s.append('<g fill="none" stroke="#111">' + ''.join(f'<path d="{M.d(r["p"])}" stroke-width="{RW.get(r["k"], .8)}" stroke-opacity="{roads if r["k"] in ("main", "lane") else roads * .5}"/>' for r in B.G['roads']) + '</g>')
    s.append(f'<path d="{M.d(B.G["river"])}" fill="none" stroke="#111" stroke-width="1" stroke-dasharray="1 4" stroke-opacity=".6"/>')
    return ''.join(s)

def label(x, y, s, size=16, bg='#e8f7c2'):
    w = sum(size * (1.0 if ord(c) > 0x2e80 else .62) for c in s) + 16
    return f'<rect x="{x}" y="{y - size - 5}" width="{w:.0f}" height="{size + 12}" fill="{bg}"/>' + text(x + 8, y, s, size, family=MONO, fill=INK, ls=1)

def frame(tag, title, sub, body):
    s = [B.DEFS, f'<rect width="{S}" height="{S + 260}" fill="{PAPER}"/>', body,
         label(40, 60, tag), text(S - 40, 60, 'SHENJIA’AN · 39.595N 115.679E', 14, family=MONO, fill=INK, anchor='end', ls=1.5, op=.7),
         text(40, S + 110, title, 64, 700, INK, ls=-2), text(40, S + 160, sub, 22, fill=INK, op=.6),
         text(40, S + 220, f'HAND < {B.LOW:.0f} m · {B.n_low} / {len(B.HOUSES)} 户 · Copernicus DEM · OSM', 14, family=MONO, fill=INK, op=.55)]
    return f'<svg viewBox="0 0 {S} {S + 260}" xmlns="http://www.w3.org/2000/svg">{"".join(s)}</svg>'

def shelters(M, col='#111'):
    out = []
    for g in B.SHELTERS:
        X, Y = M.P(*g); out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="12" fill="none" stroke="{col}" stroke-width="1.6"/><circle cx="{X:.1f}" cy="{Y:.1f}" r="3.5" fill="{col}"/>')
        out.append(label(X + 18, Y + 6, '安置点', 14, '#ffffff'))
    return ''.join(out)

def variant_a():
    M = B.Map(EXT, (0, 0, S, S)); L = B.raster(EXT, 380, 380, thermal)
    body = [base(M), M.img(L, 'filter="url(#g1)"'), M.img(L, 'filter="url(#g2)" opacity=".55"'),
            M.houses(S / (EXT[1] - EXT[0]), lambda h: '#111'), shelters(M)]
    return frame('A · THERMAL / 热成像', '水记得路', '颜色越“热”，离水道越近：黄心是水会先到的地方。', ''.join(body))

def variant_b():
    M = B.Map(EXT, (0, 0, S, S)); sc = S / (EXT[1] - EXT[0]); dots = []
    for h in M.houses_in():
        X, Y = M.P(h['x'], h['z'])
        if h['hand'] < B.LOW:
            c = '#ff3d9a' if h['kind'] == 2 else '#2f7bff'; r = 14 + (B.LOW - h['hand']) * 3
            dots.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{r:.1f}" fill="{c}" fill-opacity=".38"/>')
        elif h['hand'] < 12:
            dots.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="9" fill="#ffb03a" fill-opacity=".28"/>')
    body = [base(M, (.06, .14), .35), f'<g filter="url(#g2)">{"".join(dots)}</g>',
            M.houses(sc, lambda h: ('#ff3d9a' if h['kind'] == 2 else '#2f7bff') if h['hand'] < B.LOW else '#111'), shelters(M)]
    return frame('B · DIFFUSE POINTS / 弥散点', '218 户', '每一团光是一户人家：粉色靠近沟道，蓝色靠近拒马河。', ''.join(body))

def variant_c():
    M = B.Map(EXT, (0, 0, S, S)); L = B.raster(EXT, 380, 380, blue)
    body = [base(M, (.12, .26), .6), M.img(L, 'filter="url(#g1)" opacity=".9"'),
            M.houses(S / (EXT[1] - EXT[0]), lambda h: '#ff1f8f' if h['hand'] < B.LOW else '#111'), shelters(M)]
    return frame('C · LINE + ONE LIGHT / 线 + 一种光', '水会到这里', '只有一种颜色：水能到的范围。品红色是在这个范围里的房子。', ''.join(body))

page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>水记得路 · 三个视觉方向</title><style>
html,body{{margin:0;background:#e9e6e0;font-family:{SANS}}}
.wrap{{display:flex;flex-wrap:wrap;gap:28px;justify-content:center;padding:36px 20px 60px}}
.v{{width:min(31vw,520px);min-width:320px;box-shadow:0 20px 50px -30px rgba(0,0,0,.35)}}.v svg{{display:block;width:100%;height:auto}}
</style></head><body><div class="wrap"><div class="v">{variant_a()}</div><div class="v">{variant_b()}</div><div class="v">{variant_c()}</div></div></body></html>'''
open(os.path.join(B.HERE, 'explore.html'), 'w', encoding='utf-8').write(page)
print('wrote explore.html', len(page) // 1024, 'KB')
