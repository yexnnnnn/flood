#!/usr/bin/env python3
"""Community-based Early Warning · system design sheets, English "archive" edition.
   python3 v2/system_design_en.py  ->  v2/figma/system-design-en/*.svg   (drag into Figma; everything stays editable)

   Visual: brushed-aluminium ground, pale blue-white punched paper (Aizome), crosshair dot grid,
   medium grotesk headlines + big numerals, tracked serif small caps with a trailing dash (directory map),
   one orange oval (Kunsthalle).  Level colours appear only where they carry meaning.
   Fonts (Google Fonts, all available in Figma): Inter Tight · Inter · EB Garamond.
"""
import os, re
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figma', 'system-design-en')
GROT = 'Inter Tight, Inter, Helvetica Neue, Arial, sans-serif'
SANS = 'Inter, Helvetica Neue, Arial, sans-serif'
SER = 'EB Garamond, Cormorant Garamond, Times New Roman, serif'
INK, MUTE, FAINT, HAIR = '#111214', '#7d838b', '#b3b8bf', '#cdd2d8'
PAPER, PAPER2, WHITE, MAP = '#f3f5f7', '#e9edf2', '#ffffff', '#e8ebef'
OR = '#ff5a1f'                                                     # the one accent
LV = {'blue': '#2f5bea', 'yellow': '#f2c200', 'orange': OR, 'red': '#e0301e'}
ON = {'blue': WHITE, 'yellow': INK, 'orange': INK, 'red': WHITE}
ACT = {'blue': 'Watch', 'yellow': 'Prepare', 'orange': 'Leave the gully', 'red': 'Evacuate now'}
PROJECT = "CBEWS — Shenjia'an village, Laishui"

# ------------------------------------------------------------------ primitives
_GW = dict(zip('abcdefghijklmnopqrstuvwxyz', [.53, .56, .5, .56, .53, .32, .56, .55, .24, .24, .5, .24, .83, .55, .55, .56, .56, .35, .47, .33, .55, .5, .74, .5, .5, .46]))
_GW.update({' ': .23, ',': .24, '.': .24, "'": .2, '’': .2, '“': .4, '”': .4, '-': .38, '·': .25, 'I': .26, 'M': .8, 'W': .9})
def tw(s, fs, font=SANS, ls=0):
    if font == GROT: return fs * sum(_GW.get(ch, .62 if ch.isupper() else .56) + ls for ch in s)
    if font == SER: return len(s) * fs * (.66 + ls)
    return len(s) * fs * (.55 + ls)
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
def T(x, y, s, fs=13, w=None, fill=INK, font=SANS, weight=None, anchor='start', lh=1.45, ls=None, up=False, italic=False, op=1):
    if font == GROT: weight = weight or 500; ls = -.03 if ls is None else ls; lh = min(lh, 1.08)
    weight = weight or 400; ls = ls or 0
    s = s.upper() if up else s
    lines = wrap(s, fs, w, font, ls) if w else s.split('\n')
    a = (f' letter-spacing="{ls * fs:.2f}"' if ls else '') + (' font-style="italic"' if italic else '') + (f' opacity="{op}"' if op != 1 else '')
    return ''.join(f'<text x="{x:.1f}" y="{y + i * fs * lh:.1f}" font-family="{font}" font-size="{fs}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{a}>{escape(l)}</text>'
                   for i, l in enumerate(lines)), len(lines) * fs * lh
def CAP(x, y, s, fs=10, fill=MUTE, anchor='start', dash=True, w=None):
    """directory-style label: tracked serif small caps with a trailing dash"""
    s = s + (' —' if dash and not s.endswith('—') else '')
    return T(x, y, s, fs, w=w, fill=fill, font=SER, anchor=anchor, ls=.14, up=True, weight=500)
def R(x, y, w, h, r=0, fill='none', stroke=None, sw=1, dash=None, op=1):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"' + (f' rx="{r}"' if r else '') + f' fill="{fill}"'
            + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '') + (f' stroke-dasharray="{dash}"' if dash else '') + (f' opacity="{op}"' if op != 1 else '') + '/>')
def C(x, y, r, fill='none', stroke=None, sw=1, dash=None, op=1):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')
            + (f' stroke-dasharray="{dash}"' if dash else '') + (f' opacity="{op}"' if op != 1 else '') + '/>')
def L(x1, y1, x2, y2, stroke=HAIR, sw=1, dash=None, arrow=False):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else '')
            + (' marker-end="url(#arr)"' if arrow else '') + '/>')
def P(d, fill='none', stroke=INK, sw=1, dash=None, op=1, cap=None):
    return (f'<path d="{d}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '') + (f' stroke-dasharray="{dash}"' if dash else '')
            + (f' stroke-linecap="{cap}"' if cap else '') + (f' opacity="{op}"' if op != 1 else '') + '/>')
def oval(cx, cy, s, fs=10, color=OR, padx=16, h=None):
    """the orange oval tag (Kunsthalle)"""
    w = tw(s.upper(), fs, SER, .14) + 2 * padx; h = h or fs * 2.6
    return (f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w / 2:.1f}" ry="{h / 2:.1f}" fill="none" stroke="{color}" stroke-width="1.4"/>'
            + T(cx, cy + fs * .36, s, fs, fill=color, font=SER, anchor='middle', ls=.14, up=True, weight=500)[0]), w
def chip(x, y, s, fs=11, stroke=INK, color=INK, h=26, pad=10, fill='none'):
    w = tw(s, fs) + 2 * pad
    return R(x, y, w, h, 0, fill, stroke, .8) + T(x + pad, y + h / 2 + fs * .36, s, fs, fill=color)[0], w
def defs():
    return ('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M0,1 L9,5 L0,9" fill="none" stroke="{INK}" stroke-width="1.2"/></marker>'
            '<linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e9eaec"/><stop offset=".45" stop-color="#d3d6da"/>'
            '<stop offset=".7" stop-color="#e2e4e7"/><stop offset="1" stop-color="#c2c6cb"/></linearGradient>'
            + ''.join(f'<radialGradient id="g{k}"><stop offset="0" stop-color="#fff"/><stop offset=".22" stop-color="{c}"/>'
                      f'<stop offset=".6" stop-color="{c}" stop-opacity=".28"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>' for k, c in LV.items())
            + '<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".32" stop-color="#fff" stop-opacity=".9"/>'
              '<stop offset="1" stop-color="#fff" stop-opacity=".97"/></linearGradient></defs>')
