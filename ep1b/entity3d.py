"""Creature rig: tall hunched digitigrade shadow-figure with extra-long jointed arms, built on the same 3D/yaw projection as char2."""
import math
import numpy as np
from char2 import Cam, ik3, stroke_poly, rot_x, rot_y, v3, shade, hull, lerp, ang_of

BODY = (10, 9, 15)
BODY2 = (20, 18, 28)
RIM = (74, 66, 118)

PELV = 800.0
SPINE = 520.0
THI = 390.0
SHI = 410.0
FOOT_L = 170.0
ARM1 = 340.0
ARM2 = 380.0
SHW = 120.0
HIPW = 60.0


class CPose:
    def __init__(self, **kw):
        self.yaw = 0.0
        self.hip = (0.0, 0.0, 0.0)
        self.lean = 0.38
        self.roll = 0.0
        self.twist = 0.0
        self.neck_pitch = 0.5      # head forward droop
        self.head_yaw = 0.0
        self.head_roll = 0.0
        self.foot = {-1: (-HIPW, 150.0, 0.0), 1: (HIPW, 150.0, 0.0)}
        self.hand = {-1: None, 1: None}
        self.curl = 0.5            # finger curl 0 open .. 1 fist
        self.sway = 0.0
        self.mouth = 0.0           # 0..1 jaw opening
        self.eyes = 1.0
        self.arm_scale = 1.0
        self.__dict__.update(kw)


def csolve(p):
    J = {}
    P = v3(0, PELV, 0) + v3(*p.hip)
    J['pelvis'] = P
    sp = v3(math.sin(p.roll), math.cos(p.lean) * math.cos(p.roll), math.sin(p.lean))
    sp = sp / np.linalg.norm(sp)
    C = P + sp * SPINE
    J['chest'] = C; J['spine'] = sp
    ax = rot_y(v3(1, 0, 0), p.twist)
    J['axis'] = ax
    for sd in (-1, 1):
        J[('sh', sd)] = C - sp * 50 + ax * (sd * SHW)
        J[('hip', sd)] = P + v3(sd * HIPW, 0, 0)
        f = v3(*p.foot[sd])
        j, e = ik3(J[('hip', sd)], f, THI, SHI, (0, 0, -1.0))
        J[('knee', sd)] = j; J[('ankle', sd)] = e
        tgt = p.hand[sd]
        S = J[('sh', sd)]
        if tgt is None:
            tgt = S + v3(sd * 55, -(ARM1 + ARM2) * 0.97 * p.arm_scale, 90)
        else:
            tgt = v3(*tgt)
        j, e = ik3(S, tgt, ARM1, ARM2, (sd * 0.4, -0.2, -1.0))
        J[('elbow', sd)] = j; J[('wrist', sd)] = e
    nv = rot_x(v3(0, 1, 0), 0) * 1.0
    J['neck'] = C + sp * 20
    hd = v3(0, math.cos(p.neck_pitch * 0.6), math.sin(p.neck_pitch)) * 215
    J['head'] = C + hd + v3(0, 20, 0)
    return J


def draw_finger(g, base, ang, lengths, curl, w, col_, ol, s, sideways=0.0, sag=1.0):
    pts = [base]
    a = ang + sideways
    x, y = base
    for i, L in enumerate(lengths):
        a += curl * (0.35 + 0.15 * i) * (1 if sag >= 0 else -1)
        x += math.cos(a) * L * s; y += math.sin(a) * L * s
        pts.append((x, y))
    g.poly(stroke_poly(pts, [w * s, w * 0.8 * s, w * 0.62 * s, w * 0.4 * s][:len(pts)], 4), col_, ol, 1.6 * s)


