"""2D cartoon character rig (front / side / back views) drawn with aggdraw.

All coordinates are design units (1080x1920 canvas); G applies the render scale.
Local character space: feet on y=0, up is negative, x forward = +x (side view).
"""
import math
import numpy as np
import aggdraw
from PIL import Image

SKIN = (243, 214, 205)
SKIN_D = (206, 164, 158)
HAIR = (96, 52, 52)
HAIR_D = (66, 34, 38)
HOOD = (92, 94, 104)
HOOD_D = (58, 60, 70)
HOOD_L = (128, 130, 142)
PANTS = (44, 46, 58)
PANTS_D = (28, 29, 38)
SHOE = (206, 206, 214)
SHOE_D = (150, 150, 162)


def col(c, a=255): return (int(c[0]), int(c[1]), int(c[2]), a)


def mix(a, b, t): return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


class G:
    """Thin aggdraw wrapper with an affine transform stack."""

    def __init__(self, img, k=1.0):
        self.img = img
        self.d = aggdraw.Draw(img)
        self.d.setantialias(True)
        self.k = k
        self.M = np.eye(3)
        self.stack = []
        self.mask = False

    def c(self, c, a=255):
        return (0, 0, 0, a) if self.mask else col(c, a)

    def push(self): self.stack.append(self.M.copy())

    def pop(self): self.M = self.stack.pop()

    def xf(self, tx=0, ty=0, rot=0, sx=1, sy=1):
        c, s = math.cos(rot), math.sin(rot)
        T = np.array([[c * sx, -s * sy, tx], [s * sx, c * sy, ty], [0, 0, 1]])
        self.M = self.M @ T

    def P(self, x, y):
        v = self.M @ np.array([x, y, 1.0])
        return v[0] * self.k, v[1] * self.k

    def flat(self, pts):
        out = []
        for x, y in pts:
            a, b = self.P(x, y); out += [a, b]
        return out

    def poly(self, pts, fill=None, line=None, lw=0, a=255):
        pen = aggdraw.Pen(self.c(line, a), max(lw * self.k, 0.5)) if line is not None and lw > 0 else None
        br = aggdraw.Brush(self.c(fill, a)) if fill is not None else None
        self.d.polygon(self.flat(pts), pen, br) if pen else self.d.polygon(self.flat(pts), br)

    def ell(self, cx, cy, rx, ry, fill=None, line=None, lw=0, a=255, n=28):
        pts = [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
        self.poly(pts, fill, line, lw, a)

    def line(self, pts, color, w, a=255):
        pen = aggdraw.Pen(self.c(color, a), max(w * self.k, 0.6))
        p = aggdraw.Path()
        f = self.flat(pts)
        p.moveto(f[0], f[1])
        for i in range(2, len(f), 2): p.lineto(f[i], f[i + 1])
        self.d.path(p, pen)

    def capsule(self, p0, p1, w, fill, line=None, ow=3, a=255):
        if line is not None:
            self._cap(p0, p1, w + 2 * ow, line, a)
        self._cap(p0, p1, w, fill, a)

    def _cap(self, p0, p1, w, fill, a):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy) or 1e-6
        nx, ny = -dy / L * w / 2, dx / L * w / 2
        self.poly([(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)], fill, a=a)
        self.ell(p0[0], p0[1], w / 2, w / 2, fill, a=a, n=16)
        self.ell(p1[0], p1[1], w / 2, w / 2, fill, a=a, n=16)

    def flush(self): self.d.flush()


def ik(p0, t, l1, l2, bend=1):
    dx, dy = t[0] - p0[0], t[1] - p0[1]
    d = max(min(math.hypot(dx, dy), l1 + l2 - 1e-3), abs(l1 - l2) + 1e-3)
    a = math.atan2(dy, dx)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    ang = a + bend * math.acos(max(-1, min(1, c)))
    j = (p0[0] + l1 * math.cos(ang), p0[1] + l1 * math.sin(ang))
    e = (p0[0] + (t[0] - p0[0]) * min(1, (l1 + l2 - 1e-3) / max(math.hypot(dx, dy), 1e-6)),
         p0[1] + (t[1] - p0[1]) * min(1, (l1 + l2 - 1e-3) / max(math.hypot(dx, dy), 1e-6)))
    return j, e


