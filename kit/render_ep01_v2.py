"""EP01 v2 — 3D inked plates + sketch characters. usage: render_ep01_v2.py timings.json a b out.mp4 scriptsdir platesdir"""
import sys, json, math, subprocess
sys.path.insert(0, sys.argv[5])
from gfx import *
from toon2 import toon2

TJ = json.load(open(sys.argv[1]))
PL = sys.argv[6]
L = {l["i"]: l for l in TJ["lines"]}
DUR = TJ["duration"]
CHUNKS = build_chunks(TJ)
CAP_Y = 1370
_IMG = {}


def img(name):
    if name not in _IMG:
        _IMG[name] = skia.Image.open(f"{PL}/{name}_ink.png")
    return _IMG[name]


SAMP = skia.SamplingOptions(skia.FilterMode.kLinear)


def plate(cv, name, z=1.0, cx=W / 2, cy=H / 2, dx=0, dy=0, sigma=0, alpha=1.0, rot=0, tint=None, scale=1.0):
    im = img(name)
    cv.save()
    cv.translate(cx + dx, cy + dy); cv.rotate(rot); cv.scale(z * scale, z * scale); cv.translate(-cx, -cy)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(alpha)
    if sigma > 0.3:
        p.setImageFilter(skia.ImageFilters.Blur(sigma, sigma))
    if tint:
        p.setColorFilter(skia.ColorFilters.Blend(C(*tint), skia.BlendMode.kMultiply))
    cv.drawImageRect(im, skia.Rect(0, 0, W, H), SAMP, p)
    cv.restore()


def ws(i, word, nth=0):
    hits = [w for w in L[i]["words"] if w["w"].strip(".,!?'\"").lower().startswith(word.lower())]
    return hits[nth]["s"]


def P(lt, d, a=1.0, b=1.08):
    return lerp(a, b, ease(lt / d))


# ---------- 2D skies / layers ----------

def sky_night(cv, T):
    sky(cv, "#050a1a", "#22335c", H); stars(cv, T, 1.0, 900); moon(cv, 830, 260, 52)


def sky_day(cv, T):
    sky(cv, "#4f8fd0", "#f1e7d2", H); sun_glow(cv, 860, 420, 560, "#fff4cf", 170)
    for i, (x, y, w) in enumerate(((220, 330, 260), (760, 220, 300), (520, 520, 220))):
        xx = (x + T * 8 * (1 + i * 0.3)) % (W + 400) - 200
        for k in range(4):
            cv.drawCircle(xx - w * 0.35 + k * w * 0.23, y - (k % 2) * 30, w * 0.22, fill(C("#ffffff", 210)))
        cv.drawRect(skia.Rect(xx - w * 0.45, y, xx + w * 0.45, y + w * 0.12), fill(C("#ffffff", 210)))


def sky_sunset(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 1000, [C("#2b3a73"), C("#8c6fa0"), C("#f6a65e"), C("#ffd79a")], [0, 0.45, 0.85, 1]))
    sun_glow(cv, 760, 900, 620, "#ffe2a8", 220); cv.drawCircle(760, 900, 70, fill(C("#fff2d0")))


def sky_storm(cv, T, flash_a=0):
    sky(cv, "#2b3240" if not flash_a else "#8a96b3", "#5d6676", H)


def sky_dawn(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, 900, [C("#5a6aa8"), C("#e7a4a0"), C("#ffd29a")], [0, 0.6, 1]))
    sun_glow(cv, 540, 700, 700, "#ffe0a6", 200)


def under_bg(cv, T):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#3fb0d8"), C("#0f5a82"), C("#031a2c")], [0, 0.45, 1]))
    rays(cv, 540, -300, T, col="#cff0ff", n=7, a=28, spread=60)


def rain(cv, T, a=110):
    for i in range(80):
        x = (i * 137 + T * 900) % (W + 200) - 100; y = (i * 291 + T * 2100) % H
        cv.drawLine(x, y, x - 26, y + 80, stroke(C("#d8e2f0", a), 3))


