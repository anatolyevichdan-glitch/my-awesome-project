import math, sys
from PIL import Image, ImageDraw
from rig import *

W, H = 1600, 900
im = Image.new('RGBA', (W, H), (40, 50, 62, 255))
def fig(x, yaw, P, e=None, kind='hero'):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    render_hero(d, lay, x, 820, 420, yaw, P, e, kind)
    im.alpha_composite(lay)
fig(200, 0, dict(p=0.1, amp=1, armL=None), expr('unaware'))
fig(500, math.pi, dict(p=0.3, amp=1))
fig(850, math.pi / 2, dict(p=0.2, amp=1, run=1, head=(0, 0, 0)), expr('fear'))
fig(1150, 0.5, dict(p=0.6, amp=1, run=0, head=(0.4, 0, 0)), expr('terror'), 'double')
lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
render_entity(d, lay, 1450, 820, 300, 0, dict(p=0.2, amp=1, head=(0, 0.2, 0.15), t=1))
im.alpha_composite(lay)
im.convert('RGB').save('/tmp/t_rig.png')
# close up
im2 = Image.new('RGBA', (1000, 1000), (40, 50, 62, 255))
sp = head_sprite(300, 0.0, 0.0, expr('fear'), 'hero', 1.0, (0.9, 1, 1.1))
im2.alpha_composite(sp, (100, 100))
sp = head_sprite(180, 0.0, 0.0, expr('calm'), 'double', 1.0, (0.9, 1, 1.1))
im2.alpha_composite(sp, (500, 500))
im2.convert('RGB').save('/tmp/t_face.png')
