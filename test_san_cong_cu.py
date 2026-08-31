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
        self._dd_cu = SCC.tim_dien_dan
        self._nghi_cu = SCC.NGHI_GIAY
        SCC.NGHI_GIAY = 0.0

    def tearDown(self):
        SCC.KHO = self._kho_cu
        SCC.tim_github = self._tim_cu
        SCC.tim_arxiv = self._arxiv_cu
        SCC.tim_huggingface = self._hf_cu
        SCC.tim_dien_dan = self._dd_cu
        SCC.NGHI_GIAY = self._nghi_cu
        self._tmp.cleanup()

    def test_gieo_tay_luon_vao_kho_ke_ca_khi_mang_hong(self):
        hong = lambda *a, **k: [{"loi": "HTTP 403"}]              # noqa: E731
        SCC.tim_github = SCC.tim_arxiv = hong
        SCC.tim_huggingface = SCC.tim_dien_dan = hong
        SCC.mot_luot(gioi_han_truy_van=1, im_lang=True)
        kho = SCC.doc_kho()
        for g in SCC.GIEO_TAY:
            self.assertIn(g["full_name"], kho,
                          "cong cu chu du an chi thang bi mat khi mang hong")

    def test_khong_them_trung_khi_chay_hai_lan(self):
        # Gia lap CA BON duong: mot nhu cau co the di nhieu duong, va mot
        # duong khong gia lap se goi mang THAT -> ket qua khac nhau moi lan
        # chay va bai kiem do vi mot ly do khong lien quan den chuyen trung.
        mot = lambda *a, **k: [_repo(full_name="ai/mot-cai")]     # noqa: E731
        SCC.tim_github = SCC.tim_arxiv = mot
        SCC.tim_huggingface = SCC.tim_dien_dan = mot
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
        SCC.tim_dien_dan = lambda *a, **k: [{"loi": "ConnectionError"}]
        r = SCC.mot_luot(gioi_han_truy_van=2, im_lang=True)
        self.assertGreaterEqual(r["loi"], 1)
        self.assertIn("tong_kho", r)

    def test_kho_luu_duoc_va_doc_lai_duoc(self):
        SCC.tim_github = lambda *a, **k: [_repo(full_name="ai/luu-thu")]
        SCC.tim_arxiv = lambda *a, **k: [_repo(full_name="ai/luu-thu")]
        SCC.tim_huggingface = lambda *a, **k: [_repo(full_name="ai/luu-thu")]
        SCC.tim_dien_dan = lambda *a, **k: [_repo(full_name="ai/luu-thu")]
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
        # 31/08: phep dinh tuyen tach khoi `mot_luot` ra `_duong_cua` de
        # `_san_mot_truy_van` doc duoc mot dong. Bai kiem soi dung ham do.
        import inspect
        than = inspect.getsource(SCC._duong_cua)
        # Chuoi lui mac dinh phai giu dung thu tu: dien_dan -> hugging ->
        # arxiv -> github. Mot nhu cau khai nhieu co ma doc sai thu tu se lang
        # le di nham duong.
        i_d = than.find('nc.get("tren_dien_dan")')
        i_h = than.find('nc.get("tren_hugging")')
        i_a = than.find('nc.get("doi_chieu_voi")')
        for ten, i in (("tren_dien_dan", i_d), ("tren_hugging", i_h),
                       ("doi_chieu_voi", i_a)):
            self.assertNotEqual(i, -1, f"_duong_cua khong dinh tuyen {ten}")
        self.assertLess(i_d, i_h)
        self.assertLess(i_h, i_a)
        self.assertIn('"dien_dan"', than)
        self.assertIn("tim_huggingface(tv)", inspect.getsource(SCC._san_mot_truy_van))
        # KHAI BAO `duong` van phai thang chuoi lui mac dinh.
        self.assertEqual(SCC._duong_cua({"duong": ["github"],
                                         "tren_hugging": True}), ["github"])
        self.assertEqual(SCC._duong_cua({"tren_hugging": True,
                                         "doi_chieu_voi": "nhan/cong.py"}),
                         ["hugging"])

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


