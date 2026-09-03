# -*- coding: utf-8 -*-
"""DAY CHUYEN TAI LIEU -> CO CHE: bo doc song song + bo boc LLM.

Do 03/09/2026 truoc khi sua:
  3.489 tai lieu -> 2.543 ban doc -> **4 ban tung duoc boc** -> 152 co che.
  `seeker.boc_co_che` chay 10 bai het 202 giay va ra **0 co che**, vi chinh
  loi nhac cua no kem danh sach 170 co che da co + menh lenh "KHONG de xuat
  lai, ke ca doi ten hay doi tham so".
  `seeker.doc_toan_van` tai TUAN TU: 8,75 s/ban, va di theo thu tu BANG nen
  roi vao me crossref/openalex -> vong 3 chi doc duoc 1/27.

Bo test nay KHONG goi mang va KHONG goi LLM. No kiem phan THUAN LOGIC:
loc ung vien, chuan hoa dau ra, uu tien nguon, phan loai ban doc.
"""
from __future__ import annotations

import unittest

from nhan import boc_llm as BL
from nhan import doc_song_song as DS
from nhan import ngu_phap as NP


class LocUngVien(unittest.TestCase):
    """Chi dua tai lieu CO KHA NANG chua luat - bai hoc thuat ta PHUONG PHAP
    chu khong ta LUAT (suat do duoc: arxiv 0,8%, openalex 6%)."""

    def test_van_ban_co_luat_thi_diem_cao(self):
        vb = ("Buy when RSI crosses above 30 and close is above the 200 EMA. "
              "Stop loss at 1% below entry. Take profit at 3%.")
        self.assertGreaterEqual(BL._diem_luat(vb), 2)

    def test_van_xuoi_hoc_thuat_thi_diem_thap(self):
        vb = ("We propose a novel framework for asset pricing under stochastic "
              "volatility, and derive the asymptotic distribution of the "
              "estimator. Our contribution extends the literature on ...")
        self.assertLess(BL._diem_luat(vb), 2)

    def test_bat_duoc_ca_luat_viet_bang_tieng_viet(self):
        vb = "Vao lenh khi gia cat len EMA34. Thoat lenh khi RSI > 70. Stop loss 1%."
        self.assertGreaterEqual(BL._diem_luat(vb), 2)

    def test_van_ban_rong_khong_no(self):
        self.assertEqual(BL._diem_luat(""), 0)
        self.assertEqual(BL._diem_luat(None), 0)


