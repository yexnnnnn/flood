"""Prepare the real-geography data for the diorama (pure Python, no numpy).
Output: shenjia_data.json in local metres: x = east, z = south, origin = crop centre."""
import json, math, heapq
D = '/projects/sandbox/flood/'
C_LON, C_LAT, HALF, N = 115.6785, 39.5950, 1200.0, 160          # 2.4 km square, 15 m cells
KX = 111320 * math.cos(math.radians(C_LAT)); KY = 110540.0
rows = [l.split() for l in open(D + 'output_hh.asc').read().splitlines()[6:]]
Z = [[float(v) for v in r] for r in rows]; nr, nc = len(Z), len(Z[0])
x0, y0, cs = 115.654861100000, 39.577916677778, 0.000277777778; lat0 = y0 + nr * cs
def dem(lon, lat):  # bilinear on cell centres
    fi = (lon - x0) / cs - 0.5; fj = (lat0 - lat) / cs - 0.5
    i = max(0, min(nc - 2, int(math.floor(fi)))); j = max(0, min(nr - 2, int(math.floor(fj)))); u = min(1, max(0, fi - i)); v = min(1, max(0, fj - j))
    return (Z[j][i] * (1 - u) + Z[j][i + 1] * u) * (1 - v) + (Z[j + 1][i] * (1 - u) + Z[j + 1][i + 1] * u) * v
loc = lambda lon, lat: ((lon - C_LON) * KX, (C_LAT - lat) * KY)
ll = lambda x, z: (C_LON + x / KX, C_LAT - z / KY)
cell = 2 * HALF / N; cx = lambda i: -HALF + (i + 0.5) * cell
E = [[dem(*ll(cx(i), cx(j))) for i in range(N)] for j in range(N)]
g = json.load(open(D + 'shenjia_an_4km_osm.geojson'))
inside = lambda p, m=0: abs(p[0]) <= HALF + m and abs(p[1]) <= HALF + m
def lines_of(f):
    gt, co = f['geometry']['type'], f['geometry']['coordinates']
    return [co] if gt == 'LineString' else co if gt == 'MultiLineString' else []
# --- river centreline (拒马河), extended to the crop edges, and carved into the 30 m DEM
river = []
for f in g['features']:
    p = f['properties']
    if p.get('waterway') == 'river' and p.get('name') == '拒马河':
        for L in lines_of(f): river += [loc(*q) for q in L]
