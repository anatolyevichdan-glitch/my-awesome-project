"""Synthesised sound design -> audio/music.wav, audio/ambience.wav, audio/sfx.wav, audio/mix_no_voice.wav (44.1k stereo)."""
import os
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
DUR = 108.0
N = int(SR * DUR)
rng = np.random.default_rng(42)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')
os.makedirs(OUT, exist_ok=True)


def T(n): return np.arange(int(n)) / SR
def noise(sec): return rng.normal(0, 1, int(sec * SR))
def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f, order=2): return signal.sosfilt(signal.butter(order, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, order=2): return signal.sosfilt(signal.butter(order, f, 'high', fs=SR, output='sos'), x)
def env(n, a, d):
    t = np.arange(int(n)) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-t / max(d, 1e-4))
def smoothstep(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


class Track:
    def __init__(self): self.d = np.zeros((2, N), np.float32)
    def add(self, t0, sig, gain=1.0, pan=0.0):
        i = int(t0 * SR)
        if i >= N or i < 0: return
        sig = np.asarray(sig, np.float32)[: N - i]
        l = gain * (1 - max(pan, 0)); r = gain * (1 + min(pan, 0))
        self.d[0, i:i + len(sig)] += sig * l; self.d[1, i:i + len(sig)] += sig * r
    def addstereo(self, t0, sl, sr_, gain=1.0):
        i = int(t0 * SR); n = min(len(sl), N - i)
        self.d[0, i:i + n] += sl[:n] * gain; self.d[1, i:i + n] += sr_[:n] * gain
    def gain_curve(self, pts):
        t = np.arange(N) / SR
        g = np.interp(t, [p[0] for p in pts], [p[1] for p in pts]).astype(np.float32)
        self.d *= g[None, :]


def reverb(x, sec=1.8, wet=0.3):
    n = int(sec * SR)
    ir = noise(sec) * np.exp(-np.arange(n) / (SR * sec / 4.5))
    ir = lp(ir, 5000)
    y = signal.fftconvolve(x, ir / np.sqrt(np.sum(ir ** 2)))[: len(x)]
    return x * (1 - wet) + y * wet


# ------------------------------------------------------------------ sound elements
def footstep(heavy=1.0, wet=True):
    n = int(0.22 * SR)
    th = np.sin(2 * np.pi * (70 + 40 * np.exp(-T(n) * 30)) * T(n)) * env(n, 0.002, 0.04)
    sc = bp(noise(0.22), 300, 2400) * env(n, 0.001, 0.025)
    sp = hp(noise(0.22), 3500) * env(n, 0.001, 0.02) * (0.4 if wet else 0.1)
    return (th * 0.9 + sc * 0.5 + sp * 0.25) * heavy


def entity_step():
    n = int(0.6 * SR)
    th = np.sin(2 * np.pi * (38 + 25 * np.exp(-T(n) * 12)) * T(n)) * env(n, 0.004, 0.15)
    cr = bp(noise(0.6), 80, 400) * env(n, 0.003, 0.12)
    return (th + 0.4 * cr) * 1.1


def breath(dur=0.7, sharp=False, gain=1.0):
    n = int(dur * SR); t = T(n)
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** (1.5 if not sharp else 0.8)
    return bp(noise(dur), 500, 3500) * e * gain * (1.5 if sharp else 1.0)


def vib(dur, f=170):
    n = int(dur * SR); t = T(n)
    am = (np.sign(np.sin(2 * np.pi * 22 * t)) * 0.5 + 0.5)
    x = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.02 * t)) * am
    x += bp(noise(dur), 100, 900) * am * 0.4
    return x * np.minimum(t / 0.01, 1) * np.minimum((dur - t) / 0.03, 1)


def ping(f=1318, dur=1.0):
    n = int(dur * SR); t = T(n)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.5 * t)) * env(n, 0.002, 0.18)


def notify():
    return np.concatenate([ping(1175, 0.25), ping(1568, 0.8)[: int(0.8 * SR)]]) if False else None


def click(gain=1.0):
    n = int(0.25 * SR)
    c = hp(noise(0.25), 1500) * env(n, 0.0005, 0.01)
    th = np.sin(2 * np.pi * 120 * T(n)) * env(n, 0.001, 0.05)
    zap = bp(noise(0.25), 2000, 9000) * env(n, 0.001, 0.05) * (np.sin(2 * np.pi * 120 * T(n)) > 0)
    return (c * 0.9 + th * 0.8 + zap * 0.5) * gain


