# The multi-view clips

Four 15-second loops of the same man, same clothes, same lighting, same camera
distance and framing, on a plain mid-grey backdrop — differing only in which way
he is turned. Generated through nano-banana with two references (his hero for the
face, a finished front still for the outfit and framing), then animated.

| file | he faces |
|---|---|
| `neutral/neutral-front-idle-1.mp4` | the camera |
| `neutral/neutral-left-idle-1.mp4` | the left edge of frame |
| `neutral/neutral-right-idle-1.mp4` | the right edge of frame |
| `neutral/neutral-back-idle-1.mp4` | away, back to camera |

848x1056, 24 fps, h264. `frames/` holds one reference frame from each, for
inspection or reconstruction experiments — the clips are authoritative.

`neutral/neutral-front.packed.mp4` is the front view already matted and packed
(colour left, greyscale matte right) as VintosRoom's fallback format expects. The
other three are unpacked; the tooling for that is in the app project.

**These are committed here because the ad-hoc HTTP server on Aegis was a one-off
that Gloria ran by hand and is long gone.** Anything the app or a reconstruction
experiment needs should live in the repository, not behind a command she has to
run again.

## Known limitation of this particular set

The action is wrong, and Gloria said so: he crosses one leg over the other as
though leaning on something that is not there, and mid-clip he folds his arms in
a way that reads as hugging himself. Both came from the prompt — "weight settled
on one leg" and "folds his arms" — not from the model.

The corrected action prompt (both feet flat, no leaning, no folded arms, only a
slow head turn) is written down but has not been generated. Use this set to test
the *mechanism*; do not treat the pose as final.
