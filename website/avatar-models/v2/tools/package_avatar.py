"""Export the preserved-rig local refinement as GLB, VRM 1.0, and skinned FBX."""
from refine_vintos import *
from fbx_binary import read_fbx,write_fbx,N,child,val
from collections import Counter
j,b=load(ROOT/'vintos-refined.glb')
# Correct inherited glTF metadata without changing bone transforms or deformation.
j['skins'][0]['skeleton']=next(i for i,n in enumerate(j['nodes']) if n.get('name')=='mixamorigHips')
for n in j['nodes']:
 if n.get('name')=='VintosRoot':
  assert not any(k in n for k in ['matrix','translation','rotation','scale']);n['children'].remove(65)
j['scenes'][0]['nodes'].append(65)
zero_slots=0
for p in j['meshes'][0]['primitives']:
 ji=p['attributes']['JOINTS_0'];jj=arr(j,b,ji);ww=arr(j,b,p['attributes']['WEIGHTS_0']);zero_slots+=int(((ww==0)&(jj!=0)).sum());jj[ww==0]=0
 ac=j['accessors'][ji];bv=j['bufferViews'][ac['bufferView']];start=bv.get('byteOffset',0)+ac.get('byteOffset',0);b[start:start+jj.nbytes]=jj.tobytes();ac['min']=jj.min(0).tolist();ac['max']=jj.max(0).tolist()
js=json.dumps(j,separators=(',',':')).encode();js+=b' '*(-len(js)%4);(ROOT/'vintos.glb').write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(b))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(b),0x004e4942)+b)
# Add semantic humanoid roles to existing nodes; do not rename or re-rig.
names={n.get('name'):i for i,n in enumerate(j['nodes'])};roles={}
for role,bone in {'hips':'Hips','spine':'Spine','chest':'Spine1','upperChest':'Spine2','neck':'Neck','head':'Head'}.items():roles[role]={'node':names['mixamorig'+bone]}
for side in ['left','right']:
 S=side.capitalize()
 for role,bone in {'Shoulder':'Shoulder','UpperArm':'Arm','LowerArm':'ForeArm','Hand':'Hand','UpperLeg':'UpLeg','LowerLeg':'Leg','Foot':'Foot','Toes':'ToeBase'}.items():roles[side+role]={'node':names['mixamorig'+S+bone]}
 for finger in ['Thumb','Index','Middle','Ring','Little']:
  mixfinger='Pinky' if finger=='Little' else finger
  segments=['Metacarpal','Proximal','Distal'] if finger=='Thumb' else ['Proximal','Intermediate','Distal']
  for n,seg in enumerate(segments,1):roles[side+finger+seg]={'node':names['mixamorig'+S+'Hand'+mixfinger+str(n)]}
vrj=copy.deepcopy(j);vrj.setdefault('extensionsUsed',[]).append('VRMC_vrm');vrj.setdefault('extensions',{})['VRMC_vrm']={'specVersion':'1.0','meta':{'name':'Vintos','version':'2-local-refinement','authors':['gloriaariayvette-lgtm (local refinement)','Original character supplied in vintos-app'],'licenseUrl':'https://vrm.dev/licenses/1.0/','references':['https://github.com/gloriaariayvette-lgtm/vintos-app'],'avatarPermission':'onlySeparatelyLicensedPerson','allowRedistribution':False},'humanoid':{'humanBones':roles},'firstPerson':{'meshAnnotations':[{'node':65,'type':'auto'}]}}
js=json.dumps(vrj,separators=(',',':')).encode();js+=b' '*(-len(js)%4);(ROOT/'vintos.vrm').write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(b))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(b),0x004e4942)+b)
# Merge the three losslessly partitioned draw groups for the FBX Geometry.
aa={};tt=[];offset=0
for p in j['meshes'][0]['primitives']:
 a={k:arr(j,b,i) for k,i in p['attributes'].items()}
 for k,v in a.items():aa.setdefault(k,[]).append(v)
 tt.append(arr(j,b,p['indices']).astype('<i4').reshape(-1,3)+offset);offset+=len(a['POSITION'])
