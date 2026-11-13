import numpy as np, json
from scipy.io import wavfile
from scipy import signal
def rd(p):
    sr, x = wavfile.read(p); 
    x = x.astype(np.float64)
    if x.dtype != np.float64 or np.abs(x).max() > 2: x /= 2**31 if np.abs(x).max()>2**23 else 2**23
    return sr, x
names = ["narration","music","ambience","foley","sfx"]
st = {n: rd(f"stem_{n}.wav")[1] for n in names}
sr, m = rd("mix_master.wav")
print("lens", {n: len(v) for n,v in st.items()}, len(m), "sum err", np.abs(sum(st.values())-m).max())
mono = {n: v.mean(1) for n,v in st.items()}
w = sr
def rmsdb(x, a, b):
    s = x[int(a*sr):int(b*sr)]
    return 20*np.log10(np.sqrt(np.mean(s**2))+1e-12)
print("sec  narr  music amb  foley sfx   (1 s RMS dBFS, music>80Hz)")
mus = signal.sosfilt(signal.butter(2,80,'hp',fs=sr,output='sos'), mono["music"])
for a in range(0,109,2):
    b=min(a+2,108.3)
    print(f"{a:3d} {rmsdb(mono['narration'],a,b):6.1f} {rmsdb(mus,a,b):6.1f} {rmsdb(mono['ambience'],a,b):6.1f} {rmsdb(mono['foley'],a,b):6.1f} {rmsdb(mono['sfx'],a,b):6.1f}")
# voice vs music while speaking
n = mono["narration"]; seg = sr//20
r = np.sqrt(np.mean(n[:len(n)//seg*seg].reshape(-1,seg)**2,axis=1))
act = r > 0.3*np.percentile(r,90)
mm = np.sqrt(np.mean(mus[:len(mus)//seg*seg].reshape(-1,seg)**2,axis=1))
mfull = np.sqrt(np.mean(mono["music"][:len(n)//seg*seg].reshape(-1,seg)**2,axis=1))
print("speech: voice rms %.1f, music(>80Hz) rms %.1f, music(full) %.1f dBFS; diff %.1f / %.1f dB"%(
 20*np.log10(np.sqrt(np.mean(r[act]**2))),20*np.log10(np.sqrt(np.mean(mm[act]**2))),20*np.log10(np.sqrt(np.mean(mfull[act]**2))),
 20*np.log10(np.sqrt(np.mean(r[act]**2))/np.sqrt(np.mean(mm[act]**2))),20*np.log10(np.sqrt(np.mean(r[act]**2))/np.sqrt(np.mean(mfull[act]**2)))))
print("pauses: music %.1f dBFS"%(20*np.log10(np.sqrt(np.mean(mm[~act]**2)))))
for k in ["foley","sfx","ambience"]:
    x=mono[k]; q=np.sqrt(np.mean(x[:len(x)//seg*seg].reshape(-1,seg)**2,axis=1))
    print(k,"speech rms diff vs voice %.1f dB"%(20*np.log10(np.sqrt(np.mean(r[act]**2))/np.sqrt(np.mean(q[act]**2)))), "peak %.1f dBFS"%(20*np.log10(np.abs(x).max())))
print("master clip samples:", int((np.abs(m)>=0.9999).sum()))
