"""Transcribe the site-visit footage and make contact sheets to pick shots from.
  python3 -I transcribe.py <work-dir>/source.mov <work-dir>
Writes <work-dir>/transcript.json (segments + words, Whisper large-v3, Malay), prints the
transcript with timestamps, and writes <work-dir>/sheet_<n>.jpg: 1 frame per second,
48 per sheet, each stamped MMSS (so 0105 = 65 s).
The audio is high-passed and loudness-normalised first, and VAD is on: without that,
Whisper hallucinates "Terima kasih kerana menonton" over quiet phone audio."""
import json, os, subprocess, sys, wave
import numpy as np
from faster_whisper import WhisperModel

src, work = sys.argv[1], sys.argv[2]
os.makedirs(work, exist_ok=True)
wav = os.path.join(work, "audio16k.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-af", "highpass=f=90,loudnorm=I=-16", "-ac", "1", "-ar", "16000", wav], check=True)
wf = wave.open(wav); a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
m = WhisperModel("large-v3", device="cpu", compute_type="int8")
segs, _ = m.transcribe(a, language="ms", word_timestamps=True, vad_filter=True, beam_size=5, condition_on_previous_text=False)
out = []
for s in segs:
    out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                "words": [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2), "p": round(w.probability, 2)} for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}", flush=True)
json.dump(out, open(os.path.join(work, "transcript.json"), "w"), ensure_ascii=False, indent=1)
fr = os.path.join(work, "frames"); os.makedirs(fr, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
                "fps=1,scale=180:-2,drawtext=text='%{pts\\:gmtime\\:0\\:%M%S}':x=4:y=4:fontsize=22:fontcolor=yellow:box=1:boxcolor=black",
                "-q:v", "4", os.path.join(fr, "f_%03d.jpg")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(fr, "f_%03d.jpg"), "-vf", "tile=12x4", "-q:v", "3",
                os.path.join(work, "sheet_%d.jpg")], check=True)
print("sheets:", sorted(f for f in os.listdir(work) if f.startswith("sheet_")))
