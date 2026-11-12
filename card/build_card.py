#!/usr/bin/env python3
"""沈家庵村 · 山洪泥石流自然征兆卡 (A5, two sides) -> card/index.html

Style: diffuse gradients (弥散) for "how dangerous", precise hairlines + monospace labels for everything
that must be exact. The back-side map is drawn from the real data in ../shenjia_embed.js
(Copernicus DEM contours, OSM roads, DEM-derived gullies, houses detected in satellite images).
"""
import json, math, heapq, html, os, base64, struct

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', 'shenjia_embed.js'), encoding='utf-8').read()
G = json.loads(src[src.index('{'):src.rindex('}') + 1])

W, H = 1480, 2100            # 0.1 mm units: A5 148 x 210 mm
INK = '#141414'
PAPER = '#f4f2ee'
SANS = '"PingFang SC","Noto Sans SC","Source Han Sans SC","Helvetica Neue",Arial,sans-serif'
MONO = '"JetBrains Mono","SF Mono",ui-monospace,Menlo,Consolas,"PingFang SC",monospace'
esc = html.escape

# --------------------------------------------------------------- content
# t: tag shown in the source pill. "新编" = phrase written for this project (the phenomenon is documented,
# the rhyme is not a verified traditional saying). Rain numbers are illustrative, to be calibrated per gully.
LEVELS = [
    dict(n='留意', en='WATCH', act='抬头看天，收好院里的东西',
         day=[('有雨山戴帽', '山顶罩住云，说明山里水汽重', '中国天气网'),
              ('天上钩钩云', '钩卷云常出现在降雨系统前方', '中国天气网'),
              ('清早宝塔云', '中层空气不稳，午后易起雷雨', '中科院科普')],
         night=[('远处闷雷，忽东忽西', '附近山里有强对流', '水利部资料'),
                ('雨声一直不停', '记下开始下雨的时间', '新编')]),
    dict(n='准备', en='PREPARE', act='证件、药、手电装好；老人孩子先走',
         day=[('天上灰布悬，雨丝定连绵', '厚厚的雨层云，雨会下很久', '中国天气网'),
              ('雨大看不清对面山', '一小时的雨已经很大', '新编'),
              ('雨量桶 ≥ 10 cm，或 1 小时涨 3 cm', '直筒桶放空地，水深就是雨量', '示意值')],
         night=[('闷雷越来越近', '雷雨正向村子移动', '水利部资料'),
                ('雨量桶 1 小时涨 3 cm', '每小时打手电看一次', '示意值')]),
    dict(n='转移', en='MOVE', act='按路线去安置点，不用等通知',
         day=[('清水忽变黄，山洪在上方', '上游已经在冲泥沙', '应急管理局 · 新编'),
              ('溪水突然涨，树枝顺水淌', '上游的洪水下来了', '国家应急广播 · 新编'),
              ('雨量桶 ≥ 20 cm，或 1 小时涨 4 cm', '接近本地泥石流的暴发雨量', '示意值')],
         night=[('溪水声变大、变闷', '水里夹了泥沙和石头', '国家应急广播 · 新编'),
                ('停电断网也要走', '23·7 时很多村子先断了信号', '新编')]),
    dict(n='快跑', en='RUN', act='往沟两侧的高处跑，别顺着沟跑，别回去拿东西',
         day=[('溪水突然断，山沟莫久看', '上游可能被堵住，随时会冲下来', '国家应急广播 · 新编'),
              ('山谷轰隆响，石头撞石头', '泥石流正在下来', '国家应急广播 · 新编'),
              ('山坡裂缝增，落石声不断', '坡体正在变形', '应急管理局 · 新编')],
         night=[('水声突然没了', '断流，比涨水更危险', '国家应急广播 · 新编'),
                ('沟里轰隆、地在抖', '不要出门去看，直接往高处跑', '应急管理局 · 新编')]),
]

