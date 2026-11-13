"""GATE TEST 2 — reflection, episode 35.4–43.4 s.
A 35.4–38.5  two-shot at the shop window: he relaxes, blinks, tilts his head; the reflection does none
             of it — it keeps staring at him, unblinking, not breathing.
B 38.5–42.6  close on the glass: the reflection leans in a hair, then slowly lifts a finger to its lips. «Тсс!»
C 42.6–43.4  from inside the shop, through the glass: his reaction, eyes wide, starting to recoil.
"""
import math
import random
import sys
sys.path.insert(0, '/tmp/hoplite/workspace/opus')
sys.path.insert(0, '/tmp/hoplite/workspace/rem')
import skia  # noqa: E402
import rig as R  # noqa: E402
from rig import V  # noqa: E402
import toon  # noqa: E402
import motion as M  # noqa: E402
import world as Wd  # noqa: E402
from gfx import P, lin, rad, path_poly, mix  # noqa: E402
from t_sheet import EX  # noqa: E402
import harness  # noqa: E402

W, H = Wd.W, Wd.H
NEON = (120, 220, 200)
GLASS_TINT = (0.62, 0.72, 0.92)


def shop_interior(cv, x0, y0, x1, y1, t, cam=0.0):
    """dim 24h shop seen through the glass: fridge glow, shelves, a hanging tube light"""
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(shader=lin((0, y0), (0, y1), (30, 40, 52), (18, 22, 30))))
    w = x1 - x0
    # back fridge row
    fx = x0 + w * 0.08 - cam * 0.3
    for i in range(4):
        rx = fx + i * w * 0.24
        cv.drawRect(skia.Rect(rx, y0 + 120, rx + w * 0.2, y1 - 260), P((70, 120, 120), 0.55))
        for j in range(5):
            yy = y0 + 170 + j * (y1 - y0 - 420) / 5
            cv.drawRect(skia.Rect(rx + 10, yy, rx + w * 0.2 - 10, yy + 8), P((110, 160, 150), 0.6))
            rnd = random.Random(i * 10 + j)
            for k in range(5):
                px = rx + 18 + k * (w * 0.2 - 30) / 5
                cv.drawRect(skia.Rect(px, yy - 46, px + 22, yy), P(rnd.choice([(170, 70, 60), (200, 170, 80), (80, 120, 170), (210, 210, 200)]), 0.55))
    cv.drawRect(skia.Rect(x0, y0 + 60, x1, y0 + 78), P((200, 240, 230), 0.55, blur=6))     # tube light
    # near shelf (dark)
    cv.drawRect(skia.Rect(x0 + w * 0.05 - cam * 0.7, y1 - 330, x0 + w * 0.65 - cam * 0.7, y1), P((22, 26, 34)))


def glass_fx(cv, x0, y0, x1, y1, t):
    """streak highlights + clinging rain drops on the glass"""
    cv.save(); cv.clipRect(skia.Rect(x0, y0, x1, y1))
    for k, (o, wd, a) in enumerate([(0.15, 120, 0.06), (0.42, 40, 0.07), (0.75, 180, 0.04)]):
        x = x0 + (x1 - x0) * o
        cv.drawPath(path_poly([(x, y0), (x + wd, y0), (x + wd - 400, y1), (x - 400, y1)]), P((220, 230, 255), a))
    rnd = random.Random(11)
    for _ in range(70):
        dx, dy, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(2, 6)
        slide = 0.0
        if rnd.random() < 0.15:
            slide = (t * rnd.uniform(20, 60)) % 300
        cv.drawCircle(dx, dy + slide, r, P((200, 215, 240), 0.35))
        cv.drawCircle(dx - r * 0.3, dy + slide - r * 0.3, r * 0.35, P((255, 255, 255), 0.5))
    cv.restore()


def neon_sign(cv, x, y, t, size=96):
    font = skia.Font(skia.Typeface('DejaVu Sans', skia.FontStyle.Bold()), size)
    txt = 'ПРОДУКТЫ 24'
    flick = 0.35 if (int(t * 13) % 17 == 0) else 1.0
    cv.drawString(txt, x, y, font, P(NEON, 0.55 * flick, blur=16))
    cv.drawString(txt, x, y, font, P(mix(NEON, (240, 255, 250), 0.5), flick))


