"""Synthesize raw stems (music, ambience, foley, sfx) + event log. Levels here are provisional;
mix.py calibrates music/ambience against the narration and enforces the voice-relative guards.
Usage: python build.py   (writes cache/raw_*.npy and cache/events.json, ~1-2 min)"""
import json, sys, time
import numpy as np
from scipy import signal
from lib import *
import synth as S

t0_ = time.time()
CACHE = os.path.join(HERE, "cache")
os.makedirs(CACHE, exist_ok=True)
EV = []  # event log

# ---------------------------------------------------------------- helpers
IRS = {
    "int": (ir_reverb(0.30, 11, 50, 7000, 0, True, 200), 0.35),    # small metal bus box
    "ext": (ir_reverb(1.3, 12, 55, 3500, 0.01, True, 150), 0.28),  # wet street between buildings
    "big": (ir_reverb(2.2, 13, 55, 4500, 0.0, True, 100), 0.55),   # for the large impacts
    "phone": (ir_reverb(0.08, 14, 40, 6000, 0, True, 400), 0.12),
}


def put(buf, clip, t, peak_db, pan=0.0, space="int"):
    x = clip * 10 ** (peak_db / 20)
    place(buf, x, t, 1.0, pan)
    if space in IRS:
        ir, w = IRS[space]
        for c in range(2):
            wet = signal.fftconvolve(x, ir[c])
            i0 = int(round(t * SR))
            e = min(len(wet), N - i0)
            if e > 0:
                buf[c, i0:i0 + e] += wet[:e] * w


def ev(stem, t, name, peak_db, dur=0.0, prominent=False, **kw):
    EV.append(dict(t=round(float(t), 3), stem=stem, name=name, peak_dbfs=peak_db, dur=dur, prominent=prominent, **kw))


def gcurve(points_db, tau=0.03):
    """dB automation -> linear gain on the sample grid. Points (t, dB)."""
    p = np.array(points_db, float)
    g = np.interp(T, p[:, 0], p[:, 1])
    return 10 ** (onepole(g, tau) / 20)


def unit_rms(x):
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-12)


def stereo_noise(kind, seed):
    return np.stack([lowshelf_free_noise(rng(seed + c), N, kind) for c in range(2)])


# ---------------------------------------------------------------- AMBIENCE
def rain_layers():
    base = {}
    for c, name in enumerate(["L", "R"]):
        r = rng(100 + c)
        w = r.standard_normal(N)
        hi = bp(w, 1800, 9000, 2)
        body = lowshelf_free_noise(rng(110 + c), N, "pink")
        body = bp(body, 250, 2500, 2)
        sizzle = hp(rng(120 + c).standard_normal(N), 6000, 2)
        # density texture: slow irregular amplitude
        tex = 1 + 0.18 * onepole(rng(130 + c).standard_normal(N), 0.05) * 12
        # drops: sparse impulses hitting puddles
        k = int(N / SR * 260)
        idx = rng(140 + c).integers(0, N - 200, k)
        imp = np.zeros(N)
        imp[idx] = rng(150 + c).uniform(0.2, 1.0, k) ** 2
        drops = bp(signal.lfilter([1], [1, -0.985], imp), 2500, 8000, 1)
        base[name] = unit_rms(hi) * 0.8 * tex + unit_rms(body) * 0.9 + unit_rms(sizzle) * 0.35 + unit_rms(drops) * 0.45
    ext = np.stack([base["L"], base["R"]])
    roof = np.stack([lp(ext[c], 1400, 2) for c in range(2)])
    # roof drumming: resonant patter at ~330 / 780 Hz
    pat = np.stack([bp(ext[c], 280, 420, 2) * 1.6 + bp(ext[c], 650, 900, 2) * 0.9 for c in range(2)])
    roof = unit_rms(roof) * 0.6 + unit_rms(pat) * 0.5
    fog = np.stack([lp(ext[c], 3200, 2) for c in range(2)])
    return unit_rms(ext), unit_rms(roof), unit_rms(fog)