# thermal palettes per level: list of (radius factor, colour, opacity) from outside to core
AURA = [
    [(1.0, '#c9d3ff', .55), (.62, '#e3e8ff', .9), (.3, '#f5f3ff', .9)],
    [(1.0, '#ffd6b8', .7), (.7, '#ffe9a8', .8), (.35, '#fff8dc', .9)],
    [(1.0, '#ff9a5c', .75), (.72, '#7fb2ff', .85), (.45, '#ffc7e4', .9), (.22, '#fff27a', 1)],
    [(1.0, '#ff6a3d', .85), (.78, '#ff4fb4', .7), (.58, '#5f9bff', .95), (.36, '#bfe9ff', .9), (.18, '#fff36a', 1)],
]

def aura(cx, cy, r, lv, fid):
    out = [f'<g filter="url(#{fid})">']
    for f, c, o in AURA[lv]:
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * f:.1f}" fill="{c}" fill-opacity="{o}"/>')
    if lv == 3:   # satellite blobs, like a specimen that is spreading
        for a, d, rr in [(0.6, 1.12, .26), (2.2, 1.05, .2), (3.9, 1.18, .22), (5.2, 1.0, .17)]:
            x, y = cx + math.cos(a) * r * d, cy + math.sin(a) * r * d
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * rr:.1f}" fill="#ff7a45" fill-opacity=".8"/>')
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * rr * .5:.1f}" fill="#7fb2ff" fill-opacity=".9"/>')
    out.append('</g>')
    return ''.join(out)

def text(x, y, s, size, weight=400, fill=INK, family=SANS, anchor='start', ls=0, op=1):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{family}\' font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'fill-opacity="{op}" text-anchor="{anchor}" letter-spacing="{ls}">{esc(s)}</text>')

def tag(x, y, s, size=17, fill='#e7f5c4'):   # highlighted monospace label (specimen-label look)
    w = len(s) * size * 0.62 + 18
    for ch in s:
        if ord(ch) > 0x2e80: w += size * 0.38
    return f'<rect x="{x:.1f}" y="{y - size - 6:.1f}" width="{w:.1f}" height="{size + 14:.1f}" fill="{fill}"/>' + text(x + 9, y, s, size, family=MONO, ls=1)

def pill(x, y, s, size=16, anchor='end'):   # hairline source pill
    w = sum(size * (1.0 if ord(c) > 0x2e80 else .62) for c in s) + 18
    x0 = x - w if anchor == 'end' else x
    return (f'<rect x="{x0:.1f}" y="{y - size - 4:.1f}" width="{w:.1f}" height="{size + 11:.1f}" rx="{(size + 11) / 2:.1f}" fill="none" stroke="{INK}" stroke-width="1.2" stroke-opacity=".55"/>'
            + text(x0 + 9, y, s, size, family=MONO, op=.7))

def defs():
    return ('<defs>'
            '<filter id="b1" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="16"/></filter>'
            '<filter id="b2" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="10"/></filter>'
            '<filter id="bm" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="9"/></filter>'
            '<filter id="bw" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="16"/></filter>'
            '<linearGradient id="rain" x1="0" x2="1"><stop offset="0" stop-color="#e3e8ff"/><stop offset=".3" stop-color="#ffe9a8"/>'
            '<stop offset=".62" stop-color="#ff9a5c"/><stop offset=".8" stop-color="#ff4fb4"/><stop offset="1" stop-color="#5f9bff"/></linearGradient>'
            '<marker id="arr" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#141414"/></marker>'
            '</defs>')

def header(side_tag, right, title, sub):
    s = [tag(70, 104, side_tag, 19), tag(70, 140, '4 LEVELS / NOT OFFICIAL', 19, '#f1ece2')]
    s.append(text(1410, 104, right, 19, family=MONO, anchor='end', ls=1.5))
    s.append(text(1410, 136, 'PROJ :: 沈家庵 · 拒马河 · 39.595N 115.679E', 16, family=MONO, anchor='end', ls=1, op=.6))
    s.append(text(66, 300, title, 118, 700, ls=-3))
    s.append(text(70, 362, sub, 30, op=.62))
    return ''.join(s)

def footer(left):
    return (f'<line x1="70" y1="2010" x2="1410" y2="2010" stroke="{INK}" stroke-width="1.2" stroke-opacity=".35"/>'
            + text(70, 2050, left, 16, family=MONO, ls=.8, op=.75)
            + text(1410, 2050, 'Ø 148 × 210 mm · 2026 · v0.1', 16, family=MONO, anchor='end', ls=.8, op=.75))

