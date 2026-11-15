"""TECA 01 — trilha + efeitos sintetizados. uso: sfx.py timings_pN.json out.wav"""
import sys, json, os, numpy as np, soundfile as sf
TJ = json.load(open(sys.argv[1])); out = sys.argv[2]
PART = 2 if "p2" in os.path.basename(sys.argv[1]) else 1
SR = 48000; D = TJ["duration"] + 1.3; N = int(D * SR); rs = np.random.RandomState(4)
L = {l["i"]: l for l in TJ["lines"]}
t = np.arange(N) / SR
mix = np.zeros(N); mus = np.zeros(N)


def ws(i, w, n=0):
    return [x for x in L[i]["words"] if x["w"].strip(".,!?:…'\"").lower().startswith(w)][n]["s"]


def smooth(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def put(buf, at, s, g):
    i0 = int(at * SR)
    if i0 >= N: return
    n = min(len(s), N - i0); buf[i0:i0 + n] += g * s[:n]


def pluck(f, dur=0.5, bright=1.0):
    tt = np.arange(int(dur * SR)) / SR
    return sum(np.sin(2 * np.pi * f * k * tt) * (bright / k ** 1.6) * np.exp(-tt * (5 + 2 * k)) for k in range(1, 5))


def boom(at, g=0.6, f0=90, f1=28, dur=1.4):
    n = int(dur * SR); tt = np.arange(n) / SR; f = f1 + (f0 - f1) * np.exp(-tt * 4)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3) + smooth(rs.randn(n), 8) * np.exp(-tt * 10) * 0.5
    put(mix, at, s, g)


def pop(at, g=0.25, f=900):
    n = int(0.12 * SR); tt = np.arange(n) / SR
    put(mix, at, np.sin(2 * np.pi * (f + 900 * tt / 0.12) * tt) * np.exp(-tt * 40), g)


def knock(at, g=0.55):
    n = int(0.18 * SR); tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 160 * tt) + 0.6 * np.sin(2 * np.pi * 310 * tt)) * np.exp(-tt * 38) + smooth(rs.randn(n), 4) * np.exp(-tt * 70) * 0.6
    put(mix, at, s, g)


def whoosh(at, dur=0.45, g=0.2):
    n = int(dur * SR); tt = np.linspace(0, 1, n); nz = rs.randn(n); nz = nz - smooth(nz, 25)
    put(mix, at - dur * 0.7, nz * np.sin(np.pi * tt) ** 2, g)


def splash(at, g=0.5):
    n = int(1.4 * SR); tt = np.arange(n) / SR; nz = rs.randn(n)
    s = (nz - smooth(nz, 6)) * np.exp(-tt * 3.5) + smooth(rs.randn(n), 30) * np.exp(-tt * 2) * 2
    put(mix, at, s, g); boom(at, 0.3, 70, 30, 0.6)


def siren(at, dur=1.6, g=0.12):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = np.where((tt * 2.5).astype(int) % 2 == 0, 950, 700)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.6
    put(mix, at, s * np.clip(tt / 0.1, 0, 1) * np.clip((dur - tt) / 0.4, 0, 1), g)


def chime(at, g=0.2):
    n = int(2.2 * SR); tt = np.arange(n) / SR
    put(mix, at, sum(np.sin(2 * np.pi * f * tt) * a for f, a in ((880, 1), (1320, .5), (1760, .25))) * np.exp(-tt * 2.2), g)


