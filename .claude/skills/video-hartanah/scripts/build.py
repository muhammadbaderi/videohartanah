"""Build a property-video HyperFrames project from <project>/project.json and the VO timing.

Reads   <project>/project.json
        <project>/video/assets/audio/vo/<line>.wav + <line>.words.json   (enhance_vo.py, align_vo.py)
        <project>/video/assets/map/map.json                              (make_map.py, if there is a map scene)
Writes  <project>/video/index.html, <project>/video/compositions/*.html, <project>/video/vo_timing.json
        (re-running OVERWRITES them; edit project.json, not the HTML)

Anchors (any "at"/"start"/"switch" value) point at the voice:
  "lot"               start of line "lot"
  "lot:Porch,"        start of the first word "Porch," in line "lot" (case/punctuation-insensitive)
  "pkg:legal#1"       the second "legal" in line "pkg"
  "hook1:Pulau@-0.1"  ...minus 0.1 s (any anchor can take @offset)

Usage: python3 -I .claude/skills/video-hartanah/scripts/build.py <project-dir>
"""
import html, json, math, os, re, subprocess, sys
from string import Template

PROJ = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
VID = os.path.join(PROJ, "video")
COMP = os.path.join(VID, "compositions")
os.makedirs(COMP, exist_ok=True)
P = json.load(open(os.path.join(PROJ, "project.json")))
SC = P.get("scenes", {})
FPS = 30
r3 = lambda x: f"{x:.3f}".rstrip("0").rstrip(".") if abs(x) > 1e-9 else "0"
esc = html.escape
FOOTAGE = P["footage"]
ACCENT = P.get("accent", "#FFC83D")

# =============================================================== VOICE + WORDS
TOKEN = re.compile(r"\{([^|}]*)\|([^}]*)\}|\[[^\]]*\]|(\S+)")

def parse(text):
    """-> words [{sp, grp}] and display units [{text}] of a script line"""
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

END_HOLD = P.get("timeline", {}).get("end_hold", 3.2)
lines, t = {}, 0.0
for ln in P["lines"]:
    lid = ln["id"]
    aw = json.load(open(os.path.join(VID, "assets", "audio", "vo", f"{lid}.words.json")))
    words, units = parse(ln["text"])
    assert [w["sp"] for w in words] == [w["sp"] for w in aw], (lid, [w["sp"] for w in words], [w["sp"] for w in aw])
    t += ln.get("gap", 0.3)
    for w, a in zip(words, aw):
        w["s"], w["e"] = t + a["s"], t + a["e"]
    for gi, u in enumerate(units):
        ws = [w for w in words if w["grp"] == gi]
        u["s"], u["e"] = ws[0]["s"], ws[-1]["e"]
    wav = os.path.join(VID, "assets", "audio", "vo", f"{lid}.wav")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                               capture_output=True, text=True).stdout)
    lines[lid] = {"start": t, "dur": dur, "end": t + aw[-1]["e"], "words": words, "units": units}
    t += max(aw[-1]["e"], dur - 0.12)   # the WAV keeps ~0.13 s of tail after the last voiced frame
speech_end = t
TOTAL = round(speech_end + END_HOLD, 3)
ORDER = [l["id"] for l in P["lines"]]
L = lambda lid: lines[lid]["start"]
norm = lambda s: re.sub(r"[^\w-]", "", s).lower()

def A(anchor):
    """anchor string -> seconds on the edit timeline"""
    m = re.fullmatch(r"([^:@]+)(?::(.+?))?(?:#(\d+))?(?:@([+-]?\d*\.?\d+))?", anchor)
    if not m:
        raise ValueError(f"bad anchor {anchor!r}")
    lid, word, n, off = m.group(1), m.group(2), int(m.group(3) or 0), float(m.group(4) or 0)
    if lid not in lines:
        raise KeyError(f"anchor {anchor!r}: no line {lid!r}")
    if word is None:
        return L(lid) + off
    hits = [w for w in lines[lid]["words"] if norm(w["sp"]) == norm(word)]
    if len(hits) <= n:
        raise KeyError(f"anchor {anchor!r}: word not found; line {lid} has {[w['sp'] for w in lines[lid]['words']]}")
    return hits[n]["s"] + off

# =============================================================== SCENE WINDOWS
KINDS = ["hook", "answer", "map", "plan", "status", "price", "package", "cashback", "cta"]
present = [k for k in KINDS if k in SC]
starts = {k: (0.0 if k == "hook" else A(SC[k]["start"])) for k in present}
ends = {}
for i, k in enumerate(present):
    ends[k] = starts[present[i + 1]] if i + 1 < len(present) else TOTAL
CTA_AT = starts.get("cta", TOTAL)

# =============================================================== PICTURE
shots = []
for i, sh in enumerate(P["shots"]):
    st = 0.0 if i == 0 else (A(sh["switch"]) - 0.12 if sh.get("switch") else L(sh["line"]))
    shots.append({"lid": sh["line"], "src": sh["src"], "start": st, "max": sh.get("max"), "why": sh.get("why", "")})
for i, s in enumerate(shots):
    s["end"] = shots[i + 1]["start"] if i + 1 < len(shots) else CTA_AT
    s["dur"] = s["end"] - s["start"]
    if isinstance(s["src"], (int, float)):
        s["src"] = float(s["src"])
        assert s["max"] is None or s["src"] + s["dur"] <= s["max"] + 1e-6, \
            f"shot {i} ({s['why']}) needs {s['dur']:.2f}s from {s['src']} but the usable take ends at {s['max']}: start it earlier, add a switch, or split it"

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
    if kind:
        cues.append((t_ev, kind, why))

# =============================================================== SHARED SCENE PARTS
SCENES = []
def scene(sid, start, end, body):
    SCENES.append((sid, start, end))
    open(os.path.join(COMP, f"{sid}.html"), "w").write(body)

BASE_CSS = """
    #root { position: absolute; inset: 0; color: #fff; font-family: "Inter", sans-serif; overflow: hidden; }
    .hd { font-family: "Montserrat", sans-serif; font-weight: 900; letter-spacing: -0.02em; line-height: 0.95; }
    .y { color: @ACC; }
    .glass { background: rgba(10, 12, 18, 0.82); backdrop-filter: blur(18px); box-shadow: 0 18px 50px rgba(0,0,0,0.45); }
    .kick { font-weight: 800; letter-spacing: 0.16em; font-size: 30px; color: @ACC; text-transform: uppercase; }
    .ctr { position: absolute; left: 0; width: 1080px; text-align: center; }
    svg.ic { fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
""".replace("@ACC", ACCENT)
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
    "mall": '<path d="M4 8h16l-1.2 12H5.2z"/><path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8"/>',
    "train": '<rect x="5" y="3.5" width="14" height="13" rx="3"/><path d="M5 11h14M8.5 20l1.5-3.5M15.5 20L14 16.5"/><circle cx="9" cy="14" r="0.8"/><circle cx="15" cy="14" r="0.8"/>',
    "park": '<path d="M12 3l5 7h-3l4 6H6l4-6H7z"/><path d="M12 16v5"/>',
    "hospital": '<path d="M4 21V5h16v16"/><path d="M12 8v6M9 11h6"/><path d="M10 21v-3h4v3"/>',
    "ship": '<path d="M3 15l2 5h14l2-5z"/><path d="M6 15V9h12v6"/><path d="M12 9V4"/>',
    "road": '<path d="M8 3L4 21M16 3l4 18M12 4v3M12 10v4M12 17v3"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.6"/>',
    "shield": '<path d="M12 3l8 3v6c0 4.6-3.4 8-8 9-4.6-1-8-4.4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    "star": '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
    "car": '<path d="M5 16V12l2-5h10l2 5v4"/><path d="M3.5 12h17v4.5h-17z"/><circle cx="7.5" cy="17.5" r="1.6"/><circle cx="16.5" cy="17.5" r="1.6"/>',
    "chat": '<path d="M4 19.5l1.3-3.9A8 8 0 1 1 8.4 18.7z"/><path d="M9.2 8.6c.3 2.8 2.4 5 5.2 5.6l1.3-1.3 2 1-.5 1.6c-4.4.4-8.6-3.6-8.6-8l1.6-.5 1 2z"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
}
ic = lambda k, cls="ic": f'<svg class="{cls}" viewBox="0 0 24 24">{ICONS.get(k, ICONS["star"])}</svg>'
fmt_money = lambda v: f"{v:,.0f}"

def tpl(s, **kw):
    return Template(s).substitute({k: (r3(v) if isinstance(v, float) else v) for k, v in kw.items()})

def page(sid, css, body, js):
    return tpl("""<template>
  <style>$BASE$CSS
  </style>
  <div id="root" data-composition-id="$SID" data-width="1080" data-height="1920">
$BODY
  </div>
  <script>$JS$SCRIPT
    window.__timelines["$SID"] = tl;
  </script>
</template>
""", BASE=BASE_CSS, CSS=css, SID=sid, BODY=body, JS=JS_HELPERS, SCRIPT=js)

