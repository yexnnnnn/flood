process.env.LIB=1; const G=require('./gen.js'); G.setZS(7);
const res=[]; const D=G.DESIGNS.A;
for (const b of [31,33]) for (const zb of [-4.2,-5,-5.8]) for (const tBot of [12,13.5,15]) for (const qBot of [1.9,2.2,2.5]) for (const zc of [6,7]) {
  G.setPB({b,zb,tBot,qBot,zc}); const P=G.parts(D), w=G.wallReport(D,P); delete w.at;
  const m=Math.min(w.side,w.end,w.bot,w.top-.3);
  const bot=(x,y)=>{let z=zb-1; while(D.outer(x,y,z)>0&&z<10) z+=.05; return z;}; const z0=bot(0,0);
  let fw=0,fl=0; for(let y=-30;y<=30;y+=.5) if(bot(0,y)<z0+.3) fw+=.5; for(let x=-45;x<=45;x+=.5) if(bot(x,0)<z0+.3) fl+=.5;
  let top=40; while(D.outer(0,0,top)>0) top-=.1; let ymax=0; for(let y=0;y<45;y+=.2){let ok=false; for(let z=zb;z<top;z+=.5) if(D.outer(0,y,z)<0) ok=true; if(ok) ymax=y;}
  res.push([+m.toFixed(2), fw, fl, +(top-z0).toFixed(1), JSON.stringify({b,zb,tBot,qBot,zc})]);
}
res.filter(r=>r[0]>=2.1).sort((p,q)=>p[1]-q[1]||p[3]-q[3]).slice(0,10).forEach(r=>console.log(r.join(' ')));
