"""Word timings for burned-in captions, on the EDITED timeline.

1. Concatenate the kept stretches of the cleaned voice (per scripts/edl.json).
2. Transcribe that with faster-whisper (large-v3) for rough word times.
3. Align whisper's tokens to the corrected text in the EDL (difflib), so the
   captions use the right spelling, then snap each word start to the nearest
   speech onset in the waveform and clamp it inside its own segment.

Usage: python3 -I scripts/align_captions.py video/assets/audio/voice.wav scripts/edl.json video/captions.json
"""
import sys, json, re, difflib, wave
import numpy as np

voice, edl_path, out_path = sys.argv[1:4]
edl = json.load(open(edl_path))

# --- load voice (any rate, mono 16-bit) and resample to 16 kHz for whisper ---
wf = wave.open(voice); sr = wf.getframerate()
a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
if sr != 16000:
    idx = np.arange(0, len(a), sr / 16000.0)
    a = np.interp(idx, np.arange(len(a)), a).astype(np.float32)
SR = 16000

# --- build the edited voice track and the segment map ---
pieces, segmap, t = [], [], 0.0
for s in edl["segments"]:
    x = a[int(s["a_in"] * SR):int(s["a_out"] * SR)].copy()
    if s.get("ambient") or s.get("silent"):
        x[:] = 0
    pieces.append(x)
    segmap.append({"id": s["id"], "start": t, "end": t + len(x) / SR, "text": s["text"]})
    t += len(x) / SR
cut = np.concatenate(pieces)

# --- energy envelope (10 ms) for onset snapping ---
hop = SR // 100
env = np.array([np.sqrt(np.mean(cut[i:i + hop] ** 2) + 1e-10) for i in range(0, len(cut) - hop, hop)])
db = 20 * np.log10(env)

def snap_onset(t0, lo, hi):
    """Nearest rise from quiet to speech within +-0.15 s of t0, inside [lo, hi)."""
    best, bestd = t0, 9
    for k in range(int((t0 - 0.15) * 100), int((t0 + 0.15) * 100)):
        if k < 1 or k >= len(db) or k / 100 < lo or k / 100 >= hi:
            continue
        if db[k] > -34 and db[k - 1] <= db[k] - 4:
            d = abs(k / 100 - t0)
            if d < bestd:
                best, bestd = k / 100, d
    return best

from faster_whisper import WhisperModel
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
prompt = " ".join(s["text"] for s in edl["segments"] if s["text"])
res, _ = m.transcribe(cut, language="ms", word_timestamps=True, beam_size=5,
                      initial_prompt=prompt[:800], condition_on_previous_text=False)
hyp = [(w.word.strip(), w.start, w.end) for seg in res for w in seg.words]

norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
words = []
for sm in segmap:
    if not sm["text"]:
        continue
    exp = sm["text"].split()
    # whisper words whose centre falls in this segment
    hw = [h for h in hyp if sm["start"] - 0.05 <= (h[1] + h[2]) / 2 < sm["end"] + 0.05]
    times = [None] * len(exp)
    sm_ = difflib.SequenceMatcher(None, [norm(e) for e in exp], [norm(h[0]) for h in hw], autojunk=False)
    for blk in sm_.get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = (hw[blk.b + k][1], hw[blk.b + k][2])
    # speech span of the segment from the envelope
    k0, k1 = int(sm["start"] * 100), int(sm["end"] * 100)
    loud = [k for k in range(k0, min(k1, len(db))) if db[k] > -34]
    sp0 = loud[0] / 100 if loud else sm["start"]
    sp1 = (loud[-1] + 1) / 100 if loud else sm["end"]
    # fill gaps by character-weighted interpolation between known anchors
    anchors = [(-1, sp0)] + [(i, times[i][0]) for i in range(len(exp)) if times[i]] + [(len(exp), sp1)]
    for (ia, ta), (ib, tb) in zip(anchors, anchors[1:]):
        gap = list(range(ia + 1, ib))
        if not gap:
            continue
        tstart = ta if ia < 0 else (times[ia][1] if times[ia] else ta)
        weights = [max(2, len(norm(exp[i]))) for i in gap]
        span = max(0.05, tb - tstart); acc = tstart
        for i, wgt in zip(gap, weights):
            d = span * wgt / sum(weights)
            times[i] = (acc, acc + d); acc += d
    for i, e in enumerate(exp):
        st, en = times[i]
        st = min(max(st, sm["start"]), sm["end"] - 0.05)
        st = snap_onset(st, sm["start"], sm["end"])
        en = min(max(en, st + 0.08), sm["end"])
        words.append({"text": e, "start": round(st, 3), "end": round(en, 3), "seg": sm["id"]})
# monotonic + contiguous ends
for i in range(len(words) - 1):
    if words[i + 1]["start"] < words[i]["start"] + 0.04:
        words[i + 1]["start"] = round(words[i]["start"] + 0.04, 3)
    if words[i]["seg"] == words[i + 1]["seg"]:
        words[i]["end"] = round(min(max(words[i]["end"], words[i]["start"] + 0.08), words[i + 1]["start"]), 3)
for i, w in enumerate(words):
    w["id"] = f"w{i}"
json.dump({"duration": round(t, 3), "segments": segmap, "words": words}, open(out_path, "w"), indent=1, ensure_ascii=False)
print("whisper:", " ".join(h[0] for h in hyp))
for w in words:
    print(f'{w["start"]:6.2f}-{w["end"]:6.2f} {w["seg"]:9s} {w["text"]}')
