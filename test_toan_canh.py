# -*- coding: utf-8 -*-
"""TOAN CANH — mot man hinh tra loi "he dang o dau", va no phai KHONG BAO GIO VO.

Vi sao can bai kiem: day la thu dau tien nguoi doc khi mo phien. Neu no vo vi
mot bang chua ton tai hay mot khoa doi ten, thi cai hong dau tien nguoi thay
lai la chinh cai man hinh bao trang thai - va do la kieu hong lam mat long tin
vao moi so lieu con lai.

Nen no phai chay duoc ca khi so cai TRONG, ca khi khong co anh chup be mat, va
ca khi trinh duyet dang tat.
"""
from __future__ import annotations

import io
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

import toan_canh as TC   # noqa: E402


class ChayDuocTrenSoTHAT(unittest.TestCase):

    def test_in_ra_du_bon_muc_va_khong_nem_ngoai_le(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ma = TC.main()
        ra = buf.getvalue()
        self.assertEqual(ma, 0)
        for muc in ("DAU VAO", "KHO CO CHE", "TANG KHAM PHA", "CONG / SO CAI",
                    "TAI NGUYEN"):
            self.assertIn(muc, ra, f"thieu muc '{muc}'")

    def test_co_bao_trang_thai_DUNG_LAI(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            TC.main()
        self.assertIn("DUNG_LAI", buf.getvalue())


class KhongVoKhiThIEU(unittest.TestCase):
    """Thieu bang, thieu anh chup, trinh duyet tat - deu khong duoc lam vo."""

    def test_so_cai_TRONG_van_chay(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "rong.db"
            sqlite3.connect(db).close()
            goc = TC._cn
            TC._cn = lambda: sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    ma = TC.main()
                self.assertEqual(ma, 0)
                self.assertIn("DAU VAO", buf.getvalue())
            finally:
                TC._cn = goc

    def test_mot_tra_ve_mac_dinh_khi_bang_khong_ton_tai(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "rong.db"
            sqlite3.connect(db).close()
            cn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            self.assertEqual(TC._mot(cn, "SELECT COUNT(*) FROM bang_khong_co"), 0)
            self.assertEqual(
                TC._mot(cn, "SELECT COUNT(*) FROM bang_khong_co", mac_dinh=-1), -1)
            cn.close()


if __name__ == "__main__":
    unittest.main()
