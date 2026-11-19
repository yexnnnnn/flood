#!/usr/bin/env python3
"""Community-based Early Warning · system design sheets, English editorial edition.
   python3 v2/system_design_en.py  ->  v2/figma/system-design-en/*.svg   (drag into Figma; everything stays editable)
   Type: Instrument Serif (display) · Inter (text) · JetBrains Mono (labels) — all on Google Fonts, all in Figma.
"""
import os, re, math
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figma', 'system-design-en')
# Swiss-signal edition: one grotesk family (Inter Tight display / Inter text), white paper + crosshair dot grid,
# flat saturated highlighter blocks, an orange oval, black ticker bands.  All fonts are on Google Fonts / in Figma.
SERIF = 'Inter Tight, Inter, Helvetica Neue, Arial, sans-serif'      # display (kept the old name so call sites stay)
SANS = 'Inter, Helvetica Neue, Arial, sans-serif'
MONO = 'Inter, Arial, Helvetica Neue, sans-serif'                     # small caps labels
BG, INK, MUTE, HAIR, PAPER, TINT, MAP = '#ffffff', '#0a0a0a', '#7a7a7a', '#d6d6d6', '#ffffff', '#f1f1ef', '#ebebe8'
LV = {'blue': '#1f4bff', 'yellow': '#ffe100', 'orange': '#ff6a00', 'red': '#ff2a1f'}
ON = {'blue': '#fff', 'yellow': INK, 'orange': INK, 'red': '#fff'}   # text colour on each level block
HL = {'yellow': '#ffe100', 'orange': '#ff6a00', 'pink': '#ff3fae', 'green': '#1fd17a', 'violet': '#a98bff', 'blue': '#1f4bff'}
STC = ['#1fd17a', '#a98bff', '#ff3fae', '#ff6a00', '#1f4bff']       # Observe Map Assess Alert Evacuate
ACT = {'blue': 'Watch', 'yellow': 'Prepare', 'orange': 'Leave the gully', 'red': 'Evacuate now'}
FACT = {SERIF: .50, SANS: .55, MONO: .68}
PROJECT = "CBEWS — SHENJIA'AN VILLAGE, LAISHUI"

# ------------------------------------------------------------------ primitives
_BW = dict(zip('abcdefghijklmnopqrstuvwxyz', [.56, .6, .54, .6, .57, .36, .6, .6, .26, .26, .55, .26, .9, .6, .59, .6, .6, .39, .52, .37, .6, .55, .8, .55, .55, .5]))
_BW.update({' ': .24, ',': .26, '.': .26, "'": .22, '-': .4, 'I': .28, 'M': .86, 'W': .95, 'J': .5})
def tw(s, fs, font=SANS, ls=0):
    if font == SERIF:                       # per-glyph widths ≈ Inter Tight Bold (display text gets highlighter blocks)
        return fs * sum(_BW.get(ch, .68 if ch.isupper() else .6) * .96 + ls for ch in s)
    return len(s) * fs * (FACT[font] + ls)
def wrap(s, fs, w, font=SANS, ls=0):
    out = []
    for para in s.split('\n'):
        cur = ''
        for word in para.split(' '):
            t = (cur + ' ' + word) if cur else word
            if tw(t, fs, font, ls) > w and cur: out.append(cur); cur = word
            else: cur = t
        out.append(cur)
    return out
def T(x, y, s, fs=14, w=None, fill=INK, font=SANS, weight=400, anchor='start', lh=1.45, ls=0, up=False, italic=False, op=1):
    s = s.upper() if up else s
    if font == SERIF:                                   # display: bold, tight, upright
        weight = 700 if weight == 400 else weight; ls = ls or -.04; italic = False; lh = min(lh, 1.08)
    lines = wrap(s, fs, w, font, ls) if w else s.split('\n')
    a = (f' letter-spacing="{ls * fs:.2f}"' if ls else '') + (' font-style="italic"' if italic else '') + (f' opacity="{op}"' if op != 1 else '')
    return ''.join(f'<text x="{x:.1f}" y="{y + i * fs * lh:.1f}" font-family="{font}" font-size="{fs}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{a}>{escape(l)}</text>'
                   for i, l in enumerate(lines)), len(lines) * fs * lh
def M_(x, y, s, fs=11, fill=MUTE, anchor='start', w=None):          # mono label
    return T(x, y, s, fs, w=w, fill=fill, font=MONO, anchor=anchor, ls=.06, up=True, weight=600)
def R(x, y, w, h, r=0, fill='none', stroke=None, sw=1, dash=None, op=1):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')
            + (f' stroke-dasharray="{dash}"' if dash else '') + (f' opacity="{op}"' if op != 1 else '') + '/>')
def C(x, y, r, fill='none', stroke=None, sw=1, dash=None, op=1):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')
            + (f' stroke-dasharray="{dash}"' if dash else '') + (f' opacity="{op}"' if op != 1 else '') + '/>')
def L(x1, y1, x2, y2, stroke=HAIR, sw=1, dash=None, arrow=False):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else '')
            + (' marker-end="url(#arr)"' if arrow else '') + '/>')