# ------------------------------------------------------------------ hook: kinetic phrases + question
if "hook" in SC:
    c = SC["hook"]; s0, s1 = starts["hook"], ends["hook"]; h = lambda x: r3(x - s0)
    phrases, q = c.get("phrases", []), c.get("question")
    body, js = [], []
    body.append('    <div id="hk-shade"></div>\n    <div id="hk-dark"></div>')
    if c.get("tag"):
        body.append(f'    <div id="hk-tag"><span>{esc(c["tag"])}</span></div>')
        js.append('    inPop("#hk-tag", 0.05);')
    q_at = A(q["at"]) if q else s1
    for i, ph in enumerate(phrases):
        t_in = A(ph["at"])
        t_out = (A(phrases[i + 1]["at"]) - 0.22) if i + 1 < len(phrases) else q_at - 0.25
        rows = []
        if ph.get("icon"):
            rows.append(f'<div class="hk-ic">{ic(ph["icon"])}</div>')
        for j, li in enumerate(ph["lines"]):
            cls = "hd" + (" y" if li.get("accent") else "")
            style = f'font-size: {li.get("size", 68)}px;' + (" margin-top: 6px;" if j else "") + \
                    (" text-shadow: 0 0 60px rgba(255,200,61,0.35);" if li.get("glow") else "")
            rows.append(f'<div id="hk-{i}-{j}" class="{cls}" style="{style}">{esc(li["text"])}</div>')
        body.append(f'    <div id="hk-{i}" class="ph sh">{"".join(rows)}</div>')
        js.append(f'    inUp("#hk-{i}", {h(t_in)}, {r3(ph.get("dur", 0.4))});')
        if ph.get("icon"):
            js.append(f'    tl.fromTo("#hk-{i} .hk-ic", {{ y: -140, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "bounce.out" }}, {h(t_in)});')
        cue(t_in, ph.get("sfx"), f"hook phrase {i}")
        for j, li in enumerate(ph["lines"]):
            if li.get("slam"):
                ts = A(li["slam"])
                js.append(f'    slam("#hk-{i}-{j}", {h(ts)});')
                if li.get("shake"):
                    js.append(f'    tl.fromTo("#hk-{i}-{j}", {{ x: -14 }}, {{ x: 0, duration: 0.4, ease: "elastic.out(1.2, 0.25)" }}, {h(ts + 0.3)});')
                cue(ts, li.get("sfx"), f"hook: {li['text']} slams in")
        js.append(f'    out("#hk-{i}", {h(t_out)});')
    if c.get("tag"):
        js.append(f'    out("#hk-tag", {h(q_at - 0.25)});')
    if q:
        js.append(f'    tl.to("#hk-dark", {{ opacity: 1, duration: 0.25, ease: "power2.out" }}, {h(q_at - 0.05)});')
        rows = []
        for j, wd in enumerate(q["words"]):
            qm = '<span class="hk-q">?</span>' if wd.get("q") else ""
            rows.append(f'<div class="hd" style="font-size: {wd.get("size", 120)}px"><span id="hk-q{j}">{esc(wd["text"])}</span>{qm}</div>')
            tw = A(wd["at"])
            js.append(f'    slam("#hk-q{j}", {h(tw)});')
            cue(tw, wd.get("sfx"), f"question word {wd['text']}")
            if wd.get("q"):
                js.append(f'    tl.fromTo(".hk-q", {{ opacity: 0, rotation: -25, scale: 0.4 }}, {{ opacity: 1, rotation: 0, scale: 1, duration: 0.5, ease: "back.out(3)" }}, {h(tw + 0.12)});')
                js.append(f'    tl.to(".hk-q", {{ rotation: 12, duration: 0.18, ease: "sine.inOut", yoyo: true, repeat: 3 }}, {h(tw + 0.65)});')
        body.append(f'    <div id="hk-qq" class="ph sh" style="top: 620px">{"".join(rows)}</div>')
        js.append(f'    tl.to("#hk-qq", {{ scale: 1.12, opacity: 0, filter: "blur(16px)", duration: 0.25, ease: "power2.in" }}, {h(s1 - 0.25)});')
        if "answer" in SC:
            cue(s1 - 0.02, "riser", "riser into the answer (peaks on the cut)")
    css = f"""
    #hk-shade {{ position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.15) 40%, rgba(0,0,0,0.15) 60%, rgba(0,0,0,0.6) 100%); }}
    #hk-dark {{ position: absolute; inset: 0; background: rgba(5,6,10,0.62); opacity: 0; }}
    #hk-tag {{ position: absolute; top: 250px; left: 0; width: 1080px; text-align: center; }}
    #hk-tag span {{ display: inline-block; padding: 14px 30px; border-radius: 999px; white-space: nowrap;
      font-weight: 800; font-size: 30px; letter-spacing: 0.14em; color: #15120a; background: {ACCENT}; }}
    .ph {{ position: absolute; left: 0; width: 1080px; text-align: center; top: 640px; }}
    .hk-ic svg {{ width: 84px; height: 84px; color: {ACCENT}; stroke-width: 1.8; }}
    .sh {{ text-shadow: 0 8px 30px rgba(0,0,0,0.55); }}
    .hk-q {{ display: inline-block; color: {ACCENT}; transform-origin: 50% 85%; }}"""
    scene("g-hook", s0, s1, page("g-hook", css, "\n".join(body), "\n" + "\n".join(js)))

# ------------------------------------------------------------------ answer: stamp + site-visit badge
if "answer" in SC:
    c = SC["answer"]; s0, s1 = starts["answer"], ends["answer"]; h = lambda x: r3(x - s0)
    body, js = [], []
    if c.get("stamp"):
        st = c["stamp"]; tw = A(st["at"])
        body.append(f'    <div id="an-st"><span class="hd">{esc(st["text"])}</span></div>')
        js += [f'    tl.fromTo("#an-st", {{ opacity: 0, scale: 2.4 }}, {{ opacity: 1, scale: 1, duration: 0.22, ease: "power4.in" }}, {h(tw - 0.12)});',
               f'    tl.fromTo("#an-st", {{ y: 0 }}, {{ y: 8, duration: 0.06, yoyo: true, repeat: 3, ease: "none" }}, {h(tw + 0.1)});']
        to = A(st["out"]) if st.get("out") else s1 - 0.3
        js += [f'    tl.to("#an-st", {{ opacity: 0, scale: 0.85, filter: "blur(10px)", duration: 0.25, ease: "power2.in" }}, {h(to)});',
               f'    tl.set("#an-st", {{ visibility: "hidden" }}, {h(to + 0.26)});']
        cue(tw + 0.1, "stamp", f"{st['text']} stamp lands")
    if c.get("badge"):
        b = c["badge"]; tb = A(b["at"])
        body.append(f'    <div id="an-live" class="glass"><div id="an-dot"></div>{esc(b["text"])}</div>')
        js += [f'    inUp("#an-live", {h(tb)}, 0.4);',
               f'    tl.to("#an-dot", {{ opacity: 0.25, duration: 0.4, yoyo: true, repeat: 5, ease: "sine.inOut" }}, {h(tb + 0.4)});',
               f'    out("#an-live", {h(s1 - 0.25)});']
    css = f"""
    #an-st {{ position: absolute; left: 0; width: 1080px; top: 640px; text-align: center; }}
    #an-st span {{ display: inline-block; transform: rotate(-6deg); padding: 8px 34px 14px; border: 9px solid {ACCENT};
      border-radius: 22px; color: {ACCENT}; font-size: 124px; background: rgba(10,12,18,0.35); text-shadow: 0 6px 30px rgba(0,0,0,0.4); white-space: nowrap; }}
    #an-live {{ position: absolute; left: 60px; top: 230px; display: flex; align-items: center; gap: 16px; padding: 14px 28px 14px 22px; border-radius: 999px;
      font-weight: 800; font-size: 30px; letter-spacing: 0.14em; }}
    #an-dot {{ width: 22px; height: 22px; border-radius: 50%; background: #ff3b3b; box-shadow: 0 0 18px #ff3b3b; }}"""
    scene("g-ans", s0, s1, page("g-ans", css, "\n".join(body), "\n" + "\n".join(js)))

