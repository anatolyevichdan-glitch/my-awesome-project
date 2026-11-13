import math, skia, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from gfx import *
import rig as R, anim as A, scenes as S, env as E
from anim import keyf, kexp, ease, lerp
from rig import V

WW = 5.2        # walk angular speed (rad/s)
WSPD = 127 * WW  # px/s per unit scale for planted foot
FONT_PATH = '/tmp/hoplite/workspace/rem/subs/fonts/Oswald-Bold-static.ttf'


def blur_bg(f, sigma):
    if sigma <= 0:
        return
    img = f.bg.surf.makeImageSnapshot()
    flt = skia.ImageFilters.Blur(sigma, sigma)
    pnt = skia.Paint(ImageFilter=flt)
    f.bg.c.drawImage(img, 0, 0, skia.SamplingOptions(), pnt)


def fog_puff(f, x, y, T, t0, dirx=1.0, n=7, size=1.0):
    age0 = T - t0
    if age0 < 0 or age0 > 1.6:
        return
    cv = f.fg.c
    for i in range(n):
        age = age0 - i * 0.05
        if age < 0:
            continue
        r = (22 + 80 * age) * size
        px = x + dirx * (60 * age + 20 * i * age) * size
        py = y - 70 * age * size - 8 * i
        cv.drawCircle(px, py, r, P((226, 234, 252), max(0, 0.34 * (1 - age / 1.4)), blur=r * 0.5))


def breath_fog(f, x, y, T, period=1.9, dirx=1.0, size=1.0, ph=0.0):
    k = math.floor((T - ph) / period)
    for j in (k - 1, k):
        fog_puff(f, x, y, T, j * period + ph, dirx, size=size)


def new(T, seed=0, ambient=None, gain=1.3):
    f = Frame(T, seed)
    f.grade['gain'] = gain
    return f


# ---------------------------------------------------------------- shots
class Out:
    def __init__(self):
        self.zoom = 1.0
        self.ox = 0.0
        self.oy = 0.0
        self.shake = 0.0
        self.cctv = False
        self.flash = 0.0
        self.fade = 1.0
        self.mono = 0.0
        self.title = None
        self.glitch = 0.0


def hpose(T, e, yaw=0.0, seed=0, **kw):
    p = R.Pose()
    p.yaw = yaw
    p.e = R.EXPR[e] if isinstance(e, str) else e
    A.idle(p, T, seed)
    return p


def phone_inset(f, T, u, text1, text2, t_in=0.0, buzz=0.0, hand=True, big=1.0):
    """full-screen phone close-up: sender line + new message sliding in"""
    cv = f.fg.c
    sh = buzz * 8 * math.sin(T * 90)
    cx_, cy_ = 540 + sh, 800
    w, h = 700 * big, 1280 * big
    # hands
    if hand:
        for sd in (-1, 1):
            hx = cx_ + sd * (w / 2 + 6)
            cv.drawRoundRect(skia.Rect(hx - 70, cy_ + 60, hx + 70, cy_ + 760), 70, 70, P(shader=lin((hx - 70, 0), (hx + 70, 0), (246, 196, 180), (226, 160, 150))))
        cv.drawRoundRect(skia.Rect(cx_ - 120, cy_ + h / 2 - 80, cx_ + 120, cy_ + h / 2 + 60), 50, 50, P((246, 196, 180)))
    cv.drawRoundRect(skia.Rect(cx_ - w / 2 - 16, cy_ - h / 2 - 16, cx_ + w / 2 + 16, cy_ + h / 2 + 16), 70, 70, P((14, 16, 22)))
    cv.drawRoundRect(skia.Rect(cx_ - w / 2, cy_ - h / 2, cx_ + w / 2, cy_ + h / 2), 56, 56, P(shader=lin((0, cy_ - h / 2), (0, cy_ + h / 2), (24, 34, 58), (12, 16, 30))))
    fo = skia.Font(E.TF, 54)
    fo2 = skia.Font(E.TF, 74)
    cv.drawString('Неизвестный номер', cx_ - w / 2 + 50, cy_ - h / 2 + 120, fo, P((150, 170, 210)))
    cv.drawLine(cx_ - w / 2 + 40, cy_ - h / 2 + 150, cx_ + w / 2 - 40, cy_ - h / 2 + 150, P((60, 74, 110), style='stroke', width=3))
    a = ease((u - t_in) / 0.25)
    if a > 0:
        yb = cy_ - 60 + (1 - a) * 80
        bw = w - 120
        cv.drawRoundRect(skia.Rect(cx_ - w / 2 + 50, yb - 100, cx_ - w / 2 + 50 + bw, yb + 130), 40, 40, P((46, 80, 160), a))
        lines = text1
        for i, ln in enumerate(lines):
            cv.drawString(ln, cx_ - w / 2 + 90, yb + 8 + i * 84, fo2, P((240, 246, 255), a))
    cv.drawString('сейчас', cx_ + w / 2 - 190, cy_ + h / 2 - 60, skia.Font(E.TF, 40), P((110, 130, 170)))
    f.glow(cx_, cy_, 900, (120, 170, 255), 0.10)
    f.light_pool(cx_, cy_ + 200, 1100, (0.35, 0.45, 0.75), 0.5)


