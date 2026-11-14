"""Enhance the ElevenLabs VO clips.

For every line: vo/<id>.mp3  ->  vo/<id>.wav
  1. tighten pauses: silent runs (from the audio's own level) longer than MAX_GAP are cut
     down to KEEP_GAP (10 ms crossfades), lead-in trimmed to 60 ms
  2. tempo x TEMPO with rubberband (pitch kept), so the expressive eleven_v3 read fits
  3. broadcast EQ, de-ess, compression, then the same loudness on every clip
     (-16 LUFS, -1.5 dBTP), 48 kHz mono WAV
Word timings are then measured on the final WAV by align_vo.py (eleven_v3's own
timestamps are off by ~0.2 s, up to 1.7 s).

Usage: python3 -I pulau-indah/scripts/enhance_vo.py [line_id ...]
"""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VO = os.path.join(HERE, "..", "video", "assets", "audio", "vo")
ids = sys.argv[1:] or [l["id"] for l in json.load(open(os.path.join(HERE, "vo_script.json")))["lines"]]
SR = 44100
MAX_GAP, KEEP_GAP = 0.42, 0.32   # s
LEAD, TAIL = 0.06, 0.15          # s kept before the first / after the last word
TEMPO = 1.12
SIL_DB = -42.0                  # dBFS, 10 ms frames
XF = int(0.010 * SR)
CHAIN = ",".join([
    "highpass=f=75:p=2",                          # rumble
    "equalizer=f=170:t=q:w=1.0:g=2.0",            # chest / warmth
    "equalizer=f=380:t=q:w=1.3:g=-2.5",           # boxy mud
    "equalizer=f=3300:t=q:w=1.4:g=2.5",           # presence, words cut through the music
    "deesser=i=0.35:m=0.5:f=0.5",                 # tame the s
    "highshelf=f=9500:g=1.5",                     # air
    "acompressor=threshold=-21dB:ratio=3:attack=4:release=90:knee=3:makeup=2",
])

for lid in ids:
    src = os.path.join(VO, f"{lid}.mp3")
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                     capture_output=True, check=True).stdout, dtype=np.float32)
    # silent runs from the audio itself (10 ms frames below SIL_DB), not from the v3 alignment
    fr = int(0.01 * SR)
    db = np.array([20 * np.log10(np.sqrt(np.mean(a[i:i + fr] ** 2)) + 1e-9) for i in range(0, len(a) - fr, fr)])
    voiced = np.where(db > SIL_DB)[0]
    first, last = voiced[0] * 0.01, (voiced[-1] + 1) * 0.01
    segs, run0 = [[max(0.0, first - LEAD), None]], None
    for i in range(voiced[0], voiced[-1] + 1):
        if db[i] <= SIL_DB:
            run0 = i if run0 is None else run0
        elif run0 is not None:
            if (i - run0) * 0.01 > MAX_GAP:
                segs[-1][1] = run0 * 0.01 + KEEP_GAP / 2
                segs.append([i * 0.01 - KEEP_GAP / 2, None])
            run0 = None
    segs[-1][1] = min(len(a) / SR, last + TAIL)
    # stitch with short crossfades; map(t) = output time (pre-tempo) for a source time t
    pieces, offs, pos = [], [], 0.0
    for s0, s1 in segs:
        offs.append((s0, s1, pos - s0))
        pieces.append(a[int(s0 * SR):int(s1 * SR)].copy())
        pos += s1 - s0
    out = pieces[0]
    for p in pieces[1:]:
        ramp = np.linspace(0, 1, XF, dtype=np.float32)
        out = np.concatenate([out[:-XF], out[-XF:] * (1 - ramp) + p[:XF] * ramp, p[XF:]])
        # each later piece shifts XF samples earlier
    tmp = os.path.join(VO, f".{lid}.tight.f32")
    out.astype(np.float32).tofile(tmp)
    # loudness pass 1 (measure), pass 2 (apply) on the stretched + processed signal
    pre = f"rubberband=tempo={TEMPO}:window=short,{CHAIN}"
    m = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", tmp, "-af",
                        pre + ",loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=7:linear=true:measured_I={j['input_i']}:measured_TP={j['input_tp']}"
          f":measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}")
    dst = os.path.join(VO, f"{lid}.wav")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", tmp,
                    "-af", f"{pre},{ln},aresample=48000", "-ac", "1", "-c:a", "pcm_s16le", dst], check=True)
    os.remove(tmp)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst],
                               capture_output=True, text=True).stdout)
    print(f"{lid:6s} {len(a) / SR:5.2f}s -> {dur:5.2f}s  ({len(segs) - 1} pauses tightened, in {j['input_i']} LUFS)", flush=True)
