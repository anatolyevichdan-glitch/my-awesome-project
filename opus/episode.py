"""DON'T LOOK BACK — EPISODE 1 (OPUS rebuild). Full 108.36 s shot list.

Every shot is fn(cv, t) with t = episode time; it draws a 1080x1920 frame and returns post-grade kwargs.
Opening (0–9.2) and reflection (32.6–43.9) shots come from the approved gate tests.
"""
import math
import random
import sys
import wave
import numpy as np
sys.path.insert(0, '/tmp/hoplite/workspace/opus')
sys.path.insert(0, '/tmp/hoplite/workspace/rem')
import skia  # noqa: E402
import rig as R  # noqa: E402
from rig import V  # noqa: E402
import toon  # noqa: E402
import motion as M  # noqa: E402
import world as Wd  # noqa: E402
import creature2 as C  # noqa: E402
from gfx import P, lin, rad, path_poly, mix  # noqa: E402
from t_sheet import EX  # noqa: E402
import opening as O  # noqa: E402
import reflection as F  # noqa: E402

W, H = Wd.W, Wd.H
TAU = 2 * math.pi
DUR = 108.36
FONT = '/tmp/hoplite/workspace/rem/subs2/fonts/Inter-Bold.ttf'
_TF = skia.Typeface.MakeFromFile(FONT)
STEPS = []          # (t, kind, who) footstep log for the foley pass


def font(sz):
    return skia.Font(_TF, sz)


# ------------------------------------------------------------------ narration envelope (lip-sync for the double's whisper)
def _env():
    w = wave.open('/tmp/hoplite/workspace/rem/audio2/stem_narration.wav')
    n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
    a = np.frombuffer(w.readframes(n), dtype=np.int16 if w.getsampwidth() == 2 else np.int32).astype(np.float32)
    a = a.reshape(-1, ch).mean(axis=1)
    hop = sr // 60
    e = np.sqrt(np.convolve(a * a, np.ones(hop) / hop, 'same')[::hop])
    return e / (np.percentile(e, 98) + 1e-9), 60.0


ENV, ENV_RATE = _env()


def voice(t):
    i = int(t * ENV_RATE)
    return float(np.clip(ENV[i], 0, 1)) if 0 <= i < len(ENV) else 0.0


# ------------------------------------------------------------------ helpers
def integ(fn, t0, t, dt=1 / 240):
    """∫ fn dt from t0 to t (cheap, deterministic)"""
    n = max(0, int((t - t0) / dt))
    s = sum(fn(t0 + (i + 0.5) * dt) for i in range(n))
    return s * dt + fn(t) * ((t - t0) - n * dt)


def look(k=0.0, side=-1, rim=None, tint=None):
    lk = O.look_for(k, side)
    if rim is not None:
        lk.rim = rim
    if tint is not None:
        lk.tint = tint
    return lk


def push(cv, z, cx=W / 2, cy=H / 2):
    cv.translate(cx, cy); cv.scale(z, z); cv.translate(-cx, -cy)


def blur_layer(cv, r):
    cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(r, r)))


def phone_prop(glow=1.0, scale=1.0):
    def fn(cv, hp, cam, S, sd):
        s = cam.s * scale
        cv.save(); cv.translate(hp[0], hp[1] - 40 * s); cv.rotate(-8)
        r = skia.Rect(-46 * s, -86 * s, 46 * s, 86 * s)
        cv.drawRoundRect(r, 14 * s, 14 * s, P((14, 14, 18)))
        r2 = skia.Rect(-40 * s, -78 * s, 40 * s, 78 * s)
        cv.drawRoundRect(r2, 9 * s, 9 * s, P(mix((20, 24, 34), (190, 214, 255), glow)))
        cv.restore()
        if glow > 0:
            cv.drawCircle(hp[0], hp[1] - 60 * s, 330 * s, P(shader=rad((hp[0], hp[1] - 60 * s), 330 * s, (170, 200, 255), (170, 200, 255), 0.22 * glow, 0.0)))
    return fn


def vibrate_rings(cv, x, y, t, s=1.0):
    for k in range(3):
        a = ((t * 3 + k / 3) % 1.0)
        cv.drawArc(skia.Rect(x - (30 + 60 * a) * s, y - (30 + 60 * a) * s, x + (30 + 60 * a) * s, y + (30 + 60 * a) * s),
                   200, 140, False, P((230, 236, 255), 0.6 * (1 - a), style='stroke', width=5 * s))


def shake(t, amt, f=23.0):
    return amt * math.sin(t * f) * math.sin(t * f * 0.71 + 1.3)


# ------------------------------------------------------------------ A: street walk + CCTV (gate test, extended)
def A3(cv, t):
    return O.shot3(cv, t)


SHADOW_GAP = 330.0        # world px behind the boy (at S=0.62)


def B1(cv, t):
    """9.2–11.9 «прямо за твоей спиной»: tall shape right behind him, matching his walk"""
    S = 0.62
    gy = 1480
    ph = (t - 9.2) * O.CAD
    bx = 300 + O.V1 * (t - 9.2)
    cx = bx - 640
    zoom = M.keys(t, [(9.2, 1.08), (11.9, 1.16)], fn=M.smooth)
    push(cv, zoom, W / 2, H * 0.55)
    heads = O.street_layers(cv, cx + 2000, gy, t)
    p = O.boy_walk(t, 0.45)
    p.e = M.kexpr(t, [(9.2, 'worried'), (11.9, EX['worried'] | dict(gx=-0.5))], EX)
    p.blink = M.blink_at(t, [10.4])
    sx = bx - cx
    # the shape: huge, its head above frame; walks in step one beat later
    cp = C.CPose(); cp.facing = 1; cp.stride = 0.5
    ch = 1500
    cp.step = ph * (O.V1 / O.CAD) / (500 * cp.stride * ch / 1000) * 1.0
    a = M.smooth((t - 9.2) / 1.0)
    C.draw(cv, cp, sx - SHADOW_GAP, gy + 66, ch, t=t, alpha=0.95 * a, rim=(70, 80, 110), smoke=0.8)
    toon.draw(cv, p, sx, gy + 60, S, cam_pitch=0.06, look=look(O.light_at(sx, heads)))
    Wd.rainfall(cv, t, seed=1, n=150, cx=cx, par=1.0)
    return dict(vign=0.68)


def B2(cv, t):
    """11.9–14.3 «Ты ускоряешь шаг. Он тоже.» low tracking shot on the feet"""
    S = 1.2
    gy = 1780
    cad = lambda x: M.keys(x, [(11.9, 0.95), (12.6, 1.45), (14.3, 1.5)])
    ph = integ(cad, 11.9, t)
    bx = 660 * S * ph
    cx = bx - 700
    Wd.sky(cv, (14, 16, 30), (40, 44, 70), gy)
    for i in range(-2, 12):     # blurred lamp bokeh far behind
        x = i * 380 - (cx * 0.25) % 380
        cv.drawCircle(x, 760, 70, P(Wd.SODIUM, 0.30, blur=34))
    blur_layer(cv, 6)
    for i in range(-2, 14):
        wx = i * 520 - cx * 0.5
        Wd.panel_building(cv, wx, 470, 300, gy - 120, (40, 44, 70), seed=300 + i, lit=0.2, floor_h=120, t=t)
    cv.restore()
    Wd.street_ground(cv, gy, cx)
    # puddle with lamp reflection
    for i in range(-1, 8):
        x = i * 900 + 420 - cx
        if -500 < x < W + 500:
            cv.drawOval(skia.Rect(x - 260, gy + 10, x + 260, gy + 90), P((60, 70, 104)))
            cv.drawOval(skia.Rect(x - 120, gy + 30, x + 40, gy + 70), P(Wd.SODIUM, 0.35, blur=10))
    # the shape's legs behind him (dark, out of focus, speeding up too)
    cp = C.CPose(); cp.facing = 1; cp.stride = 0.55
    ch = 3300
    cp.step = bx / (500 * cp.stride * ch / 1000)
    blur_layer(cv, 5)
    C.draw(cv, cp, (bx - cx) - 560, gy + 40, ch, t=t, alpha=0.95, rim=(80, 90, 120), smoke=0.4)
    cv.restore()
    p = R.Pose(); p.yaw = 1.35
    mood = M.keys(t, [(11.9, 0.5), (12.6, 0.9)])
    M.walk(p, ph, mood=mood, arm=1.2)
    toon.draw(cv, p, bx - cx, gy + 40, S, cam_pitch=-0.06, look=look(0.35, rim=(255, 200, 140)))
    Wd.rainfall(cv, t, seed=7, n=110, ln=70, alpha=0.3)
    return dict(vign=0.66)


