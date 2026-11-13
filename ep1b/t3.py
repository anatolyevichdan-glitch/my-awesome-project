import sys
from PIL import Image
import shots2 as S
from core import *
def render(fn,T):
    fr=Frame(seed=int(T*30)); kw=fn(fr,T); return finish(fr,**kw)
sel=[(S.shot_K,93.5),(S.shot_K,94.8),(S.shot_L,95.5),(S.shot_L,96.5),(S.shot_L,97.8),(S.shot_L,100.2),(S.shot_L,102.5),(S.shot_L,104.8)]
ims=[Image.fromarray(render(f,T)).resize((300,533)) for f,T in sel]
sh=Image.new('RGB',(1200,1066))
for i,im in enumerate(ims): sh.paste(im,((i%4)*300,(i//4)*533))
sh.save('/tmp/verify/s3.png')
