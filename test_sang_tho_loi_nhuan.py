# -*- coding: utf-8 -*-
"""Sang tho cua quantlab theo BA yeu to cot loi (18/10/2026).

Truoc 18/10, cong (che do "loi_nhuan") da bo dieu kien "thang mua-giu" nhung sang tho o `quantlab.kham_pha` van
doi he thang mua-giu CA tong lai LAN Sharpe tren train -> he co lai bi loai TRUOC khi toi cong.
"""
from unittest import mock

from nhan import cong as CONG
from tru import quantlab as QL

BH = {"tong_lai_pct": 300.0, "sharpe": 1.5}


def _cs(cagr, dd, tong=None, sharpe=0.3):
    return {"cagr_pct": cagr, "max_dd_pct": -abs(dd), "tong_lai_pct": cagr * 5 if tong is None else tong,
            "sharpe": sharpe}


def test_dat_cot_loi_dung_mot_cong_thuc_voi_cong():
    assert CONG.dat_cot_loi(_cs(5, 30)) and not CONG.dat_cot_loi(_cs(5, 50))
    assert CONG.dat_cot_loi(_cs(40, 120))          # giam lot duoc
    assert not CONG.dat_cot_loi(_cs(-1, 10))
    assert CONG.ti_so_cot_loi(_cs(10, 20)) == 0.5


def test_loi_nhuan_he_thua_mua_giu_van_qua_sang_tho():
    with mock.patch.object(CONG, "che_do_cong", return_value="loi_nhuan"):
        assert QL._qua_sang_tho(_cs(8, 40), BH, so_lenh=50)          # thua mua-giu xa, van dat cot loi
        assert not QL._qua_sang_tho(_cs(5, 50), BH, so_lenh=50)      # lai qua mong so voi sut giam
        assert not QL._qua_sang_tho(_cs(8, 40, tong=-1), BH, so_lenh=50)
        assert not QL._qua_sang_tho(_cs(8, 40), BH, so_lenh=QL.SO_LENH_SANG_THO_LOI_NHUAN - 1)
        assert QL._toi_da_dang_ky() == QL.TOI_DA_DANG_KY_MOI_CAP_LOI_NHUAN


def test_loi_nhuan_xep_theo_lai_tren_sut_giam_khong_theo_sharpe():
    with mock.patch.object(CONG, "che_do_cong", return_value="loi_nhuan"):
        a, b = _cs(20, 20, sharpe=0.5), _cs(10, 40, sharpe=1.2)
        assert QL._diem_xep(a) > QL._diem_xep(b)


def test_che_do_cu_giu_nguyen_doi_thang_mua_giu():
    with mock.patch.object(CONG, "che_do_cong", return_value="nhan"):
        assert not QL._qua_sang_tho(_cs(8, 40), BH, so_lenh=50)
        assert QL._qua_sang_tho(_cs(80, 40, tong=400, sharpe=2.0), BH, so_lenh=50)
        assert QL._toi_da_dang_ky() == QL.TOI_DA_DANG_KY_MOI_CAP
        assert QL._diem_xep(_cs(1, 1, sharpe=1.7)) == 1.7
