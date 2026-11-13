"""Audio-only fix: attenuate + peak-limit the foley and SFX stems, clamp isolated ambience spikes.
Narration and music stems are used sample-for-sample unchanged."""
import sys
import numpy as np
import soundfile as sf
from scipy.ndimage import minimum_filter1d

D = '/tmp/hoplite/workspace/rem/audio2/'
st = {k: sf.read(D + f'stem_{k}.wav', always_2d=True) for k in ('narration', 'music', 'ambience', 'foley', 'sfx')}
sr = st['narration'][1]
x = {k: v[0].astype(np.float64) for k, v in st.items()}


def db(v):
    return 20 * np.log10(max(v, 1e-12))


def win_peak(a, n):
    m = np.abs(a).max(axis=1)
    m = np.pad(m, (0, (-len(m)) % n))
    return m.reshape(-1, n).max(axis=1)


def report(tag):
    n = sr // 20
    for k in ('narration', 'music', 'ambience', 'foley', 'sfx'):
        a = x[k]
        print(f'{tag} {k:9s} peak {db(np.abs(a).max()):6.1f} dBFS  rms {db(np.sqrt((a ** 2).mean())):6.1f}  '
              f'p99(50ms peaks) {db(np.percentile(win_peak(a, n), 99)):6.1f}')


def limiter_gain(a, ceil, attack=0.005, release=0.12):
    """look-ahead peak limiter gain curve: never lets |a| exceed ceil, smooth release"""
    m = np.abs(a).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(m, 1e-12))
    la = int(attack * sr)
    g = minimum_filter1d(need, size=2 * la + 1)
    # smooth the attack edge so the gain ramps down over the look-ahead instead of stepping
    g = np.minimum(g, np.convolve(g, np.ones(la) / la, 'same'))
    rel = np.exp(-1 / (release * sr))
    out = np.empty_like(g)
    cur = 1.0
    for i, v in enumerate(g):
        cur = v if v < cur else v + (cur - v) * rel
        out[i] = cur
    return out


if __name__ == '__main__':
    report('before')
    if len(sys.argv) < 4:
        sys.exit()
    gain_db, ceil_rel, amb_ceil_db = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    nar_ref = np.percentile(win_peak(x['narration'], sr // 20), 90)   # typical narration word peak
    ceil = nar_ref * 10 ** (ceil_rel / 20)
    print(f'narration word peak {db(nar_ref):.1f} dBFS -> effects ceiling {db(ceil):.1f} dBFS')
    gl = 10 ** (gain_db / 20)
    gfx = limiter_gain((x['foley'] + x['sfx']) * gl, ceil)
    for s in ('foley', 'sfx'):
        x[s] = x[s] * gl * gfx[:, None]
    gamb = limiter_gain(x['ambience'], 10 ** (amb_ceil_db / 20), release=0.25)
    x['ambience'] = x['ambience'] * gamb[:, None]
    report('after ')
    mix = x['narration'] + x['music'] + x['ambience'] + x['foley'] + x['sfx']
    print('mix peak', round(db(np.abs(mix).max()), 2), 'dBFS | fx limiter max', round(db(gfx.min()), 1),
          'dB | ambience clamp max', round(db(gamb.min()), 1), 'dB, active', round(100 * (gamb < 0.99).mean(), 2), '% of samples')
    for k in ('foley', 'sfx', 'ambience'):
        sf.write(D + f'stem_{k}_fxfixed.wav', x[k].astype(np.float32), sr, subtype='FLOAT')
    sf.write(D + 'mix_master_fxfixed.wav', mix.astype(np.float32), sr, subtype='FLOAT')
