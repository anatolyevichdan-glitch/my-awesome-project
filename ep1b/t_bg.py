import numpy as np
from PIL import Image
from core import *
from char import *
from bg import *
from anim import *
# frame 1: persp street front walk
fr=Frame()
P=Persp()
lamps=P.draw(fr.ga,fr.ge,cam_z=-200,lamp_state=lambda k:1.0)
fr.lamps=[l[:4] for l in lamps]
draw_hero(fr.ga,540,1560,0.95,walk_front(1.0,e=EXPR['worried']))
for i in range(1):
    draw_entity(fr.gn,540,P.pr(0,0,1100)[1],P.ground_scale(1100)*0.95*0.34,dict(stride=0.6,phase=1.0))
img=finish(fr,t=1.0)
Image.fromarray(img).save('/tmp/f1.png')
fr=Frame()
lamps=flat_street(fr.ga,fr.ge,camx=300)
fr.lamps=[l[:4] for l in lamps]
draw_hero(fr.ga,500,1520,0.95,walk_side(1.0,e=EXPR['worried']))
draw_entity(fr.gn,160,1520,0.95,dict(view='side',phase=0.4,stride=1,tall=1.15))
img2=finish(fr,t=1.0)
Image.fromarray(img2).save('/tmp/f2.png')
both=np.concatenate([img,img2],axis=1); Image.fromarray(both).save('/tmp/f12.png')
import time; t0=time.time(); finish(fr,t=1.0); print('finish s',time.time()-t0)
