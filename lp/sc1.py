"""Scenes 1–3: college street, bus stop, arrival, boarding, passengers, the repeating stop, walk to the driver."""
from common import *  # noqa: F401,F403
from common import (math, random, skia, R, V, T2, M, Wd, E, P, lin, rad, path_poly, mix, EX, W, H, voice, integ, push,
                    blur_layer, shake, LK, STREET_LK, BUS_LK, fig, hero_walk, lerp_pose_sit, arm_into_frame, rain, puddles, flick)

STOP_NAME = 'ул. Лесная'
GY = 1500


# ------------------------------------------------------------------ side view of the interior (across the aisle)
def side_interior(cv, t, cx=0.0, gy=1640, s=0.75, moving=1.0, L=1.0, door_x=None, door=0.0, outside=None, seats=True):
    """wall + window band + seats in profile; the bus front is to screen-left. cx = camera pan (px)."""
    wall = mix((10, 14, 14), (58, 74, 66), L)
    cv.drawRect(skia.Rect(0, 0, W, H), P(wall))
    cv.drawRect(skia.Rect(0, 0, W, 260), P(mix((8, 10, 10), (84, 100, 92), L)))     # ceiling
    for k in range(-1, 4):
        x = k * 520 - cx % 520
        cv.drawRect(skia.Rect(x + 60, 180, x + 380, 206), P(mix((40, 44, 44), (236, 252, 240), L)))   # strip light
    wy0, wy1 = 470, gy - 98 * 6.6 * s + 40
    seg = 360
    for k in range(-1, 5):
        x0 = k * seg - (cx % seg) + 20
        x1 = x0 + seg - 40
        if door_x is not None and abs((x0 + x1) / 2 - door_x) < seg * 0.6:
            continue
        cv.drawRect(skia.Rect(x0, wy0, x1, wy1), P((6, 9, 18)))
        cv.save(); cv.clipRect(skia.Rect(x0, wy0, x1, wy1))
        if outside:
            outside(cv, t, x0, wy0, x1, wy1)
        else:
            for j in range(4):    # street lights sliding past (bus moves left -> lights go right)
                u = ((t * 0.55 * moving + j / 4 + k * 0.13) % 1.0)
                lx = x0 - 200 + u * (seg + 400)
                cv.drawCircle(lx, wy0 + 90, 34, P(E.SODIUM, 0.75 * moving, blur=14))
                cv.drawRect(skia.Rect(lx - 3, wy0 + 100, lx + 3, wy1), P((14, 16, 24), 0.8))
            cv.drawRect(skia.Rect(x0, wy1 - 120, x1, wy1), P((16, 18, 28)))
        cv.drawRect(skia.Rect(x0, wy0, x1, wy1), P(E.FLUO, 0.07 * L))     # reflection of the interior
        cv.restore()
        cv.drawRect(skia.Rect(x0, wy0, x1, wy1), P(mix((8, 10, 10), (38, 46, 42), L), style='stroke', width=14))
    cv.drawRect(skia.Rect(0, gy - 6, W, H), P(mix((6, 7, 8), (40, 44, 42), L)))    # floor
    cv.drawRect(skia.Rect(0, wy1 + 8, W, wy1 + 30), P(mix((10, 12, 12), (90, 96, 90), L)))   # sill rail
    if door_x is not None:
        dx0, dx1 = door_x - 230, door_x + 230
        cv.drawRect(skia.Rect(dx0, 300, dx1, gy), P((10, 12, 18)))
        if outside:
            cv.save(); cv.clipRect(skia.Rect(dx0, 300, dx1, gy)); outside(cv, t, dx0, 300, dx1, gy); cv.restore()
        hw = (dx1 - dx0) / 2
        for sd in (0, 1):
            w_ = hw * (1 - 0.8 * door)
            lx = dx0 if sd == 0 else dx1 - w_
            cv.drawRect(skia.Rect(lx, 300, lx + w_, gy), P(mix((10, 12, 12), (56, 64, 60), L)))
            cv.drawRect(skia.Rect(lx + 14, 330, lx + w_ - 14, gy - 260), P(mix((6, 8, 14), (40, 56, 56), L * 0.6)))
            cv.drawRect(skia.Rect(lx, 300, lx + w_, gy), P((8, 8, 8), style='stroke', width=8))
    # poles
    for k in range(-1, 4):
        x = k * 720 - cx % 720 + 300
        cv.drawRect(skia.Rect(x - 9, 200, x + 9, gy), P(mix((24, 26, 26), (170, 176, 170), L * 0.9)))
    return wy0, wy1


