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

HEAD_R = R.HEAD_R
R.NECK_H = 282.0   # head sits on the hood collar like the PAPA characters


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
    # front fringe -> temple -> above ear -> nape
    base = np.interp(a, [0.0, 0.45, 0.95, 1.35, 1.75, 2.3, 3.2], [0.66, 0.62, 0.50, 0.26, 0.10, -0.28, -0.40])
    # side-swept fringe: hangs lower on the character's right (phi<0 = screen-left when facing camera)
    sweep = -0.06 * np.exp(-((phi + 0.30) / 0.32) ** 2) + 0.04 * np.exp(-((phi - 0.45) / 0.25) ** 2)
    # messy teeth only on the fringe
    teeth = 0.0  # PAPA hair is a smooth helmet, no jagged fringe
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
    cv.restore()   # head clip

    # ---- hair (rasterised on the head sphere)
    draw_hair(cv, S, cam, hc, Rp, hr_c, hu_c, hf_c, look, T)
    return A_mouth


def draw_hair(cv, S, cam, hc, Rp, hr_c, hu_c, hf_c, look, T):
    RH = 1.07                          # hair shell radius (volume over the skull)
    pad = int(Rp * RH + 4)
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
    tuft = 1.0
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
        if front_d > 0.15:
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
        if front_d > 0.2:
            for sd in (1, -1):
                top = S.S0 + S.u * -6 + S.r * (22 * sd) + S.f * 52
                bot = top - S.u * 120 + S.f * 10 + S.r * (p.hem * 30 + sd * 4)
                a_, b_ = pr(top)[0], pr(bot)[0]
                cv.drawLine(a_[0], a_[1], b_[0], b_[1], P(T(PAL['string']), min(1, (front_d - 0.2) * 4), style='stroke', width=5 * cam.s))
        # back view: hood lump on the upper back
        if front_d < -0.25:
            hb = ring(S.S0 - S.f * 52 - S.u * 44, S.r, S.u, 92, 62, 18)
            pa2 = hull_path([pr(v)[0] for v in hb], 0.5)
            cv.drawPath(pa2, P(mix(T(PAL['hood']), T(PAL['hood_sh']), 0.5), min(1, (-front_d - 0.25) * 3)))
            cv.drawPath(pa2, P(T(PAL['collar']), 0.5, style='stroke', width=3 * cam.s))
    parts.append((tz, torso))

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
