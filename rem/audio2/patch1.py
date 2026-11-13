import re
s = open("build.py").read()
s = s.replace("(104, 0.62), (105.4, 0.40), (106.7, 0.10), (108.4, 0.03)]", "(104, 0.62), (105.5, 0.50), (107, 0.25), (108.3, 0.04), (108.4, 0.04)]")
s = s.replace("np.array([(0, 0), (4, 1), (100, 1), (108.4, 1)]).T", "np.array([(0, 0), (1.5, 1), (100, 1), (108.4, 1)]).T")
s = s.replace("lvl = curve([(0, 0), (2.5, 0.5), (6, 0.8), (105.4, 0.9), (106.7, 0.35), (108.4, 0.12)])",
 "lvl = curve([(0, 0), (1.5, 0.5), (6, 0.8), (105.5, 0.9), (108.3, 0.0), (108.4, 0.0)])")
# ambience ending: gentle fade instead of hard cut
s = s.replace("""    gate = np.where(T < 105.4, 1.0, 0.0)
    gate = onepole(gate, 0.012)
    amb = amb * gate""", """    gate = curve([(0, 1), (105.5, 1), (108.3, 0.02), (108.4, 0.0)])
    amb = amb * gate""")
s = s.replace("rt_g = curve([(105.4, 0), (105.5, 0), (106.0, 1), (107.5, .6), (108.4, 0)])", "rt_g = curve([(105.4, 0), (106.0, .5), (107.5, .3), (108.4, 0)])")
# foley: dB gain in json, splash kind
s = s.replace('''        g = float(e.get("gain", 1.0))
        foot''', '''        g = float(e["gain"]) if e.get("lin") else 10 ** (float(e.get("gain", 0.0)) / 20)
        foot''')
s = s.replace('"gain": gain, "who": who})', '"gain": gain, "who": who, "lin": True})')
s = re.sub(r'(ev\.append\(\{"t": [^\n]*"gain": [0-9.]+)(\}\))', r'\1, "lin": True\2', s)
s = s.replace('''        elif kind == "impact":''', '''        elif kind == "splash":
            place(buf, clip_splash(rr), t0, g * 0.5, pan)
        elif kind == "impact":''')
s = s.replace("def clip_rustle(", '''def clip_splash(rr):
    L = int(0.5 * SR)
    t = np.arange(L) / SR
    w = bp(rr.standard_normal(L), 900, 7000, 2) * np.exp(-t / 0.07) * np.clip(t / .004, 0, 1)
    dr = sum(np.sin(2 * np.pi * rr.uniform(1500, 3500) * t) * np.exp(-(t - rr.uniform(.04, .25)).clip(0) / .02) * (t > .04) * .08 for _ in range(4))
    return _norm(w + dr * 0.5 + lp(rr.standard_normal(L), 300, 2) * np.exp(-t / .05) * 0.6)

def clip_rustle(''', 1)
# default foley: add splashes during escape, drop collision impact (sfx covers it), softer creature
s = s.replace('''    ev.append({"t": 64.9, "kind": "impact", "foot": 0, "gain": 1.0, "lin": True})
''', '''    for ts in [59.7, 60.5, 61.2, 62.4, 63.6, 64.4]:
        ev.append({"t": ts, "kind": "splash", "foot": 0, "gain": 0.6, "lin": True})
''')
s = s.replace('gain=0.55, offset=0.28', 'gain=0.4, offset=0.28').replace('gain=0.6, offset=0.28', 'gain=0.45, offset=0.28')
open("build.py", "w").write(s)
