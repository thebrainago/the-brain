# -*- coding: utf-8 -*-
"""Quet SONG SONG nhung dang ky TUAN TU.

So FDR nhay THU TU: nguong LORD giam theo 1/j^1.6, nen phep thu thu j duoc xet
o mot nguong khac phep thu thu j+1. Neu nhieu tien trinh cung dang ky thi chuoi
quyet dinh phu thuoc thu tu hoan thanh cua he dieu hanh - khong tai dung lai
duoc. Vi the phan QUET (thuan tinh toan) chia cho nhieu tien trinh, con phan
DANG KY (cham so) o lai tien trinh cha.
"""
from __future__ import annotations

import inspect
import unittest

from tru import quantlab as QL


class QuetTachKhoiDangKy(unittest.TestCase):
    def test_kham_pha_co_the_quet_ma_khong_cham_so(self):
        self.assertIn("dang_ky", inspect.signature(QL.kham_pha).parameters)

    def test_tien_trinh_con_KHONG_dang_ky(self):
        """`_quet_mot` chay o tien trinh con - phai goi voi dang_ky=False."""
        self.assertIn("dang_ky=False", inspect.getsource(QL._quet_mot))

    def test_dang_ky_sau_quet_la_ham_rieng(self):
        self.assertTrue(callable(QL.dang_ky_sau_quet))

    def test_dang_ky_nam_o_CHA_trong_vong_lap_ket_qua(self):
        src = inspect.getsource(QL.kham_pha_nhieu)
        self.assertIn("dang_ky_sau_quet", src)
        self.assertNotIn("Pool(", src)      # tao pool da chuyen sang _pool_quet


class SoTienTrinhCoTRAN(unittest.TestCase):
    """Do that tren may nay: 1->2 duoc 1,47x nhung 4->10 chi them 1,18x. Quet
    nghet BANG THONG BO NHO, khong nghet CPU - vuot so nhan vat ly thi cac tien
    trinh tranh bang thong chu khong them viec."""

    def test_khong_vuot_qua_nua_so_luong_logic(self):
        import os
        tran = max(1, (os.cpu_count() or 2) // 2)
        self.assertLessEqual(QL._so_tien_trinh_quet(999), tran)

    def test_luon_it_nhat_mot(self):
        self.assertGreaterEqual(QL._so_tien_trinh_quet(0), 1)
        self.assertGreaterEqual(QL._so_tien_trinh_quet(-5), 1)


class PoolDuocDUNG_LAI(unittest.TestCase):
    """Tren Windows moi tien trinh con phai nap lai pandas/numpy - vai giay MOI
    LAN. Tao pool cho tung me thi mot luot 150 giay quet duoc nhieu tai san hon
    nhung so TO HOP khong tang; do that: 10.266 -> 21.982 to hop sau khi dung lai."""

    def test_co_ham_dung_lai_pool(self):
        self.assertTrue(callable(QL._pool_quet))

    def test_pool_duoc_dep_khi_thoat(self):
        """De lai 10 tien trinh con moi luot thi sau vai gio may day tien trinh
        chet ma khong ai truy ra tu dau."""
        self.assertIn("atexit.register", inspect.getsource(QL))


if __name__ == "__main__":
    unittest.main()
