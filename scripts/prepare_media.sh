#!/usr/bin/env bash
# Rebuild the media the HyperFrames project needs from the original phone clip.
#
#   scripts/prepare_media.sh /path/to/IMG_0725.MOV
#
# The 4K Dolby Vision / HLG iPhone clip is tone-mapped to SDR and scaled to
# 1080x1920 with a keyframe every 15 frames (so the Studio can seek it), the
# voice is cleaned (high-pass, light denoise, gentle compression) and
# loudness-normalised to -16 LUFS / -1.5 dBTP, and the closing frame is
# exported for the end card.
set -euo pipefail
SRC="${1:?usage: $0 IMG_0725.MOV}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$HERE/video/assets"
mkdir -p "$OUT/footage" "$OUT/audio"

ffmpeg -hide_banner -loglevel error -y -i "$SRC" -map 0:v:0 -an \
  -vf "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,scale=1080:1920:flags=lanczos" \
  -c:v libx264 -preset veryfast -crf 18 -g 15 -movflags +faststart "$OUT/footage/IMG_0725_1080.mp4"

ffmpeg -hide_banner -loglevel error -y -ss 87.25 -i "$OUT/footage/IMG_0725_1080.mp4" -frames:v 1 -q:v 2 "$OUT/footage/endframe.jpg"
ffmpeg -hide_banner -loglevel error -y -i "$OUT/footage/endframe.jpg" -vf "gblur=sigma=28,eq=brightness=-0.04:saturation=0.9" -q:v 3 "$OUT/footage/endframe_blur.jpg"

PRE="highpass=f=85,afftdn=nr=10:nf=-40,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=2"
J=$(ffmpeg -hide_banner -i "$SRC" -vn -af "$PRE,loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
read -r I TP LRA TH OFF < <(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
ffmpeg -hide_banner -loglevel error -y -i "$SRC" -vn \
  -af "$PRE,loudnorm=I=-16:TP=-1.5:LRA=9:measured_I=$I:measured_TP=$TP:measured_LRA=$LRA:measured_thresh=$TH:offset=$OFF:linear=true,aresample=48000" \
  -ac 1 -c:a pcm_s16le "$OUT/audio/voice.wav"
echo "done -> $OUT"
