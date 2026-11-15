#!/usr/bin/env bash
# Download the inputs for a new edit and resolve the map pin.
#   fetch_inputs.sh <work-dir> <video-drive-link> [floorplan-drive-link] [google-maps-link]
# Drive links must be shared "anyone with the link" (or use the Google Drive connector's
# download tool for small files). Writes <work-dir>/source.<ext>, <work-dir>/floorplan.<ext>
# and prints the map coordinates. The work dir should be outside git (big files).
set -euo pipefail
WORK="${1:?usage: $0 <work-dir> <video-link> [floorplan-link] [maps-link]}"; VID="${2:?video link}"; PLAN="${3:-}"; MAPS="${4:-}"
mkdir -p "$WORK"
drive_id() { echo "$1" | sed -nE 's#.*/d/([A-Za-z0-9_-]+).*#\1#p; s#.*[?&]id=([A-Za-z0-9_-]+).*#\1#p' | head -1; }
fetch() {  # <link> <basename>
  local id; id=$(drive_id "$1"); [ -n "$id" ] || { echo "not a Drive link: $1" >&2; return 1; }
  local tmp="$WORK/.$2.part"
  curl -sSL -o "$tmp" -w "  $2: HTTP %{http_code}, %{size_download} bytes, %{content_type}\n" \
    "https://drive.usercontent.google.com/download?id=$id&export=download&confirm=t"
  local kind; kind=$(file -b --mime-type "$tmp")
  case "$kind" in
    video/quicktime) ext=mov ;; video/mp4) ext=mp4 ;; image/jpeg) ext=jpg ;; image/png) ext=png ;; image/heic) ext=heic ;; application/pdf) ext=pdf ;;
    text/html) echo "  $2: got an HTML page, not the file. The Drive file is probably not shared publicly." >&2; rm -f "$tmp"; return 1 ;;
    *) ext=bin ;;
  esac
  mv "$tmp" "$WORK/$2.$ext"; echo "  -> $WORK/$2.$ext ($kind)"
}
fetch "$VID" source
[ -n "$PLAN" ] && fetch "$PLAN" floorplan
if [ -n "$MAPS" ]; then
  url=$(curl -sS -o /dev/null -w "%{redirect_url}" "$MAPS"); [ -n "$url" ] || url="$MAPS"
  echo "  maps -> $url"
  echo "$url" | grep -oE '(-?[0-9]+\.[0-9]+),\+?(-?[0-9]+\.[0-9]+)' | head -1 | sed 's/+//; s/^/  pin (lat,lon): /' || echo "  could not read coordinates; open the link and copy them"
fi
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,color_transfer:stream_side_data=rotation -of compact "$WORK"/source.* || true
