process.env.LIB=1; const G=require('./gen.js');
for (const id of 'ABC') { G.setZS(G.DESIGNS[id].zs||9); const ZS=G.DESIGNS[id].zs||9; const P=G.parts(G.DESIGNS[id]); let bl=0,cl=0; const h=.2;
  for(let x=-50;x<50;x+=h)for(let y=-36;y<36;y+=h)for(let z=ZS-.5;z<ZS+3;z+=h) if(P.base(x,y,z)<-.02&&P.lid(x,y,z)<-.02) bl++;
  for(let x=G.AX-15;x<G.AX+15;x+=h)for(let y=-15;y<15;y+=h)for(let z=16.5;z<30;z+=h) if(P.cap(x,y,z)<-.02&&P.lid(x,y,z)<-.02) cl++;
  console.log(id,'base∩lid',bl,'cap∩lid',cl); }
