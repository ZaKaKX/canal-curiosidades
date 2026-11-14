"""EP08 (PT-BR) sound bed: drone, harbor air, creaks/drips, burst + rumbling wave, twist hit, cold wind, final chime. usage: sfx.py timings.json out.wav"""
import sys, json, numpy as np, soundfile as sf
TJ = json.load(open(sys.argv[1])); out = sys.argv[2]
SR = 48000; D = TJ["duration"]; N = int(D * SR); rs = np.random.RandomState(7)
L = {l["i"]: l for l in TJ["lines"]}
def ws(i, w, n=0):
    cl = lambda x: x["w"].strip(".,!?'").lower()
    hits = [x for x in L[i]["words"] if cl(x) == w] or [x for x in L[i]["words"] if cl(x).startswith(w)]
    return hits[n]["s"]
t = np.arange(N) / SR
def smooth(x, k): return np.convolve(x, np.ones(k) / k, mode="same")
mix = np.zeros(N)
twist = L[13]["s"]

# ambient drone (mysterious, D minor-ish)
drone = sum(np.sin(2*np.pi*f*t + p) * a for f, a, p in ((73.4, .5, 0), (110, .3, 1), (146.8, .2, 2), (174.6, .08, 3)))
drone *= 0.6 + 0.4 * np.sin(2*np.pi*0.05*t)
air = smooth(rs.randn(N), 80) * (0.6 + 0.4*np.sin(2*np.pi*0.1*t))
mix += (0.03*drone + 0.04*air) * np.clip(t/1.0, 0, 1) * np.clip((D - t)/1.5, 0, 1)

def seg(at, dur):
    i0 = max(0, int(at*SR)); n = max(0, min(int(dur*SR), N-i0)); return i0, n
def env_span(a, b, fade=0.4):
    e = np.zeros(N); i0, n = seg(a, b - a); tt = np.arange(n)/SR
    e[i0:i0+n] = np.clip(tt/fade, 0, 1) * np.clip(((b-a) - tt)/fade, 0, 1); return e
def boom(at, gain=0.6, f0=90, f1=28, dur=1.6):
    i0, n = seg(at, dur); tt = np.arange(n)/SR; f = f1 + (f0-f1)*np.exp(-tt*4)
    s = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*2.8); nz = smooth(rs.randn(n), 8)*np.exp(-tt*9)*0.6
    mix[i0:i0+n] += gain*(s + nz)
def tick(at, gain=0.16, f=3200):
    i0, n = seg(at, 0.05); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*(np.sin(2*np.pi*f*tt) + 0.6*rs.randn(n))*np.exp(-tt*160)
def tink(at, gain=0.2, f=2400):
    i0, n = seg(at, 0.25); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*(np.sin(2*np.pi*f*tt) + 0.5*np.sin(2*np.pi*f*1.51*tt))*np.exp(-tt*28) + gain*0.5*rs.randn(n)*np.exp(-tt*80)
def whoosh(at, dur=0.6, gain=0.25):
    i0, n = seg(at-dur, dur); tt = np.linspace(0,1,n); nz = rs.randn(n); nz = nz - smooth(nz, 30)
    mix[i0:i0+n] += gain*nz*tt**2
def sweep(at, dur, gain=0.06):
    i0, n = seg(at, dur); tt = np.arange(n)/SR
    f = 300 + 900*((tt*0.6) % 1)
    mix[i0:i0+n] += gain*np.sin(2*np.pi*np.cumsum(f)/SR)*np.clip(tt/0.2,0,1)*np.clip((dur-tt)/0.3,0,1)
def chime(at, gain=0.18, base=880):
    i0, n = seg(at, 2.5); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*sum(np.sin(2*np.pi*fr*tt)*a for fr,a in ((base,1),(base*1.5,.5),(base*2,.25)))*np.exp(-tt*2.2)
def splash(at, gain=0.3):
    i0, n = seg(at, 1.2); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*smooth(rs.randn(n), 3)*np.exp(-tt*4)
def bubbles(a, b, gain=0.08):
    k = a
    while k < b:
        i0, n = seg(k, 0.08); tt = np.arange(n)/SR; f = 500 + rs.rand()*700
        mix[i0:i0+n] += gain*np.sin(2*np.pi*(f + 3000*tt)*tt)*np.exp(-tt*50)
        k += 0.08 + rs.rand()*0.25


def beep(at, dur=0.08, gain=0.1, f=900):
    i0, n = seg(at, dur); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*np.sin(2*np.pi*f*tt)*np.clip(tt/0.005,0,1)*np.clip((dur-tt)/0.005,0,1)
