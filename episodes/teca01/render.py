"""TECA 01 — Perdido na Colômbia (Parte 1 e 2).
uso: render.py <timings_pN.json> <frame_a> <frame_b> <out.mp4> <kitdir> <platesdir>
(mouth_pN.json na mesma pasta do timings)"""
import sys, json, math, subprocess, os
sys.path.insert(0, sys.argv[5])
from gfx import *
import gfx
from teca import teca
from cast import pessoa, mochila
from joca import _tt

TJ = json.load(open(sys.argv[1]))
PART = 2 if "p2" in os.path.basename(sys.argv[1]) else 1
MOUTH = json.load(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), f"mouth_p{PART}.json")))
PL = sys.argv[6]
L = {l["i"]: l for l in TJ["lines"]}
DUR = TJ["duration"]
END = DUR + 1.3
gfx.KEYWORDS |= ({"atlético", "colômbia", "spoiler", "pasto", "vulcão", "van", "fraco", "sozinho", "caminhonete", "preta", "portunhol",
                  "tito", "cinco", "mal-encarados", "séria", "parte", "2", "perfil", "sinal", "mapa", "brasileiro", "buenas", "hermano"}
                 if PART == 1 else
                 {"tito", "mochila", "pesada", "polícia", "atleta", "corri", "raiz", "rio", "viatura", "brasil", "neymar", "turista",
                  "meses", "caminhão", "todo", "mundo", "delegacia", "café", "colombiano", "herói", "acidente…", "acidente", "currículo", "colômbia"})
CHUNKS = build_chunks(TJ)
CAP_Y = 1370
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear)


def ws(i, word, nth=0):
    hits = [w for w in L[i]["words"] if w["w"].strip(".,!?:…'\"").lower().startswith(word.lower())]
    return hits[nth]["s"]


def MO(T, k=1.0):
    i = int(T * FPS)
    return MOUTH[i] * k if 0 <= i < len(MOUTH) else 0.0


# ------------------------------------------------------------ plates / sky (cache)
_IMG, _BL = {}, {}


def img(name):
    if name not in _IMG:
        f = f"{PL}/{name}_ink.png"
        if not os.path.exists(f): f = f"{PL}/../prev/{name}.png"
        _IMG[name] = skia.Image.open(f)
    return _IMG[name]


def blurred(name, sig):
    k = (name, round(sig, 1))
    if k not in _BL:
        s = skia.Surface(W, H); c = s.getCanvas(); c.clear(C("#000000", 0))
        p = skia.Paint(AntiAlias=True)
        if sig > 0.3: p.setImageFilter(skia.ImageFilters.Blur(sig, sig))
        c.drawImageRect(img(name), skia.Rect(0, 0, W, H), SAMP, p)
        _BL[k] = s.makeImageSnapshot()
    return _BL[k]


def plate(cv, name, sig=2.5, z=1.0, dx=0, dy=0, cx=W / 2, cy=H / 2, alpha=1.0, tint=None):
    im = blurred(name, sig)
    cv.save(); cv.translate(cx + dx, cy + dy); cv.scale(z, z); cv.translate(-cx, -cy)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(alpha)
    if tint: p.setColorFilter(skia.ColorFilters.Blend(C(*tint), skia.BlendMode.kMultiply))
    cv.drawImage(im, 0, 0, SAMP, p)
    cv.restore()


_SKY = {}


def sky_img(kind):
    if kind in _SKY: return _SKY[kind]
    s = skia.Surface(W, H); c = s.getCanvas()
    if kind == "gold":
        c.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1250, [C("#2f4a7a"), C("#7d86a8"), C("#f0a56a"), C("#ffd9a0")], [0, 0.4, 0.8, 1]))
        sx, sy = 260, 1050
    else:  # dusk
        c.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1250, [C("#1d2448"), C("#5b4a7a"), C("#e0805a"), C("#ffc488")], [0, 0.45, 0.82, 1]))
        sx, sy = 820, 1120
    c.drawCircle(sx, sy, 900, rad(sx, sy, 900, [C("#ffe2a8", 200), C("#ffb46a", 60), C("#ffb46a", 0)], [0, 0.4, 1]))
    p = skia.Paint(AntiAlias=True); p.setImageFilter(skia.ImageFilters.Blur(30, 30)); c.saveLayer(None, p)
    for (x, y, w_, h_) in ((180, 380, 520, 90), (760, 260, 600, 110), (520, 620, 700, 80), (950, 700, 400, 70)):
        c.drawOval(skia.Rect(x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2), fill(C("#ffd7b8", 120)))
    c.restore()
    _SKY[kind] = s.makeImageSnapshot()
    return _SKY[kind]


def sky(cv, kind="gold"):
    cv.drawImage(sky_img(kind), 0, 0)


# ------------------------------------------------------------ atmosphere
import random as _r
_RB = _r.Random(11)
BOKEH = [(_RB.random() * W, _RB.random() * H, _RB.uniform(30, 120), _RB.random() * 6, _RB.uniform(0.3, 1)) for _ in range(40)]
DUST = [(_RB.random() * W, _RB.random() * H, _RB.uniform(1.5, 4.5), _RB.random() * 6, _RB.uniform(0.2, 1)) for _ in range(140)]


def bokeh(cv, T, n=14, col="#ffd9a0", a=48, ymin=0, ymax=H, seed=0):
    p = skia.Paint(AntiAlias=True); p.setBlendMode(skia.BlendMode.kPlus)
    for i in range(n):
        x, y, r, ph, sp = BOKEH[(i + seed * 7) % len(BOKEH)]
        x = (x + T * 12 * sp) % (W + 240) - 120; y = ymin + (y % max(1, ymax - ymin)) + 14 * math.sin(T * 0.6 + ph)
        aa = a * (0.6 + 0.4 * math.sin(T * 1.3 + ph))
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), r, [C(col, aa * 0.55), C(col, aa * 0.75), C(col, aa), C(col, 0)], [0, 0.75, 0.9, 1]))
        cv.drawCircle(x, y, r, p)


def dust(cv, T, n=90, col="#fff0c8", a=170, wind=18):
    p = skia.Paint(AntiAlias=True); p.setBlendMode(skia.BlendMode.kPlus)
    for i in range(n):
        x, y, r, ph, sp = DUST[i % len(DUST)]
        x = (x + T * wind * sp + 30 * math.sin(T * 0.4 * sp + ph)) % W
        y = (y - T * 10 * sp + 20 * math.cos(T * 0.5 + ph)) % H
        aa = a * max(0, math.sin(T * 1.7 * sp + ph)) ** 2
        p.setColor(C(col, aa)); cv.drawCircle(x, y, r, p)


