"""Night-city environments (flat vector, PAPA-style), drawn per frame with parallax pan."""
import math, skia, numpy as np
from gfx import *

GY = 1560  # default ground line (sidewalk/ground contact for characters)
FONT = skia.Typeface.MakeFromFile('/tmp/hoplite/workspace/rem/fonts/Oswald-Bold.ttf') if False else None

def R_(f, x0, y0, x1, y1, c, a=1.0, r=0, layer='bg'):
    cv = getattr(f, layer).c
    if r: cv.drawRoundRect(skia.Rect(x0, y0, x1, y1), r, r, P(c, a))
    else: cv.drawRect(skia.Rect(x0, y0, x1, y1), P(c, a))

def grad_rect(cv, x0, y0, x1, y1, c0, c1):
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(shader=lin((0, y0), (0, y1), c0, c1)))

def sky(f, top=(14, 18, 40), bot=(46, 52, 86)):
    grad_rect(f.bg.c, 0, 0, W, 1300, top, bot)

def facade(f, x0, x1, ytop, ybot, col, seed, cols=4, rows=9, lit=0.25, win=(20, 30, 58), t=0.0, dark_all=False, lit_col=(236, 190, 108)):
    cv = f.bg.c
    cv.drawRect(skia.Rect(x0, ytop, x1, ybot), P(shader=lin((0, ytop), (0, ybot), shade(col, 1.05), shade(col, 0.78))))
    rng = np.random.default_rng(seed)
    w = x1 - x0
    cw = w / cols
    rh = (ybot - ytop) / (rows + 0.6)
    for r in range(rows):
        for c in range(cols):
            wx0 = x0 + c * cw + cw * 0.16
            wx1 = x0 + (c + 1) * cw - cw * 0.16
            wy0 = ytop + (r + 0.45) * rh
            wy1 = wy0 + rh * 0.58
            on = (not dark_all) and rng.random() < lit
            col2 = lit_col if on else win
            if on:
                col2 = shade(col2, 0.85 + 0.15 * math.sin(t * 0.4 + r + c))
            cv.drawRect(skia.Rect(wx0, wy0, wx1, wy1), P(col2))
            cv.drawRect(skia.Rect((wx0 + wx1) / 2 - 3, wy0, (wx0 + wx1) / 2 + 3, wy1), P(shade(col, 0.6)))
            cv.drawRect(skia.Rect(wx0 - 8, wy1, wx1 + 8, wy1 + 9), P(shade(col, 1.3)))
            if on:
                f.glow((wx0 + wx1) / 2, (wy0 + wy1) / 2, cw * 0.7, lit_col, 0.22)
                f.light_pool((wx0 + wx1) / 2, wy1 + 80, cw * 0.9, (0.55, 0.42, 0.22), 0.5)

def ground(f, y=GY, road=(34, 36, 50), walk=(70, 74, 98), curb=(96, 100, 126), road_y=None):
    cv = f.bg.c
    grad_rect(cv, 0, y - 150, W, y + 60, shade(walk, 0.8), walk)
    cv.drawRect(skia.Rect(0, y + 60, W, y + 100), P(curb))
    grad_rect(cv, 0, y + 100, W, H, road, shade(road, 0.55))
    for i in range(-1, 8):
        cv.drawRect(skia.Rect(i * 190 + 30, y + 190, i * 190 + 150, y + 205), P((150, 154, 170), 0.35))