def seat_profile(cv, x, gy, s, L=1.0, front=False):
    """bus seat seen from the side, facing screen-left. x = cushion centre."""
    u = 6.6 * s
    col = mix((16, 10, 10), (106, 44, 38), L)
    if not front:
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x + 18 * u, gy - 102 * u, x + 30 * u, gy - 42 * u), 6 * u, 6 * u), P(mix(col, (0, 0, 0), 0.15)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 24 * u, gy - 50 * u, x + 28 * u, gy - 40 * u), 4 * u, 4 * u), P(col))
    cv.drawRect(skia.Rect(x - 2 * u, gy - 40 * u, x + 4 * u, gy), P(mix((20, 20, 20), (80, 82, 80), L)))
    cv.drawLine(x + 24 * u, gy - 102 * u, x + 24 * u, gy - 112 * u, P(mix((30, 30, 30), (190, 190, 186), L), style='stroke', width=3 * u))


# ------------------------------------------------------------------ A1 college
def A1(cv, t):
    """0–2.86 «Ты выходишь из колледжа в 11 вечера.»"""
    cx = 30 * t
    z = M.keys(t, [(0, 1.06), (2.86, 1.0)])
    push(cv, z, W * 0.5, H * 0.65)
    door = M.keys(t, [(0.1, 0.0), (0.6, 1.0), (1.5, 1.0), (2.2, 0.0)])
    E.college(cv, t, cx=cx, door_open=door)
    Wd.lamp(cv, 1000 - cx, GY + 120, 820, side=-1)
    puddles(cv, GY, cx, t)
    # he steps out of the doors, then turns right along the pavement
    t0 = 0.35
    if t >= t0:
        u = t - t0
        yaw = M.keys(t, [(t0, 0.15), (1.2, 0.15), (1.8, 1.1)])
        p = hero_walk(u, cad=0.95, mood=0.2)
        p.e = EX['tired']; p.blink = M.blink_at(t, [1.4])
        p.head_pitch = 0.08
        dx = integ(lambda x: 660 * 0.52 * 0.95 * math.sin(M.keys(x, [(t0, 0.15), (1.2, 0.15), (1.8, 1.1)])), t0, t)
        dy = integ(lambda x: 660 * 0.52 * 0.95 * math.cos(M.keys(x, [(t0, 0.15), (1.2, 0.15), (1.8, 1.1)])) * 0.25, t0, t)
        fig(cv, 'hero', p, 570 - cx + dx, GY - 6 + dy, 0.52, yaw=yaw, lk=LK(**STREET_LK))
    rain(cv, t, cx=cx)
    return dict(vign=0.55)


# ------------------------------------------------------------------ A2 phone low battery
def phone_body(cv, x, y, w, h, rot=0.0):
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    cv.drawRoundRect(skia.Rect(-w / 2 - 22, -h / 2 - 22, w / 2 + 22, h / 2 + 22), 70, 70, P((14, 14, 18)))
    scr = skia.Rect(-w / 2, -h / 2, w / 2, h / 2)
    return scr


def status_bar(cv, scr, batt=0.03, time_s='23:04', blink=True, t=0.0):
    f = E.font(30)
    cv.drawString(time_s, scr.left() + 50, scr.top() + 56, f, P((230, 232, 240)))
    bx, by = scr.right() - 120, scr.top() + 30
    cv.drawRoundRect(skia.Rect(bx, by, bx + 60, by + 30), 6, 6, P((230, 232, 240), style='stroke', width=3))
    on = (not blink) or (int(t * 2.5) % 2 == 0)
    cv.drawRect(skia.Rect(bx + 4, by + 4, bx + 4 + 52 * max(batt, 0.04), by + 26), P((240, 60, 50), 1.0 if on else 0.3))
    cv.drawRect(skia.Rect(bx + 62, by + 9, bx + 67, by + 21), P((230, 232, 240)))
    cv.drawString(f'{int(round(batt * 100))}%', bx - 70, by + 26, f, P((240, 80, 70)))