def light_leak(cv, x=120, y=200, r=1100, col="#ffb070", a=70):
    p = skia.Paint(AntiAlias=True); p.setBlendMode(skia.BlendMode.kPlus)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), r, [C(col, a), C(col, 0)])); cv.drawRect(skia.Rect(0, 0, W, H), p)


def haze(cv, y=1050, col="#ffd2a0", a=70):
    cv.drawRect(skia.Rect(0, y - 400, W, y + 300), lin(0, y - 400, 0, y + 300, [C(col, 0), C(col, a), C(col, 0)]))


def grade(cv, warm=True):
    p = skia.Paint(); p.setBlendMode(skia.BlendMode.kSoftLight)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                               [C("#ffb46a", 110), C("#ff9a5a", 40), C("#2a3a6a", 120)] if warm else [C("#6a8cff", 90), C("#2a3a6a", 120), C("#0a1020", 150)]))
    cv.drawRect(skia.Rect(0, 0, W, H), p)


def cam(cv, lt, d, z0=1.0, z1=1.06, fx=540, fy=1280, hand=1.0):
    z = lerp(z0, z1, ease(min(1, lt / max(d, 0.01))))
    cv.translate(hand * 5 * math.sin(lt * 0.9), hand * 4 * math.sin(lt * 1.3 + 1))
    cv.translate(fx, fy); cv.scale(z, z); cv.translate(-fx, -fy)


def pop(lt, d=0.18):
    return eout(min(1, max(0, lt / d)))


def stamp(cv, text, lt, x=540, y=520, size=150, col="#e8463a", rot=-8, fg="#ffffff"):
    if lt < 0: return
    a = pop(lt, 0.15); sc = lerp(1.6, 1.0, a)
    f = skia.Font(TF, size); w = f.measureText(text)
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(sc, sc)
    r = skia.Rect(-w / 2 - 40, -size * 0.92, w / 2 + 40, size * 0.32)
    cv.drawRoundRect(r.makeOffset(10, 12), 20, 20, fill(C("#000000", 110 * a)))
    cv.drawRoundRect(r, 20, 20, fill(C(col, 255 * a))); cv.drawRoundRect(r, 20, 20, stroke(C("#1b1410", 255 * a), 10))
    cv.drawString(text, -w / 2, 0, f, fill(C(fg, 255 * a)))
    cv.restore()


def bigword(cv, text, lt, y=560, size=200, col="#ffd54a"):
    if lt < 0: return
    a = pop(lt, 0.12); sc = lerp(1.5, 1.0, a) * (1 + 0.03 * math.sin(lt * 20) * math.exp(-lt * 3))
    f = skia.Font(TF, size); w = f.measureText(text)
    if w > 980: f = skia.Font(TF, size * 980 / w); w = f.measureText(text)
    cv.save(); cv.translate(540, y); cv.scale(sc, sc)
    cv.drawString(text, -w / 2 + 8, 12, f, fill(C("#000000", 120 * a)))
    cv.drawString(text, -w / 2, 0, f, stroke(C("#120c08", 255 * a), 24)); cv.drawString(text, -w / 2, 0, f, fill(C(col, 255 * a)))
    cv.restore()


def bubble(cv, text, x, y, lt, size=70, tail=(-60, 90)):
    if lt < 0: return
    a = pop(lt, 0.15); f = skia.Font(TF, size); w = f.measureText(text)
    cv.save(); cv.translate(x, y); cv.scale(lerp(0.5, 1, a), lerp(0.5, 1, a))
    r = skia.Rect(-w / 2 - 34, -size * 0.95, w / 2 + 34, size * 0.45)
    b = skia.Path(); b.addRoundRect(r, 40, 40)
    t_ = skia.Path(); t_.moveTo(-20, r.bottom() - 4); t_.lineTo(tail[0], r.bottom() + tail[1]); t_.lineTo(30, r.bottom() - 4); t_.close()
    b = skia.Op(b, t_, skia.PathOp.kUnion_PathOp) or b
    cv.drawPath(b, fill(C("#ffffff", 255 * a))); cv.drawPath(b, stroke(C("#1b1410", 255 * a), 7))
    cv.drawString(text, -w / 2, 0, f, fill(C("#1b1410", 255 * a)))
    cv.restore()


def sparkle(cv, x, y, lt, s=1.0, col="#fff3b0"):
    if lt < 0 or lt > 0.8: return
    a = math.sin(min(1, lt / 0.8) * math.pi); r = 60 * s * a
    p = skia.Paint(AntiAlias=True); p.setBlendMode(skia.BlendMode.kPlus); p.setColor(C(col, 255 * a))
    st = skia.Path(); st.moveTo(x, y - r); st.quadTo(x, y, x + r * 0.3, y); st.quadTo(x, y, x, y + r); st.quadTo(x, y, x - r * 0.3, y); st.quadTo(x, y, x, y - r)
    st2 = skia.Path(); st2.moveTo(x - r, y); st2.quadTo(x, y, x, y + r * 0.3); st2.quadTo(x, y, x + r, y); st2.quadTo(x, y, x, y - r * 0.3); st2.quadTo(x, y, x - r, y)
    cv.drawPath(st, p); cv.drawPath(st2, p)


def cup(cv, x, y, s, T):
    cp = skia.Path(); cp.addRoundRect(skia.Rect(x - 30 * s, y - 60 * s, x + 30 * s, y + 8 * s), 8 * s, 8 * s)
    _tt(cv, cp, "#f4f1ea", "#cfc9bd", lw=3.5 * s, off=(6 * s, 6 * s))
    cv.drawRect(skia.Rect(x - 30 * s, y - 40 * s, x + 30 * s, y - 24 * s), fill(C("#c8462f")))
    for k in range(3):
        st = skia.Path(); xx = x - 14 * s + k * 14 * s; st.moveTo(xx, y - 66 * s)
        st.cubicTo(xx - 14 * s, y - (90 + 8 * math.sin(T * 3 + k)) * s, xx + 14 * s, y - 110 * s, xx, y - 140 * s)
        cv.drawPath(st, stroke(C("#ffffff", 130), 5 * s))


