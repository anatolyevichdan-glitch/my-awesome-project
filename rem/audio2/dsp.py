"""Shared DSP helpers: all synthesis is procedural and seeded."""
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
DUR = 108.4
N = int(round(DUR * SR))
T = np.arange(N) / SR


def rng(seed):
    return np.random.default_rng(seed)


def curve(points, t=None, kind="linear"):
    """Piecewise-linear automation curve [(t, v), ...] sampled on the master grid."""
    t = T if t is None else t
    p = np.array(points, float)
    return np.interp(t, p[:, 0], p[:, 1])


def smooth_curve(points, tau=0.3):
    c = curve(points)
    return onepole(c, tau)


def onepole(x, tau):
    a = np.exp(-1.0 / (tau * SR))
    return signal.lfilter([1 - a], [1, -a], x)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)


def peaking(x, f0, gain_db, q):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / SR
    al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]
    a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x)


def lowshelf_free_noise(r, n, kind="pink"):
    w = r.standard_normal(n)
    if kind == "white":
        return w
    if kind == "pink":
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]
        return signal.lfilter(b, a, w) * 3.0
    if kind == "brown":
        x = np.cumsum(w)
        x -= onepole(x, 5.0)
        return x / (np.std(x) + 1e-9)


def ir_reverb(seconds, seed, decay_db=60, lp_hz=6000, predelay=0.0, stereo=True, hp_hz=120):
    """Synthetic exponential-decay noise impulse response (L,R decorrelated)."""
    r = rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    env = 10 ** (-decay_db * t / seconds / 20)
    outs = []
    for _ in range(2 if stereo else 1):
        h = r.standard_normal(n) * env
        h = lp(h, lp_hz, 1)
        h = hp(h, hp_hz, 1)
        # damp highs progressively (later tail darker)
        h = 0.55 * h + 0.45 * lp(h, max(900, lp_hz / 4), 1) * np.linspace(0.5, 1.5, n)
        pd = int(predelay * SR)
        h = np.concatenate([np.zeros(pd), h])
        h /= np.sqrt(np.sum(h ** 2)) + 1e-12
        outs.append(h)
    return np.stack(outs)


def convolve_stereo(x2, ir2):
    """x2: (2,n) ; returns (2,n) truncated."""
    n = x2.shape[1]
    return np.stack([signal.fftconvolve(x2[c], ir2[c])[:n] for c in range(2)])


def to_stereo(x):
    return np.stack([x, x]) if x.ndim == 1 else x


def place(buf, x, t0, gain=1.0, pan=0.0):
    """Add mono clip x into stereo buf (2,N) at time t0 with constant-power pan (-1..1)."""
    i0 = int(round(t0 * SR))
    if i0 >= buf.shape[1] or i0 + len(x) <= 0:
        return
    s = max(0, -i0)
    e = min(len(x), buf.shape[1] - i0)
    ang = (pan + 1) * np.pi / 4
    gl, gr = np.cos(ang), np.sin(ang)
    seg = x[s:e] * gain
    buf[0, i0 + s:i0 + e] += seg * gl * 1.4142
    buf[1, i0 + s:i0 + e] += seg * gr * 1.4142


def expenv(n, tau, attack=0.002):
    t = np.arange(n) / SR
    e = np.exp(-t / tau)
    a = int(attack * SR)
    if a > 1:
        e[:a] *= np.linspace(0, 1, a)
    return e


def bump(t0, t1, t2, t3):
    """Smooth trapezoid window on the master grid (rise t0->t1, fall t2->t3)."""
    up = np.clip((T - t0) / max(t1 - t0, 1e-6), 0, 1)
    dn = np.clip((t3 - T) / max(t3 - t2, 1e-6), 0, 1)
    w = np.minimum(up, dn)
    return 0.5 - 0.5 * np.cos(np.pi * w)


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def rms_db(x):
    return 10 * np.log10(np.mean(np.square(x)) + 1e-20)


def write_wav(path, x2, bits=24):
    """x2 (2,n) float -> WAV. 24-bit PCM via ffmpeg for universal compatibility."""
    import subprocess, os, tempfile
    tmp = tempfile.mktemp(suffix=".wav", dir="/tmp")
    wavfile.write(tmp, SR, x2.T.astype(np.float32))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "pcm_s24le", path], check=True)
    os.remove(tmp)


def read_audio(path):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).T.astype(np.float64)


def fit(x2):
    n = x2.shape[1]
    if n >= N:
        return x2[:, :N]
    return np.pad(x2, ((0, 0), (0, N - n)))