# ---------------------------------------------------------------- expressions
EXPR = {
    'neutral': dict(eye=1.0, px=0, py=0, brow=0, brin=0, mo=0.0, mw=1.0, mc=0.1),
    'worried': dict(eye=1.1, px=0, py=0, brow=0.4, brin=0.8, mo=0.1, mw=0.9, mc=-0.5),
    'scared': dict(eye=1.35, px=0, py=0, brow=0.8, brin=0.9, mo=0.45, mw=0.9, mc=-0.6),
    'terror': dict(eye=1.5, px=0, py=0, brow=1.0, brin=1.0, mo=0.9, mw=1.0, mc=-0.5),
    'shock': dict(eye=1.45, px=0, py=0, brow=1.0, brin=0.3, mo=0.7, mw=0.6, mc=0.0),
    'serious': dict(eye=0.8, px=0, py=0, brow=-0.2, brin=-0.8, mo=0.0, mw=1.0, mc=-0.25),
    'relief': dict(eye=0.65, px=0, py=0, brow=0.1, brin=0.3, mo=0.35, mw=0.7, mc=0.0),
    'pain': dict(eye=0.45, px=0, py=0, brow=0.2, brin=0.9, mo=0.5, mw=1.2, mc=-0.7),
    'shh': dict(eye=0.85, px=0, py=0, brow=-0.1, brin=-0.4, mo=0.0, mw=0.5, mc=0.3),
}
EXPR_KEYS = ['eye', 'px', 'py', 'brow', 'brin', 'mo', 'mw', 'mc']


def expr(name, **kw):
    e = dict(EXPR[name]); e.update(kw); return e


def blend_expr(a, b, t):
    return {k: a[k] * (1 - t) + b[k] * t for k in EXPR_KEYS}


# ---------------------------------------------------------------- hero rig
class Pose:
    """Pose parameters; defaults give an idle front-facing stance."""

    def __init__(self, **kw):
        self.view = 'front'          # front | side | back
        self.flip = 1                # +1 faces right in side view, -1 left
        self.bob = 0.0               # hips drop (+down)
        self.lean = 0.0              # torso lean rad (+forward)
        self.tilt = 0.0              # head roll rad
        self.nod = 0.0               # head vertical shift
        self.yaw = 0.0               # head turn -1..1 (+ looks to flip direction in front view: +right)
        self.fL = (-52, 0); self.fR = (52, 0)    # feet
        self.zL = 1.0; self.zR = 1.0
        self.liftL = 0.0; self.liftR = 0.0
        self.hL = None; self.hR = None           # hands (local coords); None = relaxed
        self.bendL = 1; self.bendR = -1
        self.e = EXPR['neutral']
        self.blink = 0.0             # 0 open .. 1 closed
        self.breath = 0.0
        self.phone = None            # None | (screen_text, glow)
        self.phone_hand = 'R'
        self.sway = 0.0              # hair/drawstring lag
        self.black_eyes = False
        self.hand_open = False
        self.shoulder_shrug = 0.0
        self.finger_lips = False
        self.__dict__.update(kw)


HIP_H = 405
THIGH = 195
SHIN = 195
TORSO = 275
UARM = 150
FARM = 150
HEAD_R = 118


