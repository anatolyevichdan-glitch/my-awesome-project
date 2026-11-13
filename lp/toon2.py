"""Flat 2D/2.5D character renderer in the PAPA VERNULSYA language.

The 3D skeleton (pose, IK, camera) is solved by rig.solve; this module only decides how the
character LOOKS: flat fills with soft gradients, big white eyes with dot pupils, boxy hoodie,
capsule limbs, mitten hands, oval sneakers. Hair and face features live on the head sphere so
the design stays identical from every angle.
"""
import math
import sys
import numpy as np
import skia

sys.path.insert(0, '/tmp/hoplite/workspace/rem')
from gfx import P, lin, rad, path_smooth, path_poly, hull, capsule_path, mix, shade  # noqa: E402
import rig as R  # noqa: E402
from rig import V, nrm  # noqa: E402

# ------------------------------------------------------------------ palette (sampled from PAPA refs)
PAL = dict(
    skin=(248, 203, 195), skin_hi=(252, 218, 210), skin_sh=(226, 170, 166), skin_line=(196, 128, 126),
    hair=(98, 52, 56), hair_hi=(124, 70, 72), hair_sh=(70, 36, 42),
    hood=(60, 59, 70), hood_hi=(78, 77, 90), hood_sh=(42, 41, 50), collar=(26, 24, 32), string=(196, 196, 206),
    pants=(30, 30, 40), pants_hi=(44, 44, 56),
    shoe=(168, 168, 176), shoe_hi=(196, 196, 204), sole=(214, 214, 220),
    eye=(247, 247, 245), eye_sh=(214, 214, 220), pupil=(16, 14, 20),
    brow=(72, 36, 44), mouth=(104, 30, 48), tongue=(214, 104, 112), teeth=(250, 248, 244),
    black_eye=(6, 6, 10),
)

R.HEAD_R = 108.0   # slightly smaller head than EP1: an 18-year-old, not a child
HEAD_R = R.HEAD_R
R.NECK_H = 262.0

# ------------------------------------------------------------------ cast
BASE_PAL = dict(PAL)
CHARS = {
    'hero': dict(hair='messy', backpack=True, pal=dict(
        hair=(30, 28, 36), hair_hi=(54, 52, 64), hair_sh=(16, 15, 22), brow=(30, 26, 32),
        hood=(30, 30, 36), hood_hi=(46, 46, 56), hood_sh=(18, 18, 24), collar=(10, 10, 14), string=(150, 150, 160),
        pants=(26, 28, 36), pants_hi=(38, 40, 50), shoe=(60, 60, 68), shoe_hi=(84, 84, 92), sole=(190, 190, 196),
        skin=(240, 204, 190), skin_hi=(248, 218, 206), skin_sh=(214, 170, 160))),
    'driver': dict(hair='cap', uniform=True, marks=('wrinkles', 'pale'), pal=dict(
        hair=(38, 46, 62), hair_hi=(56, 66, 86), hair_sh=(22, 28, 40), brow=(120, 116, 112),
        hood=(46, 56, 74), hood_hi=(62, 74, 96), hood_sh=(30, 36, 50), collar=(24, 28, 38), string=(170, 150, 90),
        pants=(30, 34, 46), pants_hi=(42, 48, 62), shoe=(24, 22, 24), shoe_hi=(44, 42, 44), sole=(30, 28, 30),
        skin=(214, 210, 200), skin_hi=(228, 226, 218), skin_sh=(176, 176, 172), skin_line=(140, 134, 132),
        mouth=(100, 80, 86))),
    'babka': dict(hair='scarf', coat=True, marks=('wrinkles', 'old'), pal=dict(
        hair=(52, 40, 46), hair_hi=(78, 60, 66), hair_sh=(32, 24, 30), brow=(170, 164, 160),
        hood=(34, 30, 34), hood_hi=(50, 44, 50), hood_sh=(20, 18, 22), collar=(60, 52, 50), string=(120, 110, 100),
        pants=(30, 28, 32), pants_hi=(42, 40, 44), shoe=(26, 22, 22), shoe_hi=(44, 38, 38), sole=(30, 26, 26),
        skin=(222, 200, 188), skin_hi=(234, 216, 206), skin_sh=(188, 164, 156), skin_line=(150, 118, 112),
        mouth=(110, 60, 70))),
    'burned': dict(hair='messy', backpack=False, marks=('burn',), pal=None),
}
for _i, (_h, _c, _s) in enumerate([((70, 60, 54), (58, 66, 60), (226, 196, 176)), ((44, 40, 40), (80, 52, 48), (236, 206, 190)),
                                    ((120, 116, 112), (52, 54, 70), (214, 196, 184)), ((26, 24, 28), (66, 70, 58), (232, 200, 180)),
                                    ((90, 70, 50), (48, 44, 58), (224, 190, 172)), ((150, 146, 140), (70, 60, 52), (216, 200, 192))]):
    CHARS[f'pax{_i}'] = dict(hair=['thin', 'helmet', 'thin', 'messy', 'helmet', 'thin'][_i], coat=True,
                            marks=('pale',), pal=dict(hair=_h, hair_hi=tuple(min(255, v + 22) for v in _h),
                                                      hair_sh=tuple(int(v * 0.6) for v in _h), brow=_h,
                                                      hood=_c, hood_hi=tuple(min(255, v + 16) for v in _c),
                                                      hood_sh=tuple(int(v * 0.65) for v in _c), collar=tuple(int(v * 0.5) for v in _c),
                                                      skin=_s, skin_hi=tuple(min(255, v + 12) for v in _s),
                                                      skin_sh=tuple(int(v * 0.86) for v in _s),
                                                      pants=(28, 28, 34), pants_hi=(40, 40, 48), shoe=(30, 28, 30),
                                                      shoe_hi=(50, 48, 50), sole=(40, 38, 40)))
CHARS['burned']['pal'] = CHARS['hero']['pal']
CHAR = {}


class use:
    """with use('driver'): toon2.draw(...)"""
    def __init__(self, name):
        self.spec = CHARS[name]

    def __enter__(self):
        global CHAR
        self.prev = (dict(PAL), CHAR)
        PAL.clear(); PAL.update(BASE_PAL); PAL.update(self.spec.get('pal') or {})
        CHAR = self.spec
        return self

    def __exit__(self, *a):
        global CHAR
        PAL.clear(); PAL.update(self.prev[0]); CHAR = self.prev[1]


def _t(c, tint):
    if tint is None:
        return c
    return tuple(max(0, min(255, c[i] * tint[i])) for i in range(3))