def boy_pose_A(t):
    """the real boy: relief, blink, puzzled head tilt, a small lean toward the glass"""
    p = R.Pose()
    M.stand(p, weight=0.3, t=t, breath=0.35)
    drop = M.keys(t, [(35.4, 0.0), (35.9, 1.0)])
    p.sh_up = {1: 0.2 - 0.35 * drop, -1: 0.2 - 0.35 * drop}
    p.head_roll = M.keys(t, [(35.4, 0.0), (36.4, 0.0), (37.2, 0.16), (38.5, 0.2)])
    p.head_pitch = M.keys(t, [(35.4, 0.05), (36.0, -0.02), (38.5, 0.04)])
    p.lean = M.keys(t, [(35.4, 0.0), (37.0, 0.0), (38.5, 0.07)])
    p.e = M.kexpr(t, [(35.4, 'calm'), (36.3, 'calm'), (37.2, EX['confusion']), (38.5, EX['worried'] | dict(brow=0.4))], EX)
    p.blink = M.blink_at(t, [33.9, 36.55, 37.95])
    return p


def reflection_pose(t, base):
    """mirror of the starting pose, then it stops following him"""
    q = R.Pose()
    M.stand(q, weight=0.3, t=35.4, breath=0.0)         # frozen breath
    q = R.mirror_pose(q)
    q.sh_up = {1: 0.2, -1: 0.2}
    q.head_pitch = M.keys(t, [(35.4, 0.05), (38.5, 0.02), (40.0, 0.0)])
    q.lean = M.keys(t, [(38.5, 0.0), (40.0, 0.05)])  # creeps a hair closer
    q.e = M.kexpr(t, [(35.4, EX['neutral'] | dict(gx=0.12, smile=0.0)), (38.5, EX['neutral'] | dict(gx=0.0, smile=0.0, lid=0.06)),
                      (41.2, EX['neutral'] | dict(smile=0.02, lid=0.12)), (42.1, EX['shh']), (42.6, EX['shh'] | dict(lid=0.22))], EX)
    q.blink = 0.0
    # finger to lips (40.0 → 41.7), deliberately slow, then held
    k = M.keys(t, [(40.0, 0.0), (41.7, 1.0)], fn=M.smooth)
    if k > 0:
        rest = V(-60, 470, 60)
        tgt = V(45, 730, 300)
        q.hand_abs[1] = V(*(rest[i] + (tgt[i] - rest[i]) * k for i in range(3)))
        q.hand_mode[1] = 'point' if k > 0.35 else 'relaxed'
        q.hand_dir[1] = V(0, 1, 0) if k > 0.35 else None
    return q


def draw_reflection(cv, q, x, y, s, yaw, alpha=0.85):
    cv.saveLayer(None, P((255, 255, 255), alpha))
    lk = toon.Look(key=(0.6, -0.6), rim=(110, 190, 200), rim_w=4, tint=GLASS_TINT)
    lk.rim_dir = (0.9, -0.3)
    toon.draw(cv, q, x, y, s, yaw=yaw, cam_pitch=0.04, look=lk, ground_shadow=0)
    cv.restore()


# ------------------------------------------------------------------ A: two-shot
def shotA(cv, t):
    u = t - 35.4
    push = M.keys(t, [(32.6, 1.0), (38.5, 1.1)], fn=M.smooth)
    cv.translate(W * 0.45, H * 0.5); cv.scale(push, push); cv.translate(-W * 0.45, -H * 0.5)
    # wall
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (36, 40, 60), (26, 28, 42))))
    gx0, gy0, gx1, gy1 = 40, 420, 760, 1500
    shop_interior(cv, gx0, gy0, gx1, gy1, t)
    draw_reflection(cv, reflection_pose(t, None), 330, 1640, 0.78, yaw=-0.62)
    glass_fx(cv, gx0, gy0, gx1, gy1, t)
    # frame
    for r in [(gx0 - 22, gy0 - 22, gx1 + 22, gy0), (gx0 - 22, gy1, gx1 + 22, gy1 + 30), (gx0 - 22, gy0, gx0, gy1), (gx1, gy0, gx1 + 22, gy1)]:
        cv.drawRect(skia.Rect(*r), P((18, 20, 28)))
    neon_sign(cv, 70, 360, t, size=88)
    cv.drawRect(skia.Rect(0, gy1 + 30, W, H), P(shader=lin((0, gy1 + 30), (0, H), (44, 48, 70), (24, 26, 38))))
    Wd.wet_reflection(cv, 400, gy1 + 30, NEON, w=200, ln=380, a=0.12)
    # neon spill on the boy
    p = boy_pose_A(t)
    lk = toon.Look(key=(-0.8, -0.4), rim=(130, 220, 205), rim_w=5, tint=(0.82, 0.92, 0.98))
    lk.rim_dir = (-0.9, -0.3)
    a = toon.draw(cv, p, 830, 1840, 0.86, yaw=-2.35, cam_pitch=0.04, look=lk)
    # his breath — the reflection has none
    mx, my = a['mouth']
    Wd.breath_puff(cv, mx - 30, my, (t - 33.2) / 1.1, s=0.9, side=-1)
    Wd.breath_puff(cv, mx - 30, my, (t - 35.5) / 1.1, s=0.9, side=-1)
    Wd.breath_puff(cv, mx - 30, my, (t - 37.6) / 1.1, s=0.7, side=-1)
    Wd.rainfall(cv, t, seed=2, n=80, alpha=0.25)
    return dict(vign=0.62)


