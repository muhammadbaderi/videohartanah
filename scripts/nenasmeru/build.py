"""Build the Jalan Nenas, Meru video timeline (scripts/<name>/ -> <name>/) from the voiceover's word timings.

Inputs (all in scripts/<name>/):
  vo_lines.json       the script (spoken text, caption text, v3 audio tag) and the ElevenLabs settings
  vo_align.json       character timings from ElevenLabs (with-timestamps) for each line's chosen take
  edl.json            lead-in, gaps between lines, shots (anchored to words) and how each enters, music
  captions_src.json   caption chunks: display tokens mapped to spoken-word indices

Writes:
  <name>/index.html                   (OVERWRITTEN: Studio edits to it are lost)
  <name>/compositions/captions.html    (OVERWRITTEN)
  the CUES block of every compositions/g-*.html (only the text between the CUES markers):
    W = word start times, E = word end times (seconds, local to the scene), D = scene length,
    PB = where the second part of the split CTA line starts (the end card).
The rest of each scene file is hand-written and never touched.

Usage: python3 -I scripts/<name>/build.py
"""
import json, os, re, html, wave

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = os.path.basename(HERE)  # scripts/<name>/ builds the HyperFrames project <name>/
VID = os.path.abspath(os.path.join(HERE, "..", "..", NAME))
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
    if t_prev_end is None:
        clip0 = E.get("lead_in", 0.0) - ws[0][1]
    else:
        clip0 = t_prev_end + E["gaps"].get(k, E["gaps"]["default"]) - ws[0][1]
    parts = [{"media_in": 0.0, "media_out": dur, "start": clip0}]
    if clip0 < 0:  # lead-in silence longer than the lead-in: skip into the file
        parts = [{"media_in": -clip0, "media_out": dur, "start": 0.0}]
    split = E.get("split", {}).get(k)
    if split:
        # cut the pause after word `after`: part A ends just after it, part B starts just before the next word
        i = split["after"]
        a_out = ws[i][2] + 0.08
        b_in = ws[i + 1][1] - 0.12
        p0 = parts[0]
        parts = [{"media_in": p0["media_in"], "media_out": a_out, "start": p0["start"]},
                 {"media_in": b_in, "media_out": dur, "start": p0["start"] + (a_out - p0["media_in"]) + split["pause"]}]

    def to_film(t, parts=parts):
        for p in parts:
            if p["media_in"] - 0.05 <= t < p["media_out"] + 0.05:
                return p["start"] + t - p["media_in"]
        return None
    parts[-1]["media_out"] = min(parts[-1]["media_out"], ws[-1][2] + 0.3)
    words = [(w, to_film(s), to_film(e)) for w, s, e in ws]
    VO[k] = {"parts": parts, "words": words}
    t_prev_end = max(x[2] for x in words if x[2] is not None)

VO_END = t_prev_end
for k, nk in zip(LINE_IDS, LINE_IDS[1:]):
    p, nxt = VO[k]["parts"][-1], VO[nk]["parts"][0]["start"]
    p["media_out"] = min(p["media_out"], p["media_in"] + (nxt - 0.01 - p["start"]))
TOTAL = round(VO_END + E["end_hold"], 2)

# scenes: a scene starts with its line's first word (minus a short lead), the last runs to the end
SCENES = []
starts = [0.0] + [round(VO[k]["words"][0][1] - 0.12, 3) for k in LINE_IDS[1:]]
for i, k in enumerate(LINE_IDS):
    st = starts[i]
    en = starts[i + 1] if i + 1 < len(LINE_IDS) else TOTAL
    SCENES.append((SCENE_OF[k], k, round(st, 3), round(en, 3)))
SC = {s[0]: s for s in SCENES}
CTA_B = VO["cta"]["words"][E["split"]["cta"]["after"] + 1][1] - 0.12 if "cta" in E.get("split", {}) else SC["g-cta"][2]


def local_words(scene):
    sid, k, st, en = SC[scene]
    W = [round(x[1] - st, 3) if x[1] is not None else None for x in VO[k]["words"]]
    Ee = [round(x[2] - st, 3) if x[2] is not None else None for x in VO[k]["words"]]
    return W, Ee, round(en - st, 3)


