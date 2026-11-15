---
name: video-hartanah
description: Turn a property site-visit video into a vertical (1080x1920) Malay promo short with HyperFrames — storytelling script, ElevenLabs voiceover ("Mad Serious" by default), satellite location map, animated floor plan, kinetic captions, SFX, music and a WhatsApp CTA — and stop at a preview for approval. Use this whenever the user sends a Google Drive video link (often with a floor-plan image link, a Google Maps link and a block of project details like PAKEJ / Harga / Kemudahan / Akses Mudah) and asks to edit it, "edit video ni", "buat video hartanah/rumah", "macam video Pulau Indah", or wants a new property reel, even if they don't mention HyperFrames or this skill by name. Also use it to revise such an edit (VO tone, text size, timing, re-render).
---

# Video hartanah

Makes a 60 to 80 s property reel from one phone walkthrough. The house style and every default below were
settled with the owner on the Pulau Indah edit (`pulau-indah/` in this repo, the reference project).
Each new edit is a project folder with one `project.json`; the scripts in `scripts/` do the rest.

```
S=.claude/skills/video-hartanah/scripts      # run python with: python3 -I $S/<script>.py <project-dir> ...
```

## What the owner gives you, and the defaults to use without asking

The input is usually: Drive link to the video, Drive link to the floor plan (S&P plan image), Google Maps
link, and the project details (package, price, specs, facilities, highways), plus maybe the CTA number.

Defaults (they asked for these. Change one only when the new request says so):
- **Language**: Malay, casual-confident ("korang", "je").
- **Voice**: ElevenLabs voice **"Mad Serious"** (`SZ0xfPd6MASL0W36QxnX`, a cloned voice on their account),
  `eleven_v3` with audio tags, then enhanced. It must **not be monotone**: the first draft on
  multilingual_v2 was rejected for that. The voice replaces the presenter's own audio entirely.
  Talking-head selfie shots are dropped, because the new voice would not match the lips.
- **CTA**: WhatsApp **016-370 8908**, unless the request gives another number.
- **Opening text**: moderate sizes (see the hook in `references/project-json.md`). They asked for smaller
  text than the first draft.
- **Never render the final file until they approve.** "Preview dulu" means the Studio preview plus a
  `--quality draft` MP4 named `PREVIEW-…` that you send them to watch on the phone. That draft is not
  the final.

## Workflow

### 1. Fetch and look
```bash
SLUG=<area-or-project>                       # e.g. bandar-baru-klang
$S/new_project.sh $SLUG "Teres 2 Tingkat Bandar Baru Klang"
W=<scratchpad>/work-$SLUG                    # big files stay out of git
$S/fetch_inputs.sh $W "<video link>" "<floor plan link>" "<maps link>"
python3 -I $S/transcribe.py $W/source.* $W     # source.mov or .mp4
```
Then **read** `$W/sheet_*.jpg` (1 frame per second, stamped MMSS) and the floor plan image. Note what each
second shows: exterior, porch, each room, back, selfie, blur and whip pans. Note what the presenter says
and when. That decides which footage goes under which line.
If a Drive download returns HTML, the file isn't shared: ask the user to set "anyone with the link", or
fetch small files with the Google Drive connector.

### 2. Write the story (project.json → `lines`)
Turn the details into a story, not a spec list. The arc that worked:
1. **Hook** (≤ 6 s): the strongest claim, as a tease. "Rumah teres freehold di Pulau Indah, harga bawah
   tiga ratus ribu." then a question: "Masih wujud ke?"
2. **Answer**: "Wujud. Dan saya tengah berdiri depan dia sekarang." (proof: real footage)
3. **Location** (map): street + area; 3 to 6 nearby facilities in one breath; the highways.
4. **Walkthrough**: type and lot size, then each room in the order the footage shows them, one short line
   each, with one benefit (e.g. a kitchen separated from the living room = more privacy).
5. **Status**: built now / completion date.
6. **Offer**: old price → new price, package items, early-bird cashback.
7. **CTA**: tenure + urgency + "WhatsApp saya sekarang, <number>".

Keep only what sells. A list of 14 facilities becomes 6 chips plus one spoken line. Use facts only from
the user's details and the transcript. Anything you calculate (e.g. "JIMAT RM9,000") gets flagged to
the user. Write numbers as Malay words on the spoken side, and use tags and punctuation for energy (see
`references/project-json.md` §3). Aim for 140 to 170 spoken words.

