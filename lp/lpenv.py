"""LAST PASSENGER — environments: college street, bus stop, bus (exterior + perspective interior), home street, facade."""
import math
import random
import sys
for _p in ('/tmp/hoplite/workspace/rem', '/tmp/hoplite/workspace/opus', '/tmp/hoplite/workspace/lp'):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)
import skia  # noqa: E402
from gfx import P, lin, rad, path_poly, path_smooth, mix  # noqa: E402
import world as Wd  # noqa: E402

W, H = 1080, 1920
SODIUM = (238, 160, 82)          # dirty orange streetlight
FLUO = (196, 226, 206)           # pale green fluorescent
NIGHT = ((8, 12, 26), (30, 38, 62))
_F = skia.Typeface.MakeFromFile('/tmp/hoplite/workspace/rem/subs2/fonts/Inter-Bold.ttf')


def font(sz):
    return skia.Font(_F, sz)


def text_c(cv, s, x, y, sz, col, a=1.0):
    f = font(sz)
    cv.drawString(s, x - f.measureText(s) / 2, y, f, P(col, a))


def fog(cv, t, y0, y1, a=0.35, col=(120, 134, 150), seed=1, cx=0.0):
    """drifting horizontal fog banks"""
    r = random.Random(seed)
    for i in range(9):
        y = r.uniform(y0, y1)
        x = (r.uniform(-400, 1400) + t * r.uniform(8, 24) - cx * 0.3) % 1900 - 400
        w = r.uniform(500, 900)
        cv.drawOval(skia.Rect(x - w, y - 70, x + w, y + 70), P(col, a * r.uniform(0.4, 0.9), blur=60))


def wires(cv, cx, y=260, sag=60, col=(14, 16, 26), n=3, par=0.4):
    for k in range(n):
        yy = y + k * 34
        for i in range(-1, 4):
            x0 = i * 700 - (cx * par) % 700
            pa = skia.Path(); pa.moveTo(x0, yy); pa.quadTo(x0 + 350, yy + sag, x0 + 700, yy)
            cv.drawPath(pa, P(col, style='stroke', width=3))


# ------------------------------------------------------------------ college street
def college(cv, t, cx=0.0, gy=1460, door_open=0.0):
    Wd.sky(cv, (6, 10, 22), (30, 38, 60), gy)
    for i in range(-1, 5):
        Wd.panel_building(cv, i * 340 - 100 - cx * 0.25, 300, gy - 900 - (i * 113) % 220, gy - 220, (26, 32, 50), seed=60 + i,
                          lit=0.10, floor_h=70, t=t)
    x0 = 80 - cx
    # four-storey brick college with a lit glass entrance
    cv.drawRect(skia.Rect(x0, gy - 980, x0 + 980, gy), P(shader=lin((0, gy - 980), (0, gy), (58, 46, 46), (40, 32, 34))))
    for fl in range(4):
        for c in range(6):
            wx, wy = x0 + 50 + c * 156, gy - 930 + fl * 170
            lit_ = (c * 7 + fl * 3) % 5 == 0
            cv.drawRect(skia.Rect(wx, wy, wx + 100, wy + 110), P((150, 160, 130) if lit_ else (24, 28, 40)))
            cv.drawRect(skia.Rect(wx, wy, wx + 100, wy + 110), P((20, 18, 22), style='stroke', width=6))
    cv.drawRect(skia.Rect(x0 + 300, gy - 330, x0 + 680, gy - 260), P((24, 30, 40)))
    text_c(cv, 'КОЛЛЕДЖ', x0 + 490, gy - 278, 46, (210, 220, 206))
    # entrance glass doors
    dx0, dx1 = x0 + 380, x0 + 600
    cv.drawRect(skia.Rect(dx0 - 20, gy - 250, dx1 + 20, gy), P((22, 22, 26)))
    cv.drawRect(skia.Rect(dx0, gy - 236, dx1, gy), P((200, 214, 196)))
    cv.drawRect(skia.Rect(dx0, gy - 236, dx1, gy), P(shader=lin((0, gy - 236), (0, gy), (230, 236, 220), (150, 170, 150))))
    w2 = (dx1 - dx0) / 2
    for sd, xa in ((-1, dx0), (1, dx1)):
        off = door_open * w2 * 0.85
        lx = xa - sd * off if sd == -1 else xa - w2 + off
        cv.drawRect(skia.Rect(dx0 + (w2 * (0 if sd == -1 else 1)) - (off if sd == -1 else -off), gy - 236,
                              dx0 + (w2 * (1 if sd == -1 else 2)) - (off if sd == -1 else -off), gy), P((30, 34, 40), style='stroke', width=8))
    cv.drawOval(skia.Rect(dx0 - 160, gy - 40, dx1 + 160, gy + 140), P((200, 220, 190), 0.16, blur=40))
    Wd.street_ground(cv, gy, cx)
    Wd.wet_reflection(cv, (dx0 + dx1) / 2, gy + 6, (200, 220, 196), w=110, ln=360, a=0.18)
    wires(cv, cx, 210)


