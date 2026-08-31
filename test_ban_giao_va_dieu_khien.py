# -*- coding: utf-8 -*-
"""BAN GIAO SONG + DIEU KHIEN XA — hai thu phai song sot khi agent chet.

Ca hai file nay ton tai vi mot ly do: **khong duoc phu thuoc vao agent**. Ban
giao phai day du ke ca khi phien dut giua chung (het han muc token, may ngu),
va lenh tat may phai chay duoc khi agent da im.

Bon dieu nam trong bo kiem:
  1. Ban giao GHI THEM, khong bao gio ghi de - mat mot dong la mat mot viec.
  2. So dai qua thi cat phan CU ve nhat_ky, giu phan MOI.
  3. `/tat` khong duoc tat ngay: phai hen gio va phai co duong huy.
  4. Nguoi la nhan tin vao bot thi khong duoc phuc vu.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

import ban_giao_song as BG      # noqa: E402
import dieu_khien_xa as DK      # noqa: E402


class BanGiaoPhaiGhiTHEM(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self._so = BG.SO
        BG.SO = self.tmp / "BAN_GIAO_SONG.md"

    def tearDown(self):
        BG.SO = self._so

    def test_hai_lan_ghi_thi_con_ca_hai(self):
        BG.ghi("viec mot")
        BG.ghi("viec hai")
        van = BG.SO.read_text(encoding="utf-8")
        self.assertIn("viec mot", van)
        self.assertIn("viec hai", van)

    def test_so_dai_thi_cat_phan_CU_ve_nhat_ky_giu_phan_MOI(self):
        self._nhat_ky = BG.LAB
        with mock.patch.object(BG, "LAB", self.tmp):
            for i in range(BG.TRAN_DONG + 20):
                BG.ghi(f"viec {i}")
            van = BG.SO.read_text(encoding="utf-8")
        self.assertIn(f"viec {BG.TRAN_DONG + 19}", van, "mat dong MOI NHAT")
        self.assertTrue(list((self.tmp / "nhat_ky").glob("BAN_GIAO_SONG_*.md")),
                        "khong cat phan cu ve nhat_ky")

    def test_chup_trang_thai_khong_bao_gio_nem_loi(self):
        """Hook goi ham nay moi luot; no ma nem loi thi chan ca phien lam viec."""
        self.assertIsInstance(BG.chup(), str)


class TatMayPhaiCoDUONGHUY(unittest.TestCase):

    def test_tat_la_HEN_GIO_chu_khong_tat_ngay(self):
        with mock.patch.object(DK.subprocess, "run") as gia:
            DK.xu_ly("/tat")
        lenh = gia.call_args[0][0]
        self.assertIn("/t", lenh, "khong hen gio - mot cu cham nham la mat viec")
        self.assertGreaterEqual(int(lenh[lenh.index("/t") + 1]), 30)

    def test_co_lenh_huy(self):
        with mock.patch.object(DK.subprocess, "run") as gia:
            gia.return_value = mock.Mock(returncode=0, stdout="")
            ra = DK.xu_ly("/huy")
        self.assertIn("/a", gia.call_args[0][0])
        self.assertIn("huy", ra.lower())

    def test_dung_va_chay_dat_va_go_dung_mot_co(self):
        import tempfile
        with mock.patch.object(DK, "DUNG_LAI", Path(tempfile.mkdtemp()) / "DUNG_LAI.flag"):
            DK.xu_ly("/dung")
            self.assertTrue(DK.DUNG_LAI.exists())
            DK.xu_ly("/chay")
            self.assertFalse(DK.DUNG_LAI.exists())

    def test_lenh_la_khong_lam_gi_nguy_hiem(self):
        with mock.patch.object(DK.subprocess, "run") as gia:
            DK.xu_ly("xin chao")
        gia.assert_not_called()


class ChiPhucVuCHUNHAN(unittest.TestCase):

    def test_nguoi_la_khong_duoc_phuc_vu(self):
        goi = []
        with mock.patch.object(DK, "_ch", lambda: {"bot_token": "x", "chat_id": 111}), \
             mock.patch.object(DK, "gui", lambda *a, **k: goi.append(a)), \
             mock.patch.object(DK.requests, "get") as g:
            g.return_value = mock.Mock(json=lambda: {"result": [
                {"update_id": 1, "message": {"chat": {"id": 999}, "text": "/tat"}}]})
            DK._mot_luot(None)
        self.assertEqual(goi, [], "da tra loi nguoi la")

    def test_lan_dau_chua_co_chat_id_thi_nhan_chu(self):
        luu = {}
        with mock.patch.object(DK, "_ch", lambda: {"bot_token": "x", "chat_id": 0}), \
             mock.patch.object(DK, "_luu", lambda c: luu.update(c)), \
             mock.patch.object(DK, "gui", lambda *a, **k: True), \
             mock.patch.object(DK.requests, "get") as g:
            g.return_value = mock.Mock(json=lambda: {"result": [
                {"update_id": 1, "message": {"chat": {"id": 777}, "text": "/help"}}]})
            DK._mot_luot(None)
        self.assertEqual(luu.get("chat_id"), 777)


if __name__ == "__main__":
    unittest.main()
