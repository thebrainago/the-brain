# -*- coding: utf-8 -*-
"""kiem_the_nhap.py - MAY CHAM cho ban nhap the phuong phap do LLM re viet (tai_lieu/GIAO_VIEC_DEEPSEEK.md muc 3).

    python3 -m nhan.kiem_the_nhap reports/deepseek/the        # cham ca thu muc; ma thoat 0 = tat ca dat
Mot ban nhap `<ma>.json` DAT khi: (1) qua `the_phuong_phap.kiem_the`; (2) cung ma voi the trong kho va CHI doi `tham_so` (cac khoa khac
giu nguyen y het); (3) moi o co ten snake_case ASCII khong trung, lop thuoc `dich_tham_so.LOP` (khong con CHUA_PHAN_LOP), don vi khong
rong tru CONG_TAC / HE_SO, mien [min, max, buoc] day du; (4) so o 1..8; (5) o dau tien khong la chuoi mo ta tieng Viet. Khong cham duoc y nghia - Claude lay mau 3 the doc tay.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from nhan import dich_tham_so as DTS
from nhan import the_phuong_phap as TP

_RX = re.compile(r"^[a-z][a-z0-9_]{1,40}$")


def cham(ban_nhap: dict) -> list:
    loi = TP.kiem_the(ban_nhap)
    if loi:
        return loi
    try:
        goc = TP.doc(ban_nhap["ma"])
    except FileNotFoundError:
        return ["ma '%s' khong co trong kho" % ban_nhap["ma"]]
    for k in goc:
        if k != "tham_so" and ban_nhap.get(k) != goc.get(k):
            loi.append("khoa '%s' bi doi (chi duoc doi tham_so)" % k)
    o = ban_nhap["tham_so"]
    if not 1 <= len(o) <= 8:
        loi.append("so o phai 1..8, co %d" % len(o))
    for x in o:
        if not _RX.match(str(x.get("ten", ""))):
            loi.append("o '%s': ten phai snake_case ASCII ngan" % x.get("ten"))
        if x.get("lop") not in DTS.LOP:
            loi.append("o '%s': lop '%s' khong hop le / chua phan lop" % (x.get("ten"), x.get("lop")))
        if x.get("lop") not in (DTS.CONG_TAC, DTS.HE_SO) and not x.get("don_vi"):
            loi.append("o '%s': thieu don_vi" % x.get("ten"))
        if x.get("lop") != DTS.CONG_TAC and not x.get("mien"):
            loi.append("o '%s': thieu mien" % x.get("ten"))
    return loi


def main(argv: list) -> int:
    d = Path(argv[1]) if len(argv) > 1 else TP.LAB / "reports" / "deepseek" / "the"
    xau = 0
    tep = sorted(d.glob("*.json"))
    for p in tep:
        try:
            loi = cham(json.loads(p.read_text(encoding="utf-8")))
        except Exception as e:
            loi = ["khong doc duoc: %s" % e]
        print("%s %s%s" % ("DAT " if not loi else "HONG", p.name, "" if not loi else " :: " + "; ".join(loi[:4])))
        xau += bool(loi)
    print("%d tep, %d dat, %d hong" % (len(tep), len(tep) - xau, xau))
    return 1 if xau else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
