#!/usr/bin/env python3
"""社区参与式早期预警 · 系统设计图（drag the SVGs into Figma; text and shapes stay editable)
   python3 v2/system_design.py  ->  v2/figma/系统设计/{1 线框图,2 流程,3 用户旅程,4 服务蓝图}.svg
"""
import os, re, math
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figma', '系统设计')
FONT = 'Noto Sans SC, PingFang SC, Source Han Sans SC, Microsoft YaHei, sans-serif'
SERIF = 'Georgia, Times New Roman, serif'
MONO = 'JetBrains Mono, SF Mono, Menlo, Consolas, monospace'
BG, INK, GREY, LINE, PAPER, MAP = '#f5f3ef', '#1f1f1f', '#85827a', '#d6d1c7', '#ffffff', '#e6e3db'
LV = {'蓝': '#3b6cf6', '黄': '#e9b10a', '橙': '#ef7a1a', '红': '#e0352b'}
ACT = {'蓝': '留意', '黄': '准备', '橙': '离开河沟', '红': '立即撤离'}

# ------------------------------------------------------------------ text helpers
def cw(c, fs): return fs * (0.56 if ord(c) < 128 else 1.0)
def tw(s, fs): return sum(cw(c, fs) for c in s)
def wrap(s, fs, w):
    toks, lines = re.findall(r'[A-Za-z0-9\.\-/%:+×±]+|\s|.', s), []
    cur = ''
    for t in toks:
        if t == '\n': lines.append(cur); cur = ''; continue
        if tw(cur + t, fs) > w and cur.strip():
            if t in '，。、；：）」』”！？,.;:)' and len(t) == 1: cur += t; continue   # no punctuation at line start
            lines.append(cur.rstrip()); cur = t.lstrip()
        else: cur += t
    if cur.strip(): lines.append(cur)
    return lines
def T(x, y, s, fs=14, w=None, fill=INK, weight=400, anchor='start', lh=1.45, font=FONT, op=1):
    """text block; y is the first baseline. returns (svg, height of the block)"""
    lines = wrap(s, fs, w) if w else s.split('\n')
    out = []
    for i, l in enumerate(lines):
        out.append(f'<text x="{x:.1f}" y="{y + i * fs * lh:.1f}" font-family="{font}" font-size="{fs}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"'
                   + (f' opacity="{op}"' if op != 1 else '') + f'>{escape(l)}</text>')
    return ''.join(out), len(lines) * fs * lh
def R(x, y, w, h, r=0, fill='none', stroke=None, sw=1, dash=None, op=1):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')
            + (f' stroke-dasharray="{dash}"' if dash else '') + (f' opacity="{op}"' if op != 1 else '') + '/>')
def C(x, y, r, fill='none', stroke=None, sw=1, dash=None, op=1):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')
            + (f' stroke-dasharray="{dash}"' if dash else '') + (f' opacity="{op}"' if op != 1 else '') + '/>')
def L(x1, y1, x2, y2, stroke=GREY, sw=1.5, dash=None, arrow=False):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else '')
            + (' marker-end="url(#arr)"' if arrow else '') + '/>')
def chip(x, y, s, fs=13, fill=PAPER, stroke=LINE, color=INK, h=30, pad=13):
    w = tw(s, fs) + 2 * pad
    return R(x, y, w, h, h / 2, fill, stroke) + T(x + w / 2, y + h / 2 + fs * .36, s, fs, fill=color, anchor='middle')[0], w
