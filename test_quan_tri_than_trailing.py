# -*- coding: utf-8 -*-
"""DAC TA: `quan_tri_than` phai boc duoc TRAILING va BASKET TP tu than ham.

Bai test viet TRUOC phan cai dat.

## VI SAO HAI CO CHE NAY

`dich_mq5_quan_tri.py` ghi: *"`trailing` la co che manh nhat tung do duoc: lai
holdout x4,8, sut giam giam 15 lan"*. Va `quan_tri.py` ghi kho co 262 co che
toan tin hieu VAO, 0 co che quan tri.

Ban `quan_tri_than` hien boc duoc: chot theo rot dinh lai · dung lo ca ro ·
chot lai ca ro · khoang cach hedge · tia mot phan. Con THIEU hai thu viet rat
pho bien trong EA that:

  1. TRAILING STOP viet thang trong ma - `SL = gia - N * _Point`, doi theo gia.
  2. BASKET TP theo SO PIP (khong phai theo tien) - dong ca ro khi lai >= N pip.

## BA CHO KHONG DUOC NHAN BUA - giong het ban hien tai

  * dong da CHU THICH la ban tac gia DA BO;
  * nguong khong phai hang so thi KHONG doan;
  * so sanh khong dan toi lenh sua/dong thi khong tinh.
"""
from __future__ import annotations

import unittest

from nhan import quan_tri_than as QTT

#: Trailing viet kieu pho bien nhat cua MQL5: doi SL theo gia, cach N diem.
MQL_TRAILING = """
input int TrailingStart = 150;
input int TrailingStep  = 50;

void QuanLiTrailing()
{
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      double gia_mo = PositionGetDouble(POSITION_PRICE_OPEN);
      double gia    = SymbolInfoDouble(_Symbol,SYMBOL_BID);
      if(gia - gia_mo > TrailingStart*_Point)
      {
         double sl_moi = gia - TrailingStep*_Point;
         trade.PositionModify(_Symbol, sl_moi, 0);
      }
   }
}
"""

#: Basket TP theo PIP: dong ca ro khi lai tinh bang diem vuot nguong.
MQL_BASKET_PIP = """
input int BasketTPPoints = 300;

double LaiRoDiem()
{
   double t=0;
   for(int i=PositionsTotal()-1;i>=0;i--)
      t += PositionGetDouble(POSITION_PROFIT);
   return t;
}

void CloseAll()
{
   for(int i=PositionsTotal()-1;i>=0;i--)
      trade.PositionClose(PositionGetSymbol(i));
}

void Kiem()
{
   double diem = (SymbolInfoDouble(_Symbol,SYMBOL_BID) - GiaTB())/_Point;
   if(diem >= BasketTPPoints)
      CloseAll();
}
"""


class BocDuocTrailing(unittest.TestCase):

    def setUp(self):
        self.r = QTT.boc_than(MQL_TRAILING)

    def test_boc_duoc_nguong_bat_trailing(self):
        self.assertEqual(self.r["nut_van"].get("trailing_tu"), 150.0)

    def test_boc_duoc_buoc_trailing(self):
        self.assertEqual(self.r["nut_van"].get("trailing_buoc"), 50.0)

    def test_don_vi_la_DIEM_khong_phai_pip(self):
        """`_Point` la DIEM: tren ma 5 chu so 150 diem = 15 pip. Quy doi thuoc
        ve ben dung vi so chu so phu thuoc symbol - bo boc khong duoc tu chia."""
        self.assertIn("diem", QTT.__doc__.lower())


class BocDuocBasketTPTheoDiem(unittest.TestCase):

    def test_boc_duoc_tp_ca_ro_theo_diem(self):
        r = QTT.boc_than(MQL_BASKET_PIP)
        self.assertEqual(r["nut_van"].get("tp_ro_diem"), 300.0)


class KhongNhanBua(unittest.TestCase):

    def test_dong_da_CHU_THICH_khong_duoc_tinh(self):
        src = MQL_TRAILING.replace("         double sl_moi",
                                   "         //double sl_moi")
        src = src.replace("         trade.PositionModify",
                          "         //trade.PositionModify")
        self.assertNotIn("trailing_buoc", QTT.boc_than(src)["nut_van"])

    def test_nguong_KHONG_phai_hang_so_thi_khong_doan(self):
        src = MQL_TRAILING.replace("input int TrailingStart = 150;", "")
        r = QTT.boc_than(src)
        self.assertNotIn("trailing_tu", r["nut_van"])
        self.assertTrue(r["thieu"], "doc duoc co che ma khong doc duoc so thi phai bao")

    def test_so_sanh_khong_dan_toi_SUA_LENH_thi_bo_qua(self):
        src = MQL_TRAILING.replace("trade.PositionModify(_Symbol, sl_moi, 0);",
                                   'Print("chi in thoi");')
        self.assertNotIn("trailing_buoc", QTT.boc_than(src)["nut_van"])

    def test_ma_khong_co_gi_thi_khong_ra_nut(self):
        self.assertEqual(QTT.boc_than("void OnTick(){int a=1;}")["nut_van"], {})


