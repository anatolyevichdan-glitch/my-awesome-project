import sys, math
from PIL import Image
from char import G
import char2 as C, anim2 as A
mode = sys.argv[1] if len(sys.argv) > 1 else 'walk'
yaw = float(sys.argv[2]) if len(sys.argv) > 2 else math.pi / 2
n = 8
img = Image.new('RGB', (200 * n, 560), (70, 78, 108))
g = G(img, 1.0)
for i in range(n):
    ph = i / n
    if mode == 'walk': p = A.gait(ph)
    else: p = A.gait(ph, A=150, D=0.38, L=190, rho=0.78, Sx=12, Tp=0.1, Tc=0.28, lean=0.3, run=True)
    p.yaw = yaw
    p.e = C.EXPR['neutral']
    C.draw_hero(g, 100 + i * 200, 530, 0.5, p)
g.flush()
img.save('/tmp/verify/w_%s.png' % mode)
