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
    # ground sheet: matte warm-grey slab with rounded corners
    top = rounded_rect(-0.5, D + 0.32, -W - 0.4, W + 0.4, 0.3, 0)
    bot = [(a, b, -0.12) for a, b, _ in top]
    d.append(f'<g id="底板"><polygon points="{pts(*hull([P(*q) for q in top + bot]))}" fill="url(#slabSide)"/>')
    d.append(f'<polygon points="{pts(*[P(*q) for q in top])}" fill="url(#slabTop)"/>')
    inner = rounded_rect(-0.36, D + 0.18, -W - 0.26, W + 0.26, 0.2, 0)
    d.append(f'<polygon points="{pts(*[P(*q) for q in inner])}" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="1.2"/></g>')

    FL, FR, F = (0, -W, 0), (0, W, 0), (0, 0, H)
    BL, BR, B = (D, -W, 0), (D, W, 0), (D, 0, H)
    # guy lines + pegs (behind the body on the far side first)
    def peg(a, b):
        x, y = P(a, b, 0)
        return (f'<rect x="{x-2.2:.1f}" y="{y-9:.1f}" width="4.4" height="10" rx="2.2" fill="url(#aluV)"/>'
                f'<circle cx="{x:.1f}" cy="{y-9:.1f}" r="3" fill="{ORANGE}"/>')
    tipB, tipF = P(D + 0.02, 0, H + 0.22), P(-0.02, 0, H + 0.22)
    gB, gF = (D + 0.2, W * 0.55), (-0.36, -W * 0.55)
    d.append('<g id="风绳">')
    for (ga, gb), tip in ((gB, tipB),):
        x, y = P(ga, gb, 0)
        d.append(f'<line x1="{tip[0]:.1f}" y1="{tip[1]:.1f}" x2="{x:.1f}" y2="{y-6:.1f}" stroke="#9a8f80" stroke-width="1.3"/>' + peg(ga, gb))
    d.append('</g>')

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
    x, y = P(*gF, 0)
    d.append(f'<g id="前杆"><line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y-6:.1f}" stroke="#9a8f80" stroke-width="1.3"/>{peg(*gF)}'
             f'<rect x="{x1-3.5:.1f}" y="{y1:.1f}" width="7" height="{y0-y1:.1f}" rx="3.5" fill="url(#aluV)"/>'
             f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="6" fill="url(#cap)"/></g>')
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

PERSON_DEFS = f'''
<linearGradient id="aluSide" x1="0" y1="0" x2="1" y2="0">{ALU}</linearGradient>
<radialGradient id="puckTop" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#f1ede6"/><stop offset="1" stop-color="#d4cdc1"/></radialGradient>
<radialGradient id="ao" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#6b5a48" stop-opacity=".42"/><stop offset="1" stop-color="#6b5a48" stop-opacity="0"/></radialGradient>
<radialGradient id="body" cx="34%" cy="22%" r="85%"><stop offset="0" stop-color="#ecc396"/><stop offset=".45" stop-color="#cf9764"/><stop offset="1" stop-color="#9a6438"/></radialGradient>
<radialGradient id="bodyRim" cx="50%" cy="0%" r="100%"><stop offset=".7" stop-color="#5e3a1e" stop-opacity="0"/><stop offset="1" stop-color="#5e3a1e" stop-opacity=".35"/></radialGradient>
<radialGradient id="head" cx="36%" cy="30%" r="72%"><stop offset="0" stop-color="#fffdf9"/><stop offset=".55" stop-color="#f1ebe1"/><stop offset="1" stop-color="#c9bfae"/></radialGradient>
<radialGradient id="gloss" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<linearGradient id="neck" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#efe8dc"/><stop offset="1" stop-color="#b9ad9a"/></linearGradient>
<radialGradient id="dot" cx="35%" cy="30%" r="70%"><stop offset="0" stop-color="#ffb184"/><stop offset=".5" stop-color="{ORANGE}"/><stop offset="1" stop-color="#b2461a"/></radialGradient>
'''


def person():
    cx = 256
    py, prx, pry, ph = 380, 138, 50, 30        # puck top centre, radii, height
    d = ['<g id="底座">',
         f'<path d="M{cx-prx},{py} L{cx-prx},{py+ph} A{prx},{pry} 0 0 0 {cx+prx},{py+ph} L{cx+prx},{py} Z" fill="url(#aluSide)"/>',
         f'<path d="M{cx-prx},{py+ph-3} A{prx},{pry} 0 0 0 {cx+prx},{py+ph-3}" fill="none" stroke="#7d8082" stroke-opacity=".5" stroke-width="1.2"/>',
         f'<ellipse cx="{cx}" cy="{py}" rx="{prx}" ry="{pry}" fill="url(#puckTop)"/>',
         f'<ellipse cx="{cx}" cy="{py}" rx="{prx-1}" ry="{pry-1}" fill="none" stroke="#fff" stroke-width="2"/>',
         f'<ellipse cx="{cx}" cy="{py}" rx="{prx-16}" ry="{pry-7}" fill="none" stroke="#bdb4a6" stroke-opacity=".6" stroke-width="1.2"/>',
         # Braun orange indicator on the front of the puck
         f'<ellipse cx="{cx-44}" cy="{py+pry-2+ph*0.48:.0f}" rx="7" ry="6" fill="url(#dot)"/>',
         f'<ellipse cx="{cx-46}" cy="{py+pry-4+ph*0.48:.0f}" rx="2.5" ry="1.6" fill="#fff" opacity=".7"/>',
         '</g>']
    # contact occlusion of the bust on the puck
    d.append(f'<ellipse id="接触阴影" cx="{cx+6}" cy="{py+2}" rx="122" ry="40" fill="url(#ao)"/>')
    by, brx, bry = 376, 108, 38                  # base ellipse of the shoulders
    sh = 272                                     # shoulder top
    body = (f'M{cx-brx},{by} C{cx-brx},{sh+18} {cx-84},{sh} {cx},{sh} '
            f'C{cx+84},{sh} {cx+brx},{sh+18} {cx+brx},{by} A{brx},{bry} 0 0 1 {cx-brx},{by} Z')
    d += ['<g id="身体">',
          f'<path d="{body}" fill="url(#body)"/>',
          f'<path d="{body}" fill="url(#bodyRim)"/>',
          f'<path d="M{cx-brx+3},{by} A{brx-3},{bry-3} 0 0 0 {cx+brx-3},{by}" fill="none" stroke="#f3d3ae" stroke-opacity=".6" stroke-width="1.5"/>',
          # soft highlight on the left shoulder
          f'<ellipse cx="{cx-46}" cy="{sh+30}" rx="30" ry="14" transform="rotate(-24 {cx-46} {sh+30})" fill="url(#gloss)" opacity=".35"/>',
          # soft V seam at the neckline
          f'<path d="M{cx-30},{sh+6} Q{cx},{sh+30} {cx+30},{sh+6}" fill="none" stroke="#9a6438" stroke-opacity=".45" stroke-width="2"/>',
          '</g>']
    hy, hr = 208, 56
    d += ['<g id="头部">',
          f'<rect x="{cx-18}" y="{sh-14}" width="36" height="22" rx="9" fill="url(#neck)"/>',
          f'<ellipse cx="{cx+6}" cy="{sh+4}" rx="44" ry="12" fill="url(#ao)"/>',
          f'<circle cx="{cx}" cy="{hy}" r="{hr}" fill="url(#head)"/>',
          f'<ellipse cx="{cx-24}" cy="{hy-28}" rx="20" ry="13" transform="rotate(-30 {cx-24} {hy-28})" fill="url(#gloss)" opacity=".9"/>',
          f'<circle cx="{cx}" cy="{hy}" r="{hr-.8}" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="1.2"/>',
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
