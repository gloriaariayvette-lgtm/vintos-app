# Clip batch 01 — the first three

Built to `CAPTURE-STANDARD.md`. Generated through his own `avatar_stage.py`, not
raw `vintos-video.py`, because the stage path composes a **face-locked still**
first and carries the loop constraints (locked camera, stays in place, matching
first and last pose). Likeness consistency is the whole reason.

These three come first deliberately:

1. **`neutral-standing`** — belongs to no room. Plain background, anchors to any
   detected floor. This is the one that lets him appear in a cafe, a hotel room,
   her mother's kitchen. Everything else is polish on top of it.
2. **`sofa-forward`** — seated, facing out into the room, for when she is standing
   or across from him.
3. **`sofa-beside`** — seated, turned toward the empty seat on his left, for when
   she sits down next to him.

Two sofa clips because a seated body has a committed orientation and must not be
billboarded — see the standard.

## Parameters used

| | camera height | distance | seat |
|---|---|---|---|
| neutral-standing | 155 cm (her standing eye) | 2.2 m | — |
| sofa-forward | 155 cm | 2.2 m | 48.3 cm |
| sofa-beside | 121 cm (her eye seated on that sofa) | 1.1 m | 48.3 cm |

He sits at the end that appears left when facing the sofa, so she sits on his
left and he turns his head and shoulders to **his left** toward her.

## About the exterior photo

`refs/exterior-front-1.jpg` is the front of the house. It is **not** a reference
for an AR clip — AR clips need plain backgrounds so he can be cut out and placed
anywhere. It is useful for a *scene* clip of him arriving or on the steps, which is
a different kind of asset, and for eventually anchoring an outdoor location.
Recorded here so it does not get used for the wrong thing.
