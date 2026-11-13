import time, numpy as np
from PIL import Image
from gfx import *
import rig as R
t0=time.time()
f=Frame(0,1)
f.bg.c.clear(skia.Color4f(.2,.22,.3,1))
f.set_ambient((0.3,0.4,0.6))
f.light_cone(300,300,1500,60,400,(1,.8,.5),1.0)
p=R.Pose(); p.e=R.EXPR['suspicious']
R.draw_hero(f.ch.c,p,540,1500,1.0,ground_shadow=.5)
f.glow(300,300,200,(255,200,120),.8)
a=f.compose()
print(time.time()-t0)
t0=time.time()
for i in range(3):
    f=Frame(0,1); f.bg.c.clear(skia.Color4f(.2,.22,.3,1)); f.set_ambient((0.3,0.4,0.6)); f.light_cone(300,300,1500,60,400,(1,.8,.5),1.0)
    R.draw_hero(f.ch.c,p,540,1500,1.0); a=f.compose()
print((time.time()-t0)/3)
Image.fromarray(a).save('/tmp/verify/speed.png')
