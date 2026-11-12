"""EP03 — Vasa (1628), versão PT-BR. 3D inked plates + sketch characters. usage: render.py timings.json a b out.mp4 kitdir platesdir"""
import sys, json, math, subprocess
sys.path.insert(0, sys.argv[5])
from gfx import *
import gfx
import toon2 as T2
from toon2 import toon2, ink, sk

gfx.KEYWORDS.clear()
gfx.KEYWORDS.update({"guerra", "porto", "suécia", "1628", "vasa", "64", "canhões", "centenas", "poderosos", "problema",
                     "trinta", "três", "virar", "calados", "agosto", "rajada", "inclinou", "água", "aberturas", "trezentos",
                     "metros", "morreram", "reviravolta", "teredo", "madeira", "fundo", "anos", "1961", "superfície",
                     "noventa", "oito", "original", "milhão", "mundo", "rei", "almirante", "parar", "sabiam"})
T2.OUTFITS["king"] = dict(body="#8a1f2d", trim="#e2b54b", hat="none")

TJ = json.load(open(sys.argv[1]))
PL = sys.argv[6]
L = {l["i"]: l for l in TJ["lines"]}
DUR = TJ["duration"]
CHUNKS = build_chunks(TJ)
CAP_Y = 1370
_IMG = {}
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear)


def img(name):
    if name not in _IMG:
        _IMG[name] = skia.Image.open(f"{PL}/{name}_ink.png")
    return _IMG[name]


def plate(cv, name, z=1.0, cx=W / 2, cy=H / 2, dx=0, dy=0, sigma=0, alpha=1.0, rot=0, tint=None, bright=None):
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
    cv.drawImageRect(im, skia.Rect(0, 0, W, H), SAMP, p)
    cv.restore()


def ws(i, word, nth=0):
    cl = lambda w: w["w"].strip(".,!?'\"").lower()
    hits = [w for w in L[i]["words"] if cl(w) == word.lower()] or [w for w in L[i]["words"] if cl(w).startswith(word.lower())]
    return hits[nth]["s"]


_ds, _bn = date_stamp, banner


def _fit(text, size, maxw=930):
    while skia.Font(TF, size).measureText(text) > maxw and size > 40: size -= 4
    return size


def date_stamp(cv, text, lt, y=430, size=170, **k): _ds(cv, text, lt, y=y, size=_fit(text, size), **k)
def banner(cv, text, lt, y=420, size=78, **k): _bn(cv, text, lt, y=y, size=_fit(text, size, 900), **k)


def P(lt, d, a=1.0, b=1.08):
    return lerp(a, b, ease(lt / d))


# ---------- 2D layers ----------

def sky_day(cv, T):
    sky(cv, "#4f8fd0", "#f1e7d2", H); sun_glow(cv, 860, 420, 560, "#fff4cf", 170)
    for i, (x, y, w) in enumerate(((220, 330, 260), (760, 220, 300), (520, 520, 220))):
        xx = (x + T * 8 * (1 + i * 0.3)) % (W + 400) - 200
        for k in range(4):
            cv.drawCircle(xx - w * 0.35 + k * w * 0.23, y - (k % 2) * 30, w * 0.22, fill(C("#ffffff", 210)))
        cv.drawRect(skia.Rect(xx - w * 0.45, y, xx + w * 0.45, y + w * 0.12), fill(C("#ffffff", 210)))


def sky_sunset(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1000, [C("#2b3a73"), C("#8c6fa0"), C("#f6a65e"), C("#ffd79a")], [0, 0.45, 0.85, 1]))
    sun_glow(cv, 300, 820, 620, "#ffe2a8", 220); cv.drawCircle(300, 820, 70, fill(C("#fff2d0")))


def sky_grey(cv, T):
    sky(cv, "#59657a", "#c9c3b6", H)


