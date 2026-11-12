#!/usr/bin/env python3
"""Figma frames in the 写实 · 玻璃 theme -> v2/figma/写实/*.svg (same frames and layer names as frames.py)

frames.py stays the source of layout and content. This module swaps in the photoreal map, a dark pill,
white markers and its own frame writer, then recolours the frame body:
  paper fills -> translucent white, ink -> white, level letters on light glow cores -> dark,
  the paper fades (左侧渐隐 / 底栏) -> glass panels.
Glass in SVG is a translucent dark fill + a faint white edge. In Figma, select the layers named 玻璃
and add Effect -> Background blur (about 40) to get the frosted look.
"""
import os, re
import design as D
import frames as F
import real_theme as RT

OUT = os.path.join(D.HERE, 'figma', '写实'); os.makedirs(OUT, exist_ok=True)
INK, PAPER, DARK, W, H = D.INK, D.PAPER, RT.DARK, D.W, D.H
LVD = RT.lv_dark()

# ---------------------------------------------------------------- patched pieces
D.map_layers = lambda pre='', hs=None: RT.map_layers(pre)
_marker = D.marker_svg
D.marker_svg = lambda pre, sid, on=False, focus=False: (_marker(pre, sid, on, focus)
    .replace(f'fill="{PAPER}" fill-opacity="0.7"', 'fill="#ffffff" fill-opacity=".22"').replace(f'fill="{PAPER}"', 'fill="#ffffff"').replace(INK, '#ffffff'))
F.LV = LVD

def pill(x, y, label, lv=None, dashed=False, id_='标签', size=22, fill=None):
    w = sum(size * (1.0 if ord(c) > 0x2e80 else .6) for c in label) + size * 1.4; h = size * 1.9
    if dashed:
        bg = f'fill="none" stroke="#ffffff" stroke-opacity=".5" stroke-dasharray="4 4"'; tc, top = '#ffffff', .65
    else:
        bg = f'fill="{fill or (LVD[lv]["halo"] if lv is not None else "#ffffff")}" fill-opacity=".92"'; tc, top = DARK, 1
    return (f'<g id="{id_}"><rect x="{x:.0f}" y="{y - h * .68:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{h / 2:.0f}" {bg}/>'
            + F.t(f'{x + size * .7:.0f}', y, label, size, fill=tc, op=top) + '</g>'), w
F.pill = pill

PANELS = {   # frame-name prefix -> (left panel, bottom panel), in frame px
    'cover': ((48, 56, 900, 968), None),
    'story': ((48, 56, 720, 808), (48, 880, 1824, 160)),
    'explore': ((48, 56, 780, 720), (48, 820, 1824, 200)),
}

def recolor(body):
    # cards that are 'on' are solid white: their text goes dark (before ink becomes white)
    def card(m):
        g = m.group(0)
        if 'fill="#ffffff" stroke=' in g:
            g = g.replace(INK, DARK).replace('fill="#ffffff" stroke=', 'fill="#ffffff" fill-opacity=".94" stroke=', 1)
        return g
    body = re.sub(r'<g id="卡片-[^"]*">.*?</g>', card, body)
    body = body.replace(f'fill="{PAPER}" fill-opacity="', 'fill="#ffffff" fill-opacity="')
    body = re.sub(f'fill="{PAPER}"', 'fill="#ffffff" fill-opacity=".07"', body)
    body = body.replace('stroke-opacity=".14"', 'stroke-opacity=".2"')
    # level letters sit on near-white glow cores
    body = re.sub(rf'fill="{INK}"([^>]*text-anchor="middle"[^>]*>)([蓝黄橙红—])</text>', rf'fill="{DARK}"\1\2</text>', body)
    body = body.replace(INK, '#ffffff')
    body = body.replace('纸 #F5F3EF · 墨 #161514', f'底 {RT.BG.upper()} · 字 #FFFFFF · 玻璃 = 深色 42% + 白描边 16%，Figma 里加 Background blur 40')
    return body

def frame(name, body):
    kind = 'cover' if name.startswith('00') else 'explore' if name.startswith('20') else 'comp' if name.startswith('99') else 'story'
    left, bottom = PANELS.get(kind, (None, None))
    body = re.sub(r'<rect id="左侧渐隐"[^>]*/>', RT.glass('玻璃-左栏', *left) if left else '', body)
    body = re.sub(r'<rect id="底栏"[^>]*/>', RT.glass('玻璃-底栏', *bottom) if bottom else '', body)
    if kind == 'comp': body = RT.glass('玻璃-面板', 48, 48, 1824, 984) + body
    body = recolor(body)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           f'{D.defs().replace("</defs>", RT.defs_extra() + "</defs>")}<g id="{name}">{RT.backdrop(W, H)}{body}</g></svg>')
    open(os.path.join(OUT, name + '.svg'), 'w', encoding='utf-8').write(svg)
    return svg
F.frame = frame

# ---------------------------------------------------------------- glass UI mockup: four-level panel + proverb cards
def wrap(s, n):
    return [s[i:i + n] for i in range(0, len(s), n)]

def card_lv(sid):
    return min(r['lv'] for r in D.RULES if sid in r['ids'])

