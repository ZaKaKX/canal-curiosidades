"""EP04 — As estátuas gregas nunca foram brancas (PT-BR). 3D inked plates + sketch characters.
usage: render.py timings.json a b out.mp4 kitdir platesdir"""
import sys, json, math, subprocess
sys.path.insert(0, sys.argv[5])
from gfx import *
import gfx
import toon2 as T2
from toon2 import toon2, ink, sk

gfx.KEYWORDS.clear()
gfx.KEYWORDS.update({"brancas", "grécia", "mil", "quinhentos", "escultor", "mármore", "pintada", "pele", "olhos", "cabelo",
                     "desenhos", "colorido", "séculos", "sumindo", "renascimento", "branca", "propósito", "michelangelo",
                     "1764", "winckelmann", "branco", "bonito", "século", "1937", "museu", "britânico", "rasparam",
                     "partenon", "cobre", "reviravolta", "brinkmann", "ultravioleta", "desenhos", "2023", "azul",
                     "egípcio", "brilha", "infravermelha", "microscópicos", "tempo", "cores", "nunca"})
T2.OUTFITS.update({
    "greek": dict(body="#e9dcc0", trim="#b5452a", hat="none"),
    "painter": dict(body="#c8562e", trim="#e9dcc0", hat="none"),
    "ren": dict(body="#5b2a5e", trim="#e2b54b", hat="none"),
    "scholar": dict(body="#3a2b1f", trim="#e9dcc0", hat="none"),
    "worker": dict(body="#59606a", trim="#e9dcc0", hat="cap"),
    "lab": dict(body="#f2f2ee", trim="#2f6fd6", hat="none"),
})

TJ = json.load(open(sys.argv[1]))
PL = sys.argv[6]
L = {l["i"]: l for l in TJ["lines"]}
DUR = TJ["duration"]
CHUNKS = build_chunks(TJ)
FIX = {"vínquelman": "Winckelmann", "brinkman": "Brinkmann"}
for ch in CHUNKS:  # on-screen spelling of names written phonetically for the voice
    ch["words"] = [w.replace(w.strip(".,!?"), FIX[w.strip(".,!?").lower()]) if w.strip(".,!?").lower() in FIX else w for w in ch["words"]]
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


# statue anchors in st_* plates (frame px)
ST = dict(head=(540, 667), face=(560, 690), eyes=(527, 650), hair=(490, 730), torso=(540, 867), skirt=(450, 1090), plinth_top=1253)


# ---------- 2D layers ----------

def sky_day(cv, T):
    sky(cv, "#4f8fd0", "#f1e7d2", H); sun_glow(cv, 860, 380, 560, "#fff4cf", 170)
    for i, (x, y, w) in enumerate(((220, 300, 260), (760, 200, 300), (520, 480, 220))):
        xx = (x + T * 8 * (1 + i * 0.3)) % (W + 400) - 200
        for k in range(4):
            cv.drawCircle(xx - w * 0.35 + k * w * 0.23, y - (k % 2) * 30, w * 0.22, fill(C("#ffffff", 210)))
        cv.drawRect(skia.Rect(xx - w * 0.45, y, xx + w * 0.45, y + w * 0.12), fill(C("#ffffff", 210)))


def sky_warm(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1100, [C("#3f6fb0"), C("#9fb6d6"), C("#f6d9a8")], [0, 0.55, 1]))
    sun_glow(cv, 760, 520, 600, "#ffe9b8", 190)


def dark_room(cv, T, col="#120a22"):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C(col), C("#05030a")]))


def red_pulse(cv, T, col="#c0161c"):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#0a0405")))
    cv.drawCircle(540, 900, 900, rad(540, 900, 900, [C(col, 150 * (0.7 + 0.3 * math.sin(T * 12))), C("#000000", 0)]))


