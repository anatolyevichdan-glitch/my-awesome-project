"""LAST PASSENGER — EP1, scenes 4-8 (36.14 s → end)."""
from common import *
from rig import V
import rig as R
import motion as M
import sc1 as S1


# ------------------------------------------------------------------ helpers
def head_off(p, s, yaw, cam_pitch=0.10):
    cam = R.Cam(0.0, 0.0, s, yaw, cam_pitch, 0.0, False)
    h = cam.proj(R.solve(p).H)[0]
    return h[0], h[1]


def figh(cv, name, p, hx, hy, s, yaw, lk=None, **kw):
    """draw a figure so that its head centre lands on (hx, hy)"""
    ox, oy = head_off(p, s, yaw)
    kw.setdefault('ground_shadow', 0)
    return fig(cv, name, p, hx - ox, hy - oy, s, yaw=yaw, lk=lk, **kw)


def phone_prop(lit=1.0):
    def fn(cv, hp, cam, S, sd):
        x, y = hp if isinstance(hp, tuple) else (hp[0], hp[1])
        w, h = 34 * cam.s, 66 * cam.s
        cv.save(); cv.translate(x, y - h * 0.25); cv.rotate(-12)
        cv.drawRoundRect(skia.Rect(-w, -h, w, h), 10 * cam.s, 10 * cam.s, P((16, 16, 20)))
        if lit > 0:
            cv.drawRoundRect(skia.Rect(-w + 5 * cam.s, -h + 6 * cam.s, w - 5 * cam.s, h - 6 * cam.s), 7 * cam.s, 7 * cam.s, P((120, 150, 220), 0.6 * lit))
        cv.restore()
    return fn


def wet_glass(cv, rect, t, n=30, seed=4, a=0.18):
    r = random.Random(seed)
    for i in range(n):
        x = r.uniform(rect.left(), rect.right())
        y = rect.top() + (r.uniform(0, rect.height()) + t * r.uniform(8, 60)) % rect.height()
        rd = r.uniform(4, 12)
        cv.drawCircle(x, y, rd, P((200, 214, 240), a))
        cv.drawCircle(x - rd * 0.3, y - rd * 0.3, rd * 0.3, P((255, 255, 255), a * 1.3))


def windshield(cv, t, x0, y0, x1, y1, speed=1.0):
    """night road seen through the windshield: headlight cone, dashes, rain."""
    cv.save(); cv.clipRect(skia.Rect(x0, y0, x1, y1))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(shader=lin((0, y0), (0, y1), (6, 8, 18), (16, 20, 34))))
    hy = y0 + (y1 - y0) * 0.42
    cx = (x0 + x1) / 2
    road = path_poly([(cx - 30, hy), (cx + 30, hy), (x1 + 400, y1), (x0 - 400, y1)])
    cv.drawPath(road, P(shader=lin((0, hy), (0, y1), (20, 22, 30), (70, 70, 72))))
    cv.drawPath(road, P((255, 230, 170), 0.10, blur=40))
    for i in range(8):
        k = ((i / 8.0) + t * 0.55 * speed) % 1.0
        kk = k * k
        yy = hy + (y1 - hy) * kk
        hw = 3 + 26 * kk
        cv.drawRect(skia.Rect(cx - hw, yy, cx + hw, yy + 6 + 120 * kk), P((220, 210, 170), 0.7 * min(1, k * 3)))
    for i in range(-1, 4):          # passing lamps
        k = ((i / 3.0) + t * 0.3 * speed) % 1.0
        lx = cx + (x1 - cx + 300) * k * k
        ly = hy - (hy - y0 + 100) * k * k
        cv.drawCircle(lx, ly, 8 + 60 * k * k, P(E.SODIUM, 0.55, blur=20))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P((140, 160, 200), 0.05))
    Wd.rainfall(cv, t, seed=9, n=110, alpha=0.3, ln=30, area=(x0, y0, x1, y1))
    wet_glass(cv, skia.Rect(x0, y0, x1, y1), t, n=40, seed=11, a=0.16)
    cv.restore()


def cab_bg(cv, t, top=260, bot=1150, L=1.0):
    """front of the bus seen from behind the driver: dashboard, windshield, pillars"""
    cv.drawRect(skia.Rect(0, 0, W, H), P(mix((10, 14, 14), (50, 64, 58), L)))
    windshield(cv, t, -20, top, W + 20, bot)
    cv.drawRect(skia.Rect(-20, top - 30, W + 20, top + 10), P((24, 28, 28)))
    cv.drawRect(skia.Rect(-20, bot - 10, W + 20, bot + 240), P((30, 32, 34)))          # dashboard
    cv.drawRect(skia.Rect(-20, bot - 10, W + 20, bot + 6), P((90, 96, 96)))
    for x, c in ((180, (230, 120, 40)), (240, (90, 200, 120)), (880, (220, 60, 50))):
        cv.drawCircle(x, bot + 60, 10, P(c, 0.9))
        cv.drawCircle(x, bot + 60, 30, P(c, 0.25, blur=14))
    # route plate "13"
    r = skia.Rect(W - 300, top + 20, W - 120, top + 110)
    cv.drawRect(r, P((14, 14, 16)))
    E.text_c(cv, '13', r.centerX(), r.bottom() - 18, 64, (250, 170, 50))


def babka_pose(t, e, talk=0.0, pitch=0.2, yaw=0.0):
    p = R.Pose(); M.sit(p, t=t, breath=0.05)
    p.e = e; p.talk = talk; p.head_pitch = pitch; p.head_yaw = yaw
    return p


BABKA_LK = dict(key=(0.0, -1.0), rim=None, tint=(0.62, 0.68, 0.64))


def cabin_people(cv, cam, t, look=+1, babka_e=None, babka_talk=0.0, babka_pitch=0.3, hl=None, black=False,
                 jolt=0.0, heads=None, babka=True, pax_turn=0.0):
    """six passengers + babka at the rear; hl = index being counted (0..6) lights that person."""
    items = []
    for i, (x, z, nm) in enumerate(S1.PAX):
        def fn(x=x, z=z, nm=nm, i=i):
            X, Y, s = E.person_at(cam, x, z - 30)
            p = R.Pose(); M.sit(p, t=t, breath=0.0)
            p.e = EX['blank']
            p.head_pitch = 0.18 + 0.05 * (i % 2) - 0.25 * pax_turn
            p.head_yaw = [0.05, -0.1, 0.0, 0.12, -0.05, 0.0][i] * (1 - pax_turn)
            p.lean = 0.25 * jolt
            if nm == 'pax2':
                p.head_roll = 0.7 * (1 - pax_turn); p.head_pitch = 0.55 * (1 - pax_turn)
            lk = None
            if hl is not None:
                lk = LK(key=(0.0, -1.0), rim=E.FLUO, tint=(1.05, 1.08, 1.05) if hl == i else (0.55, 0.6, 0.58))
            A = fig(cv, nm, p, X, Y, s, yaw=0.0 if look > 0 else math.pi, ground_shadow=0, lk=lk, black_eyes=black)
            if heads is not None:
                heads[i] = (A['head'], A['head_r'])
        items.append((z, fn))
    if babka:
        def bab():
            X, Y, s = E.person_at(cam, 0, E.REAR_Z - 30)
            p = babka_pose(t, babka_e or EX['babka_calm'], babka_talk, babka_pitch)
            tint = BABKA_LK['tint'] if hl is None else ((1.0, 1.05, 1.0) if hl == 6 else (0.5, 0.55, 0.52))
            A = fig(cv, 'babka', p, X, Y, s, yaw=0.0 if look > 0 else math.pi, ground_shadow=0,
                    lk=LK(key=(0.0, -1.0), rim=None, tint=tint))
            if heads is not None:
                heads[6] = (A['head'], A['head_r'])
        items.append((E.REAR_Z, bab))
    return items


