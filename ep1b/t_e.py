import sys, math
from PIL import Image
from char import G
import entity3d as E
img = Image.new('RGB', (1800, 1000), (60, 66, 100))
g = G(img, 1.0)
yaws = [0, 0.6, math.pi / 2, math.pi / 2, 2.4, math.pi]
for i, y in enumerate(yaws):
    p = E.creature_walk(i * 0.17) if i != 5 else E.CPose()
    p.yaw = y
    p.eyes = 1
    out = E.draw_creature(g, 150 + i * 290, 960, 0.33, p)
g.flush()
img2 = img.copy()
g2 = G(img2, 1.0)
for i, y in enumerate(yaws):
    p = E.creature_walk(i * 0.17) if i != 5 else E.CPose()
    p.yaw = y
    p.mouth = 0.6 if i == 0 else 0.0
    # eyes on top
    out = E.draw_creature(G(Image.new('RGB', (10, 10)), 1.0), 150 + i * 290, 960, 0.33, p)
    E.draw_creature_glow(g2, out, 0.33)
g2.flush()
img2.save('/tmp/verify/e1.png')
