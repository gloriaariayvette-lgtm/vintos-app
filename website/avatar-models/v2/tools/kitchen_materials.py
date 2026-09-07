"""Surface reconstruction from the two kitchen photographs; deterministic local processing."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scipy.ndimage import gaussian_filter
R=Path(__file__).resolve().parents[1];O=R/'house/kitchen-materials';O.mkdir(exist_ok=True)
def warp(file,q,size,name):
 im=Image.open(R/'refs/rooms'/file);w,h=size;A=[];B=[]
 for (x,y),(u,v) in zip([(0,0),(w,0),(w,h),(0,h)],q):
  A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);B.extend([u,v])
 out=im.transform(size,Image.Transform.PERSPECTIVE,np.linalg.solve(A,B),Image.Resampling.BICUBIC);out.save(O/(name+'.jpg'),quality=94);return out
warp('kitchen-1.jpg',[(129,331),(470,357),(476,970),(132,1011)],(512,1024),'ovens')
warp('kitchen-1.jpg',[(704,699),(987,694),(978,962),(707,1028)],(512,512),'range-front')
warp('kitchen-2.jpg',[(25,1005),(556,960),(560,1340),(22,1340)],(512,512),'dishwasher')
warp('kitchen-2.jpg',[(1332,68),(1415,60),(1416,185),(1330,199)],(512,1024),'wood')
warp('kitchen-1.jpg',[(1141,642),(1290,676),(1235,704),(1099,665)],(512,512),'stone')
warp('kitchen-1.jpg',[(850,756),(917,759),(909,863),(849,863)],(256,512),'towel')
warp('kitchen-1.jpg',[(760,1020),(850,1000),(884,1060),(786,1080)],(512,512),'runner')
warp('kitchen-1.jpg',[(751,60),(972,113),(971,187),(749,136)],(512,256),'wallpaper')
im=Image.open(R/'refs/rooms/diningtable-1.jpg').crop((340,130,570,405)).resize((512,512));im.save(O/'outside.jpg',quality=92)
rng=np.random.default_rng(221);n=1024;y,x=np.mgrid[:n,:n]
# Retain real grain, remove broad exposure falloff, then create a restrained relief map.
im=np.asarray(Image.open(O/'wood.jpg').crop((70,30,480,720)).resize((512,1024)),float);low=gaussian_filter(im,(55,30,0));im=np.clip(im-low*.6+np.array([129,75,35])*.6,0,255);Image.fromarray(im.astype('uint8')).save(O/'wood.jpg',quality=94)
Image.open(O/'stone.jpg').crop((20,40,480,240)).resize((512,512)).save(O/'stone.jpg',quality=94)
for name,strength in [('wood',1.7),('stone',.55),('towel',2.1),('runner',2.2)]:
 im=np.asarray(Image.open(O/(name+'.jpg')).convert('L').resize((512,512)),float)/255
 im=gaussian_filter(im,.6);dy,dx=np.gradient(im);a=np.dstack([-dx*strength,-dy*strength,np.ones_like(dx)]);a/=np.linalg.norm(a,axis=-1,keepdims=True);Image.fromarray(np.uint8((a*.5+.5)*255)).save(O/(name+'-normal.jpg'),quality=94)
# Fine oak planks, with the two counter runs represented in the floor contact bake.
n=2048;y,x=np.mgrid[:n,:n];wx=(x/n-.5)*3.4;wz=(1-y/n)*2.65
grain=rng.normal(0,1,(n,n))*1.1+np.sin(x*.10+np.sin(y*.017)*2)*2+np.sin(x*.29+np.sin(y*.035))*1.3
floor=np.zeros((n,n,3))+[164,123,76];floor+=grain[:,:,None]
for k in range(23):
 a=int(k*n/23);b=int((k+1)*n/23);floor[a:b]+=rng.normal(0,4)
 for t in range((k%4)*128,n,650):floor[a:b,t:t+1]*=.73
 floor[a:a+2]*=.79
ao=np.ones((n,n))
for x0,z0,x1,z1 in [[-1.70,.12,-1.26,2.65],[-1.70,2.18,.76,2.65],[-1.70,0,-.37,.44]]:
 dx=np.maximum(np.maximum(x0-wx,wx-x1),0);dz=np.maximum(np.maximum(z0-wz,wz-z1),0);ao*=1-.37*np.exp(-(dx*dx+dz*dz)/.018)
ao*=.90+.10*np.exp(-((wx+1.0)**2+(wz-1.25)**2)/2)
Image.fromarray(np.uint8(np.clip(floor*ao[:,:,None],0,255))).save(O/'floor.jpg',quality=93)
# Wall diffuse bake: localized warm under-hood light and cabinet contact occlusion.
y,x=np.mgrid[:512,:1024];wx=(x/1024-.5)*3.4;wy=(1-y/512)*1.67
warm=np.exp(-((wx+.34)**2/.16+(wy-.82)**2/.07))
shade=np.exp(-((wy-.86)/.07)**2)*(wx<-.65)+np.exp(-((wy-.86)/.07)**2)*(wx>-.05)*(wx<.26)
a=np.zeros((512,1024,3))+[187,179,151];a+=warm[:,:,None]*[57,43,13];a-=shade[:,:,None]*18
Image.fromarray(np.uint8(np.clip(a,0,255))).save(O/'wall-baked.jpg',quality=93)
print('Kitchen surface maps rebuilt:',len(list(O.glob('*.jpg'))))
