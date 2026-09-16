# -*- coding: utf-8 -*-
"""Test G4: mot danh muc MOT CHAN phai bao CHUA_DO_DUOC, khong phai ket qua.

Do 16/09: `danh_muc_hien_tai("PASS")` tra `n = 1`,
`tuong_quan_duoi_lon_nhat = 0.0`, va van in ra day du bang chi so. Mot bang nhu
the doc y het mot danh muc da duoc do - trong khi moi so cua no bang dung so
cua chan duy nhat, va cot tuong quan dep chi vi khong co gi de tuong quan voi.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import danh_muc as DM  # noqa: E402


def _tp(ma, seed=0, n=400):
    r = np.random.default_rng(seed).normal(0.0004, 0.01, n)
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    return DM.ThanhPhan(ma=ma, tai_san=ma.split(".")[0], khung="D1",
                        template="t", ho="xu_huong", loi=r, index=idx,
                        chi_so={"tong_lai_pct": 10.0, "sharpe": 1.0})


def test_mot_chan_la_CHUA_DO_DUOC():
    r = DM.ghep([_tp("A")])
    assert r["trang_thai"] == "CHUA_DO_DUOC"
    assert r["n"] == 1
    assert "khong phai danh muc" in r["ly_do_chua_do"]


def test_mot_chan_VAN_TINH_nhung_phai_co_ly_do(monkeypatch):
    """Khong chan tinh toan - hai bai co san goi ghep() voi mot chan de so voi
    mua-giu, va do la viec hop le. Chi buoc phai noi ro no la gi."""
    r = DM.ghep([_tp("A")])
    assert "danh_muc" in r, "van phai tinh, khong duoc chan"
    assert r["trang_thai"] == "CHUA_DO_DUOC"
    assert "khong phai danh muc" in r["ly_do_chua_do"]


def test_khong_chan_nao():
    r = DM.ghep([])
    assert r["n"] == 0 and "khong co thanh phan" in r["ly_do"]


def test_hai_chan_thi_khong_con_nhan_CHUA_DO_DUOC():
    r = DM.ghep([_tp("A", 1), _tp("B", 2)])
    assert r.get("trang_thai") != "CHUA_DO_DUOC"
    assert "ly_do_chua_do" not in r
    assert r["n"] == 2


def test_du_chan_de_ghep_tra_ly_do_doc_duoc():
    d = DM.du_chan_de_ghep([_tp("A")])
    assert not d["dat"] and d["n"] == 1 and "CHUA_DO_DUOC" in d["ly_do"]
    d2 = DM.du_chan_de_ghep([_tp("A", 1), _tp("B", 2)])
    assert d2["dat"] and not d2["ly_do"]


def test_nguong_lay_tu_hang_so_chu_khong_go_cung():
    """Doi CHAN_TOI_THIEU thi hanh vi doi theo - khong co so 2 nao go cung."""
    goc = DM.CHAN_TOI_THIEU
    try:
        DM.CHAN_TOI_THIEU = 3
        assert not DM.du_chan_de_ghep([_tp("A", 1), _tp("B", 2)])["dat"]
    finally:
        DM.CHAN_TOI_THIEU = goc
