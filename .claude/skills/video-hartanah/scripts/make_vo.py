"""Generate the voiceover line by line with ElevenLabs (project.json "voice": voice_id,
model_id eleven_v3, stability), one MP3 per line in video/assets/audio/vo/.
eleven_v3 + audio tags ([serious], [excited], [urgent]...) give an expressive, non-monotone read.
Its own character timestamps (<id>.align.json) are kept but NOT used: they drift ~0.2 s.
Next: enhance_vo.py, then align_vo.py.
Auth: in Claude cloud sessions the proxy injects the key for api.elevenlabs.io; elsewhere set ELEVENLABS_API_KEY.
Usage: python3 -I .claude/skills/video-hartanah/scripts/make_vo.py <project-dir> [line_id ...]"""
import json, os, re, sys, base64, time, urllib.request, urllib.error
PROJ = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
cfg = json.load(open(os.path.join(PROJ, "project.json")))
V = cfg["voice"]
OUT = os.path.join(PROJ, "video", "assets", "audio", "vo")
os.makedirs(OUT, exist_ok=True)
spoken = lambda t: re.sub(r"\{([^|}]*)\|[^}]*\}", r"\1", t).replace("[b]", "[short pause]")
only = set(sys.argv[2:])
for ln in cfg["lines"]:
    if only and ln["id"] not in only: continue
    body = {"text": spoken(ln["text"]), "model_id": V.get("model_id", "eleven_v3"),
            "voice_settings": {"stability": V.get("stability", 0.5), "similarity_boost": V.get("similarity", 0.85), "use_speaker_boost": True}}
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{V['voice_id']}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "proxy"), "User-Agent": "curl/8.5.0"})
    for attempt in range(5):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=180)); break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4: raise
            time.sleep(3 * (attempt + 1))
    open(os.path.join(OUT, f"{ln['id']}.mp3"), "wb").write(base64.b64decode(d["audio_base64"]))
    json.dump(d["alignment"], open(os.path.join(OUT, f"{ln['id']}.align.json"), "w"))
    print(ln["id"], "ok", round(d["alignment"]["character_end_times_seconds"][-1], 2), "s", flush=True)
