s=open("build.py").read()
s=s.replace('''    stepseq(11.9, 14.3, 2.6, gain=1.1)''','''    stepseq(11.9, 14.3, 2.6, gain=1.1)
    stepseq(24.0, 36.2, 1.8, gain=0.8)   # unhurried approach to the shop window (placeholder cadence)''')
open("build.py","w").write(s)
