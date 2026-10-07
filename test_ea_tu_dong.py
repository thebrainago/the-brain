# -*- coding: utf-8 -*-
"""Test cho `ea_tu_dong.py`.

Khong test phan cham mang hay goi MetaEditor. Test dung nhung cho DA SAP THAT:
duong dan `Report=`, mac dinh `Model`, va viec doc input cua tac gia.
"""
from __future__ import annotations

import hashlib
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import ea_tu_dong as EA


class TenSach(unittest.TestCase):
    def test_bo_ky_tu_pha_duong_dan(self):
        self.assertEqual(EA.ten_sach("[MQL5 mt5/experts] Sonic R v2.1!"),
                         "MQL5_mt5_experts_Sonic_R_v2_1")

    def test_khong_bao_gio_rong(self):
        self.assertTrue(EA.ten_sach("!!!"))

    def test_co_tran_do_dai(self):
        self.assertLessEqual(len(EA.ten_sach("x" * 200)), 40)


class VietIni(unittest.TestCase):
    def setUp(self):
        self.p = EA.viet_ini("thu_test", "abc.ex5", "abc.set", "US500m", "H1",
                             "2022.01.01", "2026.06.30")
        self.t = self.p.read_text(encoding="utf-16")

    def tearDown(self):
        try:
            self.p.unlink()
        except OSError:
            pass

    def test_report_la_duong_TUONG_DOI(self):
        """`Report=` tuyet doi bi tester lo di, khong bao loi (bai hoc 27/07)."""
        dong = [l for l in self.t.splitlines() if l.startswith("Report=")][0]
        gia_tri = dong.split("=", 1)[1]
        self.assertFalse(Path(gia_tri).is_absolute(), dong)
        self.assertNotIn(":", gia_tri)

    def test_mac_dinh_la_Model_4_tick_that(self):
        """`Model=1` noi doi khi TP/SL nho hon ~2x bien do nen M1 (bay 01/08)."""
        self.assertIn("Model=4", self.t)

    def test_tat_toi_uu_hoa(self):
        """MT5 optimization chon tham so = curve-fitting (luat cua du an)."""
        self.assertIn("Optimization=0", self.t)

    def test_tu_thoat_de_chay_hang_loat_duoc(self):
        self.assertIn("ShutdownTerminal=1", self.t)

    def test_ghi_bang_utf16(self):
        """MT5 chi doc .ini utf-16; utf-8 thi terminal mo roi khong chay gi."""
        with self.assertRaises(UnicodeDecodeError):
            self.p.read_text(encoding="utf-8")


class DocInputCuaTacGia(unittest.TestCase):
    MA = ("input int    InpPeriod = 14;   // chu ky\n"
          "input double InpRisk   = 2.0;  // rui ro %\n"
          "input bool   InpDung   = true;\n")

    def test_chi_lay_input_co_gia_tri_SO(self):
        from nhan import doc_ma as DM
        khai = DM.rut_input(self.MA)
        self.assertEqual(set(khai), {"InpPeriod", "InpRisk"})
        self.assertEqual(khai["InpPeriod"]["gia_tri"], 14.0)


class Duong(unittest.TestCase):
    def test_moi_terminal_deu_khai_du_ba_duong(self):
        for ten in EA.TERMINAL:
            mql5, me, term = EA._duong(ten)
            self.assertTrue(str(mql5).endswith("MQL5"))
            self.assertTrue(str(me).endswith("metaeditor64.exe"))
            self.assertTrue(str(term).endswith("terminal64.exe"))



