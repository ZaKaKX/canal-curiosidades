"""Alinha falas (texto) ao áudio do Pedro usando segmentos do ASR + atividade de voz.
uso: align.py falas.txt asr.json audio.wav out_timings.json out_mouth.json"""
import sys, json, re, difflib, subprocess, unicodedata
import numpy as np
falas, asrj, wav, outj, outm = sys.argv[1:6]
lines = [l.strip() for l in open(falas, encoding="utf-8") if l.strip()]
asr = json.load(open(asrj))
SR = 16000
a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, dtype=np.float32)
dur = len(a) / SR
hop = SR // 100  # 10ms
rms = np.sqrt(np.convolve(a ** 2, np.ones(hop * 3) / (hop * 3), "same")[::hop])
db = 20 * np.log10(rms + 1e-6)
act = (db > np.percentile(db, 30) + 6).astype(float)

def norm(w):
    w = unicodedata.normalize("NFD", w.lower()); w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)

# ASR words with times: within each segment, map cumulative chars -> cumulative voice activity
aw = []
for sg in asr:
    ws = sg["text"].split()
    if not ws: continue
    i0, i1 = int(sg["s"] * 100), max(int(sg["s"] * 100) + 1, int(sg["e"] * 100))
    seg = act[i0:i1] + 0.05; cum = np.concatenate([[0], np.cumsum(seg)]); cum /= cum[-1]
    wts = np.array([len(w) + 1.5 for w in ws], float); cw = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
    tt = lambda f: (i0 + np.searchsorted(cum, f)) / 100
    for k, w in enumerate(ws):
        aw.append({"n": norm(w), "s": tt(cw[k]), "e": tt(cw[k + 1])})
# script words
sw = []
for li, l in enumerate(lines):
    for w in l.split():
        sw.append({"w": w, "n": norm(w), "li": li})
A = [x["n"] for x in aw]; S = [x["n"] for x in sw]
sm = difflib.SequenceMatcher(None, S, A, autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        for k in range(i2 - i1):
            sw[i1 + k]["s"], sw[i1 + k]["e"] = aw[j1 + k]["s"], aw[j1 + k]["e"]
    elif tag == "replace" and j2 > j1:
        t0, t1 = aw[j1]["s"], aw[j2 - 1]["e"]
        wt = np.array([len(sw[i]["n"]) + 1.5 for i in range(i1, i2)]); c = np.concatenate([[0], np.cumsum(wt)]) / wt.sum()
        for k, i in enumerate(range(i1, i2)):
            sw[i]["s"], sw[i]["e"] = t0 + (t1 - t0) * c[k], t0 + (t1 - t0) * c[k + 1]
# interpolate unmatched
for i, x in enumerate(sw):
    if "s" not in x:
        p = next((sw[j]["e"] for j in range(i - 1, -1, -1) if "e" in sw[j]), 0.0)
        n = next((sw[j]["s"] for j in range(i + 1, len(sw)) if "s" in sw[j]), dur)
        x["s"], x["e"] = p, min(n, p + 0.3)
out = {"duration": round(dur, 3), "lines": []}
for li, l in enumerate(lines):
    wl = [x for x in sw if x["li"] == li]
    out["lines"].append({"i": li + 1, "text": l, "s": round(wl[0]["s"], 3), "e": round(wl[-1]["e"], 3),
                         "words": [{"w": x["w"], "s": round(float(x["s"]), 3), "e": round(float(x["e"]), 3)} for x in wl]})
json.dump(out, open(outj, "w"), ensure_ascii=False, indent=1)
# mouth envelope at 30 fps
fr = int(dur * 30) + 1; m = []
for f in range(fr):
    i = int(f / 30 * 100); v = db[max(0, i - 2):i + 3].max() if i < len(db) else -90
    m.append(v)
m = np.array(m); lo, hi = np.percentile(m, 35), np.percentile(m, 97)
m = np.clip((m - lo) / (hi - lo), 0, 1)
sm_ = np.copy(m)
for f in range(1, fr): sm_[f] = max(m[f], sm_[f - 1] * 0.55)
json.dump([round(float(v), 3) for v in sm_], open(outm, "w"))
for l in out["lines"]: print(f'{l["s"]:6.2f}-{l["e"]:6.2f} {l["text"]}')
