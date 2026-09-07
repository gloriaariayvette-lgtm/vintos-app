"""Deterministic photo-derived materials; no image-generation service.
Photo crops supply surface detail, not billboard substitutes for room geometry.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter
R=Path(__file__).resolve().parents[1]
O=R/'house/materials'; O.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(370)
def save(a,name):
    if not isinstance(a,Image.Image): a=Image.fromarray(np.uint8(np.clip(a,0,255)))
    a.convert('RGB').save(O/(name+'.jpg'),quality=91)
def rectify(file,quad,size,name):
    im=Image.open(R/'refs/rooms'/file)
    w,h=size; dst=[(0,0),(w,0),(w,h),(0,h)]; A=[]; b=[]
    for (x,y),(u,v) in zip(dst,quad):
        A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);b.extend([u,v])
    c=np.linalg.solve(A,b)
    out=im.transform(size,Image.Transform.PERSPECTIVE,c,Image.Resampling.BICUBIC)
    save(out,name)
# Rectified visible, unobstructed surface patches. Coordinates in original photos.
rectify('diningtable-1.jpg',[(900,564),(1250,590),(889,800),(618,696)],(1024,1024),'inlay')
rectify('kitchen-2.jpg',[(1160,807),(1516,823),(1446,903),(1037,870)],(1024,1024),'counter')
rectify('kitchen-2.jpg',[(1113,129),(1219,123),(1215,289),(1113,306)],(512,1024),'cabinet-wood')
rectify('livingroom-1.jpg',[(1680,633),(1777,632),(1778,751),(1640,733)],(512,512),'sage-fabric')
# Tight surface-only subcrops exclude the bowl, cabinet molding and reflections.
im=Image.open(O/'inlay.jpg').crop((380,640,860,1000)).resize((1024,1024));save(im,'inlay')
im=Image.open(O/'cabinet-wood.jpg').crop((12,10,165,360)).resize((512,1024));save(im,'cabinet-wood')
im=Image.open(O/'counter.jpg').crop((650,160,1020,670)).resize((1024,1024));save(im,'counter')
a=np.array(Image.open(O/'sage-fabric.jpg'),float);a=a-a.mean((0,1))+[105,116,92];save(a,'sage-fabric')
# Leaf canopy through a real reference window, used solely beyond glazing.
Image.open(R/'refs/rooms/diningtable-1.jpg').crop((320,100,575,405)).resize((1024,1024)).save(O/'foliage.jpg',quality=90)
# Woven floral rug reconstructed from a clear strip, mirrored into a symmetric field.
im=Image.open(R/'refs/rooms/livingroom-1.jpg').crop((330,1190,1180,1390)).resize((1024,256))
tile=Image.new('RGB',(1024,1024))
for n in range(4):tile.paste(im.transpose(Image.Transpose.FLIP_TOP_BOTTOM) if n%2 else im,(0,n*256))
d=ImageDraw.Draw(tile)
for k,c in [(8,'#aaa08c'),(19,'#444a40'),(28,'#aaa08c'),(39,'#55594b')]:d.rectangle((k,k,1023-k,1023-k),outline=c,width=5)
save(tile,'rug')
N=1024;y,x=np.mgrid[:N,:N];noise=rng.normal(0,1,(N,N));soft=gaussian_filter(noise,5)
wood=np.zeros((N,N,3))+[167,122,72]
for row in range(12):
    lo=int(row*N/12);hi=int((row+1)*N/12)
    wood[lo:hi]+=rng.normal(0,9)
    wood[lo:lo+2]*=.64
    for a in range((row%3)*120,1024,340):wood[lo:hi,a:a+2]*=.66
grain=np.sin(x*.07+np.sin(y*.024)*3+soft*8)*4+np.sin(x*.61+np.sin(y*.02))*2+noise*1.5
save(wood+grain[:,:,None],'oak')
# Small-scale jacquard motifs and weave, matching ivory/gold upholstery.
a=np.zeros((N,N,3))+[203,188,148];a+=noise[:,:,None]*2
im=Image.fromarray(np.uint8(np.clip(a,0,255)));d=ImageDraw.Draw(im)
for j in range(50,N,125):
    for i in range(55,N,125):
        i+=35 if (j//125)%2 else 0
        for ang in np.linspace(0,2*np.pi,7)[:-1]:
            cx=i+9*np.cos(ang);cy=j+9*np.sin(ang);d.ellipse((cx-6,cy-6,cx+6,cy+6),fill=(153,132,91))
        d.ellipse((i-4,j-4,i+4,j+4),fill=(199,176,120))
save(im,'brocade')
b=np.zeros((N,N,3))+[65,49,37];b+=(noise*3+np.sin(y*.14+np.sin(x*.05))*5)[:,:,None];save(b,'brown-throw')
wall=Image.new('RGB',(512,512),(218,214,194));d=ImageDraw.Draw(wall)
for j in range(0,512,80):
    for i in range(0,512,60):
        i+=30 if j%160 else 0
        d.line((i,j+68,i,j+8),fill=(133,140,119),width=2)
        for k in range(3):
            for sign in [-1,1]:d.ellipse((i-1+(sign-1)*8,j+13+k*14,i+1+(sign+1)*8,j+29+k*14),outline=(133,140,119),width=2)
save(wall,'wallpaper')
# Floor diffuse bake: soft furniture contact occlusion and window-side falloff.
# Rectangles are shared with the builder; all coordinates are room-local meters.
footprints={
 'livingroom':[[-.19,2.18,1.39,2.82],[-.84,1.55,-.06,2.32],[1.20,1.40,1.97,2.20],[.20,1.12,1.04,1.94],[-1.86,1.18,-1.00,2.48],[1.85,.75,2.16,1.45],[1.35,2.24,1.69,2.58]],
 'kitchen':[[.82,.08,1.25,2.25],[-.31,1.70,1.25,2.25],[.69,.08,1.22,.62]]}
import json
(O/'footprints.json').write_text(json.dumps(footprints,indent=2)+'\n')
for room,W,D in [('livingroom',4.4,3.15),('kitchen',2.5,2.25)]:
    n=2048; yy,xx=np.mgrid[:n,:n]; wx=(xx/n-.5)*W;wz=(1-yy/n)*D
    ao=np.ones((n,n))
    for x0,z0,x1,z1 in footprints[room]:
        dx=np.maximum(np.maximum(x0-wx,wx-x1),0);dz=np.maximum(np.maximum(z0-wz,wz-z1),0)
        ao*=1-.36*np.exp(-(dx*dx+dz*dz)/.006)
    base=np.array(Image.open(O/'oak.jpg').resize((n,n)),float)
    ao*=.88+.12*(1-wz/D)
    save(base*ao[:,:,None],room+'-floor-baked')
print('Wrote photo-derived and procedural materials to',O)