def under_bg(cv, T, dark=0.0):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#3f9fb8"), C("#0f4a62"), C("#031a22")], [0, 0.45, 1]))
    rays(cv, 540, -300, T, col="#cff0ff", n=7, a=24, spread=60)
    if dark: cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#000a10", 255 * dark)))


def wind(cv, T, k=1.0, a=170):
    for i in range(int(10 * k) + 4):
        ph = (T * (0.9 + (i % 3) * 0.2) + i * 0.37) % 1.0
        x = -500 + ph * (W + 900); y = 250 + (i * 173) % 900
        p = skia.Path(); p.moveTo(x, y)
        p.cubicTo(x + 120, y - 30, x + 240, y + 30, x + 380, y - 10)
        cv.drawPath(p, stroke(C("#ffffff", a * math.sin(ph * math.pi)), 6))
        p2 = skia.Path(); p2.addArc(skia.Rect(x + 340, y - 60, x + 420, y + 20), 90, 250)
        cv.drawPath(p2, stroke(C("#ffffff", a * math.sin(ph * math.pi)), 5))


def splash(cv, x, y, p, n=18, s=1.0):
    if p <= 0 or p >= 1: return
    for i in range(n):
        a = -math.pi * (0.1 + 0.8 * i / n)
        v = (300 + (i * 53) % 250) * s
        px = x + math.cos(a) * v * p; py = y + math.sin(a) * v * p + 900 * p * p * s
        r = (16 - 10 * p) * s
        cv.drawCircle(px, py, r, fill(C("#eaf7ff", 230 * (1 - p)))); cv.drawCircle(px, py, r, stroke(C("#231a14", 160 * (1 - p)), 3))


def crown(cv, x, y, s):
    """crown on a toon2 standing at (x,y) scale s"""
    hy = y - 505 * s - 165 * s
    pts = [(-110, 25), (-120, -70), (-60, -20), (0, -95), (60, -20), (120, -70), (110, 25)]
    cv.save(); cv.translate(x, hy + 10 * s); cv.scale(s, s)
    sk(cv, poly(pts), "#f2c14e", 7, 1)
    for gx, gc in ((-60, "#d6372b"), (0, "#2f6fd6"), (60, "#d6372b")):
        cv.drawCircle(gx, 0, 13, fill(C(gc)))
    cv.restore()


def sailor_run(cv, T, x0, x1, y, s, ph, expr="shock"):
    k = 0.5 + 0.5 * math.sin(T * 2.2 + ph)
    x = lerp(x0, x1, k)
    toon2(cv, x, y, s, T, outfit="sailor", expr=expr, pose="panic", walk=T * 14 + ph, look=(1 if math.cos(T * 2.2 + ph) > 0 else -1), shadow=True, seed=ph)


def worm(cv, x, y, s, T, seed=0):
    p = skia.Path()
    for i in range(9):
        xx = x + i * 16 * s; yy = y + 12 * s * math.sin(T * 6 + i * 0.8 + seed)
        (p.moveTo if i == 0 else p.lineTo)(xx, yy)
    cv.drawPath(p, stroke(C("#231a14"), 26 * s)); cv.drawPath(p, stroke(C("#e9d7b0"), 17 * s))
    cv.drawCircle(x + 8 * 16 * s, y + 12 * s * math.sin(T * 6 + 6.4 + seed), 13 * s, fill(C("#e9d7b0")))
    cv.drawCircle(x + 8 * 16 * s + 3, y - 4 + 12 * s * math.sin(T * 6 + 6.4 + seed), 4 * s, fill(C("#231a14")))


def red_pulse(cv, T, col="#c0161c"):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#0a0405")))
    cv.drawCircle(540, 900, 900, rad(540, 900, 900, [C(col, 150 * (0.7 + 0.3 * math.sin(T * 12))), C("#000000", 0)]))


# plate anchors (frame px)
A = dict(lean_pivot=(560, 1180), port_water0=1180, port_water1=760)


# ---------- scenes ----------