# ------------------------------------------------------------------ bus stop
def bus_stop(cv, x, gy, s=1.0, sign='ул. Лесная', lit=1.0):
    """glass shelter with a bench, timetable, stop sign on a pole; x = shelter centre"""
    w, h = 520 * s, 470 * s
    cv.drawRect(skia.Rect(x - w / 2, gy - h, x + w / 2, gy - h + 26 * s), P((30, 34, 44)))       # roof
    cv.drawRect(skia.Rect(x - w / 2, gy - h + 26 * s, x + w / 2, gy - 30 * s), P((120, 150, 170), 0.10))   # back glass
    for k in (-0.5, 0.0, 0.5):
        cv.drawRect(skia.Rect(x + k * w - 6 * s, gy - h, x + k * w + 6 * s, gy), P((44, 48, 60)))
    cv.drawRect(skia.Rect(x - w * 0.38, gy - 150 * s, x + w * 0.38, gy - 130 * s), P((52, 56, 70)))   # bench
    cv.drawRect(skia.Rect(x + w * 0.05, gy - h + 70 * s, x + w * 0.42, gy - h + 250 * s), P((210, 214, 196), 0.85 * lit))   # timetable
    for r_ in range(6):
        cv.drawRect(skia.Rect(x + w * 0.08, gy - h + (90 + r_ * 24) * s, x + w * 0.38, gy - h + (98 + r_ * 24) * s), P((90, 96, 100), 0.6 * lit))
    cv.drawRect(skia.Rect(x - w / 2, gy - h + 26 * s, x + w / 2, gy - h + 40 * s), P(FLUO, 0.6 * lit))
    cv.drawOval(skia.Rect(x - w * 0.7, gy - 60 * s, x + w * 0.7, gy + 80 * s), P(FLUO, 0.10 * lit, blur=40 * s))
    # pole sign
    px = x - w / 2 - 70 * s
    cv.drawRect(skia.Rect(px - 6 * s, gy - 640 * s, px + 6 * s, gy), P((60, 64, 74)))
    stop_sign(cv, px, gy - 560 * s, 0.5 * s, sign)


def stop_sign(cv, x, y, s, name='ул. Лесная'):
    """yellow 'A' plate + white name plate"""
    cv.drawRect(skia.Rect(x - 90 * s, y - 90 * s, x + 90 * s, y + 90 * s), P((222, 190, 40)))
    cv.drawRect(skia.Rect(x - 90 * s, y - 90 * s, x + 90 * s, y + 90 * s), P((20, 20, 20), style='stroke', width=6 * s))
    text_c(cv, 'А', x, y + 50 * s, 140 * s, (20, 20, 24))
    cv.drawRect(skia.Rect(x - 170 * s, y + 104 * s, x + 170 * s, y + 190 * s), P((230, 232, 226)))
    text_c(cv, name, x, y + 164 * s, 50 * s, (24, 28, 36))
    text_c(cv, '13', x - 130 * s + 50 * s, y + 250 * s, 44 * s, (230, 232, 226)) if False else None


# ------------------------------------------------------------------ bus exterior
BUS_BODY = (176, 168, 120)   # faded yellow-cream LiAZ
BUS_STRIPE = (120, 44, 36)


