# -*- coding: utf-8 -*-
"""han_muc.py - KILL-SWITCH va TRAN. Cai phanh, khong phai cai ga.

## Vi sao

Chu du an: *"muc dich cuoi cung la co tien chap nhan ca chi phi va rui ro cao"*.
Chap nhan rui ro cao KHONG phai la chay khong phanh - no la biet chinh xac minh
dang chap nhan bao nhieu, va co mot cai ngat khi vuot qua.

Truoc 11/09/2026 he khong co: tran sut giam, tran lenh/ngay, tran phoi nhiem,
tran von. Mot he chay sai co the chay den khi het tien va khong ai biet truoc.

## Ba nguyen tac

1. **Phanh mac dinh la BAT.** Mot he chua khai han muc thi `duoc_vao_lenh` tra
   False. De quen khai = khong chay, chu khong phai = chay khong gioi han.
2. **Ngat thi PHAI CO NGUOI mo lai.** Tu mo lai sau X phut la cach bien mot cai
   phanh thanh mot cai cham tre.
3. **Moi lan ngat ghi mot su kien.** Mot cai phanh khong doc duoc lich su la mot
   cai phanh khong ai tin.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO, so_lenh as SL
else:
    from . import so as SO
    from . import so_lenh as SL

_SCHEMA = """
CREATE TABLE IF NOT EXISTS han_muc(
  he            TEXT PRIMARY KEY,
  tran_sut_giam REAL,
  tran_lenh_ngay INTEGER,
  tran_phoi_nhiem REAL,
  tran_von      REAL,
  ngat          INTEGER DEFAULT 0,
  ly_do_ngat    TEXT,
  ngat_luc      TEXT,
  mo_lai_boi    TEXT,
  doi_luc       TEXT
);
"""


def _khoi_tao() -> None:
    with SO.ket_noi() as cn:
        cn.executescript(_SCHEMA)


def dat(he: str, tran_sut_giam: float, tran_lenh_ngay: int,
        tran_phoi_nhiem: float, tran_von: float) -> dict:
    """Khai han muc cho mot he. Tat ca deu BAT BUOC va phai duong."""
    _khoi_tao()
    loi = [f"{k} phai > 0" for k, v in
           (("tran_sut_giam", tran_sut_giam), ("tran_lenh_ngay", tran_lenh_ngay),
            ("tran_phoi_nhiem", tran_phoi_nhiem), ("tran_von", tran_von))
           if not v or v <= 0]
    if loi:
        return {"nhan": False, "ly_do": loi}
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT INTO han_muc(he,tran_sut_giam,tran_lenh_ngay,tran_phoi_nhiem,"
            "tran_von,doi_luc) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(he) DO UPDATE SET tran_sut_giam=excluded.tran_sut_giam,"
            "tran_lenh_ngay=excluded.tran_lenh_ngay,"
            "tran_phoi_nhiem=excluded.tran_phoi_nhiem,tran_von=excluded.tran_von,"
            "doi_luc=excluded.doi_luc",
            (he, float(tran_sut_giam), int(tran_lenh_ngay), float(tran_phoi_nhiem),
             float(tran_von), SO.bay_gio()))
    SO.ghi_su_kien("CHAM_TIEN", "dat_han_muc",
                   {"he": he, "tran_sut_giam": tran_sut_giam,
                    "tran_lenh_ngay": tran_lenh_ngay,
                    "tran_phoi_nhiem": tran_phoi_nhiem, "tran_von": tran_von})
    return {"nhan": True, "ly_do": []}


def cua(he: str) -> dict | None:
    _khoi_tao()
    r = SO.mot("SELECT * FROM han_muc WHERE he = ?", he)
    return dict(r) if r else None


def ngat(he: str, ly_do: str) -> dict:
    """KILL-SWITCH. Sau khi goi, `duoc_vao_lenh` tra False cho toi khi co NGUOI
    goi `mo_lai`."""
    _khoi_tao()
    with SO.ket_noi() as cn:
        cn.execute("INSERT INTO han_muc(he,ngat,ly_do_ngat,ngat_luc) "
                   "VALUES(?,1,?,?) ON CONFLICT(he) DO UPDATE SET "
                   "ngat=1, ly_do_ngat=excluded.ly_do_ngat, "
                   "ngat_luc=excluded.ngat_luc",
                   (he, ly_do, SO.bay_gio()))
    SO.ghi_su_kien("CHAM_TIEN", "NGAT", {"he": he, "ly_do": ly_do})
    return {"nhan": True, "ly_do": [], "ngat": True, "vi": ly_do}


def mo_lai(he: str, nguoi: str) -> dict:
    """Mo lai sau khi ngat. PHAI co nguoi - tu mo lai bien phanh thanh cham tre."""
    if not (nguoi or "").strip():
        return {"nhan": False, "ly_do": [
            "mo lai PHAI co ten nguoi. Mot cai phanh tu nha la mot cai cham tre."]}
    _khoi_tao()
    with SO.ket_noi() as cn:
        cn.execute("UPDATE han_muc SET ngat=0, mo_lai_boi=?, doi_luc=? WHERE he=?",
                   (nguoi, SO.bay_gio(), he))
    SO.ghi_su_kien("CHAM_TIEN", "mo_lai", {"he": he, "nguoi": nguoi})
    return {"nhan": True, "ly_do": []}


def duoc_vao_lenh(he: str, phoi_nhiem: float = 0.0,
                  so_lenh_hom_nay: int = 0) -> tuple[bool, str]:
    """(duoc, ly_do). MAC DINH LA KHONG - chua khai han muc thi khong chay."""
    hm = cua(he)
    if not hm or hm.get("tran_von") is None:
        return False, ("chua khai han muc cho he nay - phanh mac dinh la BAT. "
                       "Goi `han_muc.dat(...)` truoc.")
    if hm["ngat"]:
        return False, f"DA NGAT: {hm['ly_do_ngat']} (luc {hm['ngat_luc']})"
    tk = SL.tong_ket(he)
    if tk["sut_giam"] is not None and -tk["sut_giam"] > hm["tran_sut_giam"]:
        return False, (f"sut giam {-tk['sut_giam']:.4g} vuot tran "
                       f"{hm['tran_sut_giam']:.4g}")
    if so_lenh_hom_nay >= hm["tran_lenh_ngay"]:
        return False, (f"da {so_lenh_hom_nay} lenh hom nay, tran "
                       f"{hm['tran_lenh_ngay']}")
    if phoi_nhiem > hm["tran_phoi_nhiem"]:
        return False, (f"phoi nhiem {phoi_nhiem:.4g} vuot tran "
                       f"{hm['tran_phoi_nhiem']:.4g}")
    return True, "trong han muc"


def quet() -> dict:
    """Quet moi he dang chay; NGAT cai nao vuot tran. Goi dinh ky."""
    _khoi_tao()
    da_ngat = []
    for r in SO.nhieu("SELECT ma FROM he_chay WHERE trang_thai <> 'DUNG'"):
        duoc, ly = duoc_vao_lenh(r["ma"])
        if not duoc and ly.startswith("sut giam"):
            ngat(r["ma"], ly)
            da_ngat.append({"he": r["ma"], "ly_do": ly})
    return {"so_ngat": len(da_ngat), "da_ngat": da_ngat}


if __name__ == "__main__":
    print(json.dumps(quet(), ensure_ascii=False, indent=1))