def sparkles(cv, T, cx, cy, rx, ry, n=12, col="#fff3b0", seed=0):
    for i in range(n):
        ph = (T * 0.9 + i / n + seed) % 1
        x = cx + rx * math.sin(i * 2.39 + seed); y = cy + ry * math.cos(i * 1.71 + seed)
        r = 24 * math.sin(ph * math.pi)
        p = poly([(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25), (x, y + r), (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)])
        cv.drawPath(p, fill(C(col, 240)))


def chips(cv, T, x, y, n=10, col="#f4f1ea"):
    for i in range(n):
        ph = (T * 2.2 + i / n) % 1
        a = -math.pi * (0.15 + 0.7 * ((i * 37) % n) / n)
        px = x + math.cos(a) * 260 * ph; py = y + math.sin(a) * 200 * ph + 500 * ph * ph
        r = 10 * (1 - ph) + 4
        q = poly([(px - r, py), (px, py - r), (px + r, py + r * 0.4)])
        cv.drawPath(q, fill(C(col, 255 * (1 - ph)))); cv.drawPath(q, stroke(C("#231a14", 200 * (1 - ph)), 3))


def rain(cv, T, a=170, n=60):
    for i in range(n):
        ph = (T * 1.6 + i * 0.137) % 1
        x = (i * 97) % W + 40 * ph; y = -100 + ph * (H + 200)
        cv.drawLine(x, y, x - 18, y + 60, stroke(C("#d9ecff", a), 4))


def dust(cv, T, a=150, n=40, col="#d9b98a"):
    for i in range(n):
        ph = (T * 0.25 + i * 0.173) % 1
        x = (i * 131 + ph * 400) % (W + 200) - 100; y = 300 + (i * 211) % 1200 - ph * 120
        cv.drawCircle(x, y, 6 + (i % 4) * 3, fill(C(col, a * math.sin(ph * math.pi))))


def hand(x, y, s, pose, side=1):
    hl, hr = T2.HANDS[pose]
    h = hr if side > 0 else hl
    return x + h[0] * s, y + h[1] * s


def prop(cv, kind, x, y, s, T, ang=0.0):
    cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(s, s)
    if kind == "hammer":
        sk(cv, poly([(-8, 0), (8, 0), (8, -150), (-8, -150)]), "#8a5a2b", 5, 1)
        sk(cv, poly([(-45, -150), (45, -150), (45, -195), (-45, -195)]), "#6d6f75", 6, 2)
    elif kind == "chisel":
        sk(cv, poly([(-7, 0), (7, 0), (7, -110), (0, -130), (-7, -110)]), "#9aa0a8", 5, 3)
    elif kind == "brush":
        sk(cv, poly([(-7, 0), (7, 0), (7, -150), (-7, -150)]), "#d8b06a", 5, 1)
        sk(cv, poly([(-14, -150), (14, -150), (8, -200), (0, -215), (-8, -200)]), "#d6372b", 5, 2)
    elif kind == "scraper":
        sk(cv, poly([(-7, 0), (7, 0), (7, -120), (-7, -120)]), "#8a5a2b", 5, 1)
        sk(cv, poly([(-40, -120), (40, -120), (32, -165), (-32, -165)]), "#c87533", 6, 2)
    elif kind == "shovel":
        sk(cv, poly([(-7, 60), (7, 60), (7, -220), (-7, -220)]), "#8a5a2b", 5, 1)
        sk(cv, poly([(-40, 60), (40, 60), (30, 150), (0, 175), (-30, 150)]), "#7f858c", 6, 2)
    elif kind == "quill":
        sk(cv, poly([(0, 0), (30, -150), (6, -120), (-4, -10)]), "#fbfbf6", 5, 1)
    elif kind == "book":
        sk(cv, poly([(-110, -60), (0, -40), (110, -60), (110, 40), (0, 60), (-110, 40)]), "#fbf3df", 6, 2)
        cv.drawLine(0, -40, 0, 60, ink(4, 1))
        for k in range(4):
            cv.drawLine(-90, -30 + k * 18, -20, -22 + k * 18, ink(3, k)); cv.drawLine(20, -22 + k * 18, 90, -30 + k * 18, ink(3, k + 2))
    elif kind == "lamp":
        sk(cv, poly([(-12, 0), (12, 0), (12, -80), (-12, -80)]), "#3a3d44", 5, 1)
        sk(cv, poly([(-40, -80), (40, -80), (55, -150), (-55, -150)]), "#2a2d34", 6, 2)
        cv.drawRect(skia.Rect(-50, -158, 50, -146), fill(C("#b98cff")))
    cv.restore()


