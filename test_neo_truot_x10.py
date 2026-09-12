# -*- coding: utf-8 -*-
"""test_neo_truot_x10.py - Bo sua bar phai thay duoc loi thang khi NHIEU cot cung lech.

## Cai da xay ra 12/09/2026

`sua_bar_hong` buoc 1 neo vao TRUNG VI BA COT CON LAI tren cung bar. No dung khi
mot cot lech (GBPZAR: rieng `high` x10), nhung MU khi tu hai cot tro len cung
lech - vi luc do chinh cai neo bi keo theo:

    EURMXN 2023-06-26   open 186.86   high 187.57   low 18.65   close 187.24

Ba cot x10 -> trung vi ba cot con lai cung x10 -> ty le 1,0 -> khong sua gi.
68 o nhu vay tren 2.439 bar du de:

    do lech chuan loi suat open-to-open   0,0072  ->  0,2382   (33 lan)
    `cagr_dd20` cua mot co che             -2,35  ->  +695,59
    `moc_dd20` (mua-giu cung sut giam)       0,0  ->  +221,76

va **120/120 dong dau bang xep hang cua pheu deu la EURMXN** - mot ma di ngang
tu 20,72 xuong 19,89 trong 9,4 nam.

## HAI CHIEU, KHONG MOT CHIEU

Mot bo sua chua sai bao gio thi vo dung; mot bo sua "sua" ca du lieu sach con te
hon - no be chuoi that. Nen o day co ca hai phep thu, va phep thu chuoi SACH la
phep quan trong hon ([[cong-pass-phai-hieu-chuan-hai-chieu]]).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import du_lieu as DL          # noqa: E402


def _chuoi_sach(n: int = 800, tang: float = 0.001, hat: int = 7):
    idx = pd.date_range("2016-01-01", periods=n, freq="D", tz="UTC")
    rng = np.random.default_rng(hat)
    c = 20 * np.exp(np.cumsum(rng.normal(tang, 0.01, n)))
    df = pd.DataFrame({"open": c * (1 + rng.normal(0, 0.001, n)),
                       "high": c * 1.008, "low": c * 0.992, "close": c},
                      index=idx)
    df["high"] = np.maximum.reduce([df["high"], df["open"], df["close"]])
    df["low"] = np.minimum.reduce([df["low"], df["open"], df["close"]])
    return df


# --------------------------------------------------- chieu 1: PHAI SUA DUOC
def test_ba_cot_cung_lech_van_sua_duoc():
    """Dung hinh dang cua EURMXN: open/high/close x10, low giu nguyen."""
    sach = _chuoi_sach()
    do = sach.copy()
    i = np.arange(300, 340, 2)
    for cot in ("open", "high", "close"):
        do.iloc[i, do.columns.get_loc(cot)] *= 10.0
    fix, bc = DL.sua_bar_hong(do)
    assert bc, "khong sua gi ca"
    lech = np.max(np.abs(fix["close"].to_numpy() - sach["close"].to_numpy()))
    assert lech < 1e-6, "sua xong van lech %.4f so voi ban sach" % lech


def test_ca_bon_cot_cung_lech_van_sua_duoc():
    """Truong hop nang nhat - khong con cot nao lam neo trong cung bar."""
    sach = _chuoi_sach()
    do = sach.copy()
    i = np.arange(500, 530)
    for cot in ("open", "high", "low", "close"):
        do.iloc[i, do.columns.get_loc(cot)] *= 10.0
    fix, bc = DL.sua_bar_hong(do)
    assert "neo_truot_x10" in bc, "khau neo truot phai la khau vot duoc ca nay"
    lech = np.max(np.abs(fix["close"].to_numpy() - sach["close"].to_numpy()))
    assert lech < 1e-6


def test_loi_suat_ve_lai_binh_thuong():
    """Thuoc doc duoc: do lech chuan loi suat phai ve gan ban sach."""
    sach = _chuoi_sach()
    do = sach.copy()
    i = np.arange(300, 340, 2)
    for cot in ("open", "high", "close"):
        do.iloc[i, do.columns.get_loc(cot)] *= 10.0
    sd_do = np.std(np.diff(np.log(do["open"].to_numpy())))
    sd_fix = np.std(np.diff(np.log(DL.sua_bar_hong(do)[0]["open"].to_numpy())))
    sd_sach = np.std(np.diff(np.log(sach["open"].to_numpy())))
    assert sd_do > 5 * sd_sach                  # truoc khi sua: rac
    assert abs(sd_fix - sd_sach) < 0.1 * sd_sach


# ------------------------------------------- chieu 2: KHONG DUOC DUNG CHAM
def test_chuoi_sach_khong_bi_dung_cham():
    sach = _chuoi_sach()
    fix, bc = DL.sua_bar_hong(sach)
    assert not bc, "bo sua dong vao chuoi sach: %s" % bc
    for cot in ("open", "high", "low", "close"):
        assert np.array_equal(fix[cot].to_numpy(), sach[cot].to_numpy())


def test_tai_san_tang_muoi_lan_khong_bi_be():
    """Tang 10 lan qua nhieu nam KHONG phai loi thang - neo phai troi theo."""
    sach = _chuoi_sach(n=2500, tang=0.001)
    assert sach["close"].iloc[-1] / sach["close"].iloc[0] > 3
    fix, bc = DL.sua_bar_hong(sach)
    assert not bc
    assert np.array_equal(fix["close"].to_numpy(), sach["close"].to_numpy())


def test_bien_dong_manh_that_khong_bi_sua():
    """Crypto/dau nhay 20-40% mot bar la THAT - chi lech ~10 lan moi la loi."""
    sach = _chuoi_sach()
    do = sach.copy()
    i = [100, 200, 300]
    do.iloc[i, do.columns.get_loc("close")] *= 1.35
    do["high"] = np.maximum.reduce([do["high"], do["open"], do["close"]])
    fix, bc = DL.sua_bar_hong(do)
    assert not bc.get("neo_truot_x10"), "neo truot dong vao bien dong that"


# ------------------------------------------------------ cong o trong pheu
def test_pheu_doc_co_dung_duoc():
    """`to_hop._mot_o` phai TU CHOI ma ma `kiem` bao khong dung duoc.

    Bay chat luong da co tu lau va bao dung; cai thieu la khong noi nao doc no.
    """
    import inspect

    from nhan import to_hop as TH
    ma = inspect.getsource(TH._mot_o)
    assert "dung_duoc" in ma, "pheu van khong doc co chat luong du lieu"
