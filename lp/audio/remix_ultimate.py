import numpy as np, soundfile as sf
d='/tmp/hoplite/workspace/lp/audio/'
st={k:sf.read(d+f'stem_{k}.wav',dtype='float64')[0] for k in ('narration','music','ambience','foley','sfx')}
m,sr=sf.read(d+'mix_master.wav',dtype='float64')
print('sum-vs-master err',np.abs(sum(st.values())-m).max())
G={'ambience':0.25,'foley':0.25,'sfx':0.20}   # ULTIMATE: effects 20-25% of the original amplitude
out=st['narration']+st['music']+sum(st[k]*g for k,g in G.items())
print('peak',np.abs(out).max(),'old peak',np.abs(m).max())
for k in ('ambience','foley','sfx'):
    print(k,'peak before',20*np.log10(np.abs(st[k]).max()+1e-12),'after',20*np.log10(np.abs(st[k]*G[k]).max()+1e-12))
sf.write(d+'mix_master_ultimate.wav',out,sr,subtype='PCM_24')
