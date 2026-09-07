async function optimizeRoom(room){await MikkTSpace.ready;const cache=new Map();
 room.traverse(o=>{if(!o.isMesh)return;let geo=o.geometry;if(!o.material.map&&!o.material.normalMap)geo.deleteAttribute('uv');if(o.material.normalMap)geo=computeMikkTSpaceTangents(geo,MikkTSpace);geo=mergeVertices(geo,1e-6);const arrays=[...Object.entries(geo.attributes).sort().map(([k,a])=>a.array),...(geo.index?[geo.index.array]:[])];let hash=2166136261;for(const a of arrays)for(const b of new Uint8Array(a.buffer,a.byteOffset,a.byteLength))hash=Math.imul(hash^b,16777619);const key=hash+':'+arrays.map(a=>a.length).join(',');const prior=cache.get(key);if(prior&&arrays.every((a,i)=>a.every((v,k)=>v===prior.arrays[i][k])))o.geometry=prior.geo;else{cache.set(key,{geo,arrays});o.geometry=geo;}});
}
import {replaceLivingFurniture} from './livingroom_rebuild.js';
import {computeMikkTSpaceTangents, mergeVertices} from 'three/addons/utils/BufferGeometryUtils.js';
import * as MikkTSpace from 'three/addons/libs/mikktspace.module.js';
import {completeKitchen} from './kitchen_rebuild.js';
import * as T from 'three';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const root='../../',texRoot=root+'house/materials/';
const loader=new T.TextureLoader(),textures={};
for(const name of ['inlay','counter','cabinet-wood','sage-fabric','foliage','rug','oak','brocade','brown-throw','wallpaper','livingroom-floor-baked','kitchen-floor-baked']){
 const t=await loader.loadAsync(texRoot+name+'.jpg');t.colorSpace=T.SRGBColorSpace;t.wrapS=t.wrapT=T.RepeatWrapping;t.userData.mimeType="image/jpeg";textures[name]=t;
}
const footprints=await (await fetch(texRoot+'footprints.json')).json();
function mat(name,color,roughness=.7,metalness=0,map){const m=new T.MeshStandardMaterial({name,color,roughness,metalness,map:map?textures[map]:null});return m;}
const M={wall:mat('Warm painted wall',0xc9c4ad),trim:mat('Ivory painted molding',0xe4deca,.5),gold:mat('Aged carved gilt',0xad833b,.48,.55),darkgold:mat('Carving recesses',0x64512e,.6,.5),cream:mat('Ivory brocade',0xffffff,.92,0,'brocade'),sage:mat('Sage woven drapery',0xffffff,.95,0,'sage-fabric'),brown:mat('Brown textured throw',0xffffff,.98,0,'brown-throw'),rug:mat('Faded botanical rug',0xffffff,1,0,'rug'),wood:mat('Warm cabinet wood',0x9d6538,.48,0,'cabinet-wood'),inlay:mat('Cream shell inlay',0xfff0d3,.26,0,'inlay'),counter:mat('Cream stone laminate',0xffffff,.3,0,'counter'),black:mat('Black enamel appliances',0x11191c,.23,.22),steel:mat('Brushed stainless steel',0xaab4b4,.29,.85),wallpaper:mat('Sage botanical wallpaper',0xffffff,.95,0,'wallpaper'),leaf:mat('Window exterior foliage',0xffffff,1,0,'foliage'),nav:new T.MeshBasicMaterial({name:'Invisible navigation',transparent:true,opacity:0,depthWrite:false}),portal:new T.MeshBasicMaterial({name:'Invisible portal',transparent:true,opacity:0,depthWrite:false})};
M.leaf.emissive=new T.Color(0x859474);M.leaf.emissiveMap=textures.foliage;M.leaf.emissiveIntensity=.36;
let room,roomId,manifest,obstacles=[];
function mesh(name,g,m,p=[0,0,0],rot=[0,0,0],parent=room){const o=new T.Mesh(g,m);o.name=name;o.position.set(...p);o.rotation.set(...rot);o.castShadow=true;o.receiveShadow=true;parent.add(o);return o;}
function box(name,p,s,m=M.trim,r=0,parent=room){return mesh(name,r?new RoundedBoxGeometry(...s,3,r):new T.BoxGeometry(...s),m,p,[0,0,0],parent);}
function ball(name,p,s,m,parent=room){const o=mesh(name,new T.SphereGeometry(1,18,12),m,p,[0,0,0],parent);o.scale.set(...s);return o;}
function cyl(name,p,r,h,m,parent=room){return mesh(name,new T.CylinderGeometry(r,r,h,48),m,p,[0,0,0],parent);}
function tube(name,points,r,m=M.gold,parent=room){return mesh(name,new T.TubeGeometry(new T.CatmullRomCurve3(points.map(v=>new T.Vector3(...v))),Math.min(96,Math.max(12,points.length*8)),r,7,false),m,[0,0,0],[0,0,0],parent);}
function group(name,p=[0,0,0],rot=0){const g=new T.Group();g.name=name;g.position.set(...p);g.rotation.y=rot;room.add(g);return g;}
function leg(p,h,parent,m=M.trim){const prof=[[.034,0],[.047,.04],[.032,.09],[.052,.18],[.063,.27],[.039,.36],[.048,.46],[.039,.62],[.058,.76],[.043,.89],[.055,1]].map(([r,y])=>new T.Vector2(r,y*h));return mesh('Turned furniture leg',new T.LatheGeometry(prof,32),m,p,[0,0,0],parent);}
function scroll(cx,cy,z,s,parent){const pts=[];for(let i=0;i<=28;i++){let a=i/28*Math.PI*3.2;let r=s*(1-i/34);pts.push([cx+Math.cos(a)*r,cy+Math.sin(a)*r,z]);}tube('Gilt scroll',pts,.007,M.gold,parent);}
function leaf(p,angle,s,parent){const o=ball('Carved acanthus leaf',p,[s*.4,s,.008],M.gold,parent);o.rotation.z=angle;}
function ornateSeat(name,x,z,w,rot=0){const g=group(name,[x,0,z],rot),back=.28;
 box('Upholstered seat',[0,.295,0],[w,.13,.47],M.cream,.055,g);
 box('Carved seat apron',[0,.227,-.02],[w+.07,.065,.49],M.darkgold,.02,g);
 tube('Seat front gilt rail',[[-w/2,.26,-.265],[0,.245,-.285],[w/2,.26,-.265]],.022,M.gold,g);
 box('Brocade back cushion',[0,.63,back],[w-.1,.50,.085],M.cream,.075,g);
 const profile=[[-w/2,.33,back],[-w/2-.04,.61,back],[-w/2+.01,.84,back],[-w*.30,.89,back],[0,.95,back],[w*.30,.89,back],[w/2-.01,.84,back],[w/2+.04,.61,back],[w/2,.33,back]];
 tube('Carved back frame',profile,.027,M.darkgold,g);tube('Gilded frame ridge',profile.map(([a,b,c])=>[a,b,c-.019]),.014,M.gold,g);
 for(const sign of [-1,1]){
  tube('Curved carved arm',[[sign*w/2,.30,-.19],[sign*(w/2+.06),.51,-.19],[sign*(w/2+.025),.57,.04],[sign*w/2,.69,.25]],.023,M.gold,g);
  for(const zz of [-.19,.20]){tube('Cabriole leg',[[sign*(w/2-.03),.23,zz],[sign*(w/2+.025),.13,zz-.02],[sign*(w/2-.00),.035,zz-.04]],.023,M.gold,g);}
  scroll(sign*w*.42,.81,.245,.067,g);
 }
 for(let i=0;i<13;i++){const px=(i/12-.5)*w*.88;leaf([px,.9+.046*Math.cos(px/w*Math.PI*2),.267],px*2,.027,g);}
 scroll(0,.959,.28,.072,g);for(let i=0;i<28;i++){const px=(i/27-.5)*w*.94,py=.885+.042*Math.cos(px/w*Math.PI*2);leaf([px,py,.242],Math.sin(i*1.7)*.7,.037,g);scroll(px,py,.24,.019,g);}for(const sign of [-1,1])for(let i=0;i<9;i++){const y=.37+i*.046;leaf([sign*(w/2+.024),y,.25],sign*.5,.027,g);}
 if(w>1){box('Brown draped seat throw',[0,.375,-.04],[w-.10,.085,.49],M.brown,.035,g);for(let i=0;i<6;i++){const px=(i/5-.5)*(w-.16);box('Throw fold',[px,.318,-.275],[.085,.19,.035],M.brown,.025,g);} }
 for(const [px,col] of w>1?[[-w*.33,M.brown],[w*.30,M.sage]]:[[0,M.sage]]){const c=box('Loose woven cushion',[px,.54,.10],[w>1?.34:.32,.32,.10],col,.045,g);c.rotation.z=px<0?.22:-.14;c.rotation.x=-.18;}
 return g;
}
function table(name,x,z,w,d,h,round=false){const g=group(name,[x,0,z]);
 if(round){const o=cyl('Inlaid round tabletop',[0,h,0],w/2,.035,M.inlay,g);const ring=mesh('Pearl tabletop rim',new T.TorusGeometry(w/2-.008,.012,10,80),M.trim,[0,h+.008,0],[-Math.PI/2,0,0],g);}
 else{box('Inlaid dining tabletop',[0,h,0],[w,.035,d],M.inlay,.015,g);box('Painted table apron',[0,h-.06,0],[w-.08,.10,d-.08],M.trim,.008,g);}
 for(const xx of [-1,1])for(const zz of [-1,1])leg([xx*w*.34,0,zz*d*.34],h-.02,g);
 return g;
}
function drape(name,x,y,z,w,h,rot=0){const g=group(name,[x,y,z],rot);const geo=new T.PlaneGeometry(w,h,64,28),p=geo.attributes.position;
 for(let i=0;i<p.count;i++){const u=(p.getX(i)/w+.5),v=(p.getY(i)/h+.5);const pinch=1-.40*Math.exp(-1*((v-.28)/.18)**2);p.setX(i,(u-.5)*w*pinch);p.setZ(i,.018*Math.sin(u*Math.PI*14)*(1+.5*v));}geo.computeVertexNormals();const m=M.sage.clone();m.side=T.DoubleSide;mesh('Pleated fabric',geo,m,[0,0,0],[0,0,0],g);tube('Brass curtain tie',[[-w*.29,-h*.22,.04],[0,-h*.24,.05],[w*.29,-h*.22,.04]],.006,M.gold,g);
}
function windowUnit(name,x,z,w,h,y,rot=0){const g=group(name,[x,y,z],rot);g.userData={window:true};box('Window exterior',[0,0,.015],[w,h,.009],M.leaf,0,g);
 for(const xx of [-w/2,w/2])box('Window jamb',[xx,0,-.013],[.035,h+.08,.06],M.trim,0,g);
 for(const yy of [-h/2,h/2,0])box('Sash rail',[0,yy,-.025],[w+.08,.028,.06],M.trim,0,g);
 box('Central mullion',[0,0,-.028],[.019,h,.035],M.trim,0,g);box('Deep window sill',[0,-h/2-.025,-.044],[w+.13,.035,.12],M.trim,0,g);
 const side=w*.53;for(const sign of [-1,1]){const p=new T.Vector3(sign*side,-.12,-.08).applyAxisAngle(new T.Vector3(0,1,0),rot);drape('Sage curtains',x+p.x,y+p.y,z+p.z,w*.27,h+.35,rot);}
}
function wallSegment(name,axis,coord,a,b,H){if(b-a<.001)return;const along=axis==='z';box(name,along?[(a+b)/2,H/2,coord]:[coord,H/2,(a+b)/2],along?[b-a,H,.075]:[.075,H,b-a],M.wall);}
function wallWithHoles(axis,coord,lo,hi,H,holes){
 const cuts=[lo,hi,...holes.flatMap(h=>[h.c-h.w/2,h.c+h.w/2])].sort((a,b)=>a-b);
 for(let i=0;i<cuts.length-1;i++){const a=Math.max(lo,cuts[i]),b=Math.min(hi,cuts[i+1]);if(b<=a)continue;const mid=(a+b)/2,h=holes.find(h=>mid>h.c-h.w/2&&mid<h.c+h.w/2);if(!h)wallSegment('Wall',axis,coord,a,b,H);else{
 const along=axis==='z';for(const [y0,y1] of [[0,h.bottom||0],[h.top,H]])if(y1-y0>.001)box('Wall above or below opening',along?[mid,(y0+y1)/2,coord]:[coord,(y0+y1)/2,mid],along?[b-a,y1-y0,.075]:[.075,y1-y0,b-a],M.wall);
 }}
}
function portal(next,p,normal,width=.62,type='doorway'){
 const name=`PORTAL_${roomId}_${next}`,g=box(name,[p[0],.68,p[1]],Math.abs(normal[0])>.5?[.16,1.36,width]:[width,1.36,.16],M.portal);g.castShadow=g.receiveShadow=false;
 const info={name,targetRoom:next,partner:`PORTAL_${next}_${roomId}`,position:[p[0],.68,p[1]],floorCenter:[p[0],0,p[1]],inwardNormal:[normal[0],0,normal[1]],size:g.geometry.parameters.width?[g.geometry.parameters.width,g.geometry.parameters.height,g.geometry.parameters.depth]:null,width,height:1.36,type,partnerStatus:['livingroom','kitchen'].includes(next)?'built':'pending-review',spawn:[p[0]+normal[0]*.22,0,p[1]+normal[1]*.22]};g.userData={...info,render:false,triggerOnly:true};manifest.portals.push(info);
 // Frame geometry only, no swinging leaf in Phase 3.
 const along=Math.abs(normal[0])<.5;for(const sign of [-1,1])box('Doorway frame',along?[p[0]+sign*(width/2+.017),.68,p[1]]:[p[0],.68,p[1]+sign*(width/2+.017)],along?[.034,1.36,.095]:[.095,1.36,.034],M.trim);
 box('Doorway lintel',[p[0],1.385,p[1]],along?[width+.09,.05,.095]:[.095,.05,width+.09],M.trim);
}
function nav(W,D){
 // Exact rectilinear polygon subtraction by constrained cell decomposition.
 // Shared coordinates make adjacent cells meet without cracks; occupied cells omitted.
 const rects=footprints[roomId],xs=[-W/2,W/2,...rects.flatMap(r=>[r[0],r[2]])].filter(x=>x>=-W/2&&x<=W/2).sort((a,b)=>a-b),zs=[0,D,...rects.flatMap(r=>[r[1],r[3]])].filter(z=>z>=0&&z<=D).sort((a,b)=>a-b);const verts=[];
 for(let i=0;i<xs.length-1;i++)for(let j=0;j<zs.length-1;j++){const a=xs[i],b=xs[i+1],c=zs[j],d=zs[j+1],x=(a+b)/2,z=(c+d)/2;if(b-a<1e-6||d-c<1e-6||rects.some(r=>x>r[0]&&x<r[2]&&z>r[1]&&z<r[3]))continue;verts.push(a,0,c,a,0,d,b,0,d,a,0,c,b,0,d,b,0,c);}
 const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(verts,3));geo.computeVertexNormals();const o=mesh('NAV_'+roomId,geo,M.nav);o.castShadow=o.receiveShadow=false;o.userData={render:false,walkable:true,obstacleFootprints:rects,clearance:'Footprints include furniture edges. Client must erode by avatar radius.'};manifest.nav=o.name;manifest.obstacleFootprints=rects;
}
function ceiling(W,D,H=1.67){const o=mesh('Ceiling',new T.PlaneGeometry(W,D),M.trim,[0,H,D/2],[Math.PI/2,0,0]);o.castShadow=false;}
function floor(W,D){const m=mat(roomId+' baked floor',0xffffff,.75,0,roomId+'-floor-baked');mesh('Oak floor with baked contact lighting',new T.PlaneGeometry(W,D),m,[0,0,D/2],[-Math.PI/2,0,0]);}
function emo(name,p,s){const m=mat(name,0xffecd1,.65);m.emissive=new T.Color(0xffd7a3);m.emissiveIntensity=.45;box(name,p,s,m);manifest.emo.push(name);}
function paneling(W,D,H){for(let x=-W/2+.10;x<W/2;x+=.16)box('Beadboard seam',[x,.30,D-.043],[.005,.60,.004],M.trim);for(let z=.12;z<D;z+=.16)box('Beadboard seam',[-W/2+.043,.30,z],[.004,.60,.005],M.trim);for(const y of [.045,H-.04]){box('Back wall molding',[0,y,D-.046],[W,.035,.035],M.trim);box('Left wall molding',[-W/2+.047,y,D/2],[.035,.035,D],M.trim);}}
function kitchenCabinet(x,z,w,h,y,rot=0){const g=group('Raised-panel wood cabinetry',[x,y,z],rot);
 box('Cabinet carcass',[0,0,.08],[w,h,.19],M.wood,.005,g);box('Door frame',[0,0,-.025],[w-.012,h-.015,.035],M.wood,.005,g);box('Recessed wood panel',[0,-.003,-.048],[w-.071,h-.086,.017],M.wood,.012,g);
 const l=-w/2+.035,r=w/2-.035,bot=-h/2+.042,top=h/2-.045; tube('Arched panel molding',[[l,bot,-.062],[l,top-.035,-.062],[-w*.2,top-.028,-.062],[0,top+.01,-.062],[w*.2,top-.028,-.062],[r,top-.035,-.062],[r,bot,-.062]],.0055,M.wood,g);tube('Panel bottom molding',[[l,bot,-.062],[r,bot,-.062]],.0055,M.wood,g);
 tube('Antique brass cabinet pull',[[r-.012,-.036,-.07],[r-.016,-.025,-.085],[r-.016,.026,-.085],[r-.012,.038,-.07]],.005,M.darkgold,g);
}
function living(){const W=4.4,D=3.15,H=1.67;floor(W,D);ceiling(W,D,H);wallWithHoles('z',0,-W/2,W/2,H,[{c:0,w:.68,top:1.36}]);wallWithHoles('z',D,-W/2,W/2,H,[{c:-1.32,w:1.10,bottom:.65,top:1.51},{c:.6,w:1.28,bottom:.65,top:1.51}]);wallWithHoles('x',-W/2,0,D,H,[{c:1.91,w:1.40,bottom:.65,top:1.51}]);wallWithHoles('x',W/2,0,D,H,[]);
 paneling(W,D,H);windowUnit('Front dining window',-1.32,D-.035,1.10,.86,1.08);windowUnit('Front sofa window',.6,D-.035,1.28,.86,1.08);windowUnit('Left dining window',-W/2+.03,1.91,1.40,.86,1.08,-Math.PI/2);
 mesh('Seating rug',new T.PlaneGeometry(2.43,1.97),M.rug,[.58,.002,1.95],[-Math.PI/2,0,0]);mesh('Dining rug',new T.PlaneGeometry(1.13,1.65),M.rug,[-1.43,.002,1.89],[-Math.PI/2,0,0]);
 ornateSeat('Gilded sofa',.60,2.48,1.42);ornateSeat('Left carved chair',-.45,1.94,.45,-.68);ornateSeat('Right carved chair',1.58,1.80,.45,.67);
 table('Round pearl inlay coffee table',.62,1.55,.81,.71,.30,true);
 table('Dining table',-1.43,1.83,.72,1.15,.52);table('Round side table',1.52,2.41,.32,.30,.40,true);
 // TV inferred from map anchor; its appearance/location is not photographed.
 box('Estimated TV console',[2.015,.23,1.1],[.27,.46,.64],M.wood,.01);box('TV housing',[2.08,.83,1.1],[.035,.49,.79],M.black,.01);const screen=mat('Dark television glass',0x172324,.19,.15);screen.emissive=new T.Color(0x152a2d);screen.emissiveIntensity=.3;box('Static TV glass',[2.057,.83,1.1],[.004,.43,.73],screen);
 emo('EMO_livingroom_cove',[0,1.60,.06],[3.9,.025,.025]);portal('kitchen',[0,0],[0,1],.68);nav(W,D);return {W,D,H};}