def B3(cv, t):
    """14.3–17.5 «Ты останавливаешься. И он замирает.»"""
    S = 0.62
    gy = 1480
    stop = 14.95
    amp = lambda x: M.keys(x, [(14.3, 1.0), (stop, 0.0)], fn=M.smooth)
    cad = lambda x: 1.2
    ph = integ(lambda x: cad(x) * amp(x), 14.3, t)
    bx = 660 * S * math.sin(O.YAW1) * ph
    cx = 200.0 + bx * 0.25 - 400     # camera nearly locked off, a slight drift
    heads = O.street_layers(cv, cx + 4000, gy, t)
    sx = 640 + bx - (cx + 400)
    p = R.Pose(); p.yaw = O.YAW1
    w = amp(t)
    if w > 0.001:
        M.walk(p, integ(cad, 14.3, t), amp=w, mood=0.7)
    if w < 0.999:
        q = R.Pose(); q.yaw = O.YAW1; M.stand(q, weight=0.0, t=t, breath=0.0)
        if w <= 0.001:
            p = q
    p.yaw = O.YAW1
    p.sh_up = {1: 0.7, -1: 0.7}
    p.e = M.kexpr(t, [(14.3, 'worried'), (15.2, EX['mild_fear'] | dict(gx=-0.9)), (16.2, EX['terror'] | dict(gx=-1.0, mopen=0.2)),
                      (17.5, EX['terror'] | dict(gx=-1.0, mopen=0.25))], EX)
    p.head_yaw = M.keys(t, [(15.2, 0.0), (15.9, -0.25)])
    p.blink = M.blink_at(t, [15.05])
    # the shape stops a beat later, mid-stride, and stays frozen
    cp = C.CPose(); cp.facing = 1; cp.stride = 0.5
    ch = 1250
    cstop = 15.9
    cph = lambda x: M.keys(x, [(14.3, 0.0), (cstop, 1.15)], fn=lambda u: 1 - (1 - u) ** 2)
    cp.step = cph(t)
    cp.head_roll = M.keys(t, [(16.3, 0.0), (17.4, 0.35)], fn=M.smooth)
    cxs = sx - 470 + 500 * cp.stride * ch / 1000 * (cp.step - 1.15)
    C.draw(cv, cp, cxs, gy + 66, ch, t=t, alpha=0.96, rim=(70, 80, 110), smoke=0.8)
    toon.draw(cv, p, sx, gy + 60, S, cam_pitch=0.06, look=look(O.light_at(sx, heads)))
    Wd.rainfall(cv, t, seed=1, n=150, cx=0, par=1.0)
    return dict(vign=0.7)


# ------------------------------------------------------------------ C: phone, message, window
def C1(cv, t):
    """17.5–19.0 phone vibrates; he pulls it out. Medium close 3/4."""
    blur_layer(cv, 10)
    push(cv, 1.25, W / 2, H * 0.55)
    O.street_layers(cv, 2600, 1500, t)
    cv.restore()
    p = R.Pose(); M.stand(p, t=t, breath=0.0)
    p.yaw = 0.6
    k = M.keys(t, [(17.95, 0.0), (18.6, 1.0)], fn=M.smooth)
    p.hand_abs[1] = V(-30 * k + 120 * (1 - k), 470 + 180 * k, 120 + 160 * k) if k > 0 else None
    p.hand_mode[1] = 'phone' if k > 0.1 else 'relaxed'
    p.head_pitch = M.keys(t, [(17.5, 0.0), (18.0, 0.18), (18.8, 0.42)])
    p.e = M.kexpr(t, [(17.5, EX['terror'] | dict(gx=-1, mopen=0.2)), (18.0, EX['shock'] | dict(gy=-0.6)), (19.0, EX['worried'] | dict(gy=-0.8))], EX)
    p.blink = M.blink_at(t, [17.62])
    p.shake = 0.0
    sx = 560 + shake(t, 4 * (t < 18.1))
    props = {1: phone_prop(glow=M.keys(t, [(18.3, 0.0), (18.7, 1.0)]))} if k > 0.1 else None
    toon.draw(cv, p, sx, 2650, 1.55, cam_pitch=0.0, look=look(0.3, side=1, rim=(150, 170, 220)), ground_shadow=0, props=props)
    if t < 18.25:
        vibrate_rings(cv, sx + 150, 2650 - 1.55 * 420, t, 1.3)
    Wd.rainfall(cv, t, seed=8, n=90, ln=70, alpha=0.3)
    return dict(vign=0.7)


def phone_screen(cv, t, msgs, glitch=None):
    """insert: phone held in two hands, messenger UI. msgs = [(t_arrive, text, color)]"""
    blur_layer(cv, 18)
    O.street_layers(cv, 3000, 1600, t)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 0.35))
    sway = 6 * math.sin(t * 1.3)
    cv.save(); cv.translate(W / 2 + sway, H * 0.47 + 4 * math.sin(t * 1.7)); cv.rotate(-3 + 1.2 * math.sin(t * 0.9))
    pw, ph = 660, 1260
    cv.drawRoundRect(skia.Rect(-pw / 2 - 24, -ph / 2 - 24, pw / 2 + 24, ph / 2 + 24), 70, 70, P((12, 12, 16)))
    scr = skia.Rect(-pw / 2, -ph / 2, pw / 2, ph / 2)
    cv.drawRoundRect(scr, 50, 50, P(shader=lin((0, -ph / 2), (0, ph / 2), (24, 28, 40), (16, 18, 26))))
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(scr, 50, 50))
    cv.drawRect(skia.Rect(-pw / 2, -ph / 2, pw / 2, -ph / 2 + 190), P((34, 38, 54)))
    cv.drawCircle(-pw / 2 + 80, -ph / 2 + 120, 40, P((90, 96, 120)))
    cv.drawString('?', -pw / 2 + 66, -ph / 2 + 140, font(56), P((220, 224, 240)))
    cv.drawString('Неизвестный номер', -pw / 2 + 140, -ph / 2 + 110, font(40), P((236, 238, 246)))
    cv.drawString('+7 (9••) •••-••-••', -pw / 2 + 140, -ph / 2 + 156, font(28), P((140, 146, 170)))
    cv.drawString(f'02:4{7 + int(t // 40)}', -50, -ph / 2 + 44, font(28), P((200, 204, 220)))
    y = -ph / 2 + 260
    for ta, txt, col in msgs:
        if t < ta - 0.9:
            continue
        if t < ta:            # typing dots
            cv.drawRoundRect(skia.Rect(-pw / 2 + 40, y, -pw / 2 + 200, y + 84), 40, 40, P((50, 56, 78)))
            for d in range(3):
                b = 0.4 + 0.6 * max(0, math.sin(t * 9 - d * 0.9))
                cv.drawCircle(-pw / 2 + 85 + d * 36, y + 42, 10, P((200, 206, 230), b))
            break
        u = M.smooth((t - ta) / 0.25)
        f_ = font(54)
        tw = f_.measureText(txt)
        cv.save(); cv.translate(-pw / 2 + 40, y + 50); cv.scale(0.85 + 0.15 * u, 0.85 + 0.15 * u)
        cv.drawRoundRect(skia.Rect(0, -50, tw + 64, 66), 40, 40, P((50, 56, 78), u))
        cv.drawString(txt, 32, 26, f_, P(col, u))
        cv.restore()
        y += 150
    if glitch is not None and glitch[0] <= t < glitch[1]:
        g = (t - glitch[0]) / (glitch[1] - glitch[0])
        cv.drawRect(scr, P((0, 0, 0), 0.92))
        # his face, reflected in the dead screen — with black eyes
        p = R.Pose(); p.e = EX['neutral'] | dict(smile=0.05); p.head_pitch = 0.05
        cv.saveLayer(None, P((255, 255, 255), 0.35 * math.sin(math.pi * g)))
        toon.draw(cv, p, 0, 2050, 2.1, look=toon.Look(tint=(0.6, 0.65, 0.8)), black_eyes=True, ground_shadow=0)
        cv.restore()
        rnd = random.Random(int(t * 30))
        for _ in range(5):
            yy = rnd.uniform(-ph / 2, ph / 2)
            cv.drawRect(skia.Rect(-pw / 2, yy, pw / 2, yy + rnd.uniform(4, 22)), P((180, 200, 255), 0.25))
    cv.restore()
    cv.drawRoundRect(scr, 50, 50, P((255, 255, 255), 0.04))
    cv.restore()
    # thumbs
    for sd in (-1, 1):
        cv.drawOval(skia.Rect(W / 2 + sd * 360 - 70 + sway, H * 0.62, W / 2 + sd * 360 + 70 + sway, H * 0.62 + 260),
                    P(mix(toon.PAL['skin'], (120, 140, 190), 0.25)))
    cv.drawCircle(W / 2, H * 0.47, 900, P(shader=rad((W / 2, H * 0.47), 900, (150, 180, 255), (150, 180, 255), 0.10, 0.0)))
    return dict(vign=0.75)