def bus_side(cv, x, gy, s, t, bob=0.0, door=0.0, inside=1.0, facing=1, roll=0.0, flicker=1.0, head_on=1.0, dirt=0.4):
    """old city bus, side view. x = bus centre, s = px per cm (bus 1100 cm long, 300 tall)."""
    L, Hh = 1100 * s, 290 * s
    cv.save()
    cv.translate(x, gy - 46 * s + bob * s)
    cv.rotate(roll)
    if facing < 0:
        cv.scale(-1, 1)
    x0, x1 = -L / 2, L / 2
    top = -Hh
    body = skia.RRect.MakeRectXY(skia.Rect(x0, top, x1, -18 * s), 34 * s, 34 * s)
    cv.drawRRect(body, P(shader=lin((0, top), (0, 0), mix(BUS_BODY, (255, 255, 255), 0.05), mix(BUS_BODY, (20, 20, 20), 0.35))))
    cv.drawRect(skia.Rect(x0, -100 * s, x1, -76 * s), P(BUS_STRIPE))
    # windows: lit interior, pale green
    wy0, wy1 = top + 48 * s, -128 * s
    for k in range(7):
        wx0 = x0 + 150 * s + k * 128 * s
        if 2.2 < k + 0.5 < 3.6:
            continue
        inner = mix((20, 26, 30), FLUO, 0.75 * inside * flicker)
        cv.drawRect(skia.Rect(wx0, wy0, wx0 + 110 * s, wy1), P(shader=lin((0, wy0), (0, wy1), inner, mix(inner, (40, 50, 50), 0.4))))
        # silhouettes of passengers in some windows
        if k in (1, 4, 6):
            hx = wx0 + 55 * s
            cv.drawCircle(hx, wy1 - 60 * s, 18 * s, P((40, 46, 46), 0.8 * inside))
            cv.drawRect(skia.Rect(hx - 26 * s, wy1 - 42 * s, hx + 26 * s, wy1), P((40, 46, 46), 0.8 * inside))
        cv.drawRect(skia.Rect(wx0, wy0, wx0 + 110 * s, wy1), P((30, 30, 30), style='stroke', width=6 * s))
    # front door (two leaves) at k≈3
    dx0, dx1 = x0 + 150 * s + 2.5 * 128 * s, x0 + 150 * s + 3.4 * 128 * s
    cv.drawRect(skia.Rect(dx0, top + 40 * s, dx1, -24 * s), P(mix((20, 26, 30), FLUO, 0.8 * inside * flicker)))
    dw = (dx1 - dx0) / 2
    for sd in (0, 1):
        a = door * dw * 0.9
        lx0 = dx0 + sd * dw + (a if sd else -a) * 0.0
        shrink = dw * (1 - 0.18 * door) if door > 0 else dw
        lx = dx0 if sd == 0 else dx1 - shrink
        if door > 0:
            lx = dx0 - door * dw * 0.15 if sd == 0 else dx1 - shrink + door * dw * 0.15
            shrink = dw * (1 - 0.82 * door)
        cv.drawRect(skia.Rect(lx, top + 40 * s, lx + shrink, -24 * s), P((44, 48, 44)))
        cv.drawRect(skia.Rect(lx + 6 * s, top + 52 * s, lx + shrink - 6 * s, -130 * s), P(mix((26, 32, 34), FLUO, 0.5 * inside * flicker)))
    # route plate "13" over the front window
    cv.drawRect(skia.Rect(x1 - 170 * s, top + 8 * s, x1 - 40 * s, top + 42 * s), P((24, 22, 18)))
    text_c(cv, '13', x1 - 105 * s, top + 38 * s, 34 * s, (250, 180, 60))
    # windshield
    cv.drawRect(skia.Rect(x1 - 26 * s, top + 46 * s, x1, -120 * s), P(mix((20, 26, 30), FLUO, 0.4 * inside)))
    # headlight + taillight
    cv.drawCircle(x1 - 10 * s, -50 * s, 13 * s, P((255, 240, 200), head_on))
    if head_on > 0:
        pa = skia.Path(); pa.moveTo(x1, -50 * s); pa.lineTo(x1 + 900 * s, -150 * s); pa.lineTo(x1 + 900 * s, 60 * s); pa.close()
        cv.drawPath(pa, P(shader=lin((x1, 0), (x1 + 900 * s, 0), (255, 236, 190), (255, 236, 190), 0.30 * head_on, 0.0)))
    cv.drawRect(skia.Rect(x0, -70 * s, x0 + 14 * s, -36 * s), P((200, 30, 30)))
    # dirt / rust streaks
    r = random.Random(13)
    for _ in range(14):
        rx = r.uniform(x0 + 20 * s, x1 - 20 * s)
        cv.drawRect(skia.Rect(rx, -76 * s, rx + r.uniform(3, 9) * s, -20 * s - r.uniform(0, 30) * s), P((80, 60, 40), dirt * 0.5))
    cv.restore()
    # wheels (no body bob)
    for wx in (x0 + 210 * s, x1 - 260 * s):
        X = x + (wx if facing > 0 else -wx)
        cv.drawCircle(X, gy - 46 * s, 50 * s, P((14, 14, 16)))
        cv.drawCircle(X, gy - 46 * s, 26 * s, P((70, 70, 72)))
        ang = t * 8
        for k in range(5):
            a = ang + k * 1.2566
            cv.drawCircle(X + math.cos(a) * 16 * s, gy - 46 * s + math.sin(a) * 16 * s, 3.5 * s, P((30, 30, 32)))
    cv.drawOval(skia.Rect(x - L * 0.55, gy - 14 * s, x + L * 0.55, gy + 18 * s), P((0, 0, 0), 0.5, blur=14 * s))


