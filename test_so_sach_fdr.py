# -*- coding: utf-8 -*-
"""SO SACH FDR PHAI DOC DUOC. Ba cho gay, do ngay 01/09/2026.

Hai van de `vd_so_sach_khong_khop` va `vd_duong_du_phong` do tang chan doan mo
tu 16/08 deu la HAU QUA, khong phai nguyen nhan. Nguyen nhan that:

1. **`fdr.gt_ma` chua HAI khong gian khoa khac nhau.** Truoc 17/08 no la ma gia
   thuyet; tu khi `lord_v2` vao viec no la economic plan hash. Do duoc: **0 tren
   1.124 hang moi** co `gt_ma` ton tai trong bang `gia_thuyet`. Nghia la moi
   phep doi soat `JOIN ket_qua k ON k.gt_ma = f.gt_ma` chi con nhin thay 675
   hang cu cua 15-16/08 - va no khong bao loi, no tra ve mot con so nho hon.

2. **Bao cao in ba don vi canh nhau nhu mot.** 1.799 hang so cai = 23 kham pha
   song + 675 epoch da chet + 1.101 dung cu do. Tang chan doan doc "687 khong
   khop moc nao" va mo mot van de khong ton tai.

3. **Bat bien `khop_ba_tang` sai chieu.** Ban cu doi moi gia thuyet co ket qua
   phai co mot hang FDR, nen 96 gia thuyet FAIL o cong re (dung thiet ke) lam
   den bao do vinh vien. Huong nguy hiem that su la hai huong con lai: mot gia
   thuyet an HAI suat trong cung epoch, hoac mot hang FDR khong co ket qua nao.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nhan import cong as CONG
from nhan import so as SO


class PhanLoaiHo(unittest.TestCase):

    def test_ho_do_dac_duoc_nhan_ra(self):
        for family in CONG.HO_DO_DAC:
            epoch = CONG.tao_epoch_fdr("legacy", family, "X", 5)
            self.assertTrue(CONG.la_ho_do_dac(epoch), family)

    def test_ho_kham_pha_khong_bi_xep_nham(self):
        for family in ("xu_huong", "lich", "quay_ve_trung_binh", "pha_vo", "vi_mo"):
            epoch = CONG.tao_epoch_fdr("legacy", family, "X", 5)
            self.assertFalse(CONG.la_ho_do_dac(epoch), family)

    def test_ten_ho_chua_chuoi_con_khong_bi_xep_nham(self):
        """`xu_huong@do_luc_thap` la ho THAT, khong phai dung cu do. Nhan dien
        bang chuoi con se nuot no va giau mot ho that khoi moi bang tong."""
        epoch = CONG.tao_epoch_fdr("legacy", "xu_huong@do_luc_thap", "X", 5)
        self.assertFalse(CONG.la_ho_do_dac(epoch))

    def test_phan_epoch_ra_doc_nguoc_duoc_khoa(self):
        epoch = CONG.tao_epoch_fdr("kham_pha", "lich", "2026Q3", 5)
        p = CONG.phan_epoch_ra(epoch)
        self.assertEqual(p["lane"], "kham_pha")
        self.assertEqual(p["family"], "lich")
        self.assertEqual(p["data_release"], "2026Q3")
        self.assertEqual(p["decision_generation"], "5")

    def test_khoa_cu_khong_lam_vo_bo_phan_tich(self):
        self.assertEqual(CONG.phan_epoch_ra("lich@cp2"), {})
        self.assertFalse(CONG.la_ho_do_dac("lich@cp2"))


class SoTam(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._db_cu = SO.DB
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()


class CotGtMaNguon(SoTam):

    def test_so_cai_co_cot_gt_ma_nguon(self):
        cot = {r["name"] for r in SO.nhieu("PRAGMA table_info(fdr)")}
        self.assertIn("gt_ma_nguon", cot)

    def test_khoi_tao_them_cot_vao_bang_da_ton_tai(self):
        """`CREATE TABLE IF NOT EXISTS` khong dong bo cot cho bang cu. Neu
        `khoi_tao` khong tu them thi cot moi se khong bao gio xuat hien tren so
        dang chay, va lan ghi dau tien hong lang le."""
        with SO.ket_noi() as cn:
            cn.execute("DROP TABLE fdr")
            cn.execute("CREATE TABLE fdr(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                       "luc TEXT, ho TEXT, gt_ma TEXT, p REAL, nguong REAL, "
                       "bac_bo INTEGER, tai_nguyen REAL)")
        SO.khoi_tao()
        cot = {r["name"] for r in SO.nhieu("PRAGMA table_info(fdr)")}
        self.assertIn("gt_ma_nguon", cot)

    def test_lord_v2_ghi_ma_gia_thuyet_de_doi_soat_duoc(self):
        CONG.lord_v2(0.01, "plan-hash-abc", lane="legacy", family="lich",
                     data_release="X", decision_generation=5,
                     gt_ma_nguon="US500M.D1.ibs_bat_day.nguong0.2")
        r = SO.mot("SELECT gt_ma, gt_ma_nguon FROM fdr ORDER BY id DESC LIMIT 1")
        self.assertEqual(r["gt_ma"], "plan-hash-abc")
        self.assertEqual(r["gt_ma_nguon"], "US500M.D1.ibs_bat_day.nguong0.2")

    def test_doi_soat_qua_gt_ma_nguon_tim_thay_hang_moi(self):
        """Day la bai kiem cua chinh cai da gay: noi bang `f.gt_ma` tra ve 0."""
        ma = "US500M.D1.ibs_bat_day.nguong0.2"
        CONG.lord_v2(0.01, "plan-hash-abc", lane="legacy", family="lich",
                     data_release="X", decision_generation=5, gt_ma_nguon=ma)
        with SO.ket_noi() as cn:
            cn.execute("INSERT INTO ket_qua(gt_ma, verdict) VALUES(?, 'PASS')", (ma,))
        cu = SO.mot("SELECT COUNT(*) n FROM fdr f JOIN ket_qua k "
                    "ON k.gt_ma = f.gt_ma")["n"]
        moi = SO.mot("SELECT COUNT(*) n FROM fdr f JOIN ket_qua k "
                     "ON k.gt_ma = COALESCE(f.gt_ma_nguon, f.gt_ma)")["n"]
        self.assertEqual(cu, 0, "noi bang gt_ma phai tra ve rong - do la loi cu")
        self.assertEqual(moi, 1, "noi qua gt_ma_nguon phai tim thay")

    def test_hang_cu_khong_co_gt_ma_nguon_van_doi_soat_duoc(self):
        """675 hang cua 15-16/08 khong co cot do; COALESCE phai do chung."""
        ma = "AUDCHF.D1.cuoi_thang.truoc1_sau1"
        with SO.ket_noi() as cn:
            cn.execute("INSERT INTO fdr(luc,ho,gt_ma,p,nguong,bac_bo,tai_nguyen) "
                       "VALUES('2026-08-15','lich@cp2',?,0.02,0.05,0,0.1)", (ma,))
            cn.execute("INSERT INTO ket_qua(gt_ma, verdict) VALUES(?, 'FAIL')", (ma,))
        n = SO.mot("SELECT COUNT(*) n FROM fdr f JOIN ket_qua k "
                   "ON k.gt_ma = COALESCE(f.gt_ma_nguon, f.gt_ma)")["n"]
        self.assertEqual(n, 1)

    def test_lord_v2_khong_bat_buoc_gt_ma_nguon(self):
        """Do dac (null factory, thu luc) khong co gia thuyet nao dang sau."""
        ra = CONG.lord_v2(0.5, "plan-do-dac", lane="legacy", family="do_luc",
                          data_release="X", decision_generation=5)
        self.assertIn("nguong_fdr", ra)
        r = SO.mot("SELECT gt_ma_nguon FROM fdr ORDER BY id DESC LIMIT 1")
        self.assertIsNone(r["gt_ma_nguon"])


class BatBienBaTang(SoTam):
    """`khop_ba_tang` phai do dung huong lech nguy hiem."""

    def _do(self):
        from tru import evolution as EVO
        return EVO.do_suc_khoe_day_chuyen()

    def test_fail_truoc_fdr_KHONG_lam_lech_bat_bien(self):
        """96 gia thuyet FAIL o cong re la THIET KE ('cong re truoc placebo').
        Ban cu bao TACH moi ngay vi dieu nay va khong ai dong duoc."""
        with SO.ket_noi() as cn:
            for i in range(5):
                cn.execute("INSERT INTO gia_thuyet(ma,ho) VALUES(?,'lich')", (f"gt{i}",))
                cn.execute("INSERT INTO ket_qua(gt_ma,verdict) VALUES(?,'FAIL')", (f"gt{i}",))
        sk = self._do()
        self.assertEqual(sk["gt_fail_truoc_fdr"], 5)
        self.assertTrue(sk["khop_ba_tang"],
                        "FAIL truoc buoc FDR khong duoc tinh la lech so sach")

    def test_hang_fdr_mo_coi_MOI_lam_lech_bat_bien(self):
        """Da tieu mot suat cho phep thu ma khong ai doc ket qua."""
        CONG.lord_v2(0.01, "plan-x", lane="legacy", family="lich",
                     data_release="X", decision_generation=5,
                     gt_ma_nguon="gt-khong-co-ket-qua")
        sk = self._do()
        self.assertEqual(sk["fdr_mo_coi_moi"], 1)
        self.assertFalse(sk["khop_ba_tang"])

    def test_hang_mo_coi_CU_khong_lam_lech_bat_bien(self):
        """Hang ghi truoc khi co cot `gt_ma_nguon` khong doi soat duoc theo cau
        tao. Dem chung vao bat bien song = mot den bao do vinh vien."""
        with SO.ket_noi() as cn:
            cn.execute("INSERT INTO fdr(luc,ho,gt_ma,p,nguong,bac_bo,tai_nguyen) "
                       "VALUES('2026-08-15','lich@cp2','gt-cu',0.02,0.05,0,0.1)")
        sk = self._do()
        self.assertEqual(sk["fdr_mo_coi_moi"], 0)
        self.assertEqual(sk["fdr_mo_coi_cu_khong_doi_soat_duoc"], 1)
        self.assertTrue(sk["khop_ba_tang"])

    def test_ba_don_vi_cong_lai_dung_bang_tong(self):
        """Neu chung khong cong lai dung thi co mot tang dang dem tren tap khac,
        va do CHINH LA dieu tang chan doan bao hom 16/08."""
        with SO.ket_noi() as cn:
            cn.execute("INSERT INTO fdr(luc,ho,gt_ma,p,nguong,bac_bo,tai_nguyen) "
                       "VALUES('2026-08-15','lich@cp2','a',0.02,0.05,0,0.1)")
        CONG.lord_v2(0.5, "p1", lane="legacy", family="do_luc",
                     data_release="X", decision_generation=5)
        CONG.lord_v2(0.01, "p2", lane="legacy", family="lich",
                     data_release="X", decision_generation=5, gt_ma_nguon="gt2")
        sk = self._do()
        self.assertEqual(sk["fdr_tho_epoch_chet"], 1)
        self.assertEqual(sk["fdr_tho_do_dac"], 1)
        self.assertEqual(sk["fdr_tho_kham_pha"], 1)
        self.assertEqual(sk["fdr_tong_tho"], 3)
        self.assertEqual(
            sk["fdr_tong_tho"],
            SO.mot("SELECT COUNT(*) n FROM fdr")["n"],
            "tong ba don vi phai bang so hang that trong so cai")


if __name__ == "__main__":
    unittest.main(verbosity=2)
