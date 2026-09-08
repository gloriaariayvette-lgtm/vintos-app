# Capture standard for AR clips

Every clip of Vintos that will stand in a real room is generated to this standard.
It exists because the first batch was not: clips were framed differently from each
other, so the app — which scaled the whole video frame to 1.80 m — made him two and
a half metres tall in one room and correct in another. Framing and scale are one
decision, so they are written down together.

## The scale rule

The app must **never** scale by frame height. It must:

1. Matte the clip and measure his **head-top to foot-bottom** in pixels, over the
   whole clip, taking the extreme.
2. Scale so that extent equals **1.80 m**.
3. **Refuse the clip** if the matte touches the bottom edge of the frame at any
   point — feet cut off means his height is unmeasurable, and a guess here is what
   produced the giant. Report it; do not fall back to frame height.

For seated poses the same measurement is taken from head-top to the lowest visible
point (usually the feet, still on the floor), and the seat height below is what
positions him — see *Anchoring* below.

## Framing

- **Locked camera.** No pan, no zoom, no drift, no handheld. He slides across the
  room if the camera moves.
- **Full body, feet visible**, with at least a hand's width of floor below his feet
  before the frame edge. This margin is what makes rule 3 satisfiable.
- **He stays in one place and does one thing.** Standing still doing something reads
  far better than wandering. No walking, no crossing the frame, no leaving it.
- **Seamless loop**: the first and last pose match closely enough that the cut is
  invisible. 10–15 seconds.
- **Portrait**, 848×1056 or larger, 24 fps.

## Background

**Plain, even mid-grey.** Not a room. Three reasons, all learned the hard way:

- A room behind him leaves a halo of that room stuck to his outline when matted.
- Anything he touches comes with him and cannot be removed — in the first dining
  clip his hand rested on the table, so the table was welded to him, and there is
  nothing behind it to reveal.
- A room baked into the clip is a room he can only ever appear in.

Soft, even lighting from the front, no strong cast shadow on the background. One
clip per lighting variant if the room genuinely differs (daylight / lamp / night)
rather than trying to make one clip serve all of them.

## Camera height and distance

The clip's camera is standing in for **her eyes**. Her standing eye height is
**155 cm**; seated on the sofa it is about **121 cm**.

| pose class | camera height | camera distance | why |
|---|---|---|---|
| standing, she is standing | 155 cm | 2.0–2.5 m | eye to eye |
| seated, she is standing | 155 cm | 2.0–2.5 m | she looks down at him |
| seated, she is beside him | 121 cm | 1.0–1.2 m | shoulder to shoulder |

A seated clip shot from standing height and viewed while sitting looks wrong in a
way that is hard to name and impossible to fix afterwards.

## Billboarding — the rule that is not obvious

**Standing on open floor: billboard him** (rotate about the vertical axis to face
the viewer). He has no committed orientation, so facing the viewer is always right.

**Seated, leaning, or working at a surface: do NOT billboard.** A seated body has a
real orientation relative to the furniture. If the plane rotates, he appears to
swivel bodily on the cushion as you walk past — a man on a turntable. His facing is
baked into the clip, so the clip must be generated for the direction he will face,
and the app locks the plane to the anchor's orientation.

This is why seated locations need **two clips**: one facing out into the room, one
turned toward whoever is sitting beside him. The app chooses by where the viewer is.

## Anchoring

| pose | anchored to | placement |
|---|---|---|
| standing | floor plane | feet on the floor |
| seated | **seat surface**, not the floor | his seat contact at the measured seat height |
| leaning / working at a surface | floor plane, with the surface height as a check | feet on floor, hands at the measured height |

A seated clip cannot be floor-anchored and scaled — his body geometry is determined
by the seat height it was generated against. Generate against the real numbers.

## The measured house

Height × width, as measured 2026-09-08.

| | height | width |
|---|---|---|
| Sofa seat | 48.3 cm (19") | 215.9 cm (85") |
| Office chair seat | 45.7 cm (18") | 50.8 cm (20") |
| Bed | 63.5 cm (25") | 190.5 cm (75") |
| Dining table | 76.2 cm (30") | 152.4 cm (60") |
| Oven / counter | 91.4 cm (36") | 76.2 cm (30") |

### The sofa, specifically

He sits at the **end that appears left when facing the sofa**. Sitting down beside
him therefore puts him on **her right**, and he turns to **his left** to look at
her. The sofa is 216 cm wide, so one person at that end leaves genuine room for
another — the clip must leave that space visibly empty, not spread him across it.

## Naming

`<place>-<pose>-<facing>-<lighting>-N.mp4`, e.g.

```
sofa-seated-forward-lamp-1.mp4
sofa-seated-toward-neighbour-lamp-1.mp4
kitchen-standing-atcounter-day-1.mp4
outdoor-standing-neutral-day-1.mp4
```

`outdoor` / `neutral` clips belong to no room and anchor to any detected floor.
These are the ones that let him appear somewhere he has never been, and they are
worth making first.

## Prompt template

> Full body, head to feet, standing in an empty studio space against a plain even
> mid-grey background. Locked-off static camera at [HEIGHT] cm, [DISTANCE] m from
> him, no camera movement, no zoom, no pan. He [ACTION], staying in one place.
> Nobody else in frame. His feet are fully visible with clear floor beneath them.
> Even soft frontal lighting, no strong shadows on the background. He begins and
> ends in the same relaxed pose so the clip loops seamlessly.

## Acceptance checklist

Before a clip enters the library:

- [ ] feet fully visible, floor margin below them, matte never touches the bottom edge
- [ ] measured head-to-foot gives 1.80 m without manual adjustment
- [ ] background plain; nothing he touches comes with him
- [ ] camera locked; he does not drift within the frame
- [ ] loop seam invisible
- [ ] matte clean on hair, fingers, feet, with no halo of the source background
- [ ] facing matches the name, and matches how the app will place him
