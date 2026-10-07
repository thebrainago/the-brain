# -*- coding: utf-8 -*-
"""Test cho module hang_doi. Chay bang cach goi tung ham test_*()."""
from __future__ import annotations

import json
import time

from nhan import so as SO
from nhan import hang_doi as HD


def _don_sach():
    """Xoa bang de moi test bat dau tu trang thai trong."""
    with SO.ket_noi() as cn:
        cn.execute("DROP TABLE IF EXISTS viec_quantlab")
    HD._DA_TAO = False


def _viec(ts="A", khung="1d", template="t1"):
    return {"tai_san": ts, "khung": khung, "template": template,
            "tham_so": {"a": 1}}


def test_van_tay_on_dinh_voi_thu_tu_khoa():
    """tham_so sap khoa -> cung van tay du thu tu dict khac nhau."""
    v1 = HD.van_tay("noi_sinh", "A", "1d", "t1", {"x": 1, "y": 2})
    v2 = HD.van_tay("noi_sinh", "A", "1d", "t1", {"y": 2, "x": 1})
    assert v1 == v2
    assert isinstance(v1, str) and len(v1) == 64


def test_van_tay_khac_khi_doi_nguon():
    v1 = HD.van_tay("noi_sinh", "A", "1d", "t1", {})
    v2 = HD.van_tay("ngoai_sinh", "A", "1d", "t1", {})
    assert v1 != v2


def test_nap_idempotent_khong_sinh_ban_trung():
    _don_sach()
    r1 = HD.nap([_viec(), _viec()], "noi_sinh")
    assert r1["them"] == 1
    assert r1["da_co"] == 1
    r2 = HD.nap([_viec()], "noi_sinh")
    assert r2["them"] == 0
    assert r2["da_co"] == 1


def test_nap_danh_sach_rong():
    _don_sach()
    r = HD.nap([], "noi_sinh")
    assert r["them"] == 0
    assert r["da_co"] == 0


def test_uu_tien_mac_dinh_theo_nguon():
    _don_sach()
    r = HD.nap([_viec()], "ngoai_sinh")
    assert r["uu_tien"] == HD.UU_TIEN["ngoai_sinh"]
    r2 = HD.nap([_viec(ts="B")], "noi_sinh")
    assert r2["uu_tien"] == HD.UU_TIEN["noi_sinh"]


def test_uu_tien_ngoai_sinh_nho_hon_noi_sinh():
    """So nho = uu tien cao -> ngoai_sinh phai nho hon noi_sinh."""
    assert HD.UU_TIEN["ngoai_sinh"] < HD.UU_TIEN["noi_sinh"]


def test_nhan_viec_tra_ve_va_danh_dau_dang_lam():
    _don_sach()
    HD.nap([_viec()], "noi_sinh")
    ra = HD.nhan_viec("w1", so_luong=1)
    assert len(ra) == 1
    assert ra[0]["trang_thai"] == "DANG_LAM"
    assert ra[0]["worker"] == "w1"
    assert ra[0]["so_lan_thu"] == 1
    assert ra[0]["tham_so"] == {"a": 1}


def test_nhan_viec_uu_tien_ngoai_sinh_truoc():
    _don_sach()
    HD.nap([_viec(ts="NOI")], "noi_sinh")
    HD.nap([_viec(ts="NGOAI")], "ngoai_sinh")
    ra = HD.nhan_viec("w1", so_luong=1)
    assert len(ra) == 1
    assert ra[0]["tai_san"] == "NGOAI"


def test_nhan_viec_loc_theo_nguon():
    _don_sach()
    HD.nap([_viec(ts="NOI")], "noi_sinh")
    HD.nap([_viec(ts="NGOAI")], "ngoai_sinh")
    ra = HD.nhan_viec("w1", so_luong=5, nguon="noi_sinh")
    assert len(ra) == 1
    assert ra[0]["nguon"] == "noi_sinh"


def test_nhan_viec_khi_hang_rong():
    _don_sach()
    ra = HD.nhan_viec("w1", so_luong=3)
    assert ra == []


def test_xong_danh_dau_trang_thai():
    _don_sach()
    HD.nap([_viec()], "noi_sinh")
    ra = HD.nhan_viec("w1", so_luong=1)
    vid = ra[0]["id"]
    HD.xong(vid, {"kq": 42})
    with SO.ket_noi() as cn:
        r = cn.execute("SELECT trang_thai, ket_qua FROM viec_quantlab "
                       "WHERE id=?", (vid,)).fetchone()
    assert r["trang_thai"] == "XONG"
    assert json.loads(r["ket_qua"]) == {"kq": 42}


def test_that_bai_qua_so_lan_thi_thanh_HONG():
    _don_sach()
    HD.nap([_viec()], "noi_sinh")
    # Thu TOI_DA_THU lan: moi lan nhan roi that bai
    for _ in range(HD.TOI_DA_THU):
        ra = HD.nhan_viec("w1", so_luong=1)
        assert len(ra) == 1
        HD.that_bai(ra[0]["id"], "loi thu")
    with SO.ket_noi() as cn:
        r = cn.execute("SELECT trang_thai FROM viec_quantlab").fetchone()
    assert r["trang_thai"] == "HONG"
    # Sau khi HONG, khong con nhan duoc nua
    assert HD.nhan_viec("w1", so_luong=1) == []


def test_lease_qua_han_duoc_tra_ve_CHO():
    _don_sach()
    HD.nap([_viec()], "noi_sinh")
    ra = HD.nhan_viec("w1", so_luong=1, han_lease=-1.0)
    assert len(ra) == 1
    # het_han da qua -> lan nhan tiep theo phai tra ve CHO roi gianh lai
    ra2 = HD.nhan_viec("w2", so_luong=1)
    assert len(ra2) == 1
    assert ra2[0]["worker"] == "w2"


def test_trang_thai_dem_theo_nguon():
    _don_sach()
    HD.nap([_viec(ts="A"), _viec(ts="B")], "noi_sinh")
    HD.nap([_viec(ts="C")], "ngoai_sinh")
    tt = HD.trang_thai()
    assert tt["theo_nguon"]["noi_sinh"]["CHO"] == 2
    assert tt["theo_nguon"]["ngoai_sinh"]["CHO"] == 1
    assert tt["tong"]["CHO"] == 3
    assert tt["lease_qua_han"] == 0


def test_don_lease_treo_tra_ve_so_viec():
    _don_sach()
    HD.nap([_viec()], "noi_sinh")
    HD.nhan_viec("w1", so_luong=1, han_lease=-1.0)
    n = HD.don_lease_treo()
    assert n == 1
    # Sau khi don, viec da ve CHO
    tt = HD.trang_thai()
    assert tt["tong"].get("CHO", 0) == 1
    assert tt["lease_qua_han"] == 0
