import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
a = np.frombuffer(open("out/mix16.wav", "rb").read()[44:], dtype="int16").astype("float32") / 32768
seg, _ = m.transcribe(a, language="ru", beam_size=3, condition_on_previous_text=False)
print(' '.join(s.text.strip() for s in seg))
