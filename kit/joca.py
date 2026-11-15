"""JOCA — personagem fixo do canal. Cabeçona redonda, pele morena clara, cabelo castanho com topete,
moletom verde-petróleo com cordão, calça jeans escura, tênis branco. Sombra cel (2 tons) + gradiente suave,
linha fina marrom, rim light configurável, boca com sincronia labial (mouth_open 0..1)."""
import math
from gfx import skia, C, fill, stroke, poly, lin

SKIN, SKIN_SH, SKIN_HI = "#f2bf98", "#d6926b", "#ffe3cc"
HAIR, HAIR_HI = "#3b2418", "#6a4330"
HOOD, HOOD_SH, HOOD_HI = "#2f8f83", "#1f6a61", "#4fb3a5"
JEANS, JEANS_SH = "#2c3a55", "#1e283d"
LINE = "#2a1c15"


def P(**k):
    p = skia.Paint(AntiAlias=True)
    for a, v in k.items():
        getattr(p, "set" + a)(v)
    return p


def _two_tone(cv, path, base, shade, light_dir=(-0.6, -0.8), hi=None, lw=4.5, shade_off=(26, 22)):
    """Fill path with base, then a hard-edged shadow (path offset toward away-from-light, clipped), soft gradient, outline."""
    cv.drawPath(path, fill(C(base)))
    cv.save(); cv.clipPath(path, doAntiAlias=True)
    sp = skia.Path(path); sp.offset(-light_dir[0] * shade_off[0], -light_dir[1] * shade_off[1])
    inv = skia.Path(path); inv.offset(light_dir[0] * shade_off[0] * 0.0, 0)
    # shadow = area of path NOT covered by the offset copy shifted toward light
    lit = skia.Path(path); lit.offset(light_dir[0] * shade_off[0], light_dir[1] * shade_off[1])
    cv.drawPath(path, fill(C(shade)))
    cv.drawPath(lit, fill(C(base)))
    b = path.computeTightBounds()
    g = skia.Paint(AntiAlias=True)
    g.setShader(skia.GradientShader.MakeLinear([skia.Point(b.left(), b.top()), skia.Point(b.right(), b.bottom())],
                                               [C(hi or "#ffffff", 60), C("#ffffff", 0), C("#000000", 40)], [0, 0.5, 1]))
    cv.drawRect(b, g)
    cv.restore()
    cv.drawPath(path, stroke(C(LINE), lw))