def seg_d(px, pz, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dz * dz or 1e-9; t = max(0, min(1, ((px - a[0]) * dx + (pz - a[1]) * dz) / L2))
    return math.hypot(px - a[0] - dx * t, pz - a[1] - dz * t)
def rdist(px, pz): return min(seg_d(px, pz, river[k - 1], river[k]) for k in range(1, len(river)))
RD = [[rdist(cx(i), cx(j)) for i in range(N)] for j in range(N)]
# river water surface along the channel: take the lowest DEM near the centreline, smooth along it, monotone downstream
surf = []
for k, (rx, rz) in enumerate(river):
    lo = min(E[j][i] for j in range(N) for i in range(N) if abs(cx(i) - rx) < 50 and abs(cx(j) - rz) < 50) if inside((rx, rz), 40) else None
    surf.append(lo)
vals = [v for v in surf if v is not None]
for k in range(len(surf)):
    if surf[k] is None: surf[k] = vals[0] if k < len(surf) // 2 else vals[-1]
for k in range(1, len(surf)): surf[k] = min(surf[k], surf[k - 1])        # flows downstream (N -> S)
def river_bed_at(px, pz):
    best, bk = 1e9, 0
    for k in range(1, len(river)):
        d = seg_d(px, pz, river[k - 1], river[k])
        if d < best: best, bk = d, k
    return surf[bk] - 2.5
W_CH = 55.0   # half-width of the main low-flow channel bed in metres (braided river ~ 100-140 m wide here)
for j in range(N):
    for i in range(N):
        d = RD[j][i]
        if d < W_CH * 2.2:
            bed = river_bed_at(cx(i), cx(j)); w = max(0, 1 - (d / (W_CH * 2.2)) ** 2)
            E[j][i] = min(E[j][i], bed + (E[j][i] - bed) * (1 - w) + 0) if d < W_CH else min(E[j][i], bed + 2.5 + (d - W_CH) * 0.06 + (E[j][i] - bed - 2.5) * (1 - w))
# --- priority-flood + D8 flow accumulation on the resampled grid
F = [r[:] for r in E]; seen = [[False] * N for _ in range(N)]; pq = []
for j in range(N):
    for i in range(N):
        if i in (0, N - 1) or j in (0, N - 1): heapq.heappush(pq, (F[j][i], j, i)); seen[j][i] = True
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
while pq:
    h, j, i = heapq.heappop(pq)
    for dj, di in N8:
        b, a = j + dj, i + di
        if 0 <= b < N and 0 <= a < N and not seen[b][a]: seen[b][a] = True; F[b][a] = max(F[b][a], h + 1e-3); heapq.heappush(pq, (F[b][a], b, a))
down = [[-1] * N for _ in range(N)]
for j in range(N):
    for i in range(N):
        best, bd = 0, -1
        for dj, di in N8:
            b, a = j + dj, i + di
            if 0 <= b < N and 0 <= a < N:
                s = (F[j][i] - F[b][a]) / (cell * math.hypot(dj, di))
                if s > best: best, bd = s, b * N + a
        down[j][i] = bd
acc = [[1.0] * N for _ in range(N)]
for _, j, i in sorted(((F[j][i], j, i) for j in range(N) for i in range(N)), reverse=True):
    d = down[j][i]
    if d >= 0: acc[d // N][d % N] += acc[j][i]
slope = [[0.0] * N for _ in range(N)]
for j in range(N):
    for i in range(N):
        a, b = max(0, i - 1), min(N - 1, i + 1); c, d = max(0, j - 1), min(N - 1, j + 1)
        slope[j][i] = math.hypot((E[j][b] - E[j][a]) / ((b - a) * cell), (E[d][i] - E[c][i]) / ((d - c) * cell))
# --- tributary gullies: steep channels that reach the valley floor; keep the path from the head to the river
def upstream_path(j, i):  # follow the largest tributary upwards
    path = [(j, i)]
    while True:
        best = None
        for dj, di in N8:
            b, a = j + dj, i + di
            if 0 <= b < N and 0 <= a < N and down[b][a] == j * N + i and (best is None or acc[b][a] > acc[best[0]][best[1]]): best = (b, a)
        if not best or acc[best[0]][best[1]] < 6: return path[::-1]
        j, i = best; path.append(best)
def downstream_path(j, i):
    path = []
    while 0 <= j < N and RD[j][i] > W_CH * 0.8:
        d = down[j][i]
        if d < 0: break
        j, i = d // N, d % N; path.append((j, i))
    return path
def catch_cells(j, i):
    out, st = [], [(j, i)]
    while st:
        b, a = st.pop(); out.append(b * N + a)
        for dj, di in N8:
            q, p = b + dj, a + di
            if 0 <= q < N and 0 <= p < N and down[q][p] == b * N + a: st.append((q, p))
    return out
cands = []
for j in range(N):
    for i in range(N):
        a = acc[j][i]; d = down[j][i]
        if a < 120 or d < 0 or RD[j][i] < W_CH * 1.3: continue
        nj, ni = d // N, d % N
        if slope[j][i] > 0.08 and (slope[nj][ni] <= 0.08 or RD[nj][ni] < W_CH * 2.5):
            path = upstream_path(j, i); hj, hi = path[0]; relief = E[hj][hi] - E[j][i]
            if relief >= 110: cands.append((a * relief, j, i, path, relief))
cands.sort(reverse=True)
gullies = []; used = []
chosen = []
for score, j, i, path, relief in cands:
    if any(abs(j - q) + abs(i - p) < 12 for q, p in used): continue
    ps = set(path); dup = None
    for gi, (pj, pi, pset, rel, ee, aa) in enumerate(chosen):
        if len(ps & pset) > 0.3 * min(len(ps), len(pset)): dup = gi; break
    if dup is not None:   # same drainage: keep the mouth higher up (where the gully leaves the mountain)
        if E[j][i] > chosen[dup][4] and acc[j][i] >= 0.35 * chosen[dup][5]:
            gullies[dup] = None; chosen[dup] = (j, i, ps, relief, E[j][i], acc[j][i])
        else: continue
    else: chosen.append((j, i, ps, relief, E[j][i], acc[j][i]))
    run = downstream_path(j, i)
    gullies.append({'outlet': [round(cx(i), 1), round(cx(j), 1)], 'area_km2': round(acc[j][i] * cell * cell / 1e6, 3), 'relief': round(relief), 'mouth_elev': round(E[j][i], 1),
                    'path': [[round(cx(p), 1), round(cx(q), 1)] for q, p in path], 'run': [[round(cx(p), 1), round(cx(q), 1)] for q, p in run], 'cells': catch_cells(j, i)})
    if dup is not None: gullies[dup] = gullies.pop()
    used.append((j, i))
    if len([q for q in gullies if q]) >= 7: break
gullies = [q for q in gullies if q]
# the channel that crosses 沈家庵 old village first
vil = (-45, -98)
gullies.sort(key=lambda gg: min(math.hypot(p[0] - vil[0], p[1] - vil[1]) for p in gg['run'] + gg['path']))
# --- roads (local metres, simplified), bridges
roads = []
for f in g['features']:
    p = f['properties']; hw = p.get('highway')
    if not hw or hw in ('construction',): continue
    kind = 'main' if hw in ('secondary', 'tertiary', 'unclassified') else 'lane' if hw in ('residential', 'service', 'living_street') else 'track' if hw == 'track' else 'path'
    for L in lines_of(f):
        pts = [loc(*q) for q in L]
        if not any(inside(q, 30) for q in pts): continue
        simp = pts   # keep every vertex: OSM junctions are shared vertices
        roads.append({'k': kind, 'b': 1 if p.get('bridge') else 0, 'n': p.get('name') or '', 'pts': [[round(a, 1), round(b, 1)] for a, b in simp]})
# --- houses (from the screenshots), shifted to the crop origin
H = json.load(open(D + 'shenjia_an_houses.json')); ox, oz = loc(H['origin']['lon'], H['origin']['lat'])
houses = []
for h in H['houses']:
    x, z = h['x'] + ox, h['z'] + oz
    if inside((x, z), -20): houses.append({'x': round(x, 1), 'z': round(z, 1), 'm2': h['m2'], 'ang': h['ang'], 'kind': h['kind'], 'zone': h['zone']})
places = []
for f in g['features']:
    p = f['properties']
    if f['geometry']['type'] == 'Point' and (p.get('place') or p.get('natural')):
        q = loc(*f['geometry']['coordinates'])
        if inside(q): places.append({'n': p.get('name'), 't': p.get('place') or p.get('natural'), 'x': round(q[0]), 'z': round(q[1])})
out = {'center': [C_LON, C_LAT], 'half_m': HALF, 'N': N, 'cell_m': cell, 'elev_min': round(min(min(r) for r in E), 2), 'elev_max': round(max(max(r) for r in E), 2),
       'elev': [round(E[j][i], 1) for j in range(N) for i in range(N)], 'acc': [int(acc[j][i]) for j in range(N) for i in range(N)], 'down': [down[j][i] for j in range(N) for i in range(N)],
       'river': [[round(a, 1), round(b, 1)] for a, b in river], 'river_surf': [round(v, 1) for v in surf], 'gullies': gullies, 'roads': roads, 'houses': houses, 'places': places}
json.dump(out, open(D + 'shenjia_data.json', 'w'))
print('elev', out['elev_min'], out['elev_max'], 'houses', len(houses), 'roads', len(roads), 'river pts', len(river))
for gg in gullies: print('gully outlet', gg['outlet'], 'area', gg['area_km2'], 'km2 relief', gg['relief'], 'mouth', gg['mouth_elev'], 'cells', len(gg['cells']))
print('places', places)
# --- compact embed for the single-file HTML
import base64, struct
gid = [0] * (N * N)
for k, gg in enumerate(gullies):
    for c in gg['cells']: gid[c] = k + 1
dcode = []
for j in range(N):
    for i in range(N):
        d = down[j][i]
        if d < 0: dcode.append(255); continue
        dj, di = d // N - j, d % N - i; dcode.append(N8.index((dj, di)))
b64 = lambda fmt, arr: base64.b64encode(struct.pack('<%d%s' % (len(arr), fmt), *arr)).decode()
emb = {'N': N, 'half': HALF, 'center': [C_LON, C_LAT],
       'elev': b64('H', [int(round(v * 10)) for row in E for v in row]),     # decimetres
       'acc': b64('H', [min(65535, int(acc[j][i])) for j in range(N) for i in range(N)]),
       'down': b64('B', dcode), 'gid': b64('B', gid),
       'river': [[round(a), round(b)] for a, b in river], 'riverSurf': [round(v, 1) for v in surf],
       'gullies': [{'outlet': gg['outlet'], 'area': gg['area_km2'], 'relief': gg['relief'], 'path': gg['path'][::2], 'run': gg['run'][::2]} for gg in gullies],
       'roads': [{'k': r['k'], 'b': r['b'], 'n': r['n'], 'p': [[round(a), round(b)] for a, b in r['pts']]} for r in roads],
       'houses': [[round(h['x']), round(h['z']), h['m2'], round(h['ang'], 2), {'flat': 0, 'red': 1, 'blue': 2, 'villaS': 3, 'villaD': 4}[h['kind']], {'沈家庵老村': 0, '渡外云居': 1, '一渡新新小镇': 2, '一渡青青小镇': 3}[h['zone']]] for h in houses],
       'places': places}
s = 'const GEO = ' + json.dumps(emb, ensure_ascii=False, separators=(',', ':')) + ';\n'
open(D + 'shenjia_embed.js', 'w').write(s); print('embed bytes', len(s.encode()))
