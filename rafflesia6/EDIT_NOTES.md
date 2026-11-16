# Edit: Taman Rafflesia 6, Seksyen 29 Shah Alam (IMG_1073.MOV)

Marketing video, 1080×1920, 30 fps, **56.6 s**. Blue theme (navy `#061636`, royal blue `#1d5cff`, sky `#5cc2ff`, ice `#e6f2ff`),
Montserrat for headings and numbers, Inter for small text.

- Source: `IMG_1073.MOV` (iPhone 4K SDR, portrait, 127.8 s) from Google Drive. Only the pictures are used.
- Voice: a script read by the owner's cloned voice on ElevenLabs (not the voice recorded in the clip).
- Render: `renders/rafflesia6-v1.mp4` (not in git, too big).

## Script (voiceover)

| Film (s) | Line | On screen |
|---|---|---|
| 0.00–4.21 | Cari rumah teres setingkat kat Shah Alam, bawah lima ratus ribu? Jom tengok! | Hook from frame 0: "Rumah Teres 1 TINGKAT bawah RM500K?", blue marker on the price |
| 4.41–11.19 | Projek baru, Taman Rafflesia 6, Seksyen 29, Shah Alam. Terhad 19 unit je! | Location card; badge "TERHAD 19 UNIT SAHAJA" counting up |
| 11.44–19.09 | 4 bilik tidur, 2 bilik air. Tanah 21 × 68, binaan 924 kaki persegi. | Two stat cards; lot plan drawn to scale (21' × 68' land, 21' × 48' built-up) |
| 19.24–21.81 | Porch muat 2 kereta, siling pun tinggi. | PORCH: 2 KERETA (two car icons); SILING TINGGI |
| 22.11–31.97 | Harga dari 455 ribu. Booking RM500 je, free legal fee SPA, dan free MOT untuk pembeli rumah pertama. | Price counts up to **RM455,120**; package with 3 ticks |
| 32.27–41.56 | Dekat Quayside Mall Rimbayu, Saujana Putra dan Kota Kemuning. Akses mudah ke ELITE, SKVE, KESAS dan LKSA. | Distance list (2.8 / 5 / 6 KM); 4 highway signs |
| 41.77–46.33 | Leasehold, Rizab Melayu. Siap suku pertama 2027. | Tags LEASEHOLD · RIZAB MELAYU; card DIJANGKA SIAP Q1 2027 |
| 46.63–54.45 | Unit terhad! Berminat? Contact saya di 016-370 8908. | "UNIT TERHAD!"; end card: your face, 016-370 8908, project name, price |

Not in the video (too much for under a minute): the schools, the mosques, Tropicana Aman, Putra Perdana, Subang Jaya.
They are in the post caption (`POST_CAPTION.md`).

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
python3 -I scripts/rafflesia6/build.py                  # regenerates index.html + captions.html
cd rafflesia6 && npx hyperframes preview                # Studio
npx hyperframes render --quality delivery -o renders/rafflesia6-v1.mp4
```

- Change a word in the voiceover: edit `scripts/rafflesia6/vo_lines.json`, run `python3 -I scripts/rafflesia6/tts.py <line id>`
  (ElevenLabs credits), redo the 1.05x + loudness step (see `assets/audio/CREDITS.md`), adjust `edl.json` timings, then `build.py`.
- **Warning:** `build.py` overwrites `index.html` and `compositions/captions.html`. The scene files `compositions/g-*.html` are not touched.
