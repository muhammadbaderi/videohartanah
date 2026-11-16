# The map chapter (g-loc)

A real map that dives to the owner's pin, then draws a dotted line and a distance label to each nearby place
as the voice names it, with highway signs below. The camera move is baked to video (live tiles change between
renders); pins, lines and labels are live HTML placed on the same zoom curve, so they stay editable.

## 1. Coordinates

- The owner's link (`https://maps.app.goo.gl/...`) redirects to `https://maps.google.com/?q=<lat>,<lng>&...`:
  `curl -sS -o /dev/null -w "%{redirect_url}" "<link>"` and read `q=`.
- Nearby places from the listing (pick the 2-3 the voice names): Nominatim, one request a second, a generic
  User-Agent (never the owner's details):
  `curl -sS -H "User-Agent: videohartanah-map/1.0" "https://nominatim.openstreetmap.org/search?format=json&limit=3&countrycodes=my&viewbox=<w>,<n>,<e>,<s>&bounded=1&q=<name>"`.
  Malls are often under a shorter name ("Quayside Mall" not "Quayside Mall Rimbayu"). Distance labels use the
  owner's driving distances from the listing, not straight lines; say so in EDIT_NOTES.
- Overpass (road geometry) is blocked here, so highways are signs, not lines.

## 2. Bake (`scripts/<name>/map.json`, `bake_map.cjs`)

`map.json` holds the camera: `center` [lng, lat], `zstart` -> `zend` over `hold_t` seconds (ease in-out cubic),
then a slow `drift`; `dur` = the scene length (bake a little longer than `g-loc` will be); the places in `pois`.
Zoom is MapLibre's (512-px world): `zend` ~12.85 frames a ~6 km cluster on a 1080-wide frame.
Tiles: Esri World Dark Gray Canvas tinted blue (`tint` background under `raster_opacity` 0.7, contrast 0.35).

```bash
(cd /tmp && npm install maplibre-gl@5.24.0)          # jsdelivr/unpkg are blocked; load MapLibre from npm
export MAPLIBRE=/tmp/node_modules/maplibre-gl/dist
node scripts/<name>/bake_map.cjs --still             # one frame at the hold view -> .media-src/map_still.png: check framing
node scripts/<name>/bake_map.cjs                     # ~5 min for 9.5 s; writes <name>/assets/footage/map.mp4 + map_coords.json
```

Framing rules for portrait: keep every pin between y 300 and 1000 at the end of the drift (header pill at
y 196, highway signs at y 1062, captions at y 1188, nothing readable below 1330), and labels away from the
right edge (the app's action rail). Move `center` to shift the cluster; one degree of latitude is ~111 km and
there are ~10.6 m per pixel at zoom 12.85.

## 3. Wire it into g-loc.html

- Copy `map_coords.json`'s offsets into `POI` and `map.json`'s camera into `CAM` (same numbers, or the pins drift
  off their places during the zoom).
- Place each label on the side away from its connecting line (two-line card: name, then the distance in sky
  blue). Lines are computed from time in `place()`, which keeps them right when the timeline is seeked.
- The map shot in `edl.json` uses `"file": "assets/footage/map.mp4"` with `s0 = s1 = 1.0` (no push-in, or pins
  slide off).
- Credit the tiles on screen, small: "Peta: Esri, HERE, Garmin, © OpenStreetMap" with `data-layout-ignore`.
