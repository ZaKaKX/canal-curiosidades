"""EP09 — O homem que sobreviveu às duas bombas atômicas (Tsutomu Yamaguchi, 1945). PT-BR.
3D inked plates (cidade de Hiroshima, rua, cidade destruída, estaleiro de Nagasaki, escritório de projetos,
trem, abrigo antiaéreo) + personagens 2D. usage: render.py timings.json a b out.mp4 kitdir platesdir"""
import sys, json, math, subprocess
import numpy as np
KW = {"1945", "bomba", "atômica", "três", "dias", "outra", "tsutomu", "yamaguchi", "engenheiro", "mitsubishi", "navios",
      "verão", "meses", "hiroshima", "6", "agosto", "último", "embora", "8", "15", "avião", "clarão", "3", "quilômetros",
      "queimaduras", "esquerdo", "tímpanos", "estouraram", "noite", "abrigo", "antiaéreo", "trem", "casa", "nagasaki",
      "reviravolta", "9", "enfaixado", "trabalho", "chefe", "única", "cidade", "inteira", "enlouquecido", "segunda",
      "novo", "sobreviveu", "2009", "único", "oficialmente", "japão", "duas", "bombas", "93", "anos", "armas", "nucleares",
      "sobrevive"}
OUT = {
    "yama":  dict(body="#c9c3b2", trim="#2a2a30", hat="none"),
    "boss":  dict(body="#2e3440", trim="#f2e6c8", hat="none"),
    "clerk": dict(body="#5a6a5a", trim="#f2e6c8", hat="none"),
    "old":   dict(body="#5a4a6a", trim="#f2e6c8", hat="none"),
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
for _l in TJ["lines"]:  # roteiro escrito foneticamente p/ a voz; na tela, grafia correta
    for _w in _l["words"]:
        _w["w"] = _w["w"].replace("Tsutômu", "Tsutomu").replace("Iamagútchi", "Yamaguchi")
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



def speed_lines(cv, T, n=18, col="#ffffff", a=120):
    for i in range(n):
        ph = (T * 2.2 + i / n) % 1
        y = 200 + (i * 97) % 1100
        x = W - ph * (W + 600)
        cv.drawLine(x, y, x + 260, y, stroke(C(col, a * (1 - ph)), 8))



def measure(cv, x, y0, y1, lt, label, size=110, col="#ffd54a", lx=None):
    k = eout(clamp(lt / 0.8))
    yt = lerp(y0, y1, k)
    cv.drawLine(x, y0, x, yt, stroke(C("#14100c"), 18)); cv.drawLine(x, y0, x, yt, stroke(C(col), 10))
    cv.drawLine(x - 40, y0, x + 40, y0, stroke(C(col), 10))
    if k > 0.95:
        cv.drawLine(x - 40, y1, x + 40, y1, stroke(C(col), 10))
        f = skia.Font(TF, size); tx = lx if lx is not None else x - f.measureText(label) - 40
        cv.drawString(label, tx, (y0 + y1) / 2, f, stroke(C("#14100c"), 16)); cv.drawString(label, tx, (y0 + y1) / 2, f, fill(C(col)))




# ---------- EP09 helpers ----------

def sky_dusk(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1100, [C("#141a33"), C("#4a3150"), C("#b0705a")], [0, 0.6, 1]))
    stars(cv, T, 0.5, ymax=H * 0.3)


def sky_ash(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1100, [C("#3a2c2a"), C("#8a5a44"), C("#d29a6a")], [0, 0.55, 1]))
    for i in range(30):  # falling ash
        x = (i * 137 + T * 20 * (1 + i % 3)) % W; y = (i * 251 + T * 60 * (1 + i % 2)) % H
        cv.drawCircle(x, y, 3 + i % 3, fill(C("#2a2220", 120)))


