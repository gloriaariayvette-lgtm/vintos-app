# The floor plan Gloria drew

`floorplan.png`. Hand-drawn, and the only source that says where rooms sit relative
to each other, how big they are relative to each other, which wall each window is
on, and where the furniture stands. `source-house-map.json` gives connectivity;
this gives layout.

Bottom edge of the drawing is the **front of the house**. Entry is marked
"Enter here" at the front, up the stairs.

## Legend

| colour | what it marks |
|---|---|
| **pink** | windows |
| **green** | doors |
| **dark blue** | the dining room table |
| **yellow stars** | sofa and chairs |
| **light purple** | the TV |
| **light blue** | the bed |
| **dark purple** | the desk |
| **orange** | kitchen countertops |

## Rooms as drawn

Top band: **livingroom**, running the full width, windows along the top and upper
left, sofa and chairs to the right, TV on the right wall, dining table standing
alone at the far left.

Middle: **kitchen** at the left with countertops in an L against the left wall;
**laundry and back exit** at the right with the back door on the right wall;
**bedroom** below the laundry with the bed against its left side; **office** below
the kitchen with the desk against the left wall; **hall** as the narrow spine
between them; **closet** off the hall; **bathroom** to the right of it.

Bottom band: **vanity** at the left, **stairs to front entrance** in the middle,
**cats' room** to the right, **balcony** across the bottom left.

## How to use it

Take proportions and window/door placement from here, and metric dimensions from
`scan/house-scan.glb`. The drawing is not to scale; the scan is. Where the two
disagree about which wall something is on, the drawing is the intent and should
be checked against the room photographs in `../refs/rooms/` before overriding it.
