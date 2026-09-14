import numpy as np
from nhan import pmg_g0 as G0
rng=np.random.default_rng(23); n=20000
e=rng.normal(0,0.001,n); r=np.zeros(n)
for i in range(1,n): r[i]=0.6*r[i-1]+e[i]
gia=100*np.exp(np.cumsum(r))
atr_tv=float(np.std(np.diff(gia)))*5
L=G0._cua_so_cho_h(gia,1.0*atr_tv); print("L =",L,"so cua so",len(gia)//L)
lr=np.diff(np.log(gia))
print("ac1 that :",round(float(np.corrcoef(lr[:-1],lr[1:])[0,1]),4))
mau=G0._null_block(lr,5,4242,khoi=max(20,L))
print("ac1 null :",[round(float(np.corrcoef(m[:-1],m[1:])[0,1]),4) for m in mau])
print("ER that  :",round(float(np.median(G0._er_cac_cua_so(gia,L))),4))
for m in mau[:3]:
    gn=100*np.exp(np.cumsum(m))
    print("  ER null:",round(float(np.median(G0._er_cac_cua_so(gn,L))),4))
