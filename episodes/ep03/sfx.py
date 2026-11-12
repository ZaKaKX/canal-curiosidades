"""EP03 (PT-BR) sound bed (adapted from kit/sfx_ep01.py): drone + harbor water, wind gusts, creaks, splashes, impacts, final chime."""
import sys, json, numpy as np, soundfile as sf
TJ = json.load(open(sys.argv[1])); out = sys.argv[2]
SR = 48000; D = TJ["duration"]; N = int(D * SR); rs = np.random.RandomState(2)
L = {l["i"]: l for l in TJ["lines"]}
def ws(i, w, n=0): return ([x for x in L[i]["words"] if x["w"].strip(".,!?'").lower() == w] or [x for x in L[i]["words"] if x["w"].strip(".,!?'").lower().startswith(w)])[n]["s"]
t = np.arange(N) / SR
def smooth(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")
mix = np.zeros(N)
twist = L[19]["s"]
drone = sum(np.sin(2*np.pi*f*t + p) * a for f, a, p in ((49, .5, 0), (73.4, .3, 1), (98, .2, 2), (146.8, .08, 3)))
drone *= 0.6 + 0.4 * np.sin(2*np.pi*0.07*t)
water = smooth(rs.randn(N), 60) * (0.6 + 0.4*np.sin(2*np.pi*0.12*t))
amb = 0.035*drone + 0.07*water
amb *= np.where(t < twist, 1.0, 1.3)
mix += amb * np.clip(t/1.0, 0, 1) * np.clip((D - t)/1.5, 0, 1)
def boom(at, gain=0.6, f0=90, f1=28, dur=1.6):
    i0 = int(at*SR); n = min(int(dur*SR), N-i0)
    tt = np.arange(n)/SR; f = f1 + (f0-f1)*np.exp(-tt*4)
    s = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*2.8)
    nz = smooth(rs.randn(n), 8) * np.exp(-tt*9) * 0.6
    mix[i0:i0+n] += gain*(s + nz)
def whoosh(at, dur=0.6, gain=0.25):
    i0 = int((at-dur)*SR); n = int(dur*SR); tt = np.linspace(0,1,n)
    nz = rs.randn(n); nz = nz - smooth(nz, 30)
    mix[i0:i0+n] += gain*nz*tt**2
def gust(at, dur=1.8, gain=0.35):
    i0 = int(at*SR); n = min(int(dur*SR), N-i0); tt = np.linspace(0, 1, n)
    nz = smooth(rs.randn(n), 14) - smooth(rs.randn(n), 120)
    mix[i0:i0+n] += gain * nz * np.sin(np.pi*tt)**2
def creak(at, dur=0.7, gain=0.18, f=140):
    i0 = int(at*SR); n = min(int(dur*SR), N-i0); tt = np.arange(n)/SR
    fm = f * (1 + 0.15*np.sin(2*np.pi*3*tt)); s = np.sign(np.sin(2*np.pi*np.cumsum(fm)/SR)) * (rs.rand(n) > 0.3)
    mix[i0:i0+n] += gain * smooth(s, 20) * np.sin(np.pi*np.linspace(0, 1, n))
def splash_s(at, dur=1.2, gain=0.3):
    i0 = int(at*SR); n = min(int(dur*SR), N-i0); tt = np.arange(n)/SR
    nz = rs.randn(n) - smooth(rs.randn(n), 10)
    mix[i0:i0+n] += gain * nz * np.exp(-tt*3.5)
def chime(at, gain=0.18):
    i0 = int(at*SR); n = min(int(2.5*SR), N-i0); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*sum(np.sin(2*np.pi*f*tt)*a for f,a in ((880,1),(1320,.5),(1760,.25)))*np.exp(-tt*2.2)
# hook: ship going down
creak(0.3, 1.2, .2, 110); splash_s(1.2, 1.5, .25)
# test runs: footsteps + creaks
for k in np.arange(L[8]["s"] + 1.0, ws(9, "almirante"), 0.32):
    boom(k, .05, 160, 90, .12)
for k in (L[9]["s"] + 0.5, L[9]["s"] + 2.0, L[9]["s"] + 3.4): creak(k, .8, .2, 120)
boom(ws(9, "almirante"), .3, 120, 60, .5)
# sinking sequence
gust(L[13]["s"], 2.0, .4); creak(L[14]["s"], 1.0, .25, 100); boom(L[14]["s"] + 0.1, .35, 70, 30, 1.2)
gust(L[15]["s"], 1.6, .55); boom(L[15]["s"] + 0.6, .5, 60, 25, 1.8)
splash_s(L[16]["s"], 2.2, .4); splash_s(L[16]["s"] + 0.8, 1.6, .3)
boom(L[18]["s"], .25, 50, 25, 2.0)
whoosh(twist, .7, .3)
boom(ws(20, "não"), .25, 140, 70, .35)
splash_s(L[23]["s"] + 0.3, 2.0, .35); boom(L[23]["s"] + 0.2, .3, 80, 40, 1.0)
for w in (L[24]["s"], L[25]["s"]): boom(w + 0.1, .18, 140, 70, .35)
chime(L[26]["s"])
mix = mix / max(1e-6, np.abs(mix).max()) * 0.5
sf.write(out, mix.astype(np.float32), SR)
print("ok")
