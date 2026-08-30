# -*- coding: utf-8 -*-
"""MOT MAN HINH cho biet he dang o dau — doc xong trong 30 giay.

Khac `bang_dieu_khien.py` (do van hanh cua dieu phoi) va `BAN_GIAO.py` (in ban
giao hom qua), file nay tra loi dung mot cau: **dau vao dang chay the nao, va
tang kham pha dang co gi.**

Chay:  b toan-canh
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))


def _cn():
    return sqlite3.connect(f"file:{LAB / 'nao.db'}?mode=ro", uri=True)


def _mot(cn, cau, mac_dinh=0):
    try:
        return cn.execute(cau).fetchone()[0]
    except Exception:
        return mac_dinh


def _bang(cn, cau) -> list:
    """Moi truy van deu phai chiu duoc mot so cai TRONG.

    Man hinh nay la thu dau tien nguoi doc khi mo phien. No ma vo vi mot bang
    chua ton tai thi cai hong dau tien nguoi thay lai la chinh cai bao trang
    thai - kieu hong lam mat long tin vao moi so lieu con lai.
    """
    try:
        return list(cn.execute(cau))
    except Exception:
        return []


def main() -> int:
    cn = _cn()
    try:
        return _in(cn)
    finally:
        # Khong dong thi tren Windows file .db bi giu khoa - bo test khong xoa
        # duoc thu muc tam, va tren may that thi mot tien trinh song lau se giu
        # khoa doc suot doi.
        try:
            cn.close()
        except Exception:
            pass


def _in(cn) -> int:
    print("=" * 74)
    print("THE BRAIN — TOAN CANH")
    print("=" * 74)

    print("\n--- DAU VAO ---")
    tl = _mot(cn, "SELECT COUNT(*) FROM tai_lieu")
    nd = _mot(cn, "SELECT COUNT(*) FROM noi_dung WHERE so_ky_tu>0")
    ky = _mot(cn, "SELECT COALESCE(SUM(so_ky_tu),0) FROM noi_dung")
    thieu = _mot(cn, "SELECT COUNT(*) FROM tai_lieu t LEFT JOIN noi_dung n "
                     "ON n.tai_lieu_id=t.id WHERE n.id IS NULL AND t.url LIKE 'http%'")
    khong = _mot(cn, "SELECT COUNT(*) FROM noi_dung WHERE kieu='khong_doc_duoc'")
    print(f"  tai lieu thu duoc   : {tl}")
    print(f"  doc tron ven        : {nd}  ({ky // 4000} trang A4)")
    print(f"  cho doc toan van    : {thieu}")
    print(f"  khong doc duoc      : {khong}")

    print("\n  nguon manh nhat:")
    hang = _bang(cn, "SELECT nguon, COUNT(*) c FROM tai_lieu GROUP BY 1 "
                     "ORDER BY c DESC LIMIT 8")
    for r in hang:
        print(f"    {r[1]:5d}  {r[0]}")
    if not hang:
        print("    (chua co nguon nao)")

    print("\n--- KHO CO CHE / CONG CU ---")
    try:
        from nhan import mau as MAU
        print(f"  mau chien luoc      : {len(MAU.MAU)}")
    except Exception:
        pass
    try:
        from nhan import san_cong_cu as SCC
        kho = SCC.doc_kho()
        pp = sum(1 for v in kho.values()
                 if str(v.get("nhu_cau", "")).startswith("phuong_phap"))
        print(f"  cong cu trong kho   : {len(kho)}  (trong do {pp} la phuong phap)")
    except Exception:
        pass

    print("\n--- TANG KHAM PHA (anh chup gan nhat) ---")
    f = LAB / "reports" / "be_mat_song_song.json"
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        print(f"  {d.get('so_mau')} co che x {d.get('so_ma')} tai san, {d.get('giay')}s "
              f"({d.get('so_tien_trinh')} tien trinh)")
        print(f"  {d.get('tong')}")
        co = [m for m, v in (d.get("pham_vi") or {}).items()
              if v.get("ket_luan") == "CO_CO_CHE"]
        print(f"  qua phep thu phan chung: {', '.join(co) or '(khong co)'}")
    else:
        print("  (chua co anh chup - chay `b quet`)")

    print("\n--- CONG / SO CAI ---")
    print(f"  dong FDR            : {_mot(cn, 'SELECT COUNT(*) FROM fdr')}")
    print(f"  gia thuyet dang ky  : {_mot(cn, 'SELECT COUNT(*) FROM gia_thuyet')}")
    print(f"  ket qua             : {_mot(cn, 'SELECT COUNT(*) FROM ket_qua')}")
    print(f"  ung vien xep hang   : {_mot(cn, 'SELECT COUNT(*) FROM candidate_queue')}")
    print(f"  van de con mo       : "
          f"{_mot(cn, chr(34).join(['SELECT COUNT(*) FROM van_de WHERE trang_thai NOT IN (', 'XONG', ',', 'DA_SUA', ')']).replace(chr(34), chr(39)))}")

    print("\n--- TAI NGUYEN ---")
    try:
        from nhan import do_tai_nguyen as DTN
        t = DTN.tat_ca()
        tab = (t.get("tab") or {}).get("so_tab")
        print(f"  trinh duyet         : {'tat' if tab is None else str(tab) + ' tab'}"
              f"   Chrome {(t.get('chrome') or {}).get('gb')} GB")
        print(f"  may                 : RAM trong {t.get('ram_trong_gb')} GB, "
              f"dung {t.get('ram_dung_pct')}%")
    except Exception as e:
        print(f"  (khong do duoc: {type(e).__name__})")

    print(f"\n  DUNG_LAI: {'CO (he nam im)' if (LAB / 'DUNG_LAI').exists() else 'KHONG'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
