#!/usr/bin/env python3
"""M7 写实: the rendered aerial base (real_base.py -> real_render.js) with a light overlay in the
'photoreal map + white UI' style: white hairline roads, white pill labels, round observation nodes,
and warning glows (one group per level, only 四级 visible by default).

Writes v2/figma/地图组件/M7 写实.svg (1000 x 1000, base image embedded) and M7 写实底图.jpg (the raster alone).
Same Figma rules as map_only.py: every piece is its own named layer, no pattern / clipPath / filter.
"""
import os, base64, shutil, math
import map_styles as S
import map_only as MO

D, BW, G = S.D, S.BW, S.G
pts_d, chaikin, X, Y = S.pts_d, S.chaikin, S.X, S.Y
JPG = os.path.join(D.HERE, '_real.jpg')
FIG_JPG = os.path.join(MO.OUT, 'M7 写实底图.jpg')       # committed copy, used when _real.jpg (local render) is absent
BLUR_JPG = os.path.join(MO.OUT, 'M7 背景模糊.jpg')      # blurred, darkened copy for glass backdrops
SZ = 1000
INKG = '#1c261e'          # label text on white pills
FONT = D.SANS

def jpg_uri(p): return 'data:image/jpeg;base64,' + base64.b64encode(open(p, 'rb').read()).decode()

def base():
    uri = jpg_uri(JPG if os.path.exists(JPG) else FIG_JPG)
    return f'<image id="写实底图" x="0" y="0" width="{SZ}" height="{SZ}" preserveAspectRatio="none" href="{uri}"/>'

def vignette():
    return ('<radialGradient id="vig" cx="50%" cy="50%" r="72%"><stop offset=".55" stop-color="#000" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#000" stop-opacity=".38"/></radialGradient>',
            f'<rect id="暗角" width="{SZ}" height="{SZ}" fill="url(#vig)"/>')

