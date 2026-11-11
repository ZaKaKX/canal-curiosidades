"""Shared 2.5D drawing kit (skia): paints, easing, sky/sea, ships, characters, captions, post."""
import math, random
import numpy as np
import skia

W, H, FPS = 1080, 1920, 30
INK = None
FONT_PATH = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
TF = skia.Typeface.MakeFromFile(FONT_PATH)


def C(h, a=255):
    h = h.lstrip("#")
    return skia.ColorSetARGB(int(max(0, min(255, a))), int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


INK = C("#1b1410")


def fill(c):
    return skia.Paint(Color=c, AntiAlias=True)


def stroke(c, w):
    return skia.Paint(Color=c, AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap)


def lin(x0, y0, x1, y1, cols, pos=None):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], cols, pos))
    return p


def rad(cx, cy, r, cols, pos=None):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(1, r), cols, pos))
    return p


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)


def eout(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ein(x):
    x = clamp(x); return x ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def shape(cv, path, paint, ow=6):
    cv.drawPath(path, paint)
    if ow:
        cv.drawPath(path, stroke(INK, ow))


def poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


class blur:
    def __init__(self, cv, sigma):
        self.cv, self.s = cv, sigma

    def __enter__(self):
        if self.s > 0.3:
            p = skia.Paint()
            p.setImageFilter(skia.ImageFilters.Blur(self.s, self.s))
            self.cv.saveLayer(None, p)
        else:
            self.cv.save()

    def __exit__(self, *a):
        self.cv.restore()


def zoom(cv, z, cx=W / 2, cy=H / 2):
    cv.translate(cx, cy); cv.scale(z, z); cv.translate(-cx, -cy)


# ---------------- environment ----------------
RNG = random.Random(7)
STARS = [(RNG.random() * W, RNG.random() * H * 0.55, RNG.random() * 2.6 + 0.8, RNG.random() * 6) for _ in range(160)]


def sky(cv, top, bot, y1=H):
    cv.drawRect(skia.Rect(0, 0, W, y1), lin(0, 0, 0, y1, [C(top), C(bot)]))


def stars(cv, t, alpha=1.0, ymax=H * 0.55):
    for x, y, r, ph in STARS:
        if y > ymax: continue
        a = (0.55 + 0.45 * math.sin(t * 2 + ph)) * 255 * alpha
        cv.drawCircle(x, y, r, fill(C("#fff6dc", a)))


def moon(cv, x, y, r=60):
    cv.drawCircle(x, y, r * 5, rad(x, y, r * 5, [C("#cfe0ff", 70), C("#cfe0ff", 0)]))
    cv.drawCircle(x, y, r, fill(C("#f4f1e4")))
    cv.drawCircle(x - r * 0.3, y - r * 0.2, r * 0.18, fill(C("#d9d4c2")))
    cv.drawCircle(x + r * 0.25, y + r * 0.3, r * 0.12, fill(C("#d9d4c2")))


def sun_glow(cv, x, y, r, col="#ffd27a", a=160):
    cv.drawCircle(x, y, r, rad(x, y, r, [C(col, a), C(col, 0)]))


def rays(cv, x, y, t, col="#fff2c4", n=7, length=2400, a=38, spread=70, base=90):
    for i in range(n):
        ang = math.radians(base - spread / 2 + spread * i / max(1, n - 1) + 3 * math.sin(t * 0.6 + i))
        w = math.radians(2.2 + 1.4 * math.sin(i * 1.7))
        p = poly([(x, y), (x + math.cos(ang - w) * length, y + math.sin(ang - w) * length),
                  (x + math.cos(ang + w) * length, y + math.sin(ang + w) * length)])
        pt = skia.Paint(AntiAlias=True)
        pt.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), length, [C(col, a), C(col, 0)]))
        pt.setBlendMode(skia.BlendMode.kPlus)
        cv.drawPath(p, pt)


def wave_path(y, t, amp, k, speed, y2=H, phase=0.0):
    p = skia.Path()
    p.moveTo(-20, y2)
    for x in range(-20, W + 41, 20):
        yy = y + amp * math.sin(x * k + t * speed + phase) + amp * 0.5 * math.sin(x * k * 2.3 - t * speed * 1.3 + phase)
        p.lineTo(x, yy)
    p.lineTo(W + 40, y2); p.close()
    return p