def C2(cv, t):
    """19.0–22.9 message: «Не оборачивайся.»"""
    push(cv, M.keys(t, [(19.0, 1.0), (22.9, 1.1)], fn=M.smooth), W / 2, H * 0.42)
    return phone_screen(cv, t, [(21.37, 'Не оборачивайся.', (255, 110, 100))])


def C3(cv, t):
    """22.9–24.6 «Ты резко поднимаешь глаза.» close, phone-lit from below"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (18, 20, 34), (8, 9, 16))))
    for i in range(4):
        cv.drawCircle(120 + i * 300, 500 + (i % 2) * 120, 70, P(Wd.SODIUM, 0.25, blur=40))
    p = R.Pose(); M.stand(p, t=t, breath=0.0)
    up = M.keys(t, [(23.05, 0.0), (23.3, 1.0)], fn=lambda u: 1 - (1 - u) ** 3)
    p.head_pitch = 0.42 - 0.5 * up + 0.04 * math.sin(max(0, t - 23.3) * 14) * math.exp(-max(0, t - 23.3) * 5)
    p.e = M.kexpr(t, [(22.9, EX['worried'] | dict(gy=-0.8)), (23.2, EX['shock'] | dict(gy=0.2)), (24.6, EX['mild_fear'] | dict(gy=0.1))], EX)
    p.yaw = 0.15
    lk = toon.Look(key=(0.0, 1.0), rim=(150, 180, 240), rim_w=7, tint=(0.75, 0.82, 1.05))
    lk.rim_dir = (0.0, 1.0)
    toon.draw(cv, p, 540, 3900, 3.3, cam_pitch=0.0, look=lk, ground_shadow=0)
    cv.drawRect(skia.Rect(0, H - 500, W, H), P(shader=lin((0, H - 500), (0, H), (170, 200, 255), (170, 200, 255), 0.0, 0.25)))
    return dict(vign=0.75)


def window_reflection_street(cv, x0, y0, x1, y1, t, cam=0.0):
    """the street behind him, as seen reflected in the glass (mirrored, dim, cool)"""
    cv.save(); cv.clipRect(skia.Rect(x0, y0, x1, y1))
    cv.saveLayer(None, P((255, 255, 255), 0.55))
    cv.translate(x1 + x0, 0); cv.scale(-1, 1)
    blur_layer(cv, 3)
    O.street_layers(cv, 2400 + cam, y1 - 120, t)
    cv.restore()
    cv.restore()
    cv.restore()


def C4(cv, t):
    """24.6–29.4 the window: his reflection, the street behind him — empty"""
    push(cv, M.keys(t, [(24.6, 1.0), (29.4, 1.08)], fn=M.smooth), W * 0.5, H * 0.4)
    F.shop_interior(cv, -100, -200, W + 100, H + 100, t, cam=60)
    window_reflection_street(cv, 0, 0, W, 1500, t)
    # his reflection — for now it copies him exactly
    p = R.Pose(); M.stand(p, t=t, breath=0.35)
    p.head_yaw = M.keys(t, [(24.6, 0.0), (26.9, 0.0), (27.5, 0.32), (28.3, -0.28), (29.0, 0.0)])
    p.e = M.kexpr(t, [(24.6, 'worried'), (26.9, EX['worried'] | dict(gx=0.6)), (28.3, EX['worried'] | dict(gx=-0.6)), (29.4, 'worried')], EX)
    p.blink = M.blink_at(t, [25.5, 28.8])
    q = R.mirror_pose(p)
    lk = toon.Look(key=(0.6, -0.6), rim=(110, 190, 200), rim_w=4, tint=F.GLASS_TINT)
    cv.saveLayer(None, P((255, 255, 255), 0.85))
    toon.draw(cv, q, 470, 2560, 1.62, yaw=-0.22, cam_pitch=0.04, look=lk, ground_shadow=0)
    cv.restore()
    F.glass_fx(cv, 0, 0, W, H, t)
    blur_layer(cv, 22)
    toon.draw(cv, p, 1230, 2700, 1.9, yaw=2.6, cam_pitch=0.0, look=toon.Look(tint=(0.4, 0.45, 0.55)), ground_shadow=0)
    cv.restore()
    return dict(vign=0.7)


def C5(cv, t):
    """29.4–32.6 «Ты выдыхаешь. И вдруг замечаешь странность.» side close, breath on the cold air"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (30, 36, 54), (18, 20, 30))))
    # window edge glow on the left
    cv.drawRect(skia.Rect(0, 0, 260, H), P(shader=lin((0, 0), (260, 0), (120, 200, 190), (120, 200, 190), 0.30, 0.0)))
    p = R.Pose(); M.stand(p, t=t, breath=0.0)
    rel = M.keys(t, [(29.45, 0.0), (30.3, 1.0)], fn=M.smooth)
    p.sh_up = {1: 0.5 - 0.7 * rel, -1: 0.5 - 0.7 * rel}
    p.head_pitch = 0.05 + 0.12 * rel - M.keys(t, [(30.8, 0.0), (31.4, 0.12)])
    p.lean = 0.04 * rel
    p.e = M.kexpr(t, [(29.4, 'worried'), (29.8, EX['calm'] | dict(lid=0.55, mopen=0.25, mround=0.6)), (30.5, EX['calm'] | dict(lid=0.3)),
                      (31.0, EX['calm'] | dict(lid=0.25)), (31.5, EX['confusion'] | dict(gx=-0.8)), (32.6, EX['suspicious'] | dict(gx=-1.0))], EX)
    p.blink = M.blink_at(t, [31.1])
    lk = toon.Look(key=(-0.9, -0.3), rim=(130, 220, 205), rim_w=6, tint=(0.84, 0.92, 1.0))
    lk.rim_dir = (-0.95, -0.2)
    a = toon.draw(cv, p, 600, 3050, 2.35, yaw=-1.05, cam_pitch=0.0, look=lk, ground_shadow=0)
    mx, my = a['mouth']
    Wd.breath_puff(cv, mx - 20, my, (t - 29.7) / 1.6, s=2.2, side=-1)
    Wd.rainfall(cv, t, seed=9, n=60, ln=80, alpha=0.22)
    return dict(vign=0.7)


