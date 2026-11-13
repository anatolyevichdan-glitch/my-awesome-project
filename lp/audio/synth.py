"""Procedural one-shot clip synthesizers (mono, peak-normalised to 1.0). All seeded."""
import numpy as np
from scipy import signal
from lib import SR, rng, bp, lp, hp, expenv, onepole


def _t(n):
    return np.arange(n) / SR


def norm(x):
    return x / (np.abs(x).max() + 1e-12)


def fade(x, a=0.002, b=0.004):
    x = x.copy()
    na, nb = int(a * SR), int(b * SR)
    if na > 1: x[:na] *= np.linspace(0, 1, na)
    if nb > 1: x[-nb:] *= np.linspace(1, 0, nb)
    return x


def modes(freqs, taus, amps, dur, seed=0):
    t = _t(int(dur * SR))
    r = rng(seed)
    y = np.zeros_like(t)
    for f, tau, a in zip(freqs, taus, amps):
        y += a * np.sin(2 * np.pi * f * t + r.uniform(0, 6.28)) * np.exp(-t / tau)
    return y


# ----- footsteps -----
def step(kind, seed):
    r = rng(seed)
    if kind == "wet":      # soft sole on wet pavement
        n = int(0.28 * SR); t = _t(n)
        body = bp(r.standard_normal(n), 180, 1400) * expenv(n, 0.035, 0.002)
        thump = np.sin(2 * np.pi * r.uniform(70, 95) * t) * np.exp(-t / 0.03)
        slosh = bp(r.standard_normal(n), 2500, 7500) * expenv(n, 0.07, 0.012) * 0.5
        x = body * 1.0 + thump * 0.8 + slosh
    elif kind == "run_wet":
        n = int(0.24 * SR); t = _t(n)
        body = bp(r.standard_normal(n), 200, 1800) * expenv(n, 0.03, 0.001)
        thump = np.sin(2 * np.pi * r.uniform(80, 110) * t) * np.exp(-t / 0.028)
        slosh = bp(r.standard_normal(n), 2000, 8000) * expenv(n, 0.06, 0.006) * 0.7
        x = body + thump + slosh
    elif kind == "metal":  # shoe on bus floor (ribbed metal)
        n = int(0.4 * SR); t = _t(n)
        thud = lp(r.standard_normal(n), 400, 2) * expenv(n, 0.03, 0.001)
        ring = modes([r.uniform(480, 560), r.uniform(1150, 1300), 2300], [0.07, 0.05, 0.03], [0.5, 0.3, 0.15], 0.4, seed)
        x = thud * 1.5 + ring + np.sin(2 * np.pi * 85 * t) * np.exp(-t / 0.04)
    elif kind == "run_metal":
        n = int(0.3 * SR); t = _t(n)
        thud = lp(r.standard_normal(n), 500, 2) * expenv(n, 0.025, 0.001)
        ring = modes([r.uniform(520, 620), r.uniform(1200, 1400), 2500], [0.05, 0.035, 0.02], [0.6, 0.35, 0.2], 0.3, seed)
        x = thud * 1.5 + ring + np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.03)
    elif kind == "stair":  # step up onto bus step plate
        n = int(0.5 * SR); t = _t(n)
        thud = lp(r.standard_normal(n), 350, 2) * expenv(n, 0.04, 0.001)
        ring = modes([310, 740, 1480, 2210], [0.15, 0.1, 0.06, 0.04], [0.5, 0.4, 0.25, 0.12], 0.5, seed)
        x = thud * 1.4 + ring + np.sin(2 * np.pi * 75 * t) * np.exp(-t / 0.06)
    else:
        raise ValueError(kind)
    return norm(fade(x))


def rustle(dur, seed, lo=1500, hi=6500, rate=18, soft=1.0):
    r = rng(seed)
    n = int(dur * SR)
    x = bp(r.standard_normal(n), lo, hi)
    am = np.abs(onepole(r.standard_normal(n), 1 / rate / 2))
    am = am / am.max()
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    return norm(fade(x * (0.15 + am ** 1.5) * env, 0.02, 0.03)) * soft


