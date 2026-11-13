"""Shot library part 2 (58.7-108.4 s): escape, courtyard double, rooftop, end card."""
from shots1 import *

CY = 1560
HS = 0.95
SHO = SH_REL * HS


def lerp2(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def zc(fr, px, py, z):
    """camera zoom z centred on world point (px,py)."""
    fr.cam(-z * (px - 540), -z * (py - 960), z)


# ---------------------------------------------------------------- G: run (58.7 - 63.3)
def vg(T): return klin(T, [(58.7, 0), (59.3, 0), (60.1, 640), (63.4, 640)])


def shot_G(fr, T):
    t = T
    camx = 300 + integ('vg', vg, 58.7, T)
    lamps = flat_street(fr.ga, fr.ge, camx, lamp_fn=lambda k: 0.0)
    fr.cam(2.5 * math.sin(3 * t), 3 * math.sin(7 * t) * sstep((T - 59.3) / 0.6), 1.0)
    add_lamps(fr, lamps)
    v = vg(T)
    ph = integ('phg', lambda x: 2 * math.pi * vg(x) / 330.0, 58.7, T)
    e = dict(blend_expr(EXPR['scared'], EXPR['terror'], sstep((T - 59.2) / 0.5)))
    e['px'] = -0.6 if v > 20 else 0.5
    if v > 20:
        p = run_side(ph, e=e, blink=0.0)
        p.nod = 6 * math.sin(ph * 2)
    else:
        p = idle_side(t, e, fL=(-40, 0), fR=(56, 0))
        p.lean = 0.03 - 0.15 * sstep((T - 59.0) / 0.3)
        p.hL = (-30, SH_REL + 230); p.hR = (30, SH_REL + 230)
    hx = 570
    hero(fr, hx, CY, HS, p, occ=True)
    gp = 520 - 320 * sstep((T - 59.3) / 3.5)
    ph_e = integ('phge', lambda x: math.pi * max(vg(x), 60) / 250.0, 58.7, T)
    entity(fr, hx - gp - 40, 1560, 0.82, view='side', flip=1, phase=ph_e, stride=1.3 * sstep(v / 200.0),
           tall=1.5, lean=0.16, head_tilt=0.1, sway=0.0)
    return finish_kw(fog=0.24, fog_y=0.6, t=t, amb=tuple(c * 0.92 for c in AMB))


# ---------------------------------------------------------------- H: courtyard crash (63.3 - 66.3)
DX = 700
CAMX = -420


def shot_H(fr, T):
    t = T
    lamps = courtyard(fr.ga, fr.ge, CAMX)
    add_lamps(fr, lamps)
    fr.cam(2 * math.sin(2 * t), 2 * math.sin(2.9 * t), 1.0)
    ed = blend_expr(EXPR['serious'], EXPR['neutral'], 0.5)
    pd = idle_side(t, ed, flip=-1, seed=3)
    pd.nod = 8
    if T > 64.88: pd.sway = 0.6 * math.sin((T - 64.88) * 18) * math.exp(-(T - 64.88) * 3)
    hero(fr, DX, CY, HS, pd)
    run_t = T < 64.9
    if run_t:
        xh = -160 + 470 * (T - 63.3)
    else:
        xh = 590 - 120 * sstep((T - 64.9) / 0.6)
    ph = integ('phh2', lambda x: 2 * math.pi * 470 / 330.0, 63.3, min(T, 64.9))
    if run_t:
        p = run_side(ph, e=dict(EXPR['terror'], px=-0.5), blink=0.0)
    else:
        k = T - 64.9
        e = blend_expr(EXPR['shock'], EXPR['pain'], sstep(k / 0.3))
        if T > 65.3: e = blend_expr(e, EXPR['shock'], sstep((T - 65.3) / 0.5))
        p = idle_side(t, e, fL=(-60, 0), fR=(70, 0))
        rec = math.exp(-k * 4) * math.sin(min(k, 0.6) * 5.2)
        p.lean = -0.18 * rec + 0.03
        p.hL = (-20, SH_REL + 180); p.hR = (70, SH_REL + 150 + 80 * sstep((T - 65.2) / 0.5))
        p.nod = 22 * (1 - sstep((T - 65.3) / 0.9))
        p.bob = 10 * math.sin(min(k, 1) * 3)
    hero(fr, xh, CY, HS, p, occ=True)
    return finish_kw(fog=0.2, fog_y=0.62, t=t)


# ---------------------------------------------------------------- I: face to face (66.3 - 93.0)
HX, DXX = 470, 700


def shot_I(fr, T):
    t = T
    ls = 1.0 if T < 79 else (0.55 + 0.45 * (int(T * 11) % 3 != 0))
    lamps = courtyard(fr.ga, fr.ge, CAMX, lamp_state=ls)
    add_lamps(fr, lamps)
    if T < 72.0:
        z = 1.0 + 0.10 * sstep((T - 66.3) / 5.7); cxp, cyp = 590, 1240
    elif T < 75.2:
        z = 1.1 + 0.9 * sstep((T - 72.0) / 0.9) - 0.5 * sstep((T - 74.0) / 1.2); cxp, cyp = DXX, 1190
    elif T < 83.0:
        z = 1.35 + 0.15 * sstep((T - 75.3) / 6.0); cxp, cyp = 590, 1200
    else:
        z = 1.5 + 0.55 * sstep((T - 83.2) / 1.2) - 0.3 * sstep((T - 88.0) / 2.0); cxp, cyp = DXX - 20, 1130
    zc(fr, cxp, cyp, z)
    fr.cam(2 * math.sin(1.9 * t) + (4 * math.sin(40 * t) if 75.4 < T < 83 else 0), 2 * math.sin(2.7 * t), 1.0)
    grab = sstep((T - 75.3) / 0.35) * (1 - sstep((T - 90.2) / 0.5))
    ed = EXPR['serious']
    if T >= 72.3: ed = blend_expr(EXPR['serious'], EXPR['neutral'], 0.3)
    if 77.0 <= T < 80.7: ed = blend_expr(ed, EXPR['scared'], 0.4)
    if T >= 83.2: ed = blend_expr(ed, EXPR['scared'], sstep((T - 83.4) / 0.6))
    if T >= 86.0: ed = blend_expr(ed, EXPR['terror'], sstep((T - 86.3) / 1.0))
    ed = dict(ed)
    ed['px'] = (-0.2 if T < 83.2 else 0.9 * sstep((T - 83.2) / 0.3))
    ed['py'] = (0.0 if T < 83.2 else -0.3)
    if 76.6 <= T < 81.2: ed['mo'] = 0.25 + 0.25 * abs(math.sin(T * 9))
    dx = DXX - 70 * grab + (80 * sstep((T - 90.4) / 0.8) if T > 90.2 else 0)
    pd = idle_side(t, ed, flip=-1, seed=5)
    pd.black_eyes = T >= 72.3
    pd.lean = 0.03 + 0.1 * grab
    pd.nod = 6 * grab
    sh = (HX + 20, CY + SHO + 40)
    reachL = (-(HX - dx) / HS + 10, (sh[1] - CY) / HS)
    pd.hL = lerp2((-6, SH_REL + 292), reachL, grab)
    pd.hR = lerp2((14, SH_REL + 292), (reachL[0] - 30, reachL[1] + 10), grab)
    if T >= 83.2: pd.tilt = -0.06 * math.sin(T * 7)
    if T >= 86.0: pd.sway = 0.4 * math.sin(T * 12)
    pd.bob = 4 * grab * math.sin(T * 13) if T > 83 else 0
    hero(fr, dx, CY, HS, pd)
    if T < 66.9: e = blend_expr(EXPR['shock'], EXPR['terror'], sstep((T - 66.4) / 0.5))
    else: e = blend_expr(EXPR['terror'], EXPR['scared'], 0.4)
    if T >= 81.0: e = blend_expr(e, EXPR['terror'], 0.6)
    if T >= 90.8: e = blend_expr(EXPR['scared'], EXPR['worried'], sstep((T - 91.0) / 1.5))
    e = dict(e)
    hxx = HX
    p = idle_side(t, e, fL=(-60, 0), fR=(70, 0), seed=9)
    p.lean = -0.04 - 0.1 * grab
    p.hL = (-20, SH_REL + 200); p.hR = (60, SH_REL + 210)
    if 81.0 <= T < 83.2:
        hxx += 8 * math.sin(T * 26)
        p.lean += 0.08 * math.sin(T * 20)
        p.hL = (-10 + 60 * math.sin(T * 17), SH_REL + 180); p.hR = (80 - 30 * math.sin(T * 17), SH_REL + 160)
    if T >= 92.2:
        p.hL = (-10, SH_REL + 260); p.hR = (30, SH_REL + 270)
    hero(fr, hxx, CY, HS, p, occ=True)
    amb = AMB if T < 72 else tuple(c * 0.92 for c in AMB)
    return finish_kw(fog=0.2, fog_y=0.62, t=t, amb=amb)


# ---------------------------------------------------------------- K: turning head (93.0 - 95.0)
def shot_K(fr, T):
    t = T
    lamps = courtyard(fr.ga, fr.ge, CAMX)
    add_lamps(fr, lamps)
    k = sstep((T - 93.1) / 1.3)
    e = dict(blend_expr(EXPR['worried'], EXPR['terror'], sstep((T - 93.6) / 1.2)))
    e['py'] = -0.8 * sstep((T - 94.2) / 0.6)
    p = idle_front(t, e, yaw=0.9 * k, tilt=0.05 * k)
    p.nod = -12 * sstep((T - 94.2) / 0.6)
    p.hL = (-120, SH_REL + 250); p.hR = (120, SH_REL + 250)
    z = 1.7 + 0.5 * sstep((T - 93.0) / 2.0)
    zc(fr, 540, CY + SHO - 130, z)
    fr.cam(2 * math.sin(2.1 * t), 2 * math.sin(2.9 * t), 1.0)
    hero(fr, 540, CY, 1.15, p, occ=True)
    return finish_kw(fog=0.2, fog_y=0.62, t=t, bright=1.15)


# ---------------------------------------------------------------- L: rooftop (95.0 - 105.7)
def shot_L(fr, T):
    t = T
    roof = 520 + 1180 * sstep((T - 95.0) / 2.6)
    roof += 25 * sstep((T - 98.4) / 1.5)
    lit = 0.2
    lamps = []
    tower(fr.ga, fr.ge, roof, lit=lit)
    fr.cam(2 * math.sin(1.4 * t), 2 * math.sin(2.1 * t), 1.0)
    bend = sstep((T - 99.0) / 0.9)
    tl = 0.12 * math.sin(t * 0.9) + 0.30 * bend
    speak = 100.6 < T < 105.2
    eyes = 1.0 if not speak else 0.75 + 0.25 * abs(math.sin(T * 11))
    sc = 0.78 + 0.1 * bend
    entity(fr, 540 + 60 * bend, roof + 30, sc, eyes=eyes, tall=1.6, lean=0.28 * bend, head_tilt=tl, sway=0.15 * math.sin(t * 1.3),
           stride=0.0, arm_swing=0.0, eye_col=(255, 255, 255) if T < 100.6 else (255, 215, 200))
    fade = 1 - sstep((T - 104.4) / 0.9)
    return finish_kw(fog=0.22, fog_y=0.5, t=t, amb=tuple(c * 0.9 for c in AMB), bright=fade, ent_alpha=1.0)


_old_L = shot_L
def shot_L(fr, T):
    kw = _old_L(fr, T)
    return kw
