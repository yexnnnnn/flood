import json, math, zlib, struct, heapq
rows=[l.split() for l in open('output_hh.asc').read().splitlines()[6:]]
Z=[[float(v) for v in r] for r in rows]; nr=len(Z); nc=len(Z[0])
x0,y0,cs=115.654861100000,39.577916677778,0.000277777778; lat0=y0+nr*cs
mx=111320*math.cos(math.radians(39.6))*cs; my=110540*cs
ij=lambda lon,lat:((lon-x0)/cs,(lat0-lat)/cs)
# --- priority-flood fill, D8 flow accumulation
F=[r[:] for r in Z]; seen=[[False]*nc for _ in range(nr)]; pq=[]
for j in range(nr):
    for i in range(nc):
        if i in(0,nc-1) or j in(0,nr-1): heapq.heappush(pq,(F[j][i],j,i)); seen[j][i]=True
N8=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
order=[]
while pq:
    h,j,i=heapq.heappop(pq); order.append((j,i))
    for dj,di in N8:
        b,a=j+dj,i+di
        if 0<=b<nr and 0<=a<nc and not seen[b][a]:
            seen[b][a]=True; F[b][a]=max(F[b][a],h+1e-3); heapq.heappush(pq,(F[b][a],b,a))
acc=[[1.0]*nc for _ in range(nr)]; down={}
for j in range(nr):
    for i in range(nc):
        best=0;bd=None
        for dj,di in N8:
            b,a=j+dj,i+di
            if 0<=b<nr and 0<=a<nc:
                d=(F[j][i]-F[b][a])/math.hypot(dj*my,di*mx)
                if d>best: best=d;bd=(b,a)
        down[(j,i)]=bd
for j,i in sorted(order,key=lambda t:-F[t[0]][t[1]]):
    d=down[(j,i)]
    if d: acc[d[0]][d[1]]+=acc[j][i]
# --- hillshade
def hs(j,i):
    jm,jp=max(0,j-1),min(nr-1,j+1); im,ip=max(0,i-1),min(nc-1,i+1)
    dzdx=(Z[j][ip]-Z[j][im])/((ip-im)*mx); dzdy=(Z[jp][i]-Z[jm][i])/((jp-jm)*my)
    sl=math.atan(math.hypot(dzdx,dzdy)); asp=math.atan2(dzdy,-dzdx)
    az=math.radians(315); al=math.radians(40)
    return max(0,math.cos(al)*math.cos(sl)+math.sin(al)*math.sin(sl)*math.cos(az-asp))
S=6; W=nc*S; H=nr*S
img=[[(0,0,0)]*W for _ in range(H)]
zmin,zmax=99.5,702
for j in range(nr):
    for i in range(nc):
        h=hs(j,i); t=(Z[j][i]-zmin)/(zmax-zmin); base=(0.55+0.3*t,0.62+0.12*t,0.5+0.1*t)
        a=acc[j][i]; wet=min(1,math.log(a)/math.log(400)) if a>12 else 0
        c=[int(255*min(1,v*(0.45+0.7*h))) for v in base]
        if wet>0.3: c=[int(c[0]*(1-wet*0.7)+40*wet*0.7),int(c[1]*(1-wet*0.7)+110*wet*0.7),int(c[2]*(1-wet*0.7)+190*wet*0.7)]
        for dj in range(S):
            for di in range(S): img[j*S+dj][i*S+di]=tuple(c)
def px(x,y,c):
    if 0<=x<W and 0<=y<H: img[y][x]=c
def line(a,b,c):
    (xa,ya),(xb,yb)=a,b; n=int(max(abs(xb-xa),abs(yb-ya)))+1
    for k in range(n+1): px(int(xa+(xb-xa)*k/n),int(ya+(yb-ya)*k/n),c)
g=json.load(open('shenjia_an_4km_osm.geojson'))
def P(lon,lat): i,j=ij(lon,lat); return (i*S,j*S)
for f in g['features']:
    p=f['properties']; gt=f['geometry']['type']; co=f['geometry']['coordinates']
    lines=[co] if gt=='LineString' else co if gt=='MultiLineString' else []
    if p.get('highway'):
        col={'secondary':(250,250,250),'tertiary':(250,250,250),'residential':(255,235,190),'track':(200,170,120),'service':(235,220,190)}.get(p['highway'],(215,95,60) if p['highway'] in('path','steps','footway') else (200,200,200))
        for L in lines:
            for k in range(len(L)-1): line(P(*L[k]),P(*L[k+1]),col)
    elif p.get('waterway'):
        col=(20,60,200) if p['waterway'] in('river','stream') else (90,150,230)
        for L in lines:
            for k in range(len(L)-1): line(P(*L[k]),P(*L[k+1]),col)
    elif p.get('building') and gt=='Polygon':
        ring=co[0]; xs=[P(*q)[0] for q in ring]; ys=[P(*q)[1] for q in ring]
        for y in range(int(min(ys)),int(max(ys))+1):
            for x in range(int(min(xs)),int(max(xs))+1): px(x,y,(210,30,30))
    elif p.get('natural')=='water' and gt in('Polygon','MultiPolygon'):
        ring=co[0] if gt=='Polygon' else co[0][0]
        for k in range(len(ring)-1): line(P(*ring[k]),P(*ring[k+1]),(0,40,160))
    elif gt=='Point':
        x,y=P(*co)
        for dx in range(-5,6):
            for dy in range(-5,6): px(int(x)+dx,int(y)+dy,(255,200,0) if p.get('place') else (160,0,160))
def png(path,img):
    raw=b''.join(b'\x00'+bytes([v for c in row for v in c]) for row in img)
    def ch(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw,6))+ch(b'IEND',b''))
png('_analysis/map.png',img)
# --- catchments that drain to the village (沈家庵村 node at ij 83,64) and nearby
vi,vj=[round(v) for v in ij(115.6779697,39.5958882)]
print('village ij',vi,vj,'elev',Z[vj][vi])
best=None
for dj in range(-6,7):
    for di in range(-6,7):
        b,a=vj+dj,vi+di
        if 0<=b<nr and 0<=a<nc and (best is None or acc[b][a]>acc[best[0]][best[1]]): best=(b,a)
print('highest accumulation within 6 cells of village: ij',best[1],best[0],'upstream area km2 %.3f'%(acc[best[0]][best[1]]*mx*my/1e6),'elev',Z[best[0]][best[1]])
# list the main gullies: cells with acc>150 on slopes, outlet points on the valley floor (elev<135)
outs=[]
for j in range(nr):
    for i in range(nc):
        if acc[j][i]>60 and Z[j][i]<175:
            d=down[(j,i)]
            if d and acc[d[0]][d[1]]>acc[j][i]*3 and acc[j][i]>60: outs.append((acc[j][i],i,j))
outs.sort(reverse=True)
print('gully mouths (catchment km2, ij, elev, nearest-slope m/m):')
for a,i,j in outs[:14]:
    # max elevation upstream (rough): walk up along the biggest-acc neighbour
    ci,cj=i,j; zt=Z[j][i]
    for _ in range(400):
        nb=[(acc[cj+dj][ci+di],ci+di,cj+dj) for dj,di in N8 if 0<=cj+dj<nr and 0<=ci+di<nc and down.get((cj+dj,ci+di))==(cj,ci)]
        if not nb: break
        _,ci,cj=max(nb); zt=max(zt,Z[cj][ci])
    print('  %.2f km2 ij(%d,%d) mouth elev %d  head elev %d  relief %d m'%(a*mx*my/1e6,i,j,Z[j][i],zt,zt-Z[j][i]))
