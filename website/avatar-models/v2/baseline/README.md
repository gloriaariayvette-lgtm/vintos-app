# Baseline renders (headless three.js r160, FBXLoader, software WebGL)

served-*.png   source.fbx            -> THIS is Vintos as the app serves him today. Mixamo rig (65 bones, 1 skin), 32.7k tris,
                                        height 1.17 units, no textures inside the file, no vertex normals (rendered with computed normals, clay shading).
repo-*.png     source-vintos-repo.fbx -> a DIFFERENT character: armored sci-fi body with a faceless helmet (materials Ch44_Body),
                                        46k tris, 189.8 units tall, 10 embedded textures. Not the man in refs/vintos/vintos-1.jpg.

Use source.fbx as the Phase 1 baseline. Do not build on source-vintos-repo.fbx.

textured-*.png  source.fbx with tex/atlas.png applied as the color map (single material, one UV set). This is how he looks in the app.
                The gloves are texture, not separate geometry: the hand UV island is the gray leather region in the top-right quarter
                of atlas.png (HAND.png and its metallic/normal/roughness maps are the full-res source of that island).

barehands-*.png  vintos-barehands.glb: his mesh with the two glove pieces deleted and real hands transplanted from default.glb
                 (the unclothed base mesh he was built on). Hands are cut at the wrist, sized to pass through the sleeve cuff,
                 seated just inside the cuff mouth, and skinned by copying weights from the nearest glove vertices so his
                 existing Mixamo rig and every animation clip still drive them. Skin comes from a tile painted into the empty
                 bottom-right of tex/atlas-barehands.png (atlas-original + tile; nothing else touched). Built by
                 tools/hand_transplant.html + run_hand_transplant.js (three.js, headless Chromium, no Blender).
                 NOTE: the phone app loads character.fbx; this file is GLB. Swapping it in needs a GLTFLoader line in the app.