def mockup(cur=2, obs=('03', '09'), cards=('01', '07', '03', '09', '11', '13', '14')):
    t, g = F.t, RT.glass
    s = [F.map_group(list(obs), {k: cur for k in obs}, focus=obs[0])]
    # title
    s.append(g('玻璃-标题', 48, 56, 560, 236))
    s.append(t(88, 112, '沈家庵村 · 拒马河', 18, op=.62, ls=2))
    s.append(t(88, 176, '看见什么，', 48, w=500) + t(88, 240, '就升到哪一级', 48, w=500))
    # four-level panel
    y0 = 316; s.append(g('玻璃-四级预警面板', 48, y0, 560, 708))
    s.append(t(88, y0 + 56, '四级预警', 22, w=600) + t(568, y0 + 56, 'WARNING LEVEL', 14, fam=D.MONO, op=.5, anchor='end', ls=2))
    for i in range(1, 5):
        L = LVD[i]; on = i == cur; y = y0 + 88 + (i - 1) * 150
        s.append(f'<g id="等级-{L["k"]}">')
        if on:
            s.append(f'<rect id="当前底" x="72" y="{y}" width="512" height="138" rx="20" fill="#ffffff" fill-opacity=".1" stroke="{L["mid"]}" stroke-opacity=".9" stroke-width="1.5"/>')
        if i <= cur:
            s.append(f'<circle id="光" cx="116" cy="{y + 48}" r="30" fill="{L["mid"]}"/>')
        else:
            s.append(f'<circle id="光" cx="116" cy="{y + 48}" r="29" fill="none" stroke="{L["mid"]}" stroke-width="2"/>')
        s.append(t(116, y + 56, L['k'], 22, fill=(DARK if i > 1 else '#ffffff') if i <= cur else L['txt'], w=700, anchor='middle'))
        s.append(t(164, y + 42, f'{L["no"]} · {L["name"]}', 20, fill=L['txt'], w=600, op=1 if i <= cur else .8))
        s.append(F.lines(164, y + 76, wrap(L['act'], 20), 16, 26, '行动', op=.78 if on else .5))
        n = sum(1 for r in D.RULES if r['lv'] == i)
        s.append(t(560, y + 42, f'{n} 条规则', 14, fam=D.MONO, op=.5, anchor='end'))
        s.append('</g>')
    # current status chip, top right
    L = LVD[cur]
    s.append(g('玻璃-当前状态', 1452, 56, 420, 96, r=48))
    s.append(f'<circle cx="1508" cy="104" r="22" fill="{L["mid"]}"/>' + t(1508, 112, L['k'], 20, fill='#ffffff' if cur == 1 else DARK, w=700, anchor='middle'))
    s.append(t(1548, 96, '当前预警', 14, op=.6, ls=2) + t(1548, 126, f'{L["no"]} · {L["name"]}', 20, fill=L['txt'], w=600))
    # proverb cards
    cx0, cy0, cw, ch, gap = 640, 724, 154, 276, 17
    s.append(g('玻璃-谚语卡片', 624, 664, 1248, 360))
    s.append(t(656, 706, '谚语卡片', 22, w=600) + t(1840, 706, '点亮你看见的现象，组合即规则', 16, op=.55, anchor='end'))
    for j, sid in enumerate(cards):
        v = D.SIG[sid]; lv = card_lv(sid); on = sid in obs; x = cx0 + 16 + j * (cw + gap); y = cy0 + 12
        ink = DARK if on else '#ffffff'; LC = LVD[lv]
        s.append(f'<g id="谚语-{sid} {v["s"]}">')
        s.append(f'<rect id="卡底" x="{x}" y="{y}" width="{cw}" height="{ch - 24}" rx="18" fill="#ffffff" fill-opacity="{.94 if on else .07}" stroke="#ffffff" stroke-opacity="{0 if on else .18}"/>')
        s.append(t(x + 18, y + 34, f'{sid} · {v["g"]} {D.GRP[v["g"]][:2]}', 13, fill=ink, fam=D.MONO, op=.55))
        s.append(F.lines(x + 18, y + 80, wrap(v['s'], 5), 24, 32, '谚语', fill=ink, w=600))
        s.append(F.lines(x + 18, y + 160, wrap(v['f'], 8)[:2], 14, 20, '原句', fill=ink, op=.6))
        s.append(f'<rect id="等级标" x="{x + 18}" y="{y + 206}" width="{cw - 36}" height="30" rx="15" fill="{LC["mid"]}"/>')
        s.append(t(x + cw / 2, y + 226, f'→ {LC["k"]} · {LC["no"]}' + (' 组合' if not any(r['ids'] == [sid] for r in D.RULES) else ''), 14, fill='#ffffff' if lv == 1 else DARK, w=600, anchor='middle'))
        s.append('</g>')
    return F.frame('30 玻璃样稿 · 四级预警与谚语卡片', ''.join(s))

if __name__ == '__main__':
    states = D.story_states(); total = len(states) - 2
    F.cover()
    for k, S in enumerate(states):
        if not S.get('kind'): F.story(k, S, total)
    F.explore(); F.components(); mockup()
    for n in sorted(os.listdir(OUT)): print(n, os.path.getsize(os.path.join(OUT, n)) // 1024, 'KB')