# --------------------------------------------------------------- front (day)
def front():
    s = [defs(), f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
         header('CARD 01 · 白天 / DAY', '看天 → 看水 → 看山', '看天 看水 看山', '老人说的天象和水情，对应四步行动。看到哪一级，就做哪一级的事。')]
    y0, rh = 410, 322
    for i, L in enumerate(LEVELS):
        y = y0 + i * rh
        cx, cy, r = 215, y + 160, 88 + i * 14
        s.append(aura(cx, cy, r, i, 'b1'))
        s.append(text(cx, cy + 22, L['n'], 66, 700, anchor='middle', ls=2))
        s.append(text(cx, cy + 62, f'LV.{i + 1} / {L["en"]}', 16, family=MONO, anchor='middle', ls=2, op=.7))
        if i: s.append(f'<line x1="70" y1="{y:.0f}" x2="1410" y2="{y:.0f}" stroke="{INK}" stroke-width="1" stroke-opacity=".18"/>')
        s.append(text(420, y + 64, L['act'], 38, 700, ls=-.5))
        for k, (q, ex, src_) in enumerate(L['day']):
            yy = y + 132 + k * 70
            s.append(f'<circle cx="430" cy="{yy - 10}" r="5" fill="none" stroke="{INK}" stroke-width="1.5"/>')
            s.append(text(452, yy, q, 28, 600))
            s.append(text(452, yy + 30, ex, 20, op=.6))
            s.append(pill(1410, yy, src_))
    # rain bucket gauge
    gy = 1830; x0, x1 = 70, 1410; pxcm = (x1 - x0) / 30
    s.append(text(70, gy - 52, '雨量桶', 30, 700))
    s.append(text(186, gy - 52, '直筒桶放在空地上，桶里水深就是雨量：1 cm = 10 mm', 22, op=.62))
    s.append(f'<rect x="{x0}" y="{gy - 6}" width="{x1 - x0}" height="44" fill="url(#rain)" filter="url(#b2)" opacity=".9"/>')
    s.append(f'<rect x="{x0}" y="{gy - 6}" width="{x1 - x0}" height="44" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    for c in range(31):
        h = 16 if c % 5 == 0 else 8
        s.append(f'<line x1="{x0 + c * pxcm:.1f}" y1="{gy + 38}" x2="{x0 + c * pxcm:.1f}" y2="{gy + 38 + h}" stroke="{INK}" stroke-width="1.2"/>')
        if c % 5 == 0: s.append(text(x0 + c * pxcm, gy + 80, f'{c} cm', 16, family=MONO, anchor='middle', op=.7))
    for c, lab in [(10, '准备'), (20, '转移'), (25, '本地泥石流暴发雨量（示意）')]:
        x = x0 + c * pxcm
        s.append(f'<line x1="{x:.1f}" y1="{gy - 22}" x2="{x:.1f}" y2="{gy + 38}" stroke="{INK}" stroke-width="2"/>')
        s.append(tag(x + 8, gy - 12, lab, 16, '#ffffff'))
    s.append(text(70, gy + 128, '还要看快慢：1 小时涨 3 cm → 准备；涨 4 cm → 转移。示意值，需按本沟标定。', 20, op=.7))
    s.append(footer('非官方预警 · 以政府发布为准 · 看到“快跑”信号，不要等任何通知'))
    return f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">{"".join(s)}</svg>'

# --------------------------------------------------------------- map data
N, HALF = G['N'], G['half']; CELL = 2 * HALF / N
elev = struct.unpack(f'<{N * N}H', base64.b64decode(G['elev']))
MX0, MX1, MZ0, MZ1 = -1200, 1200, -720, 713      # map extent (m): x east, z south
MAP = (70, 1165, 1340, 800)                         # x, y, w, h on the card
def P(x, z):
    return MAP[0] + (x - MX0) / (MX1 - MX0) * MAP[2], MAP[1] + (z - MZ0) / (MZ1 - MZ0) * MAP[3]
def path_d(pts):
    q = [P(*p) for p in pts]
    return 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in q)

