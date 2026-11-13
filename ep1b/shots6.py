"""Shots part 6 (v2 rig): lamps out, escape, courtyard double, head turn, rooftop."""
from shots3 import *
from shots1 import lamp_intensity

CY = 1560
RUNP = dict(A=128, D=0.54, L=96, rho=0.87, Tc=0.24, lean=0.15, arm=1.25, Sx=12)


def run_fq(v): return (v / HS) * RUNP['D'] / (2 * RUNP['A'])


def talk(T, a, b, f=9.0):
    return abs(math.sin(T * f)) * (1.0 if a < T < b else 0.0)


# ---------------------------------------------------------------- F: lamps out (53.7 - 58.7), front view
def shot_F(fr, T):
    t = T
    P = Persp()
    cam = -400 + 120 * sstep((T - 53.7) / 5.0)
    lamps = P.draw(fr.ga, fr.ge, cam_z=cam, lamp_state=lambda k: lamp_intensity(k, T))
    cam_shake(fr, t, 1.8, 1.0 + 0.06 * sstep((T - 55.5) / 3.2))
    add_lamps(fr, lamps)
    e = C.blend('worried', 'scared', sstep((T - 54.5) / 2.0))
    if T > 56.4: e = C.blend(e, 'terror', sstep((T - 57.8) / 0.9))
    e = eyes_alive(e, t, 3, 0.4)
    p = idle(t, e, seed=4, yaw=0.0)
    look = 0.9 * math.sin((T - 53.7) * 1.3) * (1 - 0.5 * sstep((T - 57) / 1.0))
    p.head_yaw = look
    p.yaw = 0.25 * look
    p.blink = blink_at(t, 3)
    p.lean = 0.02 + 0.06 * sstep((T - 57) / 1.5)
    p.hand[1] = (120, 560, 60); p.hand[-1] = (-120, 560, 60)
    hero2(fr, 540, GROUND + 10, 0.95, p, occ=False)
    return finish_kw(fog=0.30, fog_y=0.45, t=t, amb=tuple(c * (0.78 + 0.22 * (1 - sstep((T - 56.0) / 2.5))) for c in AMB))


# ---------------------------------------------------------------- G: run (58.7 - 63.3), side view
def vg(T): return klin(T, [(58.7, 0), (59.0, 0), (59.9, 640), (63.4, 640)])


def shot_G(fr, T):
    t = T
    camx = 300 + integ('vgx', vg, 58.7, T)
    lamps = flat_street(fr.ga, fr.ge, camx, lamp_fn=lambda k: 0.0)
    cam_shake(fr, t, 1.8 * (1 + 0.8 * sstep((T - 59.3) / 0.6)))
    add_lamps(fr, lamps)
    v = vg(T)
    e = C.blend('scared', 'terror', sstep((T - 59.1) / 0.5))
    e = eyes_alive(e, t, 5, 0.3)
    ph = integ('phg', lambda x: run_fq(vg(x)), 58.7, T)
    k = sstep(v / 160.0)
    stand = idle(t, e, seed=2, yaw=0)
    stand.foot[1] = (HW(1), C.ANKLE, 40); stand.foot[-1] = (-HW(1), C.ANKLE, -30)
    stand.lean = 0.03 - 0.15 * sstep((T - 58.9) / 0.3)
    stand.hand[1] = (100, 560, 40); stand.hand[-1] = (-100, 560, 40)
    p = blend_pose(stand, gait(ph, **RUNP), k)
    p.yaw = math.pi / 2; p.e = e; p.blink = 0.0
    p.head_yaw = -0.6 * (1 - k) * sstep((T - 58.7) / 0.2)
    hx = 600
    hero2(fr, hx, GROUND - 14, HS, p, occ=True)
    gp = 520 - 330 * sstep((T - 59.3) / 3.5)
    cph = integ('cphg', lambda x: (max(vg(x), 90) / 0.72) * 0.64 / (2 * 190.0), 58.7, T)
    cp = E.creature_walk(cph)
    cp.yaw = math.pi / 2
    cp.lean = 0.45
    cp.neck_pitch = 0.2
    creature2(fr, hx - gp - 60, GROUND - 6, 0.72, cp, eyes=1.0)
    return finish_kw(fog=0.24, fog_y=0.6, t=t, amb=tuple(c * 0.9 for c in AMB))


# ---------------------------------------------------------------- courtyard helpers
CAMX = -420
DX = 760


def dbl_pose(t, T, e, yaw, hands=None):
    p = idle(t, e, seed=7, yaw=0)
    p.yaw = yaw
    p.black_eyes = T > 71.8 or T < 66.3 - 99
    return p


