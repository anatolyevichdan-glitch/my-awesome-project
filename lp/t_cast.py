import sys
sys.path.insert(0, '/tmp/hoplite/workspace/rem'); sys.path.insert(0, '/tmp/hoplite/workspace/opus'); sys.path.insert(0, '/tmp/hoplite/workspace/lp')
import skia
from PIL import Image
import toon2 as T2
import rig as R
from rig import V
import motion as M
from t_sheet import EX

s = skia.Surface(2400, 1500); cv = s.getCanvas(); cv.clear(skia.Color(36, 40, 54))
lk = T2.Look(key=(-0.6, -0.5), rim=(120, 150, 210))


def fig(name, x, y, sc, yaw, e='neutral', blink=0.0, seated=False, **kw):
    p = R.Pose(); M.stand(p, t=0)
    p.e = EX[e] if isinstance(e, str) else e
    p.blink = blink
    if seated:
        M.sit(p) if hasattr(M, 'sit') else None
    with T2.use(name):
        T2.draw(cv, p, x, y, sc, yaw=yaw, look=lk, **kw)


for i, yaw in enumerate((0.0, 0.75, 1.57, 3.0)):
    fig('hero', 160 + i * 270, 700, 0.5, yaw, 'worried')
fig('driver', 1300, 700, 0.5, 0.0, EX['neutral'] | dict(lid=1.0))
fig('driver', 1560, 700, 0.5, 0.8, EX['neutral'] | dict(lid=1.0))
fig('babka', 1830, 700, 0.47, 0.0, EX['neutral'] | dict(smile=0.5, lid=0.35))
fig('babka', 2100, 700, 0.47, 0.6, EX['neutral'] | dict(smile=0.2))
fig('burned', 200, 1450, 0.5, 0.0, EX['neutral'] | dict(smile=0.6))
fig('burned', 470, 1450, 0.5, 0.5, EX['neutral'])
for i in range(6):
    fig(f'pax{i}', 800 + i * 270, 1450, 0.47, 0.3 * (i % 3), EX['neutral'] | dict(lid=0.5))
# close-ups
p = R.Pose(); M.stand(p, t=0); p.e = EX['neutral'] | dict(smile=0.55, lid=0.3)
Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]).save('/tmp/verify/lp_cast.png')
s2 = skia.Surface(2400, 900); cv = s2.getCanvas(); cv.clear(skia.Color(30, 34, 46))
for i, (nm, e) in enumerate([('hero', EX['shock']), ('driver', EX['neutral'] | dict(lid=1.0)), ('babka', EX['neutral'] | dict(smile=0.6, lid=0.3)),
                             ('burned', EX['neutral'] | dict(smile=0.7))]):
    p = R.Pose(); M.stand(p, t=0); p.e = e
    with T2.use(nm):
        T2.draw(cv, p, 300 + i * 600, 2800, 2.2, yaw=0.25, look=lk, ground_shadow=0)
Image.fromarray(s2.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]).save('/tmp/verify/lp_faces.png')
s3 = skia.Surface(1500, 700); cv = s3.getCanvas(); cv.clear(skia.Color(36, 40, 54))
for i, (nm, yaw) in enumerate((("hero", 0.9), ("babka", 0.0), ("pax0", 1.57), ("hero", 0.0))):
    p = R.Pose(); M.sit(p); p.e = EX["neutral"]
    with T2.use(nm):
        T2.draw(cv, p, 200 + i * 360, 650, 0.45, yaw=yaw, look=lk)
Image.fromarray(s3.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]).save('/tmp/verify/lp_sit.png')
