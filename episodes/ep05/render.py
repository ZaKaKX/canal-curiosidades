"""EP05 — A cidade que não conseguia parar de dançar (Estrasburgo, 1518). PT-BR.
3D inked medieval plates + 2D sketch characters (dançarinos). usage: render.py timings.json a b out.mp4 kitdir platesdir"""
import sys, json, math, subprocess
sys.path.insert(0, sys.argv[5])
from gfx import *
import gfx
import toon2 as T2
from toon2 import toon2, ink, sk

gfx.KEYWORDS.clear()
gfx.KEYWORDS.update({"dançar", "dança", "cidade", "parar", "estrasburgo", "1518", "julho", "rua", "pés", "inchados",
                     "sangrando", "semana", "médicos", "sangue", "quente", "receita", "palco", "músicos", "doença",
                     "400", "mortes", "cansaço", "setembro", "santuário", "vito", "montanhas", "rezaram", "parou",
                     "castigava", "pecadores", "fome", "waller", "medo", "estresse", "transe", "veneno", "maldição",
                     "trófea", "pecado"})

T2.OUTFITS.update({
    "peasant":  dict(body="#8a5a2b", trim="#d9c9a6", hat="none"),
    "peasant2": dict(body="#5f6b3a", trim="#d9c9a6", hat="none"),
    "woman":    dict(body="#9c3b3b", trim="#e4d2a8", hat="none"),
    "woman2":   dict(body="#3f5a7a", trim="#e4d2a8", hat="none"),
    "doctor":   dict(body="#2a2030", trim="#b64a3a", hat="none"),
    "monk":     dict(body="#5a3b20", trim="#3a2614", hat="none"),
    "waller":   dict(body="#2f4a68", trim="#d9c9a6", hat="none"),
})

TJ = json.load(open(sys.argv[1]))
PL = sys.argv[6]
L = {l["i"]: l for l in TJ["lines"]}
DUR = TJ["duration"]
CHUNKS = build_chunks(TJ)
FIX = {"trófea": "TRÓFEA"}
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


def _fit(text, size, maxw=940):
    while skia.Font(TF, size).measureText(text) > maxw and size > 40: size -= 4
    return size


def date_stamp(cv, text, lt, y=430, size=170, **k): _ds(cv, text, lt, y=y, size=_fit(text, size), **k)
def banner(cv, text, lt, y=420, size=78, **k): _bn(cv, text, lt, y=y, size=_fit(text, size, 900), **k)


def P(lt, d, a=1.0, b=1.08):
    return lerp(a, b, ease(lt / d))


# ---------- skies ----------

def sky_day(cv, T):
    sky(cv, "#5a8fc8", "#eadfc6", H)
    sun_glow(cv, 820, 340, 560, "#fff2cf", 150)
    for i, (x, y, w) in enumerate(((220, 280, 260), (780, 210, 300), (500, 430, 220))):
        xx = (x + T * 7 * (1 + i * 0.3)) % (W + 400) - 200
        for k in range(4):
            cv.drawCircle(xx - w * 0.35 + k * w * 0.23, y - (k % 2) * 30, w * 0.22, fill(C("#fbf6ec", 210)))
        cv.drawRect(skia.Rect(xx - w * 0.45, y, xx + w * 0.45, y + w * 0.12), fill(C("#fbf6ec", 210)))


def sky_dusk(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1100, [C("#43406e"), C("#9a5d6a"), C("#e8a85f")], [0, 0.5, 1]))
    sun_glow(cv, 720, 560, 620, "#ffcf8a", 190)


def sky_dawn(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1100, [C("#6a6fa0"), C("#c9a2a0"), C("#f6dca8")], [0, 0.55, 1]))
    sun_glow(cv, 540, 520, 600, "#ffe6b8", 170)


def dark_room(cv, col="#140a1e"):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C(col), C("#06030a")]))


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


