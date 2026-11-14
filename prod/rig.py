from lib import *

LOOKS = {
    'hero':   dict(skin='#d6a387', hair='#141110', style='messy', top='#272b34', top2='#1c1f26', pants='#0d0e11', shoes='#d9dbe0', bw=1.0, hood=True),
    'guard':  dict(skin='#c99579', hair='#3b3631', style='short', top='#1b2849', top2='#121c35', pants='#131b31', shoes='#0b0b0c', bw=1.14, badge=True, gray=True),
    'father': dict(skin='#cf9c7d', hair='#2a1c13', style='short', top='#6b4528', top2='#4e321d', pants='#1c1e25', shoes='#2a211b', bw=1.08, shirt='#9aa3ad'),
    'child':  dict(skin='#e3b495', hair='#5c3a21', style='kid', top='#b9232b', top2='#8a171d', pants='#29324a', shoes='#e2e2e2', bw=0.9, kid=True, backpack=True),
    'woman':  dict(skin='#e0ae93', hair='#110d0c', style='long', top='#6e727a', top2='#53565d', pants='#1a1c23', shoes='#1b1b1b', bw=0.88, woman=True),
}
DARK = '#000000'


class PF:
    """Paint factory; when override is set, all parts render as one silhouette colour."""

    def __init__(self, override=None, oa=1.0):
        self.o = override
        self.oa = oa

    def __call__(self, col, a=1.0, w=0, blur=0, shader=None):
        if self.o is not None:
            return P(self.o, self.oa, w=w, blend=DSTOVER)
        return P(col, a, w=w, blur=blur, shader=shader)

    @property
    def sil(self):
        return self.o is not None


def jp(b, ang, L):
    return (b[0] + math.sin(ang) * L, b[1] + math.cos(ang) * L)


def seg(c, pf, a, b, w, col):
    c.drawLine(a[0], a[1], b[0], b[1], pf(col, w=w))


SIDE_DEF = dict(lean=0.0, head=0.0, hipF=0.04, kneeF=0.06, hipB=-0.04, kneeB=0.06, shF=0.1, elF=0.25,
                shB=-0.1, elB=0.25, rot=0.0, bob=0.0, mouth=0.0, open=1.0, fear=0.0)


def walk(ph, amp=1.0):
    s, co = math.sin(ph), math.cos(ph)
    return dict(hipF=0.36 * s * amp, hipB=-0.36 * s * amp,
                kneeF=0.08 + 0.8 * max(0, co) * amp, kneeB=0.08 + 0.8 * max(0, -co) * amp,
                shF=-0.32 * s * amp, shB=0.32 * s * amp, elF=0.3 + 0.25 * max(0, -s), elB=0.3 + 0.25 * max(0, s),
                bob=-0.012 * abs(co) * amp, lean=0.05)


def run(ph, amp=1.0):
    s, co = math.sin(ph), math.cos(ph)
    return dict(hipF=0.75 * s * amp, hipB=-0.75 * s * amp,
                kneeF=0.25 + 1.45 * max(0, co) * amp, kneeB=0.25 + 1.45 * max(0, -co) * amp,
                shF=-0.85 * s * amp, shB=0.85 * s * amp, elF=1.45, elB=1.45,
                bob=-0.035 * abs(co) * amp + 0.02, lean=0.24 * amp)


def side_head(c, L, pf, hc, ang, r, po):
    c.save()
    c.translate(*hc)
    c.rotate(math.degrees(ang))
    skin = L['skin']
    hair = L['hair']
    style = L['style']
    if style == 'long' and not pf.sil:
        c.drawPath(path([(-r * 0.7, -r * 0.8), (-r * 1.05, 0), (-r * 1.15, r * 1.6), (-r * 0.9, r * 2.6), (-r * 0.2, r * 2.4),
                         (-r * 0.1, r * 1.2), (r * 0.2, r * 0.3), (r * 0.3, -r * 0.6)], smooth=True), pf(hair))
    # skull + jaw
    c.drawOval(oval(0, 0, r * 0.95, r * 1.06), pf(skin))
    c.drawOval(oval(r * 0.28, r * 0.38, r * 0.6, r * 0.6), pf(skin))
    c.drawPath(path([(r * 0.82, -r * 0.08), (r * 1.1, r * 0.22), (r * 0.84, r * 0.3)]), pf(mixh(skin, DARK, 0.06)))
    if not pf.sil:
        c.drawOval(oval(-r * 0.12, r * 0.08, r * 0.16, r * 0.24), pf(mixh(skin, DARK, 0.2)))
        op = po['open']
        if r > 9:
            c.drawOval(oval(r * 0.56, -r * 0.08, r * 0.15, max(0.6, r * 0.1 * op)), pf('#ddd6d0'))
            c.drawCircle(r * 0.66, -r * 0.08, max(0.8, r * 0.07 * min(1, op + 0.2)), pf('#1a120d'))
        else:
            c.drawCircle(r * 0.62, -r * 0.08, max(0.8, r * 0.09), pf('#1a120d'))
        f = po['fear']
        c.drawLine(r * 0.36, -r * 0.3 - f * r * 0.05, r * 0.8, -r * 0.28 - f * r * 0.16, pf(hair, w=max(1, r * 0.1)))
        m = po['mouth']
        if m > 0.05:
            c.drawOval(oval(r * 0.72, r * 0.5, r * 0.14, r * 0.14 * m + 1), pf('#2a0b0b'))
        else:
            c.drawLine(r * 0.6, r * 0.52, r * 0.82, r * 0.5, pf(mixh(skin, DARK, 0.45), w=max(1, r * 0.05)))
    # hair cap
    pts = []
    if style == 'messy':
        n = 16
        for i in range(n + 1):
            ph = math.radians(215 - i * (200 / n))
            rr = r * (1.06 + (0.16 if i % 2 else 0.0) * (1 - i / (n * 1.4)))
            pts.append((math.cos(ph) * rr, -math.sin(ph) * rr * 1.06))
        pts += [(r * 0.62, -r * 0.18), (r * 0.42, -r * 0.42), (r * 0.25, -r * 0.2), (r * 0.05, -r * 0.45), (-r * 0.35, -r * 0.1), (-r * 0.6, r * 0.35)]
        c.drawPath(path(pts), pf(hair))
    elif style in ('short', 'kid', 'long'):
        n = 12
        top = 1.05 if style != 'kid' else 1.08
        for i in range(n + 1):
            ph = math.radians(215 - i * (195 / n))
            pts.append((math.cos(ph) * r * top, -math.sin(ph) * r * top * 1.05))
        if style == 'kid':
            pts += [(r * 0.75, -r * 0.2), (r * 0.3, -r * 0.4), (-r * 0.4, -r * 0.1), (-r * 0.75, r * 0.4)]
        elif style == 'long':
            pts += [(r * 0.75, -r * 0.3), (r * 0.2, -r * 0.5), (-r * 0.2, -r * 0.1), (-r * 0.7, r * 0.5)]
        else:
            pts += [(r * 0.62, -r * 0.48), (r * 0.15, -r * 0.55), (-r * 0.35, -r * 0.2), (-r * 0.62, r * 0.3)]
        c.drawPath(path(pts, smooth=True), pf(hair))
        if L.get('gray') and not pf.sil:
            c.drawOval(oval(-r * 0.25, -r * 0.1, r * 0.25, r * 0.3), pf('#7d7a76', 0.6))
    c.restore()


