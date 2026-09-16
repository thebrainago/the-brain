# -*- coding: utf-8 -*-
"""Test G2-B: ghi theo lo, thu lai khi khoa ban, va KHONG nuot loi that.

Bai quan trong nhat la `test_loi_that_khong_bi_nuot`: mot bo thu lai bat qua
rong se bien "sai cot" thanh "thu 6 lan roi bao khoa ban" - tuc bao sai nguyen
nhan, dung kieu hong ma du an nay da dinh nhieu lan.
"""
from __future__ import annotations

import multiprocessing as mp
import sqlite3
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import pytest  # noqa: E402

from nhan import so as SO  # noqa: E402


@pytest.fixture
def db(tmp_path, monkeypatch):
    d = tmp_path / "thu.db"
    monkeypatch.setattr(SO, "DB", d)
    with SO.ket_noi() as cn:
        cn.execute("CREATE TABLE t(i INTEGER, ai TEXT)")
    return d


def test_ghi_lo_la_MOT_giao_dich(db):
    with SO.ghi_lo() as cn:
        for i in range(500):
            cn.execute("INSERT INTO t(i, ai) VALUES(?, ?)", (i, "lo"))
    assert SO.mot("SELECT COUNT(*) c FROM t")["c"] == 500


def test_ghi_lo_that_bai_thi_LUI_HET(db):
    with pytest.raises(ValueError):
        with SO.ghi_lo() as cn:
            cn.execute("INSERT INTO t(i, ai) VALUES(1, 'a')")
            raise ValueError("hong giua chung")
    assert SO.mot("SELECT COUNT(*) c FROM t")["c"] == 0, \
        "mot lo hong phai lui HET, khong de lai nua chung"


def test_nhan_ra_khoa_ban():
    assert SO._ban(sqlite3.OperationalError("database is locked"))
    assert SO._ban(sqlite3.OperationalError("database is busy"))


def test_loi_that_khong_bi_nuot():
    """Sai cot KHONG duoc coi la 'cho luot'."""
    assert not SO._ban(sqlite3.OperationalError("no such column: xyz"))
    assert not SO._ban(ValueError("database is locked"))  # dung kieu loi


def test_thu_lai_roi_thanh_cong():
    n = {"lan": 0}

    def hay_hong():
        n["lan"] += 1
        if n["lan"] < 3:
            raise sqlite3.OperationalError("database is locked")
        return "xong"
    assert SO.thu_lai(hay_hong) == "xong"
    assert n["lan"] == 3


def test_thu_lai_khong_lap_voi_loi_that():
    n = {"lan": 0}

    def hong_that():
        n["lan"] += 1
        raise sqlite3.OperationalError("no such table: khong_co")
    with pytest.raises(sqlite3.OperationalError):
        SO.thu_lai(hong_that)
    assert n["lan"] == 1, "loi that phai nem NGAY, khong thu lai 6 lan"


def _tho(duong_dan, moc):
    """Tien trinh con: ghi 50 dong bang mot lo."""
    sys.path.insert(0, str(Path(duong_dan).parent))
    from nhan import so as S
    S.DB = Path(duong_dan)
    with S.ghi_lo() as cn:
        for i in range(50):
            cn.execute("INSERT INTO t(i, ai) VALUES(?, ?)", (i, str(moc)))
    return 0


@pytest.mark.skipif(sys.platform == "win32" and sys.version_info < (3, 8),
                    reason="spawn")
def test_nam_tien_trinh_ghi_cung_luc_khong_mat_dong(db):
    """Nam luong ghi dong thoi -> du 250 dong, khong loi khoa.

    Day la phep thu ma bang ke hoach doi: khong mat dong, khong nem
    `database is locked` ra ngoai.
    """
    ps = [mp.Process(target=_tho, args=(str(db), k)) for k in range(5)]
    t0 = time.time()
    for p in ps:
        p.start()
    for p in ps:
        p.join(120)
    assert all(p.exitcode == 0 for p in ps), \
        "co tien trinh chet: %s" % [p.exitcode for p in ps]
    assert SO.mot("SELECT COUNT(*) c FROM t")["c"] == 250
    assert len(SO.nhieu("SELECT DISTINCT ai FROM t")) == 5
    assert time.time() - t0 < 120


def test_diem_tra_wal_tra_ve_kich_thuoc(db):
    with SO.ghi_lo() as cn:
        cn.execute("INSERT INTO t(i, ai) VALUES(1, 'a')")
    r = SO.diem_tra_wal()
    assert "wal_mb" in r and r["wal_mb"] >= 0


def test_do_trang_trong_tra_du_khoa(db):
    with SO.ghi_lo() as cn:
        for i in range(200):
            cn.execute("INSERT INTO t(i, ai) VALUES(?, 'x')", (i,))
    d = SO.do_trang_trong()
    for k in ("trang", "trang_trong", "gb", "gb_trong", "gb_that", "ty_le_trong"):
        assert k in d
    assert d["gb_that"] <= d["gb"] and 0.0 <= d["ty_le_trong"] <= 1.0


def test_nen_gon_khong_dong_vao_ban_goc(db, tmp_path):
    with SO.ghi_lo() as cn:
        for i in range(300):
            cn.execute("INSERT INTO t(i, ai) VALUES(?, 'x')", (i,))
    truoc = db.stat().st_size
    r = SO.nen_gon(tmp_path / "gon.db", in_ra=None)
    assert db.stat().st_size == truoc, "VACUUM INTO khong duoc dong vao nguon"
    assert (tmp_path / "gon.db").exists()
    assert SO.mot("SELECT COUNT(*) c FROM t")["c"] == 300


def test_nen_gon_tu_choi_ghi_de(db, tmp_path):
    d = tmp_path / "da_co.db"
    d.write_text("x", encoding="utf-8")
    with pytest.raises(FileExistsError):
        SO.nen_gon(d, in_ra=None)
