from lib import *

WATER_TOP = '#1f6a78'
WATER_MID = '#0c3442'
WATER_DEEP = '#03121a'
RED = '#ff2a1f'
CYAN = '#7fe8ff'


# ------------------------------------------------------------------ particles
def sparks(c, x, y, t, n=40, seed=0, life=0.7, spd=900, g=1800, spread=360, dirang=-90, size=1.0):
    if t < 0 or t > life * 1.6:
        return
    for i in range(n):
        h1, h2, h3 = hsh(i + seed * 100), hsh(i + seed * 100 + 33), hsh(i + seed * 100 + 77)
        lt = t - h3 * 0.15
        if lt < 0:
            continue
        L = life * (0.5 + h2)
        if lt > L:
            continue
        a = math.radians(dirang + (h1 - 0.5) * spread)
        v = spd * (0.35 + h2)
        px = x + math.cos(a) * v * lt
        py = y + math.sin(a) * v * lt + 0.5 * g * lt * lt
        vx, vy = math.cos(a) * v, math.sin(a) * v + g * lt
        k = 0.018
        fade = 1 - lt / L
        col = mixh('#fff6d8', '#ff7a2a', 1 - fade)
        c.drawLine(px, py, px - vx * k, py - vy * k, P(col, fade, w=2.6 * size, blend=ADD))
        c.drawCircle(px, py, 3 * size, P(col, fade * 0.5, blur=4 * size, blend=ADD))


def bubbles(c, t, n=60, seed=0, x0=0, x1=W, y0=0, y1=H, spd=260, size=14, a=0.6, origin=None, born=0.0):
    hgt = (y1 - y0) + 200
    for i in range(n):
        h1, h2, h3 = hsh(i * 3 + seed), hsh(i * 7 + seed + 1), hsh(i * 11 + seed + 2)
        r = size * (0.25 + h2 * h2 * 1.4)
        sp = spd * (0.6 + h3 * 0.9) * (0.7 + r / size * 0.4)
        if origin is not None:
            lt = t - born - h1 * 0.4
            if lt < 0:
                continue
            ox, oy, rad_ = origin
            ang = h2 * 2 * PI
            bx = ox + math.cos(ang) * rad_ * (0.3 + h3) + math.sin(lt * 3 + i) * 18
            by = oy + math.sin(ang) * rad_ * 0.5 * (0.3 + h1) - sp * lt * 1.3
            aa = a * clamp(1.5 - lt * 0.6)
        else:
            bx = x0 + h1 * (x1 - x0) + math.sin(t * (1.5 + h2) + i) * 16
            by = y1 + 100 - ((t * sp + h3 * hgt) % hgt)
            aa = a
        if aa <= 0:
            continue
        rr = r * (1 + 0.08 * math.sin(t * 9 + i))
        c.drawOval(oval(bx, by, rr, rr * 0.92), P(CYAN, aa * 0.10))
        c.drawOval(oval(bx, by, rr, rr * 0.92), P('#d8f6ff', aa * 0.55, w=max(1.0, rr * 0.13)))
        c.drawCircle(bx - rr * 0.35, by - rr * 0.35, rr * 0.22, P('#ffffff', aa * 0.85))


def dust(c, t, n=50, seed=5, col='#cfe6ee', a=0.25, spd=12, x0=0, x1=W, y0=0, y1=H, size=2.0):
    for i in range(n):
        h1, h2, h3 = hsh(i + seed * 50), hsh(i + seed * 50 + 9), hsh(i + seed * 50 + 17)
        x = x0 + ((h1 * (x1 - x0) + t * spd * (h2 - 0.3) * 3) % (x1 - x0))
        y = y0 + ((h2 * (y1 - y0) + t * spd * (0.5 + h3)) % (y1 - y0))
        c.drawCircle(x, y, size * (0.5 + h3), P(col, a * (0.4 + 0.6 * abs(math.sin(t * 0.8 + i))), blur=size * 0.6))


# ------------------------------------------------------------------ perspective tunnel
class Tun:
    def __init__(self, camz=0.0, camx=0.0, camy=0.0, vp=(540, 820), F=880, hw=2.0, floor=1.6, ceil=-1.7, zend=None, level=0.05, roll=0.0):
        self.camz, self.camx, self.camy = camz, camx, camy
        self.vp, self.F, self.hw, self.floor, self.ceil = vp, F, hw, floor, ceil
        self.zend = zend
        self.level = level

    @property
    def yw(self):
        return self.floor - self.level

    def dz(self, z):
        return max(z - self.camz, 0.08)

    def pr(self, x, y, z):
        d = self.dz(z)
        return (self.vp[0] + (x - self.camx) * self.F / d, self.vp[1] + (y - self.camy) * self.F / d)

    def sc(self, z):
        return self.F / self.dz(z)


def lamp_I(t, k):
    return 0.35 + 0.65 * max(0.0, math.sin(t * 2 * PI * 0.9 - k * 0.7)) ** 2


