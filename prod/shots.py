import wave
from lib import *
from rig import *
from env import *

# ---------------------------------------------------------------- narration envelope (mouth sync)
_wf = wave.open('n16.wav')
_A = np.frombuffer(_wf.readframes(_wf.getnframes()), np.int16).astype(np.float32) / 32768
_hop = 16000 // FPS
_n = len(_A) // _hop + 2
ENV = np.array([np.sqrt(np.mean(_A[i * _hop:(i + 1) * _hop] ** 2) + 1e-9) for i in range(_n)])
ENV = np.clip(ENV / np.percentile(ENV, 95), 0, 1.2)


def env(T):
    i = int(T * FPS)
    return float(ENV[min(max(i, 0), len(ENV) - 1)])


def blink(t, period=3.1, off=0.0):
    ph = (t + off) % period
    return clamp(1 - abs(ph - 0.08) / 0.08) if ph < 0.16 else 0.0


def cam(c, dx=0.0, dy=0.0, zoom=1.0, rot=0.0, cx=540, cy=960):
    c.translate(cx + dx, cy + dy)
    c.rotate(rot)
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)


def blurred(c, sigma, fn):
    c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma, skia.TileMode.kClamp)))
    fn()
    c.restore()


def char_t(c, T, key, x, z, pose, t, back=True, hold=None, I=1.0, wet=True, extra_dark=0.0, rimc='#9ff0ff'):
    foot = T.pr(x, T.floor, z)
    s = (1.78 if key != 'child' else 1.15) * T.sc(z)
    if key == 'guard':
        s *= 1.03
    if key == 'woman':
        s *= 0.95
    wy = T.pr(x, T.yw, z)[1]
    fog = 1 - math.exp(-(z - T.camz) / 16.0)
    shades = [(lin((foot[0] - s * 0.45, 0), (foot[0] + s * 0.25, 0), [(RED, 0.55 * I), (RED, 0.0)]), 1.0),
              (lin((0, foot[1] - s), (0, foot[1]), [('#000000', 0.15), ('#000000', 0.55)]), 1.0)]
    lit(c, lambda pf: draw_front(c, key, foot[0], foot[1], s, pose, back, pf, hold),
        rim=(rimc, 3, -2, 0.55), shades=shades, dark=clamp(0.18 + fog * 0.75 + extra_dark),
        water=(wy, '#0a3440', 0.86) if (wet and T.level > 0.03) else None)
    if wet and T.level > 0.03:
        c.drawOval(oval(foot[0], wy + 2, s * 0.13, s * 0.018 + 2), P('#d8f6ff', 0.5 * (1 - fog), w=2.5, blur=1))
    return foot, s, wy


def kid_overhead(t, kick=1.0):
    def hold(c, hands, hc, pf):
        (x0, y0), (x1, y1) = hands
        cs = abs(x1 - x0) * 3.0
        mx, my = (x0 + x1) / 2, min(y0, y1)
        draw_front(c, 'child', mx, my + cs * 0.46, cs,
                   dict(liftL=0.4 + 0.4 * math.sin(t * 9) * kick, liftR=0.4 - 0.4 * math.sin(t * 9) * kick, armL=0.9 + 0.3 * math.sin(t * 6), elL=0.6,
                        armR=0.9 + 0.3 * math.cos(t * 6), elR=0.6, fear=1, mouth=0.7), back=True, pf=pf)
    return hold


HERO_UP = dict(armL=2.75, elL=-0.15, armR=2.75, elR=-0.15)


def red_I(t):
    return 0.35 + 0.65 * max(0.0, math.sin(t * 2 * PI * 0.9)) ** 2


# ======================================================================= SHOTS
def s_open_close(c, t, T):
    """0.0-4.2 extreme close-up: neck-deep water, child held overhead."""
    I = red_I(T)
    sx, sy, sr = shake(T, 7, 1)
    rise = -40 * t / 4.2
    cam(c, sx, sy + 6 * math.sin(T * 2.2), 1.0 + 0.012 * t, sr)
    Tn = Tun(camz=0, camy=-0.05, level=1.4, vp=(540, 940), F=640, zend=None)

    def bg():
        lamps = draw_tunnel(c, Tn, T)
        draw_water_plane(c, Tn, T, lamps, flow=1.5)
    blurred(c, 14, bg)
    # arms rising from the water to the child
    sleeve = LOOKS['hero']['top']
    for i in (-1, 1):
        sh = (540 + i * 400, 1250)
        el = (540 + i * 470 + 10 * math.sin(T * 3 + i), 620 + 8 * math.sin(T * 4))
        hd = (540 + i * 215, 70 + 6 * math.sin(T * 5 + i))
        c.drawLine(*sh, *el, P(sleeve, w=190))
        c.drawLine(*el, *hd, P(sleeve, w=150))
        c.drawLine(el[0] - i * 40, el[1] + 40, hd[0] - i * 30, hd[1] + 60, P('#ff5040', 0.25 * I, w=30, blur=16, blend=ADD))
    # child dangling above
    kk = math.sin(T * 8)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(300, -260, 780, 150), 60, 60), P(LOOKS['child']['top']))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(300, -260, 780, 150), 60, 60), P(shader=lin((300, 0), (780, 0), [(RED, 0.4 * I), ('#000000', 0.4)]), blend=ATOP))
    for j, ph in ((-1, kk), (1, -kk)):
        k0 = (540 + j * 85, 120)
        k1 = (540 + j * 110 + 50 * ph, 290 + 20 * ph)
        k2 = (540 + j * 100 + 90 * ph, 420 - 30 * ph)
        c.drawLine(*k0, *k1, P(LOOKS['child']['pants'], w=95))
        c.drawLine(*k1, *k2, P(LOOKS['child']['pants'], w=80))
        c.drawOval(oval(k2[0] + 20, k2[1] + 30, 70, 42), P('#dcdcdc'))
        c.drawOval(oval(k2[0] + 20, k2[1] + 52, 72, 16), P('#9a9a9a'))
    for i in (-1, 1):
        hand(c, 540 + i * 215, 90, -90 + i * 10, 95, curl=0.8, skin=LOOKS['hero']['skin'])
    # face
    c.saveLayer()
    ex = dict(fear=0.95, open=1.05, mouth=0.35 + 0.3 * abs(math.sin(T * 6.5)), blink=blink(t, 2.4, 1.1), wet=1,
              lookx=0.8 * ramp(t, 3.0, 3.3) - 0.3 * (1 - ramp(t, 0.6, 1.0)), looky=-0.7 * (ramp(t, 0.5, 0.8) - ramp(t, 1.6, 1.9)),
              tilt=2 * math.sin(T * 1.7), turn=0.12 * ramp(t, 3.0, 3.4))
    portrait(c, 'hero', 540, 760, 560, ex, t=T)
    c.drawPaint(P(shader=lin((0, 0), (W, 0), [(RED, 0.55 * I), (RED, 0.1 * I), ('#000000', 0.0)]), blend=ATOP))
    c.drawPaint(P(shader=lin((W, 0), (W * 0.55, 0), [(CYAN, 0.3), (CYAN, 0.0)]), blend=ATOP))
    c.drawPaint(P(shader=lin((0, 300), (0, 1300), [('#000000', 0.1), ('#000000', 0.55)]), blend=ATOP))
    c.restore()
    yw = 1080 + rise
    draw_water_side(c, yw, T, 0, amp=2.6, flow=1.6, red=1, alpha=0.9)
    for k in range(4):
        splash(c, 150 + k * 260, surf_y(150 + k * 260, yw, T, 0, 2.6), T, k=1.3, seed=k * 20, w_=120)
    return dict(grain=6, ca=1)


