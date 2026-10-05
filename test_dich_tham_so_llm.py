# -*- coding: utf-8 -*-
"""Test cho nhan/dich_tham_so.py - chi doc nhung gi co that trong ma."""
import math

import numpy as np

from nhan import dich_tham_so as D
from nhan import luoi as LU


def test_thieu_lop_rong_voi_ThamSo_hien_tai():
    # Luat mot-lop: moi truong cua luoi.ThamSo phai co lop, va khong lop nao tro vao truong khong ton tai.
    assert D.thieu_lop() == []


def test_LOP_THAM_SO_LUOI_tro_dung_lop_hop_le():
    for truong, lop in D.LOP_THAM_SO_LUOI.items():
        assert lop in D.LOP, (truong, lop)


def test_MO_TA_LOP_phu_het_LOP():
    assert set(D.MO_TA_LOP) == set(D.LOP)


def test_hop_le_tra_False_voi_so_am_va_nan():
    assert D._hop_le(1.0) is True
    assert D._hop_le(0.0) is False
    assert D._hop_le(-1.0) is False
    assert D._hop_le(float("nan")) is False
    assert D._hop_le(float("inf")) is False
    assert D._hop_le(None) is False


def test_kiem_thi_truong_rong_khi_moi_truong_duong():
    tt = D.ThiTruong(ma="X", khung_phut=60.0, A=1.0, C=0.1, pip=0.0001, pv=100000.0, von=1000.0)
    assert D.kiem_thi_truong(tt) == []


def test_kiem_thi_truong_bao_khi_A_am_va_C_bang_khong():
    tt = D.ThiTruong(ma="X", khung_phut=60.0, A=-1.0, C=0.0, pip=0.0001, pv=100000.0, von=1000.0)
    loi = D.kiem_thi_truong(tt)
    assert any("A" in s for s in loi)
    assert any("C" in s for s in loi)


def test_ThiTruong_point_mac_dinh_bang_pip_chia_10():
    tt = D.ThiTruong(ma="X", khung_phut=60.0, A=1.0, C=0.1, pip=0.0001, pv=100000.0, von=1000.0)
    assert math.isclose(tt.point, 0.0001 / 10.0)


def test_do_sau_tra_None_khi_khong_co_gia():
    tt = D.ThiTruong(ma="X", khung_phut=60.0, A=1.0, C=0.1, pip=0.0001, pv=100000.0, von=1000.0)
    assert tt.do_sau(10, 0.9) is None


def test_do_sau_tra_None_khi_chuoi_qua_ngan():
    n = 50
    hi = np.linspace(1.0, 1.1, n)
    lo = np.linspace(0.9, 1.0, n)
    cl = np.linspace(0.95, 1.05, n)
    tt = D.ThiTruong(ma="X", khung_phut=60.0, A=1.0, C=0.1, pip=0.0001, pv=100000.0, von=1000.0, gia=(hi, lo, cl))
    # H + 200 > n nen khong tinh duoc
    assert tt.do_sau(10, 0.9) is None


def test_do_sau_tra_so_duong_khi_du_du_lieu():
    n = 400
    rng = np.random.default_rng(0)
    cl = 1.0 + np.cumsum(rng.normal(0.0, 0.001, n))
    hi = cl + 0.001
    lo = cl - 0.001
    tt = D.ThiTruong(ma="X", khung_phut=60.0, A=1.0, C=0.1, pip=0.0001, pv=100000.0, von=1000.0, gia=(hi, lo, cl))
    e = tt.do_sau(10, 0.9)
    assert e is not None
    assert e >= 0.0


def test_la_cung_thi_truong_khi_cung_hang_so_va_khong_co_gia():
    a = D.ThiTruong(ma="X", khung_phut=60.0, A=1.0, C=0.1, pip=0.0001, pv=100000.0, von=1000.0)
    b = D.ThiTruong(ma="Y", khung_phut=60.0, A=1.0, C=0.1, pip=0.0001, pv=100000.0, von=1000.0)
    assert D._la_cung_thi_truong(a, b) is True


def test_la_cung_thi_truong_khac_khi_A_khac():
    a = D.ThiTruong(ma="X", khung_phut=60.0, A=1.0, C=0.1, pip=0.0001, pv=100000.0, von=1000.0)
    b = D.ThiTruong(ma="X", khung_phut=60.0, A=2.0, C=0.1, pip=0.0001, pv=100000.0, von=1000.0)
    assert D._la_cung_thi_truong(a, b) is False


def test_tom_tat_tra_cac_khoa_co_ban():
    tt = D.ThiTruong(ma="X", khung_phut=60.0, A=0.001, C=0.0001, pip=0.0001, pv=100000.0, von=1000.0)
    t = tt.tom_tat()
    assert t["ma"] == "X"
    assert math.isclose(t["A_pip"], 10.0)
    assert math.isclose(t["C_pip"], 1.0)
    assert math.isclose(t["C_tren_A"], 0.1)