def s01(cv, lt, d, T):  # hook: the ship goes down in the harbor
    sky_grey(cv, T)
    plate(cv, "lean_sea", P(lt, d, 1.0, 1.06))
    k = ease(lt / d)
    px, py = A["lean_pivot"]
    cv.save(); cv.translate(px, py + 260 * k); cv.rotate(lerp(6, 24, k)); cv.translate(-px, -py)
    cv.save(); cv.clipRect(skia.Rect(0, 0, W, py + 40)); plate(cv, "lean_ship", P(lt, d, 1.0, 1.06)); cv.restore()
    cv.restore()
    near_sea(cv, py + 40, T, "#3c7fa3", "#0e3b57", 14, ca=150)
    for i in range(16):
        ph = (lt * 0.9 + i / 16) % 1
        cv.drawCircle(300 + i * 34, py + 30 - ph * 60, 10 * (1 - ph) + 3, fill(C("#eaf7ff", 220 * (1 - ph))))
    toon2(cv, 820, 2060, 0.95, T, outfit="sailor", expr="shock", pose="panic", look=-0.8, shadow=False)


def s02(cv, lt, d, T):
    sky_sunset(cv, T)
    plate(cv, "city", P(lt, d, 1.0, 1.08), cy=1000)
    date_stamp(cv, "SUÉCIA, 1628", lt - 0.1, y=330, size=118)


def s03(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "shipyard", 1.06, sigma=5)
    x, y, s = 540, 1690, 1.2
    toon2(cv, x, y, s, T, outfit="king", expr="grin", pose="point", look=0.6)
    crown(cv, x, y, s)
    banner(cv, "REI GUSTAVO ADOLFO", lt - 0.2, y=320, size=74)


def s04(cv, lt, d, T):
    sky_sunset(cv, T)
    plate(cv, "stern", P(lt, d, 1.0, 1.1), cy=900)
    banner(cv, "VASA", lt - 0.1, y=330, size=110, bg="#1b2a4a", fg="#ffd54a")


def s05a(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "gunports", P(lt, d, 1.0, 1.1), cy=900)
    near_sea(cv, A["port_water0"], T, "#2c8fbd", "#0b3f63", 12, ca=120)
    date_stamp(cv, "64 CANHÕES", lt - 0.2, y=330, size=130)


def s05b(cv, lt, d, T):
    sky_sunset(cv, T)
    plate(cv, "stern", P(lt, d, 1.12, 1.22), cx=300, cy=820)
    for i in range(14):
        ph = (T * 0.8 + i / 14) % 1
        x = 120 + (i * 151) % 700; y = 500 + (i * 211) % 700
        r = 26 * math.sin(ph * math.pi)
        p = poly([(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25), (x, y + r), (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)])
        cv.drawPath(p, fill(C("#fff3b0", 240)))


def s06(cv, lt, d, T):
    sky_day(cv, T)
    rays(cv, 600, 500, T, col="#fff0c8", n=10, a=30, spread=200, base=270)
    plate(cv, "vasa_hero", P(lt, d, 1.0, 1.1), cy=1000)


def s07(cv, lt, d, T):
    red_pulse(cv, T)
    zoom(cv, lerp(1.0, 1.3, eout(lt / d)), 540, 820)
    toon2(cv, 540, 1720, 1.7, T, outfit="sailor", expr="worried", look=-0.4)


