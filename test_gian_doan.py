# -*- coding: utf-8 -*-
"""MAY TAT hay HE CHET - hai trang thai khong duoc gop lam mot.

Truoc 01/09/2026 `dieu_phoi.ghi_gian_doan` gan cung `nguyen_nhan` =
"khong_xac_dinh", va `evolution.do_van_hanh` cong het so gio do vao mot con so
"he chet". Hau qua: gio chu du an tat may qua dem bi dem thanh gio he chet, nen
mot su co THAT se chim trong dong canh bao quen thuoc hang dem.
"""
from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta

import dieu_phoi as DP


class NguyenNhanGianDoan(unittest.TestCase):
    def test_may_khoi_dong_SAU_nhip_cuoi_la_MAY_TAT(self):
        """May ngu qua dem: nhip cuoi 23:14, may boot 07:04 -> khong phai su co."""
        import psutil
        boot = datetime.fromtimestamp(psutil.boot_time())
        truoc_boot = (boot - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(DP._nguyen_nhan_gian_doan(truoc_boot), "may_tat")

    def test_may_song_suot_ma_he_im_la_LOI_THAT(self):
        import psutil
        boot = datetime.fromtimestamp(psutil.boot_time())
        sau_boot = (boot + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(DP._nguyen_nhan_gian_doan(sau_boot), "he_chet_khi_may_chay")

    def test_khong_doc_duoc_thi_noi_la_khong_biet(self):
        """Doan bua con te hon nhan la khong biet."""
        self.assertEqual(DP._nguyen_nhan_gian_doan("khong phai ngay thang"),
                         "khong_xac_dinh")


class ThoiGianSongPhaiTHANH_THAT(unittest.TestCase):
    def setUp(self):
        from tru import evolution as EV
        self.d = EV.do_van_hanh()

    def test_gio_gian_doan_khong_vuot_qua_do_dai_cua_so(self):
        """Mot gian doan ghi TRONG cua so co the keo dai tu TRUOC do; cong nguyen
        thi ra 362,6 gio tren mot cua so 168 gio."""
        self.assertLessEqual(self.d["gian_doan_7ngay_gio"], 7 * 24 + 0.5)

    def test_ba_loai_gio_cong_lai_bang_tong(self):
        tong = (self.d["may_tat_7ngay_gio"] + self.d["he_chet_7ngay_gio"]
                + self.d["chua_ro_7ngay_gio"])
        self.assertAlmostEqual(tong, self.d["gian_doan_7ngay_gio"], places=0)

    def test_ty_le_song_luon_kem_MAU_SO(self):
        """Ty le khong kem do phu la mot cau noi thieu ve."""
        self.assertIn("gio_do_duoc_7ngay", self.d)
        if self.d["ty_le_song_7ngay"] is not None:
            self.assertGreater(self.d["gio_do_duoc_7ngay"], 0)

    def test_ty_le_song_nam_trong_0_1(self):
        t = self.d["ty_le_song_7ngay"]
        if t is not None:
            self.assertGreaterEqual(t, 0.0)
            self.assertLessEqual(t, 1.0)


if __name__ == "__main__":
    unittest.main()
