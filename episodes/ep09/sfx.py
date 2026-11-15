"""EP09 (PT-BR) sound bed: drone, city air, plane hum, flash booms + rumble, train, office, twist hit, final chime. usage: sfx.py timings.json out.wav"""
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
twist = L[11]["s"]

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

def hum(a, b, gain=0.05, f=110):
    tt = t; mix[:] += gain*(np.sin(2*np.pi*f*tt) + 0.5*np.sin(2*np.pi*f*1.02*tt))*env_span(a, b, 0.5)
def chug(a, b, gain=0.08):
    k = a
    while k < b:
        i0, n = seg(k, 0.15); tt = np.arange(n)/SR
        mix[i0:i0+n] += gain*smooth(rs.randn(n), 6)*np.exp(-tt*25); k += 0.22
def ring(a, b, gain=0.04, f=4200):
    mix[:] += gain*np.sin(2*np.pi*f*t)*env_span(a, b, 0.3)

# hook
air = smooth(rs.randn(N), 40); mix += 0.03*air*env_span(0.2, L[2]["s"], 0.5)
boom(ws(1, "bomba"), .8, 60, 22, 2.4); rumble(ws(1, "bomba"), ws(1, "e"), .35)
boom(ws(1, "outra"), .6, 70, 25, 1.8)
chime(L[2]["s"] + 0.1, .1, 660)
boom(ws(3, "mitsubishi"), .25, 140, 60, .5)
for k in range(5): tick(ws(3, "projetava") + k*0.25, .08, 2600)
chug(L[4]["s"], ws(4, "passar"), .06)
boom(ws(4, "hiroshima"), .25, 120, 50, .6)
boom(L[5]["s"], .25, 140, 60, .5)
for k in range(6): tick(L[6]["s"] + k*0.25, .12, 1800)
hum(ws(6, "ele"), ws(6, "e"), .05, 95)
boom(ws(6, "clarão") - 0.05, .9, 55, 20, 2.6); whoosh(ws(6, "clarão"), .6, .3)
rumble(L[7]["s"], L[8]["s"], .4)
ring(ws(8, "e"), L[9]["s"], .03)
wind(L[9]["s"], L[10]["s"], .06)
chug(L[10]["s"], ws(10, "em"), .1)
boom(ws(10, "nagasaki"), .3, 110, 45, .8)
whoosh(twist, .7, .3); boom(twist, .6, 70, 28, 1.8)
boom(L[12]["s"], .25, 140, 60, .5)
crowd(L[13]["s"], L[15]["s"], .03)
boom(ws(13, "bomba"), .35, 80, 30, 1.0)
boom(ws(14, "enlouquecido"), .25, 160, 80, .4)
sweep(L[15]["s"], ws(15, "outro") - L[15]["s"], .04)
boom(ws(15, "clarão") - 0.05, 1.0, 55, 20, 2.8); whoosh(ws(15, "clarão"), .6, .3)
rumble(L[16]["s"], L[17]["s"], .4)
chime(L[17]["s"] + 0.2, .14, 523)
boom(L[18]["s"], .25, 140, 60, .5); boom(ws(18, "oficialmente"), .3, 120, 50, .5)
chime(L[19]["s"] + 0.3, .1, 660)
boom(L[20]["s"] + 0.2, .35, 70, 28, 1.4); boom(ws(20, "em"), .35, 70, 28, 1.4)
chime(ws(20, "dias"), .2, 880)

mix = mix / max(1e-6, np.abs(mix).max()) * 0.5
sf.write(out, mix.astype(np.float32), SR)
print("ok", round(D, 1), "s")
