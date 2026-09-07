"""Check preserved animation deformation at four times, plus GLB structural bounds."""
from refine_vintos import *
from scipy.spatial.transform import Rotation,Slerp

def pose(j,b,t):
 nodes=copy.deepcopy(j['nodes']);an=j['animations'][0]
 for c in an['channels']:
  s=an['samplers'][c['sampler']];times=arr(j,b,s['input']).ravel();v=arr(j,b,s['output']);target=c['target'];k=target['path'];t0=np.clip(t,times[0],times[-1]);hi=min(np.searchsorted(times,t0,side='right'),len(times)-1);lo=max(hi-1,0);f=(t0-times[lo])/max(times[hi]-times[lo],1e-8)
  if k=='rotation':q=Slerp([0,1],Rotation.from_quat(v[[lo,hi]]))([float(f)]).as_quat()[0]
  else:q=v[lo]*(1-f)+v[hi]*f
  nodes[target['node']][k]=q
 local=[]
 for n in nodes:
  if 'matrix' in n:m=np.array(n['matrix']).reshape(4,4).T
  else:
   m=np.eye(4);m[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
  local.append(m)
 world={}
 def walk(i,parent):
  world[i]=parent@local[i]
  for c in nodes[i].get('children',[]):walk(c,world[i])
 for root in j['scenes'][j.get('scene',0)]['nodes']:walk(root,np.eye(4))
 skin=j['skins'][0];ib=arr(j,b,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);bones=np.array([world[i] for i in skin['joints']])@ib
 p=j['meshes'][0]['primitives'][0];a={k:arr(j,b,i) for k,i in p['attributes'].items()};v=np.column_stack([a['POSITION'],np.ones(len(a['POSITION']))]);out=np.zeros_like(v)
 for k in range(4):out+=np.einsum('nij,nj->ni',bones[a['JOINTS_0'][:,k]],v)*a['WEIGHTS_0'][:,k,None]
 return out[:,:3]

j,b=load(ROOT/'vintos-barehands.glb');k,c=load(ROOT/'vintos-refined.glb');n=j['accessors'][0]['count'];report=[]
for t in [0,2.5,5,10.1]:
 p=pose(j,b,t);q=pose(k,c,t);error=float(np.abs(p-q[:n]).max());assert error<1e-7 and np.isfinite(q).all();report.append({'time_seconds':t,'original_vertex_deformation_max_error_m':error,'all_refined_positions_finite':True})
for a in k['accessors']:
 v=k['bufferViews'][a['bufferView']];assert v.get('byteOffset',0)+v['byteLength']<=len(c)
p=k['meshes'][0]['primitives'][0];idx=arr(k,c,p['indices']);assert idx.max()<k['accessors'][p['attributes']['POSITION']]['count'];assert 'KHR_draco_mesh_compression' not in k.get('extensionsUsed',[])
f=ROOT/'baseline/refinement-verification.json';r=json.loads(f.read_text());r['animation_deformation_samples']=report;r['gltf_buffer_bounds_valid']=True;r['no_draco']=True;f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(report,indent=2))
