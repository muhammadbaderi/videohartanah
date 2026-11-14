"""Stitch Esri World Imagery tiles (+ transport and place-label reference layers)
into two 2160x3840 map images (1080x1920 CSS at 2x), centred on the project pin:
a local view (z16 look) and a regional view (z12 look).
Imagery: Esri, Maxar, Earthstar Geographics; labels: Esri."""
import math, os, io, urllib.request
from PIL import Image
LAT, LON = 2.919219, 101.301938
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video", "assets", "map")
BASE = "https://server.arcgisonline.com/ArcGIS/rest/services/"
LAYERS = ["World_Imagery", "Reference/World_Transportation", "Reference/World_Boundaries_and_Places"]
def px(lat, lon, z):
    n = 2 ** z * 256; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y
def get(layer, z, x, y):
    r = urllib.request.urlopen(urllib.request.Request(f"{BASE}{layer}/MapServer/tile/{z}/{y}/{x}", headers={"User-Agent": "curl/8"}))
    return Image.open(io.BytesIO(r.read())).convert("RGBA")
def build(zlook, name, cy_off=0, W=2160, H=3840, layers=LAYERS):
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
    print(name, "pin at css", round((cx - x0) / 2, 1), round((cy - cy_off - y0) / 2, 1))
import json
def css(lat, lon, zlook, cy_off, H):
    z = zlook + 1; cx, cy = px(LAT, LON, z); cy += cy_off; x, y = px(lat, lon, z)
    return [round((x - cx) / 2 + 540, 1), round((y - cy) / 2 + H / 4, 1)]
build(16, "map-local.jpg", H=4400, layers=LAYERS[:2])
build(12, "map-region.jpg", cy_off=-400, H=5200)
marks = {"Klang": (3.0438, 101.4456), "Pelabuhan Klang": (2.9996, 101.3928), "Westport": (2.935, 101.288)}
json.dump({"local": {"pin": css(LAT, LON, 16, 0, 4400), "h": 2200},
           "region": {"pin": css(LAT, LON, 12, -400, 5200), "h": 2600,
                      "marks": {k: css(a, b, 12, -400, 5200) for k, (a, b) in marks.items()}}},
          open(os.path.join(OUT, "map.json"), "w"), indent=1)
print(open(os.path.join(OUT, "map.json")).read())