# ---------------------------------------------------------------- shots and how they enter
LEAD = {"scan": 0.22, "whip": 0.12}          # incoming starts this early (it overlaps the outgoing)
TAIL = {"scan": 0.26, "whip": 0.14}          # outgoing stays this long after the seam


def anchor_time(scene, anchor):
    sid, k, st, en = SC[scene]
    if anchor in (0, "0"):
        return st
    m = re.fullmatch(r"0([+-][0-9.]+)", str(anchor))
    if m:
        return st + float(m.group(1))
    m = re.fullmatch(r"w(\d+)([+-][0-9.]+)?", anchor)
    return VO[k]["words"][int(m.group(1))][1] - 0.05 + (float(m.group(2)) if m.group(2) else 0.0)


SHOTS = []
for sh in E["shots"]:
    seam = round(anchor_time(sh["scene"], sh["at"]), 3)
    SHOTS.append(dict(sh, seam=seam, start=max(0.0, round(seam - LEAD.get(sh["in"], 0.0), 3))))
for i, sh in enumerate(SHOTS):
    nxt = SHOTS[i + 1] if i + 1 < len(SHOTS) else None
    sh["end"] = round(nxt["seam"] + TAIL.get(nxt["in"], 0.0), 3) if nxt else TOTAL
    m_until = re.fullmatch(r"cta_b([+-][0-9.]+)", str(sh.get("until", "")))
    if m_until:  # the shot ends under the end card instead of running to the end
        sh["end"] = round(CTA_B + float(m_until.group(1)), 3)

# ---------------------------------------------------------------- sound effects
# (scene, local time from W/E/D, file, volume, note) - the times mirror the scene files' animations.
# HIT = where each file's transient sits (placed so it lands one frame after its picture).
HIT = {"pop": 0.11, "click-soft": 0.045, "ping": 0.32, "sparkle": 0.02, "impact-bass-1": 0.045, "whoosh": 0.0,
       "stamp": 0.006, "shutter": 0.03, "scan": 0.07, "tick": 0.02, "whip": 0.03, "keys": 0.0, "pen-draw": 0.0, "riser": 1.32}
DUR = {"pop": 0.72, "click-soft": 0.366, "ping": 1.32, "sparkle": 1.8, "impact-bass-1": 2.116, "whoosh": 0.575,
       "stamp": 0.8, "shutter": 0.48, "scan": 0.6, "tick": 0.48, "whip": 0.48, "keys": 0.777, "pen-draw": 1.2, "riser": 1.36}
