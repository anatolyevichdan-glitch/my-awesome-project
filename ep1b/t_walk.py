from PIL import Image
from char import *
from anim import *
img=Image.new('RGB',(1600,760),(80,90,120))
g=G(img,1.0)
for i in range(4):
    draw_hero(g,150+i*190,700,0.62,walk_side(i*math.pi/2,e=EXPR['neutral']))
for i in range(3):
    draw_hero(g,950+i*200,700,0.62,run_side(i*2.1,e=EXPR['scared']))
g.flush(); img.save('/tmp/walk.png')
