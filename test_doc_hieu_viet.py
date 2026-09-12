# -*- coding: utf-8 -*-
"""Kiem bo doc van xuoi doc duoc TIENG VIET va tach dung ve THOAT.

Hai lo hong do duoc 12/09/2026 khi dung thu luong uu tien cua chu du an:

  1. `loai_cau` chi biet dang dai khong dau ("mua vao", "vao lenh mua"). Chu du
     an go "Mua khi RSI 14 duoi 30" - dang ngan, co dau - va he tra ve 0 co che
     ma khong noi gi. Tuc cai cua xay RIENG cho chu du an khong doc duoc ngon
     ngu cua chu du an.

  2. Nang hon: "Buy when RSI < 30, exit when RSI > 55" (ngan cach bang DAU PHAY,
     khong co "and") thi `_NOI_RA` khong khop, ve THOAT bi NUOT VAO ve VAO, va
     spec ra doi la `rsi < 30 VA rsi > 55` - **khong bao gio kich hoat duoc**.
     Khong bao loi. Mot co che chet duoc dang ky nhu mot co che that.

Cai kiem quan trong nhat o day la muc 2: no khong kiem "co doc duoc khong" ma
kiem "co doc SAI khong".
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import doc_hieu as DH  # noqa: E402


def spec(cau: str):
    b = DH.doc_bai(cau, "thu", "thu", toi_thieu=0)
    return b[0]["spec"] if b else None


class TiengVietPhaiDocDuoc(unittest.TestCase):
    def test_mua_co_dau(self):
        s = spec("Mua khi RSI 14 dưới 30.")
        self.assertIsNotNone(s, "khong doc duoc cau mua tieng Viet co dau")
        self.assertEqual(s["chieu"], 1)

    def test_ban_co_dau_ra_chieu_am(self):
        s = spec("Bán khi RSI 14 trên 70.")
        self.assertIsNotNone(s)
        self.assertEqual(s["chieu"], -1, "cau BAN phai ra chieu -1")

    def test_khong_dau_van_chay(self):
        s = spec("Mua khi RSI 14 duoi 30.")
        self.assertIsNotNone(s)
        self.assertEqual(s["chieu"], 1)

    def test_mua_vu_KHONG_bi_doc_thanh_lenh_mua(self):
        """'mua vu' (seasonality) la tu khoa cua chinh du an. Mot pattern 'mua'
        tran se nuot no va sinh co che rac tu moi bai noi ve mua vu."""
        self.assertIsNone(DH.loai_cau("Tinh mua vu cua vang khi RSI duoi 30"))
        self.assertIsNone(DH.loai_cau("Mua vu cuoi nam thuong manh hon khi VIX tren 20"))


class VeThoatKhongDuocNUOT_VAO_VE_VAO(unittest.TestCase):
    def test_dau_phay_van_tach_duoc(self):
        s = spec("Buy when RSI 14 is below 30, exit when RSI is above 55.")
        self.assertIsNotNone(s)
        self.assertEqual(len(s["vao"]), 1, "ve THOAT bi nuot vao ve VAO")
        self.assertEqual(len(s["ra"]), 1, "mat ve THOAT")

    def test_dau_phay_tieng_viet(self):
        s = spec("Mua khi RSI 14 dưới 30, thoát khi RSI trên 55.")
        self.assertIsNotNone(s)
        self.assertEqual(len(s["vao"]), 1)
        self.assertEqual(len(s["ra"]), 1)

    def test_khong_sinh_dieu_kien_TU_MAU_THUAN(self):
        """Chot chan cuoi: hai dieu kien tren CUNG mot toan hang, mot '<' mot
        '>' voi nguong '<' THAP hon, thi giao cua chung la RONG."""
        for cau in ("Buy when RSI 14 is below 30, exit when RSI is above 55.",
                    "Mua khi RSI 14 dưới 30, thoát khi RSI trên 55."):
            s = spec(cau)
            self.assertIsNotNone(s, cau)
            mau_thuan = False
            for i, a in enumerate(s["vao"]):
                for b in s["vao"][i + 1:]:
                    if a.get("trai") != b.get("trai"):
                        continue
                    ta, tb = a.get("phep"), b.get("phep")
                    va = (a.get("phai") or {}).get("hang")
                    vb = (b.get("phai") or {}).get("hang")
                    if None in (va, vb):
                        continue
                    if {ta, tb} == {"<", ">"} and (
                            (ta == "<" and va <= vb) or (tb == "<" and vb <= va)):
                        mau_thuan = True
            self.assertFalse(mau_thuan,
                             "spec co dieu kien VAO tu mau thuan: %s" % s["vao"])

    def test_giu_van_doc_duoc_so_bar(self):
        s = spec("Buy when RSI is below 30 and hold for 5 days.")
        self.assertIsNotNone(s)
        self.assertEqual(s["giu"], 5)


class TiengAnhKHONG_DUOC_HONG(unittest.TestCase):
    """Noi long mau la de doc them, khong duoc lam hong duong tieng Anh."""

    def test_cau_anh_co_lien_tu_van_tach(self):
        s = spec("Buy when RSI 14 is below 30 and exit when RSI is above 55.")
        self.assertIsNotNone(s)
        self.assertEqual(len(s["ra"]), 1)

    def test_cau_tach_bang_dau_cham(self):
        s = spec("Buy when RSI 14 is below 30. Exit when RSI is above 55.")
        self.assertIsNotNone(s)
        self.assertEqual(len(s["vao"]), 1)
        self.assertEqual(len(s["ra"]), 1)

    def test_van_ke_chuyen_van_bi_tu_choi(self):
        for c in ("The number represents a significant sell-off in a stock",
                  "I was talking to my trading buddy about buying the dip",
                  "Russell 3000 Index"):
            self.assertIsNone(DH.loai_cau(c), c)


if __name__ == "__main__":
    unittest.main(verbosity=2)
