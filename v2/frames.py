#!/usr/bin/env python3
"""Figma-ready frames (1920 x 1080, layered, named layers, editable text) -> v2/figma/*.svg

Import: download the .svg from GitHub, drag it onto a Figma canvas. Layer names come from the id attributes.
Fonts: Noto Sans SC + JetBrains Mono (both available in Figma as Google Fonts).
"""
import os
import design as D

OUT = os.path.join(D.HERE, 'figma'); os.makedirs(OUT, exist_ok=True)
W, H, INK, PAPER, SANS, MONO, LV = D.W, D.H, D.INK, D.PAPER, D.SANS, D.MONO, D.LV
MAP_X, MAP_Y, MAP_S = 560, -100, 1.26          # map placement in the frame (1000 map units -> 1260 px)
HS = D.hillshade_uri()

def t(x, y, s, size, fill=INK, fam=SANS, w=400, anchor='start', ls=0, op=1, id_=None):
    i = f' id="{id_}"' if id_ else ''
    return f'<text{i} x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{w}" fill="{fill}" fill-opacity="{op}" text-anchor="{anchor}" letter-spacing="{ls}">{s}</text>'
def lines(x, y, arr, size, lh, id_, **kw):
    return f'<g id="{id_}">' + ''.join(t(x, y + k * lh, ln, size, **kw) for k, ln in enumerate(arr)) + '</g>'
def pill(x, y, label, lv=None, dashed=False, id_='标签', size=22, fill=None):
    w = sum(size * (1.0 if ord(c) > 0x2e80 else .6) for c in label) + size * 1.4; h = size * 1.9
    L = LV[lv] if lv is not None else None
    bg = fill or (L['halo'] if L else PAPER)
    st = f'stroke="{INK}" stroke-opacity=".35" stroke-dasharray="4 4"' if dashed else 'stroke="none"'
    op = '.55' if L else '1'
    return (f'<g id="{id_}"><rect x="{x:.0f}" y="{y - h * .68:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{h / 2:.0f}" fill="{bg}" fill-opacity="{op if not dashed else 0}" {st}/>'
            + t(f'{x + size * .7:.0f}', y, label, size, op=.5 if dashed else 1, id_=None) + '</g>'), w

def map_group(obs, lv_of, focus=None, peek=()):
    s = [f'<g id="地图组" transform="translate({MAP_X} {MAP_Y}) scale({MAP_S})">', D.map_layers('', HS), '<g id="征兆光">']
    for sid in obs:
        lvl = lv_of.get(sid, 0)
        s.append(D.glow_svg('', sid, lvl, r=110 if sid == focus else None))
    s.append('</g><g id="观察点">')
    for sid in D.SIG:
        if sid in ('surge',): continue
        s.append(D.marker_svg('', sid, on=sid in obs, focus=sid == focus))
    s.append('</g></g>')
    return ''.join(s)

def frame(name, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{D.defs()}'
           f'<g id="{name}"><rect id="背景" width="{W}" height="{H}" fill="{PAPER}"/>{body}</g></svg>')
    open(os.path.join(OUT, name + '.svg'), 'w', encoding='utf-8').write(svg)
    return svg

def meter(x, y, lv, id_='等级条'):
    s = [f'<g id="{id_}">']
    for i in range(1, 5):
        L = LV[i]; on = i <= lv
        s.append(f'<rect x="{x + (i - 1) * 104}" y="{y}" width="96" height="6" rx="3" fill="{L["mid"] if on else INK}" fill-opacity="{1 if on else .12}"/>')
        s.append(t(x + (i - 1) * 104, y + 30, L['k'], 16, L['txt'] if on else INK, w=700 if i == lv else 400, op=1 if on else .35))
    s.append('</g>'); return ''.join(s)

def split2(s):
    k = (len(s) + 1) // 2 if len(s) > 3 else len(s)
    return [s[:k], s[k:]] if s[k:] else [s]

def focal_xy(sid):
    v = D.SIG[sid]; return MAP_X + v['x'] * MAP_S, MAP_Y + v['y'] * MAP_S