def notes(cv, T, x, y, n=6, col="#2a1d12"):
    for i in range(n):
        ph = (T * 0.8 + i / n) % 1
        px = x + math.sin(i * 2.1 + T) * 120 + i * 20
        py = y - ph * 520
        a = 255 * math.sin(ph * math.pi)
        cv.drawCircle(px, py, 13, fill(C(col, a)))
        cv.drawRect(skia.Rect(px + 10, py - 54, px + 16, py), fill(C(col, a)))
        cv.drawRect(skia.Rect(px + 10, py - 54, px + 40, py - 44), fill(C(col, a)))


def dust(cv, T, a=150, n=40, col="#d9b98a"):
    for i in range(n):
        ph = (T * 0.25 + i * 0.173) % 1
        x = (i * 131 + ph * 400) % (W + 200) - 100; y = 300 + (i * 211) % 1200 - ph * 120
        cv.drawCircle(x, y, 6 + (i % 4) * 3, fill(C(col, a * math.sin(ph * math.pi))))


def sweat(cv, T, x, y, n=3, seed=0):
    for k in range(n):
        ph = (T * 1.6 + k * 0.4 + seed) % 1
        dp = skia.Path(); dp.addOval(skia.Rect(x - 9 + k * 30, y + ph * 110, x + 9 + k * 30, y + 24 + ph * 110))
        sk(cv, dp, "#bfe3ff", 3, k)


# ---------- dancers ----------

def dancer(cv, x, y, s, T, outfit="peasant", seed=0.0, expr="laugh", wild=1.0, look=None, fall=0.0):
    """a flailing medieval dancer. fall 0..1 -> collapsing to the ground."""
    if fall <= 0:
        y = min(y, 1250 + 330 * s)   # keep head above the caption band (y~1290)
    ph = T * 5.0 + seed * 1.7
    if fall > 0:
        rot = lerp(0, 82, fall) * (1 if seed % 2 else -1)
        yo = lerp(0, 150, fall)
        toon2(cv, x, y + yo, s, T, outfit=outfit, expr="worried" if fall < 0.8 else "closed",
              pose="reach", look=0, seed=seed, rot=rot, walk=0.2 * math.sin(ph))
        return
    yo = -abs(math.sin(ph)) * 46 * wild
    rot = 15 * math.sin(ph * 0.9) * wild
    pose = "panic" if int(ph * 0.5 + seed) % 2 else "wave"
    lk = look if look is not None else math.sin(ph) * 0.6
    toon2(cv, x, y + yo, s, T, outfit=outfit, expr=expr, pose=pose, look=lk, seed=seed,
          rot=rot, walk=math.sin(ph) * wild)


def crowd(cv, T, spots, wild=1.0):
    spots = sorted(spots, key=lambda q: q[1])  # back-to-front
    outs = ("peasant", "woman", "peasant2", "woman2", "monk", "peasant", "woman", "peasant2")
    for i, (x, y, s) in enumerate(spots):
        dancer(cv, x, y, s, T, outfit=outs[i % len(outs)], seed=i * 1.3,
               expr="joy" if i % 2 else "laugh", wild=wild)


# ---------- scenes ----------

def s01(cv, lt, d, T, tb):  # hook
    sky_day(cv, T)
    plate(cv, "street", P(lt, d, 1.02, 1.12), cy=760)
    crowd(cv, T, [(230, 1640, 0.95), (540, 1680, 1.05), (840, 1650, 0.95), (380, 1720, 0.8), (700, 1720, 0.82)], 1.15)
    notes(cv, T, 540, 1500, 7)
    if T > tb:
        a = eout((T - tb) / 0.25)
        cv.save(); cv.translate(540, 330); cv.scale(lerp(1.4, 1, a), lerp(1.4, 1, a))
        f = skia.Font(TF, 118); t = "SEM PARAR"
        cv.drawString(t, -f.measureText(t) / 2, 0, f, stroke(C("#14100c", 255 * a), 16))
        cv.drawString(t, -f.measureText(t) / 2, 0, f, fill(C("#ffffff", 255 * a)))
        cv.restore()


