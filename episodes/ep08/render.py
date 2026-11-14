"""EP08 — A onda de melaço que matou 21 pessoas (Boston, 1919). PT-BR.
3D inked plates (porto com tanque, tanque contra-plongée, tanque estourado, rua do North End, rua inundada,
trilho do trem elevado entortado, laboratório de Harvard) + personagens 2D. usage: render.py timings.json a b out.mp4 kitdir platesdir"""
import sys, json, math, subprocess
import numpy as np
KW = {"1919", "onda", "21", "boston", "água", "janeiro", "tanque", "15", "metros", "melaço", "xarope", "grosso", "escuro",
      "cana-de-açúcar", "álcool", "munição", "guerra", "vazava", "começo", "marrom", "vazamentos", "baldes", "17", "negativos",
      "5", "graus", "meio-dia", "estourou", "8", "milhões", "litros", "56", "quilômetros", "casas", "trilho", "elevado",
      "cavalos", "reviravolta", "pior", "velocidade", "noite", "caiu", "cola", "preso", "pesadelo", "mortos", "150",
      "feridos", "2016", "harvard", "frio", "cheiro", "doce"}
OUT = {
    "worker":  dict(body="#4a5a6a", trim="#e8dcc0", hat="cap"),
    "kid":     dict(body="#b03a2e", trim="#f2e6c8", hat="none"),
    "woman":   dict(body="#6a4a7a", trim="#f2e6c8", hat="none"),
    "painter": dict(body="#7a6a4a", trim="#f2e6c8", hat="cap"),
    "rescuer": dict(body="#2a3a5a", trim="#f7f3ea", hat="sailor"),
    "sci":     dict(body="#e9edf2", trim="#3a6ab0", hat="none"),
    "sci2":    dict(body="#e9edf2", trim="#b03a2e", hat="none"),
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


def night_cf(k=1.0):
    a = lerp(1, 0.38, k); b = lerp(1, 0.5, k); c = lerp(1, 0.85, k)
    return skia.ColorFilters.Matrix([a, 0, 0, 0, 0, 0, b, 0, 0, 0.01 * k, 0, 0, c, 0, 0.06 * k, 0, 0, 0, 1, 0])


def red_cf():
    return skia.ColorFilters.Matrix([0.9, 0.2, 0.1, 0, 0.06, 0.15, 0.35, 0.1, 0, 0, 0.12, 0.2, 0.3, 0, 0, 0, 0, 0, 1, 0])


def stamp(cv, text, lt, x, y, size=110, col="#c0161c", ang=-12):
    if lt <= 0: return
    a = eout(lt / 0.2)
    f = skia.Font(TF, size); wd = f.measureText(text)
    cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(lerp(1.8, 1, a), lerp(1.8, 1, a))
    r = skia.Rect(-wd / 2 - 30, -size * 0.95, wd / 2 + 30, size * 0.35)
    cv.drawRoundRect(r, 16, 16, stroke(C(col, 235 * a), 12))
    cv.drawString(text, -wd / 2, 0, f, fill(C(col, 235 * a)))
    cv.restore()



# ---------- EP08 helpers ----------
MOL_D, MOL_M, MOL_L = "#1a0a03", "#3a1806", "#8a4a16"


def sky_winter(cv, T):
    sky(cv, "#7e97b3", "#e6e3da", H)
    sun_glow(cv, 760, 360, 480, "#fff6e0", 120)
    for i, (x, y, w) in enumerate(((200, 240, 300), (760, 170, 340), (520, 420, 230))):
        xx = (x + T * 6 * (1 + i * 0.3)) % (W + 400) - 200
        for k in range(4):
            cv.drawCircle(xx - w * 0.35 + k * w * 0.23, y - (k % 2) * 30, w * 0.22, fill(C("#f4f2ec", 200)))
        cv.drawRect(skia.Rect(xx - w * 0.45, y, xx + w * 0.45, y + w * 0.12), fill(C("#f4f2ec", 200)))


def sky_dusk(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1100, [C("#141a33"), C("#3a3150"), C("#7a5560")], [0, 0.6, 1]))
    stars(cv, T, 0.6, ymax=H * 0.35)


