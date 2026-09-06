# -*- coding: utf-8 -*-
"""_sua_ten_kho.py - DON DU CHAN CUA CUA SAU (mot lan, 06/09/2026).

Ban giao 05/09 ghi: duong LLM tung ghi thang vao `config/co_che_dsl.json` ma
KHONG di qua `ngu_phap.them_co_che`. Cua sau da bit, nhung **hang da vao roi
thi van nam trong kho**. Do lai hom nay: **125/540 co che mang ten chua qua
`chuan_hoa_ten`** - `'SuperTrend Long'`, `'ORB_Long'`, `'MA Crossover Buy'`,
`'Ban khi Stochastic cắt xuống 50'`.

Vi sao khong phai chuyen tham my (chinh docstring cua `them_co_che` noi):
ten di thang vao `gia_thuyet.ma` duoi dang `{tai_san}.{khung}.{ten}.{tham_so}`,
roi bi tim lai bang `LIKE '%.{ten}.%'`. Mot ten co DAU CHAM lam hong cach tach;
`%` va `_` la ky tu dai dien cua LIKE; khoang trang va dau tieng Viet thi lam
hong ca hai. Tuc: mot co che ten xau co the CHAY duoc o tang kham pha nhung
khong bao gio TRA CUU lai duoc o cong - dung hinh dang loi ma du an so nhat,
"duoc dem nhu da co, thuc te chua bao gio doi thanh gi".

Kiem truoc khi sua: **0/125 ten nay co mat trong `gia_thuyet`** (383 dong).
Nen doi ten khong lam mo coi ban ghi nao.

Viec thu hai: 10 cap ten khac nhau QUY VE cung mot ten sau chuan hoa
(`ORB_Long` + `orb_long`). Voi moi cum, giu ban co van tay dieu kien xuat hien
truoc; ban trung van tay bi bo (mot dieu kien mot suat FDR); ban khac van tay
nhung trung ten duoc them hau to so.

Chay: python _sua_ten_kho.py [--that]     (khong co --that = chi in ra)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import ngu_phap as NP     # noqa: E402


def sua(kho: list[dict]) -> tuple[list[dict], dict]:
    """Tra ve (kho moi, bao cao). Khong cham dia."""
    moi, da_dung, theo_vt = [], set(), {}
    bao = {"doi_ten": [], "bo_trung_van_tay": [], "them_hau_to": []}
    for c in kho:
        cu = c.get("ten", "")
        ten = NP.chuan_hoa_ten(cu)
        if not ten:
            bao["bo_trung_van_tay"].append({"ten": cu, "vi_sao": "ten rong"})
            continue
        vt = NP.van_tay_dieu_kien(c)
        if vt in theo_vt:
            bao["bo_trung_van_tay"].append({"ten": cu, "trung_voi": theo_vt[vt]})
            continue
        if ten in da_dung:
            g = 2
            while "%s_%d" % (ten, g) in da_dung:
                g += 1
            bao["them_hau_to"].append({"ten": cu, "thanh": "%s_%d" % (ten, g)})
            ten = "%s_%d" % (ten, g)
        elif ten != cu:
            bao["doi_ten"].append({"tu": cu, "thanh": ten})
        da_dung.add(ten)
        theo_vt[vt] = ten
        moi.append(dict(c, ten=ten))
    return moi, bao


def main() -> int:
    kho = NP.doc_kho()
    moi, bao = sua(kho)
    print("kho %d -> %d co che" % (len(kho), len(moi)))
    print("  doi ten            : %d" % len(bao["doi_ten"]))
    print("  bo vi trung van tay: %d" % len(bao["bo_trung_van_tay"]))
    print("  them hau to so     : %d" % len(bao["them_hau_to"]))
    for d in bao["doi_ten"][:10]:
        print("    %-42s -> %s" % (d["tu"][:42], d["thanh"]))
    for d in bao["bo_trung_van_tay"][:10]:
        print("    BO %-40s (trung %s)" % (d["ten"][:40], d.get("trung_voi", "-")))

    if "--that" not in sys.argv:
        print("\n(chua ghi - them --that de ghi vao config/co_che_dsl.json)")
        return 0
    luu = NP.KHO_CO_CHE.with_suffix(".truoc_sua_ten.json")
    luu.write_text(json.dumps(kho, ensure_ascii=False, indent=1), encoding="utf-8")
    NP.luu_kho(moi)
    print("\nda ghi. ban cu: %s" % luu.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