def draw_tunnel(c, T, t, red=1.0, cyan=0.5, zfar=None, flow=1.0, lamp_t=None):
    lamp_t = t if lamp_t is None else lamp_t
    fog = '#04070b'
    c.drawPaint(P(fog))
    hw, fl, ce = T.hw, T.floor, T.ceil
    zf = T.zend if T.zend is not None else (zfar or T.camz + 48)
    step = 3.0
    near = T.camz + 0.25
    # far
    if T.zend is None:
        cx, cy = T.pr(0, (fl + ce) / 2, zf)
        c.drawCircle(cx, cy, 300, P(shader=rad((cx, cy), 300, [('#0b1b24', 1), (fog, 0)])))
    kmax = int(math.floor(zf / step))
    kmin = int(math.floor(near / step))
    zs = [zf] + [k * step for k in range(kmax, kmin, -1) if k * step < zf] + [near]
    lamps = []
    for j in range(len(zs) - 1):
        z0, z1 = zs[j], max(zs[j + 1], near)
        if z0 <= near:
            continue
        zm = (z0 + z1) / 2
        fg = math.exp(-(zm - T.camz) / 15.0)
        wall = mixh(fog, '#3b4553', fg)
        side_r = mixh(fog, '#323b48', fg)
        ceilc = mixh(fog, '#1b222c', fg)
        floorc = mixh(fog, '#1a2128', fg)
        q = lambda x, y, z: T.pr(x, y, z)
        c.drawPath(path([q(-hw, ce, z0), q(-hw, fl, z0), q(-hw, fl, z1), q(-hw, ce, z1)]), P(wall))
        c.drawPath(path([q(hw, ce, z0), q(hw, fl, z0), q(hw, fl, z1), q(hw, ce, z1)]), P(side_r))
        c.drawPath(path([q(-hw, ce, z0), q(hw, ce, z0), q(hw, ce, z1), q(-hw, ce, z1)]), P(ceilc))
        c.drawPath(path([q(-hw, fl, z0), q(hw, fl, z0), q(hw, fl, z1), q(-hw, fl, z1)]), P(floorc))
        # panel seams & stains
        for yy in (-0.6, 0.6):
            c.drawLine(*q(-hw, yy, z0), *q(-hw, yy, z1), P('#000000', 0.25 * fg, w=max(1, 0.02 * T.sc(zm))))
        # pipes
        for (px, py, pr_, col) in ((-hw + 0.18, -1.05, 0.13, '#2c343e'), (-hw + 0.16, -0.72, 0.08, '#3a2f2a'), (hw - 0.2, -1.2, 0.15, '#28303a'), (hw - 0.12, 0.9, 0.06, '#2a3038')):
            a0, a1 = q(px, py, z0), q(px, py, z1)
            wpx = pr_ * T.sc(zm) * 2
            c.drawLine(*a0, *a1, P(mixh(fog, col, fg), w=wpx, cap=False))
            c.drawLine(a0[0], a0[1] - wpx * 0.25, a1[0], a1[1] - wpx * 0.25, P(mixh(fog, '#7c8794', fg), 0.6, w=max(1, wpx * 0.15), cap=False))
        # ceiling cable tray
        c.drawLine(*q(-0.5, ce + 0.05, z0), *q(-0.5, ce + 0.05, z1), P(mixh(fog, '#202730', fg), w=max(1, 0.1 * T.sc(zm)), cap=False))
        k = int(round(z0 / step))
        if z0 != zf or T.zend is None:
            # rib ring
            rp = path([q(-hw, fl, z0), q(-hw, ce, z0), q(hw, ce, z0), q(hw, fl, z0)], close=False)
            wpx = max(1.5, 0.28 * T.sc(z0))
            c.drawPath(rp, P(mixh(fog, '#262d36', fg), w=wpx))
            c.drawPath(rp, P(mixh(fog, '#68737f', fg), 0.5, w=max(1, wpx * 0.12)))
            if k % 2 == 0:
                lamps.append((k, z0 - 0.4, fg))
    # end wall
    if T.zend is not None:
        fg = math.exp(-(T.zend - T.camz) / 15.0)
        c.drawPath(path([T.pr(-hw, ce, T.zend), T.pr(hw, ce, T.zend), T.pr(hw, fl, T.zend), T.pr(-hw, fl, T.zend)]), P(mixh(fog, '#3a4250', fg)))
    c.save()
    c.drawPaint(tex_paint(CONCRETE, a=0.32, blend=OVER, scale=2.2))
    c.restore()
    # lamps
    for (k, z, fg) in lamps:
        I = lamp_I(lamp_t, k) * red
        p = T.pr(-hw + 0.06, -1.25, z)
        s = T.sc(z)
        c.drawCircle(p[0], p[1], 2.6 * s, P(shader=rad(p, 2.6 * s, [(RED, 0.30 * I * fg), (RED, 0)]), blend=ADD))
        c.drawRect(skia.Rect.MakeXYWH(p[0] - 0.05 * s, p[1] - 0.12 * s, 0.1 * s, 0.24 * s), P(mixh('#300805', '#ffd2c4', I)))
        c.drawCircle(p[0], p[1], 0.5 * s, P(RED, 0.6 * I, blur=0.25 * s, blend=ADD))
        # cold fluorescent strip, some dead / flickering
        if cyan > 0 and k % 4 == 2:
            fl_ = cyan * (0.25 if hsh(k) < 0.4 else 1.0) * (0.6 + 0.4 * (1 if math.sin(t * 37 + k) > -0.6 else 0))
            a0, a1 = T.pr(-0.3, ce + 0.02, z + 0.6), T.pr(0.3, ce + 0.02, z + 0.6)
            c.drawLine(*a0, *a1, P('#dff8ff', 0.8 * fl_ * fg, w=max(1, 0.06 * s)))
            m = ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2)
            c.drawCircle(m[0], m[1], 1.8 * s, P(shader=rad(m, 1.8 * s, [(CYAN, 0.18 * fl_ * fg), (CYAN, 0)]), blend=ADD))
    return lamps


def draw_water_plane(c, T, t, lamps, flow=1.0, red=1.0, alpha=0.93, zfar=None, chop=1.0, lamp_t=None):
    lamp_t = t if lamp_t is None else lamp_t
    hw = T.hw
    yw = T.yw
    if yw <= T.camy + 0.01:
        return
    zf = T.zend if T.zend is not None else (zfar or T.camz + 48)
    near = T.camz + 0.12
    pf_, pn = T.pr(0, yw, zf), T.pr(0, yw, near)
    poly = path([T.pr(-hw, yw, zf), T.pr(hw, yw, zf), T.pr(hw, yw, near), T.pr(-hw, yw, near)])
    c.save()
    c.clipPath(poly, doAntiAlias=True)
    c.drawPaint(P(shader=lin((0, pf_[1]), (0, min(H, pn[1])), [('#173a45', alpha), ('#0a2730', alpha), ('#03121a', alpha)], [0, 0.35, 1])))
    for (k, z, fg) in lamps:
        I = lamp_I(lamp_t, k) * red
        ly = -1.25
        my = 2 * yw - ly
        p = T.pr(-hw + 0.3, my, z)
        s = T.sc(z)
        for j in range(5):
            yy = p[1] - 0.6 * s + j * 0.3 * s
            wob = math.sin(t * 6 + j * 1.7 + k) * 0.12 * s
            c.drawOval(oval(p[0] + wob, yy, 0.35 * s, 0.05 * s + 1), P(RED, 0.45 * I * fg, blur=0.04 * s, blend=ADD))
    # flowing streaks
    for i in range(70):
        x = -hw + hsh(i) * 2 * hw
        L = 40.0
        z = (zf if zf < T.camz + 40 else T.camz + 40) - ((t * 3.5 * flow + hsh(i + 5) * L) % L)
        if z < near + 0.1:
            continue
        a, b = T.pr(x, yw, z), T.pr(x + 0.05 * math.sin(i), yw, z - 0.9)
        fg = math.exp(-(z - T.camz) / 12.0)
        c.drawLine(*a, *b, P('#9fe6f5', 0.22 * fg * chop, w=max(1, 0.02 * T.sc(z))))
    # ripple rings
    for i in range(10):
        ph = (t * 0.7 + hsh(i + 40)) % 1.0
        z = T.camz + 1.5 + hsh(i + 41) * 10
        x = -hw * 0.8 + hsh(i + 42) * hw * 1.6
        p = T.pr(x, yw, z)
        s = T.sc(z)
        c.drawOval(oval(p[0], p[1], ph * 0.9 * s, ph * 0.18 * s), P('#bdf3ff', 0.25 * (1 - ph) * chop, w=1.5))
    c.restore()
    c.drawLine(*T.pr(-hw, yw, zf), *T.pr(-hw, yw, near), P('#8fd9e8', 0.25, w=2))
    c.drawLine(*T.pr(hw, yw, zf), *T.pr(hw, yw, near), P('#8fd9e8', 0.25, w=2))


