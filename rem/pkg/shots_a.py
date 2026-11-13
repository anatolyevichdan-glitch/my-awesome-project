from lib import *

GY = 1560
SH = {}   # registry


def shot(t0, t1, name=''):
    def deco(fn):
        SH[len(SH)] = (t0, t1, fn, name or fn.__name__)
        return fn
    return deco


def fin(f, o, T, blur=0):
    return f.compose(), o


def head_y(s, Y0):
    return Y0 - 960 * s


# --------------------------------------------------------------------- 1-3 street walk
@shot(0.0, 2.15)
def s01_walk_side(T, u, d):
    f = new(T)
    S.street(f, T, cx=WSPD * 0.8 * T)
    p = hpose(T, A.kexp(T, [(0, 'calm'), (2, 'neutral')]), yaw=1.5708)
    A.walk(p, WW * T, 1.0)
    p.head_pitch = 0.06
    A.hero(f, p, 470, GY + 20, 0.8)
    E.snow(f, T)
    o = Out()
    o.fade = keyf(T, [(0, 0), (0.7, 1)])
    o.zoom = lerp(1.0, 1.06, u / d)
    return fin(f, o, T)


@shot(2.15, 4.9)
def s02_walk_front(T, u, d):
    f = new(T)
    S.street(f, T, cx=-WSPD * 0.3 * T + 900, lamps_on=(1, 1, 1))
    k = u / d
    s = lerp(0.62, 0.88, ease(k))
    p = hpose(T, A.kexp(u, [(0, 'calm'), (1.0, 'suspicious'), (2.0, 'worried')]), yaw=0.35 * math.sin(T * 0.8))
    A.walk(p, WW * T, 0.95)
    p.head_yaw = A.keyf(u, [(0, 0), (0.9, 0.0), (1.2, 0.7), (1.8, 0.7), (2.1, 0.0)])
    A.hero(f, p, 540, lerp(1500, 1690, ease(k)), s)
    E.snow(f, T)
    o = Out()
    return fin(f, o, T)


@shot(4.9, 6.3)
def s03_ecu_unaware(T, u, d):
    f = new(T)
    S.street(f, T, cx=300)
    blur_bg(f, 14)
    p = hpose(T, 'calm' and R.EXPR['calm'], yaw=0.25)
    p.e = A.kexp(u, [(0, 'calm'), (1.4, 'neutral')])
    p.breath = T * 0.4
    A.walk(p, WW * T, 0.25)
    A.hero(f, p, 540, 2720, 2.1, shadow=0)
    # far, soft dark shape behind him he cannot see
    E.snow(f, T, n=60, size=5)
    o = Out()
    o.zoom = lerp(1.0, 1.08, u / d)
    return fin(f, o, T)


@shot(6.3, 8.0)
def s04_pole_camera(T, u, d):
    f = new(T)
    S.street(f, T, cx=0)
    blur_bg(f, 6)
    cv = f.fg.c
    k = u / d
    sc = lerp(1.0, 1.25, k)
    cv.save()
    cv.translate(540, 800)
    cv.scale(sc, sc)
    cv.translate(-540, -800)
    cv.drawRect(skia.Rect(500, 800, 580, 1920), P((52, 56, 72)))
    cv.drawRoundRect(skia.Rect(260, 560, 800, 800), 30, 30, P((70, 74, 94)))
    cv.drawRoundRect(skia.Rect(280, 580, 780, 780), 24, 24, P((40, 42, 58)))
    cv.drawRect(skia.Rect(250, 540, 810, 590), P((34, 36, 50)))
    cv.drawCircle(660, 680, 82, P((16, 18, 26)))
    cv.drawCircle(660, 680, 62, P(shader=rad((660, 680), 62, (30, 50, 90), (8, 10, 18), 1, 1)))
    cv.drawCircle(640, 660, 14, P((200, 220, 255), 0.9))
    on = 1 if int(T * 2) % 2 == 0 else 0.15
    cv.drawCircle(350, 640, 14, P((255, 50, 50), on))
    f.glow(350, 640, 90, (255, 60, 60), 0.8 * on)
    cv.restore()
    f.light_pool(540, 700, 700, (0.5, 0.58, 0.8), 0.7)
    E.snow(f, T)
    o = Out()
    return fin(f, o, T)