def C6(cv, t):
    return F.shotA(cv, t)


def C7(cv, t):
    return F.shotB(cv, t)


def C8(cv, t):
    return F.shotC(cv, t)


def C9(cv, t):
    """43.4–45.0 «Ты отскакиваешь от витрины.» wide: he jumps back; the reflection does not"""
    u = t - 43.4
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (34, 38, 58), (22, 24, 36))))
    gx0, gy0, gx1, gy1 = 120, 520, 820, 1420
    F.shop_interior(cv, gx0, gy0, gx1, gy1, t)
    # reflection: still standing calmly, finger at its lips, at the place he was
    q = F.reflection_pose(42.6, None)
    cv.save(); cv.clipRect(skia.Rect(gx0, gy0, gx1, gy1))
    F.draw_reflection(cv, q, 560, 1560, 0.58, yaw=-0.5)
    cv.restore()
    F.glass_fx(cv, gx0, gy0, gx1, gy1, t)
    for r in [(gx0 - 20, gy0 - 20, gx1 + 20, gy0), (gx0 - 20, gy1, gx1 + 20, gy1 + 26), (gx0 - 20, gy0, gx0, gy1), (gx1, gy0, gx1 + 20, gy1)]:
        cv.drawRect(skia.Rect(*r), P((18, 20, 28)))
    F.neon_sign(cv, 150, 470, t, size=80)
    cv.drawRect(skia.Rect(0, gy1 + 26, W, H), P(shader=lin((0, gy1 + 26), (0, H), (46, 50, 72), (26, 28, 40))))
    Wd.wet_reflection(cv, 470, gy1 + 26, F.NEON, w=200, ln=380, a=0.12)
    # him, jumping back toward camera-right
    p = R.Pose(); p.yaw = -2.0
    j = M.keys(t, [(43.4, 0.0), (43.85, 1.0)], fn=lambda x: 1 - (1 - x) ** 2)
    hop = math.sin(math.pi * min(1.0, j)) * 70
    M.stand(p, t=t, breath=0.0)
    p.lean = -0.22 * j + 0.1 * M.keys(t, [(43.85, 0), (45.0, 1)])
    p.pelvis = V(0, hop - 30 * j, 0)
    p.foot[1] = V(R.HIP_W, R.ANKLE_H + hop * 0.6 * (j < 1), -120 * j)
    p.sh_up = {1: 0.8, -1: 0.8}
    for sd in (1, -1):
        p.hand[sd] = V(60 * sd, -230 + 120 * j, 120)
        p.hand_mode[sd] = 'open'
    p.e = EX['terror']
    sx = 620 + 260 * j
    toon.draw(cv, p, sx, 1700, 0.95, cam_pitch=0.05, look=look(0.2, side=-1, rim=(130, 220, 205)))
    Wd.rainfall(cv, t, seed=2, n=80, alpha=0.25)
    return dict(vign=0.66)


# ------------------------------------------------------------------ D: two more messages
def D1(cv, t):
    """45.0–48.9 «Он не за тобой.»"""
    push(cv, M.keys(t, [(45.0, 1.05), (48.9, 1.12)], fn=M.smooth), W / 2, H * 0.42)
    return phone_screen(cv, t, [(19.0, 'Не оборачивайся.', (255, 110, 100)), (47.57, 'Он не за тобой.', (240, 240, 246))])


def D2(cv, t):
    """48.9–50.2 «Ты замираешь.» ECU, frozen; only the pupils shrink"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (16, 18, 30), (8, 9, 16))))
    p = R.Pose(); M.stand(p, t=t, breath=0.0)
    p.head_pitch = 0.22
    p.e = M.kexpr(t, [(48.9, EX['shock'] | dict(gy=-0.7, mopen=0.2)), (50.2, EX['shock'] | dict(gy=-0.7, pupil=0.25, mopen=0.15, sweat=0.9))], EX)
    lk = toon.Look(key=(0.0, 1.0), rim=(150, 180, 240), rim_w=7, tint=(0.75, 0.82, 1.05))
    lk.rim_dir = (0.0, 1.0)
    z = M.keys(t, [(48.9, 4.2), (50.2, 4.6)], fn=M.smooth)
    toon.draw(cv, p, 540, 1250 + 900 * z, z, yaw=0.0, cam_pitch=0.0, look=lk, ground_shadow=0)
    return dict(vign=0.8)


def D3(cv, t):
    """50.2–53.7 «Приходит следующее. Он внутри тебя.» + the dead screen shows his face with black eyes"""
    push(cv, M.keys(t, [(50.2, 1.1), (53.7, 1.22)], fn=M.smooth), W / 2, H * 0.42)
    return phone_screen(cv, t, [(19.0, 'Не оборачивайся.', (255, 110, 100)), (47.57, 'Он не за тобой.', (240, 240, 246)),
                                (51.73, 'Он внутри тебя.', (255, 110, 100))], glitch=(52.95, 53.7))


# ------------------------------------------------------------------ E: lamps die, the run
LAMP_OFF = (56.6, 57.37, 58.2)


def lamp_state(t, toff):
    if t < toff:
        return 1.0
    u = t - toff
    if u < 0.35:
        return 0.15 if int(u * 40) % 3 == 0 else 0.8
    return 0.0


def E1(cv, t):
    """53.7–59.1 the street lamps go out one by one, from far to near"""
    gy = 1460
    z = M.keys(t, [(53.7, 1.0), (59.1, 1.07)], fn=M.smooth)
    push(cv, z, W * 0.55, H * 0.6)
    Wd.sky(cv, (6, 8, 20), (28, 32, 58), gy)
    for i in range(-1, 6):
        Wd.panel_building(cv, i * 300 - 60, 280, gy - 920 - (i * 97) % 200, gy - 150, (30, 34, 56), seed=400 + i, lit=0.12,
                          floor_h=64, t=t, balconies=False)
    Wd.street_ground(cv, gy, 0)
    # three lamps receding to the left, plus one ahead (stays on)
    lamps = [(80, 0.55, LAMP_OFF[0]), (330, 0.75, LAMP_OFF[1]), (640, 1.0, LAMP_OFF[2])]
    dark = 0.0
    for x, sc, toff in lamps:
        on = lamp_state(t, toff)
        dark += (1 - on) / 3
        cv.save(); cv.translate(x, gy + 140); cv.scale(sc, sc); cv.translate(-x, -(gy + 140))
        Wd.lamp(cv, x, gy + 140, 820, on=on, side=1, glow_r=330)
        cv.restore()
        Wd.wet_reflection(cv, x + 100 * sc, gy + 150, Wd.SODIUM, w=30 * sc, ln=300, a=0.25 * on)
    Wd.lamp(cv, 1020, gy + 140, 820, on=1.0, side=-1, glow_r=330)
    # darkness swallowing the street from the left
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (W, 0), (0, 0, 0), (0, 0, 0), 0.75 * dark, 0.0)))
    p = R.Pose(); p.yaw = -0.9
    M.stand(p, t=t, breath=0.0)
    p.sh_up = {1: 0.6, -1: 0.6}
    turn = M.keys(t, [(55.0, 0.0), (56.0, 0.6), (56.8, 0.7), (57.5, 0.85), (58.3, 1.0)])
    p.head_yaw = -0.5 * turn
    p.e = M.kexpr(t, [(53.7, 'mild_fear'), (56.7, EX['shock'] | dict(gx=-1)), (57.4, EX['terror'] | dict(gx=-1)), (59.1, EX['panic'] | dict(gx=-1))], EX)
    p.lean = -0.06 * turn
    p.blink = M.blink_at(t, [54.6])
    toon.draw(cv, p, 780, gy + 60, 0.6, cam_pitch=0.06, look=look(1.0 - 0.6 * dark, side=1))
    Wd.rainfall(cv, t, seed=3, n=140, alpha=0.3)
    return dict(vign=0.6 + 0.2 * dark)


RUN_S = 0.62


def E2(cv, t):
    """59.1–61.0 he bolts: side tracking, lights dead behind, alive ahead"""
    S = RUN_S
    gy = 1480
    cad = lambda x: M.keys(x, [(59.1, 0.6), (59.6, 1.45)], fn=M.smooth)
    amp = lambda x: M.keys(x, [(59.1, 0.4), (59.6, 1.0)], fn=M.smooth)
    ph = integ(lambda x: cad(x) * amp(x), 59.1, t)
    bx = 1529 * S * math.sin(O.YAW1) * ph
    cx = 4000 + bx - M.keys(t, [(59.1, 380), (61.0, 560)])
    heads = O.street_layers(cv, cx, gy, t, flick_lamp=None)
    # kill the lamps already behind him
    sx = bx + 4000 - cx
    cv.drawRect(skia.Rect(0, 0, sx - 160, H), P(shader=lin((0, 0), (sx - 160, 0), (0, 0, 0), (0, 0, 0), 0.8, 0.25)))
    p = R.Pose(); p.yaw = O.YAW1
    M.run(p, integ(cad, 59.1, t), amp=amp(t))
    p.e = EX['panic']
    toon.draw(cv, p, sx, gy + 60, S, cam_pitch=0.06, look=look(0.6, side=1))
    Wd.rainfall(cv, t, seed=1, n=170, cx=cx, par=1.0, alpha=0.36)
    return dict(vign=0.7)


def E3(cv, t):
    """61.0–63.0 «За спиной слышится тяжёлое дыхание.» running at camera; the dark breathes behind him"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (6, 7, 14), (16, 18, 28))))
    for i in range(3):
        cv.drawCircle(200 + i * 340, 640, 50, P(Wd.SODIUM, 0.15, blur=40))
    # the shape's head and shoulders loom out of the dark behind him
    cp = C.CPose(); cp.facing = 0; cp.head_roll = 0.2 + 0.1 * math.sin(t * 1.3); cp.bend = 0.25
    blur_layer(cv, 4)
    C.draw(cv, cp, 560 + 30 * math.sin(t * 2), 3400, 3600, t=t, alpha=0.9, rim=(60, 70, 100), smoke=1.0)
    cv.restore()
    for k in range(4):     # its breath: cold clouds pushing past his head
        Wd.breath_puff(cv, 520, 520, ((t - 61.0) * 0.9 + k * 0.25) % 1.0, s=2.4, side=1 if k % 2 else -1)
    p = R.Pose(); p.yaw = 0.25
    M.run(p, (t - 61.0) * 1.45, amp=0.85, exhaustion=0.6)
    p.e = EX['panic'] | dict(gx=-0.6 * math.sin(t * 3))
    p.head_yaw = 0.2 * math.sin(t * 2.4)
    a = toon.draw(cv, p, 540 + 30 * math.sin(t * 9), 3000 + 20 * math.sin(t * 18), 2.2, cam_pitch=0.0,
                  look=look(0.4, side=1, rim=(120, 140, 200)), ground_shadow=0)
    mx, my = a['mouth']
    Wd.breath_puff(cv, mx, my, ((t - 61.0) * 2.8) % 1.0, s=1.6, side=-1)
    Wd.rainfall(cv, t, seed=11, n=120, ln=90, alpha=0.35)
    return dict(vign=0.8)


