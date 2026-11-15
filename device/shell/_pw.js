// preview helper: node _pw.js <prefix> '<js step>' ...  -> screenshots/<prefix>.js (run with playwright browser_run_code_unsafe)
const fs = require('fs'), path = require('path');
const SH = '/projects/sandbox/.kiro/artifacts/screenshots/', V = path.join(__dirname, 'out/view');
const E = {}; for (const f of fs.readdirSync(V)) E[f] = f.endsWith('.json') ? fs.readFileSync(path.join(V, f), 'utf8') : fs.readFileSync(path.join(V, f)).toString('base64');
let html = fs.readFileSync(path.join(__dirname, 'view.html'), 'utf8').replace('<script>', '<script>window.EMBED=' + JSON.stringify(E) + ';</script><script>');
const [pre, ...steps] = process.argv.slice(2), W = +(process.env.W || 1400), H = +(process.env.H || 900);
const js = `async (page) => {
  const H = ${JSON.stringify(html)}; const S = ${JSON.stringify(steps)};
  const p = await page.context().newPage(); await p.setViewportSize({ width: ${W}, height: ${H} });
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.route('https://x.test/**', r => r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: H }));
  await p.goto('https://x.test/view.html'); await p.waitForFunction(() => window.READY || window.FAIL, null, { timeout: 120000 });
  const info = await p.evaluate(() => String(window.FAIL || 'ok')); let k = 0;
  for (const s of S) { if (s) await p.evaluate(s); await p.waitForTimeout(1500); await p.screenshot({ path: '${SH}${pre}' + k + '.png' }); k++; }
  await p.close(); return info + ' errs: ' + JSON.stringify(errs).slice(0, 1500); }`;
fs.writeFileSync(SH + pre + '.js', js); console.log('wrote', pre, (js.length / 1e6).toFixed(1) + 'MB');