def buzz(dur, gain=1.0, f=100):
    n = int(dur * SR); t = T(n)
    x = np.sign(np.sin(2 * np.pi * f * t)) * 0.4 + np.sin(2 * np.pi * f * 3 * t) * 0.2
    x += hp(noise(dur), 3000) * 0.15 * (np.sin(2 * np.pi * 7.3 * t) > -0.2)
    return lp(x, 4000) * gain * np.minimum(t / 0.02, 1) * np.minimum((dur - t) / 0.05, 1)


def metallic(f0=420, dur=2.5):
    n = int(dur * SR); t = T(n)
    x = sum(np.sin(2 * np.pi * f0 * r * t + i) * np.exp(-t / (dur / (1 + 0.5 * i))) for i, r in enumerate([1, 2.76, 5.4, 8.93, 11.3]))
    x = x * env(n, 0.001, dur / 2)
    return reverb(x * 0.4, 2.0, 0.5)


def glass(dur, f=2093):
    n = int(dur * SR); t = T(n)
    vib_ = 1 + 0.003 * np.sin(2 * np.pi * 5.2 * t)
    x = sum(np.sin(2 * np.pi * f * r * vib_ * t + i * 1.3) * (0.6 / (1 + i)) for i, r in enumerate([1, 1.5, 2.01, 2.99]))
    x *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.37 * t + 1)
    return x * smoothstep(t / 2.0) * smoothstep((dur - t) / 1.0)


def drone(dur, f=55, gain=1.0, rise=0.0):
    n = int(dur * SR); t = T(n)
    x = sum(np.sin(2 * np.pi * f * m * (1 + 0.0006 * k) * t + k) * a for k, (m, a) in enumerate([(1, 1.0), (1.5, 0.45), (2, 0.35), (3.01, 0.15)]))
    x += np.sin(2 * np.pi * (f * 1.0 + 0.7) * t) * 0.6
    x = np.tanh(x * (1 + 1.2 * rise)) * 0.5
    return x * gain


def pad(dur, notes, gain=1.0):
    n = int(dur * SR); t = T(n); x = np.zeros(n)
    for f in notes:
        for dt in (-0.4, 0.0, 0.5):
            x += signal.sawtooth(2 * np.pi * (f + dt) * t + rng.uniform(0, 6)) * 0.12
    x = lp(x, 900, 2)
    x *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t))
    return x * gain


def heartbeat(gain=1.0):
    n = int(0.5 * SR); t = T(n)
    a = np.sin(2 * np.pi * 52 * t) * env(n, 0.005, 0.07)
    b = np.sin(2 * np.pi * 46 * t) * env(n, 0.005, 0.08)
    out = np.zeros(n); out += a
    k = int(0.19 * SR); out[k:] += 0.75 * b[: n - k]
    return out * gain


def boom(dur=3.5):
    n = int(dur * SR); t = T(n)
    x = np.sin(2 * np.pi * (34 + 60 * np.exp(-t * 6)) * t) * env(n, 0.003, 0.9)
    x += lp(noise(dur), 160) * env(n, 0.003, 0.7) * 0.9
    return reverb(x, 2.5, 0.35)


def cloth(dur=0.5):
    n = int(dur * SR)
    return bp(noise(dur), 700, 5000) * (0.3 + 0.7 * np.abs(np.sin(np.linspace(0, 6, n)))) * env(n, 0.02, dur / 2)


# ------------------------------------------------------------------ build stems
amb, mus, sfx = Track(), Track(), Track()

# --- ambience: rain bed (stereo decorrelated), wind, city, constant low room tone
rl = bp(noise(DUR), 900, 9000, 2) * 0.10 + hp(noise(DUR), 6500) * 0.02
rr = bp(noise(DUR), 900, 9000, 2) * 0.10 + hp(noise(DUR), 6500) * 0.02
amb.addstereo(0, rl, rr, 1.0)
t = T(N)
wind = bp(noise(DUR), 120, 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t + 1)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.17 * t)) ** 1.5
amb.add(0, wind * 0.22)
city = lp(noise(DUR), 220) * 0.18
amb.add(0, city)
amb.add(0, buzz(DUR, 0.02, 100))

# --- footsteps (global times) --------------------------------------------------------------
def steps(t0, t1, iv0, iv1=None, heavy=1.0, pan=0.0, ent=False):
    t_ = t0; k = 0; iv1 = iv0 if iv1 is None else iv1
    while t_ < t1:
        iv = iv0 + (iv1 - iv0) * (t_ - t0) / max(t1 - t0, 1e-6)
        sig = footstep(heavy * (1.0 if k % 2 else 0.88))
        sfx.add(t_, sig * 0.5, 1.0, pan + (0.15 if k % 2 else -0.15))
        t_ += iv; k += 1

