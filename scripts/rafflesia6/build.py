"""Build rafflesia6/index.html and rafflesia6/compositions/captions.html.

Inputs (all in scripts/rafflesia6/):
  edl.json            timeline: VO line starts, shots (trims of the one phone clip), scenes, wipes, music
  vo_lines.json       the script (spoken text + caption text) and the ElevenLabs voice settings
  vo_align.json       character timings from ElevenLabs (with-timestamps), before the 1.05x tempo
  captions_src.json   caption chunks: display tokens mapped to spoken-word indices

Re-running OVERWRITES index.html and captions.html (Studio edits to those two files are lost).
The scene files compositions/g-*.html are hand-written and never touched.

Usage: python3 -I scripts/rafflesia6/build.py
"""
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.abspath(os.path.join(HERE, "..", "..", "rafflesia6"))
E = json.load(open(os.path.join(HERE, "edl.json")))
L = json.load(open(os.path.join(HERE, "vo_lines.json")))
A = json.load(open(os.path.join(HERE, "vo_align.json")))
C = json.load(open(os.path.join(HERE, "captions_src.json")))
T = E["tempo"]
TOTAL = E["duration"]
r3 = lambda x: f"{x:.3f}".rstrip("0").rstrip(".")


def spoken_words(line_id):
    """[(text, start, end)] in the tempo-adjusted file's own time."""
    v = A[line_id]
    out, cur, s, e = [], "", 0.0, 0.0
    for c, t0, t1 in zip(v["characters"], v["character_start_times_seconds"], v["character_end_times_seconds"]):
        if c == " ":
            if cur:
                out.append((cur, s / T, e / T)); cur = ""
            continue
        if not cur:
            s = t0
        cur += c; e = t1
    if cur:
        out.append((cur, s / T, e / T))
    return out


def vo_parts(ln):
    return ln.get("parts") or [{"media_in": 0.0, "media_out": 999.0, "start": ln["start"]}]


def film_time(line_id, t):
    ln = next(x for x in E["vo"] if x["id"] == line_id)
    for p in vo_parts(ln):
        if p["media_in"] - 0.05 <= t < p["media_out"]:
            return p["start"] + t - p["media_in"]
    return None


WORDS = {}
for ln in E["vo"]:
    WORDS[ln["id"]] = [(w, film_time(ln["id"], s), film_time(ln["id"], e)) for w, s, e in spoken_words(ln["id"])]

# ---------------------------------------------------------------- sound effects
# (film time the picture lands, file, volume, note). Start = picture + 1 frame - the file's own hit offset.
HIT = {"pop": 0.11, "click-soft": 0.045, "ping": 0.32, "sparkle": 0.02, "impact-bass-1": 0.045}
FRAME = 1 / E["fps"]
SFX = [
    (2.30, "pop", 0.5, "hook: blue marker sweeps under RM500K"),
    (5.24, "pop", 0.45, "location card lands (Taman)"),
    (6.70, "click-soft", 0.6, "Seksyen 29 line"),
    (9.25, "click-soft", 0.6, "TERHAD badge"),
    (9.86, "pop", 0.55, "19 lands"),
    (11.50, "pop", 0.45, "stat: 4 bilik tidur"),
    (12.45, "click-soft", 0.6, "stat: 2 bilik air"),
    (13.55, "click-soft", 0.5, "lot card enters"),
    (15.70, "ping", 0.45, "land outline closes on 21 x 68"),
    (16.25, "pop", 0.45, "built-up area fills"),
    (19.30, "pop", 0.45, "porch card"),
    (19.78, "click-soft", 0.6, "car 1"),
    (19.95, "click-soft", 0.6, "car 2"),
    (20.48, "pop", 0.45, "siling tinggi arrow"),
    (24.40, "impact-bass-1", 0.16, "price lands on RM455,120 (the payoff)"),
    (25.05, "pop", 0.45, "check: booking RM500"),
    (26.52, "click-soft", 0.6, "check: free legal fee SPA"),
    (28.77, "pop", 0.45, "check: free MOT"),
    (32.72, "click-soft", 0.55, "stop: Quayside"),
    (33.79, "pop", 0.4, "stop: Saujana Putra"),
    (34.86, "click-soft", 0.55, "stop: Kota Kemuning"),
    (37.26, "pop", 0.4, "sign: ELITE"),
    (37.91, "click-soft", 0.55, "sign: SKVE"),
    (39.33, "pop", 0.4, "sign: KESAS"),
    (40.27, "click-soft", 0.55, "sign: LKSA"),
    (41.80, "click-soft", 0.55, "tag: leasehold"),
    (42.64, "click-soft", 0.55, "tag: rizab melayu"),
    (43.45, "pop", 0.45, "completion card"),
    (44.60, "click-soft", 0.5, "2027 lands"),
    (46.97, "pop", 0.55, "UNIT TERHAD stamp"),
    (48.47, "pop", 0.45, "avatar"),
    (49.35, "click-soft", 0.6, "digits 016"),
    (50.97, "click-soft", 0.6, "digits 370"),
    (52.56, "pop", 0.5, "digits 8908"),
    (53.80, "sparkle", 0.14, "project block lands"),
]
WHOOSH_LEAD = 0.13  # whoosh energy straddles the cut
for t in E["wipes"]:
    SFX.append((t - WHOOSH_LEAD - FRAME + 0.0, "whoosh", 0.3, f"blue wipe at {t}"))
