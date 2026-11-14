"""EP07 — A torre que era pra ser desmontada (Torre Eiffel). PT-BR.
3D inked plates (torre, torre em obra, topo com antena, rua de Paris, skyline com Panteão, chaminé, sala de rádio)
+ 2D sketch characters. usage: render.py timings.json a b out.mp4 kitdir platesdir"""
import sys, json, math, subprocess
import numpy as np
KW = {"torre", "eiffel", "prazo", "validade", "antena", "1887", "paris", "1889", "exposição", "monumento", "gustave",
      "ferro", "300", "metros", "artistas", "odiaram", "40", "protesto", "inútil", "monstruosa", "chaminé", "fábrica",
      "subiu", "mais", "alta", "mundo", "licença", "20", "anos", "1910", "desmontada", "útil", "laboratório",
      "reviravolta", "1898", "inventor", "rádio", "panteão", "perfeita", "exército", "1908", "6.000", "quilômetros",
      "renovada", "70", "guerra", "ouvido", "alemães", "espiã", "mata", "hari", "derrubar", "salva"}
OUT = {
    "eiffel":  dict(body="#2b2b33", trim="#f2efe6", hat="none"),
    "artist":  dict(body="#7a2f3a", trim="#f2e6c8", hat="none"),
    "artist2": dict(body="#3d5a3a", trim="#f2e6c8", hat="none"),
    "inventor": dict(body="#5a4632", trim="#e8dcc0", hat="none"),
    "soldier": dict(body="#3f5f8f", trim="#c9a24a", hat="officer"),
    "spy":     dict(body="#6a1b2a", trim="#e7c66a", hat="none"),
}
sys.path.insert(0, sys.argv[5])
from gfx import *
import gfx
import toon2 as T2
from toon2 import toon2, ink, sk

gfx.KEYWORDS.clear()
gfx.KEYWORDS.update(KW)

T2.OUTFITS.update(OUT)

TJ = json.load(open(sys.argv[1]))
PL = sys.argv[6]
L = {l["i"]: l for l in TJ["lines"]}
DUR = TJ["duration"]
CHUNKS = build_chunks(TJ)
CAP_Y = 1370
_IMG = {}
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear)
GREEK = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")


def img(name):
    if name not in _IMG:
        _IMG[name] = skia.Image.open(f"{PL}/{name}_ink.png")
    return _IMG[name]


_BOT = {}


def layer_bottom(name):
    """lowest opaque row (in 1920-space) of a layer — the waterline of the ship layer."""
    if name not in _BOT:
        a = img(name).toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., 3]
        rows = np.where(a.max(1) > 20)[0]
        _BOT[name] = rows.max() * H / a.shape[0]
    return _BOT[name]


def plate(cv, name, z=1.0, cx=W / 2, cy=H / 2, dx=0, dy=0, sigma=0, alpha=1.0, rot=0, tint=None, bright=None, cf=None):
    im = img(name)
    cv.save()
    cv.translate(cx + dx, cy + dy); cv.rotate(rot); cv.scale(z, z); cv.translate(-cx, -cy)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(alpha)
    if sigma > 0.3:
        p.setImageFilter(skia.ImageFilters.Blur(sigma, sigma))
    if tint:
        p.setColorFilter(skia.ColorFilters.Blend(C(*tint), skia.BlendMode.kMultiply))
    if bright:
        b = bright
        p.setColorFilter(skia.ColorFilters.Matrix([b, 0, 0, 0, 0.02, 0, b, 0, 0, 0.02, 0, 0, b, 0, 0.02, 0, 0, 0, 1, 0]))
    if cf is not None:
        p.setColorFilter(cf)
    cv.drawImageRect(im, skia.Rect(0, 0, W, H), SAMP, p)
    cv.restore()


def xray_cf():
    # luminance -> cyan glow on dark
    return skia.ColorFilters.Matrix([0.05, 0.1, 0.02, 0, 0.0,
                                     0.25, 0.5, 0.1, 0, 0.05,
                                     0.3, 0.6, 0.15, 0, 0.12,
                                     0, 0, 0, 1, 0])


def sprite(cv, name, x, y, s, ang=0, alpha=1.0, cf=None, sigma=0):
    """draw a full-frame layer whose subject is centred in the frame, recentred at (x,y), scaled, rotated (deg)."""
    im = img(name)
    cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(s, s); cv.translate(-W / 2, -H / 2)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(alpha)
    if cf is not None: p.setColorFilter(cf)
    if sigma > 0.3: p.setImageFilter(skia.ImageFilters.Blur(sigma, sigma))
    cv.drawImageRect(im, skia.Rect(0, 0, W, H), SAMP, p)
    cv.restore()


def ws(i, word, nth=0):
    cl = lambda w: w["w"].strip(".,!?'\"").lower()
    hits = [w for w in L[i]["words"] if cl(w) == word.lower()] or [w for w in L[i]["words"] if cl(w).startswith(word.lower())]
    return hits[nth]["s"]


