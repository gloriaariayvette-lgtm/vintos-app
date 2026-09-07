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
  name=b[pos+hs:pos+hs+nlen].decode();q=pos+hs+nlen;props=[];types=[]
  for _ in range(n):
   t=chr(b[q]);q+=1;types.append(t)
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
  return {'name':name,'props':props,'types':types,'children':children},end
 roots=[];q=27
 while q<len(b)-hs and any(b[q:q+hs]):
  r,q=node(q);roots.append(r)
 return roots

def children(node,name):return [n for n in node['children'] if n['name']==name]
def child(node,name):return children(node,name)[0]
def val(node,name):return child(node,name)['props'][0]

def write_fbx(path,roots,version=7700):
 wide=version>=7500;fmt='<QQQB' if wide else '<IIIB';hs=25 if wide else 13
 def prop(t,v):
  if t in 'SR':
   d=v.encode('utf8') if t=='S' else bytes(v);return t.encode()+struct.pack('<I',len(d))+d
  if t in 'YCFDIL':return t.encode()+struct.pack('<'+{'Y':'h','C':'?','F':'f','D':'d','I':'i','L':'q'}[t],v)
  dt={'f':'<f4','d':'<f8','i':'<i4','l':'<i8','b':'u1','c':'u1'}[t];a=np.asarray(v,dtype=dt).ravel();d=zlib.compress(a.tobytes(),6);return t.encode()+struct.pack('<III',len(a),1,len(d))+d
 def node(n,start):
  name=n['name'].encode();ps=b''.join(prop(t,v) for t,v in zip(n['types'],n['props']));out=bytearray(b'\0'*hs+name+ps)
  for c in n['children']:out.extend(node(c,start+len(out)))
  if n['children']:out.extend(b'\0'*hs)
  out[:hs]=struct.pack(fmt,start+len(out),len(n['props']),len(ps),len(name));return out
 out=bytearray(b'Kaydara FBX Binary  \0\x1a\0'+struct.pack('<I',version))
 for n in roots:out.extend(node(n,len(out)))
 out.extend(b'\0'*hs);out.extend(bytes.fromhex('fabca903d8ced16cb879f78916f22677'));out.extend(b'\0'*(-len(out)%16));out.extend(struct.pack('<I',version));out.extend(b'\0'*120);out.extend(bytes.fromhex('f85a8c6adef5d97eece90ce3758f290b'));Path(path).write_bytes(out)

def N(name,types='',props=None,children=None):return {'name':name,'types':list(types),'props':props or [],'children':children or []}
