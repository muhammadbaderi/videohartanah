# Script and voice

## The voice

- ElevenLabs voice **"Mad Bi"**, id `j2h6UJwjLSvHhJaBXWtF` (the owner's own clone; an older clone
  "Suara sendiri (videohartanah)" `graVYRgsElnbev50WXQ2` also exists). The connected ElevenLabs key is injected by
  the proxy: send any placeholder in `xi-api-key`. If the owner names another voice, find it with
  `GET https://api.elevenlabs.io/v2/voices?search=<name>` and put its id in `vo_lines.json`.
- Model **`eleven_v3`**, stability 0.5, similarity 0.8, speaker boost, one audio tag in front of each line:
  `[excited]` for the hook, the price and the CTA, `[enthusiastic]` for the project intro, `[cheerful]` for specs and
  features, `[confident]` for location and tenure. The owner rejected the first video's voice as monotone
  (eleven_multilingual_v2): v3 with tags moves the pitch about twice as much (12-19 vs ~6 semitones/s).
  Lower v2 stability / higher style did not help.
- Natural speed (no tempo change). Processing (done by `pick_takes.py`): 70 Hz high-pass, 2.2:1 compression,
  +1.5 dB at 3.5 kHz, -16 LUFS / -1.5 dBTP per line, 48 kHz mono WAV.

## Writing the lines (`scripts/<name>/vo_lines.json`)

Each line has `id` (matches the scene `g-<id>`), `tag`, `say` (what is spoken) and `cap` (how it reads on screen).

- BM santai, short, like the owner talks on site: "je", "kat", "Jom tengok!". About 120-150 words for the whole
  video so it lands at 50-56 s with the end card.
- In `say`, write numbers and letters the way they must be spoken: "empat ratus lima puluh lima ribu",
  "dua puluh satu kali enam puluh lapan", "kosong satu enam, tiga tujuh kosong, lapan sembilan kosong lapan",
  "S P A", "M O T", "S K V E", "L K S A", "Elite", "Kesas". Round prices when speaking ("455 ribu"); the card
  shows the exact figure.
- `cap` uses digits and the listing's spelling (RM455,120, 21 x 68, SKVE, Q1 2027).
- `captions_src.json` maps each caption chunk's tokens to the index of the spoken word in `say` where it starts
  (e.g. `["21", 7]` covers "dua puluh satu"). If you change a line's words, update its chunks. The hook has no
  captions (its title says it) and the CTA captions stop before the phone number (the card shows it).
- The CTA line is split after "Berminat?" (`edl.json` `split`) so the end card can arrive with "Contact saya".

## Making and choosing takes

```bash
python3 -I scripts/<name>/tts.py --takes 3            # all lines, 3 takes each (about 2,700 characters of credit)
python3 -I scripts/<name>/tts.py --takes 3 price cta  # only these lines
pip install faster-whisper praat-parselmouth          # once per container
python3 -I scripts/<name>/pick_takes.py               # prints every take's score, keeps the best
python3 -I scripts/<name>/build.py
```

`pick_takes.py` transcribes each take with Whisper (place names in the prompt) and scores it against `cap`
(are the words right?), then by pitch movement (is it lively?). Read its printout: it shows what Whisper heard
for every take. A word heard wrongly in all three takes (e.g. "teres setingkat" as "teras tingkat") is worth a
re-roll of that one line, or a respelling in `say`; mention it to the owner either way.
