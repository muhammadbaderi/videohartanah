# Look and layout

The owner asked for a blue theme with matching tones for the motion graphics and text animation.

## Colours (defined on each scene's `#root`)

| Token | Hex | Use |
|---|---|---|
| navy | `#061636` | page ground, card fill at 0.86 alpha, caption text stroke |
| blue | `#1d5cff` | pills, icon squares, highway signs, the price marker, check circles |
| blue-d | `#0e3bbf` | gradient end on big badges (19 UNIT, Q1 2027, UNIT TERHAD) |
| sky | `#5cc2ff` | numerals, eyebrows, lines, map dots; caption highlight `#7cd0ff` |
| ice | `#e6f2ff` | secondary text |
| line | `rgba(92,194,255,0.45)` | 2 px card borders |

Cards: navy 0.86, 2 px sky border, radius 32-40 px, `backdrop-filter: blur(18px)`, soft dark shadow.
Fonts: Montserrat 800/900 for headings and every number, Inter 600-800 for small text (both bundled).
Readable text is 28 px or larger. No other accent colours; white only for the end-card phone card and FREE badges.

## Frame (1080 x 1920) and the apps' safe area

HyperFrames 0.9.56 `check` warns `outside_safe_zone` for text that TikTok, Instagram Reels or YouTube Shorts
cover with their own buttons and captions. Where all three are clear:

| Rows | Text may sit in |
|---|---|
| y 288 - 840 | x 120 - 888 |
| y 840 - 1248 | x 120 - 780 (TikTok's like/comment/share rail is on the right) |
| above 288, below 1248 | nothing readable, only picture and decoration |

(TikTok 720x1280 bands [160-560, x 80-640] and [560-840, x 80-520] scaled x1.5; Reels 14-65 % tall, 6-94 % wide;
Shorts y 288-1248, x 48-888.) Design every new video inside this from the start: a content column from x 120,
cards up to x 888 in the upper part and up to x 780 lower down, the caption line centred on x 450 (not 540) with
its bottom above 1248. The Rafflesia 6 layout predates this check (cards x 60-1020, captions at y 1188), so it
draws 12 of these warnings; a new project should fix them rather than copy them.

- Captions: one line of 2-4 words, Montserrat 800 ~58-62 px, white with a 13 px navy stroke, the spoken word turns
  sky. Cards sit above the caption line.
- Frame 0 is the thumbnail: the hook title is fully on screen at 0 s.

## Motion

- Entrances 0.35-0.5 s (`expo.out` for cards, `back.out(2)` for pills, badges and icons), numbers count up and
  land on their word with a small scale pop, exits 0.2 s just before the scene ends (`D - 0.3`).
- Shots: 1-3 s trims of the clip with a slow push-in (scale 1.0 -> 1.05); chapter cuts get a blue light-bar wipe
  and a whoosh. Shots start on words (`edl.json` `"at": "w6"`), so the picture changes with the sentence.
- Sound effects only on things that appear: pop or soft click on cards and chips (alternate the two), a ping when
  the lot outline closes, one bass impact on the price, sparkle on the end card. Music under the voice at 0.13,
  up to 0.34 when the voice ends.
- Footage looks: no CSS filters on video; the end-card background is a still blurred with ffmpeg.
