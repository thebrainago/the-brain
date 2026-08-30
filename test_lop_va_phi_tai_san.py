# -*- coding: utf-8 -*-
"""Lop tai san + tra cuu phi cho ma CO TIEN TO KHO (`XM_`, `YH_`, `ETF_`).

Hai bay bat ngay 24/08, ca hai nam o khau CHI PHI - tuc o cho quyet dinh mot
co che "song qua chi phi that" hay khong:

1. `chuan_hoa_phoi_nhiem` khong bo tien to do KHO DU LIEU dat them, nen
   `XM_US100CASH` -> 'XM_US100' khong khop gi, trong khi `US100CASH` -> 'US100'
   khop XM:US100CASH. Cung mot symbol cua cung mot san, chi khac tien to ten
   file, ma mot ben co phi do that con ben kia roi ve bang khai bao.
   Dien anh huong: 11 ma `XM_*` va 30 ma `YH_*`.

2. `_lop_cua` doi chieu bang CHUOI CON cua ten file (`"US500" in m`), nen
   SP500, YH_DOWJONES, YH_HANGSENG, XM_US100CASH... deu roi vao `fx_cheo` -
   spread tinh thua ~3,9 lan va phi giu tinh thieu 2,5 lan.
"""
from __future__ import annotations

import unittest

from nhan import chi_phi as CP
from nhan import sang_loc as SL


class TienToKho(unittest.TestCase):

    def test_bo_tien_to_truoc_khi_tra_cuu(self):
        for co, khong in (("XM_US100CASH", "US100CASH"),
                          ("XM_US500CASH", "US500CASH"),
                          ("XM_US30CASH", "US30CASH")):
            self.assertEqual(CP.chuan_hoa_phoi_nhiem(co),
                             CP.chuan_hoa_phoi_nhiem(khong),
                             f"{co} va {khong} phai la CUNG mot phoi nhiem")

    def test_chi_so_yahoo_tra_ve_phoi_nhiem_cfd(self):
        """Chi so khong mua truc tiep duoc; kenh giao dich la CFD cua san."""
        self.assertEqual(CP.chuan_hoa_phoi_nhiem("YH_NASDAQ"), "US100")
        self.assertEqual(CP.chuan_hoa_phoi_nhiem("YH_DOWJONES"), "US30")
        self.assertEqual(CP.chuan_hoa_phoi_nhiem("YH_DAX"), "GER40")
        self.assertEqual(CP.chuan_hoa_phoi_nhiem("YH_NIKKEI"), "JP225")

    def test_tim_duoc_phi_cho_ma_co_tien_to(self):
        thieu = [m for m in ("XM_US100CASH", "XM_US500CASH", "XM_US30CASH",
                             "XM_US2000CASH", "XM_AUS200CASH", "XM_JP225CASH",
                             "YH_NASDAQ", "YH_DAX", "YH_NIKKEI", "YH_FTSE100")
                 if CP.phi_cua(m) is None]
        self.assertEqual(thieu, [], f"khong tra cuu duoc phi: {thieu}")

    def test_tien_to_khong_lam_hong_ma_fx_thuong(self):
        self.assertEqual(CP.chuan_hoa_phoi_nhiem("EURCAD"), "EURCAD")
        self.assertEqual(CP.chuan_hoa_phoi_nhiem("XAUUSD"), "XAUUSD")


class LopTaiSan(unittest.TestCase):

    def test_chi_so_khong_bi_xep_thanh_fx(self):
        for m in ("SP500", "US500CASH", "XM_US100CASH", "XM_US2000CASH",
                  "XM_AUS200CASH", "YH_DOWJONES", "YH_HANGSENG", "YH_IBEX35",
                  "YH_AEX", "YH_TSX", "YH_SMI", "YH_EUSTOXX50",
                  "YH_RUSSELL2000", "YH_NASDAQ", "DE40"):
            self.assertEqual(SL._lop_cua(m), "chi_so", m)

    def test_kim_loai_va_hang_hoa_co_lop_rieng(self):
        for m in ("XAUUSD", "XM_GOLD", "XM_SILVER", "YH_VANG", "YH_BAC",
                  "XM_XAUEUR"):
            self.assertEqual(SL._lop_cua(m), "vang", m)
        for m in ("YH_DAUWTI", "YH_KHIDOT", "YH_DONG", "YH_NGO", "YH_DAUTUONG"):
            self.assertEqual(SL._lop_cua(m), "hang_hoa", m)

    def test_fx_van_dung_lop_cu(self):
        self.assertEqual(SL._lop_cua("EURUSD"), "fx_major")
        self.assertEqual(SL._lop_cua("EURCAD"), "fx_cheo")
        self.assertEqual(SL._lop_cua("NZDHUF"), "fx_cheo")

    def test_moi_lop_deu_co_dong_trong_bang_chi_phi(self):
        """Mot lop khong co dong trong bang se lang le nhan chi phi cua
        `fx_cheo` - dat hon chi so 3,9 lan o spread."""
        for m, mong in (("YH_DAUWTI", "hang_hoa"), ("YH_NASDAQ", "chi_so"),
                        ("XAUUSD", "vang")):
            cp = SL._chi_phi_cua(m)
            self.assertIsNotNone(cp, m)
            self.assertEqual(SL._lop_cua(m), mong, m)

    def test_chi_so_khong_dat_hon_fx_cheo(self):
        """Bat lai chinh chieu sai cu: chi so bi tinh spread cua FX cheo."""
        cp_cs = SL._chi_phi_cua("YH_NASDAQ")
        self.assertLess(cp_cs.spread_frac_chung, 1.0e-4,
                        "chi so an spread cua FX cheo")


