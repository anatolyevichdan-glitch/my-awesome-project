import numpy as np,subprocess,json
x=np.frombuffer(subprocess.check_output(['ffmpeg','-loglevel','error','-i','../audio/narration_original.mp3','-f','f32le','-ac','1','-ar','16000','-']),dtype=np.float32)
hop=80  # 5ms
n=len(x)//hop
fr=x[:n*hop].reshape(n,hop*1)
# 10ms window with 5ms hop
win=np.concatenate([fr[:-1],fr[1:]],axis=1)
db=20*np.log10(np.sqrt((win**2).mean(1))+1e-6)
np.save('env_db.npy',db)
print(len(db)*0.005, db.max(), np.percentile(db,5))
