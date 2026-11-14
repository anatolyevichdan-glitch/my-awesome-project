import sys, json, subprocess, os, time
from shots import *

SUBS_TEXT = [
    "Вода уже по горло.", "Ты держишь маленького ребёнка над головой.", "Внезапно металлическую дверь срывает с петель.",
    "Огромная волна сбивает тебя с ног.", "Темнота.", "За 10 минут до этого.", "Ты заходишь в лифт торгового центра.",
    "Внутри охранник, девушка и мужчина с сыном.", "Лифт начинает спускаться.", "Вдруг кабину резко трясёт.",
    "На табло минус третий этаж.", "Потом минус пятый.", "Минус седьмой.", "Охранник бледнеет.",
    "«У нас только два подземных этажа!»", "Двери открываются.", "Перед вами тёмный тоннель.", "По полу течёт вода.",
    "Из динамиков раздаётся:", "«Аварийный сброс через три минуты».", "Вы бросаетесь к лестнице.", "Но позади раздаётся грохот.",
    "Тоннель начинает затапливать.", "Мужчину уносит потоком.", "Ребёнок кричит.", "Ты хватаешь его и бежишь к двери.",
    "Вода уже по пояс.", "Потом по грудь.", "Охранник пытается открыть выход.", "И вдруг дверь начинает выгибаться внутрь.",
    "Девушка кричит:", "«Не открывай!»", "Но замок ломается.", "Ты поднимаешь ребёнка над головой.",
    "Огромная волна врывается в тоннель.", "Вас сбивает с ног.", "И последнее, что ты видишь под водой…",
    "рука ребёнка, выскальзывающая из твоей ладони.", None,
]
TR = json.load(open('transcript.json'))
assert len(TR) == len(SUBS_TEXT), (len(TR), len(SUBS_TEXT))
SUBS = []
for i, (seg_, txt) in enumerate(zip(TR, SUBS_TEXT)):
    if txt is None:
        continue
    toks = txt.split()
    ws = [w for w in seg_['words'] if w['w'].strip('.,!?«»—:') != '' or w['w'] == '10']
    if len(ws) != len(toks):
        print('WORD MISMATCH', i, toks, [w['w'] for w in ws], file=sys.stderr)
        # fall back to even spacing
        ws = [dict(s=seg_['start'] + (seg_['end'] - seg_['start']) * k / len(toks), e=seg_['start'] + (seg_['end'] - seg_['start']) * (k + 1) / len(toks)) for k in range(len(toks))]
    nxt = TR[i + 1]['start'] if i + 1 < len(TR) else seg_['end'] + 0.6
    SUBS.append(dict(a=seg_['start'] - 0.06, b=min(nxt - 0.03, seg_['end'] + 0.45), toks=toks, ws=[(w['s'], w['e']) for w in ws]))

SUB_FONT = skia.Font(FONT_XB, 64)
SPACE = SUB_FONT.measureText(' ')


def layout(toks, maxw=900):
    lines, cur, cw = [], [], 0.0
    for k, tk in enumerate(toks):
        w = SUB_FONT.measureText(tk)
        if cur and cw + SPACE + w > maxw:
            lines.append(cur)
            cur, cw = [], 0.0
        cur.append((k, tk, w))
        cw += (SPACE if len(cur) > 1 else 0) + w
    if cur:
        lines.append(cur)
    if len(lines) > 2:  # rebalance into two lines
        half = sum(SUB_FONT.measureText(t) for t in toks) / 2
        a, acc = [], 0.0
        for k, tk in enumerate(toks):
            w = SUB_FONT.measureText(tk)
            if acc + w / 2 > half and a:
                break
            a.append((k, tk, w))
            acc += w + SPACE
        b = [(k, tk, SUB_FONT.measureText(tk)) for k, tk in enumerate(toks) if k >= len(a)]
        lines = [a, b]
    return lines


def draw_subs(c, T):
    for s in SUBS:
        if s['a'] <= T < s['b']:
            a = sm(ramp(T, s['a'], s['a'] + 0.1)) * (1 - sm(ramp(T, s['b'] - 0.1, s['b'])))
            lines = layout(s['toks'])
            lh = 80
            y0 = 1235 - (len(lines) - 1) * lh / 2
            for li, line in enumerate(lines):
                tw = sum(w for _, _, w in line) + SPACE * (len(line) - 1)
                x = 540 - tw / 2
                y = y0 + li * lh
                for k, tk, w in line:
                    ws, we = s['ws'][k]
                    hl = ramp(T, ws - 0.04, ws + 0.04) * (1 - ramp(T, we + 0.02, we + 0.12))
                    col = mixh('#ffffff', '#ffd23f', hl)
                    c.drawString(tk, x + 3, y + 5, SUB_FONT, P('#000000', 0.55 * a, blur=6))
                    c.drawString(tk, x, y, SUB_FONT, P('#000000', a, w=11))
                    c.drawString(tk, x, y, SUB_FONT, P(col, a))
                    x += w + SPACE


def render_frame(fi, prev=None):
    T = fi / FPS
    a, b, f = shot_at(T)
    arr = np.zeros((H, W, 4), np.uint8)
    surf = skia.Surface(arr)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    c.save()
    o = f(c, T - a, T) or {}
    c.restore()
    del c, surf
    out = post(arr, o, fi)
    mb = o.get('mb', 0)
    if mb and prev is not None:
        out = cv2.addWeighted(out, 1 - mb, prev, mb, 0)
    raw = out.copy()
    s2 = skia.Surface(out)
    draw_subs(s2.getCanvas(), T)
    del s2
    return out, raw


def worker(i0, i1, outpath):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                          '-x264-params', 'keyint=60:min-keyint=30', outpath], stdin=subprocess.PIPE)
    prev = None
    t0 = time.time()
    for fi in range(max(0, i0 - 1), i1):
        out, raw = render_frame(fi, prev)
        prev = raw
        if fi >= i0:
            p.stdin.write(out.tobytes())
        if fi % 60 == 0:
            print(f'[{outpath}] frame {fi} ({(time.time() - t0) / max(1, fi - i0 + 1):.2f}s/f)', flush=True)
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'test':
        times = [float(x) for x in sys.argv[2].split(',')]
        tiles = []
        for T in times:
            fi = int(round(T * FPS))
            t0 = time.time()
            out, _ = render_frame(fi)
            dt = time.time() - t0
            cv2.imwrite(f'test/f_{T:06.2f}.jpg', cv2.cvtColor(out, cv2.COLOR_RGBA2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
            sm_ = cv2.resize(cv2.cvtColor(out, cv2.COLOR_RGBA2BGR), (270, 480), interpolation=cv2.INTER_AREA)
            cv2.putText(sm_, f'{T:.2f} {dt:.2f}s', (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            tiles.append(sm_)
        while len(tiles) % 6:
            tiles.append(np.zeros_like(tiles[0]))
        rows = [np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]
        cv2.imwrite(sys.argv[3], np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    elif mode == 'seg':
        worker(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
