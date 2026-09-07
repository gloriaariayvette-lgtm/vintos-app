# Phase 3: revised livingroom and kitchen for review

Gloria rejected the original pair in commit 3fd3756 for crude furniture and a mirrored kitchen. Both room models have now been revised. This supersedes the original geometry and orientation notes; it is not approval. STOP before building the other ten rooms.

## Review files

- `livingroom.glb`, `kitchen.glb`: independent room assets with embedded textures.
- `../baseline/house-livingroom-comparison.png`, `../baseline/house-kitchen-comparison.png`: source photos beside actual independently reloaded GLB renders.
- Individual `livingroom-{main,dining,overview,scale}.png` and `kitchen-{main,reverse,overview,scale}.png` in baseline: detail, plan and unchanged-avatar scale views.
- `house.json`: dimensions, portals, reciprocal names, spawn positions, inward normals, EMO surfaces, NAV names and pending rooms.
- `source-house-map.json`: preserved layout ground truth from Vintos-main/scripts/house-map.json.
- `../baseline/house-verification.json`: actual exported binary checks, sizes and triangle counts. Room validator reports and `kitchen-rebuild-verification.json` record compatibility and handedness checks. These checks do not establish visual fidelity.

## Kitchen correction

Photo 1, left to right: stacked ovens, four-drawer stack, range/hood, corner, sink/window. Local X decreases in that order when viewed toward the range wall. The sink window is on local -X. Photo 2: countertop oven to the left of the coffee machine, followed by the serving opening. Actual exported anchor transforms are checked against both orders. The old +X-window convention was wrong.

The new mesh has arched cabinet panels with extruded beveled rebates, frames, hinges and pulls, horizontal drawer rows, oven tower, appliance fascias and raised handles, range/cooktop, folded hood, cabinet carcasses, inset double sink, dishwasher and countertop-appliance shells. It is newly modeled geometry. Appliance fascia photos cover modeled surfaces; they do not replace entire appliances. Static cabinet details carry no Phase 4 state machine.

## Livingroom correction

The old seating/table groups were removed. The sofa has a tall central embroidered back, open carved wings, curved upholstered sides, cabriole legs, puffed cushions with edge seams, and a continuous draped brown throw. Chairs have rounded padded backs and oval gilt frames. Coffee and dining tables have modeled edges/aprons and turned legs. The side table has slender curved brass legs.

The visible sofa crest and wing were segmented from the actual photo, then made into solid shallow relief geometry with front, back and edge walls. Their depth is inferred, not scanned. The left wing is inferred symmetrically from the photographed right wing. Chair ornament adapts the photographed sofa crest around the oval chair frame; it is an approximation. Gilt arm/leg details and textile relief remain simplified. Seating embroidery, brocade, cushions, throw and inlay use locally processed photo crops and normal maps. Repeating photo crops and inferred hidden surfaces remain visible limitations. This is still a modeled reconstruction, not a claim of photoreal equivalence to the photos.

## Scale, portals and navigation

Meters, +Y up, floor/NAV at y=0, no Draco. Each main doorway floor center is (0,0,0), local +Z inward. Doorway is 0.68 m wide and 1.36 m high. Livingroom is estimated at 4.4 × 3.15 m; kitchen at 3.4 × 2.65 m; ceiling 1.67 m. Kitchen counter is 0.609 m; dining top 0.54 m including the inlay surface. Vintos remains 1.166 m tall. These are scaled estimates, not measurements of Gloria's house.

Livingroom window sides are local +Z and -X; kitchen window is local -X. The map has no metric survey or explicit compass axes. Unshown walls, TV appearance/placement, ceiling, opening coordinates and furniture spacing are estimated. Photos constrain appearance and the map constrains connectivity.

- `PORTAL_<thisroom>_<nextroom>` is an actual transparent box (alpha-mode BLEND, opacity zero). Use geometry bounds for triggers and exclude it from shadows.
- `EMO_livingroom_cove` and `EMO_kitchen_under_hood` are emissive surfaces for client tinting. These strips are inferred lighting additions.
- `NAV_livingroom` and `NAV_kitchen` are flat triangle meshes with furniture/cabinet footprint holes. Weld adjacent cells and erode by the avatar's collision radius if required by the client pathfinder.

The livingroom/kitchen portal names are reciprocal in both files. `partnerStatus: built` describes presence, not approval. All transitions involving these unapproved rooms should remain disabled. Kitchen's office, hall and laundry partners are `pending-review`: their files intentionally do not exist yet. The laundry connection is `type: curtains`. The serving opening is not an extra walkable portal. Separate room loading does not currently show the adjacent room through that opening.

For independent room loading, use the destination portal's `spawn` and `inwardNormal` and a re-entry cooldown until clear. Do not copy source-room coordinates to the destination. To assemble the shared main origins physically, rotate one room 180 degrees around Y.

## Materials and lighting

`materials/` contains the original shell/floor/rug sources; `kitchen-materials/` and `livingroom-materials/` contain replacement surface sources and relief geometry. GLBs embed their own images and do not request these folders at runtime. Source scripts are `../tools/house_textures.py`, `kitchen_materials.py` and `livingroom_materials.py`.

Floor textures contain soft furniture contact shading and daylight falloff. Kitchen has warm diffuse range-wall shading. Photo crops retain some captured lighting. A full path-traced room lightmap is NOT baked. The preview adds a neutral environment, hemisphere fill and directional shadows; clients still need PBR lighting. Normal-mapped geometry exports MikkTSpace tangents; identical geometry is shared without Draco. All embedded textures are within 4K.

## Reproduce

From `../tools/runtime`, use the locked npm dependencies, then:

```sh
python ../kitchen_materials.py
python ../livingroom_materials.py
TMPDIR="$PWD/qa/tmp" node build_house.mjs
python ../verify_house.py
python ../verify_kitchen_revision.py
```

`--livingroom-only` or `--kitchen-only` rebuilds one room and merges the manifest; `--render-only` renders existing exports. Packaged Chromium uses SwiftShader without a GPU. Temporary browser files stay in ignored `qa/`. No Blender, Aegis, paid service or client change was used.

## After review

Continue only after Gloria approves this pair: laundry, office, hall, bedroom, bathroom, closet, vanity, stairs, catsroom and balcony. Laundry, hall, bathroom, closet, stairs and catsroom have no photo and must be marked guessed. Normalize source ID `cats room` to `catsroom`. Preserve the laundry back exit and stairs front entrance; `outside` is an external exit, not a thirteenth room. Real doorway leaves, curtain states, INTERACT objects, controls and cat belong to Phase 4. Phase 2 remains parked.
