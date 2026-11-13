"""Transcribe narration with word timestamps -> words.json, segments printed."""
import json
import subprocess
import numpy as np
from faster_whisper import WhisperModel

P = '/tmp/hoplite/workspace/lp/audio/narration_original.mp3'
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", P, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                     capture_output=True, check=True).stdout
model = WhisperModel("medium", device="cpu", compute_type="int8")
seg, _ = model.transcribe(np.frombuffer(raw, np.float32), language="ru", beam_size=5, word_timestamps=True, vad_filter=False)
words, segs = [], []
for s in seg:
    segs.append({"s": round(s.start, 2), "e": round(s.end, 2), "text": s.text.strip()})
    for w in s.words:
        words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)})
    print(f"{s.start:6.2f}-{s.end:6.2f} {s.text.strip()}", flush=True)
json.dump({"segments": segs, "words": words}, open('/tmp/hoplite/workspace/lp/audio/words.json', 'w'), ensure_ascii=False, indent=0)