def deck_fg(cv, top=1560, rail=True):
    cv.drawRect(skia.Rect(0, top, W, H), lin(0, top, 0, H, [C("#9a6a3e"), C("#4e321c")]))
    for x in range(-120, W + 120, 110):
        cv.drawLine(x + 70, top, x - 50, H, stroke(C("#2a1a0e", 170), 4))
    cv.drawLine(0, top, W, top, stroke(C("#231a14"), 8))
    if rail:
        cv.drawRect(skia.Rect(0, top - 70, W, top - 52), fill(C("#f2ede0")))
        cv.drawRect(skia.Rect(0, top - 70, W, top - 52), stroke(C("#231a14"), 5))
        for x in range(18, W, 64):
            cv.drawLine(x, top - 52, x, top, stroke(C("#231a14"), 6))


def splash(cv, x, y, p, n=18, s=1.0):
    if p <= 0 or p >= 1: return
    for i in range(n):
        a = -math.pi * (0.1 + 0.8 * i / n)
        v = (300 + (i * 53) % 250) * s
        px = x + math.cos(a) * v * p; py = y + math.sin(a) * v * p + 900 * p * p * s
        r = (16 - 10 * p) * s
        cv.drawCircle(px, py, r, fill(C("#eaf7ff", 230 * (1 - p)))); cv.drawCircle(px, py, r, stroke(C("#231a14", 160 * (1 - p)), 3))


def ink_blob(cv, pts, col="#050506"):
    p = poly(pts); cv.drawPath(p, fill(C(col))); cv.drawPath(p, stroke(C("#231a14"), 5))


# ---------- scenes ----------
# plate-space anchor points (frame px) measured from renders
A = dict(crash_hit=(560, 1080), crash_dx=-460, crash_dy=330, ice_hit=(640, 1100), ice_dx=-620,
         lb_x=540, lb_y0=520, lb_y1=1180, dawn_rim=920, rescue_rim=920, prop=(310, 1240))


def s01(cv, lt, d, T):
    sky_night(cv, T)
    plate(cv, "night_titanic", P(lt, d, 1.0, 1.07), cy=820)
    deck_fg(cv, 1600)
    toon2(cv, 300, 1665, 1.15, T, expr="smile", look=0.6)


def s02(cv, lt, d, T):
    fl = 1.0 if 0.8 < lt < 0.95 or 1.05 < lt < 1.12 else 0.0
    sky_storm(cv, T, fl)
    plate(cv, "storm", P(lt, d, 1.0, 1.05), dy=6 * math.sin(T * 2))
    rain(cv, T)
    deck_fg(cv, 1600)
    toon2(cv, 540, 1680, 1.2, T, expr="worried" if lt < 1 else "shock", look=-0.5 + ease((lt - 0.8) / 0.3))
    flash(cv, fl * 0.45, "#e5ecff")


def s03(cv, lt, d, T):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#1a0f08")))
    plate(cv, "cabin", P(lt, d, 1.0, 1.06))
    toon2(cv, 560, 1670, 1.2, T, expr="grin", pose="hips")
    banner(cv, "VIOLET JESSOP", lt - 0.15, y=320)


def s04(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "liner_day", P(lt, d, 1.0, 1.1), dx=lerp(30, -30, ease(lt / d)))


def s05a(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "olympic_hero", P(lt, d, 1.0, 1.08), cy=900)
    date_stamp(cv, "1911", lt - 0.1, y=330)


