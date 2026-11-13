from common import *
from rig import V
from PIL import Image
import rig as R, motion as M
s = skia.Surface(2400, 900); cv = s.getCanvas(); cv.clear(skia.Color(36, 40, 54))
def mk(fn):
    p = R.Pose(); M.stand(p, t=0); p.e = EX['neutral']; fn(p); return p
tests = [
 ('R up', lambda p: (p.hand.__setitem__(1, V(80, 200, 40)), p.hand_mode.__setitem__(1, 'open'))),
 ('L up', lambda p: (p.hand.__setitem__(-1, V(-80, 200, 40)), p.hand_mode.__setitem__(-1, 'open'))),
 ('ear R', lambda p: (p.hand.__setitem__(1, V(-20, 95, 40)), p.hand_mode.__setitem__(1, 'phone'))),
 ('fwd R', lambda p: (p.hand.__setitem__(1, V(0, -60, 300)), p.hand_mode.__setitem__(1, 'open'))),
 ('fwd both', lambda p: [p.hand.__setitem__(sd, V(30*sd, -120, 240)) for sd in (1,-1)]),
 ('look up', lambda p: setattr(p, 'head_pitch', -0.5)),
]
for i, (nm, fn) in enumerate(tests):
    p = mk(fn)
    fig(cv, 'hero', p, 200 + i * 380, 850, 0.5, yaw=0.5)
    cv.drawString(nm, 120 + i*380, 60, E.font(40), P((255,255,0)))
Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]).save('/tmp/verify/pose2.png')
