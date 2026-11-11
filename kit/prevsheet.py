import sys, glob, os
import skia
d = sys.argv[1]; names = sys.argv[3:]
tw, th = 238, 422
cols = 8; rows = (len(names) + cols - 1) // cols
surf = skia.Surface(cols * tw, rows * (th + 30)); cv = surf.getCanvas(); cv.clear(skia.ColorSetRGB(60, 60, 60))
f = skia.Font(skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"), 16)
for i, n in enumerate(names):
    x, y = (i % cols) * tw, (i // cols) * (th + 30)
    cv.drawRect(skia.Rect(x, y, x + tw, y + th), skia.Paint(Color=skia.ColorSetRGB(150, 175, 205)))
    im = skia.Image.open(f"{d}/{n}.png")
    cv.drawImageRect(im, skia.Rect(x, y, x + tw, y + th), skia.SamplingOptions(skia.FilterMode.kLinear))
    cv.drawString(n, x + 6, y + th + 22, f, skia.Paint(Color=skia.ColorWHITE))
surf.makeImageSnapshot().save(sys.argv[2], skia.kPNG)