class DAU_NGOAC_CUNG_DONG(unittest.TestCase):
    """`void f(){ ... }` - kieu K&R, rat pho bien, HIEN KHONG DOC DUOC.

    `_cac_ham` doi khai bao ham ket thuc o CUOI DONG (`[ \\t]*$`), nen mot ham
    viet `void CloseAll(){...}` khong duoc nhan la ham nao ca. Hau qua khong
    phai "boc thieu mot nut" ma la boc duoc **KHONG GI**: khong tim ra ham dong
    ro thi moi nguong deu bi bo vi "so sanh khong dan toi dong ro".

    Do la mot lop ma nguon bi mu hoan toan, khong phai mot truong hop hiem.
    """

    def test_boc_duoc_ham_viet_dau_ngoac_cung_dong(self):
        src = """
double peakwin=0;
double GetProfits(){double p=0;int i=PositionsTotal()-1;
  while(i>=0){p+=PositionGetDouble(POSITION_PROFIT);i--;} return p;}
void CloseAll(){int i=PositionsTotal()-1;
  while(i>=0){trade.PositionClose(PositionGetSymbol(i));i--;}}
void Kiem(){double profits=GetProfits();
  peakwin=MathMax(peakwin,profits);
  if(peakwin>=45&&profits<(peakwin*0.9)) CloseAll();
  if(profits<=-120) CloseAll();}
"""
        n = QTT.boc_than(src)["nut_van"]
        self.assertEqual(n.get("chot_lui_tu"), 45.0)
        self.assertEqual(n.get("chot_lui_ty"), 0.9)
        self.assertEqual(n.get("dung_lo"), 120.0)


class KHONG_PHA_BAN_DANG_CHAY(unittest.TestCase):
    """Them chuc nang khong duoc lam mat chuc nang. Ban viet ngoac XUONG DONG
    da chay duoc tu truoc - phai con nguyen."""

    def test_van_boc_duoc_chot_lui_va_dung_lo_kieu_cu(self):
        src = """
double peakwin=0;

double GetProfits()
{
   double profits=0;
   int i=PositionsTotal()-1;
   while(i>=0)
   {
      profits+=PositionGetDouble(POSITION_PROFIT);
      i--;
   }
   return profits;
}

void CloseAll()
{
   int i=PositionsTotal()-1;
   while(i>=0)
   {
      trade.PositionClose(PositionGetSymbol(i));
      i--;
   }
}

void Kiem()
{
   double profits=GetProfits();
   peakwin=MathMax(peakwin,profits);
   if(peakwin>=45&&profits<(peakwin*0.9))
      CloseAll();
   if(profits<=-120)
      CloseAll();
}
"""
        n = QTT.boc_than(src)["nut_van"]
        self.assertEqual(n.get("chot_lui_tu"), 45.0)
        self.assertEqual(n.get("chot_lui_ty"), 0.9)
        self.assertEqual(n.get("dung_lo"), 120.0)


class KHONG_NHAN_BUA_TRAILING(unittest.TestCase):
    """Bo sung 19/09 sau khi mot ban cai dat lot qua bo test dau.

    Ban do bat MOI so sanh dang `X > BIEN*_Point` la nguong trailing. Nhung
    `*_Point` la cach viet "N diem" cua MQL5 va no co mat o KHAP NOI: loc
    spread, khoang cach dat TP, khoang cach toi thieu toi SL cua san, buoc
    luoi... Khong cai nao trong so do la trailing.

    Dau hieu PHAN BIET khong nam o `_Point` ma o cho: mot vong trailing phai
    SUA LENH (`PositionModify`) trong chinh nhanh do. Loc spread thi `return`.
    """

    def test_loc_spread_KHONG_phai_trailing(self):
        src = """
input int MaxSpread = 30;
void OnTick()
{
   double sp = SymbolInfoInteger(_Symbol,SYMBOL_SPREAD);
   if(sp > MaxSpread*_Point)
      return;
   trade.Buy(0.1,_Symbol);
}
"""
        n = QTT.boc_than(src)["nut_van"]
        self.assertNotIn("trailing_tu", n)
        self.assertNotIn("trailing_buoc", n)

    def test_khoang_cach_TP_KHONG_phai_buoc_trailing(self):
        src = """
input int TakeProfitPoints = 200;
void OnTick()
{
   double tp = SymbolInfoDouble(_Symbol,SYMBOL_ASK) - TakeProfitPoints*_Point;
   trade.Buy(0.1,_Symbol,tp);
}
"""
        self.assertNotIn("trailing_buoc", QTT.boc_than(src)["nut_van"])

    def test_khoang_cach_toi_thieu_cua_san_KHONG_phai_trailing(self):
        src = """
input int StopLevel = 50;
void OnTick()
{
   double kc = SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   if(kc > StopLevel*_Point)
      Print("san doi khoang cach lon hon");
}
"""
        self.assertNotIn("trailing_tu", QTT.boc_than(src)["nut_van"])

    def test_VAN_boc_duoc_trailing_that(self):
        """Hieu chuan chieu nguoc. Khong co bai nay thi cach de nhat de lam ba
        bai tren xanh la TAT han duong trailing di."""
        n = QTT.boc_than(MQL_TRAILING)["nut_van"]
        self.assertEqual(n.get("trailing_tu"), 150.0)
        self.assertEqual(n.get("trailing_buoc"), 50.0)