def s05b(cv, lt, d, T, impact):
    ti = T - impact
    sx, sy = shake(ti, 34); cv.translate(sx, sy)
    sky_day(cv, T)
    z = 1.0 + 0.04 * ease(lt / d)
    plate(cv, "crash_sea", z)
    plate(cv, "crash_olympic", z, rot=0 if ti < 0 else -2 * eout(ti / 0.5))
    hx, hy = A["crash_hit"]
    if ti > 0:
        ink_blob(cv, [(hx - 60, hy - 50), (hx + 10, hy - 70), (hx + 70, hy - 20), (hx + 40, hy + 50), (hx - 30, hy + 60), (hx - 70, hy + 10)])
    k = ease(clamp((T - (impact - 2.6)) / 2.6)) if ti < 0 else 1.0
    bump = 18 * math.sin(clamp(ti / 0.3) * math.pi) if ti > 0 else 0
    plate(cv, "crash_warship", z, dx=lerp(A["crash_dx"], 0, k) - bump, dy=lerp(A["crash_dy"], 0, k) - bump * 0.5)
    if ti > 0:
        splash(cv, hx, hy + 30, ti / 0.9, 22, 1.0)
        explosion(cv, hx, hy, ti / 0.45, 0.3)
        flash(cv, max(0, 0.6 - ti * 3))


def s06(cv, lt, d, T):
    sx, sy = shake(lt, 16, 4); cv.translate(sx, sy)
    sky_day(cv, T)
    plate(cv, "hull_hole", P(lt, d, 1.0, 1.12), cy=760)
    for i in range(14):
        ph = (lt * 1.4 + i / 14) % 1
        cv.drawCircle(400 + i * 24, 1250 - ph * 380, 13 * (1 - ph) + 3, fill(C("#e8f6ff", 200 * (1 - ph))))


def s07(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "dock", P(lt, d, 1.0, 1.04))
    toon2(cv, lerp(250, 760, lt / d), 1580, 0.9, T, expr="grin", pose="hips", walk=T * 9, look=0.6)


def s08(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "sisters", P(lt, d, 1.0, 1.06), cx=700)
    deck_fg(cv, 1700, rail=False)
    toon2(cv, lerp(120, 560, ease(lt / d)), 1780, 0.62, T, expr="smile", pose="stand", walk=T * 9, look=0.8)


def s09(cv, lt, d, T):
    sky_sunset(cv, T)
    rays(cv, 760, 900, T, col="#fff0c8", n=10, a=34, spread=200, base=270)
    plate(cv, "unsinkable", P(lt, d, 1.0, 1.1), cy=1000)


def s10(cv, lt, d, T):
    sky_sunset(cv, T)
    plate(cv, "bow", P(lt, d, 1.0, 1.16), cx=640, cy=900)


def s11(cv, lt, d, T, impact):
    ti = T - impact
    sx, sy = shake(ti, 28); cv.translate(sx, sy)
    sky_night(cv, T)
    plate(cv, "ice_sea", 1.0)
    k = ease(clamp((T - L[11]["s"]) / max(0.1, impact - L[11]["s"]))) if ti < 0 else 1.0
    plate(cv, "ice_ship", 1.0, dx=lerp(A["ice_dx"], 0, k), rot=0 if ti < 0 else 1.5 * eout(ti / 0.6))
    date_stamp(cv, "APRIL 14, 1912", lt - 0.1, y=330, size=100)
    if ti > 0:
        hx, hy = A["ice_hit"]
        for i in range(12):
            p = ti / 1.0
            cv.drawCircle(hx + 120 * p * math.cos(i * 0.8), hy - 260 * p + 520 * p * p + i * 6, 14 * (1 - p) + 3, fill(C("#e9f6ff", 255 * (1 - clamp(p)))))
        flash(cv, max(0, 0.4 - ti * 2))


def s12(cv, lt, d, T):
    sky_night(cv, T)
    plate(cv, "lifeboat_hull", P(lt, d, 1.0, 1.04))
    y = lerp(A["lb_y0"], A["lb_y1"], ease(lt / d))
    for x in (A["lb_x"] - 300, A["lb_x"] + 300):
        cv.drawLine(x, 0, x, y - 60, stroke(C("#d9c39a"), 6))
    toon2(cv, A["lb_x"] - 60, y - 10, 0.55, T, expr="worried", look=0.3, shadow=False)
    plate(cv, "lifeboat_layer", 0.62, cx=540, cy=960, dx=A["lb_x"] - 540, dy=y - 960)
    near_sea(cv, 1640, T, "#0b1630", "#030612", 12, ca=70)


