# Placement rules for VintosRoom

How a clip must be placed once it is in the app. These are not preferences; each
one comes from something that went visibly wrong.

## 1. Scale from the matte, never from the frame

Measure his **head-top to foot-bottom** in the matte, over the whole clip, and
scale that extent to **1.80 m**. Do not scale the video frame.

If the matte touches the bottom edge of the frame at any point, **refuse the clip**
and say so. Feet cut off means his height cannot be measured, and the guess that
replaced it produced a two-and-a-half-metre man standing in the kitchen.

## 2. The plane always faces the viewer. His FACING comes from the clip.

These are two different things and an earlier version of this document
conflated them, which was wrong.

- **The display plane** is a billboard carrying an image. It must **always**
  rotate about the vertical axis to face the viewer. If it does not, walking to
  his side turns it edge-on and he disappears into a line. Never lock it.
- **His apparent facing in the room** is not a transform at all. It is *which
  clip is playing*. He looks away from you because the back-view clip is
  playing, not because the plane has rotated away.

So "he does not flip to face me" does not mean freezing the plane. It means:
as the viewer moves, keep the plane facing her, and switch the clip to the view
that matches her new bearing. He stays put and stays oriented; what changes is
which side of him she is seeing.

For a single-view pose with no alternates, the plane still faces the viewer —
there is simply nothing better to show her from the side, and that is the
flatness the multi-view set exists to fix.

## 3. Seated clips anchor by hip height, not by feet

The seated clips are generated with **no visible furniture** — he is in a seated
posture against a plain backdrop, because the real sofa provides the seat. So do
not put his feet on the floor. Position him so his **seat contact lands at the
measured seat height** of the real furniture:

| | seat height |
|---|---|
| Sofa | 48.3 cm |
| Office chair | 45.7 cm |
| Bed | 63.5 cm |

Getting this wrong sinks him into the cushion or floats him above it, and no
uniform scale factor fixes it.

## 4. Multiple views, chosen by where she stands

A pose may ship as several clips — front, left, right, back — the same man in the
same clothes photographed from four sides. Pick the view whose facing is nearest
to the viewer's bearing from the anchor, and cross-fade when switching. Four views
covers +/-45 degrees each, which is enough to walk around him.

Do **not** mirror a clip to make a missing view. Mirroring flips his hair parting
and his face, and faces are asymmetric — a mirrored Vintos is a subtly different
man. It was tried and rejected.

## 5. Outdoors: place, do not persist

Plane detection works fine outdoors, so tap-to-place works. Saved world maps do
not relocalise reliably outdoors because the visual features change with light,
weather and season. Treat outdoor placement as session-only and do not present a
stale anchor as a recovered one.

`ARGeoAnchor` covers 50+ US cities but its localisation imagery comes from public
streets and roads, so it is absent in gated or pedestrian-only areas even inside a
supported city. Call `ARGeoTrackingConfiguration.checkAvailability` at her actual
address and report the real answer rather than assuming either way.

## 6. Footwear follows the room

Barefoot clips are indoor clips. Outdoor poses need shoes. Treat footwear as part
of the pose's identity, not a detail — a barefoot man on a pavement reads as wrong
immediately.

## 7. The glasses are binocular

The Air3 renders separately to each eye, so a flat billboard still sits at a real
distance — the eyes converge on him as they would on a person two metres away.
Stereo places him convincingly; it does not round him out. He stays flat, and the
answer to that is more views (rule 4), not more disparity.
