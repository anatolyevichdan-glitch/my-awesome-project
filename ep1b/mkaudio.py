import numpy as np, subprocess, wave
SR = 44100
DUR = 108.4
N = int(SR * DUR)
rng = np.random.default_rng(11)
t = np.arange(N) / SR


def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)


def env_at(T, pts):
    return np.interp(T, [p[0] for p in pts], [p[1] for p in pts])


def place(buf, sig, t0, g=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    s = sig[: N - i]
    buf[0, i:i + len(s)] += s * g * (1 - max(0, pan))
    buf[1, i:i + len(s)] += s * g * (1 + min(0, pan))


def decay(n, tau): return np.exp(-np.arange(n) / (tau * SR))


def thud(f0=55, dur=0.9, tau=0.22):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (f0 + 60 * np.exp(-tt * 30)) * tt) * decay(n, tau)


def hit(dur=2.2, tau=0.7):
    n = int(dur * SR)
    nz = lp(rng.standard_normal(n), 900) * 6
    return (thud(40, dur, tau)[:n] * 1.0 + nz * decay(n, tau * 0.6) * 0.5)


def riser(dur, f0=80, f1=900):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (tt / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    nz = lp(rng.standard_normal(n), 2500) * 3
    return (np.sin(ph) * 0.5 + np.sin(ph * 1.5) * 0.25 + nz * 0.4) * (tt / dur) ** 2


def buzz(dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * 150 * tt) * np.sign(np.sin(2 * np.pi * 14 * tt)) * 0.6
    return lp(s, 600) * 2.4 * np.minimum(1, np.minimum(tt * 50, (dur - tt) * 50))


def ping(dur=1.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1760 * tt) + 0.5 * np.sin(2 * np.pi * 2637 * tt)) * decay(n, 0.25) * 0.3