def cctv_chars(f, T, u, hx, creature_alpha, cdist=520, s=0.5, cheight=900, gait=1.0, amp=1.0, ph_off=0.0):
    gy = 1330
    p = hpose(T, R.EXPR['neutral'], yaw=1.5708)
    A.walk(p, WW * T * gait, amp)
    A.hero(f, p, hx, gy, s)
    if creature_alpha > 0:
        cx_ = hx - cdist
        r = A.creature(f, cx_, gy, cheight * s / 0.5 * 0.5, T, alpha=creature_alpha, eyes=creature_alpha > 0.5, mist=0.8)
        return r


@shot(8.0, 11.95)
def s05_cctv(T, u, d):
    f = new(T, gain=1.5)
    S.street(f, T, cx=WSPD * 0.5 * 0.6 * T)
    ca = A.keyf(u, [(0, 0), (0.7, 0), (1.6, 1)])
    if 0.7 < u < 1.4 and int(T * 18) % 3 == 0:
        ca *= 0.2
    cctv_chars(f, T, u, 560, ca, cdist=470, s=0.52, cheight=1000)
    E.snow(f, T)
    o = Out()
    o.cctv = True
    o.zoom = lerp(1.0, 1.1, u / d)
    o.glitch = 0.6 if 0.7 < u < 1.5 else 0.0
    return fin(f, o, T)


@shot(11.95, 14.3)
def s06_speedup(T, u, d):
    f = new(T)
    sp = A.keyf(u, [(0, 0.8), (1.0, 1.35)])
    S.street(f, T, cx=WSPD * 1.2 * T)
    p = hpose(T, A.kexp(u, [(0, 'worried'), (1.2, 'mild_fear')]), yaw=1.5708)
    A.walk(p, WW * T * sp, 1.3)
    A.hero(f, p, 700, GY + 30, 0.8)
    q = A.keyf(u, [(0, 0), (1.3, 0), (1.5, 0.4)])
    cr = A.creature(f, 190 + 40 * math.sin(T * 2), GY + 20, 1350, T, mist=1.0)
    E.snow(f, T)
    o = Out()
    o.shake = 0.15
    return fin(f, o, T)


@shot(14.3, 17.5)
def s07_stop_freeze(T, u, d):
    f = new(T)
    S.street(f, T, cx=WSPD * 1.2 * 14.3 + A.keyf(u, [(0, 400), (0.8, 640)]) * 1)
    stopk = ease(u / 0.6)
    p = hpose(T, A.kexp(u, [(0, 'worried'), (1.0, 'mild_fear'), (3.0, 'mild_fear')]), yaw=1.5708 - 0.3 * stopk)
    if u < 0.6:
        A.walk(p, WW * 14.3 * 1.3 + u * 7, 1.0 * (1 - stopk) + 0.05)
    p.heave = 6 * math.sin(T * 6) * stopk
    p.breath = T * 0.9
    A.hero(f, p, 760, GY + 30, 0.8)
    cx_ = 280 + A.keyf(u, [(0, 0), (1.5, 100)])
    cr = A.creature(f, cx_, GY + 20, 1350, 5.0 if u > 1.5 else T, mist=0.5 if u > 1.5 else 1.0)
    breath_fog(f, 790, GY - 810 * 0.8, T, 1.0, 1.0, 0.7)
    E.snow(f, T, speed=80)
    o = Out()
    o.zoom = lerp(1.0, 1.05, u / d)
    return fin(f, o, T)


# --------------------------------------------------------------------- phone at the bus stop
@shot(17.5, 19.0)
def s08_vibrate(T, u, d):
    f = new(T)
    S.busstop(f, T)
    p = hpose(T, A.kexp(u, [(0, 'mild_fear'), (1.0, 'worried')]), yaw=-0.45)
    p.pelvis = V(0, 0, 0)
    A.stand(p)
    buzz = 1 if (u % 0.5) < 0.22 else 0
    p.shake = buzz
    p.hand[1] = V(22, -300 + 8 * buzz * math.sin(T * 80), 40)
    p.head_pitch = 0.1
    A.hero(f, p, 720, GY + 10, 0.9)
    E.snow(f, T, speed=60)
    o = Out()
    o.shake = 0.45 * buzz
    o.zoom = lerp(1.0, 1.1, u / d)
    return fin(f, o, T)


