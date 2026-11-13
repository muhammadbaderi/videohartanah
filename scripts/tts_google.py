#!/usr/bin/env python3
"""Generate the voiceovers for a copywriting file with Google Cloud Text-to-Speech.

The API key is never read here: the session's network proxy adds the
X-Goog-Api-Key header to requests for texttospeech.googleapis.com.

    python3 -I scripts/tts_google.py voices                     # list ms-MY voices
    python3 -I scripts/tts_google.py sample "teks" out.mp3 --voice ms-MY-Wavenet-B
    python3 -I scripts/tts_google.py build copywriting/taman-tok-muda-jaya/skrip.json \
        --voice ms-MY-Wavenet-B --out copywriting/taman-tok-muda-jaya/vo
"""
import argparse
import base64
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

import requests

API = "https://texttospeech.googleapis.com/v1"

# Written form -> spoken Malay. Applied in order, after XML escaping, so the
# replacements may hold SSML. Every digit in a script must be covered here:
# build() stops if one is left, so a number is never read the wrong way.
SPOKEN = [
    ("RM345,000", "tiga ratus empat puluh lima ribu ringgit"),
    ("RM345 ribu", "tiga ratus empat puluh lima ribu ringgit"),
    ("RM200", "dua ratus ringgit"),
    ("016-370 8908", 'kosong satu enam, <break time="150ms"/>tiga tujuh kosong, '
                     '<break time="150ms"/>lapan sembilan kosong lapan'),
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

ACRONYMS = ["SPA", "SMK", "SRA", "SK", "KIIP", "ECRL", "WCE", "NKVE"]

# English words Malaysians say in English. With --english they are read by an
# en-US voice inside the Malay sentence (SSML <lang>).
ENGLISH = ["downpayment", "legal fee", "Free legal fee", "free", "booking", "Booking",
           "best", "Last-last", "Stop", "drive", "parking", "baby", "Federal Highway"]

PAUSE_ELLIPSIS = '<break time="350ms"/>'
PAUSE_SECTION = '<break time="650ms"/>'


def to_ssml(parts, english=False):
    out = []
    for text in parts:
        s = escape(text, {"'": "&apos;", '"': "&quot;"})
        for written, spoken in SPOKEN:
            s = s.replace(escape(written), spoken)
        for ac in ACRONYMS:
            s = re.sub(rf"\b{ac}\b", f'<say-as interpret-as="characters">{ac}</say-as>', s)
        if english:
            for w in sorted(ENGLISH, key=len, reverse=True):
                s = re.sub(rf"(?<![\w>]){re.escape(w)}(?![\w<])",
                           f'<lang xml:lang="en-US">{w}</lang>', s)
        s = s.replace("...", PAUSE_ELLIPSIS)
        left = re.sub(r"<[^>]+>", "", s)
        if re.search(r"\d", left):
            sys.exit(f"Digit left unspoken, add it to SPOKEN: {left!r}")
        out.append(s)
    return "<speak>" + PAUSE_SECTION.join(out) + "</speak>"


def synthesize(ssml, voice, rate, wav_path):
    lang = "-".join(voice.split("-")[:2])
    body = {
        "input": {"ssml": ssml},
        "voice": {"languageCode": lang, "name": voice},
        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000,
                        "speakingRate": rate},
    }
    r = requests.post(f"{API}/text:synthesize", json=body, timeout=120)
    if r.status_code != 200:
        sys.exit(f"TTS error {r.status_code}: {r.text[:500]}")
    Path(wav_path).write_bytes(base64.b64decode(r.json()["audioContent"]))


def finish(raw_wav, out_base):
    """Loudness -16 LUFS / -1.5 dBTP (same as the Meru edit), then wav + mp3."""
    wav, mp3 = f"{out_base}.wav", f"{out_base}.mp3"
    af = "loudnorm=I=-16:TP=-1.5:LRA=11"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw_wav, "-af", af,
                    "-ar", "48000", "-ac", "1", wav], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-codec:a", "libmp3lame",
                    "-b:a", "160k", mp3], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", mp3], capture_output=True, text=True, check=True)
    return float(dur.stdout.strip())


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def cmd_voices(_):
    r = requests.get(f"{API}/voices", params={"languageCode": "ms-MY"}, timeout=60)
    if r.status_code != 200:
        sys.exit(f"Error {r.status_code}: {r.text[:500]}")
    for v in r.json().get("voices", []):
        print(v["name"], v["ssmlGender"], v["naturalSampleRateHertz"])


def cmd_sample(a):
    with tempfile.TemporaryDirectory() as tmp:
        raw = f"{tmp}/raw.wav"
        synthesize(to_ssml([a.text], a.english), a.voice, a.rate, raw)
        print(f"{finish(raw, a.out.removesuffix('.mp3')):.1f}s")


def cmd_build(a):
    data = json.loads(Path(a.json).read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for s in data["skrip"]:
            if a.only and s["no"] not in a.only:
                continue
            ssml = to_ssml([s["hook"], s["cerita"], s["cta"]], a.english)
            raw = f"{tmp}/raw-{s['no']}.wav"
            synthesize(ssml, a.voice, a.rate, raw)
            base = out / f"vo-{s['no']:02d}-{slug(s['tajuk'])}"
            dur = finish(raw, base)
            results.append({"no": s["no"], "tajuk": s["tajuk"], "fail": base.name + ".mp3",
                            "durasi_saat": round(dur, 1)})
            print(f"{s['no']}. {s['tajuk']}: {dur:.1f}s")
    meta = {"suara": a.voice, "kelajuan": a.rate, "english_lang_tags": a.english, "vo": results}
    (out / "vo.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("voices").set_defaults(fn=cmd_voices)
    for name, fn in (("sample", cmd_sample), ("build", cmd_build)):
        sp = sub.add_parser(name)
        if name == "sample":
            sp.add_argument("text")
            sp.add_argument("out")
        else:
            sp.add_argument("json")
            sp.add_argument("--out", required=True)
            sp.add_argument("--only", type=int, nargs="*")
        sp.add_argument("--voice", default="ms-MY-Wavenet-B")
        sp.add_argument("--rate", type=float, default=1.0)
        sp.add_argument("--english", action="store_true",
                        help="read English loanwords with an en-US voice")
        sp.set_defaults(fn=fn)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
