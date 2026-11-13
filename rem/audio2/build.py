"""Procedural synthesis of the music / ambience / foley / sfx stems (unscaled; mix.py calibrates levels).
Everything is seeded; no samples or downloads."""
import json, os
import numpy as np
from scipy import signal
from dsp import *

HERE = os.path.dirname(os.path.abspath(__file__))
FOLEY_JSON = os.path.join(HERE, "foley_events.json")
ALIGN = os.path.join(HERE, "..", "subs", "align.json")

# ---- global automation shared by stems ---------------------------------------------------------
def dip_curve():
    """'Air pressure' dropouts applied to music/ambience/foley (reflection 38.6-42.1, collision 64.9)."""
    d = np.ones(N)
    d *= 1 - 0.85 * bump(38.6, 39.4, 41.9, 43.4)           # reflection stops responding
    d *= 1 - 0.9 * bump(64.88, 64.92, 65.35, 66.6)         # ringing silence after impact
    d *= 1 - 0.5 * bump(105.4 - 0.01, 105.4, 105.4, 105.45)  # (cut handled in ambience)
    return d

# ==== MUSIC =========================================================================================
TENSION = [(0, 0.0), (1.5, 0.22), (3, 0.38), (9, 0.30), (17, 0.34), (19, 0.30), (24, 0.42), (38, 0.50),
           (43, 0.58), (45, 0.55), (52, 0.70), (56, 0.80), (59, 0.88), (65, 0.82), (71, 0.74), (74, 0.80),
           (93, 0.86), (95.5, 1.0), (101, 0.85), (104, 0.62), (105.5, 0.50), (107, 0.25), (108.3, 0.04), (108.4, 0.04)]