def bus_front(cv, cx, gy, s, t, head_on=1.0, inside=1.0, bob=0.0):
    """front view of the approaching bus; s = px per cm (bus 250 cm wide)"""
    w, h = 250 * s, 300 * s
    y0 = gy - 40 * s + bob * s
    if head_on > 0:   # light cones toward the camera
        for sd in (-1, 1):
            hx = cx + sd * w * 0.36
            cv.drawCircle(hx, y0 - 50 * s, 420 * s, P(shader=rad((hx, y0 - 50 * s), 420 * s, (255, 238, 200), (255, 238, 200), 0.35 * head_on, 0.0)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - w / 2, y0 - h, cx + w / 2, y0), 26 * s, 26 * s),
                 P(shader=lin((0, y0 - h), (0, y0), BUS_BODY, mix(BUS_BODY, (10, 10, 10), 0.45))))
    cv.drawRect(skia.Rect(cx - w * 0.44, y0 - h * 0.85, cx + w * 0.44, y0 - h * 0.42), P(mix((16, 20, 24), FLUO, 0.45 * inside)))
    # driver silhouette
    cv.drawCircle(cx - w * 0.25, y0 - h * 0.62, 16 * s, P((26, 30, 30)))
    cv.drawRect(skia.Rect(cx - w * 0.33, y0 - h * 0.58, cx - w * 0.17, y0 - h * 0.42), P((26, 30, 30)))
    cv.drawRect(skia.Rect(cx - w * 0.30, y0 - h * 0.97, cx + w * 0.30, y0 - h * 0.87), P((24, 22, 18)))
    text_c(cv, '13', cx, y0 - h * 0.885, 26 * s, (250, 180, 60))
    cv.drawRect(skia.Rect(cx - w / 2, y0 - h * 0.30, cx + w / 2, y0 - h * 0.24), P(BUS_STRIPE))
    for sd in (-1, 1):
        hx = cx + sd * w * 0.36
        cv.drawCircle(hx, y0 - 50 * s, 15 * s, P((255, 246, 220), 0.3 + 0.7 * head_on))
        cv.drawCircle(hx, y0 - 50 * s, 40 * s, P((255, 236, 190), 0.5 * head_on, blur=16 * s))
    cv.drawRect(skia.Rect(cx - w * 0.2, y0 - 70 * s, cx + w * 0.2, y0 - 34 * s), P((30, 30, 30)))
    cv.drawOval(skia.Rect(cx - w * 0.7, gy - 10 * s, cx + w * 0.7, gy + 20 * s), P((0, 0, 0), 0.5, blur=10 * s))


