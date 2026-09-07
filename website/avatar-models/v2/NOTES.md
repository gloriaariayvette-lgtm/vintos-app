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
