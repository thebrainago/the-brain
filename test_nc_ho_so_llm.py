# -*- coding: utf-8 -*-
"""Test cho nhan/nc_ho_so.py - chi kiem hanh vi that thay trong ma."""
from __future__ import annotations

import tempfile
from pathlib import Path

from nhan import nc_ho_so as NC


# --------------------------------------------------------------------------------------------------- _ascii / _o / _cat
def test_ascii_bo_dau_va_giu_chu():
    assert NC._ascii("Ho so BOT") == "Ho so BOT"
    assert NC._ascii("dau") == "dau"


def test_o_thay_pipe_va_gop_khoang_trang():
    assert NC._o("a|b") == "a/b"
    assert NC._o("  a   b  ") == "a b"


def test_cat_ngan_khong_doi():
    assert NC._cat("abc", 10) == "abc"


def test_cat_dai_them_dau_biet():
    s = NC._cat("x" * 100, 10)
    assert len(s) <= 10
    assert s.endswith("...")


# --------------------------------------------------------------------------------------------------- _ten_tu_tep / _ten_sach
def test_ten_tu_tep_bo_duoi():
    assert NC._ten_tu_tep(Path("tester_vamge10k_kp_deals.csv.gz")) == "tester_vamge10k_kp_deals"


def test_ten_sach_thay_ky_tu_la():
    assert NC._ten_sach("a b/c") == "a_b_c"


def test_ten_sach_rong_tra_bot():
    assert NC._ten_sach("") == "bot"


# --------------------------------------------------------------------------------------------------- _duong
def test_duong_tu_choi_chuoi_rong():
    try:
        NC._duong("", "lenh")
        assert False, "phai loi"
    except ValueError:
        pass


def test_duong_tu_choi_ngoai_thu_muc_du_an():
    try:
        NC._duong("/etc/hosts", "lenh")
        assert False, "phai loi"
    except ValueError:
        pass


def test_duong_tu_choi_khong_phai_chuoi():
    try:
        NC._duong(123, "lenh")
        assert False, "phai loi"
    except ValueError:
        pass


# --------------------------------------------------------------------------------------------------- _cat_tep
def test_cat_tep_ngan_giu_nguyen():
    s = "a\nb\n"
    assert NC._cat_tep(s) == s


def test_cat_tep_dai_bi_cat_va_co_ghi_chu():
    s = ("dong\n" * 20000)
    ra = NC._cat_tep(s)
    assert len(ra) <= NC.TEP_TOI_DA
    assert "cat bot" in ra


# --------------------------------------------------------------------------------------------------- _viet
def test_viet_tao_tep_trong_thu_muc_ho_so():
    goc = NC.THU_MUC
    with tempfile.TemporaryDirectory() as td:
        NC.THU_MUC = Path(td)
        try:
            p = NC._viet("x.md", "noi dung\n")
            assert Path(td, "x.md").is_file()
            assert p == "x.md"
        finally:
            NC.THU_MUC = goc


# --------------------------------------------------------------------------------------------------- chay: kiem tra tham so
def test_chay_them_co_khoa_la_thi_loi():
    try:
        NC.chay("reports/fixture/tester_vamge10k_kp_deals.csv.gz", them=[{"lenh": "x", "sai": 1}])
        assert False, "phai loi"
    except ValueError:
        pass


def test_chay_qua_nhieu_cap_thi_loi():
    them = [{"lenh": "reports/fixture/tester_vamge10k_kp_deals.csv.gz"}] * NC.TOI_DA_CAP
    try:
        NC.chay("reports/fixture/tester_vamge10k_kp_deals.csv.gz", them=them)
        assert False, "phai loi"
    except ValueError:
        pass


def test_chay_he_so_don_vi_khong_hop_le_thi_loi():
    try:
        NC.chay("reports/fixture/tester_vamge10k_kp_deals.csv.gz", he_so_don_vi=-1)
        assert False, "phai loi"
    except ValueError:
        pass


def test_chay_them_khong_phai_dict_thi_loi():
    try:
        NC.chay("reports/fixture/tester_vamge10k_kp_deals.csv.gz", them=[1, 2])
        assert False, "phai loi"
    except ValueError:
        pass
