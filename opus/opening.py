"""GATE TEST 1 — opening, episode 0.0–8.0 s.
0.0–4.7  wide side-tracking walk down a wet night street (camera leads, empty space behind him)
4.7–6.25 3/4 medium walk, background soft; he does not see anything
6.25–8.0 CCTV high angle: the camera "sees"; a tall shape stands in the dark behind him at the end
"""
import math
import random
import sys
sys.path.insert(0, '/tmp/hoplite/workspace/opus')
sys.path.insert(0, '/tmp/hoplite/workspace/rem')
import skia  # noqa: E402
import rig as R  # noqa: E402
import toon  # noqa: E402
import motion as M  # noqa: E402
import world as Wd  # noqa: E402
import creature2 as C  # noqa: E402
from gfx import P, lin, rad, path_poly, mix  # noqa: E402
from t_sheet import EX  # noqa: E402
import harness  # noqa: E402

W, H = Wd.W, Wd.H
CAD = 0.92            # walk cycles per second (≈1.84 steps/s, unhurried)
NIGHT = (0.80, 0.85, 1.0)


def street_layers(cv, cx, gy, t, flick_lamp=None, flick=1.0):
    """long street in world-x; cx = world x at the left screen edge (parallax 1)."""
    Wd.sky(cv, (8, 10, 26), (34, 40, 70), gy)
    Wd.moon(cv, 820, 250, 40)
    # far blocks (parallax .2)
    for i in range(-2, 8):
        wx = i * 300 - cx * 0.2
        hgt = 520 + (i * 137) % 260
        Wd.panel_building(cv, wx, 280, gy - 260 - hgt, gy - 200, (30, 34, 58), seed=100 + i, lit=0.10, floor_h=60, t=t,
                          balconies=False)
    cv.drawRect(skia.Rect(0, gy - 420, W, gy - 150), P(shader=lin((0, gy - 420), (0, gy - 150), (40, 46, 78), (40, 46, 78), 0.0, 0.55)))
    # mid blocks (parallax .55)
    for i in range(-2, 9):
        wx = i * 520 - cx * 0.55
        hgt = 760 + (i * 211) % 200
        Wd.panel_building(cv, wx, 470, gy - hgt, gy - 60, (44, 48, 74), seed=200 + i, lit=0.17, floor_h=82, t=t)
    cv.drawRect(skia.Rect(0, gy - 260, W, gy - 40), P(shader=lin((0, gy - 260), (0, gy - 40), (60, 66, 100), (60, 66, 100), 0.0, 0.35)))
    # low fence along the yard, parallax 1
    off = (-cx) % 60
    for i in range(-1, 20):
        x = i * 60 + off
        cv.drawRect(skia.Rect(x, gy - 150, x + 6, gy - 46), P((22, 24, 36)))
    cv.drawRect(skia.Rect(0, gy - 140, W, gy - 132), P((22, 24, 36)))
    cv.drawRect(skia.Rect(0, gy - 90, W, gy - 84), P((22, 24, 36)))
    # trees + lamps, parallax 1
    heads = []
    for i in range(-1, 8):
        wx = i * 640 + 260
        x = wx - cx
        if -300 < x < W + 300:
            Wd.tree(cv, x + 300, gy - 44, 520, seed=i + 9)
    Wd.street_ground(cv, gy, cx)
    for i in range(-1, 8):
        wx = i * 640 + 40
        x = wx - cx
        if -500 < x < W + 500:
            on = flick if i == flick_lamp else 1.0
            hx, hy = Wd.lamp(cv, x, gy + 130, 820, on=on, side=1, glow_r=330)
            heads.append((hx, hy, on))
            Wd.wet_reflection(cv, hx, gy + 150, Wd.SODIUM, w=34, ln=320, a=0.28 * on)
    return heads


def light_at(x, heads):
    k = 0.0
    for hx, hy, on in heads:
        k = max(k, on * max(0.0, 1 - abs(x - hx) / 420.0))
    return k


