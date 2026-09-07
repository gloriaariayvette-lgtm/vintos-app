# Phase 1 handoff — local refinement review

Branch: `astra/avatar-house` in `gloriaariayvette-lgtm/vintos-app`. All writes remain under `website/avatar-models/v2/`. Never touch live assets.

## Current state

- Baseline, glove removal and anatomical hand graft were already complete; do not redo them.
- `vintos-barehands.glb` remains the untouched source/proportion/rig reference.
- `vintos-refined.glb` is the new local review result: two head subdivision passes, selectively transferred face detail from the reference, darker hair and olive cloth tint. No generation or re-rigging; no money spent.
- Review `baseline/refined-comparison-face.png`, `refined-comparison-front.png`, and `refined-comparison-side.png`. Before and after are actual CPU model renders under identical conditions.
- `tex/atlas-refined.png` is in embedded/glTF orientation, vertically flipped from the legacy standalone PNG convention. The completed hand tile remains pixel-identical to the source GLB.
- All 65 named Mixamo bones and the embedded animation are preserved. Details and sampled deformation checks are in `baseline/refinement-verification.json` and `NOTES.md`.

## Pending

The local result is awaiting likeness review. Phase 1 is not declared finished. Do not launch paid generation based merely on this handoff. If the local result is accepted, finish the agreed GLB/VRM 1.0/FBX packaging and verification using the preserved rig, without re-rigging. Current review files are not yet a verified VRM or updated FBX; `source.fbx` remains original.

If local refinement proves insufficient, the user permits Tripo or Rodin through their HTTP API, not a web canvas. Establish and disclose the actual cost before any paid call. No API generation has been attempted.

Do not start mocap/house/cat in this chat. Each later phase gets its own chat. Aegis SSH is `gloria@100.72.225.119`; the mocap install must be reported before generation. See the user's task for the full remaining phase requirements.
