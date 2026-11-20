"""Use a chosen take for each line and process it for the mix (no Whisper; pick_takes.py does the scoring).

  python3 -I scripts/<name>/process_vo.py [line=takeN ...]

Starts from the takes pick_takes.py chose (vo_lines.json "_takes"), applies any overrides given on the
command line (e.g. hook=take3 pkg=take3), then for each line:
  - copies .media-src/<name>/vo-takes/<take>/vo-<id>.mp3 to <name>/assets/audio/vo-<id>.raw.mp3
  - copies its ElevenLabs character timings into vo_align.json
  - writes vo-<id>.wav: tempo from edl.json ("tempo", pitch kept), 70 Hz high-pass, 2.2:1 compression,
    +1.5 dB at 3.5 kHz, -16 LUFS / -1.5 dBTP, 48 kHz mono.
build.py divides the timings by the same tempo, so run it afterwards.
"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
NAME = os.path.basename(HERE)
AUD = os.path.join(ROOT, NAME, "assets", "audio")
TAKES = os.path.join(ROOT, ".media-src", NAME, "vo-takes")
L = json.load(open(os.path.join(HERE, "vo_lines.json")))
T = json.load(open(os.path.join(HERE, "edl.json"))).get("tempo", 1.0)
CHAIN = "highpass=f=70,acompressor=threshold=-20dB:ratio=2.2:attack=10:release=150:makeup=1.5,equalizer=f=3500:t=q:w=1.2:g=1.5"
if abs(T - 1.0) > 1e-6:
    CHAIN = f"atempo={T}," + CHAIN

chosen = json.loads(re.search(r"\{.*\}", L.get("_takes", "{}")).group(0)) if L.get("_takes") else {}
for arg in sys.argv[1:]:
    k, v = arg.split("=")
    chosen[k] = v


def process(src, dst):
    j = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", CHAIN + ",loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = json.loads(j[j.rindex("{"):j.rindex("}") + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-af", f"{CHAIN},{ln},aresample=48000",
                    "-ac", "1", "-c:a", "pcm_s16le", dst], check=True)


align = {}
for ln in L["lines"]:
    k = ln["id"]
    take = chosen.get(k, "take1")
    src = os.path.join(TAKES, take, f"vo-{k}.mp3")
    shutil.copy(src, os.path.join(AUD, f"vo-{k}.raw.mp3"))
    align[k] = json.load(open(os.path.join(TAKES, take, "align.json")))[k]
    process(src, os.path.join(AUD, f"vo-{k}.wav"))
    print(k, take, flush=True)
json.dump(align, open(os.path.join(HERE, "vo_align.json"), "w"), ensure_ascii=False)
L["_takes"] = "takes used (pick_takes.py scores, then process_vo.py overrides): " + json.dumps(chosen)
json.dump(L, open(os.path.join(HERE, "vo_lines.json"), "w"), ensure_ascii=False, indent=2)
print("tempo", T, "takes", chosen)
