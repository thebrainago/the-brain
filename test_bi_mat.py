# -*- coding: utf-8 -*-
"""Test cho `nhan/bi_mat.py` — MOT CUA doc khoa.

Module nay ton tai de khoa khong bi ro ri, nen bo test cua no phai do dung dieu
do chu khong chi do "lay duoc gia tri khong". Ba tinh chat:

  1. `co()` tra loi duoc cau hoi "co khoa chua" **ma khong tra ve khoa**. Day la
     ham duy nhat duoc phep xuat hien trong bao cao / mach dap.
  2. Thieu khoa thi tra ve mac dinh chu KHONG NEM - mot ngoai le mang theo
     duong dan khoa vao traceback la mot cach ro ri.
  3. `khoi_common_ini` tra CHUOI RONG khi thieu login/mat khau. Neu no tra ve
     mot khoi `[Common]` khuyet thi luot tester chet voi *"tester not started
     because the account is not specified"* - loi do da mat mot lan truy 13/09.
"""
from __future__ import annotations

import json

import pytest

from nhan import bi_mat as BM


@pytest.fixture
def kho(tmp_path, monkeypatch):
    p = tmp_path / "tai_khoan.json"
    monkeypatch.setattr(BM, "KHO", p)
    return p


def ghi(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------------------------ lay / co
def test_lay_theo_duong_nhieu_tang(kho):
    ghi(kho, {"github": {"token": "abc123"}})
    assert BM.lay("github", "token") == "abc123"


def test_lay_thieu_khoa_tra_mac_dinh_chu_KHONG_NEM(kho):
    """Ngoai le mang duong dan file khoa vao traceback cung la mot kieu ro ri."""
    ghi(kho, {})
    assert BM.lay("github", "token") is None
    assert BM.lay("khong", "co", "gi", mac_dinh="X") == "X"


def test_lay_file_khong_ton_tai_khong_nem(kho):
    assert not kho.exists()
    assert BM.lay("github", "token") is None


def test_lay_file_HONG_khong_nem(kho):
    """JSON hong khong duoc lam do ca day chuyen - va khong duoc in noi dung ra."""
    kho.write_text("{ khong phai json", encoding="utf-8")
    assert BM.lay("github", "token") is None


def test_chuoi_rong_duoc_coi_nhu_KHONG_CO(kho):
    """Khoa rong la chua khai bao, khong phai da khai bao bang chuoi rong."""
    ghi(kho, {"github": {"token": ""}})
    assert BM.lay("github", "token") is None
    assert BM.co("github", "token") is False


def test_co_tra_ve_BOOL_chu_khong_tra_ve_khoa(kho):
    """Tinh chat quan trong nhat cua module: hoi duoc ma khong lo ra."""
    ghi(kho, {"github": {"token": "sieu_bi_mat"}})
    r = BM.co("github", "token")
    assert r is True
    assert isinstance(r, bool)
    assert "sieu_bi_mat" not in repr(r)


def test_di_xuyen_qua_gia_tri_khong_phai_dict_thi_dung_lai(kho):
    ghi(kho, {"github": "chuoi_chu_khong_phai_dict"})
    assert BM.lay("github", "token") is None


# ------------------------------------------------------------- token_github
def test_bien_moi_truong_duoc_uu_tien_hon_kho(kho, monkeypatch):
    ghi(kho, {"github": {"token": "trong_kho"}})
    monkeypatch.setenv("GITHUB_TOKEN", "tu_moi_truong")
    assert BM.token_github() == "tu_moi_truong"


def test_roi_ve_kho_khi_khong_co_bien_moi_truong(kho, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    ghi(kho, {"github": {"token": "trong_kho"}})
    assert BM.token_github() == "trong_kho"


def test_dau_github_rong_khi_khong_co_token(kho, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    ghi(kho, {})
    assert BM.dau_github() == {}


def test_dau_github_dung_dang_Bearer(kho, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    assert BM.dau_github() == {"Authorization": "Bearer t"}


# --------------------------------------------------------- khoi_common_ini
def test_khoi_common_ini_du_ba_dong_khi_co_khoa(kho):
    ghi(kho, {"mt5": {"XM": {"login": 123, "mat_khau": "mk",
                             "server_chay_duoc": "XMGlobal-MT5 17"}}})
    s = BM.khoi_common_ini("XM")
    assert "[Common]" in s and "Login=123" in s and "Server=XMGlobal-MT5 17" in s


def test_khoi_common_ini_RONG_khi_thieu_mat_khau(kho):
    """Khoi khuyet con te hon khong co: tester chet voi 'account is not specified'."""
    ghi(kho, {"mt5": {"XM": {"login": 123}}})
    assert BM.khoi_common_ini("XM") == ""


def test_khoi_common_ini_RONG_khi_khong_co_san_do(kho):
    ghi(kho, {"mt5": {}})
    assert BM.khoi_common_ini("SAN_LA") == ""


def test_khoi_common_ini_lay_server_dau_khi_chua_biet_cai_nao_chay_duoc(kho):
    ghi(kho, {"mt5": {"XM": {"login": 1, "mat_khau": "m",
                             "servers": ["A", "B"]}}})
    assert "Server=A" in BM.khoi_common_ini("XM")
