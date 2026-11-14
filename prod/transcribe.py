from faster_whisper import WhisperModel
import json, numpy as np, wave
wf=wave.open("n16.wav"); A=np.frombuffer(wf.readframes(wf.getnframes()),np.int16).astype(np.float32)/32768
m = WhisperModel("medium", device="cpu", compute_type="int8")
segs, info = m.transcribe(A, language="ru", word_timestamps=True, beam_size=5)
out=[]
for s in segs:
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}")
    out.append({"start":s.start,"end":s.end,"text":s.text.strip(),"words":[{"w":w.word.strip(),"s":w.start,"e":w.end} for w in s.words]})
json.dump(out, open("transcript.json","w"), ensure_ascii=False, indent=1)
