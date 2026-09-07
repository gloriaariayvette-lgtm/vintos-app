"""Render geometry reloaded independently by Three.js GLTF/FBX and three-vrm."""
from refine_vintos import *

def loaded(prefix):
 d=ROOT/'tools/runtime/qa'/prefix;meta=json.loads((d/'meta.json').read_text());a={k:[] for k in ['positions','normals','uv','indices']};offset=0;texture=None
 for m in meta['meshes']:
  for k,w in [('positions',3),('normals',3),('uv',2)]:a[k].append(np.fromfile(d/f"{m['prefix']}-{k}.bin",dtype='<f4').reshape(-1,w))
  uv=a['uv'][-1]
  if not m['flipY']:uv[:,1]=1-uv[:,1]
  a['indices'].append(np.fromfile(d/f"{m['prefix']}-indices.bin",dtype='<u4').reshape(-1,3)+offset);offset+=m['vertices']
  im=Image.open(d/f"{m['prefix']}-texture.png").convert('RGB')
  if texture is None:texture=im
  else:assert np.array_equal(texture,im)
 return {k:np.concatenate(v) for k,v in a.items()},texture

cameras={'front':([0,.59,.01],1.27,(1800,1600),(0,0,1)), 'face':([.005,1.065,.02],.245,(1100,1200),(0,0,1)), 'side':([.005,1.065,.02],.245,(1100,1200),(1,0,.08))}
cache=None;r=json.loads((ROOT/'baseline/exports-verification.json').read_text());r['render']={}
for kind,prefix in [('glb','vintos-glb'),('vrm','vintos-vrm'),('fbx','source-v2-fbx')]:
 a,tex=loaded(prefix);same=cache is not None and all(np.array_equal(a[k],cache[0][k]) for k in a) and np.array_equal(tex,cache[1])
 for view,(center,span,size,direction) in cameras.items():
  out=ROOT/f'baseline/v2-{kind}-{view}.png'
  if same:out.write_bytes((ROOT/f'baseline/v2-glb-{view}.png').read_bytes())
  else:render(a['positions'],a['indices'],a['uv'][a['indices']],a['normals'],out,center,span,size,direction,tex)
 r['render'][kind]={'source':'independently reloaded '+prefix,'identical_to_glb_render_inputs':same,'triangles':len(a['indices']),'bounds':[a['positions'].min(0).tolist(),a['positions'].max(0).tolist()]}
 if kind=='glb':cache=(a,tex)
for view in cameras:
 ims=[Image.open(ROOT/f'baseline/v2-{kind}-{view}.png') for kind in ['glb','vrm','fbx']];out=Image.new('RGB',(ims[0].width*3,ims[0].height+70),(30,31,35));d=ImageDraw.Draw(out);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',30)
 for i,im in enumerate(ims):out.paste(im,(i*im.width,70));d.text((i*im.width+30,18),['GLB — Three.js','VRM 1.0 — three-vrm','FBX — Three.js'][i],font=font,fill='white')
 out.save(ROOT/f'baseline/v2-exports-{view}.png')
(ROOT/'baseline/exports-verification.json').write_text(json.dumps(r,indent=2)+'\n')
