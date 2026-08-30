# -*- coding: utf-8 -*-
"""chay_tat_ca.py - Chay tat ca co che x tat ca tai san, ghi ket qua JSON.
Chay nhe: 1 tien trinh, khong giac may. Ket qua -> lab/quant/ket_qua_all.json
"""
import json, time, sys
from pathlib import Path
import numpy as np

THU_MUC = Path(__file__).resolve().parent
sys.path.insert(0, str(THU_MUC))
import du_lieu
import co_che_A_cung_cau_engulfing as A
import co_che_B_ichimoku_chikou_di as B
import co_che_C_ema_rsi as C
import co_che_D_premium_choch as D

SYMBOLS = ["^GSPC", "GC=F", "EURUSD=X"]


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (list, tuple)):
        return [_clean(x) for x in o]
    if isinstance(o, float) and np.isnan(o):
        return None
    return o


def main(out="ket_qua_all.json"):
    kq = {"chay_luc": time.strftime("%Y-%m-%d %H:%M:%S"), "data_period": du_lieu.DEFAULT_PERIOD, "ket_qua": []}
    for sym in SYMBOLS:
        for mod, fn_name in [(A, "chay"), (B, "chay"), (C, "chay"), (D, "chay")]:
            r = getattr(mod, fn_name)(sym)
            kq["ket_qua"].append(_clean(r))
            print(f"[OK] {r['ten']} | {sym} | lai={r['co_che']['tong_lai_pct']:.1f}% | BH={r['buy_hold']['tong_lai_pct']:.1f}%")
    (THU_MUC / out).write_text(json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DA GHI ->", THU_MUC / out)


if __name__ == "__main__":
    main()
