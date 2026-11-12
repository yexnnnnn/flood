#!/usr/bin/env python3
"""v2 interactive page, 写实 · 玻璃 theme -> v2/real.html

Same template, rules and story as index.html (build_web.py). Differences: the map is the photoreal M7 base
with white roads and pill labels, the UI sits on frosted-glass panels, text is white, level text colours are
the brighter set from real_theme.TXT.
"""
import os, json
import design as D
import frames as F
import real_theme as RT
import map_real as MR

HERE = D.HERE
TPL = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()

sig = {k: {q: v.get(q) for q in ('g', 's', 'f', 'why', 'src', 'at', 'type', 'x', 'y', 'h')} for k, v in D.SIG.items()}
reach = {'14': D.BW.pts_d(D.BW.REACH14), 'surge': D.BW.pts_d(D.BW.REACH_SURGE)}
steps = [{q: S.get(q) for q in ('kind', 't', 'focus', 'obs', 'lv')} for S in D.story_states()]
data = dict(SIG=sig, RULES=D.RULES, LV=RT.lv_dark(), STEPS=steps, GRP=D.GRP, REACH=reach,
            ORDER=list(D.SIG.keys()), MAP=dict(x=F.MAP_X, y=F.MAP_Y, s=F.MAP_S))

CSS = """
/* ---------------- 写实 · 玻璃 theme (overrides) ---------------- */
:root { --paper:#0d140f; --ink:#ffffff; --glass:rgba(14,22,16,.36); --edge:rgba(255,255,255,.16); --dark:#10160f; }
html, body, #stage { background:#0d140f; color:#fff; }
.fadeL, .fadeB { display:none; }
.glass { position:absolute; pointer-events:none !important; border-radius:28px; background:var(--glass);
  -webkit-backdrop-filter:blur(26px) saturate(1.4); backdrop-filter:blur(26px) saturate(1.4);
  border:1px solid var(--edge); box-shadow:inset 0 1px 0 rgba(255,255,255,.14), 0 24px 70px rgba(0,0,0,.28); }
.atm { mix-blend-mode:screen; }
.mono { opacity:.62; }
.seg { background:rgba(14,22,16,.4); -webkit-backdrop-filter:blur(20px); backdrop-filter:blur(20px); border:1px solid var(--edge); }
.seg button { color:rgba(255,255,255,.7); }
.seg button.on { background:#fff; color:var(--dark); box-shadow:none; }
a.ghost { color:rgba(255,255,255,.7); } a.ghost:hover { color:#fff; }
.why, .sub { color:rgba(255,255,255,.72); }
.pill { color:var(--dark); }
.pill.miss { border-color:rgba(255,255,255,.45); color:rgba(255,255,255,.62); }
.op { opacity:.6; }
.badge, .orb, .lvup div { color:var(--dark); }
.where .v { text-shadow:0 1px 8px rgba(0,0,0,.6); }
.where svg line { stroke:#fff; }
.meter i { background:rgba(255,255,255,.16); }
.meter span { opacity:.45; }
.dots i { background:#fff; opacity:.28; }
.start button { background:#fff; color:var(--dark); }
.start span { opacity:.7; }
.xwhy { color:rgba(255,255,255,.78); } .xwhy .next { color:rgba(255,255,255,.55); }
.xtools { top:724px; } .latch { top:772px; color:rgba(255,255,255,.7); }
.dock { top:852px; }
.chip { border-color:rgba(255,255,255,.28); color:rgba(255,255,255,.85); background:rgba(255,255,255,.04); }
.chip.on { background:#fff; color:var(--dark); }
.chip.act2 { background:transparent; color:#fff; border-color:rgba(255,255,255,.6); }
.card { background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.18); color:#fff; }
.card.on { background:rgba(255,255,255,.94); color:var(--dark); box-shadow:0 6px 24px rgba(0,0,0,.25); }
.card .d { border-color:rgba(255,255,255,.45); }
.tip { background:rgba(14,22,16,.62); -webkit-backdrop-filter:blur(24px) saturate(1.4); backdrop-filter:blur(24px) saturate(1.4);
  border:1px solid var(--edge); color:#fff; box-shadow:0 20px 60px rgba(0,0,0,.35); }
.tip .w { color:rgba(255,255,255,.78); }
.note { opacity:.55; }
/* markers: white rings on the photo */
.mk circle:first-child { fill:#fff; fill-opacity:.22; stroke:#fff; stroke-opacity:.85; }
.mk circle:nth-child(2) { fill:#fff; }
.mk.on circle:first-child { fill-opacity:0; stroke-opacity:1; }
"""
G = lambda x, y, w, h: f'<div class="glass" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>'
INS = {
    '<div id="cover">': G(48, 56, 900, 968),
    '<div id="pres" class="hide">': G(48, 56, 720, 808),
    '<div id="end" class="hide">': G(48, 56, 900, 720),
    '<div id="bar">': G(48, 880, 1824, 156),
    '<div id="explore" class="hide">': G(48, 56, 780, 756) + G(48, 830, 1824, 190),
}

markers = ''.join(D.marker_svg('', k) for k in D.SIG if k != 'surge')
html = (TPL.replace('__DEFS__', D.defs().replace('</defs>', RT.defs_extra() + '</defs>'))
           .replace('__MAP__', RT.map_layers(''))
           .replace('__MARKERS__', markers)
           .replace('__MAPTF__', f'translate({F.MAP_X} {F.MAP_Y}) scale({F.MAP_S})')
           .replace('__DATA__', json.dumps(data, ensure_ascii=False)))
PILL = "${r.fired ? 'aa' : '88'}"
assert html.count(PILL) == 1
html = html.replace(PILL, "${r.fired ? '' : 'cc'}")   # solid, bright pills on the dark glass
html = html.replace('</style>', CSS + '</style>', 1)
html = html.replace('<title>看见什么，就升到哪一级 · 沈家庵村</title>', '<title>看见什么，就升到哪一级 · 沈家庵村 · 写实</title>')
for k, v in INS.items():
    assert html.count(k) == 1, k
    html = html.replace(k, k + v)
out = os.path.join(HERE, 'real.html')
open(out, 'w', encoding='utf-8').write(html)
print('wrote', out, len(html) // 1024, 'KB')