function kitchen(){const W=2.5,D=2.25,H=1.67;floor(W,D);ceiling(W,D,H);
 wallWithHoles('z',0,-W/2,W/2,H,[{c:0,w:.68,top:1.36},{c:.90,w:.60,bottom:.63,top:1.13}]);kitchenCabinet(.90,.08,.60,.38,1.34,Math.PI);wallWithHoles('z',D,-W/2,W/2,H,[{c:-.70,w:.62,top:1.36}]);wallWithHoles('x',-W/2,0,D,H,[{c:.52,w:.62,top:1.36},{c:1.48,w:.60,top:1.36}]);wallWithHoles('x',W/2,0,D,H,[{c:.99,w:.87,bottom:.85,top:1.49}]);
 windowUnit('Left kitchen window',W/2-.03,.99,.87,.64,1.17,Math.PI/2);
 box('Botanical wallpaper back',[.39,1.54,D-.044],[1.68,.22,.008],M.wallpaper);box('Ceiling sage frieze',[.40,1.65,D-.05],[1.65,.06,.02],M.sage);
 for(const [zz,len] of [[.46,.72],[1.73,.97]])box('Right worktop',[1.04,.605,zz],[.43,.035,len],M.counter,.007);for(const xx of [.844,1.21])box('Sink counter surround',[xx,.605,1.05],[.064,.035,.38],M.counter,.003);box('Back worktop',[.94,.605,2.015],[.63,.035,.43],M.counter,.007);
 for(const zz of [.34,.75,1.16,1.57,1.98]){kitchenCabinet(1.035,zz,.40,.48,.29,Math.PI/2);box('Cabinet toe kick',[1.105,.035,zz],[.22,.07,.39],M.darkgold);}
 for(const xx of [-.02,.40,.82])kitchenCabinet(xx,2.04,.40,.47,.29,0);
 for(const xx of [-.02,.40,.82])kitchenCabinet(xx,2.13,.40,.40,1.19,0);
 for(const zz of [.28,1.78,2.08])kitchenCabinet(1.15,zz,.29,.40,1.19,Math.PI/2);
 // Static appliance shells establish the photographed room; Phase 4 adds controls.
 box('Range body',[.40,.30,1.93],[.45,.59,.40],M.black,.012);
 box('Range top',[.40,.602,1.93],[.45,.025,.40],M.black,.005);box('Range backguard',[.40,.665,2.11],[.45,.11,.035],M.black,.005);box('Range oven glass',[.40,.30,1.718],[.37,.29,.012],M.black,.012);
 tube('Range bar handle',[[.21,.49,1.69],[.59,.49,1.69]],.008,M.steel);
 box('Hood canopy',[.40,.99,2.02],[.50,.045,.37],M.steel,.012);box('Hood upper',[.40,1.05,2.13],[.43,.09,.15],M.steel,.014);
 box('Built-in oven tower',[-.10,.67,2.08],[.40,1.34,.31],M.wood,.006);
 for(const yy of [.45,.85]){box('Built-in oven fascia',[-.10,yy,1.912],[.34,.35,.02],M.black,.009);tube('Built-in oven handle',[[-.24,yy+.105,1.88],[.04,yy+.105,1.88]],.007,M.steel);}
 // Recessed sink represented by rim and basin, with real central opening in counter added below.
 box('Sink basin floor',[1.03,.53,1.05],[.28,.008,.35],M.steel,.015);for(const xx of [.882,1.18])box('Sink basin side',[xx,.57,1.05],[.006,.085,.35],M.steel);for(const zz of [.872,1.228])box('Sink basin side',[1.03,.57,zz],[.29,.085,.006],M.steel);for(const z of [.865,1.235])box('Sink steel rim',[1.03,.614,z],[.34,.01,.016],M.steel,.003);for(const x of [.873,1.187])box('Sink steel rim',[x,.614,1.05],[.014,.01,.38],M.steel,.003);box('Sink divider',[1.03,.615,1.05],[.32,.018,.014],M.steel,.004);
 tube('Static faucet arch',[[1.19,.62,1.1],[1.19,.80,1.1],[1.06,.83,1.1],[1.02,.75,1.1]],.009,M.steel);
 box('Counter pass-through base',[.95,.29,.25],[.50,.56,.33],M.wood,.008);
 mesh('Runner rug',new T.PlaneGeometry(.36,1.05),M.sage,[.63,.002,1.13],[-Math.PI/2,0,0]);
 emo('EMO_kitchen_under_counter',[.52,.91,2.17],[1.32,.012,.02]);portal('livingroom',[0,0],[0,1],.68);portal('office',[-.70,D],[0,-1]);portal('laundry',[-W/2,.52],[1,0],.62,'curtains');portal('hall',[-W/2,1.48],[1,0],.60);nav(W,D);return {W,D,H};}
