from shots_a import *
from shots_a import SH, shot

RUNW = 8.2
RSPD = 127 * 1.5 * RUNW


def dop_pose(T, e, yaw, seed=3):
    p = hpose(T, e, yaw=yaw, seed=seed)
    return p


# --------------------------------------------------------------------- the lamps go out
@shot(53.7, 56.55)
def s20_avenue_wide(T, u, d):
    f = new(T)
    S.avenue(f, T, cx=0)
    p = hpose(T, A.kexp(u, [(0, 'mild_fear'), (2.8, 'worried')]), yaw=0.0)
    A.stand(p)
    A.phone_pose(p)
    p.head_pitch = 0.1
    r = A.hero(f, p, 540, GY + 30, 0.62)
    A.draw_phone(f.ch.c, f, r['hand'][1], 0.62, glow=0.6)
    E.snow(f, T)
    o = Out()
    o.zoom = lerp(1.0, 1.1, u / d)
    return fin(f, o, T)


def lamp_shot(T, u, d, idx, t_off):
    on = [1, 1, 1]
    fl = [0, 0, 0]
    for j in range(idx):
        on[j] = 0
    k = T - t_off
    if k > 0:
        on[idx] = 0
    if -0.5 < k < 0:
        fl[idx] = 0.6 if int(T * 22) % 2 else 0.0
    f = new(T)
    info = S.avenue(f, T, cx=0, lamps=on, flick=fl)
    return f, info


@shot(56.55, 57.3)
def s21_lamp1(T, u, d):
    f, info = lamp_shot(T, u, d, 0, 56.62)
    p = hpose(T, R.EXPR['mild_fear'], yaw=0.5)
    A.stand(p)
    A.hero(f, p, 700, GY + 30, 0.55)
    E.snow(f, T)
    o = Out()
    o.zoom = 1.45
    o.ox = -55
    o.oy = -100
    o.shake = 0.5 if T > 56.62 else 0
    return fin(f, o, T)


@shot(57.3, 58.15)
def s22_lamp2(T, u, d):
    f, info = lamp_shot(T, u, d, 1, 57.38)
    p = hpose(T, R.EXPR['fear'] if 'fear' in R.EXPR else R.EXPR['mild_fear'], yaw=0.5)
    A.stand(p)
    A.hero(f, p, 700, GY + 30, 0.55)
    E.snow(f, T)
    o = Out()
    o.zoom = 1.45
    o.ox = 250
    o.oy = -100
    o.shake = 0.5 if T > 57.38 else 0
    return fin(f, o, T)


@shot(58.15, 59.1)
def s23_lamp3(T, u, d):
    f, info = lamp_shot(T, u, d, 2, 58.22)
    p = hpose(T, R.EXPR['panic'], yaw=0.2)
    A.stand(p)
    A.phone_pose(p)
    p.shake = 1
    r = A.hero(f, p, 700, GY + 30, 0.7)
    A.draw_phone(f.ch.c, f, r['hand'][1], 0.7, glow=1.0)
    # eyes in the dark behind him
    ea = A.keyf(u, [(0.2, 0), (0.7, 1)])
    for sd in (-1, 1):
        f.glow(1000 + 26 * sd, 820, 60, (225, 232, 255), 0.7 * ea)
    E.snow(f, T)
    o = Out()
    o.zoom = lerp(1.0, 1.2, u / d)
    o.shake = 0.3
    return fin(f, o, T)


# --------------------------------------------------------------------- the chase
@shot(59.1, 61.0)
def s24_run_toward(T, u, d):
    f = new(T, gain=1.2)
    S.avenue(f, T, cx=-RSPD * 0.5 * T, lamps=(0, 0, 0))
    p = hpose(T, A.kexp(u, [(0, 'panic'), (1.9, 'terror')]), yaw=0.15 * math.sin(T * 3))
    A.run(p, RUNW * T, 1.4)
    k = ease(u / d)
    s = lerp(0.5, 0.95, k)
    A.hero(f, p, 540 + 20 * math.sin(T * 4), lerp(1500, 1800, k), s)
    # pursuer looming behind, eyes only plus silhouette
    A.creature(f, 560, lerp(1440, 1560, k), lerp(900, 1500, k), T, alpha=0.85, mist=1.0)
    E.snow(f, T, speed=300)
    o = Out()
    o.shake = 0.6
    return fin(f, o, T)


