"""EP07 (PT-BR) sound bed: drone, Paris street air, impacts on action words, radio beeps/morse, twist hit, war rumble, final chime. usage: sfx.py timings.json out.wav"""
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
twist = L[12]["s"]

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

# hook
boom(ws(1, "prazo")+0.3, .4, 110, 40, 1.0)
chime(ws(1, "antena"), .14, 660); morse_run(ws(1, "antena"), L[2]["s"], .05)
boom(L[2]["s"], .3, 140, 60, .6)
crowd(L[3]["s"], L[4]["s"], .05)
boom(L[4]["s"], .2, 140, 60, .5); whoosh(ws(4, "torre"), .5, .18)
boom(ws(4, "300"), .35, 100, 40, 1.0)
boom(L[5]["s"], .45, 80, 30, 1.2)
for k in range(10): tink(L[6]["s"] + 0.4 + k*0.18, .06, 1600 + 90*k)
boom(ws(6, "inútil"), .4, 90, 35, .9); boom(ws(6, "monstruosa"), .45, 80, 30, 1.1)
boom(L[7]["s"]+0.2, .25, 70, 30, 1.6)
for k in range(6): tick(L[8]["s"] + k*0.3, .12, 1800)
boom(ws(8, "em"), .35, 120, 50, 1.0); chime(ws(8, "mais"), .12, 523)
boom(ws(9, "20"), .4, 110, 45, .9)
boom(L[10]["s"], .25, 140, 60, .5); boom(ws(10, "podia"), .5, 70, 28, 1.6)
for k in range(8): tick(ws(11, "transformou") + k*0.25, .08, 2600)
whoosh(twist, .7, .3); boom(twist, .55, 70, 28, 1.8)
boom(L[13]["s"], .25, 140, 60, .5); morse_run(ws(13, "mensagem"), L[14]["s"], .07)
chime(L[14]["s"]+0.3, .12, 660)
boom(L[15]["s"], .3, 100, 40, 1.0); morse_run(ws(15, "em"), L[16]["s"], .05, 1100); boom(ws(15, "6.000"), .35, 120, 50, 1.0)
boom(ws(16, "renovada"), .4, 110, 45, 1.0); chime(ws(16, "70"), .15, 784)
war = smooth(rs.randn(N), 600)*3*env_span(L[17]["s"], L[19]["s"], 0.6); mix += 0.6*war
boom(L[17]["s"], .45, 60, 25, 2.0)
sweep(ws(17, "a"), L[18]["s"] - ws(17, "a"), .04)
morse_run(L[18]["s"]+0.2, ws(18, "e"), .08)
boom(ws(18, "prender"), .5, 90, 30, 1.2)
chime(ws(19, "foi"), .2, 880); morse_run(ws(19, "salva"), D - 0.6, .04, 1320)

mix = mix / max(1e-6, np.abs(mix).max()) * 0.5
sf.write(out, mix.astype(np.float32), SR)
print("ok", round(D, 1), "s")
