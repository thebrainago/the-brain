# -*- coding: utf-8 -*-
"""Kiem `nhan/bai_hoc.py` - so bai hoc cua khoi 2.

Cai so nay phai giu duoc MOT tinh chat tren tat ca: no la TRI NHO, khong phai
QUYEN PHU QUYET. No tra ve the lien quan; no khong noi cai gi se that bai.
Nham lan hai thu do la cach nhanh nhat de mot he ngung hoc cai moi.
"""
from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

import sys

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import bai_hoc as BH  # noqa: E402


class CongCuaSoBaiHoc(unittest.TestCase):
    """Hai chot, ca hai deu tu bai hoc cu cua chinh du an."""

    def test_huong_nen_tranh_PHAI_co_bang_chung(self):
        """Mot the 'huong X khong an' khong kem so do se thanh mot dieu cam
        khong ai kiem lai duoc - va he ngung thu X mai mai vi mot cau noi."""
        kq = BH.them(ma="thu::khong_bang_chung", loai="huong_nen_tranh",
                     tieu_de="Huong X khong an",
                     noi_dung="Toi thay huong nay khong on lam, nen bo di.")
        self.assertFalse(kq["nhan"])
        self.assertIn("bang_chung", kq["ly_do"][0])

    def test_bay_do_luong_cung_PHAI_co_bang_chung(self):
        kq = BH.them(ma="thu::bay_khong_so", loai="bay_do_luong",
                     tieu_de="Phep do nay hay noi doi",
                     noi_dung="Hinh nhu con so do khong dang tin, can xem lai.")
        self.assertFalse(kq["nhan"])

    def test_loai_khong_biet_bi_tu_choi(self):
        kq = BH.them(ma="thu::loai_la", loai="linh_tinh", tieu_de="x",
                     noi_dung="mot noi dung du dai de qua duoc chot do dai")
        self.assertFalse(kq["nhan"])
        self.assertIn("loai khong biet", kq["ly_do"][0])

    def test_huong_dang_mo_KHONG_bi_doi_bang_chung(self):
        """Mot huong chua ket luan thi chua co so - doi so o day se lam he
        khong ghi lai duoc dung cai dang can theo doi."""
        kq = BH.them(ma="thu::dang_mo", loai="huong_dang_mo",
                     tieu_de="Huong Y co dau hieu",
                     noi_dung="Moi thay dau hieu, chua do duoc, can theo doi them.")
        self.assertTrue(kq["nhan"], kq["ly_do"])


class TraCuuPhaiTimDuocCaiDaGhi(unittest.TestCase):
    MA = "thu::tra_cuu_phi_qua_dem"

    @classmethod
    def setUpClass(cls):
        BH.them(ma=cls.MA, loai="huong_nen_tranh",
                tieu_de="Khong duoc mo hinh phi qua dem bang swap tuyet doi nhan 365",
                noi_dung=("Mo hinh nhan 365 chia gia tung ngay cho ra 38,8%/nam cho "
                          "nam 2011, sai han. Phai mo hinh theo lai suat thuc te "
                          "tung ngay cong markup hieu chinh tu quan sat hom nay."),
                bang_chung="38,8%/nam nam 2011 so voi 6,0-14,7%/nam do that")

    def test_tim_duoc_bang_tu_khoa_khac_cach_viet(self):
        the = BH.tra("phi qua dem tinh the nao cho dung")
        self.assertTrue(any(t["ma"] == self.MA for t in the),
                        [t["tieu_de"] for t in the])

    def test_cau_hoi_khong_lien_quan_thi_khong_tra_bua(self):
        the = BH.tra("mau sac giao dien nut bam")
        self.assertFalse(any(t["ma"] == self.MA for t in the))

    def test_lien_quan_nhan_mot_gia_thuyet(self):
        """Khang dinh dung phai la LIEN QUAN, khong phai "the cua toi len dau".

        Ban dau toi doi dung the vua them phai nam trong top 3. No khong - va
        do la DUNG: hai the that trong CLAUDE.md ve phi qua dem xep tren no.
        Mot bai kiem doi mot ban ghi cu the phai thang se khoa cung cach xep
        hang, va se keu moi lan so day them the tot hon.
        """
        the = BH.lien_quan({"ho": "vi_mo", "co_che": "phi qua dem swap",
                            "ten": "thu", "tai_san": "US500CASH", "khung": "D1"})
        self.assertTrue(the, "mot gia thuyet ve phi qua dem ma khong ra the nao")
        vb = " ".join((t["tieu_de"] + " " + t["noi_dung"]).lower() for t in the)
        self.assertTrue(
            any(k in vb for k in ("phi qua dem", "swap", "chi phi", "lai suat")),
            f"the tra ve khong lien quan: {[t['tieu_de'][:40] for t in the]}")

    def test_tra_KHONG_phan_xet(self):
        """Hop dong cua ham: chi tra ve the. Khong co truong nao noi dat/truot."""
        for t in BH.tra("phi qua dem"):
            self.assertNotIn("verdict", t)
            self.assertNotIn("nen_bo", t)
            self.assertNotIn("dat", t)


