import sys, os, time, numpy as np
from PIL import Image
import importlib
import shots_a
try:
    import shots_b
except ImportError:
    shots_b = None
from lib import *

SH = shots_a.SH
FPS = 30
DUR = 108.355875
NF = int(round(DUR * FPS))


def shot_at(T):
    for i in sorted(SH):
        t0, t1, fn, nm = SH[i]
        if t0 <= T < t1:
            return i, t0, t1, fn
    return None


def render_frame(n):
    T = n / FPS
    s = shot_at(T)
    if s is None:
        return np.zeros((H, W, 3), np.uint8)
    i, t0, t1, fn = s
    arr, o = fn(T, T - t0, t1 - t0)
    return post(arr, o, T)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'prev':
        a, b = int(sys.argv[2]), int(sys.argv[3])
        out = sys.argv[4]
        ims = []
        for i in sorted(SH):
            if not (a <= i <= b):
                continue
            t0, t1, fn, nm = SH[i]
            T = t0 + (t1 - t0) * 0.55
            t = time.time()
            arr = render_frame(int(T * FPS))
            ims.append(Image.fromarray(arr).resize((270, 480)))
            print(i, nm, round(T, 2), round(time.time() - t, 2), flush=True)
        cols = 6
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * 270, rows * 480))
        for k, im in enumerate(ims):
            sheet.paste(im, ((k % cols) * 270, (k // cols) * 480))
        sheet.save(out)
    elif mode == 'frame':
        n = int(sys.argv[2])
        Image.fromarray(render_frame(n)).save(sys.argv[3])
    elif mode == 'range':
        a, b, d = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        os.makedirs(d, exist_ok=True)
        for n in range(a, b):
            fp = '%s/%05d.png' % (d, n)
            if os.path.exists(fp):
                continue
            Image.fromarray(render_frame(n)).save(fp, compress_level=1)
