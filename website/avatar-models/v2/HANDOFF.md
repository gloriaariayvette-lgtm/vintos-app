# Current checkpoint — revised livingroom and kitchen, awaiting Gloria

Phase 3 is active. Phase 1 is complete; Phase 2 is parked. Do not access Aegis or redo avatar, glove, hand or baseline work. Work only inside website/avatar-models/v2/ on astra/avatar-house.

Gloria rejected the original room pair (3fd3756): crude furniture and mirrored kitchen. Kitchen was rebuilt in 5a566be, followed by a livingroom furniture rebuild and refreshed two-room exports. Read house/README.md for the current geometry, scale, naming and known limits. It supersedes all earlier house layout/render claims.

Review: baseline/house-livingroom-comparison.png and baseline/house-kitchen-comparison.png. These use actual exported GLBs reloaded before rendering. Individual main/reverse/dining, overhead and avatar-scale PNGs sit alongside. baseline/house-verification.json records compatibility, NAV sampling and portal checks; kitchen-rebuild-verification.json checks actual object order against both kitchen photos and rejects reflected transforms. Technical checks do not establish visual fidelity.

Livingroom's old furniture has been replaced with a central-backed winged sofa, rounded chairs, puffed cushions, continuous draped throw and turned-leg tables. Gilt reliefs use actual photo contours with inferred depth; chair ornament and hidden left-wing details are approximations. Kitchen has corrected handedness and modeled panel/drawer/appliance/sink geometry. Both remain photo-based estimates, not scans, and still lack a complete room lightmap. Review the renders before claiming the requested fidelity has been reached.

STOP for Gloria's review before any of the other ten rooms. house.json marks both rooms rebuilt-awaiting-review. The shared portals exist and are reciprocal; built does not mean approved. Office, hall and laundry partner files are still pending. No Phase 4 doors, INTERACT state machine or cat was added. No paid services, avatar changes, motion work or client deployment occurred.

Reproduce from v2/tools/runtime with the commands in house/README.md. The builder supports both rooms and single-room flags, uses packaged Chromium/SwiftShader, exports and independently reloads GLBs, then renders. Source materials and geometry are preserved under v2. Ground truth is house/source-house-map.json. Six no-photo rooms must be marked guessed when eventually built.

The historical Phase 1/2 notes below are retained as provenance; their next-chat instructions are superseded by the current Phase 3 checkpoint above.

---

# Phase 1 complete — local refinement and verified exports

Branch: `astra/avatar-house`, repository `gloriaariayvette-lgtm/vintos-app`. Work only under `website/avatar-models/v2/`; never overwrite live assets or commit to eve.

## Delivered

- `vintos.glb`: final phone asset, about 12.4 MB; original embedded animation retained.
- `vintos.vrm`: final VRM 1.0, about 12.4 MB; 52 humanoid roles verified through the actual three-vrm loader.
- `source-v2.fbx`: final skinned, textured FBX in the preserved Mixamo rest/T-pose, about 11.3 MB. Embedded PNG; no animation takes. Use this for mocap.
- `baseline/v2-exports-{front,side,face}.png` and individual format renders compare independently reloaded exports.
- `baseline/exports-verification.json`, validator reports, and `NOTES.md` record verification and limitations.

All 65 original named Mixamo nodes remain present. The source FBX namespace `mixamorig:` is preserved; Three.js normalizes punctuation when loading, as with the original. Neither re-rigging nor paid services were used. No Blender was used. Local subdivision and texture work came from `vintos-barehands.glb` and `refs/vintos/vintos-1.jpg`. The finished hand graft was retained. Earlier baseline/glove/hand work must not be redone.

## Next chat: Phase 2 only

1. Connect to Aegis as `gloria@100.72.225.119`. Install `github.com/squall01337/mixamo-llm-mocap` per its README. Blender 5.1+, CUDA and approximately 8 GB VRAM. Aegis runs Linux under WSL, while the documented install is Windows. Report the install result before generating anything; report exact errors before workarounds.
2. Confirm `source-v2.fbx` rest/T-pose again in the pipeline importer. Generate the user's 24 individual 6–10 second locked-camera action videos, with T-pose at start and end, through the established house-video service. Disclose cost before any paid batch. The video service has not been identified or invoked in this chat.
3. After qa_clip.py passes, export each animation from the same Blender on Aegis as `clips/<name>.glb` (+Y up, no Draco), write clips.json with duration/loopability/planted feet, and deliver `baseline/clips-contact.mp4`.

Do not perform Phase 2 in the Phase 1 chat. Full action names, later 12-room house requirements, object conventions and cat requirements remain in the user's goal. House-map.json is the room/door ground truth. The cat must use an animal-rig service or rig pack, not this human mocap pipeline.

No client deployment has occurred. eve still loads `/models/default.vrm`; changing the client is a separate job. The packaged avatar retains its inherited height/proportions and has no new facial expression morphs; see NOTES.md for integration details.

## Current Phase 2 checkpoint: Step 1 blocked by network access

Phase 2 is now authorized, but this execution workspace cannot route SSH to Aegis. The first connection exited 255 with `ssh: connect to host 100.72.225.119 port 22: Network is unreachable`. No Aegis changes or generation occurred. See `mocap/INSTALL-STATUS.md` for the exact command, upstream-only documentation findings and resume requirements. Need a reachable execution connection and the user's path to the already-downloaded `SMPLX_NEUTRAL.npz`. Do not redo Phase 1; do not advance to rig profiling until installation is completed and reported.
