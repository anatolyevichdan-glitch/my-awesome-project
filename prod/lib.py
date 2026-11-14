import math
import numpy as np
import cv2
import skia

W, H = 1080, 1920
FPS = 30
PI = math.pi

ADD = skia.BlendMode.kPlus
SCREEN = skia.BlendMode.kScreen
ATOP = skia.BlendMode.kSrcATop
MULT = skia.BlendMode.kMultiply
OVER = skia.BlendMode.kOverlay
DSTOVER = skia.BlendMode.kDstOver


def hx(h):
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def C(h, a=1.0):
    if isinstance(h, int):
        return skia.ColorSetA(h, max(0, min(255, int(a * 255))))
    r, g, b = hx(h)
    return skia.ColorSetARGB(max(0, min(255, int(a * 255))), r, g, b)


def mixh(h1, h2, t):
    a, b = hx(h1), hx(h2)
    t = max(0.0, min(1.0, t))
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def P(c=None, a=1.0, w=0, blur=0, blend=None, shader=None, cap=True):
    p = skia.Paint(AntiAlias=True)
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(max(0.0, min(1.0, a)))
    elif c is not None:
        p.setColor(C(c, a))
    if w:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        if cap:
            p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur and blur > 0.3:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend is not None:
        p.setBlendMode(blend)
    return p


def lin(p0, p1, cols, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)],
                                          [C(h, a) for h, a in cols], pos)