def mushroom(cv, x, by, k, s=1.0, T=0.0, a=1.0):
    """2D atomic cloud: stem + layered cap. k = growth 0..1 (no gore, just the cloud)."""
    if k <= 0: return
    k = eout(clamp(k))
    top = by - 760 * s * k
    hot = clamp(1 - k * 1.6)
    stem_w = 70 * s * (0.6 + 0.4 * k)
    p = skia.Path(); p.moveTo(x - stem_w * 1.8, by); p.quadTo(x - stem_w * 0.6, (by + top) / 2, x - stem_w, top + 60 * s)
    p.lineTo(x + stem_w, top + 60 * s); p.quadTo(x + stem_w * 0.6, (by + top) / 2, x + stem_w * 1.8, by); p.close()
    cv.drawPath(p, lin(x, top, x, by, [C("#b7a596", 240 * a), C("#e8c49a", 240 * a)])); cv.drawPath(p, ink(6, int(T * 8) % 3))
    # skirt ring
    rr = skia.Rect(x - 170 * s * k, top + 230 * s * k, x + 170 * s * k, top + 300 * s * k)
    cv.drawOval(rr, fill(C("#d8c8b8", 200 * a))); cv.drawOval(rr, ink(4, 1))
    cr = 250 * s * (0.35 + 0.65 * k)
    puffs = [(-0.9, 0.15, 0.55), (0.9, 0.15, 0.55), (-0.5, -0.25, 0.65), (0.5, -0.25, 0.65), (0, -0.35, 0.75), (0, 0.1, 0.7),
             (-0.45, 0.3, 0.5), (0.45, 0.3, 0.5)]
    for i, (px, py, pr) in enumerate(puffs):
        wob = 1 + 0.04 * math.sin(T * 3 + i)
        cx, cy, r = x + px * cr, top + py * cr, pr * cr * wob
        pp = skia.Path(); pp.addCircle(cx, cy, r)
        col0 = "#fff6d0" if hot > 0.3 else "#d9cbbd"; col1 = "#e89a4a" if hot > 0.1 else "#8a7a70"
        cv.drawPath(pp, rad(cx - r * 0.3, cy - r * 0.3, r * 1.4, [C(col0, 250 * a), C(col1, 250 * a)]))
    for i, (px, py, pr) in enumerate(puffs):
        cx, cy, r = x + px * cr, top + py * cr, pr * cr
        cv.drawArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), 180 + 20 * i, 140, False, ink(5, i))
    if hot > 0:
        glow(cv, x, top, cr * 2.2, "#fff2b0", 200 * hot * a, T)


def plane(cv, x, y, s, T):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    body = skia.Path(); body.addRoundRect(skia.Rect(-150, -14, 150, 14), 14, 14)
    sk(cv, body, "#c7ccd2", 5, 0)
    sk(cv, poly([(-30, -6), (40, -6), (-10, -170), (-40, -170)]), "#b4bac2", 5, 1)
    sk(cv, poly([(-30, 6), (40, 6), (-10, 150), (-40, 150)]), "#b4bac2", 5, 2)
    sk(cv, poly([(-150, 0), (-120, 0), (-150, -60), (-170, -60)]), "#b4bac2", 4, 0)
    cv.restore()


def bandage(cv, x, y, s, T, head=True, arm=True):
    """white bandages over a toon standing with feet at (x,y): forehead wrap + left arm/side (viewer's right)."""
    y = min(y, 1285 + 340 * s)
    hy = y - 505 * s
    if head:
        cv.save(); cv.translate(x, hy - 70 * s); cv.rotate(-8)
        r = skia.Rect(-168 * s, -26 * s, 168 * s, 26 * s)
        pp = skia.Path(); pp.addRoundRect(r, 18 * s, 18 * s)
        cv.save(); cv.clipPath(_headclip(0, 70 * s, s), doAntiAlias=True)
        cv.drawPath(pp, fill(C("#f7f4ec"))); cv.drawPath(pp, ink(5, 1))
        for k in range(5):
            cv.drawLine(-120 * s + k * 60 * s, -22 * s, -100 * s + k * 60 * s, 22 * s, stroke(C("#c9c2b0"), 3))
        cv.restore(); cv.restore()
        # gauze patch on viewer-right cheek
        pr = skia.Rect(x + 70 * s, hy + 20 * s, x + 135 * s, hy + 80 * s)
        cv.drawRect(pr, fill(C("#f7f4ec"))); cv.drawRect(pr, ink(4, 2))
    if arm:
        for k in range(3):
            yy = y - (330 - k * 45) * s
            rr = skia.Rect(x + 30 * s, yy, x + 95 * s, yy + 30 * s)
            cv.drawRoundRect(rr, 8, 8, fill(C("#f7f4ec"))); cv.drawRoundRect(rr, 8, 8, ink(4, k))


def _headclip(cx, cy, s):
    p = skia.Path(); R_ = 168 * s; p.addOval(skia.Rect(cx - R_, cy - R_, cx + R_, cy + R_ * 0.96)); return p