class Look:
    """per-draw lighting: key light side, optional rim light"""
    def __init__(self, key=(-0.6, -0.5), rim=None, rim_w=6.0, tint=None, flat=0.0):
        self.key = key            # screen direction the light comes FROM (x, y)
        self.rim = rim            # (r,g,b) or None
        self.rim_w = rim_w        # rim thickness in px at scale 1
        self.tint = tint
        self.flat = flat


def _fill_lit(cv, path, base, hi, sh, look, s, bbox=None):
    """flat fill with a soft key-light gradient across the shape, then an optional rim crescent"""
    hi = tuple(0.5 * h + 0.5 * c for h, c in zip(hi, base))   # flatter, PAPA-style fills
    sh = tuple(0.55 * h + 0.45 * c for h, c in zip(sh, base))
    b = path.getBounds() if bbox is None else bbox
    cx, cy = b.centerX(), b.centerY()
    rr = max(b.width(), b.height()) * 0.5 + 1
    kx, ky = look.key
    L = math.hypot(kx, ky) or 1
    kx, ky = kx / L, ky / L
    p0 = (cx + kx * rr, cy + ky * rr)
    p1 = (cx - kx * rr, cy - ky * rr)
    cv.drawPath(path, P(shader=skia.GradientShader.MakeLinear(
        [skia.Point(*p0), skia.Point(*p1)],
        [skia.Color4f(*(v / 255 for v in hi), 1), skia.Color4f(*(v / 255 for v in base), 1), skia.Color4f(*(v / 255 for v in sh), 1)],
        [0.0, 0.55, 1.0])))
    if look.rim is not None:
        w = look.rim_w * s
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        rp = skia.Path(path)
        rp.offset(-kx * 0, 0)
        # rim crescent on the side facing the rim light (opposite of key unless set)
        rx, ry = look.rim_dir if hasattr(look, 'rim_dir') else (-kx, -ky)
        cv.drawPath(path, P(look.rim, 0.85, style='stroke', width=w * 2.2, blur=w * 0.35))
        inner = skia.Path(path)
        inner.offset(-rx * w * 1.4, -ry * w * 1.4)
        cv.drawPath(inner, P(base, 1.0, blur=w * 0.25)) if False else None
        cv.restore()


def _rim(cv, path, look, s, base):
    if look.rim is None:
        return
    w = look.rim_w * s
    rx, ry = getattr(look, 'rim_dir', (0.8, -0.3))
    cv.save()
    cv.clipPath(path, skia.ClipOp.kIntersect, True)
    # light leaks in from the rim side: draw rim colour, then cover with a shifted copy of the shape
    sh = skia.Path(path)
    sh.offset(-rx * w, -ry * w)
    big = skia.Path(path)
    cv.drawPath(big, P(look.rim, 0.9, blur=w * 0.3))
    cv.restore()
    return sh


def lit_part(cv, path, cols, look, s):
    """fill + rim crescent. cols = (base, hi, sh)"""
    base, hi, sh = cols
    _fill_lit(cv, path, base, hi, sh, look if look.rim is None else Look(look.key, None, tint=look.tint), s)
    if look.rim is not None:
        w = look.rim_w * s
        rx, ry = getattr(look, 'rim_dir', (0.8, -0.3))
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        outside = skia.Path(path)
        outside.setFillType(skia.PathFillType.kInverseWinding)
        # crescent = shape minus shape shifted away from the rim light
        shifted = skia.Path(path)
        shifted.offset(-rx * w, -ry * w)
        cres = skia.Op(path, shifted, skia.PathOp.kDifference_PathOp)
        if cres is not None:
            cv.drawPath(cres, P(look.rim, 0.95, blur=max(0.6, w * 0.18)))
        cv.restore()


