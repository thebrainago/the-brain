# -*- coding: utf-8 -*-
"""_hang_doi_toan_hang.py - VI SAO 11 TOAN HANG CHUA AI DUNG?

Khoi 1 cua KE_HOACH_XAY.md bat tra loi cau nay TRUOC khi them toan hang thu 44:
*chung khong duoc sinh ra, hay sinh ra roi bi loai?*

Phep do 12/09 tra loi duoc mot nua: kho 689 -> 891 co che thi `macd` `adx` `cci`
`khoi_luong` `stochastic` LAN DAU xuat hien - dung bang nhung toan hang phien
11/09 day cho khau doc. Danh sach chet 12 -> 11. Vay don bay la KHAU DOC.

File nay do not nua con lai: voi MOI toan hang chet, kho tai lieu co bao nhieu
cau THAT SU noi ve no, va trong so do bo doc bo sot bao nhieu.

    nhac     cau co tu vung cua toan hang do
    la_luat  trong so `nhac`, `loai_cau` nhan la mot luat
    doc_ra   trong so `la_luat`, `dieu_kien_trong_cau` THUC SU sinh ra toan hang do
    thieu    la_luat - doc_ra  <- DAY la so xep hang doi

`thieu` cao = co nguyen lieu that dang bi bo. `nhac` thap = tu vung nay khong
song trong kho, them duong doc cho no la phi cong.

Chay:  python _hang_doi_toan_hang.py
Ra:    reports/HANG_DOI_TOAN_HANG.json
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import doc_hieu as DH  # noqa: E402

RA = GOC / "reports" / "HANG_DOI_TOAN_HANG.json"

#: 11 toan hang ngu phap CO MA CHAY DUOC nhung kho 891 co che chua dung lan nao.
#: Tu vung lay theo cach nguoi viet that goi chung, khong theo ten bien trong ma.
TU_VUNG = {
    "bollinger":      r"\bbollinger\b|\bbbands?\b|\bbb\s*\(|upper band|lower band|middle band",
    "wma":            r"weighted moving average|\bwma\b|linearly weighted",
    "smma":           r"smoothed moving average|\bsmma\b|\brma\b|wilder'?s (?:smoothing|average|ma)",
    "obv":            r"on[-\s]balance volume|\bobv\b",
    "dong_luong":     r"\bmomentum\b|rate of change|\broc\b|\bmom\s*\(",
    "phuong_sai":     r"\bvariance\b|phuong sai",
    "tuong_quan":     r"\bcorrelation\b|\bcorrelated\b|\bcorrelates?\b|tuong quan",
    "dem_lien_tiep":  r"consecutive|\bin a row\b|\bstreak\b|lien tiep",
    "trang_thai_lat": r"\bflips?\b|\bflipped\b|regime (?:change|switch|shift)|"
                      r"state (?:change|flip)|switch(?:es|ed)? (?:from|to)",
    "tong":           r"\bsum of\b|cumulative sum|\bsummed?\b|tong cua",
    "gann_sq9":       r"\bgann\b|square of nine|square of 9|\bsq9\b",
}
TU_VUNG_RE = {k: re.compile(v, re.I) for k, v in TU_VUNG.items()}

RAC = re.compile(r"[<>{}]|\$\.|https?://|\bJournal\b|\bpp\.\b|\bdoi:|^\s*[\[\(]\d")


def _cac_chi_bao(nut, ra: set) -> set:
    """Gom moi `chi_bao` xuat hien trong cay dieu kien."""
    if isinstance(nut, dict):
        if "chi_bao" in nut:
            ra.add(str(nut["chi_bao"]))
        for v in nut.values():
            _cac_chi_bao(v, ra)
    elif isinstance(nut, (list, tuple)):
        for v in nut:
            _cac_chi_bao(v, ra)
    return ra


def main() -> int:
    db = sqlite3.connect(GOC / "nao.db")
    dong = db.execute(
        "SELECT url, van_ban FROM noi_dung "
        "WHERE kieu IS NOT 'ma_nguon' AND length(coalesce(van_ban,'')) > 600 "
        "ORDER BY id"
    ).fetchall()
    db.close()
    print(f"ban doc: {len(dong)}")

    dem = {k: Counter() for k in TU_VUNG}
    vi_du = {k: [] for k in TU_VUNG}
    thay, so_cau = set(), 0

    for i, (url, vb) in enumerate(dong):
        if i % 500 == 0:
            print(f"  ... {i}/{len(dong)}", flush=True)
        for _, cau in DH.cac_cau(DH._chuan(vb or "")):
            c = cau.strip()
            if not (40 <= len(c) <= 320) or RAC.search(c):
                continue
            khoa = re.sub(r"\s+", " ", c.lower())[:120]
            if khoa in thay:
                continue
            thay.add(khoa)
            so_cau += 1

            trung = [k for k, rx in TU_VUNG_RE.items() if rx.search(c)]
            if not trung:
                continue
            for k in trung:
                dem[k]["nhac"] += 1

            # Chi tra gia cho `loai_cau` tren cau CO tu vung - re hon nhieu lan.
            try:
                nhan = DH.loai_cau(c)
            except Exception:
                nhan = None
            if not nhan:
                continue
            for k in trung:
                dem[k]["la_luat"] += 1

            try:
                ket = DH.dieu_kien_trong_cau(c)
            except Exception:
                continue
            dk = ket[0] if isinstance(ket, (list, tuple)) and len(ket) == 2 else ket
            co = _cac_chi_bao(dk, set())
            for k in trung:
                if k in co:
                    dem[k]["doc_ra"] += 1
                elif len(vi_du[k]) < 6:
                    vi_du[k].append({"cau": c[:300], "nguon": url or "",
                                     "doc_ra_gi": sorted(co)})

    bang = []
    for k in TU_VUNG:
        d = dem[k]
        bang.append({
            "toan_hang": k, "nhac": d["nhac"], "la_luat": d["la_luat"],
            "doc_ra": d["doc_ra"], "thieu": d["la_luat"] - d["doc_ra"],
        })
    bang.sort(key=lambda r: (-r["thieu"], -r["nhac"]))

    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(
        {"so_cau_quet": so_cau, "so_ban_doc": len(dong), "bang": bang,
         "vi_du_bo_sot": vi_du}, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\ncau duy nhat da quet: {so_cau}\n")
    print(f"{'toan hang':16s} {'nhac':>7s} {'la_luat':>8s} {'doc_ra':>7s} {'THIEU':>7s}")
    for r in bang:
        print(f"{r['toan_hang']:16s} {r['nhac']:7d} {r['la_luat']:8d} "
              f"{r['doc_ra']:7d} {r['thieu']:7d}")
    print(f"\n-> {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
