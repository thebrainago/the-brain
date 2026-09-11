# -*- coding: utf-8 -*-
"""_san_4_gia_thuyet.py - LUONG 1 cho bon gia thuyet chu du an dua ra 08/09/2026.

San theo CHU DE (`muc_tieu.TU_KHOA_THEO_CHU_DE`) chu khong theo tai san: bon
gia thuyet nay la mo ta CO CHE, khong co ten rieng va khong thuoc ma nao.

Chay: python _san_4_gia_thuyet.py [ngan_sach_giay_moi_chu_de]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import ma_nguon as MN      # noqa: E402
from nhan import muc_tieu as MT      # noqa: E402
from nhan import ngu_phap as NP      # noqa: E402
from nhan import so as SO            # noqa: E402

# Thu tu = thu tu uu tien da lap luan, khong phai thu tu chu du an liet ke.
CHU_DE = ["QUAN_TRI_LENH", "GANN", "DAO_CHIEU", "LEAD_LAG"]


def _dem_tai_lieu() -> int:
    r = SO.mot("SELECT COUNT(*) n FROM tai_lieu")
    return int(r["n"]) if r else 0


def main() -> int:
    ns = int(sys.argv[1]) if len(sys.argv) > 1 else 420
    t0 = time.time()
    tl0, cc0 = _dem_tai_lieu(), len(NP.doc_kho())
    print("=== LUONG 1: SAN 4 GIA THUYET ===")
    print("tai lieu truoc: %d | co che truoc: %d\n" % (tl0, cc0), flush=True)

    tong = {}
    for cd in CHU_DE:
        print("\n---------- %s ----------" % cd, flush=True)
        truoc = _dem_tai_lieu()
        try:
            r = MT.san(cd, ngan_sach_giay=ns, toan_luc=40)
        except Exception as e:                      # nguon loi khong duoc chan ca luot
            print("  LOI: %r" % (e,), flush=True)
            r = {}
        sau = _dem_tai_lieu()
        tong[cd] = {"moi": sau - truoc, "chi_tiet": r}
        print("  => tai lieu moi: %d" % (sau - truoc), flush=True)

    # MQL5 Code Base: nguon CO FILE .mq5 that - uu tien theo quy tac cua du an.
    print("\n---------- MQL5 Code Base (.mq5 that) ----------", flush=True)
    mq = {"tai_duoc": 0, "ghi_moi": 0}
    for v in range(4):
        try:
            r = MN.thu_thap(muc_can=("experts", "indicators"), so_bai=30)
        except Exception as e:
            print("  LOI: %r" % (e,), flush=True)
            break
        mq["tai_duoc"] += int(r.get("tai_duoc", 0) or 0)
        mq["ghi_moi"] += int(r.get("ghi_moi", 0) or 0)
        print("  vong %d: tai %s | moi %s" % (v + 1, r.get("tai_duoc"),
                                              r.get("ghi_moi")), flush=True)
        if not r.get("nhin_thay"):
            break

    tl1 = _dem_tai_lieu()
    print("\n=== TONG KET LUONG 1 (%.0fs) ===" % (time.time() - t0))
    for cd in CHU_DE:
        print("  %-14s +%d tai lieu" % (cd, tong[cd]["moi"]))
    print("  %-14s +%d file .mq5" % ("MQL5", mq["ghi_moi"]))
    print("  tai lieu: %d -> %d (+%d)" % (tl0, tl1, tl1 - tl0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