SFX.sort()

# ---------------------------------------------------------------- index.html
o = []
w = o.append
w("""<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Taman Rafflesia 6 - teres 1 tingkat</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #061636; }
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; }
      #ground { position: absolute; inset: 0; background: #061636; }
      #cam { position: absolute; inset: 0; overflow: hidden; z-index: 1; }
      #cam-inner { position: absolute; inset: 0; transform-origin: 50% 45%; }
      #cam-inner video, #cam-inner img { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }
      #tint { position: absolute; inset: 0; z-index: 2; background: linear-gradient(180deg, rgba(6,22,54,0.35) 0%, rgba(6,22,54,0) 22%, rgba(6,22,54,0) 55%, rgba(6,22,54,0.55) 100%); }
      #wipe { position: absolute; left: -700px; top: -200px; width: 560px; height: 2320px; z-index: 30;
        background: linear-gradient(90deg, rgba(92,194,255,0) 0%, #5cc2ff 18%, #1d5cff 50%, #0e3bbf 82%, rgba(14,59,191,0) 100%);
        transform: rotate(14deg); opacity: 0; }
      .scene { position: absolute; inset: 0; pointer-events: none; }
    </style>
  </head>
  <body>""")
w(f'    <div id="root" data-composition-id="main" data-start="0" data-duration="{r3(TOTAL)}" data-width="1080" data-height="1920">')
w('      <div id="ground"></div>')
w("")
w("      <!-- PICTURE: every shot is a trim of the one phone clip (muted; the voiceover is its own track) -->")
w('      <div id="cam">')
w('        <div id="cam-inner" data-layout-allow-overflow>')
for sid, st, en, src, s0, s1 in E["shots"]:
    w(f'          <video id="v-{sid}" class="clip" src="{E["footage"]}" muted playsinline data-start="{r3(st)}" data-duration="{r3(en - st)}" data-media-start="{r3(src)}" data-track-index="1"></video>')
ec = E["endcard"]
w(f'          <img id="v-endcard" class="clip" src="{ec["src"]}" alt="" data-start="{r3(ec["start"])}" data-duration="{r3(TOTAL - ec["start"])}" data-track-index="1" />')
w("        </div>")
w("      </div>")
w('      <div id="tint"></div>')
w('      <div id="wipe"></div>')
w("")
w("      <!-- VOICE: the owner's cloned voice (ElevenLabs), 1.05x, -16 LUFS -->")
for ln in E["vo"]:
    for k, p in enumerate(vo_parts(ln)):
        src = f"assets/audio/vo-{ln['id']}.wav"
        media_out = p["media_out"]
        if media_out > 900:
            import wave
            wf = wave.open(os.path.join(VID, src)); media_out = wf.getnframes() / wf.getframerate()
        suffix = "" if len(vo_parts(ln)) == 1 else f"-{'ab'[k]}"
        w(f'      <audio id="vo-{ln["id"]}{suffix}" class="clip" src="{src}" data-start="{r3(p["start"])}" data-duration="{r3(media_out - p["media_in"])}" data-media-start="{r3(p["media_in"])}" data-volume="1" data-fade-in="0.01" data-fade-out="0.03" data-track-index="2"></audio>')
