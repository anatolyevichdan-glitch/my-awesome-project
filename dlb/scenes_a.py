"""Scenes 0-2: opening, the follower, the warning."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import rig
from rig import clamp, lerp, smooth, expr, expr_mix
from comp import *
from world import Cam, W, H

_font_cache = {}
def font(sz):
    if sz not in _font_cache: _font_cache[sz] = ImageFont.load_default(size=sz)
    return _font_cache[sz]


def stride(v, run_k=0.0):
    run = clamp(run_k)
    return 4 * (0.30 + 0.32 * run)


def hero_walk_pose(dist, run=0.0, extra=None):
    S = (0.30 + 0.32 * run)
    P = dict(p=dist / (4 * S), amp=1.0, run=run)
    if extra: P.update(extra)
    return P


def breathe(t, rate=0.3, a=1.0): return a * math.sin(2 * math.pi * rate * t)


# ============================================================ SCENE 0  (0-6s): opening
def scene0(t):
    wd = world('street'); li = [1.0] * len(wd.lamps)
    cz = -1.2 * t
    dx, dy = drift(t, 0.6)
    cam = Cam(x=0.0, y=1.28, z=cz, dir=1, f=2000, hor=H * 0.45 + dy, xoff=dx)
    arr, _ = wd.render(cam, li, amb=0.85, t=t)
    img = to_img(arr)
    zh = 5.2 - 1.4 * t
    dist_h = 1.4 * t
    # entity: slow follow with two unnatural lurches
    ent_d = 1.0 * t + 1.4 * smooth(seg(t, 3.55, 3.85)) + 1.2 * smooth(seg(t, 5.15, 5.4))
    ze = 11.0 - ent_d
    # entity first (farther)
    P = dict(p=ent_d / (4 * 0.38), amp=0.55, lean=0.0, t=t, head=(0, 0.04, 0.10 * math.sin(t * 0.7) + 0.25 * smooth(seg(t, 3.55, 3.9))), swing=0.06)
    em = smooth(seg(t, 0.2, 2.8))
    put_entity(img, cam, wd, 0.42, ze, -1, P, li, alpha=em, fog=lerp(0.85, 0.28, em), reflect=0.35)
    gz = 0.0
    e = expr_mix('unaware', 'unaware', 0)
    if 2.0 < t < 2.2: e = rig.expr('blink')
    P = hero_walk_pose(dist_h, 0.0, dict(head=(0.05 * math.sin(t * 0.8), 0.04 + 0.03 * math.sin(t * 1.3), 0.0), lean=0.02))
    put_hero(img, cam, wd, -0.28, zh, screen_yaw(cam, -1), P, e, li, ldir=-1, reflect=0.4)
    return finish(img, t, hor=cam.hor, fog=0.55)


# ============================================================ SCENE 1  (11 s): the follower
def v_prof(tb):
    """speed profile for rear-follow shot (local seconds)"""
    if tb < 1.0: return 1.4
    if tb < 3.0: return lerp(1.4, 3.1, smooth((tb - 1.0) / 2.0))
    if tb < 4.1: return 3.1
    return 3.1 * (1 - smooth(seg(tb, 4.1, 4.4)))


def scene1(t):
    wd = world('street'); li = [1.0] * len(wd.lamps)
    if t < 3.5:
        # A: front medium, camera backs away in front of him
        dist = 1.4 * t + 1.7
        zh = -3.2 - 1.4 * t
        cam = Cam(x=0.0, y=1.25, z=zh - 3.3 + 0.25 * t, dir=1, f=2000, hor=H * 0.45 + drift(t)[1], xoff=drift(t)[0])
        arr, _ = wd.render(cam, li, amb=0.85, t=t + 6)
        img = to_img(arr)
        ze = zh + 4.7 - 0.0
        P = dict(p=(1.4 * t) / (4 * 0.38) * 0.0 + (1.4 * t + 3) / (4 * 0.38), amp=0.55, t=t, head=(0, 0.05, 0.12), swing=0.06)
        put_entity(img, cam, wd, 0.38, ze, -1, P, li, fog=0.3, reflect=0.35)
        e = rig.expr('unaware') if t < 2.4 else expr_mix('unaware', 'tense', smooth(seg(t, 2.4, 3.4)))
        P = hero_walk_pose(dist, 0.0, dict(head=(0.05 * math.sin(t * 0.9), 0.03, 0), lean=0.03))
        put_hero(img, cam, wd, -0.2, zh, screen_yaw(cam, -1), P, e, li)
        return finish(img, t + 6, hor=cam.hor)
    if t < 8.0:
        tb = t - 3.5
        d = integ(v_prof, tb)
        zh = -14.0 - d
        gap = 4.4
        ze = zh + gap
        v = v_prof(tb)
        run = clamp((v - 1.4) / 2.2) * 0.6
        S = 0.30 + 0.32 * run
        ph = integ(lambda x: v_prof(x) / (4 * (0.30 + 0.32 * clamp((v_prof(x) - 1.4) / 2.2) * 0.6)), tb)
        cam_z = ze + 3.4
        dx, dy = drift(t, 0.8)
        cam = Cam(x=0.55, y=1.5, z=cam_z, dir=-1, f=1500, hor=H * 0.44 + dy, xoff=dx)
        arr, _ = wd.render(cam, li, amb=0.85, t=t + 6)
        img = to_img(arr)
        P = hero_walk_pose(0, run, dict(head=(0, 0.02, 0)))
        P['p'] = ph + 0.3
        put_hero(img, cam, wd, -0.1, zh, screen_yaw(cam, -1), P, rig.expr('tense'), li, reflect=0.4)
        PE = dict(p=ph * (0.30 + 0.32 * run) / 0.38 * 0.6 + 0.1, amp=0.8, t=t, head=(0, 0.05, 0.05), swing=0.05)
        put_entity(img, cam, wd, 0.0, ze, -1, PE, li, fog=0.0, reflect=0.35)
        return finish(img, t + 6, hor=cam.hor)
    # C: front, he stops, entity stops behind
    tc = t - 8.0
    zh = -30.0
    push = ease(3.5, 2.5, tc / 3.0)
    cam = Cam(x=0.0, y=1.3, z=zh - push, dir=1, f=2000, hor=H * 0.45 + drift(t)[1] * 0.5, xoff=drift(t)[0] * 0.5)
    arr, _ = wd.render(cam, li, amb=0.85, t=t + 6)
    img = to_img(arr)
    ze = zh + 4.4
    PE = dict(p=0.0, amp=0.0, t=t, head=(0, 0.08 * smooth(seg(tc, 0.5, 2.5)), 0.05 + 0.32 * smooth(seg(tc, 0.7, 2.6))), swing=0.05, stretch=0.0)
    put_entity(img, cam, wd, 0.38, ze, -1, PE, li, fog=0.22, reflect=0.35)
    br = breathe(tc, 0.7, 1.0)
    e = expr_mix('tense', 'alert', smooth(seg(tc, 0.0, 2.0)))
    if 1.3 < tc < 1.45: e = dict(e, gx=-0.7)
    elif 1.9 < tc < 2.05: e = dict(e, gx=0.7, gy=0.2)
    P = hero_walk_pose(0, 0, dict(amp=0.0, hy=0.006 * br - 0.01, lean=0.01 * br, head=(0.08 * math.sin(tc * 2.0) * 0.4, 0.05, 0.0),
                                  twist=0.02 * br))
    P['amp'] = 0.0
    put_hero(img, cam, wd, -0.2, zh, screen_yaw(cam, -1), P, e, li, sweat=0.0)
    return finish(img, t + 6, hor=cam.hor)


# ============================================================ phone
def draw_phone(img, cx, cy, sc, tilt, msgs, t, glow=1.0, vib=0.0):
    """Render a phone showing a chat; msgs = [(text, t_appear)]. Returns None. Composited onto img."""
    pw, ph = int(700 * sc), int(1380 * sc)
    lay = Image.new('RGBA', (pw + 200, ph + 200), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    ox, oy = 100, 100
    d.rounded_rectangle([ox, oy, ox + pw, oy + ph], radius=int(70 * sc), fill=(8, 9, 12), outline=(52, 56, 66), width=max(2, int(5 * sc)))
    m = int(18 * sc)
    sx0, sy0, sx1, sy1 = ox + m, oy + m, ox + pw - m, oy + ph - m
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=int(56 * sc), fill=(10, 13, 20))
    d.rounded_rectangle([ox + pw // 2 - int(80 * sc), sy0 + int(14 * sc), ox + pw // 2 + int(80 * sc), sy0 + int(52 * sc)], radius=int(20 * sc), fill=(2, 2, 4))
    fs = lambda n: font(max(8, int(n * sc)))
    d.text((sx0 + int(40 * sc), sy0 + int(30 * sc)), "3:07", font=fs(30), fill=(210, 215, 225))
    d.rectangle([sx0, sy0 + int(100 * sc), sx1, sy0 + int(210 * sc)], fill=(18, 22, 32))
    d.ellipse([sx0 + int(36 * sc), sy0 + int(120 * sc), sx0 + int(106 * sc), sy0 + int(190 * sc)], fill=(50, 56, 70))
    d.text((sx0 + int(130 * sc), sy0 + int(128 * sc)), "Unknown number", font=fs(38), fill=(225, 230, 240))
    d.text((sx0 + int(130 * sc), sy0 + int(170 * sc)), "now", font=fs(24), fill=(110, 120, 140))
    y = sy0 + int(290 * sc)
    for (text, ta) in msgs:
        a = smooth(seg(t, ta, ta + 0.35))
        if t < ta - 0.9: continue
        if t < ta:  # typing dots
            d.rounded_rectangle([sx0 + int(36 * sc), y, sx0 + int(200 * sc), y + int(80 * sc)], radius=int(36 * sc), fill=(34, 40, 54))
            for i in range(3):
                bl = 0.5 + 0.5 * math.sin(t * 9 - i * 1.2)
                c = int(90 + 120 * bl)
                cxx = sx0 + int((78 + i * 40) * sc)
                d.ellipse([cxx - int(9 * sc), y + int(31 * sc), cxx + int(9 * sc), y + int(49 * sc)], fill=(c, c, c + 10))
            y += int(110 * sc)
            continue
        f = fs(54); maxw = (sx1 - sx0) - int(260 * sc)
        lines, cur = [], ''
        for w_ in text.split():
            trial = (cur + ' ' + w_).strip()
            if d.textlength(trial, font=f) <= maxw: cur = trial
            else: lines.append(cur); cur = w_
        lines.append(cur)
        lh = int(66 * sc); tw = int(max(d.textlength(l_, font=f) for l_ in lines)); th = lh * len(lines)
        pad = int(30 * sc)
        yy = y + int((1 - a) * 30 * sc)
        col = (46 + int(10 * (1 - a)), 52, 68)
        d.rounded_rectangle([sx0 + int(36 * sc), yy, sx0 + int(36 * sc) + tw + 2 * pad, yy + th + int(1.6 * pad)], radius=int(40 * sc), fill=col)
        for li_, l_ in enumerate(lines):
            d.text((sx0 + int(36 * sc) + pad, yy + int(0.8 * pad) + li_ * lh), l_, font=f, fill=(int(245 * a), int(245 * a), int(250 * a)))
        y += th + int(1.6 * pad) + int(40 * sc)
    # screen sheen
    d.polygon([(sx0, sy0), (sx0 + int(300 * sc), sy0), (sx0, sy0 + int(500 * sc))], fill=(255, 255, 255, 3))
    lay = lay.rotate(tilt, resample=Image.BICUBIC, expand=True)
    # glow on surroundings
    glowl = Image.new('RGB', img.size, (0, 0, 0))
    gd = ImageDraw.Draw(glowl)
    gd.ellipse([cx - pw * 0.9, cy - ph * 0.6, cx + pw * 0.9, cy + ph * 0.6], fill=(int(40 * glow), int(55 * glow), int(80 * glow)))
    glowl = glowl.filter(ImageFilter.GaussianBlur(120 * sc))
    ga = np.asarray(img).astype(np.float32) + np.asarray(glowl).astype(np.float32) * 0.9
    img.paste(to_img(ga))
    img.paste(lay, (int(cx - lay.width / 2 + vib), int(cy - lay.height / 2)), lay)
    return (cx, cy, pw, ph)


def draw_hand_on_phone(img, cx, cy, sc, tilt, glow=1.0, vib=0.0):
    pw, ph = 700 * sc, 1380 * sc
    skin = (int(120 * glow), int(128 * glow), int(145 * glow))
    dark = (28, 30, 38)
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # fingers wrap around the right edge, thumb bottom-left
    for i in range(4):
        y = cy - ph * 0.22 + i * ph * 0.105
        rig.capsule(d, (cx + pw * 0.56, y), (cx + pw * 0.36, y + 6), 88 * sc, skin)
        rig.capsule(d, (cx + pw * 0.56, y - 20 * sc), (cx + pw * 0.40, y - 14 * sc), 30 * sc, mix(skin, dark, 0.35))
    rig.capsule(d, (cx - pw * 0.62, cy + ph * 0.42), (cx - pw * 0.30, cy + ph * 0.38), 110 * sc, skin)
    d.ellipse([cx - pw * 0.40, cy + ph * 0.36, cx - pw * 0.24, cy + ph * 0.41], fill=mix(skin, dark, 0.2))
    d.rectangle([cx - pw * 0.8, cy + ph * 0.46, cx + pw * 0.8, cy + ph * 0.7], fill=(0, 0, 0, 0))
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    img.paste(lay, (int(vib), 0), lay)


def mix(c1, c2, t): return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


_bg_cache = {}
def blur_bg(key, wd, cam, li, amb, rad=36, dark=0.9):
    if key not in _bg_cache:
        arr, _ = wd.render(cam, li, amb=amb, t=0)
        im = to_img(arr).resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(rad / 4)).resize((W, H), Image.BICUBIC)
        _bg_cache[key] = np.asarray(im).astype(np.float32) * dark
    return _bg_cache[key].copy()


# ============================================================ SCENE 2 (9 s): the warning
def scene2(t):
    wd = world('street'); li = [1.0] * len(wd.lamps)
    if t < 3.4:
        zh = -30.0
        push = ease(3.0, 2.6, t / 3.4)
        cam = Cam(x=0.0, y=1.3, z=zh - push, dir=1, f=2000, hor=H * 0.45 + drift(t)[1] * 0.4, xoff=drift(t)[0] * 0.4)
        arr, _ = wd.render(cam, li, amb=0.85, t=t + 17)
        img = to_img(arr)
        PE = dict(p=0.0, amp=0.0, t=t, head=(0, 0.1, 0.35 + 0.05 * math.sin(t)), swing=0.05)
        put_entity(img, cam, wd, 0.40, zh + 3.9, -1, PE, li, fog=0.2, reflect=0.35)
        vib = 0.0
        if 0.5 < t < 1.6: vib = math.sin(t * 90) * 0.007 * (1 - seg(t, 1.2, 1.6))
        up = smooth(seg(t, 1.5, 2.6))
        pocket = (-0.2, 0.9, 0.06)
        raised = (-0.08, 1.28, 0.32)
        wr = tuple(lerp(pocket[i], raised[i], up) for i in range(3))
        look = smooth(seg(t, 2.2, 3.0))
        e = expr_mix('unaware', 'tense', look * 0.6)
        e = dict(e, gy=-0.55 * look, gx=0)
        P = hero_walk_pose(0, 0, dict(amp=0.0, armR=(wr, (-0.5, -0.6, -0.5)), armL=((0.2, 0.9, 0.05), (0.5, -0.5, -0.5)),
                                      head=(0, 0.28 * look, 0), hy=-0.01 + vib, lean=0.04 * look))
        scr = look
        lit_o = None
        put_hero(img, cam, wd, -0.2, zh, screen_yaw(cam, -1), P, e, li, lit_override=lerp(0.5, 0.95, up))
        # phone seen from behind in his hand + screen glow on his face
        if up > 0.05:
            p0 = cam.proj(-0.2, 0, zh)
            sx, sy, dz, k = p0
            hx = sx + (-wr[0]) * k * -1 * 0 + (wr[0] * -1) * 0
            hx = sx + wr[0] * k * -1 * -1 * 0 + (-wr[0]) * k * -1
            hx = sx - (wr[0] - 0.0) * k * 1 + 0
            hx = sx + (wr[0]) * k * -1  # character's right is screen-left when facing camera
            hy = sy - wr[1] * k
            d = ImageDraw.Draw(img, 'RGBA')
            pw_, ph_ = 0.075 * k, 0.15 * k
            d.rounded_rectangle([hx - pw_ / 2, hy - ph_ * 0.9, hx + pw_ / 2, hy + ph_ * 0.1], radius=int(pw_ * 0.15), fill=(10, 11, 14))
            d.rounded_rectangle([hx - pw_ / 2 + 2, hy - ph_ * 0.9 + 2, hx + pw_ / 2 - 2, hy + ph_ * 0.1 - 2], radius=int(pw_ * 0.15), outline=(70, 90, 120), width=1)
        out = finish(img, t + 17, hor=cam.hor)
        return out
    if t < 6.4:
        tc = t - 3.4
        cam0 = Cam(x=0.0, y=1.3, z=-33.0, dir=1, f=2000, hor=H * 0.45)
        arr = blur_bg('s2bg', wd, cam0, li, 0.5, 38, 0.8)
        img = to_img(arr)
        sc = ease(0.88, 0.98, tc / 3.0)
        vib = 0.0
        if tc < 0.6: vib = math.sin(tc * 110) * 10 * (1 - tc / 0.6)
        msgs = [("DON'T LOOK BACK.", 0.5)]
        cx, cy = W * 0.5, H * 0.52
        draw_phone(img, cx, cy, sc, -4, msgs, tc, glow=1.0, vib=vib)
        draw_hand_on_phone(img, cx + vib, cy, sc, -4, 1.0)
        return finish(img, t + 17, hor=H * 0.45, fog=0.25, rain=0.5, splash=False, blur=0.6)
    # C: push in on eyes
    tc = t - 6.4
    cam0 = Cam(x=0.0, y=1.3, z=-33.0, dir=1, f=2000, hor=H * 0.45)
    arr = blur_bg('s2bg2', wd, cam0, li, 0.4, 44, 0.55)
    img = to_img(arr)
    R = ease(560, 900, tc / 2.6)
    e = expr_mix('tense', 'fear', smooth(seg(tc, 0.4, 2.4)))
    gx = 0.0
    e = dict(e, gy=lerp(-0.5, 0.0, smooth(seg(tc, 0.0, 0.8))), gx=0.12 * math.sin(tc * 2.5) * (1 - smooth(seg(tc, 1.0, 1.4))))
    if 1.4 < tc < 1.55: e = dict(e, open=0.1)
    sp_ = rig.head_sprite(R, 0.0, 0.0 + 0.05 * (1 - smooth(seg(tc, 0, 1))), e, 'hero', 0.9, (0.78, 0.95, 1.2), ldir=-1, shade_on=True)
    cx, cy = W / 2, H * 0.47 + R * 0.02
    img.paste(sp_, (int(cx - sp_.width / 2), int(cy - sp_.height / 2)), sp_)
    # cold screen light from below
    arr = np.asarray(img).astype(np.float32)
    ys = np.linspace(0, 1, H)[:, None, None]
    arr = arr * (0.82 + 0.35 * ys)
    return finish(to_img(arr), t + 17, hor=H * 0.45, fog=0.18, rain=0.35, splash=False, blur=0.8)