class SoPhaiCoTHAT(unittest.TestCase):
    def test_bang_ton_tai_va_da_co_the_that(self):
        """Chan tho: neu bo nhap chua chay thi so rong, va ca khoi 2 la vo nghia."""
        d = BH.dem()
        self.assertGreaterEqual(
            d["tong"], 100,
            "so bai hoc gan nhu rong - chay `python _nhap_bai_hoc.py --that`")

    def test_ma_la_khoa_DUY_NHAT(self):
        """Chay lai bo nhap khong duoc sinh ban thu hai cua cung mot the."""
        truoc = BH.dem()["tong"]
        for _ in range(2):
            BH.them(ma="thu::trung_ma", loai="huong_dang_mo", tieu_de="x",
                    noi_dung="mot noi dung du dai de qua duoc chot do dai toi thieu")
        sau = BH.dem()["tong"]
        self.assertLessEqual(sau - truoc, 1)




class QuantlabPhaiHOI_SO_TRUOC_KHI_DANG_KY(unittest.TestCase):
    """Vong phan hoi chi khep khi ben SINH gia thuyet co doc so bai hoc.

    Bai kiem nay khoa MOT dieu: quantlab phai GHI RA canh bao, va phai KHONG
    chan. Neu mot ngay nao do ai do doi no thanh cai chan, bai kiem duoi day keu.
    """

    def test_dang_ky_sau_quet_co_goi_bai_hoc(self):
        import inspect
        from tru import quantlab as QL
        ma = inspect.getsource(QL.dang_ky_sau_quet)
        self.assertIn("bai_hoc", ma,
                      "dang_ky_sau_quet khong hoi so bai hoc - vong phan hoi dut")
        self.assertIn("bai_hoc_canh_bao", ma)

    def test_KHONG_duoc_chan_bang_bai_hoc(self):
        """`continue` / `return` ngay sau canh bao = da thanh cai chan."""
        import inspect, re
        from tru import quantlab as QL
        ma = inspect.getsource(QL.dang_ky_sau_quet)
        i = ma.find("bai_hoc_canh_bao")
        self.assertGreater(i, 0)
        sau = ma[i:i + 400]
        self.assertNotRegex(
            sau, r"\n\s+(?:continue|return|raise)\b",
            "so bai hoc dang CHAN quantlab - no la tri nho, khong phai quyen phu quyet")

    def test_so_hong_khong_duoc_chan_quantlab(self):
        import inspect
        from tru import quantlab as QL
        ma = inspect.getsource(QL.dang_ky_sau_quet)
        i = ma.find("from nhan import bai_hoc")
        self.assertGreater(i, 0)
        self.assertIn("except Exception", ma[i:i + 1200],
                      "goi so bai hoc ma khong bat loi - so hong se lam sap quantlab")


if __name__ == "__main__":
    unittest.main()
