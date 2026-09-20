# -*- coding: utf-8 -*-
"""Chay NOI SINH tren du lieu THAT, bao cao can bang chieu + thoi gian.

Sinh ra tu goi 20/09/2026: ba bo sinh tung chi de ve MUA (3.669/0), va
`kiem_khong_nhin_truoc` goi sai tang lam `sinh()` mat 153,7 giay. Don nay do
lai ca hai tren du lieu THAT chu khong tren chuoi tong hop.
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nhan import du_lieu as DL      # noqa: E402
from nhan import ngu_phap as NP     # noqa: E402
from nhan import noi_sinh as NS     # noqa: E402

MA = sys.argv[1] if len(sys.argv) > 1 else "AUDCAD"
KHUNG = sys.argv[2] if len(sys.argv) > 2 else "H4"


def main() -> int:
    NP.nap_vao_mau()
    df = DL.nap(MA, KHUNG)
    tr = DL.hai_nua(df, 0.6)[0]
    ra = {"ma": MA, "khung": KHUNG, "bar_train": len(tr)}
    for ten, ham in (("sinh", NS.sinh), ("sinh_cap", NS.sinh_cap),
                     ("sinh_xu_huong", NS.sinh_xu_huong)):
        t = time.time()
        ds = ham(tr)
        c = Counter(d["chieu"] for d in ds)
        ra[ten] = {"tong": len(ds), "long": c.get(1, 0), "short": c.get(-1, 0),
                   "chieu_0": c.get(0, 0), "giay": round(time.time() - t, 1),
                   "trung_ten": len(ds) - len({d["ten"] for d in ds})}
    print(json.dumps(ra, ensure_ascii=False, indent=1))
    # KHONG DAT khi van lech mot chieu hay con co che khong co huong.
    for ten in ("sinh", "sinh_cap", "sinh_xu_huong"):
        d = ra[ten]
        if d["tong"] and (d["short"] == 0 or d["long"] == 0 or d["chieu_0"]):
            print("KHONG DAT: %s van lech chieu" % ten)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