# ------------------------------------------------------------------ F: courtyard, collision, the double
YARD_GY = 1500


def courtyard(cv, t, cx=0.0, lamp_on=1.0, gy=YARD_GY, moon=True):
    Wd.sky(cv, (6, 8, 22), (30, 34, 60), gy)
    if moon:
        Wd.moon(cv, 840 - cx * 0.1, 260, 44)
    # nine-storey blocks around the yard
    Wd.panel_building(cv, -200 - cx * 0.5, 760, gy - 1180, gy - 40, (40, 44, 70), seed=501, lit=0.08, floor_h=120, t=t)
    Wd.panel_building(cv, 640 - cx * 0.5, 700, gy - 1120, gy - 40, (36, 40, 64), seed=502, lit=0.06, floor_h=120, t=t)
    cv.drawRect(skia.Rect(0, gy - 400, W, gy - 40), P(shader=lin((0, gy - 400), (0, gy - 40), (50, 56, 88), (50, 56, 88), 0.0, 0.4)))
    # ground: packed snow-less dirt + asphalt path
    cv.drawRect(skia.Rect(0, gy - 50, W, H), P(shader=lin((0, gy - 50), (0, H), (40, 42, 58), (20, 21, 30))))
    cv.drawPath(path_poly([(0, gy + 60), (W, gy + 20), (W, gy + 160), (0, gy + 220)]), P((54, 58, 78)))
    # playground: swing frame + slide, parallax 1
    x = 140 - cx
    cv.drawLine(x, gy - 10, x + 120, gy - 420, P((26, 28, 40), style='stroke', width=14))
    cv.drawLine(x + 240, gy - 10, x + 120, gy - 420, P((26, 28, 40), style='stroke', width=14))
    cv.drawLine(x + 120, gy - 420, x + 560, gy - 420, P((26, 28, 40), style='stroke', width=14))
    cv.drawLine(x + 440, gy - 10, x + 560, gy - 420, P((26, 28, 40), style='stroke', width=14))
    cv.drawLine(x + 680, gy - 10, x + 560, gy - 420, P((26, 28, 40), style='stroke', width=14))
    sw = 0.12 * math.sin(t * 1.1)   # the empty swing moves on its own
    for k in (300, 380):
        cv.drawLine(x + k, gy - 420, x + k + 260 * math.sin(sw), gy - 420 + 260 * math.cos(sw), P((60, 62, 80), style='stroke', width=4))
    sx_, sy_ = x + 340 + 260 * math.sin(sw), gy - 420 + 260 * math.cos(sw)
    cv.drawRect(skia.Rect(sx_ - 60, sy_ - 6, sx_ + 60, sy_ + 10), P((70, 40, 44)))
    Wd.tree(cv, 980 - cx * 1.0, gy + 10, 760, seed=31)
    hx, hy = Wd.lamp(cv, 900 - cx, gy + 120, 760, on=lamp_on, side=-1, glow_r=420)
    return hx, hy


