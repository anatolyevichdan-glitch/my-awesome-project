import json,re
a=json.load(open('align.json'));w=json.load(open('whisper.json'))
norm=lambda s:re.sub(r'[^\wё]','',s.lower().replace('ё','е'))
import difflib
A=[norm(x['word']) for x in a];W=[norm(x[0]) for x in w]
sm=difflib.SequenceMatcher(None,A,W,autojunk=False)
big=[]
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal':
        for k in range(i2-i1):
            d0=w[j1+k][1]-a[i1+k]['start'];d1=w[j1+k][2]-a[i1+k]['end']
            if abs(d0)>0.1 or abs(d1)>0.15: big.append((i1+k,a[i1+k]['word'],round(d0,2),round(d1,2)))
    else: print(tag,[x['word'] for x in a[i1:i2]],[x[0] for x in w[j1:j2]],a[i1]['start'])
print(len(big));
for b in big:print(b)
