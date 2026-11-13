import sys, time
from PIL import Image
import shots3 as S
from core import *
def render(fn, T):
    fr = Frame(seed=int(T * 30)); kw = fn(fr, T); return finish(fr, **kw)
NAME = sys.argv[1]
import importlib
M = importlib.import_module(NAME)
sel = []
for a in sys.argv[2:]:
    f, T = a.split(':'); sel.append((getattr(M, f), float(T)))
t0 = time.time()
ims = [Image.fromarray(render(f, T)).resize((360, 640)) for f, T in sel]
print('per frame', (time.time() - t0) / len(ims))
cols = min(len(ims), 6); rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (360 * cols, 640 * rows))
for i, im in enumerate(ims): sh.paste(im, ((i % cols) * 360, (i // cols) * 640))
sh.save('/tmp/verify/sheet.png')