def draw_side(c, key, x, y, s, facing=1, pose=None, pf=None, carry=None):
    L = LOOKS[key]
    pf = pf or PF()
    po = dict(SIDE_DEF)
    po.update(pose or {})
    kid = L.get('kid')
    if kid:
        hr, torso, thigh, shin, ua, fa, neck = 0.1, 0.25, 0.2, 0.19, 0.15, 0.13, 0.02
    else:
        hr, torso, thigh, shin, ua, fa, neck = 0.066, 0.30, 0.245, 0.235, 0.175, 0.155, 0.035
    u = s
    bw = L['bw']
    hipY = y - (thigh + shin + 0.03) * u * 0.985 + po['bob'] * u
    c.save()
    c.translate(x, hipY)
    c.scale(facing, 1)
    c.rotate(po['rot'])
    hip = (0.0, 0.0)
    lean = po['lean']
    ax = (math.sin(lean), -math.cos(lean))
    nr = (math.cos(lean), math.sin(lean))
    sh = (ax[0] * torso * u, ax[1] * torso * u)
    shj = (sh[0] - nr[0] * 0.01 * u, sh[1] - nr[1] * 0.01 * u + 0.02 * u)
    top, top2, pants = L['top'], L['top2'], L['pants']

    def leg(hipA, kneeA, back):
        k = jp(hip, hipA, thigh * u)
        sa = hipA - kneeA
        a = jp(k, sa, shin * u)
        pc = mixh(pants, DARK, 0.35) if back else pants
        seg(c, pf, hip, k, 0.088 * u * bw, pc)
        seg(c, pf, k, a, 0.068 * u * bw, pc)
        fw = (math.cos(sa), -math.sin(sa))
        toe = (a[0] + fw[0] * 0.075 * u, a[1] + fw[1] * 0.075 * u)
        sc = mixh(L['shoes'], DARK, 0.4) if back else L['shoes']
        seg(c, pf, (a[0] - fw[0] * 0.015 * u, a[1] - fw[1] * 0.015 * u), toe, 0.045 * u, sc)
        if not pf.sil:
            seg(c, pf, (a[0] - fw[0] * 0.02 * u + 0.012 * u * math.sin(sa), a[1] + 0.016 * u), (toe[0], toe[1] + 0.016 * u), 0.014 * u, mixh(sc, '#ffffff', 0.3) if not back else sc)

    def arm(shA, elA, back):
        e = jp(shj, shA, ua * u)
        w_ = jp(e, shA + elA, fa * u)
        cc = top2 if back else top
        seg(c, pf, shj, e, 0.062 * u * bw, cc)
        seg(c, pf, e, w_, 0.052 * u * bw, cc)
        c.drawCircle(*jp(w_, shA + elA, 0.02 * u), 0.022 * u, pf(mixh(L['skin'], DARK, 0.3 if back else 0.0)))
        return w_

    arm(po['shB'], po['elB'], True)
    leg(po['hipB'], po['kneeB'], True)
    if L.get('backpack'):
        bp = (ax[0] * 0.14 * u - nr[0] * 0.1 * u, ax[1] * 0.14 * u - nr[1] * 0.1 * u)
        c.save(); c.translate(*bp); c.rotate(math.degrees(lean))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-0.05 * u, -0.08 * u, 0.1 * u, 0.17 * u), 0.03 * u, 0.03 * u), pf('#253552'))
        c.restore()
    c.drawCircle(0, 0.01 * u, 0.078 * u * bw, pf(pants))
    tp = [(-nr[0] * 0.075 * u * bw, -nr[1] * 0.075 * u * bw + 0.03 * u),
          (nr[0] * 0.07 * u * bw, nr[1] * 0.07 * u * bw + 0.03 * u),
          (ax[0] * 0.2 * u + nr[0] * 0.088 * u * bw, ax[1] * 0.2 * u + nr[1] * 0.088 * u * bw),
          (sh[0] + nr[0] * 0.06 * u * bw, sh[1] + nr[1] * 0.06 * u * bw),
          (sh[0] - nr[0] * 0.065 * u * bw, sh[1] - nr[1] * 0.065 * u * bw),
          (ax[0] * 0.14 * u - nr[0] * 0.085 * u * bw, ax[1] * 0.14 * u - nr[1] * 0.085 * u * bw)]
    c.drawPath(path(tp, smooth=True), pf(top))
    if not pf.sil:
        if L.get('badge'):
            c.drawCircle(ax[0] * 0.21 * u + nr[0] * 0.07 * u, ax[1] * 0.21 * u + nr[1] * 0.07 * u, 0.014 * u, pf('#c9a54a'))
            c.drawLine(-nr[0] * 0.08 * u, 0.035 * u, nr[0] * 0.08 * u, 0.035 * u, pf('#0a0d16', w=0.02 * u))
        if L.get('hood'):
            c.drawCircle(sh[0] - nr[0] * 0.055 * u, sh[1] - nr[1] * 0.055 * u + 0.015 * u, 0.045 * u, pf(top2))
    leg(po['hipF'], po['kneeF'], False)
    # neck + head
    nb = (sh[0], sh[1])
    ha = lean + po['head']
    hu = (math.sin(ha), -math.cos(ha))
    r = hr * u
    hc = (nb[0] + hu[0] * (neck * u + r * 0.95) + nr[0] * 0.012 * u, nb[1] + hu[1] * (neck * u + r * 0.95))
    seg(c, pf, (nb[0], nb[1] + 0.01 * u), (hc[0] + 0.004 * u, hc[1] + r * 0.5), 0.05 * u * (0.8 if kid else 1), mixh(L['skin'], DARK, 0.18))
    side_head(c, L, pf, hc, ha, r, po)
    hand = arm(po['shF'], po['elF'], False)
    if carry:
        carry(c, hand, hc, pf)
    c.restore()
    ra = math.radians(po['rot'])
    hx_, hy_ = hand[0] * math.cos(ra) - hand[1] * math.sin(ra), hand[0] * math.sin(ra) + hand[1] * math.cos(ra)
    return (x + hx_ * facing, hipY + hy_)


