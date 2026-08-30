# -*- coding: utf-8 -*-
import unittest

import numpy as np
import pandas as pd

from nhan import chi_phi as CP


class TestHinhHocChiPhi(unittest.TestCase):
    def setUp(self):
        CP._BO_NHO_HINH_HOC.clear()

    def test_interval_duoc_gan_vao_bar_bat_dau(self):
        idx = pd.DatetimeIndex([
            "2026-08-14 20:00:00",  # Friday
            "2026-08-17 20:00:00",  # Monday
            "2026-08-18 20:00:00",
        ])
        ngay, _ = CP.hinh_hoc(idx)
        np.testing.assert_allclose(ngay, [3.0, 1.0, 0.0])

    def test_phi_cuoi_tuan_khong_roi_sang_bar_da_dong(self):
        idx = pd.DatetimeIndex(["2026-08-14 20:00:00", "2026-08-17 20:00:00"])
        cp = CP.MoHinhChiPhi(ma="TEST", phi_nam_mua=0.365, do_tin="DO")
        phi = cp.phi_giu_mang(idx, np.array([1.0, 0.0]))
        np.testing.assert_allclose(phi, [0.003, 0.0])


if __name__ == "__main__":
    unittest.main()
