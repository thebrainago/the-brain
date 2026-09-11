# -*- coding: utf-8 -*-
"""Kiem `nhan/de_quan_tri.py` - chen bo quan tri cua ta vao EA NGOAI.

Nang luc `hethong.txt` neu: *"He quan li lenh nay co the quan tri doc lap hoac
lam 1 bo quy tac de tich hop vao nhung he thong khac"*.

Cai kho khong phai chen - la chen DUNG BA CHO. Thieu mot cho thi EA van bien
dich, van chay, van ra mot bang ket qua - va bang do doc nhu "quan tri khong an"
trong khi quan tri chua he chay. Do la dang hong dat nhat cua ca du an.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import de_quan_tri as DQ  # noqa: E402

EA_TOI_THIEU = """
#property version "1.00"
input double InpLot = 0.1;

int OnInit()
  {
   Print("khoi tao");
   return(INIT_SUCCEEDED);
  }

void OnTick()
  {
   double g = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(g > 0) Print(g);
  }
"""

EA_KHONG_ONINIT = """
#property version "1.00"
void OnTick()
  {
   Print("chi co OnTick");
  }
"""

KHOI_GIA = "// khoi quan tri gia lap\nvoid QT_Khoi(){} void QT_NapBang(){}\n"


class ChenDU_BA_CHO(unittest.TestCase):
    def test_chen_du_ba_cho(self):
        ra = DQ.chen(EA_TOI_THIEU, KHOI_GIA)
        self.assertIn(KHOI_GIA.strip().splitlines()[0], ra)   # 1. khoi
        self.assertIn(DQ.GOI_MOI_TICK, ra)                    # 2. moi tick
        self.assertIn("QT_Khoi()", ra)                        # 3. khoi tao
        self.assertEqual(DQ.kiem_da_chen(ra), [])

    def test_goi_quan_tri_o_DAU_OnTick(self):
        """Quan tri phai thay vi the o trang thai DAU bar. Goi sau logic cua EA
        thi no nhin thay vi the EA vua doi trong chinh tick nay."""
        ra = DQ.chen(EA_TOI_THIEU, KHOI_GIA)
        i, j = DQ._mo_than(ra, DQ._RE_ONTICK.search(ra).end())
        than = ra[i:j]
        self.assertLess(than.index(DQ.GOI_MOI_TICK), than.index("SymbolInfoDouble"))

    def test_EA_KHONG_co_OnInit_thi_TU_THEM(self):
        """Chen goi vao mot ham khong ton tai thi bien dich bao loi; bo qua thi
        bang luat toan 0 va quan tri chet lang le."""
        ra = DQ.chen(EA_KHONG_ONINIT, KHOI_GIA)
        self.assertIn("int OnInit()", ra)
        self.assertIn("QT_Khoi()", ra)
        self.assertEqual(DQ.kiem_da_chen(ra), [])

    def test_khai_CTrade_neu_EA_chua_co(self):
        ra = DQ.chen(EA_TOI_THIEU, KHOI_GIA)
        self.assertIn("CTrade qt_trade;", ra)

    def test_KHONG_khai_CTrade_hai_lan(self):
        ea = EA_TOI_THIEU.replace("#property version", "CTrade qt_trade;\n#property version")
        ra = DQ.chen(ea, KHOI_GIA)
        self.assertEqual(ra.count("CTrade qt_trade;"), 1,
                         "khai hai lan -> bien dich bao trung ten")

    def test_khong_phai_EA_thi_TU_CHOI(self):
        with self.assertRaises(DQ.KhongChenDuoc):
            DQ.chen("void OnStart() { Print(1); }", KHOI_GIA)


class BoKiemPHAI_BAT_DUOC_CHEN_THIEU(unittest.TestCase):
    """Bien dich XONG khong co nghia la quan tri DANG CHAY."""

    def test_thieu_goi_moi_tick(self):
        loi = DQ.kiem_da_chen("QT_Khoi(); QT_NapBang(); QT_ChonLuat(0); CTrade qt_trade;")
        self.assertTrue(any("khong bao gio chay" in x for x in loi), loi)

    def test_thieu_nap_bang(self):
        loi = DQ.kiem_da_chen(DQ.GOI_MOI_TICK + " QT_Khoi(); QT_ChonLuat(0); CTrade qt_trade;")
        self.assertTrue(any("bang luat toan 0" in x for x in loi), loi)

    def test_thieu_CTrade(self):
        loi = DQ.kiem_da_chen(DQ.GOI_MOI_TICK + " QT_Khoi(); QT_NapBang(); QT_ChonLuat(0);")
        self.assertTrue(any("khong dat duoc lenh" in x for x in loi), loi)

    def test_goi_khong_o_dau_OnTick_thi_keu(self):
        xau = ("void OnTick()\n  {\n   double a = 1; double b = 2; double c = 3;\n"
               "   " + DQ.GOI_MOI_TICK + "\n  }\n"
               "QT_Khoi(); QT_NapBang(); QT_ChonLuat(0); CTrade qt_trade;")
        loi = DQ.kiem_da_chen(xau)
        self.assertTrue(any("khong o DAU OnTick" in x for x in loi), loi)


class CHEN_VAO_EA_NGOAI_THAT(unittest.TestCase):
    """Chay tren mot file .mq5 THAT do seeker tai ve, khong phai ma gia lap."""

    EA = (GOC / "downloaded_codes" / "github" /
          "EA Snippets_Breakout_Breakout1.mq5")

    @unittest.skipUnless(EA.exists(), "chua co EA ngoai trong kho")
    def test_chen_duoc_vao_EA_that(self):
        from nhan import quan_tri_dsl as QT
        kho = [c for c in QT.doc_kho() if not QT.kiem_khai_bao(c)][:6]
        self.assertGreaterEqual(len(kho), 2, "kho quan tri qua it luat")
        ma = self.EA.read_text(encoding="utf-8", errors="ignore")
        moi, luat = DQ.chen_tu_spec(ma, kho, khung="D1", magic=0)
        self.assertEqual(DQ.kiem_da_chen(moi), [])
        self.assertGreater(len(moi), len(ma) * 1.5,
                           "ma sau khi chen khong lon hon bao nhieu - chen hut?")
        self.assertGreaterEqual(len(luat), 2)

    @unittest.skipUnless(EA.exists(), "chua co EA ngoai trong kho")
    def test_luat_0_LUON_la_moc_tat_quan_tri(self):
        """Khong co moc trong CUNG lan chay thi khong so duoc voi gi."""
        from nhan import quan_tri_dsl as QT
        kho = [c for c in QT.doc_kho() if not QT.kiem_khai_bao(c)][:6]
        ma = self.EA.read_text(encoding="utf-8", errors="ignore")
        moi, _ = DQ.chen_tu_spec(ma, kho, khung="D1", magic=0)
        self.assertIn("QT_MaLuat", moi)
        self.assertIn("QT_ChonLuat(QT_MaLuat)", moi)


if __name__ == "__main__":
    unittest.main()
