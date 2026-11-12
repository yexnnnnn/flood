#!/usr/bin/env python3
"""Shared design system for v2: content, rules, story steps, map layers (1000-unit SVG), glows.

Used by frames.py (Figma-ready layered SVGs) and build_web.py (the interactive page), so the Figma frames
and the web page are the same drawing.
"""
import os, sys, math, struct, zlib, base64, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'web'))
sys.path.insert(0, os.path.join(HERE, '..', 'card'))
import build_web as BW          # data, contours, signal positions (viewBox units), reaches, OSM extras
import build_card as B

W, H = 1920, 1080
PAPER, INK = '#f5f3ef', '#161514'
SANS = "Noto Sans SC, PingFang SC, Source Han Sans SC, Microsoft YaHei, sans-serif"
MONO = "JetBrains Mono, SF Mono, Menlo, Consolas, monospace"
LV = [
    dict(k='—', no='暂无征兆', name='暂无征兆', mid='#9b93bd', halo='#d4cfe6', core='#f6f4fb', txt='#6b6585', act='在天上、天色和沟里，留意老人说的那些现象。'),
    dict(k='蓝', no='一级', name='天气征兆出现', mid='#2f6bff', halo='#8fb3ff', core='#eef3ff', txt='#2f6bff', act='山地天气可能发生变化，请开始关注云层和天气变化。'),
    dict(k='黄', no='二级', name='降雨风险增加', mid='#ffb800', halo='#ffdd55', core='#fffbe6', txt='#c48a00', act='天气可能向强降雨发展，请准备避险，远离河沟和低洼区域。'),
    dict(k='橙', no='三级', name='上游水情异常', mid='#ff5a0a', halo='#ffb489', core='#fff0e6', txt='#ff5a0a', act='请立即远离河道、沟谷和危险坡体，向安全地点转移。'),
    dict(k='红', no='四级', name='灾害正在发生或迫近', mid='#ff1450', halo='#ff92b2', core='#fff0f4', txt='#ff1450', act='立即向沟谷两侧高处撤离，不要停留观察，不要返回取物。'),
]
SIG, RULES = BW.SIGNALS, BW.RULES
GRP = {'A': '云层', 'B': '天色', 'C': '河流 · 山谷', 'D': '持续 · 增强'}

def evaluate(obs):
    lv, fired = 0, []
    for r in RULES:
        if all(i in obs for i in r['ids']): fired.append(r); lv = max(lv, r['lv'])
    return lv, fired

# story: one sign (or a pair) per step
STEPS = [
    dict(kind='cover'),
    dict(t='第 1 天 · 06:10', add=['07'], focus='07'),
    dict(t='第 1 天 · 07:40', add=['03'], focus='03'),
    dict(t='第 1 天 · 13:30', add=['09'], focus='09'),
    dict(t='第 1 天 · 22:40', add=['10'], focus='10'),
    dict(t='第 2 天 · 03:00', add=['06', '04'], focus='04'),
    dict(t='第 2 天 · 09:10', add=['11'], focus='11'),
    dict(t='第 2 天 · 12:50', add=['13'], focus='13'),
    dict(t='第 2 天 · 13:05', add=['surge', '14'], focus='14'),
    dict(kind='end'),
]
def story_states():
    obs, latched, out = [], 0, []
    for st in STEPS:
        for a in st.get('add', []):
            if a not in obs: obs.append(a)
        lv, fired = evaluate(obs); latched = max(latched, lv)
        out.append(dict(st, obs=list(obs), lv=latched, fired=fired))
    return out

def rule_for(focus, obs):
    """the sentence shown under a proverb: which rule this sign takes part in, and whether it fired"""
    rs = [r for r in RULES if focus in r['ids']]
    if not rs: return None
    fired = [r for r in rs if all(i in obs for i in r['ids'])]
    r = max(fired, key=lambda r: r['lv']) if fired else rs[0]
    return dict(ids=r['ids'], lv=r['lv'], fired=bool(fired), op='OR' if len(r['ids']) == 1 else 'AND')

def wrap(s, n):
    out, line = [], ''
    for ch in s:
        line += ch
        if len(line) >= n and ch in '，。；、：' or len(line) >= n + 3: out.append(line); line = ''
    if line: out.append(line)
    return out

