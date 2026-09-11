# -*- coding: utf-8 -*-
"""Kiem `nhan/anh_chup.py` - ghim ban du lieu de ket qua tai lap duoc.

Hai tinh chat phai giu, va chung NGUOC NHAU nen de lam hong nhau:
  - `kho()` KHONG duoc nem loi vi mot file bi sua (chay thi khong gay)
  - `kiem()` PHAI bao khi ban da ghim doi noi dung (ket luan thi phai sach)
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import anh_chup as AC  # noqa: E402
from nhan import so as SO  # noqa: E402


class HashPhaiDOI_KHI_NOI_DUNG_DOI(unittest.TestCase):
    def test_bam_lai_khi_file_doi(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "thu.bin"
            p.write_bytes(b"x" * 5000)
            h1 = AC.hash_file(p)
            p.write_bytes(b"y" * 5000)          # cung KICH THUOC, khac noi dung
            h2 = AC.hash_file(p)
            self.assertNotEqual(
                h1, h2,
                "bo dem dang khoa theo kich thuoc - mot file bi sua ma giu nguyen "
                "so byte se di lot")


class KiemPhaiBAO_KHI_BAN_GHIM_DOI(unittest.TestCase):
    MA = "THU_ANH_CHUP"

    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.p = Path(self.d.name) / "ban.parquet"
        self.p.write_bytes(b"a" * 3000)
        with SO.ket_noi() as cn:
            cn.executescript(AC._SCHEMA)
            cn.execute(
                "INSERT INTO anh_chup(ma,file,hash,so_byte,so_dong,khung_goc,"
                "tu,den,ghim_luc,ghi_chu) VALUES(?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(ma) DO UPDATE SET file=excluded.file,hash=excluded.hash",
                (self.MA, str(self.p), AC.hash_file(self.p), 3000, 10, "D1",
                 "", "", SO.bay_gio(), "ca kiem"))

    def tearDown(self):
        with SO.ket_noi() as cn:
            cn.execute("DELETE FROM anh_chup WHERE ma = ?", (self.MA,))
        self.d.cleanup()

    def test_nguyen_thi_lanh(self):
        lanh, mo_ta = AC.kiem(self.MA)
        self.assertTrue(lanh, mo_ta)

    def test_DOI_NOI_DUNG_thi_bao(self):
        self.p.write_bytes(b"b" * 3000)
        lanh, mo_ta = AC.kiem(self.MA)
        self.assertFalse(lanh)
        self.assertIn("DOI NOI DUNG", mo_ta)
        self.assertIn("KHONG tai lap duoc", mo_ta)

    def test_BIEN_MAT_thi_bao(self):
        self.p.unlink()
        lanh, mo_ta = AC.kiem(self.MA)
        self.assertFalse(lanh)
        self.assertIn("BIEN MAT", mo_ta)

    def test_kiem_tat_ca_dem_duoc(self):
        self.p.write_bytes(b"c" * 3000)
        kq = AC.kiem_tat_ca()
        self.assertGreaterEqual(kq["so_hong"], 1)
        self.assertTrue(any(h["ma"] == self.MA for h in kq["hong"]))

    def test_van_tay_DOI_khi_tap_ghim_doi(self):
        v1 = AC.van_tay_ghim()
        with SO.ket_noi() as cn:
            cn.execute("UPDATE anh_chup SET hash='khac' WHERE ma=?", (self.MA,))
        self.assertNotEqual(v1, AC.van_tay_ghim())


class ChuaGhimThiKHONG_duoc_trach(unittest.TestCase):
    def test_ma_chua_ghim_coi_la_lanh(self):
        lanh, mo_ta = AC.kiem("MA_CHUA_BAO_GIO_GHIM_XYZ")
        self.assertTrue(lanh)
        self.assertEqual(mo_ta, "chua ghim")


class KhoKHONG_DUOC_GAY_VI_ANH_CHUP(unittest.TestCase):
    """Nem loi trong `kho()` se lam sap moi duong chay chi vi mot file phu bi
    sua. Viec keu len la cua `kiem()`, va no chan o cho cham holdout."""

    def test_kho_van_chay_khi_ban_ghim_bien_mat(self):
        from nhan import du_lieu as DL
        ma = "THU_KHO_KHONG_GAY"
        with SO.ket_noi() as cn:
            cn.executescript(AC._SCHEMA)
            cn.execute(
                "INSERT INTO anh_chup(ma,file,hash,ghim_luc) VALUES(?,?,?,?) "
                "ON CONFLICT(ma) DO UPDATE SET file=excluded.file",
                (ma, r"C:\khong\ton\tai\abc.parquet", "deadbeef", SO.bay_gio()))
        try:
            k = DL.kho(lam_moi=True)
            self.assertGreater(len(k), 0)
        finally:
            with SO.ket_noi() as cn:
                cn.execute("DELETE FROM anh_chup WHERE ma = ?", (ma,))

    def test_kho_chon_dung_ban_da_ghim(self):
        from nhan import du_lieu as DL
        k = DL.kho(lam_moi=True)
        for ma, g in AC.ghim_theo_ma().items():
            if ma in k and any(str(b["file"]) == g["file"]
                               for b in k[ma].get("cac_ban", [])):
                with self.subTest(ma=ma):
                    self.assertEqual(str(k[ma]["file"]), g["file"])




class DANG_KY_PHAI_GHI_VAN_TAY_TAP_DU_LIEU(unittest.TestCase):
    """`plan_hash` dong bang KE HOACH nhung khong dong bang DU LIEU.

    Van tay tap ghim duoc ghi vao cot rieng, KHONG vao hash - cung ly do ma
    `so_phep_thu` va `the_he_cong` chi duoc ghi ra cot: dua vao hash se doi
    danh tinh cua moi gia thuyet da dang ky va lam ket luan cu khong doi chieu
    duoc.
    """
    MA = "THU.GHI_ANH_CHUP.D1.x"

    def tearDown(self):
        with SO.ket_noi() as cn:
            cn.execute("DELETE FROM gia_thuyet WHERE ma = ?", (self.MA,))

    def test_co_cot_anh_chup_hash_va_duoc_dien(self):
        SO.khoi_tao()
        SO.dang_ky_gia_thuyet(
            ma=self.MA, co_che="ca kiem ghi van tay tap du lieu", template="thu",
            tham_so={"n": 1}, tai_san="US500CASH", khung="D1",
            cua_so="2016-2021", ho="xu_huong")
        r = SO.mot("SELECT plan_hash, anh_chup_hash FROM gia_thuyet WHERE ma=?",
                   self.MA)
        self.assertTrue(r["anh_chup_hash"],
                        "dang ky ma khong ghi van tay tap du lieu")
        self.assertEqual(r["anh_chup_hash"], AC.van_tay_ghim())

    def test_van_tay_tap_du_lieu_KHONG_nam_trong_plan_hash(self):
        """Neu no nam trong hash thi ghim them mot ma se doi danh tinh cua MOI
        gia thuyet - va 361 ket luan cu thanh khong doi chieu duoc."""
        SO.khoi_tao()
        _, ph1 = SO.dang_ky_gia_thuyet(
            ma=self.MA, co_che="ca kiem ghi van tay tap du lieu", template="thu",
            tham_so={"n": 1}, tai_san="US500CASH", khung="D1",
            cua_so="2016-2021", ho="xu_huong")
        import hashlib, json as _j
        ke_hoach = _j.dumps(
            {"co_che": "ca kiem ghi van tay tap du lieu", "template": "thu",
             "tham_so": {"n": 1}, "tai_san": "US500CASH", "khung": "D1",
             "cua_so": "2016-2021"}, sort_keys=True, ensure_ascii=False)
        self.assertEqual(
            ph1, hashlib.sha256(ke_hoach.encode("utf-8")).hexdigest()[:16],
            "plan_hash da doi cong thuc - danh tinh gia thuyet cu bi pha")


if __name__ == "__main__":
    unittest.main()
