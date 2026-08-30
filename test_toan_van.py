# -*- coding: utf-8 -*-
"""TOAN VAN — duong doc noi dung, va hai loai that bai khong duoc lan.

Hai bay da sap that trong CUNG MOT NGAY (30/08/2026), va ca hai deu o day.

**Bay 1 — thieu day noi.** Ha tang trinh duyet co tu 21/08: ho so Chrome
`.browser_darwinex` 1,5 GB voi phien dang nhap that, CDP 9224,
`nhan/doc_trinh_duyet.py`, bo mo phong thao tac nguoi. Nhung `doc()` chi co ba
duong — arxiv, github, html tho — va **khong duong nao di qua trinh duyet**.
Do tren so cai: 675/1338 tai lieu khong co toan van, va reddit / mql5 /
myfxbook / darwinex / t.me **chua mot ban nao**. Noi day xong, mql5 tra ve
6.711 va 15.207 ky tu, darwinex 2.074 — truoc do deu la 0.

**Bay 2 — khoa oan.** `seeker.doc_toan_van` ghi mot ban ghi `khong_doc_duoc`
VINH VIEN moi lan `doc()` tra None. Toi hom do no danh dau **83 dia chi
Reddit** — ma Reddit hong vi `ERR_NAME_NOT_RESOLVED`, tuc **DNS bi chan tren
may nay**. Do la dieu kien MOI TRUONG, khong phai thuoc tinh cua dia chi: doi
mang hay bat VPN la doc duoc, nhung 83 bai do se khong bao gio duoc thu lai.

Hai cau phai tach bach, va bo test nay giu ranh gioi do:

    "trang nay khong co gi de doc"   -> khoa duoc
    "hom nay ta khong voi toi duoc"  -> KHONG duoc khoa

Khong goi mang: moi bai deu thay `doc_trinh_duyet` / `tu_html` bang ban gia.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import toan_van as TV   # noqa: E402


class PhanBietHaiLoaiThatBai(unittest.TestCase):
    """Chot chinh cua file nay."""

    def test_DNS_bi_chan_la_loi_TAM_THOI(self):
        TV._ghi_loi("https://www.reddit.com/r/algotrading/",
                    "Error: Page.goto: net::ERR_NAME_NOT_RESOLVED")
        self.assertTrue(
            TV.loi_tam_thoi(),
            "DNS chan bi coi la vinh vien -> 83 dia chi Reddit bi khoa oan")

    def test_trinh_duyet_dang_tat_la_loi_TAM_THOI(self):
        TV._ghi_loi("https://www.mql5.com/x", "khong_mo_cdp")
        self.assertTrue(TV.loi_tam_thoi(),
                        "tat Chrome mot luc ma khoa vinh vien ca nguon")

    def test_mang_rot_va_qua_tai_la_loi_TAM_THOI(self):
        for loi in ("ConnectionError: [Errno 11001]", "ReadTimeout",
                    "HTTP 503 Service Unavailable", "HTTP 429 Too Many Requests",
                    "SSLError: bad handshake"):
            TV._ghi_loi("https://x/y", loi)
            self.assertTrue(TV.loi_tam_thoi(), f"'{loi}' phai la tam thoi")

    def test_trang_that_su_khong_co_gi_thi_KHOA_DUOC(self):
        for loi in ("HTTP 404 Not Found", "HTTP 410 Gone",
                    "trang rong hoac qua ngan", "khong bo boc nao doc duoc"):
            TV._ghi_loi("https://x/y", loi)
            self.assertFalse(
                TV.loi_tam_thoi(),
                f"'{loi}' bi coi la tam thoi -> se keo lai mai mot dia chi hong")

    def test_khong_co_loi_thi_khong_phai_tam_thoi(self):
        TV.LOI_CUOI.clear()
        self.assertFalse(TV.loi_tam_thoi())


class DinhTuyenTheoMIEN(unittest.TestCase):

    def test_mien_can_dang_nhap_di_qua_trinh_duyet(self):
        for u in ("https://www.reddit.com/r/algotrading/x",
                  "https://www.mql5.com/en/signals/1",
                  "https://www.myfxbook.com/members/x",
                  "https://t.me/somechannel/12",
                  "https://x.com/user/status/1"):
            self.assertTrue(TV.can_trinh_duyet(u), f"{u} phai di qua trinh duyet")

    def test_mien_doc_duoc_bang_HTTP_thuong_thi_khong_can(self):
        for u in ("https://arxiv.org/abs/2401.00001",
                  "https://github.com/a/b",
                  "https://quantpedia.com/x"):
            self.assertFalse(TV.can_trinh_duyet(u), f"{u} khong can trinh duyet")


class TrinhDuyetTatThiBaoTamThoi(unittest.TestCase):
    """Khong co CDP thi phai noi ro la TAM THOI, khong im lang tra None."""

    def setUp(self):
        from nhan import doc_trinh_duyet as DTD
        self._DTD = DTD
        self._cu = DTD.cdp_dang_chay
        DTD.cdp_dang_chay = lambda *a, **k: None

    def tearDown(self):
        self._DTD.cdp_dang_chay = self._cu

    def test_cdp_tat_thi_tu_trinh_duyet_tra_None_va_danh_dau_tam_thoi(self):
        self.assertIsNone(TV.tu_trinh_duyet("https://www.reddit.com/r/x"))
        self.assertTrue(TV.loi_tam_thoi())

    def test_doc_mot_mien_can_dang_nhap_khi_cdp_tat_khong_duoc_khoa(self):
        TV.LOI_CUOI.clear()
        goc = TV.tu_html
        TV.tu_html = lambda url, kieu="khac": None
        try:
            self.assertIsNone(TV.doc("https://www.reddit.com/r/algotrading/x"))
        finally:
            TV.tu_html = goc
        self.assertTrue(
            TV.loi_tam_thoi(),
            "trinh duyet tat ma van bao la dia chi hong -> seeker se khoa oan")


class DocThanhCongThiXoaLoiCu(unittest.TestCase):

    def test_doc_duoc_thi_LOI_CUOI_phai_rong(self):
        goc = TV.tu_html
        TV.tu_html = lambda url, kieu="khac": {
            "van_ban": "x" * 900, "kieu": kieu, "cach": "html"}
        try:
            TV._ghi_loi("cu", "ERR_NAME_NOT_RESOLVED")   # loi cua lan truoc
            r = TV.doc("https://quantpedia.com/bai-viet")
        finally:
            TV.tu_html = goc
        self.assertIsNotNone(r)
        self.assertFalse(
            TV.loi_tam_thoi(),
            "loi cua lan truoc con dinh lai -> nguoi goi doc nham trang thai")




class DocTrinhDuyetBaoDungTrangThai(unittest.TestCase):
    """`doc_trinh_duyet` la cua duy nhat ra con Chrome that.

    Chi kiem phan KHONG can trinh duyet dang chay: no phai bao dung trang thai
    khi khong co CDP, thay vi nem ngoai le hay im lang tra rong. Phan doc that
    can mot con Chrome mo nen khong dua vao bo test duoc.
    """

    def test_cdp_dang_chay_tra_None_khi_khong_co_cong_nao_mo(self):
        from nhan import doc_trinh_duyet as DTD
        self.assertIsNone(DTD.cdp_dang_chay(ports=(59_999,)),
                          "bao co CDP tren mot cong khong ai nghe")

    def test_doc_gan_bao_khong_mo_cdp_thay_vi_nem_ngoai_le(self):
        from nhan import doc_trinh_duyet as DTD
        goc = DTD.cdp_dang_chay
        DTD.cdp_dang_chay = lambda *a, **k: None
        try:
            r = DTD.doc_gan("https://x/y")
        finally:
            DTD.cdp_dang_chay = goc
        self.assertEqual(r.get("loi"), "khong_mo_cdp",
                         "khong bao ro la trinh duyet dang tat")




class TranSoTabTrinhDuyet(unittest.TestCase):
    """Doc qua Chrome mo TAB MOI moi lan. Khong co tran thi no phinh vo han.

    Do that 30/08/2026 giua mot luot keo ton: **Chrome mo 356 tab**, va luot keo
    dung han. Nhin tu ngoai la "may treo" chu khong phai mot loi - khong ban ghi
    nao, khong ngoai le nao. Sau khi don ve 6 tab, moi trang doc het 10-13 giay
    thay vi ~20.

    Giu vai tab la co y (nguoi dung thay quet dang chay). Khong gioi han moi la loi.
    """

    class _Tab:
        def __init__(self, ten): self.ten, self.dong = ten, False
        def close(self): self.dong = True

    class _Ctx:
        def __init__(self, n): self.pages = [TranSoTabTrinhDuyet._Tab(i) for i in range(n)]

    def test_it_hon_tran_thi_khong_dong_gi(self):
        from nhan import doc_trinh_duyet as DTD
        ctx = self._Ctx(3)
        self.assertEqual(DTD._don_tab(ctx, giu=6), 0)
        self.assertFalse(any(t.dong for t in ctx.pages))

    def test_vuot_tran_thi_dong_bot_tab_CU_NHAT(self):
        from nhan import doc_trinh_duyet as DTD
        ctx = self._Ctx(50)
        n = DTD._don_tab(ctx, giu=6)
        self.assertEqual(n, 44)
        self.assertTrue(all(t.dong for t in ctx.pages[:44]), "khong dong tab cu")
        self.assertFalse(any(t.dong for t in ctx.pages[44:]),
                         "dong nham tab moi nhat")

    def test_mot_tab_khong_dong_duoc_khong_lam_hong_ca_luot(self):
        from nhan import doc_trinh_duyet as DTD

        class TabBuong(TranSoTabTrinhDuyet._Tab):
            def close(self): raise RuntimeError("tab da chet")

        ctx = self._Ctx(20)
        ctx.pages[0] = TabBuong("hong")
        n = DTD._don_tab(ctx, giu=6)
        self.assertEqual(n, 13, "mot tab hong lam mat ca vong don")

    def test_tran_mac_dinh_la_mot_con_so_nho(self):
        from nhan import doc_trinh_duyet as DTD
        self.assertGreaterEqual(DTD.GIU_TOI_DA_TAB, 1)
        self.assertLessEqual(DTD.GIU_TOI_DA_TAB, 20,
                             "tran qua cao thi khong con la tran")


if __name__ == "__main__":
    unittest.main()
