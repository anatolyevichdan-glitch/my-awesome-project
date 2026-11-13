"""Articulated 2.5D cartoon rig in the PAPA VERNULSYA style (flat vector, big round eyes, pale skin).
Local frame: x = character's left (screen-right when facing camera), y up, z forward (facing). yaw rotates about y;
yaw=0 faces camera, yaw=pi/2 faces screen-right. Units: ~1110 units tall."""
import math
import numpy as np
import skia
from gfx import *

V = lambda *a: np.array(a, dtype=np.float64)

# ---- palette (sampled from the PAPA references)
SKIN = (246, 196, 180)
SKIN_D = (226, 160, 150)
HAIR = (78, 42, 42)
HOOD = (52, 52, 62)
HOOD_D = (34, 34, 42)
HOOD_L = (74, 74, 88)
PANTS = (26, 26, 34)
SHOE = (178, 180, 192)
SOLE = (236, 236, 242)
MOUTH = (96, 28, 40)

# proportions
HIP_Y = 520.0
THIGH, SHIN = 250.0, 215.0
ANKLE_H = 55.0
SPINE = 270.0
NECK_H = 310.0
SH_W = 128.0
HIP_W = 62.0
UP_ARM, LO_ARM = 190.0, 185.0
HEAD_R = 125.0


def nrm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def ik2(a, t, l1, l2, pole):
    d = t - a
    L = np.linalg.norm(d)
    L = max(1e-6, min(L, (l1 + l2) * 0.9995))
    dn = nrm(d)
    x = (L * L + l1 * l1 - l2 * l2) / (2 * L)
    h = math.sqrt(max(l1 * l1 - x * x, 0.0))
    p = pole - dn * np.dot(pole, dn)
    if np.linalg.norm(p) < 1e-6:
        p = V(0, 0, 1) - dn * dn[2]
    p = nrm(p)
    return a + dn * x + p * h, a + dn * L


def rot_y(v, th):
    c, s = math.cos(th), math.sin(th)
    return V(v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)


EXPR = {}


def E(**k):
    base = dict(brow=0.0, tilt=0.0, bend=0.0, browL=None, tiltL=None, lid=0.0, lidlow=0.0, eyew=1.0, pupil=1.0, gx=0.0, gy=0.0,
                mopen=0.0, mw=1.0, smile=0.0, asym=0.0, cheek=0.0, sweat=0.0, tear=0.0, blush=0.0, mround=0.0)
    base.update(k)
    return base


EXPR['neutral'] = E(brow=0.0, mw=0.9, smile=0.05)
EXPR['calm'] = E(brow=-0.05, lid=0.12, mw=0.9, smile=0.12)
EXPR['suspicious'] = E(brow=-0.1, tilt=-0.35, browL=0.25, tiltL=0.15, lid=0.3, lidlow=0.18, eyew=0.95, pupil=0.9, mw=0.8, smile=-0.08, asym=0.25, gx=0.35)
EXPR['worried'] = E(brow=0.3, tilt=0.55, bend=0.1, eyew=1.02, pupil=0.85, mw=0.85, smile=-0.25, mopen=0.06)
EXPR['mild_fear'] = E(brow=0.45, tilt=0.6, eyew=1.08, pupil=0.7, mw=0.85, smile=-0.32, mopen=0.18, sweat=0.4)
EXPR['shock'] = E(brow=0.75, tilt=0.15, eyew=1.2, pupil=0.45, mw=0.55, smile=0.0, mopen=0.65, mround=0.6, sweat=0.3)
EXPR['panic'] = E(brow=0.7, tilt=0.55, eyew=1.18, pupil=0.4, mw=1.0, smile=-0.5, mopen=0.85, sweat=0.9, cheek=0.2)
EXPR['exhausted'] = E(brow=0.15, tilt=0.45, lid=0.42, eyew=0.98, pupil=1.0, mw=0.9, smile=-0.35, mopen=0.4, sweat=0.7, cheek=0.0)
EXPR['terror'] = E(brow=0.85, tilt=0.5, eyew=1.28, pupil=0.32, mw=1.1, smile=-0.45, mopen=1.0, sweat=1.0, mround=0.2)
EXPR['serious'] = E(brow=-0.15, tilt=-0.45, lid=0.2, mw=0.8, smile=-0.1, pupil=0.95)
EXPR['pain'] = E(brow=0.25, tilt=0.8, lid=0.62, eyew=0.9, mw=0.9, smile=-0.45, mopen=0.55)
EXPR['dead'] = E(brow=0.0, lid=0.18, eyew=1.0, pupil=0.0, mw=0.8, smile=0.0)
EXPR['shh'] = E(brow=0.0, lid=0.28, eyew=1.0, pupil=0.85, mw=0.45, smile=0.0, mround=0.9, mopen=0.15)
EXPR['look_up'] = E(brow=0.7, tilt=0.4, eyew=1.25, pupil=0.4, gy=0.9, mw=0.9, smile=-0.3, mopen=0.6)


def lerp_e(a, b, t):
    r = {}
    for k in a:
        va, vb = a[k], b[k]
        if va is None and vb is None:
            r[k] = None
        else:
            va = va if va is not None else a['brow'] if k == 'browL' else a['tilt']
            vb = vb if vb is not None else b['brow'] if k == 'browL' else b['tilt']
            r[k] = va + (vb - va) * t
    return r


def blend(*pairs):
    """blend('neutral', 0.3, 'shock', 0.7) weights normalised"""
    names = pairs[0::2]
    ws = pairs[1::2]
    tot = sum(ws)
    out = {}
    first = EXPR[names[0]]
    for k in first:
        s = 0.0
        for n, w in zip(names, ws):
            v = EXPR[n][k]
            if v is None:
                v = EXPR[n]['brow'] if k == 'browL' else EXPR[n]['tilt']
            s += v * w / tot
        out[k] = s
    return out


