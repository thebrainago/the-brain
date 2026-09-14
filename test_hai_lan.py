# -*- coding: utf-8 -*-
"""Test HAI LAN cua `nhan/uu_tien.py` (ban giao 13/09 muc 11).

Hai lan chi co gia tri neu CAI CHAN cua no that. Nen bo test nay chu yeu do
chieu NGUOC: chan co tu choi dung nhung viec phai tu choi khong, va co cho qua
dung nhung viec du dieu kien khong. Mot cai chan luon cho qua, hay mot cai chan
tu choi tat ca, deu cho bang so lieu y het nhau.
"""
from __future__ import annotations

import json

import pytest

from nhan import uu_tien as UT


@pytest.fixture
def bang(tmp_path, monkeypatch):
    p = tmp_path / "HAI_LAN.json"
    monkeypatch.setattr(UT, "_BANG_LAN", p)
    return p


def viec_du_chuan(**doi):
    d = {"qua_holdout_that": True, "hon_moc_cung_rui_ro": True,
         "do_tin_chi_phi": "SAN", "chay_duoc_that": True}
    d.update(doi)
    return d


# ------------------------------------------------------------ BON LUAT VAO
def test_du_bon_luat_thi_vao_duoc():
    ok, thieu = UT.du_dieu_kien_lan_nhanh(viec_du_chuan())
    assert ok and thieu == []


@pytest.mark.parametrize("bo", ["qua_holdout_that", "hon_moc_cung_rui_ro",
                                "chay_duoc_that"])
def test_thieu_bat_ky_luat_nao_cung_bi_chan(bo):
    ok, thieu = UT.du_dieu_kien_lan_nhanh(viec_du_chuan(**{bo: False}))
    assert not ok and len(thieu) == 1


def test_chi_phi_KHAI_bi_chan():
    """Luat cua du an: `do_tin = KHAI` thi khong bao gio PASS - ke ca o day."""
    ok, thieu = UT.du_dieu_kien_lan_nhanh(viec_du_chuan(do_tin_chi_phi="KHAI"))
    assert not ok
    assert any("do_tin" in x for x in thieu)


def test_do_tin_DO_cung_bi_chan():
    """Chi 'SAN' moi duoc. 'DO' la do tu du lieu nghien cuu, khong phai bang gia san."""
    ok, _ = UT.du_dieu_kien_lan_nhanh(viec_du_chuan(do_tin_chi_phi="DO"))
    assert not ok


# ------------------------------------------------------------------ WIP
def test_tran_wip_chan_viec_thu_tu(bang):
    for i in range(UT.WIP_LAN_NHANH):
        r = UT.them_viec_lan(f"he_{i}", "nhanh", **viec_du_chuan())
        assert r["nhan"], r
    r = UT.them_viec_lan("he_qua_tran", "nhanh", **viec_du_chuan())
    assert not r["nhan"]
    assert "WIP" in r["ly_do"][0]


def test_lan_cham_khong_co_tran(bang):
    for i in range(UT.WIP_LAN_NHANH + 5):
        assert UT.them_viec_lan(f"xay_{i}", "cham")["nhan"]
    assert len(UT._doc_lan()["cham"]) == UT.WIP_LAN_NHANH + 5


def test_khong_nhan_trung_ten(bang):
    assert UT.them_viec_lan("x", "cham")["nhan"]
    assert not UT.them_viec_lan("x", "cham")["nhan"]


# ------------------------------------------------------------- HAN CHOT
def test_viec_lan_nhanh_luon_co_han(bang):
    UT.them_viec_lan("he_a", "nhanh", **viec_du_chuan())
    assert UT._doc_lan()["nhanh"][0]["han"]


def test_het_han_bat_dung_viec_qua_han(bang):
    UT.them_viec_lan("moi", "nhanh", han_ngay=30, **viec_du_chuan())
    UT.them_viec_lan("cu", "nhanh", han_ngay=-1, **viec_du_chuan())
    ten = {v["ten"] for v in UT.het_han()}
    assert ten == {"cu"}


def test_tra_ve_kho_giai_phong_suat_wip(bang):
    for i in range(UT.WIP_LAN_NHANH):
        UT.them_viec_lan(f"he_{i}", "nhanh", **viec_du_chuan())
    assert not UT.them_viec_lan("moi", "nhanh", **viec_du_chuan())["nhan"]
    assert UT.tra_ve_kho("he_0")
    assert UT.them_viec_lan("moi", "nhanh", **viec_du_chuan())["nhan"]
    d = UT._doc_lan()
    assert len(d["kho"]) == 1 and d["kho"][0]["ly_do_tra"]


def test_tra_ve_kho_ten_khong_co_thi_tra_False(bang):
    assert UT.tra_ve_kho("khong_ton_tai") is False


def test_bang_lan_in_duoc_khi_rong(bang):
    dong = []
    d = UT.bang_lan(in_ra=dong.append)
    assert d == {"nhanh": [], "cham": [], "kho": []}
    assert any("LAN NHANH" in x for x in dong)
