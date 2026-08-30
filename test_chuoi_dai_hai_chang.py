# -*- coding: utf-8 -*-
"""BE MAT CHUOI DAI + KIEN TRUC HAI CHANG.

Bo test nay khoa bon thu, moi thu deu tung sai that:

1. Be mat kham pha phai NHIN THAY chuoi dai. Bo loc cu (`m.endswith("_D1_XM")`
   tren khoa cua kho) khong bao gio dung vi khoa da bi cat duoi ten file, nen
   80 bang OHLC >= 12 nam bi bo qua va he chi thay 11 tai san.
2. Nguong open bia phai theo CO CHE THI TRUONG, khong phai mot con so chung.
3. Che do `nghien_cuu` KHONG BAO GIO duoc tra PASS, du tin hieu manh den dau.
4. Chang hai (`bac_cau_san`) phai giu nguyen template + tham so va o lai trong
   cung LOP tai san; khong co chuoi san cung lop thi phai BAO VAN DE chu khong
   duoc im lang.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import chi_phi as CP, du_lieu as DL, so as SO
from tru import quantlab as Q


def _chuoi(n=3000, bat_dau="2000-01-03", bia_tu_nam=None, hat=7):
    """Chuoi ngay tong hop. `bia_tu_nam` -> open[i] = close[i-1] tu nam do."""
    rng = np.random.default_rng(hat)
    idx = pd.bdate_range(bat_dau, periods=n)
    r = rng.normal(0.0003, 0.01, n)
    close = 100 * np.exp(np.cumsum(r))
    op = np.concatenate([[close[0]], close[:-1] * (1 + rng.normal(0, 0.002, n - 1))])
    if bia_tu_nam is not None:
        bia = idx.year >= bia_tu_nam
        op[bia] = np.concatenate([[close[0]], close[:-1]])[bia]
    hi = np.maximum(op, close) * (1 + np.abs(rng.normal(0, 0.003, n)))
    lo = np.minimum(op, close) * (1 - np.abs(rng.normal(0, 0.003, n)))
    return pd.DataFrame({"open": op, "high": hi, "low": lo, "close": close}, index=idx)


def _voi_open_bia(df, buoc=3):
    """Dat open[i] = close[i-1] cho 1 tren `buoc` bar."""
    o = df["open"].to_numpy().copy()
    c = df["close"].to_numpy()
    lay = np.zeros(len(df), dtype=bool)
    lay[1::buoc] = True
    o[lay] = np.concatenate([[c[0]], c[:-1]])[lay]
    df = df.copy()
    df["open"] = o
    return df


class NguonDuLieu(unittest.TestCase):
    """Duoi ten file quyet dinh nguon, va nguon quyet dinh nguong chat luong."""

    def test_duoi_mt5_la_san(self):
        for ten in ("EURCAD_M1_mq", "AUDJPY_D1_xm", "auddkk_mt5_daily",
                    "us500m_m1", "us500cash_m30", "eurusd_h1"):
            self.assertEqual(DL.nguon_cua(ten), "san", ten)

    def test_feed_ngoai_la_ngoai(self):
        for ten in ("yh_nikkei_daily", "etf_spy_daily", "sp500_daily", "vix_daily"):
            self.assertEqual(DL.nguon_cua(ten), "ngoai", ten)

    def test_mt5_daily_khong_bi_doc_nham_thanh_feed_ngay(self):
        """`_mt5_daily` cung ket thuc bang `_daily` - thu tu doc phai dung."""
        self.assertEqual(DL.nguon_cua("audhkd_mt5_daily"), "san")
        self.assertEqual(DL.nguon_cua("audjpy_xm_daily"), "san")


class NguongOpenBia(unittest.TestCase):

    def test_hai_nguong_khac_nhau_va_dung_chieu(self):
        self.assertGreater(DL.NGUONG_OPEN_BIA, DL.NGUONG_OPEN_BIA_PHIEN)
        self.assertEqual(DL.nguong_open_bia(co_phien=True), DL.NGUONG_OPEN_BIA_PHIEN)
        self.assertEqual(DL.nguong_open_bia(co_phien=False), DL.NGUONG_OPEN_BIA)

    def test_ty_le_33_pct_la_binh_thuong_voi_thi_truong_lien_tuc(self):
        """FX H1 that do duoc 33-44% - siet o day la loai nham chuoi hop le."""
        df = _voi_open_bia(_chuoi(1500))
        bc = DL.kiem(df, "FX_GIA_LAP", co_phien=False)
        self.assertTrue(bc["dung_duoc"])
        self.assertEqual(len(bc["nam_open_that"]), len(set(df.index.year)))

    def test_cung_ty_le_do_la_BIA_voi_thi_truong_co_phien(self):
        df = _voi_open_bia(_chuoi(1500))
        bc = DL.kiem(df, "CHI_SO_GIA_LAP", co_phien=True)
        self.assertEqual(bc["nam_open_that"], [],
                         "gia mo phien PHAI khac gia dong hom truoc - 33% la loi ghi")

    def test_cat_ve_doan_sach_khi_mang_cuoi_bi_nhiem(self):
        df = _chuoi(3000, bia_tu_nam=2008)
        cat, _bc = DL.cat_theo_chat_luong(df, "MANG_NHIEM", co_phien=True)
        self.assertLess(len(cat), len(df))
        self.assertLessEqual(cat.index.max().year, 2007)


class BeMatKhamPha(unittest.TestCase):

    def setUp(self):
        self.ds = Q._tai_san_kha_dung()
        self.uu_tien = [m for m in Q.UU_TIEN_TAI_SAN if m in DL.kho()]

    def test_uu_tien_van_dung_dau(self):
        self.assertEqual(self.ds[:len(self.uu_tien)], self.uu_tien)

    def test_co_chuoi_dai_thuc_su_trong_be_mat(self):
        """Day la bug da sua: bo loc cu luon tra ve rong."""
        ngoai = [m for m in self.ds if DL.nguon_tai_san(m) == "ngoai"]
        self.assertGreaterEqual(len(ngoai), 4, "be mat khong nhin thay chuoi dai nao")

    def test_khong_cau_tai_san(self):
        self.assertLessEqual(len(self.ds), len(Q.UU_TIEN_TAI_SAN) + Q.TRAN_MO_RONG)

    def test_moi_lop_deu_bi_gioi_han(self):
        dem: dict[str, int] = {}
        for m in self.ds[len(self.uu_tien):]:
            lop = CP._loai_tai_san(m)
            dem[lop] = dem.get(lop, 0) + 1
        for lop, k in dem.items():
            self.assertLessEqual(k, Q.TRAN_MOI_LOP, lop)

    def test_khong_lay_bang_thieu_cot_ohlc(self):
        for m in self.ds:
            self.assertTrue(DL.kho()[m]["du_ohlc"], m)

    def test_khung_cua_bang_d1_chi_co_d1(self):
        """Hoi H1 tren bang D1 la yeu cau noi suy nguoc - khong duoc hoi."""
        for m in self.ds:
            if DL.kho()[m]["khung_goc"] == "D1":
                self.assertEqual(Q._khung_cua(m), ["D1"], m)

    def test_cap_ke_tiep_khong_sinh_cap_khong_nap_duoc(self):
        tt: dict = {"vong": 0, "da_quet": []}
        for _ in range(80):
            cap = Q._cap_ke_tiep(self.ds, tt)
            if cap is None:
                break
            ma, khung = cap
            self.assertIn(khung, Q._khung_cua(ma))
            tt["da_quet"].append(f"{ma}|{khung}")

    def test_quet_mau_co_ca_hai_lan(self):
        ds = Q._tai_san_quet_mau()
        self.assertTrue([m for m in ds if DL.nguon_tai_san(m) == "san"])
        self.assertTrue([m for m in ds if DL.nguon_tai_san(m) == "ngoai"])


class CheDo(unittest.TestCase):

    @staticmethod
    def _cp(do_tin):
        return SimpleNamespace(do_tin=do_tin)

    def test_do_duoc_thi_giao_dich(self):
        self.assertEqual(Q._che_do(self._cp("DO")), "giao_dich")
        self.assertEqual(Q._che_do(self._cp("SAN")), "giao_dich")

    def test_khai_bao_thi_nghien_cuu(self):
        self.assertEqual(Q._che_do(self._cp("KHAI")), "nghien_cuu")

    def test_hai_che_do_khong_chung_ho_fdr(self):
        a = Q._ho_fdr("xu_huong", "giao_dich")
        b = Q._ho_fdr("xu_huong", "nghien_cuu")
        self.assertNotEqual(a, b)
        self.assertIn(f"cp{CP.THE_HE}", a)


class _CoSoCaiTam(unittest.TestCase):

    def setUp(self):
        self._db_cu = SO.DB
        self._tmp = tempfile.TemporaryDirectory()
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()


class HaiChang(_CoSoCaiTam):

    def _dang_ky(self, tai_san="YH_NIKKEI", khung="D1", ho="xu_huong",
                 template="momentum_ema", tham_so=None):
        tham_so = {"n": 50} if tham_so is None else tham_so
        ma = f"{tai_san}.{khung}.{template}.thu"
        SO.dang_ky_gia_thuyet(
            ma=ma, co_che="thu nghiem", template=template, tham_so=tham_so,
            tai_san=tai_san, khung=khung, cua_so="1970..2026", ho=ho,
            nguon="test", tru_sinh="QUANTLAB")
        return ma

    def test_bac_cau_giu_nguyen_template_va_tham_so(self):
        ma = self._dang_ky(tham_so={"n": 50})
        ra = Q.bac_cau_san(ma)
        self.assertTrue(ra["da_thu"], f"khong bac cau duoc: {ra}")
        for m in ra["da_thu"]:
            gt = SO.mot("SELECT * FROM gia_thuyet WHERE ma=?", m)
            self.assertEqual(gt["template"], "momentum_ema")
            self.assertEqual(gt["tham_so"], '{"n": 50}')
            self.assertEqual(gt["nguon"], f"bac_cau_tu:{ma}")

    def test_bac_cau_chi_sang_chuoi_MUA_DUOC_cung_lop(self):
        ma = self._dang_ky(tai_san="YH_NIKKEI")
        ra = Q.bac_cau_san(ma)
        lop = CP._loai_tai_san("YH_NIKKEI")
        for m in ra["da_thu"]:
            gt = SO.mot("SELECT * FROM gia_thuyet WHERE ma=?", m)
            self.assertEqual(DL.nguon_tai_san(gt["tai_san"]), "san")
            self.assertEqual(CP._loai_tai_san(gt["tai_san"]), lop)

    def test_bac_cau_xep_viec_xac_nhan_chu_khong_tu_ket_luan(self):
        ma = self._dang_ky()
        ra = Q.bac_cau_san(ma)
        self.assertEqual(ra["dang_ky_moi"], len(ra["da_thu"]))
        loai = set()
        while True:
            v = SO.nhan_viec("QUANTLAB")
            if not v:
                break
            loai.add(v["loai"])
        self.assertEqual(loai, {"xac_nhan"})

    def test_khong_co_chuoi_san_cung_lop_thi_BAO_VAN_DE(self):
        ma = self._dang_ky(tai_san="YH_DAUWTI")     # lop hang_hoa: kho khong co
        ra = Q.bac_cau_san(ma)
        self.assertTrue(ra.get("thieu_tai_san_san"))
        self.assertEqual(ra["da_thu"], [])
        vd = SO.mot("SELECT * FROM van_de WHERE ma LIKE 'bac_cau_thieu_san_%' "
                    "ORDER BY id DESC LIMIT 1")
        self.assertIsNotNone(vd, "im lang bo qua - dung dieu bo test nay cam")

    def test_tran_bac_cau_duoc_ton_trong(self):
        ma = self._dang_ky()
        ra = Q.bac_cau_san(ma, tran=2)
        self.assertLessEqual(len(ra["da_thu"]), 2)


class NghienCuuKhongBaoGioPass(_CoSoCaiTam):
    """Bat bien cua kien truc hai chang, kiem tren DUONG THAT chu khong mock."""

    def test_tin_hieu_hoan_hao_van_chi_toi_CO_CO_CHE(self):
        from nhan import cong as CONG, mo_phong as MP
        ma, khung = "YH_NASDAQ", "D1"
        _df, _tr, hold, _c, cp = Q._nap(ma, khung)
        self.assertEqual(Q._che_do(cp), "nghien_cuu")
        # 1.500 bar cuoi la du de tra loi cau hoi BAT BIEN (verdict co the la
        # PASS khong). Chay ca 22 nam chi de doi placebo lau hon 7 phut.
        hold = hold.iloc[-1500:]
        r = MP._loi_suat_tien(hold)
        dau = np.sign(r)
        dau[dau == 0] = 1.0                      # biet truoc dau loi suat: gian lan
        kq = MP.chay(hold, dau, cp, ma=ma, khung=khung, da_dich=True)
        bh = MP.mua_giu(hold, cp, ma=ma, khung=khung)
        kt = CONG.xet(hold, kq, bh, cp, gt_ma="TEST.NC", ho="test_nc",
                      da_dang_ky=True, tren_holdout=True, che_do="nghien_cuu")
        self.assertNotEqual(kt["verdict"], "PASS")
        self.assertIn(kt["verdict"], ("CO_CO_CHE", "NGHI_NHIN_TRUOC"))

    def test_chuoi_ngoai_bi_cat_con_chuoi_san_thi_khong(self):
        df_ngoai = Q._nap("YH_NASDAQ", "D1")[0]
        self.assertLessEqual(len(df_ngoai), len(DL.nap("YH_NASDAQ", "D1")))
        df_san = Q._nap("EURCAD", "H1")[0]
        self.assertEqual(len(df_san), len(DL.nap("EURCAD", "H1")),
                         "chuoi bao gia lien tuc khong duoc cat theo nguong phien")


class CongKhaThi(_CoSoCaiTam):
    """Khong tieu suat FDR o cap khong do duoc thu dang xet.

    PHAI ke thua `_CoSoCaiTam`: `mde_cua` -> `duong_cong_luc` -> `cong.xet(
    tren_holdout=True)` -> `lord()` GHI vao so cai. Neu lop nay dung
    `unittest.TestCase` tron thi moi lan chay test lai dot vai chuc suat FDR
    cua ho `do_luc` tren SO CAI THAT - tuc bo test tu lam xau ket qua cua he
    ma no dang kiem.

    Bai kiem quan trong nhat o day khong phai "co chan khong" ma la "chan DUNG
    CHO khong": mot ung vien du manh tren cung cap do phai di tiep binh thuong.
    Mot cong chan tat ca cho so lieu y het mot cong hieu chuan tot.
    """

    def test_mde_cua_tra_ve_so_va_cache_lai(self):
        from nhan import do_luc as L
        a = L.mde_cua("EURCAD", "H4")
        b = L.mde_cua("EURCAD", "H4")
        self.assertEqual(a["mde"], b["mde"])
        self.assertGreater(a["so_bar"], 500)

    def test_ung_vien_yeu_hon_MDE_bi_chan(self):
        from nhan import do_luc as L
        mde = L.mde_cua("EURCAD", "H4")["mde"]
        self.assertIsNotNone(mde)
        r = L.du_luc_de_kiem(mde * 0.5, "EURCAD", "H4")
        self.assertFalse(r["du_luc"])
        self.assertIn("MDE", r["ly_do"])

    def test_ung_vien_manh_hon_MDE_di_tiep(self):
        from nhan import do_luc as L
        mde = L.mde_cua("EURCAD", "H4")["mde"]
        self.assertTrue(L.du_luc_de_kiem(mde * 1.5, "EURCAD", "H4")["du_luc"])

    def test_cap_dai_co_MDE_thap_hon_cap_ngan(self):
        """Day la ca ly do ky thuat cua viec nap chuoi dai."""
        from nhan import do_luc as L
        ngan = L.mde_cua("EURCAD", "H4")["mde"]
        dai = L.mde_cua("YH_NASDAQ", "D1")["mde"]
        self.assertIsNotNone(dai)
        self.assertLess(dai, ngan)

    def test_do_luc_khong_nem_khi_khong_muc_nao_qua(self):
        """Nhanh nay tung nem NameError - dung o nhung cap yeu nhat."""
        from nhan import do_luc as L
        r = L.duong_cong_luc("EURCAD", "H4", thang_p=(0.50,))
        self.assertIsInstance(r, dict)
        self.assertIsNone(r["sharpe_nho_nhat_thay_duoc"])
        self.assertIn("qua it de do", r["ly_do_neu_khong_dat"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