def chip(x, y, s, fs=12, stroke=INK, fill='none', color=INK, h=28, pad=12):
    w = tw(s, fs) + 2 * pad
    return R(x, y, w, h, h / 2, fill, stroke, .8) + T(x + w / 2, y + h / 2 + fs * .36, s, fs, fill=color, anchor='middle')[0], w
def defs():
    return ('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M0,1 L9,5 L0,9" fill="none" stroke="{INK}" stroke-width="1.2"/></marker>'
            + ''.join(f'<radialGradient id="g{k}"><stop offset="0" stop-color="#fff"/><stop offset=".2" stop-color="{c}"/>'
                      f'<stop offset=".55" stop-color="{c}" stop-opacity=".3"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
                      f'<radialGradient id="a{k}"><stop offset="0" stop-color="{c}" stop-opacity=".55"/><stop offset=".45" stop-color="{c}" stop-opacity=".16"/>'
                      f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>' for k, c in LV.items())
            + '<linearGradient id="sheet" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".3" stop-color="#fff" stop-opacity=".88"/>'
              '<stop offset="1" stop-color="#fff" stop-opacity=".96"/></linearGradient></defs>')
def legend(x, y):
    out, cx = [], x
    for k, c in LV.items():
        s = f'{k} — {ACT[k]}'; w = tw(s, 11, MONO, .06) + 24
        out += [R(cx, y - 18, w, 26, 0, c), M_(cx + 12, y - 1, s, 11, ON[k])[0]]; cx += w + 6
    return ''.join(out)
def hlblock(x, y, s, fs, color, font=SERIF, ls=-.04, maxw=1e9):
    """flat highlighter block behind a run of text (baseline y)"""
    # deliberately overhangs the text on the right (Room 6x8 style), so font metric differences never clip a word
    return R(x - fs * .12, y - fs * .76, min(maxw, tw(s, fs, font, ls) * 1.1 + fs * .9), fs * .94, 0, color)
def dotgrid(W, H, top, step=80):
    """Aizome-style registration grid: small dots at every crossing, a tick cross every 4th"""
    o = [f'<g id="grid" fill="{INK}" opacity=".32">']
    for gx in range(80, W - 79, step):
        for gy in range(top, H - 79, step):
            o.append(f'<rect x="{gx - 1.2}" y="{gy - 1.2}" width="2.4" height="2.4"/>')
    o.append('</g><g id="ticks" stroke="#0a0a0a" stroke-width="1" opacity=".5">')
    for gx in range(80, W - 79, step * 4):
        for gy in range(top, H - 79, step * 4):
            o.append(f'<path d="M{gx - 7},{gy} H{gx + 7} M{gx},{gy - 7} V{gy + 7}"/>')
    return ''.join(o) + '</g>'
def ticker(W, y, items, h=40, fs=14):
    """black band with repeating coloured words (the 'on air' marquee)"""
    o, x, i = [R(0, y, W, h, 0, INK)], 40, 0
    while x < W - 40:
        s, c = items[i % len(items)]
        if s == '•': o.append(C(x + 4, y + h / 2, 4, c)); x += 26
        else: o.append(T(x, y + h / 2 + fs * .36, s, fs, fill=c, weight=700, ls=.02, up=True)[0]); x += tw(s, fs, SANS, .02) + 18
        i += 1
    return ''.join(o)
TOPTICK = sum([[(s, STC[i]), ('•', LV[k])] for i, (s, k) in enumerate(zip(['Observe', 'Map', 'Assess', 'Alert', 'Evacuate'], ['blue', 'yellow', 'orange', 'red', 'blue']))], [])
BOTTICK = sum([[(k, LV[k]), (ACT[k], '#fff'), ('•', '#555')] for k in LV], [])
def sheet(W, H, no, kicker, title, intro, body, aura='yellow', hl=None, *_):
    """Swiss-signal frame: ticker bands, crosshair dot grid, bold tight headline with one highlighter block,
       an orange oval sheet number, level legend as flat colour blocks"""
    hc = HL.get(aura, HL['yellow']) if aura != 'blue' else HL['green']
    IW = 440; ix = W - 80 - 200 - IW
    tfs, ty = min(92, int((ix - 180) / tw(title, 1, SERIF, -.04))), 214
    hb = ''
    if hl:                                   # one flat block behind the whole headline, starting at the margin
        hb = hlblock(80, ty, title, tfs, hc, maxw=ix - 40 - 80 + tfs * .12)
    ox, oy = W - 80 - 96, 146
    head = [R(0, 0, W, H, 0, BG), dotgrid(W, H, 400), ticker(W, 0, TOPTICK),
            M_(80, 82, PROJECT, 11, INK)[0], M_(W - 80, 82, f'Sheet {no:02d} of 05 — {kicker}', 11, INK, 'end')[0], L(80, 98, W - 80, 98, INK, 1.5),
            hb, T(80, ty, title, tfs, font=SERIF)[0],
            f'<ellipse cx="{ox}" cy="{oy + 34}" rx="96" ry="52" fill="none" stroke="{LV["orange"]}" stroke-width="5"/>',
            T(ox, oy + 58, f'{no:02d}', 68, font=SERIF, anchor='middle', fill=LV['orange'])[0],
            T(ix, 140, intro, 16, w=IW, fill=INK, lh=1.45, weight=500)[0], legend(80, 276),
            L(80, 298, W - 80, 298, INK, 1.5),
            ticker(W, H - 40, BOTTICK, fs=12)]
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{defs()}{"".join(head)}{body}</svg>'

# ------------------------------------------------------------------ 01 · wireframe
PW, PH = 390, 844
def mapart(dim=0):
    o = [R(0, 0, PW, PH, 0, MAP),
         '<path d="M250,844 C220,700 300,600 290,480 C280,380 330,300 300,180 C290,120 320,60 340,0" stroke="#cfdde2" stroke-width="34" fill="none"/>',
         '<path d="M0,300 C120,320 200,360 390,330 M60,0 C90,200 150,420 120,844 M0,620 C140,600 230,640 390,560" stroke="#fff" stroke-width="2.5" fill="none" opacity=".9"/>',
         '<path d="M0,90 C60,60 110,130 150,80 C190,40 170,0 170,0 L0,0 Z M0,700 C50,660 90,720 80,844 L0,844 Z" fill="#d2d9c9"/>']
    for i in range(46): o.append(R((37 * i * 7.3) % 330 + 30, (61 * i * 3.7) % 560 + 120, 9, 7, 1.5, '#d6d2c9'))
    if dim: o.append(R(0, 0, PW, PH, 0, INK, op=dim))
    return ''.join(o)
def statusbar(light=False):
    c = '#fff' if light else INK
    return T(34, 36, '9:41', 15, fill=c, weight=600)[0] + R(PW - 64, 25, 28, 13, 4, 'none', c) + R(128, 828, 134, 5, 3, c)
def levelpill(k='blue', x=20, y=54):
    s = f'{k.capitalize()} · {ACT[k]}'; w = tw(s, 13) + 46
    w -= 20
    return R(x, y, w, 34, 0, LV[k]) + T(x + 13, y + 22, s, 13, fill=ON[k], weight=700)[0]
def mic(cx=195, cy=752, r=36, fill=INK, ring=False):
    o = (C(cx, cy, r + 14, 'none', fill, 1.2, op=.35) if ring else '') + C(cx, cy, r, fill)
    return o + R(cx - 6, cy - 17, 12, 22, 6, '#fff') + f'<path d="M{cx - 11},{cy - 2} a11,11 0 0 0 22,0" stroke="#fff" stroke-width="2" fill="none"/>' + L(cx, cy + 9, cx, cy + 15, '#fff', 2)
def sidebtn(y, label, icon):
    cx = PW - 42
    ic = {'home': f'<path d="M{cx - 9},{y + 2} L{cx},{y - 8} L{cx + 9},{y + 2} L{cx + 9},{y + 10} L{cx - 9},{y + 10} Z" fill="none" stroke="{INK}" stroke-width="1.5"/>',
          'tent': f'<path d="M{cx - 11},{y + 9} L{cx},{y - 9} L{cx + 11},{y + 9} Z M{cx},{y - 9} L{cx},{y + 9}" fill="none" stroke="{INK}" stroke-width="1.5"/>'}[icon]
    return C(cx, y, 22, PAPER, op=.96) + ic + T(cx, y + 38, label, 10, anchor='middle', font=MONO, ls=.06)[0]
def marker(x, y, k, label, verified=True, r=26, count=None):
    o = C(x, y, r, f'url(#g{k})') if verified else C(x, y, r * .55, 'none', '#5d6577', 1.4, '3 3') + C(x, y, 3.5, '#5d6577')
    if count: o += T(x, y + 5, str(count), 14, fill='#fff', weight=700, anchor='middle')[0]
    w = tw(label, 11) + 24
    return o + R(x + r * .7, y - 13, w, 26, 13, PAPER, op=.94) + T(x + r * .7 + 12, y + 4, label, 11)[0]
def btns(y, a, b):
    return (R(32, y, 160, 48, 24, INK) + T(112, y + 30, a, 15, fill='#fff', anchor='middle', weight=500)[0]
            + R(202, y, 156, 48, 24, 'none', INK, .8) + T(280, y + 30, b, 15, anchor='middle')[0])

def s_observe():
    o = [mapart(), statusbar(), levelpill('blue'), sidebtn(76, 'HOME', 'home'), sidebtn(150, 'SHELTER', 'tent'),
         C(195, 410, 36, LV['blue'], LV['blue'], 1, '4 4', op=.16), C(195, 410, 8, LV['blue'], '#fff', 3), M_(195, 466, 'You are here', 10, anchor='middle')[0],
         R(0, 540, PW, 304, 0, 'url(#sheet)'), T(195, 632, 'What do you see?', 40, font=SERIF, anchor='middle')[0],
         M_(195, 656, 'next: What do you hear?', 10, anchor='middle')[0]]
    x = 22
    for s in ['Clouds', 'Muddy water', 'Soil', 'Animals']:
        c, w = chip(x, 674, s); o.append(c); x += w + 7
    return ''.join(o) + mic() + M_(195, 812, 'Hold to talk', 10, anchor='middle')[0]
def s_record():
    o = [mapart(.4), statusbar(True), R(0, 420, PW, 440, 30, PAPER), R(175, 432, 40, 4, 2, HAIR), M_(32, 474, 'Listening…', 10)[0]]
    t, h = T(32, 516, '“The north gully sounds muffled, and the water is turning yellow.”', 27, w=330, font=SERIF, lh=1.15); o.append(t); y = 516 + h
    o += [C(37, y + 2, 4, LV['blue']), M_(49, y + 6, 'North gully mouth · ±15 m · 16:42', 10)[0]]
    y += 26; o.append(M_(32, y + 18, 'Sorted as', 10)[0]); x = 112
    for s in ['Muddy water', 'Sound']:
        c, w = chip(x, y, s, 12, LV['yellow']); o.append(c); x += w + 7
    o.append(T(32, y + 50, 'Matches: “Muffled gully” · Orange', 12, fill=MUTE)[0])
    return ''.join(o) + C(195, 752, 66, 'none', LV['red'], 1, op=.18) + mic(fill=LV['red'], ring=True) + M_(195, 812, 'Release to send · slide up to cancel', 10, anchor='middle')[0]
def s_map():
    o = [mapart(), statusbar(), levelpill('yellow'), M_(20, 116, 'Solid = verified, colour = level · Dashed = unverified', 9)[0],
         marker(110, 250, 'orange', 'Rockfall on slope'), marker(180, 180, 'yellow', 'North gully · 3 · 40 min', r=34, count=3),
         marker(210, 470, 'blue', 'My report · unverified', verified=False), marker(250, 690, 'blue', 'Dragonflies low'),
         R(20, 756, 350, 56, 28, PAPER, op=.96), M_(44, 789, 'Last 6 h', 10, INK)[0], L(120, 784, 340, 784, HAIR, 2), C(300, 784, 8, INK)]
    return ''.join(o)
def s_rule():
    o = [mapart(), statusbar(), marker(240, 180, 'orange', 'North gully', r=34, count=3), R(0, 290, PW, 570, 30, PAPER), R(175, 302, 40, 4, 2, HAIR)]
    c, w = chip(32, 322, 'Flash flood · Verified', 11, LV['orange'], 'none', LV['orange'], 24, 10); o.append(c)
    t, h = T(32, 388, 'Muffled gully. Keep clear of the mouth for 30 minutes.', 28, w=330, font=SERIF, lh=1.1); o.append(t); y = 388 + h + 2
    t, h = M_(32, y, "Villager account · North gully & 300 m of its mouth", 9, w=330); o.append(t); y += h + 18
    for k, s in [('If', 'after heavy rain the gully turns from crisp to muffled, heard from the village gate, and the water yellows'),
                 ('Then', 'alert the gully mouth and low yards, stop crossing, send two people to high ground to re-check the level')]:
        o.append(T(32, y, k, 17, font=SERIF, italic=True, fill=LV['orange'])[0]); t, h = T(82, y, s, 13, w=276, lh=1.5); o.append(t); y += h + 10
    t, h = T(32, y + 14, 'Why — a duller roar and yellow water usually mean more water and silt coming down from upstream.', 13, w=326, fill=MUTE, lh=1.5)
    o += [L(32, y, 358, y, HAIR), t]; y += h + 26
    o.append(M_(32, y, '3 villagers · 40 min · gauge 28 mm/h (sample)', 9)[0])
    return ''.join(o) + btns(760, 'I see it too', 'Not here')
def s_alert():
    o = [mapart(), C(240, 430, 120, 'url(#gorange)'), M_(240, 560, 'North gully · 300 m', 10, LV['orange'], 'middle')[0], statusbar(),
         R(16, 50, 358, 42, 0, LV['orange']), C(38, 71, 5, INK), C(352, 71, 5, INK),
         M_(195, 75, 'Broadcast on air · Orange · Leave the gully', 10, INK, 'middle')[0],
         R(16, 106, 358, 152, 22, PAPER, op=.97), R(30, 122, 32, 32, 8, LV['orange']),
         T(74, 136, "Shenjia'an Alert · Orange", 13, weight=600)[0], T(358, 136, 'now', 12, fill=MUTE, anchor='end')[0]]
    t, h = T(74, 157, 'Muffled north gully. Your home is in the zone — move away from the gully now.', 13, w=282); o.append(t)
    o += [R(74, 212, 92, 30, 15, 'none', INK, .8), T(120, 232, 'Route', 12, anchor='middle')[0], R(174, 212, 92, 30, 15, 'none', INK, .8), T(220, 232, "I'm safe", 12, anchor='middle')[0],
          R(16, 612, 358, 204, 22, PAPER, op=.97), M_(34, 642, 'The same message also goes out via', 9)[0]]
    for i, s in enumerate(['Village loudspeakers · every 10 min', 'Button device · vibrates and speaks', 'Grid workers · door to door', 'SMS · to family members']):
        o += [L(34, 662 + i * 36, 356, 662 + i * 36, HAIR), C(40, 683 + i * 36, 3.5, LV['orange']), T(54, 688 + i * 36, s, 13)[0]]
    return ''.join(o)
def s_route():
    o = [mapart(), statusbar(), levelpill('orange'),
         f'<path d="M92,430 C140,380 120,300 190,270 C250,245 270,190 300,170" stroke="{INK}" stroke-width="4" stroke-dasharray="1.5 8" stroke-linecap="round" fill="none"/>',
         C(92, 430, 9, INK), M_(92, 458, 'Home', 10, INK, 'middle')[0], C(300, 170, 13, PAPER, INK, 1.4),
         f'<path d="M291,177 L300,161 L309,177 Z" fill="{INK}"/>', M_(300, 204, 'Shelter', 10, INK, 'middle')[0],
         R(0, 488, PW, 380, 30, PAPER), R(175, 500, 40, 4, 2, HAIR)]
    y = 548
    o.append(T(32, y, 'To the Village Committee', 28, font=SERIF)[0]); y += 24
    o.append(M_(32, y, '620 m · 18 m up · main road, avoids gully bridge', 9)[0]); y += 52
    o += [T(32, y, '15 min', 44, font=SERIF)[0], T(196, y - 8, 'at 0.7 m/s, pace for age 76', 12, fill=MUTE)[0]]; y += 18
    o += [L(32, y, 358, y, LV['orange'], 1.2), T(32, y + 24, 'Leave now — 10 minutes ahead of others.', 14, fill=LV['orange'], weight=600)[0]]; y += 50
    o.append(M_(32, y, 'At the shelter', 9)[0]); y += 10; x = 32
    for s in ['120 beds', 'Water', 'Medicine', 'Blankets', 'Charging', 'Doctor']:
        c, w = chip(x, y, s, 11, HAIR, 'none', INK, 24, 10)
        if x + w > PW - 30: x = 32; y += 32; c, w = chip(x, y, s, 11, HAIR, 'none', INK, 24, 10)
        o.append(c); x += w + 6
    return ''.join(o) + btns(762, "I'm leaving", 'I need help')
SCREENS = [('Observe', 'Home', s_observe, 'The map is the interface. One button, in thumb reach. Three questions fade in and out — see, hear, feel. The words are only hints; tap one, or just speak.'),
           ('Observe', 'Recording', s_record, 'Hold, speak, release. Time and place are attached automatically, the voice is transcribed and sorted, and the villager only confirms. No signal? It waits on the phone.'),
           ('Map', 'Observations', s_map, 'A solid glow is verified and its colour is the level. A dashed ring is unverified, so it never reads as Blue. Nearby reports merge into one circle with a count.'),
           ('Assess', 'Rule card', s_rule, 'Every circle opens an If / Then card: what the saying means, why it works, how many people confirm it now. This is where the app teaches people to read the land.'),
           ('Alert', 'Broadcast', s_alert, 'Once verified, a broadcast is drafted: a persistent bar in the level colour plus a system alert. The same words go to loudspeakers, button devices, grid workers and SMS.'),
           ('Evacuate', 'My route', s_route, 'Home, age and mobility set the walking pace, so elders get an earlier start. Route, time, and what the shelter holds — one screen.')]
def wireframe():
    G = 64; W = 160 + 6 * PW + 5 * G; top = 360; H = top + PH + 260
    o = []
    for i, (stage, name, fn, note) in enumerate(SCREENS):
        x = 80 + i * (PW + G)
        o += [M_(x, top - 44, f'{i + 1:02d} — {stage}', 11, INK)[0], T(x + PW, top - 40, name, 26, font=SERIF, anchor='end')[0], L(x, top - 26, x + PW, top - 26, INK),
              f'<clipPath id="ph{i}"><rect x="0" y="0" width="{PW}" height="{PH}" rx="46"/></clipPath>',
              f'<g transform="translate({x},{top})"><g clip-path="url(#ph{i})">{fn()}</g>{R(0, 0, PW, PH, 46, "none", INK, 1)}</g>',
              T(x, top + PH + 46, note, 14, w=PW - 10, lh=1.6)[0]]
    return sheet(W, H, 1, 'Wireframe', 'Six screens, one gesture.',
                 'A villager should be able to report what they notice in ten seconds, with one hand, without reading. Everything else — sorting, checking, warning, guiding — happens around that single gesture.',
                 ''.join(o), 'yellow', 'one gesture.')

# ------------------------------------------------------------------ 02 · workflow
STAGES = [('Observe', 'Villagers notice and speak'), ('Map', 'Reports gather by place and time'), ('Assess', 'Rules weigh, people verify'),
          ('Alert', 'One message, every channel'), ('Evacuate', 'Where, when, which way')]
def step(x, y, w, sid, s, no=None, strong=False):
    t, h = T(x + 16, y + 44, s, 14, w=w - 32, lh=1.5, weight=600 if strong else 400, fill='#fff' if strong else INK); hh = h + 44
    o = R(x, y, w, hh, 0, INK if strong else PAPER, INK, 1.2 if strong else .8) + M_(x + 16, y + 22, sid, 9, MUTE)[0] + t
    if no:
        if sid.startswith('◇'): pass
        t2, h2 = T(x + 16, y + hh + 18, no, 12, w=w - 32, fill=MUTE, lh=1.45)
        o += L(x, y + hh, x + w, y + hh, HAIR, 1, '3 4') + R(x, y + hh, w, h2 + 22, 0, TINT, op=.6) + t2; hh += h2 + 22
    return o, hh
def workflow():
    W, top = 1920, 340; cw = (W - 160) / 5; nw = cw - 44
    cols = [[('1.1', 'Villager holds the button in the app and speaks'), ('1.2', 'Elder presses the button device and speaks'), ('1.3', 'Grid worker records on their behalf'),
             ('1.4', 'Speech to text; time and location attached'), ('1.5', 'No signal: kept on the device, sent later')],
            [('2.1', 'Sorted: cloud, water, soil, animal, sound'), ('2.2', 'Matched against the library of sayings and local knowledge'), ('2.3', 'Appears on the map as unverified'),
             ('2.4', 'Same place, same hour: merged into one circle')],
            [('3.1', 'Rule engine scores type × recency × distance × agreement, plus rain gauge, river gauge and weather service'),
             ('◇ 3.2', 'Above threshold?', 'No — stays on the map, keep watching'), ('3.3', 'Grid worker or village official checks in person'),
             ('◇ 3.4', 'Confirmed?', 'No — marked unconfirmed; the reporter is told why'), ('3.5', 'Level set: Blue · Yellow · Orange · Red', None, True)],
            [('4.1', 'Broadcast drafted automatically: level + place + action'), ('4.2', 'Village official confirms with one tap'),
             ('4.3', 'App bar BROADCAST ON AIR + system alert'), ('4.4', 'Village loudspeakers, repeated'), ('4.5', 'Button devices vibrate and speak'),
             ('4.6', 'Grid workers knock on doors, elders first'), ('4.7', 'SMS to family members')],
            [('5.1', 'Departure time from home location, age and mobility'), ('5.2', 'Personal route and shelter details pushed'), ('5.3', 'Check-in at the shelter'),
             ('◇ 5.4', 'Everyone accounted for?', 'No — a grid worker goes to find them'), ('5.5', 'All clear; return home')]]
    o, ends = [], []
    for i, (name, sub) in enumerate(STAGES):
        x = 80 + i * cw
        o += [M_(x, top, f'{i + 1:02d}', 11, INK)[0], hlblock(x, top + 46, name, 40, STC[i]), T(x, top + 46, name, 40, font=SERIF)[0], T(x, top + 74, sub, 13, fill=MUTE)[0]]
        if i: o.append(L(x - 22, top - 10, x - 22, 1100, HAIR))
        y = top + 106
        for k, it in enumerate(cols[i]):
            sid, s = it[0], it[1]; no = it[2] if len(it) > 2 else None; strong = len(it) > 3
            if k and not (i == 3 and k >= 3) and not (i == 0 and k in (1, 2)): o.append(L(x + 24, y - 22, x + 24, y - 3, INK, 1, arrow=True))
            elif k: o.append(L(x + 24, y - 22, x + 24, y, HAIR, 1, '2 3'))
            if i == 3 and k >= 3 or i == 0 and k in (1, 2): pass
            if sid.startswith('◇'): o.append(f'<path d="M{x + nw - 22},{y + 10} l8,8 l-8,8 l-8,-8 z" fill="none" stroke="{INK}" stroke-width="1"/>')
            s2, h = step(x, y, nw, sid.replace('◇ ', ''), s, no, strong); o.append(s2); y += h + 26
        ends.append(y)
    yb = max(ends) + 20; x3, x5 = 80 + 2 * cw + 24, 80 + 4 * cw + 24
    o += [f'<path d="M{x5},{ends[4] - 24} L{x5},{yb + 30} L{x3},{yb + 30} L{x3},{ends[2] - 24}" fill="none" stroke="{INK}" stroke-width="1" stroke-dasharray="4 5" marker-end="url(#arr)"/>',
          M_(x3 + 24, yb + 60, 'Debrief', 10, INK)[0], T(x3 + 24, yb + 84, 'Which saying came true? Rules move from Trial to Verified, or have their thresholds re-tuned.', 15, font=SERIF, w=x5 - x3 - 60)[0]]
    H = int(yb + 200)
    return sheet(W, H, 2, 'Workflow', 'From a hunch to a plan.',
                 'How one spoken observation becomes an action for everyone in the village. A rule engine does the counting; people make the call. Every alert ends in a debrief that teaches the system.',
                 ''.join(o), 'pink', 'a plan.').replace('y2="1100"', f'y2="{yb + 10}"')

# ------------------------------------------------------------------ 03 · user journeys
JOURNEYS = {
  'wang': dict(no='3a', title='Grandma Wang', aura='orange',
    meta='76 · lives alone · north gully mouth · no smartphone · walks ~0.7 m/s',
    intro='One flash-flood afternoon, seen by someone the usual apps leave out. She has no smartphone — only her ears, the old sayings, and a button device around her neck.',
    stages=['Notices', 'Reports', 'Waits', 'Is warned', 'Leaves', 'Shelters, returns'], emo=[-.4, .5, -1, -2, .8, 1.6],
    rows=[('Doing', ['After hours of hard rain she hears the gully go dull and sees the water yellow.', 'Holds the button: “The gully sounds muffled, the water’s yellow.” The light turns green.',
                     'Goes back inside. Ten minutes later a grid worker calls to ask what she saw.', 'The village loudspeaker sounds Orange. Her button device buzzes and speaks.',
                     'A grid worker walks her to the shelter, ten minutes ahead of everyone else.', 'Checks in; there is a bed and her medicine. All clear at night; home.']),
          ('Touchpoints', ['Her ears and eyes · old sayings', 'Button device', 'Phone call · rule engine (unseen)', 'Loudspeaker · button device · SMS to children', 'Grid worker · route · signs', 'Shelter · all-clear broadcast']),
          ('Thinking', ['“That sound is wrong. The old folks said…”', '“Will anyone listen to me?”', '“Am I making a fuss?”', '“It’s real. I’m slow — will I make it?”', '“Someone’s with me. I’m all right.”', '“I’ll report again next time.”']),
          ('Feeling', None),
          ('Pain points', ['Unsure whether it counts', 'Can she report without a phone or reading?', 'Silence while waiting; easy to give up', 'A colour without an action means nothing', 'Slow, and the path is dark', 'No idea when it’s safe to go home']),
          ('Opportunities', ['Saying cards; a radio “observation minute”', 'One button: voice, light, sound', 'Auto call-back: “Received, someone will call”', 'Every broadcast says level, place and action', 'Pace-based early departure; reflective signs', 'All-clear, plus who her report helped'])]),
  'li': dict(no='3b', title='Li Wei, commuter', aura='blue',
    meta='34 · works in Laishui town · drives the river bridge daily · parents and son, 6, in the village',
    intro='The same storm, seen by someone who is away all day. His phone is always on him, but he has no time to look. His worry is not himself — it is the family he left at home.',
    stages=['Notices on the way', 'Reports in 10 s', 'Warned at work', 'Checks on family', 'Reroutes home', 'Reunites, hears back'], emo=[-.3, .6, -.8, -2, -.6, 1.6],
    rows=[('Doing', ['Driving over the Juma River bridge, he sees the water muddier than usual and branches drifting.', 'Parks at work, holds the button: “Muddy water under the bridge, branches.” Adds a photo.',
                     'In a meeting, an alert arrives: Yellow, prepare.', 'Afternoon: Orange. The app shows his mother and son checked in at the shelter. His father has not.',
                     'The gully bridge is closed; the app gives a detour. He asks the grid worker to look in on his father.', 'The family meets at the shelter. Next day: his report was confirmed by three people.']),
          ('Touchpoints', ['His eyes · the commute', 'App voice report · photo', 'Push alert · broadcast bar', 'My Family · shelter check-in', 'Route · call to grid worker', 'Shelter · feedback in the app']),
          ('Thinking', ['“That water doesn’t look right.”', '“One sentence. I can’t be late.”', '“I’m not there. Do they know?”', '“Where is Dad?”', '“Is it safe to drive back? Which way?”', '“So my glance mattered.”']),
          ('Feeling', None),
          ('Pain points', ['Can’t stop to look; can’t say exactly where', 'No time for forms at work', 'Far away and helpless', 'Can’t see who got the alert or who left', 'His way home may cross the danger zone', 'No idea if his report was useful']),
          ('Opportunities', ['Auto location; voice-only while driving', 'One-sentence report, done in ten seconds', 'My Family: their level and where they are', 'Family check-in status; ask a grid worker to visit', 'Routes that follow live road closures', 'Feedback: who confirmed it, who it helped'])]),
}
def journey(key):
    J = JOURNEYS[key]; W = 1920; LW = 230; x0 = 80 + LW; cw = (W - 80 - x0) / 6
    o = [T(80, 352, J['title'], 52, font=SERIF)[0], M_(80, 384, J['meta'], 11, INK)[0], L(80, 410, W - 80, 410, INK)]
    y = 440
    for i, s in enumerate(J['stages']):
        o += [M_(x0 + i * cw, y, f'{i + 1:02d}', 10, MUTE)[0], hlblock(x0 + i * cw, y + 32, s, 22, list(HL.values())[i % 6]), T(x0 + i * cw, y + 32, s, 22, font=SERIF, fill='#fff' if i % 6 == 5 else INK)[0]]
    y += 60; ytop = y
    for name, cells in J['rows']:
        o.append(L(80, y, W - 80, y, HAIR))
        if cells is None:
            hh = 160; o.append(M_(80, y + 28, name, 10, INK)[0]); mid = y + hh / 2
            o += [L(x0, mid, W - 80, mid, HAIR, 1, '2 5'), M_(80, y + 58, 'At ease', 9)[0], M_(80, y + hh - 22, 'Worried', 9)[0]]
            pts = [(x0 + i * cw + 20, mid - e * 30) for i, e in enumerate(J['emo'])]
            d = f'M{pts[0][0]},{pts[0][1]}' + ''.join(f' C{(pts[i - 1][0] + pts[i][0]) / 2},{pts[i - 1][1]} {(pts[i - 1][0] + pts[i][0]) / 2},{pts[i][1]} {pts[i][0]},{pts[i][1]}' for i in range(1, len(pts)))
            lo = min(range(len(pts)), key=lambda i: -pts[i][1] * -1 if False else pts[i][1] * -1)
            lo = max(range(len(pts)), key=lambda i: pts[i][1])
            o += [M_(pts[lo][0] + 16, pts[lo][1] + 4, 'Lowest point', 9, LV['red'])[0], f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="1.4"/>']
            for k, (px, py) in enumerate(pts): o.append(C(px, py, 5 if k != lo else 7, INK if k != lo else LV['red'], BG, 2))
            y += hh; continue
        italic = name == 'Thinking'
        fs, font = 14, SANS
        hs = [T(0, 0, c, fs, w=cw - 40, font=font)[1] for c in cells]; hh = max(hs) + 44
        if name == 'Opportunities': o.append(R(80, y, W - 160, hh, 0, TINT, op=.7))
        o.append(M_(80, y + 30, name, 10, INK)[0])
        for i, c in enumerate(cells):
            cx = x0 + i * cw
            if name == 'Pain points': o.append(C(cx + 3, y + 25, 3, LV['orange']))
            if name == 'Opportunities': o.append(C(cx + 3, y + 25, 3, LV['blue']))
            o.append(T(cx + (14 if name in ('Pain points', 'Opportunities') else 0), y + 30, c, fs, w=cw - 40 - (14 if name in ('Pain points', 'Opportunities') else 0), font=font, lh=1.45, italic=italic, weight=500 if italic else 400)[0])
        y += hh
    o.append(L(80, y, W - 80, y, HAIR))
    for i in range(1, 6): o.append(L(x0 + i * cw - 20, ytop, x0 + i * cw - 20, y, HAIR, 1, '1 4'))
    H = int(y + 160)
    return sheet(W, H, 3, f'Journey {J["no"]}', 'One storm, two lives.', J['intro'], ''.join(o), 'orange', 'two lives.')

# ------------------------------------------------------------------ 04 · service blueprint
def blueprint():
    W = 2200; LW = 260; x0 = 80 + LW; cw = (W - 80 - x0) / 5
    rows = [('Physical evidence', 'What people see and touch', ['Button device · app home · saying cards', 'Glowing circles on the map', 'If / Then rule card', 'Broadcast bar · alert · loudspeaker · SMS', 'Route · signs · shelter supply list']),
            ('Resident actions', 'What villagers do', ['Notices a change, holds the button and speaks', 'Looks at nearby reports, taps “I see it too”', 'Reads the rule card; answers the grid worker’s call', 'Prepares or leaves according to the level', 'Follows the route, checks in at the shelter']),
            ('—', 'Line of interaction', None),
            ('Frontstage', 'What staff and system show', ['App confirms the category; the device lights green and says “received”', 'The map shows unverified circles and merged counts live', 'Grid worker calls or visits to verify', 'App bar + alert; loudspeakers; button devices; door-to-door', 'Personal route and departure time; shelter staff welcome people']),
            ('—', 'Line of visibility', None),
            ('Backstage', 'What happens out of sight', ['Dialect speech-to-text · location · de-duplication', 'Classifier + matching against the sayings library', 'Rule engine scores; a village official decides the level', 'Broadcast drafted automatically; one-tap approval', 'Departure time per household; roll call; find the missing']),
            ('—', 'Line of internal interaction', None),
            ('Support', 'Systems and partners', ['Button devices · 4G / Wi-Fi · offline cache', '3D village map · observation database', 'Rain, river and weather feeds; rule library (Trial / Verified)', 'Loudspeaker system · SMS gateway · push service', 'Household and health data (with consent) · shelter stock · pace table'])]
    o, y = [], 340
    for i, (name, sub) in enumerate(STAGES):
        o += [M_(x0 + i * cw, y, f'{i + 1:02d}', 10)[0], hlblock(x0 + i * cw, y + 40, name, 36, STC[i]), T(x0 + i * cw, y + 40, name, 36, font=SERIF)[0]]
    y += 64; o.append(L(80, y, W - 80, y, INK))
    for name, sub, cells in rows:
        if cells is None:
            o += [L(80, y + 16, W - 80, y + 16, INK, 1, '6 5'), M_(W - 80, y + 6, sub, 9, INK, 'end')[0]]; y += 32; continue
        hs = [T(0, 0, c, 14, w=cw - 48)[1] for c in cells]; hh = max(hs) + 52
        if name == 'Resident actions': o.append(R(80, y, W - 160, hh, 0, TINT, op=.75))
        o += [T(80, y + 36, name, 24, font=SERIF)[0], M_(80, y + 58, sub, 9)[0]]
        for i, c in enumerate(cells): o.append(T(x0 + i * cw, y + 34, c, 14, w=cw - 48, lh=1.5)[0])
        y += hh; o.append(L(80, y, W - 80, y, HAIR))
    for i in range(1, 5): o.append(L(x0 + i * cw - 24, 404, x0 + i * cw - 24, y, HAIR, 1, '1 4'))
    o.append(T(80, y + 44, 'Figures are samples. Age and health data are used only with consent, only to set departure times, and never shown to others.', 13, fill=MUTE)[0])
    H = int(y + 160)
    return sheet(W, H, 4, 'Service blueprint', 'What it takes, behind the glow.',
                 'Above the line of visibility is what villagers meet: a button, a map, a voice on the loudspeaker. Below it are the grid workers, officials, data and partners that make each moment work.',
                 ''.join(o), 'green', 'the glow.')

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for fn, f in [('01 Wireframe', wireframe), ('02 Workflow', workflow), ('03a Journey - Grandma Wang', lambda: journey('wang')),
                  ('03b Journey - Li Wei commuter', lambda: journey('li')), ('04 Service Blueprint', blueprint)]:
        s = f(); open(os.path.join(OUT, fn + '.svg'), 'w', encoding='utf-8').write(s)
        m = re.search(r'width="(\d+)" height="(\d+)"', s); print('wrote', fn, m.group(1), 'x', m.group(2), len(s) // 1024, 'KB')
