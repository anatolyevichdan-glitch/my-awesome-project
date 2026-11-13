import re
# char.py: mask support
s=open('char.py').read()
a=s.index('class G:'); b=s.index('def ik(')
cls=s[a:b]
cls=cls.replace('col(','self.c(')
cls=cls.replace("        self.stack = []\n","        self.stack = []\n        self.mask = False\n",1)
cls=cls.replace("    def push(self):","    def c(self, c, a=255):\n        return (0, 0, 0, a) if self.mask else col(c, a)\n\n    def push(self):",1)
s=s[:a]+cls+s[b:]
open('char.py','w').write(s)
# anim.py: shoulder rel and hand heights
s=open('anim.py').read()
s=s.replace("SH_REL = -(HIP_H) - TORSO + 22","SH_REL = -(HIP_H) - (TORSO - 52) + 22")
s=s.replace("SH_REL+300","SH_REL+292").replace("SH_REL+310","SH_REL+298")
open('anim.py','w').write(s)
s=open('shots1.py').read()
s=s.replace("SH_REL + 300","SH_REL + 292").replace("SH_REL + 250","SH_REL + 240")
s=s.replace("""    ends = draw_hero(fr.ga, x, y, s, p, tint=tint)
    if occ: draw_hero(fr.go, x, y, s, p)""","""    ends = draw_hero(fr.ga, x, y, s, p, tint=tint)
    fr.ge.mask = True; draw_hero(fr.ge, x, y, s, p); fr.ge.mask = False
    if occ: draw_hero(fr.go, x, y, s, p)""")
# phone: higher res text & placement
s=s.replace("hand = kf(T, [(17.6, (118, -330)), (18.5, (118, -330)), (19.15, (80, -600)), (22.9, (84, -604)), (23.6, (90, -520))])","hand = kf(T, [(17.6, (118, -330)), (18.5, (118, -330)), (19.15, (84, -430)), (22.9, (86, -434)), (23.6, (96, -380))])")
s=s.replace("hand = (84, -604)\n","hand = (86, -434)\n")
s=s.replace("draw_phone_big(fr, root, s, ends['R'] if False else hand, 1.0, msgs, T, glow=1.0, hdr=True, flash=flash, buzz=0)","draw_phone_big(fr, root, s, hand, 1.25, msgs, T, glow=1.0, hdr=True, flash=flash, buzz=0)")
s=s.replace("draw_phone_big(fr, root, s, hand, 1.0, msgs, T, glow=1.0, hdr=True, buzz=0)","draw_phone_big(fr, root, s, hand, 1.25, msgs, T, glow=1.0, hdr=True, buzz=0)")
open('shots1.py','w').write(s)
# core: weaker glows
s=open('core.py').read()
s=s.replace("img = img + emi * emi_gain * 0.92 + bloom * 0.75 * emi_gain","img = img + emi * emi_gain * 0.92 + bloom * 0.42 * emi_gain")
open('core.py','w').write(s)
# bg: dual trees and lamp poles
s=open('bg.py').read()
s=s.replace("""    c = (34, 34, 46)
    top = (x, gy - h)
    g.capsule((x, gy), top, 24, c)
    arm_end = (x + 130, gy - h - 22)
    g.capsule(top, arm_end, 16, c)
    g.poly([(arm_end[0] - 52, arm_end[1] - 8), (arm_end[0] + 52, arm_end[1] - 8), (arm_end[0] + 36, arm_end[1] + 26), (arm_end[0] - 36, arm_end[1] + 26)], c)
""","""    c = (34, 34, 46)
    top = (x, gy - h)
    arm_end = (x + 130, gy - h - 22)
    for gg, mk in ((g, False), (ge, True)):
        gg.mask = mk
        gg.capsule((x, gy), top, 24, c)
        gg.capsule(top, arm_end, 16, c)
        gg.poly([(arm_end[0] - 52, arm_end[1] - 8), (arm_end[0] + 52, arm_end[1] - 8), (arm_end[0] + 36, arm_end[1] + 26), (arm_end[0] - 36, arm_end[1] + 26)], c)
        gg.mask = False
""")
s=s.replace("def bare_tree(g, x, gy, h=520, seed=1, col=(34, 30, 38)):\n    top = (x, gy - h)","def bare_tree(g, x, gy, h=520, seed=1, col=(34, 30, 38), ge=None):\n    if ge is not None:\n        ge.mask = True; bare_tree(ge, x, gy, h, seed, col); ge.mask = False\n    top = (x, gy - h)")
s=s.replace("bare_tree(g, x, gy + 40, 560, seed + k)","bare_tree(g, x, gy + 40, 560, seed + k, ge=ge)")
s=s.replace("bare_tree(g, 1000 - off1, gy + 50, 640, seed)","bare_tree(g, 1000 - off1, gy + 50, 640, seed, ge=ge)").replace("bare_tree(g, 40 - off1, gy + 60, 560, seed + 1)","bare_tree(g, 40 - off1, gy + 60, 560, seed + 1, ge=ge)")
# persp tree & lamp pole dual
s=s.replace("""                    c = fogc((40, 34, 40), fade)
                    top = (base[0], base[1] - 380 * s)
                    g.capsule(base, top, max(3, 26 * s), c)
                    for br in range(5):
                        ang = -math.pi / 2 + (br - 2) * 0.55
                        L = (170 + hsh(k, br, seed) * 90) * s
                        p1 = (top[0] + math.cos(ang) * L, top[1] + math.sin(ang) * L)
                        g.capsule((top[0], top[1] + 60 * s), p1, max(2, 12 * s), c)
                        p2 = (p1[0] + math.cos(ang + 0.5) * L * 0.5, p1[1] + math.sin(ang + 0.5) * L * 0.5)
                        g.capsule(p1, p2, max(1.5, 7 * s), c)""","""                    c = fogc((40, 34, 40), fade)
                    top = (base[0], base[1] - 380 * s)
                    for gg, mk in ((g, False), (ge, True)):
                        gg.mask = mk
                        gg.capsule(base, top, max(3, 26 * s), c)
                        for br in range(5):
                            ang = -math.pi / 2 + (br - 2) * 0.55
                            L = (170 + hsh(k, br, seed) * 90) * s
                            p1 = (top[0] + math.cos(ang) * L, top[1] + math.sin(ang) * L)
                            gg.capsule((top[0], top[1] + 60 * s), p1, max(2, 12 * s), c)
                            p2 = (p1[0] + math.cos(ang + 0.5) * L * 0.5, p1[1] + math.sin(ang + 0.5) * L * 0.5)
                            gg.capsule(p1, p2, max(1.5, 7 * s), c)
                        gg.mask = False""")
