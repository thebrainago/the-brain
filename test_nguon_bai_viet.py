# -*- coding: utf-8 -*-
"""NGUON VAN XUOI qua RSS/Atom - bo doc feed.

Test nay KHONG cham mang. No khoa hai thu de nhat hong ma khong ai thay:

1. **Uu tien `content:encoded` hon `description`.** Neu doc nham, moi bai chi
   con doan mo dau ~200 ky tu va bo doc hieu se khong bao gio thay mot cau luat
   day du - nhung so lieu van bao "lay ve 12 bai", nhin nhu dang chay tot.
2. **Doc duoc CA HAI ho: RSS 2.0 va Atom.** Trong 16 feed do that 23/08 co ca
   hai (blogspot tra Atom, WordPress tra RSS). Mot bo doc chi hieu RSS se lam
   qoppac + mrzepczynski (25 muc/feed, hai nguon day chu nhat) im lang tra 0.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import nguon_bai_viet as NBV

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
 <title>Blog</title>
 <item>
  <title>An RSI strategy</title>
  <link>https://vi.du/rsi-strategy</link>
  <description>Just the teaser paragraph.</description>
  <content:encoded><![CDATA[<p>Buy when the 2-period RSI is below 10.</p>
  <p>Exit after 5 days.</p>]]></content:encoded>
 </item>
 <item>
  <title>No full text here</title>
  <link>https://vi.du/tom-tat</link>
  <description>Only a summary of the post.</description>
 </item>
</channel></rss>"""

ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <title>Blogspot style</title>
 <entry>
  <title>Trend following notes</title>
  <link rel="alternate" type="text/html" href="https://vi.du/trend"/>
  <summary>short</summary>
  <content type="html">&lt;p&gt;Go long when the close is above the 200-day moving average.&lt;/p&gt;</content>
 </entry>
</feed>"""


class DocFeed(unittest.TestCase):
    def test_rss_lay_toan_van_chu_khong_lay_tom_tat(self):
        muc = NBV.doc_feed(RSS)
        self.assertEqual(len(muc), 2)
        a = muc[0]
        self.assertEqual(a["tieu_de"], "An RSI strategy")
        self.assertEqual(a["url"], "https://vi.du/rsi-strategy")
        self.assertTrue(a["day_du"])
        self.assertIn("2-period RSI", a["van_ban"])
        self.assertNotIn("teaser", a["van_ban"])

    def test_khong_co_toan_van_thi_danh_dau_de_doc_them(self):
        b = NBV.doc_feed(RSS)[1]
        self.assertFalse(b["day_du"])
        self.assertIn("summary", b["van_ban"])

    def test_atom(self):
        muc = NBV.doc_feed(ATOM)
        self.assertEqual(len(muc), 1)
        self.assertEqual(muc[0]["url"], "https://vi.du/trend")
        self.assertIn("200-day moving average", muc[0]["van_ban"])

    def test_xml_hong_khong_nem_ngoai_le(self):
        """Feed hong la chuyen binh thuong (WordPress tra trang HTML thay vi
        XML - da gap that o quantstrattrader). Phai tra rong, khong duoc lam
        chet ca luot cua SEEKER."""
        self.assertEqual(NBV.doc_feed("<html>khong phai feed</html>"), [])
        self.assertEqual(NBV.doc_feed(""), [])


class NoiVoiBoDocHieu(unittest.TestCase):
    def test_toan_van_tu_feed_doc_ra_duoc_co_che(self):
        """Bai kiem NOI: feed -> van ban -> spec. Neu khong co bai kiem nay thi
        hai module dung rieng deu 'dat' ma duong noi giua chung co the dut."""
        from nhan import doc_hieu as DH
        vb = NBV.doc_feed(RSS)[0]["van_ban"]
        ket = DH.doc_bai(vb + " " + "Filler text to pass the length gate. " * 8,
                         "An RSI strategy", "https://vi.du/rsi-strategy")
        self.assertTrue(ket)
        s = ket[0]["spec"]
        self.assertEqual(s["vao"][0]["trai"], {"chi_bao": "rsi", "n": 2})
        self.assertEqual(s["giu"], 5)


class CauHinh(unittest.TestCase):
    def test_moi_feed_khai_bao_du_truong(self):
        for ma, c in NBV.FEEDS.items():
            self.assertTrue(c.get("url", "").startswith("http"), ma)
            self.assertIn(c.get("hang"), ("A", "B", "C"), ma)
            self.assertIn("ghi_chu", c, ma)

    def test_feed_hong_duoc_ghi_lai_lam_mon_no(self):
        """Nguon hong phai nam trong danh sach co ly do, khong duoc bien mat -
        neu khong thi lan sau lai co nguoi them lai chinh no."""
        self.assertTrue(NBV.FEED_HONG)
        for ma, ly_do in NBV.FEED_HONG.items():
            self.assertNotIn(ma, NBV.FEEDS, ma)
            self.assertGreater(len(ly_do), 5, ma)


class KhongBiTruKhacTatNham(unittest.TestCase):
    """SEEKER tat moi dong `nguon` khong nam trong bo cua no. Neu no khong biet
    den feed cua module nay thi ca tang bai viet van xuoi im lang sau MOT luot -
    khong bao loi, va "0 bai moi" nhin y het "chua den han".

    Da sap that 23/08: ca 27 feed bi chuyen `TAT` ngay o luot SEEKER ke tiep.
    """

    def test_feed_van_BAT_sau_khi_seeker_dang_ky_nguon(self):
        """Chay THAT `dang_ky_nguon()` roi doc lai trang thai. Kiem bang cach
        doc lai bo `tat_ca` la kiem chinh minh - phai do KET QUA tren so."""
        from nhan import so as SO
        from tru import seeker as SK
        ma = "rss_zzz_bai_kiem"
        try:
            SO.chay("INSERT OR REPLACE INTO nguon(ma,ten,loai,url,chu_ky_giay,"
                    "lan_cuoi,trang_thai) VALUES(?,?,?,?,?,0,'BAT')",
                    ma, "feed bai kiem", "blog", "https://vi.du/feed", 21600)
            SK.dang_ky_nguon()
            r = SO.mot("SELECT trang_thai FROM nguon WHERE ma=?", ma)
            self.assertIsNotNone(r)
            self.assertEqual(r["trang_thai"], "BAT",
                             "SEEKER tat nham nguon cua module khac")
        finally:
            SO.chay("DELETE FROM nguon WHERE ma=?", ma)

    def test_van_con_tat_duoc_nguon_da_go(self):
        """Bai kiem DOI XUNG: mien tru khong duoc rong den muc khong tat duoc
        gi nua - nguon da go khoi bo van phai bi tat."""
        from nhan import so as SO
        from tru import seeker as SK
        ma = "nguon_da_go_bai_kiem"
        try:
            SO.chay("INSERT OR REPLACE INTO nguon(ma,ten,loai,url,chu_ky_giay,"
                    "lan_cuoi,trang_thai) VALUES(?,?,?,?,?,0,'BAT')",
                    ma, "nguon da go", "blog", "", 21600)
            SK.dang_ky_nguon()
            r = SO.mot("SELECT trang_thai FROM nguon WHERE ma=?", ma)
            self.assertEqual(r["trang_thai"], "TAT")
        finally:
            SO.chay("DELETE FROM nguon WHERE ma=?", ma)


if __name__ == "__main__":
    unittest.main(verbosity=2)