def beret(cv, x, y, s):
    hy = y - 505 * s - 150 * s
    cv.save(); cv.translate(x, hy); cv.scale(s, s)
    p = skia.Path(); p.addOval(skia.Rect(-150, -60, 170, 40)); sk(cv, p, "#2c1630", 7, 1)
    cv.drawCircle(10, -66, 12, fill(C("#231a14")))
    cv.restore()


def wig(cv, x, y, s):
    hy = y - 505 * s
    cv.save(); cv.translate(x, hy); cv.scale(s, s)
    for sx in (-1, 1):
        for k in range(3):
            p = skia.Path(); p.addCircle(sx * 165, -40 + k * 50, 34); sk(cv, p, "#f1efe8", 6, k)
    p = skia.Path(); p.addOval(skia.Rect(-150, -190, 150, -110)); sk(cv, p, "#f1efe8", 6, 4)
    cv.restore()


def wreath(cv, x, y, s):
    hy = y - 505 * s - 120 * s
    cv.save(); cv.translate(x, hy); cv.scale(s, s)
    for k in range(9):
        a = math.radians(200 + k * 17)
        px, py = 170 * math.cos(a), 60 * math.sin(a) + 10
        p = skia.Path(); p.addOval(skia.Rect(px - 26, py - 14, px + 26, py + 14)); sk(cv, p, "#6f9a3a", 4, k)
    cv.restore()


def statue_wipe(cv, k, z=1.0, cx=W / 2, cy=H / 2, top_down=False, a="st_white", b="st_paint"):
    """b revealed over a with a painterly wipe (k 0..1)."""
    plate(cv, a, z, cx, cy)
    if k <= 0: return
    y = H * (1 - k) if not top_down else H * k
    p = skia.Path(); p.moveTo(-10, y)
    for i in range(13):
        xx = i * 95; p.lineTo(xx, y + 30 * math.sin(i * 1.7 + k * 9))
    if not top_down:
        p.lineTo(W + 10, H + 10); p.lineTo(-10, H + 10)
    else:
        p.lineTo(W + 10, -10); p.lineTo(-10, -10)
    p.close()
    cv.save(); cv.clipPath(p, doAntiAlias=True); plate(cv, b, z, cx, cy); cv.restore()


def stone_tag(cv, text, x, y, lt, tx, ty):
    a = eout(lt / 0.25)
    if a <= 0: return
    cv.drawLine(x, y, lerp(x, tx, a), lerp(y, ty, a), stroke(C("#14100c", 255 * a), 6))
    cv.drawCircle(x, y, 12, fill(C("#ffd54a", 255 * a))); cv.drawCircle(x, y, 12, stroke(C("#14100c", 255 * a), 4))
    f = skia.Font(TF, 58); w = f.measureText(text)
    r = skia.Rect(tx - w / 2 - 22, ty - 50, tx + w / 2 + 22, ty + 18)
    cv.save(); cv.translate(tx, ty); cv.scale(lerp(0.6, 1, a), lerp(0.6, 1, a)); cv.translate(-tx, -ty)
    cv.drawRoundRect(r, 18, 18, fill(C("#f3e4bf", 255 * a))); cv.drawRoundRect(r, 18, 18, stroke(C("#1b1410", 255 * a), 6))
    cv.drawString(text, tx - w / 2, ty, f, fill(C("#2a1d12", 255 * a)))
    cv.restore()


