"""Inspect exported GLBs, doorway contracts and actual NAV triangles."""
from pathlib import Path
import json,struct,io,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from refine_vintos import load,arr
R=Path(__file__).resolve().parents[1];H=R/'house';B=R/'baseline'
manifest=json.loads((H/'house.json').read_text());source=json.loads((H/'source-house-map.json').read_text());report={}
def inside(tris,x,z):
    p=np.array([x,z]);a=tris[:,0][:,[0,2]];b=tris[:,1][:,[0,2]];c=tris[:,2][:,[0,2]]
    cross=lambda u,v:u[:,0]*v[:,1]-u[:,1]*v[:,0]
    aa=cross(b-a,p-a);bb=cross(c-b,p-b);cc=cross(a-c,p-c)
    return bool(np.any(((aa>=-1e-8)&(bb>=-1e-8)&(cc>=-1e-8))|((aa<=1e-8)&(bb<=1e-8)&(cc<=1e-8))))
for room in manifest['rooms']:
    rid=room['id'];p=H/room['file'];j,b=load(p);nodes={n.get('name'):n for n in j['nodes']};tris=0
    assert 'KHR_draco_mesh_compression' not in j.get('extensionsUsed',[])
    assert all('uri' not in im for im in j.get('images',[]))
    sizes=[]
    for im in j.get('images',[]):
        v=j['bufferViews'][im['bufferView']];off=v.get('byteOffset',0);size=Image.open(io.BytesIO(b[off:off+v['byteLength']])).size;sizes.append(size);assert max(size)<=4096
    for m in j['meshes']:
        for pr in m['primitives']:tris+=j['accessors'][pr['indices']]['count']//3 if 'indices'in pr else j['accessors'][pr['attributes']['POSITION']]['count']//3
    assert tris<=1500000
    actual={n for n in nodes if n and n.startswith('PORTAL_')};expected={p['name'] for p in room['portals']};assert actual==expected
    adjacency=next(x['adjacent']for x in source['rooms']if x['id']==rid);assert set(adjacency)=={p['targetRoom']for p in room['portals']}
    nav=nodes[room['nav']];pr=j['meshes'][nav['mesh']]['primitives'][0];v=arr(j,b,pr['attributes']['POSITION']);ix=arr(j,b,pr['indices']).reshape(-1,3)if 'indices'in pr else np.arange(len(v)).reshape(-1,3);nt=v[ix];assert np.max(np.abs(v[:,1]))<1e-7
    assert all(n in nodes for n in room['emo'])
    pending=[]
    for portal in room['portals']:
        n=nodes[portal['name']];assert np.allclose(n.get('translation',n.get('matrix',[0]*16)[12:15]),portal['position'])
        m=j['materials'][j['meshes'][n['mesh']]['primitives'][0]['material']];assert m['alphaMode']=='BLEND' and m['pbrMetallicRoughness']['baseColorFactor'][3]==0
        assert inside(nt,portal['spawn'][0],portal['spawn'][2]),('spawn blocked',portal)
        assert portal['height']>1.166
        other=next((r for r in manifest['rooms']if r['id']==portal['targetRoom']),None)
        if other:
            partner=next(p for p in other['portals']if p['name']==portal['partner']);assert partner['partner']==portal['name'];assert partner['width']==portal['width']
        else:assert portal['partnerStatus']=='pending-review';pending.append(portal['partner'])
    # Sample actual exported triangles over the full floor, including obstacle interiors.
    W=room['dimensionsMeters']['width'];D=room['dimensionsMeters']['depth'];count=0
    for x in np.linspace(-W/2+.013,W/2-.013,61):
        for z in np.linspace(.017,D-.017,59):
            blocked=any(r[0]<x<r[2]and r[1]<z<r[3]for r in room['obstacleFootprints']);assert inside(nt,x,z)!=blocked,(rid,x,z);count+=1
    val=json.loads((B/(rid+'-validation.json')).read_text());assert val['issues']['numErrors']==val['issues']['numWarnings']==0
    report[rid]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'triangles':tris,'nodes':len(j['nodes']),'textures':sizes,'validatorErrors':0,'validatorWarnings':0,'navFloorY':0,'navSamplesPassed':count,'portals':sorted(actual),'pendingPartners':pending,'noDraco':True,'embeddedTextures':True}
(B/'house-verification.json').write_text(json.dumps(report,indent=2)+'\n')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for rid,pairs in [('livingroom',[('livingroom-1.jpg','main','Seating'),('diningtable-1.jpg','dining','Dining area')]),('kitchen',[('kitchen-1.jpg','main','Worktops and cabinetry'),('kitchen-2.jpg','reverse','Reverse angle')])]:
    sheet=Image.new('RGB',(1640,1370),'#e8e5dc');d=ImageDraw.Draw(sheet)
    d.text((20,16),rid.upper()+' — REBUILT AFTER REJECTION',font=font,fill='#28312c');d.text((20,50),'Reference photos left | Exported GLB renders right | Dimensions estimated for Vintos (1.166 m)',font=small,fill='#454d45')
    for i,(ref,view,label)in enumerate(pairs):
        y=90+i*630;d.text((20,y),label+' — reference',font=small,fill='#454d45');d.text((840,y),'3D reconstruction — '+label,font=small,fill='#454d45')
        for x,p in [(20,R/'refs/rooms'/ref),(840,B/(rid+'-'+view+'.png'))]:
            im=ImageOps.contain(Image.open(p).convert('RGB'),(780,590));sheet.paste(im,(x+(780-im.width)//2,y+27+(590-im.height)//2))
    sheet.save(B/('house-'+rid+'-comparison.png'))
print(json.dumps(report,indent=2))
