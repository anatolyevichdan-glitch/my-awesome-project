"""Supernatural / event SFX stem. Each accent is a different, restrained sound."""
import numpy as np
from scipy import signal
from dsp import *


def pv_pitch(x, semis, n_fft=2048, hop=512):
    """Phase-vocoder pitch shift preserving duration (creature voice)."""
    rho = 2 ** (semis / 12.0)
    win = np.hanning(n_fft)
    pad = np.pad(x, (n_fft, n_fft))
    F = 1 + (len(pad) - n_fft) // hop
    frames = np.stack([pad[i * hop:i * hop + n_fft] * win for i in range(F)])
    X = np.fft.rfft(frames, axis=1)
    # time-scale by rho (keeps pitch), then resample back to the original length -> pitch * rho
    steps = np.arange(0, F - 1, 1.0 / rho)
    omega = 2 * np.pi * hop * np.arange(X.shape[1]) / n_fft
    phase = np.angle(X[0])
    out = np.zeros(len(steps) * hop + n_fft)
    wsum = np.zeros_like(out)
    for k, s in enumerate(steps):
        i = int(s)
        fr = s - i
        mag = (1 - fr) * np.abs(X[i]) + fr * np.abs(X[i + 1])
        dphi = np.angle(X[i + 1]) - np.angle(X[i]) - omega
        dphi -= 2 * np.pi * np.round(dphi / (2 * np.pi))
        y = np.fft.irfft(mag * np.exp(1j * phase)) * win
        out[k * hop:k * hop + n_fft] += y
        wsum[k * hop:k * hop + n_fft] += win ** 2
        phase += omega + dphi
    out /= np.maximum(wsum, 1e-3)
    out = out[n_fft:n_fft + int(len(x) * rho)]
    return signal.resample(out, len(x))


def notif(buf, t0, tau, gain, pan=0.0):
    for k, (fq, dt) in enumerate([(784.0, 0.0), (1174.7, 0.13)]):
        L = int(1.2 * SR)
        t = np.arange(L) / SR
        x = np.sin(2 * np.pi * fq * t + 0.8 * np.exp(-t / .03) * np.sin(2 * np.pi * fq * 2 * t))
        x += 0.18 * np.sin(2 * np.pi * fq * 2.76 * t) * np.exp(-t / (tau * .4))
        x *= np.exp(-t / tau) * np.clip(t / 0.004, 0, 1)
        place(buf, lp(x, 5000, 1), t0 + dt, gain * (1.0 if k == 0 else 0.8), pan)


def swell(f_list, amps, t0, t_peak, t1, lpf=300, saw=False, seed=0):
    """Slow bowed-drone swell between t0..t1 (peak at t_peak). Returns mono (N,)."""
    r = rng(seed)
    up = np.clip((T - t0) / (t_peak - t0), 0, 1) ** 2
    dn = np.clip((t1 - T) / (t1 - t_peak), 0, 1) ** 1.5
    env = np.where(T < t_peak, up, dn)
    out = np.zeros(N)
    i0, i1 = int(t0 * SR), int(t1 * SR)
    tt = T[i0:i1]
    seg = np.zeros(i1 - i0)
    for f, a in zip(f_list, amps):
        ff = f * (1 + 0.003 * np.sin(2 * np.pi * 0.31 * tt + r.uniform(0, 6)))
        ph = 2 * np.pi * np.cumsum(ff) / SR
        if saw:
            seg += a * sum(np.sin(k * ph) / k for k in range(1, 6))
        else:
            seg += a * np.sin(ph)
    out[i0:i1] = lp(seg, lpf, 2) * env[i0:i1]
    return out


def lamp(buf, t0, k):
    r = rng(300 + k)
    L = int(2.0 * SR)
    t = np.arange(L) / SR
    click = hp(r.standard_normal(L), 1500, 2) * np.exp(-t / (0.004 + 0.003 * k))
    thump = np.sin(2 * np.pi * (95 - 18 * k) * (1 + 0.8 * np.exp(-t / .03)) * t) * np.exp(-t / (0.09 + 0.05 * k))
    f0 = [118, 100, 86][k]
    f = f0 * (1 - 0.6 * (1 - np.exp(-t / [0.35, 0.5, 0.7][k])))
    ph = 2 * np.pi * np.cumsum(f) / SR
    bz = sum(np.sin(h * ph) / h for h in range(1, 7))
    benv = np.exp(-t / [0.22, 0.35, 0.28][k])
    if k == 1:
        benv = benv * (0.4 + 0.6 * (np.sin(2 * np.pi * 17 * t) > 0))
    bz = lp(bz, 2500, 1) * benv
    f1, f2, d = [(620, 150, .6), (470, 95, .8), (330, 52, 1.3)][k]
    ft = f2 + (f1 - f2) * np.exp(-t / (d * 0.35))
    tone = np.sin(2 * np.pi * np.cumsum(ft) / SR) * np.exp(-t / (d * 0.5)) * np.clip(t / .01, 0, 1)
    sig = click * 0.5 + thump * (0.9 + 0.3 * k) + bz * 0.5 + tone * [0.28, 0.3, 0.35][k]
    place(buf, sig, t0, 1.0, [-0.5, 0.0, 0.5][k])


