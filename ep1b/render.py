import sys, subprocess, numpy as np
from PIL import Image, ImageDraw
import shots1 as S1, shots2 as S2
from core import *
FPS = 30
TOTAL = int(108.4 * FPS)
SHOTS = [(0, S1.shot_A), (6.3, S1.shot_B), (17.6, S1.shot_C), (24.6, S1.shot_D), (44.9, S1.shot_E), (53.7, S1.shot_F),
         (58.7, S2.shot_G), (63.3, S2.shot_H), (66.3, S2.shot_I), (93.0, S2.shot_K), (95.0, S2.shot_L)]
CARD = 105.5


def pick(T):
    fn = SHOTS[0][1]
    for t0, f in SHOTS:
        if T >= t0: fn = f
    return fn


def card(T, shape):
    img = Image.new('RGB', (shape[1], shape[0]), (0, 0, 0))
    a = min(1, max(0, (T - 106.1) / 0.9))
    if a > 0:
        d = ImageDraw.Draw(img)
        f = S1.font(int(shape[1] * 0.065))
        txt = 'ПРОДОЛЖЕНИЕ СЛЕДУЕТ…'
        w = d.textlength(txt, font=f)
        d.text(((shape[1] - w) / 2, shape[0] * 0.48), txt, font=f, fill=(int(205 * a), int(30 * a), int(30 * a)))
    return np.asarray(img)


def main(a, b, out):
    p = None; last = np.zeros((1280, 720, 3), np.uint8)
    for i in range(a, b):
        T = i / FPS
        if T >= CARD:
            fr_ = card(T, last.shape)
        else:
            fr = Frame(seed=i)
            kw = pick(T)(fr, T)
            fr_ = finish(fr, **kw)
        last = fr_
        if p is None:
            h, w = fr_.shape[:2]
            p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
                                  '-vf', 'scale=1080:1920:flags=lanczos', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        p.stdin.write(np.ascontiguousarray(fr_, dtype=np.uint8).tobytes())
        if i % 150 == 0: print(i, flush=True)
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    a, b = int(sys.argv[1]), int(sys.argv[2])
    main(a, b, sys.argv[3])
