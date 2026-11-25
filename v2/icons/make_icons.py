#!/usr/bin/env python3
"""Two transparent-background icons in the golf-UI miniature style:
a round grass token (mown stripes, tree clumps, soil edge, soft shadow)
with a white architectural-model object on top.
  个人.svg  – scale figure on a lime location ring
  避难帐篷.svg – A-frame shelter tent on a sand pad
Only gradients / shapes (no filters) so the files import cleanly into Figma."""
import os, random, math

HERE = os.path.dirname(os.path.abspath(__file__))
CX, CY, RX, RY, T = 256, 338, 178, 84, 30
LIME = '#C6F432'


def f(v):
    return f'{v:.1f}'.rstrip('0').rstrip('.')


DEFS = f'''
<radialGradient id="dropShadow" cx="50%" cy="50%" r="50%">
  <stop offset="0" stop-color="#0d1f08" stop-opacity=".34"/>
  <stop offset=".6" stop-color="#0d1f08" stop-opacity=".14"/>
  <stop offset="1" stop-color="#0d1f08" stop-opacity="0"/></radialGradient>
<linearGradient id="soil" x1="0" x2="1" y1="0" y2="0">
  <stop offset="0" stop-color="#4a3322"/><stop offset=".32" stop-color="#8b6545"/>
  <stop offset=".7" stop-color="#6b4b33"/><stop offset="1" stop-color="#3b281b"/></linearGradient>
<linearGradient id="soilV" x1="0" x2="0" y1="0" y2="1">
  <stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".35"/></linearGradient>
<linearGradient id="lip" x1="0" x2="1">
  <stop offset="0" stop-color="#2f5a1c"/><stop offset=".35" stop-color="#4f8a2c"/><stop offset="1" stop-color="#284d18"/></linearGradient>
<radialGradient id="turf" cx="38%" cy="30%" r="75%">
  <stop offset="0" stop-color="#b4dc6e"/><stop offset=".45" stop-color="#7db544"/>
  <stop offset=".85" stop-color="#5a9632"/><stop offset="1" stop-color="#4a8229"/></radialGradient>
<radialGradient id="crown" cx="34%" cy="28%" r="78%">
  <stop offset="0" stop-color="#93c552"/><stop offset=".42" stop-color="#3f7d26"/>
  <stop offset="1" stop-color="#173812"/></radialGradient>
<radialGradient id="crownDark" cx="40%" cy="35%" r="70%">
  <stop offset="0" stop-color="#3f7a28"/><stop offset="1" stop-color="#173512"/></radialGradient>
<radialGradient id="treeShadow" cx="50%" cy="50%" r="50%">
  <stop offset="0" stop-color="#16300e" stop-opacity=".5"/><stop offset="1" stop-color="#16300e" stop-opacity="0"/></radialGradient>
<linearGradient id="clay" x1="0" x2="1">
  <stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="#f1efe9"/><stop offset="1" stop-color="#c9c5ba"/></linearGradient>
<linearGradient id="clayDark" x1="0" x2="1">
  <stop offset="0" stop-color="#ecebe5"/><stop offset="1" stop-color="#b9b5aa"/></linearGradient>
<radialGradient id="head" cx="36%" cy="30%" r="70%">
  <stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#eeece6"/><stop offset="1" stop-color="#c4c0b5"/></radialGradient>
<radialGradient id="castShadow" cx="30%" cy="50%" r="70%">
  <stop offset="0" stop-color="#16300e" stop-opacity=".42"/><stop offset="1" stop-color="#16300e" stop-opacity="0"/></radialGradient>
<radialGradient id="limeGlow" cx="50%" cy="50%" r="50%">
  <stop offset="0" stop-color="{LIME}" stop-opacity=".55"/><stop offset="1" stop-color="{LIME}" stop-opacity="0"/></radialGradient>
<linearGradient id="tentFront" x1="0" x2="1" y1="0" y2="1">
  <stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#f2f0ea"/><stop offset="1" stop-color="#dcd8cd"/></linearGradient>
<linearGradient id="tentSide" x1="0" x2="1" y1="0" y2="1">
  <stop offset="0" stop-color="#dedad0"/><stop offset="1" stop-color="#aaa598"/></linearGradient>
<linearGradient id="tentInside" x1="0" x2="0" y1="0" y2="1">
  <stop offset="0" stop-color="#1d2419"/><stop offset="1" stop-color="#3a4632"/></linearGradient>
<radialGradient id="sand" cx="45%" cy="40%" r="60%">
  <stop offset="0" stop-color="#f3ead0"/><stop offset=".75" stop-color="#e2d5ad"/><stop offset="1" stop-color="#cdbd8f"/></radialGradient>
<clipPath id="topClip"><ellipse cx="{CX}" cy="{CY}" rx="{RX}" ry="{RY}"/></clipPath>
'''


