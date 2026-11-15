#!/usr/bin/env bash
# Rebuild the media the pipit/ HyperFrames project needs (the large files are not in git).
#
#   scripts/pipit/prepare_media.sh /path/to/folder-with-the-originals
#
# The folder holds the owner's Google Drive files: IMG_1307.MOV, IMG_1308.MOV (site clips),
# IMG_1431.JPG (floor plan), IMG_1432.JPG (side render), IMG_1433.JPG (front render).
# Clips: 4K portrait SDR -> 1080x1920, 30 fps, a keyframe every 30 frames, no audio.
# Map: real Esri World Imagery around the map pin (2.924945, 101.510804), baked to an all-intra
# MP4 with scripts/pipit/bake-map-portrait.mjs (needs network, ffmpeg, Chromium, and
# `npm i puppeteer-core@24 maplibre-gl@5.24.0` next to the script).
set -euo pipefail
SRC="${1:?usage: $0 /path/to/originals}"
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$HERE/pipit/assets"
mkdir -p "$OUT/footage" "$OUT/images"

for f in IMG_1307 IMG_1308; do
  ffmpeg -hide_banner -loglevel error -y -i "$SRC/$f.MOV" -map 0:v:0 -an \
    -vf "scale=1080:1920:flags=lanczos,fps=30,format=yuv420p" \
    -c:v libx264 -preset slow -crf 17 -g 30 -movflags +faststart "$OUT/footage/$f.mp4"
done
cp "$SRC/IMG_1433.JPG" "$OUT/images/render-depan.jpg"
cp "$SRC/IMG_1432.JPG" "$OUT/images/render-sisi.jpg"
cp "$SRC/IMG_1431.JPG" "$OUT/images/pelan.jpg"

if [ "${BAKE_MAP:-0}" = "1" ]; then
  # 7 s: hold on the plot, pull back to the Klang Valley while the plot glides to (330, 1150), hold
  (cd "$HERE/scripts/pipit" && CHROME="${CHROME:-/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell}" \
    NAME=map-pullback OUT="$OUT/footage" SITE="101.510804,2.924945" TARGET="330,1150" ZSTART=16.4 ZEND=10.55 \
    FPS=30 DUR=7 PRE=0.07 HOLD=0.47 \
    POINTS='{"klcc":[101.7123,3.1579],"shahalam":[101.5185,3.0733],"putrajaya":[101.6964,2.9264],"klang":[101.4456,3.0449]}' \
    node bake-map-portrait.mjs)
  ffmpeg -hide_banner -loglevel error -y -sseof -0.04 -i "$OUT/footage/map-pullback.mp4" -frames:v 1 -q:v 2 "$OUT/footage/map-hold.jpg"
  rm -rf "$OUT/footage/frames-map-pullback"
fi
echo "done -> $OUT"
