# Review: Rumah Berkembar 1-Tingkat, Jalan Pipit (Telok Panglima Garang)

Status: **FINAL rendered** (2026-11-15): `renders/pipit-berkembar-final.mp4`, 1080×1920, 30 fps, 53.55 s.
The render and the large footage are not in git; rebuild with `scripts/pipit/prepare_media.sh` and the
render command at the bottom.

## Creative calls

- **Storyline A** from `STORYLINES.md` ("Rumah dulu, baru tawaran"): house + price → 8 units only →
  package → floor plan + sizes → site → map → places nearby → end card. Not built: B "RM1,000"
  (the number as the hook) and C "Dari langit" (one satellite dive). Both are in `STORYLINES.md`.
- **No voiceover, no captions**: the source has no speech. Text and music carry it.
- **Music**: the same warm acoustic HeyGen catalog track as the Meru video (no sign-in was needed,
  it was already in the repo), entered at its section C so its own ending lands under the end card.
- **Phone number 016-370 8908** on the end card is taken from the Meru video (it was not in this
  brief). It is a variable (`phone` on the `s8-cta` scene); change it in Studio if this listing
  uses another number. The price is a variable there too (`price`).
- **Amenities shown** (7 of the 13 listed + 10 access points, to stay under a minute): SK / SRA Kebun
  Baharu 5 min, 99 Speedmart Tropicana Aman 6 min, Eco Sanctuary 9 min, Columbia Asia Bkt Rimau 19 min;
  on the map Shah Alam 23 min, Putrajaya 41 min, KLCC 42 min, plus SKVE / KESAS / WCE / LKSA.
  Everything else in the brief was left out, not changed.
- **Map**: real Esri satellite imagery around the map pin (2.924945, 101.510804), baked once to video.
  The three city labels sit at projected real coordinates (`assets/footage/map-pullback-points.json`);
  the city coordinates themselves are the city centres I used (KLCC tower, Shah Alam centre,
  Putrajaya core), so each label is within a couple of km of the place.
- **Site clips** are shown without a caption saying where they were filmed; the brief did not say.
  The "Dijangka siap Q4 2027" card sits over IMG_1308, which shows nearly-finished houses: if those
  houses are not this phase, swap that card onto a render.
- **"4 Bilik"** is the developer's copy. The floor plan labels 3 bedrooms + a store; the video does
  not point at rooms on the plan, so the two don't contradict on screen.

## Measured vs looked at

- `npx hyperframes check`: 0 errors, 0 warnings (lint, runtime, layout, contrast, craft, audio).
- Looked at: the beat sheet, all 7 seams, the phone sheet, and frames at 6.75–7.2 s (the flood),
  13.5, 23.5, 36.5, 44.5, 52, 53.3 s.
- Rendered file: 53.57 s, H.264 1080×1920 30 fps + AAC, 88 MB (`-share.mp4` copy: 24 MB, CRF 21).
  Frames pulled from the MP4 at 0, 7, 12.5, 21.5, 27.5, 33, 36.8, 42.5, 51 s match the Studio snapshots
  (fonts, baked map playing, labels in place).
- Audio, measured on the rendered file, **not heard**: -14.1 LUFS integrated, true peak -1.1 dBTP,
  no clipping. Loudest moment is the bass hit under the price at 47.3 s (short-term -9.3 LUFS), on purpose.

## Weakest shot

S2 → S3, the beige flood: it starts from the real lit beige panel on the side render, but for its first
2–3 frames it reads as a flat box on the panel. With more time: a push-in toward the panel before it
floods, so the eye is already on it.

## Kept on purpose

- S3 and S4 leave the bottom ~35% of the frame empty: that is the platform UI zone (captions,
  buttons) on TikTok / Reels / Shorts, so nothing readable goes there.
- The satellite credit on the map is 20 px (`data-layout-ignore`), as an imagery credit.

## Shots (film time)

| Time | Scene | What |
|---|---|---|
| 0.00–3.82 | s1-hook | Front render, dolly; DIBUKA UNTUK PENDAFTARAN, RUMAH BERKEMBAR 1-TINGKAT, Jalan Pipit; HARGA DARI RM485,700 sticker at 1.0 s |
| 3.82–7.63 | s2-unit | Side render; HANYA 8 UNIT SAHAJA (counts 1→8); beige panel floods the frame |
| 7.63–15.24 | s3-pakej | PAKEJ: BOOKING RM1,000 (counts up), FREE SPA Legal Fee, FREE MOT (pembeli rumah pertama), FREE SPA Disbursements |
| 15.24–24.77 | s4-pelan | Floor plan; 4 Bilik & 2 Bilik Air; 2,814 kps tanah (44' × 76.7'–78'); 1,266 kps binaan |
| 24.77–30.48 | s5-tapak | IMG_1308; LEASEHOLD Rizab Melayu; Dijangka siap Q4 2027 |
| 30.48–38.10 | s6-peta | Satellite: pin on Jalan Pipit, pull back; Shah Alam 23 / KLCC 42 / Putrajaya 41 min; SKVE KESAS WCE LKSA |
| 38.10–45.72 | s7-dekat | IMG_1307 dimmed; DEKAT DENGAN 5 / 6 / 9 / 19 min |
| 45.72–53.55 | s8-cta | Front render; HARGA DARI RM485,700; Booking RM1,000 · 8 unit sahaja; HUBUNGI SAYA 016-370 8908 |

## How to run

```bash
npm install                                          # hyperframes@0.9.17 (pinned)
scripts/pipit/prepare_media.sh /path/to/originals    # IMG_1307/1308.MOV, IMG_1431-1433.JPG
# the baked map (map-pullback.mp4) is also not in git: BAKE_MAP=1 rebakes it (needs network)
cd pipit && npx hyperframes preview                  # Studio
npx hyperframes render --quality delivery -o renders/pipit-berkembar-final.mp4
```