@shot(61.0, 63.0)
def s25_run_side_breath(T, u, d):
    f = new(T, gain=1.2)
    S.avenue(f, T, cx=RSPD * 0.7 * T, lamps=(0, 0, 0))
    p = hpose(T, R.EXPR['exhausted'], yaw=1.5708)
    A.run(p, RUNW * T, 1.5)
    A.hero(f, p, 640, GY + 30, 0.8)
    pulse = 0.5 + 0.5 * math.sin(T * 5)
    A.creature(f, 160 + 25 * math.sin(T * 8), GY + 30, 1500, T, alpha=1.0, mist=1.0)
    breath_fog(f, 800, GY - 820 * 0.8, T, 0.55, 1.0, 0.7)
    breath_fog(f, 280, 420, T, 0.8, 1.0, 1.4)
    E.snow(f, T, speed=300)
    o = Out()
    o.shake = 0.5
    return fin(f, o, T)


@shot(63.0, 64.3)
def s26_underpass(T, u, d):
    f = new(T, gain=1.35)
    S.underpass(f, T, cx=RSPD * 0.9 * T)
    p = hpose(T, R.EXPR['panic'], yaw=1.5708)
    A.run(p, RUNW * T, 1.5)
    A.hero(f, p, 560, GY + 30, 0.85)
    ca = A.keyf(u, [(0, 0), (0.4, 1)])
    A.creature(f, 120, GY + 30, 1450, T, alpha=ca, mist=1.0)
    o = Out()
    o.shake = 0.5
    return fin(f, o, T)


@shot(64.3, 65.8)
def s27_collision(T, u, d):
    f = new(T)
    S.alley(f, T, cx=0)
    hit = 0.6
    k = u / hit
    p = hpose(T, A.kexp(u, [(0, 'panic'), (1.0, 'panic'), (1.2, 'shock')]), yaw=0.0)
    A.run(p, RUNW * T, 1.3)
    xh = 540
    if u < hit:
        s = lerp(0.55, 1.05, ease(k))
        y = lerp(1450, 1760, ease(k))
        A.hero(f, p, xh, y, s)
        # stranger steps out ahead (back to camera), becomes visible as hero closes
        q = hpose(T, R.EXPR['neutral'], yaw=3.14159)
        A.stand(q)
        A.hero(f, q, 560, 1450 + 40 * ease(k), 0.55 * lerp(1, 1.0, k), black_eyes=False, tint=(0.8, 0.85, 1.0))
    else:
        w = ease((u - hit) / 0.35)
        p = hpose(T, R.EXPR['shock'], yaw=0.0)
        A.stand(p)
        p.lean = -0.3 * w
        p.hand[1] = V(120, -100, 100)
        p.hand[-1] = V(-120, -100, 100)
        A.hero(f, p, 540 - 40 * w, 1780 + 30 * w, 1.05)
        o_ = Out()
    E.snow(f, T, speed=200)
    o = Out()
    o.shake = 1.0 if 0.6 < u < 0.85 else 0.4
    o.flash = 0.35 if 0.6 < u < 0.68 else 0
    o.zoom = lerp(1.0, 1.1, u / d)
    return fin(f, o, T)


@shot(65.8, 67.05)
def s28_look_up(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.5)
    blur_bg(f, 14)
    p = hpose(T, A.kexp(u, [(0, 'shock'), (0.4, 'shock'), (1.2, 'terror')]), yaw=0.0)
    p.head_pitch = A.keyf(u, [(0, 0.5), (0.5, 0.5), (1.1, -0.25)])
    p.shake = 0.5
    A.hero(f, p, 540, 2760, 2.15, shadow=0)
    E.snow(f, T, n=40, size=5)
    o = Out()
    o.zoom = lerp(1.0, 1.12, u / d)
    return fin(f, o, T)


