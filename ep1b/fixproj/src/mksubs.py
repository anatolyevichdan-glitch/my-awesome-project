"""Build styled ASS + plain SRT from forced-aligned word timestamps (align.json)."""
import json, re
from PIL import ImageFont

FPS = 30.0
FONT_FILE = 'fonts/Montserrat-ExtraBold.ttf'
FS = 60
MAXW = 930
pil = ImageFont.truetype(FONT_FILE, FS)

A = json.load(open('align.json'))
WORDS = A

RED = {'не оборачивайся', 'он не за тобой', 'он внутри тебя', 'нет', 'он нашёл нас обоих', 'кто из вас настоящий'}
YEL = {'камера', 'силуэт', 'замирает', 'тсс', 'фонари', 'гаснуть', 'двойник', 'чёрные', 'испуганным', 'чёрная', 'фигура', 'один', 'второй', 'третий',
       'бежать', 'палец', 'отражение', 'странность', 'врезаешься', 'шепчет', 'убегать'}


STOP = {'по','в','на','за','к','и','с','не','от','из','во','а','но','он','ты','я','то','та'}


def norm(w): return re.sub(r'[^\w\-ё]', '', w.lower())


# ---- split into sentences
sent = []
cur = []
for i, w in enumerate(WORDS):
    cur.append(i)
    if re.search(r'[.?!]$', w['word']):
        sent.append(cur); cur = []
if cur: sent.append(cur)

phrases = []


def width(ws): return pil.getlength(' '.join(w for w in ws))


def split_two_lines(idx):
    ws = [WORDS[i]['word'] for i in idx]
    if width(ws) <= MAXW: return [idx], None
    best = None
    for k in range(1, len(ws)):
        a, b = ws[:k], ws[k:]
        wa, wb = width(a), width(b)
        if wa <= MAXW and wb <= MAXW:
            sc = max(wa, wb)
            if best is None or sc < best[0]: best = (sc, k)
    if best: return [idx[:best[1]], idx[best[1]:]], True
    return None, None