def draw_creature(g, x0, y0, s, p, rim=True, tall=1.0):
    cam = Cam(x0, y0, s, p.yaw)
    J = csolve(p)
    S = {k: cam.P(v) for k, v in J.items() if isinstance(v, np.ndarray) and v.shape == (3,)}
    scr = {k: v[0] for k, v in S.items()}
    dep = {k: v[1] for k, v in S.items()}
    body = BODY; ol = RIM if rim else (30, 28, 44)
    lw = 3.2 * s
    out = {'scr': scr, 'J': J, 'cam': cam}

    def leg(sd):
        far = dep[('hip', sd)] < 0 and abs(math.sin(cam.yaw)) > 0.25
        c = shade(body, 0.8 if far else 1.0)
        h = scr[('hip', sd)]; k = scr[('knee', sd)]; a = scr[('ankle', sd)]
        g.poly(stroke_poly([h, k, a], [105 * s, 64 * s, 36 * s], 8), c, ol, lw)
        # foot: long digitigrade foot toward forward direction
        fwd = rot_y(v3(0, 0, 1), 0.0)
        base = J[('ankle', sd)] - v3(0, J[('ankle', sd)][1], 0)
        toe = J[('ankle', sd)] + v3(0, -J[('ankle', sd)][1] + 6, FOOT_L)
        t2 = cam.p(toe); an = a
        g.poly(stroke_poly([an, ((an[0] + t2[0]) / 2, (an[1] + t2[1]) / 2 + 4 * s), t2], [34 * s, 30 * s, 20 * s], 4), c, ol, lw)
        for i in (-1, 0, 1):
            tt = cam.p(toe + v3(i * 22, 0, 40))
            g.capsule(t2, tt, 10 * s, c, ol, 1.5 * s)

    def arm(sd):
        far = dep[('sh', sd)] < 0 and abs(math.sin(cam.yaw)) > 0.25
        c = shade(body, 0.85 if far else 1.0)
        sh = scr[('sh', sd)]; el = scr[('elbow', sd)]; wr = scr[('wrist', sd)]
        # extra mid-joint kink on the forearm
        mid = ((el[0] + wr[0]) / 2, (el[1] + wr[1]) / 2)
        a = ang_of(el, wr)
        kink = (mid[0] - math.sin(a) * 26 * s * sd, mid[1] + math.cos(a) * 26 * s * sd)
        g.poly(stroke_poly([sh, el, kink, wr], [74 * s, 52 * s, 40 * s, 30 * s], 6), c, ol, lw)
        ha = ang_of(kink, wr)
        for i, side in enumerate((-0.35, -0.12, 0.12, 0.35)):
            draw_finger(g, (wr[0] + math.cos(ha + 1.57) * (i - 1.5) * 9 * s, wr[1] + math.sin(ha + 1.57) * (i - 1.5) * 9 * s), ha, [78, 70, 62], p.curl * (0.7 + 0.2 * i) - 0.1 + 0.18 * p.sway * (i - 1.5),
                        15, c, ol, s, sideways=side * (1 - 0.6 * p.curl))
        out[('hand', sd)] = (wr, ha)

    def torso():
        P = J['pelvis']; C = J['chest']; sp = J['spine']
        psi = cam.yaw + p.twist * 0.5
        n = 10
        cl = []; ws = []
        for i in range(n + 1):
            u = i / n
            c3 = P + (C - P) * u - sp * (20 * (1 - u))
            a = lerp(66, 118, math.sin(u * math.pi / 2) ** 0.8) * (1.0 if u < 0.92 else lerp(1, 0.55, (u - 0.92) / 0.08))
            b = lerp(52, 70, u)
            w = math.sqrt((a * math.cos(psi)) ** 2 + (b * math.sin(psi)) ** 2)
            cl.append(cam.p(c3)); ws.append(w)
        L = []; R = []
        for i, ((cx, cy), w) in enumerate(zip(cl, ws)):
            a_ = cl[max(i - 1, 0)]; b_ = cl[min(i + 1, n)]
            dx, dy = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(dx, dy) or 1
            nx, ny = -dy / l, dx / l
            L.append((cx + nx * w * s, cy + ny * w * s)); R.append((cx - nx * w * s, cy - ny * w * s))
        top = cl[-1]
        cap = [(top[0] + (L[-1][0] - top[0]) * math.cos(t) + (cl[-1][0] - cl[-2][0]) * 0.7 * math.sin(t),
                top[1] + (L[-1][1] - top[1]) * math.cos(t) + (cl[-1][1] - cl[-2][1]) * 0.7 * math.sin(t)) for t in np.linspace(0, math.pi, 7)[1:-1]]
        g.poly(L + cap + R[::-1], body, ol, lw)
        # ribs & spine plates (subtle)
        for i in range(2, n - 1):
            cx, cy = cl[i]; w = ws[i] * s
            g.line([(cx - w * 0.8, cy - 8 * s), (cx, cy + 6 * s), (cx + w * 0.8, cy - 8 * s)], BODY2, 3.0 * s, a=200)
        # tattered cloak hanging from shoulders over hips/thighs
        hem = []
        cb = cam.p(P - sp * 20)
        wd = math.sqrt((120 * math.cos(psi)) ** 2 + (75 * math.sin(psi)) ** 2) * s
        left = (cb[0] - wd - 10 * s + p.sway * 10 * s, cb[1])
        right = (cb[0] + wd + 10 * s + p.sway * 10 * s, cb[1])
        tl = cl[-3]
        pts = [(tl[0] - ws[-3] * s * 1.0, tl[1])]
        n_t = 9
        for i in range(n_t + 1):
            t = i / n_t
            x = left[0] + (right[0] - left[0]) * t
            ln = (150 + 120 * abs(math.sin(i * 2.3 + 0.4))) * s * (0.85 + 0.25 * math.sin(i * 1.7))
            y = cb[1] + ln * (1.0 + 0.1 * math.sin(p.sway * 3 + i))
            pts.append((x + math.sin(i * 1.3 + p.sway * 2) * 6 * s, y if i % 2 == 0 else y - 55 * s))
        pts.append((tl[0] + ws[-3] * s * 1.0, tl[1]))
        g.poly(pts, shade(body, 0.95), ol, lw * 0.9, a=240)
        return cl

    def head():
        hc = cam.p(J['head'])
        neck0 = cam.p(J['chest'] + J['spine'] * 10)
        g.poly(stroke_poly([neck0, ((neck0[0] + hc[0]) / 2 + 8 * s, (neck0[1] + hc[1]) / 2 + 20 * s), (hc[0], hc[1] + 28 * s)], [60 * s, 38 * s, 34 * s], 6), body, ol, lw)
        g.push(); g.xf(hc[0], hc[1], p.head_roll + 0.25 * math.sin(p.neck_pitch) * math.sin(cam.yaw))
        sy = math.sin(cam.yaw + p.head_yaw); cy_ = math.cos(cam.yaw + p.head_yaw)
        wx = (46 + 16 * abs(sy)) * s; hy = 100 * s * tall
        pts = []
        for i in range(30):
            th = 2 * math.pi * i / 30
            x = wx * math.cos(th) * (1 - 0.22 * max(math.sin(th), 0) ** 1.3)
            y = hy * math.sin(th) - 14 * s
            x += sy * wx * 0.35 * max(math.sin(th), 0)
            pts.append((x, y))
        g.poly(pts, body, ol, lw)
        # brow-less hollow: faint recessed face plate
        g.ell(sy * 18 * s, -12 * s, wx * 0.72, hy * 0.62, BODY2, a=180, n=20)
        # long thin hair-like strands
        for i in range(7):
            x = (i - 3) * 14 * s
            g.line([(x, -hy * 0.9), (x * 1.5 + p.sway * 5 * s, -hy * 0.2 + 50 * s), (x * 2.2 + p.sway * 14 * s + math.sin(i + p.sway) * 6 * s, hy * 1.6)], BODY2, 2.4 * s, a=190)
        g.pop()
        ex = []
        if cy_ > -0.1:
            for sd in (-1, 1):
                a = cam.yaw + p.head_yaw
                lx = sd * 24 + 0
                X = (lx * math.cos(a) + 62 * math.sin(a)) * s
                if (62 * math.cos(a) - lx * math.sin(a)) > 0:
                    ex.append((hc[0] + X, hc[1] - 14 * s * tall, 10 * s * max(0.4, math.cos(a)) , 22 * s * tall * p.eyes))
        out['eyes'] = ex
        out['head'] = hc
        # mouth slit
        if p.mouth > 0.02 and cy_ > 0.1:
            out['mouth'] = (hc[0] + sy * 20 * s, hc[1] + 46 * s * tall, 36 * s * cy_, (4 + 38 * p.mouth) * s)

    order_arms = sorted((-1, 1), key=lambda d: dep[('sh', d)])
    order_legs = sorted((-1, 1), key=lambda d: dep[('hip', d)])
    for sd in order_arms:
        if dep[('sh', sd)] < -2: arm(sd)
    for sd in order_legs: leg(sd)
    torso()
    head()
    for sd in order_arms:
        if dep[('sh', sd)] >= -2: arm(sd)
    return out


