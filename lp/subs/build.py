import json,os,re
from PIL import ImageFont
HERE=os.path.dirname(os.path.abspath(__file__))
FS=80; PILFS=54.6; BASELINE_BOTTOM=1797; MAXW=900   # same as approved rem/subs2 style
font=ImageFont.truetype(f'{HERE}/fonts/Inter-Bold.ttf',round(PILFS))
W=json.load(open('/tmp/hoplite/workspace/lp/audio/words.json'))['words']
SCRIPT="""Ты выходишь из колледжа в 11 вечера. / Телефон почти разряжен. / На остановке никого. / Через пять минут подъезжает старый автобус номер 13. / Ты заходишь внутрь. / В салоне сидят семь человек. / Все молчат. / Ты оплачиваешь проезд и садишься у окна. / Автобус трогается. / Через несколько минут замечаешь странность. / За окном снова та же остановка, на которой ты сел. / Ты думаешь, что водитель поехал по кругу. / Но через минуту остановка появляется снова. / Ты подходишь к водителю. / Спрашиваешь, куда он едет. / Тот молчит. / Ты касаешься его плеча. / Водитель медленно поворачивает голову. / У него закрыты глаза. / Ты отшатываешься. / Сзади раздаётся женский голос: / «Не трогай его. / Он уже давно мёртв». / Ты оборачиваешься. / На последнем сиденье — старуха. / Она смотрит прямо на тебя. / «Садись, мальчик. / До конечной ещё далеко». / Ты бросаешься к дверям. / Нажимаешь кнопку остановки. / Ничего. / В этот момент телефон вибрирует. / Приходит сообщение от мамы: / «Сынок, где ты? / По новостям сказали, что автобус номер 13 разбился». / Ты открываешь новость. / Авария произошла двадцать лет назад. / Погибли водитель и семь пассажиров. / Ты начинаешь считать людей в салоне. / Один. / Два. / Три. / Четыре. / Пять. / Шесть. / Семь. / Старуха улыбается. / «А теперь нас восемь». / Внезапно автобус резко тормозит. / Двери открываются. / За ними — твоя родная улица. / Ты выбегаешь наружу. / Автобус уезжает. / Ты с облегчением достаёшь телефон и звонишь маме. / Она отвечает. / Ты говоришь: / «Мам, я уже дома». / Несколько секунд тишины. / Потом она шёпотом произносит: / «Сынок, не заходи в квартиру. / Ты уже пришёл домой десять минут назад». / Ты медленно поднимаешь глаза. / В окне своей комнаты видишь человека. / Он стоит неподвижно. / А потом машет тебе рукой. / И ты понимаешь. / Это ты сам. / Только его лицо полностью обгорело. / Продолжение следует."""
phrases=[p.strip().replace(' —','\u00a0—').split(' ') for p in SCRIPT.split(' / ')]
def width(t): return font.getlength(t.replace('\u00a0',' '))
def norm(w): return re.sub(r'[^\w]','',w.lower().replace('ё','е'))
# map each script word to a whisper token index (whisper merged "До конечной" into one token)
spans=[];ti=0;warn=[]
for p in phrases:
    idx=[]
    for j,w in enumerate(p):
        idx.append(ti)
        if w=='До': warn.append('До конечной: whisper token "%s" shared'%W[ti]['w']); continue  # next word shares token
        ti+=1
    spans.append(idx)
assert ti==len(W),(ti,len(W))
# same-token words ("До","конечной") get split in half
def wtime(i,p,j):
    t=W[i]
    if p[j]=='До': m=t['s']+(t['e']-t['s'])*0.4; return t['s'],m
    if j>0 and p[j-1]=='До': m=t['s']+(t['e']-t['s'])*0.4; return m,t['e']
    return t['s'],t['e']
def split2(ws):
    best=None
    for k in range(1,len(ws)):
        w=max(width(' '.join(ws[:k])),width(' '.join(ws[k:])))
        if best is None or w<best[0]: best=(w,k)
    return best
def chunks(ws):  # -> list of word-index groups, each fits in <=2 lines
    if len(ws)==1 or width(' '.join(ws))<=MAXW: return [list(range(len(ws)))]
    b=split2(ws)
    if b[0]<=MAXW: return [list(range(len(ws)))]
    # too long for two lines: break into two events at the best point
    k=b[1];return [list(range(k)),list(range(k,len(ws)))]
EV=[]
for p,idx in zip(phrases,spans):
    def rec(js):
        sub=[p[j] for j in js]
        if len(sub)>1 and (lambda b:b[0]>MAXW)(split2(sub)) and width(' '.join(sub))>MAXW:
            k=split2(sub)[1];rec(js[:k]);rec(js[k:]);return
        EV.append(js)
    for g in chunks(p): rec(g)
E=[]
for js_ in EV:
    pass
# rebuild with timing
E=[]
pi=0
flat=[(pi_,j) for pi_,p in enumerate(phrases) for j in range(len(p))]
# EV order matches flat order
pos=0
for js in EV:
    items=flat[pos:pos+len(js)];pos+=len(js)
    pidx=items[0][0];p=phrases[pidx];idx=spans[pidx]
    ws=[p[j] for _,j in items]
    s=wtime(idx[items[0][1]],p,items[0][1])[0]
    e=wtime(idx[items[-1][1]],p,items[-1][1])[1]
    E.append([s,e,ws])
assert pos==len(flat)
for n,x in enumerate(E):
    nxt=E[n+1][0] if n+1<len(E) else 1e9
    x[1]=max(min(x[1]+0.25,nxt-0.03),x[0]+0.3 if nxt-0.03>x[0]+0.3 else x[0]+0.05)
    x[1]=min(x[1],nxt-0.02)
def ts_ass(t):
    cs=int(t*100+1e-6);h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100)
    return f'{h}:{m:02d}:{s:02d}.{cs:02d}'
def ts_srt(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
def lines(ws):
    if width(' '.join(ws))<=MAXW: return [' '.join(ws)]
    k=split2(ws)[1];return [' '.join(ws[:k]),' '.join(ws[k:])]
head=f'''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: None

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter,{FS},&H00FFFFFF,&H00FFFFFF,&H00101010,&H99000000,-1,0,0,0,100,100,0,0,1,4,3,2,90,90,{1920-BASELINE_BOTTOM},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
tag='{\\fad(70,70)\\fscx97\\fscy97\\t(0,120,\\fscx100\\fscy100)}'
out=[];srt=[];res=[]
for n,(s,e,ws) in enumerate(E):
    L=[l.replace('\u00a0',' ') for l in lines(ws)];res.append((s,e,L))
    out.append(f'Dialogue: 0,{ts_ass(s)},{ts_ass(e)},Sub,,0,0,0,,{tag}'+'\\N'.join(L))
    srt.append(f'{n+1}\n{ts_srt(s)} --> {ts_srt(e)}\n'+'\n'.join(L)+'\n')
open(f'{HERE}/subs.ass','w').write(head+'\n'.join(out)+'\n')
open(f'{HERE}/subs.srt','w').write('\n'.join(srt))
json.dump(res,open(f'{HERE}/events.json','w'),ensure_ascii=False)
print('events',len(E),'maxwidth',round(max(width(l) for _,_,L in res for l in L)),'two-line',sum(len(L)==2 for _,_,L in res))
print(warn)
