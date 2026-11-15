# SPEC: Rumah Berkembar 1-Tingkat, Jalan Pipit (storyline A)

GOAL:    a buyer scrolling past stops on the house and price, knows in under a minute what it costs
         to book, what's free, how big it is, where it is, and has the number to call.
OUTPUT:  HyperFrames, 1080 x 1920, 30 fps, no voiceover, no captions (no speech)
TIME:    53.55 s x 30 = 1607 frames. Music bed 126 BPM (14.3 frames/beat), entered at 30.485 s
         (section C, on a beat) so the track's own ending (83.4 s) lands under the end card.
         Bars (film time): 0, 1.91, 3.82, 5.72, 7.63, 9.53, 11.43, 13.34, 15.24, 17.15, 19.05,
         20.96, 22.86, 24.77, 26.68, 28.58, 30.48, 32.38, 34.29, 36.20, 38.10, 40.01, 41.91,
         43.82, 45.72, 47.62, 49.54, 51.44. Every scene cut sits on a bar.
LOOK:    taken from the renders' facade: charcoal #2B2D31 (panels, cards), concrete white #F4F3F0
         (plan sheet), warm beige #B99C84 (sampled from the lit panel in the side render) (package screen ground, the beige wall panel), ink white
         #FFFFFF on photos, ink charcoal on light grounds. One accent, yellow #FFC83D, only on: the
         price, "RM1,000", the word FREE, the minutes, the phone icon (same accent as the Meru video).
         Display: Montserrat 900, titles 112-150 px, tracking -2%. Body: Inter 700/600, 36-48 px.
         Cards: solid charcoal at 90%, radius 28 px, shadow 0 16 40 rgba(0,0,0,.35). No glass.
         Photos/renders: full-bleed, a top or bottom scrim (black 0 -> 55%) only where type sits.
OBJECTS: the house is always the real render or the real site clip; the floor plan is the
         developer's drawing (one unit highlighted, the mirror unit dimmed to 25%); the location is
         real Esri satellite imagery baked from the map pin (2.924945, 101.510804).
MOTION:  arrivals expo.out / power4.out 0.35-0.5 s; camera moves power2.inOut; exits power3.in,
         0.15-0.25 s (about half the entrance). Pops use back.out(2) on scale only. Words stagger
         0.07 s. Numbers count up 0.8-1.2 s then hold dead still. Landed titles never drift.
SHOTS:
  S1 0.00-3.82   render-depan, slow lateral pan right (-120 px -> +120 px, linear-ish power1.inOut).
                 On frame 0: badge DIBUKA UNTUK PENDAFTARAN, title RUMAH BERKEMBAR / 1-TINGKAT in the
                 sky, line "Jalan Pipit, Telok Panglima Garang". 1.0 s: sticker "DARI RM485,700"
                 stamps on (pop). Out: horizontal whip 0.2 s (whoosh).
  S2 3.82-7.63   render-sisi lands from the whip blurred, sharpens 0.15 s; slow push 1.0 -> 1.06.
                 "HANYA" then the 8 counts 1 -> 8 (pop on land), "UNIT SAHAJA". 6.9 s: the beige
                 wall panel floods the frame 0.6 s (power2.inOut) = the next world.
  S3 7.63-15.24  beige ground. "PAKEJ" kicker, BOOKING / RM1,000 counts up (pop), then three lines
                 stamp in one per 1.4 s: FREE SPA Legal Fee, FREE MOT (pembeli rumah pertama),
                 FREE SPA Disbursements (pop each). Out: white plan sheet slides up 0.4 s.
  S4 15.24-24.77 white sheet: whole plan (2 units) arrives, then the camera pushes into one unit
                 (scale to fit width), the mirror unit dims. Facts land one per bar below:
                 4 Bilik / 2 Bilik Air; Tanah 2,814 kps (44' x 76.7'-78'); Binaan 1,266 kps.
                 Out: white flash 3 frames (whoosh).
  S5 24.77-30.48 IMG_1308 site clip (muted). LEASEHOLD / Rizab Melayu card, then
                 "Dijangka siap Q4 2027". Out: zoom through (scale 1 -> 1.25 + blur 0.3 s).
  S6 30.48-38.10 satellite pull-back: holds on the plot with the pin and "Jalan Pipit" label, pulls
                 back to the Klang Valley (pin glides with the plot), then Shah Alam 23 min,
                 Putrajaya 41 min, KLCC 42 min pop on at their real positions; highway chips
                 SKVE / KESAS / WCE / LKSA. Imagery credit bottom-left. Out: vertical whip.
  S7 38.10-45.72 IMG_1307 site clip under a 60% charcoal scrim. "DEKAT DENGAN" + 4 rows, one per
                 0.9 s: 5 min SK Kebun Baharu, 6 min 99 Speedmart, 11 min Tropicana Aman,
                 19 min Columbia Asia Bkt Rimau. Out: dip to charcoal 3 frames.
  S8 45.72-53.55 render-depan, dark lower scrim. HARGA DARI / RM485,700 (riser into impact),
                 Booking RM1,000 · 8 unit sahaja, phone card 016-370 8908 with HUBUNGI SAYA. Holds
                 dead still from 50.5 s to the end while the music ends.
BANNED:  dark void ground; glow, particles, gradients as decoration; glass cards; cream-paper serif;
         everything fading and sliding up (each scene enters differently); three cards in a row /
         KPI grid (facts land one at a time in their own place); docked logo; text moving while read;
         claims not in the developer's copy (no "murah", no "terbaik", no invented figures).
QA:      t=0 (thumbnail reads title + house), 1.5 (price sticker), 5.5 (8 unit), 12 (package all
         visible), 21 (plan + facts), 27 (leasehold), 35 (map labels on real spots), 44 (list),
         51 (end card complete). Every word inside y 168-1330, nothing under the right action rail
         (x > 960) that must be read.
