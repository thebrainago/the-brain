# -*- coding: utf-8 -*-
"""
soi_nguon_cong_cu.py - Loc kho nguon GitHub theo LO HONG THAT cua du an
=====================================================================================
Khong hoi "repo nay co nhieu sao khong" ma hoi "no vá duoc lo nao cua du an nay".

BON LO HONG DA TU VAP PHAI (co ngay thang, khong phai phong doan):

  L1 - THONG KE TU CHE. Ngay 28/07 toi tu viet hieu chinh Newey-West bang cach nhan
       phuong sai voi 20 ("t da hieu chinh tho cho chong lan 20 ngay"). Do la uoc luong
       tam, va moi ket luan ve co che 07 (do la) dua tren no. Can `statsmodels`
       (HAC/Newey-West that) va `arch` (bootstrap khoi, kiem SPA/Reality Check cua
       Hansen - dung chuan cho "nhieu chien luoc cung luc").

  L2 - RAM. Ngay 28/07: 16 tien trinh scan + 1 lan chay MT5 tester -> can 31 GB, worker
       bi giet, scan treo 40 phut. Can quan ly bo nho tot hon (joblib memmap / polars /
       duckdb thay pandas cho phan gop).

  L3 - TOC DO QUET. magnetic_master phai rut tu 169 moc xuong 53 vi cham. Neu vong lap
       backtest nhanh hon 10-50x thi khong phai rut.

  L4 - KIEM DINH CHONG LAN THOI GIAN. Walk-forward hien tai chia theo thap ky bang tay.
       Purged/embargoed CV (Lopez de Prado) la chuan de tranh ro ri qua bien.

Chay sau `brain_sources.py github`. Doc reports/BRAIN_nguon.parquet.
"""
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
NGUON = HERE / "reports" / "BRAIN_nguon.parquet"
if not NGUON.exists():
    sys.exit("chua co reports/BRAIN_nguon.parquet - chay brain_sources.py github truoc")

LO_HONG = {
    "L1 thong ke that (thay Newey-West tu che)":
        ["statsmodels", "econometric", "newey", "hac ", "bootstrap", "arch",
         "significance", "hypothesis test", "multiple testing", "deflated sharpe"],
    "L2 bo nho (31GB da no 28/07)":
        ["polars", "duckdb", "memory", "out-of-core", "memmap", "joblib", "dask", "arrow"],
    "L3 toc do quet (magnetic phai rut 169->53 moc)":
        ["numba", "vectorized", "cython", "rust", "fast backtest", "vectorbt", "jit"],
    "L4 kiem dinh chong lan (purged CV)":
        ["purged", "embargo", "walk forward", "cross validation", "combinatorial",
         "lopez de prado", "mlfinlab"],
    "L5 du lieu (FRED chan HY spread, DTWEXM ngung)":
        ["data provider", "market data", "openbb", "data feed", "yfinance", "eod",
         "alternative data"],
}
# Repo la KHUNG chu khong phai cong cu -> The Brain da hoc bai nay 27/07: 23 repo GitHub
# cho 0 chien luoc vi deu la framework (ai-trader, EA31337...). Danh dau de khoi mat cong.
KHUNG = ["framework", "boilerplate", "template", "starter", "awesome", "collection",
         "list of", "tutorial", "course", "example"]

df = pd.read_parquet(NGUON)
df = df[df["nguon"] == "GitHub"].copy()
df["van_ban"] = (df["ten"].astype(str) + " " + df["tom_tat"].astype(str)).str.lower()


def khop(tu, s):
    mau = rf"\b{re.escape(tu)}\b" if len(tu) <= 4 else re.escape(tu)
    return re.search(mau, s) is not None


df["lo_hong"] = df["van_ban"].apply(
    lambda s: " | ".join(k for k, tu in LO_HONG.items() if any(khop(t, s) for t in tu)))
df["la_khung"] = df["van_ban"].apply(lambda s: any(khop(t, s) for t in KHUNG))

print(f"{len(df)} repo GitHub trong kho nguon\n")
hop = df[(df["lo_hong"] != "") & (~df["la_khung"])].sort_values("sao", ascending=False)
print(f"=== {len(hop)} repo VA duoc lo hong that (da bo framework/awesome-list) ===\n")
for _, r in hop.head(25).iterrows():
    sao = f"{int(r['sao']):>6}" if pd.notna(r["sao"]) else "     ?"
    print(f"  {sao} sao  {r['giay_phep']:<12} {r['ten'][:46]:46}")
    print(f"              {r['lo_hong']}")
    print(f"              {str(r['tom_tat'])[:110]}")
print(f"\n--- bi bo vi la khung/awesome-list: {int(df['la_khung'].sum())} repo ---")
for _, r in df[df["la_khung"]].head(8).iterrows():
    print(f"  {r['ten'][:52]}")
print(f"\n--- khong va lo hong nao: {int(((df['lo_hong']=='') & (~df['la_khung'])).sum())} repo ---")
