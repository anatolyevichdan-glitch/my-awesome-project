"""Character motion: keyed walk / run cycles with planted feet, weight shift and overlap."""
import math
import numpy as np
import rig as R
from rig import V

TAU = 2 * math.pi


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = min(1.0, max(0.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def lerp(a, b, t):
    return a + (b - a) * t


def keys(t, ks, fn=ease_io):
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t <= t1:
            return lerp(v0, v1, fn((t - t0) / max(1e-6, t1 - t0)))
    return ks[-1][1]


def kexpr(t, ks, EX):
    g = lambda e: EX[e] if isinstance(e, str) else e
    if t <= ks[0][0]:
        return dict(g(ks[0][1]))
    for (t0, e0), (t1, e1) in zip(ks, ks[1:]):
        if t <= t1:
            return R.lerp_e(g(e0), g(e1), ease_io((t - t0) / max(1e-6, t1 - t0)))
    return dict(g(ks[-1][1]))


def blink_at(t, times, dur=0.16):
    for b in times:
        if b <= t < b + dur:
            x = (t - b) / dur
            return 1.0 - abs(2 * x - 1) ** 1.5
    return 0.0


def auto_blinks(t0, t1, seed=0, every=3.1):
    rng = np.random.default_rng(seed)
    out, t = [], t0 + rng.uniform(0.4, 1.6)
    while t < t1:
        out.append(t)
        t += every * rng.uniform(0.6, 1.4)
    return out


def foot_cycle(q, stride, lift, heel_pitch=0.32, toe_pitch=-0.55, stance=0.5):
    """q in [0,1): 0 = heel strike. Returns (z, y_lift, pitch). z relative to pelvis (forward +)."""
    if q < stance:
        u = q / stance
        z = stride * (0.5 - u)
        y = 0.0
        if u < 0.12:
            pitch = heel_pitch * (1 - u / 0.12)
        elif u < 0.62:
            pitch = 0.0
        else:
            k = (u - 0.62) / 0.38
            pitch = toe_pitch * k * k
            y = 22 * k * k
        return z, y, pitch
    u = (q - stance) / (1 - stance)
    z = stride * (-0.5 + ease_io(u))
    y = lift * math.sin(math.pi * min(1.0, u * 1.08)) ** 1.3 + 22 * max(0.0, 1 - u / 0.25) ** 2
    pitch = toe_pitch * (1 - smooth(u / 0.35)) * 0.8 + heel_pitch * smooth((u - 0.6) / 0.4)
    return z, y, pitch


def walk(p, phase, stride=330.0, amp=1.0, arm=1.0, lift=95.0, bob=24.0, sway=10.0, mood=0.0):
    """phase in cycles (1.0 = two steps). Fills feet, pelvis, twist, arms, head stabilisation.
    mood 0 = relaxed, 1 = tense (shorter arm swing, raised shoulders, head forward)."""
    q0 = phase % 1.0
    for sd, off in ((1, 0.0), (-1, 0.5)):
        q = (q0 + off) % 1.0
        z, y, pitch = foot_cycle(q, stride * amp, lift * amp)
        p.foot[sd] = V(R.HIP_W * sd * 0.92, R.ANKLE_H + y, z)
        p.foot_pitch[sd] = pitch
        p.foot_yaw[sd] = 0.04 * sd
    # pelvis: lowest just after each contact, highest at passing
    dip = math.cos(TAU * 2 * (q0 - 0.08))
    p.pelvis = V(sway * amp * math.sin(TAU * q0), -bob * amp * (0.5 + 0.5 * dip) - 6 * mood, 0)
    p.ptwist = 0.16 * amp * math.sin(TAU * q0 + math.pi / 2) * -1
    p.twist = -p.ptwist * 0.75
    p.roll = 0.035 * amp * math.sin(TAU * q0)
    p.lean = 0.05 * amp + 0.06 * mood
    # arms swing opposite to the legs, with follow-through lag
    for sd, off in ((1, 0.5), (-1, 0.0)):
        a = math.sin(TAU * (q0 + off - 0.06) + math.pi / 2)
        sw = 105 * amp * arm * (1 - 0.55 * mood)
        fwd = a * sw
        p.hand[sd] = V(24 * sd + 6 * sd * mood, -330 + 18 * max(0, a) * amp + 30 * mood, 30 + fwd + 25 * mood)
        p.elbow_pole[sd] = V(0.5 * sd, -0.3, -1.0)
        p.hand_mode[sd] = 'relaxed'
    p.sh_up = {1: 0.25 * mood, -1: 0.25 * mood}
    # head counters the body so the gaze stays level; small delayed nod
    p.head_roll = -p.roll * 0.8
    p.head_pitch = 0.04 * math.cos(TAU * 2 * (q0 - 0.18)) * amp + 0.08 * mood
    p.head_yaw = -p.twist * 0.6
    p.hem = 0.5 * math.sin(TAU * 2 * (q0 - 0.12)) * amp


def run(p, phase, stride=520.0, amp=1.0, exhaustion=0.0):
    """running: flight phase, strong lean, pumping bent arms"""
    q0 = phase % 1.0
    for sd, off in ((1, 0.0), (-1, 0.5)):
        q = (q0 + off) % 1.0
        z, y, pitch = foot_cycle(q, stride * amp, 190 * amp, heel_pitch=0.2, toe_pitch=-0.8, stance=0.34)
        p.foot[sd] = V(R.HIP_W * sd * 0.8, R.ANKLE_H + y, z)
        p.foot_pitch[sd] = pitch
    p.pelvis = V(6 * math.sin(TAU * q0), -55 * amp + 30 * amp * math.cos(TAU * 2 * (q0 - 0.2)), 0)
    p.ptwist = -0.22 * amp * math.sin(TAU * q0 + math.pi / 2)
    p.twist = -p.ptwist * 0.9
    p.lean = 0.24 * amp + 0.06 * exhaustion
    p.roll = 0.03 * math.sin(TAU * q0)
    for sd, off in ((1, 0.5), (-1, 0.0)):
        a = math.sin(TAU * (q0 + off - 0.05) + math.pi / 2)
        p.hand[sd] = V(36 * sd, -210 + 70 * max(0, a), 40 + 190 * a * amp)
        p.elbow_pole[sd] = V(0.6 * sd, -0.2, -1.0)
        p.hand_mode[sd] = 'fist'
    p.head_pitch = -0.04 + 0.05 * math.cos(TAU * 2 * q0) + 0.1 * exhaustion
    p.head_roll = -p.roll
    p.head_yaw = -p.twist * 0.5
    p.hem = 0.8 * math.sin(TAU * 2 * (q0 - 0.1))
    p.heave = 5 * exhaustion * math.sin(TAU * 2 * q0)


def stand(p, weight=0.0, t=0.0, breath=0.25):
    """idle stance; weight -1..1 shifts onto a leg"""
    p.foot = {1: V(R.HIP_W * 1.0, R.ANKLE_H, 6), -1: V(-R.HIP_W * 1.0, R.ANKLE_H, -6)}
    p.foot_pitch = {1: 0.0, -1: 0.0}
    p.pelvis = V(14 * weight, -4 - 4 * abs(weight), 0)
    p.roll = -0.03 * weight
    p.breath = t * breath
    for sd in (1, -1):
        p.hand[sd] = V(26 * sd, -332, 22)
        p.hand_mode[sd] = 'relaxed'