class HFPhaiDuocCHAMDIEMCongBang(unittest.TestCase):
    """HF khong tra `license`/`pushed_at` nhu GitHub.

    Khong anh xa thi `cham_diem` doc ra "khong khai giay phep" va "lan day cuoi
    9999 ngay truoc" cho MOI mo hinh — tuc phat oan ca mot nguon, va no im
    lang: diem van ra mot con so, chi la con so sai.
    """

    @staticmethod
    def _goi(items):
        import sys as _s, types

        class _R:
            status_code = 200
            @staticmethod
            def json(): return items

        that = _s.modules.get("requests")
        _s.modules["requests"] = types.SimpleNamespace(get=lambda *a, **k: _R())
        try:
            return SCC.tim_huggingface("x", 5)
        finally:
            if that is not None:
                _s.modules["requests"] = that

    def test_giay_phep_lay_duoc_tu_tag_license(self):
        r = self._goi([{"id": "a/b", "downloads": 10,
                        "tags": ["license:apache-2.0", "text-classification"]}])
        self.assertEqual((r[0]["license"] or {}).get("spdx_id"), "apache-2.0")

    def test_khong_co_tag_license_thi_la_None_chu_khong_bia(self):
        r = self._goi([{"id": "a/b", "downloads": 10, "tags": ["x"]}])
        self.assertIsNone(r[0]["license"])

    def test_ngay_sua_lay_tu_lastModified(self):
        r = self._goi([{"id": "a/b", "downloads": 1,
                        "lastModified": "2026-08-01T00:00:00.000Z", "tags": []}])
        self.assertTrue(str(r[0]["pushed_at"]).startswith("2026-08-01"))

    def test_cham_diem_chay_duoc_tren_ban_ghi_HF(self):
        r = self._goi([{"id": "a/b", "downloads": 50_000, "likes": 120,
                        "lastModified": "2026-08-01T00:00:00.000Z",
                        "tags": ["license:mit"]}])
        d = SCC.cham_diem(r[0])
        self.assertIsInstance(d, (int, float, dict, tuple, list))


class XemKhongDuocVOViMotBanGhiThieuKhoa(unittest.TestCase):
    """Kho co ban ghi tu nhieu duong; mot ban thieu khoa da lam vo ca man hinh."""

    def test_xem_chay_duoc_khi_co_ban_ghi_thieu_full_name(self):
        import tempfile, json as _j
        from pathlib import Path as _P
        cu = SCC.KHO
        with tempfile.TemporaryDirectory() as tmp:
            SCC.KHO = _P(tmp) / "k.json"
            SCC.KHO.write_text(_j.dumps({
                "a/b": {"full_name": "a/b", "nhu_cau": "doc_pdf", "diem": 50},
                "loi": {"nhu_cau": "doc_pdf", "url": "https://x/y", "diem": 10},
            }), encoding="utf-8")
            import io as _io
            from contextlib import redirect_stdout
            buf = _io.StringIO()
            try:
                with redirect_stdout(buf):
                    SCC.xem(10)
            finally:
                SCC.KHO = cu
        ra = buf.getvalue()
        self.assertIn("a/b", ra, "ban ghi lanh lan cung khong hien ra")
        self.assertIn("https://x/y", ra,
                      "ban ghi thieu full_name bi bo qua im lang thay vi hien url")


