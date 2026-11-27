"""Real route data: home (一渡新新小镇) -> shelters, from OSM roads + 30 m DEM. Writes route_data.json."""
import json, math, heapq, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
g = json.load(open(os.path.join(ROOT, 'shenjia_an_4km_osm.geojson'), encoding='utf-8'))
L = open(os.path.join(ROOT, 'output_hh.asc')).read().split('\n')
hd = {l.split()[0]: float(l.split()[1]) for l in L[:6] if l.strip() and l.split()[0][0].isalpha()}
rows = [list(map(float, l.split())) for l in L[6:] if l.strip()]
nc, nr = int(hd['ncols']), int(hd['nrows']); x0, y0, cs = hd['xllcorner'], hd['yllcorner'], hd['cellsize']
def z(lon, lat):
    c = (lon-x0)/cs-.5; r = nr-1-((lat-y0)/cs-.5)
    c = min(max(c, 0), nc-1.001); r = min(max(r, 0), nr-1.001); i, j = int(r), int(c); fr, fc = r-i, c-j
    a = rows[i][j]*(1-fc)+rows[i][j+1]*fc; b = rows[i+1][j]*(1-fc)+rows[i+1][j+1]*fc; return a*(1-fr)+b*fr
d = lambda a, b: math.hypot((a[0]-b[0])*111320*math.cos(math.radians(39.59)), (a[1]-b[1])*110540)
adj = {}
for f in g['features']:
    h = f['properties'].get('highway'); gm = f['geometry']
    if not h or h == 'construction': continue
    for ln in ([gm['coordinates']] if gm['type'] == 'LineString' else gm['coordinates']):
        for a, b in zip(ln, ln[1:]):
            a, b = tuple(a), tuple(b); w = d(a, b); adj.setdefault(a, []).append((b, w)); adj.setdefault(b, []).append((a, w))
nodes = list(adj); near = lambda p: min(nodes, key=lambda n: d(n, p))
def route(A, B):
    s, t = near(A), near(B); D = {s: 0}; P = {}; q = [(0, s)]
    while q:
        c, u = heapq.heappop(q)
        if u == t: break
        if c > D[u]: continue
        for v, w in adj[u]:
            if c+w < D.get(v, 1e18): D[v] = c+w; P[v] = u; heapq.heappush(q, (c+w, v))
    p = [t]
    while p[-1] != s: p.append(P[p[-1]])
    return [A] + p[::-1] + [B]
river = []
for f in g['features']:
    p = f['properties']; gm = f['geometry']
    if p.get('natural') == 'water' or p.get('waterway') == 'river':
        cc = gm['coordinates']
        river += cc if gm['type'] == 'LineString' else [q for r in (cc if gm['type'] == 'Polygon' else [r for pp in cc for r in pp]) for q in r]
HOME = (115.68151, 39.59014)
SH = {'school': (115.67320, 39.59635), 'fire': (115.673, 39.6035), 'village': (115.67797, 39.59589)}
out = {'home': HOME, 'home_z': z(*HOME), 'home_river': min(d(HOME, q) for q in river), 'shelters': {}}
for k, pt in SH.items():
    path = route(HOME, pt)
    prof, acc = [], 0
    for a, b in zip(path, path[1:]):
        n = max(1, int(d(a, b)/10))
        for i in range(n):
            prof.append((acc + d(a, b)*i/n, z(a[0]+(b[0]-a[0])*i/n, a[1]+(b[1]-a[1])*i/n)))
        acc += d(a, b)
    prof.append((acc, z(*path[-1])))
    zs = [p[1] for p in prof]
    up = sum(max(0, b-a) for a, b in zip(zs, zs[1:]))
    out['shelters'][k] = dict(pt=pt, path=path, dist=acc, up=up, z=z(*pt), river=min(d(pt, q) for q in river), profile=prof,
                              low=min(prof, key=lambda p: p[1]), high=max(prof, key=lambda p: p[1]))
    m = 60/1.39*0.0  # placeholder
    for v in (0.6, 0.5):
        out['shelters'][k][f't{v}'] = acc/v/60 + up/10*(1.39/v) + 10
json.dump(out, open(os.path.join(HERE, 'route_data.json'), 'w'))
for k, s in out['shelters'].items():
    print(k, 'dist', round(s['dist']), 'up', round(s['up']), 'z', round(s['z']), 'river', round(s['river']), 't0.6', round(s['t0.6']), 't0.5', round(s['t0.5']), 'low', [round(x) for x in s['low']])
print('home z', round(out['home_z']), 'home river', round(out['home_river']))