def mol_wave(cv, y, T, amp=40, k=0.012, speed=2.2, drips=True, alpha=255, foam=True):
    """2D molasses surface from y down to the bottom: glossy dark brown, wobbly crest, drips."""
    p = skia.Path(); p.moveTo(-20, H + 20)
    pts = []
    for x in range(-20, W + 41, 20):
        yy = y + amp * math.sin(x * k + T * speed) + amp * 0.4 * math.sin(x * k * 2.3 - T * speed * 1.4)
        pts.append((x, yy)); p.lineTo(x, yy)
    p.lineTo(W + 40, H + 20); p.close()
    pt = skia.Paint(AntiAlias=True)
    pt.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y - amp), skia.Point(0, y + 700)], [C(MOL_M, alpha), C(MOL_D, alpha)]))
    cv.drawPath(p, pt)
    cv.drawPath(p, ink(7, int(T * 8) % 3))
    # glossy highlight just under the crest
    hp = skia.Path(); hp.moveTo(*pts[0])
    for x, yy in pts[1:]:
        hp.lineTo(x, yy + 22)
    cv.drawPath(hp, stroke(C(MOL_L, 0.7 * alpha), 9))
    for i in range(7):  # glints
        gx = (i * 173 + T * 60) % (W + 100) - 50
        gy = y + 90 + (i * 61) % 260
        cv.drawOval(skia.Rect(gx - 40, gy - 6, gx + 40, gy + 6), fill(C("#c88a4a", 0.35 * alpha)))
    if drips:
        for i in range(9):
            ph = (T * 0.7 + i / 9) % 1
            x = (i * 131 + 40) % W
            yy = y + amp * math.sin(x * k + T * speed) - 30
            cv.drawCircle(x, yy - 60 * ph + 140 * ph * ph, 12 * (1 - ph) + 4, fill(C(MOL_M, alpha * (1 - ph))))


def big_wave(cv, k, T, x0=-60, x1=W + 60, base=H, top=500):
    """towering curling wave seen from the street: k=0..1 growth."""
    h = lerp(base, top, eout(k))
    p = skia.Path(); p.moveTo(x0, H + 40)
    n = 28
    for i in range(n + 1):
        x = lerp(x0, x1, i / n)
        yy = h + 50 * math.sin(i * 0.9 + T * 3) + 30 * math.sin(i * 2.1 - T * 4)
        p.lineTo(x, yy)
    p.lineTo(x1, H + 40); p.close()
    pt = skia.Paint(AntiAlias=True)
    pt.setShader(skia.GradientShader.MakeLinear([skia.Point(0, h), skia.Point(0, h + 900)], [C("#4a2008"), C(MOL_D)]))
    cv.drawPath(p, pt); cv.drawPath(p, ink(9, int(T * 8) % 3))
    # curling lip + streaks
    for i in range(6):
        x = 90 + i * 180 + 20 * math.sin(T * 2 + i)
        yy = h + 60 + 30 * math.sin(i * 0.9 + T * 3)
        cv.drawArc(skia.Rect(x - 80, yy - 40, x + 80, yy + 80), 200, 140, False, stroke(C(MOL_L, 200), 10))
        cv.drawLine(x - 30, yy + 160, x - 50, yy + 420, stroke(C("#6a3410", 140), 8))
    for i in range(12):  # flying blobs
        ph = (T * 0.9 + i / 12) % 1
        x = (i * 97) % W; yy = h - 40 - 200 * math.sin(ph * math.pi)
        cv.drawCircle(x, yy, 16 * (1 - ph) + 6, fill(C(MOL_M, 230 * (1 - ph))))


def bucket(cv, x, y, s, T, fill_k=0.5):
    p = poly([(x - 55 * s, y - 90 * s), (x + 55 * s, y - 90 * s), (x + 42 * s, y), (x - 42 * s, y)])
    cv.drawPath(p, fill(C("#9aa3a8"))); cv.drawPath(p, ink(6 * s, int(T * 8) % 3))
    cv.drawOval(skia.Rect(x - 55 * s, y - 102 * s, x + 55 * s, y - 78 * s), fill(C(MOL_M if fill_k > 0 else "#555", 255)))
    cv.drawOval(skia.Rect(x - 55 * s, y - 102 * s, x + 55 * s, y - 78 * s), ink(5 * s, 1))
    cv.drawArc(skia.Rect(x - 55 * s, y - 160 * s, x + 55 * s, y - 40 * s), 190, 160, False, ink(5 * s, 2))


def drip_stream(cv, x, y0, y1, T, w=14):
    cv.drawRect(skia.Rect(x - w / 2, y0, x + w / 2, y1), fill(C(MOL_M)))
    cv.drawLine(x - w / 2 + 3, y0, x - w / 2 + 3, y1, stroke(C(MOL_L, 160), 3))
    for k in range(3):
        ph = (T * 1.5 + k / 3) % 1
        cv.drawCircle(x, lerp(y0, y1, ph), w * 0.7, fill(C(MOL_M)))


def leak_drips(cv, pts, T):
    for i, (x, y, L_) in enumerate(pts):
        cv.drawRect(skia.Rect(x - 6, y, x + 6, y + L_), fill(C(MOL_M, 230)))
        ph = (T * 0.8 + i * 0.37) % 1
        r = 8 + 5 * math.sin(ph * math.pi)
        cv.drawCircle(x, y + L_ + 10 + ph * 120 * ph, r, fill(C(MOL_M, 255 * (1 - ph * 0.6))))
        cv.drawCircle(x - 2, y + L_ + 6 + ph * 120 * ph, r * 0.35, fill(C(MOL_L, 160 * (1 - ph))))


