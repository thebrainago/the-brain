# -*- coding: utf-8 -*-
"""MOT PASS O LAN NHIN THU 10 KHONG PHAI MOT PASS.

Phat hien 01/09/2026 khi go ro cach ly `quant_pass_quarantine_v2`.

FDR dem suat theo HO, va ho duoc phep tach khi doi CAU TRUC mo hinh chi phi -
dung theo THIET_KE muc 7, vi hai the he chi phi la hai thuoc do khac nhau.
Nhung khi ho tach thi `j` ve 1 va nguong LORD nhay tu 5,0e-6 len 0,0129 -
**noi gap 2.600 lan** - trong khi HOLDOUT van la holdout cu: no khong duoc lam
moi theo mo hinh chi phi.

Do tren so cai: 375 gia thuyet / 1.272 lan cham = **3,39 lan moi gia thuyet**,
mot gia thuyet cham 10 lan, va 3 gia thuyet di tu FAIL sang PASS qua cac lan
cham lai - ca ba deu nam trong ro cach ly.
`AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55`:

    FAIL FAIL FAIL FAIL FAIL PASS PASS PASS INVALIDATED PASS
      \\____ nguong tut 1,3e-4 -> 5,0e-6 ____/    \\_ ho doi cp2->cp3, j ve 1 _/

Tung buoc mot deu hop le. Cai thieu la khong ai dem TONG so lan nhin, nen mot
PASS o lan nhin thu 10 trong y het mot PASS o lan nhin dau tren moi bao cao.

Bo test nay hieu chuan HAI CHIEU - mot cong ha het moi thu xuong UNG_VIEN cho
so lieu y het mot cong tot:
  * lan nhin DAU van PASS duoc (cong khong bi niem kin),
  * lan nhin LAI bi ha xuong UNG_VIEN,
  * khai `du_lieu_moi=True` thi mo lai duoc.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd

from nhan import cong as CONG
from nhan import so as SO


class SoTam(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._db_cu = SO.DB
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()


class DemPhoiNhiem(SoTam):

    def test_gia_thuyet_moi_thi_bang_khong(self):
        self.assertEqual(SO.phoi_nhiem_holdout("chua-tung-co"), 0)

    def test_dem_ca_dong_da_bi_superseded(self):
        """Dem dong SONG thi mot gia thuyet cham 10 lan van ra 1 - va do dung
        la cach cu nhin so cai, nen khong ai thay 3,39 lan/gia thuyet."""
        ma = "X.D1.abc"
        SO.ghi_ket_qua(ma, {}, {}, "FAIL", 0.5, 0.0, 0.0)
        SO.ghi_ket_qua(ma, {}, {}, "FAIL", 0.4, 0.0, 0.0, cham_lai="mo hinh chi phi moi")
        SO.ghi_ket_qua(ma, {}, {}, "PASS", 0.01, 0.0, 0.0, cham_lai="mo hinh chi phi moi")
        self.assertEqual(SO.phoi_nhiem_holdout(ma), 3)
        song = SO.mot("SELECT COUNT(*) n FROM ket_qua WHERE gt_ma=? "
                      "AND superseded_by IS NULL", ma)["n"]
        self.assertEqual(song, 1, "chi mot dong song - day la cho de nhin sot")

    def test_moi_dong_ket_qua_deu_mang_theo_lan_nhin(self):
        """Con so chi doc duoc khi no LUON co mat, khong chi tren dong PASS."""
        ma = "Y.D1.abc"
        SO.ghi_ket_qua(ma, {}, {}, "FAIL", 0.5, 0.0, 0.0)
        SO.ghi_ket_qua(ma, {}, {}, "FAIL", 0.4, 0.0, 0.0, cham_lai="du lieu moi")
        import json
        sk = SO.nhieu("SELECT noi_dung FROM su_kien WHERE loai='ket_qua' ORDER BY id")
        lan = [json.loads(r["noi_dung"]).get("lan_nhin_holdout") for r in sk]
        self.assertEqual(lan, [1, 2])


def _canh_pass():
    """Bo doi so lam `xet` di het cong. Lay tu test_cong_fdr_v2."""
    idx = pd.date_range("2026-01-01", periods=100, freq="h")
    # loi DUONG nho chu khong phai 0 (sua 25/09/2026, nhu test_cong_fdr_v2): tu TANG 2
    # KINH TE (18/09) mot "he" loi 0 co rr thuc te = 0 -> truot dieu kien 12 -> fixture
    # "di het cong" khong con di het cong.
    kq_he = SimpleNamespace(so_lenh=100, loi=np.full(100, 1e-4), index=idx,
                            vi_the=np.ones(100))
    so_sanh = {
        "he": {"tong_lai_pct": 10.0, "sharpe": 1.0, "calmar": 1.0,
               "phoi_nhiem": 0.5, "so_bar": 100},
        "mua_giu_net": {"tong_lai_pct": 1.0, "sharpe": 0.1, "calmar": 0.1},
        "alpha_vs_mua_giu": {"t_alpha": 3.0, "alpha_nam_pct": 5.0},
    }
    return (kq_he, SimpleNamespace(),
            SimpleNamespace(do_tin="DO", canh_bao=None), so_sanh,
            {"p_xau_nhat": 0.04, "null_hop_le": True, "bootstrap_hop_le": True})


class ChanPassOLanNhinLai(SoTam):

    def _xet(self, gt_ma: str, plan: str, **kw):
        kq_he, kq_bh, cp, so_sanh, pl = _canh_pass()
        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh), \
                mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]), \
                mock.patch.object(CONG, "placebo", return_value=pl):
            return CONG.xet(None, kq_he, kq_bh, cp, gt_ma=gt_ma,
                            da_dang_ky=True, tren_holdout=True,
                            economic_plan_hash=plan, lane="legacy",
                            family="lich", data_release="X",
                            decision_generation=5, **kw)

    def test_lan_nhin_dau_van_PASS_duoc(self):
        """Hieu chuan chieu nguoc: mot cong ha TAT CA xuong UNG_VIEN cho so
        lieu y het mot cong tot. Neu bai nay do thi chan moi la hong."""
        ra = self._xet("Z.D1.moi_tinh", "plan-1")
        self.assertEqual(ra["verdict"], "PASS")
        self.assertEqual(ra["lan_nhin_holdout_truoc_do"], 0)

    def test_lan_nhin_LAI_bi_ha_xuong_UNG_VIEN(self):
        ma = "Z.D1.da_nhin_roi"
        SO.ghi_ket_qua(ma, {}, {}, "FAIL", 0.5, 0.0, 0.0)
        ra = self._xet(ma, "plan-2")
        self.assertEqual(ra["verdict"], "UNG_VIEN")
        self.assertEqual(ra["lan_nhin_holdout_truoc_do"], 1)
        self.assertTrue(any("nhin holdout" in x for x in ra["ly_do"]),
                        "phai noi RO vi sao bi ha, khong duoc lang le")

    def test_ha_xuong_UNG_VIEN_chu_KHONG_phai_FAIL(self):
        """Gia thuyet co the that - no chi CHUA duoc xac nhan. Danh FAIL la
        vut mat mot gia thuyet vi ly do so sach."""
        ma = "Z.D1.co_the_that"
        SO.ghi_ket_qua(ma, {}, {}, "FAIL", 0.5, 0.0, 0.0)
        ra = self._xet(ma, "plan-3")
        self.assertNotEqual(ra["verdict"], "FAIL")
        self.assertTrue(all(ra["dieu_kien"].values()),
                        "khong dieu kien nao duoc gia vo la truot")

    def test_khai_du_lieu_moi_thi_mo_lai_duoc(self):
        """Holdout dai ra that la ly do chinh dang - nhung phai KHAI."""
        ma = "Z.D1.holdout_dai_ra"
        SO.ghi_ket_qua(ma, {}, {}, "FAIL", 0.5, 0.0, 0.0)
        ra = self._xet(ma, "plan-4", du_lieu_moi=True)
        self.assertEqual(ra["verdict"], "PASS")

    def test_ho_FDR_tach_KHONG_xoa_duoc_lich_su_nhin(self):
        """Day la chinh cai da xay ra: doi cp2 -> cp3 lam `j` ve 1 va nguong
        noi 2.600 lan, nhung holdout thi khong moi lai."""
        ma = "Z.D1.doi_the_he_chi_phi"
        SO.ghi_ket_qua(ma, {}, {}, "FAIL", 0.5, 0.0, 0.0)
        kq_he, kq_bh, cp, so_sanh, pl = _canh_pass()
        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh), \
                mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]), \
                mock.patch.object(CONG, "placebo", return_value=pl):
            ra = CONG.xet(None, kq_he, kq_bh, cp, gt_ma=ma, da_dang_ky=True,
                          tren_holdout=True, economic_plan_hash="plan-cp3",
                          lane="legacy", family="quay_ve_trung_binh@cp3",
                          data_release="X", decision_generation=5)
        self.assertEqual(ra["fdr"]["thu_tu_trong_ho"], 1, "ho moi thi j phai ve 1")
        self.assertEqual(ra["verdict"], "UNG_VIEN",
                         "ho moi khong lam holdout moi lai")

    def test_do_dac_khong_bi_chan_nham(self):
        """Null factory / thu luc dung `gt_ma` sinh moi moi lan nen phoi nhiem
        luon la 0. Neu chan nay dinh vao chung thi bai kiem LUC se bao 'cong
        khong co luc' trong khi cong khong he hong."""
        for i in range(3):
            ra = self._xet(f"NULL.US500M.D1.{i}", f"plan-null-{i}")
            self.assertEqual(ra["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
