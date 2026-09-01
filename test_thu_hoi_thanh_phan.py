# -*- coding: utf-8 -*-
"""Test cho `nhan/thu_hoi_thanh_phan.py`.

Moc doi chieu la SONIC R - vi du chu du an dua ra va la vi du DA LAM TAY trong
`SONIC_R_PHAN_TICH.md`. Neu bo rut tu dong khong lay lai duoc dung nhung manh ma
ban phan tich tay da lay, thi no chua lam duoc viec cua no.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from nhan import so as SO
from nhan import thu_hoi_thanh_phan as TH

# Rut gon tu `pineturtle.txt` that: giu dung cac dang goi co that trong do
# (`ema(high,HiLoLen)` chu khong phai `ema(high,34)`), vi chinh cho do lam ban
# dau tien cua bo rut tra ve rong.
SONIC = """//@version=3
strategy("Sonic R + Linear Reg + Kumo", overlay=true)
HiLoLen     = input(34, minval=2,title="High Low channel Length")
EMA         = input(89, minval=2,title="EMA Signal")
PeriodLookBack = input(55, minval=2)
pacL = ema(low,HiLoLen)
pacH = ema(high,HiLoLen)
pacC = ema(close,HiLoLen)
ma   = ema(close,EMA)
lr   = linreg(close, EMA, 0)
dcHi = highest(PeriodLookBack)
dcLo = lowest(PeriodLookBack)
fastLength = input(12)
slowlength = input(26)
MACDLength = input(9)
MACD = ema(close, fastLength) - ema(close, slowlength)
aMACD = ema(MACD, MACDLength)
"""

MQL = """
#property copyright "x"
int OnInit(){
  h1 = iMA(_Symbol,_Period,200,0,MODE_EMA,PRICE_CLOSE);
  h2 = iRSI(_Symbol,_Period,14,PRICE_CLOSE);
  h3 = iATR(_Symbol,_Period,14);
  return(0);
}
void OnTick(){}
"""


class RutPine(unittest.TestCase):
    def setUp(self):
        self.ds = TH.rut(SONIC, "pine")
        self.tim = lambda cb, ts, cot: [
            t for t in self.ds if t["chi_bao"] == cb
            and t["tham_so"] == ts and t["cot"] == cot]

    def test_dai_pac_ema34_tren_ca_ba_nguon_gia(self):
        """Dai PAC = EMA34 cua high / low / close - ba duong, khong phai mot."""
        for cot in ("high", "low", "close"):
            self.assertTrue(self.tim("ema", [34.0], cot),
                            f"khong lay duoc EMA34 tren {cot}")

    def test_ema89_va_linreg89(self):
        self.assertTrue(self.tim("ema", [89.0], "close"))
        self.assertTrue(self.tim("linreg", [89.0, 0.0], "close"))

    def test_donchian_55(self):
        self.assertTrue(self.tim("cao_nhat", [55.0], None))
        self.assertTrue(self.tim("thap_nhat", [55.0], None))

    def test_macd_12_26_9(self):
        for n in (12.0, 26.0, 9.0):
            self.assertTrue([t for t in self.ds
                             if t["chi_bao"] == "ema" and t["tham_so"] == [n]],
                            f"khong lay duoc thanh phan MACD ema({n:g})")

    def test_giai_bien_chu_khong_chi_lay_so_tho(self):
        """Ma that viet `ema(high,HiLoLen)`. Khong giai bien thi mat het tham so."""
        co_tham_so = [t for t in self.ds if t["tham_so"]]
        self.assertGreaterEqual(len(co_tham_so), 6)

    def test_bien_cung_ten_khac_gia_tri_theo_vi_tri(self):
        """Mot file ghep nhieu script: cung ten mang gia tri khac nhau."""
        vb = SONIC + "\nPeriodLookBack = input(34)\ndcHi2 = highest(PeriodLookBack)\n"
        ds = TH.rut(vb, "pine")
        cao = {tuple(t["tham_so"]) for t in ds if t["chi_bao"] == "cao_nhat"}
        self.assertIn((55.0,), cao)
        self.assertIn((34.0,), cao)

    def test_khong_bao_gio_chay_ma(self):
        """Bo rut chi doc van ban. Ma co hai khong duoc gay tac dung phu nao."""
        doc = "//@version=5\nimport os\nema(close, 10)\n" + "x" * 100
        ds = TH.rut(doc, "pine")
        self.assertTrue([t for t in ds if t["chi_bao"] == "ema"])


class RutMql(unittest.TestCase):
    def test_ima_lay_ca_phuong_phap_va_nguon_gia(self):
        ds = TH.rut(MQL, "mql")
        ema = [t for t in ds if t["chi_bao"] == "ema"]
        self.assertTrue(ema)
        self.assertEqual(ema[0]["tham_so"], [200.0])
        self.assertEqual(ema[0]["cot"], "close")

    def test_irsi_iatr(self):
        ds = TH.rut(MQL, "mql")
        self.assertTrue([t for t in ds if t["chi_bao"] == "rsi"])
        self.assertTrue([t for t in ds if t["chi_bao"] == "atr"])


class DienDatDuoc(unittest.TestCase):
    def test_ema_tren_high_dien_dat_duoc(self):
        """`toan_hang()` cho `ema` nhan `cot` - nen EMA34(high) viet ra duoc."""
        ok, _ = TH.dien_dat_duoc({"chi_bao": "ema", "cot": "high"})
        self.assertTrue(ok)

    def test_rsi_tren_high_dien_dat_duoc_tu_01_09(self):
        """Truoc 01/09 `rsi` luon tinh tren close, va do la khac biet THAT nen
        bai nay doi `False`. Tu 01/09 `rsi` nhan `cua`/`cot` - `rsi(hl2, 14)`
        va `rsi(ema(close,5), 14)` la dang co that trong ma nguoi ta viet."""
        ok, _ = TH.dien_dat_duoc({"chi_bao": "rsi", "cot": "high"})
        self.assertTrue(ok)

    def test_atr_tren_high_van_KHONG_dien_dat_duoc(self):
        """Hieu chuan chieu nguoc: `atr` tinh tu CA OHLC nen mot 'nguon gia'
        cho no la vo nghia. Neu moi thu deu dien dat duoc thi bang con thieu
        tro thanh mot bang rong."""
        ok, thieu = TH.dien_dat_duoc({"chi_bao": "atr", "cot": "high"})
        self.assertFalse(ok)
        self.assertIn("close", thieu)

    def test_linreg_chua_co_toan_hang(self):
        ok, thieu = TH.dien_dat_duoc({"chi_bao": "linreg", "cot": "close"})
        self.assertFalse(ok)
        self.assertIn("linreg", thieu)

    def test_hl2_gio_la_mot_nguon_gia_dien_dat_duoc(self):
        """`ta.sma(hl2, 20)` la dang co that; truoc 01/09 no bi cham la khong
        dien dat duoc va thanh phan bi vut. `ngu_phap.COT_TONG_HOP` tinh no."""
        ok, _ = TH.dien_dat_duoc({"chi_bao": "ema", "cot": "hl2"})
        self.assertTrue(ok)

    def test_nguon_tong_hop_cho_chi_bao_KHONG_nhan_cot_van_bao_thieu(self):
        ok, thieu = TH.dien_dat_duoc({"chi_bao": "atr", "cot": "hl2"})
        self.assertFalse(ok)
        self.assertIn("atr", thieu)


class GhiSo(unittest.TestCase):
    def setUp(self):
        self._db = SO.DB
        fd, duong = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        SO.DB = Path(duong)
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db

    def test_thu_hoi_ghi_va_gop_trung(self):
        a = TH.thu_hoi("Sonic R", SONIC, "http://x", "test", ly_do_loai="FAIL cong 1")
        self.assertGreater(a["rut_duoc"], 0)
        self.assertEqual(a["moi"], a["rut_duoc"])
        b = TH.thu_hoi("Sonic R ban 2", SONIC, "http://y", "test")
        self.assertEqual(b["moi"], 0, "cung thanh phan phai gop chu khong nhan ban")
        n = SO.mot("SELECT SUM(so_lan) s FROM thanh_phan")["s"]
        self.assertGreater(n, a["rut_duoc"])

    def test_giu_ly_do_loai(self):
        """Thanh phan tu he BI LOAI van duoc giu, va biet no den tu dau."""
        TH.thu_hoi("he thua", SONIC, "http://z", "test",
                   ly_do_loai="truot 1_loi_hon_mua_giu")
        r = SO.mot("SELECT ly_do_loai FROM thanh_phan WHERE ly_do_loai!='' LIMIT 1")
        self.assertIsNotNone(r)
        self.assertIn("1_loi_hon_mua_giu", r["ly_do_loai"])

    def test_toan_hang_con_thieu_xep_theo_so_lan(self):
        TH.thu_hoi("Sonic R", SONIC, "http://x", "test")
        ds = TH.toan_hang_con_thieu()
        self.assertTrue(ds)
        self.assertIn("linreg", [r["chi_bao"] for r in ds])

    def test_van_ban_rong_khong_no(self):
        self.assertEqual(TH.rut(""), [])
        self.assertEqual(TH.thu_hoi("", "", "", "")["rut_duoc"], 0)


if __name__ == "__main__":
    unittest.main()
