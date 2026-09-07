"""Losslessly repack the review GLB below the connector's 16 MiB request limit.
Split triangle draw groups for uint16 indices; use uint8 joint indices (0..51).
Preserve every attribute value, triangle corner, texture pixel, node and animation.
"""
from refine_vintos import *
path=ROOT/'vintos-refined.glb';j,b=load(path);original=copy.deepcopy(j);prim=j['meshes'][0]['primitives'][0];a={k:arr(j,b,i) for k,i in prim['attributes'].items()};tri=arr(j,b,prim['indices']).reshape(-1,3);chunks=[];seen=set();start=0
# Morton order keeps adjacent surface triangles in the same draw group and
# avoids duplicating vertices across distant pieces of the original index order.
cent=a['POSITION'][tri].mean(1);q=((cent-cent.min(0))/np.maximum(np.ptp(cent,axis=0),1e-8)*1023).astype('uint64');code=np.zeros(len(tri),dtype='uint64')
for bit in range(10):
 for axis in range(3):code|=((q[:,axis]>>bit)&1)<<(bit*3+axis)
tri=tri[np.argsort(code,kind='stable')]
for i,t in enumerate(tri):
 ids=set(map(int,t))
 if len(seen)+len(ids-seen)>65000:chunks.append(tri[start:i]);start=i;seen=set()
 seen.update(ids)
chunks.append(tri[start:]);newprim=[];corner_verified=True;totalverts=0
for ci,tr in enumerate(chunks):
 ids,inv=np.unique(tr,return_inverse=True);inv=inv.ravel();totalverts+=len(ids);part={'mode':4,'attributes':{},'material':prim['material']}
 for k,v in a.items():
  out=v[ids];component=5126
  if k=='JOINTS_0':assert out.max()<256;out=out.astype('u1');component=5121
  assert np.array_equal(out[inv],v[tr.ravel()])
  ac={'bufferView':append_view(j,b,out.tobytes(),34962),'componentType':component,'count':len(out),'type':'VEC'+str(out.shape[1]),'min':out.min(0).tolist(),'max':out.max(0).tolist()}
  idx=prim['attributes'][k] if ci==0 else len(j['accessors'])
  if ci==0:j['accessors'][idx]=ac
  else:j['accessors'].append(ac)
  part['attributes'][k]=idx
 out=inv.astype('<u2');ac={'bufferView':append_view(j,b,out.tobytes(),34963),'componentType':5123,'count':len(out),'type':'SCALAR','min':[int(out.min())],'max':[int(out.max())]};idx=prim['indices'] if ci==0 else len(j['accessors'])
 if ci==0:j['accessors'][idx]=ac
 else:j['accessors'].append(ac)
 part['indices']=idx;newprim.append(part)
j['meshes'][0]['primitives']=newprim
used=sorted({a['bufferView'] for a in j['accessors']}|{im['bufferView'] for im in j['images']});data=bytearray();views=[];mapping={}
for old in used:
 v=copy.deepcopy(j['bufferViews'][old]);raw=b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];data.extend(b'\0'*(-len(data)%4));v['byteOffset']=len(data);mapping[old]=len(views);views.append(v);data.extend(raw)
for ac in j['accessors']:ac['bufferView']=mapping[ac['bufferView']]
for im in j['images']:im['bufferView']=mapping[im['bufferView']]
j['bufferViews']=views;j['buffers'][0]['byteLength']=len(data);data.extend(b'\0'*(-len(data)%4));js=json.dumps(j,separators=(',',':')).encode();js+=b' '*(-len(js)%4);path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(data))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(data),0x004e4942)+data)
assert j['nodes']==original['nodes'] and j['skins']==original['skins'] and j['animations']==original['animations']
report=json.loads((ROOT/'baseline/refinement-verification.json').read_text());report.update(bytes=path.stat().st_size,lossless_packing={'draw_groups':len(chunks),'draw_vertices_including_group_boundaries':totalverts,'every_triangle_corner_attribute_verified_exact':True,'joint_component_type':'UNSIGNED_BYTE','index_component_type':'UNSIGNED_SHORT','unused_buffer_views_removed':True});(ROOT/'baseline/refinement-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['lossless_packing']));print('bytes',path.stat().st_size)