def token(seed):
    """ground shadow, soil side, turf top with stripes and speckles"""
    r = random.Random(seed)
    L, R = CX - RX, CX + RX
    side = (f'M{L},{CY} L{L},{CY+T} A{RX},{RY} 0 0 0 {R},{CY+T} '
            f'L{R},{CY} A{RX},{RY} 0 0 1 {L},{CY} Z')
    lip = (f'M{L},{CY} L{L},{CY+8} A{RX},{RY} 0 0 0 {R},{CY+8} '
           f'L{R},{CY} A{RX},{RY} 0 0 1 {L},{CY} Z')
    out = [f'<g id="投影"><ellipse cx="{CX+8}" cy="{CY+T+14}" rx="{RX+14}" ry="{RY*0.62:.0f}" fill="url(#dropShadow)"/></g>',
           f'<g id="土层"><path d="{side}" fill="url(#soil)"/><path d="{side}" fill="url(#soilV)"/>']
    # strata and pebbles on the soil face
    for k, (dy, op) in enumerate([(15, .18), (22, .12)]):
        out.append(f'<path d="M{L+4},{CY+dy} A{RX-4},{RY} 0 0 0 {R-4},{CY+dy}" fill="none" '
                   f'stroke="#c9a27a" stroke-opacity="{op}" stroke-width="1.4"/>')
    for _ in range(26):
        a = r.uniform(0.08, math.pi - 0.08)
        x = CX - RX * math.cos(a) * 0.99
        y = CY + RY * math.sin(a) + r.uniform(11, T - 3)
        out.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r.uniform(1.2, 2.8))}" ry="{f(r.uniform(.9, 1.8))}" '
                   f'fill="#{r.choice(["a88563", "5a3e2a", "c2a07c"])}" opacity=".7"/>')
    out.append(f'<path d="{lip}" fill="url(#lip)"/></g>')
    # turf
    out.append(f'<g id="草坪"><ellipse cx="{CX}" cy="{CY}" rx="{RX}" ry="{RY}" fill="url(#turf)"/>')
    out.append(f'<g clip-path="url(#topClip)"><g transform="translate({CX},{CY}) scale(1,{RY/RX:.4f}) rotate(32)">')
    for i in range(-9, 9):
        if i % 2 == 0:
            out.append(f'<rect x="{i*24}" y="-220" width="24" height="440" fill="#fff" opacity=".075"/>')
    for i in range(-9, 9):
        if i % 2 == 0:
            out.append(f'<rect x="-220" y="{i*24}" width="440" height="24" fill="#1d3d10" opacity=".045"/>')
    out.append('</g>')
    for _ in range(620):
        while True:
            u, v = r.uniform(-1, 1), r.uniform(-1, 1)
            if u * u + v * v < 0.97:
                break
        x, y = CX + u * RX, CY + v * RY
        c = r.choice(['2f5f1b', '3d7324', 'a9d46a', 'c4e48a', '4c8a2c'])
        out.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r.uniform(.7, 1.9))}" ry="{f(r.uniform(.5, 1.1))}" '
                   f'fill="#{c}" opacity="{r.uniform(.25, .55):.2f}"/>')
    out.append('</g>')
    out.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{RX-1}" ry="{RY-1}" fill="none" stroke="#d6efa0" '
               f'stroke-opacity=".55" stroke-width="1.6"/></g>')
    return out


