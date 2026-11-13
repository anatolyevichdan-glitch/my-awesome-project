"""The shadow entity: tall, coherent, wrong. Narrow shoulders, long neck, very long uneven arms,
hidden face, smoky textured surface with a cold rim. Drawn as one silhouette (unioned tapered
limbs) so it reads as a single body, then textured and rimmed."""
import math
import numpy as np
import skia
import sys
sys.path.insert(0, '/tmp/hoplite/workspace/rem')
from gfx import P, lin, rad, capsule_path, path_smooth  # noqa: E402

BODY = (9, 9, 15)
BODY_HI = (26, 28, 40)

_noise_img = None


def noise_shader(scale=1.0, alpha=0.5, t=0.0):
    global _noise_img
    if _noise_img is None:
        rng = np.random.default_rng(5)
        n = rng.random((256, 256)).astype(np.float32)
        from scipy.ndimage import gaussian_filter
        a = gaussian_filter(n, 2.0, mode='wrap') * 0.6 + gaussian_filter(n, 7.0, mode='wrap') * 0.9
        a = (a - a.min()) / (a.max() - a.min())
        rgba = np.zeros((256, 256, 4), np.uint8)
        v = (a * 255).astype(np.uint8)
        rgba[..., 0] = v; rgba[..., 1] = v; rgba[..., 2] = np.clip(v * 1.15, 0, 255).astype(np.uint8); rgba[..., 3] = 255
        _noise_img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)
    m = skia.Matrix()
    m.setScale(scale, scale)
    m.postTranslate(0, -t * 20 * scale)
    return _noise_img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, skia.SamplingOptions(skia.FilterMode.kLinear), m)


def tapered(a, b, ra, rb):
    return capsule_path(a, b, ra, rb)


def union(paths):
    out = paths[0]
    for q in paths[1:]:
        r = skia.Op(out, q, skia.PathOp.kUnion_PathOp)
        if r is not None:
            out = r
    return out


class CPose:
    def __init__(self):
        self.step = 0.0          # walk phase (cycles)
        self.stride = 0.0        # 0 = standing
        self.lean = 0.0          # forward bend of the torso (rad, + toward screen-left = facing dir)
        self.bend = 0.0          # 0..1 big bow from the hips (rooftop lean)
        self.head_roll = 0.0     # unnatural tilt
        self.head_turn = 0.0     # -1..1 toward camera
        self.neck_fwd = 0.25
        self.arm = {1: 0.0, -1: 0.0}     # swing angle offsets (rad)
        self.reach = {1: 0.0, -1: 0.0}   # 0..1 reach forward/down
        self.facing = -1         # -1 faces screen-left, +1 faces screen-right, 0 = toward camera
        self.breathe = 0.0


