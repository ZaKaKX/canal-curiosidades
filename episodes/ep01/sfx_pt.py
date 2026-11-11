import sys, json, numpy as np, soundfile as sf
TJ = json.load(open(sys.argv[1])); out = sys.argv[2]
SR = 48000; D = TJ["duration"]; N = int(D * SR); rs = np.random.RandomState(1)
L = {l["i"]: l for l in TJ["lines"]}
def ws(i, w, n=0): return [x for x in L[i]["words"] if x["w"].strip(".,!?'").lower().startswith(w)][n]["s"]
t = np.arange(N) / SR
def lp(x, a):  # one-pole lowpass
    y = np.empty_like(x); acc = 0.0
    for i in range(0, len(x), 1): pass
    return x
def smooth(x, k):
    ker = np.ones(k) / k; return np.convolve(x, ker, mode="same")
mix = np.zeros(N)
# ambient drone + ocean, darker after twist
twist = L[16]["s"]
drone = sum(np.sin(2*np.pi*f*t + p) * a for f, a, p in ((55, .5, 0), (82.5, .3, 1), (110, .2, 2), (164.8, .08, 3)))
drone *= 0.6 + 0.4 * np.sin(2*np.pi*0.07*t)
ocean = smooth(rs.randn(N), 60) * (0.6 + 0.4*np.sin(2*np.pi*0.12*t))
amb = 0.035*drone + 0.08*ocean
amb *= np.where(t < twist, 1.0, 1.35)
fade = np.clip(t/1.0, 0, 1) * np.clip((D - t)/1.5, 0, 1)
mix += amb * fade
def boom(at, gain=0.6, f0=90, f1=28, dur=1.6):
    i0 = int(at*SR); n = int(dur*SR); n = min(n, N-i0)
    tt = np.arange(n)/SR; f = f1 + (f0-f1)*np.exp(-tt*4)
    ph = 2*np.pi*np.cumsum(f)/SR
    env = np.exp(-tt*2.8); s = np.sin(ph)*env
    nz = smooth(rs.randn(n), 8) * np.exp(-tt*9) * 0.6
    mix[i0:i0+n] += gain*(s + nz)
def whoosh(at, dur=0.6, gain=0.25):
    i0 = int((at-dur)*SR); n = int(dur*SR); tt = np.linspace(0,1,n)
    nz = rs.randn(n); env = tt**2
    nz = nz - smooth(nz, 30)
    mix[i0:i0+n] += gain*nz*env
def chime(at, gain=0.18):
    i0 = int(at*SR); n = int(2.5*SR); n=min(n,N-i0); tt = np.arange(n)/SR
    s = sum(np.sin(2*np.pi*f*tt)*a for f,a in ((880,1),(1320,.5),(1760,.25)))*np.exp(-tt*2.2)
    mix[i0:i0+n] += gain*s
boom(ws(5,"bateu"), .7); boom(ws(11,"bateu"), .55, 70, 25, 2.2); boom(ws(19,"bateu"), .9, 110, 22, 2.4)
boom(ws(21,"bateu"), .35, 120, 60, .5); boom(L[6]["s"], .25, 60, 30, 1.0)
whoosh(twist, .7, .3); whoosh(L[10]["s"], .5, .15)
for k,(w,n) in enumerate((("três",0),("três",1),("uma",0))): boom(ws(22,w,n), .22, 140, 70, .35)
chime(L[23]["s"])
mix = mix / max(1e-6, np.abs(mix).max()) * 0.5
sf.write(out, mix.astype(np.float32), SR)
print("ok")
