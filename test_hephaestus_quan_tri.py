# -*- coding: utf-8 -*-
"""HEPHAESTUS de CAU HINH QUAN TRI LENH, khong chi tin hieu vao.

## VI SAO NUA NAY QUAN TRONG HON

Bang chung cua chinh du an, khong phai suy doan:

  * 18/09 tren AUDCAD: cung mot bo tham so luoi, chi bat/tat `tia_lenh` thi
    holdout di tu **+0,66%/nam len +13,26%/nam**, sut giam tu -15,6% xuong
    -3,5%. Tia lenh la TOAN BO khac biet.
  * Cung phien do, **668 co che ENTRY** qua MT5 tester that: 0 co che vua du
    2 lenh/tuan vua Sharpe duong.
  * `quan_tri.py`: *"entry co tinh SAI van cho 92-97%/nam"* voi lop luoi.

Nen mot may de chi de ra tin hieu VAO la dang de ra nua it gia tri hon. Bo
test nay khoa nua con lai.

## LUAT KHONG DUOC PHA - PHAN GIAI CUA BAR

`pmg_engine.NGUONG_PHAN_GIAI = 2.0`: buoc luoi phai rong >= 2 lan BIEN DO MOT
NEN, khong thi ca cai luoi nam gon trong mot nen va ket qua la tao tac cua gia
dinh duong di chu khong phai cua thi truong. Do 14/09 tren random walk khong
chi phi: buoc/bien_do = 0,54 cho ra **+720%** trong khi dap an la ~0.

Cau hinh khong dat nguong nay phai ra `CHUA_DO_DUOC`, **khong phai** `AM`.
"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from nhan import hephaestus as HP


def _khung(n: int = 4000, bien_do: float = 0.0008) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    c = 1.0 * np.exp(np.cumsum(rng.normal(0, bien_do, n)))
    op = np.r_[c[0], c[:-1]]
    hi = np.maximum(c, op) * (1 + bien_do / 2)
    lo = np.minimum(c, op) * (1 - bien_do / 2)
    return pd.DataFrame(
        {"open": op, "high": hi, "low": lo, "close": c,
         "tick_volume": np.full(n, 100.0)},
        index=pd.date_range("2018-01-01", periods=n, freq="h"))


class DeRaCauHinhCHAY_DUOC(unittest.TestCase):

    def setUp(self):
        self.ds = HP.duc_quan_tri(han_ngach=120)

    def test_de_ra_duoc_nhieu_cau_hinh(self):
        self.assertGreaterEqual(len(self.ds), 50)

    def test_moi_cau_hinh_la_THAM_SO_HOP_LE_cua_mo_phong(self):
        import inspect
        import mo_phong_v2 as MP
        nhan = set(inspect.signature(MP.mo_phong).parameters)
        for cf in self.ds:
            for k in cf["nut"]:
                self.assertIn(k, nhan, "%s: `mo_phong` khong nhan '%s'"
                              % (cf["ten"], k))

    def test_moi_cau_hinh_co_LUAN_DIEM(self):
        for cf in self.ds:
            self.assertGreaterEqual(len(cf["co_che"]), 25, cf["ten"])

    def test_khong_trung_nhau(self):
        vt = [HP.van_tay_quan_tri(cf) for cf in self.ds]
        self.assertEqual(len(vt), len(set(vt)))

    def test_xac_dinh(self):
        a = [c["ten"] for c in HP.duc_quan_tri(han_ngach=60)]
        b = [c["ten"] for c in HP.duc_quan_tri(han_ngach=60)]
        self.assertEqual(a, b)

    def test_han_ngach_nho_la_TAP_CON_DAU(self):
        it = [c["ten"] for c in HP.duc_quan_tri(han_ngach=15)]
        nhieu = [c["ten"] for c in HP.duc_quan_tri(han_ngach=90)]
        self.assertEqual(it, nhieu[:len(it)])

    def test_co_de_ra_cau_hinh_CO_TIA(self):
        """Ho da chung minh gia tri bang so - phai co mat."""
        self.assertTrue([c for c in self.ds if "tia_tu" in c["nut"]])

    def test_cau_hinh_CO_TIA_phai_TAT_cat_hoa(self):
        """Do 19/09: `cat_hoa` bat mac dinh thi `tia` kich hoat 0 lan - cat hoa
        dong cac cap truoc khi lai ca ro kip cham nguong. De ra mot cau hinh
        'co tia' ma de cat hoa bat la de ra mot cau hinh KHONG tia."""
        for c in self.ds:
            if "tia_tu" not in c["nut"]:
                continue
            self.assertGreaterEqual(c["nut"].get("cat_hoa_tu", 2), 99, c["ten"])


class LuatPhanGiaiCuaBar(unittest.TestCase):
    """Buoc luoi hep hon nen -> CHUA_DO_DUOC, khong phai AM."""

    def setUp(self):
        self.df = _khung()

    def test_buoc_qua_HEP_bi_cham_CHUA_DO_DUOC(self):
        r = HP.kiem_phan_giai({"nut": {"buoc": 1.0, "tp": 2.0}}, self.df)
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC")
        self.assertIn("buoc", r["ly_do"])

    def test_buoc_DU_RONG_thi_dat(self):
        r = HP.kiem_phan_giai({"nut": {"buoc": 200.0, "tp": 200.0}}, self.df)
        self.assertEqual(r["trang_thai"], "DU", r["ly_do"])

    def test_KHONG_bao_gio_tra_ve_AM(self):
        """Ba trang thai, khong phai hai. `AM` la mot KET LUAN, con day chi noi
        chuoi bar co do min de mo phong hay khong."""
        for buoc in (0.5, 5.0, 50.0, 500.0):
            r = HP.kiem_phan_giai({"nut": {"buoc": buoc, "tp": buoc}}, self.df)
            self.assertIn(r["trang_thai"], ("DU", "CHUA_DO_DUOC"))

    def test_bao_ca_TY_LE_do_duoc_de_nguoi_doc_tu_kiem(self):
        r = HP.kiem_phan_giai({"nut": {"buoc": 200.0, "tp": 200.0}}, self.df)
        self.assertGreater(r["buoc_tren_bien_do"], 0)


class ChayLoVaChamDiem(unittest.TestCase):
    """De -> chay -> cham diem. Ca chang, tren mot khung tong hop."""

    def setUp(self):
        self.df = _khung()
        self.ds = HP.duc_quan_tri(han_ngach=12)

    def test_chay_duoc_ca_lo(self):
        r = HP.chay_lo(self.ds, self.df)
        self.assertEqual(len(r["dong"]), len(self.ds))

    def test_moi_dong_co_BANG_DIEM(self):
        for d in HP.chay_lo(self.ds, self.df)["dong"]:
            self.assertIn(d["diem"]["muc"], ("CHAY_DUOC", "MONG", "BO",
                                             "CHUA_DO_DUOC"))

    def test_cau_hinh_khong_du_PHAN_GIAI_bi_cham_CHUA_DO_DUOC(self):
        """Khong duoc chay roi bao AM mot cau hinh ma bar khong do noi."""
        hep = [{"ten": "hep", "khuon": "thu", "co_che": "x" * 30,
                "nut": {"buoc": 1.0, "tp": 2.0}}]
        d = HP.chay_lo(hep, self.df)["dong"][0]
        self.assertEqual(d["diem"]["muc"], "CHUA_DO_DUOC")

    def test_lo_co_TIEN_DANG_KY(self):
        r = HP.chay_lo(self.ds, self.df)
        self.assertIn("plan_hash", r)
        self.assertEqual(r["so_phep_thu"], len(self.ds))


class MOI_NUT_KHOANG_CACH_deu_phai_qua_nguong(unittest.TestCase):
    """Do 19/09: cong chi kiem `buoc` va `tp` thi cac cau hinh `trailing` lot het.

    `trailing_buoc = 10 pip` tren chuoi co bien do nen 14,4 pip cho ra
    **12.805%/nam tren random walk** voi sut giam 4,67 - dung chu ky cua loi
    "AUDCAD 6.557%/nam voi von 41 USD".

    Lai chay theo dung mot duong don dieu voi do min: trailing_buoc 5 pip cho
    +1.267/nam, 120 pip (8,3x nen) cho **-12/nam** tuc dap an dung. Khong phai
    mot cau hinh tot o do phan giai cao - la mot phep do khong hop le.
    """

    def setUp(self):
        self.df = _khung()          # bien do nen ~14 pip

    def test_trailing_buoc_duoi_nen_bi_chan(self):
        r = HP.kiem_phan_giai(
            {"nut": {"buoc": 60.0, "tp": 200.0,
                     "trailing_tu": 20.0, "trailing_buoc": 10.0}}, self.df)
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC")
        self.assertIn("trailing", r["ly_do"])

    def test_trailing_buoc_du_rong_thi_dat(self):
        r = HP.kiem_phan_giai(
            {"nut": {"buoc": 60.0, "tp": 200.0,
                     "trailing_tu": 120.0, "trailing_buoc": 120.0}}, self.df)
        self.assertEqual(r["trang_thai"], "DU", r["ly_do"])

    def test_nut_KHONG_DAT_thi_khong_bi_cham(self):
        """`trailing_buoc` co gia tri mac dinh du `trailing_tu` khong dat -
        luc do trailing KHONG chay, nen cham no la cham mot thu khong ton tai."""
        r = HP.kiem_phan_giai({"nut": {"buoc": 60.0, "tp": 200.0}}, self.df)
        self.assertEqual(r["trang_thai"], "DU", r["ly_do"])

    def test_cac_nut_khoang_cach_khac_cung_bi_kiem(self):
        for k in ("kc_bs", "cho_lui", "hedge_go", "breakeven_tu"):
            r = HP.kiem_phan_giai(
                {"nut": {"buoc": 60.0, "tp": 200.0, k: 3.0}}, self.df)
            self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC", k)

    def test_KHONG_cau_hinh_trailing_nao_lot_qua_duoc_nua(self):
        """Bai chot: chay ca lo va doi hoi moi cau hinh trailing co buoc duoi
        nen deu bi cham CHUA_DO_DUOC, khong cai nao ra mot con so lai."""
        ds = [c for c in HP.duc_quan_tri(han_ngach=100000)
              if c["khuon"] == "luoi_trailing"]
        self.assertTrue(ds)
        for d in HP.chay_lo(ds, self.df)["dong"]:
            tb = None
            for c in ds:
                if c["ten"] == d["ten"]:
                    tb = c["nut"].get("trailing_buoc")
            if tb is not None and tb < 2 * d["phan_giai"].get("bien_do_nen_pip", 0):
                self.assertEqual(d["diem"]["muc"], "CHUA_DO_DUOC", d["ten"])


class HieuChuanCongHAI_CHIEU(unittest.TestCase):
    """*"Mot cong tu choi TAT CA cho so lieu y het mot cong tot"* - luat du an.

    Do 19/09 chinh bang phep nay ma tim ra `cat_hoa` gat bien do trong nen:
    ty le lot 42% tren chuoi da bi pha edge, va sau khi sua con 2,9%.
    """

    def setUp(self):
        self.df = _khung(n=8000)

    def test_chuoi_null_GIU_NGUYEN_bien_do_nen(self):
        """Dieu kien song con: phep kiem phan giai va moi tao tac trong-bar deu
        phu thuoc bien do nen, nen null phai giu no."""
        a = float(np.median(self.df["high"] - self.df["low"]))
        b = float(np.median(HP.chuoi_null(self.df)["high"]
                            - HP.chuoi_null(self.df)["low"]))
        self.assertAlmostEqual(a, b, delta=a * 0.15)

    def test_chuoi_null_KHAC_chuoi_goc(self):
        self.assertFalse(np.allclose(
            np.asarray(self.df["close"]),
            np.asarray(HP.chuoi_null(self.df)["close"])))

    def test_chuoi_null_XAC_DINH_theo_hat(self):
        a = np.asarray(HP.chuoi_null(self.df, hat=3)["close"])
        b = np.asarray(HP.chuoi_null(self.df, hat=3)["close"])
        self.assertTrue(np.allclose(a, b))

    def test_hieu_chuan_bao_TY_LE_LOT(self):
        r = HP.hieu_chuan(HP.duc_quan_tri(han_ngach=8), self.df, so_lan=2)
        self.assertIn("ty_le_lot", r)
        self.assertGreaterEqual(r["ty_le_lot"], 0.0)
        self.assertLessEqual(r["ty_le_lot"], 1.0)

    def test_CHAM_MOT_DUONG_khong_phan_biet_duoc_gi(self):
        """PHAT HIEN 19/09, va la ly do `danh_gia_vs_null` phai ton tai.

        Tren chuoi DA BI PHA EDGE, ty le cau hinh duoc cham `CHAY_DUOC` van
        rat cao. Khong phai vi cong hong, ma vi mot cai luoi co hinh dang tra
        thuong **trung vi DUONG, ky vong AM**: phan lon duong mau cho lai nho
        deu, mot thieu so cho lo rat sau.

        Nen `cham_diem` tren MOT luot chay **ve mat cau truc** khong phan biet
        duoc luoi co edge voi luoi khong co. Bai nay khoa chinh su that do lai
        de khong ai vo tinh "sua" no bang cach noi long nguong.
        """
        r = HP.hieu_chuan(HP.duc_quan_tri(han_ngach=40), self.df, so_lan=3)
        self.assertGreater(r["ty_le_lot"], 0.05,
                           "neu ty le nay da thap thi cau chuyen doi - doc lai "
                           "docstring truoc khi xoa bai test")


class PhanQuyetPhaiSO_VOI_NULL(unittest.TestCase):
    """He qua cua bai tren: thu hang so voi phan bo null, khong phai mot duong."""

    def setUp(self):
        self.df = _khung(n=6000)
        self.ds = HP.duc_quan_tri(han_ngach=6)

    def test_moi_dong_co_THU_HANG_so_voi_null(self):
        for d in HP.danh_gia_vs_null(self.ds, self.df, so_null=6)["dong"]:
            if d.get("vuot_null") is None:
                self.assertIn("CHUA_DO_DUOC", d.get("ghi_chu", ""))
            else:
                self.assertGreaterEqual(d["vuot_null"], 0.0)
                self.assertLessEqual(d["vuot_null"], 1.0)

    def test_xep_theo_THU_HANG_giam_dan(self):
        ds = [d for d in HP.danh_gia_vs_null(self.ds, self.df, so_null=6)["dong"]
              if d.get("vuot_null") is not None]
        self.assertEqual([d["vuot_null"] for d in ds],
                         sorted([d["vuot_null"] for d in ds], reverse=True))

    def test_KHONG_du_ban_null_thi_khong_ket_luan(self):
        r = HP.danh_gia_vs_null(self.ds, self.df, so_null=1)
        self.assertTrue(all(d.get("vuot_null") is None for d in r["dong"]),
                        "xep hang voi mot ban null - do la bia thu hang")

    def test_van_tien_dang_ky(self):
        r = HP.danh_gia_vs_null(self.ds, self.df, so_null=6)
        self.assertIn("plan_hash", r)
