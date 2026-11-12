"""Frame compositor: albedo * lighting + emissive + fog + rain + entity layer + grain/vignette."""
import math
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from char import G

K = 2.0 / 3.0          # render scale (design 1080x1920 -> 720x1280)
DW, DH = 1080, 1920
W, H = int(DW * K), int(DH * K)
LW, LH = 180, 320
_xs = (np.arange(LW) + 0.5) * (DW / LW)
_ys = (np.arange(LH) + 0.5) * (DH / LH)
XS, YS = np.meshgrid(_xs, _ys)

rng = np.random.default_rng(7)
_yy, _xx = np.mgrid[0:H, 0:W]
_r2 = ((_xx - W / 2) / (W / 2)) ** 2 * 0.8 + ((_yy - H / 2) / (H / 2)) ** 2 * 0.9
VIG = (1 - 0.42 * np.clip(_r2, 0, 1.6) ** 1.2).astype(np.float32)[..., None]
_n = rng.random((90, 50)).astype(np.float32)
NOISE = np.array(Image.fromarray((_n * 255).astype(np.uint8)).resize((360, 640), Image.BICUBIC).filter(ImageFilter.GaussianBlur(16)), np.float32) / 255
NOISE = (NOISE - NOISE.min()) / (NOISE.max() - NOISE.min())

WARM = np.array([255, 200, 120], np.float32) / 255


class Frame:
    def __init__(self, seed=0):
        self.alb = Image.new('RGB', (W, H), (0, 0, 0))
        self.emi = Image.new('RGB', (W, H), (0, 0, 0))
        self.ent = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.occ = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.ga = G(self.alb, K); self.ge = G(self.emi, K); self.gn = G(self.ent, K); self.go = G(self.occ, K)
        self.lamps = []
        self.extra = []      # (x,y,sx,sy,(r,g,b),intensity)
        self.glows = []      # (x,y,r,(r,g,b),intensity)
        self.seed = seed
        self.post = []       # callbacks run on final array: fn(arr)

    def cam(self, dx=0.0, dy=0.0, zoom=1.0, rot=0.0, cx=540, cy=960):
        for g in (self.ga, self.ge, self.gn, self.go):
            g.xf(cx + dx, cy + dy, rot, zoom, zoom)
            g.xf(-cx, -cy)

    def flush(self):
        self.ga.flush(); self.ge.flush(); self.gn.flush(); self.go.flush()

    def screen_pt(self, x, y):
        return self.ga.P(x, y)


def lightfield(amb, lamps, extra):
    L = np.zeros((LH, LW, 3), np.float32) + np.array(amb, np.float32)
    for lp in lamps:
        x, y, inten, foot = lp[:4]
        if inten <= 0.01: continue
        sc = max((foot - y) / 800.0, 0.15)
        dy = YS - y
        cone = np.exp(-((XS - x) / ((110 + 0.30 * np.maximum(dy, 0)) * sc)) ** 2) * (dy > -30 * sc) * np.exp(-np.maximum(dy, 0) / (1200 * sc))
        halo = np.exp(-(((XS - x) / (260 * sc)) ** 2 + ((YS - y) / (260 * sc)) ** 2))
        pool = np.exp(-(((XS - x) / (420 * sc)) ** 2 + ((YS - foot) / (110 * sc)) ** 2))
        v = (0.85 * cone + 0.55 * halo + 0.9 * pool) * inten
        L += v[..., None] * WARM * 1.25
    for (x, y, sx, sy, c, it) in extra:
        v = np.exp(-(((XS - x) / sx) ** 2 + ((YS - y) / sy) ** 2)) * it
        L += v[..., None] * (np.array(c, np.float32) / 255)
    return L


def finish(fr, amb=(0.34, 0.40, 0.70), fog=0.25, fog_y=0.55, rain=1.0, vig=1.0, ent_alpha=1.0, halo=0.55, bright=1.0,
           emi_gain=1.0, t=0.0, tint=(1, 1, 1), grain=5.0, desat=0.0, fx_red=0.0, nrain=170, rain_slant=0.22):
    fr.flush()
    alb = np.asarray(fr.alb, np.float32)
    emi = np.asarray(fr.emi, np.float32)
    L = lightfield(amb, fr.lamps, fr.extra)
    Lu = np.asarray(Image.fromarray(np.clip(L * 128, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 128
    img = alb * Lu * bright
    # bloom of emissive
    sm = Image.fromarray(emi.astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
    bloom = np.asarray(sm.resize((W, H), Image.BILINEAR), np.float32)
    img = img + emi * emi_gain * 0.92 + bloom * 0.75 * emi_gain
    # lamp glows
    if fr.glows:
        gl = np.zeros((LH, LW, 3), np.float32)
        for (x, y, r, c, it) in fr.glows:
            x, y = fr.screen_pt(x, y)
            x /= K; y /= K
            v = np.exp(-(((XS - x) ** 2 + (YS - y) ** 2) / (r * r))) * it
            gl += v[..., None] * np.array(c, np.float32)
        img += np.asarray(Image.fromarray(np.clip(gl, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)
    # fog
    if fog > 0:
        off = (t * 6.0) % 360
        nz = np.roll(NOISE, int(off), axis=1)
        nz = np.asarray(Image.fromarray((nz * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
        gy = np.exp(-(((np.arange(H) / H) - fog_y) / 0.28) ** 2)[:, None]
        fa = np.clip(fog * gy * (0.55 + 0.9 * nz), 0, 0.85)[..., None]
        fogcol = np.array([86, 86, 128], np.float32) * (0.35 + 0.45 * np.clip(Lu.mean(axis=2, keepdims=True), 0, 1.6))
        img = img * (1 - fa) + fogcol * fa
    # entity layer with dark halo
    if ent_alpha > 0.01:
        ea = np.asarray(fr.ent, np.float32)
        oa = 1 - np.asarray(fr.occ, np.float32)[..., 3:4] / 255
        a = ea[..., 3:4] / 255 * ent_alpha * oa
        if halo > 0:
            hb = np.asarray(fr.ent.split()[3].resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR), np.float32)[..., None] / 255
            img = img * (1 - np.clip(hb * 1.4, 0, 0.78) * halo * ent_alpha * oa)
        entc = ea[..., :3] * (0.55 + 0.25 * np.clip(Lu, 0, 1.2))
        img = img * (1 - a) + entc * a
    # rain
    if rain > 0:
        rl = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(rl)
        r2 = np.random.default_rng(int(t * 30) + fr.seed * 1000)
        n = int(nrain * rain)
        xs = r2.random(n) * (W + 120) - 60; ys = r2.random(n) * H
        ln = 18 + r2.random(n) * 36; br = 70 + r2.random(n) * 130
        for x, y, l, b in zip(xs, ys, ln, br):
            d.line([(x, y), (x - l * rain_slant * 0.6, y + l)], fill=int(b), width=1)
        img += np.asarray(rl, np.float32)[..., None] * np.array([0.55, 0.62, 0.85], np.float32) * 0.9
    for fn in fr.post: img = fn(img)
    if desat: 
        gray = img.mean(axis=2, keepdims=True); img = img * (1 - desat) + gray * desat
    img = img * np.array(tint, np.float32)
    if fx_red: img = img + np.array([60, 0, 0], np.float32) * fx_red
    img = img * (VIG ** vig)
    img = img + 5.0  # lift: never pure black
    if grain: img += rng.standard_normal((H, W, 1)).astype(np.float32) * grain
    # soft tonemap
    img = 255 * (1 - np.exp(-img / 190.0)) * 1.26
    return np.clip(img, 0, 255).astype(np.uint8)
