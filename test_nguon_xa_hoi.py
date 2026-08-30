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

    def test_tieu_de_NGAN_van_giu_khi_URL_da_qua_bo_loc(self):
        """Doi hanh vi co y 30/08 — bo loc URL moi la chot chat luong.

        Ban dau bai nay khang dinh nguoc lai (tieu de ngan thi bo), va chinh
        no che mat mot loi that: trang tim kiem cua X co **65 link bai hop le**,
        nhung link bai cua X boc mot dau thoi gian ("2h", "1d") lam chu, nen
        `len(tt) < 12` giet sach — thu ve 3 bai thay vi 65.

        Khi `loc_lien_ket` da chung minh do la URL cua mot BAI THAT thi khong
        duoc siet them bang do dai chu. Tieu de ngan duoc bo sung dinh danh lay
        tu duong dan.
        """
        c = S.NGUON_TRINH_DUYET["x"]
        d = self._trang([("2h", "https://x.com/a/status/1"),
                         ("1d", "https://x.com/b/status/2")])
        ra = S._duyet_tai_lieu(d, "x", c)
        self.assertEqual(len(ra), 2, "link bai co chu ngan van bi bo")
        for m in ra:
            self.assertIn("status/", m["tieu_de"],
                          "tieu de ngan ma khong duoc bo sung dinh danh")

    def test_the_a_KHONG_CO_CHU_thi_van_bo(self):
        """Noi long khong co nghia la nhan tat ca: the rong van la the rong."""
        c = S.NGUON_TRINH_DUYET["x"]
        d = self._trang([("", "https://x.com/a/status/1")])
        self.assertEqual(S._duyet_tai_lieu(d, "x", c), [])

    def test_nguon_KHONG_co_loc_URL_van_doi_tieu_de_dai(self):
        """Chi noi long o nhung nguon da co bo loc duong dan."""
        c = dict(S.NGUON_TRINH_DUYET["x"])
        c.pop("loc_lien_ket", None)
        d = self._trang([("2h", "https://x.com/a/status/1")])
        self.assertEqual(S._duyet_tai_lieu(d, "x", c), [],
                         "khong co loc URL ma van nhan tieu de 2 ky tu")

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

class ChuanHoaLienKetTruocKhiKhuTrung(unittest.TestCase):
    """Mot so tai lieu bi thoi phong khong chi lam ban so lieu.

    Do that 30/08/2026: mot vong quet YouTube ghi **75 "bai"**, nhung phan lon
    la link MOC THOI GIAN trong CUNG MOT video (`...v=0rzXU-BlKCg&t=561s`,
    `&t=434s`, `&t=379s`, `&t=240s`...) - tuc muc luc chuong, khong phai 75
    video. Khu trung theo URL THO nen chung deu lot.

    Sau khi chuan hoa va don so: **92 ban ghi -> 42 URL that su khac nhau**,
    xoa 50 ban trung.

    Hau qua neu de nguyen: `doc_toan_van` tai cung mot trang chuc lan, va ty le
    "bai moi tren moi luot quet" - con so EVO dung de biet nguon con song hay
    da can - tro nen vo nghia.
    """

    def test_moc_thoi_gian_youtube_gop_ve_MOT_video(self):
        u = ["https://www.youtube.com/watch?v=0rzXU-BlKCg&t=561s&pp=0gcJ",
             "https://www.youtube.com/watch?v=0rzXU-BlKCg&t=26s",
             "https://www.youtube.com/watch?v=0rzXU-BlKCg",
             "https://youtu.be/0rzXU-BlKCg?si=abc"]
        self.assertEqual(len({S._chuan_hoa_lien_ket(x) for x in u}), 1,
                         "bon link cua CUNG mot video van dem thanh nhieu bai")

    def test_hai_video_KHAC_nhau_khong_bi_gop(self):
        a = S._chuan_hoa_lien_ket("https://www.youtube.com/watch?v=AAAAAAAAAAA&t=5s")
        b = S._chuan_hoa_lien_ket("https://www.youtube.com/watch?v=BBBBBBBBBBB&t=5s")
        self.assertNotEqual(a, b, "gop nham hai video khac nhau")

    def test_bo_tham_so_theo_doi_nhung_giu_dinh_danh_bai(self):
        u = S._chuan_hoa_lien_ket(
            "https://x.com/a/status/123?utm_source=x&fbclid=zz")
        self.assertEqual(u, "https://x.com/a/status/123")

    def test_bo_neo_trang(self):
        self.assertEqual(
            S._chuan_hoa_lien_ket("https://www.reddit.com/r/x/hot/#main-content"),
            "https://www.reddit.com/r/x/hot/")

    def test_url_la_khong_lam_vo(self):
        """Truoc day bai nay chi goi ham roi khong khang dinh gi - cong hien
        phap bat duoc dung no (lan thu hai trong phien)."""
        for u in ("", "khong-phai-url", "https://", "https://a.com"):
            ra = S._chuan_hoa_lien_ket(u)
            self.assertIsInstance(ra, str, f"'{u}' khong tra ve chuoi")
            self.assertLessEqual(len(ra), len(u) + 40)

    def test_boc_trang_khong_dem_trung_moc_thoi_gian(self):
        c = S.NGUON_TRINH_DUYET["youtube"]
        d = {"url": "https://www.youtube.com/results?search_query=a",
             "title": "tim kiem", "text": "x" * 800, "links": [],
             "anchor": [("Bai giang ve mean reversion phan 1",
                         "https://www.youtube.com/watch?v=ZZZZZZZZZZZ&t=10s"),
                        ("Bai giang ve mean reversion phan 2",
                         "https://www.youtube.com/watch?v=ZZZZZZZZZZZ&t=99s"),
                        ("Mot video hoan toan khac ve backtest",
                         "https://www.youtube.com/watch?v=YYYYYYYYYYY")]}
        ra = S._duyet_tai_lieu(d, "youtube", c)
        self.assertEqual(len(ra), 2,
                         f"boc ra {len(ra)} bai - hai moc cua cung mot video "
                         "van bi dem thanh hai")


if __name__ == "__main__":
    unittest.main()
