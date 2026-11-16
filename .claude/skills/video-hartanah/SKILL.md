---
name: video-hartanah
description: Make a vertical (1080x1920) property marketing video under a minute from a phone walkthrough clip and a listing in Malay - voiceover in the owner's cloned ElevenLabs voice "Mad Bi", blue motion graphics (price, package, lot plan, highlights), a real map animation from the Google Maps pin, word-timed captions, music and sound effects - rendered with HyperFrames. Use this whenever the user pastes a property listing (projek perumahan, rumah teres, harga dari, booking, luas tanah, kemudahan terdekat...) or a Google Drive video of a house and asks for a video, reel, TikTok, "video marketing", "buatkan video", "voice over guna suara aku", or wants an existing rafflesia6-style video changed (voice, theme, map, script), even if they never say "skill".
---

# Video hartanah (property marketing video)

The owner (an agent in Selangor) sends a listing in Malay plus a phone walkthrough clip, and wants a
finished social video they can post. This skill is the proven recipe from `rafflesia6/` in this repo
(Taman Rafflesia 6, Seksyen 29 Shah Alam): copy that project, swap in the new listing, footage, voice
and map, check, render, deliver. Read the HyperFrames skill (`/hyperframes`, plus `/media-use` for audio)
for the framework contract; this file is the house style and the order of work.

Write to the owner in casual Malay (BM santai, "aku/kau" as they do), short status lines while working,
and end with what to check. They follow on a phone, so send the MP4 with `SendUserFile`.

## The order of work

1. **Footage.** Get the Drive file id from the link, read its metadata with the Google Drive connector
   (`get_file_metadata`), then download it with curl from
   `https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t` into `.media-src/`
   (works when the file is shared "anyone with the link"; the connector's base64 download is too big for video).
   `ffprobe` it (iPhone clips are portrait via a rotation tag; ffmpeg auto-rotates). Make a 1 s contact sheet
   to pick shots, and transcribe the parts where the owner talks with faster-whisper large-v3
   (`language="ms"`, place names in `initial_prompt`, pass a numpy array, not a path: PyAV 19 breaks the path call).
   What the owner says on site (porch for 2 cars, high ceiling, 4-5 ft at the back) is good script material;
   their phone number at the end is the CTA.
2. **New project.** `bash .claude/skills/video-hartanah/scripts/new_project.sh <name>` clones the template into
   `<name>/` (HyperFrames project) and `scripts/<name>/` (script, timeline, builders). Then
   `scripts/<name>/prepare_media.sh /path/to/clip.MOV` makes the 1080x1920 seekable footage and the end-card stills
   (edit the still times in it: a frame where the owner looks at camera with the mouth closed).
3. **Script and voice** - read `references/voice.md`. Lines in `scripts/<name>/vo_lines.json`, generate 3 takes per
   line with `tts.py --takes 3`, keep the best with `pick_takes.py`. Under 60 s in total: about 120-150 words.
4. **Map** - read `references/map.md`. Resolve the owner's Google Maps link to coordinates, geocode 2-3 nearby
   places, bake the camera move, paste the pin offsets into `compositions/g-loc.html`.
5. **Graphics.** Edit the listing text in `<name>/compositions/g-*.html` (names, prices, sizes, distances,
   phone) and `captions_src.json`. Keep the timing code: every animation is written against the word cues
   `W[i]` (start of spoken word i of that scene's line), `E[i]` (its end) and `D` (scene length), which
   `build.py` fills in from the voice. Look and layout rules: `references/look.md`.
6. **Build and check.** `python3 -I scripts/<name>/build.py`, then in `<name>/`: `npx hyperframes check --json`
   (fix every error and warning), `npx hyperframes snapshot --at ...` at each scene's busiest moment and look at
   the frames. Overlapping labels, text under 28 px and things cut by the 168-1330 px band are the usual fixes.
7. **Render and master.** `npx hyperframes render --quality delivery -o renders/<name>-vN.mp4` (about 5 min for
   55 s), then set the audio to -14 LUFS / -1.5 dBTP with a two-pass ffmpeg `loudnorm` and `-c:v copy`
   into `renders/<Project>-FINAL.mp4`. Measure, don't guess: `ffmpeg -af loudnorm=print_format=summary`.
8. **Deliver.** Send the MP4 with `SendUserFile`. Write `<name>/EDIT_NOTES.md` (script table, what came from
   where, points to check) and `<name>/POST_CAPTION.md` (the full listing as a post with emojis and hashtags:
   everything that did not fit in the video - schools, mosques, other towns - goes here). Commit and push;
   renders and footage stay out of git (`.gitignore` already covers them).

Say plainly in the delivery message that the sound was measured, not listened to, and list what the owner
should check: pronunciation of names, any fact you inferred, any place you geocoded.

## What the video contains (scene by scene)

One HyperFrames scene per voiceover line; `build.py` lays them out from the voice, so lengths follow the take.

| Scene | Line (example) | On screen |
|---|---|---|
| g-hook | Cari rumah teres setingkat kat Shah Alam, bawah lima ratus ribu? Jom tengok! | Frame 0 is the thumbnail: "Rumah Teres / 1 TINGKAT / bawah RM500K?", blue marker sweeps on the price |
| g-intro | Projek baru, Taman X, Seksyen 29, Shah Alam. Terhad 19 unit je! | Location card; "TERHAD 19 UNIT" badge counting up |
| g-spec | 4 bilik tidur, 2 bilik air. Tanah 21 x 68, binaan 924 kaki persegi. | Two stat cards; lot plan drawn to scale with counting numbers |
| g-porch | Porch muat 2 kereta, siling pun tinggi. | Two cards with icons (cars pop in, arrow up) |
| g-price | Harga dari ... Booking RM500 je, free legal fee SPA, free MOT ... | Price counts up to the exact figure (impact sound), package ticks |
| g-loc | Dekat A, B dan C. Akses mudah ke ELITE, SKVE, KESAS, LKSA. | Map: dives to the pin, lines + distance labels to each place as it is named, highway signs |
| g-tenure | Leasehold, Rizab Melayu. Siap suku pertama 2027. | Tags; "DIJANGKA SIAP Q1 2027" card |
| g-cta | Unit terhad! Berminat? Contact saya di 016-... | Stamp, then end card: owner's face in a ring, phone number, project name and price |

Drop or merge scenes the listing has nothing for; add one if the listing has a strong extra point
(then add its CUES block, its line, its caption chunks and its shots - see how `g-porch` is wired).
Facts on screen come from the listing or from what the owner said on camera; never invent a figure.

## Things that cost time before (so they don't again)

- ElevenLabs: `mp3_44100_192` returns 403 on this plan, use `mp3_44100_128`. The key has no `models_read`;
  `eleven_v3` works with `/with-timestamps`. v3 takes vary: always make 3 and pick.
- CARTO basemaps now return "API KEY REQUIRED" tiles; use Esri World Dark Gray Canvas. cdn.jsdelivr.net,
  unpkg.com and overpass-api.de are blocked here: install `maplibre-gl@5.24.0` from npm and load it locally.
- HeyGen is not signed in inside cloud sessions, so new music cannot be searched; reuse
  `assets/audio/music-bed.mp3` (licensed, from the Meru video) and place it so its last chord lands just after
  the voice ends (`edl.json` `music.media_start`; the track's final chord is at ~80 s).
- A wrong-time render wastes 5 minutes: kill a running render before changing the project.
- `build.py` overwrites `index.html`, `captions.html` and the CUES blocks; everything else in the scene files is yours.