def thermo_big(cv, x, y, val, T, vmin=-20, vmax=10, label=True, col="#c0161c"):
    top, bot = y - 640, y
    r = skia.Rect(x - 50, top, x + 50, bot)
    cv.drawRoundRect(r.makeOffset(10, 12), 50, 50, fill(C("#000000", 100)))
    cv.drawRoundRect(r, 50, 50, fill(C("#f1e8d0"))); cv.drawRoundRect(r, 50, 50, ink(8, int(T * 8) % 3))
    for v in range(vmin, vmax + 1, 5):
        yy = lerp(bot - 60, top + 60, (v - vmin) / (vmax - vmin))
        cv.drawLine(x + 50, yy, x + 80, yy, stroke(C("#14100c"), 5))
        f = skia.Font(TF, 40)
        cv.drawString(f"{v}", x + 92, yy + 14, f, stroke(C("#14100c"), 8)); cv.drawString(f"{v}", x + 92, yy + 14, f, fill(C("#ffffff")))
    lv = lerp(bot - 60, top + 60, (val - vmin) / (vmax - vmin))
    cv.drawRect(skia.Rect(x - 20, lv, x + 20, bot), fill(C(col)))
    cv.drawCircle(x, bot + 30, 75, fill(C(col))); cv.drawCircle(x, bot + 30, 75, ink(8, 1))
    if label:
        f = skia.Font(TF, 120); s = f"{round(val):+d}°C".replace("+0", "0")
        cv.drawString(s, x - 420, lv + 40, f, stroke(C("#14100c"), 16)); cv.drawString(s, x - 420, lv + 40, f, fill(C("#ffd54a")))


def clock(cv, x, y, r, T, hh=12.5, a=1.0):
    p = skia.Path(); p.addCircle(x, y, r)
    cv.drawPath(p, fill(C("#f1e8d0", 255 * a))); cv.drawPath(p, ink(10, int(T * 8) % 3))
    for k in range(12):
        an = k / 12 * 2 * math.pi
        cv.drawLine(x + math.sin(an) * r * 0.82, y - math.cos(an) * r * 0.82, x + math.sin(an) * r * 0.92, y - math.cos(an) * r * 0.92, stroke(C("#14100c", 255 * a), 8))
    mn = (hh % 1) * 2 * math.pi; hr = (hh % 12) / 12 * 2 * math.pi
    cv.drawLine(x, y, x + math.sin(hr) * r * 0.5, y - math.cos(hr) * r * 0.5, stroke(C("#14100c", 255 * a), 16))
    cv.drawLine(x, y, x + math.sin(mn) * r * 0.78, y - math.cos(mn) * r * 0.78, stroke(C("#c0161c", 255 * a), 10))
    cv.drawCircle(x, y, 14, fill(C("#14100c", 255 * a)))


def shell(cv, x, y, s, T):
    b = skia.Path(); b.moveTo(x - 40 * s, y); b.lineTo(x - 40 * s, y - 170 * s); b.quadTo(x, y - 290 * s, x + 40 * s, y - 170 * s)
    b.lineTo(x + 40 * s, y); b.close()
    cv.drawPath(b, fill(C("#c9a24a"))); cv.drawPath(b, ink(6, int(T * 8) % 3))
    cv.drawRect(skia.Rect(x - 44 * s, y - 30 * s, x + 44 * s, y), fill(C("#8a6a2a")))
    cv.drawRect(skia.Rect(x - 44 * s, y - 30 * s, x + 44 * s, y), ink(5, 1))


def cane(cv, x, y, h, T, ang=0):
    cv.save(); cv.translate(x, y); cv.rotate(ang)
    for k in range(int(h / 90)):
        r = skia.Rect(-22, -k * 90 - 86, 22, -k * 90)
        cv.drawRoundRect(r, 10, 10, fill(C("#9bbf4a"))); cv.drawRoundRect(r, 10, 10, ink(5, k))
    for k in range(3):
        lf = poly([(0, -h + 40 * k), (120 - 240 * (k % 2), -h - 90 + 40 * k), (10, -h + 20 + 40 * k)])
        cv.drawPath(lf, fill(C("#5f9a3a"))); cv.drawPath(lf, ink(4, k))
    cv.restore()


