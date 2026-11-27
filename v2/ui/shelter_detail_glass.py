#!/usr/bin/env python3
"""Shelter detail screen (集贤小学) as a Figma-ready layered SVG, 390 wide.
Map, route, elevation profile and comparison use real data from route_data.json."""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
R = json.load(open(os.path.join(HERE, 'route_data.json')))
G = json.load(open(os.path.join(ROOT, 'shenjia_an_4km_osm.geojson'), encoding='utf-8'))
S = R['shelters']; SC = S['school']

W, H = 390, 1236
BLUE, BLUE2 = '#0B2E9E', '#0A2685'
LIME, ORANGE = '#DDF59A', '#FF7A45'
INK = '#23272A'
SERIF = "'Roboto Slab', 'Zilla Slab', Georgia, serif"
SANS = "Inter, 'PingFang SC', 'Noto Sans SC', Helvetica, Arial, sans-serif"
f1 = lambda v: f'{v:.1f}'

# ---------------------------------------------------------------- map projection
HOME, SCH = R['home'], SC['pt']
CLON, CLAT = (HOME[0] + SCH[0]) / 2, (HOME[1] + SCH[1]) / 2
PXM = 0.21                                    # px per metre
MX, MY = 205, 162                             # screen centre of the map
def P(q):
    x = MX + (q[0] - CLON) * 111320 * math.cos(math.radians(39.59)) * PXM
    y = MY - (q[1] - CLAT) * 110540 * PXM
    return x, y
pts = lambda ring: ' '.join(f'{f1(x)},{f1(y)}' for x, y in map(P, ring))

def rings(gm):
    t, c = gm['type'], gm['coordinates']
    return [c] if t == 'LineString' else c if t in ('MultiLineString', 'Polygon') else [r for p in c for r in p] if t == 'MultiPolygon' else []