a={k:np.concatenate(v) for k,v in aa.items()};tri=np.concatenate(tt).astype('<i4');roots=read_fbx(ROOT/'source.fbx');o=next(n for n in roots if n['name']=='Objects');conn=next(n for n in roots if n['name']=='Connections');g=next(n for n in o['children'] if n['name']=='Geometry');models={n['props'][0]:n for n in o['children'] if n['name']=='Model'};mesh=next(n for n in models.values() if n['props'][2]=='Mesh')
child(g,'Vertices')['props']=[a['POSITION'].astype('<f8').ravel()];poly=tri.copy();poly[:,2]=-poly[:,2]-1;child(g,'PolygonVertexIndex')['props']=[poly.ravel()]
uv=child(g,'LayerElementUV');coords=a['TEXCOORD_0'].astype('<f8');coords[:,1]=1-coords[:,1];child(uv,'UV')['props']=[coords.ravel()];child(uv,'UVIndex')['props']=[tri.ravel()]
normal=N('LayerElementNormal','I',[0],[N('Version','I',[101]),N('Name','S',['Normals']),N('MappingInformationType','S',['ByVertice']),N('ReferenceInformationType','S',['Direct']),N('Normals','d',[a['NORMAL'].astype('<f8').ravel()])]);g['children'].append(normal)
material_layer=N('LayerElementMaterial','I',[0],[N('Version','I',[101]),N('Name','S',['']),N('MappingInformationType','S',['AllSame']),N('ReferenceInformationType','S',['IndexToDirect']),N('Materials','i',[np.array([0],dtype='<i4')])]);g['children'].append(material_layer)
for kind in ['LayerElementNormal','LayerElementMaterial']:child(g,'Layer')['children'].append(N('LayerElement',children=[N('Type','S',[kind]),N('TypedIndex','I',[0])]))
jointnames=[j['nodes'][i]['name'] for i in j['skins'][0]['joints']];weights=a['WEIGHTS_0'];joints=a['JOINTS_0']
for cluster in [n for n in o['children'] if n['name']=='Deformer' and n['props'][2]=='Cluster']:
 cid=cluster['props'][0];mid=next(c['props'][1] for c in conn['children'] if c['props'][0]=='OO' and c['props'][2]==cid and c['props'][1] in models);name=models[mid]['props'][1].split('\0')[0].replace(':','');jid=jointnames.index(name);w=np.where(joints==jid,weights,0).sum(1);ids=np.flatnonzero(w>0);child(cluster,'Indexes')['props']=[ids.astype('<i4')];child(cluster,'Weights')['props']=[w[ids].astype('<f8')]
# FBX source metadata said centimeters despite meter-valued geometry. Declare meters.
settings=child(next(n for n in roots if n['name']=='GlobalSettings'),'Properties70')
for p in settings['children']:
 if p['props'][0] in ['UnitScaleFactor','OriginalUnitScaleFactor']:p['props'][-1]=100.
# Rest-pose mocap source: remove animation takes, retain bind pose and skeleton.
removed={n['props'][0] for n in o['children'] if n['name'].startswith('Animation')};o['children']=[n for n in o['children'] if not n['name'].startswith('Animation')];conn['children']=[c for c in conn['children'] if c['props'][1] not in removed and c['props'][2] not in removed];roots=[n for n in roots if n['name']!='Takes']
matid,texid,vidid=990000001,990000002,990000003
mat=N('Material','LSS',[matid,'VintosAtlas\0\1Material',''],[N('Version','I',[102]),N('ShadingModel','S',['phong']),N('MultiLayer','I',[0]),N('Properties70',children=[N('P','SSSSDDD',['DiffuseColor','Color','','A',1.,1.,1.]),N('P','SSSSD',['DiffuseFactor','Number','','A',1.]),N('P','SSSSDDD',['SpecularColor','Color','','A',.04,.04,.04]),N('P','SSSSD',['Shininess','Number','','A',12.])])])
tex=N('Texture','LSS',[texid,'VintosAtlas\0\1Texture',''],[N('Type','S',['TextureVideoClip']),N('Version','I',[202]),N('TextureName','S',['VintosAtlas']),N('Media','S',['VintosAtlas']),N('FileName','S',['tex/atlas-refined.png']),N('RelativeFilename','S',['tex/atlas-refined.png']),N('ModelUVTranslation','DD',[0.,0.]),N('ModelUVScaling','DD',[1.,1.]),N('Texture_Alpha_Source','S',['None']),N('Cropping','IIII',[0,0,0,0])])
imagebytes=(ROOT/'tex/atlas-refined.png').read_bytes();video=N('Video','LSS',[vidid,'VintosAtlas\0\1Video','Clip'],[N('Type','S',['Clip']),N('Filename','S',['tex/atlas-refined.png']),N('RelativeFilename','S',['tex/atlas-refined.png']),N('Content','R',[imagebytes])]);o['children'].extend([mat,tex,video]);conn['children'].extend([N('C','SLL',['OO',matid,mesh['props'][0]]),N('C','SLLS',['OP',texid,matid,'DiffuseColor']),N('C','SLL',['OO',vidid,texid])])
defs=next(n for n in roots if n['name']=='Definitions');counts=Counter(n['name'] for n in o['children']);child(defs,'Count')['props']=[sum(counts.values())];defs['children']=[n for n in defs['children'] if n['name']!='ObjectType' or n['props'][0] in counts]
for n in defs['children']:
 if n['name']=='ObjectType':child(n,'Count')['props']=[counts[n['props'][0]]]
for kind in ['Material','Texture','Video']:defs['children'].append(N('ObjectType','S',[kind],[N('Count','I',[1])]))
write_fbx(ROOT/'source-v2.fbx',roots)
report={'zero_weight_joint_slots_cleaned':zero_slots,'inherited_skin_root_metadata_fixed':True,'vrm_version':'1.0','human_bones':{r:j['nodes'][v['node']]['name'] for r,v in roles.items()},'named_mixamo_nodes':65,'fbx_vertices':len(a['POSITION']),'triangles':len(tri),'fbx_texture_embedded':True,'fbx_animation_takes':0,'fbx_units':'meters (UnitScaleFactor=100 centimeters per unit)','fbx_bone_names':'original source FBX names with mixamorig: namespace preserved; Three.js normalizes punctuation as for the original source','no_paid_services':True,'sizes':{f:(ROOT/f).stat().st_size for f in ['vintos.glb','vintos.vrm','source-v2.fbx']}}
(ROOT/'baseline/exports-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['sizes']))