# ------------------------------------------------------------------ map: satellite zoom-in, pin, amenities, zoom-out, roads
if "map" in SC:
    c = SC["map"]; s0, s1 = starts["map"], ends["map"]; h = lambda x: r3(x - s0)
    MAP = json.load(open(os.path.join(VID, "assets", "map", "map.json")))
    PIN_Y = 800
    lp, rp = MAP["local"]["pin"], MAP["region"]["pin"]
    body, js = [], []
    body.append('    <div id="mp-bg"></div>')
    body.append('    <div id="mp-r" class="mw"><img id="mp-ri" src="assets/map/map-region.jpg" alt="" /></div>')
    body.append('    <div id="mp-l" class="mw"><img id="mp-li" src="assets/map/map-local.jpg" alt="" /></div>')
    body.append('    <div id="mp-tint"></div>')
    for i, mk in enumerate(MAP["region"].get("marks", [])):
        x, y = mk["css"]
        shift = "-85%" if x > 860 else "-15%" if x < 220 else "-50%"
        body.append(f'    <div id="mp-m{i}" class="mk" style="left: {x}px; top: {r3(y + PIN_Y - rp[1])}px; transform: translate({shift}, -50%)"><i></i><span>{esc(mk["name"].upper())}</span></div>')
    pin = c.get("pin", {})
    body.append('    <div class="ring" id="mp-ring1"></div><div class="ring" id="mp-ring2"></div>')
    body.append('    <div id="mp-pin"><div class="body"><svg viewBox="0 0 24 24"><path d="M12 22s-7.5-6.6-7.5-12.3a7.5 7.5 0 0 1 15 0C19.5 15.4 12 22 12 22z"/><circle cx="12" cy="9.7" r="2.8" fill="#15120a"/></svg></div></div>')
    if pin.get("label"):
        body.append(f'    <div id="mp-lab"><span>{esc(pin["label"])}</span></div>')
    ti = c.get("title")
    if ti:
        body.append(f'    <div id="mp-title" class="glass"><div class="kick">{esc(ti.get("kicker", "Lokasi"))}</div><div class="hd t1">{esc(ti["text"])}</div><div class="t2">{esc(ti.get("sub", ""))}</div></div>')
    am = c.get("amenities", [])
    body.append('    <div id="mp-am" class="grid">' + "".join(f'<div id="mp-a{i}" class="chip glass">{ic(a.get("icon", "star"))}<span>{esc(a["text"])}</span></div>' for i, a in enumerate(am)) + '</div>')
    rd = c.get("roads", [])
    body.append('    <div id="mp-rd" class="flow">' + "".join(f'<div id="mp-r{i}" class="chip glass{" big" if r_.get("big") else ""}">{ic("road")}<span>{esc(r_["text"])}</span></div>' for i, r_ in enumerate(rd)) + '</div>')
    body.append(f'    <div id="mp-cr" data-layout-ignore>{esc(c.get("credit", "Imej satelit: Esri, Maxar, Earthstar Geographics"))}</div>')
    js.append('    tl.fromTo("#mp-l", { scale: 1.7, filter: "blur(6px)" }, { scale: 1, filter: "blur(0px)", duration: 1.5, ease: "expo.out" }, 0);')
    if ti:
        js.append(f'    inUp("#mp-title", {h(A(ti["at"]))}, 0.5);')
    tP = A(pin["at"]) if pin.get("at") else s0 + 0.6
    js.append(f'    tl.fromTo("#mp-pin", {{ y: -260, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "bounce.out" }}, {h(tP)});')
    if pin.get("label"):
        js.append(f'    inPop("#mp-lab", {h(tP + 0.35)});')
    nring = max(1, int((s1 - tP) / 1.6) + 1)
    js.append(f'    const ring = (s, t0) => {{ tl.set(s, {{ opacity: 0, scale: 0.3 }}, 0); for (let k = 0; k < {nring}; k++) tl.fromTo(s, {{ scale: 0.3, opacity: 0.9 }}, {{ scale: 4.2, opacity: 0, duration: 1.6, ease: "power1.out" }}, t0 + k * 1.6); }};')
    js.append(f'    ring("#mp-ring1", {h(tP + 0.5)}); ring("#mp-ring2", {h(tP + 1.3)});')
    cue(s0 - 0.05, "whoosh", "cut into the map (zoom)")
    cue(tP + 0.45, "pin", "pin lands")
    for i, a in enumerate(am):
        js.append(f'    inPop("#mp-a{i}", {h(A(a["at"]))});')
        cue(A(a["at"]), "pop" if i % 2 == 0 else "tick", f"amenity chip {i}")
    if c.get("zoom_out"):
        tZ = A(c["zoom_out"])
        if am:
            js.append(f'    out([{", ".join(chr(34) + "#mp-a" + str(i) + chr(34) for i in range(len(am)))}], {h(tZ - 0.3)}, 0.2);')
        if pin.get("label"):
            js.append(f'    out("#mp-lab", {h(tZ - 0.3)}, 0.2);')
        if ti:
            js.append(f'    out("#mp-title", {h(tZ - 0.3)}, 0.25);')
        js += [f'    tl.to("#mp-l", {{ scale: 0.125, opacity: 0, duration: 1.2, ease: "power3.inOut" }}, {h(tZ - 0.1)});',
               f'    tl.fromTo("#mp-r", {{ scale: 8 }}, {{ scale: 1, duration: 1.2, ease: "power3.inOut" }}, {h(tZ - 0.1)});',
               f'    tl.to("#mp-pin", {{ scale: 0.75, duration: 1.2, ease: "power3.inOut" }}, {h(tZ - 0.1)});',
               f'    tl.fromTo([".mk"], {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, stagger: 0.15, ease: "power2.out" }}, {h(tZ + 0.9)});']
        cue(tZ - 0.1, "whoosh", "zoom out to the region")
    else:
        js.append('    tl.set([".mk"], { opacity: 0 }, 0);')
    for i, r_ in enumerate(rd):
        js.append(f'    inPop("#mp-r{i}", {h(A(r_["at"]))});')
        cue(A(r_["at"]), "pop" if r_.get("big") else "tick", f"road chip {i}")
    js.append(f'    tl.to("#root", {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, {h(s1 - 0.25)});')
    css = f"""
    #mp-bg {{ position: absolute; inset: 0; background: #0b0f14; }}
    .mw {{ position: absolute; inset: 0; transform-origin: 540px {PIN_Y}px; }}
    .mw img {{ position: absolute; left: 0; width: 1080px; }}
    #mp-li {{ top: {r3(PIN_Y - lp[1])}px; height: {MAP["local"]["h"]}px; }} #mp-ri {{ top: {r3(PIN_Y - rp[1])}px; height: {MAP["region"]["h"]}px; }}
    #mp-tint {{ position: absolute; inset: 0; background: linear-gradient(180deg, rgba(5,7,10,0.75) 0%, rgba(5,7,10,0.1) 26%, rgba(5,7,10,0.05) 45%, rgba(5,7,10,0.7) 62%, rgba(5,7,10,0.88) 100%); }}
    #mp-pin {{ position: absolute; left: 488px; top: {PIN_Y - 98}px; width: 104px; height: 104px; color: #15120a; }}
    #mp-pin .body {{ position: absolute; inset: 0; }}
    #mp-pin svg {{ width: 104px; height: 104px; fill: {ACCENT}; stroke: #15120a; stroke-width: 1.2; filter: drop-shadow(0 8px 14px rgba(0,0,0,0.6)); }}
    .ring {{ position: absolute; left: 540px; top: {PIN_Y}px; width: 60px; height: 60px; margin: -30px 0 0 -30px; border-radius: 50%; border: 5px solid {ACCENT}; opacity: 0; }}
    #mp-lab {{ position: absolute; left: 0; width: 1080px; top: {PIN_Y + 30}px; text-align: center; }}
    #mp-lab span {{ display: inline-block; padding: 12px 26px; border-radius: 16px; white-space: nowrap;
      font-weight: 800; font-size: 30px; letter-spacing: 0.08em; background: {ACCENT}; color: #15120a; }}
    #mp-title {{ position: absolute; left: 60px; right: 60px; top: 220px; padding: 30px 36px; border-radius: 30px; }}
    #mp-title .t1 {{ font-size: 66px; margin-top: 10px; }} #mp-title .t2 {{ font-size: 34px; font-weight: 600; opacity: 0.85; margin-top: 10px; }}
    .grid {{ position: absolute; left: 60px; top: 1010px; width: 960px; display: grid; grid-template-columns: 470px 470px; gap: 16px 20px; }}
    .flow {{ position: absolute; left: 60px; top: 1010px; width: 960px; display: flex; flex-wrap: wrap; gap: 20px; }}
    .chip {{ height: 84px; border-radius: 22px; display: flex; align-items: center; gap: 16px; padding: 0 22px;
      font-weight: 700; font-size: 29px; white-space: nowrap; overflow: hidden; }}
    .chip svg {{ width: 46px; height: 46px; flex: none; color: {ACCENT}; }}
    .chip.big {{ font-family: "Montserrat", sans-serif; font-weight: 900; font-size: 44px; height: 100px; padding: 0 34px 0 26px; }}
    .mk {{ position: absolute; display: flex; flex-direction: column; align-items: center; gap: 8px; }}
    .mk i {{ width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 5px rgba(255,255,255,0.25); }}
    .mk span {{ font-weight: 800; font-size: 28px; letter-spacing: 0.1em; text-shadow: 0 2px 10px #000, 0 0 3px #000; white-space: nowrap; }}
    #mp-cr {{ position: absolute; left: 24px; bottom: 26px; font-size: 18px; opacity: 0.6; }}"""
    scene("g-map", s0, s1, page("g-map", css, "\n".join(body), "\n" + "\n".join(js)))