_ds, _bn = date_stamp, banner


def _fit(text, size, maxw=940):
    while skia.Font(TF, size).measureText(text) > maxw and size > 40: size -= 4
    return size


def date_stamp(cv, text, lt, y=430, size=170, **k): _ds(cv, text, lt, y=y, size=_fit(text, size), **k)
def banner(cv, text, lt, y=420, size=78, **k): _bn(cv, text, lt, y=y, size=_fit(text, size, 900), **k)


def P(lt, d, a=1.0, b=1.08):
    return lerp(a, b, ease(lt / d))


def toon(cv, x, y, s, T, **k):
    """toon2 with the face kept above the caption band (head bottom <= ~1285)."""
    if not k.get("rot"):
        y = min(y, 1285 + 340 * s)
    toon2(cv, x, y, s, T, **k)


def pop_text(cv, text, lt, t0, y, size, col="#ffffff", font=None):
    if lt <= t0: return
    a = eout((lt - t0) / 0.25)
    f = skia.Font(font or TF, size)
    while f.measureText(text) > 820 and size > 40:
        size -= 6; f = skia.Font(font or TF, size)
    cv.save(); cv.translate(540, y); cv.scale(lerp(1.4, 1, a), lerp(1.4, 1, a))
    cv.drawString(text, -f.measureText(text) / 2, 0, f, stroke(C("#14100c", 255 * a), max(10, size // 8)))
    cv.drawString(text, -f.measureText(text) / 2, 0, f, fill(C(col, 255 * a)))
    cv.restore()


# ---------- skies / backgrounds ----------

def sky_sunset(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1100, [C("#2e3566"), C("#a35a5e"), C("#f0a85a")], [0, 0.5, 1]))
    sun_glow(cv, 760, 760, 560, "#ffcf8a", 200)


def sky_day(cv, T):
    sky(cv, "#4f8ac6", "#e9e2cf", H)
    sun_glow(cv, 820, 320, 520, "#fff2cf", 150)
    for i, (x, y, w) in enumerate(((220, 260, 260), (780, 190, 300), (520, 430, 200))):
        xx = (x + T * 7 * (1 + i * 0.3)) % (W + 400) - 200
        for k in range(4):
            cv.drawCircle(xx - w * 0.35 + k * w * 0.23, y - (k % 2) * 30, w * 0.22, fill(C("#fbf6ec", 210)))
        cv.drawRect(skia.Rect(xx - w * 0.45, y, xx + w * 0.45, y + w * 0.12), fill(C("#fbf6ec", 210)))


def under(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#3fa3b8"), C("#0f4a63"), C("#062433")]))
    rays(cv, 540, -200, T, n=8, a=26, spread=60, base=90, col="#bff3ff")


def studio(cv, col="#2a1c12"):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C(col), C("#0b0705")]))
    cv.drawCircle(540, 760, 900, rad(540, 760, 900, [C("#ffd9a0", 60), C("#ffd9a0", 0)]))