def A2(cv, t):
    """2.86–4.56 «Телефон почти разряжен.» ECU: lock screen, battery 3 %"""
    u = t - 2.86
    blur_layer(cv, 22)
    E.college(cv, t, cx=300)
    Wd.lamp(cv, 700, GY + 120, 820, side=-1)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 10), 0.35))
    rot = -6 + 1.5 * math.sin(t * 1.1)
    scr = phone_body(cv, W / 2 + 10 * math.sin(t * 0.9), H * 0.47, 600, 1150, rot)
    lit = M.keys(t, [(2.9, 0.0), (3.1, 1.0), (4.2, 1.0), (4.5, 0.55)])
    cv.drawRoundRect(scr, 50, 50, P(shader=lin((0, scr.top()), (0, scr.bottom()), mix((6, 6, 10), (40, 50, 80), lit), mix((6, 6, 10), (16, 18, 34), lit))))
    if lit > 0.1:
        status_bar(cv, scr, 0.03, '23:04', t=t)
        E.text_c(cv, '23:04', 0, scr.top() + 300, 170, (235, 238, 248), lit)
        E.text_c(cv, 'среда, 13 ноября', 0, scr.top() + 370, 40, (200, 206, 224), lit)
        # low battery banner
        k = M.smooth((t - 3.25) / 0.3)
        if k > 0:
            r = skia.Rect(scr.left() + 30, scr.top() + 470 - 30 * (1 - k), scr.right() - 30, scr.top() + 640 - 30 * (1 - k))
            cv.drawRoundRect(r, 34, 34, P((40, 40, 50), 0.92 * k))
            cv.drawString('Низкий заряд батареи', r.left() + 36, r.top() + 66, E.font(38), P((245, 245, 250), k))
            cv.drawString('Осталось 3%. Подключите зарядку.', r.left() + 36, r.top() + 120, E.font(30), P((200, 204, 216), k))
    # rain drops on the glass
    rr = random.Random(7)
    for i in range(26):
        x = rr.uniform(scr.left(), scr.right()); y = rr.uniform(scr.top(), scr.bottom()) + (t * rr.uniform(10, 40)) % 60
        rd = rr.uniform(6, 16)
        cv.drawCircle(x, y, rd, P((200, 210, 240), 0.10 + 0.08 * lit))
        cv.drawCircle(x - rd * 0.3, y - rd * 0.3, rd * 0.3, P((255, 255, 255), 0.25))
    cv.restore()
    # his fingers around the phone
    for sd in (-1, 1):
        cv.drawOval(skia.Rect(W / 2 + sd * 335 - 60, H * 0.56, W / 2 + sd * 335 + 60, H * 0.56 + 300), P((214, 176, 168)))
    cv.drawCircle(W / 2, H * 0.47, 800, P(shader=rad((W / 2, H * 0.47), 800, (140, 170, 255), (140, 170, 255), 0.12 * lit, 0.0)))
    rain(cv, t, n=90, alpha=0.25, ln=70)
    return dict(vign=0.7)


# ------------------------------------------------------------------ A3 bus stop
def A3(cv, t):
    """4.56–6.52 «На остановке никого.» he walks into the empty shelter and stops"""
    z = M.keys(t, [(4.56, 1.0), (6.52, 1.05)])
    push(cv, z, W * 0.5, H * 0.6)
    Wd.sky(cv, *E.NIGHT, GY)
    for i in range(-1, 5):
        Wd.panel_building(cv, i * 330 - 80, 300, GY - 820 - (i * 131) % 200, GY - 250, (24, 30, 46), seed=90 + i, lit=0.08, floor_h=66, t=t)
    E.wires(cv, 0, 220)
    Wd.street_ground(cv, GY, 0)
    E.bus_stop(cv, 600, GY + 40, 1.15, STOP_NAME, lit=E and (0.85 + 0.15 * flick(t, [(5.6, 0.25)])))
    Wd.lamp(cv, 960, GY + 160, 860, side=-1)
    puddles(cv, GY, 0, t, seed=8)
    amp = M.keys(t, [(4.56, 1.0), (5.7, 1.0), (6.1, 0.0)])
    ph = integ(lambda x: 0.95 * M.keys(x, [(4.56, 1.0), (5.7, 1.0), (6.1, 0.0)]), 4.56, t)
    x = 120 + 660 * 0.5 * math.sin(1.2) * ph
    p = R.Pose()
    if amp > 0.02:
        M.walk(p, ph, amp=amp, mood=0.3)
    else:
        M.stand(p, t=t)
    p.e = EX['tired']; p.head_yaw = M.keys(t, [(5.9, 0.0), (6.3, -0.5)])
    p.blink = M.blink_at(t, [6.0])
    fig(cv, 'hero', p, x, GY + 80, 0.5, yaw=M.keys(t, [(5.8, 1.2), (6.3, 0.5)]), lk=LK(**STREET_LK))
    rain(cv, t)
    return dict(vign=0.6)


