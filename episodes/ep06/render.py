"""EP06 — O computador de 2.000 anos (Mecanismo de Anticítera). PT-BR.
3D inked plates (navio antigo, ilha, fundo do mar, laboratório 1902, mecanismo, engrenagens, tomógrafo, torre do relógio)
+ 2D sketch characters. usage: render.py timings.json a b out.mp4 kitdir platesdir"""
import sys, json, math, subprocess
import numpy as np
sys.path.insert(0, sys.argv[5])
from gfx import *
import gfx
import toon2 as T2
from toon2 import toon2, ink, sk

gfx.KEYWORDS.clear()
gfx.KEYWORDS.update({"2.000", "anos", "navio", "afundou", "computador", "1900", "esponjas", "naufrágio", "anticítera",
                     "estátuas", "moedas", "tesouro", "bronze", "corroído", "ninguém", "1902", "engrenagem",
                     "engrenagem?", "raios", "30", "engrenagens", "milímetro", "sapato", "manivela", "sol", "lua",
                     "fases", "olímpicos", "reviravolta", "2005", "letras", "manual", "instruções", "eclipses",
                     "mil", "relógios", "astronômicos", "construiu", "antigo"})

T2.OUTFITS.update({
    "diver":   dict(body="#2f5d7a", trim="#f2e6c8", hat="none"),
    "diver2":  dict(body="#7a3f2f", trim="#f2e6c8", hat="none"),
    "archaeo": dict(body="#5a4632", trim="#e8dcc0", hat="none"),
    "greek":   dict(body="#ece3cc", trim="#b33a2a", hat="none"),
    "athlete": dict(body="#c9a24a", trim="#ffffff", hat="none"),
    "sci":     dict(body="#f4f4f2", trim="#3a7bd5", hat="none"),
})

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


def sun_icon(cv, x, y, r, T):
    for k in range(12):
        a = k * math.pi / 6 + T * 0.6
        cv.drawLine(x + math.cos(a) * r * 1.2, y + math.sin(a) * r * 1.2, x + math.cos(a) * r * 1.6, y + math.sin(a) * r * 1.6,
                    stroke(C("#ffd54a"), 8))
    sp = skia.Path(); sp.addCircle(x, y, r); sk(cv, sp, "#ffcf3a", 6, int(T * 8) % 3)


def moon_icon(cv, x, y, r, T, phase=0.5, base="#1a2140"):
    """phase 0 new .. 0.5 full .. 1 new; drawn lit part over dark disk."""
    sd = int(T * 8) % 3
    disk = skia.Path(); disk.addCircle(x, y, r)
    cv.drawPath(disk, fill(C(base)))
    cv.save(); cv.clipPath(disk, doAntiAlias=True)
    k = math.cos(phase * 2 * math.pi)  # 1 new, -1 full
    lit = skia.Path()
    if phase <= 0.5:   # waxing: right side lit
        lit.addArc(skia.Rect(x - r, y - r, x + r, y + r), -90, 180)
        ex = r * k
        lit.arcTo(skia.Rect(x - abs(ex), y - r, x + abs(ex), y + r), 90, 180 if k > 0 else -180, False)
    else:
        lit.addArc(skia.Rect(x - r, y - r, x + r, y + r), 90, 180)
        ex = r * k
        lit.arcTo(skia.Rect(x - abs(ex), y - r, x + abs(ex), y + r), -90, 180 if k > 0 else -180, False)
    lit.close()
    cv.drawPath(lit, fill(C("#f3eed8")))
    cv.restore()
    cv.drawPath(disk, ink(5, sd))


def bubbles2(cv, T, x, y, n=8, seed=0):
    for k in range(n):
        ph = (T * 0.9 + k / n + seed) % 1
        bx = x + 30 * math.sin(k * 2.1 + T * 2); by = y - ph * 520
        cv.drawCircle(bx, by, 8 + (k % 3) * 5, stroke(C("#e6fbff", 200 * (1 - ph)), 4))


