import json, re, torch, torchaudio, numpy as np
import torchaudio.functional as F

MAP = dict(zip("абвгдежзийклмнопрстуфхцчшщъыьэюяё",
               ["a", "b", "v", "g", "d", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u", "f", "h", "ts", "ch", "sh", "sh", "", "y", "", "e", "yu", "ya", "o"]))
TEXT = open('script_ru.txt', encoding='utf-8').read().strip()
words = [w for w in re.split(r'\s+', TEXT) if w]
clean = [re.sub(r'[^а-яё]', '', w.lower()) for w in words]
rom = [''.join(MAP[c] for c in w) for w in clean]

bundle = torchaudio.pipelines.MMS_FA
model = bundle.get_model(with_star=False)
dic = bundle.get_dict(star=None)
wav, sr = torchaudio.load('narr.mp3')
wav = wav.mean(0, keepdim=True)
wav = torchaudio.functional.resample(wav, sr, bundle.sample_rate)
with torch.inference_mode():
    em, _ = model(wav)
toks = []
for r in rom:
    toks += [dic[c] for c in r if c in dic]
ali, sc = F.forced_align(em, torch.tensor([toks], dtype=torch.int32), blank=0)
spans = F.merge_tokens(ali[0], sc[0])
assert len(spans) == len(toks), (len(spans), len(toks))
ratio = wav.shape[1] / em.shape[1] / bundle.sample_rate
out = []
i = 0
for w, r in zip(words, rom):
    n = len([c for c in r if c in dic])
    sp = spans[i:i + n]; i += n
    out.append(dict(word=w, start=round(sp[0].start * ratio, 3), end=round(sp[-1].end * ratio, 3), score=round(float(np.mean([s.score for s in sp])), 3)))
json.dump(out, open('align.json', 'w'), ensure_ascii=False, indent=0)
for o in out: print(f"{o['start']:7.2f} {o['end']:7.2f} {o['score']:.2f} {o['word']}")