# --------------------------------------------------------------------- the double
def facing_pair(f, T, u, hero_e, dop_e, dop_pitch=0.0, black=False, hx=330, dx=760, y=GY + 30, s=0.95, dop_roll=0.0,
                grab=0.0, hero_pitch=0.0, struggle=0.0, dop_talk=0.0, hero_yaw_off=0.0):
    ph = hpose(T, hero_e, yaw=1.15 + hero_yaw_off, seed=1)
    A.stand(ph)
    pd = hpose(T, dop_e, yaw=-1.15, seed=5)
    A.stand(pd)
    pd.head_pitch = dop_pitch
    pd.head_roll = dop_roll
    pd.talk = dop_talk
    ph.head_pitch = hero_pitch
    if grab > 0:
        # double grips the hero's shoulders
        for sd in (1, -1):
            pd.hand_abs[sd] = V(sd * 130, 760, 260 * grab)
            pd.hand_mode[sd] = 'grip'
        pd.lean = 0.12 * grab
    if struggle:
        ph.lean = -0.1 * struggle * math.sin(T * 18)
        ph.roll = 0.08 * math.sin(T * 22) * struggle
        ph.shake = 1
    xs = hx + (math.sin(T * 20) * 8 * struggle)
    A.hero(f, ph, xs, y, s)
    A.hero(f, pd, dx, y, s, black_eyes=black)


@shot(67.05, 68.65)
def s29_before_you(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.55)
    facing_pair(f, T, u, A.kexp(u, [(0, 'terror'), (1.5, 'shock')]), 'neutral', dop_pitch=0.35)
    E.snow(f, T)
    o = Out()
    o.zoom = lerp(1.0, 1.1, u / d)
    return fin(f, o, T)


@shot(68.65, 71.7)
def s30_same_clothes(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.55)
    facing_pair(f, T, u, A.kexp(u, [(0, 'shock'), (3.0, 'mild_fear')]), 'neutral', dop_pitch=0.35)
    E.snow(f, T)
    o = Out()
    o.zoom = A.keyf(u, [(0, 1.0), (3.0, 1.35)])
    o.ox = A.keyf(u, [(0, 0), (3.0, 20)])
    o.oy = A.keyf(u, [(0, 0), (3.0, -120)])
    return fin(f, o, T)


@shot(71.7, 73.0)
def s31_black_eyes(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.4, eerie=1.0)
    blur_bg(f, 14)
    p = hpose(T, A.kexp(u, [(0, 'neutral'), (0.6, 'serious')]), yaw=0.0, seed=5)
    p.head_pitch = A.keyf(u, [(0, 0.4), (0.5, 0.4), (0.9, -0.02)])
    A.hero(f, p, 540, 2780, 2.15, shadow=0, black_eyes=True)
    f.glow(540, 760, 500, (170, 255, 210), 0.12)
    o = Out()
    o.zoom = A.keyf(u, [(0, 1.0), (1.3, 1.1)])
    o.mono = 0.2
    return fin(f, o, T)


@shot(73.0, 76.7)
def s32_grab(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.45)
    g = A.keyf(u, [(0, 0), (0.7, 1)])
    facing_pair(f, T, u, A.kexp(u, [(0, 'shock'), (1.0, 'panic')]), 'serious', black=True, hx=330 + 90 * g, dx=760 - 60 * g, grab=g,
                hero_yaw_off=0)
    f.glow(700, 700, 300, (160, 255, 210), 0.06)
    E.snow(f, T)
    o = Out()
    o.shake = 0.8 if 0.55 < u < 0.85 else 0.1
    o.zoom = lerp(1.05, 1.0, u / d)
    return fin(f, o, T)


def whisper_ecu(f, T, u, e, talk_on, pitch=0.0, roll=0.0, side=0.0):
    p = hpose(T, e, yaw=side, seed=5)
    p.head_pitch = pitch
    p.head_roll = roll
    p.talk = 0.6 * max(0, math.sin(T * 17)) * talk_on
    A.hero(f, p, 540, 2780, 2.2, shadow=0, black_eyes=True)


