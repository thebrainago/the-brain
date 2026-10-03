# -*- coding: utf-8 -*-
"""Xuat M1 tu terminal XM DEMO ra data/<MA>_M1_mq.parquet (chuan kho gia cua du an). Chi doc gia, KHONG dat lenh.

Bay da biet (xem `_tai_chi_so_xm.py`): goi dau sau `symbol_select` tra thieu bar -> thu lai; moc phai RAT XA; dem bar moi nam
de bat doan bi don tu khung khac; spread cua bar M1 la spread THAT (D1 thi bang 0).
Chay: .venv\\Scripts\\python.exe _xuat_m1_xm.py [MA ...]   (khong doi so = ca danh sach)
Ghi `reports/xuat_m1_xm.json` (ho chieu: so bar, tu-den, bar/nam, spread trung vi, thong so ma, loai tai khoan).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

import pandas as pd

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
import MetaTrader5 as mt5  # noqa: E402

from nhan import du_lieu as DL  # noqa: E402

XM = r"C:\Program Files\XM Global MT5\terminal64.exe"
# ma trong kho -> ten ma o san (thu theo thu tu; ma co '#' la loai ma cua tk demo nay)
DANH_SACH = {
    "AUDCAD": ["AUDCAD#", "AUDCAD"], "EURCAD": ["EURCAD#", "EURCAD"], "NZDCAD": ["NZDCAD#", "NZDCAD"],
    "EURGBP": ["EURGBP#", "EURGBP"], "USDCHF": ["USDCHF#", "USDCHF"], "AUDCHF": ["AUDCHF#", "AUDCHF"],
    "AUDNZD": ["AUDNZD#", "AUDNZD"], "USDCAD": ["USDCAD#", "USDCAD"], "EURUSD": ["EURUSD#", "EURUSD"],
    "GBPAUD": ["GBPAUD#", "GBPAUD"], "USDJPY": ["USDJPY#", "USDJPY"],
    "XAUUSD": ["GOLD.i#", "GOLD#", "GOLD"], "US500CASH": ["US500Cash#", "US500Cash"],
}
TU = dt.datetime(2000, 1, 1)


def _lay(sym: str):
    """MOT lenh dai tu 2000 (can MaxBars=2147483647 trong config/common.ini, neu khong 'Invalid params'). Lan dau terminal phai tai lich su
    tu may chu: co the 'Call failed' sau ~4 phut -> thu lai (lan sau xong nhanh vi da nam trong bo nho dem)."""
    tot = None
    for lan in range(5):
        r = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M1, TU, dt.datetime.now() + dt.timedelta(days=1))
        if r is not None and len(r) and (tot is None or len(r) > len(tot)):
            tot = r
            if lan >= 1:
                break
        print("   %s lan %d: %s %s" % (sym, lan + 1, None if r is None else len(r), mt5.last_error()), flush=True)
        time.sleep(3.0)
    return tot

def main(chon: list[str]) -> int:
    if not mt5.initialize(path=XM, timeout=120000):
        print("khong noi duoc MT5:", mt5.last_error())
        return 1
    a = mt5.account_info()
    if a is None or a.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        print("DUNG: khong phai tai khoan DEMO (trade_mode=%s)" % (a.trade_mode if a else None))
        return 2
    bc = {"may_chu": a.server, "loai": "demo", "ngay": time.strftime("%Y-%m-%d %H:%M"), "ma": {}}
    DL.DATA.mkdir(parents=True, exist_ok=True)
    for ma in (chon or DANH_SACH):
        sym = next((s for s in DANH_SACH.get(ma, [ma]) if mt5.symbol_info(s) is not None), None)
        if sym is None:
            bc["ma"][ma] = {"loi": "khong co ma o san"}
            print(ma, "KHONG CO")
            continue
        mt5.symbol_select(sym, True)
        r = _lay(sym)
        if r is None or not len(r):
            bc["ma"][ma] = {"loi": "khong lay duoc bar", "san": sym}
            print(ma, sym, "KHONG LAY DUOC", mt5.last_error())
            continue
        d = pd.DataFrame(r)
        d["time"] = pd.to_datetime(d["time"], unit="s")
        d = d.set_index("time").sort_index()
        d = d[~d.index.duplicated(keep="last")][["open", "high", "low", "close", "tick_volume", "spread"]]
        dich = DL.DATA / ("%s_M1_mq.parquet" % ma)
        d.to_parquet(dich)
        si = mt5.symbol_info(sym)
        theo_nam = d.groupby(d.index.year).size().to_dict()
        sp = d["spread"].where(d["spread"] > 0)
        bc["ma"][ma] = {"san": sym, "bar": int(len(d)), "tu": str(d.index[0]), "den": str(d.index[-1]),
                        "bar_moi_nam": {int(k): int(v) for k, v in theo_nam.items()},
                        "spread_diem_trung_vi": float(sp.median()), "digits": si.digits, "point": si.point,
                        "hop_dong": si.trade_contract_size, "lot_min": si.volume_min, "swap_mua": si.swap_long,
                        "swap_ban": si.swap_short, "file": dich.name}
        print("%-9s %-11s %9d bar  %s -> %s  spread TV %.0f diem" % (ma, sym, len(d), str(d.index[0])[:10], str(d.index[-1])[:10], sp.median()))
    (LAB / "reports").mkdir(exist_ok=True)
    (LAB / "reports" / "xuat_m1_xm.json").write_text(json.dumps(bc, ensure_ascii=False, indent=1), encoding="utf-8")
    mt5.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
