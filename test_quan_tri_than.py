# -*- coding: utf-8 -*-
"""Test cho `nhan/quan_tri_than.py` - boc quan tri lenh tu THAN HAM.

Khac `test_quan_tri_nhieu`: o do bo boc doc TEN INPUT cua tac gia, o day no doc
CHINH MA CHAY. Hai thu bat duoc hai lop khac han nhau, va lop thu hai la lop
chu du an hoi den ngay 18/09: *"cach tia lenh can tinh vi hon - can tim cac EA
co kha nang tia lenh de rut loi phan quan ly lenh"*.
"""
from __future__ import annotations

import unittest

from nhan import quan_tri_than as QTT

#: Rut gon tu `mau_thu/EA Snippets_Breakout_Breakout2.mq5` - mot ro theo ROT
#: DINH LAI that: vu trang o $45, dong ca ro khi lai tut ve 90% dinh. KHONG co
#: mot `input` nao mo ta viec nay, nen bo boc theo ten input mu hoan toan.
MQL_CHOT_LUI = """
input double InpLot = 1.0;
double peakwin=0;

double GetProfits()
{
   double profits=0;
   int i=PositionsTotal()-1;
   while(i>=0)
   {
      PositionGetSymbol(i);
      profits+=PositionGetDouble(POSITION_PROFIT);
      i--;
   }
   return profits;
}

void CloseAll()
{
   CTrade trade;
   int i=PositionsTotal()-1;
   while(i>=0)
   {
      trade.PositionClose(PositionGetSymbol(i));
      i--;
   }
}

void checkForClose()
{
   double profits=GetProfits();
   if(profits<=0)
      peakwin=0;
   else
      peakwin=MathMax(peakwin,profits);
   if(peakwin>=45&&profits<(peakwin*0.9))
      CloseAll();
   if(profits<=-120)
      CloseAll();
   if(profits>=200)
      CloseAll();
}
"""


class TimDuocBoKhungCuaRo(unittest.TestCase):
    """Truoc khi doc duoc nguong, phai biet dau la `lai ca ro` va dau la `dong ca ro`."""

    def setUp(self):
        self.r = QTT.boc_than(MQL_CHOT_LUI)

    def test_nhan_ra_ham_tinh_lai_ca_ro(self):
        self.assertIn("GetProfits", self.r["ham_lai_ro"])

    def test_nhan_ra_ham_dong_ca_ro(self):
        self.assertIn("CloseAll", self.r["ham_dong_ro"])

    def test_nhan_ra_bien_mang_lai_ca_ro(self):
        self.assertIn("profits", self.r["bien_lai_ro"])

    def test_nhan_ra_bien_dinh_lai(self):
        """`peakwin=MathMax(peakwin,profits)` - bien theo DINH cua lai ro."""
        self.assertIn("peakwin", self.r["bien_dinh"])


class ChotTheoLUIKHOIDINH(unittest.TestCase):
    """`peakwin>=45 && profits<peakwin*0.9` - trailing tren LAI CA RO."""

    def setUp(self):
        self.nut = QTT.boc_than(MQL_CHOT_LUI)["nut_van"]

    def test_boc_duoc_muc_vu_trang(self):
        self.assertEqual(self.nut.get("_chot_lui_tu"), 45.0)

    def test_boc_duoc_ty_le_lui(self):
        self.assertEqual(self.nut.get("_chot_lui_ty"), 0.9)

    def test_danh_dau_la_CHUA_MO_PHONG(self):
        """`mo_phong_v2` chua co nut nay. Bo im lang la mat ca mot co che."""
        self.assertTrue(
            all(k.startswith("_") for k in ("_chot_lui_tu", "_chot_lui_ty")),
            "nut chua mo phong duoc phai mang tien to `_`")


class ChanDuoiVaChotLaiCaRo(unittest.TestCase):
    def setUp(self):
        self.nut = QTT.boc_than(MQL_CHOT_LUI)["nut_van"]

    def test_dung_lo_ca_ro_lay_TRI_TUYET_DOI(self):
        """`profits<=-120` la dung lo 120, khong phai -120."""
        self.assertEqual(self.nut.get("dung_lo"), 120.0)

    def test_chot_tien_ca_ro(self):
        self.assertEqual(self.nut.get("chot_tien"), 200.0)


class KhongNhanBua(unittest.TestCase):
    """Bo boc nay doc ma CHAY - nhan bua thi sinh co che khong co trong EA."""

    def test_ma_khong_co_quan_tri_thi_khong_ra_nut(self):
        self.assertEqual(QTT.boc_than("void OnTick(){ int a=1; }")["nut_van"], {})

    def test_nguong_so_sanh_voi_BIEN_khong_duoc_nhan(self):
        """`profits <= -InpMaxLoss` khong phai hang so -> khong duoc doan gia tri."""
        src = MQL_CHOT_LUI.replace("profits<=-120", "profits<=-InpMaxLoss")
        self.assertNotIn("dung_lo", QTT.boc_than(src)["nut_van"])

    def test_dong_da_CHU_THICH_khong_duoc_tinh(self):
        """Ban goc de day dong `//if(...) CloseAll();` - do la ban da BO."""
        src = MQL_CHOT_LUI.replace("   if(profits>=200)", "   //if(profits>=200)")
        self.assertNotIn("chot_tien", QTT.boc_than(src)["nut_van"])

    def test_so_sanh_khong_dan_toi_dong_ro_thi_bo_qua(self):
        src = MQL_CHOT_LUI.replace("   if(profits>=200)\n      CloseAll();",
                                   "   if(profits>=200)\n      Print(\"vui\");")
        self.assertNotIn("chot_tien", QTT.boc_than(src)["nut_van"])


