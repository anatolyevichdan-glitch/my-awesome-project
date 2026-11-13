from PIL import Image,ImageDraw,ImageFont
import glob
ref=Image.open('../refs/RUSSIAN_SUBTITLE_FONT_PNG_EXAMPLES/POSLEDNIY_UROK_EP2_SUBTITLE_085s.png').convert('RGB').crop((300,290,780,410))
W=Image.new('RGB',(480,120*4),(40,40,60));W.paste(ref,(0,0))
d=ImageDraw.Draw(W)
def put(y,path,var=None):
    f=ImageFont.truetype(path,100)
    if var: f.set_variation_by_name(var)
    # scale so cap height=75
    bb=f.getbbox('СТОРОНУ');s=75/(bb[3]-bb[1]);f=ImageFont.truetype(path,int(100*s))
    if var: f.set_variation_by_name(var)
    d.text((100,y+10),'СТОРОНУ',font=f,fill='white',stroke_width=6,stroke_fill='black')
    bb=f.getbbox('СТОРОНУ');print(path,var,bb[2]-bb[0])
F='../fonts/'
put(120,F+'Anton-Regular.ttf');put(240,F+'Oswald[wght].ttf','Bold');put(360,F+'BebasNeue-Regular.ttf')
W.save('fontcmp.png')
