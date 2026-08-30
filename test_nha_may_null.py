# -*- coding: utf-8 -*-
"""Test nha may null: kiem tra ca ba phuong phap sinh null.
Kiem tra:
  1. Block bootstrap sinh du so chuoi
  2. GARCH sinh du so chuoi
  3. Hoan vi thoi gian sinh du so chuoi
  4. So chuoi >= 200 (chiều nghịch: it nhat co null)
  5. Chuoi null co gia tri trung binh ~ 0
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
import numpy as np
LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)
from nhan import nha_may_null as NM

class NullBlockBootstrap(unittest.TestCase):

    def test_sinh_du_200_chuoi(self):
        nulls = NM.null_block_bootstrap('EURCAD', 'H1', so_chuoi=200)
        self.assertGreaterEqual(len(nulls), 200)
        for n in nulls:
            self.assertGreater(len(n), 100)

    def test_chuoi_null_co_trung_binh_gan_0(self):
        nulls = NM.null_block_bootstrap('EURCAD', 'H1', so_chuoi=5)
        for n in nulls:
            self.assertAlmostEqual(float(np.mean(n)), 0.0, delta=0.001)

    def test_chuoi_null_co_phuong_sai_duong(self):
        nulls = NM.null_block_bootstrap('EURCAD', 'H1', so_chuoi=5)
        for n in nulls:
            self.assertGreater(float(np.std(n)), 0)

class NullGARCH(unittest.TestCase):

    def test_sinh_du_200_chuoi(self):
        nulls = NM.null_garch('EURCAD', 'H1', so_chuoi=200)
        self.assertGreaterEqual(len(nulls), 200)

    def test_chuoi_null_co_phuong_sai_thay_doi(self):
        """GARCH phai co cum bien dong."""
        nulls = NM.null_garch('EURCAD', 'H1', so_chuoi=3)
        for n in nulls:
            var_first = float(np.var(n[:len(n)//2]))
            var_second = float(np.var(n[len(n)//2:]))
            self.assertGreater(abs(var_first - var_second), 0)

class NullPermuteTime(unittest.TestCase):

    def test_sinh_du_200_chuoi(self):
        nulls = NM.null_permute_time('EURCAD', 'H1', so_chuoi=200)
        self.assertGreaterEqual(len(nulls), 200)

    def test_chuoi_null_giu_phan_phoi_bien(self):
        """Hoan vi phai giu phan phoi bien cua chuoi goc."""
        nulls = NM.null_permute_time('EURCAD', 'H1', so_chuoi=3)
        df = __import__('nhan.du_lieu', fromlist=['']).nap('EURCAD', 'H1')
        r = __import__('nhan.mo_phong', fromlist=[''])._loi_suat_tien(df)
        r = r[r != 0]
        for n in nulls:
            self.assertAlmostEqual(float(np.mean(n)), float(np.mean(r)), delta=0.001)
            self.assertAlmostEqual(float(np.std(n)), float(np.std(r)), delta=0.001)

class TaoNull(unittest.TestCase):

    def test_tao_null_block_bootstrap(self):
        nulls = NM.tao_null('EURCAD', 'H1', 'test', so_chuoi=10,
                            phuong_phap='block_bootstrap')
        self.assertEqual(len(nulls), 10)

    def test_tao_null_garch(self):
        nulls = NM.tao_null('EURCAD', 'H1', 'test', so_chuoi=10,
                            phuong_phap='garch')
        self.assertEqual(len(nulls), 10)

    def test_tao_null_permute_time(self):
        nulls = NM.tao_null('EURCAD', 'H1', 'test', so_chuoi=10,
                            phuong_phap='permute_time')
        self.assertEqual(len(nulls), 10)

    def test_tao_null_day_du_co_3_pp(self):
        ra = NM.tao_null_day_du('EURCAD', 'H1', 'test', so_chuoi=5)
        self.assertEqual(set(ra.keys()), {'block_bootstrap', 'garch', 'permute_time'})
        for pp, nulls in ra.items():
            self.assertEqual(len(nulls), 5, f'{pp} khong du 5 chuoi')

    def test_phuong_phap_khong_hop_le(self):
        with self.assertRaises(ValueError):
            NM.tao_null('EURCAD', 'H1', 'test', phuong_phap='khong_co')