def draw_wave_p(c, T, zw, hgt, t, seed=0, foam=1.0):
    """Wall of water filling the tunnel at depth zw, crest hgt metres above current level."""
    hw = T.hw
    yw = T.yw
    crest = yw - hgt
    zback = zw + 6
    # raised surface behind the front
    if crest > T.camy:
        c.drawPath(path([T.pr(-hw, crest, zback + 30), T.pr(hw, crest, zback + 30), T.pr(hw, crest, zw), T.pr(-hw, crest, zw)]), P('#0e3a46'))
    n = 28
    top = []
    for i in range(n + 1):
        x = -hw + 2 * hw * i / n
        dy = 0.18 * hgt * nz(t * 3 + i * 0.7, seed) + 0.08 * hgt * math.sin(i * 1.9 + t * 7)
        top.append(T.pr(x, crest + dy, zw))
    base = [T.pr(hw, yw, zw - 0.5), T.pr(-hw, yw, zw - 0.5)]
    face = path(top + base, smooth=False)
    a, b = T.pr(0, crest, zw), T.pr(0, yw, zw - 0.5)
    c.drawPath(face, P(shader=lin(a, b, [('#d9f4f7', 0.95), ('#3f8f9d', 0.95), ('#0b3a47', 0.97), ('#082a34', 0.98)], [0, 0.18, 0.55, 1])))
    s = T.sc(zw)
    # whitewater
    for i in range(70):
        u = hsh(i + seed * 13)
        v = hsh(i + seed * 13 + 50)
        x = -hw + u * 2 * hw
        y = crest + v * hgt * 0.9 + 0.1 * hgt * math.sin(t * 9 + i)
        p = T.pr(x, y, zw - 0.05)
        r = (0.12 + 0.25 * hsh(i + 7)) * s * (1.2 - v)
        c.drawCircle(p[0], p[1], r, P('#eaf9fb', 0.55 * foam * (1 - v * 0.7), blur=r * 0.5))
    # spray ahead of the crest
    for i in range(90):
        lt = (t * 1.6 + hsh(i + 300)) % 1.0
        x = -hw + hsh(i + 301) * 2 * hw
        y = crest - 0.2 - lt * (0.6 + hsh(i + 302)) * hgt * 0.5 + lt * lt * hgt * 0.6
        z = zw - lt * 2.0
        if z <= T.camz + 0.2:
            continue
        p = T.pr(x, y, z)
        ss_ = T.sc(z)
        c.drawCircle(p[0], p[1], max(1.0, 0.03 * ss_), P('#e8fbff', 0.6 * (1 - lt) * foam, blur=1.0))
    # mist
    p = T.pr(0, crest, zw - 0.3)
    c.drawOval(oval(p[0], p[1], hw * s * 1.4, 0.5 * s), P('#cfeff5', 0.25 * foam, blur=0.3 * s))