def dotgrid(x0, y0, x1, y1, step=80):
    """Aizome registration grid: a dot at every crossing, a short hairline leaving every third one"""
    o = [f'<g id="grid">']
    k = 0
    for gy in range(int(y0), int(y1) + 1, step):
        for gx in range(int(x0), int(x1) + 1, step):
            o.append(f'<rect x="{gx - 1.3}" y="{gy - 1.3}" width="2.6" height="2.6" fill="{INK}" opacity=".5"/>')
            if k % 3 == 0 and gx + step <= x1: o.append(f'<line x1="{gx + 6}" y1="{gy}" x2="{gx + step - 6}" y2="{gy}" stroke="{INK}" stroke-width=".6" opacity=".22"/>')
            if k % 5 == 2 and gy + step <= y1: o.append(f'<line x1="{gx}" y1="{gy + 6}" x2="{gx}" y2="{gy + step - 6}" stroke="{INK}" stroke-width=".6" opacity=".22"/>')
            k += 1
    return ''.join(o) + '</g>'
def holes(x0, x1, y, step=160):
    return ''.join(C(x, y, 6.5, INK) for x in range(int(x0), int(x1) + 1, step))
def legend(x, y):
    o, cx = [], x
    for k, c in LV.items():
        s = f'{k} {ACT[k]}'; o += [R(cx, y - 9, 10, 10, 0, c), CAP(cx + 16, y, s, 9, INK, dash=False)[0]]; cx += 16 + tw(s.upper(), 9, SER, .14) + 26
    return ''.join(o)
def sheet(W, H, no, kicker, title, intro, body, num=None):
    """aluminium ground · punched paper · masthead in serif caps · grotesk headline · (01) numeral · orange oval kicker"""
    num = num or f'({no:02d})'
    nw = tw(num, 150, GROT, -.04); IW = 430; ix = W - 110 - nw - 60 - IW
    tfs = min(78, int((ix - 170) / tw(title, 1, GROT)))
    ov, ow = oval(0, 0, kicker, 11)
    head = [R(0, 0, W, H, 0, 'url(#metal)'), R(36, 36, W - 72, H - 72, 0, PAPER, '#b9bec5', 1),
            holes(116, W - 116, 64), holes(116, W - 116, H - 64),
            dotgrid(110, 400, W - 110, H - 110),
            CAP(110, 116, PROJECT, 10, INK)[0], CAP(W - 110, 116, f'Sheet {no:02d} / 05', 10, INK, 'end')[0], L(110, 130, W - 110, 130, INK, .8),
            T(110, 236, title, tfs, font=GROT)[0],
            f'<g transform="translate({110 + ow / 2:.1f},{290})">{ov}</g>', legend(110 + ow + 34, 294),
            T(W - 110, 262, num, 150, font=GROT, weight=300, anchor='end', ls=-.04)[0],
            T(ix, 170, intro, 14, w=IW, lh=1.5)[0],
            L(110, 336, W - 110, 336, INK, .8),
            CAP(110, H - 92, 'Community-based Early Warning System · 2026', 9)[0],
            CAP(W - 110, H - 92, 'Observe · Map · Assess · Alert · Evacuate', 9, anchor='end')[0]]
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{defs()}{"".join(head)}{body}</svg>'

# ------------------------------------------------------------------ phone UI pieces
PW, PH = 390, 844
def iso_house(x, y, s=7, h=6, top='#ffffff', l='#d9dee5', r='#c9d0d9'):
    a, b = s * .866, s * .5
    return (P(f'M{x},{y - h} l{a},{b} l{-a},{b} l{-a},{-b} z', top, '#aeb6c0', .5)
            + P(f'M{x - a},{y - h + b} l{a},{b} v{h} l{-a},{-b} z', l, '#aeb6c0', .5)
            + P(f'M{x},{y - h + 2 * b} l{a},{-b} v{h} l{-a},{b} z', r, '#aeb6c0', .5))
def mapart(dim=0, h=PH):
    """stand-in for the Shenjia'an 3D model: contour hills, river, roads, isometric houses"""
    o = [R(0, 0, PW, h, 0, MAP)]
    for i, k in enumerate([0, 1, 2, 3]):
        o.append(P(f'M-20,{120 + k * 26} C80,{70 + k * 30} 160,{150 + k * 22} 260,{90 + k * 30} S380,{40 + k * 26} 420,{70 + k * 26}', 'none', '#cfd5dc', 1))
    o += [P('M250,900 C220,700 300,600 290,480 C280,380 330,300 300,180 C290,120 320,60 340,-20', 'none', '#cfdbe6', 30),
          P('M250,900 C220,700 300,600 290,480 C280,380 330,300 300,180 C290,120 320,60 340,-20', 'none', '#bccbd9', 1),
          P('M-10,300 C120,320 200,360 400,330 M60,-10 C90,200 150,420 120,900 M-10,620 C140,600 230,640 400,560', 'none', WHITE, 3)]
    for i in range(54):
        x = (37 * i * 7.3) % 320 + 36; y = (61 * i * 3.7) % 600 + 130
        if y < h - 10 and abs(x - (290 if y > 300 else 310)) > 26: o.append(iso_house(x, y))
    if dim: o.append(R(0, 0, PW, h, 0, INK, op=dim))
    return ''.join(o)
def statusbar(light=False):
    c = WHITE if light else INK
    return T(34, 36, '9:41', 15, fill=c, weight=600)[0] + R(PW - 64, 25, 28, 13, 3, 'none', c) + R(128, 828, 134, 5, 3, c)
def lvtag(k, x, y):
    s = f'{k.capitalize()} · {ACT[k]}'; w = tw(s, 12, ls=0) + 26
    return R(x, y, w, 28, 0, LV[k]) + T(x + 13, y + 19, s, 12, fill=ON[k], weight=600)[0]
def mic(cx=195, cy=760, r=34, fill=INK, ring=False):
    o = (C(cx, cy, r + 14, 'none', fill, 1, op=.35) if ring else '') + C(cx, cy, r, fill)
    return o + R(cx - 6, cy - 16, 12, 21, 6, WHITE) + P(f'M{cx - 11},{cy - 2} a11,11 0 0 0 22,0', 'none', WHITE, 2) + L(cx, cy + 9, cx, cy + 15, WHITE, 2)
def icon(kind, cx, y, c=INK):
    return {'home': P(f'M{cx - 9},{y + 2} L{cx},{y - 8} L{cx + 9},{y + 2} L{cx + 9},{y + 10} L{cx - 9},{y + 10} Z', 'none', c, 1.4),
            'tent': P(f'M{cx - 11},{y + 9} L{cx},{y - 9} L{cx + 11},{y + 9} Z M{cx},{y - 9} L{cx},{y + 9}', 'none', c, 1.4),
            'air': P(f'M{cx - 8},{y - 4} h5 l7,-6 v20 l-7,-6 h-5 z M{cx + 7},{y - 5} q5,5 0,10', 'none', c, 1.4)}[kind]
