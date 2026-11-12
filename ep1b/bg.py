"""Illustrated night environments. Each draws ALBEDO into g, EMISSIVE into ge and returns lamps/glows."""
import math
import numpy as np
from char import G, mix

FOG = (58, 58, 92)


def hsh(i, j, seed=0):
    v = (int(i) * 73856093) ^ (int(j) * 19349663) ^ (seed * 83492791)
    v = (v ^ (v >> 13)) * 1274126177
    return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0


def fogc(c, a): return mix(c, FOG, max(0, min(1, a)))


WARM = (255, 206, 120)
WARM_D = (210, 150, 80)


# ------------------------------------------------------------ perspective corridor
class Persp:
    """One-point-perspective street/alley. Camera at x=0 looking +z."""

    def __init__(self, kind='street', vp=(540, 700), f=1000, cam_h=300, half_w=520):
        self.kind = kind; self.vp = vp; self.f = f; self.h = cam_h; self.W = half_w

    def pr(self, X, Y, z):
        """world (X lateral, Y height above ground, z depth) -> screen design coords"""
        z = max(z, 20.0)
        return self.vp[0] + X * self.f / z, self.vp[1] + (self.h - Y) * self.f / z

    def ground_scale(self, z): return self.f / z

    def draw(self, g, ge, cam_z, lamp_state=None, seed=1, near_z=60.0, bg_brick=False):
        """lamp_state: function(k)->0..1 intensity. returns lamps list [(sx,sy,intensity,kind)]"""
        f = self.f; vx, vy = self.vp; Wd = self.W
        alley = self.kind == 'alley'
        wall_c = (118, 92, 86) if alley else (112, 112, 142)
        wall_c2 = (100, 78, 74) if alley else (96, 96, 126)
        floor_c = (84, 88, 108) if not alley else (70, 70, 84)
        road_c = (66, 70, 92)
        W, H = 1080, 1920
        # sky + far fade
        g.poly([(0, 0), (W, 0), (W, vy + 40), (0, vy + 40)], (60, 56, 96))
        # distant end of the street: low silhouettes
        for i in range(-6, 7):
            hgt = 120 + hsh(i, 5, seed) * 160
            x0 = vx + i * 70
            g.poly([(x0, vy + 24), (x0, vy - hgt), (x0 + 66, vy - hgt), (x0 + 66, vy + 24)], fogc((78, 76, 110), 0.5))
        # road + sidewalks
        zf = 9000.0
        def gp(X, z): return self.pr(X, 0, z)
        zn = near_z
        g.poly([gp(-Wd, zn), gp(Wd, zn), gp(Wd, zf), gp(-Wd, zf)], road_c)
        sw = 300 if not alley else 190
        for sgn in (-1, 1):
            g.poly([self.pr(sgn * sw, 18, zn), self.pr(sgn * Wd, 18, zn), self.pr(sgn * Wd, 18, zf), self.pr(sgn * sw, 18, zf)], floor_c)
            g.poly([self.pr(sgn * sw, 0, zn), self.pr(sgn * sw, 18, zn), self.pr(sgn * sw, 18, zf), self.pr(sgn * sw, 0, zf)], mix(floor_c, (0, 0, 0), .3))
        # walls with windows
        bay = 330.0
        k0 = int(math.floor((cam_z + zn) / bay)) + 12
        lamps = []
        bay_range = range(k0, k0 - 30, -1)  # far -> near
        wall_h = 1500 if not alley else 1400
        for k in bay_range:
            z0 = k * bay - cam_z
            z1 = z0 + bay
            if z1 < zn: continue
            z0c = max(z0, zn)
            fade = min(1, max(0, (z0 - 800) / 5000.0))
            for sgn in (-1, 1):
                X = sgn * Wd
                base = wall_c if (k + (sgn > 0)) % 3 else wall_c2
                g.poly([self.pr(X, 0, z0c), self.pr(X, wall_h, z0c), self.pr(X, wall_h, z1), self.pr(X, 0, z1)], fogc(base, fade))
                # ground floor shop band / door
                if hsh(k, sgn, seed) < 0.25 and not alley:
                    zz0, zz1 = z0 + 70, z1 - 70
                    if zz1 > zn:
                        zz0 = max(zz0, zn)
                        g.poly([self.pr(X, 0, zz0), self.pr(X, 230, zz0), self.pr(X, 230, zz1), self.pr(X, 0, zz1)], fogc((50, 44, 54), fade))
                        if hsh(k, sgn + 7, seed) < 0.6:
                            ge.poly([self.pr(X, 40, zz0 + 10), self.pr(X, 200, zz0 + 10), self.pr(X, 200, zz1 - 10), self.pr(X, 40, zz1 - 10)], mix((220, 170, 100), (10, 10, 20), fade), a=170)
                # window grid
                rows = 5 if not alley else 4
                for r in range(rows):
                    Y0 = 300 + r * 230
                    zz0 = z0 + 90; zz1 = z1 - 90
                    if zz1 <= zn + 5: continue
                    zz0 = max(zz0, zn + 2)
                    q = [self.pr(X * 0.999, Y0, zz0), self.pr(X * 0.999, Y0 + 150, zz0), self.pr(X * 0.999, Y0 + 150, zz1), self.pr(X * 0.999, Y0, zz1)]
                    lit = hsh(k * 2 + (sgn > 0), r, seed + 3)
                    if lit < 0.20:
                        c = mix((255, 200, 120) if lit < 0.13 else (190, 220, 170), (40, 40, 70), fade)
                        ge.poly(q, c)
                        g.poly(q, (30, 30, 30))
                    else:
                        g.poly(q, fogc((22, 26, 48), fade * 0.6))
                    if fade < 0.5:
                        pass
        # lamps (world positions)
        lk0 = int(math.floor((cam_z + zn) / 1100.0)) + 6
        for k in range(lk0, lk0 - 14, -1):
            for sgn in (-1, 1):
                if (k + (sgn > 0)) % 2: continue
                zl = k * 1100.0 + (300 if sgn > 0 else 0) - cam_z
                if zl < zn + 40: continue
                fade = min(1, max(0, (zl - 800) / 5000.0))
                foot = self.pr(sgn * (sw - 40), 18, zl)
                top = self.pr(sgn * (sw - 40), 620, zl)
                arm = self.pr(sgn * (sw - 40 - 120), 640, zl)
                pw = max(4, 26 * f / zl)
                pc = fogc((30, 30, 40), fade)
                g.capsule(foot, top, pw, pc)
                g.capsule(top, arm, pw * 0.7, pc)
                inten = lamp_state(k * 2 + (sgn > 0)) if lamp_state else 1.0
                bulb_r = max(5, 34 * f / zl)
                g.ell(arm[0], arm[1] + bulb_r * 0.4, bulb_r * 1.4, bulb_r * 0.7, pc)
                col = mix((60, 56, 50), (255, 236, 170), inten)
                ge.ell(arm[0], arm[1] + bulb_r * 0.9, bulb_r * 0.9, bulb_r * 0.55, mix((0, 0, 0), col, 1))
                lamps.append((arm[0], arm[1], inten, foot[1], zl))
        # trees on sidewalk (bare)
        if not alley:
            tk0 = int(math.floor((cam_z + zn) / 900.0)) + 6
            for k in range(tk0, tk0 - 12, -1):
                for sgn in (-1, 1):
                    if hsh(k, sgn, seed + 9) < 0.45: continue
                    zt = k * 900.0 + 450 - cam_z
                    if zt < zn + 60: continue
                    fade = min(1, max(0, (zt - 800) / 5000.0))
                    X = sgn * (sw + 70)
                    base = self.pr(X, 18, zt)
                    s = f / zt
                    c = fogc((40, 34, 40), fade)
                    top = (base[0], base[1] - 380 * s)
                    g.capsule(base, top, max(3, 26 * s), c)
                    for br in range(5):
                        ang = -math.pi / 2 + (br - 2) * 0.55
                        L = (170 + hsh(k, br, seed) * 90) * s
                        p1 = (top[0] + math.cos(ang) * L, top[1] + math.sin(ang) * L)
                        g.capsule((top[0], top[1] + 60 * s), p1, max(2, 12 * s), c)
                        p2 = (p1[0] + math.cos(ang + 0.5) * L * 0.5, p1[1] + math.sin(ang + 0.5) * L * 0.5)
                        g.capsule(p1, p2, max(1.5, 7 * s), c)
        if alley:
            # dumpster + pipes
            for k in range(k0, k0 - 30, -1):
                z0 = k * bay - cam_z
                if z0 < zn or hsh(k, 11, seed) > 0.18: continue
                sgn = -1 if hsh(k, 3, seed) < 0.5 else 1
                X = sgn * (Wd - 20)
                zz0, zz1 = z0 + 40, z0 + 280
                q = [self.pr(X, 0, zz0), self.pr(X, 170, zz0), self.pr(X, 170, zz1), self.pr(X, 0, zz1)]
                g.poly(q, fogc((54, 84, 70), min(1, z0 / 5000)))
            for sgn in (-1, 1):
                g.poly([self.pr(sgn * (Wd - 10), 900, zn), self.pr(sgn * (Wd - 10), 960, zn), self.pr(sgn * (Wd - 10), 960, zf), self.pr(sgn * (Wd - 10), 900, zf)], (40, 40, 52))
        return lamps