class DuongDIENDAN(unittest.TestCase):
    """Duong thu tu cua EVO, va no khac ba duong kia ve BAN CHAT cai tim duoc.

        GitHub      -> mot goi de goi
        arXiv       -> mot phuong phap de doc
        HuggingFace -> mot bo trong so da huan luyen
        Dien dan    -> mot KINH NGHIEM: cai gi cham, vi sao, ai da vap

    Phan lon nut that cua The Brain khong giai bang mot thu vien moi ma bang
    mot cau "hoa ra `os.stat` goi 80.000 lan/phut" — thu chi nam trong bai viet
    va cau tra loi cua nguoi khac. Chu du an chi 30/08/2026: EVO nam RONG HON
    linh vuc giao dich.
    """

    @staticmethod
    def _goi(hn=None, so=None):
        import types, urllib.request as _ur, json as _j

        class _F:
            def __init__(self, b): self.b = b
            def read(self): return self.b
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def gia(rq, timeout=0):
            u = rq.full_url if hasattr(rq, "full_url") else str(rq)
            if "algolia" in u:
                if hn is None:
                    raise OSError("chan")
                return _F(_j.dumps({"hits": hn}).encode())
            if "stackexchange" in u:
                if so is None:
                    raise OSError("chan")
                return _F(_j.dumps({"items": so}).encode())
            raise OSError("chan")

        goc = _ur.urlopen
        _ur.urlopen = gia
        try:
            return SCC.tim_dien_dan("x", 5)
        finally:
            _ur.urlopen = goc

    def test_gop_ket_qua_tu_CA_HAI_dien_dan(self):
        r = self._goi(hn=[{"title": "a", "url": "http://a", "points": 9}],
                      so=[{"title": "b", "link": "http://b", "score": 4}])
        nguon = {x.get("_nguon") for x in r}
        self.assertEqual(nguon, {"hackernews", "stackoverflow"})

    def test_diem_cua_moi_dien_dan_quy_ve_MOT_khoa(self):
        """`cham_diem` chi doc `stargazers_count`; moi dien dan mot khoa la lam cam."""
        r = self._goi(hn=[{"title": "a", "url": "http://a", "points": 9}],
                      so=[{"title": "b", "link": "http://b", "score": 4}])
        self.assertEqual({x["stargazers_count"] for x in r}, {9, 4})

    def test_MOT_dien_dan_hong_van_lay_duoc_cua_dien_dan_kia(self):
        """Chot quan trong: mot nguon chan khong duoc lam mat ca luot."""
        r = self._goi(hn=None, so=[{"title": "b", "link": "http://b", "score": 4}])
        that = [x for x in r if "loi" not in x]
        self.assertEqual(len(that), 1)
        self.assertEqual(that[0]["_nguon"], "stackoverflow")

    def test_CA_HAI_hong_thi_bao_LOI_chu_khong_bao_rong(self):
        """'Khong tim thay gi' va 'khong voi toi duoc' phai la hai cau khac nhau."""
        r = self._goi(hn=None, so=None)
        self.assertTrue(r and "loi" in r[0],
                        "ca hai dien dan chan ma bao nhu la khong co ket qua")
        self.assertIn("voi toi", r[0]["loi"])

    def test_HOI_DUOC_ma_khong_co_gi_thi_tra_RONG_chu_khong_phai_LOI(self):
        """Chieu con lai, va no la chieu de sai hon.

        Ban dau (30/08/2026) toi viet ca hai truong hop deu tra
        `[{"loi": "khong dien dan nao tra ve ket qua"}]`. EVO se ghi mot truy
        van hop le nhung khong trung gi thanh LOI MANG, roi thu lai mai mot
        truy van that su khong co cau tra loi — dung hinh dang cua bay
        "chua do" bi ghi thanh "do roi ma khong co", chi la nguoc chieu.
        """
        r = self._goi(hn=[], so=[])
        self.assertEqual(r, [], "hoi duoc ca hai ma bao la loi mang")


class NhuCauKYTHUATPhaiGanVoiNutThatDADO(unittest.TestCase):
    """EVO rong hon linh vuc giao dich, nhung khong duoc rong thanh vo dinh.

    Moi nhu cau ky thuat phai gan voi mot nut that DA DO DUOC tren may nay -
    do la ly do no dang mot suat tim kiem, con "lam cho he nhanh hon" thi khong.
    """

    KY_THUAT = ("do_nut_that", "song_song_va_bo_nho", "nhanh_hon_so_hoc",
                "luu_tru_va_doc_gia", "chay_lau_dai_khong_nguoi_truc")

    def test_du_nam_nhu_cau_ky_thuat(self):
        for k in self.KY_THUAT:
            self.assertIn(k, SCC.NHU_CAU)

    def test_moi_nhu_cau_ky_thuat_deu_dan_MOT_CON_SO_da_do(self):
        import re
        for k in self.KY_THUAT:
            with self.subTest(nhu_cau=k):
                self.assertRegex(
                    SCC.NHU_CAU[k]["vi_sao"], r"\d",
                    "vi_sao khong dan mot con so nao - do la mong muon chung "
                    "chung, khong phai nut that da do")

    def test_khong_nhu_cau_ky_thuat_nao_duoc_cham_duong_quyet_dinh(self):
        for k in self.KY_THUAT:
            with self.subTest(nhu_cau=k):
                kd = SCC.NHU_CAU[k]["khong_duoc_thay"].lower()
                self.assertTrue(len(kd) > 20, "khai rang buoc qua so sai")
                self.assertNotIn("cong.py", SCC.NHU_CAU[k]["cam_vao"].lower())

    def test_duong_khai_ra_deu_la_duong_co_that(self):
        hop_le = {"github", "arxiv", "hugging", "dien_dan"}
        for k, v in SCC.NHU_CAU.items():
            for d in (v.get("duong") or []):
                with self.subTest(nhu_cau=k, duong=d):
                    self.assertIn(d, hop_le, f"duong '{d}' khong ton tai")


