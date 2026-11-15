"""Generate the pipit/ voiceover with ElevenLabs in one take, with character timestamps.

    python3 -I scripts/pipit/voiceover.py OUT_DIR [--model eleven_v3|eleven_multilingual_v2] [--stability S]
           [--style S] [--speed S] [--seed N]

Writes OUT_DIR/take.mp3, OUT_DIR/take.json (ElevenLabs alignment) and OUT_DIR/lines.json
(start/end of each scene's line in the take, in seconds). The API key is injected by the session
proxy (the header value here is a placeholder). The script text lives in LINES below and in
pipit/VOICEOVER.md.
"""
import argparse, base64, json, re, subprocess, sys
from pathlib import Path

VOICE = "graVYRgsElnbev50WXQ2"  # "Suara sendiri (videohartanah)": the owner's cloned voice

LINES = [
    ("s1-hook", "[excited] Rumah berkembar setingkat, kat Telok Panglima Garang... dah buka pendaftaran!"),
    ("s2-unit", "[playfully] Tapi jangan tunggu lama, lapan unit je tau!"),
    ("s3-pakej", "[cheerful] Booking? Seribu ringgit je. Legal fee S P A, free. Disbursement, free. Rumah pertama? M O T pun free!"),
    ("s4-pelan", "[confident] Empat bilik, dua bilik air. Tanah, dua ribu lapan ratus empat belas kaki persegi. Binaan, seribu dua ratus enam puluh enam."),
    ("s5-tapak", "Leasehold, Rizab Melayu. Dijangka siap hujung tahun dua ribu dua puluh tujuh."),
    ("s6-peta", "[excited] Nak ke Shah Alam? Dua puluh tiga minit. K L C C, empat puluh dua minit. S K V E, KESAS, W C E, semua dekat."),
    ("s7-dekat", "Sekolah? Lima minit je. Ninety-nine Speedmart, enam minit. Eco Sanctuary, sembilan minit."),
    ("s8-cta", "[warmly] Harga dari empat ratus lapan puluh lima ribu tujuh ratus. Booking seribu je... [excited] jom, hubungi saya sekarang!"),
]

TAG = re.compile(r"\[[a-z ]+\]\s*")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--model", default="eleven_v3")
    ap.add_argument("--stability", type=float, default=0.5)
    ap.add_argument("--style", type=float, default=0.0)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--only", help="comma-separated line ids to voice (default: all)")
    ap.add_argument("--tail", default="", help="throwaway words after the last line, cut off later: v3 can "
                    "truncate the final word of a request, so the line that matters is never the last thing said")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    tags = a.model == "eleven_v3"
    chosen = [(sid, t) for sid, t in LINES if not a.only or sid in a.only.split(",")]
    texts = [t if tags else TAG.sub("", t) for _, t in chosen]
    text = "  ".join(texts)
    spans, pos = [], 0
    for (sid, _), t in zip(chosen, texts):
        spans.append((sid, pos, pos + len(t)))
        pos += len(t) + 2
    if a.tail:
        text += "  " + a.tail

    settings = {"stability": a.stability, "similarity_boost": 0.8, "use_speaker_boost": True}
    if not tags:
        settings.update(style=a.style, speed=a.speed)
    body = {"text": text, "model_id": a.model, "language_code": "ms", "voice_settings": settings, "seed": a.seed}
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128"
    r = subprocess.run(["curl", "-sS", "--fail-with-body", "-X", "POST", url, "-H", "xi-api-key: placeholder",
                        "-H", "Content-Type: application/json", "-d", json.dumps(body)], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ElevenLabs refused: {r.stdout[:600]} {r.stderr[:300]}")
    d = json.loads(r.stdout)
    (out / "take.mp3").write_bytes(base64.b64decode(d["audio_base64"]))
    al = d.get("alignment") or d.get("normalized_alignment")
    (out / "take.json").write_text(json.dumps({"text": text, "alignment": al}, ensure_ascii=False))

    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    aligned = "".join(chars)
    lines = []
    for sid, s, e in spans:
        # first and last spoken (non-tag, non-space) characters of the line
        seg = text[s:e]
        m = [i for i, ch in enumerate(seg) if not ch.isspace()]
        tagged = [range(x.start(), x.end()) for x in TAG.finditer(seg)]
        m = [i for i in m if not any(i in rg for rg in tagged)]
        i0, i1 = s + m[0], s + m[-1]
        if aligned != text:  # alignment text differs: fall back to proportional mapping
            i0 = round(i0 * len(aligned) / len(text))
            i1 = min(len(aligned) - 1, round(i1 * len(aligned) / len(text)))
        lines.append({"id": sid, "start": round(st[i0], 3), "end": round(en[i1], 3), "text": TAG.sub("", text[s:e])})
    (out / "lines.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1))
    for l in lines:
        print(f"{l['id']:9s} {l['start']:6.2f} - {l['end']:6.2f}  ({l['end'] - l['start']:4.2f}s)  {l['text']}")
    print("aligned text matches request:", aligned == text)


if __name__ == "__main__":
    main()
