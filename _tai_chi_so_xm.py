# -*- coding: utf-8 -*-
"""Tai bar + phi that cho cac chi so CASH cua XM (03/09/2026).

Chu du an: "mot cong chay hay xem luon ca us500 va uk100, nhung chi so em a va
an toan nhat".

Bay da biet, deu ap o day:
  - goi `copy_rates_*` DAU sau `symbol_select` tra THIEU bar -> thu lai 4 lan
  - phai dung `copy_rates_range` voi moc RAT XA (`copy_rates_from_pos` cat mat
    nhieu nam), roi DEM BAR MOI NAM de bat doan bi don tu khung khac
  - bar D1 cua XM co `spread = 0`, chi H1/M1 moi co spread THAT
"""
from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import MetaTrader5 as mt5  # noqa: E402

from nhan import chi_phi as CP  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
XM = r"C:\Program Files\XM MT5\terminal64.exe"
CHI_SO = ["UK100Cash", "US500Cash", "GER40Cash", "EU50Cash", "FRA40Cash",
          "JP225Cash", "AUS200Cash", "US30Cash"]
KHUNG = {"D1": mt5.TIMEFRAME_D1, "H4": mt5.TIMEFRAME_H4, "H1": mt5.TIMEFRAME_H1}
TU = dt.datetime(1990, 1, 1)


def _bar(sym: str, tf, ten_khung: str):
    """Lay bar, thu lai 4 lan vi goi dau sau symbol_select tra thieu."""
    tot = None
    for _ in range(4):
        r = mt5.copy_rates_range(sym, tf, TU, dt.datetime.now())
        if r is not None and len(r) and (tot is None or len(r) > len(tot)):
            tot = r
        if tot is not None and len(tot) > 500:
            break
        time.sleep(1.5)
    if tot is None or not len(tot):
        return None
    d = pd.DataFrame(tot)
    d["time"] = pd.to_datetime(d["time"], unit="s")
    d = d.set_index("time").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    return d


def main():
    if not mt5.initialize(path=XM, timeout=120000):
        print("khong noi duoc MT5:", mt5.last_error())
        return
    print("server:", mt5.account_info().server)
    for sym in CHI_SO:
        if not mt5.symbol_select(sym, True):
            print(f"{sym:<12} khong bat duoc")
            continue
        time.sleep(0.5)
        si = mt5.symbol_info(sym)
        gia = si.bid or si.ask or 0
        m, b, tc = CP._quy_doi_swap(si, gia, si.point, si.trade_contract_size)
        print(f"\n{sym}  gia {gia:.2f}  swap_mode {si.swap_mode}  "
              f"phi mua {m*100 if m is not None else float('nan'):.3f}%/nam  "
              f"phi ban {b*100 if b is not None else float('nan'):.3f}%/nam  ({tc})")
        for ten_khung, tf in KHUNG.items():
            d = _bar(sym, tf, ten_khung)
            if d is None:
                print(f"   {ten_khung}: khong co bar")
                continue
            # DEM BAR MOI NAM - bat doan bi don tu khung khac
            dem = d.groupby(d.index.year).size()
            mong = [f"{y}:{n}" for y, n in dem.items() if n < (50 if ten_khung == "D1" else 200)]
            f = DATA / f"xm_{sym.lower()}_{ten_khung.lower()}.parquet"
            d.to_parquet(f)
            print(f"   {ten_khung}: {len(d):>7} bar  {d.index[0].date()} -> "
                  f"{d.index[-1].date()}  -> {f.name}"
                  + (f"   NAM MONG: {mong[:6]}" if mong else ""))
    mt5.shutdown()


if __name__ == "__main__":
    main()
