import json, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8")
a = np.frombuffer(open("narr16.wav", "rb").read()[44:], dtype="int16").astype("float32") / 32768
seg, info = m.transcribe(a, language="ru", word_timestamps=True, beam_size=5, condition_on_previous_text=False)
out = []
for s in seg:
    for w in s.words: out.append((round(w.start, 2), round(w.end, 2), w.word.strip()))
json.dump(out, open("words_medium.json", "w"), ensure_ascii=False)
print(' '.join(f"[{a:.1f}]{c}" for a, b, c in out))