def tunnel_burst(c, t, T, t_burst, z_hero, show_guard=False, speed=5.6):
    """Door at the end of the tunnel bulges, tears off, flood rushes toward the camera."""
    I = red_I(T)
    tb = t - t_burst
    amp = 4 + (28 * math.exp(-max(tb, 0) * 2.5) if tb > 0 else 0) + (10 * ramp(tb, 0.8, 2.0) if tb > 0 else 0)
    sx, sy, sr = shake(T, amp, 2)
    cam(c, sx, sy, 1.0 + 0.04 * clamp(t / 3), sr)
    Tn = Tun(camz=0, camy=-0.05, level=1.4, vp=(540, 860), F=820, zend=9.0)
    lamps = draw_tunnel(c, Tn, T)
    bul = sm(ramp(tb, -1.0, 0.0))
    gone = 1 if tb >= 0 else 0
    draw_end_door(c, Tn, T, bulge=bul, wheel=-20 * bul + 6 * math.sin(T * 30) * bul, jets=bul * 1.2 if tb < 0 else 0, gone=gone)
    draw_water_plane(c, Tn, T, lamps, flow=1.6 + 2 * ramp(tb, 0, 1))
    if show_guard and tb < 0.25:
        char_t(c, Tn, 'guard', 0.15, 8.0 - 0.4 * ramp(tb, -0.8, 0), dict(armL=0.6, elL=1.2, armR=0.6, elR=1.2, fsL=0.6, fsR=0.6,
                                                                      sway=0.05 * math.sin(T * 7)), T, I=I)
    if tb >= 0:
        zw = 9.0 - tb * speed
        hgt = 0.6 + 1.6 * eout(ramp(tb, 0, 0.7))
        if zw > z_hero:
            draw_wave_p(c, Tn, zw, hgt, T, seed=1)
            door_flying(c, Tn, T, eout(ramp(tb, 0, 0.9)))
        sparks(c, *Tn.pr(-1.9, -1.25, 6.4), tb, n=60, seed=3, spd=700, size=1.3)
    # hero with child overhead (back view)
    hit = clamp((9.0 - (tb * speed if tb > 0 else 0) - z_hero) <= 0)
    ph = dict(HERO_UP)
    ph['sway'] = 0.04 * math.sin(T * 2.5) - 0.25 * ramp(tb, (9 - z_hero) / speed, (9 - z_hero) / speed + 0.4)
    char_t(c, Tn, 'hero', -0.25, z_hero, ph, T, back=True, hold=kid_overhead(T), I=I)
    if tb >= 0:
        zw = 9.0 - tb * speed
        if zw <= z_hero:
            draw_wave_p(c, Tn, max(zw, 0.6), 2.2, T, seed=2)
            c.drawPaint(P('#d9f4f7', clamp((z_hero - zw) / 1.2) * 0.9))
    o = dict(grain=6)
    if tb >= 0:
        o['flash'] = 0.35 * math.exp(-tb * 6)
        o['ca'] = 4 * math.exp(-tb * 3)
        o['mb'] = 0.35
    return o


def s_open_door(c, t, T):
    return tunnel_burst(c, t, T, 1.15, 2.3)


def s_open_hit(c, t, T):
    """7.3-10.0 side view: wave knocks him off his feet, then underwater."""
    I = red_I(T)
    if t < 0.95:
        k = ramp(t, 0.35, 0.8)
        sx, sy, sr = shake(T, 6 + 26 * k, 4)
        cam(c, sx, sy, 1.12, sr)
        draw_side_tunnel(c, 0, T, red=1)
        yw = 860
        draw_water_side(c, yw, T, 0, amp=1.6, flow=2, layer='back')
        pose = dict(shF=PI - 0.25, elF=0.15, shB=PI - 0.4, elB=0.2, lean=-0.1 - 0.9 * k, rot=-70 * ein(k), head=-0.2, hipF=0.3 * k, hipB=-0.2,
                    mouth=0.8, fear=1)
        x = 560 + 260 * ein(k)
        y = 1480 + 300 * ein(k)

        def carry(cc, hand_, hc, pf):
            draw_side(cc, 'child', hand_[0] - 20, hand_[1] + 330, 380, 1, dict(hipF=0.6 + 0.4 * math.sin(T * 9), kneeF=1.2, hipB=0.2, kneeB=1.4,
                                                                             shF=2.4, elF=0.3, shB=2.0, elB=0.3, mouth=0.9, fear=1), pf=pf)
        lit(c, lambda pf: draw_side(c, 'hero', x, y, 900, -1, pose, pf, carry=carry), rim=('#ffb0a0', -3, 0, 0.6),
            shades=[(lin((0, 0), (W, 0), [(RED, 0.5 * I), (RED, 0)]), 1)], dark=0.3, water=(yw, '#0a3440', 0.85))
        draw_water_side(c, yw, T, 0, amp=1.6, flow=2, alpha=0.85)
        xf = -250 + t * 1100
        draw_wave_side(c, xf, yw, 520 + 600 * k, T, seed=3)
        if t > 0.6:
            c.drawPaint(P('#cfeff5', ramp(t, 0.6, 0.95) * 0.95))
        return dict(grain=6, mb=0.4, ca=3 * k)
    tt = t - 0.95
    draw_underwater(c, T, dark=clamp(tt / 1.7) * 0.75, red=0.6)
    bubbles(c, T, 120, seed=7, origin=(560, 1000, 380), born=7.3 + 0.95, spd=420, size=26, a=0.9)
    bubbles(c, T, 40, seed=3, spd=200, size=10, a=0.4)
    c.save()
    c.translate(560, 1050)
    c.rotate(-50 + 35 * tt)
    lit(c, lambda pf: draw_side(c, 'hero', 0, 300, 700, -1, dict(shF=2.0 + 0.6 * math.sin(T * 3), elF=0.4, shB=1.2, elB=0.6, hipF=0.6, kneeF=0.9, hipB=-0.4, kneeB=0.8, mouth=0.3), pf),
        dark=0.55 + 0.3 * clamp(tt / 1.7), shades=[(lin((0, -400), (0, 400), [(CYAN, 0.3), (CYAN, 0)]), 1)])
    c.restore()
    c.save()
    c.translate(340 - 60 * tt, 620 - 40 * tt)
    c.rotate(30 - 25 * tt)
    lit(c, lambda pf: draw_side(c, 'child', 0, 200, 380, 1, dict(shF=2.6, elF=0.3, shB=2.2, hipF=0.8, kneeF=1.0, mouth=0.4), pf), dark=0.6 + 0.3 * clamp(tt / 1.7))
    c.restore()
    bubbles(c, T, 30, seed=9, origin=(560, 900, 200), born=7.3 + 1.1, spd=380, size=18, a=0.8)
    c.drawPaint(P('#000000', clamp(tt / 1.75) * 0.55))
    return dict(grain=6, uw=1.0, black=0.0 if tt < 1.2 else ramp(tt, 1.2, 1.75) * 0.7)


def s_dark(c, t, T):
    c.drawPaint(P('#010406'))
    bubbles(c, T, 18, seed=21, spd=120, size=10, a=0.25 * (1 - ramp(t, 0.6, 1.3)), x0=300, x1=800, y0=600, y1=1500)
    c.drawCircle(540, 900, 500, P(shader=rad((540, 900), 500, [('#0b2a36', 0.5 * (1 - ramp(t, 0, 1.3))), ('#0b2a36', 0)])))
    return dict(grain=5, uw=0.6)


def s_title(c, t, T):
    c.drawPaint(P('#000000'))
    a = sm(ramp(t, 0.05, 0.35)) * (1 - sm(ramp(t, 1.7, 1.95)))
    fl = 1.0 if (t > 0.42 or int(t * 30) % 3) else 0.3
    g = 6 if t < 0.4 else 1.5
    text_c(c, '10 МИНУТ НАЗАД', 540 - g, 775, 82, '#ff2a1f', 0.5 * a * fl, tf=FONT_BL, spacing=6)
    text_c(c, '10 МИНУТ НАЗАД', 540 + g, 775, 82, '#2ad6ff', 0.5 * a * fl, tf=FONT_BL, spacing=6)
    text_c(c, '10 МИНУТ НАЗАД', 540, 775, 82, '#ffffff', a * fl, tf=FONT_BL, spacing=6)
    c.drawLine(380, 810, 700, 810, P('#ff2a1f', 0.8 * a, w=4))
    return dict(grain=7)


