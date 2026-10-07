# -*- coding: utf-8 -*-
from nhan import cmt_prior as C

RSI = {"vao": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<", "phai": 30}]}
STO = {"vao": [{"trai": {"chi_bao": "stochastic", "n": 14}, "phep": "<", "phai": 20}]}
EMA = {"vao": [{"trai": {"chi_bao": "ema", "n": 20, "cua": {"chi_bao": "gia"}}, "phep": ">", "phai": {"chi_bao": "sma", "n": 50}}]}
VOL = {"vao": [{"trai": {"chi_bao": "obv"}, "phep": ">", "phai": 0}]}


def test_cung_ho_gop_mot_phep_thu():
    r = C.loc([RSI, STO, EMA])
    assert r["so_spec"] == 3 and r["so_phep_thu_hieu_dung"] == 2


def test_uu_tien_theo_che_do():
    assert C.loc([EMA, RSI], "hoi_quy")["cum"][0]["dai_dien"] == 1
    assert C.loc([EMA, RSI], "quan_tinh")["cum"][0]["dai_dien"] == 0


def test_canh_bao_khoi_luong_va_xac_nhan_khong_doc_lap():
    assert any("tick volume" in w for w in C.canh_bao(VOL))
    hai = {"vao": [RSI["vao"][0], STO["vao"][0]]}
    assert any("xac_nhan_khong_doc_lap" in w for w in C.canh_bao(hai))
    doc_lap = {"vao": [RSI["vao"][0], EMA["vao"][0]]}
    assert not any("xac_nhan" in w for w in C.canh_bao(doc_lap))


def test_moi_chi_bao_co_that_deu_duoc_xep_ho_hoac_nen_tang():
    from nhan import ngu_phap as N
    chua = sorted(c for c in N.CHI_BAO_CO if c not in C.TEN_HO and c not in C.NEN_TANG)
    assert chua == [], chua
