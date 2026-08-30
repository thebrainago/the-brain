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
        self._tim_cu = SCC.tim_github
        self._nghi_cu = SCC.NGHI_GIAY
        SCC.NGHI_GIAY = 0.0

    def tearDown(self):
        SCC.KHO = self._kho_cu
        SCC.tim_github = self._tim_cu
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
        SCC.tim_github = lambda *a, **k: [{"loi": "ConnectionError"}]
        r = SCC.mot_luot(gioi_han_truy_van=2, im_lang=True)
        self.assertGreaterEqual(r["loi"], 1)
        self.assertIn("tong_kho", r)

    def test_kho_luu_duoc_va_doc_lai_duoc(self):
        SCC.tim_github = lambda *a, **k: [_repo(full_name="ai/luu-thu")]
        SCC.mot_luot(gioi_han_truy_van=1, im_lang=True)
        lai = json.loads(SCC.KHO.read_text(encoding="utf-8"))
        self.assertIn("ai/luu-thu", lai)
        self.assertEqual(lai["ai/luu-thu"]["trang_thai"], "MOI")


if __name__ == "__main__":
    unittest.main()
