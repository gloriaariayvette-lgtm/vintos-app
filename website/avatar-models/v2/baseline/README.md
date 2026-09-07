# Baseline renders (headless three.js r160, FBXLoader, software WebGL)

served-*.png   source.fbx            -> THIS is Vintos as the app serves him today. Mixamo rig (65 bones, 1 skin), 32.7k tris,
                                        height 1.17 units, no textures inside the file, no vertex normals (rendered with computed normals, clay shading).
repo-*.png     source-vintos-repo.fbx -> a DIFFERENT character: armored sci-fi body with a faceless helmet (materials Ch44_Body),
                                        46k tris, 189.8 units tall, 10 embedded textures. Not the man in refs/vintos/vintos-1.jpg.

Use source.fbx as the Phase 1 baseline. Do not build on source-vintos-repo.fbx.
