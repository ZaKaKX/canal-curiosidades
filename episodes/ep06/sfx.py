"""EP06 (PT-BR) sound bed: mysterious drone, sea/underwater wash, clockwork ticks under the gear scenes,
x-ray scan sweep, impacts on action words, twist hit, eclipse swell, final chime. usage: sfx.py timings.json out.wav"""
import sys, json, numpy as np, soundfile as sf
TJ = json.load(open(sys.argv[1])); out = sys.argv[2]
SR = 48000; D = TJ["duration"]; N = int(D * SR); rs = np.random.RandomState(6)
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

# sea wash under ship + island scenes
wash = smooth(rs.randn(N), 400) * (0.6 + 0.4*np.sin(2*np.pi*0.18*t))
mix += 0.9*wash * (env_span(0, L[2]["s"]) + env_span(L[2]["s"], ws(3, "acham")))
# hook
boom(ws(1, "afundou"), .5, 80, 30, 1.8); splash(ws(1, "afundou")+0.2, .25)
chime(ws(1, "computador"), .16, 660)
boom(L[2]["s"], .25, 140, 60, .5)
# dive + underwater
splash(ws(3, "acham"), .3)
bubbles(ws(3, "acham"), L[6]["s"]); bubbles(L[19]["s"], ws(19, "chamado"))
tink(ws(4, "tesouro"), .18, 2000)
# 1902: discovery hit
boom(L[6]["s"], .25, 140, 60, .5); tink(ws(6, "engrenagem"), .22, 1800)
boom(L[7]["s"], .45, 90, 35, 1.2)
# x-ray sweep
sweep(L[8]["s"], ws(8, "revelaram") - L[8]["s"])
boom(ws(8, "30"), .35, 120, 50, 1.0)
# clockwork ticks under the gear/mechanism scenes
for a, b, step in ((ws(8, "revelaram"), L[13]["s"], 0.25), (L[16]["s"], ws(16, "eclipses"), 0.25), (ws(19, "chamado"), D - 0.6, 0.25)):
    k = a; i = 0
    while k < b - 0.05:
        tick(k, .12 if i % 2 == 0 else .08, 3200 if i % 2 == 0 else 2600); k += step; i += 1
# twist
whoosh(twist, .7, .3); boom(twist, .55, 70, 28, 1.8)
# 2005 CT
boom(L[14]["s"], .25, 140, 60, .5); sweep(L[14]["s"]+0.3, ws(14, "milhares") - L[14]["s"] - 0.3, .05)
for k in range(8): tink(ws(14, "milhares") + 0.3 + k*0.4, .07, 2600 + 200*k)
# eclipse swell
boom(ws(16, "eclipses"), .3, 60, 30, 2.5)
# 1000 years / clocks
boom(ws(17, "mil"), .3, 110, 45, 1.2); chime(ws(17, "relógios"), .12, 523)
# mystery
boom(L[18]["s"]+0.2, .2, 90, 45, 1.0)
# close
chime(ws(19, "chamado"), .2, 880)

mix = mix / max(1e-6, np.abs(mix).max()) * 0.5
sf.write(out, mix.astype(np.float32), SR)
print("ok", round(D, 1), "s")