def map_layer():
    o = ['<g id="地图" clip-path="url(#mapClip)">', f'<rect width="{W}" height="{H}" fill="#D9E8BF"/>']
    res, water, roads, small = [], [], [], []
    for f in G['features']:
        p, gm = f['properties'], f['geometry']
        if p.get('landuse') == 'residential':
            res += [f'<polygon points="{pts(r)}"/>' for r in rings(gm)]
        elif p.get('natural') == 'water':
            water += [f'<polygon points="{pts(r)}"/>' for r in rings(gm)]
        elif p.get('waterway') == 'river':
            water += [f'<polyline points="{pts(r)}" fill="none" stroke="#86CBE6" stroke-width="5" stroke-linecap="round"/>' for r in rings(gm)]
        h = p.get('highway')
        if h in ('secondary', 'tertiary'):
            roads += [f'<polyline points="{pts(r)}"/>' for r in rings(gm)]
        elif h and h != 'construction':
            small += [f'<polyline points="{pts(r)}"/>' for r in rings(gm)]
    o += ['<g id="居住区" fill="#EAF1D8">'] + res + ['</g>']
    o += ['<g id="河流" fill="#86CBE6">'] + water + ['</g>']
    o += ['<g id="小路" fill="none" stroke="#FFFFFF" stroke-opacity=".75" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">'] + small + ['</g>']
    o += ['<g id="主路" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">'] + roads + ['</g>']
    rp = pts(SC['path'])
    o += ['<g id="路线">',
          f'<polyline points="{rp}" fill="none" stroke="{BLUE}" stroke-opacity=".25" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>',
          f'<polyline points="{rp}" fill="none" stroke="{BLUE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>', '</g>']
    # lowest point along the route
    acc, low = 0, None
    path = SC['path']
    for a, b in zip(path, path[1:]):
        seg = math.hypot((a[0]-b[0])*111320*math.cos(math.radians(39.59)), (a[1]-b[1])*110540)
        if acc <= SC['low'][0] <= acc + seg:
            t = (SC['low'][0] - acc) / seg; low = (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
        acc += seg
    lx, ly = P(low)
    hx, hy = P(HOME); sx, sy = P(SCH)
    o += ['<g id="最低点">',
          f'<circle cx="{f1(lx)}" cy="{f1(ly)}" r="9" fill="{ORANGE}" fill-opacity=".25"/>',
          f'<circle cx="{f1(lx)}" cy="{f1(ly)}" r="4.5" fill="{ORANGE}" stroke="#fff" stroke-width="1.5"/>', '</g>',
          '<g id="家">',
          f'<circle cx="{f1(hx)}" cy="{f1(hy)}" r="16" fill="#3B6CFF" fill-opacity=".18"/>',
          f'<circle cx="{f1(hx)}" cy="{f1(hy)}" r="7" fill="#3B6CFF" stroke="#fff" stroke-width="2.5"/>',
          f'<text x="{f1(hx+12)}" y="{f1(hy+4)}" font-family="{SANS}" font-size="11" font-weight="600" fill="#1D2A1A">Home</text>', '</g>',
          '<g id="避难点">',
          f'<path d="M{f1(sx)},{f1(sy)} c-9,-11 -13,-17 -13,-23 a13,13 0 0 1 26,0 c0,6 -4,12 -13,23 Z" fill="{LIME}" stroke="{BLUE}" stroke-width="2"/>',
          f'<circle cx="{f1(sx)}" cy="{f1(sy-23)}" r="4.5" fill="{BLUE}"/>',
          f'<text x="{f1(sx-16)}" y="{f1(sy-42)}" text-anchor="end" font-family="{SANS}" font-size="11" font-weight="600" fill="#1D2A1A">集贤小学</text>', '</g>',
          '</g>']
    # back button like the existing screens
    o += ['<g id="返回">', '<circle cx="356" cy="46" r="20" fill="#FFFFFF" fill-opacity=".55"/>',
          '<path d="M364,46 H349 M355,40 L349,46 L355,52" stroke="#1D1D1D" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>', '</g>']
    return o

def pill(x, y, label, fill=None, dashed=False, color='#1D2A1A', w=None, size=11):
    w = w or (len(label) * size * .58 + 22)
    s = f'<rect x="{f1(x)}" y="{y}" width="{f1(w)}" height="24" rx="12" '
    s += (f'fill="{fill}"/>' if fill else f'fill="none" stroke="{INK}" stroke-opacity=".3" stroke-dasharray="3 3"/>')
    s += f'<text x="{f1(x+w/2)}" y="{y+16}" text-anchor="middle" font-family="{SANS}" font-size="{size}" font-weight="600" fill="{color}">{label}</text>'
    return s, w

def glass(x, y, w, h, op=.12):
    # Figma: add Background blur 24 to this layer
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="#FFFFFF" fill-opacity=".62"/>'
            f'<rect x="{x+.5}" y="{y+.5}" width="{w-1}" height="{h-1}" rx="21.5" stroke="#FFFFFF" stroke-opacity=".95"/>')

def T(x, y, s, size=13, weight=400, fill=INK, op=1, family=SANS, anchor='start', ls=0, id_=None):
    i = f' id="{id_}"' if id_ else ''
    return (f'<text{i} x="{f1(x)}" y="{f1(y)}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" fill-opacity="{op}" text-anchor="{anchor}" letter-spacing="{ls}">{s}</text>')