SFX_SPEC = [
    # intro / hook: the blueprint drafts itself
    ("g-hook", lambda W, E_, D: 0.0, "pen-draw", 0.32, "blueprint lines start drafting (intro)"),
    ("g-hook", lambda W, E_, D: W[2] + 0.02, "pop", 0.45, "marker sweeps under JE?"),
    ("g-hook", lambda W, E_, D: W[3] + 0.04, "click-soft", 0.55, "chip: deposit kereta"),
    ("g-hook", lambda W, E_, D: W[5] + 0.12, "tick", 0.5, "strike through deposit kereta"),
    ("g-hook", lambda W, E_, D: W[6] + 0.04, "click-soft", 0.55, "chip: sewa rumah"),
    ("g-hook", lambda W, E_, D: W[8] + 0.12, "tick", 0.5, "strike through sewa rumah"),
    ("g-hook", lambda W, E_, D: W[9] + 0.02, "scan", 0.45, "render develops over the drawing"),
    ("g-hook", lambda W, E_, D: W[13] + 0.02, "stamp", 0.42, "title block: RUMAH LANDED"),
    ("g-hook", lambda W, E_, D: W[14] + 0.06, "pop", 0.45, "1 TINGKAT"),
    # yes
    ("g-yes", lambda W, E_, D: W[0] + 0.02, "impact-bass-1", 0.13, "YES slams in"),
    ("g-yes", lambda W, E_, D: W[4] + 0.04, "pop", 0.45, "DENGAR + sound rings"),
    # intro: title block
    ("g-intro", lambda W, E_, D: W[2] - 0.02, "click-soft", 0.55, "title block card"),
    ("g-intro", lambda W, E_, D: W[2] + 0.12, "keys", 0.3, "row PROJEK types in"),
    ("g-intro", lambda W, E_, D: W[4] + 0.04, "stamp", 0.35, "BAHARU stamp"),
    ("g-intro", lambda W, E_, D: W[6] + 0.0, "keys", 0.3, "row LOKASI types in"),
    ("g-intro", lambda W, E_, D: W[6] + 0.05, "pop", 0.4, "pin icon"),
    # type: two cards, then the floor plan
    ("g-type", lambda W, E_, D: W[3] + 0.02, "pop", 0.45, "card TERES"),
    ("g-type", lambda W, E_, D: W[5] + 0.02, "click-soft", 0.6, "card SEMI-D"),
    ("g-type", lambda W, E_, D: W[7] + 0.05, "pen-draw", 0.3, "floor plan drafts in"),
    ("g-type", lambda W, E_, D: W[9] + 0.03, "pop", 0.45, "bedrooms light up 1-4"),
    ("g-type", lambda W, E_, D: W[11] + 0.02, "click-soft", 0.6, "counter 4 BILIK TIDUR"),
    ("g-type", lambda W, E_, D: W[13] + 0.03, "pop", 0.45, "bathrooms light up"),
    ("g-type", lambda W, E_, D: W[15] + 0.02, "click-soft", 0.6, "counter 2 BILIK AIR"),
    ("g-type", lambda W, E_, D: D - 0.36, "whoosh", 0.3, "plan zooms through into the map"),
    # loc: map
    ("g-loc", lambda W, E_, D: 0.25, "click-soft", 0.5, "header LOKASI STRATEGIK"),
    ("g-loc", lambda W, E_, D: 0.55, "pop", 0.5, "site pin lands"),
    ("g-loc", lambda W, E_, D: W[6] + 0.25, "click-soft", 0.55, "line + label Hospital Kapar"),
    ("g-loc", lambda W, E_, D: W[11] + 0.05, "pop", 0.45, "label SRA Meru 2"),
    ("g-loc", lambda W, E_, D: W[17] + 0.05, "click-soft", 0.55, "facility dots"),
    ("g-loc", lambda W, E_, D: W[17] + 0.3, "pop", 0.4, "legend chips"),
    # tenure: stamps
    ("g-tenure", lambda W, E_, D: W[0] + 0.02, "click-soft", 0.5, "PALING MENARIK"),
    ("g-tenure", lambda W, E_, D: W[4] + 0.1, "stamp", 0.75, "FREEHOLD stamp"),
    ("g-tenure", lambda W, E_, D: W[5] + 0.1, "stamp", 0.55, "RIZAB MELAYU stamp"),
    ("g-tenure", lambda W, E_, D: E_[6] + 0.05, "click-soft", 0.5, "DIJANGKA SIAP Q3 2027"),
    # pkg: checklist
    ("g-pkg", lambda W, E_, D: 0.12, "pop", 0.42, "package card"),
    ("g-pkg", lambda W, E_, D: W[2] + 0.04, "tick", 0.55, "tick: booking RM1,000"),
    ("g-pkg", lambda W, E_, D: W[4] + 0.04, "tick", 0.55, "tick: free SPA legal fee"),
    ("g-pkg", lambda W, E_, D: W[11] + 0.04, "tick", 0.55, "tick: free MOT fee"),
    # price
    ("g-price", lambda W, E_, D: 0.2, "pen-draw", 0.22, "render frame drafts in"),
    ("g-price", lambda W, E_, D: W[0] + 0.02, "click-soft", 0.55, "row TERES"),
    ("g-price", lambda W, E_, D: W[7] + 0.1, "riser", 0.4, "riser into the first price"),
    ("g-price", lambda W, E_, D: W[7] + 0.1, "impact-bass-1", 0.16, "RM441,720 lands (the payoff)"),
    ("g-price", lambda W, E_, D: W[9] + 0.02, "click-soft", 0.55, "row SEMI-D"),
    ("g-price", lambda W, E_, D: W[15] + 0.05, "pop", 0.5, "RM516,420 lands"),
    ("g-price", lambda W, E_, D: W[15] + 0.12, "sparkle", 0.12, "price glint"),
    # cta: montage, then the end card
    ("g-cta", lambda W, E_, D: W[5] + 0.02, "click-soft", 0.5, "LEBIH DEKAT? focus brackets"),
    ("g-cta", lambda W, E_, D: (CTA_B - SC["g-cta"][2]) - 0.08, "whoosh", 0.28, "iris opens onto the end card"),
    ("g-cta", lambda W, E_, D: (CTA_B - SC["g-cta"][2]) + 0.12, "pop", 0.45, "avatar ring"),
    ("g-cta", lambda W, E_, D: W[7] + 0.1, "pop", 0.5, "WhatsApp button"),
    ("g-cta", lambda W, E_, D: W[7] + 0.3, "keys", 0.3, "phone number types in"),
    ("g-cta", lambda W, E_, D: W[10] + 0.02, "click-soft", 0.55, "project block"),
    ("g-cta", lambda W, E_, D: W[12] + 0.05, "pop", 0.4, "pills"),
    ("g-cta", lambda W, E_, D: E_[18] + 0.25, "pen-draw", 0.25, "outro: house outline drafts"),
    ("g-cta", lambda W, E_, D: E_[18] + 0.72, "sparkle", 0.14, "outro: glint on the WhatsApp button"),
]
SFX = []
for scene, fn, f, vol, note in SFX_SPEC:
    W, Ee, D = local_words(scene)
    SFX.append((SC[scene][2] + fn(W, Ee, D), f, vol, note))