@shot(76.7, 79.0)
def s33_whisper(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.4, eerie=1.0)
    blur_bg(f, 14)
    whisper_ecu(f, T, u, R.EXPR['serious'], 1.0 if u < 0.7 or u > 0.9 else 0.4, roll=0.06 * math.sin(T))
    o = Out()
    o.zoom = lerp(1.0, 1.12, u / d)
    o.mono = 0.15
    return fin(f, o, T)


@shot(79.0, 81.5)
def s34_stop_running(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.4, eerie=1.0)
    blur_bg(f, 14)
    whisper_ecu(f, T, u, A.kexp(u, [(0, 'serious'), (2.4, 'pain')]), 1.0, pitch=-0.05, side=0.25)
    o = Out()
    o.zoom = lerp(1.0, 1.15, u / d)
    o.mono = 0.15
    return fin(f, o, T)


@shot(81.5, 84.0)
def s35_struggle(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.4)
    facing_pair(f, T, u, A.kexp(u, [(0, 'panic'), (2.5, 'terror')]), 'serious', black=True, hx=420, dx=760, grab=1.0, struggle=1.0)
    E.snow(f, T)
    o = Out()
    o.shake = 0.6
    o.zoom = lerp(1.0, 1.1, u / d)
    return fin(f, o, T)


@shot(84.0, 86.65)
def s36_looks_behind(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.4)
    blur_bg(f, 14)
    p = hpose(T, A.kexp(u, [(0, 'serious'), (1.3, 'worried'), (2.6, 'mild_fear')]), yaw=0.0, seed=5)
    p.e = dict(p.e)
    p.e['gx'] = A.keyf(u, [(0, 0), (1.0, 0.0), (1.6, 0.9)])
    p.e['gy'] = A.keyf(u, [(0, 0), (1.0, 0.0), (1.6, 0.6)])
    p.head_yaw = A.keyf(u, [(0, 0), (1.0, 0.0), (1.7, -0.5)])
    p.head_pitch = A.keyf(u, [(0, 0), (1.0, 0), (1.7, -0.2)])
    A.hero(f, p, 540, 2780, 2.2, shadow=0, black_eyes=True)
    o = Out()
    o.zoom = lerp(1.0, 1.1, u / d)
    return fin(f, o, T)


@shot(86.65, 90.2)
def s37_fear(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.3)
    blur_bg(f, 14)
    p = hpose(T, A.kexp(u, [(0, 'mild_fear'), (1.2, 'panic'), (3.2, 'terror')]), yaw=-0.3, seed=5)
    p.head_yaw = 0.0
    p.shake = 1
    A.hero(f, p, 540, 2800, 2.25, shadow=0, black_eyes=True)
    o = Out()
    o.zoom = A.keyf(u, [(0, 1.0), (3.5, 1.2)])
    o.shake = 0.35
    return fin(f, o, T)


@shot(90.2, 93.0)
def s38_found_us(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.25)
    rel = A.keyf(u, [(0, 0), (1.0, 1)])
    pd = hpose(T, A.kexp(u, [(0, 'terror'), (2.8, 'terror')]), yaw=-1.15, seed=5)
    A.stand(pd)
    pd.head_yaw = -0.7
    pd.hand[1] = V(120, -120 * (1 - rel), 120)
    pd.shake = 1
    ph = hpose(T, A.kexp(u, [(0, 'panic'), (2.8, 'terror')]), yaw=1.15, seed=1)
    A.stand(ph)
    ph.head_yaw = -0.4
    A.hero(f, ph, 330, GY + 30, 0.95)
    A.hero(f, pd, 760, GY + 30, 0.95, black_eyes=True)
    E.snow(f, T)
    o = Out()
    o.shake = 0.3
    return fin(f, o, T)


@shot(93.0, 95.2)
def s39_turn_head(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.25)
    blur_bg(f, 14)
    p = hpose(T, A.kexp(u, [(0, 'terror'), (2.2, 'terror')]), yaw=A.keyf(u, [(0, 0.3), (1.8, -0.9)]), seed=1)
    p.head_yaw = A.keyf(u, [(0, 0), (1.9, -0.45)])
    p.head_pitch = A.keyf(u, [(0, 0), (1.9, -0.3)])
    p.e = dict(p.e)
    p.e['gx'] = A.keyf(u, [(0, 0), (1.9, -0.8)])
    p.shake = 1
    A.hero(f, p, 540, 2800, 2.2, shadow=0)
    o = Out()
    o.zoom = lerp(1.0, 1.1, u / d)
    return fin(f, o, T)


