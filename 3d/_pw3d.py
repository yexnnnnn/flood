#!/usr/bin/env python3
"""preview helper: python3 _pw3d.py <prefix> '<js step>' ...  -> screenshots/<prefix>.js (run with playwright browser_run_code_unsafe)
each step is evaluated in the page, then a screenshot <prefix><k>.png is taken. Optional env W,H for the viewport."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = '/projects/sandbox/.kiro/artifacts/screenshots/'
pre, steps = sys.argv[1], sys.argv[2:]
W, H = int(os.environ.get('W', 1600)), int(os.environ.get('H', 900))
html = open(os.path.join(HERE, os.environ.get('PAGE', 'index.html')), encoding='utf-8').read()
js = f'''async (page) => {{
  const H = {json.dumps(html)};
  const S = {json.dumps(steps)};
  const p = await page.context().newPage(); await p.setViewportSize({{ width: {W}, height: {H} }});
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => {{ if (m.type() === 'error') errs.push(m.text()); }});
  await p.route('https://x.test/**', r => r.fulfill({{ status: 200, contentType: 'text/html; charset=utf-8', body: H }}));
  await p.goto('https://x.test/3d.html{os.environ.get('QS', '')}');
  await p.waitForFunction(() => window.READY || window.FAIL, null, {{ timeout: 120000 }});
  const info = await p.evaluate(() => JSON.stringify(window.READY || window.FAIL));
  let k = 0;
  for (const s of S) {{
    if (s) await p.evaluate(s); await p.waitForTimeout(1800);
    await p.screenshot({{ path: '{SHOTS}{pre}' + k + '.png' }}); k++;
  }}
  await p.close(); return info + ' errs: ' + JSON.stringify(errs).slice(0, 1500);
}}'''
open(SHOTS + pre + '.js', 'w', encoding='utf-8').write(js)
print('wrote', SHOTS + pre + '.js', len(js) // 1024, 'KB')