if __name__ == "__main__":
    unittest.main()


class NutCauHinhChet(unittest.TestCase):
    """Nut chet = khoa trong `config/tieu_chi.json` khong cho nao doc.

    Nguy hon nut sai gia tri: van nut ma khong co gi doi, nen nguoi van tin la
    minh da siet tieu chi. Ngay 24/08 co 5 nut nhu vay, trong do
    `v2.ty_le_lenh_lon_nhat_max` chi khac ten that (`..._bar_...`) mot chu.
    """

    def test_cau_hinh_dang_dung_khong_con_khoa_la(self):
        import json
        if not SL.TIEU_CHI_FILE.exists():
            self.skipTest("khong co file tieu chi")
        ngoai = json.loads(SL.TIEU_CHI_FILE.read_text(encoding="utf-8-sig"))
        self.assertEqual(SL.khoa_la(ngoai), [])

    def test_bat_duoc_khoa_go_sai(self):
        la = SL.khoa_la({"v2": {"ty_le_lenh_lon_nhat_max": 0.4}, "v9": {}})
        self.assertIn("v2.ty_le_lenh_lon_nhat_max", la)
        self.assertIn("v9", la)

    def test_khoa_dung_thi_khong_bao(self):
        self.assertEqual(SL.khoa_la({"v1": {"so_lenh_min": 30},
                                     "phien_ban": "x"}), [])


class DoChiPhiTuNguonTotNhat(unittest.TestCase):
    """Chi phi la DAI LUONG RIENG - phai do tu nguon tot nhat cho no.

    Sau khi `ban_cho_khung` chon ban D1 dai nhat (24/08), bon ma FX tut tu
    `do_tin=SAN` xuong `KHAI` va an spread bia 1,00 bps, chi vi ban D1 dai nhat
    khong co cot spread - trong khi ban M1 cua chinh chung co 82.000+ bar spread
    that. Muc do duoc: 1,90-2,75 bps, tuc chi phi bi tinh THIEU 1,9-2,75 lan.
    """

    def test_chon_khung_co_spread_that(self):
        from nhan import du_lieu as DL
        # FX: ban M1 co spread -> gop len H1 (khong nap 5 trieu dong M1)
        for m in ("EURCAD", "AUDCAD", "EURGBP", "AUDNZD", "AUDCHF"):
            if m not in DL.kho():
                continue
            self.assertEqual(DL.khung_do_spread(m), "H1", m)
        # US500CASH nguoc lai: chi ban D1 co spread, H1 khong co
        if "US500CASH" in DL.kho():
            self.assertEqual(DL.khung_do_spread("US500CASH"), "D1")

    def test_khong_ma_nao_tut_ve_spread_bia(self):
        """1,00 bps la gia tri KHAI BAO cuoi cung cua `chi_phi.tu_du_lieu` khi
        khong do duoc gi. Ma nao co cot spread that ma van nhan so do la dau
        hieu duong do bi dut."""
        from nhan import du_lieu as DL
        xau = []
        for m in ("EURCAD", "GBPCAD", "AUDCAD", "NZDCAD", "EURGBP", "AUDNZD",
                  "AUDCHF"):
            if m not in DL.kho():
                continue
            cp = SL._chi_phi_cua(m)
            if str(getattr(cp, "do_tin", "KHAI")) == "KHAI":
                xau.append((m, cp.spread_frac_chung * 1e4))
        self.assertEqual(xau, [], f"tut ve chi phi khai bao: {xau}")