def tree(x, y, s, r):
    """clump of shaded spheres, base at (x, y), size s"""
    g = [f'<g><ellipse cx="{f(x+s*.42)}" cy="{f(y+s*.06)}" rx="{f(s*1.05)}" ry="{f(s*.36)}" fill="url(#treeShadow)"/>',
         f'<ellipse cx="{f(x)}" cy="{f(y-s*.55)}" rx="{f(s*.78)}" ry="{f(s*.66)}" fill="url(#crownDark)"/>']
    blobs = []
    for _ in range(int(16 + s / 2.2)):
        a = r.uniform(0, 2 * math.pi)
        d = math.sqrt(r.uniform(0, 1)) * .58 * s
        bx, by = x + math.cos(a) * d, y - s * .62 + math.sin(a) * d * .82
        blobs.append((by, bx, s * r.uniform(.17, .29)))
    for by, bx, br in sorted(blobs):
        g.append(f'<circle cx="{f(bx)}" cy="{f(by)}" r="{f(br)}" fill="url(#crown)"/>')
    for _ in range(int(s / 2)):
        a = r.uniform(0, 2 * math.pi); d = math.sqrt(r.uniform(0, 1)) * .6 * s
        g.append(f'<circle cx="{f(x + math.cos(a)*d)}" cy="{f(y - s*.66 + math.sin(a)*d*.8)}" '
                 f'r="{f(s*r.uniform(.025, .05))}" fill="#{r.choice(["14300d", "b8e07a"])}" opacity=".5"/>')
    g.append('</g>')
    return by_base(y, g)


def by_base(y, parts):
    return (y, '\n'.join(parts))


def trees(seed, skip=()):
    r = random.Random(seed)
    items = []
    # back rim, from left to right across the top of the token
    for deg in range(196, 352, 13):
        if any(a <= deg <= b for a, b in skip):
            continue
        a = math.radians(deg + r.uniform(-4, 4))
        k = r.uniform(.8, .92)
        s = r.uniform(24, 36)
        items.append(tree(CX + RX * k * math.cos(a), CY + RY * k * math.sin(a) + 4, s, r))
    # a second, inner row for depth
    for deg in (205, 228, 318, 338):
        a = math.radians(deg)
        items.append(tree(CX + RX * .62 * math.cos(a), CY + RY * .62 * math.sin(a) + 6, r.uniform(20, 26), r))
    # low bushes at the front corners
    for deg, s in ((160, 17), (172, 13), (18, 16), (30, 12)):
        a = math.radians(deg)
        items.append(tree(CX + RX * .9 * math.cos(a), CY + RY * .9 * math.sin(a), s, r))
    return items


def person():
    bx, by = 256, 356
    p = ['<g id="人物">',
         f'<ellipse cx="{bx}" cy="{by}" rx="70" ry="33" fill="url(#limeGlow)"/>',
         f'<ellipse cx="{bx}" cy="{by}" rx="62" ry="29" fill="none" stroke="{LIME}" stroke-width="2" stroke-opacity=".55"/>',
         f'<ellipse cx="{bx}" cy="{by}" rx="42" ry="19.5" fill="{LIME}" fill-opacity=".22" stroke="{LIME}" stroke-width="5"/>',
         f'<ellipse cx="{bx+52}" cy="{by+3}" rx="62" ry="13" transform="rotate(10 {bx+52} {by+3})" fill="url(#castShadow)"/>',
         f'<ellipse cx="{bx}" cy="{by}" rx="20" ry="6" fill="#16300e" opacity=".45"/>',
         # legs
         f'<path d="M{bx-14},{by-72} L{bx-1},{by-72} L{bx-2.5},{by-5} Q{bx-2.5},{by} {bx-7},{by} Q{bx-11.5},{by} {bx-11.5},{by-5} Z" fill="url(#clay)"/>',
         f'<path d="M{bx+1},{by-72} L{bx+14},{by-72} L{bx+11.5},{by-5} Q{bx+11.5},{by} {bx+7},{by} Q{bx+2.5},{by} {bx+2.5},{by-5} Z" fill="url(#clayDark)"/>',
         # arms, hanging slightly outward from the shoulders
         f'<rect x="{bx-30}" y="{by-136}" width="10" height="68" rx="5" transform="rotate(5 {bx-25} {by-136})" fill="url(#clay)"/>',
         f'<rect x="{bx+20}" y="{by-136}" width="10" height="68" rx="5" transform="rotate(-5 {bx+25} {by-136})" fill="url(#clayDark)"/>',
         # torso: rounded shoulders tapering to the hips
         f'<path d="M{bx-15},{by-142} Q{bx-26},{by-142} {bx-26},{by-130} L{bx-17},{by-74} Q{bx-16},{by-66} {bx-8},{by-66} '
         f'L{bx+8},{by-66} Q{bx+16},{by-66} {bx+17},{by-74} L{bx+26},{by-130} Q{bx+26},{by-142} {bx+15},{by-142} Z" fill="url(#clay)"/>',
         # neck + head
         f'<rect x="{bx-5}" y="{by-152}" width="10" height="14" rx="4" fill="url(#clayDark)"/>',
         f'<circle cx="{bx}" cy="{by-166}" r="16" fill="url(#head)"/>',
         '</g>']
    return (by, '\n'.join(p))


