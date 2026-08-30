# -*- coding: utf-8 -*-
"""Chon BAN du lieu theo khung, khong theo dung luong byte.

Bay bi bat ngay 24/08/2026: `kho()` giu MOT ban moi ma - ban to nhat theo byte.
File phut luon to hon file ngay, nen moi yeu cau D1 deu gop file phut len ngay
va nhan doan lich su NGAN NHAT co trong kho:

    US500CASH     2.642 bar (2018+)  trong khi ban D1 co 4.027 (2011+)
    XM_US500CASH    367 bar          trong khi ban D1 co 4.028
    XM_US100CASH    367 bar          trong khi ban D1 co 3.995

367 bar la duoi nguong 1.500 cua `nha_may_null.duong_cong_luc`, nen hai ma chi
so cua XM khong co mat trong bat ky vong quet D1 nao - im lang hoan toan.

286 bai test truoc do khong bai nao bat duoc, vi khong bai nao hoi "chuoi nay
da la chuoi DAI NHAT kho co chua".
"""
from __future__ import annotations

import unittest

from nhan import du_lieu as DL


class ChonBanTheoKhung(unittest.TestCase):

    def test_uoc_bar_tu_choi_khung_min_hon(self):
        """Ban D1 khong duoc dung de tao H1 - do la noi suy nguoc."""
        ban_d1 = {"khung_goc": "D1", "so_dong": 5000}
        self.assertEqual(DL._uoc_bar_o_khung(ban_d1, "H1"), 0)
        self.assertEqual(DL._uoc_bar_o_khung(ban_d1, "D1"), 5000)

    def test_uoc_bar_quy_doi_khung(self):
        ban_h1 = {"khung_goc": "H1", "so_dong": 24_000}
        self.assertEqual(DL._uoc_bar_o_khung(ban_h1, "D1"), 1000)

    def test_lop_nguon_co_ban_san_thi_la_san(self):
        """Mot ban `san` la du de ma do thuoc ve san - ban `ngoai` cung ten la
        nhan sai (us500cash_daily thuc ra la Yahoo ^GSPC)."""
        self.assertEqual(DL.lop_nguon_cua(
            [{"nguon": "ngoai"}, {"nguon": "san"}]), "san")
        self.assertEqual(DL.lop_nguon_cua([{"nguon": "ngoai"}]), "ngoai")

    def test_xm_la_file_san_khong_phai_nguon_ngoai(self):
        """`xm_us500cash_daily` va `us500cash_xm_daily` la CUNG MOT chuoi
        (lech 0,0000%, tuong quan 1,0000). Xep chung khac lop la ap hai nguong
        open bia khac nhau len cung mot cong cu."""
        self.assertEqual(DL.nguon_cua("xm_us500cash_daily"), "san")
        self.assertEqual(DL.nguon_cua("us500cash_xm_daily"), "san")
        self.assertEqual(DL.nguon_cua("yh_nasdaq_daily"), "ngoai")
        self.assertEqual(DL.nguon_cua("sp500_daily"), "ngoai")

    def test_us500cash_khong_duoc_lay_ban_yahoo(self):
        """`us500cash_daily.parquet` khop 0,000 voi `sp500_daily` (Yahoo ^GSPC).
        Neu ban do duoc chon thi US500CASH tro thanh ban sao cua SP500 - hai
        'tai san' trong cung ho FDR ma thuc ra la mot chuoi."""
        kho = DL.kho()
        if "US500CASH" not in kho:
            self.skipTest("kho khong co US500CASH")
        ban = DL.ban_cho_khung("US500CASH", "D1")
        self.assertIsNotNone(ban)
        self.assertNotEqual(ban["file"].name, "us500cash_daily.parquet")
        self.assertEqual(ban["nguon"], "san")

    def test_moi_khung_lay_ban_phu_dai_nhat(self):
        """Tinh chat chung: khong ma nao duoc nhan chuoi NGAN hon ban tot nhat
        cung lop dang nam trong kho."""
        kho = DL.kho()
        thieu = []
        for ma, v in kho.items():
            cac = v.get("cac_ban") or []
            lop = v.get("lop_nguon")
            ung = [b for b in cac if b["du_ohlc"] and b["nguon"] == lop
                   and DL._uoc_bar_o_khung(b, "D1") > 0]
            if not ung:
                continue
            tot = max(DL._uoc_bar_o_khung(b, "D1") for b in ung)
            chon = DL.ban_cho_khung(ma, "D1")
            if chon is None:
                thieu.append((ma, "khong chon duoc"))
                continue
            if DL._uoc_bar_o_khung(chon, "D1") < 0.9 * tot:
                thieu.append((ma, chon["file"].name, tot))
        self.assertEqual(thieu, [], f"ban duoc chon ngan hon ban tot nhat: {thieu}")

    def test_cache_mang_ten_file_nguon(self):
        """Ten cache phai mang ten ban nguon. Neu chi `{ma}_{khung}` thi doi
        luat chon xong cache cu van 'moi hon file goc' va duoc dung tiep."""
        ban = DL.ban_cho_khung("US500CASH", "D1")
        if ban is None:
            self.skipTest("kho khong co US500CASH")
        DL.nap("US500CASH", "D1")
        f = DL.CACHE / f"US500CASH_D1__{ban['file'].stem}.parquet"
        self.assertTrue(f.exists(), f"khong thay cache {f.name}")


class BeMatSauKhiSua(unittest.TestCase):

    def test_us500cash_d1_du_dai(self):
        """Moc chan: 4.027 bar tu 2011. Truoc 24/08 la 2.642 bar tu 2018."""
        try:
            df = DL.nap("US500CASH", "D1")
        except Exception as e:      # kho co the thieu tren may khac
            self.skipTest(str(e))
        self.assertGreaterEqual(len(df), 4000)
        self.assertLessEqual(df.index.min().year, 2012)
        self.assertIn("spread", df.columns,
                      "ban D1 cua US500CASH phai giu cot spread that")

    def test_chi_so_xm_vao_duoc_be_mat_d1(self):
        """Hai ma nay tung bi loai khoi moi vong quet D1 vi chi co 367 bar."""
        for ma in ("XM_US500CASH", "XM_US100CASH"):
            if ma not in DL.kho():
                continue
            df = DL.nap(ma, "D1")
            self.assertGreaterEqual(len(df), 1500,
                                    f"{ma} van duoi nguong quet")


if __name__ == "__main__":
    unittest.main()