def svg(w, h, body):
    defs = ('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{GREY}"/></marker>'
            + ''.join(f'<radialGradient id="g{k}"><stop offset="0" stop-color="#fff"/><stop offset=".22" stop-color="{c}"/>'
                      f'<stop offset=".55" stop-color="{c}" stop-opacity=".35"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>' for k, c in LV.items())
            + '<linearGradient id="sheet" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".25" stop-color="#fff" stop-opacity=".9"/>'
              '<stop offset="1" stop-color="#fff" stop-opacity=".95"/></linearGradient></defs>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{defs}{R(0, 0, w, h, 0, BG)}{body}</svg>'
def legend(x, y, fs=14):
    out, cx = [], x
    for k, c in LV.items():
        out.append(C(cx + 7, y - fs * .35, 7, c)); s = f'{k} {ACT[k]}'
        out.append(T(cx + 20, y, s, fs)[0]); cx += 20 + tw(s, fs) + 26
    return ''.join(out)

# ------------------------------------------------------------------ 1 · wireframe
PW, PH = 390, 844
def mapart(dim=0):
    """a light placeholder for the 3D village map"""
    o = [R(0, 0, PW, PH, 0, MAP),
         f'<path d="M250,844 C220,700 300,600 290,480 C280,380 330,300 300,180 C290,120 320,60 340,0" stroke="#c9dbe3" stroke-width="34" fill="none"/>',
         f'<path d="M0,300 C120,320 200,360 390,330 M60,0 C90,200 150,420 120,844 M0,620 C140,600 230,640 390,560" stroke="#fff" stroke-width="3" fill="none" opacity=".9"/>',
         f'<path d="M0,90 C60,60 110,130 150,80 C190,40 170,0 170,0 L0,0 Z M0,700 C50,660 90,720 80,844 L0,844 Z" fill="#cfd8c4"/>']
    for i in range(46):                                                   # houses
        hx, hy = (37 * i * 7.3) % 330 + 30, (61 * i * 3.7) % 560 + 120
        o.append(R(hx, hy, 9, 7, 1.5, '#d3cfc6'))
    if dim: o.append(R(0, 0, PW, PH, 0, INK, op=dim))
    return ''.join(o)
def statusbar(light=False):
    c = '#fff' if light else INK
    return T(34, 36, '9:41', 15, fill=c, weight=600)[0] + R(PW - 64, 25, 28, 13, 4, 'none', c) + R(128, 828, 134, 5, 3, c)
def levelpill(k='蓝', x=20, y=54):
    s = f'{k} · {ACT[k]}'; w = tw(s, 14) + 46
    return R(x, y, w, 36, 18, PAPER, op=.95) + C(x + 20, y + 18, 6.5, LV[k]) + T(x + 34, y + 23, s, 14, weight=500)[0]
def mic(cx=195, cy=752, r=38, fill=INK, ring=False):
    o = (C(cx, cy, r + 14, 'none', fill, 2, op=.25) if ring else '') + C(cx, cy, r, fill)
    o += R(cx - 6, cy - 17, 12, 22, 6, '#fff') + f'<path d="M{cx - 11},{cy - 2} a11,11 0 0 0 22,0" stroke="#fff" stroke-width="2.2" fill="none"/>' + L(cx, cy + 9, cx, cy + 15, '#fff', 2.2)
    return o
def sidebtn(y, label, icon):
    cx = PW - 42
    ic = {'home': f'<path d="M{cx - 9},{y + 2} L{cx},{y - 8} L{cx + 9},{y + 2} L{cx + 9},{y + 10} L{cx - 9},{y + 10} Z" fill="none" stroke="{INK}" stroke-width="1.8"/>',
          'tent': f'<path d="M{cx - 11},{y + 9} L{cx},{y - 9} L{cx + 11},{y + 9} Z M{cx},{y - 9} L{cx},{y + 9}" fill="none" stroke="{INK}" stroke-width="1.8"/>'}[icon]
    return C(cx, y, 22, PAPER, op=.95) + ic + T(cx, y + 38, label, 10, anchor='middle', fill=INK)[0]
def marker(x, y, k, label, verified=True, r=26, count=None):
    o = C(x, y, r, f'url(#g{k})') if verified else C(x, y, r * .55, 'none', '#5d6b8a', 1.6, '3 3') + C(x, y, 4, '#5d6b8a')
    if count: o += T(x, y + 5, str(count), 14, fill='#fff', weight=700, anchor='middle')[0]
    w = tw(label, 11) + 24
    return o + R(x + r * .7, y - 13, w, 26, 13, PAPER, op=.92) + T(x + r * .7 + 12, y + 4, label, 11)[0]

def screen1():
    o = [mapart(), statusbar(), levelpill('蓝'), sidebtn(76, '我的家', 'home'), sidebtn(150, '安置点', 'tent'),
         C(195, 410, 36, LV['蓝'], LV['蓝'], 1.2, '4 4', op=.18), C(195, 410, 8, LV['蓝'], '#fff', 3), T(195, 466, '你的位置', 12, fill=GREY, anchor='middle')[0],
         R(0, 548, PW, 296, 0, 'url(#sheet)'),
         T(195, 630, 'What do you see?', 31, font=SERIF, anchor='middle')[0],
         T(195, 652, '↻  What do you hear?  ·  What feels different?', 11, fill=GREY, anchor='middle')[0]]
    x = 20
    for s in ['云', '河水浑浊', '泥土', '动物', '声音']:
        c, w = chip(x, 672, s)
        if x + w > PW - 8: break
        o.append(c); x += w + 8
    o += [mic(), T(195, 812, '按住说话', 11, fill=GREY, anchor='middle')[0]]
    return ''.join(o)
def screen2():
    o = [mapart(.35), statusbar(True), R(0, 420, PW, 440, 28, PAPER), R(175, 432, 40, 5, 3, LINE),
         T(32, 474, '正在听…', 13, fill=GREY)[0]]
    t, h = T(32, 510, '“北沟水声变闷了，水也有点发黄。”', 22, w=326, lh=1.4); o.append(t); y = 510 + h
    o += [C(39, y + 4, 5, LV['蓝']), T(52, y + 9, '沈家庵村 · 北沟口 · ±15 m · 16:42', 13, fill=GREY)[0]]
    y += 30; o.append(T(32, y + 19, '自动归类', 12, fill=GREY)[0]); x = 94
    for s in ['河水浑浊', '声音']:
        c, w = chip(x, y, s, 13, '#fff7e0', LV['黄']); o.append(c); x += w + 8
    o.append(T(32, y + 52, '对应经验：北沟水声变闷（橙）', 12, fill=GREY)[0])
    for i in range(34):                                                   # waveform
        hh = 6 + 26 * abs(math.sin(i * .7) * math.cos(i * .23)); o.append(R(62 + i * 8, 690 - hh / 2, 4, hh, 2, INK, op=.55))
    o += [mic(fill=LV['红'], ring=True), T(195, 812, '松开发送 · 上滑取消', 11, fill=GREY, anchor='middle')[0]]
    return ''.join(o)
def screen3():
    o = [mapart(), statusbar(), levelpill('黄'),
         T(20, 112, '●  已核实，颜色即等级      ◌  待核实', 11, fill=GREY)[0],
         marker(110, 250, '橙', '山坡掉石'), marker(250, 180, '黄', '北沟 · 3 条 · 40 分钟内', r=34, count=3),
         marker(220, 470, '蓝', '我的观察 · 待核实', verified=False), marker(300, 690, '蓝', '蜻蜓低飞要下雨'),
         R(20, 756, 350, 56, 28, PAPER, op=.95), T(44, 790, '过去 6 小时', 13)[0], L(140, 784, 340, 784, LINE, 3), C(300, 784, 9, INK)]
    return ''.join(o)
def screen4():
    o = [mapart(), statusbar(), marker(250, 180, '橙', '北沟', r=34, count=3), R(0, 290, PW, 570, 28, PAPER), R(175, 302, 40, 5, 3, LINE)]
    c, w = chip(32, 322, '山洪 · 已验证', 12, '#fdeee1', LV['橙'], LV['橙'], 26, 11); o.append(c)
    y = 382
    for s, fs, col, wt, gap in [('北沟水声变闷，半小时内避开沟口', 20, INK, 600, 6), ('村民口述 · 沈家庵村北沟及沟口 300 米范围', 12, GREY, 400, 16)]:
        t, h = T(32, y, s, fs, w=326, fill=col, weight=wt); o.append(t); y += h + gap
    for k, s in [('如果', '连续急雨后，在村口还能听见北沟水声由清脆变得发闷，同时水色开始发黄'), ('那么', '立即通知沟口与低洼院落人员，停止过沟，并安排两人到安全高点复核水位')]:
        o.append(T(32, y, k, 12, fill=LV['橙'], weight=600)[0]); t, h = T(72, y, s, 14, w=286); o.append(t); y += h + 10
    t, h = T(46, y + 26, '为什么：水声发闷、水色发黄，往往说明上游来水变大、泥沙变多。', 13, w=300, fill=INK)
    o += [R(32, y + 4, 326, h + 30, 14, BG), t]; y += h + 48
    o.append(T(32, y, '印证：3 位村民 · 40 分钟内 · 雨量站 28 mm/h（示例）', 12, fill=GREY, w=326)[0])
    o += [R(32, 760, 160, 48, 24, INK), T(112, 790, '我也看到了', 15, fill='#fff', anchor='middle', weight=500)[0],
          R(202, 760, 156, 48, 24, PAPER, LINE), T(280, 790, '没看到', 15, anchor='middle')[0]]
    return ''.join(o)
def screen5():
    o = [mapart(), C(240, 430, 120, f'url(#g橙)'), T(240, 560, '北沟沟口 300 m', 12, anchor='middle', fill=LV['橙'], weight=600)[0], statusbar(),
         R(16, 50, 358, 44, 22, LV['橙']), C(38, 72, 6, '#fff', op=.7), C(352, 72, 6, '#fff', op=.7),
         T(195, 77, 'BROADCAST ON AIR · 橙 · 离开河沟', 13, fill='#fff', weight=600, anchor='middle')[0],
         R(16, 108, 358, 150, 20, PAPER, op=.97), R(30, 124, 34, 34, 8, LV['橙']),
         T(76, 138, '沈家庵预警 · 橙色', 13, weight=600)[0], T(358, 138, '现在', 12, fill=GREY, anchor='end')[0]]
    t, h = T(76, 158, '北沟水声变闷，半小时内避开沟口。你家在影响范围内，请离开河沟。', 14, w=282); o.append(t)
    o += [R(76, 214, 100, 30, 15, BG), T(126, 234, '查看路线', 13, anchor='middle')[0], R(184, 214, 100, 30, 15, BG), T(234, 234, '我已安全', 13, anchor='middle')[0],
          R(16, 620, 358, 196, 20, PAPER, op=.97), T(34, 650, '同一条消息也会通过', 13, fill=GREY)[0]]
    for i, s in enumerate(['村广播喇叭 · 每 10 分钟重复', '按键设备 · 震动并播报', '网格员 · 上门通知独居老人', '短信 · 发给子女']):
        o += [C(42, 678 + i * 33, 4, LV['橙']), T(56, 683 + i * 33, s, 14)[0]]
    return ''.join(o)
def screen6():
    o = [mapart(), statusbar(), levelpill('橙'),
         f'<path d="M92,430 C140,380 120,300 190,270 C250,245 270,190 300,170" stroke="{INK}" stroke-width="5" stroke-dasharray="2 9" stroke-linecap="round" fill="none"/>',
         C(92, 430, 10, INK), T(92, 460, '家', 12, anchor='middle', weight=600)[0],
         C(300, 170, 13, PAPER, INK, 2), f'<path d="M291,177 L300,161 L309,177 Z" fill="{INK}"/>', T(300, 204, '村委会安置点', 12, anchor='middle', weight=600)[0],
         R(0, 488, PW, 380, 28, PAPER), R(175, 500, 40, 5, 3, LINE)]
    y = 540
    o.append(T(32, y, '去 村委会安置点', 20, weight=600)[0]); y += 24
    o.append(T(32, y, '620 m · 上坡 18 m · 走大路，不过北沟桥', 13, fill=GREY)[0]); y += 44
    o += [T(32, y, '约 15 分钟', 28, weight=600)[0], T(186, y - 2, '按 76 岁步速 0.7 m/s 估算', 12, fill=GREY)[0]]; y += 16
    o += [R(32, y, 326, 38, 12, '#fdeee1'), T(46, y + 25, '建议现在出发 · 比一般人早 10 分钟', 14, fill=LV['橙'], weight=600)[0]]; y += 56
    o.append(T(32, y, '安置点有', 12, fill=GREY)[0]); y += 10; x = 32
    for s in ['床位 120', '饮用水', '常用药', '毛毯', '充电', '医生值班']:
        c, w = chip(x, y, s, 12, BG, None, INK, 26, 10)
        if x + w > PW - 30: x = 32; y += 34; c, w = chip(x, y, s, 12, BG, None, INK, 26, 10)
        o.append(c); x += w + 6
    o += [R(32, 762, 160, 48, 24, INK), T(112, 792, '我已出发', 15, fill='#fff', anchor='middle', weight=500)[0],
          R(202, 762, 156, 48, 24, PAPER, LINE), T(280, 792, '我需要人帮忙', 15, anchor='middle')[0]]
    return ''.join(o)

SCREENS = [
    ('01 · Observe 观察', '首页', screen1, '背景是可拖拽、缩放、旋转的 3D 村庄地图。打开就是地图和话筒，不用先登录、不用先选类别。三句英文提问缓慢交替淡入淡出；下面的词只是提示，点一下就开始录音。话筒在拇指区，离底部约 90 px。'),
    ('01 · Observe 观察', '录音中', screen2, '按住说话，松开发送。系统自动加时间和位置，转成文字并初步归类，村民只需确认。没信号时先存在手机里，有网再补发。'),
    ('02 · Map 汇集', '观察地图', screen3, '实心发光圈 = 已核实，颜色就是等级；虚线空心圈 = 待核实，不和蓝色等级混淆。同一地点、同一时段的观察合并成一个圈，显示条数。'),
    ('03 · Assess 判断', '规则卡 · 学习', screen4, '点开一个圈，看到“如果……那么……”规则卡：这条经验说什么、为什么、现在多少人印证。这里就是教育功能，每次上报都在学怎么看懂自然。'),
    ('04 · Alert 传播', '广播 + 推送', screen5, '核实后自动生成广播：顶部常驻 BROADCAST ON AIR 条，颜色跟等级；同时发系统推送。同一条消息也走村广播、按键设备、网格员和短信。'),
    ('05 · Evacuate 行动', '我的逃生路线', screen6, '按家的位置、年龄和身体状况估算步速，给老人更早的出发时间。显示路线、时长，以及安置点有什么。'),
]
def wireframe():
    M, G = 80, 72; W = M * 2 + len(SCREENS) * PW + (len(SCREENS) - 1) * G; TOP = 230; H = TOP + PH + 250
    o = [T(M, 96, '沈家庵 · 社区参与式早期预警 · 线框图', 40, weight=600)[0],
         T(M, 138, 'Wireframe · 6 个关键页面，对应 Observe → Map → Assess → Alert → Evacuate', 18, fill=GREY)[0],
         legend(W - M - 520, 100, 16)]
    for i, (stage, name, fn, note) in enumerate(SCREENS):
        x = M + i * (PW + G)
        o += [T(x, TOP - 30, stage, 15, fill=GREY, font=MONO)[0], T(x + PW, TOP - 30, name, 15, weight=600, anchor='end')[0],
              f'<clipPath id="ph{i}"><rect x="0" y="0" width="{PW}" height="{PH}" rx="44"/></clipPath>',
              f'<g transform="translate({x},{TOP})"><g clip-path="url(#ph{i})">{fn()}</g>{R(0, 0, PW, PH, 44, "none", "#bdb7ab", 2)}</g>',
              T(x, TOP + PH + 44, note, 14, w=PW, fill=INK, lh=1.6)[0]]
        if i: o.append(L(x - G + 12, TOP + PH / 2, x - 12, TOP + PH / 2, GREY, 1.5, arrow=True))
    return svg(W, H, ''.join(o))

# ------------------------------------------------------------------ 2 · workflow
STAGES = [('01', 'Observe', '观察'), ('02', 'Map', '汇集'), ('03', 'Assess', '判断'), ('04', 'Alert', '传播'), ('05', 'Evacuate', '行动')]
def node(x, y, w, s, fs=15, fill=PAPER, stroke=LINE, color=INK, pad=14, weight=400):
    t, h = T(x + pad, y + pad + fs * .9, s, fs, w=w - 2 * pad, fill=color, weight=weight)
    return R(x, y, w, h + 2 * pad - fs * .3, 12, fill, stroke) + t, h + 2 * pad - fs * .3
def diamond(x, y, w, h, s):
    cx, cy = x + w / 2, y + h / 2
    return (f'<polygon points="{cx},{y} {x + w},{cy} {cx},{y + h} {x},{cy}" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/>'
            + T(cx, cy + 5, s, 14, anchor='middle', weight=600)[0])
def workflow():
    W, H, M, top = 1920, 1180, 80, 200; cwid = (W - 2 * M) / 5; nw = cwid - 48
    o = [T(M, 90, '工作流程 · Workflow', 40, weight=600)[0], T(M, 130, '一条观察怎样变成每个人的行动。灰色虚线 = 回到前一步。', 18, fill=GREY)[0], legend(W - M - 520, 92, 16)]
    for i, (n, en, cn) in enumerate(STAGES):
        x = M + i * cwid
        o += [R(x, top, cwid - 24, 52, 26, INK), T(x + 22, top + 33, f'{n}  {en}', 16, fill='#fff', font=MONO)[0], T(x + cwid - 46, top + 33, cn, 16, fill='#fff', anchor='end', weight=600)[0]]
        if i: o.append(L(x - 22, top + 26, x - 4, top + 26, GREY, 1.5, arrow=True))
    def col(i, items):
        x, y = M + i * cwid, top + 84
        for it in items:
            kind = it[0]
            if kind == 'n':
                if y > top + 84: o.append(L(x + nw / 2, y - 26, x + nw / 2, y - 4, arrow=True))
                s, h = node(x, y, nw, it[1], **(it[2] if len(it) > 2 else {})); o.append(s); y += h + 30
            elif kind == 'multi':                                      # several sources feeding the next node
                for s_ in it[1]:
                    s, h = node(x, y, nw, s_, 14, BG, LINE); o.append(s); y += h + 8
                y += 22
            elif kind == 'fan':                                        # one node feeding several channels
                o.append(L(x + nw / 2, y - 26, x + nw / 2, y - 4, arrow=True))
                for s_ in it[1]:
                    s, h = node(x + 20, y, nw - 20, s_, 14, BG, LINE); o.extend([L(x + 8, y - 8, x + 8, y + h / 2), L(x + 8, y + h / 2, x + 20, y + h / 2), s]); y += h + 8
                y += 22
            elif kind == 'd':                                          # decision + "no" branch on the right
                o.append(L(x + nw / 2, y - 26, x + nw / 2, y - 4, arrow=True))
                dw, dh = nw * .62, 86; o.append(diamond(x, y, dw, dh, it[1]))
                s, h = node(x + dw + 26, y + dh / 2 - 30, nw - dw - 26, it[2], 12, PAPER, GREY, GREY, 10)
                o.extend([L(x + dw, y + dh / 2, x + dw + 24, y + dh / 2, arrow=True), T(x + dw + 6, y + dh / 2 - 8, '否', 12, fill=GREY)[0], s,
                      T(x + dw / 2 + 8, y + dh + 18, '是', 12, fill=GREY)[0]])
                y += dh + 30
        return y
    ys = [col(0, [('multi', ['村民用 App 按住说话', '老人按按键设备说话', '网格员上门代录']), ('n', '语音转文字，自动加时间和位置'), ('n', '没信号：先存本地，有网再补发', {'fill': BG})]),
          col(1, [('n', '归类：云 / 水 / 土 / 动物 / 声音'), ('n', '匹配谚语和经验库'), ('n', '地图上出现「待核实」圈'), ('n', '同一地点、同一时段的观察合并成一个圈')]),
          col(2, [('n', '规则引擎打分：类型 × 时间远近 × 距离 × 互相印证\n＋ 雨量站 · 水位站 · 气象台'), ('d', '超过阈值？', '留在地图上，继续观察 ↺'),
                  ('n', '网格员 / 村干部核实'), ('d', '属实？', '标为未证实，告诉上报人为什么 ↺'), ('n', '定级：蓝 留意 · 黄 准备 · 橙 离开河沟 · 红 立即撤离', {'weight': 600})]),
          col(3, [('n', '自动生成广播稿：等级 + 地点 + 该做什么'), ('n', '村干部一键确认发布'), ('fan', ['App 顶部 BROADCAST ON AIR + 推送', '村广播喇叭 · 定时重复', '按键设备 · 震动并播报', '网格员上门 · 独居老人优先', '短信 · 发给子女'])]),
          col(4, [('n', '按家的位置、年龄、身体状况算出发时间'), ('n', '推送个人路线和安置点信息'), ('n', '到安置点签到'), ('d', '都到了吗？', '网格员上门找人'), ('n', '解除预警，回家')])]
    yb = max(ys) + 10; x3, x5 = M + 2 * cwid + nw / 2, M + 4 * cwid + nw / 2
    o += [f'<path d="M{x5},{ys[4] - 30} L{x5},{yb + 40} L{x3},{yb + 40} L{x3},{ys[2] - 26}" fill="none" stroke="{GREY}" stroke-width="1.5" stroke-dasharray="6 6" marker-end="url(#arr)"/>',
          node(x3 + 30, yb + 58, x5 - x3 - 60, '复盘：这次哪条经验应验了？规则从「试验中」变成「已验证」，或者被调整阈值', 14, BG, LINE)[0]]
    return svg(W, int(yb + 150), ''.join(o))

# ------------------------------------------------------------------ 3 · user journey
def journey():
    W, H, M = 1920, 1200, 80
    o = [T(M, 90, '用户旅程 · User Journey Map', 40, weight=600)[0], T(M, 130, '一次山洪预警中，一位没有智能手机的老人', 18, fill=GREY)[0]]
    pc, ph = node(M, 160, 760, '王奶奶，76 岁，独居，住北沟口低洼院落。没有智能手机，挂着按键设备。腿脚慢，步速约 0.7 m/s。子女在北京。', 16, PAPER, LINE)
    o.append(pc)
    stages = ['1 发现变化', '2 上报', '3 等待', '4 收到预警', '5 撤离', '6 安置与回家']
    rows = [('她在做什么', ['下午连着下急雨，她在院里听见北沟的水声变闷，水也发黄。', '按住按键说：“北沟水声闷了，水黄了。”灯变绿，设备说“收到了”。', '回屋等。十分钟后网格员打电话问情况。',
                         '村广播响了：橙色，离开河沟。按键设备震动并播报。', '网格员来接她，按路线走到村委会，比别人早出发 10 分钟。', '在安置点签到，有床有药。雨停后听到解除广播，回家。']),
            ('触点', ['自己的耳朵和眼睛 · 老辈的谚语', '按键设备', '网格员电话 · 后台规则引擎', '村广播 · 按键设备 · 子女收到短信', '网格员 · 路线 · 路标', '安置点 · 解除广播']),
            ('她在想什么', ['“这声音不对，老辈人说过……”', '“我说的有人听吗？”', '“是不是我大惊小怪了？”', '“真来了。我走得慢，来得及吗？”', '“有人陪着，心里踏实。”', '“下次我还报。”']),
            ('情绪', None),
            ('痛点', ['看到了，但不确定算不算大事', '不会用手机、不识字也能报吗', '等的时候没有反馈，容易放弃', '只有颜色没有动作，不知道该干嘛', '走得慢，夜里看不清路', '不知道什么时候可以回家']),
            ('机会', ['谚语卡片 + 广播里的“观察小课堂”', '一个按键：语音、灯、声音反馈', '自动回电：“已收到，网格员会联系你”', '广播一定说：等级 + 地点 + 动作', '按步速提前出发 · 夜间反光路标', '解除通知 + 告诉她她的上报帮了谁'])]
    LW = 190; x0 = M + LW; cwid = (W - M - x0) / 6; y = 160 + ph + 50
    for i, s in enumerate(stages):
        o += [R(x0 + i * cwid, y, cwid - 12, 46, 23, INK), T(x0 + i * cwid + 20, y + 30, s, 16, fill='#fff', weight=600)[0]]
    y += 66
    emo = [-.4, .5, -1, -2, .8, 1.6]
    for name, cells in rows:
        if cells is None:
            hh = 170; o += [R(M, y, W - 2 * M, hh, 14, PAPER), T(M + 20, y + 32, name, 15, weight=600)[0], L(x0, y + hh / 2, W - M - 12, y + hh / 2, LINE, 1, '4 6')]
            pts = [(x0 + (i + .5) * cwid - 6, y + hh / 2 - e * 34) for i, e in enumerate(emo)]
            d = f'M{pts[0][0]},{pts[0][1]}' + ''.join(f' C{(pts[i - 1][0] + pts[i][0]) / 2},{pts[i - 1][1]} {(pts[i - 1][0] + pts[i][0]) / 2},{pts[i][1]} {pts[i][0]},{pts[i][1]}' for i in range(1, len(pts)))
            o.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.5"/>')
            for (px, py), e in zip(pts, emo): o.append(C(px, py, 7, LV['红'] if e <= -1.5 else LV['橙'] if e < 0 else LV['蓝'], '#fff', 2))
            o += [T(M + 20, y + 58, '安心', 12, fill=GREY)[0], T(M + 20, y + hh - 20, '担心', 12, fill=GREY)[0]]
            y += hh + 12; continue
        hs = [T(0, 0, c, 14, w=cwid - 44)[1] for c in cells]; hh = max(hs) + 34
        fill = '#fdeee1' if name == '痛点' else '#e9eefe' if name == '机会' else PAPER
        o += [R(M, y, W - 2 * M, hh, 14, fill), T(M + 20, y + 28, name, 15, weight=600)[0]]
        for i, c in enumerate(cells): o.append(T(x0 + i * cwid + 4, y + 28, c, 14, w=cwid - 44)[0])
        y += hh + 12
    return svg(W, int(y + 70), ''.join(o))

# ------------------------------------------------------------------ 4 · service blueprint
def blueprint():
    W, M = 2200, 80
    o = [T(M, 90, '服务蓝图 · Service Blueprint', 40, weight=600)[0], T(M, 130, '村民看得见的部分在可见线以上；网格员、村干部和系统在以下。', 18, fill=GREY)[0]]
    rows = [('实物证据', 'Physical evidence', ['按键设备 · App 首页 · 谚语卡片', '地图上的观察圈', '规则卡「如果……那么……」', '顶部广播条 · 推送 · 喇叭 · 短信', '路线 · 路标 · 安置点物资清单']),
            ('村民行动', 'Resident actions', ['看到 / 听到变化，按住说话', '打开地图看附近的观察，点「我也看到了」', '读规则卡；接网格员电话确认', '收到预警，按等级准备或离开', '按路线出发，到安置点签到']),
            ('|', '互动线 Line of interaction', None),
            ('前台', 'Frontstage', ['App 录音并确认归类；设备灯变绿、播报“收到了”', '地图实时显示待核实圈和合并后的条数', '网格员电话或上门核实', 'App 广播条 + 推送；村广播；按键设备播报；网格员上门', '个人路线和出发时间；安置点工作人员接待']),
            ('|', '可见线 Line of visibility', None),
            ('后台', 'Backstage', ['语音转文字（方言）· 定位 · 去重', '分类模型 + 谚语库匹配', '规则引擎打分；村干部决定是否定级', '自动生成广播稿，村干部一键确认发布', '算每户出发时间；点名表；派网格员找未到的人']),
            ('|', '内部互动线 Line of internal interaction', None),
            ('支持系统', 'Support processes', ['按键设备 · 4G / Wi-Fi · 离线缓存', '3D 村庄地图 · 观察数据库', '雨量站 / 水位站 / 气象台接口；规则库（试验中 / 已验证）', '村广播系统 · 短信网关 · 推送服务', '户籍与健康信息（经本人同意）· 安置点物资台账 · 步速表'])]
    LW = 230; x0 = M + LW; cwid = (W - M - x0) / 5; y = 180
    for i, (n, en, cn) in enumerate(STAGES):
        o += [R(x0 + i * cwid, y, cwid - 14, 52, 26, INK), T(x0 + i * cwid + 22, y + 33, f'{n}  {en}', 16, fill='#fff', font=MONO)[0],
              T(x0 + (i + 1) * cwid - 36, y + 33, cn, 16, fill='#fff', anchor='end', weight=600)[0]]
    y += 76
    for name, en, cells in rows:
        if name == '|':
            o += [L(M, y + 6, W - M, y + 6, GREY, 1.5, '8 6'), T(W - M, y - 4, en, 13, fill=GREY, anchor='end')[0]]; y += 26; continue
        hs = [T(0, 0, c, 15, w=cwid - 58)[1] for c in cells]; hh = max(hs) + 40
        fill = '#e9eefe' if name == '村民行动' else PAPER
        o += [T(M, y + 30, name, 17, weight=600)[0], T(M, y + 52, en, 12, fill=GREY, font=MONO)[0]]
        for i, c in enumerate(cells):
            o += [R(x0 + i * cwid, y, cwid - 14, hh, 14, fill, LINE), T(x0 + i * cwid + 20, y + 30, c, 15, w=cwid - 58)[0]]
        y += hh + 18
    o.append(T(M, y + 30, '注：图中数字只是示例。年龄和健康信息必须本人同意，只用来算出发时间，不对外公开。', 14, fill=GREY)[0])
    return svg(W, int(y + 80), ''.join(o))

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for fn, f in [('1 线框图', wireframe), ('2 流程', workflow), ('3 用户旅程', journey), ('4 服务蓝图', blueprint)]:
        s = f(); open(os.path.join(OUT, fn + '.svg'), 'w', encoding='utf-8').write(s)
        m = re.search(r'width="(\d+)" height="(\d+)"', s); print('wrote', fn, m.group(1), 'x', m.group(2), len(s) // 1024, 'KB')
