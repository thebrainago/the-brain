# -*- coding: utf-8 -*-
"""BANG "TOAN HANG CON THIEU" DA GIAU DUNG NHUNG CAI CAN NHAT.

Do 01/09/2026. `thu_hoi_thanh_phan._DIEN_DAT_DUOC` la mot ban CHEP TAY cua danh
sach toan hang ngu phap noi duoc, va no da lech ca hai chieu:

  * khai THUA `macd`, `bollinger`, `dong_luong` - ngu phap khong he co chung.
    Hau qua: bang `toan_hang_con_thieu`, thu duy nhat noi cho ta biet nen them
    gi, giau dung ba toan hang duoc dung nhieu nhat trong ma that
    (macd 115 lan - hang 2, dong_luong 36, bollinger 35).
  * khai THIEU 6 toan tu co that (`tb_cua_cac`, `cao_nhat_cua_cac`,
    `thap_nhat_cua_cac`, `tong_cua_cac`, `dem_lien_tiep`, `trang_thai_lat`).
    Thanh phan nao dung chung bi cham la "khong dien dat duoc" va bi vut.

Va bang do con doc tu co `dien_dat_duoc` DA LUU luc thu hoach, nen no van doi
them `wma`/`smma`/`cci` trong khi ca ba da co tu buoi sang cung ngay.

Bo test nay khong doc lai danh sach - no GOI THAT tung toan hang mot. Mot danh
sach chep tay se lech lai; mot bai test goi that thi khong.
"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from nhan import ngu_phap as NP
from nhan import thu_hoi_thanh_phan as TP


def _df(n: int = 300) -> pd.DataFrame:
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    g = pd.Series(100 + np.cumsum(np.random.default_rng(1).normal(0, 1, n)), index=idx)
    return pd.DataFrame({"open": g, "high": g + 1.0, "low": g - 1.0,
                         "close": g, "tick_volume": 1000.0})


#: Toan hang can doi so rieng ngoai `n`. Khong co day thi bai kiem se bao chung
#: "khong chay duoc" trong khi that ra chung chi thieu doi so.
_DOI_SO = {
    "tb_cua_cac": {"toan_hang": [{"chi_bao": "ema", "n": 3}, {"chi_bao": "ema", "n": 5}]},
    "cao_nhat_cua_cac": {"toan_hang": [{"chi_bao": "ema", "n": 3}, {"chi_bao": "ema", "n": 5}]},
    "thap_nhat_cua_cac": {"toan_hang": [{"chi_bao": "ema", "n": 3}, {"chi_bao": "ema", "n": 5}]},
    "tong_cua_cac": {"toan_hang": [{"chi_bao": "ema", "n": 3}, {"chi_bao": "ema", "n": 5}]},
    "tuyen_tinh": {"toan_hang": [{"chi_bao": "gia"}], "he_so": [1.0]},
    "tuong_quan": {"toan_hang": [{"chi_bao": "gia"}, {"chi_bao": "rsi"}]},
    "trang_thai_lat": {
        "len": {"trai": {"chi_bao": "rsi"}, "phep": ">", "phai": {"hang": 50}},
        "xuong": {"trai": {"chi_bao": "rsi"}, "phep": "<", "phai": {"hang": 50}}},
    "dem_lien_tiep": {
        "khi": {"trai": {"chi_bao": "rsi"}, "phep": ">", "phai": {"hang": 50}}},
}
#: Toan tu BIEN DOI: chi co nghia khi nhan mot toan hang con qua `cua`.
_CAN_CUA = {"tb", "do_lech", "phuong_sai", "zscore", "phan_vi", "doi", "doi_pct",
            "tre", "cao_nhat", "thap_nhat", "tuyet_doi", "tong"}


class MoiToanHangKhaiRaDeuGOI_DUOC(unittest.TestCase):
    """Chot chan chinh: `CHI_BAO_CO` phai la su that, khong phai mot loi hua."""

    def test_goi_that_tung_ten_mot(self):
        df = _df()
        hong = []
        for cb in sorted(NP.CHI_BAO_CO):
            t = {"chi_bao": cb, "n": 14}
            t.update(_DOI_SO.get(cb, {}))
            if cb in _CAN_CUA:
                t["cua"] = {"chi_bao": "gia", "cot": "close"}
            try:
                s = NP.toan_hang(df, t)
                self.assertEqual(len(s), len(df), cb)
            except Exception as e:
                hong.append(f"{cb}: {type(e).__name__}: {e}")
        self.assertEqual(hong, [], "ten khai trong CHI_BAO_CO ma goi khong duoc")

    def test_bo_rut_thanh_phan_dung_chung_mot_danh_sach(self):
        self.assertIs(TP._DIEN_DAT_DUOC, NP.CHI_BAO_CO)
        self.assertIs(TP._NHAN_COT, NP.CHI_BAO_NHAN_COT)

    def test_nhan_cot_la_tap_con_cua_co(self):
        self.assertTrue(NP.CHI_BAO_NHAN_COT <= NP.CHI_BAO_CO,
                        sorted(NP.CHI_BAO_NHAN_COT - NP.CHI_BAO_CO))

    def test_ten_khong_biet_van_nem_loi(self):
        """Hieu chuan chieu nguoc: neu moi ten deu chay thi bai tren vo nghia."""
        with self.assertRaises(KeyError):
            NP.toan_hang(_df(), {"chi_bao": "khong_he_ton_tai"})


class BaToanHangDaBiGIAU(unittest.TestCase):

    def setUp(self):
        self.df = _df()

    def test_macd_dung_bang_hieu_hai_ema(self):
        from nhan import mau as MAU
        got = NP.toan_hang(self.df, {"chi_bao": "macd", "nhanh": 12, "cham": 26})
        mong = MAU.ema(self.df["close"], 12) - MAU.ema(self.df["close"], 26)
        pd.testing.assert_series_equal(got, mong, check_names=False)

    def test_macd_lay_tin_hieu_va_hieu(self):
        duong = NP.toan_hang(self.df, {"chi_bao": "macd", "lay": "macd"})
        tin = NP.toan_hang(self.df, {"chi_bao": "macd", "lay": "tin_hieu"})
        hieu = NP.toan_hang(self.df, {"chi_bao": "macd", "lay": "hieu"})
        pd.testing.assert_series_equal(hieu, duong - tin, check_names=False)

    def test_bollinger_ba_dai_dung_thu_tu(self):
        tren = NP.toan_hang(self.df, {"chi_bao": "bollinger", "n": 20, "k": 2.0, "lay": "tren"})
        giua = NP.toan_hang(self.df, {"chi_bao": "bollinger", "n": 20, "k": 2.0, "lay": "giua"})
        duoi = NP.toan_hang(self.df, {"chi_bao": "bollinger", "n": 20, "k": 2.0, "lay": "duoi"})
        m = tren.notna()
        self.assertTrue((tren[m] >= giua[m]).all())
        self.assertTrue((giua[m] >= duoi[m]).all())

    def test_bollinger_khop_voi_tuyen_tinh_viet_tay(self):
        """No phai la LOI TAT cho mot thu ngu phap da viet duoc, khong phai mot
        phep tinh khac."""
        got = NP.toan_hang(self.df, {"chi_bao": "bollinger", "n": 20, "k": 2.0, "lay": "duoi"})
        tay = NP.toan_hang(self.df, {
            "chi_bao": "tuyen_tinh", "he_so": [1.0, -2.0],
            "toan_hang": [
                {"chi_bao": "tb", "n": 20, "cua": {"chi_bao": "gia", "cot": "close"}},
                {"chi_bao": "do_lech", "n": 20, "cua": {"chi_bao": "gia", "cot": "close"}}]})
        pd.testing.assert_series_equal(got, tay, check_names=False)

    def test_dong_luong_bang_doi(self):
        a = NP.toan_hang(self.df, {"chi_bao": "dong_luong", "n": 10})
        b = NP.toan_hang(self.df, {"chi_bao": "doi", "n": 10,
                                   "cua": {"chi_bao": "gia", "cot": "close"}})
        pd.testing.assert_series_equal(a, b, check_names=False)


class NguonGiaTongHop(unittest.TestCase):

    def test_hl2_hlc3_ohlc4(self):
        df = _df()
        hl2 = NP.toan_hang(df, {"chi_bao": "gia", "cot": "hl2"})
        pd.testing.assert_series_equal(hl2, (df["high"] + df["low"]) / 2.0,
                                       check_names=False)
        hlc3 = NP.toan_hang(df, {"chi_bao": "gia", "cot": "hlc3"})
        pd.testing.assert_series_equal(
            hlc3, (df["high"] + df["low"] + df["close"]) / 3.0, check_names=False)

    def test_sma_tren_hl2_khong_con_bi_vut(self):
        """`ta.sma(hl2, 20)` la dang co that trong ma; truoc 01/09 no bi cham la
        'khong dien dat duoc' va thanh phan bi bo."""
        ok, thieu = TP.dien_dat_duoc({"chi_bao": "sma", "cot": "hl2"})
        self.assertTrue(ok, thieu)
        s = NP.toan_hang(_df(), {"chi_bao": "sma", "n": 20, "cot": "hl2"})
        self.assertEqual(len(s), 300)

    def test_chi_bao_KHONG_nhan_cot_thi_van_bao_thieu(self):
        """Hieu chuan chieu nguoc: neu moi thu deu 'dien dat duoc' thi bang
        con thieu tro thanh mot bang rong vo nghia."""
        ok, thieu = TP.dien_dat_duoc({"chi_bao": "atr", "cot": "hl2"})
        self.assertFalse(ok)
        self.assertIn("atr", thieu)


class BangConThieuPhaiCHAM_LAI(unittest.TestCase):

    def test_khong_doi_them_thu_da_co(self):
        """Bang doc tu co `dien_dat_duoc` DA LUU se doi them lai nhung toan hang
        vua duoc them. Do 01/09: no van doi wma/smma/cci sau khi ca ba da co."""
        doi_them = {x["chi_bao"] for x in TP.toan_hang_con_thieu(50)
                    if x["con_thieu"].startswith(TP.THIEU_TOAN_HANG)}
        da_co = doi_them & NP.CHI_BAO_CO
        self.assertEqual(
            da_co, set(),
            f"bang con thieu dang doi them thu ngu phap DA CO: {sorted(da_co)}")

    def test_van_con_phan_biet_duoc_hai_loai_thieu(self):
        """Hieu chuan chieu nguoc. `atr` tren `hl2` la "co toan hang nhung bien
        the nay chua nhan duoc" - khac han "chua co toan hang". Gop hai loai lam
        mot thi bang uu tien tro thanh vo nghia."""
        ds = TP.toan_hang_con_thieu(50)
        thieu_han = [x for x in ds if x["con_thieu"].startswith(TP.THIEU_TOAN_HANG)]
        chi_hep = [x for x in ds if not x["con_thieu"].startswith(TP.THIEU_TOAN_HANG)]
        self.assertTrue(thieu_han, "phai con toan hang that su chua co")
        self.assertTrue(chi_hep, "phai con bien the chua nhan duoc")
        self.assertTrue({x["chi_bao"] for x in chi_hep} <= NP.CHI_BAO_CO)


if __name__ == "__main__":
    unittest.main(verbosity=2)