def driver_pose(t, head_yaw=0.0, e=None):
    p = R.Pose(); M.sit(p, t=t, breath=0.0)
    p.head_yaw = head_yaw
    p.e = e or EX['closed']
    for sd in (1, -1):
        p.hand[sd] = V(40 * sd, -150, 260)
    return p


DRV_LK = dict(key=(0.3, -0.9), rim=(150, 180, 230), rim_w=6, tint=(0.82, 0.9, 0.9))


# ------------------------------------------------------------------ D: driver / babka
def D1(cv, t):
    """36.14–38.12 «Ты касаешься его плеча.» over-the-shoulder; his hand settles on the driver's shoulder"""
    u = t - 36.14
    push(cv, 1.0 + 0.03 * u, W / 2, H * 0.4)
    cab_bg(cv, t, 200, 1080)
    p = driver_pose(t)
    p.sh_up[1] = 0.25 * M.keys(t, [(37.0, 0.0), (37.2, 1.0), (37.5, 0.0)])
    A = figh(cv, 'driver', p, 470, 880, 1.75, yaw=math.pi + 0.35, lk=LK(**DRV_LK))
    (hx, hy), hr = A['head'], A['head_r']
    k = M.keys(t, [(36.25, 0.0), (37.05, 1.0)])
    tip = (hx + 1.55 * hr + (1 - k) * 420, hy + 1.75 * hr + (1 - k) * 700)
    arm_into_frame(cv, (W + 260, H + 160), tip, w=120, hand_r=78, open_hand=True)
    return dict(vign=0.66)


def D2(cv, t):
    """38.12–40.74 «Водитель медленно поворачивает голову.» closer; the head turns, creaking"""
    u = (t - 38.12) / 2.62
    push(cv, 1.0 + 0.06 * u, W * 0.45, H * 0.45)
    cab_bg(cv, t, 160, 1000, L=0.9 * flick(t, [(39.9, 0.2)]))
    hy = M.keys(t, [(38.3, 0.0), (40.2, 1.6)], fn=lambda x: M.smooth(x) ** 1.4)
    p = driver_pose(t, head_yaw=hy)
    p.head_pitch = 0.08
    A = figh(cv, 'driver', p, 470, 860, 2.25, yaw=math.pi + 0.55, lk=LK(**DRV_LK))
    (hx, hy), hr = A['head'], A['head_r']
    arm_into_frame(cv, (W + 300, H + 200), (hx + 1.6 * hr, hy + 1.8 * hr), w=150, hand_r=96, open_hand=True)
    return dict(vign=0.7)


def D3(cv, t):
    """40.74–42.82 «У него закрыты глаза.» ECU: dead face, closed eyes"""
    u = (t - 40.74) / 2.08
    cv.drawRect(skia.Rect(0, 0, W, H), P((12, 16, 18)))
    blur_layer(cv, 18)
    windshield(cv, t, -100, 0, W + 100, 1100)
    cv.restore()
    fl = flick(t, [(41.9, 0.25)], depth=0.6)
    p = driver_pose(t, head_yaw=0.0, e=EX['closed'] | dict(smile=-0.1))
    p.head_pitch = 0.12
    p.head_roll = 0.04 * math.sin(t * 0.6)
    s = 4.2 + 0.5 * u
    figh(cv, 'driver', p, W / 2, 900, s, yaw=0.22, lk=LK(key=(0.5, -0.3), rim=(150, 180, 230), rim_w=7, tint=(0.8 * fl, 0.88 * fl, 0.86 * fl)))
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 0.25 * (1 - fl)))
    return dict(vign=0.78, cool=0.25)


def interior_front_blur(cv, t, cz=150, blur=14, L=1.0, fl=1.0, people=True, **kw):
    cv.drawRect(skia.Rect(0, 0, W, H), P((20, 26, 24)))
    blur_layer(cv, blur)
    cam = E.Persp(0, 160, cz, look=+1, f=760)
    items = cabin_people(cv, cam, t, **kw) if people else []
    E.bus_interior(cv, t, cam, flicker=fl, moving=1.0, items=items, rear_dark=0.6)
    cv.restore()


def D4(cv, t):
    """42.82–46.48 «Ты отшатываешься. Сзади раздаётся женский голос:» recoil, then freezes"""
    u = t - 42.82
    interior_front_blur(cv, t, cz=120 + 30 * u, fl=flick(t, [(42.82, 0.25)]))
    back = M.keys(t, [(42.82, 0.0), (43.1, 1.0), (43.8, 0.75)])
    p = R.Pose(); M.stand(p, t=t)
    p.lean = -0.2 * back
    p.head_pitch = -0.1 * back
    for sd in (1, -1):
        p.hand[sd] = V(70 * sd, -120 + 60 * back, 120 * back)
        p.hand_mode[sd] = 'open'
    freeze = M.keys(t, [(44.3, 0.0), (44.7, 1.0)])
    p.e = M.kexpr(t, [(42.82, EX['shock']), (43.7, EX['terror']), (44.4, EX['shock'] | dict(gx=-0.5, gy=0.0)), (46.4, EX['mild_fear'] | dict(gx=-0.9))], EX)
    p.head_yaw = 0.35 * freeze
    p.blink = M.blink_at(t, [45.3])
    sx = shake(t, 22 * M.keys(t, [(42.82, 1.0), (43.6, 0.0)]))
    z = 1.0 + 0.05 * freeze * (t - 44.3)
    push(cv, z, W / 2, 760)
    figh(cv, 'hero', p, W / 2 + sx - 40 * back, 760 - 30 * back, 2.1, yaw=0.15 - 0.2 * back,
         lk=LK(key=(-0.2, -1.0), rim=E.FLUO, rim_w=7))
    return dict(vign=0.7)


def aisle_pov(cv, t, cz, babka_e, talk=0.0, fl=1.0, yaw=0.0, rear_dark=0.35, **kw):
    cam = E.Persp(5 * math.sin(t * 0.5), 165, cz, look=+1, f=820, yaw=yaw)
    items = cabin_people(cv, cam, t, babka_e=babka_e, babka_talk=talk, **kw)
    E.bus_interior(cv, t, cam, flicker=fl, moving=1.0, items=items, rear_dark=rear_dark)
    return cam


