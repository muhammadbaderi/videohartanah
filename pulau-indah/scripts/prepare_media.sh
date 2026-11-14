#!/usr/bin/env bash
# Rebuild the footage files the project needs from the original phone clip.
#   pulau-indah/scripts/prepare_media.sh /path/to/IMG_1360.MOV
# IMG_1360.MOV is 4K SDR (BT.709) portrait H.264, so it is only scaled to
# 1080x1920 with a keyframe every 15 frames (so the Studio can seek it).
set -euo pipefail
SRC="${1:?usage: $0 IMG_1360.MOV}"
OUT="$(cd "$(dirname "$0")/.." && pwd)/video/assets/footage"
mkdir -p "$OUT"
ffmpeg -hide_banner -loglevel error -y -i "$SRC" -map 0:v:0 -an -vf "scale=1080:1920:flags=lanczos,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 18 -g 15 -movflags +faststart "$OUT/IMG_1360_1080.mp4"
ffmpeg -hide_banner -loglevel error -y -ss 4.7 -i "$OUT/IMG_1360_1080.mp4" -frames:v 1 -q:v 2 "$OUT/freeze.jpg"
ffmpeg -hide_banner -loglevel error -y -ss 2.0 -i "$OUT/IMG_1360_1080.mp4" -frames:v 1 -vf "gblur=sigma=30,eq=brightness=-0.05:saturation=0.85" -q:v 3 "$OUT/ext_blur.jpg"
echo "done -> $OUT"
