"""LAST PASSENGER — EP1: shared helpers for all shots."""
import math
import random
import sys
import wave
for _p in ('/tmp/hoplite/workspace/rem', '/tmp/hoplite/workspace/opus', '/tmp/hoplite/workspace/lp'):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)
import numpy as np  # noqa: E402
import skia  # noqa: E402
import rig as R  # noqa: E402
from rig import V  # noqa: E402
import toon2 as T2  # noqa: E402
import motion as M  # noqa: E402
import world as Wd  # noqa: E402
import env as E  # noqa: E402
from gfx import P, lin, rad, path_poly, path_smooth, mix  # noqa: E402
from t_sheet import EX  # noqa: E402

W, H = 1080, 1920
DUR = 134.922
TAU = 2 * math.pi
EX = dict(EX)
EX['panic'] = EX['panic'] | dict(mround=0.7, mw=0.75, smile=-0.6)
EX['terror'] = EX['terror'] | dict(mround=0.65, mw=0.8, smile=-0.6)
EX['tired'] = EX['neutral'] | dict(lid=0.38, brow=0.1, tilt=0.2, smile=-0.05)
EX['closed'] = EX['neutral'] | dict(lid=1.0, smile=0.0, mw=0.7)
EX['babka_calm'] = EX['neutral'] | dict(lid=0.3, smile=0.08, mw=0.6, pupil=0.7)
EX['babka_smile'] = EX['neutral'] | dict(lid=0.38, smile=0.75, mw=0.95, asym=0.25, pupil=0.6, brow=-0.1)
EX['blank'] = EX['neutral'] | dict(lid=0.45, smile=0.0, pupil=0.5, mw=0.6, gy=-0.2)


# ------------------------------------------------------------------ narration envelope (lip-sync)
def _env():
    w = wave.open('/tmp/hoplite/workspace/lp/anim/narr_env.wav')
    n, sr = w.getnframes(), w.getframerate()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32)
    hop = sr // 60
    e = np.sqrt(np.convolve(a * a, np.ones(hop) / hop, 'same')[::hop])
    return e / (np.percentile(e, 98) + 1e-9)


ENV = _env()


def voice(t, t0=-1, t1=1e9):
    if not (t0 <= t <= t1):
        return 0.0
    i = int(t * 60)
    return float(np.clip(ENV[i], 0, 1)) if 0 <= i < len(ENV) else 0.0


# ------------------------------------------------------------------ helpers
def integ(fn, t0, t, dt=1 / 240):
    n = max(0, int((t - t0) / dt))
    s = sum(fn(t0 + (i + 0.5) * dt) for i in range(n))
    return s * dt + fn(t) * ((t - t0) - n * dt)


def push(cv, z, cx=W / 2, cy=H / 2):
    cv.translate(cx, cy); cv.scale(z, z); cv.translate(-cx, -cy)


def blur_layer(cv, r):
    cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(r, r)))


def shake(t, amt, f=23.0):
    return amt * math.sin(t * f) * math.sin(t * f * 0.71 + 1.3)


def LK(key=(-0.6, -0.5), rim=(110, 140, 200), rim_w=5, tint=None, rim_dir=None):
    lk = T2.Look(key=key, rim=rim, rim_w=rim_w, tint=tint)
    if rim_dir:
        lk.rim_dir = rim_dir
    return lk


STREET_LK = dict(key=(0.7, -0.6), rim=(240, 170, 100), tint=(0.78, 0.82, 0.98))
BUS_LK = dict(key=(0.0, -1.0), rim=(170, 210, 190), tint=(0.86, 0.96, 0.90))


def fig(cv, name, p, x, y, s, yaw=None, lk=None, **kw):
    with T2.use(name):
        return T2.draw(cv, p, x, y, s, yaw=yaw, look=lk or LK(**BUS_LK), **kw)


def hero_walk(t, cad=0.95, mood=0.3, amp=1.0, ph0=0.0):
    p = R.Pose(); M.walk(p, ph0 + t * cad, mood=mood, amp=amp)
    return p


def sit_pose(t, seed=0, breathe=0.15):
    p = R.Pose(); M.sit(p, t=t, breath=breathe)
    return p


def lerp_pose_sit(t, k):
    """blend from stand (k=0) to sit (k=1)"""
    a = R.Pose(); M.stand(a, t=t)
    b = R.Pose(); M.sit(b, t=t)
    for sd in (1, -1):
        a.foot[sd] = a.foot[sd] + (b.foot[sd] - a.foot[sd]) * k
        a.hand[sd] = a.hand[sd] + (b.hand[sd] - a.hand[sd]) * k
    a.pelvis = a.pelvis + (b.pelvis - a.pelvis) * k
    a.lean = a.lean + (b.lean - a.lean) * k + 0.25 * math.sin(math.pi * k)
    return a


def arm_into_frame(cv, root, tip, col=(30, 30, 36), skin=(240, 204, 190), w=90, hand_r=64, open_hand=False):
    """hoodie sleeve + hand drawn in screen space from root (off-frame) to tip"""
    from gfx import capsule_path
    pa = capsule_path(root, tip, w, w * 0.8)
    cv.drawPath(pa, P(col))
    cv.drawPath(pa, P((60, 62, 74), 0.5, style='stroke', width=4))
    dx, dy = tip[0] - root[0], tip[1] - root[1]
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    cx, cy = tip[0] + ux * hand_r * 0.55, tip[1] + uy * hand_r * 0.55
    cv.drawCircle(tip[0] - ux * 18, tip[1] - uy * 18, w * 0.82, P((18, 18, 22)))     # cuff
    if open_hand:
        cv.drawOval(skia.Rect(cx - hand_r * 1.05, cy - hand_r * 0.8, cx + hand_r * 1.05, cy + hand_r * 0.8), P(skin))
    else:
        cv.drawCircle(cx, cy, hand_r, P(skin))
    cv.drawCircle(cx - uy * hand_r * 0.55, cy + ux * hand_r * 0.55, hand_r * 0.42, P(skin))        # thumb
    cv.drawCircle(cx, cy, hand_r, P((170, 120, 110), 0.25, style='stroke', width=4))
    return cx, cy


def rain(cv, t, n=150, alpha=0.32, seed=5, ln=46, cx=0.0):
    Wd.rainfall(cv, t, seed=seed, n=n, alpha=alpha, ln=ln, cx=cx)


def puddles(cv, gy, cx, t, col=E.SODIUM, seed=3):
    r = random.Random(seed)
    for i in range(6):
        x = r.uniform(-200, 1300) - cx
        w = r.uniform(120, 260)
        y = gy + r.uniform(30, 260)
        cv.drawOval(skia.Rect(x - w, y - 18, x + w, y + 18), P((40, 46, 66), 0.8))
        k = (t * 1.7 + i * 0.37) % 1.0
        cv.drawOval(skia.Rect(x - 40 * k * 3, y - 6 * k * 3, x + 40 * k * 3, y + 6 * k * 3), P((150, 160, 190), 0.25 * (1 - k), style='stroke', width=2))


def flick(t, events, depth=0.85):
    """fluorescent flicker: events = [(t0, dur)]"""
    for t0, d in events:
        if t0 <= t < t0 + d:
            r = random.Random(int(t * 60))
            return 1.0 - depth * (r.random() > 0.45)
    return 1.0