def skeleton(cp, x, base, h):
    """2D joints in screen space. h = standing height in px."""
    k = h / 1000.0
    f = cp.facing if cp.facing != 0 else 0
    st = cp.step
    J = {}
    hip_y = base - 470 * k
    # slow, long strides: hips barely bob, feet lift low and late
    bob = 10 * k * math.cos(4 * math.pi * st) * min(1, cp.stride * 3)
    J['hip'] = (x, hip_y + bob)
    for sd, off in ((1, 0.0), (-1, 0.5)):
        q = (st + off) % 1.0
        if q < 0.6:
            u = q / 0.6
            fx = (0.5 - u) * cp.stride * 300 * k
            fy = 0.0
        else:
            u = (q - 0.6) / 0.4
            fx = (-0.5 + (0.5 - 0.5 * math.cos(math.pi * u))) * cp.stride * 300 * k
            fy = -40 * k * math.sin(math.pi * u) * min(1, cp.stride * 3)
        lat = 0 if f != 0 else sd * 42 * k
        J[('foot', sd)] = (x + f * fx * -1 * -1 + lat, base + fy) if f != 0 else (x + lat, base + fy)
    # torso: narrow, slightly concave, long
    bend = cp.bend
    lean = cp.lean + bend * 1.25
    dirx = -1 if f <= 0 else 1
    if f == 0:
        dirx = 0
    tl = 360 * k
    sh = (J['hip'][0] + math.sin(lean) * tl * (dirx if dirx else 0.0), J['hip'][1] - math.cos(lean) * tl)
    J['chest'] = ((J['hip'][0] + sh[0]) / 2, (J['hip'][1] + sh[1]) / 2 - 10 * k)
    J['sh'] = sh
    # neck: long, pushed forward, the head hangs
    nl = 150 * k
    na = lean + cp.neck_fwd + bend * 0.5
    head = (sh[0] + math.sin(na) * nl * (dirx if dirx else 0.0), sh[1] - math.cos(na) * nl)
    J['head'] = head
    shw = 62 * k
    for sd in (1, -1):
        # narrow, uneven shoulders (left one lower)
        sx = sh[0] + sd * shw * (1 if dirx == 0 else 0.45)
        sy = sh[1] + (14 * k if sd == -1 else 0) + 8 * k
        J[('shoulder', sd)] = (sx, sy)
        # arms: very long, delayed swing, reaching
        L1 = (285 if sd == 1 else 305) * k
        L2 = (270 if sd == 1 else 295) * k
        swing = cp.arm[sd] + 0.18 * math.sin(2 * math.pi * (st + (0.5 if sd == 1 else 0.0) - 0.15)) * min(1, cp.stride * 2.5)
        base_ang = lean * 0.6 + swing + sd * (0.06 if dirx == 0 else 0.0)
        rch = cp.reach[sd]
        a1 = base_ang + rch * (1.2 + bend * 0.4)
        a2 = a1 + 0.12 + rch * 0.5
        dd = dirx if dirx else 1
        el = (sx + math.sin(a1) * L1 * dd * (1 if dirx else 0.55 * sd), sy + math.cos(a1) * L1)
        wr = (el[0] + math.sin(a2) * L2 * dd * (1 if dirx else 0.55 * sd), el[1] + math.cos(a2) * L2)
        J[('elbow', sd)] = el
        J[('wrist', sd)] = wr
        J[('fang', sd)] = a2
    for sd in (1, -1):
        hx = J['hip'][0] + sd * 34 * k * (0.5 if dirx else 1)
        foot = J[('foot', sd)]
        # knee: bends forward, slightly too high (long shins)
        mx, my = (hx + foot[0]) / 2, (J['hip'][1] + foot[1]) / 2
        kx = mx + (dirx if dirx else 0) * 34 * k * -1 * -1
        J[('hipj', sd)] = (hx, J['hip'][1])
        J[('knee', sd)] = (kx + (dirx if dirx else 0) * 20 * k, my - 30 * k)
    return J