def draw_end_door(c, T, t, bulge=0.0, wheel=0.0, jets=0.0, gone=0.0, light=1.0):
    z = T.zend
    fl = T.floor
    dw, dh = 0.85, 2.35
    s = T.sc(z)
    q = lambda x, y: T.pr(x, y, z)
    # frame with hazard stripes
    fr = path([q(-dw - 0.25, fl - dh - 0.25), q(dw + 0.25, fl - dh - 0.25), q(dw + 0.25, fl), q(-dw - 0.25, fl)])
    c.drawPath(fr, P('#2a2f36'))
    c.save()
    c.clipPath(fr, doAntiAlias=True)
    for i in range(-12, 12):
        x0 = i * 0.25
        c.drawPath(path([q(x0, fl - dh - 0.3), q(x0 + 0.12, fl - dh - 0.3), q(x0 + 0.12 + 0.3, fl + 0.1), q(x0 + 0.3, fl + 0.1)]), P('#b8962c', 0.55))
    c.restore()
    # exit sign
    sp = q(0, fl - dh - 0.55)
    sw = 0.55 * s
    c.drawRect(skia.Rect.MakeXYWH(sp[0] - sw, sp[1] - 0.14 * s, 2 * sw, 0.28 * s), P('#0f5f2e'))
    c.drawRect(skia.Rect.MakeXYWH(sp[0] - sw * 1.6, sp[1] - 0.5 * s, 3.2 * sw, s), P(shader=rad(sp, 1.0 * s, [('#3cff8a', 0.25 * light), ('#3cff8a', 0)]), blend=ADD))
    text_c(c, 'ВЫХОД', sp[0], sp[1] + 0.07 * s, 0.19 * s, '#d8ffe6', 0.95, tf=FONT_XB, spacing=0.01 * s)
    if gone >= 1:
        hole = path([q(-dw, fl - dh), q(dw, fl - dh), q(dw, fl), q(-dw, fl)])
        c.drawPath(hole, P('#02090d'))
        return
    # door panel (bulging toward the camera)
    tl, tr_, br, bl = q(-dw, fl - dh), q(dw, fl - dh), q(dw, fl), q(-dw, fl)
    bx = bulge * 0.06 * s
    panel = skia.Path()
    panel.moveTo(*tl)
    panel.quadTo((tl[0] + tr_[0]) / 2, tl[1] - bx, *tr_)
    panel.quadTo(tr_[0] + bx, (tr_[1] + br[1]) / 2, *br)
    panel.quadTo((bl[0] + br[0]) / 2, br[1] + bx, *bl)
    panel.quadTo(bl[0] - bx, (tl[1] + bl[1]) / 2, *tl)
    panel.close()
    cen = q(0, fl - dh * 0.5)
    c.drawPath(panel, P(shader=rad(cen, dh * 0.75 * s, [(mixh('#56606b', '#8a95a1', bulge), 1), ('#3a424c', 1), ('#1f252c', 1)], [0, 0.6, 1])))
    c.save()
    c.clipPath(panel, doAntiAlias=True)
    c.drawPaint(tex_paint(STEEL, 0.35, OVER, 1.5))
    c.drawPaint(P(shader=rad((cen[0] - 0.2 * s, cen[1] - 0.3 * s), (0.4 + bulge * 0.8) * s, [('#ff6050', 0.25 * bulge * light), ('#ff6050', 0)]), blend=ADD))
    for j in range(4):
        yy = fl - dh + dh * (j + 0.6) / 4.2
        a, b = q(-dw, yy), q(dw, yy)
        sag = bulge * 0.09 * s * math.sin(PI * (j + 0.6) / 4.2)
        bar = skia.Path()
        bar.moveTo(*a)
        bar.quadTo((a[0] + b[0]) / 2, a[1] + sag * (1 if j > 1 else -1) * 0.6, *b)
        c.drawPath(bar, P('#1a1f25', w=0.09 * s))
        c.drawPath(bar, P('#8b96a2', 0.6, w=0.015 * s))
        for r_ in range(9):
            rx = -dw + 0.1 + r_ * (2 * dw - 0.2) / 8
            rp = q(rx, yy)
            c.drawCircle(rp[0], rp[1] - 0.035 * s, 0.017 * s, P('#9aa5b1', 0.8))
    if bulge > 0.15:
        for k in range(int(bulge * 6)):
            a = q(-0.3 + hsh(k) * 0.6, fl - dh * (0.2 + hsh(k + 9) * 0.6))
            cp = skia.Path()
            cp.moveTo(*a)
            for m_ in range(4):
                a = (a[0] + (hsh(k * 7 + m_) - 0.5) * 0.25 * s, a[1] + (hsh(k * 5 + m_) - 0.4) * 0.2 * s)
                cp.lineTo(*a)
            c.drawPath(cp, P('#0a0c0e', 0.8, w=0.012 * s))
    c.restore()
    c.drawPath(panel, P('#0b0d10', w=0.03 * s))
    # wheel lock
    wc = q(0, fl - dh * 0.48)
    wr = 0.3 * s
    c.drawCircle(wc[0], wc[1], wr, P('#14181d', w=0.05 * s))
    c.drawCircle(wc[0], wc[1], wr, P('#a63a2a', w=0.03 * s))
    for k in range(4):
        a = math.radians(wheel + k * 90)
        c.drawLine(wc[0], wc[1], wc[0] + math.cos(a) * wr, wc[1] + math.sin(a) * wr, P('#7e2a1f', w=0.035 * s))
    c.drawCircle(wc[0], wc[1], 0.06 * s, P('#c4cbd2'))
    # pressure jets through the seams
    if jets > 0:
        for i in range(60):
            side = i % 4
            u = hsh(i + 900)
            if side == 0:
                p0 = (lerp(tl[0], tr_[0], u), tl[1])
            elif side == 1:
                p0 = (tr_[0], lerp(tr_[1], br[1], u))
            elif side == 2:
                p0 = (lerp(bl[0], br[0], u), br[1])
            else:
                p0 = (tl[0], lerp(tl[1], bl[1], u))
            dx, dy = p0[0] - cen[0], p0[1] - cen[1]
            d = math.hypot(dx, dy) + 1e-3
            ph = (t * (2.5 + hsh(i + 77) * 3) + u) % 1.0
            Lj = (0.25 + 0.9 * hsh(i + 5)) * s * jets * (0.6 + 0.4 * math.sin(t * 13 + i))
            ex = p0[0] + dx / d * Lj * (0.5 + ph)
            ey = p0[1] + dy / d * Lj * (0.5 + ph) + ph * ph * 0.4 * s * jets
            c.drawLine(*p0, ex, ey, P('#dff6fb', 0.55 * jets * (1 - ph * 0.5), w=max(1.2, 0.025 * s), blur=1.2))
            c.drawCircle(ex, ey, 0.02 * s, P('#ffffff', 0.5 * jets * (1 - ph)))


def door_flying(c, T, t, k):
    """Door panel torn off and tumbling toward camera; k in [0,1]."""
    z0 = T.zend - 0.1
    z = z0 - k * (z0 - T.camz - 1.2)
    ang = k * 75
    cx, cy = 0.15 * k, T.floor - 1.17 - 0.4 * k
    dw, dh = 0.85, 2.35
    pts = []
    for (x, y) in ((-dw, -dh / 2), (dw, -dh / 2), (dw, dh / 2), (-dw, dh / 2)):
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        X = cx + x * ca
        Zz = z + x * sa * 0.8
        Y = cy + y * math.cos(math.radians(ang * 0.4)) + x * 0.15 * k
        pts.append(T.pr(X, Y, max(Zz, T.camz + 0.3)))
    pp = path(pts)
    c.drawPath(pp, P(shader=lin(pts[0], pts[2], [('#7f8a96', 1), ('#3a424c', 1), ('#1c2228', 1)])))
    c.drawPath(pp, P('#0a0c0f', w=4))


# ------------------------------------------------------------------ side-view tunnel
FLOOR_Y = 1480


