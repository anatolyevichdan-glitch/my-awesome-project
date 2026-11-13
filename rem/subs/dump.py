import json;a=json.load(open('align.json'))
print(len(a))
print(' '.join('%d:%s@%.2f-%.2f%s'%(i,w['word'],w['start'],w['end'],'*' if w['score']<-1.5 else '') for i,w in enumerate(a)))