### 3. Voice
```bash
python3 -I $S/make_vo.py $SLUG            # ElevenLabs, one MP3 per line (max 3 parallel requests on this plan)
python3 -I $S/enhance_vo.py $SLUG         # tighten pauses, tempo x1.12, EQ/de-ess/compress, -16 LUFS each
python3 -I $S/align_vo.py $SLUG           # word timings measured with Whisper; prints what it heard
```
Read the `align_vo.py` output: it is a pronunciation check. Re-generate (`make_vo.py $SLUG <id>`, then
enhance + align for that id) any line where a key word is wrong, after respelling it on the spoken side
(`Ri-zab`, `S.K.V.E`). "Teres setingkat" is often heard as "terace/trace tingkat" by Whisper even when
it sounds right: mention it, don't loop on it. `matched n/m` below ~90% means the line was cut or garbled.

### 4. Pictures, map, plan
```bash
$S/prepare_media.sh $W/source.* $SLUG   # 1080x1920 proxy + freeze/blur stills (set project.json "stills" first)
python3 -I $S/make_map.py $SLUG           # Esri satellite (OSM/CARTO tiles are blocked here)
```
Fill `shots` (with `max` for each take), `map`, and `scenes` in project.json. The floor-plan rooms are
measured from the plan image (method in the reference §6 plan). Shot rules: no blur/whip-pan frames, no
selfie frames, cut on words with `switch`, rooms under the line that names them, exterior under the hook,
and a dimmed exterior or interior under the price/package cards.

### 5. Build, music, check
```bash
python3 -I $S/build.py $SLUG              # prints total length, scenes and shots
python3 -I $S/make_audio.py $SLUG music   # music sized to the edit (SFX are bundled; "sfx" only regenerates)
python3 -I $S/build.py $SLUG
cd $SLUG/video && npx hyperframes check   # must say ok; fix warnings that matter (below)
npx hyperframes snapshot --at <t1,t2,...> --no-end -o <scratchpad>/snap
```
Read the snapshots at every scene: hook phrases, answer stamp, map pin + chips, zoom-out, lot cards, each
tour step, status, price before/after, package, cashback, CTA, and the end card. Look for overlaps,
captions near the edge, text over faces or busy areas, and anything unreadable.

Common check findings and their fixes:
- `line_unread` on a hook phrase: the phrase is under about 0.8 s. Move the next phrase's `at` later (onto
  a later word) or add an `@` offset.
- `clip_media_fit` / `duplicate_audio_track` on VO: lines overlap. Raise the next line's `gap`.
- Shot assertion in build: see `max` in the reference §4.
- `text_box_overflow`: shorten the text or lower its `size`.

### 6. Preview and hand over
```bash
npx hyperframes preview --background      # Studio on port 3002; also report the port
npx hyperframes render --quality draft -o renders/PREVIEW-draft-$SLUG.mp4   # ~6 min for 80 s
```
Send the draft MP4 to the user, then write `$SLUG/EDIT_NOTES.md` (template: `pulau-indah/EDIT_NOTES.md`).
It holds the transcript table (what was used or cut and why), the script/timeline table, and a "check
these before the final render" list (names you took on trust, words the voice may say oddly, calculated
numbers, map imagery age). Commit and push (footage and renders stay out of git). In chat, give a short
summary in Malay plus that check list.

The final render happens only after they approve:
`npx hyperframes render --quality delivery -o renders/FINAL-$SLUG.mp4`.

## Things that broke before (so you don't relearn them)
- Whisper on raw phone audio hallucinates "Terima kasih kerana menonton". `transcribe.py` high-passes,
  normalises and uses VAD.
- ElevenLabs on this account: max 3 concurrent requests (429 otherwise); `mp3_44100_192` returns 403 (use
  128); no forced-alignment permission. eleven_v3's own timestamps drift by ~0.2 s and up to 1.7 s,
  which is why `align_vo.py` exists. Pause tightening is done on the audio's silence, never on those
  timestamps (that clipped the first words once).
- ElevenLabs music often goes silent a few seconds before its requested length. `make_audio.py` reports
  it, and `extend_music.py <proj> <seconds>` repeats whole bars seamlessly.
- In compositions, GSAP overwrites CSS `transform`: centre things with a full-width wrapper plus
  `text-align: center`, not `translateX(-50%)`. On SVG, GSAP replaces the `transform` attribute, so wrap
  the animated element in a positioned `<g>` (the build already does both).
- Re-running `build.py` overwrites `video/index.html` and `video/compositions/`. Edits made in Studio are
  lost, so put changes in project.json.

## Revisions the owner may ask for
- "VO monotone / tak bersemangat": add or strengthen tags, lower `voice.stability` to 0.35 (more varied),
  re-generate. "Terlalu laju": `voice.tempo` 1.05. Always re-run enhance and align after make_vo.
- "Tulisan besar sangat": lower the `size` values in the hook (and stamp/cards if named).
- "Pendekkan": drop a whole chapter line (e.g. highways or status) rather than squeezing words.
- Another voice: `voice.voice_id` (list voices: `curl -s https://api.elevenlabs.io/v1/voices`).
