import numpy as np,json
db=np.load('env_db.npy');a=json.load(open('align.json'))
T=lambda i:i*0.005
def show(i):
    s=a[i]['start'];k=int(s/0.005)
    seg=db[max(0,k-30):k+30:2]
    print(i,a[i]['word'],s,' '.join('%d'%v for v in seg))
for i in [0,5,10,14,17,25,27,28,30,32,35,37,41,43,47,52,58,60,64,66,68,74,76,79,81,82,86,91,95,97,99,102,110,111,112,113,116,121,125,129,131,134,136,139,142,144,146,153,155,159,162,169,172,177,178,182,186,193,196,200,204,206]: show(i)