@shot(19.0, 21.35)
def s08b_pull_phone(T, u, d):
    f = new(T)
    S.busstop(f, T)
    k = ease((u - 0.3) / 0.9)
    p = hpose(T, A.kexp(u, [(0, 'worried'), (2.0, 'worried')]), yaw=-0.3)
    A.stand(p)
    p.hand_abs[1] = V(110, lerp(520, 700, k), lerp(120, 300, k))
    p.hand_mode[1] = 'phone'
    p.hand_dir[1] = V(0, 0.8, 0.4)
    p.head_pitch = 0.18 * k
    r = A.hero(f, p, 700, GY + 10, 1.0)
    A.draw_phone(f.ch.c, f, r['hand'][1], 1.0, glow=k)
    E.snow(f, T, speed=60)
    o = Out()
    o.zoom = lerp(1.04, 1.18, u / d)
    o.oy = lerp(0, -160, u / d)
    return fin(f, o, T)


@shot(21.35, 22.95)
def s09_phone_ecu(T, u, d):
    f = new(T)
    S.busstop(f, T)
    blur_bg(f, 18)
    phone_inset(f, T, u, ['Не оборачивайся.'], '', t_in=0.15, buzz=0.2)
    E.snow(f, T, n=40, size=6)
    o = Out()
    o.zoom = lerp(1.0, 1.06, u / d)
    return fin(f, o, T)


@shot(22.95, 24.55)
def s10_eyes_up(T, u, d):
    f = new(T)
    S.busstop(f, T)
    blur_bg(f, 16)
    p = hpose(T, A.kexp(u, [(0, 'worried'), (0.35, 'worried'), (0.55, 'look_up'), (1.6, 'look_up')]), yaw=0.15)
    p.head_pitch = A.keyf(u, [(0, 0.3), (0.35, 0.3), (0.6, -0.35)])
    p.head_yaw = 0
    p.shake = 0
    A.hero(f, p, 540, 2740, 2.1, shadow=0)
    E.snow(f, T, n=50, size=5)
    o = Out()
    o.zoom = A.keyf(u, [(0, 1.0), (0.45, 1.0), (0.6, 1.1), (1.6, 1.14)])
    o.shake = 0.3 if 0.4 < u < 0.7 else 0
    return fin(f, o, T)


# --------------------------------------------------------------------- storefront and the reflection
def glass_reflection(f, T, info, hero_pose, rx, ry, rs, mode, t_mode=0.0, show_crowd=False):
    """draw the reflected hero inside the glass pane. mode: mimic | stare | shush"""
    gx0, gy0, gx1, gy1 = info['glass']
    cv = f.bg.c
    cv.save()
    cv.clipRect(skia.Rect(gx0, gy0, gx1, gy1))
    # mirrored street in glass
    cv.drawRect(skia.Rect(gx0, gy0, gx1, gy1), P(shader=lin((0, gy0), (0, gy1), (52, 70, 118), (28, 38, 74))))
    for lx in (gx0 + 120, gx1 - 100):
        cv.drawRect(skia.Rect(lx, gy0, lx + 10, gy1), P((80, 86, 110), 0.5))
        cv.drawOval(skia.Rect(lx - 40, gy0 + 20, lx + 50, gy0 + 60), P((255, 214, 140), 0.65, blur=14))
    rp = hero_pose.copy()
    q = R.mirror_pose(rp) if mode == 'mimic' else rp
    rp.yaw = 0.0
    if mode == 'mimic':
        rp.yaw = 0.0
    q = rp
    q.e = A.kexp(T - t_mode, [(0, rp.e)]) if False else rp.e
    A.hero(f, q, rx, ry, rs, tint=(0.8, 0.88, 1.15), layer='bg', shadow=0, yaw=0.0)
    cv.restore()
    cv.drawRect(skia.Rect(gx0, gy0, gx1, gy1), P(shader=lin((gx0, gy0), (gx1, gy1), (180, 210, 255), (180, 210, 255), 0.12, 0.0)))
    # diagonal streaks
    cv.drawPath(path_poly([(gx0 + 60, gy0), (gx0 + 160, gy0), (gx0 + 40, gy1), (gx0 - 60, gy1)]), P((200, 225, 255), 0.06))


def storefront_base(f, T, cx=0):
    return S.storefront(f, T, cx)


