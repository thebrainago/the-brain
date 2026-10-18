# -*- coding: utf-8 -*-
"""Sai so mo phong lam dep ket qua (ra soat 18/10/2026). Moi test la mot loi THAT da do duoc:

1. Chay tai khoan bi ghi la thang (bar chay mang log 0).
2. Lenh BAN duoc tang ~ phuong sai moi bar (cong don log).
3. SL bi nhay qua (gap) van khop o gia SL.
4. Stress "chi phi x2" khong doi gi (sai ten khoa; spread theo nam triet tieu he so).
5. Spread gio rollover khong bao gio bi tinh.
(the-brain: chua co mo hinh phi theo nua dem P3 - muc 6 cua brain2 khong ap dung o day.)
"""
import numpy as np
import pandas as pd

from nhan import chi_phi as CP, do_luong as DO, mo_phong as MP, sang_loc as SL


def _df(gia, freq="D", bat_dau="2020-01-06"):
    gia = np.asarray(gia, float)
    idx = pd.date_range(bat_dau, periods=len(gia), freq=freq)
    return pd.DataFrame({"open": gia, "high": gia * 1.001, "low": gia * 0.999, "close": gia}, index=idx)


def _cp0(ma="US500CASH", **kw):
    return CP.MoHinhChiPhi(ma=ma, do_tin="DO", **kw)


def test_chay_tai_khoan_khong_duoc_ghi_la_thang():
    gia = np.r_[np.linspace(100, 160, 60), 96.0, np.linspace(96, 120, 40)]
    kq = MP.chay(_df(gia), np.ones(len(gia)), _cp0(), don_bay=3.0)
    assert kq.chay_tai_khoan
    cs = DO.chi_so(kq.loi, kq.index)
    assert cs["tong_lai_pct"] <= -99.0 and cs["max_dd_pct"] <= -99.0


def test_ban_khong_duoc_tang_phuong_sai():
    rng = np.random.default_rng(1)
    r = rng.normal(0, 0.011, 2000)
    gia = 100 * np.exp(np.cumsum(r))
    df = _df(gia)
    kq = MP.chay(df, -np.ones(len(gia)), _cp0())          # mac dinh "tu_dong"
    ra = np.expm1(MP._loi_suat_tien(df))
    ky_vong = np.sum(np.log1p(-ra[1:]))                   # ban ca von, can bang moi bar (so hoc)
    assert abs(np.sum(kq.loi) - ky_vong) < 1e-9
    kq_log = MP.chay(df, -np.ones(len(gia)), _cp0(), gop="log")
    assert np.sum(kq_log.loi) - ky_vong > 0.1              # ban cu: ~ sum r^2 lai "tu tren troi"


def test_sl_bi_gap_khop_o_open_khong_o_sl():
    gia = [100.0, 100.0, 100.0, 90.0, 90.0, 90.0]
    df = _df(gia)
    th = np.zeros(len(gia))
    th[0] = 1.0                                            # vao mua open bar 1 = 100
    kq = MP.chay_tpsl(df, th, tp_frac=0.10, sl_frac=0.02, cp=_cp0())
    assert abs(np.exp(np.sum(kq.loi)) - 0.90) < 1e-3       # lo ca gap (-10 %), khong phai -2 %


def test_stress_chi_phi_x2_that_su_nhan_doi():
    cp = _cp0(spread_frac_chung=1e-4, spread_frac_theo_gio={10: 1e-4, 0: 8e-4}, truot_gia_frac=2e-5,
              phi_nam_mua=0.05, phi_nam_ban=-0.01)
    cp2 = SL._nhan_doi_chi_phi(cp)
    idx = pd.date_range("2020-03-02 10:00", periods=3, freq="h")
    assert np.allclose(cp2.spread_mang(idx), 2 * cp.spread_mang(idx))
    assert cp2.truot_gia_frac == 2 * cp.truot_gia_frac
    assert cp2.phi_nam_mua == 0.10 and cp2.phi_nam_ban == 0.0  # khoan nhan bi bo, khong nhan doi