def ear_rings(cv, x, y, s, T, a=1.0):
    y = min(y, 1285 + 340 * s)
    hy = y - 505 * s
    for sx in (-1, 1):
        for k in range(3):
            ph = (T * 2 + k / 3) % 1
            r = 40 + ph * 120
            cv.drawArc(skia.Rect(x + sx * 175 * s - r, hy - r, x + sx * 175 * s + r, hy + r), (-45 if sx > 0 else 135), 90, False,
                       stroke(C("#ffd54a", 230 * (1 - ph) * a), 8))


def suitcase(cv, x, y, s):
    r = skia.Rect(x - 70 * s, y - 100 * s, x + 70 * s, y); pp = skia.Path(); pp.addRoundRect(r, 12, 12)
    sk(cv, pp, "#7a4a24", 6, 0)
    h = skia.Path(); h.addRoundRect(skia.Rect(x - 28 * s, y - 130 * s, x + 28 * s, y - 100 * s), 10, 10)
    cv.drawPath(h, ink(6, 1))
    cv.drawLine(x - 70 * s, y - 55 * s, x + 70 * s, y - 55 * s, stroke(C("#4a2a10"), 6))


def blueprint(cv, x, y, w, h, k, T):
    r = skia.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    cv.save(); cv.rotate(-3)
    cv.drawRect(r, fill(C("#1d4f8f"))); cv.drawRect(r, ink(7, 1))
    gp = stroke(C("#ffffff", 40), 2)
    for gx in range(int(r.left()), int(r.right()), 40): cv.drawLine(gx, r.top(), gx, r.bottom(), gp)
    for gy in range(int(r.top()), int(r.bottom()), 40): cv.drawLine(r.left(), gy, r.right(), gy, gp)
    # ship side profile, drawn progressively
    hull = skia.Path(); x0 = x - w * 0.42; x1 = x + w * 0.42; yd = y + h * 0.05; yk = y + h * 0.28
    hull.moveTo(x0, yd); hull.lineTo(x1, yd - 20); hull.lineTo(x1 - 60, yk); hull.lineTo(x0 + 40, yk); hull.close()
    hull.moveTo(x - w * 0.05, yd); hull.lineTo(x - w * 0.05, yd - 90); hull.lineTo(x + w * 0.18, yd - 90); hull.lineTo(x + w * 0.18, yd)
    hull.moveTo(x + w * 0.05, yd - 90); hull.lineTo(x + w * 0.05, yd - 160)
    meas = skia.PathMeasure(hull, False); seg = skia.Path(); tot = 0
    pm = skia.PathMeasure(hull, False)
    lens = []
    while True:
        lens.append(pm.getLength())
        if not pm.nextContour(): break
    total = sum(lens); want = total * clamp(k); acc = 0
    pm = skia.PathMeasure(hull, False)
    for L_ in lens:
        if want > acc:
            pm.getSegment(0, min(L_, want - acc), seg, True)
        acc += L_
        if not pm.nextContour(): break
    cv.drawPath(seg, stroke(C("#ffffff", 235), 6))
    cv.restore()


def certificate(cv, x, y, lt, T):
    k = eout(clamp(lt / 0.4))
    cv.save(); cv.translate(x, lerp(y + 300, y, k)); cv.rotate(-4)
    r = skia.Rect(-260, -330, 260, 330); pp = skia.Path(); pp.addRect(r)
    sk(cv, pp, "#f4ecd8", 7, 0)
    for i in range(9):
        yy = -220 + i * 52
        cv.drawLine(-200, yy, 200 - (i % 3) * 60, yy, stroke(C("#6a5a4a", 160), 7))
    for i in range(3):  # vertical "writing" columns
        cv.drawLine(150 - i * 50, -300, 150 - i * 50, -250, stroke(C("#2a2420"), 9))
    if lt > 0.6:
        a = eout(clamp((lt - 0.6) / 0.15))
        cv.save(); cv.translate(110, 200); cv.scale(lerp(1.8, 1, a), lerp(1.8, 1, a))
        cv.drawCircle(0, 0, 80, stroke(C("#c0161c", 230 * a), 12)); cv.drawCircle(0, 0, 55, stroke(C("#c0161c", 200 * a), 6))
        cv.restore()
    cv.restore()


def steam(cv, x, y, T, n=7, s=1.0):
    for i in range(n):
        ph = (T * 0.6 + i / n) % 1
        cv.drawCircle(x - ph * 260 * s + 30 * math.sin(i), y - ph * 360 * s, (30 + ph * 90) * s, fill(C("#f2efe8", 200 * (1 - ph))))