# ---------------------------------------------------------------- H: crash (63.3 - 66.3)
def shot_H(fr, T):
    t = T
    lamps = courtyard(fr.ga, fr.ge, CAMX)
    add_lamps(fr, lamps)
    cam_shake(fr, t, 1.6)
    FACE = math.pi / 2
    # double stands with his back to the runner, turns around only after the crash
    turn = sstep((T - 65.5) / 0.9)
    ed = C.blend('neutral', 'serious', 0.5)
    pd = idle(t, ed, seed=7, yaw=0)
    pd.yaw = FACE + (-math.pi) * turn
    pd.head_yaw = 0.0
    pd.black_eyes = False
    C.draw_hero(fr.go, DX, CY, HS, pd, double=True) if False else None
    hit = 64.9
    sw = (math.exp(-(T - hit) * 3) * math.sin((T - hit) * 18) * 0.04) if T > hit else 0
    pd.lean = 0.03 + 0.08 * (1 - sstep((T - hit - 0.1) / 0.4)) * (T > hit)
    pd.sway = 0.6 * sw * 20
    C.draw_hero(fr.ga, DX, CY, HS, pd, double=True)
    fr.ge.mask = True; C.draw_hero(fr.ge, DX, CY, HS, pd, double=True); fr.ge.mask = False
    # runner
    if T < hit:
        xh = -160 + 470 * (T - 63.3) / 1.0
        ph = integ('phh', lambda x: run_fq(470), 63.3, T)
        e = C.blend('scared', 'terror', 0.8)
        p = gait(ph, **RUNP); p.e = e; p.blink = 0.0
        p.yaw = math.pi / 2
    else:
        k = T - hit
        xh = 590 - 90 * sstep(k / 0.7)
        e = C.blend('shock', 'pain', sstep(k / 0.3))
        if T > 65.3: e = C.blend(e, 'shock', sstep((T - 65.3) / 0.5))
        p = idle(t, e, seed=2, yaw=0)
        rec = math.exp(-k * 4) * math.sin(min(k, 0.6) * 5.2)
        p.yaw = math.pi / 2
        p.lean = -0.18 * rec + 0.03
        p.foot[1] = (HW(1), C.ANKLE, 70); p.foot[-1] = (-HW(1), C.ANKLE, -40)
        p.hand[1] = (110, 640, 70); p.hand[-1] = (-110, 560, 20)
        p.head_pitch = 0.0
        p.head_yaw = 0.0
        p.e = e; p.blink = blink_at(t, 2)
        p.head_pitch = -0.35 * sstep((T - 65.4) / 0.5)   # looks up
    hero2(fr, xh, CY, HS, p, occ=True)
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
        z = 1.35 + 0.15 * sstep((T - 77) / 5); cxp, cyp = 590, 1230
    else:
        z = 1.5 + 0.2 * sstep((T - 85.3) / 2.0) - 0.5 * sstep((T - 90.2) / 2.0); cxp, cyp = 600, 1230
    cam_shake(fr, t, 1.4 + (2.0 if T > 81.5 else 0))
    fr.cam(fr.cam_x if hasattr(fr, 'cam_x') else 0, 0, 1.0) if False else None
    zx, zy = -z * (cxp - 540), -z * (cyp - 960)
    fr.cam(zx + 1.4 * math.sin(3 * t), zy + 1.4 * math.sin(2.3 * t), z)
    FACE_R, FACE_L = math.pi / 2, -math.pi / 2
    grab = sstep((T - 74.9) / 0.5) * (1 - sstep((T - 90.0) / 0.5))
    struggle = sstep((T - 81.5) / 0.3) * (1 - sstep((T - 90.0) / 0.3))
    shake = struggle * math.sin(T * 14) * 18
    # ---- double
    shown = sstep((T - 66.3) / 0.5)
    ed = C.blend('serious', 'neutral', 0.5)
    if T > 85.3: ed = C.blend(ed, 'terror', sstep((T - 85.3) / 0.6))
    if T > 90.1: ed = C.blend(ed, 'shock', 0.5)
    ed = eyes_alive(ed, t, 7, 0.2)
    pd = idle(t, ed, seed=7, yaw=0)
    pd.yaw = FACE_L
    pd.black_eyes = T > 71.8
    pd.lean = 0.03 + 0.10 * grab
    dxp = DXX + 30 * grab - 80 * sstep((T - 90.2) / 0.8)
    pd.hand[1] = (60 + 0 * grab, 640 - 70 * grab, 220 * grab + 40 * (1 - grab))
    pd.hand[-1] = (-60, 640 - 70 * grab, 220 * grab + 40 * (1 - grab))
    pd.mouth_talk = talk(T, 74.9, 77.5) + talk(T, 77.7, 81.2) + talk(T, 81.4, 82.2, 0) * 0
    if T > 81.5:
        pd.head_yaw = -0.8 * sstep((T - 81.8) / 0.6)
    pd.sway = 0.2 * math.sin(T * 1.1)
    if T > 86.7: pd.shoulder_up = 0.4
    C.draw_hero(fr.ga, dxp, CY, HS, pd, double=True)
    fr.ge.mask = True; C.draw_hero(fr.ge, dxp, CY, HS, pd, double=True); fr.ge.mask = False
    # ---- hero
    e = C.blend('shock', 'scared', sstep((T - 67.5) / 1.5))
    if T > 71.8: e = C.blend(e, 'terror', 0.6 * sstep((T - 71.8) / 1.0))
    if T > 90.0: e = C.blend(e, 'terror', 0.5)
    e = eyes_alive(e, t, 2, 0.4)
    p = idle(t, e, seed=2, yaw=0)
    p.yaw = FACE_R
    p.lean = -0.04 - 0.08 * grab
    p.head_pitch = -0.3 * (1 - sstep((T - 67.2) / 0.8)) - 0.0
    p.head_yaw = 0.0
    if T > 81.5: p.head_yaw = 0.0
    p.roll = 0.05 * struggle * math.sin(T * 14)
    p.hand[1] = (110, 560, 50 + 50 * struggle * math.sin(T * 14)); p.hand[-1] = (-110, 560, 30)
    p.e = e; p.blink = blink_at(t, 2)
    hxp = HX - 18 * grab - shake
    hxp -= 70 * sstep((T - 90.4) / 0.6)
    p.foot[1] = (HW(1), C.ANKLE, 30); p.foot[-1] = (-HW(1), C.ANKLE, -40)
    hero2(fr, hxp, CY, HS, p, occ=True)
    return finish_kw(fog=0.2, fog_y=0.62, t=t, amb=tuple(c * (1.0 - 0.1 * struggle) for c in AMB))


