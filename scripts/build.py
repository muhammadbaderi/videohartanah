"""Generate video/index.html (the cut, voice, SFX, camera moves, scene hosts)
and video/compositions/captions.html from scripts/edl.json + video/captions.json.

The motion-graphics scenes in video/compositions/g-*.html are hand-written;
their hosts (start/duration) are placed here from the EDL sections.

Re-running this OVERWRITES index.html and captions.html, so edits made to
those two files in the HyperFrames Studio are lost. Scene files are untouched.

Usage: python3 -I scripts/build.py
"""
import json, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VID = os.path.join(ROOT, "video")
edl = json.load(open(os.path.join(ROOT, "scripts", "edl.json")))
cap = json.load(open(os.path.join(VID, "captions.json")))

FOOTAGE = "assets/footage/IMG_0725_1080.mp4"
VOICE = "assets/audio/voice.wav"
FPS = 30
r3 = lambda x: f"{x:.3f}".rstrip("0").rstrip(".")

# ---------------------------------------------------------------- timeline
clips, t = [], 0.0
for s in edl["segments"]:
    d = s["a_out"] - s["a_in"]
    clips.append(dict(s, start=t, dur=d, v_in=s.get("v_in", s["a_in"])))
    t += d
speech_end = t
total = round(speech_end + edl["end_hold"], 3)

sec = {}
for c in clips:
    a = sec.setdefault(c["sec"], [c["start"], c["start"] + c["dur"]])
    a[1] = c["start"] + c["dur"]
sec["cta"][1] = total  # the CTA scene runs through the end card
sec["usp"][1] += 0.5   # the privacy card lingers under the first CTA line so it can be read

def at(seg_id):
    return next(c for c in clips if c["id"] == seg_id)["start"]

def word(text, after=0.0):
    for w in cap["words"]:
        if w["start"] >= after and re.sub(r"[^\w-]", "", w["text"]).lower() == text.lower():
            return w["start"]
    raise KeyError(text)

# ---------------------------------------------------------------- SFX
# (file, peak offset inside the file in s, volume). Peaks measured with
# `npx hyperframes audio assets/sfx/*.mp3 --json`.
SFX = {
    "whoosh": ("assets/sfx/whoosh.mp3", 0.162, 0.32),
    "pop": ("assets/sfx/pop.mp3", 0.120, 0.55),
    "tick": ("assets/sfx/click-soft.mp3", 0.073, 0.75),
    "ping": ("assets/sfx/ping.mp3", 0.324, 0.6),
    "sparkle": ("assets/sfx/sparkle.mp3", 0.027, 0.16),
    "impact": ("assets/sfx/impact-bass-1.mp3", 0.073, 0.14),
}
# (event time on the edited timeline, sound, why)
cues = [
    (word("jaga"), "pop", "hook: highlight sweeps under JAGA AURAT"),
    (at("intro-a"), "whoosh", "cut: hook -> intro (flash)"),
    (word("Jalan"), "pop", "location pill lands"),
    (word("projek", 10), "tick", "'projek baru' tag"),
    (word("teres", 12), "pop", "chip: teres setingkat"),
    (word("semi-D"), "tick", "chip: semi-D"),
    (at("est"), "whoosh", "cut: establishing shot + title"),
    (word("4"), "pop", "stat card: 4 bilik tidur"),
    (word("2", 18.5), "tick", "stat card: 2 bilik air"),
    (word("20x67") + 0.55, "pop", "stat card: 20 x 67 counter lands"),
    (word("living") - 0.08, "whoosh", "label: LIVING HALL"),
    (word("15"), "ping", "dimension line lands on 15 kaki"),
    (word("tingkap"), "pop", "chip: tingkap"),
    (word("sliding"), "tick", "chip: sliding door"),
    (at("bed-a"), "whoosh", "cut: master bedroom"),
    (word("lampu"), "tick", "check: point lampu"),
    (word("kipas"), "pop", "check: point kipas"),
    (at("bath-a"), "whoosh", "cut: master bathroom"),
    (word("Belum"), "pop", "note chip: belum dipasang"),
    (word("bilik", 39.5), "tick", "label: bilik air 2"),
    (word("2", 41.5), "pop", "badge 2"),
    (word("3", 42), "tick", "badge 3"),
    (word("4", 43), "pop", "badge 4"),
    (word("kitchen"), "tick", "chip: + dapur"),
    (word("privasi") - 0.1, "whoosh", "privacy card enters"),
    (word("living", 47) , "pop", "box: living hall"),
    (word("tak", 48.5), "impact", "wall + X: tak bersambung (the payoff)"),
    (at("usp-b"), "whoosh", "cut: camera flip to selfie"),
    (word("dapur"), "pop", "box: dapur"),
    (word("Senang"), "sparkle", "badge: senang jaga aurat"),
    (at("cta-a") + 0.62, "pop", "pill: berminat? (enters 0.5 s into the CTA, after the privacy card leaves)"),
    (word("contact"), "whoosh", "phone card enters"),
    (word("016"), "tick", "digits 016"),
    (word("370"), "tick", "digits 370"),
    (word("8908"), "pop", "digits 8908"),
    (speech_end, "whoosh", "end card"),
]