def bubble(cx, cy, kind, label, ring=INK, fill=WHITE, ic=INK):
    """the persistent map bubbles: a white circle on the map, a serif-caps name under it"""
    w = tw(label.upper(), 8.5, SER, .14) + 14
    return (C(cx, cy, 23, fill, ring, 1) + icon(kind, cx, cy - 1, ic) + R(cx - w / 2, cy + 29, w, 16, 0, WHITE, op=.92)
            + CAP(cx, cy + 40, label, 8.5, INK, 'middle', dash=False)[0])
def marker(x, y, k, label=None, verified=True, r=24, count=None):
    o = C(x, y, r, f'url(#g{k})') if verified else C(x, y, r * .55, 'none', '#5d6577', 1.3, '3 3') + C(x, y, 3.2, '#5d6577')
    if count: o += T(x, y + 5, str(count), 13, fill=WHITE, weight=700, anchor='middle')[0]
    if label:
        w = tw(label, 10.5) + 20; o += R(x + r * .7, y - 12, w, 24, 0, WHITE, op=.94) + T(x + r * .7 + 10, y + 4, label, 10.5)[0]
    return o
def btns(y, a, b=None, x0=24, x1=366):
    if not b: return R(x0, y, x1 - x0, 46, 0, INK) + T((x0 + x1) / 2, y + 29, a, 14, fill=WHITE, anchor='middle', weight=500)[0]
    w = (x1 - x0 - 6) / 2
    return (R(x0, y, w, 46, 0, INK) + T(x0 + w / 2, y + 29, a, 14, fill=WHITE, anchor='middle', weight=500)[0]
            + R(x0 + w + 6, y, w, 46, 0, WHITE, INK, .8) + T(x1 - w / 2, y + 29, b, 14, anchor='middle')[0])
def sheet_up(y, h=None):
    return R(0, y, PW, (h or PH - y) + 40, 0, WHITE) + L(0, y, PW, y, INK, .8) + R(175, y + 10, 40, 3, 0, FAINT)
def chev(x, y):
    return P(f'M{x - 12},{y} H{x} M{x - 4},{y - 4} L{x},{y} L{x - 4},{y + 4}', 'none', INK, 1.1)
def row(y, k, v, x2=118, w=240, fs=12.5, arrow=False, vfill=INK):
    t, h = T(x2, y, v, fs, w=w, fill=vfill)
    return CAP(24, y, k, 9, MUTE, dash=False)[0] + t + (chev(366, y - 4) if arrow else ''), h

# ------------------------------------------------------------------ 01 · wireframe (8 screens)
def s_home():
    o = [mapart(), statusbar(),
         R(16, 52, 358, 196, 0, WHITE, INK, .8), CAP(32, 78, 'Village status')[0], T(358, 78, '10:32', 10.5, fill=MUTE, anchor='end')[0],
         R(32, 92, 10, 10, 0, LV['blue']), T(48, 101, 'Blue · Watch', 12, fill=LV['blue'], weight=600)[0],
         T(32, 140, 'Normal watch', 30, font=GROT)[0], T(32, 160, 'Sample · source: community observations', 10.5, fill=MUTE)[0],
         T(32, 184, 'No village-wide evacuation notice. Keep watching the weather and the river.', 12, w=320)[0],
         L(32, 214, 358, 214, HAIR), T(32, 236, 'What should I do now?', 12, weight=600)[0], chev(358, 232),
         CAP(20, 272, '3D view', 9, INK)[0],
         marker(250, 478, 'yellow', None, r=18), marker(138, 528, 'blue', None, verified=False),
         C(182, 430, 30, LV['blue'], op=.14), C(182, 430, 7, LV['blue'], WHITE, 3), CAP(182, 456, 'You', 8.5, INK, 'middle', dash=False)[0],
         bubble(96, 372, 'home', 'My household'), bubble(306, 326, 'tent', 'Shelters'),
         R(0, 570, PW, 280, 0, 'url(#fade)'), T(195, 652, 'What do you see?', 32, font=GROT, anchor='middle')[0],
         CAP(195, 676, 'next — what do you hear?', 8.5, anchor='middle', dash=False)[0]]
    x = 24
    for s in ['Clouds', 'Muddy water', 'Soil', 'Animals']:
        c, w = chip(x, 692, s); o.append(c); x += w + 6
    return ''.join(o) + mic() + CAP(195, 812, 'Hold to talk', 8.5, anchor='middle', dash=False)[0]
def s_confirm():
    o = [mapart(.35), statusbar(True), sheet_up(250), CAP(24, 292, 'You said')[0]]
    t, h = T(24, 326, '“The river is much muddier than this morning.”', 24, w=290, font=GROT); o.append(t)
    y = 326 + h + 12; o += [L(24, y, 366, y, INK, .8)]
    ov, ow = oval(0, 0, 'pending your ok', 8.5, padx=10, h=20)
    o += [CAP(24, y + 26, 'Detected observation', 9, INK)[0], f'<g transform="translate({366 - ow / 2:.1f},{y + 23})">{ov}</g>']
    y += 56
    for k, v in [('What', 'River colour: clear, now muddy'), ('Time', 'Recorded automatically · 10:41'), ('Place', 'Approximate · tap map to adjust'), ('Type', 'Water')]:
        r_, h = row(y, k, v); o += [r_, L(24, y + 16, 366, y + 16, HAIR)]; y += 40
    t, h = T(24, y + 14, 'Only what you said is recorded. The app sorts it; it never adds what you did not report.', 11.5, w=340, fill=MUTE); o.append(t); y += h + 24
    for i, s in enumerate(['+ Photo', '+ Sound', '+ Note']):
        o += [R(24 + i * 116, y, 110, 44, 0, 'none', INK, .8, '3 3'), T(79 + i * 116, y + 27, s, 12, anchor='middle')[0]]
    return ''.join(o) + btns(764, 'Confirm & upload', 'Edit')