# ------------------------------------------------------------------ bus interior (one-point perspective)
class Persp:
    """camera inside the bus. world: x lateral (cm, + = right when looking down -z... ), y height, z along the bus (cm)."""
    def __init__(self, cx_cm, cy_cm, cz_cm, look=+1, f=900.0, vx=W / 2, vy=H * 0.42, roll=0.0, yaw=0.0):
        self.c = (cx_cm, cy_cm, cz_cm)
        self.look = look      # +1 looks toward +z (rear), -1 toward -z (front)
        self.f, self.vx, self.vy = f, vx, vy
        self.yaw = yaw

    def p(self, x, y, z):
        dz = (z - self.c[2]) * self.look
        dx = (x - self.c[0]) * self.look
        dx, dz = dx * math.cos(self.yaw) - dz * math.sin(self.yaw), dx * math.sin(self.yaw) + dz * math.cos(self.yaw)
        dz = max(dz, 25.0)
        k = self.f / dz
        return self.vx + dx * k, self.vy - (y - self.c[1]) * k, k

    def poly(self, pts3):
        return path_poly([self.p(*q)[:2] for q in pts3])


BUS_HW = 125      # half width (cm)
BUS_LEN = 1100
SEAT_ROWS = [260, 360, 460, 560, 660, 760, 860]     # z of seat rows (front ~ 0, rear bench at 1000)
REAR_Z = 1000


