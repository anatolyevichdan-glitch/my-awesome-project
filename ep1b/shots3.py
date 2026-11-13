"""Shots part 3 (v2 rig): helpers, opening walk, side-tracking chase."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core import *
import char2 as C
import entity3d as E
import anim2 as AN
from anim2 import sstep, kf, klin, blink_at, eyes_alive, gait, idle
from bg import Persp, flat_street, courtyard, tower, shop_front, draw_shop_window, hsh, fogc
from shots1 import add_lamps, add_extra, tp, zoomf, finish_kw, AMB, font, integ, _paste

HS = 0.95
GROUND = 1560


def blend_pose(a, b, t):
    """blend two Poses (numeric attrs, tuples, dicts) -> new Pose"""
    t = max(0.0, min(1.0, t))
    r = C.Pose()
    for k, va in a.__dict__.items():
        vb = b.__dict__.get(k, va)
        r.__dict__[k] = _bl(va, vb, t)
    return r


def _bl(a, b, t):
    if isinstance(a, bool) or isinstance(a, str): return b if t > 0.5 else a
    if isinstance(a, (int, float)): return a + (b - a) * t
    if a is None or b is None: return b if (a is None and t > 0.5) or (b is None and t > 0.5) else a if t <= 0.5 else b
    if isinstance(a, dict): return {k: _bl(a[k], b[k], t) for k in a}
    if isinstance(a, (tuple, list)): return type(a)(_bl(x, y, t) for x, y in zip(a, b))
    return a if t < 0.5 else b


def hero2(fr, x, y, s, p, occ=False, tint=None):
    out = C.draw_hero(fr.ga, x, y, s, p, tint=tint)
    fr.ge.mask = True; C.draw_hero(fr.ge, x, y, s, p, tint=tint); fr.ge.mask = False
    if occ: C.draw_hero(fr.go, x, y, s, p, tint=tint)
    return out


def creature2(fr, x, y, s, p, eyes=1.0, glow=1.0):
    out = E.draw_creature(fr.gn, x, y, s, p)
    if eyes > 0.02 or 'mouth' in out:
        E.draw_creature_glow(fr.ge, out, s, a=eyes * glow)
    return out


def cam_shake(fr, t, amp=2.0, zoom=1.0, dx=0.0, dy=0.0):
    fr.cam(dx + amp * math.sin(3.1 * t) + 0.6 * amp * math.sin(7.3 * t), dy + amp * math.sin(2.3 * t + 1) + 0.6 * amp * math.sin(5.9 * t), zoom)


# ---------------------------------------------------------------- A: opening front walk (0 - 6.3)
def shot_A(fr, T):
    t = T
    P = Persp()
    cam = -380 * t
    lamps = P.draw(fr.ga, fr.ge, cam_z=cam, lamp_state=lambda k: 1.0)
    cam_shake(fr, t, 2.5, 1.0 + 0.03 * t / 6.3)
    add_lamps(fr, lamps)
    f = 0.95
    ph = f * t
    # walk in a worried-but-unaware mood; slow glance to the sides
    e = AN.blend_expr_safe(C.EXPR['neutral'], C.EXPR['worried'], 0.25 * sstep((t - 2.2) / 3)) if hasattr(AN, 'blend_expr_safe') else C.blend('neutral', 'worried', 0.22 * sstep((t - 2.2) / 3))
    e = eyes_alive(e, t, 1)
    walk = gait(ph, A=92, D=0.6, L=56, rho=0.94, Sx=19, Tp=0.12, Tc=0.17, arm=1.0, lean=0.035)
    walk.yaw = 0.0 + 0.10 * math.sin(t * 0.9)
    walk.e = e; walk.blink = blink_at(t, 1)
    walk.head_yaw = 0.18 * math.sin(t * 0.7) * (1 if t > 1.2 else 0.3)
    hero2(fr, 540, GROUND + 10, 0.95, walk, occ=True)
    # creature emerging far behind, same direction of travel (toward camera)
    z = 1250 - 70 * t
    sc = 0.95 * 349 / z * 0.95
    ey = 700 + 300 * 1000 / z
    ex_ = 540 + 150 * math.sin(0.33 * t + 0.4)
    al = 0.85 * sstep((t - 0.9) / 2.6) + 0.15 * sstep((t - 4.2) / 2.0)
    cp = E.creature_walk(0.5 * t * 0.8 + 0.3)
    cp.yaw = 0.0 + 0.15 * math.sin(t * 0.5)
    cp.neck_pitch = 0.55 + 0.1 * math.sin(t * 0.8)
    creature2(fr, ex_, ey, sc, cp, eyes=al)
    return finish_kw(fog=0.19, fog_y=0.42, ent_alpha=al, t=t)


# ---------------------------------------------------------------- B: side track (6.3 - 17.6)
def vh(T):
    return klin(T, [(6.3, 0), (6.7, 330), (11.9, 330), (12.5, 540), (14.05, 540), (14.65, 0)])


def gap(T):
    return kf(T, [(6.3, 640), (11.4, 380), (13.3, 330), (14.7, 230), (15.84, 200)])


def ve(T):
    dg = (gap(T + 0.02) - gap(T - 0.02)) / 0.04
    return max(0.0, vh(T) - dg)


def hero_gait_params(T):
    k = sstep((T - 11.94) / 0.6)
    return dict(A=AN.lerp1(92, 128, k), D=AN.lerp1(0.6, 0.54, k), L=AN.lerp1(56, 96, k), rho=AN.lerp1(0.93, 0.87, k),
                Tc=AN.lerp1(0.17, 0.24, k), lean=AN.lerp1(0.04, 0.15, k), arm=AN.lerp1(1.0, 1.25, k), Sx=AN.lerp1(18, 12, k)), k


def hero_phase(T):
    def fq(x):
        pr, _ = hero_gait_params(x)
        return (vh(x) / HS) * pr['D'] / (2 * pr['A'])
    return integ('hph', fq, 6.3, T)


def creature_phase(T):
    return integ('cph', lambda x: (ve(x) / 0.72) * 0.64 / (2 * 190.0), 6.3, T)


def shot_B(fr, T):
    t = T
    camx = 300 + integ('vhx', vh, 6.3, T)
    lamps = flat_street(fr.ga, fr.ge, camx)
    cam_shake(fr, t, 1.6)
    add_lamps(fr, lamps)
    v = vh(T)
    pr, k = hero_gait_params(T)
    e = C.blend('neutral', 'worried', 0.25 + 0.5 * sstep((T - 11) / 1.2))
    if T > 14.3: e = C.blend(e, 'scared', sstep((T - 14.3) / 0.5))
    e = eyes_alive(e, t, 2, 0.5)
    brake_t = 14.3
    if T < brake_t:
        ph = hero_phase(T)
        p = gait(ph, **pr)
    else:
        ph = hero_phase(brake_t)
        pw = gait(ph, **pr)
        stand = idle(t, e, seed=2, yaw=0)
        stand.foot[1] = (HW(1), C.ANKLE, 70); stand.foot[-1] = (-HW(1), C.ANKLE, -30)
        stand.lean = -0.10
        stand.hand[1] = (110, 640, 70); stand.hand[-1] = (-110, 640, 70)   # arms thrown out for balance
        kb = sstep((T - brake_t) / 0.32)
        p = blend_pose(pw, stand, kb)
        settle = sstep((T - 14.75) / 0.9)
        rest = idle(t, e, seed=2)
        rest.foot[1] = (HW(1), C.ANKLE, 25); rest.foot[-1] = (-HW(1), C.ANKLE, -20)
        rest.hand[1] = (100, 560, 40); rest.hand[-1] = (-100, 560, 40)
        rest.lean = 0.02
        p = blend_pose(p, rest, settle)
        # frozen torso, glance back toward the following sound
        p.head_yaw = -0.7 * sstep((T - 16.3) / 0.8) * (1 - sstep((T - 17.3) / 0.3))
    p.yaw = math.pi / 2
    p.e = e; p.blink = blink_at(t, 2)
    hx = 600
    hero2(fr, hx, GROUND - 14, HS, p, occ=True)
    # creature
    g_ = gap(T)
    cph = creature_phase(T)
    freeze = sstep((T - 15.84) / 0.45)
    cp = E.creature_walk(cph)
    st = E.CPose(); st.neck_pitch = 0.62; st.curl = 0.8
    st.foot[1] = (E.HIPW, 150, 90); st.foot[-1] = (-E.HIPW, 150, -90)
    cp = blend_pose_c(cp, st, freeze)
    cp.yaw = math.pi / 2
    cp.lean = 0.38 + 0.08 * sstep((T - 12) / 1.5) * (1 - freeze)
    cp.head_roll = cp.head_roll * (1 - freeze) + 0.55 * sstep((T - 16.1) / 1.4)
    cp.neck_pitch = cp.neck_pitch * (1 - 0.3 * freeze) + 0.12 * math.sin(T * 0.9) * freeze
    ex_ = hx - g_ - 60
    creature2(fr, ex_, GROUND - 6, 0.72, cp, eyes=1.0)
    return finish_kw(fog=0.22, fog_y=0.6, t=t)


def HW(sd): return C.HIP_W + 4


def blend_pose_c(a, b, t):
    r = E.CPose()
    for k, va in a.__dict__.items():
        vb = b.__dict__.get(k, va)
        r.__dict__[k] = _bl(va, vb, t)
    return r