def lampzap(dur=0.9):
    n = int(dur * SR); tt = np.arange(n) / SR
    g = (np.sin(2 * np.pi * 120 * tt) + rng.standard_normal(n) * 0.5) * (rng.random(n // 400 + 1).repeat(400)[:n] > 0.4)
    return lp(g, 3000) * decay(n, 0.3) * 0.7 + thud(70, dur, 0.15) * 0.8


def step(f=140):
    n = int(0.18 * SR); return lp(rng.standard_normal(n), f * 3) * decay(n, 0.05) * 2.0


def breath(dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    nz = lp(rng.standard_normal(n), 1400) - lp(rng.standard_normal(n), 250)
    return nz * (0.5 - 0.5 * np.cos(2 * np.pi * tt / 0.9)) ** 1.5 * 2.6


mix = np.zeros((2, N))
# --- rain bed
rain = lp(rng.standard_normal(N), 7000) - lp(rng.standard_normal(N), 800)
rain2 = lp(rng.standard_normal(N), 5000) - lp(rng.standard_normal(N), 500)
rg = env_at(t, [(0, .5), (105, .55), (106, 0)]) * 0.11
mix[0] += rain * rg; mix[1] += rain2 * rg
# --- drone (grows with tension)
dg = env_at(t, [(0, .03), (17, .05), (24, .09), (44, .08), (52, .16), (58, .22), (66, .12), (72, .26), (83, .3), (93, .18), (95, .34), (103, .4), (104.8, .0), (108.4, 0)])
dr = (np.sin(2 * np.pi * 43 * t + 2 * np.sin(2 * np.pi * .13 * t)) + .6 * np.sin(2 * np.pi * 64.5 * t) + .35 * np.sin(2 * np.pi * 86.5 * t + np.sin(2 * np.pi * .3 * t)))
mix[0] += dr * dg * 0.55; mix[1] += dr[::-1].copy() * dg * 0.55 if False else dr * dg * 0.55
# dissonant high shimmer
sh = np.sin(2 * np.pi * (1318 + 4 * np.sin(2 * np.pi * .21 * t)) * t) * np.sin(2 * np.pi * (1396) * t)
sg = env_at(t, [(0, 0), (30, 0), (52, .02), (72, .04), (95, .045), (104.8, 0)])
mix[0] += sh * sg * .4; mix[1] += sh * sg * .4
# --- heartbeat
def heart(T0, T1, bpm0, bpm1, g0, g1):
    tt = T0
    while tt < T1:
        k = (tt - T0) / (T1 - T0)
        g = g0 + (g1 - g0) * k
        place(mix, thud(58, .5, .12), tt, g * .9)
        place(mix, thud(52, .5, .12), tt + .22, g * .6)
        bpm = bpm0 + (bpm1 - bpm0) * k
        tt += 60 / bpm
heart(14.3, 17.5, 70, 100, .15, .4)
heart(24.6, 29, 66, 72, .08, .1)
heart(51.7, 58.7, 100, 130, .5, .7)
heart(58.7, 66, 140, 150, .7, .8)
heart(86, 93, 90, 120, .3, .6)
heart(95, 104.4, 55, 50, .5, .7)
# --- footsteps
def steps(T0, T1, period, g):
    tt = T0; k = 0
    while tt < T1:
        place(mix, step(120 if k % 2 else 170), tt, g, pan=-.2 if k % 2 else .2); tt += period; k += 1
steps(0.3, 6.3, .52, .35)
steps(6.4, 11.8, .55, .4)
steps(11.94, 14.5, .36, .55)
steps(59.4, 63.3, .22, .85)
steps(63.4, 64.9, .22, .8)
# entity steps (heavy, slower, offset)
steps(1.5, 6.3, 1.05, .22); steps(6.8, 14.4, .82, .3); steps(59.6, 63.2, .34, .5)
# --- breath
place(mix, breath(2.6), 60.9, .5); place(mix, breath(2.6), 62.0, .7)
for T0 in (60.5, 62.4): place(mix, breath(1.5), T0, .8)
# --- events
for T0 in (17.6, 44.94, 50.14): place(mix, buzz(1.0), T0, .9)
place(mix, buzz(0.5), 18.7, .7)
for T0, g in ((21.2, 1.0), (47.6, .9), (51.74, 1.2)):
    place(mix, hit(2.4), T0, g); place(mix, ping(), T0, .8)
place(mix, riser(2.6), 15.0, .55)         # before the stop
place(mix, hit(), 15.84, .8)
place(mix, riser(2.0, 120, 1500), 22.9, .5)
place(mix, riser(3.0), 38.5, .55); place(mix, hit(3.0, 1.0), 41.55, 1.0)   # finger to lips
place(mix, thud(45, 1.2, .3), 43.2, 1.0)
place(mix, riser(4.0, 60, 700), 49.4, .5)
for T0 in (56.26, 56.88, 57.68):
    place(mix, lampzap(1.0), T0, 1.0)
for T0 in (55.0, 55.35, 55.7): place(mix, lampzap(.4), T0, .4)
place(mix, hit(3.0, 1.0), 58.7, .9)
place(mix, thud(40, 1.2, .4), 64.9, 1.5); place(mix, hit(2.6), 64.9, .9)       # collision
place(mix, riser(2.0, 90, 1200), 64.1, .6)
place(mix, hit(3.5, 1.2), 72.3, 1.1)                                           # black eyes
place(mix, riser(2.6), 72.4 - 2.6 + 2.6 - 2.6, .0)
place(mix, thud(42, 1.0, .3), 75.3, 1.4)                                       # grab
place(mix, riser(3.0, 100, 1400), 83.2 - 3.0 + 2.8, .0)
place(mix, hit(3.2, 1.1), 83.2, .9)
place(mix, riser(4.0, 70, 1600), 86.3, .7)
place(mix, hit(3.5, 1.2), 90.5, 1.0)
place(mix, riser(2.5, 80, 800), 92.3, .7)
place(mix, hit(4.0, 1.5), 95.0, 1.3)
place(mix, riser(3.0, 50, 400), 99.0, .6)
place(mix, hit(4.5, 1.8), 102.4, 1.2)
# --- final: silence, one low tail
mix[:, int(104.9 * SR):] *= 0
place(mix, thud(36, 2.5, 1.0), 105.0, .6)
# --- voice
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'narr.mp3', '-ar', str(SR), '-ac', '1', '-f', 'f32le', 'voice.raw'], check=True)
v = np.fromfile('voice.raw', np.float32)
vv = np.zeros(N); vv[:min(N, len(v))] = v[:N]
# normalize voice, light compression
vv = vv / (np.abs(vv).max() + 1e-9) * 0.85
vv = np.tanh(vv * 1.3) / np.tanh(1.3)
# duck music under voice
from scipy.signal import fftconvolve
vm = np.abs(vv)
duck = np.clip(lp(vm, 8) * 9, 0, 1)
duck = 1 - 0.38 * duck
mix = mix * duck
# master music level + hit transients preserved by duck being gentle
peak = np.abs(mix).max()
mix = mix / peak * 0.8
out = mix.copy()
out[0] += vv; out[1] += vv
out = np.tanh(out * 0.95) / np.tanh(0.95)
out = out / np.abs(out).max() * 0.92
pcm = (out.T * 32767).astype(np.int16)
with wave.open('DONT_LOOK_BACK_EP1_AUDIO_MIX.wav', 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes(pcm.tobytes())
print('ok', len(vv) / SR)
