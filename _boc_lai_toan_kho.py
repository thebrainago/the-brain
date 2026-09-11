# -*- coding: utf-8 -*-
"""_boc_lai_toan_kho.py - DOC LAI toan bo kho van xuoi bang bo doc HIEN TAI.

Vi sao can mot lan chay rieng, khong dua vao `_qwen_het_cong_suat.py`:
lan do chi lay tai lieu `da_khai_thac = 0`. Nhung 3.278 tai lieu DA doc thi
duoc doc bang bo doc CU - ban chua biet macd, adx, cci, stochastic, %D, obv,
wma, khoi luong, "highest high of the last N bars", va con doc qua mot lop rac
vi chua giai ma chuoi thoat `\\uXXXX` (40,0% so ban).

Nang cap bo doc ma khong doc lai kho thi phan nang cap chi an vao tai lieu
TUONG LAI. Kho hien co - thu dat tien nhat cua du an - van giu nguyen hinh dang
cu. Do la ly do 12/43 toan hang van "chua ai dung" ngay sau khi da va bo doc.

`ngu_phap.them_co_che` moi la cong: no CHAY spec tren du lieu that, do ty le
kich hoat, va tu choi cai khong chay duoc. Nen sai sot cua bo doc bi MAY bat,
khong phai bi nguoi tin.

Chay:  python _boc_lai_toan_kho.py [gioi_han_ban]
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import doc_hieu as DH  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402

RA = GOC / "reports" / "BOC_LAI_TOAN_KHO.json"


def chay(gioi_han: int | None = None) -> dict:
    db = sqlite3.connect(GOC / "nao.db")
    q = ("SELECT url, van_ban FROM noi_dung "
         "WHERE kieu IS NOT 'ma_nguon' AND length(coalesce(van_ban,'')) > 600 "
         "ORDER BY id")
    dong = db.execute(q).fetchall()
    db.close()
    if gioi_han:
        dong = dong[:gioi_han]

    truoc = len(NP.doc_kho())
    t0 = time.time()
    dem = Counter()
    toan_hang = Counter()
    moi: list[dict] = []

    for i, (url, vb) in enumerate(dong):
        try:
            bai = DH.doc_bai(vb or "", "", url or "")
        except Exception:
            dem["ban_nem_loi"] += 1
            continue
        for r in bai:
            spec = dict(r["spec"], nguon=url or "boc_lai_11_09")
            try:
                kq = NP.them_co_che(spec)
            except Exception as e:
                dem["cong_nem_loi"] += 1
                dem[f"loi::{type(e).__name__}"] += 1
                continue
            nhan = bool((kq or {}).get("nhan"))
            dem["NHAN" if nhan else "TU_CHOI"] += 1
            if not nhan:
                # Gom LY DO tu choi: day la chan doan quy nhat cua ca lan chay -
                # no noi cong dang chan o dau, thay vi chi noi "khong them duoc".
                for ly in (kq or {}).get("ly_do", [])[:1]:
                    g = str(ly).split(":")[0][:60]
                    dem[f"vi::{g}"] += 1
            if nhan:
                moi.append({"ten": spec.get("ten"), "nguon": url})

                def di(nut):
                    if isinstance(nut, dict):
                        if "chi_bao" in nut:
                            toan_hang[str(nut["chi_bao"])] += 1
                        for v in nut.values():
                            di(v)
                    elif isinstance(nut, list):
                        for v in nut:
                            di(v)
                di(spec.get("vao", []))
                di(spec.get("ra", []))
        if i % 500 == 0 and i:
            print(f"  ... {i}/{len(dong)} ban · kho {len(NP.doc_kho())}", flush=True)

    sau = len(NP.doc_kho())
    ket = {
        "luc": time.strftime("%Y-%m-%d %H:%M:%S"),
        "so_ban": len(dong),
        "giay": round(time.time() - t0),
        "kho_truoc": truoc,
        "kho_sau": sau,
        "them": sau - truoc,
        "trang_thai_cong": dict(dem),
        "toan_hang_trong_co_che_moi": toan_hang.most_common(),
        "vi_du_moi": moi[:30],
    }
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(dong)} ban · {ket['giay']}s")
    print(f"kho {truoc} -> {sau}  (them {sau - truoc})")
    print("cong:", ", ".join(f"{k}={v}" for k, v in dem.most_common(8)))
    if toan_hang:
        print("toan hang trong co che MOI:",
              " · ".join(f"{k} {v}" for k, v in toan_hang.most_common(12)))
    print(f"-> {RA}")
    return ket


if __name__ == "__main__":
    chay(int(sys.argv[1]) if len(sys.argv) > 1 else None)
