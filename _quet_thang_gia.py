# -*- coding: utf-8 -*-
"""_quet_thang_gia.py - quet CA KHO: loi khai nao dinh DON VI GIA.

    python _quet_thang_gia.py            # quet het, ghi config/thang_gia.json
    python _quet_thang_gia.py --so 200   # thu nhanh

Xem `nhan/thang_gia.py` cho vi sao. Tom tat: `than_nen > 0.5` chet sach tren
moi cap FX va song tren vang/chi so, chi vi muc gia khac nhau - va cua vao kho
do ty le kich hoat tren XAUUSD nen no vao kho voi mot con so dep.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

_DS = None


def _khoi_tao():
    global _DS
    from nhan import thang_gia as TG
    _DS = TG.chuoi()


def _mot(spec):
    from nhan import thang_gia as TG
    try:
        return TG.mot_co_che(spec, _DS)
    except Exception as e:                       # pragma: no cover
        return {"ten": spec.get("ten"), "ho": spec.get("ho"),
                "ty_le": {}, "xep_loai": "CHUA_DO_DUOC", "loi": str(e)[:120]}


def main() -> int:
    import multiprocessing as mp
    from nhan import ngu_phap as NP
    from nhan import thang_gia as TG
    from nhan import tran_cpu as TC

    so = 0
    if "--so" in sys.argv:
        so = int(sys.argv[sys.argv.index("--so") + 1])
    kho = NP.doc_kho()
    if so:
        kho = kho[:so]
    n_luong = max(1, min(TC.so_luong_goi_y(), 10))
    print("quet %d co che tren %d chuoi, %d luong"
          % (len(kho), len(TG.CHUOI_DO), n_luong))
    t0 = time.time()
    with mp.Pool(n_luong, initializer=_khoi_tao) as p:
        ket = p.map(_mot, kho, chunksize=8)
    giay = round(time.time() - t0, 1)

    dem = Counter(k["xep_loai"] for k in ket)
    d = {c["ten"]: c for c in ket if c.get("ten")}
    TG.KHO.write_text(json.dumps(
        {"do_luc": time.strftime("%Y-%m-%d %H:%M"), "chuoi": [t for t, _, _ in TG.chuoi()],
         "dem": dict(dem), "co_che": d}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print("\n%d co che, %ss" % (len(ket), giay))
    for k, v in dem.most_common():
        print("  %-22s %5d  (%.1f%%)" % (k, v, 100.0 * v / max(1, len(ket))))

    xau = [k for k in ket if k["xep_loai"] == "PHU_THUOC_THANG_GIA"]
    print("\nHO CUA CAC CO CHE DINH DON VI GIA:")
    for h, n in Counter(k.get("ho") or "?" for k in xau).most_common(8):
        print("  %-24s %4d" % (h, n))
    print("\n%-46s %s" % ("co che", "  ".join(
        t.split(".")[0][:7] for t, _, _ in TG.chuoi())))
    for k in xau[:20]:
        print("%-46s %s" % (k["ten"][:46], "  ".join(
            "  .  " if k["ty_le"].get(t) is None else "%5.3f" % k["ty_le"][t]
            for t, _, _ in TG.chuoi())))
    print("\n-> config/thang_gia.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