def D5(cv, t):
    """46.48–49.68 «Не трогай его. Он уже давно мёртв.» the voice from the back of the bus"""
    cz = M.keys(t, [(46.48, 120), (49.68, 330)])
    aisle_pov(cv, t, cz, EX['babka_calm'] | dict(lid=0.25), talk=voice(t, 46.48, 49.5), fl=flick(t, [(48.4, 0.18)]), rear_dark=0.15)
    return dict(vign=0.72)


def D6(cv, t):
    """49.68–51.18 «Ты оборачиваешься.» seen from the rear: he turns from the driver to us"""
    cam = E.Persp(-30, 160, 430, look=-1, f=820)
    items = []
    items.append((70, lambda: S1.driver_back(cv, cam, t)))
    turn = M.keys(t, [(49.75, 0.0), (50.6, 1.0)])

    def hero():
        X, Y, s = E.person_at(cam, 20, 180)
        p = R.Pose(); M.stand(p, t=t)
        p.head_yaw = -0.4 * (1 - turn)
        p.e = EX['shock'] | dict(gx=0.0)
        p.blink = M.blink_at(t, [50.4])
        fig(cv, 'hero', p, X, Y, s, yaw=math.pi - math.pi * turn, ground_shadow=0.3)
    items.append((180, hero))
    E.bus_interior(cv, t, cam, moving=1.0, items=items, rear_dark=0.2)
    return dict(vign=0.66)


def D7(cv, t):
    """51.18–53.62 «На последнем сиденье — старуха.» his POV pushes down the aisle"""
    cz = M.keys(t, [(51.18, 200), (53.62, 640)])
    aisle_pov(cv, t, cz, EX['babka_calm'] | dict(lid=0.2, gx=0.0, gy=0.0), babka_pitch=0.05, rear_dark=0.05)
    return dict(vign=0.72)


def babka_close(cv, t, s, hy, e, talk=0.0, yaw=0.12, fl=1.0, pitch=0.05):
    cv.drawRect(skia.Rect(0, 0, W, H), P((14, 18, 18)))
    blur_layer(cv, 20)
    cam = E.Persp(0, 140, 900, look=+1, f=700)
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), mix((10, 12, 14), (60, 70, 66), fl), (12, 14, 16))))
    for x in (120, 960):                        # rear windows: darkness and passing lamps
        r = skia.Rect(x - 230, 300, x + 230, 1100)
        cv.drawRect(r, P((8, 10, 20)))
        k = (t * 0.8 + x / 1000) % 1.0
        cv.drawCircle(r.left() + r.width() * (1 - k), 420, 50, P(E.SODIUM, 0.6))
    cv.restore()
    p = babka_pose(t, e, talk, pitch, 0.0)
    figh(cv, 'babka', p, W / 2, hy, s, yaw=yaw, lk=LK(key=(0.1, -1.0), rim=E.FLUO, rim_w=6, tint=(0.8 * fl, 0.86 * fl, 0.82 * fl)))


def D8(cv, t):
    """53.62–55.82 «Она смотрит прямо на тебя.» medium on babka, slow push"""
    u = (t - 53.62) / 2.2
    babka_close(cv, t, 1.8 + 0.35 * u, 760, EX['babka_calm'] | dict(lid=0.2, gx=0.0, gy=0.0, pupil=0.55))
    return dict(vign=0.75)


def D9(cv, t):
    """55.82–59.86 «Садись, мальчик. До конечной ещё далеко.» close, she talks with a thin smile"""
    u = (t - 55.82) / 4.04
    e = M.kexpr(t, [(55.82, EX['babka_calm'] | dict(lid=0.25, gx=0.0)), (57.2, EX['babka_smile'] | dict(smile=0.4, gx=0.0)), (59.8, EX['babka_smile'] | dict(smile=0.55, gx=0.0))], EX)
    babka_close(cv, t, 3.0 + 0.4 * u, 820, e, talk=voice(t, 55.82, 59.75), yaw=0.08)
    return dict(vign=0.78)


# ------------------------------------------------------------------ E: doors, phone, news, counting
def E1(cv, t):
    """59.86–61.36 «Ты бросаешься к дверям.» side view, he sprints to the door"""
    u = t - 59.86
    S1.side_interior(cv, t, cx=200 * u, moving=1.0, door_x=260 - 200 * u, door=0.0)
    ph = 1.6 * u * 1.4
    p = R.Pose(); M.run(p, ph, amp=1.0)
    p.e = EX['panic']
    x = M.keys(t, [(59.86, 900), (61.2, 330)])
    fig(cv, 'hero', p, x, 1640, 0.95, yaw=-math.pi / 2 + 0.25, lk=LK(**BUS_LK))
    return dict(vign=0.65)


def stop_button(cv, x, y, s, lit=0.0, press=0.0):
    cv.drawRect(skia.Rect(x - 40 * s, -10, x + 40 * s, H + 10), P((176, 180, 172)))
    cv.drawRect(skia.Rect(x - 40 * s, -10, x - 20 * s, H + 10), P((220, 224, 216)))
    r = skia.Rect(x - 150 * s, y - 210 * s, x + 150 * s, y + 210 * s)
    cv.drawRoundRect(r, 40 * s, 40 * s, P((214, 170, 40)))
    cv.drawCircle(x, y - 30 * s, 100 * s, P((90, 20, 20)))
    rr = 82 * s * (1 - 0.06 * press)
    cv.drawCircle(x, y - 30 * s + 6 * s * press, rr, P(mix((150, 30, 30), (255, 90, 70), lit)))
    cv.drawCircle(x - 20 * s, y - 55 * s, rr * 0.4, P((255, 255, 255), 0.18))
    if lit > 0:
        cv.drawCircle(x, y - 30 * s, 200 * s, P((255, 60, 40), 0.3 * lit, blur=40))
    E.text_c(cv, 'СТОП', x, y + 150 * s, 62 * s, (30, 24, 20))


def E2(cv, t):
    """61.36–63.24 «Нажимаешь кнопку остановки.» he hammers the button — no light, no sound"""
    cv.drawRect(skia.Rect(0, 0, W, H), P((20, 26, 24)))
    blur_layer(cv, 18)
    S1.side_interior(cv, t, cx=600, moving=1.0)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 0.25))
    hits = [61.55, 62.05, 62.45, 62.8]
    press = 0.0
    for h in hits:
        d = t - h
        if -0.12 < d < 0.18:
            press = max(press, 1 - abs(d) / 0.15)
    press = max(0.0, press)
    stop_button(cv, W / 2, 900, 2.0, lit=0.0, press=press)
    tip = (W / 2 + 120 + 60 * (1 - press), 900 + 40 + 120 * (1 - press))
    arm_into_frame(cv, (W + 200, H + 100), tip, w=140, hand_r=92)
    return dict(vign=0.7)


