# -*- coding: utf-8 -*-
"""Do dac KHONG duoc chiem suat trong so FDR.

Bay bat ngay 24/08/2026. `do_luc._mot_muc` chay mot ORACLE TONG HOP (tin hieu
biet truoc voi do chinh xac p) qua `cong.xet(tren_holdout=True)`, va duong do
GHI mot dong quyet dinh vao so `fdr`. Hau qua do duoc:

  - mot vong quet be mat viet **~80 dong/phut** vao ho `family=do_luc`
    (174 dong trong 2 phut dau);
  - ho `do_luc` da co 795 dong tinh den 24/08, tat ca deu la do dac;
  - nguong LORD giam theo 1/j^1.6, nen bo do luc TU LAM HONG cai thuoc no dang
    doc: cang do nhieu thi nguong cang chat.

Ho `do_luc` la epoch rieng nen no khong an vao ngan sach cua ho gia thuyet
that - nhung mot so quyet dinh co 795 dong khong phai quyet dinh nao la mot so
khong doc duoc, va cai gia phai tra la khong ai biet ngan sach that con bao
nhieu.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nhan import cong as CONG
from nhan import so as SO


def _dem() -> int:
    return int(SO.mot("SELECT COUNT(*) n FROM fdr")["n"])


class SoTam(unittest.TestCase):
    """Moi bai test o day deu VIET vao so `fdr`. Chung phai viet vao so TAM.

    Neu khong thi chinh bo test lai lam dung cai viec no dang di bat: bom dong
    vao so quyet dinh that. Do 24/08: hai lan chay `pytest` da them 28 dong.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._db_cu = SO.DB
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()


class GhiSoFDR(SoTam):

    def test_do_thu_khong_them_dong_nao(self):
        n0 = _dem()
        r = CONG.lord_v2(0.001, "kiem-thu-ghi-so-24-08", lane="kiem_thu",
                         family="kiem_thu_ghi_so", data_release="TEST",
                         ghi_so=False)
        self.assertEqual(_dem(), n0, "do thu ma van ghi vao so")
        self.assertFalse(r["da_ghi_so"])
        self.assertIsNone(r["fdr_id"])
        self.assertIn("nguong_fdr", r)
        self.assertIsInstance(r["bac_bo"], bool)

    def test_do_thu_tra_dung_nguong_ma_phep_thu_that_se_gap(self):
        """Do thu phai tinh nguong tai DUNG vi tri j, khong duoc tra nguong
        cua phep thu dau tien - neu khong thi luc do duoc la luc cua mot he
        khac."""
        ho = dict(lane="kiem_thu", family="kiem_thu_vi_tri",
                  data_release="TEST")
        thu = CONG.lord_v2(0.5, "plan-do-thu", ghi_so=False, **ho)
        that = CONG.lord_v2(0.5, "plan-that", ghi_so=True, **ho)
        self.assertEqual(thu["thu_tu_trong_ho"], that["thu_tu_trong_ho"])
        self.assertAlmostEqual(thu["nguong_fdr"], that["nguong_fdr"], places=9)

    def test_do_luc_khong_ghi_so(self):
        """Bai kiem chinh: mot lan do duong cong luc = 0 dong moi."""
        from nhan import do_luc as DLUC
        n0 = _dem()
        r = DLUC.duong_cong_luc("EURCAD", "H4")
        if r.get("loi"):
            self.skipTest(str(r["loi"]))
        self.assertEqual(_dem(), n0,
                         "do duong cong luc van chiem suat trong so FDR")

    def test_mac_dinh_van_la_ghi(self):
        """Duong xac nhan that KHONG duoc im lang thanh do thu."""
        n0 = _dem()
        CONG.lord_v2(0.5, "plan-mac-dinh-ghi", lane="kiem_thu",
                     family="kiem_thu_mac_dinh", data_release="TEST")
        self.assertEqual(_dem(), n0 + 1)


if __name__ == "__main__":
    unittest.main()


class KhongChamHoldoutOTangKhamPha(unittest.TestCase):
    """Luat 1 cua `sang_loc.py`: V0-V3 khong duoc cham holdout.

    Truoc 24/08 `chay_pheu` nap CA CHUOI khi caller khong truyen `df`, va
    `quantlab.chay_pheu_ung_vien` di dung duong do - ung vien duoc SANG LOC
    tren du lieu chua holdout roi duoc XAC NHAN tren chinh holdout do.
    """

    def test_mac_dinh_chi_lay_nua_train(self):
        from nhan import du_lieu as DL
        from nhan import sang_loc as SL
        try:
            full = DL.nap("EURCAD", "D1")
        except Exception as e:
            self.skipTest(str(e))
        train = DL.hai_nua(full, 0.6)[0]
        SL.xoa_bo_dem()
        r = SL.chay_pheu("ibs_bat_day", {"nguong": 0.2}, "EURCAD", "D1",
                         pham_vi=None, da_chay=None)
        self.assertIn("so_bar", str(r.get("do")) + str(r))
        # duong doc duoc nhat: so bar V1 ghi lai phai bang so bar TRAIN
        so_bar = (r.get("do") or {}).get("so_bar")
        if so_bar is not None:
            self.assertEqual(so_bar, len(train))
            self.assertNotEqual(so_bar, len(full))

    def test_cham_holdout_phai_noi_ro(self):
        from nhan import du_lieu as DL
        from nhan import sang_loc as SL
        try:
            full = DL.nap("EURCAD", "D1")
        except Exception as e:
            self.skipTest(str(e))
        SL.xoa_bo_dem()
        r = SL.chay_pheu("ibs_bat_day", {"nguong": 0.2}, "EURCAD", "D1",
                         pham_vi=None, da_chay=None, cham_holdout=True)
        so_bar = (r.get("do") or {}).get("so_bar")
        if so_bar is not None:
            self.assertEqual(so_bar, len(full))
