# -*- coding: utf-8 -*-
"""Engine luoi (`nhan/luoi.py`) theo QUY CACH TUNG MA - 03/10/2026.

Chu du an: "he co lai san -> khai thac truoc". 18/31 nguoi thang song >= 2 nam la luoi/DCA, nhung engine chi chay duoc
AUDCAD vi hang so (pip, hop dong, point, phi qua dem) di cung ma nguon. Nay hang so thanh `QuyCach`; mac dinh = AUDCAD.

Ba lop bao ve, vi KHONG co ma nao ngoai AUDCAD de doi chieu kinh te tren cloud:
  1. HOI QUY: ket qua AUDCAD phai y het ban cu (GOLDEN sinh tu ban TRUOC khi sua, tren chuoi tong hop tat dinh).
  2. BAT BIEN: doi don vi (gia x k, pip/point x k, von x k; hop dong x m, lot / m) khong duoc doi ty le lai/DD -
     mot hang so AUDCAD con sot lai se lam hong phep nay.
  3. TAY: kich ban nho tinh bang tay (lai, spread, phi qua dem dung dau, dung chieu).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from nhan import chi_phi as CP
from nhan import luoi as LU
from nhan import nc_du_lieu as NDL
from nhan import nc_so_tay as ST
from nhan import nc_thi_nghiem as TN


# ------------------------------------------------------------------ DU LIEU TONG HOP TAT DINH
def _chuoi(n: int = 6000, seed: int = 7, gia0: float = 0.95, k: float = 1.0, xu_huong: float = 0.0,
           hoi_quy: float = 0.02) -> pd.DataFrame:
    """OHLC + spread (POINT) tong hop, hoi quy ve gia0 (luoi co viec de lam). `k` nhan gia (cap pip 1e-2...).
    `xu_huong` < 0 + `hoi_quy` = 0: gia troi xuong lien tuc -> luoi mua chat tang va CHAY tai khoan giua chung."""
    rng = np.random.RandomState(seed)
    x = np.empty(n)
    x[0] = gia0
    for i in range(1, n):
        x[i] = x[i - 1] + hoi_quy * (gia0 - x[i - 1]) + xu_huong + rng.normal(0, 4e-4)
    o = np.r_[x[0], x[:-1]]
    hi = np.maximum(o, x) + np.abs(rng.normal(0, 2e-4, n))
    lo = np.minimum(o, x) - np.abs(rng.normal(0, 2e-4, n))
    sp = np.where(rng.rand(n) < 0.02, 0, rng.randint(12, 40, n)).astype(float)
    idx = pd.date_range("2024-01-01", periods=n, freq="15min")
    return pd.DataFrame({"open": o * k, "high": hi * k, "low": lo * k, "close": x * k, "spread": sp}, index=idx)


#: ten -> (tham so ThamSo, von, tham so chuoi). Phu moi nhanh cua `_mot_ro`: tia lenh, cho lui, chot tien, gian dan,
#: nhan lot, va stop-out GIUA CHUNG (chuoi troi xuong + luoi mua chat tang: equity cham 0,5 x margin o bar 695).
CASES = {
    "mac_dinh": (dict(buoc=15, tp=10, tran_tang=12), 10000.0, {}),
    "mua_nhan_lot": (dict(che_do="mua", kieu_lot="nhan", he_so_lot=1.3, buoc=12, tp=8, tran_tang=10), 10000.0, {}),
    "tia_lenh": (dict(tia_lenh=True, bien_cap=3.0, cap_moi_bar=1, buoc=10, tp=15, tran_tang=15), 10000.0, {}),
    "cho_lui": (dict(cho_lui=8.0, buoc=15, tp=10, tran_tang=12), 10000.0, {}),
    "chot_tien_ban": (dict(che_do="ban", chot_tien=3.0, buoc=15, tp=10, tran_tang=12), 10000.0, {}),
    "gian_dan": (dict(he_so_buoc=1.25, buoc_tran=60.0, buoc=10, tp=10, tran_tang=14), 10000.0, {}),
    "chay_giua_chung": (dict(che_do="mua", buoc=10, tp=40, tran_tang=30), 1000.0,
                        dict(xu_huong=-4e-5, hoi_quy=0.0)),
}


def _tom_tat(kq, von: float) -> dict:
    """Tom tat so lieu cua mot lan chay. `eq_*` bo bar 0 vi GOLDEN sinh tu ban cu, khi equity[0] = von - TONG spread ca chuoi
    (loi da sua 03/10/2026: nay equity[0] = von - spread lenh dau). Bar 0 co test rieng o muc 9 - giu nguyen cach tom tat nay de
    golden khong phai sinh lai (khong con so nao khac trong golden doi)."""
    cs = LU.chi_so(kq, von)
    e = np.asarray(kq.duong_equity, float)[1:]
    return {"lai_rong": float(kq.lai_rong), "lai_gop": float(kq.lai_gop), "phi_spread": float(kq.phi_spread),
            "phi_swap": float(kq.phi_swap), "so_ro": int(kq.so_ro), "so_lenh": int(kq.so_lenh),
            "tang_max": int(kq.tang_max), "lo_treo_dinh": float(kq.lo_treo_dinh), "chay": bool(kq.chay),
            "bar_chay": kq.bar_chay, "eq_tong": float(e.sum()), "eq_min": float(e.min()),
            "eq_cuoi": float(e[-1]), "loi_suat_nam_pct": float(cs["loi_suat_nam_pct"]),
            "maxdd_pct": float(cs["maxdd_pct"])}


#: SINH TU BAN CU cua luoi.py (truoc khi them QuyCach) bang `_sinh_golden()`. KHONG sua tay.
#: NGOAI LE 03/10/2026: 'gian_dan' sinh lai sau khi sua loi lech mot nac cua `_buoc` (khoang dau tien = buoc, khong phai
#: buoc * he_so_buoc) - xem test_khoang_cach_gian_dan_tinh_bang_tay. Cac ca khac KHONG doi mot bit.
GOLDEN = {'chay_giua_chung': {'bar_chay': 695,
                     'chay': True,
                     'eq_cuoi': 0.0,
                     'eq_min': 0.0,
                     'eq_tong': 470325.4322381076,
                     'lai_gop': 0.0,
                     'lai_rong': 3.1999179477048676,
                     'lo_treo_dinh': 8090.802813695505,
                     'loi_suat_nam_pct': 1.8851129522567789,
                     'maxdd_pct': -100.0,
                     'phi_spread': 7.120000000000002,
                     'phi_swap': -10.31991794770487,
                     'so_lenh': 30,
                     'so_ro': 0,
                     'tang_max': 30},
 'cho_lui': {'bar_chay': None,
             'chay': False,
             'eq_cuoi': 10118.384558361367,
             'eq_min': 9997.556104124176,
             'eq_tong': 60492511.19014801,
             'lai_gop': 161.0,
             'lai_rong': 118.38455836136664,
             'lo_treo_dinh': 15.268301121212357,
             'loi_suat_nam_pct': 6.974187087336962,
             'maxdd_pct': -0.16486000368981513,
             'phi_spread': 41.080000000000005,
             'phi_swap': 1.5354416386333467,
             'so_lenh': 161,
             'so_ro': 119,
             'tang_max': 5},
 'chot_tien_ban': {'bar_chay': None,
                   'chay': False,
                   'eq_cuoi': 10195.330729874437,
                   'eq_min': 9993.542468328566,
                   'eq_tong': 60544115.45619063,
                   'lai_gop': 268.9797644875687,
                   'lai_rong': 196.5790397442068,
                   'lo_treo_dinh': 31.57955049658578,
                   'loi_suat_nam_pct': 11.580724881705084,
                   'maxdd_pct': -0.3329974399520874,
                   'phi_spread': 54.79000000000004,
                   'phi_swap': 17.61072474336182,
                   'so_lenh': 221,
                   'so_ro': 73,
                   'tang_max': 7},
 'gian_dan': {'bar_chay': None,
              'chay': False,
              'eq_cuoi': 10358.468377509236,
              'eq_min': 9992.20544526764,
              'eq_tong': 61009900.04212849,
              'lai_gop': 529.0,
              'lai_rong': 372.42593056717124,
              'lo_treo_dinh': 50.123213388548194,
              'loi_suat_nam_pct': 21.940092119299884,
              'maxdd_pct': -0.2703620682947383,
              'phi_spread': 134.77000000000004,
              'phi_swap': 21.804069432828754,
              'so_lenh': 534,
              'so_ro': 202,
              'tang_max': 7},
 'mac_dinh': {'bar_chay': None,
              'chay': False,
              'eq_cuoi': 10387.431515779064,
              'eq_min': 9994.037769353008,
              'eq_tong': 61081031.20704551,
              'lai_gop': 558.0,
              'lai_rong': 399.34105916438216,
              'lo_treo_dinh': 46.929012467070926,
              'loi_suat_nam_pct': 23.525697074159773,
              'maxdd_pct': -0.3051926731049259,
              'phi_spread': 139.83999999999997,
              'phi_swap': 18.818940835617852,
              'so_lenh': 563,
              'so_ro': 242,
              'tang_max': 8},
 'mua_nhan_lot': {'bar_chay': None,
                  'chay': False,
                  'eq_cuoi': 10440.489840789505,
                  'eq_min': 9968.24668723032,
                  'eq_tong': 61340280.668271944,
                  'lai_gop': 673.8241239863994,
                  'lai_rong': 458.85262324273845,
                  'lo_treo_dinh': 167.75162326239595,
                  'loi_suat_nam_pct': 27.031600103130675,
                  'maxdd_pct': -1.7119881943105097,
                  'phi_spread': 216.8484733300698,
                  'phi_swap': -1.8769725864088247,
                  'so_lenh': 584,
                  'so_ro': 279,
                  'tang_max': 10},
 'tia_lenh': {'bar_chay': None,
              'chay': False,
              'eq_cuoi': 10343.589283618558,
              'eq_min': 9983.563989035598,
              'eq_tong': 60988141.354554296,
              'lai_gop': 986.3675601894754,
              'lai_rong': 356.6081685687479,
              'lo_treo_dinh': 64.94968780065024,
              'loi_suat_nam_pct': 21.008247349957283,
              'maxdd_pct': -0.5639694105295079,
              'phi_spread': 616.42,
              'phi_swap': 13.3393916207275,
              'so_lenh': 1345,
              'so_ro': 235,
              'tang_max': 11}}


def _sinh_golden() -> dict:  # pragma: no cover - chi dung mot lan, voi ban luoi.py cu
    return {ten: _tom_tat(LU.chay(_chuoi(**ck), LU.ThamSo(**kw), von), von)
            for ten, (kw, von, ck) in CASES.items()}


# ------------------------------------------------------------------ 1. HOI QUY AUDCAD
@pytest.mark.parametrize("ten", sorted(CASES))
def test_audcad_mac_dinh_giong_het_ban_cu(ten):
    kw, von, ck = CASES[ten]
    df = _chuoi(**ck)
    cu = GOLDEN[ten]
    for qc in (None, LU.QC_AUDCAD):
        kq = LU.chay(df, LU.ThamSo(**kw), von) if qc is None else LU.chay(df, LU.ThamSo(**kw), von, qc)
        moi = _tom_tat(kq, von)
        for k, v in cu.items():
            if isinstance(v, float):
                assert moi[k] == pytest.approx(v, rel=1e-12, abs=1e-9), (ten, k)
            else:
                assert moi[k] == v, (ten, k)


def test_bo_golden_phu_du_nhanh_va_co_ca_chay_lan_khong_chay():
    chay = [GOLDEN[t]["chay"] for t in CASES]
    assert any(chay) and not all(chay), "can ca ca stop-out lan ca khong stop-out de golden co y nghia"
    assert GOLDEN["chay_giua_chung"]["bar_chay"] > 50, "stop-out phai den tu lo treo that, khong tu bar 0"
    assert all(GOLDEN[t]["so_lenh"] > 20 for t in CASES)
    assert GOLDEN["tia_lenh"]["so_lenh"] != GOLDEN["mac_dinh"]["so_lenh"]


# ------------------------------------------------------------------ 2. BAT BIEN DON VI
def _rut(kq, von):
    t = _tom_tat(kq, von)
    return {k: t[k] for k in ("loi_suat_nam_pct", "maxdd_pct", "so_ro", "so_lenh", "tang_max", "chay", "bar_chay")}


@pytest.mark.parametrize("ten", ["mac_dinh", "tia_lenh", "gian_dan", "chot_tien_ban", "chay_giua_chung"])
def test_bat_bien_theo_quy_mo_gia_va_pip(ten):
    """Gia x k, pip x k, point x k, von x k -> ty le lai / DD y het. Con 1e-4 / 1e-5 / 2e-4 nao sot trong engine se lam hong."""
    kw, von, ck = CASES[ten]
    k = 100.0
    a = _rut(LU.chay(_chuoi(**ck), LU.ThamSo(**kw), von), von)
    qc = LU.QuyCach(ma="JPY_GIA", pip=LU.QC_AUDCAD.pip * k, point=LU.QC_AUDCAD.point * k,
                    phi_nam_mua=LU.QC_AUDCAD.phi_nam_mua, phi_nam_ban=LU.QC_AUDCAD.phi_nam_ban,
                    spread_du_phong=LU.QC_AUDCAD.spread_du_phong * k)
    kw_k = dict(kw)
    if "chot_tien" in kw_k:
        kw_k["chot_tien"] *= k          # `chot_tien` la TIEN (dong bao gia / 0,01 lot), khong phai pip: nhan theo gia
    b = _rut(LU.chay(_chuoi(k=k, **ck), LU.ThamSo(**kw_k), von * k, qc), von * k)
    for key in a:
        if isinstance(a[key], float):
            assert b[key] == pytest.approx(a[key], rel=1e-7, abs=1e-9), key
        else:
            assert b[key] == a[key], key


@pytest.mark.parametrize("ten", ["mac_dinh", "chay_giua_chung"])
def test_bat_bien_theo_lot_va_hop_dong(ten):
    """Hop dong / m, lot x m -> cung vi the that: ket qua y het - ke ca BAR stop-out (margin = lot x hop dong x gia)."""
    kw, von, ck = CASES[ten]
    m = 100.0
    a = LU.chay(_chuoi(**ck), LU.ThamSo(**kw), von)
    qc = LU.QuyCach(ma="X", hop_dong=LU.QC_AUDCAD.hop_dong / m)
    b = LU.chay(_chuoi(**ck), LU.ThamSo(**dict(kw, lot=0.01 * m)), von, qc)
    assert b.lai_rong == pytest.approx(a.lai_rong, rel=1e-9, abs=1e-12)
    assert b.phi_spread == pytest.approx(a.phi_spread, rel=1e-9)
    assert b.phi_swap == pytest.approx(a.phi_swap, rel=1e-9, abs=1e-12)
    assert (b.so_lenh, b.so_ro, b.tang_max, b.chay, b.bar_chay) == (a.so_lenh, a.so_ro, a.tang_max, a.chay, a.bar_chay)


def test_von_tuyen_tinh_voi_lot_khi_khong_chay():
    """Lot x2 va von x2 -> ty le lai / DD y het (luat 'lai lo luoi tuyen tinh theo lot' ma danh_gia_luoi dua vao)."""
    kw, von, _ = CASES["mac_dinh"]
    a = _rut(LU.chay(_chuoi(), LU.ThamSo(**kw), von), von)
    b = _rut(LU.chay(_chuoi(), LU.ThamSo(**dict(kw, lot=0.02)), 2 * von), 2 * von)
    for key in a:
        if isinstance(a[key], float):
            assert b[key] == pytest.approx(a[key], rel=1e-9, abs=1e-12), key
        else:
            assert b[key] == a[key], key


# ------------------------------------------------------------------ 3. KICH BAN TINH BANG TAY
def _hai_bar(c0, c1, hi1, lo1, sp_point):
    idx = pd.to_datetime(["2024-01-02", "2024-01-03"])      # cach nhau DUNG 1 ngay -> dem = 1
    return pd.DataFrame({"open": [c0, c0], "high": [c0, hi1], "low": [c0, lo1], "close": [c0, c1],
                         "spread": [sp_point, sp_point]}, index=idx)


def test_tay_mua_chot_tp_tru_spread_tru_phi_qua_dem():
    # mua 0,01 lot tai 1,0000; bar 2 cham TP 40 pip (1,0040): lai 0,01 * 100.000 * 0,0040 = 4,0
    qc = LU.QuyCach(ma="T", pip=1e-4, hop_dong=100_000.0, point=1e-5, phi_nam_mua=0.0365, phi_nam_ban=-0.0365)
    df = _hai_bar(1.0000, 1.0020, 1.0045, 0.9999, 20.0)     # spread 20 point = 2 pip = 2e-4
    kq = LU.chay(df, LU.ThamSo(che_do="mua", buoc=60, tp=40, tran_tang=5), 10000.0, qc)
    assert kq.so_ro == 1 and kq.so_lenh == 2                 # lenh dau + mo lai sau khi chot
    assert kq.lai_gop == pytest.approx(4.0)
    assert kq.phi_spread == pytest.approx(2 * 2e-4 * 0.01 * 100_000.0)            # 2 lan mo x 0,4/... = 0,4
    # phi qua dem: 1 vi the 0,01 lot qua 1 ngay: 0,01*100000 * 0,0365 * 1/365 * close(bar 2)
    assert kq.phi_swap == pytest.approx(0.01 * 100_000.0 * 0.0365 / 365.0 * 1.0020)
    assert kq.lai_rong == pytest.approx(4.0 - kq.phi_spread - kq.phi_swap)


def test_tay_ban_dung_phi_ban_va_dau_am_la_duoc_tra():
    # ban 0,01 lot tai 1,0000; bar 2 cham TP (gia ve 0,9960): lai 4,0. phi_nam_ban am -> DUOC tra: phi_swap < 0
    qc = LU.QuyCach(ma="T", phi_nam_mua=0.5, phi_nam_ban=-0.0730)
    df = _hai_bar(1.0000, 0.9980, 1.0001, 0.9955, 20.0)
    kq = LU.chay(df, LU.ThamSo(che_do="ban", buoc=60, tp=40, tran_tang=5), 10000.0, qc)
    assert kq.so_ro == 1
    assert kq.lai_gop == pytest.approx(4.0)
    assert kq.phi_swap == pytest.approx(0.01 * 100_000.0 * (-0.0730) / 365.0 * 0.9980)
    assert kq.phi_swap < 0


def test_tay_point_doi_don_vi_cot_spread():
    # cung 20 point nhung point 1e-3 (cap JPY) -> spread 0,02 gia = 2 pip (pip 0,01): phi spread 2 lan x 0,02 x 0,01 x 100.000
    qc = LU.QuyCach(ma="T", pip=1e-2, hop_dong=100_000.0, point=1e-3, phi_nam_mua=0.0, phi_nam_ban=0.0)
    df = _hai_bar(100.00, 100.20, 100.45, 99.99, 20.0)
    kq = LU.chay(df, LU.ThamSo(che_do="mua", buoc=60, tp=40, tran_tang=5), 1_000_000.0, qc)
    assert kq.so_ro == 1
    assert kq.lai_gop == pytest.approx(0.01 * 100_000.0 * 0.40)          # TP 40 pip = 0,40 gia
    assert kq.phi_spread == pytest.approx(2 * 0.02 * 0.01 * 100_000.0)


def test_tay_bar_spread_bang_khong_dung_phong_cua_quy_cach():
    # khong co cot spread: dung `spread_du_phong` cua quy cach (khong con 2e-4 cung)
    qc = LU.QuyCach(ma="T", spread_du_phong=5e-4, phi_nam_mua=0.0, phi_nam_ban=0.0)
    df = _hai_bar(1.0000, 1.0020, 1.0045, 0.9999, 20.0).drop(columns="spread")
    kq = LU.chay(df, LU.ThamSo(che_do="mua", buoc=60, tp=40, tran_tang=5), 10000.0, qc)
    assert kq.phi_spread == pytest.approx(2 * 5e-4 * 0.01 * 100_000.0)


# ------------------------------------------------------------------ 4. CHON QUY CACH THEO MA
def _cp(pm=0.02, pb=-0.01, do_tin="SAN", sp=1e-4):
    return CP.MoHinhChiPhi(ma="X", spread_frac_chung=sp, phi_nam_mua=pm, phi_nam_ban=pb, do_tin=do_tin)


@pytest.fixture
def khong_ghi_de(tmp_path, monkeypatch):
    monkeypatch.setattr(LU, "FILE_QUY_CACH", tmp_path / "luoi_quy_cach.json")
    return tmp_path / "luoi_quy_cach.json"


def test_audcad_luon_la_hang_so_cu_khong_theo_mo_hinh_chi_phi(khong_ghi_de):
    qc, ly = LU.quy_cach_cho("AUDCAD", 0.9, _cp(pm=9.9, pb=9.9, do_tin="KHAI"))
    assert qc == LU.QC_AUDCAD and ly == ""
    assert (LU.QC_AUDCAD.pip, LU.QC_AUDCAD.hop_dong, LU.QC_AUDCAD.point) == (1e-4, 100_000.0, 1e-5)
    assert (LU.QC_AUDCAD.phi_nam_mua, LU.QC_AUDCAD.phi_nam_ban) == (-0.00263, 0.03853)
    assert LU.PIP == 1e-4 and LU.HOP_DONG == 100_000.0           # tuong thich ma cu


@pytest.mark.parametrize("ma", ["USDCHF", "AUDCHF", "AUDNZD", "USDCAD", "EURUSD", "GBPAUD", "EURGBP", "EURCAD",
                                "NZDCAD", "XM_EURUSD", "EURUSDM"])
def test_cap_fx_chuan_lay_phi_tu_mo_hinh_chi_phi(ma, khong_ghi_de):
    qc, ly = LU.quy_cach_cho(ma, 1.1, _cp(pm=0.02, pb=-0.01, do_tin="SAN", sp=1e-4))
    assert qc is not None, ly
    assert (qc.pip, qc.hop_dong, qc.point) == (1e-4, 100_000.0, 1e-5)
    assert (qc.phi_nam_mua, qc.phi_nam_ban, qc.do_tin) == (0.02, -0.01, "SAN")
    assert qc.spread_du_phong == pytest.approx(1e-4 * 1.1)         # frac cua gia -> don vi gia
    assert qc.da_doi_chieu and qc.ma == ma.upper()
    assert "lop FX chuan" in qc.nguon and "SAN" in qc.nguon


def test_khong_co_mo_hinh_chi_phi_thi_khai_bao(khong_ghi_de):
    qc, _ = LU.quy_cach_cho("USDCHF", 0.9, None)
    assert qc.do_tin == "KHAI" and qc.phi_nam_mua == qc.phi_nam_ban == CP.PHI_QUAN_SAT["fx"]["phi_nam_mua"]
    assert qc.spread_du_phong == pytest.approx(2 * qc.pip)


@pytest.mark.parametrize("ma,tu_khoa", [
    ("USDJPY", "doi chieu"), ("EURJPY", "doi chieu"), ("XAUUSD", "doi chieu"),
    ("US500Cash", "chua ho tro"), ("XAUEUR", "chua ho tro"), ("USDZAR", "chua ho tro"),
    ("BTCUSD", "chua ho tro"), ("XM_US100CASH", "chua ho tro"), ("EURUSD1", "chua ho tro"),
])
def test_ma_chua_ho_tro_hoac_chua_doi_chieu_bi_tu_choi_co_ly_do(ma, tu_khoa, khong_ghi_de):
    qc, ly = LU.quy_cach_cho(ma, 100.0, _cp())
    assert qc is None and tu_khoa in ly and "luoi_quy_cach.json" in ly


def test_ghi_de_cau_hinh_mo_khoa_ma_da_do_that(khong_ghi_de):
    khong_ghi_de.write_text(json.dumps({
        "XAUUSD": {"pip": 0.1, "hop_dong": 100.0, "point": 0.01, "da_doi_chieu": True,
                   "nguon": "symbol_info XM demo (do tay)"},
        "USDJPY": {"pip": 0.01, "point": 0.001, "von_quy_doi": 150.0, "da_doi_chieu": True}}), encoding="utf-8")
    qc, ly = LU.quy_cach_cho("XAUUSD", 2300.0, _cp(pm=0.075, pb=-0.02, sp=1e-4))
    assert qc is not None, ly
    assert (qc.pip, qc.hop_dong, qc.point) == (0.1, 100.0, 0.01)
    assert (qc.phi_nam_mua, qc.phi_nam_ban) == (0.075, -0.02)       # phi van lay tu mo hinh chi phi, khong tu file
    assert "symbol_info" in qc.nguon
    qj, _ = LU.quy_cach_cho("USDJPY", 150.0, _cp())
    assert qj.pip == 0.01 and qj.von_quy_doi == 150.0 and qj.hop_dong == 100_000.0
    # file hong / khoa la -> tu choi ro rang, khong doan
    khong_ghi_de.write_text(json.dumps({"XAUUSD": {"pip_la": 1}}), encoding="utf-8")
    q2, ly2 = LU.quy_cach_cho("XAUUSD", 2300.0, _cp())
    assert q2 is None and "pip_la" in ly2
    khong_ghi_de.write_text("khong phai json", encoding="utf-8")
    q3, _ = LU.quy_cach_cho("EURUSD", 1.1, _cp())
    assert q3 is not None                                            # file hong khong lam hong ma chuan


def test_khoa_quy_cach_doi_khi_phi_doi():
    a = LU.khoa_quy_cach(LU.QuyCach(ma="X", phi_nam_mua=0.01, phi_nam_ban=0.01, do_tin="SAN"))
    b = LU.khoa_quy_cach(LU.QuyCach(ma="X", phi_nam_mua=0.02, phi_nam_ban=0.01, do_tin="SAN"))
    c = LU.khoa_quy_cach(LU.QuyCach(ma="X", phi_nam_mua=0.01, phi_nam_ban=0.01, do_tin="KHAI"))
    assert len({a, b, c}) == 3 and a == LU.khoa_quy_cach(LU.QuyCach(ma="X", phi_nam_mua=0.01,
                                                                    phi_nam_ban=0.01, do_tin="SAN"))


# ------------------------------------------------------------------ 5. THU_LUOI QUA nc_thi_nghiem.danh_gia_luoi
@pytest.fixture
def moi_truong(tmp_path, monkeypatch, khong_ghi_de):
    """Trang thai doc LUC GOI (cp, df): test doi chung giua chung de thay van tay thi nghiem doi theo phi."""
    monkeypatch.setattr(ST, "DB", tmp_path / "nc.db")
    monkeypatch.setattr(TN, "_DEM_MOC", {})
    st = {"cp": _cp(do_tin="SAN"), "df": _chuoi()}
    monkeypatch.setattr(NDL, "nap", lambda ma, khung="H4": st["df"])
    monkeypatch.setattr(NDL, "chi_phi", lambda ma, d: st["cp"])
    return st


TS = dict(buoc=15, tp=10, tran_tang=12)


def test_thu_luoi_ma_anh_em_chay_va_ghi_quy_cach(moi_truong):
    r = TN.danh_gia_luoi("USDCHF", "M15", TS, "kham_pha", von=10000.0)
    assert r["trang_thai"] in ("DAT", "AM"), r.get("ly_do")
    assert r["quy_cach"]["ma"] == "USDCHF" and r["quy_cach"]["do_tin"] == "SAN"
    assert r["quy_cach"]["phi_nam_mua"] == 0.02 and r["quy_cach"]["pip"] == 1e-4
    assert r["chi_phi_do_tin"] == "SAN" and r["lenh"]["so_lenh"] > 0 and "tn_id" in r
    assert any("tester" in c for c in r["canh_bao"]), "ma moi phai nhac chua doi chieu voi MT5 tester"
    r2 = TN.danh_gia_luoi("USDCHF", "M15", TS, "kham_pha", von=10000.0)
    assert "tu_so_tay" in r2


def test_thu_luoi_doi_phi_thi_khong_lay_ket_qua_cu(moi_truong):
    TN.danh_gia_luoi("USDCHF", "M15", TS, "kham_pha", von=10000.0)
    moi_truong["cp"] = _cp(pm=0.30, pb=0.30, do_tin="SAN")           # phi qua dem dat gap 15 lan
    r = TN.danh_gia_luoi("USDCHF", "M15", TS, "kham_pha", von=10000.0)
    assert "tu_so_tay" not in r and r["quy_cach"]["phi_nam_mua"] == 0.30


def test_thu_luoi_phi_dat_hon_thi_lai_giam(moi_truong):
    """Phi qua dem di vao ket qua that: cung chuoi, cung tham so, phi cao -> loi suat THAP hon."""
    r0 = TN.danh_gia_luoi("EURUSD", "M15", TS, "kham_pha", von=10000.0)
    moi_truong["cp"] = _cp(pm=0.50, pb=0.50, do_tin="SAN")
    r1 = TN.danh_gia_luoi("EURUSD", "M15", TS, "kham_pha", von=10000.0)
    assert r1["tien"]["loi_suat_nam_pct"] < r0["tien"]["loi_suat_nam_pct"]
    assert r1["lenh"]["so_lenh"] == r0["lenh"]["so_lenh"], "phi khong duoc doi so lenh"


def test_thu_luoi_chi_phi_khai_la_nhan_khong_phai_cong(moi_truong):
    """Kham pha chi GAN NHAN `KHAI` (nhu `ho_so`/`thu_co_che`); cong niem phong moi ha xuong CHUA_DO_DUOC."""
    moi_truong["cp"] = _cp(do_tin="KHAI")
    r = TN.danh_gia_luoi("EURUSD", "M15", TS, "kham_pha", von=10000.0)
    assert r["trang_thai"] in ("DAT", "AM")
    assert r["chi_phi_do_tin"] == "KHAI" and r["quy_cach"]["do_tin"] == "KHAI"
    assert any("KHAI" in x for x in r["nhan_canh_bao"]), r["nhan_canh_bao"]


def test_thu_luoi_ma_chua_ho_tro_hoac_chua_doi_chieu_van_tu_choi(moi_truong):
    for ma, tk in (("USDJPY", "doi chieu"), ("XAUUSD", "doi chieu"), ("US500Cash", "chua ho tro")):
        r = TN.danh_gia_luoi(ma, "M15", TS, "kham_pha", von=10000.0)
        assert r["trang_thai"] == "CHUA_DO_DUOC" and tk in r["ly_do"], (ma, r)
    # niem phong van khong mo qua duong nay
    r = TN.danh_gia_luoi("USDCHF", "M15", TS, "niem_phong", von=10000.0)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "kham_pha/xac_nhan" in r["ly_do"]
    # tham so la bi chan truoc khi nap du lieu
    r = TN.danh_gia_luoi("USDCHF", "M15", {"khong_co": 1}, "kham_pha", von=10000.0)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "khong biet" in r["ly_do"]


def test_thu_luoi_audcad_khong_doi_theo_mo_hinh_chi_phi(moi_truong):
    moi_truong["cp"] = _cp(pm=5.0, pb=5.0, do_tin="KHAI")           # neu AUDCAD lay phi tu day thi lo sap san
    r = TN.danh_gia_luoi("AUDCAD", "M15", TS, "kham_pha", von=10000.0)
    assert r["quy_cach"]["phi_nam_mua"] == -0.00263 and r["quy_cach"]["phi_nam_ban"] == 0.03853
    assert not any("KHAI" in x for x in r["nhan_canh_bao"])           # dung nhu cu: AUDCAD khong bi nhan KHAI moi
    assert not any("tester" in c for c in r["canh_bao"])              # va dau ra AUDCAD khong them canh bao moi
    # cung ket qua voi chay thang engine cu (khong qua danh_gia_luoi)
    seg = NDL.cat_doan(moi_truong["df"], "kham_pha")
    pre, a = seg
    kq = LU.chay(pre.iloc[a:], LU.ThamSo(**TS), 10000.0)
    assert r["lenh"]["so_lenh"] == kq.so_lenh and r["lenh"]["so_ro"] == kq.so_ro
    assert r["tien"]["loi_suat_nam_pct"] == round(LU.chi_so(kq, 10000.0)["loi_suat_nam_pct"], 2)


def test_thu_luoi_von_quy_doi_cho_ma_co_ghi_de(moi_truong, khong_ghi_de):
    khong_ghi_de.write_text(json.dumps({"USDJPY": {"pip": 0.01, "point": 0.001, "von_quy_doi": 150.0,
                                                   "da_doi_chieu": True}}), encoding="utf-8")
    moi_truong["df"] = _chuoi(k=150 / 0.95)                           # gia ~150
    r = TN.danh_gia_luoi("USDJPY", "M15", TS, "kham_pha", von=10000.0)
    assert r["trang_thai"] in ("DAT", "AM"), r.get("ly_do")
    assert r["quy_cach"]["von_quy_doi"] == 150.0 and r["quy_cach"]["pip"] == 0.01 and r["von"] == 10000.0


# ------------------------------------------------------------------ 6. THAM SO KHAI BAO MA ENGINE KHONG DOC
def test_moi_truong_thamso_hoac_duoc_doc_hoac_bi_tu_choi():
    """Mot truong `ThamSo` ma engine khong doc se cho ket qua y het 0 ma khong loi nao (`dung_lo_tong` da nhu vay
    tu truoc 03/10). Truong nao khong xuat hien nhu `ts.<ten>` trong `_mot_ro`/`chay` phai nam trong CHUA_CAI_DAT -
    va nguoc lai: da cai dat roi thi phai go khoi danh sach (khong de chan nham)."""
    import dataclasses
    import inspect
    nguon = inspect.getsource(LU._mot_ro) + inspect.getsource(LU.chay) + inspect.getsource(LU.chay_mang)
    for f in dataclasses.fields(LU.ThamSo):
        doc = ("ts." + f.name) in nguon
        assert doc != (f.name in LU.CHUA_CAI_DAT), (
            "%s: engine %s nhung CHUA_CAI_DAT %s" % (f.name, "doc" if doc else "KHONG doc",
                                                      "co ten" if f.name in LU.CHUA_CAI_DAT else "khong co ten"))


def test_chay_tu_choi_tham_so_chua_cai_dat():
    with pytest.raises(ValueError, match="CHUA cai dat"):
        LU.chay(_chuoi(500), LU.ThamSo(buoc=15, tp=10, dung_lo_tong=500.0), 10000.0)
    LU.chay(_chuoi(500), LU.ThamSo(buoc=15, tp=10, dung_lo_tong=0.0), 10000.0)        # 0 = tat: van chay
    assert LU.tham_so_chua_cai_dat({"dung_lo_tong": 3, "buoc": 5}) == ["dung_lo_tong"]
    assert LU.tham_so_chua_cai_dat(LU.ThamSo()) == []


def test_thu_luoi_tu_choi_dung_lo_tong_truoc_khi_nap_du_lieu(moi_truong, monkeypatch):
    def _khong_duoc_goi(*a, **k):
        raise AssertionError("tham so bi chan phai tu choi TRUOC khi nap du lieu")
    monkeypatch.setattr(NDL, "nap", _khong_duoc_goi)
    r = TN.danh_gia_luoi("USDCHF", "M15", dict(TS, dung_lo_tong=500.0), "kham_pha", von=10000.0)
    assert r["trang_thai"] == "CHUA_DO_DUOC" and "CHUA cai dat" in r["ly_do"] and "dung_lo_tong" in r["ly_do"]


# ------------------------------------------------------------------ 7. GHI LENH (danh sach lenh mo phong)
@pytest.mark.parametrize("ten", sorted(CASES))
def test_ghi_lenh_khong_doi_so_nao_va_khop_bo_dem(ten):
    """`ghi_lenh=True` chi THEM nhat ky: moi con so van y het ban khong ghi, va nhat ky khop bo dem cua chinh engine
    (so lenh, so ro chot TP, lai gop) - de `lenh` doi chieu duoc voi lich su that / tester ma khong lech ngam."""
    ts, von, kw = CASES[ten]
    df = _chuoi(**kw)
    a = LU.chay(df, LU.ThamSo(**ts), von)
    b = LU.chay(df, LU.ThamSo(**ts), von, ghi_lenh=True)
    assert a.lenh is None and b.lenh is not None
    assert _tom_tat(a, von) == _tom_tat(b, von) and np.array_equal(a.duong_equity, b.duong_equity)
    ln = b.lenh
    assert len(ln) == b.so_lenh, "so lenh nhat ky phai bang so_lenh cua engine"
    dong = ln[ln["dong"].notna()]
    assert (dong["gia_dong"].notna()).all() and (ln.loc[ln["dong"].isna(), "gia_dong"].isna()).all()
    assert (dong["dong"] >= dong["mo"]).all(), "lenh khong duoc dong truoc khi mo"
    # lai da chot (gop) = tong (gia_dong - gia_mo) x lot x hop: dung chinh tong `lai_gop` cua engine (khong co lenh dang mo)
    hop = LU.QC_AUDCAD.hop_dong
    lai = float((dong["chieu"] * (dong["gia_dong"] - dong["gia_mo"]) * dong["lot"]).sum() * hop)
    assert abs(lai - b.lai_gop) <= 1e-6 * max(1.0, abs(b.lai_gop)), (lai, b.lai_gop)
    # moi ro co dung MOT tang 0, cac tang lien tuc 0..k theo thu tu mo (tia lenh chi bo bot o giua nen khong bat buoc)
    if not ts.get("tia_lenh"):
        for _ro, g in ln.groupby("ro"):
            assert sorted(g["tang"]) == list(range(len(g)))
    for _ro, g in ln.groupby("ro"):
        assert (g["tang"] == 0).sum() == 1 and g["chieu"].nunique() == 1


def test_ghi_lenh_ban_chi_co_lenh_ban_va_chieu_ghi_dung():
    df = _chuoi()
    b = LU.chay(df, LU.ThamSo(buoc=15, tp=10, tran_tang=12, che_do="ban"), 10000.0, ghi_lenh=True)
    assert set(b.lenh["chieu"]) == {-1}
    assert (b.lenh["ro"] % 2 == 1).all(), "ro cua chieu ban danh so le"
    h = LU.chay(df, LU.ThamSo(buoc=15, tp=10, tran_tang=12), 10000.0, ghi_lenh=True)
    assert set(h.lenh["chieu"]) == {1, -1} and h.lenh.attrs["pip"] == LU.QC_AUDCAD.pip


# ------------------------------------------------------------------ 8. KHOANG CACH GIAN DAN (tinh bang tay)
@pytest.mark.parametrize("che_do,chieu", [("mua", 1), ("ban", -1)])
def test_khoang_cach_gian_dan_tinh_bang_tay(che_do, chieu):
    """Khoang dau tien = `buoc`, tiep theo nhan he_so_buoc, chan `buoc_tran`: buoc 10, he 2, tran 30 -> 10, 20, 30, 30 pip.
    (Truoc 03/10/2026 engine goi `_buoc(so_tang)` thay vi `_buoc(so_tang - 1)`: khoang dau = buoc * he_so_buoc, lech moi ro
    gian dan mot nac so voi tai lieu va `mo_phong_v2.py`.) Duong gia dung cho gia di mot mach qua tat ca cac moc."""
    pip = LU.QC_AUDCAD.pip
    n = 4
    idx = pd.date_range("2024-01-01", periods=n, freq="15min")
    g0 = 1.0000
    xa = g0 - chieu * 200 * pip                       # lui sau 200 pip nguoc chieu lenh: cham het cac tang
    hi = [g0, g0, g0, g0] if chieu > 0 else [g0, xa, xa, xa]
    lo = [g0, xa, xa, xa] if chieu > 0 else [g0, g0, g0, g0]
    close = [g0, xa, xa, xa]
    df = pd.DataFrame({"open": [g0, g0, xa, xa], "high": hi, "low": lo, "close": close, "spread": 0.0}, index=idx)
    kq = LU.chay(df, LU.ThamSo(che_do=che_do, buoc=10, he_so_buoc=2.0, buoc_tran=30.0, tp=500, tran_tang=5, lot=0.01),
                 1e9, ghi_lenh=True)
    gia = kq.lenh.sort_values("tang")["gia_mo"].to_numpy()
    khoang = [round(chieu * (a - b) / pip, 6) for a, b in zip(gia[:-1], gia[1:])]
    assert len(gia) == 5 and gia[0] == g0
    assert khoang == [10.0, 20.0, 30.0, 30.0], khoang


# ------------------------------------------------------------------ 9. BAR 0 = CHI spread lenh dau (sua 03/10/2026)
def _sp_gia(df, qc):
    """Spread theo GIA tung bar, tinh y het `chay` (cot POINT x point; bar bang 0 thay bang trung vi)."""
    sp = df["spread"].to_numpy(float) * qc.point
    return np.where(sp > 0, sp, np.nanmedian(sp[sp > 0]))


@pytest.mark.parametrize("che_do,so_chieu", [("mua", 1), ("ban", 1), ("hai_chieu", 2)])
def test_bar_dau_chi_tinh_spread_lenh_dau_khong_phai_tong_ca_chuoi(che_do, so_chieu):
    """equity[0] = von - spread cua LENH DAU. Ban cu gan `von - TONG spread ca chuoi`: mot diem dau gia o rat thap. No khong
    doi lai rong, nhung lam sai moi phep do tren duong von dung diem dau (he so lot o tran DD chang han)."""
    qc = LU.QC_AUDCAD
    df = _chuoi()
    ts = LU.ThamSo(che_do=che_do, buoc=15, tp=10, tran_tang=12)
    von = 10000.0
    kq = LU.chay(df, ts, von, qc)
    sp0 = _sp_gia(df, qc)[0] * ts.lot * qc.hop_dong
    assert kq.so_lenh > 50 and kq.phi_spread > 20 * so_chieu * sp0       # nhieu lenh: tong >> lenh dau (neu khong, test vo nghia)
    assert kq.duong_equity[0] == pytest.approx(von - so_chieu * sp0, abs=1e-9, rel=0)
    assert kq.duong_equity[0] > von - kq.phi_spread + 10 * sp0             # khong con la `von - tong spread`


def test_khong_bao_chay_tai_khoan_gia_o_bar_0():
    """Von nam giua `muc stop-out + spread lenh dau` va `muc stop-out + tong spread`: ban cu bao `chay o bar 0` du lenh dau
    moi mat dung mot spread. Day la dau hieu NGOAI cua loi bar 0 (khong chi la mot con so dep/xau di)."""
    qc = LU.QC_AUDCAD
    df = _chuoi()
    ts = LU.ThamSo(che_do="mua", buoc=15, tp=10, tran_tang=12)
    kq0 = LU.chay(df, ts, 1e7, qc)                                           # von khong lo: lay tang_max + tong spread
    lot_tong = ts.lot * kq0.tang_max                                         # kieu_lot mac dinh = hang
    nguong = ts.muc_stopout * lot_tong * qc.hop_dong * float(df["close"].mean()) / ts.don_bay
    sp0 = _sp_gia(df, qc)[0] * ts.lot * qc.hop_dong
    assert kq0.phi_spread > 20 * sp0
    von = nguong + 0.5 * (sp0 + kq0.phi_spread)
    assert von - kq0.phi_spread < nguong < von - sp0                         # dung khoang can kiem
    kq = LU.chay(df, ts, von, qc)
    assert kq.bar_chay != 0, "stop-out o bar 0 (equity[0] bi tru tong spread ca chuoi)"
    assert kq.duong_equity[0] == pytest.approx(von - sp0, abs=1e-9, rel=0)


@pytest.mark.parametrize("ma", ["AUDCAD", "USDCHF"])
def test_doi_phien_ban_engine_thi_so_tay_khong_tai_dung_ket_qua_cu(moi_truong, monkeypatch, ma):
    """Engine doi so lieu (nhu sua bar 0) ma van tay khong doi thi sau nay `thu_luoi` tra lai con so cua ban engine CU nhu thuc
    do. Ca hai nhanh van tay (chuan: AUDCAD; ma khac: co khoa quy cach) deu phai gom phien ban engine."""
    r0 = TN.danh_gia_luoi(ma, "M15", TS, "kham_pha", von=10000.0)
    assert "tu_so_tay" in TN.danh_gia_luoi(ma, "M15", TS, "kham_pha", von=10000.0)      # cung phien ban: dung lai
    monkeypatch.setattr(LU, "PHIEN_BAN_ENGINE", LU.PHIEN_BAN_ENGINE + 1)
    r1 = TN.danh_gia_luoi(ma, "M15", TS, "kham_pha", von=10000.0)
    assert "tu_so_tay" not in r1, "van tay khong gom phien ban engine"
    assert r1["tien"] == r0["tien"]                                                       # engine that khong doi gi o day


# ------------------------------------------------------------------ FILE QUY CACH THAT (config/luoi_quy_cach.json)
def test_file_quy_cach_that_hop_le_va_khop_bang_xuat_xm():
    """File that nam trong git (khong dung `khong_ghi_de`): moi muc phai qua duoc `quy_cach_cho`, pip = 10 point, va
    pip/hop_dong/point khop `symbol_info` XM demo ma may nha xuat (`reports/xuat_m1_xm.json`). Go nham mot so 0 o day se
    am tham doi luoi vang thanh luoi sai kich co - khong loi, khong canh bao."""
    from pathlib import Path
    bang, loi = LU._doc_ghi_de()
    assert loi == "" and set(bang) == {"XAUUSD", "USDJPY"}
    xuat = json.loads((Path(LU.LAB) / "reports" / "xuat_m1_xm.json").read_text(encoding="utf-8"))["ma"]
    for ma, gd in bang.items():
        qc, ly = LU.quy_cach_cho(ma, 4000.0 if ma == "XAUUSD" else 150.0, _cp(pm=0.05, pb=-0.02, sp=1e-4))
        assert qc is not None, ly
        x = xuat[ma]
        assert qc.point == pytest.approx(x["point"]) and qc.hop_dong == pytest.approx(x["hop_dong"])
        assert qc.pip == pytest.approx(10 * x["point"]), "pip phai la 10 point (quy uoc FX 5 chu so)"
        assert gd["da_doi_chieu"] is True and "xuat_m1_xm" in gd["nguon"]
    assert LU.quy_cach_cho("AUDCAD", 0.9, None)[0] == LU.QC_AUDCAD            # file khong dong toi hang so cu
