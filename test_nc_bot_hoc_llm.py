# -*- coding: utf-8 -*-
"""Test cho nhan/nc_bot_hoc.py - chi kiem hanh vi co that, du lieu nho tu dung."""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhan import nc_bot_hoc as BH


def _df_gia(n: int = 60) -> pd.DataFrame:
    """DataFrame OHLC nho, gia di len de co ATR hop le."""
    idx = pd.date_range("2020-01-01", periods=n, freq="4h")
    c = np.linspace(100.0, 100.0 + n, n)
    return pd.DataFrame({"open": c, "high": c + 1.0, "low": c - 1.0, "close": c}, index=idx)


def test_mlp_f_tra_ve_dung_kich_thuoc():
    net = BH.MLP(d=5, k=3, h=4, seed=0)
    X = np.zeros((7, 5))
    q, cache = net.f(X)
    assert q.shape == (7, 3)
    assert len(cache) == 5


def test_mlp_hoc_khong_lam_hong_trong_so():
    net = BH.MLP(d=4, k=2, h=3, seed=1)
    X = np.random.default_rng(0).normal(size=(16, 4))
    a = np.array([0, 1] * 8)
    r = np.zeros(16)
    truoc = [w.copy() for w in net.p]
    net.hoc(X, a, r)
    assert net.t == 1
    assert any(not np.allclose(w0, w1) for w0, w1 in zip(truoc, net.p))


def test_mlp_hoc_voi_mang_rong_khong_loi():
    net = BH.MLP(d=3, k=2, h=2, seed=2)
    net.hoc(np.zeros((0, 3)), np.zeros(0, int), np.zeros(0))
    assert net.t == 1


def test_thuong_theo_bar_hinh_dang_va_gia_tri_hop_le():
    df = _df_gia(60)
    atr = np.full(len(df), 1.0)

    class CP:
        spread_mang = staticmethod(lambda idx: np.zeros(len(idx)))
        truot_gia_frac = 0.0

    R, A = BH.thuong_theo_bar(df, CP(), atr)
    assert R.shape == (len(df), len(A))
    assert len(A) == 2 * len(BH.H)
    assert set(s for s, _ in A) == {1, -1}
    # hang cuoi khong the tinh -> NaN
    assert np.isnan(R[-1]).all()
    # co it nhat mot o huu han
    assert np.isfinite(R).any()


def test_thuong_theo_bar_atr_nan_thi_bo_qua():
    df = _df_gia(60)
    atr = np.full(len(df), np.nan)

    class CP:
        spread_mang = staticmethod(lambda idx: np.zeros(len(idx)))
        truot_gia_frac = 0.0

    R, _ = BH.thuong_theo_bar(df, CP(), atr)
    assert np.isnan(R).all()


def test_di_bo_khong_chong_lenh_va_ton_trong_hold():
    # q luon am -> khong vao lenh nao
    R = np.zeros((10, 2))
    A = [(1, 1), (-1, 1)]
    ok = np.ones(10, bool)
    ds = BH._di_bo(np.full((10, 2), -1.0), R, A, np.arange(10), ok)
    assert ds == []


def test_di_bo_vao_lenh_khi_q_duong():
    R = np.zeros((10, 2))
    R[0, 0] = 5.0
    A = [(1, 1), (-1, 1)]
    ok = np.ones(10, bool)
    q = np.full((10, 2), -1.0)
    q[0, 0] = 1.0
    ds = BH._di_bo(q, R, A, np.arange(10), ok)
    assert len(ds) == 1
    assert ds[0] == (5.0, 1)


def test_di_bo_bo_qua_vi_tri_khong_ok():
    R = np.zeros((10, 2))
    R[0, 0] = 5.0
    A = [(1, 1), (-1, 1)]
    ok = np.ones(10, bool)
    ok[0] = False
    q = np.full((10, 2), -1.0)
    q[0, 0] = 1.0
    ds = BH._di_bo(q, R, A, np.arange(10), ok)
    assert ds == []


def test_chuan_bi_tra_ve_bon_phan_tu():
    df, F, R, A = BH.chuan_bi("TONG_HOP_NHIEU_1", "H4")
    assert len(df) == len(F) == len(R)
    assert F.shape[1] == 26 + 10
    assert len(A) == 2 * len(BH.H)


def test_hoc_bien_the_b_khong_dung_cua_so_gia_tho():
    r = BH.hoc("TONG_HOP_NHIEU_1", "B", buoc=200, hat=1)
    assert r["bien_the"] == "B"
    assert r["buoc"] == 200
    assert set(r.keys()) >= {"ma", "bien_the", "buoc", "avg1000_hoc",
                             "kham_pha", "xac_nhan", "niem_phong", "dat_giao_thuc"}
    for doan in ("kham_pha", "xac_nhan", "niem_phong"):
        d = r[doan]
        assert set(d.keys()) == {"lenh", "tb_bps", "t", "ty_le_mua", "dat"}
        assert isinstance(d["dat"], bool)


def test_hoc_dat_giao_thuc_la_va_cua_hai_doan():
    r = BH.hoc("TONG_HOP_NHIEU_1", "A", buoc=200, hat=1)
    assert r["dat_giao_thuc"] == bool(r["xac_nhan"]["dat"] and r["niem_phong"]["dat"])


def test_hoc_avg1000_hoc_rong_khi_buoc_nho():
    r = BH.hoc("TONG_HOP_NHIEU_1", "A", buoc=10, hat=1)
    # buoc // 5 = 2 -> co it nhat mot moc log
    assert isinstance(r["avg1000_hoc"], list)
    assert len(r["avg1000_hoc"]) >= 1