def bomb_icon(cv, x, y, s, lt, label=None):
    if lt <= 0: return
    a = eout(clamp(lt / 0.25))
    cv.save(); cv.translate(x, y); cv.scale(s * lerp(1.5, 1, a), s * lerp(1.5, 1, a))
    mushroom(cv, 0, 260, 1.0, 0.42, 3.0, a)
    cv.restore()


def big_flash(cv, lt, dur=0.5):
    if lt < dur:
        flash(cv, 1.0 - clamp(lt / dur) ** 0.6)


def warm_cf(k=1.0):
    return skia.ColorFilters.Matrix([1, 0, 0, 0, 0.06 * k, 0, 0.9, 0, 0, 0.02 * k, 0, 0, 0.75, 0, 0, 0, 0, 0, 1, 0])


# anchors (checked on stills)
CITY_C = (540, 1000)
YARD_C = (540, 1000)


# ---------- scenes ----------

def s01a(cv, lt, d, T):  # 1945, a man survived an atomic bomb
    sky_day(cv, T)
    plate(cv, "city", P(lt, d, 1.0, 1.05), cy=900)
    toon(cv, 540, 1660, 1.0, T, outfit="yama", expr="smile", pose="stand", seed=1)
    date_stamp(cv, "1945", lt - 0.05, y=330, size=170)


def s01b(cv, lt, d, T):  # ... the bomb
    sky_ash(cv, T)
    plate(cv, "ruins", P(lt, d, 1.0, 1.06), cy=900, alpha=0.95)
    mushroom(cv, 640, 980, lt / 1.4, 1.0, T)
    big_flash(cv, lt)


def s01c(cv, lt, d, T):  # three days later, another
    studio(cv, "#2a1c12")
    bomb_icon(cv, 300, 760, 1.0, lt)
    bomb_icon(cv, 780, 760, 1.0, lt - 0.9)
    pop_text(cv, "3 DIAS DEPOIS", lt, 0.3, 360, 110, "#ffd54a")
    toon(cv, 540, 1660, 0.85, T, outfit="yama", expr="shock", pose="panic", seed=2)


def s02(cv, lt, d, T):  # his name was Tsutomu Yamaguchi
    studio(cv, "#1c2433")
    rays(cv, 540, 700, T, n=10, a=20, spread=180, base=120, col="#fff2c4")
    toon(cv, 540, 1660, 1.25, T, outfit="yama", expr="grin", pose="wave", seed=3)
    banner(cv, "TSUTOMU YAMAGUCHI", lt - 0.1, y=330, size=86, bg="#14100c", fg="#ffd54a")


def s03a(cv, lt, d, T):  # engineer at Mitsubishi
    sky_day(cv, T)
    plate(cv, "yard", P(lt, d, 1.0, 1.06), cy=900)
    toon(cv, 300, 1660, 0.95, T, outfit="yama", expr="grin", pose="point", look=0.7, seed=4)
    banner(cv, "ENGENHEIRO", lt - 0.1, y=330, size=96, bg="#1b4a9a", fg="#ffffff")
    if T > ws(3, "mitsubishi") - 0.05:
        banner(cv, "MITSUBISHI", T - ws(3, "mitsubishi") + 0.05, y=470, size=80, bg="#c0161c", fg="#ffffff")


def s03b(cv, lt, d, T):  # designed ships
    plate(cv, "office", 1.12, cy=1000, sigma=5)
    blueprint(cv, 540, 820, 860, 560, lt / 1.3, T)
    toon(cv, 820, 1660, 0.9, T, outfit="yama", expr="determined", pose="think", look=-0.7, seed=5)
    banner(cv, "PROJETAVA NAVIOS", lt - 0.1, y=330, size=84, bg="#14100c", fg="#ffffff")


def s04a(cv, lt, d, T):  # that summer the company sent him...
    sky_day(cv, T)
    plate(cv, "train", P(lt, d, 1.0, 1.05), cy=900, cf=warm_cf(0.5))
    toon(cv, 760, 1660, 0.9, T, outfit="yama", expr="smile", pose="wave", seed=6)
    suitcase(cv, 560, 1660, 1.1)
    banner(cv, "VIAGEM A TRABALHO", lt - 0.2, y=330, size=82, bg="#1b4a9a", fg="#ffffff")