def contours(step=20):
    out = []
    E = lambda i, j: elev[j * N + i] / 10
    cx = lambda i: -HALF + (i + .5) * CELL
    lo, hi = min(elev) / 10, max(elev) / 10
    for lv in range(int(lo // step + 1) * step, int(hi), step):
        segs = []
        for j in range(N - 1):
            for i in range(N - 1):
                v = [E(i, j), E(i + 1, j), E(i + 1, j + 1), E(i, j + 1)]
                c = [(cx(i), cx(j)), (cx(i + 1), cx(j)), (cx(i + 1), cx(j + 1)), (cx(i), cx(j + 1))]
                pts = []
                for a in range(4):
                    b = (a + 1) % 4
                    if (v[a] < lv) != (v[b] < lv):
                        t = (lv - v[a]) / (v[b] - v[a])
                        pts.append((c[a][0] + (c[b][0] - c[a][0]) * t, c[a][1] + (c[b][1] - c[a][1]) * t))
                for k in range(0, len(pts) - 1, 2):
                    (x0, z0), (x1, z1) = pts[k], pts[k + 1]
                    if MX0 <= x0 <= MX1 and MZ0 <= z0 <= MZ1:
                        a0, b0 = P(x0, z0); a1, b1 = P(x1, z1)
                        segs.append(f'M{a0:.1f} {b0:.1f}L{a1:.1f} {b1:.1f}')
        if segs:
            major = lv % 100 == 0
            out.append(f'<path d="{"".join(segs)}" fill="none" stroke="{INK}" stroke-width="{1.1 if major else .7}" stroke-opacity="{.32 if major else .14}"/>')
    return ''.join(out)

# road graph for the evacuation routes
def routes(start, goals):
    nodes, adj = [], {}
    def nid(p):
        for k, q in enumerate(nodes):
            if abs(q[0] - p[0]) < 4 and abs(q[1] - p[1]) < 4: return k
        nodes.append(p); return len(nodes) - 1
    for r in G['roads']:
        pts = r['p']; prev = None
        for p in pts:
            k = nid(tuple(p))
            if prev is not None and prev != k:
                d = math.dist(nodes[prev], nodes[k]) * (1.3 if r['k'] == 'path' else 1)
                adj.setdefault(prev, []).append((k, d)); adj.setdefault(k, []).append((prev, d))
            prev = k
    near = lambda p: min(range(len(nodes)), key=lambda k: math.dist(nodes[k], p))
    s0 = near(start); dist = {s0: 0}; prev = {}; pq = [(0, s0)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18): continue
        for v, w in adj.get(u, []):
            if d + w < dist.get(v, 1e18): dist[v] = d + w; prev[v] = u; heapq.heappush(pq, (d + w, v))
    out = []
    for g in goals:
        t = min(dist, key=lambda k: math.dist(nodes[k], g) + dist[k] * 0.15)
        p = [g]; k = t
        while k in prev or k == s0:
            p.append(nodes[k])
            if k == s0: break
            k = prev[k]
        p.append(start); p.reverse(); out.append((p, dist[t] + math.dist(nodes[t], g)))
    return out

def mapsvg():
    s = [f'<clipPath id="mc"><rect x="{MAP[0]}" y="{MAP[1]}" width="{MAP[2]}" height="{MAP[3]}"/></clipPath>', '<g clip-path="url(#mc)">']
    s.append(contours())
    # danger: diffuse fields along the Juma and every gully (low ground where water and debris go)
    s.append(f'<g filter="url(#bw)" opacity=".75"><path d="{path_d(G["river"])}" fill="none" stroke="#7fb2ff" stroke-width="95" stroke-linecap="round"/>'
             f'<path d="{path_d(G["river"])}" fill="none" stroke="#c9d3ff" stroke-width="150" stroke-opacity=".6" stroke-linecap="round"/></g>')
    for gi, g in enumerate(G['gullies']):
        pts = g['path'] + g.get('run', [])
        s.append(f'<g filter="url(#bm)"><path d="{path_d(pts)}" fill="none" stroke="#ff9a5c" stroke-width="{46 if gi == 0 else 34}" stroke-opacity=".75" stroke-linecap="round"/>'
                 f'<path d="{path_d(pts)}" fill="none" stroke="#ff4fb4" stroke-width="{16 if gi == 0 else 12}" stroke-opacity=".75" stroke-linecap="round"/></g>')
        ox, oz = g['outlet']
        X, Y = P(ox, oz)
        s.append(f'<g filter="url(#b2)"><circle cx="{X:.1f}" cy="{Y:.1f}" r="{30 if gi == 0 else 20}" fill="#fff36a"/></g>')
    s.append(f'<path d="{path_d(G["river"])}" fill="none" stroke="{INK}" stroke-width="1.4" stroke-dasharray="2 5" stroke-opacity=".7"/>')
    for g in G['gullies']:
        s.append(f'<path d="{path_d(g["path"] + g.get("run", []))}" fill="none" stroke="{INK}" stroke-width="1" stroke-opacity=".55"/>')
    # roads
    RW = {'main': 2.4, 'lane': 1.4, 'track': 1.0, 'path': .7}
    for r in G['roads']:
        dash = ' stroke-dasharray="4 4"' if r['k'] == 'path' else ''
        s.append(f'<path d="{path_d(r["p"])}" fill="none" stroke="{INK}" stroke-width="{RW.get(r["k"], 1)}" stroke-opacity=".8"{dash}/>')
    # houses
    hs = []
    for h in G['houses']:
        x, y = P(h[0], h[1])
        hs.append(f'M{x - 2.2:.1f} {y - 2.2:.1f}h4.4v4.4h-4.4z')
    s.append(f'<path d="{"".join(hs)}" fill="{PAPER}" stroke="{INK}" stroke-width=".9"/>')
    # routes from the village centre to the two shelters (illustrative)
    home = (-60, -60)
    shelters = [((-682, -262), '安置点 A · 西坡台地'), ((-232, 698), '安置点 B · 南坡台地')]
    for (pts, L), (g, lab) in zip(routes(home, [g for g, _ in shelters]), shelters):
        s.append(f'<path d="{path_d(pts)}" fill="none" stroke="#ffffff" stroke-width="9" stroke-linejoin="round" stroke-opacity=".9"/>')
        s.append(f'<path d="{path_d(pts)}" fill="none" stroke="{INK}" stroke-width="3.6" stroke-linejoin="round" marker-end="url(#arr)"/>')
        X, Y = P(*g)
        s.append(f'<g filter="url(#b2)"><circle cx="{X:.1f}" cy="{Y:.1f}" r="34" fill="#cfeec0"/></g>')
        s.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="15" fill="none" stroke="{INK}" stroke-width="2"/><circle cx="{X:.1f}" cy="{Y:.1f}" r="4" fill="{INK}"/>')
        tx, ty = (X + 26, Y - 22) if Y < MAP[1] + MAP[3] - 90 else (X + 30, Y - 64)
        s.append(tag(tx, ty, lab, 17, '#e7f5c4'))
        s.append(text(tx + 6, ty + 30, f'≈ {round(L / 10) * 10:.0f} m · 示意', 15, family=MONO, op=.7))
    X, Y = P(*home)
    s.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="11" fill="{INK}"/><circle cx="{X:.1f}" cy="{Y:.1f}" r="21" fill="none" stroke="{INK}" stroke-width="1.6"/>')
    s.append(tag(X + 28, Y + 6, '你家', 18, '#ffffff'))
    for pl in G['places']:
        if pl['n'] == '杜龙沟':
            x, y = P(pl['x'], pl['z']); s.append(text(x - 60, y - 34, '杜龙沟 ↘', 20, 600))
    rx, ry = P(*G['river'][15])
    s.append(text(rx + 70, ry, '拒马河', 22, 600, op=.8))
    s.append('</g>')
    s.append(f'<rect x="{MAP[0]}" y="{MAP[1]}" width="{MAP[2]}" height="{MAP[3]}" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    # scale + north
    sx, sy = MAP[0] + 20, MAP[1] + MAP[3] - 26; px500 = 500 / (MX1 - MX0) * MAP[2]
    s.append(f'<rect x="{sx - 8}" y="{sy - 28}" width="{px500 + 120}" height="44" fill="{PAPER}" fill-opacity=".85"/>')
    s.append(f'<path d="M{sx} {sy - 6}v10h{px500:.1f}v-10" fill="none" stroke="{INK}" stroke-width="1.4"/>' + text(sx + px500 + 12, sy + 4, '500 m', 15, family=MONO))
    nx, ny = MAP[0] + MAP[2] - 36, MAP[1] + 46
    s.append(f'<path d="M{nx} {ny - 22}l9 26l-9 -6l-9 6z" fill="{INK}"/>' + text(nx, ny + 26, 'N', 15, family=MONO, anchor='middle'))
    return ''.join(s)

# --------------------------------------------------------------- back (night)
def back():
    s = [defs(), f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
         header('CARD 01 · 夜里 / NIGHT', '看不见就听 · 听不清就量', '听声 量雨 认路', '夜里看不到云和水色，就靠耳朵和雨量桶。手电、雨衣放在门口。')]
    y0, rh = 400, 170
    for i, L in enumerate(LEVELS):
        y = y0 + i * rh
        cx, cy, r = 160, y + 84, 54 + i * 8
        s.append(aura(cx, cy, r, i, 'b2'))
        s.append(text(cx, cy + 16, L['n'], 44, 700, anchor='middle', ls=1))
        if i: s.append(f'<line x1="70" y1="{y:.0f}" x2="1410" y2="{y:.0f}" stroke="{INK}" stroke-width="1" stroke-opacity=".18"/>')
        for k, (q, ex, src_) in enumerate(L['night']):
            x = 300 + k * 560
            s.append(text(x, y + 74, q, 30, 600))
            s.append(text(x, y + 108, ex, 20, op=.6))
            s.append(pill(x, y + 146, src_, 15, 'start'))
    s.append(text(70, 1135, '认路', 30, 700))
    s.append(text(150, 1135, '弥散的颜色是低处：沟道和拒马河两侧，水和泥都往这里走。路线避开它们，往两侧的坡上走。', 21, op=.62))
    s.append(mapsvg())
    s.append(text(70, 1996, '地图：Copernicus GLO-30 DEM（等高线 20 m）· OpenStreetMap 道路 · 卫星影像识别的 654 栋房屋 · 路线与安置点为示意，需村委确认', 15, family=MONO, op=.6))
    s.append(footer('口诀标“新编”的：现象有官方资料，句子为本项目新写，不是已查证的老话'))
    return f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">{"".join(s)}</svg>'

page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>沈家庵村 · 山洪泥石流自然征兆卡 · 原型 v0.1</title>
<style>
@page {{ size: 148mm 210mm; margin: 0 }}
html,body {{ margin:0; background:#dedbd5; font-family:{SANS} }}
.wrap {{ display:flex; flex-wrap:wrap; gap:36px; justify-content:center; padding:40px 24px 60px }}
.side {{ width:min(46vw, 620px); aspect-ratio:148/210; box-shadow:0 30px 60px -30px rgba(0,0,0,.35) }}
.side svg {{ width:100%; height:100%; display:block }}
.cap {{ width:100%; text-align:center; font:12px/1.6 {MONO}; letter-spacing:.08em; color:#555 }}
@media (max-width:900px) {{ .side {{ width:92vw }} }}
@media print {{ html,body {{ background:none }} .wrap {{ display:block; padding:0 }} .cap {{ display:none }}
  .side {{ width:148mm; height:210mm; box-shadow:none; break-after:page }} }}
</style></head><body>
<div class="wrap">
<div class="cap">沈家庵村 · 山洪泥石流自然征兆卡 · A5 双面 · 原型 v0.1 · 打印：浏览器“打印”→ 纸张 A5、边距无、勾选“背景图形”</div>
<div class="side">{front()}</div>
<div class="side">{back()}</div>
</div></body></html>'''
open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(page)
print('wrote card/index.html', len(page) // 1024, 'KB')