def s02(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "street", P(lt, d, 1.0, 1.08), cy=760, dx=lerp(16, -16, ease(lt / d)))
    date_stamp(cv, "ESTRASBURGO", lt - 0.1, y=330, size=120)
    banner(cv, "JULHO DE 1518", lt - 0.8, y=500, size=74, bg="#1b2a4a", fg="#ffd54a")


def s03(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "street", 1.06, cy=760)
    dancer(cv, 560, 1650, 1.25, T, outfit="woman", seed=0.3, expr="wide", wild=1.1)
    banner(cv, "SRA. TRÓFEA", lt - 0.5, y=330, size=84, bg="#9c3b3b", fg="#ffffff")


def s04(cv, lt, d, T):  # dances all day until she collapses
    # day -> dusk sky as the day passes
    k = ease(lt / d)
    if k < 0.6:
        sky_day(cv, T)
    else:
        sky_dusk(cv, T)
    plate(cv, "street", 1.06, cy=760, bright=lerp(1.0, 0.7, clamp((k - 0.5) / 0.5)))
    if k < 0.7:
        dancer(cv, 560, 1650, 1.25, T, outfit="woman", seed=0.3, expr="wide", wild=1.1)
        sweat(cv, T, 440, 1200, 3, 0.3)
    else:
        f = eout((k - 0.7) / 0.3)
        dancer(cv, 560, 1650, 1.25, T, outfit="woman", seed=0.3, fall=f)
    banner(cv, "O DIA INTEIRO", lt - 0.2, y=330, size=82, bg="#1b2a4a", fg="#ffd54a")


def s05(cv, lt, d, T):  # next day, bloody feet, dances again
    sky_day(cv, T)
    plate(cv, "street", 1.06, cy=760)
    x, y, s = 560, 1650, 1.25
    dancer(cv, x, y, s, T, outfit="woman", seed=0.3, expr="worried", wild=0.95)
    # red marks at feet
    for sx in (-1, 1):
        cv.drawCircle(x + sx * 48 * s, y - 6, 16, fill(C("#b4231c", 220)))
    banner(cv, "PÉS INCHADOS", lt - 0.3, y=330, size=82, bg="#8a1f1f", fg="#ffffff")


def s06(cv, lt, d, T):  # a week later: 30+ dancing
    sky_day(cv, T)
    plate(cv, "street", P(lt, d, 1.0, 1.06), cy=760)
    spots = [(170, 1660, 0.8), (330, 1700, 0.9), (480, 1660, 1.0), (560, 1720, 0.85),
             (680, 1670, 0.95), (840, 1700, 0.85), (930, 1650, 0.75), (250, 1740, 0.7)]
    crowd(cv, T, spots, 1.1)
    banner(cv, "UMA SEMANA DEPOIS", lt - 0.1, y=330, size=70, bg="#1b2a4a", fg="#ffd54a")


def s07(cv, lt, d, T):  # doctors: hot blood
    sky_day(cv, T)
    plate(cv, "square", 1.04, cy=820)
    toon2(cv, 300, 1630, 1.2, T, outfit="doctor", expr="smug", pose="point", look=1, seed=2)
    # patient dancing on the right
    dancer(cv, 820, 1680, 1.0, T, outfit="peasant", seed=1.1, expr="wide", wild=1.0)
    banner(cv, "SANGUE QUENTE", lt - 0.4, y=330, size=84, bg="#8a1f1f", fg="#ffffff")
    date_stamp(cv, "OS MÉDICOS", lt - 0.1, y=190, size=72)


def s08(cv, lt, d, T):  # the cure? more dancing
    sky_day(cv, T)
    plate(cv, "square", 1.1, cy=820, sigma=3)
    toon2(cv, 540, 1688, 1.35, T, outfit="doctor", expr="grin", pose="hips", look=0, seed=2)
    if lt > 0.5:
        a = eout((lt - 0.5) / 0.3)
        f = skia.Font(TF, 120); t = "MAIS DANÇA!"
        cv.save(); cv.translate(540, 360); cv.scale(lerp(1.3, 1, a), lerp(1.3, 1, a))
        cv.drawString(t, -f.measureText(t) / 2, 0, f, stroke(C("#14100c", 255 * a), 16))
        cv.drawString(t, -f.measureText(t) / 2, 0, f, fill(C("#ffd54a", 255 * a)))
        cv.restore()


