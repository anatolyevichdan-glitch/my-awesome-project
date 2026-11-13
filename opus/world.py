"""Night-city environments in the PAPA VERNULSYA flat style: big flat shapes, few soft gradients,
warm sodium lamps against cold blue night, falling snow. Everything is drawn in layers with a
parallax factor so the camera can track a walking character."""
import math
import random
import sys
import numpy as np
import skia

sys.path.insert(0, '/tmp/hoplite/workspace/rem')
from gfx import P, lin, rad, path_poly, path_smooth, mix  # noqa: E402

W, H = 1080, 1920
SODIUM = (255, 196, 120)


def sky(cv, top=(10, 13, 30), bot=(38, 44, 74), y1=H):
    cv.drawRect(skia.Rect(0, 0, W, y1), P(shader=lin((0, 0), (0, y1), top, bot)))


def moon(cv, x, y, r=46):
    cv.drawCircle(x, y, r * 5, P(shader=rad((x, y), r * 5, (120, 130, 170), (120, 130, 170), 0.18, 0.0)))
    cv.drawCircle(x, y, r, P((214, 218, 230)))
    cv.drawCircle(x + r * 0.3, y - r * 0.2, r * 0.22, P((196, 200, 214)))


def panel_building(cv, x, w, top, base, col, seed, lit=0.18, cols=None, floor_h=86, t=0.0, lit_col=(236, 186, 112),
                   balconies=True, dark=False):
    """Soviet panel block: flat facade, window grid, a few warm windows, balcony slabs, roof edge."""
    rnd = random.Random(seed)
    cv.drawRect(skia.Rect(x, top, x + w, base), P(col))
    # side shade + roof lip
    cv.drawRect(skia.Rect(x + w - w * 0.07, top, x + w, base), P(tuple(c * 0.78 for c in col)))
    cv.drawRect(skia.Rect(x - 6, top - 10, x + w + 6, top + 4), P(tuple(c * 0.7 for c in col)))
    cols = cols or max(3, int(w / 110))
    cw = w / cols
    rows = int((base - top - 40) / floor_h)
    for r in range(rows):
        y = top + 34 + r * floor_h
        for c in range(cols):
            wx = x + c * cw + cw * 0.22
            ww = cw * 0.56
            on = (not dark) and rnd.random() < lit
            if on:
                flick = 1.0 if rnd.random() > 0.08 else 0.6 + 0.4 * math.sin(t * 9 + seed + r)
                wc = mix((40, 34, 40), lit_col, flick)
                cv.drawRect(skia.Rect(wx - 8, y - 8, wx + ww + 8, y + floor_h * 0.5 + 8),
                            P(lit_col, 0.10 * flick, blur=10))
                cv.drawRect(skia.Rect(wx, y, wx + ww, y + floor_h * 0.5), P(wc))
                cv.drawRect(skia.Rect(wx + ww * 0.48, y, wx + ww * 0.52, y + floor_h * 0.5), P(tuple(v * 0.7 for v in wc)))
            else:
                cv.drawRect(skia.Rect(wx, y, wx + ww, y + floor_h * 0.5), P(tuple(c * 0.55 for c in col)))
        if balconies and r % 1 == 0:
            cv.drawRect(skia.Rect(x + w * 0.04, y + floor_h * 0.62, x + w * 0.93, y + floor_h * 0.68),
                        P(tuple(c * 0.86 for c in col)))


def lamp(cv, x, base, h=640, on=1.0, side=1, glow_r=360):
    """curved-arm street lamp; light pool on the ground; returns lamp-head point."""
    pole = (28, 30, 42)
    cv.drawRect(skia.Rect(x - 7, base - h, x + 7, base), P(pole))
    cv.drawRect(skia.Rect(x - 14, base - 30, x + 14, base), P(pole))
    arm = skia.Path()
    arm.moveTo(x, base - h)
    arm.quadTo(x, base - h - 60, x + side * 90, base - h - 52)
    cv.drawPath(arm, P(pole, style='stroke', width=10))
    hx, hy = x + side * 100, base - h - 44
    cv.drawRoundRect(skia.Rect(hx - 34, hy - 12, hx + 34, hy + 8), 8, 8, P(pole))
    if on > 0.01:
        cv.drawOval(skia.Rect(hx - 26, hy + 2, hx + 26, hy + 14), P(mix((90, 80, 60), (255, 236, 190), on)))
        # cone
        cone = path_poly([(hx - 24, hy + 8), (hx + 24, hy + 8), (hx + glow_r * 0.55, base), (hx - glow_r * 0.55, base)])
        cv.drawPath(cone, P(shader=lin((hx, hy), (hx, base), SODIUM, SODIUM, 0.20 * on, 0.02 * on), blur=18))
        cv.drawCircle(hx, hy + 8, 110, P(shader=rad((hx, hy + 8), 110, SODIUM, SODIUM, 0.55 * on, 0.0)))
        # ground pool
        cv.drawOval(skia.Rect(hx - glow_r, base - 34, hx + glow_r, base + 46),
                    P(shader=rad((hx, base + 6), glow_r, SODIUM, SODIUM, 0.30 * on, 0.0)))
    return hx, hy