def s_mall(c, t, T):
    camx = 60 + 200 * sm(t / 2.45)
    sx, sy, _ = shake(T, 2, 5, 0.3)
    cam(c, sx, sy, 1.0)
    ex = draw_mall(c, camx, T)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(ex - 170, 800, ex + 170, 1460))
    lit(c, lambda pf: draw_front(c, 'guard', ex + 70, 1450, 640, dict(breath=math.sin(T * 2), blink=blink(T, 3.3), turn=-0.35, lookx=-0.6), pf=pf),
        shades=[(lin((0, 800), (0, 1460), [('#fff1d6', 0.15), ('#000000', 0.25)]), 1)])
    c.restore()

    def walker(xw, s_, sd, dirn, col):
        ph = (xw / (s_ * 0.6)) * PI
        blurred(c, 6, lambda: draw_side(c, 'father', xw - camx * 0.85, 1440, s_, dirn, walk(ph), PF(col, 0.85)))
    walker(900 - 250 * t, 560, 1, -1, '#0c141f')
    walker(-100 + 220 * t, 520, 2, 1, '#101a28')
    xw = 260 + 1020 * sm(clamp(t / 2.45) * 0.9 + 0.05)
    ph = (xw / (720 * 0.55)) * PI
    pose = walk(ph)
    pose.update(head=0.04, open=1.0)
    lit(c, lambda pf: draw_side(c, 'hero', xw - camx, 1470, 760, 1, pose, pf), rim=('#cfefff', -3, -2, 0.6),
        shades=[(lin((0, 700), (0, 1470), [('#d6efff', 0.12), ('#000000', 0.35)]), 1)], dark=0.05)
    c.drawOval(oval(xw - camx, 1475, 120, 14), P('#000000', 0.45, blur=10))
    return dict(grain=4)


ELEV_POS = dict(guard=(290, 1570, 860), woman=(560, 1575, 800), father=(770, 1700, 960), child=(620, 1720, 560), hero=(1000, 1890, 1120))


def elevator_people(c, t, T, shake_k=0.0, light=1.0, red=0.0, lookup=0.0, panic=0.0, hero_grab=0.0, child_cling=0.0, group_fear=0.0):
    sw = lambda s_: 0.07 * shake_k * nz(T * 7, s_)
    redsh = [(lin((540, 300), (540, 1900), [(RED, 0.5 * red), (RED, 0.15 * red)]), 1)] if red else []
    dk = clamp(0.15 + 0.6 * (1 - light))
    common = lambda seed: dict(breath=math.sin(T * 2.1 + seed), blink=blink(T, 2.7 + seed * 0.3, seed), fear=group_fear, sway=sw(seed))
    gx, gy, gs = ELEV_POS['guard']
    pg = common(1)
    pg.update(turn=0.35 * (1 - lookup), lookx=0.6 * (1 - lookup) - 0.0, looky=-0.9 * lookup, tilt=-0.15 * lookup,
              armL=0.12 + 0.5 * panic, elL=0.3 * panic, armR=0.12 + 0.5 * panic, elR=0.2, mouth=0.3 * panic)
    lit(c, lambda pf: draw_front(c, 'guard', gx, gy, gs, pg, pf=pf), shades=redsh, dark=dk, rim=('#dff6ff', 2, -2, 0.35 * light))
    wx, wy, ws = ELEV_POS['woman']
    pw = common(2)
    phone = 1 - max(lookup, panic)
    pw.update(looky=0.7 * phone - 0.9 * lookup, lookx=0.1, tilt=-0.08 * phone, armR=0.25 + 0.15 * phone, elR=1.9 * phone + 0.9 * panic,
              armL=0.2 + 0.6 * panic, elL=1.2 * panic, mouth=0.45 * panic)

    def phone_hold(cc, hands, hc, pf):
        if phone > 0.3 and not pf.sil:
            hx_, hy_ = hands[1]
            cc.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(hx_ - 22, hy_ - 40, hx_ + 22, hy_ + 30), 6, 6), P('#111418'))
            cc.drawRect(skia.Rect.MakeLTRB(hx_ - 18, hy_ - 35, hx_ + 18, hy_ + 24), P('#bfe7ff', 0.9 * light))
            cc.drawCircle(hx_, hy_ - 120, 160, P('#9fd8ff', 0.15 * light, blur=50, blend=ADD))
    lit(c, lambda pf: draw_front(c, 'woman', wx, wy, ws, pw, pf=pf, hold=phone_hold), shades=redsh, dark=dk, rim=('#dff6ff', 2, -2, 0.35 * light))
    fx, fy, fs = ELEV_POS['father']
    cx_, cy_, cs = ELEV_POS['child']
    cx_ = cx_ + 60 * child_cling
    pc = common(4)
    pc.update(looky=-0.9 * max(lookup, 1 - child_cling) * 0.6, lookx=0.5 * (1 - child_cling), armR=0.35 + 1.0 * child_cling, elR=0.4 + 1.0 * child_cling,
              armL=0.25 + 0.6 * child_cling, elL=0.6 * child_cling + 0.5 * math.sin(T * 1.3) * (1 - child_cling), mouth=0.6 * panic, fear=group_fear,
              tilt=0.15 * child_cling)
    pf_ = common(3)
    pf_.update(lookx=-0.6 * (1 - lookup), looky=0.6 * (1 - lookup) - 0.9 * lookup, tilt=0.1 * (1 - lookup) - 0.1 * lookup, turn=-0.2,
               armL=0.28 + 0.5 * panic, elL=0.2, armR=0.12 + 0.3 * panic, mouth=0.35 * panic)
    lit(c, lambda pf: draw_front(c, 'child', cx_, cy_, cs, pc, pf=pf), shades=redsh, dark=dk, rim=('#dff6ff', 2, -2, 0.35 * light))
    lit(c, lambda pf: draw_front(c, 'father', fx, fy, fs, pf_, pf=pf), shades=redsh, dark=dk + 0.03, rim=('#dff6ff', 2, -2, 0.35 * light))
    if child_cling > 0.5:
        lit(c, lambda pf: draw_front(c, 'child', cx_, cy_, cs, pc, pf=pf), shades=redsh, dark=dk, rim=('#dff6ff', 2, -2, 0.3))
    hx, hy, hs = ELEV_POS['hero']
    ph = common(5)
    ph.update(turn=-0.45 * (1 - lookup), lookx=-0.7 * (1 - lookup), looky=-0.9 * lookup, tilt=-0.1 * lookup,
              armR=0.12 + 1.25 * hero_grab, elR=-0.1 * hero_grab, armL=0.12 + 0.35 * panic, elL=0.4 * panic, mouth=0.4 * panic)
    lit(c, lambda pf: draw_front(c, 'hero', hx, hy, hs, ph, pf=pf), shades=redsh, dark=dk, rim=('#dff6ff', 2, -2, 0.4 * light))


def s_elev_intro(c, t, T):
    sx, sy, sr = shake(T, 3, 6, 0.4)
    cam(c, sx + 50 - 70 * sm(t / 3.3), sy, 1.1 - 0.03 * t / 3.3, sr)
    draw_elevator(c, T, light=1.0)
    elevator_people(c, t, T)
    return dict(grain=4)


def s_elev_shake(c, t, T):
    tq = T - 21.1
    k = math.exp(-max(tq, 0) * 1.6) if tq > 0 else 0
    tremble = 0.0 if tq < 0 else 1.0
    amp = 2.5 + 38 * k + 7 * tremble
    sx, sy, sr = shake(T, amp, 7, 1.4)
    desc = 6 * math.sin(T * 1.3) if tq < 0 else 0
    cam(c, sx, sy + desc, 1.04, sr * (1 + 3 * k))
    flick = 1.0
    if tq > 0:
        flick = 0.0 if (math.sin(T * 41) > 0.3 and tq < 1.4) or (1.4 < tq < 1.55) else 1.0
        flick *= 1 - 0.6 * ramp(tq, 1.5, 1.7)
    red = ramp(tq, 0.4, 0.8)
    draw_elevator(c, T, light=flick, red=red)
    elevator_people(c, t, T, shake_k=k * 1.5 + 0.2 * tremble, light=max(flick, 0.25), red=red, panic=ramp(tq, 0.0, 0.25),
                    hero_grab=sm(ramp(tq, 0.1, 0.45)), child_cling=sm(ramp(tq, 0.2, 0.7)), group_fear=ramp(tq, 0, 0.3), lookup=ramp(tq, 1.6, 2.0))
    sparks(c, 760, 330, tq, n=50, seed=8, spd=600, size=1.2)
    sparks(c, 330, 340, tq - 0.55, n=30, seed=9, spd=500)
    return dict(grain=5, ca=3 * k, mb=0.25 * k)


def s_indicator(vals):
    def f(c, t, T):
        v = vals[0][1]
        for tt, vv in vals:
            if T >= tt:
                v = vv
        sx, sy, sr = shake(T, 6, 10, 1.5)
        cam(c, sx, sy, 1.0 + 0.05 * t, sr)
        fl = 0.25 if (math.sin(T * 53) > 0.85) else 1.0
        draw_indicator(c, T, v, flick=fl, shake_=(3 * nz(T * 20), 0), red=1)
        sparks(c, 980, 300, T - vals[-1][0] - 0.2, n=30, seed=12, spd=500)
        return dict(grain=6, ca=1.5)
    return f