#: `Tradesinfo.hedgeprice=price-(hedgerange*_Point)` - zone recovery that, va
#: khoang cach nam trong THAN HAM chu khong phai ten input.
MQL_HEDGE = """
input int HedgeRange = 300;
void moLenh(double price)
{
   int hedgerange=HedgeRange;
   Tradesinfo.hedgeprice=price-(hedgerange*_Point);
}
"""


class KhoangCachHedgeDocTuThanHam(unittest.TestCase):
    def test_boc_duoc_khoang_cach_hedge_theo_diem(self):
        nut = QTT.boc_than(MQL_HEDGE)["nut_van"]
        self.assertEqual(nut.get("hedge_tu"), 300.0)


MQL_TIA = """
void tia()
{
   if(PositionGetDouble(POSITION_PROFIT)>=30)
      trade.PositionClosePartial(_Symbol, PositionGetDouble(POSITION_VOLUME)*0.5);
}
"""


class TiaLenhDocTuThanHam(unittest.TestCase):
    """Dung cau chu du an hoi: EA nao tia lenh, va tia bao nhieu."""

    def setUp(self):
        self.nut = QTT.boc_than(MQL_TIA)["nut_van"]

    def test_nhan_ra_co_tia_lenh(self):
        self.assertEqual(self.nut.get("_tia_ty"), 0.5)

    def test_boc_duoc_muc_lai_kich_hoat_tia(self):
        self.assertEqual(self.nut.get("_tia_tu"), 30.0)


class DocDUOC_CO_CHE_nhung_KHONG_DOC_DUOC_SO(unittest.TestCase):
    """Luat cua du an: `CHUA_DO_DUOC` khong duoc lan voi ket qua AM.

    `EA Snippets_Breakout_Breakout5-2-2.mq5` la ca nay that: no CO chot theo
    dinh lai, nhung nguong vu trang la `takeprofitamountperstartvolume *
    GetStartVolume()` - co gian theo lot. Im lang o day thi ban quet doc y het
    "EA nay khong co co che gi".
    """

    def setUp(self):
        src = MQL_CHOT_LUI.replace("peakwin>=45", "peakwin>=expectation")
        self.r = QTT.boc_than(src)

    def test_khong_bia_ra_con_so(self):
        self.assertNotIn("_chot_lui_tu", self.r["nut_van"])

    def test_nhung_phai_BAO_RA_la_co_co_che(self):
        self.assertTrue(any("chot_lui" in x for x in self.r["thieu"]),
                        "doc duoc co che ma khong doc duoc so thi phai bao")


class TyLeLuiViet_BANG_HOAC_NHO_HON(unittest.TestCase):
    """`profits<=(peakwin*0.7)` - ban goc viet `<=`, khong chi `<`."""

    def test_nhan_ca_hai_cach_viet(self):
        src = MQL_CHOT_LUI.replace("profits<(peakwin*0.9)", "profits<=(peakwin*0.7)")
        self.assertEqual(QTT.boc_than(src)["nut_van"].get("_chot_lui_ty"), 0.7)


class NoiVaoDUONG_CHAY_THAT(unittest.TestCase):
    """`quan_tri.boc_mot` la buoc 1 cua `day_chuyen_quantlab` - duong chay that.

    Viet mot module moi ma khong noi vao day thi no la module MO COI: theo luat
    cua du an, module khong duoc goi tu mot cua vao that thi *bang khong co*.
    """

    def setUp(self):
        from nhan import quan_tri as QT
        self.QT = QT
        self.s = QT.boc_mot(MQL_CHOT_LUI, ten="thu.mq5")

    def test_boc_mot_thay_duoc_nut_tu_than_ham(self):
        self.assertIsNotNone(self.s, "than ham co nut ma spec van None")
        self.assertEqual(self.s["nut_van"].get("dung_lo"), 120.0)

    def test_ghi_ro_nut_den_tu_than_ham(self):
        """Phai truy duoc nguon cua tung con so, khong tron voi input tac gia."""
        self.assertEqual(self.s["input_goc"].get("dung_lo"), "than_ham")

    def test_INPUT_THANG_khi_ca_hai_cung_noi_mot_nut(self):
        """Input la so nguoi chay THAT SU dat; hang so trong ma chi la mac dinh."""
        src = MQL_CHOT_LUI.replace(
            "input double InpLot = 1.0;",
            "input double InpLot = 1.0;\ninput double MaxLossUSD = 500;")
        s = self.QT.boc_mot(src, ten="thu.mq5")
        self.assertEqual(s["nut_van"].get("dung_lo"), 500.0)
        self.assertEqual(s["input_goc"].get("dung_lo"), "MaxLossUSD")

    def test_QUA_DUOC_BUOC_LOC(self):
        """Dich cuoi: `loc` doi >= 2 nut chay duoc. Truoc day khong file nao du."""
        giu, _ = self.QT.loc([self.s], in_ra=lambda *a, **k: None)
        self.assertEqual(len(giu), 1, "co che co du nut ma van bi loc bo")