class ChuanHoaDauRaLLM(unittest.TestCase):
    """Lo thu dau tien mat 2/4 khai bao chi vi `giu` sai KIEU. Do la loi dinh
    dang, khong phai loi noi dung."""

    def _spec(self, **doi):
        d = {"ten": "Thu Nghiem", "co_che": "x" * 40, "ho": "xu_huong",
             "chieu": 1, "giu": 1,
             "vao": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<",
                      "phai": {"hang": 30}}], "ra": []}
        d.update(doi)
        return d

    def test_giu_so_thuc_thanh_so_nguyen(self):
        self.assertEqual(BL.chuan_hoa_spec(self._spec(giu=3.0))["giu"], 3)

    def test_giu_chuoi_thanh_so_nguyen(self):
        self.assertEqual(BL.chuan_hoa_spec(self._spec(giu="5"))["giu"], 5)

    def test_giu_None_hoac_rac_thanh_1(self):
        for x in (None, "khong biet", [], {}):
            self.assertEqual(BL.chuan_hoa_spec(self._spec(giu=x))["giu"], 1, x)

    def test_giu_ngoai_mien_bi_keo_ve_mien(self):
        self.assertEqual(BL.chuan_hoa_spec(self._spec(giu=0))["giu"], 1)
        self.assertEqual(BL.chuan_hoa_spec(self._spec(giu=9999))["giu"], 500)

    def test_chieu_chuoi_va_ngoai_mien(self):
        self.assertEqual(BL.chuan_hoa_spec(self._spec(chieu="-1"))["chieu"], -1)
        self.assertEqual(BL.chuan_hoa_spec(self._spec(chieu=7))["chieu"], 1)

    def test_ten_co_dau_va_khoang_trang_duoc_chuan_hoa(self):
        t = BL.chuan_hoa_spec(self._spec(ten="Mua Khi RSI Thap"))["ten"]
        self.assertEqual(t, NP.chuan_hoa_ten("Mua Khi RSI Thap"))

    def test_ten_rong_van_ra_mot_ten(self):
        self.assertTrue(BL.chuan_hoa_spec(self._spec(ten=""))["ten"])

    def test_vao_la_dict_don_thanh_list(self):
        d = self._spec()
        d["vao"] = d["vao"][0]
        self.assertIsInstance(BL.chuan_hoa_spec(d)["vao"], list)

    def test_ra_None_thanh_list_rong(self):
        self.assertEqual(BL.chuan_hoa_spec(self._spec(ra=None))["ra"], [])

    def test_hang_dang_CHUOI_thanh_so(self):
        d = self._spec()
        d["vao"][0]["phai"]["hang"] = "30"
        self.assertEqual(BL.chuan_hoa_spec(d)["vao"][0]["phai"]["hang"], 30.0)

    def test_KHONG_sua_spec_goc_tai_cho(self):
        d = self._spec(giu=3.0)
        BL.chuan_hoa_spec(d)
        self.assertEqual(d["giu"], 3.0, "spec goc bi sua tai cho")

    def test_spec_hop_le_qua_duoc_cong_sau_khi_chuan_hoa(self):
        self.assertEqual(NP.kiem_khai_bao(BL.chuan_hoa_spec(self._spec(giu=2.0))), [])

    def test_chuan_hoa_KHONG_cuu_spec_thieu_dieu_kien(self):
        """Hieu chuan chieu nguoc: chi sua DINH DANG, khong bia noi dung."""
        d = BL.chuan_hoa_spec(self._spec(vao=[]))
        self.assertNotEqual(NP.kiem_khai_bao(d), [])


class UuTienNguonKhiDoc(unittest.TestCase):
    """`doc_toan_van` cu lay theo thu tu BANG nen roi vao me DOI -> vong 3 chi
    doc duoc 1/27. Ban moi xep theo suat DO DUOC."""

    def test_nguon_ma_di_truoc_nguon_hoc_thuat(self):
        self.assertLess(DS._thu_tu("tradingview_pine"), DS._thu_tu("crossref"))
        self.assertLess(DS._thu_tu("mql5_code"), DS._thu_tu("openalex"))
        self.assertLess(DS._thu_tu("github"), DS._thu_tu("arxiv"))

    def test_nguon_la_nam_giua_chu_khong_bi_vut(self):
        t = DS._thu_tu("mot_nguon_chua_biet")
        self.assertGreater(t, DS._thu_tu("tradingview_pine"))
        self.assertLess(t, DS._thu_tu("crossref"))

    def test_thu_tu_on_dinh_qua_hai_lan_goi(self):
        self.assertEqual(DS._thu_tu("github"), DS._thu_tu("github"))


class PhanLoaiBanDoc(unittest.TestCase):
    def test_ma_pine_duoc_nhan_la_ma_nguon(self):
        self.assertEqual(DS._loai("//@version=5\nstrategy('x')"), "ma_nguon")

    def test_ma_mql_duoc_nhan(self):
        self.assertEqual(DS._loai("#property copyright\nvoid OnTick() {}"),
                         "ma_nguon")

    def test_van_xuoi_khong_bi_nhan_nham_la_ma(self):
        self.assertEqual(
            DS._loai("The strategy performed well over the sample period."),
            "bai_bao")

    def test_rong_khong_no(self):
        self.assertEqual(DS._loai(""), "bai_bao")
        self.assertEqual(DS._loai(None), "bai_bao")


if __name__ == "__main__":
    unittest.main()
