# -*- coding: utf-8 -*-
"""TIEU CHI DUYET CUA CHU DU AN (25/09/2026) - moi cong phai noi cung mot cau.

Nguyen van: *"toi khong quan tam martingale hay dca hay la phuong phap gi. Toi
trade don bay toi chap nhan rui ro, chi can co lai va maxdd duoi 80% la ok"*.

Hieu chuan HAI chieu (luat cua lab): moi cong co ca phep thu "phai QUA" (he co
lai nhung thua mua-giu, he kieu martingale) lan "phai TRUOT" (khong lai, DD >=
80%). Mot cong tu choi tat ca cho so lieu y het mot cong tot.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd
LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import cham_diem as CD          # noqa: E402
from nhan import cong as CONG             # noqa: E402
from nhan import cong_ra_tien as CRT      # noqa: E402
from nhan import nc_thi_nghiem as TN      # noqa: E402
from nhan import so as SO                 # noqa: E402


# ------------------------------------------------------------ MOT NGUON
def test_moi_cong_doc_cung_mot_tran_sut_giam():
    assert CD.TRAN_SUT_GIAM == 80.0
    assert CRT.TRAN_DD == CD.TRAN_SUT_GIAM / 100.0
    assert TN.DD_TRAN == CD.TRAN_SUT_GIAM / 100.0
    assert CRT.MUC_CAGR == 0.0, "nguong duyet la CO LAI, khong phai 20%/nam"


def test_cong_chinh_chi_chan_tien_va_tinh_dung_cua_so():
    assert set(CONG.CHAN_CUNG) == {"7_chi_phi_do_duoc", "8_du_lenh", "11_khong_an_khe_dao_ngay",
                                   "14_co_lai_sau_phi", "15_sut_giam_duoi_tran"}
    for k in ("1_loi_hon_mua_giu", "2_sharpe_hon_mua_giu", "3_calmar_hon_mua_giu",
              "12_rr_thuc_te", "13_edge_vuot_spread"):
        assert k in CONG.NHAN_MEM, k
    assert not set(CONG.CHAN_CUNG) & set(CONG.NHAN_MEM)
    assert CONG.THE_HE_CONG >= 6, "doi luat quyet dinh ma khong tang the he cong"


# ------------------------------------------------------------ cong.xet
def _so_sanh(lai=10.0, dd=-20.0, lai_bh=1.0):
    return {
        "he": {"tong_lai_pct": lai, "sharpe": 1.0, "calmar": 1.0, "max_dd_pct": dd,
               "phoi_nhiem": 0.5, "so_bar": 300},
        "mua_giu_net": {"tong_lai_pct": lai_bh, "sharpe": 0.1, "calmar": 0.1},
        "alpha_vs_mua_giu": {"t_alpha": 3.0, "alpha_nam_pct": 5.0},
    }


def _he_martingale():
    """30 lenh 2 bar cach nhau 1 bar phang: 29 lenh +0,1%, 1 lenh -1% -> rr 0,1, co lai."""
    v, l = [], []
    for i in range(30):
        loi = -0.01 if i == 17 else 0.001
        v += [1.0, 1.0, 0.0]
        l += [loi / 2, loi / 2, 0.0]
    idx = pd.date_range("2026-01-01", periods=len(v), freq="h")
    return SimpleNamespace(so_lenh=100, loi=np.array(l), index=idx, vi_the=np.array(v))


class CongChinh(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._db_cu = SO.DB
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()

    def _xet(self, so_sanh, kq_he=None):
        kq_he = kq_he or SimpleNamespace(
            so_lenh=100, loi=np.full(300, 1e-4), index=pd.date_range("2026-01-01", periods=300,
                                                                      freq="h"),
            vi_the=np.ones(300))
        pl = {"p_xau_nhat": 0.04, "null_hop_le": True, "bootstrap_hop_le": True}
        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh), \
                mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]), \
                mock.patch.object(CONG, "placebo", return_value=pl), \
                mock.patch.object(CONG, "che_do_cong", return_value="nhan"):
            return CONG.xet(None, kq_he, SimpleNamespace(),
                            SimpleNamespace(do_tin="DO", canh_bao=None), gt_ma="t:tieu_chi",
                            da_dang_ky=True, tren_holdout=False, ghi_so=False)

    def test_co_lai_ma_THUA_mua_giu_van_qua_va_mang_nhan(self):
        ra = self._xet(_so_sanh(lai=5.0, lai_bh=40.0))
        self.assertFalse(ra["dieu_kien"]["1_loi_hon_mua_giu"])
        self.assertEqual(ra["verdict"], "UNG_VIEN")
        self.assertTrue(any("mua-giu" in x for x in ra["nhan"]))
        self.assertEqual(ra["verdict_chan"], "FAIL", "ban chat nhat van phai doc duoc")

    def test_kieu_martingale_co_lai_van_qua_va_mang_nhan(self):
        ra = self._xet(_so_sanh(), _he_martingale())
        self.assertFalse(ra["dieu_kien"]["12_rr_thuc_te"])
        self.assertEqual(ra["verdict"], "UNG_VIEN")
        self.assertTrue(any("martingale" in x for x in ra["nhan"]))

    def test_khong_co_lai_thi_truot(self):
        ra = self._xet(_so_sanh(lai=-0.5))
        self.assertEqual(ra["verdict"], "FAIL")
        self.assertFalse(ra["dieu_kien"]["14_co_lai_sau_phi"])

    def test_sut_giam_80_thi_truot_duoi_80_thi_qua(self):
        self.assertEqual(self._xet(_so_sanh(dd=-80.0))["verdict"], "FAIL")
        self.assertEqual(self._xet(_so_sanh(dd=-79.9))["verdict"], "UNG_VIEN")

    def test_thieu_so_sut_giam_thi_do_tren_chuoi_loi_khong_doan(self):
        ss = _so_sanh()
        del ss["he"]["max_dd_pct"]
        ra = self._xet(ss)                      # chuoi 1e-4 moi bar: DD 0
        self.assertTrue(ra["dieu_kien"]["15_sut_giam_duoi_tran"])


# ------------------------------------------------------------ cong_ra_tien
def test_cong_ra_tien_so_voi_mua_giu_la_nhan_khong_chan():
    """He co lai deu, DD thap, du lenh, du nam - nhung mua-giu cung DD ra tien hon."""
    idx = pd.date_range("2010-01-01", periods=2600, freq="B")
    rng = np.random.default_rng(3)
    gia = 100 * np.exp(np.cumsum(0.0012 + rng.normal(0, 0.004, len(idx))))
    df = pd.DataFrame({"open": gia, "high": gia * 1.002, "low": gia * 0.998, "close": gia},
                      index=idx)
    vi_the = (np.arange(len(idx)) % 10 < 3).astype(float)       # vao/ra deu -> nhieu lenh
    from nhan import chi_phi as CP
    cp = CP.MoHinhChiPhi(ma="T", spread_frac_chung=0.00005, do_tin="DO")
    r = CRT.xet(df, vi_the, cp, ma="T", khung="D1")
    assert r["he"]["cagr"] > 0 and abs(r["he"]["maxdd"]) < CRT.TRAN_DD
    assert r["nhan"]["3_hon_mua_giu_cung_DD"] is False, "fixture phai THUA mua-giu"
    assert "3_hon_mua_giu_cung_DD" not in r["truot"]
    assert r["verdict"] == "RA_TIEN", r["truot"]


# ------------------------------------------------------------ nc: tien duoi tran
def _x(mu, sd, n=3000, hat=0):
    return np.random.default_rng(hat).normal(mu, sd, n)


def test_co_lai_khong_phu_thuoc_don_bay():
    x = _x(0.0004, 0.01)
    t = TN.tien_duoi_tran(np.log1p(x), np.zeros_like(x), 12.0)
    assert t["co_lai"] == (x.sum() > 0)
    y = _x(-0.0004, 0.01)
    u = TN.tien_duoi_tran(np.log1p(y), np.zeros_like(y), 12.0)
    assert not u["co_lai"] and u["gioi_han"] == "KHONG_LAI"


def test_khong_bao_gio_bao_cagr_o_don_bay_qua_kelly_va_luon_duoi_tran():
    for mu, sd in ((0.0002, 0.01), (0.0006, 0.004), (0.00005, 0.002)):
        x = _x(mu, sd, hat=7)
        t = TN.tien_duoi_tran(np.log1p(x), np.zeros_like(x), 12.0)
        if not t["co_lai"]:
            continue
        assert t["dd"] < TN.DD_TRAN
        L = t["don_bay"]
        tot = TN.o_don_bay(x, 12.0, L)["cagr"]
        for k in (0.8, 0.95):
            khac = TN.o_don_bay(x, 12.0, L * k)
            assert khac["cagr"] <= tot + 1e-9, "giam don bay khong duoc ra NHIEU tien hon"
        if t["gioi_han"] == "KELLY":
            assert TN.o_don_bay(x, 12.0, L * 1.05)["cagr"] <= tot + 1e-9


def test_he_so_lot_luoi_tai_tran_la_chinh_xac_tren_duong_equity():
    rng = np.random.default_rng(5)
    e = 10000 + np.cumsum(rng.normal(3, 40, 4000))
    k = TN._he_so_lot_tai_tran(e, 10000.0)
    v = 10000 + k * (e - 10000)
    dd = float(np.max(1 - v / np.maximum.accumulate(v)))
    assert abs(dd - (TN.DD_TRAN - 1e-3)) < 1e-3


# ------------------------------------------------------------ nc: nhan (khong chan)
def test_tach_beta_bat_he_nghieng_mua_tren_tai_san_troi_nhung_khong_bat_canh_thoi_diem():
    n = 2000
    r = np.full(n, 0.0004)                                 # tai san troi deu
    v = np.ones(n)                                          # luon mua = beta thuan
    kq = SimpleNamespace(vi_the=v, r=r, loi_tho=v * r)
    assert TN.tach_beta(kq)["ty_le_beta"] > 0.99
    r2 = np.tile([0.002, -0.002], n // 2)                   # khong troi, dao chieu deu
    v2 = np.tile([1.0, -1.0], n // 2)                       # canh dung moi nhip
    kq2 = SimpleNamespace(vi_the=v2, r=r2, loi_tho=v2 * r2)
    assert abs(TN.tach_beta(kq2)["ty_le_beta"]) < 0.01


def test_duoi_lo_doi_du_lenh_de_thay_cu_thua_theo_rr():
    # rr 0,025 (TP 0,1 ATR / SL 4 ATR): hoa von khi thua 2,4% -> can >= 123 lenh
    d = TN.duoi_lo({"so_lenh": 20, "ty_le_thang": 0.95, "rr": 0.025})
    assert d["so_lenh_can_de_thay_duoi"] == 123 and "canh_bao" in d
    assert "canh_bao" not in TN.duoi_lo({"so_lenh": 200, "ty_le_thang": 0.97, "rr": 0.025})
    assert "canh_bao" not in TN.duoi_lo({"so_lenh": 30, "ty_le_thang": 0.5, "rr": 1.2})
    assert "chua thay lenh thua" in TN.duoi_lo({"so_lenh": 40, "ty_le_thang": 1.0, "rr": None})["canh_bao"]


def test_kich_ban_beta_troi_nhu_chi_so_va_khong_co_edge_sau_phi():
    from nhan import nc_du_lieu as NDL
    d = NDL.nap("TONG_HOP_BETA_1", "D1")
    r = np.log(d["open"]).diff().dropna()
    assert 0.02 < r.mean() * 260 < 0.12
    assert NDL.CO_EDGE_SAU_PHI["BETA"] is False
