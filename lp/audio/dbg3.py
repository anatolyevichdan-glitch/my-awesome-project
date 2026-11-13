import numpy as np, soundfile as sf, json
from lib import *
st={k:sf.read(os.path.join(HERE,f"stem_{k}.wav"),dtype="float64")[0].T for k in ["foley","sfx"]}
ev=json.load(open(os.path.join(HERE,"event_log.json")))["events"]
for e in ev:
    if e["stem"] in st and e["peak_dbfs"] is not None and not e["name"].startswith(("heartbeat","dial","count")):
        i=int(e["t"]*SR); seg=st[e["stem"]][:, i:i+int(0.5*SR)]
        pk=db(np.abs(seg).max())
        if pk < e["peak_dbfs"]+4-5: print(f'{e["t"]:7.2f} {e["name"][:30]:30s} design+trim {e["peak_dbfs"]+4:6.1f} actual {pk:6.1f}')
