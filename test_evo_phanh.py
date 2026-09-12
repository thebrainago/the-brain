# -*- coding: utf-8 -*-
"""test_evo_phanh.py - EVO co canh duoc cai PHANH khong.

`nhan/han_muc.py` (kill-switch: tran sut giam / lenh ngay / phoi nhiem / von)
la module MO COI cho toi 12/09 - ban do sinh tu ma nguon tim ra. No mo coi vi
he chua danh lenh that, va do la BINH THUONG. Cai khong binh thuong la de nguyen
nhu vay den luc cam VPS chay nhieu thang.

Nen EVO canh dung mot dieu: **co he dang chay ma chua khai han muc khong**.
Hai chieu deu phai test - mot bo canh khong bao gio keu cho so lieu y het mot
bo canh tot ([[cong-pass-phai-hieu-chuan-hai-chieu]]).
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import nhan.so as _so                       # noqa: E402
from nhan import evo as E                   # noqa: E402
from nhan import han_muc as HM              # noqa: E402


def _gia_he_chay(monkeypatch, ma_list):
    """Gia lam bang `he_chay` tra ve danh sach cho truoc."""
    that = _so.nhieu

    def gia(q, *a, **k):
        if "he_chay" in q:
            return [{"ma": m} for m in ma_list]
        return that(q, *a, **k)

    monkeypatch.setattr(_so, "nhieu", gia)


def test_khong_he_nao_chay_thi_khong_keu(monkeypatch):
    """Chua danh lenh that thi phanh chua can - khong duoc bia ra van de."""
    _gia_he_chay(monkeypatch, [])
    cs = E.suc_khoe_phanh()
    assert any(c["ten"] == "phanh.he_chay" and c["trang_thai"] == E.TOT
               for c in cs)
    assert not any(c["trang_thai"] == E.XAU for c in cs)


def test_he_chay_ma_chua_khai_thi_XAU(monkeypatch):
    """Chieu nguoc lai: phai keu, va phai noi ro he nao."""
    _gia_he_chay(monkeypatch, ["he_khong_co_that_123"])
    cs = E.suc_khoe_phanh()
    xau = [c for c in cs if c["ten"] == "phanh.chua_khai"]
    assert xau and xau[0]["trang_thai"] == E.XAU
    assert xau[0]["gia_tri"] == 1
    assert "he_khong_co_that_123" in xau[0]["bang_chung"]


def test_de_xuat_phai_go_duoc(monkeypatch):
    """De xuat cua EVO phai la lenh CHAY DUOC, khong phai loi khuyen rong."""
    _gia_he_chay(monkeypatch, ["he_khong_co_that_123"])
    xau = [c for c in E.suc_khoe_phanh() if c["ten"] == "phanh.chua_khai"][0]
    lenh = xau["de_xuat"].split()[1]          # "b phanh <he> ..." -> "phanh"
    import b as B
    assert lenh in B.LENH, "`b %s` khong co trong bang lenh" % lenh


def test_phanh_nam_trong_do_het():
    """Phep do phai NAM TRONG `do_het`, khong chi ton tai."""
    import inspect
    assert "suc_khoe_phanh" in inspect.getsource(E.do_het)


def test_cat_nghia_co_cho_moi_chi_so_xau():
    """Moi chi so co the XAU deu phai co cat nghia - khong de nguoi doc tu doan."""
    for ten in ("phanh.chua_khai", "phanh.vua_ngat"):
        assert ten in E.CAT_NGHIA and E.CAT_NGHIA[ten].strip()


def test_dat_han_muc_tu_choi_so_khong_duong():
    """Phanh mac dinh la BAT: khai thieu / khai 0 thi khong nhan."""
    assert HM.dat("he_thu", 0.0, 10, 1.0, 1000.0)["nhan"] is False
    assert HM.dat("he_thu", 0.2, 0, 1.0, 1000.0)["nhan"] is False


def test_chua_khai_thi_khong_duoc_vao_lenh():
    """Quen khai = khong chay, chu khong phai = chay khong gioi han."""
    duoc, ly = HM.duoc_vao_lenh("he_chua_bao_gio_khai_han_muc_xyz")
    assert duoc is False and ly
