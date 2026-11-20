# Audio credits

- `vo-*.raw.mp3`: voiceover generated with ElevenLabs **`eleven_v3`** (stability 0.5, similarity 0.8, an audio tag such as
  `[excited]` per line) in the owner's cloned voice **"Mad Bi"** (voice id `j2h6UJwjLSvHhJaBXWtF`), one file per line of
  `scripts/nenasmeru/vo_lines.json`. Three takes per line; the take used is listed in `vo_lines.json` (`_takes`).
- `vo-*.wav`: the same takes at tempo 1.06 (pitch kept), 70 Hz high-pass, gentle compression (2.2:1), +1.5 dB presence at 3.5 kHz,
  loudness-normalised to -16 LUFS / -1.5 dBTP, 48 kHz mono (`scripts/nenasmeru/process_vo.py`).
- `music-bed.mp3`: composed for this video with **ElevenLabs Music** (`music_v1`, instrumental, 120 BPM, 62 s), prompt in
  `EDIT_NOTES.md`. Used from 9.285 s so its ring-out ends with the film.
