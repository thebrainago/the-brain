# -*- coding: utf-8 -*-
"""DO SUAT THAT cua `doc_ma` tren 469 ban doc MA NGUON dang nam khong.

Chu du an 03/09/2026: *"ty le chuyen doi phai xap xi hoac hon nguon dau vao"*.

Do duoc hom nay: 3.489 tai lieu -> 2.543 ban doc -> **4 ban tung duoc boc**.
Kho 152 co che khong den tu day chuyen, no den tu mot lo chay tay 01/09.
469 ban doc kieu `ma_nguon` dang nam khong - va ma nguon la dau vao cho suat
CAO NHAT (khong mo ho nhu van xuoi).

File nay KHONG ghi gi vao kho. No chi DO: neu chay het 469 ban thi ra bao
nhieu co che, va suat la bao nhieu phan tram.
"""
from __future__ import annotations

import sys
import time
import warnings
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from nhan import doc_ma as DM      # noqa: E402
from nhan import ngu_phap as NP    # noqa: E402
from nhan import so as SO          # noqa: E402


def main(gioi_han=469):
    ds = SO.nhieu(
        "SELECT n.id, n.van_ban, n.so_ky_tu, t.tieu_de, t.nguon, t.url "
        "FROM noi_dung n LEFT JOIN tai_lieu t ON t.id = n.tai_lieu_id "
        "WHERE n.kieu='ma_nguon' AND n.so_ky_tu > 500 "
        "ORDER BY n.so_ky_tu DESC LIMIT ?", gioi_han) or []
    print(f"=== DO SUAT `doc_ma` tren {len(ds)} ban doc MA NGUON ===")

    t0 = time.time()
    da_co = {c.get("ten") for c in NP.doc_kho()}
    ra_co_che, loi, rong, trung = 0, 0, 0, 0
    theo_nguon = Counter()
    ten_moi = set()
    for i, r in enumerate(ds):
        d = dict(r)
        try:
            kq = DM.doc_chien_luoc(d["van_ban"], nguon=d.get("url") or "",
                                   tien_to="ma")
        except Exception:
            loi += 1
            continue
        cc = (kq or {}).get("co_che") or []
        if not cc:
            rong += 1
            continue
        for spec in cc:
            ten = NP.chuan_hoa_ten(spec.get("ten", ""))
            if not ten:
                continue
            if ten in da_co or ten in ten_moi:
                trung += 1
                continue
            if NP.kiem_khai_bao(spec):
                continue
            ten_moi.add(ten)
            ra_co_che += 1
            theo_nguon[(d.get("nguon") or "?")] += 1
        if (i + 1) % 100 == 0:
            print(f"  ... {i+1}/{len(ds)}  co che MOI {ra_co_che}  "
                  f"({time.time()-t0:.0f}s)", flush=True)

    n = len(ds)
    print(f"\n  da doc      : {n} ban  ({time.time()-t0:.0f}s, "
          f"{(time.time()-t0)/max(n,1)*1000:.0f} ms/ban)")
    print(f"  co che MOI  : {ra_co_che}")
    print(f"  trung ten   : {trung}")
    print(f"  khong ra gi : {rong}")
    print(f"  loi         : {loi}")
    print(f"\n  SUAT: {ra_co_che/max(n,1)*100:.1f} co che moi tren 100 ban ma nguon")
    print(f"  Kho hien tai {len(da_co)} -> se thanh {len(da_co)+ra_co_che}")
    print("\n  -- co che moi theo nguon --")
    for k, v in theo_nguon.most_common(10):
        print(f"     {k:<26}{v:>5}")
    print("\n  -- vai ten moi --")
    for t in sorted(ten_moi)[:15]:
        print(f"     {t}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 469)
