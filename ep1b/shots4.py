"""Shots part 4: phone sequences (C: 17.56-24.6, E: 44.94-53.7)."""
import math
import numpy as np
from PIL import Image
from shots3 import *
import phone as PH

SKINL = (226, 206, 214)


def bokeh(fr, T, seed=3):
    g = fr.ga; ge = fr.ge
    g.poly([(0, 0), (1080, 0), (1080, 1920), (0, 1920)], (36, 38, 66))
    g.poly([(0, 0), (1080, 0), (1080, 700), (0, 700)], (48, 48, 84))
    rng = np.random.default_rng(seed)
    for i in range(14):
        x = rng.random() * 1200 - 60; y = 200 + rng.random() * 1300; r = 40 + rng.random() * 90
        c = [(255, 205, 140), (150, 200, 255), (255, 160, 120)][i % 3]
        ge.ell(x, y + 8 * math.sin(T * 0.4 + i), r, r, c, a=int(38 + 30 * rng.random()), n=22)


def grip_overlay(ovg, cx, cy, pw, ph, ang, s_=1.0, thumb=(0.0, 0.0), skin=SKINL):
    c, sn = math.cos(ang), math.sin(ang)

    def L(x, y): return (cx + x * c - y * sn, cy + x * sn + y * c)
    ol = tuple(int(v * 0.55) for v in skin)
    # fingertips wrap the right edge
    for i, yy in enumerate((0.16, 0.25, 0.34, 0.43)):
        a = L(pw / 2 - 18, ph * yy); b = L(pw / 2 + 36, ph * yy + 4 - i)
        ovg.capsule(a, b, 52 * s_, skin, ol, 3)
    # thumb on the left, over the screen edge
    tx, ty = thumb
    a = L(-pw / 2 - 40, ph * 0.46); b = L(-pw / 2 + 120 + tx, ph * 0.36 + ty)
    ovg.capsule(a, b, 62 * s_, skin, ol, 3)
    ovg.ell(*b, 20 * s_, 18 * s_, shade_(skin, 1.05), n=14)


def shade_(c, k): return tuple(min(255, int(v * k)) for v in c)


class Overlay:
    """RGBA overlay drawn with the same design coords; composited in post after the phone."""

    def __init__(self):
        self.img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self.g = G(self.img, K)

    def fn(self):
        self.g.flush()
        arr = np.asarray(self.img, np.float32)

        def f(img):
            a = arr[..., 3:4] / 255.0
            return img * (1 - a) + arr[..., :3] * a
        return f


from char import G


def buzz_off(T, times, amp=9.0, dur=0.75):
    dx = dy = 0.0
    for tb in times:
        if tb <= T < tb + dur:
            a = amp * math.exp(-(T - tb) * 3.2)
            dx += a * math.sin(T * 97); dy += a * 0.7 * math.cos(T * 83)
    return dx, dy


def hand_target_screen(p, x0, y0, s, sx, sy, depth=70):
    return AN.hand_at(p.yaw, x0, y0, s, sx, sy, depth)


