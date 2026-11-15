#!/usr/bin/env bash
# Scaffold a new property-video project folder at the repo root.
#   new_project.sh <slug> ["Title"]
set -euo pipefail
SLUG="${1:?usage: $0 <slug> [title]}"; TITLE="${2:-$1}"
SKILL="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(git -C "$SKILL" rev-parse --show-toplevel)"
P="$ROOT/$SLUG"; [ -e "$P" ] && { echo "$P already exists" >&2; exit 1; }
mkdir -p "$P/video/assets/"{audio/vo,footage,map,sfx,vendor} "$P/video/compositions"
cp "$SKILL/assets/scaffold/"{hyperframes.json,package.json,CLAUDE.md,AGENTS.md} "$P/video/"
cp "$SKILL/assets/scaffold/assets/vendor/gsap.min.js" "$P/video/assets/vendor/"
cp "$SKILL/assets/sfx/"* "$P/video/assets/sfx/"
printf '{\n  "id": "%s",\n  "name": "%s",\n  "createdAt": "%s"\n}\n' "$SLUG" "$TITLE" "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" > "$P/video/meta.json"
python3 - "$SKILL/examples/project.example.json" "$P/project.json" "$SLUG" "$TITLE" <<'PY'
import json, sys
p = json.load(open(sys.argv[1])); p["slug"], p["title"] = sys.argv[3], sys.argv[4]
json.dump(p, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
PY
G="$ROOT/.gitignore"; touch "$G"
for pat in "$SLUG/video/assets/footage/*.mp4" "$SLUG/video/renders/" "$SLUG/video/.hyperframes/" "__pycache__/"; do
  grep -qxF "$pat" "$G" || echo "$pat" >> "$G"
done
echo "created $P (project.json starts as a copy of the Pulau Indah example: replace every field)"
