s=open('shots1.py').read()
s=s.replace("55 * max((l[3] - l[1]) / 800.0, 0.2) * zoomf(fr), (255, 210, 140), 38 * l[2]","42 * max((l[3] - l[1]) / 800.0, 0.2) * zoomf(fr), (255, 210, 140), 14 * l[2]")
s=s.replace("hx = kf(T, [(24.6, -120), (26.2, 250)])","hx = kf(T, [(24.6, -60), (26.2, 320)])").replace("hx = 250; walking = False","hx = 320; walking = False").replace("hx = kf(T, [(43.16, 250), (43.5, 150), (44.9, 100)])","hx = kf(T, [(43.16, 320), (43.5, 210), (44.9, 170)])")
s=s.replace("zrel = 900 - cam\n    s = 0.95 * 349 / zrel\n    gy_ = 700 + 300 * 1000 / zrel","zrel = 760 - cam\n    s = 0.95 * 349 / zrel\n    gy_ = 700 + 300 * 1000 / zrel")
open('shots1.py','w').write(s)
c=open('core.py').read()
c=c.replace("bloom * 0.42 * emi_gain","bloom * 0.3 * emi_gain")
c=c.replace("    return np.clip(img, 0, 255).astype(np.uint8)","    img = 255 * (np.clip(img, 0, 255) / 255) ** 1.18\n    return np.clip(img, 0, 255).astype(np.uint8)")
open('core.py','w').write(c)
h=open('char.py').read()
h=h.replace("""    # torso
    g.push(); g.xf(hip[0], hip[1], lean)
    g.poly([(-78, 0), (-96, -250), (-70, -330), (70, -330), (96, -250), (78, 0)] if not sd else [(-50, 0), (-62, -240), (-40, -330), (46, -330), (60, -240), (50, 0)], body, rim, 4)
    g.pop()""","""    # torso + tattered coat
    g.push(); g.xf(hip[0], hip[1], lean)
    wd = 1.0 if not sd else 0.62
    sw_ = math.sin(ph * 0.5 + sway * 3) * 14
    hem = []
    for i in range(7):
        xx = (-1 + i / 3.0) * 100 * wd
        hem.append((xx + sw_ * (0.4 + i * 0.1), 300 + (40 if i % 2 else -10) + 10 * math.sin(ph + i)))
    g.poly([(-70 * wd, -330), (-100 * wd, -250), (-104 * wd, 60)] + hem[::1] + [(104 * wd, 60), (100 * wd, -250), (70 * wd, -330)], body, rim, 4)
    g.pop()""")
h=h.replace("limb(hp_, j, 52); limb(j, e, 40)","limb(hp_, j, 58); limb(j, e, 44)").replace("limb(s0, j, 40); limb(j, e, 30)","limb(s0, j, 46); limb(j, e, 34)")
h=h.replace("g.ell(0, -140, 66 if not sd else 60, 82, body, rim, 4)","g.ell(0, -140, 70 if not sd else 62, 88, body, rim, 4)")
open('char.py','w').write(h)