def s_elev_lookup(c, t, T):
    sx, sy, sr = shake(T, 9, 11, 1.2)
    cam(c, sx, sy, 1.06 + 0.03 * t, sr)
    flick = 0.25 + 0.25 * (math.sin(T * 30) > 0.6)
    draw_elevator(c, T, light=flick, red=1.0)
    elevator_people(c, t, T, shake_k=0.25, light=0.3, red=1.0, lookup=1.0, panic=0.4, hero_grab=1.0, child_cling=1.0, group_fear=1.0)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(970, 790, 1040, 830), 4, 4), P('#050505'))
    text_c(c, '-5', 1005, 822, 34, RED, 1, tf=FONT_BL)
    return dict(grain=6)


def s_guard(c, t, T):
    sx, sy, sr = shake(T, 4, 12, 0.8)
    cam(c, sx, sy, 1.0 + 0.025 * t, sr)

    def bg():
        draw_elevator(c, T, light=0.2, red=1.0)
    blurred(c, 16, bg)
    pale = sm(ramp(T, 28.2, 29.3))
    speak = 29.36 <= T <= 31.7
    m = clamp(env(T) * 0.9) if speak else 0.0
    ex = dict(fear=0.6 + 0.4 * pale, open=1.0 + 0.1 * pale, mouth=m, blink=blink(t, 2.2, 0.5) if not speak else 0, wet=0.6 * pale,
              lookx=0.3 * math.sin(T * 0.9) - 0.2, looky=-0.5 + 0.4 * ramp(T, 29.2, 29.5), pale=pale, tilt=1.5 * math.sin(T * 1.1), turn=-0.1)
    c.saveLayer()
    portrait(c, 'guard', 540, 760, 600, ex, t=T)
    c.drawPaint(P(shader=lin((0, 0), (0, 1500), [(RED, 0.45), (RED, 0.12)]), blend=ATOP))
    c.drawPaint(P(shader=lin((W, 0), (W * 0.5, 0), [(CYAN, 0.25), (CYAN, 0)]), blend=ATOP))
    c.drawPaint(P(shader=lin((0, 0), (W, 0), [('#000000', 0.45), ('#000000', 0.0)]), blend=ATOP))
    c.restore()
    return dict(grain=6)


def s_doors(c, t, T):
    I = red_I(T)
    dolly = sm(ramp(t, 1.4, 3.3))
    Tn = Tun(camz=-3.0 + 1.8 * dolly, camy=-0.05, level=0.05, vp=(540, 900), F=900)
    sx, sy, sr = shake(T, 3, 13, 0.5)
    cam(c, sx, sy, 1.0 + 0.18 * dolly, sr)
    lamps = draw_tunnel(c, Tn, T)
    draw_water_plane(c, Tn, T, lamps, flow=1.0, chop=0.6)
    dust(c, T, 50, seed=2, col='#ffb7aa', a=0.3, spd=6)
    gap = 380 * sm(ramp(t, 0.05, 1.3)) * (1 - dolly)
    if gap < 379:
        for i in (-1, 1):
            x0 = 540 + i * gap
            x1 = 540 + i * (gap + 400)
            rr = skia.Rect.MakeLTRB(min(x0, x1), 280, max(x0, x1), 1700)
            c.drawRect(rr, P('#5f6873'))
            c.save()
            c.clipRect(rr)
            c.drawPaint(tex_paint(STEEL, 0.6, OVER, 1.6))
            c.drawPaint(P(shader=lin((0, 280), (0, 1700), [('#000000', 0.1), ('#000000', 0.6)]), blend=ATOP))
            c.restore()
            c.drawLine(x0, 280, x0, 1700, P('#0b0d10', w=6))
    fr = skia.Path()
    fr.addRect(skia.Rect.MakeLTRB(-400, -400, W + 400, H + 400))
    fr.addRect(skia.Rect.MakeLTRB(140 - 200 * dolly, 280 - 200 * dolly, 940 + 200 * dolly, 1700 + 300 * dolly))
    fr.setFillType(skia.PathFillType.kEvenOdd)
    c.drawPath(fr, P('#0d1014'))
    c.drawPath(fr, P(shader=lin((0, 0), (W, 0), [(RED, 0.2 * I), ('#000000', 0)]), blend=ADD))
    # foreground silhouettes (over-the-shoulder)
    for (key, x, s_) in (('guard', 170 - 120 * dolly, 2300), ('hero', 930 + 150 * dolly, 2400)):
        lit(c, lambda pf, key=key, x=x, s_=s_: draw_front(c, key, x, 1920 + s_ * 0.62, s_, dict(breath=math.sin(T * 2), tilt=0.05), back=True, pf=pf),
            dark=0.65, rim=('#ff6a50', -4 if key == 'hero' else 4, 0, 0.5 * I))
    return dict(grain=5)


def s_floor(c, t, T):
    Tn = Tun(camz=0, camy=1.42, level=0.06, vp=(540, 700), F=760)
    sx, sy, sr = shake(T, 4, 14, 0.6)
    cam(c, sx, sy, 1.0, sr)
    lamps = draw_tunnel(c, Tn, T)
    draw_water_plane(c, Tn, T, lamps, flow=1.4, chop=1.3)
    xw = -200 + 560 * t
    ph = xw / 430 * PI
    pose = walk(ph, 1.0)
    lit(c, lambda pf: draw_side(c, 'hero', xw, 1560, 2300, 1, pose, pf), rim=('#ff6a50', -4, 0, 0.5),
        shades=[(lin((0, 0), (W, 0), [(RED, 0.4), (RED, 0)]), 1)], dark=0.35, water=(1535, '#0a3440', 0.6))
    for k in range(3):
        st = (ph / PI + k) % 2
        x = xw + (k - 1) * 280
        splash(c, xw + 120 * math.sin(ph), 1545, T, k=1.0, seed=k * 30, w_=160)
    return dict(grain=5)


def s_speaker(c, t, T):
    sx, sy, sr = shake(T, 3, 15, 0.5)
    cam(c, sx - 30 * t, sy, 1.04 + 0.03 * t, sr)
    draw_speaker(c, T, 1.0)
    return dict(grain=6)


def group_tunnel_listen(c, t, T):
    I = red_I(T)
    Tn = Tun(camz=0.2 * t, camy=-0.05, level=0.12, vp=(540, 860), F=860)
    sx, sy, sr = shake(T, 3, 16, 0.5)
    cam(c, sx, sy, 1.0, sr)
    lamps = draw_tunnel(c, Tn, T)
    draw_water_plane(c, Tn, T, lamps, flow=1.0)
    beam = 0.5 + 0.5 * math.sin(T * 5)
    c.drawPaint(P(shader=lin((0, 0), (W, 0), [(RED, 0.18 * beam), (RED, 0)]), blend=ADD))
    up = sm(ramp(t, 0.1, 0.6))
    go = sm(ramp(t, 1.8, 2.5))
    people = [('woman', 0.55, 5.4), ('guard', -0.85, 4.8), ('father', 1.05, 4.3), ('child', 0.6, 4.1), ('hero', -0.05, 3.3)]
    for key, x, z in people:
        pose = dict(tilt=-0.1 * up + 0.25 * go * (1 if x > 0 else -1), breath=math.sin(T * 2 + x), sway=0.02 * math.sin(T * 1.5 + x),
                    armL=0.15, armR=0.15 + (0.6 if key == 'father' else 0))
        if key == 'child':
            pose.update(armL=0.5, elL=0.2)
        char_t(c, Tn, key, x, z, pose, T, back=True, I=I)
    return dict(grain=5)


def front_run(ph, amp=1.0):
    s, co = math.sin(ph), math.cos(ph)
    return dict(liftL=max(0, s) * 0.9 * amp, liftR=max(0, -s) * 0.9 * amp, armL=0.3 + 0.15 * s, elL=1.4 + 0.5 * s, fsL=0.5 + 0.5 * s,
                armR=0.3 - 0.15 * s, elR=1.4 - 0.5 * s, fsR=0.5 - 0.5 * s, bob=-0.03 * abs(co) * amp, sway=0.05 * s * amp)


