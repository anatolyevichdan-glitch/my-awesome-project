"""Audio V2: music -15 dB plus smooth ducking (-4 dB more) while the narrator speaks.
Narration untouched; foley/sfx/ambience taken from the previous fx fix."""
import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d, uniform_filter1d

D = '/tmp/hoplite/workspace/rem/audio2/'
nar, sr = sf.read(D + 'stem_narration.wav', always_2d=True)
mus, _ = sf.read(D + 'stem_music.wav', always_2d=True)
rest = sum(sf.read(D + f'stem_{k}_fxfixed.wav', always_2d=True)[0] for k in ('ambience', 'foley', 'sfx'))

STATIC_DB, DUCK_DB = -14.0, -4.0
FX_DUCK_DB = -4.0
env = maximum_filter1d(np.abs(nar).max(axis=1), size=int(0.25 * sr))      # bridge gaps between syllables
speaking = (env > 10 ** (-24 / 20)).astype(np.float64)
speaking = maximum_filter1d(speaking, size=int(0.3 * sr))                 # hold through short pauses
duck = uniform_filter1d(speaking, size=int(0.4 * sr))                     # ~200 ms fade in/out, no pumping
gain = 10 ** ((STATIC_DB + DUCK_DB * duck) / 20)
mus2 = mus * gain[:, None]
rest = rest * (10 ** (FX_DUCK_DB * duck / 20))[:, None]
sf.write(D + "stem_fxbus_v2.wav", rest.astype(np.float32), sr, subtype="FLOAT")
mix = nar + mus2 + rest
print('mix peak dBFS', round(20 * np.log10(np.abs(mix).max()), 2), '| ducked share', round(100 * (duck > 0.5).mean(), 1), '%')
sf.write(D + 'stem_music_v2.wav', mus2.astype(np.float32), sr, subtype='FLOAT')
sf.write(D + 'mix_master_v2.wav', mix.astype(np.float32), sr, subtype='FLOAT')
