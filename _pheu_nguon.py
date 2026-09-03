# -*- coding: utf-8 -*-
"""PHEU NGUON: tai lieu -> ban doc -> co che -> cau hinh. Ti le chuyen doi bao nhieu?

Chu du an 03/09/2026: *"seeker tim duoc nguon co du lon va chat luong khong?
1 loai tai san pho bien ca tram nam nhu sp500 phai co hang ngan bai va chien
luoc + chien luoc co the bien tau va chuyen thanh he thong giao dich? da tham
so/da khung thi toi noi roi ty le chuyen doi phai xap xi hoac hon nguon dau
vao."*

File nay do TUNG CHANG cua pheu de biet mat hang o dau, thay vi doan.
"""
from __future__ import annotations

import sys
import warnings
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from nhan import so as SO   # noqa: E402


def _n(sql, *a):
    r = SO.mot(sql, *a)
    return int(list(dict(r).values())[0]) if r else 0


def main():
    print("=" * 74)
    print("PHEU NGUON — do 03/09/2026")
    print("=" * 74)

    tl = _n("SELECT COUNT(*) n FROM tai_lieu")
    nd = _n("SELECT COUNT(*) n FROM noi_dung")
    nd_du = _n("SELECT COUNT(*) n FROM noi_dung WHERE so_ky_tu > 800")
    nd_boc = _n("SELECT COUNT(*) n FROM noi_dung WHERE da_boc = 1")
    art = _n("SELECT COUNT(*) n FROM artifact")
    art_cand = _n("SELECT COUNT(*) n FROM artifact WHERE artifact_type='candidate'")
    from nhan import ngu_phap as NP
    kho = NP.doc_kho()
    NP.nap_vao_mau()
    from nhan import mau as MAU
    mau_tong = len(MAU.MAU)

    chang = [
        ("1. tai lieu SEEKER dao ve", tl, None),
        ("2. co ban doc toan van", nd, tl),
        ("3.   ban doc du dai (>800 ky tu)", nd_du, nd),
        ("4.   DA duoc boc co che", nd_boc, nd_du),
        ("5. co che vao kho", len(kho), nd_boc),
        ("6. mau chay duoc (kho + viet tay)", mau_tong, len(kho)),
    ]
    print(f"\n{'chang':<40}{'so luong':>10}{'ti le chang truoc':>20}")
    print("-" * 74)
    for ten, n, mau_so in chang:
        ty = f"{n/mau_so*100:>18.1f}%" if mau_so else " " * 19
        print(f"{ten:<40}{n:>10,}{ty}")
    if tl:
        print(f"\n  TI LE CHUYEN DOI TONG (tai lieu -> co che): "
              f"{len(kho)/tl*100:.2f}%   ({len(kho)} / {tl:,})")

    print("\n-- CHO O DAU MAT NHIEU NHAT --")
    chua_boc = nd_du - nd_boc
    print(f"  ban doc du dai NHUNG CHUA BOC: {chua_boc:,} "
          f"({chua_boc/max(nd_du,1)*100:.1f}% so ban doc du dai)")
    chua_doc = tl - nd
    print(f"  tai lieu CHUA CO ban doc toan van: {chua_doc:,} "
          f"({chua_doc/max(tl,1)*100:.1f}% so tai lieu)")

    print("\n-- TAI LIEU THEO NGUON (top 15) --")
    for r in SO.nhieu("SELECT nguon, COUNT(*) n FROM tai_lieu "
                      "GROUP BY nguon ORDER BY n DESC LIMIT 15") or []:
        d = dict(r)
        print(f"   {d['nguon']:<28}{d['n']:>6,}")

    print("\n-- CO CHE THEO NGUON --")
    c = Counter((k.get("nguon") or "?").split("/")[2] if (k.get("nguon") or "").startswith("http")
                else (k.get("nguon") or "?") for k in kho)
    for k, n in c.most_common(12):
        print(f"   {k[:40]:<42}{n:>5}")

    print("\n-- BAO NHIEU BAI NOI VE SP500? --")
    for tu in ("s&p", "sp500", "spx", "spy", "es futures", "index"):
        n = _n("SELECT COUNT(*) n FROM tai_lieu WHERE LOWER(tieu_de) LIKE ?",
               f"%{tu}%")
        print(f"   tieu de chua '{tu}': {n:>5}")

    print("\n-- NHAN so voi DA THAM SO / DA KHUNG --")
    co_ts = sum(1 for v in MAU.MAU.values() if v.get("tham_so_tam") or
                (v.get("luoi") and v["luoi"] != [{}]))
    print(f"   mau co tham so chinh duoc      : {co_ts}/{mau_tong}")
    print(f"   x 4 khung (D1/H4/H1/M30)       : {mau_tong*4:,} cau hinh")
    print(f"   x ~75 o lan can moi mau        : {co_ts*75:,} cau hinh")
    print(f"   => so voi {tl:,} tai lieu dau vao: "
          f"{co_ts*75/max(tl,1):.1f} lan")


if __name__ == "__main__":
    main()