def gear_icon(cv, x, y, r, ang, teeth=12, col="#ffd54a", w=7, a=255):
    p = skia.Path()
    for k in range(teeth * 2):
        aa = ang + k * math.pi / teeth
        rr = r if k % 2 == 0 else r * 0.82
        for j in (-0.3, 0.3):
            px = x + math.cos(aa + j * math.pi / teeth) * rr; py = y + math.sin(aa + j * math.pi / teeth) * rr
            (p.moveTo if (k == 0 and j < 0) else p.lineTo)(px, py)
    p.close()
    cv.drawPath(p, stroke(C(col, a), w))
    cv.drawCircle(x, y, r * 0.25, stroke(C(col, a), w))


def greek_line(seed, n):
    al = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    return "".join(al[(seed * 7 + k * 13 + (k * k) % 5) % len(al)] if (k % 6) else " " for k in range(n))


# ---------- scenes ----------

def ship_scene(cv, lt, d, T, sink=0.0, z=1.0):
    sky_sunset(cv, T)
    plate(cv, "ship_sea", z, cy=900)
    wl = layer_bottom("ship_layer")
    bob = 6 * math.sin(T * 1.6)
    # ship layer: tilt + sink, clipped at the waterline so the hull goes *under* the sea
    cv.save()
    cv.translate(W / 2, 900); cv.scale(z, z); cv.translate(-W / 2, -900)
    cv.clipRect(skia.Rect(0, 0, W, wl - 6))
    plate(cv, "ship_layer", 1.0, cx=560, cy=wl, dy=bob + sink * 900, rot=-sink * 22 + 1.5 * math.sin(T * 1.3))
    cv.restore()
    if sink > 0.05:
        bubbles2(cv, T, 560, wl * z + (1 - z) * 900 + 40, 10)


def s01a(cv, lt, d, T):  # hook: ancient ship sailing
    ship_scene(cv, lt, d, T, 0.0, P(lt, d, 1.0, 1.06))
    pop_text(cv, "2.000 ANOS", lt, ws(1, "2.000") - L[1]["s"], 330, 140)


def s01b(cv, lt, d, T, t_comp):  # it sinks... with the computer
    k = ease(clamp(lt / 1.6))
    ship_scene(cv, lt, d, T, k * 0.55, 1.06)
    if T > t_comp:
        a = eout((T - t_comp) / 0.4)
        glow(cv, 540, 640, 300, "#ffd54a", 160 * a, T)
        gear_icon(cv, 540, 640, 130, T * 0.8, 14, "#ffd54a", 10, 255 * a)
        gear_icon(cv, 690, 540, 70, -T * 1.6, 9, "#ffd54a", 8, 255 * a)


def s02(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "island", P(lt, d, 1.0, 1.06), cy=820)
    date_stamp(cv, "1900", lt - 0.05, y=360, size=190)
    banner(cv, "GRÉCIA", lt - 0.5, y=540, size=80, bg="#1b4a7a", fg="#ffffff")


def s03a(cv, lt, d, T):  # sponge divers on the boat
    sky_day(cv, T)
    plate(cv, "island", P(lt, d, 1.06, 1.12), cy=820)
    toon(cv, 300, 1650, 1.05, T, outfit="diver", expr="determined", pose="point", look=1, seed=1)
    toon(cv, 780, 1660, 1.0, T, outfit="diver2", expr="grin", pose="hips", look=-0.6, seed=2)
    banner(cv, "PESCADORES DE ESPONJAS", lt - 0.3, y=330, size=64, bg="#1b4a7a", fg="#ffd54a")


def s03b(cv, lt, d, T):  # dive down to the wreck
    under(cv, T)
    plate(cv, "seabed", P(lt, d, 1.0, 1.06), cy=900)
    k = ease(clamp(lt / d))
    x, y = lerp(260, 640, k), lerp(380, 860, k)
    toon(cv, x, y, 0.62, T, outfit="diver", expr="wide", pose="reach", look=0.6, seed=1, rot=150, walk=math.sin(T * 6), shadow=False)
    bubbles2(cv, T, x - 60, y + 60, 6)
    banner(cv, "ILHA DE ANTICÍTERA", lt - 0.2, y=330, size=70, bg="#1b4a7a", fg="#ffffff")


