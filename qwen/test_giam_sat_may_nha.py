# -*- coding: utf-8 -*-
from nhan import giam_sat_may_nha as G


def test_xong_gia_phat_hien_loi_trong_dat():
    assert G.xong_gia({"trang_thai": "DAT", "bang_chung": {"dong_cuoi": ["FileNotFoundError: khong co du lieu"]}})
    assert G.xong_gia({"trang_thai": "DAT", "bang_chung": {"dong_cuoi": ['"co_lai": true']}}) is None
    assert G.xong_gia({"trang_thai": "AM", "bang_chung": {"dong_cuoi": ["Error:"]}}) is None


def test_hanh_dong_bao_het_viec_va_bo_chet():
    k = {"nhip_tim": [{"ten": "a", "song": False, "den": None}, {"ten": "b", "song": True, "den": None}],
         "gio_viec_con": 3, "xong_gia_1h": [], "dang_ket": []}
    h = " ".join(G.hanh_dong(k))
    assert "a" in h and "giao them" in h


def test_hanh_dong_bao_xong_gia_theo_nhom_va_dung_gio_dong_ho():
    k = {"nhip_tim": [{"ten": "a", "song": True, "den": None}], "gio_viec_con": 90, "gio_dong_ho": 4, "xong_gia_1h": [], "dang_ket": [],
         "xong_gia_nhom": {"sua_duoc": 25, "can_chan_doan": 24, "khong_chay_lai": 31}}
    h = " ".join(G.hanh_dong(k))
    assert "giao them" in h and "dua-lai" in h and "mo log tester" in h and "thieu du lieu gia" in h