def s09(cv, lt, d, T):  # stage + musicians
    sky_day(cv, T)
    plate(cv, "stage", P(lt, d, 1.0, 1.05), cy=780)
    # musicians on the stage (stage top ~ y 780 in frame): place two players
    toon2(cv, 430, 1150, 0.72, T, outfit="peasant2", expr="smile", pose="think", look=0.3, seed=5)
    toon2(cv, 650, 1150, 0.72, T, outfit="peasant", expr="smile", pose="wave", look=-0.3, seed=6)
    notes(cv, T, 540, 1080, 7)
    # dancers in front
    crowd(cv, T, [(250, 1720, 0.8), (540, 1760, 0.9), (840, 1720, 0.8)], 1.1)
    banner(cv, "PALCO E MÚSICOS", lt - 0.2, y=320, size=76, bg="#5a3b20", fg="#ffd54a")


def s10(cv, lt, d, T):  # dance until the disease leaves
    sky_day(cv, T)
    plate(cv, "stage", 1.08, cy=780)
    toon2(cv, 430, 1150, 0.72, T, outfit="peasant2", expr="smile", pose="wave", look=0.3, seed=5)
    toon2(cv, 650, 1150, 0.72, T, outfit="peasant", expr="smile", pose="think", look=-0.3, seed=6)
    notes(cv, T, 540, 1080, 6)
    crowd(cv, T, [(200, 1700, 0.85), (420, 1760, 0.9), (640, 1710, 0.95), (860, 1760, 0.8)], 1.15)
    banner(cv, "DANÇAR ATÉ SARAR", lt - 0.1, y=330, size=76, bg="#1b2a4a", fg="#ffd54a")


def s11(cv, lt, d, T):  # it got worse: ~400
    sky_day(cv, T)
    plate(cv, "square", P(lt, d, 1.0, 1.05), cy=820)
    spots = []
    import math as _m
    for i in range(12):
        x = 120 + (i * 83) % 860 + 30 * _m.sin(i)
        y = 1600 + (i * 57) % 220
        spots.append((x, y, 0.62 + (i % 3) * 0.12))
    crowd(cv, T, spots, 1.2)
    if lt > 0.5:
        a = eout((lt - 0.5) / 0.3)
        f = skia.Font(TF, 230); t = "400"
        cv.save(); cv.translate(540, 470); cv.scale(lerp(1.4, 1, a), lerp(1.4, 1, a))
        cv.drawString(t, -f.measureText(t) / 2, 0, f, stroke(C("#14100c", 255 * a), 22))
        cv.drawString(t, -f.measureText(t) / 2, 0, f, fill(C("#ffd54a", 255 * a)))
        f2 = skia.Font(TF, 70); t2 = "PESSOAS"
        cv.drawString(t2, -f2.measureText(t2) / 2, 110, f2, stroke(C("#14100c", 255 * a), 12))
        cv.drawString(t2, -f2.measureText(t2) / 2, 110, f2, fill(C("#ffffff", 255 * a)))
        cv.restore()


def s12(cv, lt, d, T):  # collapsing, reports of deaths
    sky_dusk(cv, T)
    plate(cv, "square", 1.05, cy=820, bright=0.72)
    k = ease(lt / d)
    # mix of fallen and exhausted dancers
    dancer(cv, 260, 1680, 0.95, T, outfit="peasant", seed=1, fall=clamp(k * 1.3))
    dancer(cv, 560, 1700, 1.0, T, outfit="woman", seed=2, fall=clamp(k * 1.1 - 0.1))
    dancer(cv, 840, 1680, 0.9, T, outfit="peasant2", seed=3, expr="worried", wild=0.5)
    sweat(cv, T, 820, 1200, 3, 0.5)
    banner(cv, "CAINDO DE CANSAÇO", lt - 0.1, y=330, size=72, bg="#4a1f1f", fg="#ffffff")