# ------------------------------------------------------------------ A4 the bus arrives
def A4a(cv, t):
    """6.52–8.6 headlights grow out of the dark street; they light up his face"""
    u = (t - 6.52) / 2.08
    Wd.sky(cv, *E.NIGHT, 1150)
    # street receding to the left, vanishing point at (260, 1150)
    for i in range(6):
        k = 1 / (1 + i * 0.7)
        x = 260 + 700 * k
        Wd.panel_building(cv, x - 380 * k, 340 * k, 1150 - 900 * k, 1150 - 40 * k, (22, 28, 44), seed=120 + i, lit=0.06, floor_h=70 * k, t=t)
    cv.drawPath(path_poly([(260, 1150), (W + 400, 2100), (-600, 2100)]), P((24, 28, 40)))
    cv.drawPath(path_poly([(260, 1150), (300, 2100), (180, 2100)]), P((60, 64, 72), 0.4))
    s = 0.12 + 0.75 * u ** 2.2
    hl = M.keys(t, [(6.6, 0.0), (7.0, 1.0)])
    E.bus_front(cv, 260 + 200 * u ** 2, 1150 + 600 * u ** 2.2, s, t, head_on=hl, bob=2 * math.sin(t * 9))
    rain(cv, t, n=170, alpha=0.36)
    # him in the foreground, turning toward the light
    p = R.Pose(); M.stand(p, t=t)
    p.head_yaw = M.keys(t, [(6.9, 0.0), (7.6, -0.75)])
    p.e = M.kexpr(t, [(6.52, 'tired'), (7.6, EX['tired'] | dict(lid=0.25, gx=-0.8)), (8.4, EX['neutral'] | dict(lid=0.45, gx=-0.9))], EX)
    lit = hl * (0.3 + 0.7 * u)
    lk = LK(key=(-1.0, -0.2), rim=(255, 240, 210), rim_w=6 + 6 * lit, tint=tuple(0.72 + 0.35 * lit for _ in range(3)), rim_dir=(-0.9, -0.2))
    fig(cv, 'hero', p, 780, 2350, 1.6, yaw=0.55, lk=lk, ground_shadow=0)
    cv.drawRect(skia.Rect(0, 0, W, H), P((255, 240, 210), 0.10 * lit * u))
    return dict(vign=0.62)


def A4b(cv, t):
    """8.6–10.22 side view: the bus pulls in, brakes, the doors open"""
    stop = 9.55
    xs = M.keys(t, [(8.6, -380), (stop, 540)], fn=lambda x: 1 - (1 - x) ** 2.2)
    dive = 6 * math.exp(-max(0, t - stop) * 4) * math.sin(max(0, t - stop) * 9) if t > stop else 0
    door = M.keys(t, [(9.7, 0.0), (10.15, 1.0)])
    Wd.sky(cv, *E.NIGHT, 1300)
    for i in range(-1, 5):
        Wd.panel_building(cv, i * 330 - 60, 300, 1300 - 760 - (i * 97) % 200, 1300 - 200, (22, 28, 44), seed=140 + i, lit=0.08, floor_h=62, t=t)
    E.wires(cv, 0, 200)
    Wd.street_ground(cv, 1330, 0)
    E.bus_side(cv, xs, 1420, 0.92, t * (1 if t < stop else 0) + (stop if t >= stop else 0), bob=0, roll=math.radians(dive * 0.25), door=door)
    # the stop + him in the foreground, back to us
    E.bus_stop(cv, 840, 1760, 1.0, STOP_NAME)
    p = R.Pose(); M.stand(p, t=t); p.head_yaw = M.keys(t, [(8.6, -0.4), (9.6, 0.1)])
    fig(cv, 'hero', p, 560, 1820, 0.62, yaw=math.pi - 0.3, lk=LK(**STREET_LK))
    puddles(cv, 1760, 0, t, seed=2)
    rain(cv, t, n=170)
    return dict(vign=0.6)


