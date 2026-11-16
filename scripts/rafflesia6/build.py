"""Build the rafflesia6 timeline from the voiceover's word timings.

Inputs (all in scripts/rafflesia6/):
  vo_lines.json       the script (spoken text, caption text, v3 audio tag) and the ElevenLabs settings
  vo_align.json       character timings from ElevenLabs (with-timestamps) for each line's take
  edl.json            gaps between lines, shots (anchored to words), wipes, music, end-card hold
  captions_src.json   caption chunks: display tokens mapped to spoken-word indices

Writes:
  rafflesia6/index.html               (OVERWRITTEN: Studio edits to it are lost)
  rafflesia6/compositions/captions.html  (OVERWRITTEN)
  the CUES block of every compositions/g-*.html (only the text between the CUES markers):
    W = word start times, E = word end times (seconds, local to the scene), D = scene length,
    PB = where the second part of a split line starts (CTA only).
The rest of each scene file is hand-written and never touched.

Usage: python3 -I scripts/rafflesia6/build.py
"""
import json, os, re, html, wave

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.abspath(os.path.join(HERE, "..", "..", "rafflesia6"))
E = json.load(open(os.path.join(HERE, "edl.json")))
L = json.load(open(os.path.join(HERE, "vo_lines.json")))
A = json.load(open(os.path.join(HERE, "vo_align.json")))
C = json.load(open(os.path.join(HERE, "captions_src.json")))
T = E.get("tempo", 1.0)
FPS = E["fps"]
FRAME = 1 / FPS
r3 = lambda x: f"{x:.3f}".rstrip("0").rstrip(".")
LINE_IDS = [l["id"] for l in L["lines"]]
SCENE_OF = {k: f"g-{k}" for k in LINE_IDS}


def wav_dur(path):
    wf = wave.open(path)
    return wf.getnframes() / wf.getframerate()


def spoken_words(line_id):
    """[(text, start, end)] in the processed file's own time; audio tags like [excited] are skipped."""
    v = A[line_id]
    out, cur, s, e = [], "", 0.0, 0.0
    for c, t0, t1 in zip(v["characters"], v["character_start_times_seconds"], v["character_end_times_seconds"]):
        if c.isspace():
            if cur:
                out.append((cur, s / T, e / T)); cur = ""
            continue
        if not cur:
            s = t0
        cur += c; e = t1
    if cur:
        out.append((cur, s / T, e / T))
    return [w for w in out if not re.fullmatch(r"\[[^\]]*\]", w[0])]


# ---------------------------------------------------------------- lay the voice out
VO = {}          # id -> {"parts": [{media_in, media_out, start}], "words": [(text, film_s, film_e)]}
t_prev_end = None
for k in LINE_IDS:
    ws = spoken_words(k)
    dur = wav_dur(os.path.join(VID, "assets", "audio", f"vo-{k}.wav"))
    gap = E["gaps"].get(k, E["gaps"]["default"])
    clip0 = 0.0 if t_prev_end is None else t_prev_end + gap - ws[0][1]
    parts = [{"media_in": 0.0, "media_out": dur, "start": clip0}]
    split = E.get("split", {}).get(k)
    if split:
        # cut the pause after word `after`: part A ends just after it, part B starts just before the next word
        i = split["after"]
        a_out = ws[i][2] + 0.08
        b_in = ws[i + 1][1] - 0.12
        parts = [{"media_in": 0.0, "media_out": a_out, "start": clip0},
                 {"media_in": b_in, "media_out": dur, "start": clip0 + a_out + split["pause"]}]

    def to_film(t, parts=parts):
        for p in parts:
            if p["media_in"] - 0.05 <= t < p["media_out"] + 0.05:
                return p["start"] + t - p["media_in"]
        return None
    # end each clip shortly after its last word, so trailing silence never overlaps the next line
    parts[-1]["media_out"] = min(parts[-1]["media_out"], ws[-1][2] + 0.3)
    words = [(w, to_film(s), to_film(e)) for w, s, e in ws]
    VO[k] = {"parts": parts, "words": words}
    t_prev_end = max(x[2] for x in words if x[2] is not None)

VO_END = t_prev_end
# and never past the start of the next line's clip (its lead-in silence can start earlier than the gap)
for k, nk in zip(LINE_IDS, LINE_IDS[1:]):
    p, nxt = VO[k]["parts"][-1], VO[nk]["parts"][0]["start"]
    p["media_out"] = min(p["media_out"], p["media_in"] + (nxt - 0.01 - p["start"]))
TOTAL = round(VO_END + E["end_hold"], 2)

