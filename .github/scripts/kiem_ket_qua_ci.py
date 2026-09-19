# -*- coding: utf-8 -*-
"""RONG KHONG PHAI AM - cong kiem ket qua cua mot luot tester tren CI.

## VI SAO BUOC NAY TON TAI RIENG

Ma thoat cua `terminal64.exe` khong dang tin: no tra 0 ca khi tester khong
chay bar nao. Va mot bao cao 0 deal doc Y HET mot co che khong bao gio kich
hoat - do la lop loi da lam du an nay tra gia nhieu lan (xem `qwen/cong.py`):

    het quota API      -> me boc chay 2 giay, bao "0/20 co che"
    lech ten provider  -> moi loi goi tra "thieu khoa" -> doc nhu am
    406 URL chet       -> lan boc bao "het ton kho" khi con 4.560 tai lieu

Nen o day, BA trang thai:

    DAT            co bao cao, co deal, doc duoc so
    AM             co bao cao, co deal, va so khong dat nguong
    CHUA_DO_DUOC   khong co bao cao, hoac bao cao 0 deal

Trang thai thu ba tra ve ma thoat khac 0 de job do - mot job xanh voi bang so
rong la thu nguy hiem nhat trong ca duong nay.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

RA = Path("ci_out")


def doc_so_deal(vb: str) -> int | None:
    """So deal trong bao cao. `None` = khong tim thay o dau ca."""
    for mau in (r"Total\s*Trades[^0-9]{0,40}(\d+)",
                r"Total\s*Deals[^0-9]{0,40}(\d+)",
                r"<deals>(\d+)</deals>"):
        m = re.search(mau, vb, re.I)
        if m:
            return int(m.group(1))
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ma", required=True)
    a = ap.parse_args()

    if not RA.exists():
        print("CHUA_DO_DUOC: khong co thu muc ket qua")
        return 2
    bao_cao = [p for p in RA.iterdir()
               if p.suffix.lower() in (".htm", ".html", ".xml")]
    if not bao_cao:
        print("CHUA_DO_DUOC: tester khong de lai bao cao nao")
        print("  file co trong ci_out:", [p.name for p in RA.iterdir()][:20])
        return 2

    tong = None
    for p in bao_cao:
        n = doc_so_deal(p.read_text(encoding="utf-8", errors="ignore"))
        if n is not None:
            tong = (tong or 0) + n
            print(f"  {p.name}: {n} deal")

    if tong is None:
        print("CHUA_DO_DUOC: co bao cao nhung khong doc duoc so deal")
        return 2
    if tong == 0:
        # KHONG duoc doc la "co che khong ra lenh". Lich su khong tai duoc,
        # sai ten symbol, hay khung khong co du lieu deu cho dung con so nay.
        print(f"CHUA_DO_DUOC: {a.ma} - bao cao co, nhung 0 deal.")
        print("  Kiem: lich su co tai duoc khong · ten symbol co dung khong ·")
        print("  khung do co du lieu trong khoang ngay da chon khong.")
        return 2

    print(f"DA_DO: {a.ma} - {tong} deal. Doc bang so trong artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
