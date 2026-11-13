import sys
sys.path.insert(0, '/tmp/hoplite/workspace/opus'); sys.path.insert(0, '/tmp/hoplite/workspace/rem')
import skia, numpy as np
from PIL import Image, ImageDraw
import episode as E, world
ts = [float(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else [(a + min(b, E.DUR)) / 2 for a, b, _ in E.SHOTS]
cols = 6; tw, th = 270, 480
rows = (len(ts) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * th))
for i, t in enumerate(ts):
    s = skia.Surface(1080, 1920); cv = s.getCanvas(); cv.clear(skia.ColorBLACK); cv.save()
    post = E.frame(cv, t) or {}
    cv.restore()
    a = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)[..., :3].astype(np.float32)
    im = Image.fromarray(world.grade(a, t, **post)).resize((tw, th))
    ImageDraw.Draw(im).text((6, 6), f'{t:.1f}', fill=(255, 255, 0))
    sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
sheet.save(sys.argv[1], quality=85)