def blue_glow(cv, T, pts, a=1.0, r0=60):
    for i, (x, y, r) in enumerate(pts):
        pul = 0.75 + 0.25 * math.sin(T * 5 + i * 1.3)
        cv.drawCircle(x, y, r * 3, rad(x, y, r * 3, [C("#58a6ff", 140 * a * pul), C("#58a6ff", 0)]))
        cv.drawCircle(x, y, r, fill(C("#bfe3ff", 230 * a * pul)))


GLOW = [(310, 900, 22), (360, 960, 14), (420, 1010, 18), (660, 880, 20), (720, 940, 15), (780, 1000, 12), (540, 1060, 10),
        (250, 1050, 12), (830, 1060, 16), (470, 880, 9), (600, 990, 11)]


# ---------- scenes ----------

def s01(cv, lt, d, T, tn, tb):  # hook: white statue -> it was never white
    sky_day(cv, T)
    z = P(lt, d, 1.0, 1.1)
    k = ease(clamp((T - tn) / 0.6)) if T > tn else 0
    statue_wipe(cv, k, z, cy=760)
    if k > 0.2: sparkles(cv, T, 540, 900, 300, 420, 14)
    if T > tb:
        a = eout((T - tb) / 0.25)
        cv.save(); cv.translate(540, 330); cv.scale(lerp(1.5, 1, a), lerp(1.5, 1, a))
        f = skia.Font(TF, 120); t = "BRANCAS?"
        cv.drawString(t, -f.measureText(t) / 2, 0, f, stroke(C("#14100c", 255 * a), 16))
        cv.drawString(t, -f.measureText(t) / 2, 0, f, fill(C("#ffffff", 255 * a)))
        if T > tn: cv.drawLine(-330, -40, -330 + 660 * eout((T - tn) / 0.3), -40, stroke(C("#e23b2e"), 22))
        cv.restore()


def s02(cv, lt, d, T):
    sky_warm(cv, T)
    plate(cv, "temple", P(lt, d, 1.0, 1.1), cy=900, dx=lerp(20, -20, ease(lt / d)))
    date_stamp(cv, "GRÉCIA", lt - 0.1, y=330, size=150)
    banner(cv, "HÁ 2.500 ANOS", lt - 0.8, y=500, size=74, bg="#1b2a4a", fg="#ffd54a")


def s03(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "st_white", 1.04, cy=760)
    x, y, s = 230, 1620, 1.0
    ph = math.sin(T * 9)
    toon2(cv, x, y, s, T, outfit="greek", expr="determined", pose="point", look=1)
    hx, hy = hand(x, y, s, "point")
    prop(cv, "chisel", hx + 10, hy, 0.9, T, 60)
    prop(cv, "hammer", hx - 30, hy + 60, 0.9, T, -40 + 30 * ph)
    chips(cv, T, hx + 120, hy - 30, 12)
    banner(cv, "MÁRMORE", lt - 0.8, y=330, size=82)


def s04(cv, lt, d, T, tp):
    sky_day(cv, T)
    k = ease(clamp((T - tp) / 1.2))
    statue_wipe(cv, k, 1.04, cy=760)
    x, y, s = 230, 1620, 1.0
    toon2(cv, x, y, s, T, outfit="painter", expr="grin", pose="point", look=1)
    hx, hy = hand(x, y, s, "point")
    prop(cv, "brush", hx, hy, 0.9, T, 55 + 12 * math.sin(T * 7))
    for i in range(6):  # paint drops
        ph = (T * 1.5 + i / 6) % 1
        cv.drawCircle(hx + 100 + i * 18, hy - 120 + ph * 300, 9 * (1 - ph) + 3, fill(C(("#d6372b", "#2f6fd6", "#e2b54b")[i % 3], 255 * (1 - ph))))


