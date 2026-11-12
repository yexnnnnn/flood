#!/usr/bin/env python3
"""村庄自然征兆预警 · 传统经验规则模型 v0.1 (the user's concept) -> card/index.html

Proverbs are the inputs of a four-level warning (蓝 / 黄 / 橙 / 红). Front: a map of 沈家庵 showing WHERE each
proverb's phenomenon is observed (peaks for cloud signs, gully heads for rain signs, creek mouths for water
signs, inside the gullies for danger signs), each glow coloured by the level it triggers. Back: the rule set.
Colour is drawn with vector radial / blurred-stroke gradients (no rasters), so it stays smooth and pure.
"""
import os, math
import build_card as B   # data: DEM, roads, gullies, river, 701 houses incl. east bank; svg helpers

HERE = B.HERE
W, H = 1480, 2100
PAPER, INK = '#f6f4f0', '#111111'
SANS, MONO, esc = B.SANS, B.MONO, B.esc
def text(x, y, s, size, weight=400, fill=INK, family=SANS, anchor='start', ls=0, op=1): return B.text(x, y, s, size, weight, fill, family, anchor, ls, op)

# level colours: halo -> mid -> core (light, pure; the core goes paler like a hot spot)
LV = {
    '蓝': dict(no='一级', name='天气征兆出现', halo='#9fc0ff', mid='#3d7bff', core='#cfe0ff', hex='#3d7bff'),
    '黄': dict(no='二级', name='降雨风险增加', halo='#fff1a0', mid='#ffd20a', core='#fffbe0', hex='#f2c200'),
    '橙': dict(no='三级', name='上游水情异常', halo='#ffc3a0', mid='#ff6a1a', core='#ffe2cf', hex='#ff6a1a'),
    '红': dict(no='四级', name='灾害正在发生或迫近', halo='#ffa3c0', mid='#ff1f5a', core='#ffe0ea', hex='#ff1f5a'),
}
# the user's proverb library (A 云层 / B 天色 / C 河流山谷); C items are project phrasings (官方前兆, 非原句)
PROV = {
    '01': '有雨山戴帽', '02': '天上钩钩云', '03': '清早宝塔云', '04': '云交云', '05': '棉花云', '06': '灰布云',
    '07': '朝霞不出门', '09': '闷极生雨', '10': '夜里闷雷忽东忽西',
    '11': '清水忽变黄', '12': '溪水突然涨', '13': '溪水突然断', '14': '山洪响', '15': '山坡裂缝增',
}
RULES = [
    ('蓝', '任一出现', [['01'], ['02'], ['05'], ['07']], '山地天气可能发生变化，请开始关注云层和天气变化。'),
    ('黄', '组合出现', [['03', '09'], ['02', '云层加厚'], ['04', '06'], ['10']], '天气可能向强降雨发展，请准备避险，远离河沟和低洼区域。'),
    ('橙', '任一出现', [['11'], ['12'], ['13', '水位骤降'], ['15']], '发现异常水情或山体迹象，请立即远离河道、沟谷和危险坡体，向安全地点转移。'),
    ('红', '任一出现', [['14'], ['13', '后异常暴涨'], ['泥沙石块树木']], '立即向沟谷两侧高处或安全避险点撤离，不要停留观察，不要返回取物。'),
]

def defs():
    g = ['<defs>', '<filter id="sb" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="16"/></filter>',
         '<filter id="sb2" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="6"/></filter>']
    for k, c in LV.items():
        g.append(f'<radialGradient id="r{k}"><stop offset="0" stop-color="{c["core"]}" stop-opacity="1"/><stop offset=".22" stop-color="{c["mid"]}" stop-opacity=".95"/>'
                 f'<stop offset=".55" stop-color="{c["mid"]}" stop-opacity=".45"/><stop offset=".8" stop-color="{c["halo"]}" stop-opacity=".22"/><stop offset="1" stop-color="{c["halo"]}" stop-opacity="0"/></radialGradient>')
        g.append(f'<linearGradient id="v{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["halo"]}"/><stop offset=".5" stop-color="{c["mid"]}"/><stop offset="1" stop-color="{c["core"]}"/></linearGradient>')
    g.append('</defs>'); return ''.join(g)

