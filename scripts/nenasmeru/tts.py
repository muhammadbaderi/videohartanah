"""Generate voiceover takes with ElevenLabs (the voice, model and settings in vo_lines.json).

  python3 -I scripts/<name>/tts.py [--takes N] [line_id ...]     (no ids = all lines)

Each take goes to .media-src/<name>/vo-takes/take<k>/vo-<id>.mp3 with its character timings in
.media-src/<name>/vo-takes/take<k>/align.json. eleven_v3 takes vary from one call to the next, so make
a few (--takes 3) and let pick_takes.py keep the best one of each line.
The proxy injects the ElevenLabs key; the header value here is a placeholder.
"""
import json, sys, base64, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
cfg = json.load(open(os.path.join(HERE, "vo_lines.json")))
args = sys.argv[1:]
takes = 1
if "--takes" in args:
    i = args.index("--takes"); takes = int(args[i + 1]); del args[i:i + 2]
want = set(args)
lines = cfg["lines"]
for k in range(1, takes + 1):
    out = os.path.join(ROOT, ".media-src", os.path.basename(HERE), "vo-takes", f"take{k}")
    os.makedirs(out, exist_ok=True)
    apath = os.path.join(out, "align.json")
    align = json.load(open(apath)) if os.path.exists(apath) else {}
    for i, ln in enumerate(lines):
        if want and ln["id"] not in want:
            continue
        body = {"text": (ln.get("tag", "") + " " + ln["say"]).strip(), "model_id": cfg["model_id"],
                "voice_settings": cfg["voice_settings"]}
        if cfg["model_id"] != "eleven_v3":  # v2 models: no audio tags, but they take the neighbouring lines as context
            body["text"] = ln["say"]
            body["previous_text"] = lines[i - 1]["say"] if i > 0 else None
            body["next_text"] = lines[i + 1]["say"] if i + 1 < len(lines) else None
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice_id']}/with-timestamps?output_format=mp3_44100_128",
            data=json.dumps(body).encode(), headers={"xi-api-key": "placeholder", "Content-Type": "application/json"})
        r = json.load(urllib.request.urlopen(req, timeout=180))
        open(os.path.join(out, f"vo-{ln['id']}.mp3"), "wb").write(base64.b64decode(r["audio_base64"]))
        align[ln["id"]] = r.get("alignment")
        print(f"take{k}", ln["id"], flush=True)
    json.dump(align, open(apath, "w"), ensure_ascii=False)