def s05(cv, lt, d, T, tags):
    sky_day(cv, T)
    z = P(lt, d, 1.12, 1.24)
    plate(cv, "st_paint", z, cx=540, cy=820)
    def at(p):
        return 540 + (p[0] - 540) * z, 820 + (p[1] - 820) * z
    spots = (("PELE", ST["face"], (210, 560)), ("OLHOS", ST["eyes"], (860, 470)), ("CABELO", ST["hair"], (860, 640)),
             ("ROUPAS", ST["skirt"], (230, 1150)))
    for (name, p, tp), tt in zip(spots, tags):
        if T > tt:
            x, y = at(p); stone_tag(cv, name, x, y, T - tt, *tp)
    if T > tags[4]:
        banner(cv, "TUDO COLORIDO", T - tags[4], y=330, size=86, bg="#d6372b", fg="#ffffff")
        sparkles(cv, T, 540, 900, 380, 500, 16)


def s06(cv, lt, d, T):  # centuries pass: day/night cycling
    ph = (lt * 1.6) % 1
    day = 0.5 + 0.5 * math.cos(ph * 2 * math.pi)
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#0b1430"), C("#2a3560")]))
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#4f8fd0", 255 * day), C("#f1e7d2", 255 * day)]))
    a = ph * 2 * math.pi
    sx, sy = 540 + 520 * math.cos(a + math.pi), 900 - 600 * math.sin(a)
    cv.drawCircle(sx, sy, 70, fill(C("#ffe08a"))); cv.drawCircle(sx, sy, 70, stroke(C("#231a14"), 6))
    plate(cv, "st_paint", 1.04, cy=760, bright=lerp(0.45, 1.0, day))
    date_stamp(cv, "SÉCULOS", lt - 0.1, y=330, size=150)


def s07(cv, lt, d, T, t_rain, t_dirt, t_fade):
    sky_day(cv, T)
    if T > t_rain: cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#2a3550", 120)))
    k = ease(clamp((T - t_fade) / 1.6))
    statue_wipe(cv, k, 1.04, cy=760, a="st_paint", b="st_white", top_down=True)
    if T < t_rain:
        rays(cv, 860, 120, T, col="#fff0c8", n=9, a=40, spread=80, base=110)
    if T > t_rain: rain(cv, T, 180 if T < t_dirt else 90)
    if T > t_dirt: dust(cv, T, 170)


def s08(cv, lt, d, T, tr):
    sky_day(cv, T)
    plate(cv, "ruins", P(lt, d, 1.0, 1.07), cy=820)
    x, y, s = 250, 1620, 1.0
    toon2(cv, x, y, s, T, outfit="ren", expr="shock" if lt < 2.0 else "grin", pose="point", look=1)
    beret(cv, x, y, s)
    hx, hy = hand(x, y, s, "point")
    prop(cv, "shovel", hx, hy, 0.9, T, -20)
    if T > tr: banner(cv, "RENASCIMENTO", T - tr, y=330, size=84, bg="#1b2a4a", fg="#ffd54a")


def s09(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "ruins", 1.12, cy=820, sigma=5)
    zoom(cv, lerp(1.0, 1.18, eout(lt / d)), 540, 1100)
    toon2(cv, 540, 1690, 1.2, T, outfit="ren", expr="joy", pose="hips", look=0)
    beret(cv, 540, 1690, 1.2)
    sparkles(cv, T, 540, 800, 380, 250, 10)
    if lt > 1.2:
        a = eout((lt - 1.2) / 0.25)
        f = skia.Font(TF, 96); t = "DE PROPÓSITO!"
        cv.drawString(t, 540 - f.measureText(t) / 2, 360, f, stroke(C("#14100c", 255 * a), 14))
        cv.drawString(t, 540 - f.measureText(t) / 2, 360, f, fill(C("#ffffff", 255 * a)))


def s10(cv, lt, d, T, tm):
    sky_warm(cv, T)
    plate(cv, "st_white", P(lt, d, 1.0, 1.06), cy=760)
    x, y, s = 230, 1620, 1.0
    toon2(cv, x, y, s, T, outfit="ren", expr="determined", pose="point", look=1, seed=2)
    beret(cv, x, y, s)
    hx, hy = hand(x, y, s, "point")
    prop(cv, "chisel", hx + 10, hy, 0.9, T, 60); prop(cv, "hammer", hx - 30, hy + 60, 0.9, T, -40 + 30 * math.sin(T * 9))
    chips(cv, T, hx + 120, hy - 30, 10)
    if T > tm: banner(cv, "MICHELANGELO", T - tm, y=330, size=84)


