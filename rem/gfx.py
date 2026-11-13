"""Graphics core: skia drawing helpers, layered Frame with light map, emissive, bloom, grade."""
import math
import numpy as np
import skia

W, H = 1080, 1920
LS = 4  # light-map downscale


def rgb(c, a=1.0):
    return skia.Color4f(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, a)


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, v * k)) for v in c[:3])


def P(c=(0, 0, 0), a=1.0, style=None, width=1.0, shader=None, blur=0.0, blend=None, cap=None, join=None):
    p = skia.Paint(AntiAlias=True)
    if shader is not None:
        p.setShader(shader)
    else:
        p.setColor4f(rgb(c, a))
    if style == 'stroke':
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(width)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap)
        p.setStrokeJoin(join or skia.Paint.kRound_Join)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend is not None:
        p.setBlendMode(blend)
    return p


def lin(p0, p1, c0, c1, a0=1.0, a1=1.0):
    return skia.GradientShader.MakeLinear([p0, p1], [rgb(c0, a0), rgb(c1, a1)])


def lin_n(p0, p1, stops):
    """stops: [(pos,(r,g,b),a)]"""
    return skia.GradientShader.MakeLinear([p0, p1], [rgb(c, a) for _, c, a in stops], [s for s, _, _ in stops])


def rad(c, r, c0, c1, a0=1.0, a1=0.0):
    return skia.GradientShader.MakeRadial(c, max(r, 1.0), [rgb(c0, a0), rgb(c1, a1)])


def rad_n(c, r, stops):
    return skia.GradientShader.MakeRadial(c, max(r, 1.0), [rgb(cc, a) for _, cc, a in stops], [s for s, _, _ in stops])


def path_poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def path_smooth(pts, close=True, tension=0.5):
    """Catmull-Rom -> cubic path through pts"""
    n = len(pts)
    p = skia.Path()
    p.moveTo(*pts[0])
    rng = range(n) if close else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (close or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (close or i + 2 < n) else pts[(i + 1) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3 * 1.0, p1[1] + (p2[1] - p0[1]) * tension / 3 * 1.0)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3 * 1.0, p2[1] - (p3[1] - p1[1]) * tension / 3 * 1.0)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if close:
        p.close()
    return p


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) <= 2:
        return pts

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for q in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    up = []
    for q in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def rounded_hull(pts, r):
    """hull of pts, polygon inflated by circle r via stroking+filling"""
    h = hull(pts)
    return path_poly(h)


def capsule_path(a, b, ra, rb):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    ca = skia.Path(); ca.addCircle(ax, ay, ra)
    if L < 1e-3:
        return ca
    cb = skia.Path(); cb.addCircle(bx, by, rb)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    s_ = max(-0.98, min(0.98, (ra - rb) / L))
    c = math.sqrt(1 - s_ * s_)
    t1 = (nx * c + ux * s_, ny * c + uy * s_)
    t2 = (-nx * c + ux * s_, -ny * c + uy * s_)
    q = path_poly([(ax + t1[0] * ra, ay + t1[1] * ra), (bx + t1[0] * rb, by + t1[1] * rb),
                   (bx + t2[0] * rb, by + t2[1] * rb), (ax + t2[0] * ra, ay + t2[1] * ra)])
    u = skia.Op(ca, cb, skia.PathOp.kUnion_PathOp)
    return skia.Op(u, q, skia.PathOp.kUnion_PathOp) if u is not None else q


def ellipse_path(cx, cy, rx, ry, rot=0.0):
    p = skia.Path()
    p.addOval(skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry))
    if rot:
        m = skia.Matrix()
        m.setRotate(math.degrees(rot), cx, cy)
        p.transform(m)
    return p


def mat(a, b, c, d, tx, ty):
    """x' = a x + c y + tx ; y' = b x + d y + ty"""
    return skia.Matrix.MakeAll(a, c, tx, b, d, ty, 0, 0, 1)


class Layer:
    def __init__(self, w=W, h=H, scale=1.0):
        self.w, self.h = int(w * scale), int(h * scale)
        self.surf = skia.Surface(self.w, self.h)
        self.c = self.surf.getCanvas()
        if scale != 1.0:
            self.c.scale(scale, scale)
        self.scale = scale

    def clear(self, color=skia.ColorTRANSPARENT):
        self.c.clear(color)

    def arr(self):
        img = self.surf.makeImageSnapshot()
        a = img.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
        return a

    def arr_premul(self):
        img = self.surf.makeImageSnapshot()
        return img.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)


