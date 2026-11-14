"""Build the Pulau Indah HyperFrames project from the voiceover timing.

Reads  scripts/vo_script.json  + video/assets/audio/vo/*.words.json  (word
timings measured on the enhanced VO by align_vo.py) + video/assets/map/map.json, and writes
  video/index.html               cut, voice, music, SFX, camera, scene hosts
  video/compositions/*.html      one motion-graphics scene per chapter + captions

Everything is timed to the voice: change a VO line, re-run make_vo.py,
enhance_vo.py and align_vo.py for it, then re-run this. Re-running OVERWRITES every file above.

Usage: python3 -I pulau-indah/scripts/build.py
"""
import html, json, os, re, subprocess
from string import Template

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(HERE, "..", "video")
COMP = os.path.join(VID, "compositions")
os.makedirs(COMP, exist_ok=True)
cfg = json.load(open(os.path.join(HERE, "vo_script.json")))
MAP = json.load(open(os.path.join(VID, "assets", "map", "map.json")))
FPS = 30
r3 = lambda x: f"{x:.3f}".rstrip("0").rstrip(".") if abs(x) > 1e-9 else "0"
FOOTAGE = "assets/footage/IMG_1360_1080.mp4"

# =============================================================== VOICE + WORDS
TOKEN = re.compile(r"\{([^|}]*)\|([^}]*)\}|\[[^\]]*\]|(\S+)")

def parse(text):
    """-> list of words: {sp: spoken word, grp: display-unit index}, and units [{text}]"""
    words, units = [], []
    for m in TOKEN.finditer(text):
        if m.group(0).startswith("["):  # [b] pause / eleven_v3 audio tag
            continue
        if m.group(1) is not None:
            units.append({"text": m.group(2)})
            for w in m.group(1).split():
                words.append({"sp": w, "grp": len(units) - 1})
        else:
            tok = m.group(3)
            if re.fullmatch(r"[.,?!]+", tok):  # punctuation glued to a {..} group
                words[-1]["sp"] += tok
                units[-1]["text"] += tok
                continue
            units.append({"text": tok})
            words.append({"sp": tok, "grp": len(units) - 1})
    return words, units

GAP_BEFORE = {"hook1": 0.12, "hook2": 0.3, "ans": 0.38, "loc1": 0.45, "loc2": 0.28, "loc3": 0.3, "lot": 0.5,
              "liv": 0.3, "mbr": 0.3, "kit": 0.3, "rooms": 0.3, "eta": 0.35, "price": 0.55, "pkg": 0.35,
              "cash": 0.35, "cta": 0.5}
GAP_BEFORE["pkg"] = 0.65  # time to read the new price
END_HOLD = 3.2
lines, t = {}, 0.0
for ln in cfg["lines"]:
    lid = ln["id"]
    # word timings measured on the final WAV by align_vo.py
    aw = json.load(open(os.path.join(VID, "assets", "audio", "vo", f"{lid}.words.json")))
    words, units = parse(ln["text"])
    assert [w["sp"] for w in words] == [w["sp"] for w in aw], (lid, [w["sp"] for w in words], [w["sp"] for w in aw])
    t += GAP_BEFORE[lid]
    for w, a in zip(words, aw):
        w["s"], w["e"] = t + a["s"], t + a["e"]
    for gi, u in enumerate(units):
        ws = [w for w in words if w["grp"] == gi]
        u["s"], u["e"] = ws[0]["s"], ws[-1]["e"]
    wav = os.path.join(VID, "assets", "audio", "vo", f"{lid}.wav")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav], capture_output=True, text=True).stdout)
    lines[lid] = {"start": t, "dur": dur, "end": t + aw[-1]["e"], "words": words, "units": units}
    t += max(aw[-1]["e"], dur - 0.12)   # the WAV keeps ~0.13 s of tail after the last voiced frame
speech_end = t
TOTAL = round(speech_end + END_HOLD, 3)
ORDER = [l["id"] for l in cfg["lines"]]
L = lambda lid: lines[lid]["start"]
def nxt(lid):
    i = ORDER.index(lid)
    return lines[ORDER[i + 1]]["start"] if i + 1 < len(ORDER) else TOTAL
norm = lambda s: re.sub(r"[^\w-]", "", s).lower()
def W(lid, sp, n=0, end=False):
    hits = [w for w in lines[lid]["words"] if norm(w["sp"]) == norm(sp)]
    return hits[n]["e" if end else "s"]

# =============================================================== PICTURE
# (line, source-in, switch-at): each shot runs until the next shot's switch time.
# Source ranges were picked from a 1 fps contact sheet of IMG_1360.MOV.
SHOTS = [
    ("hook1", 0.0, None, 5.3, "exterior row, wide"),
    ("hook2", "freeze", None, None, "freeze frame (still) for MASIH WUJUD?"),
    ("ans", 13.2, None, 17.6, "walk-up to the porch"),
    ("loc1", "map", None, None, "map scene covers the frame"),
    ("lot", 18.0, None, 23.9, "house front, porch roof"),
    ("lot", 38.4, ("lot", "Porch,"), 42.6, "looking out through the porch"),
    ("liv", 29.8, None, 34.0, "into the living hall"),
    ("mbr", 49.2, None, 54.6, "master bedroom"),
    ("mbr", 55.0, ("mbr", "bilik", 1), 57.6, "master bathroom"),
    ("kit", 65.0, None, 70.2, "kitchen + dining, back door"),
    ("rooms", 76.5, None, 78.4, "bedroom with window"),
    ("rooms", 62.4, ("rooms", "dua"), 64.8, "bathroom 2 tiles"),
    ("rooms", 73.0, ("rooms", "Cukup"), 76.4, "bedroom door"),
    ("eta", 80.0, None, 86.2, "back door -> back yard"),
    ("price", 24.0, None, 29.6, "approach to the front opening"),
    ("price", 31.0, ("price", "Sekarang,"), 37.0, "living hall, long"),
    ("pkg", 0.0, None, 5.3, "exterior row again (dimmed under the card)"),
    ("pkg", 13.1, ("pkg", "duti"), 17.6, "porch (dimmed)"),
    ("pkg", 19.0, ("pkg", "semua"), 23.9, "house front (dimmed)"),
    ("cash", "still", None, None, "blurred exterior still"),
]
shots = []
for i, (lid, src, sw, src_max, why) in enumerate(SHOTS):
    st = L(lid) - (0.0 if lid == "hook1" else 0.0)
    if sw:
        st = W(*sw) - 0.12
    if lid == "hook1":
        st = 0.0
    shots.append({"lid": lid, "src": src, "start": st, "max": src_max, "why": why})
for i, s in enumerate(shots):
    s["end"] = shots[i + 1]["start"] if i + 1 < len(shots) else L("cta")
    s["dur"] = s["end"] - s["start"]
    if isinstance(s["src"], float):
        assert s["src"] + s["dur"] <= s["max"] + 1e-6, (s, s["src"] + s["dur"])

# =============================================================== SFX
SFX = {  # file, peak offset (s), volume, length
    "whoosh": ("assets/sfx/whoosh.mp3", 0.161, 0.35, 0.57),
    "pop": ("assets/sfx/pop.mp3", 0.119, 0.5, 0.72),
    "tick": ("assets/sfx/click-soft.mp3", 0.072, 0.7, 0.37),
    "ping": ("assets/sfx/ping.mp3", 0.323, 0.5, 1.32),
    "sparkle": ("assets/sfx/sparkle.mp3", 0.026, 0.22, 1.8),
    "impact": ("assets/sfx/impact-bass-1.mp3", 0.073, 0.35, 2.12),
    "boom": ("assets/sfx/boom.mp3", 0.164, 0.55, 2.48),
    "kaching": ("assets/sfx/kaching.mp3", 0.077, 0.45, 1.48),
    "riser": ("assets/sfx/riser.mp3", 1.047, 0.35, 1.76),
    "stamp": ("assets/sfx/stamp.mp3", 0.153, 0.55, 1.0),
    "pin": ("assets/sfx/pin.mp3", 0.024, 0.5, 1.0),
}
cues = []
def cue(t_ev, kind, why):
    cues.append((t_ev, kind, why))

# =============================================================== SCENES
SCENES = []  # (id, start, end)
def scene(sid, start, end, body):
    SCENES.append((sid, start, end))
    open(os.path.join(COMP, f"{sid}.html"), "w").write(body)