def F1(cv, t):
    """63.0–65.8 he turns into the yard and slams into someone"""
    S = 0.7
    gy = YARD_GY
    hit = 64.9
    cx = M.keys(t, [(63.0, 200), (64.9, 40), (65.8, 20)], fn=M.smooth)
    courtyard(cv, t, cx=cx)
    dbl_x = 430 - cx
    # the stranger: back-lit, dark — we must not recognise him yet
    pd = R.Pose(); M.stand(pd, t=t, breath=0.0); pd.yaw = 1.57
    pd.e = EX['neutral']; pd.blink = 1.0
    rec = M.keys(t, [(hit, 0.0), (hit + 0.25, 1.0), (hit + 0.9, 0.6)], fn=M.smooth)
    pd.lean = -0.05 * rec
    toon.draw(cv, pd, dbl_x, gy + 120, S, cam_pitch=0.06, look=toon.Look(key=(0.8, -0.4), tint=(0.25, 0.27, 0.36)), black_eyes=True)
    # him: runs in from the right toward the left, turns the corner, collides, staggers back
    p = R.Pose()
    if t < hit:
        ph = (t - 63.0) * 1.5
        M.run(p, ph, amp=0.95, exhaustion=0.7)
        p.yaw = -1.57
        bx = M.keys(t, [(63.0, 1350), (hit, dbl_x + 150 + cx)], fn=lambda u: u)
        STEP_TRACK = None
    else:
        M.stand(p, t=t, breath=0.0); p.yaw = -1.57
        k = M.keys(t, [(hit, 0.0), (hit + 0.35, 1.0)], fn=lambda u: 1 - (1 - u) ** 2)
        bx = dbl_x + 150 + cx + 170 * k
        p.lean = -0.25 * k + 0.45 * M.keys(t, [(hit + 0.35, 0.0), (65.8, 1.0)], fn=M.smooth)
        p.foot[1] = V(R.HIP_W, R.ANKLE_H, 80 * k)
        p.head_pitch = 0.35 * M.keys(t, [(hit + 0.3, 0.0), (65.6, 1.0)])
        for sd in (1, -1):
            p.hand[sd] = V(40 * sd, -260 + 60 * k, 120 * k)
        p.hand_mode = {1: 'open', -1: 'open'}
        p.e = M.kexpr(t, [(hit, 'pain'), (hit + 0.5, EX['pain'] | dict(lid=0.4)), (65.8, EX['exhausted'] | dict(gy=-0.8))], EX)
    if t < hit:
        p.e = EX['panic'] | dict(gx=0.8)
    toon.draw(cv, p, bx - cx, gy + 140, S, cam_pitch=0.06, look=look(0.6, side=1))
    if hit <= t < hit + 0.12:
        cv.drawRect(skia.Rect(0, 0, W, H), P((255, 255, 255), 0.18 * (1 - (t - hit) / 0.12)))
    Wd.rainfall(cv, t, seed=12, n=110, alpha=0.3)
    return dict(vign=0.72)


def F2(cv, t):
    """65.8–67.0 «Поднимаешь голову.» close: his head comes up slowly"""
    courtyard(cv, t, cx=600, moon=False)
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 0.25))
    p = R.Pose(); M.stand(p, t=t, breath=0.0); p.yaw = -0.35
    up = M.keys(t, [(65.8, 0.0), (66.9, 1.0)], fn=M.smooth)
    p.head_pitch = 0.45 - 0.62 * up
    p.lean = 0.12 * (1 - up)
    p.e = M.kexpr(t, [(65.8, EX['exhausted'] | dict(gy=-0.9)), (66.5, EX['exhausted'] | dict(gy=0.4, lid=0.2)), (67.0, EX['worried'] | dict(gy=0.6))], EX)
    toon.draw(cv, p, 560, 3600, 2.9, cam_pitch=-0.05, look=look(0.5, side=1), ground_shadow=0)
    return dict(vign=0.75)


def F3(cv, t):
    """67.0–69.6 «Перед тобой стоишь ты сам.» low angle on the double: lamp light finds his face"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (8, 10, 24), (30, 34, 58))))
    Wd.moon(cv, 820, 320, 40)
    Wd.panel_building(cv, -100, 1300, 300, 2100, (30, 34, 56), seed=601, lit=0.05, floor_h=150, t=t)
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (0, 0, 0), (0, 0, 0), 0.0, 0.5)))
    reveal = M.keys(t, [(67.6, 0.0), (68.7, 1.0)], fn=M.smooth)
    pd = R.Pose(); M.stand(pd, t=t, breath=0.0); pd.yaw = 0.05
    pd.e = EX['neutral'] | dict(smile=0.0); pd.blink = 1.0
    pd.head_pitch = 0.18
    tint = tuple(0.28 + (v - 0.28) * reveal for v in (1.0, 0.95, 0.88))
    z = M.keys(t, [(67.0, 1.0), (69.6, 1.06)], fn=M.smooth)
    push(cv, z, W / 2, H * 0.3)
    toon.draw(cv, pd, 540, 2650, 1.85, cam_pitch=-0.28, look=toon.Look(key=(-0.5, -0.9), rim=(255, 200, 140), rim_w=6, tint=tint),
              black_eyes=True, ground_shadow=0)
    Wd.rainfall(cv, t, seed=13, n=90, alpha=0.3)
    return dict(vign=0.78)


def F4(cv, t):
    """69.6–71.7 «Та же одежда. То же лицо.» profile two-shot, tilt from shoes to faces"""
    gy = 2600
    tilt = M.keys(t, [(69.6, 0.0), (71.5, 1.0)], fn=M.smooth)
    cv.translate(0, -900 + 900 * tilt)
    cv.drawRect(skia.Rect(0, -1200, W, 3000), P(shader=lin((0, -1200), (0, 3000), (10, 12, 26), (34, 38, 60))))
    cv.drawCircle(540, 600, 460, P(Wd.SODIUM, 0.12, blur=160))
    cv.drawRect(skia.Rect(0, gy - 20, W, 3000), P((32, 34, 48)))
    p = R.Pose(); M.stand(p, t=t, breath=0.3); p.e = EX['shock'] | dict(gx=0.0)
    pd = R.Pose(); M.stand(pd, t=t, breath=0.0); pd.e = EX['neutral'] | dict(smile=0.0); pd.blink = 1.0
    p.head_pitch = -0.05; pd.head_pitch = 0.02
    lk = toon.Look(key=(0.0, -1.0), rim=(255, 200, 140), rim_w=5, tint=(0.9, 0.88, 0.86))
    toon.draw(cv, p, 260, gy, 1.75, yaw=1.2, cam_pitch=0.0, look=lk)
    toon.draw(cv, pd, 820, gy, 1.75, yaw=-1.2, cam_pitch=0.0, look=lk, black_eyes=True)
    return dict(vign=0.72)


def F5(cv, t):
    """71.7–74.8 «Только глаза совершенно чёрные.» ECU: his eyes open"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (16, 14, 22), (6, 6, 10))))
    pd = R.Pose(); M.stand(pd, t=t, breath=0.0)
    op = M.keys(t, [(72.75, 0.0), (73.15, 1.0)], fn=M.smooth)
    pd.blink = 1.0 - op
    pd.e = EX['neutral'] | dict(smile=0.0, lid=0.05)
    z = M.keys(t, [(71.7, 4.0), (74.8, 4.7)], fn=M.smooth)
    lk = toon.Look(key=(-0.6, -0.8), rim=(255, 200, 140), rim_w=6, tint=(0.95, 0.9, 0.86))
    toon.draw(cv, pd, 540, 960 + 900 * z, z, yaw=0.0, cam_pitch=0.0, look=lk, black_eyes=True, ground_shadow=0)
    return dict(vign=0.85)


