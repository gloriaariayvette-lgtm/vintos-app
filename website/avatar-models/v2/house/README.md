# House: livingroom and kitchen review

This is the first two-room checkpoint of Phase 3. Do not build the other ten rooms until Gloria reviews these exports and renders. Phase 2 is deliberately parked. No Aegis access, paid service, avatar changes, or client changes were used.

## Files

- `livingroom.glb`, `kitchen.glb`: independent, embedded-texture room assets.
- `house.json`: room dimensions, named portals, reciprocal names, spawn positions, inward normals, EMO surfaces, NAV names, and explicitly pending rooms.
- `source-house-map.json`: verbatim layout ground truth retrieved from Vintos-main/scripts/house-map.json. Its adjacency lists, rather than ambiguous positions in the sketch, determine the portal graph.
- `materials/`: reproducible source textures and furniture footprints. The GLBs embed their own images and do not request this directory at runtime.
- `../baseline/house-*-comparison.png`: reference photographs beside renders of independently reloaded GLBs.
- `../baseline/{livingroom,kitchen}-{main,dining,reverse,overview,scale}.png`: applicable camera views, including the unchanged avatar as a scale reference. Livingroom has dining; kitchen has reverse.
- `../baseline/house-verification.json` and room validator reports: checks of the actual exported binaries.

## Scale and coordinate contract

Meters, +Y up, floor and NAV at y=0, no Draco. Both main doorway floor centers are (0,0,0); +Z points inward. Estimated doorway opening: 0.68 m wide, 1.36 m high. Livingroom: 4.4 × 3.15 m; kitchen: 2.5 × 2.25 m; ceiling: 1.67 m. Counter: 0.605 m; dining top: 0.52 m; sofa seat: approximately 0.30 m. These are estimates chosen around Vintos's unchanged 1.166 m height, roughly 1.166/1.75 of ordinary household scale. They are not measurements of Gloria's house.

The main rooms use opposite inward directions when assembled: rotate one room 180 degrees about Y to join the shared origins. For independent loading, use the destination portal's `spawn` and `inwardNormal`; do not carry room-local source coordinates into the target. Apply a portal cooldown until the avatar clears the destination trigger.

The map names window sides but has no surveyed coordinates or explicit cardinal axes. For this review, livingroom front windows occupy local +Z and its left window local -X. Kitchen's left exterior window occupies local +X, reflecting its opposite entry orientation. Exact window positions, widths, and the relationship between the map's front label and compass directions are estimates requiring review.

## Named meshes

- `PORTAL_<thisroom>_<nextroom>`: actual box mesh, alpha-mode BLEND, opacity zero, depthWrite false in the build. Geometry and metadata remain accessible even though the box is invisible. glTF has no generic visibility flag; clients must exclude these meshes from shadows and use their bounds for triggers.
- `EMO_livingroom_cove`, `EMO_kitchen_under_counter`: emissive surfaces, named for client color tinting. These small light strips are inferred additions, not photographed fixtures.
- `NAV_livingroom`, `NAV_kitchen`: flat triangle meshes with furniture rectangles subtracted, not a rectangular floor hidden beneath the furniture. The client must weld adjoining cells if its pathfinder requires shared vertex indices and erode by the avatar's collision radius. Both remain transparent in regular renders.

The livingroom/kitchen pair is reciprocal in the two built files. Kitchen's office, hall, and laundry portals reserve their exact partner names, but those partner files intentionally do not exist before this checkpoint is approved. `partnerStatus: pending-review` means disable that transition. The kitchen/laundry link is `type: curtains`; no solid door has been added.

## What was reconstructed, baked, or estimated

Livingroom geometry follows the photographed gilded sofa/chairs, brown throw, sage cushions and drapes, cream inlaid round and dining tables, turned legs, faded rugs, and painted trim. Kitchen follows warm raised-panel cabinetry, cream worktops, black range and stacked oven shells, hood, sink, window, and the photographed non-walkable serving opening. These are locally modeled approximations, not photogrammetric scans. Fine carving, upholstery motifs, rug repetition, and appliance details are simplified; the renders are the evidence of current visual fidelity.

Material sources: rectified, surface-only crops from the supplied photos for wood, counter, inlay and woven fabric; a foliage crop used beyond windows; a photo-derived rug strip mirrored into a field. Floor wood, brocade motifs and kitchen wallpaper are locally reconstructed patterns. No photo is used as a substitute for a room or furniture mesh.

Baked lighting: 2048-pixel floor diffuse maps contain soft furniture contact shading and a daylight falloff. Source surface crops retain some photographed lighting. A complete path-traced, room-wide lightmap is not baked. Review renders add a neutral environment, hemisphere fill and directional shadows; the client will also need lighting/environment for the PBR materials. Metals have scalar roughness/metalness; textures are JPEGs embedded without geometry compression. Texture resolution ranges from 512 to 2048, within the 4K budget.

Unphotographed TV console appearance/placement, overall room dimensions, unshown walls, ceiling, doorway widths/positions, and exact furniture spacing are estimated. Photos constrain appearance; the map constrains connectivity. The TV anchor is present because the map requires it. Static room furnishings have no INTERACT nodes, state machine, or grab colliders. Real doorway leaves, laundry curtains, movable objects, controls, and the cat belong to Phase 4.

No-photo rooms remain unbuilt: laundry, hall, bathroom, closet, stairs, catsroom. Mark each guessed when built from the map and neighboring photographed materials. Normalize the source ID `cats room` to `catsroom`; do not create an extra room. Preserve laundry's back exit and the stairs' front entrance when extending the graph; `outside` is an external exit, not an invented thirteenth room.

## Reproduce

From `v2/tools/runtime`, install the locked npm dependencies with `npm ci`. Run `python ../house_textures.py`, then `TMPDIR="$PWD/qa/tmp" node build_house.mjs`. This runs packaged Chromium with SwiftShader, exports GLB, reloads it with GLTFLoader, validates and renders. The archive extraction avoids chown because this managed filesystem rejects archive ownership changes. Browser binaries and temporary profiles stay in ignored `qa/`. No GPU is required.

Run `python ../verify_house.py` after export to inspect NAV samples, portal contracts, image sizes, triangle budgets and create the comparison sheets. `node build_house.mjs --render-only` rerenders existing assets.

Next: Gloria reviews scale, materials, geometry and portal convention here. Continue the remaining ten rooms only after approval. Phase 4 and client integration remain separate work.