def morse_run(a, b, gain=0.08, f=880):
    k = a; pat = ".-- --. ..- .-. .-.. -. ... - .-."; i = 0
    while k < b - 0.1:
        c = pat[i % len(pat)]; i += 1
        if c == ".": beep(k, 0.06, gain, f); k += 0.12
        elif c == "-": beep(k, 0.18, gain, f); k += 0.24
        else: k += 0.18
def crowd(a, b, gain=0.05):
    mix[:] += gain*smooth(rs.randn(N), 25)*env_span(a, b, 0.4)

def creak(at, dur=0.8, gain=0.08):
    i0, n = seg(at, dur); tt = np.arange(n)/SR
    f = 140 + 60*np.sin(2*np.pi*3*tt)
    mix[i0:i0+n] += gain*np.sign(np.sin(2*np.pi*np.cumsum(f)/SR))*np.clip(tt/0.1,0,1)*np.clip((dur-tt)/0.2,0,1)*0.5
def drip(at, gain=0.12):
    i0, n = seg(at, 0.12); tt = np.arange(n)/SR; f = 900 + 1400*tt/0.12
    mix[i0:i0+n] += gain*np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*40)
def rumble(a, b, gain=0.5):
    mix[:] += gain*smooth(rs.randn(N), 300)*4*env_span(a, b, 0.3)
def wind(a, b, gain=0.06):
    nz = smooth(rs.randn(N), 12) - smooth(rs.randn(N), 60)
    mix[:] += gain*nz*(0.6+0.4*np.sin(2*np.pi*0.3*t))*env_span(a, b, 0.6)

# hook
rumble(0.2, ws(1, "e"), .35); boom(ws(1, "21"), .4, 100, 40, 1.0)
splash(ws(1, "e"), .25); boom(ws(1, "água"), .45, 80, 30, 1.2)
boom(L[2]["s"], .3, 140, 60, .6)
air = smooth(rs.randn(N), 40); mix += 0.03*air*env_span(L[2]["s"], L[5]["s"], 0.5)
creak(ws(3, "com"), 1.0, .06); boom(ws(3, "15"), .3, 120, 50, .8)
for k in range(5): drip(L[4]["s"] + 0.5 + k*0.55, .08)
crowd(L[5]["s"], ws(5, "que"), .04)
for k in range(5): boom(ws(5, "munição") - 0.3 + k*0.12, .12, 160, 80, .3)
for k in range(8): drip(L[6]["s"] + 0.2 + k*0.28, .12)
boom(ws(6, "vazava"), .3, 100, 40, .8)
for k in range(6): whoosh(L[7]["s"] + 0.3 + k*0.27, .2, .08)
for k in range(10): drip(L[8]["s"] + 0.2 + k*0.3, .1)
sweep(ws(9, "subido"), 3.0, .04)
for k in range(int((L[10]["s"] - 0.0 - 0) * 0) + 4): tick(L[10]["s"] + k*0.3, .12, 1800)
creak(L[10]["s"] + 0.6, 1.0, .1)
boom(ws(10, "estourou") - 0.05, .9, 70, 22, 2.4); splash(ws(10, "estourou"), .4)
rumble(L[11]["s"], L[13]["s"] - 0.2, .45)
boom(ws(11, "onda"), .4, 80, 30, 1.2); whoosh(ws(11, "56"), .6, .3)
boom(ws(12, "destruiu"), .45, 90, 30, 1.2); boom(ws(12, "entortou"), .4, 140, 50, .9); creak(ws(12, "entortou"), 1.2, .12)
splash(ws(12, "arrastou"), .3)
whoosh(twist, .7, .3); boom(twist, .6, 70, 28, 1.8)
boom(ws(14, "velocidade"), .3, 110, 45, .8)
wind(L[15]["s"], L[17]["s"], .07)
boom(ws(15, "cola"), .3, 70, 30, 1.2)
boom(ws(16, "pesadelo"), .35, 70, 28, 1.4)
boom(ws(17, "21"), .45, 60, 25, 1.8); boom(ws(17, "150"), .3, 80, 30, 1.2)
boom(L[18]["s"], .25, 140, 60, .5); chime(ws(18, "harvard"), .1, 660)
for k in range(5): tink(ws(18, "o") + k*0.4, .05, 2000 + 120*k)
chime(L[19]["s"]+0.3, .1, 523)
rumble(L[20]["s"], ws(20, "era"), .3)
chime(ws(20, "doce"), .2, 880)

mix = mix / max(1e-6, np.abs(mix).max()) * 0.5
sf.write(out, mix.astype(np.float32), SR)
print("ok", round(D, 1), "s")