def deck_scene(cv, lt, d, T, rock, admiral_t=None):
    sky_day(cv, T)
    ang = rock * math.sin(T * 2.2)
    cv.save(); cv.translate(540, 1500); cv.rotate(ang); cv.translate(-540, -1500)
    plate(cv, "deck", 1.08)
    sailor_run(cv, T, 120, 960, 1960, 0.62, 0.0)
    sailor_run(cv, T, 200, 900, 1850, 0.5, 0.5)
    sailor_run(cv, T, 300, 820, 1760, 0.4, 1.0)
    cv.restore()
    if admiral_t is not None and T > admiral_t:
        k = eout((T - admiral_t) / 0.5)
        toon2(cv, lerp(1300, 860, k), 2050, 0.95, T, outfit="officer", expr="shock", pose="wave", look=-0.8)
        f = skia.Font(TF, 120)
        if T > admiral_t + 0.3:
            a = eout((T - admiral_t - 0.3) / 0.2)
            cv.save(); cv.translate(540, 360); cv.scale(lerp(1.4, 1, a), lerp(1.4, 1, a))
            r = skia.Rect(-290, -110, 290, 40)
            cv.drawRoundRect(r, 24, 24, fill(C("#d6372b", 255 * a))); cv.drawRoundRect(r, 24, 24, stroke(C("#1b1410", 255 * a), 8))
            cv.drawString("PAREM!", -f.measureText("PAREM!") / 2, 0, f, fill(C("#ffffff", 255 * a)))
            cv.restore()


def s08(cv, lt, d, T):
    deck_scene(cv, lt, d, T, 1.5)
    date_stamp(cv, "30 MARINHEIROS", lt - 1.2, y=330, size=130)


def s09(cv, lt, d, T, adm):
    deck_scene(cv, lt, d, T, lerp(3, 9, ease(lt / d)), adm)
    n = 1 + int(clamp(lt / 1.6) * 2.99)
    f = skia.Font(TF, 92)
    if T < adm:
        txt = f"CORRIDA {n} DE 3"
        cv.drawString(txt, 540 - f.measureText(txt) / 2 + 5, 345, f, fill(C("#000000", 110)))
        cv.drawString(txt, 540 - f.measureText(txt) / 2, 340, f, stroke(C("#14100c"), 14))
        cv.drawString(txt, 540 - f.measureText(txt) / 2, 340, f, fill(C("#ffffff")))


def s10(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "lean_sea", 1.05, sigma=4)
    px, py = A["lean_pivot"]
    cv.save(); cv.translate(px, py); cv.rotate(14 * math.sin(T * 2.4)); cv.translate(-px, -py)
    cv.save(); cv.clipRect(skia.Rect(-400, -400, W + 400, py + 40)); plate(cv, "lean_ship", 1.05, sigma=4); cv.restore()
    cv.restore()
    near_sea(cv, py + 40, T, "#3c7fa3", "#0e3b57", 14, ca=150)
    toon2(cv, 540, 1720, 1.3, T, outfit="officer", expr="worried", look=0.5, tears=True)


def s11(cv, lt, d, T, t2):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#23180f"), C("#090605")]))
    cv.drawCircle(540, 1300, 700, rad(540, 1300, 700, [C("#ffd27a", 70), C("#ffd27a", 0)]))
    silent = T > t2
    for i, (x, of) in enumerate(((220, "sailor"), (540, "officer"), (860, "sailor"))):
        toon2(cv, x, 1560, 0.82, T, outfit=of, expr="worried" if not silent else "closed", look=(-0.6, 0, 0.6)[i], seed=i)
        if silent:  # finger on lips
            hy = 1560 - 505 * 0.82
            cv.drawLine(x, hy + 40, x, hy + 110, stroke(C("#231a14"), 9))
    if silent:
        f = skia.Font(TF, 140)
        a = eout((T - t2) / 0.3)
        cv.drawString("SHHH...", 540 - f.measureText("SHHH...") / 2, 420, f, stroke(C("#14100c", 255 * a), 16))
        cv.drawString("SHHH...", 540 - f.measureText("SHHH...") / 2, 420, f, fill(C("#ffd54a", 255 * a)))


def s12(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "harbor", P(lt, d, 1.0, 1.08), dx=lerp(-20, 30, ease(lt / d)))
    date_stamp(cv, "10 DE AGOSTO DE 1628", lt - 0.1, y=330, size=104)


