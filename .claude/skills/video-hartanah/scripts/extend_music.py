"""Lengthen music-bed.mp3 by repeating a stretch of bars once (seamless splice), for an
ElevenLabs track that ends before the end card.
  extend_music.py <project-dir> <seconds-to-add>
Keeps the original as music-bed-orig.mp3. Detects the beat period, rounds the added time to
whole bars, and picks the loop point in the middle of the track whose audio one loop later
matches best (10 ms crossfade). Then raise project.json music.length by the printed amount."""
import os, shutil, subprocess, sys
import numpy as np
PROJ, ADD = os.path.abspath(sys.argv[1]), float(sys.argv[2])
A = os.path.join(PROJ, "video", "assets", "audio")
orig, dst = os.path.join(A, "music-bed-orig.mp3"), os.path.join(A, "music-bed.mp3")
if not os.path.exists(orig):
    shutil.copy(dst, orig)
SR = 44100
a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", orig, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout, dtype=np.float32).reshape(-1, 2)
mono = a.mean(1); dur = len(mono) / SR
# beat period from the onset envelope autocorrelation (60-180 BPM)
sr2, hop = 11025, 110
m2 = mono[::4]
e = np.array([np.sqrt(np.mean(m2[i:i + 441] ** 2)) for i in range(0, len(m2) - 441, hop)])
on = np.maximum(0, np.diff(np.log(e + 1e-6))); fps = sr2 / hop
seg = on[int(dur * 0.3 * fps):int(dur * 0.8 * fps)]; seg = seg - seg.mean()
ac = np.correlate(seg, seg, "full")[len(seg) - 1:]
lo, hi = int(fps * 60 / 180), int(fps * 60 / 60)
beat = (lo + int(np.argmax(ac[lo:hi]))) / fps
bar = beat * 4
P0 = max(1, round(ADD / bar)) * bar
best = None
for Pp in np.arange(P0 * 0.985, P0 * 1.015, 0.002):
    p = int(Pp * SR)
    for X in np.arange(dur * 0.35, dur * 0.75 - Pp, 0.05):
        x = int(X * SR); w = int(0.4 * SR)
        u, v = mono[x:x + w], mono[x + p:x + p + w]
        c = float(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-9))
        if best is None or c > best[0]:
            best = (c, Pp, X)
c, Pp, X = best
x, p, xf = int(X * SR), int(Pp * SR), int(0.03 * SR)
ramp = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
out = np.concatenate([a[:x + p], a[x + p:x + p + xf] * (1 - ramp) + a[x:x + xf] * ramp, a[x + xf:]])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "libmp3lame", "-b:a", "192k", dst],
               input=out.tobytes(), check=True)
print(f"beat {beat:.3f}s ({60 / beat:.0f} BPM); repeated {Pp:.3f}s at {X:.2f}s (similarity {c:.2f}); new length {len(out) / SR:.2f}s -> add {Pp:.2f} to music.length")
