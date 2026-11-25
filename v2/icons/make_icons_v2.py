#!/usr/bin/env python3
"""Airbnb-2024 / Braun style object icons, transparent, no drop shadow.
  帐篷_v2.svg – A-frame shelter tent: canvas, brushed-aluminium poles, leather tie-backs, Braun orange toggles
  个人_v2.svg – figurine bust: ceramic head, matte caramel shoulders, brushed-aluminium puck with orange dot
Built from projected 3D points; gradients only (Figma friendly)."""
import os, math

HERE = os.path.dirname(os.path.abspath(__file__))
ORANGE = '#E8692F'

ALU = '''<stop offset="0" stop-color="#f7f7f5"/><stop offset=".18" stop-color="#c9cbcb"/>
  <stop offset=".38" stop-color="#eeeeec"/><stop offset=".55" stop-color="#a9acad"/>
  <stop offset=".75" stop-color="#dcdddc"/><stop offset="1" stop-color="#8f9294"/>'''

# ---------- projection: a = depth (back -> upper right), b = width (right -> lower right), z = up
S, OX, OY = 96, 208, 322


def P(a, b, z):
    return (OX + (a * 0.56 + b * 0.84) * S, OY + (b * 0.34 - a * 0.36) * S - z * S)


def pts(*q):
    return ' '.join(f'{x:.1f},{y:.1f}' for x, y in q)


def hull(points):
    p = sorted(set(points))
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0: lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0: up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def rounded_rect(a0, a1, b0, b1, r, z, n=8):
    out = []
    for ca, cb, start in ((a1 - r, b1 - r, 0), (a0 + r, b1 - r, 90), (a0 + r, b0 + r, 180), (a1 - r, b0 + r, 270)):
        for i in range(n + 1):
            t = math.radians(start + 90 * i / n)
            out.append((ca + r * math.cos(t), cb + r * math.sin(t), z))
    return out


def lerp(p, q, t):
    return tuple(p[i] + (q[i] - p[i]) * t for i in range(len(p)))