BASE_CSS = """
    #root { position: absolute; inset: 0; color: #fff; font-family: "Inter", sans-serif; overflow: hidden; }
    .hd { font-family: "Montserrat", sans-serif; font-weight: 900; letter-spacing: -0.02em; line-height: 0.95; }
    .y { color: #FFC83D; }
    .glass { background: rgba(10, 12, 18, 0.82); backdrop-filter: blur(18px); box-shadow: 0 18px 50px rgba(0,0,0,0.45); }
    .kick { font-weight: 800; letter-spacing: 0.16em; font-size: 30px; color: #FFC83D; text-transform: uppercase; }
    .ctr { position: absolute; left: 0; width: 1080px; text-align: center; }
    svg.ic { fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
"""
JS_HELPERS = """
    const tl = gsap.timeline({ paused: true });
    const inUp = (s, t, d = 0.45) => tl.fromTo(s, { opacity: 0, y: 40, filter: "blur(10px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: "expo.out" }, t);
    const inPop = (s, t) => tl.fromTo(s, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.42, ease: "back.out(2.2)" }, t);
    const slam = (s, t) => tl.fromTo(s, { opacity: 0, scale: 1.9, filter: "blur(14px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.32, ease: "power4.out" }, t);
    const out = (s, t, d = 0.22) => { tl.to(s, { opacity: 0, y: -20, filter: "blur(8px)", duration: d, ease: "power2.in" }, t); tl.set(s, { visibility: "hidden" }, t + d + 0.01); };
"""
ICONS = {
    "school": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/><path d="M22 9v6"/>',
    "mosque": '<path d="M12 3c-3 2.5-5 4.5-5 7h10c0-2.5-2-4.5-5-7z"/><path d="M5 21V12h14v9"/><path d="M10 21v-4a2 2 0 0 1 4 0v4"/><path d="M3 21V9M21 21V9"/><path d="M2 21h20"/>',
    "clinic": '<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><path d="M12 8v8M8 12h8"/>',
    "cart": '<path d="M3 4h2l2.4 11h10.2L20 7H6.2"/><circle cx="9" cy="19" r="1.4"/><circle cx="17" cy="19" r="1.4"/>',
    "halal": '<path d="M12 3l2.4 2 3.1-.3.6 3.1 2.6 1.7-1.3 2.9 1.3 2.9-2.6 1.7-.6 3.1-3.1-.3L12 21l-2.4-2-3.1.3-.6-3.1-2.6-1.7 1.3-2.9-1.3-2.9 2.6-1.7.6-3.1 3.1.3z"/><path d="M9 12l2 2 4-4"/>',
    "factory": '<path d="M3 21V10l5 3V10l5 3V10l5 3V5h3v16z"/><path d="M7 17h2M12 17h2M17 17h2"/>',
    "road": '<path d="M8 3L4 21M16 3l4 18M12 4v3M12 10v4M12 17v3"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.6"/>',
    "shield": '<path d="M12 3l8 3v6c0 4.6-3.4 8-8 9-4.6-1-8-4.4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    "car": '<path d="M5 16V12l2-5h10l2 5v4"/><path d="M3.5 12h17v4.5h-17z"/><circle cx="7.5" cy="17.5" r="1.6"/><circle cx="16.5" cy="17.5" r="1.6"/>',
    "chat": '<path d="M4 19.5l1.3-3.9A8 8 0 1 1 8.4 18.7z"/><path d="M9.2 8.6c.3 2.8 2.4 5 5.2 5.6l1.3-1.3 2 1-.5 1.6c-4.4.4-8.6-3.6-8.6-8l1.6-.5 1 2z"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
}
ic = lambda k, cls="ic": f'<svg class="{cls}" viewBox="0 0 24 24">{ICONS[k]}</svg>'

def tpl(s, **kw):
    return Template(s).substitute({k: (r3(v) if isinstance(v, float) else v) for k, v in kw.items()})

# ------------------------------------------------------------------ g-hook
s0, s1 = 0.0, L("ans")
h = lambda x: x - s0
tA, tB, tC, tD = W("hook1", "Rumah"), W("hook1", "Pulau") - 0.1, W("hook1", "bawah") - 0.25, L("hook2")
scene("g-hook", s0, s1, tpl("""<template>
  <style>$BASE
    #hk-shade { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.15) 40%, rgba(0,0,0,0.15) 60%, rgba(0,0,0,0.6) 100%); }
    #hk-dark { position: absolute; inset: 0; background: rgba(5,6,10,0.62); opacity: 0; }
    #hk-tag { position: absolute; top: 250px; left: 0; width: 1080px; text-align: center; }
    #hk-tag span { display: inline-block; padding: 14px 30px; border-radius: 999px; white-space: nowrap;
      font-weight: 800; font-size: 30px; letter-spacing: 0.14em; color: #15120a; background: #FFC83D; }
    .ph { position: absolute; left: 0; width: 1080px; text-align: center; top: 640px; }
    .l1 { font-size: 68px; } .l2 { font-size: 112px; margin-top: 6px; }
    #hk-c .l2 { font-size: 148px; text-shadow: 0 0 60px rgba(255,200,61,0.35); }
    #hk-b svg { width: 84px; height: 84px; color: #FFC83D; stroke-width: 1.8; }
    .sh { text-shadow: 0 8px 30px rgba(0,0,0,0.55); }
    #hk-d { top: 620px; } #hk-d .l1 { font-size: 96px; } #hk-d .l2 { font-size: 150px; }
    #hk-q { display: inline-block; color: #FFC83D; transform-origin: 50% 85%; }
  </style>
  <div id="root" data-composition-id="g-hook" data-width="1080" data-height="1920">
    <div id="hk-shade"></div>
    <div id="hk-dark"></div>
    <div id="hk-tag"><span>PROJEK BARU · PULAU INDAH</span></div>
    <div id="hk-a" class="ph sh"><div class="hd l1">RUMAH TERES</div><div id="hk-a2" class="hd l2 y">FREEHOLD</div></div>
    <div id="hk-b" class="ph sh">$PIN<div class="hd l1" style="font-size: 66px; margin-top: 8px">DI PULAU INDAH</div></div>
    <div id="hk-c" class="ph sh"><div class="hd l1" style="font-size: 56px">HARGA BAWAH</div><div class="hd l2 y">RM300K</div></div>
    <div id="hk-d" class="ph sh"><div id="hk-d1" class="hd l1">MASIH</div><div class="hd l2"><span id="hk-d2">WUJUD</span><span id="hk-q">?</span></div></div>
  </div>
  <script>$JS
    inPop("#hk-tag", 0.05);
    inUp("#hk-a", $tA, 0.4);
    slam("#hk-a2", $tF);
    out("#hk-a", $tBo);
    inUp("#hk-b", $tB, 0.4);
    tl.fromTo("#hk-b svg", { y: -140, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, ease: "bounce.out" }, $tB);
    out("#hk-b", $tCo);
    inUp("#hk-c", $tC, 0.35);
    slam("#hk-c .l2", $tR);
    tl.fromTo("#hk-c .l2", { x: -14 }, { x: 0, duration: 0.4, ease: "elastic.out(1.2, 0.25)" }, $tR + 0.3);
    out("#hk-c", $tDo);
    out("#hk-tag", $tDo);
    tl.to("#hk-dark", { opacity: 1, duration: 0.25, ease: "power2.out" }, $tD - 0.05);
    slam("#hk-d1", $tD1);
    slam("#hk-d2", $tD2);
    tl.fromTo("#hk-q", { opacity: 0, rotation: -25, scale: 0.4 }, { opacity: 1, rotation: 0, scale: 1, duration: 0.5, ease: "back.out(3)" }, $tD2 + 0.12);
    tl.to("#hk-q", { rotation: 12, duration: 0.18, ease: "sine.inOut", yoyo: true, repeat: 3 }, $tD2 + 0.65);
    tl.to("#hk-d", { scale: 1.12, opacity: 0, filter: "blur(16px)", duration: 0.25, ease: "power2.in" }, $tEnd - 0.25);
    window.__timelines["g-hook"] = tl;
  </script>
</template>
""", BASE=BASE_CSS, JS=JS_HELPERS, PIN=ic("pin"), tA=h(tA), tF=h(W("hook1", "freehold")), tBo=h(tB - 0.22), tB=h(tB),
    tCo=h(tC - 0.22), tC=h(tC), tR=h(W("hook1", "tiga")), tDo=h(tD - 0.25), tD=h(tD), tD1=h(W("hook2", "Masih")),
    tD2=h(W("hook2", "wujud")), tEnd=h(s1)))
cue(W("hook1", "freehold"), "boom", "FREEHOLD slams in")
cue(tB, "pin", "pin drops on DI PULAU INDAH")
cue(W("hook1", "tiga"), "impact", "RM300K slams in")
cue(W("hook2", "Masih"), "whoosh", "MASIH")
cue(W("hook2", "wujud"), "boom", "WUJUD? slams in")
cue(L("ans") - 0.02, "riser", "riser into the answer (peaks on the cut)")

# ------------------------------------------------------------------ g-ans
s0, s1 = L("ans"), L("loc1")
h = lambda x: x - s0
scene("g-ans", s0, s1, tpl("""<template>
  <style>$BASE
    #an-st { position: absolute; left: 0; width: 1080px; top: 640px; text-align: center; }
    #an-st span { display: inline-block; transform: rotate(-6deg); padding: 8px 34px 14px; border: 9px solid #FFC83D;
      border-radius: 22px; color: #FFC83D; font-size: 124px; background: rgba(10,12,18,0.35); text-shadow: 0 6px 30px rgba(0,0,0,0.4); white-space: nowrap; }
    #an-live { position: absolute; left: 60px; top: 230px; display: flex; align-items: center; gap: 16px; padding: 14px 28px 14px 22px; border-radius: 999px;
      font-weight: 800; font-size: 30px; letter-spacing: 0.14em; }
    #an-dot { width: 22px; height: 22px; border-radius: 50%; background: #ff3b3b; box-shadow: 0 0 18px #ff3b3b; }
  </style>
  <div id="root" data-composition-id="g-ans" data-width="1080" data-height="1920">
    <div id="an-st"><span class="hd">WUJUD.</span></div>
    <div id="an-live" class="glass"><div id="an-dot"></div>SITE VISIT · PULAU INDAH</div>
  </div>
  <script>$JS
    tl.fromTo("#an-st", { opacity: 0, scale: 2.4 }, { opacity: 1, scale: 1, duration: 0.22, ease: "power4.in" }, $tW);
    tl.fromTo("#an-st", { y: 0 }, { y: 8, duration: 0.06, yoyo: true, repeat: 3, ease: "none" }, $tW + 0.22);
    tl.to("#an-st", { opacity: 0, scale: 0.85, filter: "blur(10px)", duration: 0.25, ease: "power2.in" }, $tWo);
    tl.set("#an-st", { visibility: "hidden" }, $tWo + 0.26);
    inUp("#an-live", $tL, 0.4);
    tl.to("#an-dot", { opacity: 0.25, duration: 0.4, yoyo: true, repeat: 5, ease: "sine.inOut" }, $tL + 0.4);
    out("#an-live", $tEnd - 0.25);
    window.__timelines["g-ans"] = tl;
  </script>
</template>
""", BASE=BASE_CSS, JS=JS_HELPERS, tW=h(W("ans", "Wujud.") - 0.12), tWo=h(W("ans", "berdiri")), tL=h(W("ans", "Dan")), tEnd=h(s1)))
cue(W("ans", "Wujud.") + 0.1, "stamp", "WUJUD. stamp lands")

