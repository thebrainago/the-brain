# -*- coding: utf-8 -*-
"""_ly_do_tu_choi.py - KHAU DOC TU CHOI VI LY DO GI, va moi ly do chan bao nhieu cau?

Khoi 1A cua KE_HOACH_XAY.md. `_corpus_ngu_phap.py` noi tang A dung o 21,3% va
140/150 cau "khong tach duoc cap". No khong noi VI SAO tung cau mot bi chan, nen
khong biet sua cai gi truoc.

File nay doc `con_lai` - phan `dieu_kien_trong_cau` tra ve khi no TU CHOI - roi
gom theo ly do. Ly do nao chan nhieu cau nhat thi sua cai do truoc.

Chi dem cau CO HINH DANG LUAT (co hanh dong giao dich + tu so sanh), khong dem
ca kho: mot ty le tren van tan man khong tra loi duoc cau hoi nao.

Chay:  python _ly_do_tu_choi.py
Ra:    reports/LY_DO_TU_CHOI.json
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

RA = GOC / "reports" / "LY_DO_TU_CHOI.json"

HANH_DONG = re.compile(
    r"\b(buy|sell|long|short|enter|entry|exit|go long|go short|open a position|"
    r"mua|ban|vao lenh|thoat)\b", re.I)
SO_SANH = re.compile(
    r"\b(above|below|cross(?:es|ing|ed)?|greater|less|over|under|exceeds?|"
    r"falls? below|rises? above|tren|duoi|vuot|cat)\b", re.I)
RAC = re.compile(r"[<>{}]|\$\.|https?://|\bJournal\b|\bpp\.\b|\bdoi:|^\s*[\[\(]\d")


def _rut_gon(ly_do: str) -> str:
    """Gop cac ban in khac nhau cua cung mot ly do ve mot khoa."""
    s = re.sub(r"\s+", " ", ly_do.strip().lower())
    s = re.sub(r"'[^']*'", "'X'", s)
    s = re.sub(r"\b\d+([.,]\d+)?\b", "N", s)
    return s[:110]


def main() -> int:
    db = sqlite3.connect(GOC / "nao.db")
    dong = db.execute(
        "SELECT van_ban FROM noi_dung "
        "WHERE kieu IS NOT 'ma_nguon' AND length(coalesce(van_ban,'')) > 600 "
        "ORDER BY id"
    ).fetchall()
    db.close()

    ly_do = Counter()
    vi_du: dict[str, list] = {}
    dem = Counter()
    thay = set()

    for i, (vb,) in enumerate(dong):
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
            # HINH DANG LUAT: phai co ca hanh dong lan tu so sanh.
            if not (HANH_DONG.search(c) and SO_SANH.search(c)):
                continue
            dem["hinh_dang_luat"] += 1

            try:
                ket = DH.dieu_kien_trong_cau(c)
            except Exception as e:
                ly_do[f"NEM LOI: {type(e).__name__}"] += 1
                continue
            dk, con = (ket if isinstance(ket, (list, tuple)) and len(ket) == 2
                       else (ket, ""))
            if dk:
                dem["ra_dieu_kien"] += 1
                continue
            k = _rut_gon(str(con)) if con else "(khong noi ly do)"
            ly_do[k] += 1
            vi_du.setdefault(k, [])
            if len(vi_du[k]) < 4:
                vi_du[k].append(c[:260])

    bang = [{"ly_do": k, "so_cau": n,
             "ty_le": round(n / max(dem["hinh_dang_luat"], 1), 4),
             "vi_du": vi_du.get(k, [])}
            for k, n in ly_do.most_common()]
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(
        {"cau_hinh_dang_luat": dem["hinh_dang_luat"],
         "ra_dieu_kien": dem["ra_dieu_kien"],
         "bi_tu_choi": sum(ly_do.values()), "bang": bang},
        ensure_ascii=False, indent=1), encoding="utf-8")

    tong = dem["hinh_dang_luat"]
    print(f"\ncau co hinh dang luat : {tong}")
    print(f"  ra dieu kien        : {dem['ra_dieu_kien']} ({dem['ra_dieu_kien']/max(tong,1):.1%})")
    print(f"  bi tu choi          : {sum(ly_do.values())}\n")
    print(f"{'so cau':>7s} {'ty le':>7s}  ly do")
    for r in bang[:25]:
        print(f"{r['so_cau']:7d} {r['ty_le']:6.1%}  {r['ly_do']}")
    print(f"\n-> {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