w("")
m = E["music"]
auto = {"version": 1, "lanes": [{"target": "volume", "points": [{"t": t, "v": v} for t, v in m["points"]]}]}
w("      <!-- MUSIC: warm acoustic bed (HeyGen catalog, same track as the Meru video), under the voice, lifts on the end card -->")
w(f'      <audio id="music" class="clip" src="{m["src"]}" data-start="0" data-duration="{r3(TOTAL)}" data-media-start="{r3(m["media_start"])}" data-volume="1" data-fade-in="0.2" data-fade-out="1.4" data-automation="{html.escape(json.dumps(auto, separators=(",", ":")))}" data-track-index="5"></audio>')
w("")
w("      <!-- SOUND EFFECTS: each lands one frame after the thing it belongs to -->")
lane_end = {3: -1.0, 4: -1.0, 8: -1.0}  # Studio lanes for effects; no two sounds overlap on one lane
for i, (t, f, vol, note) in enumerate(SFX):
    if f == "whoosh":
        st = t
    else:
        st = t + FRAME - HIT[f]
    st = max(0, st)
    dur = {"pop": 0.72, "click-soft": 0.366, "ping": 1.32, "sparkle": 1.8, "impact-bass-1": 2.116, "whoosh": 0.575}[f]
    lane = next((k for k, e in sorted(lane_end.items()) if e <= st), None)
    if lane is None:
        lane = max(lane_end) + 1
    lane_end[lane] = st + dur
    w(f'      <audio id="sfx-{i + 1:02d}" class="clip" src="assets/sfx/{f}.mp3" data-start="{r3(st)}" data-duration="{r3(dur)}" data-volume="{vol}" data-track-index="{lane}"></audio><!-- {html.escape(note)} -->')
w("")
w("      <!-- MOTION GRAPHICS: one scene per chapter of the voiceover -->")
for i, (sid, st, en) in enumerate(E["scenes"]):
    w(f'      <div id="{sid}" class="scene" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{r3(st)}" data-duration="{r3(en - st)}" data-track-index="{6 + i % 2}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index: 10"></div>')

# captions
groups = []
for line_id, chunks in C.items():
    if line_id.startswith("_"):
        continue
    ws = WORDS[line_id]
    for ch in chunks:
        toks = [(txt, ws[i][1], ws[i][2]) for txt, i in ch]
        last_idx = ch[-1][1]
        # the chunk's last token may span several spoken words ("19" = sembilan belas): end at the next token's word - 1
        groups.append({"line": line_id, "toks": toks, "first": ch[0][1], "last": last_idx})
# chunk end = last spoken word covered by the chunk
for g in groups:
    ws = WORDS[g["line"]]
    nxt = [x for x in groups if x["line"] == g["line"] and x["first"] > g["first"]]
    if nxt:
        last_spoken = min(x["first"] for x in nxt) - 1
    elif g["line"] == "cta":
        last_spoken = g["last"]  # the phone number after it is on the CTA card, not in the captions
    else:
        last_spoken = len(ws) - 1
    g["st"] = g["toks"][0][1] - 0.05
    g["en"] = ws[last_spoken][2] + 0.18
for i in range(len(groups) - 1):
    if groups[i]["en"] > groups[i + 1]["st"] - 0.02:
        groups[i]["en"] = groups[i + 1]["st"] - 0.02
CAP_START = groups[0]["st"] - 0.01
CAP_END = groups[-1]["en"] + 0.01
w(f'      <div id="captions" class="scene" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="{r3(CAP_START)}" data-duration="{r3(CAP_END - CAP_START)}" data-track-index="9" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index: 20"></div>')
w("    </div>")

# root timeline: slow push-in on every shot + blue wipes on chapter cuts
w("""    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      // each shot drifts in slowly so the walk-through never sits still""")
for sid, st, en, src, s0, s1 in E["shots"]:
    w(f'      tl.fromTo("#cam-inner", {{ scale: {s0} }}, {{ scale: {s1}, duration: {r3(en - st)}, ease: "none", immediateRender: false }}, {r3(st)});')
