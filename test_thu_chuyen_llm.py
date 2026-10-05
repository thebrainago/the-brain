# -*- coding: utf-8 -*-
"""Test cho `nhan.thu_chuyen` (phan doc duoc trong tep)."""
import math

import numpy as np
import pandas as pd

from nhan import thu_chuyen as TC


# ------------------------------------------------------------------------------------------------------ hat_on_dinh
def test_hat_on_dinh_on_dinh_va_khac_nhau():
    tg = TC.TheGioi()
    a = TC.hat_on_dinh(tg, "A", 0)
    b = TC.hat_on_dinh(tg, "A", 0)
    c = TC.hat_on_dinh(tg, "A", 1)
    d = TC.hat_on_dinh(tg, "B", 0)
    assert a == b
    assert a != c
    assert a != d
    assert 0 <= a <= 0x7FFFFFFF


def test_hat_on_dinh_doi_the_gioi_thi_doi_hat():
    tg1 = TC.TheGioi()
    tg2 = tg1.doi(sigma_pip=60.0)
    assert TC.hat_on_dinh(tg1, "A", 0) != TC.hat_on_dinh(tg2, "A", 0)


# ------------------------------------------------------------------------------------------------------ TheGioi.doi
def test_the_gioi_doi_giu_nguyen_truong_khong_doi():
    tg = TC.TheGioi(sigma_pip=30.0, nua_doi_phut=240.0, troi_nam=15.0, chi_phi_pip=10.0, hoi_quy=True)
    tg2 = tg.doi(sigma_pip=60.0)
    assert tg2.sigma_pip == 60.0
    assert tg2.nua_doi_phut == tg.nua_doi_phut
    assert tg2.troi_nam == tg.troi_nam
    assert tg2.chi_phi_pip == tg.chi_phi_pip
    assert tg2.hoi_quy == tg.hoi_quy
    assert tg.sigma_pip == 30.0  # khong sua goc


# ------------------------------------------------------------------------------------------------------ gop_khung
def test_gop_khung_k1_tra_nguyen():
    df = pd.DataFrame({"open": [1.0, 2.0, 3.0], "high": [1.5, 2.5, 3.5], "low": [0.5, 1.5, 2.5],
                       "close": [1.2, 2.2, 3.2], "spread": [0.1, 0.1, 0.1]})
    out = TC.gop_khung(df, 1)
    assert out is df


def test_gop_khung_gop_dung_ohlc():
    df = pd.DataFrame({"open": [1.0, 2.0, 3.0, 4.0], "high": [1.5, 2.5, 3.5, 4.5], "low": [0.5, 1.5, 2.5, 3.5],
                       "close": [1.2, 2.2, 3.2, 4.2], "spread": [0.1, 0.2, 0.3, 0.4]})
    out = TC.gop_khung(df, 2)
    assert len(out) == 2
    assert out["open"].tolist() == [1.0, 3.0]
    assert out["high"].tolist() == [2.5, 4.5]
    assert out["low"].tolist() == [0.5, 2.5]
    assert out["close"].tolist() == [2.2, 4.2]
    assert out["spread"].tolist() == [0.1, 0.3]


def test_gop_khung_bo_phan_du():
    df = pd.DataFrame({"open": [1.0, 2.0, 3.0], "high": [1.5, 2.5, 3.5], "low": [0.5, 1.5, 2.5],
                       "close": [1.2, 2.2, 3.2], "spread": [0.1, 0.1, 0.1]})
    out = TC.gop_khung(df, 2)
    assert len(out) == 1
    assert out["close"].tolist() == [2.2]


# ------------------------------------------------------------------------------------------------------ bien_do
def test_bien_do_nen_pip_trung_vi():
    df = pd.DataFrame({"high": [1.0, 2.0, 3.0], "low": [0.0, 1.0, 2.0]})
    # bien do = 1.0 moi nen -> 1.0 / PIP = 10000 pip
    assert TC.bien_do_nen_pip(df) == 1.0 / TC.PIP


def test_bien_do_ngang_pip_cua_so_lon_hon_nen():
    df = pd.DataFrame({"high": [1.0, 2.0, 3.0, 4.0], "low": [0.0, 1.0, 2.0, 3.0]})
    # cua so 2 nen: (2-0)=2, (3-1)=2, (4-2)=2 -> trung vi 2.0
    r = TC.bien_do_ngang_pip(df, gio_phut=2.0, khung_phut=1.0)
    assert abs(r - 2.0 / TC.PIP) < 1e-9


# ------------------------------------------------------------------------------------------------------ hoi_tuong_doi
def test_hoi_tuong_doi_bang_khong_khi_bang_dap_an():
    assert TC.hoi_tuong_doi(10.0, 10.0) == 0.0


def test_hoi_tuong_doi_am_khi_tot_hon_dap_an():
    assert TC.hoi_tuong_doi(10.0, 20.0) == -1.0


def test_hoi_tuong_doi_none_khi_dap_an_khong_duong():
    assert TC.hoi_tuong_doi(0.0, 5.0) is None
    assert TC.hoi_tuong_doi(-3.0, 5.0) is None


def test_hoi_tuong_doi_none_khi_diem_khong_huu_han():
    assert TC.hoi_tuong_doi(10.0, float("nan")) is None
    assert TC.hoi_tuong_doi(10.0, float("inf")) is None


