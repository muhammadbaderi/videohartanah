# Mode A: edit the owner's own walkthrough (their real voice)

The first video in this repo (`video/`, "Teres setingkat, Meru", IMG_0725.MOV, Nov 2026) was made this way:
the owner talks to camera while walking the house, and the edit keeps their own voice. Use this mode when the
owner says "guna suara aku dalam video", the clip is mostly them talking clearly, or there is no listing text
to script from. Use Mode B (scripted voiceover in the cloned voice "Mad Bi", the default since Rafflesia 6) when
they send a listing to read out, the clip's audio is wind/noise/silence, or they ask for a voiceover.

## Steps (files: `scripts/edl.json`, `scripts/build.py`, `scripts/align_captions.py`, `scripts/prepare_media.sh`)

1. **Media.** `scripts/prepare_media.sh clip.MOV`: iPhone 4K HDR (Dolby Vision/HLG) is tone-mapped to SDR
   (zscale + hable) and scaled to 1080x1920 with a keyframe every 15 frames; the voice is cleaned (high-pass 85 Hz,
   light denoise, 2.5:1 compression) and normalised to -16 LUFS / -1.5 dBTP; the last frame is exported for the
   end card. Check `color_transfer` with ffprobe first: an SDR (bt709) clip needs only the scale.
2. **Transcribe** with faster-whisper large-v3 (`language="ms"`) with word timestamps, three passes for anything
   that matters (street names, phone number), and fix Malay mishearings from context ("selanjutnya" ->
   "selalunya", "practice/privacy" -> "privasi"). Put each decision in EDIT_NOTES so the owner can confirm.
3. **Cut list** (`scripts/edl.json` `segments`: `a_in`/`a_out` in source seconds, the corrected `text`, `sec` =
   the chapter, optional `v_in` to lay other picture under the same words, optional `punch` = scale for a punch-in).
   - Open with the strongest selling sentence said to camera, **moved** to the front (not duplicated), with a
     title on screen from frame 0 ("Rumah ni sesuai untuk yang JAGA AURAT"); the answer comes near the end, so
     the viewer has a reason to stay.
   - Cut fillers at sentence starts ("Ok,", "So,"), repeats, stumbles and pauses over ~0.4 s; cover camera flips
     with a white flash + whoosh; replace "Ok bye" with the end card.
   - B-roll goes under the words that name it (room-corner shot under "ceiling 15 kaki").
   - Aim for ~60 s.
4. **Facts.** Anything misspoken is cut from the voice and shown only on a card with the right value. In Meru the
   owner said "20x67" and corrected it to 20 x 82 afterwards: always ask when a number sounds odd, and show
   numbers on cards (lot size counting up, phone digits landing with the voice).
5. **Captions.** `scripts/align_captions.py` aligns Whisper's words to the corrected EDL text and snaps them to
   speech onsets; `build.py` groups them into 2-5 word chunks and skips the phone number (the CTA card shows it).
6. **Graphics, music, sound** as in Mode B (the Meru video used the yellow `#ffc83d` theme; since Rafflesia 6
   the owner wants blue: use `look.md`). Music at 0.14 under the voice, lifting where nobody speaks.

The Meru project is still in `video/` and builds with `python3 -I scripts/build.py`; copy its approach, not its
files, for a new talking-head edit (its scripts are hard-wired to `video/`).
