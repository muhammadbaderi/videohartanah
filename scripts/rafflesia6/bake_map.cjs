// Bake the location-chapter map move to an all-intra MP4 (real CARTO / OpenStreetMap tiles),
// portrait 1080x1920, after the HyperFrames skill's bake-basemap.mjs (live tiles change between
// renders, so the camera move is frozen to video once).
//
//   MAPLIBRE=/path/to/node_modules/maplibre-gl/dist node scripts/rafflesia6/bake_map.cjs [--still]
//
// Writes rafflesia6/assets/footage/map.mp4 and scripts/rafflesia6/map_coords.json (each place's
// pixel offset from the frame centre at zoom `zend`). Zoom is a pure scale about the centre
// (Mercator, no pitch/bearing), so the composition places pins at centre + offset * 2^(zoomAt(t) - zend).
// --still bakes only the hold frame to map_still.png (for checking the framing).
const { chromium } = require("playwright");
const fs = require("fs"), path = require("path"), { spawnSync } = require("child_process");
const HERE = __dirname, ROOT = path.resolve(HERE, "..", "..");
const M = JSON.parse(fs.readFileSync(path.join(HERE, "map.json"), "utf8"));
const LIB = process.env.MAPLIBRE;
if (!LIB) throw new Error("set MAPLIBRE to maplibre-gl/dist (npm install maplibre-gl@5.24.0)");
const STILL = process.argv.includes("--still");
const OUT = path.join(ROOT, "rafflesia6", "assets", "footage");
const FR = path.join(process.env.FRAMES_DIR || path.join(ROOT, ".media-src", "map-frames"));
fs.mkdirSync(FR, { recursive: true });

const PAGE = `<!doctype html><html><head><style>*{margin:0}html,body{width:${M.width}px;height:${M.height}px;overflow:hidden;background:${M.tint}}
#map{position:absolute;inset:0}.maplibregl-control-container{display:none!important}</style></head><body><div id="map"></div></body></html>`;

const zoomAt = (t) => {
  const e = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  if (t <= M.hold_t) return M.zstart + (M.zend - M.zstart) * e(Math.max(0, t / M.hold_t));
  return M.zend + M.drift * (t - M.hold_t) / (M.dur - M.hold_t);
};

(async () => {
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const page = await browser.newPage({ viewport: { width: M.width, height: M.height }, deviceScaleFactor: 1 });
  await page.setContent(PAGE);
  await page.addStyleTag({ path: path.join(LIB, "maplibre-gl.css") });
  await page.addScriptTag({ path: path.join(LIB, "maplibre-gl.js") });
  await page.evaluate((M) => new Promise((res) => {
    window.map = new maplibregl.Map({ container: "map", interactive: false, attributionControl: false, fadeDuration: 0,
      preserveDrawingBuffer: true, maxTileCacheSize: 6000, center: M.center, zoom: M.zstart,
      canvasContextAttributes: { preserveDrawingBuffer: true },
      style: { version: 8, sources: { s: { type: "raster", tiles: [M.tiles], tileSize: 256, maxzoom: 16 } },
        layers: [{ id: "bg", type: "background", paint: { "background-color": M.tint } },
                 { id: "s", type: "raster", source: "s", paint: { "raster-opacity": M.raster_opacity, "raster-contrast": M.raster_contrast || 0, "raster-fade-duration": 0 } }] } });
    map.on("load", res);
    window.waitIdle = (ms) => new Promise((r) => { const t0 = performance.now();
      (function poll() { if (map.loaded() && map.areTilesLoaded()) { map.triggerRepaint(); requestAnimationFrame(() => requestAnimationFrame(() => r(false))); return; }
        if (performance.now() - t0 > ms) { r(true); return; } setTimeout(poll, 40); })(); });
  }), M);
  const N = STILL ? 1 : Math.round(M.fps * M.dur);
  let timeouts = 0;
  for (let i = 0; i < N; i++) {
    const t = STILL ? M.hold_t : i / M.fps;
    await page.evaluate(({ c, z }) => map.jumpTo({ center: c, zoom: z }), { c: M.center, z: zoomAt(t) });
    if (await page.evaluate(() => waitIdle(12000))) { timeouts++; console.warn("tile timeout at frame", i); }
    await page.screenshot({ path: STILL ? path.join(HERE, "..", "..", ".media-src", "map_still.png") : path.join(FR, `f${String(i).padStart(4, "0")}.png`) });
    if (i % 30 === 0) console.log(`frame ${i + 1}/${N}`);
  }
  // offsets at the hold zoom
  await page.evaluate(({ c, z }) => map.jumpTo({ center: c, zoom: z }), { c: M.center, z: M.zend });
  const coords = await page.evaluate((pois) => pois.map((p) => { const q = map.project([p.lng, p.lat]);
    return { id: p.id, name: p.name, dx: +(q.x - map.getCanvas().clientWidth / 2).toFixed(1), dy: +(q.y - map.getCanvas().clientHeight / 2).toFixed(1) }; }), M.pois);
  fs.writeFileSync(path.join(HERE, "map_coords.json"), JSON.stringify({ zend: M.zend, center_px: [M.width / 2, M.height / 2], pois: coords }, null, 1));
  console.log(JSON.stringify(coords));
  await browser.close();
  if (!STILL) {
    const ff = spawnSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(M.fps), "-i", path.join(FR, "f%04d.png"),
      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "1", "-crf", "16", "-movflags", "+faststart", path.join(OUT, "map.mp4")], { stdio: "inherit" });
    console.log(ff.status === 0 ? "encoded map.mp4" : "ffmpeg failed");
  }
  if (timeouts) { console.error(`${timeouts} frame(s) hit the tile timeout`); process.exitCode = 1; }
})();
