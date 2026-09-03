# -*- coding: utf-8 -*-
"""HANG DOI VIEC CUA QUANTLAB: chong nghen, gianh viec nguyen tu, uu tien nguon.

Chu du an 03/09/2026: *"Xay co che xep hang de tranh nghen va tang toc do xu li
cua quantlab. Uu tien xu li ngoai sinh roi toi noi sinh (hoac lam song song)."*

`candidate_queue` KHONG dung duoc: no la hop dong SEEKER->QUANTLAB va CHI-GHI-
THEM theo thiet ke (trigger chan ca UPDATE lan DELETE). Do that: 555 dong nam
yen tu 21/08, cung `priority=5`, khong ai tieu thu, va khong co cho nao danh
dau "da xu ly".
"""
from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from nhan import hang_doi as HD
from nhan import so as SO


def _viec(n, tai_san="US500CASH", khung="H4", template="rsi_dao_chieu"):
    return [{"tai_san": tai_san, "khung": khung, "template": template,
             "tham_so": {"n": i}} for i in range(n)]


class HangDoiRieng(unittest.TestCase):
    """Moi bai chay tren mot CSDL TAM. Bo test khong duoc bom rac vao so cai
    that - loi nay da sap ngay 01/09 (60 dong rac moi lan `b test`)."""

    def setUp(self):
        self._db_cu = SO.DB
        self._tmp = tempfile.mkdtemp()
        SO.DB = Path(self._tmp) / "thu.db"
        SO.khoi_tao() if hasattr(SO, "khoi_tao") else None
        HD._DA_TAO = False

    def tearDown(self):
        SO.DB = self._db_cu
        HD._DA_TAO = False


class Nap(HangDoiRieng):
    def test_nap_roi_dem_duoc(self):
        r = HD.nap(_viec(5), "noi_sinh")
        self.assertEqual(r["them"], 5)
        self.assertEqual(r["da_co"], 0)
        self.assertEqual(HD.trang_thai()["tong"]["CHO"], 5)

    def test_IDEMPOTENT_nap_lai_khong_sinh_ban_trung(self):
        """Bo sinh noi sinh de ra hang nghin viec moi luot - khong the phinh."""
        HD.nap(_viec(5), "noi_sinh")
        r = HD.nap(_viec(5), "noi_sinh")
        self.assertEqual(r["them"], 0)
        self.assertEqual(r["da_co"], 5)
        self.assertEqual(HD.trang_thai()["tong"]["CHO"], 5)

    def test_van_tay_khong_phu_thuoc_thu_tu_khoa(self):
        a = HD.van_tay("x", "US500CASH", "H4", "t", {"a": 1, "b": 2})
        b = HD.van_tay("x", "US500CASH", "H4", "t", {"b": 2, "a": 1})
        self.assertEqual(a, b)

    def test_nguon_khac_nhau_la_viec_khac_nhau(self):
        HD.nap(_viec(3), "noi_sinh")
        r = HD.nap(_viec(3), "ngoai_sinh")
        self.assertEqual(r["them"], 3)

    def test_uu_tien_mac_dinh_theo_nguon(self):
        self.assertLess(HD.UU_TIEN["ngoai_sinh"], HD.UU_TIEN["noi_sinh"])
        self.assertLess(HD.UU_TIEN["he_da_pass"], HD.UU_TIEN["ngoai_sinh"])