def cloth_touch(seed):
    r = rng(seed)
    n = int(0.28 * SR)
    x = lp(r.standard_normal(n), 2500, 2) * expenv(n, 0.07, 0.04)
    x += 0.5 * rustle(0.25, seed + 1, 800, 3000)[:n] if False else 0
    return norm(fade(x, 0.03, 0.05))


def seat_creak(seed):
    r = rng(seed)
    n = int(0.7 * SR); t = _t(n)
    f = 330 + 110 * np.sin(2 * np.pi * 1.7 * t) + 60 * onepole(r.standard_normal(n), 0.03) * 8
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(k * ph) / k for k in range(1, 6))
    x = bp(x, 400, 2500) * (np.sin(np.pi * t / 0.7) ** 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t))
    return norm(fade(x, 0.05, 0.1))


def neck_crack(seed):
    r = rng(seed)
    out = np.zeros(int(0.9 * SR))
    for t0, a in [(0.05, 0.5), (0.18, 0.8), (0.27, 0.35)]:
        n = int(0.05 * SR)
        c = bp(r.standard_normal(n), 900, 3500) * expenv(n, 0.008, 0.0005)
        i = int(t0 * SR); out[i:i + n] += c * a
    n = int(0.5 * SR); t = _t(n)
    cr = bp(r.standard_normal(n), 300, 1400) * (0.5 + 0.5 * np.sin(2 * np.pi * 31 * t)) * np.sin(np.pi * t / 0.5)
    out[int(0.3 * SR):int(0.3 * SR) + n] += 0.25 * cr
    return norm(fade(out))


def scuff(seed):
    r = rng(seed)
    n = int(0.16 * SR)
    return norm(fade(bp(r.standard_normal(n), 500, 3200) * np.sin(np.pi * np.linspace(0, 1, n)) ** 0.7, 0.01, 0.04))


def clank(seed):
    t = _t(int(1.0 * SR))
    x = modes([383, 1129, 2217, 3187, 4310], [0.35, 0.22, 0.14, 0.09, 0.06], [0.6, 0.5, 0.3, 0.2, 0.1], 1.0, seed)
    r = rng(seed)
    n = int(0.03 * SR)
    x[:n] += lp(r.standard_normal(n), 3000) * expenv(n, 0.006) * 0.8
    x += np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.05) * 0.8
    return norm(fade(x))


def breath(kind, dur, seed):
    r = rng(seed)
    n = int(dur * SR)
    x = bp(r.standard_normal(n), 350, 3000) + 0.4 * bp(r.standard_normal(n), 1200, 1800)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** (1.2 if kind == "in" else 2.0)
    if kind == "out":
        e = np.linspace(0.6, 1.0, n) ** 0 * e
    return norm(fade(x * e, 0.04, 0.08))


def button_click(seed):
    r = rng(seed)
    n = int(0.05 * SR)
    x = hp(r.standard_normal(n), 1500) * expenv(n, 0.003, 0.0002)
    x += modes([2600, 4100], [0.012, 0.008], [0.5, 0.3], 0.05, seed)
    x += np.sin(2 * np.pi * 180 * _t(n)) * np.exp(-_t(n) / 0.015) * 0.6
    return norm(fade(x, 0.0003, 0.01))


def hand_thud(seed, size=0.25):
    r = rng(seed)
    n = int(size * SR); t = _t(n)
    x = np.sin(2 * np.pi * 130 * t) * np.exp(-t / 0.045)
    x += lp(r.standard_normal(n), 900, 2) * expenv(n, 0.03, 0.001) * 0.9
    x += modes([430, 960], [0.05, 0.04], [0.15, 0.1], size, seed)
    return norm(fade(x))


def splash(seed):
    r = rng(seed)
    n = int(0.4 * SR); t = _t(n)
    x = bp(r.standard_normal(n), 500, 5000) * expenv(n, 0.07, 0.003)
    x += 0.6 * bp(r.standard_normal(n), 3000, 9000) * expenv(n, 0.04, 0.001)
    x += np.sin(2 * np.pi * 120 * t) * np.exp(-t / 0.04) * 0.5
    return norm(fade(x))