def s11(cv, lt, d, T, tq):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#2a2420")))
    plate(cv, "gallery", 1.1, cy=900, sigma=6, bright=0.8)
    cv.drawCircle(540, 1200, 800, rad(540, 1200, 800, [C("#ffd27a", 70), C("#ffd27a", 0)]))
    x, y, s = 540, 1690, 1.2
    toon2(cv, x, y, s, T, outfit="scholar", expr="smug" if T > tq else "smile", pose="think", look=0.4)
    wig(cv, x, y, s)
    prop(cv, "book", x - 10, y - 280 * s, 1.0, T, 0)
    hx, hy = hand(x, y, s, "think")
    prop(cv, "quill", hx, hy, 0.9, T, 10 * math.sin(T * 6))
    date_stamp(cv, "1764", lt - 0.1, y=300, size=140)
    banner(cv, "WINCKELMANN", lt - 0.9, y=450, size=70, bg="#1b2a4a", fg="#ffd54a")
    if T > tq:
        a = eout((T - tq) / 0.3)
        f = skia.Font(TF, 62)
        for j, t in enumerate(("QUANTO MAIS BRANCO,", "MAIS BONITO")):
            yy = 610 + j * 76
            cv.drawString(t, 540 - f.measureText(t) / 2, yy, f, stroke(C("#14100c", 255 * a), 12))
            cv.drawString(t, 540 - f.measureText(t) / 2, yy, f, fill(C("#ffffff" if j == 0 else "#ffd54a", 255 * a)))


def s12(cv, lt, d, T):
    sky_warm(cv, T)
    plate(cv, "st_white", 1.06, cy=760, sigma=3)
    rays(cv, 540, 760, T, n=12, a=26, spread=360, base=0)
    plate(cv, "st_white", 1.06, cy=760)
    outfits = ("ren", "scholar", "greek", "worker", "ren", "scholar")
    for i, of in enumerate(outfits):
        x = 110 + i * 172; y = 1700 + (i % 2) * 70
        toon2(cv, x, y, 0.5, T, outfit=of, expr="joy" if i % 2 else "grin", pose="wave" if i % 3 == 0 else "stand",
              look=(1 if x < 540 else -1) * 0.7, seed=i)
    banner(cv, "+1 SÉCULO", lt - 1.0, y=330, size=90, bg="#1b2a4a", fg="#ffd54a")


def worker_scrape(cv, T, x, y, s, ph):
    dx = 40 * math.sin(T * 10 + ph)
    toon2(cv, x + dx * 0.3, y, s, T, outfit="worker", expr="determined", pose="reach", look=0, seed=ph, shadow=False)
    hx, hy = hand(x + dx * 0.3, y, s, "reach")
    prop(cv, "scraper", hx + dx, hy + 30, 0.8, T, 160)
    chips(cv, T + ph, hx + dx, hy - 90, 6, "#ffffff")


def s13(cv, lt, d, T, tb):
    plate(cv, "frieze", P(lt, d, 1.0, 1.05), cy=900)
    worker_scrape(cv, T, 300, 2150, 0.9, 0.0)
    worker_scrape(cv, T, 780, 2150, 0.9, 1.7)
    date_stamp(cv, "1937", lt - 0.1, y=300, size=140)
    if T > tb: banner(cv, "MUSEU BRITÂNICO", T - tb, y=450, size=70, bg="#1b2a4a", fg="#ffd54a")


def s14(cv, lt, d, T, tc):
    k = ease(lt / d)
    plate(cv, "frieze", 1.05, cy=900, bright=lerp(1.0, 1.35, k))
    worker_scrape(cv, T, 300, 2150, 0.9, 0.0)
    worker_scrape(cv, T, 780, 2150, 0.9, 1.7)
    dust(cv, T, 160, 40, "#f4f1ea")
    sparkles(cv, T, 540, 880, 400, 200, 12, "#ffffff")
    banner(cv, "FERRAMENTAS DE COBRE", lt - 0.05, y=330, size=64, bg="#c87533", fg="#ffffff")