# ----------------------------------------------------------------------------- hillshade PNG (cached)
def png_rgb(w, h, rows):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b'')

def hillshade_uri():
    cache = os.path.join(HERE, '_hillshade.png')
    if not os.path.exists(cache):
        U, m = BW.upsample(BW.ELEV, BW.N, 6)
        cs, zf, N = 2 * BW.HALF / m, 2.2, BW.N
        L = []
        for az, wt in [(315, .55), (260, .25), (10, .2)]:
            a, el = math.radians(az), math.radians(42)
            L.append((math.sin(a) * math.cos(el), -math.cos(a) * math.cos(el), math.sin(el), wt))
        flat = math.sin(math.radians(42)); P, SH, BC = (246, 244, 240), (186, 184, 180), (214, 227, 234)
        rows = []
        for j in range(m):
            r = bytearray(); jm, jp = max(0, j - 1) * m, min(m - 1, j + 1) * m; row = j * m
            for i in range(m):
                dx = (U[row + min(m - 1, i + 1)] - U[row + max(0, i - 1)]) / (2 * cs) * zf
                dy = (U[jp + i] - U[jm + i]) / (2 * cs) * zf
                ln = math.sqrt(dx * dx + dy * dy + 1); nx, ny, nz = -dx / ln, -dy / ln, 1 / ln
                s = 0.0
                for lx, ly, lz, wt in L: s += wt * max(0.0, nx * lx + ny * ly + nz * lz)
                d = max(-1.0, min(1.0, (s - flat) * 2.4)); sl = min(1.0, math.hypot(dx, dy) / zf / 1.1)
                sh = max(0.0, min(1.0, -d * .7 + sl * .08 if d < 0 else sl * .06 - d * .05))
                c = [P[q] + (SH[q] - P[q]) * sh for q in range(3)]
                bi = BW.BED[(j * N // m) * N + (i * N // m)]
                if bi > 0 and U[row + i] < bi / 10:
                    a = min(1.0, (bi / 10 - U[row + i]) / 1.2) * .85; c = [c[q] + (BC[q] - c[q]) * a for q in range(3)]
                r += bytes(int(v) for v in c)
            rows.append(r)
        open(cache, 'wb').write(png_rgb(m, m, rows))
    return 'data:image/png;base64,' + base64.b64encode(open(cache, 'rb').read()).decode()

# ----------------------------------------------------------------------------- map layers (viewBox 0..1000)
def T(x, y, s, size, fill=INK, fam=SANS, w=400, anchor='start', ls=0, op=1, halo=True, extra=''):
    st = f' paint-order="stroke" stroke="{PAPER}" stroke-width="3" stroke-linejoin="round"' if halo else ''
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{w}" fill="{fill}" fill-opacity="{op}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}"{st} {extra}>{s}</text>')

def map_layers(pre='', hs_uri=None):
    X, Y, pts_d, chaikin, G = BW.X, BW.Y, BW.pts_d, BW.chaikin, BW.G
    s = [f'<g id="{pre}地图">', f'<rect id="{pre}纸" width="1000" height="1000" fill="{PAPER}"/>']
    s.append(f'<image id="{pre}地形晕渲" x="0" y="0" width="1000" height="1000" preserveAspectRatio="none" href="{hs_uri or hillshade_uri()}"/>')
    s.append(f'<g id="{pre}等高线" fill="none" stroke="#3a3530">')
    for lv, d in CONTOURS:
        idx = lv % 50 == 0
        s.append(f'<path d="{d}" stroke-width="{.55 if idx else .3}" stroke-opacity="{.28 if idx else .12}"/>')
    s.append('</g>')
    s.append(f'<g id="{pre}水系">')
    for d in BW.WATER: s.append(f'<path d="{d}" fill="#d6e3eb" stroke="#7d9db0" stroke-width=".4"/>')
    for d in BW.DITCH: s.append(f'<path d="{d}" fill="none" stroke="#6f93a8" stroke-width=".5" stroke-opacity=".7"/>')
    for g in BW.gs:
        pts = chaikin(g['path'] + g.get('run', []), 2); n = len(pts)
        for a in range(0, n - 1, max(1, n // 6)):
            s.append(f'<path d="{pts_d(pts[a: a + n // 6 + 2])}" fill="none" stroke="#5f87a0" stroke-width="{.5 + 1.3 * a / n:.2f}" stroke-linecap="round" stroke-opacity=".8"/>')
    s.append(f'<path d="{pts_d(chaikin(BW.RIV, 3))}" fill="none" stroke="#5f87a0" stroke-width="1.1" stroke-opacity=".75"/>')
    s.append('</g>')
    RW = {'main': 2.9, 'lane': 1.7}
    s.append(f'<g id="{pre}道路" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    for r in G['roads']:
        if r['k'] in RW: s.append(f'<path d="{pts_d(chaikin(r["p"], 1))}" stroke="#bdb6ab" stroke-width="{RW[r["k"]] + 1.1:.2f}"/>')
    for r in G['roads']:
        if r['k'] in RW: s.append(f'<path d="{pts_d(chaikin(r["p"], 1))}" stroke="#ffffff" stroke-width="{RW[r["k"]]}"/>')
        elif r['k'] == 'track': s.append(f'<path d="{pts_d(r["p"])}" stroke="#8f877c" stroke-width=".7" stroke-dasharray="3 2"/>')
        else: s.append(f'<path d="{pts_d(r["p"])}" stroke="#8f877c" stroke-width=".55" stroke-dasharray=".2 2.2"/>')
    s.append('</g>')
    s.append(f'<g id="{pre}房屋" fill="#1d1b19">')
    for h in B.HOUSES:
        x, y = X(h['x']), Y(h['z']); w, d = max(1.3, h['w'] * BW.V), max(1.0, h['d'] * BW.V)
        s.append(f'<rect x="{x - w / 2:.1f}" y="{y - d / 2:.1f}" width="{w:.1f}" height="{d:.1f}" transform="rotate({h["a"]:.0f} {x:.1f} {y:.1f})"/>')
    s.append('</g>')
    s.append(f'<g id="{pre}地名">')
    RIV = BW.RIV; k = min(range(1, len(RIV)), key=lambda k: abs(RIV[k][1] - 120) + abs(RIV[k][0] - 360) * .3)
    a, b = RIV[k - 1], RIV[k]; ang = math.degrees(math.atan2(Y(b[1]) - Y(a[1]), X(b[0]) - X(a[0])))
    ang = ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang
    mx, my = (X(a[0]) + X(b[0])) / 2 + 24, (Y(a[1]) + Y(b[1])) / 2
    s.append(T(mx, my, '拒 马 河', 14, '#4f7690', w=500, anchor='middle', ls=3, extra=f'transform="rotate({ang:.0f} {mx:.1f} {my:.1f})"'))
    vx, vy = X(BW.VILLAGE[0]) - 70, Y(BW.VILLAGE[1]) - 92
    s.append(T(vx, vy, '沈家庵村', 16, w=700, ls=2))
    s.append(T(X(-815) - 4, Y(5) + 34, '杜龙沟', 12, w=600, ls=2, op=.85))
    for name, d, cx_, cz_, zmax in BW.RES: s.append(T(X(cx_), Y(zmax) + 14, name, 9, w=500, anchor='middle', ls=1, op=.65))
    s.append('</g>')
    # soft edges: the map dissolves into the paper (no hard frame)
    s.append(f'<g id="{pre}边缘渐隐">'
             f'<rect x="0" y="0" width="140" height="1000" fill="url(#{pre}fadeL)"/><rect x="860" y="0" width="140" height="1000" fill="url(#{pre}fadeR)"/>'
             f'<rect x="0" y="0" width="1000" height="140" fill="url(#{pre}fadeT)"/><rect x="0" y="860" width="1000" height="140" fill="url(#{pre}fadeB)"/></g>')
    s.append('</g>')
    return ''.join(s)

def defs(pre=''):
    s = ['<defs>']
    for nm, (x1, y1, x2, y2) in {'fadeL': (0, 0, 1, 0), 'fadeR': (1, 0, 0, 0), 'fadeT': (0, 0, 0, 1), 'fadeB': (0, 1, 0, 0)}.items():
        s.append(f'<linearGradient id="{pre}{nm}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"><stop offset="0" stop-color="{PAPER}"/><stop offset="{.5 if nm == "fadeB" else 0}" stop-color="{PAPER}"/><stop offset="1" stop-color="{PAPER}" stop-opacity="0"/></linearGradient>')
    for i, L in enumerate(LV):
        s.append(f'<radialGradient id="{pre}g{i}"><stop offset="0" stop-color="{L["core"]}"/><stop offset=".13" stop-color="{L["mid"]}" stop-opacity=".95"/>'
                 f'<stop offset=".4" stop-color="{L["mid"]}" stop-opacity=".5"/><stop offset=".7" stop-color="{L["halo"]}" stop-opacity=".18"/><stop offset="1" stop-color="{L["halo"]}" stop-opacity="0"/></radialGradient>')
        s.append(f'<radialGradient id="{pre}atm{i}"><stop offset="0" stop-color="{L["halo"]}" stop-opacity=".34"/><stop offset=".5" stop-color="{L["halo"]}" stop-opacity=".12"/><stop offset="1" stop-color="{L["halo"]}" stop-opacity="0"/></radialGradient>')
        s.append(f'<radialGradient id="{pre}sky{i}"><stop offset="0" stop-color="{L["mid"]}" stop-opacity=".2"/><stop offset=".55" stop-color="{L["halo"]}" stop-opacity=".1"/><stop offset="1" stop-color="{L["halo"]}" stop-opacity="0"/></radialGradient>')
    s.append('</defs>')
    return ''.join(s)

def glow_svg(pre, sid, lv, r=None, cls=''):
    """one sign's light, in map units. Points: radial gradient. Reaches: stacked strokes (no filters, Figma-safe)."""
    v = SIG[sid]; L = LV[lv]
    if sid in ('14', 'surge'):
        d = BW.pts_d(BW.REACH14 if sid == '14' else BW.REACH_SURGE)
        layers = [(64, L['halo'], .07), (44, L['halo'], .12), (28, L['mid'], .16), (16, L['mid'], .32), (8, L['mid'], .7), (2.6, L['core'], 1)]
        return (f'<g id="{pre}光-{sid}" class="glow reach {cls}" data-id="{sid}">' + ''.join(f'<path d="{d}" fill="none" stroke="{c}" stroke-opacity="{o}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>' for w, c, o in layers)
                + f'<path class="flow" d="{d}" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="3 16"/></g>')
    if v['type'] == 'veil':
        return f'<g id="{pre}光-{sid}" class="glow veil {cls}" data-id="{sid}"><ellipse cx="500" cy="60" rx="620" ry="460" fill="url(#{pre}sky{lv})"/></g>'
    if v['type'] == 'ring':
        return f'<g id="{pre}光-{sid}" class="glow ring {cls}" data-id="{sid}">' + ''.join(f'<circle cx="{v["x"]:.1f}" cy="{v["y"]:.1f}" r="{40 + 25 * i}" fill="none" stroke="{L["mid"]}" stroke-opacity="{.6 - .18 * i}" stroke-width="1.4"/>' for i in range(3)) + '</g>'
    rr = r or (82 if v['g'] in 'AB' else 62)
    return f'<g id="{pre}光-{sid}" class="glow {cls}" data-id="{sid}"><circle cx="{v["x"]:.1f}" cy="{v["y"]:.1f}" r="{rr}" fill="url(#{pre}g{lv})"/></g>'

def marker_svg(pre, sid, on=False, focus=False):
    v = SIG[sid]
    if v['type'] not in ('pt', 'reach', 'ring'): return ''
    x, y = v['x'], v['y']
    return (f'<g id="{pre}标记-{sid}" class="mk" data-id="{sid}"><circle cx="{x:.1f}" cy="{y:.1f}" r="{9 if focus else 6}" fill="{PAPER}" fill-opacity="{0 if on else .7}" stroke="{INK}" stroke-width="{1.3 if focus else .8}" stroke-opacity="{1 if on else .5}"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.3" fill="{INK}"/></g>')

CONTOURS = BW.contours(10)
def sig_level(obs):
    lv, fired = evaluate(obs); out = {}
    for r in fired:
        for i in r['ids']: out[i] = max(out.get(i, 0), r['lv'])
    return out

def short(i): return SIG[i]['s']
def label_of(i): return (i + ' ' if len(i) == 2 else '') + short(i)