# scenes: from each line's clip start to the next one's (the last runs to the end)
SCENES = []
for i, k in enumerate(LINE_IDS):
    st = 0.0 if i == 0 else VO[k]["parts"][0]["start"]
    en = VO[LINE_IDS[i + 1]]["parts"][0]["start"] if i + 1 < len(LINE_IDS) else TOTAL
    SCENES.append((SCENE_OF[k], k, round(st, 3), round(en, 3)))
SC = {s[0]: s for s in SCENES}
END_CARD = VO["cta"]["parts"][1]["start"] if len(VO["cta"]["parts"]) > 1 else SC["g-cta"][2]


def local_words(scene):
    sid, k, st, en = SC[scene]
    W = [round(x[1] - st, 3) if x[1] is not None else None for x in VO[k]["words"]]
    Ee = [round(x[2] - st, 3) if x[2] is not None else None for x in VO[k]["words"]]
    return W, Ee, round(en - st, 3)


# ---------------------------------------------------------------- shots
def anchor_time(scene, anchor):
    sid, k, st, en = SC[scene]
    if anchor in (0, "0"):
        return st
    m = re.fullmatch(r"w(\d+)([+-][0-9.]+)?", anchor)
    return VO[k]["words"][int(m.group(1))][1] - 0.05 + (float(m.group(2)) if m.group(2) else 0.0)


SHOTS = [dict(sh, start=round(anchor_time(sh["scene"], sh["at"]), 3)) for sh in E["shots"]]
for i, sh in enumerate(SHOTS):
    sh["end"] = SHOTS[i + 1]["start"] if i + 1 < len(SHOTS) else END_CARD
WIPES = [s[2] for s in SCENES[1:]] + [END_CARD]

# ---------------------------------------------------------------- sound effects
# (scene, local time from W/E/D, file, volume, note) - the times mirror the scene files' animations
HIT = {"pop": 0.11, "click-soft": 0.045, "ping": 0.32, "sparkle": 0.02, "impact-bass-1": 0.045}
DUR = {"pop": 0.72, "click-soft": 0.366, "ping": 1.32, "sparkle": 1.8, "impact-bass-1": 2.116, "whoosh": 0.575}
SFX_SPEC = [
    ("g-hook", lambda W, E_, D: W[7] + 0.03, "pop", 0.5, "hook: blue marker sweeps under RM500K"),
    ("g-intro", lambda W, E_, D: W[2] + 0.04, "pop", 0.45, "location card lands (Taman)"),
    ("g-intro", lambda W, E_, D: W[5] + 0.02, "click-soft", 0.6, "Seksyen 29 line"),
    ("g-intro", lambda W, E_, D: W[11] + 0.07, "click-soft", 0.6, "TERHAD badge"),
    ("g-intro", lambda W, E_, D: max(W[13] + 0.05, W[11] + 0.45), "pop", 0.55, "19 lands"),
    ("g-spec", lambda W, E_, D: W[0] + 0.06, "pop", 0.45, "stat: 4 bilik tidur"),
    ("g-spec", lambda W, E_, D: W[3] + 0.06, "click-soft", 0.6, "stat: 2 bilik air"),
    ("g-spec", lambda W, E_, D: W[6] + 0.08, "click-soft", 0.5, "lot card enters"),
    ("g-spec", lambda W, E_, D: E_[13], "ping", 0.45, "land outline closes on 21 x 68"),
    ("g-spec", lambda W, E_, D: W[14] + 0.07, "pop", 0.45, "built-up area fills"),
    ("g-porch", lambda W, E_, D: W[0] + 0.06, "pop", 0.45, "porch card"),
    ("g-porch", lambda W, E_, D: W[2] + 0.04, "click-soft", 0.6, "car 1"),
    ("g-porch", lambda W, E_, D: W[3] + 0.06, "click-soft", 0.6, "car 2"),
    ("g-porch", lambda W, E_, D: W[4] + 0.06, "pop", 0.45, "siling tinggi card"),
    ("g-price", lambda W, E_, D: E_[7], "impact-bass-1", 0.16, "price lands on RM455,120 (the payoff)"),
    ("g-price", lambda W, E_, D: W[8] + 0.03, "pop", 0.45, "check: booking RM500"),
    ("g-price", lambda W, E_, D: W[13] + 0.03, "click-soft", 0.6, "check: free legal fee SPA"),
    ("g-price", lambda W, E_, D: W[20] + 0.03, "pop", 0.45, "check: free MOT"),
    ("g-loc", lambda W, E_, D: 0.3, "pop", 0.5, "map: site pin lands"),
    ("g-loc", lambda W, E_, D: W[1] + 0.25, "click-soft", 0.55, "map: Quayside pin"),
    ("g-loc", lambda W, E_, D: W[4] + 0.25, "click-soft", 0.55, "map: Saujana Putra pin"),
    ("g-loc", lambda W, E_, D: W[7] + 0.25, "click-soft", 0.55, "map: Kota Kemuning pin"),
    ("g-loc", lambda W, E_, D: W[12], "pop", 0.4, "sign: ELITE"),
    ("g-loc", lambda W, E_, D: W[13], "click-soft", 0.55, "sign: SKVE"),
    ("g-loc", lambda W, E_, D: W[17], "pop", 0.4, "sign: KESAS"),
    ("g-loc", lambda W, E_, D: W[19], "click-soft", 0.55, "sign: LKSA"),
    ("g-tenure", lambda W, E_, D: W[0] + 0.03, "click-soft", 0.55, "tag: leasehold"),
    ("g-tenure", lambda W, E_, D: W[1] + 0.03, "click-soft", 0.55, "tag: rizab melayu"),
    ("g-tenure", lambda W, E_, D: W[3] + 0.04, "pop", 0.45, "completion card"),
    ("g-tenure", lambda W, E_, D: W[6] + 0.08, "click-soft", 0.5, "2027 lands"),
    ("g-cta", lambda W, E_, D: W[1] + 0.03, "pop", 0.55, "UNIT TERHAD stamp"),
    ("g-cta", lambda W, E_, D: (END_CARD - SC["g-cta"][2]) + 0.06, "pop", 0.45, "avatar"),
    ("g-cta", lambda W, E_, D: W[6] + 0.04, "click-soft", 0.6, "digits 016"),
    ("g-cta", lambda W, E_, D: W[9] + 0.04, "click-soft", 0.6, "digits 370"),
    ("g-cta", lambda W, E_, D: W[12] + 0.04, "pop", 0.5, "digits 8908"),
    ("g-cta", lambda W, E_, D: W[15] + 0.12, "sparkle", 0.14, "project block lands"),
]
SFX = []
for scene, fn, f, vol, note in SFX_SPEC:
    W, Ee, D = local_words(scene)
    SFX.append((SC[scene][2] + fn(W, Ee, D), f, vol, note))