# =====================================================================
# NOI SO VAN DE VAO TRUY VAN SAN (31/08/2026)
#
# Cho toi 30/08 `san_cong_cu` di theo mot danh sach NHU_CAU **tinh**: viet
# mot lan roi khong bao gio doi, va khong biet gi ve tinh trang cua chinh
# day chuyen no phuc vu. Ket qua do duoc cua luot gan nhat:
# `tim_them=0, loi=3` - lap lai y het moi 12 gio.
#
# Hai bo test duoi day khoa hai nguyen nhan that, va ca hai deu la BIEN THE
# CUA CUNG MOT CAI BAY ("chua do duoc" bi ghi thanh "do roi, bang 0"):
#   - `RONGKhongPhaiLOI`: hoi duoc ma khong co ket qua bi dem la LOI MANG.
#   - `HangDoiTruyVanPhaiXOAY`: truy van khong ra ket qua khong de lai vet
#     nao, nen lan sau lai chon dung no - 17 truy van con lai khong bao gio
#     den luot.
# =====================================================================
class NoiVanDeVaoNhuCau(unittest.TestCase):

    @staticmethod
    def _vd(ma, muc="NANG"):
        return {"ma": ma, "muc": muc, "mo_ta": "..."}

    def test_khong_co_van_de_nao_thi_khong_sinh_nhu_cau_nao(self):
        self.assertEqual(SCC.nhu_cau_tu_van_de([]), {})
        self.assertEqual(SCC.nhu_cau_tu_van_de(None), {})

    def test_van_de_muc_VUA_KHONG_duoc_tieu_mot_suat_tim_kiem(self):
        """Suat tim kiem la co han. 'Cai gi cung dang di tim' = khong tim."""
        self.assertEqual(SCC.nhu_cau_tu_van_de([self._vd("vd_null_qua_nho", "VUA")]), {})

    def test_van_de_NANG_co_anh_xa_thi_sinh_ra_truy_van(self):
        r = SCC.nhu_cau_tu_van_de([self._vd("vd_null_qua_nho")])
        self.assertIn("nha_may_null_qua_nho", r)
        self.assertTrue(r["nha_may_null_qua_nho"]["truy_van"])
        self.assertEqual(r["nha_may_null_qua_nho"]["tu_van_de"], ["vd_null_qua_nho"])

    def test_hai_ma_van_de_cung_tro_toi_MOT_nhu_cau_thi_gop_lai(self):
        r = SCC.nhu_cau_tu_van_de([self._vd("vd_null_qua_nho"),
                                   self._vd("chua_hieu_chuan_null")])
        self.assertEqual(len(r), 1)
        self.assertEqual(sorted(r["nha_may_null_qua_nho"]["tu_van_de"]),
                         ["chua_hieu_chuan_null", "vd_null_qua_nho"])

    def test_ma_van_de_la_khong_biet_thi_bo_qua_chu_khong_vo(self):
        self.assertEqual(SCC.nhu_cau_tu_van_de([self._vd("mot_ma_chua_tung_co")]), {})

    def test_moi_anh_xa_deu_tro_toi_mot_nhu_cau_CO_THAT(self):
        for ma, nc in SCC.VAN_DE_SANG_NHU_CAU.items():
            with self.subTest(van_de=ma):
                self.assertIn(nc, SCC.NHU_CAU_TU_VAN_DE,
                              f"van de '{ma}' tro toi nhu cau '{nc}' khong ton tai")

    def test_moi_nhu_cau_dong_deu_khai_du_ranh_gioi_nhu_nhu_cau_tinh(self):
        for ten, v in SCC.NHU_CAU_TU_VAN_DE.items():
            with self.subTest(nhu_cau=ten):
                for truong in ("vi_sao", "cam_vao", "khong_duoc_thay"):
                    self.assertTrue((v.get(truong) or "").strip(),
                                    f"nhu cau '{ten}' thieu '{truong}'")
                self.assertTrue(v.get("truy_van"), f"nhu cau '{ten}' khong co truy van")

    def test_khong_nhu_cau_dong_nao_nham_thay_ONG_TOA(self):
        cam = ("cong.py", "do_luc.py", "so.py", "quant_plan.py", "canary.py")
        for ten, v in SCC.NHU_CAU_TU_VAN_DE.items():
            for tep in cam:
                with self.subTest(nhu_cau=ten, tep=tep):
                    self.assertNotIn(
                        tep, v["cam_vao"].lower(),
                        f"nhu cau '{ten}' khai cam vao '{tep}' - do la ong toa")

    def test_duong_cua_nhu_cau_dong_deu_la_duong_co_that(self):
        hop_le = {"github", "arxiv", "hugging", "dien_dan"}
        for k, v in SCC.NHU_CAU_TU_VAN_DE.items():
            for d in (v.get("duong") or []):
                with self.subTest(nhu_cau=k, duong=d):
                    self.assertIn(d, hop_le)

    def test_ma_vd_dung_chung_voi_tru_evolution_khong_duoc_lech(self):
        """Hai file dung chung mot bo chuoi. Doi mot ben la dut lien ket.

        `tru/evolution.py` dat ma chu de chuan; `nhan/san_cong_cu.py` anh xa
        chung sang nhu cau. Neu ai do doi ten mot chu de ma quen ben kia thi
        van de van mo, nhu cau lang le khong bao gio duoc sinh, va khong mot
        loi nao xuat hien.
        """
        from tru import evolution as EVO
        co_that = {ma for ma, _ in EVO.CHU_DE_VAN_DE}
        for ma in SCC.VAN_DE_SANG_NHU_CAU:
            if not ma.startswith("vd_"):
                continue
            with self.subTest(chu_de=ma):
                self.assertIn(ma, co_that,
                              f"'{ma}' khong con trong EVO.CHU_DE_VAN_DE")