def bus_interior(cv, t, cam, lights=1.0, flicker=1.0, moving=1.0, outside='street', items=(), stop_pass=None, dark=0.0, rear_dark=0.55):
    """draw the interior; items = [(z, fn(cam)) ...] people etc, depth sorted with the seats."""
    L = lights * flicker
    wall = mix((12, 16, 16), (62, 78, 70), L)
    wall_d = mix((8, 10, 12), (50, 62, 58), L)
    floor_c = mix((8, 9, 10), (46, 50, 48), L)
    ceil_c = mix((8, 10, 10), (92, 108, 98), L)
    zf, zb = (0, BUS_LEN) if cam.look > 0 else (BUS_LEN, -40)
    far = BUS_LEN if cam.look > 0 else -40
    near = cam.c[2] + cam.look * 5
    cv.drawRect(skia.Rect(0, 0, W, H), P((6, 8, 10)))
    # end wall (rear window or windshield)
    cv.drawPath(cam.poly([(-BUS_HW, 0, far), (BUS_HW, 0, far), (BUS_HW, 230, far), (-BUS_HW, 230, far)]), P(wall_d))
    win = cam.poly([(-BUS_HW + 20, 100, far), (BUS_HW - 20, 100, far), (BUS_HW - 20, 200, far), (-BUS_HW + 20, 200, far)])
    cv.drawPath(win, P((10, 14, 24)))
    if cam.look < 0:     # windshield: road ahead with lamps sweeping
        cv.save(); cv.clipPath(win, skia.ClipOp.kIntersect, True)
        a, b, _ = cam.p(0, 150, far)
        for k in range(4):
            u = ((t * 0.6 * moving + k / 4) % 1.0)
            cv.drawCircle(a + (-1 if k % 2 else 1) * 200 * u * cam.p(0, 0, far)[2], b - 20 * u, 6 + 30 * u * u, P(SODIUM, 0.7 * (1 - u)))
        cv.restore()
    # floor / ceiling / walls
    cv.drawPath(cam.poly([(-BUS_HW, 0, near), (BUS_HW, 0, near), (BUS_HW, 0, far), (-BUS_HW, 0, far)]), P(floor_c))
    cv.drawPath(cam.poly([(-30, 0.5, near), (30, 0.5, near), (30, 0.5, far), (-30, 0.5, far)]), P(mix(floor_c, (0, 0, 0), 0.25)))
    cv.drawPath(cam.poly([(-BUS_HW, 230, near), (BUS_HW, 230, near), (BUS_HW, 230, far), (-BUS_HW, 230, far)]), P(ceil_c))
    for sd in (-1, 1):
        x = sd * BUS_HW
        cv.drawPath(cam.poly([(x, 0, near), (x, 230, near), (x, 230, far), (x, 0, far)]), P(wall))
        # window band, dark night outside
        for z0 in range(0, BUS_LEN, 140):
            z1 = z0 + 124
            if (z0 - cam.c[2]) * cam.look < 0 and (z1 - cam.c[2]) * cam.look < 0:
                continue
            wp = cam.poly([(x, 100, z0), (x, 196, z0), (x, 196, z1), (x, 100, z1)])
            cv.drawPath(wp, P((8, 12, 22)))
            cv.save(); cv.clipPath(wp, skia.ClipOp.kIntersect, True)
            # passing street lights sliding along the window band
            for k in range(3):
                u = ((t * 0.9 * moving + k / 3 + z0 / 700) % 1.0)
                zz = z0 + (1 - u) * 124 if cam.look > 0 else z0 + u * 124
                q = cam.p(x, 170, zz)
                cv.drawCircle(q[0], q[1], 26 * q[2], P(SODIUM, 0.55 * moving, blur=12 * q[2]))
            # reflection of the lit interior
            q0, q1 = cam.p(x, 196, z0), cam.p(x, 100, z1)
            cv.drawRect(skia.Rect(min(q0[0], q1[0]), q0[1], max(q0[0], q1[0]), q1[1]), P(FLUO, 0.06 * L))
            cv.restore()
            cv.drawPath(wp, P(wall_d, style='stroke', width=max(2, 6 * cam.p(x, 0, z0)[2])))
    # fluorescent strips
    for z0 in [z for z in range(80, BUS_LEN, 220) if (z - cam.c[2]) * cam.look > 60 or (z + 160 - cam.c[2]) * cam.look > 200]:
        for sd in (-1, 1):
            pp = cam.poly([(sd * 70, 229, z0), (sd * 50, 229, z0), (sd * 50, 229, z0 + 160), (sd * 70, 229, z0 + 160)])
            cv.drawPath(pp, P(mix((40, 44, 44), (240, 255, 244), L)))
    # handrail along the ceiling
    for sd in (-1, 1):
        a, b = cam.p(sd * 60, 200, near), cam.p(sd * 60, 200, far)
        cv.drawLine(a[0], a[1], b[0], b[1], P(mix((30, 30, 30), (190, 196, 190), L * 0.8), style='stroke', width=max(2, 5 * a[2])))
    # seats, poles, people: depth sorted
    drawables = list(items)
    for z in SEAT_ROWS:
        for sd in (-1, 1):
            drawables.append((z + 30, lambda z=z, sd=sd: _seat_back(cv, cam, sd, z, L)))
            drawables.append((z - 10, lambda z=z, sd=sd: _seat_cushion(cv, cam, sd, z, L)))
        drawables.append((z - 40, lambda z=z: _pole(cv, cam, 35 if z % 200 else -35, z - 40, L)))
    drawables.append((REAR_Z + 30, lambda: _rear_bench(cv, cam, L)))
    drawables = [d for d in drawables if (d[0] - cam.c[2]) * cam.look > 70 or getattr(d[1], 'always', False)]
    drawables.sort(key=lambda d: -(d[0] - cam.c[2]) * cam.look)
    for _, fn in drawables:
        fn()
    # light falls off toward the far end (the rear of the bus is where she sits, in near darkness)
    fx, fy, _ = cam.p(0, 110, far)
    cv.drawCircle(fx, fy, 900, P(shader=rad((fx, fy), 900, (2, 4, 6), (2, 4, 6), rear_dark, 0.0)))
    # pale green wash from the strips
    cv.drawRect(skia.Rect(0, 0, W, H), P(shader=lin((0, 0), (0, H), FLUO, FLUO, 0.07 * L, 0.0)))
    if dark > 0:
        cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0), dark))