# ------------------------------------------------------------------ plan: floor plan + lot cards, then the room-by-room tour
if "plan" in SC:
    c = SC["plan"]; s0, s1 = starts["plan"], ends["plan"]; h = lambda x: r3(x - s0)
    R, LBL = c["rooms"], c.get("labels", {})
    Wmm, Dmm = c["width_mm"], c["depth_mm"]
    pad = 300
    SVG_W = 300
    SVG_H = round(SVG_W * (Dmm + 2 * pad) / (Wmm + 2 * pad))
    outdoor, small = set(c.get("outdoor", [])), set(c.get("small_labels", []))
    svg = [f'<svg id="pl-svg" data-layout-ignore viewBox="-{pad} -{pad} {Wmm + 2 * pad} {Dmm + 2 * pad}" width="{SVG_W}" height="{SVG_H}">']
    for k, (x, y, w, hh) in R.items():
        fill = "rgba(255,255,255,0.02)" if k in outdoor else "rgba(255,255,255,0.04)"
        svg.append(f'<rect class="rm" x="{x}" y="{y}" width="{w}" height="{hh}" fill="{fill}" stroke="rgba(255,255,255,0.9)" stroke-width="60"/>')
        svg.append(f'<rect id="hl-{k}" x="{x + 30}" y="{y + 30}" width="{w - 60}" height="{hh - 60}" fill="{ACCENT}" opacity="0"/>')
    unit = Wmm / 6096  # label sizes were tuned on a 20 ft (6096 mm) frontage
    for k, txt in LBL.items():
        x, y, w, hh = R[k]
        parts = txt.split("\n")
        fs = (300 if k in small else 420 if len(max(parts, key=len)) <= 7 else 360) * unit
        for j, p_ in enumerate(parts):
            yy = y + hh / 2 + (j - (len(parts) - 1) / 2) * fs * 1.1 + fs * 0.35
            svg.append(f'<text class="lb" x="{x + w / 2:g}" y="{yy:.0f}" font-size="{fs:g}" text-anchor="middle">{esc(p_)}</text>')
    for k, n in c.get("numbered", []):
        x, y, w, hh = R[k]
        svg.append(f'<g id="nb-{k}" opacity="0"><circle cx="{x + w - 520 * unit:g}" cy="{y + 520 * unit:g}" r="{380 * unit:g}" fill="{ACCENT}"/><text x="{x + w - 520 * unit:g}" y="{y + 660 * unit:g}" font-size="{420 * unit:g}" text-anchor="middle" fill="#15120a" font-weight="900">{n}</text></g>')
    cars_card = next((cd for cd in c.get("cards", []) if cd["type"] == "cars"), None)
    ncar = cars_card.get("count", 2) if cars_card else 0
    if ncar and c.get("porch") in R:
        px_, py_, pw, ph_ = R[c["porch"]]
        cw = pw * 0.36; chh = min(ph_ * 0.72, cw * 2); gapx = (pw - ncar * cw) / (ncar + 1)
        for j in range(ncar):
            svg.append(f'<g transform="translate({px_ + gapx + j * (cw + gapx):.0f} {py_ + (ph_ - chh) / 2:.0f})"><g id="car{j}" opacity="0"><rect width="{cw:.0f}" height="{chh:.0f}" rx="{cw * 0.23:.0f}" fill="{ACCENT}"/><rect x="{cw * 0.11:.0f}" y="{chh * 0.2:.0f}" width="{cw * 0.78:.0f}" height="{chh * 0.23:.0f}" rx="{cw * 0.11:.0f}" fill="#15120a" opacity="0.7"/><rect x="{cw * 0.11:.0f}" y="{chh * 0.66:.0f}" width="{cw * 0.78:.0f}" height="{chh * 0.18:.0f}" rx="{cw * 0.11:.0f}" fill="#15120a" opacity="0.7"/></g></g>')
    dims = next((cd for cd in c.get("cards", []) if cd["type"] == "dims"), None)
    if dims:
        svg.append(f'<g id="dim-w" stroke="{ACCENT}" stroke-width="70" fill="none"><path id="dim-wp" d="M0 -180 H{Wmm}" stroke-dasharray="{Wmm}" stroke-dashoffset="{Wmm}"/></g>')
        svg.append(f'<g id="dim-d" stroke="{ACCENT}" stroke-width="70" fill="none"><path id="dim-dp" d="M-180 0 V{Dmm}" stroke-dasharray="{Dmm}" stroke-dashoffset="{Dmm}"/></g>')
    svg.append("</svg>")
    SVG = "\n      ".join(svg)
    u_ = esc(dims.get("unit", "'")) if dims else ""
    dl = (f'<div id="dl-w" class="dl">{dims["w"]}{u_}</div><div id="dl-d" class="dl" style="top: {SVG_H // 2 + 70}px">{dims["d"]}{u_}</div>') if dims else ""
    body = [f"""    <div id="pl" class="glass">
      <div id="pl-k" data-layout-ignore>{esc(c.get("kicker", "PELAN LANTAI"))}</div>
      <div style="position: relative">
      {SVG}
      {dl}
      </div>
    </div>"""]
    js = ['    tl.fromTo("#pl", { opacity: 0, x: -120 }, { opacity: 1, x: 0, duration: 0.5, ease: "expo.out" }, 0.05);',
          '    tl.fromTo(".rm", { opacity: 0 }, { opacity: 1, duration: 0.25, stagger: 0.04, ease: "power1.out" }, 0.15);']
    cue(s0 - 0.05, "whoosh", "plan card slides in")
    cards_html = []
    for i, cd in enumerate(c.get("cards", [])):
        tc = A(cd["at"])
        if cd["type"] == "text":
            cards_html.append(f'<div id="cd-{i}" class="cd glass"><div class="kick">{esc(cd["kicker"])}</div><div class="hd v" style="font-size: {cd.get("size", 64)}px">{esc(cd["value"])}</div>' + (f'<div class="s">{cd["sub"]}</div>' if cd.get("sub") else "") + "</div>")
        elif cd["type"] == "dims":
            cards_html.append(f'<div id="cd-{i}" class="cd glass"><div class="kick">{esc(cd["kicker"])}</div><div class="hd v"><span id="n-w">{cd["w"]}</span>{u_} × <span id="n-d">{cd["d"]}</span>{u_}</div>' + (f'<div class="s">{cd["sub"]}</div>' if cd.get("sub") else "") + "</div>")
            js += [f'    tl.to("#dim-wp", {{ strokeDashoffset: 0, duration: 0.5, ease: "power2.out" }}, {h(tc)});',
                   f'    tl.to("#dim-dp", {{ strokeDashoffset: 0, duration: 0.7, ease: "power2.out" }}, {h(tc + 0.2)});',
                   f'    tl.to(["#dl-w", "#dl-d"], {{ opacity: 1, duration: 0.3, stagger: 0.2 }}, {h(tc + 0.35)});',
                   '    const n = { w: 0, d: 0 };',
                   f'    tl.fromTo(n, {{ w: 0, d: 0 }}, {{ w: {cd["w"]}, d: {cd["d"]}, duration: 0.9, ease: "power2.out",',
                   f'      onUpdate: () => {{ document.getElementById("n-w").textContent = Math.round(n.w); document.getElementById("n-d").textContent = Math.round(n.d); }} }}, {h(tc)});']
            cue(tc + 0.9, "tick", "dimension counter lands")
        elif cd["type"] == "cars":
            cards_html.append(f'<div id="cd-{i}" class="cd glass cd-car"><div class="kick">{esc(cd["kicker"])}</div><div class="hd v" style="font-size: 64px; display: flex; align-items: center">{ic("car") * ncar} {esc(cd["text"])}</div></div>')
            if c.get("porch") in R:
                js.append(f'    tl.to("#hl-{c["porch"]}", {{ opacity: 0.25, duration: 0.25 }}, {h(tc)});')
            if ncar:
                js.append(f'    tl.fromTo([{", ".join(chr(34) + "#car" + str(j) + chr(34) for j in range(ncar))}], {{ opacity: 0, y: 1200 }}, {{ opacity: 1, y: 0, duration: 0.45, stagger: 0.15, ease: "back.out(1.6)" }}, {h(tc)});')
        js.append(f'    inUp("#cd-{i}", {h(tc)});')
        cue(tc, cd.get("sfx"), f"lot card {i}")
    body.append('    <div id="cds">' + "".join(cards_html) + "</div>")
    tT = A(c["tour_start"]) if c.get("tour_start") else s1
    if c.get("cards"):
        js.append(f'    out([{", ".join(chr(34) + "#cd-" + str(i) + chr(34) for i in range(len(c["cards"])))}], {h(tT - 0.3)}, 0.2);')
    fade = ['"#dl-w"', '"#dl-d"', '"#dim-w"', '"#dim-d"'] if dims else []
    fade += [f'"#car{j}"' for j in range(ncar)]
    if fade:
        js.append(f'    tl.to([{", ".join(fade)}], {{ opacity: 0, duration: 0.2 }}, {h(tT - 0.3)});')
    if cars_card and c.get("porch") in R:
        js.append(f'    tl.to("#hl-{c["porch"]}", {{ opacity: 0, duration: 0.2 }}, {h(tT - 0.3)});')
    steps = c.get("steps", [])
    if steps:
        js += [f'    tl.to("#pl", {{ x: 742, y: -60, scale: 0.6, duration: 0.6, ease: "power3.inOut" }}, {h(tT - 0.2)});',
               '    const hl = (k, t, o = 0.62) => tl.to("#hl-" + k, { opacity: o, duration: 0.25, ease: "power2.out" }, t);',
               '    const un = (ks, t) => tl.to(ks.map(k => "#hl-" + k), { opacity: 0, duration: 0.2 }, t);',
               '    tl.set("#lt", { opacity: 0 }, 0);',
               '    const lt = (k, v, t) => { tl.set("#lt-k", { textContent: k }, t); tl.set("#lt-v", { textContent: v }, t);',
               '      tl.fromTo("#lt", { opacity: 0, x: -60 }, { opacity: 1, x: 0, duration: 0.4, ease: "expo.out" }, t); };']
        cue(tT - 0.2, "whoosh", "plan moves to the corner")
    badges, counts, badge_open = [], [], None
    for st in steps:
        ts = A(st["at"])
        if st.get("clear"):
            js.append(f'    un({json.dumps(st["clear"])}, {h(ts - 0.1)});')
        if st.get("hide_label"):
            js.append(f'    out("#lt", {h(ts - 0.25)});')
            js.append(f'    tl.set("#lt", {{ visibility: "visible" }}, {h(ts + 0.2)});')
            if badge_open is not None:
                js.append(f'    out("#pv{badge_open}", {h(ts - 0.25)});'); badge_open = None
        for k in st.get("hl", []):
            js.append(f'    hl("{k}", {h(ts)});')
        op = 0.8 if st.get("color") else 0.62
        for i, k in enumerate(st.get("hl_seq", [])):
            js.append(f'    hl("{k}", {h(ts + i * (0.15 if st.get("numbers") else 0.12))}, {op});')
            if st.get("numbers") and any(k == nk for nk, _ in c.get("numbered", [])):
                js.append(f'    inPop("#nb-{k}", {h(ts + i * 0.15)});')
        if st.get("color"):
            js.append(f'    tl.set({json.dumps(["#hl-" + k for k in st.get("hl_seq", []) + st.get("hl", [])])}, {{ fill: "{st["color"]}" }}, {h(ts)});')
        if st.get("title"):
            js.append(f'    lt({json.dumps(st.get("kicker", ""))}, {json.dumps(st["title"])}, {h(ts)});')
        for k in st.get("flash", []):
            js.append(f'    tl.to("#hl-{k}", {{ opacity: 0.22, duration: 0.2, yoyo: true, repeat: 3 }}, {h(ts)});')
        if st.get("badge"):
            bi = len(badges); badges.append(f'<div id="pv{bi}" class="pv">{ic(st.get("icon", "shield"))} {esc(st["badge"])}</div>')
            js.append(f'    tl.fromTo("#pv{bi}", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.42, ease: "back.out(2.2)" }}, {h(ts)});')
            if badge_open is not None:
                js.append(f'    out("#pv{badge_open}", {h(ts - 0.25)});')
            badge_open = bi
        if st.get("count"):
            ci = len(counts)
            counts.append(f'<div id="cnt{ci}"' + (f' style="background: {ACCENT}; color: #15120a"' if ci == 0 else ' class="glass"') + f'>{esc(st["count"])}</div>')
            js.append(f'    inUp("#cnt{ci}", {h(ts)}, 0.4);')
        cue(ts, st.get("sfx"), f"tour: {st.get('title') or st.get('badge') or st.get('count') or st['at']}")
    if badge_open is not None:
        js.append(f'    out("#pv{badge_open}", {h(s1 - 0.5)});')
    if steps:
        body.append('    <div id="lt" class="glass"><div id="lt-k" class="kick"></div><div id="lt-v" class="hd v"></div></div>')
    body += [f"    {b}" for b in badges]
    if counts:
        body.append('    <div id="cnt" class="cnt">' + "".join(counts) + "</div>")
    js.append(f'    tl.to("#root", {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, {h(s1 - 0.25)});')
    css = f"""
    #pl {{ position: absolute; left: 60px; top: 300px; width: 340px; padding: 20px; border-radius: 30px; transform-origin: 0 0; }}
    #pl-k {{ font-weight: 800; font-size: 22px; letter-spacing: 0.18em; color: {ACCENT}; margin: 0 0 10px 4px; }}
    #pl svg text.lb {{ fill: #fff; font-family: "Inter", sans-serif; font-weight: 800; opacity: 0.88; }}
    .dl {{ position: absolute; font-family: "Montserrat", sans-serif; font-weight: 900; color: {ACCENT}; font-size: 34px; opacity: 0; }}
    #dl-w {{ left: {SVG_W // 2}px; top: 36px; }} #dl-d {{ left: -6px; transform: rotate(-90deg); }}
    #cds {{ position: absolute; left: 450px; top: 300px; width: 570px; display: flex; flex-direction: column; gap: 22px; }}
    .cd {{ border-radius: 28px; padding: 26px 30px; }}
    .cd .v {{ font-size: 104px; margin-top: 6px; white-space: nowrap; }}
    .cd .s {{ font-size: 30px; font-weight: 600; opacity: 0.85; margin-top: 8px; }}
    .cd-car svg {{ width: 70px; height: 70px; color: {ACCENT}; margin-right: 6px; }}
    #lt {{ position: absolute; left: 60px; top: 1120px; padding: 22px 34px 24px; border-radius: 26px; max-width: 760px; }}
    #lt .v {{ font-size: 66px; margin-top: 6px; white-space: nowrap; }}
    .pv {{ position: absolute; left: 60px; top: 1000px; display: flex; align-items: center; gap: 14px; padding: 14px 26px 14px 18px; border-radius: 999px;
      background: {ACCENT}; color: #15120a; font-weight: 900; font-size: 32px; letter-spacing: 0.08em; opacity: 0; }}
    .pv svg {{ width: 44px; height: 44px; }}
    .cnt {{ position: absolute; left: 60px; top: 990px; display: flex; gap: 16px; }}
    .cnt div {{ padding: 14px 26px; border-radius: 20px; font-family: "Montserrat", sans-serif; font-weight: 900; font-size: 40px; }}"""
    scene("g-plan", s0, s1, page("g-plan", css, "\n".join(body), "\n" + "\n".join(js)))