def traffic():
    out = stereo_noise("brown", 200)
    out = np.stack([lp(out[c], 260, 2) for c in range(2)])
    out = unit_rms(out) * (0.7 + 0.3 * np.sin(2 * np.pi * T / 17.0)[None])
    r = rng(210)
    for _ in range(14):  # distant pass-bys
        t0 = r.uniform(2, DUR - 6); d = r.uniform(4, 8); n = int(d * SR)
        x = bp(r.standard_normal(n), 120, 900, 2) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
        pan = r.uniform(-.8, .8)
        place(out, x * 1.5, t0, 1.0, pan)
    return unit_rms(out)


def wind():
    w = stereo_noise("pink", 300)
    w = np.stack([bp(w[c], 120, 700, 2) for c in range(2)])
    mod = 0.5 + 0.5 * onepole(rng(301).standard_normal(N), 1.0) * 8
    return unit_rms(w * np.clip(mod, 0.2, 1.5)[None])


RPM = [(0, 700), (6.5, 760), (9.5, 900), (9.8, 700), (17.9, 700), (18.0, 800), (18.9, 1150), (22, 1100), (40, 1250),
       (60, 1200), (80, 1250), (92.5, 1250), (92.62, 950), (93.1, 650), (93.4, 700), (99.95, 700), (100.4, 950),
       (101.6, 1200), (104, 1350), (108, 1400), (DUR, 1400)]


def engine():
    rpm = curve(RPM)
    rpm = rpm * (1 + 0.012 * onepole(rng(400).standard_normal(N), 0.2) * 8)
    f = rpm / 60 * 3.0  # 6-cyl 4-stroke diesel: 3 firings/rev
    ph = np.cumsum(f) / SR
    lope = 1 + 0.30 * onepole(rng(401).standard_normal(N), 0.12) * 5  # uneven idle
    x = np.zeros(N)
    for k in range(1, 30):
        fk = f * k
        a = (1.0 / k ** 0.9) * np.clip((1800 - fk) / 600, 0, 1)
        x += a * np.sin(2 * np.pi * k * ph + k * 0.7)
        if k % 7 == 0 and False:
            pass
    x *= np.clip(lope, 0.4, 2.0)
    # combustion knock
    wrap = np.flatnonzero(np.diff(np.floor(ph)) > 0)
    imp = np.zeros(N)
    imp[wrap] = rng(402).uniform(0.4, 1.0, len(wrap))
    knock = signal.lfilter([1], [1, -0.99], imp)  # ~2 ms ring-out
    knock = bp(knock, 700, 2600, 2)
    x = x / np.sqrt(np.mean(x ** 2)) + 0.5 * knock / np.sqrt(np.mean(knock ** 2))
    return x


def drive_layers():
    r = rng(500)
    road = lp(lowshelf_free_noise(rng(501), N, "brown"), 140, 2) * 1.0 + lp(lowshelf_free_noise(rng(502), N, "pink"), 450, 2) * 0.12
    # suspension clunks / bumps (low) and loose panel + window rattle
    sus = np.zeros((2, N))
    t = 18.0
    while t < 92.5:
        t += r.exponential(0.9)
        n = int(0.14 * SR); tt = np.arange(n) / SR
        c = (lp(r.standard_normal(n), 220, 2) * 0.8 + np.sin(2 * np.pi * r.uniform(70, 120) * tt)) * np.exp(-tt / r.uniform(0.03, 0.07))
        c += 0.4 * np.sin(2 * np.pi * r.uniform(300, 520) * tt) * np.exp(-tt / 0.03)
        place(sus, c * r.uniform(0.3, 1.0), t, 1.0, r.uniform(-.5, .5))
    rat = np.zeros((2, N))
    for c in range(2):
        nz = bp(rng(510 + c).standard_normal(N), 900, 3800, 2)
        gate = onepole(np.abs(onepole(rng(520 + c).standard_normal(N), 0.05)), 0.03)
        gate = np.clip((gate / np.percentile(gate, 99) - 0.55) * 2.2, 0, 1)
        rat[c] = nz * gate
    window = np.stack([bp(rng(530 + c).standard_normal(N), 160, 330, 2) * (0.3 + onepole(np.abs(rng(531 + c).standard_normal(N)), 0.1) * 8)
                       for c in range(2)])
    return unit_rms(np.stack([road, road])), unit_rms(sus), unit_rms(rat), unit_rms(window)


