"""Music bed + the generated sound effects, with ElevenLabs.

  make_audio.py <project-dir> sfx     boom, kaching, riser, stamp, pin -> video/assets/sfx/ (skips files that exist)
  make_audio.py <project-dir> music   one music bed sized to the edit -> video/assets/audio/music-bed.mp3

Run "music" after build.py has run once (it reads the edit length from video/index.html and the
music start anchor from project.json "music.start"), then run build.py again.
project.json "music.prompt" overrides the default prompt (instrumental, serious, premium real estate).
ElevenLabs tracks often end a few seconds early and go silent: check the printed tail; if the
music stops before the end card, use extend_music.py.
Auth: proxy-injected in Claude cloud sessions; elsewhere set ELEVENLABS_API_KEY.
"""
import json, os, re, subprocess, sys, urllib.request
import numpy as np

PROJ = os.path.abspath(sys.argv[1]); what = sys.argv[2]
P = json.load(open(os.path.join(PROJ, "project.json")))
VID = os.path.join(PROJ, "video")
KEY = os.environ.get("ELEVENLABS_API_KEY", "proxy")

def post(path, body, out):
    req = urllib.request.Request("https://api.elevenlabs.io" + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "xi-api-key": KEY, "User-Agent": "curl/8.5.0"})
    open(out, "wb").write(urllib.request.urlopen(req, timeout=600).read())

if what == "sfx":
    SFX = {"boom": ("deep cinematic sub boom impact hit, trailer style, clean, no music", 2.5),
           "kaching": ("cash register ka-ching, single clean coin chime", 1.5),
           "riser": ("short tense cinematic riser whoosh building up, 1.5 seconds", 1.8),
           "stamp": ("heavy rubber stamp slam on paper, single hit", 1.0),
           "pin": ("digital map pin drop, soft ui blip with low thump", 1.0)}
    d = os.path.join(VID, "assets", "sfx"); os.makedirs(d, exist_ok=True)
    for name, (prompt, dur) in SFX.items():
        f = os.path.join(d, f"{name}.mp3")
        if os.path.exists(f):
            print(name, "exists"); continue
        post("/v1/sound-generation", {"text": prompt, "duration_seconds": dur, "prompt_influence": 0.6}, f)
        if name == "pin":   # generated quiet (about -22 dBFS peak): bring it up
            tmp = f + ".tmp.mp3"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-af", "volume=14dB,alimiter=limit=0.9", tmp], check=True)
            os.replace(tmp, f)
        print(name, "ok")
    with open(os.path.join(d, "CREDITS.md"), "a") as fh:
        fh.write("\n\nboom, kaching, riser, stamp, pin: generated with ElevenLabs Sound Effects for this project.\n")

elif what == "music":
    idx = open(os.path.join(VID, "index.html")).read()
    total = float(re.search(r'data-composition-id="main" data-start="0" data-duration="([\d.]+)"', idx).group(1))
    timing = json.load(open(os.path.join(VID, "vo_timing.json")))
    M = P.get("music", {})
    start = 0.0
    if M.get("start"):
        m = re.fullmatch(r"([^:@]+)(?::(.+?))?(?:#(\d+))?(?:@([+-]?\d*\.?\d+))?", M["start"])
        lid, word, n, off = m.group(1), m.group(2), int(m.group(3) or 0), float(m.group(4) or 0)
        norm = lambda s: re.sub(r"[^\w-]", "", s).lower()
        start = (timing[lid]["start"] if word is None else [w for w in timing[lid]["words"] if norm(w["t"]) == norm(word)][n]["s"]) + off
    length = total - start + 1.0
    prompt = M.get("prompt", "Instrumental only, no vocals. Serious confident cinematic hip-hop beat for a premium real estate promo video. "
                     "90 BPM, dark minimal piano motif, deep 808 sub bass, crisp hats, subtle string pad, steady tension with a lift in the "
                     "second half and a clean ending. Mood: determined, trustworthy, urgent.")
    out = os.path.join(VID, "assets", "audio", "music-bed.mp3"); os.makedirs(os.path.dirname(out), exist_ok=True)
    post("/v1/music", {"prompt": prompt, "music_length_ms": int(length * 1000)}, out)
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                                     capture_output=True).stdout, dtype=np.int16).astype(float) / 32768
    rms = [20 * np.log10(np.sqrt(np.mean(a[i:i + 8000] ** 2)) + 1e-9) for i in range(0, len(a) - 8000, 8000)]
    last = max(i for i, v in enumerate(rms) if v > -40) + 1
    print(f"music-bed.mp3: requested {length:.1f}s from {start:.2f}s; audible until {last}s of the file "
          f"(edit end needs {total - start:.1f}s)")
    if last < total - start - 1.5:
        print(f"  -> music ends {total - start - last:.1f}s before the edit: run extend_music.py {PROJ} {total - start - last + 1:.0f}")
    print("Set project.json music.length to", last, "and run build.py again.")
