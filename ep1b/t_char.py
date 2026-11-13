import math
from PIL import Image
from char import *
W,H=1080,1920
img=Image.new('RGB',(1500,1000),(70,80,100))
g=G(img,0.5)
names=['neutral','worried','scared','terror','shock','serious']
for i,n in enumerate(names):
    p=Pose(e=EXPR[n]); draw_hero(g,100+i*0+ (i%3)*200*1.0,(i//3)*0+0,0.0,p) if False else None
g.flush()
def put(x,y,s,p): draw_hero(g,x,y,s,p)
put(120,520,0.45,Pose(e=EXPR['neutral']))
put(300,520,0.45,Pose(e=EXPR['worried'],yaw=0.5))
put(480,520,0.45,Pose(e=EXPR['terror'],hL=(-60,-700),hR=(60,-700)))
put(660,520,0.45,Pose(view='side',e=EXPR['scared'],fL=(-70,0),fR=(80,-40),hL=(60,-380),hR=(-60,-380),lean=0.1))
put(840,520,0.45,Pose(view='back'))
put(1020,520,0.45,Pose(e=EXPR['shock'],black_eyes=True))
put(1220,520,0.45,Pose(e=EXPR['serious'],phone=('x',0.8),hR=(40,-560)))
g.flush()
g2=G(img,0.5)
draw_entity(g2,200,980,0.5,dict(lean=0.08,head_tilt=0.2,stride=1))
draw_entity(g2,500,980,0.5,dict(view='side',phase=1.0,stride=1))
g2.flush()
img.save('/tmp/char_test.png')
