"""CPU orthographic rasterization of source.fbx; no model or bone modifications.
Reads FBX mesh vertices and polygon UVs directly. Uses the bind/rest mesh,
computed vertex normals, a z buffer, bilinear sRGB texture sampling and diffuse light.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from fbx_read import read_fbx,child,val
ROOT=Path(__file__).resolve().parents[1]
def mesh():
 roots=read_fbx(ROOT/'source.fbx');obj=next(n for n in roots if n['name']=='Objects');g=child(obj,'Geometry')
 v=val(g,'Vertices').reshape(-1,3);p=val(g,'PolygonVertexIndex');uvn=child(g,'LayerElementUV')
 assert val(uvn,'MappingInformationType')=='ByPolygonVertex'
 uv=val(uvn,'UV').reshape(-1,2)[val(uvn,'UVIndex')]
 # This source is entirely triangulated; retain its original winding and UV corners.
 assert len(p)%3==0 and np.all(p.reshape(-1,3)[:,2]<0)
 ids=np.where(p<0,-p-1,p).reshape(-1,3);tuv=uv.reshape(-1,3,2)
 n=np.cross(v[ids[:,1]]-v[ids[:,0]],v[ids[:,2]]-v[ids[:,0]])
 norm=np.zeros_like(v)
 for i in range(3):np.add.at(norm,ids[:,i],n)
 norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-12)
 return v,ids,tuv,norm

def render(v,ids,tuv,norm,path,center,span,size,view=(0,0,1)):
 w,h=size;forward=np.array(view,dtype=float);forward/=np.linalg.norm(forward)
 right=np.cross([0.,1.,0.],forward);right/=np.linalg.norm(right);up=np.cross(forward,right)
 basis=np.array([right,up,forward]);vv=(v-np.array(center))@basis.T
 scale=h/span;scr=np.stack([vv[:,0]*scale+w/2,-vv[:,1]*scale+h/2],axis=1)
 depth=np.full((h,w),-np.inf);img=np.empty((h,w,3),dtype=np.uint8);img[:]=[40,41,46]
 tex=np.asarray(Image.open(ROOT/'tex/atlas.png').convert('RGB'),dtype=float)/255
 # Lighting in linear space; textures are color data in sRGB.
 tex=np.where(tex<=.04045,tex/12.92,((tex+.055)/1.055)**2.4)
 lights=[(np.array([-.4,.7,1.]),.65),(np.array([.6,.15,.8]),.2)]
 shade=np.full(len(v),.55)
 for direction,power in lights:
  direction/=np.linalg.norm(direction);shade+=power*np.maximum(0,norm@direction)
 for tri,uv in zip(ids,tuv):
  a,b,c=scr[tri];lo=np.maximum(np.floor(np.min([a,b,c],0)).astype(int),0);hi=np.minimum(np.ceil(np.max([a,b,c],0)).astype(int),[w-1,h-1])
  if np.any(hi<lo):continue
  den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-10:continue
  yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];px=xx+.5;py=yy+.5
  wa=((b[1]-c[1])*(px-c[0])+(c[0]-b[0])*(py-c[1]))/den
  wb=((c[1]-a[1])*(px-c[0])+(a[0]-c[0])*(py-c[1]))/den;wc=1-wa-wb
  z=wa*vv[tri[0],2]+wb*vv[tri[1],2]+wc*vv[tri[2],2]
  good=(wa>=-1e-8)&(wb>=-1e-8)&(wc>=-1e-8)&(z>depth[yy,xx])
  if not good.any():continue
  y=yy[good];x=xx[good];weights=np.stack([wa[good],wb[good],wc[good]],1);uvs=weights@uv
  tx=np.clip(uvs[:,0],0,1)*(tex.shape[1]-1);ty=(1-np.clip(uvs[:,1],0,1))*(tex.shape[0]-1)
  ix=np.floor(tx).astype(int);iy=np.floor(ty).astype(int);jx=np.minimum(ix+1,tex.shape[1]-1);jy=np.minimum(iy+1,tex.shape[0]-1)
  fx=(tx-ix)[:,None];fy=(ty-iy)[:,None]
  col=(tex[iy,ix]*(1-fx)+tex[iy,jx]*fx)*(1-fy)+(tex[jy,ix]*(1-fx)+tex[jy,jx]*fx)*fy
  col*= (weights@shade[tri])[:,None];col=np.where(col<=.0031308,12.92*col,1.055*np.maximum(col,0)**(1/2.4)-.055)
  img[y,x]=(np.clip(col,0,1)*255+.5).astype('uint8');depth[y,x]=z[good]
 Image.fromarray(img).save(path)
 print(path.name,flush=True)

def main():
 v,ids,uv,n=mesh();B=ROOT/'baseline'
 render(v,ids,uv,n,B/'gloves-off-front.png',center=[.005,.59,0],span=1.3,size=(1800,1600))
 # Hand UV faces locate the target on the positive-X side of the source itself.
 handuv=(uv[:,:,0].mean(1)>.69)&(uv[:,:,1].mean(1)>.50)
 handids=np.unique(ids[handuv]);hp=v[handids];hp=hp[hp[:,0]>.48]
 print('hand bounds',hp.min(0),hp.max(0),flush=True)
 center=(hp.min(0)+hp.max(0))/2
 render(v,ids,uv,n,B/'gloves-off-hand.png',center=center,span=.19,size=(1500,1200),view=(.05,.2,1))
 report=json.loads((B/'gloves-off-verification.json').read_text());report['render']={'method':'CPU z-buffer rasterizer, original FBX geometry and per-polygon UVs, computed vertex normals, orthographic cameras, atlas-only color map','triangles':len(ids),'source_fbx_sha256':hashlib.sha256((ROOT/'source.fbx').read_bytes()).hexdigest(),'hand_center':center.tolist(),'outputs':['gloves-off-front.png','gloves-off-hand.png']};(B/'gloves-off-verification.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