def lamp(f, x, base, h, on=1.0, tint=(255, 214, 140), spread=300, layer='bg', flick=0.0):
    cv = getattr(f, layer).c
    col = (58, 60, 74)
    cv.drawRect(skia.Rect(x - 8, base - h, x + 8, base), P(shader=lin((x - 8, 0), (x + 8, 0), (84, 88, 108), col)))
    cv.drawOval(skia.Rect(x - 36, base - 8, x + 36, base + 10), P((20, 22, 30), 0.6))
    cv.drawRect(skia.Rect(x - 18, base - 70, x + 18, base - 40), P(col))
    p = skia.Path(); p.moveTo(x - 8, base - h); p.quadTo(x - 8, base - h - 60, x + 60, base - h - 60); p.lineTo(x + 130, base - h - 52)
    cv.drawPath(p, P(col, style='stroke', width=14, cap=skia.Paint.kRound_Cap))
    hx, hy = x + 130, base - h - 40
    cv.drawPath(path_poly([(hx - 50, hy - 14), (hx + 50, hy - 14), (hx + 34, hy + 8), (hx - 34, hy + 8)]), P((44, 46, 58)))
    k = on * (1.0 - flick)
    cv.drawOval(skia.Rect(hx - 32, hy + 4, hx + 32, hy + 16), P(mix((70, 70, 80), tint, k)))
    if k > 0.02:
        f.light_cone(hx, hy + 10, base + 40, 40, spread, tuple(c / 255 for c in tint), 0.6 * k)
        f.light_pool(hx, hy + 20, 160, tuple(c / 255 for c in tint), 0.22 * k)
        f.light_pool(hx, base + 10, spread * 0.9, tuple(c / 255 for c in tint), 0.42 * k)
        f.glow(hx, hy + 10, 90, tint, 0.5 * k)
    return hx, hy

def tree(f, x, base, h, seed=1, col=(22, 24, 36), layer='bg'):
    cv = getattr(f, layer).c
    rng = np.random.default_rng(seed)
    pa = skia.Path()
    def br(x0, y0, ang, ln, wd, d):
        x1, y1 = x0 + math.cos(ang) * ln, y0 - math.sin(ang) * ln
        cv.drawLine(x0, y0, x1, y1, P(col, style='stroke', width=wd))
        if d > 0:
            for s in (-1, 1):
                br(x1, y1, ang + s * rng.uniform(0.3, 0.7), ln * rng.uniform(0.62, 0.78), max(2, wd * 0.66), d - 1)
    br(x, base, math.pi / 2, h * 0.38, 12, 5)

def bench(f, x, y, s=1.0):
    cv = f.bg.c
    cv.drawRect(skia.Rect(x, y - 70 * s, x + 220 * s, y - 56 * s), P((88, 66, 52)))
    cv.drawRect(skia.Rect(x, y - 36 * s, x + 220 * s, y - 24 * s), P((88, 66, 52)))
    for dx in (14, 196): cv.drawRect(skia.Rect(x + dx * s, y - 70 * s, x + (dx + 10) * s, y), P((36, 38, 50)))

def snow(f, t, n=150, speed=120, layer='fg', size=3.0):
    cv = getattr(f, layer).c
    rng = np.random.default_rng(7)
    xs, ys, ph, sz = rng.random(n) * W, rng.random(n) * H, rng.random(n) * 6.28, rng.uniform(0.6, 1.6, n)
    for i in range(n):
        x = (xs[i] + 30 * math.sin(t * 0.8 + ph[i]) + t * 22) % W
        y = (ys[i] + t * speed * sz[i]) % H
        cv.drawCircle(x, y, size * sz[i], P((230, 236, 250), 0.55 * min(1, sz[i])))

def fog_band(f, y, h, a=0.25, col=(120, 130, 170), layer='bg'):
    cv = getattr(f, layer).c
    cv.drawRect(skia.Rect(0, y - h, W, y + h), P(shader=lin_n((0, y - h), (0, y + h), [(0, col, 0.0), (0.5, col, a), (1, col, 0.0)])))

def sign_text(cv, text, x, y, size, col, bold=True):
    fo = skia.Font(TF, size)
    cv.drawString(text, x, y, fo, P(col))

TF = skia.Typeface.MakeFromFile('/tmp/hoplite/workspace/rem/fonts/Oswald.ttf') if False else None
import glob as _g
_fs = _g.glob('/tmp/hoplite/workspace/rem/subs/fonts/*') + _g.glob('/tmp/hoplite/workspace/rem/fonts/*')
for _p in _fs:
    if 'Oswald' in _p and _p.endswith('.ttf') and 'Bold' in _p or ('Anton' in _p and TF is None):
        TF = skia.Typeface.MakeFromFile(_p)
if TF is None:
    TF = skia.Typeface.MakeFromFile(_fs[0])
