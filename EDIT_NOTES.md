# Edit: Site visit teres setingkat, Meru (IMG_0725.MOV)

Status: **PREVIEW**. The final render has not been made; it's waiting for your approval.

- Source: `IMG_0725.MOV`, iPhone 4K HDR (Dolby Vision/HLG), portrait, 87.6 s
- Edit: 1080×1920, 30 fps, **61.3 s** (58.9 s of speech + a 2.4 s end card)
- Edited in HyperFrames (`video/`), with the cut list in `scripts/edl.json`

## Things to confirm before the final render

1. **Street name.** The audio sounds like "Jalan **Nenas**, Meru" (Whisper also heard "Denas"). It's shown on the location pill and in the captions. You can change it in the Studio *Variables* panel (`location`) and in `video/compositions/captions.html`.
2. **"dia privasi sikit"**: Whisper heard this as "practice" / "privacy". I chose **privasi** to fit the "jaga aurat" context. If you actually said "praktikal", let me know.
3. **"Selalunya orang kita ni nak jaga aurat"**: Whisper wrote "selanjutnya", but in context it should be "selalunya".
4. **"20 × 67"**: shown as "Keluasan lot (kaki)". The unit isn't said in the audio.
5. **Phone number 016-370 8908**: checked in 3 separate transcription passes, all consistent.
6. **Music**: no background music yet (there's no music source in this environment). Send me a track or sign in to HeyGen (free) for the music library.

## Hook

The video opens with the strongest selling point, said to camera:
> "Selalunya orang kita ni nak jaga aurat, okey lah untuk rumah ni."

The on-screen title from frame 0 reads **"Rumah ni sesuai untuk yang JAGA AURAT"** (with a yellow highlight on "jaga aurat"). The answer comes near the end: *"living hall tak bersambung dengan area dapur"*, with the LIVING HALL ✕ DAPUR diagram. Viewers have a reason to watch until the end.

## What was cut

| Cut | Why |
|---|---|
| "Ok," / "So," at the start of many sentences | fillers |
| "So, living hall dia tu…" | repeats "living hall" |
| "So, master bedroom." | repeats "master bedroom" |
| "Nampak dah ada tu, lampu." | repeats "lampu", stumbles |
| Pauses 0.4–2.5 s (14 places: before "dapur", after "bathroom", between rooms, etc.) | awkward pauses |
| Camera flip 13.5 s and 67.3 s (blurry) | covered with a white flash + whoosh |
| "Ok, bye bye" (clipped at the end of the file) | replaced with the end card |

The "jaga aurat" sentence was **moved** to the front as the hook (not duplicated).

## Edited timeline

| Edit (s) | Source (s) | Speech | Graphics / SFX |
|---|---|---|---|
| 0.00–5.34 | 72.16–78.20 | Selalunya orang kita ni nak jaga aurat, okey lah untuk rumah ni. | Hook title, yellow highlight on "jaga" (pop) |
| 5.34–16.21 | 0.58–13.52 | Hai, Assalamualaikum… Jom kita tengok teres setingkat. | Flash + whoosh; 📍 location pill; "Projek perumahan baru"; chips Teres Setingkat / Semi-D |
| 16.21–17.51 | 14.25–15.55 | (site shot) | Title "JOM TENGOK TERES SETINGKAT" (whoosh) |
| 17.51–22.25 | 15.86–20.60 | 4 bilik tidur, 2 bilik air, 20x67 | 3 stat cards, the lot size counts up (pop ×3) |
| 22.25–29.71 | 21.80–33.36 | Living hall, ceiling 15 kaki, tingkap, sliding door | LIVING HALL label; **dimension line 0→15 KAKI** over the room-corner shot (ping); chips |
| 29.71–34.75 | 34.16–41.96 | Master bedroom, point lampu & kipas | Label; checklist ✓ Lampu ✓ Kipas |
| 34.75–41.39 | 44.94–55.12 | Master bathroom, belum pasang, bilik air 2 | Label; note "belum dipasang"; BILIK AIR 2 |
| 41.39–45.95 | 57.20–61.76 | Bilik 2, 3, 4 + kitchen | Number badges 2·3·4 pop with the speech; "+ Dapur" |
| 45.95–53.32 | 63.36–79.60 | Privasi… living hall tak bersambung dengan area dapur. Senang sikit. | Diagram LIVING HALL ✕ DAPUR (bass impact on "tak"), badge ✓ SENANG JAGA AURAT |
| 53.32–61.32 | 81.28–87.30 | Kalau berminat… contact saya di 016-370 8908 | BERMINAT?; phone card, digits appear with the speech; end card |

The B-roll was rearranged where needed: the room-corner shot sits under "ceiling 15 kaki", and the master bedroom reveal sits under "ni master bedroom dia".

## Audio

- Voice: high-pass 85 Hz, light noise reduction, gentle compression, loudness **-16 LUFS / -1.5 dBTP**. Preview measured at -16.7 LUFS, true peak -2.7 dB, no clipping.
- SFX: 36 cues from the bundled HyperFrames library (Pixabay licence, attribution not required: `video/assets/sfx/CREDITS.md`). Every sound has a cause on screen, and each one lands one frame after its picture.

## How to run

```bash
npm install                                    # hyperframes@0.9.17 (pinned)
scripts/prepare_media.sh /path/to/IMG_0725.MOV # footage + voice (not in git, too big)
cd video && npx hyperframes preview            # Studio: http://localhost:3002/#project/video
npx hyperframes render --quality delivery -o renders/final.mp4   # FINAL, only after approval
```

`scripts/build.py` regenerates `video/index.html` and `video/compositions/captions.html` from `scripts/edl.json`.
**Warning:** it overwrites any edits made to those two files in Studio. The scene files `compositions/g-*.html` are not touched.
`scripts/align_captions.py` regenerates the caption word timing (needs `faster-whisper`).
