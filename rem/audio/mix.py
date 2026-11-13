"""Build all stems + master.  Usage: python mix.py [--rebuild]
Music/ambience/sfx are cached in cache/; foley is always rebuilt so a dropped-in foley_events.json takes effect."""
import json, os, subprocess, sys, re
import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from dsp import *
import build, build_sfx

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
os.makedirs("cache", exist_ok=True)
REBUILD = "--rebuild" in sys.argv
TARGET_LUFS, TP_LIMIT = -16.0, -1.5
# Level design, dB relative to V = the narration's loud-speech level (95th pct of 50 ms RMS while speaking)
MUSIC_DB = -25.0      # music RMS (>80 Hz) while narrator speaks, after ducking
AMB_DB = -27.0        # ambience RMS while narrator speaks, after ducking
FOLEY_PEAK_DB = -13.0  # loudest foley peak vs V (sample peak vs RMS-ish V, so effectively far quieter than the voice)
SFX_DB = -3.0        # loudest 0.5 s SFX window (>100 Hz) vs V
DUCK = {"music": 8.0, "amb": 6.0, "foley": 3.0, "sfx": 3.0}


def cached(name, fn):
    p = f"cache/{name}.npy"
    if os.path.exists(p) and not REBUILD:
        return np.load(p).astype(np.float64)
    x = fn()
    np.save(p, x.astype(np.float32))
    return x


def ctrl_smooth(x, sr, att, rel):
    out = np.zeros_like(x)
    y = 0.0
    a = np.exp(-1 / (att * sr))
    r = np.exp(-1 / (rel * sr))
    for i, v in enumerate(x):
        y = a * y + (1 - a) * v if v > y else r * y + (1 - r) * v
        out[i] = y
    return out


def process_voice(v):
    out = np.stack([hp(v[c], 70, 2) for c in range(2)])
    out = np.stack([peaking(out[c], 3500, 2.0, 0.9) for c in range(2)])
    out = np.stack([peaking(out[c], 250, -1.0, 0.8) for c in range(2)])
    cs = SR // 1000
    m = np.max(np.abs(out), axis=0)
    nn = N // cs
    env = m[:nn * cs].reshape(nn, cs).max(1)
    envd = db(ctrl_smooth(env, 1000, 0.008, 0.12))
    thr, ratio = -20.0, 1.8
    gr = np.where(envd > thr, -(envd - thr) * (1 - 1 / ratio), 0.0)
    g = np.interp(np.arange(N) / SR, np.arange(nn) / 1000, 10 ** (gr / 20))
    return out * g


def voice_activity(v):
    mono = v.mean(0)
    cs = SR // 1000
    n = N // cs
    e = np.sqrt(np.mean(mono[:n * cs].reshape(n, cs) ** 2, axis=1))
    e = signal.lfilter([0.05], [1, -0.95], e)
    thr = 0.12 * np.percentile(e, 98)
    vad = np.clip((e - thr * .5) / (thr * 1.5), 0, 1)
    vad = ctrl_smooth(vad, 1000, 0.03, 0.4)  # attack 30 ms, release 400 ms
    return np.interp(np.arange(N) / SR, np.arange(n) / 1000, vad)


