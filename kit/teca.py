"""TECA — personagem fixo do canal. Nerd desenrolado que sonha em ser o mais atlético da escola: tenta, faz coisas
bacanas, nunca consegue de primeira, é sempre o desacreditado — e sempre surpreende.
Caricatura pela silhueta e pelos detalhes (não pela cor): regata de basquete ENORME por cima de camiseta de manga longa,
bermuda alta demais, pernas finas, meião listrado até o joelho, tênis retrô gigante, faixa de suor na testa,
óculos redondos de acetato marrom translúcido presos por cordinha esportiva. Paleta sóbria: creme, marinho, cinza, marrom.
API igual ao joca(): teca(cv, x, y, s, t, expr, look, pose, mouth_open, seed, rim, rim_a, shadow, walk, blink, flip, lean)"""
import math
from gfx import skia, C, fill, stroke, lin, TF
from joca import _tt, _head_path, _curl_hair, SKIN, SKIN_SH, SKIN_HI, HAIR, HAIR_SH, HAIR_HI, LINE

JERSEY, JERSEY_SH, JERSEY_HI = "#efe6d2", "#cdbf9f", "#fffaf0"
NAVY, NAVY_SH = "#26324f", "#18203a"
TEE, TEE_SH = "#f7f7f4", "#d4d3cd"
SHORTS, SHORTS_SH = "#8b8f97", "#676b73"
SOCK, STRIPE = "#f4f2ec", "#26324f"
FRAME, FRAME_HI = "#5a3a2c", "#8a6250"


