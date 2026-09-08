# A first face

`vintos.vrm` has **zero morph targets**, no VRM expressions, no lookAt, no jaw
bone and no eye bones. His expression is painted into the texture. Nothing in the
renderer, the house or the glasses can make a static face move, so this is the
work that unblocks all of it.

`vintos-face-v1.glb` is a first pass: six shape keys authored onto the existing
`vintos-barehands.glb` geometry, no re-rigging, no re-topology, body and skinning
untouched.

| shape | what it does | verdict |
|---|---|---|
| `jaw_open` | lower face rotates 13 degrees about a hinge at ear height | **works** — reads as an open mouth |
| `mouth_round` | lips purse forward and narrow | **works** |
| `mouth_wide` | corners out, opening thins | **works** |
| `mouth_close` | lips press to the mouth line | **works**, subtle |
| `blink_L` / `blink_R` | upper lid travels to the lash line | **does not work** — see below |

See `face-shapes-contact.png` for all six rendered side by side.

## How the features were found

The mesh has no facial landmarks, so the texture was used to find them and the
geometry was used to act on them.

1. Isolate the head by `mixamorigHead` skin weight > 0.5 — 6,920 vertices.
2. Unwrap: the head occupies atlas UV u 0.002-0.498, v 0.556-0.998, with the face
   down the centre and the sides flanking it (`head-uv-atlas.png`).
3. Read the mouth, eye, nose and chin positions off that image in UV.
4. Convert each landmark to a **3D centroid**, and select regions by real distance
   in 3D with a smooth falloff.

Step 4 is the one that matters. The first attempt selected by UV proximity and
tore ragged patches out of the cheek and punched a hole through the nose, because
the face is unwrapped across seams — vertices adjacent in the atlas can sit on
opposite sides of the head. Verified afterwards: eyes above nose above mouth above
chin, nose frontmost, eyes symmetric about x.

## What this is not

- **No blink, and not fixable this way.** There is no eyeball. Measured around the
  eye centroid, the surface is continuous skin with about 10 mm of curvature and no
  separate sphere; the eye is painted on. Moving the lid drags a painted eye down
  with it. A real blink needs a modelled socket and eyeball, which is sculpting.
- **No mouth interior.** Opening the jaw stretches skin over a gap. There are no
  teeth, tongue, gums or inner lip. At conversational distance this will read as
  wrong.
- **Four vowel-ish shapes is not a viseme set.** These cover open, rounded, wide
  and closed. Convincing speech also needs consonant articulation and proper lip
  closure against teeth.
- **No expressions.** No smile, frown, brow, or anything that carries feeling. This
  is articulation only.
- Nothing here is mapped to VRM expression presets yet, so three-vrm will not
  drive it by name until that mapping exists.

## Reproducing

```bash
python build_face_shapes.py     # needs bpy 5.x and vintos-barehands.glb as face.glb
```

The script is deliberately readable: region weights first, then one block per
shape. Adjusting a shape means changing a few numbers, not re-deriving anything.

## What this changes about the estimate

The review put a controllable face at 10-20 specialist days. That still stands for
a finished one — eyeballs, mouth interior, teeth, a real viseme set, expressions.
But "he cannot move his mouth at all" is no longer true, and the parts that were
scriptable are done. What remains is the part that genuinely needs an artist.
