# Current Phase 1: local avatar refinement

The latest direction supersedes the earlier service-generation plan: improve `vintos-barehands.glb` locally first. No Meshy, Tripo, Rodin, re-rigging, paid calls, or Blender were used.

## Review deliverables

- `vintos-refined.glb`: review model, based on `vintos-barehands.glb`, below the 30 MB phone budget.
- `tex/atlas-refined.png`: embedded GLB color atlas, in glTF image orientation. This is vertically flipped relative to the legacy standalone atlas PNG. Its hand tile retains the current GLB's decoded pixels exactly.
- `baseline/refined-comparison-{front,face,side}.png`: matched before/after renders. Individual `refined-before-*` and `refined-after-*` PNGs are also included.
- `baseline/refinement-verification.json`: geometry counts, retained skeleton/animation checks, weight checks, and sampled animation deformation results.
- `tools/refine_vintos.py` and `tools/verify_refinement.py`: reproducible local processing and verification. The existing CPU rasterizer now accepts an explicit texture and skips off-screen triangles.

## Changes and limits

Two curved edge subdivision passes add head vertices above y=0.985 m, with conforming transition triangles, interpolated UVs, and merged/normalized joint weights. The original 47,838 vertices retain their exact positions. The output has 138,696 vertices and 266,579 triangles. Body proportions, model coordinates, and the original hand graft are retained. This does not rescale the character: the input is approximately 1.166 m tall in its stored units.

Facial detail is transferred from `refs/vintos/vintos-1.jpg` through manually placed UV landmarks and feathered local image processing. Eyes and mouth are protected because the photo depicts lowered, closed eyes and a different expression. The hair texture is darkened along a manually traced region plus geometrically located cap islands; neutral shirt cloth is tinted olive. Existing scalp/hair geometry is retained; no new hair cards or separate eye meshes are claimed. This is a restrained texture refinement, not a reconstructed face or a claim of photoreal likeness. Pores/wrinkles remain color detail, not new normal/displacement maps. Hidden facial detail cannot be recovered from the single photo.

All 65 Mixamo-named nodes retain their exact names, transforms and hierarchy. The source skin references 52 of those nodes as weighted joints; the remainder remain in the hierarchy. The `mixamo.com` animation, inverse bind matrices, and original buffer data are retained. Four CPU skinning samples compare the input's original vertices against the output with zero position error. This verifies the embedded animation, not every external app clip or three-vrm compatibility. No Draco is used.

Lossless packing then removes unused buffer copies and splits draw groups for 16-bit triangle indices. Joint indices use 8-bit integers, which exactly represent the existing 0–51 values. Every triangle-corner attribute is compared exactly before/after packing; no quantization or image recompression is used. Run the deformation verifier before the packer, in the reproduction order below.

The source GLB, original FBX, hand textures and original atlas are untouched. Only v2 paths are changed. Final naming/VRM/FBX packaging remains pending the local likeness review; this candidate does not silently replace the served avatar.

## Reproduce this pass

```sh
python tools/refine_vintos.py
python tools/verify_refinement.py
python tools/pack_refinement.py
```

Requires the existing NumPy, SciPy and Pillow dependencies. Renders use the actual mesh/UVs with matched orthographic cameras, a CPU z-buffer, and diffuse lighting. The comparisons are not image-generation mockups.

---

# Earlier glove-removal record

# Phase 1 — glove removal

`source.fbx` is Vintos. `source-vintos-repo.fbx` is an older, different character and is ignored. The existing baseline completes Step 1. This change does not complete the avatar rebuild or approve the next phase.

## Delivered verification renders

- `baseline/gloves-off-front.png`: full frontal rest-pose view, including both hands.
- `baseline/gloves-off-hand.png`: close view of the hand on the positive-X side.

Rendered from the unchanged `source.fbx` vertices and polygon UVs with the new `tex/atlas.png` color map. The reproducible CPU rasterizer computes vertex normals, uses a depth buffer and bilinear texture sampling, and applies diffuse lighting. No Blender, GPU, browser renderer, skeleton edit, unit conversion, or geometry export was used. These verify the texture placement, not client rendering or animation behavior.

## Textures and preservation

`tex/atlas-original.png` is a byte-for-byte copy of the original PNG. The original atlas is RGB, so it has no alpha mask. A luminance threshold alone missed dark glove seams. The final mask limits the original luminance test to the glove UV component from `source.fbx`, fills enclosed holes, then dilates by two pixels at each target resolution. The independent oval island stays excluded. Saved masks are in `baseline/`.

The built-in ImageGen repaint (`tex/HAND-repaint-source.png`) uses HEAD.png as the skin-tone reference. Its generated outline is not used as the mask. Repaint colors are extended across its edge before being composited through the original mask. HAND.png retains 4096×4096 resolution; atlas.png retains 2048×2048. The repaint itself is upsampled, not native 4K detail.

Within the hand mask, metallic is 0 and roughness is 128. Outside each saved mask all decoded pixel bytes are identical to the original files. `HAND_normal.png` remains unchanged: this requested pass and its renders use the color atlas only. A later normal-mapped material should remove the old leather detail.

The FBX file, original UV coordinates, and Mixamo bone names are unchanged. `baseline/gloves-off-verification.json` records pixel checks and file hashes.

## Reproduce

Install the Python dependencies in `tools/requirements.txt`, then run from this folder:

```sh
python tools/gloves_off.py
python tools/render_gloves_off.py
```

The compositing script reads the original hand maps from the pinned pre-edit Git commit (the commit must be available locally); the original atlas is retained as a PNG. All output writes stay inside v2.