# ---------------------------------------------------------------- C: phone (17.56 - 24.6)
def shot_C(fr, T):
    t = T
    BUZZ = [17.56, 18.35]
    if T < 19.0:
        # medium shot: hero 3/4, phone lighting his face, buzzing in raised hand
        s = 1.22; x0, y0 = 560, 1520
        bokeh(fr, T)
        p = idle(t, C.blend('neutral', 'worried', 0.3 + 0.4 * sstep((T - 17.6) / 0.6)), seed=4, yaw=0.5)
        p.head_yaw = -0.25
        p.head_pitch = 0.18
        J, cam = C.joints_of(p, x0, y0, s)
        # right hand raised holding phone
        wr_t = hand_target_screen(p, x0, y0, s, x0 + 110, y0 - 640, 70)
        p.hand[1] = wr_t; p.hand_mode[1] = 'fist'
        p.hand[-1] = (-98, 520, 30)
        p.elbow_pole[1] = (0.8, -0.5, -0.3)
        hero2(fr, x0, y0, s, p, occ=True)
        J, cam = C.joints_of(p, x0, y0, s)
        w = J[('wrist', 1)]
        dx, dy = buzz_off(T, BUZZ, 7)
        pw, ph = 215, 440
        cx, cy = w[0] + dx, w[1] - ph * 0.38 + dy
        scr = PH.phone_screen(560, 1160, t, [], mode='lock', notif_t=17.62, flash=0.0)
        lay = PH.make_phone_layer(cx, cy, pw, ph, -0.1, scr, brightness=1.1)
        fr.post.append(PH.post_layer(lay))
        ov = Overlay(); grip_overlay(ov.g, cx, cy, pw, ph, -0.1, 0.5, skin=SKINL); fr.post.append(ov.fn())
        add_extra(fr, cx, cy - 120, 330, 380, (120, 170, 255), 0.55 + 0.25 * (1 if int(T * 20) % 2 and T < 18.5 else 0))
        cam_shake(fr, t, 1.8)
        return finish_kw(fog=0.16, fog_y=0.7, t=t, amb=tuple(c * 0.8 for c in AMB))
    if T < 22.7:
        # close-up of the phone, hero's frightened face above it
        s = 2.15; x0, y0 = 540, 2215
        bokeh(fr, T, 5)
        lookdown = 1.0
        ee = C.blend('worried', 'scared', sstep((T - 21.3) / 0.5))
        ee = eyes_alive(ee, t, 4, 0.4); ee['py'] = 0.9 * (1 - 0.3 * sstep((T - 21.3) / 0.4))
        p = idle(t, ee, seed=4, yaw=0.12)
        p.head_pitch = 0.12; p.head_yaw = 0.0
        p.blink = 0.0 if 21.2 < T < 22.0 else blink_at(t, 4)
        pw, ph = 640, 1180
        dx, dy = buzz_off(T, [], 0)
        cx, cy = 540 + dx, 1040 + dy
        ang = -0.05
        wr_t = hand_target_screen(p, x0, y0, s, cx + pw * 0.28, cy + ph * 0.28, 90)
        p.hand[1] = wr_t; p.hand_mode[1] = 'fist'
        p.hand[-1] = (-90, 300, 90); p.elbow_pole[1] = (0.8, -0.4, -0.5)
        hero2(fr, x0, y0, s, p, occ=True)
        mode = 'lock' if T < 19.55 else 'chat'
        flash = 0.8 * max(0.0, 1 - (T - 21.36) / 0.4) if T >= 21.36 else (0.6 * max(0.0, 1 - (T - 19.55) / 0.2) if T >= 19.55 else 0)
        msgs = [("Не оборачивайся".upper(), 'r', 21.36)]
        scr = PH.phone_screen(600, 1140, t, msgs, mode=mode, notif_t=19.0, typing=(20.5, 21.36), flash=flash)
        dx2, dy2 = buzz_off(T, [21.36], 6, 0.5)
        lay = PH.make_phone_layer(cx + dx2, cy + dy2, pw, ph, ang, scr, brightness=1.05)
        fr.post.append(PH.post_layer(lay))
        th = (0, 0)
        if 19.1 < T < 19.6: th = (60 * math.sin(math.pi * (T - 19.1) / 0.5), -380 + 0 * T)
        ov = Overlay(); grip_overlay(ov.g, cx + dx2, cy + dy2, pw, ph, ang, 1.5, thumb=(0, 0)); fr.post.append(ov.fn())
        add_extra(fr, 540, 330, 560, 420, (120, 170, 255), 0.9)
        cam_shake(fr, t, 1.2)
        return finish_kw(fog=0.08, fog_y=0.7, t=t, amb=tuple(c * 0.7 for c in AMB), vig=1.1)
    # face close-up: he snaps his eyes up
    s = 2.7; x0, y0 = 540, 2330
    bokeh(fr, T, 7)
    k = sstep((T - 22.95) / 0.22)
    ee = C.blend('worried', 'shock', k)
    ee = C.blend(ee, 'scared', 0.5 * sstep((T - 23.6) / 0.6))
    ee['px'] = -0.4 * sstep((T - 23.3) / 0.3) ; ee['py'] = -0.6 * k
    p = idle(t, ee, seed=6, yaw=0.1)
    p.head_pitch = 0.2 - 0.5 * k
    p.head_roll = 0.05 * math.sin(T * 1.2)
    p.blink = 0.0
    p.shoulder_up = 0.8 * k
    p.hand[1] = None
    hero2(fr, x0, y0, s, p, occ=True)
    # phone drops out of frame
    drop = sstep((T - 22.95) / 0.35)
    scr = PH.phone_screen(600, 1140, t, [("НЕ ОБОРАЧИВАЙСЯ", 'r', 0)], mode='chat')
    lay = PH.make_phone_layer(760 + 40 * drop, 1750 + 560 * drop, 560, 1030, -0.2 - 0.3 * drop, scr, brightness=1.0)
    fr.post.append(PH.post_layer(lay))
    add_extra(fr, 540, 460, 600, 460, (120, 170, 255), 0.8 * (1 - drop) + 0.2)
    cam_shake(fr, t, 3.0 * (1 - drop) + 1.0)
    return finish_kw(fog=0.08, fog_y=0.7, t=t, amb=tuple(c * 0.7 for c in AMB), vig=1.1)


