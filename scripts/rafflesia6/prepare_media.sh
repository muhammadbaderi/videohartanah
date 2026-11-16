#!/usr/bin/env bash
# Rebuild the footage the rafflesia6 project needs from the original phone clip.
#
#   scripts/<name>/prepare_media.sh /path/to/clip.MOV
#
# IMG_1073.MOV is 4K SDR (BT.709) portrait. It is scaled to 1080x1920 with a keyframe
# every 15 frames (so the Studio can seek it). The end-card stills are exported too.
# The voiceover is not made here: see scripts/rafflesia6/tts.py (ElevenLabs, cloned voice).
set -euo pipefail
SRC="${1:?usage: $0 IMG_1073.MOV}"
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
NAME="$(basename "$(cd "$(dirname "$0")" && pwd)")"   # scripts/<name>/ -> <name>/
OUT="$HERE/$NAME/assets/footage"
mkdir -p "$OUT"
ffmpeg -hide_banner -loglevel error -y -i "$SRC" -map 0:v:0 -an \
  -vf "scale=1080:1920:flags=lanczos,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 18 -g 15 -movflags +faststart "$OUT/IMG_1073_1080.mp4"
# end card: blurred facade + the presenter's face (123.0 s, mouth closed)
ffmpeg -hide_banner -loglevel error -y -ss 1.0 -i "$OUT/IMG_1073_1080.mp4" -frames:v 1 \
  -vf "gblur=sigma=26,eq=brightness=-0.03:saturation=0.85" -q:v 3 "$OUT/endcard_bg.jpg"
ffmpeg -hide_banner -loglevel error -y -ss 123.0 -i "$OUT/IMG_1073_1080.mp4" -frames:v 1 \
  -vf "crop=700:700:193:570,scale=400:400:flags=lanczos" -q:v 2 "$OUT/agent.jpg"
echo "done -> $OUT"
