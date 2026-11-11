"""Cover (capa) 1080x1920 for TikTok/Shorts: a clean frame of the episode (no captions) + big title text.
usage: python3 -I kit/cover.py <render.py> <timings.json> <platesdir> <time_s> "<TITLE LINE 1|LINE 2>" <out.png> [highlight words]
Title lines split by '|'. Words listed in highlight (comma-separated) are drawn in yellow."""
import sys, os, importlib.util
KIT = os.path.dirname(os.path.abspath(__file__))
render_py, tj, pl, t, title, out = sys.argv[1:7]
hl = {w.strip().upper() for w in (sys.argv[7] if len(sys.argv) > 7 else "").split(",") if w.strip()}
sys.path.insert(0, KIT)
sys.argv = ["x", tj, "0", "0", "x", KIT, pl]
spec = importlib.util.spec_from_file_location("ep", render_py); ep = importlib.util.module_from_spec(spec); spec.loader.exec_module(ep)
from gfx import *
ep.draw_caption = lambda *a, **k: None
surf = skia.Surface(W, H)
ep.render_frame(surf, int(float(t) * FPS))
cv = surf.getCanvas()
cv.drawRect(skia.Rect(0, 0, W, 900), lin(0, 0, 0, 900, [C("#000000", 150), C("#000000", 0)]))
lines = [l.strip().upper() for l in title.split("|")]
y = 300
for ln in lines:
    size = 150
    f = skia.Font(TF, size)
    while f.measureText(ln) > 960 and size > 60:
        size -= 6; f = skia.Font(TF, size)
    x = (W - f.measureText(ln)) / 2
    cv.drawString(ln, x + 8, y + 10, f, fill(C("#000000", 140)))
    for w in ln.split(" "):
        cv.drawString(w, x, y, f, stroke(C("#0e0a07"), 22))
        cv.drawString(w, x, y, f, fill(C("#ffd54a") if w.strip(".,!?") in hl else C("#ffffff")))
        x += f.measureText(w + " ")
    y += size * 1.08
surf.makeImageSnapshot().save(out, skia.kPNG)
print("cover", out)