def jar(cv, x, y, s, T):
    b = skia.Path(); b.addRoundRect(skia.Rect(x - 150 * s, y - 330 * s, x + 150 * s, y), 50 * s, 50 * s)
    cv.save(); cv.clipPath(b, doAntiAlias=True)
    cv.drawRect(skia.Rect(x - 160 * s, y - 330 * s, x + 160 * s, y), fill(C("#dfe8ee", 140)))
    mol_wave(cv, y - 240 * s, T, amp=8, k=0.03, drips=False)
    cv.restore()
    cv.drawPath(b, ink(8, int(T * 8) % 3))
    cv.drawRoundRect(skia.Rect(x - 120 * s, y - 380 * s, x + 120 * s, y - 330 * s), 12, 12, fill(C("#8a5a2a")))
    cv.drawRoundRect(skia.Rect(x - 120 * s, y - 380 * s, x + 120 * s, y - 330 * s), 12, 12, ink(6, 1))
    cv.drawRect(skia.Rect(x - 100 * s, y - 220 * s, x + 100 * s, y - 120 * s), fill(C("#f1e8d0")))
    cv.drawRect(skia.Rect(x - 100 * s, y - 220 * s, x + 100 * s, y - 120 * s), ink(5, 2))
    text_c(cv, "MELAÇO", x, y - 152 * s, int(52 * s), "#5a2a0a")


def text_c(cv, s, x, y, size, col="#1b1410", a=1.0, font=None):
    f = skia.Font(font or TF, size)
    cv.drawString(s, x - f.measureText(s) / 2, y, f, fill(C(col, 255 * a)))


def speed_lines(cv, T, n=18, col="#ffffff", a=120):
    for i in range(n):
        ph = (T * 2.2 + i / n) % 1
        y = 200 + (i * 97) % 1100
        x = W - ph * (W + 600)
        cv.drawLine(x, y, x + 260, y, stroke(C(col, a * (1 - ph)), 8))


def smell(cv, x, y, T, col="#c08a4a"):
    for k in range(3):
        p = skia.Path(); x0 = x + k * 70
        p.moveTo(x0, y)
        for j in range(1, 9):
            p.lineTo(x0 + 26 * math.sin(j * 0.9 + T * 3 + k), y - j * 40)
        cv.drawPath(p, stroke(C(col, 200), 12))


def measure(cv, x, y0, y1, lt, label, size=110, col="#ffd54a", lx=None):
    k = eout(clamp(lt / 0.8))
    yt = lerp(y0, y1, k)
    cv.drawLine(x, y0, x, yt, stroke(C("#14100c"), 18)); cv.drawLine(x, y0, x, yt, stroke(C(col), 10))
    cv.drawLine(x - 40, y0, x + 40, y0, stroke(C(col), 10))
    if k > 0.95:
        cv.drawLine(x - 40, y1, x + 40, y1, stroke(C(col), 10))
        f = skia.Font(TF, size); tx = lx if lx is not None else x - f.measureText(label) - 40
        cv.drawString(label, tx, (y0 + y1) / 2, f, stroke(C("#14100c"), 16)); cv.drawString(label, tx, (y0 + y1) / 2, f, fill(C(col)))


def stuck_toon(cv, x, y, s, T, level, **k):
    """character sunk in molasses up to `level` (screen y)."""
    toon(cv, x, y, s, T, shadow=False, **k)


# anchors in the plates (checked on stills)
TANK_H = (520, 900)    # tank centre in "harbor"
BURST_C = (540, 930)   # molasses dome in "burst"


# ---------- scenes ----------

def s01a(cv, lt, d, T):  # 1919, a wave killed 21 in Boston
    sky_winter(cv, T)
    plate(cv, "street", P(lt, d, 1.0, 1.05), cy=900)
    big_wave(cv, clamp(lt / d) * 0.9, T, base=1300, top=780)
    toon(cv, 540, 1650, 1.0, T, outfit="worker", expr="shock", pose="panic", seed=1)
    date_stamp(cv, "1919", lt - 0.05, y=330, size=170)


def s01b(cv, lt, d, T):  # ...not water
    sky_dusk(cv, T)
    plate(cv, "flood", P(lt, d, 1.0, 1.08), cy=900)
    mol_wave(cv, 1150, T, amp=26)
    stamp(cv, "NÃO ERA ÁGUA", lt - 0.2, 540, 420, 100, "#c0161c", -8)


def s02(cv, lt, d, T):  # Boston, Jan 15 1919
    sky_winter(cv, T)
    plate(cv, "harbor", P(lt, d, 1.0, 1.05), cy=900)
    banner(cv, "BOSTON, EUA", lt - 0.05, y=300, size=90, bg="#1b4a9a", fg="#ffffff")
    date_stamp(cv, "15 DE JANEIRO DE 1919", lt - 0.4, y=470, size=96)


