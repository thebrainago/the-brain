# -*- coding: utf-8 -*-
"""VUON NGUON + CAU BROWSER: hai lan dau vao, va cai gi quyet dinh chia gio.

Bo test nay khoa BA thu de hong ma khong ai thay:

1. **Chia ngan sach phai co SAN THAM DO.** Neu chia thuan theo suat thi lan
   dang thua bi doi 0 gio vinh vien - va mot he khong bao gio thu lai thi khong
   bao gio biet minh dang sai. San la gia phai tra de con hoc duoc.
2. **Chong trung phai o dung CHO.** `hangukquant.substack.com` va
   `research.hangukquant.com` la CUNG mot nguoi viet; neu khong nhan ra, ta tra
   hai suat ngan sach cho mot nguon. Va tren Telegram moi bai co cung mot url
   kenh, nen chong trung theo url gop 116 bai khac nhau con 23.
3. **Cong cua lan xa hoi phai hieu chuan HAI CHIEU.** Mot cong tu choi tat ca
   cho so lieu y het mot cong hieu chuan tot: ca hai deu bao "0 rac". Nen bay
   phai bi chan VA bai luat that phai lot.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import cau_browser as CB
from nhan import vuon_nguon as VN


class ChiaNganSach(unittest.TestCase):
    def test_tong_bang_ngan_sach(self):
        c = VN.chia_ngan_sach(600)
        self.assertAlmostEqual(sum(c.values()), 600, delta=1.0)

    def test_moi_lan_luon_duoc_san_tham_do(self):
        """Du mot lan dang co suat 0 tuyet doi, no van phai duoc gio de thu lai."""
        c = VN.chia_ngan_sach(600)
        for ten, giay in c.items():
            self.assertGreaterEqual(giay, 600 * VN.SAN_THAM_DO * 0.95, ten)

    def test_khong_lan_nao_nuot_sach(self):
        c = VN.chia_ngan_sach(600)
        for ten, giay in c.items():
            self.assertLessEqual(giay, 600 * VN.TRAN_MOT_LAN * 1.05, ten)

    def test_lan_suat_cao_duoc_nhieu_gio_hon(self):
        """Bai kiem chieu nguoc: san khong duoc lam phang het chenh lech."""
        s = VN.suat_lan()
        c = VN.chia_ngan_sach(600)
        if abs(s["hoc_thuat"]["suat"] - s["xa_hoi"]["suat"]) < 1.0:
            self.skipTest("hai lan dang xap xi nhau, khong kiem duoc chieu nay")
        cao = max(s, key=lambda k: s[k]["suat"])
        thap = min(s, key=lambda k: s[k]["suat"])
        self.assertGreater(c[cao], c[thap])

    def test_bien_mot_lan_suat_0_van_du_ngan_sach(self):
        """Bien: mot lan suat rat cao, lan kia bang 0. Ca hai cham san/tran
        trong CUNG mot vong, khong con lan tu do nao de nhan phan con lai -
        va tong tut xuong 0,90, tuc mat 10% ngan sach ma khong ai thay."""
        import unittest.mock as M
        with M.patch.object(VN, "suat_lan",
                            lambda: {"hoc_thuat": {"suat": 99.0},
                                     "xa_hoi": {"suat": 0.0}}):
            c = VN.chia_ngan_sach(600)
        self.assertAlmostEqual(sum(c.values()), 600, delta=1.0)
        self.assertLessEqual(c["hoc_thuat"], 600 * VN.TRAN_MOT_LAN + 1)
        self.assertGreaterEqual(c["xa_hoi"], 600 * VN.SAN_THAM_DO - 1)

    def test_hai_lan_bang_nhau_thi_chia_deu(self):
        import unittest.mock as M
        with M.patch.object(VN, "suat_lan",
                            lambda: {"hoc_thuat": {"suat": 5.0},
                                     "xa_hoi": {"suat": 5.0}}):
            c = VN.chia_ngan_sach(600)
        self.assertAlmostEqual(c["hoc_thuat"], c["xa_hoi"], delta=1.0)


class ChongTrungNguon(unittest.TestCase):
    def test_cung_nguoi_viet_thi_cung_mot_khoa(self):
        self.assertEqual(VN.khoa_nha_xuat_ban("hangukquant.substack.com"),
                         VN.khoa_nha_xuat_ban("research.hangukquant.com"))

    def test_nen_tang_cho_thue_khong_gop_thanh_mot(self):
        """Neu quy `x.substack.com` ve `substack.com` thi ca Substack thanh MOT
        nguon - moi blog moi tren do se bi coi la da biet."""
        self.assertNotEqual(VN.khoa_nha_xuat_ban("hangukquant.substack.com"),
                            VN.khoa_nha_xuat_ban("quantitativo.substack.com"))

    def test_ten_mien_thuong(self):
        self.assertEqual(VN.khoa_nha_xuat_ban("www.priceactionlab.com"), "priceactionlab")
        self.assertEqual(VN.khoa_nha_xuat_ban("qoppac.blogspot.com"), "qoppac")

    def test_bo_ha_tang(self):
        for m in ("substack-post-media.s3.amazonaws.com", "i0.wp.com",
                  "blogger.googleusercontent.com", "127.0.0.1", "preview.redd.it"):
            self.assertTrue(VN._la_ha_tang(m), m)

    def test_khong_bo_nham_blog_that(self):
        for m in ("financial-hacker.com", "priceactionlab.com", "qoppac.blogspot.com"):
            self.assertFalse(VN._la_ha_tang(m), m)


class VongDoiNguon(unittest.TestCase):
    def test_nguon_moi_vao_dien_THU_chu_khong_vao_thang(self):
        """Khong nguon nao duoc vao thang dien dang tin. Neu vao thang thi mot
        nguon rac se an ngan sach thu thap cho toi khi co nguoi go tay."""
        for ma, c in VN.doc_kho().items():
            if ma.startswith("_"):
                continue
            self.assertIn(c.get("trang_thai"), ("THU", "BAT", "TAT"), ma)

    def test_feed_dang_bat_bo_khoa_he_thong(self):
        """Kho dung chung file voi so ghi nho `_da_thu_ten` - no khong duoc
        lot ra thanh mot 'nguon'."""
        for ma in VN.feed_dang_bat():
            self.assertFalse(ma.startswith("_"), ma)


class CongLanXaHoi(unittest.TestCase):
    """Hieu chuan HAI CHIEU cua cong `cau_browser`."""

    BAI_LUAT = (
        "I have been running this system on SPY for three years and here is the "
        "full description. The strategy is a mean-reversion setup on the daily "
        "timeframe. We buy when the 2-period RSI closes below 10 and the close "
        "is above the 200-day moving average, and we exit when the close crosses "
        "above the 5-day moving average. Position sizing is fixed fractional at "
        "2% risk per trade. In the backtest the win rate was 68% with a maximum "
        "drawdown of 14% and a Sharpe of 0.9. The equity curve is smooth apart "
        "from 2020. I have not traded it live yet, so treat the numbers as "
        "in-sample. Happy to answer questions about the exact indicator settings "
        "or the risk management rules I use on this portfolio."
    )

    def test_bai_luat_that_tren_dien_dan_phai_LOT(self):
        r = CB.xet_bai(self.BAI_LUAT)
        self.assertTrue(r["nhan"], r["ly_do"])

    def test_tin_hieu_le_bi_chan(self):
        """'BUY 4478, SL 4475, TP 4490' la MOT LENH cua mot ngay, khong phai
        mot luat tai lap duoc. Day la dang chiem gan het cac kenh do duoc."""
        bai = ("XAUHQ | GOLD SIGNAL DIRECTION: BUY ENTRY: 4478/82 STOP LOSS: 4475 "
               "TAKE PROFIT: TP1 4490 TP2 4500 TP3 4510. Manage your risk and "
               "follow the plan. Our trading strategy has a great win rate this "
               "week on gold volatility. " * 2)
        self.assertFalse(CB.xet_bai(bai)["nhan"])

    def test_quang_cao_bi_chan(self):
        bai = ("XAUHQ | WEEKEND OFFER 100% FREE VIP $0 CHANNEL. Join now and "
               "get our premium trading strategy signals. DM me for access, "
               "t.me/xauhq. Limited discount for the first 50 members who "
               "sign up today. We have the best win rate on the market. " * 3)
        self.assertFalse(CB.xet_bai(bai)["nhan"])

    def test_bai_ngan_bi_chan(self):
        self.assertFalse(CB.xet_bai("Good morning guys, gold looking bullish today.")["nhan"])

    def test_ban_do_nguyen_trang_bi_chan(self):
        """Bai DUY NHAT lot qua cong o lan chay dau la mot ban do nguyen trang
        tim kiem TradingView. Mat do cau khong bat duoc no (10,83 so voi 12,47
        cua bai that) - phai bat bang chuoi dieu huong."""
        bai = ("Skip to main content Search EN Get started All ideas Videos only "
               "Most recent Most popular Bitcoin trading strategy breakout "
               "momentum volatility indicator portfolio " * 8)
        self.assertTrue(CB.la_dump_trang(bai))
        self.assertFalse(CB.xet_bai(bai)["nhan"])

    def test_bai_that_khong_bi_coi_la_ban_do_trang(self):
        """Bai kiem doi xung: bo loc trang khong duoc an bai viet that, ke ca
        khi bai do tinh co nhac mot chuoi giao dien."""
        self.assertFalse(CB.la_dump_trang(self.BAI_LUAT))


if __name__ == "__main__":
    unittest.main(verbosity=2)


class BoLocHaTangPhaiTHUC_SU_LOC(unittest.TestCase):
    """Do 15/09/2026: `mien_ung_vien` tra 31 ung vien thi 27 la rac.

    Bo loc CO ton tai nhung chi chan theo NHAN con mien va DUOI, nen ba nhom di
    thang qua: cho trong may (`localhost`), ten trong vi du (`example.com`,
    `companyname.net`), va cong cu lap trinh (`get.docker.com`). Mot bo loc lot
    87% la mot bo loc chua chay.
    """

    def test_chan_cho_trong_may_va_ten_vi_du(self):
        for m in ("localhost", "example.com", "www.example.com",
                  "companyname.net", "your-backend-domain", "0.0.0.0"):
            self.assertTrue(VN._la_ha_tang(m), m)

    def test_chan_do_theo_doi_va_cong_cu_lap_trinh(self):
        for m in ("googletagmanager.com", "addtoany.com", "get.docker.com",
                  "download.pytorch.org", "abuseipdb.com", "virustotal.com"):
            self.assertTrue(VN._la_ha_tang(m), m)

    def test_chan_mien_con_ha_tang(self):
        for m in ("no-cache.hubspot.com", "cta-service-cms2.hubspot.com",
                  "cdn-ilaapkf.nitrocdn.com"):
            self.assertTrue(VN._la_ha_tang(m), m)

    def test_NHA_CUNG_CAP_BLOG_khong_phai_ha_tang(self):
        """Chieu nguoc, va no da bat duoc mot lan toi dinh chan ca `.blogspot.com`.

        `qoppac.blogspot.com` la blog cua Rob Carver - mot trong nhung nguon tot
        nhat trong ca kho. Mot mien con mot nguoi viet van la mot nguon.
        """
        for m in ("qoppac.blogspot.com", "financial-hacker.com",
                  "priceactionlab.com", "smart-lab.ru", "habr.com",
                  "qiita.com", "zhihu.com"):
            self.assertFalse(VN._la_ha_tang(m), m)

    def test_bo_loc_that_su_giam_so_ung_vien(self):
        """Chan neo: neu ai do noi long lai thi rac quay ve ma khong ai thay."""
        rac = ["localhost", "example.com", "googletagmanager.com",
               "get.docker.com", "addtoany.com", "no-cache.hubspot.com"]
        that = ["qoppac.blogspot.com", "financial-hacker.com", "smart-lab.ru"]
        self.assertEqual(sum(VN._la_ha_tang(m) for m in rac), len(rac))
        self.assertEqual(sum(VN._la_ha_tang(m) for m in that), 0)