# ---------------------------------------------------------------- camera
# punch-in scale per shot (jump cuts on the selfie get alternating scale)
cam_sets = [(c["start"], c.get("punch", 1.0)) for c in clips]
cam_sets.append((speech_end, 1.0))

# ---------------------------------------------------------------- HTML
out = []
w = out.append
w(f"""<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Teres Setingkat Meru - site visit</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #0b0d12; }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; }}
      #ground {{ position: absolute; inset: 0; background: #0b0d12; }}
      #cam {{ position: absolute; inset: 0; overflow: hidden; z-index: 1; }}
      #cam-inner {{ position: absolute; inset: 0; transform-origin: 50% 40%; }}
      #cam-inner video, #cam-inner img {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
      #flash {{ position: absolute; inset: 0; background: #fff; opacity: 0; z-index: 2; }}
      #dip {{ position: absolute; inset: 0; background: #000; opacity: 0; z-index: 2; }}
      .scene {{ position: absolute; inset: 0; pointer-events: none; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{r3(total)}" data-width="1080" data-height="1920">
      <div id="ground"></div>

      <!-- PICTURE: every shot is a trim of the one source file (muted; the voice is its own track) -->
      <div id="cam">
        <div id="cam-inner" data-layout-allow-overflow>""")
for c in clips:
    w(f'          <video id="v-{c["id"]}" class="clip" src="{FOOTAGE}" muted playsinline data-start="{r3(c["start"])}" data-duration="{r3(c["dur"])}" data-media-start="{r3(c["v_in"])}" data-track-index="1"></video>')
w(f'          <img id="v-endframe" class="clip" src="assets/footage/endframe.jpg" alt="" data-start="{r3(speech_end)}" data-duration="{r3(edl["end_hold"])}" data-track-index="1" />')
w("""        </div>
      </div>
      <div id="flash"></div>
      <div id="dip"></div>

      <!-- VOICE: cleaned + loudness-normalised take, same cuts as the picture -->""")
for c in clips:
    vol = 0.55 if c.get("ambient") else 1
    w(f'      <audio id="vo-{c["id"]}" class="clip" src="{VOICE}" data-start="{r3(c["start"])}" data-duration="{r3(c["dur"])}" data-media-start="{r3(c["a_in"])}" data-volume="{vol}" data-fade-in="0.012" data-fade-out="0.02" data-track-index="2"></audio>')
w("\n      <!-- SOUND EFFECTS: each one lands one frame after the thing it belongs to -->")
for i, (tev, kind, why) in enumerate(cues):
    f, peak, vol = SFX[kind]
    st = max(0.0, tev + 1 / FPS - peak)
    dur = {"whoosh": 0.575, "pop": 0.72, "tick": 0.366, "ping": 1.32, "sparkle": 1.8, "impact": 2.116}[kind]
    dur = min(dur, total - st)
    w(f'      <audio id="sfx-{i+1:02d}" class="clip" src="{f}" data-start="{r3(st)}" data-duration="{r3(dur)}" data-volume="{vol}" data-track-index="{3 + i % 2}"></audio><!-- {html.escape(why)} -->')

