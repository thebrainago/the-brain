# -*- coding: utf-8 -*-
"""BA LUONG CUA MOT CHIEN DICH THEO MUC TIEU (03/09/2026).

Chu du an chi ra rang phien nay da lam SAI THU TU: quet mot kho co che thu
thap CHUNG roi ket luan "khong co gi cho SP500", trong khi SEEKER chua bao gio
di san rieng cho SP500. `seeker.TU_KHOA_GOC` co 15 tu deu chung chung va
**khong mot tu nao** ve SP500 / US500 / ES futures.

  LUONG 1  `muc_tieu.san`    - SEEKER het cong suat theo dung muc tieu
  LUONG 2  `quantlab` + `do_on_dinh` - boc tach, backtest, can chinh tham so
  LUONG 3  `noi_sinh`        - tu sinh co che tu chinh lich su cua ma
"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from nhan import muc_tieu as MT
from nhan import ngu_phap as NP
from nhan import noi_sinh as NS


def _df(n: int = 1500) -> pd.DataFrame:
    r = np.random.default_rng(5)
    idx = pd.date_range("2015-01-01", periods=n, freq="4h")
    dong = 1000 + np.cumsum(r.normal(0.05, 5.0, n))
    mo = np.concatenate(([dong[0]], dong[:-1])) + r.normal(0, 1.5, n)
    bd = np.abs(r.normal(0, 6.0, n)) + 1.0
    return pd.DataFrame(
        {"open": mo, "high": np.maximum(mo, dong) + bd * r.random(n),
         "low": np.minimum(mo, dong) - bd * r.random(n), "close": dong,
         "tick_volume": r.lognormal(7.0, 0.6, n)}, index=idx)


class TuKhoaTheoMucTieu(unittest.TestCase):
    def test_moi_ma_khai_deu_co_tu_khoa_dac_thu(self):
        for ma, tk in MT.TU_KHOA_THEO_MA.items():
            self.assertGreaterEqual(len(tk), 8, ma)
            self.assertEqual(len(tk), len(set(tk)), f"{ma}: tu khoa trung")

    def test_tu_khoa_SP500_that_su_noi_ve_SP500(self):
        """Loi goc: `TU_KHOA_GOC` khong co mot tu nao ve SP500."""
        tk = " ".join(MT.TU_KHOA_THEO_MA["US500CASH"]).lower()
        for moc in ("s&p 500", "spx", "spy", "es futures", "us500"):
            self.assertIn(moc, tk, f"thieu moc '{moc}'")

    def test_tu_khoa_goc_cua_seeker_VAN_khong_du(self):
        """Hieu chuan chieu nguoc: neu `TU_KHOA_GOC` da du thi file nay thua."""
        from tru import seeker as SK
        goc = " ".join(SK.TU_KHOA_GOC).lower()
        self.assertNotIn("s&p", goc)
        self.assertNotIn("spx", goc)

    def test_ma_khong_khai_thi_bao_loi_ro_rang(self):
        with self.assertRaises(ValueError) as e:
            MT._cac_tu_khoa("KHONG_CO_MA_NAY")
        self.assertIn("TU_KHOA_THEO_MA", str(e.exception))

    def test_them_tu_khoa_duoc_gop_va_khong_trung(self):
        a = MT._cac_tu_khoa("US500CASH", ["S&P 500 trading strategy", "moi tinh"])
        self.assertIn("moi tinh", a)
        self.assertEqual(a.count("S&P 500 trading strategy"), 1)


class NoiSinhLayNguongTuLichSu(unittest.TestCase):
    def setUp(self):
        self.df = _df()

    def test_nguong_la_phan_vi_THAT_cua_chuoi(self):
        th = {"chi_bao": "ibs"}
        ng = NS.nguong_tu_lich_su(self.df, th)
        s = NP.toan_hang(self.df, th).to_numpy(float)
        s = s[np.isfinite(s)]
        for p, gt in ng.items():
            self.assertAlmostEqual(float(np.mean(s <= gt)), p, delta=0.02)

    def test_chuoi_qua_ngan_thi_KHONG_doan_bua(self):
        self.assertEqual(NS.nguong_tu_lich_su(self.df.iloc[:50], {"chi_bao": "ibs"}), {})

    def test_moi_spec_sinh_ra_deu_qua_cong_ngu_phap(self):
        for s in NS.sinh(self.df)[:120]:
            self.assertEqual(NP.kiem_khai_bao(s), [], s["ten"])

    def test_moi_spec_deu_khai_duoc_HO_hop_le(self):
        for s in NS.sinh(self.df)[:120]:
            self.assertIn(s["ho"], NP.HO_HOP_LE, s["ten"])

    def test_co_che_la_CAU_giai_thich_khong_phai_ten_tham_so(self):
        """Cong doi mot cau ve VI SAO co nguoi tra tien, khong phai mo ta luat."""
        for s in NS.sinh(self.df)[:60]:
            self.assertGreater(len(s["co_che"]), 60, s["ten"])
            self.assertNotIn("NOI SINH:", s["co_che"])

    def test_loc_hai_dau_kich_hoat(self):
        """Tran tren la 0,95 — KHONG phai 0,60.

        Doi 03/09/2026 sau khi chu du an hoi *"neu thi truong bull thi ve li ta
        cang de kiem loi voi trendfollowing"*: voi tran 0,60, moi co che theo
        XU HUONG bi loai ngay tu bo sinh (mot bo loc xu huong tren thi truong
        bo o trong thi truong 70-90% so bar). Cai chan "mua-giu doi ten" phai
        la phep so O CUNG MUC RUI RO, khong phai mot tran phoi nhiem.
        """
        for s in NS.sinh(self.df):
            self.assertGreaterEqual(s["_ty_le_kich_hoat"], 0.005, s["ten"])
            self.assertLessEqual(s["_ty_le_kich_hoat"], 0.95, s["ten"])

    def test_tran_phoi_nhiem_cho_phep_vung_XU_HUONG(self):
        """Hieu chuan chieu nguoc: tran phai du cao de he xu huong lot qua."""
        self.assertGreaterEqual(
            NS.sinh.__defaults__[-1] if NS.sinh.__defaults__ else 0, 0.90)

    def test_toan_hang_chua_khai_co_che_thi_KHONG_sinh(self):
        """Bo sinh khong duoc de ra co che vo danh roi bat nguoi khac tim y nghia."""
        la = [{"chi_bao": "obv"}]        # co trong ngu phap nhung chua khai CO_CHE_CUA
        self.assertEqual(NS.sinh(self.df, cac_toan_hang=la), [])

    def test_sinh_cap_ton_trong_tran(self):
        r = NS.sinh_cap(self.df, toi_da=40)
        self.assertLessEqual(len(r), 40)

    def test_sinh_cap_co_DUNG_hai_dieu_kien(self):
        for s in NS.sinh_cap(self.df, toi_da=20):
            self.assertEqual(len(s["vao"]), 2, s["ten"])

    def test_khong_co_spec_nao_nhin_truoc(self):
        for s in NS.sinh(self.df)[:60]:
            ok, ly = NP.kiem_khong_nhin_truoc(s, self.df)
            self.assertTrue(ok, f"{s['ten']}: {ly}")

    def test_nguong_KHAC_nhau_giua_hai_doan_du_lieu(self):
        """Diem cot yeu: nguong bam vao chuoi, nen doi chuoi thi nguong phai doi."""
        a = NS.nguong_tu_lich_su(self.df.iloc[:700], {"chi_bao": "rsi", "n": 14})
        b = NS.nguong_tu_lich_su(self.df.iloc[700:], {"chi_bao": "rsi", "n": 14})
        self.assertTrue(any(abs(a[p] - b[p]) > 1e-6 for p in a))


if __name__ == "__main__":
    unittest.main()
