import sys
for _p in ('/tmp/hoplite/workspace/rem', '/tmp/hoplite/workspace/opus', '/tmp/hoplite/workspace/lp'):
    sys.path.insert(0, _p)
import skia, numpy as np
from PIL import Image
import env as E, world as Wd, toon2 as T2, rig as R, motion as M
from rig import V
from t_sheet import EX

frames = []


def snap(fn):
    s = skia.Surface(1080, 1920); cv = s.getCanvas(); cv.clear(skia.ColorBLACK)
    fn(cv)
    a = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3].astype(np.float32)
    frames.append(Image.fromarray(Wd.grade(a, 0)).resize((360, 640)))


def f1(cv):
    E.college(cv, 0, cx=0, door_open=0.5)
    p = R.Pose(); M.walk(p, 0.3)
    with T2.use('hero'):
        T2.draw(cv, p, 700, 1500, 0.5, yaw=0.9)
    Wd.rainfall(cv, 0)


def f2(cv):
    Wd.sky(cv, *E.NIGHT, 1500); Wd.street_ground(cv, 1500, 0)
    E.bus_stop(cv, 560, 1500, 1.1)
    p = R.Pose(); M.stand(p)
    with T2.use('hero'):
        T2.draw(cv, p, 520, 1530, 0.45, yaw=0.4)
    Wd.lamp(cv, 950, 1620, 800)
    Wd.rainfall(cv, 0)


def f3(cv):
    Wd.sky(cv, *E.NIGHT, 1400); Wd.street_ground(cv, 1400, 0)
    E.bus_side(cv, 560, 1500, 0.9, 0.0, door=0.7)


def f4(cv):
    Wd.sky(cv, *E.NIGHT, 1300); Wd.street_ground(cv, 1300, 0)
    E.bus_front(cv, 540, 1400, 1.6, 0)


def interior(cv, look):
    cam = E.Persp(0, 150, 120 if look > 0 else 900, look=look)
    items = []
    seats = [(-80, 360, 'pax0'), (80, 460, 'pax1'), (-80, 560, 'pax2'), (80, 660, 'pax3'), (-80, 760, 'pax4'), (80, 860, 'pax5')]
    for x, z, nm in seats:
        def fn(x=x, z=z, nm=nm):
            X, Y, s = E.person_at(cam, x, z - 30)
            p = R.Pose(); M.sit(p); p.e = EX['neutral'] | dict(lid=0.4)
            if nm == 'pax2':
                p.head_roll = 0.6; p.head_pitch = 0.5
            with T2.use(nm):
                T2.draw(cv, p, X, Y, s, yaw=0.0 if look > 0 else 3.14159, ground_shadow=0)
        items.append((z, fn))

    def babka():
        X, Y, s = E.person_at(cam, 0, E.REAR_Z - 30)
        p = R.Pose(); M.sit(p); p.e = EX['neutral'] | dict(smile=0.3)
        with T2.use('babka'):
            T2.draw(cv, p, X, Y, s, yaw=0.0 if look > 0 else 3.14159, ground_shadow=0)
    items.append((E.REAR_Z, babka))
    E.bus_interior(cv, 0.3, cam, items=items)


snap(f1); snap(f2); snap(f3); snap(f4)
snap(lambda cv: interior(cv, 1)); snap(lambda cv: interior(cv, -1))
snap(lambda cv: E.home_street(cv, 0))
sheet = Image.new('RGB', (360 * 4, 640 * 2))
for i, im in enumerate(frames):
    sheet.paste(im, ((i % 4) * 360, (i // 4) * 640))
sheet.save('/tmp/verify/lp_env.jpg', quality=88)