def sound_wave_glitch(arr, T, k):
    if k <= 0:
        return arr
    rng = np.random.default_rng(int(T * 30))
    out = arr.copy()
    for _ in range(int(6 * k) + 1):
        y0 = int(rng.integers(0, H - 80))
        h_ = int(rng.integers(8, 60))
        dx = int(rng.integers(-60, 60) * k)
        out[y0:y0 + h_] = np.roll(arr[y0:y0 + h_], dx, axis=1)
    return out


def cctv_post(arr, T):
    a = arr.astype(np.float32)
    g = a.mean(axis=2, keepdims=True)
    a = g * np.array([0.78, 1.0, 0.82]) * 1.05 + a * 0.08
    rng = np.random.default_rng(int(T * 24))
    a += rng.normal(0, 7, a.shape[:2])[..., None]
    a[::3] *= 0.86
    a = np.clip(a, 0, 255).astype(np.uint8)
    im = Image.fromarray(a)
    d = ImageDraw.Draw(im)
    fo = ImageFont.truetype(FONT_PATH, 54)
    fs = ImageFont.truetype(FONT_PATH, 40)
    if int(T * 2) % 2 == 0:
        d.ellipse((70, 112, 112, 154), fill=(230, 40, 40))
    d.text((130, 100), 'REC', font=fo, fill=(235, 240, 235))
    sec = int(T)
    d.text((70, 190), 'CAM 03 · УЛ. ЛЕСНАЯ', font=fs, fill=(210, 230, 210))
    d.text((70, 240), '23:41:%02d' % (7 + sec % 50), font=fs, fill=(210, 230, 210))
    L_ = 60
    for (x0, y0, dx, dy) in ((L_, L_, 1, 1), (W - L_, L_, -1, 1), (L_, H - L_, 1, -1), (W - L_, H - L_, -1, -1)):
        d.line((x0, y0, x0 + 90 * dx, y0), fill=(230, 235, 230), width=5)
        d.line((x0, y0, x0, y0 + 90 * dy), fill=(230, 235, 230), width=5)
    return np.asarray(im)


def post(arr, o, T):
    if o.cctv:
        arr = cctv_post(arr, T)
    if o.glitch > 0:
        arr = sound_wave_glitch(arr, T, o.glitch)
    im = Image.fromarray(arr)
    z = o.zoom
    sx = o.shake * 14 * math.sin(T * 61 + 1.3)
    sy = o.shake * 10 * math.sin(T * 47)
    if z != 1.0 or o.ox or o.oy or sx or sy:
        cw, ch = W / z, H / z
        cx_ = W / 2 + o.ox + sx
        cy_ = H / 2 + o.oy + sy
        cx_ = min(max(cx_, cw / 2), W - cw / 2)
        cy_ = min(max(cy_, ch / 2), H - ch / 2)
        box = (cx_ - cw / 2, cy_ - ch / 2, cx_ + cw / 2, cy_ + ch / 2)
        im = im.resize((W, H), Image.BICUBIC, box=box)
    a = np.asarray(im).astype(np.float32)
    if o.mono > 0:
        g = a.mean(axis=2, keepdims=True)
        a = a * (1 - o.mono) + g * o.mono
    if o.flash > 0:
        a = a + (255 - a) * o.flash
    a *= o.fade
    return np.clip(a, 0, 255).astype(np.uint8)