def draw_hero(g, x, y, s, p, tint=None, double=False):
    """Draw the hero at ground position (x, y), scale s."""
    g.push()
    g.xf(x, y, 0, s * (p.flip if p.view == 'side' else 1), s)
    skin, hair, hood, pants, shoe = SKIN, HAIR, HOOD, PANTS, SHOE
    if tint is not None:
        skin, hair, hood, pants, shoe = [tuple(c[i] * tint[i] for i in range(3)) for c in (skin, hair, hood, pants, shoe)]
    ol = lambda c: tuple(v * 0.55 for v in c)
    hip = (0, -HIP_H + p.bob)
    sh_off = TORSO
    c, sn = math.cos(p.lean), math.sin(p.lean)
    sho = (hip[0] + sn * (sh_off - 52), hip[1] - c * (sh_off - 52) + p.shoulder_shrug * -10)
    side = p.view == 'side'
    front = p.view == 'front'
    # ---- legs
    legs = []
    for sgn, f, z, lift in ((-1, p.fL, p.zL, p.liftL), (1, p.fR, p.zR, p.liftR)):
        hp_ = (hip[0] + (0 if side else sgn * 40), hip[1])
        tgt = (f[0], f[1] - lift)
        kn, an = ik(hp_, tgt, THIGH, SHIN, bend=(-1 if side else 1))
        legs.append((sgn, hp_, kn, an, z))
    order = legs if not side else sorted(legs, key=lambda L: -L[0] * 0 + (0 if L[0] < 0 else 1))
    far, near = (legs[0], legs[1]) if side else (None, None)
    def leg(L, dark):
        sgn, hp_, kn, an, z = L
        pc = mix(pants, (0, 0, 0), 0.25) if dark else pants
        g.capsule(hp_, kn, 78, pc, ol(pc), 3)
        g.capsule(kn, an, 70, pc, ol(pc), 3)
        sc = mix(shoe, (0, 0, 0), 0.25) if dark else shoe
        if side:
            g.poly([(an[0] - 38, an[1] - 8), (an[0] + 30, an[1] - 14), (an[0] + 92, an[1] + 14), (an[0] + 92, an[1] + 30),
                    (an[0] - 40, an[1] + 30)], sc, ol(sc), 3)
            g.poly([(an[0] - 40, an[1] + 22), (an[0] + 92, an[1] + 22), (an[0] + 92, an[1] + 32), (an[0] - 40, an[1] + 32)], mix(sc, (60, 60, 70), .5))
        else:
            g.ell(an[0] + sgn * 4, an[1] + 12, 52 * z, 30 * z, sc, ol(sc), 3)
            g.ell(an[0] + sgn * 4, an[1] + 26, 52 * z, 8 * z, mix(sc, (60, 60, 70), .5))
    if side:
        leg(legs[0], True)  # far leg first
    else:
        for L in legs: leg(L, False)
    # ---- arms helper
    def arm_pts(sgn, hand, bend):
        sx = sho[0] + (0 if side else sgn * 112); sy = sho[1] + 22
        if hand is None:
            hand = (sx + (sgn * 10 if not side else 8), sy + UARM + FARM - 6)
        j, e = ik((sx, sy), hand, UARM, FARM, bend)
        return (sx, sy), j, e
    def draw_arm(sgn, hand, bend, dark):
        s0, j, e = arm_pts(sgn, hand, bend)
        hc = mix(hood, (0, 0, 0), 0.3) if dark else hood
        g.capsule(s0, j, 66, hc, ol(hc), 3)
        g.capsule(j, e, 58, hc, ol(hc), 3)
        sk = mix(skin, (0, 0, 0), 0.2) if dark else skin
        g.ell(e[0], e[1] + 6, 31, 33, sk, ol(sk), 3)
        # cuff
        g.ell(e[0] * .85 + j[0] * .15, e[1] * .85 + j[1] * .15, 33, 22, mix(hc, (0, 0, 0), .15))
        return e
    # far arm (side) before torso
    ends = {}
    if side:
        ends['far'] = draw_arm(-1, p.hL, p.bendL, True)
    # ---- torso
    g.push()
    g.xf(hip[0], hip[1], p.lean)
    br = p.breath * 6
    if side:
        g.poly([(-62, 6), (-84, -90), (-80, -TORSO + 30 - br), (-40, -TORSO - 8 - br), (56, -TORSO + 4 - br), (76, -150), (68, 14)], hood, ol(hood), 4)
        g.poly([(-40, -TORSO - 8), (-96, -TORSO + 40), (-100, -TORSO - 6), (-60, -TORSO - 34)], hood_d := mix(hood, (0, 0, 0), .35), ol(hood), 3)  # hood bulge
        g.poly([(-50, -80), (60, -76), (62, -20), (-48, -16)], mix(hood, (255, 255, 255), .06))
    else:
        g.poly([(-100, 8), (-116, -110), (-124, -TORSO + 52 - br), (-96, -TORSO + 6 - br), (-40, -TORSO - 10 - br), (40, -TORSO - 10 - br), (96, -TORSO + 6 - br),
                (124, -TORSO + 52 - br), (116, -110), (100, 8)], hood, ol(hood), 4)
        if front:
            g.poly([(-60, -126), (60, -126), (74, -26), (-74, -26)], mix(hood, (255, 255, 255), .05), ol(hood), 3)  # pocket
            g.line([(-52, -126), (-70, -44)], ol(hood), 3); g.line([(52, -126), (70, -44)], ol(hood), 3)
            g.ell(0, -TORSO + 8 - br, 64, 34, mix(hood, (0, 0, 0), .45), ol(hood), 3)  # collar
            g.ell(0, -TORSO + 14 - br, 40, 22, mix(skin, (0, 0, 0), .15))
            # drawstrings
            sw = p.sway * 14
            g.line([(-20, -TORSO + 30), (-24 + sw, -TORSO + 100)], HOOD_L, 5)
            g.line([(20, -TORSO + 30), (24 + sw, -TORSO + 100)], HOOD_L, 5)
        else:
            g.ell(0, -TORSO + 2 - br, 100, 54, mix(hood, (0, 0, 0), .35), ol(hood), 3)  # hood back
            g.line([(0, -TORSO + 40), (0, -20)], ol(hood), 3)
    g.pop()
    # ---- head
    neck = (hip[0] + sn * (TORSO + 12), hip[1] - c * (TORSO + 12) + p.shoulder_shrug * -10)
    g.push()
    g.xf(neck[0], neck[1] + p.nod, p.tilt + p.lean * 0.4)
    g.xf(0, -66)
    g.ell(0, 96, 42, 46, mix(skin, (0, 0, 0), .12))
    draw_head(g, p, skin, hair, p.black_eyes)
    g.pop()
    # ---- near leg & arms
    if side:
        leg(legs[1], False)
    if side:
        ends['near'] = draw_arm(1, p.hR, p.bendR, False)
    else:
        ends['L'] = draw_arm(-1, p.hL, p.bendL, False)
        ends['R'] = draw_arm(1, p.hR, p.bendR, False)
    # ---- phone / finger
    if p.phone is not None:
        e = ends.get('near') or ends.get('R' if p.phone_hand == 'R' else 'L')
        draw_phone(g, e, p, side)
    if p.finger_lips:
        pass
    g.pop()
    return ends


