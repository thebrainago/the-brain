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
    # Khung GIO, khong phai ngay. Tu 03/09/2026 `chi_bao='gio'` nem
    # `KhungThieuGio` tren khung khong co gio (xem `mau._phai_co_gio`), va mot
    # khung ngay lam bai kiem nay bao oan rang `gio` "khai ra ma goi khong
    # duoc". Moi toan hang con lai deu khong quan tam khung nen doi sang gio
    # la vo hai. Chieu nguoc duoc chot o `GacKhungThieuGio` ben duoi.
    idx = pd.date_range("2020-01-01", periods=n, freq="h")
    g = pd.Series(100 + np.cumsum(np.random.default_rng(1).normal(0, 1, n)), index=idx)
    return pd.DataFrame({"open": g, "high": g + 1.0, "low": g - 1.0,
                         "close": g, "tick_volume": 1000.0})



def _df_that(n: int = 1500) -> pd.DataFrame:
    """Khung co HINH DANG NEN THAT - `_df` o tren khong dung duoc cho phep cat.

    Do 12/09/2026 khi dung `_df` lam khung cho bai kiem nhin truoc: nam toan
    hang ra chuoi HANG SO nen khong nguong nao chia duoc tin hieu, va phep cat
    tren mot tin hieu hang so khong chung minh duoc gi.

        bien_do     high-low   = (g+1)-(g-1) = 2,0 o MOI bar
        ibs         (c-l)/(h-l) = 1/2        o MOI bar
        than_nen    |c-o|      = 0           vi `_df` dat open = close
        khoi_luong  tick_volume = 1000,0     o MOI bar
        thang       400 bar gio = 16 ngay    -> chi co thang 1

    Day khong phai loi cua `_df`: bai kiem "goi duoc khong" khong can hinh dang
    nen. Nhung no la loi neu dem dung cho bai kiem "co nhin truoc khong" - va
    ca hai bai deu o trong file nay, nen ghi ro o day de lan sau khong lam lai.

    1.500 bar gio = 62 ngay, du de `thang` va `ngay_trong_thang` doi gia tri.
    """
    r = np.random.default_rng(20260912)
    idx = pd.date_range("2020-01-01", periods=n, freq="h")
    dong = 100.0 + np.cumsum(r.normal(0, 0.4, n))
    mo = np.empty(n)
    mo[0] = dong[0]
    mo[1:] = dong[:-1] + r.normal(0, 0.1, n - 1)      # khe gia nho giua hai bar
    rau_tren = np.abs(r.normal(0, 0.25, n))
    rau_duoi = np.abs(r.normal(0, 0.25, n))
    cao = np.maximum(mo, dong) + rau_tren
    thap = np.minimum(mo, dong) - rau_duoi
    return pd.DataFrame(
        {"open": mo, "high": cao, "low": thap, "close": dong,
         "tick_volume": np.round(r.lognormal(7.0, 0.5, n))}, index=idx)


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
    # `moc_ky` mac dinh lay moc THANG. Khung kiem chi 1.500 bar gio = 62 ngay,
    # tuc `dong_thang_truoc` chi co 2-3 gia tri roi rac - khong nguong nao chia
    # duoc 5-95%. Do la chuyen DOI SO, khong phai loi ngu phap: doi sang moc
    # NGAY thi co 62 muc va phep cat chay binh thuong.
    "moc_ky": {"ky": "ngay", "lay": "dong_truoc"},
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


class GacKhungThieuGio(unittest.TestCase):
    """Chieu nguoc cua bai tren: toan hang theo GIO phai TU CHOI khung khong co gio.

    Do that 03/09/2026 tren US500CASH.D1 (moi bar hour=0): hai co che DSL
    `mat_can_bang_lenh_dong_cua` (gio>=20 va gio<=22) va
    `hoan_lai_sau_gio_dinh_gia_nav` (gio>=16 va gio<17) cho tin hieu TOAN 0 va
    khong doi khi doi bat ky tham so nao - nen bo do on dinh cham chung la
    "cao nguyen hoan hao".
    """

    def _df_ngay(self, n: int = 200) -> pd.DataFrame:
        idx = pd.date_range("2020-01-01", periods=n, freq="D")
        g = pd.Series(100.0 + np.arange(n) * 0.1, index=idx)
        return pd.DataFrame({"open": g, "high": g + 1, "low": g - 1, "close": g,
                             "tick_volume": 1000.0})

    def test_gio_tren_khung_ngay_thi_nem_loi(self):
        from nhan import mau as MAU
        with self.assertRaises(MAU.KhungThieuGio):
            NP.toan_hang(self._df_ngay(), {"chi_bao": "gio"})

    def test_gio_tren_khung_gio_thi_chay(self):
        s = NP.toan_hang(_df(), {"chi_bao": "gio"})
        self.assertGreater(len(set(s.tolist())), 1)

    def test_toan_hang_thoi_gian_KHAC_van_chay_tren_khung_ngay(self):
        """Chi `gio` bi chan. `ngay_trong_tuan`/`thang` van co nghia tren D1."""
        d = self._df_ngay()
        for cb in ("ngay_trong_tuan", "ngay_trong_thang", "thang"):
            self.assertEqual(len(NP.toan_hang(d, {"chi_bao": cb})), len(d), cb)



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


