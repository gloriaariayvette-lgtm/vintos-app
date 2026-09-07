"""Deterministic local refinement; preserves original GLB and all rig/animation bytes.
Selective curved edge subdivision with seam-consistent positions, interpolated UVs,
and merged/normalized skin influences. Photo detail transferred with hand-set UV
landmarks, excluding closed eyes; no external generation or Blender involved.
"""
from pathlib import Path
import copy,struct,json,io,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
from scipy.ndimage import gaussian_filter,map_coordinates,distance_transform_edt
from scipy.spatial import Delaunay
from render_gloves_off import render
ROOT=Path(__file__).resolve().parents[1]
DT={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def load(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);return j,bytearray(b[28+n:])
def arr(j,b,i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];dt=np.dtype(DT[a['componentType']]);w=NC[a['type']]
 return np.ndarray((a['count'],w),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',w*dt.itemsize),dt.itemsize)).copy()
def imread(j,b):
 v=j['bufferViews'][j['images'][0]['bufferView']];return Image.open(io.BytesIO(b[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB')
def append_view(j,b,data,target=None):
 b.extend(b'\0'*(-len(b)%4));v={'buffer':0,'byteOffset':len(b),'byteLength':len(data)}
 if target:v['target']=target
 j['bufferViews'].append(v);b.extend(data);return len(j['bufferViews'])-1

def subdiv(a,tri):
 p=a['POSITION'];norm=a['NORMAL'];head=(p[tri,1].min(1)>.985)
 # All copies at UV seams share the curvature field so the new edges stay closed.
 key=np.round(p,6);_,inv=np.unique(key,axis=0,return_inverse=True);nn=np.zeros((inv.max()+1,3));np.add.at(nn,inv,norm);nn/=np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-10);nn=nn[inv]
 edges=set()
 for t in tri[head]:
  for x,y in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:edges.add(tuple(sorted((int(x),int(y)))))
 additions={k:[] for k in a};mid={}
 for x,y in sorted(edges):
  mid[x,y]=len(p)+len(additions['POSITION']);e=p[y]-p[x]
  for k in a:
   if k in ['JOINTS_0','WEIGHTS_0']:continue
   v=(a[k][x]+a[k][y])*.5
   if k=='POSITION':v=v-(np.dot(e,nn[x])*nn[x]-np.dot(e,nn[y])*nn[y])*.125
   if k=='NORMAL':v=v/max(np.linalg.norm(v),1e-10)
   additions[k].append(v)
  ww={}
  for z in [x,y]:
   for jid,w in zip(a['JOINTS_0'][z],a['WEIGHTS_0'][z]):ww[int(jid)]=ww.get(int(jid),0)+float(w)*.5
  pairs=sorted(ww.items(),key=lambda q:-q[1])[:4];pairs+= [(0,0)]*(4-len(pairs));ws=np.array([v for _,v in pairs]);ws/=max(ws.sum(),1e-10)
  additions['JOINTS_0'].append([v for v,_ in pairs]);additions['WEIGHTS_0'].append(ws)
 out=[]
 for x,y,z in tri:
  ab=mid.get(tuple(sorted((int(x),int(y)))));bc=mid.get(tuple(sorted((int(y),int(z)))));ca=mid.get(tuple(sorted((int(z),int(x)))))
  count=sum(v is not None for v in [ab,bc,ca])
  if count==0:out.append([x,y,z])
  elif count==3:out.extend([[x,ab,ca],[ab,y,bc],[ca,bc,z],[ab,bc,ca]])
  elif count==1:
   if ab is not None:out.extend([[x,ab,z],[ab,y,z]])
   elif bc is not None:out.extend([[y,bc,x],[bc,z,x]])
   else:out.extend([[z,ca,y],[ca,x,y]])
  else:
   if ca is None:out.extend([[y,bc,ab],[x,ab,z],[ab,bc,z]])
   elif ab is None:out.extend([[z,ca,bc],[y,bc,x],[bc,ca,x]])
   else:out.extend([[x,ab,ca],[z,ca,y],[ca,ab,y]])
 return {k:np.concatenate([v,np.array(additions[k],dtype=v.dtype)]) for k,v in a.items()},np.array(out,dtype=np.uint32)

def repaint(original,geometry=None,triangles=None):
 atlas=np.array(original)[::-1].astype(float);before=atlas.copy();rng=np.random.default_rng(731)
 # Head UV tile is lower-left, upside down. Preserve the current atlas as base.
 h=atlas[1024:2048,:1024][::-1,::-1].copy();yy,xx=np.mgrid[:1024,:1024]
 ref=np.array(Image.open(ROOT/'refs/vintos/vintos-1.jpg').convert('RGB'),float)
 # Coordinates in 1024 upright head tile and the 900-wide reference preview.
 dst=np.array([[425,644],[474,631],[533,630],[588,635],[631,654], [409,696],[459,684],[495,687],[548,687],[587,685],[645,701], [429,734],[483,724],[525,708],[553,726],[624,739], [471,754],[510,751],[539,751],[571,753], [451,789],[486,782],[526,789],[567,782],[610,789], [492,817],[511,806],[541,806],[565,818]],float)
 src=np.array([[339,172],[371,156],[410,149],[451,157],[493,177], [338,226],[353,213],[384,215],[418,213],[451,211],[511,234], [349,265],[377,251],[402,227],[436,250],[493,277], [378,294],[398,293],[419,296],[448,303], [371,333],[394,322],[414,331],[440,326],[475,340], [402,364],[415,345],[432,347],[450,368]],float)*960/900
 dt=Delaunay(dst);q=np.column_stack([xx.ravel(),yy.ravel()]);simp=dt.find_simplex(q);valid=simp>=0;xy=q[valid];s=simp[valid];T=dt.transform[s];w=np.einsum('nij,nj->ni',T[:,:2],xy-T[:,2]);w=np.column_stack([w,1-w.sum(1)]);st=np.einsum('ni,nij->nj',w,src[dt.simplices[s]])
 warped=h.copy().reshape(-1,3)
 for c in range(3):warped[valid,c]=map_coordinates(ref[:,:,c],[st[:,1],st[:,0]],order=1,mode='nearest')
 warped=warped.reshape(1024,1024,3)
 mask=np.clip(distance_transform_edt(valid.reshape(1024,1024))/35,0,1);mask=gaussian_filter(mask,3)
 # Retain open eyes, eyebrows and original nostril/lip alignment.
 for cx,cy,sx,sy in [(477,703,48,24),(567,703,48,24),(525,754,32,15),(527,790,58,22)]:mask*=1-np.exp(-(((xx-cx)/sx)**2+((yy-cy)/sy)**2)*1.8)
 skin=(h[:,:,0]>h[:,:,2]*1.18)&(h[:,:,0]>45)&(yy>620)&(yy<1005)
 # Warm neutral reference tone with restrained baked lighting; no shadows pasted wholesale.
 low=gaussian_filter(warped,(16,16,0));detail=warped-low
 target=h*.45+warped*.3+np.array([168,127,107])*.25+detail*.5
 blend=mask*.68
 h=h*(1-blend[:,:,None])+target*blend[:,:,None]
 noise=gaussian_filter(rng.normal(0,1,(1024,1024)),.45);h+=noise[:,:,None]*.8*skin[:,:,None]
 # Darken the swept hair without flattening the original strand texture.
 atlas[1024:2048,:1024]=h[::-1,::-1]
 # Hair occupies several disconnected UV islands. Trace scalp faces geometrically
 # so shared color changes also reach the small cap islands.
 hp=geometry['POSITION'];huv=geometry['TEXCOORD_0'];hc=hp[triangles].mean(1)
 selected=hc[:,1]>1.125
 hairmask=Image.new('L',(2048,2048));hd=ImageDraw.Draw(hairmask)
 hd.polygon([(1023-x,2047-y) for x,y in [(162,708),(195,610),(248,536),(325,484),(401,493),(480,530),(520,568),(561,536),(621,505),(705,502),(789,541),(837,602),(875,694),(817,678),(771,650),(697,636),(632,635),(591,620),(524,620),(456,620),(402,635),(346,642),(288,665),(220,699)]],fill=255)
 for t in triangles[selected]:hd.polygon([(float(huv[i,0]*2048),float((1-huv[i,1])*2048)) for i in t],fill=255)
 hm=np.asarray(hairmask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2)),float)/255
 lum=before@np.array([.2126,.7152,.0722]);hc=np.stack([lum*.62+3,lum*.61+3,lum*.59+3],2)
 atlas=atlas*(1-hm[:,:,None])+hc*hm[:,:,None]
 # Olive henley: color-only transform on the neutral cloth in the body tile.
 yy2,xx2=np.mgrid[:2048,:2048];r,g,b=before.transpose(2,0,1)
 cloth=(xx2<780)&(yy2<1024)&(r>18)&(np.abs(r-g)<16)&(np.abs(g-b)<17)&(b>r*.83)
 cm=gaussian_filter(cloth.astype(float),.7);lum=before@np.array([.2126,.7152,.0722]);green=np.stack([lum*.91,lum*.96,lum*.73],2)
 atlas=atlas*(1-cm[:,:,None])+green*cm[:,:,None]
 # Keep the completed hand work pixel-identical in this pass.
 atlas[1100:1901,1100:1901]=before[1100:1901,1100:1901]
 result=Image.fromarray(np.clip(atlas,0,255).astype('uint8')[::-1])
 return result,{'photo_transfer':'manually landmarked piecewise affine skin-detail transfer; eyes/lips excluded; hair and cloth selectively recolored','hand_tile_unchanged':bool(np.array_equal(np.asarray(result)[147:948,1100:1901],np.asarray(original)[147:948,1100:1901]))}

def main():
 j,b=load(ROOT/'vintos-barehands.glb');origj=copy.deepcopy(j);origb=bytes(b);p=j['meshes'][0]['primitives'][0];a={k:arr(j,b,i) for k,i in p['attributes'].items()};tri=arr(j,b,p['indices']).reshape(-1,3);old={k:v.copy() for k,v in a.items()};oldtri=tri.copy();tex=imread(j,b)
 newtex,report=repaint(tex,old,oldtri);newtex.save(ROOT/'tex/atlas-refined.png')
 for _ in range(2):a,tri=subdiv(a,tri)
 for k,v in a.items():
  idx=p['attributes'][k];ac=j['accessors'][idx];ac['bufferView']=append_view(j,b,v.tobytes(),34962);ac['count']=len(v);ac['min']=v.min(0).tolist();ac['max']=v.max(0).tolist();ac.pop('byteOffset',None)
 ac=j['accessors'][p['indices']];ac.update(bufferView=append_view(j,b,tri.tobytes(),34963),componentType=5125,count=tri.size,min=[int(tri.min())],max=[int(tri.max())]);ac.pop('byteOffset',None)
 bio=io.BytesIO();newtex.save(bio,format='PNG');j['images'][0]['bufferView']=append_view(j,b,bio.getvalue());j['buffers'][0]['byteLength']=len(b);b.extend(b'\0'*(-len(b)%4));js=json.dumps(j,separators=(',',':')).encode();js+=b' '*(-len(js)%4)
 path=ROOT/'vintos-refined.glb';path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(b))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(b),0x004e4942)+b)
 assert j['nodes']==origj['nodes'] and j['skins']==origj['skins'] and j['animations']==origj['animations']
 # Every animation and inverse bind buffer is retained verbatim at its old location.
 assert bytes(b[:len(origb)])==origb
 assert np.allclose(a['WEIGHTS_0'].sum(1),1,atol=1e-5)
 assert np.array_equal(a['POSITION'][:len(old['POSITION'])],old['POSITION'])
 report.update(original_vertices=len(old['POSITION']),refined_vertices=len(a['POSITION']),original_triangles=len(oldtri),refined_triangles=len(tri),mixamo_bones=sum(n.get('name','').startswith('mixamorig') for n in j['nodes']),skin_joints=len(j['skins'][0]['joints']),animations=[x.get('name') for x in j['animations']],nodes_skins_animations_unchanged=True,original_vertices_unchanged=True,original_buffer_bytes_unchanged=True,normalized_weights=True,bytes=path.stat().st_size,subdivision='two passes, curved edge midpoint above y=.985m; conforming transition triangles; merged top-four skin influences',source_sha256=hashlib.sha256((ROOT/'vintos-barehands.glb').read_bytes()).hexdigest())
 (ROOT/'baseline/refinement-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 cameras={'front':([0,.59,.01],1.27,(1800,1600),(0,0,1)), 'face':([.005,1.065,.02],.245,(1100,1200),(0,0,1)), 'side':([.005,1.065,.02],.245,(1100,1200),(1,0,.08))}
 for label,data,tris,texture in [('before',old,oldtri,tex),('after',a,tri,newtex)]:
  if label=='before' and '--after-only' in sys.argv:continue
  uv=data['TEXCOORD_0'].copy();uv[:,1]=1-uv[:,1]
  for view,(center,span,size,direction) in cameras.items():render(data['POSITION'],tris,uv[tris],data['NORMAL'],ROOT/f'baseline/refined-{label}-{view}.png',center,span,size,direction,texture)
 for view in cameras:
  ims=[Image.open(ROOT/f'baseline/refined-{state}-{view}.png') for state in ['before','after']];out=Image.new('RGB',(ims[0].width*2,ims[0].height+70),(30,31,35));d=ImageDraw.Draw(out);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',30)
  for i,im in enumerate(ims):out.paste(im,(i*im.width,70));d.text((i*im.width+30,18),['BEFORE — current bare-hands model','AFTER — local refinement'][i],font=font,fill='white')
  out.save(ROOT/f'baseline/refined-comparison-{view}.png')
 print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
