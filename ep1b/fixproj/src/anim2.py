"""Animation helpers for char2: gait, run, blinking, idle."""
import math
from char2 import *


def sstep(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def lerp1(a, b, t): return a + (b - a) * t


def kf(t, keys):
    """smooth keyframes [(t,v),...]"""
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t < t1: return v0 + (v1 - v0) * sstep((t - t0) / (t1 - t0))
    return keys[-1][1]


def klin(t, keys):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t < t1: return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return keys[-1][1]


def blink_at(t, seed=0):
    """0 open .. 1 closed; irregular blink schedule"""
    per = 3.1 + 0.9 * math.sin(seed * 3.7 + 1)
    k = (t + seed * 1.3) % per
    d = 0.17
    if k < d:
        x = k / d
        return math.sin(math.pi * x) ** 1.5
    # occasional double blink
    if int((t + seed * 1.3) / per) % 3 == 1 and 0.32 < k < 0.32 + d:
        return math.sin(math.pi * (k - 0.32) / d) ** 1.5
    return 0.0


def eyes_alive(e, t, seed=0, amt=1.0):
    """add micro-saccades"""
    e = dict(e)
    e['px'] = e['px'] + amt * (0.10 * math.sin(t * 2.1 + seed) + 0.06 * math.sin(t * 5.3 + seed * 2))
    e['py'] = e['py'] + amt * (0.06 * math.sin(t * 1.7 + seed * 3))
    return e


def ease(s): return s * s * (3 - 2 * s)


def leg_state(u, A, D, L):
    """foot (z, lift, pitch) for local phase u in [0,1)."""
    if u < D:
        z = A * (1 - 2 * u / D)
        lift = 0.0
        pitch = 0.0
        if u < 0.12 * D / 0.6: pitch = 0.32 * (1 - u / (0.12 * D / 0.6))
        if u > D - 0.16: pitch = -0.7 * sstep((u - (D - 0.16)) / 0.16)
        stance = 1.0
    else:
        s = (u - D) / (1 - D)
        z = -A + 2 * A * ease(s)
        lift = L * math.sin(math.pi * min(1.0, s * 1.15)) ** 0.85 * (1 - 0.15 * s)
        pitch = -0.5 * (1 - sstep(s * 2.2)) + 0.28 * sstep((s - 0.7) / 0.3)
        stance = 0.0
    return z, lift, pitch, stance


def gait(ph, A=95.0, D=0.6, L=58.0, rho=0.93, Sx=20.0, Tp=0.12, Tc=0.17, arm=1.0, lean=0.045, run=False, spread=0.0):
    """ph = gait phase in cycles. Returns Pose with yaw=0."""
    p = Pose()
    f = ph % 1.0
    zs = {}
    needs = []
    hx = Sx * math.sin(2 * math.pi * f)
    p.hip = (hx, 0.0, 0.0)
    for sd in (1, -1):
        u = (f + (0.0 if sd == 1 else 0.5)) % 1.0
        z, lift, pitch, st = leg_state(u, A, D, L)
        zs[sd] = z
        fx = sd * (HIP_W + spread) - 0.0
        p.foot[sd] = (fx, ANKLE + lift, z)
        p.foot_pitch[sd] = pitch
        p.foot_yaw[sd] = 0.06 * sd
        if st > 0.5:
            dh = math.hypot(fx - (sd * HIP_W + hx), z)
            R = rho * (THIGH + SHIN)
            needs.append(ANKLE + math.sqrt(max(R * R - dh * dh, 1.0)))
    if run:
        # analytic bounce: two flights per cycle
        bounce = 0.5 * (1 - math.cos(4 * math.pi * (f + 0.08)))
        base = rho * (THIGH + SHIN) + ANKLE
        y = base + 46 * bounce * 1.0 - 6
    else:
        y = min(needs) if needs else HIP_Y
    p.hip = (hx, y - HIP_Y, 0.0)
    p.pelvis_twist = -Tp * math.cos(2 * math.pi * f)
    p.twist = Tc * math.cos(2 * math.pi * f)
    p.roll = -0.035 * math.sin(2 * math.pi * f) * (2.0 if run else 1.0)
    p.lean = lean
    p.head_roll = 0.55 * (-p.roll) * 0
    p.head_pitch = 0.035 * math.sin(4 * math.pi * f) - 0.6 * lean * (1 if run else 0)
    p.head_yaw = -0.5 * p.twist
    p.breath = 0.3 * math.sin(2 * math.pi * f * 2)
    p.sway = math.sin(2 * math.pi * f - 0.8) * (1.6 if run else 1.0)
    p.knee_pole = (0.0, 0.0, 1.0)
    # arms
    for sd in (1, -1):
        # swing opposite to same-side leg
        zl = zs[sd]
        sh_y = HIP_Y + 300 - 30
        if not run:
            za = -zl * 0.95 * arm
            fw = max(0.0, za) / max(A, 1)
            hy = sh_y - (UARM + FARM) * 0.93 + 46 * fw
            p.hand[sd] = (sd * (SH_W + 12 - 10 * fw), hy + y - HIP_Y * 0 - (y - HIP_Y) * 0, za + 10)
            # keep hand relative to the moving torso
            p.hand[sd] = (sd * (SH_W + 12 - 10 * fw) + hx * 0.4, hy + (y - HIP_Y) * 0.8, za + 10)
            p.elbow_pole[sd] = (sd * 0.5, -0.1, -1.0)
            p.hand_mode[sd] = 'relaxed'
        else:
            za = -zl * 1.25 * arm
            fw = za / max(A, 1)
            p.hand[sd] = (sd * (SH_W - 16) + hx * 0.4, sh_y - 150 + 70 * max(fw, 0) - 10 * min(fw, 0) + (y - HIP_Y) * 0.8, za * 1.1 + 40)
            p.elbow_pole[sd] = (sd * 0.55, -0.35, -1.0)
            p.hand_mode[sd] = 'fist'
    p.speed_ground = 0.0
    return p


def gait_speed(A, D, fcyc): return 2 * A * fcyc / D


def idle(t, e=None, seed=0, sway=1.0, yaw=0.0):
    p = Pose(yaw=yaw)
    p.e = eyes_alive(e or EXPR['neutral'], t, seed)
    p.blink = blink_at(t, seed)
    b = math.sin(2 * math.pi * t / 3.4 + seed)
    p.breath = b
    p.shoulder_up = 0.25 * b
    # slow weight shift between feet
    w = math.sin(t * 0.55 + seed * 2)
    p.hip = (7 * w * sway, -3 * (1 - abs(w)) * sway, 0)
    p.roll = -0.012 * w * sway
    p.foot[-1] = (-HIP_W - 6 + 3 * w, ANKLE, 4)
    p.foot[1] = (HIP_W + 6 + 3 * w, ANKLE, -2)
    p.foot_yaw[-1] = -0.12; p.foot_yaw[1] = 0.12
    p.head_roll = 0.02 * math.sin(t * 0.8 + seed)
    p.sway = 0.2 * math.sin(t * 1.3 + seed)
    return p


def hand_at(cam_pose_yaw, x0, y0, s, sx, sy, depth=0.0):
    c = Cam(x0, y0, s, cam_pose_yaw)
    v = c.inv(sx, sy, depth)
    return (float(v[0]), float(v[1]), float(v[2]))