def drips(cv, x, y, s, T):
    for i in range(10):
        ph = (T * 1.4 + i * 0.37) % 1.0
        dx = (i * 53 % 300 - 150) * s; dy = (-760 + (i * 97 % 600)) * s + ph * 260 * s
        cv.drawOval(skia.Rect(x + dx - 7 * s, y + dy - 12 * s, x + dx + 7 * s, y + dy + 12 * s), fill(C("#9fd8ff", 220 * (1 - ph))))


def van(cv, x, y, s):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    b = skia.Path(); b.addRoundRect(skia.Rect(-420, -420, 420, -70), 70, 70); _tt(cv, b, "#ece6da", "#c6bca9", lw=6, off=(40, 30))
    cv.drawRect(skia.Rect(-420, -190, 420, -160), fill(C("#3f7d8a")))
    for wx in (-300, -120, 60):
        w_ = skia.Path(); w_.addRoundRect(skia.Rect(wx, -380, wx + 150, -240), 18, 18); _tt(cv, w_, "#3a4a5a", "#22303c", lw=5, off=(10, 8))
        cv.drawLine(wx + 20, -360, wx + 60, -260, stroke(C("#ffffff", 70), 10))
    ws_ = skia.Path(); ws_.moveTo(250, -380); ws_.lineTo(380, -380); ws_.quadTo(410, -320, 405, -240); ws_.lineTo(250, -240); ws_.close(); _tt(cv, ws_, "#3a4a5a", "#22303c", lw=5, off=(10, 8))
    for wx in (-260, 260):
        cv.drawCircle(wx, -70, 78, fill(C("#1a1a1c"))); cv.drawCircle(wx, -70, 78, stroke(C("#2b1a12"), 6)); cv.drawCircle(wx, -70, 34, fill(C("#9a9a9e")))
    f = skia.Font(TF, 46); cv.drawString("TOUR", -110, -110, f, fill(C("#3f7d8a")))
    cv.restore()


def police_glow(cv, T, x=540, y=900, r=900, a=110):
    on = int(T * 5) % 2
    p = skia.Paint(AntiAlias=True); p.setBlendMode(skia.BlendMode.kPlus)
    for k, col in ((0, "#ff2a2a"), (1, "#2a5cff")):
        aa = a if on == k else a * 0.15
        cx = x + (-180 if k == 0 else 180)
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, y), r, [C(col, aa), C(col, 0)])); cv.drawRect(skia.Rect(0, 0, W, H), p)


def speed_lines(cv, T, a=120):
    for i in range(26):
        y = (i * 137) % H; x = (W - (T * 3200 + i * 271) % (W + 900))
        cv.drawLine(x, y, x + 420, y, stroke(C("#ffffff", a), 4 + (i % 3) * 2))


def splash(cv, x, y, lt, s=1.0):
    if lt < 0 or lt > 1.2: return
    k = eout(min(1, lt / 0.5)); fade = 1 - max(0, (lt - 0.4) / 0.8)
    for i in range(16):
        ang = math.radians(200 + i * 140 / 15); r = 340 * s * k
        px = x + math.cos(ang) * r; py = y + math.sin(ang) * r * 1.2 + 900 * s * lt * lt
        cv.drawCircle(px, py, (26 - i % 4 * 4) * s, fill(C("#cfeeff", 230 * fade)))
    cv.drawOval(skia.Rect(x - 380 * s * k, y - 50 * s, x + 380 * s * k, y + 50 * s), stroke(C("#ffffff", 200 * fade), 10 * s))


def circle_mark(cv, x, y, r, lt, col="#e8463a"):
    if lt < 0: return
    k = eout(min(1, lt / 0.45))
    p = stroke(C(col), 14); rr = skia.Rect(x - r, y - r * 0.75, x + r, y + r * 0.75)
    cv.drawArc(rr, -90, 370 * k, False, p)


def endcard(cv, T, lt, d):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#14182c"), C("#2a1f3a")]))
    bokeh(cv, T, 20, "#ffd9a0", 60)
    teca(cv, 540, 1950 + 180 * (1 - pop(lt - 0.25, 0.35)), 1.25, T, expr="shock", pose="panic", mouth_open=0, shadow=False)
    bigword(cv, "PARTE 2", lt, y=520, size=220, col="#ffd54a")
    bigword(cv, "NO PERFIL", lt - 0.2, y=760, size=150, col="#ffffff")
    if lt > 0.6:
        a = (math.sin(lt * 6) * 0.5 + 0.5)
        f = skia.Font(TF, 120); cv.drawString("👉", 0, 0, f, fill(C("#ffffff", 0)))
        cv.drawPath((lambda p: (p.moveTo(540, 900 + 20 * a), p.lineTo(500, 850 + 20 * a), p.lineTo(580, 850 + 20 * a), p.close(), p)[4])(skia.Path()), fill(C("#ffd54a")))


# ------------------------------------------------------------ shot helpers
def TECA(cv, T, x, y, s, expr="neutral", pose="pockets", talk=True, k=1.0, free=False, **kw):
    if not free: y = min(y, 1262 + 570 * s)
    teca(cv, x, y, s, T, expr=expr, pose=pose, mouth_open=MO(T, k) if talk else 0.0, **kw)


def P_(cv, T, look, x, y, s, expr="neutral", pose="stand", talk=False, k=1.0, sig=0, **kw):
    from cast import LOOKS
    y = min(y, 1260 + 565 * s * LOOKS[look].get("tall", 1.0))
    if sig > 0.3:
        with blur(cv, sig): pessoa(cv, x, y, s, T, look=look, expr=expr, pose=pose, mouth_open=MO(T, k) if talk else 0, **kw)
    else:
        pessoa(cv, x, y, s, T, look=look, expr=expr, pose=pose, mouth_open=MO(T, k) if talk else 0, **kw)


def outdoor(cv, T, name, kind="gold", sig=2.5, z=1.0, dx=0, dy=0):
    sky(cv, kind); plate(cv, name, sig, z, dx, dy); haze(cv, 1080, "#ffd2a0", 60)


def post(cv, T, bok=10, dst=60, leak=True, warm=True):
    if bok: bokeh(cv, T, bok)
    if dst: dust(cv, T, dst)
    if leak: light_leak(cv)
    grade(cv, warm)


