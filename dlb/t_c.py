import sys, time
sys.path.insert(0, '.')
import scenes_b as B, scenes_c as C
from PIL import Image
jobs = [(B.scene3, 7.0), (B.scene3, 16.5), (C.scene6, 3.0), (C.scene6, 7.0), (C.scene6, 9.5), (C.scene6, 14.0),
        (C.scene7, 0.9), (C.scene7, 2.0), (C.scene7, 7.0), (C.scene8, 1.5), (C.scene8, 4.5), (C.scene8, 7.0),
        (C.scene9, 0.5), (C.scene9, 3.5), (C.scene9, 6.0), (C.scene9, 8.2), (C.scene9, 9.8)]
tiles = []
for i, (f, t) in enumerate(jobs):
    t0 = time.time()
    try:
        im = f(t)
    except Exception as ex:
        import traceback; traceback.print_exc(); im = Image.new('RGB', (1080, 1920), (120, 0, 0))
    tiles.append(im.resize((300, 533)))
    print(i, round(time.time() - t0, 2), flush=True)
cols = 9
sheet = Image.new('RGB', (300 * cols, 533 * 2))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 300, (i // cols) * 533))
sheet.resize((1800, 640)).save('/tmp/sheetC.png')