def s13a(cv, lt, d, T):
    sky_night(cv, T)
    plate(cv, "deck_night", 1.04, sigma=4)
    toon2(cv, 330, 1620, 1.05, T, expr="shock" if lt < 0.9 else "worried", look=0.8, pose="stand")
    k = eout(lt / 1.0)
    ox = lerp(1250, 830, k)
    toon2(cv, ox, 1700, 0.95, T, outfit="officer", expr="determined", pose="point", bun=False, look=-0.7)
    bx, by = ox - 230 * 0.95 + 20, 1700 - 330 * 0.95
    shape(cv, skia.Path().addOval(skia.Rect(bx - 85, by - 50, bx + 55, by + 45)), fill(C("#f3e6cf")), 6)
    cv.drawCircle(bx - 30, by - 12, 30, fill(C("#ffffff"))); cv.drawCircle(bx - 30, by - 12, 30, stroke(C("#231a14"), 5))


def s13b(cv, lt, d, T):
    sky_night(cv, T)
    plate(cv, "deck_night", P(lt, d, 1.1, 1.18), sigma=7)
    for i in range(30):
        ph = (T * 0.25 + i / 30) % 1
        cv.drawCircle((i * 97) % W, ph * H, 4, fill(C("#ffffff", 150)))
    toon2(cv, 540, 1720, 1.45, T, expr="determined", pose="baby")


def s14(cv, lt, d, T):
    sky_night(cv, T)
    plate(cv, "dark_sea", P(lt, d, 1.0, 1.05))


def s15(cv, lt, d, T):
    sky_dawn(cv, T)
    rays(cv, 540, 700, T, col="#fff0c8", n=8, a=26, spread=140, base=270)
    z = P(lt, d, 1.0, 1.05)
    plate(cv, "dawn", z)
    cv.save(); cv.clipRect(skia.Rect(0, 0, W, A["dawn_rim"]))
    toon2(cv, 500, A["dawn_rim"] + 140, 0.75, T, expr="joy", pose="baby", shadow=False)
    cv.restore()


def s16(cv, lt, d, T):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(C("#0a0405")))
    cv.drawCircle(540, 900, 900, rad(540, 900, 900, [C("#c0161c", 150 * (0.7 + 0.3 * math.sin(T * 12))), C("#000000", 0)]))
    zoom(cv, lerp(1.0, 1.4, eout(lt / d)), 540, 820)
    toon2(cv, 540, 1720, 1.75, T, expr="shock")


def s17a(cv, lt, d, T):
    sky(cv, "#170f0b", "#5e4027", H)
    for i in range(3):
        a = math.radians(-60 - i * 25 + 15 * math.sin(T * 0.8 + i)); x0 = 200 + i * 340
        p = poly([(x0, 1150), (x0 + math.cos(a - 0.05) * 1800, 1150 + math.sin(a - 0.05) * 1800), (x0 + math.cos(a + 0.05) * 1800, 1150 + math.sin(a + 0.05) * 1800)])
        pt = lin(x0, 1150, x0 + math.cos(a) * 1800, 1150 + math.sin(a) * 1800, [C("#fff2c0", 90), C("#fff2c0", 0)])
        pt.setBlendMode(skia.BlendMode.kPlus); cv.drawPath(p, pt)
    plate(cv, "tri_britannic", 1.15, dy=180, tint=("#5a4030",))
    for i in range(6):
        smoke(cv, 100 + i * 180, 1200, T + i, 1.6, "#3b2d22", 5, drift=20, alpha=140)
    date_stamp(cv, "1916", lt - 0.1, y=330)


def s17b(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "nurse_bg", 1.05, sigma=6)
    deck_fg(cv, 1600)
    toon2(cv, 540, 1680, 1.2, T, outfit="nurse", expr="grin", pose="wave")


def s18(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "britannic", P(lt, d, 1.0, 1.08), cy=900)


