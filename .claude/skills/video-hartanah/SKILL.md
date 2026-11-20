---
name: video-hartanah
description: Make a vertical (1080x1920) property marketing video under a minute from a phone walkthrough clip and a Malay listing - voiceover in the owner's cloned ElevenLabs voice "Mad Bi" (or the owner's own voice cut from the clip), blue motion graphics (price, package, lot plan, highlights), a real map animation from the Google Maps pin, word-timed captions, music and sound effects - rendered with HyperFrames, plus a ready-to-post caption. Use this whenever the user pastes a property listing (projek perumahan, rumah teres, harga dari, booking, luas tanah, kemudahan terdekat...) or a Google Drive video of a house and asks for a video, reel, TikTok, "video marketing", "buatkan video", "voice over guna suara aku", or wants one of these videos changed (voice, theme, map, script, music), even if they never say "skill".
---

# Video hartanah (property marketing video)

The owner is a property agent in Selangor. They send a phone walkthrough clip (Google Drive link) and usually a
listing in Malay, and want a finished vertical video to post. Two videos have been made so far; both live in this
repo and are the templates:

| | `video/` - Teres setingkat, Meru | `rafflesia6/` - Taman Rafflesia 6, Seksyen 29 Shah Alam |
|---|---|---|
| Voice | the owner's own voice, cut from the clip | scripted voiceover, cloned voice (now "Mad Bi") |
| Look | yellow `#ffc83d` | **blue** (the owner's request; the default now) |
| Extras | hook moved to the front, lot size card | GPS map animation, price count-up, package ticks, post caption |
| How | `references/own-voice-edit.md` | this file + `voice.md`, `map.md`, `look.md` |

A third template, `nenasmeru/` (Teres & Semi-D, Jalan Nenas, Meru), is **photos only** (no clip): the developer's render,
elevation and floor plan plus site photos, a "blueprint" look (drafting grid, the developer's drawings inverted to white-on-blue,
JetBrains Mono annotations, Archivo Black), music and 8 sound effects generated with ElevenLabs, and the owner's own script read
as-is. Use it when the owner sends pictures and a script instead of a video, or asks for something that doesn't look like other
agents' reels. Its `build.py` adds photo shots (`kind: img` panned with x0/x1, s0/s1), board shots and per-shot transitions
(`in`: flash, punch, scan, whip, shutter), a `lead_in`, and `process_vo.py` (re-process chosen takes with a tempo, no Whisper).

Read the HyperFrames skill (`/hyperframes`, and `/media-use` for audio) for the framework contract; this skill is
the house style and the order of work. Default to the Rafflesia 6 way (scripted, Mad Bi, blue, map) unless the
owner asks for their recorded voice or sends no listing.

## What the owner has asked for so far (keep doing these without being asked)

- Under a minute (50-58 s), vertical, in Malay, ending on their phone number (016-370 8908 so far; take it from
  the clip or listing each time).
- Voice: "suara aku" means their cloned ElevenLabs voice **"Mad Bi"**, and it must not be monotone: eleven_v3
  with an emotion tag per line, best of 3 takes (`references/voice.md`).
- Blue theme with matching tones for the motion graphics and text animation (`references/look.md`).
- A map animation from their Google Maps pin (`references/map.md`). If they did not send a pin, ask for one in a
  line while you work on the rest; the video can be built without it and the map added later.
- Music under the voice and sounds on things that appear.
- Talk to them in casual Malay ("aku/kau"), send a short status line every few minutes (they follow on a phone
  and ask "berapa lama lagi?"), and give a time estimate before long steps (a render is ~5 min, a map bake ~5 min,
  three voice takes + picking ~6 min). Send the MP4 with `SendUserFile`.

## The order of work (Mode B: scripted voiceover)

1. **Footage.** Get the Drive file id from the link and read its metadata with the Google Drive connector
   (`get_file_metadata`), then download it with curl from
   `https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t` into `.media-src/`
   (works when the file is shared "anyone with the link"; the connector's base64 download is too big for video).
   `ffprobe` it (iPhone portrait comes as a rotation tag; ffmpeg auto-rotates; check HDR vs bt709). Make a 1 s
   contact sheet to pick shots, and transcribe the parts where the owner talks with faster-whisper large-v3
   (`language="ms"`, place names in `initial_prompt`, pass a numpy array, not a path: PyAV 19 breaks the path call).
   What they say on site (porch for 2 cars, high ceiling, 4-5 ft at the back) is good script material.
2. **New project.** `bash .claude/skills/video-hartanah/scripts/new_project.sh <name>` clones `rafflesia6/` into
   `<name>/` (HyperFrames project) and `scripts/<name>/` (script, timeline, builders). Then edit the still times in
   `scripts/<name>/prepare_media.sh` (end-card background, and a frame where the owner faces the camera with the
   mouth closed for the avatar) and run it on the clip.
3. **Script and voice** (`references/voice.md`): lines in `scripts/<name>/vo_lines.json`, then
   `tts.py --takes 3` and `pick_takes.py`. About 120-150 words.
4. **Map** (`references/map.md`): resolve the Maps link to coordinates, geocode 2-3 nearby places, bake the move,
   paste the pin offsets into `compositions/g-loc.html`.
5. **Graphics.** Edit the listing text in `<name>/compositions/g-*.html` (names, prices, sizes, distances, phone)
   and `captions_src.json`. Keep the timing code: every animation is written against the word cues `W[i]` (start
   of spoken word i of that scene's line), `E[i]` (its end) and `D` (scene length), which `build.py` fills in from
   the voice, so a new take never needs hand re-timing.
6. **Build and check.** `python3 -I scripts/<name>/build.py`, then in `<name>/`: `npx hyperframes check --json`
   (fix every error and warning), `npx hyperframes snapshot --at ...` at each scene's busiest moment and look at
   the frames. Overlapping labels, text under 28 px and text outside the apps' safe area (`look.md`: y 288-1248,
   x 120-888, only x 120-780 below y 840) are the usual fixes.
7. **Render and master.** `npx hyperframes render --quality delivery -o renders/<name>-vN.mp4`, then set the audio
   to -14 LUFS / -1.5 dBTP with a two-pass ffmpeg `loudnorm` and `-c:v copy` into `renders/<Project>-FINAL.mp4`.
   Measure (`ffmpeg -af loudnorm=print_format=summary`) and pull a frame strip from the rendered file to look at.
8. **Deliver.** Send the MP4. Write `<name>/EDIT_NOTES.md` (script table, where each fact came from, points to
   check) and `<name>/POST_CAPTION.md` (the whole listing as a post with emojis and hashtags; the schools,
   mosques and other towns that did not fit in the video go here; drop obvious duplicates and say so). Commit
   and push; renders and footage stay out of git (`.gitignore` covers them).

In the delivery message, say that the sound was measured, not listened to, and list what to check:
pronunciation of names, any fact you inferred, any place you geocoded.

## Scenes (one per voiceover line; `build.py` sizes them from the voice)

| Scene | Line (example) | On screen |
|---|---|---|
| g-hook | Cari rumah teres setingkat kat Shah Alam, bawah lima ratus ribu? Jom tengok! | Frame 0 is the thumbnail: "Rumah Teres / 1 TINGKAT / bawah RM500K?", blue marker sweeps on the price |
| g-intro | Projek baru, Taman X, Seksyen 29, Shah Alam. Terhad 19 unit je! | Location card; "TERHAD 19 UNIT" badge counting up |
| g-spec | 4 bilik tidur, 2 bilik air. Tanah 21 x 68, binaan 924 kaki persegi. | Two stat cards; lot plan drawn to scale with counting numbers |
| g-porch | Porch muat 2 kereta, siling pun tinggi. | Two cards with icons (cars pop in, arrow up) |
| g-price | Harga dari ... Booking RM500 je, free legal fee SPA, free MOT ... | Price counts up to the exact figure (impact sound), package ticks |
| g-loc | Dekat A, B dan C. Akses mudah ke ELITE, SKVE, KESAS, LKSA. | Map dives to the pin; lines + distance labels as each place is named; highway signs |
| g-tenure | Leasehold, Rizab Melayu. Siap suku pertama 2027. | Tags; "DIJANGKA SIAP Q1 2027" card |
| g-cta | Unit terhad! Berminat? Contact saya di 016-... | Stamp, then end card: the owner's face in a ring, phone number, project name and price |

Drop or merge scenes the listing has nothing for; add one for a strong extra point (it needs a line in
`vo_lines.json`, a CUES block, caption chunks and shots - copy how `g-porch` is wired). Facts on screen come
from the listing or from what the owner said on camera; never invent a figure, and ask when one sounds off.

## Things that cost time before (so they don't again)

- ElevenLabs: `mp3_44100_192` returns 403 on this plan, use `mp3_44100_128`. The key has no `models_read`;
  `eleven_v3` works with `/with-timestamps`. v3 takes vary: always make 3 and pick.
- CARTO basemaps now return "API KEY REQUIRED" tiles: use Esri World Dark Gray Canvas. cdn.jsdelivr.net,
  unpkg.com and overpass-api.de are blocked here: install `maplibre-gl@5.24.0` from npm and load it locally.
- HeyGen is not signed in inside cloud sessions, so new music cannot be searched; reuse
  `assets/audio/music-bed.mp3` (licensed, see its CREDITS.md) and place it so its last chord (~80 s into the
  track) lands just after the voice ends (`edl.json` `music.media_start`).
- A fresh cloud container has no HyperFrames skills: `npx hyperframes skills update hyperframes hyperframes-cli
  media-use` installs them. The CLI is pinned in `package.json` (0.9.56); `npm install` first.
- Kill a running render before changing the project; a render with stale timing wastes 5 minutes.
- `build.py` overwrites `index.html`, `captions.html` and the CUES blocks; everything else in the scene files is yours.
- ElevenLabs Music works with the connected key: `POST /v1/music?output_format=mp3_44100_128` with `prompt`,
  `music_length_ms` (~62000), `model_id: music_v1`, `force_instrumental: true`. Use it for a track nobody else has; then
  `npx hyperframes audio <file> --json --only onsets,silence,sections,downbeats` to find its ring-out and place it.
  Sound effects: `POST /v1/sound-generation` (`text`, `duration_seconds`, `prompt_influence`); send them one at a time
  (parallel calls get 429). Trim the leading silence and find each file's hit time before placing it.
- Start a render with the Bash tool's `run_in_background`, not `&` inside a command: the render is cancelled
  (`render_cancelled_parent_exited`) when that command returns. A 51 s draft render takes ~10 min here (one worker).
- Photos only: the developer's line drawings (black on white) become blueprint art with a luminance-to-alpha pass in PIL
  (white lines, transparent ground; 2-3x upscale first). The baked map can be graded with an ffmpeg `lutrgb` gradient map
  (`map.json` `grade`) instead of tinting tiles.
