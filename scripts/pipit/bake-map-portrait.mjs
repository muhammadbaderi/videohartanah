// Portrait (1080x1920) variant of hyperframes' bake-basemap.mjs for one shot:
// hold on the site, then pull back (zoom out) while the site glides to a target screen point,
// then hold on the region. MapLibre is inlined from node_modules (no CDN), tiles = Esri World Imagery.
// Writes <OUT>/<NAME>.mp4 (all-intra) and <OUT>/<NAME>-points.json (screen px of POINTS at the hold).
import { join, dirname } from "node:path";
import { mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const here = dirname(fileURLToPath(import.meta.url));
const W = 1080, H = 1920;
const NAME = process.env.NAME || "map";
const OUT = process.env.OUT || process.cwd();
const SITE = process.env.SITE.split(",").map(Number); // lng,lat
const TARGET = (process.env.TARGET || `${W / 2},${H / 2}`).split(",").map(Number); // site screen px at the hold
const ZSTART = +process.env.ZSTART, ZEND = +process.env.ZEND;
const FPS = +(process.env.FPS || 30), DUR = +(process.env.DUR || 6);
const PRE = +(process.env.PRE || 0.1), HOLD = +(process.env.HOLD || 0.6);
const POINTS = JSON.parse(process.env.POINTS || "{}"); // {name:[lng,lat]}
const N = Math.round(FPS * DUR);
const framesDir = join(OUT, "frames-" + NAME);
mkdirSync(framesDir, { recursive: true });

const mlJs = readFileSync(join(here, "node_modules/maplibre-gl/dist/maplibre-gl.js"), "utf8");
const mlCss = readFileSync(join(here, "node_modules/maplibre-gl/dist/maplibre-gl.css"), "utf8");
const TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

const PAGE = `<!doctype html><html><head><meta charset="utf-8"><style>${mlCss}</style>
<style>*{margin:0}html,body{width:${W}px;height:${H}px;overflow:hidden;background:#05070d}#map{position:absolute;inset:0;width:${W}px;height:${H}px}.maplibregl-control-container{display:none!important}</style>
<script>${mlJs}</script></head><body><div id="map"></div><script>
var SITE=${JSON.stringify(SITE)}, TARGET=${JSON.stringify(TARGET)}, ZSTART=${ZSTART}, ZEND=${ZEND}, PRE=${PRE}, HOLD=${HOLD};
var W=${W}, H=${H}, POINTS=${JSON.stringify(POINTS)};
var map=new maplibregl.Map({container:"map",style:{version:8,
  sources:{s:{type:"raster",tiles:[${JSON.stringify(TILES)}],tileSize:256,maxzoom:19}},
  layers:[{id:"bg",type:"background",paint:{"background-color":"#05070d"}},{id:"s",type:"raster",source:"s"}]},
  center:SITE,zoom:ZSTART,interactive:false,attributionControl:false,fadeDuration:0,preserveDrawingBuffer:true,maxTileCacheSize:6000,
  canvasContextAttributes:{preserveDrawingBuffer:true}});
function ease(x){return x<0.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;}
function seg(p,a,b){return b<=a?1:Math.min(1,Math.max(0,(p-a)/(b-a)));}
function wx(lng,z){return (lng+180)/360*512*Math.pow(2,z);}
function wy(lat,z){var r=lat*Math.PI/180;return (1-Math.asinh(Math.tan(r))/Math.PI)/2*512*Math.pow(2,z);}
function lngOf(x,z){return x/(512*Math.pow(2,z))*360-180;}
function latOf(y,z){var n=Math.PI*(1-2*y/(512*Math.pow(2,z)));return Math.atan(Math.sinh(n))*180/Math.PI;}
function camAt(p){
  var t=ease(seg(p,PRE,HOLD));
  var z=ZSTART+(ZEND-ZSTART)*t;
  var sx=W/2+(TARGET[0]-W/2)*t, sy=H/2+(TARGET[1]-H/2)*t; // site's screen point
  var cx=wx(SITE[0],z)-(sx-W/2), cy=wy(SITE[1],z)-(sy-H/2);
  return {center:[lngOf(cx,z),latOf(cy,z)],zoom:z};
}
window.__ready=new Promise(function(res){map.on("load",function(){res();});});
window.__setCam=function(p){map.jumpTo(camAt(p));};
window.__waitIdle=function(ms){return new Promise(function(res){var t0=performance.now();
  (function poll(){if(map.loaded()&&map.areTilesLoaded()){map.triggerRepaint();requestAnimationFrame(function(){requestAnimationFrame(function(){res(false);});});return;}
    if(performance.now()-t0>(ms||9000)){res(!map.areTilesLoaded());return;}setTimeout(poll,40);})();});};
window.__project=function(){var o={};Object.keys(POINTS).forEach(function(k){var p=map.project(POINTS[k]);o[k]={x:+p.x.toFixed(1),y:+p.y.toFixed(1)};});
  var s=map.project(SITE);o.__site={x:+s.x.toFixed(1),y:+s.y.toFixed(1)};o.__view={center:map.getCenter(),zoom:map.getZoom()};return o;};
</script></body></html>`;

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME,
  headless: true,
  args: ["--no-sandbox", "--hide-scrollbars", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--enable-webgl", `--window-size=${W},${H}`],
});
try {
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  await page.setContent(PAGE, { waitUntil: "load" });
  await page.evaluate(() => window.__ready);
  console.log(`[${NAME}] ready; ${N} frames, z ${ZSTART}->${ZEND}`);
  const t0 = Date.now();
  let pts = null, timeouts = 0;
  for (let i = 0; i < N; i++) {
    const p = N === 1 ? 1 : i / (N - 1);
    await page.evaluate((pp) => window.__setCam(pp), p);
    if (await page.evaluate((ms) => window.__waitIdle(ms), 15000)) { timeouts++; console.warn(`  timeout at frame ${i}`); }
    await page.screenshot({ path: join(framesDir, `f${String(i).padStart(4, "0")}.png`), clip: { x: 0, y: 0, width: W, height: H }, optimizeForSpeed: true });
    if (p >= HOLD && !pts) pts = await page.evaluate(() => window.__project());
    if (i % 20 === 0 || i === N - 1) console.log(`  ${i + 1}/${N} · ${((Date.now() - t0) / 1000 / (i + 1)).toFixed(2)} s/frame`);
  }
  const mp4 = join(OUT, NAME + ".mp4");
  const ff = spawnSync("ffmpeg", ["-y", "-v", "error", "-framerate", String(FPS), "-i", join(framesDir, "f%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "1", "-crf", "16", "-movflags", "+faststart", mp4], { stdio: "inherit" });
  console.log(ff.status === 0 ? `encoded ${mp4}` : "ffmpeg failed");
  writeFileSync(join(OUT, NAME + "-points.json"), JSON.stringify(pts, null, 1));
  console.log(JSON.stringify(pts));
  console.log(timeouts ? `WARNING ${timeouts} frames timed out` : "all frames complete");
} finally {
  await browser.close();
}