def s_run_toward(c, t, T):
    I = red_I(T)
    v = 3.2
    camz = 20 - v * t
    Tn = Tun(camz=camz, camy=-0.1, level=0.15, vp=(540, 840), F=820)
    tg = T - 43.0
    k = math.exp(-max(tg, 0) * 2.0) if tg > 0 else 0
    sx, sy, sr = shake(T, 5 + 30 * k, 17, 1.0)
    cam(c, sx, sy + 8 * math.sin(T * 9), 1.0, sr)
    lamps = draw_tunnel(c, Tn, T)
    if tg > 0:
        fp = Tn.pr(0, 0, camz + 46)
        c.drawCircle(fp[0], fp[1], 260, P(shader=rad(fp, 260, [('#ffd9b0', 0.8 * k), ('#ff7a2a', 0.3 * k), ('#ff7a2a', 0)]), blend=ADD))
    draw_water_plane(c, Tn, T, lamps, flow=1.6, chop=1.2)
    if T > 43.9:
        zw = camz + 40 - (T - 43.9) * 9.0
        draw_wave_p(c, Tn, zw, 1.6, T, seed=4, foam=0.9)
    look = sm(ramp(T, 43.35, 43.7)) * (1 - sm(ramp(T, 44.3, 44.7)))
    people = [('father', 0.95, 6.0, 0.3), ('child', 0.45, 5.9, 1.4), ('woman', -0.75, 5.0, 2.1), ('hero', 0.15, 3.9, 0.9), ('guard', -0.6, 3.1, 1.7)]
    for key, x, d, off in sorted(people, key=lambda p: -p[2]):
        ph = T * (11.5 if key != 'child' else 15) + off
        pose = front_run(ph, 1.0)
        pose.update(fear=0.6 + 0.4 * ramp(T, 43, 43.5), mouth=0.3 + 0.3 * abs(math.sin(ph)), turn=(0.9 if x > 0 else -0.9) * look, tilt=(0.2 if x > 0 else -0.2) * look,
                    blink=blink(T, 2.5, off))
        if key == 'father':
            pose.update(armL=0.5, elL=0.2, fsL=0)
        if key == 'child':
            pose.update(armR=0.6, elR=0.1, fsR=0)
        foot, s_, wy = char_t(c, Tn, key, x, camz + d, pose, T, back=False, I=I)
        splash(c, foot[0], wy, T, k=0.6, seed=int(off * 10), w_=s_ * 0.12)
    if tg > 0:
        dust(c, T, 60, seed=31, col='#b8a890', a=0.5 * k, spd=60, size=3)
    return dict(grain=6, ca=2 * k, mb=0.2)


def s_flood_side(c, t, T):
    I = red_I(T)
    hit = 46.9
    th = hit - 44.95
    camx = 600 * min(t, th) + 150 * max(0.0, t - th)
    sx, sy, sr = shake(T, 7, 18, 1.0)
    cam(c, sx, sy, 1.0, sr)
    draw_side_tunnel(c, camx, T, red=1)
    base = 1430
    xf = -300 + t * 330
    draw_water_side(c, base - 6, T, camx, amp=0.5, flow=1.5, layer='back')
    fall = ramp(T, hit, hit + 0.45)
    carried = ramp(T, hit + 0.3, 48.6)
    hero_turn = ramp(T, 48.05, 48.3)
    t1, t2 = th + 0.2, 3.1
    d = clamp(t - t1, 0, t2 - t1)
    hero_pos = 600 * min(t, t1) + (600 * d - 300 * d * d / (t2 - t1) if t > t1 else 0) - 100 * max(0.0, t - t2)
    people = [('guard', 840, 0.0), ('woman', 520, 2.3), ('father', 300, 3.1), ('child', 420, 0.7), ('hero', 660, 1.2)]
    for key, x, off in people:
        ph = (T * 11 + off)
        s_ = {'child': 470, 'guard': 790}.get(key, 760)
        pose = run(ph, 1.0 if key != 'child' else 1.1)
        pose.update(fear=1, mouth=0.4)
        fac = 1
        y = 1480
        xw = x + 600 * t
        if key == 'father':
            if T > hit:
                pose = dict(lean=0.2 + 1.2 * fall, rot=110 * ein(fall), shF=2.6, elF=0.3, shB=2.0, elB=0.5, hipF=0.8, kneeF=0.4, hipB=-0.6, kneeB=0.9, mouth=0.9, fear=1)
                xw = x + 600 * th + 300 * fall + 1300 * ein(carried)
                y = 1480 + 120 * fall + 200 * carried
            else:
                pose.update(shB=-0.3, elB=0.3)
        if key == 'child':
            if T > hit:
                st = ramp(T, hit, hit + 0.4)
                pose = dict(shF=1.6 * st + 0.4, elF=0.3, shB=1.0, lean=-0.1, hipF=0.1, kneeF=0.2, hipB=-0.1, kneeB=0.3, mouth=1.0, fear=1, head=-0.15)
                xw = x + 600 * th + 70 * st
            else:
                pose.update(shF=1.5, elF=0.2)
        if key == 'hero':
            xw = x + hero_pos
            if t > t1:
                pose = run(ph, clamp(1 - 0.7 * d / (t2 - t1)))
                pose.update(fear=1, mouth=0.6)
            if hero_turn > 0.5:
                fac = -1
                pose.update(head=-0.1)
        xx = xw - camx
        submerged = xx < xf + 120
        wy = base - (230 * ramp(xf + 120 - xx, 0, 300) if submerged else 0)
        lit(c, lambda pf, key=key, xx=xx, y=y, s_=s_, fac=fac, pose=pose: draw_side(c, key, xx, y, s_, fac, pose, pf),
            rim=('#ff8a70', -3, 0, 0.5), shades=[(lin((0, 300), (0, 1500), [(RED, 0.35 * I), ('#000000', 0.4)]), 1)], dark=0.25, water=(wy, '#0a3440', 0.85))
        splash(c, xx, wy, T, k=0.9 if submerged else 0.5, seed=int(off * 9), w_=90)
    draw_water_side(c, base, T, camx, amp=0.6, flow=1.5, alpha=0.8)
    draw_wave_side(c, xf, base, 250 + 30 * t, T, x0=-200, seed=5)
    return dict(grain=6, mb=0.3)




def s_child_scream(c, t, T):
    sx, sy, sr = shake(T, 9, 19, 1.4)
    cam(c, sx, sy, 1.03, sr)
    Tn = Tun(camz=0, camy=0.6, level=1.0, vp=(540, 860), F=700)

    def bg():
        lamps = draw_tunnel(c, Tn, T)
        draw_water_plane(c, Tn, T, lamps, flow=2)
    blurred(c, 16, bg)
    I = red_I(T)
    c.saveLayer()
    ex = dict(fear=1, open=1.1, mouth=0.75 + 0.25 * clamp(env(T) * 1.2), scream=1, wet=1, lookx=0.6 * math.sin(T * 3), looky=-0.2, tilt=4 * math.sin(T * 7))
    portrait(c, 'child', 540, 800, 540, ex, t=T)
    c.drawPaint(P(shader=lin((0, 0), (W, 0), [(RED, 0.5 * I), (RED, 0.05)]), blend=ATOP))
    c.drawPaint(P(shader=lin((0, 400), (0, 1500), [('#000000', 0.05), ('#000000', 0.5)]), blend=ATOP))
    c.restore()
    for k in range(2):
        x = 420 + k * 240
        c.drawLine(x, 820, x - 6, 960 + 30 * ((T * 3 + k) % 1), P('#cfefff', 0.5, w=7, blur=2))
    yw = 1330
    draw_water_side(c, yw, T, 0, amp=2.2, flow=2, alpha=0.9)
    for k in range(3):
        splash(c, 200 + k * 340, surf_y(200 + k * 340, yw, T, 0, 2.2), T, k=1.3, seed=k * 11, w_=140)
    return dict(grain=6, ca=1.5)