# ------------------------------------------------------------------ front / back
FRONT_DEF = dict(sway=0.0, armL=0.12, elL=0.1, armR=0.12, elR=0.1, liftL=0.0, liftR=0.0, spread=0.0, tilt=0.0,
                 turn=0.0, mouth=0.0, open=1.0, fear=0.0, blink=0.0, lookx=0.0, looky=0.0, breath=0.0, fsL=0.0, fsR=0.0, bob=0.0)


def front_face(c, L, pf, r, po):
    if pf.sil:
        return
    skin, hair = L['skin'], L['hair']
    tr = po['turn']
    op = po['open'] * (1 - po['blink'])
    f = po['fear']
    for i in (-1, 1):
        ex = i * 0.38 * r + tr * 0.28 * r
        ey = -0.02 * r
        ew = 0.19 * r * (1 - 0.25 * tr * i)
        if r > 14:
            eh = 0.11 * r * op * (1 + 0.3 * f)
            if eh > 0.8:
                c.drawOval(oval(ex, ey, ew, eh), pf('#e3dcd5'))
                c.save()
                c.clipRect(oval(ex, ey, ew, eh))
                c.drawCircle(ex + po['lookx'] * ew * 0.5, ey + po['looky'] * eh * 0.3, 0.085 * r, pf('#2a1a10'))
                c.drawCircle(ex + po['lookx'] * ew * 0.5 + 0.02 * r, ey - 0.03 * r, 0.025 * r, pf('#ffffff', 0.8))
                c.restore()
            c.drawLine(ex - ew, ey - 0.01 * r, ex + ew, ey - 0.01 * r - 0.0 * r if op < 0.2 else ey - eh * 0.9, pf('#1a1310', w=0.04 * r) if False else pf('#1a1310', 0.0))
            c.drawArc(oval(ex, ey, ew, max(0.5, 0.11 * r * op * (1 + 0.3 * f))), 180, 180, False, pf('#1a1310', w=max(1, 0.045 * r)))
        else:
            c.drawCircle(ex, ey, max(1, 0.09 * r * max(op, 0.2)), pf('#1a120d'))
        by = -0.3 * r - f * 0.08 * r
        c.drawLine(ex - i * 0.2 * r * -1 if False else ex - 0.2 * r, by + (f * 0.07 * r if i == 1 else -f * 0.0 * r) * 0 + (i * f * 0.06 * r),
                   ex + 0.2 * r, by - (i * f * 0.06 * r), pf(hair, w=max(1, 0.07 * r)))
    c.drawLine(tr * 0.3 * r, 0.05 * r, tr * 0.36 * r + 0.04 * r, 0.32 * r, pf(mixh(skin, DARK, 0.25), w=max(1, 0.05 * r)))
    m = po['mouth']
    mx = tr * 0.26 * r
    if m > 0.05:
        c.drawOval(oval(mx, 0.55 * r, 0.17 * r * (0.8 + 0.3 * m), 0.06 * r + 0.16 * r * m), pf('#2b0a0a'))
        if r > 20:
            c.drawOval(oval(mx, 0.55 * r - 0.06 * r - 0.1 * r * m, 0.12 * r, 0.03 * r), pf('#d9d2c8', 0.8))
    else:
        c.drawLine(mx - 0.15 * r, 0.56 * r + f * 0.02 * r, mx + 0.15 * r, 0.56 * r + f * 0.02 * r, pf(mixh(skin, '#5a1f1f', 0.5), w=max(1, 0.05 * r)))


def front_hair(c, L, pf, r, po, back):
    hair = L['hair']
    st = L['style']
    tr = po['turn']
    if back:
        pts = []
        n = 18
        for i in range(n + 1):
            ph = math.radians(-10 + i * 200 / n)
            rr = r * (1.08 + (0.1 if (st == 'messy' and i % 2) else 0))
            pts.append((math.cos(ph) * rr, -math.sin(ph) * rr * 1.03))
        bottom = 0.75 if st != 'long' else 2.6
        pts += [(-r * 0.95, r * bottom * 0.6), (-r * 0.6, r * bottom), (r * 0.6, r * bottom), (r * 0.95, r * bottom * 0.6)]
        c.drawPath(path(pts, smooth=(st != 'messy')), pf(hair))
        return
    pts = []
    n = 14
    for i in range(n + 1):
        ph = math.radians(-12 + i * 204 / n)
        rr = r * (1.07 + (0.12 if (st == 'messy' and i % 2) else 0))
        pts.append((math.cos(ph) * rr + tr * 0.1 * r, -math.sin(ph) * rr * 1.04))
    if st == 'messy':
        pts += [(-r * 0.85, -r * 0.2), (-r * 0.6, -r * 0.42), (-r * 0.45, -r * 0.2), (-r * 0.2, -r * 0.48), (0, -r * 0.22),
                (r * 0.25, -r * 0.5), (r * 0.45, -r * 0.24), (r * 0.65, -r * 0.45), (r * 0.9, -r * 0.15)]
        pts = [(p[0] + tr * 0.1 * r, p[1]) for p in pts]
        c.drawPath(path(pts), pf(hair))
    elif st == 'long':
        pts += [(-r * 0.9, -r * 0.1), (-r * 0.3, -r * 0.55), (r * 0.5, -r * 0.4), (r * 0.92, -r * 0.05)]
        c.drawPath(path(pts, smooth=True), pf(hair))
        for i in (-1, 1):
            c.drawPath(path([(i * r * 0.98, -r * 0.2), (i * r * 1.12, r * 0.6), (i * r * 1.05, r * 1.6), (i * r * 0.75, r * 1.5), (i * r * 0.8, r * 0.5)], smooth=True), pf(hair))
    else:
        hl = -0.5 if st == 'short' else -0.35
        pts += [(-r * 0.9, -r * 0.1), (-r * 0.4, r * hl), (r * 0.4, r * hl), (r * 0.9, -r * 0.1)]
        c.drawPath(path(pts, smooth=True), pf(hair))
        if L.get('gray') and not pf.sil:
            for i in (-1, 1):
                c.drawOval(oval(i * r * 0.9, -r * 0.05, r * 0.12, r * 0.3), pf('#8a8580', 0.7))


