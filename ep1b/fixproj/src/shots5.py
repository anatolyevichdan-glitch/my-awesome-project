"""Shots part 5: shop-window reflection scene (D: 24.6 - 44.95)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from shots3 import *
from shots4 import Overlay
from char import G
from bg import lamp_post, facade

WIN = (150, 330, 930, 1440)
GY = 1600


def shop_backdrop(fr, T, lamp_state=1.0):
    g = fr.ga; ge = fr.ge
    W_, H_ = 1080, 1920
    g.poly([(0, 0), (W_, 0), (W_, H_), (0, H_)], (70, 66, 98))
    # upper floors
    facade(g, ge, -20, W_ + 20, 300, 20, 11, 0.28, (96, 90, 118), win_w=110, win_h=150, gap=90)
    # lower shop wall
    g.poly([(0, 300), (W_, 300), (W_, 1440), (0, 1440)], (84, 72, 88))
    g.poly([(0, 300), (W_, 300), (W_, 330), (0, 330)], (50, 38, 48))
    ge.poly([(260, 262), (820, 262), (820, 290), (260, 290)], (60, 16, 20))
    x0, y0, x1, y1 = WIN
    g.poly([(x0 - 26, y0 - 22), (x1 + 26, y0 - 22), (x1 + 26, y1 + 26), (x0 - 26, y1 + 26)], (36, 28, 34))
    g.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], (24, 26, 42))
    # interior: back wall + shelves (dim warm emissive)
    ge.poly([(x0 + 6, y0 + 6), (x1 - 6, y0 + 6), (x1 - 6, y1 - 6), (x0 + 6, y1 - 6)], (34, 26, 24))
    for j in range(4):
        yy = y0 + 150 + j * 240
        g.poly([(x0 + 14, yy), (x1 - 14, yy), (x1 - 14, yy + 16), (x0 + 14, yy + 16)], (80, 60, 48))
        ge.poly([(x0 + 14, yy - 8), (x1 - 14, yy - 8), (x1 - 14, yy), (x0 + 14, yy)], (70, 52, 30))
        for i in range(8):
            if hsh(i, j, 5) < 0.72:
                hh = 50 + hsh(i, j, 6) * 90
                cc = [(150, 80, 70), (90, 120, 100), (160, 140, 90), (80, 90, 140)][int(hsh(i, j, 7) * 4)]
                xx = x0 + 40 + i * 92
                g.poly([(xx, yy - hh), (xx + 62, yy - hh), (xx + 62, yy), (xx, yy)], cc)
                ge.poly([(xx, yy - hh), (xx + 62, yy - hh), (xx + 62, yy), (xx, yy)], tuple(int(v * 0.16) for v in cc))
    # glass: street reflection bands (opposite buildings), diagonal glare, rain runs
    for k in range(7):
        xx = x0 + 30 + k * 115 + 20 * math.sin(k * 2.1)
        hh = 160 + 110 * hsh(k, 2, 4)
        g.poly([(xx, y0 + 120 + hh * 0.3), (xx + 100, y0 + 120 + hh * 0.3), (xx + 100, y0 + 120 + hh * 0.3 + hh), (xx, y0 + 120 + hh * 0.3 + hh)], (90, 100, 160), a=26)
    g.poly([(x0 + 40, y0), (x0 + 190, y0), (x0 + 560, y1), (x0 + 410, y1)], (210, 225, 255), a=20)
    g.poly([(x0 + 260, y0), (x0 + 330, y0), (x0 + 700, y1), (x0 + 630, y1)], (210, 225, 255), a=14)
    for k in range(10):
        xx = x0 + 40 + hsh(k, 9, 1) * (x1 - x0 - 80)
        yy = y0 + 30 + hsh(k, 8, 2) * 500 + ((T * 40 * (0.5 + hsh(k, 7, 3))) % 520)
        yy = y0 + 30 + (yy - y0 - 30) % 1000
        g.line([(xx, yy), (xx - 3, yy + 90)], (190, 205, 240), 3, a=70)
        g.ell(xx - 3, yy + 92, 4, 6, (190, 205, 240), a=80, n=8)
    # centre mullion & frame
    g.poly([((x0 + x1) / 2 - 9, y0), ((x0 + x1) / 2 + 9, y0), ((x0 + x1) / 2 + 9, y1), ((x0 + x1) / 2 - 9, y1)], (40, 30, 36))
    g.poly([(x0 - 26, y1 + 26), (x1 + 26, y1 + 26), (x1 + 26, y1 + 70), (x0 - 26, y1 + 70)], (60, 52, 62))
    # pavement, curb, road
    g.poly([(0, 1466), (W_, 1466), (W_, 1730), (0, 1730)], (74, 76, 104))
    for i in range(7):
        g.line([(i * 190 - 40, 1466), (i * 190 - 120, 1730)], (62, 64, 90), 3)
    g.poly([(0, 1730), (W_, 1730), (W_, 1760), (0, 1760)], (110, 112, 140))
    g.poly([(0, 1760), (W_, 1760), (W_, H_), (0, H_)], (52, 56, 82))
    # wet sheen of the window light on the pavement
    ge.poly([(x0, 1466), (x1, 1466), (x1 + 80, 1730), (x0 - 80, 1730)], (26, 20, 14))
    lamps = []
    bp = lamp_post(g, ge, 1020, 1660, 940, lamp_state)
    lamps.append((bp[0], bp[1], lamp_state, 1660, 0))
    return lamps


def pose_at_D(T, seed=9):
    """protagonist pose at time T (used for the real protagonist and, until 29.41, mirrored exactly by the reflection)"""
    t = T
    e = C.blend('neutral', 'worried', 0.2 * sstep((T - 25.6) / 1.0))
    if T >= 26.9: e = C.blend(e, 'serious', 0.4 * sstep((T - 26.9) / 0.6))
    if T >= 29.41: e = C.blend('serious', 'relief', sstep((T - 29.41) / 0.4))
    if T >= 30.9: e = C.blend('relief', 'worried', sstep((T - 30.9) / 1.0))
    if T >= 34.5: e = C.blend('worried', 'scared', 0.5 * sstep((T - 34.5) / 1.5))
    if T >= 38.57: e = C.blend('scared', 'terror', 0.55 * sstep((T - 38.57) / 2.0))
    return e


def hero_D(T, e, reflect=False):
    t = T
    yaw = 2.5 + 0.03 * math.sin(t * 0.7)
    p = idle(t, e, seed=9, yaw=yaw)
    scan = 0.0
    if 26.9 <= T < 29.2: scan = 0.42 * math.sin((T - 26.9) * 2.0)
    p.head_yaw = -0.12 + scan
    p.head_pitch = -0.02
    if T >= 29.41:
        k = sstep((T - 29.41) / 0.55) * (1 - sstep((T - 30.8) / 1.0))
        p.shoulder_up = -0.9 * k; p.lean = 0.02 + 0.09 * k; p.head_pitch = -0.02 + 0.16 * k
        p.hip = (p.hip[0], p.hip[1] - 7 * k, 0)
        p.head_roll = 0.0 + 0.05 * k
    if T >= 30.9:
        # uneasy: weight shifts and fidgets (only the living protagonist)
        k = sstep((T - 30.9) / 0.8)
        p.head_yaw += 0.18 * math.sin((T - 30.9) * 1.1) * k
        p.hip = (p.hip[0] + 9 * math.sin((T - 30.9) * 1.7) * k, p.hip[1], 0)
    if T >= 32.74:
        k = sstep((T - 32.74) / 2.0)
        p.lean = p.lean + 0.07 * k
        p.hand[1] = (150, 560, 110) if False else None
    return p


def reflect_pose(T):
    """reflection = exact mirror until 29.41, then it freezes: no breath, no blink, no sway, locked stare"""
    Tf = min(T, 29.38)
    e = pose_at_D(Tf)
    p = hero_D(Tf, e, reflect=True)
    p.yaw = math.pi - p.yaw
    if T >= 29.41:
        p.breath = 0.0; p.shoulder_up = 0.0; p.sway = 0.0; p.blink = 0.0
        p.hip = (0.0, 0.0, 0.0)
        eyes = dict(C.EXPR['dead'])
        eyes['px'] = -0.9; eyes['py'] = 0.0
        eyes['eye'] = 1.0 + 0.1 * sstep((T - 35.0) / 1.0)
        # slow unnatural head turn toward the protagonist
        k = sstep((T - 35.75) / 2.0)
        p.head_yaw = -0.12 + (-0.45) * k
        smile = sstep((T - 39.6) / 1.8)
        eyes = C.blend(eyes, C.EXPR['shh'], smile * 0.7)
        eyes['px'] = -0.9; eyes['eye'] = 1.05 - 0.2 * smile
        p.e = eyes
        # finger to lips
        a = sstep((T - 38.57) / 2.2)
        if a > 0:
            J, _ = C.joints_of(p, 0, 0, 1.0)
            hd = C.solve(p, None)['head']
            tgt = (float(hd[0] + 4), float(hd[1] - 118), float(hd[2] + 70))
            rest = (C.SH_W + 20.0, C.HIP_Y + 300 - 30 - (C.UARM + C.FARM) * 0.93, 30.0)
            p.hand[1] = tuple(rest[i] + (tgt[i] - rest[i]) * a for i in range(3))
            p.hand_mode[1] = 'shh'
            p.elbow_pole[1] = (0.7, -1.0, 0.2)
            p.point_ang = -math.pi / 2
    return p


def mouth_pos(out):
    return out['head']


def reflection_fn(fr, T, s_r, x_r, y_r, p_r):
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = G(img, K)
    g.M = fr.ga.M.copy()
    C.draw_hero(g, x_r, y_r, s_r, p_r)
    g.flush()
    arr = np.asarray(img, np.float32)
    # glass rect mask through the camera matrix
    pts = [fr.ga.P(*q) for q in ((WIN[0], WIN[1]), (WIN[2], WIN[1]), (WIN[2], WIN[3]), (WIN[0], WIN[3]))]
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon([(x / 1.0, y / 1.0) for x, y in pts], fill=255)
    mask = np.asarray(m, np.float32)[..., None] / 255.0
    rows = np.arange(H)
    shift = (2.2 * np.sin(rows * 0.05 + T * 0.7) + 1.2 * np.sin(rows * 0.13 + T * 1.3)).astype(int)
    cols = np.clip(np.arange(W)[None, :] - shift[:, None], 0, W - 1)
    arr = arr[rows[:, None], cols]
    y0s = pts[0][1]; y1s = pts[3][1]
    fade = np.clip(1.0 - 0.55 * ((rows - y0s) / max(y1s - y0s, 1)), 0.2, 1.0)[:, None, None]
    tint = np.array([0.66, 0.78, 1.0], np.float32)
    ghost = np.roll(arr, (4, 6), axis=(0, 1))
    a = np.clip(arr[..., 3:4] / 255.0 * 0.9 * mask * fade + ghost[..., 3:4] / 255.0 * 0.2 * mask * fade, 0, 1)
    rgb = (arr[..., :3] * 0.8 + ghost[..., :3] * 0.2) * tint * 0.95

    def fn(im):
        return im * (1 - a) + rgb * a
    return fn


def vapor(fr, T, hx, hy, s):
    if not (29.41 <= T < 31.2): return
    k = (T - 29.41) / 1.6
    g = fr.ga
    for i in range(7):
        kk = max(0.0, k - i * 0.05)
        x = hx + 20 * s + kk * 190 * s * (0.8 + 0.1 * i) + 12 * math.sin(i * 1.7 + T * 2)
        y = hy + 40 * s - kk * 70 * s * (0.5 + 0.12 * i) - 4 * i
        r = (22 + 55 * kk) * s * (0.8 + 0.08 * i)
        al = int(120 * (1 - kk) * (1 - 0.06 * i))
        if al > 2: g.ell(x, y, r, r * 0.7, (225, 232, 250), a=al, n=14)


def shot_D(fr, T):
    t = T
    lamps = shop_backdrop(fr, T)
    # camera: slow push toward the reflection, jolt on the recoil
    z = 1.0 + 0.28 * sstep((T - 30.0) / 11.0)
    if T >= 43.3: z = 1.28 - 0.2 * sstep((T - 43.3) / 0.5)
    cx_ = 470; cy_ = 960
    zx = cx_ - z * 0 
    shake = 1.4 + (6.0 * math.exp(-(T - 43.3) * 5) if T >= 43.3 else 0)
    fr.cam(-(z - 1) * (cx_ - 540) + shake * math.sin(t * 41) * (1 if T >= 43.3 else 0.2) + 1.5 * math.sin(2.1 * t), -(z - 1) * (cy_ - 960) + shake * math.sin(t * 33) * 0.6 + 1.5 * math.sin(2.7 * t), z)
    add_lamps(fr, lamps)
    e = pose_at_D(T)
    s_h = 1.04
    hx_, hy_ = 270, GY + 40
    p = hero_D(T, e)
    if T >= 43.31:
        k = sstep((T - 43.31) / 0.34)
        k2 = sstep((T - 43.31) / 1.2)
        ee = C.blend(e, 'terror', k)
        p.e = ee
        p.yaw = AN.lerp1(p.yaw, 0.55, sstep((T - 43.31) / 0.45))
        back = 0.9 * k2
        ph = -1.1 * (T - 43.31)
        w = gait(ph, A=60, D=0.6, L=40, rho=0.9, lean=-0.2, Tc=0.1)
        for sd in (-1, 1):
            p.foot[sd] = w.foot[sd]; p.foot_pitch[sd] = w.foot_pitch[sd]
        p.hip = w.hip
        p.lean = -0.2 * k
        p.head_pitch = -0.2 * k
        p.hand[1] = (170, 640, 130); p.hand[-1] = (-170, 620, 130); p.hand_mode[1] = 'open'; p.hand_mode[-1] = 'open'
        p.elbow_pole[1] = (0.9, -0.2, -0.4); p.elbow_pole[-1] = (-0.9, -0.2, -0.4)
        p.blink = 0.0
        hx_ = 250 - 60 * sstep((T - 43.31) / 1.4)
        hy_ = GY + 40 + 70 * sstep((T - 43.31) / 1.4)
        s_h = 1.04 + 0.12 * sstep((T - 43.31) / 1.4)
        p.shoulder_up = 0.9 * k
    # contact shadow
    fr.ga.ell(hx_, hy_ + 8, 130 * s_h, 24 * s_h, (10, 10, 20), a=110, n=24)
    out = hero2(fr, hx_, hy_, s_h, p, occ=False)
    vapor(fr, T, out['head'][0] + 25, out['head'][1] + 16, s_h)
    # reflection (glass layer)
    pr = reflect_pose(T)
    s_r = 0.95
    fr.post.append(reflection_fn(fr, T, s_r, 585, 1336, pr))
    # blue-white sheen over the glass on top of everything inside
    add_extra(fr, 540, 900, 600, 760, (110, 140, 220), 0.25)
    return finish_kw(fog=0.12, fog_y=0.75, t=t, amb=tuple(c * 0.9 for c in AMB))