# ------------------------------------------------------------------ geometry helpers
def ring(c, ax, ay, wx, wz, n=20):
    return [c + ax * (wx * math.cos(t)) + ay * (wz * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def hull_path(pts2, tension=0.42, corner=None):
    h = hull(pts2)
    if len(h) < 3:
        return path_poly(h)
    # round the corners of the convex hull without Catmull-Rom overshoot
    xs = [q[0] for q in h]; ys = [q[1] for q in h]
    size = max(max(xs) - min(xs), max(ys) - min(ys))
    rad_ = corner if corner is not None else size * tension * 0.45
    pa = path_poly(h)
    pe = skia.CornerPathEffect.Make(max(1.0, rad_))
    out = skia.Path()
    pnt = skia.Paint(PathEffect=pe)
    pnt.getFillPath(pa, out)
    return out


def cap(a, b, ra, rb):
    return capsule_path(a, b, ra, rb)


# ------------------------------------------------------------------ head
HAIR_KEYS = None


def hairline(phi, part=0.0):
    """latitude (rad) of the hair boundary as function of head azimuth phi (0 = face centre)."""
    a = np.abs(phi)
    style = CHAR.get('hair', 'helmet')
    if style == 'scarf':
        # headscarf: covers forehead, ears and wraps under the chin; face opening only at the front
        return np.interp(a, [0.0, 0.45, 0.85, 1.1, 1.35, 3.2], [0.30, 0.27, 0.02, -0.6, -1.25, -1.45])
    if style == 'cap':
        # peaked cap crown + short grey hair band at the temples (band drawn by draw_hair)
        return np.interp(a, [0.0, 0.8, 1.6, 2.4, 3.2], [0.52, 0.46, 0.34, 0.20, 0.14])
    if style == 'thin':
        return np.interp(a, [0.0, 0.6, 1.2, 1.8, 3.2], [0.80, 0.70, 0.36, 0.05, -0.30])
    # front fringe -> temple -> above ear -> nape
    base = np.interp(a, [0.0, 0.45, 0.95, 1.35, 1.75, 2.3, 3.2], [0.66, 0.62, 0.50, 0.26, 0.10, -0.28, -0.40])
    # side-swept fringe: hangs lower on the character's right (phi<0 = screen-left when facing camera)
    sweep = -0.06 * np.exp(-((phi + 0.30) / 0.32) ** 2) + 0.04 * np.exp(-((phi - 0.45) / 0.25) ** 2)
    teeth = 0.0
    if style == 'messy':
        # uneven fringe strands falling over the forehead
        teeth = 0.07 * np.abs(np.sin(phi * 7.0 + 0.6)) * np.exp(-(a / 0.9) ** 2) - 0.05 * np.exp(-(a / 0.7) ** 2)
    return base + sweep - teeth


def head_basis(cam, S):
    """head axes in camera space (x right, y up, z toward viewer)"""
    def c(v):
        dx, dy, d = cam.dirproj(v)
        return np.array([dx, -dy, d])
    return c(S.hr), c(S.hu), c(S.hf)


def sphere_pt(S, phi, lat, rr=1.0):
    return S.H + (S.hr * (math.sin(phi) * math.cos(lat)) + S.hu * math.sin(lat) + S.hf * (math.cos(phi) * math.cos(lat))) * HEAD_R * rr


def feature_frame(cam, S, phi, lat, rr=1.0):
    """screen centre + screen vectors for local (u right, v down) tangent coords in HEAD_R units, plus facing"""
    n = S.hr * (math.sin(phi) * math.cos(lat)) + S.hu * math.sin(lat) + S.hf * (math.cos(phi) * math.cos(lat))
    te = S.hr * math.cos(phi) - S.hf * math.sin(phi)            # east tangent
    tn = nrm(np.cross(n, te))                                    # north tangent (up)
    c, _, k = cam.proj(S.H + n * HEAD_R * rr)
    ex, ey, _ = cam.dirproj(te)
    nx, ny, _ = cam.dirproj(tn)
    _, _, nd = cam.dirproj(n)
    sc = cam.s * HEAD_R
    # u -> east, v -> down (= -north)
    return c, (ex * sc, ey * sc), (-nx * sc, -ny * sc), nd


def with_frame(cv, fr):
    c, au, av, _ = fr
    m = skia.Matrix.MakeAll(au[0], av[0], c[0], au[1], av[1], c[1], 0, 0, 1)
    cv.save()
    cv.concat(m)


def draw_head(cv, S, p, cam, s, look, black_eyes=False):
    tint = look.tint
    T = lambda c: _t(c, tint)
    e = p.e
    hc, _, k = cam.proj(S.H)
    Rp = HEAD_R * cam.s
    hr_c, hu_c, hf_c = head_basis(cam, S)
    up_ang = math.atan2(hu_c[0], hu_c[1])            # screen roll of the head
    head_path = skia.Path()
    head_path.addOval(skia.Rect(-Rp * 0.97, -Rp * 1.0, Rp * 0.97, Rp * 1.04))
    m = skia.Matrix()
    m.setRotate(math.degrees(up_ang))
    m.postTranslate(hc[0], hc[1])
    head_path.transform(m)

    # ears (behind the skull when they face away, on top when they face us)
    ears = []
    for sd in (1, -1):
        fr = feature_frame(cam, S, sd * math.pi / 2, -0.06, 1.0)
        ears.append((sd, fr))
    for sd, fr in ears:
        if fr[3] <= 0.35:
            with_frame(cv, fr)
            pa = skia.Path(); pa.addOval(skia.Rect(-0.15, -0.19, 0.15, 0.19))
            cv.drawPath(pa, P(T(PAL['skin_sh'])))
            cv.restore()
    # nose bump in profile (sticks out of the silhouette)
    nfr = feature_frame(cam, S, 0.0, -0.13, 1.09)
    lit_part(cv, head_path, (T(PAL['skin']), T(PAL['skin_hi']), T(PAL['skin_sh'])), look, s)
    if abs(nfr[3]) < 0.75:
        with_frame(cv, nfr)
        pa = skia.Path(); pa.addOval(skia.Rect(-0.11, -0.10, 0.11, 0.12))
        cv.drawPath(pa, P(T(PAL['skin'])))
        cv.restore()

    cv.save()
    cv.clipPath(head_path, skia.ClipOp.kIntersect, True)
    # soft form shadow on the side away from the key light
    kx, ky = look.key
    cv.drawCircle(hc[0] - kx * Rp * 1.35, hc[1] - ky * Rp * 1.35, Rp * 1.25, P(T(PAL['skin_sh']), 0.35, blur=Rp * 0.35))

    for sd, fr in ears:
        if fr[3] > 0.35:
            with_frame(cv, fr)
            pa = skia.Path(); pa.addOval(skia.Rect(-0.15, -0.19, 0.15, 0.19))
            cv.drawPath(pa, P(T(PAL['skin_sh'])))
            cv.drawArc(skia.Rect(-0.08, -0.11, 0.08, 0.11), 100, 160, False, P(T(PAL['skin_line']), style='stroke', width=0.035))
            cv.restore()

    def alpha_of(nd):
        return max(0.0, min(1.0, (nd - 0.05) / 0.2))

    # ---- eyes
    eyew = e['eyew']
    for sd in (1, -1):
        fr = feature_frame(cam, S, sd * 0.40, 0.0)
        a = alpha_of(fr[3])
        if a <= 0:
            continue
        brow_v = e['brow'] if sd == 1 or e.get('browL') is None else e['browL']
        with_frame(cv, fr)
        rx, ry = 0.255 * eyew, 0.315 * eyew
        lid = max(0.0, min(1.0, e['lid'] + p.blink * (1 - e['lid'])))
        low = e['lidlow']
        eye = skia.Path(); eye.addOval(skia.Rect(-rx, -ry, rx, ry))
        if lid > 0.97 and low <= 0.01:
            # fully shut: a flat lid fill shows as a pale oval on the shaded face, so draw only the lash line
            cv.drawArc(skia.Rect(-rx * 0.9, -ry * 0.2, rx * 0.9, ry * 0.5), 15, 150, False,
                       P(T(PAL['skin_line']), 0.8 * a, style='stroke', width=0.03))
        elif black_eyes:
            cv.drawPath(eye, P(T(PAL['black_eye']), a))
            cv.drawOval(skia.Rect(-rx * 0.55, -ry * 0.62, -rx * 0.05, -ry * 0.25), P((90, 96, 120), 0.45 * a, blur=0.02))
        else:
            cv.drawPath(eye, P(shader=lin((0, -ry), (0, ry), T(PAL['eye']), T(PAL['eye_sh'])), ) if False else P(T(PAL['eye']), a))
            cv.save(); cv.clipPath(eye, skia.ClipOp.kIntersect, True)
            cv.drawOval(skia.Rect(-rx * 1.1, ry * 0.25, rx * 1.1, ry * 1.6), P(T(PAL['eye_sh']), 0.55 * a, blur=0.03))
            # pupil: small dot, gaze offset
            pr_ = 0.052 * e['pupil'] + 0.012
            gx = e['gx'] * rx * 0.62 - sd * 0.0
            gy = e['gy'] * -ry * 0.55
            cv.drawCircle(gx, gy, pr_, P(T(PAL['pupil']), a))
            cv.drawCircle(gx + pr_ * 0.35, gy - pr_ * 0.4, pr_ * 0.28, P((255, 255, 255), 0.8 * a))
            cv.restore()
        # eyelids (skin) from top / bottom
        if (lid > 0.01 or low > 0.01) and not (lid > 0.97 and low <= 0.01):
            cv.save(); cv.clipPath(eye, skia.ClipOp.kIntersect, True)
            tilt_lid = (e['tilt'] if sd == 1 or e.get('tiltL') is None else e['tiltL']) * 0.25 * sd
            ytop = -ry + 2 * ry * lid
            pl = skia.Path(); pl.moveTo(-rx * 1.3, -ry * 1.3); pl.lineTo(rx * 1.3, -ry * 1.3)
            pl.lineTo(rx * 1.3, ytop - tilt_lid * rx); pl.lineTo(-rx * 1.3, ytop + tilt_lid * rx); pl.close()
            cv.drawPath(pl, P(T(PAL['skin']), a))
            cv.drawLine(-rx * 1.3, ytop + tilt_lid * rx, rx * 1.3, ytop - tilt_lid * rx, P(T(PAL['skin_line']), a, style='stroke', width=0.03))
            if low > 0.01:
                yb = ry - 2 * ry * low * 0.5
                cv.drawRect(skia.Rect(-rx * 1.3, yb, rx * 1.3, ry * 1.3), P(T(PAL['skin']), a))
            cv.restore()
        cv.drawPath(eye, P(T(PAL['skin_line']), 0.35 * a * (1 - lid) ** 2, style='stroke', width=0.018))
        # brow: thick rounded bar; brow raises it, tilt rotates (inner end up = worried)
        tilt = e['tilt'] if sd == 1 or e.get('tiltL') is None else e['tiltL']
        by = -ry - 0.09 - 0.085 * brow_v
        bl = 0.21
        inner_dy = -0.10 * tilt
        outer_dy = 0.03 * tilt
        bend = e.get('bend', 0.0)
        pb = skia.Path()
        # local u: +u is character-left on screen when facing camera; inner end is toward the nose
        ui, uo = -sd * 0.03 * 0 + (-0.04 if sd == 1 else 0.04), (bl if sd == 1 else -bl)
        ui = -0.02 * sd * -1
        x_in, x_out = (-0.05 * sd) * -1 * 0 + (-0.04 * sd), 0.0
        # simpler: build in eye-local coords with inner end toward face centre (u toward -sd)
        xi = -sd * 0.07 * 0 - (0.2 * sd) * 0 + (-1 if sd == 1 else 1) * 0.06
        xo = (1 if sd == 1 else -1) * 0.24
        pb.moveTo(xi, by + inner_dy)
        pb.quadTo((xi + xo) / 2, by - 0.05 - bend * 0.06 + (inner_dy + outer_dy) / 2, xo, by + outer_dy)
        cv.drawPath(pb, P(T(PAL['brow']), a, style='stroke', width=0.085))
        cv.restore()

    # ---- nose: small curl
    fr = feature_frame(cam, S, 0.0, -0.15)
    a = alpha_of(fr[3])
    if a > 0:
        with_frame(cv, fr)
        pn = skia.Path(); pn.moveTo(0.02, -0.12); pn.quadTo(-0.07, -0.02, -0.02, 0.05); pn.quadTo(0.03, 0.08, 0.06, 0.04)
        cv.drawPath(pn, P(T(PAL['skin_line']), a, style='stroke', width=0.035))
        cv.restore()

    # ---- mouth
    fr = feature_frame(cam, S, 0.0, -0.45)
    a = alpha_of(fr[3])
    A_mouth = fr[0]
    if a > 0:
        with_frame(cv, fr)
        mo = max(0.0, min(1.2, e['mopen'] + p.talk))
        mw = 0.17 * e['mw']
        sm = e['smile']
        asym = e.get('asym', 0.0)
        mround = e.get('mround', 0.0)
        if mo < 0.06:
            pm = skia.Path()
            pm.moveTo(-mw, -sm * 0.05 + asym * 0.03)
            pm.quadTo(0, sm * 0.10, mw, -sm * 0.05 - asym * 0.03)
            cv.drawPath(pm, P(T(PAL['mouth']), a, style='stroke', width=0.045))
        else:
            w = mw * (1 - 0.45 * mround) * (1 + 0.5 * mo) + 0.02
            h = 0.05 + 0.30 * mo
            pm = skia.Path()
            if mround > 0.4:
                pm.addOval(skia.Rect(-w * 0.7, -h * 0.55, w * 0.7, h * 0.65))
            else:
                # frightened open mouth: wide top, rounded bottom, corners pulled down by -smile
                cd = -sm * 0.06
                pm.moveTo(-w, -h * 0.25 + cd)
                pm.cubicTo(-w * 0.5, -h * 0.55, w * 0.5, -h * 0.55, w, -h * 0.25 + cd)
                pm.cubicTo(w * 0.9, h * 0.9, -w * 0.9, h * 0.9, -w, -h * 0.25 + cd)
                pm.close()
            cv.drawPath(pm, P(T(PAL['mouth']), a))
            cv.save(); cv.clipPath(pm, skia.ClipOp.kIntersect, True)
            if mo > 0.35 and mround <= 0.4:
                cv.drawRect(skia.Rect(-w, -h, w, -h * 0.32), P(T(PAL['teeth']), a))
            cv.drawOval(skia.Rect(-w * 0.55, h * 0.15, w * 0.55, h * 0.95), P(T(PAL['tongue']), a))
            cv.restore()
        # sweat drop
        sw = e.get('sweat', 0.0)
        if sw > 0.25:
            pass
        cv.restore()
    # sweat drop on the temple (PAPA uses a single blue drop)
    sw = e.get('sweat', 0.0)
    if sw > 0.3:
        fr = feature_frame(cam, S, -0.95, 0.42)
        a = alpha_of(fr[3]) * min(1, (sw - 0.3) * 3)
        if a > 0:
            with_frame(cv, fr)
            pd = skia.Path(); pd.moveTo(0, -0.12); pd.quadTo(0.07, 0.0, 0.05, 0.04); pd.quadTo(0, 0.1, -0.05, 0.04); pd.quadTo(-0.07, 0, 0, -0.12)
            cv.drawPath(pd, P((150, 200, 240), 0.9 * a))
            cv.restore()
    draw_marks(cv, S, cam, alpha_of, T)
    cv.restore()   # head clip

    # ---- hair (rasterised on the head sphere)
    draw_hair(cv, S, cam, hc, Rp, hr_c, hu_c, hf_c, look, T)
    draw_headwear(cv, S, cam, alpha_of, T)
    return A_mouth


def _stroke(cv, pts, col, a, w=0.022):
    pa = path_smooth(pts, close=False) if len(pts) > 2 else path_poly(pts, close=False)
    cv.drawPath(pa, P(col, a, style='stroke', width=w))


def _blob(cx, cy, r, seed, n=14, rough=0.35):
    import random as _r
    g = _r.Random(seed)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        rr = r * (1 + g.uniform(-rough, rough))
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t) * 0.9))
    return path_smooth(pts)


