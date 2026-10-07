# -*- coding: utf-8 -*-
"""TANG 2 KINH TE cua `nhan/cong.py` — chan martingale tra hinh.

Chu du an dua tong ket SP500 vao he ngay 18/09/2026. Trong do, tang 2 sinh ra
vi mot ly do cu the: tren SP500 no da loc ra **2.081 martingale tra hinh** ma
Bonferroni khong bat duoc — tp=0,1xATR / sl=4,0xATR cho rr=0,025, winrate 100%
tren 15-20 lenh. Breakeven winrate cua rr=0,025 la 97,6%, nen 100% vuot qua
moi phep thu thong ke mot cach hop le. Dung toan hoc, vo gia tri kinh te.

Test nay dung lai dung hinh dang do va bat cong phai NHAN RA no. Tu 25/09/2026
(the he cong 6) tang 2 la NHAN, khong chan - chu du an: *"toi khong quan tam
martingale hay dca hay la phuong phap gi ... chi can co lai va maxdd duoi 80%"*.
Phep do van phai dung, vi nhan sai thi chu du an doc sai.
"""
import unittest

import numpy as np

from nhan import cong as C


def _chuoi_lenh(lai_moi_lenh):
    """Dung (vi_the, loi) theo bar tu danh sach lai TUNG LENH.

    Moi lenh = 3 bar giu vi the 1.0, xen mot bar phang de tach lenh.
    """
    v, l = [], []
    for x in lai_moi_lenh:
        v += [1.0, 1.0, 1.0, 0.0]
        l += [x / 3.0, x / 3.0, x / 3.0, 0.0]
    return np.array(v), np.array(l)


class GopBarThanhLenh(unittest.TestCase):

    def test_gop_dung_so_lenh(self):
        v, l = _chuoi_lenh([1.0, -2.0, 3.0])
        x = C.lai_theo_lenh(v, l)
        self.assertEqual(len(x), 3)

    def test_gop_dung_gia_tri(self):
        v, l = _chuoi_lenh([1.0, -2.0, 3.0])
        x = C.lai_theo_lenh(v, l)
        np.testing.assert_allclose(x, [1.0, -2.0, 3.0], atol=1e-9)

    def test_chuoi_rong_khong_no(self):
        self.assertEqual(len(C.lai_theo_lenh([], [])), 0)
        self.assertEqual(C.rr_thuc_te([], []), 0.0)


class ChanMartingaleTraHinh(unittest.TestCase):

    def test_martingale_tra_hinh_bi_bat(self):
        """60 lenh thang nho + 1 lenh thua lon = dung hinh dang rr 0,025.

        Winrate 98,4%, va TONG VAN DUONG (+2,0). Do la cai lam no lot moi phep
        thu: breakeven winrate cua rr=0,025 la 97,6%, nen 98,4% qua hop le.
        """
        lai = [0.1] * 60 + [-4.0]
        v, l = _chuoi_lenh(lai)
        rr = C.rr_thuc_te(v, l)
        self.assertLess(rr, 0.2, "rr=%.4f dang le phai duoi nguong 0,2" % rr)
        self.assertGreater(sum(lai), 0, "tong van duong - do la cai lam no lot luoi")

    def test_he_lanh_manh_khong_bi_chan_oan(self):
        """WR 55%, lai TB thang ~ lo TB thua -> rr ~ 1,0, phai qua."""
        lai = [1.0] * 11 + [-1.0] * 9
        v, l = _chuoi_lenh(lai)
        self.assertGreaterEqual(C.rr_thuc_te(v, l), 0.2)

    def test_winrate_thap_nhung_payoff_lon_van_qua(self):
        """WR 30% ma thang gap 4 lan thua — kieu trend-following that."""
        lai = [4.0] * 6 + [-1.0] * 14
        v, l = _chuoi_lenh(lai)
        self.assertGreaterEqual(C.rr_thuc_te(v, l), 0.2)

    def test_chua_tung_thua_khong_bi_chia_cho_khong(self):
        v, l = _chuoi_lenh([1.0, 2.0, 3.0])
        self.assertEqual(C.rr_thuc_te(v, l), float("inf"))


class NguongCoTrongCauHinh(unittest.TestCase):

    def test_hai_nguong_da_khai_bao(self):
        n = C.nguong()
        self.assertIn("rr_thuc_te_toi_thieu", n)
        self.assertIn("edge_tren_spread_toi_thieu", n)

    def test_nguong_dung_con_so_cua_tong_ket_sp500(self):
        n = C.nguong()
        self.assertAlmostEqual(n["rr_thuc_te_toi_thieu"], 0.2, places=6)
        self.assertAlmostEqual(n["edge_tren_spread_toi_thieu"], 3.0, places=6)


if __name__ == "__main__":
    unittest.main()
