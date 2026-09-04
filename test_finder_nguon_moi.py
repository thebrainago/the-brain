# -*- coding: utf-8 -*-
"""Test cho ba module ra doi 04/09/2026: tru/finder, nhan/nguon_tinix,
nhan/telegram.

Khong test nao o day cham mang. Nhung cho CAN mang (`kiem_kenh`, `thu_thap`)
duoc do bang van ban co san, vi mot test phu thuoc mang thi khi do se bao
"hong" cho mot su that la "hom nay Telegram cham".
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import nguon_tinix as TX          # noqa: E402
from nhan import san_cong_cu as SCC         # noqa: E402
from nhan import telegram as TG             # noqa: E402
from tru import finder as F                 # noqa: E402


class DoanNhuCauKhongDuocNEO_GIA(unittest.TestCase):
    """Nhom test nay ton tai vi mot loi CU THE da xay ra 04/09/2026."""

    def test_khong_khop_ast_trong_giua_mot_tu(self):
        """Loi that: nhanh `ast` khong chan bien tu khop vao 'last', 'contrast'.

        Hau qua do duoc: 11 the neo duoc, ca 11 la bai bao arXiv khong lien
        quan, neo vao van de that `can_mau_moi_tu_ma_nguon`. Mot neo gia pha
        dung cai rang buoc "chi de xuat khi khop mot van de da biet".
        """
        for van in ("the last bar of the session",
                    "high contrast rendering",
                    "a fast vectorised loop",
                    "broadcast the result"):
            with self.subTest(van=van):
                nc, _ = F.doan_nhu_cau({"full_name": "ai/do", "mo_ta": van})
                self.assertIsNone(
                    nc, f"'{van}' khong noi gi ve doc ma, khong duoc gan nhu cau")

    def test_van_khop_khi_dung_that(self):
        nc, bc = F.doan_nhu_cau(
            {"full_name": "ai/do", "mo_ta": "A Pine Script parser in Python"})
        self.assertEqual(nc, "doc_ma_thanh_chien_luoc")
        self.assertTrue(bc, "phai kem bang chung la cum tu nao khop")

    def test_bai_bao_khong_bao_gio_duoc_gan_nhu_cau(self):
        bb = {"full_name": "Kinetic modelling of the CO2 capture",
              "mo_ta": "we use a fast crawler to gather spectra",
              "loai": "bai_bao"}
        self.assertEqual(F.doan_nhu_cau(bb), (None, ""))

    def test_nhan_dang_bai_bao_khong_dua_vao_full_name(self):
        """Bai bao trong kho VAN co `full_name` - do la TIEU DE, khong phai repo.

        Ban sua dau tien dung dieu kien `not full_name` va no khong bao gio
        dung, nen bai bao van lot vao DE_XUAT.
        """
        self.assertTrue(F.la_bai_bao({"full_name": "Mot tieu de dai",
                                      "loai": "bai_bao"}))
        self.assertTrue(F.la_bai_bao({"full_name": "X", "loai": "khac",
                                      "url": "http://arxiv.org/abs/2605.05704v3"}))
        self.assertFalse(F.la_bai_bao({"full_name": "org/repo", "loai": "khac",
                                       "url": "https://github.com/org/repo"}))


class TheDeXuat(unittest.TestCase):

    def test_khong_neo_thi_khong_bao_gio_de_xuat(self):
        t = F.lam_the("x/y", {"full_name": "x/y", "ngon_ngu": "Python",
                              "mo_ta": "m" * 200, "nhu_cau": "khong_co_that"},
                      {})
        self.assertEqual(t["trang_thai"], "TAM_HOAN")
        self.assertEqual(t["van_de_giai_quyet"], [])
        self.assertIn("CHUA NEO", " ".join(t["rui_ro"]))

    def test_neo_bang_tu_khoa_chi_duoc_toi_CHO_XAC_NHAN(self):
        t = F.lam_the("x/y", {"full_name": "x/y", "ngon_ngu": "Python",
                              "mo_ta": "m" * 200, "nhu_cau": "nguon_im_lang",
                              "nhu_cau_gan_boi": "finder.doan_nhu_cau"},
                      {"nguon_im_lang": ["vd_nguon_im_lang"]})
        self.assertEqual(t["trang_thai"], "CHO_XAC_NHAN")
        self.assertTrue(t["neo_tam"])

    def test_bai_bao_khong_vao_hang_doi_tich_hop(self):
        t = F.lam_the("Mot bai", {"full_name": "Mot bai", "loai": "bai_bao",
                                  "nhu_cau": "nguon_im_lang"},
                      {"nguon_im_lang": ["vd_nguon_im_lang"]})
        self.assertEqual(t["trang_thai"], "DOC_THAM_KHAO")

    def test_cong_tich_hop_tang_khi_ngon_ngu_khong_nhap_duoc(self):
        re_ = F.cong_tich_hop({"loai": "thu_vien", "ngon_ngu": "Python",
                               "doi_chieu_voi": "nhan/cong.py"})
        dat = F.cong_tich_hop({"loai": "thu_vien", "ngon_ngu": "Rust",
                               "doi_chieu_voi": "nhan/cong.py"})
        self.assertLess(re_["bac"], dat["bac"])

    def test_muc_khop_khong_the_vuot_100(self):
        t = F.muc_khop({"trich_dan": "x" * 500, "ngon_ngu": "Python",
                        "doi_chieu_voi": "nhan/cong.py"}, ["vd_nao_do"])
        self.assertLessEqual(t["muc_khop"], 100.0)
        self.assertEqual(t["muc_khop"], 100.0)


class AnhXaVanDe(unittest.TestCase):

    def test_moi_nhu_cau_finder_dung_deu_co_that(self):
        """Tu khoa cua Finder khong duoc tro toi mot nhu cau khong ton tai."""
        co = set(SCC.NHU_CAU) | set(SCC.NHU_CAU_TU_VAN_DE)
        for _, nc in F.TU_KHOA_NHU_CAU:
            with self.subTest(nhu_cau=nc):
                self.assertIn(nc, co)


class TinixDocDuocPayload(unittest.TestCase):

    MAU = ('self.__next_f.push([1,"7:[\\"$\\",{\\"initialProjects\\":['
           '{\\"fullName\\":\\"ai/bo-quet\\",\\"description\\":\\"A crawler\\",'
           '\\"sourceUrl\\":\\"https://github.com/ai/bo-quet\\",'
           '\\"primaryLanguage\\":\\"Python\\",\\"license\\":\\"MIT\\",'
           '\\"topics\\":[\\"scraping\\"],\\"slug\\":\\"ai-bo-quet\\"},'
           '{\\"fullName\\":\\"ai/game\\",\\"description\\":\\"A puzzle game\\",'
           '\\"sourceUrl\\":\\"https://github.com/ai/game\\",'
           '\\"primaryLanguage\\":\\"C#\\",\\"license\\":\\"NOASSERTION\\",'
           '\\"topics\\":[],\\"slug\\":\\"ai-game\\"}]}]"])')

    def test_rut_duoc_du_an_tu_chuoi_rsc(self):
        ds = TX._du_an_trong(self.MAU)
        self.assertEqual([d["fullName"] for d in ds], ["ai/bo-quet", "ai/game"])

    def test_chuan_hoa_doi_NOASSERTION_thanh_khong_khai(self):
        ds = [TX._chuan(d) for d in TX._du_an_trong(self.MAU)]
        self.assertEqual(ds[0]["giay_phep"], "MIT")
        self.assertEqual(ds[1]["giay_phep"], "?")
        self.assertEqual(ds[0]["nguon"], "tinix")

    def test_loc_quan_tam_giu_bo_quet_bo_game(self):
        ds = [TX._chuan(d) for d in TX._du_an_trong(self.MAU)]
        co, khong = TX.loc_quan_tam(ds)
        self.assertEqual([d["full_name"] for d in co], ["ai/bo-quet"])
        self.assertEqual([d["full_name"] for d in khong], ["ai/game"])

    def test_mang_sau_can_bang_duoc_ngoac_trong_chuoi(self):
        t = 'x: [1, "co ] trong chuoi", [2, 3]] duoi'
        self.assertEqual(TX._mang_sau(t, t.index("[")),
                         '[1, "co ] trong chuoi", [2, 3]]')


class TelegramDocTrangXemTruoc(unittest.TestCase):

    MAU = (
        '<div class="tgme_widget_message_wrap"><div class="tgme_widget_message" '
        'data-post="kenh/42"><div class="tgme_widget_message_text js-message_text">'
        'Mua khi RSI&lt;30<br>Thoat sau 5 nen</div>'
        '<div class="tgme_widget_message_document_title">EA_Test.mq5</div>'
        '<div class="tgme_widget_message_document_extra">12.3 KB</div>'
        '<time datetime="2026-09-01T10:00:00+00:00"></time></div></div>'
        '<a class="tme_messages_more" data-before="41"></a>')

    def test_rut_van_ban_va_go_the(self):
        vb = TG._van_ban(self.MAU)
        self.assertIn("Mua khi RSI<30", vb)
        self.assertIn("Thoat sau 5 nen", vb)
        # `<` VAN duoc phep ton tai: `RSI&lt;30` giai ma ra `RSI<30` va do la
        # noi dung that. Cai phai bien mat la THE HTML, khong phai ky tu `<`.
        self.assertNotRegex(vb, r"<\s*/?[a-zA-Z][^>]*>")

    def test_nhan_ra_file_ma_nguon_dinh_kem(self):
        dk = TG._dinh_kem(self.MAU)
        self.assertEqual(len(dk), 1)
        self.assertEqual(dk[0]["ten"], "EA_Test.mq5")
        self.assertEqual(dk[0]["loai"], "ma_nguon")

    def test_ex5_la_nhi_phan_chu_khong_phai_ma_nguon(self):
        mau = self.MAU.replace("EA_Test.mq5", "EA_Test.ex5")
        self.assertEqual(TG._dinh_kem(mau)[0]["loai"], "nhi_phan")

    def test_so_nguoi_theo_doi(self):
        self.assertEqual(TG._so_theo_doi("Kenh X 11 362 subscribers"), 11362)
        self.assertIsNone(TG._so_theo_doi("khong co gi"))

    def test_duoi_nhi_phan_khong_giao_voi_duoi_ma(self):
        self.assertEqual(set(TG.DUOI_MA) & set(TG.DUOI_NHI_PHAN), set())


class DocPdfChiOcrKhiCan(unittest.TestCase):
    """`nhan/doc_pdf.py`. Luat quan trong nhat: KHONG OCR trang da co chu."""

    class _TrangGia:
        """Gia mot trang pymupdf: chi can `get_text`."""

        def __init__(self, chu):
            self._chu = chu

        def get_text(self):
            return self._chu

        def get_pixmap(self, dpi=None):
            raise AssertionError(
                "KHONG duoc dung trang thanh anh khi lop chu da du day - "
                "do la 14 giay CPU vut di, va OCR luon te hon lop chu that")

    def test_trang_day_chu_khong_bi_dung_thanh_anh(self):
        from nhan import doc_pdf as P
        chu = "x" * (P.SAN_CHU_MOI_TRANG + 50)
        vb, cach = P.doc_mot_trang(self._TrangGia(chu), ocr=True)
        self.assertEqual(cach, "chu")
        self.assertEqual(vb, chu)

    def test_ocr_tat_thi_khong_bao_gio_dung_anh(self):
        from nhan import doc_pdf as P
        vb, cach = P.doc_mot_trang(self._TrangGia("ngan"), ocr=False)
        self.assertEqual(cach, "chu")

    def test_san_chu_dat_tren_muc_do_duoc_cua_slide_anh(self):
        """Slide-anh do duoc ~67 ky tu/trang; san phai o TREN muc do."""
        from nhan import doc_pdf as P
        self.assertGreater(P.SAN_CHU_MOI_TRANG, 67)

    def test_ghi_kho_tu_choi_van_ban_qua_ngan(self):
        from nhan import doc_pdf as P
        r = P.ghi_kho({"van_ban": "ngan qua", "duong": "x.pdf", "file": "x.pdf"},
                      "thu")
        self.assertFalse(r["ghi"])


class KhamPhaNguonKhongDuocTuBAT(unittest.TestCase):
    """`nhan/kham_pha_nguon.py`. Luat: kham pha chi DE NGHI, khong bat nguon."""

    def test_so_dang_ky_co_it_nhat_hai_kenh(self):
        """Mot kenh duy nhat la dung ho benh da do duoc: kenh blog ra 0 nguon
        moi ngay 04/09 sau khi da ra 7 nguon ngay 23/08 - tuc no can."""
        from nhan import kham_pha_nguon as KP
        self.assertGreaterEqual(len(KP.KENH), 2)
        self.assertIn("telegram", KP.KENH)

    def test_moi_kenh_deu_goi_duoc(self):
        from nhan import kham_pha_nguon as KP
        for ten, f in KP.KENH.items():
            with self.subTest(kenh=ten):
                self.assertTrue(callable(f))

    def test_de_nghi_luon_vao_dien_THU(self):
        from nhan import kham_pha_nguon as KP
        d = KP.de_nghi.__doc__ or ""
        self.assertIn("Khong bat", d)

    def test_tu_khoa_telegram_co_ca_tieng_viet(self):
        """Truy van tieng Anh khong cham toi nua thi truong. Do 04/09: tu khoa
        tieng Viet de ra @QuantTradingVN, @scalpingvangforex."""
        from nhan import kham_pha_nguon as KP
        viet = [t for t in KP.TU_KHOA_TELEGRAM
                if any(x in t for x in ("chien", "vang", "giao dich", "vietnam"))]
        self.assertGreaterEqual(len(viet), 3)

    def test_nguong_nguoi_toi_thieu_ton_tai(self):
        from nhan import kham_pha_nguon as KP
        self.assertGreater(KP.NGUOI_TOI_THIEU, 0)

    def test_ghi_ra_nhung_kenh_CHUA_LAM(self):
        """Biet minh chua lam gi thi lan sau khong phai nho lai."""
        from nhan import kham_pha_nguon as KP
        self.assertTrue(KP.CHUA_LAM)


class KetQuaGithubPhaiVaoDuocKho(unittest.TestCase):
    """LOI DA SAP, va no am tu lau.

    `mot_luot` doc `r.get("full_name")` de dat ten the, nhung `tim_github` tra
    ve khoa `ten`. Nen MOI ket qua GitHub deu bi `continue` - **khong mot kho ma
    GitHub nao tung vao duoc kho cong cu**. Duong arXiv dung khoa nen no chay,
    va do la ly do kho 110 the gan nhu toan bai bao.

    Trieu chung hien ra suot ma khong ai doc: moi luot in `[ 0 moi] <truy van>
    (N ket qua)` - co ket qua, khong bao gio co the moi.

    Va docstring cua chinh `tim_github` DA ghi nhan loi nay ("moi ket qua deu
    hien ra None None") roi sua o DAU SAI: doi ten ben trong `tim_github` thay
    vi sua ben tieu thu.
    """

    MAU_GITHUB = {"ten": "achetronic/parakeet",
                  "url": "https://github.com/achetronic/parakeet",
                  "sao": "266", "mo_ta": "Whisper-compatible ASR server",
                  "giay_phep": "Apache-2.0", "ngon_ngu": "Go", "fork": 20,
                  "cap_nhat": "2026-07-03T10:19:52Z", "nguon": "github"}

    def test_chuan_hoa_dat_duoc_full_name(self):
        c = SCC.chuan_hoa_ket_qua(self.MAU_GITHUB)
        self.assertEqual(c["full_name"], "achetronic/parakeet")

    def test_chuan_hoa_dat_du_truong_cho_cham_diem(self):
        c = SCC.chuan_hoa_ket_qua(self.MAU_GITHUB)
        for truong in ("stargazers_count", "pushed_at", "license", "html_url",
                       "language", "forks_count"):
            with self.subTest(truong=truong):
                self.assertIsNotNone(c.get(truong))

    def test_the_dung_duoc_sau_chuan_hoa(self):
        g = SCC._gon(SCC.chuan_hoa_ket_qua(self.MAU_GITHUB), "nhu_cau_x", "tv")
        self.assertEqual(g["full_name"], "achetronic/parakeet")
        self.assertEqual(g["ngon_ngu"], "Go")
        self.assertIsNotNone(g["diem"])

    def test_khong_dung_vao_ban_ghi_da_dung_hinh_dang(self):
        """arXiv da co `full_name` - khong duoc sua gi cua no."""
        bb = {"full_name": "Mot bai bao", "la_bai_bao": True, "ngay": "2026-01-01"}
        self.assertEqual(SCC.chuan_hoa_ket_qua(bb), bb)

    def test_tim_github_tra_du_truong(self):
        """Bo truong nao thi ben tieu thu am tham mat mot truc cham diem."""
        import inspect
        src = inspect.getsource(SCC.tim_github)
        for truong in ('"ten"', '"sao"', '"ngon_ngu"', '"fork"', '"giay_phep"'):
            with self.subTest(truong=truong):
                self.assertIn(truong, src)


class NhanhVideoDaNGHI_HUU(unittest.TestCase):
    """Quyet dinh 04/09/2026: giu PHU DE, bo ASR. Test khoa lai ca hai ve.

    So do duoc (co che moi trieu ky tu, kho 262 co che):
        tradingview 73,7 | pdf 44,6 | telegram 9,4 | youtube 5,5
        mql5 2,7 | blog 1,0 | github 0,2
    Phu de: 5,5 la muc GIUA va no MIEN PHI -> giu.
    ASR: 150 giay CPU cho ~8.600 ky tu = ~53 phut CPU mot co che -> bo.
    """

    def test_duong_phu_de_van_con_va_van_o_nhan(self):
        """Bo ASR KHONG duoc keo theo bo phu de - hai viec khac nhau."""
        from nhan import toan_van as TV
        self.assertTrue(callable(getattr(TV, "tu_youtube", None)))

    def test_asr_da_roi_khoi_nhan(self):
        import importlib.util
        self.assertIsNone(importlib.util.find_spec("nhan.tao_phu_de"),
                          "ASR da nghi huu, khong duoc nam trong nhan/")

    def test_ban_asr_van_giu_lai_kem_ly_do(self):
        """Khong xoa: xoa thi lan sau lai mat mot buoi do lai chinh nhung con
        so da dan den quyet dinh nay."""
        f = LAB / "nghi_huu" / "tao_phu_de.py"
        self.assertTrue(f.exists())
        van = f.read_text(encoding="utf-8")
        self.assertIn("DIEU KIEN HOI SINH", van)
        self.assertIn("53", van, "phai giu con so dan den quyet dinh")


class ChiTieuNgay(unittest.TestCase):
    """`nhan/chi_tieu.py`. Hai bay da sap that trong lan chay dau deu o day."""

    def test_tong_san_nen_tang_phai_duoi_tran(self):
        """BAY DA SAP: san ban dau cong lai DUNG 1,00, nen phan chia theo suat
        khong bao gio chay. Bang ra trong giong bang theo suat nhung thuc chat
        la bang HANG SO - dung hinh dang "cong tu choi tat ca"."""
        from nhan import chi_tieu as CT
        tong = sum(c["ty_le_san"] for c in CT.NEN_TANG.values())
        self.assertLess(tong, CT.TONG_SAN_TOI_DA + 1e-9)
        self.assertLess(tong, 0.95, "san nuot het thi do luong khong lai duoc gi")

    def test_do_luong_that_su_lai_duoc_phan_chia(self):
        from nhan import chi_tieu as CT
        chia = CT.chia_nen_tang(1000)
        self.assertAlmostEqual(sum(chia.values()), 1000, delta=1.0)
        # Khong nen tang nao duoc 0: san tham do phai giu cho moi cai mot phan.
        for t, v in chia.items():
            with self.subTest(nen_tang=t):
                self.assertGreater(v, 0)

    def test_chua_do_khac_khong(self):
        """`None` = chua do, `0` = da do va bang khong. Lan lon hai cai nay la
        ho loi da sap nhieu lan trong du an."""
        from nhan import chi_tieu as CT
        self.assertIsNone(CT._tong_chi_so("mot_chi_so_chac_chan_khong_ton_tai"))

    def test_chua_do_duoc_uu_tien_nhu_thieu_toan_bo(self):
        from nhan import chi_tieu as CT
        ut = CT.uu_tien()
        self.assertAlmostEqual(sum(ut.values()), 1.0, places=6)

    def test_moi_chi_tieu_deu_kem_ly_do_do_duoc(self):
        """Mot chi tieu bia ra chi tao them mot cai bao dong sai moi ngay."""
        from nhan import chi_tieu as CT
        for ten, c in CT.CHI_TIEU.items():
            with self.subTest(chi_tieu=ten):
                self.assertTrue(c.get("vi_sao", "").strip())
                self.assertIn("Do 04/09", c["vi_sao"])
                self.assertGreater(c["muc_tieu"], 0)


class TimKenhMoi(unittest.TestCase):
    """Rut ten kenh khac tu chinh noi dung da thu - khong cham mang."""

    def test_bat_duoc_ca_hai_cach_viet_lien_ket(self):
        van = "Tham gia t.me/nhathoaitrader hoac nhan @Congdo2909 nhe"
        thay = set(TG._RX_KENH.findall(van))
        self.assertIn("nhathoaitrader", thay)
        self.assertIn("Congdo2909", thay)

    def test_bo_ten_dich_vu_khong_phai_kenh_noi_dung(self):
        """`t.me/joinchat/...` la loi moi nhom, khong phai mot kenh de theo doi."""
        self.assertIn("joinchat", TG._BO_TEN)
        self.assertIn("addstickers", TG._BO_TEN)

    def test_ten_qua_ngan_khong_duoc_nhan(self):
        """Ten kenh Telegram toi thieu 5 ky tu - `@abc` la nhac ten, khong phai kenh."""
        self.assertEqual(TG._RX_KENH.findall("hoi @abc di"), [])


class ConTroTangDan(unittest.TestCase):
    """Con tro la thu lam cho lan quet THU HAI re. Do la ly do no ton tai."""

    def test_con_tro_moi_co_hinh_dang_dung(self):
        ct = TG._con_tro_kenh("mot_kenh_chua_tung_quet_bao_gio")
        self.assertEqual(ct["id_cao_nhat"], 0)
        self.assertEqual(ct["file_da_tai"], [])

    def test_quet_mtproto_nhan_tham_so_tang_dan(self):
        import inspect
        ts = inspect.signature(TG.quet_mtproto).parameters
        self.assertIn("tang_dan", ts)
        self.assertIs(ts["tang_dan"].default, True,
                      "tang dan phai la MAC DINH - quet lai tu dau la ngoai le")


if __name__ == "__main__":
    unittest.main(verbosity=2)