def hum_layer():
    out = np.zeros((2, N))
    r = rng(600)
    for c in range(2):
        x = sum(np.sin(2 * np.pi * 100.0 * k * T + r.uniform(0, 6)) / k ** 0.9 for k in range(1, 9))
        x += 0.3 * bp(r.standard_normal(N), 4000, 9000) * (1 + 0.7 * np.sin(2 * np.pi * 100 * T))
        out[c] = x
    return unit_rms(out)


def build_ambience():
    ext, roof, fog = rain_layers()
    trf, wnd = traffic(), wind()
    eng = engine()
    eng_int = np.stack([peaking(lp(eng, 850, 2), 110, 5, 1.2)] * 2)
    eng_int[1] = np.roll(eng_int[1], 7)
    eng_ext = np.stack([lp(eng, 520, 2)] * 2)
    eng_ext[1] = np.roll(eng_ext[1], 5)
    road, sus, rat, win = drive_layers()
    hum = hum_layer()
    unit = lambda x: x / np.sqrt(np.mean(x[:, :int(10 * SR)] ** 2))
    eng_int, eng_ext = unit_rms(eng_int), unit_rms(eng_ext)

    off = -70
    G = {}
    G["rain_ext"] = gcurve([(0, 0), (9.6, 0), (10.5, -22), (17.9, -30), (18.1, -45), (94.7, -45), (95.0, -4), (96.4, -6), (104.6, -6),
                            (108.4, -6), (108.7, -24), (112.4, -24), (113.0, -12), (118, -10), (126.5, -8), (127.1, -8), (127.4, -34),
                            (132.8, -34), (132.81, off), (DUR, off)], 0.05)
    G["roof"] = gcurve([(0, off), (10.0, off), (10.4, -9), (18, -8), (92.5, -8), (92.56, off), (93.5, off), (94.6, -12), (94.9, off), (DUR, off)], 0.04)
    G["fog_extra"] = gcurve([(0, off), (95.0, off), (96.0, -9), (104.6, -9), (108.4, -9), (108.7, -30), (113, -20), (127.1, -16), (127.4, off), (DUR, off)], 0.05)
    G["traffic"] = gcurve([(0, -6), (9.6, -6), (10.5, -22), (18, -26), (92.5, -26), (92.56, off), (94.8, off), (95.3, -10), (108.4, -10), (108.7, -30),
                           (112.4, -30), (113, -14), (127, -12), (127.4, -36), (132.8, -36), (132.81, off), (DUR, off)], 0.08)
    G["wind"] = gcurve([(0, -22), (9.6, -22), (10.5, -40), (94.8, -40), (95.5, -18), (108.4, -18), (108.7, -34), (113, -22), (127, -18),
                        (127.4, -40), (132.8, -40), (132.81, off), (DUR, off)], 0.1)
    G["eng_ext"] = gcurve([(0, off), (6.5, -34), (8.0, -22), (9.5, -12), (10.1, -12), (10.7, off), (94.8, off), (95.3, -12), (99.9, -12),
                           (100.5, -15), (102.5, -26), (104.2, -44), (104.6, off), (DUR, off)], 0.06)
    G["eng_int"] = gcurve([(0, off), (10.05, off), (10.5, -4), (17.9, -4), (18.2, -5), (92.5, -5), (92.56, off), (93.35, off), (93.55, -4),
                           (94.8, -4), (95.4, -30), (98.4, off), (DUR, off)], 0.03)
    G["hum"] = gcurve([(0, off), (10.1, off), (10.8, -17), (92.0, -17), (92.55, off), (DUR, off)], 0.02)
    G["road"] = gcurve([(0, off), (17.9, off), (18.8, -14), (92.5, -14), (92.56, off), (DUR, off)], 0.15)
    G["sus"] = gcurve([(0, off), (17.9, off), (18.8, -17), (92.5, -17), (92.56, off), (DUR, off)], 0.05)
    G["rat"] = gcurve([(0, off), (17.9, off), (19, -26), (92.5, -26), (92.56, off), (DUR, off)], 0.05)
    G["win"] = gcurve([(0, off), (17.9, off), (19, -22), (92.5, -22), (92.56, off), (DUR, off)], 0.05)
    amb = (ext * G["rain_ext"] + fog * G["fog_extra"] + roof * G["roof"] + trf * G["traffic"] + wnd * G["wind"]
           + eng_ext * G["eng_ext"] + eng_int * G["eng_int"] + hum * G["hum"] + road * G["road"] + sus * G["sus"]
           + rat * G["rat"] + win * G["win"])
    # exterior reverb flavour is inherent in the layers; add slight early-reflection smear in the first 10 s
    for a, b, d in [(0, 10.2, "outdoor street"), (10.2, 92.55, "bus interior, moving"), (92.55, 93.4, "blackout (interior bed cut)"),
                    (93.4, 94.84, "bus idle"), (95.0, 108.4, "exterior, fog-muffled"), (108.6, 112.6, "near silence + faint rain"),
                    (112.6, 127.1, "exterior, low drone"), (127.1, 132.8, "near silence, faint rain/room tone")]:
        ev("ambience", a, d, None, dur=b - a)
    return amb


