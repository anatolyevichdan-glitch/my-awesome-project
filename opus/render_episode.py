"""Render the full episode in parallel segments -> NO_SUBS and FINAL (burned subs) with the master mix."""
import os, subprocess, sys
sys.path.insert(0, '/tmp/hoplite/workspace/opus'); sys.path.insert(0, '/tmp/hoplite/workspace/rem')
OUT = '/tmp/hoplite/workspace/opus/final'
FPS = 30
MIX = '/tmp/hoplite/workspace/rem/audio2/mix_master.wav'
ASS = '/tmp/hoplite/workspace/rem/subs2/subs.ass'
FONTS = '/tmp/hoplite/workspace/rem/subs2/fonts'


def worker(i0, i1, path):
    import numpy as np, skia
    import episode as E, world
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    surf = skia.Surface(1080, 1920)
    for i in range(i0, i1):
        t = i / FPS
        cv = surf.getCanvas(); cv.clear(skia.ColorBLACK); cv.save()
        post = E.frame(cv, t) or {}
        cv.restore()
        a = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)[..., :3]
        ff.stdin.write(world.grade(a.astype(np.float32), t, **post).tobytes())
        if i % 150 == 0:
            print(path, i, flush=True)
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    if sys.argv[1] == 'seg':
        worker(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]); sys.exit()
    os.makedirs(OUT, exist_ok=True)
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', MIX]).decode())
    N = int(round(dur * FPS))
    nseg = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    bounds = [round(N * k / nseg) for k in range(nseg + 1)]
    jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    segs = [f'{OUT}/seg{k:02d}.mp4' for k in range(nseg)]
    running = []
    for k in range(nseg):
        if os.path.exists(segs[k] + '.ok'):
            continue
        while len(running) >= jobs:
            running[0][0].wait(); open(running[0][1] + '.ok', 'w').close(); running.pop(0)
        running.append((subprocess.Popen([sys.executable, __file__, 'seg', str(bounds[k]), str(bounds[k + 1]), segs[k]]), segs[k]))
    for pr, s in running:
        pr.wait(); open(s + '.ok', 'w').close()
    with open(f'{OUT}/list.txt', 'w') as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    ns = f'{OUT}/DONT_LOOK_BACK_EP1_OPUS_NO_SUBS.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt', '-i', MIX,
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', ns], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', ns, '-vf', f'subtitles={ASS}:fontsdir={FONTS}', '-c:v', 'libx264',
                    '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart',
                    f'{OUT}/DONT_LOOK_BACK_EP1_OPUS_FINAL.mp4'], check=True)
    print('DONE')
