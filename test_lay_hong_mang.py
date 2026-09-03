# -*- coding: utf-8 -*-
"""HONG MANG KHONG DUOC DICH THANH "HET TRANG".

Do 03/09/2026. `seeker._lay` tra `None` cho CA BA truong hop: 200-nhung-rong,
404, va khong-noi-duoc-mang. `n_mql5_code` dich `None` thanh "qua trang cuoi":

    if not txt:
        if n > 1:
            cuoi[muc] = n - 1     # <- coi TAI HONG la HET TRANG
            trang[muc] = 1

Hau qua do duoc: mql5.com bi loc SNI tren may nay (mo bang requests VA bang
Chrome CDP deu hong: `RemoteDisconnected` / `ERR_HTTP2_PROTOCOL_ERROR`), va
con tro bien gioi bi ghi `trang_cuoi = 3` cho gan het danh muc — trong khi
MQL5 Code Base co hang chuc trang. Tu do nguon **lang le bao "het trang" mai
mai**, va bang thu hoach hien ra nhu mot nguon da vet can.

Cung mot ho benh voi ca ngay hom nay: mot that bai duoc bao cao nhu mot ket
qua binh thuong.
"""
from __future__ import annotations

import unittest
from unittest import mock

from tru import seeker as SK


class _R:
    def __init__(self, ma, text=""):
        self.status_code = ma
        self.text = text


class PhanBietBaTruongHop(unittest.TestCase):
    def test_200_thi_tra_van_ban_va_KHONG_phai_hong_mang(self):
        with mock.patch("requests.get", return_value=_R(200, "xin chao")):
            self.assertEqual(SK._lay("http://x"), "xin chao")
        self.assertFalse(SK.lay_that_bai_vi_mang())
        self.assertEqual(SK.LAN_LAY_CUOI["ma"], 200)

    def test_404_thi_None_va_KHONG_phai_hong_mang(self):
        """404 = trang khong ton tai = HET TRANG that. Con tro duoc phep tien."""
        with mock.patch("requests.get", return_value=_R(404)):
            self.assertIsNone(SK._lay("http://x"))
        self.assertFalse(SK.lay_that_bai_vi_mang())
        self.assertEqual(SK.LAN_LAY_CUOI["ma"], 404)

    def test_ngoai_le_mang_thi_LA_hong_mang(self):
        for e in (ConnectionError("Remote end closed connection"),
                  TimeoutError("timed out"),
                  OSError("ERR_HTTP2_PROTOCOL_ERROR")):
            with mock.patch("requests.get", side_effect=e):
                self.assertIsNone(SK._lay("http://x"), e)
            self.assertTrue(SK.lay_that_bai_vi_mang(), e)
            self.assertIsNotNone(SK.LAN_LAY_CUOI["loi"], e)

    def test_loi_5xx_LA_hong_mang_chu_khong_phai_het_trang(self):
        """502/503 la may chu tam hong, khong phai trang khong ton tai."""
        for ma in (500, 502, 503):
            with mock.patch("requests.get", return_value=_R(ma)):
                SK._lay("http://x")
            self.assertTrue(SK.lay_that_bai_vi_mang(), ma)

    def test_403_429_KHONG_bi_cham_la_hong_mang(self):
        """Hieu chuan chieu nguoc: gac nay khong duoc bao "hong mang" voi moi
        ma khac 200, neu khong thi con tro khong bao gio tien duoc nua."""
        for ma in (403, 429, 401):
            with mock.patch("requests.get", return_value=_R(ma)):
                SK._lay("http://x")
            self.assertFalse(SK.lay_that_bai_vi_mang(), ma)

    def test_LAN_LAY_CUOI_duoc_xoa_moi_lan_goi(self):
        with mock.patch("requests.get", side_effect=ConnectionError("x")):
            SK._lay("http://a")
        self.assertIsNotNone(SK.LAN_LAY_CUOI.get("loi"))
        with mock.patch("requests.get", return_value=_R(200, "ok")):
            SK._lay("http://b")
        self.assertIsNone(SK.LAN_LAY_CUOI.get("loi"),
                          "ket qua lan truoc con sot lai")


class ConTroKhongBiCatKhiMangHONG(unittest.TestCase):
    def setUp(self):
        self.ct_cu = SK._con_tro("mql5_code")

    def tearDown(self):
        SK._ghi_con_tro("mql5_code", self.ct_cu)

    def test_mang_hong_thi_trang_cuoi_KHONG_bi_ghi(self):
        SK._ghi_con_tro("mql5_code", {"trang": {m: 5 for m in SK.MQL5_DANH_MUC},
                                      "trang_cuoi": {}})
        with mock.patch("requests.get", side_effect=ConnectionError("SNI")):
            SK.n_mql5_code(["strategy"])
        ct = SK._con_tro("mql5_code")
        self.assertEqual(ct.get("trang_cuoi") or {}, {},
                         "hong mang van ghi bien gioi - con tro bi cat vinh vien")
        self.assertGreater(int(ct.get("lan_hong_mang", 0)), 0,
                           "khong dem lan hong mang thi khong ai biet nguon dang chet")

    def test_404_that_thi_trang_cuoi_VAN_duoc_ghi(self):
        """Hieu chuan chieu nguoc: neu khong bao gio ghi thi phan trang vo han."""
        SK._ghi_con_tro("mql5_code", {"trang": {m: 5 for m in SK.MQL5_DANH_MUC},
                                      "trang_cuoi": {}})
        with mock.patch("requests.get", return_value=_R(404)):
            SK.n_mql5_code(["strategy"])
        self.assertTrue(SK._con_tro("mql5_code").get("trang_cuoi"),
                        "404 that ma khong ghi bien gioi")


if __name__ == "__main__":
    unittest.main()