def s04(cv, lt, d, T):  # treasure
    under(cv, T)
    plate(cv, "seabed", P(lt, d, 1.06, 1.14), cy=1000)
    sparkles(cv, T, 560, 1050, 330, 160, 12, "#fff3b0")
    if T > ws(4, "tesouro"):
        banner(cv, "UM TESOURO", T - ws(4, "tesouro"), y=360, size=96, bg="#c08a1e", fg="#ffffff")
    else:
        banner(cv, "ESTÁTUAS, VASOS, MOEDAS", lt - 0.2, y=360, size=62, bg="#1b4a7a", fg="#ffffff")


LUMP = (560, 1120)   # where the bronze lump sits in the seabed frame (checked on stills)


def s05a(cv, lt, d, T):  # the corroded lump
    under(cv, T)
    z = P(lt, d, 1.25, 1.5)
    plate(cv, "seabed", z, cx=LUMP[0], cy=LUMP[1], dy=-180)
    glow(cv, LUMP[0], LUMP[1] - 180, 220, "#7fffd0", 90, T)
    banner(cv, "PEDAÇO DE BRONZE", lt - 0.4, y=330, size=80, bg="#2c5a4a", fg="#ffffff")


def s05b(cv, lt, d, T):  # nobody cared
    under(cv, T)
    plate(cv, "seabed", 1.12, cy=1000)
    k = clamp(lt / d)
    toon(cv, lerp(900, 330, k), 640, 0.58, T, outfit="diver2", expr="smile", pose="baby", look=-1, seed=2,
         rot=-80, walk=math.sin(T * 6), shadow=False)
    bubbles2(cv, T, lerp(900, 330, k) - 80, 600, 5, 0.4)
    pop_text(cv, "...", lt, 0.2, 420, 160)


def s06a(cv, lt, d, T):  # 1902, archaeologist looks closer
    studio(cv, "#3a2615")
    plate(cv, "lab", P(lt, d, 1.0, 1.08), cy=880)
    toon(cv, 860, 1640, 1.0, T, outfit="archaeo", expr="smile", pose="think", look=-1, seed=3)
    date_stamp(cv, "1902", lt - 0.05, y=330, size=170)
    banner(cv, "UM ARQUEÓLOGO", lt - 0.6, y=500, size=64, bg="#5a4632", fg="#ffd54a")


GEARPT = (560, 1010)  # gear visible on the lump in the lab frame


def s06b(cv, lt, d, T):  # sees a gear
    studio(cv, "#3a2615")
    z = P(lt, d, 1.6, 2.1)
    plate(cv, "lab", z, cx=GEARPT[0], cy=GEARPT[1], dy=-260)
    glow(cv, GEARPT[0], GEARPT[1] - 260, 300, "#ffd54a", 120, T)
    sparkles(cv, T, GEARPT[0], GEARPT[1] - 260, 260, 220, 9)


def s07(cv, lt, d, T):  # gear?? on an ancient ship??
    red_pulse(cv, T, "#a8651a")
    zoom(cv, lerp(1.0, 1.15, eout(lt / d)), 540, 900)
    sprite(cv, "gear_big", 540, 700, 0.62, T * 25, 0.9)
    toon(cv, 540, 1700, 1.25, T, outfit="archaeo", expr="shock", pose="panic", seed=3)
    pop_text(cv, "ENGRENAGEM?!", lt, 0.05, 300, 104, "#ffd54a")


def s08a(cv, lt, d, T):  # decades later: X-rays
    xray_bg(cv, T)
    plate(cv, "lab", 2.0, cx=GEARPT[0], cy=GEARPT[1], dy=-200, cf=xray_cf())
    y = 200 + (lt * 520) % 1300
    cv.drawRect(skia.Rect(0, y - 6, W, y + 6), fill(C("#7fe9ff", 200)))
    cv.drawRect(skia.Rect(0, y - 60, W, y), lin(0, y - 60, 0, y, [C("#7fe9ff", 0), C("#7fe9ff", 80)]))
    date_stamp(cv, "RAIOS X", lt - 0.05, y=330, size=140, col="#bff3ff")
    banner(cv, "DÉCADAS DEPOIS", lt - 0.4, y=500, size=60, bg="#0f3a5a", fg="#ffffff")