def s_grab_run(c, t, T):
    I = red_I(T)
    run_t = ramp(t, 0.85, 2.34)
    camx = 900 * sm(run_t)
    sx, sy, sr = shake(T, 6, 20, 1.0)
    cam(c, sx, sy, 1.0, sr)
    draw_side_tunnel(c, camx, T, red=1, door_x=1900)
    yw = 1240 - 40 * t
    draw_water_side(c, yw - 4, T, camx, amp=0.8, flow=1.6, layer='back')
    cxw = 470
    if t < 0.45:
        hx = 980 - 380 * (t / 0.45)
        hpose = run(T * 10, 0.7)
        hpose.update(fear=1, mouth=0.6)
        fac = -1
    elif t < 0.85:
        k = (t - 0.45) / 0.4
        hx = 600 - 30 * k
        bend = math.sin(k * PI)
        hpose = dict(lean=0.9 * bend, shF=1.4 + 0.3 * k, elF=0.6, shB=1.2, elB=0.8, hipF=0.5 * bend, kneeF=0.9 * bend, hipB=-0.2, kneeB=0.5 * bend, fear=1, mouth=0.5)
        fac = -1
    else:
        k = run_t
        hx = 570 + 950 * k
        hpose = run(T * 9, 0.75)
        hpose.update(fear=1, mouth=0.6, shF=0.9, elF=1.6, shB=0.7, elB=1.7)
        fac = 1
    carried = t >= 0.7

    def carry(cc, hand_, hc, pf):
        if carried:
            draw_side(cc, 'child', 0.05 * 820, -0.04 * 820 + 0.62 * 470 * 0.98, 470,
                      -1, dict(hipF=1.4, kneeF=1.7, hipB=1.1, kneeB=1.6, shF=2.4, elF=0.8, shB=2.2, elB=0.9, head=0.3, lean=0.1, mouth=0.6, fear=1), pf=pf)
    if not carried:
        lit(c, lambda pf: draw_side(c, 'child', cxw - camx, 1480, 470, 1, dict(shF=1.9, elF=0.3, shB=1.4, hipF=0.1, kneeF=0.2, mouth=1, fear=1, head=-0.1), pf),
            rim=('#ff8a70', -3, 0, 0.5), shades=[(lin((0, 900), (0, 1500), [(RED, 0.35 * I), ('#000000', 0.4)]), 1)], dark=0.2, water=(yw, '#0a3440', 0.85))
    lit(c, lambda pf: draw_side(c, 'hero', hx - camx, 1480, 820, fac, hpose, pf, carry=carry), rim=('#ff8a70', -3 * fac, 0, 0.55),
        shades=[(lin((0, 400), (0, 1500), [(RED, 0.35 * I), ('#000000', 0.4)]), 1)], dark=0.22, water=(yw, '#0a3440', 0.85))
    splash(c, hx - camx, yw, T, k=1.2, seed=3, w_=120)
    # guard and woman ahead, wading
    for key, x0, off in (('guard', 1650, 0.4), ('woman', 1450, 1.6)):
        lit(c, lambda pf, key=key, x0=x0, off=off: draw_side(c, key, x0 + 120 * t - camx, 1480, 780, 1, dict(run(T * 8 + off, 0.6), fear=1), pf),
            rim=('#ff8a70', -3, 0, 0.5), shades=[(lin((0, 400), (0, 1500), [(RED, 0.35 * I), ('#000000', 0.4)]), 1)], dark=0.3, water=(yw, '#0a3440', 0.85))
        splash(c, x0 + 120 * t - camx, yw, T, k=0.8, seed=int(off * 7), w_=90)
    draw_water_side(c, yw, T, camx, amp=0.9, flow=1.8, alpha=0.82)
    return dict(grain=6, mb=0.2)


def s_rising(c, t, T):
    I = red_I(T)
    level = 1.0 + 0.36 * sm(t / 2.7)
    yw_ = 1.6 - level
    bob = 0.035 * math.sin(T * 2.4) + 0.015 * math.sin(T * 5.1)
    Tn = Tun(camz=0, camy=yw_ - 0.002 + bob * 0.0, level=level, vp=(540, 930), F=1250)
    cam(c, 0, 0, 1.0, 1.5 * math.sin(T * 1.7))
    lamps = draw_tunnel(c, Tn, T)
    zH = 3.1 - 0.5 * t / 2.7
    for key, x, z in (('guard', -1.1, 6.5), ('woman', 1.0, 5.8)):
        char_t(c, Tn, key, x, z, dict(armL=0.6, armR=0.6, elL=0.4, elR=0.4, sway=0.04 * math.sin(T * 2 + x), fear=1, mouth=0.4), T, back=True, I=I, wet=False)

    def hold(cc, hands, hc, pf):
        (x0, y0), (x1, y1) = hands
        cs = abs(x1 - x0) * 2.4
        draw_front(cc, 'child', (x0 + x1) / 2, (y0 + y1) / 2 + cs * 0.25, cs,
                   dict(armL=2.2, elL=0.9, armR=2.2, elR=0.9, liftL=0.8, liftR=0.8, tilt=0.1 * math.sin(T * 3)), back=True, pf=pf)
    ph = T * 3.5
    pose = dict(armL=0.75, elL=1.9, armR=0.75, elR=1.9, sway=0.05 * math.sin(ph), fear=1, mouth=0.45 + 0.2 * math.sin(T * 6), blink=blink(T, 2.0),
                looky=-0.2, bob=0.01 * math.sin(ph * 2))
    char_t(c, Tn, 'hero', 0.1, zH, pose, T, back=False, hold=hold, I=I, wet=False)
    y0 = 930 + 22 * math.sin(T * 2.4)
    for k in range(3):
        c.drawLine(-20, y0 - 6 - k * 10, W + 20, y0 - 6 - k * 10 + 8 * math.sin(T * 3 + k), P('#b8f1fb', 0.3 - k * 0.08, w=5 - k, blur=2))
    c.drawRect(skia.Rect.MakeLTRB(-50, y0 - 40, W + 50, y0), P(shader=lin((0, y0 - 40), (0, y0), [('#0f3a46', 0), ('#0f3a46', 0.55)])))
    bubbles(c, T, 40, seed=41, spd=150, size=12, a=0.6, x0=100, x1=980, y0=y0 + 50, y1=H)
    return dict(grain=6, band=(y0, 1.0))


def door_scene(c, t, T, z_off=0.0):
    I = red_I(T)
    tb = T - 56.66
    bul = sm(ramp(T, 56.66, 59.8)) * 0.85 + (0.15 * sm(ramp(T, 59.8, 63.5)))
    creak = sum(math.exp(-max(0, T - tc) * 4) * (T > tc) for tc in (57.2, 58.1, 58.9, 59.5))
    sx, sy, sr = shake(T, 4 + 18 * creak, 22, 1.2)
    cam(c, sx, sy, 1.0 + 0.04 * t, sr)
    level = 1.32 + 0.12 * ramp(T, 54.9, 63.5)
    Tn = Tun(camz=0.25 * t + z_off, camy=-0.15, level=level, vp=(540, 800), F=950, zend=8.5)
    lamps = draw_tunnel(c, Tn, T)
    wheel = 0
    pull = math.sin(T * 5)
    if T < 58.5:
        wheel = 25 * max(0, pull) ** 2 - 8
    draw_end_door(c, Tn, T, bulge=bul, wheel=wheel + 3 * math.sin(T * 40) * bul, jets=clamp(bul * 1.3))
    draw_water_plane(c, Tn, T, lamps, flow=1.4)
    back_step = sm(ramp(T, 58.5, 59.3))
    pg = dict(armL=0.55 - 0.4 * back_step, elL=1.35 - 1.2 * back_step, armR=0.55 - 0.4 * back_step, elR=1.35 - 1.2 * back_step,
              fsL=0.6, fsR=0.6, sway=0.05 * pull * (1 - back_step), tilt=-0.1 * pull * (1 - back_step))
    char_t(c, Tn, 'guard', 0.1, 7.75 - 0.9 * back_step, pg, T, I=I)
    char_t(c, Tn, 'woman', -1.25, 6.2, dict(armL=0.4, armR=0.4, elL=1.2, elR=1.2, fsL=0.5, fsR=0.5, sway=0.03 * math.sin(T * 2), tilt=0.1 * math.sin(T)), T, I=I)

    def hold(cc, hands, hc, pf):
        (x0, y0), (x1, y1) = hands
        cs = abs(x1 - x0) * 2.2
        draw_front(cc, 'child', (x0 + x1) / 2 + cs * 0.02, (y0 + y1) / 2 + cs * 0.2, cs,
                   dict(armL=2.3, elL=1.0, armR=2.3, elR=1.0, liftL=0.8, liftR=0.8, fear=1, mouth=0.5 + 0.3 * math.sin(T * 5), tilt=-0.15,
                        looky=-0.2, blink=blink(T, 2.3)), back=False, pf=pf)
    char_t(c, Tn, 'hero', 0.85, 2.35 + 0.25 * t, dict(armL=0.6, elL=1.6, armR=0.6, elR=1.6, fsL=0.5, fsR=0.5, sway=0.03 * math.sin(T * 1.7)),
           T, back=True, hold=hold, I=I)
    return dict(grain=6, ca=1.5 * creak)


