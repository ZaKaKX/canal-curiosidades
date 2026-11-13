"""EP05 (PT-BR) sound bed: medieval drone + a tireless dance drum/tambourine, pipe at the stage,
collapses, shrine bell, twist hit, final chime. usage: sfx.py timings.json out.wav"""
import sys, json, numpy as np, soundfile as sf
TJ = json.load(open(sys.argv[1])); out = sys.argv[2]
SR = 48000; D = TJ["duration"]; N = int(D * SR); rs = np.random.RandomState(5)
L = {l["i"]: l for l in TJ["lines"]}
def ws(i, w, n=0):
    hits = [x for x in L[i]["words"] if x["w"].strip(".,!?'").lower() == w] or [x for x in L[i]["words"] if x["w"].strip(".,!?'").lower().startswith(w)]
    return hits[n]["s"]
t = np.arange(N) / SR
def smooth(x, k): return np.convolve(x, np.ones(k) / k, mode="same")
mix = np.zeros(N)
twist = L[15]["s"]

# ambient drone (minor, medieval)
drone = sum(np.sin(2*np.pi*f*t + p) * a for f, a, p in ((55, .5, 0), (82.4, .3, 1), (110, .2, 2), (146.8, .1, 3)))
drone *= 0.6 + 0.4 * np.sin(2*np.pi*0.06*t)
air = smooth(rs.randn(N), 80) * (0.6 + 0.4*np.sin(2*np.pi*0.1*t))
amb = 0.03*drone + 0.045*air
mix += amb * np.clip(t/1.0, 0, 1) * np.clip((D - t)/1.5, 0, 1)

def seg(at, dur):
    i0 = max(0, int(at*SR)); n = max(0, min(int(dur*SR), N-i0)); return i0, n
def boom(at, gain=0.6, f0=90, f1=28, dur=1.6):
    i0, n = seg(at, dur); tt = np.arange(n)/SR; f = f1 + (f0-f1)*np.exp(-tt*4)
    s = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*2.8); nz = smooth(rs.randn(n), 8)*np.exp(-tt*9)*0.6
    mix[i0:i0+n] += gain*(s + nz)
def drum(at, gain=0.5, f=150):
    i0, n = seg(at, 0.22); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*np.sin(2*np.pi*f*np.exp(-tt*8)*tt*0+2*np.pi*f*tt)*np.exp(-tt*16) + gain*0.4*smooth(rs.randn(n),4)*np.exp(-tt*40)
def tamb(at, gain=0.18):
    i0, n = seg(at, 0.16); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*smooth(rs.randn(n), 2)*np.exp(-tt*30)*np.sin(2*np.pi*6000*tt)
def tink(at, gain=0.2, f=2400):
    i0, n = seg(at, 0.25); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*(np.sin(2*np.pi*f*tt) + 0.5*np.sin(2*np.pi*f*1.51*tt))*np.exp(-tt*28) + gain*0.5*rs.randn(n)*np.exp(-tt*80)
def pipe(at, dur, gain=0.07, f=392):
    i0, n = seg(at, dur); tt = np.arange(n)/SR
    mel = np.sin(2*np.pi*f*tt) + 0.3*np.sin(2*np.pi*f*1.5*tt)
    trill = 1 + 0.02*np.sin(2*np.pi*6*tt)
    mix[i0:i0+n] += gain*np.sin(2*np.pi*f*tt*trill)*np.clip(tt/0.2,0,1)*np.clip((dur-tt)/0.3,0,1)
def whoosh(at, dur=0.6, gain=0.25):
    i0, n = seg(at-dur, dur); tt = np.linspace(0,1,n); nz = rs.randn(n); nz = nz - smooth(nz, 30)
    mix[i0:i0+n] += gain*nz*tt**2
def bell(at, gain=0.2, f=523):
    i0, n = seg(at, 3.0); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*sum(np.sin(2*np.pi*fr*tt)*a for fr,a in ((f,1),(f*2.76,.5),(f*5.4,.25)))*np.exp(-tt*1.6)
def chime(at, gain=0.18, base=880):
    i0, n = seg(at, 2.5); tt = np.arange(n)/SR
    mix[i0:i0+n] += gain*sum(np.sin(2*np.pi*fr*tt)*a for fr,a in ((base,1),(base*1.5,.5),(base*2,.25)))*np.exp(-tt*2.2)

# --- hook ---
boom(ws(1, "dançar"), .25, 140, 70, .4); chime(ws(1, "parar"), .14, 660)

# --- a relentless dance beat under the dancing stretches ---
# groups of (start, end) where people are dancing
beat_spans = [(L[1]["s"], L[2]["s"]), (L[3]["s"], L[6]["s"]), (L[6]["s"], L[12]["s"]),
              (L[16]["s"], L[17]["s"]), (L[20]["s"], D)]
bpm = 132; step = 60.0/bpm/2  # eighth notes
for (a, b) in beat_spans:
    k = a
    i = 0
    while k < b - 0.05:
        if k < twist or a >= L[16]["s"]:
            if i % 2 == 0:
                drum(k, 0.34, 150 if i % 4 == 0 else 110)
            else:
                tamb(k, 0.14)
        k += step; i += 1

# --- Troffea alone (sparse taps already covered) ---
# --- doctors ---
tink(ws(7, "diagnóstico") if False else L[7]["s"]+0.2, .14, 1600)
tink(ws(8, "dança"), .16, 1300)
# --- stage: pipe melody ---
pipe(L[9]["s"], L[11]["s"]-L[9]["s"], .06, 392)
# --- 400 swell ---
boom(ws(11, "400"), .3, 120, 50, 1.2)
# --- collapses ---
for k, g in ((L[12]["s"]+0.4, .4), (L[12]["s"]+1.4, .45), (L[12]["s"]+2.4, .4)):
    boom(k, g, 70, 30, .9)
# --- shrine: bell + calm ---
bell(L[13]["s"]+0.3, .18, 466); bell(L[14]["s"]+0.4, .2, 523)
chime(L[14]["s"]+1.2, .14, 784)
# --- twist ---
whoosh(twist, .7, .3); boom(twist, .55, 70, 28, 1.8)
# --- saint belief: ominous low ---
boom(L[16]["s"]+0.3, .18, 90, 45, 1.0)
# --- waller ---
chime(L[18]["s"]+0.3, .10, 1046)
# --- debunk ticks ---
tink(ws(19, "veneno"), .12, 900)
# --- close ---
chime(L[20]["s"], .2, 880)

mix = mix / max(1e-6, np.abs(mix).max()) * 0.5
sf.write(out, mix.astype(np.float32), SR)
print("ok", round(D,1), "s")
