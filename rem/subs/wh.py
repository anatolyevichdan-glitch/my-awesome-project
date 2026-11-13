import json
from faster_whisper import WhisperModel
import numpy as np,subprocess
audio=np.frombuffer(subprocess.check_output(['ffmpeg','-loglevel','error','-i','nar16k.wav','-f','f32le','-ac','1','-ar','16000','-']),dtype=np.float32)
m=WhisperModel('medium',device='cpu',compute_type='int8')
seg,_=m.transcribe(audio,language='ru',word_timestamps=True,vad_filter=False)
out=[]
for s in seg:
    for w in s.words: out.append((w.word.strip(),round(w.start,2),round(w.end,2)))
json.dump(out,open('whisper.json','w'),ensure_ascii=False)
print(len(out))
