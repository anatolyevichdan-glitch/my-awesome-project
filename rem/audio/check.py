"""Verification: loudness, stem balance, accent spacing, Whisper intelligibility. Writes check_results.json."""
import json, os, re, subprocess, sys
import numpy as np
from dsp import *
os.chdir(os.path.dirname(os.path.abspath(__file__)))

st = {k: read_audio(f"stem_{k}.wav") for k in ["narration", "music", "ambience", "foley", "sfx"]}
ms = read_audio("mix_master.wav")
res = {}
res["peak_abs"] = float(np.abs(ms).max())
res["clipped_samples"] = int((np.abs(ms) >= 0.999).sum())
res["lengths_s"] = {k: v.shape[1] / SR for k, v in st.items()} | {"master": ms.shape[1] / SR}
res["sum_vs_master_max_err"] = float(np.abs(sum(st.values()) - ms).max())

# short-term loudness (3 s) from ebur128 frames
r = subprocess.run(["ffmpeg", "-nostats", "-i", "mix_master.wav", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
S = [float(m) for m in re.findall(r"S:\s*(-?[\d.]+)", r)]
res["short_term_max_lufs"] = max(S)
res["short_term_p10_lufs"] = float(np.percentile(S, 10))

# per-segment RMS table (dBFS) per stem, with music-vs-voice difference
segs = [(0, 3), (3, 17), (17, 24), (24, 38.6), (38.6, 43.5), (43.5, 53), (53, 59), (59, 65), (65, 71.8), (71.8, 93),
        (93, 95.2), (95.2, 102.9), (102.9, 105.4), (105.4, 106.7), (106.7, 108.4)]
rows = []
for a, b in segs:
    i, j = int(a * SR), int(b * SR)
    row = {"seg": f"{a}-{b}"}
    for k, v in st.items():
        row[k] = round(float(rms_db(v[:, i:j])), 1)
    row["music_minus_voice_dB"] = round(row["music"] - row["narration"], 1)
    rows.append(row)
res["segment_rms_dbfs"] = rows
# music vs voice peaks (during speech)
voice = st["narration"].mean(0)
w = SR // 20
v50 = np.sqrt(np.mean(voice[:N // w * w].reshape(-1, w) ** 2, axis=1))
m50 = np.sqrt(np.mean(st["music"].mean(0)[:N // w * w].reshape(-1, w) ** 2, axis=1))
sp = v50 > 0.3 * np.percentile(v50, 90)
res["music_rms_below_voice_p95_dB (full band, speech frames)"] = round(float(db(np.percentile(v50[sp], 95)) - db(np.sqrt(np.mean(m50[sp] ** 2)))), 1)
res["music_active_frac_over_-70dBFS"] = float(np.mean(db(m50[: int(105 * SR / w)]) > -70))

# per-event SFX/foley vs voice at the same time (100 ms windows >150 Hz)
ev = json.load(open("event_log.json"))["events"]
sfx = hp(st["sfx"].mean(0), 150, 2)
rows = []
for e in ev:
    i, j = int(e["t"] * SR), int((e["t"] + 1.0) * SR)
    rows.append({"name": e["name"], "t": e["t"], "sfx_rms_1s_dBFS": round(float(rms_db(sfx[i:j])), 1),
                 "voice_rms_1s_dBFS": round(float(rms_db(voice[i:j])), 1)})
res["events_vs_voice"] = rows
fol = st["foley"].mean(0)
res["foley_peak_dBFS"] = float(db(np.abs(fol).max()))
res["voice_peak_dBFS"] = float(db(np.abs(voice).max()))
prom = sorted(e["t"] for e in ev if e["prominent"])
res["prominent_times"] = prom
res["min_gap_between_prominent_s"] = float(min(np.diff(prom)))

# Whisper intelligibility: transcribe final mix and the original; compare with script words
if "--nowhisper" in sys.argv:
    json.dump(res, open("check_results.json", "w"), indent=1, ensure_ascii=False); import pprint; sys.exit(0)
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8")
norm = lambda s: re.findall(r"[а-яё0-9]+", s.lower().replace("ё", "е"))
script = norm(open("../subs/script_ru.txt").read())


def wer(ref, hyp):
    d = np.zeros((len(ref) + 1, len(hyp) + 1), int)
    d[:, 0] = range(len(ref) + 1)
    d[0, :] = range(len(hyp) + 1)
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (ref[i - 1] != hyp[j - 1]))
    return d[-1, -1] / len(ref)


def tr(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
    seg, _ = model.transcribe(np.frombuffer(raw, np.float32), language="ru", beam_size=5, vad_filter=False)
    return " ".join(s.text for s in seg)


res["script_words"] = len(script)
for name, path in [("mix_master", "mix_master.wav"), ("narration_only", "stem_narration.wav")]:
    t = tr(path)
    res[f"whisper_{name}"] = {"text": t, "WER": round(float(wer(script, norm(t))), 3)}
    # content differences
    hyp = norm(t)
    res[f"whisper_{name}"]["missing_script_words"] = [w_ for w_ in set(script) if w_ not in hyp]
json.dump(res, open("check_results.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if k not in ("events_vs_voice",)}, indent=1, ensure_ascii=False))
print(json.dumps(res["events_vs_voice"], ensure_ascii=False))
