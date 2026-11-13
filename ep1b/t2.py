import sys, time
from PIL import Image
import shots2 as S
from core import *
def render(fn,T):
    fr=Frame(seed=int(T*30)); kw=fn(fr,T); return finish(fr,**kw)
sel=[(S.shot_G,58.9),(S.shot_G,61.0),(S.shot_H,64.0),(S.shot_H,65.0),(S.shot_H,65.9),(S.shot_I,67.5),(S.shot_I,70),(S.shot_I,73.5),(S.shot_I,76.5),(S.shot_I,82),(S.shot_I,85),(S.shot_I,88.5)]
if len(sys.argv)>1: sel=[sel[int(i)] for i in sys.argv[1:]]
t0=time.time()
ims=[Image.fromarray(render(f,T)).resize((300,533)) for f,T in sel]
print('per frame',(time.time()-t0)/len(ims))
rows=(len(ims)+5)//6
sh=Image.new('RGB',(1800,533*rows))
for i,im in enumerate(ims): sh.paste(im,((i%6)*300,(i//6)*533))
sh.save('/tmp/sheet2.png')