class RONGKhongPhaiLOI(unittest.TestCase):
    """Nguyen nhan THAT cua `loi=3` o luot san 30/08.

    Do lai tung truy van ngay 31/08:
      `memory bandwidth bound numpy multiprocessing` -> HN + SO deu tra loi, 0 hit
      `numba vectorized backtest speedup`            -> GitHub tra loi, 0 hit
      `polars vs pandas time series performance`     -> GitHub tra loi, 0 hit

    Ca ba deu CHAY TOT. `mot_luot` cu bien chung thanh loi bang dong
    `ds[:1] or [{"loi": "khong duong nao tra ve"}]`: mot danh sach RONG bi
    thay bang mot ban ghi LOI bia ra.
    """

    def setUp(self):
        self._cu = (SCC.tim_github, SCC.tim_arxiv, SCC.tim_huggingface,
                    SCC.tim_dien_dan)

    def tearDown(self):
        (SCC.tim_github, SCC.tim_arxiv, SCC.tim_huggingface,
         SCC.tim_dien_dan) = self._cu

    def test_hoi_duoc_ma_khong_co_ket_qua_la_RONG_chu_khong_phai_LOI(self):
        SCC.tim_github = lambda *a, **k: []
        _, tk = SCC._san_mot_truy_van({"duong": ["github"]}, "x")
        self.assertEqual(tk["ket"], "RONG")
        self.assertEqual(tk["duong_hong"], [])

    def test_khong_duong_nao_voi_toi_duoc_moi_la_LOI(self):
        SCC.tim_github = lambda *a, **k: [{"loi": "HTTP 403"}]
        _, tk = SCC._san_mot_truy_van({"duong": ["github"]}, "x")
        self.assertEqual(tk["ket"], "LOI")
        self.assertTrue(tk["duong_hong"])

    def test_mot_duong_hong_mot_duong_tra_ve_rong_van_la_RONG(self):
        SCC.tim_github = lambda *a, **k: [{"loi": "HTTP 403"}]
        SCC.tim_dien_dan = lambda *a, **k: []
        _, tk = SCC._san_mot_truy_van({"duong": ["github", "dien_dan"]}, "x")
        self.assertEqual(tk["ket"], "RONG")
        self.assertTrue(tk["duong_hong"], "duong hong bi nuot, khong ai biet")

    def test_co_ket_qua_thi_la_CO_KET_QUA(self):
        SCC.tim_github = lambda *a, **k: [_repo()]
        ds, tk = SCC._san_mot_truy_van({"duong": ["github"]}, "x")
        self.assertEqual(tk["ket"], "CO_KET_QUA")
        self.assertEqual(len(ds), 1)

    def test_ghi_kem_so_tu_va_sao_toi_thieu_de_doc_lai_duoc_vi_sao_RONG(self):
        SCC.tim_github = lambda *a, **k: []
        _, tk = SCC._san_mot_truy_van({"duong": ["github"], "sao_toi_thieu": 800},
                                      "numba vectorized backtest speedup")
        self.assertEqual(tk["so_tu"], 4)
        self.assertEqual(tk["sao_toi_thieu"], 800)


