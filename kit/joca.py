"""JOCA v2 — personagem fixo. Formas orgânicas: cabeça em formato de feijão (bochechas cheias, queixo macio),
cabelo cacheado bagunçado com um topete rebelde, olhos grandes com íris e brilho, sardas, sorriso de canto,
fone de ouvido no pescoço (marca registrada), moletom largo mostarda com capuz amassado.
API: joca(cv, x, y, s, t, expr, look, pose, mouth_open, seed, rim, rim_a, shadow, walk, blink, flip, lean)"""
import math
from gfx import skia, C, fill, stroke, lin

SKIN, SKIN_SH, SKIN_HI = "#e9ad84", "#c98260", "#f8d2b4"
HAIR, HAIR_SH, HAIR_HI = "#2e1d15", "#1a100b", "#5a3a2a"
HOOD, HOOD_SH, HOOD_HI = "#e7a83a", "#c4842a", "#f7c766"
JEANS, JEANS_SH = "#33456a", "#222f4a"
PHONES, PAD = "#22252b", "#ff6b3d"
LINE = "#2b1a12"


def _tt(cv, path, base, shade, hi=None, lw=4.5, off=(30, 26), light=(-0.6, -0.8)):
    cv.drawPath(path, fill(C(base)))
    cv.save(); cv.clipPath(path, doAntiAlias=True)
    cv.drawPath(path, fill(C(shade)))
    lit = skia.Path(path); lit.offset(light[0] * off[0], light[1] * off[1])
    cv.drawPath(lit, fill(C(base)))
    b = path.computeTightBounds()
    g = skia.Paint(AntiAlias=True)
    g.setShader(skia.GradientShader.MakeLinear([skia.Point(b.left(), b.top()), skia.Point(b.right(), b.bottom())],
                                               [C(hi or "#ffffff", 70), C("#ffffff", 0), C("#000000", 35)], [0, 0.5, 1]))
    cv.drawRect(b, g)
    cv.restore()
    if lw:
        cv.drawPath(path, stroke(C(LINE), lw))


def _head_path(R, hy):
    p = skia.Path()
    p.moveTo(0, hy - R)
    p.cubicTo(R * 0.62, hy - R * 1.02, R * 0.98, hy - R * 0.62, R * 1.0, hy - R * 0.05)
    p.cubicTo(R * 1.04, hy + R * 0.55, R * 0.62, hy + R * 0.98, 0, hy + R * 0.98)
    p.cubicTo(-R * 0.62, hy + R * 0.98, -R * 1.04, hy + R * 0.55, -R * 1.0, hy - R * 0.05)
    p.cubicTo(-R * 0.98, hy - R * 0.62, -R * 0.62, hy - R * 1.02, 0, hy - R)
    p.close()
    return p


def _union(a, b):
    r = skia.Op(a, b, skia.PathOp.kUnion_PathOp)
    return r if r is not None else a


def _curl_hair(R, hy):
    blobs = [(-0.78, -0.42, 0.34), (-0.55, -0.72, 0.36), (-0.2, -0.9, 0.38), (0.18, -0.92, 0.37), (0.52, -0.76, 0.36),
             (0.8, -0.46, 0.32), (0.93, -0.12, 0.22), (-0.92, -0.1, 0.22), (0.0, -0.62, 0.42), (-0.35, -0.55, 0.3), (0.38, -0.55, 0.3)]
    p = skia.Path()
    for bx, by, br in blobs:
        q = skia.Path(); q.addCircle(bx * R, hy + by * R, br * R)
        p = _union(p, q)
    cut = skia.Path(); cut.moveTo(-R * 1.3, hy - R * 0.28)
    cut.cubicTo(-R * 0.6, hy - R * 0.62, -R * 0.1, hy - R * 0.38, R * 0.25, hy - R * 0.55)
    cut.cubicTo(R * 0.55, hy - R * 0.66, R * 0.85, hy - R * 0.42, R * 1.3, hy - R * 0.3)
    cut.lineTo(R * 1.3, hy + R * 1.4); cut.lineTo(-R * 1.3, hy + R * 1.4); cut.close()
    r = skia.Op(p, cut, skia.PathOp.kDifference_PathOp)
    p = r if r is not None else p
    for sx in (-1, 1):
        sb = skia.Path(); sb.moveTo(sx * R * 0.98, hy - R * 0.42)
        sb.cubicTo(sx * R * 1.04, hy - R * 0.2, sx * R * 1.0, hy - R * 0.02, sx * R * 0.9, hy + R * 0.08)
        sb.cubicTo(sx * R * 0.86, hy - R * 0.1, sx * R * 0.82, hy - R * 0.3, sx * R * 0.78, hy - R * 0.44); sb.close()
        p = _union(p, sb)
    return p


