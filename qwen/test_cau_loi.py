# -*- coding: utf-8 -*-
"""Test cau_loi: don thoat 0 nhung dau ra bao loi KHONG duoc la DAT (08/10/2026)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from qwen import cau_git as CG                                    # noqa: E402
from qwen import cau_loi as CL                                    # noqa: E402


class DauVet(unittest.TestCase):
    def test_nhan_dung_tung_loai_loi(self):
        ca = {"ImportError: Unable to find a usable engine": "thieu_thu_vien",
              "TesterDangBan: het slot ranh (4 slot)": "tester_ban",
              "tester khong ra ket qua: dia con 3.5 GB < 15.0": "het_dia",
              "tester khong ra ket qua: tester khong ra bao cao": "tester_khong_ra",
              "tester khong ra ket qua: bien dich hong: ea.mq5(113,10) : error 106: file 'Include\\Trade\\Trade.mqh' not found": "bien_dich_hong",
              "loi khi chay: FileNotFoundError: khong co du lieu cho XTIUSD": "thieu_du_lieu",
              "ngoai doan kham_pha": "ngoai_doan",
              "!! DIEN_DAN_KHONG_TIEN: khong dien dan nao doc tiep duoc: BO_QUA 8": "dien_dan_khong_tien"}
        for dong, nhan in ca.items():
            self.assertEqual(CL.dau_vet(["binh thuong", dong])["nhan"], nhan, dong)

    def test_dien_dan_khong_tien_la_can_chan_doan_va_dong_canh_bao_mot_phan_thi_khong_bi_nghi(self):
        """08/10/2026: 6/8 don quet sau bao DAT trong khi dien dan o may nha dang tat (BO_QUA). `b dien-dan quet` nay thoat 5 va in dong nay;
        dong '!! 1 dien dan khong tien duoc' (co dien dan khac van doc duoc) KHONG phai dau vet loi cua ca don."""
        r = CL.dau_vet(["a  BO_QUA  0 trang luot nay", "!! DIEN_DAN_KHONG_TIEN: khong dien dan nao doc tiep duoc: BO_QUA 8"])
        self.assertEqual((r["nhan"], r["nhom"]), ("dien_dan_khong_tien", "can_chan_doan"))
        self.assertIn("BO_QUA 8", r["bang_chung"])
        self.assertIsNone(CL.dau_vet(["a  OK  3 trang luot nay", "!! 1 dien dan khong tien duoc: b(CHAN_CAM)"]))

    def test_nhan_log_tester_cu_the_thang_dong_chung_chung(self):
        """08/10/2026 (`nhan/chan_doan_tester.py`): ly do tester hong gio mang `[tester:<nhan>]` cung dong chung
        'tester khong ra bao cao' - nhan CU THE phai thang (neu khong thi 20 don van mang mot nhan 'tester_khong_ra' mu)."""
        ca = {"chua_dang_nhap": "12:00:01 Network authorization on XMGlobal-MT5 10 failed",
              "mat_ket_noi": "12:00:01 Network connection closed",
              "thieu_lich_su": "12:00:01 Core 1 AUDCAD: no history data",
              "khong_nap_ea": "12:00:01 Tester cannot load Experts\\_tu_dong\\x",
              "ea_tu_choi": "12:00:01 Core 1 OnInit returned non-zero",
              "het_bo_nho": "12:00:01 Core 1 not enough memory",
              "agent_chet": "12:00:01 Tester agent 127.0.0.1:3000 stopped"}
        for nhan, dong_log in ca.items():
            ly_do = ("tester khong ra bao cao sau 94s [tester:%s] %s | slot s1 Trade.mqh=co, M1 AUDCAD: 2019=THIEU | "
                     "log moi: terminal 6d, agent:a3000 6d") % (nhan, dong_log)
            r = CL.dau_vet(['{"loi": "tester khong ra ket qua: %s"}' % ly_do])
            self.assertEqual((r["nhan"], r["nhom"]), ("tester_" + nhan, "can_chan_doan"), nhan)
            self.assertLessEqual(len(r["bang_chung"]), 240)
        # nhan cu the nam trong 240 ky tu DAU cua bang chung (mot khi bi cat o do thi nguoi doc khong con thay)
        dai = "tester khong ra bao cao sau 94s [tester:mat_ket_noi] " + "x" * 600
        self.assertIn("[tester:mat_ket_noi]", CL.dau_vet([dai])["bang_chung"])

    def test_tester_hong_khong_nhan_van_la_tester_khong_ra(self):
        for dong in ("tester khong ra ket qua: tester khong ra bao cao sau 94s | slot s1 Trade.mqh=co",
                     "tester khong ra bao cao (chan doan loi: RuntimeError: boom)"):
            r = CL.dau_vet([dong])
            self.assertEqual((r["nhan"], r["nhom"]), ("tester_khong_ra", "can_chan_doan"), dong)

    def test_nhan_log_khong_bat_nham_chu_thuong(self):
        for dong in ("co the tester:mat ket noi", "tester:thieu_lich_su", "[tester] ok", "[tester:khong_biet] x"):
            self.assertIsNone(CL.dau_vet([dong]), dong)

    def test_ket_qua_binh_thuong_khong_bi_nghi(self):
        self.assertIsNone(CL.dau_vet(["xong 220000-AUDCAD-M5 co_lai_that 0.953", "TONG HOP", "co_lai 0.1"]))
        self.assertIsNone(CL.dau_vet([]))
        self.assertIsNone(CL.dau_vet(None))

    def test_chi_xet_phan_cuoi(self):
        dai = ["ImportError cu"] + ["dong %d" % i for i in range(CL.SO_DONG_XET + 5)]
        self.assertIsNone(CL.dau_vet(dai))


class ChamDon(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.goc = Path(self.tmp.name)
        CG.bao_dam_thu_muc(goc=self.goc)

    def tearDown(self):
        self.tmp.cleanup()

    def _chay(self, ma, ma_in):
        CG.ra_don(ma, "thu", lenh=["python3", "-c", "print(%r)" % ma_in], cong="chay_duoc", goc=self.goc)
        d = CG.don_dang_cho(goc=self.goc)[0]
        d["cong"] = {"kieu": "chay_duoc"}
        return CG.chay_don(d, goc=self.goc, kiem_trang=False)

    def test_thoat_0_nhung_in_loi_thi_KHONG_la_DAT(self):
        r = self._chay("hong", '{"loi": "loi khi chay: ImportError: pyarrow"}')
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC", r)
        self.assertEqual(r["bang_chung"]["loi_ha_tang"]["nhan"], "thieu_thu_vien")

    def test_thoat_0_va_dau_ra_sach_van_la_DAT(self):
        self.assertEqual(self._chay("tot", "xong co_lai_that 0.95")["trang_thai"], "DAT")

    def test_cong_dang_chuoi_khong_lam_runner_nem_loi(self):
        CG.ra_don("chuoi", "thu", lenh=["python3", "-c", "print(1)"], cong="chay_duoc", goc=self.goc)
        d = CG.don_dang_cho(goc=self.goc)[0]
        d["cong"] = "chay_duoc"
        self.assertEqual(CG.chay_don(d, goc=self.goc, kiem_trang=False)["trang_thai"], "DAT")


class DuaLai(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.goc = Path(self.tmp.name)
        for t in ("cho", "xong"):
            (self.goc / "viec" / t).mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _don(self, ma, dong, co_don=True):
        if co_don:
            (self.goc / "viec" / "cho" / (ma + ".json")).write_text(json.dumps({"ma": ma}), encoding="utf-8")
        (self.goc / "viec" / "xong" / (ma + ".json")).write_text(json.dumps(
            {"ma": ma, "trang_thai": "DAT", "bang_chung": {"lenh": ["py", "b.py", "x"], "dong_cuoi": [dong]}}), encoding="utf-8")

    def test_sua_duoc_thi_dua_lai_toi_da_2_lan(self):
        self._don("a", "ImportError: pyarrow")
        self.assertEqual(CL.dua_lai(self.goc)["dua_lai"], ["a"])
        self.assertFalse((self.goc / "viec" / "xong" / "a.json").exists())     # thanh DANG CHO
        self._don("a", "ImportError: pyarrow", co_don=False)
        self.assertEqual(CL.dua_lai(self.goc)["dua_lai"], ["a"])
        self._don("a", "ImportError: pyarrow", co_don=False)
        r = CL.dua_lai(self.goc)
        self.assertEqual((r["dua_lai"], r["het_lan"]), ([], ["a"]))

    def test_can_chan_doan_khong_tu_dua_lai(self):
        self._don("c", "tester khong ra ket qua: bien dich hong: error 106: file 'Include\\Trade\\Trade.mqh' not found")
        self._don("d", "tester khong ra ket qua: tester khong ra bao cao")
        r = CL.dua_lai(self.goc)
        self.assertEqual((r["dua_lai"], sorted(r["can_chan_doan"])), ([], ["c", "d"]))
        self.assertTrue((self.goc / "viec" / "xong" / "c.json").exists())

    def test_ket_qua_moi_da_ha_bac_van_duoc_quet_va_dua_lai(self):
        (self.goc / "viec" / "cho" / "e.json").write_text(json.dumps({"ma": "e"}), encoding="utf-8")
        (self.goc / "viec" / "xong" / "e.json").write_text(json.dumps(
            {"ma": "e", "trang_thai": "CHUA_DO_DUOC", "bang_chung": {"lenh": ["py", "b.py", "x"], "dong_cuoi": ["..."],
             "loi_ha_tang": {"nhan": "thieu_thu_vien", "nhom": "sua_duoc", "bang_chung": "ImportError: pyarrow"}}}), encoding="utf-8")
        self.assertEqual(CL.dua_lai(self.goc)["dua_lai"], ["e"])

    def test_don_ten_file_khac_ma_van_duoc_dua_lai(self):
        """Ket qua nam o viec/xong/<ma>.json; don goc co the ten file khac ma (`021-lo-cmt-audcad-0.json` co ma `lo-dsl_cmt-AUDCAD-21`).
        Truoc 08/10/2026 `dua_lai` tim `viec/cho/<ma>.json` nen xep nham don do vao `khong_chay_lai` va khong bao gio chay lai."""
        (self.goc / "viec" / "cho" / "021-lo-cmt-audcad-0.json").write_text(json.dumps({"ma": "lo-dsl_cmt-AUDCAD-21"}), encoding="utf-8")
        self._don("lo-dsl_cmt-AUDCAD-21", "ImportError: Unable to find a usable engine; tried using: 'pyarrow'", co_don=False)
        r = CL.dua_lai(self.goc)
        self.assertEqual((r["dua_lai"], r["khong_chay_lai"]), (["lo-dsl_cmt-AUDCAD-21"], []))
        self.assertFalse((self.goc / "viec" / "xong" / "lo-dsl_cmt-AUDCAD-21.json").exists())
        self.assertEqual(sorted(CL.don_theo_ma(self.goc)), ["lo-dsl_cmt-AUDCAD-21"])

    def test_thieu_du_lieu_khong_tu_dua_lai(self):
        self._don("b", "FileNotFoundError: khong co du lieu cho COFFEE")
        r = CL.dua_lai(self.goc)
        self.assertEqual((r["dua_lai"], r["khong_chay_lai"]), ([], ["b"]))
        self.assertTrue((self.goc / "viec" / "xong" / "b.json").exists())


if __name__ == "__main__":
    unittest.main()