def s08b(cv, lt, d, T, t30):  # at least 30 gears
    xray_bg(cv, T)
    spots = [(300, 700, 0.42, 1), (720, 640, 0.5, -1), (520, 1040, 0.36, 1), (180, 1100, 0.22, -1), (880, 1080, 0.26, 1),
             (900, 380, 0.2, -1), (160, 420, 0.24, 1), (560, 380, 0.16, -1)]
    k = clamp(lt / 1.2)
    for i, (x, y, s, dr) in enumerate(spots):
        if i / len(spots) <= k:
            nm = "gear_big" if i % 2 == 0 else "gear_small"
            sprite(cv, nm, x, y, s, dr * T * (30 / s ** 0.5), 0.95, cf=xray_cf())
    if T > t30:
        a = T - t30
        pop_text(cv, "30+", a + 0.0, 0.0, 330, 220, "#ffd54a")
        if a > 0.25:
            pop_text(cv, "ENGRENAGENS", a, 0.25, 450, 80, "#ffffff")


def s09(cv, lt, d, T):  # teeth ~1 mm
    studio(cv)
    sprite(cv, "gear_small", 540, 1750, P(lt, d, 1.7, 1.95), T * 6, 1.0)
    sprite(cv, "gear_big", 160, 620, 0.9, -T * 3, 1.0)
    banner(cv, "DENTES DE ~1 MILÍMETRO", lt - 0.2, y=330, size=64, bg="#5a3b20", fg="#ffd54a")


def s10(cv, lt, d, T):  # shoebox-sized, hand-cranked
    studio(cv)
    plate(cv, "mech", P(lt, d, 1.0, 1.06), cy=860)
    banner(cv, "DO TAMANHO DE UMA", lt - 0.2, y=250, size=64, bg="#1b2a4a", fg="#ffffff")
    banner(cv, "CAIXA DE SAPATO", lt - 0.6, y=380, size=86, bg="#c08a1e", fg="#ffffff")
    if T > ws(10, "manivela"):
        a = T - ws(10, "manivela")
        cv.save(); cv.translate(800, 880); cv.rotate(T * 220)
        cv.drawArc(skia.Rect(-110, -110, 110, 110), 0, 270, False, stroke(C("#ffd54a", 255 * eout(a / 0.3)), 12))
        cv.restore()


def s11a(cv, lt, d, T):  # you turn the crank
    studio(cv)
    plate(cv, "mech", 1.05, cy=860, dx=-20)
    toon(cv, 860, 1640, 1.0, T, outfit="greek", expr="grin", pose="point", look=-0.6, seed=4)
    cv.save(); cv.translate(800, 850); cv.rotate(T * 260)
    cv.drawArc(skia.Rect(-95, -95, 95, 95), 0, 270, False, stroke(C("#ffd54a"), 11))
    cv.drawPath(poly([(95, -10), (120, 20), (70, 20)]), fill(C("#ffd54a")))
    cv.restore()
    banner(cv, "GIRA A MANIVELA", lt - 0.2, y=330, size=76, bg="#1b2a4a", fg="#ffd54a")


def s11b(cv, lt, d, T):  # sun + moon positions
    night(cv, T)
    plate(cv, "mech", 1.0, cy=1080, alpha=0.95)
    cx, cy, r = 540, 560, 300
    cv.drawCircle(cx, cy, r, stroke(C("#ffffff", 70), 4))
    a1 = T * 0.9; a2 = T * 2.4
    sun_icon(cv, cx + math.cos(a1) * r, cy + math.sin(a1) * r * 0.5, 54, T)
    moon_icon(cv, cx + math.cos(a2) * r * 0.65, cy + math.sin(a2) * r * 0.32, 42, T, 0.5)
    banner(cv, "SOL E LUA NO CÉU", lt - 0.2, y=210, size=72, bg="#1b2a4a", fg="#ffd54a")


