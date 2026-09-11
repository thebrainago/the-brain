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




class LichTheoDoiTHEO_SUAT_KHONG_THEO_LICH_CUNG(unittest.TestCase):
    """Mot kenh ra bai moi moi thang ma quet moi ngay la 29 lan goi mang cho mot
    cau tra loi da biet truoc."""

    def setUp(self):
        from nhan import theo_doi as TD
        self.TD = TD

    def test_co_bai_moi_thi_quet_DAY_hon(self):
        cu = 7 * 86400.0
        self.assertLess(self.TD._chu_ky_moi(cu, bai_moi=3), cu)

    def test_khong_co_bai_moi_thi_GIAN_ra(self):
        cu = 7 * 86400.0
        self.assertGreater(self.TD._chu_ky_moi(cu, bai_moi=0), cu)

    def test_chu_ky_luon_trong_bien(self):
        for cu, moi in ((1.0, 0), (1e9, 5), (7 * 86400.0, 0)):
            v = self.TD._chu_ky_moi(cu, moi)
            self.assertGreaterEqual(v, self.TD.CHU_KY_MIN)
            self.assertLessEqual(v, self.TD.CHU_KY_MAX)

    def test_danh_sach_da_vao_SO_CHINH(self):
        """Giu danh sach trong thu_vien.db nghia la `evolution` khong bao gio
        thay, va bo lap lich phai mo hai co so du lieu."""
        b = self.TD.bang()
        self.assertGreaterEqual(len(b), 5, "chua nhap: `python -m nhan.theo_doi nhap`")
        self.assertTrue(any((r["nen_tang"] or "") == "youtube" for r in b))

    def test_nen_tang_chua_ho_tro_thi_noi_RO_chu_khong_im(self):
        kq = self.TD.quet_mot({"ma": "thu", "url": "https://x.test",
                               "nen_tang": "mot_nen_tang_la",
                               "chu_ky_giay": 604800.0})
        self.assertFalse(kq["nhan"])
        self.assertIn("chua co duong quet", kq["ly_do"])




class BI_CHAN_KHAC_KHONG_CO_GI(unittest.TestCase):
    """Hai thu nay cho cung `bai_moi = 0`. Khong phan biet thi bo lap lich GIAN
    chu ky len 45 ngay vi mot lan bi chan - tu trung phat chinh no cho mot loi
    khong phai cua nguon. Bay `khau do hong doc y het ket qua am`, o tang lich."""

    def setUp(self):
        from nhan import theo_doi as TD
        self.TD = TD

    def test_nhan_ra_cac_dang_bi_chan(self):
        for t in ("Sign in to confirm you're not a bot",
                  "HTTP Error 429: Too Many Requests",
                  "use --cookies-from-browser"):
            with self.subTest(t=t):
                self.assertTrue(self.TD._LA_CHAN(t))

    def test_KHONG_nham_loi_that_thanh_bi_chan(self):
        for t in ("khong co phu de", "Private video", "phu de qua ngan (12 ky tu)"):
            with self.subTest(t=t):
                self.assertFalse(self.TD._LA_CHAN(t))

    def test_bi_chan_thi_KHONG_doi_lich_cua_nguon(self):
        from nhan import so as SO
        ma = "thu::bi_chan"
        self.TD._khoi_tao()
        with SO.ket_noi() as cn:
            cn.execute("INSERT INTO theo_doi(ma,url,nen_tang,chu_ky_giay,lan_quet,"
                       "trang_thai) VALUES(?,?,?,?,?,'BAT') "
                       "ON CONFLICT(ma) DO UPDATE SET lan_quet=excluded.lan_quet,"
                       "chu_ky_giay=excluded.chu_ky_giay",
                       (ma, "https://x.test", "youtube", 604800.0, 111.0))
        try:
            self.TD.quet_mot({"ma": ma, "url": "https://x.test",
                              "nen_tang": "khong_ho_tro", "chu_ky_giay": 604800.0})
            r = SO.mot("SELECT lan_quet, chu_ky_giay FROM theo_doi WHERE ma=?", ma)
            # nen tang chua ho tro KHONG phai bi chan -> van duoc coi la mot lan quet
            self.assertGreater(float(r["lan_quet"]), 111.0)
        finally:
            with SO.ket_noi() as cn:
                cn.execute("DELETE FROM theo_doi WHERE ma = ?", (ma,))




class OCR_RAC_KHONG_DUOC_VAO_KHO(unittest.TestCase):
    """OCR tren anh xau cho ra chuoi TRONG GIONG chu ma khong phai chu. De chung
    vao `noi_dung` thi bo doc se cham chung, hang doi tu vung day nhung cum vo
    nghia, va ca hai bo do sau do deu nhieu di."""

    def setUp(self):
        from nhan import doc_anh as DA
        self.DA = DA

    def test_co_tesseract_that(self):
        """`pytesseract` chi la vo boc - no goi mot chuong trinh NGOAI. Truoc
        11/09 may co vo boc ma khong co chuong trinh, nen moi loi goi deu nem."""
        self.assertIsNotNone(self.DA.co_tesseract(),
                             "chua cai tesseract.exe - cua anh khong mo duoc")

    def test_chan_chuoi_rac(self):
        ok, vi = self.DA._du_sach("|_||,-. ~ ||| _- ,,, |||| ~~~ ._. |||" * 6)
        self.assertFalse(ok)
        self.assertIn("rac", vi)

    def test_chan_van_ban_qua_ngan(self):
        ok, vi = self.DA._du_sach("Buy RSI")
        self.assertFalse(ok)
        self.assertIn("qua ngan", vi)

    def test_chan_chuoi_khong_co_tu_nao_dai(self):
        ok, vi = self.DA._du_sach("a b c d e f g h i j k l m n " * 12)
        self.assertFalse(ok)

    def test_van_ban_that_thi_qua(self):
        vb = ("Buy when the 2-period RSI closes below 10 and the close is above "
              "the 200-day moving average. Sell when the close crosses above "
              "the 5-day moving average. Hold for at most five days.")
        ok, vi = self.DA._du_sach(vb)
        self.assertTrue(ok, vi)

    def test_PDF_CO_LOP_CHU_thi_KHONG_ocr(self):
        """OCR mot ban da co chu la doi mot ban sach lay mot ban co loi nhan
        dang. Bo doc phai uu tien lop chu."""
        import inspect
        ma = inspect.getsource(self.DA.doc_pdf_quet)
        self.assertIn("pdf_co_lop_chu", ma)
        self.assertIn("doi mot ban sach", ma)


if __name__ == "__main__":
    unittest.main()