# ----------------------------------------------------------------------------- frames
def cover():
    b = [map_group([], {})]
    b.append(f'<rect id="左侧渐隐" x="0" y="0" width="980" height="{H}" fill="url(#fadeL)" transform="scale(1 1)"/>')
    b.append(t(96, 120, 'PROTOTYPE · 传统经验规则模型 · v0.2', 16, fam=MONO, ls=2.5, op=.55, id_='眉题'))
    b.append(lines(90, 330, ['看见什么，', '就升到哪一级。'], 104, 128, '标题', w=700, ls=-3))
    b.append(lines(96, 520, ['老人谚语描述的天象、天色和水情，', '是这套四级预警的输入。'], 30, 46, '副标题', op=.62))
    g = ['<g id="四级">']
    for i in range(1, 5):
        L = LV[i]; x = 96 + (i - 1) * 168
        g.append(f'<circle cx="{x + 30}" cy="700" r="30" fill="url(#g{i})"/>')
        g.append(t(x + 72, 694, L['k'] + ' · ' + L['no'], 20, L['txt'], w=700) + t(x + 72, 722, L['name'], 15, op=.6))
    g.append('</g>'); b.append(''.join(g))
    b.append(t(96, 980, '→  开始', 22, w=700, id_='开始'))
    b.append(t(230, 980, '沈家庵村 · 拒马河谷 · 一场暴雨的 32 小时（示意场景）', 18, op=.55, id_='场景说明'))
    return frame('00 封面', ''.join(b))

def story(k, S, total):
    st, obs, lv = S, S['obs'], S['lv']; f = st['focus']; v = D.SIG[f]; lvof = D.sig_level(obs)
    fl = lvof.get(f, 0); L = LV[lv]
    fx, fy = focal_xy(f)
    b = [map_group(obs, lvof, focus=f), f'<circle id="氛围光" cx="{fx:.0f}" cy="{fy:.0f}" r="1100" fill="url(#atm{max(lv, 0)})" opacity=".7"/>']
    b.append(f'<rect id="左侧渐隐" x="0" y="0" width="1000" height="{H}" fill="url(#fadeL)"/>')
    # where to look
    ax = fx + 34; ay = fy - 44
    b.append(f'<g id="观察位置"><line x1="{fx + 10:.0f}" y1="{fy - 10:.0f}" x2="{ax:.0f}" y2="{ay + 8:.0f}" stroke="{INK}" stroke-width="1"/>'
             + t(f'{ax:.0f}', f'{ay:.0f}', '在这里看', 15, fam=MONO, ls=1.5, op=.6) + t(f'{ax:.0f}', f'{ay + 26:.0f}', v['at'] + (f'  ▲ {v["h"]} m' if v.get('h') else ''), 18, w=500) + '</g>')
    # left: the sign
    b.append(t(96, 120, f'{k:02d} / {total:02d}', 16, fam=MONO, ls=2.5, op=.55, id_='步数') + t(196, 120, st['t'], 16, fam=MONO, ls=1.5, op=.55, id_='时间'))
    b.append(t(96, 300, f'{v["g"]} · {D.GRP[v["g"]]}', 18, fam=MONO, ls=2, op=.55, id_='分组'))
    parts = v['f'].split('，')
    b.append(lines(90, 396, [p + ('，' if i < len(parts) - 1 else '') for i, p in enumerate(parts)], 80, 100, '谚语', w=700, ls=-2))
    y = 396 + 100 * (len(parts) - 1) + 78
    b.append(lines(96, y, D.wrap(v['why'], 23), 24, 38, '解释', op=.62))
    y += 38 * len(D.wrap(v['why'], 23)) + 56
    r = D.rule_for(f, obs)
    if r:
        g = ['<g id="规则">']; x = 96
        for n, i in enumerate(r['ids']):
            if n: g.append(t(x + 4, y, '+', 26, op=.5)); x += 34
            p, w = D.pill if False else (None, None)
            have = i in obs
            ps, w = pill(x, y, D.label_of(i), r['lv'] if have else None, dashed=not have, id_=f'条件-{i}')
            g.append(ps); x += w + 10
        g.append(t(x + 8, y, '→', 26, op=.5)); x += 46
        RL = LV[r['lv']]
        g.append(f'<circle cx="{x + 24}" cy="{y - 9}" r="24" fill="url(#g{r["lv"]})"/>' + t(x + 24, y, RL['k'], 22, w=700, anchor='middle'))
        g.append(t(x + 62, y, r['op'] + (' · 已触发' if r['fired'] else ' · 等待组合'), 16, fam=MONO, ls=1.5, op=.6))
        g.append('</g>'); b.append(''.join(g))
    # bottom: current level and what to do
    b.append(f'<rect id="底栏" x="0" y="800" width="{W}" height="280" fill="url(#fadeB)"/>')
    b.append(meter(96, 924, lv))
    b.append(t(96, 1012, f'{L["k"]} · {L["no"]} · {L["name"]}', 34, L['txt'], w=700, id_='当前等级'))
    b.append(lines(700, 994, D.wrap(L['act'], 30), 26, 38, '行动', w=500))
    dots = ['<g id="进度">'] + [f'<circle cx="{1560 + i * 26}" cy="1004" r="{6 if i == k else 4}" fill="{INK}" fill-opacity="{1 if i <= k else .2}"/>' for i in range(1, total + 1)] + ['</g>']
    b.append(''.join(dots) + t(1824, 1010, '← →', 16, fam=MONO, op=.5, anchor='end', id_='翻页提示'))
    return frame(f'{k:02d} {LV[lv]["k"]} · {D.short(f)}', ''.join(b))

