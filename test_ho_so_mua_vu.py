# -*- coding: utf-8 -*-
"""Bai kiem cho `nhan/ho_so_mua_vu.py` - dac biet la `thu_da_sua`.

Sua 13/09/2026: chu du an chi ra ham `thu_da_sua` ban dau chi doan nhan THU qua
THONG KE GIAN TIEP (ty le bar T6/CN thap/cao), va canh bao no phat ra ("nhan thu
lech mot ngay") khong chan duoc gi - 41/50 phat hien mua vu M3 van "di qua" mang
theo canh bao ma khong ai doc.

Sua tai goc: doc truc tiep GIO UTC ma bar dong dau (`_gio_utc_chiem_da_so`) -
day la NGUYEN NHAN CO CHE that (broker dong bar luc 21:00 UTC = nua dem gio may
chu UTC+3, nen ngay-lich UTC luon it hon ngay giao dich that mot ngay), khong
con la mot phep doan tu hien tuong (%T6/%CN). Tin hieu thong ke cu duoc GIU LAI
lam xac nhan cheo doc lap; neu hai tin hieu MAU THUAN (hoac gio khong doc duoc
dong nhat) thi `thu_da_sua` phai tra `(None, ghi_chu)` - CHOT CHAN de goi
(`quet_mot`) ha M3 ve CHUA_DO_DUOC, KHONG duoc doan va khong duoc de mot canh
bao troi qua ma khong chan gi.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import ho_so_mua_vu as MV      # noqa: E402


def _idx_broker(n_tuan=30, gio=21):
    """Mo phong bar SAN/broker: moi tuan 5 bar CN,T2,T3,T4,T5 (dayofweek 6,0,1,2,3),
    dong dau luc `gio`:00 UTC - dung mau bay da sap that (khong co T6, co CN)."""
    d0 = pd.Timestamp("2021-01-03", tz="UTC")   # 2021-01-03 la Chu Nhat
    ts = [d0 + pd.Timedelta(days=7 * w + delta, hours=gio)
         for w in range(n_tuan) for delta in range(5)]
    return pd.DatetimeIndex(ts)


def _idx_yahoo(n_tuan=30, gio=0):
    """Mo phong bar Yahoo: T2-T6 binh thuong, dong dau luc `gio`:00, KHONG lech."""
    d0 = pd.Timestamp("2021-01-04")             # 2021-01-04 la Thu Hai
    ts = [d0 + pd.Timedelta(days=7 * w + delta, hours=gio)
         for w in range(n_tuan) for delta in range(5)]
    return pd.DatetimeIndex(ts)


class TinHieuGocGioUTC(unittest.TestCase):
    """`_gio_utc_chiem_da_so` - nen tang cua ca phep sua."""

    def test_doc_dung_gio_dong_nhat(self):
        self.assertEqual(MV._gio_utc_chiem_da_so(_idx_broker(gio=21)), 21)
        self.assertEqual(MV._gio_utc_chiem_da_so(_idx_yahoo(gio=0)), 0)

    def test_gio_khong_dong_nhat_tra_none(self):
        idx = _idx_broker(gio=21)
        arr = idx.to_list()
        for i in range(0, len(arr), 3):          # ~1/3 so bar doi gio -> < 95%
            arr[i] = arr[i].replace(hour=15)
        self.assertIsNone(MV._gio_utc_chiem_da_so(pd.DatetimeIndex(arr)))

    def test_index_rong_tra_none(self):
        self.assertIsNone(MV._gio_utc_chiem_da_so(pd.DatetimeIndex([])))


class ThuDaSuaCaHaiTinHieuKhopNhau(unittest.TestCase):
    """Truong hop THAT trong kho (13/09/2026): gio UTC va thong ke T6/CN luon
    khop nhau tren ca 159 ma - day la duong di BINH THUONG, khong chot chan."""

    def test_broker_gio_21_duoc_dich_dung_1_ngay(self):
        idx = _idx_broker(gio=21)
        thu, ghi = MV.thu_da_sua(idx)
        self.assertIsNotNone(thu)
        # CN (dayofweek=6) phai thanh T2 (0), T2(0)->T3(1), ..., T5(3)->T6(4)
        raw = idx.dayofweek.to_numpy()
        np.testing.assert_array_equal(thu, (raw + 1) % 7)
        self.assertIn("DA SUA +1 ngay", ghi)
        self.assertIn("21", ghi)

    def test_yahoo_gio_0_khong_dich(self):
        idx = _idx_yahoo(gio=0)
        thu, ghi = MV.thu_da_sua(idx)
        self.assertIsNotNone(thu)
        np.testing.assert_array_equal(thu, idx.dayofweek.to_numpy())
        self.assertEqual(ghi, "")

    def test_khong_dich_thi_khong_con_ban_ghe_cuoi_tuan_bat_thuong(self):
        """Dau hieu nhan mot phep dich SAI (docstring `thu_da_sua`): sau khi
        dich van con T7/CN mang gia tri phien day du. O day XAC NHAN nguoc
        lai: sau khi dich DUNG, khong con nhan T6/CN nao ca (dung 5 ngay lam
        viec T2-T6)."""
        idx = _idx_broker(gio=21)
        thu, _ = MV.thu_da_sua(idx)
        self.assertEqual(set(thu.tolist()), {0, 1, 2, 3, 4})


class ChotChanKhiHaiTinHieuMauThuan(unittest.TestCase):
    """Phan MOI 13/09/2026 - day la dieu chu du an doi: khong con duong nao de
    mot nhan KHONG XAC DINH duoc di qua duoi dang "dat=True kem canh bao"."""

    def test_gio_21_nhung_tuan_binh_thuong_la_mau_thuan(self):
        """Gio noi CAN dich (21:00 UTC), nhung phan bo ngay la T2-T6 binh
        thuong (khong dinh dau hieu T6=0%/CN cao) - HAI TIN HIEU DOC LAP
        khong khop nhau, khong duoc doan, phai tra ve None."""
        idx = _idx_yahoo(gio=21)      # T2-T6 binh thuong nhung dong luc 21h
        thu, ghi = MV.thu_da_sua(idx)
        self.assertIsNone(thu)
        self.assertIn("MAU THUAN", ghi)

    def test_gio_khong_doc_duoc_nhung_thong_ke_nghi_ngo_thi_khong_doan(self):
        idx = _idx_broker(gio=21)
        arr = idx.to_list()
        for i in range(0, len(arr), 3):
            arr[i] = arr[i].replace(hour=15)     # pha vo tinh dong nhat cua gio
        thu, ghi = MV.thu_da_sua(pd.DatetimeIndex(arr))
        self.assertIsNone(thu)
        self.assertIn("KHONG RO", ghi)

    def test_gio_la_khong_phai_0_hay_gan_nua_dem_thi_khong_doan(self):
        """Gio = 6:00 (khong phai 0, khong phai >=12) la mot mau hinh CHUA
        BIET - khong duoc suy dien la can hay khong can dich."""
        idx = _idx_yahoo(gio=6)
        thu, ghi = MV.thu_da_sua(idx)
        # thong ke o day la BINH THUONG (T2-T6 deu) nen khong nghi ngo gi ca,
        # va gio la (6) khong xac dinh -> tra nguyen ban, khong canh bao.
        self.assertIsNotNone(thu)
        np.testing.assert_array_equal(thu, idx.dayofweek.to_numpy())
        self.assertEqual(ghi, "")


class QuetMotHaVeCHuaDoDuoc(unittest.TestCase):
    """Tich hop: `quet_mot` phai ha M3 ve CHUA_DO_DUOC (khong phai AM, khong
    phai DAT) khi `thu_da_sua` tra None - dung ba trang thai cua du an."""

    def _df_gia(self, idx, hat=3):
        g = np.random.default_rng(hat)
        n = len(idx)
        c = 100.0 * np.exp(np.cumsum(g.normal(0, 0.01, n)))
        return pd.DataFrame({"open": c, "high": c * 1.001, "low": c * 0.999,
                             "close": c}, index=idx)

    def test_m3_thanh_chua_do_duoc_khi_mau_thuan(self):
        idx = _idx_yahoo(gio=21, n_tuan=120)     # du >=200 quan sat, mau thuan
        df = self._df_gia(idx)
        import unittest.mock as mock
        with mock.patch("nhan.du_lieu.nap", return_value=df):
            ra = MV.quet_mot("MA_GIA_LAP_MAU_THUAN", "D1")
        m3 = ra["M3_ngay_trong_tuan"]
        self.assertEqual(m3.get("trang_thai"), "CHUA_DO_DUOC")
        self.assertFalse(m3.get("dat"))
        self.assertIn("MAU THUAN", m3.get("vi_sao", ""))
        # va `cau_tra_loi` KHONG duoc dem M3 nhu mot "CO" tim thay duoc
        self.assertNotIn("M3_ngay_trong_tuan", ra.get("cau_tra_loi", ""))

    def test_m3_van_binh_thuong_khi_hai_tin_hieu_khop(self):
        idx = _idx_broker(gio=21, n_tuan=120)
        df = self._df_gia(idx)
        import unittest.mock as mock
        with mock.patch("nhan.du_lieu.nap", return_value=df):
            ra = MV.quet_mot("MA_GIA_LAP_KHOP", "D1")
        m3 = ra["M3_ngay_trong_tuan"]
        self.assertNotEqual(m3.get("trang_thai"), "CHUA_DO_DUOC")
        self.assertIn("canh_bao_nhan", m3)


if __name__ == "__main__":
    unittest.main()
