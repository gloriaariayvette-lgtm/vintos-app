# Multi-view: how he gets depth without being 3D

The problem this solves, in her words: *"He needs to stand at the kitchen counter,
I walk by and notice him facing away, I walk around to the front of the counter and
face him, the whole time he doesn't flip, and the image itself changes as if he has
depth."*

So: **the plane must not rotate**, and **which clip is playing must change with
where she stands**. Those two together read as depth. Neither alone does.

## The asset

Four clips of the same man, same clothes, same action, same locked camera, from
four sides. Generated from one front still through nano-banana's two-reference
path so face and outfit hold across all four:

```
neutral-front-idle-1.mp4    he faces the camera
neutral-left-idle-1.mp4     profile, facing the left edge of frame
neutral-right-idle-1.mp4    profile, facing the right edge of frame
neutral-back-idle-1.mp4     seen from directly behind
```

Each is matted and packed as `<name>.packed.mp4` (colour left, matte right).

## Placement

The anchor stores a **facing** — a horizontal direction in world space, the way he
is turned. At the counter that is the direction he is looking, roughly into the
counter. The plane's yaw is locked to that facing and **never** billboards.

## Choosing the view

Let `f` be his facing (unit, horizontal) and `v` the horizontal vector from the
anchor to the camera, normalised. Then

```
cosA = dot(f, v)
cross = f.x * v.z - f.z * v.x          // sign tells left from right
bearing = atan2(cross, cosA)           // -pi..pi, 0 = she is in front of him
```

`bearing` is where she is standing relative to the way he is turned:

| bearing | she is | clip |
|---|---|---|
| −45°..+45° | in front of him | `front` |
| +45°..+135° | off to one side | `right` or `left` — see below |
| ±135°..180° | behind him | `back` |

Which of `left`/`right` a positive bearing selects depends on the handedness of
the coordinate system and on which way each clip actually faces. **Do not derive
it — verify it once on the device**, standing to his left and checking that you
see the clip of his left side, and hard-code the sign with a comment saying it was
measured, not reasoned.

## Switching without a visible jump

The four clips are generated independently, so they are not frame-synchronised. A
hard cut between them will read as a glitch.

- **Hysteresis.** Switch only when the bearing crosses a boundary by more than
  ~8°, so standing near a boundary does not strobe between two views.
- **Cross-fade** over ~250 ms: keep both players alive, fade opacity from one to
  the other. Both are already decoding; only the blend changes.
- **Do not reset playback** on switch. Let each clip run continuously on its own
  loop so a returning view is not always restarting from frame zero.

## Why not just rotate one plane

Because that is exactly the thing she does not want. A billboarded plane means he
pivots to face her wherever she goes, which reads as a cardboard cut-out on a
turntable and destroys the illusion that he is standing somewhere. Fixing the yaw
is what makes him *placed*; changing the clip is what makes him *solid*.

## Why not depth maps

Tried, rejected. Estimating a depth map from the front view and displacing a mesh
gives real parallax within about ±20°, but beyond that his silhouette stretches
into ribbons, and it is guessing at a back it has never seen. Four real views are
better information and they came out clean.

## Coverage

Four views each cover ±45°, which is enough to walk around him. If a seam is
visible in practice, eight views is the same generation run twice with the
intermediate angles; nothing else changes.

## Seated poses

Same rule, more strongly: a seated body already has a committed orientation, so
locked yaw is mandatory, and the view set matters more because walking past a
seated man changes his profile a lot. Seated clips also anchor by hip height (see
`PLACEMENT-RULES.md` rule 3), not by feet.
