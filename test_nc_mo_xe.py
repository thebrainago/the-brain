# -*- coding: utf-8 -*-
"""Mo xe lenh + tim quy luat: hieu chuan HAI chieu tren du lieu biet truoc dap an.

Chieu 1: edge cai san phai duoc tim ra. Chieu 2: nhieu trang KHONG duoc thanh phat hien.
Mot bo do chi qua mot chieu thi doc y het mot bo do tot (luat du an).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from nhan import nc_dac_trung as DT
from nhan import nc_du_lieu as NDL
from nhan import nc_mo_xe as MX
from nhan import ngu_phap as NP


def _df(n=40):
    idx = pd.date_range("2020-01-01", periods=n, freq="4h")
    o = np.linspace(1.0, 1.0 + 0.001 * (n - 1), n)
    return pd.DataFrame({"open": o, "high": o * 1.001, "low": o * 0.999, "close": o}, index=idx)


def test_tach_lenh_cong_ca_phi_thoat_o_bar_sau_doan():
    df = _df()
    v = np.zeros(40)
    v[5:9] = 1.0                        # lenh 1: bar 5..8, thoat o bar 9
    v[20:23] = -1.0                     # lenh 2
    lt = np.full(40, 0.001) * v
    phi = np.zeros(40)
    phi[5], phi[9] = 0.0002, 0.0002     # vao, ra lenh 1
    phi[20], phi[23] = 0.0003, 0.0003
    lr = lt - phi
    L = MX.tach_lenh(df, v, lt, lr)
    assert len(L) == 2
    assert L.iloc[0]["loi"] == pytest.approx(4 * 0.001 - 0.0004)
    assert L.iloc[1]["loi"] == pytest.approx(-0.003 - 0.0006)   # lenh ban, gia di len
    assert list(L["tin_hieu"]) == [4, 19] and list(L["chieu"]) == [1, -1]


def test_tach_lenh_lat_chieu_chia_phi_cua_bar_lat():
    df = _df()
    v = np.zeros(40)
    v[5:8] = 1.0
    v[8:11] = -1.0                      # lat chieu o bar 8: phi bar 8 la HAI chan
    lt = np.zeros(40)
    phi = np.zeros(40)
    phi[5], phi[8], phi[11] = 0.0001, 0.0002, 0.0001
    L = MX.tach_lenh(df, v, lt, lt - phi)
    assert len(L) == 2
    assert L["loi"].sum() == pytest.approx(-phi.sum())


def _lenh_gia(n=300, hat=1, co_edge=True):
    rng = np.random.default_rng(hat)
    X = pd.DataFrame({"atr_pv": rng.uniform(0, 1, n), "z20": rng.normal(0, 1, n),
                      "thu": rng.integers(0, 5, n).astype(float)})
    y = rng.normal(0, 0.01, n)
    if co_edge:
        y = y + np.where(X["atr_pv"] < 0.4, 0.006, -0.004)
    L = pd.DataFrame({"loi": y, "mfe_atr": np.abs(rng.normal(1, 0.5, n)),
                      "mae_atr": -np.abs(rng.normal(1, 0.5, n)), "so_bar": 5, "bar_mfe": 2,
                      "mfe": 0.01, "mae": -0.01})
    return L, X


def test_mo_xe_tim_ra_bo_loc_cai_san():
    L, X = _lenh_gia(co_edge=True)
    r = MX.mo_xe_lenh(L, X, so_null=100)
    tot = r["luat_loc"][0]
    assert r["trang_thai"] == "DAT"
    assert tot["dieu_kien"].startswith("atr_pv <")
    assert tot["p_null"] <= 0.02
    assert tot["t_sau_loc"] > (r["tong_quan"]["t_lenh"] or 0)
    # dieu kien tra ve phai la DSL HOP LE - noi vao `vao` la chay duoc
    assert tot["dsl"][0]["phep"] == "<" and "hang" in tot["dsl"][0]["phai"]
    assert tot["dsl"][0]["trai"] == DT.toan_hang("atr_pv")
    # cot khong phai dac trung ngu phap -> khong bia DSL
    X2 = X.rename(columns={"atr_pv": "cot_tu_dung"})
    r2 = MX.mo_xe_lenh(L, X2, so_null=20)
    assert r2["luat_loc"][0]["dsl"] == [None]


@pytest.mark.parametrize("hat", [1, 2, 3])
def test_mo_xe_KHONG_bia_bo_loc_tren_nhieu(hat):
    L, X = _lenh_gia(hat=hat, co_edge=False)
    r = MX.mo_xe_lenh(L, X, so_null=100, hat=hat)
    assert r["trang_thai"] != "DAT" or r["luat_loc"][0]["p_null"] > 0.01


def test_mo_xe_it_lenh_la_CHUA_DO_DUOC_khong_phai_AM():
    L, X = _lenh_gia(n=20)
    assert MX.mo_xe_lenh(L, X, so_null=10)["trang_thai"] == "CHUA_DO_DUOC"


def test_phan_tich_thoat_goi_y_luat_dung_nut_cua_dap_quan_tri():
    from nhan import dap_quan_tri as DQT
    L, _ = _lenh_gia()
    r = MX.phan_tich_thoat(L)
    assert r["trang_thai"] == "DAT"
    for g in r["goi_y_quan_tri"]:
        assert set(g["luat"]) <= set(DQT.NUT)


def _kham_pha(ma):
    d = NDL.nap(ma, "H4")
    pre, a = NDL.cat_doan(d, "kham_pha")
    return pre, a, DT.tinh(pre), NDL.chi_phi(ma, pre)


def test_tim_quy_luat_nhieu_thuan_khong_ra_luat_dat():
    pre, a, X, cp = _kham_pha("TONG_HOP_NHIEU_1")
    r = MX.tim_quy_luat(pre, X, cp, bat_dau=a, so_null=100, bar_moi_ngay=6)
    assert r["trang_thai"] == "AM"
    assert r["luat"][0]["p_null"] > 0.05


def test_tim_quy_luat_tim_ra_hoi_quy_co_dieu_kien_va_spec_hop_le():
    pre, a, X, cp = _kham_pha("TONG_HOP_HOI_QUY_1")
    r = MX.tim_quy_luat(pre, X, cp, bat_dau=a, so_null=100, bar_moi_ngay=6)
    tot = r["luat"][0]
    assert r["trang_thai"] == "DAT", r["luat"][:2]
    assert tot["chieu"] == 1 and tot["p_null"] <= 0.02
    assert NP.kiem_khai_bao(tot["spec"]) == []
    ok, _ = NP.kiem_khong_nhin_truoc(tot["spec"], pre)
    assert ok


def test_dac_trung_khong_nhin_truoc():
    """Moi dac trung la toan hang ngu phap - kiem lai bang PHEP CAT."""
    d = NDL.nap("TONG_HOP_NHIEU_1", "H4").iloc[:1500]
    full = DT.tinh(d)
    for t in (700, 1100, 1499):
        cat = DT.tinh(d.iloc[:t + 1])
        for c in full.columns:
            if c in cat.columns:
                a, b = full[c].iloc[t], cat[c].iloc[t]
                assert (np.isnan(a) and np.isnan(b)) or a == pytest.approx(b), (c, t)