def s15(cv, lt, d, T):
    red_pulse(cv, T)
    zoom(cv, lerp(1.0, 1.35, eout(lt / d)), 540, 820)
    toon2(cv, 540, 1720, 1.7, T, outfit="lab", expr="shock")


def lamp_cone(cv, ox, oy, ang, spread=22, length=1500):
    a0, a1 = math.radians(ang - spread), math.radians(ang + spread)
    p = skia.Path(); p.moveTo(ox, oy)
    p.lineTo(ox + math.cos(a0) * length, oy + math.sin(a0) * length)
    p.lineTo(ox + math.cos(a1) * length, oy + math.sin(a1) * length); p.close()
    return p


def s16(cv, lt, d, T, tu):
    dark_room(cv, T)
    plate(cv, "st_white", 1.04, cy=760, bright=0.28)
    x, y, s = 200, 1620, 1.0
    toon2(cv, x, y, s, T, outfit="lab", expr="determined", pose="point", look=1, seed=3)
    hx, hy = hand(x, y, s, "point")
    ang = math.degrees(math.atan2(860 - (hy - 120), 540 - hx)) + 10 * math.sin(lt * 1.3)
    if T > tu:
        cone = lamp_cone(cv, hx, hy - 120, ang)
        cv.save(); cv.clipPath(cone, doAntiAlias=True)
        plate(cv, "st_uv", 1.04, cy=760)
        cv.drawPath(cone, fill(C("#9b6bff", 50)))
        cv.restore()
    prop(cv, "lamp", hx, hy, 0.9, T, ang + 90)
    banner(cv, "LUZ ULTRAVIOLETA", lt - 0.4, y=330, size=74, bg="#5b2fa8", fg="#ffffff")
    if lt > 0.8: banner(cv, "VINZENZ BRINKMANN", lt - 0.8, y=470, size=56)


def s17(cv, lt, d, T):
    dark_room(cv, T)
    plate(cv, "st_uv", P(lt, d, 1.08, 1.22), cx=540, cy=820)
    sparkles(cv, T, 540, 950, 330, 420, 14, "#c9b2ff")
    cv.drawCircle(540, 900, 700, rad(540, 900, 700, [C("#8a5cff", 50 + 30 * math.sin(T * 4)), C("#8a5cff", 0)]))


def s18(cv, lt, d, T, tb):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#05070c")))
    plate(cv, "frieze", P(lt, d, 1.0, 1.08), cy=900, bright=0.25)
    if T > tb:
        blue_glow(cv, T, GLOW, eout((T - tb) / 0.5))
    date_stamp(cv, "2023", lt - 0.1, y=300, size=140)
    if T > tb: banner(cv, "AZUL EGÍPCIO", T - tb, y=450, size=80, bg="#1f4fd6", fg="#ffffff")


def s19(cv, lt, d, T):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#05070c")))
    z = P(lt, d, 1.35, 1.55)
    plate(cv, "frieze", z, cx=440, cy=950, bright=0.22)
    pts = [(440 + (x - 440) * z, 950 + (y - 950) * z, r * 0.6) for x, y, r in GLOW]
    blue_glow(cv, T, pts, 1.0)
    for i in range(30):  # tiny specks
        x = (i * 173) % W; y = 600 + (i * 251) % 800
        cv.drawCircle(x, y, 3 + (i % 3), fill(C("#bfe3ff", 200 * (0.5 + 0.5 * math.sin(T * 6 + i)))))
    # camera viewfinder
    st = stroke(C("#ffffff"), 8)
    for (x0, y0, dx, dy) in ((90, 520, 1, 1), (990, 520, -1, 1), (90, 1250, 1, -1), (990, 1250, -1, -1)):
        cv.drawLine(x0, y0, x0 + dx * 90, y0, st); cv.drawLine(x0, y0, x0, y0 + dy * 90, st)
    if int(T * 2) % 2 == 0: cv.drawCircle(130, 330, 20, fill(C("#e23b2e")))
    f = skia.Font(TF, 52); cv.drawString("REC", 165, 348, f, fill(C("#ffffff")))
    banner(cv, "INFRAVERMELHO", lt - 0.2, y=470, size=64, bg="#7a1f2b", fg="#ffffff")