class Frame:
    """bg: opaque scene color; ch: characters (transparent); fg: foreground overlays (transparent);
    light: ambient+lights (multiplicative); emi: emissive/additive; fx: rain etc."""
    def __init__(self, t=0.0, seed=0):
        self.t = t
        self.rng = np.random.default_rng(seed)
        self.bg = Layer()
        self.ch = Layer()
        self.fg = Layer()
        self.emi = Layer()
        self.light = Layer(scale=1.0 / LS)
        self.rim = []        # (mask_layer_array_source, dir, color, strength)
        self.ambient = (0.35, 0.42, 0.62)
        self.bg.clear(skia.ColorBLACK)
        self.light.clear(skia.ColorBLACK)
        self.ch.clear(); self.fg.clear(); self.emi.clear()
        self.grade = dict(shadow=(0.0, 0.01, 0.03), gain=1.55, vig=0.5, grain=0.022, bloom=0.65, fogcol=None,
                          contrast=1.06, sat=1.0, dof=0.0, fade=1.0, flash=0.0)
        self.rims = []

    # lights ---------------------------------------------------------
    def set_ambient(self, c):
        self.ambient = c
        self.light.c.clear(skia.Color4f(c[0], c[1], c[2], 1.0))

    def light_pool(self, x, y, r, c, k=1.0, falloff=1.0):
        """soft round pool of light"""
        stops = [(0.0, tuple(v * 255 * k for v in c), 1.0), (0.45, tuple(v * 255 * k * 0.55 * falloff for v in c), 1.0),
                 (1.0, (0, 0, 0), 1.0)]
        sh = rad_n((x, y), r, stops)
        self.light.c.drawCircle(x, y, r, P(shader=sh, blend=skia.BlendMode.kPlus))

    def light_cone(self, x, y, y2, w1, w2, c, k=1.0):
        """vertical cone / trapezoid pool from (x,y) down to y2"""
        pts = [(x - w1, y), (x + w1, y), (x + w2, y2), (x - w2, y2)]
        sh = lin_n((x, y), (x, y2), [(0, tuple(v * 255 * k for v in c), 1.0), (1, (0, 0, 0), 1.0)])
        self.light.c.drawPath(path_poly(pts), P(shader=sh, blend=skia.BlendMode.kPlus))

    def light_rect(self, x0, y0, x1, y1, c, k=1.0, blur=12):
        self.light.c.drawRect(skia.Rect(x0, y0, x1, y1), P(tuple(v * 255 * k for v in c), blur=blur, blend=skia.BlendMode.kPlus))

    def glow(self, x, y, r, c, a=0.8):
        sh = rad_n((x, y), r, [(0, c, a), (0.3, c, a * 0.45), (1, c, 0.0)])
        self.emi.c.drawCircle(x, y, r, P(shader=sh, blend=skia.BlendMode.kPlus))

    # compose ---------------------------------------------------------
    def compose(self):
        g = self.grade
        # composite bg + ch + fg in skia (premult safe)
        self.bg.c.drawImage(self.ch.surf.makeImageSnapshot(), 0, 0)
        self.bg.c.drawImage(self.fg.surf.makeImageSnapshot(), 0, 0)
        a = self.bg.arr()[..., :3].astype(np.float32) / 255.0
        lm = self.light.arr()[..., :3].astype(np.float32) / 255.0
        lm = np.repeat(np.repeat(lm, LS, axis=0), LS, axis=1)[:H, :W]
        # smooth the blocky light map
        lm = _smooth(lm)
        out = a * lm * g['gain']
        e = self.emi.arr_premul().astype(np.float32) / 255.0
        ea = e[..., :3]
        # bloom
        small = ea[::4, ::4]
        bl = _blur(_blur(small, 3), 6)
        bl = np.repeat(np.repeat(bl, 4, axis=0), 4, axis=1)[:H, :W]
        out = out + ea + bl * g['bloom']
        # rim lights (from character silhouette)
        for (mask, dx, dy, col, k) in self.rims:
            sh = np.roll(np.roll(mask, int(dy), axis=0), int(dx), axis=1)
            edge = np.clip(mask - sh, 0, 1)
            edge = _blur(edge[..., None].repeat(3, 2)[::2, ::2], 1.2)
            edge = np.repeat(np.repeat(edge, 2, 0), 2, 1)[:H, :W, 0:1]
            out = out + edge * np.array(col, np.float32) * k
        if g['dof'] > 0:
            pass
        # grade: lifted shadows tint, contrast, vignette, grain
        out = out + np.array(g['shadow'], np.float32)
        out = np.clip(out, 0, 4)
        out = out / (1.0 + 0.25 * out)  # soft shoulder
        out = out * 1.25
        out = np.clip(out, 0, 1)
        c = g['contrast']
        out = np.clip((out - 0.5) * c + 0.5, 0, 1)
        yy, xx = np.mgrid[0:H:8, 0:W:8]
        v = 1.0 - g['vig'] * ((((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2))
        v = np.clip(v, 0.25, 1.0).astype(np.float32)
        v = np.repeat(np.repeat(v, 8, 0), 8, 1)[:H, :W, None]
        out = out * v
        if g['grain'] > 0:
            n = self.rng.standard_normal((H // 2, W // 2, 1)).astype(np.float32)
            n = np.repeat(np.repeat(n, 2, 0), 2, 1)[:H, :W]
            out = out + n * g['grain'] * (0.4 + 0.6 * (1 - out.mean(axis=2, keepdims=True)))
        if g['flash'] > 0:
            out = out + g['flash']
        out = out * g['fade']
        return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def _blur(a, s):
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(a, sigma=(s, s, 0) if a.ndim == 3 else s)


def _smooth(lm):
    from scipy.ndimage import uniform_filter
    return uniform_filter(lm, size=(LS * 2 - 1, LS * 2 - 1, 1))