def tap(seed):
    r = rng(seed)
    n = int(0.04 * SR)
    return norm(fade(bp(r.standard_normal(n), 1200, 4500) * expenv(n, 0.006, 0.0003) + np.sin(2 * np.pi * 800 * _t(n)) * np.exp(-_t(n) / 0.008) * 0.6, 0.0002, 0.01))


# ----- bus / pneumatic -----
def hiss(dur, seed, lo=2500, hi=11000, attack=0.025, shape=1.6):
    r = rng(seed)
    n = int(dur * SR); t = _t(n)
    x = bp(r.standard_normal(n), lo, hi, 2) + 0.3 * bp(r.standard_normal(n), 800, 2500)
    e = np.minimum(1, t / attack) * np.exp(-(t / dur) ** shape * 3.2)
    return norm(fade(x * e, 0.002, 0.03))


def squeal(dur, seed, f0=1700, f1=2500, wobble=35):
    r = rng(seed)
    n = int(dur * SR); t = _t(n)
    f = np.linspace(f0, f1, n) * (1 + 0.012 * np.sin(2 * np.pi * wobble * t)) + 20 * onepole(r.standard_normal(n), 0.01) * 10
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.5 * np.sin(2 * ph + 0.3) + 0.25 * np.sin(3 * ph)
    x += 0.3 * bp(r.standard_normal(n), 1500, 5000)
    e = np.sin(np.pi * t / dur) ** 0.8 * (0.75 + 0.25 * np.abs(onepole(r.standard_normal(n), 0.02)) / 0.05).clip(0.5, 1.2)
    return norm(fade(x * e, 0.02, 0.05))


def whoosh(dur, seed, f0=500, f1=2000, q=1.0):
    r = rng(seed)
    n = int(dur * SR); t = _t(n)
    x = r.standard_normal(n)
    out = np.zeros(n)
    nseg = 24
    L = n // nseg + 1
    for i in range(nseg):
        f = f0 * (f1 / f0) ** (i / (nseg - 1))
        seg = bp(x, max(60, f / 1.6), min(20000, f * 1.6), 2)[i * L:(i + 1) * L]
        out[i * L:i * L + len(seg)] = seg
    out = lp(out, 8000, 1)
    return norm(fade(out * np.sin(np.pi * t / dur) ** 1.6, 0.03, 0.05))