def s19a(cv, lt, d, T, impact):
    ti = T - impact
    sx, sy = shake(ti, 36); cv.translate(sx, sy)
    under_bg(cv, T)
    bubbles(cv, T, 25, 2)
    k = ease(clamp((T - L[19]["s"]) / max(0.1, impact - L[19]["s"]))) if ti < 0 else 1.0
    plate(cv, "hull_below", 1.0, dx=lerp(-900, 0, k), dy=-520)
    plate(cv, "mine", 1.0, dy=200 + 12 * math.sin(T * 1.5))
    if ti > 0:
        explosion(cv, 540, 820, ti / 0.8, 1.2)
        flash(cv, max(0, 0.85 - ti * 3), "#fff3d6")


def s19b(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "sink_sea", 1.0)
    k = ease(lt / d)
    plate(cv, "sink_ship", 1.0, dy=lerp(0, 160, k), rot=lerp(0, 5, k))
    plate(cv, "sink_sea", 1.0, alpha=0.0)


def s20(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "stern", 1.03)
    px, py = A["prop"]
    for dx in (0, 380):
        cv.save(); cv.translate(px + dx, py); cv.rotate(T * 420); cv.scale(0.32, 0.32); cv.translate(-W / 2, -H / 2)
        cv.drawImageRect(img("prop_layer"), skia.Rect(0, 0, W, H), SAMP); cv.restore()
    near_sea(cv, py + 140, T * 2, "#2c8fbd", "#0b3f63", 22, ca=160)
    k = ease(lt / d)
    bx = lerp(-80, px + 120, k); by = 1620 + 8 * math.sin(T * 5)
    toon2(cv, bx - 30, by + 10, 0.42, T, expr="shock", pose="panic", shadow=False)
    plate(cv, "lifeboat_layer", 0.42, cx=540, cy=960, dx=bx - 540, dy=by - 960 + 40)
    for i in range(18):
        ph = (T * 2 + i / 18) % 1
        cv.drawCircle(px + 190 + 260 * math.cos(i) * ph, py + 120 - 90 * ph, 12 * (1 - ph) + 2, fill(C("#ffffff", 200 * (1 - ph))))


def s21a(cv, lt, d, T, impact):
    ti = T - impact
    under_bg(cv, T)
    plate(cv, "hull_below", 1.25, dy=-620)
    bubbles(cv, T, 40, 5)
    y = lerp(1700, 1050, ease(clamp((T - L[21]["s"]) / max(0.1, impact - L[21]["s"])))) if ti < 0 else 1050 + 60 * eout(ti)
    toon2(cv, 540, y + 520, 0.8, T, expr="closed" if ti > 0 else "determined", pose="reach", shadow=False, rot=6 * math.sin(T * 2))
    if ti > 0:
        for i in range(5):
            a = i * 1.25 + T * 3
            cv.drawCircle(540 + math.cos(a) * 150, y - 80 + math.sin(a) * 45, 13, fill(C("#ffe066")))
        flash(cv, max(0, 0.55 - ti * 2.5))


def s21b(cv, lt, d, T):
    sky_day(cv, T)
    plate(cv, "rescue", 1.0)
    k = ease(lt / d)
    cv.save(); cv.clipRect(skia.Rect(0, 0, W, A["rescue_rim"]))
    toon2(cv, 540, lerp(A["rescue_rim"] + 700, A["rescue_rim"] + 220, k), 0.8, T, expr="closed" if k < 0.6 else "joy", pose="reach", shadow=False)
    cv.restore()