def side_lamps(camx):
    out = []
    for k in range(int((camx - 600) // 900), int((camx + W + 600) // 900) + 1):
        out.append((k, k * 900 + 450 - camx))
    return out


def draw_side_tunnel(c, camx, t, red=1.0, exit_x=None, light=1.0, door_x=None, lamp_t=None):
    lamp_t = t if lamp_t is None else lamp_t
    c.drawPaint(P(shader=lin((0, 150), (0, FLOOR_Y), [('#06090e', 1), ('#2a323d', 1), ('#232a33', 1), ('#10151b', 1)], [0, 0.35, 0.8, 1])))
    c.drawPaint(tex_paint(CONCRETE, 0.42, OVER, 2.4, -camx, 0))
    # seams
    off = -(camx % 240)
    for i in range(7):
        x = off + i * 240
        c.drawLine(x, 260, x, FLOOR_Y, P('#0a0d11', 0.35, w=3))
    c.drawLine(0, 1010, W, 1010, P('#0a0d11', 0.35, w=4))
    c.drawRect(skia.Rect.MakeLTRB(0, 1010, W, FLOOR_Y), P('#000000', 0.15))
    # hazard band
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(0, 1180, W, 1215))
    for i in range(-2, 30):
        x = i * 60 - (camx % 60)
        c.drawPath(path([(x, 1180), (x + 30, 1180), (x + 60, 1215), (x + 30, 1215)]), P('#a88a2a', 0.45))
    c.restore()
    # pipes
    for (y, r, col) in ((430, 36, '#2b333d'), (515, 22, '#3b302a'), (1330, 18, '#29303a')):
        c.drawRect(skia.Rect.MakeLTRB(0, y - r, W, y + r), P(shader=lin((0, y - r), (0, y + r), [('#7d8894', 1), (col, 1), ('#07090c', 1)], [0, 0.35, 1])))
        o2 = -(camx % 520)
        for i in range(4):
            x = o2 + i * 520
            c.drawRect(skia.Rect.MakeLTRB(x - 10, y - r - 6, x + 10, y + r + 6), P('#1a1f25'))
            c.drawRect(skia.Rect.MakeLTRB(x - 10, y - r - 6, x - 6, y + r + 6), P('#8b96a2', 0.5))
    # pillars
    for k in range(int((camx - 300) // 900), int((camx + W + 300) // 900) + 1):
        x = k * 900 - camx
        c.drawRect(skia.Rect.MakeLTRB(x - 48, 200, x + 48, FLOOR_Y), P(shader=lin((x - 48, 0), (x + 48, 0), [('#0e1217', 1), ('#46505c', 1), ('#1d232a', 1), ('#07090c', 1)], [0, 0.3, 0.7, 1])))
        for j in range(12):
            y = 300 + j * 100
            c.drawCircle(x - 30, y, 4, P('#9aa5b1', 0.5))
            c.drawCircle(x + 30, y, 4, P('#9aa5b1', 0.3))
    # ceiling
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 250), P('#05070a'))
    c.drawRect(skia.Rect.MakeLTRB(0, 235, W, 262), P('#2a313a'))
    # stencil signs
    for k in range(int((camx - 700) // 1800), int((camx + W + 700) // 1800) + 1):
        x = k * 1800 + 680 - camx
        text_c(c, 'ВЫХОД  →', x, 900, 64, '#d8d2c0', 0.35, tf=FONT_B, spacing=4)
        text_c(c, 'Б-1', x, 820, 54, '#d8d2c0', 0.25, tf=FONT_B)
    if door_x is not None:
        x = door_x - camx
        c.drawRect(skia.Rect.MakeLTRB(x - 190, 700, x + 190, FLOOR_Y), P('#1c2127'))
        c.drawRect(skia.Rect.MakeLTRB(x - 160, 740, x + 160, FLOOR_Y), P(shader=lin((x - 160, 0), (x + 160, 0), [('#3c444e', 1), ('#5a6470', 1), ('#2a3038', 1)])))
        for j in range(4):
            c.drawRect(skia.Rect.MakeLTRB(x - 160, 820 + j * 170, x + 160, 845 + j * 170), P('#22272e'))
        c.drawRect(skia.Rect.MakeLTRB(x - 120, 610, x + 120, 680), P('#0f5f2e'))
        c.drawCircle(x, 645, 200, P(shader=rad((x, 645), 200, [('#3cff8a', 0.35 * light), ('#3cff8a', 0)]), blend=ADD))
        text_c(c, 'ВЫХОД', x, 662, 46, '#e0ffe9', 1, tf=FONT_XB)
    # lamps
    for k, x in side_lamps(camx):
        I = lamp_I(lamp_t, k) * red
        y = 640
        c.drawCircle(x, y, 520, P(shader=rad((x, y), 520, [(RED, 0.33 * I), (RED, 0.08 * I), (RED, 0)], [0, 0.4, 1]), blend=ADD))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 30, y - 40, x + 30, y + 40), 12, 12), P(mixh('#3a0805', '#ffd7c9', I)))
        for j in range(4):
            c.drawLine(x - 30, y - 30 + j * 20, x + 30, y - 30 + j * 20, P('#111111', w=4))
        c.drawCircle(x, y, 60, P(RED, 0.6 * I, blur=30, blend=ADD))
    # floor
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR_Y, W, H), P(shader=lin((0, FLOOR_Y), (0, H), [('#151b21', 1), ('#06080b', 1)])))
    for k, x in side_lamps(camx):
        I = lamp_I(lamp_t, k) * red
        c.drawOval(oval(x, FLOOR_Y + 120, 260, 40), P(RED, 0.25 * I, blur=30, blend=ADD))


def surf_y(x, yw, t, camx=0.0, amp=1.0, flow=1.0):
    xx = x + camx
    return yw + amp * (9 * math.sin(xx * 0.011 - 2.3 * t * flow) + 5 * math.sin(xx * 0.029 + 1.4 * t) + 2.5 * math.sin(xx * 0.071 - 4.1 * t * flow))


def draw_water_side(c, yw, t, camx=0.0, amp=1.0, flow=1.0, layer='front', red=1.0, alpha=None, x0=-50, x1=W + 50, lamp_t=None):
    lamp_t = t if lamp_t is None else lamp_t
    off = -38 if layer == 'back' else 0
    pts = []
    for i in range(0, 61):
        x = x0 + (x1 - x0) * i / 60
        pts.append((x, surf_y(x, yw + off, t, camx, amp * (0.7 if layer == 'back' else 1), flow)))
    pp = pts + [(x1, H + 50), (x0, H + 50)]
    wp = path(pp)
    if layer == 'back':
        c.drawPath(wp, P(shader=lin((0, yw - 60), (0, yw + 200), [('#14424e', 1), ('#082731', 1)])))
        return
    a = alpha if alpha is not None else 0.82
    c.drawPath(wp, P(shader=lin((0, yw - 30), (0, min(H, yw + 700)), [('#2b7f8c', a * 0.75), ('#0d3d4a', a), ('#03151d', min(1, a + 0.12))], [0, 0.25, 1])))
    sp = path(pts, close=False)
    c.drawPath(sp, P('#c8f3fb', 0.75, w=3, blur=1.2))
    sp2 = path([(x, y + 14 + 4 * math.sin(x * 0.05 + t * 3)) for x, y in pts], close=False)
    c.drawPath(sp2, P('#6fd0e0', 0.25, w=6, blur=4))
    # caustic band under the surface
    c.save()
    c.clipPath(wp, doAntiAlias=True)
    for i in range(16):
        x = ((hsh(i) * (W + 300) + t * 90 * flow - camx * 0.0) % (W + 300)) - 150
        y = surf_y(x, yw, t, camx, amp) + 40 + hsh(i + 3) * 80
        c.drawOval(oval(x, y, 60 + 40 * hsh(i + 5), 8), P('#7fe8ff', 0.10, blur=6, blend=ADD))
    c.restore()
    for k, x in side_lamps(camx):
        I = lamp_I(lamp_t, k) * red
        y = surf_y(x, yw, t, camx, amp)
        for j in range(6):
            dx = math.sin(t * 5 + j * 2.1) * 30 + (j - 3) * 26
            c.drawOval(oval(x + dx, y + 4 + j * 3, 34 + j * 6, 3.5), P('#ff6a50', 0.45 * I, blur=2, blend=ADD))
    # foam flecks travelling with the current
    for i in range(70):
        x = ((hsh(i + 60) * (W + 400) + t * 140 * flow * (0.6 + hsh(i + 61))) % (W + 400)) - 200
        y = surf_y(x, yw, t, camx, amp) + (hsh(i + 62) - 0.3) * 10
        r = 3 + 9 * hsh(i + 63)
        c.drawOval(oval(x, y, r * 1.6, r * 0.5), P('#e9fbff', 0.45, blur=1.5))


