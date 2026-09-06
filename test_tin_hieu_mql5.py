# -*- coding: utf-8 -*-
"""Bai kiem cho `nhan/tin_hieu_mql5.py` - do nguoc phong cach tu tai khoan cong khai.

Cai dat nhat o module nay da duoc chinh no ghi lai: **thu tu mang trong trang
KHONG co dinh**. Ban dau (04/09) code lay `mang[0]` la growth va `mang[3]` la
muc tai - dung tren mot signal, sai tren nhieu signal khac, va no o cai thu ba
khi quet 288 signal. Nen `phan_loai_mang` phai nhan dang theo **HINH DANG**.

Bai kiem duoi day dung dung cach do de kiem: dao thu tu cac mang trong trang
roi doi ket qua khong doi. Neu ai do sau nay "toi uu" bang cach quay ve lay
theo vi tri, bai kiem nay do ngay.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import tin_hieu_mql5 as TH        # noqa: E402

MOC = 1_700_000_000


def _mang_von(n=30):
    """(timestamp, balance, equity) - bo BA so, so dau > 1e9."""
    ra = []
    for i in range(n):
        ra += [MOC + i * 86400, 1000.0 + i, 990.0 + i]
    return ra


def _mang_tai(n=30):
    """(timestamp, muc_tai) - bo HAI so, gia tri sau trong [0, 1]."""
    ra = []
    for i in range(n):
        ra += [MOC + i * 86400, round(0.05 + 0.01 * (i % 5), 3)]
    return ra


def _mang_growth(n=30):
    """(so lenh, %) - so dau 0,2,4..., gia tri dau = 0."""
    ra = []
    for i in range(n):
        ra += [i * 2, round(i * 1.5, 2)]
    return ra


def _mang_balance(n=30):
    """Nhu growth nhung gia tri dau KHAC 0 -> la duong tien, khong phai %."""
    ra = []
    for i in range(n):
        ra += [i * 2, 1000.0 + i * 3]
    return ra


def _trang(*mang) -> str:
    return "<html>" + "".join("var x=[%s];" % ",".join(str(x) for x in m)
                              for m in mang) + "</html>"


class NhanDangMangTheoHinhDang(unittest.TestCase):

    def test_nhan_du_bon_dang(self):
        r = TH.phan_loai_mang(_trang(_mang_von(), _mang_tai(),
                                     _mang_growth(), _mang_balance()))
        for k in ("von", "tai", "growth", "balance"):
            self.assertIn(k, r, f"khong nhan ra mang '{k}'")
        self.assertEqual(r["von"].shape[1], 3)
        self.assertEqual(r["tai"].shape[1], 2)

    def test_dao_thu_tu_khong_doi_ket_qua(self):
        """Day la ca loi that ngay 04/09. Xem docstring dau file."""
        a = TH.phan_loai_mang(_trang(_mang_von(), _mang_tai(),
                                     _mang_growth(), _mang_balance()))
        b = TH.phan_loai_mang(_trang(_mang_balance(), _mang_growth(),
                                     _mang_tai(), _mang_von()))
        self.assertEqual(sorted(a), sorted(b))
        for k in a:
            self.assertTrue(np.allclose(a[k], b[k]),
                            f"mang '{k}' doi khi dao thu tu trong trang")

    def test_thieu_mang_khong_no(self):
        """Trang chi co growth: phai tra dung mot khoa, khong duoc nem."""
        r = TH.phan_loai_mang(_trang(_mang_growth()))
        self.assertEqual(set(r), {"growth"})

    def test_trang_rong(self):
        self.assertEqual(TH.phan_loai_mang(""), {})
        self.assertEqual(TH.phan_loai_mang(None), {})

    def test_growth_va_balance_khac_nhau_o_gia_tri_dau(self):
        """Chi chuoi `growth` moi tinh duoc hieu suat - lay nham `balance` la
        lay mot chuoi KHAC DON VI (tien, khong phai %)."""
        g = TH.phan_loai_mang(_trang(_mang_growth()))
        b = TH.phan_loai_mang(_trang(_mang_balance()))
        self.assertIn("growth", g)
        self.assertIn("balance", b)
        self.assertNotIn("balance", g)
        self.assertNotIn("growth", b)


class DuongTai(unittest.TestCase):

    def test_doc_duoc_cap_thoi_gian_va_muc_tai(self):
        html = _trang(_mang_tai(30))
        cap = TH.duong_tai(html)
        self.assertEqual(len(cap), 30)
        self.assertEqual(cap[0][0], MOC)
        self.assertGreater(cap[0][1], 0)

    def test_trang_khong_co_chuoi_tra_rong(self):
        self.assertEqual(TH.duong_tai("<html>khong co gi</html>"), [])
        self.assertEqual(TH.duong_tai(""), [])


class HoSoPhongCach(unittest.TestCase):

    def test_qua_ngan_thi_noi_ro_la_qua_ngan(self):
        r = TH.ho_so_phong_cach([(MOC, 0.1)] * 5)
        self.assertEqual(r.get("du_lieu"), "qua ngan")

    def test_chuoi_du_dai_tra_ho_so(self):
        cap = [(MOC + i * 3600, 0.1 if i % 10 else 0.0) for i in range(200)]
        r = TH.ho_so_phong_cach(cap)
        self.assertNotEqual(r.get("du_lieu"), "qua ngan")
        self.assertIsInstance(r, dict)
        self.assertTrue(r, "ho so rong tren chuoi du dai")


if __name__ == "__main__":
    unittest.main()
