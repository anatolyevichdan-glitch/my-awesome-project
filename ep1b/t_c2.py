import sys, math
from PIL import Image
from char import G
import char2 as C
img = Image.new('RGB', (1800, 760), (70, 78, 108))
g = G(img, 1.0)
yaws = [0, 0.5, 1.0, math.pi / 2, 2.4, math.pi, -0.9]
for i, y in enumerate(yaws):
    p = C.Pose(yaw=y, e=C.EXPR['neutral'])
    p.head_yaw = 0.0
    C.draw_hero(g, 130 + i * 250, 720, 0.62, p)
g.flush()
img.save('/tmp/verify/h1.png')
img = Image.new('RGB', (1800, 760), (70, 78, 108))
g = G(img, 1.0)
for i, n in enumerate(['neutral', 'worried', 'scared', 'terror', 'shock', 'serious', 'shh']):
    p = C.Pose(yaw=0.25 * (i % 3 - 1), e=C.EXPR[n])
    C.draw_hero(g, 130 + i * 250, 1500 * 0.5 + 280, 1.0, p) if False else None
    # head close-up: place so head at centre
    s = 1.6
    p.head_yaw = 0.2 * (i % 3 - 1)
    C.draw_hero(g, 130 + i * 250, 1090, s, p)
g.flush()
img.save('/tmp/verify/h2.png')