class MoiToanHangDeuKHONG_NHIN_TRUOC(unittest.TestCase):
    """Cong `ca_kiem_nhin_truoc` cua khoi 1 (KE_HOACH_XAY.md).

    `test_goi_that_tung_ten_mot` chung minh moi toan hang GOI DUOC. No khong noi
    gi ve viec toan hang do co doc bar tuong lai hay khong. Mot toan hang goi
    duoc ma ro ri thi con te hon mot toan hang khong goi duoc: cai thu hai nem
    loi, cai thu nhat tra ve mot edge gia va di tiep qua moi cong phia sau.

    Bai kiem chay `kiem_khong_nhin_truoc` (phep CAT) tren TUNG toan hang mot.

    HAI DIEU PHAI DUNG cung luc, neu khong bai kiem nay vo nghia:

      1. Tin hieu phai THUC SU KICH HOAT. Luc cua phep cat ti le voi tan suat
         kich hoat - do 06/09/2026: mot ro ri co y lam lech 16/400 bar van lot
         vi co che chi kich hoat 2,75% so bar. Nen nguong o day dat tai PHAN VI
         cua chinh toan hang do, va bai kiem TU CHOI ("khong do duoc", khong
         phai "dat") neu khong tim duoc nguong nao cho ti le kich hoat 5-95%.
      2. Bay phai tung bat duoc cai gi. `test_do_nhay_bay_phai_rung` chen mot
         ro ri co y roi doi hoi phep cat GAO LEN. Mot bay chua bao gio rung thi
         khong phan biet duoc voi mot bay hong.
    """

    #: Ti le kich hoat chap nhan duoc. Ngoai khoang nay thi phep cat gan nhu
    #: chac chan khong cham vao bar tin hieu -> ket qua "dat" khong mang tin.
    SAN, TRAN = 0.05, 0.95

    def _khai_bao(self, cb: str, df: pd.DataFrame):
        """-> (spec, ti_le_kich_hoat) hoac (None, ly_do) neu khong do duoc."""
        t = {"chi_bao": cb, "n": 14}
        t.update(_DOI_SO.get(cb, {}))
        if cb in _CAN_CUA:
            t["cua"] = {"chi_bao": "gia", "cot": "close"}
        s = pd.Series(NP.toan_hang(df, t)).astype(float)
        if not np.isfinite(s.to_numpy()).any():
            return None, "toan hang tra toan NaN"

        # Quet vai phan vi thay vi chi lay trung vi: chuoi roi rac (`gio`,
        # `ngay_trong_tuan`, `trang_thai_lat`) co the cho ti le 0% hoac 100% o
        # trung vi trong khi mot phan vi khac lai chia doi dep.
        for q in (0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8):
            nguong = float(np.nanquantile(s.to_numpy(), q))
            if not np.isfinite(nguong):
                continue
            spec = {"ten": f"nhin_truoc_{cb}", "ho": "xu_huong", "chieu": 1,
                    "giu": 1, "ra": [],
                    "vao": [{"trai": t, "phep": ">", "phai": {"hang": nguong}}],
                    "co_che": "khai bao toi thieu de kiem nhin truoc - khong dang ky"}
            ti_le = float(np.mean(np.abs(NP.sinh_tu_spec(spec, df)) > 0))
            if self.SAN <= ti_le <= self.TRAN:
                return spec, ti_le
        return None, "khong tim duoc nguong cho ti le kich hoat 5-95%"

    def test_tung_toan_hang_qua_phep_cat(self):
        df = _df_that()
        ro_ri, khong_do_duoc = [], []
        for cb in sorted(NP.CHI_BAO_CO):
            with self.subTest(chi_bao=cb):
                spec, phu = self._khai_bao(cb, df)
                if spec is None:
                    khong_do_duoc.append(f"{cb}: {phu}")
                    continue
                ok, mo_ta = NP.kiem_khong_nhin_truoc(spec, df)
                if not ok:
                    ro_ri.append(f"{cb} (kich hoat {phu:.0%}): {mo_ta}")
        self.assertEqual(ro_ri, [], "toan hang DOC BAR TUONG LAI: " + str(ro_ri))
        # `CHUA_DO_DUOC` khong duoc im lang thanh `DAT` - ba trang thai, khong hai.
        self.assertEqual(khong_do_duoc, [],
                         "toan hang khong dung duoc phep cat: " + str(khong_do_duoc))

    def test_do_nhay_bay_phai_rung(self):
        """Hieu chuan chieu nguoc. Chen ro ri co y vao `rsi` roi doi phep cat bat."""
        df = _df_that()
        spec, _ = self._khai_bao("rsi", df)
        self.assertIsNotNone(spec)

        goc = NP.toan_hang

        def _ro_ri(d, t):
            x = goc(d, t)
            if isinstance(t, dict) and t.get("chi_bao") == "rsi":
                return pd.Series(x).shift(-1)      # doc RSI cua bar KE TIEP
            return x

        NP.toan_hang = _ro_ri
        try:
            ok, mo_ta = NP.kiem_khong_nhin_truoc(spec, df)
        finally:
            NP.toan_hang = goc
        self.assertFalse(ok, "chen ro ri co y ma phep cat van bao dat - BAY HONG")
        self.assertIn("NHIN TRUOC", mo_ta)


if __name__ == "__main__":
    unittest.main(verbosity=2)
