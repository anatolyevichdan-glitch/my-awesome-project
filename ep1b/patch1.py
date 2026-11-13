s=open('shots1.py').read()
s=s.replace("""    t = T
    gy = 1500
    shop_front(fr.ga, fr.ge, gy)""","""    t = T
    gy = 1500
    zoom = 1.0 + 0.30 * sstep((T - 32.5) / 3.5) - 0.12 * sstep((T - 43.1) / 1.2)
    fr.cam(2 * math.sin(2 * t), 2 * math.cos(1.6 * t), zoom, cx=760, cy=1000)
    shop_front(fr.ga, fr.ge, gy)""")
s=s.replace("""    zoom = 1.0 + 0.30 * sstep((T - 32.5) / 3.5) - 0.12 * sstep((T - 43.1) / 1.2)
    fr.cam(0, 0, 1.0, cx=0, cy=0)       # no-op placeholder transform
""","")
s=s.replace("""    lamp_x = 960
    fr.lamps.append((lamp_x, 760, 1.0, 1560))
    lamp_post(fr.ga, fr.ge, lamp_x - 130, gy + 40, 800, 1.0)
    fr.lamps = [(lamp_x - 130 + 130, 800 - 40, 0.9, 1560)]
""","""    bp = lamp_post(fr.ga, fr.ge, 900, gy + 40, 800, 1.0)
    add_lamps(fr, [(bp[0], bp[1], 0.9, gy + 40)])
""")
s=s.replace("    return finish_kw(fog=0.12, fog_y=0.6, t=t, rain=0.8), zoom","    return finish_kw(fog=0.12, fog_y=0.6, t=t, rain=0.8)")
open('shots1.py','w').write(s)
