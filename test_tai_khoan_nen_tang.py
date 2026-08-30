# -*- coding: utf-8 -*-
"""TAI KHOAN NEN TANG — trang KIEM phai la trang DOI DANG NHAP.

Ca ngay 30/08 lap lai mot canh: mot duong thu thap khong chay, va sau vai vong
do dac moi lo ra nguyen nhan la **chua dang nhap** chu khong phai loi ma.

Nang nhat: `auto_follow` bao 8/8 tac gia TradingView da follow, that ra 0/8 —
vi TradingView chua dang nhap. Va khi toi viet bo kiem nay, **ban dau no cung
bao nham**: `kiem` cua tradingview tro toi mot trang HO SO CONG KHAI, ma trang
do doc duoc ca khi chua dang nhap.

Bai hoc lap lai lan thu ba trong ngay: **mot phep kiem chi bao THANH CONG thi
khong phan biet duoc voi mot phep kiem hong.** Trang `kiem` phai la trang doi
dang nhap, de "chua dang nhap" tao ra mot tin hieu QUAN SAT DUOC (chuyen huong).
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import tai_khoan_nen_tang as TK   # noqa: E402


class MoiNenTangKhaiDuThongTin(unittest.TestCase):

    def test_du_khoa_bat_buoc(self):
        for ten, c in TK.NEN_TANG.items():
            for k in ("loai", "kiem", "dang_ky", "dau_hieu_chua", "vi_sao"):
                self.assertIn(k, c, f"'{ten}' thieu khoa '{k}'")

    def test_moi_nen_tang_noi_ro_no_MO_KHOA_cai_gi(self):
        """Khong co ly do cu the thi khong biet co dang bo cong ra lam khong."""
        for ten, c in TK.NEN_TANG.items():
            self.assertGreater(len(c["vi_sao"]), 25,
                               f"'{ten}' khong noi ro no mo khoa cai gi")

    def test_loai_chi_la_mot_trong_hai(self):
        for ten, c in TK.NEN_TANG.items():
            self.assertIn(c["loai"], ("tu_dong", "mot_lan_tay"), ten)

    def test_dau_hieu_chua_la_regex_hop_le(self):
        """Ban dau bai nay chi goi `re.compile` roi khong khang dinh gi - cong
        hien phap bat duoc (lan thu ba trong phien)."""
        for ten, c in TK.NEN_TANG.items():
            r = re.compile(c["dau_hieu_chua"], re.I)
            self.assertIsNotNone(r, ten)
            # Phai thuc su BAT duoc mot trang dang nhap dien hinh.
            self.assertTrue(
                r.search("Please Log in or Sign in to continue"),
                f"dau hieu cua '{ten}' khong bat duoc trang dang nhap dien hinh")
            # Va KHONG duoc bat mot trang binh thuong.
            self.assertIsNone(
                r.search("Bieu do gia va danh sach script cua tac gia"),
                f"dau hieu cua '{ten}' bat nham trang binh thuong")


class TrangKiemPhaiDOIDANGNHAP(unittest.TestCase):
    """Chot chinh cua file nay."""

    def test_tradingview_khong_dung_trang_ho_so_cong_khai(self):
        u = TK.NEN_TANG["tradingview"]["kiem"]
        self.assertNotRegex(
            u, r"/u/[A-Za-z0-9_]+",
            "kiem bang HO SO CONG KHAI cua nguoi khac - trang do doc duoc ca khi "
            "chua dang nhap, nen phep kiem se bao 'da dang nhap' sai. Dung "
            "tradingview.com/u/ (ho so CUA MINH), no chuyen sang /accounts/signin/")

    def test_khong_nen_tang_nao_kiem_bang_trang_cong_khai_cua_nguoi_khac(self):
        for ten, c in TK.NEN_TANG.items():
            self.assertNotRegex(
                c["kiem"], r"/(u|user|users)/[A-Za-z0-9_]{3,}/?$",
                f"'{ten}' kiem bang ho so cong khai cua mot nguoi cu the")


class DocTrangThaiKhongDoanBua(unittest.TestCase):

    class _Pg:
        def __init__(self, url, van): self.url, self._van = url, van
        def goto(self, *a, **k): pass
        def wait_for_timeout(self, *a): pass
        def inner_text(self, _): return self._van

    def test_bi_chuyen_sang_trang_dang_nhap_thi_bao_CHUA(self):
        pg = self._Pg("https://www.tradingview.com/accounts/signin/", "Sign in")
        r = TK.kiem_mot(pg, "tradingview")
        self.assertIs(r["da_dang_nhap"], False)

    def test_trang_day_du_khong_co_dau_hieu_thi_bao_DA(self):
        pg = self._Pg("https://www.tradingview.com/u/", "noi dung ho so " * 500)
        self.assertIs(TK.kiem_mot(pg, "tradingview")["da_dang_nhap"], True)

    def test_trang_RONG_thi_bao_KHONG_RO_chu_khong_doan(self):
        """Khong doc duoc != chua dang nhap. Cung nguyen tac voi do_tai_nguyen."""
        pg = self._Pg("https://www.tradingview.com/u/", "abc")
        self.assertIsNone(TK.kiem_mot(pg, "tradingview")["da_dang_nhap"])

    def test_loi_mo_trang_thi_bao_KHONG_RO(self):
        class Vo(self._Pg.__mro__[0]):
            def goto(self, *a, **k): raise RuntimeError("mang rot")
        pg = Vo("x", "")
        r = TK.kiem_mot(pg, "tradingview")
        self.assertIsNone(r["da_dang_nhap"])
        self.assertIn("loi", r)


if __name__ == "__main__":
    unittest.main()
