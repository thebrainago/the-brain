# -*- coding: utf-8 -*-
"""SAN CONG CU — di tim du an co san, va ranh gioi khong duoc vuot.

Module nay ra doi 30/08/2026 theo yeu cau cua chu du an: EVOLUTION khong chi
canh he hong, ma con phai **di tim nhung du an/cong cu da co san de tich hop**.

Bo test khoa hai thu, va thu thu hai quan trong hon:

1. Phep cham diem xep hang duoc theo suc khoe cua mot kho ma (sao, con song,
   giay phep) — va **noi ro no KHONG cham do phu hop**. Mot kho 2.000 sao lam
   dung nguoc chieu viec ta can van duoc diem cao. Do la co y: may xep hang,
   nguoi doc va quyet.

2. **Ranh gioi tich hop.** Moi nhu cau khai bao phai noi ro no CAM VAO DAU va
   CAI GI NO KHONG DUOC THAY. Neu mot ngay nao do co nguoi khai mot nhu cau kieu
   "thay cong PASS bang thu vien X" thi bai kiem nay do. Day khong phai lo xa:
   khung ngoai (vi du `investing-algorithm-framework`, 2.022 sao) manh hon `lab`
   o ban thi nghiem va **rat de bi coi la ban thay**, trong khi no khong co lop
   chong tu lua minh nao cua du an nay.

Khong goi mang: `tim_github` duoc thay bang ban gia trong moi bai.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import san_cong_cu as SCC   # noqa: E402


def _repo(**doi) -> dict:
    goc = {"full_name": "ai/do", "html_url": "https://github.com/ai/do",
           "description": "mot cai gi do", "language": "Python",
           "stargazers_count": 1000, "forks_count": 100,
           "pushed_at": "2026-08-01T00:00:00Z",
           "license": {"spdx_id": "MIT"}}
    goc.update(doi)
    return goc


class ChamDiemTheoSucKhoe(unittest.TestCase):

    def test_nhieu_sao_hon_thi_diem_cao_hon(self):
        it = SCC.cham_diem(_repo(stargazers_count=200))["diem"]
        nhieu = SCC.cham_diem(_repo(stargazers_count=4000))["diem"]
        self.assertGreater(nhieu, it)

    def test_kho_da_bo_lau_bi_tru_diem_va_bi_canh_bao(self):
        moi = SCC.cham_diem(_repo(pushed_at="2026-08-20T00:00:00Z"))
        cu = SCC.cham_diem(_repo(pushed_at="2021-01-01T00:00:00Z"))
        self.assertGreater(moi["diem"], cu["diem"])
        self.assertTrue(any("day cuoi" in c for c in cu["canh_bao"]),
                        f"khong canh bao kho da bo: {cu['canh_bao']}")

    def test_khong_khai_giay_phep_thi_bi_canh_bao(self):
        d = SCC.cham_diem(_repo(license=None))
        self.assertTrue(any("giay phep" in c.lower() for c in d["canh_bao"]))

    def test_giay_phep_lay_nhiem_bi_canh_bao_rieng(self):
        d = SCC.cham_diem(_repo(license={"spdx_id": "AGPL-3.0"}))
        self.assertTrue(any("LAY NHIEM" in c for c in d["canh_bao"]),
                        f"AGPL khong bi canh bao: {d['canh_bao']}")

    def test_diem_nam_trong_0_100(self):
        for r in (_repo(stargazers_count=0, forks_count=0, license=None,
                        pushed_at="2015-01-01T00:00:00Z"),
                  _repo(stargazers_count=99999, forks_count=99999)):
            d = SCC.cham_diem(r)["diem"]
            self.assertGreaterEqual(d, 0.0)
            self.assertLessEqual(d, 100.0)

    def test_diem_KHONG_do_do_phu_hop(self):
        """Chot chong hieu nham: diem cao khong co nghia la dung viec.

        Do that 30/08: truy van "pdf to markdown" tra ve `mdpdf` va
        `markdown-pdf` — ca hai la Markdown -> PDF, tuc NGUOC chieu — ma van
        duoc 70,3 va 64,4 diem. Neu sau nay ai do dung diem nay lam cong tu
        dong chon cong cu thi bai kiem nay nhac ho rang no khong do dieu do.
        """
        nguoc_chieu = SCC.cham_diem(_repo(
            full_name="ai/markdown-pdf", description="Markdown to PDF converter",
            stargazers_count=1500, forks_count=200))
        self.assertGreater(
            nguoc_chieu["diem"], 50.0,
            "neu bai nay do nghia la cham diem da biet do phu hop - luc do phai "
            "viet lai docstring va bo canh bao 'may xep hang, nguoi doc'")


class RanhGioiTichHop(unittest.TestCase):
    """Cong cu ngoai lam BAN THI NGHIEM, khong bao gio lam ONG TOA."""

    def test_moi_nhu_cau_deu_khai_no_cam_vao_dau(self):
        for ten, v in SCC.NHU_CAU.items():
            self.assertTrue(v.get("cam_vao", "").strip(),
                            f"nhu cau '{ten}' khong noi no cam vao dau")
            self.assertTrue(v.get("vi_sao", "").strip(),
                            f"nhu cau '{ten}' khong noi vi sao can")

    def test_moi_nhu_cau_deu_khai_cai_gi_khong_duoc_thay(self):
        for ten, v in SCC.NHU_CAU.items():
            self.assertTrue(v.get("khong_duoc_thay", "").strip(),
                            f"nhu cau '{ten}' khong khai ranh gioi")

    def test_khong_nhu_cau_nao_nham_thay_ONG_TOA(self):
        cam = ("cong.py", "do_luc.py", "so.py", "quant_plan.py", "canary.py")
        for ten, v in SCC.NHU_CAU.items():
            cam_vao = v["cam_vao"].lower()
            for tep in cam:
                self.assertNotIn(
                    tep, cam_vao,
                    f"nhu cau '{ten}' khai cam vao '{tep}' — do la ong toa, "
                    "khong phai ban thi nghiem. Xem docstring dau module.")


class MotLuotKhongGoiMang(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._kho_cu = SCC.KHO
        SCC.KHO = Path(self._tmp.name) / "cong_cu.json"
        # Giu CA BA duong tim. Giu thieu mot duong thi ban gia ro sang bai
        # sau va bai do that bai vi mot ly do khong lien quan gi den no —
        # da xay ra that 30/08/2026 khi them HuggingFace.
        self._tim_cu = SCC.tim_github
        self._arxiv_cu = SCC.tim_arxiv
        self._hf_cu = SCC.tim_huggingface
        self._nghi_cu = SCC.NGHI_GIAY
        SCC.NGHI_GIAY = 0.0

    def tearDown(self):
        SCC.KHO = self._kho_cu
        SCC.tim_github = self._tim_cu
        SCC.tim_arxiv = self._arxiv_cu
        SCC.tim_huggingface = self._hf_cu
        SCC.NGHI_GIAY = self._nghi_cu
        self._tmp.cleanup()

    def test_gieo_tay_luon_vao_kho_ke_ca_khi_mang_hong(self):
        SCC.tim_github = lambda *a, **k: [{"loi": "HTTP 403"}]
        SCC.mot_luot(gioi_han_truy_van=1, im_lang=True)
        kho = SCC.doc_kho()
        for g in SCC.GIEO_TAY:
            self.assertIn(g["full_name"], kho,
                          "cong cu chu du an chi thang bi mat khi mang hong")

    def test_khong_them_trung_khi_chay_hai_lan(self):
        SCC.tim_github = lambda *a, **k: [_repo(full_name="ai/mot-cai")]
        SCC.mot_luot(gioi_han_truy_van=1, im_lang=True)
        n1 = len(SCC.doc_kho())
        SCC.mot_luot(gioi_han_truy_van=1, im_lang=True)
        self.assertEqual(len(SCC.doc_kho()), n1, "chay lai lam kho phinh len")

    def test_loi_mang_khong_lam_vo_mot_luot(self):
        # BA duong tim (github / arxiv / huggingface) - phai gia lap CA BA.
        # Chi gia lap mot duong thi bai kiem lang le bo qua hai duong con lai,
        # va do la cach no da hong khi them HuggingFace ngay 30/08/2026.
        SCC.tim_github = lambda *a, **k: [{"loi": "ConnectionError"}]
        SCC.tim_arxiv = lambda *a, **k: [{"loi": "ConnectionError"}]
        SCC.tim_huggingface = lambda *a, **k: [{"loi": "ConnectionError"}]
        r = SCC.mot_luot(gioi_han_truy_van=2, im_lang=True)
        self.assertGreaterEqual(r["loi"], 1)
        self.assertIn("tong_kho", r)

    def test_kho_luu_duoc_va_doc_lai_duoc(self):
        SCC.tim_github = lambda *a, **k: [_repo(full_name="ai/luu-thu")]
        SCC.tim_arxiv = lambda *a, **k: [_repo(full_name="ai/luu-thu")]
        SCC.tim_huggingface = lambda *a, **k: [_repo(full_name="ai/luu-thu")]
        SCC.mot_luot(gioi_han_truy_van=1, im_lang=True)
        lai = json.loads(SCC.KHO.read_text(encoding="utf-8"))
        self.assertIn("ai/luu-thu", lai)
        self.assertEqual(lai["ai/luu-thu"]["trang_thai"], "MOI")




class NhatDocDuong(unittest.TestCase):
    """Nhat cong cu NGAY TRONG van ban SEEKER da doc — khong tai lai gi.

    Day moi la duong chinh (chu du an chot 30/08): SEEKER da di qua hang nghin
    kho ma de san chien luoc, va `bien_dich_ung_vien.loai_ma_nguon` do duoc
    **34/52 file .mq5 la tien_ich/chi_bao** chu khong phai chien luoc. Phan lon
    nhung gi cham vao khong phai chien luoc — trong do co thu nang cap duoc
    chinh cai may nay, va truoc 30/08 chung bi bo di.
    """

    KY_THUAT = ("This python library implements the deflated Sharpe ratio and "
                "purged k-fold cross-validation. pip install thing. ")

    def test_bat_duoc_cum_ky_thuat_co_van_canh(self):
        uv = SCC.xet_van_ban("t", self.KY_THUAT * 4, "https://github.com/a/b")
        self.assertTrue(uv, "khong bat duoc 'deflated Sharpe' trong van canh python")
        self.assertEqual(uv[0]["nhu_cau"], "kiem_dinh_thong_ke")

    def test_moi_ung_vien_deu_kem_TRICH_DAN_va_VI_TRI(self):
        uv = SCC.xet_van_ban("t", self.KY_THUAT * 4, "https://github.com/a/b")
        for u in uv:
            self.assertTrue(u["trich_dan"].strip(), "ung vien khong co trich dan")
            self.assertIsInstance(u["vi_tri"], int)
            self.assertIn(u["cum_khop"].lower(), u["trich_dan"].lower())

    def test_cum_dung_nhung_KHONG_co_van_canh_ky_thuat_thi_bo(self):
        """`reality check` trong mot bai ve hon nhan khong phai cong cu."""
        self.assertEqual(
            SCC.xet_van_ban("t", "a reality check on this marriage. " * 25), [])

    def test_khong_khop_chuoi_tho(self):
        """Bai hoc da sap that: `rsi` khop trong Ve-rsi-on -> 117/156 tai lieu."""
        van = "python library Version 2 of the backtesting repo. " * 25
        self.assertEqual([u["cum_khop"] for u in SCC.xet_van_ban("t", van)], [])

    def test_van_ban_qua_ngan_thi_bo(self):
        self.assertEqual(SCC.xet_van_ban("t", "deflated sharpe python"), [])

    def test_khong_tu_nhat_chinh_minh(self):
        van = self.KY_THUAT * 4
        self.assertEqual(
            SCC.xet_van_ban("t", van,
                            "https://github.com/coding-kitties/"
                            "investing-algorithm-framework"), [])


class NhatVaoKhoKhongTrung(unittest.TestCase):

    KY_THUAT = NhatDocDuong.KY_THUAT

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._kho_cu = SCC.KHO
        SCC.KHO = Path(self._tmp.name) / "cong_cu.json"

    def tearDown(self):
        SCC.KHO = self._kho_cu
        self._tmp.cleanup()

    def test_nhat_mot_ban_doc_thi_vao_kho(self):
        n = SCC.nhat_tu_ban_doc("tieu de", self.KY_THUAT * 4,
                                "https://github.com/a/b", "github")
        self.assertGreaterEqual(n, 1)
        self.assertTrue(SCC.doc_kho())

    def test_nhat_hai_lan_cung_mot_ban_thi_khong_them(self):
        d = ("tieu de", self.KY_THUAT * 4, "https://github.com/a/b", "github")
        n1 = SCC.nhat_tu_ban_doc(*d)
        n2 = SCC.nhat_tu_ban_doc(*d)
        self.assertGreaterEqual(n1, 1)
        self.assertEqual(n2, 0, "nhat lai cung mot ban doc lam kho phinh len")

    def test_ung_vien_cong_cu_KHONG_phai_ung_vien_chien_luoc(self):
        """No khong duoc mang hinh dang cua mot gia thuyet giao dich.

        Ung vien cong cu khong vao `candidate_queue` va khong tieu suat FDR.
        Chot bang cach doi no PHAI co `nhu_cau` (thu chien luoc khong co) va
        KHONG duoc co cac truong cua mot gia thuyet.
        """
        SCC.nhat_tu_ban_doc("t", self.KY_THUAT * 4, "https://github.com/a/b", "github")
        for v in SCC.doc_kho().values():
            self.assertIn("nhu_cau", v)
            for cam in ("template", "tham_so", "gt_ma", "plan_hash", "tai_san"):
                self.assertNotIn(cam, v,
                                 f"ung vien cong cu mang truong '{cam}' cua mot "
                                 "gia thuyet giao dich")


if __name__ == "__main__":
    unittest.main()


class SanTrenHuggingFace(unittest.TestCase):
    """HF la cho co san TRONG SO da huan luyen — khac GitHub (goi de goi) va
    arXiv (phuong phap de doc).

    Voi The Brain chi co MOT cho dung duoc va no phai nam NGOAI duong ra quyet
    dinh: xep thu tu doc. Bo test nay giu dung ranh gioi do.
    """

    def test_nhu_cau_hugging_KHONG_duoc_cham_duong_quyet_dinh(self):
        nc = SCC.NHU_CAU["xep_thu_tu_doc"]
        kd = nc["khong_duoc_thay"].lower()
        for cam in ("cong.py", "ngu_phap.py"):
            self.assertIn(cam, kd,
                          f"nhu cau khong khai ro la cam cham {cam}")
        self.assertNotIn("cong.py", nc["cam_vao"].lower(),
                         "nhu cau nay cam vao duong ra quyet dinh")

    def test_moi_nhu_cau_deu_phai_khai_du_ba_truong(self):
        """Mot nhu cau thieu `khong_duoc_thay` la mot cua mo khong ai gac."""
        for ten, nc in SCC.NHU_CAU.items():
            with self.subTest(nhu_cau=ten):
                for t in ("vi_sao", "cam_vao", "khong_duoc_thay", "truy_van"):
                    self.assertIn(t, nc, f"'{ten}' thieu truong '{t}'")
                self.assertTrue(nc["truy_van"], f"'{ten}' khong co truy van nao")

    def test_dinh_tuyen_hugging_di_truoc_arxiv_va_github(self):
        """`tren_hugging` phai duoc kiem TRUOC `doi_chieu_voi`, khong thi mot
        nhu cau khai ca hai se lang le di nham duong."""
        van = (Path(LAB) / "nhan" / "san_cong_cu.py").read_text(encoding="utf-8")
        than = van[van.index("def mot_luot("):]
        i_h = than.find('if NHU_CAU[nhu_cau].get("tren_hugging")')
        i_a = than.find('elif NHU_CAU[nhu_cau].get("doi_chieu_voi")')
        i_g = than.find("tim_github(")
        self.assertNotEqual(i_h, -1, "mot_luot khong dinh tuyen HuggingFace")
        self.assertLess(i_h, i_a, "kiem doi_chieu_voi truoc tren_hugging")
        self.assertLess(i_h, i_g)

    def test_chuan_hoa_ket_qua_HF_dung_khoa_ma_cham_diem_doc(self):
        """`cham_diem` doc `stargazers_count`/`description`; doi khoa la lam cam."""
        import sys as _s
        import types

        class _R:
            status_code = 200
            @staticmethod
            def json():
                return [{"id": "abc/def", "downloads": 4321,
                         "tags": ["text-classification", "finance"]}]

        that = _s.modules.get("requests")
        _s.modules["requests"] = types.SimpleNamespace(get=lambda *a, **k: _R())
        try:
            r = SCC.tim_huggingface("x", 3)
        finally:
            if that is not None:
                _s.modules["requests"] = that
            else:
                _s.modules.pop("requests", None)
        self.assertEqual(r[0]["full_name"], "abc/def")
        self.assertEqual(r[0]["stargazers_count"], 4321)
        self.assertIn("huggingface.co/", r[0]["html_url"])

    def test_loi_mang_tra_ve_ban_ghi_LOI_chu_khong_nem_ngoai_le(self):
        """EVO goi trong vong lap 24/7: mot ngoai le o day lam dung ca luot."""
        r = SCC.tim_huggingface("x" * 3, 2)
        self.assertIsInstance(r, list)