def s04b(cv, lt, d, T):  # three months in Hiroshima
    sky_day(cv, T)
    plate(cv, "city", P(lt, d, 1.05, 1.12), cx=CITY_C[0], cy=CITY_C[1])
    banner(cv, "HIROSHIMA, JAPÃO", lt - 0.05, y=300, size=90, bg="#14100c", fg="#ffffff")
    pop_text(cv, "3 MESES", lt, 0.0 if T > ws(4, "três") else 99, 470, 120, "#ffd54a")


def s05a(cv, lt, d, T):  # August 6 was the last day
    sky_day(cv, T)
    plate(cv, "street", P(lt, d, 1.0, 1.05), cy=900)
    date_stamp(cv, "6 DE AGOSTO DE 1945", lt - 0.05, y=330, size=100)
    if T > ws(5, "último"):
        banner(cv, "ÚLTIMO DIA", T - ws(5, "último"), y=480, size=90, bg="#c0161c", fg="#ffffff")


def s05b(cv, lt, d, T):  # he was already leaving
    sky_day(cv, T)
    plate(cv, "street", 1.08, cy=900)
    k = clamp(lt / d)
    x = lerp(380, 640, k)
    toon(cv, x, 1660, 0.95, T, outfit="yama", expr="smile", pose="stand", walk=T * 9, seed=7)
    suitcase(cv, x + 120, 1630, 0.9)
    banner(cv, "INDO EMBORA", lt - 0.1, y=330, size=96, bg="#1b4a9a", fg="#ffffff")


def s06a(cv, lt, d, T):  # 8:15 in the morning
    sky_day(cv, T)
    plate(cv, "street", 1.1, cy=900, sigma=6)
    hh = lerp(8.0, 8.25, eout(clamp(lt / 0.8)))
    clock(cv, 540, 640, 230, T, hh)
    banner(cv, "8H15", lt - 0.2, y=980, size=120, bg="#14100c", fg="#ffd54a")


def s06b(cv, lt, d, T):  # he saw a plane in the sky
    sky_day(cv, T)
    plate(cv, "street", P(lt, d, 1.0, 1.05), cy=900)
    plane(cv, lerp(1000, 300, clamp(lt / d)), 330, 0.9, T)
    toon(cv, 640, 1660, 1.0, T, outfit="yama", expr="wide", pose="point", look=-0.5, seed=8)
    banner(cv, "UM AVIÃO", lt - 0.2, y=560, size=90, bg="#14100c", fg="#ffffff")


def s06c(cv, lt, d, T):  # ... a flash
    sky_day(cv, T)
    plate(cv, "street", 1.05, cy=900)
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#ffffff", 255 * clamp(lt / 0.35))))
    if lt > 0.35:
        pop_text(cv, "CLARÃO", lt, 0.35, 900, 170, "#ffd54a")


def s07(cv, lt, d, T):  # the bomb exploded ~3 km from him
    sky_ash(cv, T)
    dx, dy = shake(lt, 18, 3.0)
    plate(cv, "city", 1.05, cy=900, dx=dx, dy=dy, cf=warm_cf(1.0))
    mushroom(cv, 700, 900, 0.3 + lt / 2.0, 1.1, T)
    big_flash(cv, lt, 0.4)
    if lt > 0.6:
        k = eout(clamp((lt - 0.6) / 0.6))
        cv.drawLine(180, 1150, lerp(180, 700, k), 1150, stroke(C("#14100c"), 18)); cv.drawLine(180, 1150, lerp(180, 700, k), 1150, stroke(C("#ffd54a"), 10))
    pop_text(cv, "~3 KM", lt, ws(7, "3") - (T - lt), 1080, 120, "#ffd54a")


def s08a(cv, lt, d, T):  # burns on the left side
    sky_ash(cv, T)
    plate(cv, "ruins", 1.1, cy=900, sigma=6)
    toon(cv, 540, 1660, 1.15, T, outfit="yama", expr="worried", pose="stand", seed=9)
    bandage(cv, 540, 1660, 1.15, T, head=lt > 0.5, arm=True)
    banner(cv, "QUEIMADURAS", lt - 0.1, y=330, size=96, bg="#8a1f1f", fg="#ffffff")


def s08b(cv, lt, d, T):  # eardrums burst
    sky_ash(cv, T)
    plate(cv, "ruins", 1.1, cy=900, sigma=6)
    toon(cv, 540, 1660, 1.15, T, outfit="yama", expr="shock", pose="stand", seed=9)
    bandage(cv, 540, 1660, 1.15, T)
    ear_rings(cv, 540, 1660, 1.15, T)
    banner(cv, "TÍMPANOS ESTOURADOS", lt - 0.1, y=330, size=78, bg="#8a1f1f", fg="#ffffff")