def build_music():
    r = rng(11)
    f = 4  # synthesise at SR/4 then resample (drones are band-limited)
    sr = SR // f
    n = N // f + 1
    t = np.arange(n) / sr
    ten = np.interp(t, *np.array(TENSION).T)
    ten_s = signal.lfilter([0.002], [1, -0.998], ten)  # slow
    ten = 0.5 * ten + 0.5 * ten_s * 1.0
    lfo = lambda rate, ph=0: np.sin(2 * np.pi * rate * t + ph)

    def tone(freq, amps, ph0=0):
        ph = 2 * np.pi * np.cumsum(freq) / sr + ph0
        out = np.zeros(n)
        for k, a in enumerate(amps, 1):
            out += a * np.sin(k * ph + r.uniform(0, 6.28)) * (1 + 0.25 * lfo(0.021 * k + 0.01, r.uniform(0, 6)))
        return out

    # D1: low ominous drone (A1) slowly detuned
    d1 = tone(55.0 * 2 ** (6 * lfo(0.037) / 1200), [1, .5, .33, .2, .12, .07])
    # D2: minor-2nd partner above the octave; interval wanders between ~85 and ~125 cents
    d2 = tone(110.0 * 2 ** ((105 + 20 * lfo(0.029, 1)) / 1200), [1, .4, .2, .1]) * (0.5 + 0.5 * ten)
    # D3: tritone, enters with tension
    d3 = tone(110.0 * 2 ** ((600 + 12 * lfo(0.023, 2)) / 1200), [1, .3, .12]) * ten ** 2 * 1.2
    # sub with a barely perceptible slow pulse (soft sine swell, not percussion)
    pr = 0.38 + 0.12 * ten
    pulse = (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(pr) / sr)) ** 3
    sub = np.sin(2 * np.pi * np.cumsum(36.7 * np.ones(n)) / sr) * (0.35 + 0.65 * pulse) * 1.1
    # FM texture (cold, glassy), index follows tension
    idx = 0.4 + 2.2 * ten * (0.5 + 0.5 * lfo(0.047))
    mph = 2 * np.pi * np.cumsum(220 * 1.4142 * np.ones(n)) / sr
    fm = np.sin(2 * np.pi * np.cumsum(220 * np.ones(n)) / sr + idx * np.sin(mph)) * 0.22 * (0.2 + ten)
    fm = lp(fm, 1000, 2)
    # resonant-noise "choir" bed on a cluster (C#4 / D4 / G#4), amplitude swells independently
    pad = np.zeros(n)
    for fc, ph in zip([277.2, 293.7, 415.3, 554.4], [0, 2, 4, 1]):
        w = r.standard_normal(n)
        b = bp(w, fc * 0.985, fc * 1.015, 2)
        b /= (np.std(b) + 1e-9)
        pad += b * (0.5 + 0.5 * lfo(0.031 + 0.007 * ph, ph)) ** 1.5
    pad *= 0.08 * (0.3 + ten)
    # dark air: very low-passed noise
    air = lp(r.standard_normal(n), 140, 2)
    air = air / np.std(air) * 0.25 * (0.4 + 0.6 * ten)

    bed = (d1 * (0.6 + 0.4 * ten) + d2 * 0.55 + d3 * 0.5 + sub * 0.7 + fm + pad + air)
    bed = hp(bed, 28, 2)
    bed48 = signal.resample_poly(bed, f, 1)[:N]
    bed48 = np.pad(bed48, (0, N - len(bed48)))

    # inharmonic metallic resonances (struck/bowed bar partials, long decay)
    metal = np.zeros(N)
    rm = rng(23)
    ratios = [1, 2.76, 5.40, 8.93, 13.34]
    amps = [1, .55, .3, .16, .08]
    taus = [4.0, 3.0, 2.0, 1.4, 0.9]
    for t0 in [6.2, 21.5, 34.5, 47.0, 62.0, 79.5, 90.5, 99.0]:
        base = rm.uniform(360, 640)
        L = int(9 * SR)
        tt = np.arange(L) / SR
        sig = np.zeros(L)
        for ra, a, tau in zip(ratios, amps, taus):
            att = np.clip(tt / 0.35, 0, 1) ** 2  # soft, bowed onset
            sig += a * np.sin(2 * np.pi * base * ra * tt * (1 - 0.002 * tt) + rm.uniform(0, 6)) * att * np.exp(-tt / tau)
        sig *= 0.5 + 0.5 * np.sin(2 * np.pi * rm.uniform(0.4, 0.9) * tt) ** 2 * 0.6
        i0 = int(t0 * SR)
        e = min(N, i0 + L)
        gm = 0.12 + 0.08 * float(np.interp(t0, *np.array(TENSION).T))
        metal[i0:e] += sig[:e - i0] * gm
    # reverb: long synthetic IR (6 s, dark), metals get much more wet
    ir = ir_reverb(6.0, 31, decay_db=60, lp_hz=5000, predelay=0.03)
    bed2 = to_stereo(bed48 * np.interp(T, *np.array([(0, 0), (1.5, 1), (100, 1), (108.4, 1)]).T))
    wet = convolve_stereo(bed2, ir)
    bed2 = bed2 * 0.7 + wet * 0.9 * np.sqrt(np.sum(ir[0] ** 2))
    mw = convolve_stereo(to_stereo(metal), ir_reverb(8.0, 37, decay_db=60, lp_hz=7000, predelay=0.05))
    # slow stereo drift on the dry drone
    music = bed2 + mw * 2.2 + to_stereo(metal) * 0.25
    # overall level automation: fade in from silence, long tail to the final line
    lvl = curve([(0, 0), (1.5, 0.5), (6, 0.8), (105.5, 0.9), (108.3, 0.0), (108.4, 0.0)])
    ten_g = 0.5 + 0.5 * np.interp(T, *np.array(TENSION).T)
    music = music * (lvl * ten_g)
    return music * dip_curve()