def lean_scene(cv, lt, d, T, a0, a1, wk, sh=0, sink=0):
    if sh: cv.translate(*shake(lt, sh, 4))
    sky_grey(cv, T)
    plate(cv, "lean_sea", 1.04)
    px, py = A["lean_pivot"]
    k = ease(clamp(lt / min(d, 1.2)))
    cv.save(); cv.translate(px, py + sink); cv.rotate(lerp(a0, a1, k) + 1.2 * math.sin(T * 3)); cv.translate(-px, -py)
    cv.save(); cv.clipRect(skia.Rect(-400, -400, W + 400, py + 40 - sink)); plate(cv, "lean_ship", 1.04); cv.restore()
    cv.restore()
    near_sea(cv, py + 40, T, "#3c7fa3", "#0e3b57", 14, ca=150)
    if wk: wind(cv, T, wk)


def s13(cv, lt, d, T): lean_scene(cv, lt, d, T, 0, 6, 1.0)
def s14(cv, lt, d, T): lean_scene(cv, lt, d, T, 6, 16, 0.6, 10)
def s15(cv, lt, d, T): lean_scene(cv, lt, d, T, 16, 26, 1.6, 18)


def s16(cv, lt, d, T):
    k = ease(lt / d)
    cv.translate(*shake(lt, 8, 1))
    sky_day(cv, T)
    plate(cv, "gunports", 1.05, rot=lerp(4, 12, k), cy=900)
    wy = lerp(A["port_water0"], A["port_water1"], k)
    for i in range(10):  # water jets into ports
        x = 120 + i * 95
        cv.drawLine(x, wy, x + 20, wy - 60 - 20 * math.sin(T * 9 + i), stroke(C("#d9f2ff", 200), 10))
    near_sea(cv, wy, T * 2, "#2c8fbd", "#0b3f63", 22, ca=200)
    bubbles(cv, T, 18, 4)


def s17(cv, lt, d, T, t2):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#2d6f93")))
    for i in range(18):
        y = 120 + i * 100
        cv.drawPath(wave_path(y, T, 4, 0.02, 1, y2=y + 1), stroke(C("#ffffff", 40), 3))
    land = poly([(0, 0), (W, 0), (W, 330), (760, 420), (520, 360), (300, 470), (0, 420)])
    cv.drawPath(land, fill(C("#7c9a59"))); cv.drawPath(land, stroke(C("#231a14"), 7))
    land2 = poly([(0, H), (W, H), (W, 1700), (700, 1620), (380, 1760), (0, 1680)])
    cv.drawPath(land2, fill(C("#7c9a59"))); cv.drawPath(land2, stroke(C("#231a14"), 7))
    for i in range(7):  # little houses on shore
        x = 60 + i * 140; cv.drawRect(skia.Rect(x, 300 - (i % 3) * 30, x + 70, 360 - (i % 3) * 30), fill(C("#d99a52")))
    x0, y0, x1, y1 = 200, 1180, 760, 760
    k = ease(clamp(lt / 2.2))
    n = 26
    for i in range(int(n * k)):
        t = i / n
        cv.drawCircle(lerp(x0, x1, t), lerp(y0, y1, t) + 40 * math.sin(t * 3), 9, fill(C("#ffffff")))
    xe, ye = lerp(x0, x1, k), lerp(y0, y1, k) + 40 * math.sin(k * 3)
    cv.drawCircle(x0, y0, 22, fill(C("#ffd54a"))); cv.drawCircle(x0, y0, 22, stroke(C("#231a14"), 6))
    cv.save(); cv.translate(xe, ye); cv.rotate(-35)
    sk(cv, poly([(-50, -16), (40, -16), (62, 0), (40, 16), (-50, 16)]), "#6b3b1c", 6, 0)
    cv.restore()
    if k >= 1:
        cv.drawLine(xe - 40, ye - 40, xe + 40, ye + 40, stroke(C("#e23b2e"), 18)); cv.drawLine(xe + 40, ye - 40, xe - 40, ye + 40, stroke(C("#e23b2e"), 18))
    date_stamp(cv, "1.300 METROS", lt - 0.3, y=560, size=110)
    if T > t2:
        banner(cv, "< 1,5 KM", T - t2, y=1620, size=90, bg="#1b2a4a", fg="#ffd54a")