def s_observation():
    o = [mapart(h=300), statusbar(), marker(240, 170, 'orange', 'North gully', r=32, count=3), marker(110, 230, 'blue', None, verified=False), sheet_up(280)]
    ov, ow = oval(0, 0, 'verifying', 8.5, padx=10, h=20)
    o += [CAP(24, 318, 'Observation')[0], f'<g transform="translate({366 - ow / 2:.1f},{315})">{ov}</g>']
    t, h = T(24, 356, 'The north gully sounds muffled; the water is yellow.', 22, w=290, font=GROT); o.append(t); y = 356 + h
    o.append(T(24, y + 2, '3 villagers · 40 min · 1 photo · 2 recordings', 11, fill=MUTE)[0]); y += 18
    o += [R(24, y, 160, 82, 0, PAPER2), P(f'M24,{y} L184,{y + 82} M184,{y} L24,{y + 82}', 'none', FAINT, .8), CAP(32, y + 76, 'Photo', 8, MUTE, dash=False)[0],
          R(190, y, 176, 82, 0, PAPER2)]
    for i in range(26):
        hh = 8 + (i * 37 % 11) * 4; o.append(R(200 + i * 6.2, y + 41 - hh / 2, 3, hh, 0, INK))
    y += 106; o += [L(24, y - 10, 366, y - 10, INK, .8), CAP(24, y + 8, 'What the old saying means', 9, INK)[0]]; y += 30
    for k, s in [('If', 'after heavy rain the gully goes from crisp to muffled and the water yellows'),
                 ('Then', 'keep clear of the gully mouth; two people re-check from high ground')]:
        o.append(T(24, y, k, 14, font=GROT, fill=OR)[0]); t, h = T(72, y, s, 12, w=290); o.append(t); y += h + 8
    t, h = T(24, y + 4, 'Why — a duller roar and yellow water usually mean more water and silt coming from upstream.', 11.5, w=340, fill=MUTE); o.append(t)
    return ''.join(o) + btns(764, 'I see it too', 'Not here')
def s_action():
    o = [mapart(), C(250, 600, 130, 'url(#gorange)'), statusbar(),
         R(0, 50, PW, 36, 0, OR), C(22, 68, 4, INK), CAP(195, 72, 'Broadcast on air · orange · leave the gully', 9, INK, 'middle', dash=False)[0],
         R(16, 96, 358, 724, 0, WHITE, INK, .8), CAP(32, 124, 'Action center')[0],
         T(32, 162, 'Leave the gully now.', 28, font=GROT)[0], L(32, 182, 358, 182, INK, .8)]
    y = 202
    for sq, k, v, note in [(('none', INK), 'Community notice', "Shenjia'an village committee · 15:20 · from 3 verified reports", 'Not an official warning'),
                           ((INK, None), 'Official warning', 'Laishui County Meteorological Bureau · orange rainstorm · 14:50 (sample)', 'Original level and issuer shown as published')]:
        o += [R(32, y - 9, 10, 10, 0, sq[0], sq[1], 1), CAP(50, y, k, 9, INK, dash=False)[0]]
        t, h = T(50, y + 18, v, 11.5, w=300); o.append(t); o.append(T(50, y + 18 + h, note, 10.5, fill=MUTE)[0]); y += h + 46
    o.append(L(32, y - 10, 358, y - 10, HAIR))
    for k, v in [('Why', 'Muffled gully, yellow water; rain 28 mm/h'), ('Area', 'North gully and 300 m of its mouth'), ('Do now', 'Leave the gully. Do not cross the bridge.'),
                 ('Family', 'Grandma needs someone to walk with her'), ('Shelter', 'North village shelter · 23 min'), ('Route', 'Via the Village Committee, uphill')]:
        t, h = T(112, y + 14, v, 12, w=220); o += [CAP(32, y + 14, k, 9, MUTE, dash=False)[0], t, chev(358, y + 10)]; y += max(h, 18) + 20
        o.append(L(32, y - 4, 358, y - 4, HAIR))
    return ''.join(o) + btns(752, "I've received it", 'Show route', 32, 358)
def s_household():
    o = [mapart(h=230), statusbar(), C(150, 150, 34, LV['blue'], op=.12), bubble(150, 140, 'home', 'Home · approx.'), sheet_up(212)]
    o += [CAP(24, 250, 'My household')[0], T(366, 250, 'updated 10:30', 10.5, fill=MUTE, anchor='end')[0], T(24, 288, 'Who needs what', 24, font=GROT)[0]]
    y = 314
    for nm, sub, st, c in [('Me', 'Walks on my own · 1.1 m/s', 'Notified', INK), ('Grandma Wang, 76', 'Needs a companion · 0.7 m/s', 'Needs pickup', OR), ('Xiaoyu, 6', 'Goes with grandma', 'Arrived', INK)]:
        o += [L(24, y, 366, y, HAIR), T(24, y + 22, nm, 13.5, weight=600)[0], T(24, y + 39, sub, 11, fill=MUTE)[0], T(366, y + 22, st, 11.5, fill=c, anchor='end', weight=600 if c == OR else 400)[0]]; y += 52
    o += [L(24, y, 366, y, INK, .8), CAP(24, y + 24, 'My evacuation time', 9, INK)[0], T(24, y + 72, '23 min', 42, font=GROT)[0]]
    for i, s in enumerate(['620 m route · 18 m climb · 40 steps', '+ 5 min waiting for a companion', '+ 5 min safety margin']):
        o.append(T(176, y + 46 + i * 15, s, 10.5, fill=MUTE)[0])
    o.append(T(24, y + 96, 'An estimate, not a guaranteed latest time to leave.', 11, fill=OR)[0]); y += 116
    o += [L(24, y, 366, y, INK, .8), CAP(24, y + 24, 'Safety plan', 9, INK)[0]]; y += 46
    for k, v in [('Nearest', 'North village shelter'), ('Backup', 'West terrace path'), ('Contact', 'Li Wei · son'), ('Meet at', 'Village Committee gate')]:
        o += [CAP(24, y, k, 9, MUTE, dash=False)[0], T(118, y, v, 12)[0]]; y += 24
    o.append(T(24, y + 6, 'Family locations are shared only with their consent.', 10.5, fill=MUTE)[0])
    return ''.join(o) + btns(772, 'My plan', 'Edit household')
def s_shelters():
    o = [mapart(h=290), statusbar(), C(110, 210, 7, LV['blue'], WHITE, 3)]
    for n, x, y in [(1, 300, 120), (2, 90, 70)]:
        o += [C(x, y, 15, INK), T(x, y + 5, str(n), 13, fill=WHITE, anchor='middle', weight=600)[0]]
    o += [P('M110,210 C160,190 200,150 300,120', 'none', INK, 1.4, '1.5 6', cap='round'), sheet_up(270), CAP(24, 308, 'Safe shelters')[0]]
    t, h = T(24, 330, 'Ranked by: confirmed safe · open · has room · fits your mobility · passable route', 11, w=340, fill=MUTE); o.append(t); y = 330 + h + 4
    for n, nm, st, lines, note in [(1, 'North village shelter', 'Open — to confirm', ['620 m · 23 min at your pace', 'Water · toilets · rest area'], 'Accessibility to be verified'),
                                   (2, 'South community shelter', 'Status to confirm', ['1.1 km · 31 min · crosses the gully bridge', 'First aid · charging · rest area'], 'Capacity to be verified')]:
        o += [L(24, y, 366, y, INK, .8), T(24, y + 54, str(n), 48, font=GROT, weight=300)[0], T(72, y + 26, nm, 15, weight=600)[0]]
        ov, ow = oval(0, 0, st, 8, padx=8, h=18); o.append(f'<g transform="translate({72 + ow / 2:.1f},{y + 46})">{ov}</g>')
        for i, s in enumerate(lines): o.append(T(72, y + 76 + i * 18, s, 12, fill=INK if i == 0 else MUTE)[0])
        if n == 2: o.append(R(72, y + 66, tw(lines[0], 12) + 4, 14, 0, LV['red'], op=.12))
        o.append(T(72, y + 120, note, 10.5, fill=FAINT)[0]); y += 140
    o.append(CAP(24, y + 18, 'Sample data — verify before deployment', 8.5, dash=False)[0])
    return ''.join(o) + btns(764, 'Details', 'Route')