# ------------------------------------------------------------------ B: close on the glass
def shotB(cv, t):
    push = M.keys(t, [(38.5, 1.0), (42.6, 1.12)], fn=M.smooth)
    cv.translate(W * 0.5, H * 0.42); cv.scale(push, push); cv.translate(-W * 0.5, -H * 0.42)
    shop_interior(cv, -100, -200, W + 100, H + 100, t, cam=120)
    q = reflection_pose(t, None)
    draw_reflection(cv, q, 520, 2560, 1.62, yaw=-0.22, alpha=0.88)
    glass_fx(cv, 0, 0, W, H, t)
    # his own shoulder, out of focus in the foreground
    cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(22, 22)))
    p = boy_pose_A(38.5)
    toon.draw(cv, p, 1230, 2700, 1.9, yaw=2.6, cam_pitch=0.0, look=toon.Look(tint=(0.4, 0.45, 0.55)), ground_shadow=0)
    cv.restore()
    return dict(vign=0.7)


# ------------------------------------------------------------------ C: his reaction through the glass
def shotC(cv, t):
    u = t - 42.6
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (28, 32, 50), (16, 18, 28))))
    for i in range(3):     # street lamps far behind him, soft
        cv.drawCircle(160 + i * 380, 380 + i * 40, 60, P(Wd.SODIUM, 0.35, blur=40))
    p = R.Pose()
    M.stand(p, weight=0.0, t=t, breath=0.0)
    rec = M.keys(t, [(42.6, 0.0), (42.75, 0.0), (43.4, 1.0)], fn=M.smooth)
    p.lean = -0.16 * rec
    p.pelvis = V(0, -10 * rec, -60 * rec)
    p.head_pitch = -0.08 * rec
    p.sh_up = {1: 0.7 * rec, -1: 0.7 * rec}
    p.e = M.kexpr(t, [(42.6, EX['worried']), (42.8, 'shock'), (43.4, EX['shock'] | dict(sweat=0.8))], EX)
    for sd in (1, -1):
        p.hand[sd] = V(30 * sd, -280 + 120 * rec, 60 + 80 * rec)
        p.hand_mode[sd] = 'open' if rec > 0.3 else 'relaxed'
    toon.draw(cv, p, 540, 2900 - 60 * rec, 2.0, yaw=0.18, cam_pitch=0.0,
              look=toon.Look(key=(0.7, -0.5), rim=(130, 220, 205), rim_w=6, tint=(0.86, 0.92, 1.0)), ground_shadow=0)
    # we are inside: shop light reflected faintly on the glass between us and him
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (W, H), (120, 200, 190), (40, 60, 70), 0.10, 0.02)))
    glass_fx(cv, 0, 0, W, H, t)
    # seen from inside, the window lettering reads backwards
    cv.save(); cv.translate(W, 0); cv.scale(-1, 1)
    neon_sign(cv, 60, 140, t, size=90)
    cv.restore()
    return dict(vign=0.72)


def frame(cv, t):
    if t < 38.5:
        return shotA(cv, t)
    if t < 42.6:
        return shotB(cv, t)
    return shotC(cv, t)


if __name__ == '__main__':
    t0 = 35.4
    stills = [int((x - t0) * 30) for x in (35.6, 37.4, 38.6, 40.5, 41.8, 42.4, 43.2)]
    print(harness.render('TEST_REFLECTION', t0, 43.4, frame, stills=stills))