# ------------------------------------------------------------------ g-map
s0, s1 = L("loc1"), L("lot")
h = lambda x: x - s0
PIN_Y = 800
lp, rp = MAP["local"]["pin"], MAP["region"]["pin"]
marks = MAP["region"]["marks"]
amen = [("school", "SK · SMK · SRA Pulau Indah", ("loc2", "Sekolah,")), ("mosque", "Masjid Sultan Abdul Aziz", ("loc2", "masjid,")),
        ("clinic", "Klinik Kesihatan", ("loc2", "klinik,")), ("cart", "99 Speedmart · Segi Fresh", ("loc2", "semua")),
        ("halal", "Selangor Halal Hub", ("loc2", "Halal")), ("factory", "Pulau Indah Industrial Park", ("loc2", "industri,"))]
roads = [("KESAS", ("loc3", "Kesas,")), ("SKVE", ("loc3", "S.K.V.E,")), ("WCE", ("loc3", "W-C-E,")),
         ("Lebuhraya Pulau Indah", ("loc3", "semua")), ("SHAPADU", ("loc3", "dah"))]
chips = "\n".join(f'    <div id="mp-a{i}" class="chip glass" style="left: {60 + (i % 2) * 490}px; top: {1010 + (i // 2) * 100}px">{ic(k)}<span>{html.escape(t)}</span></div>'
                  for i, (k, t, _) in enumerate(amen))
rchips = "\n".join(f'    <div id="mp-r{i}" class="chip glass {"big" if i < 3 else ""}" style="left: {[60, 400, 740, 60, 590][i]}px; top: {[1010, 1010, 1010, 1130, 1130][i]}px; width: {[300, 300, 280, 490, 430][i]}px">{ic("road")}<span>{html.escape(t)}</span></div>'
                   for i, (t, _) in enumerate(roads))
mlabels = "\n".join(f'    <div id="mp-m{i}" class="mk" style="left: {x}px; top: {y + PIN_Y - rp[1]}px"><i></i><span>{html.escape(n.upper())}</span></div>'
                    for i, (n, (x, y)) in enumerate(marks.items()) if n != "Westport")
js_a = "\n".join(f'    inPop("#mp-a{i}", {r3(h(W(*w)))});' for i, (_, _, w) in enumerate(amen))
js_r = "\n".join(f'    inPop("#mp-r{i}", {r3(h(W(*w)))});' for i, (_, w) in enumerate(roads))
tZ = L("loc3")
scene("g-map", s0, s1, tpl("""<template>
  <style>$BASE
    #mp-bg { position: absolute; inset: 0; background: #0b0f14; }
    .mw { position: absolute; inset: 0; transform-origin: 540px ${PY}px; }
    .mw img { position: absolute; left: 0; width: 1080px; }
    #mp-li { top: ${LT}px; height: ${LH}px; } #mp-ri { top: ${RT}px; height: ${RH}px; }
    #mp-tint { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(5,7,10,0.75) 0%, rgba(5,7,10,0.1) 26%, rgba(5,7,10,0.05) 45%, rgba(5,7,10,0.7) 62%, rgba(5,7,10,0.88) 100%); }
    #mp-pin { position: absolute; left: 488px; top: ${PT}px; width: 104px; height: 104px; color: #15120a; }
    #mp-pin .body { position: absolute; inset: 0; }
    #mp-pin svg { width: 104px; height: 104px; fill: #FFC83D; stroke: #15120a; stroke-width: 1.2; filter: drop-shadow(0 8px 14px rgba(0,0,0,0.6)); }
    .ring { position: absolute; left: 540px; top: ${PY}px; width: 60px; height: 60px; margin: -30px 0 0 -30px; border-radius: 50%; border: 5px solid #FFC83D; opacity: 0; }
    #mp-lab { position: absolute; left: 0; width: 1080px; top: ${LBT}px; text-align: center; }
    #mp-lab span { display: inline-block; padding: 12px 26px; border-radius: 16px; white-space: nowrap;
      font-weight: 800; font-size: 30px; letter-spacing: 0.08em; background: #FFC83D; color: #15120a; }
    #mp-title { position: absolute; left: 60px; right: 60px; top: 220px; padding: 30px 36px; border-radius: 30px; }
    #mp-title .t1 { font-size: 66px; margin-top: 10px; } #mp-title .t2 { font-size: 34px; font-weight: 600; opacity: 0.85; margin-top: 10px; }
    .chip { position: absolute; height: 84px; width: 470px; border-radius: 22px; display: flex; align-items: center; gap: 16px; padding: 0 22px;
      font-weight: 700; font-size: 29px; white-space: nowrap; }
    .chip svg { width: 46px; height: 46px; flex: none; color: #FFC83D; }
    .chip.big { font-family: "Montserrat", sans-serif; font-weight: 900; font-size: 44px; height: 100px; }
    .mk { position: absolute; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; gap: 8px; }
    .mk i { width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 5px rgba(255,255,255,0.25); }
    .mk span { font-weight: 800; font-size: 28px; letter-spacing: 0.1em; text-shadow: 0 2px 10px #000, 0 0 3px #000; white-space: nowrap; }
    #mp-m0 { transform: translate(-80%, -50%); }
    #mp-cr { position: absolute; left: 24px; bottom: 26px; font-size: 18px; opacity: 0.6; }
  </style>
  <div id="root" data-composition-id="g-map" data-width="1080" data-height="1920">
    <div id="mp-bg"></div>
    <div id="mp-r" class="mw"><img id="mp-ri" src="assets/map/map-region.jpg" alt="" /></div>
    <div id="mp-l" class="mw"><img id="mp-li" src="assets/map/map-local.jpg" alt="" /></div>
    <div id="mp-tint"></div>
$MARKS
    <div class="ring" id="mp-ring1"></div><div class="ring" id="mp-ring2"></div>
    <div id="mp-pin"><div class="body">$PINSVG</div></div>
    <div id="mp-lab"><span>PROJEK BARU</span></div>
    <div id="mp-title" class="glass"><div class="kick">Lokasi</div><div class="hd t1">PERSIARAN MASJID SULTAN</div><div class="t2">Pulau Indah, Klang · Selangor</div></div>
$CHIPS
$RCHIPS
    <div id="mp-cr" data-layout-ignore>Imej satelit: Esri, Maxar, Earthstar Geographics</div>
  </div>
  <script>$JS
    tl.fromTo("#mp-l", { scale: 1.7, filter: "blur(6px)" }, { scale: 1, filter: "blur(0px)", duration: 1.5, ease: "expo.out" }, 0);
    tl.fromTo("#mp-root-fade", {}, {}, 0);
    inUp("#mp-title", $tT, 0.5);
    tl.fromTo("#mp-pin", { y: -260, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: "bounce.out" }, $tP);
    inPop("#mp-lab", $tP + 0.35);
    const ring = (s, t0) => { tl.set(s, { opacity: 0, scale: 0.3 }, 0); for (let k = 0; k < 7; k++) tl.fromTo(s, { scale: 0.3, opacity: 0.9 }, { scale: 4.2, opacity: 0, duration: 1.6, ease: "power1.out" }, t0 + k * 1.6); };
    ring("#mp-ring1", $tP + 0.5); ring("#mp-ring2", $tP + 1.3);
$JSA
    // zoom out to the region: Klang, Pelabuhan Klang and the highways
    out(["#mp-a0", "#mp-a1", "#mp-a2", "#mp-a3", "#mp-a4", "#mp-a5"], $tZ - 0.3, 0.2);
    out("#mp-lab", $tZ - 0.3, 0.2);
    out("#mp-title", $tZ - 0.3, 0.25);
    tl.to("#mp-l", { scale: 0.125, opacity: 0, duration: 1.2, ease: "power3.inOut" }, $tZ - 0.1);
    tl.fromTo("#mp-r", { scale: 8 }, { scale: 1, duration: 1.2, ease: "power3.inOut" }, $tZ - 0.1);
    tl.to("#mp-pin", { scale: 0.75, duration: 1.2, ease: "power3.inOut" }, $tZ - 0.1);
    tl.fromTo([".mk"], { opacity: 0 }, { opacity: 1, duration: 0.4, stagger: 0.15, ease: "power2.out" }, $tZ + 0.9);
$JSR
    tl.to("#root", { opacity: 0, duration: 0.25, ease: "power2.in" }, $tEnd - 0.25);
    window.__timelines["g-map"] = tl;
  </script>
</template>
""", BASE=BASE_CSS, JS=JS_HELPERS, PY=str(PIN_Y), LT=r3(PIN_Y - lp[1]), LH=str(MAP["local"]["h"]), RT=r3(PIN_Y - rp[1]),
    RH=str(MAP["region"]["h"]), PT=str(PIN_Y - 98), LBT=str(PIN_Y + 30), PINSVG='<svg viewBox="0 0 24 24"><path d="M12 22s-7.5-6.6-7.5-12.3a7.5 7.5 0 0 1 15 0C19.5 15.4 12 22 12 22z"/><circle cx="12" cy="9.7" r="2.8" fill="#15120a"/></svg>',
    MARKS=mlabels, CHIPS=chips, RCHIPS=rchips, JSA=js_a, JSR=js_r, tT=h(W("loc1", "Projek") + 0.05), tP=h(W("loc1", "Persiaran")),
    tZ=h(tZ), tEnd=h(s1)).replace('    tl.fromTo("#mp-root-fade", {}, {}, 0);\n', ""))
