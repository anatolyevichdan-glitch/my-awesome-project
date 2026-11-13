import numpy as np, soundfile as sf, sys
from lib import *
st={k:sf.read(os.path.join(HERE,f"stem_{k}.wav"),dtype="float64")[0].T for k in ["narration","music","ambience","foley","sfx"]}
Lv=momentary(kw_energy(st["narration"])); fr=frac_on_grid(speech_mask()); win=fr>=.98
Lmed=np.median(Lv[win]); print("Lmed",Lmed,"windows",win.sum(),"voice<Lmed-14:",(Lv[win]<Lmed-14).sum(),"<Lmed-10",(Lv[win]<Lmed-10).sum())
for n in ["music","ambience","foley","sfx"]:
    L=momentary(kw_energy(st[n])); d=L-Lv; bad=win&(d>-8)&(L>-90)
    print(n,"bad",bad.sum(), [(round(g,2),round(float(Lv[i]),1),round(float(d[i]),1)) for i,g in enumerate(GRID) if bad[i]][:14])
