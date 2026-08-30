# -*- coding: utf-8 -*-
"""CANARY — thu gac engine, va cai gac no.

Vi sao file nay ra doi (30/08/2026). `nhan/canary.py` la chot chan dau tien cua
ca day chuyen: QUANTLAB goi no truoc moi lo, hong thi dung tru va khong tinh
mot p-value nao. Vay ma **no khong co mot file test nao**. Mot cong gac ma
khong ai gac lai la cong de ngo: no co the hong im lang, va trieu chung se la
"engine sach" chu khong phai mot loi.

Bo test nay do hai chieu, dung nguyen tac cua `cong-pass-phai-hieu-chuan-hai-chieu`:

  chieu XUOI  - engine dung thi moi ca canary phai DAT;
  chieu NGUOC - chen lai dung hai loi that cua 09/08/2026 thi canary phai GAO.

Chieu nguoc quan trong hon. Mot bo canary luon bao "OK" cho so lieu y het mot
bo canary tot, va do la cach chinh xac ma canary o goc du an da vo dung suot
mot thang truoc bao cao 15/08.

Du lieu tong hop, khong nap tu `data/`: bai kiem phai chay duoc ca khi kho
trong, va phai cho cung ket qua o may khac.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import canary as CA        # noqa: E402
from nhan import chi_phi as CP       # noqa: E402
from nhan import mo_phong as MP      # noqa: E402


def _khung_gia(n: int = 800, hat: int = 7) -> pd.DataFrame:
    """OHLC tong hop, buoc ngau nhien co hat co dinh. Khong doc dia."""
    rng = np.random.default_rng(hat)
    r = rng.normal(0.0, 0.004, n)
    dong = 100.0 * np.exp(np.cumsum(r))
    mo = np.concatenate([[100.0], dong[:-1]])
    bien = np.abs(rng.normal(0.0, 0.002, n)) * dong
    idx = pd.date_range("2020-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame(
        {"open": mo, "high": np.maximum(mo, dong) + bien,
         "low": np.minimum(mo, dong) - bien, "close": dong},
        index=idx)


def _chi_phi(df) -> "CP.MoHinhChiPhi":
    """Cung duong ma `chay_het` di: khong truyen phi tay, de mo hinh tu suy.

    Truyen phi tay tung lam `tu_du_lieu` nem `KeyError: 'san_lay'` - loi do da
    duoc sua ngay 30/08 va co bai kiem rieng trong `test_chi_phi_xuat_xu.py`.
    """
    return CP.tu_du_lieu("THU_NGHIEM", df)


class MoiCaCanaryDatTrenEngineDung(unittest.TestCase):
    """Chieu XUOI: engine hien tai phai qua het moi ca."""

    def setUp(self):
        self.df = _khung_gia()
        self.cp = _chi_phi(self.df)

    def test_ca_luon_mua_khop_phep_tinh_tay(self):
        ok, mo_ta = CA.ca_luon_mua(self.df, self.cp, "THU_NGHIEM")
        self.assertTrue(ok, f"ca 'luon mua' lech: {mo_ta}")

    def test_ca_luon_ban_khop_phep_tinh_tay(self):
        ok, mo_ta = CA.ca_luon_ban(self.df, self.cp, "THU_NGHIEM")
        self.assertTrue(ok, f"ca 'luon ban' lech: {mo_ta}")

    def test_ca_dung_ngoai_khong_sinh_lai_lo(self):
        ok, mo_ta = CA.ca_dung_ngoai(self.df, self.cp, "THU_NGHIEM")
        self.assertTrue(ok, f"dung ngoai ma van co lai/lo: {mo_ta}")

    def test_ca_tre_mot_bar_khop(self):
        ok, mo_ta = CA.ca_tre_mot_bar(self.df, self.cp, "THU_NGHIEM")
        self.assertTrue(ok, f"ca 'tre mot bar' lech: {mo_ta}")

    def test_ca_biet_truoc_khop(self):
        ok, mo_ta = CA.ca_biet_truoc(self.df, self.cp, "THU_NGHIEM")
        self.assertTrue(ok, f"ca 'biet truoc' lech: {mo_ta}")


class CanaryPhaiGaoKhiEngineHong(unittest.TestCase):
    """Chieu NGUOC — mutation audit.

    Chen lai dung hai loi that ngay 09/08/2026. Canary nao khong bat duoc loi
    cua chinh no thi khong dung lam cong duoc.
    """

    def setUp(self):
        self.df = _khung_gia()
        self.cp = _chi_phi(self.df)

    def test_phi_qua_dem_chi_tinh_chieu_mua_thi_ca_luon_ban_phai_hong(self):
        # Loi 1: phi giu chi tinh khi dang MUA -> chieu ban duoc mien phi ->
        # ~2 %/nam alpha gia. Chiem 63% "edge" quan sat duoc hoi 09/08.
        goc = CP.MoHinhChiPhi.phi_giu_mang

        def thien_vi(self, index, huong, lai_suat_nam=None):
            return goc(self, index, np.clip(huong, 0, 1), lai_suat_nam)

        CP.MoHinhChiPhi.phi_giu_mang = thien_vi
        try:
            ok, _ = CA.ca_luon_ban(self.df, self.cp, "THU_NGHIEM")
        finally:
            CP.MoHinhChiPhi.phi_giu_mang = goc
        self.assertFalse(
            ok, "chen loi 'phi chi tinh chieu mua' ma canary VAN BAO DAT - "
                "day bay khong hoat dong")

    def test_engine_quen_dich_mot_bar_thi_ca_tre_mot_bar_phai_hong(self):
        # Loi 2: quen dich mot bar -> nhin truoc tron mot bar, thoi alpha
        # +26,8 diem %/nam va day t tu -0,74 len +10,05.
        goc = MP.chay

        def quen_dich(df, tin_hieu, cp, lai_suat_nam=None, ma="", khung="",
                      da_dich=False):
            return goc(df, tin_hieu, cp, lai_suat_nam, ma, khung, da_dich=True)

        MP.chay = quen_dich
        try:
            ok, _ = CA.ca_tre_mot_bar(self.df, self.cp, "THU_NGHIEM")
        finally:
            MP.chay = goc
        self.assertFalse(
            ok, "chen loi 'quen dich mot bar' ma canary VAN BAO DAT - "
                "chot chong nhin truoc khong hoat dong")

    def test_khoi_phuc_xong_thi_canary_lai_dat(self):
        """Chinh bai kiem tren khong duoc de lai tac dung phu."""
        ok_ban, _ = CA.ca_luon_ban(self.df, self.cp, "THU_NGHIEM")
        ok_tre, _ = CA.ca_tre_mot_bar(self.df, self.cp, "THU_NGHIEM")
        self.assertTrue(ok_ban and ok_tre,
                        "mot bai kiem mutation khong khoi phuc lai ban goc")


class BoCanaryChayDuocCaLo(unittest.TestCase):
    """`chay_het` chi nap duoc tai san TU DIA (`nap_tap` doc `data/`).

    Bai kiem thay `nap_tap` bang tap tong hop de khong phu thuoc kho: mot cong
    gac phai kiem duoc ca khi may khac khong co du lieu.
    """

    def setUp(self):
        self._nap_goc = CA.nap_tap
        tap = {"THU_NGHIEM_A": _khung_gia(hat=1), "THU_NGHIEM_B": _khung_gia(hat=2)}
        CA.nap_tap = lambda *a, **k: dict(tap)

    def tearDown(self):
        CA.nap_tap = self._nap_goc

    def test_chay_het_tra_ve_lanh_tren_tap_tong_hop(self):
        lanh, bao = CA.chay_het(im_lang=True)
        self.assertTrue(lanh, f"canary bao hong tren du lieu sach: {bao['hong']}")
        self.assertEqual(bao["hong"], [])
        self.assertGreaterEqual(len(bao["ket_qua"]), 5,
                                "phai co du 5 ca canary")

    def test_chay_het_bao_hong_khi_engine_bi_pha(self):
        """Cong phai TU CHOI duoc, khong chi biet chap nhan."""
        goc = MP.chay

        def quen_dich(df, tin_hieu, cp, lai_suat_nam=None, ma="", khung="",
                      da_dich=False):
            return goc(df, tin_hieu, cp, lai_suat_nam, ma, khung, da_dich=True)

        MP.chay = quen_dich
        try:
            lanh, bao = CA.chay_het(im_lang=True)
        finally:
            MP.chay = goc
        self.assertFalse(lanh, "engine bi pha ma bo canary van bao lanh")
        self.assertTrue(bao["hong"], "khong ke ten ca nao hong")


if __name__ == "__main__":
    unittest.main()