def draw_phone(g, e, p, side):
    g.push()
    g.xf(e[0], e[1] - 40, 0)
    w, h = (92, 160)
    g.poly([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], (24, 24, 30), (10, 10, 14), 3)
    gl = p.phone[1]
    g.poly([(-w / 2 + 8, -h / 2 + 10), (w / 2 - 8, -h / 2 + 10), (w / 2 - 8, h / 2 - 10), (-w / 2 + 8, h / 2 - 10)], (int(40 + 150 * gl), int(60 + 170 * gl), int(90 + 160 * gl)))
    g.ell(e[0] * 0, 0, 0, 0)
    g.pop()
    # thumb over the phone
    g.ell(e[0] - 8, e[1] - 6, 22, 30, SKIN, tuple(v * .55 for v in SKIN), 3)


def draw_head(g, p, skin, hair, black_eyes):
    e = p.e
    ol = lambda c: tuple(v * 0.55 for v in c)
    if p.view == 'back':
        g.ell(-100, 6, 20, 30, skin, ol(skin), 3); g.ell(100, 6, 20, 30, skin, ol(skin), 3)
        g.ell(0, -20, 118, 126, hair, ol(hair), 4)
        g.poly([(-20, -120), (10, -60), (50, -122), (40, -140)], mix(hair, (255, 255, 255), .08))
        g.line([(-70, -90), (-20, -50), (30, -40)], mix(hair, (0, 0, 0), .35), 4)
        return
    side = p.view == 'side'
    yaw = p.yaw
    sx = 0 if side else yaw * 38     # feature shift
    comp = 1 if side else 1 - 0.28 * abs(yaw)
    # hair back
    g.ell(0, -22, 124, 128, hair, ol(hair), 4)
    if side:
        # face (profile): ellipse + nose
        g.ell(10, 14, 108, 112, skin, ol(skin), 4)
        g.poly([(100, 6), (140, 34), (104, 46)], skin, ol(skin), 4)
        g.ell(-34, 20, 26, 36, mix(skin, (0, 0, 0), .1), ol(skin), 3)
        ex, ey = 56, -6
        eyes = [(ex, ey, 1.0)]
    else:
        g.ell(0, 14, 108, 112, skin, ol(skin), 4)
        if abs(yaw) < 0.85:
            g.ell(-106, 20, 20, 32, skin, ol(skin), 3); g.ell(106, 20, 20, 32, skin, ol(skin), 3)
        eyes = [(-44 * comp + sx, -4, 1.0), (44 * comp + sx, -4, 1.0)]
    # fringe
    if side:
        g.poly([(-118, -10), (-100, -92), (-30, -128), (50, -118), (96, -70), (118, -26), (96, -40), (60, -58), (20, -78), (-40, -50), (-100, -20)], hair, ol(hair), 4)
    else:
        g.poly([(-114, -12), (-104, -80), (-50, -122), (20, -126), (84, -102), (116, -52), (112, -8), (90, -44), (50, -70), (6, -50), (-30, -78), (-74, -52), (-100, -20)], hair, ol(hair), 4)
        g.poly([(-30, -122), (30, -126), (50, -100), (-10, -96)], mix(hair, (255, 255, 255), .1))
    # eyes
    blink = p.blink
    openness = max(0.06, e['eye'] * (1 - blink))
    for (ex, ey, _) in eyes:
        rx = 33 * comp if not side else 28
        ry = 40 * openness
        if black_eyes:
            g.ell(ex, ey, rx, max(ry, 3), (6, 6, 8), (0, 0, 0), 3)
            g.ell(ex - rx * .3, ey - ry * .3, 6, 6, (70, 70, 90))
        else:
            g.ell(ex, ey, rx, max(ry, 3), (250, 250, 252), ol(skin), 3)
            if ry > 8:
                pr = 12 + 3 * (e['eye'] > 1.3)
                gx = max(-1, min(1, e['px'] + (yaw * 0.6 if not side else 0.3)))
                gy = max(-1, min(1, e['py']))
                ppx = ex + gx * (rx - pr - 3) * 0.9
                ppy = ey + gy * max(ry - pr - 2, 0) * 0.9
                g.ell(ppx, ppy, pr, min(pr, ry - 1), (20, 18, 24))
                g.ell(ppx - 4, ppy - 4, 4, 4, (255, 255, 255))
        # lid shade when narrow
        if openness < 0.7:
            g.ell(ex, ey - ry * 0.55, rx * 1.02, max(ry * 0.55, 2), skin, a=235)
            g.line([(ex - rx, ey - ry * 0.1), (ex + rx, ey - ry * 0.1)], ol(skin), 4)
    # brows
    br = tuple(v * 0.8 for v in HAIR_D)
    for idx, (ex, ey, _) in enumerate(eyes):
        sg = -1 if (idx == 0 and not side) else 1
        raise_ = -e['brow'] * 22
        inner_dy = -e['brin'] * 16
        yb = ey - 58 + raise_
        if side:
            g.line([(ex - 26, yb + 4 + inner_dy * -0.5), (ex + 4, yb - 6), (ex + 34, yb + 2 + inner_dy)], br, 11)
        else:
            ix = ex - sg * 28 * comp; ox = ex + sg * 30 * comp
            g.line([(ix, yb + inner_dy * 1.0), ((ix + ox) / 2, yb - 8 + inner_dy * 0.4), (ox, yb + 6 - inner_dy * 0.4)], br, 11)
    # nose
    nx = (sx * 1.2 if not side else 112)
    if side:
        g.line([(100, 34), (108, 46)], ol(skin), 4)
    else:
        g.line([(nx - 10 * comp, 38), (nx, 44), (nx + 10 * comp, 38)], ol(skin), 4)
    # mouth
    mx = (sx * 1.1) if not side else 70
    my = 78 + e['mo'] * 4
    mw = 34 * e['mw'] * (comp if not side else 0.7)
    mo = e['mo']
    mc = e['mc']
    if p.finger_lips:
        mo = 0
    if mo < 0.06:
        g.line([(mx - mw, my - mc * -6 * -1 + 2), (mx, my + mc * -10 + 4), (mx + mw, my - mc * -6 * -1 + 2)], tuple(v * .5 for v in skin), 5)
    else:
        top = [(mx - mw, my + (-mc) * 6), (mx, my - mo * 10 + (-mc) * 2), (mx + mw, my + (-mc) * 6)]
        bot = [(mx + mw * .8, my + (-mc) * 6 + mo * 18), (mx, my + mo * 46 + 4), (mx - mw * .8, my + (-mc) * 6 + mo * 18)]
        g.poly(top + bot, (74, 22, 30), (50, 14, 20), 3)
        if mo > 0.4:
            g.ell(mx, my + mo * 34, mw * 0.5, mo * 8, (178, 70, 80))
    if p.finger_lips:
        pass