def draw_front(c, key, x, y, s, pose=None, back=False, pf=None, hold=None):
    L = LOOKS[key]
    pf = pf or PF()
    po = dict(FRONT_DEF)
    po.update(pose or {})
    kid = L.get('kid')
    u = s
    bw = L['bw']
    if kid:
        hr, torso, thigh, shin, ua, fa = 0.1, 0.25, 0.2, 0.19, 0.15, 0.13
        sw, hw = 0.095 * bw, 0.075 * bw
    else:
        hr, torso, thigh, shin, ua, fa = 0.066, 0.30, 0.245, 0.235, 0.175, 0.155
        sw, hw = 0.118 * bw, 0.088 * bw
        if L.get('woman'):
            sw, hw = 0.105, 0.095
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(po['sway']))
    hipY = -(thigh + shin + 0.03) * u + po['bob'] * u
    shY = hipY - torso * u - po['breath'] * 0.006 * u
    top, top2, pants = L['top'], L['top2'], L['pants']
    r = hr * u
    hc = (0.0, shY - 0.03 * u - r * 0.95)
    if L['style'] == 'long' and not back and not pf.sil:
        c.drawPath(path([(-r * 1.0, hc[1] - r * 0.3), (-r * 1.25, hc[1] + r * 2.5), (r * 1.25, hc[1] + r * 2.5), (r * 1.0, hc[1] - r * 0.3)], smooth=True), pf(L['hair']))
    geo = []
    for i, a, el, fs in ((-1, po['armL'], po['elL'], po['fsL']), (1, po['armR'], po['elR'], po['fsR'])):
        sj = (i * sw * 0.9 * u, shY + 0.035 * u)
        e = (sj[0] + i * math.sin(a) * ua * u, sj[1] + math.cos(a) * ua * u)
        a2 = a - el
        fl = fa * u * (1 - 0.45 * fs)
        w_ = (e[0] + i * math.sin(a2) * fl, e[1] + math.cos(a2) * fl)
        hp = (w_[0] + i * math.sin(a2) * 0.02 * u, w_[1] + math.cos(a2) * 0.02 * u)
        geo.append((sj, e, w_, hp))
    hands = [g[3] for g in geo]
    if hold and po.get('hold_first'):
        hold(c, hands, hc, pf)
    # legs
    for i, lift in ((-1, po['liftL']), (1, po['liftR'])):
        hj = (i * hw * 0.55 * u, hipY)
        k = (hj[0] + i * (0.01 + po['spread']) * u, hipY + thigh * u * (1 - 0.6 * lift))
        a = (k[0] + i * 0.004 * u, k[1] + shin * u * (1 - 0.15 * lift))
        pc = pants if not back else pants
        seg(c, pf, hj, k, 0.09 * u * bw, pc)
        seg(c, pf, k, a, 0.07 * u * bw, pc)
        c.drawOval(oval(a[0] + i * 0.008 * u, a[1] + 0.01 * u, 0.045 * u, 0.025 * u * (1 + lift)), pf(L['shoes']))
    if back and L.get('backpack'):
        pass
    # torso
    tp = [(-sw * u, shY + 0.02 * u), (-sw * 0.97 * u, shY + 0.13 * u), (-hw * 1.12 * u, hipY + 0.035 * u), (hw * 1.12 * u, hipY + 0.035 * u),
          (sw * 0.97 * u, shY + 0.13 * u), (sw * u, shY + 0.02 * u), (sw * 0.55 * u, shY - 0.012 * u), (0, shY - 0.016 * u), (-sw * 0.55 * u, shY - 0.012 * u)]
    c.drawPath(path(tp, smooth=True), pf(top))
    if not pf.sil:
        if not back:
            if L.get('hood'):
                c.drawLine(-0.02 * u, shY + 0.01 * u, -0.025 * u, shY + 0.09 * u, pf('#b9bcc4', w=0.006 * u))
                c.drawLine(0.02 * u, shY + 0.01 * u, 0.025 * u, shY + 0.09 * u, pf('#b9bcc4', w=0.006 * u))
                c.drawLine(-hw * 0.8 * u, hipY - 0.06 * u, hw * 0.8 * u, hipY - 0.06 * u, pf(top2, w=0.012 * u))
            if L.get('badge'):
                c.drawCircle(-sw * 0.45 * u, shY + 0.07 * u, 0.016 * u, pf('#c9a54a'))
                c.drawLine(-hw * 1.1 * u, hipY + 0.01 * u, hw * 1.1 * u, hipY + 0.01 * u, pf('#0a0d16', w=0.022 * u))
                c.drawPath(path([(-0.04 * u, shY - 0.01 * u), (0, shY + 0.06 * u), (0.04 * u, shY - 0.01 * u)]), pf('#8f9bb3'))
            if L.get('shirt'):
                c.drawPath(path([(-0.035 * u, shY - 0.01 * u), (0.035 * u, shY - 0.01 * u), (0.03 * u, hipY), (-0.03 * u, hipY)]), pf(L['shirt']))
            if L.get('kid') or L.get('woman'):
                c.drawLine(0, shY, 0, hipY + 0.02 * u, pf(top2, w=0.008 * u))
            if L.get('backpack'):
                for i in (-1, 1):
                    c.drawLine(i * sw * 0.6 * u, shY, i * sw * 0.7 * u, shY + 0.14 * u, pf('#253552', w=0.025 * u))
        else:
            if L.get('backpack'):
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-sw * 0.8 * u, shY + 0.03 * u, sw * 0.8 * u, shY + 0.2 * u), 0.03 * u, 0.03 * u), pf('#253552'))
            if L.get('hood'):
                c.drawOval(oval(0, shY + 0.03 * u, sw * 0.75 * u, 0.06 * u), pf(top2))
    # neck & head
    seg(c, pf, (0, shY + 0.01 * u), (0, hc[1] + r * 0.4), 0.052 * u * (0.85 if kid else 1), mixh(L['skin'], DARK, 0.15))
    c.save()
    c.translate(*hc)
    c.rotate(math.degrees(po['tilt']))
    if back:
        c.drawOval(oval(0, 0, r * 0.95, r * 1.08), pf(L['skin']))
        for i in (-1, 1):
            c.drawOval(oval(i * r * 0.93, r * 0.1, r * 0.14, r * 0.22), pf(mixh(L['skin'], DARK, 0.15)))
        front_hair(c, L, pf, r, po, True)
    else:
        for i in (-1, 1):
            c.drawOval(oval(i * r * 0.93 + po['turn'] * 0.1 * r, r * 0.1, r * 0.14, r * 0.22), pf(mixh(L['skin'], DARK, 0.12)))
        jaw = 0.85 if not kid else 0.95
        c.drawPath(path([(-r * 0.92, -r * 0.3), (-r * 0.88, r * 0.35), (-r * 0.45 * jaw, r * 0.95), (0, r * 1.06), (r * 0.45 * jaw, r * 0.95),
                         (r * 0.88, r * 0.35), (r * 0.92, -r * 0.3), (r * 0.6, -r * 0.95), (0, -r * 1.06), (-r * 0.6, -r * 0.95)], smooth=True), pf(L['skin']))
        front_face(c, L, pf, r, po)
        front_hair(c, L, pf, r, po, False)
    c.restore()
    # arms
    for (sj, e, w_, hp) in geo:
        seg(c, pf, sj, e, 0.064 * u * bw, top)
        seg(c, pf, e, w_, 0.054 * u * bw, top)
        c.drawOval(oval(hp[0], hp[1], 0.022 * u, 0.026 * u), pf(L['skin']))
    if hold and not po.get('hold_first'):
        hold(c, hands, hc, pf)
    c.restore()
    return hands