class Pose:
    def __init__(self):
        self.yaw = 0.0
        self.pelvis = V(0, 0, 0)
        self.lean = 0.0
        self.roll = 0.0
        self.twist = 0.0
        self.ptwist = 0.0
        self.head_yaw = 0.0
        self.head_pitch = 0.0
        self.head_roll = 0.0
        self.foot = {1: V(HIP_W, ANKLE_H, 0), -1: V(-HIP_W, ANKLE_H, 0)}
        self.foot_pitch = {1: 0.0, -1: 0.0}
        self.foot_yaw = {1: 0.0, -1: 0.0}
        self.hand = {1: V(22, -345, 20), -1: V(-22, -345, 20)}   # chest-local offset from shoulder
        self.hand_abs = {1: None, -1: None}                       # optional absolute local target
        self.elbow_pole = {1: V(0.5, -0.3, -1.0), -1: V(-0.5, -0.3, -1.0)}
        self.hand_mode = {1: 'relaxed', -1: 'relaxed'}
        self.hand_dir = {1: None, -1: None}
        self.sh_up = {1: 0.0, -1: 0.0}
        self.e = EXPR['neutral']
        self.blink = 0.0
        self.black_eyes = False
        self.breath = 0.0
        self.hood_lag = V(0, 0, 0)
        self.hem = 0.0
        self.talk = 0.0
        self.heave = 0.0
        self.holding = None
        self.shake = 0.0

    def copy(self):
        import copy
        return copy.deepcopy(self)


def mirror_pose(p):
    """pose of the reflection in a mirror: swap the sides, flip lateral things"""
    q = p.copy()
    for d in ('foot', 'foot_pitch', 'foot_yaw', 'hand', 'hand_abs', 'elbow_pole', 'hand_mode', 'hand_dir', 'sh_up'):
        dd = getattr(q, d)
        dd[1], dd[-1] = dd[-1], dd[1]
    for d in (q.foot, q.hand, q.elbow_pole):
        for s in (1, -1):
            v = d[s]
            if v is not None:
                d[s] = V(-v[0], v[1], v[2])
    for s in (1, -1):
        if q.hand_abs[s] is not None:
            v = q.hand_abs[s]
            q.hand_abs[s] = V(-v[0], v[1], v[2])
        if q.hand_dir[s] is not None:
            v = q.hand_dir[s]
            q.hand_dir[s] = V(-v[0], v[1], v[2])
    q.foot_yaw = {s: -v for s, v in q.foot_yaw.items()}
    q.roll = -q.roll
    q.twist = -q.twist
    q.ptwist = -q.ptwist
    q.head_roll = -q.head_roll
    q.head_yaw = -q.head_yaw
    e = dict(q.e)
    e['gx'] = -e['gx']
    q.e = e
    return q


# ------------------------------------------------------------------------ skeleton
class Skel:
    pass


def solve(p):
    S = Skel()
    P0 = V(p.pelvis[0], HIP_Y + p.pelvis[1], p.pelvis[2])
    lean = p.lean + 0.012 * math.sin(p.breath * 2 * math.pi)
    u = nrm(V(math.sin(p.roll), math.cos(lean) * math.cos(p.roll), math.sin(lean)))
    r = V(math.cos(p.twist), 0, -math.sin(p.twist))
    r = nrm(r - u * np.dot(r, u))
    f = np.cross(r, u)
    S.u, S.r, S.f = u, r, f
    S.P = P0
    S.chest = P0 + u * (SPINE * 0.55)
    S.S0 = P0 + u * (SPINE + 4 * math.sin(p.breath * 2 * math.pi) + p.heave)
    S.N = P0 + u * (NECK_H + 2 * math.sin(p.breath * 2 * math.pi) + p.heave)
    S.sh = {s: S.S0 + r * (SH_W * s) + u * p.sh_up[s] * 40 for s in (1, -1)}
    pr = V(math.cos(p.ptwist), 0, -math.sin(p.ptwist))
    S.pr = pr
    S.pf = np.cross(pr, V(0, 1, 0))
    S.hip = {s: P0 + pr * (HIP_W * s) for s in (1, -1)}
    S.knee, S.ankle, S.toe, S.heel = {}, {}, {}, {}
    for s in (1, -1):
        ank = V(p.foot[s][0] + p.pelvis[0] * 0, p.foot[s][1], p.foot[s][2])
        # foot target is in "ground" space (x,z relative to origin below pelvis)
        ank = V(p.foot[s][0], p.foot[s][1], p.foot[s][2])
        pole = nrm(S.pf * 1.0 + pr * (0.18 * s) + V(0, 0.15, 0))
        k, a = ik2(S.hip[s], ank, THIGH, SHIN, pole)
        S.knee[s], S.ankle[s] = k, a
        fy, fp = p.foot_yaw[s], p.foot_pitch[s]
        td = V(math.sin(fy) * math.cos(fp), -math.sin(fp), math.cos(fy) * math.cos(fp))
        S.toe[s] = a + td * 100.0 + V(0, -ANKLE_H * 0.55, 0) * math.cos(fp)
        S.heel[s] = a - td * 36.0 + V(0, -ANKLE_H * 0.9, 0)
    S.elbow, S.wrist, S.handc = {}, {}, {}
    for s in (1, -1):
        if p.hand_abs[s] is not None:
            tgt = p.hand_abs[s]
        else:
            h = p.hand[s]
            tgt = S.sh[s] + r * h[0] + u * h[1] + f * h[2]
        pole = r * (0.6 * s) * p.elbow_pole[s][0] / 0.5 * 0.5 + f * p.elbow_pole[s][2] + u * p.elbow_pole[s][1]
        pole = nrm(r * (p.elbow_pole[s][0]) + u * p.elbow_pole[s][1] + f * p.elbow_pole[s][2])
        e_, w_ = ik2(S.sh[s], tgt, UP_ARM, LO_ARM, pole)
        S.elbow[s], S.wrist[s] = e_, w_
        d = nrm(w_ - e_)
        if p.hand_dir[s] is not None:
            d = nrm(p.hand_dir[s])
        S.handc[s] = w_ + d * 34.0
        S.hdir = getattr(S, 'hdir', {})
        S.hdir[s] = d
    # head
    hy, hp, hr = p.head_yaw, p.head_pitch, p.head_roll
    # head frame from chest frame
    hr_v = r * math.cos(hy) - f * math.sin(hy)
    hf_v = f * math.cos(hy) + r * math.sin(hy)
    hu_v = u
    # pitch (look down +): rotate f toward -u
    hf2 = hf_v * math.cos(hp) - hu_v * math.sin(hp)
    hu2 = hu_v * math.cos(hp) + hf_v * math.sin(hp)
    # roll about hf
    hr2 = hr_v * math.cos(hr) + hu2 * math.sin(hr)
    hu3 = hu2 * math.cos(hr) - hr_v * math.sin(hr)
    S.hr, S.hu, S.hf = nrm(hr2), nrm(hu3), nrm(hf2)
    S.H = S.N + S.hu * (HEAD_R * 0.92 + 30) + S.hf * 8
    return S


