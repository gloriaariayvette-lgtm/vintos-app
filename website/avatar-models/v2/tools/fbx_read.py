"""Read binary FBX arrays for non-mutating texture verification renders."""
import struct,zlib
from pathlib import Path
import numpy as np

def read_fbx(path):
 b=Path(path).read_bytes(); version=struct.unpack_from('<I',b,23)[0]
 wide=version>=7500; fmt='<QQQB' if wide else '<IIIB'; hs=25 if wide else 13
 def node(pos):
  end,n,plen,nlen=struct.unpack_from(fmt,b,pos)
  if not end:return None,pos+hs
  name=b[pos+hs:pos+hs+nlen].decode();q=pos+hs+nlen;props=[]
  for _ in range(n):
   t=chr(b[q]);q+=1
   if t in 'SR':
    ln=struct.unpack_from('<I',b,q)[0];q+=4;v=b[q:q+ln];q+=ln
    props.append(v.decode('utf8','replace') if t=='S' else v)
   elif t in 'YCFDIL':
    f={'Y':'h','C':'?','F':'f','D':'d','I':'i','L':'q'}[t];props.append(struct.unpack_from('<'+f,b,q)[0]);q+=struct.calcsize(f)
   elif t in 'fdilbc':
    count,enc,ln=struct.unpack_from('<III',b,q);q+=12;v=b[q:q+ln];q+=ln
    if enc:v=zlib.decompress(v)
    props.append(np.frombuffer(v,dtype={'f':'<f4','d':'<f8','i':'<i4','l':'<i8','b':'u1','c':'u1'}[t]).copy())
   else:raise ValueError(t)
  children=[]
  while q<end-hs:
   child,q=node(q)
   if child:children.append(child)
  return {'name':name,'props':props,'children':children},end
 roots=[];q=27
 while q<len(b)-hs and any(b[q:q+hs]):
  r,q=node(q);roots.append(r)
 return roots

def children(node,name):return [n for n in node['children'] if n['name']==name]
def child(node,name):return children(node,name)[0]
def val(node,name):return child(node,name)['props'][0]
if __name__=='__main__':
 import sys
 roots=read_fbx(sys.argv[1]);obj=next(x for x in roots if x['name']=='Objects')
 for n in obj['children']:
  if n['name']=='Geometry':
   print(n['props']);print([(x['name'],[('array',v.shape) if isinstance(v,np.ndarray) else v for v in x['props']]) for x in n['children']])
  if n['name']=='Model' and 'Mesh' in n['props']:
   print('MESH',n['props']);print(child(n,'Properties70'))
