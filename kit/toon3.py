"""Soft-shaded flat cartoon (v3): big round colored head, small dot eyes, thin brows, simple hair cap,
no heavy ink — soft gradient shading from a key light, rim light, contact shadow. Original design."""
import math
from gfx import skia, C, fill, stroke, poly, lin, rad

SKINS = {"peach": ("#f6c9a4", "#d99a76"), "tan": ("#e0a77c", "#b97a52"), "brown": ("#a86d4a", "#7c4a30"),
         "light": ("#fbdcc4", "#e2b296")}


def _shade_circle(cv, x, y, r, base, dark, key=(-0.45, -0.5)):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x + key[0] * r, y + key[1] * r), r * 1.9,
                                               [C(base), C(base), C(dark)], [0, 0.42, 1]))
    cv.drawCircle(x, y, r, p)


def toon3(cv, x, y, s, t, skin="peach", hair="#2b2320", shirt="#e9e4da", shirt_dark="#b9b2a6", pants="#3a3f4a",
          expr="neutral", look=0.0, pose="stand", seed=0.0, hairstyle="cap", rim="#ffd29a", rim_a=120,
          shadow=True, outline="#2a1f1a", hat=None, extra=None):
    """(x,y) = feet. Figure ~ 980*s tall. Head radius 190*s."""
    base, dark = SKINS.get(skin, SKINS["peach"])
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    br = 1 + 0.012 * math.sin(t * 2.2 + seed)
    ow = 4
    if shadow:
        cv.drawOval(skia.Rect(-170, -20, 170, 20), fill(C("#000000", 70)))
    # legs
    for sx in (-1, 1):
        cv.drawRoundRect(skia.Rect(sx * 52 - 30, -300, sx * 52 + 30, -10), 26, 26, fill(C(pants)))
        cv.drawOval(skia.Rect(sx * 52 - 42, -36, sx * 52 + 46, 6), fill(C("#22201e")))
    # torso (rounded trapezoid)
    cv.save(); cv.translate(0, -300); cv.scale(1, br); cv.translate(0, 300)
    body = skia.Path(); body.moveTo(-120, -640); body.lineTo(120, -640); body.quadTo(150, -470, 135, -290)
    body.lineTo(-135, -290); body.quadTo(-150, -470, -120, -640); body.close()
    bp = lin(-140, 0, 140, 0, [C(shirt), C(shirt), C(shirt_dark)], [0, 0.55, 1])
    cv.drawPath(body, bp); cv.drawPath(body, stroke(C(outline, 120), ow))
    # arms (sleeves as soft capsules)
    poses = {"stand": [(-130, -620, -175, -320), (130, -620, 175, -320)],
             "point": [(-130, -620, -175, -320), (130, -620, 330, -560)],
             "think": [(-130, -620, -175, -320), (130, -620, 60, -700)],
             "shrug": [(-130, -620, -260, -520), (130, -620, 260, -520)],
             "up": [(-130, -620, -230, -880), (130, -620, 230, -880)],
             "wave": [(-130, -620, -175, -320), (130, -620, 260 + 20 * math.sin(t * 8), -860)]}
    for (x0, y0, x1, y1) in poses.get(pose, poses["stand"]):
        a = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=62, StrokeCap=skia.Paint.kRound_Cap)
        a.setColor(C(shirt_dark)); cv.drawLine(x0, y0, x1, y1, a)
        a.setStrokeWidth(52); a.setColor(C(shirt)); cv.drawLine(x0, y0, x1, y1, a)
        _shade_circle(cv, x1, y1 + 6, 30, base, dark)
    cv.restore()
    # head
    hy = -840 * br
    R = 190
    cv.drawCircle(0, hy + R * 0.92, 40, fill(C(dark)))  # neck
    _shade_circle(cv, 0, hy, R, base, dark)
    # rim light
    rp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10)
    rp.setShader(skia.GradientShader.MakeLinear([skia.Point(R, hy - R), skia.Point(-R * 0.2, hy)], [C(rim, rim_a), C(rim, 0)]))
    cv.drawArc(skia.Rect(-R + 5, hy - R + 5, R - 5, hy + R - 5), -80, 120, False, rp)
    cv.drawCircle(0, hy, R, stroke(C(outline, 90), ow))
    # ears
    for sx in (-1, 1):
        _shade_circle(cv, sx * (R - 8), hy + 20, 28, base, dark)
    # hair
    if hairstyle == "cap":
        hp = skia.Path(); hp.moveTo(-R - 4, hy - 10)
        hp.cubicTo(-R - 10, hy - R * 1.35, R + 10, hy - R * 1.35, R + 4, hy - 10)
        hp.cubicTo(R * 0.8, hy - R * 0.55, R * 0.2, hy - R * 0.62, -R * 0.1, hy - R * 0.5)
        hp.cubicTo(-R * 0.5, hy - R * 0.62, -R * 0.85, hy - R * 0.5, -R - 4, hy - 10); hp.close()
        cv.drawPath(hp, lin(0, hy - R * 1.3, 0, hy, [C("#4a3b33") if hair == "#2b2320" else C(hair), C(hair)]))
        cv.drawPath(hp, stroke(C(outline, 90), ow))
    elif hairstyle == "bun":
        cv.drawCircle(0, hy - R - 30, 70, fill(C(hair)))
        hp = skia.Path(); hp.moveTo(-R - 4, hy); hp.cubicTo(-R - 10, hy - R * 1.35, R + 10, hy - R * 1.35, R + 4, hy)
        hp.quadTo(R * 0.5, hy - R * 0.6, 0, hy - R * 0.55); hp.quadTo(-R * 0.5, hy - R * 0.6, -R - 4, hy); hp.close()
        cv.drawPath(hp, fill(C(hair))); cv.drawPath(hp, stroke(C(outline, 90), ow))
    if hat == "officer":
        cv.drawPath(poly([(-R - 10, hy - 95), (R + 10, hy - 95), (R - 15, hy - 230), (-R + 15, hy - 230)]), fill(C("#1b2340")))
        cv.drawRect(skia.Rect(-R - 10, hy - 115, R + 10, hy - 95), fill(C("#e2b54b")))
        cv.drawPath(poly([(-R - 20, hy - 95), (R + 20, hy - 95), (R + 40, hy - 65), (-20, hy - 65)]), fill(C("#0f1322")))
    elif hat == "nurse":
        cv.drawPath(poly([(-R + 10, hy - 110), (R - 10, hy - 110), (R - 40, hy - 215), (-R + 40, hy - 215)]), fill(C("#ffffff")))
        cv.drawRect(skia.Rect(-10, hy - 200, 10, hy - 125), fill(C("#d23a2f"))); cv.drawRect(skia.Rect(-32, hy - 172, 32, hy - 152), fill(C("#d23a2f")))
    elif hat == "maid":
        cv.drawRoundRect(skia.Rect(-120, hy - R - 5, 120, hy - R + 35), 16, 16, fill(C("#fbf8ef")))
    # face
    lx = look * 26
    ey = hy + 10
    blink = ((t + seed * 1.7) % 3.6) < 0.1
    ink = C("#2a1f1a")
    for sx in (-1, 1):
        ex = sx * 58 + lx
        if expr == "shock":
            cv.drawCircle(ex, ey, 26, fill(C("#ffffff"))); cv.drawCircle(ex, ey, 26, stroke(ink, 4)); cv.drawCircle(ex + lx * 0.3, ey, 10, fill(ink))
        elif blink or expr in ("closed", "happy"):
            cv.drawArc(skia.Rect(ex - 16, ey - 10, ex + 16, ey + 10), 200 if expr == "happy" else 20, 140, False, stroke(ink, 6))
        else:
            cv.drawCircle(ex, ey, 11, fill(ink))
            cv.drawCircle(ex + 4, ey - 4, 3.5, fill(C("#ffffff", 200)))
    brows = {"neutral": (-48, 0), "angry": (-40, -16), "worried": (-50, 14), "shock": (-70, 4), "happy": (-52, 0),
             "skeptic": (-44, 0), "sad": (-46, 14), "closed": (-46, 0)}
    bdy, tilt = brows.get(expr, brows["neutral"])
    for sx in (-1, 1):
        dy = (-10 if (expr == "skeptic" and sx == 1) else 0)
        cv.drawLine(sx * 30 + lx, ey + bdy - tilt + dy, sx * 82 + lx, ey + bdy + dy, stroke(ink, 7))
    my = hy + 85
    if expr == "happy":
        m = skia.Path(); m.addArc(skia.Rect(-36, my - 26, 36, my + 18), 10, 160); cv.drawPath(m, fill(C("#7a2b22"))); cv.drawPath(m, stroke(ink, 4))
    elif expr == "shock":
        cv.drawOval(skia.Rect(-20, my - 10, 20, my + 30), fill(C("#5e1f19")))
    elif expr in ("sad", "worried"):
        cv.drawArc(skia.Rect(-24, my, 24, my + 24), 200, 140, False, stroke(ink, 6))
    elif expr == "angry":
        cv.drawLine(-22, my + 6, 22, my + 6, stroke(ink, 6))
    elif expr == "skeptic":
        cv.drawLine(-20, my + 8, 22, my + 2, stroke(ink, 6))
    else:
        cv.drawArc(skia.Rect(-22, my - 14, 22, my + 8), 30, 120, False, stroke(ink, 6))
    cv.restore()
