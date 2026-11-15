"""Satellite maps for the map scene, from <project>/project.json "map":
  {"lat": .., "lon": .., "local_zoom": 16, "region_zoom": 12, "marks": [{"name": "Klang", "lat": .., "lon": ..}]}

Stitches Esri World Imagery tiles (+ the transport reference layer, and place labels on the
regional view) into two images at 2x, centred on the pin:
  video/assets/map/map-local.jpg   (1080 x 2200 CSS)  zoomed in on the project
  video/assets/map/map-region.jpg  (1080 x 2600 CSS)  the area around it, pin 200 px below centre
  video/assets/map/map.json        pin positions + mark positions (CSS px) for build.py
Imagery credit to show on screen: "Imej satelit: Esri, Maxar, Earthstar Geographics".
(server.arcgisonline.com is reachable from the cloud sessions; OSM and CARTO tiles are not.)

Usage: python3 -I .claude/skills/video-hartanah/scripts/make_map.py <project-dir>
"""
import io, json, math, os, sys, urllib.request
from PIL import Image

PROJ = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
M = json.load(open(os.path.join(PROJ, "project.json")))["map"]
LAT, LON = M["lat"], M["lon"]
OUT = os.path.join(PROJ, "video", "assets", "map")
os.makedirs(OUT, exist_ok=True)
BASE = "https://server.arcgisonline.com/ArcGIS/rest/services/"
LAYERS = ["World_Imagery", "Reference/World_Transportation", "Reference/World_Boundaries_and_Places"]

def px(lat, lon, z):
    n = 2 ** z * 256; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y

def get(layer, z, x, y):
    r = urllib.request.urlopen(urllib.request.Request(f"{BASE}{layer}/MapServer/tile/{z}/{y}/{x}", headers={"User-Agent": "curl/8"}), timeout=60)
    return Image.open(io.BytesIO(r.read())).convert("RGBA")

def build(zlook, name, cy_off, H, layers, W=2160):
    z = zlook + 1                      # fetch one level deeper -> 2x pixels
    cx, cy = px(LAT, LON, z); cy += cy_off
    x0, y0 = cx - W / 2, cy - H / 2
    img = Image.new("RGBA", (W, H))
    for layer in layers:
        lay = Image.new("RGBA", (W, H))
        for tx in range(int(x0 // 256), int((x0 + W) // 256) + 1):
            for ty in range(int(y0 // 256), int((y0 + H) // 256) + 1):
                lay.paste(get(layer, z, tx, ty), (int(tx * 256 - x0), int(ty * 256 - y0)))
        img = Image.alpha_composite(img, lay)
    img.convert("RGB").save(os.path.join(OUT, name), quality=80)

def css(lat, lon, zlook, cy_off, H):
    z = zlook + 1; cx, cy = px(LAT, LON, z); cy += cy_off; x, y = px(lat, lon, z)
    return [round((x - cx) / 2 + 540, 1), round((y - cy) / 2 + H / 4, 1)]

lz, rz = M.get("local_zoom", 16), M.get("region_zoom", 12)
build(lz, "map-local.jpg", 0, 4400, LAYERS[:2])
build(rz, "map-region.jpg", -400, 5200, LAYERS)
info = {"local": {"pin": css(LAT, LON, lz, 0, 4400), "h": 2200},
        "region": {"pin": css(LAT, LON, rz, -400, 5200), "h": 2600,
                   "marks": [{"name": m["name"], "css": css(m["lat"], m["lon"], rz, -400, 5200)} for m in M.get("marks", [])]}}
for m in info["region"]["marks"]:
    x, y = m["css"]
    if not (40 <= x <= 1040 and 0 <= y + 800 - info["region"]["pin"][1] <= 1900):
        print(f"WARNING: mark {m['name']} falls outside the frame at region zoom {rz} ({x}, {y}); drop it or lower region_zoom")
json.dump(info, open(os.path.join(OUT, "map.json"), "w"), indent=1)
print(json.dumps(info))
