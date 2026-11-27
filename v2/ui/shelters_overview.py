#!/usr/bin/env python3
"""01c · Shelters overview: what opens when you tap the tent button on screen 01.
Map + three shelter pins at their real positions, and a frosted bottom sheet ranking them for this user.
Uses route_data.json (OSM roads + 30 m DEM)."""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
R = json.load(open(os.path.join(HERE, 'route_data.json')))
G = json.load(open(os.path.join(ROOT, 'shenjia_an_4km_osm.geojson'), encoding='utf-8'))
S = R['shelters']
W, H = 390, 844
INK, MUTED, BLUE, LIME, ORANGE = '#1E2420', '#6B716C', '#2F5BFF', '#DDF59A', '#FF7A45'
SERIF = "'Roboto Slab', 'Zilla Slab', Georgia, serif"
SANS = "Inter, 'PingFang SC', 'Noto Sans SC', Helvetica, Arial, sans-serif"
f1 = lambda v: f'{v:.1f}'

HOME = R['home']
CLON = (HOME[0] + S['fire']['pt'][0]) / 2 + .0006
CLAT = (HOME[1] + S['fire']['pt'][1]) / 2
PXM, MX, MY = 0.245, 195, 236
def P(q):
    return (MX + (q[0] - CLON) * 111320 * math.cos(math.radians(39.59)) * PXM,
            MY - (q[1] - CLAT) * 110540 * PXM)
pts = lambda r: ' '.join(f'{f1(x)},{f1(y)}' for x, y in map(P, r))
def rings(gm):
    t, c = gm['type'], gm['coordinates']
    return [c] if t == 'LineString' else c if t in ('MultiLineString', 'Polygon') else [r for p in c for r in p] if t == 'MultiPolygon' else []