WHOOSH_LEAD = 0.13  # whoosh energy straddles the cut
for t in WIPES:
    SFX.append((t - WHOOSH_LEAD - FRAME, "whoosh", 0.3, f"blue wipe at {r3(t)}"))
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
w("      <!-- PICTURE: trims of the one phone clip (muted; the voiceover is its own track) and the baked map -->")
w('      <div id="cam">')
w('        <div id="cam-inner" data-layout-allow-overflow>')
for sh in SHOTS:
    src = sh.get("file", E["footage"])
    w(f'          <video id="v-{sh["id"]}" class="clip" src="{src}" muted playsinline data-start="{r3(sh["start"])}" data-duration="{r3(sh["end"] - sh["start"])}" data-media-start="{r3(sh["src"])}" data-track-index="1"></video>')
ec = E["endcard"]
w(f'          <img id="v-endcard" class="clip" src="{ec["src"]}" alt="" data-start="{r3(END_CARD)}" data-duration="{r3(TOTAL - END_CARD)}" data-track-index="1" />')
w("        </div>")
w("      </div>")
w('      <div id="tint"></div>')
w('      <div id="wipe"></div>')
w("")
w(f"      <!-- VOICE: the owner's cloned voice (ElevenLabs {L['model_id']}), -16 LUFS -->")
for k in LINE_IDS:
    parts = VO[k]["parts"]
    for j, p in enumerate(parts):
        suffix = "" if len(parts) == 1 else f"-{'ab'[j]}"
        w(f'      <audio id="vo-{k}{suffix}" class="clip" src="assets/audio/vo-{k}.wav" data-start="{r3(p["start"])}" data-duration="{r3(p["media_out"] - p["media_in"])}" data-media-start="{r3(p["media_in"])}" data-volume="1" data-fade-in="0.01" data-fade-out="0.03" data-track-index="2"></audio>')