# --- the grab: profile two-shot, double on the right facing left
def grab_pair(cv, t, X, Y, S, grab, struggle=0.0, dbl_gaze=0.0, dbl_expr=None, boy_expr=None, cam_pitch=0.04, boy_yaw=1.57, dbl_yaw=-1.57):
    p = R.Pose(); M.stand(p, t=t, breath=0.0); p.yaw = boy_yaw
    p.sh_up = {1: 0.4 + 0.4 * grab, -1: 0.4 + 0.4 * grab}
    p.lean = -0.06 * grab - 0.12 * struggle * (0.5 + 0.5 * math.sin(t * 7))
    p.twist = 0.3 * struggle * math.sin(t * 5.3)
    p.head_yaw = 0.25 * struggle * math.sin(t * 6.1 + 1)
    for sd in (1, -1):
        p.hand[sd] = V(36 * sd, -280 + 100 * struggle, 140 + 80 * struggle * (0.5 + 0.5 * math.sin(t * 6 + sd)))
        p.hand_mode[sd] = 'fist' if struggle > 0.2 else 'relaxed'
    p.e = boy_expr or EX['shock']
    pd = R.Pose(); M.stand(pd, t=t, breath=0.0); pd.yaw = dbl_yaw
    pd.lean = 0.08 * grab
    pd.head_pitch = -0.28 * dbl_gaze
    pd.e = dbl_expr or EX['neutral'] | dict(smile=0.0)
    if grab > 0:
        for sd in (1, -1):
            pd.hand_abs[sd] = V(sd * 120 + (1 - grab) * sd * 40, 560 + 220 * grab, 140 + 200 * grab)
            pd.hand_mode[sd] = 'grip'
    gap = 330 * S
    bx = X - gap / 2 - 28 * S * struggle * math.sin(t * 7)
    lk = toon.Look(key=(0.2, -0.9), rim=(255, 200, 140), rim_w=5)
    toon.draw(cv, p, bx, Y, S, cam_pitch=cam_pitch, look=lk)
    toon.draw(cv, pd, X + gap / 2, Y, S, cam_pitch=cam_pitch, look=lk, black_eyes=True)


def G1(cv, t):
    """74.8–77.5 the double grabs him by the shoulders and whispers"""
    z = M.keys(t, [(74.8, 1.0), (77.5, 1.1)], fn=M.smooth)
    push(cv, z, W / 2, H * 0.45)
    courtyard(cv, t, cx=200, moon=True)
    grab = M.keys(t, [(74.95, 0.0), (75.3, 1.0)], fn=lambda u: 1 - (1 - u) ** 3)
    ex = M.kexpr(t, [(74.8, EX['shock']), (75.3, EX['terror'])], EX)
    dex = EX['serious'] | dict(mopen=0.35 * voice(t) if t > 76.6 else 0.0)
    grab_pair(cv, t, 540, 1720, 0.95, grab, dbl_expr=dex, boy_expr=ex)
    Wd.rainfall(cv, t, seed=14, n=110, alpha=0.3)
    return dict(vign=0.72)


def G2(cv, t):
    """77.5–81.5 «Слушай внимательно. Ты должен перестать убегать.» close on the double, over his shoulder"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (12, 14, 28), (28, 30, 50))))
    cv.drawCircle(300, 500, 380, P(Wd.SODIUM, 0.16, blur=140))
    pd = R.Pose(); M.stand(pd, t=t, breath=0.0); pd.yaw = -0.35
    pd.e = EX['serious'] | dict(mopen=0.45 * voice(t), mw=0.75, brow=-0.05)
    pd.head_pitch = 0.04 + 0.02 * math.sin(t * 2)
    pd.blink = 0.0
    for sd in (1, -1):
        pd.hand_abs[sd] = V(sd * 120, 780, 340)
        pd.hand_mode[sd] = 'grip'
    z = M.keys(t, [(77.5, 2.7), (81.5, 3.0)], fn=M.smooth)
    lk = toon.Look(key=(-0.6, -0.8), rim=(255, 200, 140), rim_w=6)
    toon.draw(cv, pd, 720, 1100 + 900 * z, z, cam_pitch=0.0, look=lk, black_eyes=True, ground_shadow=0)
    # his shoulder and the back of his head, soft, foreground left
    blur_layer(cv, 18)
    p = R.Pose(); M.stand(p, t=t, breath=0.0); p.yaw = 2.6
    toon.draw(cv, p, -80, 1000 + 900 * 3.4, 3.4, cam_pitch=0.0, look=toon.Look(tint=(0.45, 0.48, 0.6)), ground_shadow=0)
    cv.restore()
    return dict(vign=0.8)


def G3(cv, t):
    """81.5–85.0 he struggles; the double looks past him"""
    courtyard(cv, t, cx=200, moon=True)
    gaze = M.keys(t, [(82.9, 0.0), (84.2, 1.0)], fn=M.smooth)
    st = M.keys(t, [(81.5, 0.0), (81.8, 1.0), (83.6, 1.0), (84.4, 0.2)])
    dex = M.kexpr(t, [(81.5, EX['serious']), (82.9, EX['serious']), (84.6, EX['worried'] | dict(gy=0.8))], EX)
    bex = EX['panic'] | dict(gx=0.3)
    z = M.keys(t, [(81.5, 1.12), (85.0, 1.2)], fn=M.smooth)
    push(cv, z, W / 2, H * 0.45)
    grab_pair(cv, t, 540, 1720, 0.95, 1.0, struggle=st, dbl_gaze=gaze, dbl_expr=dex, boy_expr=bex)
    Wd.rainfall(cv, t, seed=15, n=110, alpha=0.3)
    return dict(vign=0.74)


def G4(cv, t):
    """85.0–90.2 «Его лицо меняется. Впервые он выглядит по-настоящему испуганным.»"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (14, 14, 26), (6, 6, 12))))
    pd = R.Pose(); M.stand(pd, t=t, breath=0.0)
    pd.head_pitch = -0.22
    pd.e = M.kexpr(t, [(85.0, EX['worried'] | dict(gy=0.9)), (86.5, EX['mild_fear'] | dict(gy=0.9)),
                       (88.1, EX['terror'] | dict(gy=0.9, mopen=0.35, smile=-0.7, mround=0.6, mw=0.7)), (90.2, EX['terror'] | dict(gy=0.9, mopen=0.4, smile=-0.75, mround=0.7, mw=0.7, tear=0.6))], EX)
    tremble = M.keys(t, [(87.5, 0.0), (89.0, 1.0)])
    z = M.keys(t, [(85.0, 3.1), (90.2, 3.7)], fn=M.smooth)
    lk = toon.Look(key=(-0.6, -0.8), rim=(150, 170, 230), rim_w=6, tint=(0.82, 0.86, 1.0))
    toon.draw(cv, pd, 540 + shake(t, 5 * tremble, 31), 1000 + 920 * z, z, cam_pitch=-0.08, look=lk, black_eyes=True, ground_shadow=0)
    return dict(vign=0.85)