# ============================================================ PARTE 1
def p1_flex(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.08)
    plate(cv, "quadra", 3.5)
    rays(cv, 900, 300, T, col="#ffd9a0", n=6, a=26, spread=40, base=125)
    P_(cv, T, "rafa", 210, 1640, 0.62, "laugh", "laugh", sig=3.5)
    P_(cv, T, "duda", 880, 1650, 0.6, "laugh", "laugh", sig=3.5, flip=True)
    TECA(cv, T, 540, 1830, 1.0, "smug", "flex")
    sparkle(cv, 300, 980, T - ws(1, "atlético")); sparkle(cv, 790, 960, T - ws(1, "atlético") - 0.15, 0.8)
    cv.restore(); post(cv, T, 12, 70)


def p1_map(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.1, 1.0)
    sky(cv, "gold"); plate(cv, "trilha", 9, 1.1); cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#0b1020", 120)))
    p0, p1, pc = (200, 1550), (800, 520), (180, 700)
    k = ease(min(1, lt / max(0.1, d - 0.4)))
    path = skia.Path(); path.moveTo(*p0); path.quadTo(pc[0], pc[1], p1[0], p1[1])
    pe = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10, Color=C("#ffffff", 220))
    pe.setPathEffect(skia.DashPathEffect.Make([30, 22], -lt * 60))
    meas = skia.PathMeasure(path, False); seg = skia.Path(); meas.getSegment(0, meas.getLength() * k, seg, True)
    cv.drawPath(seg, pe)
    pos, tan = meas.getPosTan(meas.getLength() * k)
    cv.save(); cv.translate(pos.x(), pos.y()); cv.rotate(math.degrees(math.atan2(tan.y(), tan.x())))
    pl = skia.Path(); pl.moveTo(60, 0); pl.lineTo(-40, -14); pl.lineTo(-50, 0); pl.lineTo(-40, 14); pl.close()
    w1 = skia.Path(); w1.moveTo(5, 0); w1.lineTo(-25, -55); w1.lineTo(-38, -55); w1.lineTo(-18, 0); w1.lineTo(-38, 55); w1.lineTo(-25, 55); w1.close()
    cv.scale(1.6, 1.6); cv.drawPath(w1, fill(C("#ffffff"))); cv.drawPath(pl, fill(C("#ffffff"))); cv.drawPath(pl, stroke(C("#1b1410"), 3)); cv.drawPath(w1, stroke(C("#1b1410"), 3))
    cv.restore()
    banner(cv, "BRASIL", lt, y=1680, size=70, bg="#2e9a4a", fg="#ffe14a")
    banner(cv, "SUL DA COLÔMBIA", lt - 1.0, y=430, size=78, bg="#ffd54a", fg="#1b2a6a")
    if lt > 1.0:
        a = pop(lt - 1.0); cv.drawCircle(p1[0], p1[1], 26 * a, fill(C("#e8463a"))); cv.drawCircle(p1[0], p1[1], 26 * a, stroke(C("#ffffff"), 6))
    cv.restore(); post(cv, T, 8, 40)


