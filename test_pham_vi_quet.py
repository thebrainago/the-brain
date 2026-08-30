# -*- coding: utf-8 -*-
"""SO PHEP THU: plan_hash khong phu no, nen phai luu o cho khac.

LO HONG DO DUOC 30/08/2026. `so.dang_ky_gia_thuyet` bam plan_hash tu: co che +
template + tham so + tai san + khung + cua so. **Khong co so phep thu.**

Hau qua cu the: quet mot luoi 3 bo roi dang ky bo thang, va quet mot luoi 20 bo
roi dang ky bo thang, cho ra plan_hash Y HET NHAU. Muoi bay phep thu kia bien
mat khoi so - va do dung la lo hong qua khop ma ca cai cong sinh ra de chan.

Bang chung ngay trong so: `momentum_ema / AUDNZD / D1` co 4 gia thuyet, tuc
luoi duoc quet 4 bo roi moi bo dang ky rieng. Neu ai do noi luoi len 20 va chi
dang ky bo thang thi khong ai biet.

`nhan/quant_plan.py` (368 dong) dac ta day du ca so phep thu lan luat quyet
dinh, nhung `tru/quantlab.py` **import no ma khong goi mot ham nao**.

BUOC NAY CHI GHI LAI, KHONG DUA VAO HASH. Dua vao hash se doi danh tinh cua
361 gia thuyet da dang ky va lam moi ket luan truoc do khong doi chieu duoc.
Ghi lai truoc thi lo hong nhin thay duoc va dem duoc; dong han no la mot lan
chay lai toan bo, can chu du an ngoi may.

Bo test nay khoa dung ba tinh chat cua buoc do.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import so as SO   # noqa: E402


def _dk(**doi):
    goc = dict(ma="GT.1", co_che="c", template="ibs_bat_day",
               tham_so={"nguong": 0.2}, tai_san="SP500", khung="D1",
               cua_so="2015/2021", ho="quay_ve_trung_binh")
    goc.update(doi)
    return SO.dang_ky_gia_thuyet(**goc)


class SoTam(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._cu = SO.DB
        SO.DB = Path(self._tmp.name) / "t.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._cu
        self._tmp.cleanup()


class GhiLaiSoPhepThu(SoTam):

    def test_ghi_duoc_so_phep_thu_va_the_he_cong(self):
        _dk(so_phep_thu=20, the_he_cong=4)
        r = SO.mot("SELECT so_phep_thu, the_he_cong FROM gia_thuyet WHERE ma=?", "GT.1")
        self.assertEqual(r["so_phep_thu"], 20)
        self.assertEqual(r["the_he_cong"], 4)

    def test_KHONG_BAO_GIO_GIAM(self):
        """Luoi noi rong thi giu so LON. Mot lan goi thieu doi so khong duoc
        xoa mat con so that."""
        _dk(so_phep_thu=20, the_he_cong=4)
        _dk(so_phep_thu=3, the_he_cong=4)
        self.assertEqual(
            SO.mot("SELECT so_phep_thu FROM gia_thuyet WHERE ma=?", "GT.1")["so_phep_thu"],
            20, "so phep thu bi giam - mot lan goi sau che mat pham vi quet that")

    def test_goi_lai_voi_so_LON_hon_thi_cap_nhat(self):
        _dk(so_phep_thu=3, the_he_cong=4)
        _dk(so_phep_thu=25, the_he_cong=4)
        self.assertEqual(
            SO.mot("SELECT so_phep_thu FROM gia_thuyet WHERE ma=?", "GT.1")["so_phep_thu"],
            25)


class KHONG_DUOC_DOI_PLAN_HASH(SoTam):
    """Chot quan trong nhat: 361 gia thuyet da dang ky phai giu nguyen danh tinh."""

    def test_them_so_phep_thu_khong_lam_doi_plan_hash(self):
        _, h_khong = _dk(ma="A")
        _, h_co = _dk(ma="B", so_phep_thu=20, the_he_cong=4)
        self.assertEqual(
            h_khong, h_co,
            "them so_phep_thu lam doi plan_hash -> 361 gia thuyet cu doi danh "
            "tinh va moi ket luan truoc do khong doi chieu duoc")

    def test_dang_ky_lai_cung_ke_hoach_van_idempotent(self):
        i1, h1 = _dk(so_phep_thu=5, the_he_cong=4)
        i2, h2 = _dk(so_phep_thu=5, the_he_cong=4)
        self.assertEqual((i1, h1), (i2, h2))

    def test_doi_THAM_SO_van_bi_chan_nhu_cu(self):
        """Bat bien cu phai con nguyen: doi ke hoach thi phai NEM ra."""
        _dk(so_phep_thu=5)
        with self.assertRaises(ValueError):
            _dk(tham_so={"nguong": 0.9}, so_phep_thu=5)


class KhongTruyenGiThiKhongVo(SoTam):

    def test_bo_qua_hai_doi_so_thi_van_dang_ky_binh_thuong(self):
        i, h = _dk()
        self.assertIsNotNone(i)
        r = SO.mot("SELECT so_phep_thu FROM gia_thuyet WHERE ma=?", "GT.1")
        self.assertIsNone(r["so_phep_thu"],
                          "khong truyen ma van dien so - dang doan bua")


if __name__ == "__main__":
    unittest.main()