cue(L("loc1") - 0.05, "whoosh", "cut into the map (zoom)")
cue(W("loc1", "Persiaran") + 0.45, "pin", "pin lands")
for i, (_, _, w) in enumerate(amen):
    cue(W(*w), "pop" if i % 2 == 0 else "tick", f"amenity chip {i}")
cue(tZ - 0.1, "whoosh", "zoom out to the region")
for i, (_, w) in enumerate(roads):
    cue(W(*w), "pop" if i < 3 else "tick", f"highway chip {i}")

# ------------------------------------------------------------------ g-plan (floor plan, lot -> rooms)
s0, s1 = L("lot"), L("eta")
h = lambda x: x - s0
# rooms in mm from the S&P floor plan (left unit), origin = rear boundary, x across the 20 ft frontage
R = {"yard": (0, 0, 6096, 1220), "b3": (0, 1220, 3048, 3150), "b2": (0, 4370, 3048, 3600), "rt": (0, 7970, 3048, 5442),
     "dp": (3048, 1220, 3048, 5000), "ba2": (4100, 6220, 1996, 1600), "ba1": (4100, 7820, 1996, 1380), "hall": (3048, 6220, 1052, 2980),
     "bu": (3048, 9200, 3048, 4212), "porch": (0, 13412, 6096, 6096)}
LBL = {"b3": "BILIK 3", "b2": "BILIK 2", "rt": "RUANG\nTAMU", "dp": "DAPUR\n& MAKAN", "ba2": "B.AIR 2", "ba1": "B.AIR 1", "bu": "BILIK\nUTAMA", "porch": "PORCH"}
svg = ['<svg id="pl-svg" data-layout-ignore viewBox="-300 -300 6696 20108" width="300" height="901">']
for k, (x, y, w, hh) in R.items():
    fill = "rgba(255,255,255,0.04)" if k not in ("yard", "porch") else "rgba(255,255,255,0.02)"
    svg.append(f'<rect class="rm" x="{x}" y="{y}" width="{w}" height="{hh}" fill="{fill}" stroke="rgba(255,255,255,0.9)" stroke-width="60"/>')
    svg.append(f'<rect id="hl-{k}" x="{x + 30}" y="{y + 30}" width="{w - 60}" height="{hh - 60}" fill="#FFC83D" opacity="0"/>')
for k, txt in LBL.items():
    x, y, w, hh = R[k]
    parts = txt.split("\n")
    fs = 420 if len(max(parts, key=len)) <= 7 else 360
    if k in ("ba1", "ba2"):
        fs = 300
    for j, p in enumerate(parts):
        yy = y + hh / 2 + (j - (len(parts) - 1) / 2) * fs * 1.1 + fs * 0.35
        svg.append(f'<text class="lb" x="{x + w / 2}" y="{yy:.0f}" font-size="{fs}" text-anchor="middle">{p}</text>')
for k, n in (("bu", 1), ("b2", 2), ("b3", 3)):
    x, y, w, hh = R[k]
    svg.append(f'<g id="nb-{k}" opacity="0"><circle cx="{x + w - 520}" cy="{y + 520}" r="380" fill="#FFC83D"/><text x="{x + w - 520}" y="{y + 660}" font-size="420" text-anchor="middle" fill="#15120a" font-weight="900">{n}</text></g>')
for j in range(2):  # two cars in the porch
    svg.append(f'<g transform="translate({600 + j * 2700} {14200})"><g id="car{j}" opacity="0"><rect width="2200" height="4400" rx="500" fill="#FFC83D"/><rect x="250" y="900" width="1700" height="1000" rx="250" fill="#15120a" opacity="0.7"/><rect x="250" y="2900" width="1700" height="800" rx="250" fill="#15120a" opacity="0.7"/></g></g>')
# dimension lines: 20' across the top, 64' down the side
svg.append('<g id="dim-w" stroke="#FFC83D" stroke-width="70" fill="none"><path id="dim-wp" d="M0 -180 H6096" stroke-dasharray="6096" stroke-dashoffset="6096"/></g>')
svg.append('<g id="dim-d" stroke="#FFC83D" stroke-width="70" fill="none"><path id="dim-dp" d="M-180 0 V19508" stroke-dasharray="19508" stroke-dashoffset="19508"/></g>')
svg.append("</svg>")
SVG = "\n      ".join(svg)
tLot = {"teres": W("lot", "Teres"), "dua": W("lot", "dua"), "kaki": W("lot", "kaki."), "porch": W("lot", "Porch,")}
scene("g-plan", s0, s1, tpl("""<template>
  <style>$BASE
    #pl { position: absolute; left: 60px; top: 300px; width: 340px; padding: 20px; border-radius: 30px; transform-origin: 0 0; }
    #pl-k { font-weight: 800; font-size: 22px; letter-spacing: 0.18em; color: #FFC83D; margin: 0 0 10px 4px; }
    #pl svg text.lb { fill: #fff; font-family: "Inter", sans-serif; font-weight: 800; opacity: 0.88; }
    .dl { position: absolute; font-family: "Montserrat", sans-serif; font-weight: 900; color: #FFC83D; font-size: 34px; opacity: 0; }
    #dl-w { left: 150px; top: 36px; } #dl-d { left: -6px; top: 520px; transform: rotate(-90deg); }
    .cd { position: absolute; left: 450px; width: 570px; border-radius: 28px; padding: 26px 30px; }
    .cd .v { font-size: 104px; margin-top: 6px; white-space: nowrap; }
    .cd .s { font-size: 30px; font-weight: 600; opacity: 0.85; margin-top: 8px; }
    #cd-car svg { width: 70px; height: 70px; color: #FFC83D; margin-right: 6px; }
    #lt { position: absolute; left: 60px; top: 1120px; padding: 22px 34px 24px; border-radius: 26px; max-width: 760px; }
    #lt .v { font-size: 66px; margin-top: 6px; white-space: nowrap; }
    #pv { position: absolute; left: 60px; top: 1000px; display: flex; align-items: center; gap: 14px; padding: 14px 26px 14px 18px; border-radius: 999px;
      background: #FFC83D; color: #15120a; font-weight: 900; font-size: 32px; letter-spacing: 0.08em; }
    #pv svg { width: 44px; height: 44px; }
    .cnt { position: absolute; left: 60px; top: 990px; display: flex; gap: 16px; }
    .cnt div { padding: 14px 26px; border-radius: 20px; font-family: "Montserrat", sans-serif; font-weight: 900; font-size: 40px; }
  </style>
  <div id="root" data-composition-id="g-plan" data-width="1080" data-height="1920">
    <div id="pl" class="glass">
      <div id="pl-k" data-layout-ignore>PELAN LANTAI</div>
      <div style="position: relative">
      $SVG
      <div id="dl-w" class="dl">20'</div><div id="dl-d" class="dl">64'</div>
      </div>
    </div>
    <div id="cd-t" class="cd glass" style="top: 300px"><div class="kick">Jenis</div><div class="hd v" style="font-size: 58px">TERES 1 TINGKAT</div><div class="s">Freehold · Rizab Melayu</div></div>
    <div id="cd-l" class="cd glass" style="top: 520px"><div class="kick">Luas tanah</div><div class="hd v"><span id="n-w">20</span>' × <span id="n-d">64</span>'</div><div class="s">1,280 kaki persegi<br />Luas binaan 20' × 40'</div></div>
    <div id="cd-car" class="cd glass" style="top: 830px"><div class="kick">Porch</div><div class="hd v" style="font-size: 64px; display: flex; align-items: center">$CAR$CAR MUAT 2</div></div>
    <div id="lt" class="glass"><div id="lt-k" class="kick">Ruang</div><div id="lt-v" class="hd v">RUANG TAMU</div></div>
    <div id="pv">$SHIELD LEBIH PRIVASI</div>
    <div id="cnt" class="cnt"><div id="cnt1" style="background: #FFC83D; color: #15120a">3 BILIK TIDUR</div><div id="cnt2" class="glass">2 BILIK AIR</div></div>
  </div>
  <script>$JS
    // --- lot: big plan on the left, spec cards on the right
    tl.fromTo("#pl", { opacity: 0, x: -120 }, { opacity: 1, x: 0, duration: 0.5, ease: "expo.out" }, 0.05);
    tl.fromTo(".rm", { opacity: 0 }, { opacity: 1, duration: 0.25, stagger: 0.04, ease: "power1.out" }, 0.15);
    inUp("#cd-t", $tTeres);
    inUp("#cd-l", $tDua);
    tl.to("#dim-wp", { strokeDashoffset: 0, duration: 0.5, ease: "power2.out" }, $tDua);
    tl.to("#dim-dp", { strokeDashoffset: 0, duration: 0.7, ease: "power2.out" }, $tDua + 0.2);
    tl.to(["#dl-w", "#dl-d"], { opacity: 1, duration: 0.3, stagger: 0.2 }, $tDua + 0.35);
    const n = { w: 0, d: 0 };
    tl.fromTo(n, { w: 0, d: 0 }, { w: 20, d: 64, duration: 0.9, ease: "power2.out",
      onUpdate: () => { document.getElementById("n-w").textContent = Math.round(n.w); document.getElementById("n-d").textContent = Math.round(n.d); } }, $tDua);
    tl.to("#hl-porch", { opacity: 0.25, duration: 0.25 }, $tPorch);
    tl.fromTo(["#car0", "#car1"], { opacity: 0, y: 1200 }, { opacity: 1, y: 0, duration: 0.45, stagger: 0.15, ease: "back.out(1.6)" }, $tPorch);
    inUp("#cd-car", $tPorch);
    out(["#cd-t", "#cd-l", "#cd-car"], $tLiv - 0.3, 0.2);
    tl.to(["#dl-w", "#dl-d", "#dim-w", "#dim-d", "#car0", "#car1"], { opacity: 0, duration: 0.2 }, $tLiv - 0.3);
    tl.to("#hl-porch", { opacity: 0, duration: 0.2 }, $tLiv - 0.3);
    // --- tour: the plan shrinks to the top-right corner and follows the rooms
    tl.to("#pl", { x: 742, y: -60, scale: 0.6, duration: 0.6, ease: "power3.inOut" }, $tLiv - 0.2);
    const hl = (k, t, o = 0.62) => tl.to("#hl-" + k, { opacity: o, duration: 0.25, ease: "power2.out" }, t);
    const un = (ks, t) => tl.to(ks.map(k => "#hl-" + k), { opacity: 0, duration: 0.2 }, t);
    tl.set("#lt", { opacity: 0 }, 0);
    const lt = (k, v, t) => { tl.set("#lt-k", { textContent: k }, t); tl.set("#lt-v", { textContent: v }, t);
      tl.fromTo("#lt", { opacity: 0, x: -60 }, { opacity: 1, x: 0, duration: 0.4, ease: "expo.out" }, t); };
    hl("rt", $tLiv + 0.1); lt("Masuk je", "RUANG TAMU", $tLiv + 0.1);
    un(["rt"], $tMbr - 0.1); hl("bu", $tMbr); lt("Master", "BILIK UTAMA", $tMbr);
    hl("ba1", $tSiap); lt("+ Bilik air sendiri", "BILIK AIR 1", $tSiap);
    un(["bu", "ba1"], $tKit - 0.1); hl("dp", $tKit); lt("Belakang", "DAPUR & MAKAN", $tKit);
    tl.to("#hl-rt", { opacity: 0.22, duration: 0.2, yoyo: true, repeat: 3 }, $tPisah);
    tl.fromTo("#pv", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.42, ease: "back.out(2.2)" }, $tPriv);
    out("#pv", $tRooms - 0.25);
    un(["dp", "rt"], $tRooms - 0.1);
    out("#lt", $tRooms - 0.25);
    tl.set("#lt", { visibility: "visible" }, $tRooms + 0.2);
    ["bu", "b2", "b3"].forEach((k, i) => { hl(k, $tTiga + i * 0.15); inPop("#nb-" + k, $tTiga + i * 0.15); });
    inUp("#cnt1", $tTiga, 0.4);
    hl("ba1", $tDua2, 0.8); hl("ba2", $tDua2 + 0.12, 0.8);
    tl.set(["#hl-ba1", "#hl-ba2"], { fill: "#5ec8ff" }, $tDua2);
    inUp("#cnt2", $tDua2, 0.4);
    tl.to("#root", { opacity: 0, duration: 0.25, ease: "power2.in" }, $tEnd - 0.25);
    window.__timelines["g-plan"] = tl;
  </script>
</template>
""", BASE=BASE_CSS, JS=JS_HELPERS, SVG=SVG, CAR=ic("car"), SHIELD=ic("shield"),
    tTeres=h(tLot["teres"]), tDua=h(tLot["dua"]), tPorch=h(tLot["porch"]), tLiv=h(L("liv")), tMbr=h(L("mbr")), tSiap=h(W("mbr", "bilik", 1)),
    tKit=h(L("kit")), tPisah=h(W("kit", "terpisah")), tPriv=h(W("kit", "privasi.")), tRooms=h(L("rooms")), tTiga=h(W("rooms", "Tiga")),
    tDua2=h(W("rooms", "dua")), tEnd=h(s1)))