# --------------------------------------------------------------------- the rooftop
@shot(95.2, 99.0)
def s40_rooftop(T, u, d):
    f = new(T, gain=1.15)
    info = S.rooftop_view(f, T, cam_up=A.keyf(u, [(0, 300), (3.8, 0)]))
    roof = info['roof']
    k = A.keyf(u, [(0, 0.5), (3.8, 1.0)])
    A.creature(f, 560, roof + 20, lerp(560, 820, k), T, alpha=A.keyf(u, [(0, 0), (1.2, 1)]), mist=1.0)
    E.snow(f, T, speed=100)
    o = Out()
    o.zoom = lerp(1.0, 1.08, u / d)
    return fin(f, o, T)


@shot(99.0, 102.6)
def s41_leans_down(T, u, d):
    f = new(T, gain=1.15)
    info = S.rooftop_view(f, T, cam_up=0)
    roof = info['roof']
    b = A.keyf(u, [(0, 0), (1.6, 0.0), (3.4, 1.0)])
    A.creature(f, 700, roof + 20, 820, T, bend=b, reach=A.keyf(u, [(0, 0), (3.2, 0.8)]), mist=1.0)
    # the two of them far below
    pd = hpose(T, R.EXPR['terror'], yaw=0.0)
    A.stand(pd)
    A.hero(f, pd, 440, 1860, 0.26)
    pd2 = hpose(T, R.EXPR['terror'], yaw=0.0, seed=4)
    A.stand(pd2)
    A.hero(f, pd2, 560, 1860, 0.26, black_eyes=True)
    E.snow(f, T, speed=100)
    o = Out()
    o.zoom = A.keyf(u, [(0, 1.0), (3.6, 1.12)])
    o.shake = 0.15 + 0.3 * (1 if u > 3.0 else 0)
    return fin(f, o, T)


@shot(102.6, 105.0)
def s42_who_is_real(T, u, d):
    f = new(T)
    S.courtyard(f, T, lamp_on=0.15)
    blur_bg(f, 16)
    ph = hpose(T, A.kexp(u, [(0, 'terror'), (2.4, 'dead')]), yaw=0.35, seed=1)
    ph.head_pitch = -0.3
    ph.shake = 1
    A.hero(f, ph, 330, 2760, 2.1, shadow=0)
    pd = hpose(T, A.kexp(u, [(0, 'terror'), (2.4, 'dead')]), yaw=-0.35, seed=5)
    pd.head_pitch = -0.3
    pd.shake = 1
    A.hero(f, pd, 780, 2760, 2.1, shadow=0, black_eyes=True)
    # shadow falls over them
    f.fg.c.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 8), A.keyf(u, [(0, 0), (2.4, 0.55)])))
    o = Out()
    o.zoom = lerp(1.0, 1.1, u / d)
    return fin(f, o, T)


@shot(105.0, 108.4)
def s43_black(T, u, d):
    f = new(T)
    f.bg.c.clear(skia.Color4f(0, 0, 0, 1))
    f.set_ambient((0.75, 0.75, 0.75))
    cv = f.fg.c
    a = A.keyf(u, [(0.3, 0), (1.2, 1), (3.2, 1), (3.4, 0)])
    ea = A.keyf(u, [(0, 0), (0.3, 0.9), (0.8, 0.0)])
    fo = skia.Font(E.TF, 68)
    t1 = 'ПРОДОЛЖЕНИЕ СЛЕДУЕТ'
    wd = fo.measureText(t1)
    cv.drawString(t1, 540 - wd / 2, 980, fo, P((235, 238, 250), a))
    for sd in (-1, 1):
        f.glow(540 + 70 * sd, 800, 110, (225, 232, 255), 0.7 * ea)
    o = Out()
    o.fade = A.keyf(u, [(0, 1), (3.3, 1), (3.4, 0)]) if False else 1.0
    return fin(f, o, T)