w("\n      <!-- MOTION GRAPHICS: one scene per chapter -->")
order = ["hook", "intro", "est", "spec", "living", "bed", "bath", "rooms", "usp", "cta"]
for i, k in enumerate(order):
    s0, s1 = sec[k]
    w(f'      <div id="g-{k}" class="scene" data-composition-id="g-{k}" data-composition-src="compositions/g-{k}.html" data-start="{r3(s0)}" data-duration="{r3(s1 - s0)}" data-track-index="{6 + i % 2}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index: 10"></div>')
w(f'      <div id="captions" class="scene" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{r3(speech_end)}" data-track-index="9" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index: 20"></div>')
w("    </div>\n    <script>\n      window.__timelines = window.__timelines || {};\n      const tl = gsap.timeline({ paused: true });")
w("      // punch-ins: the selfie jump cuts alternate framing so the cut reads as a choice")
for tt, sc in cam_sets:
    w(f'      tl.set("#cam-inner", {{ scale: {sc} }}, {r3(tt)});')

hook_end = at("intro-a")
w(f"""      // hook -> intro: flash through white
      tl.to("#flash", {{ opacity: 0.85, duration: 0.07, ease: "power2.in" }}, {r3(hook_end - 0.07)});
      tl.to("#flash", {{ opacity: 0, duration: 0.22, ease: "power2.out" }}, {r3(hook_end)});""")
for sid in ["est", "bed-a", "bath-a", "usp-a"]:
    tt = at(sid)
    w(f"""      // dip cut into {sid}
      tl.to("#dip", {{ opacity: 0.45, duration: 0.1, ease: "none" }}, {r3(tt - 0.1)});
      tl.set("#dip", {{ opacity: 0 }}, {r3(tt)});""")
tt = at("usp-b")
w(f"""      // camera flip -> short white flash hides the flip blur
      tl.to("#flash", {{ opacity: 0.6, duration: 0.05, ease: "power2.in" }}, {r3(tt - 0.05)});
      tl.to("#flash", {{ opacity: 0, duration: 0.3, ease: "power2.out" }}, {r3(tt)});""")
w(f'      tl.set({{}}, {{}}, {r3(total)});\n      window.__timelines["main"] = tl;\n    </script>\n  </body>\n</html>\n')
open(os.path.join(VID, "index.html"), "w").write("\n".join(out))

# ---------------------------------------------------------------- captions
SKIP_FROM = word("016")  # the phone number is shown on the CTA card instead
words = [x for x in cap["words"] if x["start"] < SKIP_FROM]
LIMIT = 24  # characters per caption line at 60 px
# 1) phrases: split at sentence ends and at real pauses
phrases, cur = [], []
for i, x in enumerate(words):
    cur.append(x)
    nxt = words[i + 1] if i + 1 < len(words) else None
    if nxt is None or x["text"][-1] in ".?!" or nxt["start"] - x["end"] > 0.35:
        phrases.append(cur); cur = []
# 2) each phrase -> chunks of <= 5 words and <= LIMIT characters, chosen by a
#    small DP: even lengths, no one-word orphans, prefer breaking after commas,
#    never split "okey | lah" or "rumah | ni".
import math
def chunk_cost(ws):
    chars = sum(len(x["text"]) + 1 for x in ws) - 1
    if chars > LIMIT or len(ws) > 5:
        return None
    c = (LIMIT - chars) ** 2 * 0.15
    if len(ws) == 1:
        c += 60
    return c
def break_cost(a, b):
    c = 0.0
    if a["text"].endswith(","):
        c -= 25
    if re.sub(r"[^a-z]", "", b["text"].lower()) in ("lah", "ni"):
        c += 80
    pair = (re.sub(r"[^a-z]", "", a["text"].lower()), re.sub(r"[^a-z]", "", b["text"].lower()))
    if pair in {("living", "hall"), ("bilik", "air"), ("bilik", "tidur"), ("sliding", "door"), ("master", "bedroom"),
                ("master", "bathroom"), ("toilet", "bowl"), ("teres", "setingkat"), ("site", "visit")}:
        c += 80
    return c