def joca(cv, x, y, s, t, expr="neutral", look=0.0, pose="stand", mouth_open=0.0, seed=0.0,
         rim="#ffd29a", rim_a=0, shadow=True, walk=0.0, blink=True, flip=False, lean=None):
    """(x,y)=pés. Altura ~1000*s. Cabeça centro ≈ y-770*s, raio ≈ 205*s."""
    cv.save(); cv.translate(x, y); cv.scale(-s if flip else s, s)
    br = 1 + 0.012 * math.sin(t * 2.2 + seed)
    sway = 2.2 * math.sin(t * 1.1 + seed) if lean is None else lean
    bob = 7 * abs(math.sin(walk)) if walk else 0
    if shadow:
        cv.drawOval(skia.Rect(-170, -17, 170, 17), fill(C("#000000", 75)))
    cv.translate(0, -bob)
    sw = 30 * math.sin(walk) if walk else 0
    for sx, ph in ((-1, 1), (1, -1)):
        lx = sx * 46 + ph * sw
        leg = skia.Path(); leg.moveTo(lx - 36, -300); leg.cubicTo(lx - 40, -200, lx - 34, -90, lx - 30, -40)
        leg.lineTo(lx + 30, -40); leg.cubicTo(lx + 34, -90, lx + 40, -200, lx + 36, -300); leg.close()
        _tt(cv, leg, JEANS, JEANS_SH, lw=4)
        cv.drawLine(lx - 30, -60, lx + 30, -66, stroke(C(JEANS_SH), 6))
        shoe = skia.Path(); shoe.moveTo(lx - 46, -6)
        shoe.cubicTo(lx - 52, -50, lx - 10, -62, lx + 10, -52)
        shoe.cubicTo(lx + 40, -46, lx + 70, -34, lx + 66, -6); shoe.close()
        _tt(cv, shoe, "#f7f5f0", "#cdc7bc", lw=4, off=(10, 8))
        cv.drawLine(lx - 44, -12, lx + 64, -12, stroke(C(PAD), 7))
    cv.rotate(sway)
    POSES = {
        "stand": [((-120, -560), (-158, -440), (-150, -320)), ((120, -560), (158, -440), (150, -320))],
        "hips": [((-120, -560), (-215, -455), (-120, -350)), ((120, -560), (215, -455), (120, -350))],
        "point": [((-120, -560), (-158, -440), (-150, -320)), ((120, -560), (240, -600), (345, -640))],
        "think": [((-120, -560), (-158, -440), (-150, -320)), ((120, -560), (170, -420), (70, -640))],
        "shrug": [((-120, -560), (-230, -520), (-290, -600)), ((120, -560), (230, -520), (290, -600))],
        "panic": [((-120, -560), (-230, -640), (-200, -870)), ((120, -560), (230, -640), (200, -870))],
        "wave": [((-120, -560), (-158, -440), (-150, -320)), ((120, -560), (260, -650), (280 + 30 * math.sin(t * 9), -850))],
        "phone": [((-120, -560), (-158, -440), (-150, -320)), ((120, -560), (190, -420), (95, -560))],
        "talk": [((-120, -560), (-158, -440), (-150, -320)), ((120, -560), (230, -450), (285 + 18 * math.sin(t * 3), -540 - 25 * math.sin(t * 4)))],
        "facepalm": [((-120, -560), (-158, -440), (-150, -320)), ((120, -560), (190, -520), (40, -770))],
    }
    arms = POSES.get(pose, POSES["stand"])

    def arm(a):
        (x0, y0), (x1, y1), (x2, y2) = a
        pth = skia.Path(); pth.moveTo(x0, y0); pth.quadTo(x1, y1, x2, y2)
        cv.drawPath(pth, stroke(C(LINE), 70)); cv.drawPath(pth, stroke(C(HOOD_SH), 62)); cv.drawPath(pth, stroke(C(HOOD), 46))
        cuff = skia.Path(); cuff.addOval(skia.Rect(x2 - 33, y2 - 24, x2 + 33, y2 + 24)); _tt(cv, cuff, HOOD_SH, "#a86d1f", lw=4, off=(6, 6))
        hand = skia.Path(); hand.moveTo(x2 - 26, y2 + 10)
        hand.cubicTo(x2 - 34, y2 + 60, x2 + 30, y2 + 66, x2 + 28, y2 + 14)
        hand.cubicTo(x2 + 44, y2 + 4, x2 + 46, y2 + 30, x2 + 30, y2 + 40)
        hand.close()
        _tt(cv, hand, SKIN, SKIN_SH, lw=4, off=(8, 8))
        if pose == "phone" and x2 > 0:
            ph = skia.Path(); ph.addRoundRect(skia.Rect(x2 - 34, y2 - 66, x2 + 8, y2 + 22), 9, 9)
            cv.drawPath(ph, fill(C("#1d1f24"))); cv.drawPath(ph, stroke(C(LINE), 3))
            g = lin(0, y2 - 60, 0, y2 + 16, [C("#9fe0ff", 230), C("#4a90d9", 230)])
            cv.drawRoundRect(skia.Rect(x2 - 30, y2 - 61, x2 + 4, y2 + 16), 6, 6, g)

    front = pose in ("phone", "think", "hips", "facepalm")
    up = [a for a in arms if a[2][1] < -560 or (front and a[0][0] > 0)]
    down = [a for a in arms if a not in up]
    for a in down:
        arm(a)
    cv.save(); cv.translate(0, -290); cv.scale(1, br); cv.translate(0, 290)
    body = skia.Path(); body.moveTo(-105, -600)
    body.cubicTo(-160, -585, -172, -470, -165, -360); body.cubicTo(-160, -300, -150, -265, -110, -262)
    body.cubicTo(-40, -250, 40, -250, 110, -262); body.cubicTo(150, -265, 160, -300, 165, -360)
    body.cubicTo(172, -470, 160, -585, 105, -600); body.cubicTo(40, -625, -40, -625, -105, -600); body.close()
    _tt(cv, body, HOOD, HOOD_SH, hi=HOOD_HI, lw=5, off=(48, 34))
    for fx, fy in ((-95, -470), (-60, -330), (100, -420)):
        f = skia.Path(); f.moveTo(fx, fy); f.quadTo(fx + 18, fy + 30, fx + 6, fy + 60); cv.drawPath(f, stroke(C(HOOD_SH), 5))
    pk = skia.Path(); pk.moveTo(-85, -380); pk.quadTo(0, -392, 85, -380); pk.quadTo(96, -330, 100, -300)
    pk.quadTo(0, -290, -100, -300); pk.quadTo(-96, -330, -85, -380); pk.close()
    cv.drawPath(pk, fill(C(HOOD_SH, 110))); cv.drawPath(pk, stroke(C(LINE, 170), 3.5))
    cv.drawRoundRect(skia.Rect(-150, -292, 150, -262), 14, 14, fill(C(HOOD_SH)))
    hd = skia.Path(); hd.moveTo(-120, -598); hd.cubicTo(-100, -665, 100, -665, 120, -598)
    hd.cubicTo(70, -560, -70, -560, -120, -598); hd.close()
    _tt(cv, hd, HOOD_SH, "#a86d1f", lw=4, off=(10, 10))
    for sx in (-1, 1):
        st = skia.Path(); st.moveTo(sx * 26, -568); st.quadTo(sx * 34, -520, sx * 24, -470); cv.drawPath(st, stroke(C("#fff7e8"), 7))
        cv.drawCircle(sx * 24, -466, 7.5, fill(C("#e8dcc4")))
    cv.restore()
    for a in up:
        arm(a)
    hy = -770 * br
    R = 205
    neck = skia.Path(); neck.addRoundRect(skia.Rect(-40, hy + R - 70, 40, hy + R + 30), 20, 20)
    _tt(cv, neck, SKIN_SH, "#b06e4c", lw=3.5, off=(6, 6))
    hp = skia.Path(); hp.moveTo(-92, hy + R - 18); hp.cubicTo(-86, hy + R + 52, 86, hy + R + 52, 92, hy + R - 18)
    cv.drawPath(hp, stroke(C(LINE), 26)); cv.drawPath(hp, stroke(C(PHONES), 18))
    for sx in (-1, 1):
        cup = skia.Path(); cup.addOval(skia.Rect(sx * 96 - 30, hy + R - 52, sx * 96 + 30, hy + R + 8))
        _tt(cv, cup, PHONES, "#0f1013", lw=4.5, off=(8, 8))
        pad = skia.Path(); pad.addOval(skia.Rect(sx * 96 - 18, hy + R - 40, sx * 96 + 18, hy + R - 4))
        _tt(cv, pad, PAD, "#cc4a23", lw=0, off=(5, 5))
    for sx in (-1, 1):
        ear = skia.Path(); ear.addOval(skia.Rect(sx * R - 34, hy - 14, sx * R + 30, hy + 64))
        _tt(cv, ear, SKIN, SKIN_SH, lw=4, off=(9, 9))
        cv.drawArc(skia.Rect(sx * R - 16, hy + 6, sx * R + 12, hy + 46), 60 if sx < 0 else 240, 180, False, stroke(C(SKIN_SH), 4))
    head = _head_path(R, hy)
    _tt(cv, head, SKIN, SKIN_SH, hi=SKIN_HI, lw=5, off=(44, 38))
    if rim_a:
        rp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10)
        rp.setShader(skia.GradientShader.MakeLinear([skia.Point(R, hy - R * 0.5), skia.Point(0, hy + R)], [C(rim, rim_a), C(rim, 0)]))
        cv.save(); cv.clipPath(head, doAntiAlias=True); cv.drawPath(head, rp); cv.restore()
    hair = _curl_hair(R, hy)
    _tt(cv, hair, HAIR, HAIR_SH, hi=HAIR_HI, lw=5, off=(14, 12))
    for (cx, cy) in ((-0.5, -0.78), (0.1, -0.95), (0.55, -0.72)):
        a = skia.Path(); a.addArc(skia.Rect(cx * R - 40, hy + cy * R - 30, cx * R + 40, hy + cy * R + 30), 200, 110)
        cv.drawPath(a, stroke(C(HAIR_HI, 190), 7))
    ck = skia.Path(); ck.moveTo(R * 0.05, hy - R * 1.18)
    ck.cubicTo(R * 0.3, hy - R * 1.6 + 6 * math.sin(t * 3 + seed), R * 0.55, hy - R * 1.35, R * 0.35, hy - R * 1.22)
    ck.cubicTo(R * 0.45, hy - R * 1.45, R * 0.2, hy - R * 1.45, R * 0.05, hy - R * 1.18); ck.close()
    _tt(cv, ck, HAIR, HAIR_SH, lw=4, off=(6, 6))
    lx = look * 26
    ey = hy + 16
    ink = C(LINE)
    bl = blink and ((t + seed * 1.7) % 3.7) < 0.1
    for sx in (-1, 1):
        cv.drawOval(skia.Rect(sx * 112 - 34, ey + 50, sx * 112 + 34, ey + 80), fill(C("#e8705e", 80)))
        for (fx, fy) in ((-14, 56), (2, 66), (16, 54), (6, 48)):
            cv.drawCircle(sx * 108 + fx, ey + fy, 3.2, fill(C("#9a5636", 170)))
    for sx in (-1, 1):
        ex = sx * 70 + lx
        if expr == "shock":
            e = skia.Path(); e.addOval(skia.Rect(ex - 38, ey - 44, ex + 38, ey + 40)); cv.drawPath(e, fill(C("#ffffff"))); cv.drawPath(e, stroke(ink, 4.5))
            cv.drawCircle(ex + lx * 0.35, ey, 13, fill(ink))
        elif bl or expr in ("laugh", "closed"):
            cv.drawArc(skia.Rect(ex - 26, ey - 14, ex + 26, ey + 18), 200 if expr == "laugh" else 20, 140, False, stroke(ink, 8))
        else:
            e = skia.Path(); e.addOval(skia.Rect(ex - 30, ey - 36, ex + 30, ey + 32))
            cv.drawPath(e, fill(C("#fffdf8")))
            cv.save(); cv.clipPath(e, doAntiAlias=True)
            ix, iy = ex + lx * 0.45, ey + 2
            cv.drawCircle(ix, iy, 21, fill(C("#5a3524"))); cv.drawCircle(ix, iy, 12, fill(C("#1a0f0a")))
            cv.drawCircle(ix + 8, iy - 9, 6.5, fill(C("#ffffff"))); cv.drawCircle(ix - 6, iy + 8, 3, fill(C("#ffffff", 180)))
            lid = {"tired": 0.55, "skeptic": 0.4 if sx < 0 else 0.0, "angry": 0.3, "smug": 0.35, "sad": 0.2}.get(expr, 0.0)
            if lid:
                cv.drawRect(skia.Rect(ex - 32, ey - 38, ex + 32, ey - 38 + 68 * lid), fill(C(SKIN)))
            cv.restore()
            cv.drawPath(e, stroke(ink, 4))
            ul = skia.Path(); ul.moveTo(ex - 32, ey - 4)
            ul.cubicTo(ex - 26, ey - 40 + 68 * lid, ex + 26, ey - 40 + 68 * lid, ex + 32, ey - 6)
            cv.drawPath(ul, stroke(ink, 7))
    B = {"neutral": (-62, 0), "angry": (-50, -20), "worried": (-64, 18), "shock": (-92, 6), "happy": (-66, 0), "laugh": (-66, 0),
         "skeptic": (-58, 0), "sad": (-60, 18), "tired": (-56, 6), "closed": (-60, 0), "smug": (-62, -8)}
    bdy, tilt = B.get(expr, B["neutral"])
    for sx in (-1, 1):
        dy = -18 if (expr == "skeptic" and sx == 1) else 0
        bp = skia.Path(); bp.moveTo(sx * 34 + lx, ey + bdy - tilt + dy + 4)
        bp.cubicTo(sx * 56 + lx, ey + bdy - 14 + dy - tilt * 0.4, sx * 86 + lx, ey + bdy - 10 + dy, sx * 104 + lx, ey + bdy + 2 + dy)
        cv.drawPath(bp, stroke(ink, 13))
    nz = skia.Path(); nz.moveTo(-10 + lx * 0.5, ey + 30); nz.cubicTo(-26 + lx * 0.5, ey + 62, 18 + lx * 0.5, ey + 70, 20 + lx * 0.5, ey + 52)
    cv.drawPath(nz, stroke(C(SKIN_SH), 6))
    my = hy + 118
    mo = max(0.0, min(1.0, mouth_open))
    if mo > 0.08 and expr != "shock":
        h = 12 + 40 * mo
        m = skia.Path(); m.moveTo(-34, my - 4); m.cubicTo(-30, my + h, 30, my + h, 36, my - 8); m.cubicTo(10, my + 2, -10, my + 2, -34, my - 4); m.close()
        cv.drawPath(m, fill(C("#6b2620")))
        cv.save(); cv.clipPath(m, doAntiAlias=True)
        cv.drawRect(skia.Rect(-36, my - 10, 36, my + 6), fill(C("#ffffff"))); cv.drawLine(1, my - 10, 1, my + 6, stroke(C("#6b2620"), 4))
        cv.drawOval(skia.Rect(-20, my + h * 0.55, 20, my + h + 10), fill(C("#e2716a")))
        cv.restore(); cv.drawPath(m, stroke(ink, 4.5))
    elif expr in ("happy", "laugh"):
        m = skia.Path(); m.moveTo(-58, my - 14); m.cubicTo(-46, my + 62, 46, my + 62, 60, my - 18); m.cubicTo(20, my - 2, -20, my - 2, -58, my - 14); m.close()
        cv.drawPath(m, fill(C("#6b2620")))
        cv.save(); cv.clipPath(m, doAntiAlias=True)
        cv.drawRect(skia.Rect(-60, my - 20, 60, my + 10), fill(C("#ffffff"))); cv.drawLine(1, my - 20, 1, my + 10, stroke(C("#6b2620"), 5))
        cv.drawOval(skia.Rect(-26, my + 24, 26, my + 60), fill(C("#e2716a")))
        cv.restore(); cv.drawPath(m, stroke(ink, 5))
    elif expr == "shock":
        m = skia.Path(); m.addOval(skia.Rect(-26, my - 12, 26, my + 48)); cv.drawPath(m, fill(C("#5e1f19"))); cv.drawPath(m, stroke(ink, 5))
    elif expr in ("sad", "worried"):
        m = skia.Path(); m.moveTo(-30, my + 18); m.cubicTo(-14, my - 2, 14, my - 2, 30, my + 16); cv.drawPath(m, stroke(ink, 8))
    elif expr == "angry":
        m = skia.Path(); m.moveTo(-28, my + 12); m.quadTo(0, my + 4, 28, my + 12); cv.drawPath(m, stroke(ink, 8))
    elif expr == "tired":
        cv.drawLine(-22, my + 10, 22, my + 12, stroke(ink, 7))
    else:
        m = skia.Path(); m.moveTo(-30, my + 10); m.cubicTo(-6, my + 18, 22, my + 14, 38, my - 6); cv.drawPath(m, stroke(ink, 8))
        cv.drawArc(skia.Rect(30, my - 14, 48, my + 4), 300, 120, False, stroke(ink, 4))
    if expr in ("worried", "shock"):
        sw_ = skia.Path(); sw_.moveTo(R * 0.8, hy - R * 0.35); sw_.cubicTo(R * 0.95, hy - 10, R * 0.88, hy + 22, R * 0.8, hy + 22)
        sw_.cubicTo(R * 0.72, hy + 22, R * 0.66, hy - 10, R * 0.8, hy - R * 0.35); _tt(cv, sw_, "#a8dcff", "#6fb6e6", lw=3, off=(4, 4))
    cv.restore()