# ------------------------------------------------------------ flat street (side view)
def lamp_post(g, ge, x, gy, h=760, state=1.0, lean=0.0):
    c = (34, 34, 46)
    top = (x, gy - h)
    g.capsule((x, gy), top, 24, c)
    arm_end = (x + 130, gy - h - 22)
    g.capsule(top, arm_end, 16, c)
    g.poly([(arm_end[0] - 52, arm_end[1] - 8), (arm_end[0] + 52, arm_end[1] - 8), (arm_end[0] + 36, arm_end[1] + 26), (arm_end[0] - 36, arm_end[1] + 26)], c)
    bulb = mix((70, 64, 56), (255, 238, 176), state)
    ge.ell(arm_end[0], arm_end[1] + 24, 34, 12, bulb)
    return (arm_end[0], arm_end[1] + 26)


def bare_tree(g, x, gy, h=520, seed=1, col=(34, 30, 38)):
    top = (x, gy - h)
    g.capsule((x, gy), top, 34, col)
    def br(p, ang, L, w, depth):
        if depth == 0 or L < 20: return
        q = (p[0] + math.cos(ang) * L, p[1] + math.sin(ang) * L)
        g.capsule(p, q, w, col)
        br(q, ang - 0.5 - hsh(depth, int(L), seed) * .3, L * 0.7, w * 0.7, depth - 1)
        br(q, ang + 0.5 + hsh(depth, int(L) + 1, seed) * .3, L * 0.7, w * 0.7, depth - 1)
    for a in (-2.0, -1.55, -1.1):
        br((x, gy - h * 0.8), a, h * 0.42, 22, 4)


