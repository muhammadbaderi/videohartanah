# project.json reference

One file holds everything specific to a project. `build.py` reads it and the VO timing, and writes all
the HTML. Edit this file, never the generated HTML. A worked example is `examples/project.example.json`
(the Pulau Indah edit); `new_project.sh` starts every project from a copy of it.

## Contents
1. Anchors (how anything is timed)
2. Top level
3. `lines`: the voiceover script
4. `shots`: the picture cut
5. `map`
6. `scenes`: hook, answer, map, plan, status, price, package, cashback, cta
7. `captions`, `music`, `timeline`

## 1. Anchors

Every `at`, `start`, `switch`, `slam`, `out` and `big_at` value is an anchor on the voice:

| Anchor | Means |
|---|---|
| `"lot"` | start of line `lot` |
| `"lot:Porch,"` | start of the first word `Porch,` in line `lot`. Matching ignores case and punctuation, so `"lot:porch"` works too |
| `"pkg:legal#1"` | the second `legal` in line `pkg` (`#0` is the first) |
| `"hook1:Pulau@-0.1"` | 0.1 s before that word. Any anchor can take `@±seconds` |

Words are the **spoken** words (the left side of `{spoken|display}`), so an anchor on a price uses the
spoken form: `"price:dua#1"`. A bad anchor stops the build with the list of words in that line.

## 2. Top level

| Key | Example | Notes |
|---|---|---|
| `slug`, `title` | `"pulau-indah"`, `"Teres Setingkat Pulau Indah"` | folder name / page title |
| `inputs` | `{"video_url", "floorplan_url", "maps_url"}` | the links the user gave, kept so footage can be fetched again in a new session |
| `phone` | `"016-370 8908"` | CTA number |
| `footage` | `"assets/footage/source_1080.mp4"` | written by `prepare_media.sh` |
| `stills` | `{"freeze": 4.7, "blur": 2.0}` | source seconds for the hook freeze frame (sharp) and the blurred CTA backdrop: pick a good exterior frame for both |
| `voice` | `{"voice_id", "name", "model_id": "eleven_v3", "stability": 0.5, "tempo": 1.12}` | `tempo` is applied in post by `enhance_vo.py` |
| `accent` | `"#FFC83D"` | optional brand colour (yellow by default) |
| `lang` | `"ms"` | optional |

## 3. `lines`

```json
{"id": "price", "gap": 0.55, "text": "[serious] Harga asal, {dua ratus sembilan puluh sembilan ribu lima ratus|RM299,500}. [b] [excited] Sekarang, dari {dua ratus sembilan puluh ribu lima ratus ringgit|RM290,500} je!"}
```

- `id`: short, unique. Scenes and anchors use it.
- `gap`: silence before the line, in seconds (0.12 for the first, 0.3 by default, 0.45 to 0.65 before a new chapter or after a number people must read).
- `text`:
  - `{spoken|display}`: the voice reads the left side and the captions/graphics show the right side. Write **every number in Malay words** on the left (the voice misreads digits), and acronyms as `S.K.V.E` / `W-C-E` / `M.O.T`. A hyphen fixes stress: `Ri-zab`.
  - `[b]`: short pause (sent as `[short pause]`).
  - `[serious]`, `[curious]`, `[confident]`, `[warm]`, `[upbeat]`, `[impressed]`, `[excited]`, `[urgent]`: eleven_v3 delivery tags. They are not spoken, captioned or matched. One or two per line, following the story's energy. Lines without a tag keep the previous mood.
  - Punctuation steers the read: `?` lifts, `!` punches, `.` drops. End every line with punctuation.

Changing a line's text means re-running `make_vo.py`, `enhance_vo.py` and `align_vo.py` for that id.

## 4. `shots`

The picture is a list of trims of the one footage file. Each shot runs until the next one starts. The
last one runs until the CTA starts, and the CTA has its own backdrop.

```json
{"line": "lot", "src": 38.4, "switch": "lot:Porch,", "max": 42.6, "why": "looking out through the porch"}
```

| Key | Meaning |
|---|---|
| `line` | the shot starts at this line's start... |
| `switch` | ...or 0.12 s before this anchor (use it to cut on a word) |
| `src` | source second to start from, or `"freeze"` (the freeze still), `"still"` (the blurred still), or `"map"` (nothing; the map scene covers the frame) |
| `max` | the last usable source second of this take (before a whip pan, blur or the camera turning to a selfie). The build stops if the shot needs more footage than that. Fix it by starting earlier, adding a `switch`, or splitting the shot |
| `why` | a note that ends up as an HTML comment |

The first shot always starts at 0.

## 5. `map`

```json
{"lat": 2.919219, "lon": 101.301938, "local_zoom": 16, "region_zoom": 12,
 "marks": [{"name": "Klang", "lat": 3.0438, "lon": 101.4456}]}
```