def s09(cv, lt, d, T):  # night in an air-raid shelter
    sky_dusk(cv, T)
    plate(cv, "shelter", P(lt, d, 1.0, 1.06), cy=900)
    toon(cv, 760, 1660, 0.85, T, outfit="yama", expr="sad", pose="stand", seed=10)
    bandage(cv, 760, 1660, 0.85, T)
    banner(cv, "ABRIGO ANTIAÉREO", lt - 0.1, y=330, size=86, bg="#2a2a30", fg="#ffd54a")


def s10a(cv, lt, d, T):  # next day, a train home
    sky_dusk(cv, T)
    dx = 6 * math.sin(T * 30)
    plate(cv, "train", P(lt, d, 1.0, 1.06), cy=900, dy=dx * 0.3)
    steam(cv, 640, 700, T, 8, 1.2)
    speed_lines(cv, T, 12, "#ffffff", 80)
    banner(cv, "DE VOLTA PRA CASA", lt - 0.1, y=330, size=84, bg="#1b4a9a", fg="#ffffff")


def s10b(cv, lt, d, T):  # ... in Nagasaki
    sky_day(cv, T)
    plate(cv, "yard", P(lt, d, 1.0, 1.06), cy=900)
    banner(cv, "NAGASAKI", lt - 0.05, y=330, size=130, bg="#14100c", fg="#ffd54a")


def s11(cv, lt, d, T):  # twist
    red_pulse(cv, T)
    zoom(cv, lerp(1.0, 1.3, eout(lt / d)), 540, 820)
    toon(cv, 540, 1720, 1.55, T, outfit="yama", expr="shock", seed=11)
    bandage(cv, 540, 1720 if 1720 <= 1285 + 340 * 1.55 else 1285 + 340 * 1.55, 1.55, T)


def s12a(cv, lt, d, T):  # August 9
    sky_day(cv, T)
    plate(cv, "yard", 1.08, cy=900)
    date_stamp(cv, "9 DE AGOSTO DE 1945", lt - 0.05, y=330, size=100)


def s12b(cv, lt, d, T):  # bandaged, back to work
    plate(cv, "office", P(lt, d, 1.0, 1.05), cy=900)
    toon(cv, 540, 1660, 1.0, T, outfit="yama", expr="determined", pose="stand", seed=12)
    bandage(cv, 540, 1660, 1.0, T)
    banner(cv, "DE VOLTA AO TRABALHO", lt - 0.2, y=330, size=76, bg="#1b4a9a", fg="#ffffff")


def s13a(cv, lt, d, T):  # told his boss
    plate(cv, "office", 1.08, cy=900)
    toon(cv, 330, 1660, 0.92, T, outfit="yama", expr="wide", pose="panic", look=0.7, seed=13)
    bandage(cv, 330, 1660, 0.92, T)
    toon(cv, 780, 1660, 0.92, T, outfit="boss", expr="smile", pose="hips", look=-0.7, seed=14)
    banner(cv, "O CHEFE", lt - 0.1, y=330, size=100, bg="#2e3440", fg="#ffffff")


def s13b(cv, lt, d, T):  # one single bomb destroyed a whole city
    sky_ash(cv, T)
    plate(cv, "ruins", P(lt, d, 1.0, 1.06), cy=900, alpha=0.9)
    mushroom(cv, 540, 1180, 1.0, 0.8, T + 5)
    pop_text(cv, "1 BOMBA", lt, 0.0, 340, 140, "#ffd54a")
    pop_text(cv, "1 CIDADE INTEIRA", lt, ws(13, "cidade") - (T - lt), 1170, 90, "#ffffff")


def s14(cv, lt, d, T):  # boss thought he'd gone mad
    plate(cv, "office", 1.12, cx=700, cy=900)
    toon(cv, 600, 1660, 1.15, T, outfit="boss", expr="smug", pose="think", look=-0.4, seed=14)
    for i in range(3):  # spiral "crazy" doodle
        a = T * 4 + i * 2.1
        cv.drawCircle(860 + 50 * math.cos(a), 640 + 50 * math.sin(a), 10, fill(C("#ffd54a")))
    stamp(cv, "LOUCURA!", lt - 0.4, 540, 380, 120, "#c0161c", -8)


