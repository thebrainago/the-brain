# -*- coding: utf-8 -*-
"""DOC VAN XUOI -> CO CHE. Bo test khoa HIEU CHUAN HAI CHIEU.

Mot bo doc tu choi TAT CA cho ra so lieu y het mot bo doc hieu chuan tot: ca
hai deu bao "0 rac". Nen moi bai kiem o day di theo cap:

  A. CAU LUAT THAT phai duoc doc RA DUNG - dung chi bao, dung chu ky, dung
     chieu, dung nguong. Doc ra "mot cai gi do" khong tinh la doc duoc.
  B. CAU BAY phai bi tu choi - va bay o day khong phai bay tuong tuong, chung
     lay tu chinh nhung gi da lot qua cac bo khop truoc cua du an nay:
       - chuoi tho: "rsi" trong "Ve-rsi-on", "orb" trong "col-orb-ar"
       - van canh chung chung: "alignment strategy" trong mot bai sinh hoc
       - chi bao ve duong bi doc thanh chien luoc vi co chu "sell signal"

Va mot bai kiem thu ba, quan trong khong kem: spec doc ra phai CHAY DUOC qua
`nhan/ngu_phap.py` va qua duoc phep cat nhin truoc tren du lieu that.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import doc_hieu as DH
from nhan import ngu_phap as NP

DEM = " Lorem ipsum dolor sit amet, a filler paragraph so the document passes the "\
      "minimum length gate used by the reader. It says nothing about trading. " * 2


def mot(vb: str):
    r = DH.doc_bai(vb + DEM, "thu", "test://vi_du")
    return r[0]["spec"] if r else None


class DocDuocCauLuatThat(unittest.TestCase):
    """CHIEU A: cau luat that phai ra DUNG spec."""

    def test_rsi2_kem_bo_loc_xu_huong(self):
        s = mot("Buy when the 2-period RSI closes below 10 and the close is "
                "above the 200-day moving average. Sell when the close crosses "
                "above the 5-day moving average. We hold for 5 days at most.")
        self.assertIsNotNone(s)
        self.assertEqual(s["chieu"], 1)
        self.assertEqual(s["giu"], 5)
        self.assertEqual(s["vao"][0]["trai"], {"chi_bao": "rsi", "n": 2})
        self.assertEqual(s["vao"][0]["phep"], "<")
        self.assertEqual(s["vao"][0]["phai"], {"hang": 10.0})
        self.assertEqual(s["vao"][1]["phep"], ">")
        self.assertEqual(s["vao"][1]["phai"]["n"], 200)
        self.assertEqual(s["ra"][0]["phep"], "cheo_len")
        self.assertEqual(s["ra"][0]["phai"]["n"], 5)

    def test_chu_ky_ghi_ro_khong_duoc_bi_thay_bang_mac_dinh(self):
        """Loi that lan chay dau: 'RSI(2)' bi doc thanh RSI mac dinh n=14 vi
        khop ngan bat dau muon hon khop dai, va phep 'lay cai cuoi cung' lay
        nham. Doc mot con so co san thanh mot con so bia ra la loi nang hon ca
        khong doc duoc."""
        for cach_viet, n in (("the 2-period RSI", 2), ("RSI(3)", 3),
                             ("the 14-day RSI", 14), ("RSI(2)", 2)):
            s = mot("Buy when %s is below 10. Exit after 3 days." % cach_viet)
            self.assertIsNotNone(s, cach_viet)
            self.assertEqual(s["vao"][0]["trai"]["n"], n, cach_viet)

    def test_vao_lenh_ban(self):
        s = mot("Go short when the close crosses below the 50-day moving average.")
        self.assertIsNotNone(s)
        self.assertEqual(s["chieu"], -1)
        self.assertEqual(s["vao"][0]["phep"], "cheo_xuong")

    def test_ban_khong_bi_doc_thanh_dong_vi_the(self):
        """'sell short' co chu 'sell'. Neu kiem RA truoc BAN thi mot chien luoc
        ban khong bien thanh mot dieu kien thoat lenh mo coi."""
        self.assertEqual(DH.loai_cau("We sell short when RSI is above 90"), "vao_ban")
        self.assertEqual(DH.loai_cau("We sell when RSI is above 90"), "ra")

    def test_dai_bollinger_thanh_zscore(self):
        """Ngu phap khong co phep tru/nhan nen 'sma - 2*sd' khong viet duoc,
        nhung zscore < -2 la TUONG DUONG, khong phai xap xi."""
        s = mot("Buy when the close falls below the lower Bollinger band.")
        self.assertIsNotNone(s)
        self.assertEqual(s["vao"][0]["trai"]["chi_bao"], "zscore")
        self.assertEqual(s["vao"][0]["trai"]["n"], 20)
        self.assertEqual(s["vao"][0]["phai"], {"hang": -2.0})

    def test_pha_vo_dinh_n_bar_phai_lui_mot_bar(self):
        """'20-day high' phai la dinh cua 20 bar TRUOC do. Neu tinh ca bar hien
        tai thi close > max(high) gan nhu khong bao gio dung - va khi no dung
        thi la do nhin truoc."""
        s = mot("Buy when the close is above the 20-day high. Hold for 10 days.")
        self.assertIsNotNone(s)
        t = s["vao"][0]["phai"]
        self.assertEqual(t["chi_bao"], "cao_nhat")
        self.assertEqual(t["n"], 20)
        self.assertEqual(t["cua"]["chi_bao"], "tre")

    def test_dang_bang_dau_dong(self):
        """Rat nhieu bai viet ta luat bang bang chu khong bang cau."""
        s = mot("Here are the rules.\nEntry: RSI(2) < 5\nExit: the close > "
                "the 10-day moving average\n")
        self.assertIsNotNone(s)
        self.assertEqual(s["vao"][0]["trai"], {"chi_bao": "rsi", "n": 2})
        self.assertEqual(s["vao"][0]["phai"], {"hang": 5.0})

    def test_ibs(self):
        s = mot("Buy when IBS is below 0.2 and hold for 1 day.")
        self.assertIsNotNone(s)
        self.assertEqual(s["vao"][0]["trai"], {"chi_bao": "ibs"})
        self.assertEqual(s["vao"][0]["phai"], {"hang": 0.2})
        self.assertEqual(s["ho"], "quay_ve_trung_binh")


class TuChoiCaiPhaiTuChoi(unittest.TestCase):
    """CHIEU B: bay phai bi tu choi."""

    def test_khong_co_nguong_thi_khong_doan(self):
        self.assertIsNone(mot("Buy when RSI is oversold and sell when it is "
                              "overbought."))

    def test_van_ban_ngoai_nganh(self):
        """Bay that: 'alignment strategy' trong mot bai sinh hoc tung duoc
        cham 2 diem 'co che' boi bo khop cu."""
        self.assertIsNone(mot(
            "The alignment strategy of ribosomes changes when the density of "
            "the initiation complex is above 30 units per micron."))

    def test_quang_cao(self):
        self.assertIsNone(mot("Buy our premium signals when you sign up today "
                              "and get 30 days free access to the channel."))

    def test_cau_co_hoac(self):
        """Ngu phap chi co VA. Doc mot cau OR thanh VA la doc SAI - nguy hiem
        hon doc thieu, vi ket qua trong nhu mot co che that."""
        self.assertIsNone(mot("Buy when the 2-period RSI is below 10 or the "
                              "close is below the 50-day moving average."))

    def test_muc_gia_tho_so_voi_hang_so(self):
        """'buy when the price is above 100' dung cu phap nhung 100 la muc gia
        cua mot ma tai mot nam - khong chuyen duoc di dau."""
        self.assertIsNone(mot("Buy when the price is above 100 and hold."))

    def test_ma_nguon_khong_di_qua_duong_van_xuoi(self):
        """Ma nguon co duong rieng. Neu tha vao day thi mot dong `if (x < 30)`
        bat ky trong mot thu vien bat ky thanh mot 'co che' hoan chinh."""
        ma = ("def on_bar(self, bar):\n"
              "    if self.rsi < 30 and self.close > self.ma:\n"
              "        self.buy(size=1);\n"
              "    return None;\n") * 12
        self.assertTrue(DH.la_ma_nguon(DH._chuan(ma)))
        self.assertEqual(DH.doc_bai(ma), [])

    def test_van_xuoi_that_khong_bi_nham_la_ma_nguon(self):
        """Bai kiem doi xung: bo loc ma nguon khong duoc an van xuoi that.
        Mot bai viet co the co dau ngoac, dau cham phay va vai cong thuc."""
        s = mot("The rules are simple; we use a short lookback. Buy when the "
                "2-period RSI (a momentum oscillator) is below 10, then exit "
                "after 5 days.")
        self.assertIsNotNone(s)


class NoiVaoNgocPhap(unittest.TestCase):
    """Spec doc ra phai CHAY DUOC, khong chi dung cu phap."""

    def test_qua_kiem_khai_bao(self):
        s = mot("Buy when the 2-period RSI closes below 10 and the close is "
                "above the 200-day moving average. Hold for 5 days.")
        self.assertEqual(NP.kiem_khai_bao(s), [])

    def test_chay_va_khong_nhin_truoc_tren_du_lieu_that(self):
        try:
            from nhan import du_lieu as DL
            df = None
            for ma in ("US500CASH", "EURCAD", "AUDNZD"):
                try:
                    d = DL.nap(ma, "D1")
                except Exception:
                    continue
                if d is not None and len(d) > 1200:
                    df = d
                    break
        except Exception:
            df = None
        if df is None:
            self.skipTest("khong co chuoi gia de kiem")
        s = mot("Buy when the 2-period RSI closes below 10 and the close is "
                "above the 200-day moving average. Sell when the close crosses "
                "above the 5-day moving average.")
        sach, mo_ta = NP.kiem_khong_nhin_truoc(s, df)
        self.assertTrue(sach, mo_ta)

    def test_van_tay_gop_ban_sao(self):
        """Hai bai ta cung mot luat = MOT co che voi hai trich dan, khong phai
        hai suat ngan sach thong ke."""
        a = mot("Buy when the 2-period RSI is below 10. Hold for 5 days.")
        b = mot("We go long once the RSI(2) is below 10. Holding period: 5 days.")
        self.assertIsNotNone(b)
        self.assertEqual(DH.van_tay_spec(a), DH.van_tay_spec(b))

    def test_van_tay_phan_biet_luat_khac_nhau(self):
        a = mot("Buy when the 2-period RSI is below 10. Hold for 5 days.")
        b = mot("Buy when the 2-period RSI is below 20. Hold for 5 days.")
        self.assertNotEqual(DH.van_tay_spec(a), DH.van_tay_spec(b))


class BonCoCheDocSaiNgay23_08(unittest.TestCase):
    """Bon co che SAI da duoc dang ky that truoc khi bi phat hien. Moi cai mot
    bai kiem, vi ca bon deu "dung cu phap" - chung chi sai NGHIA."""

    def test_thuc_the_html_khong_duoc_cat_cau(self):
        """`&apos;` chua dau CHAM PHAY, va bo tach menh de cat o dau cham phay.
        Cau "the 10-bar moving average of Bitcoin&apos;s close sits above the
        60-bar moving average" bi cat lam doi -> ve trai tu `sma10` thanh
        `close`. Phai giai ma thuc the TRUOC khi phan tich."""
        cau = ("buy when the 10-bar moving average of Bitcoin&apos;s close "
               "sits above the 60-bar moving average")
        dk, _ = DH.dieu_kien_trong_cau(DH._chuan(cau))
        self.assertTrue(dk)
        self.assertEqual(dk[0]["trai"], {"chi_bao": "sma", "n": 10, "cot": "close"})
        self.assertEqual(dk[0]["phai"]["n"], 60)

    def test_cau_ta_ca_hai_chieu_bi_tu_choi(self):
        """Lay CHIEU tu menh de sau va DIEU KIEN tu menh de truoc = ra co che
        nguoc han. Tu choi ca cau con hon doc nguoc."""
        cau = ("The strategy enters long positions when price breaks below the "
               "lower band and enters short positions when price breaks above "
               "the upper band")
        self.assertEqual(DH.dieu_kien_trong_cau(cau)[0], [])

    def test_cau_dinh_nghia_chi_bao_bi_tu_choi(self):
        cau = "RSI strategy: Buy when RSI is oversold (<30), sell when overbought (>70)"
        self.assertEqual(DH.dieu_kien_trong_cau(cau)[0], [])

    def test_luat_mot_chieu_van_phai_LOT(self):
        """Bai kiem doi xung cua hai cai tren: chan hai chieu khong duoc chan
        luon nhung cau chi noi mot chieu."""
        s = mot("We go long when the close is above the 200-day moving average. "
                "Hold for 10 days.")
        self.assertIsNotNone(s)
        self.assertEqual(s["chieu"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