# ------------------------------------------------------------------ status: built now -> completion date
if "status" in SC:
    c = SC["status"]; s0, s1 = starts["status"], ends["status"]; h = lambda x: r3(x - s0)
    now, nx = c["now"], c.get("next")
    tA_, tB_ = A(now["at"]), A(nx["at"]) if nx else None
    tQ = A(nx.get("big_at", nx["at"])) if nx else None
    body = f"""    <div id="et" class="glass">
      <div class="kick">{esc(c.get("kicker", "Status projek"))}</div>
      <div id="et-r1" class="row"><div id="et-d1" class="dot">{ic("check")}</div><div class="hd tx"><small>{esc(now.get("small", ""))}</small>{esc(now["text"])}</div></div>""" + (f"""
      <div id="et-bar"><div id="et-fill"></div></div>
      <div id="et-r2" class="row"><div id="et-d2" class="dot">{ic("clock")}</div><div class="hd tx"><small>{esc(nx.get("small", ""))}</small><span id="et-q" class="y">{esc(nx["text"])}</span></div></div>""" if nx else "") + """
    </div>"""
    js = [f'    inUp("#et", {h(tA_)}, 0.45);',
          f'    tl.fromTo("#et-r1", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.4, ease: "expo.out" }}, {h(tA_ + 0.1)});',
          f'    tl.fromTo("#et-d1", {{ scale: 0.4 }}, {{ scale: 1, duration: 0.45, ease: "back.out(2.4)" }}, {h(tA_ + 0.15)});']
    if nx:
        js = ['    tl.set("#et-fill", { scaleX: 0 }, 0);'] + js + [
            f'    tl.fromTo("#et-r2", {{ opacity: 0 }}, {{ opacity: 0.35, duration: 0.3 }}, {h(tA_ + 0.3)});',
            f'    tl.to("#et-fill", {{ scaleX: 0.72, duration: 1.4, ease: "power2.inOut" }}, {h(tB_ - 0.6)});',
            f'    tl.to("#et-r2", {{ opacity: 1, duration: 0.3 }}, {h(tB_)});',
            f'    tl.fromTo("#et-q", {{ opacity: 0, scale: 1.6, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.35, ease: "power4.out" }}, {h(tQ)});',
            '    tl.set("#et-q", { display: "inline-block", transformOrigin: "0% 60%" }, 0);']
        cue(tQ, "impact", f"{nx['text']} lands")
    js.append(f'    out("#et", {h(s1 - 0.25)});')
    cue(tA_, "pop", f"status: {now['text']}")
    css = f"""
    #et {{ position: absolute; left: 60px; right: 60px; top: 300px; padding: 34px 40px 40px; border-radius: 34px; }}
    .row {{ display: flex; align-items: center; gap: 22px; margin-top: 18px; }}
    .dot {{ width: 84px; height: 84px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex: none; }}
    .dot svg {{ width: 52px; height: 52px; stroke-width: 2.6; }}
    #et-d1 {{ background: {ACCENT}; color: #15120a; }} #et-d2 {{ border: 5px solid {ACCENT}; color: {ACCENT}; }}
    .tx {{ font-size: 58px; }} .tx small {{ display: block; font-family: "Inter", sans-serif; font-size: 28px; font-weight: 600; letter-spacing: 0; opacity: 0.8; margin-bottom: 6px; }}
    #et-bar {{ position: relative; height: 14px; border-radius: 7px; background: rgba(255,255,255,0.15); margin: 26px 0 8px 102px; overflow: hidden; }}
    #et-fill {{ position: absolute; left: 0; top: 0; bottom: 0; width: 100%; background: {ACCENT}; transform-origin: 0 50%; }}
    #et-q {{ font-size: 120px; }}"""
    scene("g-eta", s0, s1, page("g-eta", css, body, "\n" + "\n".join(js)))

