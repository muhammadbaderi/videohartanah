# Edit: Teres 1 Tingkat, Persiaran Masjid Sultan, Pulau Indah (IMG_1360.MOV)

Status: **PREVIEW v2**. The final file has not been rendered yet. The only render is a low-quality draft
(`video/renders/PREVIEW-v2-draft-pulau-indah.mp4`, not in git) for checking on a phone.

v2 changes (requested): the voiceover is enhanced and no longer monotone, and the opening text is smaller.
- **Voice**: regenerated with `eleven_v3` and audio tags that follow the story (serious hook, confident answer,
  warm location, excited price/package, urgent CTA). Measured pitch variation went from 2.5 to 3.5 semitones
  (range 5 → 11 st). Then `enhance_vo.py`: tighter pauses (from the audio's own silence), tempo ×1.12
  (rubberband, pitch kept), EQ (warmth +2 dB at 170 Hz, mud −2.5 dB at 380 Hz, presence +2.5 dB at 3.3 kHz,
  air), de-esser, compressor, and every clip at −16 LUFS / −1.5 dBTP (v1 clips varied from −19 to −23.5 LUFS).
- eleven_v3's own timestamps are off by about 0.2 s (up to 1.7 s), so word timings are now measured on the final
  audio with Whisper (`align_vo.py`); 169 of 174 words match directly, and the other 5 are interpolated.
- **Opening text** about 35% smaller (FREEHOLD 168 → 112 px, RM300K 228 → 148 px, MASIH WUJUD? 230 → 150 px,
  WUJUD. stamp 190 → 124 px), and the captions went from 66 to 60 px.
- The music bed is extended by two bars (seamless repeat at 47.1 s) so it runs under the whole CTA.

- Source: `IMG_1360.MOV` (iPhone 4K SDR, portrait, 92.3 s) + `IMG_1425.JPG` (floor plan, S&P Lot 144856)
- Edit: 1080×1920, 30 fps, **80.5 s** (77.3 s of voice + a 3.2 s end card)
- Voice: ElevenLabs **"Mad Serious"** (`SZ0xfPd6MASL0W36QxnX`), `eleven_v3` with audio tags, enhanced (see above)
- Location: Google Maps pin 2.919219, 101.301938

## Transcript of the original audio (Whisper large-v3)

| Source (s) | Spoken | Used? |
|---|---|---|
| 5.2–9.4 | "Ok, kalau korang nak cari rumah teres termurah di Pulau Indah…" | Used as the **hook idea** (rewritten) |
| 9.4–19.2 | "…korang boleh consider rumah ni. Rumah ni berharga daripada RM290,000 sahaja. Ada 3 bilik tidur dan 2 bilik air." | Facts only |
| 19.2–30.7 | "Ok, rumah dia pun… dah siap… dari segi… secara kasarnya structure dia dah siap." | Cut (stammering, repeats); kept as "Struktur dah siap" |
| 30.7–42.2 | "Kita masuk kawasan ni… living hall dia… memanjang. So porch ni boleh masuk 2 biji kereta." | Facts only |
| 42.2–57.5 | "Jom kita ke belakang. Ok sebelum tu… master bedroom… master bathroom." | Cut ("ok sebelum tu", 1.9 s pause) |
| 57.5–73.3 | (9 s pause) "…kitchen dengan dining area. So tempat dia agak privacy sikit lah kitchen dia." | Pause cut; fact kept |
| 74.6–83.8 | "Bilik nombor 2 dan 3… kawasan belakang lebih kurang dalam 3 ke 5 kaki" | Rooms kept; "3 ke 5 kaki" not used (unclear) |
| 85.1–90.4 | "Ok kalau korang berminat… contact saya di 016-370 8908" | Replaced by the CTA |

The original voice is **replaced** by the ElevenLabs voiceover, so the fillers ("ok", "so"), the stammering and the
long pauses (up to 9 s) are gone. The two selfie shots (6–11 s, 87–90 s) are not used, because the new voice would
not match the lips.

## Storytelling script (hook → answer → location → walkthrough → status → offer → CTA)

| # | Edit (s) | Voiceover | Picture / graphics |
|---|---|---|---|
| Hook | 0.0–5.2 | Rumah teres freehold di Pulau Indah, harga bawah tiga ratus ribu. | Row of houses, push-in. Kinetic text: RUMAH TERES **FREEHOLD** (boom) → 📍 DI PULAU INDAH → HARGA BAWAH **RM300K** (impact) |
| Hook | 5.2–6.3 | Masih wujud ke? | Darkened freeze frame, **MASIH WUJUD?** (boom), riser into the answer |
| Answer | 6.3–9.4 | Wujud. Dan saya tengah berdiri depan dia sekarang. | White flash, walk-up to the porch, **WUJUD.** stamp, ● SITE VISIT badge |
| Location | 9.4–23.2 | Projek perumahan baru, di Persiaran Masjid Sultan, Pulau Indah. Sekolah, masjid, klinik, semua dekat. Halal Hub dan kawasan industri, sebelah je. Nak keluar? Kesas, SKVE, WCE, semua dah sedia. | **Satellite map**: zoom in, pin drops on the project, 6 amenity chips pop with the words, then zoom out to the region (Klang, Pelabuhan Klang) and highway chips |
| Lot | 23.2–28.1 | Teres setingkat. Tanah 20 x 64 kaki. Porch, muat dua kereta. | **Floor plan** (redrawn from the S&P plan) + cards: TERES 1 TINGKAT, 20' × 64' counter with dimension lines, 2 cars drop into the porch |
| Tour | 28.1–41.2 | Masuk je, ruang tamu memanjang. Lapang. / Bilik utama, siap dengan bilik air sendiri. / Dapur dan ruang makan di belakang, terpisah dari ruang tamu. Lebih privasi. / Tiga bilik tidur, dua bilik air. Cukup untuk satu keluarga. | The plan shrinks to the corner and **highlights each room** as it appears; room labels; LEBIH PRIVASI badge; 3 BILIK TIDUR · 2 BILIK AIR |
| Status | 41.2–46.6 | Struktur dah siap. Dijangka siap sepenuhnya, Q3 2027. | Back yard; status card ✓ STRUKTUR SIAP → **Q3 2027** |
| Price | 46.6–55.1 | Harga asal RM299,500. Sekarang, dari RM290,500 je. | Red strike on the old price, the price counts down to **RM290,500** (ka-ching), JIMAT RM9,000 |
| Package | 55.1–65.2 | Booking RM500. Legal fee SPA, legal fee loan, duti setem, MOT, semua percuma. | Checklist ticks with the words, **SEMUA PERCUMA** stamp |
| Cashback | 65.2–68.6 | Pembeli terawal, dapat cashback RM11,000. | **RM11,000** counter, coin burst (ka-ching + sparkle) |
| CTA | 68.6–80.5 | Freehold. Rizab Melayu. Unit terhad. WhatsApp saya sekarang, 016-370 8908. | Tags FREEHOLD / RIZAB MELAYU / UNIT TERHAD, **WhatsApp card**, digits appear with the voice, end card "JOM SITE VISIT" |

Details left out on purpose (to keep it short): the full facility list beyond the 6 chips (SRA is on the school chip;
Pos Malaysia, Star Cruise Terminal, Laguna Park, Aeon Bukit Tinggi and GM Klang are not shown), and SHAPADU / Lebuhraya
Pulau Indah are only shown as chips, not spoken.

## Check these before the final render

1. **"Masjid Sultan Abdul Aziz"**: taken from your list as written.
2. **"Teres setingkat"**: Whisper heard it as "teres tertingkat", which is normal for this phrase. Listen at 23.3 s.
3. **"Rizab Melayu"**: the clone says it a little like "Rizal". Listen at 69.3 s (in v2 Whisper hears it correctly). It can be regenerated.
4. **JIMAT RM9,000** is calculated (299,500 − 290,500); it is not in your package list. Remove it if you don't want it.
5. **Phone number 016-370 8908**: on the WhatsApp card and in the voice.
6. **The map**: the pin is your Google Maps pin. The imagery is from Esri (credit shown, bottom left) and may be
   older than the project, so the site can look like empty land.
7. **The hook claim "bawah RM300K"**: comes from the RM290,500 price.

## Audio

- Voice: 16 ElevenLabs eleven_v3 clips (`vo/*.mp3`, raw) → enhanced `vo/*.wav`. The word timings (`vo/*.words.json`,
  measured with Whisper) drive the captions and every graphic cue. `*.align.json` is ElevenLabs' raw alignment (not used).
- Music: generated with ElevenLabs Music for this edit (`music-bed-orig.mp3`, dark piano and 808, about 80 BPM), extended
  by two bars with `extend_music.py` (`music-bed.mp3`). It starts on "Wujud." at 0.16 under the voice and lifts on the end card.
- SFX: 58 cues. The HyperFrames library sounds are reused from the Meru project (`sfx/CREDITS.md`). boom, kaching,
  riser, stamp and pin were generated with ElevenLabs Sound Effects.

## How to run

```bash
npm install                                                    # hyperframes@0.9.17 (pinned)
pulau-indah/scripts/prepare_media.sh /path/to/IMG_1360.MOV     # footage (not in git, too big)
python3 -I pulau-indah/scripts/build.py                        # regenerate index.html + compositions/
cd pulau-indah/video && npx hyperframes preview                # Studio
npx hyperframes render --quality delivery -o renders/FINAL-teres-pulau-indah.mp4   # FINAL, only after approval
```

- `scripts/vo_script.json` is the script. `{spoken|display}` means the voice reads the first part and the captions show
  the second, and `[serious]`-style tags set the eleven_v3 delivery. To change a line: edit it, then run
  `make_vo.py <id>`, `enhance_vo.py <id>` and `align_vo.py <id>` (all in `pulau-indah/scripts/`, run with `python3 -I`), then `build.py`.
- `scripts/make_map.py` rebuilds the satellite maps.
- **Warning:** `build.py` overwrites `video/index.html` and every file in `video/compositions/`.
