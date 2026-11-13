import math, skia, numpy as np
from PIL import Image
from gfx import *
import rig as R, anim as A, scenes as S
from rig import V
f = Frame(0, 1)
S.street(f, 0, 0)
poses = []
p = R.Pose(); A.phone_pose(p); p.yaw = 0.3; p.e = R.EXPR['worried']; poses.append(p)
p = R.Pose(); A.lips_pose(p); p.e = R.EXPR['shh']; poses.append(p)
p = R.Pose(); A.run(p, 1.0); p.yaw = 1.5708; p.e = R.EXPR['panic']; poses.append(p)
p = R.Pose(); p.yaw = 0.0; p.e = R.EXPR['terror']; p.black_eyes = True; poses.append(p)
for i, p in enumerate(poses):
    r = A.hero(f, p, 130 + i * 270, 1400, .42, black_eyes=p.black_eyes)
    if p.holding:
        A.draw_phone(f.ch.c, f, r['hand'][1], .4, glow=1)
A.creature(f, 800, 1500, 700, 0)
a = f.compose()
Image.fromarray(a).crop((0, 500, 1080, 1600)).save('/tmp/verify/pose.png')
