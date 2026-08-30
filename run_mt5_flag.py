# -*- coding: utf-8 -*-
"""run_mt5_flag.py - tick-test MT5 that cho he flagship LuoiDoiXung (EURCAD, MOC).
Chay qua Task Scheduler de tranh timeout/dup. Ghi ket qua reports/mt5_ultima.json.
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
import mt5_worker as m

LAB = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
ten = "ultima_tickcheck"
TU, DEN = "2023.01.01", "2026.07.31"

def main():
    print(f"[mt5] bat dau tick-test {m.EA} {m.CAP_CHINH} M1 {TU}->{DEN}", flush=True)
    try:
        m.dong_mt5()
        m.viet_set(ten, {})
        r = m.chay_tester(ten, symbol=m.CAP_CHINH, tu=TU, den=DEN)
    except Exception as e:
        r = {"loi": str(e)[:200]}
    out = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "ea": m.EA,
           "symbol": m.CAP_CHINH, "tu": TU, "den": DEN, "ket_qua": r}
    (LAB / "reports" / "mt5_ultima.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[mt5] XONG:", json.dumps(out, ensure_ascii=False)[:300], flush=True)

if __name__ == "__main__":
    main()
