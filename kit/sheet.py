"""Folha de stills: sheet.py <render.py> <timings.json> <plates> <out.png> [cols] — 1 still no meio de cada shot (ou a cada N s com --every N)."""
import sys, os, importlib.util
KIT = os.path.dirname(os.path.abspath(__file__))
rp, tj, pl, out = sys.argv[1:5]
every = float(sys.argv[sys.argv.index("--every") + 1]) if "--every" in sys.argv else None
sys.path.insert(0, KIT)
sys.argv = ["x", tj, "0", "0", "x", KIT, pl]
spec = importlib.util.spec_from_file_location("ep", rp); ep = importlib.util.module_from_spec(spec); spec.loader.exec_module(ep)
from gfx import *
times = [((s + min(e, ep.END)) / 2) for s, e, fn, a in ep.SHOTS] if not every else [i * every for i in range(int(ep.END / every) + 1)]
tw, th = 216, 384; cols = 8; rows = (len(times) + cols - 1) // cols
sheet = skia.Surface(cols * tw, rows * (th + 26)); sc = sheet.getCanvas(); sc.clear(C("#333333"))
surf = skia.Surface(W, H); f = skia.Font(TF, 18)
for i, t in enumerate(times):
    ep.render_frame(surf, int(t * FPS))
    x, y = (i % cols) * tw, (i // cols) * (th + 26)
    sc.drawImageRect(surf.makeImageSnapshot(), skia.Rect(x, y, x + tw, y + th), skia.SamplingOptions(skia.FilterMode.kLinear))
    sc.drawString(f"{t:.1f}s", x + 6, y + th + 20, f, fill(C("#ffffff")))
sheet.makeImageSnapshot().save(out)
print("ok", len(times))