def lit(c, fn, rim=None, shades=(), dark=0.0, water=None):
    """Draw a character with directional shading, rim light and optional submerged tint.
    rim=(color, dx, dy, alpha); shades=[(shader, alpha)]; water=(y, color, alpha)."""
    c.saveLayer()
    fn(PF())
    for sh, a in shades:
        c.drawPaint(P(shader=sh, a=a, blend=ATOP))
    if dark:
        c.drawPaint(P('#05070c', dark, blend=ATOP))
    if rim:
        col, dx, dy, a = rim
        c.save()
        c.translate(dx, dy)
        fn(PF(col, a))
        c.restore()
    if water is not None:
        wy, wc, wa = water
        p = P(shader=lin((0, wy), (0, wy + 400), [(wc, wa * 0.75), (wc, wa)]), blend=ATOP)
        c.drawRect(skia.Rect.MakeLTRB(-5000, wy, 5000, 5000), p)
    c.restore()


# ------------------------------------------------------------------ portraits (close-ups)
PORTRAIT_DEF = dict(fear=0.0, open=1.0, mouth=0.0, blink=0.0, lookx=0.0, looky=0.0, tilt=0.0, pale=0.0, wet=0.0, turn=0.0, brow=0.0, scream=0.0)


def portrait(c, key, cx, cy, hh, ex=None, light=None, clothes=True, t=0.0):
    """hh = head height in px. light = dict(key=(color, alpha, side), rim=(color, alpha, side))"""
    L = LOOKS[key]
    e = dict(PORTRAIT_DEF)
    e.update(ex or {})
    u = hh
    skin = mixh(L['skin'], '#a9b4bd', e['pale'] * 0.45)
    hair = L['hair']
    kid = L.get('kid')
    wom = L.get('woman')
    hw = 0.39 if not kid else 0.43
    if wom:
        hw = 0.36
    c.save()
    c.translate(cx, cy)
    c.rotate(e['tilt'])
    tr = e['turn']
    # long hair back layer
    if L['style'] == 'long':
        c.drawPath(path([(-0.45 * u, -0.35 * u), (-0.62 * u, 0.4 * u), (-0.7 * u, 1.4 * u), (0.7 * u, 1.4 * u), (0.62 * u, 0.4 * u), (0.45 * u, -0.35 * u), (0, -0.62 * u)], smooth=True), P(hair))
    # clothes / shoulders
    if clothes:
        top, top2 = L['top'], L['top2']
        c.drawPath(path([(-1.6 * u, 1.6 * u), (-1.35 * u, 0.98 * u), (-0.6 * u, 0.74 * u), (0, 0.7 * u), (0.6 * u, 0.74 * u), (1.35 * u, 0.98 * u), (1.6 * u, 1.6 * u)], smooth=False), P(top))
        c.drawRect(skia.Rect.MakeLTRB(-1.6 * u, 1.3 * u, 1.6 * u, 3 * u), P(top))
        if L.get('hood'):
            c.drawPath(path([(-0.55 * u, 0.62 * u), (-0.3 * u, 0.98 * u), (0.3 * u, 0.98 * u), (0.55 * u, 0.62 * u), (0.35 * u, 0.86 * u), (-0.35 * u, 0.86 * u)], smooth=True), P(top2))
            c.drawLine(-0.1 * u, 0.9 * u, -0.12 * u, 1.35 * u, P('#b4b8c0', w=0.018 * u))
            c.drawLine(0.1 * u, 0.9 * u, 0.12 * u, 1.35 * u, P('#b4b8c0', w=0.018 * u))
        if L.get('badge'):
            c.drawPath(path([(-0.22 * u, 0.7 * u), (0, 1.05 * u), (0.22 * u, 0.7 * u), (0.1 * u, 0.7 * u), (0, 0.85 * u), (-0.1 * u, 0.7 * u)]), P('#9aa6bd'))
            c.drawPath(path([(-0.06 * u, 0.86 * u), (0, 1.15 * u), (0.06 * u, 0.86 * u)]), P('#0d1424'))
            c.drawPath(path([(-0.75 * u, 1.05 * u), (-0.6 * u, 1.0 * u), (-0.55 * u, 1.12 * u), (-0.62 * u, 1.24 * u), (-0.72 * u, 1.18 * u)], smooth=True), P('#c9a54a'))
            c.drawLine(-1.2 * u, 0.95 * u, -0.25 * u, 0.78 * u, P(top2, w=0.04 * u))
            c.drawLine(1.2 * u, 0.95 * u, 0.25 * u, 0.78 * u, P(top2, w=0.04 * u))
        if kid:
            c.drawLine(0, 0.82 * u, 0, 2 * u, P('#d7d7d7', w=0.02 * u))
            c.drawPath(path([(-0.3 * u, 0.66 * u), (0, 0.84 * u), (0.3 * u, 0.66 * u), (0.32 * u, 0.8 * u), (0, 0.95 * u), (-0.32 * u, 0.8 * u)], smooth=True), P(top2))
            for i in (-1, 1):
                c.drawLine(i * 0.75 * u, 0.85 * u, i * 0.85 * u, 2 * u, P('#253552', w=0.09 * u))
        if wom:
            c.drawPath(path([(-0.3 * u, 0.7 * u), (0, 1.1 * u), (0.3 * u, 0.7 * u)]), P(top2))
            c.drawLine(0, 1.1 * u, 0, 2 * u, P(top2, w=0.012 * u))
    # neck
    c.drawRect(skia.Rect.MakeLTRB(-0.17 * u, 0.2 * u, 0.17 * u, 0.86 * u), P(mixh(skin, DARK, 0.12)))
    c.drawRect(skia.Rect.MakeLTRB(-0.17 * u, 0.2 * u, 0.17 * u, 0.86 * u), P(shader=lin((0, 0.3 * u), (0, 0.6 * u), [('#000000', 0.45), ('#000000', 0.0)])))
    # ears
    for i in (-1, 1):
        c.drawOval(oval(i * (hw + 0.02) * u + tr * 0.03 * u, 0.02 * u, 0.055 * u, 0.1 * u), P(mixh(skin, DARK, 0.1)))
        c.drawOval(oval(i * (hw + 0.025) * u + tr * 0.03 * u, 0.02 * u, 0.025 * u, 0.06 * u), P(mixh(skin, DARK, 0.3)))
    # head shape
    jaw = 0.29 if not kid else 0.33
    if wom:
        jaw = 0.24
    head = path([(-hw * u, -0.12 * u), (-(hw - 0.01) * u, 0.12 * u), (-jaw * u, 0.36 * u), (-0.1 * u, 0.5 * u), (0, 0.51 * u), (0.1 * u, 0.5 * u),
                 (jaw * u, 0.36 * u), ((hw - 0.01) * u, 0.12 * u), (hw * u, -0.12 * u), (0.3 * u, -0.42 * u), (0, -0.5 * u), (-0.3 * u, -0.42 * u)], smooth=True)
    c.drawPath(head, P(skin))
    c.save()
    c.clipPath(head, doAntiAlias=True)
    # facial modelling
    c.drawPaint(P(shader=rad((tr * 0.1 * u, -0.05 * u), 0.55 * u, [('#000000', 0.0), ('#000000', 0.0), ('#000000', 0.35)], [0, 0.55, 1.0])))
    for i in (-1, 1):
        c.drawOval(oval(i * 0.25 * u, 0.2 * u, 0.12 * u, 0.08 * u), P('#b0484a', 0.10 if not kid else 0.2, blur=0.04 * u))
        c.drawOval(oval(i * 0.3 * u + tr * 0.05 * u, 0.18 * u, 0.05 * u, 0.14 * u), P('#000000', 0.12, blur=0.04 * u))
    if key in ('guard', 'father'):
        c.drawPath(path([(-0.3 * u, 0.15 * u), (-0.2 * u, 0.48 * u), (0.2 * u, 0.48 * u), (0.3 * u, 0.15 * u), (0, 0.42 * u)], smooth=True), P('#1a1512', 0.22 if key == 'guard' else 0.16, blur=0.03 * u))
    if key == 'guard':
        for k in range(3):
            yy = -0.3 * u + k * 0.04 * u - e['fear'] * 0.02 * u
            c.drawArc(oval(0, yy + 0.2 * u, 0.2 * u, 0.2 * u), 230, 80, False, P('#5a3a2c', 0.35, w=0.008 * u))
        for i in (-1, 1):
            c.drawArc(oval(i * 0.22 * u, 0.28 * u, 0.14 * u, 0.16 * u), 200 if i < 0 else -40, 60 if i < 0 else 60, False, P('#5a3a2c', 0.35, w=0.01 * u))
    c.restore()
    # eyes
    f = e['fear']
    op = e['open'] * (1 - e['blink'])
    ew = (0.088 if not kid else 0.1) * u
    for i in (-1, 1):
        ex_ = i * 0.155 * u + tr * 0.05 * u
        ey = -0.03 * u
        eh = (0.038 + 0.02 * f) * u * op
        c.drawOval(oval(ex_, ey + 0.012 * u, ew * 1.25, 0.08 * u), P('#5a3329', 0.18, blur=0.02 * u))
        if eh > 1.0:
            ep = skia.Path()
            ep.moveTo(ex_ - ew, ey)
            ep.cubicTo(ex_ - ew * 0.5, ey - eh * 1.25 - (i * 0.004 * u), ex_ + ew * 0.5, ey - eh * 1.3, ex_ + ew, ey - 0.004 * u * i)
            ep.cubicTo(ex_ + ew * 0.5, ey + eh * 0.95, ex_ - ew * 0.5, ey + eh * 0.95, ex_ - ew, ey)
            ep.close()
            c.drawPath(ep, P('#e6dfd8'))
            c.save()
            c.clipPath(ep, doAntiAlias=True)
            ix, iy = ex_ + e['lookx'] * ew * 0.45, ey + e['looky'] * eh * 0.4
            ir = 0.036 * u if not kid else 0.042 * u
            c.drawCircle(ix, iy, ir, P(shader=rad((ix, iy), ir, [('#6b4a2e', 1), ('#3a2414', 1), ('#120b07', 1)], [0, 0.7, 1])))
            c.drawCircle(ix, iy, ir * (0.42 - 0.12 * f), P('#050404'))
            c.drawCircle(ix + ir * 0.35, iy - ir * 0.4, ir * 0.22, P('#ffffff', 0.9))
            c.drawPath(ep, P('#000000', 0.35, w=0.015 * u, blur=0.01 * u))
            c.restore()
            ul = skia.Path()
            ul.moveTo(ex_ - ew * 1.05, ey + 0.002 * u)
            ul.cubicTo(ex_ - ew * 0.5, ey - eh * 1.25, ex_ + ew * 0.5, ey - eh * 1.3, ex_ + ew * 1.02, ey - 0.004 * u * i)
            c.drawPath(ul, P('#1b120e', w=0.014 * u))
            cr = skia.Path()
            cr.moveTo(ex_ - ew * 0.8, ey - eh - 0.025 * u)
            cr.quadTo(ex_, ey - eh * 1.6 - 0.03 * u, ex_ + ew * 0.85, ey - eh - 0.02 * u)
            c.drawPath(cr, P('#6d4436', 0.6, w=0.008 * u))
        else:
            cl = skia.Path()
            cl.moveTo(ex_ - ew, ey)
            cl.quadTo(ex_, ey + 0.02 * u, ex_ + ew, ey)
            c.drawPath(cl, P('#1b120e', w=0.014 * u))
        # brows (fear: inner ends raised and pulled together)
        b0 = (ex_ - i * ew * 1.15 * -1 if False else ex_ + (-ew * 1.1 if i < 0 else -ew * 0.25) + (0.02 * u * f if i < 0 else 0), 0)
        inner = (i * 0.07 * u + tr * 0.05 * u - i * 0.01 * u * f, -0.13 * u - f * 0.045 * u - e['brow'] * 0.02 * u)
        outer = (i * 0.27 * u + tr * 0.05 * u, -0.12 * u + f * 0.005 * u)
        mid = ((inner[0] + outer[0]) / 2, -0.155 * u - f * 0.015 * u)
        bp = skia.Path()
        bp.moveTo(*inner)
        bp.quadTo(mid[0], mid[1], outer[0], outer[1])
        c.drawPath(bp, P(hair if not L.get('gray') else '#4a443e', w=(0.03 if not wom else 0.018) * u))
        if f > 0.3:
            c.drawLine(i * 0.02 * u, -0.12 * u, i * 0.04 * u, -0.17 * u, P('#6d4436', 0.4 * f, w=0.006 * u))
    # nose
    nx = tr * 0.08 * u
    np_ = skia.Path()
    np_.moveTo(nx - 0.03 * u, -0.05 * u)
    np_.quadTo(nx - 0.05 * u, 0.1 * u, nx - 0.06 * u, 0.15 * u)
    c.drawPath(np_, P('#7a4a38', 0.35, w=0.012 * u, blur=0.006 * u))
    for i in (-1, 1):
        c.drawOval(oval(nx + i * 0.035 * u, 0.17 * u, 0.022 * u, 0.012 * u), P('#3a1e16', 0.7))
    c.drawOval(oval(nx, 0.145 * u, 0.04 * u, 0.03 * u), P('#ffffff', 0.08, blur=0.01 * u))
    # mouth
    m = clamp(e['mouth'])
    mx = tr * 0.07 * u
    my = 0.3 * u
    mw = (0.11 + 0.03 * m + 0.02 * e['scream']) * u
    if kid:
        mw *= 0.9
    if m > 0.04:
        mh = (0.012 + 0.11 * m + 0.05 * e['scream']) * u
        mp = skia.Path()
        mp.moveTo(mx - mw, my)
        mp.cubicTo(mx - mw * 0.6, my - mh * 0.75, mx + mw * 0.6, my - mh * 0.75, mx + mw, my)
        mp.cubicTo(mx + mw * 0.7, my + mh * 1.25, mx - mw * 0.7, my + mh * 1.25, mx - mw, my)
        mp.close()
        c.drawPath(mp, P('#2a0909'))
        c.save()
        c.clipPath(mp, doAntiAlias=True)
        c.drawRect(skia.Rect.MakeLTRB(mx - mw, my - mh, mx + mw, my - mh * 0.5), P('#d8d0c4', 0.9))
        c.drawOval(oval(mx, my + mh * 0.9, mw * 0.55, mh * 0.45), P('#7a2b2b', 0.8))
        c.restore()
        c.drawPath(mp, P(mixh(skin, '#7a3030', 0.55), w=0.012 * u))
    else:
        mp = skia.Path()
        mp.moveTo(mx - mw, my + f * 0.01 * u)
        mp.quadTo(mx, my - 0.012 * u + f * 0.02 * u * -1, mx + mw, my + f * 0.01 * u)
        c.drawPath(mp, P(mixh(skin, '#6a2a2a', 0.55), w=0.014 * u))
        c.drawOval(oval(mx, my + 0.03 * u, mw * 0.6, 0.015 * u), P(mixh(skin, '#7a3030', 0.4), 0.6))
    # hair
    if L['style'] == 'messy':
        pts = [(-0.44 * u, 0.05 * u), (-0.47 * u, -0.25 * u), (-0.4 * u, -0.5 * u), (-0.22 * u, -0.64 * u), (-0.05 * u, -0.6 * u), (0.05 * u, -0.7 * u),
               (0.22 * u, -0.6 * u), (0.38 * u, -0.6 * u), (0.47 * u, -0.38 * u), (0.47 * u, -0.1 * u), (0.42 * u, 0.04 * u),
               (0.38 * u, -0.16 * u), (0.32 * u, -0.22 * u), (0.3 * u, -0.14 * u), (0.22 * u, -0.25 * u), (0.15 * u, -0.17 * u), (0.1 * u, -0.27 * u),
               (0.02 * u, -0.16 * u), (-0.05 * u, -0.28 * u), (-0.12 * u, -0.18 * u), (-0.2 * u, -0.27 * u), (-0.27 * u, -0.17 * u), (-0.33 * u, -0.24 * u),
               (-0.38 * u, -0.1 * u), (-0.41 * u, 0.02 * u)]
        pts = [(p[0] + tr * 0.04 * u + nz(t * 0.7, i) * 0.004 * u, p[1]) for i, p in enumerate(pts)]
        c.drawPath(path(pts), P(hair))
        for k in range(14):
            x0 = -0.35 * u + k * 0.05 * u
            c.drawLine(x0, -0.55 * u + abs(k - 7) * 0.012 * u, x0 + 0.03 * u, -0.3 * u, P('#3a3634', 0.5, w=0.006 * u))
        if e['wet'] > 0:
            for k in range(5):
                x0 = -0.22 * u + k * 0.1 * u
                c.drawLine(x0, -0.25 * u, x0 - 0.01 * u, -0.17 * u + 0.02 * u * (k % 2), P(hair, w=0.012 * u))
    elif L['style'] == 'short':
        pts = [(-0.42 * u, 0.0), (-0.45 * u, -0.3 * u), (-0.3 * u, -0.55 * u), (0, -0.62 * u), (0.3 * u, -0.55 * u), (0.45 * u, -0.3 * u),
               (0.42 * u, 0.0), (0.38 * u, -0.25 * u), (0.15 * u, -0.34 * u), (-0.15 * u, -0.33 * u), (-0.38 * u, -0.25 * u)]
        c.drawPath(path(pts, smooth=True), P(hair))
        if L.get('gray'):
            for i in (-1, 1):
                c.drawOval(oval(i * 0.41 * u, -0.17 * u, 0.04 * u, 0.12 * u), P('#8a8580', 0.8))
    elif L['style'] == 'kid':
        pts = [(-0.46 * u, 0.0), (-0.48 * u, -0.3 * u), (-0.3 * u, -0.56 * u), (0, -0.62 * u), (0.3 * u, -0.56 * u), (0.48 * u, -0.3 * u), (0.46 * u, 0.0),
               (0.4 * u, -0.2 * u), (0.25 * u, -0.25 * u), (0.1 * u, -0.2 * u), (-0.05 * u, -0.26 * u), (-0.2 * u, -0.2 * u), (-0.4 * u, -0.22 * u)]
        c.drawPath(path(pts, smooth=True), P(hair))
    elif L['style'] == 'long':
        pts = [(-0.45 * u, 0.3 * u), (-0.47 * u, -0.3 * u), (-0.3 * u, -0.56 * u), (0, -0.62 * u), (0.3 * u, -0.56 * u), (0.47 * u, -0.3 * u), (0.45 * u, 0.3 * u),
               (0.38 * u, 0.0), (0.33 * u, -0.25 * u), (0.0, -0.36 * u), (-0.2 * u, -0.25 * u), (-0.36 * u, 0.0)]
        c.drawPath(path(pts, smooth=True), P(hair))
        for i in (-1, 1):
            c.drawPath(path([(i * 0.4 * u, -0.1 * u), (i * 0.5 * u, 0.5 * u), (i * 0.55 * u, 1.1 * u), (i * 0.38 * u, 1.0 * u), (i * 0.34 * u, 0.4 * u)], smooth=True), P(hair))
    # wet highlights
    if e['wet'] > 0:
        for k in range(10):
            dx = (hsh(k) - 0.5) * 0.6 * u
            dy = (hsh(k + 20) - 0.3) * 0.6 * u + ((t * 0.08 * u * (0.5 + hsh(k + 3))) % (0.2 * u))
            c.drawCircle(dx, dy, 0.008 * u * (0.6 + hsh(k + 7)), P('#ffffff', 0.5 * e['wet']))
    c.restore()


