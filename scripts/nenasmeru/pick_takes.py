"""Keep the best ElevenLabs take of each line, then process it for the mix.

  python3 -I scripts/<name>/pick_takes.py

For every line in vo_lines.json, each take in .media-src/<name>/vo-takes/take*/ is
  1. transcribed with faster-whisper (large-v3, Malay, with the place names as a prompt) and scored
     against the caption text (character similarity: are the words right?), then
  2. scored for pitch movement (median semitones per second inside voiced runs: is it lively?).
The take with the best accuracy (to 2 decimals) wins, ties go to the livelier one. The winner is copied to
<name>/assets/audio/vo-<id>.raw.mp3, its timings to vo_align.json, and processed to vo-<id>.wav:
70 Hz high-pass, gentle compression, +1.5 dB presence at 3.5 kHz, -16 LUFS / -1.5 dBTP, 48 kHz mono.
Needs: pip install faster-whisper praat-parselmouth. Then run build.py.
"""
import os, json, glob, re, difflib, shutil, subprocess
import numpy as np, parselmouth
from faster_whisper import WhisperModel

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
NAME = os.path.basename(HERE)
AUD = os.path.join(ROOT, NAME, "assets", "audio")
L = json.load(open(os.path.join(HERE, "vo_lines.json")))
TAKES = sorted(glob.glob(os.path.join(ROOT, ".media-src", NAME, "vo-takes", "take*")))
PROMPT = ("Seribu ringgit je? Rumah landed satu tingkat. Jalan Nenas, Meru Klang. Teres dan semi-D. "
          "Hospital Kapar, SRA Meru 2. Freehold, Rizab Melayu. SPA legal fee, MOT fee. WhatsApp aku sekarang.")
CHAIN = "highpass=f=70,acompressor=threshold=-20dB:ratio=2.2:attack=10:release=150:makeup=1.5,equalizer=f=3500:t=q:w=1.2:g=1.5"


def load16k(path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768


def nz(s):
    s = s.lower().replace("sy", "sh").replace("rm", "").replace(",000", "")
    return re.sub(r"[^a-z0-9]", "", s)


def medfilt(x, k=7):
    p = k // 2; xp = np.pad(x, p, mode="edge")
    return np.array([np.median(xp[i:i + k]) for i in range(len(x))])


def movement(a):
    f0 = parselmouth.Sound(a.astype(np.float64), 16000).to_pitch_ac(time_step=0.01, pitch_floor=75, pitch_ceiling=350,
                                                                      octave_jump_cost=0.6).selected_array["frequency"]
    if (f0 > 0).sum() < 20:
        return 0.0
    st = np.where(f0 > 0, 12 * np.log2(np.maximum(f0, 1) / np.median(f0[f0 > 0])), np.nan)
    d, run = [], []
    for v in list(st) + [np.nan]:
        if not np.isnan(v):
            run.append(v)
        else:
            if len(run) > 8:
                d += list(np.abs(np.diff(medfilt(np.array(run)))) * 100)
            run = []
    return float(np.median(d)) if d else 0.0


def process(src, dst):
    j = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", CHAIN + ",loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = json.loads(j[j.rindex("{"):j.rindex("}") + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-af", f"{CHAIN},{ln},aresample=48000",
                    "-ac", "1", "-c:a", "pcm_s16le", dst], check=True)


model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
align_out, chosen = {}, {}
for ln in L["lines"]:
    ref = ln["say"]  # spoken form; Whisper may write numbers either way, the score is only compared between takes
    rows = []
    for t in TAKES:
        f = os.path.join(t, f"vo-{ln['id']}.mp3")
        if not os.path.exists(f):
            continue
        a = load16k(f)
        res, _ = model.transcribe(a, language="ms", beam_size=5, condition_on_previous_text=False, initial_prompt=PROMPT)
        hyp = " ".join(s.text.strip() for s in res)
        rows.append((difflib.SequenceMatcher(None, nz(ref), nz(hyp)).ratio(), movement(a), len(a) / 16000, t, hyp))
    rows.sort(key=lambda r: (round(r[0], 2), r[1]), reverse=True)
    best = rows[0]
    print(ln["id"], flush=True)
    for r in rows:
        print(f"  {'*' if r is best else ' '} {os.path.basename(r[3]):6s} acc={r[0]:.3f} move={r[1]:5.1f} dur={r[2]:4.1f} :: {r[4]}", flush=True)
    chosen[ln["id"]] = os.path.basename(best[3])
    shutil.copy(os.path.join(best[3], f"vo-{ln['id']}.mp3"), os.path.join(AUD, f"vo-{ln['id']}.raw.mp3"))
    align_out[ln["id"]] = json.load(open(os.path.join(best[3], "align.json")))[ln["id"]]
    process(os.path.join(AUD, f"vo-{ln['id']}.raw.mp3"), os.path.join(AUD, f"vo-{ln['id']}.wav"))
json.dump(align_out, open(os.path.join(HERE, "vo_align.json"), "w"), ensure_ascii=False)
L["_takes"] = "best take of each line (pick_takes.py): " + json.dumps(chosen)
json.dump(L, open(os.path.join(HERE, "vo_lines.json"), "w"), ensure_ascii=False, indent=2)
print("chosen", chosen)
