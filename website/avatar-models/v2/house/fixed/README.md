# livingroom-welded.glb

Astra's livingroom.glb with the furniture repaired, not rebuilt.

Each piece was a kit of separate meshes sitting adjacent but never joined, so
normals broke at every junction and nothing shaded across a joint — that is what
read as "disjointed". Per piece the gilt parts were joined into ONE mesh and the
upholstery into another, welded at 9 mm (frame) and 6 mm (upholstery) so
near-touching parts fuse, normals recalculated, smooth-shaded across the joins.

    left armchair   23 parts -> frame 4146 verts + upholstery 2336 verts
    right armchair  23 parts -> frame 4145 verts + upholstery 2346 verts
    gilded sofa     33 parts -> frame 4849 verts + upholstery 12466 verts

Still wrong and NOT fixed by welding, because these are placement errors:
the back oval floats above the seat instead of meeting the rail; the arm front
attaches to nothing; the seat is a slab; the crest reads as a strip of teeth.

Rebuild with tools/fix_furniture.py. Render with tools/render_chair.py
(Blender/Cycles, isolates one armchair).