cue(L("lot") - 0.05, "whoosh", "plan card slides in")
cue(tLot["teres"], "tick", "card: teres 1 tingkat")
cue(tLot["dua"], "pop", "card: 20 x 64 counter")
cue(tLot["dua"] + 0.9, "tick", "counter lands")
cue(tLot["porch"], "pop", "cars drop into the porch")
cue(L("liv") - 0.2, "whoosh", "plan moves to the corner")
cue(L("mbr"), "tick", "highlight: bilik utama")
cue(W("mbr", "bilik", 1), "tick", "highlight: bilik air 1")
cue(L("kit"), "tick", "highlight: dapur")
cue(W("kit", "privasi."), "ping", "badge: lebih privasi")
cue(W("rooms", "Tiga"), "pop", "3 bilik tidur")
cue(W("rooms", "dua"), "pop", "2 bilik air")

# ------------------------------------------------------------------ g-eta
s0, s1 = L("eta"), L("price")
h = lambda x: x - s0
scene("g-eta", s0, s1, tpl("""<template>
  <style>$BASE
    #et { position: absolute; left: 60px; right: 60px; top: 300px; padding: 34px 40px 40px; border-radius: 34px; }
    .row { display: flex; align-items: center; gap: 22px; margin-top: 18px; }
    .dot { width: 84px; height: 84px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex: none; }
    .dot svg { width: 52px; height: 52px; stroke-width: 2.6; }
    #et-d1 { background: #FFC83D; color: #15120a; } #et-d2 { border: 5px solid #FFC83D; color: #FFC83D; }
    .tx { font-size: 58px; } .tx small { display: block; font-family: "Inter", sans-serif; font-size: 28px; font-weight: 600; letter-spacing: 0; opacity: 0.8; margin-bottom: 6px; }
    #et-bar { position: relative; height: 14px; border-radius: 7px; background: rgba(255,255,255,0.15); margin: 26px 0 8px 102px; overflow: hidden; }
    #et-fill { position: absolute; left: 0; top: 0; bottom: 0; width: 100%; background: #FFC83D; transform-origin: 0 50%; }
    #et-q { font-size: 120px; }
  </style>
  <div id="root" data-composition-id="g-eta" data-width="1080" data-height="1920">
    <div id="et" class="glass">
      <div class="kick">Status projek</div>
      <div id="et-r1" class="row"><div id="et-d1" class="dot">$CHECK</div><div class="hd tx"><small>Sekarang</small>STRUKTUR SIAP</div></div>
      <div id="et-bar"><div id="et-fill"></div></div>
      <div id="et-r2" class="row"><div id="et-d2" class="dot">$CLOCK</div><div class="hd tx"><small>Dijangka siap sepenuhnya</small><span id="et-q" class="y">Q3 2027</span></div></div>
    </div>
  </div>
  <script>$JS
    tl.set("#et-fill", { scaleX: 0 }, 0);
    inUp("#et", $tA, 0.45);
    tl.fromTo("#et-r1", { opacity: 0, x: -40 }, { opacity: 1, x: 0, duration: 0.4, ease: "expo.out" }, $tA + 0.1);
    tl.fromTo("#et-d1", { scale: 0.4 }, { scale: 1, duration: 0.45, ease: "back.out(2.4)" }, $tA + 0.15);
    tl.fromTo("#et-r2", { opacity: 0 }, { opacity: 0.35, duration: 0.3 }, $tA + 0.3);
    tl.to("#et-fill", { scaleX: 0.72, duration: 1.4, ease: "power2.inOut" }, $tB - 0.6);
    tl.to("#et-r2", { opacity: 1, duration: 0.3 }, $tB);
    tl.fromTo("#et-q", { opacity: 0, scale: 1.6, filter: "blur(10px)" }, { opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.35, ease: "power4.out" }, $tQ);
    tl.set("#et-q", { display: "inline-block", transformOrigin: "0% 60%" }, 0);
    out("#et", $tEnd - 0.25);
    window.__timelines["g-eta"] = tl;
  </script>
</template>
""", BASE=BASE_CSS, JS=JS_HELPERS, CHECK=ic("check"), CLOCK=ic("clock"), tA=h(W("eta", "Struktur")), tB=h(W("eta", "Dijangka")),
    tQ=h(W("eta", "suku")), tEnd=h(s1)))
cue(W("eta", "Struktur"), "pop", "status card: struktur siap")
cue(W("eta", "suku"), "impact", "Q3 2027 lands")

# ------------------------------------------------------------------ g-price
s0, s1 = L("price"), L("pkg")
h = lambda x: x - s0
tOld, tNow = W("price", "Harga"), W("price", "Sekarang,")
tNum = W("price", "dua", 1)
scene("g-price", s0, s1, tpl("""<template>
  <style>$BASE
    #pr-dim { position: absolute; inset: 0; background: rgba(5,6,10,0.55); }
    #pr, #pr-b { position: absolute; left: 60px; right: 60px; padding: 36px 44px 40px; border-radius: 36px; text-align: center; }
    #pr { top: 330px; } #pr-b { top: 640px; }
    #pr-old { position: relative; display: inline-block; font-size: 112px; margin-top: 8px; }
    #pr-x { position: absolute; left: -12px; right: -12px; top: 50%; height: 12px; margin-top: -6px; background: #ff4d4d; border-radius: 6px;
      transform-origin: 0 50%; }
    #pr-now { font-size: 150px; margin-top: 14px; white-space: nowrap; text-shadow: 0 0 50px rgba(255,200,61,0.35); }
    #pr-sv { display: inline-block; margin-top: 22px; padding: 14px 30px; border-radius: 999px; background: #2ecc71; color: #06210f; font-weight: 900; font-size: 36px; letter-spacing: 0.06em; }
  </style>
  <div id="root" data-composition-id="g-price" data-width="1080" data-height="1920">
    <div id="pr-dim"></div>
    <div id="pr" class="glass"><div class="kick" style="color: #fff; opacity: 0.75">Harga asal</div><div id="pr-old" class="hd">RM299,500<div id="pr-x"></div></div></div>
    <div id="pr-b" class="glass"><div class="kick">Sekarang dari</div><div id="pr-now" class="hd y">RM<span id="pr-n">299,500</span></div><div id="pr-sv">JIMAT RM9,000</div></div>
  </div>
  <script>$JS
    tl.fromTo("#pr-dim", { opacity: 0 }, { opacity: 1, duration: 0.3 }, 0);
    inUp("#pr", $tOld - 0.05, 0.5);
    tl.set("#pr-x", { scaleX: 0, rotation: -6 }, 0);
    tl.set("#pr-b", { opacity: 0 }, 0);
    tl.to("#pr-x", { scaleX: 1, rotation: -6, duration: 0.35, ease: "power3.out" }, $tX);
    tl.to("#pr-old", { opacity: 0.45, duration: 0.3 }, $tX + 0.2);
    tl.to("#pr-b", { opacity: 1, y: 0, duration: 0.45, ease: "expo.out" }, $tNow);
    const p = { v: 299500 };
    tl.fromTo(p, { v: 299500 }, { v: 290500, duration: 1.1, ease: "power3.out",
      onUpdate: () => { document.getElementById("pr-n").textContent = (Math.round(p.v / 100) * 100).toLocaleString("en-US"); } }, $tNum);
    tl.fromTo("#pr-now", { scale: 1 }, { scale: 1.08, duration: 0.14, yoyo: true, repeat: 1, ease: "power2.out" }, $tNum + 1.1);
    tl.fromTo("#pr-sv", { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1, duration: 0.42, ease: "back.out(2.4)" }, $tNum + 1.3);
    out(["#pr", "#pr-b"], $tEnd - 0.25);
    window.__timelines["g-price"] = tl;
  </script>
</template>
""", BASE=BASE_CSS, JS=JS_HELPERS, tOld=h(tOld), tX=h(tNow - 0.45), tNow=h(tNow), tNum=h(tNum), tEnd=h(s1)))
cue(tOld - 0.05, "whoosh", "price card in")
cue(tNow - 0.45, "tick", "red strike through the old price")
cue(tNum + 1.1, "kaching", "new price lands")
cue(tNum + 1.3, "pop", "JIMAT RM9,000")