def tree(cv, x, base, h, seed=1, col=(16, 18, 30), w0=16):
    rnd = random.Random(seed)

    def br(x0, y0, ang, ln, wd, d):
        x1 = x0 + math.cos(ang) * ln
        y1 = y0 - math.sin(ang) * ln
        cv.drawLine(x0, y0, x1, y1, P(col, style='stroke', width=wd))
        if d <= 0 or ln < 14:
            return
        for _ in range(2 + (d > 2)):
            br(x1, y1, ang + rnd.uniform(-0.65, 0.65), ln * rnd.uniform(0.6, 0.78), wd * 0.66, d - 1)
    br(x, base, math.pi / 2 + rnd.uniform(-0.05, 0.05), h * 0.38, w0, 5)


def street_ground(cv, gy, cx=0.0):
    """sidewalk (with snow) + curb + road below; gy = sidewalk line where feet stand."""
    cv.drawRect(skia.Rect(0, gy - 40, W, gy + 150), P(shader=lin((0, gy - 40), (0, gy + 150), (58, 62, 86), (44, 47, 68))))
    # paving joints scroll with camera
    off = (-cx) % 220
    for i in range(-1, 7):
        x = i * 220 + off
        cv.drawLine(x, gy - 40, x - 60, gy + 150, P((50, 53, 74), style='stroke', width=3))
    # wet curb line at building base
    cv.drawRect(skia.Rect(0, gy - 52, W, gy - 40), P((70, 76, 104)))
    cv.drawRect(skia.Rect(0, gy + 150, W, gy + 176), P((112, 118, 146)))   # curb
    cv.drawRect(skia.Rect(0, gy + 176, W, H), P(shader=lin((0, gy + 176), (0, H), (30, 32, 48), (18, 19, 30))))
    off2 = (-cx * 1.15) % 300
    for i in range(-1, 5):
        x = i * 300 + off2
        cv.drawRect(skia.Rect(x, gy + 300, x + 150, gy + 312), P((90, 92, 110), 0.5))


def rainfall(cv, t, seed=5, n=120, speed=1900, ln=46, cx=0.0, par=1.0, alpha=0.32, slant=0.12, area=(0, 0, W, H)):
    """fine drizzle streaks"""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = area
    for _ in range(n):
        bx, by, sp = rnd.random(), rnd.random(), rnd.uniform(0.75, 1.25)
        y = y0 + ((by * (y1 - y0) + t * speed * sp) % (y1 - y0))
        x = x0 + ((bx * (x1 - x0) - cx * par + y * slant) % (x1 - x0))
        L = ln * sp
        cv.drawLine(x, y, x + L * slant, y + L, P((190, 200, 226), alpha * rnd.uniform(0.4, 1.0), style='stroke', width=1.6))


def wet_reflection(cv, x, gy, col, w=40, ln=260, a=0.35):
    """vertical smeared reflection of a light source on wet pavement"""
    cv.drawRect(skia.Rect(x - w, gy, x + w, gy + ln),
                P(shader=lin((x, gy), (x, gy + ln), col, col, a, 0.0), blur=w * 0.4))


def snowfall(cv, t, seed=3, n=140, speed=90, size=(2.0, 5.0), cx=0.0, par=1.0, alpha=0.8, area=(0, 0, W, H)):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = area
    for _ in range(n):
        bx, by = rnd.uniform(0, 1), rnd.uniform(0, 1)
        sp = rnd.uniform(0.6, 1.4)
        r = rnd.uniform(*size)
        y = y0 + ((by * (y1 - y0) + t * speed * sp) % (y1 - y0))
        x = x0 + ((bx * (x1 - x0) - cx * par + 24 * math.sin(t * 0.9 * sp + bx * 30)) % (x1 - x0))
        cv.drawCircle(x, y, r, P((226, 232, 246), alpha * rnd.uniform(0.5, 1.0), blur=r * 0.35))


def breath_puff(cv, x, y, age, s=1.0, side=1):
    """visible cold breath; age 0..1"""
    if not (0 <= age <= 1):
        return
    for k in range(3):
        a = age * (1 - k * 0.15)
        cx = x + side * (30 + 120 * a + k * 26) * s
        cy = y - (10 + 60 * a + k * 10) * s
        r = (18 + 60 * a + k * 10) * s
        cv.drawCircle(cx, cy, r, P((214, 222, 240), 0.22 * (1 - age) * (1 - k * 0.25), blur=r * 0.5))


# ------------------------------------------------------------------ post
_rng = np.random.default_rng(7)


def grade(img, t, vign=0.55, grain=0.016, lift=(6, 8, 14), cool=0.0, mono=0.0):
    """img float32 HxWx3 0..255 -> uint8. vignette, film grain, black lift, optional mono (CCTV)."""
    h, w = img.shape[:2]
    ys, xs = np.ogrid[0:h, 0:w]
    d = ((xs - w / 2) / (w * 0.62)) ** 2 + ((ys - h * 0.46) / (h * 0.62)) ** 2
    v = 1 - vign * np.clip(d, 0, 1.4) ** 1.3
    out = img * v[..., None]
    if mono > 0:
        g = out.mean(axis=2, keepdims=True)
        out = out * (1 - mono) + g * np.array([0.86, 1.0, 0.92]) * mono
    if cool:
        out = out * np.array([1 - cool * 0.06, 1.0, 1 + cool * 0.08])
    out = out + np.array(lift) * (1 - out / 255)
    out = out + _rng.normal(0, 255 * grain, (h, w, 1))
    return np.clip(out, 0, 255).astype(np.uint8)
