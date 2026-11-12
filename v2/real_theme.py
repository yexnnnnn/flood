#!/usr/bin/env python3
"""Shared pieces of the 写实 · 玻璃 theme (dark-green photoreal map + frosted-glass UI).

Used by build_real.py (web page -> v2/real.html) and frames_real.py (Figma frames -> v2/figma/写实/).
The light paper version (index.html, figma/*.svg) is left as it is.
"""
import design as D
import map_real as MR

BG = '#0d140f'                 # page / frame background under the map
DARK = '#10160f'               # text on white or light surfaces
GLASS = dict(fill='#0f1812', op=.42, stroke='#ffffff', sop=.16)    # SVG stand-in for frosted glass (Figma: add Background blur)
# level text colours readable on dark green (the paper version uses darker txt colours)
TXT = ['#c9c3e6', '#8fb3ff', '#ffc21a', '#ff7a33', '#ff4d76']

def lv_dark():
    return [dict(L, txt=TXT[i]) for i, L in enumerate(D.LV)]

def map_layers(pre=''):
    """the map in map units (0..1000): photoreal base, white roads, pill labels, soft fades at the frame-facing edges"""
    return (f'<g id="{pre}地图">' + MR.base() + MR.roads() + MR.labels()
            + f'<rect id="{pre}左缘渐隐" x="-80" y="-80" width="378" height="1160" fill="url(#edgeL)"/>'
            + f'<rect id="{pre}右缘渐隐" x="820" y="-80" width="260" height="1160" fill="url(#edgeR)"/>'
            + f'<rect id="{pre}上缘渐隐" x="-80" y="-80" width="1160" height="240" fill="url(#edgeT)"/>'
            + f'<rect id="{pre}下缘渐隐" x="-80" y="842" width="1160" height="240" fill="url(#edgeB)"/></g>')

def defs_extra():
    return (f'<linearGradient id="edgeL" x1="0" x2="1"><stop offset="0" stop-color="{BG}" stop-opacity="1"/><stop offset=".21" stop-color="{BG}" stop-opacity="1"/><stop offset=".3" stop-color="{BG}" stop-opacity=".85"/><stop offset=".6" stop-color="{BG}" stop-opacity=".35"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="edgeR" x1="1" x2="0"><stop offset="0" stop-color="{BG}" stop-opacity="1"/><stop offset=".3" stop-color="{BG}" stop-opacity="1"/><stop offset=".4" stop-color="{BG}" stop-opacity=".8"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="edgeT" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{BG}" stop-opacity="1"/><stop offset=".34" stop-color="{BG}" stop-opacity="1"/><stop offset=".46" stop-color="{BG}" stop-opacity=".75"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="edgeB" x1="0" x2="0" y1="1" y2="0"><stop offset="0" stop-color="{BG}" stop-opacity="1"/><stop offset=".34" stop-color="{BG}" stop-opacity="1"/><stop offset=".46" stop-color="{BG}" stop-opacity=".75"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>')

def backdrop(W=1920, H=1080):
    """solid dark ground behind the map; the map edges fade into it (a blurred photo here left hard map edges)"""
    return f'<rect id="底色" width="{W}" height="{H}" fill="{BG}"/>'

def glass(id_, x, y, w, h, r=28):
    g = GLASS
    return (f'<g id="{id_}"><rect id="玻璃" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{g["fill"]}" fill-opacity="{g["op"]}"/>'
            f'<rect id="高光描边" x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{r}" fill="none" stroke="{g["stroke"]}" stroke-opacity="{g["sop"]}"/></g>')
