import json, sys, torch
from ctc_forced_aligner import (load_audio, load_alignment_model, generate_emissions, preprocess_text,
                                get_alignments, get_spans, postprocess_results)

TEXT = open('script_ru.txt', encoding='utf-8').read().strip().replace('\n', ' ')
dev = 'cpu'
model, tok = load_alignment_model(dev, dtype=torch.float32)
audio = load_audio('narr.mp3', model.dtype, model.device)
em, stride = generate_emissions(model, audio, batch_size=2)
tokens, text_starred = preprocess_text(TEXT, romanize=True, language='rus')
seg, scores, blank = get_alignments(em, tokens, tok)
spans = get_spans(tokens, seg, blank)
res = postprocess_results(text_starred, spans, stride, scores)
json.dump(res, open('align.json', 'w'), ensure_ascii=False, indent=0)
for r in res: print(f"{r['start']:7.2f} {r['end']:7.2f} {r['text']}")