# ------------------------------------------------------------------ price: old price struck, new price counts down
if "price" in SC:
    c = SC["price"]; s0, s1 = starts["price"], ends["price"]; h = lambda x: r3(x - s0)
    cur = c.get("currency", "RM"); old, new = c.get("old"), c["new"]
    tNow, tNum = A(new["at"]), A(new.get("count_at", new["at"]))
    start_v = old["value"] if old else round(new["value"] * 1.05, -2)
    body = ['    <div id="pr-dim"></div>']
    js = ['    tl.fromTo("#pr-dim", { opacity: 0 }, { opacity: 1, duration: 0.3 }, 0);']
    if old:
        tOld = A(old["at"])
        body.append(f'    <div id="pr" class="glass"><div class="kick" style="color: #fff; opacity: 0.75">{esc(old.get("kicker", "Harga asal"))}</div><div id="pr-old" class="hd">{cur}{fmt_money(old["value"])}<div id="pr-x"></div></div></div>')
        js += [f'    inUp("#pr", {h(tOld - 0.05)}, 0.5);',
               '    tl.set("#pr-x", { scaleX: 0, rotation: -6 }, 0);',
               f'    tl.to("#pr-x", {{ scaleX: 1, rotation: -6, duration: 0.35, ease: "power3.out" }}, {h(tNow - 0.45)});',
               f'    tl.to("#pr-old", {{ opacity: 0.45, duration: 0.3 }}, {h(tNow - 0.25)});']
        cue(tOld - 0.05, "whoosh", "price card in")
        cue(tNow - 0.45, "tick", "red strike through the old price")
    save = f'<div id="pr-sv">{esc(c["save"])}</div>' if c.get("save") else ""
    body.append(f'    <div id="pr-b" class="glass"><div class="kick">{esc(new.get("kicker", "Sekarang dari"))}</div><div id="pr-now" class="hd y">{cur}<span id="pr-n">{fmt_money(start_v)}</span></div>{save}</div>')
    js += ['    tl.set("#pr-b", { opacity: 0 }, 0);',
           f'    tl.to("#pr-b", {{ opacity: 1, y: 0, duration: 0.45, ease: "expo.out" }}, {h(tNow)});',
           f'    const p = {{ v: {start_v} }};',
           f'    tl.fromTo(p, {{ v: {start_v} }}, {{ v: {new["value"]}, duration: 1.1, ease: "power3.out",',
           f'      onUpdate: () => {{ document.getElementById("pr-n").textContent = (Math.round(p.v / 100) * 100).toLocaleString("en-US"); }} }}, {h(tNum)});',
           f'    tl.fromTo("#pr-now", {{ scale: 1 }}, {{ scale: 1.08, duration: 0.14, yoyo: true, repeat: 1, ease: "power2.out" }}, {h(tNum + 1.1)});']
    if save:
        js.append(f'    tl.fromTo("#pr-sv", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.42, ease: "back.out(2.4)" }}, {h(tNum + 1.3)});')
        cue(tNum + 1.3, "pop", c["save"])
    js.append(f'    out({json.dumps(["#pr", "#pr-b"] if old else ["#pr-b"])}, {h(s1 - 0.25)});')
    cue(tNum + 1.1, "kaching", "new price lands")
    css = f"""
    #pr-dim {{ position: absolute; inset: 0; background: rgba(5,6,10,0.55); }}
    #pr, #pr-b {{ position: absolute; left: 60px; right: 60px; padding: 36px 44px 40px; border-radius: 36px; text-align: center; }}
    #pr {{ top: 330px; }} #pr-b {{ top: {640 if old else 420}px; }}
    #pr-old {{ position: relative; display: inline-block; font-size: 112px; margin-top: 8px; }}
    #pr-x {{ position: absolute; left: -12px; right: -12px; top: 50%; height: 12px; margin-top: -6px; background: #ff4d4d; border-radius: 6px;
      transform-origin: 0 50%; }}
    #pr-now {{ font-size: 150px; margin-top: 14px; white-space: nowrap; text-shadow: 0 0 50px rgba(255,200,61,0.35); }}
    #pr-sv {{ display: inline-block; margin-top: 22px; padding: 14px 30px; border-radius: 999px; background: #2ecc71; color: #06210f; font-weight: 900; font-size: 36px; letter-spacing: 0.06em; }}"""
    scene("g-price", s0, s1, page("g-price", css, "\n".join(body), "\n" + "\n".join(js)))

# ------------------------------------------------------------------ package: checklist + stamp
if "package" in SC:
    c = SC["package"]; s0, s1 = starts["package"], ends["package"]; h = lambda x: r3(x - s0)
    items = c["items"]
    rows = "\n".join(f'      <div id="pk-{i}" class="it"><div class="ck">{ic("check")}</div><div class="tg{" bk" if it.get("light") else ""}">{esc(it["tag"])}</div><div class="nm">{esc(it["text"])}</div></div>'
                     for i, it in enumerate(items))
    body = f"""    <div id="pk-dim"></div>
    <div id="pk" class="glass">
      <div class="kick">{esc(c.get("kicker", "Pakej pembeli"))}</div>
      <div class="hd t">{esc(c.get("title", ""))}</div>
{rows}
    </div>""" + (f'\n    <div id="pk-st"><span class="hd">{esc(c["stamp"]["text"])}</span></div>' if c.get("stamp") else "")
    js = ['    tl.fromTo("#pk-dim", { opacity: 0 }, { opacity: 1, duration: 0.3 }, 0);', '    inUp("#pk", 0.02, 0.45);', '    tl.set([".it"], { opacity: 0 }, 0);']
    cue(s0 - 0.05, "whoosh", "package card in")
    for i, it in enumerate(items):
        ti = A(it["at"])
        js += [f'    tl.fromTo("#pk-{i}", {{ opacity: 0.0, x: -50 }}, {{ opacity: 1, x: 0, duration: 0.35, ease: "expo.out" }}, {r3(ti - s0 - 0.05)});',
               f'    tl.fromTo("#pk-{i} .ck", {{ scale: 0.3, rotation: -40 }}, {{ scale: 1, rotation: 0, duration: 0.45, ease: "back.out(2.6)" }}, {h(ti)});']
        cue(ti, "pop" if i % 2 == 0 else "tick", f"package row {i}")
    if c.get("stamp"):
        tS = A(c["stamp"]["at"])
        js.append(f'    tl.fromTo("#pk-st", {{ opacity: 0, scale: 2.2 }}, {{ opacity: 1, scale: 1, duration: 0.22, ease: "power4.in" }}, {h(tS - 0.12)});')
        cue(tS + 0.1, "stamp", f"{c['stamp']['text']} stamp")
    js.append(f'    tl.to("#root", {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, {h(s1 - 0.25)});')
    css = f"""
    #pk-dim {{ position: absolute; inset: 0; background: rgba(5,6,10,0.6); }}
    #pk {{ position: absolute; left: 60px; right: 60px; top: 280px; padding: 36px 40px 30px; border-radius: 36px; }}
    #pk .hd.t {{ font-size: 76px; margin: 8px 0 18px; }}
    .it {{ display: flex; align-items: center; gap: 22px; height: 112px; border-top: 2px solid rgba(255,255,255,0.1); }}
    .ck {{ width: 68px; height: 68px; border-radius: 50%; background: {ACCENT}; color: #15120a; display: flex; align-items: center; justify-content: center; flex: none; }}
    .ck svg {{ width: 42px; height: 42px; stroke-width: 3; }}
    .tg {{ padding: 8px 18px; border-radius: 12px; background: #2ecc71; color: #06210f; font-weight: 900; font-size: 30px; letter-spacing: 0.08em; }}
    .tg.bk {{ background: #fff; color: #15120a; }}
    .nm {{ font-weight: 800; font-size: 46px; white-space: nowrap; }}
    #pk-st {{ position: absolute; left: 0; width: 1080px; top: {min(1010, 470 + 112 * len(items) + 30)}px; text-align: center; }}
    #pk-st span {{ display: inline-block; transform: rotate(-5deg); padding: 10px 40px 16px; border: 10px solid #2ecc71; border-radius: 22px;
      color: #2ecc71; font-size: 104px; white-space: nowrap; background: rgba(6,20,12,0.6); }}"""
    scene("g-pkg", s0, s1, page("g-pkg", css, body, "\n" + "\n".join(js)))

