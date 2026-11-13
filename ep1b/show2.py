import json
w=json.load(open("words.json"))
for a,b,x in w:
    if a>=53 : print(f"{a:6.2f} {b:6.2f} {x}")
