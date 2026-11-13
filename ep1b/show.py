import json
w=json.load(open("words.json"))
print(len(w))
line=[];st=None
for a,b,x in w:
    if st is None: st=a
    line.append(x)
    if x[-1] in ".?!…:" or len(line)>9:
        print(f"[{st:6.2f}-{b:6.2f}] "+" ".join(line)); line=[];st=None
if line: print(f"[{st:6.2f}] "+" ".join(line))