def draw(cv, cp, x, base, h, t=0.0, alpha=1.0, rim=(70, 92, 150), rim_dir=(0.7, -0.4), smoke=1.0, layer_emi=None):
    """draw the entity; returns joints"""
    J = skeleton(cp, x, base, h)
    k = h / 1000.0
    parts = []
    for sd in (1, -1):
        parts.append(tapered(J[("hipj", sd)], J[("knee", sd)], 52 * k, 28 * k))
        parts.append(tapered(J[("knee", sd)], J[("foot", sd)], 28 * k, 12 * k))
        # long narrow foot
        fx, fy = J[('foot', sd)]
        dd = 1 if cp.facing > 0 else -1
        if cp.facing == 0:
            parts.append(tapered((fx, fy - 6 * k), (fx, fy + 4 * k), 22 * k, 16 * k))
        else:
            parts.append(tapered((fx - dd * 12 * k, fy - 8 * k), (fx + dd * 70 * k, fy), 14 * k, 8 * k))
    # torso: hips -> narrow waist -> chest -> narrow shoulders
    hx, hy = J['hip']
    sx, sy = J["sh"]
    dirx = 0 if cp.facing == 0 else (-1 if cp.facing < 0 else 1)
    vx, vy = sx - hx, sy - hy
    Lt = math.hypot(vx, vy) or 1
    vx, vy = vx / Lt, vy / Lt
    nx, ny = -vy, vx                  # perpendicular (screen-right when upright)
    back = -(dirx if dirx else 0)     # sign of the back side along n
    if dirx == 0:
        prof = [(0.0, 66, 66), (0.33, 46, 46), (0.66, 84, 84), (0.86, 80, 80), (1.0, 60, 60)]
    else:
        prof = [(0.0, 60, 60), (0.33, 42, 46), (0.66, 64, 84), (0.86, 52, 100), (1.0, 34, 66)]   # (front, back): hunched back
    pts_f, pts_b = [], []
    for (u, wf, wb) in prof:
        cx_, cy_ = hx + vx * Lt * u, hy + vy * Lt * u
        sb = back if back else 1
        pts_b.append((cx_ + nx * sb * wb * k, cy_ + ny * sb * wb * k))
        pts_f.append((cx_ - nx * sb * wf * k, cy_ - ny * sb * wf * k))
    tor = path_smooth(pts_f + pts_b[::-1], True, 0.5)
    parts.append(tor)
    parts.append(tapered(J["sh"], J["head"], 34 * k, 26 * k))
    # head: small, elongated backwards, tilted; faceless
    hx2, hy2 = J['head']
    hp = skia.Path()
    hp.addOval(skia.Rect(-50 * k, -80 * k, 50 * k, 66 * k))
    m = skia.Matrix()
    m.setRotate(math.degrees(cp.head_roll) + (12 if cp.facing < 0 else -12 if cp.facing > 0 else 0))
    m.postTranslate(hx2, hy2 - 30 * k)
    hp.transform(m)
    parts.append(hp)
    fingers = []
    for sd in (1, -1):
        parts.append(tapered(J[("shoulder", sd)], J[("elbow", sd)], 28 * k, 18 * k))
        parts.append(tapered(J[("elbow", sd)], J[("wrist", sd)], 18 * k, 11 * k))
        wx, wy = J[('wrist', sd)]
        a = J[('fang', sd)]
        dd = 1 if cp.facing >= 0 else -1
        for j in range(4):
            sp = (j - 1.5) * 0.16
            L = (120 + 25 * (j in (1, 2))) * k
            ex = wx + math.sin(a + sp) * L * dd * (1 if cp.facing != 0 else 0.3)
            ey = wy + math.cos(a + sp) * L
            mx_ = (wx + ex) / 2 + math.cos(a) * 8 * k * dd
            my_ = (wy + ey) / 2
            fingers.append(tapered((wx, wy), (mx_, my_), 7 * k, 5 * k))
            fingers.append(tapered((mx_, my_), (ex, ey), 5 * k, 1.8 * k))
    body = union(parts + fingers)

    cv.save()
    # dark aura so it separates from the night
    cv.drawPath(body, P((0, 0, 4), 0.45 * alpha, blur=30 * k))
    # body fill: dark gradient + moving noise texture
    b = body.getBounds()
    cv.drawPath(body, P(shader=lin((0, b.top()), (0, b.bottom()), BODY_HI, BODY), a=alpha))
    pn = P(shader=noise_shader(1.6 * k + 0.4, t=t))
    pn.setAlphaf(0.10 * alpha)
    pn.setBlendMode(skia.BlendMode.kScreen)
    cv.save(); cv.clipPath(body, skia.ClipOp.kIntersect, True)
    cv.drawPaint(pn)
    # rim crescent from the light side
    rx, ry = rim_dir
    w = 7 * k + 1.2
    sh_ = skia.Path(body)
    sh_.offset(-rx * w, -ry * w)
    cres = skia.Op(body, sh_, skia.PathOp.kDifference_PathOp)
    if cres is not None and rim is not None:
        cv.drawPath(cres, P(rim, 0.75 * alpha, blur=1.2 * k + 0.5))
    # faint hollow where a face should be
    if cp.head_turn > 0.2:
        cv.drawOval(skia.Rect(hx2 - 20 * k, hy2 - 50 * k, hx2 + 20 * k, hy2 + 4 * k), P((0, 0, 0), 0.6 * alpha * min(1, cp.head_turn), blur=8 * k))
    cv.restore()
    # smoke: wisps peel off the silhouette and rise
    if smoke > 0:
        rng = np.random.default_rng(3)
        n = 26
        for i in range(n):
            ph = (t * 0.25 + rng.random()) % 1.0
            sx0 = b.left() + rng.random() * b.width()
            sy0 = b.top() + (0.15 + 0.85 * rng.random()) * b.height()
            px = sx0 + math.sin(t * 0.8 + i) * 18 * k + (ph * 40 * k) * (1 if i % 2 else -1)
            py = sy0 - ph * 220 * k
            r = (14 + 30 * ph) * k
            cv.drawCircle(px, py, r, P(BODY, 0.28 * smoke * alpha * (1 - ph) * math.sin(math.pi * min(1, ph * 3)), blur=r * 0.8))
    cv.restore()
    J['bounds'] = b
    return J
