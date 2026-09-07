import bpy, bmesh, re, sys, os
from mathutils import Vector
C=bpy.context; D=bpy.data
SRC='/home/user/gloriaariayvette-lgtm/vintos-app/website/avatar-models/v2/house/livingroom.glb'
OUT='/tmp/claude-0/-home-user/e2f786de-a444-57da-b30a-99f73bf1cb3e/scratchpad/fbxshot/models/livingroom-fixed.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

FRAME = re.compile(r'(cabriole|paw foot|leg carving|apron|oval carved|carved arm|arm molding|crest|gilt|frame|molding)', re.I)
UPHOL = re.compile(r'(upholster|cushion|pillow|throw|seat)', re.I)
FURN  = ['Rebuilt left armchair','Rebuilt right armchair','Rebuilt gilded sofa']

def weld_join(objs, name, dist, angle=40.0):
    """Join a set of parts into one object, weld coincident verts, and shade
       smoothly across the joins so the frame reads as a single carved piece."""
    if not objs: return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    C.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    ob = C.object; ob.name = name
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    me.shade_smooth()
    # keep hard edges where the surface genuinely turns a corner
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=angle*3.14159/180.0)
    except Exception:
        for p in me.polygons: p.use_smooth = True
    return ob

report=[]
for fname in FURN:
    root = D.objects.get(fname)
    if not root: continue
    parts=[c for c in D.objects if c.parent==root and c.type=='MESH']
    frame =[p for p in parts if FRAME.search(p.name) and not UPHOL.search(p.name)]
    uphol =[p for p in parts if UPHOL.search(p.name)]
    other =[p for p in parts if p not in frame and p not in uphol]
    before=len(parts)
    f = weld_join(frame, fname+' :: gilt frame', 0.009)
    u = weld_join(uphol, fname+' :: upholstery', 0.006)
    for o in (f,u):
        if o: o.parent = root
    report.append((fname, before, len(frame), len(uphol), len(other),
                   len(f.data.vertices) if f else 0, len(u.data.vertices) if u else 0))

for r in report:
    print('FIXED %-26s parts %2d -> frame(%d)+uphol(%d)+other(%d) | frame verts %d, uphol verts %d' % r)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_yup=True)
print('WROTE', OUT, os.path.getsize(OUT)//1024, 'KB')
