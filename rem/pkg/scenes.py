import math, skia, numpy as np
from gfx import *
from env import *

def L(c, k=1.0): return tuple(v / 255 * k for v in c)

# every scene: fn(f, t, cx=0, **kw) -> dict(gy=ground y, ...)
def street(f, t, cx=0.0, lamps_on=(1, 1, 1), warm=1.0):
    f.set_ambient((0.26, 0.34, 0.58)); sky(f)
    cv = f.bg.c
    f.bg.c.drawRect(skia.Rect(0, 0, W, 1450), P((36, 40, 62)))
    facade(f, -300 - cx * 0.25, 560 - cx * 0.25, 120, 1450, (52, 56, 82), 3, 4, 10, 0.22, t=t)
    facade(f, 560 - cx * 0.25, 1500 - cx * 0.25, 360, 1450, (62, 58, 80), 5, 5, 8, 0.2, t=t)
    facade(f, 1540 - cx * 0.25, 2600 - cx * 0.25, 60, 1450, (46, 52, 78), 8, 5, 11, 0.25, t=t)
    ground(f)
    fog_band(f, 1480, 120, 0.22)
    for i in range(6):
        x = (i * 640 - cx * 0.9) % 3200 - 400
        lamp(f, x, 1560, 760, on=lamps_on[i % 3], flick=0)
    for i in range(4):
        tree(f, (i * 820 + 200 - cx * 0.7) % 3300 - 300, 1560, 700, seed=i + 2)
    return dict(gy=GY)

def busstop(f, t, cx=0.0, phone_glow=0.0):
    f.set_ambient((0.24, 0.32, 0.58)); sky(f, (12, 16, 36), (40, 46, 80))
    facade(f, -200, 1300, 80, 1400, (58, 52, 76), 21, 4, 11, 0.2, t=t)
    ground(f)
    cv = f.bg.c
    x0 = 120 - cx * 0.1
    cv.drawRect(skia.Rect(x0, 1040, x0 + 700, 1062), P((64, 70, 92)))
    cv.drawRect(skia.Rect(x0 + 10, 1062, x0 + 690, 1100), P((70, 76, 100)))
    for dx in (20, 676): cv.drawRect(skia.Rect(x0 + dx, 1040, x0 + dx + 14, 1560), P((54, 58, 78)))
    cv.drawRect(skia.Rect(x0 + 40, 1100, x0 + 690, 1520), P((150, 190, 230), 0.12))
    cv.drawRect(skia.Rect(x0 + 360, 1180, x0 + 660, 1500), P((230, 220, 200)))   # ad poster
    cv.drawRect(skia.Rect(x0 + 372, 1192, x0 + 648, 1488), P((150, 52, 60)))
    sign_text(cv, 'ВСЕ СПОКОЙНО', x0 + 395, 1300, 52, (245, 235, 220))
    sign_text(cv, 'НИКОГО НЕТ', x0 + 395, 1370, 52, (245, 235, 220))
    bench(f, x0 + 60, 1500, 1.15)
    sign_text(cv, 'АВТОБУС 37', x0 + 500, 1020, 54, (240, 226, 150))
    f.glow(x0 + 400, 1070, 380, (200, 230, 255), 0.35)
    f.light_rect(x0, 1060, x0 + 700, 1500, (0.55, 0.62, 0.78), 0.55, blur=40)
    f.light_pool(x0 + 350, 1520, 520, (0.6, 0.66, 0.8), 0.8)
    lamp(f, 960 - cx * 0.6, 1560, 760, 1.0)
    tree(f, 1020 - cx * 0.4, 1560, 640, seed=9)
    return dict(gy=GY)

def storefront(f, t, cx=0.0, window_glow=1.0, off=False):
    f.set_ambient((0.22, 0.30, 0.56)); sky(f, (10, 14, 32), (36, 42, 74))
    cv = f.bg.c
    facade(f, -300, 1500, 40, 1000, (56, 50, 70), 31, 4, 6, 0.2, t=t)
    cv.drawRect(skia.Rect(-20, 400, 1100, 1560), P((38, 38, 52)))
    cv.drawRect(skia.Rect(-20, 330, 1100, 470), P((60, 34, 50)))
    sign_text(cv, "АПТЕКА  24", 90, 440, 112, (255, 232, 160))
    f.glow(540, 400, 420, (255, 220, 150), 0.25)
    gx0, gx1, gy0, gy1 = 440, 1040, 520, 1490
    cv.drawRect(skia.Rect(gx0 - 14, gy0 - 14, gx1 + 14, gy1 + 14), P((20, 20, 30)))
    cv.drawRect(skia.Rect(gx0, gy0, gx1, gy1), P(shader=lin((0, gy0), (0, gy1), (70, 94, 142), (34, 46, 84))))
    ground(f)
    f.light_rect(gx0, gy0, gx1, gy1, (0.7, 0.68, 0.6), 0.4 * window_glow, blur=30)
    f.light_pool(540, 1520, 600, (0.6, 0.5, 0.38), 0.55 * window_glow)
    lamp(f, 60, 1560, 760, 0.7, flick=0)
    return dict(gy=GY, glass=(gx0, gy0, gx1, gy1))

