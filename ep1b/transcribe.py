import json
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8")
seg,info=m.transcribe(__import__("numpy").frombuffer(open("narr16.wav","rb").read()[44:],dtype="int16").astype("float32")/32768,language="ru",word_timestamps=True,vad_filter=False,beam_size=5)
out=[]
for s in seg:
    for w in s.words: out.append((round(w.start,2),round(w.end,2),w.word.strip()))
json.dump(out,open("words.json","w"),ensure_ascii=False)
print(info.duration)
line=[];
for a,b,w in out: print(f"{a:6.2f} {b:6.2f} {w}")