def tyre_screech(dur, seed):
    r = rng(seed)
    n = int(dur * SR); t = _t(n)
    f = 1050 + 500 * (t / dur) + 80 * np.sin(2 * np.pi * 7 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.6 * np.sin(2 * ph + 0.5) + 0.35 * np.sin(3 * ph)
    x = x * (0.7 + 0.3 * np.sin(2 * np.pi * 31 * t))
    x += bp(r.standard_normal(n), 1500, 6500) * 0.9
    e = np.minimum(1, t / 0.08) * np.exp(-(t / dur) ** 2 * 2.0)
    return norm(fade(x * e, 0.01, 0.1))


def metal_rattle(dur, seed, density=40):
    r = rng(seed)
    n = int(dur * SR)
    out = np.zeros(n)
    k = int(dur * density)
    for _ in range(k):
        i = int(r.uniform(0, 1) ** 1.4 * (n - 4000))
        f = r.uniform(600, 3200)
        m = int(0.06 * SR)
        out[i:i + m] += r.uniform(0.2, 1) * np.sin(2 * np.pi * f * _t(m) + 1) * np.exp(-_t(m) / 0.012)
    return norm(fade(out * np.linspace(1, 0.1, n) ** 0.6, 0.001, 0.05))


def body_lurch(seed):
    r = rng(seed)
    n = int(0.6 * SR); t = _t(n)
    x = lp(r.standard_normal(n), 260, 2) * np.sin(np.pi * np.minimum(1, t / 0.4)) ** 1.5
    x += 0.8 * np.sin(2 * np.pi * 55 * t) * np.exp(-t / 0.12)
    return norm(fade(x, 0.01, 0.1))


# ----- electrical -----
def flicker(dur, seed, intensity=1.0, clicks=True):
    """Fluorescent flicker: hum gated in short irregular bursts + ballast crackle."""
    r = rng(seed)
    n = int(dur * SR); t = _t(n)
    gate = np.zeros(n)
    i = 0
    on = True
    while i < n:
        seg = int(r.uniform(0.02, 0.14) * SR)
        if on: gate[i:i + seg] = 1
        i += seg
        on = not on if r.random() < 0.75 else on
    gate = onepole(gate, 0.004)
    hum = sum(np.sin(2 * np.pi * 100 * k * t + r.uniform(0, 6)) / k ** 0.8 for k in range(1, 8))
    buzz = bp(r.standard_normal(n), 3000, 9000) * 0.25 * (1 + np.sin(2 * np.pi * 100 * t))
    x = (hum * 0.6 + buzz) * gate
    if clicks:
        d = np.abs(np.diff(gate, prepend=0))
        idx = np.flatnonzero(d > 0.02 * d.max())
        last = -10 ** 9
        for j in idx:
            if j - last > 0.01 * SR and n - j > 200:
                m = min(int(0.012 * SR), n - j)
                x[j:j + m] += hp(r.standard_normal(m), 1500) * expenv(m, 0.003) * 1.2 * intensity
                last = j
    return norm(fade(x * intensity, 0.005, 0.03))


def lamp_pop(seed):
    r = rng(seed)
    n = int(0.45 * SR); t = _t(n)
    pop = hp(r.standard_normal(n), 900) * expenv(n, 0.005, 0.0003) * 1.0
    hum = sum(np.sin(2 * np.pi * 100 * k * t) / k for k in range(1, 5)) * np.exp(-t / 0.06) * 0.35
    buz = bp(r.standard_normal(n), 3000, 8000) * np.exp(-t / 0.05) * 0.25
    return norm(fade(pop + hum + buz, 0.0003, 0.05))


# ----- phone & tones -----
def bell_tone(freqs, dur, tau, seed=0, amps=None):
    t = _t(int(dur * SR))
    amps = amps or [1] * len(freqs)
    x = sum(a * (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / (tau * 0.4))) for f, a in zip(freqs, amps))
    return norm(fade(x * np.exp(-t / tau), 0.004, 0.05))


def seq(parts, gap=0.0):
    out = np.zeros(int(sum(len(p) / SR + gap for p in parts) * SR) + 1)
    i = 0
    for p in parts:
        out[i:i + len(p)] += p
        i += len(p) + int(gap * SR)
    return out


def low_battery_chime():
    a = bell_tone([660], 0.9, 0.25)
    b = bell_tone([523], 0.9, 0.3)
    return norm(seq([a[:int(0.2 * SR)], b], 0.0))


def validator_beep():
    def b(f, d):
        t = _t(int(d * SR))
        x = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * t)
        return fade(lp(x, 5000, 2), 0.004, 0.01)
    return norm(seq([b(2000, 0.07), np.zeros(int(0.03 * SR)), b(2800, 0.09)]))


def phone_vibe(dur=0.28, seed=0):
    r = rng(seed)
    n = int(dur * SR); t = _t(n)
    x = np.sin(2 * np.pi * 175 * t) * (1 + 0.5 * np.sin(2 * np.pi * 45 * t)) + 0.4 * bp(r.standard_normal(n), 300, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 90 * t))
    x = x * np.minimum(1, t / 0.01) * np.minimum(1, (dur - t) / 0.03)
    return norm(x)


def notification():
    a = bell_tone([1175], 0.5, 0.12)
    b = bell_tone([1568], 0.8, 0.2)
    out = np.zeros(int(1.2 * SR))
    out[:len(a)] += a * 0.8
    i = int(0.14 * SR); out[i:i + len(b)] += b
    return norm(out)


