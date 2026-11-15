"""Elenco de apoio no mesmo traço do Teca (cabeça-feijão, cel shading, contorno marrom).
pessoa(cv, x, y, s, t, look=..., ...) — (x,y)=pés, altura ~1000*s.
looks prontos em LOOKS: amigos, 'mal-encarados' (cômicos, nunca caricatura de povo), policial."""
import math
from gfx import skia, C, fill, stroke, lin, TF
from joca import _tt, _head_path, _union, LINE

SKINS = {"claro": ("#efc19c", "#cf9674", "#fbdcc4"), "medio": ("#d39a6c", "#b07850", "#e8bb92"),
         "moreno": ("#a86a43", "#84502f", "#c48a62"), "escuro": ("#6e4429", "#52301c", "#8c5a3a")}

LOOKS = {
    # amigos do Teca
    "rafa": dict(skin="moreno", hair="cap", hair_c="#1c120c", cap_c="#c8462f", top="tee", top_c="#3f7d5a", pants="#3a3f4a", tall=1.06),
    "duda": dict(skin="claro", hair="pony", hair_c="#7a4a26", top="tee", top_c="#e2b23e", pants="#2f3a55", tall=0.95, female=True),
    "biel": dict(skin="escuro", hair="short", hair_c="#120b07", top="hoodie", top_c="#8e8f98", pants="#2c2f36", beard=True, wide=1.08),
    # caras da casa (comédia, cara de mau exagerada)
    "chefe": dict(skin="medio", hair="buzz", hair_c="#1a120d", top="jacket", top_c="#2a2b30", pants="#1f2024", mustache=True, shades=True, wide=1.18, tall=1.04),
    "capanga1": dict(skin="moreno", hair="bald", top="tank", top_c="#e9e6dd", pants="#2b2d33", beard=True, wide=1.25),
    "capanga2": dict(skin="claro", hair="short", hair_c="#3a2416", top="shirt", top_c="#5b3b5e", pants="#25262b", mustache=True, shades=True, wide=1.05),
    "capanga3": dict(skin="escuro", hair="cap", hair_c="#0e0906", cap_c="#222222", top="jacket", top_c="#4a3b2c", pants="#1d1e22", wide=1.1),
    "capanga4": dict(skin="medio", hair="curly", hair_c="#20140d", top="tank", top_c="#3b3d44", pants="#2a2b30", mustache=True, wide=1.15, tall=0.94),
    # policiais (verde-oliva, simpáticos)
    "policial": dict(skin="medio", hair="police", hair_c="#1a110b", top="police", top_c="#4d5a33", pants="#3e4829", mustache=True, wide=1.08),
    "policial2": dict(skin="claro", hair="police", hair_c="#3a2416", top="police", top_c="#4d5a33", pants="#3e4829", female=True),
}


def _sh(h, k=0.78):
    c = C(h); r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))