def s12a(cv, lt, d, T):  # moon phases
    night(cv, T)
    n = 8
    for i in range(n):
        a = eout(clamp((lt - i * 0.12) / 0.3))
        if a <= 0: continue
        x = 130 + i * 117; y = 700 + 60 * math.sin(i / (n - 1) * math.pi) * -1
        moon_icon(cv, x, y, 50 * a, T, (i + 0.5) / n)
    banner(cv, "FASES DA LUA", lt - 0.1, y=420, size=88, bg="#1b2a4a", fg="#ffffff")


def laurel(cv, x, y, r, T):
    for sd in (-1, 1):
        for k in range(7):
            a = math.radians(90 + sd * (25 + k * 20))
            px, py = x + math.cos(a) * r, y + math.sin(a) * r
            leaf = skia.Path(); leaf.addOval(skia.Rect(-14, -30, 14, 30))
            cv.save(); cv.translate(px, py); cv.rotate(math.degrees(a) + 90 + sd * 30)
            sk(cv, leaf, "#7fae4a", 4, k); cv.restore()


def s12b(cv, lt, d, T):  # olympics
    sky_day(cv, T)
    plate(cv, "island", 1.1, cy=820, sigma=5)
    k = clamp(lt / d)
    toon(cv, lerp(260, 820, k), 1650, 1.05, T, outfit="athlete", expr="joy", pose="wave", look=1, seed=5, walk=T * 9)
    laurel(cv, 540, 560, 170, T)
    banner(cv, "JOGOS OLÍMPICOS", lt - 0.2, y=330, size=88, bg="#c08a1e", fg="#ffffff")


def s13(cv, lt, d, T):  # twist
    red_pulse(cv, T)
    zoom(cv, lerp(1.0, 1.35, eout(lt / d)), 540, 820)
    toon(cv, 540, 1720, 1.7, T, outfit="greek", expr="shock", seed=4)


def s14a(cv, lt, d, T):  # 2005: CT scans
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#cfe2ee"), C("#7f9fb5")]))
    plate(cv, "ct", P(lt, d, 1.0, 1.06), cy=880)
    toon(cv, 830, 1640, 1.0, T, outfit="sci", expr="determined", pose="point", look=-1, seed=6)
    date_stamp(cv, "2005", lt - 0.05, y=330, size=180)
    banner(cv, "TOMOGRAFIA", lt - 0.5, y=500, size=70, bg="#0f3a5a", fg="#ffffff")


def s14b(cv, lt, d, T):  # thousands of hidden letters
    xray_bg(cv, T)
    plate(cv, "ct", 1.7, cx=540, cy=1000, dy=-120, cf=xray_cf(), alpha=0.8)
    f = skia.Font(GREEK, 64)
    al = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    for i in range(46):
        ph = (lt * 0.35 + i * 0.137) % 1
        a0 = i * 2.39
        r = 120 + ph * 640
        x = 540 + math.cos(a0) * r; y = 820 + math.sin(a0) * r * 0.9
        if y > 1280: continue
        a = 255 * math.sin(ph * math.pi) * clamp(lt / 0.4)
        ch = al[(i * 7) % len(al)]
        cv.drawString(ch, x, y, f, fill(C("#9ff0ff", a)))
    banner(cv, "MILHARES DE LETRAS", lt - 0.2, y=330, size=76, bg="#0f3a5a", fg="#ffd54a")