def draw_marks(cv, S, cam, alpha_of, T):
    marks = CHAR.get('marks', ())
    if not marks:
        return
    line = T(PAL['skin_line'])
    if 'wrinkles' in marks or 'old' in marks:
        fr = feature_frame(cam, S, 0.0, 0.40)
        a = alpha_of(fr[3])
        if a > 0:
            with_frame(cv, fr)
            for k, y in enumerate((-0.02, 0.07, 0.15)):
                _stroke(cv, [(-0.28 + 0.03 * k, y + 0.02), (0, y - 0.02), (0.28 - 0.03 * k, y + 0.02)], line, 0.45 * a)
            cv.restore()
        for sd in (1, -1):
            fr = feature_frame(cam, S, sd * 0.78, -0.02)
            a = alpha_of(fr[3])
            if a > 0:
                with_frame(cv, fr)
                for k in (-1, 0, 1):
                    _stroke(cv, [(-0.02 * sd, 0.0), (0.13 * sd, k * 0.07)], line, 0.4 * a, 0.018)
                cv.restore()
            fr = feature_frame(cam, S, sd * 0.40, -0.17)
            a = alpha_of(fr[3])
            if a > 0:
                with_frame(cv, fr)
                _stroke(cv, [(-0.17, -0.02), (0, 0.05), (0.17, -0.02)], line, 0.45 * a, 0.02)
                cv.restore()
            fr = feature_frame(cam, S, sd * 0.26, -0.30)
            a = alpha_of(fr[3])
            if a > 0:
                with_frame(cv, fr)
                _stroke(cv, [(0.02 * sd, -0.12), (0.08 * sd, 0.02), (0.06 * sd, 0.17)], line, 0.5 * a, 0.024)
                cv.restore()
    if 'old' in marks:
        for sd in (1, -1):
            fr = feature_frame(cam, S, sd * 0.62, -0.32)
            a = alpha_of(fr[3])
            if a > 0:
                with_frame(cv, fr)
                cv.drawOval(skia.Rect(-0.12, -0.16, 0.12, 0.16), P(T(PAL['skin_sh']), 0.6 * a, blur=0.06))
                cv.restore()
        fr = feature_frame(cam, S, 0.0, -0.70)
        a = alpha_of(fr[3])
        if a > 0:
            with_frame(cv, fr)
            _stroke(cv, [(-0.12, 0.0), (0, 0.04), (0.12, 0.0)], line, 0.4 * a)
            cv.restore()
    if 'pale' in marks:
        for sd in (1, -1):
            fr = feature_frame(cam, S, sd * 0.40, -0.14)
            a = alpha_of(fr[3])
            if a > 0:
                with_frame(cv, fr)
                cv.drawOval(skia.Rect(-0.2, -0.05, 0.2, 0.09), P((110, 120, 130), 0.10 * a, blur=0.08))
                cv.restore()
    if 'burn' in marks:
        # one large burn over the character's right side (cheek, eye socket, temple, part of forehead)
        for k, (phi, lat, r, seed) in enumerate([(-0.50, 0.05, 0.62, 3), (-0.18, 0.40, 0.36, 5), (0.10, -0.45, 0.22, 9)]):
            fr = feature_frame(cam, S, phi, lat)
            a = alpha_of(fr[3] + 0.3)
            if a <= 0:
                continue
            with_frame(cv, fr)
            cv.drawPath(_blob(0, 0, r * 1.10, seed, rough=0.18), P(T((206, 150, 136)), 0.9 * a, blur=0.02))   # tight shiny edge
            cv.drawPath(_blob(0, 0, r * 0.96, seed + 1, rough=0.20), P(T((150, 64, 56)), a))                 # raw skin
            cv.drawPath(_blob(-0.02, 0.02, r * 0.70, seed + 4, rough=0.25), P(T((112, 40, 36)), a, blur=0.03))
            cv.drawPath(_blob(0.04, -0.03, r * 0.40, seed + 2, rough=0.35), P(T((52, 26, 24)), 0.95 * a, blur=0.01))   # charred core
            cv.restore()