# ------------------------------------------------------------------ B1 boarding
def B1(cv, t):
    """10.22–11.68 «Ты заходишь внутрь.» behind him at the open door"""
    u = (t - 10.22) / 1.46
    Wd.sky(cv, *E.NIGHT, 1700)
    E.bus_side(cv, 300, 1900, 2.3, 9.55, door=1.0)
    p = hero_walk(t - 10.22, cad=0.9, mood=0.2, amp=0.8)
    step = M.keys(t, [(10.5, 0.0), (10.75, 1.0), (11.0, 1.0), (11.25, 2.0)])
    s = 0.95 - 0.12 * u
    fig(cv, 'hero', p, 480 + 30 * u, 1980 - 60 * step - 120 * u, s, yaw=math.pi + 0.15, lk=LK(key=(0.0, -1.0), rim=E.FLUO, rim_w=8))
    rain(cv, t, n=160, alpha=0.3)
    return dict(vign=0.6)


# ------------------------------------------------------------------ B2 seven silent passengers
PAX = [(-80, 360, 'pax0'), (80, 460, 'pax1'), (-80, 560, 'pax2'), (80, 660, 'pax3'), (-80, 760, 'pax4'), (80, 860, 'pax5')]


def passengers(cv, cam, t, look=+1, babka_e=None, babka_pitch=0.35, alive=0.0, hang=True, skip=()):
    items = []
    for i, (x, z, nm) in enumerate(PAX):
        if nm in skip:
            continue

        def fn(x=x, z=z, nm=nm, i=i):
            X, Y, s = E.person_at(cam, x, z - 30)
            p = R.Pose(); M.sit(p, t=t, breath=alive * 0.2)
            p.e = EX['blank']
            p.head_pitch = 0.18 + 0.05 * (i % 2)
            p.head_yaw = [0.05, -0.1, 0.0, 0.12, -0.05, 0.0][i]
            if nm == 'pax2' and hang:
                p.head_roll = 0.7; p.head_pitch = 0.55   # head hanging at a wrong angle
            fig(cv, nm, p, X, Y, s, yaw=0.0 if look > 0 else math.pi, ground_shadow=0)
        items.append((z, fn))

    def babka(cam=cam):
        X, Y, s = E.person_at(cam, 0, E.REAR_Z - 30)
        p = R.Pose(); M.sit(p, t=t, breath=0.0)
        p.e = babka_e or EX['babka_calm']
        p.head_pitch = babka_pitch
        fig(cv, 'babka', p, X, Y, s, yaw=0.0 if look > 0 else math.pi, ground_shadow=0, lk=LK(key=(0.0, -1.0), rim=None, tint=(0.6, 0.66, 0.62)))
    items.append((E.REAR_Z, babka))
    return items


def B2(cv, t):
    """11.68–14.96 «В салоне сидят 7 человек. Все молчат.» slow push down the aisle"""
    cz = M.keys(t, [(11.68, -40), (14.96, 90)])
    cam = E.Persp(6 * math.sin(t * 0.7), 165, cz, look=+1, f=800)
    fl = flick(t, [(13.9, 0.22)])
    E.bus_interior(cv, t, cam, flicker=fl, moving=0.0, items=passengers(cv, cam, t), rear_dark=0.65)
    return dict(vign=0.62)


# ------------------------------------------------------------------ B3 pay + sit
def B3a(cv, t):
    """14.96–16.3 validator: his card taps, the screen turns green"""
    u = t - 14.96
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), (36, 46, 42), (14, 18, 18))))
    blur_layer(cv, 16)
    cam = E.Persp(40, 165, 80, look=+1, f=700)
    E.bus_interior(cv, t, cam, moving=0.0, items=passengers(cv, cam, t), rear_dark=0.6)
    cv.restore()
    # pole + yellow validator
    cv.drawRect(skia.Rect(470, 0, 520, H), P((150, 156, 150)))
    vx, vy = 520, 820
    cv.drawRoundRect(skia.Rect(vx - 260, vy - 330, vx + 160, vy + 330), 40, 40, P((214, 170, 40)))
    cv.drawRoundRect(skia.Rect(vx - 220, vy - 280, vx + 120, vy - 40), 20, 20, P((20, 24, 26)))
    paid = t > 15.3
    col = (60, 200, 110) if paid else (60, 70, 80)
    cv.drawRoundRect(skia.Rect(vx - 200, vy - 260, vx + 100, vy - 60), 14, 14, P(col, 0.9))
    E.text_c(cv, 'ОПЛАЧЕНО' if paid else 'ПРИЛОЖИТЕ', vx - 50, vy - 175, 40, (240, 255, 244))
    E.text_c(cv, 'КАРТУ' if not paid else '✓', vx - 50, vy - 110, 40 if not paid else 60, (240, 255, 244))
    cv.drawRoundRect(skia.Rect(vx - 200, vy + 20, vx + 100, vy + 260), 30, 30, P((40, 40, 40)))
    E.text_c(cv, '))))', vx - 50, vy + 160, 70, (200, 200, 200), 0.5)
    if paid:
        cv.drawCircle(vx - 50, vy - 160, 300, P((60, 220, 120), 0.18 * math.exp(-(t - 15.3) * 2), blur=60))
    # his hand with a card
    k = M.keys(t, [(14.96, 0.0), (15.25, 1.0), (15.7, 1.0), (16.2, 0.2)])
    tip = (vx - 50 + 600 * (1 - k), vy + 140 + 200 * (1 - k))
    cv.save(); cv.translate(tip[0] - 20, tip[1] - 80); cv.rotate(-12)
    cv.drawRoundRect(skia.Rect(-150, -95, 150, 95), 16, 16, P((40, 90, 160)))
    cv.drawRect(skia.Rect(-150, -50, 150, -20), P((20, 40, 80)))
    cv.drawString('ТРОЙКА', -120, 60, E.font(40), P((230, 236, 255)))
    cv.restore()
    arm_into_frame(cv, (W + 300, H * 0.75), tip, w=95, hand_r=70)
    return dict(vign=0.62)


