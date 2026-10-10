# -*- coding: utf-8 -*-
from nhan import guong_dsl as G

MUA = {"ten": "a_mua", "chieu": 1, "giu": 5,
       "vao": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<", "phai": {"hang": 30}},
               {"trai": {"chi_bao": "ema", "n": 9}, "phep": ">", "phai": {"chi_bao": "ema", "n": 21}}],
       "ra": [{"trai": {"chi_bao": "gia", "cot": "close"}, "phep": "<", "phai": {"chi_bao": "thap_nhat_cua_cac", "n": 10}}]}


def test_guong_dung_nghia():
    b = G.guong(MUA)
    assert b["chieu"] == -1 and b["ten"] == "a_ban"
    assert b["vao"][0] == {"trai": {"chi_bao": "rsi", "n": 14}, "phep": ">", "phai": {"hang": 70}}
    assert b["vao"][1]["phep"] == "<"
    assert b["ra"][0]["phai"]["chi_bao"] == "cao_nhat_cua_cac" and b["ra"][0]["phep"] == ">"


def test_guong_hai_lan_ve_nguyen_ban():
    b = G.guong(G.guong(MUA))
    assert b["vao"] == MUA["vao"] and b["ra"] == MUA["ra"] and b["chieu"] == 1


def test_khong_doan_khi_chua_biet_lat():
    s = {"ten": "x", "chieu": 1, "giu": 3, "vao": [{"trai": {"chi_bao": "macd"}, "phep": ">", "phai": {"hang": 0}}], "ra": []}
    assert G.guong(s) is None


def test_khong_sua_ban_goc():
    import copy
    c = copy.deepcopy(MUA)
    G.guong(MUA)
    assert MUA == c


def test_dieu_kien_trung_tinh_giu_nguyen():
    s = {"ten": "x_mua", "chieu": 1, "giu": 3, "vao": [{"trai": {"chi_bao": "adx", "n": 14}, "phep": ">", "phai": {"hang": 25}},
                                                       {"trai": {"chi_bao": "gio"}, "phep": ">=", "phai": {"hang": 7}}], "ra": []}
    b = G.guong(s)
    assert b["vao"] == s["vao"] and b["chieu"] == -1


def test_kenh_donchian_doi_ca_cot_va_khong_lat_keltner():
    s = {"ten": "d_mua", "chieu": 1, "giu": 3, "vao": [{"trai": {"chi_bao": "gia", "cot": "close"}, "phep": ">",
         "phai": {"chi_bao": "cao_nhat_cua_cac", "cua": {"chi_bao": "gia", "cot": "high"}, "n": 20}}], "ra": []}
    b = G.guong(s)
    assert b["vao"][0]["phai"] == {"chi_bao": "thap_nhat_cua_cac", "cua": {"chi_bao": "gia", "cot": "low"}, "n": 20}
    k = {"ten": "k_mua", "chieu": 1, "giu": 3, "vao": [{"trai": {"chi_bao": "gia", "cot": "close"}, "phep": "<", "phai": {"chi_bao": "keltner", "n": 20}}], "ra": []}
    assert G.guong(k) is None