class HangDoiTruyVanPhaiXOAY(unittest.TestCase):
    """Truy van khong ra ket qua phai de lai VET, neu khong no bi thu lai mai.

    Do that 31/08: 27 truy van khai bao, 20 chua tung ra ket qua, va vi
    `da_lam` duoc suy tu KHO KET QUA nen `mot_luot(gioi_han=3)` lan nao cung
    chon dung ba truy van dau. 17 truy van con lai khong bao gio den luot.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._kho_cu, self._nghi_cu = SCC.KHO, SCC.NGHI_GIAY
        SCC.KHO = Path(self._tmp.name) / "cong_cu.json"
        SCC.NGHI_GIAY = 0.0
        self._cu = (SCC.tim_github, SCC.tim_arxiv, SCC.tim_huggingface,
                    SCC.tim_dien_dan)
        rong = lambda *a, **k: []                                 # noqa: E731
        SCC.tim_github = SCC.tim_arxiv = rong
        SCC.tim_huggingface = SCC.tim_dien_dan = rong

    def tearDown(self):
        SCC.KHO, SCC.NGHI_GIAY = self._kho_cu, self._nghi_cu
        (SCC.tim_github, SCC.tim_arxiv, SCC.tim_huggingface,
         SCC.tim_dien_dan) = self._cu
        self._tmp.cleanup()

    def test_truy_van_ra_RONG_van_duoc_ghi_vao_so(self):
        SCC.mot_luot(gioi_han_truy_van=2, im_lang=True)
        so = SCC.doc_so_truy_van()
        self.assertEqual(len(so), 2)
        self.assertEqual({g["ket"] for g in so.values()}, {"RONG"})

    def test_luot_sau_chon_truy_van_KHAC_chu_khong_lap_lai_ba_cai_cu(self):
        SCC.mot_luot(gioi_han_truy_van=3, im_lang=True)
        dot1 = set(SCC.doc_so_truy_van())
        SCC.mot_luot(gioi_han_truy_van=3, im_lang=True)
        dot2 = set(SCC.doc_so_truy_van()) - dot1
        self.assertEqual(len(dot2), 3,
                         "luot hai lam lai dung nhung truy van cua luot mot")

    def test_truy_van_LOI_duoc_thu_lai_som_hon_truy_van_RONG(self):
        self.assertLess(SCC.CHU_KY_THU_LAI["LOI"], SCC.CHU_KY_THU_LAI["RONG"],
                        "loi mang va 'khong ai viet ve chuyen nay' bi doi xu nhu nhau")

    def test_moi_truy_van_deu_trong_ky_cho_thi_tim_them_la_None_CHU_KHONG_0(self):
        """Bay `da_quet=0` bi bao thanh 'khong bo nao thang', chieu san cong cu."""
        while True:
            r = SCC.mot_luot(gioi_han_truy_van=8, im_lang=True)
            if r["tim_them"] is None:
                break
            self.assertGreater(r["da_thu"], 0)
        self.assertIsNone(r["tim_them"])
        self.assertEqual(r["da_thu"], 0)
        self.assertEqual(r["con_cho"], len(SCC.doc_so_truy_van()))

    def test_van_de_dang_mo_day_truy_van_cua_no_LEN_TRUOC(self):
        vd = [{"ma": "vd_null_qua_nho", "muc": "NANG", "mo_ta": "..."}]
        SCC.mot_luot(gioi_han_truy_van=2, im_lang=True, van_de_mo=vd)
        da_thu = set(SCC.doc_so_truy_van())
        self.assertTrue(
            da_thu <= set(SCC.NHU_CAU_TU_VAN_DE["nha_may_null_qua_nho"]["truy_van"]),
            f"truy van sinh tu van de khong duoc uu tien: {da_thu}")

    def test_khong_truyen_van_de_thi_chi_san_theo_danh_sach_TINH(self):
        SCC.mot_luot(gioi_han_truy_van=2, im_lang=True)
        tinh = {tv for v in SCC.NHU_CAU.values() for tv in v["truy_van"]}
        self.assertTrue(set(SCC.doc_so_truy_van()) <= tinh)


class HangDoiDOC(unittest.TestCase):
    """Bon kho ma phai DOI CHIEU voi cong, khong bao gio THAY cong."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._kho_cu = SCC.KHO
        SCC.KHO = Path(self._tmp.name) / "cong_cu.json"

    def tearDown(self):
        SCC.KHO = self._kho_cu
        self._tmp.cleanup()

    def test_KHONG_CHAY_khi_kho_khong_co_kho_ma_nao_khop(self):
        """Dieu kien khong thoa thi khong doi mot truong nao."""
        SCC.luu_kho({"ai/khong-lien-quan": {"full_name": "ai/khong-lien-quan",
                                            "trang_thai": "MOI"}})
        self.assertEqual(SCC.xep_hang_doc(), [])
        self.assertEqual(SCC.doc_kho()["ai/khong-lien-quan"]["trang_thai"], "MOI")
        self.assertEqual(SCC.dang_cho_doc(), [])

    def test_danh_dau_dung_kho_ma_da_khai_bao(self):
        kho = {m["khop"]: {"full_name": m["khop"], "trang_thai": "MOI"}
               for m in SCC.HANG_DOI_DOC}
        kho["ai/khac"] = {"full_name": "ai/khac", "trang_thai": "MOI"}
        SCC.luu_kho(kho)
        self.assertEqual(len(SCC.xep_hang_doc()), len(SCC.HANG_DOI_DOC))
        self.assertEqual(len(SCC.dang_cho_doc()), len(SCC.HANG_DOI_DOC))
        self.assertEqual(SCC.doc_kho()["ai/khac"]["trang_thai"], "MOI")

    def test_chay_lai_khong_lam_hang_doi_phinh(self):
        kho = {}
        for i, m in enumerate(SCC.HANG_DOI_DOC):
            # Kho THAT co nhieu ban ghi cho cung mot kho ma (nhat tu nhieu bai
            # doc khac nhau). Da sap that 31/08: moi luot lai danh dau them mot
            # ban, hang doi doc tu 4 len 7 chi sau hai luot.
            for j in range(3):
                kho[f"doc:x{i}{j}:{m['khop']}"] = {
                    "url": f"https://github.com/{m['khop']}", "trang_thai": "MOI"}
        SCC.luu_kho(kho)
        SCC.xep_hang_doc()
        n1 = len(SCC.dang_cho_doc())
        SCC.xep_hang_doc()
        SCC.xep_hang_doc()
        self.assertEqual(len(SCC.dang_cho_doc()), n1)
        self.assertEqual(n1, len(SCC.HANG_DOI_DOC))

    def test_moi_muc_deu_noi_ro_doi_chieu_voi_FILE_NAO(self):
        for m in SCC.HANG_DOI_DOC:
            with self.subTest(kho=m["khop"]):
                self.assertTrue(m["doi_chieu_voi"].strip())
                self.assertTrue(m["vi_sao"].strip())
                self.assertIn(".py", m["doi_chieu_voi"],
                              "khong chi ra file nao trong lab de doi chieu")