def G5(cv, t):
    """90.2–93.0 «Нет. Он нашёл нас обоих.» tight two-shot"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (12, 14, 28), (24, 26, 44))))
    cv.drawCircle(540, 500, 420, P(Wd.SODIUM, 0.12, blur=150))
    let_go = M.keys(t, [(91.0, 0.0), (92.6, 0.5)])
    dex = EX['terror'] | dict(gy=0.8, mopen=0.1 + 0.4 * voice(t), mw=0.7, smile=-0.7, mround=0.5)
    grab_pair(cv, t, 540, 2600, 1.75, 1.0 - let_go, boy_yaw=1.95, dbl_yaw=-1.05, dbl_gaze=1.0, dbl_expr=dex, boy_expr=EX['terror'] | dict(gx=0.6))
    return dict(vign=0.8)


# ------------------------------------------------------------------ H: the rooftop
def H1(cv, t):
    """93.0–95.2 «Ты медленно поворачиваешь голову.»"""
    courtyard(cv, t, cx=500, moon=False)
    blur_layer(cv, 0.1)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 0.3))
    p = R.Pose(); M.stand(p, t=t, breath=0.0); p.yaw = 0.1
    turn = M.keys(t, [(93.2, 0.0), (95.1, 1.0)], fn=M.smooth)
    p.head_yaw = 1.25 * turn
    p.head_pitch = -0.15 * turn
    p.twist = 0.25 * turn
    p.e = EX['terror'] | dict(gx=1.0 * turn, gy=0.3 * turn, mopen=0.2)
    toon.draw(cv, p, 540, 3400, 2.5, cam_pitch=0.0, look=look(0.4, side=1), ground_shadow=0)
    # the double's hand still on his shoulder, entering frame left
    cv.drawOval(skia.Rect(-60, 1450, 140, 1640), P(mix(toon.PAL['skin'], (40, 40, 60), 0.4)))
    return dict(vign=0.8)


def ninestorey(cv, x, w, top, base, t, col=(30, 34, 56)):
    Wd.panel_building(cv, x, w, top, base, col, seed=777, lit=0.05, floor_h=(base - top) / 9.4, t=t, dark=False)


def H2(cv, t):
    """95.2–98.9 «На крыше девятиэтажки стоит огромная чёрная фигура.» low angle wide, tilt up"""
    tilt = M.keys(t, [(95.2, 0.0), (97.8, 1.0)], fn=M.smooth)
    cv.translate(0, -960 + 1440 * tilt)
    cv.drawRect(skia.Rect(0, -700, W, 3000), P(shader=lin((0, -700), (0, 2700), (6, 8, 22), (34, 38, 64))))
    Wd.moon(cv, 760, 220, 64)
    for i in range(30):
        rnd = random.Random(i)
        cv.drawCircle(rnd.uniform(0, W), rnd.uniform(0, 600), rnd.uniform(1, 2.5), P((220, 224, 240), 0.6))
    # building in strong low-angle perspective (narrower at the top)
    top, base = 820, 2620
    cv.save()
    m = skia.Matrix()
    m.setPolyToPoly([skia.Point(0, top), skia.Point(W, top), skia.Point(W, base), skia.Point(0, base)],
                    [skia.Point(140, top), skia.Point(W - 140, top), skia.Point(W + 120, base), skia.Point(-120, base)])
    cv.concat(m)
    ninestorey(cv, 0, W, top, base, t)
    cv.restore()
    # the figure on the roof edge, against the moon
    cp = C.CPose(); cp.facing = 0; cp.head_roll = 0.15 * math.sin(t * 0.6)
    cp.breathe = t
    C.draw(cv, cp, 560, top - 6, 1150, t=t, alpha=1.0, rim=(170, 180, 220), rim_dir=(0.4, -0.9), smoke=1.0)
    cv.drawRect(skia.Rect(-200, base - 10, W + 200, 3000), P(shader=lin((0, base), (0, 2900), (38, 40, 56), (20, 21, 30))))
    # the two of them, tiny, backs to us, at the bottom
    for i, be in enumerate((False, True)):
        p = R.Pose(); M.stand(p, t=t, breath=0.0); p.yaw = math.pi + (0.15 if i else -0.15)
        p.head_pitch = -0.4
        toon.draw(cv, p, 440 + i * 220, 2640, 0.55, cam_pitch=-0.1, look=toon.Look(tint=(0.4, 0.42, 0.55)), black_eyes=be, ground_shadow=0)
    cv.restore() if False else None
    return dict(vign=0.7)


def H3(cv, t):
    """98.9–102.6 «Она наклоняется вниз и произносит твоим голосом.»"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (6, 8, 22), (24, 28, 50))))
    Wd.moon(cv, 840, 300, 90)
    bend = M.keys(t, [(99.0, 0.0), (101.6, 1.0)], fn=M.smooth)
    # roof edge (we look up the facade)
    cv.drawPath(path_poly([(0, 1150), (W, 1080), (W, H), (0, H)]), P((26, 30, 50)))
    for r in range(4):
        y = 1260 + r * 200
        for c in range(5):
            x = 40 + c * 210
            cv.drawRect(skia.Rect(x, y - c * 14, x + 120, y + 90 - c * 14), P((18, 20, 34)))
    cv.drawRect(skia.Rect(0, 1120, W, 1170), P((40, 44, 70)))
    cp = C.CPose(); cp.facing = 1; cp.bend = bend; cp.head_roll = 0.3 * bend; cp.neck_fwd = 0.25 + 0.4 * bend
    cp.reach = {1: 0.5 * bend, -1: 0.8 * bend}
    z = M.keys(t, [(98.9, 1.0), (102.6, 1.18)], fn=M.smooth)
    push(cv, z, W / 2, H * 0.45)
    C.draw(cv, cp, 380, 1130, 1350, t=t, alpha=1.0, rim=(170, 180, 220), rim_dir=(0.5, -0.8), smoke=1.0)
    # when it speaks, a ripple of cold breath from where its face would be
    v = voice(t) if t > 100.5 else 0.0
    if v > 0.05:
        cv.drawCircle(760, 820, 120 + 200 * v, P((160, 170, 210), 0.10 * v, blur=60))
    return dict(vign=0.8)


def H4(cv, t):
    """102.6–105.33 «Кто из вас настоящий?» high angle from the roof: two of them, side by side"""
    z = M.keys(t, [(102.6, 1.0), (105.33, 1.25)], fn=M.smooth)
    push(cv, z, W / 2, H * 0.55)
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (30, 32, 46), (20, 22, 32))))
    # courtyard ground from above: path, puddles, swing shadow
    cv.drawPath(path_poly([(0, 900), (W, 700), (W, 1200), (0, 1400)]), P((44, 48, 64)))
    cv.drawOval(skia.Rect(160, 1400, 520, 1520), P((54, 64, 96)))
    cv.drawCircle(860, 400, 520, P(Wd.SODIUM, 0.14, blur=160))
    # the creature's shadow spreading over them
    sh = M.keys(t, [(102.6, 0.2), (105.3, 1.0)])
    cv.drawOval(skia.Rect(540 - 900 * sh, -300, 540 + 900 * sh, 1100 + 900 * sh), P((0, 0, 0), 0.55, blur=80))
    for i, be in enumerate((False, True)):
        p = R.Pose(); M.stand(p, t=t, breath=0.0); p.yaw = -0.2 if i == 0 else 0.25
        p.head_pitch = -0.55
        p.sh_up = {1: 0.8, -1: 0.8}
        p.e = EX['terror'] | dict(gy=1.0, mopen=0.4) if not be else EX['terror'] | dict(gy=1.0, mopen=0.3)
        toon.draw(cv, p, 360 + i * 380 + shake(t, 3, 27 + i), 1420, 0.85, cam_pitch=0.65, look=toon.Look(tint=(0.7, 0.72, 0.85)), black_eyes=be)
    Wd.rainfall(cv, t, seed=17, n=150, alpha=0.3)
    return dict(vign=0.82)


def END(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0)))
    return dict(vign=0.0, grain=0.0, lift=(0, 0, 0))


# ------------------------------------------------------------------ timeline
SHOTS = [
    (0.0, 4.7, O.shot1), (4.7, 6.25, O.shot2), (6.25, 9.2, A3), (9.2, 11.9, B1), (11.9, 14.3, B2), (14.3, 17.5, B3),
    (17.5, 19.0, C1), (19.0, 22.9, C2), (22.9, 24.6, C3), (24.6, 29.4, C4), (29.4, 32.6, C5), (32.6, 38.5, C6),
    (38.5, 42.6, C7), (42.6, 43.4, C8), (43.4, 45.0, C9), (45.0, 48.9, D1), (48.9, 50.2, D2), (50.2, 53.7, D3),
    (53.7, 59.1, E1), (59.1, 61.0, E2), (61.0, 63.0, E3), (63.0, 65.8, F1), (65.8, 67.0, F2), (67.0, 69.6, F3),
    (69.6, 71.7, F4), (71.7, 74.8, F5), (74.8, 77.5, G1), (77.5, 81.5, G2), (81.5, 85.0, G3), (85.0, 90.2, G4),
    (90.2, 93.0, G5), (93.0, 95.2, H1), (95.2, 98.9, H2), (98.9, 102.6, H3), (102.6, 105.33, H4), (105.33, DUR + 1, END),
]


def frame(cv, t):
    for a, b, fn in SHOTS:
        if a <= t < b:
            return fn(cv, t)
    return END(cv, t)
