# -*- coding: utf-8 -*-
"""Test cho `nhan/doc_ma.py` - doc ma nguon thanh NHIEU khai bao co che.

Moc doi chieu van la SONIC R. Diem khac voi `test_thu_hoi_thanh_phan`: o do ta
hoi "co lay lai duoc cac manh khong", o day hoi "co ghep duoc thanh khai bao
CHAY DUOC khong".
"""
from __future__ import annotations

import unittest

from nhan import doc_ma as DM
from nhan import ngu_phap as NP

PINE = """//@version=3
strategy("Sonic R", overlay=true)
HiLoLen = input(34, minval=2)
EMA     = input(89, minval=2)
Look    = input(55, minval=2)
pacL = ema(low,HiLoLen)
pacH = ema(high,HiLoLen)
ma   = ema(close,EMA)
dcHi = highest(high, Look)
rsiv = rsi(close, 14)
longC  = pacH > ma
shortC = pacL < ma
brk    = close > dcHi[1]
qua    = rsiv < 30
he_so  = input(1.5)
sai    = close > he_so
"""

CHEO = """//@version=5
fast = ta.ema(close, 20)
slow = ta.ema(close, 50)
up = ta.crossover(fast, slow)
dn = ta.crossunder(fast, slow)
"""


class MotFileRaNhieuKieuDanh(unittest.TestCase):
    """Doi hoi trung tam cua chu du an: mot script = nhieu kieu danh."""

    def setUp(self):
        self.ds = DM.doc_ma(PINE, "pine", nguon="thu", tien_to="t")
        self.dk = [s["vao"][0] for s in self.ds]

    def test_ra_nhieu_hon_mot_khai_bao(self):
        self.assertGreaterEqual(len(self.ds), 3, "mot file phai ra nhieu kieu danh")

    def test_moi_khai_bao_deu_qua_kiem_cu_phap(self):
        for s in self.ds:
            self.assertEqual(NP.kiem_khai_bao(s), [], s["ten"])

    def test_khong_sinh_ho_khac(self):
        """Ho `khac` khong khai duoc pham vi -> khong duoc vao thu vien."""
        self.assertNotIn("khac", [s["ho"] for s in self.ds])

    def test_giu_do_tre_cua_pha_vo(self):
        """`close > dcHi[1]` phai giu do tre.

        Cat bo `[1]` bien dieu kien thanh `close > highest(high,55)`, ma
        `highest` gom ca nen hien tai nen dieu kien do KHONG BAO GIO dung - cong
        bao 'kich hoat 0,000%'. Cung ho loi voi quy tac `Open[i+1]`.
        """
        co_tre = [d for d in self.dk
                  if (d.get("phai") or {}).get("chi_bao") == "tre"]
        self.assertTrue(co_tre, "mat do tre cua dieu kien pha vo")
        self.assertEqual(co_tre[0]["phai"]["n"], 1)

    def test_bo_so_sanh_lech_thang_do(self):
        """`close > he_so` voi `he_so = input(1.5)` la rac, phai bi bo.

        Do that tren Sonic R: khong chan thi sinh ra `open < 2` va
        `ema34_high < 1.5`, ca hai kich hoat 100% so bar.
        """
        for d in self.dk:
            if "hang" in (d.get("phai") or {}):
                self.assertNotIn((d.get("trai") or {}).get("chi_bao"),
                                 DM._THANG_GIA, str(d))

    def test_giu_nguon_gia_cua_tung_duong(self):
        """Dai PAC la EMA34 tren high VA tren low - hai duong khac nhau."""
        cot = {(d.get("trai") or {}).get("cot") for d in self.dk}
        self.assertTrue({"high", "low"} & cot)

    def test_nguong_rsi_giu_duoc_vi_rsi_co_thang_do_bi_chan(self):
        rsi = [d for d in self.dk
               if (d.get("trai") or {}).get("chi_bao") == "rsi"]
        self.assertTrue(rsi)
        self.assertEqual(rsi[0]["phai"], {"hang": 30.0})


class Cheo(unittest.TestCase):
    def test_crossover_thanh_phep_cheo_len(self):
        ds = DM.doc_ma(CHEO, "pine", tien_to="c")
        phep = {s["vao"][0]["phep"] for s in ds}
        self.assertIn("cheo_len", phep)
        self.assertIn("cheo_xuong", phep)

    def test_hai_ve_deu_la_ema_dung_chu_ky(self):
        ds = DM.doc_ma(CHEO, "pine", tien_to="c")
        d = ds[0]["vao"][0]
        self.assertEqual(d["trai"], {"chi_bao": "ema", "n": 20, "cot": "close"})
        self.assertEqual(d["phai"], {"chi_bao": "ema", "n": 50, "cot": "close"})


class KhongNo(unittest.TestCase):
    def test_van_ban_rong(self):
        self.assertEqual(DM.doc_ma(""), [])

    def test_van_xuoi_thuan_khong_ra_gi(self):
        self.assertEqual(DM.doc_ma("Mua khi RSI thap va ban khi RSI cao."), [])

    def test_khong_chay_ma(self):
        """Bo doc chi doc van ban. Ma co hai khong gay tac dung phu nao."""
        doc = PINE + "\nimport os\nos.system('echo x')\n"
        self.assertTrue(DM.doc_ma(doc, "pine", tien_to="t"))

    def test_ten_khong_co_ky_tu_pha_LIKE(self):
        """Ten di vao `gia_thuyet.ma` roi bi tim lai bang LIKE."""
        for s in DM.doc_ma(PINE, "pine", tien_to="t"):
            self.assertNotIn("%", s["ten"])
            self.assertNotIn(".", s["ten"])



class MienQuetCuaTacGia(unittest.TestCase):
    """Lay mien quet tu `input(...)` cua chinh tac giả - khong chay ma cua ho."""

    def test_doc_duoc_input_pine_kem_minval(self):
        khai = DM.rut_input(PINE)
        self.assertEqual(khai["HiLoLen"]["gia_tri"], 34.0)
        self.assertEqual(khai["HiLoLen"]["min"], 2.0)

    def test_doc_duoc_input_mql(self):
        mql = "input int    InpPeriod   = 14;  // chu ky\ninput double InpRisk = 2.0;\n"
        khai = DM.rut_input(mql)
        self.assertEqual(khai["InpPeriod"]["gia_tri"], 14.0)
        self.assertEqual(khai["InpRisk"]["gia_tri"], 2.0)

    def test_luoi_neo_quanh_gia_tri_tac_gia_dung(self):
        self.assertEqual(DM._luoi_quanh(34, None), [17, 34, 68])

    def test_luoi_bi_chan_trong_mien_tac_gia_khai(self):
        self.assertEqual(DM._luoi_quanh(10, {"min": 8.0, "max": 12.0}), [8, 10, 12])

    def test_hai_ve_cung_chi_bao_khong_ghi_de_nhau(self):
        """`ema34 < ema89`: khoa theo ten chi bao thi mat mot nua dieu kien."""
        ds = DM.doc_ma(PINE, "pine", tien_to="t")
        hai = [s for s in ds if len(s["luoi_goc"]) == 2]
        self.assertTrue(hai, "dieu kien hai ve deu co chu ky phai giu ca hai")

    def test_moi_khai_bao_deu_co_luoi_goc(self):
        for s in DM.doc_ma(PINE, "pine", tien_to="t"):
            self.assertIn("luoi_goc", s)

if __name__ == "__main__":
    unittest.main()