def sea(cv, hy, t, top, bot, lines="#ffffff", la=40):
    cv.drawRect(skia.Rect(0, hy, W, H), lin(0, hy, 0, H, [C(top), C(bot)]))
    for i in range(12):
        yy = hy + 6 + (i ** 1.7) * 9
        if yy > H: break
        amp = 1.5 + i * 0.8
        p = skia.Path()
        for j, x in enumerate(range(-20, W + 41, 24)):
            y = yy + amp * math.sin(x * 0.012 + t * (0.8 + i * 0.1) + i)
            (p.moveTo if j == 0 else p.lineTo)(x, y)
        cv.drawPath(p, stroke(C(lines, la * (1 - i / 14)), 1.5 + i * 0.35))


def near_sea(cv, y, t, top, bot, amp=10, crest="#ffffff", ca=110):
    p = wave_path(y, t, amp, 0.009, 1.4)
    cv.drawPath(p, lin(0, y - amp, 0, H, [C(top), C(bot)]))
    cv.drawPath(wave_path(y, t, amp, 0.009, 1.4, y2=H), stroke(C(crest, ca), 4))


def vignette(cv, strength=170):
    cv.drawRect(skia.Rect(0, 0, W, H), rad(W / 2, H * 0.48, H * 0.75, [C("#000000", 0), C("#000000", 0), C("#000000", strength)], [0, 0.55, 1]))


_NOISE = []


