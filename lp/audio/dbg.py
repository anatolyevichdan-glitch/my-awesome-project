"""Debug: per-section median loudness of each stem relative to the voice while speaking."""
import numpy as np, soundfile as sf
from lib import *
st={k:sf.read(os.path.join(HERE,f"stem_{k}.wav"),dtype="float64")[0].T for k in ["narration","music","ambience","foley","sfx"]}
Lv=momentary(kw_energy(st["narration"])); fr=frac_on_grid(speech_mask()); win=fr>=.98
L={k:momentary(kw_energy(v)) for k,v in st.items()}
for a,b in [(0,6.5),(6.5,10.2),(10.2,18),(18,36),(36,46),(46,60),(60,74),(74,92.5),(92.6,98),(98,105),(105,108.5),(112.6,118.3),(118.3,127),(127.1,133)]:
    k=(GRID>=a)&(GRID<b)&win
    row=[]
    for n in ["music","ambience","foley","sfx"]:
        d=(L[n]-Lv)[k]; d=d[L[n][k]>-90]
        row.append(f"{n[:3]} med {np.median(d):6.1f} max {d.max():6.1f}" if len(d) else f"{n[:3]} --")
    print(f"{a:6.1f}-{b:6.1f} n={k.sum():3d} | "+" | ".join(row))
