"""Hero rig v2: 3D skeleton with IK, continuous body/head yaw, tapered limbs, hands, shoes, expressive face.

Local space: y up, +z = direction the character faces, +x = sign +1 side. Origin at ground between the feet.
Projection (body yaw ψ, 0 = facing camera, +π/2 = facing screen right):
    X = x cosψ + z sinψ ;  depth d = z cosψ - x sinψ (+ = toward camera)
    screen = (X, -y + d*TILT)
"""
import math
import numpy as np
from char import G, mix, col

TILT = 0.17
PERSP = 0.00045
ANKLE = 46.0
THIGH = 218.0
SHIN = 216.0
HIP_Y = 480.0
TORSO = 300.0
UARM = 168.0
FARM = 150.0
SH_W = 98.0
HIP_W = 50.0
HR = 80.0

SKIN = (243, 214, 205)
HAIR = (96, 52, 52)
HOOD = (92, 94, 104)
PANTS = (44, 46, 58)
SHOE = (206, 206, 214)
SOLE = (120, 120, 134)

EXPR = {
    'neutral': dict(eye=0.95, ir=0.52, brow=0.0, brin=0.0, mo=0.0, mw=1.0, mc=0.08, px=0, py=0),
    'worried': dict(eye=1.02, ir=0.48, brow=0.3, brin=0.75, mo=0.06, mw=0.9, mc=-0.35, px=0, py=0),
    'scared': dict(eye=1.2, ir=0.4, brow=0.65, brin=0.8, mo=0.35, mw=0.95, mc=-0.5, px=0, py=0),
    'terror': dict(eye=1.38, ir=0.32, brow=0.95, brin=0.95, mo=0.8, mw=1.05, mc=-0.4, px=0, py=0),
    'shock': dict(eye=1.32, ir=0.34, brow=0.95, brin=0.2, mo=0.6, mw=0.7, mc=0.0, px=0, py=0),
    'serious': dict(eye=0.78, ir=0.55, brow=-0.15, brin=-0.6, mo=0.0, mw=1.0, mc=-0.2, px=0, py=0),
    'pain': dict(eye=0.45, ir=0.5, brow=0.2, brin=0.9, mo=0.5, mw=1.2, mc=-0.7, px=0, py=0),
    'relief': dict(eye=0.7, ir=0.5, brow=0.1, brin=0.3, mo=0.25, mw=0.8, mc=0.15, px=0, py=0),
    'shh': dict(eye=0.82, ir=0.5, brow=-0.1, brin=-0.3, mo=0.0, mw=0.6, mc=0.3, px=0, py=0),
    'dead': dict(eye=0.9, ir=0.5, brow=-0.05, brin=-0.4, mo=0.0, mw=1.0, mc=0.02, px=0, py=0),
}
EKEYS = list(EXPR['neutral'].keys())


def expr(name, **kw):
    e = dict(EXPR[name]); e.update(kw); return e


def blend(a, b, t):
    a = EXPR[a] if isinstance(a, str) else a
    b = EXPR[b] if isinstance(b, str) else b
    t = max(0.0, min(1.0, t))
    return {k: a[k] * (1 - t) + b[k] * t for k in EKEYS}


def v3(*a): return np.array(a, float)


def lerp(a, b, t): return a + (b - a) * t


def shade(c, k): return tuple(max(0, min(255, v * k)) for v in c)


class Pose:
    def __init__(self, **kw):
        self.yaw = 0.0
        self.hip = (0.0, 0.0, 0.0)
        self.pelvis_twist = 0.0
        self.lean = 0.0      # torso pitch, + = forward
        self.roll = 0.0      # torso side lean
        self.twist = 0.0     # chest yaw relative to pelvis
        self.head_yaw = 0.0
        self.head_pitch = 0.0   # + = look down
        self.head_roll = 0.0
        self.foot = {-1: (-HIP_W, ANKLE, 0.0), 1: (HIP_W, ANKLE, 0.0)}
        self.foot_pitch = {-1: 0.0, 1: 0.0}
        self.foot_yaw = {-1: 0.0, 1: 0.0}
        self.hand = {-1: None, 1: None}          # local 3D target for wrist
        self.hand_mode = {-1: 'relaxed', 1: 'relaxed'}
        self.hand_rot = {-1: 0.0, 1: 0.0}
        self.elbow_pole = {-1: (-0.6, -0.2, -1.0), 1: (0.6, -0.2, -1.0)}
        self.knee_pole = (0.0, 0.1, 1.0)
        self.e = EXPR['neutral']
        self.blink = 0.0
        self.breath = 0.0
        self.sway = 0.0
        self.sway2 = 0.0
        self.black_eyes = False
        self.shoulder_up = 0.0
        self.point_ang = -math.pi / 2     # finger direction for 'point' mode
        self.mouth_talk = 0.0
        self.__dict__.update(kw)