class VanDia(unittest.TestCase):
    """Chay tester khi dia thap la tu dap vao cong quyet dinh cua chinh minh."""

    def test_nguong_khop_voi_cong_cua_evolution(self):
        """`evolution` khoa mt5_tick_test khi dia < 15 GB - phai cung mot so."""
        from tru import evolution as EV
        import inspect
        src = inspect.getsource(EV.do_van_hanh)
        self.assertIn("15", src)
        self.assertEqual(EA.DIA_TOI_THIEU_GB, 15.0)

    def test_do_duoc_dia_trong(self):
        g = EA.dia_trong_gb()
        self.assertGreater(g, 0)
        self.assertLess(g, 100_000)

    def test_don_tick_khong_dong_vao_history(self):
        """Bo dem tick tai lai duoc; `history` (bar OHLC) thi khong duoc xoa."""
        import inspect
        src = inspect.getsource(EA.don_tick)
        self.assertIn('rglob("ticks")', src)
        self.assertNotIn('rglob("history")', src)

    def test_tu_choi_chay_khi_dia_thap(self):
        goc = EA.DIA_TOI_THIEU_GB
        try:
            EA.DIA_TOI_THIEU_GB = 10 ** 6      # ep dieu kien thieu dia
            r = EA.chay_mot({"terminal": "xm", "ea": "x.ex5", "nhan": "thu_dia",
                             "symbol": "EURUSDmicro", "khung": "H1",
                             "tu": "2025.01.01", "den": "2025.02.01"})
            self.assertFalse(r["xong"])
            self.assertIn("dia con", r.get("bo_qua", ""))
        finally:
            EA.DIA_TOI_THIEU_GB = goc


