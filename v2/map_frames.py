#!/usr/bin/env python3
"""Map style board: one Figma-ready frame per style -> v2/figma/地图样式/*.svg, plus v2/maps.html to flip through them."""
import os, sys
import design as D, map_styles as S
from frames import t, lines, MAP_X, MAP_Y, MAP_S

OUT = os.path.join(D.HERE, 'figma', '地图样式'); os.makedirs(OUT, exist_ok=True)
W, H, INK, PAPER, MONO = D.W, D.H, D.INK, D.PAPER, D.MONO
OBS = ['07', '03', '09', '11']; LVOF = D.sig_level(OBS)
CX = sum(h['x'] for h in S.REG) / len(S.REG); CY = sum(h['y'] for h in S.REG) / len(S.REG)

def signs():
    s = ['<g id="征兆光">'] + [D.glow_svg('', i, LVOF.get(i, 0)) for i in OBS] + ['</g><g id="观察点">']
    s += [D.marker_svg('', i, on=i in OBS) for i in D.SIG if i != 'surge'] + ['</g>']
    return ''.join(s)

def frame(k, key, name, en, desc):
    body = S.style_svg(key)
    b = [f'<g id="地图组" transform="translate({MAP_X} {MAP_Y}) scale({MAP_S})">{body}{signs()}</g>']
    b.append(f'<rect id="左侧渐隐" x="0" y="0" width="1000" height="{H}" fill="url(#fadeL)"/>')
    b.append(t(96, 120, f'地图组件 · 样式 {key} / M{len(S.STYLES) - 1}', 16, fam=MONO, ls=2.5, op=.55, id_='眉题'))
    b.append(t(90, 270, name, 112, w=700, ls=-3, id_='样式名') + t(96, 322, en.upper(), 18, fam=MONO, ls=3, op=.55, id_='英文名'))
    b.append(lines(96, 392, D.wrap(desc, 17), 26, 40, '说明', op=.66))
    # zoom inset on the village: same drawing, 2.9x
    ix, iy, iw, ih, k2 = 96, 560, 470, 330, 2.9
    tx, ty = ix + iw / 2 - CX * k2, iy + ih / 2 - CY * k2
    inset = body.replace('<g id="边缘渐隐"', '<g display="none" id="边缘渐隐-局部"').replace('id="', 'id="局部-')
    b.append(f'<defs><clipPath id="clipInset"><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="18"/></clipPath></defs>'
             f'<g id="局部放大"><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="18" fill="{PAPER}"/>'
             f'<g clip-path="url(#clipInset)"><g transform="translate({tx:.1f} {ty:.1f}) scale({k2})">{inset}</g></g>'
             f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="18" fill="none" stroke="{INK}" stroke-opacity=".12"/></g>')
    b.append(t(ix, iy + ih + 34, '村子 · 局部放大 ×2.3', 15, fam=MONO, ls=1.5, op=.5, id_='放大说明'))
    row = ['<g id="样式切换">']
    for n, (kk, nm, *_r) in enumerate(S.STYLES):
        on = kk == key; x = 96 + n * 76
        row.append(t(x, 1000, kk, 15, fam=MONO, op=1 if on else .35, w=700 if on else 400) + t(x, 1024, nm, 15, op=1 if on else .4))
        if on: row.append(f'<rect x="{x}" y="972" width="28" height="3" rx="1.5" fill="{INK}"/>')
    b.append(''.join(row) + '</g>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{D.defs().replace("</defs>", S.EXTRA_DEFS + "</defs>")}'
           f'<g id="{key} {name}"><rect id="背景" width="{W}" height="{H}" fill="{PAPER}"/>{"".join(b)}</g></svg>')
    fn = f'{key} {name}.svg'
    open(os.path.join(OUT, fn), 'w', encoding='utf-8').write(svg)
    return fn, len(svg)

GALLERY = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>地图组件 · 样式</title><style>
html,body{margin:0;height:100%;background:#f5f3ef;font-family:"Noto Sans SC","PingFang SC",sans-serif;color:#161514;overflow:hidden}
#v{position:absolute;inset:0 0 64px 0;display:grid;place-items:center}
#v img{max-width:100%;max-height:100%;box-shadow:0 10px 50px rgba(22,21,20,.08);background:#f5f3ef}
nav{position:absolute;left:0;right:0;bottom:0;height:64px;display:flex;gap:6px;align-items:center;justify-content:center}
nav button{border:0;background:transparent;font:500 15px "Noto Sans SC",sans-serif;padding:8px 16px;border-radius:999px;cursor:pointer;color:rgba(22,21,20,.55)}
nav button.on{background:#fff;color:#161514;box-shadow:0 1px 8px rgba(22,21,20,.08)}
nav span{font:400 13px "JetBrains Mono",monospace;opacity:.45;margin-left:18px}
</style></head><body><div id="v"><img id="im" alt=""></div><nav id="n"></nav><script>
const S = __S__; const n = document.getElementById('n'), im = document.getElementById('im'); let k = 1;
n.innerHTML = S.map((s, i) => `<button data-i="${i}">${s[0]} ${s[1]}</button>`).join('') + '<span>← → 或 0–5 切换</span>';
S.forEach(s => { const p = new Image(); p.src = 'figma/地图样式/' + encodeURIComponent(s[2]); });
function go(i) { k = (i + S.length) % S.length; im.src = 'figma/地图样式/' + encodeURIComponent(S[k][2]); n.querySelectorAll('button').forEach((b, j) => b.classList.toggle('on', j === k)); history.replaceState(null, '', '#' + S[k][0]); }
n.onclick = e => { if (e.target.dataset.i) go(+e.target.dataset.i); };
addEventListener('keydown', e => { if (e.key === 'ArrowRight') go(k + 1); if (e.key === 'ArrowLeft') go(k - 1); if (/^[0-9]$/.test(e.key) && +e.key < S.length) go(+e.key); });
const h = S.findIndex(s => '#' + s[0] === location.hash); go(h < 0 ? 1 : h);
</script></body></html>'''

if __name__ == '__main__':
    only = sys.argv[1:]
    made = []
    for k, (key, name, en, desc, _) in enumerate(S.STYLES):
        if only and key not in only: continue
        fn, n = frame(k, key, name, en, desc); made.append(fn); print(fn, n // 1024, 'KB')
    import json
    open(os.path.join(D.HERE, 'maps.html'), 'w', encoding='utf-8').write(
        GALLERY.replace('__S__', json.dumps([(k, n, f'{k} {n}.svg') for k, n, *_ in S.STYLES], ensure_ascii=False)))