# ==== AMBIENCE ======================================================================================
def build_ambience(events):
    n = N
    r = rng(5)
    G = lambda pts, tau=0.6: smooth_curve(pts, tau)
    LAMPS = [56.6, 57.37, 58.2]

    # rain: bright hiss + dull hiss + sparse drops, decorrelated L/R
    def rain_ch(seed):
        rr = rng(seed)
        w = rr.standard_normal(n)
        bright = bp(w, 1800, 9500, 2)
        dull = lp(bp(rr.standard_normal(n), 400, 3000, 2), 1800, 2) * 1.4
        mod = 1 + 0.18 * lp(rr.standard_normal(n), 0.6, 1) / 0.12
        imp = np.zeros(n)
        k = int(30 * DUR)
        idx = rr.integers(0, n, k)
        imp[idx] = rr.exponential(1.0, k) ** 1.5
        drops = bp(imp, 2500, 7500, 2) * 3.0
        # a few resonant puddle plinks
        pl = np.zeros(n)
        for i in rr.integers(0, n - 4000, int(2.2 * DUR)):
            tt = np.arange(2400) / SR
            fq = rr.uniform(1400, 3200)
            pl[i:i + 2400] += rr.uniform(.3, 1.0) * np.sin(2 * np.pi * fq * (1 + 6 * tt) * tt) * np.exp(-tt / 0.012)
        return bright * mod, dull * mod, drops, pl
    rb = [rain_ch(101), rain_ch(102)]
    bright_w = G([(0, 1), (17, 1), (21, .85), (24, .6), (43, .55), (45, 1), (56.5, 1), (56.8, .8), (57.4, .65), (58.2, .35),
                  (59.2, .95), (63, .8), (64.5, .35), (93, .35), (95, .55), (105.4, .5)], 0.7)
    rain_g = G([(0, 0), (1.5, 0.9), (17, .9), (24, .75), (43, .6), (45, .9), (60, 1.0), (64, .8), (93, .7), (105.4, .8)], .7)
    rain = np.zeros((2, n))
    for c in range(2):
        b, d, dr, pl = rb[c]
        rain[c] = (b * bright_w * 0.55 + d * (1 - bright_w * 0.6) * 0.45 + dr * bright_w * 0.35 + pl * 0.05) * rain_g

    # traffic: brown rumble + occasional distant pass-bys
    tr = np.stack([lp(rng(7 + c).standard_normal(n), 220, 2) * 4 for c in range(2)])
    tr_swell = 0.7 + 0.3 * lp(rng(9).standard_normal(n), 0.15, 1) / 0.06
    for t0 in [4.5, 13.0, 31.0, 48.5, 62.5, 80.0, 99.0]:
        tt = (T - t0)
        e = np.exp(-0.5 * (tt / 1.6) ** 2)
        car = bp(rng(int(t0 * 10)).standard_normal(n), 140 + 80 * 0, 700, 2) * e * 1.8
        pan = np.clip(0.5 + 0.5 * np.tanh(tt / 2.0), 0, 1)
        if rng(int(t0)).random() < 0.5:
            pan = 1 - pan
        tr[0] += car * (1 - pan)
        tr[1] += car * pan
    tr_g = G([(0, 0), (2, .8), (17, .75), (24, .45), (43, .4), (45, .75), (56.5, .75), (56.8, .25), (60, .3), (64, .2),
              (93, .22), (97, .35), (105.4, .4)], .6)
    tr = tr * tr_swell * tr_g * 0.35

    # wind: gusting band noise, rising on the roof
    wd = np.stack([bp(rng(13 + c).standard_normal(n), 90, 650, 2) * 3 for c in range(2)])
    wd_hi = np.stack([bp(rng(17 + c).standard_normal(n), 500, 1500, 2) for c in range(2)])
    gust = np.clip(0.55 + 0.45 * lp(rng(19).standard_normal(n), 0.35, 1) / 0.08, 0.1, 1.6)
    wind_g = G([(0, .3), (24, .3), (43, .25), (50, .35), (57.4, .35), (57.5, .15), (63, .1), (65, .2), (93, .22),
                (95.2, .5), (99, 0.95), (105.3, 1.4), (105.4, 1.4)], 1.2)
    wind_hi_g = G([(0, 0), (95, 0), (101, .5), (105.3, 1.0)], 1.5)
    wind = (wd * wind_g + wd_hi * wind_hi_g * 0.6) * gust * 0.25

    # lamp buzz layers (100 Hz mains hum + harmonics + crackle), dying lamp by lamp
    def buzz(f0, t0, t1, death, seed, level, harm=8):
        i0, i1 = int(t0 * SR), int(t1 * SR)
        tt = np.arange(i1 - i0) / SR + t0
        rr = rng(seed)
        f = f0 * np.ones_like(tt)
        amp = np.clip((tt - t0) / 0.8, 0, 1) * level
        if death is not None:
            x = np.clip((tt - death) / 0.4, 0, 1)
            f = f0 * (1 - 0.55 * x ** 0.6)
            flick = (rr.random(len(tt)) > 0.5)
            fl = onepole(flick.astype(float), 0.015)
            amp = amp * np.where(tt < death, 1.0, np.clip(1 - x, 0, 1) ** 1.5 * (0.4 + fl))
        ph = 2 * np.pi * np.cumsum(f) / SR
        s = sum(np.sin(k * ph + rr.uniform(0, 6)) / (k ** 0.9) for k in range(1, harm + 1))
        am = 1 + 0.35 * lp(rr.standard_normal(len(tt)), 25, 1) / 0.5
        crack = bp(rr.standard_normal(len(tt)), 3000, 9000, 1) * (rr.random(len(tt)) > 0.9985) * 6
        s = (s * am + crack)
        out = np.zeros(n)
        out[i0:i1] = s * amp
        return out
    buzz_L = np.zeros(n); buzz_R = np.zeros(n)
    specs = [(100.0, LAMPS[0], 0.55, -0.6), (100.45, LAMPS[1], 0.5, 0.0), (99.6, LAMPS[2], 0.55, 0.6)]
    for j, (f0, td, lv, pn) in enumerate(specs):
        b = buzz(f0, 45.0, td + 0.9, td, 60 + j, lv * 0.02)
        # build-up: buzz more present as the lights begin to fail
        b *= 0.5 + 0.5 * np.clip((T - 45) / 11, 0, 1)
        buzz_L += b * (1 - pn) / 2 * 1.4
        buzz_R += b * (1 + pn) / 2 * 1.4
    # faint passing-streetlight / neon buzz bursts elsewhere
    for (a, b_, f0, lv, pn) in [(5.5, 9.0, 100.2, .012, -.4), (11.5, 14.3, 99.8, .01, .5), (29.5, 36.0, 120.0, .008, .3),
                                 (19.0, 22.0, 100.0, .006, .0)]:
        bb = buzz(f0, a, b_ + 0.5, None, int(a * 7), lv)
        bb *= bump(a, a + 1.2, b_ - 0.3, b_ + 0.5)
        buzz_L += bb * (1 - pn) / 2 * 1.4
        buzz_R += bb * (1 + pn) / 2 * 1.4
    # distant window hum in the courtyard (63-93)
    hum = np.zeros(n)
    hw = bump(62.5, 66, 91, 94) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * T))
    for fh, a in [(100, 1), (150, .5), (200, .35), (50, .5)]:
        hum += a * np.sin(2 * np.pi * fh * T + fh)
    hum = lp(hum, 400, 1) * hw * 0.006
    buzz_st = np.stack([buzz_L, buzz_R])

    amb = rain + tr + wind + buzz_st + np.stack([hum, hum * 0.8])

    # alley: tight, wet reflections of the ambience (59-64.5)
    ir_t = ir_reverb(0.45, 71, decay_db=50, lp_hz=8000, predelay=0.004)
    alley_w = bump(58.8, 59.6, 63.2, 64.8)
    wetamb = convolve_stereo(amb, ir_t) * alley_w
    amb = amb + wetamb * 0.9
    # high-passed boost for the narrow canyon feel
    amb = amb * dip_curve()
    # hard cut at 105.4 then faint room tone tail
    gate = curve([(0, 1), (105.5, 1), (108.3, 0.02), (108.4, 0.0)])
    amb = amb * gate
    rt = lp(rng(77).standard_normal(n), 260, 2) * 0.6
    rt += 0.02 * np.sin(2 * np.pi * 50 * T) + 0.012 * np.sin(2 * np.pi * 100 * T)
    rt_g = curve([(105.4, 0), (106.0, .5), (107.5, .3), (108.4, 0)])
    amb = amb + np.stack([rt, np.roll(rt, 37)]) * rt_g * 0.012
    return amb

