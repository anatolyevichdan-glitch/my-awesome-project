"""Scenes 6-9: escape, the double, the warning from the double, the final reveal."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import rig
from rig import clamp, lerp, smooth, expr, expr_mix
from comp import *
from world import Cam, W, H
from scenes_a import hero_walk_pose, breathe, blur_bg
from scenes_b import shop_bg, flick


def black(): return Image.new('RGB', (W, H), (0, 0, 0))


def run_pose(dist, extra=None):
    P = dict(p=dist / (4 * 0.62), amp=1.0, run=1.0)
    if extra: P.update(extra)
    return P


def fg_blob(img, x, y, r, col=(14, 13, 16), blur=34):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([x - r, y - r * 1.15, x + r, y + r * 1.15], fill=col + (255,))
    d.polygon([(x - r * 2.2, y + r * 3), (x - r * 1.6, y + r * 1.1), (x + r * 1.6, y + r * 1.1), (x + r * 2.2, y + r * 3)], fill=(34, 36, 42, 255))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    img.paste(lay, (0, 0), lay)


# ============================================================ SCENE 6 (16 s)
def scene6(t):
    if t < 5.5:
        fxo = fx(); ppm = 560; gy = H * 0.80
        X = -6.0 + 5.2 * t
        camx = X + 0.4
        arr = shop_bg(camx, ppm, gy, t, 0.0)
        img = to_img(arr)
        # something follows far behind
        if t > 2.2:
            ex = X - lerp(11.0, 6.5, smooth(seg(t, 2.2, 5.5))) + (0.8 if int(t * 7) % 5 == 0 else 0)
            PE = dict(p=0.0, amp=0.0, t=t, head=(0, 0.05, 0.1), swing=0.05)
            fn = lambda d_, layer, ox, oy, s: rig.render_entity(d_, layer, ox, oy, s, math.pi / 2, PE)
            place(img, fn, W / 2 + (ex - camx) * ppm, gy + 0.1 * ppm, ppm * 0.8, ENT_EXT, alpha=0.9 * smooth(seg(t, 2.2, 3.5)), fog=0.4, reflect=0.2, soft=0.02)
        P = run_pose(5.2 * t, dict(head=(0, 0.0, 0)))
        fn = lambda d_, layer, ox, oy, s: rig.render_hero(d_, layer, ox, oy, s, math.pi / 2, P, rig.expr('fear'), 'hero', 0.6, (0.82, 0.95, 1.12), -1, 0.04)
        place(img, fn, W / 2 + (X - camx) * ppm, gy + 0.2 * ppm, ppm, HERO_EXT, reflect=0.3)
        return fxo.apply(np.asarray(img).astype(np.float32), t + 63, hor=H * 0.4, fog=0.3, rain=1.0)
    if t < 8.5:
        tb = t - 5.5
        wd = world('street'); li = [flick(t, i, 0.0, 0.6) if i < 4 else 1.0 for i in range(len(wd.lamps))]
        zh = 20.0 + 5.0 * tb
        cam = Cam(x=0.3, y=1.9, z=zh - 4.3, dir=1, f=1500, hor=H * 0.46 + drift(t, 2)[1] + 8 * math.sin(tb * 12), xoff=drift(t, 2)[0])
        arr, _ = wd.render(cam, li, amb=0.7, t=t)
        img = to_img(arr)
        P = run_pose(5.0 * tb + 3.0)
        put_hero(img, cam, wd, 0.0 + 0.0 * tb, zh, screen_yaw(cam, 1), P, rig.expr('fear'), li, reflect=0.4)
        return finish(img, t + 63, hor=cam.hor, fog=0.45)
    if t < 11.0:
        tb = t - 8.5
        wd = world('alley'); li = [1.0, 0.7, 0.4]
        zh = 5.0 + 4.6 * tb
        cam = Cam(x=0.0, y=1.8, z=zh - 4.0, dir=1, f=1500, hor=H * 0.46 + 10 * math.sin(tb * 12), xoff=drift(t, 2)[0])
        arr, _ = wd.render(cam, li, amb=0.5, t=t)
        img = to_img(arr)
        P = run_pose(4.6 * tb + 1.0)
        put_hero(img, cam, wd, 0.0, zh, screen_yaw(cam, 1), P, rig.expr('terror'), li, reflect=0.4)
        return finish(img, t + 63, hor=cam.hor, fog=0.5, bright=0.7)
    tc = t - 11.0
    wd = world('courtyard'); li = [0.7 + 0.3 * (int(t * 9) % 2), 0.8, 0.5, 0.9]
    def v(x): return lerp(5.2, 2.2, smooth(x / 5.0))
    zh = -14.0 + integ(v, tc)
    cam = Cam(x=0.0, y=1.5, z=7.0, dir=-1, f=1700, hor=H * 0.44 + drift(t, 1.5)[1], xoff=drift(t, 1.5)[0])
    arr, _ = wd.render(cam, li, amb=0.5, t=t, back_walls=[(-20.0, 28.8)])
    img = to_img(arr)
    spd = v(tc)
    run = clamp((spd - 1.5) / 3.7)
    S = 0.30 + 0.32 * run
    dist = integ(lambda x: v(x) / (4 * (0.30 + 0.32 * clamp((v(x) - 1.5) / 3.7))), tc)
    P = dict(p=dist, amp=1.0, run=run, head=(0.5 * math.sin(tc * 1.5) * (tc > 2.5), 0.05, 0))
    put_hero(img, cam, wd, 0.0, zh, screen_yaw(cam, 1), P, rig.expr('fear'), li, reflect=0.35)
    return finish(img, t + 63, hor=cam.hor, fog=0.5, bright=0.7)


# ============================================================ SCENE 7 (9 s)
def stranger_pose(t, back=False):
    return dict(p=0.0, amp=0.0, hy=0.003 * breathe(t, 0.4), head=(0, 0.0, 0.06 * math.sin(t * 0.5)))


def scene7(t):
    wd = world('courtyard'); li = [0.5, 0.9, 0.3, 0.9]
    if t < 3.3:
        zc_ = -8.5
        cam = Cam(x=0.0, y=1.55, z=zc_, dir=1, f=1800, hor=H * 0.44 + drift(t, 1.5)[1], xoff=drift(t, 1.5)[0])
        arr, _ = wd.render(cam, li, amb=0.5, t=t, back_walls=[(36.0, 28.8)])
        img = to_img(arr)
        coll = 1.0
        sx_ = lerp(4.0, 0.15, smooth(seg(t, 0.0, 0.95)))
        # stranger walks in from the right, then squares up toward the hero
        if t < coll:
            P = dict(p=t * 0.9, amp=1.0, head=(0, 0, 0))
            yaw = -math.pi / 2 * (1 - smooth(seg(t, 0.55, 1.0))) * 1.0
            screen = lambda: None
            put_hero(img, cam, wd, sx_, -3.0, yaw, P, rig.expr('calm'), li, kind='double', ldir=-1)
        else:
            tc = t - coll
            put_hero(img, cam, wd, 0.15, -3.0, 0.0, dict(p=0, amp=0, lean=0.12 * math.exp(-tc * 3), head=(0, 0, 0)), rig.expr('calm'), li, kind='double')
        # hero runs in from behind, collides, stumbles back
        if t < coll:
            zh = -6.5 + 3.0 * t
            P = run_pose(3.0 * t + 2)
            put_hero(img, cam, wd, -0.1, zh, math.pi, P, rig.expr('terror'), li, reflect=0.35)
        else:
            tc = t - coll
            back = 0.9 * smooth(seg(tc, 0, 0.6))
            zh = -6.5 + 3.0 * coll - back
            flail = math.sin(tc * 14) * math.exp(-tc * 2.0)
            P = dict(p=-back * 0.6, amp=0.0 if tc > 0.9 else clamp(1 - tc / 0.9), run=0.2, lean=-0.4 * math.exp(-tc * 1.6),
                     armL=((0.45, 1.3 + 0.2 * flail, 0.2), (0.5, 0, -1)), armR=((-0.45, 1.2 - 0.2 * flail, 0.15), (-0.5, 0, -1)),
                     head=(0, -0.2 * math.exp(-tc * 2), 0))
            put_hero(img, cam, wd, -0.1, zh, math.pi, P, rig.expr('terror'), li, reflect=0.35)
        return finish(img, t + 79, hor=cam.hor, fog=0.45, bright=0.7)
    tc = t - 3.3
    cam0 = Cam(x=0.0, y=1.5, z=-9.0, dir=1, f=1800, hor=H * 0.44)
    arr = blur_bg('s7bg', wd, cam0, li, 0.5, 26, 0.7)
    img = to_img(arr)
    fg_blob(img, 70, 1560, 300)
    R = ease(300, 360, tc / 5.7, lambda x: x)
    s_big = R / 0.108
    P = stranger_pose(tc)
    e = rig.expr('calm', gx=0.0)
    fn = lambda d_, layer, ox, oy, s: rig.render_hero(d_, layer, ox, oy, s, 0.0, P, e, 'double', 0.8, (0.8, 0.95, 1.15), -1, 0.0)
    place(img, fn, W / 2 + 40, 700 + 1.74 * s_big, s_big, (1.2, 1.2, 2.4, 0.01), q=1)
    out = np.asarray(img).astype(np.float32)
    return fx().apply(out, t + 79, hor=H * 0.44, fog=0.2, rain=0.5, splash=False, blur=0.9)


# ============================================================ SCENE 8 (8 s)
def scene8(t):
    wd = world('courtyard'); li = [0.5, 0.9, 0.3, 0.9]
    cam0 = Cam(x=0.0, y=1.5, z=-9.0, dir=1, f=1800, hor=H * 0.44)
    if t < 3.0:
        arr = blur_bg('s8bg', wd, cam0, li, 0.5, 12, 0.75)
        img = to_img(arr)
        gy = H * 0.97
        st = math.sin(t * 9) + 0.6 * math.sin(t * 15)
        k_ = smooth(seg(t, 0.6, 1.0))
        s_h, s_s = 1000.0, 820.0
        hx = 330 + 16 * st * k_; sxs = 700
        reach = smooth(seg(t, 0.2, 0.8))
        gy_s = gy - 70
        def tgt(sg): return ((hx + sg * 0.2 * s_h - sxs) / s_s, 1.46 + 0.02 * st, 0.5)
        Ps = dict(p=0, amp=0, lean=0.1 * reach, head=(-0.28 * smooth(seg(t, 0.3, 0.8)), 0, 0))
        if reach > 0.02:
            a = tgt(-1); b = tgt(1)
            Ps['armL'] = ((lerp(0.2, b[0], reach), lerp(0.9, b[1], reach), lerp(0.1, b[2], reach)), (0.4, -0.3, -1))
            Ps['armR'] = ((lerp(-0.2, a[0], reach), lerp(0.9, a[1], reach), lerp(0.1, a[2], reach)), (-0.4, -0.3, -1))
        es = expr_mix('grim', 'fear', smooth(seg(t, 1.5, 3.0)))
        fn = lambda d_, layer, ox, oy, s: rig.render_hero(d_, layer, ox, oy, s, 0.0, Ps, es, 'double', 0.55, (0.82, 0.95, 1.15), 1, 0.04)
        place(img, fn, sxs, gy_s, s_s, HERO_EXT, q=1)
        Ph = dict(p=0, amp=0, lean=-0.06 + 0.07 * st * k_, twist=0.45 * st * k_,
                  armL=((0.3, 1.2, 0.45), (0.5, -0.3, -0.5)), armR=((-0.3, 1.2, 0.45), (-0.5, -0.3, -0.5)), head=(0.1 * st * k_, 0, 0.08 * st * k_))
        fn = lambda d_, layer, ox, oy, s: rig.render_hero(d_, layer, ox, oy, s, math.pi, Ph, rig.expr('terror'), 'hero', 0.5, (0.82, 0.95, 1.15), -1, 0.04)
        place(img, fn, hx, gy + 140, s_h, HERO_EXT, q=1)
        return fx().apply(np.asarray(img).astype(np.float32), t + 88, hor=H * 0.4, fog=0.3, rain=0.8, splash=False)
    if t < 6.0:
        tc = t - 3.0
        arr = blur_bg('s8bg2', wd, cam0, li, 0.5, 26, 0.65)
        img = to_img(arr)
        fg_blob(img, 90 + 12 * math.sin(tc * 9) * (1 - seg(tc, 0, 2.0)), 1540, 310)
        e = expr_mix('grim', 'fear', smooth(seg(tc, 0.0, 0.6)))
        gaze_up = smooth(seg(tc, 1.0, 1.5))
        e = expr_mix(e, 'terror', smooth(seg(tc, 1.5, 2.6)))
        e = dict(e, gy=0.8 * gaze_up, gx=0.0)
        pitch = -0.18 * gaze_up
        yaw = 0.0 + 0.1 * gaze_up
        R = 340 + 10 * tc
        s_big = R / 0.108
        P = dict(p=0, amp=0, hy=0.004 * math.sin(tc * 3), head=(yaw, pitch, 0.04),
                 armL=((0.3, 1.5, 0.3), (0.5, 0, -1)), armR=((-0.3, 1.5, 0.3), (-0.5, 0, -1)))
        fn = lambda d_, layer, ox, oy, s: rig.render_hero(d_, layer, ox, oy, s, 0.0, P, e, 'double', 0.8, (0.8, 0.95, 1.15), -1, 0.0)
        place(img, fn, W / 2 + 40, 740 + 1.74 * s_big, s_big, (1.2, 1.2, 2.4, 0.01), q=1)
        return fx().apply(np.asarray(img).astype(np.float32), t + 88, hor=H * 0.44, fog=0.2, rain=0.5, splash=False, blur=0.9)
    tc = t - 6.0
    cam = Cam(x=0.0, y=1.6, z=-7.0, dir=1, f=1800, hor=H * 0.45, xoff=drift(t, 1)[0])
    arr, _ = wd.render(cam, li, amb=0.5, t=t, back_walls=[(36.0, 28.8)])
    img = to_img(arr)
    back = lerp(0.0, 2.2, smooth(seg(tc, 0.3, 2.0)))
    ph = -back / (4 * 0.30)
    mv = 0.0 < (back % 2.2) < 2.1 and tc < 2.0
    Ps = dict(p=ph, amp=1.0 if mv else 0.0, head=(0, 0, 0.0), armL=((0.3, 1.0 - 0.3 * smooth(seg(tc, 0, 1)), 0.1), (0.5, -0.5, -0.5)), armR=((-0.3, 1.0, 0.1), (-0.5, -0.5, -0.5)))
    put_hero(img, cam, wd, 0.0, 2.0 + back, 0.0, Ps, expr_mix('terror', 'terror', 0), li, kind='double')
    Ph = dict(p=0, amp=0, lean=0.02, head=(0, 0, 0))
    put_hero(img, cam, wd, 0.0, -0.3, math.pi, Ph, rig.expr('fear'), li, reflect=0.3)
    return finish(img, t + 88, hor=cam.hor, fog=0.45, bright=0.7)


# ============================================================ SCENE 9 (12 s)
def scene9(t):
    world("courtyard").skytop = (26, 36, 54)
    if t >= 10.4: return black()
    wd = world('courtyard'); li = [0.35 + 0.35 * (int(t * 6) % 2 if t > 5 else 1), 0.5, 0.15, 0.4]
    turn = smooth(seg(t, 1.2, 4.2))
    hor = lerp(H * 0.46, 1700, smooth(seg(t, 3.8, 7.6)))
    cam = Cam(x=0.0, y=1.6, z=8.0, dir=-1, f=lerp(1700, 1000, smooth(seg(t, 3.8, 7.6))), hor=hor + drift(t, 0.5)[1], xoff=drift(t, 0.5)[0])
    if 7.7 <= t < 9.0:
        tc = t - 7.7
        arr = np.full((H, W, 3), 8, np.float32)
        img = to_img(arr)
        e = expr_mix('fear', 'terror', smooth(seg(tc, 0, 0.5)))
        e = dict(e, gy=0.6)
        R = ease(520, 600, tc / 1.3)
        sp_ = rig.head_sprite(R, 0.0, -0.3, e, 'hero', 0.55, (0.75, 0.92, 1.2), ldir=1, sweat=0.6)
        img.paste(sp_, (int(W / 2 - sp_.width / 2), int(H * 0.47 - sp_.height / 2)), sp_)
        return fx().apply(np.asarray(img).astype(np.float32), t + 96, hor=H * 0.45, fog=0.2, rain=0.4, splash=False, blur=0.8, bright=0.5)
    arr, _ = wd.render(cam, li, amb=0.35, t=t, back_walls=[(-20.0, 28.8)])
    img = to_img(arr)
    # the giant on the roof
    p = cam.proj(0.0, 28.8, -18.8)
    if p:
        bend = smooth(seg(t, 7.0, 10.2))
        PE = dict(p=0, amp=0, t=t, lean=0.05 + 0.85 * bend, head=(0, 0.1 + 0.5 * bend, 0.12 + 0.7 * bend), swing=0.03, spread=0.05)
        put_entity(img, cam, wd, 0, -18.8, 1, PE, li, alpha=1.0, fog=0.1, scale=5.5, reflect=0.0, base_xy=(p[0], p[1] + 14, p[3]), yaw=0.0)
    # the two characters at the foot of the frame
    P2 = dict(p=0, amp=0, head=(0, 0, 0))
    e = expr_mix('fear', 'terror', smooth(seg(t, 4.0, 7.0)))
    yaw = math.pi * turn
    sh = 0.14 * math.sin(t * 20) * smooth(seg(t, 6, 8))
    Ph = dict(p=0, amp=0, lean=0.02, head=(0.0, -0.1 * smooth(seg(t, 4.2, 6.0)) * 0, 0), twist=0)
    put_hero(img, cam, wd, 0.0, 0.0, yaw, Ph, e, li, reflect=0.0)
    Ps = dict(p=0, amp=0, head=(0, 0, 0), lean=0.02)
    put_hero(img, cam, wd, -1.0, 2.6, math.pi, Ps, rig.expr('terror'), li, kind='double', reflect=0.0)
    return finish(img, t + 96, hor=cam.hor, fog=0.4, bright=0.6)
