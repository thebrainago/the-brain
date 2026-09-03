# -*- coding: utf-8 -*-
"""DNS BI DAU DOC: ba trieu chung khac nhau cua MOT nguyen nhan.

Do 03/09/2026, khi chu du an yeu cau vao bang duoc MQL5 ("nguon thuc chien
nhat"). Chan doan theo tung tang thay vi doan:

  `nslookup www.mql5.com` -> DUY NHAT `2401:fce0:31:1::247` (IPv6 cua ISP Viet
  Nam), va may chu DNS dau tien `timed out`. Hau qua o moi tang:
     requests -> RemoteDisconnected
     Chrome   -> ERR_HTTP2_PROTOCOL_ERROR
     curl     -> HTTP 000 o ca http/1.0, 1.1 va 2
  Ba trieu chung nay tung bi doan nham thanh "chan bot" va "render bang JS".

  IP that qua DNS-over-HTTPS: Cloudflare 203.29.60.247 / Google 36.255.76.151.
  Noi thang vao do voi SNI dung: **HTTP 200, Server: Caddy, 82.347 ky tu,
  40 link ma nguon**.

Bo test nay KHONG goi mang ra ngoai (tru mot bai danh dau `mang` bi bo qua khi
khong co ket noi).
"""
from __future__ import annotations

import socket
import unittest
from unittest import mock

from nhan import dns_vuot as DV
from nhan import duyet_nguoi as DN


class BatTat(unittest.TestCase):
    def setUp(self):
        DV.tat()

    def tearDown(self):
        DV.tat()

    def test_bat_roi_tat_tra_lai_dung_ham_goc(self):
        goc = socket.getaddrinfo
        self.assertTrue(DV.bat())
        self.assertIsNot(socket.getaddrinfo, goc)
        self.assertTrue(DV.tat())
        self.assertIs(socket.getaddrinfo, goc)

    def test_bat_nhieu_lan_an_toan(self):
        self.assertTrue(DV.bat())
        self.assertFalse(DV.bat(), "lan hai phai bao la DA bat roi")
        sau_hai_lan = socket.getaddrinfo
        DV.tat()
        self.assertIsNot(socket.getaddrinfo, sau_hai_lan)

    def test_tat_khi_chua_bat_khong_no(self):
        self.assertFalse(DV.tat())

    def test_context_manager_tra_lai_nguyen_trang(self):
        goc = socket.getaddrinfo
        with DV.Bat():
            self.assertTrue(DV.dang_bat())
        self.assertIs(socket.getaddrinfo, goc)

    def test_context_KHONG_tat_cai_da_bat_tu_truoc(self):
        """Long nhau thi cai trong khong duoc tat cai ngoai."""
        DV.bat()
        with DV.Bat():
            pass
        self.assertTrue(DV.dang_bat(), "context trong da tat nham cai ngoai")


class DoiTenSangIP(unittest.TestCase):
    def setUp(self):
        DV.tat()
        self.ban_do_cu = dict(DV.BAN_DO)

    def tearDown(self):
        DV.tat()
        DV.BAN_DO.clear()
        DV.BAN_DO.update(self.ban_do_cu)

    def _bat_voi_gia_lap(self):
        """Thay `socket.getaddrinfo` TRUOC khi `bat()` chup no lam `_GOC`.

        Va vao `DV._GOC` sau khi `bat()` la vo dung: `bat()` chup
        `socket.getaddrinfo` NGAY LUC GOI va dong kin no trong closure.
        """
        goi = []
        gia = lambda h, p, *a, **k: goi.append(h)      # noqa: E731
        that = socket.getaddrinfo
        socket.getaddrinfo = gia
        DV.bat()
        self.addCleanup(setattr, socket, "getaddrinfo", that)
        return goi

    def test_ten_trong_ban_do_duoc_doi_sang_IP(self):
        DV.BAN_DO.clear()
        DV.BAN_DO["thu.example"] = "1.2.3.4"
        goi = self._bat_voi_gia_lap()
        socket.getaddrinfo("thu.example", 443)
        self.assertEqual(goi, ["1.2.3.4"])

    def test_ten_NGOAI_ban_do_giu_nguyen(self):
        """Hieu chuan chieu nguoc: va nay khong duoc dong vao ten khac."""
        DV.BAN_DO.clear()
        DV.BAN_DO["thu.example"] = "1.2.3.4"
        goi = self._bat_voi_gia_lap()
        socket.getaddrinfo("google.com", 443)
        self.assertEqual(goi, ["google.com"])

    def test_khong_phan_biet_hoa_thuong(self):
        DV.BAN_DO.clear()
        DV.BAN_DO["thu.example"] = "1.2.3.4"
        goi = self._bat_voi_gia_lap()
        socket.getaddrinfo("Thu.Example", 443)
        self.assertEqual(goi, ["1.2.3.4"])


class MaNenPhaiGiaiDuoc(unittest.TestCase):
    """Khai `br` khi khong giai nen duoc thi `r.text` ra RAC, va HTTP van 200.

    Do that: cung mot trang MQL5, khai `br` -> 21.245 ky tu / 0 link;
    bo `br` -> 82.347 ky tu / 40 link. Loi khong hien o ma trang thai.
    """

    def test_chi_khai_br_khi_giai_nen_duoc(self):
        co = DN._co_brotli()
        self.assertEqual("br" in DN._MA_NEN, co)

    def test_luon_co_gzip_va_deflate(self):
        self.assertIn("gzip", DN._MA_NEN)
        self.assertIn("deflate", DN._MA_NEN)


class DuyetNhuNguoi(unittest.TestCase):
    def test_referer_day_theo_trang_vua_di(self):
        k = DN.Khach.__new__(DN.Khach)
        k.truoc = None
        self.assertNotIn("Referer", DN._dau_trang(None))
        self.assertEqual(DN._dau_trang("https://a/b")["Referer"], "https://a/b")

    def test_nhip_la_KHOANG_chu_khong_phai_hang_so(self):
        """Nhip deu tam tap la dau van de nhan ra nhat cua may."""
        self.assertIsInstance(DN.NHIP, tuple)
        self.assertLess(DN.NHIP[0], DN.NHIP[1])
        self.assertGreaterEqual(DN.NHIP[0], 2.0)

    def test_thong_ke_dem_ca_403(self):
        k = DN.Khach.__new__(DN.Khach)
        k.so_lan, k.so_403 = 8, 2
        self.assertAlmostEqual(k.thong_ke()["ty_le_403"], 0.2, places=3)


if __name__ == "__main__":
    unittest.main()