def teca(cv, x, y, s, t, expr="neutral", look=0.0, pose="stand", mouth_open=0.0, seed=0.0,
         rim="#ffd29a", rim_a=0, shadow=True, walk=0.0, blink=True, flip=False, lean=None, number="00"):
    """(x,y)=pés. Altura ~1000*s. Cabeça centro ≈ y-770*s, raio ≈ 205*s."""
    cv.save(); cv.translate(x, y); cv.scale(-s if flip else s, s)
    br = 1 + 0.012 * math.sin(t * 2.2 + seed)
    sway = 2.2 * math.sin(t * 1.1 + seed) if lean is None else lean
    bob = 7 * abs(math.sin(walk)) if walk else 0
    if shadow:
        cv.drawOval(skia.Rect(-175, -17, 175, 17), fill(C("#000000", 75)))
    cv.translate(0, -bob)
    sw = 30 * math.sin(walk) if walk else 0
    # ---- skinny legs, tube socks, big retro sneakers
    for sx, ph in ((-1, 1), (1, -1)):
        lx = sx * 44 + ph * sw
        leg = skia.Path(); leg.addRoundRect(skia.Rect(lx - 15, -260, lx + 15, -150), 14, 14)
        _tt(cv, leg, SKIN, SKIN_SH, lw=4, off=(6, 6))
        sock = skia.Path(); sock.moveTo(lx - 21, -190); sock.lineTo(lx + 21, -190); sock.lineTo(lx + 20, -40); sock.lineTo(lx - 20, -40); sock.close()
        _tt(cv, sock, SOCK, "#d6d2c8", lw=4, off=(6, 6))
        for k in (0, 1):
            cv.drawRect(skia.Rect(lx - 20, -182 + k * 18, lx + 20, -172 + k * 18), fill(C(STRIPE)))
        shoe = skia.Path(); shoe.moveTo(lx - 54, -4)
        shoe.cubicTo(lx - 62, -62, lx - 18, -74, lx + 6, -64)
        shoe.cubicTo(lx + 44, -56, lx + 84, -40, lx + 80, -4); shoe.close()
        _tt(cv, shoe, "#f7f5f0", "#cdc7bc", lw=4.5, off=(10, 8))
        cv.drawRoundRect(skia.Rect(lx - 56, -18, lx + 82, -2), 8, 8, fill(C("#d9d1c2")))
        sw2 = skia.Path(); sw2.moveTo(lx - 30, -40); sw2.quadTo(lx + 10, -26, lx + 46, -44); cv.drawPath(sw2, stroke(C(NAVY), 7))
    # ---- shorts (too high, wide legs)
    sh = skia.Path(); sh.moveTo(-118, -400); sh.lineTo(118, -400); sh.lineTo(136, -238); sh.lineTo(14, -230)
    sh.lineTo(0, -275); sh.lineTo(-14, -230); sh.lineTo(-136, -238); sh.close()
    _tt(cv, sh, SHORTS, SHORTS_SH, lw=4.5, off=(16, 12))
    for sx in (-1, 1):
        cv.drawLine(sx * 128, -290, sx * 132, -242, stroke(C(TEE), 6))
    cv.rotate(sway)
    POSES = {
        "stand": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (152, -450), (146, -330))],
        "hips": [((-118, -570), (-210, -465), (-118, -360)), ((118, -570), (210, -465), (118, -360))],
        "point": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (240, -610), (345, -650))],
        "think": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (170, -430), (70, -650))],
        "shrug": [((-118, -570), (-230, -530), (-290, -610)), ((118, -570), (230, -530), (290, -610))],
        "panic": [((-118, -570), (-230, -650), (-200, -880)), ((118, -570), (230, -650), (200, -880))],
        "wave": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (260, -660), (280 + 30 * math.sin(t * 9), -860))],
        "phone": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (190, -430), (95, -570))],
        "talk": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (230, -460), (285 + 18 * math.sin(t * 3), -550 - 25 * math.sin(t * 4)))],
        "flex": [((-118, -570), (-290, -585), (-285, -760)), ((118, -570), (290, -585), (285, -760))],
        "facepalm": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (190, -530), (40, -780))],
    }
    arms = POSES.get(pose, POSES["stand"])

    def arm(a, sweat=False):
        (x0, y0), (x1, y1), (x2, y2) = a
        pth = skia.Path(); pth.moveTo(x0, y0); pth.quadTo(x1, y1, x2, y2)
        cv.drawPath(pth, stroke(C(LINE), 40)); cv.drawPath(pth, stroke(C(TEE_SH), 33)); cv.drawPath(pth, stroke(C(TEE), 24))
        if pose == "flex":  # tiny bicep bump — the joke is it's barely there
            mx_, my_ = 0.25 * x0 + 0.5 * x1 + 0.25 * x2, 0.25 * y0 + 0.5 * y1 + 0.25 * y2 - 14
            cv.drawCircle(mx_, my_, 15, fill(C(TEE))); cv.drawArc(skia.Rect(mx_ - 15, my_ - 15, mx_ + 15, my_ + 15), 180, 180, False, stroke(C(LINE), 3))
        if sweat:
            band = skia.Path(); band.addRoundRect(skia.Rect(x2 - 22, y2 - 30, x2 + 22, y2 - 4), 8, 8)
            _tt(cv, band, NAVY, NAVY_SH, lw=3.5, off=(4, 4))
        hand = skia.Path(); hand.moveTo(x2 - 22, y2 - 4)
        hand.cubicTo(x2 - 30, y2 + 48, x2 + 26, y2 + 52, x2 + 24, y2 + 2)
        hand.cubicTo(x2 + 38, y2 - 8, x2 + 40, y2 + 18, x2 + 26, y2 + 26); hand.close()
        _tt(cv, hand, SKIN, SKIN_SH, lw=4, off=(7, 7))
        if pose == "phone" and x2 > 0:
            ph = skia.Path(); ph.addRoundRect(skia.Rect(x2 - 34, y2 - 66, x2 + 8, y2 + 22), 9, 9)
            cv.drawPath(ph, fill(C("#1d1f24"))); cv.drawPath(ph, stroke(C(LINE), 3))
            cv.drawRoundRect(skia.Rect(x2 - 30, y2 - 61, x2 + 4, y2 + 16), 6, 6, lin(0, y2 - 60, 0, y2 + 16, [C("#9fe0ff", 230), C("#4a90d9", 230)]))

    front = pose in ("phone", "think", "hips", "facepalm")
    up = [a for a in arms if a[2][1] < -570 or (front and a[0][0] > 0)]
    down = [a for a in arms if a not in up]
    for a in down:
        arm(a, sweat=a[0][0] > 0)
    # ---- oversized jersey over long-sleeve tee
    cv.save(); cv.translate(0, -300); cv.scale(1, br); cv.translate(0, 300)
    tee = skia.Path(); tee.addRoundRect(skia.Rect(-120, -612, 120, -560), 26, 26)
    _tt(cv, tee, TEE, TEE_SH, lw=4, off=(8, 8))
    jer = skia.Path(); jer.moveTo(-70, -612)
    jer.quadTo(0, -548, 70, -612)                     # V-neck
    jer.lineTo(104, -612); jer.cubicTo(100, -560, 120, -520, 162, -510)  # right armhole
    jer.cubicTo(176, -430, 180, -360, 172, -300)
    jer.cubicTo(60, -282, -60, -282, -172, -300)
    jer.cubicTo(-180, -360, -176, -430, -162, -510)
    jer.cubicTo(-120, -520, -100, -560, -104, -612); jer.close()
    _tt(cv, jer, JERSEY, JERSEY_SH, hi=JERSEY_HI, lw=5, off=(46, 34))
    trim = skia.Path(); trim.moveTo(-70, -612); trim.quadTo(0, -548, 70, -612); cv.drawPath(trim, stroke(C(NAVY), 14))
    for sx in (-1, 1):
        ah = skia.Path(); ah.moveTo(sx * 104, -612); ah.cubicTo(sx * 100, -560, sx * 120, -520, sx * 162, -510)
        cv.drawPath(ah, stroke(C(NAVY), 12))
    cv.drawLine(-168, -312, 168, -312, stroke(C(NAVY), 8))
    f = skia.Font(TF, 120); w = f.measureText(number)
    cv.drawString(number, -w / 2, -380, f, stroke(C(NAVY_SH), 10)); cv.drawString(number, -w / 2, -380, f, fill(C(NAVY)))
    for fx, fy in ((-120, -470), (110, -440), (-60, -350)):
        fo = skia.Path(); fo.moveTo(fx, fy); fo.quadTo(fx + 14, fy + 30, fx + 4, fy + 56); cv.drawPath(fo, stroke(C(JERSEY_SH), 5))
    cv.restore()
    for a in up:
        arm(a, sweat=a[0][0] > 0)
    # ---- head
    hy = -775 * br
    R = 205
    neck = skia.Path(); neck.addRoundRect(skia.Rect(-34, hy + R - 70, 34, hy + R + 30), 18, 18)
    _tt(cv, neck, SKIN_SH, "#b06e4c", lw=3.5, off=(6, 6))
    for sx in (-1, 1):
        ear = skia.Path(); ear.addOval(skia.Rect(sx * R - 34, hy - 14, sx * R + 30, hy + 64))
        _tt(cv, ear, SKIN, SKIN_SH, lw=4, off=(9, 9))
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
    # sweatband across forehead (hair puffs above it)
    band = skia.Path(); band.moveTo(-R * 1.0, hy - R * 0.5)
    band.cubicTo(-R * 0.5, hy - R * 0.74, R * 0.5, hy - R * 0.74, R * 1.0, hy - R * 0.5)
    band.lineTo(R * 1.0, hy - R * 0.3); band.cubicTo(R * 0.5, hy - R * 0.54, -R * 0.5, hy - R * 0.54, -R * 1.0, hy - R * 0.3); band.close()
    cv.save(); cv.clipPath(_head_path(R * 1.03, hy), doAntiAlias=True)
    _tt(cv, band, NAVY, NAVY_SH, lw=4.5, off=(6, 8))
    for k in range(-6, 7):
        cv.drawLine(k * 30, hy - R * 0.66 + abs(k) * 2.2, k * 30 + 4, hy - R * 0.44 + abs(k) * 2.2, stroke(C(NAVY_SH), 3))
    cv.restore()
    # ---- face
    lx = look * 24
    ey = hy + 22
    ink = C(LINE)
    bl = blink and ((t + seed * 1.7) % 3.7) < 0.1
    for sx in (-1, 1):
        cv.drawOval(skia.Rect(sx * 116 - 30, ey + 62, sx * 116 + 30, ey + 88), fill(C("#e8705e", 75)))
        for (fx, fy) in ((-12, 70), (3, 80), (16, 68)):
            cv.drawCircle(sx * 110 + fx, ey + fy, 3.2, fill(C("#9a5636", 160)))
    GX = 76   # lens centers
    GR = 64   # lens radius (eyes look a bit magnified)
    for sx in (-1, 1):
        ex = sx * GX + lx * 0.6
        if expr == "shock":
            e = skia.Path(); e.addOval(skia.Rect(ex - 40, ey - 44, ex + 40, ey + 42)); cv.drawPath(e, fill(C("#ffffff"))); cv.drawPath(e, stroke(ink, 4.5))
            cv.drawCircle(ex + lx * 0.35, ey, 13, fill(ink))
        elif bl or expr in ("laugh", "closed"):
            cv.drawArc(skia.Rect(ex - 28, ey - 14, ex + 28, ey + 18), 200 if expr == "laugh" else 20, 140, False, stroke(ink, 8))
        else:
            e = skia.Path(); e.addOval(skia.Rect(ex - 33, ey - 38, ex + 33, ey + 34))
            cv.drawPath(e, fill(C("#fffdf8")))
            cv.save(); cv.clipPath(e, doAntiAlias=True)
            ix, iy = ex + lx * 0.45, ey + 2
            cv.drawCircle(ix, iy, 23, fill(C("#5a3524"))); cv.drawCircle(ix, iy, 13, fill(C("#1a0f0a")))
            cv.drawCircle(ix + 9, iy - 10, 7, fill(C("#ffffff"))); cv.drawCircle(ix - 7, iy + 9, 3, fill(C("#ffffff", 180)))
            lid = {"tired": 0.55, "skeptic": 0.4 if sx < 0 else 0.0, "angry": 0.3, "smug": 0.35, "sad": 0.2, "determined": 0.28}.get(expr, 0.0)
            if lid:
                cv.drawRect(skia.Rect(ex - 36, ey - 40, ex + 36, ey - 40 + 72 * lid), fill(C(SKIN)))
            cv.restore()
            cv.drawPath(e, stroke(ink, 4))
            ul = skia.Path(); ul.moveTo(ex - 35, ey - 4)
            ul.cubicTo(ex - 28, ey - 42 + 72 * lid, ex + 28, ey - 42 + 72 * lid, ex + 35, ey - 6)
            cv.drawPath(ul, stroke(ink, 7))
    # glasses: round brown translucent acetate, keyhole bridge, rivet dots, sports cord
    for sx in (-1, 1):
        cx = sx * GX
        lens = skia.Path(); lens.addCircle(cx, ey, GR)
        cv.drawPath(lens, fill(C("#cfe6f2", 40)))
        gl = skia.Paint(AntiAlias=True); gl.setShader(skia.GradientShader.MakeLinear([skia.Point(cx - GR, ey - GR), skia.Point(cx + GR, ey + GR)], [C("#ffffff", 120), C("#ffffff", 0), C("#ffffff", 0)], [0, 0.35, 1]))
        cv.save(); cv.clipPath(lens, doAntiAlias=True); cv.drawRect(skia.Rect(cx - GR, ey - GR, cx + GR, ey + GR), gl)
        cv.drawLine(cx - GR * 0.55, ey - GR * 0.1, cx - GR * 0.1, ey - GR * 0.6, stroke(C("#ffffff", 170), 9)); cv.restore()
        cv.drawCircle(cx, ey, GR, stroke(C(LINE), 18)); cv.drawCircle(cx, ey, GR, stroke(C(FRAME), 13))
        cv.drawArc(skia.Rect(cx - GR, ey - GR, cx + GR, ey + GR), 200, 70, False, stroke(C(FRAME_HI), 4))
        tx = sx * (GX + GR)
        cv.drawLine(tx, ey - 10, sx * (R - 6), ey - 18, stroke(C(LINE), 13)); cv.drawLine(tx, ey - 10, sx * (R - 6), ey - 18, stroke(C(FRAME), 8))
        for d in (0, 13):
            cv.drawCircle(tx - sx * (16 + d), ey - GR * 0.55, 3, fill(C("#d9c2a8")))
    br_ = skia.Path(); br_.moveTo(-GX + GR - 2, ey - 14); br_.cubicTo(-18, ey - 40, 18, ey - 40, GX - GR + 2, ey - 14)
    cv.drawPath(br_, stroke(C(LINE), 15)); cv.drawPath(br_, stroke(C(FRAME), 10))
    B = {"neutral": (-74, 0), "angry": (-60, -20), "worried": (-76, 18), "shock": (-100, 6), "happy": (-78, 0), "laugh": (-78, 0),
         "skeptic": (-70, 0), "sad": (-72, 18), "tired": (-68, 6), "closed": (-72, 0), "smug": (-74, -8), "determined": (-64, -16)}
    bdy, tilt = B.get(expr, B["neutral"])
    for sx in (-1, 1):
        dy = -18 if (expr == "skeptic" and sx == 1) else 0
        bp = skia.Path(); bp.moveTo(sx * 34 + lx, ey + bdy - tilt + dy + 4)
        bp.cubicTo(sx * 56 + lx, ey + bdy - 14 + dy - tilt * 0.4, sx * 86 + lx, ey + bdy - 10 + dy, sx * 108 + lx, ey + bdy + 2 + dy)
        cv.drawPath(bp, stroke(ink, 13))
    nz = skia.Path(); nz.moveTo(-10 + lx * 0.5, ey + 48); nz.cubicTo(-26 + lx * 0.5, ey + 78, 18 + lx * 0.5, ey + 86, 20 + lx * 0.5, ey + 68)
    cv.drawPath(nz, stroke(C(SKIN_SH), 6))
    my = hy + 132
    mo = max(0.0, min(1.0, mouth_open))
    if mo > 0.08 and expr != "shock":
        h = 12 + 38 * mo
        m = skia.Path(); m.moveTo(-32, my - 4); m.cubicTo(-28, my + h, 28, my + h, 34, my - 8); m.cubicTo(10, my + 2, -10, my + 2, -32, my - 4); m.close()
        cv.drawPath(m, fill(C("#6b2620")))
        cv.save(); cv.clipPath(m, doAntiAlias=True)
        cv.drawRect(skia.Rect(-14, my - 10, 14, my + 10), fill(C("#ffffff"))); cv.drawLine(0, my - 10, 0, my + 10, stroke(C("#6b2620"), 3))  # big front teeth
        cv.drawOval(skia.Rect(-18, my + h * 0.55, 18, my + h + 10), fill(C("#e2716a")))
        cv.restore(); cv.drawPath(m, stroke(ink, 4.5))
    elif expr in ("happy", "laugh"):
        m = skia.Path(); m.moveTo(-56, my - 14); m.cubicTo(-44, my + 58, 44, my + 58, 58, my - 18); m.cubicTo(20, my - 2, -20, my - 2, -56, my - 14); m.close()
        cv.drawPath(m, fill(C("#6b2620")))
        cv.save(); cv.clipPath(m, doAntiAlias=True)
        cv.drawRect(skia.Rect(-20, my - 20, 20, my + 18), fill(C("#ffffff"))); cv.drawLine(0, my - 20, 0, my + 18, stroke(C("#6b2620"), 4))
        cv.drawOval(skia.Rect(-26, my + 26, 26, my + 58), fill(C("#e2716a")))
        cv.restore(); cv.drawPath(m, stroke(ink, 5))
    elif expr == "shock":
        m = skia.Path(); m.addOval(skia.Rect(-26, my - 12, 26, my + 46)); cv.drawPath(m, fill(C("#5e1f19"))); cv.drawPath(m, stroke(ink, 5))
    elif expr in ("sad", "worried"):
        m = skia.Path(); m.moveTo(-28, my + 16); m.cubicTo(-14, my - 2, 14, my - 2, 28, my + 14); cv.drawPath(m, stroke(ink, 8))
    elif expr in ("angry", "determined"):
        m = skia.Path(); m.moveTo(-28, my + 10); m.quadTo(0, my + 2, 28, my + 8); cv.drawPath(m, stroke(ink, 8))
        if expr == "determined":
            cv.drawRect(skia.Rect(-12, my + 4, 12, my + 16), fill(C("#ffffff"))); cv.drawRect(skia.Rect(-12, my + 4, 12, my + 16), stroke(ink, 3))
    elif expr == "tired":
        cv.drawLine(-22, my + 10, 22, my + 12, stroke(ink, 7))
    else:  # signature: confident half-smile + one buck tooth peeking
        m = skia.Path(); m.moveTo(-30, my + 6); m.cubicTo(-6, my + 16, 22, my + 12, 38, my - 8); cv.drawPath(m, stroke(ink, 8))
        cv.drawRect(skia.Rect(-4, my + 10, 12, my + 22), fill(C("#ffffff"))); cv.drawRect(skia.Rect(-4, my + 10, 12, my + 22), stroke(ink, 3))
    if expr in ("worried", "shock"):
        sw_ = skia.Path(); sw_.moveTo(R * 0.86, hy - R * 0.3); sw_.cubicTo(R * 1.0, hy - 6, R * 0.94, hy + 26, R * 0.86, hy + 26)
        sw_.cubicTo(R * 0.78, hy + 26, R * 0.72, hy - 6, R * 0.86, hy - R * 0.3); _tt(cv, sw_, "#a8dcff", "#6fb6e6", lw=3, off=(4, 4))
    cv.restore()
