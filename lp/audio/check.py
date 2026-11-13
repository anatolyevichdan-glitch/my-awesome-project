"""Measurements for the delivered files. Usage: python check.py [--nowhisper] [--events]  -> check_results.json"""
import json, re, subprocess, sys
import numpy as np
import soundfile as sf
from lib import *

def rd(n):
    x, sr = sf.read(os.path.join(HERE, n), dtype="float64"); assert sr == SR
    return x.T

names = ["narration", "music", "ambience", "foley", "sfx"]
st = {k: rd(f"stem_{k}.wav") for k in names}
ms = rd("mix_master.wav")
res = {}
res["length_s"] = {k: v.shape[1] / SR for k, v in st.items()} | {"master": ms.shape[1] / SR, "narration_original": N / SR}
res["sum_vs_master_max_abs_err"] = float(np.abs(sum(st.values()) - ms).max())
res["peak_abs"] = float(np.abs(ms).max())
res["clipped_samples_ge_0.999"] = int((np.abs(ms) >= 0.999).sum())
res["true_peak_dBTP"] = true_peak_db(ms)
res["integrated_LUFS_own_meter"] = float(integrated(kw_energy(ms)))
r = subprocess.run(["ffmpeg", "-nostats", "-i", os.path.join(HERE, "mix_master.wav"), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
res["ffmpeg_ebur128"] = {"I": float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]), "LRA": float(re.findall(r"LRA:\s+(-?[\d.]+) LU", r)[-1]),
                         "TP": float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])}
# narration untouched apart from gain
ref = to_stereo(NARR48)
gdb = 20 * np.log10(np.dot(st["narration"][0], ref[0]) / np.dot(ref[0], ref[0]))
res["narration_gain_dB"] = float(gdb)
res["narration_residual_after_gain_max"] = float(np.abs(st["narration"] - ref * 10 ** (gdb / 20)).max())

# loudness of each stem vs voice
Lv = momentary(kw_energy(st["narration"]))
sp = speech_mask(); fr = frac_on_grid(sp); win = fr >= 0.98
Lmed = float(np.median(Lv[win]))
res["voice_speech_median_momentary_LUFS"] = Lmed
nonv = {k: st[k] for k in names[1:]}
nvsum = sum(nonv.values())
rows = {}
for k, v in list(nonv.items()) + [("all_non_voice_sum", nvsum)]:
    L = momentary(kw_energy(v))
    ok = win & (L > -90)
    d = (L - Lv)[ok]
    # sting exception window excluded from the count and reported separately
    exw = (GRID >= 132.1) & (GRID <= 133.0)
    ok2 = ok & ~exw
    d2 = (L - Lv)[ok2]
    rows[k] = {"speech_windows_checked": int(ok2.sum()), "median_rel_voice_LU": float(np.median(d2)) if ok2.size and ok2.any() else None,
               "closest_rel_voice_LU": float(d2.max()) if ok2.any() else None,
               "windows_within_8LU": int((d2 > -8).sum()),
               "windows_within_10LU": int((d2 > -10).sum()),
               "windows_within_8LU_in_sting_window_132.1-133.0": int(((L - Lv)[ok & exw] > -8).sum())}
    if k == "music":
        rows[k]["pause_median_rel_voice_LU"] = float(np.median((L - Lv)[(fr == 0) & (L > -90) & (GRID < 105)]))
        rows[k]["closest_rel_voice_within_all_speech_windows"] = float(d.max())
res["stems_vs_voice_while_speaking"] = rows
# peak-ish check: 100 ms windows of foley/sfx RMS vs voice 100 ms RMS at the same time while speaking
w = int(0.1 * SR); nb = N // w
def rms100(x): return np.sqrt(np.mean(x[:, :nb * w].reshape(2, nb, w) ** 2, axis=(0, 2)))
v100 = rms100(st["narration"]); spm = sp[:nb * w].reshape(nb, w).mean(1) > 0.98
for k in ["foley", "sfx"]:
    d = db(rms100(st[k])) - db(v100)
    res.setdefault("short_100ms_rms_rel_voice_while_speaking_dB", {})[k] = {"max": float(d[spm].max()), "p99": float(np.percentile(d[spm], 99))}

# quiet / silent regions
def seg(name, a, b):
    i, j = int(a * SR), int(b * SR)
    return {k: float(10 * np.log10(np.mean(v[:, i:j] ** 2) + 1e-20)) for k, v in nonv.items()} | {"all_non_voice": float(10 * np.log10(np.mean(nvsum[:, i:j] ** 2) + 1e-20)),
            "narration": float(10 * np.log10(np.mean(st["narration"][:, i:j] ** 2) + 1e-20))}
