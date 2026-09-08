# Action prompts

What he is doing in a clip, written down. Two batches have been generated and the
differences between them are the whole lesson.

## The suffix, always

```
Locked-off camera, no camera movement, no zoom. He stays exactly where he is and
keeps facing the SAME direction the whole time - he never turns toward the camera
and never walks. His mouth never forms words; he does not talk. He begins and
ends in the same pose so the clip loops seamlessly.
```

"Never turns toward the camera" is load-bearing. The multi-view illusion is that
he holds his orientation in the room; if he turns to face the lens mid-clip, the
side and back views stop meaning anything.

## Do not use `LOOP_SUFFIX` from avatar_stage.py

It appends *"natural breathing and weight shifts... a fond glance toward the
camera"* to every clip. Breathing is filler, and a fond glance is wrong in a view
where his back is turned. Call `atlas_generate` directly with the suffix above.

## Neutral standing — rejected

```
He stands at ease, weight settled on one leg. He folds his arms, looks off to one
side at something across the room, considers it, then lets his arms fall and
rolls his shoulders once.
```

Two failures, both from the wording:

- **"weight settled on one leg"** on a plain backdrop gave him one leg crossed
  over the other, as though leaning on something that is not there.
- **"folds his arms"** was read as hugging himself — arms high and tight, hands
  gripping his own upper arms. It reads as cold, not relaxed.

Clips: `neutral-{front,left,right,back}-idle-1.mp4`. Mechanism tests only.

## Neutral standing — corrected, not yet generated

```
He stands upright and squarely on both feet, feet slightly apart, both arms
hanging relaxed at his sides, unhurried and at ease. He slowly turns his head to
look at something across the room, considers it, then turns his head back. He
does NOT cross his legs, does NOT lean on anything, and does NOT fold his arms.
```

Naming the negatives matters. Removing "folds his arms" is not enough; it comes
back unless it is forbidden. Output: `neutral-*-idle-2.mp4`.

## Writing new ones

- Say what his **feet** are doing. Left unsaid, he leans on absent furniture.
- Say what his **arms** are doing, and forbid what you do not want.
- One action, not a sequence. Fifteen seconds holds about one idea.
- No breathing, no blinking, no "subtle movements" — filler words produce filler.
- For a located pose, the thing he is doing should belong to that place: at the
  counter he is doing something at the counter, not standing near it.
