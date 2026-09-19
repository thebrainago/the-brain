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