def splash(c, x, y, t, k=1.0, seed=0, w_=60):
    for i in range(int(18 * k) + 2):
        ph = (t * (1.6 + hsh(i + seed) * 1.5) + hsh(i + seed + 9)) % 1.0
        vx = (hsh(i + seed + 3) - 0.5) * 300 * k
        vy = -(180 + 320 * hsh(i + seed + 4)) * k
        px = x + (hsh(i + seed + 5) - 0.5) * w_ + vx * ph * 0.6
        py = y + vy * ph * 0.6 + 900 * (ph * 0.6) ** 2
        r = 2 + 6 * hsh(i + seed + 6) * k
        c.drawOval(oval(px, py, r, r * 1.3), P('#e6fbff', 0.7 * (1 - ph)))
    c.drawOval(oval(x, y + 4, w_ * 0.9, 10), P('#e8fbff', 0.45 * k, w=4, blur=2))
    c.drawOval(oval(x, y + 2, w_ * 0.7, 8), P('#ffffff', 0.35 * k, blur=6))


def draw_wave_side(c, xf, base, hgt, t, x0=-100, seed=0):
    """Flood front moving right; xf = front position on screen."""
    pts = [(x0, H + 50), (x0, base - hgt + 10 * nz(t * 2, seed))]
    n = 30
    for i in range(1, n + 1):
        x = x0 + (xf - 160 - x0) * i / n
        pts.append((x, base - hgt + 18 * nz(t * 3 + i * 0.4, seed) + 10 * math.sin(i + t * 6)))
    pts += [(xf - 80, base - hgt * 1.12), (xf + 10, base - hgt * 1.05), (xf + 55, base - hgt * 0.8), (xf + 40, base - hgt * 0.62),
            (xf + 70, base - hgt * 0.4), (xf + 120, base - hgt * 0.12), (xf + 200, base), (W + 100, base), (W + 100, H + 50)]
    wp = path(pts, smooth=False)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(-200, 0, xf + 210, H))
    c.drawPath(wp, P(shader=lin((0, base - hgt), (0, base + 500), [('#3e98a8', 0.95), ('#0e4250', 0.96), ('#04161d', 0.98)], [0, 0.35, 1])))
    c.restore()
    # foam
    for i in range(110):
        u, v = hsh(i + seed * 7), hsh(i + seed * 7 + 400)
        if u < 0.65:
            x = xf - 160 + u / 0.65 * 280
            y = base - hgt * (1.1 - (x - xf + 160) / 280 * 1.0 * v)
        else:
            x = x0 + (u - 0.65) / 0.35 * (xf - 160 - x0)
            y = base - hgt + v * 30
        x += 12 * math.sin(t * 11 + i)
        y += 10 * math.sin(t * 9 + i * 1.3)
        r = 8 + 26 * hsh(i + 11)
        c.drawCircle(x, y, r, P('#effcff', 0.55 * (0.5 + 0.5 * hsh(i + 12)), blur=r * 0.45))
    # spray
    for i in range(80):
        ph = (t * (1.3 + hsh(i + 500)) + hsh(i + 501)) % 1.0
        x = xf - 40 + ph * (160 + 260 * hsh(i + 502))
        y = base - hgt * 1.05 - 200 * ph * hsh(i + 503) + 700 * ph * ph
        c.drawCircle(x, y, 2 + 4 * hsh(i + 504), P('#effcff', 0.7 * (1 - ph)))
    c.drawOval(oval(xf + 40, base - hgt * 0.9, 200, 90), P('#d6f2f7', 0.25, blur=50))


# ------------------------------------------------------------------ underwater
def draw_underwater(c, t, dark=0.0, red=0.4, surface=True, rays=1.0, rot=0.0):
    c.drawPaint(P(shader=lin((0, 0), (0, H), [('#0f3b4a', 1), ('#062130', 1), ('#01070b', 1)], [0, 0.45, 1])))
    if surface:
        for i in range(8):
            y = 90 + i * 22
            pts = [(x, y + 14 * math.sin(x * 0.01 + t * 2 + i) + 8 * math.sin(x * 0.033 - t * 3)) for x in range(-40, W + 80, 40)]
            c.drawPath(path(pts, close=False, smooth=True), P('#9fe9f7', 0.12 * (1 - i / 8), w=6 - i * 0.5, blur=3))
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 120), P(shader=lin((0, 0), (0, 160), [('#7fd6e6', 0.35), ('#7fd6e6', 0)])))
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 300), P(shader=lin((0, 0), (0, 300), [(RED, 0.18 * red * (0.6 + 0.4 * math.sin(t * 5.6))), (RED, 0)]), blend=ADD))
    if rays:
        for i in range(7):
            x = 80 + i * 150 + 40 * math.sin(t * 0.4 + i)
            wt, wb = 30 + 20 * hsh(i), 140 + 80 * hsh(i + 2)
            sk = 160 + 60 * math.sin(i)
            a = rays * 0.07 * (0.6 + 0.4 * math.sin(t * 1.7 + i * 2))
            c.drawPath(path([(x - wt, 0), (x + wt, 0), (x + sk + wb, 1500), (x + sk - wb, 1500)]),
                       P(shader=lin((0, 0), (0, 1500), [('#b9f3ff', a), ('#b9f3ff', 0)]), blend=ADD, blur=18))
    dust(c, t, 70, seed=9, col='#a8d8e2', a=0.35, spd=10, size=2.2)
    if dark:
        c.drawPaint(P('#000000', dark))


# ------------------------------------------------------------------ elevator interior (front view)
EB = (170, 380, 910, 1560)


