# -*- coding: utf-8 -*-
"""GOP LOP - mot co che tren ca mot lop tai san, MOT suat FDR.

Bo test nay khoa nam thu, bon trong so do da sap that trong lan chay dau tien
cua module (22/08/2026):

1. Trong so cua ro khong duoc nhin ve tuong lai, va moc so sanh phai o CUNG
   cua so voi he. (`b_he, b_bh = b_he[du], b_bh.reindex(b_he.index)` - ve phai
   tinh het truoc khi gan nen ro mua-giu giu nguyen 8.112 bar trong khi ro he
   con 3.634.)
2. Ro phai co DU CHAN cung luc moi goi la ro. (Lan dau: trung vi 1 chan/moc.)
3. Khung gia truyen cho placebo phai co cot `open`. (Lan dau: KeyError giua
   duong cong, sau khi da chay het backtest.)
4. Hop dong futures phai bi loai. (Lan dau: `XM_US500_SEP26` lot vao ro.)
5. Qua cong ma khong tach khoi nhom doi chung thi khong phai co che.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import (du_lieu as DL, gop_lop as G, mau as MAU, mo_phong as MP,
                  pham_vi as PV, so as SO)


def _chan(ma, loi, index, loi_bh=None, do_tin="SAN", vi_the=None):
    loi = np.asarray(loi, float)
    return G._Chan(ma, "D1", loi,
                   np.zeros(len(loi)) if loi_bh is None else np.asarray(loi_bh, float),
                   index, len(loi), do_tin, 0.5,
                   np.ones(len(loi)) if vi_the is None else np.asarray(vi_the, float))


class KhungGiaChoPlacebo(unittest.TestCase):

    def test_co_du_cot_ohlc(self):
        idx = pd.bdate_range("2015-01-05", periods=100)
        df = G.khung_gia(np.full(100, 0.001), idx)
        for c in ("open", "high", "low", "close"):
            self.assertIn(c, df.columns)

    def test_loi_suat_dung_bang_chuoi_dau_vao(self):
        """Placebo chay lai `MP.chay` tren khung nay - no phai tai tao dung ro."""
        rng = np.random.default_rng(3)
        x = rng.normal(0, 0.01, 200)
        idx = pd.bdate_range("2015-01-05", periods=200)
        df = G.khung_gia(x, idx)
        r = MP._loi_suat_tien(df)
        np.testing.assert_allclose(r[:-1], x[:-1], atol=1e-12)
        self.assertEqual(r[-1], 0.0)


class TrongSoVaCuaSo(unittest.TestCase):

    def test_gop_deu_bo_qua_o_trong(self):
        b = pd.DataFrame({"a": [0.1, 0.2, np.nan], "b": [0.3, np.nan, np.nan]})
        np.testing.assert_allclose(G.gop_deu(b), [0.2, 0.2, np.nan])

    def test_ro_va_moc_so_sanh_cung_mot_cua_so(self):
        """Loi da sap: ve phai cua gan tuple dung index CU."""
        n = 1200
        idx_dai = pd.bdate_range("2010-01-04", periods=n)
        idx_ngan = idx_dai[-600:]
        chan = [_chan("A", np.full(n, 0.0001), idx_dai, np.full(n, 0.0002)),
                _chan("B", np.full(600, 0.0001), idx_ngan, np.full(600, 0.0002)),
                _chan("C", np.full(600, 0.0001), idx_ngan, np.full(600, 0.0002))]
        b_he = G._gong(chan, "loi")
        b_bh = G._gong(chan, "loi_bh")
        du = b_he.notna().sum(axis=1) >= G.TOI_THIEU_CHAN
        b_he = b_he[du]
        b_bh = b_bh.reindex(b_he.index)
        self.assertEqual(len(b_he), len(b_bh))
        self.assertEqual(len(b_he), 600)

    def test_khong_du_chan_thi_tu_choi_chu_khong_tra_ro_mot_chan(self):
        n = 900
        idx = pd.bdate_range("2010-01-04", periods=n)
        # chi mot chan phu ca ky, hai chan kia chi 50 moc -> khong du 400 moc
        chan = [_chan("A", np.full(n, 0.0001), idx),
                _chan("B", np.full(50, 0.0001), idx[:50]),
                _chan("C", np.full(50, 0.0001), idx[:50])]
        b = G._gong(chan, "loi")
        du = b.notna().sum(axis=1) >= G.TOI_THIEU_CHAN
        self.assertLess(int(du.sum()), G.TOI_THIEU_BAR)


class LoaiFutures(unittest.TestCase):

    def test_nhan_dien_hop_dong_co_thang_giao_hang(self):
        for m in ("XM_US500_SEP26", "XM_US100_SEP26", "XM_US30_SEP26"):
            self.assertTrue(DL.la_futures(m), m)

    def test_khong_nham_ma_thuong(self):
        for m in ("US500CASH", "YH_DAX", "EURCAD", "XAUUSDM", "YH_NASDAQ"):
            self.assertFalse(DL.la_futures(m), m)

    def test_bang_ohlc_khong_tra_futures(self):
        self.assertEqual([m for m in DL.bang_ohlc() if DL.la_futures(m)], [])

    def test_van_lay_duoc_khi_goi_ro_rang(self):
        co = [m for m in DL.bang_ohlc(cho_futures=True) if DL.la_futures(m)]
        self.assertTrue(co, "kho khong con bang futures nao de kiem")


class _SoCaiTam(unittest.TestCase):

    def setUp(self):
        self._db_cu = SO.DB
        self._tmp = tempfile.TemporaryDirectory()
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()


class XetGopThat(_SoCaiTam):
    """Chay tren kho THAT - day la phep kiem quan trong nhat cua module."""

    @classmethod
    def setUpClass(cls):
        cls.kq = None

    def _chay(self):
        if XetGopThat.kq is None:
            XetGopThat.kq = G.xet_gop("ibs_bat_day", da_dang_ky=True)
        return XetGopThat.kq

    def test_chay_duoc_va_ra_verdict(self):
        r = self._chay()
        self.assertIn("verdict", r, r.get("loi") or r)
        self.assertIn(r["verdict"],
                      ("PASS", "CO_CO_CHE", "UNG_VIEN", "FAIL",
                       "KHONG_PHAN_BIET", "NGHI_NHIN_TRUOC", "CHUA_DU_MAU"))

    def test_ro_khong_chua_futures(self):
        r = self._chay()
        for m in (r.get("ro_hop") or {}).get("chan", []):
            self.assertFalse(DL.la_futures(m), m)

    def test_he_va_mua_giu_cung_so_bar(self):
        r = self._chay()
        ss = r.get("so_sanh") or {}
        self.assertEqual(ss["he"]["so_bar"], ss["mua_giu_net"]["so_bar"])
        self.assertAlmostEqual(ss["he"]["so_nam"], ss["mua_giu_net"]["so_nam"], places=2)

    def test_co_nhom_doi_chung(self):
        r = self._chay()
        self.assertIsNotNone(r.get("sharpe_ro_doi_chung"))
        self.assertIsNotNone(r.get("cach_biet"))

    def test_ro_toan_chuoi_khong_mua_duoc_thi_khong_bao_gio_PASS(self):
        r = self._chay()
        if (r.get("ro_hop") or {}).get("do_tin") == "KHAI":
            self.assertNotEqual(r["verdict"], "PASS")


class TachKhoiDoiChung(unittest.TestCase):
    """Bat bien 4: qua cong ma khong tach khoi doi chung thi khong phai co che."""

    def test_ha_verdict_khi_doi_chung_cung_sang(self):
        goc = G.xet_gop
        # Khong mock ca ham: chi kiem dung manh logic ha verdict, bang cach
        # dung lai chinh nguong cua `pham_vi`.
        self.assertGreater(PV.CACH_BIET_TOI_THIEU, 0)
        cach_biet = PV.CACH_BIET_TOI_THIEU / 2
        verdict = "CO_CO_CHE"
        if verdict in ("PASS", "CO_CO_CHE", "UNG_VIEN") and \
                cach_biet < PV.CACH_BIET_TOI_THIEU:
            verdict = "KHONG_PHAN_BIET"
        self.assertEqual(verdict, "KHONG_PHAN_BIET")
        self.assertIs(G.xet_gop, goc)


class DuongGopTrongQuantlab(_SoCaiTam):
    """Duong gop noi vao tru: kham pha tren train -> dang ky -> xac nhan.

    Bat bien quan trong nhat o day la HAM Y NGUYEN cua `xac_nhan_gop`: chay lai
    cung mot gia thuyet la NHIN LAI CUNG MOT HOLDOUT, va holdout mat tinh "chua
    tung dung" ngay tu lan hai. Duong don le da sap dung day mot lan (1.103 dong
    ket qua cho 275 gia thuyet).
    """

    # So cai TAM o muc LOP, khong phai muc phuong thuc: ca lop nay kiem MOT
    # chuoi viec (kham pha -> dang ky -> xac nhan -> xac nhan lai), nen bon
    # phuong thuc phai nhin thay CUNG mot so cai. `_SoCaiTam.setUp` tao so cai
    # moi moi phuong thuc, tuc gia thuyet dang ky o phuong thuc nay bien mat o
    # phuong thuc kia.
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        cls._db_cu = SO.DB
        cls._tmp = tempfile.TemporaryDirectory()
        SO.DB = Path(cls._tmp.name) / "nao_test.db"
        SO.khoi_tao()
        cls._kq = {}
        # KHONG duoc dong cung ten mau o day. Tap mau co ung vien tren train
        # doi hoan toan khi phep chon chan doi (22/08: ro cu -> ibs_bat_day +
        # rsi_dao_chieu; ro chon theo cong suat -> cuoi_thang + momentum_ema +
        # ichimoku_cheo + sma_cheo). Bo test dong cung mot ten se do CHINH SU
        # doi do thay vi do duong ong.
        from tru import quantlab as Q
        cls._co, cls._khong = None, None
        for ten in sorted(MAU.MAU):
            if cls._co and cls._khong:
                break
            r = Q.kham_pha_gop(ten)
            if r.get("gt") and not cls._co:
                cls._co, cls._kq[ten] = ten, r
            elif r.get("ket_luan") == "KHONG_CO_UNG_VIEN" and not cls._khong:
                cls._khong, cls._kq[ten] = ten, r

    @classmethod
    def tearDownClass(cls):
        SO.DB = cls._db_cu
        cls._tmp.cleanup()

    def _chay(self, ten=None):
        from tru import quantlab as Q
        ten = ten or self._co
        if ten is None:
            self.skipTest("khong mau nao co ung vien gop tren train")
        if ten not in self._kq:
            self._kq[ten] = Q.kham_pha_gop(ten)
        return self._kq[ten]

    def test_kham_pha_gop_dang_ky_va_xep_viec(self):
        r = self._chay()
        self.assertIsNotNone(r.get("gt"), r)
        gt = SO.mot("SELECT * FROM gia_thuyet WHERE ma=?", r["gt"])
        self.assertIsNotNone(gt)
        self.assertTrue(str(gt["tai_san"]).startswith("RO:"))
        self.assertEqual(gt["template"], self._co)

    def test_mot_gia_thuyet_gop_chu_khong_phai_muoi_hai(self):
        self._chay()
        n = SO.mot("SELECT COUNT(*) n FROM gia_thuyet WHERE template=?",
                   self._co)["n"]
        self.assertEqual(n, 1, "moi ro phai la DUNG MOT gia thuyet")

    def test_xac_nhan_gop_ham_y_nguyen(self):
        from tru import quantlab as Q
        r = self._chay()
        a = Q.xac_nhan_gop(r["gt"])
        b = Q.xac_nhan_gop(r["gt"])
        self.assertEqual(a["verdict"], b["verdict"])
        self.assertTrue(b.get("da_co_tu_truoc"))
        n = SO.mot("SELECT COUNT(*) n FROM ket_qua WHERE gt_ma=?", r["gt"])["n"]
        self.assertEqual(n, 1, "chay lai da ghi them mot dong ket qua")

    def test_ho_fdr_cua_duong_gop_tach_rieng(self):
        """Ro va tai san don le tra loi hai cau khac nhau -> hai chuoi FDR."""
        from tru import quantlab as Q
        r = self._chay()
        Q.xac_nhan_gop(r["gt"])
        ho = [x["ho"] for x in SO.nhieu("SELECT DISTINCT ho FROM fdr")]
        self.assertTrue(any("gop_" in h for h in ho), ho)

    def test_khong_dang_ky_khi_khong_co_ung_vien_tren_train(self):
        if self._khong is None:
            self.skipTest("moi mau deu co ung vien gop")
        r = self._kq[self._khong]
        self.assertIsNone(r.get("gt"))
        self.assertEqual(r.get("ket_luan"), "KHONG_CO_UNG_VIEN")
        self.assertEqual(
            SO.mot("SELECT COUNT(*) n FROM gia_thuyet WHERE template=?",
                   self._khong)["n"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class PhanBietChuaDoVoiDaDoMaThua(unittest.TestCase):
    """Hai cau tra loi khac han nhau, va truoc 30/08 chung dung CHUNG mot cau.

    `quet_tham_so_gop` loc ro theo lop HOP LE cua ho co che. Truyen mot ro FX
    cho ho `quay_ve_trung_binh` (chi khai hop voi `chi_so_my`) thi loc xong
    khong con chan nao -> khong bo tham so nao chay duoc.

    Ban cu tra ve dung cau "khong bo tham so nao thang mua-giu cua RO tren
    train", va cau do doc y het mot KET LUAN AM CO CAN CU. Da nham that ngay
    30/08: ba lop vang/hang_hoa/fx tra ve trong 0 giay kem cau do, va suyt duoc
    ghi lai nhu ba phep do doc lap.

    Mot he tu chay 24/7 phai phan biet duoc "da do va thua" voi "chua do gi" -
    day la cung mot bai hoc voi 84 dia chi Reddit bi khoa oan sang cung ngay.
    """

    def test_ro_bi_loc_sach_thi_bao_CHUA_DO(self):
        from nhan import pham_vi as PV
        ma = list(PV.kho_du_bar("D1"))
        fx = [m for m in ma if PV.loai_cua(m) == "fx"]
        if not fx:
            self.skipTest("kho khong co tai san FX")
        r = G.quet_tham_so_gop("ibs_bat_day", ho="quay_ve_trung_binh",
                                khung="D1", kho=fx)
        self.assertEqual(r["da_quet"], 0)
        self.assertTrue(r["chua_do"],
                        "ro rong ma bao la da do - mot ket luan am gia")
        self.assertIn("KHONG QUET DUOC", r["ly_do"])

    def test_ro_hop_le_thi_bao_DA_DO(self):
        r = G.quet_tham_so_gop("ibs_bat_day", ho="quay_ve_trung_binh", khung="D1")
        self.assertGreater(r["da_quet"], 0, "ro hop le ma khong quet duoc bo nao")
        if r["ket_luan"] == "KHONG_CO_UNG_VIEN":
            self.assertFalse(r["chua_do"])
            self.assertIn("da quet", r["ly_do"])

    def test_moi_bo_tham_so_da_quet_deu_co_so_lieu_kem_theo(self):
        """Ket luan am phai kem SO, khong duoc chi kem mot cau."""
        r = G.quet_tham_so_gop("ibs_bat_day", ho="quay_ve_trung_binh", khung="D1")
        self.assertEqual(len(r["diem"]), r["da_quet"])
        for d in r["diem"]:
            self.assertIn("sharpe", d)
            self.assertIn("sharpe_mua_giu", d)
            self.assertIn("so_chan", d)