def p1_eu_primeiro(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    plate(cv, "quadra", 4)
    P_(cv, T, "biel", 190, 1680, 0.66, "neutral", "cross", sig=3)
    P_(cv, T, "duda", 900, 1680, 0.64, "skeptic", "hips", sig=3, flip=True)
    TECA(cv, T, 560, 1830, 1.0, "happy", "wave")
    cv.restore(); post(cv, T, 12, 60)


def p1_guio(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.02, 1.1)
    outdoor(cv, T, "trilha", sig=4)
    P_(cv, T, "rafa", 160, 1640, 0.62, "skeptic", "cross", sig=4)
    P_(cv, T, "biel", 930, 1650, 0.66, "skeptic", "hips", sig=4, flip=True)
    TECA(cv, T, 470, 2060, 1.35, "determined", "point")
    cv.restore(); post(cv, T, 14, 80)


def p1_spoiler(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.05)
    plate(cv, "mato", 3, tint=("#8f9fb8",))
    TECA(cv, T, 540, 1820, 0.95, "tired", "stand", talk=False, lean=6)
    for i in range(3):  # moscas de desânimo
        a = T * 3 + i * 2.1; cv.drawCircle(540 + 120 * math.cos(a), 760 + 40 * math.sin(a * 1.7), 6, fill(C("#1b1410")))
    cv.restore()
    p = skia.Paint(); p.setColorFilter(skia.ColorFilters.Matrix([0.33, 0.33, 0.33, 0, 0] * 3 + [0, 0, 0, 1, 0]))
    post(cv, T, 0, 40, leak=False, warm=False)
    stamp(cv, "SPOILER", lt - 0.05, y=560, size=150, rot=-9)


def p1_dia1(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.12, 1.04, fy=900)
    outdoor(cv, T, "pasto", sig=1.5)
    cv.restore(); post(cv, T, 8, 50)
    date_stamp(cv, "DIA 1", lt, y=520, size=200)


def p1_pasto(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.07)
    outdoor(cv, T, "pasto", sig=2.5)
    wk = T * 7
    for i, (lk, x) in enumerate((("rafa", 150), ("duda", 330), ("biel", 760), (None, 560))):
        xx = x + lt * 30
        if lk: P_(cv, T, lk, xx, 1760 - (i % 2) * 20, 0.62, "happy", "stand", walk=wk + i, seed=i)
        else: TECA(cv, T, xx, 1800, 0.72, "happy", "pockets", talk=False, walk=wk + 1.5)
    for (x, y) in ((260, 920), (420, 900), (650, 905), (880, 930)):  # bafo de frio
        k = ((T * 0.8 + x * 0.01) % 1.0)
        cv.drawCircle(x + 60 * k, y - 50 * k, 14 + 30 * k, fill(C("#ffffff", 90 * (1 - k))))
    cv.restore(); post(cv, T, 10, 70)
    banner(cv, "PASTO, COLÔMBIA", lt, y=420, size=80, bg="#ffd54a", fg="#1b2a6a")


def p1_cafe(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    outdoor(cv, T, "pasto", sig=7, z=1.3, dy=-120)
    TECA(cv, T, 540, 2100, 1.45, "happy", "think", talk=False)
    cup(cv, 540 + 75 * 1.45, 2100 - 600 * 1.45, 2.0, T)
    cv.restore(); post(cv, T, 18, 80)


def p1_vulcao(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.5, fx=300, fy=760, hand=0.5)
    outdoor(cv, T, "pasto", sig=1.0)
    for i in range(10):  # fumacinha no topo do vulcão
        ph = (T * 0.25 + i / 10) % 1.0
        cv.drawCircle(250 + 90 * ph + 10 * math.sin(T + i), 690 - 200 * ph, 18 + 50 * ph, fill(C("#e8e2da", 120 * (1 - ph))))
    cv.restore(); post(cv, T, 6, 40)


def p1_van(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.05)
    outdoor(cv, T, "pasto", sig=5, z=1.15, dy=-60)
    van(cv, 760, 1700, 1.0)
    P_(cv, T, "rafa", 170, 1800, 0.78, "happy", "point")
    P_(cv, T, "duda", 400, 1830, 0.74, "happy", "point")
    cv.restore(); post(cv, T, 10, 60)


def p1_fraco(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.08)
    outdoor(cv, T, "pasto", sig=6, z=1.2, dy=-80)
    P_(cv, T, "duda", 170, 1700, 0.62, "skeptic", "cross", sig=4)
    P_(cv, T, "rafa", 920, 1700, 0.64, "shock", "stand", sig=4, flip=True)
    TECA(cv, T, 540, 2050, 1.35, "smug", "hips")
    cv.restore(); post(cv, T, 14, 70)


def p1_duashoras(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    outdoor(cv, T, "trilha", sig=2.5)
    wk = T * 3.5
    P_(cv, T, "biel", 230, 1720, 0.62, "tired", "stand", walk=wk, lean=-8)
    P_(cv, T, "duda", 440, 1760, 0.6, "tired", "stand", walk=wk + 1, lean=-10)
    P_(cv, T, "rafa", 870, 1740, 0.64, "angry", "stand", walk=wk + 2, lean=-6)
    TECA(cv, T, 650, 1820, 0.72, "worried", "stand", talk=False, walk=wk + 0.5, lean=-6)
    cv.restore(); post(cv, T, 10, 60)
    date_stamp(cv, "2 HORAS DEPOIS", lt, y=470, size=120)


def p1_semsinal(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.08)
    outdoor(cv, T, "trilha", sig=6, z=1.2, dy=-100)
    TECA(cv, T, 540, 2080, 1.4, "worried", "phone")
    cv.restore(); post(cv, T, 14, 60)
    for k, (wd, txt, x) in enumerate((("sinal", "SEM SINAL", 300), ("mapa", "SEM MAPA", 780), ("ideia", "???", 540))):
        t0 = ws(9, wd)
        if T >= t0:
            y = 470 if k < 2 else 640
            bubble(cv, txt, x, y, T - t0, size=64, tail=(0, 0))


def p1_brasileiro(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.05, 1.12)
    outdoor(cv, T, "trilha", sig=8, z=1.3, dy=-140)
    TECA(cv, T, 540, 2120, 1.5, "smug", "pockets")
    sparkle(cv, 720, 860, lt - 0.8)
    cv.restore(); post(cv, T, 18, 60)


def p1_pulinho(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.05)
    outdoor(cv, T, "trilha", sig=3)
    P_(cv, T, "biel", 160, 1820, 0.7, "tired", "stand", lean=-14)
    P_(cv, T, "duda", 370, 1850, 0.66, "tired", "hips")
    P_(cv, T, "rafa", 920, 1830, 0.7, "skeptic", "cross", flip=True)
    TECA(cv, T, 650, 1840, 0.9, "happy", "talk")
    cv.restore(); post(cv, T, 10, 60)


def p1_sozinho(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.1)
    outdoor(cv, T, "trilha", sig=2)
    TECA(cv, T, 540 + lt * 260, 1560 - lt * 120, 0.42, "happy", "pockets", talk=False, walk=T * 8, shadow=True)
    cv.restore(); post(cv, T, 8, 70)


def p1_andei(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.03, hand=0.6)
    plate(cv, "mato", 2.5, 1.12, dx=-lt * 90)
    rays(cv, 780, -100, T, col="#fff0b8", n=6, a=34, spread=30, base=105)
    TECA(cv, T, 300 + lt * 260, 1820, 0.8, "worried", "pockets", talk=False, walk=T * 9)
    cv.restore(); post(cv, T, 12, 90)


def p1_casinha(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.08)
    outdoor(cv, T, "casa", "dusk", sig=1.5)
    TECA(cv, T, 860, 1900, 0.95, "shock", "stand", talk=False, flip=True)
    cv.restore(); post(cv, T, 10, 60)


def p1_caminhonetes(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.25, fx=320, fy=1150)
    outdoor(cv, T, "casa", "dusk", sig=1.2)
    cv.restore(); post(cv, T, 8, 50, warm=True)


def p1_bati(cv, lt, d, T, t_buenas):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    outdoor(cv, T, "casa_close", "dusk", sig=2)
    if T < t_buenas:
        TECA(cv, T, 640, 1840, 1.0, "neutral", "point", talk=False, flip=True)
    else:
        TECA(cv, T, 640, 1840, 1.0, "happy", "wave", flip=True)
    cv.restore(); post(cv, T, 10, 50)
    t0 = ws(15, "porta")
    for k in range(2):
        if 0 < T - t0 - k * 0.25 < 1.2:
            stamp(cv, "TOC", T - t0 - k * 0.25, x=330 + k * 150, y=700 - k * 60, size=90, col="#ffffff", fg="#1b1410", rot=-10 + k * 16)


def p1_olhou(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.05)
    outdoor(cv, T, "casa_close", "dusk", sig=3)
    g = math.sin(lt * 3.2)
    P_(cv, T, "chefe", 760, 1880, 0.95, "skeptic", "cross", gaze=0, flip=True, lean=4 * g)
    TECA(cv, T, 260, 1880, 0.9, "worried", "pockets", talk=False)
    cv.restore(); post(cv, T, 8, 50)


def p1_jaqueta(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.1, fx=540)
    outdoor(cv, T, "casa_close", "dusk", sig=8, z=1.4)
    TECA(cv, T, 540, 2540, 2.2, "worried", "pockets", talk=False)
    cv.restore(); post(cv, T, 14, 50)
    circle_mark(cv, 540 + (540 - 86 * 2.2 - 540) * 1.1, 1280 + (2540 - 515 * 2.2 - 1280) * 1.1, 130, lt - 0.2, "#ffd54a")


def p1_tito(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.08)
    outdoor(cv, T, "casa_close", "dusk", sig=6, z=1.25, dy=-100)
    P_(cv, T, "chefe", 540, 2080, 1.35, "happy", "point", talk=True, flip=True)
    cv.restore(); post(cv, T, 14, 50)
    bubble(cv, "TITO?", 820, 420, lt - 0.3, size=90, tail=(-80, 80))


def p1_naosou(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.05, 1.15)
    outdoor(cv, T, "casa_close", "dusk", sig=9, z=1.4, dy=-160)
    TECA(cv, T, 540, 2350, 1.9, "worried", "pockets", talk=True, look=-0.2)
    cv.restore(); post(cv, T, 16, 40)


def p1_cinco(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.1)
    outdoor(cv, T, "casa_close", "dusk", sig=3)
    for i, (lk, x) in enumerate((("capanga3", 110), ("capanga1", 330), ("chefe", 545), ("capanga2", 760), ("capanga4", 975))):
        P_(cv, T, lk, x, 1650 + abs(i - 2) * -20, 0.68, "angry", "cross" if i != 3 else "radio", seed=i)
    TECA(cv, T, 540, 2250, 0.78, "shock", "stand", talk=False, free=True)
    cv.restore(); post(cv, T, 8, 40, warm=True)
    vignette(cv, 120)


def p1_soueu(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    outdoor(cv, T, "casa_close", "dusk", sig=7, z=1.3, dy=-120)
    TECA(cv, T, 540, 2080, 1.4, "happy" if T >= ws(20, "sou") else "worried", "stand", look=0.3)
    cv.restore(); post(cv, T, 14, 40)


def p1_seria(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.25)
    outdoor(cv, T, "casa_close", "dusk", sig=3)
    k = ease(min(1, lt / d))
    P_(cv, T, "capanga1", 120 + 90 * k, 1900, 1.0 + 0.2 * k, "angry", "cross", sig=2)
    P_(cv, T, "capanga4", 960 - 90 * k, 1900, 1.0 + 0.2 * k, "angry", "cross", sig=2, flip=True)
    TECA(cv, T, 540, 1830, 0.8, "shock", "stand", talk=False)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#5a0a0a", 90 * k)))
    post(cv, T, 0, 30, leak=False, warm=False); vignette(cv, 200 * k)


# ============================================================ PARTE 2
def p2_recap(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    plate(cv, "mato", 3)
    TECA(cv, T, 540, 1830, 1.0, "worried", "phone")
    cv.restore(); post(cv, T, 10, 70)
    stamp(cv, "PARTE 2", lt, y=480, size=140, col="#ffd54a", fg="#1b2a6a", rot=-5)


def p2_confundido(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.08)
    outdoor(cv, T, "casa_close", "dusk", sig=3)
    for i, (lk, x) in enumerate((("capanga1", 150), ("chefe", 400), ("capanga2", 930))):
        P_(cv, T, lk, x, 1720, 0.68, "happy" if lk == "chefe" else "skeptic", "cross" if i != 1 else "point", flip=x > 540)
    TECA(cv, T, 660, 1850, 0.9, "worried", "stand", talk=False)
    cv.restore(); post(cv, T, 8, 50)
    bubble(cv, "TITO!", 660, 520, T - ws(2, "tito"), size=90, tail=(0, 70))


def p2_mochila(cv, lt, d, T, t_fal):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    outdoor(cv, T, "casa_close", "dusk", sig=3)
    got = T >= ws(3, "mochila") + 0.5
    if T < t_fal:
        P_(cv, T, "chefe", 720, 1860, 0.95, "smug", "give" if not got else "hips", flip=True)
        if not got: mochila(cv, 720 - 330 * 0.95, 1860 - 470 * 0.95, 0.6)
        TECA(cv, T, 290, 1860 + (14 if got else 0), 0.9, "shock" if got else "worried", "stand", talk=False, lean=(-8 if got else None))
        if got: mochila(cv, 290, 1860 - 330 * 0.9, 0.62, rot=-6)
    else:
        P_(cv, T, "chefe", 720, 1860, 0.95, "angry", "point", talk=True, flip=True)
        TECA(cv, T, 290, 1874, 0.9, "worried", "stand", talk=False, lean=-8)
        mochila(cv, 290, 1860 - 330 * 0.9, 0.62, rot=-6)
    cv.restore(); post(cv, T, 8, 50)
    for k, w in enumerate(("abre", "para")):
        try: t0 = ws(3, w)
        except IndexError: continue
        if T >= t0: stamp(cv, "NÃO " + w.upper(), T - t0, x=540, y=430 + k * 160, size=96, rot=-6 + k * 8)


def p2_naosabia(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.1)
    outdoor(cv, T, "estrada", sig=8, z=1.3, dy=-120)
    mochila(cv, 540 - 220, 2100 - 900, 1.1, rot=-10)
    TECA(cv, T, 540, 2100, 1.4, "closed" if T >= ws(4, "nem") else "worried", "pockets")
    cv.restore(); post(cv, T, 14, 60)


def p2_radio(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    outdoor(cv, T, "estrada", sig=2)
    P_(cv, T, "capanga2", 190, 1660, 0.6, "angry", "radio", sig=2.5)
    wk = T * 6
    mochila(cv, 640 - 40, 1820 - 480 * 0.85, 0.55, rot=-4)
    TECA(cv, T, 640, 1820, 0.85, "worried", "pockets", talk=False, walk=wk)
    cv.restore(); post(cv, T, 10, 70)
    bub = "#@%&*!?" if int(T * 6) % 2 else "&%#@!?*"
    bubble(cv, bub, 300, 1000, lt - 0.2, size=60, tail=(-40, 60))


def p2_entendi(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.05, 1.18)
    outdoor(cv, T, "estrada", sig=9, z=1.4, dy=-160)
    TECA(cv, T, 540, 2300, 1.8, "skeptic", "think", look=-0.4)
    cv.restore(); post(cv, T, 14, 40)


def p2_policia(cv, lt, d, T):
    dx, dy = shake(lt, 30, 4)
    cv.save(); cv.translate(dx, dy); cam(cv, lt, d, 1.1, 1.2)
    outdoor(cv, T, "estrada", sig=9, z=1.4, dy=-160)
    TECA(cv, T, 540, 2300, 1.8, "shock", "panic", talk=False)
    cv.restore()
    police_glow(cv, T, 540, 800, 1000, 130)
    flash(cv, max(0, 0.8 - lt * 3))
    bigword(cv, "POLICÍA!", lt, y=520, size=210, col="#ffffff")


def p2_atleta(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.12)
    outdoor(cv, T, "estrada", sig=6, z=1.25, dy=-80)
    rays(cv, 540, 600, T, col="#fff0b8", n=14, a=40, spread=360, base=0)
    TECA(cv, T, 540, 2100, 1.45, "determined", "flex")
    cv.restore(); post(cv, T, 16, 80)


def p2_corri(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.05)
    outdoor(cv, T, "estrada", sig=2.5)
    t_drop = ws(9, "mochila"); t_run = ws(9, "corri")
    if T < t_drop:
        mochila(cv, 540 - 40, 1820 - 480 * 0.9, 0.58, rot=-4); TECA(cv, T, 540, 1820, 0.9, "determined", "stand", talk=False)
    else:
        k = min(1, (T - t_drop) / 0.25)
        mochila(cv, 470, lerp(1820 - 430, 1760, ein(k)), 0.58, rot=lerp(-4, 20, k))
        if T < t_run:
            TECA(cv, T, 540, 1820, 0.9, "shock", "panic", talk=False)
        else:
            r = (T - t_run)
            TECA(cv, T, 540 + r * 900, 1820, 0.9, "shock", "panic", talk=False, walk=T * 16, lean=12)
            cv.drawCircle(540 + r * 900 - 140, 1800, 60 + 40 * r, fill(C("#d9c2a0", 160 * max(0, 1 - r))))
    cv.restore(); post(cv, T, 10, 60)


def p2_correndo(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.04, hand=1.6)
    plate(cv, "mato", 5, 1.2, dx=-((lt * 600) % 200) + 100)
    TECA(cv, T, 540, 1840, 1.0, "shock", "panic", talk=False, walk=T * 18, lean=14)
    cv.restore(); speed_lines(cv, T, 110); post(cv, T, 8, 0)


def p2_tropecei(cv, lt, d, T):
    t0 = ws(11, "tropecei")
    cv.save(); cam(cv, lt, d, 1.0, 1.04, hand=1.4)
    plate(cv, "mato", 4, 1.2, dx=-((lt * 500) % 200) + 100)
    root = skia.Path(); root.moveTo(300, 1840); root.cubicTo(420, 1760, 560, 1760, 700, 1850); cv.drawPath(root, stroke(C("#2b1a12"), 34)); cv.drawPath(root, stroke(C("#5a3a22"), 24))
    if T < t0 + 0.15:
        TECA(cv, T, 520, 1840, 1.0, "shock", "panic", talk=False, walk=T * 18, lean=14)
    else:
        k = min(1, (T - t0 - 0.15) / 0.5)
        cv.save(); cv.translate(560 + 260 * k, 1840 - 160 * math.sin(k * math.pi)); cv.rotate(95 * ease(k))
        TECA(cv, T, 0, 0, 1.0, "shock", "panic", talk=False, shadow=False); cv.restore()
    cv.restore(); post(cv, T, 8, 30)


def p2_rio(cv, lt, d, T):
    t_cai = ws(12, "caí")
    cv.save(); cam(cv, lt, d, 1.0, 1.05)
    sky(cv, "dusk"); plate(cv, "rio", 2)
    if T < t_cai:
        k = min(1, lt / max(0.1, t_cai - (T - lt)))
        x, y = lerp(-100, 520, k), lerp(900, 1500, k)
        cv.save(); cv.translate(x, y); cv.rotate(lt * 720)
        TECA(cv, T, 0, 380, 0.55, "shock", "panic", talk=False, shadow=False); cv.restore()
    splash(cv, 540, 1520, T - t_cai, 1.2)
    cv.restore(); post(cv, T, 8, 40)


def p2_viatura(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    outdoor(cv, T, "viatura", "dusk", sig=2)
    police_glow(cv, T, 330, 1150, 600, 80 if T >= ws(13, "viatura") else 0)
    P_(cv, T, "policial", 260, 1880, 0.85, "skeptic", "hips")
    TECA(cv, T, 790, 1880, 0.9, "worried", "stand", talk=False, flip=True)
    drips(cv, 790, 1880, 0.9, T)
    cv.restore(); post(cv, T, 8, 40)


def p2_maos(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.08)
    outdoor(cv, T, "viatura", "dusk", sig=5, z=1.2, dy=-80)
    police_glow(cv, T, 400, 900, 700, 60)
    TECA(cv, T, 540, 2050, 1.35, "shock", "panic", talk=False)
    drips(cv, 540, 2050, 1.35, T)
    cv.restore(); post(cv, T, 12, 40)


def p2_neymar(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.05, 1.15)
    outdoor(cv, T, "viatura", "dusk", sig=9, z=1.4, dy=-150)
    TECA(cv, T, 540, 2330, 1.85, "happy", "panic", k=1.2)
    drips(cv, 540, 2330, 1.85, T)
    cv.restore(); post(cv, T, 14, 40)
    for k, w in enumerate(("brasil", "neymar")):
        t0 = ws(15, w)
        if T >= t0: sparkle(cv, 260 + k * 560, 520, T - t0, 1.4, "#ffe14a")


def p2_riu(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.08)
    outdoor(cv, T, "viatura", "dusk", sig=6, z=1.25, dy=-100)
    P_(cv, T, "policial", 540, 2080, 1.4, "laugh", "laugh", lean=4 * math.sin(T * 14))
    cv.restore(); post(cv, T, 14, 40)


def p2_meses(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.1, fy=1000)
    outdoor(cv, T, "casa", "dusk", sig=2, )
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#0a1430", 110)))
    police_glow(cv, T, 540, 1150, 900, 110)
    post(cv, T, 6, 40, warm=False)


def p2_largar(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.35, fx=560, fy=1050)
    outdoor(cv, T, "estrada", sig=1.5)
    mochila(cv, 520, 1500, 0.28, rot=20)
    cv.restore(); post(cv, T, 6, 40)
    circle_mark(cv, 520 + (520 - 560) * 0.35, 1050 + (1500 - 1050) * 1.35, 120, T - ws(18, "mochila"))
    circle_mark(cv, 600, 1020, 110, T - ws(18, "caminhão"), "#ffd54a")


def p2_pegou(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    outdoor(cv, T, "casa_close", "dusk", sig=3)
    for i, (lk, x) in enumerate((("capanga3", 120), ("capanga1", 320), ("chefe", 530), ("capanga2", 740))):
        P_(cv, T, lk, x, 1700, 0.6, "sad", "panic", seed=i)
    P_(cv, T, "policial2", 960, 1880, 0.85, "smug", "hips", flip=True)
    cv.restore(); police_glow(cv, T, 540, 900, 900, 70); post(cv, T, 6, 40)


def p2_amigos(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.05)
    plate(cv, "delegacia", 3)
    k = eout(min(1, lt / 0.5))
    P_(cv, T, "duda", lerp(-150, 180, k), 1860, 0.85, "shock", "stand")
    P_(cv, T, "rafa", lerp(-300, 420, k), 1890, 0.88, "shock", "panic")
    P_(cv, T, "biel", lerp(1300, 880, k), 1880, 0.9, "shock", "stand", flip=True)
    cv.restore(); post(cv, T, 12, 60)


def p2_cafe(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    plate(cv, "delegacia", 3)
    P_(cv, T, "policial", 220, 1860, 0.85, "laugh", "cup")
    P_(cv, T, "policial2", 880, 1860, 0.82, "happy", "cup", flip=True)
    TECA(cv, T, 560, 1880, 0.95, "laugh", "think", talk=False)
    cup(cv, 560 + 70 * 0.95, 1880 - 640 * 0.95, 1.0, T)
    cv.restore(); post(cv, T, 16, 70)


def p2_naovirei(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.06)
    plate(cv, "delegacia", 7, 1.25, dy=-80)
    TECA(cv, T, 540, 2080, 1.4, "neutral", "shrug")
    cv.restore(); post(cv, T, 14, 60)


def p2_heroi(cv, lt, d, T):
    cv.save(); cam(cv, lt, d, 1.0, 1.12)
    plate(cv, "delegacia", 8, 1.3, dy=-100)
    rays(cv, 540, 700, T, col="#fff0b8", n=14, a=36, spread=360, base=T * 8)
    TECA(cv, T, 540, 2100, 1.45, "smug", "hips")
    # medalha
    mx, my = 540 + 40 * 1.45, 2100 - 520 * 1.45
    k = pop(lt - 0.6, 0.3)
    if k > 0:
        cv.drawLine(mx - 40, my - 120, mx, my, stroke(C("#2e9a4a"), 14)); cv.drawLine(mx + 40, my - 120, mx, my, stroke(C("#ffe14a"), 14))
        m = skia.Path(); m.addCircle(mx, my + 30, 46 * k); _tt(cv, m, "#f2c84b", "#c9982a", lw=5, off=(10, 10))
        sparkle(cv, mx + 30, my + 10, (lt - 0.6) % 1.4, 0.8)
    cv.restore(); post(cv, T, 18, 90)


SHOTS = []


def add(s, e, fn, *a):
    SHOTS.append((s, e, fn, a))


if PART == 1:
    S = lambda i: L[i]["s"]
    add(0, S(2), p1_flex); add(S(2), ws(2, "eu"), p1_map); add(ws(2, "eu"), S(3), p1_eu_primeiro)
    add(S(3), S(4), p1_guio); add(S(4), S(5), p1_spoiler); add(S(5), S(6), p1_dia1)
    add(S(6), ws(6, "café"), p1_pasto); add(ws(6, "café"), ws(6, "vulcão") - 0.3, p1_cafe); add(ws(6, "vulcão") - 0.3, S(7), p1_vulcao)
    add(S(7), ws(7, "disse"), p1_van); add(ws(7, "disse"), S(8), p1_fraco)
    add(S(8), S(9), p1_duashoras); add(S(9), S(10), p1_semsinal); add(S(10), S(11), p1_brasileiro)
    add(S(11), S(12), p1_pulinho); add(S(12), S(13), p1_sozinho)
    add(S(13), ws(13, "achei"), p1_andei); add(ws(13, "achei"), S(14), p1_casinha); add(S(14), S(15), p1_caminhonetes)
    add(S(15), S(16), p1_bati, ws(15, "buenas")); add(S(16), ws(16, "viu"), p1_olhou); add(ws(16, "viu"), S(17), p1_jaqueta)
    add(S(17), S(18), p1_tito); add(S(18), S(19), p1_naosou); add(S(19), S(20), p1_cinco); add(S(20), S(21), p1_soueu)
    add(S(21), S(22), p1_seria); add(S(22), END + 1, endcard)
    CAP_HIDE = S(22)
else:
    S = lambda i: L[i]["s"]
    add(0, S(2), p2_recap); add(S(2), S(3), p2_confundido); add(S(3), S(4), p2_mochila, ws(3, "falaram"))
    add(S(4), S(5), p2_naosabia); add(S(5), S(6), p2_radio); add(S(6), S(7), p2_entendi); add(S(7), S(8), p2_policia)
    add(S(8), S(9), p2_atleta); add(S(9), S(10), p2_corri); add(S(10), S(11), p2_correndo); add(S(11), S(12), p2_tropecei)
    add(S(12), S(13), p2_rio); add(S(13), S(14), p2_viatura); add(S(14), S(15), p2_maos); add(S(15), S(16), p2_neymar)
    add(S(16), S(17), p2_riu); add(S(17), S(18), p2_meses); add(S(18), S(19), p2_largar); add(S(19), S(20), p2_pegou)
    add(S(20), S(21), p2_amigos); add(S(21), S(22), p2_cafe); add(S(22), S(23), p2_naovirei); add(S(23), END + 1, p2_heroi)
    CAP_HIDE = None
NFRAMES = int(END * FPS)


def render_frame(surface, fi):
    T = fi / FPS
    cv = surface.getCanvas(); cv.clear(C("#000000"))
    for s, e, fn, a in SHOTS:
        if s <= T < e:
            cv.save(); fn(cv, T - s, e - s, T, *a); cv.restore(); break
    vignette(cv, 120)
    draw_caption(cv, CHUNKS, T, y=CAP_Y, hide_after=CAP_HIDE)
    grain(cv, fi, 14)


if __name__ == "__main__":
    a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    if b <= 0: b = NFRAMES
    surf = skia.Surface(W, H)
    if out.endswith(".png"):
        for fi in range(a, b):
            render_frame(surf, fi); surf.makeImageSnapshot().save(out.replace(".png", f"_{fi:05d}.png"))
        sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fi in range(a, b):
        render_frame(surf, fi)
        ff.stdin.write(surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).tobytes())
    ff.stdin.close(); ff.wait()
