# -*- coding: utf-8 -*-
"""Test: SPEC HONG khong duoc bien mat trong im lang.

## Chuyen da xay ra, 14/09/2026

Toi them 5 spec DSL vao kho voi `ho = "hoi_quy"` - mot ten khong thuoc danh sach
ho hop le. Ket qua:

  - `luu_kho` nhan het, khong mot loi nao.
  - `chay_tester_kho` loc chung ra va in `kho 0 -> dich duoc 1`.
  - Neu khong tinh co dem lai so co che, toi da chay tester tren **mot he** roi
    tuong do la ket qua cua ca **ba he** dang o lan nhanh.

Va do khong phai ca le: do lai thi **44/3233 co che trong kho** dang hong va bi
vut moi luot chay tester, suot nhieu ngay, khong ai biet.

Cung ho loi voi moi thu bat duoc trong ngay: **he im lang khi sai**. Bo test nay
giu cho hai cai mieng vua mo ra khong bi bit lai.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import ngu_phap as NP   # noqa: E402


def spec_tot(ten: str = "thu_tot") -> dict:
    return {
        "ten": ten,
        "ho": "quay_ve_trung_binh",
        "chieu": 1,
        "giu": 1,
        "co_che": ("Ban qua da ngan han thi ap luc mua quay lai, nen vao khi RSI "
                   "xuong duoi 30 va thoat khi no hoi len tren 55."),
        "vao": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<",
                 "phai": {"hang": 30.0}}],
        "ra": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": ">",
                "phai": {"hang": 55.0}}],
    }


# ------------------------------------------------- CONG NGU PHAP CON SONG
def test_spec_tot_qua_duoc_cong():
    """Chieu nguoc: cong tu choi TAT CA thi so lieu y het mot cong tot."""
    assert NP.kiem_khai_bao(spec_tot()) == []


def test_ho_khong_hop_le_bi_tu_choi():
    """Dung cai da sap 14/09: `ho = "hoi_quy"` khong thuoc danh sach ho."""
    xau = {**spec_tot(), "ho": "hoi_quy"}
    loi = NP.kiem_khai_bao(xau)
    assert loi and "ho" in loi[0]


def test_thieu_co_che_bi_tu_choi():
    """37/44 spec hong trong kho la vi thieu truong nay."""
    xau = {k: v for k, v in spec_tot().items() if k != "co_che"}
    assert NP.kiem_khai_bao(xau)


def test_zscore_thieu_ve_cua_thi_KHONG_sinh_duoc():
    """Cai bay thu hai cua 14/09: `zscore` khong noi tinh tren gia nao.

    Cho nay ngu phap NEM LOI (tot) chu khong tra ve mang 0 - nhung ghi lai de
    neu ai do "sua cho no khoi nem" thi test nay do.
    """
    import numpy as np
    import pandas as pd
    df = pd.DataFrame({"open": np.arange(100.0, 200.0),
                       "high": np.arange(100.5, 200.5),
                       "low": np.arange(99.5, 199.5),
                       "close": np.arange(100.0, 200.0)},
                      index=pd.date_range("2020-01-01", periods=100, freq="h"))
    thieu = {**spec_tot(),
             "vao": [{"trai": {"chi_bao": "zscore", "n": 20}, "phep": "<",
                      "phai": {"hang": -2.0}}]}
    with pytest.raises(Exception):
        NP.sinh_tu_spec(thieu, df)


def test_zscore_CO_ve_cua_thi_sinh_duoc():
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(3)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 300)))
    df = pd.DataFrame({"open": c, "high": c * 1.001, "low": c * 0.999, "close": c},
                      index=pd.date_range("2020-01-01", periods=300, freq="h"))
    du = {**spec_tot(),
          "vao": [{"trai": {"chi_bao": "zscore",
                            "cua": {"chi_bao": "gia", "cot": "close"}, "n": 20},
                   "phep": "<", "phai": {"hang": -1.0}}],
          "ra": []}
    th = np.asarray(NP.sinh_tu_spec(du, df), float)
    assert len(th) == len(df)
    assert np.sum(np.abs(th) > 0) > 0


# ------------------------------------- LUU_KHO PHAI KEU KHI NHAN SPEC HONG
def test_luu_kho_KEU_khi_co_spec_hong(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(NP, "KHO_CO_CHE", tmp_path / "kho.json")
    monkeypatch.setattr(NP, "_doc_moc_cao", lambda: 0)
    monkeypatch.setattr(NP, "_ghi_moc_cao", lambda n: None)
    ds = [spec_tot("a"), {**spec_tot("b_hong"), "ho": "hoi_quy"}]
    NP.luu_kho(ds, ep=True)
    err = capsys.readouterr().err
    assert "CANH BAO" in err
    assert "b_hong" in err
    assert "1/2" in err


def test_luu_kho_IM_LANG_khi_moi_spec_deu_tot(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(NP, "KHO_CO_CHE", tmp_path / "kho.json")
    monkeypatch.setattr(NP, "_doc_moc_cao", lambda: 0)
    monkeypatch.setattr(NP, "_ghi_moc_cao", lambda n: None)
    NP.luu_kho([spec_tot("a"), spec_tot("b")], ep=True)
    assert "CANH BAO" not in capsys.readouterr().err


def test_luu_kho_VAN_GHI_du_co_spec_hong(tmp_path, monkeypatch):
    """Keu to, nhung KHONG tu choi ghi.

    Kho dang co 44 cai hong tu truoc; tu choi ghi la lam do ca nhung duong ghi
    hop le khac - va do la cach bien mot canh bao thanh mot su co.
    """
    monkeypatch.setattr(NP, "KHO_CO_CHE", tmp_path / "kho.json")
    monkeypatch.setattr(NP, "_doc_moc_cao", lambda: 0)
    monkeypatch.setattr(NP, "_ghi_moc_cao", lambda n: None)
    NP.luu_kho([spec_tot("a"), {**spec_tot("b_hong"), "ho": "hoi_quy"}], ep=True)
    ds = json.loads((tmp_path / "kho.json").read_text(encoding="utf-8"))
    assert len(ds) == 2


# -------------------------------- TESTER PHAI NOI RO NO BO CAI NAO VA VI SAO
def test_chay_tester_kho_co_in_ly_do_bo():
    """Bo quet ma nguon: doan loc phai in ra ly do, khong chi in con so cuoi."""
    s = (LAB / "chay_tester_kho.py").read_text(encoding="utf-8-sig")
    assert "BI BO vi khai bao hong" in s, "tester khong con bao ly do bo co che"
    assert "KHOP BO LOC" in s, "tester khong con bao co che bi bo NAM TRONG bo loc"
    assert "khong dich duoc" in s, "tester khong con liet ke co che khong dich duoc"
