import json, re, os
from PIL import ImageFont

FPS = 30
a = json.load(open('align.json'))
segs = json.load(open('voiced.json'))
FONT = 'fonts/Oswald-Bold-static.ttf'
FS = int(os.environ.get('FS', '94'))
ASSFS = int(os.environ.get('ASSFS', '151'))
OUTL = os.environ.get('OUT', '8')
SH = os.environ.get('SH', '4')
pf = ImageFont.truetype(FONT, FS)


def width(t):
    return pf.getlength(t)


Y, R = 'y', 'r'
P = [(0, 4, {}), (5, 9, {}), (10, 13, {}), (14, 16, {16: Y}), (17, 20, {18: Y, 19: Y}), (21, 24, {}), (25, 27, {}), (28, 29, {}), (30, 31, {}), (32, 34, {}),
     (35, 36, {}), (37, 38, {37: Y}), (39, 40, {}), (41, 42, {41: Y, 42: Y}), (43, 46, {}), (47, 49, {48: Y, 49: Y}), (50, 51, {}), (52, 57, {}), (58, 59, {}), (60, 63, {}), (64, 65, {65: Y}), (66, 67, {}),
     (68, 70, {}), (71, 73, {}), (74, 76, {}), (77, 80, {78: Y}), (81, 81, {81: Y}), (82, 85, {}), (86, 88, {}), (89, 90, {90: Y}), (91, 94, {}), (95, 96, {}), (97, 98, {}), (99, 101, {99: R, 100: R, 101: R}),
     (102, 105, {105: Y}), (106, 109, {}), (110, 110, {110: Y}), (111, 111, {111: Y}), (112, 112, {112: Y}), (113, 115, {}), (116, 118, {}), (119, 120, {}), (121, 124, {}), (125, 128, {}),
     (129, 130, {}), (131, 133, {}), (134, 135, {134: Y, 135: Y}), (136, 138, {}), (139, 141, {}), (142, 143, {}), (144, 145, {144: R, 145: R}), (146, 150, {}), (151, 152, {}), (153, 154, {}), (155, 158, {}),
     (159, 161, {}), (162, 165, {}), (166, 168, {}), (169, 171, {}), (172, 174, {}), (175, 176, {176: Y}), (177, 177, {}), (178, 181, {178: R, 179: R, 180: R, 181: R}), (182, 183, {}), (184, 185, {}), (186, 188, {}),
     (189, 192, {190: R, 191: R, 192: R}), (193, 195, {}), (196, 199, {}), (200, 203, {203: Y}), (204, 205, {}), (206, 207, {206: R, 207: R})]
assert P[0][0] == 0 and P[-1][1] == 207 and all(P[i][1] + 1 == P[i + 1][0] for i in range(len(P) - 1))


def fr(t):
    return round(t * FPS)


def clean(w):
    return re.sub(r'[.,;:]+$', '', w.upper())


def near_seg(t, lo, hi, which):
    best = None
    for s in segs:
        v = s[which]
        if t - lo <= v <= t + hi and (best is None or abs(v - t) < abs(best - t)):
            best = v
    return best


notes = []
ev = []
for pi, (f, l, em) in enumerate(P):
    s = a[f]['start']
    e = a[l]['end']
    se = near_seg(e, 0.05, 0.6, 1)
    if se is not None and se > e + 0.03 and (l + 1 >= len(a) or a[l + 1]['start'] - se > 0.15):
        notes.append('end %d %s: %.2f->%.2f (voiced tail)' % (l, a[l]['word'], e, se))
        e = se
    ss = near_seg(s, 0.12, 0.03, 0)
    if ss is not None and abs(ss - s) > 0.015:
        notes.append('start %d %s: %.2f->%.2f (voiced onset)' % (f, a[f]['word'], s, ss))
        s = ss
    ev.append(dict(f=f, l=l, s=s, e=e, em=em))
for i, x in enumerate(ev):
    x['ds'] = x['s']
    x['de'] = x['e'] + 0.08
    if i + 1 < len(ev):
        x['de'] = min(x['de'], ev[i + 1]['s'])