def joca(cv, x, y, s, t, expr="neutral", look=0.0, pose="stand", mouth_open=0.0, seed=0.0,
         rim="#ffd29a", rim_a=0, shadow=True, walk=0.0, blink=True, flip=False):
    """(x,y) = pés. Altura total ~1000*s. Cabeça: centro em y-760*s, raio 200*s."""
    cv.save(); cv.translate(x, y); cv.scale(-s if flip else s, s)
    br = 1 + 0.010 * math.sin(t * 2.2 + seed)
    bob = 6 * abs(math.sin(walk)) if walk else 0
    cv.translate(0, -bob)
    if shadow:
        cv.drawOval(skia.Rect(-175, -18 + bob, 175, 18 + bob), fill(C("#000000", 75)))
    # ---- legs + sneakers
    sw = 30 * math.sin(walk) if walk else 0
    for sx, ph in ((-1, 1), (1, -1)):
        lx = sx * 50 + ph * sw
        leg = skia.Path(); leg.addRoundRect(skia.Rect(lx - 34, -285, lx + 34, -30), 24, 24)
        _two_tone(cv, leg, JEANS, JEANS_SH, lw=4)
        shoe = skia.Path(); shoe.moveTo(lx - 42, -10); shoe.quadTo(lx - 44, -52, lx - 8, -50)
        shoe.lineTo(lx + 20, -48); shoe.quadTo(lx + 62 * (1 if sx > 0 else 0.6), -36, lx + 58, -10); shoe.close()
        _two_tone(cv, shoe, "#f4f2ee", "#cfcac2", lw=4)
        cv.drawLine(lx - 40, -14, lx + 56, -14, stroke(C("#b9b2a6"), 6))
    # ---- arms (behind torso for down poses)
    POSES = {
        "stand": ((-130, -560, -175, -330), (130, -560, 175, -330)),
        "hips": ((-130, -560, -200, -420, -115, -330), (130, -560, 200, -420, 115, -330)),
        "point": ((-130, -560, -175, -330), (130, -560, 330, -600)),
        "think": ((-130, -560, -175, -330), (130, -560, 150, -420, 60, -640)),
        "shrug": ((-130, -560, -270, -470), (130, -560, 270, -470)),
        "panic": ((-130, -560, -250, -800), (130, -560, 250, -800)),
        "wave": ((-130, -560, -175, -330), (130, -560, 270, -820)),
        "phone": ((-130, -560, -175, -330), (130, -560, 160, -420, 70, -540)),
        "talk": ((-130, -560, -175, -330), (130, -560, 250, -470)),
    }
    arms = POSES.get(pose, POSES["stand"])
    if pose == "wave":
        arms = (arms[0], (130, -560, 270 + 28 * math.sin(t * 9), -820))
    if pose == "talk":
        arms = (arms[0], (130, -560, 250 + 15 * math.sin(t * 3), -470 - 20 * math.sin(t * 4)))

    def arm(a):
        pts = [(a[i], a[i + 1]) for i in range(0, len(a), 2)]
        pth = skia.Path(); pth.moveTo(*pts[0])
        if len(pts) == 3:
            pth.quadTo(*pts[1], *pts[2])
        else:
            pth.lineTo(*pts[1])
        cv.drawPath(pth, stroke(C(LINE), 66)); cv.drawPath(pth, stroke(C(HOOD_SH), 58))
        cv.drawPath(pth, stroke(C(HOOD), 44))
        hx, hy = pts[-1]
        cuff = skia.Path(); cuff.addCircle(hx, hy, 31); cv.drawPath(cuff, fill(C(HOOD_SH))); cv.drawPath(cuff, stroke(C(LINE), 4))
        hand = skia.Path(); hand.addOval(skia.Rect(hx - 27, hy - 4, hx + 27, hy + 46))
        _two_tone(cv, hand, SKIN, SKIN_SH, lw=4, shade_off=(8, 8))
        th = skia.Path(); th.addOval(skia.Rect(hx + 12, hy, hx + 34, hy + 28)); _two_tone(cv, th, SKIN, SKIN_SH, lw=3.5, shade_off=(5, 5))
        if pose == "phone" and hx > 0:
            ph = skia.Path(); ph.addRoundRect(skia.Rect(hx - 30, hy - 60, hx + 10, hy + 20), 8, 8)
            cv.drawPath(ph, fill(C("#1d1f24"))); cv.drawPath(ph, stroke(C(LINE), 3))
            cv.drawRoundRect(skia.Rect(hx - 26, hy - 55, hx + 6, hy + 14), 5, 5, fill(C("#8fd3ff", 200)))

    front = pose in ("phone", "think", "hips")
    up = [a for a in arms if a[-1] < -560 or (front and a[0] > 0)]
    down = [a for a in arms if a not in up]
    for a in down:
        arm(a)
    # ---- torso (hoodie)
    cv.save(); cv.translate(0, -290); cv.scale(1, br); cv.translate(0, 290)
    body = skia.Path(); body.moveTo(-118, -600); body.cubicTo(-150, -560, -158, -420, -150, -300)
    body.quadTo(-152, -262, -112, -258); body.lineTo(112, -258); body.quadTo(152, -262, 150, -300)
    body.cubicTo(158, -420, 150, -560, 118, -600); body.close()
    _two_tone(cv, body, HOOD, HOOD_SH, hi=HOOD_HI, lw=5, shade_off=(40, 30))
    # pocket + hem + drawstrings
    pk = skia.Path(); pk.moveTo(-80, -370); pk.lineTo(80, -370); pk.lineTo(98, -300); pk.lineTo(-98, -300); pk.close()
    cv.drawPath(pk, fill(C(HOOD_SH, 120))); cv.drawPath(pk, stroke(C(LINE, 160), 3.5))
    cv.drawLine(-140, -290, 140, -290, stroke(C(HOOD_SH), 10))
    for sx in (-1, 1):
        cv.drawLine(sx * 28, -575, sx * 34, -470, stroke(C("#f4f2ee"), 7))
        cv.drawCircle(sx * 34, -466, 7, fill(C("#d8d2c8")))
    # hood collar behind neck
    col = skia.Path(); col.moveTo(-110, -600); col.quadTo(0, -540, 110, -600); col.quadTo(0, -650, -110, -600); col.close()
    cv.drawPath(col, fill(C(HOOD_SH))); cv.drawPath(col, stroke(C(LINE), 4))
    cv.restore()
    for a in up:
        arm(a)
    # ---- head
    hy = -770 * br
    R = 200
    neck = skia.Path(); neck.addRoundRect(skia.Rect(-38, hy + R - 60, 38, hy + R + 30), 18, 18)
    _two_tone(cv, neck, SKIN_SH, "#bf7d58", lw=3.5)
    for sx in (-1, 1):
        ear = skia.Path(); ear.addOval(skia.Rect(sx * R - 34 - sx * 6, hy - 18, sx * R + 26 - sx * 6, hy + 52))
        _two_tone(cv, ear, SKIN, SKIN_SH, lw=4, shade_off=(8, 8))
    head = skia.Path(); head.addOval(skia.Rect(-R, hy - R * 0.98, R, hy + R * 0.98))
    _two_tone(cv, head, SKIN, SKIN_SH, hi=SKIN_HI, lw=5, shade_off=(46, 40))
    if rim_a:
        rp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=9)
        rp.setShader(skia.GradientShader.MakeLinear([skia.Point(R, hy - R * 0.4), skia.Point(0, hy + R)], [C(rim, rim_a), C(rim, 0)]))
        cv.drawArc(skia.Rect(-R + 6, hy - R + 6, R - 6, hy + R - 6), -60, 110, False, rp)
    # hair with swoosh fringe
    hp = skia.Path(); hp.moveTo(-R - 6, hy - 20)
    hp.cubicTo(-R - 20, hy - R * 1.25, R * 0.4, hy - R * 1.45, R + 8, hy - 50)
    hp.cubicTo(R * 0.95, hy - R * 0.72, R * 0.55, hy - R * 0.9, R * 0.25, hy - R * 0.74)
    hp.cubicTo(R * 0.05, hy - R * 0.56, -R * 0.35, hy - R * 0.7, -R * 0.55, hy - R * 0.62)
    hp.cubicTo(-R * 0.8, hy - R * 0.55, -R * 0.95, hy - R * 0.3, -R - 6, hy - 20); hp.close()
    _two_tone(cv, hp, HAIR, "#24150e", hi=HAIR_HI, lw=5, shade_off=(16, 14))
    hl = skia.Path(); hl.moveTo(-R * 0.35, hy - R * 0.95); hl.quadTo(R * 0.1, hy - R * 1.1, R * 0.55, hy - R * 0.92)
    cv.drawPath(hl, stroke(C(HAIR_HI, 200), 10))
    # face
    lx = look * 28
    ey = hy + 18
    bl = blink and ((t + seed * 1.7) % 3.7) < 0.1
    ink = C(LINE)
    for sx in (-1, 1):
        cv.drawOval(skia.Rect(sx * 105 - 30, ey + 52, sx * 105 + 30, ey + 76), fill(C("#f08e7e", 90)))
    for sx in (-1, 1):
        ex = sx * 66 + lx
        if expr == "shock":
            e = skia.Path(); e.addOval(skia.Rect(ex - 30, ey - 34, ex + 30, ey + 34)); cv.drawPath(e, fill(C("#ffffff"))); cv.drawPath(e, stroke(ink, 4.5))
            cv.drawCircle(ex + lx * 0.4, ey + 2, 12, fill(ink))
        elif bl or expr in ("happy", "laugh", "closed"):
            cv.drawArc(skia.Rect(ex - 20, ey - 12, ex + 20, ey + 14), 200 if expr in ("happy", "laugh") else 20, 140, False, stroke(ink, 7))
        else:
            cv.drawOval(skia.Rect(ex - 13, ey - 17, ex + 13, ey + 17), fill(ink))
            cv.drawCircle(ex + 5, ey - 7, 5, fill(C("#ffffff", 230)))
            if expr in ("tired", "skeptic") and (sx == -1 or expr == "tired"):
                cv.drawRect(skia.Rect(ex - 18, ey - 22, ex + 18, ey - 2), fill(C(SKIN)))
                cv.drawLine(ex - 17, ey - 2, ex + 17, ey - 2, stroke(ink, 5))
    B = {"neutral": (-56, 0), "angry": (-46, -18), "worried": (-58, 16), "shock": (-82, 6), "happy": (-60, 0),
         "laugh": (-62, 0), "skeptic": (-52, 0), "sad": (-54, 16), "tired": (-50, 4), "closed": (-54, 0), "smug": (-56, -6)}
    bdy, tilt = B.get(expr, B["neutral"])
    for sx in (-1, 1):
        dy = -14 if (expr == "skeptic" and sx == 1) else 0
        bp = skia.Path(); bp.moveTo(sx * 36 + lx, ey + bdy - tilt + dy)
        bp.quadTo(sx * 64 + lx, ey + bdy - 8 + dy - tilt * 0.3, sx * 92 + lx, ey + bdy + dy)
        cv.drawPath(bp, stroke(ink, 10))
    # nose
    cv.drawArc(skia.Rect(-14 + lx * 0.5, ey + 30, 14 + lx * 0.5, ey + 52), 20, 140, False, stroke(C(SKIN_SH), 6))
    # mouth (lip sync overrides closed shapes)
    my = hy + 112
    mo = max(0.0, min(1.0, mouth_open))
    if mo > 0.08 and expr not in ("shock",):
        h = 10 + 34 * mo
        m = skia.Path(); m.addRoundRect(skia.Rect(-26, my - h * 0.35, 26, my + h * 0.65), 18, 18)
        cv.drawPath(m, fill(C("#6b2620"))); cv.drawPath(m, stroke(ink, 4.5))
        cv.save(); cv.clipPath(m, doAntiAlias=True); cv.drawOval(skia.Rect(-18, my + h * 0.3, 18, my + h * 0.9), fill(C("#e2716a"))); cv.restore()
    elif expr in ("happy", "laugh"):
        m = skia.Path(); m.moveTo(-44, my - 10); m.quadTo(0, my + 52, 44, my - 10); m.quadTo(0, my + 6, -44, my - 10); m.close()
        cv.drawPath(m, fill(C("#6b2620"))); cv.drawPath(m, stroke(ink, 4.5))
        cv.save(); cv.clipPath(m, doAntiAlias=True); cv.drawRect(skia.Rect(-44, my - 12, 44, my + 4), fill(C("#ffffff"))); cv.restore()
    elif expr == "shock":
        m = skia.Path(); m.addOval(skia.Rect(-22, my - 10, 22, my + 42)); cv.drawPath(m, fill(C("#5e1f19"))); cv.drawPath(m, stroke(ink, 4.5))
    elif expr in ("sad", "worried"):
        cv.drawArc(skia.Rect(-26, my + 2, 26, my + 30), 205, 130, False, stroke(ink, 7))
    elif expr in ("angry", "tired"):
        cv.drawLine(-24, my + 10, 24, my + 10, stroke(ink, 7))
    elif expr in ("skeptic", "smug"):
        sp = skia.Path(); sp.moveTo(-24, my + 12); sp.quadTo(6, my + 14, 28, my); cv.drawPath(sp, stroke(ink, 7))
    else:
        cv.drawArc(skia.Rect(-26, my - 16, 26, my + 12), 25, 130, False, stroke(ink, 7))
    if expr == "worried" or expr == "shock":
        sw_ = skia.Path(); sw_.moveTo(R * 0.72, hy - R * 0.2); sw_.quadTo(R * 0.86, hy + 10, R * 0.72, hy + 24); sw_.quadTo(R * 0.6, hy + 10, R * 0.72, hy - R * 0.2)
        cv.drawPath(sw_, fill(C("#9fd3f5"))); cv.drawPath(sw_, stroke(ink, 3))
    cv.restore()