def s03a(cv, lt, d, T):  # at the port, a huge tank
    sky_winter(cv, T)
    plate(cv, "harbor", P(lt, d, 1.05, 1.2), cx=TANK_H[0], cy=TANK_H[1])
    banner(cv, "O TANQUE", lt - 0.4, y=330, size=96, bg="#5a2a0a", fg="#ffd54a")


def s03b(cv, lt, d, T):  # 15 m tall, full of molasses
    sky_winter(cv, T)
    plate(cv, "tank_low", P(lt, d, 1.0, 1.05), cy=900)
    measure(cv, 980, 1250, 430, lt, "15 M", 120)
    if T > ws(3, "melaço"):
        banner(cv, "CHEIO DE MELAÇO", T - ws(3, "melaço"), y=300, size=80, bg="#3a1806", fg="#ffd54a")


def s04(cv, lt, d, T):  # molasses = thick dark syrup from sugarcane
    studio(cv, "#3a2412")
    jar(cv, 540, 1180, 1.6, T)
    if T > ws(4, "cana-de-açúcar") - 0.1:
        k = eout(clamp((T - ws(4, "cana-de-açúcar") + 0.1) / 0.4))
        cane(cv, lerp(-100, 150, k), 1250, 760, T, -8)
        cane(cv, lerp(1180, 930, k), 1250, 700, T, 8)
    banner(cv, "XAROPE GROSSO", lt - 0.3, y=330, size=88, bg="#3a1806", fg="#ffd54a")


def s05a(cv, lt, d, T):  # company turned it into alcohol
    sky_winter(cv, T)
    plate(cv, "harbor", 1.12, cx=TANK_H[0], cy=TANK_H[1], sigma=5)
    toon(cv, 300, 1650, 1.0, T, outfit="worker", expr="grin", pose="point", look=0.6, seed=2)
    if T > ws(5, "álcool"):
        banner(cv, "ÁLCOOL", T - ws(5, "álcool"), y=420, size=120, bg="#1b4a9a", fg="#ffffff")


def s05b(cv, lt, d, T):  # munitions for the war
    red_pulse(cv, T, "#5a1a10")
    for i in range(5):
        k = eout(clamp((lt - i * 0.12) / 0.35))
        shell(cv, 180 + i * 180, lerp(1500, 1180, k), 1.5, T)
    banner(cv, "MUNIÇÃO PRA GUERRA", lt - 0.2, y=380, size=80, bg="#3f5f2f", fg="#ffffff")
    banner(cv, "1ª GUERRA MUNDIAL", lt - 0.5, y=520, size=56, bg="#14100c", fg="#ffd54a")


def s06(cv, lt, d, T):  # the tank leaked from the start
    sky_winter(cv, T)
    plate(cv, "tank_low", P(lt, d, 1.05, 1.15), cy=1000)
    leak_drips(cv, [(330, 700, 160), (470, 880, 230), (640, 760, 140), (760, 960, 200)], T)
    stamp(cv, "VAZAVA", lt - 0.3, 540, 380, 130, "#c0161c", -10)


def s07(cv, lt, d, T):  # painted brown to hide the leaks
    sky_winter(cv, T)
    plate(cv, "tank_low", 1.1, cy=1000)
    k = clamp(lt / 1.6)
    for i in range(5):  # brush strokes
        kk = clamp(k * 5 - i)
        if kk > 0:
            y = 560 + i * 110
            cv.drawLine(150, y, lerp(150, 930, kk), y + 10 * math.sin(i), stroke(C("#4d2a10", 235), 95))
    toon(cv, 820, 1650, 0.95, T, outfit="painter", expr="smug", pose="wave", look=-0.6, seed=3)
    if T > ws(7, "marrom"):
        banner(cv, "PINTADO DE MARROM", T - ws(7, "marrom"), y=330, size=80, bg="#4d2a10", fg="#ffffff")


def s08(cv, lt, d, T):  # residents filled buckets
    sky_winter(cv, T)
    plate(cv, "tank_low", 1.12, cy=1000, sigma=4)
    drip_stream(cv, 330, 700, 1510, T)
    bucket(cv, 330, 1600, 1.3, T)
    toon(cv, 600, 1660, 0.85, T, outfit="kid", expr="joy", pose="reach", look=-0.8, seed=4)
    toon(cv, 860, 1650, 0.95, T, outfit="woman", expr="grin", pose="hips", look=-0.7, seed=5)
    bucket(cv, 980, 1640, 0.9, T)
    banner(cv, "BALDES DE MELAÇO", lt - 0.3, y=330, size=80, bg="#3a1806", fg="#ffd54a")


def s09(cv, lt, d, T):  # -17 to +5 in a few days
    sky_winter(cv, T)
    plate(cv, "harbor", 1.08, cy=900, sigma=6, alpha=0.9)
    t0 = ws(9, "subido")
    v = lerp(-17, 5, ease(clamp((T - t0) / 3.2)))
    thermo_big(cv, 760, 1180, v, T)
    banner(cv, "EM POUCOS DIAS", lt - 0.1, y=330, size=84, bg="#1b4a9a", fg="#ffffff")