@shot(24.55, 26.9)
def s11_window_approach(T, u, d):
    f = new(T)
    info = S.storefront(f, T)
    p = hpose(T, A.kexp(u, [(0, 'look_up'), (0.8, 'worried'), (2.0, 'suspicious')]), yaw=2.3)
    A.stand(p)
    k = ease(u / 1.6)
    p.hand[1] = V(22, -300, 40)
    hero_x = lerp(300, 380, k)
    mp = p.copy()
    mp.yaw = 0.0
    glass_reflection(f, T, info, mp, 740, 1540, 0.8, 'mimic')
    A.hero(f, p, hero_x, GY + 30, 0.95)
    E.snow(f, T)
    o = Out()
    o.zoom = lerp(1.0, 1.12, u / d)
    return fin(f, o, T)


@shot(26.9, 29.4)
def s12_nobody_behind(T, u, d):
    f = new(T)
    info = S.storefront(f, T)
    p = hpose(T, A.kexp(u, [(0, 'suspicious'), (2.5, 'worried')]), yaw=2.3)
    A.stand(p)
    p.head_yaw = A.keyf(u, [(0, 0), (1.0, -0.5), (2.0, 0.2)])
    mp = hpose(T, R.EXPR['suspicious'], yaw=0)
    A.stand(mp)
    glass_reflection(f, T, info, mp, 740, 1540, 0.8, 'mimic')
    A.hero(f, p, 260, GY + 30, 0.95)
    E.snow(f, T)
    o = Out()
    o.zoom = lerp(1.1, 1.0, u / d)
    o.ox = lerp(60, 0, u / d)
    return fin(f, o, T)


@shot(29.4, 32.55)
def s13_exhale_notice(T, u, d):
    f = new(T)
    info = S.storefront(f, T)
    blur_bg(f, 10)
    p = hpose(T, A.kexp(u, [(0, 'worried'), (1.0, 'calm'), (1.7, 'calm'), (2.2, 'suspicious'), (3.1, 'mild_fear')]), yaw=1.1)
    p.head_pitch = A.keyf(u, [(0, 0.12), (1.0, -0.05), (1.7, 0.0)])
    p.talk = 0
    p.breath = A.keyf(u, [(0, 0), (1.0, 0.5)])
    A.hero(f, p, 440, 2760, 2.1, shadow=0)
    breath_fog(f, 700, 1010, T, 3.0, 1.0, 2.0, ph=29.9)
    E.snow(f, T, n=50, size=5)
    o = Out()
    o.zoom = lerp(1.0, 1.08, u / d)
    return fin(f, o, T)


@shot(32.55, 38.5)
def s14_reflection_no_breath(T, u, d):
    f = new(T)
    info = S.storefront(f, T)
    p = hpose(T, A.kexp(u, [(0, 'calm'), (2.0, 'suspicious'), (5.0, 'mild_fear')]), yaw=2.3)
    A.stand(p)
    p.head_yaw = A.keyf(u, [(0, 0), (3.0, 0.0), (4.0, -0.3)])
    mp = hpose(T, R.EXPR['neutral'], yaw=0)
    mp.e = dict(R.EXPR['neutral'])
    mp.e['gx'] = 0
    mp.breath = 0.0
    mp.blink = 0.0
    A.stand(mp)
    # reflection holds still and stares straight out of the glass
    glass_reflection(f, T, info, mp, 740, 1540, 0.8, 'stare')
    A.hero(f, p, 260, GY + 30, 0.95)
    breath_fog(f, 420, GY - 880 * 0.95, T, 2.1, 1.0, 0.8, ph=32.6)
    E.snow(f, T)
    o = Out()
    o.zoom = A.keyf(u, [(0, 1.0), (5.9, 1.2)])
    o.ox = A.keyf(u, [(0, 0), (5.9, 150)])
    o.oy = A.keyf(u, [(0, 0), (5.9, -100)])
    return fin(f, o, T)


@shot(38.5, 43.3)
def s15_finger_lips(T, u, d):
    f = new(T)
    info = S.storefront(f, T)
    p = hpose(T, A.kexp(u, [(0, 'suspicious'), (2.2, 'mild_fear'), (3.6, 'shock')]), yaw=2.3)
    A.stand(p)
    mp = hpose(T, R.EXPR['neutral'], yaw=0)
    A.stand(mp)
    k = ease((u - 0.2) / 3.0)
    A.lips_pose(mp, 1, k)
    mp.e = A.kexp(u, [(0, 'neutral'), (3.2, 'neutral'), (3.6, 'shh')])
    mp.e = dict(mp.e)
    mp.e['gx'] = 0
    mp.breath = 0
    mp.blink = 0
    glass_reflection(f, T, info, mp, 740, 1640, 0.92, 'shush')
    A.hero(f, p, 240, GY + 30, 0.95)
    E.snow(f, T)
    o = Out()
    o.zoom = A.keyf(u, [(0, 1.1), (4.7, 1.45)])
    o.ox = A.keyf(u, [(0, 80), (4.7, 190)])
    o.oy = A.keyf(u, [(0, -50), (4.7, -330)])
    return fin(f, o, T)