def s20(cv, lt, d, T):
    sky_day(cv, T)
    xs = 540 + 330 * math.sin(lt * 1.4)
    plate(cv, "st_white", 1.06, cy=760)
    cv.save(); cv.clipRect(skia.Rect(xs, 0, W, H)); plate(cv, "st_paint", 1.06, cy=760); cv.restore()
    cv.drawLine(xs, 0, xs, H, stroke(C("#14100c"), 14)); cv.drawLine(xs, 0, xs, H, stroke(C("#ffd54a"), 7))
    cv.drawCircle(xs, 900, 40, fill(C("#ffd54a"))); cv.drawCircle(xs, 900, 40, stroke(C("#14100c"), 7))
    f = skia.Font(TF, 58)
    for t, x in (("TEMPO", 200), ("ORIGINAL", 880)):
        cv.drawString(t, x - f.measureText(t) / 2, 330, f, stroke(C("#14100c"), 12))
        cv.drawString(t, x - f.measureText(t) / 2, 330, f, fill(C("#ffffff" if t == "TEMPO" else "#ffd54a")))


def s21(cv, lt, d, T):
    sky_day(cv, T)
    rays(cv, 540, 760, T, n=12, a=30, spread=360, base=0)
    plate(cv, "st_paint", P(lt, d, 1.0, 1.1), cy=760)
    sparkles(cv, T, 540, 900, 380, 520, 18)
    x, y, s = 200, 1610, 0.95
    toon2(cv, x, y, s, T, outfit="greek", expr="joy", pose="wave", look=1)
    wreath(cv, x, y, s)
    toon2(cv, 880, 1610, 0.95, T, outfit="lab", expr="grin", pose="hips", look=-1, seed=4)
    banner(cv, "NUNCA FORAM BRANCAS", lt - 0.1, y=330, size=74, bg="#d6372b", fg="#ffffff")


SHOTS = []


def add(s, e, fn, *a):
    SHOTS.append((s, e, fn, a))


add(0, L[2]["s"], s01, ws(1, "nunca"), ws(1, "brancas")); add(L[2]["s"], L[3]["s"], s02); add(L[3]["s"], L[4]["s"], s03)
add(L[4]["s"], L[5]["s"], s04, ws(4, "pintada")); add(L[5]["s"], L[6]["s"], s05, (ws(5, "pele"), ws(5, "olhos"), ws(5, "cabelo"), ws(5, "roupas"), ws(5, "tudo")))
add(L[6]["s"], L[7]["s"], s06); add(L[7]["s"], L[8]["s"], s07, ws(7, "chuva"), ws(7, "terra"), ws(7, "tinta"))
add(L[8]["s"], L[9]["s"], s08, ws(8, "renascimento")); add(L[9]["s"], L[10]["s"], s09); add(L[10]["s"], L[11]["s"], s10, ws(10, "michelangelo"))
add(L[11]["s"], L[12]["s"], s11, ws(11, "quanto")); add(L[12]["s"], L[13]["s"], s12)
add(L[13]["s"], ws(13, "rasparam"), s13, ws(13, "museu")); add(ws(13, "rasparam"), L[15]["s"], s14, 0)
add(L[15]["s"], L[16]["s"], s15); add(L[16]["s"], L[17]["s"], s16, ws(16, "apontou")); add(L[17]["s"], L[18]["s"], s17)
add(L[18]["s"], L[19]["s"], s18, ws(18, "azul")); add(L[19]["s"], L[20]["s"], s19); add(L[20]["s"], L[21]["s"], s20)
add(L[21]["s"], DUR + 0.01, s21)


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
