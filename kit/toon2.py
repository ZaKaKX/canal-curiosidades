"""Original sketch-style cartoon: white round head, wobbly hand-drawn ink, capsule body, stick limbs, big expressions."""
import math
from gfx import skia, C, fill, stroke, poly

INK2 = C("#231a14")


def ink(w, seed=0, wob=1.6):
    p = stroke(INK2, w)
    p.setPathEffect(skia.DiscretePathEffect.Make(9, wob, abs(int(seed)) % 997))
    return p


def sk(cv, path, fillcol, w=6, seed=0):
    if fillcol is not None:
        cv.drawPath(path, fill(C(fillcol) if isinstance(fillcol, str) else fillcol))
    cv.drawPath(path, ink(w, seed))


OUTFITS = {
    "steward": dict(body="#27365e", trim="#f7f3ea", hat="cap"),
    "nurse": dict(body="#dfe6ee", trim="#d6372b", hat="nurse"),
    "officer": dict(body="#1b2340", trim="#e2b54b", hat="officer"),
    "sailor": dict(body="#3c5a86", trim="#f7f3ea", hat="sailor"),
}

HANDS = {
    "stand": ((-105, -150), (105, -150)),
    "hips": ((-80, -230), (80, -230)),
    "wave": ((-105, -150), (210, -520)),
    "panic": ((-200, -520), (200, -520)),
    "reach": ((-85, -760), (85, -770)),
    "baby": ((-35, -250), (40, -240)),
    "point": ((-105, -150), (220, -330)),
    "think": ((-105, -150), (30, -350)),
}