def s_door(c, t, T):
    return door_scene(c, t, T)


def s_woman(c, t, T):
    sx, sy, sr = shake(T, 7, 23, 1.2)
    cam(c, sx, sy, 1.0 + 0.04 * t, sr)
    Tn = Tun(camz=0, camy=-0.1, level=1.4, vp=(640, 820), F=700, zend=8)

    def bg():
        lamps = draw_tunnel(c, Tn, T)
        draw_end_door(c, Tn, T, bulge=1, jets=1)
        draw_water_plane(c, Tn, T, lamps, flow=2)
    blurred(c, 14, bg)
    I = red_I(T)
    shout = 60.86 <= T <= 61.75
    m = clamp(env(T) * 1.15) if shout else (0.3 + 0.1 * math.sin(T * 6))
    c.saveLayer()
    ex = dict(fear=1, open=1.1, mouth=m, scream=1.0 if shout else 0.3, wet=1, lookx=0.7, looky=-0.1, turn=0.25, tilt=-3 + 3 * math.sin(T * 2))
    portrait(c, 'woman', 520, 780, 580, ex, t=T)
    c.drawPaint(P(shader=lin((0, 0), (W, 0), [(RED, 0.5 * I), (RED, 0.1)]), blend=ATOP))
    c.drawPaint(P(shader=lin((W, 0), (W * 0.45, 0), [(CYAN, 0.3), (CYAN, 0)]), blend=ATOP))
    c.drawPaint(P(shader=lin((0, 300), (0, 1500), [('#000000', 0.05), ('#000000', 0.5)]), blend=ATOP))
    c.restore()
    yw = 1420
    draw_water_side(c, yw, T, 0, amp=2.0, flow=2, alpha=0.9)
    splash(c, 300, surf_y(300, yw, T, 0, 2), T, k=1.1, seed=4, w_=140)
    return dict(grain=6, ca=1.0 + (2 if shout else 0))


def s_lock(c, t, T):
    tb = T - 62.62
    k = math.exp(-max(tb, 0) * 3) if tb > 0 else 0
    sx, sy, sr = shake(T, 6 + 34 * k + 8 * (tb < 0), 24, 1.6)
    cam(c, sx, sy, 1.0 + 0.05 * t, sr * 2)
    c.drawPaint(P(shader=lin((0, 0), (W, H), [('#6a7480', 1), ('#2f363f', 1), ('#3f4752', 1)])))
    c.drawPaint(tex_paint(STEEL, 0.6, OVER, 2.5))
    c.drawPaint(P(shader=rad((300, 500), 900, [(RED, 0.35 * red_I(T)), (RED, 0)]), blend=ADD))
    for j in range(5):
        for i in range(4):
            x, y = 140 + i * 270, 200 + j * 380
            c.drawCircle(x, y, 22, P('#2a3038'))
            c.drawCircle(x - 5, y - 5, 10, P('#b8c2cc', 0.7))
    # bracket + latch bar
    vib = 6 * math.sin(T * 70) * (tb < 0)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(330, 760, 760, 1180), 24, 24), P('#252b32'))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(330, 760, 760, 1180), 24, 24), P('#8c96a0', 0.6, w=4))
    ang = 0 if tb < 0 else 75 * eout(ramp(tb, 0, 0.5))
    c.save()
    c.translate(540 + vib, 970)
    c.rotate(ang)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-520, -70, 520, 70), 20, 20), P(shader=lin((0, -70), (0, 70), [('#c9d1d9', 1), ('#5a636d', 1), ('#262b31', 1)])))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-520, -70, 520, 70), 20, 20), P('#111', w=3))
    c.restore()
    # bolts
    for i, (bx, by) in enumerate(((390, 820), (700, 820), (390, 1120), (700, 1120))):
        if tb < 0:
            c.drawCircle(bx + vib * 0.5, by, 30, P('#151a1f'))
            c.drawCircle(bx + vib * 0.5, by, 22, P('#9aa4ae'))
            c.drawLine(bx - 14, by, bx + 14, by, P('#3a3f45', w=6))
        else:
            fly = eout(ramp(tb, 0, 0.6))
            dx, dy = (bx - 545) * 3 * fly, (by - 970) * 3 * fly
            r = 22 * (1 + 4 * fly)
            c.drawCircle(bx + dx, by + dy, r, P('#9aa4ae', 1 - 0.5 * fly))
            c.drawCircle(bx, by, 26, P('#050608'))
    # crack + jets
    if tb > -0.4:
        st = ramp(tb, -0.4, 0.2)
        cp = path([(80, 600), (300, 760), (420, 700), (560, 860), (700, 800), (1000, 1000)], close=False)
        c.drawPath(cp, P('#020304', w=4 + 10 * st))
        for i in range(70):
            u = hsh(i + 70)
            x0 = 80 + u * 920
            y0 = 600 + u * 400 + 60 * math.sin(u * 9)
            ph = (T * (3 + 3 * hsh(i)) + u) % 1
            L = (200 + 600 * hsh(i + 3)) * st * (0.5 + ph)
            ag = math.radians(-120 + 240 * hsh(i + 9))
            c.drawLine(x0, y0, x0 + math.cos(ag) * L, y0 + math.sin(ag) * L + 400 * ph * ph, P('#e3f8ff', 0.6 * st * (1 - ph * 0.6), w=3 + 4 * hsh(i), blur=2))
    sparks(c, 545, 970, tb, n=90, seed=14, spd=1300, g=1500, size=1.8)
    sparks(c, 390, 820, tb - 0.05, n=40, seed=15, spd=900, size=1.4)
    return dict(grain=6, flash=0.45 * math.exp(-max(tb, 0) * 8) * (tb > 0), ca=5 * k, mb=0.3 * k)


def s_lift(c, t, T):
    I = red_I(T)
    sx, sy, sr = shake(T, 8, 25, 1.2)
    cam(c, sx, sy, 1.05, sr)
    draw_side_tunnel(c, 300, T, red=1, door_x=1250)
    # jets from the door at the right
    for i in range(50):
        ph = (T * (2 + 2 * hsh(i)) + hsh(i + 1)) % 1
        y0 = 760 + hsh(i + 2) * 700
        L = (150 + 450 * hsh(i + 3)) * (0.4 + ph)
        c.drawLine(790, y0, 790 - L, y0 - 40 * hsh(i + 4) + 300 * ph * ph, P('#e3f8ff', 0.55 * (1 - ph * 0.5), w=3, blur=1.5))
    yw = 900
    draw_water_side(c, yw - 4, T, 300, amp=1.4, flow=2.2, layer='back')
    k = sm(ramp(t, 0.1, 1.4))
    pose = dict(shF=0.9 + (PI - 0.25 - 0.9) * k, elF=1.6 * (1 - k) + 0.12, shB=0.8 + (PI - 0.45 - 0.8) * k, elB=1.6 * (1 - k) + 0.2,
                lean=-0.05, head=-0.15 * k, fear=1, mouth=0.5 + 0.3 * math.sin(T * 7), hipF=0.1, hipB=-0.1, kneeF=0.2, kneeB=0.2,
                open=1.0 - blink(T, 2.0))

    def carry(cc, hand_, hc, pf):
        cs = 470
        draw_side(cc, 'child', hand_[0] - 0.02 * 900, hand_[1] + 0.6 * cs * (0.4 + 0.6 * k), cs, 1,
                  dict(hipF=0.6 + 0.4 * math.sin(T * 9) * k + 0.8 * (1 - k), kneeF=1.2, hipB=0.2 + 0.9 * (1 - k), kneeB=1.4, shF=2.4 * k + 1.0 * (1 - k), elF=0.3,
                       shB=2.0 * k + 1.2 * (1 - k), elB=0.3, mouth=0.8, fear=1, rot=-10 * (1 - k)), pf=pf)
    lit(c, lambda pf: draw_side(c, 'hero', 420, 1480, 900, -1, pose, pf, carry=carry), rim=('#ff8a70', 3, 0, 0.55),
        shades=[(lin((0, 300), (0, 1500), [(RED, 0.4 * I), ('#000000', 0.4)]), 1)], dark=0.22, water=(yw, '#0a3440', 0.86))
    splash(c, 420, yw, T, k=1.0, seed=5, w_=130)
    draw_water_side(c, yw, T, 300, amp=1.4, flow=2.2, alpha=0.86)
    return dict(grain=6)