def s15(cv, lt, d, T):  # instruction manual
    studio(cv, "#24180e")
    r = skia.Rect(110, 470, 970, 1240)
    cv.drawRoundRect(r.makeOffset(10, 14), 30, 30, fill(C("#000000", 110)))
    pl = skia.Path(); pl.addRoundRect(r, 30, 30)
    sk(cv, pl, "#5f8a6a", 8, int(T * 8) % 3)
    cv.save(); cv.clipPath(pl, doAntiAlias=True)
    cv.drawRect(r, lin(110, 470, 970, 1240, [C("#79a585", 120), C("#2f5640", 120)]))
    f = skia.Font(GREEK, 52)
    for row in range(10):
        a = eout(clamp((lt - row * 0.12) / 0.3))
        cv.drawString(greek_line(row, 22), 150, 560 + row * 68, f, fill(C("#e8f2d8", 220 * a)))
    cv.restore()
    banner(cv, "MANUAL DE INSTRUÇÕES", lt - 0.2, y=330, size=72, bg="#c08a1e", fg="#ffffff")


def s16a(cv, lt, d, T):  # confirmed: predicted eclipses
    studio(cv)
    plate(cv, "mech", P(lt, d, 1.1, 1.5), cx=540, cy=760, dy=-60)
    glow(cv, 540, 700, 380, "#ffd54a", 70, T)
    banner(cv, "A MÁQUINA PREVIA...", lt - 0.2, y=300, size=70, bg="#1b2a4a", fg="#ffffff")


def s16b(cv, lt, d, T):  # eclipse
    k = ease(clamp(lt / (d * 0.7)))
    dark = k
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#2a6db0"), C("#f0d9a8")]))
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#05060f", 230 * dark)))
    stars(cv, T, dark, ymax=H * 0.7)
    sx, sy, r = 540, 700, 190
    if dark > 0.85:
        cv.drawCircle(sx, sy, r * 1.9, rad(sx, sy, r * 1.9, [C("#fff6d8", 220), C("#ffe9a8", 90), C("#ffe9a8", 0)], [0.45, 0.6, 1]))
    sun_glow(cv, sx, sy, r * 2.4, "#fff2c4", 180 * (1 - dark * 0.6))
    cv.drawCircle(sx, sy, r, fill(C("#ffd54a")))
    mx = lerp(sx + 480, sx, k)
    mp = skia.Path(); mp.addCircle(mx, sy, r * 1.02)
    cv.drawPath(mp, fill(C("#0b0d18")))
    cv.drawPath(mp, ink(6, int(T * 8) % 3))
    banner(cv, "ECLIPSES", lt - 0.1, y=310, size=110, bg="#1b2a4a", fg="#ffd54a")
    if lt > 1.2:
        banner(cv, "COM ANOS DE ANTECEDÊNCIA", lt - 1.2, y=1110, size=56, bg="#c08a1e", fg="#ffffff")


def s17a(cv, lt, d, T):  # nothing as complex for 1000+ years
    studio(cv, "#1a120c")
    k = ease(clamp(lt / d))
    plate(cv, "mech", lerp(1.0, 1.1, k), cy=860, alpha=lerp(1, 0.35, k), sigma=lerp(0, 6, k))
    # calendar pages flying
    f = skia.Font(TF, 64)
    for i in range(8):
        ph = (lt * 0.8 + i / 8) % 1
        a = 255 * math.sin(ph * math.pi)
        x = 140 + (i * 233) % 820; y = 1250 - ph * 900
        rr = skia.Rect(x - 60, y - 70, x + 60, y + 70)
        cv.drawRoundRect(rr, 10, 10, fill(C("#f3ead2", a))); cv.drawRoundRect(rr, 10, 10, stroke(C("#2a1d12", a), 5))
    pop_text(cv, "+ DE 1.000 ANOS", lt, 0.1, 360, 120, "#ffd54a")


def s17b(cv, lt, d, T):  # medieval astronomical clocks
    sky_day(cv, T)
    plate(cv, "clocktower", P(lt, d, 1.0, 1.07), cy=700)
    banner(cv, "RELÓGIOS ASTRONÔMICOS", lt - 0.2, y=250, size=66, bg="#1b2a4a", fg="#ffd54a")
    banner(cv, "EUROPA, SÉCULO XIV", lt - 0.8, y=1150, size=58, bg="#5a3b20", fg="#ffffff")


