"""Scenes 3-5: reflection, second warning, lights out."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import rig
from rig import clamp, lerp, smooth, expr, expr_mix
from comp import *
from world import Cam, W, H
from scenes_a import draw_phone, draw_hand_on_phone, blur_bg, hero_walk_pose, breathe, mix


# ============================================================ shop front (2D flat world, metres)
def shop_bg(camx, ppm, gy, t, mann=0.0, lamp_on=1.0):
    img = Image.new('RGB', (W, H), (14, 18, 25))
    d = ImageDraw.Draw(img, 'RGBA')
    sx = lambda X: W / 2 + (X - camx) * ppm
    sy = lambda Y: gy - Y * ppm
    # wall
    for y in range(0, int(gy), 24):
        c = 16 + int(10 * y / max(gy, 1))
        d.rectangle([0, y, W, y + 24], fill=(c - 2, c + 2, c + 10))
    for kx in range(-3, 3):
        X0 = kx * 13.0
        # pilasters and cornice
        for X in (X0 - 4.4, X0 + 2.0, X0 + 6.5):
            d.rectangle([sx(X) - 0.14 * ppm, 0, sx(X) + 0.14 * ppm, sy(0)], fill=(26, 30, 38))
        d.rectangle([sx(X0 - 4.4), sy(4.2), sx(X0 + 6.5), sy(3.95)], fill=(30, 34, 44))
        # sign band
        d.rectangle([sx(X0 - 4.1), sy(3.75), sx(X0 + 1.8), sy(3.0)], fill=(12, 14, 19))
        d.rectangle([sx(X0 - 3.8), sy(3.5), sx(X0 - 1.2), sy(3.25)], fill=(18, 22, 28))
        # shop A: door + window
        d.rectangle([sx(X0 - 4.0), sy(2.6), sx(X0 - 2.9), sy(0)], fill=(8, 10, 14))
        d.rectangle([sx(X0 - 3.9), sy(2.5), sx(X0 - 3.0), sy(0.1)], fill=(5, 7, 11))
        wx0, wx1, wy0, wy1 = X0 - 1.7, X0 + 1.7, 0.55, 2.7
        d.rectangle([sx(wx0) - 0.09 * ppm, sy(wy1) - 0.09 * ppm, sx(wx1) + 0.09 * ppm, sy(wy0) + 0.09 * ppm], fill=(9, 11, 15))
        # interior
        iw0, iw1, ih0, ih1 = sx(wx0), sx(wx1), sy(wy1), sy(wy0)
        for y in range(int(ih0), int(ih1), 16):
            f = (y - ih0) / max(1, ih1 - ih0)
            c = int(3 + 12 * f)
            d.rectangle([iw0, y, iw1, y + 16], fill=(c, c + 3, c + 8))
        for Yh in (1.1, 1.75, 2.35):
            d.rectangle([sx(wx0), sy(Yh), sx(wx1), sy(Yh) + 3], fill=(26, 32, 42))
        rr = random.Random(int(kx * 17 + 5))
        for i in range(10):
            bx = rr.uniform(wx0 + 0.2, wx1 - 0.3); by = rr.choice([1.1, 1.75, 2.35])
            bw, bh = rr.uniform(0.15, 0.4), rr.uniform(0.1, 0.3)
            d.rectangle([sx(bx), sy(by + bh), sx(bx + bw), sy(by)], fill=(11, 14, 19), outline=(24, 30, 40))
        # mannequins
        for mi, mx in enumerate((X0 + 1.0, X0 - 0.9)):
            turn = mann if mi == 0 else 0.0
            hx = sx(mx) + (turn - 1) * 0.05 * ppm * 0 + 0
            d.ellipse([hx - 0.09 * ppm, sy(1.78), hx + 0.09 * ppm, sy(1.54)], fill=(16, 19, 25), outline=(38, 46, 60))
            if mi == 0:  # face plane: lighter sliver appears as it turns to the glass
                d.ellipse([hx - 0.05 * ppm * turn, sy(1.74), hx + 0.05 * ppm * turn, sy(1.58)], fill=(26, 32, 42))
            d.polygon([(hx - 0.22 * ppm, sy(1.45)), (hx + 0.22 * ppm, sy(1.45)), (hx + 0.17 * ppm, sy(0.85)), (hx - 0.17 * ppm, sy(0.85))],
                      fill=(14, 17, 23), outline=(34, 42, 54))
            d.line([hx, sy(0.85), hx, sy(0.6)], fill=(26, 30, 38), width=3)
        # shop B: shutter
        d.rectangle([sx(X0 + 2.1), sy(3.0), sx(X0 + 6.4), sy(0)], fill=(20, 24, 30))
        for Y in np.arange(0.05, 3.0, 0.12):
            d.line([sx(X0 + 2.1), sy(Y), sx(X0 + 6.4), sy(Y)], fill=(30, 35, 44), width=1)
    # pavement (wet)
    d.rectangle([0, gy, W, H], fill=(13, 17, 23))
    d.rectangle([0, gy, W, gy + 6], fill=(34, 40, 50))
    for i in range(14):
        y = gy + 40 + i * (H - gy) / 14
        d.line([0, y, W, y], fill=(16, 21, 28), width=1)
    arr = np.asarray(img).astype(np.float32)
    # lamp light on the left
    lx = sx(-7.0)
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
    g = np.exp(-(((xx - lx) / (4.2 * ppm)) ** 2 + ((yy - (gy - 3 * ppm)) / (4.5 * ppm)) ** 2))
    g = np.kron(g, np.ones((4, 4), np.float32))[:H, :W]
    arr += g[..., None] * np.array([70, 62, 44], np.float32) * lamp_on
    # pavement reflection streak
    g2 = np.exp(-(((xx - lx) / (0.7 * ppm)) ** 2 + ((yy - (gy + 1.2 * ppm)) / (2.0 * ppm)) ** 2))
    g2 = np.kron(g2, np.ones((4, 4), np.float32))[:H, :W]
    arr += g2[..., None] * np.array([90, 76, 50], np.float32) * lamp_on
    return arr


def glass_overlay(arr, t, ppm, camx, gy, strength=1.0):
    sx = lambda X: W / 2 + (X - camx) * ppm
    sy = lambda Y: gy - Y * ppm
    x0, x1, y0, y1 = int(sx(-1.7)), int(sx(1.7)), int(sy(2.7)), int(sy(0.55))
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    inside = ((xs > x0) & (xs < x1) & (ys > y0) & (ys < y1))
    sheen = np.clip(1 - np.abs((xs + ys * 0.6 - (x0 + 0.35 * (x1 - x0))) / (0.16 * (x1 - x0))), 0, 1) * 7 * strength
    arr = arr + (sheen * inside)[..., None] * np.array([0.9, 1.0, 1.1], np.float32)
    arr = arr + (inside[..., None] * np.array([3, 5, 8], np.float32)) * strength
    im = to_img(arr); d = ImageDraw.Draw(im, 'RGBA')
    rr = random.Random(2)
    for i in range(46):
        x = rr.uniform(x0, x1); y = rr.uniform(y0, y1)
        ln = rr.uniform(40, 200) * ppm / 600
        sp = rr.uniform(8, 30)
        yy = y0 + ((y - y0 + t * sp) % (y1 - y0))
        d.line([(x, yy), (x + 1.5, min(y1, yy + ln))], fill=(170, 190, 215, 26), width=1)
        d.ellipse([x - 2, yy - 2, x + 2, yy + 3], fill=(200, 215, 235, 38))
    return np.asarray(im).astype(np.float32)


def scene3(t):
    fxo = fx()
    wd = world('street')
    if t < 4.6:
        ppm = 640; gy = H * 0.80
        # hero walks +X, decelerates to stop at X=0, then turns to the glass
        def vx(x): return 1.25 * (1 - smooth(seg(x, 3.0, 3.7)))
        X = -5.2 + integ(vx, t)
        camx = X + 0.5 - 0.35 * smooth(seg(t, 2.5, 4.0))
        arr = shop_bg(camx, ppm, gy, t, 0.0)
        arr = glass_overlay(arr, t, ppm, camx, gy)
        img = to_img(arr)
        v = vx(t); S = 0.30
        turn = smooth(seg(t, 3.6, 4.5))
        yaw = math.pi / 2 + turn * (math.pi / 2)
        dist = X + 5.2
        P = dict(p=dist / (4 * S), amp=clamp(v / 1.25) ** 0.5 if v > 0.05 else 0.0, head=(0, 0.03, 0), lean=0.03)
        if P['amp'] > 0.01: P['p'] = dist / (4 * S * 1.0)
        # reflection of the street-facing passer-by in the glass: faint, same cycle
        lit = 0.42
        fn = lambda d_, layer, ox, oy, s: rig.render_hero(d_, layer, ox, oy, s, yaw, P, rig.expr('tense'), 'hero', lit, (0.8, 0.95, 1.15), -1, 0.08)
        sxp = W / 2 + (X - camx) * ppm
        place(img, fn, sxp, gy + 0.3 * ppm, ppm, HERO_EXT, reflect=0.28)
        out = np.asarray(img).astype(np.float32)
        return fxo.apply(out, t + 26, hor=H * 0.40, fog=0.35, rain=1.0, splash=True)
    # ---------------- OTS shots (B, C, D)
    tb = t - 4.6
    zoom = 1.0 + 0.10 * seg(t, 4.6, 13.4) + (0.25 * smooth(seg(t, 15.4, 17.0)) if False else 0)
    gy = H * 0.93; ppm = 560 * zoom; camx = 0.15
    mann = smooth(seg(t, 12.0, 16.5))
    arr = shop_bg(camx, ppm, gy, t, mann, lamp_on=0.7)
    # distant street lamp reflected on the glass (cold bar)
    img = to_img(arr)
    # reflection figure
    ex = 'tense'
    rel = smooth(seg(t, 5.4, 6.2))
    e = expr_mix('tense', 'relief', rel)
    finger = smooth(seg(t, 12.0, 13.6))
    if t > 7.2:  # reflection stops mirroring: expression freezes, becomes eerily blank
        e = expr_mix(e, dict(rig.EXPR['calm'], open=0.92), smooth(seg(t, 8.0, 9.2)))
    Pr = dict(p=0.0, amp=0.0, hy=0.0,
              armR=((0.015, 1.50, 0.13), (0.7, -0.4, -0.2)) if False else None,
              head=(0, 0, 0))
    wr_h = (0.0, 0.9, 0.05)
    mouth = (0.02, 1.62, 0.2)
    tgt = tuple(lerp(wr_h[i], mouth[i], finger) for i in range(3))
    if finger > 0.001:
        Pr['armR'] = (tgt, (0.8, -0.4, -0.6))
        Pr['armL'] = ((0.2, 0.9, 0.04), (0.5, -0.5, -0.5))
    if t < 15.8:
        # reflection stands further behind the glass (scale smaller), slightly to the left
        s_r = 540 * zoom * (1 + 0.1 * seg(t, 4.6, 8))
        rx = 660 - 20 * seg(t, 4.6, 13)
        ry = gy - 260 * zoom
        fn = lambda d_, layer, ox, oy, s: rig.render_hero(d_, layer, ox, oy, s, 0.0, Pr, e, 'hero', 0.6, (0.78, 0.95, 1.18), 1, 0.06)
        place(img, fn, rx, ry, s_r, HERO_EXT, alpha=0.8, fog=0.28, fogcol=(30, 44, 58), reflect=0.0)
    arr = np.asarray(img).astype(np.float32)
    arr = glass_overlay(arr, t, ppm, camx, gy)
    img = to_img(arr)
    if t < 15.8:
        # protagonist from behind in the foreground (left)
        step = smooth(seg(t, 13.4, 14.4))
        s_h = 880 * zoom * (1 + 0.28 * step)
        hx = 230 + 30 * seg(t, 4.6, 13) - 40 * step
        exh = math.sin(math.pi * seg(t, 5.3, 7.0)) if t < 7.0 else 0
        tilt = 0.40 * smooth(seg(t, 7.6, 9.4))
        hurt = smooth(seg(t, 13.4, 13.9))
        Ph = dict(p=0.0, amp=0.0, lean=-0.07 * exh - 0.1 * step, hy=-0.012 * exh, head=(0.0, 0.0, tilt * (1 - step)),
                  armL=((0.28, 1.0 + 0.5 * hurt, 0.1 + 0.2 * hurt), (0.6, -0.3, -0.5)) if step > 0.01 else None,
                  armR=((-0.28, 1.0 + 0.5 * hurt, 0.1 + 0.2 * hurt), (-0.6, -0.3, -0.5)) if step > 0.01 else None)
        lit = 0.48
        fn = lambda d_, layer, ox, oy, s: rig.render_hero(d_, layer, ox, oy, s, math.pi, Ph, rig.expr('relief'), 'hero', lit, (0.82, 0.95, 1.12), -1, 0.05)
        place(img, fn, hx, gy + 40 + 120 * step, s_h, HERO_EXT, reflect=0.3)
    else:
        # ECU of the reflection, finger to lips
        k = smooth(seg(t, 15.8, 17.0))
        R = 330 + 40 * k
        Pc = dict(Pr); Pc['armR'] = ((0.02, 1.62, 0.2), (0.8, -0.4, -0.6))
        s_big = R / 0.108
        oy = 760 + 1.74 * s_big * 1.0
        fn = lambda d_, layer, ox, oy_, s: rig.render_hero(d_, layer, ox, oy_, s, 0.0, Pc, e, 'hero', 0.62, (0.78, 0.95, 1.18), 1, 0.0)
        glass_dark = to_img(shop_bg(camx, ppm, gy, t, mann, 0.7))
        img = glass_dark
        place(img, fn, W / 2, oy, s_big, (1.2, 1.2, 2.4, 0.01), alpha=0.82, fog=0.25, fogcol=(30, 44, 58), q=1)
        img = to_img(glass_overlay(np.asarray(img).astype(np.float32), t, ppm, camx, gy))
    out = np.asarray(img).astype(np.float32)
    # darkening toward silence
    return fxo.apply(out, t + 26, hor=H * 0.40, fog=0.25, rain=0.8, splash=False)


# ============================================================ flicker helper
def flick(t, seed, start, amt=1.0):
    if t < start: return 1.0
    k = clamp((t - start) / 4.0)
    v = abs(math.sin(t * 37.3 + seed * 11.1) * math.cos(t * 53.7 + seed * 3.7) + 0.35 * math.sin(t * 91.0 + seed))
    thr = 0.28 + 0.2 * k
    on = 1.0 if v > thr else 0.12
    return lerp(1.0, on, min(1.0, amt * (0.5 + k)))


# ============================================================ SCENE 4 (10 s): second warning
def scene4(t):
    wd = world('street')
    zh = -30.0
    nl = len(wd.lamps)
    li = [flick(t, i, 1.2) for i in range(nl)]
    if t < 3.5:
        cam = Cam(x=0.0, y=1.38, z=zh - 2.2 + 0.0, dir=1, f=2000, hor=H * 0.43 + drift(t)[1] * 0.4, xoff=drift(t)[0] * 0.4)
        cam.z = zh - ease(2.4, 2.0, t / 3.5)
        arr, _ = wd.render(cam, li, amb=0.8, t=t + 43)
        img = to_img(arr)
        vib = math.sin(t * 90) * 0.006 * (1 if t < 0.9 else 0)
        up = smooth(seg(t, 0.6, 1.5))
        wr = tuple(lerp(a, b, up) for a, b in zip((-0.2, 0.95, 0.1), (-0.07, 1.22, 0.3)))
        e = dict(expr_mix('tense', 'fear', smooth(seg(t, 1.5, 3.2))), gy=-0.4 * up)
        Pp = hero_walk_pose(0, 0, dict(amp=0.0, armR=(wr, (-0.5, -0.6, -0.5)), armL=((0.2, 1.0, 0.1), (0.5, -0.5, -0.5)),
                                       head=(0, 0.2 * up, 0.0), hy=-0.01 + vib, lean=0.03 * up))
        put_hero(img, cam, wd, -0.15, zh, screen_yaw(cam, -1), Pp, e, li, lit_override=lerp(0.45, 0.95, up) * (0.5 + 0.5 * li[0]), sweat=0.5)
        p0 = cam.proj(-0.15, 0, zh); sx, sy, dz, k = p0
        hx = sx - wr[0] * k; hy = sy - wr[1] * k
        d = ImageDraw.Draw(img, 'RGBA')
        pw_, ph_ = 0.075 * k, 0.15 * k
        d.rounded_rectangle([hx - pw_ / 2, hy - ph_ * 0.9, hx + pw_ / 2, hy + ph_ * 0.1], radius=int(pw_ * 0.15), fill=(10, 11, 14))
        d.rounded_rectangle([hx - pw_ / 2 + 2, hy - ph_ * 0.9 + 2, hx + pw_ / 2 - 2, hy + ph_ * 0.1 - 2], radius=int(pw_ * 0.15), outline=(70, 90, 120), width=1)
        return finish(img, t + 43, hor=cam.hor, fog=0.5)
    if t < 7.4:
        tc = t - 3.5
        cam0 = Cam(x=0.0, y=1.3, z=-33.0, dir=1, f=1700, hor=H * 0.45)
        arr = blur_bg('s4bg', wd, cam0, [1.0] * nl, 0.5, 38, 0.7)
        mod = 0.65 + 0.35 * li[1]
        img = to_img(arr * mod)
        vib = math.sin(tc * 110) * 10 * (1 - seg(tc, 0, 0.5)) + (math.sin(tc * 110) * 8 * (1 - seg(tc - 2.1, 0, 0.5)) if tc > 2.1 else 0)
        msgs = [("HE IS NOT BEHIND YOU.", 0.7), ("HE IS INSIDE YOU.", 2.7)]
        sc = ease(0.85, 0.93, tc / 3.9)
        cx, cy = W * 0.5, H * 0.50
        draw_phone(img, cx, cy, sc, -3, msgs, tc, glow=0.8 + 0.4 * li[2], vib=vib)
        draw_hand_on_phone(img, cx + vib, cy, sc, -3, 0.9)
        # electrical interference bands
        arr = np.asarray(img).astype(np.float32)
        if li[3] < 0.5: arr = arr * 0.82
        return finish(to_img(arr), t + 43, hor=H * 0.45, fog=0.2, rain=0.4, splash=False)
    tc = t - 7.4
    cam0 = Cam(x=0.0, y=1.3, z=-33.0, dir=1, f=1700, hor=H * 0.45)
    arr, _ = wd.render(cam0, li, amb=0.5, t=t)
    bgi = to_img(arr).resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BICUBIC)
    img = to_img(np.asarray(bgi).astype(np.float32) * 0.8)
    e = expr_mix('fear', 'terror', smooth(seg(tc, 0.3, 2.0)))
    e = dict(e, gx=0.25 * math.sin(tc * 5) * (1 - smooth(seg(tc, 1.4, 2.0))))
    R = ease(560, 640, tc / 2.6)
    lit = 0.9 * (0.55 + 0.45 * li[1])
    sp_ = rig.head_sprite(R, 0.12 * math.sin(tc * 3.0) * 0, 0.0, e, 'hero', lit, (0.78, 0.95, 1.2), ldir=-1, sweat=0.8)
    img.paste(sp_, (int(W / 2 - sp_.width / 2), int(H * 0.47 - sp_.height / 2)), sp_)
    arr = np.asarray(img).astype(np.float32)
    return finish(to_img(arr), t + 43, hor=H * 0.45, fog=0.15, rain=0.3, splash=False, blur=0.8)


# ============================================================ SCENE 5 (10 s): lights go out
def scene5(t):
    wd = world('street'); nl = len(wd.lamps)
    li = [1.0] * nl
    # three lamps die in sequence (far -> near); the nearest one keeps struggling
    def die(t, t0): return 1.0 if t < t0 - 0.5 else (0.0 if t > t0 else (0.6 if int(t * 22) % 2 else 0.0))
    li[3] = die(t, 2.3); li[2] = die(t, 4.6); li[1] = die(t, 6.9)
    li[0] = 1.0 - 0.55 * smooth(seg(t, 7.5, 9.5)) if t < 9.3 else 0.3 + 0.2 * (int(t * 17) % 2)
    amb = lerp(0.85, 0.30, smooth(seg(t, 2.0, 8.0)))
    zh = -31.0
    push = ease(5.6, 4.4, t / 10.0)
    dx, dy = drift(t, 0.7)
    cam = Cam(x=0.0, y=1.45, z=zh - push, dir=1, f=1800, hor=H * 0.44 + dy, xoff=dx)
    arr, _ = wd.render(cam, li, amb=amb, t=t + 53)
    img = to_img(arr)
    # something moves in the distant shadows
    sh_t = t - 5.2
    if 0 < sh_t < 5.0:
        xe = lerp(3.4, -2.8, smooth(sh_t / 4.0)) if sh_t < 4.0 else -2.8
        step = sh_t * 0.45
        PE = dict(p=step, amp=0.7, t=t, head=(0, 0.1, 0.2), swing=0.1)
        vis = smooth(seg(sh_t, 0, 0.8)) * (1 - smooth(seg(sh_t, 3.6, 5.0)))
        put_entity(img, cam, wd, xe, zh + 24 - 3.0 * sh_t * 0.3, -1, PE, li, alpha=0.9 * vis, fog=0.45, reflect=0.2)
    # a second shape much nearer the end, standing still beside the dead lamp
    if t > 8.3:
        PE = dict(p=0, amp=0, t=t, head=(0, 0.1, 0.3), swing=0.05)
        put_entity(img, cam, wd, 3.9, zh + 11, -1, PE, li, alpha=smooth(seg(t, 8.3, 9.3)) * 0.85, fog=0.55, reflect=0.2)
    look = math.sin(t * 0.9) * 0.9 * smooth(seg(t, 0.6, 1.5))
    yaw_head = 0.75 * math.sin(t * 1.15) * (1 if t > 1.0 else t)
    if 3.0 < t < 3.4: yaw_head = -0.9
    e = dict(expr_mix('alert', 'fear', smooth(seg(t, 3.0, 8.0))), gx=clamp(yaw_head, -1, 1) * 0.6)
    br = breathe(t, 0.55)
    Ph = hero_walk_pose(0, 0, dict(amp=0.0, head=(yaw_head, 0.02, 0), hy=0.004 * br - 0.01, twist=0.25 * math.sin(t * 0.6) * smooth(seg(t, 0.8, 2.0)), lean=0.01 * br))
    put_hero(img, cam, wd, -0.15, zh, screen_yaw(cam, -1), Ph, e, li, sweat=0.0)
    # global dimming toward the end
    out = np.asarray(img).astype(np.float32)
    return fx().apply(out, t + 53, hor=cam.hor, fog=0.5, bright=lerp(1.0, 0.45, smooth(seg(t, 2.0, 8.0))))