def B3b(cv, t):
    """16.3–17.96 he sits down by the window"""
    s = 0.78
    gy = 1660
    wy = side_interior(cv, t, cx=0, gy=gy, s=s, moving=0.0)
    seat_x = 520
    for sx in (seat_x - 380, seat_x + 380):
        seat_profile(cv, sx, gy, s)
    seat_profile(cv, seat_x, gy, s)
    k = M.keys(t, [(16.75, 0.0), (17.4, 1.0)])
    walk_amp = M.keys(t, [(16.3, 1.0), (16.7, 0.0)])
    if t < 16.75:
        ph = integ(lambda x: 0.9 * M.keys(x, [(16.3, 1.0), (16.7, 0.0)]), 16.3, t)
        p = R.Pose(); M.walk(p, ph, amp=max(walk_amp, 0.001), mood=0.2) if walk_amp > 0.02 else M.stand(p, t=t)
        x = seat_x + 260 - 660 * s * ph
        yaw = -1.57 + 0.0
    else:
        p = lerp_pose_sit(t, k)
        x = seat_x + 40 * 6.6 * s * k * 0.0 + 30
        yaw = M.keys(t, [(16.75, -1.57), (17.0, -1.2), (17.4, -1.57)])
    p.e = EX['tired']; p.blink = M.blink_at(t, [17.6])
    p.head_yaw = M.keys(t, [(17.5, 0.0), (17.9, 0.5)])
    fig(cv, 'hero', p, x, gy, s, yaw=yaw)
    seat_profile(cv, seat_x - 380, gy, s, front=True)
    return dict(vign=0.6)


# ------------------------------------------------------------------ B4 the bus moves off
def B4(cv, t):
    """17.96–19.46 «Автобус трогается.» exterior, the bus pulls away with a lurch"""
    u = t - 17.96
    xs = 540 + 260 * u ** 2
    sway = -math.radians(1.6) * math.exp(-u * 2) * math.sin(u * 5)
    Wd.sky(cv, *E.NIGHT, 1300)
    for i in range(-1, 5):
        Wd.panel_building(cv, i * 330 - 60, 300, 1300 - 760 - (i * 97) % 200, 1300 - 200, (22, 28, 44), seed=140 + i, lit=0.08, floor_h=62, t=t)
    E.wires(cv, 0, 200)
    Wd.street_ground(cv, 1330, 0)
    E.bus_side(cv, xs, 1420, 0.92, 9.55 + u ** 2 * 3, roll=sway, door=0.0)
    for k in range(3):    # exhaust
        a = (u * 1.3 + k * 0.33) % 1.0
        cv.drawCircle(xs - 520 * 0.92 - 60 - 120 * a, 1390 - 40 * a, 30 + 70 * a, P((150, 150, 160), 0.18 * (1 - a), blur=20))
    E.bus_stop(cv, 840, 1760, 1.0, STOP_NAME)
    puddles(cv, 1760, 0, t, seed=2)
    rain(cv, t, n=170)
    return dict(vign=0.6)