def avenue(f, t, cx=0.0, lamps=(1, 1, 1), flick=(0, 0, 0), crash=None):
    f.set_ambient((0.2, 0.28, 0.52)); sky(f, (8, 12, 28), (30, 36, 66))
    facade(f, -100 - cx * 0.2, 1400 - cx * 0.2, 240, 1440, (44, 48, 72), 41, 6, 10, 0.18, t=t)
    facade(f, 1400 - cx * 0.2, 3400 - cx * 0.2, 120, 1440, (50, 46, 70), 43, 8, 11, 0.18, t=t)
    ground(f, road=(30, 32, 46))
    fog_band(f, 1470, 150, 0.28)
    hs = []
    for i in range(3):
        x = 140 + i * 640 - cx * 0.9
        hs.append(lamp(f, x, 1560, 760, on=lamps[i], flick=flick[i]))
    return dict(gy=GY, lamps=hs)

def underpass(f, t, cx=0.0):
    f.set_ambient((0.22, 0.3, 0.5)); 
    cv = f.bg.c
    cv.drawRect(skia.Rect(0, 0, W, H), P((30, 34, 48)))
    grad_rect(cv, 0, 0, W, 1500, (34, 40, 56), (58, 62, 80))
    # tunnel tiles
    for i in range(-2, 16):
        x = i * 220 - (cx * 1.0) % 220
        cv.drawRect(skia.Rect(x, 0, x + 6, 1500), P((24, 26, 38), 0.8))
    for j in range(0, 14):
        cv.drawRect(skia.Rect(0, j * 110, W, j * 110 + 5), P((24, 26, 38), 0.6))
    cv.drawRect(skia.Rect(0, 1500, W, H), P((40, 42, 56)))
    ground(f, y=1560, road=(44, 46, 62), walk=(66, 70, 90))
    # ceiling lights
    for i in range(5):
        x = (i * 520 - cx * 1.2) % 2600 - 300
        on = 0.35 + 0.65 * (1 if (int(t * 3 + i) % 5) else 0.3)
        cv.drawRect(skia.Rect(x, 120, x + 260, 150), P(mix((60, 64, 70), (210, 240, 255), on)))
        f.light_cone(x + 130, 150, 1560, 120, 520, (0.55, 0.75, 0.9), 0.8 * on)
        f.glow(x + 130, 140, 220, (180, 220, 255), 0.5 * on)
    # graffiti
    sign_text(cv, 'НЕ ОГЛЯДЫВАЙСЯ', 80 - cx * 1.0 % 2000, 700, 120, (90, 40, 60))
    return dict(gy=GY)

def alley(f, t, cx=0.0):
    f.set_ambient((0.2, 0.26, 0.5)); sky(f, (6, 9, 22), (26, 30, 56))
    cv = f.bg.c
    facade(f, -200 - cx * 0.3, 420 - cx * 0.3, 0, 1560, (38, 40, 60), 51, 2, 14, 0.12, t=t)
    facade(f, 660 - cx * 0.3, 1500 - cx * 0.3, 0, 1560, (34, 38, 58), 53, 3, 14, 0.14, t=t)
    cv.drawRect(skia.Rect(420 - cx * 0.3, 0, 660 - cx * 0.3, 1560), P((14, 16, 28)))
    ground(f, road=(28, 30, 44), walk=(40, 44, 64), curb=(50, 54, 74))
    # dumpsters + pipes
    for i, x in enumerate((60, 760, 1500)):
        x -= cx * 0.9
        cv.drawRect(skia.Rect(x, 1330, x + 240, 1560), P((34, 62, 56)))
        cv.drawRect(skia.Rect(x - 8, 1310, x + 248, 1340), P((26, 48, 44)))
    for x in (480, 560):
        cv.drawRect(skia.Rect(x - cx * 0.3, 0, x + 14 - cx * 0.3, 1560), P((54, 58, 76)))
    f.light_rect(420 - cx * 0.3, 0, 660 - cx * 0.3, 1560, (0.2, 0.25, 0.4), 0.5, blur=60)
    lamp(f, 880 - cx * 0.8, 1560, 700, 0.7, tint=(255, 160, 90), flick=0.2 * (math.sin(t * 17) > 0.3))
    fog_band(f, 1500, 100, 0.3)
    return dict(gy=GY)