`marks` are town labels on the regional view (2 or 3 nearby towns the viewer knows). `make_map.py` warns
when a mark falls outside the frame. Region zoom 12 shows about 40 km across, and 11 shows about 80 km.

## 6. `scenes`

Every scene is optional. Order is fixed: hook, answer, map, plan, status, price, package, cashback, cta.
Each scene runs from its `start` until the next present scene's `start` (the hook starts at 0, and the
cta runs to the end). SFX for each scene are built in.

### hook
```json
{"tag": "PROJEK BARU · PULAU INDAH",
 "phrases": [
   {"at": "hook1:Rumah", "lines": [{"text": "RUMAH TERES", "size": 68},
                                   {"text": "FREEHOLD", "size": 112, "accent": true, "slam": "hook1:freehold", "sfx": "boom"}]},
   {"at": "hook1:Pulau@-0.1", "icon": "pin", "sfx": "pin", "lines": [{"text": "DI PULAU INDAH", "size": 66}]},
   {"at": "hook1:bawah@-0.25", "lines": [{"text": "HARGA BAWAH", "size": 56},
                                          {"text": "RM300K", "size": 148, "accent": true, "glow": true, "slam": "hook1:tiga", "shake": true, "sfx": "impact"}]}],
 "question": {"at": "hook2", "words": [{"text": "MASIH", "at": "hook2:Masih", "size": 96, "sfx": "whoosh"},
                                       {"text": "WUJUD", "at": "hook2:wujud", "size": 150, "q": true, "sfx": "boom"}]}}
```
Phrases replace each other, so each must stay on screen for at least about 1 s. Keep the sizes about as
shown: the owner asked for **smaller** opening text than the first draft (which used 104/168/228 px).
`slam` punches one line in on its word. `q: true` adds the wobbling "?". The question darkens the frame,
and a riser leads into the answer.

### answer
`{"start": "ans", "stamp": {"text": "WUJUD.", "at": "ans:Wujud.", "out": "ans:berdiri"}, "badge": {"text": "SITE VISIT · PULAU INDAH", "at": "ans:Dan"}}`

### map
```json
{"start": "loc1",
 "title": {"kicker": "Lokasi", "text": "PERSIARAN MASJID SULTAN", "sub": "Pulau Indah, Klang · Selangor", "at": "loc1:Projek@0.05"},
 "pin": {"at": "loc1:Persiaran", "label": "PROJEK BARU"},
 "amenities": [{"icon": "school", "text": "SK · SMK · SRA Pulau Indah", "at": "loc2:Sekolah,"}],
 "zoom_out": "loc3",
 "roads": [{"text": "KESAS", "at": "loc3:Kesas,", "big": true}, {"text": "Lebuhraya Pulau Indah", "at": "loc3:semua"}],
 "credit": "Imej satelit: Esri, Maxar, Earthstar Geographics"}
```
Up to 6 amenities (a 2-column grid, about 26 characters each). Icons available: school, mosque, clinic,
hospital, cart, mall, halal, factory, train, park, ship, star. Roads: 3 `big` ones in one row, then
smaller ones. Each chip pops on the word that names it.

### plan
```json
{"start": "lot", "width_mm": 6096, "depth_mm": 19508,
 "rooms": {"b3": [0, 1220, 3048, 3150], "porch": [0, 13412, 6096, 6096]},
 "labels": {"b3": "BILIK 3", "rt": "RUANG\nTAMU"},
 "small_labels": ["ba1", "ba2"], "outdoor": ["yard", "porch"],
 "numbered": [["bu", 1], ["b2", 2], ["b3", 3]], "porch": "porch",
 "cards": [{"type": "text", "kicker": "Jenis", "value": "TERES 1 TINGKAT", "size": 58, "sub": "Freehold · Rizab Melayu", "at": "lot:Teres", "sfx": "tick"},
           {"type": "dims", "kicker": "Luas tanah", "w": 20, "d": 64, "unit": "'", "sub": "1,280 kaki persegi<br />Luas binaan 20' × 40'", "at": "lot:dua", "sfx": "pop"},
           {"type": "cars", "kicker": "Porch", "text": "MUAT 2", "count": 2, "at": "lot:Porch,", "sfx": "pop"}],
 "tour_start": "liv",
 "steps": [{"at": "liv@0.1", "hl": ["rt"], "kicker": "Masuk je", "title": "RUANG TAMU"},
           {"at": "mbr", "clear": ["rt"], "hl": ["bu"], "kicker": "Master", "title": "BILIK UTAMA", "sfx": "tick"},
           {"at": "kit:privasi.", "badge": "LEBIH PRIVASI", "icon": "shield", "sfx": "ping"},
           {"at": "rooms", "clear": ["dp", "rt"], "hide_label": true},
           {"at": "rooms:Tiga", "hl_seq": ["bu", "b2", "b3"], "numbers": true, "count": "3 BILIK TIDUR", "sfx": "pop"},
           {"at": "rooms:dua", "hl_seq": ["ba1", "ba2"], "color": "#5ec8ff", "count": "2 BILIK AIR", "sfx": "pop"}]}
```
- **Rooms** are `[x, y, w, h]` in millimetres for ONE unit. x runs across the frontage, and y runs from
  the rear boundary (0) to the road. Read them from the floor plan's dimension strings: measure the unit's
  frontage in pixels, get mm/px from the stated width (6096 mm = 20 ft), then convert each wall line. Round
  to the dimension strings where they exist. `depth_mm` is the full lot depth including the porch.
  Include yard/porch so the outline is the whole lot.
