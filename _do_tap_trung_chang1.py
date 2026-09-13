# -*- coding: utf-8 -*-
"""_do_tap_trung_chang1.py - DO xem chang 1 cua pheu giu lai BAO NHIEU MA.

Chang 1 chon `r1.sort(-cagr_dd20)[:200]`. Mot phep sort tren mot so vo huong,
khong co han ngach theo ma. Neu mot ma bat ky cho diem cao co he thong (dong
tien mat gia, ma phi re bat thuong, ma con bar hong chua bi bat) thi no an het
200 o, va chang 2/3/4 - toan bo phan con lai cua pheu - chi nhin thay ma do.

Do 12/09 (ban co bar hong): 200 o song sot -> **2 ma** (EURMXN 2.567 /
GBPTRY 42 cap holdout). File nay do lai sau khi bar hong da duoc sua, de biet
tap trung la TRIEU CHUNG cua ma hong hay la TINH CHAT cua phep chon.
"""
from __future__ import annotations

import collections
import sys
import time
from multiprocessing import Pool
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
sys.stdout.reconfigure(encoding="utf-8")

from nhan import to_hop as TH          # noqa: E402
from nhan import ho_so_symbol as HSS   # noqa: E402


def main() -> int:
    def lay(c, md):
        return sys.argv[sys.argv.index(c) + 1] if c in sys.argv else md
    gh_ma = int(lay("--so-ma", "60"))
    gh_cc = int(lay("--so-co-che", "120"))
    sp = int(lay("--luong", "4"))

    hs = HSS.doc()
    if isinstance(hs, dict):
        hs = list(hs.values())
    ma0 = sorted({str(x.get("ma")) for x in hs
                  if isinstance(x, dict) and x.get("ma")})
    ma, _ = TH.ma_khong_trung(ma0, "D1")
    ma = ma[:gh_ma]
    cap = {m: TH.khung_dung_duoc(m, ["--khung", "D1"]) for m in ma}
    o_mk = [(m, k) for m in ma for k in (cap[m] or [])]
    cc = TH.co_che_dung_duoc(gh_cc)
    v1 = [(m, k, s, "thi_truong", None, None) for m, k in o_mk for s in cc]
    print("%d ma x %d co che = %d o, %d luong" % (len(ma), len(cc), len(v1), sp),
          flush=True)

    t0 = time.time()
    with Pool(sp) as p:
        r = [x for x in p.map(TH._mot_o, v1, chunksize=24)
             if x and "cagr_dd20" in x]
    print("%d o co ket qua trong %.0f giay" % (len(r), time.time() - t0))

    r.sort(key=lambda d: -d["cagr_dd20"])
    for n in (40, 200):
        top = r[:n]
        c = collections.Counter(x["ma"] for x in top)
        print("\ntop %d  ->  %d ma khac nhau (tren %d ma co ket qua)"
              % (n, len(c), len({x["ma"] for x in r})))
        for k, v in c.most_common(6):
            print("   %-14s %3d o  (%.0f%%)" % (k, v, 100 * v / len(top)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
