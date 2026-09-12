# -*- coding: utf-8 -*-
"""Chay 262 co che tren cac cap MDE THAP NHAT, gop da thoi dai.

Chi do - KHONG dang ky gia thuyet, khong cham holdout, khong ghi so FDR.
"""
import sys, json, time, warnings
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

from nhan import da_thoi_dai as DT
from nhan import do_luc as DL
from nhan import ngu_phap as NP
from pathlib import Path

# Cap co MDE thap nhat do duoc, cong SP500 (co 3 cua so sach de gop).
CAP = [("YH_NASDAQ", "D1"), ("USDJPY", "D1"), ("EURUSD", "D1"),
       ("YH_NIKKEI", "D1"), ("SP500", "D1")]

kho = NP.doc_kho()
print(f"kho co che: {len(kho)} | cap: {len(CAP)}")
mde = {}
for ma, k in CAP:
    try:
        mde[(ma, k)] = DL.mde_cua(ma, k).get("mde")
    except Exception:
        mde[(ma, k)] = None
print("MDE:", {f"{a}|{b}": v for (a, b), v in mde.items()})
print()

t0 = time.time()
ket = []
for i, spec in enumerate(kho, 1):
    for ma, k in CAP:
        try:
            r = DT.chay_co_che(spec, ma, k)
        except Exception:
            continue
        g = r.get("gop") or {}
        s = g.get("sharpe_gop")
        if s is None:
            continue
        m = mde.get((ma, k))
        ket.append({"ten": spec.get("ten"), "ho": spec.get("ho"),
                    "ma": ma, "khung": k, "sharpe_gop": s,
                    "so_bar": g.get("so_bar"), "so_thoi_dai": g.get("so_thoi_dai"),
                    "dong_thuan": g.get("dong_thuan"),
                    "tung_thoi_dai": g.get("sharpe_tung_thoi_dai"),
                    "mde": m, "vuot_mde": (m is not None and s >= m)})
    if i % 40 == 0:
        print(f"  ... {i}/{len(kho)} co che ({time.time()-t0:.0f}s, "
              f"{len(ket)} phep do)")

ket.sort(key=lambda x: -(x["sharpe_gop"] or -9))
json.dump(ket, open("quet_nen_dat.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

vuot = [k for k in ket if k["vuot_mde"]]
print()
print(f"TONG phep do: {len(ket)} | VUOT MDE: {len(vuot)}")
print()
print(f"{'sharpe':>7} {'mde':>6} {'bar':>7} {'td':>3} {'dth':>5}  co che / cap")
for k in ket[:25]:
    dau = "**" if k["vuot_mde"] else "  "
    print(f"{k['sharpe_gop']:>7.3f} {str(k['mde'])[:6]:>6} {k['so_bar']:>7} "
          f"{k['so_thoi_dai']:>3} {str(k['dong_thuan']):>5} {dau}"
          f"{str(k['ten'])[:30]:<30} {k['ma']}|{k['khung']}")