def explore():
    obs = ['01', '03', '09', '11']; lvof = D.sig_level(obs); lv, fired = D.evaluate(obs); L = LV[lv]
    b = [map_group(obs, lvof), f'<circle id="氛围光" cx="1180" cy="460" r="1200" fill="url(#atm{lv})" opacity=".7"/>']
    b.append(f'<rect id="左侧渐隐" x="0" y="0" width="1000" height="{H}" fill="url(#fadeL)"/>')
    b.append(t(96, 120, '自由体验 · 你看到了什么？点一下', 16, fam=MONO, ls=2, op=.55, id_='眉题'))
    b.append(f'<circle id="等级光球" cx="190" cy="330" r="130" fill="url(#g{lv})"/>' + t(190, 362, L['k'], 92, w=700, anchor='middle', id_='等级字'))
    b.append(t(360, 300, L['no'], 20, fam=MONO, ls=2, op=.6, id_='等级号') + t(360, 352, L['name'], 44, L['txt'], w=700, id_='等级名'))
    b.append(lines(96, 520, D.wrap(L['act'], 18), 30, 46, '行动', w=500))
    top = [r for r in fired if r['lv'] == lv]
    if top:
        b.append(t(96, 680, '触发  ' + '  ·  '.join(' + '.join(D.label_of(i) for i in r['ids']) for r in top) + f'  →  {L["k"]}', 20, op=.7, id_='触发说明'))
    # dock of cards
    b.append(f'<rect id="底栏" x="0" y="760" width="{W}" height="320" fill="url(#fadeB)"/>')
    CW = 101
    dock = ['<g id="谚语卡片">']; x = 96
    for g in 'ABC':
        ids = [i for i, s in D.SIG.items() if s['g'] == g]
        dock.append(t(x, 862, f'{g} · {D.GRP[g]}', 15, fam=MONO, ls=2, op=.55))
        for i in ids:
            on = i in obs; l2 = lvof.get(i, 0); role = D.rule_for(i, [])
            dock.append(f'<g id="卡片-{i}"><rect x="{x}" y="880" width="{CW}" height="112" rx="14" fill="{"#ffffff" if on else PAPER}" stroke="{INK}" stroke-opacity="{0 if on else .14}"/>')
            if on: dock.append(f'<circle cx="{x + CW - 22}" cy="904" r="16" fill="url(#g{l2})"/>')
            else: dock.append(f'<circle cx="{x + CW - 22}" cy="904" r="7" fill="none" stroke="{INK}" stroke-opacity=".3" stroke-dasharray="{"3 3" if not role or role["op"] == "AND" else "none"}"/>')
            dock.append(t(x + 16, 912, i, 15, fam=MONO, op=.5) + ''.join(t(x + 14, 950 + k * 28, ln, 20, w=700 if on else 500) for k, ln in enumerate(split2(D.short(i)))) + '</g>')
            x += CW + 10
        x += 38
    dock.append('</g>'); b.append(''.join(dock))
    return frame('20 自由体验', ''.join(b))