# ==== FOLEY =========================================================================================
def default_foley():
    ev = []
    def stepseq(t0, t1, rate, who="hero", gain=1.0, kind="step", offset=0.0, accel_to=None):
        t = t0 + offset
        k = 0
        while t < t1:
            ev.append({"t": round(t, 3), "kind": kind, "foot": -1 if k % 2 == 0 else 1, "gain": gain, "who": who, "lin": True})
            rr = rate if accel_to is None else rate + (accel_to - rate) * (t - t0) / (t1 - t0)
            t += 1.0 / rr
            k += 1
    stepseq(0.35, 11.9, 1.9)
    stepseq(11.9, 14.3, 2.6, gain=1.1)
    stepseq(24.0, 36.2, 1.8, gain=0.8)   # unhurried approach to the shop window (placeholder cadence)
    # creature: heavier, slower, softer, offset
    stepseq(1.5, 6.0, 1.25, who="creature", gain=0.4, offset=0.28)
    stepseq(8.0, 14.3, 1.25, who="creature", gain=0.45, offset=0.28)
    ev.append({"t": 14.3, "kind": "scuff", "foot": 1, "gain": 0.8, "who": "hero"})
    ev.append({"t": 17.75, "kind": "rustle", "foot": 0, "gain": 0.55, "lin": True})   # hand into pocket for the phone
    ev.append({"t": 22.95, "kind": "rustle", "foot": 0, "gain": 0.35, "lin": True})
    ev.append({"t": 43.4, "kind": "rustle", "foot": 0, "gain": 0.8, "lin": True})     # recoil stumble
    ev.append({"t": 43.55, "kind": "step", "foot": -1, "gain": 1.2, "lin": True})
    ev.append({"t": 43.85, "kind": "step", "foot": 1, "gain": 0.9, "lin": True})
    stepseq(59.1, 64.85, 3.0, kind="run_step", gain=1.0, accel_to=4.2)
    t = 60.6
    while t < 63.0:
        ev.append({"t": round(t, 3), "kind": "breath", "foot": -1, "gain": 0.9, "lin": True})
        ev.append({"t": round(t + 0.38, 3), "kind": "breath", "foot": 1, "gain": 1.0, "lin": True})
        t += 0.86
    for ts in [59.7, 60.5, 61.2, 62.4, 63.6, 64.4]:
        ev.append({"t": ts, "kind": "splash", "foot": 0, "gain": 0.6, "lin": True})
    ev.append({"t": 65.35, "kind": "step", "foot": -1, "gain": 0.9, "lin": True})
    ev.append({"t": 66.05, "kind": "breath", "foot": 0, "gain": 0.6, "lin": True})
    ev.append({"t": 74.9, "kind": "rustle", "foot": 0, "gain": 1.0, "lin": True})     # grab
    ev.append({"t": 81.6, "kind": "rustle", "foot": 0, "gain": 0.8, "lin": True})     # struggle
    ev.append({"t": 82.2, "kind": "rustle", "foot": 0, "gain": 0.6, "lin": True})
    ev.append({"t": 90.4, "kind": "rustle", "foot": 0, "gain": 0.9, "lin": True})     # release
    ev.append({"t": 90.55, "kind": "step", "foot": -1, "gain": 0.8, "lin": True})
    ev.append({"t": 93.3, "kind": "step", "foot": 1, "gain": 0.7, "lin": True})
    ev.append({"t": 93.8, "kind": "step", "foot": -1, "gain": 0.6, "lin": True})
    return ev

