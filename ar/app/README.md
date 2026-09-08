# Drop-in for VintosRoom

`MultiViewFigure.swift` implements `../MULTIVIEW.md`: locked yaw, view chosen by
the viewer's bearing, hysteresis and cross-fade.

It is written against the app as described in its own README (packed colour+matte
clips through `PackedVideo.metal`, RealityKit, `CustomMaterial`). Two lines will
need pointing at the real symbols in that project — the shader lookup and the
placeholder texture — because this was written without the project open. Nothing
else should need changing.

## Wiring

1. Where the single billboarded plane is built today, build a `MultiViewFigure`
   instead and add `figure.entity` to the anchor.
2. **Delete the billboard update for these entities.** The yaw is fixed
   deliberately; leaving the billboard in defeats the entire feature.
3. Subscribe to `SceneEvents.Update` and call
   `figure.update(cameraWorldPosition:now:)` with the ARView camera's world
   position.
4. Add a "set facing" step to placement: after tapping where his feet go, the
   user aims the phone the way he should be looking and confirms. Pass that
   horizontal direction in as `facing`.
5. Set `MultiViewFigure.bearingSign` **by measurement**: stand to his left and
   check whether the left-side clip appears. If it does not, flip the sign and
   leave a comment saying it was measured on device.

## The view set

```swift
let views = [
    FigureView(url: front, bearing: 0),
    FigureView(url: left,  bearing: -.pi / 2),
    FigureView(url: right, bearing:  .pi / 2),
    FigureView(url: back,  bearing:  .pi),
]
```

A missing view is fine — `nearestView` simply picks the closest one that exists,
so three views degrade gracefully to wider coverage each rather than failing.

## Size

`size.y` is his height, 1.80 m. `size.x` is `1.80 * (mattWidth / mattHeight)`
using the **matte's** measured head-to-foot extent, never the video frame — see
`../PLACEMENT-RULES.md` rule 1. The side and back clips arrive at twice the
resolution of the front one and must still come out the same height; measuring
the matte is what makes that automatic.