def ik3(a, t, l1, l2, pole):
    """two-bone IK in 3D. returns (joint, end)."""
    d = t - a
    dist = float(np.linalg.norm(d))
    dist = max(min(dist, (l1 + l2) * 0.9995), abs(l1 - l2) + 1e-3)
    u = d / (np.linalg.norm(d) + 1e-9)
    p = np.array(pole, float)
    pv = p - u * float(p @ u)
    n = np.linalg.norm(pv)
    pv = pv / n if n > 1e-6 else np.array([0, 0, 1.0])
    ca = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    ca = max(-1, min(1, ca))
    sa = math.sqrt(1 - ca * ca)
    j = a + u * (l1 * ca) + pv * (l1 * sa)
    e = a + u * dist
    return j, e


def rot_x(v, ang):   # pitch: + tilts +z forward-down ... rotates y toward z
    c, s = math.cos(ang), math.sin(ang)
    return v3(v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c)


def rot_y(v, ang):
    c, s = math.cos(ang), math.sin(ang)
    return v3(v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)


class Cam:
    def __init__(self, x0, y0, s, yaw):
        self.x0, self.y0, self.s, self.yaw = x0, y0, s, yaw
        self.c, self.sn = math.cos(yaw), math.sin(yaw)

    def depth(self, v): return v[2] * self.c - v[0] * self.sn

    def P(self, v):
        X = v[0] * self.c + v[2] * self.sn
        d = v[2] * self.c - v[0] * self.sn
        f = 1 + d * PERSP
        return (self.x0 + self.s * X * f, self.y0 + self.s * (-v[1] * f + d * TILT)), d

    def p(self, v): return self.P(v)[0]

    def inv(self, sx, sy, d=0.0):
        """screen point + chosen depth -> local 3D (approx, ignores perspective)."""
        X = (sx - self.x0) / self.s
        y = -((sy - self.y0) / self.s - d * TILT)
        # X = x c + z sn ; d = z c - x sn
        x = X * self.c - d * self.sn
        z = X * self.sn + d * self.c
        return v3(x, y, z)


