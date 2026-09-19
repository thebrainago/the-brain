# -*- coding: utf-8 -*-
"""Test cho `nhan/kiem_quy_uoc.py` - CHUYEN VIEC DOC DIFF THANH MOT PHEP DO.

Sau ba don hang giao cho mo hinh re, cung mot nhom loi lap lai o ca ba. Doc
diff de bat chung la viec lap lai, va viec lap lai thi khong nen tra tien cho
mot mo hinh manh.

Bo test nay lam hai viec:
  1. kiem chinh bo kiem (no co bat duoc loi that khong, va co bao dong gia
     khong);
  2. AP no len kho that - de mot don hang moi khong the lot vao voi cac loi da
     biet.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from nhan import hephaestus as HP
from nhan import kiem_quy_uoc as KQ


class BoKiemPhaiBAT_DUNG(unittest.TestCase):
    """Hieu chuan HAI CHIEU: bat duoc loi that, va khong bao dong gia."""

    def test_bat_duoc_dong_chu_thich_co_dau(self):
        self.assertTrue(KQ.dong_co_dau("# day la mot dòng có dấu\n"))

    def test_khong_bao_dong_tieng_viet_KHONG_dau(self):
        self.assertEqual(KQ.dong_co_dau("# day la mot dong khong dau\n"), [])

    def test_khong_cham_dong_MA_chi_cham_chu_thich(self):
        """`x = 'chuỗi có dấu'` la du lieu, khong phai chu thich."""
        self.assertEqual(KQ.dong_co_dau("x = 'chuoi có dấu'\n"), [])

    def test_bat_duoc_co_che_TRUNG_giua_hai_khuon(self):
        ds = [{"ten": "a", "khuon": "k1", "co_che": "x" * 80},
              {"ten": "b", "khuon": "k2", "co_che": "x" * 80}]
        self.assertEqual(len(KQ.co_che_trung(ds)), 1)

    def test_cung_mot_khuon_dung_lai_cau_thi_KHONG_phai_loi(self):
        """Hai chieu cua cung mot luan diem duoc phep dung chung cau."""
        ds = [{"ten": "a", "khuon": "k1", "co_che": "x" * 80},
              {"ten": "b", "khuon": "k1", "co_che": "x" * 80}]
        self.assertEqual(KQ.co_che_trung(ds), [])

    def test_bat_duoc_cau_qua_ngan(self):
        self.assertTrue(KQ.co_che_yeu([{"ten": "a", "co_che": "ngan qua"}]))

    def test_bat_duoc_cau_chi_liet_ke_tham_so(self):
        ds = [{"ten": "a", "co_che": "Mua khi rsi voi tham so n = 14 va "
                                     "nguong = 30 tren khung gio cua tai san."}]
        self.assertTrue(KQ.co_che_yeu(ds))

    def test_bat_duoc_ho_lech_nhom(self):
        ds = [{"ten": "a", "ho": "bien_dong",
               "vao": [{"trai": {"chi_bao": "gio"}, "phep": "==",
                        "phai": {"hang": 9}}]}]
        self.assertTrue(KQ.ho_lech_nhom(ds, HP.nhom_cua))

    def test_co_che_GHEP_qua_ho_thi_khong_bi_cham(self):
        """Ghep hai nhom thi `ho` la mot LUA CHON, khong phai mot suy ra."""
        ds = [{"ten": "a", "ho": "quay_ve_trung_binh",
               "vao": [{"trai": {"chi_bao": "rsi", "n": 14}, "phep": "<",
                        "phai": {"hang": 30}},
                       {"trai": {"chi_bao": "gia", "cot": "close"}, "phep": ">",
                        "phai": {"chi_bao": "ema", "n": 200}}]}]
        self.assertEqual(KQ.ho_lech_nhom(ds, HP.nhom_cua), [])


class AP_LEN_KHO_THAT(unittest.TestCase):
    """Mot don hang moi khong duoc lot vao voi cac loi da biet."""

    def setUp(self):
        self.ds = HP.duc(han_ngach=100000)

    def test_khong_co_che_nao_dung_chung_cau_voi_khuon_khac(self):
        trung = KQ.co_che_trung(self.ds)
        self.assertEqual(trung, [],
                         "hai khuon chung mot luan diem = tra tien FDR hai lan")

    def test_moi_cau_co_che_deu_la_mot_LUAN_DIEM(self):
        self.assertEqual(KQ.co_che_yeu(self.ds)[:5], [])

    def test_ho_khai_khop_von_tu(self):
        self.assertEqual(KQ.ho_lech_nhom(self.ds, HP.nhom_cua)[:5], [])

    def test_ba_module_may_de_viet_khong_dau(self):
        for ten in ("hephaestus.py", "kiem_quy_uoc.py", "quan_tri_than.py"):
            p = Path(HP.__file__).parent / ten
            self.assertEqual(
                KQ.dong_co_dau(p.read_text(encoding="utf-8"))[:3], [], ten)