def door_view(cv, t, open_k, outside, push_z=1.0, hands=0.0):
    """facing the bus door from inside. outside(cv, rect) draws what's beyond."""
    cv.drawRect(skia.Rect(0, 0, W, H), P((46, 58, 54)))
    fr = skia.Rect(150, 200, 930, 1700)
    cv.save(); cv.clipRect(fr)
    outside(cv, fr)
    cv.restore()
    cv.drawRect(skia.Rect(fr.left(), fr.bottom() - 60, fr.right(), fr.bottom() + 140), P((40, 42, 44)))  # step
    cv.drawRect(skia.Rect(fr.left(), fr.bottom() - 60, fr.right(), fr.bottom() - 40), P((200, 170, 40)))
    half = fr.width() / 2
    for sd in (-1, 1):            # two leaves folding outward
        w = half * (1 - 0.88 * open_k)
        if sd < 0:
            r = skia.Rect(fr.left(), fr.top(), fr.left() + w, fr.bottom() - 60)
        else:
            r = skia.Rect(fr.right() - w, fr.top(), fr.right(), fr.bottom() - 60)
        cv.drawRect(r, P((150, 170, 170), 0.12))
        cv.drawRect(r, P((24, 28, 28), style='stroke', width=26))
        cv.drawRect(skia.Rect(r.left() + 40, r.centerY() - 10, r.right() - 40, r.centerY() + 10), P((24, 28, 28)))
        wet_glass(cv, r, t, n=14, seed=20 + sd, a=0.14)
    cv.drawRect(fr, P((30, 36, 34), style='stroke', width=50))
    cv.drawRect(skia.Rect(60, 0, 110, H), P((170, 176, 168)))
    cv.drawRect(skia.Rect(970, 0, 1020, H), P((170, 176, 168)))
    if hands > 0:
        for sd in (-1, 1):
            arm_into_frame(cv, (W / 2 + sd * 600, H + 300), (W / 2 + sd * 190, 900 + 40 * math.sin(t * 9 + sd) * hands), w=130, hand_r=84, open_hand=True)


def E3(cv, t):
    """63.24–64.26 «Ничего.» he pushes on the closed door; the street keeps flowing past"""
    door_view(cv, t, 0.0, lambda cv, r: S1.street_outside(cv, t, r.left() - 200, r.top(), r.right() + 200, r.bottom(), speed=600), hands=1.0)
    return dict(vign=0.7)


def phone_hold(cv, t, scr_fn, glow=(140, 170, 255), rot=-4, z=1.0, buzz=0.0, bg=None):
    if bg:
        bg(cv)
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 8), 0.4))
    bx = shake(t, 10 * buzz, 70)
    cv.save()
    push(cv, z, W / 2, H * 0.47)
    scr = S1.phone_body(cv, W / 2 + bx + 8 * math.sin(t * 0.9), H * 0.47, 640, 1240, rot + 1.2 * math.sin(t * 1.1))
    cv.save(); cv.clipRect(scr)
    cv.drawRoundRect(scr, 50, 50, P((246, 246, 248)))
    scr_fn(cv, scr)
    cv.restore()
    wet_glass(cv, scr, t, n=12, seed=3, a=0.08)
    cv.restore()
    cv.restore()
    for sd in (-1, 1):
        cv.drawOval(skia.Rect(W / 2 + sd * 355 - 60, H * 0.56, W / 2 + sd * 355 + 60, H * 0.56 + 300), P((214, 176, 168)))
    cv.drawCircle(W / 2, H * 0.47, 900, P(shader=rad((W / 2, H * 0.47), 900, glow, glow, 0.10, 0.0)))


def bus_bg_blur(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), P((20, 26, 24)))
    blur_layer(cv, 24)
    S1.side_interior(cv, t, cx=600 + 100 * t, moving=1.0)
    cv.restore()


def E4(cv, t):
    """64.26–66.36 «В этот момент телефон вибрирует.» his face lit from below by the buzzing phone"""
    u = t - 64.26
    bus_bg_blur(cv, t)
    buzz = 1.0 if (int((t - 64.3) / 0.45) % 2 == 0 and t > 64.3) else 0.0
    p = R.Pose(); M.stand(p, t=t)
    p.hand[1] = V(-10, -90, 230); p.hand_mode[1] = 'phone'
    p.head_pitch = M.keys(t, [(64.4, 0.0), (65.0, 0.35)])
    p.e = M.kexpr(t, [(64.26, EX['panic'] | dict(gx=-0.6)), (64.9, EX['worried'] | dict(gy=-0.9, gx=0.0))], EX)
    lk = LK(key=(0.0, 1.0), rim=(120, 150, 240), rim_w=8, tint=(0.75, 0.85, 1.05))
    figh(cv, 'hero', p, W / 2 + shake(t, 4 * buzz, 60), 780, 2.2, yaw=0.1, lk=lk, props={1: phone_prop(1.0)})
    cv.drawCircle(W / 2, 1500, 700, P((120, 150, 255), 0.12, blur=80))
    return dict(vign=0.72)


def bubble(cv, scr, y, text_lines, k, mine=False):
    if k <= 0:
        return y
    f = E.font(34)
    w = max(f.measureText(s) for s in text_lines) + 60
    h = 54 * len(text_lines) + 30
    x0 = scr.left() + 34 if not mine else scr.right() - 34 - w
    r = skia.Rect(x0, y + 20 * (1 - k), x0 + w, y + h + 20 * (1 - k))
    cv.drawRoundRect(r, 34, 34, P((232, 232, 238) if not mine else (60, 130, 250), k))
    for i, s in enumerate(text_lines):
        cv.drawString(s, r.left() + 30, r.top() + 56 + 54 * i, f, P((20, 20, 26), k))
    return y + h + 24


def chat_screen(t):
    def fn(cv, scr):
        S1.status_bar(cv, scr, 0.02, '23:31', t=t)
        cv.drawRect(skia.Rect(scr.left(), scr.top() + 80, scr.right(), scr.top() + 220), P((236, 238, 244)))
        cv.drawCircle(scr.left() + 110, scr.top() + 150, 46, P((200, 140, 160)))
        E.text_c(cv, 'М', scr.left() + 110, scr.top() + 168, 46, (255, 255, 255))
        cv.drawString('Мама', scr.left() + 180, scr.top() + 145, E.font(40), P((20, 20, 26)))
        cv.drawString('в сети', scr.left() + 180, scr.top() + 190, E.font(28), P((90, 140, 90)))
        y = scr.top() + 320
        cv.drawString('Сегодня', scr.centerX() - 60, y - 40, E.font(26), P((150, 150, 160)))
        y = bubble(cv, scr, y, ['Я задержусь, мам'], 1.0, mine=True)
        y = bubble(cv, scr, y, ['Сынок, где ты?'], M.smooth((t - 68.2) / 0.25))
        y = bubble(cv, scr, y, ['По новостям сказали,', 'что автобус номер 13', 'разбился'], M.smooth((t - 69.6) / 0.25))
        k = M.smooth((t - 70.3) / 0.3)
        if k > 0:                                        # link card
            r = skia.Rect(scr.left() + 34, y, scr.left() + 480, y + 300)
            cv.drawRoundRect(r, 28, 28, P((232, 232, 238), k))
            cv.save(); cv.clipRect(skia.Rect(r.left(), r.top(), r.right(), r.top() + 180))
            cv.drawRect(r, P((40, 30, 26), k))
            cv.drawCircle(r.centerX(), r.top() + 120, 120, P((240, 120, 40), 0.5 * k, blur=30))
            cv.restore()
            cv.drawString('Автобус №13 ...', r.left() + 24, r.top() + 230, E.font(30), P((20, 20, 26), k))
            cv.drawString('news.ru', r.left() + 24, r.top() + 275, E.font(24), P((120, 120, 130), k))
        if 72.6 < t < 73.3:                              # tap
            kk = (t - 72.6) / 0.7
            cv.drawCircle(scr.left() + 250, y + 150, 40 + 60 * kk, P((0, 0, 0), 0.25 * (1 - kk)))
    return fn


