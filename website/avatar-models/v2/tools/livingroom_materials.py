"""Photo surface extraction and shallow solid reliefs for the actual carved seating."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageFilter
from scipy.ndimage import gaussian_filter,binary_closing,binary_opening,label
R=Path(__file__).resolve().parents[1];O=R/'house/livingroom-materials';O.mkdir(exist_ok=True)
src=Image.open(R/'refs/rooms/livingroom-1.jpg')
def warp(im,q,size):
 w,h=size;A=[];B=[]
 for (x,y),(u,v) in zip([(0,0),(w,0),(w,h),(0,h)],q):A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);B.extend([u,v])
 return im.transform(size,Image.Transform.PERSPECTIVE,np.linalg.solve(A,B),Image.Resampling.BICUBIC)
def save(im,n):im.convert('RGB').save(O/(n+'.jpg'),quality=94)
save(warp(src,[(593,78),(870,91),(865,300),(610,300)],(768,768)),'medallion')
save(Image.open(O/'medallion.jpg').crop((90,35,630,620)).resize((768,768)),'medallion')
save(src.crop((1580,780,1750,915)).resize((512,512)),'brocade')
save(src.crop((353,371,641,484)).resize((768,512)),'throw')
save(src.crop((1000,251,1100,317)).resize((512,512)),'sage')
a=np.array(Image.open(O/'sage.jpg'),float);a=a-a.mean((0,1))+[88,97,67];save(Image.fromarray(np.uint8(np.clip(a,0,255))),'sage')
save(src.crop((1128,244,1200,319)).resize((512,512)),'dark-pillow')
# Unobstructed floral inlay from the near part of the round table, not its bowl/laptop.
save(warp(src,[(399,779),(819,734),(937,871),(456,905)],(1024,512)),'inlay')
for n,scale in [('medallion',1),('brocade',1),('throw',2),('sage',2),('dark-pillow',2),('inlay',1)]:
 a=np.asarray(Image.open(O/(n+'.jpg')).convert('L').resize((512,512)),float)/255;a=gaussian_filter(a,1);dy,dx=np.gradient(a);v=np.dstack([-dx*scale,-dy*scale,np.ones_like(dx)]);v/=np.linalg.norm(v,axis=-1,keepdims=True);save(Image.fromarray(np.uint8((v*.5+.5)*255)),n+'-normal')
def relief(n,crop,res):
 im=src.crop(crop).resize(res,Image.Resampling.LANCZOS);a=np.asarray(im,float)/255;r,g,b=a.transpose(2,0,1)
 mask=(r>g*1.13)&(g>b*1.16)&(r>.19);mask=binary_closing(mask,iterations=1);mask=binary_opening(mask,iterations=1)
 yy,xx=np.mgrid[:res[1],:res[0]]
 if n=='crest':mask&=yy<(45+30*xx/res[0])*res[1]/108
 if n=='wing':mask&=yy<res[1]*.84
 labels,count=label(mask);sizes=np.bincount(labels.ravel());mask&=sizes[labels]>max(20,sizes[1:].max()*.015)
 # Front and back share a sampled contour, with thickness and light-derived carved relief.
 h,w=mask.shape;lum=gaussian_filter(a.mean(2),1);active=mask[:-1,:-1]&mask[1:,:-1]&mask[:-1,1:]&mask[1:,1:]
 use=np.zeros_like(mask);use[:-1,:-1]|=active;use[1:,:-1]|=active;use[:-1,1:]|=active;use[1:,1:]|=active
 ys,xs=np.where(use);ids=np.full(mask.shape,-1,int);ids[ys,xs]=np.arange(len(xs));N=len(xs)
 xy=np.c_[xs/(w-1)-.5,.5-ys/(h-1)];front=np.c_[xy,.003+lum[ys,xs]*.012];back=np.c_[xy,np.zeros(N)-.006];pos=np.vstack([front,back]).astype('<f4');uv=np.tile(np.c_[xs/(w-1),1-ys/(h-1)],(2,1)).astype('<f4');ix=[]
 for y,x in zip(*np.where(active)):
  aa,bb,cc,dd=ids[y,x],ids[y,x+1],ids[y+1,x+1],ids[y+1,x]
  ix.extend([aa,dd,cc,aa,cc,bb,aa+N,cc+N,dd+N,aa+N,bb+N,cc+N])
  for boundary,u,v in [(y==0 or not active[y-1,x],aa,bb),(x==w-2 or not active[y,x+1],bb,cc),(y==h-2 or not active[y+1,x],cc,dd),(x==0 or not active[y,x-1],dd,aa)]:
   if boundary:ix.extend([u,v,v+N,u,v+N,u+N])
 ix=np.asarray(ix,dtype='<u4');data=pos.tobytes()+uv.tobytes()+ix.tobytes();(O/(n+'.bin')).write_bytes(data);save(im,n)
 Image.fromarray(np.uint8(mask)*255).save(R/'tools/runtime/qa'/(n+'-mask.png'))
 return {'name':n,'vertices':len(pos),'indices':len(ix),'positionsBytes':pos.nbytes,'uvBytes':uv.nbytes,'sourceCrop':crop,'resolution':res,'method':'Color-segmented photographed gilt, solid shallow relief; depth inferred'}
meta=[relief('crest',(476,0,964,108),(400,90)),relief('wing',(900,57,1157,207),(240,140))]
(O/'reliefs.json').write_text(json.dumps(meta,indent=2)+'\n')
print(meta)