def night(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#0b1030"), C("#1c2a5a"), C("#0a0d1e")], [0, 0.6, 1]))
    stars(cv, T, 1.0, ymax=H * 0.6)


def xray_bg(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#04172a"), C("#020a14")]))
    p = stroke(C("#1d4a6a", 90), 2)
    for x in range(0, W + 1, 60): cv.drawLine(x, 0, x, H, p)
    for y in range(0, H + 1, 60): cv.drawLine(0, y, W, y, p)


def red_pulse(cv, T, col="#c0161c"):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#0a0405")))
    cv.drawCircle(540, 900, 900, rad(540, 900, 900, [C(col, 150 * (0.7 + 0.3 * math.sin(T * 12))), C("#000000", 0)]))


# ---------- effects ----------

def sparkles(cv, T, cx, cy, rx, ry, n=12, col="#fff3b0", seed=0):
    for i in range(n):
        ph = (T * 0.9 + i / n + seed) % 1
        x = cx + rx * math.sin(i * 2.39 + seed); y = cy + ry * math.cos(i * 1.71 + seed)
        r = 22 * math.sin(ph * math.pi)
        p = poly([(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25),
                  (x, y + r), (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)])
        cv.drawPath(p, fill(C(col, 230)))


def glow(cv, x, y, r, col="#ffd54a", a=150, T=0):
    a = a * (0.75 + 0.25 * math.sin(T * 6))
    cv.drawCircle(x, y, r, rad(x, y, r, [C(col, a), C(col, 0)]))



# ---------- EP07 helpers ----------
TOP = (540, 372)        # antenna tip in the "tower" plate (checked on stills)
TTOP = (540, 470)       # antenna tip in the "tower_top" plate
SKY_T = (275, 600)      # antenna tip in the "skyline" plate
SKY_P = (735, 1000)      # Panteão dome in the "skyline" plate


def night_cf(k=1.0):
    a = lerp(1, 0.38, k); b = lerp(1, 0.5, k); c = lerp(1, 0.85, k)
    return skia.ColorFilters.Matrix([a, 0, 0, 0, 0, 0, b, 0, 0, 0.01 * k, 0, 0, c, 0, 0.06 * k, 0, 0, 0, 1, 0])


def red_cf():
    return skia.ColorFilters.Matrix([0.9, 0.2, 0.1, 0, 0.06, 0.15, 0.35, 0.1, 0, 0, 0.12, 0.2, 0.3, 0, 0, 0, 0, 0, 1, 0])


def waves(cv, x, y, T, col="#ffd54a", n=4, maxr=520, speed=0.9, w=10, a0=-150, sweep=120, alpha=1.0):
    for k in range(n):
        ph = (T * speed + k / n) % 1
        r = 40 + ph * maxr
        a = 255 * (1 - ph) * alpha
        cv.drawArc(skia.Rect(x - r, y - r, x + r, y + r), a0, sweep, False, stroke(C(col, a), w))
        cv.drawArc(skia.Rect(x - r, y - r, x + r, y + r), a0 + 180, sweep, False, stroke(C(col, a), w))


def top_hat(cv, x, y, s, T):
    hy = y - 505 * s - 150 * s
    sd = int(T * 8) % 3
    brim = skia.Path(); brim.addRoundRect(skia.Rect(x - 130 * s, hy - 18 * s, x + 130 * s, hy + 14 * s), 10 * s, 10 * s)
    crown = skia.Path(); crown.addRoundRect(skia.Rect(x - 82 * s, hy - 175 * s, x + 82 * s, hy), 12 * s, 12 * s)
    T2.sk(cv, crown, "#1c1c22", 6, sd); T2.sk(cv, brim, "#1c1c22", 6, sd)
    cv.drawRect(skia.Rect(x - 80 * s, hy - 40 * s, x + 80 * s, hy - 14 * s), fill(C("#7a2f3a")))


def eiffel_t(cv, x, y, s, T, **k):
    y = min(y, 1285 + 340 * s)
    toon2(cv, x, y, s, T, outfit="eiffel", **k)
    top_hat(cv, x, y, s, T)


def headphones(cv, x, y, s, T):
    hc = y - 505 * s
    cv.drawArc(skia.Rect(x - 175 * s, hc - 200 * s, x + 175 * s, hc + 120 * s), 190, 160, False, stroke(C("#1a1a1a"), 16 * s))
    for sx in (-1, 1):
        cv.drawRoundRect(skia.Rect(x + sx * 168 * s - 28 * s, hc - 40 * s, x + sx * 168 * s + 28 * s, hc + 50 * s), 14 * s, 14 * s, fill(C("#2a2a2a")))


def paper(cv, r, T, a=1.0):
    cv.drawRoundRect(r.makeOffset(10, 14), 14, 14, fill(C("#000000", 110 * a)))
    pl = skia.Path(); pl.addRoundRect(r, 14, 14)
    cv.drawPath(pl, fill(C("#f1e8d0", 255 * a))); cv.drawPath(pl, ink(6, int(T * 8) % 3))


def text_c(cv, s, x, y, size, col="#1b1410", a=1.0, font=None):
    f = skia.Font(font or TF, size)
    cv.drawString(s, x - f.measureText(s) / 2, y, f, fill(C(col, 255 * a)))


def scribble_lines(cv, x0, y0, w, n, gap, T, a=1.0, seed=0):
    for i in range(n):
        ww = w * (0.6 + 0.4 * ((i * 37 + seed) % 10) / 10)
        cv.drawLine(x0, y0 + i * gap, x0 + ww, y0 + i * gap, stroke(C("#3a2c20", 200 * a), 7))


def morse(cv, lt, y, T, col="#ffd54a"):
    code = ".-- --. ..- .-. .-.. -."
    f = skia.Font(TF, 84)
    n = int(clamp(lt / 1.6) * len(code))
    s = code[:n]
    cv.drawString(s, 540 - f.measureText(code) / 2, y, f, stroke(C("#14100c"), 14))
    cv.drawString(s, 540 - f.measureText(code) / 2, y, f, fill(C(col)))


def stamp(cv, text, lt, x, y, size=110, col="#c0161c", ang=-12):
    if lt <= 0: return
    a = eout(lt / 0.2)
    f = skia.Font(TF, size); wd = f.measureText(text)
    cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(lerp(1.8, 1, a), lerp(1.8, 1, a))
    r = skia.Rect(-wd / 2 - 30, -size * 0.95, wd / 2 + 30, size * 0.35)
    cv.drawRoundRect(r, 16, 16, stroke(C(col, 235 * a), 12))
    cv.drawString(text, -wd / 2, 0, f, fill(C(col, 235 * a)))
    cv.restore()


def flags(cv, T, y=260):
    cols = ["#1b4a9a", "#ffffff", "#c0161c", "#ffd54a"]
    for i in range(14):
        x = 20 + i * 80
        yy = y + 30 * math.sin(i / 13 * math.pi)
        p = poly([(x, yy), (x + 60, yy), (x + 30, yy + 70 + 8 * math.sin(T * 6 + i))])
        cv.drawPath(p, fill(C(cols[i % 4]))); cv.drawPath(p, ink(4, int(T * 8) % 3))
    cv.drawPath(poly([(0, y), (1080, y + 10)], close=False), stroke(C("#14100c"), 4))


def smoke2(cv, x, y, T, s=1.0, col="#3a3532", alpha=200):
    for i in range(12):
        ph = (T * 0.35 + i / 12) % 1
        cx = x + ph * 380 * s + 30 * math.sin(T * 2 + i)
        cy = y - ph * 520 * s
        r = (40 + ph * 140) * s
        cv.drawCircle(cx, cy, r, fill(C(col, alpha * (1 - ph))))


def anemometer(cv, x, y, s, T):
    cv.drawLine(x, y, x, y + 160 * s, stroke(C("#14100c"), 8 * s))
    for k in range(3):
        a = T * 7 + k * 2.094
        ex, ey = x + math.cos(a) * 90 * s, y + math.sin(a) * 30 * s
        cv.drawLine(x, y, ex, ey, stroke(C("#14100c"), 6 * s))
        cv.drawCircle(ex, ey, 22 * s, fill(C("#ffd54a"))); cv.drawCircle(ex, ey, 22 * s, stroke(C("#14100c"), 5 * s))


def thermo(cv, x, y, s, T):
    r = skia.Rect(x - 22 * s, y - 220 * s, x + 22 * s, y)
    cv.drawRoundRect(r, 22 * s, 22 * s, fill(C("#f1e8d0"))); cv.drawRoundRect(r, 22 * s, 22 * s, stroke(C("#14100c"), 6 * s))
    lv = 120 + 50 * math.sin(T * 2)
    cv.drawRect(skia.Rect(x - 9 * s, y - lv * s, x + 9 * s, y), fill(C("#c0161c")))
    cv.drawCircle(x, y + 10 * s, 36 * s, fill(C("#c0161c"))); cv.drawCircle(x, y + 10 * s, 36 * s, stroke(C("#14100c"), 6 * s))


def bars(cv, k, T):
    for i in range(7):
        x = 110 + i * 143
        y1 = lerp(-1300, 0, ein(k))
        cv.drawRect(skia.Rect(x - 16, y1, x + 16, y1 + 1290), fill(C("#2a2a30")))
        cv.drawRect(skia.Rect(x - 16, y1, x - 6, y1 + 1290), fill(C("#6a6a75")))
    yb = lerp(-1300, 0, ein(k)) + 620
    cv.drawRect(skia.Rect(0, yb, W, yb + 30), fill(C("#2a2a30")))


# ---------- scenes ----------

def s01a(cv, lt, d, T):  # the tower had an expiry date
    sky_day(cv, T)
    plate(cv, "tower", P(lt, d, 1.0, 1.06), cy=900)
    stamp(cv, "PRAZO DE VALIDADE", T - ws(1, "prazo") - 0.3, 540, 330, 92)


def s01b(cv, lt, d, T):  # ...saved by an antenna
    sky_day(cv, T)
    plate(cv, "tower_top", P(lt, d, 1.0, 1.08), cx=TTOP[0], cy=TTOP[1])
    glow(cv, TTOP[0], TTOP[1], 220, "#ffd54a", 140, T)
    waves(cv, TTOP[0], TTOP[1], T, "#ffd54a", 4, 520)
    if T > ws(1, "antena"):
        banner(cv, "UMA ANTENA", T - ws(1, "antena"), y=1150, size=96, bg="#c08a1e", fg="#ffffff")


def s02(cv, lt, d, T):  # Paris, 1887
    sky_day(cv, T)
    plate(cv, "street", P(lt, d, 1.0, 1.06), cy=900)
    date_stamp(cv, "1887", lt - 0.3, y=360, size=190)
    banner(cv, "PARIS", lt - 0.05, y=540, size=90, bg="#1b4a9a", fg="#ffffff")


def s03(cv, lt, d, T):  # France wanted a giant monument for the 1889 Exposition
    sky_day(cv, T)
    plate(cv, "street", P(lt, d, 1.06, 1.12), cy=900)
    flags(cv, T, 150)
    toon(cv, 300, 1650, 1.0, T, outfit="inventor", expr="grin", pose="wave", look=0.6, seed=1)
    toon(cv, 790, 1660, 0.95, T, outfit="artist2", expr="joy", pose="hips", look=-0.6, seed=2)
    banner(cv, "EXPOSIÇÃO DE 1889", lt - 0.2, y=420, size=78, bg="#1b4a9a", fg="#ffd54a")


def s04a(cv, lt, d, T):  # engineer Gustave Eiffel
    sky_day(cv, T)
    plate(cv, "street", 1.12, cy=900, sigma=4)
    eiffel_t(cv, 560, 1700, 1.2, T, expr="smug", pose="point", look=0.6, seed=3)
    banner(cv, "GUSTAVE EIFFEL", lt - 0.2, y=330, size=90, bg="#2b2b33", fg="#ffd54a")


def s04b(cv, lt, d, T):  # iron tower of 300 m
    sky_day(cv, T)
    plate(cv, "tower", P(lt, d, 1.0, 1.04), cy=900)
    k = eout(clamp(lt / 1.0))
    x = 870; y0, y1 = 1490, 372
    yt = lerp(y0, y1, k)
    cv.drawLine(x, y0, x, yt, stroke(C("#ffd54a"), 10))
    cv.drawLine(x - 40, y0, x + 40, y0, stroke(C("#ffd54a"), 10))
    if k > 0.95:
        cv.drawLine(x - 40, y1, x + 40, y1, stroke(C("#ffd54a"), 10))
    pop_text(cv, "300 M", lt, 0.9, 760, 120, "#ffd54a")
    banner(cv, "TORRE DE FERRO", lt - 0.1, y=250, size=80, bg="#5a3b20", fg="#ffffff")


def s05(cv, lt, d, T):  # artists hated it
    red_pulse(cv, T, "#8a1f1f")
    plate(cv, "street", 1.1, cy=900, alpha=0.35, sigma=6)
    toon(cv, 280, 1650, 1.0, T, outfit="artist", expr="shock", pose="panic", seed=4)
    toon(cv, 800, 1650, 1.0, T, outfit="artist2", expr="worried", pose="hips", look=-0.5, seed=5)
    banner(cv, "OS ARTISTAS", lt - 0.1, y=330, size=96, bg="#8a1f1f", fg="#ffffff")


def s06a(cv, lt, d, T):  # ~40 signed a protest in the newspaper
    studio(cv, "#2a1c12")
    r = skia.Rect(120, 380, 960, 1230)
    paper(cv, r, T)
    text_c(cv, "LE TEMPS", 540, 500, 96, "#14100c", font=GREEK)
    cv.drawLine(160, 540, 920, 540, stroke(C("#14100c"), 6))
    text_c(cv, "PROTESTO", 540, 650, 92, "#8a1f1f")
    text_c(cv, "CONTRA A TORRE", 540, 740, 60, "#14100c")
    scribble_lines(cv, 170, 800, 740, 3, 44, T)
    n = int(clamp(lt / 1.8) * 40)
    for i in range(n):
        x = 190 + (i % 5) * 150; y = 960 + (i // 5) * 32
        cv.drawPath(poly([(x, y), (x + 30, y - 14), (x + 60, y + 6), (x + 100, y - 10)], close=False), stroke(C("#1d2a6a"), 4))
    if T > ws(6, "40"):
        pop_text(cv, "~40 ASSINATURAS", T - ws(6, "40"), 0.0, 300, 86, "#ffd54a")


def s06b(cv, lt, d, T):  # useless and monstrous
    red_pulse(cv, T, "#a01818")
    plate(cv, "tower", 1.05, cy=900, cf=red_cf())
    pop_text(cv, "INÚTIL", lt, ws(6, "inútil") - (T - lt), 380, 150, "#ffffff")
    pop_text(cv, "MONSTRUOSA", lt, ws(6, "monstruosa") - (T - lt), 560, 130, "#ffd54a")


def s07(cv, lt, d, T):  # a giant black factory chimney
    sky_day(cv, T)
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#6a5a50", 90)))
    plate(cv, "chimney", P(lt, d, 1.0, 1.06), cy=900)
    smoke2(cv, 640, 330, T, 1.0)
    banner(cv, "CHAMINÉ DE FÁBRICA", lt - 0.2, y=1130, size=76, bg="#2a2a30", fg="#ffffff")


def s08a(cv, lt, d, T):  # it went up anyway
    sky_sunset(cv, T)
    plate(cv, "tower_build", P(lt, d, 1.0, 1.06), cy=900)
    sparkles(cv, T, 540, 900, 260, 120, 8, "#fff3b0")
    banner(cv, "MESMO ASSIM...", lt - 0.1, y=330, size=90, bg="#5a3b20", fg="#ffffff")


def s08b(cv, lt, d, T):  # 1889 tallest in the world
    sky_day(cv, T)
    rays(cv, 540, 372, T, n=11, a=30, spread=360, base=90, col="#fff2c4")
    plate(cv, "tower", P(lt, d, 1.0, 1.06), cy=900)
    date_stamp(cv, "1889", lt - 0.05, y=250, size=150)
    if T > ws(8, "mais"):
        banner(cv, "A MAIS ALTA DO MUNDO", T - ws(8, "mais"), y=1150, size=72, bg="#c08a1e", fg="#ffffff")


def s09(cv, lt, d, T):  # permit only 20 years
    sky_day(cv, T)
    plate(cv, "tower", 1.1, cy=900, sigma=6, alpha=0.9)
    r = skia.Rect(200, 360, 880, 1000)
    paper(cv, r, T)
    text_c(cv, "LICENÇA", 540, 470, 90, "#14100c")
    scribble_lines(cv, 260, 540, 560, 4, 50, T)
    if T > ws(9, "20"):
        stamp(cv, "SÓ 20 ANOS", T - ws(9, "20"), 540, 880, 100, "#c0161c", -8)
    eiffel_t(cv, 860, 1660, 0.9, T, expr="worried", pose="think", look=-0.6, seed=3)


def s10a(cv, lt, d, T):  # 1910 → city
    sky_day(cv, T)
    plate(cv, "tower", P(lt, d, 1.0, 1.05), cy=900)
    date_stamp(cv, "1910", lt - 0.05, y=330, size=180)
    banner(cv, "PASSA PRA CIDADE", lt - 0.5, y=500, size=66, bg="#1b4a9a", fg="#ffffff")


def s10b(cv, lt, d, T):  # could be dismantled
    red_pulse(cv, T)
    sx = 8 * math.sin(T * 40) * clamp(lt / 0.3)
    plate(cv, "tower", 1.0, cy=900, dx=sx, cf=red_cf())
    k = eout(clamp(lt / 0.5))
    if k > 0:
        cv.drawLine(200, 400, lerp(200, 880, k), lerp(400, 1250, k), stroke(C("#ff2a2a"), 34))
        if lt > 0.25:
            k2 = eout(clamp((lt - 0.25) / 0.5))
            cv.drawLine(880, 400, lerp(880, 200, k2), lerp(400, 1250, k2), stroke(C("#ff2a2a"), 34))
    banner(cv, "DESMONTADA?", lt - 0.1, y=300, size=100, bg="#8a1f1f", fg="#ffffff")


def s11a(cv, lt, d, T):  # Eiffel rushed to prove it was useful
    sky_day(cv, T)
    plate(cv, "tower", 1.12, cy=900, sigma=3)
    k = clamp(lt / d)
    eiffel_t(cv, lerp(260, 760, k), 1680, 1.0, T, expr="determined", pose="point", look=1, seed=3, walk=T * 10)
    banner(cv, "PROVAR QUE ERA ÚTIL", lt - 0.2, y=330, size=72, bg="#2b2b33", fg="#ffd54a")


def s11b(cv, lt, d, T):  # a lab at the top
    sky_day(cv, T)
    plate(cv, "tower_top", P(lt, d, 1.0, 1.06), cx=540, cy=700)
    anemometer(cv, 240, 760, 1.2, T)
    thermo(cv, 860, 1000, 1.1, T)
    banner(cv, "LABORATÓRIO", lt - 0.1, y=300, size=96, bg="#1b4a9a", fg="#ffffff")


def s12(cv, lt, d, T):  # twist
    red_pulse(cv, T)
    zoom(cv, lerp(1.0, 1.3, eout(lt / d)), 540, 820)
    eiffel_t(cv, 540, 1720, 1.55, T, expr="shock", seed=3)


def s13a(cv, lt, d, T):  # 1898, an inventor at the top
    sky_day(cv, T)
    plate(cv, "tower_top", P(lt, d, 1.0, 1.08), cx=TTOP[0], cy=TTOP[1])
    date_stamp(cv, "1898", lt - 0.05, y=330, size=170)
    toon(cv, 800, 1650, 0.95, T, outfit="inventor", expr="grin", pose="point", look=-1, seed=6)
    banner(cv, "UM INVENTOR", lt - 0.5, y=500, size=70, bg="#5a4632", fg="#ffd54a")


def s13b(cv, lt, d, T):  # radio message to the Panthéon
    sky_sunset(cv, T)
    plate(cv, "skyline", P(lt, d, 1.0, 1.04), cy=900)
    k = clamp(lt / d)
    for i in range(6):
        ph = (T * 0.8 + i / 6) % 1
        x = lerp(SKY_T[0], SKY_P[0], ph); y = lerp(SKY_T[1], SKY_P[1] - 120, ph) - 160 * math.sin(ph * math.pi)
        cv.drawArc(skia.Rect(x - 40, y - 40, x + 40, y + 40), -60, 120, False, stroke(C("#ffd54a", 255 * math.sin(ph * math.pi)), 9))
    glow(cv, SKY_T[0], SKY_T[1], 120, "#ffd54a", 140, T)
    banner(cv, "PANTEÃO", lt - 0.8, y=SKY_P[1] - 260, size=60, bg="#1b4a9a", fg="#ffffff")
    banner(cv, "MENSAGEM DE RÁDIO", lt - 0.1, y=300, size=76, bg="#c08a1e", fg="#ffffff")


def s14(cv, lt, d, T):  # 300 m = perfect antenna
    sky_day(cv, T)
    plate(cv, "tower", P(lt, d, 1.0, 1.05), cy=900)
    waves(cv, TOP[0], TOP[1], T, "#ffd54a", 5, 700, 0.8, 12)
    glow(cv, TOP[0], TOP[1], 160, "#ffd54a", 160, T)
    banner(cv, "A ANTENA PERFEITA", lt - 0.2, y=1150, size=80, bg="#c08a1e", fg="#ffffff")


def s15a(cv, lt, d, T):  # the army joined
    studio(cv, "#2a2015")
    plate(cv, "radio", P(lt, d, 1.0, 1.05), cy=900)
    toon(cv, 820, 1660, 1.0, T, outfit="soldier", expr="determined", pose="hips", look=-0.6, seed=7)
    banner(cv, "O EXÉRCITO", lt - 0.1, y=300, size=96, bg="#3f5f8f", fg="#ffffff")


def globe(cv, x, y, r, T):
    p = skia.Path(); p.addCircle(x, y, r)
    cv.drawPath(p, fill(C("#2a6db0")))
    cv.save(); cv.clipPath(p, doAntiAlias=True)
    for i, (dx, dy, rr) in enumerate(((-0.3, -0.3, 0.35), (0.25, -0.1, 0.3), (0.1, 0.45, 0.25), (-0.45, 0.35, 0.2))):
        q = skia.Path(); q.addOval(skia.Rect(x + (dx - rr) * r + (T * 30 % (2 * r)) * 0, y + (dy - rr * 0.7) * r, x + (dx + rr) * r, y + (dy + rr * 0.7) * r))
        cv.drawPath(q, fill(C("#6fae4a")))
    cv.restore()
    cv.drawPath(p, ink(7, int(T * 8) % 3))


def s15b(cv, lt, d, T):  # 1908: 6,000 km
    night(cv, T)
    globe(cv, 540, 820, 330, T)
    px, py = 470, 600
    waves(cv, px, py, T, "#ffd54a", 5, 900, 0.7, 10, -180, 360, 0.9)
    cv.drawCircle(px, py, 16, fill(C("#c0161c")))
    date_stamp(cv, "1908", lt - 0.05, y=300, size=150)
    if T > ws(15, "6.000"):
        pop_text(cv, "6.000 KM", T - ws(15, "6.000"), 0.0, 1240, 130, "#ffd54a")


def s16(cv, lt, d, T):  # renewed for 70 years
    sky_day(cv, T)
    rays(cv, 540, 372, T, n=11, a=30, spread=360, base=90, col="#fff2c4")
    plate(cv, "tower", 1.04, cy=900)
    date_stamp(cv, "1910", lt - 0.05, y=260, size=130)
    if T > ws(16, "renovada"):
        stamp(cv, "RENOVADA", T - ws(16, "renovada"), 540, 520, 110, "#1f8a3a", -8)
    if T > ws(16, "70"):
        pop_text(cv, "+70 ANOS", T - ws(16, "70"), 0.0, 1150, 130, "#ffd54a")


def search_beams(cv, T):
    for k, (x, sp) in enumerate(((200, 0.5), (880, -0.4))):
        a = math.radians(-90 + 25 * math.sin(T * sp + k))
        p = poly([(x, 1500), (x + math.cos(a - 0.08) * 1800, 1500 + math.sin(a - 0.08) * 1800),
                  (x + math.cos(a + 0.08) * 1800, 1500 + math.sin(a + 0.08) * 1800)])
        cv.drawPath(p, fill(C("#fff6c8", 40)))


def s17a(cv, lt, d, T):  # WWI
    night(cv, T)
    search_beams(cv, T)
    plate(cv, "tower", P(lt, d, 1.0, 1.05), cy=900, cf=night_cf())
    banner(cv, "PRIMEIRA GUERRA", lt - 0.1, y=300, size=86, bg="#3f5f8f", fg="#ffffff")


def s17b(cv, lt, d, T):  # the big ear
    night(cv, T)
    plate(cv, "tower", 1.08, cy=900, cf=night_cf())
    # incoming waves (converge to the antenna)
    for k in range(5):
        ph = 1 - (T * 0.8 + k / 5) % 1
        r = 40 + ph * 700
        cv.drawArc(skia.Rect(TOP[0] - r, TOP[1] - r, TOP[0] + r, TOP[1] + r), -160, 140, False, stroke(C("#7fe9ff", 255 * (1 - ph)), 10))
        cv.drawArc(skia.Rect(TOP[0] - r, TOP[1] - r, TOP[0] + r, TOP[1] + r), 20, 140, False, stroke(C("#7fe9ff", 255 * (1 - ph)), 10))
    glow(cv, TOP[0], TOP[1], 150, "#7fe9ff", 150, T)
    banner(cv, "O GRANDE OUVIDO", lt - 0.1, y=1150, size=86, bg="#0f3a5a", fg="#ffd54a")


def s18a(cv, lt, d, T):  # listening to German messages
    studio(cv, "#1a140e")
    plate(cv, "radio", 1.08, cy=900, dx=-60)
    x, y, s = 760, 1660, 1.0
    toon(cv, x, y, s, T, outfit="soldier", expr="wide", pose="think", look=-0.8, seed=7)
    headphones(cv, x, min(y, 1285 + 340 * s), s, T)
    morse(cv, lt, 330, T)
    banner(cv, "MENSAGENS ALEMÃS", lt - 0.2, y=470, size=70, bg="#3f5f8f", fg="#ffffff")


def s18b(cv, lt, d, T):  # helped arrest spy Mata Hari
    studio(cv, "#140a0c")
    cv.drawCircle(540, 900, 700, rad(540, 900, 700, [C("#c0161c", 70), C("#000000", 0)]))
    toon(cv, 540, 1700, 1.2, T, outfit="spy", expr="shock", pose="panic", seed=8)
    if T > ws(18, "prender"):
        bars(cv, clamp((T - ws(18, "prender")) / 0.35), T)
    banner(cv, "A ESPIÃ MATA HARI", lt - 0.2, y=300, size=80, bg="#6a1b2a", fg="#ffd54a")


def s19a(cv, lt, d, T):  # the tower the artists wanted to tear down
    sky_day(cv, T)
    plate(cv, "tower", P(lt, d, 1.08, 1.0), cy=900)
    toon(cv, 250, 1650, 0.9, T, outfit="artist", expr="worried", pose="hips", look=0.6, seed=4)
    toon(cv, 830, 1650, 0.9, T, outfit="artist2", expr="sad", pose="stand", look=-0.6, seed=5)


def s19b(cv, lt, d, T):  # ...saved by an antenna
    sky_day(cv, T)
    rays(cv, TTOP[0], TTOP[1], T, n=11, a=34, spread=360, base=90, col="#ffe6b0")
    plate(cv, "tower_top", P(lt, d, 1.0, 1.08), cx=TTOP[0], cy=TTOP[1])
    waves(cv, TTOP[0], TTOP[1], T, "#ffd54a", 4, 560)
    sparkles(cv, T, TTOP[0], TTOP[1] + 200, 360, 300, 10)
    banner(cv, "SALVA POR", lt - 0.1, y=1000, size=90, bg="#1b2a4a", fg="#ffffff")
    banner(cv, "UMA ANTENA", lt - 0.4, y=1140, size=100, bg="#c08a1e", fg="#ffffff")


SHOTS = []


def add(s, e, fn, *a):
    SHOTS.append((s, e, fn, a))


add(0, ws(1, "salvou") - 0.25, s01a)
add(ws(1, "salvou") - 0.25, L[2]["s"], s01b)
add(L[2]["s"], L[3]["s"], s02)
add(L[3]["s"], L[4]["s"], s03)
add(L[4]["s"], ws(4, "torre"), s04a)
add(ws(4, "torre"), L[5]["s"], s04b)
add(L[5]["s"], L[6]["s"], s05)
add(L[6]["s"], ws(6, "chamando"), s06a)
add(ws(6, "chamando"), L[7]["s"], s06b)
add(L[7]["s"], L[8]["s"], s07)
add(L[8]["s"], ws(8, "em"), s08a)
add(ws(8, "em"), L[9]["s"], s08b)
add(L[9]["s"], L[10]["s"], s09)
add(L[10]["s"], ws(10, "podia"), s10a)
add(ws(10, "podia"), L[11]["s"], s10b)
add(L[11]["s"], ws(11, "transformou"), s11a)
add(ws(11, "transformou"), L[12]["s"], s11b)
add(L[12]["s"], L[13]["s"], s12)
add(L[13]["s"], ws(13, "mensagem"), s13a)
add(ws(13, "mensagem"), L[14]["s"], s13b)
add(L[14]["s"], L[15]["s"], s14)
add(L[15]["s"], ws(15, "em"), s15a)
add(ws(15, "em"), L[16]["s"], s15b)
add(L[16]["s"], L[17]["s"], s16)
add(L[17]["s"], ws(17, "a"), s17a)
add(ws(17, "a"), L[18]["s"], s17b)
add(L[18]["s"], ws(18, "e"), s18a)
add(ws(18, "e"), L[19]["s"], s18b)
add(L[19]["s"], ws(19, "foi"), s19a)
add(ws(19, "foi"), DUR + 0.01, s19b)


def render_frame(surface, fi):
    T = fi / FPS
    cv = surface.getCanvas(); cv.clear(C("#000000"))
    for s, e, fn, a in SHOTS:
        if s <= T < e:
            cv.save(); fn(cv, T - s, e - s, T, *a); cv.restore(); break
    vignette(cv, 140)
    draw_caption(cv, CHUNKS, T, y=CAP_Y)
    grain(cv, fi, 16)


if __name__ == "__main__":
    a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    surf = skia.Surface(W, H)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fi in range(a, b):
        render_frame(surf, fi)
        ff.stdin.write(surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).tobytes())
    ff.stdin.close(); ff.wait()

