import sys, math
from PIL import Image
from char import G
import char2 as C
img = Image.new('RGB', (1800, 1800), (70, 78, 108))
g = G(img, 1.0)
names = ['neutral', 'worried', 'scared', 'terror', 'shock', 'serious', 'shh']
for i, n in enumerate(names):
    p = C.Pose(yaw=0.0, e=C.EXPR[n])
    p.head_yaw = 0.35 * (i % 3 - 1)
    p.blink = 0.0
    C.draw_hero(g, 130 + i * 250, 1700, 1.6, p)
g.flush()
img.crop((0, 130, 1800, 530)).save('/tmp/verify/h2.png')
