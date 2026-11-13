#!/usr/bin/env python3
"""Generate the voiceovers for a copywriting file with ElevenLabs.

The API key is never read here: the session's network proxy adds the
xi-api-key header to requests for api.elevenlabs.io.

    python3 -I scripts/tts_elevenlabs.py sample "teks" out.mp3 --voice <voice_id>
    python3 -I scripts/tts_elevenlabs.py build copywriting/taman-tok-muda-jaya/skrip.json \
        --voice <voice_id> --out copywriting/taman-tok-muda-jaya/vo
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

API = "https://api.elevenlabs.io/v1"
MODEL = "eleven_multilingual_v2"
# eleven_v3 is more expressive and reads audio tags such as [excited], but has
# no <break> tag (a pause is written as "...") and takes stability 0.0, 0.5 or 1.0.
V3 = "eleven_v3"

# Written form -> spoken Malay, applied in order. Every digit must be covered:
# build() stops if one is left, so a price or the phone number is never misread.
SPOKEN = [
    ("RM345,000", "tiga ratus empat puluh lima ribu ringgit"),
    ("RM345 ribu", "tiga ratus empat puluh lima ribu ringgit"),
    ("RM200", "dua ratus ringgit"),
    ("016-370 8908", "kosong satu enam... tiga tujuh kosong... lapan sembilan kosong lapan"),
    ("10%", "sepuluh peratus"),
    ("0%", "kosong peratus"),
    ("1,280", "seribu dua ratus lapan puluh"),
    ("934", "sembilan ratus tiga puluh empat"),
    ("2027", "dua ribu dua puluh tujuh"),
    ("6.45 pagi", "enam empat puluh lima pagi"),
    ("20 kali 64", "dua puluh kali enam puluh empat"),
    ("64 unit", "enam puluh empat unit"),
    ("34 ribu", "tiga puluh empat ribu"),
    ("11 kaki", "sebelas kaki"),
    ("15 minit", "lima belas minit"),
    ("24 minit", "dua puluh empat minit"),
    ("30 minit", "tiga puluh minit"),
    ("10 kilometer", "sepuluh kilometer"),
]

# Read letter by letter.
ACRONYMS = ["SPA", "SMK", "SRA", "SK", "KIIP", "ECRL", "WCE", "NKVE"]

SECTION_BREAK = ' <break time="0.7s" /> '


def spoken(parts, model=MODEL):
    out = []
    for text in parts:
        s = text
        for written, said in SPOKEN:
            s = s.replace(written, said)
        for ac in ACRONYMS:
            s = re.sub(rf"\b{ac}\b", " ".join(ac), s)
        if re.search(r"\d", s):
            sys.exit(f"Digit left unspoken, add it to SPOKEN: {s!r}")
        out.append(s)
    return (" ... " if model == V3 else SECTION_BREAK).join(out)


def synthesize(text, voice, mp3_path, stability, style, speed, model=MODEL):
    body = {
        "text": text,
        "model_id": model,
        "voice_settings": {"stability": stability, "similarity_boost": 0.8,
                           "style": style, "use_speaker_boost": True, "speed": speed},
    }
    r = requests.post(f"{API}/text-to-speech/{voice}", params={"output_format": "mp3_44100_128"},
                      json=body, timeout=300)
    if r.status_code != 200:
        sys.exit(f"TTS error {r.status_code}: {r.text[:500]}")
    Path(mp3_path).write_bytes(r.content)


def finish(raw, out_base):
    """Loudness -16 LUFS / -1.5 dBTP (same as the Meru edit), then wav + mp3."""
    wav, mp3 = f"{out_base}.wav", f"{out_base}.mp3"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", "48000", "-ac", "1", wav], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-codec:a", "libmp3lame",
                    "-b:a", "160k", mp3], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", mp3], capture_output=True, text=True, check=True)
    return float(dur.stdout.strip())


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def cmd_sample(a):
    with tempfile.TemporaryDirectory() as tmp:
        raw = f"{tmp}/raw.mp3"
        synthesize(spoken([a.text], a.model), a.voice, raw, a.stability, a.style, a.speed, a.model)
        print(f"{finish(raw, a.out.removesuffix('.mp3')):.1f}s")


def cmd_build(a):
    data = json.loads(Path(a.json).read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    meta_path = out / "vo.json"
    old = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    results = {v["no"]: v for v in old.get("vo", [])}
    with tempfile.TemporaryDirectory() as tmp:
        for s in data["skrip"]:
            if a.only and s["no"] not in a.only:
                continue
            raw = f"{tmp}/raw-{s['no']}.mp3"
            parts = [s.get("vo_" + k, s[k]) for k in ("hook", "cerita", "cta")]
            synthesize(spoken(parts, a.model), a.voice, raw, a.stability, a.style, a.speed, a.model)
            base = out / f"vo-{s['no']:02d}-{slug(s['tajuk'])}"
            dur = finish(raw, base)
            results[s["no"]] = {"no": s["no"], "tajuk": s["tajuk"], "fail": base.name + ".mp3",
                                "durasi_saat": round(dur, 1)}
            print(f"{s['no']}. {s['tajuk']}: {dur:.1f}s")
    meta = {"enjin": "ElevenLabs", "model": a.model, "suara": a.voice_name or a.voice,
            "voice_id": a.voice, "tetapan": {"stability": a.stability, "style": a.style,
                                             "speed": a.speed},
            "vo": [results[k] for k in sorted(results)]}
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("sample", cmd_sample), ("build", cmd_build)):
        sp = sub.add_parser(name)
        if name == "sample":
            sp.add_argument("text")
            sp.add_argument("out")
        else:
            sp.add_argument("json")
            sp.add_argument("--out", required=True)
            sp.add_argument("--only", type=int, nargs="*")
            sp.add_argument("--voice-name", default="")
        sp.add_argument("--voice", required=True, help="ElevenLabs voice_id")
        sp.add_argument("--model", default=MODEL, help=f"{MODEL} (default) or {V3}")
        sp.add_argument("--stability", type=float, default=0.45)
        sp.add_argument("--style", type=float, default=0.25)
        sp.add_argument("--speed", type=float, default=1.0)
        sp.set_defaults(fn=fn)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