# ------------------------------------------------------------------ cashback: big counter + coin burst
if "cashback" in SC:
    c = SC["cashback"]; s0, s1 = starts["cashback"], ends["cashback"]; h = lambda x: r3(x - s0)
    tA_, tC = A(c["title"]["at"]), A(c["value"]["at"])
    amt, pre = c["value"]["amount"], c["value"].get("prefix", "RM")
    coins = "\n".join(f'    <div class="coin" id="cn{i}"></div>' for i in range(14))
    body = f"""    <img id="cs-bg" src="assets/footage/ext_blur.jpg" alt="" />
    <div id="cs-dim"></div>
{coins}
    <div id="cs-k" class="ctr kick">{esc(c.get("kicker", ""))}</div>
    <div id="cs-a" class="ctr hd">{esc(c["title"]["text"])}</div>
    <div id="cs-n" class="ctr hd y">{esc(pre)}<span id="cs-v">0</span></div>"""
    js = [f'    tl.fromTo("#cs-bg", {{ scale: 1.15 }}, {{ scale: 1, duration: {h(s1)}, ease: "none" }}, 0);',
          '    inUp("#cs-k", 0.05, 0.4);', f'    slam("#cs-a", {h(tA_)});', f'    inUp("#cs-n", {h(tC - 0.1)}, 0.3);',
          '    const c = { v: 0 };',
          f'    tl.fromTo(c, {{ v: 0 }}, {{ v: {amt}, duration: 1.0, ease: "power3.out",',
          f'      onUpdate: () => {{ document.getElementById("cs-v").textContent = (Math.round(c.v / 100) * 100).toLocaleString("en-US"); }} }}, {h(tC)});',
          f'    tl.fromTo("#cs-n", {{ scale: 1 }}, {{ scale: 1.1, duration: 0.14, yoyo: true, repeat: 1 }}, {h(tC + 1.0)});']
    for i in range(14):
        js.append(f'    tl.fromTo("#cn{i}", {{ x: 0, y: 0, opacity: 1, scale: 0.4 }}, {{ x: {math.cos(i / 14 * 6.283 + 0.3) * (260 + (i * 37) % 160):.0f}, y: {math.sin(i / 14 * 6.283 + 0.3) * (220 + (i * 53) % 140):.0f}, opacity: 0, scale: 1.1, duration: 1.1, ease: "power3.out" }}, {h(tC + 1.0)});')
    js.append(f'    tl.to("#root", {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, {h(s1 - 0.25)});')
    cue(tA_, "boom", f"{c['title']['text']} slams in")
    cue(tC + 1.0, "kaching", "cashback amount lands")
    cue(tC + 1.02, "sparkle", "coin burst")
    css = f"""
    #cs-bg {{ position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    #cs-dim {{ position: absolute; inset: 0; background: radial-gradient(circle at 50% 42%, rgba(40,30,5,0.55), rgba(5,6,10,0.85) 70%); }}
    #cs-k {{ top: 470px; font-size: 40px; }}
    #cs-a {{ top: 560px; font-size: 120px; }}
    #cs-n {{ top: 700px; font-size: 210px; white-space: nowrap; text-shadow: 0 0 70px rgba(255,200,61,0.45); }}
    .coin {{ position: absolute; left: 520px; top: 800px; width: 40px; height: 40px; border-radius: 50%; background: radial-gradient(circle at 35% 35%, #fff3c4, {ACCENT} 45%, #b8860b); opacity: 0; }}"""
    scene("g-cash", s0, s1, page("g-cash", css, body, "\n" + "\n".join(js)))

# ------------------------------------------------------------------ cta: tags, WhatsApp card with the number, end card
if "cta" in SC:
    c = SC["cta"]; s0, s1 = starts["cta"], ends["cta"]; h = lambda x: r3(x - s0)
    STY = {"accent": (ACCENT, "#15120a"), "light": ("#fff", "#15120a"), "alert": ("#ff3b3b", "#fff")}
    body = ['    <img id="ct-bg" src="assets/footage/ext_blur.jpg" alt="" />', '    <div id="ct-dim"></div>']
    js = [f'    tl.fromTo("#ct-bg", {{ scale: 1.12 }}, {{ scale: 1, duration: {h(s1)}, ease: "none" }}, 0);',
          '    tl.fromTo("#ct-dim", { opacity: 0.5 }, { opacity: 1, duration: 0.4 }, 0);',
          '    const tag = (s, t) => tl.fromTo(s, { opacity: 0, scale: 0.5, rotation: -6 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.4, ease: "back.out(2.4)" }, t);']
    cue(s0 - 0.05, "whoosh", "cut to the CTA")
    tags = c.get("tags", [])
    for i, tg in enumerate(tags):
        bg, fg = STY.get(tg.get("style", "accent"), STY["accent"])
        body.append(f'    <div id="tg{i}" class="tag" style="top: {300 + i * 120}px"><span style="background: {bg}; color: {fg}">{esc(tg["text"])}</span></div>')
        tt = A(tg["at"])
        js.append(f'    tag("#tg{i}", {h(tt)});')
        if tg.get("pulse"):
            js.append(f'    tl.to("#tg{i}", {{ scale: 1.07, duration: 0.3, yoyo: true, repeat: 5, ease: "sine.inOut" }}, {h(tt + 0.45)});')
        cue(tt, tg.get("sfx", "pop"), f"tag {tg['text']}")
    wa = c["whatsapp"]; tWA = A(wa["at"])
    spans = "".join(f'<span id="wa-{i}">{esc(g["text"]).replace(" ", "&nbsp;")}</span>' for i, g in enumerate(wa["groups"]))
    body.append(f"""    <div id="wa">
      <div id="wa-i">{ic("chat")}</div>
      <div><div id="wa-k">{esc(wa.get("kicker", "WHATSAPP SEKARANG"))}</div><div id="wa-n">{spans}</div></div>
    </div>""")
    if c.get("end_title"):
        body.append(f'    <div id="ct-end" class="ctr hd">{c["end_title"]}</div>')
    if c.get("summary"):
        body.append(f'    <div id="ct-sum" class="ctr">{c["summary"]}</div>')
    tE = speech_end + 0.2
    js += [f'    tl.fromTo("#wa", {{ opacity: 0, y: 60, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out" }}, {h(tWA)});',
           f'    tl.fromTo("#wa-i", {{ scale: 0.4, rotation: -30 }}, {{ scale: 1, rotation: 0, duration: 0.55, ease: "back.out(2.4)" }}, {h(tWA + 0.05)});',
           f'    tl.set({json.dumps(["#wa-" + str(i) for i in range(len(wa["groups"]))])}, {{ opacity: 0 }}, 0);',
           '    const grp = (s, t) => tl.fromTo(s, { opacity: 0, y: 28, filter: "blur(6px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.26, ease: "expo.out" }, t);']
    cue(tWA, "whoosh", "WhatsApp card")
    for i, g in enumerate(wa["groups"]):
        js.append(f'    grp("#wa-{i}", {h(A(g["at"]))});')
        cue(A(g["at"]), "pop" if i == len(wa["groups"]) - 1 else "tick", f"digits {g['text'].strip()}")
    if tags:
        js.append(f'    tl.to({json.dumps(["#tg" + str(i) for i in range(len(tags))])}, {{ y: -40, opacity: 0.0, duration: 0.4, stagger: 0.05, ease: "power2.in" }}, {h(tE)});')
    js.append(f'    tl.to("#wa", {{ y: 40, scale: 1.04, duration: 0.6, ease: "power3.inOut" }}, {h(tE + 0.1)});')
    if c.get("summary"):
        js.append(f'    tl.fromTo("#ct-sum", {{ opacity: 0, y: 70 }}, {{ opacity: 1, y: 50, duration: 0.5, ease: "expo.out" }}, {h(tE + 0.4)});')
    if c.get("end_title"):
        js.append(f'    tl.fromTo("#ct-end", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }}, {h(tE + 0.25)});')
    js.append(f'    tl.to("#wa", {{ boxShadow: "0 20px 60px rgba(0,0,0,0.5), 0 0 0 12px #25D366 inset", duration: 0.35, yoyo: true, repeat: 3, ease: "sine.inOut" }}, {h(tE + 0.8)});')
    cue(speech_end + 0.3, "ping", "end card")
    css = f"""
    #ct-bg {{ position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    #ct-dim {{ position: absolute; inset: 0; background: rgba(5,6,10,0.62); }}
    .tag {{ position: absolute; left: 0; width: 1080px; text-align: center; }}
    .tag span {{ display: inline-block; padding: 16px 40px; border-radius: 999px; white-space: nowrap;
      font-family: "Montserrat", sans-serif; font-weight: 900; font-size: 56px; letter-spacing: 0.02em; }}
    #wa {{ position: absolute; left: 60px; top: {max(720, 300 + len(tags) * 120 + 60)}px; width: 960px; padding: 34px 40px; border-radius: 40px; display: flex; align-items: center; gap: 30px;
      background: rgba(10,12,18,0.9); box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 0 4px #25D366 inset; }}
    #wa-i {{ width: 140px; height: 140px; border-radius: 50%; background: #25D366; color: #fff; display: flex; align-items: center; justify-content: center; flex: none; }}
    #wa-i svg {{ width: 84px; height: 84px; stroke-width: 1.7; }}
    #wa-k {{ font-weight: 800; font-size: 32px; letter-spacing: 0.14em; color: #25D366; }}
    #wa-n {{ font-family: "Montserrat", sans-serif; font-weight: 900; font-size: 100px; line-height: 1.05; letter-spacing: -0.02em; white-space: nowrap; }}
    #wa-n span {{ display: inline-block; }}
    #ct-end {{ top: 560px; font-size: 92px; }}
    #ct-sum {{ top: 1010px; font-size: 40px; font-weight: 700; }}
    #ct-sum b {{ color: {ACCENT}; }}"""
    page_html = page("g-cta", css, "\n".join(body), "\n" + "\n".join(js)).replace(
        'data-composition-id="g-cta" data-width="1080" data-height="1920">',
        f'data-composition-id="g-cta" data-width="1080" data-height="1920" data-composition-variables=\'[{{"id":"phone","type":"string","label":"Nombor telefon","default":"{esc(P.get("phone", ""))}"}}]\'>', 1)
    scene("g-cta", s0, s1, page_html)

