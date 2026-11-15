"""Measure word timings on the final VO WAVs (eleven_v3's own timestamps are off by
~0.2 s and up to 1.7 s). Whisper large-v3 word timestamps are matched to the script
words; numbers Whisper writes as digits ("RM500", "016-370-8908") are expanded to
Malay words first, and script words Whisper missed are interpolated.
Writes vo/<id>.words.json: [{"sp": spoken word, "s": start, "e": end}, ...] in script order.
Usage: python3 -I .claude/skills/video-hartanah/scripts/align_vo.py <project-dir> [line_id ...]"""
import difflib, json, os, re, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

PROJ = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
cfg = json.load(open(os.path.join(PROJ, "project.json")))
VO = os.path.join(PROJ, "video", "assets", "audio", "vo")
os.makedirs(VO, exist_ok=True)
ids = sys.argv[2:] or [l["id"] for l in cfg["lines"]]

D = "kosong satu dua tiga empat lima enam tujuh lapan sembilan".split()
def num(n):
    if n < 10: return [D[n]]
    if n < 20: return ["sepuluh"] if n == 10 else ["sebelas"] if n == 11 else [D[n - 10], "belas"]
    if n < 100: return [D[n // 10], "puluh"] + (num(n % 10) if n % 10 else [])
    if n < 1000:
        h = ["seratus"] if n // 100 == 1 else [D[n // 100], "ratus"]
        return h + (num(n % 100) if n % 100 else [])
    if n < 1000000:
        t = ["seribu"] if n // 1000 == 1 else num(n // 1000) + ["ribu"]
        return t + (num(n % 1000) if n % 1000 else [])
    return [str(n)]
def expand(tok):
    t = tok.lower().strip(".,?!")
    if re.fullmatch(r"0\d{2}-?\d{3}-?\d{4}", t):                 # phone number: digit by digit
        return [D[int(c)] for c in t if c.isdigit()]
    t = re.sub(r"^rm", "", t)
    m = re.fullmatch(r"(\d+)x(\d+)", t)
    if m: return num(int(m.group(1))) + ["kali"] + num(int(m.group(2)))
    if re.fullmatch(r"[\d,]+", t) and t.strip(","):
        return num(int(t.replace(",", "")))
    return [t]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

def script_words(text):
    t = re.sub(r"\{([^|}]*)\|[^}]*\}", r"\1", text)
    t = re.sub(r"\[[^\]]*\]", " ", t)
    return t.split()

model = WhisperModel("large-v3", device="cpu", compute_type="int8")
for lid in ids:
    ln = next(l for l in cfg["lines"] if l["id"] == lid)
    sw = script_words(ln["text"])
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(VO, f"{lid}.wav"), "-ac", "1", "-ar", "16000",
                                      "-f", "s16le", "-"], capture_output=True, check=True).stdout, dtype=np.int16).astype(np.float32) / 32768
    segs, _ = model.transcribe(a, language="ms", beam_size=5, word_timestamps=True, condition_on_previous_text=False)
    segs = list(segs)
    raw = []                                                     # whisper words; glue "RM300"+",000" and "016"+"-370"
    for s in segs:
        for w in s.words:
            t = w.word.strip()
            if raw and re.match(r"^[,\-]\d", t) and re.search(r"\d$", raw[-1][0]):
                raw[-1] = [raw[-1][0] + t, raw[-1][1], w.end]
            else:
                raw.append([t, w.start, w.end])
    hw = []                                                      # (normalised sub-token, start, end)
    for t, ws, we in raw:
        subs = [x for x in (norm(p) for e in expand(t) for p in re.split(r"[-\s]", e)) if x]
        for k, x in enumerate(subs):
            d = (we - ws) / len(subs)
            hw.append((x, ws + k * d, ws + (k + 1) * d))
    # script sub-tokens (S.K.V.E -> skve, W-C-E -> wce, Ri-zab -> rizab)
    sn = [norm(w) for w in sw]
    hn = [x for x, _, _ in hw]
    times = [None] * len(sw)
    for blk in difflib.SequenceMatcher(None, sn, hn, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = [hw[blk.b + k][1], hw[blk.b + k][2]]
    # fuzzy pass for near-misses (teres/terace, freehold/t-hall) inside unmatched gaps
    for i, t in enumerate(times):
        if t is None:
            prev_end = next((times[j][1] for j in range(i - 1, -1, -1) if times[j]), 0.0)
            next_start = next((times[j][0] for j in range(i + 1, len(sw)) if times[j]), len(a) / 16000)
            cands = [(difflib.SequenceMatcher(None, sn[i], x).ratio(), s0, e0) for x, s0, e0 in hw if s0 >= prev_end - 0.02 and e0 <= next_start + 0.02]
            best = max(cands, default=(0, 0, 0))
            if best[0] >= 0.6:
                times[i] = [best[1], best[2]]
    matched = sum(t is not None for t in times)
    # interpolate the rest between known neighbours, by character length
    i = 0
    while i < len(sw):
        if times[i] is None:
            j = i
            while j < len(sw) and times[j] is None: j += 1
            t0 = times[i - 1][1] if i > 0 else 0.05
            t1 = times[j][0] if j < len(sw) else len(a) / 16000 - 0.1
            L = sum(len(sw[k]) for k in range(i, j)); acc = 0
            for k in range(i, j):
                s0 = t0 + (t1 - t0) * acc / L; acc += len(sw[k])
                times[k] = [s0, t0 + (t1 - t0) * acc / L]
            i = j
        else:
            i += 1
    for k in range(1, len(times)):                               # monotonic
        times[k][0] = max(times[k][0], times[k - 1][0] + 0.02)
        times[k][1] = max(times[k][1], times[k][0] + 0.05)
    json.dump([{"sp": w, "s": round(t[0], 3), "e": round(t[1], 3)} for w, t in zip(sw, times)],
              open(os.path.join(VO, f"{lid}.words.json"), "w"), ensure_ascii=False)
    print(f"{lid:6s} matched {matched}/{len(sw)}  | {' '.join(w.word.strip() for s in segs for w in s.words)}", flush=True)
