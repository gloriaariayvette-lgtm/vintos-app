# Phase 2 — Step 1 blocked before installation

Read HANDOFF.md and NOTES.md from astra/avatar-house before attempting access. Phase 1 assets remain complete and unchanged.

## Exact access result

Command:

```sh
ssh -o BatchMode=yes -o ConnectTimeout=12 gloria@100.72.225.119 'cat /mnt/c/mocap/docs/INSTALL.md; cat /mnt/c/mocap/docs/PIPELINE.md'
```

Exit code 255:

```text
ssh: connect to host 100.72.225.119 port 22: Network is unreachable
```

No remote connection was established. This is a route failure from the execution workspace, not evidence that Aegis is offline or that its credentials or software are wrong. No alternate callable SSH/remote-shell connector was available.

No Aegis files, interpreters, packages, originals, clips or Blender settings were modified. No generation, rig-profile build or mocap was run. There is no new render to deliver at this blocked install checkpoint.

## Read-only upstream findings

Because Aegis was unreachable, read the current upstream docs through GitHub. These are not verified to match the existing C:\mocap checkout:

- https://api.github.com/repos/squall01337/mixamo-llm-mocap/contents/docs/INSTALL.md (resolved through the repository contents API/default branch)
- https://api.github.com/repos/squall01337/mixamo-llm-mocap/contents/docs/PIPELINE.md (same)

INSTALL.md describes GVHMR under tools/GVHMR, a dedicated Python 3.10 venv, and a Windows Scripts/python.exe entry point. Its older torch/CUDA/pytorch3d pins must not be blindly applied to the user's verified sm_120 Blackwell setup. Use isolated venvs and the supplied cu128 requirement; never change WSL system Python or torch.

Four checkpoint downloads total approximately 5.3 GB: GVHMR, YOLO, ViTPose and HMR2. The SMPL-X file belongs at tools/GVHMR/inputs/checkpoints/body_models/smplx/SMPLX_NEUTRAL.npz. The user must provide its already-downloaded source path; do not redownload or accept a license on their behalf.

The guide identifies Blender 5.1+ as an add-on requirement. Follow the user's instruction to assess the existing Blender 5.0.1 first; report a concrete failure before any side-by-side 5.2 installation. No compatibility test has occurred yet.

The documented UI path is Edit > Preferences > System > Network > Allow Online Access. The official Blender Lab MCP add-on is installed by dragging its install link into Blender twice (repository, then extension), or by Install from Disk. Its bridge is localhost:9876. Verify this against the actual installed Blender/add-on before requesting UI steps.

PIPELINE.md requests approximately one second of T-pose at both video ends. Its action-spec section calls rest_blend_start optional and rest_blend_end required; its QA checks final rest hand error. rig_profile.json measures character proportions. The docs do not establish that this profile removes the video-bookend requirement. Inspect the local code and validate existing footage at Step 3 before concluding whether a generated test plate is necessary. No new video has been commissioned.

## Required to resume Step 1

1. An execution connection with a route to gloria@100.72.225.119. The current workspace cannot reach that private address.
2. The path to the already-downloaded SMPLX_NEUTRAL.npz.

Then read /mnt/c/mocap/docs/INSTALL.md and PIPELINE.md on Aegis, inspect the isolated GVHMR environment/add-on state, and complete installation. Keep work on C: and use the specified venvs. Read ~/Vintos/bin/vintos-video.py before invoking it and never print XAI_API_KEY. Copy the eight existing plates without modifying originals, inspect with ffprobe, and measure background camera motion before calling them static.

Stop with the install result before Step 2. Stop after the rig profile for review. Stop after one approved existing-footage test before a batch. No downstream checkpoint has been passed.
