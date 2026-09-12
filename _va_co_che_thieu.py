# -*- coding: utf-8 -*-
"""_va_co_che_thieu.py - DIEN BU TRUONG `co_che` cho hang TON trong kho.

O so 3 cua `KE_HOACH_HOAN_THIEN.md`.

## VAN DE

Do 12/09 (`_truy_chang_4_5.py`): 166/1.418 co che trong kho truot
`kiem_khai_bao`, va **149 trong so do chi thieu dung mot truong: `co_che`**.
Tat ca den tu khau boc `.mq5` (AAPL_Pro.mq5, SteepMA.mq5, Quantora_...).

Mot khai bao truot `kiem_khai_bao` thi **khong bao gio vao duoc cong** - no nam
trong kho nhu hang chet.

## VI SAO KHONG PHAI LOI CUA DUONG BOC HIEN TAI

`boc_ma_llm._dien_co_che` da duoc viet 05/09 dung cho viec nay, va
`ngu_phap.them_co_che` co gac cong. Nen 149 cai nay la **hang TON tu truoc
05/09**, khong phai loi dang tiep dien.

## CACH DIEN - KHONG BIA LY LE

Dung dung quy uoc ma `_dien_co_che` da chot: khong bia mot lap luan kinh te
nghe hop li, ma noi THANG rang khai bao nay CHUA co lap luan. Va danh dau
`_ly_do_may_dien = True` de nguoi duyet loc duoc.

  "Mot cau bia tron tru con te hon truong bo trong: no lam co che trong nhu
   da co ly do."

## NAM CAI KHONG DUOC DIEN

5 khai bao truot vi dieu kien HANG DUNG (`close >= low` luon dung trong mot
bar) hoac hai ve giong het nhau. Chung truot DUNG - dien `co_che` vao khong
cuu duoc gi, chi lam mot dieu kien vo nghia trong nhu hop le. De nguyen.

## GHI TRONG KHOA

`luu_kho` la chuoi DOC-SUA-GHI. Su co 11/09: kho tut 1.149 -> 3 vi hai tien
trinh ghi de nhau, khong mot dong log. Dung `ngu_phap.voi_khoa()`.

Chay:  python _va_co_che_thieu.py [--that]     (khong co --that thi chi DO)
Ra:    reports/VA_CO_CHE_THIEU.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import boc_ma_llm as BML  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402

RA = LAB / "reports" / "VA_CO_CHE_THIEU.json"


def main(argv: list[str]) -> int:
    that = "--that" in argv
    print("che do:", "GHI THAT" if that else "chi DO, khong ghi")

    with NP.voi_khoa():
        kho = NP.doc_kho()
        thieu, khac, lanh = [], [], 0
        for s in kho:
            loi = NP.kiem_khai_bao(s)
            if not loi:
                lanh += 1
            elif all("co_che" in x for x in loi):
                # MOI loi deu noi ve `co_che` -> dien bu cuu duoc.
                # (Khong dung `len(loi) == 1`: mot khai bao thieu truong do
                # sinh HAI loi cung luc - "thieu truong" va "phai la MOT CAU" -
                # nen loc theo so luong loi se bo sot dung 149 cai can va.)
                thieu.append(s)
            else:
                khac.append((s.get("ten"), loi[0][:90]))

        print("kho %d · lanh %d · chi thieu co_che %d · truot ly do KHAC %d"
              % (len(kho), lanh, len(thieu), len(khac)))
        if khac:
            print("\nKHONG dien (truot vi ly do khac - de nguyen):")
            for t, l in khac[:8]:
                print("  %-38s %s" % (str(t)[:38], l[:64]))

        va = []
        for s in thieu:
            nguon = str(s.get("nguon") or s.get("nguon_lan") or "?")
            truoc = str(s.get("co_che") or "")
            BML._dien_co_che(s, nguon)
            sau = NP.kiem_khai_bao(s)
            va.append({"ten": s.get("ten"), "nguon": nguon,
                       "co_che_truoc": truoc[:60],
                       "con_truot": sau})

        con_truot = [x for x in va if x["con_truot"]]
        print("\nda dien %d · con truot sau khi dien: %d" % (len(va), len(con_truot)))
        for x in con_truot[:5]:
            print("  %-38s %s" % (str(x["ten"])[:38], str(x["con_truot"])[:60]))

        if that and va and not con_truot:
            NP.luu_kho(kho)
            print("\nDA GHI kho (%d co che)" % len(kho))
        elif that and con_truot:
            print("\nKHONG GHI: con %d cai truot sau khi dien - sua truoc da"
                  % len(con_truot))

    # Do lai NGOAI khoa de thay trang thai that tren dia
    lai = NP.doc_kho()
    lanh2 = sum(1 for s in lai if not NP.kiem_khai_bao(s))
    print("\nsau khi chay: kho %d · lanh %d (truoc: %d)" % (len(lai), lanh2, lanh))

    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(
        {"ghi_that": that, "kho": len(kho), "lanh_truoc": lanh,
         "lanh_sau": lanh2, "da_dien": len(va),
         "khong_dien_ly_do_khac": [{"ten": t, "loi": l} for t, l in khac],
         "chi_tiet": va[:40]}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("-> %s" % RA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