# ------------------------------------------------------------------------ projection
class Cam:
    def __init__(self, x0, y0, s, yaw=0.0, pitch=0.14, persp=0.0, flip=False):
        self.x0, self.y0, self.s, self.yaw, self.pitch, self.persp = x0, y0, s, yaw, pitch, persp
        self.cp, self.sp = math.cos(pitch), math.sin(pitch)
        self.flip = flip

    def world(self, v):
        w = rot_y(v, self.yaw)
        return w

    def proj(self, v):
        w = rot_y(v, self.yaw)
        y = w[1] * self.cp - w[2] * self.sp
        d = w[2] * self.cp + w[1] * self.sp
        k = self.s * (1.0 + self.persp * d / 1000.0)
        x = w[0]
        if self.flip:
            x = -x
        return (self.x0 + x * k, self.y0 - y * k), d, k

    def dirproj(self, v):
        """projection of a direction vector -> (dx_screen, dy_screen, depth)"""
        w = rot_y(v, self.yaw)
        y = w[1] * self.cp - w[2] * self.sp
        d = w[2] * self.cp + w[1] * self.sp
        x = -w[0] if self.flip else w[0]
        return x, -y, d


def lit_shader(a, b, c0, c1):
    return lin(a, b, c0, c1)


def tube(canvas, pa, pb, ra, rb, col, dcol, light=(-0.6, -0.8), alpha=1.0):
    path = capsule_path(pa, pb, ra, rb)
    mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
    dx, dy = pb[0] - pa[0], pb[1] - pa[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    if nx * light[0] + ny * light[1] < 0:
        nx, ny = -nx, -ny
    rr = max(ra, rb)
    sh = lin((mx + nx * rr, my + ny * rr), (mx - nx * rr, my - ny * rr), mix(col, (255, 255, 255), 0.06), dcol)
    canvas.drawPath(path, P(shader=sh))
    return path


def draw_hero(cv, p, X0, Y0, s, yaw=None, cam_pitch=0.14, persp=0.0, tint=None, light=(-0.6, -0.8), expr_scale=1.0,
              ground_shadow=0.0, hood_col=HOOD, mask_cv=None, flip=False, skin=SKIN, hair=HAIR, pants=PANTS, shoe=SHOE, parts_only=False):
    """draws hero; returns dict with anchors (screen coords)"""
    cam = Cam(X0, Y0, s, p.yaw if yaw is None else yaw, cam_pitch, persp, flip)
    S = solve(p)
    A = {}
    pr = cam.proj

    def T(c):
        if tint is None:
            return c
        return tuple(max(0, min(255, c[i] * tint[i])) for i in range(3))

    skin_c, skin_d = T(skin), T(SKIN_D)
    hood_c, hood_d, hood_l = T(hood_col), T(HOOD_D), T(HOOD_L)
    pants_c, pants_d = T(pants), T(shade(pants, 0.7))
    parts = []

    # ground shadow
    if ground_shadow > 0:
        gp, _, k = pr(V(S.P[0] * 0 + (p.foot[1][0] + p.foot[-1][0]) / 2, 0, (p.foot[1][2] + p.foot[-1][2]) / 2))
        cv.drawOval(skia.Rect(gp[0] - 190 * s, gp[1] - 30 * s, gp[0] + 190 * s, gp[1] + 40 * s), P((0, 0, 8), ground_shadow, blur=18 * s))

    # ---- legs
    for sd in (1, -1):
        hp_, dh, _ = pr(S.hip[sd])
        kp_, dk, _ = pr(S.knee[sd])
        ap_, da, _ = pr(S.ankle[sd])
        zl = (dh + dk + da) / 3

        def leg(sd=sd, hp_=hp_, kp_=kp_, ap_=ap_):
            tube(cv, hp_, kp_, 50 * s, 40 * s, pants_c, pants_d, light)
            tube(cv, kp_, ap_, 40 * s, 31 * s, pants_c, pants_d, light)
            # shoe
            fy, fpt = p.foot_yaw[sd], p.foot_pitch[sd]
            td = V(math.sin(fy) * math.cos(fpt), -math.sin(fpt), math.cos(fpt) * math.cos(fy))
            lat = V(math.cos(fy), 0, -math.sin(fy))
            a3 = S.ankle[sd]
            pts3 = []
            for tz, ty, w in ((105, -ANKLE_H * 0.55, 34), (105, -ANKLE_H * 0.55, -34), (-38, -ANKLE_H * 0.9, 32), (-38, -ANKLE_H * 0.9, -32),
                              (40, 22, 30), (40, 22, -30), (-20, 18, 28), (-20, 18, -28)):
                q = a3 + td * tz + V(0, ty, 0) + lat * w
                pts3.append(pr(q)[0])
            # sole: same hull offset down
            sole = [(x, y + 10 * s) for x, y in hull(pts3)]
            cv.drawPath(path_poly(sole), P(T(SOLE)))
            hh = hull(pts3)
            shp = path_smooth(hh, tension=0.35) if len(hh) > 3 else path_poly(hh)
            cv.drawPath(path_poly(hh), P(shader=lin((hh[0][0], min(y for _, y in hh)), (hh[0][0], max(y for _, y in hh)), T(mix(shoe, (255, 255, 255), 0.12)), T(shade(shoe, 0.78)))))
            # laces tick
            tpt = pr(a3 + td * 40 + V(0, 22, 0))[0]
            cv.drawCircle(tpt[0], tpt[1], 5 * s, P(T(shade(shoe, 0.6)), 0.7))

        parts.append((zl - 5, leg))

    # ---- pelvis block / trousers hips
    pel = []
    for sx in (1, -1):
        for yy in (HIP_Y - 60, HIP_Y + 25):
            for zz in (1, -1):
                q = S.P + S.pr * (sx * 96) + V(0, yy - HIP_Y, 0) + S.pf * (zz * 66)
                pel.append(pr(q)[0])
    pz = pr(S.P)[1]
    parts.append((pz - 30, lambda: cv.drawPath(path_poly(hull(pel)), P(shader=lin(pel[0], pel[-1], pants_c, pants_d)))))

    # ---- torso (hoodie)
    tor = []
    sway = p.hem
    for (yy, wx, dz) in ((0, 104, 74), (SPINE * 0.35, 104, 74), (SPINE * 0.78, 122, 72), (SPINE * 1.02, 128, 68)):
        base = S.P + S.u * yy
        for sx in (1, -1):
            for zz in (1, -1):
                q = base + S.r * (sx * wx) + S.f * (zz * dz) * (0.92 if yy > SPINE else 1.0)
                if yy == 0:
                    q = q + V(sway * 6 * zz, -26, 0)
                tor.append(pr(q)[0])
    torso_z = pr(S.chest)[1]
    tpath = path_smooth(hull(tor), tension=0.35)
    # front-facing amount for details
    fdir = cam.dirproj(S.f)
    facing = fdir[2]            # >0 front visible
    rdir = cam.dirproj(S.r)

    def torso():
        cs = pr(S.chest)[0]
        top = pr(S.P + S.u * SPINE)[0]
        bot = pr(S.P)[0]
        cv.drawPath(tpath, P(shader=lin(top, bot, T(mix(hood_col, (255, 255, 255), 0.05)), hood_d)))
        # side shade
        bb = tpath.getBounds()
        cv.save()
        cv.clipPath(tpath, doAntiAlias=True)
        lx, ly = light
        shx = bb.centerX() + (-lx) * bb.width() * 0.5
        cv.drawRect(skia.Rect(bb.left(), bb.top(), bb.right(), bb.bottom()), P(shader=lin((bb.centerX() + lx * bb.width() * 0.2, bb.centerY()), (shx, bb.centerY()), (0, 0, 0), (0, 0, 0), 0.0, 0.32)))
        # hem rib
        hemy = pr(S.P + S.u * 28)[0]
        cv.drawPath(path_poly([(bb.left(), hemy[1] - 14 * s), (bb.right(), hemy[1] - 14 * s), (bb.right(), bb.bottom()), (bb.left(), bb.bottom())]), P(hood_d, 0.55))
        if facing > 0.2:
            a = min(1.0, (facing - 0.2) / 0.5)
            # kangaroo pocket + drawstrings
            pc = pr(S.P + S.u * 85 + S.f * 82)[0]
            rx = rdir[0] * 80 * s
            cv.drawPath(path_smooth([(pc[0] - 82 * s * abs(rdir[0] if abs(rdir[0]) > .3 else 1) - 0, pc[1] - 8 * s), (pc[0], pc[1] + 6 * s), (pc[0] + 82 * s * abs(rdir[0] if abs(rdir[0]) > .3 else 1), pc[1] - 8 * s)], close=False),
                        P(hood_l, 0.55 * a, style='stroke', width=3.2 * s))
            # centre seam
            n0 = pr(S.P + S.u * (SPINE * 0.95) + S.f * 76)[0]
            n1 = pr(S.P + S.u * 105 + S.f * 82)[0]
            cv.drawLine(n0[0], n0[1], n1[0], n1[1], P(hood_l, 0.35 * a, style='stroke', width=2.5 * s))
        cv.restore()
        if facing > 0.15:
            a = min(1.0, (facing - 0.15) / 0.5)
            # neckline + drawstrings
            nb = pr(S.N + S.f * 62 - S.u * 14)[0]
            for sx in (1, -1):
                q0 = pr(S.N - S.u * 16 + S.f * 70 + S.r * sx * 28)[0]
                q1 = pr(S.N - S.u * 120 + S.f * 82 + S.r * sx * 24 + V(0, 0, 0))[0]
                cv.drawPath(path_smooth([q0, ((q0[0] + q1[0]) / 2 + sx * 3 * s, (q0[1] + q1[1]) / 2), q1], close=False), P(hood_l, 0.75 * a, style='stroke', width=3.5 * s))
                cv.drawCircle(q1[0], q1[1], 4.4 * s, P(hood_l, 0.9 * a))

    parts.append((torso_z, torso))

    # ---- hood bundle (behind the neck), collar ring
    hb = pr(S.N - S.f * 30 - S.u * 18 + p.hood_lag)[0]
    hbz = pr(S.N - S.f * 60)[1]

    def hood_back():
        cv.drawPath(path_smooth([(hb[0] - 92 * s, hb[1] + 4 * s), (hb[0] - 70 * s, hb[1] - 38 * s), (hb[0] + 70 * s, hb[1] - 38 * s), (hb[0] + 92 * s, hb[1] + 4 * s),
                                 (hb[0] + 60 * s, hb[1] + 46 * s), (hb[0] - 60 * s, hb[1] + 46 * s)], tension=0.5),
                    P(shader=lin((hb[0], hb[1] - 40 * s), (hb[0], hb[1] + 46 * s), hood_c, hood_d)))
    parts.append((min(torso_z, hbz) - 4, hood_back))

    # collar front ring
    def collar():
        c = pr(S.N - S.u * 8 + S.f * 10)[0]
        wd = 64 * s * (abs(rdir[0]) * 0.5 + 0.5)
        cv.drawPath(path_smooth([(c[0] - wd * 1.55, c[1] + 4 * s), (c[0] - wd * 0.8, c[1] - 24 * s), (c[0] + wd * 0.8, c[1] - 24 * s), (c[0] + wd * 1.55, c[1] + 4 * s),
                                 (c[0] + wd * 0.8, c[1] + 34 * s), (c[0] - wd * 0.8, c[1] + 34 * s)], tension=0.5),
                    P(shader=lin((c[0], c[1] - 24 * s), (c[0], c[1] + 34 * s), hood_l, hood_c)))
    parts.append((torso_z + 8, collar))

    # ---- arms
    for sd in (1, -1):
        sp_, dsh, _ = pr(S.sh[sd])
        ep_, dep, _ = pr(S.elbow[sd])
        wp_, dwr, _ = pr(S.wrist[sd])
        hp3, dhd, _ = pr(S.handc[sd])
        za = (dsh + dep + dwr) / 3 + (6 if sd == 1 else -6) * 0
        bias = 0.0

        def arm(sd=sd, sp_=sp_, ep_=ep_, wp_=wp_, hp3=hp3):
            tube(cv, sp_, ep_, 35 * s, 29 * s, hood_c, hood_d, light)
            tube(cv, ep_, wp_, 29 * s, 24 * s, hood_c, hood_d, light)
            # sleeve cuff
            d = (wp_[0] - ep_[0], wp_[1] - ep_[1])
            L = math.hypot(*d) or 1
            ux, uy = d[0] / L, d[1] / L
            c0 = (wp_[0] - ux * 14 * s, wp_[1] - uy * 14 * s)
            cv.drawLine(c0[0], c0[1], wp_[0] + ux * 3 * s, wp_[1] + uy * 3 * s, P(hood_d, 0.9, style='stroke', width=26 * s))
            # shoulder cap
            cv.drawCircle(sp_[0], sp_[1], 36 * s, P(hood_c))
            draw_hand(cv, S, p, sd, cam, s, skin_c, skin_d, light)

        parts.append((za + 4, arm))

    # ---- neck
    npos = pr(S.N)[0]
    hpos = pr(S.H)[0]
    nz_ = pr(S.N)[1]

    def neck():
        tube(cv, npos, (npos[0] + (hpos[0] - npos[0]) * 0.6, npos[1] + (hpos[1] - npos[1]) * 0.6), 34 * s, 33 * s, skin_c, skin_d, light)
        # chin shadow
    parts.append((nz_ - 2, neck))

    # ---- head
    hz = pr(S.H)[1] + 40
    parts.append((hz, lambda: draw_head(cv, S, p, cam, s, skin_c, skin_d, T(hair), light, tint, expr_scale, A)))

    parts.sort(key=lambda t: t[0])
    for _, fn in parts:
        fn()
    A['head'] = pr(S.H)[0]
    A['chest'] = pr(S.chest)[0]
    A['hand'] = {sd: pr(S.handc[sd])[0] for sd in (1, -1)}
    A['wrist'] = {sd: pr(S.wrist[sd])[0] for sd in (1, -1)}
    A['pelvis'] = pr(S.P)[0]
    A['feet'] = {sd: pr(S.ankle[sd])[0] for sd in (1, -1)}
    A['skel'] = S
    A['cam'] = cam
    A['mouth'] = A.get('mouth', pr(S.H)[0])
    return A


def draw_hand(cv, S, p, sd, cam, s, skin_c, skin_d, light):
    mode = p.hand_mode[sd]
    wp = S.wrist[sd]
    d = S.hdir[sd]
    hp, _, _ = cam.proj(S.handc[sd])
    w2, _, _ = cam.proj(wp)
    dx, dy = hp[0] - w2[0], hp[1] - w2[1]
    L = math.hypot(dx, dy)
    if L < 1e-3:
        dx, dy = 0.0, 1.0
        L = 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    outward = 1 if sd == 1 else -1
    # thumb side: toward body
    ts = -1.0 if (nx * outward > 0) else 1.0
    ts = ts * (1 if sd == 1 else -1) * -1 if False else ts
    r = 30 * s
    if mode in ('fist', 'phone', 'grip'):
        cv.drawCircle(hp[0], hp[1], 37 * s, P(shader=lin((hp[0], hp[1] - 37 * s), (hp[0], hp[1] + 37 * s), skin_c, skin_d)))
        # finger lines
        for k in (-1, 0, 1):
            q = (hp[0] + nx * k * 12 * s + ux * 12 * s, hp[1] + ny * k * 12 * s + uy * 12 * s)
            cv.drawCircle(q[0], q[1], 3 * s, P(skin_d, 0.8))
        tp = (hp[0] - nx * 22 * s * ts * -1 + ux * 8 * s, hp[1] - ny * 22 * s * ts * -1 + uy * 8 * s)
        cv.drawPath(capsule_path((hp[0] + ux * 4 * s, hp[1] + uy * 4 * s), tp, 12 * s, 10 * s), P(skin_c))
        return
    if mode == 'point':
        cv.drawCircle(hp[0], hp[1], 34 * s, P(shader=lin((hp[0], hp[1] - 37 * s), (hp[0], hp[1] + 37 * s), skin_c, skin_d)))
        tip = (hp[0] + ux * 92 * s, hp[1] + uy * 92 * s)
        cv.drawPath(capsule_path((hp[0] + ux * 10 * s, hp[1] + uy * 10 * s), tip, 12.5 * s, 10 * s), P(skin_c))
        cv.drawCircle(tip[0], tip[1], 10 * s, P(mix(skin_c, (255, 255, 255), 0.04)))
        tp = (hp[0] - nx * 18 * s * ts * -1 + ux * 8 * s, hp[1] - ny * 18 * s * ts * -1 + uy * 8 * s)
        cv.drawPath(capsule_path((hp[0] + ux * 2 * s, hp[1] + uy * 2 * s), tp, 11 * s, 9 * s), P(skin_c))
        return
    if mode == 'open':
        base = (hp[0] - ux * 6 * s, hp[1] - uy * 6 * s)
        for k, ang in enumerate((-0.42, -0.16, 0.12, 0.38)):
            ca, sa = math.cos(ang), math.sin(ang)
            fx, fy = ux * ca - uy * sa, ux * sa + uy * ca
            ln = (62 - abs(k - 1.5) * 4) * s
            cv.drawPath(capsule_path((base[0] + fx * 16 * s, base[1] + fy * 16 * s), (base[0] + fx * ln, base[1] + fy * ln), 11 * s, 9 * s), P(skin_c))
        cv.drawCircle(hp[0], hp[1], 33 * s, P(shader=lin((hp[0], hp[1] - 37 * s), (hp[0], hp[1] + 37 * s), skin_c, skin_d)))
        tp = (hp[0] - nx * 40 * s * ts * -1 + ux * 22 * s, hp[1] - ny * 40 * s * ts * -1 + uy * 22 * s)
        cv.drawPath(capsule_path((hp[0] - nx * 14 * s * ts * -1, hp[1] - ny * 14 * s * ts * -1), tp, 11 * s, 9 * s), P(skin_c))
        return
    # relaxed / default: soft mitten with thumb
    base = (hp[0] + ux * 16 * s, hp[1] + uy * 16 * s)
    cv.drawPath(capsule_path((hp[0] - ux * 6 * s, hp[1] - uy * 6 * s), (hp[0] + ux * 30 * s, hp[1] + uy * 30 * s), 31 * s, 23 * s),
                P(shader=lin((hp[0] - nx * 30 * s, hp[1] - ny * 30 * s), (hp[0] + nx * 30 * s, hp[1] + ny * 30 * s), skin_c, skin_d)))
    for k in (-1, 0, 1):
        q = (base[0] + nx * k * 12 * s + ux * 16 * s, base[1] + ny * k * 12 * s + uy * 16 * s)
        cv.drawLine(q[0], q[1], q[0] - ux * 14 * s, q[1] - uy * 14 * s, P(skin_d, 0.55, style='stroke', width=2.2 * s))
    tp = (hp[0] - nx * 25 * s * ts * -1 + ux * 16 * s, hp[1] - ny * 25 * s * ts * -1 + uy * 16 * s)
    cv.drawPath(capsule_path((hp[0] - nx * 10 * s * ts * -1 - ux * 2 * s, hp[1] - ny * 10 * s * ts * -1 - uy * 2 * s), tp, 12 * s, 9 * s), P(skin_c))


# ------------------------------------------------------------------------ head
def sph(S, phi, lat, R=1.0):
    """point on head sphere (local head frame) -> 3D vector from centre; plus tangent vectors"""
    cl, sl = math.cos(lat), math.sin(lat)
    cp, sp = math.cos(phi), math.sin(phi)
    n = S.hr * (sp * cl) + S.hu * sl + S.hf * (cp * cl)
    tr = S.hr * cp - S.hf * sp                     # d/dphi
    tu = -S.hr * (sp * sl) + S.hu * cl - S.hf * (cp * sl)   # d/dlat
    return n * R, nrm(n), nrm(tr), nrm(tu)


def draw_head(cv, S, p, cam, s, skin_c, skin_d, hair_c, light, tint, es, A):
    e = p.e
    R = HEAD_R
    Hc, dH, k0 = cam.proj(S.H)
    RX, RY = R * 0.98 * s, R * 1.04 * s

    def proj_pt(phi, lat, rr=1.0):
        v, n, tr, tu = sph(S, phi, lat, R * rr)
        pp, d, _ = cam.proj(S.H + v)
        nx, ny, nz = cam.dirproj(n)
        return pp, nz, n, tr, tu

    def sil(pp, nz):
        dx, dy = pp[0] - Hc[0], pp[1] - Hc[1]
        if nz < 0:
            L = math.hypot(dx, dy) or 1
            f = 0.995 * R * s / L
            # push to silhouette ellipse
            ang = math.atan2(dy, dx)
            return (Hc[0] + math.cos(ang) * RX * 0.995, Hc[1] + math.sin(ang) * RY * 0.995)
        return (Hc[0] + (pp[0] - Hc[0]) * 0.98, Hc[1] + (pp[1] - Hc[1]) * 1.04)

    # skin base: full head ellipse
    hu2 = cam.dirproj(S.hu)
    cv.drawOval(skia.Rect(Hc[0] - RX, Hc[1] - RY, Hc[0] + RX, Hc[1] + RY),
                P(shader=lin((Hc[0] + light[0] * RX, Hc[1] + light[1] * RY), (Hc[0] - light[0] * RX, Hc[1] - light[1] * RY), mix(skin_c, (255, 255, 255), 0.05), skin_d)))

    def ear_draw(sd):
        pp, nz, n, tr, tu = proj_pt(sd * 1.5708, -0.1, 1.0)
        er = R * 0.2 * s
        if abs(nz) < 0.93:
            cv.drawOval(skia.Rect(pp[0] - er * 0.7, pp[1] - er * 1.1, pp[0] + er * 0.7, pp[1] + er * 1.1), P(skin_c))
            cv.drawOval(skia.Rect(pp[0] - er * 0.35, pp[1] - er * 0.6, pp[0] + er * 0.35, pp[1] + er * 0.6), P(skin_d, 0.6))
        return nz
    nzs = {}
    for sd in (1, -1):
        pp, nz, *_ = proj_pt(sd * 1.5708, -0.1, 1.0)
        nzs[sd] = nz
        if nz < -0.3:
            ear_draw(sd)
    # hair cap made of sphere quads (visible ones) -> exact occlusion for every yaw
    def lat_h(phi):
        a = abs((phi + math.pi) % (2 * math.pi) - math.pi)
        if a <= 1.9:
            return math.radians(37 + 4.5 * math.sin(5.3 * phi + 0.5) + 3 * math.sin(11 * phi) - 17 * a / 1.9 - 12 * max(0.0, a - 1.2))
        k = min(1.0, (a - 1.9) / 0.7)
        return (0.29 + (-0.62 - 0.29) * k) + 0.05 * math.sin(7 * phi)
    cols = []
    ph = -1.9
    while ph < 1.9 + 1e-6:
        cols.append(ph); ph += 0.085
    ph = 1.9
    back = []
    while ph < 2 * math.pi - 1.9 + 1e-6:
        back.append(ph); ph += 0.2
    cols = cols + back[1:]
    hp_ = skia.Path()
    NSUB = 5
    RH = 1.05

    def pt(phi, lat):
        v, n, tr, tu = sph(S, phi, lat, R * RH)
        pp, d, _ = cam.proj(S.H + v)
        nz = cam.dirproj(n)[2]
        return ((Hc[0] + (pp[0] - Hc[0]) * 0.98, Hc[1] + (pp[1] - Hc[1]) * 1.04)), nz
    for a_, b_ in zip(cols[:-1], cols[1:]):
        la, lb = lat_h(a_), lat_h(b_)
        for k in range(NSUB):
            t0, t1 = k / NSUB, (k + 1) / NSUB
            q = []
            nzsum = 0.0
            for (phi, lh, t) in ((a_, la, t0), (b_, lb, t0), (b_, lb, t1), (a_, la, t1)):
                lat = lh + (1.5708 - lh) * t
                p2, nz = pt(phi, lat)
                q.append(p2); nzsum += nz
            if nzsum / 4 > -0.02:
                hp_.moveTo(*q[0]); hp_.lineTo(*q[1]); hp_.lineTo(*q[2]); hp_.lineTo(*q[3]); hp_.close()
    hp_.setFillType(skia.PathFillType.kWinding)
    hair_sh = lin((Hc[0], Hc[1] - RY * 1.05), (Hc[0], Hc[1] + RY * 0.7), mix(hair_c, (255, 255, 255), 0.10), shade(hair_c, 0.72))
    cv.drawPath(hp_, P(shader=hair_sh))
    # a few tufts on top
    for (ph_, sc) in ((-0.55, 0.26), (-0.1, 0.32), (0.4, 0.3), (0.95, 0.22), (2.9, 0.3), (-2.6, 0.27)):
        pp2, nz2 = pt(ph_, 1.26)
        if nz2 > -0.35:
            cv.drawCircle(pp2[0], pp2[1], R * sc * 0.5 * s, P(hair_c))
    for sd in (1, -1):
        if nzs[sd] >= -0.3:
            ear_draw(sd)
    # features
    ex = lambda k: e[k]
    eyes_visible = False
    blink = p.blink
    lidc = max(0.0, min(1.0, e['lid'] + blink * (1 - e['lid'])))
    for sd in (1, -1):
        phi, lat = sd * 0.44, 0.0
        pp, nz, n, tr, tu = proj_pt(phi, lat, 1.0)
        if nz < 0.08:
            continue
        a_r = cam.dirproj(tr)
        a_u = cam.dirproj(tu)
        ew, eh = 0.30 * R * s * e['eyew'], 0.345 * R * s * (1.0 + (e['eyew'] - 1) * 0.5)
        M = mat(a_r[0] * 1.0, a_r[1] * 1.0, a_u[0], a_u[1], pp[0], pp[1])
        cv.save()
        cv.concat(M)
        eye_path = ellipse_path(0, 0, ew, eh)
        cv.save()
        cv.clipPath(eye_path, doAntiAlias=True)
        if p.black_eyes:
            cv.drawPaint(P((6, 6, 10)))
            cv.drawOval(skia.Rect(-ew * 0.5, -eh * 0.65, ew * 0.1, -eh * 0.2), P((90, 100, 130), 0.25, blur=2))
        else:
            cv.drawPaint(P(shader=lin((0, -eh), (0, eh), (252, 252, 255), (214, 218, 232))))
            gx, gy = e['gx'], e['gy']
            pr_ = 0.115 * R * s * e['pupil'] * 1.0
            pr_ = max(pr_, 3.0 * s)
            px_, py_ = gx * (ew - pr_ * 1.1), -gy * (eh - pr_ * 1.1) * 0.9
            cv.drawCircle(px_, py_, pr_, P((12, 10, 16)))
            cv.drawCircle(px_ - pr_ * 0.35, py_ - pr_ * 0.38, pr_ * 0.27, P((255, 255, 255), 0.85))
        # lids
        top = -eh * 1.2 + lidc * (eh * 2.0)
        cv.drawRect(skia.Rect(-ew * 1.3, -eh * 1.4, ew * 1.3, top), P(skin_c))
        if lidc > 0.05:
            cv.drawLine(-ew * 1.2, top, ew * 1.2, top, P(shade(skin_d, 0.75), 0.9, style='stroke', width=2.6 * s))
        if e['lidlow'] > 0.02:
            bot = eh * 1.2 - e['lidlow'] * eh * 1.2
            cv.drawRect(skia.Rect(-ew * 1.3, bot, ew * 1.3, eh * 1.4), P(skin_c))
        cv.restore()
        # eye outline (very thin, soft)
        cv.drawPath(eye_path, P(shade(skin_d, 0.6), 0.5, style='stroke', width=1.8 * s))
        cv.restore()
    # brows
    for sd in (1, -1):
        phi, lat = sd * 0.45, 0.50
        pp, nz, n, tr, tu = proj_pt(phi, lat, 1.0)
        if nz < 0.05:
            continue
        a_r = cam.dirproj(tr)
        a_u = cam.dirproj(tu)
        side_brow = e['brow'] if (sd == 1 or e['browL'] is None) else e['browL']
        side_tilt = e['tilt'] if (sd == 1 or e['tiltL'] is None) else e['tiltL']
        M = mat(a_r[0], a_r[1], a_u[0], a_u[1], pp[0], pp[1])
        cv.save()
        cv.concat(M)
        rr = R * s
        y0 = -0.04 * rr - side_brow * 0.30 * rr
        w = 0.26 * rr
        # inner end is toward centre (x = -sd*w). tilt>0: inner end up
        yin = y0 - side_tilt * 0.22 * rr
        yout = y0 + side_tilt * 0.12 * rr
        mid = y0 - 0.10 * rr - e['bend'] * 0.05 * rr - abs(side_tilt) * 0.0
        pth = skia.Path()
        pth.moveTo(-sd * w, yin)
        pth.quadTo(0, mid - 0.02 * rr, sd * w, yout)
        cv.drawPath(pth, P(shade(hair_c, 0.78), 1.0, style='stroke', width=0.064 * rr, cap=skia.Paint.kRound_Cap))
        cv.restore()
    # nose
    pp, nz, n, tr, tu = proj_pt(0.0, -0.28, 1.0)
    npp, nnz, *_ = proj_pt(0.0, -0.28, 1.12)
    if nnz > -0.2:
        a_r = cam.dirproj(tr)
        a_u = cam.dirproj(tu)
        M = mat(a_r[0], a_r[1], a_u[0], a_u[1], npp[0], npp[1])
        cv.save()
        cv.concat(M)
        rr = R * s
        cv.drawOval(skia.Rect(-0.1 * rr, -0.11 * rr, 0.1 * rr, 0.09 * rr), P(shader=lin((0, -0.1 * rr), (0, 0.1 * rr), mix(skin_c, (255, 255, 255), 0.05), mix(skin_d, (180, 110, 110), 0.3))))
        cv.restore()
    # cheeks
    if e['cheek'] > 0.01 or e['blush'] > 0.01:
        for sd in (1, -1):
            pp, nz, n, tr, tu = proj_pt(sd * 0.72, -0.28, 1.0)
            if nz > 0.1:
                cv.drawCircle(pp[0], pp[1], 0.17 * R * s * nz, P((240, 110, 120), 0.35 * max(e['cheek'], e['blush'])))
    # mouth
    pp, nz, n, tr, tu = proj_pt(0.0, -0.66, 1.0)
    A['mouth'] = pp
    if nz > 0.08:
        a_r = cam.dirproj(tr)
        a_u = cam.dirproj(tu)
        M = mat(a_r[0], a_r[1], a_u[0], a_u[1], pp[0], pp[1])
        cv.save()
        cv.concat(M)
        rr = R * s
        mo = max(0.0, min(1.0, e['mopen'] + p.talk * 0.55))
        w = 0.24 * rr * e['mw'] * (1 - 0.45 * e['mround'])
        sm = e['smile']
        asym = e['asym']
        wl, wr = -w, w
        yl = -sm * 0.10 * rr + asym * 0.05 * rr
        yr = -sm * 0.10 * rr - asym * 0.05 * rr
        mid_y = sm * 0.09 * rr
        if mo < 0.05:
            pth = skia.Path()
            pth.moveTo(wl, yl)
            pth.quadTo(0, mid_y * 1.2 + (yl + yr) / 2 * 0.0, wr, yr)
            cv.drawPath(pth, P(shade(skin_d, 0.55), 0.95, style='stroke', width=0.052 * rr))
        else:
            hh = mo * 0.28 * rr * (1 + 0.3 * e['mround'])
            pth = skia.Path()
            pth.moveTo(wl, yl)
            pth.quadTo(0, mid_y - 0.02 * rr, wr, yr)
            pth.quadTo(wr * 0.9, yr + hh * 0.9, 0, yr + hh * 1.0 + mid_y * 0.2)
            pth.quadTo(wl * 0.9, yl + hh * 0.9, wl, yl)
            pth.close()
            cv.drawPath(pth, P(MOUTH))
            cv.save()
            cv.clipPath(pth, doAntiAlias=True)
            cv.drawOval(skia.Rect(-w * 0.6, yl + hh * 0.55, w * 0.6, yl + hh * 1.4), P((196, 84, 96), 0.9))
            if mo > 0.35 and e['mround'] < 0.5:
                cv.drawRect(skia.Rect(-w * 0.8, yl - 0.02 * rr, w * 0.8, yl + hh * 0.22), P((245, 240, 240), 0.95))
            cv.restore()
        cv.restore()
    # sweat
    if e['sweat'] > 0.05:
        pp, nz, n, tr, tu = proj_pt(-0.95 if cam.dirproj(S.hr)[0] > 0 else 0.95, 0.75, 1.0)
        if nz > 0.1:
            sz = 0.09 * R * s * e['sweat']
            dp = skia.Path()
            dp.moveTo(pp[0], pp[1] - sz * 1.5)
            dp.quadTo(pp[0] + sz * 1.1, pp[1] + sz * 0.4, pp[0], pp[1] + sz * 1.2)
            dp.quadTo(pp[0] - sz * 1.1, pp[1] + sz * 0.4, pp[0], pp[1] - sz * 1.5)
            cv.drawPath(dp, P((200, 225, 255), 0.85))
