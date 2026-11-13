"""Phone close-up helpers: readable smartphone UI, rotated overlay, gripping fingers."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core import K, W, H
from anim2 import sstep

_F = {}


def mf(sz, bold=True):
    key = (sz, bold)
    if key not in _F:
        _F[key] = ImageFont.truetype('fonts/Montserrat-ExtraBold.ttf' if bold else 'fonts/Montserrat-Bold.ttf', sz)
    return _F[key]


def wrap(d, text, font, maxw):
    lines = []; cur = ''
    for w in text.split():
        tr = (cur + ' ' + w).strip()
        if d.textlength(tr, font=font) > maxw and cur: lines.append(cur); cur = w
        else: cur = tr
    lines.append(cur)
    return lines


def phone_screen(w, h, t, msgs, mode='chat', notif_t=None, typing=None, flash=0.0, clock='03:17'):
    """msgs: [(text, kind, t_appear)]; kind 'n' normal, 'r' ominous.  mode 'lock' shows lock screen + notification."""
    im = Image.new('RGB', (w, h), (13, 17, 29))
    d = ImageDraw.Draw(im)
    if mode == 'lock':
        for yy in range(h):
            c = int(14 + 22 * yy / h)
            d.line([(0, yy), (w, yy)], fill=(c, c + 4, c + 22))
        d.text((w / 2, 170), clock, fill=(235, 240, 250), font=mf(130), anchor='mm')
        d.text((w / 2, 262), 'Пятница, 13 ноября', fill=(170, 180, 205), font=mf(32, False), anchor='mm')
        if notif_t is not None and t >= notif_t:
            a = sstep((t - notif_t) / 0.18)
            y0 = 420 + int((1 - a) * 40)
            d.rounded_rectangle([28, y0, w - 28, y0 + 190], radius=34, fill=(40, 48, 70))
            d.ellipse([52, y0 + 28, 52 + 74, y0 + 28 + 74], fill=(74, 86, 120))
            d.text((89, y0 + 66), '?', fill=(220, 228, 245), font=mf(48), anchor='mm')
            d.text((150, y0 + 52), 'Неизвестный номер', fill=(236, 240, 250), font=mf(33), anchor='lm')
            d.text((w - 56, y0 + 52), 'сейчас', fill=(150, 160, 185), font=mf(25, False), anchor='rm')
            d.text((150, y0 + 116), 'Новое сообщение', fill=(190, 198, 218), font=mf(31, False), anchor='lm')
    else:
        d.rectangle([0, 0, w, 150], fill=(24, 31, 50))
        d.text((24, 40), clock, fill=(225, 230, 245), font=mf(30), anchor='lm')
        # signal + battery
        for i in range(4): d.rectangle([w - 190 + i * 14, 48 - i * 5, w - 190 + i * 14 + 8, 52], fill=(210, 216, 235))
        d.rounded_rectangle([w - 100, 30, w - 40, 56], radius=6, outline=(210, 216, 235), width=3)
        d.rectangle([w - 96, 34, w - 70, 52], fill=(210, 216, 235))
        d.polygon([(34, 104), (52, 90), (52, 118)], fill=(180, 190, 215))
        d.ellipse([78, 82, 78 + 56, 82 + 56], fill=(74, 86, 120))
        d.text((106, 110), '?', fill=(220, 228, 245), font=mf(36), anchor='mm')
        d.text((152, 98), 'Неизвестный номер', fill=(236, 240, 250), font=mf(30), anchor='lm')
        d.text((152, 130), 'был(а) только что', fill=(140, 152, 182), font=mf(22, False), anchor='lm')
        y = 200
        d.rounded_rectangle([w / 2 - 80, y, w / 2 + 80, y + 40], radius=20, fill=(30, 38, 60))
        d.text((w / 2, y + 20), 'Сегодня', fill=(150, 162, 190), font=mf(22, False), anchor='mm')
        y += 78
        for text, kind, ta in msgs:
            if t < ta: continue
            age = t - ta
            a = sstep(age / 0.16)
            sz = 46
            lines = wrap(d, text, mf(sz), w - 150)
            bh = len(lines) * (sz + 14) + 38
            bw = max(d.textlength(l, font=mf(sz)) for l in lines) + 56
            yy = y + int((1 - a) * 46)
            ov = Image.new('RGBA', (w, bh + 60), (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            fill = (46, 55, 80) if kind == 'n' else (92, 16, 24)
            od.rounded_rectangle([24, 0, 24 + bw, bh], radius=34, fill=fill + (int(255 * a),), outline=(150, 40, 48, int(255 * a)) if kind == 'r' else None, width=3)
            for i, l in enumerate(lines):
                od.text((24 + 28, 19 + i * (sz + 14)), l, fill=((238, 242, 252) if kind == 'n' else (255, 150, 150)) + (int(255 * a),), font=mf(sz))
            od.text((24 + bw - 4, bh + 10), '03:17', fill=(130, 142, 172, int(200 * a)), font=mf(20, False), anchor='ra')
            im.paste(ov, (0, yy), ov)
            y += bh + 56
        if typing is not None and typing[0] <= t < typing[1]:
            od = ImageDraw.Draw(im)
            od.rounded_rectangle([24, y, 24 + 150, y + 74], radius=36, fill=(46, 55, 80))
            for i in range(3):
                k = 0.5 + 0.5 * math.sin(t * 8 - i * 0.9)
                r = 8 + 4 * k
                od.ellipse([70 + i * 36 - r, y + 37 - r, 70 + i * 36 + r, y + 37 + r], fill=(150 + int(70 * k),) * 2 + (190 + int(50 * k),))
        # composer bar
        d.rounded_rectangle([20, h - 120, w - 20, h - 40], radius=40, fill=(26, 33, 54))
        d.text((56, h - 80), 'Сообщение', fill=(100, 112, 142), font=mf(30, False), anchor='lm')
    if flash > 0:
        im = Image.blend(im, Image.new('RGB', (w, h), (225, 235, 255)), min(1, flash) * 0.5)
    return im


def make_phone_layer(cx, cy, pw, ph, angle, scr, brightness=1.0, shadow=True):
    """returns RGBA (W,H) numpy float with the phone body + screen, rotated by angle (rad) about its centre; coordinates in design units."""
    sc = K
    bw, bh = int(pw * sc), int(ph * sc)
    pad = int(26 * sc)
    body = Image.new('RGBA', (bw + 2 * pad, bh + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    r = int(70 * sc)
    d.rounded_rectangle([pad, pad, pad + bw, pad + bh], radius=r, fill=(14, 14, 20, 255), outline=(60, 62, 78, 255), width=max(2, int(5 * sc)))
    bez = int(20 * sc)
    sw, sh = bw - 2 * bez, bh - 2 * bez
    s_im = scr.resize((sw, sh), Image.LANCZOS)
    s_im = Image.eval(s_im, lambda v: min(255, int(v * brightness)))
    mask = Image.new('L', (sw, sh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw, sh], radius=int(r * 0.7), fill=255)
    body.paste(s_im, (pad + bez, pad + bez), mask)
    # notch
    d.rounded_rectangle([pad + bw / 2 - 70 * sc, pad + bez + 8 * sc, pad + bw / 2 + 70 * sc, pad + bez + 34 * sc], radius=int(14 * sc), fill=(8, 8, 12, 255))
    # glass sheen
    sheen = Image.new('RGBA', body.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.polygon([(pad + bez, pad + bez), (pad + bez + sw * 0.55, pad + bez), (pad + bez, pad + bez + sh * 0.42)], fill=(255, 255, 255, 14))
    body = Image.alpha_composite(body, sheen)
    rot = body.rotate(-math.degrees(angle), resample=Image.BICUBIC, expand=True)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    layer.paste(rot, (int(cx * sc - rot.width / 2), int(cy * sc - rot.height / 2)), rot)
    return layer


def post_layer(layer, glow=None):
    arr = np.asarray(layer, np.float32)

    def fn(img):
        a = arr[..., 3:4] / 255.0
        return img * (1 - a) + arr[..., :3] * a
    return fn
