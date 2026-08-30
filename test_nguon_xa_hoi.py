# -*- coding: utf-8 -*-
"""NGUON XA HOI — trang tim kiem KHONG phai noi dung.

Do that 30/08/2026: bon nguon x / tiktok / facebook / youtube deu khai
`kieu="tu_khoa"`, tuc mo trang tim kiem roi LUU NGUYEN VAN BAN TRANG DO lam mot
bai. Ket qua: moi nguon sinh dung 3 "bai", va ca ba deu la **900 ky tu van ban
dieu huong** - khong mot bai viet nao.

Voi Reddit hay MQL5 thi cach do con tam duoc vi trang liet ke co san tieu de.
Voi Facebook/TikTok thi trang tim kiem gan nhu rong: noi dung nam sau khi bam
vao tung bai.

Nen bon nguon do chuyen sang `tu_khoa_lien_ket`: dung MAU + tu khoa de mo trang
tim kiem (nhu `tu_khoa`), roi BOC LIEN KET (nhu `trang`), va loc lay dung duong
dan cua BAI THAT bang `loc_lien_ket`.

Bo test khoa hai thu: bo loc phai nhan dung dang URL cua tung nen tang, va
nhanh dung MAU phai bao trum ca hai kieu `tu_khoa*` (quen cho nay thi
`quet_trinh_duyet` nem `KeyError: 'trang'` - da xay ra that khi them kieu moi).
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from tru import seeker as S   # noqa: E402

XA_HOI = ("x", "tiktok", "facebook", "youtube")


class BonNguonXaHoiDungKieuMoi(unittest.TestCase):

    def test_deu_la_tu_khoa_lien_ket(self):
        for n in XA_HOI:
            self.assertEqual(S.NGUON_TRINH_DUYET[n]["kieu"], "tu_khoa_lien_ket",
                             f"'{n}' con luu trang tim kiem thay vi vao tung bai")

    def test_deu_co_bo_loc_duong_dan(self):
        for n in XA_HOI:
            self.assertTrue(S.NGUON_TRINH_DUYET[n].get("loc_lien_ket"),
                            f"'{n}' khong loc -> nhat ca link dang nhap/cai dat")

    def test_bo_loc_nhan_dung_URL_BAI_THAT(self):
        that = {
            "x": "https://x.com/quantguy/status/1234567890",
            "tiktok": "https://www.tiktok.com/@trader/video/7412345678901234567",
            "facebook": "https://www.facebook.com/groups/algo/posts/998877/",
            "youtube": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        }
        for n, u in that.items():
            self.assertTrue(re.search(S.NGUON_TRINH_DUYET[n]["loc_lien_ket"], u),
                            f"bo loc cua '{n}' bo sot URL bai that: {u}")

    def test_bo_loc_LOAI_link_dieu_huong(self):
        rac = {
            "x": ["https://x.com/settings/account", "https://x.com/i/flow/login",
                  "https://help.x.com/en/rules"],
            "tiktok": ["https://www.tiktok.com/login",
                       "https://www.tiktok.com/legal/privacy-policy"],
            "facebook": ["https://www.facebook.com/privacy/policy/",
                         "https://www.facebook.com/login.php"],
            "youtube": ["https://www.youtube.com/about/",
                        "https://www.youtube.com/feed/trending"],
        }
        for n, ds in rac.items():
            for u in ds:
                self.assertIsNone(
                    re.search(S.NGUON_TRINH_DUYET[n]["loc_lien_ket"], u),
                    f"bo loc cua '{n}' nhan nham link dieu huong: {u}")


class BocTrangKetQua(unittest.TestCase):

    def _trang(self, anchor):
        return {"url": "https://x.com/search?q=a", "title": "tim kiem",
                "text": "x" * 800, "anchor": anchor, "links": []}

    def test_boc_duoc_bai_that_va_bo_link_rac(self):
        c = S.NGUON_TRINH_DUYET["x"]
        d = self._trang([
            ("Mot bai ve mean reversion tren SP500", "https://x.com/a/status/1"),
            ("Dang nhap", "https://x.com/i/flow/login"),
            ("Bai thu hai ve backtest overfitting", "https://x.com/b/status/2"),
        ])
        ra = S._duyet_tai_lieu(d, "x", c, tu_khoa="https://x.com/search?q=a")
        self.assertEqual(len(ra), 2, f"boc ra {len(ra)} bai thay vi 2")
        for m in ra:
            self.assertIn("/status/", m["url"])

    def test_tieu_de_qua_ngan_thi_bo(self):
        c = S.NGUON_TRINH_DUYET["x"]
        d = self._trang([("ok", "https://x.com/a/status/1")])
        self.assertEqual(S._duyet_tai_lieu(d, "x", c), [])

    def test_khong_trung_URL(self):
        c = S.NGUON_TRINH_DUYET["x"]
        d = self._trang([("Mot bai du dai de duoc nhan", "https://x.com/a/status/1")] * 4)
        self.assertEqual(len(S._duyet_tai_lieu(d, "x", c)), 1)


class NhanhDungMauBaoTrumCaHaiKieu(unittest.TestCase):
    """Quen cho nay thi `quet_trinh_duyet` nem KeyError: 'trang'. Da xay ra that."""

    def test_moi_nguon_kieu_tu_khoa_deu_co_MAU(self):
        for ten, c in S.NGUON_TRINH_DUYET.items():
            if str(c.get("kieu", "")).startswith("tu_khoa"):
                self.assertIn("mau", c, f"'{ten}' dung tu khoa nhung khong co mau")
                self.assertIn("{k}", c["mau"], f"'{ten}' co mau nhung khong co cho dien tu khoa")

    def test_moi_nguon_kieu_trang_deu_co_DANH_SACH_TRANG(self):
        for ten, c in S.NGUON_TRINH_DUYET.items():
            if c.get("kieu") == "trang":
                self.assertTrue(c.get("trang"), f"'{ten}' kieu trang nhung khong co trang nao")


if __name__ == "__main__":
    unittest.main()