def s18(cv, lt, d, T):
    sky_grey(cv, T)
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#1a2030", 90)))
    plate(cv, "lean_sea", 1.04, tint=("#9aa6b8",))
    px, py = A["lean_pivot"]
    sink = lerp(420, 520, ease(lt / d))
    cv.save(); cv.translate(px, py + sink); cv.rotate(30); cv.translate(-px, -py)
    cv.save(); cv.clipRect(skia.Rect(-400, -400, W + 400, py + 40 - sink)); plate(cv, "lean_ship", 1.04, tint=("#9aa6b8",)); cv.restore()
    cv.restore()
    near_sea(cv, py + 40, T * 0.6, "#2f5b75", "#0b2436", 10, ca=90)
    for i in range(8):
        ph = (T * 0.5 + i / 8) % 1
        cv.drawCircle(380 + i * 50, py + 30, 30 * ph, stroke(C("#ffffff", 160 * (1 - ph)), 4))
    date_stamp(cv, "30+ MORTOS", lt - 0.2, y=330, size=120)


def s19(cv, lt, d, T):
    red_pulse(cv, T)
    zoom(cv, lerp(1.0, 1.4, eout(lt / d)), 540, 820)
    toon2(cv, 540, 1720, 1.75, T, outfit="sailor", expr="shock")


def s20(cv, lt, d, T, tw):
    under_bg(cv, T)
    plate(cv, "wreck", 1.0, cy=1000, dy=120)
    bubbles(cv, T, 25, 2)
    k = ease(clamp((T - tw) / 1.6)) if T > tw else 0
    for i in range(3):
        x = lerp(-300, 250 + i * 40, ease(clamp(lt / 1.5))) - 700 * k
        worm(cv, x, 520 + i * 170, 1.6 - i * 0.2, T, i)
    if T > tw:
        a = eout((T - tw) / 0.25)
        cv.save(); cv.translate(440, 680); cv.scale(lerp(1.6, 1, a), lerp(1.6, 1, a))
        cv.drawCircle(0, 0, 230, stroke(C("#e23b2e", 255 * a), 26))
        cv.drawLine(-160, 160, 160, -160, stroke(C("#e23b2e", 255 * a), 26))
        cv.restore()
        banner(cv, "SEM TEREDO", T - tw, y=300, size=80)


def s21(cv, lt, d, T):
    under_bg(cv, T, 0.25)
    plate(cv, "wreck", P(lt, d, 1.0, 1.08), cy=1000, dy=120)
    for i in range(5):  # fish silhouettes
        x = (i * 260 + T * 60 * (1 + i % 2)) % (W + 300) - 150; y = 420 + i * 110
        p = poly([(x, y), (x - 50, y - 22), (x - 90, y), (x - 50, y + 22)])
        cv.drawPath(p, fill(C("#062430", 200))); cv.drawPath(poly([(x - 85, y), (x - 115, y - 20), (x - 115, y + 20)]), fill(C("#062430", 200)))
    bubbles(cv, T, 20, 3)


def s22(cv, lt, d, T):
    under_bg(cv, T, 0.45)
    plate(cv, "wreck", P(lt, d, 1.08, 1.14), cy=1000, dy=120, tint=("#8fb3b8",))
    yr = int(lerp(1628, 1961, clamp(lt / (d * 0.85))))
    f = skia.Font(TF, 200)
    s_ = str(yr)
    cv.drawString(s_, 540 - f.measureText(s_) / 2, 400, f, stroke(C("#14100c"), 18))
    cv.drawString(s_, 540 - f.measureText(s_) / 2, 400, f, fill(C("#ffffff")))
    banner(cv, "333 ANOS", lt - 0.2, y=560, size=86, bg="#1b2a4a", fg="#ffd54a")


