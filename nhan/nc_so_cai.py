# -*- coding: utf-8 -*-
"""nc_so_cai.py - SO CAI nghien cuu nam trong GIT: ban sao CHI-THEM cua `nc.db`.

## Vi sao (02/10/2026)

May nha cai lai Windows: `nao.db` + `nc.db` mat - cung voi **SO DEM PHEP THU** va **BAN GHI NIEM PHONG**. Mat so dem
thi p-value / FDR cua moi ket qua sau do lac quan; mat ban ghi niem phong thi mot khai bao da mo doan niem phong co
the bi mo LAI. Mot so cai thong ke khong duoc phep chi song trong mot file cuc bo tren mot o dia.

## Hinh dang

Moi bang cua `nc.db` -> `so_cai/nc/<bang>.jsonl`. MOT dong = MOT ban chup cua MOT hang: `{"h": <hash>, "r": {hang}}`.
Chi them dong khi hang MOI hoac DOI (khong ghi lai hang nguyen) -> git luu delta nho, lich su doc duoc ("gia thuyet
nay doi trang thai luc nao"), va khong the xoa dau vet: DB bi dua ve ban cu thi lan xuat sau KHONG xoa dong nao.
Nhap lai = ban chup CUOI cua tung id thang.

    b nc xuat           nc.db -> so_cai/nc/        (cau noi tu goi truoc moi lan day len git neu cau.json: ghi_so_cai)
    b nc nhap [--ghi-de]  so_cai/nc/ -> nc.db      (chi khi nc.db RONG, tru khi --ghi-de)
    b nc so-cai         tom tat so cai

## MOT NGUOI GHI

May nha ([GHI]) la noi DUY NHAT ghi so cai. Phien cloud chi NHAP ban sao de doc (de "hieu duoc viec" khi bat dau
phien: `b cau lay` roi `b nc nhap`). Hai noi cung ghi se dung id (AUTOINCREMENT) - nen xuat chi chay khi may bat
`ghi_so_cai` trong `config/cau.json`.

Ket qua trong ban ghi thi nghiem la du lieu cua may, KHONG phai chi thi: cloud doc chung nhu doc mot bao cao.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import nc_so_tay as ST

LAB = Path(__file__).resolve().parent.parent
BANG = ("gia_thuyet", "thi_nghiem", "hieu_biet", "cau_hoi", "vong", "niem_phong")


class LoiSoCai(RuntimeError):
    pass


def thu_muc_mac_dinh() -> Path:
    return Path(os.environ.get("NC_SO_CAI") or (LAB / "so_cai")) / "nc"


def _hash(hang: dict) -> str:
    return hashlib.sha1(json.dumps(hang, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _doc_dong(f: Path):
    """Moi dong hop le cua file; dong cut do (may sap giua luc ghi) bi bo qua, khong lam hong ca file."""
    if not f.exists():
        return
    with f.open(encoding="utf-8", errors="replace") as g:
        for ln in g:
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            if isinstance(d, dict) and isinstance(d.get("r"), dict) and "id" in d["r"]:
                yield d


def _cuoi(f: Path) -> dict:
    """{id: (hash, hang)} - ban chup CUOI cua tung id."""
    ra = {}
    for d in _doc_dong(f):
        ra[d["r"]["id"]] = (d.get("h"), d["r"])
    return ra


def xuat(db: Path | str | None = None, dich: Path | str | None = None) -> dict:
    """nc.db -> so cai (chi them). Tra {bang: so_dong_moi}. Khong co DB thi khong lam gi."""
    p = Path(db or ST.DB)
    if not p.exists() or p.stat().st_size == 0:
        return {b: 0 for b in BANG}
    thu = Path(dich or thu_muc_mac_dinh())
    thu.mkdir(parents=True, exist_ok=True)
    ra = {}
    # Ket noi THUONG + query_only (khong dung `mode=ro`): DB o che do WAL, `mode=ro` can file -shm san co va se hong
    # khi tien trinh khac vua dong; query_only van chan moi lenh ghi.
    cn = sqlite3.connect(str(p), timeout=30.0)
    cn.row_factory = sqlite3.Row
    try:
        cn.execute("PRAGMA query_only=ON")
        co = {r[0] for r in cn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for bang in BANG:
            if bang not in co:
                ra[bang] = 0
                continue
            f = thu / ("%s.jsonl" % bang)
            truoc = _cuoi(f)
            moi = []
            for r in cn.execute("SELECT * FROM %s ORDER BY id" % bang):
                hang = {k: r[k] for k in r.keys()}
                h = _hash(hang)
                if truoc.get(hang["id"], (None,))[0] != h:
                    moi.append(json.dumps({"h": h, "r": hang}, ensure_ascii=False, sort_keys=True, default=str))
            if moi:
                with f.open("a", encoding="utf-8", newline="\n") as g:
                    g.write("\n".join(moi) + "\n")
            ra[bang] = len(moi)
    finally:
        cn.close()
    return ra


def nhap(nguon: Path | str | None = None, db: Path | str | None = None, ghi_de: bool = False) -> dict:
    """so cai -> nc.db. Chi khi nc.db RONG (tru `ghi_de`): nhap de len so dang co la tron hai lich su. Tra {bang: so_hang}."""
    thu = Path(nguon or thu_muc_mac_dinh())
    if not thu.is_dir():
        raise LoiSoCai("khong co so cai o %s (b cau lay truoc?)" % thu)
    cu = ST.DB
    if db:
        ST.DB = Path(db)
    try:
        with ST.ket_noi() as cn:
            dem = {b: cn.execute("SELECT COUNT(*) FROM %s" % b).fetchone()[0] for b in BANG}
            if any(dem.values()) and not ghi_de:
                raise LoiSoCai("nc.db KHONG rong (%s) - nhap de len se tron hai lich su; dung --ghi-de neu co chu y"
                               % ", ".join("%s=%d" % (b, n) for b, n in dem.items() if n))
            ra = {}
            for bang in BANG:
                cot = [r[1] for r in cn.execute("PRAGMA table_info(%s)" % bang)]
                n = 0
                for _, (_h, hang) in sorted(_cuoi(thu / ("%s.jsonl" % bang)).items()):
                    k = [c for c in cot if c in hang]
                    cn.execute("INSERT OR REPLACE INTO %s(%s) VALUES(%s)" % (bang, ",".join(k), ",".join("?" * len(k))),
                               [hang[c] for c in k])
                    n += 1
                ra[bang] = n
        return ra
    finally:
        ST.DB = cu


def tom_tat(nguon: Path | str | None = None) -> dict:
    thu = Path(nguon or thu_muc_mac_dinh())
    return {b: len(_cuoi(thu / ("%s.jsonl" % b))) for b in BANG}


def main(argv: list[str]) -> int:
    lenh = argv[0] if argv else "so-cai"
    try:
        if lenh == "xuat":
            print(json.dumps(xuat(), ensure_ascii=False))
        elif lenh == "nhap":
            print(json.dumps(nhap(ghi_de="--ghi-de" in argv), ensure_ascii=False))
        else:
            print(json.dumps(tom_tat(), ensure_ascii=False))
    except LoiSoCai as e:
        print("LOI: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