res["rms_dBFS_127.1-132.3"] = seg("a", 127.1, 132.3)
res["rms_dBFS_127.1-132.2_music_max_abs"] = float(np.abs(st["music"][:, int(127.1 * SR):int(132.3 * SR)]).max())
res["rms_dBFS_108.6-112.6"] = seg("b", 108.6, 112.6)
res["after_132.8_non_voice_max_abs"] = float(np.abs(nvsum[:, int(132.8 * SR):]).max())
res["after_132.81_non_voice_max_abs"] = float(np.abs(nvsum[:, int(132.81 * SR):]).max())
res["sting_132.3-132.8"] = {"peak_dBFS_of_sfx": float(db(np.abs(st["sfx"][:, int(132.3 * SR):int(132.8 * SR)]).max())),
                            "narration_peak_dBFS_same_window": float(db(np.abs(st["narration"][:, int(132.3 * SR):int(132.8 * SR)]).max())),
                            "master_true_peak_in_window": true_peak_db(ms[:, int(132.0 * SR):int(133.0 * SR)])}
res["blackout_92.55-93.35_non_voice_rms_dBFS_excluding_sfx"] = float(10 * np.log10(np.mean((st["music"] + st["ambience"])[:, int(92.6 * SR):int(93.3 * SR)] ** 2) + 1e-20))
# overall level per section for music (dBFS)
secs = [(0, 6.5), (6.5, 10.2), (10.2, 17.9), (18, 36), (36, 44.3), (46.5, 60), (60, 74), (74, 92.5), (93, 95), (95, 104.6), (104.6, 108.6), (112.6, 118.3), (118.3, 127.1)]
res["music_rms_dBFS_sections"] = {f"{a}-{b}": float(10 * np.log10(np.mean(st["music"][:, int(a * SR):int(b * SR)] ** 2) + 1e-20)) for a, b in secs}

if "--events" in sys.argv:
    evs = json.load(open(os.path.join(HERE, "event_log.json")))["events"]
    sfxL = momentary(kw_energy(st["sfx"])); folL = momentary(kw_energy(st["foley"]))
    for e in evs:
        if e["stem"] in ("sfx", "foley") and e["peak_dbfs"] is not None:
            k = int(e["t"] / HOP); sl = slice(max(0, k - 2), k + 8)
            L = (sfxL if e["stem"] == "sfx" else folL)[sl].max()
            print(f'{e["t"]:7.2f} {e["stem"]:5s} {e["name"]:34s} design {e["peak_dbfs"]:6.1f}  mom {L:6.1f}  voice {Lv[sl].max():6.1f}  rel {L - Lv[sl].max():6.1f}')

if "--nowhisper" not in sys.argv:
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    norm = lambda s: re.findall(r"[а-яё0-9]+", s.lower().replace("ё", "е"))
    NUM = {"11": "одиннадцать", "5": "пять", "13": "тринадцать", "7": "семь", "20": "двадцать", "10": "десять", "1": "один", "2": "два", "3": "три", "4": "четыре", "6": "шесть", "8": "восемь"}
    script = None

    def wer(ref, hyp):
        d = np.zeros((len(ref) + 1, len(hyp) + 1), int); d[:, 0] = range(len(ref) + 1); d[0, :] = range(len(hyp) + 1)
        for i in range(1, len(ref) + 1):
            for j in range(1, len(hyp) + 1):
                d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (ref[i - 1] != hyp[j - 1]))
        return d[-1, -1] / len(ref)

    def tr(x2):
        m = x2.mean(0)
        m = signal.resample_poly(m, 1, 3).astype(np.float32)
        seg, _ = model.transcribe(m, language="ru", beam_size=5, vad_filter=False)
        return " ".join(s.text for s in seg)

    def expand(ws):
        out = []
        for w in ws:
            out.append(NUM.get(w, w))
        return out
    script = expand(norm(open(os.path.join(HERE, "script_ru.txt")).read()))
    res["script_words"] = len(script)
    for name, x in [("mix_master", ms), ("narration_only", st["narration"])]:
        t = tr(x)
        hyp = norm(t)
        # digits in hypothesis -> words; script is already spelled with words
        hyp = expand(hyp)
        res[f"whisper_{name}"] = {"WER": round(float(wer(script, hyp)), 4), "text": t}
    res["WER_delta_mix_minus_narration"] = round(res["whisper_mix_master"]["WER"] - res["whisper_narration_only"]["WER"], 4)
    # intelligibility of the final word under the sting
    i, j = int(130.0 * SR), int(133.0 * SR)
    res["whisper_130-133_mix"] = tr(ms[:, i:j]); res["whisper_130-133_narration_only"] = tr(st["narration"][:, i:j])
json.dump(res, open(os.path.join(HERE, "check_results.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if not k.startswith("whisper_mix") and not k.startswith("whisper_narr")}, indent=1, ensure_ascii=False))
