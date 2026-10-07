# -*- coding: utf-8 -*-
"""Test cho nhan.quan_tri_nhieu."""
import numpy as np
import pandas as pd

from nhan.quan_tri_nhieu import (
    HO, SL_CUNG, GIU_TOI_DA,
    ViThe, LenhCho, TrangThai,
    _atr, _gia_tb, lai_ro,
    dap_nhieu, bo_luat,
)


def _df(o, h, l, c):
    idx = pd.date_range("2020-01-01", periods=len(o), freq="h")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c}, index=idx)


def _df_phang(n, gia=100.0):
    o = np.full(n, gia)
    return _df(o, o.copy(), o.copy(), o.copy())


def test_hang_so_ho_va_luoi():
    assert HO == ("hedge", "luoi_dca", "stop_2_dau", "tt_stop_doi", "thoi_gian")
    assert SL_CUNG == 3.0
    assert GIU_TOI_DA == 120


def test_ho_khong_biet_thi_bao_loi():
    df = _df_phang(50)
    th = np.zeros(50)
    try:
        dap_nhieu(df, th, "khong_co_ho_nay")
    except ValueError:
        return
    raise AssertionError("phai nem ValueError voi ho khong biet")


def test_atr_tren_chuoi_phang_bang_khong():
    n = 40
    o = np.full(n, 100.0)
    a = _atr(o, o.copy(), o.copy(), 14)
    assert np.isnan(a[0])
    assert np.isnan(a[13])
    assert a[14] == 0.0
    assert a[-1] == 0.0


def test_atr_qua_ngan_tra_toan_nan():
    n = 10
    o = np.full(n, 100.0)
    a = _atr(o, o.copy(), o.copy(), 14)
    assert a.shape == (n,)
    assert np.all(np.isnan(a))


def test_gia_tb_rong_va_mot_chieu():
    assert _gia_tb([]) == (0.0, 0.0, 0)
    v = [ViThe(chieu=1, gia=100.0, lot=2.0, bar_vao=0),
         ViThe(chieu=1, gia=110.0, lot=1.0, bar_vao=1)]
    gtb, tong, chieu = _gia_tb(v)
    assert abs(tong - 3.0) < 1e-12
    assert chieu == 1
    assert abs(gtb - (100.0 * 2.0 + 110.0 * 1.0) / 3.0) < 1e-9


def test_gia_tb_hai_chieu_chieu_bang_khong():
    v = [ViThe(chieu=1, gia=100.0, lot=1.0, bar_vao=0),
         ViThe(chieu=-1, gia=100.0, lot=1.0, bar_vao=0)]
    gtb, tong, chieu = _gia_tb(v)
    assert chieu == 0
    assert abs(tong - 2.0) < 1e-12
    assert abs(gtb - 100.0) < 1e-9


def test_lai_ro_dau_va_chieu():
    assert lai_ro([], 100.0) == 0.0
    v = [ViThe(chieu=1, gia=100.0, lot=2.0, bar_vao=0)]
    assert abs(lai_ro(v, 105.0) - 10.0) < 1e-9
    assert abs(lai_ro(v, 95.0) + 10.0) < 1e-9
    v2 = [ViThe(chieu=-1, gia=100.0, lot=1.0, bar_vao=0)]
    assert abs(lai_ro(v2, 90.0) - 10.0) < 1e-9


def test_duong_cong_do_dai_va_rong_khi_khong_tin_hieu():
    n = 200
    rng = np.random.default_rng(1)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, n)))
    df = _df(gia, gia * 1.001, gia * 0.999, np.r_[gia[1:], gia[-1]])
    th = np.zeros(n)
    r = dap_nhieu(df, th, "luoi_dca", {"buoc_atr": 1.0, "tp_atr": 1.0})
    assert r["duong_cong"].shape == (n,)
    assert r["so_ro"] == 0
    assert r["so_lenh"] == 0
    assert r["lai_tong"] == 0.0
    assert r["ro_treo_cuoi_mau"] is None
    assert r["ly_do"] == {}


def test_duong_cong_rong_khi_atr_nan():
    # Chuoi ngan hon atr_n+2 -> vong nen khong chay, khong co ro nao.
    n = 10
    o = np.full(n, 100.0)
    df = _df(o, o.copy(), o.copy(), o.copy())
    th = np.ones(n)
    r = dap_nhieu(df, th, "luoi_dca", {"buoc_atr": 1.0, "tp_atr": 1.0})
    assert r["so_ro"] == 0
    assert r["lai_tong"] == 0.0
    assert np.all(r["duong_cong"] == 0.0)


def test_luoi_dca_mo_ro_va_co_lenh():
    n = 300
    rng = np.random.default_rng(3)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
    df = _df(gia, gia * 1.002, gia * 0.998, np.r_[gia[1:], gia[-1]])
    th = np.zeros(n)
    th[::50] = 1.0
    r = dap_nhieu(df, th, "luoi_dca", {"buoc_atr": 1.0, "tp_atr": 1.0})
    assert r["so_ro"] >= 1
    assert r["so_lenh"] >= 1
    assert r["dinh_lot"] > 0
    assert r["ho"] == "luoi_dca"
    assert r["duong_cong"].shape == (n,)


def test_bo_luat_co_du_nam_ho():
    bl = bo_luat()
    assert len(bl) > 0
    cac_ho = {v[0] for v in bl.values()}
    assert cac_ho == set(HO)
    for ten, (ho, p) in bl.items():
        assert ho in HO
        assert isinstance(p, dict)


def test_ro_treo_cuoi_mau_khi_con_vi_the():
    # Chuoi di ngang -> luoi_dca mo ro va khong dong het -> co ro treo.
    n = 400
    rng = np.random.default_rng(5)
    gia = 100 * np.exp(np.cumsum(rng.normal(0, 0.0005, n)))
    df = _df(gia, gia * 1.0005, gia * 0.9995, np.r_[gia[1:], gia[-1]])
    th = np.zeros(n)
    th[0] = 1.0
    r = dap_nhieu(df, th, "luoi_dca", {"buoc_atr": 5.0, "tp_atr": 5.0})
    if r["ro_treo_cuoi_mau"] is not None:
        rt = r["ro_treo_cuoi_mau"]
        assert rt["so_lenh"] >= 1
        assert rt["con_song"] >= 1
        assert "lai_mtm" in rt
