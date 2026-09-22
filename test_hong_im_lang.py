# -*- coding: utf-8 -*-
"""BA CHO CON HONG TRONG IM LANG - tim 19/09/2026 bang mot luot kiem toan.

Loi nguy hiem nhat cua du an nay khong phai crash - la mot khau DO hong nhung
tra ve gia tri trong nhu ket qua hop le. `qwen/cong.py` liet ke bon lan da tra
gia: het quota -> "0/20 co che" · lech ten provider -> doc nhu am · 406 URL
chet -> "het ton kho" · `da_quet=0` -> "khong bo nao thang".

Ba cho duoi day cung mot benh, va deu con song trong `nhan/`.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from nhan import cong as CONG
from nhan import du_lieu as DU


class SoDongCuaFileHONG(unittest.TestCase):
    """`so_dong_goc` tra 0 khi khong doc duoc - doc y het mot file rong that.

    Ham nay nuoi `ban["so_dong"]` va `uoc_so_nam` cua `kho()`. Mot parquet
    hong se vao ban do du lieu voi "0 dong, 0 nam" - va `kho()` CHON BAN THEO
    DO PHU, nen mot file hong khong chi bi bo qua: no co the day mot ma tut
    xuong hang hoac lam ca ma do bien khoi danh sach chay duoc.
    """

    def test_file_HONG_tra_None_chu_khong_tra_0(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tm:
            p = Path(tm) / "hong.parquet"
            p.write_bytes(b"day khong phai parquet")
            self.assertIsNone(DU.so_dong_goc(p),
                              "file hong doc y het file rong")

    def test_file_KHONG_TON_TAI_cung_tra_None(self):
        self.assertIsNone(DU.so_dong_goc(Path("/khong/he/co/file.parquet")))


class KiemKS_KhongDoDuocKhacVoiDoDuoc(unittest.TestCase):
    """`kiem_ks` tra 1.0 cho CA HAI: "null giong that" va "khong do duoc".

    Hau qua doc duoc thang trong `nhan/cong.py`: `bs_hop_le = min(ks) > 0,01`.
    Tra 1,0 khi hong nghia la null BOOTSTRAP duoc NHAN la hop le, va cac
    p-value cua no o lai trong ket luan - tuc mot null co the sai hoan toan
    van duoc dung de phan xu mot chien luoc.

    Day la cong hieu chuan null. Mot cong hieu chuan tu nhan minh "dat" khi no
    khong chay duoc la cong nguy hiem hon khong co cong.
    """

    def test_qua_it_mau_tra_None_chu_khong_tra_1(self):
        v = np.zeros(20)
        v[3] = 1.0
        self.assertIsNone(CONG.kiem_ks(v, v))

    def test_do_duoc_thi_van_tra_so(self):
        """Hieu chuan chieu nguoc: sua xong ma khong con do duoc gi thi do la
        mot cong bi tat, khong phai mot cong da sua."""
        rng = np.random.default_rng(3)
        a = (rng.random(4000) < 0.05).astype(float)
        b = (rng.random(4000) < 0.05).astype(float)
        p = CONG.kiem_ks(a, b)
        self.assertIsNotNone(p)
        self.assertGreaterEqual(p, 0.0)
        self.assertLessEqual(p, 1.0)

    def test_hai_phan_phoi_KHAC_HAN_thi_p_thap(self):
        rng = np.random.default_rng(4)
        a = (rng.random(4000) < 0.02).astype(float)
        b = (rng.random(4000) < 0.40).astype(float)
        p = CONG.kiem_ks(a, b)
        self.assertIsNotNone(p)
        self.assertLess(p, 0.05, "null khac han that ma KS khong phat hien")


class GhiVanDeKhongDuocNUOT_LOI(unittest.TestCase):
    """`evo.ghi_van_de` con mot `except: return 0` o lan import dau.

    Chinh docstring cua ham nay ghi lai lan loi do da xay ra: *"Loi bi `except`
    nuot va EVO in 'ghi 0 van de moi' - doc nhu ket qua binh thuong."* Nguoi
    sua da va `try` THU HAI (no in ly do) nhung bo sot `try` thu nhat.
    """

    def test_khong_con_except_return_0_o_import_dau(self):
        import inspect

        from nhan import evo as EVO
        src = inspect.getsource(EVO.ghi_van_de)
        dau = src.split("# DUNG `tru/evolution.bao_van_de_gop`")[0]
        self.assertNotIn("return 0", dau,
                         "loi import bi nuot roi tra 0 - doc nhu 'khong co "
                         "van de moi'")

    def test_van_de_rong_van_tra_0_binh_thuong(self):
        """Hieu chuan chieu nguoc: KHONG co van de nao that su thi van la 0."""
        from nhan import evo as EVO
        self.assertEqual(EVO.ghi_van_de([], in_ra=None), 0)


class SpreadCU_PHAI_TU_KHAI_LA_CU(unittest.TestCase):
    """`chi_phi.spread_cua` tra ban CU khi khong do lai duoc - khong noi gi.

    Duong di: ban luu con han thi tra ngay. Het han thi goi
    `do_spread_tu_bar_mt5`; MT5 khong cai / khong dang nhap / san tu choi thi
    ham do tra `None`, va `spread_cua` LANG LE tra lai ban cu da het han.

    Ban cu co truong `do_luc` nen tuoi cua no KHONG bi giau - nhung khong ai
    buoc phai nhin. Mot con so spread ba thang tuoi doc y het mot con so vua do
    xong, va spread la dau vao cua moi phep tinh lai/lo.

    Sua: khong doi hanh vi (tra ban cu van dung - co con hon khong), chi THEM
    truong de ben doc phan biet duoc.
    """

    def test_ban_cu_mang_co_KHONG_DO_LAI_DUOC(self):
        from nhan import chi_phi as CP
        cu = {"spread_bps": 1.2, "do_luc": "2020-01-01 00:00:00"}
        r = CP._danh_dau_cu(cu, do_lai_duoc=False)
        self.assertIs(r["do_lai_duoc"], False)
        self.assertGreater(r["tuoi_gio"], 24 * 365)

    def test_ban_VUA_DO_thi_khong_bi_danh_dau_nham(self):
        """Hieu chuan chieu nguoc."""
        import time
        from nhan import chi_phi as CP
        moi = {"spread_bps": 1.2,
               "do_luc": time.strftime("%Y-%m-%d %H:%M:%S")}
        r = CP._danh_dau_cu(moi, do_lai_duoc=True)
        self.assertIs(r["do_lai_duoc"], True)
        self.assertLess(r["tuoi_gio"], 1.0)

    def test_khong_co_do_luc_thi_tuoi_la_None_chu_khong_phai_0(self):
        from nhan import chi_phi as CP
        r = CP._danh_dau_cu({"spread_bps": 1.2}, do_lai_duoc=False)
        self.assertIsNone(r["tuoi_gio"], "khong biet tuoi ma bao 0 gio la noi doi")


class LopDoiChungKhongDuocIM_LANG_RONG(unittest.TestCase):
    """`quantlab._lop_doi_chung` tra `set()` khi import hong.

    `set()` rong lam `lop in _lop_doi_chung()` LUON sai, nen moi lop deu dung
    `TRAN_MOI_LOP` thay vi `TRAN_LOP_DOI_CHUNG`. Thuat toan chon tai san doi
    hoan toan ma khong mot dong nao bao - va chinh docstring cua
    `_tai_san_kha_dung` ke lai mot lan y het the: mot dieu kien khong bao gio
    dung lam ca he chi nhin thay 11 tai san trong khi kho co 80.
    """

    def test_import_hong_thi_NEM_LOI_chu_khong_tra_rong(self):
        """Phai go CA HAI cho: `sys.modules` VA thuoc tinh cua goi `nhan`.

        `from nhan import pham_vi` thu `getattr(nhan, "pham_vi")` TRUOC khi hoi
        `sys.modules`. Neu module da tung duoc nap thi thuoc tinh do co san, va
        chi dat `sys.modules[...] = None` thi phep import van thanh cong -
        bai test se "dat" ma khong kiem duoc gi.

        Do dung la cho bai nay truot luc dau: chay mot minh thi xanh (chua ai
        nap `pham_vi`), chay ca file thi do.
        """
        import sys as _s
        from tru import quantlab as QL
        import nhan as _goi
        cu_m = _s.modules.get("nhan.pham_vi", "_KHONG_CO_")
        cu_a = getattr(_goi, "pham_vi", "_KHONG_CO_")
        _s.modules["nhan.pham_vi"] = None
        if cu_a != "_KHONG_CO_":
            delattr(_goi, "pham_vi")
        try:
            with self.assertRaises(ImportError):
                QL._lop_doi_chung()
        finally:
            if cu_m == "_KHONG_CO_":
                _s.modules.pop("nhan.pham_vi", None)
            else:
                _s.modules["nhan.pham_vi"] = cu_m
            if cu_a != "_KHONG_CO_":
                setattr(_goi, "pham_vi", cu_a)

    def test_binh_thuong_van_tra_ve_duoc(self):
        from tru import quantlab as QL
        self.assertIsInstance(QL._lop_doi_chung(), set)


class ConTroHONG_khac_CON_TRO_0(unittest.TestCase):
    """`_doc_con_tro` tra 0 khi khong doc duoc - doc y het "bat dau tu dau".

    He se quet lai tu artifact 0: ton cong, va moi ung vien cu duoc xep lai vao
    hang doi mot lan nua. So ung vien phinh len ma khong ai biet vi sao.
    """

    def test_file_hong_tra_None_chu_khong_tra_0(self):
        import tempfile
        from pathlib import Path as _P

        from nhan import bien_dich_ung_vien as BD
        cu = BD.CON_TRO
        with tempfile.TemporaryDirectory() as tm:
            p = _P(tm) / "con_tro.json"
            p.write_text("{khong phai json}", encoding="utf-8")
            BD.CON_TRO = p
            try:
                self.assertIsNone(BD._doc_con_tro())
            finally:
                BD.CON_TRO = cu

    def test_con_tro_THAT_bang_0_van_doc_ra_0(self):
        """Hieu chuan chieu nguoc: 0 that la mot gia tri hop le."""
        import json as _j
        import tempfile
        from pathlib import Path as _P

        from nhan import bien_dich_ung_vien as BD
        cu = BD.CON_TRO
        with tempfile.TemporaryDirectory() as tm:
            p = _P(tm) / "con_tro.json"
            p.write_text(_j.dumps({"artifact_id": 0}), encoding="utf-8")
            BD.CON_TRO = p
            try:
                self.assertEqual(BD._doc_con_tro(), 0)
            finally:
                BD.CON_TRO = cu


class MOI_DIEU_KIEN_CONG_PHAI_DUOC_XEP_LOAI(unittest.TestCase):
    """Them mot dieu kien vao cong ma quen xep loai thi CONG NEM LOI.

    Do 19/09/2026: `12_rr_thuc_te` va `13_edge_vuot_spread` duoc them vao ma
    khong ai xep, nen `cong.xet` nem `KeyError` o che do "nhan" - tuc che do
    MAC DINH. Ba bai test cua `test_cong_fdr_v2` do vi ly do nay.

    Chinh ghi chu cua `CHAN_CUNG` da noi truoc: *"Liet ke tuong minh de them
    mot dieu kien moi khong tu dong roi vao ben nao ma khong ai quyet dinh."*
    Co che canh bao hoat dong dung - chi la khong ai sua sau khi no keu.
    """

    def test_khong_con_dieu_kien_nao_chua_xep_loai(self):
        import inspect
        import re

        from nhan import cong as CONG
        src = inspect.getsource(CONG.xet)
        khoa = set(re.findall(r'dk\["(\d+_[a-z_0-9]+)"\]\s*=', src))
        self.assertTrue(khoa, "khong tim thay dieu kien nao - doi cach doc")
        thieu = sorted(k for k in khoa
                       if k not in CONG.NHAN_MEM and k not in CONG.CHAN_CUNG)
        self.assertEqual(thieu, [], "dieu kien chua xep chan/nhan: %s" % thieu)

    def test_RR_THUC_TE_la_NHAN_khong_phai_CHAN(self):
        """Dat no lam chan cung se chan chinh he da ra tien nhat cua du an.

        RR thuc te thap la hinh dang cua mot cai LUOI - nhieu lenh thang nho,
        it lenh thua sau - va AUDCAD 18/09 cho holdout +13,26%/nam voi dung
        profile do. LUAT SO 0: chi chan o cau hoi TIEN; RR khong tra loi cau
        hoi do, `nguy_co_chay` va sut giam moi tra loi.
        """
        from nhan import cong as CONG
        self.assertIn("12_rr_thuc_te", CONG.NHAN_MEM)
        self.assertNotIn("12_rr_thuc_te", CONG.CHAN_CUNG)

    def test_EDGE_VUOT_SPREAD_la_CHAN_CUNG(self):
        """Day LA cau hoi tien: mot edge mong hon chi phi thi khong ton tai
        ngoai doi, va khong muc chap nhan rui ro nao cuu duoc no."""
        from nhan import cong as CONG
        self.assertIn("13_edge_vuot_spread", CONG.CHAN_CUNG)
        self.assertNotIn("13_edge_vuot_spread", CONG.NHAN_MEM)


# ---------------------------------------------------------------------------
# Dot 3 (20/09/2026): ba cho tra `None` GOP NHIEU NGUYEN NHAN lam mot.
#
# Cung mot hinh dang loi o ca ba: mot phep KHONG DO DUOC (thieu `data/`, so cai
# khong doc duoc, mo phong hong) di ra bang cung mot gia tri voi mot ket luan
# AM that (tai san khong hop, ho chua tieu suat nao). LUAT SO 0 bat phan biet.
# ---------------------------------------------------------------------------

def test_nguong_fdr_noi_ro_khi_khong_doc_duoc_so_cai():
    """`nguong_fdr_hien_tai = None` phai kem ly do, khong doc thanh 'ho trong'."""
    from nhan import do_luc as DL

    nguong, ly_do = DL._nguong_fdr("do_luc")
    if nguong is None:
        assert ly_do and "CHUA_DO_DUOC" in ly_do, (
            "khong lay duoc nguong FDR ma khong noi vi sao - dung cai bay "
            "CHUA_DO_DUOC bi doc thanh AM")
    else:
        assert ly_do is None and nguong > 0


def test_hieu_chinh_gop_khong_bien_KHONG_DO_DUOC_thanh_ty_le_0():
    """Spec khong sinh duoc tin hieu -> tra spec GOC + None, khong phai 0.0.

    Ban cu `kh = NP._ty_le_kich_hoat(s2, df_d) or 0.0` tra ve chinh cai spec
    khong chay duoc, dan nhan "da hieu chinh", kem `sau_khop_phan_vi = 0.0`.
    """
    import numpy as np
    import pandas as pd
    from nhan import doi_khung as DK
    from nhan import ngu_phap as NP

    n = 300
    idx = pd.date_range("2020-01-01", periods=n, freq="h")
    df = pd.DataFrame({"open": 1.0, "high": 1.1, "low": 0.9,
                       "close": np.linspace(1.0, 1.2, n)}, index=idx)
    spec = {"ten": "x", "vao": [{"trai": {"chi_bao": "dong"},
                                 "phep": "<", "phai": {"hang": 1.05}}]}
    bao = [{"phan": "vao", "chi_so": 0, "phep": "<", "_duoi": True,
            "_chuoi": np.asarray(df["close"], float), "cu": 1.05,
            "moi": 1.05, "p_goc": 0.2}]

    goc = NP._ty_le_kich_hoat
    NP._ty_le_kich_hoat = lambda *_a, **_k: None
    try:
        ra, hs, kh = DK._hieu_chinh_gop(spec, df, bao, muc=0.2, hien=None)
    finally:
        NP._ty_le_kich_hoat = goc

    assert kh is None, "KHONG DO DUOC bi bien thanh ty le kich hoat = %r" % (kh,)
    assert ra is spec, "tra ve spec da bi doi he so du khong do duoc lan nao"
    assert hs == 1.0


def test_ngoai_sinh_phan_biet_thieu_du_lieu_voi_co_che_khong_chay():
    from nhan import ngoai_sinh as NS

    ty = NS.ty_le_kich_hoat("KHONG_CO_MA_NAY_XYZ", "H1", "khong_co_mau", {})
    assert ty is None
    assert NS._LY_DO_CUOI and "CHUA_DO_DUOC" in NS._LY_DO_CUOI, (
        "thieu du lieu phai la CHUA_DO_DUOC, khong duoc im lang: %r"
        % (NS._LY_DO_CUOI,))


def test_gop_lop_dem_rieng_chan_roi_vi_khong_do_duoc():
    from nhan import gop_lop as GL

    bo = []
    c = GL._mot_chan("khong_co_mau", "KHONG_CO_MA_NAY_XYZ", "H1", {},
                     ghi_ly_do=bo)
    assert c is None
    assert len(bo) == 1 and bo[0]["ma"] == "KHONG_CO_MA_NAY_XYZ"
    assert bo[0]["ly_do"].startswith("CHUA_DO_DUOC"), bo[0]["ly_do"]


# ---------------------------------------------------------------------------
# Dot 4 (20/09/2026): CONG CHAN CUNG HONG THI MO
#
# Day la cho dat nhat trong ca he: mot cong CHAN CUNG ma khong do duoc thi
# van cho di qua.
# ---------------------------------------------------------------------------

class CongChanCungHongThiMo(unittest.TestCase):
    """Cho dat nhat trong ca he: mot cong CHAN CUNG khong do duoc ma van cho
    di qua.

    Ke thua khuon `SoTam`: `CONG.xet` GHI vao so `fdr`, nen bai kiem phai tro
    `SO.DB` sang thu muc tam. Neu khong thi chinh bo test lam dung cai viec no
    dang di bat - bom dong vao so quyet dinh that (do 24/08: hai lan chay
    `pytest` da them 28 dong).
    """

    def setUp(self):
        import tempfile
        from pathlib import Path as _P
        from nhan import so as SO
        self._tmp = tempfile.TemporaryDirectory()
        self._db_cu = SO.DB
        SO.DB = _P(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        from nhan import so as SO
        SO.DB = self._db_cu
        self._tmp.cleanup()

    @staticmethod
    def _df_sach(n=420):
        import numpy as np
        import pandas as pd
        idx = pd.date_range("2020-01-01", periods=n, freq="D")
        gia = np.linspace(100.0, 120.0, n)
        return pd.DataFrame({"open": np.r_[gia[0], gia[:-1]],
                             "high": gia * 1.001, "low": gia * 0.999,
                             "close": gia}, index=idx)

    def _chay(self, df, ma_gt):
        from types import SimpleNamespace
        from unittest import mock
        import numpy as np
        from nhan import cong as CONG

        n = 420
        idx = self._df_sach(n).index
        kq = SimpleNamespace(so_lenh=n, loi=np.zeros(n), index=idx,
                             vi_the=np.ones(n), chi_phi_spread=0.0)
        so_sanh = {"he": {"tong_lai_pct": 50.0, "sharpe": 2.0, "calmar": 2.0,
                          "phoi_nhiem": 0.5, "so_bar": n},
                   "mua_giu_net": {"tong_lai_pct": 5.0, "sharpe": 0.2,
                                   "calmar": 0.2},
                   "alpha_vs_mua_giu": {"t_alpha": 3.0, "alpha_nam_pct": 20.0}}
        pl = {"p_xau_nhat": 0.001, "null_hop_le": True, "bootstrap_hop_le": True}
        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh), \
                mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]), \
                mock.patch.object(CONG, "placebo", return_value=pl):
            return CONG.xet(df, kq, SimpleNamespace(),
                            SimpleNamespace(do_tin="DO", canh_bao=None),
                            gt_ma=ma_gt, ho="test_cong_mo",
                            da_dang_ky=True, tren_holdout=True,
                            che_do="giao_dich")

    def test_cong_CHAN_CUNG_khong_do_duoc_thi_KHONG_duoc_PASS(self):
        """Cong `11_khong_an_khe_dao_ngay` tung HONG THI MO.

        Ban cu khoi tao `True` roi giu nguyen `True` o moi duong that bai: qua
        it bar, chi mot o thoi gian, hay mot ngoai le bat ky. Chinh dong
        `ly_do` ben duoi no viet *"KHONG ket luan la sach"* - tuc tac gia da
        biet - nhung GIA TRI thi van la `True`. Van noi mot dang, so noi mot
        dang.

        Va day la cong CHAN CUNG, dung cai cong sinh ra de bat
        `EURGBP.H4.mua_qua_dem`: he do dat `t_alpha = 14,52` va di het cong
        nho an khe dao ngay, *"khong mot cong nao trong 10 cong cu nhin thay"*.
        Mot cong chan cung ma hong thi mo se cho ung vien tiep theo cung kieu
        di qua y het.
        """
        ra = self._chay(None, "CONG_MO.khong_do_duoc")
        self.assertIn("11_khong_an_khe_dao_ngay", ra["cong_khong_do_duoc"])
        self.assertNotEqual(ra["verdict"], "PASS",
                            "cong chan cung KHONG DO DUOC ma van ra PASS")
        # Nhung cung khong duoc FAIL: chua do duoc khong phai la ban.
        self.assertEqual(ra["verdict"], "UNG_VIEN")

    def test_HIEU_CHUAN_NGUOC_chuoi_DO_DUOC_va_SACH_thi_VAN_PASS(self):
        """Mot cong tu choi TAT CA cho so lieu y het mot cong tot.

        Neu chan tren lam PASS thanh bat kha thi thi ca he vo nghia - nen phai
        con mot duong ra PASS tren chuoi DO DUOC va that su sach.
        """
        ra = self._chay(self._df_sach(), "CONG_MO.do_duoc_va_sach")
        self.assertEqual(ra["cong_khong_do_duoc"], [])
        self.assertIs(ra["dieu_kien"]["11_khong_an_khe_dao_ngay"], True)
        self.assertEqual(ra["verdict"], "PASS", ra["ly_do"][-3:])

    def test_cong_13_khong_doc_duoc_chi_phi_thi_cung_KHONG_PASS(self):
        """Cung hinh dang "hong thi mo" o cong `13_edge_vuot_spread`.

        Ban cu: `except Exception: _lai_rong = _phi_sp = 0.0`, roi
        `(_phi_sp <= 0)` la `True` -> CONG MO. Mot cong CHAN CUNG hoi "edge co
        day hon chi phi khong" lai di qua **dung luc khong doc duoc chi phi**.
        """
        from types import SimpleNamespace
        from unittest import mock
        import numpy as np
        from nhan import cong as CONG

        n = 420
        df = self._df_sach(n)

        class _Hong:
            """`chi_phi_spread` NEM khi doc - dung duong `except` cua cong 13."""
            so_lenh = n
            loi = np.zeros(n)
            index = df.index
            vi_the = np.ones(n)

            @property
            def chi_phi_spread(self):
                raise RuntimeError("khong doc duoc phi")

        so_sanh = {"he": {"tong_lai_pct": 50.0, "sharpe": 2.0, "calmar": 2.0,
                          "phoi_nhiem": 0.5, "so_bar": n},
                   "mua_giu_net": {"tong_lai_pct": 5.0, "sharpe": 0.2,
                                   "calmar": 0.2},
                   "alpha_vs_mua_giu": {"t_alpha": 3.0, "alpha_nam_pct": 20.0}}
        pl = {"p_xau_nhat": 0.001, "null_hop_le": True, "bootstrap_hop_le": True}
        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh), \
                mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]), \
                mock.patch.object(CONG, "placebo", return_value=pl):
            ra = CONG.xet(df, _Hong(), SimpleNamespace(),
                          SimpleNamespace(do_tin="DO", canh_bao=None),
                          gt_ma="CONG_MO.phi_hong", ho="test_cong_mo",
                          da_dang_ky=True, tren_holdout=True,
                          che_do="giao_dich")
        self.assertIn("13_edge_vuot_spread", ra["cong_khong_do_duoc"])
        self.assertNotEqual(ra["verdict"], "PASS")

    def test_chi_phi_bang_0_KHAI_TUONG_MINH_thi_VAN_di_qua(self):
        """Pham vi hep co chu dich: `0.0` khai TUONG MINH la truong hop that
        cua che do nghien cuu (chi phi la KHAI BAO, va `7_chi_phi_do_duoc` da
        chan san). Mot chot chan chan nham tang thi khong phai la chat hon."""
        ra = self._chay(self._df_sach(), "CONG_MO.phi_khai_0")
        self.assertNotIn("13_edge_vuot_spread", ra["cong_khong_do_duoc"])
        self.assertEqual(ra["verdict"], "PASS", ra["ly_do"][-2:])

    def test_moi_cong_CHAN_CUNG_deu_duoc_khai_bao_ro_rang(self):
        """`CHAN_CUNG` liet ke tuong minh de them mot dieu kien moi khong tu
        dong roi vao ben nao ma khong ai quyet dinh."""
        from nhan import cong as CONG
        self.assertIn("11_khong_an_khe_dao_ngay", CONG.CHAN_CUNG)
