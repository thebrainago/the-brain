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
