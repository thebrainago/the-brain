# -*- coding: utf-8 -*-
"""Test vong SUA bang LLM: khong goi mang, chi kiem HANH VI quanh no.

Cai dang so nhat khong phai loi cua LLM ma la duong SUA tro thanh mot cua sau
di vong qua cong: ban sua PHAI qua `kiem_khai_bao` y het ban goc.
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import boc_ma_llm as B  # noqa: E402

HONG = {"ten": "x", "ho": "xu_huong", "chieu": 1, "giu": 5, "co_che": "ngan",
        "vao": [{"trai": {"chi_bao": "gia", "cot": "close"}, "phep": ">",
                 "phai": {"chi_bao": "gia", "cot": "high"}}]}
DAT = {"ten": "x", "ho": "xu_huong", "chieu": 1, "giu": 5,
       "co_che": "Ben doi ung la quy phong ho buoc phai dong vi the khi cham "
                 "nguong rui ro noi bo, nen ho tra gia de thoat.",
       "vao": [{"trai": {"chi_bao": "gia", "cot": "close"}, "phep": ">",
                "phai": {"chi_bao": "sma", "n": 20}}]}


def test_khong_bat_sua_thi_khong_goi_mang(monkeypatch):
    goi = {"n": 0}

    def cam(*a, **k):
        goi["n"] += 1
        return None, "khong duoc goi"
    monkeypatch.setattr(B, "sua_bang_llm", cam)
    B.kiem_va_giu([dict(HONG)], nguon="t")
    assert goi["n"] == 0, "mac dinh phai KHONG goi LLM"


def test_ban_sua_van_phai_qua_cong(monkeypatch):
    """LLM tra ve mot ban VAN HONG -> khong duoc vao kho."""
    monkeypatch.setattr(B, "sua_bang_llm", lambda *a, **k: (dict(HONG), ""))
    giu, ho = B.kiem_va_giu([dict(HONG)], nguon="t", sua_llm=True)
    assert giu == [] and ho, "ban sua hong van phai bi tu choi"


def test_ban_sua_dat_thi_duoc_vao_va_co_dau_vet(monkeypatch):
    monkeypatch.setattr(B, "sua_bang_llm", lambda *a, **k: (dict(DAT), ""))
    giu, ho = B.kiem_va_giu([dict(HONG)], nguon="t", sua_llm=True)
    assert len(giu) == 1 and not ho
    assert giu[0]["da_sua_bang_llm"] is True, \
        "phai co dau vet: ban nay do LLM sua, khong phai boc truc tiep"


def test_chi_goi_LLM_MOT_lan_cho_moi_khai_bao(monkeypatch):
    n = {"lan": 0}

    def dem(*a, **k):
        n["lan"] += 1
        return dict(HONG), ""          # luon tra ban hong
    monkeypatch.setattr(B, "sua_bang_llm", dem)
    B.kiem_va_giu([dict(HONG)], nguon="t", sua_llm=True)
    assert n["lan"] == 1, "mot vong sua khong gioi han la cach dot tien"


def test_LLM_tra_chuoi_thay_vi_dict_khong_lam_vo_me(monkeypatch):
    """Sap that 16/09: AttributeError 'str' object has no attribute 'get'."""
    monkeypatch.setattr(B, "sua_bang_llm", lambda *a, **k: (None, "khong phai dict"))
    giu, ho = B.kiem_va_giu([dict(HONG)], nguon="t", sua_llm=True)
    assert giu == [] and len(ho) == 1


def test_khai_bao_dat_san_thi_khong_goi_sua(monkeypatch):
    goi = {"n": 0}

    def dem(*a, **k):
        goi["n"] += 1
        return None, ""
    monkeypatch.setattr(B, "sua_bang_llm", dem)
    giu, _ = B.kiem_va_giu([dict(DAT)], nguon="t", sua_llm=True)
    assert len(giu) == 1 and goi["n"] == 0


def test_loi_nhac_sua_co_ca_khai_bao_lan_loi():
    s = B._nhac_sua("EA.mq5", HONG, ["vao[0]: hai ve GIONG HET nhau"])
    assert "EA.mq5" in s and "GIONG HET" in s and "xu_huong" in s
    assert "Khong duoc doi co che" in s, "phai co rang buoc giu nguyen y nghia"