def test_spread_gio_rollover_duoc_do_va_bar_ngay_lay_gio_khop():
    idx = pd.date_range("2024-01-01", periods=24 * 400, freq="h")
    idx = idx[idx.dayofweek < 5]
    gia = np.full(len(idx), 1.1)
    sp = np.where(np.isin(idx.hour, [23, 0]), 100.0, 10.0)    # point; rollover rong 10 lan
    df = pd.DataFrame({"open": gia, "high": gia, "low": gia, "close": gia, "spread": sp}, index=idx)
    theo_gio, chung, _ = CP.do_spread("EURUSD", df)
    assert abs(theo_gio[0] / chung - 10.0) < 1e-9 and abs(theo_gio[23] / chung - 10.0) < 1e-9
    cp = _cp0("EURUSD", spread_frac_theo_gio=theo_gio, spread_frac_chung=chung)
    h1 = pd.DatetimeIndex(["2024-03-04 00:00", "2024-03-04 01:00", "2024-03-04 10:00"])
    assert cp.spread_mang(h1)[0] > 9 * cp.spread_mang(h1)[2]         # bar H1 00:00 tra spread rollover
    d1 = pd.date_range("2024-03-04", periods=5, freq="D")
    assert np.allclose(cp.spread_mang(d1), theo_gio[CP.GIO_KHOP_NGAY])  # bar ngay: gio khop that


def test_atr_dat_sl_khong_nhin_bien_do_nen_vao_lenh():
    # 30 nen bien do 1,0; nen VAO LENH (bar 31) bien do 20; bar 32 xuong 98,5. SL 1 ATR tinh tu ATR BIET luc tin
    # hieu (~1,0) -> SL ~99 -> bar 32 cham SL. Ban cu dung atr[31] (~2,4: gom ca nen 31 chua biet luc vao) ->
    # SL ~97,6 -> khong cham.
    from nhan import dap_quan_tri as DQ
    n = 40
    o = np.full(n, 100.0); h = o + 0.5; l = o - 0.5; c = o.copy()
    h[31], l[31] = 110.0, 90.0
    l[32] = 98.5
    df = pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                      index=pd.date_range("2024-01-01", periods=n, freq="D"))
    th = np.zeros(n); th[30] = 1.0
    atr = DQ._atr(df)
    assert atr[31] > 2 * atr[30]
    l0 = DQ.dap(df, th, {"sl_atr": 1.0})["lenh"][0]
    assert l0["vao"] == 31 and l0["ly_do"] == "sl" and l0["ra"] == 32


def test_mo_phong_v2_thong_so_theo_tung_ma_khong_ghim_eurcad():
    import pytest
    import mo_phong_v2 as V2
    bang = {"EURCAD": {"point": 1e-5, "contract_size": 1e5, "phi_nam_mua": 0.01, "phi_nam_ban": 0.005},
            "USDJPY": {"point": 1e-3, "contract_size": 1e5, "gia_luc_do": 150.0},
            "USDCAD": {"gia_luc_do": 1.40},
            "XAUUSD": {"point": 0.01, "contract_size": 100.0},
            "JP225CASH": {"point": 1.0, "contract_size": 1.0}}
    e = V2.thong_so("EURCAD", bang)
    assert abs(e["pv"] - 0.1 / 1.40) < 1e-12 and e["pip"] == 1e-4          # ~0,0714 nhu hang so cu
    j = V2.thong_so("USDJPY", bang)
    assert abs(j["pip"] - 0.01) < 1e-15 and abs(j["pv"] - 10.0 / 150.0) < 1e-12   # cu: 0,0714 voi pip 0,0001
    assert abs(V2.thong_so("XAUUSD", bang)["pv"] - 0.1) < 1e-12
    assert abs(V2.thong_so("JP225CASH", bang)["pv"] - 0.01 * 10.0 / 150.0) < 1e-12   # yet JPY
    with pytest.raises(ValueError):
        V2.thong_so("GBPNOK", bang)                                       # chua do -> nem loi, khong doan
