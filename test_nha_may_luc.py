# -*- coding: utf-8 -*-
"""NHA MAY LUC: cay mot edge biet truoc, do xac suat pheu phat hien ra no.

Bo test nay thay ban dau (DS, 23/08). Ban do co bon bai va mot bai trong so do
**bat buoc dung hanh vi SAI**:

    def test_cay_edge_lam_doi_trung_binh(self):
        \"\"\"Cay edge duong lam tang trung binh loi suat.\"\"\"
        self.assertGreater(np.mean(r_edged), np.mean(r0))

Nang trung binh loi suat cua ca chuoi chinh la cay mot XU HUONG THI TRUONG,
khong phai mot edge: mua-giu o trong thi truong 100% thoi gian se huong tron
ven, con co che chi ~18% - nen cang cay manh, co che cang THUA mua-giu. Do that
truoc khi sua: delta 200 bps cho mua-giu Sharpe 6,67 va co che 2,41.

Mot phep cay DUNG phai giu ba thu cung luc, va day la ba bai kiem dau tien:
  1. TIN HIEU khong doi  -> IBS tung bar giu nguyen
  2. DRIFT khong doi     -> Sharpe mua-giu giu nguyen
  3. PHAN THUONG tang    -> Sharpe co che tang theo delta
Thieu bat ky cai nao thi duong cong luc do mot thu khac chu khong do luc.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import du_lieu as DL
from nhan import nha_may_null as NM
from nhan import sang_loc as SL


def _chuoi_that():
    for ma, khung in (("US500CASH", "D1"), ("EURCAD", "D1"), ("AUDNZD", "D1")):
        try:
            d = DL.nap(ma, khung)
        except Exception:
            continue
        if d is not None and len(d) > 1900:
            return d.iloc[:1900], ma, khung
    return None, None, None


class PhepCay(unittest.TestCase):
    """Ba tinh chat cua mot phep cay dung. Ba bai nay chay nhanh."""

    def setUp(self):
        self.df, self.ma, self.khung = _chuoi_that()
        if self.df is None:
            self.skipTest("khong co chuoi gia that")

    def test_1_tin_hieu_khong_doi(self):
        """IBS tung bar phai giu nguyen: neu doi thi ta vua doi LUAT vua doi
        PHAN THUONG, va khong biet cai nao gay ra khac biet."""
        ibs0, _ = NM._ibs_cua(self.df)
        for delta in (5.0, 50.0):
            d2, _ = NM.cay_edge_vao_gia(self.df, delta)
            ibs1, _ = NM._ibs_cua(d2)
            self.assertLess(float(np.max(np.abs(ibs0 - ibs1))), 1e-9,
                            f"delta={delta} lam doi IBS")

    def test_2_mua_giu_KHONG_huong(self):
        """Bai kiem thay cho `test_cay_edge_lam_doi_trung_binh` cua ban cu.

        Ban cu bat buoc trung binh loi suat PHAI tang - tuc bat buoc mua-giu
        cung huong edge. Bai nay bat dieu nguoc lai, va no moi la dieu dung."""
        from nhan import mo_phong as MP
        cp = SL._chi_phi_cua(self.ma)
        goc = MP.mua_giu(self.df, cp, ma=self.ma, khung=self.khung)
        s_goc = float(np.mean(goc.loi) / max(np.std(goc.loi), 1e-12))
        for delta in (10.0, 50.0):
            d2, _ = NM.cay_edge_vao_gia(self.df, delta)
            r = MP.mua_giu(d2, cp, ma=self.ma, khung=self.khung)
            s = float(np.mean(r.loi) / max(np.std(r.loi), 1e-12))
            self.assertLess(abs(s - s_goc), 0.02 * max(abs(s_goc), 0.05) + 0.01,
                            f"delta={delta} lam doi mua-giu ({s_goc:.4f} -> {s:.4f})")

    def test_3_phan_thuong_tang_theo_delta(self):
        """Va phai tang DON DIEU. Chi can 'co tang' thi mot phep cay lech cho
        van qua duoc - do that: cay nham cho engine an lai chi nang Sharpe tu
        0,127 len 0,138 khi delta = 20 bps."""
        from nhan import mau as MAU, mo_phong as MP, do_luong as DO
        cp = SL._chi_phi_cua(self.ma)
        diem = []
        for delta in (0.0, 10.0, 30.0):
            d2, _ = NM.cay_edge_vao_gia(self.df, delta)
            th = MAU.sinh("ibs_bat_day", d2, {"nguong": NM.NGUONG_IBS})
            kq = MP.chay(d2, th, cp, ma=self.ma, khung=self.khung)
            diem.append(DO.chi_so(kq.loi, kq.index, kq.vi_the).get("sharpe") or 0.0)
        self.assertLess(diem[0], diem[1], f"khong tang tu 0 len 10 bps: {diem}")
        self.assertLess(diem[1], diem[2], f"khong tang tu 10 len 30 bps: {diem}")
        self.assertGreater(diem[2] - diem[0], 0.5,
                           f"cay 30 bps ma Sharpe chi tang {diem[2]-diem[0]:.3f}")

    def test_khong_cay_gi_thi_khong_doi_gi(self):
        d2, _ = NM.cay_edge_vao_gia(self.df, 0.0)
        for cot in ("open", "high", "low", "close"):
            self.assertLess(
                float(np.max(np.abs(d2[cot].to_numpy() - self.df[cot].to_numpy()))),
                1e-6, cot)


class DuongCongLuc(unittest.TestCase):
    """Bai kiem cham (chay pheu that). Giu so_lan nho."""

    def setUp(self):
        self.df, self.ma, self.khung = _chuoi_that()
        if self.df is None:
            self.skipTest("khong co chuoi gia that")

    def test_cau_truc_day_du(self):
        ra = NM.duong_cong_luc(self.ma, self.khung, cac_delta=(0.0, 50.0), so_lan=2)
        self.assertIn("bang", ra)
        for d in ("0.0", "50.0"):
            self.assertIn(d, ra["bang"])
            self.assertIn("ty_le_phat_hien_pct", ra["bang"][d])
            self.assertIn("dung_o_vong", ra["bang"][d])
        self.assertIn("MDE_bps_moi_lenh", ra)
        self.assertIn("duong_tinh_gia_pct", ra)
        self.assertEqual(ra["tai_san"], self.ma)

    def test_delta_0_khong_lot(self):
        """CHIEU NGHICH. Delta=0 la null: khong co edge nao ca. Lot o day nghia
        la cong dang nhan bua."""
        ra = NM.duong_cong_luc(self.ma, self.khung, cac_delta=(0.0,), so_lan=4)
        self.assertLessEqual(ra["bang"]["0.0"]["ty_le_phat_hien_pct"], 25.0)

    def test_delta_lon_thi_lot(self):
        """CHIEU THUAN, va la bai quan trong nhat: mot cong tu choi TAT CA se
        dat bai kiem tren voi diem tuyet doi. Chi hai bai di cung nhau moi noi
        len duoc dieu gi."""
        ra = NM.duong_cong_luc(self.ma, self.khung, cac_delta=(80.0,), so_lan=4)
        self.assertGreaterEqual(ra["bang"]["80.0"]["ty_le_phat_hien_pct"], 50.0)

    def test_MDE_noi_ro_khi_nam_ngoai_dai_quet(self):
        """Khong dat muc nao thi phai NOI RA, khong tra None trong - 'None' doc
        nhu 'khong co MDE' trong khi su that la 'MDE lon hon moi muc da thu'."""
        ra = NM.duong_cong_luc(self.ma, self.khung, cac_delta=(0.0, 1.0), so_lan=2)
        if ra["MDE_bps_moi_lenh"] is None:
            self.assertIn("ngoai dai", ra["ghi_chu"])


class NhaMayNull(unittest.TestCase):
    """Chieu con lai: cong co NHAN BUA khong. Doc cung `DuongCongLuc`."""

    def setUp(self):
        self.df, self.ma, self.khung = _chuoi_that()
        if self.df is None:
            self.skipTest("khong co chuoi gia that")

    def test_chuoi_null_thanh_bar_dung_hinh(self):
        """Bar null phai co IBS phan phoi THAT (khong phai 0,5 o moi bar) va
        high >= close >= low. Neu bar null co IBS hang so thi co che khong bao
        gio kich hoat va ty le lot bang 0 - dat bai kiem null vi ly do sai."""
        from nhan import du_lieu as DL
        df = DL.nap(self.ma, self.khung)
        r = NM.null_block_bootstrap(self.ma, self.khung, so_chuoi=1)[0]
        d = NM.bar_tu_chuoi_null(r, df, hat=1)
        self.assertIsNotNone(d)
        ibs, _ = NM._ibs_cua(d)
        self.assertGreater(float(np.std(ibs)), 0.1, "IBS gan nhu hang so")
        self.assertGreater(float(np.mean(ibs < NM.NGUONG_IBS)), 0.02,
                           "khong bar nao kich hoat duoc co che")
        self.assertTrue(bool((d["high"] >= d["close"] - 1e-9).all()))
        self.assertTrue(bool((d["low"] <= d["close"] + 1e-9).all()))

    def test_null_khong_lot_nhieu(self):
        """Duoi gia thuyet null, ty le lot phai thap. Doc CUNG bai
        `test_delta_lon_thi_lot` - mot cong tu choi tat ca dat bai nay tuyet doi."""
        r = NM.chay_pheu_tren_null(self.ma, self.khung, so_chuoi=6)
        self.assertLessEqual(r["ty_le_lot_pct"], 25.0)
        self.assertGreater(r["so_chuoi"], 0, "khong chuoi null nao chay duoc")

    def test_ba_phuong_phap_null_deu_chay(self):
        r = NM.null_day_du(self.ma, self.khung, so_chuoi=3)
        for pp in ("block_bootstrap", "garch", "permute_time"):
            self.assertIn(pp, r["theo_pp"])
            self.assertNotIn("loi", r["theo_pp"][pp], f"{pp}: {r['theo_pp'][pp]}")
            self.assertEqual(r["theo_pp"][pp].get("so_loi", 0), 0, pp)
            self.assertGreater(r["theo_pp"][pp]["so_chuoi"], 0, pp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