def lock_screen(t):
    def fn(cv, scr):
        cv.drawRoundRect(scr, 50, 50, P(shader=lin((0, scr.top()), (0, scr.bottom()), (40, 50, 80), (16, 18, 34))))
        S1.status_bar(cv, scr, 0.02, '23:31', t=t)
        E.text_c(cv, '23:31', scr.centerX(), scr.top() + 300, 170, (235, 238, 248))
        k = M.smooth((t - 64.4) / 0.25)
        r = skia.Rect(scr.left() + 30, scr.top() + 440 - 30 * (1 - k), scr.right() - 30, scr.top() + 620 - 30 * (1 - k))
        cv.drawRoundRect(r, 34, 34, P((44, 44, 54), 0.95 * k))
        cv.drawString('Мама', r.left() + 36, r.top() + 66, E.font(38), P((245, 245, 250), k))
        cv.drawString('Сынок, где ты?', r.left() + 36, r.top() + 120, E.font(32), P((200, 204, 216), k))
    return fn


def E5(cv, t):
    """66.36–73.22 the message from mom"""
    z = M.keys(t, [(66.36, 1.0), (73.2, 1.08)])
    phone_hold(cv, t, chat_screen(t), z=z, bg=lambda cv: bus_bg_blur(cv, t))
    return dict(vign=0.7)


def victim_photo(cv, r, name, k, seed):
    """small greyscale portrait inside rect r"""
    cv.save(); cv.clipRect(r)
    cv.drawRect(r, P((70, 72, 76)))
    p = R.Pose(); M.stand(p, t=0)
    p.e = EX['neutral'] | (dict(lid=0.3) if name != 'driver' else dict(lid=0.0))
    s = r.width() / 330
    figh(cv, name, p, r.centerX(), r.top() + r.height() * 0.45, s, yaw=0.15,
         lk=LK(key=(-0.5, -0.6), rim=None, tint=(0.62, 0.62, 0.62)))
    cv.drawRect(r, P((120, 110, 90), 0.25))
    cv.restore()
    cv.drawRect(r, P((255, 255, 255), k, style='stroke', width=4))


