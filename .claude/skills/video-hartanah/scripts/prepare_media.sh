#!/usr/bin/env bash
# Footage files the project needs, from the original phone clip.
#   prepare_media.sh <source-video> <project-dir>
# Scales to 1080x1920 with a keyframe every 15 frames (so the Studio can seek), tone-maps
# HDR (HLG/PQ, iPhone Dolby Vision) to SDR when needed, and exports the two stills named in
# project.json "stills": freeze (sharp, for the hook question) and blur (CTA/cashback backdrop).
set -euo pipefail
SRC="${1:?usage: $0 <source-video> <project-dir>}"; P="$(cd "${2:?project dir}" && pwd)"
read -r FOOT FREEZE BLUR < <(python3 -c "import json,sys;p=json.load(open(sys.argv[1]));s=p.get('stills',{});print(p['footage'],s.get('freeze',2.0),s.get('blur',2.0))" "$P/project.json")
OUT="$P/video/$FOOT"; DIR="$(dirname "$OUT")"; mkdir -p "$DIR"
TRC=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of csv=p=0 "$SRC")
VF="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p"
if [ "$TRC" = "arib-std-b67" ] || [ "$TRC" = "smpte2084" ]; then
  VF="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,$VF"
  echo "HDR ($TRC) -> tone-mapped to SDR"
fi
ffmpeg -hide_banner -loglevel error -y -i "$SRC" -map 0:v:0 -an -vf "$VF" -c:v libx264 -preset veryfast -crf 18 -g 15 -movflags +faststart "$OUT"
ffmpeg -hide_banner -loglevel error -y -ss "$FREEZE" -i "$OUT" -frames:v 1 -q:v 2 "$DIR/freeze.jpg"
ffmpeg -hide_banner -loglevel error -y -ss "$BLUR" -i "$OUT" -frames:v 1 -vf "gblur=sigma=30,eq=brightness=-0.05:saturation=0.85" -q:v 3 "$DIR/ext_blur.jpg"
echo "done -> $OUT, freeze.jpg (${FREEZE}s), ext_blur.jpg (${BLUR}s)"
