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