w(f'      tl.fromTo("#cam-inner", {{ scale: 1.0 }}, {{ scale: 1.06, duration: {r3(TOTAL - ec["start"])}, ease: "none", immediateRender: false }}, {r3(ec["start"])});')
w("      // chapter cuts: a blue light bar sweeps across and hides the cut")
for t in E["wipes"]:
    w(f'      tl.fromTo("#wipe", {{ x: 0, opacity: 0.95 }}, {{ x: 2100, opacity: 0.95, duration: 0.42, ease: "power2.inOut", immediateRender: false }}, {r3(t - 0.21)});')
    w(f'      tl.set("#wipe", {{ opacity: 0 }}, {r3(t + 0.22)});')
w(f"""      tl.set({{}}, {{}}, {r3(TOTAL)});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
""")
open(os.path.join(VID, "index.html"), "w").write("\n".join(o))

# ---------------------------------------------------------------- captions.html
c = []
a = c.append
a("""<template>
  <style>
    #root { position: absolute; inset: 0; }
    .cg { position: absolute; left: 0; top: 1188px; width: 1080px; height: 110px; }
    .cg-in { position: absolute; left: 60px; right: 60px; top: 0; text-align: center; white-space: nowrap; overflow: visible;
      font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 62px; line-height: 1.15; letter-spacing: -0.01em;
      color: #ffffff; -webkit-text-stroke: 13px rgba(6, 22, 54, 0.94); paint-order: stroke fill;
      text-shadow: 0 6px 18px rgba(6, 22, 54, 0.5); }
    .cw { display: inline-block; transform-origin: 50% 80%; }
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">""")
k = 0
for gi, g in enumerate(groups):
    spans = []
    for txt, s, e in g["toks"]:
        spans.append(f'<span id="cw-{k}" class="cw">{html.escape(txt)}</span>'); g.setdefault("ids", []).append(k); k += 1
    a(f'    <div id="cg-{gi}" class="clip cg" data-start="{r3(g["st"] - CAP_START)}" data-duration="{r3(g["en"] - g["st"])}" data-track-index="0"><div id="cgi-{gi}" class="cg-in">{" ".join(spans)}</div></div>')
a("""  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    const HI = "#5cc2ff";""")
for gi, g in enumerate(groups):
    st, en = g["st"] - CAP_START, g["en"] - CAP_START
    a(f'    tl.fromTo("#cgi-{gi}", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.14, ease: "power3.out" }}, {r3(st)});')
    for j, (txt, s, e) in enumerate(g["toks"]):
        on = max(s - CAP_START, st)
        a(f'    tl.fromTo("#cw-{g["ids"][j]}", {{ color: "#ffffff", scale: 1 }}, {{ color: HI, scale: 1.06, duration: 0.08, ease: "power2.out" }}, {r3(on)});')
        if j + 1 < len(g["toks"]):
            off = max(g["toks"][j + 1][1] - CAP_START, on + 0.12)
            a(f'    tl.to("#cw-{g["ids"][j]}", {{ color: "#ffffff", scale: 1, duration: 0.08, ease: "power2.in" }}, {r3(off)});')
    a(f'    tl.to("#cgi-{gi}", {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, {r3(en - 0.1)});')
    a(f'    tl.set("#cgi-{gi}", {{ opacity: 0, visibility: "hidden" }}, {r3(en)});')
a("""    window.__timelines["captions"] = tl;
  </script>
</template>
""")
open(os.path.join(VID, "compositions", "captions.html"), "w").write("\n".join(c))

print(f"total {TOTAL}s, {len(E['shots'])} shots, {len(SFX)} sfx, {len(groups)} caption groups ({r3(CAP_START)} -> {r3(CAP_END)})")
for ln in E["vo"]:
    ws = WORDS[ln["id"]]
    ends = [x[2] for x in ws if x[2] is not None]
    print(f"  {ln['id']:7s} {ws[0][1]:6.2f} -> {max(ends):6.2f}")