def grain(cv, frame, a=14):
    global _NOISE
    if not _NOISE:
        rs = np.random.RandomState(3)
        for _ in range(4):
            n = rs.randint(0, 255, (H // 2, W // 2), dtype=np.uint8)
            arr = np.dstack([n, n, n, np.full_like(n, 255)])
            _NOISE.append(skia.Image.fromarray(arr))
    p = skia.Paint(Alphaf=a / 255)
    p.setBlendMode(skia.BlendMode.kOverlay)
    cv.drawImageRect(_NOISE[frame % 4], skia.Rect(0, 0, W, H), skia.SamplingOptions(), p)


def flash(cv, a, col="#ffffff"):
    if a > 0:
        cv.drawRect(skia.Rect(0, 0, W, H), fill(C(col, a * 255)))


def shake(t_since, mag=26, decay=5.0):
    if t_since < 0: return 0, 0
    m = mag * math.exp(-decay * t_since)
    return m * math.sin(t_since * 73), m * math.cos(t_since * 61)


def smoke(cv, x, y, t, s=1.0, col="#8d8a86", n=8, drift=-70, alpha=110):
    for i in range(n):
        ph = (t * 0.35 + i / n) % 1.0
        px = x + drift * ph * 3 * s + 12 * math.sin(i * 3 + t)
        py = y - ph * 260 * s
        r = (26 + ph * 70) * s
        cv.drawCircle(px, py, r, fill(C(col, alpha * (1 - ph))))


# ---------------- props ----------------

def ship(cv, x, y, s, kind="titanic", t=0.0, night=False, name=None, smoke_on=True, tilt=0.0, flip=False,
         damage=0.0, lit=True):
    """Side view liner facing right. (x,y)=waterline center."""
    cv.save(); cv.translate(x, y); cv.rotate(tilt)
    if flip: cv.scale(-1, 1)
    cv.scale(s, s)
    ow = 5 / max(0.4, s) * 0.9 + 2
    if kind == "warship":
        hull = poly([(-420, -95), (380, -100), (420, -80), (500, 50), (380, 70), (-380, 70), (-440, -20)])
        shape(cv, hull, lin(0, -100, 0, 70, [C("#8a929c"), C("#4b525b")]), ow)
        for fx in (-120, 30):
            f = poly([(fx, -95), (fx + 50, -95), (fx + 30, -260), (fx - 15, -260)])
            shape(cv, f, fill(C("#5d646d")), ow)
        shape(cv, poly([(-300, -95), (220, -95), (200, -150), (-280, -150)]), fill(C("#767e88")), ow)
        for gx in (-330, 260):
            cv.drawRoundRect(skia.Rect(gx - 40, -140, gx + 40, -100), 14, 14, fill(C("#5d646d")))
            cv.drawLine(gx + 20, -125, gx + 110, -135, stroke(INK, 12))
        cv.drawLine(-200, -150, -200, -380, stroke(INK, 7))
        cv.drawLine(150, -150, 150, -360, stroke(INK, 7))
        if smoke_on:
            for fx in (-120, 30):
                smoke(cv, fx + 5, -270, t + fx, 1.0, "#55534f", 6)
        cv.restore(); return

    white = kind == "britannic"
    hull_top, hull_bot = ("#fbfaf3", "#cfd2c8") if white else ("#2a2a33", "#0d0d12")
    hull = skia.Path()
    hull.moveTo(-440, -150); hull.lineTo(450, -158); hull.lineTo(490, -168)
    hull.lineTo(455, 70); hull.lineTo(-380, 70); hull.quadTo(-470, 10, -440, -150); hull.close()
    # funnels behind superstructure
    funnel_x = [-250, -100, 50, 200]
    for fx in funnel_x:
        f = poly([(fx - 30, -255), (fx + 30, -255), (fx + 5, -430), (fx - 55, -430)])
        shape(cv, f, lin(fx - 50, 0, fx + 30, 0, [C("#e6b25a"), C("#b9822f")]), ow)
        shape(cv, poly([(fx - 49, -390), (fx + 10, -390), (fx + 5, -430), (fx - 55, -430)]), fill(C("#15151a")), ow)
        if smoke_on and fx != 200:
            smoke(cv, fx - 25, -440, t + fx * 0.01, 1.0, "#9a958c" if not night else "#5e5b57", 7)
    # masts
    cv.drawLine(-400, -150, -420, -560, stroke(INK, 7)); cv.drawLine(390, -160, 370, -560, stroke(INK, 7))
    cv.drawLine(-420, -540, 370, -545, stroke(C("#1b1410", 140), 2.5))
    # superstructure
    sup = poly([(-360, -150), (330, -156), (300, -255), (-330, -250)])
    shape(cv, sup, lin(0, -255, 0, -150, [C("#ffffff"), C("#d8d6cc")]), ow)
    shape(cv, poly([(-280, -250), (250, -253), (235, -285), (-265, -282)]), fill(C("#f2f0e8")), ow)
    for bx in range(-250, 230, 70):
        cv.drawRoundRect(skia.Rect(bx, -300, bx + 46, -284), 8, 8, fill(C("#fbfbf6")))
        cv.drawRoundRect(skia.Rect(bx, -300, bx + 46, -284), 8, 8, stroke(INK, 2.5))
    # hull
    shape(cv, hull, lin(0, -168, 0, 70, [C(hull_top), C(hull_bot)]), ow)
    if white:
        cv.drawRect(skia.Rect(-430, -95, 470, -80), fill(C("#3d8b4b")))
        for cx in (-250, 20, 280):
            cv.drawRect(skia.Rect(cx - 12, -150, cx + 12, -40), fill(C("#d23a2f")))
            cv.drawRect(skia.Rect(cx - 50, -107, cx + 50, -83), fill(C("#d23a2f")))
    else:
        cv.drawLine(-440, -140, 480, -150, stroke(C("#e9e2cf"), 5))
    # windows
    wc = C("#ffd77a") if (night and lit) else (C("#4a5560") if not white else C("#7d8a96"))
    for row, yy in enumerate((-235, -205, -175)):
        for wx in range(-320, 300, 34):
            if (wx * 7 + row * 13) % 5 == 0 and night: continue
            cv.drawRect(skia.Rect(wx, yy, wx + 14, yy + 10), fill(wc))
    for wx in range(-400, 440, 30):
        cv.drawCircle(wx, -120 if not white else -125, 4.5, fill(wc if night and lit else C("#d9d4c6" if not white else "#8b98a4")))
    if night and lit:
        cv.drawRect(skia.Rect(-360, -260, 330, -140), rad(0, -200, 420, [C("#ffd77a", 40), C("#ffd77a", 0)]))
    if damage > 0:
        d = damage
        hole = poly([(-330, -140), (-300, -150 + 30 * d), (-270, -120), (-250, -60 * d - 40), (-290, -10),
                     (-320, -50), (-350, -80)])
        shape(cv, hole, fill(C("#050506")), 4)
        for i in range(5):
            cv.drawLine(-330 + i * 18, -140 + i * 7, -360 + i * 25, -170 + i * 5, stroke(INK, 3))
    if name:
        f = skia.Font(TF, 34)
        cv.drawString(name, 330 - f.measureText(name), -100, f, fill(C("#f4e3b0") if not white else C("#24302a")))
    cv.restore()


def iceberg(cv, x, y, s, light="#e9f6ff", mid="#a9d1ea", dark="#5f8fb3"):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    body = poly([(-300, 0), (-250, -180), (-150, -260), (-80, -420), (20, -330), (90, -480), (170, -300),
                 (240, -230), (320, 0)])
    shape(cv, body, lin(-300, -480, 300, 0, [C(light), C(mid), C(dark)], [0, 0.5, 1]), 6)
    shape(cv, poly([(-80, -420), (20, -330), (-20, -150), (-150, -260)]), fill(C(light, 230)), 0)
    shape(cv, poly([(90, -480), (170, -300), (120, -120), (20, -330)]), fill(C(dark, 120)), 0)
    cv.drawPath(body, stroke(INK, 6))
    cv.restore()


def lifeboat(cv, x, y, s, num="16", fullness=0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    b = skia.Path(); b.moveTo(-230, -60); b.lineTo(230, -60); b.quadTo(220, 40, 120, 50); b.lineTo(-120, 50)
    b.quadTo(-220, 40, -230, -60); b.close()
    shape(cv, b, lin(0, -60, 0, 50, [C("#f3efe2"), C("#b9b2a0")]), 6)
    cv.drawLine(-225, -40, 225, -40, stroke(C("#8b5a2b"), 8))
    f = skia.Font(TF, 46)
    cv.drawString(num, -f.measureText(num) / 2, 25, f, fill(C("#2b2b2b")))
    cv.restore()


def mine(cv, x, y, s, t):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    cv.drawLine(0, 120, 0, 900, stroke(C("#20262b"), 8))
    for i in range(8):
        a = math.radians(i * 45 + 10 * math.sin(t))
        cv.drawLine(math.cos(a) * 100, math.sin(a) * 100, math.cos(a) * 150, math.sin(a) * 150, stroke(INK, 16))
        cv.drawCircle(math.cos(a) * 150, math.sin(a) * 150, 14, fill(C("#3a3f45")))
    cv.drawCircle(0, 0, 120, rad(-40, -40, 180, [C("#5d646b"), C("#22272b")]))
    cv.drawCircle(0, 0, 120, stroke(INK, 7))
    cv.restore()


def propeller(cv, x, y, s, ang):
    cv.save(); cv.translate(x, y); cv.scale(s, s); cv.rotate(ang)
    for i in range(3):
        cv.save(); cv.rotate(i * 120)
        b = skia.Path(); b.moveTo(0, -20); b.cubicTo(80, -60, 210, -40, 230, 20); b.cubicTo(180, 60, 80, 40, 0, 20); b.close()
        shape(cv, b, lin(0, -40, 230, 40, [C("#e7b866"), C("#9b6a28")]), 6)
        cv.restore()
    cv.drawCircle(0, 0, 50, fill(C("#a9772f"))); cv.drawCircle(0, 0, 50, stroke(INK, 6))
    cv.restore()


def explosion(cv, x, y, p, s=1.0):
    """p: 0..1 progress"""
    if p <= 0 or p >= 1: return
    r = (120 + 900 * eout(p)) * s
    a = 255 * (1 - p)
    cv.drawCircle(x, y, r, rad(x, y, r, [C("#fff7d6", a), C("#ffb347", a * 0.8), C("#d9481f", a * 0.4), C("#d9481f", 0)], [0, 0.25, 0.6, 1]))
    cv.drawCircle(x, y, r * 0.9, stroke(C("#ffffff", a * 0.6), 10 * (1 - p) + 1))
    for i in range(14):
        ang = i * 2.39996
        d = r * (0.6 + 0.4 * ((i * 37) % 10) / 10)
        cv.drawCircle(x + math.cos(ang) * d, y + math.sin(ang) * d, 10 * s * (1 - p) + 2, fill(C("#2b1d14", a)))


def bubbles(cv, t, n=40, seed=1, col="#d8f3ff"):
    r = random.Random(seed)
    for i in range(n):
        x0, sp, rr, ph = r.random() * W, 120 + r.random() * 220, 4 + r.random() * 14, r.random() * 10
        y = H - ((t * sp + ph * 200) % (H + 100))
        cv.drawCircle(x0 + 10 * math.sin(t * 2 + ph), y, rr, stroke(C(col, 150), 3))


def date_stamp(cv, text, lt, y=430, size=170, col="#ffffff"):
    a = eout(lt / 0.35)
    if a <= 0: return
    f = skia.Font(TF, size)
    wdt = f.measureText(text)
    sc = lerp(1.25, 1.0, a)
    cv.save(); cv.translate(W / 2, y); cv.scale(sc, sc)
    cv.drawString(text, -wdt / 2 + 6, 8, f, fill(C("#000000", 90 * a)))
    sp = stroke(C("#14100c", 255 * a), 16)
    cv.drawString(text, -wdt / 2, 0, f, sp)
    cv.drawString(text, -wdt / 2, 0, f, fill(C(col, 255 * a)))
    cv.drawLine(-wdt / 2, 40, -wdt / 2 + wdt * eout((lt - 0.15) / 0.5), 40, stroke(C("#ffd54a", 255 * a), 10))
    cv.restore()


def banner(cv, text, lt, y=420, size=78, bg="#f3e4bf", fg="#2a1d12"):
    a = eout(lt / 0.3)
    if a <= 0: return
    f = skia.Font(TF, size)
    wdt = f.measureText(text)
    cv.save(); cv.translate(W / 2, y); cv.scale(lerp(0.7, 1, a), lerp(0.7, 1, a))
    r = skia.Rect(-wdt / 2 - 46, -size * 0.95, wdt / 2 + 46, size * 0.45)
    cv.drawRoundRect(r.makeOffset(8, 10), 26, 26, fill(C("#000000", 90 * a)))
    cv.drawRoundRect(r, 26, 26, fill(C(bg, 255 * a)))
    cv.drawRoundRect(r, 26, 26, stroke(C("#1b1410", 255 * a), 8))
    cv.drawString(text, -wdt / 2, 0, f, fill(C(fg, 255 * a)))
    cv.restore()


# ---------------- character ----------------

def character(cv, x, y, s, t, outfit="steward", expr="neutral", pose="stand", look=0.0, seed=0.0,
              shadow=True, rot=0.0, hair="#5a3220", skin="#f3c7a0"):
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    ow = 7
    br = 1 + 0.012 * math.sin(t * 2.3 + seed)
    if shadow:
        cv.drawOval(skia.Rect(-190, -22, 190, 22), fill(C("#000000", 80)))
    # legs + shoes
    for sx in (-1, 1):
        cv.drawLine(sx * 45, -70, sx * 50, -10, stroke(INK, 18))
        cv.drawOval(skia.Rect(sx * 50 - 34, -24, sx * 50 + 34, 6), fill(INK))
    cv.save(); cv.scale(1, br)
    nurse = outfit == "nurse"
    dress = C("#cfd9e6") if nurse else C("#2b3656")
    d = skia.Path(); d.moveTo(-90, -445); d.lineTo(90, -445); d.quadTo(130, -250, 180, -55)
    d.quadTo(0, -30, -180, -55); d.quadTo(-130, -250, -90, -445); d.close()
    shape(cv, d, fill(dress), ow)
    ap = poly([(-62, -390), (62, -390), (95, -95), (-95, -95)])
    shape(cv, ap, fill(C("#fbfaf5")), 5)
    if nurse:
        cv.drawRect(skia.Rect(-12, -350, 12, -270), fill(C("#d23a2f")))
        cv.drawRect(skia.Rect(-40, -322, 40, -298), fill(C("#d23a2f")))
    else:
        shape(cv, poly([(-60, -445), (0, -395), (60, -445)]), fill(C("#fbfaf5")), 5)
    # arms
    hand = fill(C(skin))
    arms = {
        "stand": [((-88, -420), (-150, -240)), ((88, -420), (150, -240))],
        "baby": [((-88, -420), (-70, -300)), ((88, -420), (60, -290))],
        "panic": [((-88, -420), (-210, -650 + 20 * math.sin(t * 9))), ((88, -420), (210, -650 + 20 * math.cos(t * 9)))],
        "reach": [((-88, -420), (-60, -760)), ((88, -420), (70, -770))],
        "wave": [((-88, -420), (-150, -240)), ((88, -420), (210 + 25 * math.sin(t * 8), -640))],
        "hips": [((-88, -420), (-150, -280)), ((88, -420), (150, -280))],
        "suitcase": [((-88, -420), (-150, -240)), ((88, -420), (150, -230))],
    }[pose]
    for a, b in arms:
        cv.drawLine(*a, *b, stroke(INK, 20)); cv.drawLine(*a, *b, stroke(dress, 10))
        cv.drawCircle(*b, 24, hand); cv.drawCircle(*b, 24, stroke(INK, 6))
    if pose == "suitcase":
        cv.drawLine(150, -230, 150, -205, stroke(INK, 8))
        shape(cv, skia.Path().addRoundRect(skia.Rect(85, -205, 235, -95), 14, 14), fill(C("#8a5a32")), 6)
    if pose == "baby":
        shape(cv, skia.Path().addOval(skia.Rect(-110, -380, 110, -250)), fill(C("#f6efe0")), 6)
        cv.drawCircle(40, -345, 40, fill(C("#f7d2b3"))); cv.drawCircle(40, -345, 40, stroke(INK, 5))
        cv.drawArc(skia.Rect(18, -352, 34, -340), 0, 180, False, stroke(INK, 3))
        cv.drawArc(skia.Rect(46, -352, 62, -340), 0, 180, False, stroke(INK, 3))
    cv.restore()
    # head
    hy = -575 * br
    cv.drawCircle(0, hy - 140, 58, fill(C(hair))); cv.drawCircle(0, hy - 140, 58, stroke(INK, ow))
    cv.drawCircle(0, hy, 125, fill(C(skin))); cv.drawCircle(0, hy, 125, stroke(INK, ow))
    hp = skia.Path(); hp.moveTo(-127, hy - 5); hp.cubicTo(-135, hy - 160, 135, hy - 160, 127, hy - 5)
    hp.quadTo(70, hy - 95, 0, hy - 70); hp.quadTo(-70, hy - 95, -127, hy - 5); hp.close()
    shape(cv, hp, fill(C(hair)), ow)
    if nurse:
        cap = poly([(-120, hy - 70), (120, hy - 70), (100, hy - 135), (-100, hy - 135)])
        shape(cv, cap, fill(C("#ffffff")), 6)
        cv.drawRect(skia.Rect(-9, hy - 125, 9, hy - 80), fill(C("#d23a2f")))
        cv.drawRect(skia.Rect(-24, hy - 111, 24, hy - 95), fill(C("#d23a2f")))
    else:
        shape(cv, skia.Path().addRoundRect(skia.Rect(-70, hy - 128, 70, hy - 98), 14, 14), fill(C("#ffffff")), 5)
    cv.drawOval(skia.Rect(-95, hy + 15, -55, hy + 40), fill(C("#f08a7a", 110)))
    cv.drawOval(skia.Rect(55, hy + 15, 95, hy + 40), fill(C("#f08a7a", 110)))
    lx = look * 18
    blink = ((t + seed * 1.7) % 3.3) < 0.11
    ey = hy - 5
    if expr == "wide":
        for sx in (-1, 1):
            cv.drawCircle(sx * 45 + lx, ey, 24, fill(C("#ffffff"))); cv.drawCircle(sx * 45 + lx, ey, 24, stroke(INK, 5))
            cv.drawCircle(sx * 45 + lx * 1.4, ey, 10, fill(INK))
    elif blink or expr == "closed":
        for sx in (-1, 1):
            cv.drawLine(sx * 45 - 14 + lx, ey, sx * 45 + 14 + lx, ey, stroke(INK, 6))
    else:
        for sx in (-1, 1):
            cv.drawCircle(sx * 45 + lx, ey, 13, fill(INK))
    brows = {"neutral": (-40, 0), "raised": (-62, 0), "worried": (-45, 10), "determined": (-38, -12),
             "happy": (-48, 0), "wide": (-70, 0), "sad": (-44, 12), "closed": (-40, 0)}[expr]
    for sx in (-1, 1):
        by = ey + brows[0]
        cv.drawLine(sx * 25 + lx, by - brows[1], sx * 65 + lx, by, stroke(INK, 7))
    my = hy + 58
    if expr in ("happy", "neutral"):
        w = 34 if expr == "happy" else 22
        cv.drawArc(skia.Rect(-w, my - 22, w, my + 14), 20, 140, False, stroke(INK, 7))
    elif expr == "wide":
        shape(cv, skia.Path().addOval(skia.Rect(-26, my - 16, 26, my + 34)), fill(C("#7a2b22")), 6)
    elif expr in ("worried", "sad"):
        cv.drawArc(skia.Rect(-26, my, 26, my + 34), 200, 140, False, stroke(INK, 7))
    elif expr == "determined":
        cv.drawLine(-24, my + 6, 24, my + 2, stroke(INK, 7))
    elif expr == "raised":
        cv.drawArc(skia.Rect(-22, my - 10, 22, my + 14), 10, 120, False, stroke(INK, 7))
    else:
        cv.drawLine(-18, my + 4, 18, my + 4, stroke(INK, 7))
    cv.restore()


# ---------------- captions ----------------
KEYWORDS = {"titanic", "unsinkable", "1911", "olympic", "warship", "iceberg", "sixteen", "baby", "fifteen", "hundred",
            "twist", "britannic", "mine", "propellers", "keel", "survivor", "violet", "jessop", "1912", "hospital",
            "nurse", "three", "scratch", "torn"}


def build_chunks(timings, maxw=2):
    chunks = []
    for ln in timings["lines"]:
        cur = []
        for w in ln["words"]:
            cur.append(w)
            end = w["w"][-1] in ".,!?"
            if len(cur) >= maxw or end:
                chunks.append(cur); cur = []
        if cur: chunks.append(cur)
        chunks[-1] = chunks[-1]  # keep
    out = []
    for i, ch in enumerate(chunks):
        s = ch[0]["s"]
        e = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else ch[-1]["e"] + 0.4
        e = min(e, ch[-1]["e"] + 0.35)
        out.append({"s": s, "e": e, "words": [w["w"] for w in ch]})
    return out


def draw_caption(cv, chunks, T, y=1150, size=112, hide_after=None):
    if hide_after is not None and T >= hide_after: return
    for ch in chunks:
        if ch["s"] <= T < ch["e"]:
            words = ch["words"]
            key = any(w.strip(".,!?'\"").lower() in KEYWORDS for w in words)
            f = skia.Font(TF, size)
            txt = " ".join(words).upper().replace("'S", "'S")
            wd = f.measureText(txt)
            sc = min(1.0, 940 / wd)
            pop = 1.0
            if key:
                pop = lerp(0.82, 1.0, eout((T - ch["s"]) / 0.09))
            cv.save(); cv.translate(W / 2, y); cv.scale(sc * pop, sc * pop)
            x = -wd / 2
            cv.drawString(txt, x + 5, 9, f, fill(C("#000000", 120)))
            for w in words:
                ww = w.upper()
                k = w.strip(".,!?'\"").lower() in KEYWORDS
                cv.drawString(ww, x, 0, f, stroke(C("#0e0a07"), 18))
                cv.drawString(ww, x, 0, f, fill(C("#ffd54a") if k else C("#ffffff")))
                x += f.measureText(ww + " ")
            cv.restore()
            return