@shot(43.3, 44.95)
def s16_jump_back(T, u, d):
    f = new(T)
    info = S.storefront(f, T)
    k = ease(u / 0.5)
    p = hpose(T, A.kexp(u, [(0, 'shock'), (1.6, 'terror')]), yaw=2.3 - 0.8 * k)
    A.stand(p)
    p.lean = -0.25 * k
    p.hand[1] = V(120, lerp(-300, -80, k), 160)
    p.hand[-1] = V(-120, lerp(-300, -80, k), 160)
    hx = lerp(380, 130, k)
    p.foot[1] = V(R.HIP_W, R.ANKLE_H + 60 * (1 - k) * k * 4, -120 * k)
    mp = hpose(T, R.EXPR['neutral'], yaw=0)
    A.lips_pose(mp, 1, 1.0)
    mp.e = dict(R.EXPR['shh'])
    mp.breath = 0
    mp.blink = 0
    glass_reflection(f, T, info, mp, 740, 1640, 0.92, 'shush')
    A.hero(f, p, hx, GY + 30 - 60 * math.sin(k * math.pi) * (1 if u < 0.5 else 0), 0.95)
    E.snow(f, T)
    o = Out()
    o.shake = 0.5 * (1 if u < 0.4 else 0.2)
    o.zoom = 1.0
    return fin(f, o, T)


# --------------------------------------------------------------------- messages 2 and 3
@shot(44.95, 47.5)
def s17_message2(T, u, d):
    f = new(T)
    S.storefront(f, T)
    blur_bg(f, 18)
    phone_inset(f, T, u, ['Он не за тобой.'], '', t_in=0.5, buzz=1.0 if u < 0.5 else 0)
    E.snow(f, T, n=40, size=6)
    o = Out()
    o.shake = 0.3 if u < 0.4 else 0
    o.zoom = lerp(1.0, 1.06, u / d)
    return fin(f, o, T)


@shot(47.5, 50.2)
def s18_freeze(T, u, d):
    f = new(T)
    S.storefront(f, T)
    blur_bg(f, 8)
    p = hpose(T, A.kexp(u, [(0, 'mild_fear'), (1.4, 'panic')]), yaw=0.2)
    A.stand(p)
    A.phone_pose(p)
    p.head_pitch = 0.15
    p.head_yaw = A.keyf(u, [(0, 0), (0.7, 0.35), (1.4, -0.35), (2.2, 0.0)])
    p.shake = 1
    r = A.hero(f, p, 540, 2300, 1.7, shadow=0)
    A.draw_phone(f.ch.c, f, r['hand'][1], 1.7, glow=0.8)
    breath_fog(f, 560, 1100, T, 1.3, 1.0, 1.4)
    E.snow(f, T, n=50, size=5)
    o = Out()
    o.zoom = lerp(1.0, 1.1, u / d)
    return fin(f, o, T)


@shot(50.2, 51.75)
def s18b_message3(T, u, d):
    f = new(T)
    S.storefront(f, T)
    blur_bg(f, 20)
    phone_inset(f, T, u, ['Он внутри тебя.'], '', t_in=0.25, buzz=1.0 if u < 0.4 else 0)
    o = Out()
    o.shake = 0.35 if u < 0.4 else 0
    o.zoom = lerp(1.0, 1.1, u / d)
    return fin(f, o, T)


@shot(51.75, 53.7)
def s19_inside_you(T, u, d):
    f = new(T)
    S.busstop(f, T)
    blur_bg(f, 20)
    p = hpose(T, A.kexp(u, [(0, 'panic'), (1.9, 'terror')]), yaw=0.0)
    p.head_pitch = 0.1
    p.shake = 1
    r = A.hero(f, p, 540, 2780, 2.15, shadow=0)
    f.light_pool(540, 900, 700, (0.4, 0.55, 0.95), 0.8)
    f.glow(540, 1500, 700, (120, 170, 255), 0.25)
    o = Out()
    o.zoom = lerp(1.0, 1.18, ease(u / d))
    o.shake = 0.3
    o.mono = 0.15
    return fin(f, o, T)