# ------------------------------------------------------------------ g-pkg
s0, s1 = L("pkg"), L("cash")
h = lambda x: x - s0
items = [("BOOKING", "RM500", ("pkg", "Booking,")), ("FREE", "Legal fee SPA", ("pkg", "Legal")), ("FREE", "Legal fee loan", ("pkg", "legal")),
         ("FREE", "Duti setem loan", ("pkg", "duti")), ("FREE", "MOT fee", ("pkg", "M.O.T,"))]
def Wn(lid, sp, n):
    hits = [w for w in lines[lid]["words"] if norm(w["sp"]) == norm(sp)]
    return hits[n]["s"]
item_t = [W("pkg", "Booking,"), Wn("pkg", "legal", 0), Wn("pkg", "legal", 1), W("pkg", "duti"), W("pkg", "M.O.T,")]
rows = "\n".join(f'      <div id="pk-{i}" class="it"><div class="ck">{ic("check")}</div><div class="tg {"bk" if i == 0 else ""}">{a}</div><div class="nm">{html.escape(b)}</div></div>'
                 for i, (a, b, _) in enumerate(items))
js_rows = "\n".join(f'    tl.fromTo("#pk-{i}", {{ opacity: 0.0, x: -50 }}, {{ opacity: 1, x: 0, duration: 0.35, ease: "expo.out" }}, {r3(h(t) - 0.05)});\n'
                    f'    tl.fromTo("#pk-{i} .ck", {{ scale: 0.3, rotation: -40 }}, {{ scale: 1, rotation: 0, duration: 0.45, ease: "back.out(2.6)" }}, {r3(h(t))});'
                    for i, t in enumerate(item_t))
scene("g-pkg", s0, s1, tpl("""<template>
  <style>$BASE
    #pk-dim { position: absolute; inset: 0; background: rgba(5,6,10,0.6); }
    #pk { position: absolute; left: 60px; right: 60px; top: 280px; padding: 36px 40px 30px; border-radius: 36px; }
    #pk .hd.t { font-size: 76px; margin: 8px 0 18px; }
    .it { display: flex; align-items: center; gap: 22px; height: 112px; border-top: 2px solid rgba(255,255,255,0.1); }
    .ck { width: 68px; height: 68px; border-radius: 50%; background: #FFC83D; color: #15120a; display: flex; align-items: center; justify-content: center; flex: none; }
    .ck svg { width: 42px; height: 42px; stroke-width: 3; }
    .tg { padding: 8px 18px; border-radius: 12px; background: #2ecc71; color: #06210f; font-weight: 900; font-size: 30px; letter-spacing: 0.08em; }
    .tg.bk { background: #fff; color: #15120a; }
    .nm { font-weight: 800; font-size: 46px; white-space: nowrap; }
    #pk-st { position: absolute; left: 0; width: 1080px; top: 1010px; text-align: center; }
    #pk-st span { display: inline-block; transform: rotate(-5deg); padding: 10px 40px 16px; border: 10px solid #2ecc71; border-radius: 22px;
      color: #2ecc71; font-size: 104px; white-space: nowrap; background: rgba(6,20,12,0.6); }
  </style>
  <div id="root" data-composition-id="g-pkg" data-width="1080" data-height="1920">
    <div id="pk-dim"></div>
    <div id="pk" class="glass">
      <div class="kick">Pakej pembeli</div>
      <div class="hd t">SEMUA DAH COVER</div>
$ROWS
    </div>
    <div id="pk-st"><span class="hd">SEMUA PERCUMA</span></div>
  </div>
  <script>$JS
    tl.fromTo("#pk-dim", { opacity: 0 }, { opacity: 1, duration: 0.3 }, 0);
    inUp("#pk", 0.02, 0.45);
    tl.set([".it"], { opacity: 0 }, 0);
$JSROWS
    tl.fromTo("#pk-st", { opacity: 0, scale: 2.2 }, { opacity: 1, scale: 1, duration: 0.22, ease: "power4.in" }, $tS - 0.12);
    tl.to("#root", { opacity: 0, duration: 0.25, ease: "power2.in" }, $tEnd - 0.25);
    window.__timelines["g-pkg"] = tl;
  </script>
</template>
""", BASE=BASE_CSS, JS=JS_HELPERS, ROWS=rows, JSROWS=js_rows, tS=h(W("pkg", "semua")), tEnd=h(s1)))
cue(L("pkg") - 0.05, "whoosh", "package card in")
for i, t in enumerate(item_t):
    cue(t, "pop" if i % 2 == 0 else "tick", f"package row {i}")
cue(W("pkg", "semua") + 0.1, "stamp", "SEMUA PERCUMA stamp")

# ------------------------------------------------------------------ g-cash
s0, s1 = L("cash"), L("cta")
h = lambda x: x - s0
import math
coins = "\n".join(f'    <div class="coin" id="cn{i}"></div>' for i in range(14))
coin_js = "\n".join(
    f'    tl.fromTo("#cn{i}", {{ x: 0, y: 0, opacity: 1, scale: 0.4 }}, {{ x: {math.cos(i / 14 * 6.283 + 0.3) * (260 + (i * 37) % 160):.0f}, y: {math.sin(i / 14 * 6.283 + 0.3) * (220 + (i * 53) % 140):.0f}, opacity: 0, scale: 1.1, duration: 1.1, ease: "power3.out" }}, $tC + 1.0);'
    for i in range(14))
scene("g-cash", s0, s1, tpl(f"""<template>
  <style>$BASE
    #cs-bg {{ position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    #cs-dim {{ position: absolute; inset: 0; background: radial-gradient(circle at 50% 42%, rgba(40,30,5,0.55), rgba(5,6,10,0.85) 70%); }}
    #cs-k {{ top: 470px; font-size: 40px; }}
    #cs-a {{ top: 560px; font-size: 120px; }}
    #cs-n {{ top: 700px; font-size: 210px; white-space: nowrap; text-shadow: 0 0 70px rgba(255,200,61,0.45); }}
    #cs-s {{ top: 950px; font-size: 38px; font-weight: 700; opacity: 0.9; }}
    .coin {{ position: absolute; left: 520px; top: 800px; width: 40px; height: 40px; border-radius: 50%; background: radial-gradient(circle at 35% 35%, #fff3c4, #FFC83D 45%, #b8860b); opacity: 0; }}
  </style>
  <div id="root" data-composition-id="g-cash" data-width="1080" data-height="1920">
    <img id="cs-bg" src="assets/footage/ext_blur.jpg" alt="" />
    <div id="cs-dim"></div>
{coins}
    <div id="cs-k" class="ctr kick">Pembeli terawal</div>
    <div id="cs-a" class="ctr hd">CASHBACK</div>
    <div id="cs-n" class="ctr hd y">RM<span id="cs-v">0</span></div>
  </div>
  <script>$JS
    tl.fromTo("#cs-bg", {{ scale: 1.15 }}, {{ scale: 1, duration: $tEnd, ease: "none" }}, 0);
    inUp("#cs-k", 0.05, 0.4);
    slam("#cs-a", $tA);
    inUp("#cs-n", $tC - 0.1, 0.3);
    const c = {{ v: 0 }};
    tl.fromTo(c, {{ v: 0 }}, {{ v: 11000, duration: 1.0, ease: "power3.out",
      onUpdate: () => {{ document.getElementById("cs-v").textContent = (Math.round(c.v / 100) * 100).toLocaleString("en-US"); }} }}, $tC);
    tl.fromTo("#cs-n", {{ scale: 1 }}, {{ scale: 1.1, duration: 0.14, yoyo: true, repeat: 1 }}, $tC + 1.0);
{coin_js}
    tl.to("#root", {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, $tEnd - 0.25);
    window.__timelines["g-cash"] = tl;
  </script>
</template>
""", BASE=BASE_CSS, JS=JS_HELPERS, tA=h(W("cash", "cashback")), tC=h(W("cash", "sebelas")), tEnd=h(s1)))
cue(W("cash", "cashback"), "boom", "CASHBACK slams in")
cue(W("cash", "sebelas") + 1.0, "kaching", "RM11,000 lands")
cue(W("cash", "sebelas") + 1.02, "sparkle", "coin burst")

