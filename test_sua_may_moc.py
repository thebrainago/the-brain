# -*- coding: utf-8 -*-
"""Test G3-C: sua HINH THUC truoc cong, va khong duoc sua NOI DUNG.

Ranh gioi la toan bo gia tri cua bo sua nay. Sua cach viet (`quay_ve_trung_bình`
-> `quay_ve_trung_binh`) thi cuu duoc mot khai bao dung. Sua noi dung (lam mot
dieu kien suy bien het suy bien) thi che ra mot "phat hien" chua ai tung viet.
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import boc_ma_llm as B  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402
from nhan import pham_vi as PV  # noqa: E402


def test_bo_dau_ten_ho():
    c, da = B.sua_may_moc({"ho": "quay_ve_trung_bình"})
    assert c["ho"] == "quay_ve_trung_binh"
    assert c["ho"] in PV.PHAM_VI
    assert da


def test_khong_doan_ten_ho_khac_han():
    """`pha_vào` khong phai `pha_vo` chi khac dau - dung doan."""
    c, _ = B.sua_may_moc({"ho": "pha_vào"})
    assert c["ho"] == "pha_vào", "bo dau ra 'pha_vao', khong co trong bang -> giu nguyen"


def test_ho_dung_roi_thi_khong_dong_vao():
    c, da = B.sua_may_moc({"ho": "xu_huong"})
    assert c["ho"] == "xu_huong" and not any("ho " in x for x in da)


def test_co_che_giu_cau_dau():
    c, _ = B.sua_may_moc({"co_che": "Cau mot. Cau hai. Cau ba."})
    assert c["co_che"] == "Cau mot."


def test_toan_hang_chuoi_gia_thanh_dict():
    c, _ = B.sua_may_moc({"vao": [{"trai": "close", "phep": ">", "phai": 3}]})
    assert c["vao"][0]["trai"] == {"chi_bao": "gia", "cot": "close"}
    assert c["vao"][0]["phai"] == {"so": 3}


def test_n_so_thuc_va_chuoi_thanh_so_nguyen():
    c, _ = B.sua_may_moc({"vao": [{"trai": {"chi_bao": "sma", "n": 20.0},
                                   "phep": ">",
                                   "phai": {"chi_bao": "sma", "n": "50"}}]})
    assert c["vao"][0]["trai"]["n"] == 20 and isinstance(c["vao"][0]["trai"]["n"], int)
    assert c["vao"][0]["phai"]["n"] == 50


def test_bo_ve_khong_doc_duoc_NHUNG_danh_dau():
    c, da = B.sua_may_moc({"vao": [
        {"trai": {"chi_bao": "gia", "cot": "close"}, "phep": ">",
         "phai": {"chi_bao": "sma", "n": 20}},
        "khong_dien_dat_duoc"]})
    assert len(c["vao"]) == 1
    assert c["khong_day_du"] is True and c["so_ve_mat"] == 1, \
        "bo ve ma khong danh dau = che ra mot co che khong co trong ma nguon"
    assert any("khong_day_du" in x for x in da)


def test_moi_ve_deu_hong_thi_GIU_NGUYEN_cho_cong_tu_choi():
    c, _ = B.sua_may_moc({"vao": ["khong_dien_dat_duoc", "khong_dien_dat_duoc"]})
    assert c["vao"] == ["khong_dien_dat_duoc", "khong_dien_dat_duoc"]
    assert not c.get("khong_day_du")


def test_KHONG_sua_dieu_kien_suy_bien():
    """`close > high` LUON sai - phai de cong tu choi, khong duoc 'sua'."""
    goc = {"ten": "x", "ho": "xu_huong", "chieu": 1, "giu": 5,
           "co_che": "mot cau dai hon hai lam ky tu de qua kiem do dai",
           "vao": [{"trai": {"chi_bao": "gia", "cot": "close"}, "phep": ">",
                    "phai": {"chi_bao": "gia", "cot": "high"}}]}
    c, _ = B.sua_may_moc(goc)
    assert c["vao"][0]["phai"] == {"chi_bao": "gia", "cot": "high"}
    assert NP.kiem_khai_bao(c), "dieu kien suy bien VAN phai bi cong tu choi"


def test_khong_doi_ban_goc():
    goc = {"ho": "quay_ve_trung_bình", "vao": [{"trai": "close"}]}
    B.sua_may_moc(goc)
    assert goc["ho"] == "quay_ve_trung_bình", "phai lam tren ban sao"
    assert goc["vao"][0]["trai"] == "close"
