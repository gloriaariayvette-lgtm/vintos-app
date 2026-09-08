# The scan — Gloria's actual floor, measured

`house-scan.glb` is a phone scan of the real upper floor, remeshed adaptively at
100% / 8k. It is not a model of the house. It is the house.

| | |
|---|---|
| triangles | 313,337 |
| bounding box | 10.686 × 3.019 × 8.775 m |
| materials | 1, with two 8K JPEG textures |
| attributes | POSITION, TEXCOORD_0 — **no normals, no vertex colours** |
| structure | one mesh, one node — the whole floor is a single undivided surface |

## Why this matters more than it looks

**It is at real scale.** A 3.0 m ceiling and a ~10.7 × 8.8 m floor are a real
apartment. Every room built by hand so far is dimensioned against a 1.166 m Vintos,
giving 1.67 m ceilings and 1.36 m doorways — a dollhouse, roughly 65% of life size,
and that error is baked into `house.json` and both finished room GLBs. The scan
does not have that error. It can be used to *settle* the scale question rather than
argue it: measure a known doorway here and the correction factor falls out.

**It is the ground truth the photographs only gesture at.** Room proportions, wall
runs, ceiling height, where the openings actually are, how far the sofa really is
from the dining table — all of it is in this file and none of it is in a photo.

## Why it is not simply the answer

- **One undivided mesh.** There are no rooms in it, no objects, no separable
  furniture. Splitting it into the twelve rooms of `../source-house-map.json` is
  real work and has not been done.
- **Scan artefacts.** Phone scans hole out under tables, smear thin geometry, weld
  things that should be separate, and thicken edges. Expect the sofa and the chairs
  to be fused to the floor and to each other.
- **Lighting is baked into the texture.** The room's real illumination is painted
  into the 8K maps, so it will not respond to scene lights and will fight any
  lightmap put over it.
- **No normals.** They will be generated on load; on a remesh that usually reads
  soft and slightly melted unless they are recomputed with a sensible angle.
- **313k triangles for one floor.** Fine on a desktop, not obviously fine on the
  glasses. Decimation per room is likely, and should be measured, not assumed.

An earlier attempt to render this straight out of the box produced, in Gloria's
words, "an amorphous blob that used to be my house." That was a camera and
material-handling failure, not evidence about the scan. Do not repeat it, and do
not treat that outcome as a verdict on the asset.

## The open question

Two routes to twelve rooms, and this asset is the reason it is a real choice:

- **Model from photographs** (what has been done for livingroom and kitchen):
  clean, riggable, controllable geometry — and, so far, furniture that does not
  match the references and a scale that is wrong.
- **Segment the scan**: correct proportions and true spatial relationships for
  free, at the cost of artefacts, baked lighting, and no clean objects to
  manipulate.

The likeliest good answer is neither alone: take the shell, proportions and scale
from the scan, and model the furniture that has to be interactive. Nobody has
tested that, and it should be tested before ten more rooms are built either way.

## Companion files

- `../floorplan.png` — the plan Gloria drew: room positions, relative sizes, which
  wall each window is on, every door, and furniture anchors by colour. Legend in
  `../floorplan.md`.
- `../source-house-map.json` — rooms as nodes, doors as edges, verified by Gloria.
  Connectivity only; no metrics.

Between the three, the scan gives metric truth, the plan gives layout and intent,
and the map gives connectivity. They should agree. Where they do not, the scan wins
on dimensions and Gloria's plan wins on what a room is for.
