# -*- coding: utf-8 -*-
"""Test: cong DO cua `sua_bar_hong` phai TUONG DUONG ban khong co cong.

## Chuyen bat duoc 15/09/2026

`chay_test_tung_me` bao me 10 **QUA GIO 1800s**. Lay stack cua tien trinh dang
chay ra thi thay no dang o `du_lieu.sua_bar_hong`, goi tu `ngoai_sinh.chuyen`.

Do tren EURUSD H1 (171.113 bar):

    nap KHONG sua bar     0,63 s
    rieng `sua_bar_hong`  8,12 s   <- va bao cao sua la {} : KHONG sua gi ca
    nap CO sua bar        8,13 s

Vong tuan tu chay Python thuan tren `n x 4` o, moi o mot `np.log10`, moi bar
mot `np.median`. Va `nap()` goi no SAU cache, nen cache parquet khong cuu duoc
gi. `ngoai_sinh.chuyen` goi `nap` mot lan cho MOI ung vien lan can -> hon 30
phut CPU cho mot bai test, va ca me khong bao gio ket thuc.

Cai gia that khong phai thoi gian: **mot me khong ket thuc la mot me khong ai
doc ket qua**. Me 10 co 10 file, va chung im lang nhieu ngay.

## Bo test nay giu gi

Cong toc do KHONG duoc doi ket qua. Day la kieu toi uu de lam lech nhat: no
chay nhanh hon, khong bao loi, va cho mot chuoi gia hoi khac - roi moi backtest
sau do deu dung chuoi do.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import du_lieu as DL   # noqa: E402

COT = ("open", "high", "low", "close")


def _chuoi(n=3000, gia=1.2, hat=0):
    r = np.random.default_rng(hat)
    c = gia * np.exp(np.cumsum(r.normal(0, 0.002, n)))
    o = np.concatenate([[c[0]], c[:-1]])
    h = np.maximum(o, c) * (1 + np.abs(r.normal(0, 0.001, n)))
    l = np.minimum(o, c) * (1 - np.abs(r.normal(0, 0.001, n)))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                        index=pd.date_range("2015-01-01", periods=n, freq="h"))


def _khong_cong(df):
    """Chay `sua_bar_hong` voi cong LUON MO - tuc ban truoc 15/09."""
    goc = DL._co_bar_lech_bac
    DL._co_bar_lech_bac = lambda *a, **k: True
    try:
        return DL.sua_bar_hong(df)
    finally:
        DL._co_bar_lech_bac = goc


def _giong(a, b) -> bool:
    return all(np.allclose(a[c].to_numpy(float), b[c].to_numpy(float),
                           equal_nan=True) for c in COT)


def test_chuoi_SACH_cho_ket_qua_y_het_ban_khong_cong():
    df = _chuoi()
    a, bca = DL.sua_bar_hong(df)
    b, bcb = _khong_cong(df)
    assert bca == bcb, "bao cao sua khac nhau: %s vs %s" % (bca, bcb)
    assert _giong(a, b), "cong toc do lam doi chinh chuoi gia"


@pytest.mark.parametrize("he", [10.0, 0.1, 100.0])
@pytest.mark.parametrize("cot", list(COT))
def test_bar_HONG_van_bi_bat_va_sua_y_het(cot, he):
    """Cong phai MO khi that su co bar lech mot bac 10 - moi cot, moi chieu."""
    df = _chuoi()
    df = df.copy()
    df.iloc[1500, df.columns.get_loc(cot)] *= he
    a, bca = DL.sua_bar_hong(df)
    b, bcb = _khong_cong(df)
    assert bca == bcb, "cong CHAN OAN mot chuoi co bar hong: %s vs %s" % (bca, bcb)
    assert _giong(a, b)
    assert bca, "khong bat duoc bar hong x%g o cot %s" % (he, cot)


def test_ca_BON_cot_cung_lech_van_bi_bat():
    """Ca EURMXN 2023-06-26: ba cot x10, neo theo bar cung luc thi mu.

    Day la ly do neo TRUOT ton tai; cong do phai thay duoc dung ca do.
    """
    df = _chuoi().copy()
    for c in COT:
        df.iloc[1500, df.columns.get_loc(c)] *= 10.0
    a, bca = DL.sua_bar_hong(df)
    b, bcb = _khong_cong(df)
    assert bca == bcb and _giong(a, b)
    assert bca, "ca bon cot cung lech ma cong khong mo"


def test_bien_dong_THAT_khong_bi_coi_la_bar_hong():
    """Chieu nguoc: mot tai san tang truong that khong duoc dung cham."""
    n = 3000
    c = 1.0 * np.exp(np.linspace(0, np.log(8.0), n))   # tang 8 lan, that
    df = pd.DataFrame({"open": c, "high": c * 1.01, "low": c * 0.99, "close": c},
                      index=pd.date_range("2015-01-01", periods=n, freq="h"))
    a, bca = DL.sua_bar_hong(df)
    b, bcb = _khong_cong(df)
    assert bca == bcb and _giong(a, b)
    assert "neo_truot_x10" not in bca, "sua oan mot xu huong tang THAT"


def test_cong_re_hon_vong_tuan_tu_it_nhat_5_lan():
    """Neu cong khong nhanh hon thi no chi them mot lop rui ro.

    Do that 15/09 tren EURUSD H1: 8,12s -> 0,20s (40 lan). O day chi doi 5 lan
    de bai kiem khong gion tren may khac.
    """
    df = _chuoi(n=60000)
    t0 = time.time(); DL.sua_bar_hong(df); co = time.time() - t0
    t0 = time.time(); _khong_cong(df); khong = time.time() - t0
    assert khong > co * 5, ("cong chi nhanh hon %.1f lan (%.2fs vs %.2fs)"
                            % (khong / max(co, 1e-9), co, khong))


def test_nguong_cong_CHAT_HON_nguong_sua_that():
    """Cong phai nghieng ve phia CHO CHAY.

    Chay thua ton vai giay; chan oan lam mot bar hong x10 lot vao backtest.
    """
    s = (LAB / "nhan" / "du_lieu.py").read_text(encoding="utf-8-sig")
    assert DL.NGUONG_DO_LECH_BAC < 0.35, (
        "nguong cong khong duoc rong bang hay hon nguong sua that (0,35)")
    assert "0.35" in s, "nguong sua that da doi - xem lai nguong cong"


def test_khong_do_duoc_thi_CHO_CHAY_chu_khong_chan():
    """Chuoi qua ngan / toan NaN: tra True (chay vong tuan tu), khong chan mu."""
    d = {c: np.full(3, np.nan) for c in COT}
    assert DL._co_bar_lech_bac(d, 3) is True