def build_sfx(narr_mono, align):
    buf = np.zeros((2, N))
    log = []

    def L(t, name, moment, prominent, desc):
        log.append({"t": round(float(t), 3), "name": name, "moment": moment, "prominent": prominent, "desc": desc})
    r = rng(500)

    # 1) shadow appears
    sh = swell([41.2, 82.4, 123.0], [1.0, 0.35, 0.12], 1.2, 2.3, 3.8, lpf=220, seed=1)
    nz = lp(r.standard_normal(N), 160, 2) * bump(1.4, 2.3, 2.5, 3.6) * 0.5
    buf += to_stereo((sh * 0.9 + nz) * 0.5)
    L(1.2, "shadow_swell", 1, True, "low-frequency swell + sub pressure change 1.2-3.8 s")

    # 2) phone vibration (2 pulses) + soft notification
    for t0 in [17.60, 18.05]:
        Ld = int(0.34 * SR)
        t = np.arange(Ld) / SR
        ph = 2 * np.pi * 172 * t
        m = np.sin(ph) + .55 * np.sin(2 * ph) + .3 * np.sin(3 * ph)
        m *= 1 + 0.3 * np.sin(2 * np.pi * 7 * t)
        rattle = bp(r.standard_normal(Ld), 350, 1300, 2) * (0.5 + 0.5 * np.sin(ph))
        env = np.clip(t / .012, 0, 1) * np.clip((0.34 - t) / .02, 0, 1)
        place(buf, lp((m * 0.7 + rattle * 1.2) * env, 1800, 2), t0, 0.55, 0.15)
    L(17.6, "phone_vibration", 2, True, "2-pulse vibration muffled by cloth")
    notif(buf, 19.0, 0.16, 0.36, 0.1)
    L(19.0, "notification_1", 2, False, "soft two-note notification")

    # 3) reflection: dropout (applied to other stems) + squeak + 'Tss' tail
    t = np.arange(int(0.9 * SR)) / SR
    stick = (np.sin(2 * np.pi * 36 * t * (1 + 0.5 * t)) > 0.2).astype(float)
    stick = onepole(stick, 0.003)
    fq = 2300 + 900 * (t / 0.9) ** 1.5
    sq = np.sin(2 * np.pi * np.cumsum(fq) / SR) * stick
    sq += 0.6 * np.sin(2 * np.pi * np.cumsum(fq * 1.5) / SR) * stick
    sq += bp(r.standard_normal(len(t)), 4000, 9000, 1) * 0.25 * stick
    sq *= np.sin(np.pi * t / 0.9) ** 1.5
    place(buf, sq, 40.95, 0.09, 0.2)
    L(38.6, "reflection_dropout", 3, True, "ambience/music/foley dip ~-17 dB 38.6-43.4 (no stinger); skin-on-glass squeak 40.95")
    seg = narr_mono[int(42.05 * SR):int(42.9 * SR)]
    env = onepole(np.abs(seg), 0.01)
    env /= (env.max() + 1e-9)
    hiss = bp(r.standard_normal(len(seg)), 3500, 9500, 2) * env
    irt = ir_reverb(2.8, 61, decay_db=60, lp_hz=9000, predelay=0.10)
    tail = np.stack([signal.fftconvolve(hiss, irt[c]) for c in range(2)])
    w = np.arange(tail.shape[1]) / SR
    tail *= np.clip((w - 0.12) / 0.3, 0, 1)  # drop the part coinciding with the word itself
    i0 = int(42.05 * SR)
    e = min(N, i0 + tail.shape[1])
    buf[:, i0:e] += tail[:, :e - i0] * 2.2
    L(42.1, "tss_tail", 3, False, "breathy reverb tail of 'Тсс!' only")

    # 4) second/third notifications + tonal swell
    notif(buf, 45.0, 0.12, 0.36, 0.1)
    L(45.0, "notification_2", 4, True, "same phone tone")
    notif(buf, 50.2, 0.075, 0.33, 0.1)
    L(50.2, "notification_3", 4, False, "same tone, shorter")
    tn = swell([49.0, 51.9, 69.3, 98.0], [1.0, 0.8, 0.5, 0.25], 51.8, 53.4, 56.2, lpf=240, saw=True, seed=3)
    buf += to_stereo(tn * 0.45)
    L(51.8, "inside_tone", 4, False, "low tonal swell (G1/G#1 cluster)")

    # 5) lamps
    for k, t0 in enumerate([56.6, 57.4, 58.2]):
        lamp(buf, t0, k)
        L(t0, "lamp_%d_off" % (k + 1), 5, True, "clunk + decaying buzz + pitch-down tone (distinct per lamp)")

    # 7) collision
    Lc = int(1.0 * SR)
    t = np.arange(Lc) / SR
    body = np.sin(2 * np.pi * 52 * (1 + 0.9 * np.exp(-t / .06)) * t) * np.exp(-t / 0.2)
    body += lp(r.standard_normal(Lc), 180, 2) * np.exp(-t / 0.07) * 1.5
    place(buf, body, 64.9, 2.0, 0)
    t = np.arange(int(1.6 * SR)) / SR
    ring = (np.sin(2 * np.pi * 4620 * t) + 0.7 * np.sin(2 * np.pi * 6180 * t + 1)) * np.clip(t / .25, 0, 1) * np.exp(-t / 0.55)
    place(buf, ring, 65.0, 0.012, 0)
    L(64.9, "collision", 7, True, "single dull body impact + short ringing silence (dip 64.9-66.6)")

    # 8) black eyes
    win = bump(71.8, 73.0, 73.8, 75.5)
    rum = lp(r.standard_normal(N), 90, 2) * win
    s48 = np.sin(2 * np.pi * 48 * T) * win
    sh2 = (np.sin(2 * np.pi * 5200 * T) * (0.5 + 0.5 * np.sin(2 * np.pi * 3.1 * T)) +
           np.sin(2 * np.pi * 6730 * T) * (0.5 + 0.5 * np.sin(2 * np.pi * 2.3 * T + 1)) +
           np.sin(2 * np.pi * 7900 * T) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.7 * T + 2))) * bump(72.0, 73.3, 73.8, 75.6)
    buf += to_stereo(rum * 3.0 + s48 * 0.5)
    buf += np.stack([sh2, np.roll(sh2, 23)]) * 0.012
    L(71.8, "black_eyes", 8, True, "restrained low rumble swell + thin high shimmer")

    # 9) rooftop reveal
    sub = swell([34.0, 36.2, 68.5, 51.0], [1.0, 0.8, 0.35, 0.3], 94.5, 96.0, 101.8, lpf=140, seed=9)
    buf += to_stereo(sub * 0.9)
    i0, i1 = int(95.2 * SR), int(100.8 * SR)
    tt = np.arange(i1 - i0) / SR
    sag = 1 - 0.035 * (tt / tt[-1]) ** 0.7
    vib = 1 + 0.004 * np.sin(2 * np.pi * 4.7 * tt)
    gr = np.zeros(len(tt))
    for ra, a in zip([1, 1.47, 2.09, 2.76, 3.9], [1, .7, .5, .35, .2]):
        gr += a * np.sin(2 * np.pi * np.cumsum(88 * ra * sag * vib) / SR + ra)
    gr *= (1 + 0.5 * lp(r.standard_normal(len(tt)), 8, 1) / 0.2)
    gr = lp(gr, 1400, 2) * np.clip(tt / 1.2, 0, 1) ** 2 * np.clip((tt[-1] - tt) / 2.5, 0, 1)
    g_full = np.zeros(N)
    g_full[i0:i1] = gr
    gw = convolve_stereo(to_stereo(g_full), ir_reverb(5.0, 81, decay_db=60, lp_hz=4000, predelay=0.06))
    buf += gw * 0.9 + to_stereo(g_full) * 0.15
    L(95.2, "rooftop_reveal", 9, True, "deep sub swell 94.5-101.8 + distant metallic groan 95.2-100.8")

    # 10) creature voice: -3 st copy of 'Кто из вас настоящий?'
    ws = [w_ for w_ in align if 102.85 <= w_["start"] <= 105.3]
    a0 = ws[0]["start"] - 0.02
    a1 = ws[-1]["end"] + 0.1
    seg = narr_mono[int(a0 * SR):int(a1 * SR)]
    sh_ = lp(pv_pitch(seg, -3.0), 3200, 2)
    dl = int(0.07 * SR)
    dbl = sh_ + 0.45 * np.concatenate([np.zeros(dl), sh_[:-dl]])
    irv = ir_reverb(2.4, 83, decay_db=60, lp_hz=5000, predelay=0.03)
    ln = len(dbl) + int(2.0 * SR)
    vw = np.stack([signal.fftconvolve(dbl, irv[c])[:ln] for c in range(2)])
    voice = vw * 1.2
    voice[:, :len(dbl)] += dbl * 0.8
    i0 = int(a0 * SR)
    e = min(N, i0 + voice.shape[1])
    gate = onepole(np.where(np.arange(e - i0) / SR + a0 < 105.4, 1.0, 0.0), 0.02)
    buf[:, i0:e] += voice[:, :e - i0] * gate
    L(a0, "creature_voice", 10, True, "narration segment pitched -3 st, low-passed, doubled (70 ms delay + 2.4 s reverb)")

    # 11) black cut tail
    tail = np.sin(2 * np.pi * 41 * T) * curve([(105.4, 0), (105.5, 1), (106.4, 0.5), (108.0, 0), (108.4, 0)]) * 0.35
    tail += np.sin(2 * np.pi * 61.5 * T) * curve([(105.4, 0), (105.6, .5), (107, 0), (108.4, 0)]) * 0.12
    buf += to_stereo(tail)
    L(105.4, "black_cut_tail", 11, True, "near silence with very low fading sub tail")
    return buf, log