# ---------------------------------------------------------------- stroke helpers
def stroke_poly(pts, ws, n=6):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []; W = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y)); W.append(ws[i - 1] + (ws[i] - ws[i - 1]) * t)
    out.append(tuple(pts[-1])); W.append(ws[-1])
    L = []; R = []
    for i, (p, w) in enumerate(zip(out, W)):
        a = out[max(i - 1, 0)]; b = out[min(i + 1, len(out) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / l, dx / l
        L.append((p[0] + nx * w / 2, p[1] + ny * w / 2)); R.append((p[0] - nx * w / 2, p[1] - ny * w / 2))

    def cap(c, tdir, w, sign):
        tx, ty = tdir; nx, ny = -ty, tx; r = w / 2
        return [(c[0] + r * sign * (nx * math.cos(th) + tx * math.sin(th)), c[1] + r * sign * (ny * math.cos(th) + ty * math.sin(th)))
                for th in np.linspace(0, math.pi, 7)[1:-1]]
    t_end = (out[-1][0] - out[-2][0], out[-1][1] - out[-2][1]); l = math.hypot(*t_end) or 1; t_end = (t_end[0] / l, t_end[1] / l)
    t_st = (out[1][0] - out[0][0], out[1][1] - out[0][1]); l = math.hypot(*t_st) or 1; t_st = (-t_st[0] / l, -t_st[1] / l)
    # start cap points along -tangent
    sc = cap(out[0], t_st, W[0], -1)
    ec = cap(out[-1], t_end, W[-1], 1)
    return L + ec + R[::-1] + sc


def hull(pts):
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(pts) < 3: return pts

    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def ang_of(a, b): return math.atan2(b[1] - a[1], b[0] - a[0])


# ---------------------------------------------------------------- hand
def draw_hand(g, W, ang, s, skin, mode='relaxed', near=True, point_ang=None, outline=None, side=1, flip=1):
    """W wrist screen pos, ang direction of forearm (screen radians)."""
    ol = outline or shade(skin, 0.62)
    k = s
    c, sn = math.cos(ang), math.sin(ang)

    def at(l, w): return (W[0] + (c * l - sn * w) * k, W[1] + (sn * l + c * w) * k)
    lw = 2.4 * k
    if mode in ('relaxed', 'open', 'grab'):
        g.poly([at(-4, -15), at(26, -19), at(40, -12), at(42, 10), at(26, 17), at(-4, 14)], skin, ol, lw)
    else:
        g.poly([at(-4, -15), at(28, -18), at(38, -8), at(38, 12), at(24, 17), at(-4, 14)], skin, ol, lw)
    th = flip * side
    if mode == 'relaxed':
        for i, w in enumerate((-12, -4, 4, 12)):
            a0 = 0.15 + 0.08 * i
            g.capsule(at(38, w * 0.8), at(64 - i % 2 * 4, w + 6 * a0 * 6 * (1 if w > 0 else 0.6)), 9 * k, skin, ol, 1.4 * k)
        g.capsule(at(10, -14 * th), at(34, -26 * th), 10 * k, skin, ol, 1.4 * k)
    elif mode == 'open':
        for w, spread in ((-14, -0.36), (-5, -0.12), (5, 0.1), (14, 0.34)):
            a2 = spread
            g.capsule(at(38, w * 0.8), at(38 + 38 * math.cos(a2), w * 0.8 + 38 * math.sin(a2) * 1.0), 9 * k, skin, ol, 1.4 * k)
        g.capsule(at(10, -14 * th), at(32, -38 * th), 10.5 * k, skin, ol, 1.4 * k)
    elif mode == 'grab':
        for i, w in enumerate((-12, -4, 4, 12)):
            g.capsule(at(40, w * 0.8), at(58, w * 0.8 + 3), 9 * k, skin, ol, 1.4 * k)
            g.capsule(at(58, w * 0.8 + 3), at(54, w * 0.8 + 20 * th), 8.5 * k, skin, ol, 1.4 * k)
        g.capsule(at(10, -14 * th), at(36, -20 * th), 10 * k, skin, ol, 1.4 * k)
    elif mode == 'fist':
        g.ell(*at(30, 0), 22 * k, 20 * k, skin, ol, lw, n=18)
        for w in (-11, -4, 3, 10):
            g.ell(*at(46, w * 0.8), 6.5 * k, 6 * k, skin, ol, 1.3 * k, n=10)
        g.capsule(at(26, -16 * th), at(44, -12 * th), 9 * k, skin, ol, 1.4 * k)
    elif mode in ('point', 'shh'):
        pa = (point_ang if point_ang is not None else ang) - ang
        # curled fingers + extended index
        for w in (-4, 4, 12):
            g.ell(*at(40, w * 0.8), 7 * k, 6.5 * k, skin, ol, 1.3 * k, n=10)
        ix, iy = at(36, -9)
        tipx = ix + math.cos(ang + pa) * 56 * k; tipy = iy + math.sin(ang + pa) * 56 * k
        g.capsule((ix, iy), (tipx, tipy), 9.5 * k, skin, ol, 1.4 * k)
        g.capsule(at(10, -14 * th), at(32, -4 * th), 10 * k, skin, ol, 1.4 * k)


# ---------------------------------------------------------------- face
def head_pts(R, yaw, n=34):
    sx = math.sin(yaw)
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        ux, uy = math.cos(th), math.sin(th)
        rx = R * (0.94 + 0.06 * abs(sx)); ry = R * 1.1
        low = max(uy, 0.0)
        x = rx * ux * (1 - 0.34 * low ** 1.4)
        y = ry * uy - 4
        x += sx * R * 0.2 * low ** 1.5
        if ux * sx < 0 and uy < 0.2: x -= sx * R * 0.1 * abs(ux)   # back of skull
        pts.append((x, y))
    return pts


def face_pt(R, x, y, yaw, pitch):
    """feature on head ellipsoid. x,y in units of R (y down +). returns (X,Y,depth)."""
    z = math.sqrt(max(1.0 - x * x - (y * 0.7) ** 2, 0.0))
    p = v3(x, -y, z)
    p = rot_x(p, -pitch)
    p = rot_y(p, yaw)
    return p[0] * R, -p[1] * R, p[2]


def draw_head(g, C, s, yaw, pitch, roll, e, blink, skin, hair, black_eyes, talk=0.0, sway=0.0, view_back=False, hair_style=0):
    R = HR * s
    g.push(); g.xf(C[0], C[1], roll)
    cy, sy_ = math.cos(yaw), math.sin(yaw)
    ol = shade(skin, 0.6)
    olh = shade(hair, 0.55)
    lw = 2.6 * s
    # ---- hair back mass
    hb = [(x * 1.1 + (0), y * 1.04 - 6 * s) for x, y in head_pts(R, yaw)]
    # ---- skull / skin
    sil = head_pts(R, yaw)
    g.poly([(x * 1.0, y * 1.0 + 3 * s) for x, y in hb], hair, olh, lw)   # hair silhouette back
    facing = cy > -0.05
    # ears (behind skin when far)
    for side in (-1, 1):
        ex, ey, ed = face_pt(R, 0.96 * side, 0.06, yaw, pitch)
        if ed > -0.2 and abs(cy) < 0.97 or True:
            if ed > -0.15:
                g.ell(ex, ey, R * 0.12 * (0.45 + abs(sy_)), R * 0.2, skin, ol, lw, n=14)
    if facing:
        g.poly(sil, skin, ol, lw)
        # profile nose / brow ridge
        if abs(sy_) > 0.28:
            sgn = 1 if sy_ > 0 else -1
            nx, ny, nd = face_pt(R, 0.98 * sgn * min(1, 0.45 + abs(sy_)), 0.14, yaw, pitch)
            ext = R * 0.2 * (abs(sy_) ** 1.2)
            bx = nx + sgn * ext
            g.poly([(nx - sgn * R * 0.1, ny - R * 0.2), (bx, ny + R * 0.12), (nx - sgn * R * 0.05, ny + R * 0.2)], skin, ol, lw * 0.8)
            g.poly([(nx - sgn * R * 0.12, ny - R * 0.2), (bx - sgn * 1, ny + R * 0.1), (nx - sgn * R * 0.03, ny + R * 0.2)], skin)
    else:
        g.poly(sil, hair, olh, lw)
    # ---- hair top (cap bounded by hairline)
    hl = []
    for k in range(-18, 19):
        ph = k * 10 * math.pi / 180.0     # longitude from facing direction
        if abs(ph) < 1.2: yy = -0.43 + 0.07 * abs(math.sin(ph * 4.5 + 0.7)) + 0.05 * (1 - abs(ph) / 1.2) * 0
        elif abs(ph) < 1.75: yy = -0.43 + (abs(ph) - 1.2) / 0.55 * 0.36
        else: yy = -0.07 + (abs(ph) - 1.75) / (math.pi - 1.75) * 0.34
        lat = yy
        zz = math.cos(ph); xx = math.sin(ph)
        rr = math.sqrt(max(1 - lat * lat * 0.7, 0.0))
        p3 = v3(xx * rr * 1.04, -lat, zz * rr * 1.04)
        p3 = rot_x(p3, -pitch); p3 = rot_y(p3, yaw)
        hl.append((p3[0] * R, -p3[1] * R, p3[2]))
    vis = [(a, b) for a, b, d in hl if d > -0.04]
    top_out = []
    for i in range(0, 19):
        th = math.pi + math.pi * i / 18.0
        x, y = hb[0] if False else (0, 0)
        rx = R * 1.12; ry = R * 1.14
        top_out.append((rx * math.cos(th) + sway * 6 * s * (1 - math.sin(th) * -1) * 0.0, ry * math.sin(th) - 8 * s))
    if vis and facing or (vis and abs(yaw) > 1.5):
        poly = top_out + vis[::-1][:] if False else None
        # order vis from right to left on screen
        vis.sort(key=lambda p: -p[0])
        poly = top_out + [vis[0]] + vis + [vis[-1]]
        # top_out runs left->right so after it we go right->left through hairline
        g.poly(poly, hair, olh, lw)
        # hair highlight
        g.poly([(x * 0.7, y * 0.9 - 6 * s) for x, y in top_out[3:12]] + [(x * 0.55, y * 0.75 - 6 * s) for x, y in top_out[11:3:-1]], mix(hair, (255, 255, 255), 0.16), a=170)
    # ---- face features
    if facing:
        eo = e['eye']
        eyes = []
        for side in (-1, 1):
            ex, ey, ed = face_pt(R, 0.36 * side, -0.02, yaw, pitch)
            if ed < 0.04: continue
            eyes.append((side, ex, ey, ed))
        gx, gy = e['px'], e['py']
        for side, ex, ey, ed in eyes:
            fw = max(0.18, ed)
            ew = R * 0.30 * (0.55 + 0.45 * fw) * (0.9 + 0.1 * eo)
            op = max(0.06, min(1.4, eo * (1 - blink)))
            eh = R * 0.27 * op
            if black_eyes:
                g.ell(ex, ey, ew, max(eh, 1.5), (4, 4, 6), (0, 0, 0), 1.5 * s, n=18)
                g.ell(ex - ew * 0.25, ey - eh * 0.25, ew * 0.18, eh * 0.14, (70, 74, 96), a=170, n=10)
            else:
                g.ell(ex, ey, ew, max(eh, 1.5), (244, 242, 248), ol, 1.8 * s, n=20)
                ri = min(ew * 0.98, eh * 0.98) * (e['ir'] / 0.52) * 0.95
                ri = max(ri, 2.0)
                mx = (ew - ri) * 0.9; my = max(eh - ri, 0) * 0.9
                ix = ex + gx * mx * 1.0 + (sy_ * 0.0); iy = ey + gy * my
                g.ell(ix, iy, ri, ri, (88, 62, 52), (40, 24, 24), 1.2 * s, n=16)
                g.ell(ix, iy, ri * 0.5 * (1.0 if e['ir'] > 0.36 else 0.7), ri * 0.5 * (1.0 if e['ir'] > 0.36 else 0.7), (12, 10, 14), n=12)
                g.ell(ix - ri * 0.3, iy - ri * 0.35, ri * 0.22, ri * 0.22, (255, 255, 255), n=8)
            # upper lid line / lid shading
            g.line([(ex - ew, ey - eh * 0.1), (ex - ew * 0.5, ey - eh * 0.95), (ex + ew * 0.5, ey - eh * 0.95), (ex + ew, ey - eh * 0.1)], (50, 28, 32), 2.4 * s)
            if blink > 0.4:
                g.line([(ex - ew, ey), (ex, ey + eh * 0.5 + 2), (ex + ew, ey)], (50, 28, 32), 2.4 * s)
            # brow
            bh = -R * (0.3 + 0.11 * e['brow']) + 0
            inner = side * -1
            bx0, by0, _ = face_pt(R, 0.36 * side - 0.2 * side, -0.35 - 0.12 * e['brow'] - (0.02), yaw, pitch)
            bx1, by1, _ = face_pt(R, 0.36 * side + 0.2 * side, -0.35 - 0.1 * e['brow'], yaw, pitch)
            by0 -= e['brin'] * R * 0.1 * 1.0 * -1   # inner end moves
            g.line([(bx0, by0 - e['brin'] * R * 0.1), ((bx0 + bx1) / 2, (by0 + by1) / 2 - R * 0.03 - e['brin'] * R * 0.03), (bx1, by1 + e['brin'] * R * 0.025)],
                   shade(hair, 0.8), 6.5 * s)
        # nose
        nx, ny, nd = face_pt(R, 0.0, 0.17, yaw, pitch)
        if nd > 0.1:
            g.line([(nx, ny - R * 0.12), (nx - 3 * s - sy_ * 6 * s, ny + R * 0.1), (nx + 3 * s - sy_ * 6 * s, ny + R * 0.12)], shade(skin, 0.7), 2.2 * s)
        # mouth
        mo = max(0.0, min(1.0, e['mo'] + talk))
        mx0, my0, md = face_pt(R, -0.26 * e['mw'], 0.46, yaw, pitch)
        mx1, my1, _ = face_pt(R, 0.26 * e['mw'], 0.46, yaw, pitch)
        mcx, mcy, _ = face_pt(R, 0.0, 0.47, yaw, pitch)
        if md > 0.0:
            curve = e['mc'] * R * 0.14
            if mo < 0.07:
                g.line([(mx0, my0 - curve * 0.4), (mcx, mcy + curve), (mx1, my1 - curve * 0.4)], (120, 56, 64), 3.2 * s)
            else:
                oh = R * (0.06 + 0.3 * mo)
                up = [(mx0, my0), (mcx, mcy - curve * 0.3 - oh * 0.2), (mx1, my1)]
                lo = [(mx1, my1), (mcx, mcy + oh), (mx0, my0)]
                g.poly(up + lo[1:-1], (70, 22, 34), (120, 56, 64), 2.4 * s)
                if mo > 0.3:
                    g.poly([(mx0 * 0.6 + mcx * 0.4, my0 + oh * 0.2), (mcx, mcy - curve * 0.3 - oh * 0.15), (mx1 * 0.6 + mcx * 0.4, my1 + oh * 0.2), (mcx, mcy + oh * 0.08)], (240, 238, 240), a=235)
                    g.ell(mcx, mcy + oh * 0.55, (mx1 - mx0) * 0.2, oh * 0.25, (178, 74, 84), n=10)
        # cheeks/jaw shade
        sgn = 1 if sy_ >= 0 else -1
        g.poly([face_pt(R, 0.95 * sgn * -1, 0.2, yaw, pitch)[:2], face_pt(R, 0.65 * sgn * -1, 0.7, yaw, pitch)[:2], face_pt(R, 0.3 * sgn * -1, 0.85, yaw, pitch)[:2],
                face_pt(R, 0.9 * sgn * -1, 0.55, yaw, pitch)[:2]], shade(skin, 0.78), a=90)
    g.pop()


# ---------------------------------------------------------------- body
def solve(p, cam):
    """returns dict of 3D joints (local coordinates)."""
    J = {}
    hp = v3(*p.hip)
    P = v3(0, HIP_Y, 0) + hp
    J['pelvis'] = P
    sp = v3(math.sin(p.roll), math.cos(p.lean) * math.cos(p.roll), math.sin(p.lean))
    sp = sp / np.linalg.norm(sp)
    br = p.breath
    C = P + sp * (TORSO + 4 * br)
    J['chest'] = C
    J['spine'] = sp
    tw = p.twist
    ax = v3(math.cos(tw), -math.sin(p.roll) * 0.6, math.sin(tw))
    ax = rot_y(v3(1, 0, 0), tw) + v3(0, -math.sin(p.roll) * 0.5, 0)
    J['axis'] = ax
    for sd in (-1, 1):
        J[('sh', sd)] = C - sp * (30 - p.shoulder_up * 14 - 3 * br) + ax * (sd * SH_W)
        h = v3(sd * HIP_W, 0, 0)
        h = rot_y(h, p.pelvis_twist)
        J[('hip', sd)] = P + h
    nd = rot_x(sp, 0.0)
    J['neck'] = C + sp * 8
    hdir = rot_x(v3(0, 1, 0), 0.0)
    pitch = p.head_pitch
    hd = v3(0, math.cos(pitch * 0.5), math.sin(pitch * 0.5) * 0.6)
    J['head'] = C + sp * 30 + v3(0, 62, 0) * 1.0 + v3(0, 0, 12 + 22 * math.sin(p.lean)) + hd * 22
    J['head'] = C + sp * 24 + v3(0, 74, 4 + 28 * math.sin(p.lean) + 8 * math.sin(pitch))
    # legs
    for sd in (-1, 1):
        f = v3(*p.foot[sd])
        j, e = ik3(J[('hip', sd)], f, THIGH, SHIN, p.knee_pole)
        J[('knee', sd)] = j; J[('ankle', sd)] = e
    # arms
    for sd in (-1, 1):
        S = J[('sh', sd)]
        tgt = p.hand[sd]
        if tgt is None:
            tgt = S + v3(sd * 16, -(UARM + FARM) * 0.93, 8 + 20 * math.sin(p.lean))
        else:
            tgt = v3(*tgt)
        j, e = ik3(S, tgt, UARM, FARM, p.elbow_pole[sd])
        J[('elbow', sd)] = j; J[('wrist', sd)] = e
    return J


def torso_poly(g, cam, J, p, s, hood, outline):
    P = J['pelvis']; C = J['chest']; sp = J['spine']
    psi = cam.yaw + p.twist * 0.5
    n = 9
    Lp = []; Rp = []
    for i in range(n + 1):
        u = i / n
        c3 = P + (C - P) * u + sp * (-34)  # start slightly below the pelvis (hem)
        c3 = P + (C - P) * u - sp * (34 * (1 - u))
        a = lerp(78, 100, u ** 0.7) * (1 + 0.06 * math.sin(u * math.pi) + 0.03 * p.breath * u)
        if u > 0.9: a *= lerp(1.0, 0.82, (u - 0.9) / 0.1)
        b = lerp(56, 64, u) * (1 + 0.04 * p.breath)
        w = math.sqrt((a * math.cos(psi)) ** 2 + (b * math.sin(psi)) ** 2)
        (sx, sy), d = cam.P(c3)
        # perpendicular in screen: use shoulder axis projected
        Lp.append((c3, w))
    # screen center-line and normals
    cl = [cam.p(c) for c, _ in Lp]
    L = []; R = []
    for i, ((c3, w), (cx, cy)) in enumerate(zip(Lp, cl)):
        a_ = cl[max(i - 1, 0)]; b_ = cl[min(i + 1, len(cl) - 1)]
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(dx, dy) or 1
        nx, ny = -dy / l, dx / l
        L.append((cx + nx * w * s, cy + ny * w * s)); R.append((cx - nx * w * s, cy - ny * w * s))
    # shoulder rounding top & hem bottom
    top = cl[-1]; bot = cl[0]
    topL = L[-1]; topR = R[-1]
    cap = [(top[0] + (topL[0] - top[0]) * math.cos(t) + (top[0] - bot[0]) * 0.1 * math.sin(t) * 0 + (cl[-1][0] - cl[-2][0]) * 0.8 * math.sin(t),
            top[1] + (topL[1] - top[1]) * math.cos(t) + (cl[-1][1] - cl[-2][1]) * 0.8 * math.sin(t)) for t in np.linspace(0, math.pi, 7)[1:-1]]
    poly = L + cap + R[::-1]
    g.poly(poly, hood, outline, 2.8 * s)
    return L, R, cl, psi


def draw_hero(g, x0, y0, s, p, tint=None, double=False):
    """Draw hero at ground pos (x0,y0) design coords, scale s. Returns joint screen dict."""
    cam = Cam(x0, y0, s, p.yaw)
    J = solve(p, cam)
    skin, hair, hood, pants, shoe = SKIN, HAIR, HOOD, PANTS, SHOE
    if tint is not None:
        skin, hair, hood, pants, shoe = [tuple(min(255, c * t) for c, t in zip(col_, tint)) for col_ in (skin, hair, hood, pants, shoe)]
    hood_d = shade(hood, 0.62); hood_l = shade(hood, 1.25)
    ol_h = shade(hood, 0.45); ol_p = shade(pants, 0.5); ol_s = shade(skin, 0.6)
    out = {}
    S = {}
    for k, v in J.items():
        if isinstance(v, np.ndarray) and v.shape == (3,): S[k] = cam.P(v)
    scr = {k: v[0] for k, v in S.items()}
    dep = {k: v[1] for k, v in S.items()}
    lw = 2.6 * s

    parts = []   # (depth, fn)

    # ---- legs
    def leg(sd):
        far = dep[('hip', sd)] < 0 and abs(math.sin(cam.yaw)) > 0.25
        ck = 0.72 if far else 1.0
        pc = shade(pants, ck); ol = shade(pants, 0.5 * ck)
        hip = scr[('hip', sd)]; kn = scr[('knee', sd)]; an = scr[('ankle', sd)]
        pts = [hip, kn, an]
        ws = [92 * s, 70 * s, 50 * s]
        g.poly(stroke_poly(pts, ws, 7), pc, ol, lw)
        # knee highlight crease
        # shoe
        fa = v3(*p.foot[sd])
        fy = p.foot_yaw[sd] + (0.12 * sd)
        fwd = rot_y(v3(0, 0, 1), fy)
        lat = rot_y(v3(1, 0, 0), fy)
        pitch = p.foot_pitch[sd]
        base = v3(fa[0], max(J[('ankle', sd)][1] - ANKLE, 0.0), fa[2]) + v3(0, 0, 0)
        base = J[('ankle', sd)] - v3(0, ANKLE, 0)
        prof = [(-30, 0), (-34, 40), (-14, 60), (12, 56), (46, 32), (76, 14), (80, 0)]
        pivot = 50.0

        def to3(l, h, w_):
            ll = l - pivot; hh = h
            c_, s_ = math.cos(pitch), math.sin(pitch)
            l2 = ll * c_ - hh * s_ + pivot; h2 = ll * s_ + hh * c_
            return base + fwd * (l2 - 16) + lat * w_ + v3(0, h2, 0) + v3(0, 0, 0)
        pts2 = []
        for l, h in prof:
            for w_ in (-30, 30):
                pts2.append(cam.p(to3(l, h, w_ * (0.55 if l > 55 else 1.0))))
        g.poly(hull(pts2), shade(shoe, ck), shade(shoe, 0.55 * ck), lw)
        solep = []
        for l, h in ((-30, 0), (82, 0), (82, 13), (-30, 13)):
            for w_ in (-30, 30):
                solep.append(cam.p(to3(l, h, w_ * (0.62 if l > 55 else 1.0))))
        g.poly(hull(solep), shade(SOLE, ck * 0.9), shade(shoe, 0.4 * ck), lw * 0.8)
        # toe cap + laces
        tc = cam.p(to3(60, 24, 0)); g.ell(tc[0], tc[1], 11 * s, 7 * s, shade(shoe, 1.0 * ck * 0.85), n=12, a=200)
        lc = cam.p(to3(8, 56, 0)); lc2 = cam.p(to3(36, 42, 0))
        g.line([lc, lc2], shade(shoe, 0.55 * ck), 2.4 * s)
        return

    def pelvis():
        c3 = J['pelvis'] + v3(0, 4, 0)
        w = math.sqrt((82 * math.cos(cam.yaw)) ** 2 + (56 * math.sin(cam.yaw)) ** 2)
        cx, cy = cam.p(c3)
        g.ell(cx, cy, w * s, 62 * s, pants, ol_p, lw, n=22)

    # ---- arms
    def arm(sd):
        far = dep[('sh', sd)] < 0 and abs(math.sin(cam.yaw)) > 0.25 or (abs(math.sin(cam.yaw)) <= 0.25 and dep[('wrist', sd)] < -10)
        ck = 0.74 if far else 1.0
        hc = shade(hood, ck); ol = shade(hood, 0.45 * ck); sk = shade(skin, ck)
        sh = scr[('sh', sd)]; el = scr[('elbow', sd)]; wr = scr[('wrist', sd)]
        g.poly(stroke_poly([sh, el, wr], [62 * s, 52 * s, 40 * s], 7), hc, ol, lw)
        # sleeve crease/highlight
        ang = ang_of(el, wr)
        c_, s_ = math.cos(ang), math.sin(ang)
        cuff = (wr[0] - c_ * 6 * s, wr[1] - s_ * 6 * s)
        g.poly([(cuff[0] - s_ * 22 * s, cuff[1] + c_ * 22 * s), (cuff[0] + s_ * 22 * s, cuff[1] - c_ * 22 * s),
                (cuff[0] + s_ * 22 * s + c_ * 12 * s, cuff[1] - c_ * 22 * s + s_ * 12 * s), (cuff[0] - s_ * 22 * s + c_ * 12 * s, cuff[1] + c_ * 22 * s + s_ * 12 * s)], shade(hood, 0.8 * ck), ol, lw * 0.7)
        mode = p.hand_mode[sd]
        ha = ang + p.hand_rot[sd]
        draw_hand(g, wr, ha, s, sk, mode, near=not far, point_ang=p.point_ang, outline=shade(skin, 0.6 * ck), side=sd, flip=1 if math.cos(cam.yaw) >= 0 else -1)
        out[('hand', sd)] = (wr, ha)
        return

    def torso_and_head():
        L, R, cl, psi = torso_poly(g, cam, J, p, s, hood, ol_h)
        # shading: far half
        sgn = 1 if math.sin(psi) >= 0 else -1
        half = R if math.cos(psi) * 0 + 1 else L
        # lighten rim / darker right half
        for i in range(len(cl) - 1):
            pass
        g.poly([cl[0], cl[-1]] + [R[-1], R[0]][:0] + R[::-1][:len(R)], hood_d, a=0)
        g.poly(list(cl) + R[::-1], hood_d, a=70)
        # hem band
        hb = [L[0], R[0], (R[1][0], R[1][1]), (L[1][0], L[1][1])]
        g.poly(hb, shade(hood, 0.8), ol_h, lw * 0.8)
        # front details
        fr = math.cos(psi)
        # pocket (front) / hood (back)
        if fr > 0.2:
            c3 = J['pelvis'] + (J['chest'] - J['pelvis']) * 0.28 + v3(0, 0, 50)
            cx, cy = cam.p(c3)
            wv = 62 * fr * s
            g.poly([(cx - wv, cy - 20 * s), (cx + wv, cy - 20 * s), (cx + wv * 1.15, cy + 42 * s), (cx - wv * 1.15, cy + 42 * s)], shade(hood, 0.88), ol_h, lw * 0.8)
            g.line([(cx - wv * 0.9, cy - 6 * s), (cx - wv * 1.05, cy + 36 * s)], hood_d, 2.2 * s)
            g.line([(cx + wv * 0.9, cy - 6 * s), (cx + wv * 1.05, cy + 36 * s)], hood_d, 2.2 * s)
        # waist fold lines
        mid = cam.p(J['pelvis'] + (J['chest'] - J['pelvis']) * 0.42)
        g.line([(mid[0] - 40 * s * abs(fr) - 14 * s, mid[1]), (mid[0] - 10 * s, mid[1] + 8 * s)], hood_d, 2.4 * s, a=150)
        g.line([(mid[0] + 14 * s, mid[1] + 6 * s), (mid[0] + 44 * s * abs(fr) + 14 * s, mid[1] - 2 * s)], hood_d, 2.4 * s, a=150)
        # hood bunched at collar
        nk = cam.p(J['chest'] + J['spine'] * 6)
        wv = math.sqrt((78 * math.cos(psi)) ** 2 + (52 * math.sin(psi)) ** 2)
        hood_back = fr < 0.15
        g.ell(nk[0], nk[1] - 8 * s, wv * s * 0.95, 34 * s, hood_d if hood_back else shade(hood, 0.7), ol_h, lw, n=22)
        # neck
        hd = cam.p(J['head'])
        nkn = cam.p(J['chest'] + J['spine'] * 20)
        g.poly(stroke_poly([nkn, (nkn[0] * 0.5 + hd[0] * 0.5, nkn[1] * 0.5 + hd[1] * 0.5 + 8 * s)], [46 * s, 42 * s], 3), shade(skin, 0.92), ol_s, lw)
        # drawstrings
        if fr > 0.25:
            ds = cam.p(J['chest'] - J['spine'] * 12 + v3(0, 0, 56))
            for sd_ in (-1, 1):
                ex_ = ds[0] + sd_ * (26 * s) * fr + p.sway * 6 * s
                g.line([(ds[0] + sd_ * 26 * s * fr, ds[1] - 6 * s), (ex_, ds[1] + 62 * s)], (210, 210, 220), 3 * s)
                g.ell(ex_, ds[1] + 64 * s, 3.4 * s, 4 * s, (210, 210, 220), n=8)
        # collar front over neck
        if fr > 0.15:
            g.poly([(nk[0] - wv * s * 0.9, nk[1] - 2 * s), (nk[0], nk[1] + 20 * s), (nk[0] + wv * s * 0.9, nk[1] - 2 * s), (nk[0], nk[1] - 14 * s)], shade(hood, 0.72), ol_h, lw)

    # compose draw order
    order = []
    for sd in (-1, 1):
        order.append((dep[('hip', sd)] + dep[('ankle', sd)], 'leg', sd))
    for sd in (-1, 1):
        order.append((dep[('sh', sd)] + dep[('wrist', sd)], 'arm', sd))
    # far parts first
    legs = sorted([o for o in order if o[1] == 'leg'], key=lambda o: o[0])
    arms = sorted([o for o in order if o[1] == 'arm'], key=lambda o: o[0])
    farm = [a for a in arms if a[0] < -2]
    narm = [a for a in arms if a[0] >= -2]
    for o in farm: arm(o[2])
    for o in legs: leg(o[2])
    pelvis()
    torso_and_head()
    # head
    hdp = cam.p(J['head'])
    tyaw = cam.yaw + p.twist * 0.5 + p.head_yaw
    draw_head(g, hdp, s, tyaw, p.head_pitch, p.head_roll, p.e, p.blink, skin, hair, p.black_eyes, p.mouth_talk, p.sway)
    for o in narm: arm(o[2])
    out['scr'] = scr; out['J'] = J; out['cam'] = cam
    out['head'] = hdp
    return out


def joints_of(p, x0, y0, s):
    cam = Cam(x0, y0, s, p.yaw)
    J = solve(p, cam)
    return {k: cam.p(v) for k, v in J.items() if isinstance(v, np.ndarray) and v.shape == (3,)}, cam
