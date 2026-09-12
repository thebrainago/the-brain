# -*- coding: utf-8 -*-
"""test_suy_giam.py - He dang chay co con giong cai da kiem dinh khong.

`nhan/suy_giam.py` ra doi 11/09 nhung chua co test - `test_hien_phap` bat duoc
12/09. No la module se phai chay MOI NGAY khi he cam VPS nhieu thang, nen ba
dieu duoi day phai duoc chan bang test chu khong phai bang niem tin:

  * **`CHUA_DO_DUOC` khong phai `SUY_GIAM`.** Voi n nho thi khong the phan biet
    "edge chet" voi "xui" - va goi nham la cach vut mot he tot vi mot chuoi
    binh thuong ([[ket-luan-am-phai-phan-biet-CHUA-DO]]).
  * **Hieu chuan hai chieu.** Mot bo do khong bao gio keu cho so lieu y het mot
    bo do tot. Phai co ca ca "phai keu" lan "khong duoc keu".
  * **`n_can` phai co that.** Khong co no thi moi ket luan "he da chet" la doan.
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import nhan.so_lenh as SL                  # noqa: E402
from nhan import suy_giam as SG            # noqa: E402


def _gia_lenh(monkeypatch, cac_r):
    monkeypatch.setattr(
        SL, "lenh_cua",
        lambda he, con_mo=False: [{"r": r} for r in cac_r])


# ------------------------------------------------------------------ n_can
def test_n_can_tang_khi_nhieu_lon_hon():
    """Chuoi nhieu hon thi can nhieu lenh hon moi thay duoc cung cu hut."""
    it = SG.n_can(tb_bt=0.10, sd_bt=1.0)
    nhieu = SG.n_can(tb_bt=0.10, sd_bt=2.0)
    assert nhieu > it


def test_n_can_none_khi_khong_tinh_duoc():
    assert SG.n_can(tb_bt=0.0, sd_bt=1.0) is None
    assert SG.n_can(tb_bt=0.1, sd_bt=0.0) is None


# ------------------------------------------- CHUA_DO_DUOC vs SUY_GIAM
def test_it_lenh_thi_CHUA_DO_DUOC_chu_khong_phai_SUY_GIAM(monkeypatch):
    """Ba lenh thua lien tiep KHONG duoc goi la he chet."""
    _gia_lenh(monkeypatch, [-1.0, -1.0, -1.0])
    k = SG.do("he_x", tb_bt=0.10, sd_bt=1.0)
    assert k["trang_thai"] == "CHUA_DO_DUOC"
    assert k["n"] == 3 and k["n_can"] and k["n_can"] > 3
    assert "CHUA du luc" in k["mo_ta"]


def test_khong_co_lenh_nao_thi_CHUA_DO_DUOC(monkeypatch):
    _gia_lenh(monkeypatch, [])
    assert SG.do("he_x", 0.10, 1.0)["trang_thai"] == "CHUA_DO_DUOC"


# ------------------------------------------------ hieu chuan hai chieu
def test_du_luc_va_that_su_te_thi_keu_SUY_GIAM(monkeypatch):
    """Chieu 1: edge chet that thi PHAI keu."""
    n = SG.n_can(tb_bt=0.10, sd_bt=1.0)
    _gia_lenh(monkeypatch, [-0.30] * (n + 50))
    k = SG.do("he_x", tb_bt=0.10, sd_bt=1.0)
    assert k["trang_thai"] == "SUY_GIAM"
    assert k["t"] < SG.NGUONG_T


def test_du_luc_va_chay_dung_ky_vong_thi_BINH_THUONG(monkeypatch):
    """Chieu 2: he chay dung nhu backtest thi KHONG duoc keu.

    Khong co phep thu nay thi mot ham `return "SUY_GIAM"` cung qua test tren.
    """
    n = SG.n_can(tb_bt=0.10, sd_bt=1.0)
    _gia_lenh(monkeypatch, [0.10] * (n + 50))
    k = SG.do("he_x", tb_bt=0.10, sd_bt=1.0)
    assert k["trang_thai"] == "BINH_THUONG"


def test_chay_TOT_hon_backtest_cung_khong_keu(monkeypatch):
    """`t` mot phia: lai hon ky vong khong phai la suy giam."""
    n = SG.n_can(tb_bt=0.10, sd_bt=1.0)
    _gia_lenh(monkeypatch, [0.40] * (n + 50))
    assert SG.do("he_x", 0.10, 1.0)["trang_thai"] == "BINH_THUONG"


# ------------------------------------------------------------------ quet
def test_quet_dem_dung_so_he_suy_giam(monkeypatch):
    n = SG.n_can(tb_bt=0.10, sd_bt=1.0)

    def gia(he, con_mo=False):
        r = -0.30 if he == "xau" else 0.10
        return [{"r": r}] * (n + 50)

    monkeypatch.setattr(SL, "lenh_cua", gia)
    k = SG.quet({"xau": (0.10, 1.0), "tot": (0.10, 1.0)})
    assert k["so_he"] == 2 and k["so_suy_giam"] == 1


def test_bo_qua_lenh_chua_dong(monkeypatch):
    """Lenh `r is None` (chua dong) khong duoc tinh vao thong ke."""
    monkeypatch.setattr(
        SL, "lenh_cua",
        lambda he, con_mo=False: [{"r": 0.1}, {"r": None}, {"r": 0.1}])
    assert SG.do("he_x", 0.10, 1.0)["n"] == 2