# ---------------------------------------------------------------- K: head turn (93.0 - 95.2)
def shot_K(fr, T):
    t = T
    lamps = courtyard(fr.ga, fr.ge, CAMX, lamp_state=0.5)
    add_lamps(fr, lamps)
    k = sstep((T - 93.0) / 1.9)
    zoom = 1.25 + 0.25 * k
    fr.cam(-zoom * (560 - 540) + 2 * math.sin(3 * t), -zoom * (1150 - 960), zoom)
    e = C.blend('scared', 'terror', k)
    e = eyes_alive(e, t, 2, 0.2)
    p = idle(t, e, seed=2, yaw=0)
    p.yaw = math.pi / 2 - 1.25 * k
    p.head_yaw = 0.0
    p.lean = -0.03 + 0.02 * k
    p.hand[1] = (110, 560, 30); p.hand[-1] = (-110, 560, 30)
    p.e = e; p.blink = 0.0
    hero2(fr, 560, CY, HS, p, occ=False)
    return finish_kw(fog=0.2, fog_y=0.62, t=t)


# ---------------------------------------------------------------- L: rooftop (95.2 - 105.5)
def shot_L(fr, T):
    t = T
    roof = 520 + 1180 * sstep((T - 95.2) / 2.8)
    tower(fr.ga, fr.ge, roof, lit=0.2)
    cam_shake(fr, t, 1.5)
    bend = sstep((T - 99.0) / 2.6)
    cp = E.CPose()
    cp.yaw = 0.0
    cp.lean = 0.10 + 0.55 * bend
    cp.neck_pitch = 0.25 + 0.7 * bend
    cp.head_roll = 0.2 * math.sin(t * 0.8) + 0.35 * bend
    cp.sway = 0.2 * math.sin(t * 1.1)
    cp.curl = 0.4 + 0.3 * bend
    cp.mouth = 0.55 * talk(T, 102.9, 105.2, 8.0)
    cp.hand[1] = None
    eyes = 0.8 + 0.2 * abs(math.sin(T * 7)) * (1 if T > 102.9 else 0)
    creature2(fr, 540 + 40 * bend, roof + 30, 0.95, cp, eyes=eyes)
    fade = 1 - sstep((T - 104.6) / 0.9)
    return finish_kw(fog=0.22, fog_y=0.5, t=t, amb=tuple(c * 0.9 for c in AMB), bright=fade, ent_alpha=1.0)