def toon2(cv, x, y, s, t, outfit="steward", expr="smile", pose="stand", look=0.0, seed=0.0, shadow=True,
          rot=0.0, walk=0.0, bun=True, tears=False):
    o = OUTFITS[outfit]
    sd = int(t * 8) % 3  # boil the line: 8 fps wobble like hand-drawn
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    br = 1 + 0.015 * math.sin(t * 2.4 + seed)
    if shadow:
        cv.drawOval(skia.Rect(-140, -16, 140, 16), fill(C("#000000", 90)))
    sw = 26 * math.sin(walk) if walk else 0
    for sx, ph in ((-1, 1), (1, -1)):
        fx = sx * 38 + ph * sw
        cv.drawPath(poly([(sx * 32, -125), (fx, -10)], close=False), ink(10, sd + sx))
        cv.drawPath(poly([(fx, -10), (fx + sx * 34, -10)], close=False), ink(12, sd))
    hl, hr = HANDS[pose]
    if pose == "wave": hr = (hr[0] + 25 * math.sin(t * 9), hr[1])
    if pose == "panic": hl = (hl[0], hl[1] + 16 * math.sin(t * 11)); hr = (hr[0], hr[1] + 16 * math.cos(t * 11))
    cv.save(); cv.translate(0, -125); cv.scale(1, br); cv.translate(0, 125)
    for sh, hd in (((-62, -300), hl), ((62, -300), hr)):
        cv.drawPath(poly([sh, hd], close=False), ink(9, sd))
    # capsule body
    body = skia.Path(); body.addRoundRect(skia.Rect(-92, -360, 92, -110), 70, 60)
    sk(cv, body, o["body"], 7, sd)
    if outfit == "steward":
        ap = skia.Path(); ap.addRoundRect(skia.Rect(-48, -300, 48, -125), 20, 20); sk(cv, ap, "#f7f3ea", 5, sd)
        sk(cv, poly([(-40, -352), (0, -318), (40, -352)]), "#f7f3ea", 5, sd)
    elif outfit == "nurse":
        cv.drawRect(skia.Rect(-9, -290, 9, -220), fill(C("#d6372b"))); cv.drawRect(skia.Rect(-32, -264, 32, -246), fill(C("#d6372b")))
        cv.drawRect(skia.Rect(-92, -200, 92, -184), fill(C("#d6372b", 200)))
    elif outfit == "officer":
        for by in (-320, -280, -240, -200):
            cv.drawCircle(0, by, 8, fill(C("#e2b54b")))
        cv.drawRect(skia.Rect(-92, -200, 92, -180), fill(C("#111522")))
    # texture hatching on body for hand-drawn feel
    for i in range(5):
        yy = -330 + i * 14
        cv.drawPath(poly([(70, yy), (84, yy + 10)], close=False), ink(3, i))
    for hd in (hl, hr):
        if hd[1] > -420:
            hp = skia.Path(); hp.addCircle(*hd, 17); sk(cv, hp, "#fbfbf6", 5, sd)
    if pose == "baby":
        bb = skia.Path(); bb.addOval(skia.Rect(-80, -300, 80, -200)); sk(cv, bb, "#f3e6cf", 6, sd)
        bh = skia.Path(); bh.addCircle(28, -268, 30); sk(cv, bh, "#ffffff", 5, sd)
        cv.drawArc(skia.Rect(14, -272, 26, -262), 200, 140, False, ink(3))
        cv.drawArc(skia.Rect(32, -272, 44, -262), 200, 140, False, ink(3))
    cv.restore()
    # head: big white circle, sits on body (no neck)
    hy = -505 * br
    R = 165
    if bun and outfit in ("steward",):
        b = skia.Path(); b.addCircle(0, hy - R - 18, 52); sk(cv, b, "#5a3320", 7, sd)
    head = skia.Path(); head.addOval(skia.Rect(-R, hy - R, R, hy + R * 0.96)); sk(cv, head, "#fcfcf8", 8, sd)
    # 3D-ish shading: warm key from top-left, cool shadow bottom-right, specular dot
    shp = skia.Paint(AntiAlias=True)
    shp.setShader(skia.GradientShader.MakeRadial(skia.Point(-R * 0.35, hy - R * 0.4), R * 1.9, [C("#ffffff", 0), C("#ffffff", 0), C("#a9b4cc", 120)], [0, 0.45, 1]))
    cv.save(); cv.clipPath(head, doAntiAlias=True); cv.drawRect(skia.Rect(-R, hy - R, R, hy + R), shp); cv.restore()
    cv.drawOval(skia.Rect(-R * 0.62, hy - R * 0.78, -R * 0.3, hy - R * 0.55), fill(C("#ffffff", 230)))
    if o["hat"] == "cap":
        hp = skia.Path(); hp.addRoundRect(skia.Rect(-120, hy - R - 2, 120, hy - R + 40), 18, 18); sk(cv, hp, "#f7f3ea", 6, sd)
        cv.drawPath(poly([(-100, hy - R + 18), (100, hy - R + 18)], close=False), ink(3, sd))
    elif o["hat"] == "nurse":
        sk(cv, poly([(-150, hy - 95), (150, hy - 95), (120, hy - 190), (-120, hy - 190)]), "#ffffff", 7, sd)
        cv.drawRect(skia.Rect(-10, hy - 180, 10, hy - 110), fill(C("#d6372b"))); cv.drawRect(skia.Rect(-30, hy - 155, 30, hy - 135), fill(C("#d6372b")))
    elif o["hat"] == "officer":
        sk(cv, poly([(-160, hy - 105), (160, hy - 105), (135, hy - 205), (-135, hy - 205)]), "#1b2340", 7, sd)
        sk(cv, poly([(-170, hy - 105), (170, hy - 105), (185, hy - 75), (-30, hy - 75)]), "#0f1322", 6, sd)
        cv.drawRect(skia.Rect(-135, hy - 125, 135, hy - 112), fill(C("#e2b54b")))
    elif o["hat"] == "sailor":
        sk(cv, poly([(-120, hy - 120), (120, hy - 120), (100, hy - 175), (-100, hy - 175)]), "#f7f3ea", 6, sd)
    # face
    lx = look * 22; ey = hy + 10
    blink = ((t + seed * 1.7) % 3.4) < 0.1
    # blush hatch
    for sx in (-1, 1):
        cv.drawOval(skia.Rect(sx * 95 - 26, ey + 40, sx * 95 + 26, ey + 66), fill(C("#f29a9a", 110)))
        for k in range(3):
            cv.drawPath(poly([(sx * 95 - 14 + k * 11, ey + 62), (sx * 95 - 6 + k * 11, ey + 46)], close=False), ink(2.5, k))
    if expr in ("wide", "shock"):
        for sx in (-1, 1):
            e = skia.Path(); e.addCircle(sx * 52 + lx, ey, 32); sk(cv, e, "#ffffff", 6, sd)
            cv.drawCircle(sx * 52 + lx * 1.4, ey + 2, 10, fill(INK2))
    elif expr in ("laugh", "joy") or blink or expr == "closed":
        for sx in (-1, 1):
            cv.drawArc(skia.Rect(sx * 52 - 24 + lx, ey - 14, sx * 52 + 24 + lx, ey + 18), 200, 140, False, ink(7, sd))
    else:
        for sx in (-1, 1):
            cv.drawCircle(sx * 52 + lx, ey, 13, fill(INK2))
    brow = {"smile": (-50, 0), "grin": (-55, 0), "worried": (-52, 14), "determined": (-42, -16), "wide": (-82, 4),
            "shock": (-85, 4), "laugh": (-56, 0), "joy": (-60, 0), "sad": (-48, 16), "closed": (-50, 0), "smug": (-50, -8)}[expr]
    for sx in (-1, 1):
        cv.drawPath(poly([(sx * 26 + lx, ey + brow[0] - brow[1]), (sx * 78 + lx, ey + brow[0])], close=False), ink(7, sd))
    my = hy + 88
    if expr in ("grin", "laugh", "joy", "smug"):
        m = skia.Path(); m.moveTo(-58, my - 14); m.quadTo(0, my + 52, 58, my - 14); m.quadTo(0, my + 6, -58, my - 14); m.close()
        sk(cv, m, "#ffffff", 6, sd)
        for tx in (-34, -12, 10, 32):
            cv.drawPath(poly([(tx, my - 4), (tx + 2, my + 22)], close=False), ink(3, tx))
    elif expr == "smile":
        cv.drawArc(skia.Rect(-34, my - 30, 34, my + 10), 25, 130, False, ink(7, sd))
    elif expr in ("wide", "shock"):
        m = skia.Path(); m.addOval(skia.Rect(-30, my - 22, 30, my + 42)); sk(cv, m, "#5e1f19", 6, sd)
    elif expr in ("worried", "sad"):
        cv.drawPath(poly([(-34, my + 12), (-12, my - 2), (12, my + 6), (34, my - 6)], close=False), ink(7, sd))
    elif expr == "determined":
        cv.drawPath(poly([(-30, my + 8), (30, my + 2)], close=False), ink(7, sd))
    else:
        cv.drawPath(poly([(-24, my + 4), (24, my + 4)], close=False), ink(7, sd))
    if tears or expr == "sad":
        for k in range(2):
            ph = (t * 1.4 + k * 0.5) % 1
            dp = skia.Path(); dp.addOval(skia.Rect(-70 - 9, ey + 30 + ph * 90, -70 + 9, ey + 52 + ph * 90)); sk(cv, dp, "#9fd3f5", 3, k)
    for sh, hd in (((-62, -300 * br - 125 * (br - 1)), hl), ((62, -300 * br), hr)):
        if hd[1] <= -420:
            cv.drawPath(poly([sh, hd], close=False), ink(9, sd))
            hp = skia.Path(); hp.addCircle(*hd, 17); sk(cv, hp, "#fbfbf6", 5, sd)
    cv.restore()