def T(x, y, s, size=13, weight=400, fill=INK, anchor='start', family=SANS, op=1, ls=0):
    return (f'<text x="{f1(x)}" y="{f1(y)}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'fill-opacity="{op}" text-anchor="{anchor}" letter-spacing="{ls}">{s}</text>')

TENT = ('M26.4,26.9 L69.6,26.9 L87.4,56 L87.4,69.4 Q87.4,71.2 85.6,71.2 L10.3,71.2 Q8.5,71.2 8.5,69.4 L8.5,56 Z '
        'M66.4,37.1 L54.1,56.8 L54.1,67.2 L66.4,67.2 Z M70.4,36 L83.2,56 L83.2,67.2 L70.4,67.2 Z')
def tent(x, y, s, c):          # glyph centred at x,y, s = width in px
    k = s / 96
    return (f'<g transform="translate({f1(x - 48*k)} {f1(y - 49*k)}) scale({k:.4f})">'
            f'<path d="{TENT}" fill="{c}" fill-rule="evenodd" stroke="{c}" stroke-width="3.6" stroke-linejoin="round"/>'
            f'<path d="M3.2,64.8 L26.4,26.9 L69.6,26.9 L92.8,64.8" stroke="{c}" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/></g>')

def map_layer():
    o = ['<g id="地图（可替换为3D地图）">', f'<rect width="{W}" height="{H}" fill="#CFE2AE"/>']
    res, water, small, main = [], [], [], []
    for f in G['features']:
        p, gm = f['properties'], f['geometry']; h = p.get('highway')
        if p.get('landuse') == 'residential': res += [f'<polygon points="{pts(r)}"/>' for r in rings(gm)]
        elif p.get('natural') == 'water': water += [f'<polygon points="{pts(r)}"/>' for r in rings(gm)]
        elif p.get('waterway') == 'river':
            water += [f'<polyline points="{pts(r)}" fill="none" stroke="#7CC3DE" stroke-width="5" stroke-linecap="round"/>' for r in rings(gm)]
        if h in ('secondary', 'tertiary'): main += [f'<polyline points="{pts(r)}"/>' for r in rings(gm)]
        elif h and h != 'construction': small += [f'<polyline points="{pts(r)}"/>' for r in rings(gm)]
    o += ['<g id="居住区" fill="#E5EED3">'] + res + ['</g>', '<g id="河流" fill="#7CC3DE">'] + water + ['</g>',
          '<g id="小路" fill="none" stroke="#fff" stroke-opacity=".8" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">'] + small + ['</g>',
          '<g id="主路" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">'] + main + ['</g>',
          f'<polyline id="推荐路线" points="{pts(S["school"]["path"])}" fill="none" stroke="{BLUE}" stroke-width="3" stroke-dasharray="1 6" stroke-linecap="round" stroke-linejoin="round"/>',
          '</g>']
    return o

def pins():
    hx, hy = P(HOME)
    o = ['<g id="位置点">', '<g id="你的位置">',
         f'<circle cx="{f1(hx)}" cy="{f1(hy)}" r="22" fill="#fff" fill-opacity=".45"/>',
         f'<circle cx="{f1(hx)}" cy="{f1(hy)}" r="8" fill="#fff"/><circle cx="{f1(hx)}" cy="{f1(hy)}" r="4" fill="{INK}"/>',
         T(hx, hy + 38, 'Your location', 11, 500, MUTED, 'middle'), '</g>']
    for key, name, best in (('school', '集贤小学', True), ('fire', '防火站', False), ('village', '村委会', False)):
        x, y = P(S[key]['pt'])
        if best:
            o += [f'<g id="避难点-{name}">', f'<circle cx="{f1(x)}" cy="{f1(y)}" r="30" fill="{BLUE}" fill-opacity=".16"/>',
                  f'<rect x="{f1(x-22)}" y="{f1(y-22)}" width="44" height="44" rx="14" fill="{BLUE}"/>', tent(x, y, 28, '#fff'),
                  f'<rect x="{f1(x-38)}" y="{f1(y+34)}" width="76" height="24" rx="12" fill="#fff" fill-opacity=".88"/>',
                  T(x, y + 50, name, 11, 600, INK, 'middle'), '</g>']
        else:
            o += [f'<g id="避难点-{name}">', f'<rect x="{f1(x-16)}" y="{f1(y-16)}" width="32" height="32" rx="11" fill="#fff" fill-opacity=".9"/>',
                  tent(x, y, 20, '#8A918C'),
                  f'<rect x="{f1(x+21)}" y="{f1(y-11)}" width="56" height="22" rx="11" fill="#fff" fill-opacity=".75"/>',
                  T(x + 49, y + 4, name, 10.5, 500, MUTED, 'middle'), '</g>']
    o.append('</g>')
    return o

def chrome():
    return ['<g id="顶部按钮">',
            '<circle cx="46" cy="76" r="24" fill="#fff" fill-opacity=".35"/><circle cx="46" cy="76" r="7" fill="#3B6CFF"/>',
            '<circle cx="346" cy="76" r="22" fill="#fff" fill-opacity=".55"/>',
            '<path d="M354,76 H339 M345,70 L339,76 L345,82" stroke="#1D1D1D" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
            '</g>']

def row(y, key, name, sub, tag, tag_fill, tag_ink, note, note_ink, best):
    s = S[key]; t = round(s['t0.6'])
    o = [f'<g id="列表-{name}">']
    if best:
        o += [f'<rect x="16" y="{y}" width="{W-32}" height="96" rx="22" fill="#fff" fill-opacity=".92"/>',
              f'<rect x="16.5" y="{y+.5}" width="{W-33}" height="95" rx="21.5" stroke="{BLUE}" stroke-opacity=".35"/>']
    else:
        o += [f'<rect x="16" y="{y}" width="{W-32}" height="80" rx="20" fill="#fff" fill-opacity=".5"/>']
    ic = 44 if best else 36
    o += [f'<rect x="32" y="{y+16}" width="{ic}" height="{ic}" rx="{ic*.32:.0f}" fill="{BLUE if best else "#E8EAE6"}"/>',
          tent(32 + ic / 2, y + 16 + ic / 2, ic * .62, '#fff' if best else '#8A918C')]
    tx = 32 + ic + 14
    o += [T(tx, y + 32, name, 16 if best else 14, 600 if best else 500),
          T(tx, y + 50, sub, 11, 400, MUTED)]
    tw = len(tag) * 6.3 + 18
    o += [f'<rect x="{f1(tx)}" y="{y+(60 if best else 58)}" width="{f1(tw)}" height="20" rx="10" fill="{tag_fill}"/>',
          T(tx + tw / 2, y + (74 if best else 72), tag, 10, 600, tag_ink, 'middle')]
    if note:
        o.append(T(tx + tw + 8, y + (74 if best else 72), note, 10, 500, note_ink))
    o += [T(W - 64 if best else W - 36, y + (44 if best else 40), f'{t}', 26 if best else 20, 500, INK, 'end'),
          T(W - 64 if best else W - 36, y + (62 if best else 56), 'min', 10.5, 400, MUTED, 'end')]
    if best:
        o += [f'<circle cx="{W-40}" cy="{y+48}" r="16" fill="{ORANGE}"/>',
              f'<path d="M{W-46},{y+48} H{W-34} M{W-39},{y+43} L{W-34},{y+48} L{W-39},{y+53}" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>']
    o.append('</g>')
    return o

def sheet():
    y0 = 470
    hr = R['home_river']
    o = ['<g id="底部面板">',
         f'<rect x="0" y="{y0}" width="{W}" height="{H-y0}" rx="30" fill="url(#sheetFill)"/>',
         f'<rect x="0.5" y="{y0+.5}" width="{W-1}" height="{H-y0}" rx="29.5" stroke="#fff" stroke-opacity=".7"/>',
         f'<rect x="175" y="{y0+10}" width="40" height="4" rx="2" fill="{INK}" fill-opacity=".18"/>',
         T(24, y0 + 52, 'Shelters nearby', 26, 300, INK, family=SERIF),
         T(24, y0 + 74, f'Ranked for you · 0.6 m/s with a companion · home is {round(hr)} m from the river', 10.5, 400, MUTED)]
    sc, fi, vi = S['school'], S['fire'], S['village']
    o += row(y0 + 92, 'school', '集贤小学', f'{sc["dist"]/1000:.1f} km · {round(sc["river"])} m from river',
             'Recommended', LIME, INK, 'Farthest from the river', '#3C7A2A', True)
    o += row(y0 + 196, 'fire', '沈家庵防火站', f'{fi["dist"]/1000:.1f} km · {round(fi["river"])} m from river',
             'Backup', '#E8EAE6', MUTED, 'By the river', MUTED, False)
    o += row(y0 + 284, 'village', '沈家庵村委会', f'{vi["dist"]/1000:.1f} km · location to confirm',
             'Not for floods', '#FFE3D6', '#C2471B', f'{round(vi["z"]-R["home_z"])} m below home', '#C2471B', False)
    o += [f'<rect x="135" y="{H-14}" width="120" height="4" rx="2" fill="{INK}" fill-opacity=".8"/>', '</g>']
    return o

DEFS = f'''<defs>
<linearGradient id="sheetFill" x1="0" y1="470" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#F4F6F1" stop-opacity=".82"/><stop offset="1" stop-color="#EEF1EA" stop-opacity=".95"/></linearGradient>
</defs>'''
svg = '\n'.join([f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none">', DEFS,
                 '<g id="01c · 避难点总览">'] + map_layer() + pins() + chrome() + sheet() + ['</g>', '</svg>'])
out = os.path.join(HERE, '01c 避难点总览.svg')
open(out, 'w', encoding='utf-8').write(svg); print('wrote', out, len(svg))
for k in ('school', 'fire', 'village'): print(k, [round(v) for v in P(S[k]['pt'])])
print('home', [round(v) for v in P(HOME)])