TRANS_SFX = {"flash": ("whoosh", 0.3, -0.16), "scan": ("scan", 0.45, -0.18), "whip": ("whip", 0.42, -0.1), "shutter": ("shutter", 0.5, 0.0)}
whips = 0
for sh in SHOTS:
    if sh["in"] in TRANS_SFX and sh["seam"] > 0.05:
        f, vol, off = TRANS_SFX[sh["in"]]
        if f == "whip":
            whips += 1
            if whips % 2 == 0:
                f, vol = "whoosh", 0.3   # alternate two takes of the repeated sound
        SFX.append((sh["seam"] + off + (HIT[f] if f != "whoosh" else 0.0), f, vol, f"{sh['in']} into {sh['id']}"))
SFX.sort()

# ---------------------------------------------------------------- music: the track's ring-out ends with the film
m = E["music"]
beat = lambda x: m["bar0"] + 0.25 + 0.5 * round((x - m["bar0"] - 0.25) / 0.5)
MUSIC_IN = round(beat(m["end_at"] - TOTAL), 3)

# ---------------------------------------------------------------- index.html
BP_CSS = ("background-color: #0a2e84; background-image: "
          "linear-gradient(rgba(185, 225, 255, 0.17) 2px, transparent 2px), linear-gradient(90deg, rgba(185, 225, 255, 0.17) 2px, transparent 2px), "
          "linear-gradient(rgba(185, 225, 255, 0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(185, 225, 255, 0.07) 1px, transparent 1px); "
          "background-size: 180px 180px, 180px 180px, 36px 36px, 36px 36px; background-position: 89px 59px, 89px 59px, 17px 23px, 17px 23px;")