# ---------------------------------------------------------------- E: second/third message (44.94 - 53.7)
def shot_E(fr, T):
    t = T
    s = 2.15; x0, y0 = 540, 2215
    bokeh(fr, T, 11)
    base = C.blend('worried', 'scared', 0.3 + 0.25 * sstep((T - 45.4) / 1.2))
    if T >= 47.67: base = C.blend(base, 'scared', 0.5 + 0.5 * sstep((T - 47.67) / 0.4))
    if T >= 49.07: base = C.blend('scared', 'shock', 0.4)     # freeze
    if T >= 51.83: base = C.blend('shock', 'terror', sstep((T - 51.9) / 0.4))
    ee = eyes_alive(base, t, 5, 0.3 if T < 49.07 or T > 50.2 else 0.0)
    ee['py'] = 0.9 if T < 51.9 else 0.4
    p = idle(t, ee, seed=5, yaw=0.12)
    frozen = 49.07 <= T < 50.14
    p.head_pitch = 0.12 + (0.08 if T > 51.9 else 0.0)
    p.blink = 0.0 if (T > 47.5) else blink_at(t, 5)
    if frozen: p.breath = 0.0; p.shoulder_up = 0.0; p.hip = (0, 0, 0)
    if T > 51.9:
        p.head_roll = 0.03 * math.sin(T * 30); p.hip = (2.5 * math.sin(T * 41), 0, 0)
    pw, ph = 640, 1180
    BUZ = [44.94, 50.14, 51.5]
    dx, dy = buzz_off(T, BUZ, 10, 0.9)
    cx, cy = 540 + dx, 1040 + dy
    wr_t = hand_target_screen(p, x0, y0, s, cx + pw * 0.28, cy + ph * 0.28, 90)
    p.hand[1] = wr_t; p.hand_mode[1] = 'fist'
    p.hand[-1] = (-90, 300, 90); p.elbow_pole[1] = (0.8, -0.4, -0.5)
    hero2(fr, x0, y0, s, p, occ=True)
    msgs = [("НЕ ОБОРАЧИВАЙСЯ", 'r', -1), ("ОН НЕ ЗА ТОБОЙ", 'r', 47.67), ("ОН ВНУТРИ ТЕБЯ", 'r', 51.83)]
    typing = None
    if 44.94 <= T < 47.67: typing = (44.94, 47.67)
    if 50.14 <= T < 51.83: typing = (50.14, 51.83)
    flash = 0.0
    for tm in (47.67, 51.83):
        if tm <= T < tm + 0.4: flash = max(flash, 0.9 * (1 - (T - tm) / 0.4))
    scr = PH.phone_screen(600, 1140, t, msgs, mode='chat', typing=typing, flash=flash)
    lay = PH.make_phone_layer(cx, cy, pw, ph, -0.05, scr, brightness=1.05)
    fr.post.append(PH.post_layer(lay))
    ov = Overlay(); grip_overlay(ov.g, cx, cy, pw, ph, -0.05, 1.5); fr.post.append(ov.fn())
    add_extra(fr, 540, 330, 560, 420, (120, 170, 255), 0.9)
    cam_shake(fr, t, 1.0 + (3.0 if T > 51.9 else 0), 1.0)
    amb = AMB
    if T > 51.74:
        amb = tuple(c * (0.55 + 0.45 * (1 if int(T * 14) % 2 else 0.3)) for c in AMB)
    amb = tuple(c * 0.7 for c in amb)
    return finish_kw(fog=0.08, fog_y=0.7, t=t, amb=amb, vig=1.1, fx_red=0.12 * sstep((T - 52) / 1.0))
