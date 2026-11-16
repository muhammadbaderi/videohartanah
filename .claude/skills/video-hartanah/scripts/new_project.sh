#!/usr/bin/env bash
# Start a new property video from the proven template (rafflesia6 by default).
#
#   bash .claude/skills/video-hartanah/scripts/new_project.sh <name> [template]
#
# Copies <template>/ -> <name>/ (the HyperFrames project: scenes, theme, sfx, music, GSAP) and
# scripts/<template>/ -> scripts/<name>/ (script, timeline rules, builders), leaving out everything that
# belongs to the old listing: renders, footage, voice takes, word timings, notes. The scripts find their
# project by folder name, so scripts/<name>/build.py builds <name>/.
set -euo pipefail
NAME="${1:?usage: new_project.sh <name> [template]}"
TPL="${2:-rafflesia6}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
[ -e "$NAME" ] && { echo "$NAME/ already exists" >&2; exit 1; }
[ -d "$TPL" ] && [ -d "scripts/$TPL" ] || { echo "template $TPL/ or scripts/$TPL/ not found in $ROOT" >&2; exit 1; }

mkdir -p "$NAME" "scripts/$NAME"
tar -C "$TPL" -cf - \
  --exclude=renders --exclude=.hyperframes --exclude='assets/footage/*' \
  --exclude='assets/audio/vo-*' --exclude=EDIT_NOTES.md --exclude=POST_CAPTION.md . | tar -C "$NAME" -xf -
mkdir -p "$NAME/assets/footage"
tar -C "scripts/$TPL" -cf - --exclude=vo_align.json --exclude=map_coords.json --exclude=__pycache__ . | tar -C "scripts/$NAME" -xf -

python3 - "$NAME" <<'PY'
import json, sys
name = sys.argv[1]
m = json.load(open(f"{name}/meta.json")); m["id"] = name; m["name"] = name
json.dump(m, open(f"{name}/meta.json", "w"), indent=2)
p = json.load(open(f"{name}/package.json")); p["name"] = name
json.dump(p, open(f"{name}/package.json", "w"), indent=2)
PY
cat <<MSG
Created $NAME/ and scripts/$NAME/ from $TPL.
Next:
  scripts/$NAME/prepare_media.sh /path/to/clip.MOV      # footage + end-card stills (edit the still times first)
  edit scripts/$NAME/vo_lines.json + captions_src.json  # the new script
  python3 -I scripts/$NAME/tts.py --takes 3 && python3 -I scripts/$NAME/pick_takes.py
  edit scripts/$NAME/map.json, bake, paste offsets into $NAME/compositions/g-loc.html
  edit the listing text in $NAME/compositions/g-*.html, then python3 -I scripts/$NAME/build.py
MSG
