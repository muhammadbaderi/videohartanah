# Edit notes: Rumah Berkembar 1-Tingkat, Pulau Indah (Hyperframes, Vox / poster style)

Source: `IMG_1365.MOV`, 19.9 s, iPhone HLG HDR, portrait, tone-mapped to SDR Rec.709 (Hable).
Floor plan: JPEG from Drive, cropped to `assets/img/pelan-crop.png`.
Edit: **34.4 s**, 1080×1920, 30 fps.

## Transcript (source)

| Source | Speech | Decision |
|---|---|---|
| 0.0–3.1 | silent B-roll: row of houses, road still under construction | Reused for the "Dijangka siap Q1 2027" beat |
| 3.1–4.3 | "Hello hai assalamualaikum. Ok" | **Cut** (weak hook + filler) |
| 4.98–7.80 | "Sekarang ni saya di projek perumahan" | Keep |
| 7.80–8.28 | pause | **Cut** |
| 8.28–10.45 | "Semi-D setingkat di Pulau Indah" | Keep → **moved to the front (hook), over B-roll** |
| 10.45–12.05 | pause + "Ok" | **Cut** |
| 12.05–13.25 | "Kita tengok rumah dia" | Keep → transition into the tour |
| 13.3–19.9 | silent B-roll: finished houses (pan) | B-roll for the info cards (slowed 0.43–0.6×) |

## Story (hook first)

1. **0–3.6 HOOK.** Finished-house B-roll plus the voice "Semi-D setingkat di Pulau Indah". The poster card is readable at frame 0: PROJEK PERUMAHAN BARU / Rumah Berkembar 1-Tingkat / Harga dari **RM385,000**. The location appears on "Pulau Indah".
2. **3.6–7.6 TALK.** Yellow wipe, then the face: "Sekarang ni saya di projek perumahan… kita tengok rumah dia". Word-by-word captions, punch-in on "projek perumahan".
3. **7.5–12.4 PELAN LANTAI.** A paper page slides up. The real floor plan, with the neighbouring unit faded; bedrooms counted 1→4 (soft ticks), both bathrooms, *Luas binaan 24'×39' · 1,178 kps*.
4. **12.2–16.8 PILIHAN UNIT.** RB1 (2 unit) vs RB2 (26 unit): land size and price.
5. **16.7–21.5 PAKEJ.** FREE Legal Fee SPA · FREE MOT Fee · Pinjaman Kerajaan 100% (ikut kelayakan), with FREEHOLD and RIZAB MELAYU tags.
6. **21.5–24.3 STATUS.** Yellow wipe → under-construction row: *Dijangka siap Q1 2027*.
7. **24.1–29.6 LOKASI.** Access: KESAS, SKVE, WCE, Lebuhraya Pulau Indah. Nearby: SK/SMK/SRA, Masjid Sultan Abdul Aziz, Klinik Kesihatan, Selangor Halal Hub.
8. **29.6–34.4 END CARD.** Riser → impact: **HARGA DARI RM385,000** + FREEHOLD · RIZAB MELAYU · SIAP Q1 2027 (held 4.6 s).

### Information left out (to keep it short)
Surau Haji Omar, 99 Speedmart, Segi Fresh, Pos Malaysia, Pulau Indah Industrial Park, Star Cruise Terminal, Laguna Park, Lebuhraya SHAPADU. These can be added back on the Lokasi page if needed.

## Design (poster rules)
- One grid: 72 px margin, everything left-aligned in a 936 px column, text inside the 168–1330 px safe band (clear of the TikTok/Reels UI).
- Three type levels: kicker 28 px (tracked), body 30–38 px, headline 52–68 px; price 64 px (hook) and 88 px (end, the only payoff). Smaller than the previous edit.
- Two typefaces: Archivo Black (headlines and numbers) + Outfit (text).
- Colours: paper #F4EFE4, ink #161616, yellow highlighter #FFD84D only on what matters (price, Q1 2027, 1,178 kps, keywords).

## Audio
Voice: highpass + light denoise + loudnorm. SFX are bundled Pixabay files, each tied to a visual action. Mix: −18.3 LUFS integrated (low because the tour has no voice), true peak −1.4 dBTP, no clipping. Measured, not listened to.
**No music yet**: the 26 s info section feels empty without it. The HeyGen music catalog needs `npx hyperframes auth login`, or provide your own track.

## Commands
```bash
cd edit2
npx hyperframes preview
npx hyperframes check
npx hyperframes render -q high -o final.mp4   # FINAL render: only once approved
```