def look_for(k, side=-1):
    tint = tuple(NIGHT[i] * (1 - k) + (1.05, 0.96, 0.84)[i] * k for i in range(3))
    lk = toon.Look(key=(0.5 * side, -0.7), rim=mix((52, 54, 72), (255, 200, 130), k) if k > 0.05 else None, rim_w=5, tint=tint)
    lk.rim_dir = (0.4 * side, -0.9)
    return lk


def boy_walk(t, mood):
    p = R.Pose()
    p.yaw = math.pi / 2
    M.walk(p, t * CAD, mood=mood)
    return p


# ------------------------------------------------------------------ shot 1
S1 = 0.50
V1 = 660 * S1 * CAD


def shot1(cv, t):
    gy = 1430
    bx = 300 + V1 * t                       # world x of the boy root
    lead = M.keys(t, [(0, 560), (4.7, 640)])
    cx = bx - lead
    zoom = M.keys(t, [(0, 1.0), (4.7, 1.07)], fn=M.smooth)
    cv.translate(W / 2, H * 0.62); cv.scale(zoom, zoom); cv.translate(-W / 2, -H * 0.62)
    heads = street_layers(cv, cx, gy, t, flick_lamp=0, flick=1.0 - 0.85 * (3.05 < t < 3.18 or 3.32 < t < 3.62))
    mood = M.keys(t, [(0, 0.0), (2.3, 0.0), (3.6, 0.55), (4.7, 0.6)])
    p = boy_walk(t, mood)
    p.e = M.kexpr(t, [(0, 'neutral'), (2.2, 'neutral'), (2.9, EX['mild_fear'] | dict(gx=-0.9, sweat=0.0)),
                       (3.9, EX['mild_fear'] | dict(gx=-0.7, sweat=0.0)), (4.4, 'worried')], EX)
    p.blink = M.blink_at(t, [1.25, 4.05])
    p.head_yaw += M.keys(t, [(0, 0), (2.5, 0), (3.1, -0.22), (4.0, -0.18), (4.5, 0.0)])   # half-glance, never turns
    sx = bx - cx
    k = light_at(sx, heads)
    toon.draw(cv, p, sx, gy + 70, S1, cam_pitch=0.06, look=look_for(k))
    # foreground railing posts sweep past (parallax 1.35)
    for i in range(-1, 6):
        x = i * 900 + 500 - cx * 1.35
        if -80 < x < W + 80:
            cv.drawRect(skia.Rect(x, gy + 120, x + 46, H), P((10, 11, 18)))
    Wd.rainfall(cv, t, seed=1, n=150, cx=cx, par=1.0)
    return dict(vign=0.6)


# ------------------------------------------------------------------ shot 2
S2 = 1.30


def shot2(cv, t):
    u = t - 4.7
    gy = 1500
    cxw = 300 + V1 * t
    # soft background: the same street, pushed out of focus
    cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(9, 9)))
    cv.translate(W / 2, H * 0.55); cv.scale(1.25, 1.25); cv.translate(-W / 2, -H * 0.55)
    heads = street_layers(cv, cxw * 0.7, gy, t)
    cv.restore()
    p = R.Pose()
    p.yaw = 0.75
    M.walk(p, t * CAD, amp=0.85, mood=0.55)
    p.e = M.kexpr(t, [(4.7, 'worried'), (5.4, EX['worried'] | dict(gx=0.15)), (6.25, EX['worried'] | dict(gx=0.1, brow=0.38))], EX)
    p.blink = M.blink_at(t, [5.55])
    k = 0.35 + 0.45 * max(0.0, math.sin(u * 2.2))     # passing lamp light slides over him
    a = toon.draw(cv, p, 560 + 20 * u, 2380, S2, cam_pitch=0.02, look=look_for(k, side=1), ground_shadow=0)
    mx, my = a['mouth']
    for b in (4.95, 5.95):
        Wd.breath_puff(cv, mx, my, (t - b) / 0.9, s=1.0, side=1)
    Wd.rainfall(cv, t, seed=4, n=90, ln=70, alpha=0.38)
    return dict(vign=0.7)