steps(0.2, 6.0, 0.43, 0.43, 0.7)
steps(6.0, 9.5, 0.43, 0.43, 0.85)
steps(9.5, 14.0, 0.43, 0.30, 0.9)
steps(14.1, 14.1, 1)
for tt in (0.9, 2.2, 3.55, 3.75, 5.15, 5.3):  # entity: slow, wrong-footed steps
    sfx.add(tt + 0.0, entity_step(), 0.55, 0.15)
steps(6.3, 9.5, 0.9, 0.9, 0.0)
for tt in np.arange(10.0, 14.0, 0.62): sfx.add(tt, entity_step(), 0.5, -0.1)
sfx.add(14.1, entity_step(), 0.55, -0.1)
steps(26.0, 30.0, 0.43, 0.55, 0.9)
for tt in (39.4, 39.85, 40.3): sfx.add(tt, footstep(0.8) * 0.6, 1.0, -0.2)
steps(63.0, 74.0, 0.26, 0.26, 1.15)
steps(74.0, 79.0, 0.26, 0.42, 1.0)
steps(79.0, 80.0, 0.3, 0.3, 1.1)
for tt in (80.15, 80.35, 80.55): sfx.add(tt, footstep(0.8) * 0.6)
for tt in (94.3, 94.9, 95.5): sfx.add(tt, footstep(0.6) * 0.5)

# --- breathing
for tt in np.arange(63.2, 79.0, 0.62): sfx.add(tt, breath(0.5, True, 0.35), 1.0)
for tt in np.arange(14.5, 17.0, 1.4): sfx.add(tt, breath(0.9, False, 0.2), 1.0)
for tt in np.arange(46.5, 53.0, 1.0): sfx.add(tt, breath(0.7, True, 0.3), 1.0)
sfx.add(80.15, breath(0.5, True, 0.7), 1.0)
for tt in np.arange(81.0, 88.0, 1.6): sfx.add(tt, breath(0.8, False, 0.12), 1.0)
for tt in np.arange(88.0, 95.0, 0.7): sfx.add(tt, breath(0.5, True, 0.35), 1.0)
sfx.add(98.5, breath(1.2, False, 0.25))
sfx.add(102.5, breath(1.0, True, 0.4))

# --- phone
sfx.add(17.5, vib(1.1) * 0.5)
sfx.add(20.3, vib(0.5) * 0.4); sfx.add(20.9, reverb(ping(1175, 0.4) + ping(1568, 1.0)[: int(0.4 * SR)] * 0, 0.5, 0.15) * 0.45)
sfx.add(20.95, ping(1568, 1.0) * 0.4)
sfx.add(43.0, vib(0.9) * 0.55)
sfx.add(46.5, vib(0.5) * 0.4); sfx.add(47.2, ping(1175, 0.5) * 0.45); sfx.add(47.25, ping(1568, 1.0) * 0.4)
sfx.add(48.9, vib(0.5) * 0.4); sfx.add(49.2, ping(1175, 0.5) * 0.5); sfx.add(49.25, ping(1568, 1.0) * 0.45)

# --- glass reflection scene (26-43): resonance, tension, sudden silence at 38.0
sfx.add(30.6, glass(7.4, 2093) * 0.10, 1.0)
sfx.add(34.0, glass(4.0, 3136) * 0.07, 1.0, 0.3)
sfx.add(36.0, hp(noise(2.0), 7000) * smoothstep(T(2 * SR) / 2.0) * 0.05, 1.0)
sfx.add(38.5, glass(4.0, 2637) * 0.03, 1.0)   # faint residue inside the silence
sfx.add(39.35, cloth(0.5) * 0.4)

# --- electrical / lights
for tt in np.arange(44.0, 53.0, 0.37):
    if abs(np.sin(tt * 37.3)) > 0.55: sfx.add(tt, click(0.4), 1.0, rng.uniform(-0.4, 0.4))
sfx.add(44.0, buzz(8.5, 0.12, 100) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * T(int(8.5 * SR)))), 1.0)
for tt in (55.3, 57.6, 59.9):
    for k in range(4): sfx.add(tt - 0.5 + k * 0.12, click(0.5))
    sfx.add(tt, click(1.0), 1.0, 0.2); sfx.add(tt, boom(1.2) * 0.2, 1.0)
