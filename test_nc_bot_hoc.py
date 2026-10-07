# -*- coding: utf-8 -*-
"""Dau truong bot tu hoc: luat lenh dung, mang hoc duoc, va con so "dang hoc" khong phai bang chung."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from nhan import nc_bot_hoc as BH

_CP0 = SimpleNamespace(spread_mang=lambda idx: np.zeros(len(idx)), truot_gia_frac=0.0)


def _df(o, h, l, c):
    idx = pd.date_range("2026-01-05", periods=len(o), freq="4h")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c}, index=idx)


def test_thuong_tp_sl_va_het_gio_dung_luat_va_vao_o_gia_mo_bar_sau():
    n = 12
    o = np.full(n, 100.0)
    c = np.full(n, 100.0)
    h = np.full(n, 100.2)
    l = np.full(n, 99.8)
    h[1], c[1] = 103.0, 102.5                     # bar 1 vot len: mua cham TP, ban cham SL
    R, A = BH.thuong_theo_bar(_df(o, h, l, c), _CP0, np.full(n, 1.0))
    j_mua1, j_ban1 = A.index((1, 1)), A.index((-1, 1))
    assert R[0, j_mua1] == pytest.approx(200.0)   # TP = 2 ATR = +2% tu gia mo bar 1
    assert R[0, j_ban1] == pytest.approx(-200.0)  # SL = 2 ATR
    # bar 3 -> 4: di ngang, khong cham gi -> TIMEOUT o gia dong bar het gio
    j_mua5 = A.index((1, 5))
    assert R[3, j_mua5] == pytest.approx(0.0)


def test_phi_khu_hoi_tru_vao_moi_lenh():
    n = 12
    cp = SimpleNamespace(spread_mang=lambda idx: np.full(len(idx), 1e-4), truot_gia_frac=0.5e-4)
    o = c = np.full(n, 100.0)
    R, A = BH.thuong_theo_bar(_df(o, o + 0.1, o - 0.1, c), cp, np.full(n, 1.0))
    assert R[2, 0] == pytest.approx(-3.0)          # 2 x (1 + 0,5) bps, gia khong doi


def test_mang_hoc_duoc_ham_don_gian():
    g = np.random.default_rng(1)
    X = g.normal(size=(2000, 3))
    r = np.where(X[:, 0] > 0, 1.0, -1.0)
    net = BH.MLP(3, 2, h=16, seed=1, lr=3e-3)
    for _ in range(1500):
        j = g.integers(2000, size=64)
        net.hoc(X[j], np.zeros(64, int), r[j])
    q = net.f(X)[0][:, 0]
    assert np.mean(np.sign(q) == np.sign(X[:, 0])) > 0.9


@pytest.mark.cham
def test_avg_luc_hoc_duong_tren_NHIEU_nhung_giao_thuc_khong_DAT():
    """Con so quang cao khoe (Avg reward luc hoc) moc ra ca tren chuoi KHONG co edge."""
    r = BH.hoc("TONG_HOP_NHIEU_1", "A", buoc=40_000, hat=1)
    assert r["avg1000_hoc"][-1] > 5.0, r["avg1000_hoc"]
    assert r["kham_pha"]["t"] > 5.0
    assert not r["dat_giao_thuc"]