def s15a(cv, lt, d, T):  # right at that moment...
    plate(cv, "office", P(lt, d, 1.0, 1.12), cx=300, cy=800)
    glow(cv, 300, 760, 500 * clamp(lt / d + 0.2), "#fff6c8", 230, T)
    toon(cv, 640, 1660, 1.0, T, outfit="yama", expr="wide", pose="stand", look=-0.8, seed=15)
    bandage(cv, 640, 1660, 1.0, T)


def s15b(cv, lt, d, T):  # ... another flash
    dx, dy = shake(lt, 26, 4.0)
    plate(cv, "office", 1.12, cx=300, cy=800, dx=dx, dy=dy)
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#ffffff", 255 * (1 - clamp((lt - 0.3) / 1.2)))))
    pop_text(cv, "OUTRO CLARÃO", lt, 0.25, 820, 130, "#c0161c")


def s16(cv, lt, d, T):  # second bomb, again ~3 km
    sky_ash(cv, T)
    plate(cv, "yard", 1.05, cy=900, cf=warm_cf(1.0))
    mushroom(cv, 640, 860, 0.3 + lt / 2.2, 1.05, T)
    pop_text(cv, "~3 KM", lt, ws(16, "3") - (T - lt), 1150, 120, "#ffd54a")
    pop_text(cv, "DE NOVO", lt, ws(16, "novo") - (T - lt), 380, 120, "#ffffff")


def s17(cv, lt, d, T):  # and he survived again
    sky_ash(cv, T)
    rays(cv, 540, 600, T, n=10, a=26, spread=180, base=120, col="#fff2c4")
    plate(cv, "ruins", 1.08, cy=900, alpha=0.7)
    toon(cv, 540, 1660, 1.15, T, outfit="yama", expr="determined", pose="stand", seed=16)
    bandage(cv, 540, 1660, 1.15, T)
    stamp(cv, "SOBREVIVEU 2x", lt - 0.3, 540, 380, 100, "#ffd54a", -6)


def s18a(cv, lt, d, T):  # 2009
    studio(cv, "#1c2433")
    date_stamp(cv, "2009", lt - 0.05, y=330, size=170)
    certificate(cv, 540, 860, lt, T)


def s18b(cv, lt, d, T):  # the only one officially recognized
    studio(cv, "#1c2433")
    certificate(cv, 320, 880, 1.0, T)
    toon(cv, 780, 1660, 0.95, T, outfit="old", expr="smile", pose="point", look=-0.8, seed=17)
    banner(cv, "O ÚNICO RECONHECIDO", lt - 0.1, y=300, size=78, bg="#c0161c", fg="#ffffff")
    banner(cv, "OFICIALMENTE PELO JAPÃO", lt - 0.4, y=430, size=62, bg="#14100c", fg="#ffd54a")


def s18c(cv, lt, d, T):  # survivor of both bombs
    studio(cv, "#2a1c12")
    bomb_icon(cv, 300, 760, 1.0, lt)
    bomb_icon(cv, 780, 760, 1.0, lt - 0.3)
    pop_text(cv, "AS DUAS BOMBAS", lt, 0.2, 360, 100, "#ffd54a")
    toon(cv, 540, 1660, 0.85, T, outfit="old", expr="grin", pose="stand", seed=18)


def s19a(cv, lt, d, T):  # lived to 93
    sky_sunset(cv, T)
    plate(cv, "city", 1.05, cy=900, cf=warm_cf(0.6))
    toon(cv, 540, 1660, 1.0, T, outfit="old", expr="smile", pose="wave", seed=19)
    pop_text(cv, "93 ANOS", lt, ws(19, "93") - (T - lt), 380, 150, "#ffd54a")


def s19b(cv, lt, d, T):  # fought against nuclear weapons
    sky_sunset(cv, T)
    plate(cv, "city", P(lt, d, 1.05, 1.1), cy=900, cf=warm_cf(0.6))
    toon(cv, 540, 1660, 1.0, T, outfit="old", expr="determined", pose="reach", seed=20)
    # protest sign held up
    cv.save(); cv.translate(540, 1660 - 770 * 1.0 - 120)
    sg = skia.Path(); sg.addRect(skia.Rect(-210, -120, 210, 120)); sk(cv, sg, "#f4ecd8", 7, 0)
    cv.drawCircle(0, 0, 80, stroke(C("#14100c"), 14)); cv.drawLine(0, -80, 0, 80, stroke(C("#14100c"), 14))
    cv.drawLine(0, 0, -57, 57, stroke(C("#14100c"), 14)); cv.drawLine(0, 0, 57, 57, stroke(C("#14100c"), 14))
    cv.restore()
    banner(cv, "CONTRA AS ARMAS NUCLEARES", lt - 0.2, y=300, size=66, bg="#1b4a9a", fg="#ffffff")


