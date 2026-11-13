"""Shot library part 1 (0-58.7 s): street, side track, phone, shop window, messages, lamps out."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import *
from char import *
from bg import *
from anim import *

AMB = (0.30, 0.37, 0.66)
_FD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
_FONTS = {}


def font(sz):
    if sz not in _FONTS: _FONTS[sz] = ImageFont.truetype(_FD, sz)
    return _FONTS[sz]


# ---------------------------------------------------------------- helpers
def zoomf(fr): return float(np.sqrt(abs(np.linalg.det(fr.ga.M[:2, :2]))))


def tp(fr, x, y):
    X, Y = fr.ga.P(x, y); return X / K, Y / K


def add_lamps(fr, lamps, mult=1.0):
    for l in lamps:
        x, y = tp(fr, l[0], l[1]); _, f = tp(fr, l[0], l[3])
        fr.lamps.append((x, y, l[2] * mult, f))
        if l[2] > 0.05:
            fr.glows.append((l[0], l[1], 42 * max((l[3] - l[1]) / 800.0, 0.2) * zoomf(fr), (255, 210, 140), 14 * l[2]))


def add_extra(fr, x, y, sx, sy, c, it):
    X, Y = tp(fr, x, y); z = zoomf(fr)
    fr.extra.append((X, Y, sx * z, sy * z, c, it))


def hero(fr, x, y, s, p, occ=False, tint=None):
    ends = draw_hero(fr.ga, x, y, s, p, tint=tint)
    fr.ge.mask = True; draw_hero(fr.ge, x, y, s, p); fr.ge.mask = False
    if occ: draw_hero(fr.go, x, y, s, p)
    return ends


def entity(fr, x, y, s, eyes=1.0, **st):
    draw_entity(fr.gn, x, y, s, st)
    if eyes > 0.02:
        hx, hy, a = entity_head_pos(x, y, s, st)
        g = fr.ge
        g.push(); g.xf(hx, hy, a)
        H = st.get('tall', 1.0)
        c = st.get('eye_col', (255, 255, 255))
        cc = tuple(int(v * eyes) for v in c)
        if st.get('view', 'front') == 'side':
            fl = st.get('flip', 1)
            g.ell(30 * s * fl, -10 * s * H, 17 * s, 6 * s, cc)
        else:
            g.ell(-24 * s, -10 * s * H, 17 * s, 6 * s, cc); g.ell(24 * s, -10 * s * H, 17 * s, 6 * s, cc)
        g.pop()
        X, Y = tp(fr, hx, hy)


def breathe(t, period=3.4): return math.sin(2 * math.pi * t / period)


def idle_front(t, e, **kw):
    b = breathe(t)
    p = Pose(view='front', e=e, blink=blink_at(t, kw.pop('seed', 0)), breath=b, shoulder_shrug=0.25 * b, bob=2 * b)
    p.sway = 0.2 * math.sin(t * 1.3)
    p.__dict__.update(kw)
    return p


def idle_side(t, e, flip=1, **kw):
    b = breathe(t)
    p = Pose(view='side', flip=flip, e=e, blink=blink_at(t, kw.pop('seed', 0)), breath=b, bob=2 * b, fL=(-40, 0), fR=(46, 0), lean=0.03)
    p.hL = (-6, SH_REL + 292); p.hR = (14, SH_REL + 292)
    p.bendL = 1; p.bendR = 1
    p.__dict__.update(kw)
    return p


_cum = {}
def integ(name, fn, t0, T, dt=1 / 60.0):
    """numeric integral of fn from t0 to T (cached grid)"""
    key = (name, t0)
    if key not in _cum:
        ts = np.arange(t0, t0 + 120, dt)
        vals = np.array([fn(x) for x in ts])
        _cum[key] = (ts, np.concatenate([[0], np.cumsum((vals[1:] + vals[:-1]) * 0.5 * dt)]))
    ts, cs = _cum[key]
    return float(np.interp(T, ts, cs))


def phone_screen(w, h, msgs, t, hdr=True, flash=0.0):
    """msgs: [(text, kind, t_appear)]; drawn at 2x for crisp text"""
    m = 2
    W2, H2 = w * m, h * m
    im = Image.new('RGB', (W2, H2), (12, 17, 30))
    d = ImageDraw.Draw(im)
    if hdr:
        d.rectangle([0, 0, W2, 62 * m], fill=(24, 32, 52))
        d.ellipse([12 * m, 12 * m, 50 * m, 50 * m], fill=(70, 80, 110)); d.text((31 * m, 31 * m), '?', fill=(210, 220, 240), font=font(24 * m), anchor='mm')
        d.text((60 * m, 24 * m), 'Неизвестный номер', fill=(225, 232, 245), font=font(15 * m), anchor='lm')
        d.text((60 * m, 46 * m), 'сейчас', fill=(140, 150, 175), font=font(13 * m), anchor='lm')
    y = 84 * m
    for text, kind, ta in msgs:
        if t < ta: continue
        age = t - ta
        pop = sstep(age / 0.18)
        sz = (19 if kind == 'n' else 20) * m
        lines = []; cur = ''
        for wd in text.split():
            tr = (cur + ' ' + wd).strip()
            if d.textlength(tr, font=font(sz)) > W2 - 60 * m and cur:
                lines.append(cur); cur = wd
            else: cur = tr
        lines.append(cur)
        bh = len(lines) * (sz + 8 * m) + 22 * m
        bw = max(d.textlength(l, font=font(sz)) for l in lines) + 34 * m
        fill = (44, 52, 74) if kind == 'n' else (96, 14, 20)
        tc = (236, 240, 250) if kind == 'n' else (255, 110, 110)
        yy = y + int((1 - pop) * 18 * m)
        d.rounded_rectangle([14 * m, yy, 14 * m + bw, yy + bh], radius=18 * m, fill=fill)
        for i, l in enumerate(lines):
            d.text((14 * m + 17 * m, yy + 12 * m + i * (sz + 8 * m)), l, fill=tc, font=font(sz))
        y += bh + 16 * m
    if flash > 0:
        im = Image.blend(im, Image.new('RGB', (W2, H2), (230, 240, 255)), flash * 0.5)
    return im


def draw_phone_big(fr, root, s, hand, ps, msgs, t, glow=1.0, w=230, h=410, tilt=0.0, hdr=True, flash=0.0, buzz=0.0):
    hx = root[0] + hand[0] * s; hy = root[1] + hand[1] * s
    bx = hx + buzz * math.sin(t * 90) * 3
    by = hy - h * ps * 0.45 + buzz * math.cos(t * 83) * 3
    pw, ph_ = w * ps, h * ps
    g = fr.ga
    g.poly([(bx - pw / 2 - 12, by - ph_ / 2 - 12), (bx + pw / 2 + 12, by - ph_ / 2 - 12), (bx + pw / 2 + 12, by + ph_ / 2 + 12), (bx - pw / 2 - 12, by + ph_ / 2 + 12)], (22, 22, 28), (8, 8, 12), 4)
    scr = phone_screen(w, h, msgs, t, hdr, flash)
    fr.flush()
    z = zoomf(fr)
    sw, sh = max(2, int(pw * z * K)), max(2, int(ph_ * z * K))
    X, Y = fr.ga.P(bx - pw / 2, by - ph_ / 2)
    arr = np.asarray(scr.resize((sw, sh), Image.BILINEAR), np.float32) * (0.5 + 0.6 * glow)
    fr.post.append(lambda img, X=int(X), Y=int(Y), arr=arr: _paste(img, arr, X, Y))
    # fingers over the edges
    skin = SKIN
    g.ell(bx + pw / 2 + 6, by + ph_ * 0.18, 22 * ps / 1.0 * 1.2, 36 * ps * 1.2, skin, tuple(v * .55 for v in skin), 3)
    g.ell(bx - pw / 2 - 6, by + ph_ * 0.08, 20 * ps * 1.2, 30 * ps * 1.2, skin, tuple(v * .55 for v in skin), 3)
    g.ell(bx - pw / 2 - 6, by + ph_ * 0.28, 20 * ps * 1.2, 30 * ps * 1.2, skin, tuple(v * .55 for v in skin), 3)
    add_extra(fr, bx, by, 240, 300, (110, 170, 255), 0.55 * glow)
    return bx, by


def _paste(img, arr, X, Y):
    H_, W_ = img.shape[:2]
    h, w = arr.shape[:2]
    x0, y0 = max(X, 0), max(Y, 0); x1, y1 = min(X + w, W_), min(Y + h, H_)
    if x1 <= x0 or y1 <= y0: return img
    img[y0:y1, x0:x1] = arr[y0 - Y:y1 - Y, x0 - X:x1 - X]
    return img


def finish_kw(**kw):
    d = dict(amb=AMB)
    d.update(kw); return d


# ---------------------------------------------------------------- shot A: front walk (0 - 6.3)
def shot_A(fr, T):
    t = T
    P = Persp()
    cam = -380 * t
    lamps = P.draw(fr.ga, fr.ge, cam_z=cam, lamp_state=lambda k: 1.0)
    fr.cam(3 * math.sin(1.7 * t), 4 * math.sin(2.3 * t) , 1.0 + 0.025 * t / 6.3)
    add_lamps(fr, lamps)
    ph = 2 * math.pi * 1.9 * t
    e = blend_expr(EXPR['neutral'], EXPR['worried'], 0.25 * sstep((t - 2) / 3))
    e['px'] = 0.35 * math.sin(t * 1.6) * (1 if t > 1.5 else 0.2)
    p = walk_front(ph, e=e, blink=blink_at(t))
    hero(fr, 540, 1570, 0.95, p, occ=True)
    # shadow behind: emerges from the fog
    z = 1150 - 38 * t
    ex_ = 540 + 190 * math.sin(0.33 * t + 0.4)
    sc = 0.95 * 349 / z
    ey = 700 + 300 * 1000 / z
    al = 0.78 * sstep((t - 0.6) / 2.4) + 0.22 * sstep((t - 4.2) / 2.0)
    entity(fr, ex_, ey, sc, eyes=al, stride=0.55, phase=ph * 0.9 + 1, tall=1.55)
    fr.post.append(lambda img: img)
    return finish_kw(fog=0.17, fog_y=0.42, ent_alpha=al, t=t, bright=1.0)


# ---------------------------------------------------------------- shot B: side track (6.3 - 17.6)
def vh(T):
    return klin(T, [(6.3, 0), (6.6, 330), (11.8, 330), (12.3, 520), (14.0, 520), (14.6, 0)])


def gap(T):
    return kf(T, [(6.3, 600), (11.4, 340), (13.3, 330), (14.7, 220), (15.84, 190)])


def ve(T):
    dg = (gap(T + 0.02) - gap(T - 0.02)) / 0.04
    return max(0.0, vh(T) - dg)


def shot_B(fr, T):
    t = T
    camx = 300 + integ('vh', vh, 6.3, T)
    lamps = flat_street(fr.ga, fr.ge, camx)
    fr.cam(2 * math.sin(3 * t), 2 * math.sin(2.2 * t), 1.0)
    add_lamps(fr, lamps)
    v = vh(T)
    ph_h = integ('phh', lambda x: 2 * math.pi * vh(x) / 360.0, 6.3, T) * 1.0
    fast = sstep((T - 11.94) / 0.4)
    e = blend_expr(EXPR['neutral'], EXPR['worried'], 0.3 + 0.4 * sstep((T - 11) / 1.2))
    if T > 14.3: e = blend_expr(e, EXPR['scared'], sstep((T - 14.3) / 0.4))
    e['px'] = 0.3
    if v > 20:
        p = walk_side(ph_h, A=95 + 22 * fast, lift=62 + 20 * fast, e=e, blink=blink_at(t), lean=0.04 + 0.06 * fast, arm=1 + 0.3 * fast)
    else:
        p = idle_side(t, e, fL=(-40, 0), fR=(56, 0))
        k = sstep((T - 14.6) / 0.25)
        if T < 15.2 and T > 14.3:
            p.lean = 0.04 - 0.12 * math.sin(min(1, (T - 14.6) / 0.5) * math.pi) * (T > 14.6)
    # screech-to-stop recoil
    hx, hy = 570, 1545
    hero(fr, hx, hy, 0.95, p, occ=True)
    # entity behind
    g_ = gap(T)
    ph_e = integ('phe', lambda x: math.pi * ve(x) / 260.0, 6.3, T)
    stride = sstep(ve(T) / 120.0) * (1 if T < 15.84 else sstep(1 - (T - 15.84) / 0.35))
    amp_e = 1.0 * min(1.3, 0.6 + ve(T) / 400.0)
    ex_ = hx - g_ - 40
    sw = 0.05 * math.sin(t * 1.1) if T > 15.84 else 0
    ht = 0.07 * math.sin(t * 0.9) + (0.22 * sstep((T - 16.2) / 1.2) if T > 15.84 else 0)
    entity(fr, ex_, 1560, 0.82, view='side', flip=1, phase=ph_e, stride=amp_e * stride, tall=1.5, lean=0.06 + 0.1 * fast, head_tilt=ht, sway=sw)
    return finish_kw(fog=0.22, fog_y=0.6, t=t)


# ---------------------------------------------------------------- shot C: phone #1 (17.6 - 24.6)
def shot_C(fr, T):
    t = T
    camx = 700
    lamps = flat_street(fr.ga, fr.ge, camx)
    fr.cam(1.5 * math.sin(2.5 * t), 1.5 * math.cos(2.0 * t), 1.0 + 0.04 * (T - 17.6) / 7.0, cx=540, cy=900)
    add_lamps(fr, lamps)
    # shadow standing in the distance behind his shoulder
    entity(fr, 190, 1560, 0.70, view='front', phase=0, stride=0, tall=1.5, head_tilt=0.12 * sstep((T - 18) / 3) + 0.03 * math.sin(t), lean=0.0, sway=0.1)
    # hero medium shot
    root = (540, 1900); s = 1.72
    buzz = 1.0 if (17.6 <= T < 19.0) else 0.0
    # hand: pocket -> chest
    hand = kf(T, [(17.6, (118, -330)), (18.5, (118, -330)), (19.15, (84, -430)), (22.9, (86, -434)), (23.6, (96, -380))])
    e0 = EXPR['worried']
    e = blend_expr(EXPR['neutral'], e0, sstep((T - 17.6) / 0.5))
    look_down = sstep((T - 19.3) / 0.3) * (1 - sstep((T - 22.88) / 0.15))
    e['py'] = 0.9 * look_down - 0.3 * sstep((T - 22.9) / 0.1)
    e['px'] = -0.3 * look_down
    if T > 21.22:
        e = blend_expr(e, EXPR['scared'], sstep((T - 21.3) / 0.5)); e['py'] = 0.9 * look_down
    if T > 22.88:
        e = blend_expr(e, EXPR['terror'], sstep((T - 22.88) / 0.25)); e['py'] = -0.2; e['px'] = 0.0
    p = idle_front(t, e, hR=hand, bendR=-1, bendL=1)
    p.hL = (-126, SH_REL + 292 + 8 * math.sin(t))
    p.nod = 22 * look_down - 8 * sstep((T - 22.88) / 0.15)
    p.tilt = -0.05 * look_down
    if buzz: root = (root[0] + 2.5 * math.sin(T * 75), root[1] + 1.5 * math.cos(T * 61))
    ends = hero(fr, root[0], root[1], s, p, occ=True)
    if T > 18.7:
        msgs = []
        if T > 19.4: pass
        msgs.append(('НЕ ОБОРАЧИВАЙСЯ', 'red', 21.22))
        flash = max(0, 1 - (T - 21.22) / 0.35) if T > 21.22 else 0
        hb = kf(T, [(18.7, hand), (22.9, hand)])
        draw_phone_big(fr, root, s, hand, 1.25, msgs, T, glow=1.0, hdr=True, flash=flash, buzz=0)
    return finish_kw(fog=0.18, fog_y=0.6, t=t, ent_alpha=1.0, bright=1.0)


# ---------------------------------------------------------------- shot D: shop window (24.6 - 44.9)
WIN = (400, 560, 1040, 1450)


def shot_D(fr, T):
    t = T
    gy = 1500
    zoom = 1.0 + 0.30 * sstep((T - 32.5) / 3.5) - 0.12 * sstep((T - 43.1) / 1.2)
    fr.cam(2 * math.sin(2 * t), 2 * math.cos(1.6 * t), zoom, cx=760, cy=1000)
    shop_front(fr.ga, fr.ge, gy)
    # ground
    g = fr.ga
    g.poly([(0, gy - 130), (1080, gy - 130), (1080, gy + 90), (0, gy + 90)], (78, 80, 104))
    g.poly([(0, gy - 130), (1080, gy - 130), (1080, gy - 110), (0, gy - 110)], (100, 102, 128))
    g.poly([(0, gy + 90), (1080, gy + 90), (1080, gy + 120), (0, gy + 120)], (44, 46, 62))
    g.poly([(0, gy + 120), (1080, gy + 120), (1080, 1920), (0, 1920)], (60, 64, 86))
    draw_shop_window(g, fr.ge, WIN, 0.8)
    # reflection hero (front view) inside glass
    appear = sstep((T - 25.3) / 0.8)
    # hero (profile) position
    if T < 26.4:
        hx = kf(T, [(24.6, -60), (26.2, 320)])
        walking = T < 26.0
    elif T < 43.16:
        hx = 320; walking = False
    else:
        hx = kf(T, [(43.16, 320), (43.5, 210), (44.9, 170)])
        walking = False
    ph = integ('shw', lambda x: 2 * math.pi * 1.7 * (1 - sstep((x - 25.4) / 0.9)), 24.6, T)
    eh = EXPR['neutral']
    if T < 26.4: e = blend_expr(EXPR['neutral'], EXPR['worried'], sstep((T - 24.6) / 1.6))
    else: e = EXPR['worried']
    if T > 29.26: e = blend_expr(EXPR['worried'], EXPR['relief'], sstep((T - 29.26) / 0.6))
    if T > 30.56: e = blend_expr(EXPR['relief'], EXPR['worried'], sstep((T - 30.9) / 0.8))
    if T > 35.68: e = blend_expr(e, EXPR['scared'], 0.6 * sstep((T - 36.5) / 1.5))
    if T > 43.16: e = blend_expr(e, EXPR['terror'], sstep((T - 43.16) / 0.2))
    e = dict(e); e['px'] = 0.7 if T < 43 else 0.0
    if walking:
        p = walk_side(ph, e=e, blink=blink_at(t))
    else:
        p = idle_side(t, e, fL=(-60, 0), fR=(52, 0))
    shrug = 0.9 * (1 - sstep((T - 29.26) / 0.5)) if T > 26.4 else 0.0
    if 26.4 < T < 29.26: p.shoulder_shrug = 1.0
    elif T >= 29.26: p.shoulder_shrug = max(-0.4, 1.0 - 1.4 * sstep((T - 29.26) / 0.7))
    # head tilt at 35.68 .. returns slowly
    p.tilt = 0.30 * sstep((T - 35.7) / 1.4) * (1 - sstep((T - 43.1) / 0.3))
    if T >= 43.16:
        u = sstep((T - 43.16) / 0.35)
        p.lean = -0.28 * u; p.hL = (-30, SH_REL + 80); p.hR = (60, SH_REL + 60); p.bendL = 1; p.bendR = 1
        p.fL = (-110, 0); p.fR = (-10, -40)
        p.nod = 0
        p.blink = 0
    hero(fr, hx, 1535, 1.02, p)
    # breath puff on exhale
    if 29.2 < T < 31.0:
        for i in range(7):
            u = (T - 29.26 - i * 0.07)
            if u < 0: continue
            a = int(160 * max(0, 1 - u / 1.5))
            fr.ga.ell(hx + 190 + u * 130 + i * 8, 1535 - 760 - u * 70, 22 + u * 38, 16 + u * 26, (225, 232, 245), a=a)
    # reflection
    rx, ry, rs = 720, 1440, 0.88
    re = EXPR['neutral']
    re = blend_expr(EXPR['worried'], EXPR['neutral'], 0.4)
    gaze = -0.8 if T < 33 else -0.8 * (1 - sstep((T - 33) / 1.0))
    re = dict(re); re['px'] = gaze; re['eye'] = 1.0
    if T > 36.5: re = blend_expr(re, EXPR['shh'], sstep((T - 38.5) / 0.8))
    if T > 44.0: re = blend_expr(re, EXPR['neutral'], sstep((T - 44.0) / 0.8))
    mimic = T < 27.5
    if mimic:
        rp = walk_front(ph + math.pi * 0.0, e=re, amp=1.0 - sstep((T - 25.4) / 0.9))
    else:
        rp = idle_front(t * 0.0 + 26.0, re)   # frozen: does not breathe/exhale
        rp.breath = 0.0; rp.shoulder_shrug = 1.0 if T < 29.26 else (0.9)
    # independent finger-to-lips raise
    fl = sstep((T - 38.54) / 1.5)
    if fl > 0 and T < 44.8:
        mouth = (4, -614)
        rp.hR = (mouth[0] + 30 * (1 - fl) + 4, kf(T, [(38.54, SH_REL + 292), (40.1, -560)]))
        rp.hR = (kf(T, [(38.54, 126), (40.1, 38)]), kf(T, [(38.54, SH_REL + 292), (40.1, -566), (41.5, -612)]))
        rp.bendR = -1
        rp.finger_lips = True
        rp.e = dict(re)
    if T > 44.0:
        d = sstep((T - 44.0) / 0.7)
        rp.hR = (kf(T, [(44.0, 38), (44.9, 100)]), kf(T, [(44.0, -612), (44.9, SH_REL + 280)]))
    if mimic is False and T < 38.54:
        rp.blink = 0.0
    # draw reflection with cool tint and soft alpha via tint
    tintc = (0.78, 0.93, 1.15)
    rends = hero(fr, rx, ry, rs, rp, tint=tintc) if appear > 0.02 else None
    if appear > 0.02 and fl > 0 and T < 44.8:
        # raised index finger drawn over the lips
        g.push()
        g.line([(rx + 8 * rs, ry - 600 * rs), (rx + 8 * rs, ry - 690 * rs)], (240, 205, 196), 22 * rs)
        g.ell(rx + 8 * rs, ry - 694 * rs, 12 * rs, 14 * rs, (243, 214, 205))
        g.pop()
    # glass: gloss streaks & dim to simulate reflection
    x0, y0, x1, y1 = WIN
    g.poly([(x0, y0), (x0 + 130, y0), (x0 + 330, y1), (x0 + 200, y1)], (200, 215, 255), a=22)
    g.poly([(x0 + 330, y0), (x0 + 380, y0), (x0 + 570, y1), (x0 + 520, y1)], (200, 215, 255), a=16)
    if appear < 1:
        pass
    # lights
    bp = lamp_post(fr.ga, fr.ge, 900, gy + 40, 800, 1.0)
    add_lamps(fr, [(bp[0], bp[1], 0.9, gy + 40)])
    add_extra(fr, 700, 1100, 520, 480, (255, 170, 100), 0.45)
    # camera zoom toward the reflection as tension grows
    return finish_kw(fog=0.12, fog_y=0.6, t=t, rain=0.8)


# ---------------------------------------------------------------- shot E: second messages (44.9 - 53.7)
def shot_E(fr, T):
    t = T
    camx = 1900
    def lamp_fn(k):
        base = 1.0
        if T > 51.74: return 0.5 + 0.5 * (1 if int(T * 18) % 3 == 0 else 0.0) * (0.3 + 0.7 * abs(math.sin(T * 40)))
        return base
    lamps = flat_street(fr.ga, fr.ge, camx, lamp_fn=lamp_fn)
    fr.cam(1.5 * math.sin(2.7 * t), 1.5 * math.cos(2.1 * t), 1.0 + 0.05 * (T - 44.9) / 8.8, cx=540, cy=900)
    add_lamps(fr, lamps)
    # shadow again behind, closer than before
    entity(fr, 880, 1560, 0.78 + 0.04 * sstep((T - 49) / 4), view='front', stride=0, phase=0, tall=1.5, head_tilt=-0.14, sway=0.0)
    root = (540, 1900); s = 1.72
    msgs = [('НЕ ОБОРАЧИВАЙСЯ', 'red', -1), ('ОН НЕ ЗА ТОБОЙ', 'n', 47.56), ('ОН ВНУТРИ ТЕБЯ', 'red', 51.74)]
    hand = (86, -434)
    buzz = 1.0 if (44.94 <= T < 46.0 or 50.14 <= T < 51.2) else 0.0
    e = EXPR['worried']
    look_down = 1.0
    if T < 47.56: e = blend_expr(EXPR['worried'], EXPR['worried'], 0)
    if T >= 47.56: e = blend_expr(EXPR['worried'], EXPR['shock'], sstep((T - 47.7) / 0.4) * 0.6)
    if T >= 49.02: e = blend_expr(e, EXPR['neutral'], 0.4 * sstep((T - 49.02) / 0.3))
    if T >= 51.74: e = blend_expr(EXPR['worried'], EXPR['terror'], sstep((T - 51.9) / 0.35))
    e = dict(e); e['py'] = 0.85 if T < 51.6 else 0.0
    frozen = 49.02 <= T < 50.14
    p = idle_front(40.0 if frozen else t, e, hR=hand, bendR=-1, bendL=1)
    if frozen: p.blink = 0.0; p.breath = 0.0
    p.hL = (-126, SH_REL + 292)
    p.nod = 20 if T < 51.6 else -10
    if T >= 51.9: p.nod = -14 + 3 * math.sin(T * 30)
    if buzz: root = (root[0] + 2.5 * math.sin(T * 75), root[1] + 1.5 * math.cos(T * 61))
    if T > 51.74: root = (root[0] + 2.2 * math.sin(T * 41), root[1])
    hero(fr, root[0], root[1], s, p, occ=True)
    draw_phone_big(fr, root, s, hand, 1.25, msgs, T, glow=1.0, hdr=True, buzz=0)
    amb = AMB
    if T > 51.74:
        amb = tuple(c * (0.55 + 0.45 * (1 if int(T * 14) % 2 else 0.3)) for c in AMB)
    return finish_kw(fog=0.18, fog_y=0.6, t=t, amb=amb)


# ---------------------------------------------------------------- shot F: lamps going out (53.7 - 58.7)
LAMP_OFF = {7: 56.26, 4: 56.88, 3: 57.68}


def lamp_intensity(k, T):
    off = LAMP_OFF.get(k, None)
    fl_start = 54.9
    if off is None:
        return 1.0 if T < 56.2 else 1.0
    if T >= off: return 0.0
    if T > off - 0.5:
        return 0.35 + 0.65 * abs(math.sin(T * 47 + k)) * (1 if int(T * 25 + k) % 3 else 0.2)
    if T > fl_start:
        return 1.0 if int((T + k) * 9) % 5 else 0.45
    return 1.0


def shot_F(fr, T):
    t = T
    P = Persp()
    cam = -400 + 230 * sstep((T - 53.7) / 5.0)
    lamps = P.draw(fr.ga, fr.ge, cam_z=cam, lamp_state=lambda k: lamp_intensity(k, T))
    fr.cam(2 * math.sin(1.9 * t), 2 * math.sin(2.7 * t), 1.0)
    add_lamps(fr, lamps)
    zrel = 760 - cam
    s = 0.95 * 349 / zrel
    gy_ = 700 + 300 * 1000 / zrel
    yaw = 0.9 * math.sin((T - 53.7) * 1.5) * (1 - 0.4 * sstep((T - 57) / 1.0))
    e = blend_expr(EXPR['worried'], EXPR['scared'], sstep((T - 55) / 2.5))
    e['px'] = yaw * 0.9
    p = idle_front(t, e, yaw=yaw, tilt=0.06 * yaw)
    p.hL = (-120, SH_REL + 240); p.hR = (120, SH_REL + 240)
    hero(fr, 540, gy_, s, p, occ=False)
    dark = 1 - sstep((T - 56.0) / 2.5) * 0.45
    return finish_kw(fog=0.34, fog_y=0.45, t=t, amb=tuple(c * (0.75 + 0.25 * dark) for c in AMB))