def tent():
    F, FL, FR = (220, 232), (152, 352), (286, 360)
    R, RR = (306, 212), (364, 322)
    P = lambda *pts: ' '.join(f'{x},{y}' for x, y in pts)
    t = ['<g id="帐篷">',
         f'<ellipse cx="262" cy="342" rx="132" ry="50" fill="url(#sand)"/>',
         f'<ellipse cx="262" cy="342" rx="132" ry="50" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="1.4"/>',
         # cast shadow to the lower right
         f'<polygon points="{P(FR, RR, (420, 334), (338, 376))}" fill="url(#castShadow)"/>',
         f'<ellipse cx="226" cy="356" rx="80" ry="9" fill="#2a2414" opacity=".28"/>',
         # guy lines + pegs
         f'<line x1="{F[0]}" y1="{F[1]}" x2="124" y2="350" stroke="#7d7a70" stroke-width="1.4"/>',
         f'<line x1="{R[0]}" y1="{R[1]}" x2="398" y2="296" stroke="#7d7a70" stroke-width="1.4"/>',
         '<circle cx="124" cy="350" r="2.6" fill="#5c574b"/><circle cx="398" cy="296" r="2.6" fill="#5c574b"/>',
         # side roof (shade) then front gable (lit)
         f'<polygon points="{P(F, R, RR, FR)}" fill="url(#tentSide)"/>',
         f'<polygon points="{P(FL, F, FR)}" fill="url(#tentFront)"/>',
         # door opening + lime flap
         f'<polygon points="{P((220, 268), (190, 354), (252, 357))}" fill="url(#tentInside)"/>',
         f'<polygon points="{P((220, 268), (252, 357), (270, 348))}" fill="{LIME}"/>',
         f'<polygon points="{P((220, 268), (252, 357), (258, 352))}" fill="#9cc41c"/>',
         # ridge + edge highlights
         f'<line x1="{F[0]}" y1="{F[1]}" x2="{R[0]}" y2="{R[1]}" stroke="{LIME}" stroke-width="4" stroke-linecap="round"/>',
         f'<polyline points="{P(FL, F, FR)}" fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/>',
         f'<line x1="{FR[0]}" y1="{FR[1]}" x2="{RR[0]}" y2="{RR[1]}" stroke="#8f8a7d" stroke-width="1.2"/>',
         '</g>']
    return (352, '\n'.join(t))


def icon(name, seed, obj, skip=()):
    items = trees(seed, skip) + [obj]
    body = token(seed) + [s for _, s in sorted(items, key=lambda i: i[0])]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">\n'
           f'<defs>{DEFS}</defs>\n<g id="{name}">\n' + '\n'.join(body) + '\n</g>\n</svg>\n')
    path = os.path.join(HERE, name + '.svg')
    open(path, 'w', encoding='utf-8').write(svg)
    print('wrote', path, len(svg))


if __name__ == '__main__':
    icon('个人', 7, person())
    icon('避难帐篷', 11, tent(), skip=((240, 300),))