o = []
w = o.append
w(f"""<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Teres &amp; Semi-D 1 Tingkat, Jalan Nenas Meru</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #0a2e84; }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; }}
      .bp {{ {BP_CSS} }}
      #ground {{ position: absolute; inset: 0; }}
      #cam {{ position: absolute; inset: 0; overflow: hidden; z-index: 1; }}
      .shot {{ position: absolute; inset: 0; overflow: hidden; }}
      .rv {{ position: absolute; inset: 0; overflow: hidden; }}
      .mv {{ position: absolute; inset: 0; transform-origin: 50% 50%; }}
      .mv img {{ position: absolute; left: -740px; top: 0; width: 2560px; height: 1920px; }}
      .mv video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
      .board {{ position: absolute; inset: 0; }}
      .scrim {{ position: absolute; inset: 0; background: linear-gradient(180deg, rgba(6, 22, 54, 0.55) 0%, rgba(6, 22, 54, 0.05) 26%, rgba(6, 22, 54, 0.05) 52%, rgba(6, 22, 54, 0.62) 100%); }}
      .tag {{ position: absolute; left: 120px; top: 292px; display: flex; align-items: center; gap: 12px; padding: 8px 16px 8px 12px;
        background: rgba(6, 22, 54, 0.72); border: 2px solid rgba(185, 225, 255, 0.55); border-radius: 10px;
        font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 28px; letter-spacing: 0.06em; color: #e6f2ff; white-space: nowrap; }}
      .tag i {{ display: block; width: 14px; height: 14px; border-radius: 50%; background: #5cc2ff; box-shadow: 0 0 0 5px rgba(92, 194, 255, 0.25); }}
      #vig {{ position: absolute; inset: 0; z-index: 2; pointer-events: none;
        background: radial-gradient(ellipse 80% 62% at 50% 46%, rgba(4, 16, 52, 0) 55%, rgba(4, 16, 52, 0.5) 100%); }}
      #scan {{ position: absolute; left: 0; top: 0; width: 1080px; height: 0; z-index: 29; opacity: 0; }}
      #scan-line {{ position: absolute; left: 0; top: -3px; width: 1080px; height: 6px; background: #e6f2ff;
        box-shadow: 0 0 18px 6px rgba(92, 194, 255, 0.9), 0 0 60px 20px rgba(29, 92, 255, 0.55); }}
      #scan-band {{ position: absolute; left: 0; top: -150px; width: 1080px; height: 150px;
        background: linear-gradient(180deg, rgba(92, 194, 255, 0) 0%, rgba(92, 194, 255, 0.22) 100%); }}
      #flash {{ position: absolute; inset: 0; z-index: 30; background: #f2f8ff; opacity: 0; pointer-events: none; }}
      #deco {{ position: absolute; inset: 0; z-index: 25; pointer-events: none; }}
      .cm {{ position: absolute; width: 54px; height: 54px; border-color: rgba(230, 242, 255, 0.75); border-style: solid; border-width: 0; }}
      .cm.tl {{ left: 56px; top: 176px; border-left-width: 4px; border-top-width: 4px; }}
      .cm.tr {{ right: 56px; top: 176px; border-right-width: 4px; border-top-width: 4px; }}
      .cm.bl {{ left: 56px; bottom: 176px; border-left-width: 4px; border-bottom-width: 4px; }}
      .cm.br {{ right: 56px; bottom: 176px; border-right-width: 4px; border-bottom-width: 4px; }}
      #coord {{ position: absolute; left: 124px; bottom: 182px; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 20px;
        letter-spacing: 0.08em; color: rgba(230, 242, 255, 0.7); white-space: nowrap; }}
      .scene {{ position: absolute; inset: 0; pointer-events: none; }}
    </style>
  </head>
  <body>""")
w(f'    <div id="root" data-composition-id="main" data-start="0" data-duration="{r3(TOTAL)}" data-width="1080" data-height="1920" data-motion-blur="on">')
w('      <div id="ground" class="bp"></div>')
w("")
w("      <!-- PICTURE: the developer's render, real site photos, the blueprint board and the baked map; each shot enters its own way -->")
w('      <div id="cam">')
for i, sh in enumerate(SHOTS):
    z = i + 1
    if sh["kind"] == "video":
        w(f'        <div id="sh-{sh["id"]}" class="shot" style="z-index: {z}"><div id="rv-{sh["id"]}" class="rv"><div id="mv-{sh["id"]}" class="mv">'
          f'<video id="v-{sh["id"]}" class="clip" src="{sh["src"]}" muted playsinline data-start="{r3(sh["start"])}" data-duration="{r3(sh["end"] - sh["start"])}" data-media-start="0" data-track-index="1"></video></div></div></div>')
        continue
    inner = (f'<div id="mv-{sh["id"]}" class="mv"><img src="{sh["src"]}" alt="" /></div><div class="scrim"></div>' if sh["kind"] == "img"
             else '<div class="board bp"></div>')
    label = f'<div class="tag"><i></i>{html.escape(sh["label"])}</div>' if sh.get("label") else ""
    w(f'        <div id="sh-{sh["id"]}" class="clip shot" data-start="{r3(sh["start"])}" data-duration="{r3(sh["end"] - sh["start"])}" data-track-index="1" style="z-index: {z}">'
      f'<div id="rv-{sh["id"]}" class="rv">{inner}{label}</div></div>')
