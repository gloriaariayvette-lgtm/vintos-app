import * as T from 'three';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
import {ParametricGeometry} from 'three/addons/geometries/ParametricGeometry.js';
export async function replaceLivingFurniture(room){
 const base='../../house/livingroom-materials/',L=new T.TextureLoader(),tx={};
 for(const n of ['medallion','brocade','throw','sage','dark-pillow','inlay','crest','wing','medallion-normal','brocade-normal','throw-normal','sage-normal','dark-pillow-normal','inlay-normal']){const t=await L.loadAsync(base+n+'.jpg');t.userData.mimeType='image/jpeg';t.colorSpace=n.endsWith('normal')?T.NoColorSpace:T.SRGBColorSpace;tx[n]=t;}
 for(const n of ['brocade','brocade-normal','throw','throw-normal','inlay','inlay-normal']){tx[n].wrapS=tx[n].wrapT=T.RepeatWrapping;tx[n].repeat.set(3,3);}
 const mat=(name,color,roughness,metalness=0,map)=>new T.MeshStandardMaterial({name,color,roughness,metalness,map:map?tx[map]:null});
 const M={gold:mat('Carved aged gilt',0xa88842,1/2,3/5),darkgold:mat('Gilt recess shadow',0x4a3419,3/5,2/5),cream:mat('Photographed brocade',0xffffff,9/10,0,'brocade'),medallion:mat('Actual embroidered central medallion',0xffffff,9/10,0,'medallion'),throw:mat('Photographed brown velvet throw',0xffffff,1,0,'throw'),sage:mat('Photographed sage cord cushion',0xffffff,1,0,'sage'),dark:mat('Photographed dark cord cushion',0xffffff,1,0,'dark-pillow'),ivory:mat('Pearl painted table structure',0xd6c7a7,2/5),inlay:mat('Actual floral shell inlay',0xffffff,1/4,1/10,'inlay')};
 for(const [m,n]of [['cream','brocade'],['medallion','medallion'],['throw','throw'],['sage','sage'],['dark','dark-pillow'],['inlay','inlay']]){M[m].normalMap=tx[n+'-normal'];M[m].normalScale.set(1/3,1/3);}
 const cm=x=>x/100,V=a=>a.map(cm);
 const mesh=(n,geo,m,p,parent)=>{const a=new T.Mesh(geo,m);a.name=n;a.position.set(...V(p));a.castShadow=a.receiveShadow=true;parent.add(a);return a;};
 const B=(n,p,s,m,parent,r=2)=>mesh(n,new RoundedBoxGeometry(...V(s),4,cm(r)),m,p,parent);
 const U=(n,pts,r,m,parent)=>mesh(n,new T.TubeGeometry(new T.CatmullRomCurve3(pts.map(p=>new T.Vector3(...V(p)))),Math.min(96,pts.length*12),cm(r),10,false),m,[0,0,0],parent);
 const G=(n,p,rot=0,parent=room)=>{const a=new T.Group();a.name=n;a.position.set(...V(p));a.rotation.y=rot;parent.add(a);return a;};
 const reliefData=await (await fetch(base+'reliefs.json')).json(),reliefs={};
 for(const d of reliefData){const a=await(await fetch(base+d.name+'.bin')).arrayBuffer(),geo=new T.BufferGeometry();geo.setAttribute('position',new T.BufferAttribute(new Float32Array(a,0,d.vertices*3),3));geo.setAttribute('uv',new T.BufferAttribute(new Float32Array(a,d.positionsBytes,d.vertices*2),2));geo.setIndex(new T.BufferAttribute(new Uint32Array(a,d.positionsBytes+d.uvBytes,d.indices),1));geo.computeVertexNormals();reliefs[d.name]=geo;}
 function relief(n,p,w,h,parent,flip=false){const geo=reliefs[n].clone(),v=geo.attributes.position;for(let i=0;i<v.count;i++)v.setXYZ(i,v.getX(i)*cm(w)*(flip?-1:1),v.getY(i)*cm(h),v.getZ(i));if(flip){const ix=geo.index.array;for(let i=0;i<ix.length;i+=3){const a=ix[i];ix[i]=ix[i+2];ix[i+2]=a;}}geo.computeVertexNormals();const m=mat('Photographed carved '+n,0xffffff,3/5,2/5,n);return mesh('Photo-derived solid '+n+' relief',geo,m,p,parent);}
 function cabriole(x,z,sign,parent){const geo=new ParametricGeometry((u,v,out)=>{const a=u*Math.PI*2,t=v,r=cm(1.5+1.2*Math.sin(Math.PI*t)+t);out.set(cm(x+sign*(3*Math.sin(Math.PI*t)-t))+Math.cos(a)*r,cm(2+24*t),cm(z+2*Math.sin(Math.PI*t))+Math.sin(a)*r);},18,32);mesh('Sculpted cabriole leg',geo,M.gold,[0,0,0],parent);const foot=mesh('Carved paw foot',new T.SphereGeometry(1,18,12),M.gold,[x-sign,z*0+2,z+1],parent);foot.scale.set(cm(3),cm(2),cm(4));
  U('Leg carving ridge',[[x,4,z+3],[x+sign*2,12,z+4],[x+sign*2,22,z+2]],1/2,M.darkgold,parent);
 }
 function cushion(n,p,w,h,material,parent,tilt=0){
  const geo=new RoundedBoxGeometry(...V([w,h,12]),10,cm(5));
  const pos=geo.attributes.position;for(let i=0;i<pos.count;i++){
   const x=pos.getX(i),y=pos.getY(i),z=pos.getZ(i),nx=x/cm(w/2),ny=y/cm(h/2);
   const puff=Math.max(0,(1-nx*nx)*(1-ny*ny));
   pos.setXYZ(i,x*(1-.035*Math.cos(ny*4)),y, z+Math.sign(z)*cm(3)*puff);
  }geo.computeVertexNormals();
  const a=mesh(n,geo,material,p,parent);a.rotation.z=tilt;a.rotation.x=-1/8;
  const seam=[];for(let i=0;i<=80;i++){const t=i/80*Math.PI*2,c=Math.cos(t),s=Math.sin(t);seam.push([Math.sign(c)*Math.pow(Math.abs(c),.3)*(w/2-.5),Math.sign(s)*Math.pow(Math.abs(s),.3)*(h/2-.5),0]);}
  U(n+' stitched edge',seam,.25,material,a);return a;
 }
 function seating(n,p,w,rot,sofa){const a=G(n,p,rot),half=w/2;
  B('Deep upholstered seat',[0,30,0],[w,14,51],M.cream,a,5);B('Shaped gilt seat apron',[0,23,0],[w+3,7,48],M.darkgold,a,2);
  U('Front carved serpentine apron',[[-half,25,24],[-half/2,23,28],[0,22,29],[half/2,23,28],[half,25,24]],2,M.gold,a);
  for(const x of [-1,1])for(const z of [-17,18])cabriole(x*(half-5),z,x,a);
  if(sofa){
   B('Central tall upholstered back',[0,67,-23],[67,56,11],M.medallion,a,5);
   U('Central back carved frame',[[-36,37,-22],[-37,68,-23],[-35,95,-23],[0,97,-24],[35,95,-23],[37,68,-23],[36,37,-22]],2,M.gold,a);
   relief('crest',[0,98,-21],88,20,a);
   for(const sign of [-1,1]){relief('wing',[sign*53,78,-16],43,31,a,sign<0);const side=B('Curved upholstered side back',[sign*56,53,-11],[31, 31,12],M.cream,a,8);side.rotation.y=-sign/3;
    U('Wing support and scroll',[ [sign*35,94,-23],[sign*50,76,-20],[sign*70,75,-14],[sign*73,56,0]],1.5,M.gold,a);
   }
   // Continuous draped cloth, with rolls across the seat and a hanging scalloped skirt.
   const cloth=new ParametricGeometry((u,v,out)=>{
    const drape=Math.min(v/.28,1),z=v<.28?27+Math.sin(drape*Math.PI):27-(v-.28)/.72*53;
    const y=v<.28?16+24*drape:40;
    out.set((u-.5)*cm(w-2),cm(y+.6*Math.sin(u*33+v*4)*Math.sin(v*11)),cm(z+.3*Math.sin(u*41)));
   },120,64);const clothMat=M.throw.clone();clothMat.side=T.DoubleSide;mesh('Continuous heavy draped throw',cloth,clothMat,[0,0,0],a);
   cushion('Left dark cushion',[-43,60,-4],31,40,M.dark,a,1/6);cushion('Right dark cushion',[49,59,-4],31,40,M.dark,a,-1/6);cushion('Sage pillow',[35,53,6],29,29,M.sage,a,-1/8);cushion('Cream pillow',[-56,54,6],27,28,M.cream,a,1/9);
  }else{
   const back=mesh('Rounded upholstered chair back',new T.SphereGeometry(1, 40,30),M.cream,[0,61,-19],a);back.scale.set(cm(23),cm(29),cm(6));
   const pts=[];for(let i=0;i<=40;i++){const t=i/40*Math.PI*2;pts.push([26*Math.sin(t),61+31*Math.cos(t),-19]);}U('Oval carved chair frame',pts,2,M.gold,a);const crest=relief('crest',[0,92,-17],54,14,a);const cp=crest.geometry.attributes.position;for(let i=0;i<cp.count;i++){const x=cp.getX(i)/cm(27);cp.setY(i,cp.getY(i)+cm(31*(Math.sqrt(Math.max(0,1-x*x))-1)));}crest.geometry.computeVertexNormals();
   cushion('Large sage chair cushion',[0,57,0],37,36,M.sage,a,-1/20);
  }
  for(const sign of [-1,1]){U('Carved arm and front support',[[sign*(half-2),34,22],[sign*(half+2),51,20],[sign*(half+3),56,4],[sign*(half-1),62,-14]],2.5,M.gold,a);U('Arm molding shadow',[[sign*(half-1),35,24],[sign*(half+3),51,22],[sign*(half+4),56,6]],1/2,M.darkgold,a);}
  return a;
 }
 function table(n,p,w,d,h,round){const a=G(n,p);if(round){mesh('Molded round table edge',new T.CylinderGeometry(cm(w/2),cm(w/2),cm(3),80),M.ivory,[0,h,0],a);const top=mesh('Floral inlay surface',new T.CircleGeometry(cm(w/2-1),80),M.inlay,[0,h+2,0],a);top.rotation.x=-Math.PI/2;}else{B('Molded dining top',[0,h,0],[w,3,d],M.ivory,a,1);const top=mesh('Floral inlay dining surface',new T.PlaneGeometry(cm(w-2),cm(d-2)),M.inlay,[0,h+2,0],a);top.rotation.x=-Math.PI/2;B('Dining apron',[0,h-5,0],[w-7,9,d-7],M.ivory,a,1);}
  for(const x of [-1,1])for(const z of [-1,1]){const profile=[[2,0],[3,2],[2,5],[3,7],[5,13],[3,18],[2,23],[4,28],[5,36],[3,43],[4,48]].map(([r,y])=>new T.Vector2(cm(r),cm(y/48*(h-2))));mesh('Turned pearl table leg',new T.LatheGeometry(profile,36),M.ivory,[x*w/3,0,z*d/3],a);for(const yy of [7,22,42]){const ring=mesh('Aged gilt leg band',new T.TorusGeometry(cm(3),cm(1/3),8,32),M.gold,[x*w/3,yy/48*(h-2),z*d/3],a);ring.rotation.x=Math.PI/2;}}
 }
 for(const n of ['Gilded sofa','Left carved chair','Right carved chair','Round pearl inlay coffee table','Dining table','Round side table']){const old=room.getObjectByName(n);old?.removeFromParent();}
 seating('Rebuilt gilded sofa',[60,0,248],142,Math.PI,true);seating('Rebuilt left armchair',[-45,0,194], 40,Math.PI-2/3,false);seating('Rebuilt right armchair',[158,0,180],40,Math.PI+2/3,false);
 table('Rebuilt inlay coffee table',[62,0,155],81, 60,30,true);table('Rebuilt inlay dining table',[-143,0,183],72,115,52,false);
 const side=G('Rebuilt side table',[152,0,241]);mesh('Side table inlay',new T.CylinderGeometry(cm(16),cm(16),cm(2),48),M.inlay,[0, 40,0],side);for(let i=0;i<3;i++){const a=i*Math.PI*2/3;U('Slender curved brass side-table leg',[[Math.cos(a)*10,39,Math.sin(a)*10],[Math.cos(a)*8,27,Math.sin(a)*8],[Math.cos(a)*14,2,Math.sin(a)*14]],1/2,M.gold,side);}
 return {furnitureRebuilt:true,reliefSource:'actual photo color segmentation; shallow inferred depth',centralSofaBack:true,mirroredWingDetails:'left filigree inferred symmetrically from visible right wing'};
}
