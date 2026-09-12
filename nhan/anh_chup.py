# -*- coding: utf-8 -*-
"""anh_chup.py - GHIM BAN DU LIEU de mot ket qua tai lap duoc.

## Lo hong no va

`du_lieu.kho()` chon ban theo KICH THUOC FILE: voi moi ma, ban `.parquet` to
nhat thang. Nen chi can them mot file vao `data/` la ban duoc chon cua ca mot ma
doi - **khong mot loi canh bao nao**. Ket qua chay hom nay va ket qua chay lai
sau ba thang co the den tu hai bang gia khac nhau.

Voi mot he lay HOLDOUT lam trong tai, do la lo hong nen mong: `quant_plan` dong
bang KE HOACH (plan_hash) nhung khong dong bang DU LIEU. Hai gia thuyet cung
plan_hash van co the da chay tren hai the gioi khac nhau.

## Cach lam

    ghim(ma)          ghi lai ban DANG duoc chon: duong dan, hash noi dung,
                      so dong, khoang thoi gian
    ban_ghim(ma)      tra ve duong dan da ghim (hoac None)
    kiem(ma)          ban da ghim co con NGUYEN khong -> (lanh, mo_ta)
    kiem_tat_ca()     quet ca kho
    van_tay_ghim()    mot hash cua TOAN BO tap ghim - de nhet vao plan_hash

## Hai quyet dinh co y

1. `kho()` **TON TRONG** ghim (chon dung ban da ghim), no khong nem loi. Nem loi
   trong `kho()` se lam sap moi duong chay chi vi mot file phu bi sua.
2. `kiem()` thi **NEM RA su that**: ban da ghim ma noi dung doi thi do la mot su
   kien nghiem trong, phai doc duoc bang may, va phai chan viec cham holdout.

Tuc la: chay thi khong gay, nhung KET LUAN thi phai sach.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

_SCHEMA = """
CREATE TABLE IF NOT EXISTS anh_chup(
  ma        TEXT PRIMARY KEY,
  file      TEXT NOT NULL,
  hash      TEXT NOT NULL,
  so_byte   INTEGER,
  so_dong   INTEGER,
  khung_goc TEXT,
  tu        TEXT,
  den       TEXT,
  ghim_luc  TEXT,
  ghi_chu   TEXT
);
"""

#: Bo nho tam trong MOT tien trinh: (duong dan, so byte, mtime) -> hash.
#: Bam lai mot file 200 MB moi lan goi `kho()` se giet toc do; nhung neu kich
#: thuoc HOAC mtime doi thi bam lai, nen no khong bo sot thay doi that.
_DEM: dict[tuple, str] = {}


def _khoi_tao() -> None:
    with SO.ket_noi() as cn:
        cn.executescript(_SCHEMA)


def hash_file(p: Path | str, dung_dem: bool = False) -> str:
    """Bam noi dung file. `dung_dem=True` moi tin bo dem.

    ## MAC DINH DOI 12/09/2026: TU `True` SANG `False`

    Bo dem khoa theo `(duong dan, so byte, mtime_ns)`. Mot file bi ghi de voi
    CUNG kich thuoc trong cung mot nhip dong ho cua he tep se giu nguyen khoa -
    tuc mot thay doi DI LOT, im lang. Ghi chu cu cua chinh ham nay da noi ro
    dieu do, va `test_bam_lai_khi_file_doi` bat duoc that (tren Windows/NTFS,
    hai lan ghi 5.000 byte lien tiep cho cung `mtime_ns`).

    Nhung mac dinh khi do van la `True`, tuc **duong NGUY HIEM la duong mac
    dinh** va duong an toan phai duoc nho. Mot bo "chup anh" de phat hien thay
    doi ma bo sot thay doi thi te hon la khong co.

    Nen gio: mac dinh BAM LAI. Ai can toc do thi khai ro `dung_dem=True` -
    `ghim_ca_kho()` (269 file parquet) dang GHI chu khong dang KIEM, no duoc
    phep tin bo dem.
    """
    p = Path(p)
    st = p.stat()
    khoa = (str(p), st.st_size, st.st_mtime_ns)
    if dung_dem and khoa in _DEM:
        return _DEM[khoa]
    h = hashlib.blake2b(digest_size=16)
    with p.open("rb") as f:
        for khoi in iter(lambda: f.read(1 << 20), b""):
            h.update(khoi)
    _DEM[khoa] = h.hexdigest()
    return _DEM[khoa]


def ghim(ma: str, ghi_chu: str = "") -> dict:
    """Ghim ban DANG duoc `du_lieu.kho()` chon cho ma nay."""
    from . import du_lieu as DL  # nhap muon: du_lieu khong duoc phu thuoc nguoc
    _khoi_tao()
    b = DL.kho().get(ma)
    if not b:
        return {"nhan": False, "ly_do": [f"khong co ma {ma!r} trong kho"]}
    p = Path(b["file"])
    tu = den = ""
    try:
        df = DL.nap(ma, b.get("khung_goc") or "D1")
        if df is not None and len(df):
            tu, den = str(df.index[0])[:19], str(df.index[-1])[:19]
    except Exception:
        pass
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT INTO anh_chup(ma,file,hash,so_byte,so_dong,khung_goc,tu,den,"
            "ghim_luc,ghi_chu) VALUES(?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(ma) DO UPDATE SET file=excluded.file,hash=excluded.hash,"
            "so_byte=excluded.so_byte,so_dong=excluded.so_dong,"
            "khung_goc=excluded.khung_goc,tu=excluded.tu,den=excluded.den,"
            "ghim_luc=excluded.ghim_luc,ghi_chu=excluded.ghi_chu",
            (ma, str(p), hash_file(p, dung_dem=True), p.stat().st_size, b.get("so_dong"),
             b.get("khung_goc"), tu, den, SO.bay_gio(), ghi_chu))
    return {"nhan": True, "ly_do": [], "file": str(p),
            "hash": hash_file(p, dung_dem=True)}


def ghim_theo_ma() -> dict[str, dict]:
    """Toan bo tap ghim, mot lan truy van. `du_lieu.kho()` goi ham nay moi lan
    dung bo dem nen no phai RE - mot truy van, khong bam file nao."""
    _khoi_tao()
    return {d["ma"]: dict(d) for d in SO.nhieu("SELECT * FROM anh_chup")}


def ban_ghim(ma: str) -> dict | None:
    _khoi_tao()
    r = SO.mot("SELECT * FROM anh_chup WHERE ma = ?", ma)
    return dict(r) if r else None


def kiem(ma: str) -> tuple[bool, str]:
    """(lanh, mo_ta). Chua ghim thi coi la LANH - khong the trach cai chua hua."""
    g = ban_ghim(ma)
    if not g:
        return True, "chua ghim"
    p = Path(g["file"])
    if not p.exists():
        return False, f"ban da ghim BIEN MAT: {p.name}"
    h = hash_file(p, dung_dem=False)      # KHONG tin bo dem o cho PHAT HIEN thay doi
    if h != g["hash"]:
        return False, (f"ban da ghim DOI NOI DUNG: {p.name} "
                       f"({g['hash'][:12]} -> {h[:12]}); ket qua cu KHONG tai lap duoc")
    return True, "nguyen"


def kiem_tat_ca() -> dict:
    _khoi_tao()
    dong = SO.nhieu("SELECT ma FROM anh_chup ORDER BY ma")
    hong = []
    for d in dong:
        lanh, mo_ta = kiem(d["ma"])
        if not lanh:
            hong.append({"ma": d["ma"], "mo_ta": mo_ta})
    return {"so_ghim": len(dong), "so_hong": len(hong), "hong": hong}


def van_tay_ghim() -> str:
    """Mot hash cua TOAN BO tap ghim - de nhet vao `plan_hash`.

    Hai gia thuyet cung ke hoach nhung khac tap du lieu se co plan_hash khac
    nhau. Khong co dieu nay thi `plan_hash` chi dong bang duoc mot nua bai toan.
    """
    _khoi_tao()
    dong = SO.nhieu("SELECT ma, hash FROM anh_chup ORDER BY ma")
    h = hashlib.blake2b(digest_size=16)
    for d in dong:
        h.update(f"{d['ma']}={d['hash']};".encode())
    return h.hexdigest()


def ghim_ca_kho(chi_du_ohlc: bool = True) -> dict:
    from . import du_lieu as DL
    dem = {"ghim": 0, "bo_qua": 0}
    for ma, b in DL.kho().items():
        if chi_du_ohlc and not b.get("du_ohlc"):
            dem["bo_qua"] += 1
            continue
        dem["ghim" if ghim(ma)["nhan"] else "bo_qua"] += 1
    dem["van_tay"] = van_tay_ghim()
    return dem


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ghim-ca-kho":
        print(json.dumps(ghim_ca_kho(), ensure_ascii=False, indent=1))
    else:
        print(json.dumps(kiem_tat_ca(), ensure_ascii=False, indent=1))
        print("van tay tap ghim:", van_tay_ghim())
