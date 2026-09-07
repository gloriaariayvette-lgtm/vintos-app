import bpy, sys, math, os
from mathutils import Vector
src, out, mode = sys.argv[-3], sys.argv[-2], sys.argv[-1]
C=bpy.context; D=bpy.data
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)

# isolate ONE armchair: everything parented under the left armchair root
root=None
for o in D.objects:
    if 'left armchair' in o.name.lower() or 'left_armchair' in o.name.lower(): root=o; break
keep=set()
if root:
    keep.add(root.name)
    for o in D.objects:
        p=o
        while p:
            if p==root: keep.add(o.name); break
            p=p.parent
for o in list(D.objects):
    if o.type=='MESH' and o.name not in keep:
        D.objects.remove(o, do_unlink=True)
meshes=[o for o in D.objects if o.type=='MESH']
bb_min=Vector((1e9,)*3); bb_max=Vector((-1e9,)*3)
for o in meshes:
    for c in o.bound_box:
        w=o.matrix_world @ Vector(c)
        bb_min=Vector((min(bb_min[i],w[i]) for i in range(3)))
        bb_max=Vector((max(bb_max[i],w[i]) for i in range(3)))
ctr=(bb_min+bb_max)/2; size=bb_max-bb_min
print('CHAIR OBJECTS', len(meshes), 'size', [round(v,3) for v in size])

# world: soft studio
w=D.worlds.new('W'); C.scene.world=w; w.use_nodes=True
bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.55,0.57,0.60,1); bg.inputs[1].default_value=1.6
# key + fill
def lamp(name, loc, energy, size=2.0):
    l=D.lights.new(name,'AREA'); l.energy=energy; l.size=size
    o=D.objects.new(name,l); o.location=loc; C.collection.objects.link(o)
    d=(ctr-Vector(loc)).normalized()
    o.rotation_euler=d.to_track_quat('-Z','Y').to_euler(); return o
d=max(size)*2.2
lamp('key', (ctr.x+d, ctr.y-d*0.8, ctr.z+d*0.9), 900, 3.0)
lamp('fill',(ctr.x-d*0.9, ctr.y-d*0.5, ctr.z+d*0.4), 260, 3.0)

cam_d=max(size)*2.6
cd=D.cameras.new('cam'); cd.lens=60
cam=D.objects.new('cam',cd); C.collection.objects.link(cam); C.scene.camera=cam
cam.location=Vector((ctr.x+cam_d*0.62, ctr.y-cam_d*0.78, ctr.z+cam_d*0.30))
cam.rotation_euler=(ctr-cam.location).to_track_quat('-Z','Y').to_euler()

sc=C.scene
sc.render.engine='CYCLES'; sc.cycles.samples=48; sc.cycles.use_denoising=True
sc.cycles.device='CPU'
sc.render.resolution_x=900; sc.render.resolution_y=1000
sc.render.film_transparent=False
sc.view_settings.view_transform='Filmic'; sc.view_settings.look='Medium Contrast'
sc.render.filepath=out
bpy.ops.render.render(write_still=True)
print('RENDERED', out, os.path.getsize(out)//1024,'KB')
