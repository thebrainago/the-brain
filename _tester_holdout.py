# -*- coding: utf-8 -*-
"""_tester_holdout.py - CUNG MOT KHO, HAI CUA SO THOI GIAN, TREN TICK THAT.

Bang xep hang cua mot cua so la mot bang cuc tri ngau nhien. Bai nay chay CA KHO
hai lan tren cung symbol - doan TRAIN va doan HOLDOUT - roi doi chieu THU HANG.
Co che song that thi giu duoc hang; con so dep cua mot giai doan thi rot.

Moc cat lay dung moc cua `du_lieu.hai_nua(0.6)` ma Python dung, de hai ben so
duoc voi nhau.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chay_tester_kho as C     # noqa: E402

MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
CAT = "2020.05.01"        # ~60% cua 2011-09..2026-07

ra = {}
for ten, tu, den in (("train", "2011.01.01", CAT),
                     ("holdout", CAT, "2026.07.29")):
    print("\n===", ten, tu, "->", den, flush=True)
    r = C.chay(MA, "D1", tu=tu, den=den)
    if r.get("loi"):
        print("  LOI:", r["loi"])
        continue
    ra[ten] = r["ket"]
    print("  %d pass, %ss" % (r["so_pass"], r["giay"]))

Path("reports/TESTER_HOLDOUT_%s.json" % MA).write_text(
    json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")

tr = {r["ten"]: r for r in ra.get("train", []) if r["lenh"] >= 25}
ho = {r["ten"]: r for r in ra.get("holdout", []) if r["lenh"] >= 25}
chung = sorted(set(tr) & set(ho), key=lambda t: -tr[t]["sharpe"])
print("\n%d co che co >=25 lenh o CA HAI doan" % len(chung))
print("%-40s %8s %8s %7s %7s" % ("co che", "sh_train", "sh_hold", "lenh_tr", "lenh_ho"))
giu = 0
for t in chung[:30]:
    a, b = tr[t], ho[t]
    if a["sharpe"] > 0 and b["sharpe"] > 0:
        giu += 1
    print("%-40s %8.2f %8.2f %7d %7d"
          % (t[:40], a["sharpe"], b["sharpe"], a["lenh"], b["lenh"]))
print("\nduong o CA HAI doan: %d/%d" % (giu, len(chung)))