def s13(cv, lt, d, T):  # september: shrine in the mountains
    sky_dawn(cv, T)
    plate(cv, "shrine", P(lt, d, 1.0, 1.06), cy=820)
    # pilgrims walking up toward the chapel
    for i, (x, y, s, ph) in enumerate(((330, 1510, 0.8, 0), (470, 1500, 0.72, 1), (600, 1505, 0.78, 2))):
        toon2(cv, x, y, s, T, outfit=("monk", "woman", "peasant")[i], expr="worried", pose="reach",
              look=0.5, seed=ph, walk=math.sin(T * 3 + ph))
    date_stamp(cv, "SETEMBRO", lt - 0.1, y=300, size=120)
    banner(cv, "SANTUÁRIO DE SÃO VITO", lt - 0.9, y=470, size=60, bg="#1b2a4a", fg="#ffd54a")


def s14(cv, lt, d, T):  # prayed, dance finally stopped
    dark_room(cv, "#201630")
    plate(cv, "shrine_glow", P(lt, d, 1.0, 1.05), cy=820, bright=0.95)
    rays(cv, 540, 560, T, n=9, a=30, spread=120, base=90, col="#ffe6b0")
    # kneeling, calm figures
    toon2(cv, 330, 1550, 0.95, T, outfit="monk", expr="closed", pose="think", look=0.3, seed=1)
    toon2(cv, 740, 1550, 0.95, T, outfit="woman", expr="closed", pose="baby", look=-0.3, seed=2)
    sparkles(cv, T, 540, 760, 240, 280, 10, "#ffe9b0")
    banner(cv, "E A DANÇA PAROU", lt - 0.3, y=330, size=80, bg="#1b2a4a", fg="#ffd54a")


def s15(cv, lt, d, T):  # twist
    red_pulse(cv, T)
    zoom(cv, lerp(1.0, 1.35, eout(lt / d)), 540, 820)
    toon2(cv, 540, 1720, 1.7, T, outfit="woman", expr="shock")


def s16(cv, lt, d, T):  # belief: St Vitus cursed sinners to dance
    dark_room(cv, "#160c20")
    # a looming saint silhouette (cross) + glow
    cv.drawCircle(540, 620, 520, rad(540, 620, 520, [C("#c9a2ff", 90 + 30 * math.sin(T * 3)), C("#c9a2ff", 0)]))
    cv.drawRect(skia.Rect(515, 330, 565, 860), fill(C("#2a1d3a")))
    cv.drawRect(skia.Rect(420, 470, 660, 520), fill(C("#2a1d3a")))
    # dancing shadows below, cursed
    for i, (x, s) in enumerate(((240, 0.8), (430, 0.9), (640, 0.9), (840, 0.8))):
        dancer(cv, x, 1760, s, T, outfit=("peasant", "woman", "peasant2", "monk")[i], seed=i, expr="wide", wild=1.1)
    banner(cv, "SÃO VITO", lt - 0.2, y=320, size=90, bg="#3a1f5a", fg="#ffffff")
    if lt > 1.4:
        a = eout((lt - 1.4) / 0.3)
        f = skia.Font(TF, 58); t = "CASTIGO AOS PECADORES"
        cv.drawString(t, 540 - f.measureText(t) / 2, 430, f, stroke(C("#14100c", 255 * a), 12))
        cv.drawString(t, 540 - f.measureText(t) / 2, 430, f, fill(C("#ffd54a", 255 * a)))


def s17(cv, lt, d, T):  # years of famine and disease
    sky_dusk(cv, T)
    plate(cv, "street_dusk", P(lt, d, 1.0, 1.05), cy=760, bright=0.85)
    for i, (x, y, s) in enumerate(((300, 1552, 0.95), (560, 1570, 1.0), (800, 1548, 0.92))):
        toon2(cv, x, y, s, T, outfit=("peasant", "woman", "peasant2")[i], expr="sad", pose="stand",
              look=0, seed=i)
    dust(cv, T, 120, 30, "#8a7a5a")
    banner(cv, "ANOS DE FOME E DOENÇA", lt - 0.1, y=330, size=66, bg="#4a2f1a", fg="#ffffff")


