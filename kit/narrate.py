"""Narrate script.md lines with Kokoro, output narration.wav + timings.json."""
import sys, re, json
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

model_dir, script_md, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
voice = sys.argv[4] if len(sys.argv) > 4 else "am_michael"
speed = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
lang = sys.argv[6] if len(sys.argv) > 6 else ("pt-br" if voice.startswith("p") else "en-us")

lines = []
for row in open(script_md, encoding="utf-8"):
    m = re.match(r"\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", row)
    if m:
        lines.append(m.group(2))

k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
SR = 24000
audio, timings, t = [], [], 0.0
lead = np.zeros(int(0.15 * SR), dtype=np.float32)
audio.append(lead); t += len(lead) / SR
for i, text in enumerate(lines):
    s, sr = k.create(text, voice=voice, speed=speed, lang=lang)
    assert sr == SR
    s = s.astype(np.float32)
    # trim silence
    idx = np.where(np.abs(s) > 0.01)[0]
    if len(idx):
        s = s[max(0, idx[0] - 600): idx[-1] + 1200]
    dur = len(s) / SR
    words = text.split()
    weights = [(6 * len(re.sub(r"\D", "", w)) if re.search(r"\d", w) else len(re.sub(r"[^\w]", "", w))) + 2 for w in words]
    tot = sum(weights); wt, acc = [], t
    for w, wgt in zip(words, weights):
        d = dur * wgt / tot
        wt.append({"w": w, "s": round(acc, 3), "e": round(acc + d, 3)})
        acc += d
    timings.append({"i": i + 1, "text": text, "s": round(t, 3), "e": round(t + dur, 3), "words": wt})
    audio.append(s); t += dur
    gap = 0.55 if len(text.split()) <= 6 else 0.22
    audio.append(np.zeros(int(gap * SR), dtype=np.float32)); t += gap
audio.append(np.zeros(int(0.8 * SR), dtype=np.float32)); t += 0.8
full = np.concatenate(audio)
full = full / max(1e-6, np.abs(full).max()) * 0.89
sf.write(f"{out_dir}/narration.wav", full, SR)
json.dump({"duration": round(t, 3), "lines": timings}, open(f"{out_dir}/timings.json", "w"), indent=1)
print("duration", round(t, 2), "s,", len(lines), "lines")