- During `start` → `tour_start` the plan is big on the left and the `cards` stack on the right (lot
  facts). At `tour_start` the plan shrinks to the top-right corner. Then each step can: `clear` highlights,
  `hl` rooms, `hl_seq` rooms one after another (`numbers` pops the `numbered` badges, and `color` recolours
  them), show a lower-third `kicker`/`title`, `flash` a room, pop a `badge` pill, add a `count` chip, or
  `hide_label` the lower third (when chips take over). One step per spoken room.

### status
`{"start": "eta", "kicker": "Status projek", "now": {"small": "Sekarang", "text": "STRUKTUR SIAP", "at": "eta:Struktur"}, "next": {"small": "Dijangka siap sepenuhnya", "text": "Q3 2027", "at": "eta:Dijangka", "big_at": "eta:suku"}}`

### price
`{"start": "price", "currency": "RM", "old": {"kicker": "Harga asal", "value": 299500, "at": "price:Harga"}, "new": {"kicker": "Sekarang dari", "value": 290500, "at": "price:Sekarang,", "count_at": "price:dua#1"}, "save": "JIMAT RM9,000"}`
`old` is optional (without it the counter starts 5% above the new price). Only add `save` when the
difference is real and tell the user it was calculated.

### package
`{"start": "pkg", "kicker": "Pakej pembeli", "title": "SEMUA DAH COVER", "items": [{"tag": "BOOKING", "text": "RM500", "at": "pkg:Booking,", "light": true}, {"tag": "FREE", "text": "Legal fee SPA", "at": "pkg:legal#0"}], "stamp": {"text": "SEMUA PERCUMA", "at": "pkg:semua"}}`
Up to 5 items fit.

### cashback
`{"start": "cash", "kicker": "Pembeli terawal", "title": {"text": "CASHBACK", "at": "cash:cashback"}, "value": {"amount": 11000, "prefix": "RM", "at": "cash:sebelas"}}`

### cta
```json
{"start": "cta",
 "tags": [{"text": "FREEHOLD", "at": "cta:Freehold.", "style": "accent", "sfx": "pop"},
          {"text": "RIZAB MELAYU", "at": "cta:Ri-zab", "style": "light", "sfx": "pop"},
          {"text": "UNIT TERHAD", "at": "cta:Unit", "style": "alert", "pulse": true, "sfx": "impact"}],
 "whatsapp": {"kicker": "WHATSAPP SEKARANG", "at": "cta:WhatsApp",
              "groups": [{"text": "016-", "at": "cta:kosong"}, {"text": "370 ", "at": "cta:tiga"}, {"text": "8908", "at": "cta:lapan"}]},
 "end_title": "JOM <span class=\"y\">SITE VISIT</span>",
 "summary": "Teres 1 Tingkat · Pulau Indah · dari <b>RM290,500</b>"}
```
Phone groups appear as the voice reads each group: anchor each on its first spoken digit (`#n` for repeats).

## 7. `captions`, `music`, `timeline`

```json
"captions": {"lines": ["ans", "loc1", "lot"], "skip": [["ans", "Wujud."]], "nobreak": [["bilik", "air"]], "limit": 22},
"music": {"file": "assets/audio/music-bed.mp3", "start": "ans:Wujud.@-0.05", "length": 75.5, "bed": 0.16, "lift": 0.34, "lifts": [["loc3@3.8", "lot"]]},
"timeline": {"end_hold": 3.2, "flash_cuts": ["ans", "lot", "price", "cta"], "strong_push": ["hook1", "hook2"]}
```
- Captions (karaoke, yellow active word) only on narrative lines. Leave out lines whose words are already
  big on screen (hook, price, package, cashback, cta) and `skip` single units shown elsewhere. `nobreak`
  word pairs never split across caption lines.
- Music starts on the answer's first word (the hook runs on SFX alone). `length` is where the track
  audibly ends (from `make_audio.py`'s report). The bed sits at `bed` under the voice and lifts to `lift`
  in `lifts` windows and on the end card.
- `flash_cuts`: white flash on those line starts (chapter changes). `strong_push`: shots under these
  lines push in harder (1.14 instead of 1.07).