DTMF = {"1": (697, 1209), "2": (697, 1336), "3": (697, 1477), "4": (770, 1209), "5": (770, 1336), "6": (770, 1477),
        "7": (852, 1209), "8": (852, 1336), "9": (852, 1477), "0": (941, 1336)}


def dtmf(key):
    t = _t(int(0.07 * SR))
    f1, f2 = DTMF[key]
    return norm(fade((np.sin(2 * np.pi * f1 * t) + np.sin(2 * np.pi * f2 * t)), 0.004, 0.008))


def phone_band(x):
    return bp(x, 300, 3400, 2)


def ringback(dur=0.9):
    t = _t(int(dur * SR))
    x = np.sin(2 * np.pi * 425 * t)
    return norm(fade(phone_band(x), 0.02, 0.03))


def click_soft(seed):
    r = rng(seed)
    n = int(0.03 * SR)
    return norm(fade(bp(r.standard_normal(n), 800, 3500) * expenv(n, 0.004, 0.0002), 0.0002, 0.005))


def pulse_tick(seed):
    t = _t(int(0.18 * SR))
    x = np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.05) + 0.3 * np.sin(2 * np.pi * 220 * t) * np.exp(-t / 0.03)
    return norm(fade(x, 0.002, 0.03))


def heartbeat_beat(seed=0):
    t = _t(int(0.6 * SR))
    def thump(f0, f1, tau):
        f = f1 + (f0 - f1) * np.exp(-t / 0.03)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau)
    lub = thump(95, 55, 0.07)
    dub = thump(110, 62, 0.06)
    # mid-frequency body so it carries on phone speakers
    r = rng(seed)
    mid = lp(r.standard_normal(len(t)), 320, 2) * np.exp(-t / 0.035) * 0.7
    out = np.zeros(len(t))
    out += lub + mid
    i = int(0.22 * SR)
    out[i:] += 0.7 * (dub + mid)[:len(t) - i]
    return norm(fade(out, 0.003, 0.05))


def boom(dur=1.6, seed=0):
    """Low impact: pitch-dropping sine + sub + dark noise thump + metallic inharmonic hit."""
    r = rng(seed)
    n = int(dur * SR); t = _t(n)
    f = 38 + 60 * np.exp(-t / 0.12)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55) * 1.6
    body = lp(r.standard_normal(n), 380, 2) * np.exp(-t / 0.09)
    metal = modes([212, 547, 891, 1342, 2077], [0.7, 0.5, 0.4, 0.3, 0.2], [0.35, 0.3, 0.25, 0.15, 0.1], dur, seed) * np.minimum(1, t / 0.002)
    knock = bp(r.standard_normal(n), 1200, 4500) * np.exp(-t / 0.012) * 0.6
    return norm(fade(sub * 1.0 + body * 0.9 + metal * 0.6 + knock, 0.001, 0.2))


def sting(dur=0.95, seed=0):
    """Final shock: low boom + dissonant metallic cluster + noise slam. Short, clean."""
    r = rng(seed)
    n = int(dur * SR); t = _t(n)
    f = 36 + 70 * np.exp(-t / 0.09)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.14)
    body = lp(r.standard_normal(n), 500, 2) * np.exp(-t / 0.07)
    cl = np.zeros(n)
    for fr, a in [(466, 1.0), (494, 0.8), (932, 0.7), (1397, 0.55), (1976, 0.45), (2960, 0.3)]:
        cl += a * np.sin(2 * np.pi * fr * t * (1 + 0.004 * np.exp(-t / 0.3)) + r.uniform(0, 6)) * np.exp(-t / 0.13)
    shriek = bp(r.standard_normal(n), 1800, 7000) * np.exp(-t / 0.05) * 0.8
    slam = hp(r.standard_normal(n), 600) * np.exp(-t / 0.008) * 1.2
    x = sub * 1.0 + body * 0.8 + cl * 0.55 + shriek + slam
    return norm(fade(x, 0.0008, 0.12))
