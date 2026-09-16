# -*- coding: utf-8 -*-
"""Test tru BANKER ban 2."""

import unittest
from datetime import date, timedelta
from unittest.mock import patch

from tru import banker


class TestBankerAsOf(unittest.TestCase):
    def test_tuoi_ngay(self):
        hom_nay = date(2026, 8, 16)
        self.assertEqual(banker._tuoi_ngay("2026-08-14", hom_nay), 2)
        self.assertIsNone(banker._tuoi_ngay("khong-phai-ngay", hom_nay))

    def test_cap_vix_stale_khong_duoc_gan_nhan(self):
        hom_nay = date.today()
        moi = (hom_nay - timedelta(days=2)).isoformat()
        cu = (hom_nay - timedelta(days=30)).isoformat()
        gia = {
            "LS10Y": 4.2, "LS3M": 3.5, "VIX": 14.0, "VIX3M": 20.0,
            "USD": 100.0, "HYG": 75.0, "LQD": 100.0,
            "VN_CPI": 3.0, "VN_GDP": 6.0, "VN_TYGIA": 25000.0,
        }

        def gan_nhat(ma, n=1):
            # Seri khong co trong bang gia gia lap -> tra RONG, dung nem KeyError.
            # Rong la trang thai THAT (seri chua nap); nem loi se lam moi seri
            # them vao sau nay pha vo bai test nay ma khong lien quan gi den no.
            if ma not in gia:
                return []
            ngay = cu if ma == "VIX3M" else moi
            if ma.startswith("VN_"):
                ngay = (hom_nay - timedelta(days=200)).isoformat()
            return [{"ngay": ngay, "gia_tri": gia[ma]}]

        def cap(a, b, ngay_toi_da=None):
            if (a, b) == ("VIX3M", "VIX"):
                return {"ngay": cu, "gia_a": 20.0, "gia_b": 14.0}
            if (a, b) == ("LS10Y", "LS3M"):
                return {"ngay": moi, "gia_a": 4.2, "gia_b": 3.5}
            if (a, b) == ("HYG", "LQD"):
                return {"ngay": moi, "gia_a": 75.0, "gia_b": 100.0}
            return None

        with patch.object(banker, "gan_nhat", side_effect=gan_nhat), \
             patch.object(banker, "_cap_cung_ngay", side_effect=cap), \
             patch.object(banker, "_doi", return_value=0.0):
            r = banker.phan_loai_che_do()

        self.assertNotIn("cau_truc_ky_han_vix", r["che_do"])
        self.assertIn("VIX3M/VIX", r["stale"])
        self.assertEqual(r["che_do"]["duong_cong"]["ngay"], moi)


if __name__ == "__main__":
    unittest.main()
