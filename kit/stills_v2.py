import sys
sd, tj, pl, out = sys.argv[1:5]
sys.argv = ["x", tj, "0", "0", "x", sd, pl]
sys.path.insert(0, sd)
import render_ep01_v2 as R
import skia
surf = skia.Surface(R.W, R.H)
for i, (s, e, fn, a) in enumerate(R.SHOTS):
    fi = int((s + (e - s) * 0.65) * R.FPS)
    R.render_frame(surf, fi)
    surf.makeImageSnapshot().resize(270, 480).save(f"{out}/v2_{i:02d}.png", skia.kPNG)
