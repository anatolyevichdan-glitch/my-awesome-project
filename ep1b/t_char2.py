from PIL import Image
from char import *
img=Image.new('RGB',(1500,700),(70,80,100))
g=G(img,1.0)
draw_hero(g,160,660,0.62,Pose(e=EXPR['neutral']))
draw_hero(g,460,660,0.62,Pose(e=EXPR['scared'],yaw=0.6,hL=(-110,-640),hR=(110,-640),bendL=-1,bendR=1))
draw_hero(g,760,660,0.62,Pose(view='side',e=EXPR['worried'],fL=(-70,0),fR=(80,-40),hL=(60,-380),hR=(-60,-380),lean=0.1))
draw_hero(g,1060,660,0.62,Pose(e=EXPR['shock'],black_eyes=True,phone=('x',0.8),hR=(70,-600),bendR=1))
draw_hero(g,1330,660,0.62,Pose(view='back'))
g.flush(); img.save('/tmp/char_test2.png')
