import numpy as np, pandas as pd
from nhan import pmg as P, pmg_engine as E
def khung(gia, rau=0.0):
    gia=np.asarray(gia,float); idx=pd.date_range("2020-01-01",periods=len(gia),freq="h")
    o=gia; c=np.r_[gia[1:],gia[-1]]
    return pd.DataFrame({"open":o,"high":np.maximum(o,c)*(1+rau),
                         "low":np.minimum(o,c)*(1-rau),"close":c},index=idx)
rng=np.random.default_rng(2)
gia=np.r_[100+np.cumsum(rng.normal(0,0.05,120)), np.linspace(100,80,900)]
df=khung(gia)
cf=P.CauHinh(ma="THU",direction="AGAINST",h=0.5,tp_dist=1.0,size_mode="flat",max_legs=6,
             hard_sl_atr=0,max_basket_dd=0,time_stop_bar=0)
r=E.mo_phong(df,cf)
print("A ro treo:",r["ro_treo_cuoi_mau"],"| lai",round(r["lai_tong"],4),
      "| ly do",r["ly_do_dong"],"| tt",r["trang_thai"], r["phan_giai"]["buoc_tren_bien_do"])
print("  ro cuoi cung:", r["so_ro"])

rng=np.random.default_rng(4)
truoc=100+np.cumsum(rng.normal(-0.02,0.05,200))
gia=np.r_[truoc, truoc[-1]*0.88*np.ones(40)]
df=khung(gia)
cf=P.CauHinh(ma="THU",direction="AGAINST",h=0.5,tp_dist=1.0,size_mode="flat",max_legs=6,
             hard_sl_atr=2.0,max_basket_dd=0,time_stop_bar=0)
r=E.mo_phong(df,cf)
print("B khe:",r["khe_truot_so_lan"],r["khe_truot_atr_tb"],"| ly do",r["ly_do_dong"],
      "| tt",r["trang_thai"], round(r["phan_giai"]["buoc_tren_bien_do"],2))
