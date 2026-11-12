import sys, time
sys.path.insert(0, '.')
import scenes_a as A

jobs = [(A.scene0, 0.5), (A.scene0, 4.5), (A.scene1, 2.0), (A.scene1, 6.0), (A.scene1, 9.5), (A.scene2, 2.5), (A.scene2, 5.0), (A.scene2, 8.0)]
for i, (f, t) in enumerate(jobs):
    t0 = time.time()
    im = f(t)
    im.resize((540, 960)).save(f'/tmp/s_{i}.png')
    print(i, round(time.time() - t0, 2))
