# -*- coding: utf-8 -*-
"""Khu trung co che theo DIEU KIEN, khong chi theo TEN.

Do that 01/09: mot lo tu dong dua thu vien tu 29 len 146 co che nhung chi co 81
dieu kien rieng biet - 65 cai trung y het, chi khac ten, vi cung mot script bi
xu ly hai lan. Moi ban trung se an MOT SUAT FDR rieng o tang kham pha.
"""
from __future__ import annotations

import unittest

from nhan import ngu_phap as NP

SPEC = {
    "ten": "thu_khu_trung_a",
    "co_che": "Mot cau du dai de qua duoc bai kiem do dai cua kiem_khai_bao.",
    "ho": "xu_huong", "chieu": 1, "giu": 1,
    "vao": [{"trai": {"chi_bao": "ema", "n": 14, "cot": "close"},
             "phep": ">", "phai": {"chi_bao": "ema", "n": 28, "cot": "close"}}],
}


class VanTayDieuKien(unittest.TestCase):
    def test_doi_TEN_khong_doi_van_tay(self):
        a = NP.van_tay_dieu_kien(SPEC)
        b = NP.van_tay_dieu_kien(dict(SPEC, ten="ten_hoan_toan_khac"))
        self.assertEqual(a, b)

    def test_doi_cau_giai_thich_khong_doi_van_tay(self):
        a = NP.van_tay_dieu_kien(SPEC)
        b = NP.van_tay_dieu_kien(dict(SPEC, co_che="Mot cau giai thich khac han."))
        self.assertEqual(a, b)

    def test_doi_CHU_KY_thi_van_tay_PHAI_doi(self):
        khac = dict(SPEC)
        khac["vao"] = [{"trai": {"chi_bao": "ema", "n": 20, "cot": "close"},
                        "phep": ">", "phai": {"chi_bao": "ema", "n": 28,
                                              "cot": "close"}}]
        self.assertNotEqual(NP.van_tay_dieu_kien(SPEC),
                            NP.van_tay_dieu_kien(khac))

    def test_doi_CHIEU_thi_van_tay_PHAI_doi(self):
        self.assertNotEqual(NP.van_tay_dieu_kien(SPEC),
                            NP.van_tay_dieu_kien(dict(SPEC, chieu=-1)))

    def test_doi_GIU_thi_van_tay_PHAI_doi(self):
        self.assertNotEqual(NP.van_tay_dieu_kien(SPEC),
                            NP.van_tay_dieu_kien(dict(SPEC, giu=5)))


class ChanTrungTrongKho(unittest.TestCase):
    def test_kho_hien_tai_khong_con_ban_trung(self):
        kho = NP.doc_kho()
        vt = [NP.van_tay_dieu_kien(c) for c in kho]
        self.assertEqual(len(vt), len(set(vt)),
                         "thu vien dang chua co che trung dieu kien")


if __name__ == "__main__":
    unittest.main()
