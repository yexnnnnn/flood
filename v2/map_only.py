#!/usr/bin/env python3
"""Map-only components for Figma: v2/figma/地图组件/M3 线稿.svg, M4 点阵.svg, M6 点阵晕渲.svg (M4 houses on the M1 shaded base)

Built so every piece can be selected and dragged after the SVG is dropped into Figma:
- each house is its own layer (M3: a real rotated <rect>; M4: one compound path of its grid cells),
  houses are grouped into 片区 by proximity, so a whole cluster or a single house can be moved
- each road, contour, river, ditch and gully is its own named path
- no <pattern>, <clipPath>, filters or paint-order (Figma drops or mangles them); hatching is real lines
- 1 SVG px = 1 map unit; the frame is 1000 x 1000
"""
import os, re, math
import map_styles as S

D, BW = S.D, S.BW
INK, PAPER, X, Y, V = S.INK, S.PAPER, S.X, S.Y, S.V
pts_d, chaikin, G = S.pts_d, S.chaikin, S.G
OUT = os.path.join(D.HERE, 'figma', '地图组件'); os.makedirs(OUT, exist_ok=True)
SZ = 1000

# ----------------------------------------------------------------------------- house clusters (片区)
def split(g, size=45):
    """chained clusters get long; cut big ones into compact blocks of ~size houses (k-means, fixed seeds)"""
    k = round(len(g) / size)
    if k < 2: return [g]
    P = [(S.REG[i]['x'], S.REG[i]['y']) for i in g]
    C = [P[int(j * len(P) / k)] for j in range(k)]
    for _ in range(30):
        lab = [min(range(k), key=lambda c: (p[0] - C[c][0]) ** 2 + (p[1] - C[c][1]) ** 2) for p in P]
        C = [(sum(p[0] for p, l in zip(P, lab) if l == c) / max(1, lab.count(c)),
              sum(p[1] for p, l in zip(P, lab) if l == c) / max(1, lab.count(c))) if c in lab else C[c] for c in range(k)]
    return [[i for i, l in zip(g, lab) if l == c] for c in range(k) if c in lab]

def clusters(link=30 * V):
    n = len(S.REG); par = list(range(n))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(n):
        a = S.REG[i]
        for j in range(i + 1, n):
            b = S.REG[j]
            if (a['x'] - b['x']) ** 2 + (a['y'] - b['y']) ** 2 < link * link: par[f(i)] = f(j)
    grp = {}
    for i in range(n): grp.setdefault(f(i), []).append(i)
    grp = {k: g for k0, g0 in grp.items() for k, g in enumerate(split(g0), start=k0 * 100)}
    big = sorted((g for g in grp.values() if len(g) >= 4), key=lambda g: (min(S.REG[i]['y'] for i in g)))
    loose = [i for g in grp.values() if len(g) < 4 for i in g]
    return [(f'片区-{k + 1:02d}', g) for k, g in enumerate(big)] + ([('散户', loose)] if loose else [])
CL = clusters()

def houses_rect(fill=PAPER, stroke=INK, op=.75, w=.32):
    s = ['<g id="房屋">']
    for name, idx in CL:
        s.append(f'<g id="{name}">')
        for n, i in enumerate(idx):
            h = S.REG[i]
            s.append(f'<rect id="{name}-{n + 1:03d}" x="{h["x"] - h["w"] / 2:.2f}" y="{h["y"] - h["d"] / 2:.2f}" width="{h["w"]:.2f}" height="{h["d"]:.2f}" '
                     f'transform="rotate({h["a"]:.1f} {h["x"]:.2f} {h["y"]:.2f})" fill="{fill}" stroke="{stroke}" stroke-opacity="{op}" stroke-width="{w}"/>')
        s.append('</g>')
    return ''.join(s) + '</g>'