def s10a(cv, lt, d, T):  # 12:30
    sky_winter(cv, T)
    plate(cv, "harbor", P(lt, d, 1.1, 1.18), cx=TANK_H[0], cy=TANK_H[1])
    hh = lerp(12.25, 12.5, eout(clamp(lt / 0.8)))
    clock(cv, 540, 560, 210, T, hh)
    banner(cv, "12H30", lt - 0.2, y=880, size=110, bg="#14100c", fg="#ffd54a")


def s10b(cv, lt, d, T):  # burst
    sky_winter(cv, T)
    dx, dy = shake(lt, 30, 4.0)
    plate(cv, "burst", P(lt, d, 1.0, 1.08), cx=BURST_C[0], cy=BURST_C[1], dx=dx, dy=dy)
    explosion(cv, BURST_C[0], BURST_C[1], clamp(lt / 0.8), 1.0)
    flash(cv, 0.9 * (1 - clamp(lt / 0.25)))
    pop_text(cv, "ESTOUROU!", lt, 0.1, 380, 150, "#ffd54a")


def s11a(cv, lt, d, T):  # 8+ million litres
    sky_winter(cv, T)
    plate(cv, "burst", P(lt, d, 1.08, 1.16), cx=BURST_C[0], cy=BURST_C[1])
    pop_text(cv, "+8 MILHÕES", lt, 0.1, 360, 130, "#ffd54a")
    pop_text(cv, "DE LITROS", lt, 0.3, 500, 100, "#ffffff")


def s11b(cv, lt, d, T):  # 8 m wave
    sky_winter(cv, T)
    plate(cv, "street", 1.05, cy=900)
    k = clamp(lt / 1.2)
    big_wave(cv, k, T, base=1250, top=560)
    toon(cv, 540, 1650, 0.9, T, outfit="woman", expr="shock", pose="panic", seed=6)
    if k > 0.7:
        measure(cv, 120, 1250, 560, lt - 0.85, "8 M", 120, lx=170)


def s11c(cv, lt, d, T):  # 56 km/h
    sky_winter(cv, T)
    dx, dy = shake(lt, 10, 1.0)
    plate(cv, "flood", 1.1, cy=900, dx=dx, dy=dy, sigma=2)
    speed_lines(cv, T, 22, "#e8c08a", 170)
    big_wave(cv, 1.0, T, base=1250, top=960)
    pop_text(cv, "56 KM/H", lt, ws(11, "56") - (T - lt), 430, 170, "#ffd54a")


def s12a(cv, lt, d, T):  # destroyed houses
    sky_winter(cv, T)
    dx, dy = shake(lt, 22, 3.0)
    plate(cv, "street", 1.08, cy=900, dx=dx, dy=dy, rot=2 * math.sin(lt * 6))
    big_wave(cv, 1.0, T, base=1250, top=900)
    for i in range(10):  # flying planks
        ph = clamp(lt / 1.2 - i * 0.05)
        x = 200 + i * 80 + ph * 300 * (1 if i % 2 else -1); y = 900 - 500 * math.sin(ph * math.pi)
        cv.save(); cv.translate(x, y); cv.rotate(ph * 400 + i * 30)
        cv.drawRect(skia.Rect(-60, -10, 60, 10), fill(C("#8a5a2a"))); cv.drawRect(skia.Rect(-60, -10, 60, 10), ink(4, i))
        cv.restore()
    banner(cv, "CASAS DESTRUÍDAS", lt - 0.1, y=330, size=84, bg="#8a1f1f", fg="#ffffff")


def s12b(cv, lt, d, T):  # bent elevated train track
    sky_winter(cv, T)
    plate(cv, "bent", P(lt, d, 1.0, 1.08), cy=900)
    mol_wave(cv, 1250, T, amp=14)
    banner(cv, "TRILHO DO TREM ELEVADO", lt - 0.1, y=300, size=66, bg="#2a2a30", fg="#ffd54a")


def s12c(cv, lt, d, T):  # dragged people and horses
    sky_winter(cv, T)
    plate(cv, "flood", 1.08, cy=900)
    k = clamp(lt / d)
    toon(cv, lerp(150, 700, k), 1500, 0.8, T, outfit="worker", expr="shock", pose="panic", seed=7, rot=-20 + 30 * math.sin(T * 3), shadow=False)
    mol_wave(cv, 1250, T, amp=30, speed=4)
    banner(cv, "PESSOAS E CAVALOS", lt - 0.2, y=330, size=80, bg="#3a1806", fg="#ffd54a")


