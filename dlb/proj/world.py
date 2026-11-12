"""Environment: perspective street / alley / courtyard renderer with real lamp lighting, fog, rain, grading."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
LW, LH = W // 4, H // 4


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t


class Cam:
    def __init__(self, x=0.0, y=1.6, z=0.0, dir=1, f=900.0, hor=None, xoff=0.0):
        self.x, self.y, self.z, self.dir, self.f = x, y, z, dir, f
        self.hor = H * 0.46 if hor is None else hor
        self.xoff = xoff

    def proj(self, X, Y, Z):
        dz = (Z - self.z) * self.dir
        if dz < 0.25: return None
        k = self.f / dz
        return (W / 2 + self.xoff + self.dir * (X - self.x) * k, self.hor + (self.y - Y) * k, dz, k)

    def scale_at(self, Z):
        dz = max((Z - self.z) * self.dir, 0.25)
        return self.f / dz


FOG_COL = np.array([58.0, 72.0, 88.0])


def fogmix(col, dz, dens=0.026, amb=1.0):
    t = 1 - math.exp(-dz * dens)
    fc = FOG_COL * (0.42 + 0.58 * amb) * 0.62
    return tuple(int(col[i] * (1 - t) + fc[i] * t) for i in range(3))


class World:
    def __init__(self, kind='street', seed=3):
        self.kind = kind
        rnd = random.Random(seed)
        if kind == 'street':
            self.road, self.wall, self.zmin, self.zmax = 4.2, 8.5, -40.0, 130.0
        elif kind == 'alley':
            self.road, self.wall, self.zmin, self.zmax = 1.2, 2.3, -40.0, 130.0
        else:
            self.road, self.wall, self.zmin, self.zmax = 6.0, 9.0, -20.0, 36.0
        self.blocks = []
        step = 9.0
        z = self.zmin
        i = 0
        while z < self.zmax:
            for side in (-1, 1):
                r = random.Random(seed * 1000 + i * 7 + (side + 1))
                if kind == 'courtyard':
                    h = 28.8; floors = 9
                elif kind == 'alley':
                    floors = r.choice([4, 5, 6]); h = floors * 3.2
                else:
                    floors = r.choice([4, 5, 6, 7, 8]); h = floors * 3.2 + 0.6
                shade_ = r.uniform(0.8, 1.2)
                col = (int(38 * shade_), int(42 * shade_), int(52 * shade_))
                if r.random() < 0.3: col = (int(46 * shade_), int(40 * shade_), int(40 * shade_))
                self.blocks.append((side, z, z + step, h, col, floors, r.randint(0, 10 ** 6)))
            z += step; i += 1
        self.lamps = []
        if kind == 'street':
            zz = -30.0
            while zz < 120:
                self.lamps.append((-self.road - 0.5, zz)); self.lamps.append((self.road + 0.5, zz + 12)); zz += 24
        elif kind == 'courtyard':
            self.lamps = [(-5.5, 6.0), (5.5, 18.0), (-5.5, 28.0), (5.5, -8.0)]
        else:
            self.lamps = [(0.0, 12.0), (0.0, 40.0), (0.0, 70.0)]
        self.lamp_h = 5.6
        self.puddles = [(rnd.uniform(-self.road * 0.8, self.road * 0.8), rnd.uniform(self.zmin, self.zmax),
                         rnd.uniform(0.25, 0.8), rnd.uniform(0.25, 0.6)) for _ in range(70)]
        self.sky = [(rnd.uniform(-1, 1), rnd.uniform(0.04, 0.2), rnd.uniform(0.05, 0.14)) for _ in range(18)]

    def illum(self, X, Z, li):
        s = 0.10
        for i, (lx, lz) in enumerate(self.lamps):
            if li[i] <= 0.001: continue
            d2 = (X - lx) ** 2 + (Z - lz) ** 2
            s += li[i] * math.exp(-d2 / (2 * 5.0 ** 2)) * 1.1
        return s

    def render(self, cam, li=None, amb=0.9, t=0.0, back_walls=(), extra_lights=()):
        """Returns (float32 RGB array, lamp screen info)."""
        if li is None: li = [1.0] * len(self.lamps)
        ys = np.arange(H, dtype=np.float32)
        hor = cam.hor
        tsky = np.clip((hor - ys) / max(hor, 1), 0, 1)[:, None]
        skytop = np.array(getattr(self, "skytop", (5, 8, 15)), np.float32); skyhor = np.array([34, 46, 62], np.float32) * (0.5 + 0.5 * amb)
        col = skyhor * (1 - tsky ** 0.7) + skytop * (tsky ** 0.7)
        arr = np.repeat(col[:, None, :], W, axis=1)
        img = Image.fromarray(arr.astype(np.uint8), 'RGB')
        d = ImageDraw.Draw(img, 'RGBA')
        dirn = cam.dir
        for (fx, fh, fw) in self.sky:
            x0 = W / 2 + cam.xoff + fx * W * 0.6 - fw * W / 2 - cam.x * 2 * dirn
            d.rectangle([x0, hor - fh * H * 0.5, x0 + fw * W, hor + 4], fill=(22, 30, 42))
        far = 170.0
        P = cam.proj

        def zc(Z): return cam.z + dirn * max((Z - cam.z) * dirn, 0.3)
        zn = cam.z + dirn * 0.35; zf = cam.z + dirn * far
        q = [P(-self.wall, 0, zn), P(self.wall, 0, zn), P(self.wall, 0, zf), P(-self.wall, 0, zf)]
        if all(q): d.polygon([(a[0], a[1]) for a in q], fill=(21, 28, 38))
        for sd in (-1, 1):
            xa, xb = sd * self.road, sd * self.wall
            q = [P(xa, 0.12, zn), P(xb, 0.12, zn), P(xb, 0.12, zf), P(xa, 0.12, zf)]
            if all(q): d.polygon([(a[0], a[1]) for a in q], fill=(24, 30, 39))
            q = [P(xa, 0.0, zn), P(xa, 0.12, zn), P(xa, 0.12, zf), P(xa, 0.0, zf)]
            if all(q): d.polygon([(a[0], a[1]) for a in q], fill=(32, 38, 48))
        if self.kind != 'courtyard':
            q = [P(-self.road, 0, zn), P(self.road, 0, zn), P(self.road, 0, zf), P(-self.road, 0, zf)]
            if all(q): d.polygon([(a[0], a[1]) for a in q], fill=(11, 14, 19))
            zz = math.floor(cam.z / 6) * 6
            for k in range(-3, 40):
                z0 = zz + k * 6 * dirn
                za, zb = z0, z0 + 2.4 * dirn
                dza, dzb = (za - cam.z) * dirn, (zb - cam.z) * dirn
                if max(dza, dzb) < 0.4 or min(dza, dzb) > 90: continue
                q = [P(-0.08, 0.0, zc(za)), P(0.08, 0.0, zc(za)), P(0.08, 0.0, zc(zb)), P(-0.08, 0.0, zc(zb))]
                if all(q): d.polygon([(a[0], a[1]) for a in q], fill=fogmix((44, 48, 54), q[0][2], amb=amb))
        blocks = []
        for b in self.blocks:
            side, z0, z1, h, bcol, floors, bs = b
            dz0, dz1 = (z0 - cam.z) * dirn, (z1 - cam.z) * dirn
            if max(dz0, dz1) < 0.4 or min(dz0, dz1) > 140: continue
            blocks.append((min(dz0, dz1), b))
        blocks.sort(key=lambda t_: -t_[0])
        wx = self.wall
        for _, b in blocks:
            side, z0, z1, h, bcol, floors, bs = b
            r = random.Random(bs)
            za, zb = (z0, z1) if dirn > 0 else (z1, z0)
            za, zb = zc(za), zc(zb)
            cz = (z0 + z1) / 2
            X = side * wx
            L = self.illum(side * (self.road + 0.5), cz, li)
            k = clamp(0.30 + 0.9 * (L - 0.10) + 0.15 * amb, 0.1, 1.6)
            dzc = max((cz - cam.z) * dirn, 0.5)
            base = tuple(int(c * k) for c in bcol)
            fc = fogmix(base, dzc, amb=amb)
            q = [P(X, 0, za), P(X, h, za), P(X, h, zb), P(X, 0, zb)]
            if not all(q): continue
            d.polygon([(a[0], a[1]) for a in q], fill=fc)
            ce = fogmix(tuple(int(c * 1.5) for c in base), dzc, amb=amb)
            c1, c2, c3, c4 = P(X, h, za), P(X, h, zb), P(X, h - 0.5, zb), P(X, h - 0.5, za)
            if c1 and c2 and c3 and c4: d.polygon([c1[:2], c2[:2], c3[:2], c4[:2]], fill=ce)
            if dzc < 75:
                span = abs(zb - za)
                ncols = 3 if self.kind != 'alley' else 2
                zlo = min(za, zb)
                sh0, sh1 = zlo + span * 0.1, zlo + span * 0.9
                sc = fogmix(tuple(int(c * 0.55) for c in base), dzc, amb=amb)
                qs = [P(X, 0.0, sh0), P(X, 2.9, sh0), P(X, 2.9, sh1), P(X, 0.0, sh1)]
                if all(qs):
                    d.polygon([a[:2] for a in qs], fill=sc)
                    if dzc < 45:
                        for yy in np.arange(0.3, 2.9, 0.22):
                            a, b2 = P(X, yy, sh0), P(X, yy, sh1)
                            if a and b2: d.line([a[:2], b2[:2]], fill=fogmix(tuple(int(c * 0.8) for c in base), dzc, amb=amb), width=1)
                if r.random() < 0.45 and self.kind == 'street':
                    sg = [P(X, 3.3, sh0), P(X, 3.9, sh0), P(X, 3.9, sh1), P(X, 3.3, sh1)]
                    if all(sg): d.polygon([a[:2] for a in sg], fill=fogmix((26 + r.randint(0, 24), 30, 38), dzc, amb=amb))
                for fl in range(1 if self.kind != 'alley' else 2, floors):
                    y0 = fl * 3.2 + 0.7; y1 = y0 + 1.7
                    if y1 > h - 0.6: break
                    for cidx in range(ncols):
                        zc0 = zlo + span * (cidx + 0.28) / ncols; zc1 = zlo + span * (cidx + 0.72) / ncols
                        qw = [P(X, y0, zc0), P(X, y1, zc0), P(X, y1, zc1), P(X, y0, zc1)]
                        if not all(qw): continue
                        lit = ((bs * 31 + fl * 17 + cidx * 5) % 100)
                        if lit < 6:
                            wc = (150, 120, 70) if lit % 2 else (80, 110, 130)
                            wc = tuple(int(c * (0.7 + 0.3 * math.sin(t * 0.5 + bs))) for c in wc)
                        else:
                            wc = (9, 12, 18)
                        d.polygon([a[:2] for a in qw], fill=fogmix(wc, dzc, amb=amb))
                        if lit >= 6 and dzc < 40:
                            a, b2 = P(X, y0, zc0), P(X, y0, zc1)
                            d.line([a[:2], b2[:2]], fill=fogmix(tuple(int(c * 1.8) for c in base), dzc, amb=amb), width=1)
        for (zw, hh) in back_walls:
            dzw = (zw - cam.z) * dirn
            if dzw < 0.5: continue
            q = [P(-wx, 0, zw), P(-wx, hh, zw), P(wx, hh, zw), P(wx, 0, zw)]
            if all(q):
                Lw = self.illum(0, zw, li)
                kk = clamp(0.35 + 0.8 * (Lw - 0.1) + 0.1 * amb, 0.15, 1.5)
                d.polygon([a[:2] for a in q], fill=fogmix((int(40 * kk), int(44 * kk), int(54 * kk)), dzw, amb=amb))
                rr = random.Random(11)
                for fl in range(1, int(hh / 3.2)):
                    for ci in range(9):
                        x0 = -wx + (ci + 0.25) * 2 * wx / 9; x1 = -wx + (ci + 0.75) * 2 * wx / 9
                        y0 = fl * 3.2 + 0.5; y1 = y0 + 1.8
                        qw = [P(x0, y0, zw), P(x0, y1, zw), P(x1, y1, zw), P(x1, y0, zw)]
                        if not all(qw): continue
                        litv = rr.random(); wc = (9, 12, 18)
                        if litv < 0.07: wc = (120, 100, 60)
                        elif litv < 0.10: wc = (70, 100, 120)
                        d.polygon([a[:2] for a in qw], fill=fogmix(wc, dzw, amb=amb))
                d.line([P(-wx, hh, zw)[:2], P(wx, hh, zw)[:2]], fill=fogmix((70, 76, 90), dzw, amb=amb), width=3)
        for (px, pz, pr_, pa) in self.puddles:
            dzp = (pz - cam.z) * dirn
            if dzp < 1.0 or dzp > 70: continue
            c0 = P(px, 0, pz)
            if not c0: continue
            rx = pr_ * c0[3]; ry = rx * 0.10 + 1
            Lp = self.illum(px, pz, li)
            a = int(clamp(14 + 90 * (Lp - 0.1), 6, 90) * pa)
            d.ellipse([c0[0] - rx, c0[1] - ry, c0[0] + rx, c0[1] + ry], fill=(70, 90, 110, a))
        lamp_info = []
        order = sorted(range(len(self.lamps)), key=lambda i: -((self.lamps[i][1] - cam.z) * dirn))
        for i in order:
            lx, lz = self.lamps[i]
            base_p = P(lx, 0, lz); top_p = P(lx, self.lamp_h, lz)
            if not base_p or not top_p: continue
            dzl = base_p[2]
            pc = fogmix((18, 20, 26), dzl, amb=amb)
            wdt = max(2, 0.14 * base_p[3])
            d.line([base_p[:2], top_p[:2]], fill=pc, width=int(wdt))
            arm_p = P(lx - (1.2 if lx > 0 else -1.2), self.lamp_h + 0.1, lz)
            if arm_p:
                d.line([top_p[:2], arm_p[:2]], fill=pc, width=max(2, int(wdt * 0.7)))
                hp = arm_p
            else:
                hp = top_p
            lamp_info.append((i, hp[0], hp[1], hp[3], dzl))
            rr_ = max(2, 0.3 * hp[3])
            if li[i] > 0.01:
                d.ellipse([hp[0] - rr_, hp[1] - rr_ * 0.5, hp[0] + rr_, hp[1] + rr_ * 0.5], fill=(255, 238, 200))
            else:
                d.ellipse([hp[0] - rr_, hp[1] - rr_ * 0.5, hp[0] + rr_, hp[1] + rr_ * 0.5], fill=(20, 22, 26))
        Ls = np.zeros((LH, LW, 3), np.float32)

        def glow(cx, cy, rx, ry, color, amt):
            if rx < 0.5 or ry < 0.5: return
            x0, x1 = int(max(0, cx - rx * 3)), int(min(LW, cx + rx * 3 + 1))
            y0, y1 = int(max(0, cy - ry * 3)), int(min(LH, cy + ry * 3 + 1))
            if x1 <= x0 or y1 <= y0: return
            gx = (np.arange(x0, x1, dtype=np.float32) - cx) / rx; gy = (np.arange(y0, y1, dtype=np.float32) - cy) / ry
            g = np.exp(-(gx[None, :] ** 2 + gy[:, None] ** 2))
            Ls[y0:y1, x0:x1] += g[..., None] * (np.array(color, np.float32) * amt / 255.0)
        for (i, hx, hy, k, dzl) in lamp_info:
            on = li[i]
            if on <= 0.01: continue
            fadef = math.exp(-dzl * 0.012)
            glow(hx / 4, hy / 4, max(3, 0.9 * k / 4), max(3, 0.9 * k / 4), (255, 214, 150), 160 * on * fadef)
            glow(hx / 4, hy / 4, max(8, 3.4 * k / 4), max(8, 3.4 * k / 4), (255, 200, 140), 34 * on * fadef)
            glow(hx / 4, (hy + 2.1 * k) / 4, max(4, 1.3 * k / 4), max(6, 2.8 * k / 4), (190, 190, 170), 20 * on * fadef)
            lx, lz = self.lamps[i]
            gp = P(lx - (1.2 if lx > 0 else -1.2), 0, lz)
            if gp:
                glow(gp[0] / 4, gp[1] / 4, 4.6 * gp[3] / 4, 0.6 * gp[3] / 4 + 1, (150, 150, 130), 46 * on * fadef)
                glow(gp[0] / 4, (gp[1] + 0.75 * gp[3]) / 4, max(1.2, 0.35 * gp[3] / 4), max(4, 3.2 * gp[3] / 4), (255, 214, 160), 70 * on * fadef)
        for (px, py, pz, rad, colr, amt) in extra_lights:
            pp = P(px, py, pz)
            if pp: glow(pp[0] / 4, pp[1] / 4, rad * pp[3] / 4, rad * pp[3] / 4, colr, amt)
        lim = Image.fromarray(np.clip(Ls, 0, 255).astype(np.uint8), 'RGB').resize((W, H), Image.BICUBIC)
        out = np.asarray(img).astype(np.float32) + np.asarray(lim).astype(np.float32)
        return out, lamp_info


def _tile(seed, n=256, beta=2.2):
    rng = np.random.default_rng(seed)
    f = np.fft.fft2(rng.normal(size=(n, n)))
    fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.fftfreq(n)[None, :]
    r = np.sqrt(fx * fx + fy * fy); r[0, 0] = 1
    a = np.real(np.fft.ifft2(f / (r ** beta)))
    a = (a - a.min()) / (a.max() - a.min())
    return np.clip((a - 0.25) * 1.6, 0, 1).astype(np.float32)


class FX:
    def __init__(self):
        n = 512
        self.fog = [Image.fromarray((np.tile(_tile(s, n), (1, 2)) * 255).astype(np.uint8), 'L') for s in (1, 5)]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        v = ((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.72)) ** 2
        self.vig = (1 - np.clip(v, 0, 1) * 0.72)[..., None].astype(np.float32)
        rnd = random.Random(5)
        self.rain = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(30, 120), rnd.uniform(1400, 2600), rnd.uniform(0.3, 1.0))
                     for _ in range(320)]
        self.splash = [(rnd.uniform(0, W), rnd.uniform(0, 1), rnd.uniform(0, 1)) for _ in range(90)]
        self.rng = np.random.default_rng(9)

    def fogalpha(self, t, hor, dens):
        out = np.zeros((H, W), np.float32)
        for i, im in enumerate(self.fog):
            sz = (180, 320) if i == 0 else (120, 213)
            x0 = (t * (3.0 + 2 * i) * (1 if i == 0 else -0.6)) % 512
            y0 = 20 + 5 * math.sin(t * 0.2 + i)
            a = im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + sz[0], y0 + sz[1]))
            out += np.asarray(a).astype(np.float32) / 255.0 * (0.55 if i == 0 else 0.45)
        ys = np.arange(H, dtype=np.float32)
        prof = 0.28 + 0.9 * np.exp(-((ys - hor) / (H * 0.2)) ** 2)
        return out * prof[:, None] * dens

    def apply(self, arr, t, hor=None, fog=0.55, rain=1.0, fogcol=(62, 78, 96), bright=1.0, grain=3.0,
              tint=(0.93, 1.0, 1.08), fade=1.0, blur=0.7, splash=True):
        hor = H * 0.46 if hor is None else hor
        if fog > 0:
            a = self.fogalpha(t, hor, fog)
            fc = np.array(fogcol, np.float32) * bright
            arr = arr * (1 - a[..., None]) + fc[None, None, :] * a[..., None]
        if rain > 0:
            L = Image.new('L', (W, H), 0); d = ImageDraw.Draw(L)
            for (x, y0, ln, sp, al) in self.rain:
                y = (y0 + t * sp) % (H + ln) - ln
                xx = (x - t * sp * 0.10) % W
                d.line([(xx, y), (xx - ln * 0.10, y + ln)], fill=int(34 * al * rain), width=1 if al < 0.7 else 2)
            if splash:
                for (x, yf, ph) in self.splash:
                    y = hor + 60 + (H - hor - 80) * (yf ** 1.7)
                    k = (t * 3.1 + ph) % 1.0
                    r = 2 + 9 * k * (0.4 + yf)
                    d.ellipse([x - r, y - r * 0.25, x + r, y + r * 0.25], outline=int(40 * (1 - k) * rain), width=1)
            rl = np.asarray(L).astype(np.float32) / 255.0
            arr = arr + rl[..., None] * np.array([150, 170, 190], np.float32)
        arr = arr * np.array(tint, np.float32)[None, None, :] * self.vig
        arr = (arr - 8) * 1.06 + 10.5
        if grain > 0:
            n = self.rng.normal(0, grain, (H // 2, W // 2)).astype(np.float32)
            arr = arr + np.repeat(np.repeat(n, 2, 0), 2, 1)[..., None]
        arr = arr * fade
        out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')
        if blur > 0: out = out.filter(ImageFilter.GaussianBlur(blur))
        return out
