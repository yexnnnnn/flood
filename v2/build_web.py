#!/usr/bin/env python3
"""v2 interactive page -> v2/index.html (single file, no build step at runtime).

Same drawing as the Figma frames: map layers, gradients and signal positions come from design.py.
Presentation mode: ← / → (or click) steps through the storm. Explore mode (E): tap what you see.
"""
import os, json
import design as D
import frames as F

HERE = D.HERE
TPL = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()

sig = {}
for k, v in D.SIG.items():
    sig[k] = {q: v.get(q) for q in ('g', 's', 'f', 'why', 'src', 'at', 'type', 'x', 'y', 'h')}
reach = {'14': D.BW.pts_d(D.BW.REACH14), 'surge': D.BW.pts_d(D.BW.REACH_SURGE)}
steps = []
for S in D.story_states():
    steps.append({q: S.get(q) for q in ('kind', 't', 'focus', 'obs', 'lv')})
data = dict(SIG=sig, RULES=D.RULES, LV=D.LV, STEPS=steps, GRP=D.GRP, REACH=reach,
            ORDER=list(D.SIG.keys()), MAP=dict(x=F.MAP_X, y=F.MAP_Y, s=F.MAP_S))

markers = ''.join(D.marker_svg('', k) for k in D.SIG if k != 'surge')
html = (TPL.replace('__DEFS__', D.defs())
           .replace('__MAP__', D.map_layers('', F.HS))
           .replace('__MARKERS__', markers)
           .replace('__MAPTF__', f'translate({F.MAP_X} {F.MAP_Y}) scale({F.MAP_S})')
           .replace('__DATA__', json.dumps(data, ensure_ascii=False)))
out = os.path.join(HERE, 'index.html')
open(out, 'w', encoding='utf-8').write(html)
print('wrote', out, len(html) // 1024, 'KB')