def s13(cv, lt, d, T):  # twist
    red_pulse(cv, T)
    zoom(cv, lerp(1.0, 1.3, eout(lt / d)), 540, 820)
    toon(cv, 540, 1720, 1.55, T, outfit="worker", expr="shock", seed=8)


def s14(cv, lt, d, T):  # the worst was not the speed
    sky_winter(cv, T)
    plate(cv, "flood", 1.1, cy=900, sigma=4, alpha=0.8)
    pop_text(cv, "56 KM/H", lt, 0.0, 700, 170, "#ffffff")
    if lt > 0.6:
        k = eout(clamp((lt - 0.6) / 0.3))
        cv.drawLine(240, 760, lerp(240, 840, k), lerp(760, 560, k), stroke(C("#c0161c"), 30))
    banner(cv, "O PIOR NÃO FOI ISSO", lt - 0.2, y=330, size=78, bg="#8a1f1f", fg="#ffffff")


def s15a(cv, lt, d, T):  # at night the temperature fell
    sky_dusk(cv, T)
    plate(cv, "flood", P(lt, d, 1.0, 1.06), cy=900, cf=night_cf())
    v = lerp(5, -2, ease(clamp((lt - 0.4) / 2.0)))
    thermo_big(cv, 760, 1180, v, T, label=True, col="#2a7ac0")
    banner(cv, "À NOITE", lt - 0.1, y=300, size=96, bg="#0f2a4a", fg="#ffffff")


def s15b(cv, lt, d, T):  # molasses thickened like glue
    studio(cv, "#24120a")
    # thick strands stretching from a spoon
    k = clamp(lt / d)
    sy = lerp(700, 520, ease(k))
    cv.drawRoundRect(skia.Rect(380, sy - 60, 700, sy + 10), 30, 30, fill(C("#b8bec4")))
    cv.drawRoundRect(skia.Rect(380, sy - 60, 700, sy + 10), 30, 30, ink(7, 1))
    for i in range(4):
        x = 420 + i * 80
        w = 30 - 10 * k
        p = skia.Path(); p.moveTo(x - w, sy); p.quadTo(x + 10 * math.sin(T * 2 + i), (sy + 1150) / 2, x - 18, 1150)
        p.lineTo(x + 18, 1150); p.quadTo(x + 10 * math.sin(T * 2 + i), (sy + 1150) / 2, x + w, sy); p.close()
        cv.drawPath(p, fill(C(MOL_M))); cv.drawPath(p, ink(5, i))
    mol_wave(cv, 1150, T, amp=6, speed=0.4, drips=False)
    banner(cv, "FEITO COLA", lt - 0.2, y=330, size=110, bg="#3a1806", fg="#ffd54a")
    pop_text(cv, "4x MAIS GROSSO", lt, 0.8, 1300 - 60, 70, "#ffffff")


def s16a(cv, lt, d, T):  # those stuck couldn't get out
    sky_dusk(cv, T)
    plate(cv, "flood", 1.12, cy=900, cf=night_cf(0.7))
    stuck_toon(cv, 540, 1720, 1.0, T, 1490, outfit="woman", expr="worried", pose="panic", seed=9)
    mol_wave(cv, 1440, T, amp=12, k=0.01, speed=0.5, drips=False)
    banner(cv, "PRESOS", lt - 0.1, y=330, size=110, bg="#0f2a4a", fg="#ffffff")


def s16b(cv, lt, d, T):  # rescue became a nightmare
    sky_dusk(cv, T)
    plate(cv, "bent", 1.08, cy=900, cf=night_cf(0.7))
    search = poly([(900, 0), (300, 1500), (700, 1500)])
    cv.drawPath(search, fill(C("#fff6c8", 40)))
    stuck_toon(cv, 330, 1700, 0.9, T, 1480, outfit="rescuer", expr="determined", pose="reach", seed=10)
    stuck_toon(cv, 760, 1720, 0.9, T, 1500, outfit="worker", expr="worried", pose="panic", seed=11)
    mol_wave(cv, 1440, T, amp=12, k=0.01, speed=0.5, drips=False)
    banner(cv, "O RESGATE", lt - 0.1, y=330, size=100, bg="#2a3a5a", fg="#ffffff")


def s17(cv, lt, d, T):  # 21 dead, ~150 injured
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#0a0806")))
    plate(cv, "flood", 1.05, cy=900, cf=night_cf(1.0), alpha=0.5)
    pop_text(cv, "21 MORTOS", lt, ws(17, "21") - (T - lt), 520, 150, "#ffffff")
    pop_text(cv, "~150 FERIDOS", lt, ws(17, "150") - (T - lt), 720, 110, "#ffd54a")