def iso(u, v, z=0, ox=162, oy=196, s=19):
    return ox + (u - v) * .866 * s, oy + (u + v) * .5 * s - z
def poly(pts, fill, stroke=INK, sw=.9):
    return P('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + ' Z', fill, stroke, sw)
def s_shelter():
    o = [R(0, 0, PW, PH, 0, WHITE), statusbar(), CAP(24, 82, 'Shelter details')[0], T(24, 118, 'North village shelter', 25, font=GROT)[0],
         T(24, 138, 'Entrance · inside · what is where', 11, fill=MUTE)[0]]
    H = 28
    o += [poly([iso(0, 0, H), iso(10, 0, H), iso(10, 0), iso(0, 0)], '#e3e7ec'), poly([iso(0, 0, H), iso(0, 6, H), iso(0, 6), iso(0, 0)], '#d5dbe2'),
          poly([iso(0, 0), iso(10, 0), iso(10, 6), iso(0, 6)], WHITE)]
    for (u1, v1, u2, v2) in [(4, 0, 4, 6), (4, 3, 10, 3), (7, 3, 7, 6)]:
        a, b, c, d = iso(u1, v1), iso(u2, v2), iso(u2, v2, 10), iso(u1, v1, 10); o.append(poly([a, b, c, d], '#eef1f4', INK, .7))
    o += [poly([iso(1, 6), iso(2.6, 6), iso(2.6, 8.4), iso(1, 8.4)], '#eef1f4', INK, .9),
          P(' '.join(f'M{iso(1, 6 + k * .6)[0]:.1f},{iso(1, 6 + k * .6)[1]:.1f} L{iso(2.6, 6 + k * .6)[0]:.1f},{iso(2.6, 6 + k * .6)[1]:.1f}' for k in range(1, 4)), 'none', INK, .5)]
    labs = ['Entrance · ramp', 'Rest · 80 beds', 'Water & food', 'Toilets', 'First aid']
    for n, (u, v) in enumerate([(1.8, 7.6), (2, 3), (7, 1.5), (5.5, 4.5), (8.5, 4.5)], 1):
        x, y = iso(u, v); o += [C(x, y, 8.5, INK), T(x, y + 3.5, str(n), 9.5, fill=WHITE, anchor='middle', weight=600)[0]]
    for n, lab in enumerate(labs, 1):
        lx, ly = 24 + ((n - 1) % 3) * 118, 392 + ((n - 1) // 3) * 22
        o += [C(lx + 7, ly - 4, 7, INK), T(lx + 7, ly - .5, str(n), 8.5, fill=WHITE, anchor='middle', weight=600)[0], T(lx + 20, ly, lab, 10.5)[0]]
    y = 436; o.append(L(24, y, 366, y, INK, .8)); o.append(CAP(24, y + 22, "What's inside", 9, INK)[0]); y += 36
    tiles = [('Drinking water', '400 L · updated 20 Oct'), ('Food', 'For 120 people · 2 days'), ('First aid', '2 kits · nurse on call'),
             ('Rest', '80 beds · blankets'), ('Accessible', 'Ramp · 1 toilet'), ('Power & comms', 'Charging · backup power')]
    for i, (k, v) in enumerate(tiles):
        tx, ty = 24 + (i % 2) * 174, y + (i // 2) * 78
        o += [R(tx, ty, 168, 72, 0, 'none', INK, .7), CAP(tx + 12, ty + 22, k, 8.5, INK, dash=False)[0], T(tx + 12, ty + 48, v, 11.5, w=148)[0]]
    o.append(T(24, y + 254, 'Sample figures. Stock and capacity are updated by shelter staff.', 10.5, fill=MUTE)[0])
    return ''.join(o) + btns(764, 'Inside map', 'How to get there')
def s_route():
    o = [mapart(h=500), statusbar(), lvtag('orange', 16, 50)]
    pts = [(86, 430), (150, 380), (190, 300), (250, 240), (300, 170)]
    o.append(P('M' + ' L'.join(f'{x},{y}' for x, y in pts), 'none', INK, 4, '1.5 8', cap='round'))
    o.append(P('M86,430 C40,360 60,250 130,200 C190,160 250,140 300,170', 'none', MUTE, 1.2, '5 5'))
    o += [L(214, 404, 230, 420, LV['red'], 2.4), L(230, 404, 214, 420, LV['red'], 2.4), T(240, 418, 'Bridge closed', 10, fill=LV['red'])[0]]
    for n, (x, y) in enumerate(pts, 1):
        o += [C(x, y, 10, WHITE if n < 5 else INK, INK, 1.2), T(x, y + 4, str(n), 10, fill=INK if n < 5 else WHITE, anchor='middle', weight=600)[0]]
    o += [T(66, 460, 'Home', 10, weight=600)[0], T(316, 160, 'Shelter', 10, weight=600)[0], sheet_up(480), CAP(24, 518, 'How to get there')[0],
          T(24, 556, '23 min · 620 m', 27, font=GROT)[0], T(24, 576, 'At your pace, incl. 5 min margin · an estimate', 11, fill=MUTE)[0]]
    y = 604
    for n, s in enumerate(['From your door, turn left', 'North along the east road', 'Turn left at the Village Committee', 'Uphill, away from the river', 'Shelter entrance · ramp on the right'], 1):
        o += [C(34, y - 4, 9, 'none', INK, .8), T(34, y, str(n), 9.5, anchor='middle', weight=600)[0], T(54, y, s, 12.5)[0]]; y += 26
    c1, w1 = chip(24, y - 6, 'Gully bridge · closed', 10, LV['red'], LV['red'], 22, 8); c2, w2 = chip(24 + w1 + 6, y - 6, 'Slope · muddy, to verify', 10, INK, INK, 22, 8)
    return ''.join(o) + c1 + c2 + btns(772, "I'm leaving", 'Backup route')
SCREENS = [('Home', 'Status · map · voice', s_home, 'Answers “what is happening now”. Village status on top with one link to what to do; the 3D village in the middle; two bubbles that never move (My household, Shelters); the voice button at the thumb.'),
           ('Observe', 'Say it, then confirm', s_confirm, 'Hold, speak, release. The app drafts a structured observation, but the villager confirms it. It records only what was said: “muddier” never becomes “rising fast”.'),
           ('Map', 'Observation', s_observation, 'Tap any circle on the map. Solid glow = verified, colour = level; dashed ring = unverified. The old saying, and why it works, lives here, not on the home page.'),
           ('Alert', 'Action center', s_action, 'The status card opens this. Community notices and official warnings are labelled apart, with issuer and time. Then: why, where, what to do, who needs help, where to go.'),
           ('Evacuate', 'My household', s_household, 'Useful on a dry day too: who lives here, who needs a companion, how long leaving takes and why, and the family plan. Locations are shared only with consent.'),
           ('Evacuate', 'Shelters', s_shelters, 'Not sorted by distance alone: confirmed safe, open, has room, fits your mobility, reachable on a passable route. Every unknown is shown as unknown.'),
           ('Evacuate', 'Inside the shelter', s_shelter, 'One axonometric drawing, not indoor navigation: where to enter, where the water, toilets, beds and first aid are, and which parts suit people who move slowly.'),
           ('Evacuate', 'How to get there', s_route, 'Landmarks instead of compass directions: “turn left at the Village Committee” is easier than “go 200 m north”. Closed roads, a backup route, time at your own pace.')]
def wireframe():
    G = 56; W = 220 + 8 * PW + 7 * G; top = 430; H = top + PH + 290
    o = []
    for i, (stage, name, fn, note) in enumerate(SCREENS):
        x = 110 + i * (PW + G)
        o += [CAP(x, top - 52, f'{i + 1:02d} {stage}', 9.5, INK)[0], T(x + PW, top - 46, name, 20, font=GROT, anchor='end')[0], L(x, top - 34, x + PW, top - 34, INK, .8),
              f'<clipPath id="ph{i}"><rect x="0" y="0" width="{PW}" height="{PH}" rx="46"/></clipPath>',
              f'<g id="screen-{i + 1:02d}" transform="translate({x},{top})"><g clip-path="url(#ph{i})">{fn()}</g>{R(0, 0, PW, PH, 46, "none", INK, 1.2)}</g>',
              T(x, top + PH + 44, note, 12.5, w=PW - 6, lh=1.55)[0]]
    return sheet(W, H, 1, 'Wireframe', 'Say what changed. Know where to go.',
                 'Not an app for reading disaster data. A community service where villagers report changes in nature by voice, read their village on a map, and know when to prepare, when to leave, and where to go. '
                 'The home page answers “what is happening now”; a bubble answers “what it means for me”; the next page answers “what do I do”.',
                 ''.join(o), '(8)')

# ------------------------------------------------------------------ 02 · workflow
STAGES = [('Observe', 'Villagers notice and speak'), ('Map', 'Reports gather by place and time'), ('Assess', 'Rules weigh, people verify'),
          ('Alert', 'One message, every channel'), ('Evacuate', 'Where, when, which way')]
def step(x, y, w, sid, s, no=None, strong=False):
    t, h = T(x + 16, y + 44, s, 13, w=w - 32, lh=1.5, weight=600 if strong else 400, fill=WHITE if strong else INK); hh = h + 40
    o = R(x, y, w, hh, 0, INK if strong else WHITE, INK, .8) + CAP(x + 16, y + 22, sid, 8.5, FAINT if strong else MUTE, dash=False)[0] + t
    if no:
        t2, h2 = T(x + 16, y + hh + 20, no, 11.5, w=w - 32, fill=MUTE, lh=1.45)
        o += R(x, y + hh, w, h2 + 22, 0, PAPER2, INK, .8, '2 3') + t2; hh += h2 + 22
    return o, hh
def workflow():
    W, top = 1960, 410; cw = (W - 220) / 5; nw = cw - 40
    cols = [[('1.1', 'Villager holds the button in the app and speaks'), ('1.2', 'Elder presses the button device and speaks'), ('1.3', 'Grid worker records on their behalf'),
             ('1.4', 'Speech to text; the app drafts what, when, where, type'), ('1.5', 'Villager confirms; nothing is added that was not said'), ('1.6', 'No signal: kept on the device, sent later')],
            [('2.1', 'Sorted: cloud, water, soil, animal, sound'), ('2.2', 'Matched against the library of sayings and local knowledge'), ('2.3', 'Appears on the map as unverified'),
             ('2.4', 'Same place, same hour: merged into one circle')],
            [('3.1', 'Rule engine scores type × recency × distance × agreement, plus rain gauge, river gauge and weather service'),
             ('◇ 3.2', 'Above threshold?', 'No — stays on the map, keep watching'), ('3.3', 'Grid worker or village official checks in person'),
             ('◇ 3.4', 'Confirmed?', 'No — marked unconfirmed; the reporter is told why'), ('3.5', 'Community level set: Blue · Yellow · Orange · Red', None, True)],
            [('4.1', 'Notice drafted: level + place + action, labelled “community notice”'), ('4.2', 'Village official confirms with one tap'),
             ('4.3', 'Official warnings shown separately, with issuer, original level and time'), ('4.4', 'Status card + broadcast bar + system alert; Action center opens'),
             ('4.5', 'Loudspeakers · button devices · grid workers door to door · SMS'), ('4.6', 'Each household confirms receipt; no reply, a grid worker calls')],
            [('5.1', 'Time to leave per household: route, climb, steps, companion, margin'), ('5.2', 'Shelters ranked: safe, open, room, fits mobility, passable route'),
             ('5.3', 'Landmark route pushed; closed roads swap to the backup'), ('5.4', 'Check-in at the shelter; family sees “arrived”'),
             ('◇ 5.5', 'Everyone accounted for?', 'No — a grid worker goes to find them'), ('5.6', 'All clear; return home')]]
    o, ends = [], []
    for i, (name, sub) in enumerate(STAGES):
        x = 110 + i * cw
        o += [T(x, top + 4, f'{i + 1:02d}', 64, font=GROT, weight=300)[0], T(x + 92, top - 22, name, 30, font=GROT)[0], CAP(x + 92, top + 2, sub, 8.5, dash=False)[0]]
        if i: o.append(L(x - 20, top - 60, x - 20, 1300, HAIR))
        y = top + 40
        for k, it in enumerate(cols[i]):
            sid, s = it[0], it[1]; no = it[2] if len(it) > 2 else None; strong = len(it) > 3
            if k: o.append(L(x + 24, y - 22, x + 24, y - 3, INK, .9, arrow=True))
            if sid.startswith('◇'): o.append(P(f'M{x + nw - 22},{y + 10} l8,8 l-8,8 l-8,-8 z', 'none', OR, 1.2))
            s2, h = step(x, y, nw, sid.replace('◇ ', ''), s, no, strong); o.append(s2); y += h + 26
        ends.append(y)
    yb = max(ends) + 20; x3, x5 = 110 + 2 * cw + 24, 110 + 4 * cw + 24
    o += [f'<path d="M{x5},{ends[4] - 24} L{x5},{yb + 30} L{x3},{yb + 30} L{x3},{ends[2] - 24}" fill="none" stroke="{OR}" stroke-width="1.2" stroke-dasharray="4 5" marker-end="url(#arr)"/>']
    ov, ow = oval(0, 0, 'debrief', 10)
    o += [f'<g transform="translate({x3 + 24 + ow / 2:.1f},{yb + 64})">{ov}</g>',
          T(x3 + 24 + ow + 20, yb + 72, 'Which saying came true? Rules move from Trial to Verified, or have their thresholds re-tuned.', 16, font=GROT, w=x5 - x3 - ow - 80)[0]]
    H = int(yb + 220)
    return sheet(W, H, 2, 'Workflow', 'From a hunch to a plan.',
                 'How one spoken observation becomes an action for everyone in the village. A rule engine does the counting; people make the call. Community notices never pose as official warnings. Every alert ends in a debrief that teaches the system.',
                 ''.join(o)).replace('y2="1300.0"', f'y2="{yb + 10:.1f}"')

# ------------------------------------------------------------------ 03 · user journeys
JOURNEYS = {
  'wang': dict(no='3a', title='Grandma Wang',
    meta='76 · lives alone · north gully mouth · no smartphone · walks about 0.7 m/s',
    intro='One flash-flood afternoon, seen by someone the usual apps leave out. She has no smartphone, only her ears, the old sayings, and a button device around her neck.',
    stages=['Notices', 'Reports', 'Waits', 'Is warned', 'Leaves', 'Shelters, returns'], emo=[-.4, .5, -1, -2, .8, 1.6],
    rows=[('Doing', ['After hours of hard rain she hears the gully go dull and sees the water yellow.', 'Holds the button: “The gully sounds muffled, the water’s yellow.” The light turns green.',
                     'Goes back inside. Ten minutes later a grid worker calls to ask what she saw.', 'The loudspeaker: community notice, Orange, leave the gully. Her button device buzzes and speaks.',
                     'Her household plan says “needs a companion”; a grid worker walks her to the shelter, ten minutes early.', 'Checks in; there is a bed and her medicine. Her son sees “arrived”. All clear at night; home.']),
          ('Touchpoints', ['Her ears and eyes · old sayings', 'Button device', 'Phone call · rule engine (unseen)', 'Loudspeaker · button device · SMS to her son', 'Grid worker · landmark route · signs', 'Shelter check-in · all-clear broadcast']),
          ('Thinking', ['“That sound is wrong. The old folks said…”', '“Will anyone listen to me?”', '“Am I making a fuss?”', '“It’s real. I’m slow. Will I make it?”', '“Someone’s with me. I’m all right.”', '“I’ll report again next time.”']),
          ('Feeling', None),
          ('Pain points', ['Unsure whether it counts', 'Can she report without a phone or reading?', 'Silence while waiting; easy to give up', 'A colour without an action means nothing', 'Slow, and the path is dark', 'No idea when it’s safe to go home']),
          ('Opportunities', ['Saying cards; a radio “observation minute”', 'One button: voice, light, sound', 'Auto call-back: “Received, someone will call”', 'Every notice says level, place, action and who issued it', 'Household plan flags “needs a companion”; landmark signs', 'All-clear, plus who her report helped'])]),
  'li': dict(no='3b', title='Li Wei, commuter',
    meta='34 · works in Laishui town · drives the river bridge daily · his mother and son, 6, live in the village',
    intro='The same storm, seen by someone who is away all day. His phone is always on him, but he has no time to look. His worry is not himself but the family he left at home.',
    stages=['Notices on the way', 'Reports in 10 s', 'Warned at work', 'Checks household', 'Reroutes home', 'Reunites, hears back'], emo=[-.3, .6, -.8, -2, -.6, 1.6],
    rows=[('Doing', ['Driving over the Juma River bridge, he sees the water muddier than usual and branches drifting.', 'Parks, holds the button: “Muddy water under the bridge, branches.” Confirms the draft, adds a photo.',
                     'In a meeting, the status card turns Yellow: prepare. The Action center says check your household.', 'Orange. My household shows his son arrived at the shelter; his mother: “needs pickup”.',
                     'He taps “ask a grid worker”. The gully bridge is closed; the app swaps to the backup route.', 'The family meets at the shelter. Next day: his report was confirmed by three people.']),
          ('Touchpoints', ['His eyes · the commute', 'Voice report · confirm card · photo', 'Status card · push · Action center', 'My household · shelter check-in', 'Grid worker request · backup route', 'Shelter · feedback in the app']),
          ('Thinking', ['“That water doesn’t look right.”', '“One sentence. I can’t be late.”', '“I’m not there. Do they know?”', '“Who is with Mum?”', '“Is it safe to drive back? Which way?”', '“So my glance mattered.”']),
          ('Feeling', None),
          ('Pain points', ['Can’t stop to look; can’t say exactly where', 'No time for forms at work', 'Far away and helpless', 'Can’t see who got the alert or who left', 'His way home may cross the danger zone', 'No idea if his report was useful']),
          ('Opportunities', ['Auto location; voice-only while driving', 'Ten-second report; the app drafts, he only confirms', 'One status card with one next step', 'Household check-in, shared with consent', 'Routes that follow live road closures', 'Feedback: who confirmed it, who it helped'])]),
}
def journey(key):
    J = JOURNEYS[key]; W = 1960; LW = 240; x0 = 110 + LW; cw = (W - 110 - x0) / 6
    o = [T(110, 420, J['title'], 46, font=GROT)[0], CAP(110, 448, J['meta'], 9.5, INK, dash=False)[0], L(110, 470, W - 110, 470, INK, .8)]
    y = 500
    for i, s in enumerate(J['stages']):
        o += [CAP(x0 + i * cw, y, f'{i + 1:02d}', 9, MUTE, dash=False)[0], T(x0 + i * cw, y + 30, s, 21, font=GROT)[0]]
    y += 56; ytop = y
    for name, cells in J['rows']:
        o.append(L(110, y, W - 110, y, HAIR))
        if cells is None:
            hh = 160; o.append(CAP(110, y + 28, name, 9.5, INK)[0]); mid = y + hh / 2
            o += [L(x0, mid, W - 110, mid, FAINT, .8, '2 5'), CAP(110, y + 58, 'At ease', 8.5, dash=False)[0], CAP(110, y + hh - 22, 'Worried', 8.5, dash=False)[0]]
            pts = [(x0 + i * cw + 20, mid - e * 30) for i, e in enumerate(J['emo'])]
            d = f'M{pts[0][0]},{pts[0][1]}' + ''.join(f' C{(pts[i - 1][0] + pts[i][0]) / 2},{pts[i - 1][1]} {(pts[i - 1][0] + pts[i][0]) / 2},{pts[i][1]} {pts[i][0]},{pts[i][1]}' for i in range(1, len(pts)))
            lo = max(range(len(pts)), key=lambda i: pts[i][1])
            ov, ow = oval(0, 0, 'lowest point', 8.5, padx=10, h=20)
            o += [P(d, 'none', INK, 1.3), f'<g transform="translate({pts[lo][0]:.1f},{pts[lo][1] - 26})">{ov}</g>']
            for k, (px, py) in enumerate(pts): o.append(C(px, py, 4.5 if k != lo else 7, INK if k != lo else OR, PAPER, 2))
            y += hh; continue
        italic = name == 'Thinking'
        hs = [T(0, 0, c, 13.5, w=cw - 40)[1] for c in cells]; hh = max(hs) + 44
        if name == 'Opportunities': o.append(R(110, y, W - 220, hh, 0, WHITE, INK, .8))
        o.append(CAP(110 + (14 if name == 'Opportunities' else 0), y + 30, name, 9.5, INK)[0])
        for i, c in enumerate(cells):
            cx = x0 + i * cw; ind = 14 if name in ('Pain points', 'Opportunities') else 0
            if name == 'Pain points': o.append(R(cx, y + 21, 7, 7, 0, OR))
            if name == 'Opportunities': o.append(R(cx, y + 21, 7, 7, 0, 'none', INK, 1))
            o.append(T(cx + ind, y + 30, c, 13.5, w=cw - 40 - ind, lh=1.45, italic=italic, weight=500 if italic else 400)[0])
        y += hh
    o.append(L(110, y, W - 110, y, HAIR))
    for i in range(1, 6): o.append(L(x0 + i * cw - 20, ytop, x0 + i * cw - 20, y, FAINT, .8, '1 4'))
    H = int(y + 190)
    return sheet(W, H, 3, f'Journey {J["no"]}', 'One storm, two lives.', J['intro'], ''.join(o), f'({J["no"]})')

# ------------------------------------------------------------------ 04 · service blueprint
def blueprint():
    W = 2240; LW = 270; x0 = 110 + LW; cw = (W - 110 - x0) / 5
    rows = [('Physical evidence', 'What people see and touch', ['Button device · voice button · confirm card', 'Glowing circles on the 3D village map', 'Observation page with the saying and its reason', 'Status card · broadcast bar · Action center · loudspeaker · SMS', 'My household · shelter list · axonometric shelter · landmark route']),
            ('Resident actions', 'What villagers do', ['Notices a change, speaks, confirms the draft', 'Looks at nearby reports, taps “I see it too”', 'Answers the grid worker’s call', 'Opens the Action center, confirms receipt, checks family', 'Follows landmarks to the shelter, checks in']),
            ('—', 'Line of interaction', None),
            ('Frontstage', 'What staff and system show', ['App drafts what / when / where / type; device lights green and says “received”', 'Map shows unverified rings and merged counts live', 'Grid worker calls or visits to verify', 'Community notice and official warning, each labelled with issuer and time', 'Time to leave and shelter ranking per household; shelter staff welcome people']),
            ('—', 'Line of visibility', None),
            ('Backstage', 'What happens out of sight', ['Dialect speech-to-text · location · de-duplication', 'Classifier + matching against the sayings library', 'Rule engine scores; a village official decides the community level', 'Notice drafted automatically; one-tap approval; receipts tracked', 'Roll call against check-ins; grid workers sent to the missing']),
            ('—', 'Line of internal interaction', None),
            ('Support', 'Systems and partners', ['Button devices · 4G / Wi-Fi · offline cache', '3D village model · observation database', 'Rain, river and weather feeds; rule library (Trial / Verified)', 'Loudspeakers · SMS gateway · push · official warning feed', 'Household data (with consent) · shelter stock and capacity · road status · pace table'])]
    o, y = [], 420
    for i, (name, sub) in enumerate(STAGES):
        o += [T(x0 + i * cw, y, f'{i + 1:02d}', 44, font=GROT, weight=300)[0], T(x0 + i * cw + 66, y - 2, name, 28, font=GROT)[0]]
    y += 30; o.append(L(110, y, W - 110, y, INK, .8))
    for name, sub, cells in rows:
        if cells is None:
            o += [L(110, y + 16, W - 110, y + 16, OR, 1, '6 5'), CAP(W - 110, y + 8, sub, 8.5, OR, 'end', dash=False)[0]]; y += 32; continue
        hs = [T(0, 0, c, 13, w=cw - 48)[1] for c in cells]; hh = max(hs) + 54
        if name == 'Resident actions': o.append(R(110, y, W - 220, hh, 0, WHITE, INK, .8))
        o += [T(110, y + 36, name, 20, font=GROT)[0], CAP(110, y + 56, sub, 8.5, dash=False)[0]]
        for i, c in enumerate(cells): o.append(T(x0 + i * cw, y + 34, c, 13, w=cw - 48, lh=1.5)[0])
        y += hh; o.append(L(110, y, W - 110, y, HAIR))
    for i in range(1, 5): o.append(L(x0 + i * cw - 24, 450, x0 + i * cw - 24, y, FAINT, .8, '1 4'))
    o.append(T(110, y + 44, 'Figures are samples. Household and health data are used only with consent, only to set departure times, and never shown to others.', 12, fill=MUTE)[0])
    H = int(y + 190)
    return sheet(W, H, 4, 'Service blueprint', 'What it takes, behind the glow.',
                 'Above the line of visibility is what villagers meet: a button, a map, two bubbles, a voice on the loudspeaker. Below it are the grid workers, officials, data and partners that make each moment work.',
                 ''.join(o))

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for fn, f in [('01 Wireframe', wireframe), ('02 Workflow', workflow), ('03a Journey - Grandma Wang', lambda: journey('wang')),
                  ('03b Journey - Li Wei commuter', lambda: journey('li')), ('04 Service Blueprint', blueprint)]:
        s = f(); open(os.path.join(OUT, fn + '.svg'), 'w', encoding='utf-8').write(s)
        m = re.search(r'width="(\d+)" height="(\d+)"', s); print('wrote', fn, m.group(1), 'x', m.group(2), len(s) // 1024, 'KB')