def s22(cv, lt, d, T, t1, t2, t3):
    cv.drawRect(skia.Rect(0, 0, W, H), lin(0, 0, 0, H, [C("#14213d"), C("#05070d")]))
    f = skia.Font(TF, 46)
    for i, (k, nm) in enumerate((("tri_olympic", "OLYMPIC"), ("tri_titanic", "TITANIC"), ("tri_britannic", "BRITANNIC"))):
        y = 300 + i * 280
        app = eout((T - t1 - i * 0.18) / 0.3)
        if app <= 0: continue
        cv.save(); cv.translate(lerp(-700, 0, app), 0)
        cv.save(); cv.clipRect(skia.Rect(0, y - 150, W, y + 110))
        plate(cv, k, 1.0, cy=960, dy=y - 960 + 30)
        cv.restore()
        cv.drawString(nm, 540 - f.measureText(nm) / 2, y + 100, f, fill(C("#f3e4bf")))
        if T > t2 + i * 0.2:
            p = eout((T - t2 - i * 0.2) / 0.2)
            cv.drawLine(540 - 230 * p, y - 120 * p, 540 + 230 * p, y + 60 * p, stroke(C("#e23b2e"), 22))
            cv.drawLine(540 + 230 * p, y - 120 * p, 540 - 230 * p, y + 60 * p, stroke(C("#e23b2e"), 22))
        cv.restore()
    if T > t3:
        p = eout((T - t3) / 0.35)
        cv.drawCircle(540, 1650, 520 * p, rad(540, 1650, 520 * p + 1, [C("#ffd54a", 120), C("#ffd54a", 0)]))
        toon2(cv, 540, 1900, lerp(0.2, 0.7, p), T, expr="grin", pose="hips")


def s23(cv, lt, d, T):
    sky_sunset(cv, T)
    rays(cv, 760, 900, T, n=12, a=40, spread=360, base=0)
    plate(cv, "unsinkable", 1.1, sigma=6, cy=1000)
    deck_fg(cv, 1600)
    toon2(cv, 540, 1690, 1.25, T, expr="grin", pose="hips")
    banner(cv, "MISS UNSINKABLE", lt - 0.05, y=330, size=92, bg="#1b2a4a", fg="#ffd54a")


SHOTS = []


def add(s, e, fn, *a):
    SHOTS.append((s, e, fn, a))


add(0, L[2]["s"], s01); add(L[2]["s"], L[3]["s"], s02); add(L[3]["s"], L[4]["s"], s03); add(L[4]["s"], L[5]["s"], s04)
add(L[5]["s"], ws(5, "when"), s05a); add(ws(5, "when"), L[6]["s"], s05b, ws(5, "crashed"))
add(L[6]["s"], L[7]["s"], s06); add(L[7]["s"], L[8]["s"], s07); add(L[8]["s"], L[9]["s"], s08)
add(L[9]["s"], L[10]["s"], s09); add(L[10]["s"], L[11]["s"], s10); add(L[11]["s"], L[12]["s"], s11, ws(11, "hit"))
add(L[12]["s"], L[13]["s"], s12); add(L[13]["s"], ws(13, "and"), s13a); add(ws(13, "and"), L[14]["s"], s13b)
add(L[14]["s"], L[15]["s"], s14); add(L[15]["s"], L[16]["s"], s15); add(L[16]["s"], L[17]["s"], s16)
add(L[17]["s"], ws(17, "she"), s17a); add(ws(17, "she"), L[18]["s"], s17b); add(L[18]["s"], L[19]["s"], s18)
add(L[19]["s"], ws(19, "and"), s19a, ws(19, "hit")); add(ws(19, "and"), L[20]["s"], s19b)
add(L[20]["s"], L[21]["s"], s20); add(L[21]["s"], ws(21, "and"), s21a, ws(21, "hit")); add(ws(21, "and"), L[22]["s"], s21b)
add(L[22]["s"], L[23]["s"], s22, ws(22, "three", 0), ws(22, "three", 1), ws(22, "one")); add(L[23]["s"], DUR + 0.01, s23)


def render_frame(surface, fi):
    T = fi / FPS
    cv = surface.getCanvas(); cv.clear(C("#000000"))
    for s, e, fn, a in SHOTS:
        if s <= T < e:
            cv.save(); fn(cv, T - s, e - s, T, *a); cv.restore(); break
    vignette(cv, 140)
    draw_caption(cv, CHUNKS, T, y=CAP_Y, hide_after=L[23]["s"])
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