// Build uses only standard static glTF meshes/materials, no Draco/extensions required for geometry.
window.buildHouse=async id=>{
 if(id==='kitchen'){
 const rebuilt=await completeKitchen();const room=rebuilt.room;await optimizeRoom(room);
 const bytes=await new GLTFExporter().parseAsync(room,{binary:true,onlyVisible:false,maxTextureSize:4096});return {bytes:btoa(new Uint8Array(bytes).reduce((s,b)=>s+String.fromCharCode(b),'')),manifest:rebuilt.manifest};
 }

 roomId=id;room=new T.Group();room.name=id;manifest={id,file:id+'.glb',status:'review',photographed:true,dimensionsEstimated:true,portals:[],emo:[],mainDoorway:id==='livingroom'?'kitchen':'livingroom',origin:'floor center of main doorway; local +Z points into room',windows:id==='livingroom'?['front','left']:['left']};console.log("GEOMETRY start");const dims=id==='livingroom'?living():kitchen();manifest.dimensionsMeters={width:dims.W,depth:dims.D,height:dims.H};if(id==='livingroom'){manifest.rebuild=await replaceLivingFurniture(room);manifest.status='rebuilt-awaiting-review';
 const tvFootprint=footprints.livingroom[5];room.updateMatrixWorld(true);
 footprints.livingroom=['Rebuilt gilded sofa','Rebuilt left armchair','Rebuilt right armchair','Rebuilt inlay coffee table','Rebuilt inlay dining table','Rebuilt side table'].map(n=>{const b=new T.Box3().setFromObject(room.getObjectByName(n));return [b.min.x-.01,b.min.z-.01,b.max.x+.01,b.max.z+.01];});footprints.livingroom.push(tvFootprint);
 room.getObjectByName('NAV_livingroom').removeFromParent();nav(dims.W,dims.D);
}room.userData={...manifest,meters:true,avatarHeight:1.166};window.currentRoom=room;window.roomManifest=manifest;
 console.log("GEOMETRY complete",room.children.length);await optimizeRoom(room);const exporter=new GLTFExporter();const bytes=await exporter.parseAsync(room,{binary:true,onlyVisible:false,maxTextureSize:4096});console.log("EXPORT complete",bytes.byteLength);return {bytes:btoa(new Uint8Array(bytes).reduce((s,b)=>s+String.fromCharCode(b),"")),manifest};
};
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setSize(1200,900);renderer.setPixelRatio(1);renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFShadowMap;renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;document.body.append(renderer.domElement);
window.renderHouse=async(id,view='main')=>{
 const gltf=await new GLTFLoader().loadAsync(root+'house/'+id+'.glb?v='+Date.now());const s=new T.Scene();s.background=new T.Color(0xb4bcae);s.add(gltf.scene);const pmrem=new T.PMREMGenerator(renderer);s.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;s.environmentIntensity=.30;gltf.scene.traverse(o=>{if(o.isMesh){o.castShadow=o.receiveShadow=!o.name.startsWith('PORTAL_')&&!o.name.startsWith('NAV_')&&o.name!=='Ceiling';}});
 s.add(new T.HemisphereLight(0xe1ebee,0x6c5b40,0.80));const sun=new T.DirectionalLight(0xffe3b6,1.7);sun.position.set(-3,3,4);sun.target.position.set(0,0,1);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-4,right:4,top:4,bottom:-4,near:.1,far:12});sun.shadow.bias=-.0004;sun.shadow.normalBias=.008;s.add(sun,sun.target);
 const fill=new T.DirectionalLight(0xd5e5ff,.7);fill.position.set(0,2,-2);s.add(fill);
 const camera=new T.PerspectiveCamera(65,4/3,.025,30);
 const poses=id==='livingroom'?{main:[[-.37,1.10,.58],[.63,.55,2.42]],dining:[[-0.90,1.06,0.55],[-1.43,0.52,1.83]],overview:[[0,3.9,1.58],[0,0,1.58]],scale:[[0,1.2,.16],[.1,.65,2.15]]}:{main:[[0.68,1.12,0.54],[-0.54,0.80,2.28]],reverse:[[-0.50,1.07,2.17],[-1.05,0.83,0.30]],overview:[[0,3.5,1.325],[0,0,1.325]],scale:[[0.70,1.18,0.45],[-0.40,0.65,1.9]]};let [p,t]=poses[view]||poses.main;
 if(view==='scale'){const a=await new GLTFLoader().loadAsync(root+'vintos.glb');a.scene.position.set(id==='livingroom'?-.45:-.35,0,id==='livingroom'?1.0:1.05);a.scene.rotation.y=Math.PI;s.add(a.scene);}
 if(view==='overview'){gltf.scene.traverse(o=>{if(o.name==='Ceiling'||o.name==='Wall'||o.name.startsWith('Wall_above')||o.name==='Doorway_lintel')o.visible=false;});camera.up.set(0,0,-1);}
 camera.position.set(...p);camera.lookAt(...t);renderer.render(s,camera);return {url:renderer.domElement.toDataURL('image/png'),renderer:renderer.getContext().getParameter(renderer.getContext().RENDERER)};
};window.houseReady=true;
