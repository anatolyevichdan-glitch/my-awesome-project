"""Procedural character rigs: hero / doppelganger (3D skeleton -> 2.5D draw) and the shadow entity."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HAIR = (21, 18, 20)
SKIN = (208, 192, 186)
JACKET = (62, 64, 71)
JACKET_HI = (96, 102, 112)
PANTS = (15, 15, 19)
SHOE = (26, 26, 30)
SOLE = (78, 80, 88)


def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)


def shade(c, k, tint=(1, 1, 1)):
    return tuple(int(clamp(c[i] * k * tint[i], 0, 255)) for i in range(3))


# ---------------------------------------------------------------- expressions
EXPR = {
    'calm':    dict(open=0.82, brow=0.0, knit=0.0, mo=0.0, curve=0.05, gx=0, gy=0, fear=0),
    'unaware': dict(open=0.78, brow=0.0, knit=0.0, mo=0.0, curve=0.0, gx=0.1, gy=-0.05, fear=0),
    'tense':   dict(open=0.9, brow=-0.15, knit=0.6, mo=0.0, curve=-0.35, gx=0, gy=-0.1, fear=0.2),
    'alert':   dict(open=1.05, brow=0.25, knit=0.2, mo=0.05, curve=-0.2, gx=0, gy=0, fear=0.35),
    'fear':    dict(open=1.25, brow=0.7, knit=0.55, mo=0.35, curve=-0.5, gx=0, gy=0, fear=0.8),
    'terror':  dict(open=1.45, brow=1.0, knit=0.7, mo=0.85, curve=-0.7, gx=0, gy=0, fear=1.0),
    'relief':  dict(open=0.55, brow=0.15, knit=-0.2, mo=0.12, curve=0.1, gx=0, gy=0.1, fear=0),
    'blink':   dict(open=0.05, brow=0.0, knit=0.0, mo=0.0, curve=0.0, gx=0, gy=0, fear=0),
    'grim':    dict(open=0.95, brow=-0.1, knit=0.8, mo=0.1, curve=-0.4, gx=0, gy=0, fear=0.4),
}


def expr(name, **kw):
    e = dict(EXPR[name]); e.update(kw); return e


def expr_mix(a, b, t):
    A = EXPR[a] if isinstance(a, str) else a
    B = EXPR[b] if isinstance(b, str) else b
    return {k: lerp(A[k], B[k], t) for k in A}


# ---------------------------------------------------------------- primitives
def capsule(d, p1, p2, w, col, hl=None, lx=-1):
    w = max(1.0, w); r = w / 2
    d.line([p1, p2], fill=col, width=int(round(w)))
    for p in (p1, p2):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
    if hl is not None and w > 6:
        o = (lx * w * 0.17, -w * 0.12); ww = w * 0.55
        a = (p1[0] + o[0], p1[1] + o[1]); b = (p2[0] + o[0], p2[1] + o[1])
        d.line([a, b], fill=hl, width=int(round(ww)))
        for p in (a, b):
            d.ellipse([p[0] - ww / 2, p[1] - ww / 2, p[0] + ww / 2, p[1] + ww / 2], fill=hl)


def chaikin(pts, n=2):
    for _ in range(n):
        out = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1])); out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = out
    return pts


def hull(pts):
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(pts) < 3: return pts
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def ik3(r, t, l1, l2, pole):
    r = np.array(r, float); t = np.array(t, float)
    v = t - r; d = np.linalg.norm(v)
    d = clamp(d, abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    u = v / (np.linalg.norm(v) + 1e-9)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0))
    pv = np.array(pole, float); pv = pv - u * np.dot(pv, u)
    pv = pv / (np.linalg.norm(pv) + 1e-9)
    return r + u * a + pv * h, r + u * d


# ---------------------------------------------------------------- hero skeleton
def hero_joints(P):
    """P: p phase, amp (walk 0..1), run (0..1), lean, twist, hy, armL/armR=(wrist target, pole), head=(yaw,pitch,roll)"""
    p = P.get('p', 0.0); amp = P.get('amp', 0.0); run = P.get('run', 0.0)
    lean = P.get('lean', 0.0) + 0.22 * run * amp; twist = P.get('twist', 0.0)
    S = (0.30 + 0.32 * run) * amp; lift = (0.07 + 0.21 * run) * amp
    hip_h = 0.93 - 0.07 * run * amp + P.get('hy', 0.0)
    bob = (0.028 + 0.032 * run) * amp
    hip_y = hip_h - bob * (0.5 + 0.5 * math.cos(4 * math.pi * p))
    sway = 0.018 * amp * math.sin(2 * math.pi * p)
    J = {}
    for s, name in ((1, 'L'), (-1, 'R')):
        ph = (p + (0.0 if s > 0 else 0.5)) % 1.0
        if amp < 1e-3:
            fz, fy = 0.0, 0.0
        elif ph < 0.5:
            fz, fy = S * (1 - 4 * ph), 0.0
        else:
            v = (ph - 0.5) / 0.5
            fz = -S + 2 * S * (0.5 - 0.5 * math.cos(math.pi * v)); fy = lift * math.sin(math.pi * v)
        so = P.get('stance', 0.0)
        hip = (s * 0.095 + sway, hip_y, 0.0)
        ank = (s * 0.10 + sway * 0.5, 0.075 + fy, fz + (so if s > 0 else -so * 0.4))
        knee, ank2 = ik3(hip, ank, 0.46, 0.46, (s * 0.12, 0, 1))
        ppitch = 0.0
        if amp > 1e-3:
            ppitch = (-0.3 * math.sin(math.pi * (ph - 0.5) / 0.5)) if ph >= 0.5 else 0.25 * clamp(ph / 0.5)
        toe = (ank2[0], ank2[1] - 0.045 - 0.1 * ppitch, ank2[2] + 0.2)
        heel = (ank2[0], ank2[1] - 0.02, ank2[2] - 0.05)
        J['hip' + name] = hip; J['knee' + name] = tuple(knee); J['ank' + name] = tuple(ank2)
        J['toe' + name] = toe; J['heel' + name] = heel
    hipc = np.array([sway, hip_y, 0.0])
    cl, sl = math.cos(lean), math.sin(lean)
    ct, st = math.cos(twist), math.sin(twist)

    def up(x, y, z=0.0):
        xx = x * ct + z * st; zz = -x * st + z * ct
        return (hipc[0] + xx, hipc[1] + y * cl, hipc[2] + y * sl + zz)

    J['shL'] = up(0.18, 0.50); J['shR'] = up(-0.18, 0.50)
    J['hipc'] = tuple(hipc); J['shc'] = up(0, 0.52)
    J['neck'] = up(0, 0.58, 0.01)
    J['head'] = up(0, 0.74, 0.03)
    J['headrot'] = P.get('head', (0, 0, 0))
    for s, name in ((1, 'L'), (-1, 'R')):
        sh = np.array(J['sh' + name])
        tgt = P.get('arm' + name)
        if tgt is not None:
            wr, pole = tgt
            el, wr2 = ik3(sh, wr, 0.29, 0.27, pole)
        else:
            a = -(0.50) * amp * math.cos(2 * math.pi * (p + (0.5 if s > 0 else 0.0)))
            a = a * (1 + 0.15 * run) + 0.05
            b = 0.25 * amp + 0.18 + 0.2 * max(0, a)
            if run > 0.01 and amp > 0.01:
                b = (0.3 + 1.2 * run) + 0.15 * run * math.sin(4 * math.pi * p)
            uv = np.array([0.08 * s, -math.cos(a), math.sin(a)]); uv /= np.linalg.norm(uv)
            el = sh + 0.29 * uv
            a2 = a + b
            fo = np.array([0.04 * s, -math.cos(a2), math.sin(a2)]); fo /= np.linalg.norm(fo)
            wr2 = el + 0.27 * fo
        dd = wr2 - el; dd = dd / (np.linalg.norm(dd) + 1e-9)
        J['el' + name] = tuple(el); J['wr' + name] = tuple(wr2); J['hand' + name] = tuple(wr2 + dd * 0.085)
    return J


# ---------------------------------------------------------------- head sprite
_LOCKS = None


def _locks():
    global _LOCKS
    if _LOCKS is None:
        rnd = random.Random(7)
        L = []
        for i in range(15):
            ang = lerp(-1.25, 1.25, i / 14) + rnd.uniform(-0.05, 0.05)
            L.append(('top', ang, rnd.uniform(0.06, 0.2), rnd.uniform(0.26, 0.4), rnd.uniform(-0.5, 0.5)))
        for i in range(8):
            x = lerp(-0.6, 0.6, i / 7) + rnd.uniform(-0.05, 0.05)
            L.append(('fringe', x, rnd.uniform(0.14, 0.3), rnd.uniform(0.2, 0.3), rnd.uniform(-0.4, 0.4)))
        _LOCKS = L
    return _LOCKS


def head_sprite(R, yaw=0.0, pitch=0.0, e=None, kind='hero', lit=1.0, tint=(1, 1, 1), ldir=-1, sweat=0.0, shade_on=True):
    """RGBA sprite (3.2R square) centred on the head. yaw 0 = faces camera, pi = back of head."""
    e = e or EXPR['calm']
    R = float(R)
    S = int(R * 3.2) | 1; c = S / 2.0
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy, sy = math.cos(yaw), math.sin(yaw); cp, sp = math.cos(pitch), math.sin(pitch)

    def P(x, y, z):
        y2 = y * cp - z * sp; z2 = y * sp + z * cp
        return (c + (x * cy + z2 * sy) * R, c - y2 * R), (-x * sy + z2 * cy)

    skin = shade(SKIN, lit, tint); hair = shade(HAIR, max(lit, 0.5), tint)
    hair_hi = shade((70, 76, 90), lit, tint)
    wsk = math.sqrt((0.8 * cy) ** 2 + (0.92 * sy) ** 2) * R
    hsk = (1.0 * cp + 0.1 * abs(sp)) * R
    d.ellipse([c - wsk, c - hsk, c + wsk, c + hsk], fill=hair)
    for sx in (-1, 1):
        pt, Z = P(sx * 0.80, -0.08, -0.05)
        if Z > -0.25:
            ew, eh = 0.14 * R * max(0.25, abs(sy) + 0.3), 0.26 * R
            d.ellipse([pt[0] - ew, pt[1] - eh, pt[0] + ew, pt[1] + eh], fill=shade(skin, 0.85))
    face_visible = cy > -0.05
    outline = [(-0.62, 0.42), (-0.50, 0.66), (-0.2, 0.78), (0.2, 0.78), (0.5, 0.66), (0.62, 0.42),
               (0.78, 0.15), (0.77, -0.15), (0.70, -0.48), (0.52, -0.84), (0.26, -1.05), (0, -1.12),
               (-0.26, -1.05), (-0.52, -0.84), (-0.70, -0.48), (-0.77, -0.15), (-0.78, 0.15)]
    facepts = []
    if face_visible:
        for (x, y) in outline:
            z = 0.92 * math.sqrt(max(0.03, 1 - (x / 0.84) ** 2)) * (1 - 0.12 * y * y)
            pt, Z = P(x, y, z)
            if Z > -0.04: facepts.append(pt)
        if len(facepts) >= 3:
            facepts = chaikin(facepts, 2)
            d.polygon(facepts, fill=skin)
    if abs(sy) > 0.4 and cy > -0.2:
        prof = [(0.62, 0.70), (0.88, 0.35), (0.92, 0.12), (0.95, -0.05), (0.97, -0.3), (1.0, -0.45), (1.0, -0.62),
                (0.92, -0.78), (0.85, -1.08), (0.5, -1.15), (0.1, -0.95), (-0.05, 0.0), (0.1, 0.6)]
        sgn = 1 if sy > 0 else -1
        pp_ = [(c + zz * sy * R * 0.0 + (zz * sy) * R, c - yy * R * cp) for zz, yy in prof]
        d.polygon(pp_, fill=skin)
        facepts = facepts or pp_
    if face_visible and shade_on and len(facepts) >= 3:
        sh = Image.new('L', (S, S), 0); sd = ImageDraw.Draw(sh)
        hl = Image.new('L', (S, S), 0); hd = ImageDraw.Draw(hl)
        side = -ldir
        far = [P(side * 0.95, 0.7, 0.2)[0], P(side * 0.35, 0.5, 0.9)[0], P(side * 0.3, -0.4, 1.0)[0],
               P(side * 0.4, -1.1, 0.7)[0], P(side * 1.0, -1.1, 0.0)[0], P(side * 1.0, 0.7, 0.0)[0]]
        sd.polygon(far, fill=150)
        for sx in (-1, 1):
            pt, _ = P(sx * 0.37, 0.0, 0.8); rr = 0.30 * R
            sd.ellipse([pt[0] - rr, pt[1] - rr * 0.8, pt[0] + rr, pt[1] + rr * 0.8], fill=95 + int(60 * e['fear']))
            pt, _ = P(sx * 0.50, -0.45, 0.7); rr = 0.22 * R
            sd.ellipse([pt[0] - rr, pt[1] - rr, pt[0] + rr, pt[1] + rr], fill=45)
        pt, _ = P(0, -0.34, 0.95); sd.ellipse([pt[0] - 0.14 * R, pt[1] - 0.05 * R, pt[0] + 0.14 * R, pt[1] + 0.1 * R], fill=110)
        pt, _ = P(0, -0.82, 0.8); sd.ellipse([pt[0] - 0.25 * R, pt[1] - 0.05 * R, pt[0] + 0.25 * R, pt[1] + 0.07 * R], fill=70)
        sd.rectangle([0, P(0, -1.04, 0.5)[0][1], S, S], fill=170)
        pt, _ = P(ldir * 0.45, -0.1, 0.9); rr = 0.25 * R
        hd.ellipse([pt[0] - rr, pt[1] - rr * 1.2, pt[0] + rr, pt[1] + rr * 1.2], fill=70)
        pt, _ = P(0, -0.2, 1.1); hd.ellipse([pt[0] - 0.07 * R, pt[1] - 0.12 * R, pt[0] + 0.07 * R, pt[1] + 0.1 * R], fill=80)
        pt, _ = P(0, 0.55, 0.85); hd.ellipse([pt[0] - 0.3 * R, pt[1] - 0.12 * R, pt[0] + 0.3 * R, pt[1] + 0.12 * R], fill=45)
        mask = Image.new('L', (S, S), 0); ImageDraw.Draw(mask).polygon(facepts, fill=255)
        rad = max(1.0, R * 0.09)
        sh = sh.filter(ImageFilter.GaussianBlur(rad)); hl = hl.filter(ImageFilter.GaussianBlur(rad))
        arr = np.asarray(img).astype(np.float32)
        m = (np.asarray(mask).astype(np.float32) / 255.0)[..., None]
        k = 1 - (np.asarray(sh).astype(np.float32) / 255.0)[..., None] * 0.62
        k = k + (np.asarray(hl).astype(np.float32) / 255.0)[..., None] * 0.55
        arr[..., :3] = np.clip(arr[..., :3] * (1 - m) + arr[..., :3] * k * m, 0, 255)
        img = Image.fromarray(arr.astype(np.uint8), 'RGBA'); d = ImageDraw.Draw(img)
    for kind_, a_, ln, wd, bend in _locks():
        if kind_ == 'top':
            x = math.sin(a_) * 0.85; y = math.cos(a_) * 0.95
            z = 0.1 + 0.16 * math.cos(a_)
            base, _ = P(x, y, z)
            tip, _ = P(x * (1 + ln * 0.9) + bend * 0.3, y + ln, z)
            nx = wd * 0.5 * R
            capsule(d, base, tip, max(2.0, nx * 1.5), hair)
        else:
            if cy < 0.15: continue
            x = a_; y = 0.74 - 0.03 * abs(x)
            base, _ = P(x * 0.9, y + 0.05, 0.85)
            tip, _ = P(x * 0.9 + bend * 0.4, y - ln * (0.7 if abs(x) < 0.45 else 0.35), 0.95)
            nx = wd * 0.5 * R * cy
            capsule(d, base, tip, max(2.0, nx * 1.3), hair)
    if cy < 0.3:
        pt, _ = P(-ldir * 0.3, 0.55, -0.7)
        d.ellipse([pt[0] - R * .35, pt[1] - R * .12, pt[0] + R * .35, pt[1] + R * .12], fill=hair_hi + (90,))
    if not face_visible or cy < 0.05:
        return img
    # ------------------------------ features
    eyecol = (3, 3, 5) if kind == 'double' else None
    for sx in (-1, 1):
        ex, ey = sx * 0.37, 0.02 - 0.03 * e['fear']
        pt, Z = P(ex, ey, 0.84)
        if Z < 0.05: continue
        kx = clamp(Z / 0.9, 0.18, 1.0)
        W = 0.34 * R * kx; H = 0.15 * R * clamp(e['open'], 0.04, 1.6)
        q = 3 if R < 260 else 2
        pw, ph = int(W * 2.4 * q) | 1, int(0.7 * R * q) | 1
        cx_, cy_ = pw / 2, ph / 2
        n = 22
        up_, lo_ = [], []
        for i in range(n + 1):
            t = i / n; xx = (t - 0.5) * 2 * W * q
            top = H * q * (1 - (2 * t - 1) ** 2) ** 0.8
            tilt = (0.10 * (t - 0.5) * 2 * -sx) * R * q * 0.25
            up_.append((cx_ + xx, cy_ - top + tilt)); lo_.append((cx_ + xx, cy_ + top * 0.55 + tilt))
        almond = up_ + lo_[::-1]
        amask = Image.new('L', (pw, ph), 0); ImageDraw.Draw(amask).polygon(almond, fill=255)
        eye = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); ed = ImageDraw.Draw(eye)
        if eyecol:
            ed.polygon(almond, fill=eyecol)
            gl = W * 0.12 * q
            ed.ellipse([cx_ - W * 0.3 * q, cy_ - H * q * 0.5, cx_ - W * 0.3 * q + gl, cy_ - H * q * 0.5 + gl * 0.7], fill=(40, 48, 60))
        else:
            ed.polygon(almond, fill=shade((214, 218, 222), lit, tint))
            ir = W * 0.5 * q
            gx = clamp(e['gx'], -1, 1) * W * 0.42 * q
            gy = -clamp(e['gy'], -1, 1) * H * 0.3 * q
            ix, iy = cx_ + gx, cy_ + gy
            ed.ellipse([ix - ir, iy - ir, ix + ir, iy + ir], fill=shade((62, 74, 86), max(lit, 0.6), tint))
            ed.ellipse([ix - ir * 0.8, iy - ir * 0.8, ix + ir * 0.8, iy + ir * 0.8], fill=shade((86, 104, 118), max(lit, 0.6), tint))
            pr_ = ir * (0.30 if e['fear'] > 0.5 else 0.44)
            ed.ellipse([ix - pr_, iy - pr_, ix + pr_, iy + pr_], fill=(4, 4, 6))
            ed.ellipse([ix - ir * 0.2, iy - ir * 0.65, ix + ir * 0.1, iy - ir * 0.35], fill=(235, 240, 250))
        ed.polygon(up_ + [(x, y + H * q * 0.45) for x, y in up_[::-1]], fill=(20, 16, 18, 150))
        eye.putalpha(amask)
        lids = Image.new('RGBA', (pw, ph), (0, 0, 0, 0)); ld = ImageDraw.Draw(lids)
        lw = max(1, int(R * q * 0.035))
        ld.line(up_, fill=(10, 8, 9, 255), width=lw)
        ld.line(lo_, fill=shade((120, 90, 90), lit, tint) + (150,), width=max(1, lw // 2))
        ld.line([(x, y - H * q * 0.5 - R * q * 0.04) for x, y in up_[3:-3]], fill=shade((90, 70, 70), lit, tint) + (110,), width=max(1, lw // 2))
        eye = Image.alpha_composite(eye, lids)
        eye = eye.resize((max(1, pw // q), max(1, ph // q)), Image.LANCZOS)
        img.alpha_composite(eye, (int(pt[0] - eye.width / 2), int(pt[1] - eye.height / 2)))
        by = 0.30 + 0.12 * e['brow']
        inner_y = by - 0.10 * e['knit'] + 0.07 * e['fear']
        outer_y = by + 0.04 * e['knit']
        pi_, _ = P(sx * 0.14, inner_y, 0.9); po_, _ = P(sx * 0.66, outer_y, 0.7)
        pm_, _ = P(sx * 0.40, max(inner_y, outer_y) + 0.05 + 0.04 * e['brow'], 0.88)
        bw = 0.05 * R
        bc = shade((24, 20, 20), max(lit, 0.6), tint) if kind != 'double' else (18, 16, 16)
        d.polygon([(pi_[0], pi_[1] - bw * 0.6), (pm_[0], pm_[1] - bw * 1.0), (po_[0], po_[1] - bw * 0.2),
                   (po_[0], po_[1] + bw * 0.4), (pm_[0], pm_[1] + bw * 0.5), (pi_[0], pi_[1] + bw * 0.8)], fill=bc)
    # nose
    tip, _ = P(0, -0.22, 1.18)
    nshade = shade(skin, 0.62)
    d.line([P(ldir * -0.07, 0.0, 0.98)[0], P(-ldir * 0.1, -0.26, 1.0)[0]], fill=nshade + (140,), width=max(1, int(R * 0.03)))
    d.ellipse([tip[0] - R * .11, tip[1] - R * .07, tip[0] + R * .11, tip[1] + R * .08], fill=shade(skin, 0.95))
    for sx in (-1, 1):
        pn, _ = P(sx * 0.085, -0.31, 1.0)
        d.ellipse([pn[0] - R * .04, pn[1] - R * .025, pn[0] + R * .04, pn[1] + R * .03], fill=shade(skin, 0.35))
    if abs(sy) > 0.5:
        a_, _ = P(0, 0.0, 0.96); b_, _ = P(0, -0.38, 1.0); t_, _ = P(0, -0.24, 1.32)
        d.polygon([a_, t_, b_], fill=skin)
    # mouth
    my = -0.64; mw = 0.30 + 0.05 * e['mo']; cv = e['curve']; mo = e['mo']
    left, _ = P(-mw, my - 0.05 * cv, 0.82); right, _ = P(mw, my - 0.05 * cv, 0.82)
    mid_u, _ = P(0, my + 0.02 + 0.03 * mo, 0.95)
    lowc = shade((158, 104, 104), lit * 0.9, tint); lipc = shade((150, 100, 102), lit * 0.85, tint)
    if mo > 0.12:
        low2, _ = P(0, my - 0.02 - 0.20 * mo, 0.95)
        d.polygon([left, mid_u, right, low2], fill=(18, 8, 10))
        d.line([left, mid_u, right], fill=lipc, width=max(1, int(R * 0.05)))
        d.line([left, low2, right], fill=lowc, width=max(1, int(R * 0.06)))
        if mo > 0.5:
            tu, _ = P(0, my + 0.0, 0.94); t2, _ = P(0, my - 0.06, 0.94)
            d.rectangle([tu[0] - R * .18, tu[1], tu[0] + R * .18, t2[1] + R * 0.02], fill=shade((196, 190, 184), lit * 0.7, tint))
    else:
        d.line([left, mid_u, right], fill=shade((96, 56, 58), lit, tint), width=max(1, int(R * 0.05)))
        lp, _ = P(0, my - 0.12, 0.95)
        d.line([left, lp, right], fill=lowc, width=max(1, int(R * 0.045)))
        d.line([left, mid_u, right], fill=shade((70, 40, 42), lit, tint), width=max(1, int(R * 0.03)))
    if sweat > 0.01:
        for (x, y) in ((-0.55, 0.5), (0.6, 0.3), (-0.2, 0.7)):
            pt, _ = P(x, y - 0.35 * sweat * ((x * 7) % 1), 0.8)
            d.ellipse([pt[0] - R * .015, pt[1] - R * .02, pt[0] + R * .015, pt[1] + R * .03], fill=(190, 205, 220, 150))
    return img


# ---------------------------------------------------------------- hero render
def render_hero(d, layer, ox, oy, s, yaw, P, e=None, kind='hero', lit=1.0, tint=(1, 1, 1), ldir=-1, persp=0.10, sweat=0.0):
    """Draw figure on RGBA `layer` (d = ImageDraw of layer), feet at (ox,oy), s px/metre.
    yaw: 0 faces camera, pi back to camera, pi/2 faces screen-right."""
    J = hero_joints(P)
    cy, sy = math.cos(yaw), math.sin(yaw)

    def pr(pt):
        x, y, z = pt
        X = x * cy + z * sy; Z = -x * sy + z * cy
        k = 1.0 / (1 - persp * Z)
        return (ox + X * s * k, oy - y * s * k), Z, k

    C = lambda base: shade(base, lit, tint)
    parts = []
    add = lambda depth, fn: parts.append((depth, fn))
    jacket, jhi = C(JACKET), C(JACKET_HI); pants, shoe, sole = C(PANTS), C(SHOE), C(SOLE)
    pants_hi = shade((46, 50, 62), lit, tint)
    skin_c = C(SKIN)
    for nm in ('L', 'R'):
        h = pr(J['hip' + nm]); k_ = pr(J['knee' + nm]); a_ = pr(J['ank' + nm]); t_ = pr(J['toe' + nm]); hl_ = pr(J['heel' + nm])
        add((h[1] + k_[1]) / 2, lambda h=h, k_=k_: capsule(d, h[0], k_[0], 0.15 * s * h[2], pants, pants_hi, ldir))
        add((k_[1] + a_[1]) / 2, lambda k_=k_, a_=a_: capsule(d, k_[0], a_[0], 0.108 * s * k_[2], pants, pants_hi, ldir))

        def shoe_draw(a_=a_, t_=t_, hl_=hl_):
            capsule(d, hl_[0], t_[0], 0.105 * s * a_[2], shoe)
            capsule(d, (hl_[0][0], hl_[0][1] + 0.03 * s), (t_[0][0], t_[0][1] + 0.035 * s), 0.028 * s * a_[2], sole)
        add((a_[1] + t_[1]) / 2 + 0.05, shoe_draw)
        sh = pr(J['sh' + nm]); el = pr(J['el' + nm]); wr = pr(J['wr' + nm]); hd_ = pr(J['hand' + nm])
        add((sh[1] + el[1]) / 2 + 0.02, lambda sh=sh, el=el: capsule(d, sh[0], el[0], 0.105 * s * sh[2], jacket, jhi, ldir))
        add((el[1] + wr[1]) / 2 + 0.02, lambda el=el, wr=wr: capsule(d, el[0], wr[0], 0.088 * s * el[2], jacket, jhi, ldir))
        add((wr[1] + hd_[1]) / 2 + 0.03, lambda wr=wr, hd_=hd_: capsule(d, wr[0], hd_[0], 0.072 * s * wr[2], skin_c, None))
    hc = np.array(J['hipc'])
    sL, sR = np.array(J['shL']), np.array(J['shR'])
    pts3 = []
    for sgn in (1, -1):
        sh = sL if sgn > 0 else sR
        for dz in (-0.11, 0.11): pts3.append(tuple(sh + np.array([sgn * 0.015, 0.06, dz])))
        hp = np.array([hc[0] + sgn * 0.15, hc[1] - 0.04, 0])
        for dz in (-0.1, 0.1): pts3.append(tuple(hp + np.array([0, 0, dz])))
        pts3.append(tuple((sh * 0.5 + hp * 0.5) + np.array([sgn * 0.035, 0, 0.0])))
    pp = [pr(p_) for p_ in pts3]

    def torso():
        poly = hull([q[0] for q in pp])
        d.polygon(poly, fill=jacket); d.line(poly + [poly[0]], fill=jacket, width=max(2, int(0.07 * s)), joint='curve')
        hem = hc[1] - 0.03
        a1 = pr((-0.175, hem + 0.07, 0.0)); a2 = pr((0.175, hem + 0.07, 0.0))
        d.line([a1[0], a2[0]], fill=shade(JACKET, lit * 0.6, tint), width=max(1, int(0.03 * s)))
        ed = sorted(poly, key=lambda p: p[0] * -ldir)[:2]
        d.line([ed[0], ed[1]], fill=jhi, width=max(1, int(0.016 * s)))
        if cy > 0.15:
            top = pr((0, J['neck'][1] - 0.04, 0.13)); bot = pr((0, hem + 0.02, 0.11))
            d.line([top[0], bot[0]], fill=shade(JACKET, lit * 0.45, tint), width=max(1, int(0.014 * s)))
            for sg in (-1, 1):
                dr = pr((sg * 0.05, J['neck'][1] - 0.12, 0.13)); dr2 = pr((sg * 0.055, J['neck'][1] - 0.28, 0.13))
                d.line([dr[0], dr2[0]], fill=shade((120, 120, 128), lit, tint), width=max(1, int(0.007 * s)))
    add(0.0, torso)
    nk = pr(J['neck']); hd = pr(J['head'])

    def hood():
        r = 0.115 * s * nk[2]
        hb = pr((J['neck'][0], J['neck'][1] + 0.01, J['neck'][2] - 0.07))
        d.ellipse([hb[0][0] - r * 1.35, hb[0][1] - r * 0.55, hb[0][0] + r * 1.35, hb[0][1] + r * 0.85], fill=C((50, 52, 58)))
        d.ellipse([hb[0][0] - r * 0.9, hb[0][1] - r * 0.25, hb[0][0] + r * 0.9, hb[0][1] + r * 0.55], fill=C((42, 44, 50)))
        nr = 0.045 * s * nk[2]
        d.rectangle([nk[0][0] - nr, nk[0][1] - 0.07 * s, nk[0][0] + nr, nk[0][1] + 0.02 * s], fill=shade(SKIN, lit * 0.8, tint))
    add(-0.02, hood)
    yaw_h = yaw + J['headrot'][0]
    R = 0.108 * s * hd[2]

    def head():
        sp_ = head_sprite(R, yaw_h, J['headrot'][1], e, kind, lit, tint, ldir, sweat, shade_on=(R > 30))
        roll = J['headrot'][2]
        if abs(roll) > 1e-3: sp_ = sp_.rotate(math.degrees(roll), resample=Image.BICUBIC)
        layer.alpha_composite(sp_, (int(hd[0][0] - sp_.width / 2), int(hd[0][1] - sp_.height / 2)))
    add(0.12, head)
    parts.sort(key=lambda t: t[0])
    for _, fn in parts: fn()
    return J, pr


# ---------------------------------------------------------------- entity
ENT = (4, 5, 8)
ENT_RIM = (22, 30, 44)


def entity_joints(P):
    p = P.get('p', 0.0); amp = P.get('amp', 0.0); lean = P.get('lean', 0.0); t = P.get('t', 0.0)
    S = 0.38 * amp
    hip_y = 1.18 - 0.02 * amp
    J = {}
    for s, name in ((1, 'L'), (-1, 'R')):
        ph = (p + (0 if s > 0 else 0.5)) % 1.0
        if amp < 1e-3: fz, fy = 0, 0
        elif ph < 0.5: fz, fy = S * (1 - 4 * ph), 0
        else:
            v = (ph - 0.5) / 0.5; fz = -S + 2 * S * (0.5 - 0.5 * math.cos(math.pi * v)); fy = 0.18 * math.sin(math.pi * v)
        hip = (s * 0.085, hip_y, 0)
        ank = (s * 0.09, 0.07 + fy, fz)
        knee, ank2 = ik3(hip, ank, 0.62, 0.62, (s * 0.1, 0, 1))
        J['hip' + name] = hip; J['knee' + name] = tuple(knee); J['ank' + name] = tuple(ank2)
        J['toe' + name] = (ank2[0], 0.03, ank2[2] + 0.25)
    cl, sl = math.cos(lean), math.sin(lean)
    up = lambda x, y, z=0.0: (x, hip_y + y * cl, y * sl + z * cl)
    J['shL'] = up(0.17, 0.66); J['shR'] = up(-0.17, 0.66); J['hipc'] = (0, hip_y, 0)
    J['neck'] = up(0, 0.72, 0.0)
    ntop = up(0, 1.02 + P.get('stretch', 0.0), 0.0)
    ht, hp, hr = P.get('head', (0, 0, 0))
    J['ntop'] = (ntop[0], ntop[1], ntop[2] + 0.08 * math.sin(hp))
    J['head'] = (ntop[0], ntop[1] + 0.14, ntop[2] + 0.1 * hp)
    J['headrot'] = (ht, hp, hr)
    for s, name in ((1, 'L'), (-1, 'R')):
        sh = np.array(J['sh' + name])
        sw = P.get('swing', 0.0)
        a = 0.06 * s + 0.12 * math.sin(2 * math.pi * p + s) * amp + sw * math.sin(t * 0.9 + s) + lean * 0.8
        wr = sh + np.array([s * (0.09 + P.get('spread', 0.0)), -1.30 * math.cos(a * 0.3), 0.15 + 1.1 * math.sin(a)])
        wr[2] += 0.05 * math.sin(t * 1.3 + s * 2)
        el, wr2 = ik3(sh, wr, 0.70, 0.70, (s * 0.6, 0.0, -1.0))
        J['el' + name] = tuple(el); J['wr' + name] = tuple(wr2)
    return J


def render_entity(d, layer, ox, oy, s, yaw, P, persp=0.14, lit=0.0):
    J = entity_joints(P)
    cy, sy = math.cos(yaw), math.sin(yaw)

    def pr(pt):
        x, y, z = pt
        X = x * cy + z * sy; Z = -x * sy + z * cy
        k = 1.0 / (1 - persp * Z)
        return (ox + X * s * k, oy - y * s * k), Z, k

    col = ENT; rim = shade(ENT_RIM, 0.45 + lit * 3)
    parts = []
    for nm in ('L', 'R'):
        h = pr(J['hip' + nm]); k_ = pr(J['knee' + nm]); a_ = pr(J['ank' + nm]); t_ = pr(J['toe' + nm])
        parts.append(((h[1] + k_[1]) / 2, lambda h=h, k_=k_: capsule(d, h[0], k_[0], 0.15 * s * h[2], col, rim, -1)))
        parts.append(((k_[1] + a_[1]) / 2, lambda k_=k_, a_=a_: capsule(d, k_[0], a_[0], 0.105 * s * k_[2], col, rim, -1)))
        parts.append((a_[1], lambda a_=a_, t_=t_: capsule(d, a_[0], t_[0], 0.07 * s * a_[2], col)))
        sh = pr(J['sh' + nm]); el = pr(J['el' + nm]); wr = pr(J['wr' + nm])
        parts.append(((sh[1] + el[1]) / 2 + 0.02, lambda sh=sh, el=el: capsule(d, sh[0], el[0], 0.10 * s * sh[2], col, rim, -1)))
        parts.append(((el[1] + wr[1]) / 2 + 0.02, lambda el=el, wr=wr: capsule(d, el[0], wr[0], 0.075 * s * el[2], col, rim, -1)))

        def fingers(wr=wr, el=el):
            dx = wr[0][0] - el[0][0]; dy = wr[0][1] - el[0][1]
            ln = math.hypot(dx, dy) + 1e-6
            ux, uy = dx / ln, dy / ln
            for i in range(4):
                sp_ = (i - 1.5) * 0.045 * s * wr[2]
                a0 = (wr[0][0] + sp_, wr[0][1])
                a1 = (a0[0] + ux * 0.24 * s * wr[2] + sp_ * 0.4, a0[1] + max(uy, 0.3) * 0.26 * s * wr[2])
                capsule(d, a0, a1, 0.018 * s * wr[2], col)
        parts.append((wr[1] + 0.03, fingers))
    sL, sR = np.array(J['shL']), np.array(J['shR']); hc = np.array(J['hipc'])
    pts3 = []
    for sg in (1, -1):
        sh = sL if sg > 0 else sR
        pts3 += [tuple(sh + [sg * 0.01, 0.04, -0.07]), tuple(sh + [sg * 0.01, 0.04, 0.07])]
        pts3 += [(sg * 0.17, hc[1] - 0.5, -0.11), (sg * 0.17, hc[1] - 0.5, 0.11), (sg * 0.15, hc[1] - 0.15, -0.1), (sg * 0.15, hc[1] - 0.15, 0.1)]
        pts3 += [(sg * 0.11, hc[1] + 0.4, -0.08), (sg * 0.11, hc[1] + 0.4, 0.08)]
    pp = [pr(p_)[0] for p_ in pts3]
    parts.append((0.0, lambda: d.polygon(hull(pp), fill=col)))
    n0 = pr(J['neck']); n1 = pr(J['ntop']); hd = pr(J['head'])
    parts.append((0.01, lambda: capsule(d, n0[0], n1[0], 0.11 * s * n0[2], col, rim, -1)))

    def head():
        ht, hp, hr = J['headrot']
        rx, ry = 0.088 * s * hd[2], 0.155 * s * hd[2]
        tmp = Image.new('RGBA', (int(rx * 6) | 1, int(ry * 4) | 1), (0, 0, 0, 0)); td = ImageDraw.Draw(tmp)
        cx_, cy_ = tmp.width / 2, tmp.height / 2
        td.ellipse([cx_ - rx, cy_ - ry, cx_ + rx, cy_ + ry], fill=col)
        tmp = tmp.rotate(math.degrees(hr), resample=Image.BICUBIC)
        layer.alpha_composite(tmp, (int(hd[0][0] - tmp.width / 2), int(hd[0][1] - tmp.height / 2)))
    parts.append((0.3, head))
    parts.sort(key=lambda t: t[0])
    for _, fn in parts: fn()
    return J, pr
