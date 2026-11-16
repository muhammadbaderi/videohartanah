# Audio credits

- `vo-*.raw.mp3`: voiceover generated with ElevenLabs **`eleven_v3`** (stability 0.5, an audio tag such as `[excited]` per line)
  in the owner's cloned voice "Suara sendiri (videohartanah)" (voice id `graVYRgsElnbev50WXQ2`), one file per line of
  `scripts/rafflesia6/vo_lines.json`; each line is the best of 3 takes (Whisper accuracy, then pitch movement).
- `vo-*.wav`: the same takes at natural speed, 70 Hz high-pass, gentle compression (2.2:1), +1.5 dB presence at 3.5 kHz,
  loudness-normalised to -16 LUFS / -1.5 dBTP, 48 kHz mono.
- `music-bed.mp3`: HeyGen music catalog, track id `e819a5365f1c48608d631e6c99191c2c` (same track as the Meru video,
  see `video/assets/audio/CREDITS.md`). Used from 27.64 s (beat 58), so the track's last chord lands just after the voice ends.
- Sound effects: see `../sfx/CREDITS.md` (Pixabay Content License).
