s=open("mix.py").read()
s=s.replace("def process_voice(v):\n","def process_voice(v):\n    return v  # narration kept untouched (no EQ/compression); only gain + shared limiter are applied later\n",1)
open("mix.py","w").write(s)