# ------------------------------------------------------------------ B5 seated, the strangeness
def B5(cv, t):
    """19.46–22.12 seated by the window; light bands sweep; behind him a head hangs wrong"""
    cam = E.Persp(60, 125, 280, look=+1, f=820, vx=W * 0.5)
    items = passengers(cv, cam, t, skip=('pax0',))
    E.bus_interior(cv, t, cam, moving=1.0, items=items, rear_dark=0.6)
    # him in the foreground right, seated by the window, 3/4 view
    p = R.Pose(); M.sit(p, t=t)
    p.e = M.kexpr(t, [(19.46, 'tired'), (20.8, 'tired'), (21.2, EX['neutral'] | dict(lid=0.15, gx=0.7)), (22.1, EX['suspicious'] | dict(gx=0.9))], EX)
    p.head_yaw = M.keys(t, [(20.9, 0.15), (21.5, 0.7)])
    p.blink = M.blink_at(t, [20.2])
    sweep = 0.5 + 0.5 * math.sin(t * 3.4)
    lk = LK(key=(1.0, -0.3), rim=E.SODIUM, rim_w=4 + 8 * sweep, tint=(0.85, 0.92, 0.9), rim_dir=(0.95, -0.2))
    fig(cv, 'hero', p, 760, 2300, 1.25, yaw=-0.55, lk=lk, ground_shadow=0)
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((W, 0), (W * 0.4, 0), E.SODIUM, E.SODIUM, 0.14 * sweep, 0.0)))
    return dict(vign=0.66)


# ------------------------------------------------------------------ C: the same stop, again
def street_outside(cv, t, x0, y0, x1, y1, speed=520.0, stop_at=None, sign_scale=1.0):
    """what passes the window: lamps, buildings; the same bus stop at time stop_at (crossing the window)"""
    w = x1 - x0
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(shader=lin((0, y0), (0, y1), (10, 14, 28), (22, 26, 40))))
    off = t * speed
    for i in range(-2, 8):
        bx = x0 + i * 300 + (off * 0.3) % 300 - 300
        cv.drawRect(skia.Rect(bx, y0 + 60, bx + 240, y1), P((20, 24, 38)))
        for r_ in range(4):
            for c_ in range(3):
                if (i * 7 + r_ * 3 + c_) % 6 == 0:
                    cv.drawRect(skia.Rect(bx + 20 + c_ * 76, y0 + 90 + r_ * 70, bx + 60 + c_ * 76, y0 + 130 + r_ * 70), P((200, 150, 90), 0.7))
    for i in range(-1, 6):
        lx = x0 + i * 520 + off % 520 - 520
        cv.drawRect(skia.Rect(lx - 5, y0 + 40, lx + 5, y1), P((12, 14, 22)))
        cv.drawCircle(lx, y0 + 50, 40, P(E.SODIUM, 0.8, blur=16))
    if stop_at is not None:
        sx = x0 + w / 2 + (t - stop_at) * speed
        E.bus_stop(cv, sx, y1 + 10, 0.85 * sign_scale, STOP_NAME)


def C1(cv, t):
    """22.12–25.76 POV through the window: the same stop passes"""
    cv.drawRect(skia.Rect(0, 0, W, H), P((30, 38, 36)))
    x0, y0, x1, y1 = 60, 360, 1020, 1520
    cv.save(); cv.clipRect(skia.Rect(x0, y0, x1, y1))
    push(cv, M.keys(t, [(22.12, 1.0), (25.76, 1.08)]), W / 2, H * 0.5)
    street_outside(cv, t, x0 - 200, y0, x1 + 200, y1, speed=380, stop_at=24.0)
    cv.restore()
    # his reflection in the glass
    cv.saveLayer(None, P((255, 255, 255), 0.16))
    p = R.Pose(); M.sit(p, t=t); p.e = EX['neutral'] | dict(gx=-0.6)
    fig(cv, 'hero', p, 620, 2600, 1.7, yaw=0.3, lk=LK(rim=None), ground_shadow=0)
    cv.restore()
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(E.FLUO, 0.05))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P((40, 48, 44), style='stroke', width=40))
    cv.drawRect(skia.Rect(0, y1 + 20, W, y1 + 60), P((120, 126, 120)))
    return dict(vign=0.62)


