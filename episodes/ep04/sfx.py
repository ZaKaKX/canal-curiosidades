"""EP04 (PT-BR) sound bed (adapted from ep03/sfx.py): drone + chisel taps, brush, rain, scraping, twist hit, UV hum, final chime."""
import sys, json, numpy as np, soundfile as sf
TJ = json.load(open(sys.argv[1])); out = sys.argv[2]
SR = 48000; D = TJ["duration"]; N = int(D * SR); rs = np.random.RandomState(4)
L = {l["i"]: l for l in TJ["lines"]}
def ws(i, w, n=0): return ([x for x in L[i]["words"] if x["w"].strip(".,!?'").lower() == w] or [x for x in L[i]["words"] if x["w"].strip(".,!?'").lower().startswith(w)])[n]["s"]
t = np.arange(N) / SR
def smooth(x, k): return np.convolve(x, np.ones(k) / k, mode="same")
mix = np.zeros(N)
twist = L[15]["s"]
drone = sum(np.sin(2*np.pi*f*t + p) * a for f, a, p in ((55, .5, 0), (82.4, .3, 1), (110, .2, 2), (164.8, .08, 3)))
drone *= 0.6 + 0.4 * np.sin(2*np.pi*0.07*t)
air = smooth(rs.randn(N), 80) * (0.6 + 0.4*np.sin(2*np.pi*0.1*t))
amb = 0.035*drone + 0.05*air
amb *= np.where(t < twist, 1.0, 1.3)
mix += amb * np.clip(t/1.0, 0, 1) * np.clip((D - t)/1.5, 0, 1)
def seg(at, dur):
    i0 = max(0, int(at*SR)); n = max(0, min(int(dur*SR), N-i0)); return i0, n
def boom(at, gain=0.6, f0=90, f1=28, dur=1.6):
    i0, n = seg(at, dur); tt = np.arange(n)/SR; f = f1 + (f0-f1)*np.exp(-tt*4)
    s = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*2.8); nz = smooth(rs.randn(n), 8) * np.exp(-tt*9) * 0.6
    mix[i0:i0+n] += gain*(s + nz)
def tink(at, gain=0.2, f=2400):
    i0, n = seg(at, 0.25); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*(np.sin(2*np.pi*f*tt) + 0.5*np.sin(2*np.pi*f*1.51*tt))*np.exp(-tt*28) + gain*0.5*rs.randn(n)*np.exp(-tt*80)
def noise_bed(at, dur, gain, k1=6, k2=60, mod=0.0):
    i0, n = seg(at, dur); tt = np.linspace(0, 1, n)
    nz = smooth(rs.randn(n), k1) - smooth(rs.randn(n), k2)
    env = np.sin(np.pi*tt)**0.5
    if mod: env = env * (0.5 + 0.5*np.abs(np.sin(2*np.pi*mod*np.arange(n)/SR)))
    mix[i0:i0+n] += gain*nz*env
def whoosh(at, dur=0.6, gain=0.25):
    i0, n = seg(at-dur, dur); tt = np.linspace(0,1,n); nz = rs.randn(n); nz = nz - smooth(nz, 30)
    mix[i0:i0+n] += gain*nz*tt**2
def hum(at, dur, gain=0.08):
    i0, n = seg(at, dur); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*(np.sin(2*np.pi*120*tt) + 0.4*np.sin(2*np.pi*240*tt))*np.clip(tt/0.3, 0, 1)*np.clip((dur-tt)/0.3, 0, 1)
def chime(at, gain=0.18, base=880):
    i0, n = seg(at, 2.5); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*sum(np.sin(2*np.pi*f*tt)*a for f,a in ((base,1),(base*1.5,.5),(base*2,.25)))*np.exp(-tt*2.2)
# hook
boom(ws(1, "brancas"), .25, 140, 70, .4); chime(ws(1, "nunca"), .16, 660)
# chisel
for k in np.arange(L[3]["s"] + 0.3, L[4]["s"], 0.35): tink(k, .15, 2200 + 300*rs.rand())
for k in np.arange(L[10]["s"] + 0.3, L[11]["s"], 0.35): tink(k, .12, 2200 + 300*rs.rand())
# brush strokes
for k in np.arange(ws(4, "pintada"), L[5]["s"], 0.45): noise_bed(k, 0.35, .12, 3, 40)
# tags pop
for w in ("pele", "olhos", "cabelo", "roupas"): tink(ws(5, w), .1, 1400)
chime(ws(5, "tudo"), .15, 1046)
# rain
noise_bed(ws(7, "chuva"), L[8]["s"] - ws(7, "chuva"), .1, 2, 30)
boom(L[8]["s"] + 0.2, .2, 80, 40, 1.0)
# scraping 1937
noise_bed(ws(13, "rasparam"), L[15]["s"] - ws(13, "rasparam") - 0.2, .16, 2, 20, 5.0)
# twist
whoosh(twist, .7, .3); boom(twist, .55, 70, 28, 1.8)
hum(ws(16, "apontou"), L[18]["s"] - ws(16, "apontou"), .06)
chime(L[17]["s"] + 0.3, .12, 1318)
boom(ws(18, "azul"), .2, 120, 60, .5); chime(ws(18, "azul"), .12, 784)
for k in np.arange(L[19]["s"] + 0.5, L[20]["s"], 1.0): tink(k, .05, 3000)
chime(L[21]["s"], .2, 880)
mix = mix / max(1e-6, np.abs(mix).max()) * 0.5
sf.write(out, mix.astype(np.float32), SR)
print("ok")
