"""Frame renderer: python render.py [scene ...]  -> frames/NNNN.jpg (resumable, 2 workers)."""
import os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FPS = 30
TIMELINE = [  # name, function path, duration (s)
    ('s0_opening', 'scenes_a.scene0', 6), ('s1_follower', 'scenes_a.scene1', 11), ('s2_warning', 'scenes_a.scene2', 9),
    ('s3_reflection', 'scenes_b.scene3', 17), ('s4_second_warning', 'scenes_b.scene4', 10), ('s5_lights_out', 'scenes_b.scene5', 10),
    ('s6_escape', 'scenes_c.scene6', 16), ('s7_double', 'scenes_c.scene7', 9), ('s8_double_warns', 'scenes_c.scene8', 8),
    ('s9_reveal', 'scenes_c.scene9', 12)]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frames')


def jobs():
    n = 0; out = []
    for i, (name, fn, dur) in enumerate(TIMELINE):
        for f in range(dur * FPS):
            out.append((n, i, f / FPS)); n += 1
    return out


def work(job):
    n, i, t = job
    path = os.path.join(OUT, '%05d.jpg' % n)
    if os.path.exists(path): return n
    import importlib
    mod, fn = TIMELINE[i][1].split('.')
    im = getattr(importlib.import_module(mod), fn)(t)
    im.save(path + '.tmp.jpg', quality=94, subsampling=0); os.rename(path + '.tmp.jpg', path)
    return n


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    js = jobs()
    with Pool(2) as p:
        for k, n in enumerate(p.imap(work, js, chunksize=4)):
            if k % 100 == 0: print(k, len(js), flush=True)
    print('DONE', flush=True)