def draw_headwear(cv, S, cam, alpha_of, T):
    style = CHAR.get('hair')
    if style == 'cap':
        for sd in (1, -1):    # grey hair at the temples under the cap
            fr = feature_frame(cam, S, sd * 1.5, 0.10)
            a = alpha_of(fr[3] + 0.2)
            if a > 0:
                with_frame(cv, fr)
                cv.drawPath(_blob(0, 0, 0.09, 21 + sd, rough=0.2), P(T((150, 150, 148)), a))
                cv.restore()
        fr = feature_frame(cam, S, 0.0, 0.50, 1.07)
        a = alpha_of(fr[3] + 0.35)
        if a > 0:
            with_frame(cv, fr)
            pv = skia.Path()
            pv.moveTo(-0.62, 0.0); pv.cubicTo(-0.5, 0.30, 0.5, 0.30, 0.62, 0.0); pv.close()
            cv.drawPath(pv, P(T((14, 16, 22)), a))
            cv.drawLine(-0.6, -0.02, 0.6, -0.02, P(T((24, 28, 38)), a, style='stroke', width=0.07))
            cv.drawOval(skia.Rect(-0.07, -0.26, 0.07, -0.12), P(T((176, 150, 80)), a))
            cv.restore()
    elif style == 'scarf':
        fr = feature_frame(cam, S, 0.0, -0.95, 1.02)
        a = alpha_of(fr[3] + 0.9)
        if a > 0:
            with_frame(cv, fr)
            cv.drawPath(_blob(0, 0, 0.11, 31, rough=0.15), P(T(PAL['hair']), a))
            for sd in (1, -1):
                pt = skia.Path(); pt.moveTo(0, 0); pt.quadTo(0.10 * sd, 0.18, 0.06 * sd, 0.34); pt.lineTo(0.0, 0.30); pt.close()
                cv.drawPath(pt, P(T(PAL['hair_sh']), a))
            cv.restore()