# ------------------------------------------------------------------ shot 3 (CCTV)
def shot3(cv, t):
    u = t - 6.25
    # elevated, wide-lens view down the pavement: ground plane fills the frame
    cv.drawRect(skia.Rect(0, 0, W, H), P((40, 44, 56)))
    cv.drawRect(skia.Rect(0, 0, W, 520), P(shader=lin((0, 0), (0, 520), (24, 26, 34), (52, 56, 70))))
    for i in range(6):                                   # building wall windows (dark)
        cv.drawRect(skia.Rect(60 + i * 180, 120, 160 + i * 180, 330), P((30, 32, 42)))
    cv.drawRect(skia.Rect(0, 520, W, 1180), P(shader=lin((0, 520), (0, 1180), (64, 68, 82), (78, 82, 96))))
    for i in range(12):                                   # paving joints in perspective
        x = -400 + i * 170
        cv.drawLine(x, 520, x * 1.6 - 200, 1180, P((56, 60, 74), style='stroke', width=3))
    cv.drawRect(skia.Rect(0, 1180, W, 1230), P((96, 100, 116)))
    cv.drawRect(skia.Rect(0, 1230, W, H), P((34, 36, 46)))
    # two lamps: pools on the ground
    for lx in (220, 900):
        cv.drawOval(skia.Rect(lx - 330, 760, lx + 330, 1120), P(shader=rad((lx, 940), 330, (220, 220, 200), (220, 220, 200), 0.32, 0.0)))
        cv.drawRect(skia.Rect(lx - 9, 300, lx + 9, 950), P((22, 24, 30)))
    # the boy, small, crossing the frame
    p = R.Pose(); p.yaw = math.pi / 2
    M.walk(p, t * CAD, mood=0.6)
    p.e = EX['worried']
    s3 = 0.40
    bx = 250 + 660 * s3 * CAD * u
    toon.draw(cv, p, bx, 1010, s3, cam_pitch=0.42, look=toon.Look(key=(0.2, -1)))
    # the shape: far behind him at the dark edge of the lamp pool, only at the end
    if u > 1.05:
        a = M.smooth((u - 1.05) / 0.5)
        cp = C.CPose(); cp.facing = 1
        cv.saveLayer(None, None)
        C.draw(cv, cp, -30, 900, 760, t=t, alpha=0.92 * a, rim=(80, 84, 96), smoke=0.6)
        cv.restore()
    # CCTV overlay
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 0.0))
    for y in range(0, H, 6):
        cv.drawRect(skia.Rect(0, y, W, y + 2), P((0, 0, 0), 0.10))
    font = skia.Font(skia.Typeface('DejaVu Sans Mono'), 40)
    if int(t * 2) % 2 == 0:
        cv.drawCircle(84, 106, 15, P((230, 50, 50)))
    cv.drawString('REC', 112, 120, font, P((236, 236, 236)))
    cv.drawString('CAM 03', 860, 120, font, P((236, 236, 236)))
    secs = 13 + int(u)
    cv.drawString(f'02:47:{secs:02d}', 72, 1830, font, P((236, 236, 236)))
    cv.drawString('ул. Лесная, 14', 690, 1830, font, P((236, 236, 236)))
    # brief tracking glitch as the shape resolves
    if 7.62 < t < 7.74:
        rnd = random.Random(int(t * 30))
        for _ in range(7):
            y = rnd.uniform(0, H)
            cv.drawRect(skia.Rect(0, y, W, y + rnd.uniform(6, 40)), P((200, 200, 200), 0.22))
    return dict(vign=0.75, mono=0.92, grain=0.06)


def frame(cv, t):
    if t < 4.7:
        return shot1(cv, t)
    if t < 6.25:
        return shot2(cv, t)
    return shot3(cv, t)


if __name__ == '__main__':
    out = harness.render('TEST_OPENING', 0.0, 8.0, frame, stills=(0, 45, 90, 120, 160, 200, 236))
    print(out)
