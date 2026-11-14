"""Generate the voiceover line by line with ElevenLabs (voice "Mad Serious"),
keeping character timestamps for captions and graphics cues.
Usage: python3 -I pulau-indah/scripts/make_vo.py [line_id ...]"""
import json, os, re, sys, base64, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "video", "assets", "audio", "vo")
cfg = json.load(open(os.path.join(HERE, "vo_script.json")))
spoken = lambda t: re.sub(r"\{([^|}]*)\|[^}]*\}", r"\1", t).replace("[b]", '<break time="0.35s" />')
lines = cfg["lines"]; only = set(sys.argv[1:])
for i, ln in enumerate(lines):
    if only and ln["id"] not in only: continue
    body = {"text": spoken(ln["text"]), "model_id": cfg["model_id"],
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.85, "style": 0.15, "use_speaker_boost": True, "speed": 1.1}}
    if i > 0: body["previous_text"] = spoken(lines[i-1]["text"]).replace('<break time="0.35s" />', "")
    if i + 1 < len(lines): body["next_text"] = spoken(lines[i+1]["text"]).replace('<break time="0.35s" />', "")
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice_id']}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "xi-api-key": "proxy", "User-Agent": "curl/8.5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=120))
    open(os.path.join(OUT, f"{ln['id']}.mp3"), "wb").write(base64.b64decode(d["audio_base64"]))
    json.dump(d["alignment"], open(os.path.join(OUT, f"{ln['id']}.align.json"), "w"))
    print(ln["id"], "ok", round(d["alignment"]["character_end_times_seconds"][-1], 2), "s")