def courtyard(f, t, cx=0.0, lamp_on=0.55, eerie=0.0):
    f.set_ambient((0.2, 0.26, 0.5)); sky(f, (6, 8, 22), (24, 28, 54))
    cv = f.bg.c
    for k, (x0, x1) in enumerate(((-300, 560), (560, 1400), (1400, 2400))):
        facade(f, x0 - cx * 0.3, x1 - cx * 0.3, 0, 1500, [(46, 50, 72), (58, 54, 74), (42, 48, 70)][k], 61 + k, 4, 14, 0.22, t=t)
    ground(f, road=(34, 38, 52), walk=(52, 58, 80), curb=(70, 74, 98))
    # playground
    x = 110 - cx * 0.9
    cv.drawRect(skia.Rect(x, 1000, x + 14, 1560), P((150, 70, 60)))
    cv.drawRect(skia.Rect(x + 360, 1000, x + 374, 1560), P((150, 70, 60)))
    cv.drawRect(skia.Rect(x, 990, x + 374, 1010), P((150, 70, 60)))
    for sx in (110, 250):
        cv.drawLine(x + sx, 1010, x + sx - 6, 1380, P((90, 92, 110), style='stroke', width=5))
        cv.drawLine(x + sx + 70, 1010, x + sx + 64, 1380, P((90, 92, 110), style='stroke', width=5))
        cv.drawRect(skia.Rect(x + sx - 14, 1376, x + sx + 84, 1396), P((60, 60, 74)))
    sx = 1100 - cx * 0.9
    p = skia.Path(); p.moveTo(sx, 1100); p.lineTo(sx + 130, 1100); p.lineTo(sx + 480, 1560); p.lineTo(sx + 300, 1560); p.close()
    cv.drawPath(p, P((70, 110, 170)))
    cv.drawRect(skia.Rect(sx - 10, 1080, sx + 140, 1100), P((60, 62, 80)))
    cv.drawRect(skia.Rect(sx, 1100, sx + 14, 1560), P((60, 62, 80)))
    tree(f, 640 - cx * 0.7, 1560, 800, seed=14)
    lamp(f, 860 - cx * 0.9, 1560, 780, on=lamp_on, tint=(255, 196, 130) if not eerie else (180, 255, 210))
    fog_band(f, 1500, 130, 0.25)
    return dict(gy=GY)

def rooftop_view(f, t, cx=0.0, cam_up=0.0):
    """low-angle on a nine-storey block with the roofline against the night sky"""
    f.set_ambient((0.2, 0.26, 0.5)); sky(f, (12, 18, 46), (84, 98, 168))
    cv = f.bg.c
    # moon
    cv.drawCircle(850, 300 + cam_up, 120, P((226, 232, 255), 0.9)); f.glow(850, 300 + cam_up, 520, (160, 180, 255), 0.5)
    # clouds
    for i in range(5):
        cv.drawOval(skia.Rect(80 + i * 260, 560 + (i % 2) * 120 + cam_up, 360 + i * 260, 640 + (i % 2) * 120 + cam_up), P((40, 46, 80), 0.5))
    # building
    top = 1000 + cam_up
    facade(f, -40, 1120, top, H + 100, (46, 48, 70), 71, 9, 9, 0.22, t=t)
    cv.drawRect(skia.Rect(-40, top - 40, 1120, top), P((30, 32, 48)))
    cv.drawRect(skia.Rect(-40, top - 80, 1120, top - 40), P((24, 26, 40)))
    cv.drawRect(skia.Rect(100, top - 150, 220, top - 80), P((24, 26, 40)))   # stair house
    cv.drawRect(skia.Rect(700, top - 120, 760, top - 80), P((24, 26, 40)))
    cv.drawLine(900, top - 80, 900, top - 230, P((30, 32, 48), style='stroke', width=8))
    return dict(roof=top - 80)

def cctv(f, t, cx=0.0, lamps_on=(1, 1, 1)):
    return street(f, t, cx, lamps_on)
