import sys, math
sys.path.insert(0, '/tmp/hoplite/workspace/opus'); sys.path.insert(0, '/tmp/hoplite/workspace/rem')
import skia
from PIL import Image
import creature2 as C
from t_sheet import save, bg, EX
import toon, rig as R

surf = skia.Surface(2000, 1300); cv = surf.getCanvas(); bg(cv, 2000, 1300)
for i, (fac, stp, rch, bend, roll) in enumerate([(-1, 0.0, 0.0, 0.0, 0.0), (-1, 0.3, 0.0, 0.0, 0.3), (0, 0.0, 0.0, 0.0, -0.5), (-1, 0.0, 0.8, 0.5, 0.2), (1, 0.6, 0.0, 0.0, 0.0)]):
    cp = C.CPose(); cp.facing = fac; cp.step = stp; cp.stride = 0.5 if stp else 0.0; cp.reach = {1: rch * 0.5, -1: rch}; cp.bend = bend; cp.head_roll = roll
    C.draw(cv, cp, 220 + i * 390, 1250, 1150, t=i * 0.7)
p = R.Pose(); p.e = EX['mild_fear']; p.yaw = 0.4
toon.draw(cv, p, 1880, 1250, 0.55)
save(surf, '/tmp/verify/opus_creature.png')