class NhanViec(HangDoiRieng):
    def test_NGOAI_SINH_duoc_lam_TRUOC_noi_sinh(self):
        """Yeu cau truc tiep cua chu du an."""
        HD.nap(_viec(3), "noi_sinh")
        HD.nap(_viec(3, template="sma_cheo"), "ngoai_sinh")
        v = HD.nhan_viec("w1", 3)
        self.assertEqual([x["nguon"] for x in v], ["ngoai_sinh"] * 3)

    def test_FIFO_trong_cung_muc_uu_tien(self):
        HD.nap(_viec(4), "noi_sinh")
        a = HD.nhan_viec("w1", 2)
        b = HD.nhan_viec("w2", 2)
        self.assertLess(a[-1]["id"], b[0]["id"])

    def test_hai_worker_KHONG_gianh_trung_viec(self):
        HD.nap(_viec(10), "noi_sinh")
        a = {x["id"] for x in HD.nhan_viec("w1", 5)}
        b = {x["id"] for x in HD.nhan_viec("w2", 5)}
        self.assertEqual(len(a), 5)
        self.assertEqual(len(b), 5)
        self.assertEqual(a & b, set())

    def test_loc_theo_nguon_de_chay_SONG_SONG(self):
        HD.nap(_viec(3), "noi_sinh")
        HD.nap(_viec(3, template="sma_cheo"), "ngoai_sinh")
        v = HD.nhan_viec("w_noi", 3, nguon="noi_sinh")
        self.assertEqual([x["nguon"] for x in v], ["noi_sinh"] * 3)

    def test_het_viec_thi_tra_rong_chu_khong_treo(self):
        self.assertEqual(HD.nhan_viec("w1", 5), [])

    def test_tham_so_tra_ve_la_dict_khong_phai_chuoi(self):
        HD.nap(_viec(1), "noi_sinh")
        v = HD.nhan_viec("w1", 1)
        self.assertIsInstance(v[0]["tham_so"], dict)


class ChongNghen(HangDoiRieng):
    def test_LEASE_QUA_HAN_tu_tra_viec_ve_CHO(self):
        """Worker chet giua chung khong duoc lam nghen ca hang doi."""
        HD.nap(_viec(2), "noi_sinh")
        HD.nhan_viec("w_chet", 2, han_lease=0.001)
        time.sleep(0.05)
        self.assertEqual(HD.trang_thai()["lease_qua_han"], 2)
        v = HD.nhan_viec("w_song", 2)
        self.assertEqual(len(v), 2)
        self.assertEqual([x["worker"] for x in v], ["w_song"] * 2)

    def test_don_lease_treo_goi_rieng_duoc(self):
        HD.nap(_viec(2), "noi_sinh")
        HD.nhan_viec("w_chet", 2, han_lease=0.001)
        time.sleep(0.05)
        self.assertEqual(HD.don_lease_treo(), 2)
        self.assertEqual(HD.trang_thai()["tong"].get("CHO"), 2)

    def test_lease_CON_HAN_thi_KHONG_bi_cuop(self):
        """Hieu chuan chieu nguoc: neu cuop bua thi hai worker lam trung."""
        HD.nap(_viec(2), "noi_sinh")
        HD.nhan_viec("w1", 2, han_lease=600)
        self.assertEqual(HD.nhan_viec("w2", 2), [])

    def test_viec_HONG_LIEN_TUC_bi_dua_ra_khoi_vong(self):
        """Dang nghen am tham nhat: mot viec hong quay mai."""
        HD.nap(_viec(1), "noi_sinh")
        for _ in range(HD.TOI_DA_THU):
            v = HD.nhan_viec("w1", 1)
            self.assertEqual(len(v), 1)
            HD.that_bai(v[0]["id"], "loi thu nghiem")
        self.assertEqual(HD.nhan_viec("w1", 1), [])
        self.assertEqual(HD.trang_thai()["tong"].get("HONG"), 1)

    def test_that_bai_lan_dau_thi_van_thu_lai(self):
        HD.nap(_viec(1), "noi_sinh")
        v = HD.nhan_viec("w1", 1)
        HD.that_bai(v[0]["id"], "loi tam thoi")
        self.assertEqual(HD.trang_thai()["tong"].get("CHO"), 1)


class Xong(HangDoiRieng):
    def test_xong_thi_khong_duoc_lay_lai(self):
        HD.nap(_viec(2), "noi_sinh")
        v = HD.nhan_viec("w1", 2)
        for x in v:
            HD.xong(x["id"], {"sharpe": 0.5})
        self.assertEqual(HD.nhan_viec("w2", 2), [])
        self.assertEqual(HD.trang_thai()["tong"].get("XONG"), 2)

    def test_trang_thai_tach_theo_nguon(self):
        HD.nap(_viec(2), "noi_sinh")
        HD.nap(_viec(2, template="sma_cheo"), "ngoai_sinh")
        t = HD.trang_thai()
        self.assertEqual(t["theo_nguon"]["noi_sinh"]["CHO"], 2)
        self.assertEqual(t["theo_nguon"]["ngoai_sinh"]["CHO"], 2)


if __name__ == "__main__":
    unittest.main()