def rad(cen, r, cols, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*cen), max(0.5, r),
                                          [C(h, a) for h, a in cols], pos)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ramp(t, a, b):
    if b == a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def sm(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def eout(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ein(x):
    x = clamp(x)
    return x ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def nz(t, seed=0.0):
    s = seed * 12.9898
    return (math.sin(t * 1.73 + s) * 0.5 + math.sin(t * 2.97 + s * 1.7 + 1.1) * 0.3
            + math.sin(t * 5.31 + s * 2.3 + 2.3) * 0.2)


def hsh(i):
    x = math.sin(i * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)


def path(pts, close=True, smooth=False):
    p = skia.Path()
    if not pts:
        return p
    if not smooth:
        p.moveTo(*pts[0])
        for q in pts[1:]:
            p.lineTo(*q)
    else:
        n = len(pts)
        p.moveTo(*pts[0])
        rng = range(n) if close else range(n - 1)
        for i in rng:
            p0 = pts[(i - 1) % n] if (close or i > 0) else pts[i]
            p1 = pts[i]
            p2 = pts[(i + 1) % n]
            p3 = pts[(i + 2) % n] if (close or i + 2 < n) else pts[(i + 1) % n]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if close:
        p.close()
    return p


def oval(cx, cy, rx, ry):
    return skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)


def shake(t, amp, seed=0.0, fr=1.0):
    return (amp * nz(t * 9 * fr, seed), amp * nz(t * 8.3 * fr, seed + 3.3), amp * 0.04 * nz(t * 6 * fr, seed + 7))


# ---------------------------------------------------------------- textures
def fbm(n, octaves, seed, base=4):
    rng = np.random.default_rng(seed)
    out = np.zeros((n, n), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = base * 2 ** o
        a = rng.random((s, s)).astype(np.float32)
        out += cv2.resize(a, (n, n), interpolation=cv2.INTER_CUBIC) * amp
        tot += amp
        amp *= 0.55
    return out / tot


def _mkimg(gray, alpha=None):
    g = np.clip(gray * 255, 0, 255).astype(np.uint8)
    a = np.full_like(g, 255) if alpha is None else np.clip(alpha * 255, 0, 255).astype(np.uint8)
    arr = np.ascontiguousarray(np.dstack([g, g, g, a]))
    return skia.Image.fromarray(arr)


_conc = fbm(512, 7, 1, 4)
_conc = (_conc - _conc.mean()) * 1.8 + 0.5
_stain = fbm(512, 3, 9, 2)
_conc = np.clip(_conc - np.clip(_stain - 0.55, 0, 1) * 1.2, 0, 1)
CONCRETE = _mkimg(_conc)
_st = cv2.resize(np.random.default_rng(3).random((8, 512)).astype(np.float32), (512, 512), interpolation=cv2.INTER_LINEAR)
_st = 0.5 + (_st - 0.5) * 0.6 + (fbm(512, 4, 5) - 0.5) * 0.3
STEEL = _mkimg(np.clip(_st, 0, 1))


def tex_paint(img, a=0.4, blend=OVER, scale=1.0, ox=0, oy=0):
    m = skia.Matrix()
    m.setScale(scale, scale)
    m.postTranslate(ox, oy)
    sh = img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, skia.SamplingOptions(skia.FilterMode.kLinear), m)
    p = skia.Paint(AntiAlias=True, Shader=sh, BlendMode=blend)
    p.setAlphaf(a)
    return p


# ---------------------------------------------------------------- fonts
FONT_XB = skia.Typeface.MakeFromFile('fonts/Montserrat-ExtraBold.ttf')
FONT_BL = skia.Typeface.MakeFromFile('fonts/Montserrat-Black.ttf')
FONT_B = skia.Typeface.MakeFromFile('fonts/Montserrat-Bold.ttf')


def text_c(c, s, x, y, size, col='#ffffff', a=1.0, tf=None, spacing=0.0, outline=0, ocol='#000000', blur=0):
    f = skia.Font(tf or FONT_XB, size)
    widths = [f.measureText(ch) for ch in s]
    total = sum(widths) + spacing * (len(s) - 1)
    xx = x - total / 2
    for ch, w in zip(s, widths):
        if outline:
            c.drawString(ch, xx, y, f, P(ocol, a, w=outline, blur=blur))
        c.drawString(ch, xx, y, f, P(col, a, blur=blur if not outline else 0))
        xx += w + spacing


# ---------------------------------------------------------------- post
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_d = np.sqrt(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H * 0.47) / (H * 0.62)) ** 2)
VIG = np.clip(1.0 - 0.75 * np.clip(_d - 0.45, 0, 1) ** 1.4, 0.15, 1)[..., None].astype(np.float32)
_rng = np.random.default_rng(11)
GRAIN = [(_rng.standard_normal((H // 2, W // 2)).astype(np.float32)) for _ in range(6)]
GRAIN = [cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] for g in GRAIN]
# grading LUT: lift blacks to navy, gentle S-curve
_x = np.arange(256, dtype=np.float32) / 255
_s = _x + 0.22 * (_x - 0.5) * (1 - np.abs(2 * _x - 1)) * 1.0
LUT_R = np.clip((_s * 0.97 + 0.012) * 255, 0, 255).astype(np.uint8)
LUT_G = np.clip((_s * 0.99 + 0.016) * 255, 0, 255).astype(np.uint8)
LUT_B = np.clip((_s * 0.98 + 0.03) * 255, 0, 255).astype(np.uint8)


def post(arr, o, fi):
    img = arr[:, :, :3]
    uw = o.get('uw', 0)
    if uw:
        t = fi / FPS
        mx = _xx + uw * (np.sin(_yy * 0.012 + t * 3.1) * 7 + np.sin(_yy * 0.031 - t * 4.7) * 3)
        my = _yy + uw * (np.sin(_xx * 0.010 + t * 2.3) * 6)
        img = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    band = o.get('band')  # (y, strength) underwater region below y
    if band is not None:
        y0, st, t = band[0], band[1], fi / FPS
        y0 = int(clamp(y0, 0, H - 1))
        if y0 < H - 1:
            sub = img[y0:].copy()
            hh = sub.shape[0]
            yy, xx = _yy[:hh], _xx[:hh]
            mx = xx + np.sin(yy * 0.03 + t * 5) * 9 * st
            my = yy + np.sin(xx * 0.02 + t * 3) * 4 * st
            sub = cv2.remap(sub, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            sub = cv2.GaussianBlur(sub, (0, 0), 2.5 * st + 0.1)
            tint = np.array([20, 70, 85], np.float32)
            sub = (sub.astype(np.float32) * 0.55 + tint * 0.45).astype(np.uint8)
            img = img.copy()
            img[y0:] = sub
    ca = o.get('ca', 0)
    if ca:
        k = int(round(ca))
        if k:
            img = img.copy()
            img[:, k:, 0] = img[:, :-k, 0]
            img[:, :-k, 2] = img[:, k:, 2]
    blur = o.get('blur', 0)
    if blur > 0.3:
        img = cv2.GaussianBlur(img, (0, 0), blur)
    img = np.dstack([cv2.LUT(img[:, :, 0], LUT_R), cv2.LUT(img[:, :, 1], LUT_G), cv2.LUT(img[:, :, 2], LUT_B)])
    f = img.astype(np.float32)
    f *= VIG if o.get('vig', 1) else 1.0
    g = o.get('grain', 5.0)
    if g:
        f += GRAIN[fi % len(GRAIN)] * g
    fl = o.get('flash', 0)
    if fl:
        f += fl * 255
    bk = o.get('black', 0)
    if bk:
        f *= (1 - clamp(bk))
    out = np.empty((H, W, 4), np.uint8)
    out[:, :, :3] = np.clip(f, 0, 255)
    out[:, :, 3] = 255
    return out