def s18(cv, lt, d, T):  # John Waller: fear + stress -> collective trance
    sky_day(cv, T)
    plate(cv, "square", 1.05, cy=820, sigma=4, bright=0.9)
    toon2(cv, 540, 1655, 1.3, T, outfit="waller", expr="smile", pose="think", look=0, seed=7)
    date_stamp(cv, "JOHN WALLER", lt - 0.1, y=300, size=96)
    banner(cv, "HISTORIADOR", lt - 0.6, y=440, size=58, bg="#1b2a4a", fg="#ffd54a")
    if lt > 1.5:
        a = eout((lt - 1.5) / 0.3)
        f = skia.Font(TF, 64); t = "TRANSE COLETIVO"
        cv.drawString(t, 540 - f.measureText(t) / 2, 560, f, stroke(C("#14100c", 255 * a), 12))
        cv.drawString(t, 540 - f.measureText(t) / 2, 560, f, fill(C("#ffffff", 255 * a)))


def s19(cv, lt, d, T):  # not poison, not bodily disease
    sky_day(cv, T)
    plate(cv, "street", 1.04, cy=760, sigma=2, bright=0.95)
    # crossed-out items: rye/poison + illness
    f = skia.Font(TF, 72)
    f0 = skia.Font(TF, 70)
    cv.drawString("NÃO ERA...", 540 - f0.measureText("NÃO ERA...") / 2, 300, f0, fill(C("#ffffff")))
    yy = 460
    for t in ("VENENO", "DOENÇA DO CORPO"):
        w = f.measureText(t); x = 540 - w / 2
        cv.drawString(t, x, yy, f, stroke(C("#14100c"), 12))
        cv.drawString(t, x, yy, f, fill(C("#ffffff")))
        p = eout(clamp((lt - 0.3) / 0.6))
        cv.drawLine(x - 20, yy - 24, x - 20 + (w + 40) * p, yy - 24 + 8, stroke(C("#e23b2e"), 16))
        yy += 120


def s20(cv, lt, d, T):  # close the loop: fear of a curse
    sky_day(cv, T)
    plate(cv, "street", P(lt, d, 1.0, 1.08), cy=760)
    crowd(cv, T, [(230, 1640, 0.95), (540, 1680, 1.05), (840, 1650, 0.95), (400, 1730, 0.8)], 1.15)
    notes(cv, T, 540, 1500, 6)
    banner(cv, "NÃO CONSEGUIA PARAR", lt - 0.1, y=330, size=72, bg="#9c3b3b", fg="#ffffff")


SHOTS = []


def add(s, e, fn, *a):
    SHOTS.append((s, e, fn, a))


add(0, L[2]["s"], s01, ws(1, "dançar", 1) if False else L[1]["s"] + 2.6)
add(L[2]["s"], L[3]["s"], s02)
add(L[3]["s"], L[4]["s"], s03)
add(L[4]["s"], L[5]["s"], s04)
add(L[5]["s"], L[6]["s"], s05)
add(L[6]["s"], L[7]["s"], s06)
add(L[7]["s"], L[8]["s"], s07)
add(L[8]["s"], L[9]["s"], s08)
add(L[9]["s"], L[10]["s"], s09)
add(L[10]["s"], L[11]["s"], s10)
add(L[11]["s"], L[12]["s"], s11)
add(L[12]["s"], L[13]["s"], s12)
add(L[13]["s"], L[14]["s"], s13)
add(L[14]["s"], L[15]["s"], s14)
add(L[15]["s"], L[16]["s"], s15)
add(L[16]["s"], L[17]["s"], s16)
add(L[17]["s"], L[18]["s"], s17)
add(L[18]["s"], L[19]["s"], s18)
add(L[19]["s"], L[20]["s"], s19)
add(L[20]["s"], DUR + 0.01, s20)


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
