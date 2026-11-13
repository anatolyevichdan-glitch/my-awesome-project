"""Calibrate raw stems against the narration, enforce voice-relative guards, write stems + master + event_log.json.
Usage: python mix.py   (needs cache/raw_*.npy from build.py; ~1 min)"""
import json, time
import numpy as np
from scipy import ndimage
from lib import *

CACHE = os.path.join(HERE, "cache")
TP_TARGET = -1.55          # narration true peak after the single global gain
MUSIC_REL = -20.5          # median music momentary loudness re voice while speaking
AMB_REL = -17.0            # ambience bed re voice while speaking
MARGIN = 8.0               # every non-voice stem >= 8 LU under the voice while speaking
SAFETY = 0.4

# ---- narration (only resample + one global gain)
g_db = TP_TARGET - true_peak_db(NARR48)
narr = to_stereo(NARR48 * 10 ** (g_db / 20))
sp = speech_mask()
fr = frac_on_grid(sp)
speech_win = fr >= 0.98
Lv = momentary(kw_energy(narr))
Lmed = float(np.median(Lv[speech_win]))
print(f"narration gain {g_db:+.2f} dB; speech median momentary {Lmed:.2f} LUFS", flush=True)


def duck_curve(depth_db):
    f = frac_on_grid(sp, 0.1)
    d = np.zeros_like(f); y = 0.0
    for i, v in enumerate(f):  # attack 0.12 s, release 0.5 s
        a = np.exp(-HOP / (0.12 if v > y else 0.5))
        y = a * y + (1 - a) * v
        d[i] = y
    return 10 ** (-depth_db * d / 20)


def calibrate(stem, gcurve, target_rel):
    s = stem * to_samples(gcurve)[None]
    L = momentary(kw_energy(s))
    ok = speech_win & (L > -80)
    off = float(np.median(L[ok] - Lv[ok]))
    return s * 10 ** ((target_rel - off) / 20), off


def allow_curve(margin, exceptions=()):
    fr_ = np.clip(fr, 0, 1)
    a_sp = np.maximum(Lv, Lmed - 14) - margin
    a_pause = Lmed - 2.0
    allow = a_pause * (1 - fr_) + a_sp * fr_
    for t0, t1, m in exceptions:
        k = (GRID >= t0 - 0.1) & (GRID <= t1)
        allow[k] = np.maximum(Lv[k], Lmed - 14) - m
    return allow


def guard(stem, margin=MARGIN, exceptions=(), name=""):
    worst = 0.0
    tot = np.ones(N)
    for it in range(4):
        L = momentary(kw_energy(stem))
        ex = L - allow_curve(margin, exceptions) + SAFETY
        gd = -np.clip(ex, 0, None)
        if gd.min() > -0.05:
            break
        gd = ndimage.minimum_filter1d(gd, size=9)
        gd = ndimage.uniform_filter1d(gd, size=5)
        gain = 10 ** (to_samples(np.minimum(gd, 0)) / 20)
        stem = stem * gain[None]
        tot *= gain
        worst = min(worst, float(gd.min()))
    print(f"guard {name}: max reduction {worst:.1f} dB", flush=True)
    return stem, worst


def window_floor(stem, t0, t1, rms_db_target, ramp=0.4):
    """Scale a stem inside [t0,t1] so its RMS equals the target (smooth ramps)."""
    i, j = int(t0 * SR), int(t1 * SR)
    cur = rms_db(stem[:, i:j]) / 2 * 2 / 2  # 10log10(mean sq) already dB
    cur = 10 * np.log10(np.mean(stem[:, i:j] ** 2) + 1e-20)
    d = rms_db_target - cur
    c = np.interp(T, [t0 - ramp, t0, t1, t1 + 0.01], [0, d, d, 0])
    return stem * (10 ** (c / 20))[None]


if __name__ == "__main__":
    t_ = time.time()
    raw = {k: np.load(os.path.join(CACHE, f"raw_{k}.npy")).astype(np.float64) for k in ["music", "ambience", "foley", "sfx"]}
    info = {}

    # music: duck 4 dB under speech, calibrate to -20.5 LU re voice
    gm = np.interp(GRID, GRID, 20 * np.log10(duck_curve(4.0)))
    music, off = calibrate(raw["music"], gm, MUSIC_REL)
    info["music_cal_offset_dB"] = off
    music, w = guard(music, 18.0, name="music")

    # ambience: duck 3 dB under speech, calibrate, then enforce the explicit near-silence windows
    ga = 20 * np.log10(duck_curve(3.0))
    amb, off = calibrate(raw["ambience"], ga, AMB_REL)
    amb, w = guard(amb, 10.0, name="ambience")
    amb = window_floor(amb, 127.5, 132.7, -55.0, 0.4)
    amb = window_floor(amb, 108.9, 112.3, -47.0, 0.4)

    foley, w = guard(raw["foley"], MARGIN, name="foley")
    sfx, w = guard(raw["sfx"], MARGIN, exceptions=[(132.3, 132.8, 3.0)], name="sfx")

    # hard cut at 132.8: everything except narration silent (fast fade 132.65-132.8)
    cut = np.interp(T, [0, 132.65, 132.8, DUR], [1, 1, 0, 0])
    music, amb, foley, sfx = [x * cut[None] for x in (music, amb, foley, sfx)]
    music[:, T >= 127.1] = 0

    # shared guard on the sum of all non-voice stems (common gain keeps stems summing to the master)
    nv = music + amb + foley + sfx
    L = momentary(kw_energy(nv))
    ex = L - allow_curve(MARGIN, [(132.3, 132.8, 3.0)]) + SAFETY
    gd = ndimage.uniform_filter1d(ndimage.minimum_filter1d(-np.clip(ex, 0, None), size=9), size=5)
    gain = 10 ** (to_samples(np.minimum(gd, 0)) / 20)
    print(f"sum guard max reduction {gd.min():.1f} dB", flush=True)
    music, amb, foley, sfx = [x * gain[None] for x in (music, amb, foley, sfx)]
    info["sum_guard_max_reduction_dB"] = float(gd.min())

    stems = dict(narration=narr, music=music, ambience=amb, foley=foley, sfx=sfx)
    master = sum(stems.values())
    tp = true_peak_db(master)
    print(f"master TP {tp:.2f} dBTP, peak {np.abs(master).max():.3f}", flush=True)
    if tp > -1.5:  # reduce the one global gain (all stems) if the mix overshoots
        d = -1.5 - 0.05 - tp
        stems = {k: v * 10 ** (d / 20) for k, v in stems.items()}
        master = sum(stems.values()); g_db += d
        print(f"global gain trimmed by {d:.2f} dB -> TP {true_peak_db(master):.2f}")
    for k, v in stems.items():
        write_wav_exact(os.path.join(HERE, f"stem_{k}.wav"), v)
    write_wav_exact(os.path.join(HERE, "mix_master.wav"), master)
    ev = json.load(open(os.path.join(CACHE, "events.json")))
    info.update(narration_global_gain_dB=g_db, narration_speech_median_LUFS=Lmed, duration_s=DUR, samples=N,
                master_integrated_LUFS_dualmono_stereo=float(integrated(kw_energy(master))), master_true_peak_dBTP=true_peak_db(master))
    json.dump(dict(info=info, events=ev), open(os.path.join(HERE, "event_log.json"), "w"), indent=1, ensure_ascii=False)
    print("mix done", round(time.time() - t_, 1), json.dumps(info))