def draw_elevator(c, t, light=1.0, red=0.0, spark=None):
    l, tp, r, b = EB
    base = mixh('#141820', '#717b88', light)
    side = mixh('#0e1117', '#59626e', light)
    c.drawPaint(P('#05070a'))
    back = path([(l, tp), (r, tp), (r, b), (l, b)])
    lw = path([(0, 0), (l, tp), (l, b), (0, H)])
    rw = path([(W, 0), (r, tp), (r, b), (W, H)])
    ceil = path([(0, 0), (W, 0), (r, tp), (l, tp)])
    flo = path([(l, b), (r, b), (W, H), (0, H)])
    c.drawPath(back, P(shader=lin((0, tp), (0, b), [(mixh(base, '#ffffff', 0.08), 1), (base, 1), (mixh(base, '#000000', 0.3), 1)])))
    c.drawPath(lw, P(shader=lin((0, 0), (l, 0), [(mixh(side, '#000000', 0.4), 1), (side, 1)])))
    c.drawPath(rw, P(shader=lin((W, 0), (r, 0), [(mixh(side, '#000000', 0.5), 1), (side, 1)])))
    c.drawPath(ceil, P(mixh('#07090c', '#2b313a', light)))
    c.drawPath(flo, P(shader=lin((0, b), (0, H), [(mixh('#07090b', '#2a2d33', light), 1), ('#050608', 1)])))
    for pp in (back, lw, rw):
        c.save()
        c.clipPath(pp, doAntiAlias=True)
        c.drawPaint(tex_paint(STEEL, 0.55, OVER, 1.6))
        c.restore()
    for x in (417, 663):
        c.drawLine(x, tp, x, b, P('#0b0d10', 0.6, w=3))
        c.drawLine(x + 3, tp, x + 3, b, P('#ffffff', 0.08 * light, w=2))
    # handrails
    hy = 1110
    c.drawLine(l + 20, hy, r - 20, hy, P('#0a0b0d', 0.6, w=26, blur=6))
    c.drawLine(l + 20, hy - 8, r - 20, hy - 8, P(mixh('#22262c', '#c9d1d9', light), w=20))
    c.drawLine(l + 20, hy - 13, r - 20, hy - 13, P('#ffffff', 0.35 * light, w=4))
    for (x0, y0, x1, y1) in ((l - 5, hy - 8, 0, hy + 230), (r + 5, hy - 8, W, hy + 230)):
        c.drawLine(x0, y0, x1, y1, P(mixh('#22262c', '#b9c1c9', light), w=24))
    # control panel on right wall
    c.drawPath(path([(960, 820), (1040, 780), (1040, 1150), (960, 1140)]), P(mixh('#101317', '#3a414a', light)))
    for j in range(6):
        y = 860 + j * 45
        c.drawOval(oval(1000, y, 12, 14), P('#d8f4ff', 0.25 + 0.4 * (j == 5)))
    # ceiling light panel
    lp = path([(330, 170), (750, 170), (800, 330), (280, 330)])
    c.drawPath(lp, P(mixh('#14171c', '#f3fbff', light)))
    if light > 0.05:
        c.drawPath(lp, P('#e9fbff', 0.6 * light, blur=30, blend=ADD))
        c.drawCircle(540, 280, 700, P(shader=rad((540, 280), 700, [('#dff6ff', 0.20 * light), ('#dff6ff', 0)]), blend=ADD))
        c.drawOval(oval(540, b + 140, 360, 60), P('#e9f6ff', 0.10 * light, blur=30, blend=ADD))
    if red > 0:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(500, 345, 580, 375), 8, 8), P(mixh('#300', '#ff9a8a', red) if False else mixh('#300606', '#ff9a8a', red)))
        c.drawCircle(540, 400, 900, P(shader=rad((540, 380), 900, [(RED, 0.35 * red), (RED, 0.1 * red), (RED, 0)], [0, 0.5, 1]), blend=ADD))


def draw_indicator(c, t, val, flick=1.0, shake_=(0, 0), red=0.0):
    c.drawPaint(P(shader=lin((0, 0), (W, H), [('#59626e', 1), ('#2b3139', 1), ('#3d454f', 1)])))
    c.drawPaint(tex_paint(STEEL, 0.6, OVER, 3))
    for i in range(30):
        x = hsh(i) * W
        y = hsh(i + 3) * H
        c.drawLine(x, y, x + 60 * hsh(i + 5), y + 8 * hsh(i + 6), P('#ffffff', 0.08, w=1))
    box = skia.Rect.MakeLTRB(170, 560, 910, 1120)
    c.drawRRect(skia.RRect.MakeRectXY(box.makeOutset(26, 26), 38, 38), P('#15181c'))
    c.drawRRect(skia.RRect.MakeRectXY(box.makeOutset(26, 26), 38, 38), P('#9aa4ae', 0.5, w=3))
    c.drawRRect(skia.RRect.MakeRectXY(box, 22, 22), P('#050505'))
    text_c(c, 'ЭТАЖ', 540, 480, 64, '#c6ccd2', 0.7, tf=FONT_B, spacing=14)
    for (x, y) in ((110, 420), (970, 420), (110, 1270), (970, 1270)):
        c.drawCircle(x, y, 16, P('#20252b'))
        c.drawLine(x - 10, y - 4, x + 10, y + 4, P('#8a949e', w=4))
    a = flick
    c.save()
    c.clipRect(box)
    tx = 600 + shake_[0]
    text_c(c, val, tx, 1010, 400, RED, 0.35 * a, tf=FONT_BL, blur=30)
    text_c(c, val, tx, 1010, 400, '#ff3a2e', 0.95 * a, tf=FONT_BL)
    text_c(c, val, tx, 1010, 400, '#ffd0c8', 0.35 * a, tf=FONT_BL, blur=3)
    ar = 0.5 + 0.5 * (math.sin(t * 12) > 0)
    c.drawPath(path([(230, 760), (330, 760), (280, 860)]), P('#ff3a2e', 0.9 * ar * a))
    for y in range(560, 1120, 6):
        c.drawLine(170, y, 910, y, P('#000000', 0.35, w=2))
    c.restore()
    c.drawCircle(540, 840, 700, P(shader=rad((540, 840), 700, [(RED, 0.22 * a), (RED, 0)]), blend=ADD))
    if red:
        c.drawPaint(P(RED, 0.1 * red, blend=ADD))


