import sys, time
sys.path.insert(0, '.')
import scenes_b as B
from PIL import Image

jobs = [(B.scene3, 2.5), (B.scene3, 6.0), (B.scene3, 10.5), (B.scene3, 13.0), (B.scene3, 15.0), (B.scene3, 16.5),
        (B.scene4, 1.8), (B.scene4, 5.0), (B.scene4, 8.8), (B.scene5, 1.0), (B.scene5, 4.0), (B.scene5, 6.0), (B.scene5, 7.8), (B.scene5, 9.2)]
tiles = []
for i, (f, t) in enumerate(jobs):
    t0 = time.time()
    im = f(t)
    tiles.append(im.resize((360, 640)))
    print(i, round(time.time() - t0, 2), flush=True)
cols = 7
sheet = Image.new('RGB', (360 * cols, 640 * 2))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 360, (i // cols) * 640))
sheet.resize((1800, 640)).save('/tmp/sheetB.png')