def sheet():
    o = [f'<g id="内容">', f'<g id="模糊地图" clip-path="url(#sheetClip)" filter="url(#bgBlur)">'] + map_layer() + ['</g>', f'<rect id="面板" x="0" y="270" width="{W}" height="{H-270}" rx="30" fill="url(#sheetFill)"/>', f'<rect x="0.5" y="270.5" width="{W-1}" height="{H-270}" rx="29.5" stroke="#FFFFFF" stroke-opacity=".9"/>']
    # ---- title
    o += ['<g id="标题">', T(24, 316, '集贤小学', 30, 600, family=SERIF, id_='名称'),
          T(24, 340, f'Jixian Primary School · {round(SC["t0.6"])} min · {SC["dist"]/1000:.1f} km · 0 steps', 13, op=.72)]
    p1, w1 = pill(24, 356, 'Recommended', LIME)
    p2, _ = pill(24 + w1 + 8, 356, 'Opening hours: confirm', None, color=INK)
    o += [p1, p2, '</g>']
    # ---- why here: distance-from-river bars
    y0 = 400
    o += ['<g id="为什么选这里">', glass(24, y0, W - 48, 222), T(44, y0 + 34, 'Why here', 18, 500, family=SERIF),
          T(44, y0 + 54, 'Distance from the Juma River · height vs. your home', 11, op=.6)]
    rows = [('集贤小学', SC, True), ('沈家庵防火站', S['fire'], False), ('村中心 · 村委会', S['village'], False)]
    hz = R['home_z']; maxr = 900
    for i, (name, s, best) in enumerate(rows):
        y = y0 + 84 + i * 40
        bw = (W - 48 - 40) * s['river'] / maxr
        dz = s['z'] - hz
        dzs = '±0 m' if abs(dz) < 3 else f'{dz:+.0f} m'
        o += [T(44, y, name, 12, 600 if best else 400, op=1 if best else .75),
              T(W - 44, y, f'{round(s["t0.6"])} min', 12, 600 if best else 400, op=1 if best else .75, anchor='end'),
              f'<rect x="44" y="{y+8}" width="{W-88}" height="6" rx="3" fill="#23272A" fill-opacity=".07"/>',
              f'<rect x="44" y="{y+8}" width="{f1(max(bw, 6))}" height="6" rx="3" fill="{"#B9E35A" if best else "#23272A"}" fill-opacity="{1 if best else .22}"/>',
              T(44 + max(bw, 6) + 6 if bw < 200 else 44 + bw - 6, y + 15, f'{round(s["river"])} m', 9.5, 600,
                fill=INK, op=1 if best else .7, anchor='start' if bw < 200 else 'end'),
              T(W - 44, y + 26, dzs + ' vs home', 9.5, fill='#C2471B' if dz < -3 else INK, op=1 if dz < -3 else .55, anchor='end')]
    o += [T(44, y0 + 204, f'Farthest from the river. Home is only {round(R["home_river"])} m away.', 11, op=.7), '</g>']
    # ---- elevation profile
    y0 = 642
    o += ['<g id="路线剖面">', glass(24, y0, W - 48, 222), T(44, y0 + 34, 'Route profile', 18, 500, family=SERIF)]
    prof = SC['profile']; D = SC['dist']
    zmin, zmax = 112, 142
    cx0, cx1, cy0, cy1 = 60, W - 44, y0 + 64, y0 + 160
    X = lambda m: cx0 + (cx1 - cx0) * m / D
    Y = lambda e: cy1 - (cy1 - cy0) * (e - zmin) / (zmax - zmin)
    step = max(1, len(prof) // 80)
    sp = prof[::step] + [prof[-1]]
    line = ' '.join(f'{f1(X(m))},{f1(Y(e))}' for m, e in sp)
    area = f'M{f1(X(0))},{cy1} L' + line.replace(' ', ' L') + f' L{f1(X(D))},{cy1} Z'
    lm, le = SC['low']
    o += [f'<line x1="{cx0}" y1="{f1(Y(hz))}" x2="{cx1}" y2="{f1(Y(hz))}" stroke="#23272A" stroke-opacity=".25" stroke-dasharray="2 4"/>',
          T(cx1, Y(hz) - 6, f'home level {round(hz)} m', 9.5, op=.55, anchor='end'),
          f'<path d="{area}" fill="url(#profFill)"/>',
          f'<polyline points="{line}" fill="none" stroke="#8FDDB0" stroke-opacity=".55" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/>',
          f'<polyline points="{line}" fill="none" stroke="#2E8B57" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>',
          f'<circle cx="{f1(X(lm))}" cy="{f1(Y(le))}" r="10" fill="{ORANGE}" fill-opacity=".28"/>',
          f'<circle cx="{f1(X(lm))}" cy="{f1(Y(le))}" r="4.5" fill="{ORANGE}" stroke="#fff" stroke-width="1.5"/>',
          T(X(lm), Y(le) + 22, f'{round(le)} m', 10, 600, fill=ORANGE, anchor='middle'),
          T(cx0 - 6, cy1 + 4, f'{zmin}', 9, op=.45, anchor='end'), T(cx0 - 6, cy0 + 4, f'{zmax}', 9, op=.45, anchor='end'),
          T(cx0, cy1 + 18, '0 km', 9, op=.5), T((cx0 + cx1) / 2, cy1 + 18, f'{D/2000:.1f}', 9, op=.5, anchor='middle'),
          T(cx1, cy1 + 18, f'{D/1000:.1f} km', 9, op=.5, anchor='end')]
    pw = W - 88
    o += [f'<rect x="44" y="{y0+196-15}" width="{pw}" height="26" rx="13" fill="{ORANGE}" fill-opacity=".16"/>',
          T(W / 2, y0 + 199, f'Lowest point: {round(hz-le)} m below home. Pass it early.', 11, 600, fill='#C2471B', anchor='middle'),
          '</g>']
    # ---- at the shelter (unconfirmed)
    y0 = 884
    o += ['<g id="避难点设施">', glass(24, y0, W - 48, 222), T(44, y0 + 34, 'At the shelter', 18, 500, family=SERIF)]
    for i, k in enumerate(['Capacity', 'Toilets · water', 'Beds · blankets', 'Step-free entrance']):
        y = y0 + 68 + i * 30
        p, _ = pill(W - 44 - 104, y - 16, 'Not confirmed', None, color=INK, w=104, size=10)
        o += [T(44, y, k, 13, op=.9), p.replace('fill-opacity="1"', '')]
    o += [f'<rect x="44" y="{y0+178}" width="{W-88}" height="30" rx="15" fill="#FFFFFF" fill-opacity=".9"/>',
          T(W / 2, y0 + 198, 'Ask the village committee  →', 12, 600, anchor='middle'), '</g>']
    o += ['<g id="数据来源">', T(W / 2, 1132, 'Route: OpenStreetMap · Elevation: Copernicus 30 m DEM · Times at 0.6 m/s', 9, op=.45, anchor='middle'), '</g>']
    o.append('</g>')
    return o

def cta():
    # fixed bottom button — in Figma, set this group to "Fix position when scrolling"
    return ['<g id="开始路线（固定底部）">',
            f'<rect x="0" y="{H-96}" width="{W}" height="96" fill="url(#ctaFade)"/>',
            f'<rect x="24" y="{H-74}" width="{W-48}" height="54" rx="27" fill="{ORANGE}"/>',
            T(48, H - 41, 'Start route', 17, 600),
            f'<circle cx="{W-51}" cy="{H-47}" r="19" fill="#FFFFFF" fill-opacity=".22"/>',
            f'<path d="M{W-59},{H-47} H{W-43} M{W-49},{H-53} L{W-43},{H-47} L{W-49},{H-41}" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
            '</g>']

DEFS = f'''<defs>
<clipPath id="mapClip"><rect width="{W}" height="{H}"/></clipPath>
<clipPath id="sheetClip"><rect x="0" y="270" width="{W}" height="{H-270}" rx="30"/></clipPath>
<filter id="bgBlur" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="14"/></filter>
<linearGradient id="sheetFill" x1="0" y1="270" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#FBF8F1" stop-opacity=".55"/><stop offset="1" stop-color="#F6F1E6" stop-opacity=".72"/></linearGradient>
<linearGradient id="profFill" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#8FDDB0" stop-opacity=".45"/><stop offset="1" stop-color="#8FDDB0" stop-opacity="0"/></linearGradient>
<linearGradient id="ctaFade" x1="0" y1="{H-96}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#F6F1E6" stop-opacity="0"/><stop offset=".5" stop-color="#F6F1E6" stop-opacity=".9"/></linearGradient>
</defs>'''

svg = '\n'.join([f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none">', DEFS,
                 f'<rect id="背景" width="{W}" height="{H}" fill="#FFFFFF"/>'] + map_layer() + sheet() + cta() + ['</svg>'])
out = os.path.join(HERE, '避难点详情_集贤小学_glass.svg')
open(out, 'w', encoding='utf-8').write(svg)
print('wrote', out, len(svg))