# ------------------------------------------------------------------------------------------------------ luoi_o_dap_an
def test_luoi_o_dap_an_loc_theo_san_pip():
    kieu = TC.KIEU["phang"]
    cac, chi = TC.luoi_o_dap_an(kieu, san_pip=0.0)
    assert len(cac) == len(chi)
    assert len(cac) == len(TC.BUOC) * len(TC.TY_LE_TP) * len(TC.TANG)
    for ts, (ib, ir, it) in zip(cac, chi):
        assert ts.buoc == TC.BUOC[ib]
        assert ts.tran_tang == TC.TANG[it]


def test_luoi_o_dap_an_san_cao_loai_bot_o():
    kieu = TC.KIEU["phang"]
    cac_cao, _ = TC.luoi_o_dap_an(kieu, san_pip=1e9)
    assert len(cac_cao) == 0


# ------------------------------------------------------------------------------------------------------ Kieu.tham_so
def test_kieu_tham_so_geo_giu_he_so():
    k = TC.KIEU["geo"]
    ts = k.tham_so(buoc=10.0, tp=15.0, tang=8, lot=0.02)
    assert ts.buoc == 10.0
    assert ts.tp == 15.0
    assert ts.tran_tang == 8
    assert ts.lot == 0.02
    assert ts.kieu_lot == "nhan"
    assert ts.he_so_lot == 1.1
    assert ts.he_so_buoc == 1.15
    assert ts.che_do == "hai_chieu"


# ------------------------------------------------------------------------------------------------------ kich_ban
def test_kich_ban_tra_dung_va_loi_khi_khong_co():
    kb = TC.kich_ban("Z0")
    assert kb.ten == "Z0"
    assert kb.loai == "L0"
    assert kb.nguon == kb.dich
    try:
        TC.kich_ban("khong_ton_tai")
    except KeyError:
        pass
    else:
        raise AssertionError("phai KeyError")


# ------------------------------------------------------------------------------------------------------ ten_bien_the
def test_ten_bien_the_dinh_dang():
    s = TC.ten_bien_the("A_chart", 0.5, "giu", 0.0)
    assert s == "A_chart|w=0.5|tam=giu|san=0"


# ------------------------------------------------------------------------------------------------------ thi_truong_do_duoc
def test_thi_truong_do_duoc_kieu_quy_mo_sai_thi_loi():
    df = pd.DataFrame({"open": [1.0, 1.0], "high": [1.1, 1.1], "low": [0.9, 0.9],
                       "close": [1.0, 1.0], "spread": [0.0002, 0.0002]},
                      index=pd.date_range("2000-01-03", periods=2, freq="min"))
    try:
        TC.thi_truong_do_duoc(df, 1, "khong_hop_le")
    except ValueError:
        pass
    else:
        raise AssertionError("phai ValueError")


def test_thi_truong_do_duoc_R_H_can_gio_giu():
    df = pd.DataFrame({"open": [1.0, 1.0], "high": [1.1, 1.1], "low": [0.9, 0.9],
                       "close": [1.0, 1.0], "spread": [0.0002, 0.0002]},
                      index=pd.date_range("2000-01-03", periods=2, freq="min"))
    try:
        TC.thi_truong_do_duoc(df, 1, "R_H", gio_giu_phut=None)
    except ValueError:
        pass
    else:
        raise AssertionError("phai ValueError")


# ------------------------------------------------------------------------------------------------------ san_chi_phi_tam
def test_san_chi_phi_tam_dat_va_khoi_phuc():
    from nhan import dich_tham_so as DT
    cu = DT.SAN_CHI_PHI
    with TC.san_chi_phi_tam(7.0):
        assert DT.SAN_CHI_PHI == 7.0
    assert DT.SAN_CHI_PHI == cu


def test_san_chi_phi_tam_khoi_phuc_khi_co_loi():
    from nhan import dich_tham_so as DT
    cu = DT.SAN_CHI_PHI
    try:
        with TC.san_chi_phi_tam(7.0):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert DT.SAN_CHI_PHI == cu


# ------------------------------------------------------------------------------------------------------ _json_an_toan
def test_json_an_toan_nan_thanh_none():
    out = TC._json_an_toan({"a": float("nan"), "b": np.float64(1.5), "c": np.int64(3), "d": np.bool_(True)})
    assert out["a"] is None
    assert out["b"] == 1.5
    assert out["c"] == 3
    assert out["d"] is True


def test_json_an_toan_mang_va_tuple():
    out = TC._json_an_toan(np.array([1.0, float("inf")]))
    assert out[0] == 1.0
    assert out[1] is None
    out2 = TC._json_an_toan((1, 2))
    assert out2 == [1, 2]


# ------------------------------------------------------------------------------------------------------ ke_hoach_s1
def test_ke_hoach_s1_co_plan_hash_va_cau_hinh():
    kh = TC.ke_hoach_s1()
    assert isinstance(kh["plan_hash"], str)
    assert len(kh["plan_hash"]) == 16
    ch = kh["cau_hinh"]
    assert ch["phien_ban_module"] == TC.PHIEN_BAN
    assert ch["buoc"] == list(TC.BUOC)
    assert ch["ty_le_tp"] == list(TC.TY_LE_TP)
    assert ch["tang"] == list(TC.TANG)
    assert ch["von"] == TC.VON
    assert ch["don_bay_toi_da"] == TC.DON_BAY_TOI_DA


def test_ke_hoach_s1_on_dinh():
    assert TC.ke_hoach_s1()["plan_hash"] == TC.ke_hoach_s1()["plan_hash"]