def facade(g, ge, x0, x1, gy, top, seed, lit_p=0.28, c=(112, 112, 146), win_w=120, win_h=170, gap=100, curtain=True):
    g.poly([(x0, top), (x1, top), (x1, gy), (x0, gy)], c)
    g.poly([(x0, top), (x1, top), (x1, top + 40), (x0, top + 40)], mix(c, (0, 0, 0), .3))
    cols = int((x1 - x0) // (win_w + gap))
    rows = int((gy - top - 260) // (win_h + 110))
    for i in range(cols + 1):
        for j in range(rows):
            wx = x0 + 50 + i * (win_w + gap); wy = top + 100 + j * (win_h + 110)
            if wx + win_w > x1: continue
            lit = hsh(int(wx // 10), j, seed)
            q = [(wx, wy), (wx + win_w, wy), (wx + win_w, wy + win_h), (wx, wy + win_h)]
            g.poly([(wx - 8, wy - 8), (wx + win_w + 8, wy - 8), (wx + win_w + 8, wy + win_h + 8), (wx - 8, wy + win_h + 8)], mix(c, (255, 255, 255), .15))
            if lit < lit_p:
                ge.poly(q, (255, 206, 120) if lit < lit_p * .7 else (176, 214, 170))
                g.poly(q, (30, 30, 30))
                if curtain:
                    ge.poly([(wx, wy), (wx + win_w * .35, wy), (wx + win_w * .25, wy + win_h), (wx, wy + win_h)], (170, 110, 70))
                    ge.poly([(wx + win_w, wy), (wx + win_w * .65, wy), (wx + win_w * .75, wy + win_h), (wx + win_w, wy + win_h)], (170, 110, 70))
            else:
                g.poly(q, (22, 26, 48))
                g.poly([(wx + 8, wy + 8), (wx + win_w * .45, wy + 8), (wx + 8, wy + win_h * .5)], (46, 54, 90))
            g.poly([(wx - 14, wy + win_h + 8), (wx + win_w + 14, wy + win_h + 8), (wx + win_w + 14, wy + win_h + 24), (wx - 14, wy + win_h + 24)], mix(c, (255, 255, 255), .2))


def flat_street(g, ge, camx, seed=3, gy=1500, lamp_fn=None, shop=None, kind='street'):
    """Side-view street. camx: camera world x. Returns lamps [(sx,sy,state,id)]"""
    W, H = 1080, 1920
    lamps = []
    g.poly([(0, 0), (W, 0), (W, H), (0, H)], (58, 54, 96))
    # far skyline (depth .15)
    d = 0.15
    off = camx * d
    for i in range(-2, 12):
        wx = i * 330 - (off % 330) - 330 + 0
        idx = int((off // 330)) + i - 2
        hgt = 380 + hsh(idx, 1, seed) * 520
        g.poly([(wx, gy - 120 - hgt), (wx + 320, gy - 120 - hgt), (wx + 320, gy)], (54, 54, 88)) if False else g.poly([(wx, gy - 120 - hgt), (wx + 320, gy - 120 - hgt), (wx + 320, gy), (wx, gy)], (74, 72, 112))
        for j in range(int(hgt // 90)):
            for kx in range(3):
                if hsh(idx * 3 + kx, j, seed + 5) < 0.14:
                    ge.poly([(wx + 40 + kx * 95, gy - 150 - hgt + 40 + j * 90), (wx + 70 + kx * 95, gy - 150 - hgt + 40 + j * 90), (wx + 70 + kx * 95, gy - 150 - hgt + 70 + j * 90), (wx + 40 + kx * 95, gy - 150 - hgt + 70 + j * 90)], (200, 160, 100))
    # main facade (depth .85)
    d = 0.85
    off = camx * d
    blk = 1400
    b0 = int(off // blk) - 1
    for b in range(b0, b0 + 3):
        x0 = b * blk - off
        if x0 > W or x0 + blk < -20: continue
        top = 190 + hsh(b, 2, seed) * 80
        facade(g, ge, x0, x0 + blk - 60, gy - 120, top, seed + b)
        # door / shop
        dx = x0 + 300 + hsh(b, 4, seed) * 500
        g.poly([(dx, gy - 120), (dx, gy - 330), (dx + 150, gy - 330), (dx + 150, gy - 120)], (54, 44, 40))
        ge.poly([(dx + 12, gy - 316), (dx + 138, gy - 316), (dx + 138, gy - 250), (dx + 12, gy - 250)], (140, 100, 70))
        g.poly([(dx - 30, gy - 350), (dx + 180, gy - 350), (dx + 180, gy - 330), (dx - 30, gy - 330)], (40, 34, 36))
        ge.ell(dx + 75, gy - 360, 22, 10, (255, 220, 150))
    # ground
    g.poly([(0, gy - 130), (W, gy - 130), (W, gy + 90), (0, gy + 90)], (78, 80, 104))  # sidewalk
    g.poly([(0, gy - 130), (W, gy - 130), (W, gy - 112), (0, gy - 112)], (96, 98, 124))
    g.poly([(0, gy + 90), (W, gy + 90), (W, gy + 118), (0, gy + 118)], (44, 46, 62))     # curb
    g.poly([(0, gy + 118), (W, gy + 118), (W, H), (0, H)], (60, 64, 86))                # road wet
    # sidewalk tiles
    off = camx * 1.0
    for i in range(-1, 14):
        x = i * 140 - (off % 140)
        g.line([(x, gy - 112), (x - 40, gy + 90)], (60, 62, 84), 3)
    # puddles
    pi0 = int(off // 700) - 1
    for i in range(pi0, pi0 + 4):
        px = i * 700 + 200 + hsh(i, 8, seed) * 300 - off
        g.ell(px, gy + 150 + hsh(i, 9, seed) * 120, 150, 22, (140, 150, 190), a=140)
    # lamps (depth 1)
    d = 1.0
    off = camx
    sp = 1000
    k0 = int(off // sp) - 1
    for k in range(k0, k0 + 3):
        x = k * sp + 280 - off
        st = lamp_fn(k) if lamp_fn else 1.0
        bp = lamp_post(g, ge, x, gy + 20, 800, st)
        lamps.append((bp[0], bp[1], st, gy + 20, k))
    # trees
    tp = 1300
    k0 = int(off // tp) - 1
    for k in range(k0, k0 + 3):
        x = k * tp + 760 - off
        bare_tree(g, x, gy + 40, 560, seed + k)
    return lamps


# ------------------------------------------------------------ shop front
def shop_front(g, ge, gy=1500, win=(300, 700, 1050, 1420)):
    """Static shop facade with big window; returns window rect"""
    W, H = 1080, 1920
    g.poly([(0, 0), (W, 0), (W, H), (0, H)], (96, 84, 100))
    # upper floors
    facade(g, ge, 0, W, gy - 120, 120, 11, 0.3, (100, 92, 112))
    # shop band
    g.poly([(0, 820), (W, 820), (W, gy - 120), (0, gy - 120)], (72, 56, 62))
    g.poly([(0, 820), (W, 820), (W, 880), (0, 880)], (48, 36, 44))
    # sign (neon-ish)
    ge.poly([(240, 826), (840, 826), (840, 874), (240, 874)], (70, 20, 24))
    return win


def draw_shop_window(g, ge, rect, lit=0.7):
    x0, y0, x1, y1 = rect
    g.poly([(x0 - 22, y0 - 22), (x1 + 22, y0 - 22), (x1 + 22, y1 + 22), (x0 - 22, y1 + 22)], (40, 30, 34))
    g.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], (30, 34, 52))
    # shelves inside (emissive warm dim)
    for j in range(3):
        yy = y0 + 70 + j * 140
        g.poly([(x0 + 10, yy), (x1 - 10, yy), (x1 - 10, yy + 14), (x0 + 10, yy + 14)], (74, 56, 46))
        for i in range(8):
            if hsh(i, j, 5) < 0.75:
                hh = 40 + hsh(i, j, 6) * 50
                cc = [(150, 80, 70), (90, 120, 100), (160, 140, 90), (80, 90, 140)][int(hsh(i, j, 7) * 4)]
                g.poly([(x0 + 30 + i * 85, yy - hh), (x0 + 30 + i * 85 + 50, yy - hh), (x0 + 30 + i * 85 + 50, yy), (x0 + 30 + i * 85, yy)], cc)
    ge.poly([(x0 + 4, y0 + 4), (x1 - 4, y0 + 4), (x1 - 4, y1 - 4), (x0 + 4, y1 - 4)], mix((0, 0, 0), (60, 46, 36), lit))
    # window frame bars
    g.poly([((x0 + x1) / 2 - 8, y0), ((x0 + x1) / 2 + 8, y0), ((x0 + x1) / 2 + 8, y1), ((x0 + x1) / 2 - 8, y1)], (40, 30, 34))


# ------------------------------------------------------------ courtyard
def courtyard(g, ge, camx=0, seed=7, gy=1500, lamp_state=1.0):
    W, H = 1080, 1920
    lamps = []
    g.poly([(0, 0), (W, 0), (W, H), (0, H)], (62, 58, 96))
    # surrounding block facades (depth .5)
    off = camx * 0.5
    facade(g, ge, -off - 100, W - off + 160, gy - 200, 130, seed, 0.3, (116, 106, 128))
    # entrance / door
    dx = 640 - off
    g.poly([(dx, gy - 200), (dx, gy - 400), (dx + 190, gy - 400), (dx + 190, gy - 200)], (50, 40, 40))
    ge.poly([(dx + 14, gy - 380), (dx + 176, gy - 380), (dx + 176, gy - 300), (dx + 14, gy - 300)], (160, 120, 80))
    g.poly([(dx - 36, gy - 420), (dx + 226, gy - 420), (dx + 226, gy - 400), (dx - 36, gy - 400)], (36, 30, 32))
    # ground
    g.poly([(0, gy - 200), (W, gy - 200), (W, H), (0, H)], (66, 68, 88))
    g.poly([(0, gy - 200), (W, gy - 200), (W, gy - 180), (0, gy - 180)], (88, 90, 112))
    off1 = camx
    # swing set, bench, trees
    sx = 120 - off1
    for dx_ in (0, 330):
        g.capsule((sx + dx_, gy + 40), (sx + 80 + dx_, gy - 380), 20, (44, 44, 56))
        g.capsule((sx + 160 + dx_, gy + 40), (sx + 80 + dx_, gy - 380), 20, (44, 44, 56))
    g.capsule((sx + 80, gy - 380), (sx + 410, gy - 380), 22, (44, 44, 56))
    for dd in (170, 260):
        g.line([(sx + dd, gy - 380), (sx + dd, gy - 120)], (60, 60, 72), 5)
        g.poly([(sx + dd - 36, gy - 120), (sx + dd + 36, gy - 120), (sx + dd + 36, gy - 100), (sx + dd - 36, gy - 100)], (50, 46, 60))
    bx = 780 - off1
    g.poly([(bx, gy - 60), (bx + 250, gy - 60), (bx + 250, gy - 36), (bx, gy - 36)], (74, 56, 46))
    g.poly([(bx, gy - 150), (bx + 250, gy - 150), (bx + 250, gy - 120), (bx, gy - 120)], (74, 56, 46))
    g.capsule((bx + 20, gy - 36), (bx + 20, gy + 40), 16, (40, 40, 50)); g.capsule((bx + 230, gy - 36), (bx + 230, gy + 40), 16, (40, 40, 50))
    bare_tree(g, 1000 - off1, gy + 50, 640, seed)
    bare_tree(g, 40 - off1, gy + 60, 560, seed + 1)
    bp = lamp_post(g, ge, 540 - off1 * 1.05, gy + 40, 780, lamp_state)
    lamps.append((bp[0], bp[1], lamp_state, gy + 40, 0))
    # puddles
    for i in range(4):
        g.ell(180 + i * 280 - off1, gy + 130 + (i % 2) * 90, 130, 20, (140, 150, 190), a=140)
    return lamps


# ------------------------------------------------------------ tower (nine storeys)
def tower(g, ge, roof_y, W=1080, H=1920, seed=21, lit=0.2, fh=241):
    """Tall facade; roof edge at screen y=roof_y. returns (roof_y, tower_cx)"""
    g.poly([(0, 0), (W, 0), (W, H), (0, H)], (66, 62, 104))
    # moonlit sky glow handled by compose; clouds
    for i in range(6):
        g.ell(100 + i * 220, 160 + (i % 3) * 120, 260, 40, (84, 80, 120), a=110)
    # neighbouring blocks
    g.poly([(0, roof_y + 160), (230, roof_y + 160), (230, H), (0, H)], (88, 84, 118))
    g.poly([(860, roof_y + 240), (W, roof_y + 240), (W, H), (860, H)], (84, 80, 116))
    # main tower
    x0, x1 = 170, 910
    g.poly([(x0, roof_y), (x1, roof_y), (x1, H), (x0, H)], (112, 108, 132))
    g.poly([(x0 - 14, roof_y - 22), (x1 + 14, roof_y - 22), (x1 + 14, roof_y + 20), (x0 - 14, roof_y + 20)], (84, 78, 98))  # parapet
    cols = 6
    for r in range(9):
        for c in range(cols):
            wx = x0 + 34 + c * 118; wy = roof_y + 70 + r * fh
            q = [(wx, wy), (wx + 78, wy), (wx + 78, wy + fh * 0.64), (wx, wy + fh * 0.64)]
            l = hsh(c, r, seed)
            if l < lit:
                ge.poly(q, (255, 200, 120) if l < lit * .7 else (176, 214, 170)); g.poly(q, (30, 30, 30))
            else:
                g.poly(q, (24, 28, 52))
                g.poly([(wx + 6, wy + 6), (wx + 40, wy + 6), (wx + 6, wy + 60)], (50, 58, 94))
            g.poly([(wx - 8, wy + fh * 0.66), (wx + 86, wy + fh * 0.66), (wx + 86, wy + fh * 0.66 + 14), (wx - 8, wy + fh * 0.66 + 14)], (150, 146, 170))
    # antenna & water tank on roof
    g.capsule((300, roof_y - 22), (300, roof_y - 150), 8, (40, 38, 50))
    g.line([(260, roof_y - 100), (340, roof_y - 100)], (40, 38, 50), 6)
    ge.ell(300, roof_y - 154, 7, 7, (255, 60, 60))
    return roof_y, (x0 + x1) / 2
