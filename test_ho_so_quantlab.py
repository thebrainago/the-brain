# -*- coding: utf-8 -*-
"""Kiem bon module HO SO cua QUANTLAB: song · mua vu · tuong quan · quy luat song.

`test_hien_phap` doi moi module phai co nguoi kiem. Nhung viet test cho mot bo DO
DAC thi de sa vao kieu "goi duoc ham la xanh" - vo dung. Nen o day moi bai kiem
nham vao mot CACH HONG DA XAY RA THAT trong chinh cac module nay:

  ho_so_song        zigzag phai LUAN PHIEN dinh-day; do tre xac nhan khong duoc am
  ho_so_mua_vu      nhan THU cua FX lech mot ngay (FX dong 22:00 thu Sau UTC nen
                    bar cuoi tuan mang nhan T7/CN); va nhom qua nho thi khong
                    duoc phep tuyen bo gi
  ho_so_tuong_quan  "cap am nhat" tung toan la NGHICH DAO CO HOC (chung mot dong
                    tien, nguoc ve) va "cap cao nhat" toan la TRUNG CONG CU
  quy_luat_song     p hai phia phai doi xung; mot phia se goi mot nua so nhieu
                    ngau nhien la "quy luat"
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import ho_so_mua_vu as MV      # noqa: E402
from nhan import ho_so_song as HS        # noqa: E402
from nhan import ho_so_tuong_quan as TQ  # noqa: E402
from nhan import quy_luat_song as QL     # noqa: E402


def khung_rang_cua(n=400, bien=6.0, chu_ky=20, hat=11):
    """Chuoi co SONG THAT (rang cua + nhieu) de zigzag co cai de bat."""
    rng = np.random.default_rng(hat)
    t = np.arange(n)
    c = 100 + bien * np.sin(2 * np.pi * t / chu_ky) + np.cumsum(
        rng.normal(0, 0.25, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + 0.6
    l = np.minimum(o, c) - 0.6
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                        index=pd.date_range("2020-01-01", periods=n, freq="D"))


# --------------------------------------------------------------- ho_so_song
class ZigzagPhaiLuanPhien(unittest.TestCase):
    def test_dinh_va_day_xen_ke(self):
        moc = HS.zigzag(khung_rang_cua())["moc"]
        self.assertGreater(len(moc), 4, "chuoi rang cua ma khong sinh du diem xoay")
        for a, b in zip(moc, moc[1:]):
            self.assertNotEqual(a["loai"], b["loai"],
                                "hai diem xoay lien tiep cung loai")
            self.assertLess(a["i"], b["i"], "diem xoay khong tang theo thoi gian")

    def test_do_tre_xac_nhan_khong_am(self):
        """Do tre xac nhan la SO BAR phai doi sau mot dinh/day moi biet no la
        dinh/day. Am = he biet truoc khi no thanh dinh = nhin truoc."""
        tre = HS.dac_tinh_song(khung_rang_cua())["tre_xac_nhan_bar"]
        for k in ("trung_vi", "p75", "toi_da"):
            self.assertGreaterEqual(float(tre[k]), 0.0, k)
        self.assertLessEqual(float(tre["trung_vi"]), float(tre["toi_da"]))

    def test_moi_moc_deu_mang_do_tre_cua_rieng_no(self):
        """Co che dung `moc_ky`/magnetic phai biet lui bao nhieu bar. Mot moc
        khong co do tre la mot moc dung duoc ngay tai dinh - khong co that."""
        for m in HS.zigzag(khung_rang_cua())["moc"]:
            self.assertIn("tre_xac_nhan", m)
            self.assertGreaterEqual(int(m["tre_xac_nhan"]), 0)

    def test_chuoi_phang_khong_sinh_song_ao(self):
        n = 500
        c = np.full(n, 100.0)
        df = pd.DataFrame({"open": c, "high": c, "low": c, "close": c},
                          index=pd.date_range("2020-01-01", periods=n, freq="D"))
        self.assertLessEqual(len(HS.zigzag(df)["moc"]), 2,
                             "gia phang tuyet doi ma van ra song")

    def test_chuoi_qua_ngan_van_tra_ve_khoa_moc(self):
        """Ham khong duoc doi HINH DANG tra ve theo du lieu vao: nguoi goi
        `zigzag(df)["moc"]` phai doc duoc loi chu khong phai nem KeyError."""
        n = 50
        c = 100 + np.arange(n) * 0.1
        df = pd.DataFrame({"open": c, "high": c + 0.2, "low": c - 0.2, "close": c},
                          index=pd.date_range("2020-01-01", periods=n, freq="D"))
        z = HS.zigzag(df)
        self.assertIn("moc", z)
        self.assertEqual(z["moc"], [])
        self.assertIn("loi", z)


# ------------------------------------------------------------ ho_so_mua_vu
class NhanThuCuaFX_PhaiDuocSUA(unittest.TestCase):
    """FX chay CN 22:00 -> T6 22:00 UTC. Bar D1 dong 22:00 mang nhan cua ngay
    HOM TRUOC phien, nen chuoi 'khong co thu Sau, co Chu Nhat' la dau hieu lech
    mot ngay chu khong phai mot phat hien mua vu.

    SUA 13/09/2026: ban dau lop nay dung idx NAIVE (khong tz, gio 00:00) de mo
    phong "FX" - nhung do KHONG PHAI hinh dang du lieu FX THAT trong kho (bar
    FX/CFD SAN dong dau 21:00 UTC dong nhat, xem `ho_so_mua_vu._gio_utc_
    chiem_da_so`). Voi bo dem CHOT CHAN moi (gio UTC doc lap xac nhan thong
    ke T6/CN), mot idx naive-00:00-nhung-mang-mau-hinh-T6/CN la MAU THUAN va
    dung phai tra ve None - bai kiem CU kiem tra bang `assertNotIn(5, set(...))`
    tren ket qua do van "xanh" mot cach VO NGHIA (`set(np.unique(None))` =
    `{None}`, va `5 not in {None}` la True du dung hay sai). Da sua idx cho
    DUNG hinh dang that (tz=UTC, gio=21) va them bai kiem rieng cho truong hop
    MAU THUAN de khong con lo hong "test xanh nhung khong kiem gi ca" nay.
    """

    def _idx_fx(self, tuan=30, gio=21, tz="UTC"):
        # dung bar: CN..T5 (dai dien cho phien T2..T6), KHONG co T6, dong dau
        # gio 21:00 UTC - DUNG hinh dang that cua 82/159 ma nguon SAN trong kho.
        d0 = pd.Timestamp("2020-01-05", tz=tz)     # mot Chu Nhat
        ngay = [d0 + pd.Timedelta(days=7 * w + k, hours=gio)
               for w in range(tuan) for k in range(5)]
        return pd.DatetimeIndex(ngay)

    def test_chuoi_thieu_thu_sau_duoc_dich_len_mot_ngay(self):
        idx = self._idx_fx()
        nhan, cach = MV.thu_da_sua(idx)
        self.assertIsNotNone(nhan, "gio UTC=21 + mau hinh T6/CN phai KHOP nhau "
                             "va dich duoc, khong duoc tra None")
        ten = set(np.unique(nhan))
        self.assertNotIn(5, ten, "sau khi sua van con nhan thu Bay")
        self.assertNotIn(6, ten, "sau khi sua van con nhan Chu Nhat")
        self.assertIsInstance(cach, str)
        self.assertNotEqual(cach, "")

    def test_chuoi_du_nam_ngay_thuong_thi_KHONG_bi_dich(self):
        # Gio=0 (kieu Yahoo) + T2-T6 binh thuong: DAY moi la hinh dang that cua
        # nguon KHONG can dich trong kho (77/159 ma). Dung gio=21 o day se la
        # mot to hop khong co that (hour=21 luon di kem mau hinh CN/T6 trong
        # toan bo du lieu that) va dung bi CHOT CHAN bat - xem bai kiem ke tiep.
        d0 = pd.Timestamp("2020-01-06")             # thu Hai, naive
        ngay = [d0 + pd.Timedelta(days=7 * w + k)
               for w in range(30) for k in range(5)]
        nhan, ghi = MV.thu_da_sua(pd.DatetimeIndex(ngay))
        self.assertIsNotNone(nhan)
        self.assertEqual(set(np.unique(nhan)), {0, 1, 2, 3, 4},
                         "chuoi da dung lai bi dich them")
        self.assertEqual(ghi, "")

    def test_mau_hinh_T6_CN_nhung_gio_UTC_noi_khac_thi_KHONG_DOAN(self):
        """Day chinh la lo hong da sua: mot chuoi mang dung "dau hieu thong ke"
        (khong T6, nhieu CN) nhung GIO GOC lai noi "khong can dich" (vd du lieu
        naive/Yahoo bi ghep nham voi mot chu ky FX) - hai tin hieu MAU THUAN,
        `thu_da_sua` phai tra None thay vi tin mu quang vao thong ke."""
        idx = self._idx_fx(gio=0, tz=None)         # gio noi KHONG can dich
        nhan, ghi = MV.thu_da_sua(idx)
        self.assertIsNone(nhan)
        self.assertIn("MAU THUAN", ghi)

    def test_nguong_nhom_toi_thieu_ton_tai_va_hop_le(self):
        self.assertGreater(MV.TY_LE_NHOM_TOI_THIEU, 0.0)
        self.assertLessEqual(MV.TY_LE_NHOM_TOI_THIEU, 1.0)


# ------------------------------------------------------- ho_so_tuong_quan
class TuongQuanPhaiLOC_QUAN_HE_GIA(unittest.TestCase):
    def test_chung_dong_tien_nguoc_ve_bi_danh_dau(self):
        self.assertIn("NGUOC", TQ.quan_he_co_hoc("EURGBP", "GBPDKK"))
        self.assertIn("cung ve", TQ.quan_he_co_hoc("EURUSD", "GBPUSD"))

    def test_khong_chung_dong_tien_thi_khong_danh_dau(self):
        self.assertEqual(TQ.quan_he_co_hoc("EURAUD", "NZDCHF"), "")

    def test_dong_tien_NEO_duoc_quy_ve_goc(self):
        """HKD neo cung vao USD: AUDHKD that ra la AUDUSD. Bang chung do duoc
        tren chinh du lieu: AUDHKD|AUDUSD = +0,969."""
        self.assertEqual(TQ.NEO.get("HKD"), "USD")
        self.assertNotEqual(TQ.quan_he_co_hoc("AUDHKD", "USDCAD"), "",
                            "AUDHKD vs USDCAD la cuoc vao USD hai chieu, phai bi bat")

    def test_trung_cong_cu(self):
        self.assertTrue(TQ.trung_cong_cu("US500CASH", "XM_US500CASH"))
        self.assertTrue(TQ.trung_cong_cu("SP500", "TS_SPY"))
        self.assertTrue(TQ.trung_cong_cu("XM_US100CASH", "XM_US100_SEP26"))
        self.assertFalse(TQ.trung_cong_cu("EURUSD", "GBPUSD"))

    def test_on_dinh_KHONG_phai_thuoc_cung_dau(self):
        """Ban dau `on_dinh` dem 'cua so cung DAU voi r toan mau' va no tra 1,000
        cho gan nhu moi cap - mot thuoc do khong phan biet duoc gi. Gio no do
        khoang cach toi r, nen hai cap co cung dau nhung khac do on dinh phai ra
        hai so khac nhau."""
        n = 1200
        rng = np.random.default_rng(5)
        a = pd.Series(rng.normal(0, 1, n))
        on = a * 0.8 + rng.normal(0, 0.3, n)          # on dinh
        doi = a * np.where(np.arange(n) < n // 2, 1.6, 0.05) + rng.normal(0, 0.3, n)
        r1 = TQ.mot_cap(a, on)
        r2 = TQ.mot_cap(a, doi)
        self.assertIsNotNone(r1); self.assertIsNotNone(r2)
        self.assertGreater(r1["on_dinh"], r2["on_dinh"],
                           "cap doi tinh chat giua chung ma do on dinh khong thap hon")

    def test_moi_khung_mot_tep_rieng(self):
        """Dung chung mot tep thi khung chay sau xoa ket qua khung chay truoc -
        loi da mac 12/09/2026."""
        self.assertNotEqual(str(TQ.kho_cua("D1")), str(TQ.kho_cua("H4")))


# ------------------------------------------------------- quy_luat_song
class PHaiPhiaPhaiDOI_XUNG(unittest.TestCase):
    def test_lech_hai_dau_cho_p_nhu_nhau(self):
        null = np.arange(0.0, 100.0)
        cao = QL._p_hai_phia(200.0, null)
        thap = QL._p_hai_phia(-100.0, null)
        self.assertAlmostEqual(cao, thap, places=12,
                               msg="p hai phia khong doi xung")

    def test_o_giua_null_thi_p_lon(self):
        null = np.arange(0.0, 100.0)
        self.assertGreater(QL._p_hai_phia(float(np.median(null)), null), 0.4)

    def test_p_khong_bao_gio_bang_khong(self):
        """p = 0 la khong the voi hoan vi huu han; cong thuc phai la (k+1)/(n+1)."""
        null = np.zeros(50)
        self.assertGreater(QL._p_hai_phia(1e9, null), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
