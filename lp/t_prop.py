import sys
sys.path.insert(0, '/tmp/hoplite/workspace/opus'); sys.path.insert(0, '/tmp/hoplite/workspace/rem')
import skia, numpy as np
from PIL import Image
import rig as R
import toon, motion as M
from t_sheet import EX
hr, nh = float(sys.argv[2]), float(sys.argv[3])
toon.HEAD_R = hr; R.HEAD_R = hr; R.NECK_H = nh
s = skia.Surface(1600, 900); cv = s.getCanvas(); cv.clear(skia.Color(40, 44, 60))
for i, yaw in enumerate((0.0, 0.7, 1.57, 3.0)):
    p = R.Pose(); M.stand(p, t=0)
    p.e = EX['worried']
    toon.draw(cv, p, 220 + i * 380, 860, 0.62, yaw=yaw, look=toon.Look(key=(-0.6, -0.5), rim=(120, 150, 210)))
Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]).save(sys.argv[1])