def s23(cv, lt, d, T):
    sky_day(cv, T)
    k = eout(clamp(lt / 2.5))
    plate(cv, "raise", 1.04, dy=lerp(260, 0, k))
    near_sea(cv, 1500, T, "#2c8fbd", "#0b3f63", 14, ca=150)
    splash(cv, 380, 1150, (lt % 1.4) / 1.4, 16, 0.8); splash(cv, 720, 1150, ((lt + 0.7) % 1.4) / 1.4, 16, 0.8)
    date_stamp(cv, "1961", lt - 0.1, y=330)


def museum_bg(cv, T, z=1.0, sigma=0):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#120e0b")))
    plate(cv, "museum", z, cy=900, sigma=sigma, bright=1.7)
    cv.drawCircle(540, 900, 700, rad(540, 900, 700, [C("#ffcf8a", 50), C("#ffcf8a", 0)]))


def s24(cv, lt, d, T):
    museum_bg(cv, T, P(lt, d, 1.0, 1.08))
    date_stamp(cv, "98% ORIGINAL", lt - 0.2, y=330, size=118)


def s25(cv, lt, d, T):
    museum_bg(cv, T, 1.08, 3)
    outfits = ("sailor", "officer", "nurse", "steward", "sailor", "officer", "steward")
    for i, of in enumerate(outfits):
        x = (i * 190 + T * (40 + 12 * (i % 3))) % (W + 300) - 150
        toon2(cv, x, 1880 + (i % 2) * 30, 0.48, T, outfit=of, expr="joy" if i % 2 else "grin", pose="wave" if i % 3 == 0 else "stand",
              walk=T * 9 + i, look=0.7, seed=i, bun=False)
    date_stamp(cv, "+1 MILHÃO / ANO", lt - 0.2, y=330, size=96)


def s26(cv, lt, d, T):
    museum_bg(cv, T, 1.1, 5)
    rays(cv, 540, 900, T, n=12, a=30, spread=360, base=0)
    x, y, s = 540, 1690, 1.25
    toon2(cv, x, y, s, T, outfit="king", expr="grin", pose="hips")
    crown(cv, x, y, s)
    banner(cv, "O VASA", lt - 0.05, y=330, size=100, bg="#1b2a4a", fg="#ffd54a")


SHOTS = []


def add(s, e, fn, *a):
    SHOTS.append((s, e, fn, a))


add(0, L[2]["s"], s01); add(L[2]["s"], L[3]["s"], s02); add(L[3]["s"], L[4]["s"], s03); add(L[4]["s"], L[5]["s"], s04)
add(L[5]["s"], ws(5, "centenas"), s05a); add(ws(5, "centenas"), L[6]["s"], s05b); add(L[6]["s"], L[7]["s"], s06); add(L[7]["s"], L[8]["s"], s07)
add(L[8]["s"], L[9]["s"], s08); add(L[9]["s"], L[10]["s"], s09, ws(9, "almirante")); add(L[10]["s"], L[11]["s"], s10)
add(L[11]["s"], L[12]["s"], s11, ws(11, "ficaram")); add(L[12]["s"], L[13]["s"], s12); add(L[13]["s"], L[14]["s"], s13)
add(L[14]["s"], L[15]["s"], s14); add(L[15]["s"], L[16]["s"], s15); add(L[16]["s"], L[17]["s"], s16)
add(L[17]["s"], L[18]["s"], s17, ws(17, "menos")); add(L[18]["s"], L[19]["s"], s18); add(L[19]["s"], L[20]["s"], s19)
add(L[20]["s"], L[21]["s"], s20, ws(20, "não")); add(L[21]["s"], L[22]["s"], s21); add(L[22]["s"], L[23]["s"], s22)
add(L[23]["s"], L[24]["s"], s23); add(L[24]["s"], L[25]["s"], s24); add(L[25]["s"], L[26]["s"], s25); add(L[26]["s"], DUR + 0.01, s26)


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