def s20a(cv, lt, d, T):  # that's how a man survives two atomic bombs...
    studio(cv, "#2a1c12")
    bomb_icon(cv, 300, 760, 1.0, lt)
    bomb_icon(cv, 780, 760, 1.0, lt - 0.6)
    toon(cv, 540, 1660, 0.95, T, outfit="yama", expr="determined", pose="hips", seed=21)
    bandage(cv, 540, 1660, 0.95, T)


def s20b(cv, lt, d, T):  # ... in three days
    studio(cv, "#2a1c12")
    for i, lab in enumerate(("6/8", "7/8", "8/8", "9/8")):
        k = eout(clamp((lt - i * 0.15) / 0.3))
        x = 180 + i * 240
        r = skia.Rect(x - 95, 640 - 110, x + 95, 640 + 110)
        cv.save(); cv.translate(0, lerp(80, 0, k))
        pp = skia.Path(); pp.addRect(r); sk(cv, pp, "#f4ecd8", 6, i)
        cv.drawRect(skia.Rect(r.left(), r.top(), r.right(), r.top() + 50), fill(C("#c0161c")))
        f = skia.Font(TF, 64); cv.drawString(lab, x - f.measureText(lab) / 2, 690, f, fill(C("#14100c", 255 * k)))
        cv.restore()
        if i in (0, 3) and k > 0.9:
            cv.drawCircle(x, 640, 120, stroke(C("#c0161c"), 12))
    toon(cv, 540, 1660, 0.95, T, outfit="yama", expr="shock", pose="panic", seed=22)
    bandage(cv, 540, 1660, 0.95, T)
    banner(cv, "EM 3 DIAS", lt - 0.1, y=330, size=110, bg="#14100c", fg="#ffd54a")


SHOTS = []


def add(s, e, fn, *a):
    SHOTS.append((s, e, fn, a))


add(0, ws(1, "bomba") - 0.1, s01a)
add(ws(1, "bomba") - 0.1, ws(1, "e") - 0.1, s01b)
add(ws(1, "e") - 0.1, L[2]["s"], s01c)
add(L[2]["s"], L[3]["s"], s02)
add(L[3]["s"], ws(3, "e"), s03a)
add(ws(3, "e"), L[4]["s"], s03b)
add(L[4]["s"], ws(4, "passar"), s04a)
add(ws(4, "passar"), L[5]["s"], s04b)
add(L[5]["s"], ws(5, "ele"), s05a)
add(ws(5, "ele"), L[6]["s"], s05b)
add(L[6]["s"], ws(6, "ele"), s06a)
add(ws(6, "ele"), ws(6, "e", 1), s06b)
add(ws(6, "e", 1), L[7]["s"], s06c)
add(L[7]["s"], L[8]["s"], s07)
add(L[8]["s"], ws(8, "e"), s08a)
add(ws(8, "e"), L[9]["s"], s08b)
add(L[9]["s"], L[10]["s"], s09)
add(L[10]["s"], ws(10, "em"), s10a)
add(ws(10, "em"), L[11]["s"], s10b)
add(L[11]["s"], L[12]["s"], s11)
add(L[12]["s"], ws(12, "todo"), s12a)
add(ws(12, "todo"), L[13]["s"], s12b)
add(L[13]["s"], ws(13, "que"), s13a)
add(ws(13, "que"), L[14]["s"], s13b)
add(L[14]["s"], L[15]["s"], s14)
add(L[15]["s"], ws(15, "outro"), s15a)
add(ws(15, "outro"), L[16]["s"], s15b)
add(L[16]["s"], L[17]["s"], s16)
add(L[17]["s"], L[18]["s"], s17)
add(L[18]["s"], ws(18, "o"), s18a)
add(ws(18, "o"), ws(18, "como"), s18b)
add(ws(18, "como"), L[19]["s"], s18c)
add(L[19]["s"], ws(19, "e"), s19a)
add(ws(19, "e"), L[20]["s"], s19b)
add(L[20]["s"], ws(20, "em"), s20a)
add(ws(20, "em"), DUR + 0.01, s20b)


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