# ------------------------------------------------------------------ mall (side view)
def draw_mall(c, camx, t):
    c.drawPaint(P(shader=lin((0, 0), (0, H), [('#0a1220', 1), ('#18263a', 1), ('#0f1824', 1)], [0, 0.6, 1])))
    # upper gallery
    px = camx * 0.55
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 360), P('#070b12'))
    for i in range(-2, 14):
        x = i * 160 - (px % 160)
        c.drawCircle(x, 120, 9, P('#f6fbff', 0.9))
        c.drawCircle(x, 120, 40, P('#d9f2ff', 0.25, blur=20, blend=ADD))
    c.drawRect(skia.Rect.MakeLTRB(0, 360, W, 420), P('#1d2838'))
    c.drawRect(skia.Rect.MakeLTRB(0, 420, W, 520), P('#9fd6ee', 0.12))
    c.drawLine(0, 420, W, 420, P('#cfeaf7', 0.5, w=3))
    # storefronts
    for i in range(-1, 6):
        x = i * 520 - (camx * 0.85 % 520)
        c.drawRect(skia.Rect.MakeLTRB(x + 20, 620, x + 480, 1380), P('#0a0f17'))
        c.drawRect(skia.Rect.MakeLTRB(x + 40, 700, x + 460, 1380), P(shader=lin((0, 700), (0, 1380), [('#2f6f8a', 1), ('#163246', 1), ('#0d1a26', 1)])))
        for j in range(3):
            mx = x + 110 + j * 130
            c.drawOval(oval(mx, 900, 34, 40), P('#0b141e', 0.85))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(mx - 48, 940, mx + 48, 1250), 30, 30), P('#0b141e', 0.85))
        c.drawRect(skia.Rect.MakeLTRB(x + 120, 640, x + 380, 685), P('#e6f6ff', 0.85))
        c.drawRect(skia.Rect.MakeLTRB(x + 100, 620, x + 400, 705), P('#bfe9ff', 0.3, blur=20, blend=ADD))
        c.drawLine(x + 40, 700, x + 40, 1380, P('#c9e6f2', 0.25, w=4))
        c.drawPath(path([(x + 300, 700), (x + 380, 700), (x + 200, 1380), (x + 120, 1380)]), P('#ffffff', 0.05))
    # elevator portal
    ex = 1350 - camx
    c.drawRect(skia.Rect.MakeLTRB(ex - 200, 760, ex + 200, 1460), P('#2a313b'))
    c.drawRect(skia.Rect.MakeLTRB(ex - 170, 800, ex + 170, 1460), P(shader=lin((0, 800), (0, 1460), [('#e8ddc8', 1), ('#a99f8d', 1)])))
    c.drawRect(skia.Rect.MakeLTRB(ex - 170, 800, ex + 170, 1460), P('#ffffff', 0.15, blur=30, blend=ADD))
    c.drawRect(skia.Rect.MakeLTRB(ex - 215, 800, ex - 170, 1460), P('#8d96a1'))
    c.drawRect(skia.Rect.MakeLTRB(ex + 170, 800, ex + 215, 1460), P('#8d96a1'))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ex - 60, 700, ex + 60, 745), 6, 6), P('#050505'))
    text_c(c, '1 ▼', ex, 737, 34, '#ff3a2e', 0.95, tf=FONT_XB)
    # floor
    c.drawRect(skia.Rect.MakeLTRB(0, 1460, W, H), P(shader=lin((0, 1460), (0, H), [('#253244', 1), ('#0b111a', 1)])))
    for i in range(-1, 8):
        x = i * 260 - (camx % 260)
        c.drawLine(x, 1460, x - 300, H, P('#000000', 0.25, w=2))
    for i in range(-1, 6):
        x = i * 520 - (camx * 0.85 % 520)
        c.drawRect(skia.Rect.MakeLTRB(x + 60, 1470, x + 440, 1760), P(shader=lin((0, 1470), (0, 1760), [('#4fa3c4', 0.22), ('#4fa3c4', 0)])))
    c.drawRect(skia.Rect.MakeLTRB(ex - 170, 1470, ex + 170, 1800), P(shader=lin((0, 1470), (0, 1800), [('#f0e6d2', 0.35), ('#f0e6d2', 0)])))
    return ex


def draw_speaker(c, t, I):
    c.drawPaint(P(shader=lin((0, 0), (0, H), [('#1b2129', 1), ('#2f3742', 1), ('#11161c', 1)])))
    c.drawPaint(tex_paint(CONCRETE, 0.5, OVER, 1.4))
    # cable
    c.drawPath(path([(980, -20), (900, 300), (760, 520)], close=False, smooth=True), P('#0b0d10', w=16))
    # bracket
    c.drawRect(skia.Rect.MakeLTRB(700, 470, 860, 560), P('#262c33'))
    for (x, y) in ((720, 490), (840, 490), (720, 540), (840, 540)):
        c.drawCircle(x, y, 7, P('#8f99a3'))
    # horn
    horn = path([(700, 520), (360, 330), (300, 420), (330, 780), (420, 830), (700, 600)], smooth=True)
    c.drawPath(horn, P(shader=lin((300, 330), (700, 830), [('#c9d0d6', 1), ('#69737d', 1), ('#2b3036', 1)])))
    c.drawOval(oval(340, 580, 85, 255), P('#1a1d21'))
    c.drawOval(oval(340, 580, 60, 210), P(shader=rad((340, 580), 200, [('#05060a', 1), ('#262b31', 1)])))
    vib = 4 * math.sin(t * 60) * (0.5 + 0.5 * math.sin(t * 7))
    c.drawOval(oval(345 + vib * 0.3, 580, 26, 80), P('#3a3f46'))
    c.drawPath(horn, P('#ffffff', 0.25, w=3))
    # rotating beacon
    bx, by = 600, 1060
    ang = t * 5.0
    beam_dir = math.cos(ang)
    c.drawRect(skia.Rect.MakeLTRB(bx - 80, by + 60, bx + 80, by + 110), P('#20242a'))
    c.drawOval(oval(bx, by, 80, 85), P(mixh('#5a0a06', '#ff5a40', 0.5 + 0.5 * abs(beam_dir))))
    c.drawOval(oval(bx - 20, by - 30, 25, 20), P('#ffd0c8', 0.6))
    c.drawCircle(bx, by, 140, P(RED, 0.6 * (0.5 + 0.5 * abs(beam_dir)), blur=60, blend=ADD))
    L_ = 1400
    a0 = ang
    for side in (0, PI):
        aa = a0 + side
        wx = math.cos(aa)
        if wx < -0.2:
            continue
        x1 = bx + math.cos(aa) * L_
        y1 = by + math.sin(aa) * L_ * 0.35
        c.drawPath(path([(bx, by - 30), (x1, y1 - 300), (x1, y1 + 300), (bx, by + 30)]),
                   P(shader=lin((bx, by), (x1, y1), [(RED, 0.35 * I), (RED, 0)]), blend=ADD, blur=20))
    c.drawPaint(P(RED, 0.10 * (0.5 + 0.5 * math.sin(ang * 2)) * I, blend=ADD))
    dust(c, t, 60, seed=4, col='#ffb0a0', a=0.35, spd=8, size=2.5)
    text_c(c, 'ОПАСНО', 540, 1450, 92, '#d9cfa8', 0.3, tf=FONT_BL, spacing=16)