def tent():
    W, D, H = 1.0, 1.75, 1.6
    d = []
    FL, FR, F = (0, -W, 0), (0, W, 0), (0, 0, H)
    BL, BR, B = (D, -W, 0), (D, W, 0), (D, 0, H)
    # guy lines + pegs (behind the body on the far side first)
    def peg(a, b):
        x, y = P(a, b, 0)
        return (f'<rect x="{x-2.2:.1f}" y="{y-9:.1f}" width="4.4" height="10" rx="2.2" fill="url(#aluV)"/>'
                f'<circle cx="{x:.1f}" cy="{y-9:.1f}" r="3" fill="{ORANGE}"/>')
    tipB, tipF = P(D + 0.02, 0, H + 0.22), P(-0.02, 0, H + 0.22)
    gB, gF = (D + 0.2, W * 0.55), (-0.36, -W * 0.55)
    # rear pole
    x0, y0 = P(D + 0.02, 0, H - 0.05); x1, y1 = tipB
    d.append(f'<g id="后杆"><rect x="{x1-3:.1f}" y="{y1:.1f}" width="6" height="{y0-y1:.1f}" rx="3" fill="url(#aluV)"/>'
             f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="5" fill="url(#cap)"/></g>')

    # right roof panel (shaded), with a soft sag and a stitched seam
    rr = [P(*F), P(*B), P(*BR), P(*FR)]
    sag = lerp(P(*lerp(F, BR, .5)), (0, 0), 0)  # centre of the panel
    d.append('<g id="侧面">')
    d.append(f'<path d="M{rr[0][0]:.1f},{rr[0][1]:.1f} L{rr[1][0]:.1f},{rr[1][1]:.1f} '
             f'Q{(rr[1][0]+rr[2][0])/2+5:.1f},{(rr[1][1]+rr[2][1])/2-2:.1f} {rr[2][0]:.1f},{rr[2][1]:.1f} '
             f'Q{(rr[2][0]+rr[3][0])/2:.1f},{(rr[2][1]+rr[3][1])/2-7:.1f} {rr[3][0]:.1f},{rr[3][1]:.1f} Z" fill="url(#roof)"/>')
    for t in (0.36, 0.7):
        p, q = P(*lerp(F, FR, t)), P(*lerp(B, BR, t))
        d.append(f'<line x1="{p[0]+4:.1f}" y1="{p[1]:.1f}" x2="{q[0]-2:.1f}" y2="{q[1]:.1f}" stroke="#8f8574" '
                 f'stroke-opacity=".5" stroke-width="1.1" stroke-dasharray="3 3"/>')
    # ridge highlight
    d.append(f'<line x1="{rr[0][0]:.1f}" y1="{rr[0][1]:.1f}" x2="{rr[1][0]:.1f}" y2="{rr[1][1]:.1f}" stroke="#fffaf0" stroke-width="2.4" stroke-linecap="round"/>')
    # hem band at the bottom of the side panel
    h1, h2 = P(*lerp(FR, F, .07)), P(*lerp(BR, B, .07))
    d.append(f'<polygon points="{pts(P(*FR), P(*BR), h2, h1)}" fill="#a99d8a" opacity=".55"/></g>')

    # front gable (lit)
    fl, fr, f = P(*FL), P(*FR), P(*F)
    d.append('<g id="正面">')
    d.append(f'<path d="M{fl[0]:.1f},{fl[1]:.1f} L{f[0]:.1f},{f[1]:.1f} L{fr[0]:.1f},{fr[1]:.1f} '
             f'Q{(fl[0]+fr[0])/2:.1f},{(fl[1]+fr[1])/2-5:.1f} {fl[0]:.1f},{fl[1]:.1f} Z" fill="url(#front)"/>')
    hl, hr = P(*lerp(FL, F, .07)), P(*lerp(FR, F, .07))
    d.append(f'<path d="M{fl[0]:.1f},{fl[1]:.1f} L{hl[0]:.1f},{hl[1]:.1f} Q{(hl[0]+hr[0])/2:.1f},{(hl[1]+hr[1])/2-5:.1f} {hr[0]:.1f},{hr[1]:.1f} '
             f'L{fr[0]:.1f},{fr[1]:.1f} Q{(fl[0]+fr[0])/2:.1f},{(fl[1]+fr[1])/2-5:.1f} {fl[0]:.1f},{fl[1]:.1f} Z" fill="#cfc4b1" opacity=".7"/>')
    # door: dark interior, rounded top
    dt = P(0, 0, H * 0.78)
    dl, dr = P(0, -W * 0.56, 0.02), P(0, W * 0.56, 0.02)
    d.append(f'<path d="M{dl[0]:.1f},{dl[1]:.1f} L{dt[0]-4:.1f},{dt[1]+8:.1f} Q{dt[0]:.1f},{dt[1]:.1f} {dt[0]+4:.1f},{dt[1]+8:.1f} '
             f'L{dr[0]:.1f},{dr[1]:.1f} Q{(dl[0]+dr[0])/2:.1f},{(dl[1]+dr[1])/2-4:.1f} {dl[0]:.1f},{dl[1]:.1f} Z" fill="url(#inside)"/>')
    # rolled-up door flap along the right edge of the opening, tied with a leather strap
    rt, rb = (dt[0]+5, dt[1]+12), (dr[0]-3, dr[1]-3)
    d.append(f'<line x1="{rt[0]:.1f}" y1="{rt[1]:.1f}" x2="{rb[0]:.1f}" y2="{rb[1]:.1f}" stroke="#b9ad97" stroke-width="13" stroke-linecap="round"/>')
    d.append(f'<line x1="{rt[0]-1:.1f}" y1="{rt[1]:.1f}" x2="{rb[0]-1.5:.1f}" y2="{rb[1]:.1f}" stroke="url(#roll)" stroke-width="10" stroke-linecap="round"/>')
    for t in (.3, .72):
        q = lerp(rt, rb, t)
        ang = math.degrees(math.atan2(rb[1]-rt[1], rb[0]-rt[0])) + 90
        d.append(f'<rect x="{q[0]-9:.1f}" y="{q[1]-2.6:.1f}" width="18" height="5.2" rx="2.4" fill="url(#leather)" transform="rotate({ang:.1f} {q[0]:.1f} {q[1]:.1f})"/>')
    q = lerp(rt, rb, .72)
    d.append(f'<circle cx="{q[0]+8:.1f}" cy="{q[1]+1:.1f}" r="4" fill="url(#toggle)"/>')
    # zipper track on the left edge of the door + aluminium pull
    zl = P(0, -W * 0.5, 0.05)
    d.append(f'<line x1="{dt[0]-4:.1f}" y1="{dt[1]+10:.1f}" x2="{zl[0]:.1f}" y2="{zl[1]-2:.1f}" stroke="url(#aluD)" stroke-width="2.4"/>')
    zp = lerp((dt[0]-4, dt[1]+10), (zl[0], zl[1]), .45)
    d.append(f'<rect x="{zp[0]-3:.1f}" y="{zp[1]-2:.1f}" width="6" height="13" rx="3" fill="url(#aluV)"/>'
             f'<circle cx="{zp[0]:.1f}" cy="{zp[1]+11:.1f}" r="2.6" fill="{ORANGE}"/>')
    # edge highlights
    d.append(f'<polyline points="{pts(fl, f, fr)}" fill="none" stroke="#fffdf8" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    d.append('</g>')

    # front pole + guy line to the front peg
    x0, y0 = P(-0.02, 0, H - 0.05); x1, y1 = tipF
    d.append(f'<g id="前杆"><rect x="{x1-3.5:.1f}" y="{y1:.1f}" width="7" height="{y0-y1:.1f}" rx="3.5" fill="url(#aluV)"/>'
             f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="6" fill="url(#cap)"/></g>')
    # centre the object in the 512 canvas
    return ['<g transform="translate(256 262) scale(1.22) translate(-255 -228)">'] + d + ['</g>']
    return d


TENT_DEFS = f'''
<linearGradient id="slabTop" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ece7de"/><stop offset="1" stop-color="#d6cfc3"/></linearGradient>
<linearGradient id="slabSide" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#cfc7ba"/><stop offset=".5" stop-color="#b9b0a2"/><stop offset="1" stop-color="#a1978a"/></linearGradient>
<linearGradient id="front" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fdfaf3"/><stop offset=".55" stop-color="#f1eadd"/><stop offset="1" stop-color="#ddd3c1"/></linearGradient>
<linearGradient id="roof" x1="0" y1="0" x2=".35" y2="1"><stop offset="0" stop-color="#e6ddcd"/><stop offset=".6" stop-color="#cdc2ae"/><stop offset="1" stop-color="#b5a993"/></linearGradient>
<linearGradient id="inside" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2e2620"/><stop offset="1" stop-color="#4c3f34"/></linearGradient>
<linearGradient id="flap" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#d9cfbd"/><stop offset=".6" stop-color="#efe7d9"/><stop offset="1" stop-color="#cdbfa9"/></linearGradient>
<linearGradient id="roll" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fbf6ec"/><stop offset="1" stop-color="#cfc3ad"/></linearGradient>
<linearGradient id="leather" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c99566"/><stop offset="1" stop-color="#8c5c37"/></linearGradient>
<radialGradient id="toggle" cx="35%" cy="30%" r="70%"><stop offset="0" stop-color="#ffb184"/><stop offset=".5" stop-color="{ORANGE}"/><stop offset="1" stop-color="#b2461a"/></radialGradient>
<radialGradient id="cap" cx="35%" cy="30%" r="70%"><stop offset="0" stop-color="#ffb184"/><stop offset=".5" stop-color="{ORANGE}"/><stop offset="1" stop-color="#b2461a"/></radialGradient>
<linearGradient id="aluV" x1="0" y1="0" x2="1" y2="0">{ALU}</linearGradient>
<linearGradient id="aluD" x1="0" y1="0" x2="1" y2="1">{ALU}</linearGradient>
'''

PERSON_DEFS = f"""
<radialGradient id="skin" cx="34%" cy="30%" r="75%"><stop offset="0" stop-color="#fbeee0"/><stop offset=".55" stop-color="#efd9c2"/><stop offset="1" stop-color="#c9a988"/></radialGradient>
<radialGradient id="hair" cx="40%" cy="25%" r="80%"><stop offset="0" stop-color="#7a5a42"/><stop offset=".6" stop-color="#4b3526"/><stop offset="1" stop-color="#2e2018"/></radialGradient>
<linearGradient id="jacket" x1="0" y1="0" x2="1" y2=".4"><stop offset="0" stop-color="#e9bf8f"/><stop offset=".5" stop-color="#cf9563"/><stop offset="1" stop-color="#9f6739"/></linearGradient>
<linearGradient id="jacketSide" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#b47a48"/><stop offset="1" stop-color="#875427"/></linearGradient>
<linearGradient id="sleeveL" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#f0cb9f"/><stop offset="1" stop-color="#c58a57"/></linearGradient>
<linearGradient id="sleeveR" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#b37946"/><stop offset="1" stop-color="#7f4f27"/></linearGradient>
<linearGradient id="pantL" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#a8a196"/><stop offset="1" stop-color="#857d72"/></linearGradient>
<linearGradient id="pantR" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#857d72"/><stop offset="1" stop-color="#635c53"/></linearGradient>
<linearGradient id="shoe" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fbf8f2"/><stop offset="1" stop-color="#d9d2c6"/></linearGradient>
<linearGradient id="sole" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e6ddcf"/><stop offset="1" stop-color="#b4aa9b"/></linearGradient>
<linearGradient id="alu" x1="0" y1="0" x2="1" y2="0">{ALU}</linearGradient>
<radialGradient id="dot" cx="35%" cy="30%" r="70%"><stop offset="0" stop-color="#ffb184"/><stop offset=".5" stop-color="{ORANGE}"/><stop offset="1" stop-color="#b2461a"/></radialGradient>
<radialGradient id="gloss" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<radialGradient id="occl" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#4a2c14" stop-opacity=".35"/><stop offset="1" stop-color="#4a2c14" stop-opacity="0"/></radialGradient>
"""


def person():
    """full-body vinyl-toy figure, three-quarter front-left, no base"""
    d = []
    # legs (right leg slightly behind)
    d += ['<g id="腿">',
          '<path d="M262,330 L298,330 L296,446 Q296,454 288,454 L270,454 Q262,454 262,446 Z" fill="url(#pantR)"/>',
          '<path d="M214,326 L256,326 L254,452 Q254,460 246,460 L224,460 Q216,460 216,452 Z" fill="url(#pantL)"/>',
          '<path d="M236,334 L236,452" stroke="#f1ece4" stroke-opacity=".25" stroke-width="2"/>',
          '</g>']
    # shoes, toes turned toward lower-left
    d += ['<g id="鞋">',
          '<path d="M262,446 L300,446 Q306,446 306,454 L306,462 L252,462 Q250,452 262,446 Z" fill="url(#shoe)"/>',
          '<rect x="250" y="460" width="58" height="8" rx="4" fill="url(#sole)"/>',
          '<path d="M216,450 L258,450 Q262,450 262,458 L262,468 L196,468 Q194,456 216,450 Z" fill="url(#shoe)"/>',
          '<rect x="193" y="466" width="72" height="9" rx="4.5" fill="url(#sole)"/>',
          '<circle cx="245" cy="459" r="3" fill="url(#dot)"/>',
          '</g>']
    # back arm (right side, shaded)
    d += ['<g id="右臂">',
          '<path d="M318,190 Q340,196 340,224 L338,318 Q338,332 326,332 Q314,332 314,318 L312,210 Z" fill="url(#sleeveR)"/>',
          '<circle cx="326" cy="338" r="13" fill="url(#skin)"/>',
          '</g>']
    # torso: puffer-style jacket with a side panel for volume
    jacket = 'M206,186 Q256,170 312,184 Q326,188 326,206 L320,322 Q318,340 298,340 L214,340 Q194,340 192,322 L188,210 Q188,192 206,186 Z'
    d += ['<g id="外套">',
          f'<path d="{jacket}" fill="url(#jacket)"/>',
          '<path d="M300,188 Q326,190 326,206 L320,322 Q318,340 298,340 L290,340 Q306,330 306,312 L310,206 Q310,194 300,188 Z" fill="url(#jacketSide)"/>',
          # quilting seams
          '<path d="M192,248 Q250,258 322,246" fill="none" stroke="#8d5a2e" stroke-opacity=".35" stroke-width="2"/>',
          '<path d="M194,292 Q250,302 320,290" fill="none" stroke="#8d5a2e" stroke-opacity=".35" stroke-width="2"/>',
          '<path d="M194,250 Q250,260 322,248" fill="none" stroke="#f6d6ad" stroke-opacity=".45" stroke-width="1.2" transform="translate(0 3)"/>',
          '<path d="M196,294 Q250,304 320,292" fill="none" stroke="#f6d6ad" stroke-opacity=".45" stroke-width="1.2" transform="translate(0 3)"/>',
          # hem band
          '<path d="M193,318 Q256,330 320,318 L320,322 Q318,340 298,340 L214,340 Q194,340 192,322 Z" fill="#8d5a2e" opacity=".35"/>',
          # brushed-aluminium zip with orange pull, set left of centre for the 3/4 turn
          '<path d="M246,192 Q244,260 246,338" fill="none" stroke="url(#alu)" stroke-width="3"/>',
          '<rect x="241" y="214" width="9" height="16" rx="4" fill="url(#alu)"/>',
          '<circle cx="245.5" cy="234" r="4" fill="url(#dot)"/>',
          # stand collar
          '<path d="M214,184 Q252,170 300,182 L298,198 Q252,188 216,200 Z" fill="#b97f4b"/>',
          '<path d="M214,184 Q252,170 300,182" fill="none" stroke="#f3cfa3" stroke-width="2" stroke-linecap="round"/>',
          '<ellipse cx="226" cy="214" rx="26" ry="12" transform="rotate(-12 226 214)" fill="url(#gloss)" opacity=".35"/>',
          '</g>']
    # front arm (left side, lit)
    d += ['<g id="左臂">',
          '<path d="M196,192 Q168,198 168,226 L170,316 Q170,330 183,330 Q196,330 196,316 L200,212 Z" fill="url(#sleeveL)"/>',
          '<path d="M170,300 Q183,306 196,300" fill="none" stroke="#9f6739" stroke-opacity=".45" stroke-width="2"/>',
          '<circle cx="183" cy="337" r="13.5" fill="url(#skin)"/>',
          '</g>']
    # neck, head and hair
    d += ['<g id="头部">',
          '<rect x="240" y="150" width="34" height="34" rx="12" fill="url(#skin)"/>',
          '<ellipse cx="258" cy="180" rx="30" ry="8" fill="url(#occl)"/>',
          '<circle cx="254" cy="112" r="58" fill="url(#skin)"/>',
          # ear on the far side
          '<ellipse cx="308" cy="118" rx="9" ry="14" fill="#e2c3a3"/>',
          # hair: rounded cap swept to the back-right
          '<path d="M198,104 Q196,52 252,48 Q312,46 316,104 Q318,124 310,132 Q308,104 290,92 Q262,100 226,90 Q208,96 200,116 Z" fill="url(#hair)"/>',
          '<path d="M216,70 Q240,54 270,58" fill="none" stroke="#a07a5c" stroke-opacity=".6" stroke-width="3" stroke-linecap="round"/>',
          '<ellipse cx="226" cy="128" rx="16" ry="12" fill="url(#gloss)" opacity=".55"/>',
          '</g>']
    return d


def write(name, defs, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">\n'
           f'<defs>{defs}</defs>\n<g id="{name}">\n' + '\n'.join(body) + '\n</g>\n</svg>\n')
    open(os.path.join(HERE, name + '.svg'), 'w', encoding='utf-8').write(svg)
    print('wrote', name, len(svg))


if __name__ == '__main__':
    write('帐篷_v2', TENT_DEFS, tent())
    write('个人_v2', PERSON_DEFS, person())
