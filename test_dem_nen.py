# -*- coding: utf-8 -*-
"""Test: bo dem nen, va cai bay lon nhat cua no.

Chu du an 15/09/2026: *"nen co 1 bo dem nen thuong va 1 bo nen Ha va cac loai
nen khac"*.

Cai bay: **nen Heikin-Ashi LUON cho chuoi dai hon**, vi phep bien doi lam muot.
Do 15/09 tren 134 ma: chuoi HA trung binh 3,7-4,7 nen trong khi nen thuong chi
1,9-2,2. Doc so HA roi ket luan "tai san nay rat xu huong" la doc dac tinh cua
PHEP BIEN DOI chu khong phai cua thi truong.

Va mot ket qua AM TINH phai giu lai: do tren 134 ma, dem nen **khong noi them
gi so voi hurst** (|r| <= 0,195, va cai duy nhat p<0,05 khong song noi hieu
chinh da phep thu). Neu sau nay ai do dung con so nay de du bao, bai test cuoi
tep se nhac.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import dem_nen as DN   # noqa: E402


def _khung(dau: list) -> pd.DataFrame:
    """Chuoi nen voi chieu cho truoc: +1 nen tang, -1 nen giam."""
    o, c = [100.0], []
    for d in dau:
        c.append(o[-1] + d)
        o.append(c[-1])
    o = o[:-1]
    h = [max(a, b) + 0.2 for a, b in zip(o, c)]
    l = [min(a, b) - 0.2 for a, b in zip(o, c)]
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                        index=pd.date_range("2020-01-01", periods=len(o), freq="D"))


def test_chuoi_lien_tiep_dem_dung():
    d = np.array([1, 1, 1, -1, -1, 1, 0, 1, 1])
    ch = DN._chuoi_lien_tiep(d)
    # Doji (0) CAT chuoi: [1,1,1] [-1,-1] [1] | [1,1]
    assert ch["tang"] == [3, 1, 2] and ch["giam"] == [2], ch


def test_nen_doi_mau_lien_tuc_thi_chuoi_NGAN_hon_ngau_nhien():
    """Chuoi luan phien = hoi quy tuyet doi. Ty le phai << 1."""
    h = DN.dem(_khung([1, -1] * 300))
    assert h["hon_ngau_nhien_tang"] < 0.6, h["hon_ngau_nhien_tang"]
    assert h["chuoi_tang"]["trung_binh"] == 1.0


def test_nen_cung_mau_keo_dai_thi_chuoi_DAI_hon_ngau_nhien():
    h = DN.dem(_khung(([1] * 10 + [-1] * 10) * 30))
    assert h["hon_ngau_nhien_tang"] > 2.0, h["hon_ngau_nhien_tang"]


def test_moc_ngau_nhien_dung_cong_thuc_Bernoulli():
    """Khong co moc thi con so 'chuoi trung binh 2,1 nen' khong noi len gi."""
    r = np.random.default_rng(0)
    h = DN.dem(_khung(list(r.choice([1, -1], 4000))))
    # p ~ 0,5 -> moc ~ 2,0 cho ca hai chieu
    assert abs(h["chuoi_tang_ngau_nhien"] - 2.0) < 0.1
    assert 0.85 < h["hon_ngau_nhien_tang"] < 1.15, (
        "chuoi ngau nhien phai ra ~1 lan moc, duoc %.3f" % h["hon_ngau_nhien_tang"])


def test_HA_luon_cho_chuoi_DAI_HON_nen_thuong():
    """Cai bay chinh cua file nay. Dung so cheo hai bo dem."""
    r = np.random.default_rng(1)
    df = _khung(list(r.choice([1, -1], 3000)))
    t = DN.dem(df, "thuong")
    a = DN.dem(df, "ha")
    assert a["chuoi_tang"]["trung_binh"] > t["chuoi_tang"]["trung_binh"] * 1.5, (
        "HA khong lam muot nhu mong doi - kiem lai `nen.heikin_ashi`")


def test_doji_dem_theo_than_tren_bien_do():
    df = _khung([1, -1] * 100)
    df.loc[df.index[:50], "close"] = df.loc[df.index[:50], "open"]
    h = DN.dem(df)
    assert h["doji_pct"] > 20


def test_ho_so_tra_ve_du_hai_bo_dem_va_mot_nhan():
    import types
    df = _khung(list(np.random.default_rng(2).choice([1, -1], 1200)))
    import nhan.du_lieu as DL
    cu = DL.nap
    DL.nap = lambda ma, khung="H1", **k: df
    try:
        h = DN.ho_so("THU", "D1")
    finally:
        DL.nap = cu
    assert set(h["bo_dem"]) == {"thuong", "ha"}
    assert h["nghieng"] in ("XU_HUONG", "HOI_QUY", "TRUNG_TINH")
    assert "hon_ngau_nhien_tb" in h
    assert isinstance(DN.in_ra(h), str)


def test_KET_QUA_AM_TINH_duoc_ghi_lai_trong_tai_lieu():
    """Do tren 134 ma: dem nen KHONG noi them gi so voi hurst.

    Mot ket qua am tinh khong duoc ghi o dau se duoc ai do do lai sau vai tuan.
    """
    s = (LAB / "nhan" / "dem_nen.py").read_text(encoding="utf-8-sig")
    assert "MOC NGAU NHIEN" in s
    s2 = (LAB / "nhan" / "ho_so_tai_san.py").read_text(encoding="utf-8-sig")
    assert "dem nen KHONG noi them gi so voi " in s2, (
        "ho so tai san khong con canh bao rang dem nen chi de MO TA")
