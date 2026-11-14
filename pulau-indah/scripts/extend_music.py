"""Lengthen music-bed by repeating two bars once (seamless splice), so the track's own
ending lands on the end card. Searches the full-arrangement section for the loop
point whose two-bar-later audio matches best. music-bed-orig.mp3 -> music-bed.mp3"""
import os, subprocess, numpy as np
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video", "assets", "audio")
SR = 44100
a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(A, "music-bed-orig.mp3"), "-ac", "2", "-ar", str(SR),
                                  "-f", "f32le", "-"], capture_output=True, check=True).stdout, dtype=np.float32).reshape(-1, 2)
mono = a.mean(1)
best = None
for P in np.arange(5.90, 6.10, 0.002):                # two bars at ~80 BPM
    p = int(P * SR)
    for X in np.arange(46.0, 58.0, 0.05):
        x = int(X * SR); w = int(0.4 * SR)
        u, v = mono[x:x + w], mono[x + p:x + p + w]
        c = float(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-9))
        if best is None or c > best[0]:
            best = (c, P, X)
c, P, X = best
x, p, xf = int(X * SR), int(P * SR), int(0.03 * SR)
ramp = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
# play [0, X+P), then jump back to X and continue: the bars X..X+P are heard twice
out = np.concatenate([a[:x + p], a[x + p:x + p + xf] * (1 - ramp) + a[x:x + xf] * ramp, a[x + xf:]])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "libmp3lame", "-b:a", "192k",
                os.path.join(A, "music-bed.mp3")], input=out.tobytes(), check=True)
print(f"splice at {X:.2f}s, period {P:.3f}s, similarity {c:.3f}, new length {len(out) / SR:.2f}s")
