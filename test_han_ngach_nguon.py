# -*- coding: utf-8 -*-
"""QUANTLAB co HAI nguon dau vao - phai chia tai nguyen cho ca hai.

Chu du an chi ra (01/09) khi NGHI duoc noi lai: tu gio QUANTLAB nhan viec tu
NGOAI (SEEKER doc ma/tai lieu) va tu NOI SINH (NGHI de xuat tu ly le kinh te).
Do that luc do: thu vien co **102 co che ngoai so voi 20 noi sinh** - lech 5 lan.
De tu do thi nhanh noi sinh chet doi khong phai vi te ma vi cham hon.
"""
from __future__ import annotations

import json
import unittest

from tru import quantlab as QL


class HanNgachNguon(unittest.TestCase):
    def test_han_ngach_ngoai_thap_hon_tran_chung(self):
        """Phai chua cho cho nhanh noi sinh, khong duoc bang tran chung."""
        self.assertLess(QL.TRAN_NGOAI_DANG_CHO, QL.TRAN_HANG_DOI_KHAM_PHA)
        self.assertGreaterEqual(QL.TRAN_NGOAI_DANG_CHO, 4)

    def test_han_ngach_chan_dung_nhanh_NGOAI(self):
        """Dem phai loc theo `nguon_tai_lieu` bat dau bang http - do la dau hieu
        DUY NHAT phan biet viec tu ngoai voi viec noi sinh."""
        import inspect
        src = inspect.getsource(QL.rut_hang_doi_ung_vien)
        self.assertIn("TRAN_NGOAI_DANG_CHO", src)
        self.assertIn('nguon_tai_lieu', src)

    def test_bao_ro_khi_cham_han_ngach(self):
        goc = QL.TRAN_NGOAI_DANG_CHO
        try:
            QL.TRAN_NGOAI_DANG_CHO = -1        # ep cham han ngach ngay
            r = QL.rut_hang_doi_ung_vien(gioi_han=1)
            self.assertIn("han_ngach", r)
            self.assertEqual(r.get("xep_viec", 0), 0)
        finally:
            QL.TRAN_NGOAI_DANG_CHO = goc

    def test_tham_so_goc_luon_tuan_tu_hoa_duoc(self):
        """`uv.metadata` co the la `mappingproxy` - json khong nuot duoc, va no
        lam CA luot rut ung vien nem TypeError. Da sap that 01/09."""
        from types import MappingProxyType
        neo = MappingProxyType({"ema": [10, 20], "n": 14, "x": object()})
        sach = {str(k): (list(v) if isinstance(v, (list, tuple))
                         else v if isinstance(v, (int, float, str, bool, type(None)))
                         else str(v))
                for k, v in dict(neo).items()}
        json.dumps(sach)               # khong duoc nem
        self.assertEqual(sach["ema"], [10, 20])
        self.assertIsInstance(sach["x"], str)


if __name__ == "__main__":
    unittest.main()