groups = []
for ph in phrases:
    n = len(ph)
    best = [math.inf] * (n + 1); prev = [0] * (n + 1); best[0] = 0
    for j in range(1, n + 1):
        for i in range(max(0, j - 5), j):
            cc = chunk_cost(ph[i:j])
            if cc is None or best[i] == math.inf:
                continue
            tot = best[i] + cc + (break_cost(ph[i - 1], ph[i]) if i > 0 else 0)
            if tot < best[j]:
                best[j], prev[j] = tot, i
    cuts, j = [], n
    while j > 0:
        cuts.append((prev[j], j)); j = prev[j]
    for i, j in reversed(cuts):
        groups.append(ph[i:j])
seg_end = {s["id"]: s["end"] for s in cap["segments"]}
cg = []
for gi, g in enumerate(groups):
    st = max(0.05, g[0]["start"] - 0.06)
    en = g[-1]["end"] + 0.18
    if gi + 1 < len(groups):
        en = min(en, groups[gi + 1][0]["start"] - 0.06)
    en = max(en, st + 0.45)
    cg.append((st, en, g))
# no overlaps after the min-length rule
for i in range(len(cg) - 1):
    st, en, g = cg[i]
    if en > cg[i + 1][0] - 0.02:
        cg[i] = (st, cg[i + 1][0] - 0.02, g)
assert all(en - st >= 0.3 for st, en, g in cg), [(round(st, 2), round(en, 2), [x["text"] for x in g]) for st, en, g in cg if en - st < 0.3]

c = []
a = c.append
a("""<template>
  <style>
    #root { position: absolute; inset: 0; }
    .cg { position: absolute; left: 0; top: 1205px; width: 1080px; height: 110px; }
    .cg-in { position: absolute; left: 60px; right: 60px; top: 0; text-align: center; white-space: nowrap; overflow: visible;
      font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 60px; line-height: 1.15; letter-spacing: -0.01em;
      color: #ffffff; -webkit-text-stroke: 12px rgba(0,0,0,0.92); paint-order: stroke fill;
      text-shadow: 0 6px 18px rgba(0,0,0,0.45); }
    .cw { display: inline-block; transform-origin: 50% 80%; }
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">""")
for gi, (st, en, g) in enumerate(cg):
    spans = " ".join(f'<span id="cw-{x["id"]}" class="cw">{html.escape(x["text"])}</span>' for x in g)
    a(f'    <div id="cg-{gi}" class="clip cg" data-start="{r3(st)}" data-duration="{r3(en - st)}" data-track-index="0"><div id="cgi-{gi}" class="cg-in">{spans}</div></div>')
a("""  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    const Y = "#FFC83D";""")
for gi, (st, en, g) in enumerate(cg):
    a(f'    tl.fromTo("#cgi-{gi}", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.14, ease: "power3.out" }}, {r3(st)});')
    for k, x in enumerate(g):
        on = max(x["start"], st)
        off = g[k + 1]["start"] if k + 1 < len(g) else en
        off = max(off, on + 0.14)
        a(f'    tl.fromTo("#cw-{x["id"]}", {{ color: "#ffffff", scale: 1 }}, {{ color: Y, scale: 1.05, duration: 0.08, ease: "power2.out" }}, {r3(on)});')
        if k + 1 < len(g):
            a(f'    tl.to("#cw-{x["id"]}", {{ color: "#ffffff", scale: 1, duration: 0.08, ease: "power2.in" }}, {r3(off)});')
    a(f'    tl.to("#cgi-{gi}", {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, {r3(en - 0.1)});')
    a(f'    tl.set("#cgi-{gi}", {{ opacity: 0, visibility: "hidden" }}, {r3(en)});')
a("""    window.__timelines["captions"] = tl;
  </script>
</template>
""")
open(os.path.join(VID, "compositions", "captions.html"), "w").write("\n".join(c))

print(f"total {total}s, speech ends {speech_end:.2f}s, {len(clips)} shots, {len(cues)} sfx, {len(cg)} caption groups")
for k in order:
    print(f"  g-{k:7s} {sec[k][0]:6.2f} -> {sec[k][1]:6.2f}")
