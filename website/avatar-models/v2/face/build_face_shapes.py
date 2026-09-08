"""First pass at giving him a face: shape keys built from UV landmarks.

The mesh has no morph targets at all, so there is nothing to edit — these are
authored from scratch by deforming the existing head geometry. Landmarks were
read off the unwrapped texture and verified against 3D position (eyes above
nose above mouth above chin, nose frontmost, eyes symmetric about x).
"""
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="face.glb")
ob=[o for o in bpy.data.objects if o.name=='Vintos'][0]
me=ob.data
n=len(me.vertices)

co=np.empty(n*3); me.vertices.foreach_get("co",co); co=co.reshape(n,3)
uv=np.load("uv.npy"); head=np.load("head_mask.npy")

def L(xc,yc): return np.array([xc/2048.0, 0.9976 - yc/2048.0])
MOUTH=L(497,800); EYEL=L(452,688); EYER=L(543,688)

def uvdist(p): return np.linalg.norm(uv-p,axis=1)
def smooth(t): t=np.clip(t,0,1); return t*t*(3-2*t)

# Landmarks are FOUND in UV (the texture is what knows where the lips are) but
# regions must be SELECTED in 3D. The face is unwrapped across seams, so
# neighbours in the atlas can sit on opposite sides of the head; selecting by
# UV proximity tore patches out of the cheek and punched a hole through the
# nose. Take each landmark's 3D centroid, then fall off by real distance.
def centroid(p, r=0.012):
    m = head & (uvdist(p) < r)
    return co[m].mean(0)

C_MOUTH, C_EYEL, C_EYER = centroid(MOUTH), centroid(EYEL), centroid(EYER)
print("3D landmarks  mouth", C_MOUTH.round(4), " eyeL", C_EYEL.round(4), " eyeR", C_EYER.round(4))

def radial(c, r_in, r_out, squash=(1.0,1.0,1.0)):
    d = (co - c) / np.array(squash)
    return smooth((r_out - np.linalg.norm(d,axis=1)) / (r_out - r_in)) * head

# the mouth region is wider than it is tall, and shallow front-to-back
w_mouth = radial(C_MOUTH, 0.004, 0.030, squash=(1.9,1.0,1.0))
w_eyeL  = radial(C_EYEL,  0.002, 0.014, squash=(1.5,1.0,1.0))
w_eyeR  = radial(C_EYER,  0.002, 0.014, squash=(1.5,1.0,1.0))
# only the front of the head: y is depth, face is at negative y
front = smooth((C_MOUTH[1] + 0.045 - co[:,1]) / 0.030)
w_mouth *= front; w_eyeL *= front; w_eyeR *= front
print("mouth region %d verts, eyeL %d, eyeR %d"%((w_mouth>0.01).sum(),(w_eyeL>0.01).sum(),(w_eyeR>0.01).sum()))

Z_MOUTH=float(C_MOUTH[2])
Z_CHIN=1.0012
Z_EYE=float((C_EYEL[2]+C_EYER[2])*0.5)

basis=ob.shape_key_add(name="Basis", from_mix=False)

def add(name, delta):
    k=ob.shape_key_add(name=name, from_mix=False)
    for i in range(n):
        d=delta[i]
        if d[0] or d[1] or d[2]:
            k.data[i].co = Vector(co[i]+d)
    k.value=0.0
    return k

# ---- jaw_open: rotate the lower face about a hinge at ear height ------------
# weight rises below the mouth line, so the upper lip barely moves and the chin
# travels the full arc, which is what a jaw actually does.
t=(Z_MOUTH+0.006-co[:,2])/(Z_MOUTH+0.006-Z_CHIN)
w_jaw=smooth(t)*head*smooth((C_MOUTH[1]+0.075-co[:,1])/0.055)
w_jaw=np.maximum(w_jaw, w_mouth*smooth((Z_MOUTH-co[:,2])/0.010))
hinge=np.array([0.0,0.010,Z_EYE-0.004])       # behind and above, near the ear
ang=np.radians(13.0)
R=np.array([[1,0,0],[0,np.cos(ang),-np.sin(ang)],[0,np.sin(ang),np.cos(ang)]])
rel=co-hinge
rot=(rel@R.T)+hinge
d_jaw=(rot-co)*w_jaw[:,None]
add("jaw_open", d_jaw)

# ---- mouth_close: press the lips together toward the mouth line -------------
lip=w_mouth*smooth((0.014-np.abs(co[:,2]-Z_MOUTH))/0.012)
d=np.zeros((n,3)); d[:,2]=(Z_MOUTH-co[:,2])*0.55*lip
add("mouth_close", d)

# ---- mouth_round (ou): purse forward and narrow -----------------------------
d=np.zeros((n,3))
d[:,0]=-co[:,0]*0.45*w_mouth
d[:,1]=-0.006*w_mouth
d[:,2]=(Z_MOUTH-co[:,2])*0.20*w_mouth
add("mouth_round", d)

# ---- mouth_wide (ee): corners out, opening thins ---------------------------
d=np.zeros((n,3))
d[:,0]=np.sign(co[:,0])*0.0055*w_mouth
d[:,1]=0.002*w_mouth
d[:,2]=(Z_MOUTH-co[:,2])*0.25*w_mouth
add("mouth_wide", d)

# ---- blinks: upper lid down to the lash line -------------------------------
for nm,wv in (("blink_L",w_eyeL),("blink_R",w_eyeR)):
    upper=wv*smooth((co[:,2]-Z_EYE)/0.011)          # only the lid above centre
    d=np.zeros((n,3))
    d[:,2]=-(co[:,2]-(Z_EYE-0.0035))*0.95*upper
    d[:,1]=-0.0015*upper
    add(nm,d)

print("shape keys:",[k.name for k in me.shape_keys.key_blocks])
bpy.ops.export_scene.gltf(filepath="vintos-face.glb", export_format='GLB',
                          export_morph=True, use_selection=False)
print("exported")
