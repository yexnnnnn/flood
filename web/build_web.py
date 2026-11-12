#!/usr/bin/env python3
"""村庄自然征兆预警 · 交互原型 -> web/index.html

The user's model: proverbs (A 云层 / B 天色 / C 河流山谷) are the inputs of a four-level warning
(蓝 / 黄 / 橙 / 红) with OR / AND / TIME rules. The page lets you mark what you observe (or play a storm
scenario); the level is computed live and the map shows where each sign is watched, coloured by the level
it triggers. Static cartography (contours, water, roads, houses, labels) is precomputed here; the hillshade
is rendered in the browser from the embedded DEM.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'card'))
import build_card as B          # DEM, roads, gullies, river, 701 houses (incl. east bank)
import build_card3 as C         # peak picking

G, N, HALF, ELEV = B.G, B.N, B.HALF, B.ELEV
V = 1000 / (2 * HALF)                                   # viewBox units per metre
X = lambda x: (x + HALF) * V
Y = lambda z: (z + HALF) * V
f1 = lambda v: f'{v:.1f}'.rstrip('0').rstrip('.')
def pts_d(pts, close=False): return 'M' + ' '.join(f'{f1(X(x))} {f1(Y(z))}' for x, z in pts) + (' Z' if close else '')
def chaikin(P, n):
    for _ in range(n):
        q = [P[0]]
        for a, b in zip(P, P[1:]): q += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        q.append(P[-1]); P = q
    return P

# ----------------------------------------------------------------- contours (Catmull-Rom x2, marching squares)
def upsample(E, n, f):
    m = n * f; out = [0.0] * (m * m); idx = lambda a: min(n - 1, max(0, a))
    def w(t):
        t2, t3 = t * t, t * t * t
        return (-.5 * t3 + t2 - .5 * t, 1.5 * t3 - 2.5 * t2 + 1, -1.5 * t3 + 2 * t2 + .5 * t, .5 * t3 - .5 * t2)
    for j in range(m):
        gz = (j + .5) / f - .5; j0 = math.floor(gz); wz = w(gz - j0); rows = [idx(j0 - 1 + k) * n for k in range(4)]
        for i in range(m):
            gx = (i + .5) / f - .5; i0 = math.floor(gx); wx = w(gx - i0); c = [idx(i0 - 1 + k) for k in range(4)]
            v = 0.0
            for a in range(4):
                r = rows[a]; v += wz[a] * (wx[0] * E[r + c[0]] + wx[1] * E[r + c[1]] + wx[2] * E[r + c[2]] + wx[3] * E[r + c[3]])
            out[j * m + i] = v
    return out, m

def rdp(P, eps):
    if len(P) < 3: return P
    keep = [False] * len(P); keep[0] = keep[-1] = True; st = [(0, len(P) - 1)]
    while st:
        a, b = st.pop(); ax, ay = P[a]; bx, by = P[b]; dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy) or 1e-9; best, bi = 0, -1
        for k in range(a + 1, b):
            d = abs((P[k][0] - ax) * dy - (P[k][1] - ay) * dx) / L
            if d > best: best, bi = d, k
        if best > eps: keep[bi] = True; st += [(a, bi), (bi, b)]
    return [p for p, k in zip(P, keep) if k]

def contours(step=10):
    U, m = upsample(ELEV, N, 2); cs = 2 * HALF / m
    px = lambda i: -HALF + (i + .5) * cs
    lo, hi = min(U), max(U); levels = list(range(int(lo // step + 1) * step, int(hi) + 1, step))
    segs = {lv: [] for lv in levels}
    for j in range(m - 1):
        for i in range(m - 1):
            a, b, c, d = U[j * m + i], U[j * m + i + 1], U[(j + 1) * m + i + 1], U[(j + 1) * m + i]
            mn, mx = min(a, b, c, d), max(a, b, c, d)
            if mx - mn < 1e-9: continue
            e_top, e_right, e_bot, e_left = (j * m + i) * 2, (j * m + i + 1) * 2 + 1, ((j + 1) * m + i) * 2, (j * m + i) * 2 + 1
            for lv in range(int(mn // step + 1) * step, int(mx) + 1, step):
                if lv not in segs: continue
                sa, sb, sc, sd = a >= lv, b >= lv, c >= lv, d >= lv
                cr = []
                def ip(p, q, vp, vq): t = (lv - vp) / (vq - vp); return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
                PA, PB, PC, PD = (px(i), px(j)), (px(i + 1), px(j)), (px(i + 1), px(j + 1)), (px(i), px(j + 1))
                if sa != sb: cr.append((e_top, ip(PA, PB, a, b)))
                if sb != sc: cr.append((e_right, ip(PB, PC, b, c)))
                if sc != sd: cr.append((e_bot, ip(PC, PD, c, d)))
                if sd != sa: cr.append((e_left, ip(PD, PA, d, a)))
                if len(cr) == 2: segs[lv].append((cr[0], cr[1]))
                elif len(cr) == 4:
                    if ((a + b + c + d) / 4 >= lv) == sa: segs[lv] += [(cr[0], cr[1]), (cr[2], cr[3])]
                    else: segs[lv] += [(cr[3], cr[0]), (cr[1], cr[2])]
    out = []
    for lv, S in segs.items():
        if not S: continue
        adj, pos = {}, {}
        for (ea, pa), (eb, pb) in S:
            adj.setdefault(ea, []).append(eb); adj.setdefault(eb, []).append(ea); pos[ea] = pa; pos[eb] = pb
        seen = set(); lines = []
        starts = [e for e, v in adj.items() if len(v) == 1] + list(adj)
        for s0 in starts:
            if s0 in seen: continue
            line = [s0]; seen.add(s0); cur = s0
            while True:
                nxt = [e for e in adj[cur] if e not in seen]
                if not nxt: break
                cur = nxt[0]; seen.add(cur); line.append(cur)
            if len(line) >= 3:
                P = rdp([(X(pos[e][0]), Y(pos[e][1])) for e in line], .28)
                lines.append('M' + ' '.join(f'{x:.1f} {y:.1f}' for x, y in P))
        out.append((lv, ''.join(lines)))
    return out

# ----------------------------------------------------------------- riverbed (DEM low-flow surface of the Juma)
RIV = G['river']
lo = []
for p in RIV:
    m_ = 1e9
    for k in range(N * N):
        if math.hypot(B.cx(k % N) - p[0], B.cx(k // N) - p[1]) < 60: m_ = min(m_, ELEV[k])
    lo.append(m_)
ok = [v < 1e8 for v in lo]; first, last = ok.index(True), len(ok) - 1 - ok[::-1].index(True)
lo = [lo[first] if k < first else lo[last] if k > last else v for k, v in enumerate(lo)]
for k in range(1, len(lo)): lo[k] = min(lo[k], lo[k - 1])
def river_surf(x, z):
    best, val = 1e9, 0
    for k in range(1, len(RIV)):
        a, b = RIV[k - 1], RIV[k]; dx, dz = b[0] - a[0], b[1] - a[1]; L = dx * dx + dz * dz or 1; t = max(0, min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / L))
        d = math.hypot(x - a[0] - dx * t, z - a[1] - dz * t)
        if d < best: best, val = d, lo[k - 1] + (lo[k] - lo[k - 1]) * t
    return best, val
BED = []
for k in range(N * N):
    d, s = river_surf(B.cx(k % N), B.cx(k // N))
    BED.append(round((s + 1.2) * 10) if d < 280 else -1)    # decimetres; cells below this are riverbed

# ----------------------------------------------------------------- OSM extras
gj = json.load(open(os.path.join(HERE, '..', 'shenjia_an_4km_osm.geojson'), encoding='utf-8'))
lon0, lat0 = G['center']; KX, KY = 85780.96, 110540.0
mxz = lambda c: ((c[0] - lon0) * KX, -(c[1] - lat0) * KY)
WATER, DITCH, RES = [], [], []
for f in gj['features']:
    p, g = f['properties'], f['geometry']
    if p.get('natural') == 'water' and g['type'] == 'Polygon': WATER.append(pts_d([mxz(c) for c in g['coordinates'][0]], True))
    elif p.get('waterway') == 'ditch' and g['type'] == 'LineString': DITCH.append(pts_d(chaikin([mxz(c) for c in g['coordinates']], 2)))
    elif p.get('landuse') == 'residential' and p.get('name') and g['type'] == 'Polygon':
        ring = [mxz(c) for c in g['coordinates'][0]]
        if all(abs(x) < HALF and abs(z) < HALF for x, z in ring):
            RES.append((p['name'], pts_d(ring, True), sum(x for x, _ in ring) / len(ring), sum(z for _, z in ring) / len(ring), max(z for _, z in ring)))

# ----------------------------------------------------------------- where each sign is watched
EXT = (-HALF, HALF, -HALF, HALF)
gs = G['gullies']; MAIN = gs[0]
VILLAGE = (-45.5, -98.2)
pk = C.peaks(8, EXT, sep=420, margin=150)
SKY = {}
rest = list(pk)
take = lambda fn: rest.pop(rest.index(fn(rest)))
SKY['01'] = take(lambda r: max(r))                       # cloud cap: the highest summit
SKY['07'] = take(lambda r: max(r, key=lambda p: p[1]))   # morning glow: eastern skyline
SKY['08'] = take(lambda r: min(r, key=lambda p: p[1]))   # sunset cloud: western skyline
def hi_in(fx):   # highest DEM cell satisfying fx(x, z)
    best = max((ELEV[k], B.cx(k % N), B.cx(k // N)) for k in range(N * N) if fx(B.cx(k % N), B.cx(k // N)))
    return best
SKY['10'] = hi_in(lambda x, z: x < -500 and z < -500 and x > -1050 and z > -1050)              # distant thunder: north-west mountains
for sid in ['03', '02', '05']:
    rest = [p for p in rest if math.hypot(p[1] - SKY['10'][1], p[2] - SKY['10'][2]) > 300]
    if rest: SKY[sid] = rest.pop(0)
    else: SKY[sid] = hi_in(lambda x, z, s=sid: abs(x) < 1000 and abs(z) < 1000 and all(math.hypot(x - v[1], z - v[2]) > 450 for v in SKY.values()))
SKY['04'] = (None, VILLAGE[0] + 120, -720)                                                     # clouds crossing: over the valley
def slope(k):
    i, j = k % N, k // N
    if not (0 < i < N - 1 and 0 < j < N - 1): return 0
    return math.hypot(ELEV[k + 1] - ELEV[k - 1], ELEV[k + N] - ELEV[k - N]) / (2 * B.CELL)
old = [h for h in B.HOUSES if not h['east']][::6]
cand = []
for k in range(N * N):
    x, z = B.cx(k % N), B.cx(k // N)
    dmin = min(math.hypot(x - h['x'], z - h['z']) for h in old)
    if 90 < dmin < 260 and -700 < x < 60 and abs(z - VILLAGE[1]) < 600: cand.append((slope(k), x, z))
SLOPE15 = max(cand)[1:]
P = MAIN['path']; L = len(P)
SIG_POS = {k: ('pt', v[1], v[2], round(v[0]) if v[0] else None) for k, v in SKY.items()}
SIG_POS['09'] = ('pt', VILLAGE[0] + 40, VILLAGE[1] + 30, None)
SIG_POS['06'] = ('veil', 0, 0, None)
SIG_POS['11'] = ('pt', *MAIN['outlet'], None)
SIG_POS['12'] = ('pt', *gs[1]['outlet'], None)
SIG_POS['13'] = ('pt', *P[int(L * .62)], None)
SIG_POS['15'] = ('pt', *SLOPE15, None)
REACH14 = chaikin(P[int(L * .18): int(L * .6) + 1], 2)
REACH_SURGE = chaikin(P[int(L * .6):] + MAIN.get('run', []), 2)
SIG_POS['14'] = ('reach', *P[int(L * .4)], None)
SIG_POS['quake'] = ('ring', *VILLAGE, None)

SIGNALS = {
    '01': dict(g='A', s='有雨山戴帽', f='有雨山戴帽，无雨云拦腰', why='山顶被云层覆盖，可能意味着山地附近水汽较多；需要观察云层是否继续降低、加厚。', src='中国天气网；水利部山洪防御科普资料', at='最高的山头'),
    '02': dict(g='A', s='天上钩钩云', f='天上钩钩云，地下雨淋淋', why='钩卷云可能出现在暖锋、低压系统前方，天气可能向阴雨发展。', src='中国天气网湖北站；广东省气象局', at='高空，西南方向的山脊上方'),
    '03': dict(g='A', s='清早宝塔云', f='清早宝塔云，下午雨倾盆', why='暖季早晨出现堡状高积云，说明中层空气可能不稳定；低层对流继续发展，可能形成雷雨。', src='中国科学院科普（采访气象专家）', at='清晨，山脊上空'),
    '04': dict(g='A', s='云交云', f='云交云，雨淋淋', why='不同高度云层移动方向不一致，可能反映不同高度风向变化，常见于锋面或低压附近。', src='中国天气网湖北站', at='山谷上空'),
    '05': dict(g='A', s='棉花云', f='棉花云，雨快临', why='絮状高积云出现时，中层大气可能不稳定；水汽充足且有上升气流时，可能发展为雷雨。', src='中国天气网', at='山脊上空'),
    '06': dict(g='A', s='天上灰布悬', f='天上灰布悬，雨丝定连绵', why='灰布状云对应较厚的雨层云，可能带来范围较大、持续时间较长的降水。', src='中国天气网', at='满天'),
    '07': dict(g='B', s='朝霞不出门', f='朝霞不出门，晚霞行千里', why='早霞可能反映西方云系或水汽条件；需要结合云层移动方向和天气系统判断。', src='中国科学院科普（采访气象专家）', at='清晨，东边的天际线'),
    '08': dict(g='B', s='乌云接落日', f='乌云接落日，不落今日落明日', why='西方云层遮住落日，可能表示降雨系统正在接近，但要结合云层形态和移动判断。', src='中国天气网天津站', at='傍晚，西边的天际线'),
    '09': dict(g='B', s='闷极生雨', f='热极生风，闷极生雨', why='持续闷热可能伴随水汽充足和大气不稳定，但单独的闷热不能作为强降雨判断条件。', src='中国天气网天津站', at='村里'),
    '10': dict(g='B', s='夜里闷雷', f='炎热的夜晚，沉闷雷声忽东忽西', why='山区夜间听到远处持续的沉闷雷声，可能意味着附近存在强对流天气，需要警惕夜间降雨。', src='水利部资料（中国天气网转引）', at='夜里，远处的山'),
    '11': dict(g='C', s='清水忽变黄', f='清水忽变黄，山洪在上方', why='河水突然由清变浑，可能意味着上游降雨、侵蚀或泥沙正在进入河道。', src='重庆市应急管理局 · 项目整理的易记表达', at='杜龙沟出沟口，进村的地方'),
    '12': dict(g='C', s='溪水突然涨', f='溪水突然涨，树枝顺水淌', why='水流突然增大，并夹带柴草、树木，可能是上游洪水或泥石流正在向下游移动。', src='国家应急广播 · 项目整理的易记表达', at='东侧沟口'),
    '13': dict(g='C', s='溪水突然断', f='溪水突然断，山沟莫久看', why='溪流突然断流或水位骤降，可能是上游崩塌堵塞河道；后续可能发生堵塞体溃决。', src='国家应急广播 · 项目整理的易记表达', at='杜龙沟中段'),
    '14': dict(g='C', s='山洪响', f='山洪响，河水涨', why='山谷突然传来不同于风雨雷电的轰鸣、巨石撞击声，可能是洪流或泥石流正在形成或逼近。', src='国家应急广播 · 项目整理的易记表达', at='杜龙沟上游沟谷'),
    '15': dict(g='C', s='山坡裂缝增', f='山坡裂缝增，落石声不断', why='新裂缝扩大、坡面掉土掉石、异常渗水，可能提示滑坡或崩塌风险。', src='应急部门地灾前兆资料 · 项目整理的易记表达', at='村旁最陡的坡'),
    'thick': dict(g='D', s='云层逐渐加厚', f='云层逐渐加厚、降低', why='单一云象在持续增强：与钩钩云组合时升到黄色。', src='规则：时间连续性', at='—'),
    'surge': dict(g='D', s='断流后又暴涨', f='河水突然断流后异常暴涨', why='堵塞体可能已经溃决，洪流正在下来。', src='国家应急广播', at='杜龙沟下游到村里'),
    'debris': dict(g='D', s='裹着石块树木', f='水流急速上涨，裹挟大量泥沙、石块和树木', why='泥石流或山洪已经到达。', src='国家应急广播', at='杜龙沟下游到村里'),
    'quake': dict(g='D', s='地面在抖', f='明显地面震动，伴随沟谷异常变化', why='大规模泥石流或崩塌正在发生。', src='重庆市应急管理局', at='村里'),
}
for k, v in SIGNALS.items():
    pos = SIG_POS.get(k)
    v['id'] = k
    if pos: v['type'], v['x'], v['y'], v['h'] = pos[0], X(pos[1]), Y(pos[2]), pos[3]
    else: v['type'] = 'none'

RULES = [
    dict(lv=1, ids=['01']), dict(lv=1, ids=['02']), dict(lv=1, ids=['05']), dict(lv=1, ids=['07']),
    dict(lv=2, ids=['03', '09']), dict(lv=2, ids=['02', 'thick']), dict(lv=2, ids=['04', '06']), dict(lv=2, ids=['10']),
    dict(lv=3, ids=['11']), dict(lv=3, ids=['12']), dict(lv=3, ids=['13']), dict(lv=3, ids=['15']),
    dict(lv=4, ids=['14']), dict(lv=4, ids=['13', 'surge']), dict(lv=4, ids=['debris']), dict(lv=4, ids=['quake']),
]
SCENARIO = [(0.2, '07', '第1天 06:10'), (1.7, '03', '07:40'), (7.5, '09', '13:30'), (10, '01', '16:00'), (10.4, '02', '16:20'),
            (12, 'thick', '18:00'), (16.7, '10', '22:40'), (21, '06', '第2天 03:00'), (23.5, '04', '05:30'), (27.2, '11', '09:10'),
            (28.3, '12', '10:20'), (30.8, '13', '12:50'), (31.1, 'surge', '13:05'), (31.15, '14', '13:08'), (31.2, 'debris', '13:10')]

# ----------------------------------------------------------------- static SVG
SANS = "'PingFang SC','Noto Sans SC','Source Han Sans SC','Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','SF Mono',ui-monospace,Menlo,Consolas,monospace"
def T(x, y, s, size, fill='#1a1a1a', fam=SANS, w=400, anchor='start', ls=0, op=1, extra=''):
    return (f'<text x="{f1(x)}" y="{f1(y)}" font-family="{fam}" font-size="{size}" font-weight="{w}" fill="{fill}" fill-opacity="{op}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}" paint-order="stroke" stroke="#f5f3ef" stroke-width="3" stroke-linejoin="round" {extra}>{s}</text>')

def build_svg():
    s = []
    s.append('''<defs>
<clipPath id="frame"><rect x="0" y="0" width="1000" height="1000"/></clipPath>
<filter id="blurL" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="blurS" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3"/></filter>''')
    for k, (core, mid, halo) in {'l1': ('#eef3ff', '#2f6bff', '#8fb3ff'), 'l2': ('#fffbe6', '#ffb800', '#ffdd55'), 'l3': ('#fff0e6', '#ff5a0a', '#ffb489'),
                                 'l4': ('#fff0f4', '#ff1450', '#ff92b2'), 'aux': ('#f6f4fb', '#9b93bd', '#d4cfe6')}.items():
        s.append(f'<radialGradient id="{k}"><stop offset="0" stop-color="{core}"/><stop offset=".14" stop-color="{mid}" stop-opacity=".95"/>'
                 f'<stop offset=".42" stop-color="{mid}" stop-opacity=".5"/><stop offset=".72" stop-color="{halo}" stop-opacity=".2"/><stop offset="1" stop-color="{halo}" stop-opacity="0"/></radialGradient>')
        s.append(f'<linearGradient id="v{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{mid}" stop-opacity=".30"/><stop offset=".16" stop-color="{halo}" stop-opacity=".16"/><stop offset=".42" stop-color="{halo}" stop-opacity="0"/></linearGradient>')
    s.append('</defs>')
    s.append('<g clip-path="url(#frame)">')
    s.append('<rect width="1000" height="1000" fill="#f5f3ef"/>')
    s.append('<image id="hs" x="0" y="0" width="1000" height="1000" preserveAspectRatio="none" class="L L1"/>')
    # contours
    s.append('<g class="L L2" fill="none" stroke="#3a3530">')
    for lv, d in contours(10):
        idx = lv % 50 == 0
        s.append(f'<path d="{d}" stroke-width="{.55 if idx else .3}" stroke-opacity="{.30 if idx else .14}"/>')
    s.append('</g>')
    # water
    s.append('<g class="L L3">')
    for d in WATER: s.append(f'<path d="{d}" fill="#d5e2ea" stroke="#7d9db0" stroke-width=".4"/>')
    for d in DITCH: s.append(f'<path d="{d}" fill="none" stroke="#6f93a8" stroke-width=".5" stroke-opacity=".7"/>')
    for g in gs:
        pts = chaikin(g['path'] + g.get('run', []), 2); n = len(pts)
        for a in range(0, n - 1, max(1, n // 6)):
            seg = pts[a: a + n // 6 + 2]; w = .5 + 1.3 * a / n
            s.append(f'<path d="{pts_d(seg)}" fill="none" stroke="#5f87a0" stroke-width="{w:.2f}" stroke-linecap="round" stroke-opacity=".8"/>')
    s.append(f'<path d="{pts_d(chaikin(RIV, 3))}" fill="none" stroke="#5f87a0" stroke-width="1.1" stroke-opacity=".75"/>')
    s.append('</g>')
    # roads (casing + fill)
    RW = {'main': 2.9, 'lane': 1.7, 'track': 1.0, 'path': .6}
    s.append('<g class="L L4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    for r in G['roads']:
        if r['k'] in ('main', 'lane'):
            w = RW[r['k']]; d = pts_d(chaikin(r['p'], 1))
            s.append(f'<path d="{d}" stroke="#b9b2a7" stroke-width="{w + 1.1:.2f}"/>')
    for r in G['roads']:
        d = pts_d(chaikin(r['p'], 1)) if r['k'] in ('main', 'lane') else pts_d(r['p'])
        if r['k'] in ('main', 'lane'): s.append(f'<path d="{d}" stroke="#ffffff" stroke-width="{RW[r["k"]]}"/>')
        elif r['k'] == 'track': s.append(f'<path d="{d}" stroke="#8f877c" stroke-width=".7" stroke-dasharray="3 2"/>')
        else: s.append(f'<path d="{d}" stroke="#8f877c" stroke-width=".55" stroke-dasharray=".2 2.2"/>')
    s.append('</g>')
    # residential outlines
    s.append('<g class="L L4" fill="none" stroke="#1a1a1a" stroke-width=".45" stroke-opacity=".35" stroke-dasharray="1.5 2">')
    for name, d, *_ in RES: s.append(f'<path d="{d}"/>')
    s.append('</g>')
    # glows (dynamic)
    s.append('<g id="glows">')
    for k, v in SIGNALS.items():
        t = v['type']
        if t == 'pt':
            r = 78 if v['g'] in 'AB' else 58
            s.append(f'<g class="glow" id="g-{k}"><circle class="breath" cx="{f1(v["x"])}" cy="{f1(v["y"])}" r="{r}" fill="url(#aux)"/></g>')
        elif t == 'veil':
            s.append(f'<g class="glow veil" id="g-{k}"><rect x="0" y="0" width="1000" height="1000" fill="url(#vaux)"/></g>')
        elif t == 'reach':
            d = pts_d(REACH14)
            s.append(f'<g class="glow reach" id="g-{k}"><path d="{d}" class="rw" stroke-width="44" filter="url(#blurL)"/><path d="{d}" class="rm" stroke-width="12" filter="url(#blurS)"/>'
                     f'<path d="{d}" class="rc" stroke-width="2.4"/><path d="{d}" class="flow" stroke-width="2.4"/></g>')
        elif t == 'ring':
            s.append(f'<g class="glow ring" id="g-{k}">' + ''.join(f'<circle class="rip r{i}" cx="{f1(v["x"])}" cy="{f1(v["y"])}" r="70" fill="none" stroke-width="1.6"/>' for i in range(3)) + '</g>')
    d = pts_d(REACH_SURGE)
    s.append(f'<g class="glow reach" id="g-surge"><path d="{d}" class="rw" stroke-width="54" filter="url(#blurL)"/><path d="{d}" class="rm" stroke-width="14" filter="url(#blurS)"/>'
             f'<path d="{d}" class="rc" stroke-width="2.6"/><path d="{d}" class="flow" stroke-width="2.6"/></g>')
    s.append('</g>')
    # houses
    s.append('<g class="L L5" fill="#1d1b19">')
    for h in B.HOUSES:
        x, y = X(h['x']), Y(h['z']); w, d = max(1.3, h['w'] * V), max(1.0, h['d'] * V)
        s.append(f'<rect x="{x - w / 2:.1f}" y="{y - d / 2:.1f}" width="{w:.1f}" height="{d:.1f}" transform="rotate({h["a"]:.0f} {x:.1f} {y:.1f})"/>')
    s.append('</g>')
    # labels
    s.append('<g class="L L6">')
    k = min(range(1, len(RIV)), key=lambda k: abs(RIV[k][1] - 120) + abs(RIV[k][0] - 360) * .3)
    a, b = RIV[k - 1], RIV[k]; ang = math.degrees(math.atan2(Y(b[1]) - Y(a[1]), X(b[0]) - X(a[0])))
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    mx_, my_ = (X(a[0]) + X(b[0])) / 2 + 24, (Y(a[1]) + Y(b[1])) / 2
    s.append(T(mx_, my_, '拒 马 河', 15, '#4f7690', w=500, anchor='middle', ls=3, extra=f'transform="rotate({ang:.0f} {mx_:.1f} {my_:.1f})"'))
    s.append(T(mx_, my_ + 15, 'JUMA RIVER', 7.5, '#4f7690', MONO, anchor='middle', ls=2, op=.8, extra=f'transform="rotate({ang:.0f} {mx_:.1f} {my_:.1f})"'))
    s.append(T(X(VILLAGE[0]) - 70, Y(VILLAGE[1]) - 92, '沈家庵村', 17, w=700, ls=2))
    s.append(T(X(VILLAGE[0]) - 70, Y(VILLAGE[1]) - 79, 'SHENJIA’AN', 7.5, fam=MONO, ls=2, op=.7))
    s.append(T(X(-815) - 4, Y(5) + 34, '杜龙沟', 13, w=600, ls=2, op=.85))
    for name, d, cx_, cz_, zmax in RES:
        s.append(T(X(cx_), Y(zmax) + 14, name, 9.5, w=500, anchor='middle', ls=1, op=.7))
    s.append('</g>')
    s.append('</g>')   # end clip
    # frame, graticule, scale, north
    s.append('<rect x="0" y="0" width="1000" height="1000" fill="none" stroke="#1a1a1a" stroke-width=".8"/>')
    g = []
    lon_a = math.ceil((lon0 - HALF / KX) / .005) * .005
    lon = lon_a
    while lon < lon0 + HALF / KX:
        x = X((lon - lon0) * KX); g.append(f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="-7" /><line x1="{x:.1f}" y1="1000" x2="{x:.1f}" y2="1007"/>')
        g.append(T(x, -12, f'{lon:.3f}°E', 8, fam=MONO, anchor='middle', op=.6, extra='stroke-width="0"')); lon += .005
    lat = math.floor((lat0 + HALF / KY) / .004) * .004
    while lat > lat0 - HALF / KY:
        y = Y(-(lat - lat0) * KY); g.append(f'<line x1="0" y1="{y:.1f}" x2="-7" y2="{y:.1f}"/><line x1="1000" y1="{y:.1f}" x2="1007" y2="{y:.1f}"/>')
        g.append(T(1012, y + 3, f'{lat:.3f}°N', 8, fam=MONO, op=.6, extra='stroke-width="0"')); lat -= .004
    s.append('<g stroke="#1a1a1a" stroke-width=".7">' + ''.join(g) + '</g>')
    sb = 500 * V
    s.append(f'<g transform="translate(24 968)"><rect x="-8" y="-20" width="{sb + 70:.0f}" height="30" fill="#f5f3ef" fill-opacity=".85"/>'
             f'<path d="M0 -6 V0 H{sb:.1f} V-6 M{sb / 2:.1f} 0 V-4" fill="none" stroke="#1a1a1a" stroke-width=".9"/>'
             + T(0, -10, '0', 8, fam=MONO, anchor='middle', extra='stroke-width="0"') + T(sb, -10, '500 m', 8, fam=MONO, anchor='middle', extra='stroke-width="0"') + '</g>')
    s.append('<g transform="translate(968 36)"><path d="M0 -16 L6 6 L0 2 L-6 6 Z" fill="#1a1a1a"/>' + T(0, 20, 'N', 9, fam=MONO, anchor='middle', extra='stroke-width="0"') + '</g>')
    # markers (dynamic)
    s.append('<g id="markers">')
    for k, v in SIGNALS.items():
        if v['type'] in ('pt', 'reach', 'ring'):
            x, y = v['x'], v['y']
            s.append(f'<g class="mk" id="m-{k}" data-id="{k}"><circle class="hit" cx="{f1(x)}" cy="{f1(y)}" r="16" fill="transparent"/>'
                     f'<circle class="ring" cx="{f1(x)}" cy="{f1(y)}" r="6.5"/><circle class="dot" cx="{f1(x)}" cy="{f1(y)}" r="2.4"/>'
                     + T(x + 10, y - 8, k, 9, fam=MONO, w=500, ls=.5, extra='class="num"')
                     + (T(x + 10, y + 13, f'▲ {v["h"]} m', 7.5, fam=MONO, op=.6, extra='class="ht"') if v.get('h') else '') + '</g>')
    s.append('</g>')
    return ''.join(s)

data = dict(N=N, half=HALF, elev=G['elev'], bed=BED, signals=SIGNALS, rules=RULES, scenario=SCENARIO)
tpl = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
page = tpl.replace('/*%DATA%*/', json.dumps(data, ensure_ascii=False, separators=(',', ':'))).replace('<!--%SVG%-->', build_svg())
open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(page)
print('wrote web/index.html', len(page) // 1024, 'KB · peaks', {k: v[0] for k, v in SKY.items()}, '· slope15', [round(c) for c in SLOPE15])