w("      </div>")
w('      <div id="vig"></div>')
w('      <div id="scan"><div id="scan-band"></div><div id="scan-line"></div></div>')
w('      <div id="flash"></div>')
w('      <div id="deco" data-layout-ignore><div class="cm tl"></div><div class="cm tr"></div><div class="cm bl"></div><div class="cm br"></div>'
  '<div id="coord">3.1416°N · 101.4117°E · JALAN NENAS, MERU</div></div>')
w("")
w(f"      <!-- VOICE: the owner's cloned voice \"{L.get('voice_name', '')}\" (ElevenLabs {L['model_id']}), tempo {T}, -16 LUFS -->")
for k in LINE_IDS:
    parts = VO[k]["parts"]
    for j, p in enumerate(parts):
        suffix = "" if len(parts) == 1 else f"-{'ab'[j]}"
        w(f'      <audio id="vo-{k}{suffix}" class="clip" src="assets/audio/vo-{k}.wav" data-start="{r3(p["start"])}" data-duration="{r3(p["media_out"] - p["media_in"])}" data-media-start="{r3(p["media_in"])}" data-volume="1" data-fade-in="0.01" data-fade-out="0.03" data-track-index="2"></audio>')
w("")
first_word = VO[LINE_IDS[0]]["words"][0][1]
pts = [(0, m["lift"]), (round(first_word - 0.08, 2), m["lift"]), (round(first_word + 0.12, 2), m["base"]),
       (round(VO_END, 2), m["base"]), (round(VO_END + 0.4, 2), m["end"])]
auto = {"version": 1, "lanes": [{"target": "volume", "points": [{"t": t, "v": v} for t, v in pts]}]}
w("      <!-- MUSIC: made for this video with ElevenLabs Music (120 BPM); its ring-out ends with the film -->")
w(f'      <audio id="music" class="clip" src="{m["src"]}" data-start="0" data-duration="{r3(TOTAL)}" data-media-start="{r3(MUSIC_IN)}" data-volume="1" data-fade-in="0.05" data-fade-out="1.0" data-automation="{html.escape(json.dumps(auto, separators=(",", ":")))}" data-track-index="5"></audio>')
w("")
w("      <!-- SOUND EFFECTS: each lands one frame after the thing it belongs to -->")
lane_end = {3: -1.0, 4: -1.0, 8: -1.0}
for i, (t, f, vol, note) in enumerate(SFX):
    st = max(0, t + FRAME - HIT[f])
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
groups.sort(key=lambda g: g["toks"][0][1])
for g in groups:
    ws = VO[g["line"]]["words"]
    nxt = [x for x in groups if x["line"] == g["line"] and x["first"] > g["first"]]
    last_spoken = (min(x["first"] for x in nxt) - 1) if nxt else g["last"]
    g["st"] = g["toks"][0][1] - 0.05
    g["en"] = ws[last_spoken][2] + 0.18
    # a caption never runs into the next scene
    sc_end = SC[SCENE_OF[g["line"]]][3]
    g["en"] = min(g["en"], sc_end - 0.05)
for i in range(len(groups) - 1):
    if groups[i]["en"] > groups[i + 1]["st"] - 0.02:
        groups[i]["en"] = groups[i + 1]["st"] - 0.02
CAP_START = groups[0]["st"] - 0.01
CAP_END = groups[-1]["en"] + 0.01
w(f'      <div id="captions" class="scene" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="{r3(CAP_START)}" data-duration="{r3(CAP_END - CAP_START)}" data-track-index="9" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index: 20"></div>')
w("    </div>")
w("""    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      // resting states for the overlays that several transitions share
      tl.set("#flash", { opacity: 0 }, 0);
      tl.set("#scan", { opacity: 0 }, 0);
      // each photo pans slowly across the room (the photos are 4:3; the frame is 9:16)""")
for sh in SHOTS:
    if sh["kind"] == "img":
        w(f'      tl.fromTo("#mv-{sh["id"]}", {{ x: {sh["x0"]}, scale: {sh["s0"]} }}, {{ x: {sh["x1"]}, scale: {sh["s1"]}, duration: {r3(sh["end"] - sh["start"])}, ease: "sine.inOut", immediateRender: false }}, {r3(sh["start"])});')
