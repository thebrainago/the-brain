# -*- coding: utf-8 -*-
"""Thu nhanh engine PMG tren chuoi dung san co dap an."""
import numpy as np
import pandas as pd
from nhan import pmg as P
from nhan import pmg_engine as E


def khung(gia, tu="2020-01-01", freq="h"):
    gia = np.asarray(gia, float)
    idx = pd.date_range(tu, periods=len(gia), freq=freq)
    o = gia
    c = np.r_[gia[1:], gia[-1]]
    hi = np.maximum(o, c) * 1.0005
    lo = np.minimum(o, c) * 0.9995
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": c}, index=idx)


print("=== D_BE doi chieu dac ta ===")
print("geometric r=2 n=30 :", round(P.d_be("geometric", 30, 1.0, 2.0), 4), " (dac ta: -> 1)")
print("linear n=8         :", round(P.d_be("linear", 8, 1.0), 4), " (dac ta: 2.333)")
print("flat n=9           :", round(P.d_be("flat", 9, 1.0), 4), " (dac ta: (n-1)/2 = 4)")
print("inverse n=4/8/16   :", [round(P.d_be("inverse", n, 1.0), 3) for n in (4, 8, 16)])

print("\n=== G1 ===")
cf = P.CauHinh(ma="THU", h=0.5, tp_dist=0.5, max_legs=8, size_mode="flat")
r = P.kiem_g1(cf, spread_frac=1e-4, atr_frac=0.01)
print(r["ma"]); print(" kha_thi:", r["kha_thi"], "d_be", round(r["d_be_atr"], 3),
                      "chi phi ATR", round(r["chi_phi_atr"], 4))
xau = P.CauHinh(ma="THU", max_basket_dd=0, time_stop_bar=0, hard_sl_atr=0)
print(" khong co stop ->", P.kiem_g1(xau)["ly_do"])
vn = P.CauHinh(ma="THU", tp_mode="anchor_return", direction="WITH")
print(" anchor_return+WITH ->", P.kiem_g1(vn)["ly_do"])

print("\n=== chuoi TANG THANG: WITH phai lai, AGAINST phai lo ===")
gia = 100 * np.exp(np.linspace(0, 0.5, 3000))
df = khung(gia)
for d in ("WITH", "AGAINST"):
    cf = P.CauHinh(ma="THU", direction=d, h=0.5, tp_dist=1.0, max_legs=8,
                   time_stop_bar=200, hard_sl_atr=6.0, max_basket_dd=0.05)
    r = E.mo_phong(df, cf)
    print(f"  {d:8s} so_ro {r['so_ro']:4d}  lenh {r['so_lenh']:5d} "
          f"lai {r['lai_tong']*100:8.2f}%  dd {r['dd_max']*100:5.2f}%  {r['ly_do_dong']}")

print("\n=== chuoi DAO QUANH: AGAINST phai lai, WITH phai lo ===")
t = np.arange(4000)
gia = 100 * (1 + 0.02 * np.sin(t / 40.0))
df = khung(gia)
for d in ("WITH", "AGAINST"):
    cf = P.CauHinh(ma="THU", direction=d, h=0.3, tp_dist=0.5, max_legs=8,
                   time_stop_bar=300, hard_sl_atr=8.0, max_basket_dd=0.08)
    r = E.mo_phong(df, cf)
    print(f"  {d:8s} so_ro {r['so_ro']:4d}  lenh {r['so_lenh']:5d} "
          f"lai {r['lai_tong']*100:8.2f}%  dd {r['dd_max']*100:5.2f}%  {r['ly_do_dong']}")

print("\n=== random walk: ky vong = -chi phi (dac ta muc 0) ===")
rng = np.random.default_rng(7)
gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, 20000)))
df = khung(gia)
for sm in ("flat", "linear", "geometric", "inverse"):
    cf = P.CauHinh(ma="THU", direction="AGAINST", h=0.5, tp_dist=0.5, size_mode=sm,
                   max_legs=6, time_stop_bar=500, hard_sl_atr=8.0, max_basket_dd=0.08)
    r = E.mo_phong(df, cf)
    print(f"  {sm:10s} ro {r['so_ro']:4d} lai {r['lai_tong']*100:7.2f}% "
          f"dd {r['dd_max']*100:5.2f}% don bay dinh {r['dinh_don_bay']:.1f} "
          f"treo {bool(r['ro_treo_cuoi_mau'])}")

print("\n=== bat bien voi tie-break ===")
cf = P.CauHinh(ma="THU", direction="AGAINST", h=0.5, tp_dist=0.5, max_legs=6,
               time_stop_bar=500, hard_sl_atr=8.0, max_basket_dd=0.08)
bb = E.do_bat_bien(df, cf)
print(" dung_duoc", bb["dung_duoc"], "bi quan", round(bb["lai_bi_quan"], 5),
      "lac quan", round(bb["lai_lac_quan"], 5))
