#!/usr/bin/env python3
"""Make a TTS voiceover livelier and cleaner, like a radio ad read.

1. Intonation: widen the pitch movement around the speaker's median by
   --intonation (1.0 = unchanged, 1.3 = 30% wider), with Praat PSOLA.
2. Light noise reduction (the clone copies the room tone of its reference),
   EQ (less mud, more presence and air), de-essing and compression.
3. Pitch-preserving speed-up with --tempo (rubberband).
4. Loudness -16 LUFS / -1.5 dBTP, same as the other edits.

    python3 -I scripts/vo_enhance.py in.wav out_base --intonation 1.3 --tempo 1.07
writes out_base.wav and out_base.mp3. Needs praat-parselmouth and ffmpeg.
"""
import argparse
import subprocess
import tempfile

import numpy as np
import parselmouth
from parselmouth.praat import call

CHAIN = ",".join([
    "afftdn=nr=10:nf=-42",
    "highpass=f=85",
    "equalizer=f=280:t=q:w=1.0:g=-2.5",
    "equalizer=f=3200:t=q:w=1.0:g=3",
    "highshelf=f=9000:g=2",
    "deesser=i=0.4",
    "acompressor=threshold=-22dB:ratio=3:attack=4:release=90:makeup=2",
])


def widen_intonation(src, dst, factor):
    snd = parselmouth.Sound(src)
    manip = call(snd, "To Manipulation", 0.01, 70, 350)
    tier = call(manip, "Extract pitch tier")
    n = call(tier, "Get number of points")
    times = [call(tier, "Get time from index", i) for i in range(1, n + 1)]
    freqs = np.array([call(tier, "Get value at index", i) for i in range(1, n + 1)])
    median = float(np.median(freqs))
    new = median * (freqs / median) ** factor
    call(tier, "Remove points between", snd.xmin, snd.xmax)
    for t, f in zip(times, new):
        call(tier, "Add point", t, float(f))
    call([tier, manip], "Replace pitch tier")
    out = call(manip, "Get resynthesis (overlap-add)")
    out.scale_peak(0.89)  # headroom, so the 16-bit file never clips; loudness is set later
    out.save(dst, "WAV")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("out_base")
    p.add_argument("--intonation", type=float, default=1.3)
    p.add_argument("--tempo", type=float, default=1.07)
    a = p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        src = a.src
        if a.intonation != 1.0:
            src = f"{tmp}/pitch.wav"
            widen_intonation(a.src, src, a.intonation)
        af = f"{CHAIN},rubberband=tempo={a.tempo},loudnorm=I=-16:TP=-1.5:LRA=9"
        wav, mp3 = f"{a.out_base}.wav", f"{a.out_base}.mp3"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", af, "-ar", "48000", "-ac", "1", wav],
                       check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-codec:a", "libmp3lame", "-b:a", "160k", mp3],
                       check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
                         capture_output=True, text=True, check=True).stdout.strip()
    print(f"{float(dur):.1f}s")


if __name__ == "__main__":
    main()