def draw_finger_to_lips(g, x, y, s, flip=1):
    """Raised index finger over the mouth for the reflection (front view). Coordinates relative to head neck anchor."""
    pass


# ---------------------------------------------------------------- shadow entity
def draw_entity(g, x, y, s, st):
    """Tall black humanoid. st keys: lean, head_tilt, sway, walk(phase), arm_drop, eyes(0..1), scale_h, view, flip, glow."""
    view = st.get('view', 'front')
    flip = st.get('flip', 1)
    lean = st.get('lean', 0.0)
    ht = st.get('head_tilt', 0.0)
    ph = st.get('phase', 0.0)
    amp = st.get('stride', 0.0)
    sway = st.get('sway', 0.0)
    H = st.get('tall', 1.0)
    rim = st.get('rim', (52, 44, 78))
    body = (8, 7, 12)
    g.push()
    g.xf(x, y, 0, s * (flip if view == 'side' else 1), s * H)
    leg_l = 250; arm_l = st.get('arm_len', 250)
    hip = (0, -520)
    sh = (math.sin(lean) * 330, hip[1] - math.cos(lean) * 330)
    sd = view == 'side'
    def limb(a, b, w):
        g.capsule(a, b, w, body, rim, 4)
    # legs
    for sgn in (-1, 1):
        ph_ = ph + (0 if sgn < 0 else math.pi)
        fx = (math.sin(ph_) * amp * 130) if sd else sgn * 46
        fy = -max(0, math.cos(ph_)) * amp * 70 if sd or True else 0
        if not sd: fy = -max(0, math.sin(ph_)) * amp * 60
        hp_ = (0 if sd else sgn * 40, hip[1])
        j, e = ik(hp_, (fx, fy), leg_l, leg_l, 1)
        limb(hp_, j, 58); limb(j, e, 44)
        g.ell(e[0] + (24 if sd else 0), e[1] + 8, 52 if sd else 42, 18, body, rim, 3)
    # torso + tattered coat
    g.push(); g.xf(hip[0], hip[1], lean)
    wd = 1.0 if not sd else 0.62
    sw_ = math.sin(ph * 0.5 + sway * 3) * 14
    hem = []
    for i in range(7):
        xx = (-1 + i / 3.0) * 100 * wd
        hem.append((xx + sw_ * (0.4 + i * 0.1), 300 + (40 if i % 2 else -10) + 10 * math.sin(ph + i)))
    g.poly([(-70 * wd, -330), (-100 * wd, -250), (-104 * wd, 60)] + hem[::1] + [(104 * wd, 60), (100 * wd, -250), (70 * wd, -330)], body, rim, 4)
    g.pop()
    # arms
    sa = st.get('arm_swing', 0.0)
    for sgn in (-1, 1):
        s0 = (sh[0] + (0 if sd else sgn * 92), sh[1] + 30)
        ph_ = ph + (0 if sgn < 0 else math.pi)
        tgt = (s0[0] + (math.sin(ph_) * amp * 90 if sd else sgn * 30 + sway * sgn * 24), s0[1] + arm_l * 2 - 40 + st.get('arm_up', 0) * -200)
        tgt = st.get('hands', {}).get(sgn, tgt)
        j, e = ik(s0, tgt, arm_l, arm_l, -sgn if not sd else 1)
        limb(s0, j, 46); limb(j, e, 34)
        # long fingers
        for fi in range(3):
            g.line([e, (e[0] + (fi - 1) * 14, e[1] + 70 + fi * 4)], body, 7)
    # neck + head
    g.push(); g.xf(sh[0], sh[1] - 10, ht + lean * 0.5)
    limb((0, 0), (0, -70), 36)
    g.ell(0, -140, 70 if not sd else 62, 88, body, rim, 4)
    g.pop()
    g.pop()
    # glowing eyes handled by caller (emissive) via head position
    hx = x + (sh[0] + math.sin(ht + lean * .5) * -140 * 0) * s
    return


def entity_head_pos(x, y, s, st):
    H = st.get('tall', 1.0)
    lean = st.get('lean', 0.0); ht = st.get('head_tilt', 0.0)
    hip = (0, -520)
    sh = (math.sin(lean) * 330, hip[1] - math.cos(lean) * 330)
    a = ht + lean * 0.5
    hx = sh[0] + math.sin(a) * 150
    hy = sh[1] - 10 - math.cos(a) * 150
    flip = st.get('flip', 1) if st.get('view', 'front') == 'side' else 1
    return x + hx * s * flip, y + hy * s * H, a