def s18a(cv, lt, d, T):  # 2016 Harvard scientists
    studio(cv, "#1a2028")
    plate(cv, "lab", P(lt, d, 1.0, 1.05), cy=900)
    date_stamp(cv, "2016", lt - 0.05, y=300, size=160)
    toon(cv, 830, 1660, 0.95, T, outfit="sci", expr="grin", pose="point", look=-0.8, seed=12)
    if T > ws(18, "harvard"):
        banner(cv, "HARVARD", T - ws(18, "harvard"), y=470, size=90, bg="#8a1f1f", fg="#ffffff")


def s18b(cv, lt, d, T):  # the cold made it much thicker
    studio(cv, "#1a2028")
    plate(cv, "lab", 1.15, cy=1000, sigma=5)
    thermo_big(cv, 300, 1180, -2, T, label=False, col="#2a7ac0")
    toon(cv, 760, 1660, 0.95, T, outfit="sci2", expr="wide", pose="think", look=-0.6, seed=13)
    banner(cv, "FRIO = MAIS GROSSO", lt - 0.2, y=330, size=80, bg="#0f2a4a", fg="#ffd54a")


def s19(cv, lt, d, T):  # smelled of molasses for years
    sky_winter(cv, T)
    rays(cv, 760, 300, T, n=9, a=26, spread=120, base=110, col="#fff2c4")
    plate(cv, "street", P(lt, d, 1.0, 1.06), cy=900)
    smell(cv, 380, 1050, T); smell(cv, 720, 950, T)
    toon(cv, 540, 1650, 0.95, T, outfit="woman", expr="closed", pose="hips", seed=14)
    banner(cv, "CHEIRO DE MELAÇO", lt - 0.3, y=330, size=80, bg="#3a1806", fg="#ffd54a")
    banner(cv, "POR ANOS", lt - 0.6, y=470, size=70, bg="#14100c", fg="#ffffff")


def s20a(cv, lt, d, T):  # the wave that killed 21 in Boston...
    sky_winter(cv, T)
    plate(cv, "street", 1.05, cy=900)
    big_wave(cv, 0.4 + 0.6 * clamp(lt / d), T, base=1300, top=820)
    toon(cv, 540, 1650, 0.9, T, outfit="kid", expr="worried", pose="stand", look=0.3, seed=15)


def s20b(cv, lt, d, T):  # ...was made of something sweet
    sky_winter(cv, T)
    plate(cv, "burst", P(lt, d, 1.0, 1.08), cx=BURST_C[0], cy=BURST_C[1])
    sparkles(cv, T, BURST_C[0], BURST_C[1], 300, 160, 10, "#ffd54a")
    banner(cv, "ERA FEITA DE DOCE", lt - 0.1, y=330, size=84, bg="#3a1806", fg="#ffd54a")


SHOTS = []


def add(s, e, fn, *a):
    SHOTS.append((s, e, fn, a))


add(0, ws(1, "e") - 0.15, s01a)
add(ws(1, "e") - 0.15, L[2]["s"], s01b)
add(L[2]["s"], L[3]["s"], s02)
add(L[3]["s"], ws(3, "com"), s03a)
add(ws(3, "com"), L[4]["s"], s03b)
add(L[4]["s"], L[5]["s"], s04)
add(L[5]["s"], ws(5, "que"), s05a)
add(ws(5, "que"), L[6]["s"], s05b)
add(L[6]["s"], L[7]["s"], s06)
add(L[7]["s"], L[8]["s"], s07)
add(L[8]["s"], L[9]["s"], s08)
add(L[9]["s"], L[10]["s"], s09)
add(L[10]["s"], ws(10, "o"), s10a)
add(ws(10, "o"), L[11]["s"], s10b)
add(L[11]["s"], ws(11, "viraram"), s11a)
add(ws(11, "viraram"), ws(11, "a"), s11b)
add(ws(11, "a"), L[12]["s"], s11c)
add(L[12]["s"], ws(12, "entortou"), s12a)
add(ws(12, "entortou"), ws(12, "e", 0), s12b)
add(ws(12, "e", 0), L[13]["s"], s12c)
add(L[13]["s"], L[14]["s"], s13)
add(L[14]["s"], L[15]["s"], s14)
add(L[15]["s"], ws(15, "e"), s15a)
add(ws(15, "e"), L[16]["s"], s15b)
add(L[16]["s"], ws(16, "e"), s16a)
add(ws(16, "e"), L[17]["s"], s16b)
add(L[17]["s"], L[18]["s"], s17)
add(L[18]["s"], ws(18, "o"), s18a)
add(ws(18, "o"), L[19]["s"], s18b)
add(L[19]["s"], L[20]["s"], s19)
add(L[20]["s"], ws(20, "era"), s20a)
add(ws(20, "era"), DUR + 0.01, s20b)


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
