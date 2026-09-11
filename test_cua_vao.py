# -*- coding: utf-8 -*-
"""Kiem hai cua vao moi cua khoi 5: `nhan/doc_video.py` va `nhan/uu_tien.py`.

Cac bai kiem o day KHONG goi mang. Duong mang da duoc do that (8/8 video lay
duoc phu de luc 21:05 ngay 11/09) va ghi vao bao cao; con bai kiem thi phai chay
duoc khi may khong co mang, neu khong no se do mang moi lan mat ket noi.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import doc_video as DV  # noqa: E402
from nhan import uu_tien as UT  # noqa: E402


class BocPhuDe(unittest.TestCase):
    def test_json3(self):
        vb = json.dumps({"events": [
            {"segs": [{"utf8": "buy when "}, {"utf8": "rsi is below 30"}]},
            {"segs": [{"utf8": "\n"}]},
            {"segs": [{"utf8": "and hold for five days"}]}]})
        self.assertEqual(DV._doc_json3(vb),
                         "buy when rsi is below 30 and hold for five days")

    def test_vtt_bo_dong_lap_cua_hieu_ung_cuon(self):
        """Phu de tu dong lap lai dong truoc de lam hieu ung cuon. Khong bo thi
        mot cau bi dem nhieu lan va bo doc thay mot van ban khac han."""
        vtt = ("WEBVTT\nKind: captions\nLanguage: en\n\n"
               "00:00:01.000 --> 00:00:03.000\nbuy when rsi\n\n"
               "00:00:03.000 --> 00:00:05.000\nbuy when rsi\nis below 30\n\n"
               "00:00:05.000 --> 00:00:07.000\nis below 30\nand hold\n")
        self.assertEqual(DV._doc_vtt(vtt), "buy when rsi is below 30 and hold")

    def test_vtt_bo_the_dinh_dang(self):
        vtt = ("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n"
               "<c.colorE5E5E5>close</c> above <00:00:01.500><c> 200</c>\n")
        self.assertEqual(DV._doc_vtt(vtt), "close above  200")


class ChonPhuDeDUNG_THU_TU(unittest.TestCase):
    def test_uu_tien_phu_de_NGUOI_hon_phu_de_may(self):
        info = {"subtitles": {"en": [{"ext": "vtt", "url": "NGUOI"}]},
                "automatic_captions": {"en": [{"ext": "json3", "url": "MAY"}]}}
        self.assertEqual(DV._chon_phu_de(info)[0], "NGUOI")

    def test_trong_cung_kho_thi_json3_truoc_vtt(self):
        info = {"subtitles": {}, "automatic_captions": {"en": [
            {"ext": "vtt", "url": "V"}, {"ext": "json3", "url": "J"}]}}
        u, dd = DV._chon_phu_de(info)
        self.assertEqual((u, dd), ("J", "json3"))

    def test_khong_co_gi_thi_tra_None(self):
        self.assertIsNone(DV._chon_phu_de({"subtitles": {}, "automatic_captions": {}}))


class NHAN_PHU_DE_PHAI_RIENG(unittest.TestCase):
    """Lan chay dau tien module nay ghi ban phu de voi nhan `video` - trung nhan
    da bi 71 trang ket qua tim kiem chiem - va bo qua nham 23 video THAT."""

    def test_nhan_khong_phai_video(self):
        self.assertNotEqual(DV.KIEU, "video")
        self.assertEqual(DV.KIEU, "video_phu_de")


class CuaUuTienDocDuocFILE(unittest.TestCase):
    """Duong quan trong nhat cua `b uu-tien`: chu du an dua mot file, he tra co
    che ngay. Khong can mang."""

    def test_doc_file_txt_va_ra_co_che(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bai.txt"
            p.write_text(
                "A simple mean reversion system.\n"
                "Buy when the 2-period RSI closes below 10 and the close is "
                "above the 200-day moving average.\n"
                "Sell when the close crosses above the 5-day moving average.\n"
                "We hold for 5 days at most.\n", encoding="utf-8")
            kq = UT.xu_ly(str(p), ghi_kho=False)
        self.assertTrue(kq["nhan"], kq.get("ly_do"))
        self.assertEqual(kq["cach"], "file")
        self.assertTrue(kq["co_che"] or kq["tu_choi"],
                        "mot bai co luat ro rang ma khong ra co che nao")

    def test_nguon_khong_nhan_ra_thi_noi_ro(self):
        kq = UT.xu_ly("khong phai url cung khong phai file", ghi_kho=False)
        self.assertFalse(kq["nhan"])
        self.assertIn("khong nhan ra nguon", kq["ly_do"][0])

    def test_KHONG_ket_luan_tot_xau(self):
        """Cua nay rut ngan duong TU LINK DEN UNG VIEN. No khong backtest va
        khong phan xet - lam vay la lam thay viec cua cong."""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bai.txt"
            p.write_text("Buy when the 2-period RSI closes below 10.\n" * 3,
                         encoding="utf-8")
            kq = UT.xu_ly(str(p), ghi_kho=False)
        for cam in ("verdict", "sharpe", "lai", "nen_dung"):
            self.assertNotIn(cam, kq)

    def test_bao_cum_NGU_PHAP_CHUA_NOI_DUOC(self):
        """Mot bai "khong ra gi" phai noi duoc VI SAO: thieu tu vung, hay that
        su khong co luat nao."""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bai.txt"
            p.write_text(
                "Our approach is simple.\n"
                "Buy when the Ichimoku cloud thickness is above 30.\n"
                "Sell when the supertrend flips below 12.\n", encoding="utf-8")
            kq = UT.xu_ly(str(p), ghi_kho=False)
        self.assertTrue(kq["nhan"])
        self.assertIn("cum_chua_hieu", kq)

class CauNoiMimicKHONG_DUOC_DICH_MOT_PHAN(unittest.TestCase):
    """`ds/mimic` lam dung viec `hethong.txt` neu - suy nguoc tu so lenh - nhung
    nam trong mot kho git rieng va KHONG file nao trong lab goi toi. Cau noi nay
    la duong duy nhat, nen no phai tu choi dung cho."""

    def setUp(self):
        from nhan import mimic_cau_noi as MC
        self.MC = MC

    def test_dac_trung_khop_thi_dich_duoc(self):
        r = self.MC.dich_dieu_kien("rsi_14 <= 30.0000")
        self.assertTrue(r["nhan"], r.get("ly_do"))
        self.assertEqual(r["dieu_kien"]["trai"], {"chi_bao": "rsi", "n": 14})
        self.assertEqual(r["dieu_kien"]["phai"], {"hang": 30.0})

    def test_dac_trung_la_BIEU_THUC_thi_tu_choi_va_ghi_hang_doi(self):
        r = self.MC.dich_dieu_kien("price_position <= 0.2000")
        self.assertFalse(r["nhan"])
        self.assertEqual(r["thieu_tu_vung"], "price_position")

    def test_DICH_MOT_PHAN_bi_tu_choi(self):
        """Bo mot dieu kien khong dich duoc thi luat con lai LONG HON luat goc:
        no kich hoat nhieu hon han, an mot suat FDR, va khi truot thi ket luan
        'suy nguoc khong an' - trong khi cai truot la ban dich."""
        r = self.MC.dich_luat({"conditions": ["rsi_14 <= 25.0000",
                                              "price_position <= 0.2000"],
                               "pos_ratio": 0.7, "samples": 90})
        self.assertFalse(r["nhan"])
        self.assertIn("LONG HON", r["ly_do"][0])

    def test_dich_tron_ven_thi_ra_spec_hop_le(self):
        from nhan import ngu_phap as NP
        r = self.MC.dich_luat({"conditions": ["rsi_14 <= 30.0000",
                                              "momentum_20 <= -0.0500"],
                               "pos_ratio": 0.71, "samples": 140},
                              chieu=1, nguon="ca_kiem")
        self.assertTrue(r["nhan"], r.get("ly_do"))
        self.assertEqual(NP.kiem_khai_bao(r["spec"]), [])
        self.assertEqual(r["spec"]["ho"], "quay_ve_trung_binh")

    def test_luat_YEU_bi_bo_qua(self):
        kq = self.MC.dich_the({"rules": [
            {"conditions": ["rsi_14 <= 30.0000"], "pos_ratio": 0.31,
             "samples": 300}]}, nguon="ca_kiem")
        self.assertEqual(kq["spec"], [],
                         "luat co pos_ratio duoi nguong van duoc dich")

    def test_ban_do_khong_duoc_bia_toan_hang_gan_dung(self):
        """Hai dac trung la bieu thuc PHAI la None. Ep chung vao mot toan hang
        gan dung se cho ra mot luat KHAC luat cua trader."""
        self.assertIsNone(self.MC.BAN_DO["price_position"])
        self.assertIsNone(self.MC.BAN_DO["dist_ma200_atr"])


if __name__ == "__main__":
    unittest.main()