# ---------------------------------------------------------------- FOLEY + SFX
def build_foley_sfx():
    F = np.zeros((2, N)); X = np.zeros((2, N))
    r = rng(900)

    def foley(t, kind, peak, pan=0.0, space="int", seed=None, **kw):
        s = int(t * 1000) if seed is None else seed
        clip = {
            "step_wet": lambda: S.step("wet", s), "run_wet": lambda: S.step("run_wet", s), "step_metal": lambda: S.step("metal", s),
            "run_metal": lambda: S.step("run_metal", s), "stair": lambda: S.step("stair", s),
            "rustle": lambda: S.rustle(kw.get("dur", 0.6), s, kw.get("lo", 1500), kw.get("hi", 6500)),
            "cloth": lambda: S.cloth_touch(s), "creak": lambda: S.seat_creak(s), "neck": lambda: S.neck_crack(s),
            "scuff": lambda: S.scuff(s), "clank": lambda: S.clank(s), "breath_in": lambda: S.breath("in", kw.get("dur", 0.45), s),
            "breath_out": lambda: S.breath("out", kw.get("dur", 0.5), s), "button": lambda: S.button_click(s),
            "thud": lambda: S.hand_thud(s, kw.get("size", 0.25)), "splash": lambda: S.splash(s), "tap": lambda: S.tap(s),
            "squeak": lambda: S.squeal(0.18, s, 2100, 2600, 55),
        }[kind]()
        put(F, clip, t, peak, pan, space)
        ev("foley", t, kind, peak, dur=len(clip) / SR)

    def sfx(t, name, clip, peak, pan=0.0, space="int", prominent=False):
        put(X, clip, t, peak, pan, space)
        ev("sfx", t, name, peak, dur=len(clip) / SR, prominent=prominent)

    # --- scene 1: exterior
    sfx(0.2, "college door squeak", S.squeal(0.22, 21, 1900, 2400, 50) * 0.3, -30, -0.4, "ext")
    foley(0.3, "thud", -30, -0.4, "ext", size=0.2)
    t = 0.42
    while t < 2.8:
        foley(t, "step_wet", -20 + r.uniform(-1.5, 1), 0.1 * (t % 1 - .5), "ext"); t += 0.526
    sfx(3.2, "low-battery chime", S.low_battery_chime(), -26, 0.0, "phone")
    t = 4.62
    while t < 6.0:
        foley(t, "step_wet", -20 + r.uniform(-1.5, 1), 0.0, "ext"); t += 0.526
    # --- bus arrives (engine in ambience)
    sfx(9.3, "air-brake hiss", S.hiss(1.0, 31, 2800, 11000, 0.06), -30, 0.3, "ext")
    sfx(9.5, "brake squeal", S.squeal(0.55, 32, 2300, 3100, 22) * 0.6, -33, 0.3, "ext")
    sfx(9.72, "door squeal", S.squeal(0.45, 33, 1500, 2300, 28), -29, 0.3, "ext")
    sfx(9.9, "door pneumatic opening", S.hiss(0.6, 34, 2500, 10000, 0.02), -30, 0.3, "ext")
    foley(10.5, "stair", -22, 0.2, "int"); foley(11.0, "stair", -22, 0.1, "int")
    # --- scene 2
    sfx(13.9, "fluorescent flicker", S.flicker(0.55, 41, 1.0), -34, 0.0, "int")
    sfx(15.2, "validator beep", S.validator_beep(), -30, -0.3, "int")
    foley(16.3, "rustle", -33, 0, "int", dur=0.55, lo=800, hi=5000)
    foley(16.9, "rustle", -33, 0.3, "int", dur=0.6, lo=800, hi=5000)
    foley(17.0, "creak", -32, 0.3, "int")
    sfx(17.95, "door close hiss", S.hiss(0.7, 42, 2500, 10000, 0.02), -30, 0.0, "int")
    sfx(18.05, "door clunk", S.hand_thud(43, 0.3) * 0.8, -31, 0.0, "int")
    sfx(18.2, "bus lurch (pulling away)", S.body_lurch(44), -32, 0, "int")
    for tt in (23.8, 29.6):
        sfx(tt, "shelter whoosh (passing stop)", S.whoosh(1.1, 45, 400, 1500), -35, 0.7, "int")
    sfx(30.5, "light flicker", S.flicker(0.7, 46, 1.0), -33, 0.0, "int")
    for i, tt in enumerate([31.8, 32.2, 32.62, 33.02, 33.4]):
        foley(tt, "step_metal", -21 + r.uniform(-1.5, 1), 0.0, "int", seed=2000 + i)
    sfx(32.5, "light flicker", S.flicker(0.5, 47, 0.9), -33, 0.0, "int")
    foley(36.9, "cloth", -33, -0.2, "int", seed=51)
    foley(39.0, "neck", -34, -0.2, "int", seed=52)
    foley(42.9, "scuff", -28, 0, "int", seed=53)
    foley(43.2, "clank", -24, 0.4, "int", seed=54)
    sfx(44.3, "turn whoosh", S.whoosh(0.4, 55, 300, 3200), -27, 0, "int")
    sfx(44.5, "horror impact", S.boom(1.7, 56), -9, 0, "big", prominent=True)
    foley(49.7, "rustle", -30, 0, "int", dur=0.55, lo=800, hi=5000)
    for tt, d, s in [(51.2, 0.5, 61), (52.5, 0.45, 62), (53.8, 0.5, 63), (55.0, 0.6, 64)]:
        sfx(tt, "ceiling light flicker (old woman)", S.flicker(d, s, 0.9), -33, 0.2, "int")
    foley(52.0, "creak", -38, 0.5, "int", seed=65)
    # --- panic
    for i, tt in enumerate([59.95, 60.28, 60.6, 60.92, 61.22]):
        foley(tt, "run_metal", -19 + r.uniform(-1, 1), 0, "int", seed=3000 + i)
    for tt in (61.5, 62.0, 62.5):
        foley(tt, "button", -26, 0.5, "int")
    foley(63.3, "thud", -24, -0.3, "int", size=0.25, seed=71)
    foley(63.45, "thud", -27, 0.3, "int", size=0.2, seed=72)
    foley(63.35, "breath_in", -33, 0, "int", dur=0.4, seed=73)
    foley(63.8, "breath_out", -33, 0, "int", dur=0.45, seed=74)
    foley(64.25, "breath_in", -36, 0, "int", dur=0.4, seed=75)
    for tt in (64.4, 65.0):
        sfx(tt, "phone vibration", S.phone_vibe(0.28, int(tt * 10)), -29, 0.0, "phone")
    for tt in (66.4, 68.3, 69.7):
        sfx(tt, "message notification", S.notification(), -28, 0.0, "phone")
    foley(73.4, "tap", -33, 0, "phone", seed=81)
    # --- heartbeat (sfx stem), tick pulses
    def beats(ta, tb, bpm_a, bpm_b, peak):
        t = ta
        while t < tb:
            bpm = bpm_a + (bpm_b - bpm_a) * (t - ta) / (tb - ta)
            put(X, S.heartbeat_beat(int(t * 100)), t, peak * (0.9 + 0.1 * (t - ta) / (tb - ta)), 0, None)
            ev("sfx", t, "heartbeat", peak, dur=0.6)
            t += 60 / bpm
    beats(76.0, 88.0, 60, 80, -30)
    beats(88.0, 92.5, 80, 80, -29)
    beats(114.0, 127.0, 60, 72, -36)
    for i, tt in enumerate([82.3, 83.46, 84.4, 85.06, 86.08, 86.72, 87.56]):
        sfx(tt, f"count pulse {i + 1}", S.pulse_tick(i), -34, 0, None)
    # --- blackout
    for i, tt in enumerate([92.0, 92.14, 92.28, 92.42]):
        sfx(tt, "light pop", S.lamp_pop(90 + i), -31 - i * 0.0, (i - 1.5) * 0.3, "int")
    sfx(92.52, "final light dies", S.lamp_pop(99) * 1.0, -30, 0, "int")
    sfx(92.62, "tyre/brake screech", S.tyre_screech(0.85, 100), -31, 0, "int", prominent=True)
    sfx(92.68, "body lurch", S.body_lurch(101), -27, 0, "int")
    sfx(92.75, "metal rattle", S.metal_rattle(0.9, 102), -33, 0, "int")
    sfx(94.84, "door pneumatic opening", S.hiss(0.8, 110, 2500, 10000, 0.02), -29, 0.0, "int")
    sfx(94.86, "door squeal", S.squeal(0.5, 111, 1500, 2200, 30), -30, 0.0, "int")
    # --- escape
    for i, tt in enumerate([98.45, 98.73, 99.01, 99.29, 99.57]):
        foley(tt, "run_wet", -19 + r.uniform(-1, 1), 0.0, "ext", seed=4000 + i)
    foley(99.0, "splash", -25, 0.1, "ext", seed=121)
    sfx(99.95, "door close hiss", S.hiss(0.7, 122, 2500, 10000, 0.02), -31, 0.4, "ext")
    sfx(100.05, "door close thunk", S.hand_thud(123, 0.3) * 0.7, -33, 0.4, "ext")
    foley(101.7, "breath_out", -30, 0, "ext", dur=0.8, seed=124)
    for i, k in enumerate("8916231"):
        sfx(103.0 + 0.14 * i, f"dial tone {k}", S.phone_band(S.dtmf(k)), -37, 0, "phone")
    sfx(104.02, "ringback", S.ringback(0.5), -37, 0, "phone")
    foley(104.6, "tap", -31, 0, "phone", seed=125)
    # --- finale
    sfx(124.9, "faint high tone (wave)", S.bell_tone([3135], 1.8, 0.9) * 0.7, -48, 0.3, None)
    sfx(132.3, "SHOCK STING", S.sting(0.95, 7), -4, 0, "big", prominent=True)
    return F, X