# ------------------------------------------------------------------ g-cta
s0, s1 = L("cta"), TOTAL
h = lambda x: x - s0
tWA = W("cta", "WhatsApp")
scene("g-cta", s0, s1, tpl("""<template>
  <style>$BASE
    #ct-bg { position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; }
    #ct-dim { position: absolute; inset: 0; background: rgba(5,6,10,0.62); }
    .tag { position: absolute; left: 0; width: 1080px; text-align: center; }
    .tag span { display: inline-block; padding: 16px 40px; border-radius: 999px; white-space: nowrap;
      font-family: "Montserrat", sans-serif; font-weight: 900; font-size: 56px; letter-spacing: 0.02em; }
    #tg1 { top: 300px; } #tg1 span { background: #FFC83D; color: #15120a; }
    #tg2 { top: 420px; } #tg2 span { background: #fff; color: #15120a; }
    #tg3 { top: 540px; } #tg3 span { background: #ff3b3b; color: #fff; }
    #wa { position: absolute; left: 60px; top: 720px; width: 960px; padding: 34px 40px; border-radius: 40px; display: flex; align-items: center; gap: 30px;
      background: rgba(10,12,18,0.9); box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 0 4px #25D366 inset; }
    #wa-i { width: 140px; height: 140px; border-radius: 50%; background: #25D366; color: #fff; display: flex; align-items: center; justify-content: center; flex: none; }
    #wa-i svg { width: 84px; height: 84px; stroke-width: 1.7; }
    #wa-k { font-weight: 800; font-size: 32px; letter-spacing: 0.14em; color: #25D366; }
    #wa-n { font-family: "Montserrat", sans-serif; font-weight: 900; font-size: 100px; line-height: 1.05; letter-spacing: -0.02em; white-space: nowrap; }
    #wa-n span { display: inline-block; }
    #ct-end { top: 560px; font-size: 92px; }
    #ct-sum { top: 1010px; font-size: 40px; font-weight: 700; }
    #ct-sum b { color: #FFC83D; }
  </style>
  <div id="root" data-composition-id="g-cta" data-width="1080" data-height="1920" data-composition-variables='[{"id":"phone","type":"string","label":"Nombor telefon","default":"016-370 8908"}]'>
    <img id="ct-bg" src="assets/footage/ext_blur.jpg" alt="" />
    <div id="ct-dim"></div>
    <div id="tg1" class="tag"><span>FREEHOLD</span></div>
    <div id="tg2" class="tag"><span>RIZAB MELAYU</span></div>
    <div id="tg3" class="tag"><span>UNIT TERHAD</span></div>
    <div id="wa">
      <div id="wa-i">$CHAT</div>
      <div><div id="wa-k">WHATSAPP SEKARANG</div><div id="wa-n"><span id="wa-1">016-</span><span id="wa-2">370&nbsp;</span><span id="wa-3">8908</span></div></div>
    </div>
    <div id="ct-end" class="ctr hd">JOM <span class="y">SITE VISIT</span></div>
    <div id="ct-sum" class="ctr">Teres 1 Tingkat · Pulau Indah · dari <b>RM290,500</b></div>
  </div>
  <script>$JS
    tl.fromTo("#ct-bg", { scale: 1.12 }, { scale: 1, duration: $tEnd, ease: "none" }, 0);
    tl.fromTo("#ct-dim", { opacity: 0.5 }, { opacity: 1, duration: 0.4 }, 0);
    const tag = (s, t) => tl.fromTo(s, { opacity: 0, scale: 0.5, rotation: -6 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.4, ease: "back.out(2.4)" }, t);
    tag("#tg1", $t1); tag("#tg2", $t2); tag("#tg3", $t3);
    tl.to("#tg3", { scale: 1.07, duration: 0.3, yoyo: true, repeat: 5, ease: "sine.inOut" }, $t3 + 0.45);
    tl.fromTo("#wa", { opacity: 0, y: 60, filter: "blur(10px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out" }, $tWA);
    tl.fromTo("#wa-i", { scale: 0.4, rotation: -30 }, { scale: 1, rotation: 0, duration: 0.55, ease: "back.out(2.4)" }, $tWA + 0.05);
    tl.set(["#wa-1", "#wa-2", "#wa-3"], { opacity: 0 }, 0);
    const grp = (s, t) => tl.fromTo(s, { opacity: 0, y: 28, filter: "blur(6px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.26, ease: "expo.out" }, t);
    grp("#wa-1", $tN1); grp("#wa-2", $tN2); grp("#wa-3", $tN3);
    // end card: tags lift, the number card takes the centre and pulses
    tl.to(["#tg1", "#tg2", "#tg3"], { y: -40, opacity: 0.0, duration: 0.4, stagger: 0.05, ease: "power2.in" }, $tE);
    tl.to("#wa", { y: 40, scale: 1.04, duration: 0.6, ease: "power3.inOut" }, $tE + 0.1);
    tl.fromTo("#ct-sum", { opacity: 0, y: 70 }, { opacity: 1, y: 50, duration: 0.5, ease: "expo.out" }, $tE + 0.4);
    tl.fromTo("#ct-end", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }, $tE + 0.25);
    tl.to("#wa", { boxShadow: "0 20px 60px rgba(0,0,0,0.5), 0 0 0 12px #25D366 inset", duration: 0.35, yoyo: true, repeat: 3, ease: "sine.inOut" }, $tE + 0.8);
    window.__timelines["g-cta"] = tl;
  </script>
</template>
""", BASE=BASE_CSS, JS=JS_HELPERS, CHAT=ic("chat"), t1=h(W("cta", "Freehold.")), t2=h(W("cta", "Ri-zab")), t3=h(W("cta", "Unit")),
    tWA=h(tWA), tN1=h(W("cta", "kosong")), tN2=h(W("cta", "tiga")), tN3=h(W("cta", "lapan")), tE=h(speech_end + 0.2), tEnd=h(s1)))
cue(L("cta") - 0.05, "whoosh", "cut to the CTA")
cue(W("cta", "Freehold."), "pop", "tag FREEHOLD")
cue(W("cta", "Ri-zab"), "pop", "tag RIZAB MELAYU")
cue(W("cta", "Unit"), "impact", "tag UNIT TERHAD")
cue(tWA, "whoosh", "WhatsApp card")
cue(W("cta", "kosong"), "tick", "digits 016")
cue(W("cta", "tiga"), "tick", "digits 370")
cue(W("cta", "lapan"), "pop", "digits 8908")
cue(speech_end + 0.3, "ping", "end card")

# =============================================================== CAPTIONS
CAP_LINES = ["ans", "loc1", "loc2", "loc3", "lot", "liv", "mbr", "kit", "rooms", "eta"]
SKIP_UNITS = {("ans", "Wujud.")}
LIMIT = 22
import math
clen = lambda g: sum(len(x["text"]) + 1 for x in g) - 1
groups = []
for lid in CAP_LINES:
    us = [dict(u, id=f"{lid}-{i}") for i, u in enumerate(lines[lid]["units"]) if (lid, u["text"]) not in SKIP_UNITS]
    NOBREAK = {("bilik", "air"), ("bilik", "tidur"), ("satu", "keluarga"), ("halal", "hub"), ("ruang", "tamu"), ("ruang", "makan"), ("pulau", "indah")}
    j = 0
    while j + 1 < len(us):                         # keep word pairs on one caption line
        if (norm(us[j]["text"]), norm(us[j + 1]["text"])) in NOBREAK:
            us[j] = dict(us[j], text=us[j]["text"] + " " + us[j + 1]["text"], e=us[j + 1]["e"]); del us[j + 1]
        j += 1
    phrases, cur = [], []
    for u in us:                                   # 1) split at punctuation
        cur.append(u)
        if re.search(r"[.,?!]$", u["text"]):
            phrases.append(cur); cur = []
    if cur:
        phrases.append(cur)
    merged = []                                    # 2) glue one-word phrases to a neighbour in the same sentence
    for ph in phrases:
        if merged and (len(ph) == 1 or len(merged[-1]) == 1) and clen(merged[-1] + ph) <= LIMIT + 2 and not merged[-1][-1]["text"].endswith((".", "?")):
            merged[-1] = merged[-1] + ph
        else:
            merged.append(ph)
    for ph in merged:                              # 3) balanced chunks of <= LIMIT characters
        k = math.ceil(clen(ph) / LIMIT)
        while True:
            target, chunks, cur = clen(ph) / k, [], []
            for u in ph:
                if cur and clen(cur + [u]) > target + 4 and len(chunks) < k - 1:
                    chunks.append(cur); cur = []
                cur.append(u)
            chunks.append(cur)
            if all(clen(c) <= LIMIT + 2 for c in chunks) or k > 6:
                break
            k += 1
        if len(chunks) > 1 and len(chunks[-1]) == 1 and clen(chunks[-2] + chunks[-1]) <= LIMIT + 3:
            last = chunks.pop(); chunks[-1] = chunks[-1] + last
        groups.extend(chunks)
# merge one-word orphans into the previous group of the same line when they fit
cg = []
for gi, g in enumerate(groups):
    st = g[0]["s"] - 0.05
    en = g[-1]["e"] + 0.15
    if gi + 1 < len(groups):
        en = min(en, groups[gi + 1][0]["s"] - 0.05)
    cg.append([st, max(en, st + 0.4), g])
for i in range(len(cg) - 1):
    cg[i][1] = min(cg[i][1], cg[i + 1][0] - 0.02)
