# -*- coding: utf-8 -*-
"""Kiem tang CHAM TIEN: `nhan/so_lenh.py` + `nhan/han_muc.py`.

Day la tang duy nhat cua du an cham toi tien that, nen cac bai kiem o day khoa
nhung tinh chat AN TOAN chu khong phai tinh nang. Mot bai kiem o day keu nghia la
mot duong tat vao tien that vua duoc mo.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import han_muc as HM  # noqa: E402
from nhan import so as SO  # noqa: E402
from nhan import so_lenh as SL  # noqa: E402

#: MOI ca kiem dung mot ten he RIENG.
#:
#: So lenh la CHI-THEM va co trigger CAM XOA - do la tinh chat dang gia nhat cua
#: no. Bai kiem khong duoc chong lai tinh chat do bang cach xoa sach giua cac
#: ca; lam vay la kiem mot phien ban khac voi ban se chay that. Nen: ten rieng.
#: Tien to phai duy nhat GIUA CAC LAN CHAY, khong chi trong mot lan. Lan dau
#: toi chi dem 1,2,3... - va lan chay thu hai lay lai dung nhung ten do, thua
#: ke luon lenh cua lan truoc (so cam xoa nen chung con nguyen): bai kiem doi 3
#: lenh nhung thay 6. Chinh tinh chi-them ma module nay bao ve lam bai kiem sai.
_DEM = {"n": 0}
_PHIEN = __import__("uuid").uuid4().hex[:8]


def _ten_he() -> str:
    _DEM["n"] += 1
    return f"THU_CHAM_TIEN_{_PHIEN}_{_DEM['n']}"


def _don(he: str):
    with SO.ket_noi() as cn:
        cn.execute("DELETE FROM he_chay WHERE ma = ?", (he,))
        cn.execute("DELETE FROM han_muc WHERE he = ?", (he,))


class MayTrangThaiKHONG_DUOC_NHAY_COC(unittest.TestCase):
    def setUp(self):
        SL._khoi_tao(); HM._khoi_tao()
        self.HE = _ten_he()
        SL.dang_ky_he(self.HE, "gt.thu", "US500CASH", "D1")

    def tearDown(self):
        _don(self.HE)

    def test_bat_dau_o_PAPER_CANDIDATE(self):
        self.assertEqual(SL.he(self.HE)["trang_thai"], "PAPER_CANDIDATE")

    def test_khong_duoc_nhay_thang_len_LIVE_CAP(self):
        kq = SL.doi_trang_thai(self.HE, "LIVE_CAP", nguoi_duyet="chu du an",
                               tran_von=100)
        self.assertFalse(kq["nhan"])
        self.assertIn("nhay coc", kq["ly_do"][0])

    def test_di_len_PHAI_co_nguoi_duyet(self):
        kq = SL.doi_trang_thai(self.HE, "PAPER")
        self.assertFalse(kq["nhan"], "da cho di len ma khong co nguoi duyet")
        self.assertIn("nguoi_duyet", kq["ly_do"][0])

    def test_di_len_tung_buoc_thi_duoc(self):
        self.assertTrue(SL.doi_trang_thai(self.HE, "PAPER", "chu du an")["nhan"])
        self.assertTrue(SL.doi_trang_thai(self.HE, "LIVE_SHADOW", "chu du an")["nhan"])
        kq = SL.doi_trang_thai(self.HE, "LIVE_CAP", "chu du an", tran_von=200)
        self.assertTrue(kq["nhan"], kq.get("ly_do"))

    def test_LIVE_CAP_phai_co_tran_von(self):
        SL.doi_trang_thai(self.HE, "PAPER", "chu du an")
        SL.doi_trang_thai(self.HE, "LIVE_SHADOW", "chu du an")
        kq = SL.doi_trang_thai(self.HE, "LIVE_CAP", "chu du an", tran_von=0)
        self.assertFalse(kq["nhan"])

    def test_DUNG_thi_luon_lam_duoc_va_khong_can_duyet(self):
        """Dung khan cap khong duoc phu thuoc vao viec tim duoc nguoi."""
        kq = SL.doi_trang_thai(self.HE, "DUNG")
        self.assertTrue(kq["nhan"], kq.get("ly_do"))


class SoLenhLaCHI_THEM(unittest.TestCase):
    def setUp(self):
        SL._khoi_tao(); HM._khoi_tao()
        self.HE = _ten_he()
        SL.dang_ky_he(self.HE, "gt.thu", "US500CASH", "D1")
        SL.doi_trang_thai(self.HE, "PAPER", "chu du an")

    def tearDown(self):
        _don(self.HE)

    def test_PAPER_CANDIDATE_chua_duoc_ghi_lenh(self):
        he2 = _ten_he()
        SL.dang_ky_he(he2, "gt.thu", "US500CASH", "D1")   # van o PAPER_CANDIDATE
        try:
            kq = SL.vao_lenh(he2, 1, "2026-09-11 10:00", 100.0, 1.0)
            self.assertFalse(kq["nhan"])
            self.assertIn("PAPER_CANDIDATE", kq["ly_do"][0])
        finally:
            _don(he2)

    def test_khong_sua_duoc_lenh_da_dong(self):
        vid = SL.vao_lenh(self.HE, 1, "2026-09-11 10:00", 100.0, 1.0)["id"]
        self.assertTrue(SL.ra_lenh(vid, "2026-09-11 12:00", 105.0, 0.5)["nhan"])
        lai = SL.ra_lenh(vid, "2026-09-11 13:00", 900.0)
        self.assertFalse(lai["nhan"], "sua duoc lenh da dong - phep doi chieu "
                                      "voi backtest mat y nghia")

    def test_tinh_lai_dung_ca_hai_chieu(self):
        a = SL.vao_lenh(self.HE, 1, "t1", 100.0, 2.0)["id"]
        self.assertAlmostEqual(SL.ra_lenh(a, "t2", 105.0, 1.0)["lai"], 9.0)
        b = SL.vao_lenh(self.HE, -1, "t3", 100.0, 2.0)["id"]
        self.assertAlmostEqual(SL.ra_lenh(b, "t4", 95.0, 1.0)["lai"], 9.0)

    def test_tong_ket_do_duoc_sut_giam(self):
        for gia_ra in (90.0, 95.0, 130.0):
            i = SL.vao_lenh(self.HE, 1, "t", 100.0, 1.0)["id"]
            SL.ra_lenh(i, "t2", gia_ra)
        tk = SL.tong_ket(self.HE)
        self.assertEqual(tk["so_lenh"], 3)
        self.assertLess(tk["sut_giam"], 0)


class PhanhMAC_DINH_LA_BAT(unittest.TestCase):
    def setUp(self):
        SL._khoi_tao(); HM._khoi_tao()
        self.HE = _ten_he()
        SL.dang_ky_he(self.HE, "gt.thu", "US500CASH", "D1")

    def tearDown(self):
        _don(self.HE)

    def test_chua_khai_han_muc_thi_KHONG_duoc_vao_lenh(self):
        duoc, ly = HM.duoc_vao_lenh(self.HE)
        self.assertFalse(duoc, "de quen khai han muc ma van chay duoc")
        self.assertIn("chua khai han muc", ly)

    def test_han_muc_phai_duong(self):
        kq = HM.dat(self.HE, tran_sut_giam=0, tran_lenh_ngay=5,
                    tran_phoi_nhiem=1.0, tran_von=100)
        self.assertFalse(kq["nhan"])

    def test_ngat_roi_thi_khong_vao_lenh_duoc(self):
        HM.dat(self.HE, 50.0, 5, 1.0, 100.0)
        self.assertTrue(HM.duoc_vao_lenh(self.HE)[0])
        HM.ngat(self.HE, "dien tap")
        duoc, ly = HM.duoc_vao_lenh(self.HE)
        self.assertFalse(duoc)
        self.assertIn("DA NGAT", ly)

    def test_mo_lai_PHAI_co_nguoi(self):
        HM.dat(self.HE, 50.0, 5, 1.0, 100.0)
        HM.ngat(self.HE, "dien tap")
        self.assertFalse(HM.mo_lai(self.HE, "")["nhan"])
        self.assertTrue(HM.mo_lai(self.HE, "chu du an")["nhan"])
        self.assertTrue(HM.duoc_vao_lenh(self.HE)[0])

    def test_tran_lenh_ngay_va_phoi_nhiem_chan_duoc(self):
        HM.dat(self.HE, 50.0, 3, 1.0, 100.0)
        self.assertFalse(HM.duoc_vao_lenh(self.HE, so_lenh_hom_nay=3)[0])
        self.assertFalse(HM.duoc_vao_lenh(self.HE, phoi_nhiem=1.5)[0])

    def test_quet_NGAT_khi_sut_giam_vuot_tran(self):
        """Dien tap kill-switch: khong can nguoi, va ghi su kien."""
        HM.dat(self.HE, tran_sut_giam=5.0, tran_lenh_ngay=99,
               tran_phoi_nhiem=99.0, tran_von=100.0)
        SL.doi_trang_thai(self.HE, "PAPER", "chu du an")
        i = SL.vao_lenh(self.HE, 1, "t", 100.0, 1.0)["id"]
        SL.ra_lenh(i, "t2", 80.0)                    # lo 20 > tran 5
        kq = HM.quet()
        self.assertTrue(any(x["he"] == self.HE for x in kq["da_ngat"]), kq)
        self.assertFalse(HM.duoc_vao_lenh(self.HE)[0])




class SuyGiamPHAI_PHAN_BIET_CHET_VOI_XUI(unittest.TestCase):
    """Bai hoc MDE cua du an, ap vao chieu nguoc: truoc khi tuyen bo mot he DA
    CHET phai co du luc de thay cai chet do. Mot bo giam sat khong biet noi
    'chua do duoc' se vut he tot vi mot chuoi binh thuong."""

    def setUp(self):
        from nhan import suy_giam as SG
        self.SG = SG
        SL._khoi_tao(); HM._khoi_tao()
        self.HE = _ten_he()
        SL.dang_ky_he(self.HE, "gt.thu", "US500CASH", "D1")
        SL.doi_trang_thai(self.HE, "PAPER", "chu du an")

    def tearDown(self):
        _don(self.HE)

    def _lenh(self, lai: float):
        i = SL.vao_lenh(self.HE, 1, "t", 100.0, 1.0)["id"]
        SL.ra_lenh(i, "t2", 100.0 + lai)

    def test_it_lenh_thi_CHUA_DO_DUOC_chu_khong_phai_SUY_GIAM(self):
        for _ in range(3):
            self._lenh(-5.0)           # lo dam, nhung moi 3 lenh
        kq = self.SG.do(self.HE, tb_bt=1.0, sd_bt=2.0)
        self.assertEqual(kq["trang_thai"], "CHUA_DO_DUOC", kq["mo_ta"])
        self.assertIsNotNone(kq["n_can"])
        self.assertGreater(kq["n_can"], 3)

    def test_du_lenh_va_lech_han_thi_SUY_GIAM(self):
        can = self.SG.n_can(1.0, 2.0)
        for _ in range(can + 5):
            self._lenh(-3.0)
        kq = self.SG.do(self.HE, tb_bt=1.0, sd_bt=2.0)
        self.assertEqual(kq["trang_thai"], "SUY_GIAM", kq["mo_ta"])
        self.assertLess(kq["t"], self.SG.NGUONG_T)

    def test_chay_dung_nhu_backtest_thi_BINH_THUONG(self):
        can = self.SG.n_can(1.0, 2.0)
        for k in range(can + 5):
            self._lenh(1.0 + (1.0 if k % 2 else -1.0))   # tb 1,0
        kq = self.SG.do(self.HE, tb_bt=1.0, sd_bt=2.0)
        self.assertEqual(kq["trang_thai"], "BINH_THUONG", kq["mo_ta"])

    def test_n_can_ti_le_nghich_voi_do_lon_cua_edge(self):
        """Edge cang nho cang can nhieu lenh - day la ly do mot he 'mong' khong
        bao gio bi tuyen bo chet som."""
        self.assertGreater(self.SG.n_can(0.1, 2.0), self.SG.n_can(1.0, 2.0))


if __name__ == "__main__":
    unittest.main()