for s in sent:
    ls, ok = split_two_lines(s)
    if ls is not None:
        phrases.append(s)
        continue
    # too long: split at comma or middle into two phrases
    k = next((j + 1 for j, i in enumerate(s) if WORDS[i]['word'].endswith(',')), len(s) // 2)
    phrases.append(s[:k]); phrases.append(s[k:])

# re-merge "Нет." with next? keep separate. Build events.
ev = []
for n, idx in enumerate(phrases):
    ws = [WORDS[i] for i in idx]
    text = ' '.join(w['word'] for w in ws)
    key = re.sub(r'\s+', ' ', re.sub(r'[.,!?]', '', text.lower())).strip()
    red = key in RED
    # tokens
    toks = []
    for j, w in enumerate(ws):
        t = w['word']
        if red: t = t.upper()
        y = (not red) and norm(w['word']) in YEL
        if (not red) and norm(w['word']) == 'сам' and j > 0 and norm(ws[j - 1]['word']) == 'ты': y = True
        if (not red) and norm(w['word']) == 'ты' and j + 1 < len(ws) and norm(ws[j + 1]['word']) == 'сам': y = True
        if (not red) and norm(w['word']) == 'ты' and y:
            t = t.upper()
        if (not red) and norm(w['word']) == 'сам': t = t.upper()
        toks.append(dict(t=t, s=w['start'], e=w['end'], y=y))
    first = ws[0]['start']; last = ws[-1]['end']
    ev.append(dict(idx=idx, toks=toks, red=red, start=first, end=last, key=key))

# frame-snapped timing
for i, e in enumerate(ev):
    s = round(e['start'] * FPS) / FPS
    en = round((e['end'] + 0.12) * FPS) / FPS
    if i + 1 < len(ev):
        nxt = round(ev[i + 1]['start'] * FPS) / FPS
        en = min(en, nxt - 1 / FPS)
    e['S'] = s; e['E'] = max(en, min(s + 0.7, (round(ev[i + 1]['start'] * FPS) / FPS - 1 / FPS) if i + 1 < len(ev) else 999))

WHITE = '&H00FFFFFF&'
YELLOW = '&H0000D4FF&'
REDC = '&H002A21E8&'
REDHI = '&H00A0A0FF&'


def ts_ass(t):
    cs = int(round(t * 100))
    h = cs // 360000; m = cs // 6000 % 60; s = cs // 100 % 60; c = cs % 100
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def ts_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def line_break(toks):
    ws = [t['t'] for t in toks]
    if width(ws) <= MAXW: return None
    best = None
    for k in range(1, len(ws)):
        wa, wb = width(ws[:k]), width(ws[k:])
        if wa <= MAXW and wb <= MAXW:
            sc = abs(wa - wb) * 0.3 + max(wa, wb) + (400 if norm(ws[k - 1]) in STOP else 0)
            if best is None or sc < best[0]: best = (sc, k)
    return best[1] if best else len(ws) // 2


ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Montserrat ExtraBold,{FS},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0.5,0,1,5.5,2.5,2,70,70,330,1
Style: Final,Montserrat ExtraBold,76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,6.5,3,2,50,50,330,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
srt = []
for n, e in enumerate(ev, 1):
    toks = e['toks']
    brk = line_break(toks)
    final = e['key'] == 'кто из вас настоящий'
    d_ms = int(round((e['E'] - e['S']) * 1000))
    parts = []
    for j, t in enumerate(toks):
        if brk is not None and j == brk: parts[-1] = parts[-1].rstrip(' ') + r'\N'
        ts_ = int(round((t['s'] - e['S']) * 1000)); te_ = int(round((t['e'] - e['S']) * 1000))
        te_ = max(te_, ts_ + 120)
        if e['red']:
            tag = f"{{\\1c{REDC}\\t({max(ts_ - 20, 0)},{ts_ + 70},\\1c{REDHI})\\t({te_},{te_ + 160},\\1c{REDC})}}"
        elif t['y']:
            tag = f"{{\\1c{WHITE}\\t({max(ts_ - 20, 0)},{ts_ + 70},\\1c{YELLOW})}}"
        else:
            tag = f"{{\\1c{WHITE}\\t({max(ts_ - 20, 0)},{ts_ + 70},\\1c{YELLOW})\\t({te_},{te_ + 150},\\1c{WHITE})}}"
        parts.append(tag + t['t'] + ' ')
    body = ''.join(parts).rstrip(' ')
    pop = f"{{\\fad(70,90)\\fscx93\\fscy93\\t(0,140,\\fscx100\\fscy100)}}"
    if final:
        pop = f"{{\\fad(220,0)\\fscx96\\fscy96\\t(0,{d_ms},\\fscx108\\fscy108)\\blur0.6}}"
    style = 'Final' if final else 'Main'
    ass += f"Dialogue: 0,{ts_ass(e['S'])},{ts_ass(e['E'])},{style},,0,0,0,,{pop}{body}\n"
    txt = ' '.join(t['t'] for t in toks)
    if brk is not None: txt = ' '.join(t['t'] for t in toks[:brk]) + '\n' + ' '.join(t['t'] for t in toks[brk:])
    # plain SRT keeps natural case
    plain = ' '.join(WORDS[i]['word'] for i in e['idx'])
    if brk is not None: plain = ' '.join(WORDS[i]['word'] for i in e['idx'][:brk]) + '\n' + ' '.join(WORDS[i]['word'] for i in e['idx'][brk:])
    srt.append(f"{n}\n{ts_srt(e['S'])} --> {ts_srt(e['E'])}\n{plain}\n")
open('subs_fixed.ass', 'w', encoding='utf-8').write(ass)
open('subs_fixed.srt', 'w', encoding='utf-8').write('\n'.join(srt))
json.dump([dict(S=e['S'], E=e['E'], text=' '.join(t['t'] for t in e['toks']), red=e['red']) for e in ev], open('subs_events.json', 'w'), ensure_ascii=False, indent=1)
print(len(ev), 'phrases')
