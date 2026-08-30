# -*- coding: utf-8 -*-
"""XUAT XU CHI PHI — `do_tin` phai noi dung no biet gi.

`cp.do_tin` la mot trong ba chot cua cong PASS (AGENTS.md muc 3): chi `DO` hoac
`SAN` moi duoc PASS, `KHAI` thi khong bao gio. Nhan nay vi the la mot phan cua
LUAT QUYET DINH, khong phai mot dong ghi chu.

Bay bat 30/08/2026. `chi_phi.tu_du_lieu` co ba nhanh, va nhanh giua bi thieu:

    pm is None            -> KHAI   (khong ai co so lieu)
    pm do NGUOI GOI truyen -> roi nham vao nhanh cuoi
    pm doc tu bang san    -> SAN

Nhanh giua lam hai viec sai cung luc. Thu nhat, no doc `luu['san_lay']` trong
khi `luu` rong -> `KeyError: 'san_lay'`. Thu hai, va nang hon: neu khong vo thi
no gan `do_tin="SAN"` cho mot con so GO TAY - tuc mot phi khai bao se du dieu
kien 7 de PASS.

Khong caller san xuat nao dang truyen phi tay nen loi con tiem an. Bo test nay
giu no o trang thai tiem an vinh vien.
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

from nhan import chi_phi as CP   # noqa: E402


def _khung_gia(n: int = 600, hat: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(hat)
    dong = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.004, n)))
    mo = np.concatenate([[100.0], dong[:-1]])
    bien = np.abs(rng.normal(0.0, 0.002, n)) * dong
    return pd.DataFrame(
        {"open": mo, "high": np.maximum(mo, dong) + bien,
         "low": np.minimum(mo, dong) - bien, "close": dong},
        index=pd.date_range("2021-01-01", periods=n, freq="h", tz="UTC"))


class PhiNguoiGoiTruyenVaoLaKHAI(unittest.TestCase):

    def setUp(self):
        self.df = _khung_gia()

    def test_khong_nem_KeyError_khi_truyen_phi_tay(self):
        cp = CP.tu_du_lieu("KHONG_CO_TREN_SAN_NAO", self.df,
                           phi_nam_mua=0.03, phi_nam_ban=0.01)
        self.assertAlmostEqual(cp.phi_nam_mua, 0.03)
        self.assertAlmostEqual(cp.phi_nam_ban, 0.01)

    def test_phi_go_tay_KHONG_duoc_mang_nhan_SAN(self):
        cp = CP.tu_du_lieu("KHONG_CO_TREN_SAN_NAO", self.df,
                           phi_nam_mua=0.03, phi_nam_ban=0.01)
        self.assertNotEqual(
            cp.do_tin, "SAN",
            "phi go tay bi gan nhan SAN - mot con so khai bao se du dieu kien 7 "
            "de PASS")
        self.assertEqual(cp.do_tin, "KHAI")

    def test_co_canh_bao_noi_ro_phi_den_tu_dau(self):
        cp = CP.tu_du_lieu("KHONG_CO_TREN_SAN_NAO", self.df,
                           phi_nam_mua=0.03, phi_nam_ban=0.01)
        self.assertTrue(
            any("nguoi goi" in c.lower() for c in cp.canh_bao),
            f"khong canh bao ve xuat xu phi: {cp.canh_bao}")

    def test_khong_truyen_gi_thi_van_la_KHAI(self):
        cp = CP.tu_du_lieu("KHONG_CO_TREN_SAN_NAO", self.df)
        self.assertEqual(cp.do_tin, "KHAI")


class ChiSanMoiDuocNhanSAN(unittest.TestCase):
    """Chieu nguoc: phi DOC TU BANG SAN thi phai duoc nhan SAN.

    Neu khong co bai nay thi mot ban sua "cho tat ca thanh KHAI" cung qua -
    va do lai la cai cong tu choi tat ca.
    """

    def setUp(self):
        # Co cot `spread` -> spread DO DUOC. `do_tin` la ket hop cua CA HAI
        # nguon (spread + phi), nen thieu spread thi no tut ve KHAI du phi co
        # xuat xu san - do la hanh vi DUNG, va la ly do bai kiem nay phai cap
        # cot spread thay vi doi mot minh phi la du.
        self.df = _khung_gia()
        self.df["spread"] = 12.0
        self._goc = CP.phi_cua
        CP.phi_cua = lambda ma, san_uu_tien=None: {
            "phi_nam_mua": 0.041, "phi_nam_ban": 0.012,
            "san_lay": "XM", "symbol_lay": "EURCADMICRO",
            "do_luc": "2026-08-30 00:00:00", "tin_cay": "CAO"}

    def tearDown(self):
        CP.phi_cua = self._goc

    def test_phi_doc_tu_san_duoc_nhan_SAN(self):
        cp = CP.tu_du_lieu("EURCAD", self.df)
        self.assertEqual(cp.do_tin, "SAN")
        self.assertAlmostEqual(cp.phi_nam_mua, 0.041)

    def test_tin_cay_THAP_thi_tut_ve_KHAI(self):
        CP.phi_cua = lambda ma, san_uu_tien=None: {
            "phi_nam_mua": 0.041, "phi_nam_ban": 0.012,
            "san_lay": "FXCE", "symbol_lay": "EURCAD",
            "do_luc": "2026-08-30 00:00:00", "tin_cay": "THAP"}
        cp = CP.tu_du_lieu("EURCAD", self.df)
        self.assertEqual(
            cp.do_tin, "KHAI",
            "swap_mode khong quy doi chac chan ma van duoc nhan SAN")


if __name__ == "__main__":
    unittest.main()