def s18(cv, lt, d, T):  # nobody knows who built it
    studio(cv, "#140d08")
    plate(cv, "mech", 1.0, cy=860, bright=0.55)
    toon(cv, 540, 1700, 1.15, T, outfit="greek", expr="worried", pose="think", look=0.3, seed=4)
    f = skia.Font(TF, 150)
    for i, (x, y) in enumerate(((220, 640), (860, 560), (300, 1050), (820, 1000))):
        bob = 18 * math.sin(T * 3 + i)
        a = 255 * eout(clamp((lt - i * 0.2) / 0.3))
        cv.drawString("?", x, y + bob, f, stroke(C("#14100c", a), 16))
        cv.drawString("?", x, y + bob, f, fill(C("#ffd54a", a)))
    banner(cv, "QUEM CONSTRUIU?", lt - 0.2, y=330, size=90, bg="#8a1f1f", fg="#ffffff")


def s19a(cv, lt, d, T):  # this piece of bronze from the sea floor
    under(cv, T)
    z = P(lt, d, 1.2, 1.4)
    plate(cv, "seabed", z, cx=LUMP[0], cy=LUMP[1], dy=-160)
    glow(cv, LUMP[0], LUMP[1] - 160, 260, "#ffd54a", 120, T)
    sparkles(cv, T, LUMP[0], LUMP[1] - 160, 240, 160, 8)


def s19b(cv, lt, d, T):  # ...the oldest computer known
    studio(cv)
    rays(cv, 540, 760, T, n=11, a=34, spread=360, base=90, col="#ffe6b0")
    plate(cv, "mech", P(lt, d, 0.95, 1.05), cy=860)
    sparkles(cv, T, 540, 760, 380, 420, 12)
    banner(cv, "O COMPUTADOR", lt - 0.1, y=250, size=96, bg="#1b2a4a", fg="#ffffff")
    banner(cv, "MAIS ANTIGO", lt - 0.5, y=390, size=96, bg="#c08a1e", fg="#ffffff")


SHOTS = []


def add(s, e, fn, *a):
    SHOTS.append((s, e, fn, a))


add(0, ws(1, "afundou"), s01a)
add(ws(1, "afundou"), L[2]["s"], s01b, ws(1, "computador"))
add(L[2]["s"], L[3]["s"], s02)
add(L[3]["s"], ws(3, "acham"), s03a)
add(ws(3, "acham"), L[4]["s"], s03b)
add(L[4]["s"], L[5]["s"], s04)
add(L[5]["s"], ws(5, "ninguém"), s05a)
add(ws(5, "ninguém"), L[6]["s"], s05b)
add(L[6]["s"], ws(6, "viu"), s06a)
add(ws(6, "viu"), L[7]["s"], s06b)
add(L[7]["s"], L[8]["s"], s07)
add(L[8]["s"], ws(8, "revelaram"), s08a)
add(ws(8, "revelaram"), L[9]["s"], s08b, ws(8, "30"))
add(L[9]["s"], L[10]["s"], s09)
add(L[10]["s"], L[11]["s"], s10)
add(L[11]["s"], ws(11, "mostrava"), s11a)
add(ws(11, "mostrava"), L[12]["s"], s11b)
add(L[12]["s"], ws(12, "até"), s12a)
add(ws(12, "até"), L[13]["s"], s12b)
add(L[13]["s"], L[14]["s"], s13)
add(L[14]["s"], ws(14, "milhares"), s14a)
add(ws(14, "milhares"), L[15]["s"], s14b)
add(L[15]["s"], L[16]["s"], s15)
add(L[16]["s"], ws(16, "eclipses"), s16a)
add(ws(16, "eclipses"), L[17]["s"], s16b)
add(L[17]["s"], ws(17, "mil"), s17a)
add(ws(17, "mil"), L[18]["s"], s17b)
add(L[18]["s"], L[19]["s"], s18)
add(L[19]["s"], ws(19, "chamado"), s19a)
add(ws(19, "chamado"), DUR + 0.01, s19b)


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