def draw_hair(cv, S, cam, hc, Rp, hr_c, hu_c, hf_c, look, T):
    RH = 1.07                          # hair shell radius (volume over the skull)
    pad = int(Rp * RH * 1.1 + 4)
    x0, y0 = int(hc[0]) - pad, int(hc[1]) - pad
    n = 2 * pad
    if n <= 4:
        return
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32)
    X = (xs + x0 + 0.5 - hc[0]) / (Rp * RH)
    Y = -(ys + y0 + 0.5 - hc[1]) / (Rp * RH)
    rho2 = X * X + Y * Y
    inside = rho2 < 1.0
    Z = np.sqrt(np.clip(1 - rho2, 0, 1))
    # camera-space point -> head-local
    a = X * hr_c[0] + Y * hr_c[1] + Z * hr_c[2]
    b = X * hu_c[0] + Y * hu_c[1] + Z * hu_c[2]
    c = X * hf_c[0] + Y * hf_c[1] + Z * hf_c[2]
    phi = np.arctan2(a, c)
    lat = np.arcsin(np.clip(b, -1, 1))
    hl = hairline(phi)
    margin = (lat - hl) * Rp * RH
    # outer edge: little messy tufts on the silhouette
    ang = np.arctan2(Y, X)
    style = CHAR.get('hair', 'helmet')
    tuft = 1.0
    if style == 'messy':
        tuft = 1.0 + 0.055 * np.clip(np.sin(ang * 11 + 0.4) + 0.6 * np.sin(ang * 17 + 2.0), 0, None) * (Y > -0.2)
    elif style == 'scarf':
        tuft = 1.03
    edge = (tuft - np.sqrt(rho2)) * Rp * RH
    alpha = np.clip(margin + 0.5, 0, 1) * np.clip(edge + 0.5, 0, 1)
    if alpha.max() <= 0:
        return
    base = np.array(T(PAL['hair']), np.float32)
    hi = np.array(T(PAL['hair_hi']), np.float32)
    shd = np.array(T(PAL['hair_sh']), np.float32)
    kx, ky = look.key
    L = math.hypot(kx, ky) or 1
    lam = np.clip(0.5 + 0.55 * (X * kx / L - Y * ky / L) + 0.25 * Y, 0, 1)[..., None]
    col = shd * (1 - lam) + base * lam
    col = col * (1 - np.clip(lam - 0.75, 0, 1) * 2) + hi * np.clip(lam - 0.75, 0, 1) * 2
    # darker band just above the hairline gives the fringe some thickness
    band = np.clip(1 - margin / (0.06 * Rp), 0, 1)[..., None] * 0.35
    col = col * (1 - band) + shd * band
    if style == 'scarf':
        # wool headscarf: folded front edge + small faded flower print
        fold = np.clip(1 - np.abs(margin - 0.05 * Rp) / (0.035 * Rp), 0, 1)[..., None]
        col = col * (1 - 0.45 * fold) + hi * 0.45 * fold * 1.3
        dots = (np.sin(phi * 16) * np.sin(lat * 16 + 0.5) > 0.82)[..., None] * (lam * 0.6 + 0.4)
        col = col * (1 - 0.5 * dots) + np.array(T((150, 96, 70)), np.float32) * 0.5 * dots
    if look.rim is not None:
        rx, ry = getattr(look, 'rim_dir', (0.8, -0.3))
        rr_ = np.clip((X * rx - Y * ry - 0.55) / 0.3, 0, 1) * np.clip((np.sqrt(rho2) - 0.78) / 0.2, 0, 1)
        col = col * (1 - rr_[..., None] * 0.85) + np.array(look.rim, np.float32) * rr_[..., None] * 0.85
    rgba = np.zeros((n, n, 4), np.uint8)
    pa = alpha
    rgba[..., :3] = np.clip(col * pa[..., None], 0, 255).astype(np.uint8)   # premultiplied
    rgba[..., 3] = (pa * 255).astype(np.uint8)
    img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    cv.drawImage(img, x0, y0)


# ------------------------------------------------------------------ hands
def draw_hand(cv, S, p, sd, cam, s, look):
    T = lambda c: _t(c, look.tint)
    mode = p.hand_mode[sd]
    hp, _, _ = cam.proj(S.handc[sd])
    wp, _, _ = cam.proj(S.wrist[sd])
    dx, dy = hp[0] - wp[0], hp[1] - wp[1]
    Ld = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(dy, dx)) - 90 if Ld > 1e-3 else 0.0
    r = 56 * cam.s   # PAPA hands are oversized mittens
    cv.save()
    cv.translate(hp[0], hp[1])
    cv.rotate(ang)
    skin = (T(PAL['skin']), T(PAL['skin_hi']), T(PAL['skin_sh']))
    # thumb side: toward the body midline in screen space
    _, _, dthumb = cam.dirproj(S.f)
    ts = -sd if dthumb >= 0 else sd
    if cam.flip:
        ts = -ts
    if mode in ('fist', 'grip', 'phone'):
        pa = skia.Path(); pa.addOval(skia.Rect(-r * 0.95, -r * 0.85, r * 0.95, r * 0.95))
        lit_part(cv, pa, skin, look, s)
        cv.drawArc(skia.Rect(-r * 0.6, -r * 0.2, r * 0.6, r * 0.7), 200, 140, False, P(T(PAL['skin_line']), 0.6, style='stroke', width=2.2 * cam.s * 2))
    elif mode == 'point':
        pa = skia.Path(); pa.addOval(skia.Rect(-r * 0.9, -r * 0.8, r * 0.9, r * 0.9))
        fing = cap((0, -r * 0.2), (ts * r * 0.15, r * 1.75), r * 0.26, r * 0.22)
        pa = skia.Op(pa, fing, skia.PathOp.kUnion_PathOp) or pa
        lit_part(cv, pa, skin, look, s)
    elif mode == 'open':
        pa = skia.Path(); pa.addOval(skia.Rect(-r * 0.95, -r * 0.6, r * 0.95, r * 1.05))
        for j in range(4):
            fx = (j - 1.5) * r * 0.42
            f_ = cap((fx, r * 0.5), (fx * 1.25, r * 1.55), r * 0.2, r * 0.18)
            pa = skia.Op(pa, f_, skia.PathOp.kUnion_PathOp) or pa
        th = cap((ts * r * 0.6, 0), (ts * r * 1.35, r * 0.55), r * 0.22, r * 0.2)
        pa = skia.Op(pa, th, skia.PathOp.kUnion_PathOp) or pa
        lit_part(cv, pa, skin, look, s)
    else:  # relaxed mitten
        pa = skia.Path(); pa.addOval(skia.Rect(-r * 0.85, -r * 0.7, r * 0.85, r * 1.15))
        th = skia.Path(); th.addOval(skia.Rect(ts * r * 0.45 - r * 0.32, -r * 0.35, ts * r * 0.45 + r * 0.32, r * 0.6))
        th.transform(skia.Matrix.RotateDeg(ts * 25, skia.Point(ts * r * 0.45, 0)))
        pa = skia.Op(pa, th, skia.PathOp.kUnion_PathOp) or pa
        lit_part(cv, pa, skin, look, s)
    cv.restore()
    return hp