def _norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)

def clip_step(rr, kind, who):
    L = int(0.45 * SR)
    t = np.arange(L) / SR
    if who == "creature":
        f = rr.uniform(42, 58)
        th = np.sin(2 * np.pi * f * (1 + 2 * np.exp(-t / .05)) * t) * np.exp(-t / 0.12)
        th += lp(rr.standard_normal(L), 130, 2) * np.exp(-t / 0.09) * 1.5
        sl = lp(rr.standard_normal(L), 1200, 2) * np.exp(-t / 0.05) * 0.5
        return _norm(th + sl) * 1.0
    run = kind == "run_step"
    f = rr.uniform(75, 120) * (1.15 if run else 1)
    thump = np.sin(2 * np.pi * f * (1 + 1.5 * np.exp(-t / .02)) * t) * np.exp(-t / (0.035 if run else 0.05))
    thump += lp(rr.standard_normal(L), 220, 2) * np.exp(-t / 0.04) * 1.3
    squelch = bp(rr.standard_normal(L), 600, 2600, 2) * np.exp(-t / (0.022 if run else 0.03)) * (0.7 if run else 0.55)
    heel = hp(rr.standard_normal(L), 2200, 2) * np.exp(-t / 0.006) * 0.5       # heel tick on wet stone
    splash = hp(rr.standard_normal(L), 3500, 2) * np.exp(-t / 0.09) * rr.uniform(0.25, 0.5) * (1.4 if run else 1)
    return _norm(thump * 0.8 + squelch + heel + splash)

def clip_splash(rr):
    L = int(0.5 * SR)
    t = np.arange(L) / SR
    w = bp(rr.standard_normal(L), 900, 7000, 2) * np.exp(-t / 0.07) * np.clip(t / .004, 0, 1)
    dr = sum(np.sin(2 * np.pi * rr.uniform(1500, 3500) * t) * np.exp(-(t - rr.uniform(.04, .25)).clip(0) / .02) * (t > .04) * .08 for _ in range(4))
    return _norm(w + dr * 0.5 + lp(rr.standard_normal(L), 300, 2) * np.exp(-t / .05) * 0.6)

