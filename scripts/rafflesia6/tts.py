"""Generate the voiceover, one file per line, with the owner's cloned ElevenLabs voice (eleven_v3 + an audio tag per line).

v3 takes vary: generate a few and keep the one whose words come out right (see vo_lines.json \"_takes\").

Writes rafflesia6/assets/audio/vo-<id>.mp3 and scripts/rafflesia6/vo_align.json
(character timings per line, from the with-timestamps endpoint).
Usage: python3 -I scripts/rafflesia6/tts.py [line_id ...]   (no ids = all lines)
The proxy injects the ElevenLabs key; the header value here is a placeholder.
"""
import json, sys, base64, os, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
cfg = json.load(open(os.path.join(HERE, "vo_lines.json")))
out_dir = os.path.join(ROOT, "rafflesia6", "assets", "audio")
align_path = os.path.join(HERE, "vo_align.json")
align = json.load(open(align_path)) if os.path.exists(align_path) else {}
want = set(sys.argv[1:])
lines = cfg["lines"]
for i, ln in enumerate(lines):
    if want and ln["id"] not in want:
        continue
    body = {
        "text": (ln.get("tag", "") + " " + ln["say"]).strip(),
        "model_id": cfg["model_id"],
        "voice_settings": cfg["voice_settings"],
        "language_code": "ms",
        "previous_text": lines[i - 1]["say"] if i > 0 else None,
        "next_text": lines[i + 1]["say"] if i + 1 < len(lines) else None,
    }
    if cfg["model_id"] != "eleven_turbo_v2_5" and cfg["model_id"] != "eleven_flash_v2_5":
        body.pop("language_code")
    if cfg["model_id"] == "eleven_v3":  # v3 reads the audio tag ([excited] ...) and takes no previous/next text
        body.pop("previous_text"); body.pop("next_text")
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice_id']}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), headers={"xi-api-key": "placeholder", "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    path = os.path.join(out_dir, f"vo-{ln['id']}.raw.mp3")
    open(path, "wb").write(base64.b64decode(r["audio_base64"]))
    align[ln["id"]] = r.get("alignment")
    print("ok", ln["id"], path, flush=True)
json.dump(align, open(align_path, "w"), ensure_ascii=False)
