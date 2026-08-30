# -*- coding: utf-8 -*-
"""Do LUC: edge nho nhat ma cong con nhin thay duoc.

Y nghia cua module duoc do: mot ket luan am tinh khong kem con so nay thi khong
phan biet duoc "thi truong rong" voi "thuoc do qua tho". Bo test khoa ba thu:
so hoc gop tai san phai tinh theo k HIEU DUNG, quy luat 1/sqrt(T) phai dung
chieu, va duong cong luc phai don dieu.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import do_luc as L


class KHieuDung(unittest.TestCase):

    def test_doc_lap_hoan_toan_thi_k_hieu_dung_bang_k(self):
        for k in (2, 5, 20):
            self.assertAlmostEqual(L.k_hieu_dung(0.0, k), float(k), places=9)

    def test_trung_khop_hoan_toan_thi_chi_bang_mot(self):
        self.assertAlmostEqual(L.k_hieu_dung(0.999, 20), 20 / (1 + 19 * 0.999), places=6)
        self.assertLess(L.k_hieu_dung(0.999, 20), 1.05)

    def test_vang_gop_nam_cap_gan_nhu_khong_duoc_gi(self):
        """rho da do cua 5 cap vang la 0,859."""
        self.assertLess(L.k_hieu_dung(0.859, 5), 1.2)

    def test_cang_tuong_quan_cang_it_loi(self):
        moc = [L.k_hieu_dung(r, 10) for r in (0.0, 0.2, 0.5, 0.9)]
        self.assertEqual(moc, sorted(moc, reverse=True))

    def test_k_am_hoac_khong_khong_lam_vo(self):
        self.assertGreaterEqual(L.k_hieu_dung(0.3, 0), 1.0)
        self.assertGreaterEqual(L.k_hieu_dung(-5.0, 3), 1.0)


class LoiTheKhiGop(unittest.TestCase):

    def test_bo_qua_rho_thi_noi_qua_loi_the(self):
        """Day la loi da mac: 'gop 9 -> 0,46' trong khi so that la 0,75."""
        bo_qua = L.loi_the_khi_gop(9, rho_trung_binh=0.0)
        that = L.loi_the_khi_gop(9, rho_trung_binh=0.203)
        self.assertLess(bo_qua, that, "bo qua rho phai cho nguong THAP hon (lac quan hon)")
        self.assertAlmostEqual(bo_qua, 1.39 / 3.0, places=3)
        self.assertGreater(that, 0.70)

    def test_gop_mot_tai_san_thi_khong_ha_nguong(self):
        self.assertAlmostEqual(L.loi_the_khi_gop(1, 1.39, 0.3), 1.39, places=6)

    def test_gop_cang_nhieu_nguong_cang_thap(self):
        moc = [L.loi_the_khi_gop(k, 1.39, 0.2) for k in (1, 4, 11, 20)]
        self.assertEqual(moc, sorted(moc, reverse=True))


class NamCanDeThay(unittest.TestCase):

    def test_quy_luat_nghich_binh_phuong(self):
        """Muon thay edge nho di mot nua thi can gap 4 lan du lieu."""
        self.assertAlmostEqual(L.nam_can_de_thay(0.5) / L.nam_can_de_thay(1.0),
                               4.0, places=6)

    def test_edge_bang_moc_thi_can_dung_so_nam_cua_moc(self):
        self.assertAlmostEqual(L.nam_can_de_thay(1.39), 5.5, places=6)

    def test_edge_that_cua_thi_truong_can_rat_nhieu_nam(self):
        """Sharpe 0,5 la muc THAT cua FX/chi so sau phi."""
        self.assertGreater(L.nam_can_de_thay(0.5), 35)

    def test_edge_khong_duong_thi_khong_tra_so(self):
        self.assertIsNone(L.nam_can_de_thay(0.0))
        self.assertIsNone(L.nam_can_de_thay(-1.0))


class DuongCongLuc(unittest.TestCase):
    """Chay THAT tren du lieu that - cham hon nhung day la cai dang do."""

    @classmethod
    def setUpClass(cls):
        # PHAI doi sang so cai TAM. `duong_cong_luc` goi `cong.xet(
        # tren_holdout=True)` cho moi muc p, va moi lan goi la mot dong FDR.
        # Chay bo test tren so cai that lam ho `do_luc` phinh len hang tram
        # dong - do that 22/08: 588 dong trong mot buoi. Ho `do_luc` khong anh
        # huong quyet dinh (MDE da loai dieu kien 10) nhung so cai la ban ghi
        # cua he, khong phai bai nhap cua bo test.
        from nhan import so as SO
        cls._db_cu = SO.DB
        cls._tmp = tempfile.TemporaryDirectory()
        SO.DB = Path(cls._tmp.name) / "nao_test.db"
        SO.khoi_tao()
        cls.r = L.duong_cong_luc("EURCAD", "H4",
                                 thang_p=(0.50, 0.55, 0.60, 0.70))

    @classmethod
    def tearDownClass(cls):
        from nhan import so as SO
        SO.DB = cls._db_cu
        cls._tmp.cleanup()

    def test_do_duoc(self):
        self.assertNotIn("loi", self.r, self.r.get("loi"))
        self.assertGreater(self.r["so_bar"], 1000)

    def test_khong_co_edge_thi_bi_tu_choi(self):
        """p=0,50 la khong co edge -> cong PHAI tu choi."""
        d = next(x for x in self.r["diem"] if x["p"] == 0.50)
        self.assertFalse(d["qua"], f"p=0,50 ma qua duoc cong: {d}")

    def test_edge_lon_thi_di_qua(self):
        """BAI KIEM LUC: cong tu choi tat ca thi con so MDE vo nghia."""
        d = next(x for x in self.r["diem"] if x["p"] == 0.70)
        self.assertTrue(d["qua"], f"edge cuc lon ma van bi chan: {d}")

    def test_duong_cong_don_dieu(self):
        """p cao hon phai cho Sharpe cao hon - neu khong thi phep cay tin hieu sai."""
        sharpe = [x["sharpe"] for x in self.r["diem"]]
        self.assertEqual(sharpe, sorted(sharpe), sharpe)

    def test_co_nguong_va_no_duong(self):
        self.assertIsNotNone(self.r["sharpe_nho_nhat_thay_duoc"])
        self.assertGreater(self.r["sharpe_nho_nhat_thay_duoc"], 0)

    def test_nguong_cao_hon_edge_that_cua_thi_truong(self):
        """Ghi nhan su that kho chiu: nguong hien tai cao hon Sharpe 0,8.

        Neu mot ngay nao do bai nay do, nghia la luc da tang that - luc do sua
        lai con so va an mung.
        """
        self.assertGreater(self.r["sharpe_nho_nhat_thay_duoc"], 0.8,
                           "nguong da xuong duoi 0,8 - cap nhat lai tai lieu do_luc")


if __name__ == "__main__":
    unittest.main(verbosity=2)
