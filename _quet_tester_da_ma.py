# -*- coding: utf-8 -*-
"""_quet_tester_da_ma.py - chay ca kho tren NHIEU symbol, moi symbol mot luot
optimization. Ket qua gop lai de xem co che nao song tren NHIEU tai san - mot
co che chi song tren mot ma la mot con so ngau nhien."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chay_tester_kho as C     # noqa: E402

MA = sys.argv[1].split(",") if len(sys.argv) > 1 else [
    "US100Cash", "US500Cash", "US30Cash", "GER40Cash", "GOLD"]

gop = {}
for m in MA:
    print("\n===", m, flush=True)
    try:
        r = C.chay(m, "D1")
    except Exception as e:
        print("  LOI:", type(e).__name__, str(e)[:120])
        continue
    if r.get("loi"):
        print("  LOI:", r["loi"])
        continue
    gop[m] = r["ket"]
    print("  %d pass, %ss" % (r["so_pass"], r["giay"]))

Path("reports/TESTER_DA_MA.json").write_text(
    json.dumps(gop, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n-> reports/TESTER_DA_MA.json")