def tag(x, y, s, size=17, bg='#ffffff', fg=INK):
    w = sum(size * (1.0 if ord(c) > 0x2e80 else .62) for c in s) + 18
    return f'<rect x="{x:.1f}" y="{y - size - 6:.1f}" width="{w:.1f}" height="{size + 13}" fill="{bg}"/>' + text(x + 9, y, s, size, family=MONO, fill=fg, ls=1)

def glow(X, Y, r, lv):
    return (f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{r:.1f}" fill="url(#r{lv})"/>'
            f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="3" fill="{INK}"/><circle cx="{X:.1f}" cy="{Y:.1f}" r="11" fill="none" stroke="{INK}" stroke-width="1" stroke-opacity=".6"/>')
def stream(M, pts, lv, w):   # elongated glow along a creek reach: wide halo + saturated core, both blurred vector strokes
    c = LV[lv]; d = M.d(pts)
    return (f'<path d="{d}" fill="none" stroke="{c["halo"]}" stroke-width="{w * 2.6:.0f}" stroke-linecap="round" stroke-opacity=".5" filter="url(#sb)"/>'
            f'<path d="{d}" fill="none" stroke="{c["mid"]}" stroke-width="{w:.0f}" stroke-linecap="round" stroke-opacity=".85" filter="url(#sb2)"/>'
            f'<path d="{d}" fill="none" stroke="{c["core"]}" stroke-width="{w * .22:.1f}" stroke-linecap="round"/>')

def peaks(n, ext, sep=480, margin=200):   # highest point of each tile of a 3 x 3 grid, then the n highest, kept apart
    N, E, cx = B.N, B.ELEV, B.cx; best = {}
    x0, x1, z0, z1 = ext[0] + margin, ext[1] - margin, ext[2] + margin, ext[3] - margin
    for k in range(N * N):
        x, z = cx(k % N), cx(k // N)
        if not (x0 < x < x1 and z0 < z < z1): continue
        t = (int(3 * (x - x0) / (x1 - x0)), int(3 * (z - z0) / (z1 - z0)))
        if t not in best or E[k] > best[t][0]: best[t] = (E[k], x, z)
    out = []
    for e, x, z in sorted(best.values(), reverse=True):
        if e > B.village_e + 50 and all(math.hypot(x - a, z - b) > sep for _, a, b in out): out.append((e, x, z))
        if len(out) == n: break
    return out

# ---------------------------------------------------------------- front: where to look
def front():
    ext = (-1200, 1200, -1200, 1200); M = B.Map(ext, (70, 390, 1340, 1340))
    s = [defs(), f'<rect width="{W}" height="{H}" fill="{PAPER}"/>', M.clip('cf'), '<g clip-path="url(#cf)">']
    s.append(M.contours(20, .08, .2))
    RW = {'main': 1.5, 'lane': 1.0, 'track': .7, 'path': .55}
    s.append('<g fill="none" stroke="#111">' + ''.join(f'<path d="{M.d(r["p"])}" stroke-width="{RW.get(r["k"], .7)}" stroke-opacity="{.5 if r["k"] in ("main", "lane") else .25}"/>' for r in B.G['roads']) + '</g>')
    s.append(f'<path d="{M.d(B.G["river"])}" fill="none" stroke="#111" stroke-width="1.1" stroke-dasharray="1 4" stroke-opacity=".7"/>')
    for g in B.G['gullies']: s.append(f'<path d="{M.d(g["path"] + g.get("run", []))}" fill="none" stroke="#111" stroke-width=".8" stroke-opacity=".45"/>')
    # observation places, coloured by the level they trigger
    labels = []
    gs = B.G['gullies']
    # 蓝: cloud signs, watched on the peaks
    for (e, x, z), no in zip(peaks(4, ext), ['01', '02', '05', '07']):
        X, Y = M.P(x, z); s.append(glow(X, Y, 120, '蓝')); labels.append((X, Y, f'{no} {PROV[no]}', '蓝'))
    # 黄: rain signs, over the heads of the three largest gullies
    inside = lambda p, m=230: ext[0] + m < p[0] < ext[1] - m and ext[2] + m < p[1] < ext[3] - m
    for g, nos in zip(sorted(gs, key=lambda g: -g['area'])[:3], [('03', '09'), ('04', '06'), ('10',)]):
        x, z = next((p for p in g['path'] if inside(p)), g['path'][len(g['path']) // 2]); X, Y = M.P(x, z); s.append(glow(X, Y, 105, '黄')); labels.append((X, Y, ' + '.join(f'{n} {PROV[n]}' for n in nos), '黄'))
    # 红: danger signs inside the gullies (middle reach of the two gullies nearest the village)
    for g, no in zip([g for g in gs if sum(inside(q, 150) for q in g['path']) >= 6][:2], ['14', '13']):
        p = [q for q in g['path'] if inside(q, 150)]; seg = p[len(p) // 4: len(p) * 3 // 4 + 1]
        s.append(stream(M, seg, '红', 34)); X, Y = M.P(*seg[len(seg) // 2]); labels.append((X, Y, f'{no} {PROV[no]}', '红'))
    # 橙: water signs, where people can watch the water: gully mouths at the village, the Juma bank, a steep slope
    for g, no in zip(gs[:2], ['11', '12']):
        x, z = g['outlet']; X, Y = M.P(x, z); s.append(glow(X, Y, 90, '橙')); labels.append((X, Y, f'{no} {PROV[no]}', '橙'))
    best = max(((B.ELEV[k], k) for k in range(B.N * B.N) if 150 < min(math.hypot(B.cx(k % B.N) - h['x'], B.cx(k // B.N) - h['z']) for h in B.HOUSES[::25]) < 260 and B.HAND[k] > 25), default=None)
    if best:
        k = best[1]; X, Y = M.P(B.cx(k % B.N), B.cx(k // B.N)); s.append(glow(X, Y, 80, '橙')); labels.append((X, Y, f'15 {PROV["15"]}', '橙'))
    s.append(M.houses(M.box[2] / (ext[1] - ext[0]), lambda h: '#111'))
    for X, Y, lab, lv in labels:
        tx = X + 22 if X < 1080 else X - 22 - sum(17 * (1.0 if ord(c) > 0x2e80 else .62) for c in lab) - 18
        s.append(f'<line x1="{X:.1f}" y1="{Y:.1f}" x2="{tx + (0 if tx > X else 0):.1f}" y2="{Y - 30:.1f}" stroke="{INK}" stroke-width="1" stroke-opacity=".6"/>')
        s.append(tag(tx, Y - 30, lab, 16))
    s.append('</g>')
    s.append(f'<rect x="{M.box[0]}" y="{M.box[1]}" width="{M.box[2]}" height="{M.box[3]}" fill="none" stroke="{INK}" stroke-width="1"/>')
    # header
    s.append(tag(70, 98, 'PROTOTYPE · 传统经验规则模型 · v0.1', 18, '#e9f7c4'))
    s.append(text(1410, 98, '沈家庵村 · 拒马河谷', 18, family=MONO, anchor='end', ls=1.5, op=.7))
    s.append(text(64, 250, '看见什么，', 104, 700, ls=-3) + text(64, 360, '就升到哪一级。', 104, 700, ls=-3))
    # legend: four levels as smooth gradient chips
    y = 1800
    for i, (k, c) in enumerate(LV.items()):
        x = 70 + i * 340
        s.append(f'<rect x="{x}" y="{y}" width="64" height="64" rx="32" fill="url(#r{k})"/><circle cx="{x + 32}" cy="{y + 32}" r="3" fill="{INK}"/>')
        s.append(text(x + 82, y + 28, f'{k} · {c["no"]}', 26, 700, c['hex']) + text(x + 82, y + 60, c['name'], 20, op=.7))
    s.append(f'<line x1="70" y1="1950" x2="1410" y2="1950" stroke="{INK}" stroke-opacity=".2"/>')
    s.append(text(70, 1992, '光点 = 在哪里观察这句谚语描述的现象 · 颜色 = 它会触发的预警等级', 16, family=MONO, op=.65))
    s.append(text(70, 2024, '地图：Copernicus DEM（等高线 20 m）· OpenStreetMap · 卫星影像识别 701 栋房屋 · 观察点位置为示意', 15, family=MONO, op=.5))
    return f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">{"".join(s)}</svg>'

# ---------------------------------------------------------------- back: the rules
def chip(no):
    return f'{no} {PROV[no]}' if no in PROV else no
def back():
    s = [defs(), f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
    s.append(tag(70, 98, 'RULES · 四级规则', 18, '#e9f7c4'))
    s.append(text(1410, 98, '非官方 · 不能替代政府预警', 18, family=MONO, anchor='end', ls=1.5, op=.7))
    s.append(text(64, 230, '谚语 → 等级 → 行动', 84, 700, ls=-2))
    y = 330
    for lv, how, combos, msg in RULES:
        c = LV[lv]; h = 300
        s.append(f'<rect x="70" y="{y}" width="14" height="{h - 50}" rx="7" fill="url(#v{lv})"/>')
        s.append(f'<circle cx="190" cy="{y + 80}" r="88" fill="url(#r{lv})"/>')
        s.append(text(190, y + 98, lv, 58, 700, INK, anchor='middle'))
        s.append(text(330, y + 40, f'{c["no"]} · {c["name"]}', 34, 700, c['hex']))
        s.append(text(1410, y + 40, how.upper() if False else how, 18, family=MONO, anchor='end', ls=2, op=.65))
        xx, yy = 330, y + 100
        for combo in combos:
            lab = ' + '.join(chip(n) for n in combo)
            w = sum(19 * (1.0 if ord(ch) > 0x2e80 else .62) for ch in lab) + 26
            if xx + w > 1410: xx, yy = 330, yy + 50
            s.append(f'<rect x="{xx}" y="{yy - 27}" width="{w:.0f}" height="38" rx="19" fill="none" stroke="{INK}" stroke-width="1.1"/>')
            s.append(text(xx + 13, yy, lab, 19, family=MONO, ls=.5))
            xx += w + 12
        lines = [msg[i:i + 30] for i in range(0, len(msg), 30)]
        for k, ln in enumerate(lines): s.append(text(330, yy + 62 + k * 34, ln, 24, 600))
        y += h + 70
    yb = 1880
    s.append(f'<line x1="70" y1="{yb - 40}" x2="1410" y2="{yb - 40}" stroke="{INK}" stroke-opacity=".2"/>')
    for i, (k, v) in enumerate([('OR', '强信号任一出现就升级'), ('AND', '弱信号组合出现才升级'), ('TIME', '看信号是否持续、增强')]):
        x = 70 + i * 450; s.append(tag(x, yb, k, 18, '#e9f7c4') + text(x + 92, yb, v, 22, 500))
    s.append(text(70, yb + 56, '只升不轻易降：降级要重新看天气、河流、山体，并参考官方信息。明确的紧急信号直接撤离，不等逐级升级。', 20, op=.75))
    s.append(text(70, 2024, '来源：中国天气网 · 中科院科普 · 水利部山洪防御资料 · 国家应急广播 · 重庆市应急管理局 · 11–15 为项目整理的易记表达，非已查证老人原句', 15, family=MONO, op=.5))
    return f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">{"".join(s)}</svg>'

if __name__ == '__main__':
    page = f'''<!doctype html>
    <html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>村庄自然征兆预警 · 传统经验规则模型 v0.1</title>
    <style>
    @page {{ size: 148mm 210mm; margin: 0 }}
    html,body {{ margin:0; background:#e6e3dd; font-family:{SANS} }}
    .wrap {{ display:flex; flex-wrap:wrap; gap:36px; justify-content:center; padding:40px 24px 60px }}
    .side {{ width:min(46vw, 640px); aspect-ratio:148/210; box-shadow:0 30px 60px -30px rgba(0,0,0,.35) }}
    .side svg {{ width:100%; height:100%; display:block }}
    @media (max-width:900px) {{ .side {{ width:92vw }} }}
    @media print {{ html,body {{ background:none }} .wrap {{ display:block; padding:0 }} .side {{ width:148mm; height:210mm; box-shadow:none; break-after:page }} }}
    </style></head><body><div class="wrap"><div class="side">{front()}</div><div class="side">{back()}</div></div></body></html>'''
    open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(page)
    print('wrote index.html (concept v0.3)', len(page) // 1024, 'KB')