def components():
    b = [t(96, 110, '组件 · Components', 40, w=700, id_='标题'), t(96, 150, '谚语卡片三种状态 · 四级光 · 等级徽章 · 规则条件 · 观察点', 18, op=.6, id_='说明')]
    b.append('<g id="卡片状态">')
    for k, (nm, on, l2, dash) in enumerate([('默认', False, 0, False), ('已观察 · 已触发', True, 2, False), ('已观察 · 等待组合', True, 0, True)]):
        x = 96 + k * 220
        b.append(f'<g id="卡片-{nm}"><rect x="{x}" y="220" width="180" height="140" rx="16" fill="{"#ffffff" if on else PAPER}" stroke="{INK}" stroke-opacity="{.14 if not on else 0}"/>'
                 + (f'<circle cx="{x + 150}" cy="250" r="18" fill="url(#g{l2})"/>' if on else f'<circle cx="{x + 150}" cy="250" r="8" fill="none" stroke="{INK}" stroke-opacity=".3"/>')
                 + t(x + 18, 256, '03', 16, fam=MONO, op=.5) + t(x + 18, 300, '清早', 24, w=700) + t(x + 18, 332, '宝塔云', 24, w=700) + t(x, 392, nm, 15, op=.6) + '</g>')
    b.append('</g><g id="四级光">')
    for i in range(1, 5):
        x = 860 + (i - 1) * 250; L = LV[i]
        b.append(f'<g id="光-{L["k"]}"><circle cx="{x + 90}" cy="290" r="90" fill="url(#g{i})"/>' + t(x + 90, 410, f'{L["k"]} · {L["no"]}', 22, L['txt'], w=700, anchor='middle')
                 + t(x + 90, 440, L['mid'], 15, fam=MONO, anchor='middle', op=.6) + '</g>')
    b.append('</g><g id="等级徽章">')
    for i in range(1, 5):
        x = 96 + (i - 1) * 430; L = LV[i]
        b.append(f'<g id="徽章-{L["k"]}"><circle cx="{x + 60}" cy="580" r="60" fill="url(#g{i})"/>' + t(x + 60, 602, L['k'], 52, w=700, anchor='middle')
                 + t(x + 140, 566, L['no'], 16, fam=MONO, ls=2, op=.6) + t(x + 140, 604, L['name'], 26, L['txt'], w=700) + '</g>')
    b.append('</g><g id="规则条件">')
    p1, w1 = pill(96, 780, '03 清早宝塔云', 2, id_='条件-已观察'); p2, w2 = pill(96 + w1 + 50, 780, '09 闷极生雨', None, dashed=True, id_='条件-缺')
    b.append(p1 + t(96 + w1 + 14, 780, '+', 26, op=.5) + p2 + t(96 + w1 + w2 + 70, 780, '→  黄 · AND', 24, op=.7))
    b.append('</g><g id="观察点样式">')
    for k, (nm, on, foc) in enumerate([('未观察', False, False), ('已观察', True, False), ('当前', True, True)]):
        x = 1000 + k * 220
        b.append(f'<g id="点-{nm}"><circle cx="{x}" cy="770" r="{9 if foc else 6}" fill="{PAPER}" fill-opacity="{0 if on else .7}" stroke="{INK}" stroke-width="{1.3 if foc else .8}" stroke-opacity="{1 if on else .5}" transform="translate({x} 770) scale(2.4) translate({-x} -770)"/>'
                 f'<circle cx="{x}" cy="770" r="5.5" fill="{INK}"/>' + t(x + 40, 778, nm, 18, op=.7) + '</g>')
    b.append('</g>')
    b.append(t(96, 980, '字体 · Noto Sans SC（中文）· JetBrains Mono（数字和标签）· 纸 #F5F3EF · 墨 #161514', 18, fam=MONO, op=.6, id_='字体说明'))
    return frame('99 组件', ''.join(b))

if __name__ == '__main__':
    states = D.story_states(); total = len(states) - 2
    cover()
    for k, S in enumerate(states):
        if S.get('kind'): continue
        story(k, S, total)
    explore(); components()
    print('frames:', sorted(os.listdir(OUT)))