def pessoa(cv, x, y, s, t, look="rafa", expr="neutral", pose="stand", gaze=0.0, mouth_open=0.0, seed=0.0,
           flip=False, walk=0.0, shadow=True, rim="#ffd29a", rim_a=0, lean=None, **over):
    L = dict(LOOKS[look]); L.update(over)
    SK, SK_SH, SK_HI = SKINS[L.get("skin", "medio")]
    top = L.get("top_c", "#777777"); top_sh = _sh(top); pants = L.get("pants", "#333333")
    wd = L.get("wide", 1.0); tl = L.get("tall", 1.0)
    cv.save(); cv.translate(x, y); cv.scale((-s if flip else s), s * tl)
    br = 1 + 0.012 * math.sin(t * 2.0 + seed)
    sway = 2.0 * math.sin(t * 1.0 + seed * 1.3) if lean is None else lean
    bob = 7 * abs(math.sin(walk)) if walk else 0
    if shadow:
        cv.drawOval(skia.Rect(-175 * wd, -17, 175 * wd, 17), fill(C("#000000", 75)))
    cv.translate(0, -bob)
    sw = 30 * math.sin(walk) if walk else 0
    for sx, ph in ((-1, 1), (1, -1)):
        lx = sx * 46 * wd + ph * sw
        leg = skia.Path(); leg.moveTo(lx - 40, -330); leg.cubicTo(lx - 42, -230, lx - 38, -120, lx - 36, -40)
        leg.lineTo(lx + 36, -40); leg.cubicTo(lx + 38, -120, lx + 42, -230, lx + 40, -330); leg.close()
        _tt(cv, leg, pants, _sh(pants), lw=4, off=(10, 8))
        shoe = skia.Path(); shoe.moveTo(lx - 44, -4)
        shoe.cubicTo(lx - 50, -46, lx - 12, -54, lx + 6, -48); shoe.cubicTo(lx + 34, -42, lx + 62, -30, lx + 60, -4); shoe.close()
        dark = L.get("top") in ("police", "jacket")
        _tt(cv, shoe, "#2a2420" if dark else "#efeae2", "#15110e" if dark else "#c9c1b4", lw=4, off=(8, 6))
    cv.rotate(sway)
    POSES = {
        "stand": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (152, -450), (146, -330))],
        "cross": [((-118, -570), (-60, -420), (70, -470)), ((118, -570), (60, -440), (-70, -490))],
        "point": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (240, -610), (345, -650))],
        "hips": [((-118, -570), (-210, -465), (-118, -360)), ((118, -570), (210, -465), (118, -360))],
        "wave": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (260, -660), (280 + 30 * math.sin(t * 9), -860))],
        "talk": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (230, -460), (285 + 18 * math.sin(t * 3), -550 - 25 * math.sin(t * 4)))],
        "radio": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (190, -470), (70, -690))],
        "shrug": [((-118, -570), (-230, -530), (-290, -610)), ((118, -570), (230, -530), (290, -610))],
        "panic": [((-118, -570), (-230, -650), (-200, -880)), ((118, -570), (230, -650), (200, -880))],
        "give": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (220, -500), (330, -470))],
        "cup": [((-118, -570), (-152, -450), (-146, -330)), ((118, -570), (200, -420), (110, -560))],
        "laugh": [((-118, -570), (-170, -430), (-90, -400)), ((118, -570), (170, -430), (90, -400))],
    }
    arms = POSES.get(pose, POSES["stand"])
    sleeve_short = L.get("top") in ("tee", "tank", "police_short")

    def arm(a):
        (x0, y0), (x1, y1), (x2, y2) = [(px * (wd if i == 0 else 1), py) for i, (px, py) in enumerate(a)]
        pth = skia.Path(); pth.moveTo(x0, y0); pth.quadTo(x1, y1, x2, y2)
        if L.get("top") == "tank":
            cv.drawPath(pth, stroke(C(LINE), 50)); cv.drawPath(pth, stroke(C(SK_SH), 44)); cv.drawPath(pth, stroke(C(SK), 34))
        elif sleeve_short:
            cv.drawPath(pth, stroke(C(LINE), 50)); cv.drawPath(pth, stroke(C(SK_SH), 44)); cv.drawPath(pth, stroke(C(SK), 34))
            sl = skia.Path(); sl.moveTo(x0, y0); sl.quadTo((x0 + x1) / 2, (y0 + y1) / 2, x0 + (x1 - x0) * 0.6, y0 + (y1 - y0) * 0.6)
            cv.drawPath(sl, stroke(C(LINE), 64)); cv.drawPath(sl, stroke(C(top), 56))
        else:
            cv.drawPath(pth, stroke(C(LINE), 62)); cv.drawPath(pth, stroke(C(top_sh), 54)); cv.drawPath(pth, stroke(C(top), 40))
        hand = skia.Path(); hand.moveTo(x2 - 22, y2 - 4)
        hand.cubicTo(x2 - 30, y2 + 48, x2 + 26, y2 + 52, x2 + 24, y2 + 2)
        hand.cubicTo(x2 + 38, y2 - 8, x2 + 40, y2 + 18, x2 + 26, y2 + 26); hand.close()
        _tt(cv, hand, SK, SK_SH, lw=4, off=(7, 7))
        if pose == "radio" and x2 < 100 and a[0][0] > 0:
            r = skia.Path(); r.addRoundRect(skia.Rect(x2 - 26, y2 - 70, x2 + 14, y2 + 18), 8, 8)
            cv.drawPath(r, fill(C("#1b1c20"))); cv.drawPath(r, stroke(C(LINE), 3)); cv.drawLine(x2 + 4, y2 - 70, x2 + 4, y2 - 120, stroke(C("#1b1c20"), 7))
        if pose == "cup" and a[0][0] > 0:
            cp = skia.Path(); cp.addRoundRect(skia.Rect(x2 - 22, y2 - 46, x2 + 22, y2 + 6), 6, 6)
            _tt(cv, cp, "#f4f1ea", "#cfc9bd", lw=3.5, off=(5, 5))
            for k in range(3):
                st = skia.Path(); xx = x2 - 10 + k * 10; st.moveTo(xx, y2 - 52)
                st.cubicTo(xx - 10, y2 - 70 - 6 * math.sin(t * 3 + k), xx + 10, y2 - 82, xx, y2 - 100); cv.drawPath(st, stroke(C("#ffffff", 120), 4))

    front = pose in ("cross", "radio", "cup", "laugh")
    up = [a for a in arms if a[2][1] < -570 or (front)]
    down = [a for a in arms if a not in up]
    for a in down: arm(a)
    # torso
    cv.save(); cv.translate(0, -300); cv.scale(wd, br); cv.translate(0, 300)
    jk = skia.Path(); jk.moveTo(-108, -612)
    jk.cubicTo(-158, -598, -170, -480, -164, -360); jk.cubicTo(-160, -320, -156, -300, -146, -292)
    jk.lineTo(146, -292); jk.cubicTo(156, -300, 160, -320, 164, -360)
    jk.cubicTo(170, -480, 158, -598, 108, -612); jk.cubicTo(50, -626, -50, -626, -108, -612); jk.close()
    if L.get("female"):
        jk = skia.Path(); jk.moveTo(-96, -612); jk.cubicTo(-140, -598, -146, -480, -130, -400); jk.cubicTo(-150, -340, -150, -310, -140, -292)
        jk.lineTo(140, -292); jk.cubicTo(150, -310, 150, -340, 130, -400); jk.cubicTo(146, -480, 140, -598, 96, -612); jk.cubicTo(44, -624, -44, -624, -96, -612); jk.close()
    tp = L.get("top")
    if tp == "tank":
        _tt(cv, jk, SK, SK_SH, lw=5, off=(40, 30))
        tk = skia.Path(); tk.moveTo(-62, -616); tk.quadTo(0, -560, 62, -616); tk.lineTo(80, -616)
        tk.cubicTo(96, -540, 150, -500, 160, -420); tk.cubicTo(164, -360, 156, -310, 146, -292); tk.lineTo(-146, -292)
        tk.cubicTo(-156, -310, -164, -360, -160, -420); tk.cubicTo(-150, -500, -96, -540, -80, -616); tk.close()
        _tt(cv, tk, top, top_sh, lw=5, off=(36, 28))
    else:
        _tt(cv, jk, top, top_sh, lw=5, off=(40, 30))
    if tp == "jacket":
        cv.drawLine(0, -600, 0, -296, stroke(C(LINE), 4))
        v = skia.Path(); v.moveTo(-40, -615); v.lineTo(0, -540); v.lineTo(40, -615); v.close(); cv.drawPath(v, fill(C("#d7d2c7"))); cv.drawPath(v, stroke(C(LINE), 3))
    if tp == "shirt":
        cv.drawLine(0, -580, 0, -296, stroke(C(LINE), 3))
        for k in range(5): cv.drawCircle(8, -560 + k * 55, 4, fill(C("#f3eee4")))
        for k in range(8):  # estampa de flores discreta
            cx, cy = -120 + (k * 67) % 240, -560 + (k * 113) % 250
            cv.drawCircle(cx, cy, 10, fill(C("#e8b44c", 140)))
    if tp == "hoodie":
        cv.drawPath((lambda p: (p.moveTo(-70, -612), p.quadTo(0, -560, 70, -612), p)[2])(skia.Path()), stroke(C(top_sh), 16))
        cv.drawLine(-22, -590, -26, -520, stroke(C("#e9e6dd"), 5)); cv.drawLine(22, -590, 26, -520, stroke(C("#e9e6dd"), 5))
        pk = skia.Path(); pk.addRoundRect(skia.Rect(-80, -420, 80, -340), 20, 20); cv.drawPath(pk, stroke(C(top_sh), 5))
    if tp == "police":
        cv.drawLine(0, -600, 0, -296, stroke(C(LINE), 3))
        for sx in (-1, 1):
            pk = skia.Path(); pk.addRoundRect(skia.Rect(sx * 75 - 38, -560, sx * 75 + 38, -500), 6, 6); cv.drawPath(pk, stroke(C(top_sh), 5))
        bd = skia.Path(); bd.moveTo(-95, -560); bd.lineTo(-55, -560); bd.lineTo(-55, -520); bd.quadTo(-75, -500, -95, -520); bd.close()
        _tt(cv, bd, "#e6c35a", "#b8952f", lw=3, off=(4, 4))
        cv.drawRect(skia.Rect(-150, -340, 150, -310), fill(C("#2a2a24"))); cv.drawRect(skia.Rect(-20, -342, 20, -308), fill(C("#c9b25a")))
        f = skia.Font(TF, 24); cv.drawString("POLICÍA", 40, -520, f, fill(C("#f2ead3")))
    cv.restore()
    for a in up: arm(a)
    # head
    R = 195; hy = -760 * br
    neck = skia.Path(); neck.addRoundRect(skia.Rect(-36, hy + R - 70, 36, hy + R + 30), 18, 18); _tt(cv, neck, SK_SH, _sh(SK_SH, 0.85), lw=3.5, off=(6, 6))
    for sx in (-1, 1):
        ear = skia.Path(); ear.addOval(skia.Rect(sx * R - 34, hy - 14, sx * R + 30, hy + 64)); _tt(cv, ear, SK, SK_SH, lw=4, off=(9, 9))
    head = _head_path(R, hy)
    if L.get("wide", 1) > 1.12:  # cabeção quadradão pros capangas
        head = skia.Path(); head.addRoundRect(skia.Rect(-R * 1.02, hy - R, R * 1.02, hy + R * 0.98), R * 0.6, R * 0.6)
    _tt(cv, head, SK, SK_SH, hi=SK_HI, lw=5, off=(44, 38))
    if rim_a:
        rp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10)
        rp.setShader(skia.GradientShader.MakeLinear([skia.Point(R, hy - R * 0.5), skia.Point(0, hy + R)], [C(rim, rim_a), C(rim, 0)]))
        cv.save(); cv.clipPath(head, doAntiAlias=True); cv.drawPath(head, rp); cv.restore()
    hc = L.get("hair_c", "#1a120c"); hs = L.get("hair", "short")
    if hs in ("short", "cap", "police", "buzz", "pony"):
        hp = skia.Path(); hp.moveTo(-R * 1.0, hy - R * 0.05)
        hp.cubicTo(-R * 1.02, hy - R * 0.9, -R * 0.5, hy - R * 1.12, 0, hy - R * 1.08)
        hp.cubicTo(R * 0.5, hy - R * 1.12, R * 1.02, hy - R * 0.9, R * 1.0, hy - R * 0.05)
        hp.cubicTo(R * 0.9, hy - R * 0.45, R * 0.5, hy - R * 0.62, R * 0.1, hy - R * 0.5)
        hp.cubicTo(-R * 0.3, hy - R * 0.66, -R * 0.8, hy - R * 0.5, -R * 1.0, hy - R * 0.05); hp.close()
        if hs == "buzz":
            cv.save(); cv.clipPath(head, doAntiAlias=True); cv.drawPath(hp, fill(C(hc, 170))); cv.restore()
        else:
            if hs == "pony":
                pt = skia.Path(); pt.moveTo(R * 0.6, hy - R * 0.7); pt.cubicTo(R * 1.5, hy - R * 0.6, R * 1.45, hy + R * 0.5, R * 1.15, hy + R * 0.9)
                pt.cubicTo(R * 1.05, hy + R * 0.3, R * 1.0, hy - R * 0.2, R * 0.5, hy - R * 0.4); pt.close(); _tt(cv, pt, hc, _sh(hc), lw=4.5, off=(10, 10))
            _tt(cv, hp, hc, _sh(hc), lw=4.5, off=(12, 10))
    elif hs == "curly":
        p = skia.Path()
        for bx, by, brr in ((-0.7, -0.5, 0.36), (-0.3, -0.85, 0.4), (0.15, -0.9, 0.4), (0.6, -0.65, 0.38), (0.0, -0.6, 0.42)):
            q = skia.Path(); q.addCircle(bx * R, hy + by * R, brr * R); p = _union(p, q)
        cut = skia.Path(); cut.addRect(skia.Rect(-R * 1.5, hy - R * 0.42, R * 1.5, hy + R * 1.5))
        p = skia.Op(p, cut, skia.PathOp.kDifference_PathOp) or p
        _tt(cv, p, hc, _sh(hc), lw=4.5, off=(12, 10))
    if hs == "cap":
        cp = skia.Path(); cp.moveTo(-R * 1.02, hy - R * 0.32); cp.cubicTo(-R * 1.0, hy - R * 1.15, R * 1.0, hy - R * 1.15, R * 1.02, hy - R * 0.32); cp.close()
        _tt(cv, cp, L.get("cap_c", "#333333"), _sh(L.get("cap_c", "#333333")), lw=5, off=(14, 12))
        bill = skia.Path(); bill.moveTo(-R * 1.0, hy - R * 0.36); bill.quadTo(-R * 1.55, hy - R * 0.3, -R * 1.5, hy - R * 0.18); bill.lineTo(-R * 0.8, hy - R * 0.25); bill.close()
        _tt(cv, bill, _sh(L.get("cap_c", "#333333")), _sh(L.get("cap_c", "#333333"), 0.6), lw=4, off=(6, 6))
    if hs == "police":
        cp = skia.Path(); cp.moveTo(-R * 1.06, hy - R * 0.4); cp.cubicTo(-R * 1.05, hy - R * 1.25, R * 1.05, hy - R * 1.25, R * 1.06, hy - R * 0.4); cp.close()
        _tt(cv, cp, "#4d5a33", "#3a4526", lw=5, off=(14, 12))
        bill = skia.Path(); bill.moveTo(-R * 1.06, hy - R * 0.4); bill.quadTo(0, hy - R * 0.2, R * 1.06, hy - R * 0.4); bill.lineTo(R * 0.9, hy - R * 0.52); bill.quadTo(0, hy - R * 0.38, -R * 0.9, hy - R * 0.52); bill.close()
        _tt(cv, bill, "#1f2318", "#121510", lw=4, off=(4, 4))
        bd = skia.Path(); bd.addCircle(0, hy - R * 0.75, 18); _tt(cv, bd, "#e6c35a", "#b8952f", lw=3, off=(4, 4))
    # face
    lx = gaze * 22; ey = hy + 20; ink = C(LINE)
    bl = ((t + seed * 2.3) % 4.1) < 0.1
    for sx in (-1, 1):
        ex = sx * 70 + lx * 0.6
        if L.get("shades"):
            continue
        if expr == "shock":
            e = skia.Path(); e.addOval(skia.Rect(ex - 34, ey - 38, ex + 34, ey + 36)); cv.drawPath(e, fill(C("#ffffff"))); cv.drawPath(e, stroke(ink, 4.5))
            cv.drawCircle(ex, ey, 11, fill(ink))
        elif bl or expr in ("laugh", "closed"):
            cv.drawArc(skia.Rect(ex - 24, ey - 12, ex + 24, ey + 16), 200 if expr == "laugh" else 20, 140, False, stroke(ink, 7))
        else:
            e = skia.Path(); e.addOval(skia.Rect(ex - 22, ey - 25, ex + 22, ey + 23)); cv.drawPath(e, fill(C("#fffdf8")))
            cv.save(); cv.clipPath(e, doAntiAlias=True)
            cv.drawCircle(ex + lx * 0.4, ey + 2, 15, fill(C("#3d2618"))); cv.drawCircle(ex + lx * 0.4, ey + 2, 8, fill(C("#120a06")))
            cv.drawCircle(ex + lx * 0.4 + 7, ey - 7, 5, fill(C("#ffffff")))
            lid = {"angry": 0.35, "skeptic": 0.4 if sx < 0 else 0, "tired": 0.5, "smug": 0.35}.get(expr, 0)
            if lid: cv.drawRect(skia.Rect(ex - 25, ey - 27, ex + 25, ey - 27 + 50 * lid), fill(C(SK)))
            cv.restore(); cv.drawPath(e, stroke(ink, 4))
    if L.get("shades"):
        sg = skia.Path(); sg.moveTo(-R * 0.86, ey - 26); sg.lineTo(R * 0.86, ey - 26); sg.lineTo(R * 0.8, ey + 8)
        sg.cubicTo(R * 0.7, ey + 34, R * 0.2, ey + 34, R * 0.12, ey + 6); sg.lineTo(-R * 0.12, ey + 6)
        sg.cubicTo(-R * 0.2, ey + 34, -R * 0.7, ey + 34, -R * 0.8, ey + 8); sg.close()
        cv.drawPath(sg, fill(C("#16171b"))); cv.drawPath(sg, stroke(C(LINE), 4))
        cv.drawLine(-R * 0.6, ey - 14, -R * 0.35, ey - 14, stroke(C("#ffffff", 140), 6))
    B = {"neutral": (-62, 0), "angry": (-48, -26), "worried": (-64, 18), "shock": (-86, 6), "happy": (-66, 0), "laugh": (-66, 0),
         "skeptic": (-58, 0), "sad": (-60, 18), "tired": (-56, 6), "smug": (-62, -8)}
    bdy, tilt = B.get(expr, B["neutral"])
    if L.get("shades"): bdy -= 14
    for sx in (-1, 1):
        dy = -16 if (expr == "skeptic" and sx == 1) else 0
        bp = skia.Path(); bp.moveTo(sx * 30 + lx, ey + bdy - tilt + dy + 4)
        bp.cubicTo(sx * 50 + lx, ey + bdy - 12 + dy - tilt * 0.4, sx * 76 + lx, ey + bdy - 8 + dy, sx * 98 + lx, ey + bdy + 2 + dy)
        cv.drawPath(bp, stroke(ink, 15 if wd > 1.1 else 12))
    nz = skia.Path(); nz.moveTo(-8 + lx * 0.5, ey + 44); nz.cubicTo(-30 + lx * 0.5, ey + 80, 20 + lx * 0.5, ey + 88, 22 + lx * 0.5, ey + 66)
    cv.drawPath(nz, stroke(C(SK_SH), 7))
    my = hy + 124
    if L.get("beard"):
        bd = skia.Path(); bd.moveTo(-R * 0.92, hy + R * 0.15); bd.cubicTo(-R * 0.9, hy + R * 1.05, R * 0.9, hy + R * 1.05, R * 0.92, hy + R * 0.15)
        bd.cubicTo(R * 0.6, hy + R * 0.55, R * 0.35, hy + R * 0.42, 0, hy + R * 0.48); bd.cubicTo(-R * 0.35, hy + R * 0.42, -R * 0.6, hy + R * 0.55, -R * 0.92, hy + R * 0.15); bd.close()
        cv.save(); cv.clipPath(head, doAntiAlias=True); cv.drawPath(bd, fill(C(hc if hs != "bald" else "#2a1a10", 230))); cv.restore()
    mo = max(0.0, min(1.0, mouth_open))
    if mo > 0.08 and expr != "shock":
        h = 10 + 34 * mo
        m = skia.Path(); m.moveTo(-30, my - 4); m.cubicTo(-26, my + h, 26, my + h, 32, my - 6); m.cubicTo(10, my + 2, -10, my + 2, -30, my - 4); m.close()
        cv.drawPath(m, fill(C("#5e1f19"))); cv.drawPath(m, stroke(ink, 4.5))
    elif expr in ("happy", "laugh"):
        m = skia.Path(); m.moveTo(-50, my - 12); m.cubicTo(-40, my + 52, 40, my + 52, 52, my - 16); m.cubicTo(18, my - 2, -18, my - 2, -50, my - 12); m.close()
        cv.drawPath(m, fill(C("#5e1f19")))
        cv.save(); cv.clipPath(m, doAntiAlias=True); cv.drawRect(skia.Rect(-52, my - 18, 52, my + 6), fill(C("#ffffff"))); cv.restore()
        cv.drawPath(m, stroke(ink, 5))
    elif expr == "shock":
        m = skia.Path(); m.addOval(skia.Rect(-24, my - 10, 24, my + 42)); cv.drawPath(m, fill(C("#5e1f19"))); cv.drawPath(m, stroke(ink, 5))
    elif expr in ("angry",):
        m = skia.Path(); m.moveTo(-34, my + 14); m.quadTo(0, my - 4, 34, my + 14); cv.drawPath(m, stroke(ink, 8))
    elif expr in ("sad", "worried"):
        m = skia.Path(); m.moveTo(-26, my + 14); m.cubicTo(-12, my - 2, 12, my - 2, 26, my + 12); cv.drawPath(m, stroke(ink, 7))
    elif expr == "skeptic":
        cv.drawLine(-26, my + 8, 24, my + 2, stroke(ink, 7))
    else:
        m = skia.Path(); m.moveTo(-30, my + 4); m.cubicTo(-10, my + 18, 12, my + 18, 32, my + 2); cv.drawPath(m, stroke(ink, 7))
    if L.get("mustache"):
        ms = skia.Path(); ms.moveTo(0, my - 22); ms.cubicTo(-30, my - 34, -62, my - 18, -66, my + 6); ms.cubicTo(-44, my - 6, -20, my - 4, 0, my - 10)
        ms.cubicTo(20, my - 4, 44, my - 6, 66, my + 6); ms.cubicTo(62, my - 18, 30, my - 34, 0, my - 22); ms.close()
        _tt(cv, ms, hc if hs != "bald" else "#2a1a10", "#0d0805", lw=3.5, off=(4, 4))
    cv.restore()


def mochila(cv, x, y, s, rot=0.0, col="#3b4a2f"):
    """mochila pesada (a famosa). (x,y)=centro."""
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    b = skia.Path(); b.moveTo(-110, -150); b.cubicTo(-130, -20, -125, 110, -100, 140); b.lineTo(100, 140); b.cubicTo(125, 110, 130, -20, 110, -150)
    b.cubicTo(60, -190, -60, -190, -110, -150); b.close()
    _tt(cv, b, col, _sh(col), lw=6, off=(30, 24))
    pk = skia.Path(); pk.addRoundRect(skia.Rect(-80, 10, 80, 120), 24, 24); _tt(cv, pk, _sh(col, 0.9), _sh(col, 0.7), lw=5, off=(10, 8))
    cv.drawLine(-70, 30, 70, 30, stroke(C("#c9b98a"), 5))
    for sx in (-1, 1):
        st = skia.Path(); st.moveTo(sx * 40, -168); st.cubicTo(sx * 70, -240, sx * 20, -250, 0, -200); cv.drawPath(st, stroke(C(LINE), 16)); cv.drawPath(st, stroke(C(_sh(col)), 10))
    cv.restore()