def news_screen(t):
    def fn(cv, scr):
        S1.status_bar(cv, scr, 0.01, '23:32', t=t)
        sc = M.keys(t, [(73.22, 0.0), (77.6, 0.0), (78.4, 1.0)]) * 640
        cv.save(); cv.translate(0, -sc)
        x0, y = scr.left() + 40, scr.top() + 120
        cv.drawRect(skia.Rect(scr.left(), y - 40, scr.right(), y + 40), P((200, 30, 40)))
        cv.drawString('НОВОСТИ ГОРОДА', x0, y + 14, E.font(32), P((255, 255, 255)))
        y += 110
        for s in ('Автобус №13 сорвался', 'с моста в реку'):
            cv.drawString(s, x0, y, E.font(48), P((20, 20, 26)))
            y += 62
        d = skia.Rect(x0 - 8, y - 6, x0 + 410, y + 50)
        hk = M.smooth((t - 74.9) / 0.35)
        cv.drawRect(d, P((255, 220, 60), 0.85 * hk))
        cv.drawString('13 ноября 2006 года', x0, y + 36, E.font(34), P((60, 60, 70) if hk < 0.5 else (20, 20, 26)))
        y += 90
        ph = skia.Rect(scr.left() + 30, y, scr.right() - 30, y + 380)          # archive photo of the wreck
        cv.save(); cv.clipRect(ph)
        cv.drawRect(ph, P(shader=lin((0, ph.top()), (0, ph.bottom()), (30, 30, 34), (60, 58, 56))))
        cv.drawRect(skia.Rect(ph.left(), ph.bottom() - 90, ph.right(), ph.bottom()), P((40, 42, 46)))
        cv.saveLayer(None, P((255, 255, 255), 0.9))
        cv.translate(ph.centerX(), ph.bottom() - 70); cv.rotate(-9); cv.translate(-ph.centerX(), -(ph.bottom() - 70))
        E.bus_side(cv, ph.centerX() - 270, ph.bottom() - 60, 0.75, 0.0, inside=0.0, head_on=0.0, dirt=1.0)
        cv.restore()
        cv.drawRect(ph, P((10, 8, 6), 0.45))
        for i in range(5):
            cv.drawCircle(ph.left() + 100 + i * 110, ph.top() + 120 + 30 * (i % 2), 60, P((10, 10, 12), 0.5, blur=30))
        cv.restore()
        cv.drawRect(ph, P((0, 0, 0), style='stroke', width=2))
        y += 430
        f = E.font(31)
        for s in ('Ровно двадцать лет назад', 'ночной автобус №13 потерял', 'управление на мосту.'):
            cv.drawString(s, x0, y, f, P((40, 40, 48)))
            y += 46
        y += 30
        vk = M.smooth((t - 78.2) / 0.4)
        cv.drawString('Погибли водитель', x0, y, E.font(40), P((180, 20, 30)))
        cv.drawString('и семь пассажиров.', x0, y + 52, E.font(40), P((180, 20, 30)))
        y += 100
        names = ['driver', 'pax0', 'pax1', 'pax2', 'pax3', 'pax4', 'pax5', 'babka']
        cw = (scr.width() - 60 - 3 * 14) / 4
        for i, nm in enumerate(names):
            r = skia.Rect(x0 - 10 + (i % 4) * (cw + 14), y + (i // 4) * (cw * 1.25 + 14), x0 - 10 + (i % 4) * (cw + 14) + cw, y + (i // 4) * (cw * 1.25 + 14) + cw * 1.25)
            if r.top() - sc < scr.bottom():
                victim_photo(cv, r, nm, 0.0, i)
            # black mourning ribbon
            cv.drawPath(path_poly([(r.right() - 50, r.top()), (r.right(), r.top()), (r.right(), r.top() + 50)]), P((10, 10, 10)))
        cv.restore()
        cv.drawRect(scr, P((0, 0, 0), 0.0 + 0.0 * vk))
    return fn


def E6(cv, t):
    """73.22–80.24 the article: 20 years ago; the driver and seven passengers died — with their photos"""
    z = M.keys(t, [(73.22, 1.04), (76.0, 1.10), (78.0, 1.10), (80.2, 1.22)])
    phone_hold(cv, t, news_screen(t), z=z, bg=lambda cv: bus_bg_blur(cv, t))
    return dict(vign=0.74)


COUNT = [82.3, 83.46, 84.4, 85.06, 86.08, 86.72, 87.56]


def E7(cv, t):
    """80.24–88.53 counting: one … seven, his finger moves from face to face; seven is the old woman"""
    n = sum(1 for c in COUNT if t >= c - 0.05)
    hl = n - 1 if n > 0 else None
    cz = M.keys(t, [(80.24, 120), (82.2, 170), (88.5, 260)])
    cam = E.Persp(5 * math.sin(t * 0.5), 165, cz, look=+1, f=820)
    heads = {}
    items = cabin_people(cv, cam, t, hl=hl, heads=heads, babka_e=EX['babka_calm'] | dict(gx=0.0, lid=0.2), babka_pitch=0.05)
    dim = 0.7 if hl is not None else 1.0
    E.bus_interior(cv, t, cam, lights=1.0, flicker=dim * flick(t, [(80.4, 0.2)]), moving=1.0, items=items, rear_dark=0.25)
    # every counted face keeps a faint ring + its number; the current one is bright
    for i in range(0 if hl is None else hl + 1):
        if i not in heads:
            continue
        (x, y), r = heads[i]
        cur = i == hl
        k = M.smooth((t - COUNT[i] + 0.05) / 0.2)
        a = (0.95 if cur else 0.45) * k
        rr = r * (1.55 + 0.25 * (1 - k))
        cv.drawCircle(x, y, rr, P((235, 245, 235), a, style='stroke', width=6 if cur else 4))
        if cur:
            cv.drawCircle(x, y, rr * 1.4, P((200, 255, 220), 0.10 * k, blur=r))
        sz = 88 if cur else 54
        E.text_c(cv, str(i + 1), x, y - rr - 22, sz, (250, 250, 240), a)
    return dict(vign=0.7)


def E8(cv, t):
    """88.53–91.4 «Старуха улыбается. А теперь нас восемь.» ECU, the smile widens"""
    u = (t - 88.53) / 2.9
    e = M.kexpr(t, [(88.53, EX['babka_calm'] | dict(gx=0.0, lid=0.2)), (89.4, EX['babka_smile'] | dict(gx=0.0, smile=0.95, mw=1.1))], EX)
    babka_close(cv, t, 3.6 + 1.0 * u, 840, e, talk=voice(t, 90.0, 92.6), yaw=0.05, fl=flick(t, [(91.0, 0.3)]), pitch=0.08)
    return dict(vign=0.8)


def E9(cv, t):
    """91.4–92.62 «…восемь.» every passenger now faces him, black eyes"""
    turn = M.keys(t, [(91.4, 0.6), (91.9, 1.0)])
    cz = M.keys(t, [(91.4, 300), (92.62, 380)])
    aisle_pov(cv, t, cz, EX['babka_smile'] | dict(gx=0.0), talk=voice(t, 91.4, 92.6), fl=flick(t, [(91.4, 1.3)], depth=0.5),
              black=True, pax_turn=turn, rear_dark=0.1)
    return dict(vign=0.8)


# ------------------------------------------------------------------ F: the stop, home street, the call
def F1(cv, t):
    """92.62–94.84 «Внезапно автобус резко тормозит.» brakes: everything lurches"""
    u = t - 92.62
    j = M.keys(t, [(92.75, 0.0), (93.05, 1.0), (93.9, 0.4), (94.6, 0.0)])
    sh = shake(t, 34 * M.keys(t, [(92.75, 1.0), (94.2, 0.0)]), 31)
    cv.save(); cv.translate(sh, shake(t + 3, 20 * j, 27))
    cv.rotate(2.5 * j)
    cam = E.Persp(-20, 165, 560 - 60 * j, look=-1, f=760)
    items = cabin_people(cv, cam, t, look=-1, jolt=-j, babka=False)

    def hero():
        X, Y, s = E.person_at(cam, 5, 300)
        p = R.Pose(); M.stand(p, t=t)
        p.lean = 0.45 * j
        p.e = EX['panic']
        for sd in (1, -1):
            p.hand[sd] = V(60 * sd, 120 * j, 200 * j); p.hand_mode[sd] = 'open'
        fig(cv, 'hero', p, X, Y, s, yaw=math.pi + 0.5, ground_shadow=0.3)
    items.append((300, hero))
    items.append((70, lambda: S1.driver_back(cv, cam, t)))
    E.bus_interior(cv, t, cam, flicker=flick(t, [(92.8, 1.2)], depth=0.7), moving=1.0 - min(1, u / 1.5), items=items, rear_dark=0.3)
    cv.restore()
    return dict(vign=0.72)


def home_out(t, cx=0.0):
    def fn(cv, r):
        cv.save(); cv.translate(r.left() - 80, r.top() - 300); cv.scale(0.9, 0.9)
        E.home_street(cv, t, cx=cx, gy=1500)
        rain(cv, t, n=120, alpha=0.28)
        cv.restore()
    return fn


def F2(cv, t):
    """94.84–98.44 «Двери открываются. За ними — твоя родная улица.»"""
    k = M.keys(t, [(94.95, 0.0), (95.7, 1.0)])
    z = M.keys(t, [(95.7, 1.0), (98.44, 1.25)])
    cv.save(); push(cv, z, W / 2, 900)
    door_view(cv, t, k, home_out(t))
    cv.restore()
    return dict(vign=0.7)


def F3(cv, t):
    """98.44–99.86 «Ты выбегаешь наружу.» exterior: he leaps from the door towards us"""
    u = t - 98.44
    E.home_street(cv, t, cx=0, gy=1500)
    E.bus_side(cv, -320, 1560, 1.6, t, door=1.0, flicker=0.6)
    ph = u * 2.0
    p = R.Pose(); M.run(p, ph, amp=1.0)
    p.e = EX['panic']
    x = M.keys(t, [(98.44, 200), (99.86, 700)])
    y = M.keys(t, [(98.44, 1560), (99.86, 1900)])
    s = M.keys(t, [(98.44, 0.75), (99.86, 1.25)])
    fig(cv, 'hero', p, x, y, s, yaw=0.6, lk=LK(**STREET_LK))
    rain(cv, t, n=160, alpha=0.3)
    return dict(vign=0.62)


def F4(cv, t):
    """99.86–101.48 «Автобус уезжает.» it pulls away into the fog; he watches, panting"""
    u = t - 99.86
    E.home_street(cv, t, cx=0, gy=1500)
    bx = -320 - 260 * u * u
    E.bus_side(cv, bx, 1560, 1.6, t, door=max(0.0, 1 - u * 2), flicker=0.6)
    cv.drawRect(skia.Rect(0, 0, W, H), P((120, 134, 150), 0.0))
    p = R.Pose(); M.stand(p, t=t, breath=1.0)
    p.lean = 0.25; p.e = EX['exhausted']
    p.head_yaw = -0.6
    for sd in (1, -1):
        p.hand[sd] = V(30 * sd, -250, 120)
    fig(cv, 'hero', p, 760, 2050, 1.5, yaw=math.pi + 0.5, lk=LK(**STREET_LK))
    rain(cv, t, n=160, alpha=0.3)
    return dict(vign=0.64)


def hero_call(cv, t, s, hy, e, talk=0.0, phone=1.0, lift=1.0, z=1.0, yaw=0.25, blur=10):
    cv.save(); push(cv, z, W / 2, hy)
    cv.drawRect(skia.Rect(0, 0, W, H), P((10, 14, 26)))
    blur_layer(cv, blur)
    E.home_street(cv, t, cx=-200, gy=1500)
    cv.restore()
    p = R.Pose(); M.stand(p, t=t, breath=0.5)
    p.e = e; p.talk = talk
    if phone > 0:
        p.hand[1] = V(-20 + 40 * (1 - lift), 95 * lift - 200 * (1 - lift), 40 + 160 * (1 - lift)); p.hand_mode[1] = 'phone'
    p.head_roll = 0.08 * lift
    figh(cv, 'hero', p, W / 2, hy, s, yaw=yaw, lk=LK(**STREET_LK), props={1: phone_prop(1.0)} if phone > 0 else None)
    rain(cv, t, n=110, alpha=0.26)
    cv.restore()


def F5(cv, t):
    """101.48–108.64 relief; he calls mom: «Мам, я уже дома.»"""
    lift = M.keys(t, [(102.2, 0.0), (103.2, 1.0)])
    e = M.kexpr(t, [(101.48, EX['exhausted']), (102.4, EX['calm'] | dict(smile=0.35, lid=0.25)), (104.6, EX['calm'] | dict(smile=0.5)), (108.5, EX['calm'] | dict(smile=0.55))], EX)
    z = M.keys(t, [(101.48, 1.0), (108.64, 1.12)])
    hero_call(cv, t, 1.55, 760, e, talk=voice(t, 106.7, 108.31), lift=lift, z=z)
    return dict(vign=0.62)


def F6(cv, t):
    """108.64–118.28 silence… then the whisper: «Сынок, не заходи в квартиру. Ты уже пришёл домой десять минут назад.»"""
    u = (t - 108.64) / 9.64
    e = M.kexpr(t, [(108.64, EX['calm'] | dict(smile=0.5)), (110.2, EX['confusion']), (112.8, EX['worried']),
                    (115.5, EX['shock'] | dict(mopen=0.25)), (118.2, EX['terror'] | dict(mopen=0.2, gy=0.0))], EX)
    s = 2.4 + 1.6 * M.smooth(u)
    hero_call(cv, t, s, 860, e, lift=1.0, yaw=0.2, blur=18)
    if t > 112.6:
        cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 0.15 * min(1, (t - 112.6) / 3)))
    return dict(vign=0.66 + 0.12 * u)