w("")
m = E["music"]
pts = [(0, m["base"]), (round(VO_END, 2), m["base"]), (round(VO_END + 0.4, 2), m["end"])]
auto = {"version": 1, "lanes": [{"target": "volume", "points": [{"t": t, "v": v} for t, v in pts]}]}
w("      <!-- MUSIC: warm acoustic bed (HeyGen catalog, same track as the Meru video), under the voice, lifts on the end card -->")
w(f'      <audio id="music" class="clip" src="{m["src"]}" data-start="0" data-duration="{r3(TOTAL)}" data-media-start="{r3(m["media_start"])}" data-volume="1" data-fade-in="0.2" data-fade-out="1.4" data-automation="{html.escape(json.dumps(auto, separators=(",", ":")))}" data-track-index="5"></audio>')
w("")
w("      <!-- SOUND EFFECTS: each lands one frame after the thing it belongs to -->")
lane_end = {3: -1.0, 4: -1.0, 8: -1.0}  # Studio lanes for effects; no two sounds overlap on one lane
for i, (t, f, vol, note) in enumerate(SFX):
    st = max(0, t if f == "whoosh" else t + FRAME - HIT[f])
    lane = next((k for k, e in sorted(lane_end.items()) if e <= st), None)
    if lane is None:
        lane = max(lane_end) + 1
    lane_end[lane] = st + DUR[f]
    w(f'      <audio id="sfx-{i + 1:02d}" class="clip" src="assets/sfx/{f}.mp3" data-start="{r3(st)}" data-duration="{r3(DUR[f])}" data-volume="{vol}" data-track-index="{lane}"></audio><!-- {html.escape(note)} -->')
w("")
w("      <!-- MOTION GRAPHICS: one scene per line of the voiceover -->")
for i, (sid, k, st, en) in enumerate(SCENES):
    w(f'      <div id="{sid}" class="scene" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{r3(st)}" data-duration="{r3(en - st)}" data-track-index="{6 + i % 2}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index: 10"></div>')

# captions
groups = []
for line_id, chunks in C.items():
    if line_id.startswith("_"):
        continue
    ws = VO[line_id]["words"]
    for ch in chunks:
        groups.append({"line": line_id, "toks": [(txt, ws[i][1], ws[i][2]) for txt, i in ch], "first": ch[0][1], "last": ch[-1][1]})
for g in groups:
    ws = VO[g["line"]]["words"]
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
groups[-1]["en"] = min(groups[-1]["en"], END_CARD - 0.02)
CAP_START = groups[0]["st"] - 0.01
CAP_END = groups[-1]["en"] + 0.01
w(f'      <div id="captions" class="scene" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="{r3(CAP_START)}" data-duration="{r3(CAP_END - CAP_START)}" data-track-index="9" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index: 20"></div>')
w("    </div>")
w("""    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      // each shot drifts in slowly so the walk-through never sits still (the map shot stays at 1.0 so its pins line up)""")
for sh in SHOTS:
    w(f'      tl.fromTo("#cam-inner", {{ scale: {sh["s0"]} }}, {{ scale: {sh["s1"]}, duration: {r3(sh["end"] - sh["start"])}, ease: "none", immediateRender: false }}, {r3(sh["start"])});')
w(f'      tl.fromTo("#cam-inner", {{ scale: 1.0 }}, {{ scale: 1.06, duration: {r3(TOTAL - END_CARD)}, ease: "none", immediateRender: false }}, {r3(END_CARD)});')
w("      // chapter cuts: a blue light bar sweeps across and hides the cut")
for t in WIPES:
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
    const HI = "#7cd0ff";""")
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

# ---------------------------------------------------------------- CUES blocks in the scene files
CUE_RE = re.compile(r"/\* CUES:BEGIN.*?/\* CUES:END \*/", re.S)
for sid, k, st, en in SCENES:
    W, Ee, D = local_words(sid)
    extra = f" const PB = {r3(END_CARD - st)};" if sid == "g-cta" else ""
    block = (f"/* CUES:BEGIN (generated by scripts/rafflesia6/build.py from the voiceover; do not edit by hand) */\n"
             f"    // words: {' '.join(x[0] for x in VO[k]['words'])}\n"
             f"    const W = {json.dumps(W)}; // word starts (s, local to this scene)\n"
             f"    const E = {json.dumps(Ee)}; // word ends\n"
             f"    const D = {r3(D)};{extra}\n"
             f"    /* CUES:END */")
    p = os.path.join(VID, "compositions", f"{sid}.html")
    s = open(p).read()
    if not CUE_RE.search(s):
        raise SystemExit(f"{sid}.html has no CUES block")
    open(p, "w").write(CUE_RE.sub(lambda _m: block, s))

print(f"total {TOTAL}s (voice ends {VO_END:.2f}s), {len(SHOTS)} shots, {len(SFX)} sfx, {len(groups)} caption groups")
for sid, k, st, en in SCENES:
    print(f"  {sid:9s} {st:6.2f} -> {en:6.2f}  ({en - st:5.2f}s)")
for sh in SHOTS:
    print(f"    shot {sh['id']:8s} {sh['start']:6.2f} -> {sh['end']:6.2f}  src {sh['src']:7.2f} -> {sh['src'] + sh['end'] - sh['start']:7.2f}")