def measure(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    tail = r[r.rfind("Summary:"):]
    g = lambda pat: float(re.search(pat, tail).group(1))
    return {"I": g(r"I:\s+(-?[\d.]+) LUFS"), "LRA": g(r"LRA:\s+(-?[\d.]+) LU"), "TP": g(r"Peak:\s+(-?[\d.]+) dBFS")}


def tmp_measure(x):
    p = "/tmp/_m.wav"
    wavfile.write(p, SR, x.T.astype(np.float32))
    return measure(p)


def limiter_gain(x, ceiling_db):
    """Look-ahead peak limiter gain curve from 4x-oversampled peaks (shared by all stems)."""
    ceil = 10 ** (ceiling_db / 20)
    over = np.abs(signal.resample_poly(x, 4, 1, axis=1)).max(0)
    pk = over[:4 * N].reshape(N, 4).max(1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    la = int(0.004 * SR)
    g = minimum_filter1d(need, 2 * la + 1)
    g = uniform_filter1d(g, 2 * la + 1)
    return np.minimum(g, 1.0)


def main():
    full = read_audio("narration_original.mp3")
    print("narration duration (s): %.3f" % (full.shape[1] / SR))
    narr_raw = fit(full)
    align = json.load(open("../subs/align.json"))
    voice = process_voice(narr_raw)
    vad = voice_activity(voice)
    mono = voice.mean(0)
    w = SR // 20
    rms50 = np.sqrt(np.mean(mono[:N // w * w].reshape(-1, w) ** 2, axis=1))
    act = rms50 > 0.3 * np.percentile(rms50, 90)
    V = np.percentile(rms50[act], 95)
    print("voice reference V: %.1f dBFS (pre-master)" % db(V))

    music = cached("music", build.build_music)

    amb = cached("amb", lambda: build.build_ambience(None))

    def mk_sfx():
        s, l = build_sfx.build_sfx(narr_raw.mean(0), align)
        json.dump(l, open("cache/sfx_log.json", "w"), indent=1, ensure_ascii=False)
        return s
    sfx_raw = cached("sfx", mk_sfx)
    log = json.load(open("cache/sfx_log.json"))
    foley, fsrc, fev = build.build_foley()
    print("foley source:", fsrc, len(fev), "events")

    duck = lambda d: 10 ** (-d * vad / 20)
    mask = vad > 0.5

    def active_rms(x, hpf=80):
        xs = np.stack([hp(x[c], hpf, 2) for c in range(2)]).mean(0)
        return np.sqrt(np.mean(xs[mask] ** 2))

    mu = music * duck(DUCK["music"])
    mu *= V * 10 ** (MUSIC_DB / 20) / active_rms(mu)
    am = amb * duck(DUCK["amb"])
    am *= V * 10 ** (AMB_DB / 20) / active_rms(am)
    fo = foley * duck(DUCK["foley"])
    fo *= V * 10 ** (FOLEY_PEAK_DB / 20) / np.percentile(np.abs(fo), 99.99)
    sx = sfx_raw * duck(DUCK["sfx"])
    sh = np.stack([hp(sx[c], 100, 2) for c in range(2)]).mean(0)
    wl = SR // 2
    wr = np.sqrt(np.mean(sh[:N // wl * wl].reshape(-1, wl) ** 2, axis=1))
    sx *= V * 10 ** (SFX_DB / 20) / np.max(wr)

    stems = {"narration": voice, "music": mu, "ambience": am, "foley": fo, "sfx": sx}
    pre = sum(stems.values())
    m0 = tmp_measure(pre)
    print("pre-master:", m0)
    gain = 10 ** ((TARGET_LUFS - m0["I"]) / 20)
    for it in range(5):
        y = pre * gain
        lim = limiter_gain(y, TP_LIMIT - 0.3)
        m1 = tmp_measure(y * lim)
        print("iter %d: gain %.2f dB, limiter max reduction %.2f dB ->" % (it, db(gain), -db(lim.min())), m1)
        if abs(m1["I"] - TARGET_LUFS) < 0.1 and m1["TP"] < TP_LIMIT:
            break
        gain *= 10 ** ((TARGET_LUFS - m1["I"]) / 20)
    print("limiter: >0.5 dB reduction for %.2f%% of samples" % (100 * np.mean(lim < 10 ** (-0.5 / 20))))
    out = {k: v * gain * lim for k, v in stems.items()}
    master = sum(out.values())
    for k, v in out.items():
        write_wav(f"stem_{k}.wav", v)
    write_wav("mix_master.wav", master)
    write_wav("music_only.wav", out["music"])
    write_wav("sfx_only.wav", out["foley"] + out["sfx"])
    ev_log = {"duration_s": DUR, "prominent_moments": sorted({e["moment"] for e in log if e["prominent"]}),
              "events": sorted(log, key=lambda e: e["t"]), "foley_source": fsrc,
              "levels_db_re_voice_loud_speech": {"music_during_speech": MUSIC_DB, "ambience_during_speech": AMB_DB,
                                                  "foley_peak": FOLEY_PEAK_DB, "sfx_loudest_window": SFX_DB},
              "master": measure("mix_master.wav")}
    json.dump(ev_log, open("event_log.json", "w"), indent=1, ensure_ascii=False)
    print("master:", ev_log["master"])


if __name__ == "__main__":
    main()
