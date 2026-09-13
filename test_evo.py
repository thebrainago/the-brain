# -*- coding: utf-8 -*-
"""Kiem `nhan/evo.py` - bo giam sat.

## Mot bo giam sat SAI con te hon khong co bo giam sat nao

Trong DUNG mot phien (12/09/2026) bo do cua chinh du an bao sai ba lan:

    "9 nguon SEEKER la ma chet"   -> chung duoc goi GIAN TIEP qua bang `NGUON`
    "567 ung vien bi ket"         -> bang do la NHAT KY chi-ghi-them, dung thiet ke
    "43 co che nem loi khung"     -> toi chay chung tren D1 trong khi he da chot H1

Ca ba deu la doan kien truc thay vi doc quy uoc. Nen bai kiem quan trong nhat o
day khong phai "bao cao co chay khong" ma la **bo giam sat co TU BIA RA van de
khong**: thieu du lieu phai ra `CHUA_DO`, khong duoc ra `XAU`.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import evo as EVO  # noqa: E402


class ThieuDuLieuPhaiLaCHUA_DO_KhongPhaiXAU(unittest.TestCase):
    def test_ba_trang_thai_tach_biet(self):
        self.assertNotEqual(EVO.CHUA_DO, EVO.XAU)
        self.assertNotEqual(EVO.CHUA_DO, EVO.TOT)

    def test_khong_doc_duoc_so_thi_ra_CHUA_DO(self):
        that = EVO._mot
        EVO._mot = lambda cau, mac_dinh=None: None
        try:
            cs = EVO.suc_khoe_evo() + EVO.suc_khoe_quantlab()
        finally:
            EVO._mot = that
        tu_so = [c for c in cs if c["ten"] in ("evo.van_de_mo", "evo.bai_hoc",
                                               "quantlab.ket_qua")]
        self.assertTrue(tu_so, "khong lay duoc chi so nao de kiem")
        for c in tu_so:
            self.assertEqual(c["trang_thai"], EVO.CHUA_DO,
                             "%s: khong doc duoc so ma bao XAU" % c["ten"])

    def test_tep_chua_ton_tai_thi_ra_CHUA_DO(self):
        that = EVO._tuoi_tep
        EVO._tuoi_tep = lambda p: None
        try:
            cs = EVO.suc_khoe_quantlab() + EVO.suc_khoe_evo()
        finally:
            EVO._tuoi_tep = that
        theo_tep = [c for c in cs if c["ten"].startswith("quantlab.ho_so_")
                    or c["ten"] == "evo.finder"]
        self.assertTrue(theo_tep)
        for c in theo_tep:
            self.assertEqual(c["trang_thai"], EVO.CHUA_DO, c["ten"])


class MoiKetLuanXAU_PhaiKemBANG_CHUNG(unittest.TestCase):
    def test_khong_co_chi_so_XAU_nao_trong_rong(self):
        ket = EVO.do_het()
        for c in ket["chi_so"]:
            if c["trang_thai"] != EVO.XAU:
                continue
            self.assertTrue(
                str(c["bang_chung"]).strip() or c["gia_tri"] is not None,
                "%s bao XAU ma khong co bang chung dem duoc" % c["ten"])

    def test_chi_so_XAU_co_cat_nghia(self):
        ket = EVO.do_het()
        for c in ket["chi_so"]:
            if c["trang_thai"] == EVO.XAU:
                self.assertIn("cat_nghia", c,
                              "%s bao XAU ma khong cat nghia" % c["ten"])

    def test_moi_ten_trong_bang_cat_nghia_deu_la_chi_so_that(self):
        """Mot dong cat nghia tro toi chi so khong ton tai = ghi chu chet."""
        ten = {c["ten"] for c in EVO.do_het()["chi_so"]}
        la = sorted(set(EVO.CAT_NGHIA) - ten)
        self.assertEqual(la, [], "cat nghia cho chi so khong co: %s" % la)


class BaoCaoPhaiDOC_DUOC(unittest.TestCase):
    def test_bao_cao_noi_ro_CHUA_DO_khac_XAU(self):
        vb = EVO.bao_cao(in_ra=lambda *a, **k: None)
        self.assertIn("CHUA_DO", vb)
        self.assertIn("khong phai", vb)

    def test_de_xuat_neu_co_thi_phai_la_LENH(self):
        ket = EVO.do_het()
        for c in ket["chi_so"]:
            dx = (c.get("de_xuat") or "").strip()
            if dx:
                self.assertTrue(dx.startswith("python") or dx.startswith("xem"),
                                "%s: de xuat khong phai lenh chay duoc: %r"
                                % (c["ten"], dx[:60]))

    def test_ghi_so_khong_nem_loi_khi_khong_co_van_de(self):
        self.assertEqual(EVO.ghi_van_de([], in_ra=lambda *a, **k: None), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)


# ------------------------------------------- SO VAN DE PHAI DONG LAI DUOC
#
# Them 13/09/2026. So van de chi MO ma khong DONG thi khong ai doc no nua -
# va do khong phai suy doan: chieu 13/09 no co 24 dong, trong do
#   `dia_thap`            "Dia con 7.6 GB" trong khi dia da 30,8 GB
#   `EVO/xay.viec_hong`   trong khi chi so do dang TOT
#   `EVO/evo.van_de_mo`   mot VAN DE ve viec CO VAN DE - vong tu nuoi
#
# Ba duong dong, ba ho loi khac nhau:
#   1. `dong_van_de_het_hieu_luc` chi nam trong `mot_luot()` (duong
#      supervisor); duong chay tay `b evo` chi biet MO.
#   2. Van de do LLM ghi mang ma sinh, khong nam trong `EVO_TU_QUAN`, nen
#      khong co duong dong nao ca.
#   3. `evo.van_de_mo` do CHINH so van de ma lai duoc phep ghi them mot van
#      de - mot thuoc do khong duoc lam thay doi thu no dang do.

class SoVanDePhaiDongLaiDuoc(unittest.TestCase):

    def test_chi_so_tu_chieu_khong_duoc_sinh_van_de(self):
        from nhan import evo as EVO
        self.assertIn("evo.van_de_mo", EVO.CHI_SO_TU_CHIEU)

    def test_ham_dong_dung_chung_cho_CA_HAI_duong(self):
        """Mot luat chi song neu no nam o cho HEP NHAT."""
        from tru import evolution as TEVO
        from nhan import evo as EVO
        self.assertTrue(callable(TEVO.dong_van_de_het_hieu_luc))
        self.assertTrue(callable(EVO.dong_van_de_theo_chi_so))
        import inspect
        ma = inspect.getsource(EVO.ghi_van_de)
        self.assertIn("dong_van_de_het_hieu_luc", ma,
                      "duong chay tay khong goi ham dong -> so chi dai ra")

    def test_dong_khi_chi_so_goc_da_TOT(self):
        import json
        from nhan import evo as EVO
        from nhan import so as SO
        ma = "thu_dong_theo_chi_so"
        SO.bao_van_de(ma, "VUA", "thu", {"chi_so": "dia.con_trong"})
        try:
            mo = {x["ma"] for x in SO.van_de_mo()}
            self.assertIn(ma, mo, "chua ghi duoc van de thu - bo do mu")
            EVO.dong_van_de_theo_chi_so(in_ra=None)
            self.assertNotIn(ma, {x["ma"] for x in SO.van_de_mo()},
                             "chi so `dia.con_trong` dang TOT ma van de van mo")
        finally:
            SO.dong_van_de(ma, "don test")

    def test_KHONG_dong_khi_chi_so_goc_van_XAU(self):
        """Chieu nguoc lai - mot cong dong TAT CA cung vo dung."""
        from nhan import evo as EVO
        from nhan import so as SO
        ma = "thu_khong_duoc_dong"
        SO.bao_van_de(ma, "VUA", "thu", {"chi_so": "chi_so_khong_ton_tai_xyz"})
        try:
            EVO.dong_van_de_theo_chi_so(in_ra=None)
            self.assertIn(ma, {x["ma"] for x in SO.van_de_mo()},
                          "dong ca van de ma chi so goc khong do duoc")
        finally:
            SO.dong_van_de(ma, "don test")

    def test_nguong_khong_tai_phat_hop_ly(self):
        from nhan import evo as EVO
        self.assertGreaterEqual(EVO.NGAY_KHONG_TAI_PHAT, 1,
                                "dong ngay trong ngay se dong oan su co that")
        self.assertLessEqual(EVO.NGAY_KHONG_TAI_PHAT, 7)