# =============================================================== CAPTIONS
CC = P.get("captions", {})
CAP_LINES = CC.get("lines", [])
SKIP_UNITS = {tuple(x) for x in CC.get("skip", [])}
NOBREAK = {tuple(x) for x in CC.get("nobreak", [])}
LIMIT = CC.get("limit", 22)
clen = lambda g: sum(len(x["text"]) + 1 for x in g) - 1
groups = []
for lid in CAP_LINES:
    us = [dict(u, id=f"{lid}-{i}") for i, u in enumerate(lines[lid]["units"]) if (lid, u["text"]) not in SKIP_UNITS]
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
            if all(clen(c_) <= LIMIT + 2 for c_ in chunks) or k > 6:
                break
            k += 1
        if len(chunks) > 1 and len(chunks[-1]) == 1 and clen(chunks[-2] + chunks[-1]) <= LIMIT + 3:
            last = chunks.pop(); chunks[-1] = chunks[-1] + last
        groups.extend(chunks)
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
cap = ["""<template>
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
    spans = " ".join(f'<span id="cw-{x["id"]}" class="cw">{esc(clean(x["text"]))}</span>' for x in g)
    cap.append(f'    <div id="cg-{gi}" class="clip cg" data-start="{r3(st)}" data-duration="{r3(en - st)}" data-track-index="0"><div id="cgi-{gi}" class="cg-in">{spans}</div></div>')
cap.append(f"""  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    const Y = "{ACCENT}";""")
for gi, (st, en, g) in enumerate(cg):
    cap.append(f'    tl.fromTo("#cgi-{gi}", {{ opacity: 0, y: 16, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.14, ease: "back.out(2)" }}, {r3(st)});')
    for k, x in enumerate(g):
        on = max(x["s"], st)
        cap.append(f'    tl.fromTo("#cw-{x["id"]}", {{ color: "#ffffff", scale: 1 }}, {{ color: Y, scale: 1.04, duration: 0.08, ease: "power2.out" }}, {r3(on)});')
        if k + 1 < len(g):
            off = max(g[k + 1]["s"], on + 0.12)
            cap.append(f'    tl.to("#cw-{x["id"]}", {{ color: "#ffffff", scale: 1, duration: 0.08, ease: "power2.in" }}, {r3(off)});')
    cap.append(f'    tl.to("#cgi-{gi}", {{ opacity: 0, duration: 0.08, ease: "power2.in" }}, {r3(en - 0.08)});')
    cap.append(f'    tl.set("#cgi-{gi}", {{ visibility: "hidden" }}, {r3(en)});')
cap.append("""    window.__timelines["captions"] = tl;
  </script>
</template>
""")
open(os.path.join(COMP, "captions.html"), "w").write("\n".join(cap))

# =============================================================== INDEX
TL = P.get("timeline", {})
o = []
w = o.append
w(f"""<!doctype html>
<html lang="{P.get("lang", "ms")}" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>{esc(P["title"])}</title>
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
      <!-- PICTURE: trims of the site-visit footage (muted: the voice is the ElevenLabs VO) -->
      <div id="cam">
        <div id="cam-inner" data-layout-allow-overflow>""")
for i, s in enumerate(shots):
    sid = f"v{i:02d}"
    if s["src"] == "map":
        continue
    if s["src"] in ("freeze", "still"):
        img = "freeze.jpg" if s["src"] == "freeze" else "ext_blur.jpg"
        w(f'          <img id="{sid}" class="clip" src="assets/footage/{img}" alt="" data-start="{r3(s["start"])}" data-duration="{r3(s["dur"])}" data-track-index="1" /><!-- {esc(s["why"])} -->')
    else:
        w(f'          <video id="{sid}" class="clip" src="{FOOTAGE}" muted playsinline data-start="{r3(s["start"])}" data-duration="{r3(s["dur"])}" data-media-start="{r3(s["src"])}" data-track-index="1"></video><!-- {esc(s["why"])} -->')
w(f'          <img id="v-end" class="clip" src="assets/footage/ext_blur.jpg" alt="" data-start="{r3(CTA_AT)}" data-duration="{r3(TOTAL - CTA_AT)}" data-track-index="1" />')
w(f"""        </div>
      </div>
      <div id="grade"></div>
      <div id="flash"></div>

      <!-- VOICE: ElevenLabs "{esc(P["voice"].get("name", ""))}" ({P["voice"].get("model_id", "")}), enhanced by enhance_vo.py, one clip per line -->""")
for lid in ORDER:
    ln = lines[lid]
    w(f'      <audio id="vo-{lid}" class="clip" src="assets/audio/vo/{lid}.wav" data-start="{r3(ln["start"])}" data-duration="{r3(ln["dur"])}" data-volume="1" data-track-index="2"></audio>')
MU = P.get("music")
mstr = "none"
if MU and os.path.exists(os.path.join(VID, MU["file"])):
    MUSIC_AT = A(MU["start"]) if MU.get("start") else 0.0
    flen = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(VID, MU["file"])],
                                capture_output=True, text=True).stdout)
    mdur = min(TOTAL - MUSIC_AT, MU.get("length", flen))   # "length" = where the track ends audibly
    BED, LIFT = MU.get("bed", 0.16), MU.get("lift", 0.34)
    pts = [(0.0, 0.0), (0.25, BED)]
    for a0, a1 in [(A(x), A(y)) for x, y in MU.get("lifts", [])] + [(speech_end, TOTAL)]:
        a0, a1 = a0 - MUSIC_AT, a1 - MUSIC_AT
        pts += [(a0, BED), (a0 + 0.25, LIFT)]
        if a1 < mdur - 0.1:
            pts += [(a1 - 0.15, LIFT), (a1 + 0.1, BED)]
    lane = ",".join(f'{{&quot;t&quot;:{r3(max(0, t_))},&quot;v&quot;:{v}}}' for t_, v in pts)
    w('\n      <!-- MUSIC: ElevenLabs Music generated for this edit; ducked under the voice -->')
    w(f'      <audio id="music" class="clip" src="{MU["file"]}" data-start="{r3(MUSIC_AT)}" data-duration="{r3(mdur)}" data-media-start="0" data-volume="1" data-fade-out="1.2" data-automation="{{&quot;version&quot;:1,&quot;lanes&quot;:[{{&quot;target&quot;:&quot;volume&quot;,&quot;points&quot;:[{lane}]}}]}}" data-track-index="5"></audio>')
    mstr = f"{MUSIC_AT:.2f}->{MUSIC_AT + mdur:.2f}"
w("\n      <!-- SOUND EFFECTS: each one lands one frame after its picture event -->")
cues.sort()
lane_end, SFX_LANES, missing = {}, [3, 4, 10, 11, 12, 13], set()
for i, (tev, kind, why) in enumerate(cues):
    f, peak, vol, ln_ = SFX[kind]
    if not os.path.exists(os.path.join(VID, f)):
        missing.add(f); continue
    st = max(0.0, tev + 1 / FPS - peak)
    dur = min(ln_, TOTAL - st)
    sfx_lane = next((k for k in SFX_LANES if lane_end.get(k, -1) <= st), SFX_LANES[-1])
    lane_end[sfx_lane] = st + dur
    w(f'      <audio id="sfx-{i + 1:02d}" class="clip" src="{f}" data-start="{r3(st)}" data-duration="{r3(dur)}" data-volume="{vol}" data-track-index="{sfx_lane}"></audio><!-- {esc(why)} -->')
w("\n      <!-- MOTION GRAPHICS -->")
for i, (sid, a, b) in enumerate(SCENES):
    w(f'      <div id="{sid}" class="scene" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{r3(a)}" data-duration="{r3(b - a)}" data-track-index="{6 + i % 2}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index: 10"></div>')
if cg:
    cap_end = max(en for _, en, _ in cg)
    w(f'      <div id="captions" class="scene" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{r3(cap_end + 0.05)}" data-track-index="9" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index: 20"></div>')
w("    </div>\n    <script>\n      window.__timelines = window.__timelines || {};\n      const tl = gsap.timeline({ paused: true });")
w("      // slow push-in on every shot; the hook gets a stronger one")
strong = set(TL.get("strong_push", []))
for s in shots:
    if s["src"] == "map":
        continue
    z = 1.14 if s["lid"] in strong else 1.07
    w(f'      tl.fromTo("#cam-inner", {{ scale: 1 }}, {{ scale: {z}, duration: {r3(s["dur"] - 0.002)}, ease: "none", immediateRender: false }}, {r3(s["start"])});')
w(f'      tl.set("#cam-inner", {{ scale: 1 }}, {r3(CTA_AT)});')
for tt in [L(x) for x in TL.get("flash_cuts", [])]:
    w(f'      tl.to("#flash", {{ opacity: 0.7, duration: 0.06, ease: "power2.in" }}, {r3(tt - 0.06)});')
    w(f'      tl.to("#flash", {{ opacity: 0, duration: 0.25, ease: "power2.out" }}, {r3(tt)});')
w(f'      tl.set({{}}, {{}}, {r3(TOTAL)});\n      window.__timelines["main"] = tl;\n    </script>\n  </body>\n</html>\n')
open(os.path.join(VID, "index.html"), "w").write("\n".join(o))

# =============================================================== REPORT
json.dump({lid: {"start": round(v["start"], 3), "end": round(v["end"], 3),
                 "words": [{"t": w_["sp"], "s": round(w_["s"], 3), "e": round(w_["e"], 3)} for w_ in v["words"]]}
           for lid, v in lines.items()}, open(os.path.join(VID, "vo_timing.json"), "w"), ensure_ascii=False, indent=0)
print(f"total {TOTAL}s, speech ends {speech_end:.2f}s, music {mstr}, {len(shots)} shots, {len(cues)} sfx, {len(cg)} caption groups")
if missing:
    print("WARNING: missing SFX files (skipped):", ", ".join(sorted(missing)))
for sid, a, b in SCENES:
    print(f"  {sid:8s} {a:6.2f} -> {b:6.2f}")
for s in shots:
    print(f"  shot {s['lid']:6s} {s['start']:6.2f}+{s['dur']:5.2f}  src {s['src']}")