def roads():
    W = {'main': (1.1, .92), 'lane': (.6, .72)}
    s = ['<g id="道路-白线"><g id="道路-主路村路">']
    for n, r in enumerate(G['roads']):
        if r['k'] in W:
            w, o = W[r['k']]
            s.append(f'<path id="{MO.NAME[r["k"]]}-{n:03d}" d="{pts_d(chaikin(r["p"], 1))}" fill="none" stroke="#ffffff" stroke-opacity="{o}" '
                     f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append('</g><g id="道路-小径">')
    for n, r in enumerate(G['roads']):
        if r['k'] == 'track':
            s.append(f'<path id="机耕路-{n:03d}" d="{pts_d(r["p"])}" fill="none" stroke="#ffffff" stroke-opacity=".5" stroke-width=".45" stroke-dasharray="2.4 1.8"/>')
    return ''.join(s) + '</g></g>'

def pill(id_, x, y, text, fs=11, w=600, anchor='middle', op=.94, dot=False):
    """white rounded label; x, y = pill centre (anchor middle) or left edge (anchor start)"""
    tw = sum(fs if ord(c) > 255 else fs * .58 for c in text) + (len(text) - 1) * .6
    pw, ph = tw + fs * 1.3 + (fs * .9 if dot else 0), fs * 1.9
    x0 = x - pw / 2 if anchor == 'middle' else x
    tx = x0 + fs * .65 + (fs * .9 if dot else 0)
    s = [f'<g id="{id_}"><rect id="底" x="{x0:.1f}" y="{y - ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="{ph / 2:.1f}" fill="#ffffff" fill-opacity="{op}"/>']
    if dot: s.append(f'<circle id="点" cx="{x0 + fs * .85:.1f}" cy="{y:.1f}" r="{fs * .26:.1f}" fill="{INKG}"/>')
    s.append(f'<text id="字" x="{tx:.1f}" y="{y + fs * .36:.1f}" font-family="{FONT}" font-size="{fs}" font-weight="{w}" fill="{INKG}" letter-spacing=".6">{text}</text></g>')
    return ''.join(s)

def labels():
    RIV = BW.RIV; k = min(range(1, len(RIV)), key=lambda k: abs(RIV[k][1] - 120) + abs(RIV[k][0] - 360) * .3)
    rx, ry = X(RIV[k][0]), Y(RIV[k][1])
    s = ['<g id="地名">',
         pill('地名-沈家庵村', X(BW.VILLAGE[0]) - 40, Y(BW.VILLAGE[1]) - 92, '沈家庵村', 14, 700, dot=True),
         pill('地名-拒马河', rx + 34, ry, '拒马河', 11),
         pill('地名-杜龙沟', X(-815) + 10, Y(5) + 8, '杜龙沟', 11)]
    for name, d, cx_, cz_, zmax in BW.RES: s.append(pill(f'地名-{name}', X(cx_), Y(zmax) + 16, name, 9, 500, op=.85))
    return ''.join(s) + '</g>'

PTS = [(k, v) for k, v in D.SIG.items() if v['type'] == 'pt' and k.isdigit()]

def glow_defs():
    s = []
    for i in range(1, 5):
        L = D.LV[i]
        s.append(f'<radialGradient id="w{i}"><stop offset="0" stop-color="{L["core"]}" stop-opacity=".95"/>'
                 f'<stop offset=".18" stop-color="{L["mid"]}" stop-opacity=".9"/><stop offset=".45" stop-color="{L["mid"]}" stop-opacity=".38"/>'
                 f'<stop offset=".75" stop-color="{L["halo"]}" stop-opacity=".12"/><stop offset="1" stop-color="{L["halo"]}" stop-opacity="0"/></radialGradient>')
    return ''.join(s)

def glows():
    """one group per warning level; on green the colour needs a white edge ring to stay readable"""
    s = ['<g id="预警光晕">']
    for i in range(1, 5):
        L = D.LV[i]; vis = 1 if i == 4 else 0
        s.append(f'<g id="{L["no"]} {L["k"]}" opacity="{vis}">')
        for k, v in PTS:
            s.append(f'<g id="光-{k}"><circle id="光晕" cx="{v["x"]:.1f}" cy="{v["y"]:.1f}" r="{60 if v["g"] in "AB" else 46}" fill="url(#w{i})"/>'
                     f'<circle id="白边" cx="{v["x"]:.1f}" cy="{v["y"]:.1f}" r="11" fill="none" stroke="#ffffff" stroke-width="1.4" stroke-opacity=".9"/></g>')
        s.append('</g>')
    return ''.join(s) + '</g>'

def nodes():
    s = ['<g id="观测点">']
    for k, v in PTS:
        x, y = v['x'], v['y']
        left = x > 860                                   # keep pills inside the frame
        lab = f'{k} {v["s"]}'
        tw = sum(9 if ord(c) > 255 else 5.2 for c in lab) + 12
        px = x - 12 - tw if left else x + 12
        s.append(f'<g id="观测点-{k}"><circle id="外圈" cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="#ffffff" fill-opacity=".28" stroke="#ffffff" stroke-width="1.3"/>'
                 f'<circle id="中心" cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#ffffff"/>'
                 + pill('标签', px, y, lab, 9, 600, anchor='start', op=.9) + '</g>')
    return ''.join(s) + '</g>'

def build():
    vd, vr = vignette()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SZ}" height="{SZ}" viewBox="0 0 {SZ} {SZ}">'
            f'<defs>{vd}{glow_defs()}</defs><g id="地图 M7 写实">{base()}{vr}{roads()}{glows()}{nodes()}{labels()}</g></svg>')

if __name__ == '__main__':
    s = build(); p = os.path.join(MO.OUT, 'M7 写实.svg')
    open(p, 'w', encoding='utf-8').write(s)
    if os.path.exists(JPG): shutil.copy(JPG, FIG_JPG)
    print(os.path.basename(p), f'{len(s) // 1024} KB', 'layers≈', s.count('<path') + s.count('<rect') + s.count('<text') + s.count('<circle'))
