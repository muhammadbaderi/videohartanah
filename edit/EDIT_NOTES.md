# Edit notes: Semi-D Pulau Indah (Hyperframes, Vox style)

Source: 15.0 s selfie video, 2160×3840 (Google Drive `1-445njOhhGo45_EdiOfJMyrWzz5hUqxt`).
Edit: **9.0 s**, 1080×1920, 30 fps.

## Transcript (original, Whisper large-v3, ms)

| Time (src) | Speech | Decision |
|---|---|---|
| 0.00–1.32 | "Hello, hai, assalamualaikum" | **Cut**: greeting, weak hook |
| 1.32–2.06 | "Ok," | **Cut**: filler |
| 2.08–4.80 | "kali ni kita tengok lagi satu projek di Pulau" | Keep (beat 4) |
| 4.80–5.08 | pause in the middle of "Pulau… Indah" | **Cut** |
| 5.08–6.32 | "Indah" | Keep (beat 5) |
| 6.32–7.04 | silence 0.7 s | **Cut** |
| 7.02–7.58 | "Semi-D" | Keep → **moved to the front (hook)** |
| 7.58–8.00 | silence | **Cut** |
| 8.00–9.06 | "Kali ni" | **Cut**: repeats "kali ni" |
| 9.06–9.92 | "lebar dia" | Keep (beat 2) |
| 9.92–10.82 | hesitation / dead air | **Cut** |
| 10.82–12.88 | "41 x 60" | Keep (beat 3, payoff) |
| 12.88–14.97 | "Ok" + ending | **Cut** (0.75 s of ambience reused as the end-card tail) |

## New order (hook first)

> **"Semi-D. Lebar dia 41 x 60."** → "Kali ni kita tengok lagi satu projek di Pulau Indah."

The hook opens on the product and a number; the context (location) comes after.

## Timeline (output)

| Out | Visual | Motion graphic | SFX |
|---|---|---|---|
| 0.00–0.56 | Face punch-in 1.14× | **SEMI-D** title on a yellow highlighter, already on screen at frame 0 (thumbnail) | impact-bass |
| 0.56–1.42 | Jump cut, punch out 1.0× | "lebar dia…" paper label, word by word | — |
| 1.28–1.68 | Camera shrinks into a tilted paper card | Grid paper revealed | whoosh |
| 1.42–3.48 | Card at bottom left | **Land diagram drawn to scale (60×41)**: "41 kaki" lands on "41", "60 kaki" on "60", big **41 × 60** text | pop ×2 |
| 2.80 | — | Hatched area + **2,460 kaki persegi** | soft click |
| 3.48–4.17 | "kali ni kita tengok" starts in the card, card opens back to full frame | Caption | cinematic whoosh |
| 3.40–7.62 | Full frame, punch on "projek" | Word-by-word captions, keywords highlighted yellow | — |
| 6.26–9.00 | Punch-in 1.16× on "Indah" | **📍 PULAU INDAH** card, Klang, Selangor, chips SEMI-D / 41' × 60' | pop (pin), sparkle (highlighter) |

Audio: highpass + light denoise + loudnorm on the voice; mix measured at −14.6 LUFS, true peak −1.2 dBTP (no clipping). No music yet.

## Assumptions to confirm

- "41 x 60" is read as **feet** (41' × 60' → 2,460 sq ft). If the units are different, change `compositions/plot.html` and `compositions/place.html`.
- "Pulau Indah" → subtitle "Klang, Selangor".

## Commands

```bash
cd edit
npx hyperframes preview      # Studio preview
npx hyperframes check
npx hyperframes render -q high -o final.mp4   # FINAL render: only once approved
```
