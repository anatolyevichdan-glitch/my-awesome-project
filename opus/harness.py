"""Render a test clip: frame callback -> ffmpeg (h264) + matching slice of the episode mix + shifted subtitles."""
import os
import re
import subprocess
import sys
import numpy as np
import skia

sys.path.insert(0, '/tmp/hoplite/workspace/opus')
import world  # noqa: E402

FPS = 30
MIX = '/tmp/hoplite/workspace/rem/audio2/mix_master.wav'
ASS = '/tmp/hoplite/workspace/rem/subs2/subs.ass'
FONTS = '/tmp/hoplite/workspace/rem/subs2/fonts'


def _ts(s):
    h, m, x = s.split(':')
    return int(h) * 3600 + int(m) * 60 + float(x)


def _fmt(t):
    t = max(0.0, t)
    cs = int(round(t * 100))
    return f'{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}'


def shifted_ass(t0, t1, out):
    lines = []
    for ln in open(ASS, encoding='utf-8'):
        if ln.startswith('Dialogue:'):
            parts = ln.split(',', 9)
            a, b = _ts(parts[1]), _ts(parts[2])
            if b <= t0 or a >= t1:
                continue
            parts[1], parts[2] = _fmt(a - t0), _fmt(min(b, t1) - t0)
            ln = ','.join(parts)
        lines.append(ln)
    open(out, 'w', encoding='utf-8').write(''.join(lines))


def render(name, t0, t1, frame_fn, outdir='/tmp/hoplite/workspace/opus/out', stills=()):
    """frame_fn(cv, t_episode) draws onto a 1080x1920 canvas and returns post kwargs for world.grade."""
    os.makedirs(outdir, exist_ok=True)
    n = int(round((t1 - t0) * FPS))
    raw = os.path.join(outdir, f'{name}_nosubs.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                           '-s', f'{world.W}x{world.H}', '-r', str(FPS), '-i', '-',
                           '-ss', f'{t0:.3f}', '-t', f'{t1 - t0:.3f}', '-i', MIX,
                           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-shortest', raw], stdin=subprocess.PIPE)
    surf = skia.Surface(world.W, world.H)
    for i in range(n):
        t = t0 + i / FPS
        cv = surf.getCanvas()
        cv.clear(skia.ColorBLACK)
        cv.save()
        post = frame_fn(cv, t) or {}
        cv.restore()
        a = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
        img = world.grade(a[..., :3].astype(np.float32), t, **post)
        ff.stdin.write(img.tobytes())
        if i in stills:
            from PIL import Image
            Image.fromarray(img).save(os.path.join(outdir, f'{name}_f{i:03d}.png'))
    ff.stdin.close()
    ff.wait()
    sub = os.path.join(outdir, f'{name}.ass')
    shifted_ass(t0, t1, sub)
    final = os.path.join(outdir, f'{name}.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-vf', f"subtitles={sub}:fontsdir={FONTS}",
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'copy', final],
                   check=True)
    return final
