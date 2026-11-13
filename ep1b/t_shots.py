import sys, numpy as np
from PIL import Image
import shots1 as S
from core import *
def render(fn,T):
    fr=Frame(seed=int(T*30))
    kw=fn(fr,T)
    return finish(fr,**kw)
tests=[(S.shot_A,1.0),(S.shot_A,5.0),(S.shot_B,9.0),(S.shot_B,13.8),(S.shot_B,16.5),(S.shot_C,20.0),(S.shot_C,23.5),(S.shot_D,28.0),(S.shot_D,39.5),(S.shot_D,43.8),(S.shot_E,52.5),(S.shot_F,57.0)]
sel=[tests[int(i)] for i in sys.argv[1:]] if len(sys.argv)>1 else tests
ims=[Image.fromarray(render(f,T)).resize((300,533)) for f,T in sel]
cols=6; rows=(len(ims)+cols-1)//cols
sheet=Image.new('RGB',(300*cols,533*rows))
for i,im in enumerate(ims): sheet.paste(im,((i%cols)*300,(i//cols)*533))
sheet.save('/tmp/sheet.png')
