"""Additional geometry-level handedness checks for the rejected kitchen rebuild."""
from pathlib import Path
import json
import numpy as np
from refine_vintos import load
R=Path(__file__).resolve().parents[1]
j,b=load(R/'house/kitchen.glb');world={};names={}
def visit(i,parent):
 n=j['nodes'][i];m=np.array(n.get('matrix',np.eye(4).T.flatten())).reshape(4,4).T
 if 'translation'in n:m[:3,3]=n['translation']
 assert np.linalg.det(m[:3,:3])>0,('Reflected transform',n.get('name'))
 w=parent@m;world[i]=w;names.setdefault(n.get('name'),[]).append(i)
 for c in n.get('children',[]):visit(c,w)
for i in j['scenes'][j.get('scene',0)]['nodes']:visit(i,np.eye(4))
camera=np.array([.68,1.12,.54]);target=np.array([-.54,.80,2.28]);f=target-camera;f/=np.linalg.norm(f);right=np.cross(f,[0,1,0]);right/=np.linalg.norm(right)
anchors=['Oven tower','Four-drawer stack','Range','Window above sink'];positions={n:world[names[n][0]][:3,3].tolist()for n in anchors}
screen=[]
for n in anchors:
 d=np.array(positions[n])-camera;screen.append(float(d@right/(d@f)))
assert all(a<b for a,b in zip(screen,screen[1:])),screen
assert positions['Window above sink'][0]<0
reverseCamera=np.array([-.50,1.07,2.17]);reverseTarget=np.array([-1.05,.83,.30]);rf=reverseTarget-reverseCamera;rf/=np.linalg.norm(rf);rr=np.cross(rf,[0,1,0]);rr/=np.linalg.norm(rr)
reverseOrder=[]
for n in ['Counter oven shell','Coffee machine shell']:
 d=world[names[n][0]][:3,3]-reverseCamera;reverseOrder.append(float(d@rr/(d@rf)))
assert reverseOrder[0]<reverseOrder[1],reverseOrder
manifest=json.loads((R/'house/house.json').read_text());room=next(r for r in manifest['rooms']if r['id']=='kitchen')
assert {p['targetRoom']for p in room['portals']}=={'livingroom','office','laundry','hall'}
assert next(p for p in room['portals']if p['targetRoom']=='laundry')['type']=='curtains'
assert next(r for r in manifest['rooms']if r['id']=='livingroom')['status']=='rejected'
val=json.loads((R/'baseline/kitchen-validation.json').read_text());assert val['issues']['numErrors']==val['issues']['numWarnings']==0
report={'status':'kitchen rebuilt, awaiting visual review; livingroom rejected','anchorWorldPositions':positions,'projectedHorizontalOrder':dict(zip(anchors,screen)),'orderMatchesPhoto1':True,'counterApplianceOrderMatchesPhoto2':True,'photo2ProjectedOrder':reverseOrder,'allNodeTransformsPositiveDeterminant':True,'nodesChecked':len(world),'windowWall':'-X','mapAdjacenciesPreserved':True,'kitchenLaundryCurtains':True,'validatorErrors':0,'validatorWarnings':0,'visualLimitations':['Dimensions and unphotographed doorway coordinates estimated','Adjacent livingroom is not represented through the pass-through until rebuilt','No claim of photogrammetry or full path-traced room bake']}
(R/'baseline/kitchen-rebuild-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

from PIL import Image,ImageDraw,ImageFont
p=R/'baseline/house-kitchen-comparison.png'
im=Image.open(p);d=ImageDraw.Draw(im);d.rectangle((0,0,1640,44),fill='#e8e5dc');d.text((20,16),'KITCHEN — REBUILT AFTER REJECTION',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22),fill='#28312c');im.save(p)