def houses_grid(cell=2.5, sq=1.9, color='#6b665f', shadow=None):
    taken, s, o = set(), ['<g id="房屋">'], (cell - sq) / 2
    for name, idx in CL:
        s.append(f'<g id="{name}">')
        for n, i in enumerate(idx):
            h = S.REG[i]; c, s_ = math.cos(math.radians(h['a'])), math.sin(math.radians(h['a']))
            nu, nv = max(1, int(h['w'] / .6)), max(1, int(h['d'] / .6)); mine = set()
            for a in range(nu + 1):
                for b in range(nv + 1):
                    u, v = -h['w'] / 2 + h['w'] * a / nu, -h['d'] / 2 + h['d'] * b / nv
                    k = (int((h['x'] + c * u - s_ * v) // cell), int((h['y'] + s_ * u + c * v) // cell))
                    if k not in taken: mine.add(k)
            taken |= mine
            if mine:
                d = ''.join(f'M{p * cell + o:.1f} {q * cell + o:.1f}h{sq}v{sq}h-{sq}z' for p, q in sorted(mine))
                if shadow:   # one group per house: cast shadow + dots move together
                    sd = ''.join(f'M{p * cell:.1f} {q * cell:.1f}h{cell}v{cell}h-{cell}z' for p, q in sorted(mine))
                    s.append(f'<g id="{name}-{n + 1:03d}"><path id="投影" d="{sd}" transform="translate({shadow[0]} {shadow[0]})" fill="#7d776e" fill-opacity="{shadow[1]}"/>'
                             f'<path id="点" d="{d}" fill="{color}"/></g>')
                else: s.append(f'<path id="{name}-{n + 1:03d}" d="{d}" fill="{color}"/>')
        s.append('</g>')
    return ''.join(s) + '</g>'

# ----------------------------------------------------------------------------- lines
def contours(minor, index):
    s = ['<g id="等高线"><g id="等高线-计曲线 50m">']
    for lv, d in D.CONTOURS:
        if lv % 50 == 0: s.append(f'<path id="等高线-{lv:.0f}m" d="{d}" fill="none" stroke="{index[2]}" stroke-width="{index[0]}" stroke-opacity="{index[1]}"/>')
    s.append('</g>')
    if minor[1] > 0:
        s.append('<g id="等高线-首曲线 10m">')
        for lv, d in D.CONTOURS:
            if lv % 50: s.append(f'<path id="等高线-{lv:.0f}m" d="{d}" fill="none" stroke="{minor[2]}" stroke-width="{minor[0]}" stroke-opacity="{minor[1]}"/>')
        s.append('</g>')
    return ''.join(s) + '</g>'

def poly_of(d):
    v = [float(t) for t in re.findall(r'-?\d+(?:\.\d+)?', d)]
    return list(zip(v[0::2], v[1::2]))

def hatch(P, gap=2.2, ang=-35):
    """hatch lines inside polygon P as real segments (Figma has no <pattern>)"""
    a = math.radians(-ang); ca, sa = math.cos(a), math.sin(a)
    R = [(x * ca - y * sa, x * sa + y * ca) for x, y in P]
    ys = [p[1] for p in R]; out = []
    y = math.floor(min(ys) / gap) * gap + gap / 2
    while y < max(ys):
        xs = []
        for (x1, y1), (x2, y2) in zip(R, R[1:] + R[:1]):
            if (y1 <= y < y2) or (y2 <= y < y1): xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for x1, x2 in zip(xs[0::2], xs[1::2]):
            p = [(u * ca + y * sa, -u * sa + y * ca) for u in (x1, x2)]
            out.append(f'M{p[0][0]:.1f} {p[0][1]:.1f}L{p[1][0]:.1f} {p[1][1]:.1f}')
        y += gap
    return ''.join(out)

def water(fill, edge, river, rw, hatched=False):
    s = ['<g id="水系">']
    for n, d in enumerate(BW.WATER):
        s.append(f'<g id="水面-{n + 1}"><path id="水面-{n + 1}-底" d="{d}" fill="{fill}" stroke="{edge}" stroke-width=".4"/>')
        if hatched: s.append(f'<path id="水面-{n + 1}-排线" d="{hatch(poly_of(d))}" fill="none" stroke="#6f93a8" stroke-width=".35"/>')
        s.append('</g>')
    for n, d in enumerate(BW.DITCH):
        s.append(f'<path id="水渠-{n + 1}" d="{d}" fill="none" stroke="{river}" stroke-width=".45" stroke-opacity=".6"/>')
    for n, g in enumerate(BW.gs):
        pts = chaikin(g['path'] + g.get('run', []), 2); m = len(pts); k = max(1, m // 6)
        seg = [f'<path d="{pts_d(pts[a: a + k + 2])}" fill="none" stroke="{river}" stroke-width="{.45 + 1.2 * a / m:.2f}" stroke-linecap="round" stroke-opacity=".8"/>'
               for a in range(0, m - 1, k)]
        s.append(f'<g id="支沟-{n + 1}">{"".join(seg)}</g>')
    s.append(f'<path id="拒马河-主流线" d="{pts_d(chaikin(BW.RIV, 3))}" fill="none" stroke="{river}" stroke-width="{rw}" stroke-opacity=".8"/>')
    return ''.join(s) + '</g>'

NAME = {'main': '主路', 'lane': '村路'}
def roads(kind):
    if kind == 'white':
        R = [(n, r, pts_d(chaikin(r['p'], 1))) for n, r in enumerate(G['roads'])]
        out = ['<g id="道路"><g id="道路-边线">'] + [f'<path id="{NAME[r["k"]]}-{n:03d}-边线" d="{d}" fill="none" stroke="#d4cec4" stroke-width="{S.RW[r["k"]] + 1:.1f}" stroke-linecap="round" stroke-linejoin="round"/>' for n, r, d in R if r['k'] in S.RW]
        out += ['</g><g id="道路-路面">'] + [f'<path id="{NAME[r["k"]]}-{n:03d}-路面" d="{d}" fill="none" stroke="#ffffff" stroke-width="{S.RW[r["k"]]}" stroke-linecap="round" stroke-linejoin="round"/>' for n, r, d in R if r['k'] in S.RW]
        paths = roads('hair'); paths = paths[paths.index('<g id="道路-小径">'):-len('</g>')]   # reuse the 小径 group
        return ''.join(out) + '</g>' + paths + '</g>'
    R = [(n, r, pts_d(chaikin(r['p'], 1))) for n, r in enumerate(G['roads'])]
    s = ['<g id="道路">']
    if kind == 'double':
        # two layers so junctions stay clean; the same number marks the two halves of one road
        s.append('<g id="道路-边线">' + ''.join(f'<path id="{NAME[r["k"]]}-{n:03d}-边线" d="{d}" fill="none" stroke="{INK}" stroke-opacity=".6" stroke-width="{S.RW[r["k"]] + .7:.1f}" stroke-linecap="round" stroke-linejoin="round"/>' for n, r, d in R if r['k'] in S.RW) + '</g>')
        s.append('<g id="道路-路面">' + ''.join(f'<path id="{NAME[r["k"]]}-{n:03d}-路面" d="{d}" fill="none" stroke="{PAPER}" stroke-width="{S.RW[r["k"]]}" stroke-linecap="round" stroke-linejoin="round"/>' for n, r, d in R if r['k'] in S.RW) + '</g>')
    else:
        s.append('<g id="道路-主路村路">' + ''.join(f'<path id="{NAME[r["k"]]}-{n:03d}" d="{d}" fill="none" stroke="{INK}" stroke-opacity=".45" stroke-width="{.9 if r["k"] == "main" else .5}" stroke-linecap="round" stroke-linejoin="round"/>' for n, r, d in R if r['k'] in S.RW) + '</g>')
    s.append('<g id="道路-小径">')
    for n, r, d in R:
        if r['k'] == 'track': s.append(f'<path id="机耕路-{n:03d}" d="{pts_d(r["p"])}" fill="none" stroke="#8f877c" stroke-width=".6" stroke-dasharray="3 2"/>')
        elif r['k'] not in S.RW: s.append(f'<path id="小路-{n:03d}" d="{pts_d(r["p"])}" fill="none" stroke="#8f877c" stroke-width=".5" stroke-dasharray=".2 2" stroke-linecap="round"/>')
    return ''.join(s) + '</g></g>'

def labels():
    # D.T without the paint-order halo: Figma would draw the halo stroke on top of the glyphs
    s = S.L_labels().replace('paint-order="stroke" ', '')
    s = re.sub(r' stroke="[^"]*" stroke-width="3" stroke-linejoin="round"', '', s)
    names = iter(['地名-拒马河', '地名-沈家庵村', '地名-杜龙沟'] + [f'地名-{r[0]}' for r in BW.RES])
    return re.sub(r'<text ', lambda m: f'<text id="{next(names)}" ', s)

# ----------------------------------------------------------------------------- terrain
def dots(step=7.0, color='#8a847b', tile=250):
    """halftone terrain, split into 4x4 tiles so the layer stays light and parts can be moved or deleted"""
    T = {}; f = S.M / 1000; n = int(1000 / step)
    for j in range(n):
        for i in range(n):
            x, y = (i + .5) * step + (step / 2 if j % 2 else 0), (j + .5) * step
            if x >= 1000: continue
            pi, pj = min(S.M - 1, int(x * f)), min(S.M - 1, int(y * f)); k = pj * S.M + pi
            d, sl = S.SH[2 * k], S.SH[2 * k + 1]
            if S.bed(pi, pj): continue
            r = .32 + 1.9 * min(1, max(0.0, -d) * .95 + sl * .35) ** 1.1
            if r < .42 and (i + j) % 2: continue
            T.setdefault((int(y // tile), int(x // tile)), []).append(
                f'M{x - r:.1f} {y:.1f}a{r:.2f} {r:.2f} 0 1 0 {2 * r:.2f} 0a{r:.2f} {r:.2f} 0 1 0 {-2 * r:.2f} 0')
    s = ['<g id="地形-点阵">']
    for (r, c), P in sorted(T.items()):
        s.append(f'<path id="点阵-{"ABCD"[r]}{c + 1}" d="{"".join(P)}" fill="{color}" fill-opacity=".5"/>')
    return ''.join(s) + '</g>'

def shade(op):
    return f'<image id="地形-晕渲" x="0" y="0" width="1000" height="1000" opacity="{op}" preserveAspectRatio="none" href="{S.raster("soft", S.pix_soft)}"/>'

# ----------------------------------------------------------------------------- build
def svg(key, name, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SZ}" height="{SZ}" viewBox="0 0 {SZ} {SZ}">'
            f'<g id="地图 {key} {name}"><rect id="底色" width="{SZ}" height="{SZ}" fill="{PAPER}"/>{body}</g></svg>')

MAPS = {
    'M3': ('线稿', lambda: shade(.22) + contours((.3, .3, INK), (.62, .62, INK)) + water('#e4edf2', '#5f87a0', '#5f87a0', 1.1, True)
           + roads('double') + houses_rect() + labels()),
    'M4': ('点阵', lambda: dots() + contours((.3, 0, INK), (.4, .14, INK)) + water('#dce8ef', 'none', '#3f7fa6', 1.3)
           + roads('hair') + houses_grid() + labels()),
    'M6': ('点阵晕渲', lambda: shade(1) + contours((.28, .1, '#4a443d'), (.5, .22, '#4a443d')) + water('#d6e3eb', '#7d9db0', '#5f87a0', 1.1)
           + roads('white') + houses_grid(2.5, 1.9, '#5f5a53', (.7, .28)) + labels()),
}

if __name__ == '__main__':
    for key, (name, build) in MAPS.items():
        s = svg(key, name, build()); p = os.path.join(OUT, f'{key} {name}.svg')
        open(p, 'w', encoding='utf-8').write(s)
        print(os.path.basename(p), f'{len(s) // 1024} KB', 'layers≈', s.count('<path') + s.count('<rect') + s.count('<text'))
    print('片区', [(n, len(g)) for n, g in CL])
