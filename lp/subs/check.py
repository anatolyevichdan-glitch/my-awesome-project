import json
from PIL import ImageFont
f=ImageFont.truetype('fonts/Inter-Bold.ttf',55)
E=json.load(open('events.json'));W=json.load(open('../audio/words.json'))['words']
ws=[w['s'] for w in W]
for i,(s,e,L) in enumerate(E):
    assert len(L)<=2
    assert max(f.getlength(l) for l in L)<=900,L
    if i+1<len(E): assert e<=E[i+1][0],('overlap',i)
    assert e>s
    first=min(ws,key=lambda x:abs(x-s)); assert s>=first-0.05
print('ok',len(E),'last end',E[-1][1])