w("      // transitions: flash (a hit), scan (the blueprint scanner line), whip (a fast pan), shutter (a camera click), punch (a hard cut closer)")
for i, sh in enumerate(SHOTS):
    t, kind = sh["seam"], sh["in"]
    prev = SHOTS[i - 1] if i else None
    if kind == "flash":
        w(f'      tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 0.92, duration: 0.05, ease: "none", immediateRender: false }}, {r3(t - 0.05)});')
        w(f'      tl.to("#flash", {{ opacity: 0, duration: 0.3, ease: "power2.out" }}, {r3(t)});')
    elif kind == "shutter":
        w(f'      tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.033, ease: "none", immediateRender: false }}, {r3(t - 0.033)});')
        w(f'      tl.to("#flash", {{ opacity: 0, duration: 0.14, ease: "power2.out" }}, {r3(t)});')
    elif kind == "scan":
        s0 = sh["start"]
        w(f'      tl.fromTo("#rv-{sh["id"]}", {{ clipPath: "inset(0px 0px 1920px 0px)" }}, {{ clipPath: "inset(0px 0px 0px 0px)", duration: 0.46, ease: "power2.inOut", immediateRender: false }}, {r3(s0)});')
        w(f'      tl.fromTo("#scan", {{ y: 0, opacity: 1 }}, {{ y: 1920, opacity: 1, duration: 0.46, ease: "power2.inOut", immediateRender: false }}, {r3(s0)});')
        w(f'      tl.set("#scan", {{ opacity: 0 }}, {r3(s0 + 0.47)});')
    elif kind == "whip":
        s0 = sh["start"]
        if prev:
            w(f'      tl.fromTo("#rv-{prev["id"]}", {{ x: 0 }}, {{ x: -1180, duration: 0.24, ease: "power3.in", immediateRender: false }}, {r3(s0)});')
        w(f'      tl.fromTo("#rv-{sh["id"]}", {{ x: 1180 }}, {{ x: 0, duration: 0.3, ease: "power3.out", immediateRender: false }}, {r3(s0 + 0.08)});')
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
    .cg { position: absolute; left: 120px; top: 1152px; width: 660px; height: 90px; }
    .cg-in { position: absolute; left: 0; right: 0; top: 0; text-align: center; white-space: nowrap; overflow: visible;
      font-family: "Archivo Black", sans-serif; font-size: 52px; line-height: 1.2; letter-spacing: 0;
      color: #ffffff; -webkit-text-stroke: 12px rgba(6, 22, 54, 0.95); paint-order: stroke fill;
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
    extra = f" const PB = {r3(CTA_B - st)};" if sid == "g-cta" else ""
    block = (f"/* CUES:BEGIN (generated by scripts/{NAME}/build.py from the voiceover; do not edit by hand) */\n"
             f"    // words: {' '.join(x[0] for x in VO[k]['words'])}\n"
             f"    const W = {json.dumps(W)}; // word starts (s, local to this scene)\n"
             f"    const E = {json.dumps(Ee)}; // word ends\n"
             f"    const D = {r3(D)};{extra}\n"
             f"    /* CUES:END */")
    p = os.path.join(VID, "compositions", f"{sid}.html")
    s = open(p).read() if os.path.exists(p) else None
    if s is None or not CUE_RE.search(s):
        print(f"  ! {sid}.html missing or has no CUES block; cues: W={W} D={D}")
        continue
    open(p, "w").write(CUE_RE.sub(lambda _m: block, s))

print(f"total {TOTAL}s (voice ends {VO_END:.2f}s), music from {MUSIC_IN}s, {len(SHOTS)} shots, {len(SFX)} sfx, {len(groups)} caption groups")
for sid, k, st, en in SCENES:
    print(f"  {sid:9s} {st:6.2f} -> {en:6.2f}  ({en - st:5.2f}s)")
for sh in SHOTS:
    print(f"    shot {sh['id']:10s} {sh['start']:6.2f} -> {sh['end']:6.2f}  seam {sh['seam']:6.2f}  in {sh['in']}")
