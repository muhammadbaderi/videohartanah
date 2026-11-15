# Review: Rumah Berkembar 1-Tingkat, Jalan Pipit (Telok Panglima Garang)

Status: **v2 with voiceover, rendered** (2026-11-15): `renders/pipit-berkembar-vo.mp4`, 1080×1920, 30 fps,
58.1 s. (v1, music only, 53.55 s: `renders/pipit-berkembar-final.mp4`; the owner found it too dull.)
Renders and the large footage are not in git; rebuild with `scripts/pipit/prepare_media.sh` and the
render command at the bottom.

## Creative calls

- **Storyline A** from `STORYLINES.md` ("Rumah dulu, baru tawaran"): house + price → 8 units only →
  package → floor plan + sizes → site → map → places nearby → end card. Not built: B "RM1,000"
  (the number as the hook) and C "Dari langit" (one satellite dive). Both are in `STORYLINES.md`.
- **Voiceover (v2)**: the owner asked for one from ElevenLabs, not monotone, script written by me.
  Voice: the account's own clone, "Suara sendiri (videohartanah)" (made from the Meru video), on
  `eleven_v3` with emotion tags. Script, takes and measurements: `VOICEOVER.md`. The voice is now the
  clock: every cut lands just before its line, every card/number lands on the word that says it.
  The map scene got 1.7 s before the voice starts so the pull-back lands before "Shah Alam".
- **Music**: same warm acoustic HeyGen catalog track as the Meru video, ducked to 0.2 under the voice,
  up to 0.45 in the map lead-in and 0.55 after the last line, entered on a beat so it ends on its own.
- **Phone number 016-370 8908** on the end card is from the Meru video (not in this brief). It is a
  variable (`phone` on `s8-cta`); the price is a variable there too. The voice says "hubungi saya
  sekarang", not the number, so a different number only needs the card changed.
- **Amenities**: the voice names school 5 min, 99 Speedmart 6 min, Eco Sanctuary 9 min; the screen
  shows those three (v1's Columbia Asia row was dropped so nothing on screen goes unspoken). The map
  shows Shah Alam 23, KLCC 42 (both spoken) and Putrajaya 41 min (screen only), plus 4 highways.
- **FREE rows follow the voice's order**: Legal Fee, Disbursements, MOT (pembeli rumah pertama).
- **Map**: real Esri satellite imagery around the map pin (2.924945, 101.510804), baked once, played
  at 1.75×. City labels sit at projected real coordinates (`assets/footage/map-pullback-points.json`).
- **Site clips** carry no "filmed here" caption. "Dijangka siap Q4 2027" sits over IMG_1308, which
  shows nearly-finished houses: if those aren't this phase, move that card onto a render.
- **"4 Bilik"** is the developer's copy; the plan labels 3 bedrooms + a store and the video does not
  point at rooms, so the two don't contradict on screen.

## Measured vs looked at

- `npx hyperframes check`: 0 errors; 1 warning kept (below).
- Looked at: the beat sheet, all 7 seams, the phone sheet, and frames at 8.5–8.8 s (the flood), 41.5,
  57.85, 57.95 s.
- Voice: pitch movement measured per take, and a Whisper read-back of the used audio matched the script
  (`VOICEOVER.md`). **Not heard by anyone**: tone and pronunciation are measured, not listened to.
- Render numbers: see the delivery note in the commit / reply (loudness measured on the file).

## Weakest shot

S2 → S3, the beige flood: it starts on the real lit beige panel of the side render, but for its first
2–3 frames it is a flat box on that panel. With more time: push in toward the panel before it floods.

## Kept on purpose

- `line_unread` on "99 Speedmart / Tropicana Aman · 4.3 km": the check counts 1.8 s because its "6 MIN"
  lands beside it on the spoken number; the text itself stays on screen 4.4 s.
- S3 and S4 leave the bottom ~35% of the frame empty: the platform UI zone on TikTok / Reels / Shorts.
- The satellite credit on the map is 20 px (`data-layout-ignore`), as an imagery credit.

## Shots (film time, v2)

| Time | Scene | Voice | Screen |
|---|---|---|---|
| 0.00–6.23 | s1-hook | Rumah berkembar setingkat, kat Telok Panglima Garang... dah buka pendaftaran! | Front render, dolly; badge, title, location; DARI RM485,700 sticker at 1.2 s; badge pops on "pendaftaran" |
| 6.23–9.10 | s2-unit | Tapi jangan tunggu lama, lapan unit je tau! | HANYA 8 (lands on "lapan") UNIT SAHAJA; beige panel floods |
| 9.10–18.07 | s3-pakej | Booking? Seribu ringgit je. Legal fee SPA, free. Disbursement, free. Rumah pertama? MOT pun free! | RM1,000 counts up; FREE rows on their words |
| 18.07–26.43 | s4-pelan | Empat bilik, dua bilik air. Tanah, 2,814 kaki persegi. Binaan, 1,266. | Plan; facts wipe on as spoken, numbers count while spoken |
| 26.43–32.15 | s5-tapak | Leasehold, Rizab Melayu. Dijangka siap hujung tahun 2027. | IMG_1308; two cards on their words |
| 32.15–42.71 | s6-peta | (1.7 s lead) Nak ke Shah Alam? 23 minit. KLCC, 42 minit. SKVE, KESAS, WCE, semua dekat. | Satellite pull-back; cities pop as named; highway card on "SKVE" |
| 42.71–48.95 | s7-dekat | Sekolah? Lima minit je. 99 Speedmart, enam minit. Eco Sanctuary, sembilan minit. | Names land on the name, minutes on the number |
| 48.95–58.10 | s8-cta | Harga dari 485,700. Booking seribu je... jom, hubungi saya sekarang! | Price on "empat"; booking line; phone card on "hubungi"; 2 s hold |

## How to run

```bash
npm install                                          # hyperframes@0.9.17 (pinned)
scripts/pipit/prepare_media.sh /path/to/originals    # IMG_1307/1308.MOV, IMG_1431-1433.JPG
# the baked map (map-pullback.mp4) is also not in git: BAKE_MAP=1 rebakes it (needs network)
cd pipit && npx hyperframes preview                  # Studio
npx hyperframes render --quality delivery -o renders/pipit-berkembar-vo.mp4
# voiceover (already in assets/audio): python3 -I scripts/pipit/voiceover.py OUT_DIR  (see VOICEOVER.md)
```