def music(t0, t1, bpm=104, key=0, mood="fun", g=0.11):
    """trilha leve de 'pizzicato' com baixo — mood fun/tense/run"""
    beat = 60 / bpm
    prog = {"fun": [(0, 4, 7), (5, 9, 12), (7, 11, 14), (5, 9, 12)], "tense": [(0, 3, 7), (1, 4, 8), (0, 3, 7), (-1, 3, 6)],
            "run": [(0, 4, 7), (2, 5, 9), (5, 9, 12), (7, 11, 14)]}[mood]
    base = 220 * 2 ** (key / 12)
    k = 0; tt = t0
    while tt < t1:
        ch = prog[(k // 8) % 4]; step = k % 8
        div = 0.5 if mood == "run" else 1.0
        if mood != "tense" or step % 2 == 0:
            n_ = ch[[0, 1, 2, 1, 0, 2, 1, 2][step]]
            put(mus, tt, pluck(base * 2 ** (n_ / 12), 0.45 if mood != "tense" else 0.9), g * (0.8 if step % 2 else 1.0))
        if step % 4 == 0:
            put(mus, tt, pluck(base / 2 * 2 ** (ch[0] / 12), 0.9, 0.6), g * 1.2)
        if mood == "run" and step % 2 == 0:
            n = int(0.05 * SR); put(mus, tt, smooth(rs.randn(n), 2) * np.exp(-np.arange(n) / SR * 80), g * 0.5)
        tt += beat * div / 2 if mood == "run" else beat / 2; k += 1
    fade = np.clip((t - t0) / 0.3, 0, 1) * np.clip((t1 - t) / 0.4, 0, 1) * ((t >= t0) & (t < t1))
    return fade


if PART == 1:
    f1 = music(0, L[19]["s"], 104, 0, "fun"); m1 = mus.copy(); mus[:] = 0
    f2 = music(L[19]["s"], L[22]["s"], 70, -3, "tense", 0.13); m2 = mus.copy(); mus[:] = 0
    f3 = music(L[22]["s"], D, 104, 0, "fun"); m3 = mus.copy()
    mus = m1 * f1 + m2 * f2 + m3 * f3
    drone = (np.sin(2 * np.pi * 55 * t) * 0.6 + np.sin(2 * np.pi * 58.3 * t) * 0.4) * ((t > L[19]["s"]) & (t < L[22]["s"])) * 0.05
    mix += drone
    pop(ws(1, "atlético"), .2, 1400); pop(ws(4, "spoiler"), .3); pop(L[5]["s"], .25); pop(L[6]["s"], .2)
    pop(ws(9, "sinal"), .2, 1100); pop(ws(9, "mapa"), .2, 1200); pop(ws(9, "ideia"), .2, 1300)
    knock(ws(15, "porta")); knock(ws(15, "porta") + 0.25)
    pop(ws(17, "tito"), .25); whoosh(L[19]["s"], .5, .2); boom(L[19]["s"], .35, 80, 30, 1.2)
    boom(ws(21, "séria"), .8, 100, 24, 2.0); chime(L[22]["s"] + 0.1)
else:
    f1 = music(0, L[7]["s"], 96, 0, "tense", 0.12); m1 = mus.copy(); mus[:] = 0
    f2 = music(L[8]["s"], L[13]["s"], 150, 2, "run", 0.12); m2 = mus.copy(); mus[:] = 0
    f3 = music(L[16]["s"], D, 104, 0, "fun"); m3 = mus.copy()
    mus = m1 * f1 + m2 * f2 + m3 * f3
    pop(L[1]["s"], .25); pop(ws(2, "tito"), .25)
    boom(ws(3, "mochila") + 0.5, .35, 90, 50, 0.4)
    pop(ws(3, "abre"), .25); pop(ws(3, "para"), .25)
    boom(L[7]["s"], .7, 110, 26, 1.6); siren(L[7]["s"] + 0.05, 1.3, .1)
    boom(ws(9, "mochila") + 0.2, .5, 80, 40, 0.5); whoosh(ws(9, "corri"), .4, .25)
    boom(ws(11, "tropecei") + 0.25, .4, 100, 40, 0.5); splash(ws(12, "caí"))
    siren(ws(13, "viatura"), 2.0, .07); pop(ws(15, "brasil"), .2, 1400); pop(ws(15, "neymar"), .2, 1500)
    siren(L[17]["s"], 2.0, .06); pop(ws(18, "mochila"), .2); pop(ws(18, "caminhão"), .2)
    chime(L[23]["s"] + 0.6)
if os.environ.get("MUSIC", "0") == "1": mix += mus
mix *= np.clip((D - t) / 1.0, 0, 1)
mix = mix / max(1e-6, np.abs(mix).max()) * 0.5
sf.write(out, mix.astype(np.float32), SR)
print("ok", PART)