sfx.add(58.3, metallic(380, 3.0) * 0.5, 1.0, 0.6)
sfx.add(61.0, metallic(520, 3.0) * 0.4, 1.0, -0.7)
sfx.add(62.2, metallic(300, 2.0) * 0.5, 1.0, 0.4)

# --- the collision and the doubles
sfx.add(80.0, boom(1.5) * 0.5, 1.0); sfx.add(80.0, cloth(0.5) * 0.6, 1.0)
sfx.add(88.0, cloth(0.6) * 0.6)
for tt in np.arange(88.8, 91.5, 0.35): sfx.add(tt, cloth(0.35) * rng.uniform(0.3, 0.6), 1.0, rng.uniform(-0.3, 0.3))
sfx.add(93.0, cloth(0.7) * 0.5)
sfx.add(94.0, cloth(0.7) * 0.4)

# --- final reveal
sfx.add(101.6, boom(3.0) * 0.8)
sfx.add(100.0, metallic(150, 4.0) * 0.4, 1.0, 0.0)
sfx.add(103.0, metallic(95, 1.5) * 0.35)

# --- music: pad, pulse, risers (restrained)
mus.add(0.0, pad(26.0, [55, 82.4, 110.0, 130.8]) * smoothstep(T(26 * SR) / 6.0) * 0.5)
mus.add(24.0, pad(20.0, [55, 77.8, 110.0, 116.5]) * 0.45)
mus.add(41.0, pad(24.0, [49.0, 73.4, 98.0, 116.5]) * 0.5)
mus.add(62.0, pad(46.0, [55, 82.4, 103.8, 130.8]) * 0.55)
mus.add(0.0, drone(106, 55, 0.12))
mus.add(43.0, drone(20, 41.2, 0.2, 1.0) * smoothstep(T(20 * SR) / 12.0))
mus.add(96.0, drone(8.4, 36.7, 0.5, 2.0) * smoothstep(T(int(8.4 * SR)) / 7.0))
# pulse: heartbeat accelerating during the escape
tt = 63.0; iv = 0.9
while tt < 79.0:
    mus.add(tt, heartbeat(0.6)); tt += iv; iv = max(0.38, iv - 0.025)
# rising riser before the first reveal and before the final reveal
rs = hp(noise(8.0), 2500) * smoothstep(T(8 * SR) / 8.0) ** 2 * 0.08
mus.add(21.0, bp(noise(4.0), 300, 3000) * smoothstep(T(4 * SR) / 4.0) * 0.04)
mus.add(88.0, rs); mus.add(53.0 + 3.0, bp(noise(6), 200, 2400) * smoothstep(T(6 * SR) / 6.0) * 0.05)
for tt in (33.0, 56.0, 98.0):
    n = int(5 * SR); tv = T(n)
    mus.add(tt, np.sin(2 * np.pi * (220 * (1 + 0.5 * tv / 5)) * tv) * smoothstep(tv / 5) * 0.03)

# ------------------------------------------------------------------ automation & export
mus.gain_curve([(0, 0), (4, 0.7), (37.9, 0.7), (38.0, 0.05), (43.0, 0.05), (45, 0.8), (79.9, 0.9), (80.05, 0.15), (88, 0.15), (92, 0.7), (104.3, 1.0), (104.45, 0.0), (108, 0)])
amb.gain_curve([(0, 0.8), (37.9, 0.9), (38.02, 0.04), (42.8, 0.04), (43.2, 0.8), (79.9, 0.9), (80.05, 0.5), (88, 0.6), (104.3, 0.8), (104.45, 0), (108, 0)])
sfx.gain_curve([(0, 1), (37.9, 1), (38.02, 0.12), (43.0, 0.12), (43.05, 1), (104.3, 1), (104.45, 0), (108, 0)])


def norm_export(tr, name, peak):
    d = tr.d
    m = np.max(np.abs(d)) + 1e-9
    d = d / m * peak
    fade = np.ones(N, np.float32); fade[: int(0.05 * SR)] = np.linspace(0, 1, int(0.05 * SR))
    d = d * fade[None, :]
    wavfile.write(os.path.join(OUT, name), SR, (np.clip(d.T, -1, 1) * 32767).astype(np.int16))
    return d


a = norm_export(amb, 'ambience.wav', 0.5)
m = norm_export(mus, 'music.wav', 0.5)
s = norm_export(sfx, 'sfx.wav', 0.7)
mix = a * 0.75 + m * 0.7 + s * 0.9
mix = np.tanh(mix * 1.1) / 1.1
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.85
wavfile.write(os.path.join(OUT, 'mix_no_voice.wav'), SR, (mix.T * 32767).astype(np.int16))
print('audio ok')