def clip_rustle(rr, dur=0.45):
    L = int(dur * SR)
    t = np.arange(L) / SR
    base = bp(rr.standard_normal(L), 700, 6500, 2)
    env = np.zeros(L)
    for _ in range(rr.integers(4, 8)):
        c = rr.uniform(0.05, dur - 0.05)
        env += rr.uniform(.3, 1) * np.exp(-0.5 * ((t - c) / rr.uniform(.012, .05)) ** 2)
    env = onepole(env, 0.004) * np.clip(t / .03, 0, 1) * np.clip((dur - t) / .08, 0, 1)
    return _norm(base * env)

def clip_scuff(rr):
    L = int(0.32 * SR)
    t = np.arange(L) / SR
    n_ = bp(rr.standard_normal(L), 900, 5000, 2)
    env = np.exp(-0.5 * ((t - 0.1) / 0.06) ** 2)
    th = lp(rr.standard_normal(L), 160, 2) * np.exp(-t / .04) * 0.5
    return _norm(n_ * env + th)

def clip_breath(rr, exhale):
    dur = 0.42 if not exhale else 0.5
    L = int(dur * SR)
    t = np.arange(L) / SR
    w = rr.standard_normal(L)
    if exhale:
        x = bp(w, 350, 2400, 2) + 0.7 * bp(w, 700, 1000, 2) * 2
        env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5 * (1 - 0.4 * t / dur)
    else:
        x = bp(w, 500, 3200, 2) + 0.9 * bp(w, 1500, 1900, 2) * 2
        env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.2 * (0.5 + 0.5 * t / dur)
    turb = np.clip(1 + 0.4 * lp(rr.standard_normal(L), 40, 1) / 0.1, 0.3, 2)
    return _norm(x * env * turb)

def clip_impact(rr):
    L = int(0.6 * SR)
    t = np.arange(L) / SR
    th = np.sin(2 * np.pi * 70 * (1 + 0.6 * np.exp(-t / .08)) * t) * np.exp(-t / 0.12)
    th += lp(rr.standard_normal(L), 200, 2) * np.exp(-t / 0.05) * 1.5
    cl = bp(rr.standard_normal(L), 500, 5000, 2) * np.exp(-0.5 * ((t - 0.04) / 0.05) ** 2) * 0.7
    return _norm(th + cl)

def build_foley():
    if os.path.exists(FOLEY_JSON):
        ev = json.load(open(FOLEY_JSON))
        src = "foley_events.json"
    else:
        ev = default_foley()
        src = "default cadence"
    rr = rng(41)
    buf = np.zeros((2, N))
    for e in ev:
        t0, kind = float(e["t"]), e.get("kind", "step")
        g = float(e["gain"]) if e.get("lin") else 10 ** (float(e.get("gain", 0.0)) / 20)
        foot = float(e.get("foot", 0))
        who = e.get("who", "hero")
        pan = 0.18 * foot
        if kind in ("step", "run_step"):
            x = clip_step(rr, kind, who)
            gg = g * (0.8 if kind == "step" and who != "creature" else 0.9 if kind == "run_step" else 0.7)
            place(buf, x, t0, gg, pan * (1 if who != "creature" else -2))
            if who != "creature" and rr.random() < 0.5:  # cloth swing with the step
                place(buf, clip_rustle(rr, 0.3), t0 + 0.03, gg * 0.09, 0)
        elif kind == "rustle":
            place(buf, clip_rustle(rr), t0, g * 0.35, rr.uniform(-.3, .3))
        elif kind == "breath":
            x = clip_breath(rr, foot > 0)
            place(buf, x, t0, g * 0.45, rr.uniform(-.1, .1))
        elif kind == "splash":
            place(buf, clip_splash(rr), t0, g * 0.5, pan)
        elif kind == "impact":
            place(buf, clip_impact(rr), t0, g * 0.9, 0)
        elif kind == "scuff":
            place(buf, clip_scuff(rr), t0, g * 0.6, 0.25)
        else:
            place(buf, clip_rustle(rr, 0.3), t0, g * 0.3, 0)
    # space: small outdoor reflection; wetter in the alley
    ir = ir_reverb(0.5, 91, decay_db=55, lp_hz=7000, predelay=0.006)
    wet = convolve_stereo(buf, ir)
    wmix = 0.10 + 0.35 * bump(58.8, 59.5, 63.5, 64.8)
    out = buf + wet * wmix * 3
    return out * dip_curve(), src, ev
