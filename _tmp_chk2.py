import numpy as np, pandas as pd
from nhan import pmg as P
from nhan import pmg_engine as E

def khung(gia, tu="2020-01-01", freq="h"):
    gia=np.asarray(gia,float); idx=pd.date_range(tu,periods=len(gia),freq=freq)
    o=gia; c=np.r_[gia[1:],gia[-1]]
    return pd.DataFrame({"open":o,"high":np.maximum(o,c)*1.0005,
                         "low":np.minimum(o,c)*0.9995,"close":c},index=idx)

rng=np.random.default_rng(7)
gia=100*np.exp(np.cumsum(rng.normal(0,0.001,60000)))
df=khung(gia)
print("RANDOM WALK, KHONG CHI PHI -> dap an dung la ~0")
print(f"{'h':>5} {'trang thai':>13} {'buoc/nen':>9} {'ro':>6} {'lai %':>9} {'dd %':>7}")
for h in (0.3, 0.5, 1.0, 2.0, 3.0):
    cf=P.CauHinh(ma="THU",direction="AGAINST",h=h,tp_dist=min(h,2.0),size_mode="flat",
                 max_legs=6,time_stop_bar=500,hard_sl_atr=8.0,max_basket_dd=0.08)
    r=E.mo_phong(df,cf)
    print(f"{h:5.1f} {r['trang_thai']:>13} {r['phan_giai']['buoc_tren_bien_do']:9.2f} "
          f"{r['so_ro']:6d} {r['lai_tong']*100:9.2f} {r['dd_max']*100:7.2f}")
