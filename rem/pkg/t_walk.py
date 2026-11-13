import math, skia, numpy as np
from PIL import Image
from gfx import *
import rig as R
V=R.V
def walk(p,ph,amp=1.0):
    for sd,o in ((1,0),(-1,math.pi)):
        c=math.sin(ph+o); l=max(0,math.cos(ph+o))
        f=p.foot[sd]; p.foot[sd]=V(f[0],R.ANKLE_H+95*l*amp,200*c*amp)
        p.foot_pitch[sd]=0.5*l*amp-0.2*c*amp
        p.hand[sd]=V(p.hand[sd][0],-345+10*abs(c),-30*c*amp*sd*-1+20)
    p.pelvis=V(0,-22*abs(math.sin(ph))*amp,0)
    p.lean=0.06*amp
surf=skia.Surface(2200,700);cv=surf.getCanvas();cv.clear(skia.Color4f(.3,.34,.45,1))
for i in range(8):
    p=R.Pose();p.yaw=1.5708 if i<8 else 0;walk(p,i*math.pi/4);R.draw_hero(cv,p,140+i*270,640,.5)
Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType,alphaType=skia.kUnpremul_AlphaType)[...,:3]).save('/tmp/verify/walk.png')