s=s.replace("""                g.capsule(foot, top, pw, pc)
                g.capsule(top, arm, pw * 0.7, pc)
                inten""","""                for gg, mk in ((g, False), (ge, True)):
                    gg.mask = mk
                    gg.capsule(foot, top, pw, pc)
                    gg.capsule(top, arm, pw * 0.7, pc)
                    gg.mask = False
                inten""")
open('bg.py','w').write(s)
# glows weaker
s=open('shots1.py').read()
s=s.replace("fr.glows.append((l[0], l[1], 70 * max((l[3] - l[1]) / 800.0, 0.2) * zoomf(fr), (255, 210, 140), 70 * l[2]))","fr.glows.append((l[0], l[1], 55 * max((l[3] - l[1]) / 800.0, 0.2) * zoomf(fr), (255, 210, 140), 38 * l[2]))")
# phone screen supersampled
a=s.index("def phone_screen"); b=s.index("def draw_phone_big")
new='''def phone_screen(w, h, msgs, t, hdr=True, flash=0.0):
    """msgs: [(text, kind, t_appear)]; drawn at 2x for crisp text"""
    m = 2
    W2, H2 = w * m, h * m
    im = Image.new('RGB', (W2, H2), (12, 17, 30))
    d = ImageDraw.Draw(im)
    if hdr:
        d.rectangle([0, 0, W2, 62 * m], fill=(24, 32, 52))
        d.ellipse([12 * m, 12 * m, 50 * m, 50 * m], fill=(70, 80, 110)); d.text((31 * m, 31 * m), '?', fill=(210, 220, 240), font=font(24 * m), anchor='mm')
        d.text((60 * m, 24 * m), 'Неизвестный номер', fill=(225, 232, 245), font=font(15 * m), anchor='lm')
        d.text((60 * m, 46 * m), 'сейчас', fill=(140, 150, 175), font=font(13 * m), anchor='lm')
    y = 84 * m
    for text, kind, ta in msgs:
        if t < ta: continue
        age = t - ta
        pop = sstep(age / 0.18)
        sz = (19 if kind == 'n' else 20) * m
        lines = []; cur = ''
        for wd in text.split():
            tr = (cur + ' ' + wd).strip()
            if d.textlength(tr, font=font(sz)) > W2 - 60 * m and cur:
                lines.append(cur); cur = wd
            else: cur = tr
        lines.append(cur)
        bh = len(lines) * (sz + 8 * m) + 22 * m
        bw = max(d.textlength(l, font=font(sz)) for l in lines) + 34 * m
        fill = (44, 52, 74) if kind == 'n' else (96, 14, 20)
        tc = (236, 240, 250) if kind == 'n' else (255, 110, 110)
        yy = y + int((1 - pop) * 18 * m)
        d.rounded_rectangle([14 * m, yy, 14 * m + bw, yy + bh], radius=18 * m, fill=fill)
        for i, l in enumerate(lines):
            d.text((14 * m + 17 * m, yy + 12 * m + i * (sz + 8 * m)), l, fill=tc, font=font(sz))
        y += bh + 16 * m
    if flash > 0:
        im = Image.blend(im, Image.new('RGB', (W2, H2), (230, 240, 255)), flash * 0.5)
    return im


'''
s=s[:a]+new+s[b:]
open('shots1.py','w').write(s)
