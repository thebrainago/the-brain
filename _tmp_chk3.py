import time, numpy as np
from nhan import du_lieu as DL, chi_phi as CP, pmg as P, pmg_engine as E
df = DL.nap("EURGBP","M5")
print("bar:", len(df), df.index[0], "->", df.index[-1])
t=time.time(); a=E.atr_khung(df,"H1",14); print("atr_khung", round(time.time()-t,2),"s")
cp=CP.tu_du_lieu("EURGBP", df)
print("spread bps", round(cp.spread_frac_chung*1e4,3), "do_tin", cp.do_tin,
      "phi mua/ban %/nam", round(cp.phi_nam_mua*100,2), round(cp.phi_nam_ban*100,2))
cf=P.CauHinh(ma="EURGBP",atr_tf="H1",h=1.0,tp_dist=1.0,size_mode="flat",max_legs=6,
             direction="AGAINST",time_stop_bar=500,hard_sl_atr=8.0,max_basket_dd=0.05)
t=time.time(); r=E.mo_phong(df,cf,cp,a); dt=time.time()-t
print(f"mo_phong {dt:.1f}s  ({len(df)/dt/1000:.0f}k bar/s)")
print(" trang thai", r["trang_thai"], "buoc/nen", round(r["phan_giai"]["buoc_tren_bien_do"],2))
print(" ro", r["so_ro"], "lenh", r["so_lenh"], "lai %", round(r["lai_tong"]*100,2),
      "dd %", round(r["dd_max"]*100,2), r["ly_do_dong"])