# ---------------------------------------------------------------- MUSIC
def build_music():
    tens = curve([(0, .15), (6.5, .15), (11.7, .3), (17, .3), (36, .45), (38, .5), (41, .65), (44.3, .55), (46.5, .35), (55.8, .5),
                  (59.5, .55), (62, .6), (74, .55), (92.5, 1.0), (92.56, .0), (94.8, .0), (97.5, .25), (104.6, .22), (108.4, .2),
                  (108.7, .02), (112.4, .02), (118.3, .35), (127.0, 1.0), (127.1, 0), (DUR, 0)])
    tens = onepole(tens, 0.4)
    out = np.zeros((2, N))
    for c, d in enumerate([-0.12, 0.12]):
        r = rng(700 + c)
        wob = 1 + 0.003 * onepole(r.standard_normal(N), 2.0) * 25
        # sub + fifth
        sub = np.sin(2 * np.pi * np.cumsum(36.71 * wob + d) / SR) * 1.0 + 0.6 * np.sin(2 * np.pi * np.cumsum(55.0 * wob - d) / SR)
        # pad: D2 cluster with minor second / tritone, additive harmonics
        pad = np.zeros(N)
        for f0, a in [(73.42, 1.0), (77.78, 0.7), (103.83, 0.5), (146.83 + d * 2, 0.4)]:
            ph = 2 * np.pi * np.cumsum(f0 * wob + d) / SR
            for k in range(1, 9):
                pad += a * np.sin(k * ph + r.uniform(0, 6)) / k ** 1.3
        pad_dark, pad_bright = lp(pad, 380, 2), lp(pad, 2400, 2)
        pad = pad_dark * (1 - tens) + pad_bright * tens
        padlfo = 0.75 + 0.25 * np.sin(2 * np.pi * T / 9.0 + c)
        # high dissonant shimmer rising with tension
        hi = (np.sin(2 * np.pi * np.cumsum(1480 + 6 * np.sin(2 * np.pi * T * 0.2) + d) / SR)
              + np.sin(2 * np.pi * np.cumsum(1568 + d) / SR)) * (0.5 + 0.5 * np.sin(2 * np.pi * T / 6.0 + 2 * c)) * tens ** 2.5
        # air / noise swell
        air = bp(lowshelf_free_noise(rng(710 + c), N, "pink"), 150, 1200, 2) * (0.5 + 0.5 * np.sin(2 * np.pi * T / 13 + c * 1.3)) * (0.3 + tens)
        # risers 74-92.5 and 118.3-127.1: noise sweep + gliss
        riser = np.zeros(N)
        for a, b in [(74.0, 92.5), (118.3, 127.1)]:
            i0, i1 = int(a * SR), int(b * SR)
            u = np.linspace(0, 1, i1 - i0)
            f = 180 * (3.2 ** u)
            g = np.sin(2 * np.pi * np.cumsum(f + d * 3) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5 + d * 3) / SR)
            nz = bp(rng(720 + c + i0).standard_normal(i1 - i0), 250, 1800, 1)
            riser[i0:i1] = (g * 0.5 + nz * 0.7) * u ** 2.2
        # low dissonant drone while old woman speaks
        diss = (np.sin(2 * np.pi * np.cumsum(98 + d + 0 * T) / SR) + np.sin(2 * np.pi * np.cumsum(103.8 + d + 0 * T) / SR) * 0.9
                + 0.5 * np.sin(2 * np.pi * np.cumsum(207.6 + d) / SR)) * bump(55.3, 56.3, 59.6, 60.8)
        out[c] = (sub * 0.7 * (0.8 + 0.5 * tens) + pad * padlfo * 0.9 + hi * 0.12 + air * 0.5 + riser * 0.6 + diss * 0.35)
    # metallic resonances (bells with long reverb)
    for tt in [6.2, 21.5, 34.5, 47.0, 62.0, 80.0, 99.0, 115.0, 122.0]:
        f0 = rng(int(tt * 10)).uniform(330, 520)
        m = S.modes([f0, f0 * 2.41, f0 * 3.77, f0 * 5.43], [2.5, 1.6, 1.0, 0.6], [1, .6, .35, .2], 4.0, int(tt)) * np.minimum(1, np.arange(int(4 * SR)) / SR / 0.04)
        place(out, m * 0.35, tt, 1.0, rng(int(tt)).uniform(-.6, .6))
    # reverb (long, dark hall)
    ir = ir_reverb(3.2, 800, 55, 3500, 0.02, True, 80)
    wet = np.stack([signal.oaconvolve(out[c], ir[c])[:N] for c in range(2)])
    out = 0.7 * out + 0.55 * wet
    # music stops completely at 127.1 and stays silent (hard zero after short fade)
    g = np.interp(T, [0, 1.5, 92.5, 92.55, 94.6, 97.0, 126.96, 127.1, 127.2, DUR], [0, 1, 1, 0, 0, 1, 1, 0, 0, 0])
    ev("music", 0, "drone/pad music bed", None, dur=127.1)
    ev("music", 92.55, "music cut at blackout", None)
    ev("music", 127.1, "MUSIC STOPS COMPLETELY", None)
    return out * g[None]


if __name__ == "__main__":
    t = time.time()
    amb = build_ambience(); print("ambience", round(time.time() - t, 1), flush=True)
    F, X = build_foley_sfx(); print("foley/sfx", round(time.time() - t, 1), flush=True)
    M = build_music(); print("music", round(time.time() - t, 1), flush=True)
    for k, v in [("ambience", amb), ("foley", F), ("sfx", X), ("music", M)]:
        np.save(os.path.join(CACHE, f"raw_{k}.npy"), v.astype(np.float32))
    json.dump(EV, open(os.path.join(CACHE, "events.json"), "w"), indent=1, ensure_ascii=False)
    print("done", round(time.time() - t0_, 1))