for i, x in enumerate(ev):
    ks = fr(x['ds'])
    ke = fr(x['de'])
    if i > 0 and ks < ev[i - 1]['ke']:
        ks = ev[i - 1]['ke']
    if ke <= ks + 3:
        ke = ks + 4
    if i + 1 < len(ev) and ke > fr(ev[i + 1]['ds']):
        ke = max(ks + 3, fr(ev[i + 1]['ds']))
    x['ks'] = ks
    x['ke'] = ke


def split_lines(words):
    t = ' '.join(words)
    if width(t) <= 860 and len(words) < 7:
        return [t]
    best = None
    for k in range(1, len(words)):
        l1 = ' '.join(words[:k])
        l2 = ' '.join(words[k:])
        m = max(width(l1), width(l2))
        if best is None or m < best[0]:
            best = (m, [l1, l2])
    if best[0] > 900: print('WIDE', words, best[0])
    return best[1]


CY = '&H0000D4FF&'
CR = '&H002020E0&'
CW = '&H00FFFFFF&'


def ass_t(k):
    cs = (k * 100) // FPS
    return '%d:%02d:%02d.%02d' % (cs // 360000, (cs // 6000) % 60, (cs // 100) % 60, cs % 100)


def srt_t(k):
    ms = round(k * 1000 / FPS)
    return '%02d:%02d:%02d,%03d' % (ms // 3600000, (ms // 60000) % 60, (ms // 1000) % 60, ms % 1000)


dial = []
srt = []
out = []
for n, x in enumerate(ev):
    ws = [clean(a[i]['word']) for i in range(x['f'], x['l'] + 1)]
    lines = split_lines(ws)
    wi = 0
    txt = ''
    for li, ln in enumerate(lines):
        toks = ln.split(' ')
        for j, wd in enumerate(toks):
            gi = x['f'] + wi
            wi += 1
            c = x['em'].get(gi)
            seg = wd if c is None else '{\\c%s}%s{\\c%s}' % (CY if c == 'y' else CR, wd, CW)
            txt += seg + (' ' if j < len(toks) - 1 else '')
        if li < len(lines) - 1:
            txt += '\\N'
    x['text'] = ' '.join(ws)
    dial.append('Dialogue: 0,%s,%s,Sub,,0,0,0,,{\\fad(70,80)\\fscx94\\fscy94\\t(0,120,\\fscx100\\fscy100)}%s' % (ass_t(x['ks']), ass_t(x['ke']), txt))
    srt.append('%d\n%s --> %s\n%s\n' % (n + 1, srt_t(x['ks']), srt_t(x['ke']), '\n'.join(lines)))
    out.append(dict(start=round(x['ks'] / FPS, 4), end=round(x['ke'] / FPS, 4), start_frame=x['ks'], end_frame=x['ke'], text=x['text'], lines=lines,
                    emph=[dict(word=clean(a[i]['word']), color={'y': 'yellow', 'r': 'red'}[c]) for i, c in sorted(x['em'].items())],
                    words=[dict(word=clean(a[i]['word']), start=round(a[i]['start'], 3), end=round(a[i]['end'], 3)) for i in range(x['f'], x['l'] + 1)]))
hdr = '''[Script Info]
; Subtitles for DON'T LOOK BACK EP1 (remaster). Font: Oswald Bold (static instance of Oswald[wght].ttf, wght=700)
; Timing: every event is snapped to the 30 fps grid and written as (frame*100 div 30) centiseconds.
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: None

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Oswald,%d,&H00FFFFFF,&H0000D4FF,&H00000000,&H78000000,-1,0,0,0,100,100,0.5,0,1,%s,%s,2,90,90,272,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
''' % (ASSFS, OUTL, SH)
open('subs_final.ass', 'w', encoding='utf-8').write(hdr + '\n'.join(dial) + '\n')
open('subs_final.srt', 'w', encoding='utf-8').write('\n'.join(srt))
json.dump(dict(fps=FPS, events=out), open('subs_events.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
open('adjust_notes.txt', 'w').write('\n'.join(notes))
print(len(ev), 'events;', len(notes), 'adjustments; maxwidth', max(width(l) for e in out for l in e['lines']))
