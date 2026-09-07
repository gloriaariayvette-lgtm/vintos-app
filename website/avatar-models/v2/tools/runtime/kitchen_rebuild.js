import * as T from 'three';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
// Architectural detail coordinates below are authored in centimeters and exported in meters.
const W=3.4,D=2.65,H=1.67;
export async function rebuildKitchen(){
 const g=new T.Group();g.name='kitchen';const L=new T.TextureLoader(),tx={};
 for(const n of ['wood','stone','towel','runner','wallpaper','ovens','range-front','dishwasher','outside','floor','wall-baked','wood-normal','stone-normal','towel-normal','runner-normal']){const t=await L.loadAsync('../../house/kitchen-materials/'+n+'.jpg');t.colorSpace=n.endsWith('normal')?T.NoColorSpace:T.SRGBColorSpace;t.userData.mimeType='image/jpeg';tx[n]=t;}
 tx.runner.wrapS=tx.runner.wrapT=T.RepeatWrapping;tx.runner.repeat.set(3,5);tx.wallpaper.wrapS=tx.wallpaper.wrapT=T.RepeatWrapping;tx.wallpaper.repeat.set(5,1);
 const material=(name,color,roughness=.6,metalness=0,map)=>new T.MeshStandardMaterial({name,color,roughness,metalness,map:map?tx[map]:null});
 const M={wood:material('Photo wood with grain relief',0xffffff,.43,0,'wood'),endgrain:material('Cabinet edge grain',0x956039,.48),recess:material('Dark cabinet rebates',0x39261a,.68),wall:material('Warm ivory painted wall',0xc9be9b,.94),trim:material('Aged white painted trim',0xe4ddca,.63),stone:material('Photo cream countertop',0xe5d9c3,.31,0,'stone'),black:material('Black appliance enamel',0x111617,.21,.25),glass:material('Dark reflective oven glass',0x131f22,.12,.3),steel:material('Brushed hood and sink steel',0x9aa2a0,.32,.88),brass:material('Patinated brass handles',0x635136,.43,.68),floor:material('Oak with baked cabinet contact shadows',0xffffff,.68,0,'floor'),towel:material('Photographed cotton towel',0xffffff,.95,0,'towel'),rug:material('Photographed woven runner',0xc9cebc,.99,0,'runner'),paper:material('Photographed botanical wallpaper',0xffffff,.96,0,'wallpaper'),shade:material('Sage sheer curtains',0x777d66,.97),nav:new T.MeshBasicMaterial({transparent:true,opacity:0,depthWrite:false}),portal:new T.MeshBasicMaterial({transparent:true,opacity:0,depthWrite:false})};
 for(const [m,n,k]of [['wood','wood',.24],['stone','stone',.10],['towel','towel',.26],['rug','runner',.22]]){M[m].normalMap=tx[n+'-normal'];M[m].normalScale.set(k,k);}
 const part=(name,geo,mat,p=[0,0,0],parent=g)=>{const m=new T.Mesh(geo,mat);m.name=name;m.position.set(...p);m.castShadow=m.receiveShadow=true;parent.add(m);return m;};
 const box=(name,p,size,mat=M.wood,parent=g,r=.002)=>part(name,r?new RoundedBoxGeometry(...size,2,r):new T.BoxGeometry(...size),mat,p,parent);
 const group=(name,p=[0,0,0],rot=0)=>{const a=new T.Group();a.name=name;a.position.set(...p);a.rotation.y=rot;g.add(a);return a;};
 const tube=(name,pts,r,mat,parent=g)=>part(name,new T.TubeGeometry(new T.CatmullRomCurve3(pts.map(p=>new T.Vector3(...p))),Math.min(60,pts.length*10),r,10,false),mat,[0,0,0],parent);
 const cylinder=(name,p,r,h,mat,parent=g)=>part(name,new T.CylinderGeometry(r,r,h,32),mat,p,parent);
 const plane=(name,p,w,h,mat,parent=g)=>part(name,new T.PlaneGeometry(w,h),mat,p,parent);
 const arch=(w,h,inset=0)=>{let l=-w/2+inset,r=w/2-inset,b=-h/2+inset,t=h/2-inset;const p=new T.Shape();p.moveTo(l,b);p.lineTo(r,b);p.lineTo(r,t-.035);p.bezierCurveTo(w*.25,t-.048,w*.17,t-.012,0,t);p.bezierCurveTo(-w*.17,t-.012,-w*.25,t-.048,l,t-.035);p.closePath();return p;};
 const panel=(name,shape,depth,p,parent,mat)=>{const a=new T.ExtrudeGeometry(shape,{depth,steps:1,curveSegments:18,bevelEnabled:true,bevelSize:.004,bevelThickness:.004,bevelSegments:3});const v=a.attributes.position,u=a.attributes.uv;for(let i=0;i<v.count;i++)u.setXY(i,v.getX(i)*2+.5,v.getY(i)*1.5+.5);a.computeVertexNormals();return part(name,a,mat,p,parent);};
 // Cabinet front local +Z faces the room. Frames, recessed arch, bevels and handles have depth.
 function door(parent,cx,cy,w,h,z,drawer=false){
  box('Solid cabinet door',[cx,cy,z],[w,h,.018],M.wood,parent);
  if(drawer){box('Drawer recessed center',[cx,cy,z+.011],[w-.046,h-.042,.006],M.recess,parent);box('Raised drawer panel',[cx,cy,z+.016],[w-.057,h-.053,.009],M.wood,parent,.004);}
  else{panel('Arched rebate',arch(w-.036,h-.042),.003,[cx,cy,z+.010],parent,M.recess);panel('Raised arched wood panel',arch(w-.055,h-.064),.006,[cx,cy-.002,z+.015],parent,M.wood);}
  const hx=drawer?cx:cx+w*.32,hy=drawer?cy:cy-h*.13;
  const pts=drawer?[[hx-.045,hy,z+.024],[hx-.032,hy,z+.044],[hx+.032,hy,z+.044],[hx+.045,hy,z+.024]]:[[hx,hy-.043,z+.024],[hx,hy-.029,z+.044],[hx,hy+.029,z+.044],[hx,hy+.043,z+.024]];
  tube('Cast brass pull',pts,.0045,M.brass,parent);
  for(const sign of [-1,1]){const knob=part('Handle mounting rosette',new T.SphereGeometry(.009,16,10),M.brass,[drawer?hx+sign*.045:hx,drawer?hy:hy+sign*.043,z+.023],parent);knob.scale.z=.3;}
  if(!drawer)for(const sign of [-1,1])box('Exposed cabinet hinge',[cx-w*.47,cy+sign*h*.30,z+.024],[.008,.028,.012],M.brass,parent);
 }
 function cabinet(name,x,z,w,h,y,rot=0,drawers=0,depth=.36){const c=group(name,[x,y,z],rot);
  box('Cabinet carcass',[0,name.startsWith('Sink run')?-0.07:0,-depth/2],[w,name.startsWith('Sink run')?0.40:h,depth],M.wood,c);box('Face frame shadow',[0,0,.002],[w-.011,h-.009,.005],M.recess,c);
  for(const sign of [-1,1])box('Vertical cabinet stile',[sign*(w/2-.012),0,.009],[.024,h,.024],M.wood,c);
  for(const sign of [-1,1])box('Horizontal cabinet rail',[0,sign*(h/2-0.012),0.009],[w,0.024,0.024],M.wood,c);if(name.startsWith('Sink run')||name.startsWith('Pass-through lower')){door(c,0,h/2-0.065,w-0.034,0.10,0.025,true);door(c,0,-0.065,w-0.029,h-0.15,0.025);}else if(drawers){const hh=(h-.018)/drawers;for(let k=0;k<drawers;k++)door(c,0,h/2-.009-hh*(k+.5),w-.034,hh-.010,.025,true);}
  else door(c,0,0,w-.029,h-.018,.025);
  return c;
 }
 function counter(name,x,z,w,d){box(name,[x,.609,z],[w,.027,d],M.stone,g,.005);}
 // The range wall reads LEFT-to-RIGHT in photo 1: ovens, drawers, range, corner, sink.
 // Camera looks toward +Z, so that order is decreasing local X. No negative scales.
 const front=2.205;
 const tower=group('Oven tower',[51/100,0,front],Math.PI);box('Oven tower carcass',[0,70/100,-21/100],[46/100,140/100,42/100],M.wood,tower);cabinet('Tower upper door',51/100,front,46/100,30/100,125/100,Math.PI,0,42/100);cabinet('Tower bottom drawer',51/100,front,46/100,12/100,8/100,Math.PI,1,42/100);
 const oven=group('Stacked ovens with photo fascias',[.51,0,front-.050],Math.PI);
 const ovenFace=material('Photographed oven controls and glass',0xffffff,.34,.12,'ovens');plane('Stacked oven fascia',[0,.70,.01],.405,.86,ovenFace,oven);
 for(const yy of [.49,.88])tube('Oven raised bar handle',[[-.17,yy,.021],[-.15,yy,.048],[.15,yy,.048],[.17,yy,.021]],.007,M.black,oven);
 cabinet('Four-drawer stack',.09,front,.32,.54,.31,Math.PI,4,.40);
 counter('Worktop above drawers',.09,2.43,.34,.44);
 for(const xx of [-.83,-1.26]){cabinet('Range wall base cabinet',xx,front,.42,.54,.31,Math.PI);}
 counter('Corner worktop',-1.08,2.43,1.24,.44);
 // Remaining details and architecture are appended below.
 return {g,M,tx,part,box,plane,tube,cylinder,group,cabinet,counter,W,D,H};
}
export async function buildDetailedKitchen(){
 const {g,M,tx,part,box,plane,tube,cylinder,group,cabinet,counter,W,D,H}=await rebuildKitchen();
 const material=(name,color,roughness=0.6,metalness=0,map)=>new T.MeshStandardMaterial({name,color,roughness,metalness,map:map?tx[map]:null});
 // Upper cabinets differ in height over the hood and beside the tower.
 cabinet('Tall upper beside ovens',0.09,2.40,0.32,0.50,1.13,Math.PI,0,0.23);
 for(const x of [-0.24,-0.49])cabinet('Short upper above hood',x,2.40,0.24,0.28,1.24,Math.PI,0,0.23);
 for(const x of [-0.82,-1.17,-1.48])cabinet('Tall corner upper',x,2.40,0.30,0.50,1.13,Math.PI,0,0.23);
 for(const z of [2.11,0.40])cabinet('Side upper cabinet',-1.40,z,0.40,0.50,1.13,Math.PI/2,0,0.23);
 // Side run: corner storage, sink cabinets, dishwasher and coffee counter.
 for(const z of [1.96,1.57,1.18])cabinet('Sink run lower cabinet',-1.26,z,0.38,0.54,0.31,Math.PI/2,0,0.40);
 cabinet('Coffee end base',-1.26,0.30,0.40,0.54,0.31,Math.PI/2,0,0.40);
 box('Dishwasher body',[-1.47,0.30,0.76],[0.40,0.54,0.43],M.black);
 const dw=plane('Photographed dishwasher fascia',[-1.252,0.30,0.76],0.42,0.52,material('Dishwasher fascia',0xffffff,0.30,0.1,'dishwasher'));dw.rotation.y=Math.PI/2;
 // Worktop cutout surrounds the sink; nothing covers the bowls.
 for(const [z,d]of [[0.60,1.0],[2.12,0.80]])counter('Side countertop',-1.48,z,0.44,d);
 for(const x of [-1.675,-1.285])counter('Sink counter margin',x,1.44,0.05,0.68);
 for(const z of [1.25,1.59]){
  box('Stainless bowl bottom',[-1.48,0.51,z],[0.29,0.015,0.29],M.steel,g,0.02);
  for(const x of [-1.635,-1.325])box('Bowl side',[x,0.56,z],[0.012,0.10,0.30],M.steel,g,0.005);
  for(const zz of [z-0.15,z+0.15])box('Bowl end',[-1.48,0.56,zz],[0.30,0.10,0.012],M.steel,g,0.005);
  cylinder('Drain',[-1.48,0.52,z],0.019,0.004,M.black);
 }
 box('Sink outer lip',[-1.315,0.624,1.42],[0.02,0.01,0.66],M.steel);box('Sink back lip',[-1.645,0.624,1.42],[0.02,0.01,0.66],M.steel);
 tube('Curved chrome tap',[[-1.63,0.62,1.43],[-1.63,0.78,1.43],[-1.55,0.81,1.43],[-1.48,0.77,1.43],[-1.48,0.74,1.43]],0.009,M.steel);
 for(const z of [1.30,1.56])tube('Separate tap control',[[-1.64,0.62,z],[-1.64,0.67,z],[-1.60,0.69,z]],0.009,M.steel);
 // Return worktop and three cupboards over the photographed serving opening.
 counter('Livingroom serving worktop',-1.02,0.23,1.30,0.44);
 for(const x of [-0.60,-0.99,-1.38]){cabinet('Pass-through lower drawer and cupboard',x,0.44,0.38,0.54,0.31,0,0,0.40);cabinet('Pass-through overhead cabinet',x,0.24,0.38,0.30,1.32,0,0,0.22);}
 return {g,M,tx,part,box,plane,tube,cylinder,group,cabinet,counter,W,D,H};
}
export async function completeKitchen(){
 const k=await buildDetailedKitchen();const {g,M,tx,part,box,plane,tube,cylinder,group,W,D,H}=k;
 const cm=x=>x/100,V=a=>a.map(cm);
 const B=(n,p,s,m=M.wood,par=g,r=1/500)=>box(n,V(p),V(s),m,par,r);
 const P=(n,p,w,h,m,par=g)=>plane(n,V(p),cm(w),cm(h),m,par);
 const U=(n,pts,r,m,par=g)=>tube(n,pts.map(V),cm(r),m,par);
 const G=(n,p,rot=0)=>group(n,V(p),rot);
 const C=(n,p,r,h,m,par=g)=>cylinder(n,V(p),cm(r),cm(h),m,par);
 // A freestanding cooker with an inset oven, control rail, rear guard and metal cooktop.
 const range=G('Range',[-34,0,218],Math.PI);
 B('Range enamel shell',[0,30,-20],[48,59,42],M.black,range,1/100);
 const rf=new T.MeshStandardMaterial({name:'Photographed range fascia',map:tx['range-front'],roughness:1/3,metalness:1/10});
 P('Range front with oven window',[0,29,2],43,46,rf,range);
 B('Range raised control strip',[0,55,2],[46,7,3],M.black,range);
 for(const x of [-17,-8,8,17]){const a=C('Fixed control dial',[x,55,4],2,1,M.black,range);a.rotation.x=Math.PI/2;U('Dial index',[[x,55,5],[x,56,5]],1/5,M.trim,range);}
 U('Oven handle',[[-19,46,3],[-17,46,6],[17,46,6],[19,46,3]],4/5,M.black,range);
 B('Hob surface',[0,61,-18],[48,2,41],M.black,range);
 B('Curved rear guard',[0,67,-38],[48,13,4],M.black,range,1/100);
 for(const x of [-12,12])for(const z of [-9,-29]){C('Fixed burner cap',[x,63,z],4,1,M.black,range);for(const sign of [-1,1])U('Cast grate prong',[[x+sign*7,63,z-6],[x+sign*7,65,z],[x+sign*3,65,z]],1/2,M.black,range);U('Grate crossbar',[[x-7,64,z-6],[x+7,64,z-6]],1/2,M.black,range);}
 // Sloped hood, not a rectangular placeholder: folded stainless cross-section.
 const hs=new T.Shape();hs.moveTo(-25,0);hs.lineTo(25,0);hs.lineTo(25,8);hs.lineTo(-25,8);hs.closePath();
 const hood=G('Folded stainless range hood',[-34,98,242],Math.PI);
 const hg=new T.BufferGeometry();const vv=[-26,0,0,26,0,0,26,0,28,-26,0,28,-24,9,0,24,9,0,24,9,7,-24,9,7].flatMap((v,i)=>[cm(v)]);hg.setAttribute('position',new T.Float32BufferAttribute(vv,3));hg.setIndex([0,1,2,0,2,3,4,7,6,4,6,5,0,4,5,0,5,1,1,5,6,1,6,2,2,6,7,2,7,3,3,7,4,3,4,0]);hg.computeVertexNormals();part('Sloping steel hood',hg,new T.MeshStandardMaterial({color:0x9aa2a0,roughness:0.45,metalness:0.8,flatShading:true}),[0,0,0],hood);
 B('Rolled hood lip',[0,0,29],[54,2,2],M.steel,hood);
 const glow=new T.MeshStandardMaterial({name:'Warm under-hood diffuser',color:0xffe8c0,emissive:0xffd59a,emissiveIntensity:2});B('EMO_kitchen_under_hood',[0,-1,16],[35,1,8],glow,hood);
 // A hanging towel is modeled as a folded surface; it is static until Phase 4.
 function towel(n,p,w,h,rot=0){const a=new T.PlaneGeometry(cm(w),cm(h),30,40),v=a.attributes.position;for(let i=0;i<v.count;i++)v.setZ(i,Math.sin(v.getX(i)*230)*cm(1/2));a.computeVertexNormals();const m=M.towel.clone();m.side=T.DoubleSide;const t=part(n,a,m,V(p));t.rotation.y=rot;}
 towel('Range handle towel',[-34,33,211],15,29);
 towel('Sink rail towel',[-119,40,177],13,28,Math.PI/2);
 // Counter-top small appliances are static visual shells only, not stateful objects.
 const air=G('Counter oven shell',[-143,62,78],Math.PI/2);
 B('Counter oven rounded enclosure',[0,15,0],[30,30,25],M.black,air,2/100);
 B('Counter oven steel surround',[0,12,14],[25,20,1],M.steel,air);
 B('Counter oven glass inset',[0,12,15],[21,16,1],M.glass,air);
 U('Counter oven handle',[[12,4,16],[12,21,16]],1,M.steel,air);
 const coffee=G('Coffee machine shell',[-151,62,36],Math.PI/2);
 B('Coffee base',[0,1,0],[16,2,19],M.black,coffee,1/100);B('Coffee rear upright',[0,13,-6],[14,26,6],M.black,coffee,1/100);
 C('Steel coffee head',[0,23,0],7,9,M.steel,coffee);B('Coffee drip tray',[0,3,3],[13,2,12],M.steel,coffee);
 C('Cup beneath coffee spout',[0,8,3],4,8,M.steel,coffee);U('Coffee handle',[[4,17,4],[11,17,4]],1,M.black,coffee);
 // Room shell retains the map's four neighbors. Unphotographed openings remain estimates.
 function wall(axis,coord,lo,hi,holes=[]){const cuts=[lo,hi,...holes.flatMap(h=>[h.c-h.w/2,h.c+h.w/2])].sort((a,b)=>a-b);
  for(let i=0;i<cuts.length-1;i++){let a=cuts[i],b=cuts[i+1];if(b<=a)continue;const m=(a+b)/2,h=holes.find(h=>m>h.c-h.w/2&&m<h.c+h.w/2);for(const [y0,y1]of h?[[0,h.b||0],[h.t,167]]:[[0,167]])if(y1>y0)B('Wall',axis==='z'?[m,(y0+y1)/2,coord]:[coord,(y0+y1)/2,m],axis==='z'?[b-a,y1-y0,7]:[7,y1-y0,b-a],M.wall,g,0);}}
 wall('z',0,-170,170,[{c:0,w:68,t:136},{c:-100,w:120,b:63,t:116}]);
 wall('z',265,-170,170,[{c:128,w:62,t:136}]);
 wall('x',170,0,265,[{c:55,w:62,t:136},{c:157,w:62,t:136}]);
 wall('x',-170,0,265,[{c:139,w:115,b:82,t:153}]);
 const wallBake=new T.MeshStandardMaterial({name:'Baked under-hood wall lighting',map:tx['wall-baked'],roughness:1});const wallPatch=P('Baked range-wall lighting',[-44,83.5,261],252,167,wallBake);wallPatch.rotation.y=Math.PI;for(let i=0;i<wallPatch.geometry.attributes.position.count;i++){const px=wallPatch.geometry.attributes.position.getX(i);wallPatch.geometry.attributes.uv.setX(i,(-0.44-px+1.7)/3.4);}
 const floor=P('Oak floor with baked lighting',[0,0,132.5],340,265,M.floor);floor.rotation.x=-Math.PI/2;
 const ceiling=P('Ceiling',[0,167,132.5],340,265,M.trim);ceiling.rotation.x=Math.PI/2;
 B('Range wall wallpaper band',[-44,150,261],[242,20,1],M.paper);
 B('Ceiling olive border',[-44,163,260],[242,7,2],M.shade);
 B('Range wall baseboard',[-42,3,260],[245,6,2],M.trim);
 B('Side cabinet recessed plinth',[-162,3,140],[10,6,240],M.recess);
 const light=new T.MeshStandardMaterial({color:0xf4f4df,emissive:0xffffed,emissiveIntensity:2});B('Ceiling fluorescent panel',[-49,165,142],[104,1,29],light);
 const win=G('Window above sink',[-166,117.5,139],Math.PI/2);
 const exterior=new T.MeshStandardMaterial({map:tx.outside,emissiveMap:tx.outside,emissive:0xffffff,emissiveIntensity:1/2,roughness:1});P('Exterior through glazing',[0,0,-3],115,71,exterior,win);
 for(const x of [-58,58])B('Window side casing',[x,0,0],[4,78,5],M.trim,win);
 for(const y of [-37,0,37])B('Window sash rail',[0,y,1],[121,3,6],M.trim,win);
 B('Window central mullion',[0,0,2],[2,71,4],M.trim,win);B('Deep window sill',[0,-40,3],[125,4,11],M.trim,win);
 for(let y=-32;y<=32;y+=4)B('Horizontal blind slat',[0,y,-1],[112,1/3,2],M.trim,win,0);
 for(const xx of [-42,42]){const a=new T.PlaneGeometry(cm(32),cm(78),36,30),p=a.attributes.position;for(let i=0;i<p.count;i++){let u=p.getX(i)/cm(32);p.setZ(i,cm(1.2)*Math.sin(u*50));}a.computeVertexNormals();const m=M.shade.clone();m.side=T.DoubleSide;m.transparent=true;m.opacity=4/5;part('Sheer sage window curtain',a,m,V([xx,0,6]),win);}
 // Runner pieces follow the L-shaped counter, as photographed.
 for(const [p,w,h]of [[[ -83,1/5,174],35,86],[[ -39,1/5,191],77,29]]){const a=P('Woven kitchen runner',p,w,h,M.rug);a.rotation.x=-Math.PI/2;}
 const portals=[];
 function portal(next,x,z,nx,nz,w=62,type='doorway'){const name='PORTAL_kitchen_'+next,sz=nx?[16,136,w]:[w,136,16];const a=B(name,[x,68,z],sz,M.portal);a.castShadow=a.receiveShadow=false;
  const p={name,targetRoom:next,partner:'PORTAL_'+next+'_kitchen',position:V([x,68,z]),floorCenter:V([x,0,z]),inwardNormal:[nx,0,nz],size:V(sz),width:cm(w),height:cm(136),type,partnerStatus:next==='livingroom'?'built':'pending-review',spawn:V([x+nx*22,0,z+nz*22]),placement:'Main shared origin fixed; other doorway coordinates are estimates, adjacency from house map'};a.userData={...p,render:false,triggerOnly:true};portals.push(p);
  for(const s of [-1,1])B('Doorway casing',nx?[x,68,z+s*(w/2+2)]:[x+s*(w/2+2),68,z],nx?[10,136,4]:[4,136,10],M.trim);
  B('Doorway lintel',[x,139,z],nx?[10,6,w+8]:[w+8,6,10],M.trim);
 }
 portal('livingroom',0,0,0,1,68);portal('office',128,265,0,-1);portal('laundry',170,55,-1,0,62,'curtains');portal('hall',170,157,-1,0);
 const rects=[[-170,10,-122,265],[-170,213,76,265],[-170,0,-37,48]].map(V);
 const xs=[-W/2,W/2,...rects.flatMap(r=>[r[0],r[2]])].sort((a,b)=>a-b),zs=[0,D,...rects.flatMap(r=>[r[1],r[3]])].sort((a,b)=>a-b),verts=[];
 for(let i=0;i<xs.length-1;i++)for(let j=0;j<zs.length-1;j++){const a=xs[i],b=xs[i+1],c=zs[j],d=zs[j+1],x=(a+b)/2,z=(c+d)/2;if(b<=a||d<=c||rects.some(r=>x>r[0]&&x<r[2]&&z>r[1]&&z<r[3]))continue;verts.push(a,0,c,a,0,d,b,0,d,a,0,c,b,0,d,b,0,c);}
 const navgeo=new T.BufferGeometry();navgeo.setAttribute('position',new T.Float32BufferAttribute(verts,3));navgeo.computeVertexNormals();const nav=part('NAV_kitchen',navgeo,M.nav);nav.userData={render:false,walkable:true,obstacleFootprints:rects};nav.castShadow=nav.receiveShadow=false;
 const manifest={id:'kitchen',file:'kitchen.glb',status:'rebuilt-awaiting-review',photographed:true,dimensionsEstimated:true,dimensionsMeters:{width:W,depth:D,height:H},mainDoorway:'livingroom',origin:'floor center of livingroom doorway; +Z inward',windows:['left'],portals,emo:['EMO_kitchen_under_hood'],nav:'NAV_kitchen',obstacleFootprints:rects,handedness:{photo1LeftToRight:['stacked ovens','drawer stack','range and hood','corner','sink'],localXDescending:[0.51,0.09,-0.34,-1.08,-1.48],windowWall:'-X',passThroughWall:'Z=0',negativeScale:false},limitations:['No metric survey; exact other door coordinates estimated','Livingroom partner remains rejected','Static appliance shells; no Phase 4 interactions','Photo textures retain some source lighting']};
 g.userData={meters:true,avatarHeight:1.166,handedness:manifest.handedness};
 return {room:g,manifest};
}
