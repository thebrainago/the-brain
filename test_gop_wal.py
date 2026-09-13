# -*- coding: utf-8 -*-
"""test_gop_wal.py - cai phanh cho mot kieu day dia lang le.

Module `gop_wal.py` ra doi 12/09/2026 sau khi `nao.db-wal` phinh len 1,4 GB va
lam o C con 177 MB. Nhung no **chua co bai kiem nao** cho toi 13/09 - va dung
ngay 13/09 ca ho su co do lap lai o quy mo lon hon: dia ve 233 MB, pytest chet
vi paging, va kho co che bi ghi de HAI lan.

Nen file nay gac hai thu, va ca hai deu la nhung dieu chinh docstring cua
module do da canh bao:

  1. **BUSY khong duoc doc thanh XONG.** Mot lenh don dep bao "xong" ma khong
     don gi thi nguy hiem hon khong co lenh don dep.
  2. **Khong co file thi phai noi khong co**, khong duoc tra ve mot bang so
     0 MB doc y het "da gop, khong co gi de gop".
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import gop_wal as GW  # noqa: E402


def _db_co_wal(tmp_path: Path) -> Path:
    """Mot db THAT o che do WAL, co san du lieu chua checkpoint."""
    db = tmp_path / "thu.db"
    cn = sqlite3.connect(str(db))
    cn.execute("PRAGMA journal_mode=WAL")
    cn.execute("CREATE TABLE t(a TEXT)")
    cn.executemany("INSERT INTO t VALUES(?)", [("x" * 500,)] * 2000)
    cn.commit()
    cn.close()
    return db


def test_gop_that_lam_wal_nho_di(tmp_path):
    """Lay mot thu chac chan CO ra thu truoc khi tin bat ky bao cao nao."""
    db = _db_co_wal(tmp_path)
    wal = db.with_name(db.name + "-wal")
    # Mo lai de WAL co noi dung chua checkpoint.
    cn = sqlite3.connect(str(db))
    cn.execute("PRAGMA journal_mode=WAL")
    cn.executemany("INSERT INTO t VALUES(?)", [("y" * 500,)] * 2000)
    cn.commit()
    truoc = wal.stat().st_size if wal.exists() else 0
    cn.close()
    assert truoc > 0, "bo do mu: chua tao duoc WAL nao de gop"

    r = GW.gop_mot(db, in_ra=lambda *a: None)
    assert r.get("busy") is False
    assert r["sau_mb"] <= r["truoc_mb"]


def test_BUSY_khong_duoc_doc_thanh_XONG(tmp_path):
    """Con ket noi khac dang mo -> phai bao BUSY, khong bao da gop.

    `PRAGMA wal_checkpoint(TRUNCATE)` tra `(1, -1, -1)` khi busy. Neu ham nuot
    con so do va tra ve mot bang "0 MB", nguoi doc se ket luan "khong con gi
    de gop" trong khi WAL van 1,4 GB nam do.
    """
    db = _db_co_wal(tmp_path)
    giu = sqlite3.connect(str(db))
    giu.execute("PRAGMA journal_mode=WAL")
    giu.execute("BEGIN IMMEDIATE")
    giu.execute("INSERT INTO t VALUES('giu khoa')")
    try:
        r = GW.gop_mot(db, in_ra=lambda *a: None)
        # Hoac bao BUSY, hoac bao LOI - mien la KHONG bao mot ket qua sach se.
        assert r.get("busy") or r.get("loi"), \
            "gop khi dang bi giu khoa ma van bao xong - day la bao cao gia"
    finally:
        giu.rollback()
        giu.close()


def test_khong_co_db_thi_noi_khong_co(tmp_path):
    r = GW.gop_mot(tmp_path / "khong_ton_tai.db", in_ra=lambda *a: None)
    assert "bo" in r, "db khong ton tai ma tra ve bang so -> doc thanh 'da gop'"
    assert "giai_phong_mb" not in r


def test_gop_het_tra_ve_tong(tmp_path, monkeypatch):
    monkeypatch.setattr(GW, "LAB", tmp_path)
    _db_co_wal(tmp_path)
    r = GW.gop_het(in_ra=lambda *a: None)
    assert isinstance(r["giai_phong_mb"], int)
    assert len(r["db"]) >= 1


def test_mb_khong_no_khi_file_vang(tmp_path):
    assert GW._mb(tmp_path / "khong_co") == 0