def s_burst2(c, t, T):
    return tunnel_burst(c, t, T, 0.55, 2.6, show_guard=True, speed=4.2)


def s_under(c, t, T):
    if t < 0.35:
        c.drawPaint(P('#d9f4f7'))
        for i in range(60):
            x, y = hsh(i) * W, hsh(i + 1) * H
            c.drawCircle(x, y, 60 + 80 * hsh(i + 2), P('#7fb8c4', 0.4, blur=40))
        return dict(grain=6, flash=0.2 * (1 - t / 0.35), mb=0.3)
    tt = t - 0.35
    rot = -12 * math.sin(T * 0.6) + 8 * tt
    cam(c, 0, 0, 1.0, rot)
    draw_underwater(c, T, dark=0.1 + 0.08 * tt, red=0.7, rays=1.0)
    bubbles(c, T, 140, seed=51, origin=(540, 1100, 520), born=68.15 + 0.35, spd=380, size=24, a=0.9)
    hx, hy = 470 + 30 * math.sin(T * 0.8), 1250 + 30 * math.sin(T * 0.6)
    pose = dict(shF=2.1 + 0.15 * math.sin(T * 2), elF=0.15, shB=1.0 + 0.5 * math.sin(T * 2.3), elB=0.8, hipF=0.5 + 0.3 * math.sin(T * 2), kneeF=0.8, hipB=-0.3, kneeB=1.0,
                mouth=0.3, lean=0.3)
    c.save()
    c.translate(hx, hy)
    c.rotate(-35)
    hpos = draw_side(c, 'hero', 0, 0, 760, 1, pose, PF(), carry=None) if False else None
    c.restore()
    # place the child so hands meet
    def hero_draw(pf):
        c.save(); c.translate(hx, hy); c.rotate(-35)
        r = draw_side(c, 'hero', 0, 0, 760, 1, pose, pf)
        c.restore()
        return r
    ra = math.radians(-35)
    hl = draw_side(skia.Surface(4, 4).getCanvas(), 'hero', 0, 0, 760, 1, pose)
    hw_ = (hx + hl[0] * math.cos(ra) - hl[1] * math.sin(ra), hy + hl[0] * math.sin(ra) + hl[1] * math.cos(ra))
    cpose = dict(shF=2.3 + 0.1 * math.sin(T * 2.5), elF=0.1, shB=1.6, elB=0.5, hipF=0.7 + 0.3 * math.sin(T * 3), kneeF=1.0, hipB=-0.2, kneeB=0.9, mouth=0.3, lean=0.2)
    crot = 160 + 10 * math.sin(T * 0.9)
    cl = draw_side(skia.Surface(4, 4).getCanvas(), 'child', 0, 0, 420, 1, cpose)
    rc = math.radians(crot)
    cl_w = (cl[0] * math.cos(rc) - cl[1] * math.sin(rc), cl[0] * math.sin(rc) + cl[1] * math.cos(rc))
    cx_, cy_ = hw_[0] - cl_w[0], hw_[1] - cl_w[1]
    dk = 0.45 + 0.1 * tt

    def child_draw(pf):
        c.save(); c.translate(cx_, cy_); c.rotate(crot)
        draw_side(c, 'child', 0, 0, 420, 1, cpose, pf)
        c.restore()
    lit(c, child_draw, dark=dk, shades=[(lin((0, 0), (0, H), [(CYAN, 0.25), ('#000000', 0.3)]), 1)], rim=('#7fe8ff', 0, -3, 0.5))
    lit(c, hero_draw, dark=dk, shades=[(lin((0, 0), (0, H), [(CYAN, 0.25), ('#000000', 0.3)]), 1)], rim=('#7fe8ff', 0, -3, 0.5))
    bubbles(c, T, 20, seed=52, origin=(hx + 60, hy - 380, 30), born=68.6, spd=300, size=12, a=0.8)
    bubbles(c, T, 50, seed=53, spd=260, size=14, a=0.5)
    c.drawPaint(P('#000000', 0.15 + 0.08 * tt))
    return dict(grain=6, uw=1.0)


def s_hands(c, t, T):
    cam(c, 0, 0, 1.0 + 0.04 * t, 2 * math.sin(T * 0.7))
    draw_underwater(c, T, dark=0.35 + 0.1 * t, red=0.9, surface=False, rays=0.7)
    slip = sm(ramp(t, 0.8, 2.25))
    gone = ramp(t, 2.25, 3.85)
    cx_ = 590 + 110 * slip + 260 * eout(gone)
    cy_ = 820 - 70 * slip - 420 * eout(gone)
    ca = 150 + 8 * math.sin(T * 3) + 25 * gone
    c.saveLayer()
    hand(c, cx_, cy_, ca, 150, curl=0.35 - 0.2 * gone, skin=mixh(LOOKS['child']['skin'], '#5f8f9a', 0.25), sleeve=LOOKS['child']['top'], child=True, spread=0.3 * gone)
    c.drawPaint(P('#000000', clamp(0.15 + 0.75 * gone), blend=ATOP))
    c.restore()
    reach = eout(gone)
    hx_, hy_ = 400 + 120 * reach + 8 * math.sin(T * 9) * slip, 1040 - 120 * reach
    curl = 0.85 * (1 - slip) + 0.25 * slip - 0.25 * reach
    c.saveLayer()
    hand(c, hx_, hy_, -32 + 6 * math.sin(T * 7) * slip, 230, curl=clamp(curl), skin=mixh(LOOKS['hero']['skin'], '#5f8f9a', 0.25), sleeve=LOOKS['hero']['top'], spread=reach)
    c.drawPaint(P(shader=lin((0, 600), (0, 1400), [(CYAN, 0.15), ('#000000', 0.35)]), blend=ATOP))
    c.restore()
    bubbles(c, T, 40, seed=61, origin=(520, 930, 120), born=72.1 + 0.9, spd=240, size=12, a=0.8)
    bubbles(c, T, 30, seed=62, spd=200, size=10, a=0.4)
    return dict(grain=6, uw=0.7, black=ramp(t, 3.25, 3.85))


def s_end(c, t, T):
    c.drawPaint(P('#000000'))
    a = sm(ramp(t, 0.2, 0.6))
    text_c(c, 'ПРОДОЛЖЕНИЕ', 540, 900, 96, '#ffffff', a, tf=FONT_BL, spacing=4)
    text_c(c, 'СЛЕДУЕТ', 540, 1020, 96, '#ffffff', a, tf=FONT_BL, spacing=10)
    c.drawLine(400, 1060, 680, 1060, P('#ff2a1f', 0.9 * a, w=5))
    return dict(grain=5)


SHOTS = [
    (0.0, 4.2, s_open_close),
    (4.2, 7.3, s_open_door),
    (7.3, 10.04, s_open_hit),
    (10.04, 11.28, s_dark),
    (11.28, 13.25, s_title),
    (13.25, 15.7, s_mall),
    (15.7, 19.05, s_elev_intro),
    (19.05, 23.2, s_elev_shake),
    (23.2, 25.36, s_indicator([(23.2, '-1'), (23.3, '-3')])),
    (25.36, 26.97, s_elev_lookup),
    (26.97, 28.2, s_indicator([(26.97, '-6'), (27.02, '-7')])),
    (28.2, 32.0, s_guard),
    (32.0, 35.3, s_doors),
    (35.3, 36.9, s_floor),
    (36.9, 38.6, s_speaker),
    (38.6, 41.12, group_tunnel_listen),
    (41.12, 44.95, s_run_toward),
    (44.95, 48.58, s_flood_side),
    (48.58, 49.84, s_child_scream),
    (49.84, 52.2, s_grab_run),
    (52.2, 54.9, s_rising),
    (54.9, 59.78, s_door),
    (59.78, 62.0, s_woman),
    (62.0, 63.5, s_lock),
    (63.5, 65.84, s_lift),
    (65.84, 68.15, s_burst2),
    (68.15, 72.1, s_under),
    (72.1, 75.95, s_hands),
    (75.95, 78.0, s_end),
]
DURATION = 78.0


def shot_at(T):
    for a, b, f in SHOTS:
        if a <= T < b:
            return a, b, f
    return SHOTS[-1]
