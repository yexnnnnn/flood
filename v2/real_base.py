#!/usr/bin/env python3
"""写实底图 (style B): an aerial-photo-like raster painted from our own data, no imagery used.

The terrain fields (shading, slope, elevation, riverbed) are packed into two PNGs and handed to a
canvas renderer that runs in the Playwright browser (the sandbox has no numpy/PIL):
  land cover from slope / elevation / riverbed / house density -> fields, forest canopy, gravel bar,
  river channel, then hillshade multiplied over everything.
Colours were picked from the Google Earth screenshots of 沈家庵村 (Sept 2024) as reference only.

usage: python3 real_base.py <tag>      -> writes the Playwright script ../.kiro/.../real.js
       (run it, then) python3 real_base.py take <tag> -> copies the rendered jpeg to v2/_real.jpg
"""
import os, sys, json, base64, shutil
import map_styles as S

D, BW = S.D, S.BW
SHOTS = '/projects/sandbox/.kiro/artifacts/screenshots/'
PX = 2400                                    # 1 px = 1 m (map is 2.4 km wide)
JPG = os.path.join(D.HERE, '_real.jpg')

def bedv(i, j):
    """riverbed strength: 255 on the active bed, fading out over 3 m above it (wider gravel bar than S.bed)"""
    b = BW.BED[(j * BW.N // S.M) * BW.N + (i * BW.N // S.M)]
    if b <= 0: return 0
    return int(255 * max(0.0, min(1.0, (b / 10 + 3.0 - S.U[j * S.M + i]) / 3.0)))

def fields():
    M, U, SH = S.M, S.U, S.SH
    r1, r2 = [], []
    for j in range(M):
        a, b = bytearray(), bytearray()
        for i in range(M):
            k = j * M + i
            a += bytes((int((SH[2 * k] + 1) * 127.5), int(SH[2 * k + 1] * 255), int((U[k] - S.LO) / (S.HI - S.LO) * 255)))
            b += bytes((bedv(i, j), 0, 0))
        r1.append(a); r2.append(b)
    uri = lambda rows: 'data:image/png;base64,' + base64.b64encode(D.png_rgb(M, M, rows)).decode()
    return uri(r1), uri(r2)

def geometry():
    pd, ch = S.pts_d, S.chaikin
    return dict(
        LO=S.LO, HI=S.HI, PX=PX,
        river=pd(ch(BW.RIV, 3)), water=list(BW.WATER), ditch=list(BW.DITCH),
        gully=[pd(ch(g['path'] + g.get('run', []), 2)) for g in BW.gs],
        roads=[dict(k=r['k'], d=pd(ch(r['p'], 1))) for r in S.G['roads']],
        houses=[(round(h['x'], 2), round(h['y'], 2), round(max(h['w'], h['d']), 2), round(h['w'], 2), round(h['d'], 2), round(h['a'], 1)) for h in S.REG],
    )

def script(tag):
    f1, f2 = fields(); g = geometry()
    js = open(os.path.join(D.HERE, 'real_render.js'), encoding='utf-8').read()
    html = ('<!doctype html><html><body style="margin:0;background:#000"><canvas id="c" width="%d" height="%d"></canvas>'
            '<script>const F1=%s,F2=%s,G=%s;\n%s</script></body></html>') % (PX, PX, json.dumps(f1), json.dumps(f2), json.dumps(g), js)
    pw = f'''async (page) => {{
  const H = {json.dumps(html)};
  const p = await page.context().newPage(); await p.setViewportSize({{ width: {PX}, height: {PX} }});
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => errs.push(m.text()));
  await p.setContent(H, {{ waitUntil: 'commit' }});
  await p.waitForFunction(() => window.DONE || window.FAIL, null, {{ timeout: 170000 }});
  await p.screenshot({{ path: '{SHOTS}_real_{tag}.jpg', type: 'jpeg', quality: 90 }});
  await p.close(); return errs.join(' | ').slice(0, 2000) || 'ok';
}}'''
    open(SHOTS + f'real_{tag}.js', 'w', encoding='utf-8').write(pw); print('wrote', SHOTS + f'real_{tag}.js', len(pw) // 1024, 'KB')

if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'take': shutil.copy(SHOTS + f'_real_{a[1]}.jpg', JPG); print('->', JPG, os.path.getsize(JPG) // 1024, 'KB')
    else: script(a[0] if a else 'a')