clean = lambda s: re.sub(r"[.,]$", "", s)
c = ["""<template>
  <style>
    #root { position: absolute; inset: 0; }
    .cg { position: absolute; left: 0; top: 1350px; width: 1080px; height: 110px; }
    .cg-in { position: absolute; left: 40px; right: 40px; top: 0; text-align: center; white-space: nowrap;
      font-family: "Montserrat", sans-serif; font-weight: 900; font-size: 60px; line-height: 1.15; letter-spacing: -0.01em; text-transform: uppercase;
      color: #ffffff; -webkit-text-stroke: 14px rgba(0,0,0,0.92); paint-order: stroke fill; text-shadow: 0 6px 18px rgba(0,0,0,0.45); }
    .cw { display: inline-block; transform-origin: 50% 80%; margin: 0 0.09em; }
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">"""]
for gi, (st, en, g) in enumerate(cg):
    spans = " ".join(f'<span id="cw-{x["id"]}" class="cw">{html.escape(clean(x["text"]))}</span>' for x in g)
    c.append(f'    <div id="cg-{gi}" class="clip cg" data-start="{r3(st)}" data-duration="{r3(en - st)}" data-track-index="0"><div id="cgi-{gi}" class="cg-in">{spans}</div></div>')
c.append("""  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    const Y = "#FFC83D";""")
for gi, (st, en, g) in enumerate(cg):
    c.append(f'    tl.fromTo("#cgi-{gi}", {{ opacity: 0, y: 16, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.14, ease: "back.out(2)" }}, {r3(st)});')
    for k, x in enumerate(g):
        on = max(x["s"], st)
        c.append(f'    tl.fromTo("#cw-{x["id"]}", {{ color: "#ffffff", scale: 1 }}, {{ color: Y, scale: 1.04, duration: 0.08, ease: "power2.out" }}, {r3(on)});')
        if k + 1 < len(g):
            off = max(g[k + 1]["s"], on + 0.12)
            c.append(f'    tl.to("#cw-{x["id"]}", {{ color: "#ffffff", scale: 1, duration: 0.08, ease: "power2.in" }}, {r3(off)});')
    c.append(f'    tl.to("#cgi-{gi}", {{ opacity: 0, duration: 0.08, ease: "power2.in" }}, {r3(en - 0.08)});')
    c.append(f'    tl.set("#cgi-{gi}", {{ visibility: "hidden" }}, {r3(en)});')
c.append("""    window.__timelines["captions"] = tl;
  </script>
</template>
""")
open(os.path.join(COMP, "captions.html"), "w").write("\n".join(c))

# =============================================================== INDEX
o = []
w = o.append
w(f"""<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Teres Setingkat Pulau Indah</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #0b0d12; }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; }}
      #cam {{ position: absolute; inset: 0; overflow: hidden; z-index: 1; }}
      #cam-inner {{ position: absolute; inset: 0; transform-origin: 50% 45%; }}
      #cam-inner video, #cam-inner img {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
      #grade {{ position: absolute; inset: 0; z-index: 2; pointer-events: none;
        background: radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.38) 100%); }}
      #flash {{ position: absolute; inset: 0; background: #fff; opacity: 0; z-index: 3; }}
      .scene {{ position: absolute; inset: 0; pointer-events: none; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{r3(TOTAL)}" data-width="1080" data-height="1920">
      <!-- PICTURE: trims of IMG_1360.MOV (muted: the voice is the ElevenLabs VO) -->
      <div id="cam">
        <div id="cam-inner" data-layout-allow-overflow>""")
for i, s in enumerate(shots):
    sid = f"v{i:02d}"
    s["el"] = sid
    if s["src"] == "map":
        continue
    if s["src"] in ("freeze", "still"):
        img = "freeze.jpg" if s["src"] == "freeze" else "ext_blur.jpg"
        w(f'          <img id="{sid}" class="clip" src="assets/footage/{img}" alt="" data-start="{r3(s["start"])}" data-duration="{r3(s["dur"])}" data-track-index="1" /><!-- {s["why"]} -->')
    else:
        w(f'          <video id="{sid}" class="clip" src="{FOOTAGE}" muted playsinline data-start="{r3(s["start"])}" data-duration="{r3(s["dur"])}" data-media-start="{r3(s["src"])}" data-track-index="1"></video><!-- {s["why"]} -->')
w(f'          <img id="v-end" class="clip" src="assets/footage/ext_blur.jpg" alt="" data-start="{r3(L("cta"))}" data-duration="{r3(TOTAL - L("cta"))}" data-track-index="1" />')
w("""        </div>
      </div>
      <div id="grade"></div>
      <div id="flash"></div>

      <!-- VOICE: ElevenLabs "Mad Serious" (eleven_v3), enhanced by enhance_vo.py, one clip per line -->""")
for lid in ORDER:
    ln = lines[lid]
    w(f'      <audio id="vo-{lid}" class="clip" src="assets/audio/vo/{lid}.wav" data-start="{r3(ln["start"])}" data-duration="{r3(ln["dur"])}" data-volume="1" data-track-index="2"></audio>')
# music: starts on "Wujud." so its own ending lands on the end card
MUSIC_AT = W("ans", "Wujud.") - 0.05
MUSIC_LEN = 75.5  # music-bed.mp3 after extend_music.py (two bars repeated); the track ends on its own at ~75.5 s
mdur = min(TOTAL - MUSIC_AT, MUSIC_LEN)
BED, LIFT = 0.16, 0.34
pts = [(0.0, 0.0), (0.25, BED)]
for a0, a1 in [(L("loc3") + 3.8, L("lot")), (speech_end, TOTAL)]:
    a0, a1 = a0 - MUSIC_AT, a1 - MUSIC_AT
    pts += [(a0, BED), (a0 + 0.25, LIFT)]
    if a1 < mdur - 0.1:
        pts += [(a1 - 0.15, LIFT), (a1 + 0.1, BED)]
lane = ",".join(f'{{&quot;t&quot;:{r3(max(0, t_))},&quot;v&quot;:{v}}}' for t_, v in pts)
w(f'\n      <!-- MUSIC: ElevenLabs Music, generated for this edit; ducked under the voice -->')
w(f'      <audio id="music" class="clip" src="assets/audio/music-bed.mp3" data-start="{r3(MUSIC_AT)}" data-duration="{r3(mdur)}" data-media-start="0" data-volume="1" data-fade-out="1.2" data-automation="{{&quot;version&quot;:1,&quot;lanes&quot;:[{{&quot;target&quot;:&quot;volume&quot;,&quot;points&quot;:[{lane}]}}]}}" data-track-index="5"></audio>')
w("\n      <!-- SOUND EFFECTS: each one lands one frame after its picture event -->")
cues.sort()
lane_end = {}
SFX_LANES = [3, 4, 10, 11, 12]
for i, (tev, kind, why) in enumerate(cues):
    f, peak, vol, ln_ = SFX[kind]
    st = max(0.0, tev + 1 / FPS - peak)
    dur = min(ln_, TOTAL - st)
    sfx_lane = next(k for k in SFX_LANES if lane_end.get(k, -1) <= st)
    lane_end[sfx_lane] = st + dur
    w(f'      <audio id="sfx-{i + 1:02d}" class="clip" src="{f}" data-start="{r3(st)}" data-duration="{r3(dur)}" data-volume="{vol}" data-track-index="{sfx_lane}"></audio><!-- {html.escape(why)} -->')
w("\n      <!-- MOTION GRAPHICS -->")
for i, (sid, a, b) in enumerate(SCENES):
    w(f'      <div id="{sid}" class="scene" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{r3(a)}" data-duration="{r3(b - a)}" data-track-index="{6 + i % 2}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index: 10"></div>')
cap_end = max(en for _, en, _ in cg)
w(f'      <div id="captions" class="scene" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{r3(cap_end + 0.05)}" data-track-index="9" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index: 20"></div>')
w("    </div>\n    <script>\n      window.__timelines = window.__timelines || {};\n      const tl = gsap.timeline({ paused: true });")
w("      // slow push-in on every shot; the hook gets a stronger one")
for s in shots:
    if s["src"] == "map":
        continue
    z = 1.14 if s["lid"] in ("hook1", "hook2") else 1.07
    w(f'      tl.fromTo("#cam-inner", {{ scale: 1 }}, {{ scale: {z}, duration: {r3(s["dur"] - 0.002)}, ease: "none", immediateRender: false }}, {r3(s["start"])});')
w(f'      tl.set("#cam-inner", {{ scale: 1 }}, {r3(L("cta"))});')
for tt in [L("ans"), L("lot"), L("price"), L("cta")]:
    w(f'      tl.to("#flash", {{ opacity: 0.7, duration: 0.06, ease: "power2.in" }}, {r3(tt - 0.06)});')
    w(f'      tl.to("#flash", {{ opacity: 0, duration: 0.25, ease: "power2.out" }}, {r3(tt)});')
w(f'      tl.set({{}}, {{}}, {r3(TOTAL)});\n      window.__timelines["main"] = tl;\n    </script>\n  </body>\n</html>\n')
open(os.path.join(VID, "index.html"), "w").write("\n".join(o))

# =============================================================== REPORT
json.dump({lid: {"start": round(v["start"], 3), "end": round(v["end"], 3),
                 "words": [{"t": w_["sp"], "s": round(w_["s"], 3), "e": round(w_["e"], 3)} for w_ in v["words"]]}
           for lid, v in lines.items()}, open(os.path.join(VID, "vo_timing.json"), "w"), ensure_ascii=False, indent=0)
print(f"total {TOTAL}s, speech ends {speech_end:.2f}s, music {MUSIC_AT:.2f}->{MUSIC_AT + mdur:.2f}, {len(shots)} shots, {len(cues)} sfx, {len(cg)} caption groups")
for sid, a, b in SCENES:
    print(f"  {sid:8s} {a:6.2f} -> {b:6.2f}")
for s in shots:
    print(f"  shot {s['lid']:6s} {s['start']:6.2f}+{s['dur']:5.2f}  src {s['src']}")