def draw_creature_glow(ge, out, s, a=1.0, mouth_col=(255, 240, 230)):
    for (x, y, rx, ry) in out.get('eyes', []):
        ge.ell(x, y, rx, ry, tuple(int(c * a) for c in (255, 255, 255)), n=14)
        ge.ell(x, y, rx * 0.5, ry * 0.5, tuple(int(c * a) for c in (255, 255, 255)), n=10)
    if 'mouth' in out and a > 0:
        mx, my, mw, mh = out['mouth']
        g_ = ge
        g_.ell(mx, my, mw, mh, tuple(int(c * a * 0.9) for c in mouth_col), n=16)
        # teeth lines
        for i in range(-3, 4):
            g_.line([(mx + i * mw / 3.5, my - mh * 0.9), (mx + i * mw / 3.5, my + mh * 0.9)], (0, 0, 0), 2.0)


def creature_walk(ph, A=190.0, D=0.64, L=70.0, drag=1.0):
    p = CPose()
    f = ph % 1.0
    hx = 24 * math.sin(2 * math.pi * f)
    zs = {}
    needs = []
    for sd in (1, -1):
        u = (f + (0.0 if sd == 1 else 0.5)) % 1.0
        if u < D:
            z = A * (1 - 2 * u / D); lift = 0; st = 1
        else:
            s_ = (u - D) / (1 - D); z = -A + 2 * A * (s_ * s_ * (3 - 2 * s_)); lift = L * math.sin(math.pi * s_) ** 0.8; st = 0
        zs[sd] = z
        p.foot[sd] = (sd * HIPW, 150 + lift, z)
        if st:
            dh = math.hypot(z, 0)
            R = 0.9 * (THI + SHI)
            needs.append(150 + math.sqrt(max(R * R - dh * dh, 1.0)) * 0.97)
    y = min(needs) if needs else PELV
    p.hip = (hx, y - PELV, 0)
    p.twist = 0.22 * math.cos(2 * math.pi * f)
    p.roll = -0.05 * math.sin(2 * math.pi * f)
    p.sway = math.sin(2 * math.pi * f - 1.0)
    p.neck_pitch = 0.5 + 0.08 * math.sin(4 * math.pi * f)
    p.head_roll = 0.12 * math.sin(2 * math.pi * f + 0.6)
    for sd in (1, -1):
        zl = zs[sd]
        p.hand[sd] = None
    return p
