#!/usr/bin/env python3
"""Bake the ground texture and the land-cover mask for the 3D diorama (3d/_tex/ground.jpg, 3d/_tex/mask.jpg).

The sandbox has no PIL/numpy, so the painting runs in the Playwright browser (3d/tex_render.js), fed with the same
fields and geometry as the v2 写实 base (v2/real_base.py).

usage: python3 3d/build_tex.py            -> writes the Playwright script (.kiro/artifacts/screenshots/tex3d.js); run it,
       python3 3d/build_tex.py take       -> copies the two renders into 3d/_tex/
"""
import os, sys, json, shutil, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'v2'))
with contextlib.redirect_stdout(io.StringIO()):
    import real_base as RB
SHOTS = '/projects/sandbox/.kiro/artifacts/screenshots/'
OUT = os.path.join(HERE, '_tex')

def script():
    f1, f2 = RB.fields(); g = RB.geometry(); PX = g['PX']
    js = open(os.path.join(HERE, 'tex_render.js'), encoding='utf-8').read()
    html = ('<!doctype html><html><body style="margin:0;background:#000"><canvas id="c" width="%d" height="%d"></canvas>'
            '<script>const F1=%s,F2=%s,G=%s;\n%s</script></body></html>') % (PX, PX, json.dumps(f1), json.dumps(f2), json.dumps(g), js)
    pw = f'''async (page) => {{
  const H = {json.dumps(html)};
  const p = await page.context().newPage(); await p.setViewportSize({{ width: {PX}, height: {PX} }});
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => errs.push(m.text()));
  await p.setContent(H, {{ waitUntil: 'commit' }});
  await p.waitForFunction(() => window.DONE || window.FAIL, null, {{ timeout: 170000 }});
  await p.screenshot({{ path: '{SHOTS}_tex3d_ground.jpg', type: 'jpeg', quality: 88 }});
  await p.evaluate(() => window.MASK && window.MASK());
  await p.screenshot({{ path: '{SHOTS}_tex3d_mask.jpg', type: 'jpeg', quality: 92 }});
  await p.close(); return errs.join(' | ').slice(0, 2000) || 'ok';
}}'''
    open(SHOTS + 'tex3d.js', 'w', encoding='utf-8').write(pw); print('wrote', SHOTS + 'tex3d.js', len(pw) // 1024, 'KB')

if __name__ == '__main__':
    if sys.argv[1:2] == ['take']:
        os.makedirs(OUT, exist_ok=True)
        for a, b in (('_tex3d_ground.jpg', 'ground.jpg'), ('_tex3d_mask.jpg', 'mask.jpg')):
            shutil.copy(SHOTS + a, os.path.join(OUT, b)); print('->', b, os.path.getsize(os.path.join(OUT, b)) // 1024, 'KB')
    else:
        script()