class _TerminalGia:
    """Terminal gia trong thu muc tam: khong dong vao thu muc MT5 that, cung khong ghi vao `reports/tester_ini/` (git)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.goc = Path(self._tmp.name)
        self.dat, self.cai = self.goc / "dat", self.goc / "cai"
        for p in (mock.patch.dict(EA.TERMINAL, {"thu": (self.dat, self.cai, "EURUSD")}),
                  mock.patch.object(EA, "REPORTS", self.goc / "reports")):
            p.start()
            self.addCleanup(p.stop)

    def tep_set(self, nhan):
        return self.dat / "MQL5" / "Profiles" / "Tester" / (nhan + ".set")


class VietSetTho(_TerminalGia, unittest.TestCase):
    """`viet_set_tho`: .set cua tac gia ghi NGUYEN VAN (bool / chuoi / enum), khong dich qua so nhu `viet_set`."""

    def test_utf16_co_bom_va_dung_van_ban(self):
        ten = EA.viet_set_tho("nhan1", "InpBuoc=true\nInpFast=8\nInpGhiChu=Alpha beta\n", "thu")
        self.assertEqual(ten, "nhan1.set")
        f = self.tep_set("nhan1")
        self.assertEqual(f.read_bytes()[:2], b"\xff\xfe", "MT5 chi doc .set UTF-16 co BOM")
        self.assertEqual(f.read_text(encoding="utf-16"), "InpBuoc=true\nInpFast=8\nInpGhiChu=Alpha beta\n")

    def test_dung_mot_dau_xuong_dong_cuoi(self):
        for van in ("A=1", "A=1\n", "A=1\n\n\n"):
            EA.viet_set_tho("nhan2", van, "thu")
            self.assertEqual(self.tep_set("nhan2").read_text(encoding="utf-16"), "A=1\n", repr(van))

    def test_ghi_de_chu_khong_noi_them(self):
        EA.viet_set_tho("nhan3", "A=1\nB=2\n", "thu")
        EA.viet_set_tho("nhan3", "C=3\n", "thu")
        self.assertEqual(self.tep_set("nhan3").read_text(encoding="utf-16"), "C=3\n")


class ChayMotDungBoSetCuaTacGia(_TerminalGia, unittest.TestCase):
    """`chay_mot` khong co MT5: Popen gia ghi san bao cao. Chi kiem AI viet .set nao va `.ini` tro vao dau."""

    def setUp(self):
        super().setUp()
        self.mo = []                                            # cac lan "mo terminal": [duong terminal, /config:...]
        self.gio = [1000.0]

        def popen(args):
            self.mo.append(list(args))
            nhan = Path(args[1][len("/config:"):]).stem
            bc = self.dat / "_bao_cao" / (nhan + ".htm")
            bc.parent.mkdir(parents=True, exist_ok=True)
            bc.write_bytes(b"x" * 3000)                         # > 2000 byte: chay_mot coi la bao cao xong
            return object()

        def dong_ho():
            self.gio[0] += 1.0
            return self.gio[0]
        gia = {"dia_trong_gb": lambda: 100.0, "dong_terminal": lambda t: 0, "_pid_cua_ten": lambda t: [1],
               "time": types.SimpleNamespace(time=dong_ho, sleep=lambda s: None),
               "subprocess": types.SimpleNamespace(Popen=popen, run=lambda *a, **k: None)}
        for ten, thay in gia.items():
            p = mock.patch.object(EA, ten, thay)
            p.start()
            self.addCleanup(p.stop)

    def viec(self, **kw):
        v = {"terminal": "thu", "nhan": "ea_tho_abc", "ea": "BotDen_abc123", "symbol": "XAUUSD", "khung": "M15",
             "tu": "2018.08.01", "den": "2021.10.01"}
        v.update(kw)
        return v

    def ini(self, nhan="ea_tho_abc"):
        return (self.goc / "reports" / "tester_ini" / (nhan + ".ini")).read_text(encoding="utf-16")

    def test_co_tep_set_tho_thi_ghi_nguyen_van_va_bo_qua_input(self):
        r = EA.chay_mot(self.viec(tep_set_tho="InpBuoc=true\nInpGhiChu=Alpha beta\n", input={"InpFast": {"gia_tri": 99}}))
        self.assertTrue(r["xong"])
        self.assertEqual(self.tep_set("ea_tho_abc").read_text(encoding="utf-16"), "InpBuoc=true\nInpGhiChu=Alpha beta\n")
        ini = self.ini()
        self.assertIn("ExpertParameters=ea_tho_abc.set", ini)
        self.assertIn("Expert=_tu_dong\\BotDen_abc123", ini)
        self.assertEqual(len(self.mo), 1)

    def test_khong_co_tep_set_tho_thi_di_duong_input_cu(self):
        r = EA.chay_mot(self.viec(input={"InpFast": {"gia_tri": 8}, "InpStep": {"gia_tri": 35.5}}))
        self.assertTrue(r["xong"])
        self.assertEqual(self.tep_set("ea_tho_abc").read_text(encoding="utf-16"), "InpFast=8\nInpStep=35.5\n")

    def test_khong_input_khong_set_tho_la_chay_mac_dinh_cua_ea(self):
        """EA nhi phan chay mac dinh: .set rong, MT5 dung gia tri bien dich san."""
        r = EA.chay_mot(self.viec(input={}))
        self.assertTrue(r["xong"])
        self.assertEqual(self.tep_set("ea_tho_abc").read_text(encoding="utf-16").strip(), "")

    def test_dia_thap_thi_khong_viet_set_khong_mo_terminal(self):
        with mock.patch.object(EA, "dia_trong_gb", lambda: 1.0), mock.patch.object(EA, "don_tick", lambda t: 0.0):
            r = EA.chay_mot(self.viec(tep_set_tho="A=1\n"))
        self.assertFalse(r["xong"])
        self.assertIn("dia con", r["bo_qua"])
        self.assertFalse(self.tep_set("ea_tho_abc").exists())
        self.assertEqual(self.mo, [])


class ChoPhepDll(_TerminalGia, unittest.TestCase):
    """EA nhi phan chi chay khi terminal tat 'Allow DLL imports' - nen cho doc sai phai nghieng ve TU CHOI."""

    def ghi(self, noi, ma_hoa="utf-16"):
        (self.dat / "config").mkdir(parents=True, exist_ok=True)
        p = self.dat / "config" / "common.ini"
        tho = noi.replace("\n", "\r\n")
        if ma_hoa == "utf-16":                                   # nhu MT5 ghi
            p.write_bytes(b"\xff\xfe" + tho.encode("utf-16-le"))
        elif ma_hoa == "utf-16-khong-bom":
            p.write_bytes(tho.encode("utf-16-le"))
        else:
            p.write_bytes(tho.encode(ma_hoa))

    def test_bat(self):
        self.ghi("[Common]\nLogin=0\n[Experts]\nAllowLiveTrading=1\nAllowDllImport=1\n")
        self.assertIs(EA.cho_phep_dll("thu"), True)

    def test_gia_tri_khac_khong_deu_la_bat(self):
        self.ghi("[Experts]\nAllowDllImport=2\n")
        self.assertIs(EA.cho_phep_dll("thu"), True)

    def test_tat(self):
        self.ghi("[Experts]\nAllowDllImport=0\n")
        self.assertIs(EA.cho_phep_dll("thu"), False)

    def test_chua_co_tep_la_tat_mac_dinh_cua_mt5(self):
        self.assertIs(EA.cho_phep_dll("thu"), False)

    def test_thieu_khoa_hoac_gia_tri_rong_la_tat(self):
        self.ghi("[Experts]\nEnabled=1\n")
        self.assertIs(EA.cho_phep_dll("thu"), False)
        self.ghi("[Experts]\nAllowDllImport=\n")
        self.assertIs(EA.cho_phep_dll("thu"), False)

    def test_khoa_nam_sai_muc_khong_tinh(self):
        self.ghi("AllowDllImport=1\n[Common]\nAllowDllImport=1\n[Experts]\nEnabled=1\n")
        self.assertIs(EA.cho_phep_dll("thu"), False)

    def test_khong_phan_biet_hoa_thuong_va_khoang_trang(self):
        self.ghi("[ experts ]\nallowdllimport = 1\n")
        self.assertIs(EA.cho_phep_dll("thu"), True)

    def test_doc_duoc_ca_utf8_va_utf16_khong_bom(self):
        for ma_hoa in ("utf-8", "utf-16-khong-bom"):
            self.ghi("[Experts]\nAllowDllImport=1\n", ma_hoa)
            self.assertIs(EA.cho_phep_dll("thu"), True, ma_hoa)

    def test_tep_co_nhung_khong_doc_duoc_la_none(self):
        (self.dat / "config" / "common.ini").mkdir(parents=True)        # thu muc o cho cua tep
        self.assertIsNone(EA.cho_phep_dll("thu"))


class ChepNhiPhan(_TerminalGia, unittest.TestCase):
    THO = bytes(range(256)) * 8

    def nguon(self, ten="Bot Den v3.0.5.ex5", tho=None):
        f = self.goc / ten
        f.write_bytes(self.THO if tho is None else tho)
        return f

    @staticmethod
    def sha(tho):
        return hashlib.sha1(tho).hexdigest()[:16]

    def test_copy_dung_tung_byte_vao_experts_tu_dong(self):
        f = self.nguon()
        ten_file, dich = EA.chep_nhi_phan(str(f), "Bot Den v3.0.5_abc123", "thu", self.sha(self.THO))
        self.assertEqual(ten_file, EA.ten_sach("Bot Den v3.0.5_abc123"))
        self.assertEqual(dich, self.dat / "MQL5" / "Experts" / "_tu_dong" / (ten_file + ".ex5"))
        self.assertEqual(dich.read_bytes(), self.THO)
        self.assertEqual(f.read_bytes(), self.THO, "khong sua file goc")

    def test_sha_khong_khop_thi_khong_ghi_gi(self):
        f = self.nguon()
        with self.assertRaises(ValueError) as e:
            EA.chep_nhi_phan(str(f), "x", "thu", "0" * 16)
        self.assertIn("DOI", str(e.exception))
        self.assertFalse((self.dat / "MQL5" / "Experts").exists())

    def test_tep_nguon_khong_con_la_loi_os(self):
        with self.assertRaises(OSError):
            EA.chep_nhi_phan(str(self.goc / "mat.ex5"), "x", "thu", "0" * 16)

    def test_ban_sau_ghi_de_ban_truoc_cung_ten(self):
        a, b = bytes(range(200)) * 3, bytes(reversed(range(200))) * 3
        EA.chep_nhi_phan(str(self.nguon("a.ex5", a)), "BotX", "thu", self.sha(a))
        _, dich = EA.chep_nhi_phan(str(self.nguon("b.ex5", b)), "BotX", "thu", self.sha(b))
        self.assertEqual(dich.read_bytes(), b)


if __name__ == "__main__":
    unittest.main()