# ------------------------------------------------------------------ whole character
def draw(cv, p, X0, Y0, s, yaw=None, cam_pitch=0.10, persp=0.0, look=None, black_eyes=False, flip=False,
         ground_shadow=0.45, props=None):
    """Draw the character. Returns screen anchors."""
    look = look or Look()
    T = lambda c: _t(c, look.tint)
    cam = R.Cam(X0, Y0, s, p.yaw if yaw is None else yaw, cam_pitch, persp, flip)
    S = R.solve(p)
    pr = cam.proj
    A = {}
    hood = (T(PAL['hood']), T(PAL['hood_hi']), T(PAL['hood_sh']))
    pants = (T(PAL['pants']), T(PAL['pants_hi']), T(PAL['pants']))
    parts = []

    if ground_shadow > 0:
        gc, _, gk = pr(V((p.foot[1][0] + p.foot[-1][0]) / 2, 0, (p.foot[1][2] + p.foot[-1][2]) / 2))
        spread = abs(pr(p.foot[1] * V(1, 0, 1))[0][0] - pr(p.foot[-1] * V(1, 0, 1))[0][0])
        w = 150 * cam.s + spread * 0.6
        cv.drawOval(skia.Rect(gc[0] - w, gc[1] - 26 * cam.s, gc[0] + w, gc[1] + 26 * cam.s), P((0, 0, 8), ground_shadow, blur=14 * cam.s))

    def depth(v):
        return pr(v)[1]

    # legs
    for sd in (1, -1):
        hp_, kp_, ap_ = pr(S.hip[sd])[0], pr(S.knee[sd])[0], pr(S.ankle[sd])[0]
        z = (depth(S.hip[sd]) + depth(S.knee[sd]) + depth(S.ankle[sd])) / 3

        def leg(sd=sd, hp_=hp_, kp_=kp_, ap_=ap_):
            pa = cap(hp_, kp_, 50 * cam.s, 44 * cam.s)
            pa = skia.Op(pa, cap(kp_, ap_, 44 * cam.s, 38 * cam.s), skia.PathOp.kUnion_PathOp) or pa
            lit_part(cv, pa, pants, look, s)
        parts.append((z - 30, leg))

        # shoe = rounded hull of a projected box
        heel, toe = S.heel[sd], S.toe[sd]
        fwd = nrm(toe - heel)
        side = nrm(np.cross(V(0, 1, 0), fwd))
        upv = nrm(np.cross(fwd, side))
        corners = []
        for a_ in (-36, 130):
            for b_ in (-58, 58):
                for c_ in (0, 54):
                    corners.append(pr(heel + fwd * a_ + side * b_ + upv * (c_ - 18))[0])
        zf = (depth(heel) + depth(toe)) / 2

        def shoe(corners=corners, heel=heel, fwd=fwd, side=side, upv=upv):
            pa = hull_path(corners, corner=34 * cam.s)
            lit_part(cv, pa, (T(PAL['shoe']), T(PAL['shoe_hi']), shade(T(PAL['shoe']), 0.82)), look, s)
            sole = [pr(heel + fwd * a_ + side * b_ + upv * (-18))[0] for a_ in (-36, 130) for b_ in (-50, 50)]
            sole += [pr(heel + fwd * a_ + side * b_ + upv * (-4))[0] for a_ in (-36, 130) for b_ in (-50, 50)]
            cv.save(); cv.clipPath(pa, skia.ClipOp.kIntersect, True)
            cv.drawPath(hull_path(sole, 0.3), P(T(PAL['sole']), 0.9))
            cv.restore()
        parts.append((zf - 10, shoe))

    # torso (hoodie) as hull of rings
    hem_c = S.P + S.u * -40
    rings = ring(hem_c, S.pr, S.pf, 118, 70) + ring(S.P + S.u * 140, S.r, S.f, 122, 76) + \
        ring(S.S0 - S.u * 18, S.r, S.f, 120, 70) + ring(S.S0 + S.u * 14, S.r, S.f, 82, 52)
    tz = depth(S.chest)
    torso_pts = [pr(v)[0] for v in rings]
    _, _, front_d = cam.dirproj(S.f)

    def torso():
        pa = hull_path(torso_pts, 0.45)
        lit_part(cv, pa, hood, look, s)
        cv.save(); cv.clipPath(pa, skia.ClipOp.kIntersect, True)
        # hem band + kangaroo pocket seam (only on the front)
        hem = [pr(v)[0] for v in ring(hem_c + S.u * 26, S.pr, S.pf, 120, 72, 32)]
        hem_lo = [pr(v)[0] for v in ring(hem_c - S.u * 10, S.pr, S.pf, 120, 72, 32)]
        cv.drawPath(hull_path(hem + hem_lo, 0.4), P(T(PAL['hood_sh']), 0.55))
        plain = CHAR.get("uniform") or CHAR.get("coat")
        if front_d > 0.15 and not plain:
            pk = [S.P + S.u * 30 + S.r * -70 + S.f * 74, S.P + S.u * 30 + S.r * 70 + S.f * 74,
                  S.P + S.u * 130 + S.r * 45 + S.f * 78, S.P + S.u * 130 + S.r * -45 + S.f * 78]
            pp = [pr(v)[0] for v in pk]
            cv.drawPath(path_poly(pp), P(T(PAL['hood_sh']), 0.35 * min(1, front_d * 2), style='stroke', width=3.0 * cam.s * 2))
        cv.restore()
        # hood collar: dark U around the neck (front half)
        col_pts = []
        for t_ in np.linspace(-math.pi * 0.95, -math.pi * 0.05, 18):
            v = S.S0 + S.u * 6 + S.r * (64 * math.cos(t_)) + S.f * (-48 * math.sin(t_))
            col_pts.append(pr(v)[0])
        if front_d > -0.2:
            pc = skia.Path(); pc.moveTo(*col_pts[0])
            for q in col_pts[1:]:
                pc.lineTo(*q)
            cv.drawPath(pc, P(T(PAL['collar']), min(1, (front_d + 0.2) * 3), style='stroke', width=13 * cam.s))
        # drawstrings with a little swing (p.hem = secondary motion)
        if front_d > 0.2 and not plain:
            for sd in (1, -1):
                top = S.S0 + S.u * -6 + S.r * (22 * sd) + S.f * 52
                bot = top - S.u * 120 + S.f * 10 + S.r * (p.hem * 30 + sd * 4)
                a_, b_ = pr(top)[0], pr(bot)[0]
                cv.drawLine(a_[0], a_[1], b_[0], b_[1], P(T(PAL['string']), min(1, (front_d - 0.2) * 4), style='stroke', width=5 * cam.s))
        # back view: hood lump on the upper back
        if front_d < -0.25 and not plain:
            hb = ring(S.S0 - S.f * 52 - S.u * 44, S.r, S.u, 92, 62, 18)
            pa2 = hull_path([pr(v)[0] for v in hb], 0.5)
            cv.drawPath(pa2, P(mix(T(PAL['hood']), T(PAL['hood_sh']), 0.5), min(1, (-front_d - 0.25) * 3)))
            cv.drawPath(pa2, P(T(PAL['collar']), 0.5, style='stroke', width=3 * cam.s))
        if plain and front_d > 0.1:
            fa = min(1, (front_d - 0.1) * 4)
            # placket + buttons; uniform gets lapels and a breast pocket
            a_, b_ = pr(S.S0 + S.f * 66 - S.u * 30)[0], pr(S.P + S.f * 76 - S.u * 30)[0]
            cv.drawLine(a_[0], a_[1], b_[0], b_[1], P(T(PAL['hood_sh']), 0.8 * fa, style='stroke', width=4 * cam.s))
            for k in range(4):
                q = pr(S.S0 + S.f * 70 - S.u * (60 + k * 62) + S.r * 10)[0]
                cv.drawCircle(q[0], q[1], 7 * cam.s, P(T(PAL['string']), 0.9 * fa))
            for sd in (1, -1):
                lap = [pr(S.S0 + S.r * (20 * sd) + S.f * 58 + S.u * 4)[0], pr(S.S0 + S.r * (70 * sd) + S.f * 40 - S.u * 4)[0],
                       pr(S.S0 + S.r * (10 * sd) + S.f * 68 - S.u * 120)[0]]
                cv.drawPath(path_poly(lap), P(T(PAL['hood_hi']) if CHAR.get('uniform') else T(PAL['collar']), 0.9 * fa))
                cv.drawPath(path_poly(lap), P(T(PAL['hood_sh']), 0.8 * fa, style='stroke', width=3 * cam.s))
            if CHAR.get('uniform'):
                pk = [pr(S.S0 + S.r * -60 + S.f * 66 - S.u * v_)[0] for v_ in (70, 110)]
                cv.drawLine(pk[0][0] - 26 * cam.s, pk[0][1], pk[0][0] + 26 * cam.s, pk[0][1], P(T(PAL['hood_sh']), fa, style='stroke', width=4 * cam.s))
        if CHAR.get('backpack') and front_d > -0.3:
            # shoulder straps over the hoodie
            for sd in (1, -1):
                st = [pr(S.S0 + S.r * (52 * sd) + S.u * 10)[0], pr(S.S0 + S.r * (60 * sd) + S.f * 62 - S.u * 60)[0],
                      pr(S.S0 + S.r * (66 * sd) + S.f * 60 - S.u * 190)[0]]
                cv.drawPath(path_smooth(st, close=False), P(T((20, 20, 24)), min(1, (front_d + 0.3) * 3), style='stroke', width=17 * cam.s))
    parts.append((tz, torso))

    if CHAR.get('backpack'):
        bc = S.chest - S.f * 92 - S.u * 20
        bpts = [pr(bc + S.r * x_ + S.u * y_ + S.f * z_)[0] for x_ in (-88, 88) for y_ in (-150, 130) for z_ in (-40, 40)]
        top = [pr(bc + S.r * x_ + S.u * 130 + S.f * z_)[0] for x_ in (-70, 70) for z_ in (-30, 30)]

        def pack(bpts=bpts):
            pa = hull_path(bpts, corner=30 * cam.s)
            lit_part(cv, pa, (T((44, 46, 56)), T((64, 66, 78)), T((26, 26, 32))), look, s)
            # front pocket + zip
            pk = [pr(bc + S.r * x_ + S.u * y_ - S.f * 44)[0] for x_ in (-60, 60) for y_ in (-130, -20)]
            if front_d < 0.2:
                cv.drawPath(hull_path(pk, corner=16 * cam.s), P(T((30, 30, 38)), min(1, (0.2 - front_d) * 3)))
                z1, z2 = pr(bc + S.r * -60 + S.u * 0 - S.f * 44)[0], pr(bc + S.r * 60 + S.u * 0 - S.f * 44)[0]
                cv.drawLine(z1[0], z1[1], z2[0], z2[1], P(T((150, 150, 160)), 0.6 * min(1, (0.2 - front_d) * 3), style='stroke', width=3 * cam.s))
        parts.append((depth(bc), pack))

    # neck
    nz = depth(S.N)

    def neck():
        a_, b_ = pr(S.S0 - S.u * 10)[0], pr(S.N + S.u * 50)[0]
        pa = cap(a_, b_, 30 * cam.s, 30 * cam.s)
        cv.drawPath(pa, P(T(PAL['skin_sh'])))
    parts.append((tz - 1000, neck))

    # arms
    for sd in (1, -1):
        shp, elp, wrp = pr(S.sh[sd])[0], pr(S.elbow[sd])[0], pr(S.wrist[sd])[0]
        z = (depth(S.sh[sd]) + depth(S.elbow[sd]) * 2 + depth(S.wrist[sd]) * 2) / 5

        def arm(sd=sd, shp=shp, elp=elp, wrp=wrp):
            pa = cap(shp, elp, 42 * cam.s, 37 * cam.s)
            pa = skia.Op(pa, cap(elp, wrp, 37 * cam.s, 33 * cam.s), skia.PathOp.kUnion_PathOp) or pa
            lit_part(cv, pa, hood, look, s)
            cv.drawPath(pa, P(T(PAL['hood_sh']), 0.6, style='stroke', width=2.5 * cam.s))
            # cuff
            dx, dy = wrp[0] - elp[0], wrp[1] - elp[1]
            Ld = math.hypot(dx, dy) or 1
            cx_, cy_ = wrp[0] - dx / Ld * 10 * cam.s, wrp[1] - dy / Ld * 10 * cam.s
            cv.drawLine(cx_ - dy / Ld * 32 * cam.s, cy_ + dx / Ld * 32 * cam.s, cx_ + dy / Ld * 32 * cam.s, cy_ - dx / Ld * 32 * cam.s,
                        P(T(PAL['hood_sh']), 0.8, style='stroke', width=6 * cam.s))
        hz = depth(S.handc[sd])

        def hand(sd=sd):
            A.setdefault('hand', {})[sd] = draw_hand(cv, S, p, sd, cam, s, look)
            if props and props.get(sd):
                props[sd](cv, A['hand'][sd], cam, S, sd)
        parts.append((z + 2, arm))
        parts.append((max(z, hz) + 3, hand))

    hz = depth(S.H)

    def head():
        A['mouth'] = draw_head(cv, S, p, cam, s, look, black_eyes)
    parts.append((hz + (60 if front_d > -0.3 else -5), head))

    parts.sort(key=lambda q: q[0])
    for _, fn in parts:
        fn()
    A['head'] = pr(S.H)[0]
    A['chest'] = pr(S.chest)[0]
    A['pelvis'] = pr(S.P)[0]
    A['feet'] = {sd: pr(S.ankle[sd])[0] for sd in (1, -1)}
    A['wrist'] = {sd: pr(S.wrist[sd])[0] for sd in (1, -1)}
    A['sh'] = {sd: pr(S.sh[sd])[0] for sd in (1, -1)}
    A['skel'] = S
    A['cam'] = cam
    A['head_r'] = HEAD_R * cam.s
    return A