def hand(c, x, y, ang, s, curl=0.5, skin='#d6a387', sleeve=None, spread=0.0, child=False):
    """Hand pointing along ang (deg). s = palm length."""
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    if sleeve:
        c.drawRect(skia.Rect.MakeLTRB(-s * 4, -s * 0.62, -s * 0.55, s * 0.62), P(sleeve))
        c.drawRect(skia.Rect.MakeLTRB(-s * 0.75, -s * 0.66, -s * 0.5, s * 0.66), P(mixh(sleeve, '#000000', 0.3)))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-s * 0.6, -s * 0.38, s * 0.45, s * 0.38), s * 0.3, s * 0.3), P(skin))
    fw = s * 0.17 if not child else s * 0.2
    for k in range(4):
        off = (-0.27 + k * 0.18 + (k - 1.5) * spread * 0.1) * s
        L1 = s * (0.42 if k in (1, 2) else 0.36)
        a1 = math.radians((k - 1.5) * spread * 12 + curl * 50)
        p0 = (s * 0.4, off)
        p1 = (p0[0] + math.cos(a1) * L1, p0[1] + math.sin(a1) * L1)
        a2 = a1 + math.radians(curl * 60)
        p2 = (p1[0] + math.cos(a2) * L1 * 0.8, p1[1] + math.sin(a2) * L1 * 0.8)
        c.drawLine(*p0, *p1, P(mixh(skin, '#000000', 0.08 * k), w=fw))
        c.drawLine(*p1, *p2, P(mixh(skin, '#000000', 0.08 * k), w=fw * 0.9))
        c.drawCircle(*p1, fw * 0.25, P('#000000', 0.12))
    ta = math.radians(-60 - spread * 20 + curl * 40)
    t0 = (s * 0.0, -s * 0.32)
    t1 = (t0[0] + math.cos(ta) * s * 0.4, t0[1] + math.sin(ta) * s * 0.4)
    t2 = (t1[0] + math.cos(ta + 0.6) * s * 0.3, t1[1] + math.sin(ta + 0.6) * s * 0.3)
    c.drawLine(*t0, *t1, P(skin, w=fw * 1.1))
    c.drawLine(*t1, *t2, P(skin, w=fw))
    c.restore()