# ------------------------------------------------------------------ G: the window
WIN = (612, 1020)        # lit window of his room, in facade px


def facade(cv, t, lit=1.0, fig_k=1.0, wave=0.0, reveal=0.0, room_flick=1.0):
    """panel block close-up, his room lit on the 4th floor; a still figure inside"""
    cv.drawRect(skia.Rect(-400, -400, W + 400, 2600), P(shader=lin((0, 0), (0, 2000), (34, 40, 58), (24, 28, 42))))
    for r_ in range(-3, 12):
        for c_ in range(-2, 5):
            x, y = 132 + c_ * 240, 180 + r_ * 210
            if (c_, r_) == (2, 4):
                continue
            cv.drawRect(skia.Rect(x - 4, y + 140, x + 184, y + 160), P((50, 56, 76)))
            on = ((c_ * 5 + r_ * 3) % 11 == 0)
            cv.drawRect(skia.Rect(x, y, x + 180, y + 140), P((200, 150, 90) if on else (12, 14, 24), 0.75 if on else 1.0))
            cv.drawRect(skia.Rect(x + 86, y, x + 94, y + 140), P((40, 44, 60)))
    for r_ in range(-3, 12):
        cv.drawRect(skia.Rect(-400, 340 + r_ * 210, W + 400, 350 + r_ * 210), P((20, 22, 34)))
    # his window
    x, y = WIN
    r = skia.Rect(x - 90, y - 70, x + 90, y + 70)
    cv.save(); cv.clipRect(r)
    room = mix((20, 18, 18), (238, 196, 140), lit * room_flick)
    cv.drawRect(r, P(room))
    cv.drawRect(skia.Rect(r.left(), r.top() + 60, r.left() + 50, r.bottom()), P(mix((10, 10, 10), (150, 100, 70), lit)))
    if fig_k > 0:
        p = R.Pose(); M.stand(p, t=0)
        p.e = EX['blank'] | dict(smile=0.15 + 0.5 * reveal, gx=0.0, gy=-0.3)
        if wave > 0:
            p.hand[1] = V(90, 150 + 20 * math.sin(t * 9), 40); p.hand_mode[1] = 'open'
        tint = 0.08 + 0.85 * reveal * room_flick
        figh(cv, 'burned', p, x + 10, y - 20, 0.13, yaw=0.0, lk=LK(key=(0.0, -0.4), rim=(255, 180, 120), rim_w=4, tint=(tint, tint * 0.9, tint * 0.85)))
    cv.restore()
    cv.drawRect(skia.Rect(r.left() - 4, r.bottom(), r.right() + 4, r.bottom() + 20), P((60, 64, 84)))
    cv.drawRect(skia.Rect(x - 4, r.top(), x + 4, r.bottom()), P((40, 34, 30), 0.0))
    cv.drawRect(r, P((60, 56, 60), style='stroke', width=8))
    cv.drawCircle(x, y, 260, P((240, 180, 110), 0.10 * lit * room_flick, blur=60))


def G1(cv, t):
    """118.28–120.64 «Ты медленно поднимаешь глаза.» low angle, his head lifts"""
    u = (t - 118.28) / 2.36
    cv.drawRect(skia.Rect(0, 0, W, H), P((10, 14, 26)))
    blur_layer(cv, 16)
    cv.save(); cv.translate(0, -300 + 200 * u); cv.scale(0.8, 0.8)
    facade(cv, t, lit=1.0, fig_k=0.0)
    cv.restore()
    cv.restore()
    p = R.Pose(); M.stand(p, t=t, breath=0.6)
    p.hand[1] = V(-20, 95 * (1 - u) - 200 * u, 40 + 160 * u); p.hand_mode[1] = 'phone'
    p.head_pitch = M.keys(t, [(118.4, 0.25), (120.3, -0.28)])
    p.e = EX['terror'] | dict(mopen=0.15, gy=M.keys(t, [(118.4, 0.6), (120.2, -1.0)]), gx=0.0)
    figh(cv, 'hero', p, W / 2, 1150 - 120 * u, 2.6, yaw=0.12, lk=LK(key=(0.4, -0.3), rim=E.SODIUM, rim_w=7), props={1: phone_prop(0.6)})
    rain(cv, t, n=120, alpha=0.28)
    return dict(vign=0.7)


def G2(cv, t):
    """120.64–124.9 «В окне своей комнаты видишь человека. Он стоит неподвижно.» slow push to the window"""
    u = M.smooth((t - 120.64) / 4.26)
    z = 0.9 + 1.4 * u
    cv.save()
    push(cv, z, WIN[0] - 60 * (1 - u), WIN[1])
    cv.translate(W / 2 - WIN[0], 0)
    facade(cv, t, lit=1.0, fig_k=1.0)
    cv.restore()
    rain(cv, t, n=140, alpha=0.3)
    return dict(vign=0.72)


