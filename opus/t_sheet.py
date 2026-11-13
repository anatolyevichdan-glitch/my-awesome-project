import sys, math
sys.path.insert(0, '/tmp/hoplite/workspace/opus')
sys.path.insert(0, '/tmp/hoplite/workspace/rem')
import numpy as np, skia
from PIL import Image
import rig as R
import toon
from rig import V

EX = dict(R.EXPR)
EX['confusion'] = R.E(brow=0.25, browL=-0.15, tilt=0.3, tiltL=-0.25, eyew=1.0, pupil=0.95, gx=0.3, gy=0.2, mw=0.7, smile=-0.1, asym=0.5, mopen=0.0)
EX['mild_fear'] = R.E(brow=0.35, tilt=0.6, eyew=1.08, pupil=0.75, mw=0.8, smile=-0.3, mopen=0.1, sweat=0.5)
EX['suspicious'] = R.E(brow=-0.15, tilt=-0.4, browL=0.25, tiltL=0.2, lid=0.32, lidlow=0.2, eyew=0.96, pupil=0.95, mw=0.75, smile=-0.08, asym=0.3, gx=0.55)


def save(surf, path):
    a = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)[..., :3]
    Image.fromarray(a).save(path)


def bg(cv, w, h):
    cv.drawRect(skia.Rect(0, 0, w, h), toon.P(shader=toon.lin((0, 0), (0, h), (70, 74, 96), (40, 42, 58))))


if __name__ == '__main__':
    W_, H_ = 2400, 1200
    surf = skia.Surface(W_, H_); cv = surf.getCanvas(); bg(cv, W_, H_)
    views = [('front', 0.0), ('3/4', 0.75), ('side', 1.5708), ('back 3/4', 2.4), ('back', 3.1416)]
    font = skia.Font(skia.Typeface('DejaVu Sans'), 34)
    for i, (nm, y) in enumerate(views):
        p = R.Pose(); p.yaw = y; p.e = EX['neutral']
        toon.draw(cv, p, 260 + i * 470, 1100, 0.85)
        cv.drawString(nm, 220 + i * 470, 60, font, toon.P((230, 230, 240)))
    save(surf, '/tmp/verify/opus_turn.png')
    names = ['neutral', 'suspicious', 'mild_fear', 'shock', 'panic', 'confusion', 'exhausted', 'terror']
    surf = skia.Surface(2400, 760); cv = surf.getCanvas(); bg(cv, 2400, 760)
    for i, n in enumerate(names):
        p = R.Pose(); p.yaw = 0.25 if i % 2 else -0.2; p.e = EX[n]
        toon.draw(cv, p, 150 + i * 300, 1900, 1.55, ground_shadow=0)
        cv.drawString(n, 90 + i * 300, 740, font, toon.P((230, 230, 240)))
    save(surf, '/tmp/verify/opus_expr.png')