def C2(cv, t):
    """25.76–28.08 «Ты думаешь, что водитель поехал по кругу.» he looks toward the front"""
    cam = E.Persp(-40, 125, 700, look=-1, f=820, vx=W * 0.42)
    items = passengers(cv, cam, t, look=-1, skip=('pax0', 'pax1', 'pax2', 'pax3', 'pax4'))
    items.append((40, lambda: driver_back(cv, cam, t)))
    E.bus_interior(cv, t, cam, moving=1.0, items=items, rear_dark=0.3)
    p = R.Pose(); M.sit(p, t=t)
    p.lean = M.keys(t, [(26.2, 0.06), (27.0, 0.2)])
    p.head_yaw = M.keys(t, [(25.9, 0.6), (26.6, 0.0)])
    p.e = M.kexpr(t, [(25.76, EX['suspicious'] | dict(gx=0.9)), (26.6, EX['confusion'] | dict(gx=0.0, gy=0.0)), (28.0, EX['suspicious'] | dict(gx=-0.2))], EX)
    p.blink = M.blink_at(t, [27.3])
    fig(cv, 'hero', p, 860, 2250, 1.15, yaw=2.6, lk=LK(key=(0.4, -0.8), rim=E.SODIUM, rim_w=6), ground_shadow=0)
    return dict(vign=0.64)


def driver_back(cv, cam, t, head_yaw=0.0, e=None, turn=0.0):
    X, Y, s = E.person_at(cam, -70, 70)
    p = R.Pose(); M.sit(p, t=t, breath=0.0)
    p.head_yaw = head_yaw
    p.e = e or EX['closed']
    for sd in (1, -1):
        p.hand[sd] = V(40 * sd, -150, 260)
    fig(cv, 'driver', p, X, Y, s, yaw=math.pi if cam.look < 0 else 0.0, ground_shadow=0)
    # cabin partition with glass behind him
    q0, q1 = cam.p(-125, 200, 150), cam.p(-10, 0, 150)


def C3(cv, t):
    """28.08–31.7 «Но через минуту остановка появляется снова.» the sign slides into frame and stops"""
    cv.drawRect(skia.Rect(0, 0, W, H), P((30, 38, 36)))
    x0, y0, x1, y1 = 0, 200, W, 1700
    cv.save(); cv.clipRect(skia.Rect(x0, y0, x1, y1))
    sp = M.keys(t, [(28.08, 300), (29.6, 120), (30.4, 0.0)])
    xs = M.keys(t, [(28.08, -700), (29.6, 300), (30.6, 540)], fn=lambda u: 1 - (1 - u) ** 2)
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(shader=lin((0, y0), (0, y1), (10, 14, 28), (22, 26, 40))))
    for i in range(-1, 4):
        lx = i * 520 + (t * sp) % 520
        cv.drawCircle(lx, y0 + 140, 60, P(E.SODIUM, 0.6, blur=30))
    E.stop_sign(cv, xs, 760, 2.2, STOP_NAME)
    cv.drawRect(skia.Rect(xs - 14, 760 + 2.2 * 200, xs + 14, y1), P((50, 54, 64)))
    rain(cv, t, n=120, alpha=0.3)
    cv.restore()
    fl = flick(t, [(30.4, 0.5)], depth=0.9)
    cv.drawRect(skia.Rect(0, 0, W, H), P(E.FLUO, 0.08 * fl))
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), 0.55 * (1 - fl)))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P((34, 42, 38), style='stroke', width=50))
    return dict(vign=0.66)


def C4(cv, t):
    """31.7–36.14 he walks up the aisle to the driver; asks; silence. Camera follows behind."""
    walk_end = 33.1
    ph = integ(lambda x: 0.95 * M.keys(x, [(31.7, 1.0), (32.8, 1.0), (walk_end, 0.0)]), 31.7, t)
    hz = 640 - 660 / 6.6 * ph          # his z along the bus (cm)
    cz = hz + 170
    fl = flick(t, [(32.5, 0.3)])
    cam = E.Persp(15, 165, cz, look=-1, f=800)
    items = passengers(cv, cam, t, look=-1)
    items.append((40, lambda: driver_back(cv, cam, t)))

    def hero():
        X, Y, s = E.person_at(cam, 10, hz)
        amp = M.keys(t, [(31.7, 1.0), (32.8, 1.0), (walk_end, 0.0)])
        p = R.Pose()
        if amp > 0.02:
            M.walk(p, ph, amp=amp, mood=0.5)
        else:
            M.stand(p, t=t)
        p.head_pitch = 0.05 * voice(t, 33.18, 34.9)
        p.lean = 0.08 * M.keys(t, [(33.1, 0.0), (33.5, 1.0)])
        fig(cv, 'hero', p, X, Y, s, yaw=math.pi, ground_shadow=0.3)
    items.append((hz, hero))
    E.bus_interior(cv, t, cam, flicker=fl, moving=1.0, items=items, rear_dark=0.2)
    return dict(vign=0.64)