def _seat_back(cv, cam, sd, z, L):
    x0, x1 = (BUS_HW - 6, 34) if sd > 0 else (-BUS_HW + 6, -34)
    zb = z + 30
    col = mix((16, 10, 10), (96, 40, 36), L)
    cv.drawPath(cam.poly([(x0, 45, zb), (x1, 45, zb), (x1, 98, zb + 8), (x0, 98, zb + 8)]), P(col))
    cv.drawPath(cam.poly([(x0, 90, zb + 6), (x1, 90, zb + 6), (x1, 100, zb + 8), (x0, 100, zb + 8)]), P(mix(col, (0, 0, 0), 0.3)))
    a = cam.p(x1, 100, zb + 8); b = cam.p(x1, 114, zb + 8)
    cv.drawLine(a[0], a[1], b[0], b[1], P(mix((30, 30, 30), (200, 200, 196), L), style='stroke', width=max(2, 5 * a[2])))


def _seat_cushion(cv, cam, sd, z, L):
    x0, x1 = (BUS_HW - 6, 34) if sd > 0 else (-BUS_HW + 6, -34)
    col = mix((24, 16, 16), (136, 60, 50), L)
    cv.drawPath(cam.poly([(x0, 45, z - 14), (x1, 45, z - 14), (x1, 45, z + 30), (x0, 45, z + 30)]), P(col))
    cv.drawPath(cam.poly([(x0, 20, z - 14), (x1, 20, z - 14), (x1, 45, z - 14), (x0, 45, z - 14)]), P(mix(col, (0, 0, 0), 0.4)))


def _pole(cv, cam, x, z, L):
    a, b = cam.p(x, 0, z), cam.p(x, 230, z)
    cv.drawLine(a[0], a[1], b[0], b[1], P(mix((26, 28, 28), (150, 156, 150), L * 0.85), style='stroke', width=max(2, 3.2 * a[2])))


def _rear_bench(cv, cam, L):
    col = mix((20, 14, 14), (110, 48, 40), L)
    cv.drawPath(cam.poly([(-BUS_HW + 6, 45, REAR_Z + 40), (BUS_HW - 6, 45, REAR_Z + 40), (BUS_HW - 6, 125, REAR_Z + 48), (-BUS_HW + 6, 125, REAR_Z + 48)]), P(col))
    cv.drawPath(cam.poly([(-BUS_HW + 6, 45, REAR_Z - 10), (BUS_HW - 6, 45, REAR_Z - 10), (BUS_HW - 6, 45, REAR_Z + 40), (-BUS_HW + 6, 45, REAR_Z + 40)]), P(mix(col, (255, 255, 255), 0.05)))


def person_at(cam, x, z, y=0.0):
    """ground point + toon2 scale for a figure standing/sitting at (x, z) (cm)."""
    q = cam.p(x, y, z)
    return q[0], q[1], q[2] / 6.6     # toon units: ~6.6 per cm


# ------------------------------------------------------------------ home street + facade
def home_street(cv, t, cx=0.0, gy=1500, fog_a=0.4, lamp_on=1.0):
    Wd.sky(cv, (6, 9, 20), (34, 42, 62), gy)
    for i in range(-1, 6):
        Wd.panel_building(cv, i * 330 - 120 - cx * 0.2, 300, gy - 760 - (i * 97) % 180, gy - 260, (24, 30, 46), seed=700 + i, lit=0.06,
                          floor_h=60, t=t, balconies=False)
    fog(cv, t, gy - 700, gy - 300, a=0.25 * fog_a / 0.4, seed=4, cx=cx)
    Wd.panel_building(cv, -60 - cx * 0.6, 760, gy - 1250, gy - 30, (40, 46, 66), seed=777, lit=0.05, floor_h=128, t=t)
    Wd.street_ground(cv, gy, cx)
    Wd.tree(cv, 960 - cx * 0.9, gy + 10, 700, seed=12)
    Wd.lamp(cv, 820 - cx, gy + 120, 760, on=lamp_on, side=-1, glow_r=420)
    wires(cv, cx, 190, par=0.6)
    fog(cv, t, gy - 200, gy + 200, a=fog_a, seed=9, cx=cx)
