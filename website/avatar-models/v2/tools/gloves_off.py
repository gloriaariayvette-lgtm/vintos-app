"""Masked repaint; pixels outside the saved two-pixel bleed masks stay exact."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
from scipy import ndimage as ndi
from fbx_read import read_fbx,child,val
import subprocess,io
ROOT=Path(__file__).resolve().parents[1];T=ROOT/'tex';B=ROOT/'baseline'
BASE_COMMIT='0c1d45711779c77f439c2a85b1f88b298ce15c73'
def mask_for(rgb):
 # Restrict the luminance test to the actual original glove UV island.
 # A global threshold misses its dark seams and also selects bright background.
 roots=read_fbx(ROOT/'source.fbx');obj=next(n for n in roots if n['name']=='Objects');g=child(obj,'Geometry');uvn=child(g,'LayerElementUV')
 uv=val(uvn,'UV').reshape(-1,2)[val(uvn,'UVIndex')].reshape(-1,3,2)
 h,w=np.asarray(rgb).shape[:2];canvas=Image.new('L',(w,h));draw=ImageDraw.Draw(canvas)
 for tri in uv:
  if np.all(tri[:,0]>=.5) and np.all(tri[:,1]>=.5):
   pts=[((u-.5)*2*(w-1),(1-v)*2*(h-1)) for u,v in tri]
   draw.polygon(pts,fill=255)
 coverage=np.asarray(canvas)>0
 labels,n=ndi.label(coverage);sizes=np.bincount(labels.ravel());sizes[0]=0
 # Select the component sampled at the palm, not the independent oval island.
 label=labels[int(h*.35),int(w*.80)]
 if label==0:label=sizes.argmax()
 region=ndi.binary_fill_holes(labels==label)
 lum=np.asarray(rgb)[...,:3]@np.array([.2126,.7152,.0722])
 m=ndi.binary_fill_holes(region & (lum>0))
 return ndi.binary_dilation(m,structure=ndi.generate_binary_structure(2,2),iterations=2)
def original_image(name):
 data=subprocess.check_output(['git','show',BASE_COMMIT+':website/avatar-models/v2/tex/'+name],cwd=ROOT)
 return Image.open(io.BytesIO(data))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(repaint):
 if not (T/'atlas-original.png').exists():shutil.copyfile(T/'atlas.png',T/'atlas-original.png')
 raw=Image.open(repaint).convert('RGB');ar=np.asarray(raw).astype(float)
 skin=(ar[:,:,0]>ar[:,:,1]*1.25)&(ar[:,:,1]>ar[:,:,2]*1.1)&(ar[:,:,0]>110)
 labels,n=ndi.label(skin);sizes=np.bincount(labels.ravel());sizes[0]=0;skin=ndi.binary_fill_holes(labels==sizes.argmax())
 # Extend repaint colors into its dark edge pixels before applying the ORIGINAL mask.
 nearest=ndi.distance_transform_edt(~skin,return_distances=False,return_indices=True)
 extended=ar[nearest[0],nearest[1]].astype('uint8')
 paint=Image.fromarray(extended).filter(ImageFilter.GaussianBlur(.65))
 hand=original_image('HAND.png').convert('RGB');hm=mask_for(hand)
 atlas=Image.open(T/'atlas-original.png').convert('RGB');aa=np.asarray(atlas).copy();q=atlas.width//2
 tile=atlas.crop((q,0,atlas.width,q));tm=mask_for(tile);am=np.zeros(aa.shape[:2],bool);am[:q,q:]=tm
 stats={}
 for name,original,mask,value in [('atlas.png',atlas,am,None),('HAND.png',hand,hm,None),('HAND_metallic.png',original_image('HAND_metallic.png'),hm,0),('HAND_roughness.png',original_image('HAND_roughness.png'),hm,128)]:
  old=np.asarray(original).copy();out=old.copy()
  if name=='atlas.png':
   replacement=np.asarray(paint.resize((q,q),Image.Resampling.LANCZOS));out[:q,q:][tm]=replacement[tm]
  elif value is None:out[mask]=np.asarray(paint.resize(original.size,Image.Resampling.LANCZOS))[mask]
  else:
   if old.ndim==3 and old.shape[2]==4:out[mask,:3]=value
   else:out[mask]=value
  assert np.array_equal(out[~mask],old[~mask]),name
  Image.fromarray(out).save(T/name)
  check=np.asarray(Image.open(T/name));assert np.array_equal(check[~mask],old[~mask])
  stats[name]={'size':list(original.size),'masked_pixels':int(mask.sum()),'changed_pixels_outside_mask':int(np.count_nonzero(np.any(check[~mask]!=old[~mask],axis=-1))) if old.ndim==3 else int(np.count_nonzero(check[~mask]!=old[~mask])),'sha256':digest(T/name)}
 Image.fromarray((am*255).astype('uint8')).save(B/'gloves-off-atlas-mask.png')
 Image.fromarray((hm*255).astype('uint8')).save(B/'gloves-off-hand-mask.png')
 stats['mask']={'source':'original color-map luminance > 0 within original FBX glove UV island, palm-seeded connected component; enclosed holes filled','bleed':'2 pixels of 8-connected dilation at each target resolution','atlas_original_sha256':digest(T/'atlas-original.png'),'normal_map':'unchanged; requested verification uses only the atlas color map'}
 (B/'gloves-off-verification.json').write_text(json.dumps(stats,indent=2)+'\n')
 # Review image, not used as material.
 overlay=aa.copy();overlay[am]=(overlay[am]*.3+np.array([255,50,20])*.7).astype('uint8');Image.fromarray(overlay).save(B/'gloves-off-mask-review.png')
 print(json.dumps(stats,indent=2))
if __name__=='__main__':
 import sys;main(sys.argv[1] if len(sys.argv)>1 else T/'HAND-repaint-source.png')
