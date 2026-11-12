"""Compositing helpers shared by all scenes."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import rig
from rig import clamp, lerp, smooth
from world import World, Cam, FX, W, H

FX_ = None
WORLDS = {}


def fx():
    global FX_
    if FX_ is None: FX_ = FX()
    return FX_


def world(kind):
    if kind not in WORLDS: WORLDS[kind] = World(kind, seed={'street': 3, 'alley': 8, 'courtyard': 5}[kind])
    return WORLDS[kind]


def integ(fn, t, dt=1 / 60.0):
    """Numerical integral of fn over [0,t]."""
    n = max(1, int(t / dt)); h = t / n; s = 0.0
    for i in range(n):
        s += fn((i + 0.5) * h) * h
    return s


def ease(a, b, t, f=smooth): return a + (b - a) * f(t)
def seg(t, t0, t1): return clamp((t - t0) / (t1 - t0))


def place(img, drawfn, ox, oy, s, ext, alpha=1.0, fog=0.0, fogcol=(48, 60, 74), reflect=0.0, soft=0.0, q=None):
    """drawfn(d, layer, ox, oy, s) draws at feet (ox,oy). ext=(left,right,top,bottom) in metres from the feet."""
    l, r, top, bot = ext
    x0, x1 = int(ox - l * s), int(ox + r * s); y0, y1 = int(oy - top * s), int(oy + bot * s)
    X0, X1, Y0, Y1 = max(0, x0), min(W, x1), max(0, y0), min(H, y1 + int(top * s * 0.0))
    if X1 <= X0 or Y1 <= Y0: return None
    # draw region may exceed frame at bottom for reflection; keep frame clip only
    w, h = X1 - X0, Y1 - Y0
    if q is None: q = 2 if (w * h < 1.3e6 and s < 700) else 1
    layer = Image.new('RGBA', (w * q, h * q), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    drawfn(d, layer, (ox - X0) * q, (oy - Y0) * q, s * q)
    if q > 1: layer = layer.resize((w, h), Image.LANCZOS)
    a = layer.getchannel('A')
    rgb = layer.convert('RGB')
    if fog > 0:
        fc = Image.new('RGB', (w, h), tuple(int(c) for c in fogcol))
        rgb = Image.blend(rgb, fc, clamp(fog))
    if alpha < 1: a = a.point(lambda v: int(v * alpha))
    if soft > 0 and w * h < 3e6:
        sm = a.filter(ImageFilter.GaussianBlur(max(1.0, soft * s)))
        halo = Image.new('RGB', (w, h), (6, 8, 12))
        img.paste(halo, (X0, Y0), sm.point(lambda v: int(v * 0.55)))
    if reflect > 0:
        fy = int(oy - Y0)
        if 0 < fy < h:
            part = rgb.crop((0, 0, w, fy)).transpose(Image.FLIP_TOP_BOTTOM)
            pa = a.crop((0, 0, w, fy)).transpose(Image.FLIP_TOP_BOTTOM)
            rows = np.linspace(1, 0, fy)[:, None] ** 1.5 * reflect
            pa = Image.fromarray((np.asarray(pa).astype(np.float32) * rows).astype(np.uint8), 'L')
            pa = pa.filter(ImageFilter.GaussianBlur(2.0)); part = part.filter(ImageFilter.GaussianBlur(1.5))
            img.paste(part, (X0, int(oy)), pa)
    img.paste(rgb, (X0, Y0), a)
    return a


def lighting(wd, X, Z, li, base=0.34):
    I = wd.illum(X, Z, li)
    lit = clamp(base + 0.85 * (I - 0.1), 0.18, 1.35)
    wm = clamp((I - 0.1) * 1.2, 0, 0.6)
    tint = (0.82 + 0.25 * wm, 0.94 + 0.04 * wm, 1.12 - 0.3 * wm)
    return lit, tint, I


HERO_EXT = (1.6, 1.6, 2.4, 0.05)
ENT_EXT = (1.9, 1.9, 3.0, 0.05)


def put_hero(img, cam, wd, X, Z, yaw_world, P, e=None, li=None, kind='hero', reflect=0.35, persp=0.10, ldir=None, fog=None, lit_override=None, sweat=0.0):
    """yaw_world: 0 facing +z? we convert: heading sign h=+1 means facing +z. Camera dir converts to screen yaw."""
    p = cam.proj(X, 0, Z)
    if not p: return None
    sx, sy, dz, k = p
    li = li or [1.0] * len(wd.lamps)
    lit, tint, I = lighting(wd, X, Z, li)
    if lit_override is not None: lit = lit_override
    fogv = fog if fog is not None else 1 - math.exp(-dz * 0.02)
    fn = lambda d, layer, ox, oy, s: rig.render_hero(d, layer, ox, oy, s, yaw_world, P, e, kind, lit, tint, ldir if ldir is not None else -1, persp)
    return place(img, fn, sx, sy, k, HERO_EXT, fog=fogv * 0.8, reflect=reflect)


def screen_yaw(cam, heading):
    """heading +1 faces +z. returns yaw (0 faces camera, pi away)."""
    return 0.0 if heading * cam.dir < 0 else math.pi


def put_entity(img, cam, wd, X, Z, heading, P, li=None, alpha=1.0, fog=None, scale=1.0, reflect=0.3, base_xy=None, yaw=None):
    p = cam.proj(X, 0, Z) if base_xy is None else (base_xy[0], base_xy[1], 10, base_xy[2])
    if not p: return None
    sx, sy, dz, k = p
    li = li or [1.0] * len(wd.lamps)
    I = wd.illum(X, Z, li)
    lit = clamp((I - 0.1) * 0.35, 0, 0.5)
    fogv = fog if fog is not None else 1 - math.exp(-dz * 0.03)
    yw = screen_yaw(cam, heading) if yaw is None else yaw
    fn = lambda d, layer, ox, oy, s: rig.render_entity(d, layer, ox, oy, s, yw, P, lit=lit)
    ext = (ENT_EXT[0], ENT_EXT[1], ENT_EXT[2], ENT_EXT[3])
    return place(img, fn, sx, sy, k * scale, ext, alpha=alpha, fog=fogv * 0.55, reflect=reflect, soft=0.02)


def finish(arr_or_img, t, hor=None, **kw):
    arr = np.asarray(arr_or_img).astype(np.float32)
    return fx().apply(arr, t, hor=hor, **kw)


def to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')


def drift(t, a=1.0):
    return a * (3.0 * math.sin(t * 0.55) + 1.5 * math.sin(t * 1.3 + 1)), a * (2.0 * math.sin(t * 0.43 + 2) + 1.0 * math.sin(t * 1.1))
