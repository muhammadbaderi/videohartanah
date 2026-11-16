# Edit: Taman Rafflesia 6, Seksyen 29 Shah Alam (IMG_1073.MOV)

Marketing video, 1080×1920, 30 fps, **54.2 s**. Blue theme (navy `#061636`, royal blue `#1d5cff`, sky `#5cc2ff`, ice `#e6f2ff`),
Montserrat for headings and numbers, Inter for small text.

- Source: `IMG_1073.MOV` (iPhone 4K SDR, portrait, 127.8 s) from Google Drive. Only the pictures are used.
- Voice: a script read by the owner's cloned voice on ElevenLabs (not the voice recorded in the clip).
  **v3: voice "Mad Bi"** (`j2h6UJwjLSvHhJaBXWtF`), `eleven_v3` with an audio tag per line ([excited], [enthusiastic],
  [cheerful], [confident]), best of 3 takes per line (`tts.py --takes 3`, `pick_takes.py`). v2 used the same model with
  the older clone "Suara sendiri"; v1 (eleven_multilingual_v2) was found monotone.
- Status: **v2 rendered** (2026-11-16): `renders/Taman-Rafflesia-6-FINAL-v2.mp4`, 1080×1920, 30 fps, 54.2 s, H.264 delivery quality,
  audio mastered to **-14.0 LUFS, true peak -1.8 dBTP** (measured, not listened to). `renders/rafflesia6-v2.mp4` is the raw render
  (-13.1 LUFS) before that loudness step. v1 (`Taman-Rafflesia-6-FINAL.mp4`, 56.6 s) had the first, flatter voice. The renders are not in git (too big).
- Music: the track's last chord lands just after the voice ends (52 s); its ring-out carries the end card and fades out by 53.8 s.

## Script (voiceover)

| Scene (s) | Line | On screen |
|---|---|---|
| 0.00–4.60 | Cari rumah teres setingkat kat Shah Alam, bawah lima ratus ribu? Jom tengok! | Hook from frame 0: "Rumah Teres 1 TINGKAT bawah RM500K?", blue marker on the price |
| 4.60–10.40 | Projek baru, Taman Rafflesia 6, Seksyen 29, Shah Alam. Terhad 19 unit je! | Location card; badge "TERHAD 19 UNIT SAHAJA" counting up |
| 10.40–17.55 | 4 bilik tidur, 2 bilik air. Tanah 21 × 68, binaan 924 kaki persegi. | Two stat cards; lot plan drawn to scale (21' × 68' land, 21' × 48' built-up) |
| 17.55–20.82 | Porch muat 2 kereta, siling pun tinggi. | PORCH: 2 KERETA (two car icons); SILING TINGGI |
| 20.82–29.80 | Harga dari 455 ribu. Booking RM500 je, free legal fee SPA, dan free MOT untuk pembeli rumah pertama. | Price counts up to **RM455,120**; package with 3 ticks |
| 29.80–38.98 | Dekat Quayside Mall Rimbayu, Saujana Putra dan Kota Kemuning. Akses mudah ke ELITE, SKVE, KESAS dan LKSA. | **Map animation**: zooms in on your GPS pin, then a line and a distance label to each of the 3 places as they are named; 4 highway signs |
| 38.98–43.81 | Leasehold, Rizab Melayu. Siap suku pertama 2027. | Tags LEASEHOLD · RIZAB MELAYU; card DIJANGKA SIAP Q1 2027 |
| 43.81–54.18 | Unit terhad! Berminat? Contact saya di 016-370 8908. | "UNIT TERHAD!"; end card: your face, 016-370 8908, project name, price |

Not in the video (too much for under a minute): the schools, the mosques, Tropicana Aman, Putra Perdana, Subang Jaya.
They are in the post caption (`POST_CAPTION.md`).

## Map (location chapter)

- Your pin from Google Maps: **2.9717222, 101.5476944** (https://maps.app.goo.gl/aU5Aw5cPhVfhGUq16).
- The other 3 places were looked up on OpenStreetMap (Nominatim): Quayside Mall (2.95685, 101.55297), Bandar Saujana Putra (2.95225, 101.57976), Kota Kemuning (3.00490, 101.53598).
  The distance labels (2.8 / 5 / 6 KM) are the driving distances you gave, not straight lines.
- Map tiles: Esri World Dark Gray Canvas (data from HERE, Garmin and OpenStreetMap), tinted blue. The credit is on screen, small, bottom right.
- The camera move is baked to `assets/footage/map.mp4` (live tiles change between renders): `scripts/rafflesia6/bake_map.cjs` with the settings in `scripts/rafflesia6/map.json`.
  The pins, lines and labels are live HTML in `compositions/g-loc.html`, placed from `map_coords.json` on the same zoom curve, so they stay editable.
  If you change `map.json`, bake again and copy the new offsets from `map_coords.json` into `POI` in `g-loc.html`.
- The highways are signs only (no lines on the map): the route data service is not reachable from here.

## Points to check (change them and render again if something is wrong)

1. **Porch for 2 cars and a high ceiling**: taken from what you said in the clip ("porch dia boleh buat dua bilik kereta", "ceiling tinggi").
2. **The VO says "455 ribu"**, the card shows the full RM455,120.
3. **Lot plan**: the built-up area (21' × 48') is drawn starting about 15' from the front, leaving ~5' at the back (you said "4 ke 5 kaki belakang"). It is a sketch, not the developer's plan.
4. **Pronunciation** (checked by transcribing the voice again with Whisper): all words come out right. "SKVE" may sound like "S-K-V-A"; "Leasehold" is read in English.
5. **Phone number 016-370 8908**: same as in the clip and the Meru video.

## How to run

```bash
npm install                                             # hyperframes@0.9.17 (pinned)
scripts/rafflesia6/prepare_media.sh /path/to/IMG_1073.MOV   # footage + end-card stills (not in git)
(cd /tmp && npm install maplibre-gl@5.24.0) && MAPLIBRE=/tmp/node_modules/maplibre-gl/dist node scripts/rafflesia6/bake_map.cjs   # map.mp4 (not in git)
python3 -I scripts/rafflesia6/build.py                  # regenerates index.html + captions.html
cd rafflesia6 && npx hyperframes preview                # Studio
npx hyperframes render --quality delivery -o renders/rafflesia6-v1.mp4
# then -14 LUFS / -1.5 dBTP on the audio only (two-pass ffmpeg loudnorm, video copied) -> renders/Taman-Rafflesia-6-FINAL.mp4
```

- Change a word in the voiceover: edit `scripts/rafflesia6/vo_lines.json`, run `python3 -I scripts/rafflesia6/tts.py <line id>`
  (ElevenLabs credits), redo the compression/EQ + loudness step (see `assets/audio/CREDITS.md`), then `build.py`.
- **Everything follows the voice.** `build.py` lays the lines out from ElevenLabs' word timings (`vo_align.json`), anchors shots to words
  (`edl.json`), times the captions and sound effects, and writes `W` (word starts), `E` (word ends) and `D` (scene length) into the
  `CUES` block of each `compositions/g-*.html`; the scene animations are written against those (`W[7]` = word 7 of that scene's line).
  A new take therefore only needs `build.py` to stay in sync, as long as the words stay the same (the caption chunks use word indices).
- **Warning:** `build.py` overwrites `index.html`, `compositions/captions.html` and the `CUES` blocks. The rest of each scene file is not touched.
