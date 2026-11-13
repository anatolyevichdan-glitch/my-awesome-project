import math, sys, skia, numpy as np
from PIL import Image
from gfx import *
import rig as R
W_, H_ = 2200, 1000
surf = skia.Surface(W_, H_); cv = surf.getCanvas()
cv.clear(skia.Color4f(0.30, 0.34, 0.45, 1))
views = [0, 0.7, 1.5708, 2.4, 3.1416]
for i, y in enumerate(views):
    p = R.Pose(); p.yaw = y; p.e = R.EXPR['neutral']
    R.draw_hero(cv, p, 220 + i * 420, 900, 0.78)
Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)[..., :3]).save('/tmp/verify/model1.png')
names = ['neutral', 'suspicious', 'mild_fear', 'shock', 'panic', 'exhausted', 'look_up', 'terror']
surf = skia.Surface(2200, 700); cv = surf.getCanvas(); cv.clear(skia.Color4f(0.30, 0.34, 0.45, 1))
for i, n in enumerate(names):
    p = R.Pose(); p.yaw = 0.35 if i % 2 else -0.3; p.e = R.EXPR[n]
    if n == 'look_up': p.head_pitch = -0.5
    R.draw_hero(cv, p, 140 + i * 270, 1500, 1.2)
Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)[..., :3]).save('/tmp/verify/model2.png')
