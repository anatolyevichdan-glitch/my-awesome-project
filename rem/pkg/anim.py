import math, skia, numpy as np
from gfx import *
import rig as R
from rig import V
from env import TF


def ease(x):
    x = max(0, min(1, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def keyf(t, ks):
    """smooth interpolation through [(t, value), ...]"""
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t <= t1:
            return lerp(v0, v1, ease((t - t0) / max(1e-6, t1 - t0)))
    return ks[-1][1]


def kexp(t, ks):
    """expression keys [(t, name or dict), ...]"""
    g = lambda e: R.EXPR[e] if isinstance(e, str) else e
    if t <= ks[0][0]:
        return g(ks[0][1])
    for (t0, e0), (t1, e1) in zip(ks, ks[1:]):
        if t <= t1:
            return R.lerp_e(g(e0), g(e1), ease((t - t0) / max(1e-6, t1 - t0)))
    return g(ks[-1][1])


def blinkv(t, seed=0):
    ph = (t * 0.37 + seed * 0.17) % 1.0
    return max(0.0, 1 - abs(ph - 0.03) / 0.018) if abs(ph - 0.03) < 0.018 else 0.0


def idle(p, t, seed=0, breath=0.28):
    p.breath = t * breath + seed * 0.3
    p.blink = blinkv(t, seed)


def walk(p, ph, amp=1.0, arm=1.0, bob=22):
    for sd, o in ((1, 0), (-1, math.pi)):
        c = math.sin(ph + o)
        l = max(0, math.cos(ph + o))
        f = p.foot[sd]
        p.foot[sd] = V(f[0], R.ANKLE_H + 95 * l * amp, 200 * c * amp)
        p.foot_pitch[sd] = 0.5 * l * amp - 0.2 * c * amp
        h = p.hand[sd]
        p.hand[sd] = V(h[0], -345 + 12 * abs(c) * amp, 20 + 110 * c * sd * arm * amp)
    p.pelvis = V(0, -bob * abs(math.sin(ph)) * amp, 0)
    p.lean = 0.07 * amp


def run(p, ph, amp=1.5):
    walk(p, ph, amp, 1.4, bob=60)
    p.lean = 0.28
    for sd, o in ((1, 0), (-1, math.pi)):
        c = math.sin(ph + o)
        p.hand[sd] = V(p.hand[sd][0], -230 + 40 * c, 60 + 220 * c * sd)
        p.elbow_pole[sd] = V(0.5 * sd, 0.0, -1.0)
    p.head_pitch = -0.05


def stand(p):
    p.foot = {1: V(R.HIP_W, R.ANKLE_H, 0), -1: V(-R.HIP_W, R.ANKLE_H, 0)}
    p.foot_pitch = {1: 0.0, -1: 0.0}
    p.pelvis = V(0, 0, 0)


def phone_pose(p, sd=1, up=0.0):
    p.hand_abs[sd] = V(110 * sd, 690 + 160 * up, 300 - 40 * up)
    p.hand_mode[sd] = 'phone'
    p.hand_dir[sd] = V(0, 0.8, 0.4)
    p.holding = 'phone'


def lips_pose(p, sd=1, k=1.0):
    tgt = V(10 * sd, 960, 330)
    cur = V(30 * sd, 640, 120)
    p.hand_abs[sd] = cur + (tgt - cur) * k
    p.hand_mode[sd] = 'point'
    p.hand_dir[sd] = V(0, 0.9, 0.3)


def draw_phone(cv, f, hand, s, ang=-0.15, glow=0.0, lit=True):
    x, y = hand
    cv.save()
    cv.translate(x, y)
    cv.rotate(math.degrees(ang))
    w, h = 70 * s, 130 * s
    cv.drawRoundRect(skia.Rect(-w / 2, -h * 0.62, w / 2, h * 0.38), 10 * s, 10 * s, P((16, 18, 26)))
    col = (150, 200, 255) if lit else (28, 32, 44)
    cv.drawRoundRect(skia.Rect(-w / 2 + 5 * s, -h * 0.62 + 6 * s, w / 2 - 5 * s, h * 0.38 - 6 * s), 6 * s, 6 * s, P(col))
    cv.restore()
    if lit and glow > 0:
        f.glow(x, y - 40 * s, 110 * s * (1 + glow), (140, 190, 255), 0.3 * min(1, glow + 0.3))
        f.light_pool(x, y - 40 * s, 300 * s, (0.3, 0.42, 0.7), 0.5 * min(1, glow + 0.3))


def hero(f, p, x, y, s, yaw=None, tint=None, black_eyes=False, flip=False, layer='ch', shadow=0.5, **kw):
    p.black_eyes = black_eyes
    return R.draw_hero(getattr(f, layer).c, p, x, y, s, yaw=yaw, tint=tint, flip=flip, ground_shadow=shadow, **kw)


RIM = (70, 90, 170)


def creature(f, x, base, h, t, bend=0.0, alpha=1.0, layer='ch', eyes=True, reach=0.0, mist=1.0):
    """tall faceless shadow figure; bend leans torso and head down and to the left"""
    cv = getattr(f, layer).c
    col = (6, 6, 12)
    k = h / 1000.0
    sw = math.sin(t * 1.3)
    bx = bend * 260 * k
    hip = (x, base - 420 * k)
    sh = (x - bx * 0.9 + 6 * sw * k, base - 780 * k + bend * 260 * k)
    head = (x - bx * 1.9, base - 920 * k + bend * 420 * k)
    a = alpha

    def limb(p0, p1, w0, w1):
        pp_ = capsule_path(p0, p1, w0, w1)
        cv.drawPath(pp_, P(RIM, 0.8 * a, style="stroke", width=7 * k + 2))
        cv.drawPath(pp_, P(col, a))
    for sd in (-1, 1):
        limb((x + sd * 36 * k, hip[1]), (x + sd * 52 * k, base - 210 * k), 30 * k, 18 * k)
        limb((x + sd * 52 * k, base - 210 * k), (x + sd * 46 * k, base), 18 * k, 9 * k)
    tp = [(hip[0] - 50 * k, hip[1]), (hip[0] + 50 * k, hip[1]), (sh[0] + 66 * k, sh[1]), (sh[0] - 66 * k, sh[1])]
    cv.drawPath(path_smooth(tp), P(RIM, 0.8 * a, style="stroke", width=7 * k + 2))
    cv.drawPath(path_smooth(tp), P(col, a))
    for sd in (-1, 1):
        s0 = (sh[0] + 66 * k * sd, sh[1] + 10 * k)
        rr = reach if sd < 0 else 0
        el = (s0[0] + 80 * k * sd + 20 * k * sw * sd - rr * 220 * k, s0[1] + 240 * k - rr * 140 * k)
        hd = (el[0] + 30 * k * sd - rr * 260 * k, el[1] + 280 * k - rr * 120 * k)
        limb(s0, el, 22 * k, 14 * k)
        limb(el, hd, 14 * k, 9 * k)
        for j in range(4):
            cv.drawLine(hd[0], hd[1], hd[0] + (j - 1.5) * 12 * k * sd + 8 * k, hd[1] + (120 + 20 * j) * k, P(col, a, style='stroke', width=6 * k))
    limb((sh[0], sh[1] - 10 * k), head, 22 * k, 34 * k)
    hr_ = skia.Rect(head[0] - 52 * k, head[1] - 90 * k, head[0] + 52 * k, head[1] + 56 * k)
    cv.drawOval(hr_, P(RIM, 0.8 * a, style="stroke", width=7 * k + 2))
    cv.drawOval(hr_, P(col, a))
    for i in range(7 if mist else 0):
        ph = i * 0.9 + t * 0.9
        mx = x + (i - 3) * 38 * k + 14 * k * math.sin(ph)
        my = base - (200 + i * 90) * k
        cv.drawOval(skia.Rect(mx - 50 * k, my - 120 * k, mx + 50 * k, my + 120 * k), P(col, 0.35 * a * mist, blur=26 * k))
    if eyes:
        ex, ey = head[0], head[1] - 20 * k
        for sd in (-1, 1):
            cv.drawPath(path_poly([(ex + 12 * k * sd, ey), (ex + 40 * k * sd, ey - 12 * k), (ex + 36 * k * sd, ey + 6 * k)]), P((240, 244, 255), a))
        f.glow(ex, ey, 140 * k, (210, 220, 255), 0.45 * a)
    return dict(head=head, sh=sh)