def G3(cv, t):
    """124.9–127.14 «А потом машет тебе рукой.» close on the window, the silhouette waves"""
    u = (t - 124.9) / 2.24
    wave = M.keys(t, [(125.1, 0.0), (125.5, 1.0)])
    cv.save()
    push(cv, 4.6 + 0.4 * u, WIN[0], WIN[1])
    cv.translate(W / 2 - WIN[0], H * 0.47 - WIN[1])
    facade(cv, t, lit=1.0, fig_k=1.0, wave=wave)
    cv.restore()
    rain(cv, t, n=140, alpha=0.3)
    return dict(vign=0.75)


def G4(cv, t):
    """127.14–130.04 «И ты понимаешь. Это ты сам.» ECU of his face, vertigo push"""
    u = (t - 127.14) / 2.9
    cv.drawRect(skia.Rect(0, 0, W, H), P((10, 14, 26)))
    blur_layer(cv, 20)
    cv.save(); push(cv, 1.4 - 0.4 * u, W / 2, H / 2)
    E.home_street(cv, t, cx=-200, gy=1500)
    cv.restore()
    cv.restore()
    p = R.Pose(); M.stand(p, t=t, breath=0.8)
    p.head_pitch = -0.18
    p.e = EX['terror'] | dict(gy=-0.6, gx=0.0, mopen=0.35 + 0.1 * voice(t, 127, 130))
    p.blink = M.blink_at(t, [128.3])
    figh(cv, 'hero', p, W / 2 + shake(t, 4), 960, 4.2 + 0.9 * u, yaw=0.05, lk=LK(key=(0.4, -0.3), rim=E.SODIUM, rim_w=8))
    rain(cv, t, n=90, alpha=0.24)
    return dict(vign=0.78)


def G5(cv, t):
    """130.04–133.36 «Только его лицо полностью обгорело.» lamp stutters on: it is him, burned; the hand
    rises slowly and the smile spreads too wide"""
    u = (t - 130.04) / 3.32
    # one short stutter, then the lamp holds — the face stays readable for most of the shot
    fl = flick(t, [(130.04, 0.22), (132.1, 0.08)], depth=0.9)
    rev = M.keys(t, [(130.04, 0.15), (130.3, 1.0)])
    lit = rev * fl
    # room behind him: wallpaper, door frame, hanging bulb
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), mix((6, 6, 8), (196, 150, 100), lit), mix((4, 4, 6), (120, 84, 56), lit))))
    for i in range(7):
        x = 40 + i * 170
        cv.drawRect(skia.Rect(x, 0, x + 6, H), P(mix((0, 0, 0), (170, 124, 82), lit), 0.6))
    cv.drawRect(skia.Rect(780, 260, 1000, H), P(mix((4, 4, 4), (90, 60, 40), lit)))
    sway = 14 * math.sin(t * 1.7)
    cv.drawLine(300, 0, 300 + sway, 210, P((20, 16, 14), style='stroke', width=4))
    cv.drawCircle(300 + sway, 240, 34, P(mix((40, 36, 30), (255, 236, 190), lit)))
    cv.drawCircle(300 + sway, 240, 260, P((255, 220, 150), 0.35 * lit, blur=70))
    # the double: slow push in, hand rises from his side, smile widens past natural
    p = R.Pose(); M.stand(p, t=t, breath=0.1)
    raise_k = M.keys(t, [(130.4, 0.0), (132.4, 1.0)])
    p.hand[1] = V(25 + 80 * raise_k, -345 + 520 * raise_k, 20 + 30 * raise_k)
    p.hand_mode[1] = 'open' if raise_k > 0.3 else 'relaxed'
    if raise_k >= 1.0:
        p.hand[1] = p.hand[1] + V(0, 0, 0)
    p.head_roll = 0.10 * M.smooth((t - 131.0) / 1.5)          # wrong, slight tilt
    p.head_pitch = -0.06
    sm = M.smooth((t - 130.9) / 1.9)
    p.e = EX['neutral'] | dict(smile=0.1 + 0.95 * sm, mw=0.9 + 0.5 * sm, asym=0.35 * sm, lid=0.05, pupil=0.42,
                               gx=0.0, gy=0.0, brow=-0.15 * sm, mopen=0.0)
    p.blink = 0.0                                              # never blinks
    s = 2.55 + 0.45 * M.smooth(u)
    tint = 0.08 + 0.92 * lit
    figh(cv, 'burned', p, W / 2 + shake(t, 1.5, 3), 760, s, yaw=0.06,
         lk=LK(key=(-0.3, -0.7), rim=(255, 190, 130), rim_w=8, tint=(tint, tint * 0.93, tint * 0.88)))
    # window frame + cross bar + rain on the glass in front
    cv.drawRect(skia.Rect(0, 0, W, H), P((30, 30, 36), style='stroke', width=90))
    cv.drawRect(skia.Rect(0, 1420, W, 1470), P((30, 30, 36)))
    cv.drawRect(skia.Rect(0, 0, W, H), P((80, 100, 140), 0.06))
    wet_glass(cv, skia.Rect(0, 0, W, H), t, n=50, seed=8, a=0.13)
    rain(cv, t, n=80, alpha=0.2)
    return dict(vign=0.78)


def G6(cv, t):
    """133.36–end: hard cut to the title card"""
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0)))
    k = M.smooth((t - 133.5) / 0.5)
    E.text_c(cv, 'ПОСЛЕДНИЙ', W / 2, 860, 120, (200, 30, 36), k)
    E.text_c(cv, 'ПАССАЖИР', W / 2, 990, 120, (200, 30, 36), k)
    E.text_c(cv, 'ЭПИЗОД 1', W / 2, 1090, 46, (170, 170, 176), k * 0.9)
    return dict(vign=0.0, grain=0.02, lift=(0, 0, 0))


SHOTS = [
    (36.14, 38.12, D1), (38.12, 40.74, D2), (40.74, 42.82, D3), (42.82, 46.48, D4), (46.48, 49.68, D5),
    (49.68, 51.18, D6), (51.18, 53.62, D7), (53.62, 55.82, D8), (55.82, 59.86, D9),
    (59.86, 61.36, E1), (61.36, 63.24, E2), (63.24, 64.26, E3), (64.26, 66.36, E4), (66.36, 73.22, E5),
    (73.22, 80.24, E6), (80.24, 88.53, E7), (88.53, 91.4, E8), (91.4, 92.62, E9),
    (92.62, 94.84, F1), (94.84, 98.44, F2), (98.44, 99.86, F3), (99.86, 101.48, F4), (101.48, 108.64, F5), (108.64, 118.28, F6),
    (118.28, 120.64, G1), (120.64, 124.9, G2), (124.9, 127.14, G3), (127.14, 130.04, G4), (130.04, 133.36, G5), (133.36, 135.5, G6),
]
