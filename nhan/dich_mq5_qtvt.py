# -*- coding: utf-8 -*-
"""dich_mq5_qtvt.py - DICH KHAI BAO QUAN TRI VI THE SANG MQL5. Hai duong ra.

    sinh_khoi(spec)      -> ma de CHEN vao EA co san (de DO trong tester)
    sinh_ea_giam_sat()   -> EA DOC LAP quan ly vi the cua EA khac (de CHAY THAT)

Chu du an 07/09: *"EA khong gan duoc sau nay ta van co the de lenh len de quan
li von."* Duong `giam_sat` lam dung viec do: no **khong co tin hieu vao nao**,
chi doc vi the dang mo tren symbol (theo magic, hoac MOI magic) roi ap luat.

**Rang buoc cung:** MT5 Strategy Tester chi chay DUNG MOT EA. Nen ban giam sat
**khong backtest duoc cung EA ngoai** - muon do thi phai dung ban `nhung`. Hai
ban dung CHUNG mot khoi luat de khong lech nhau.

## THU TU AP LUAT - co chu dich, doi thu tu la doi ket qua

    1. CHAN        tran cung: tuoi gio · lo toi da · so vi the · lot toi da
    2. CHOT RO     tong ca ro dat muc -> dong het
    3. CAT HOA     dong cap lai+lo khi tong >= 0
    4. DAT HUE     da tung lai >= muc -> dong khi ve entry
    5. TRAILING    doi dinh, dong khi lui qua khoang
    6. DONG MOT PHAN
    7. NHOI        chi khi KHONG co lenh dong nao o tren

Chan truoc chot, chot truoc quan tri chi tiet: mot tran cung bi vuot thi moi
luat khac deu vo nghia.

## BA BAY DA SAP THAT, DA BIT TRONG MA SINH RA

1. **Hanh dong sinh Y DINH, khong dat lenh thang.** Nen khung tin hieu doi luc
   00:00 nam NGOAI phien CFD -> dat thang o do thi "Market closed", khong dau
   vet [[tester-cfd-chi-so-3-bay]]. Moi lenh di qua `QT_KhopYDinh()`.
2. **`PositionClosePartial` duoi min lot that bai IM LANG** -> `QT_DongMotPhan`
   kiem `SYMBOL_VOLUME_MIN` va **bao ra bien dem** thay vi im.
3. **Nhoi khong tran = chay tai khoan** (do 07/09: lot_x 1,5 -> DD 99,98% ngay
   trong mau). `sinh_khoi` **TU CHOI** spec co nhoi ma khong co tran.
"""
from __future__ import annotations


class KhongDichDuoc(Exception):
    pass


def _atr(v, mac_dinh=0.0) -> float:
    """Lay so do khoang cach theo ATR. Chi nhan {'atr': x} - don vi khac phai
    qua `quan_tri_dsl.sang_atr()` truoc, vi quy doi can du lieu tai san dich."""
    if isinstance(v, dict):
        if "atr" in v:
            return float(v["atr"])
        raise KhongDichDuoc("con so chua quy ve ATR: %s (goi sang_atr truoc)" % v)
    if isinstance(v, (int, float)):
        return float(v)
    return float(mac_dinh)


def _so(v, mac_dinh=0.0) -> float:
    if isinstance(v, dict):
        for k in ("tien", "pct", "so", "gio", "atr"):
            if k in v:
                return float(v[k])
        return float(mac_dinh)
    return float(v) if isinstance(v, (int, float)) else float(mac_dinh)


KHOI = r"""
//=================== QUAN TRI VI THE: %(ten)s ======================
//  Sinh tu nhan/dich_mq5_qtvt.py. KHONG SUA TAY.
//  lop = %(lop)s | luat = %(luat)s
input long   QT_Magic      = %(magic)d;   // 0 = quan ly MOI vi the cua symbol
input double QT_DatHue     = %(dat_hue)s; // >0: dua SL ve entry sau k x ATR lai
input double QT_TrailKhoang= %(tr_khoang)s;
input double QT_TrailBatDau= %(tr_batdau)s;
input double QT_TiaTu      = %(tia_tu)s;  // >0: dong mot phan o k x ATR lai
input double QT_TiaTyLe    = %(tia_ty)s;
input double QT_NhoiKhoang = %(nhoi_khoang)s;
input double QT_NhoiLotX   = %(nhoi_lotx)s;
input int    QT_NhoiMax    = %(nhoi_max)d;
input int    QT_NhoiChieu  = %(nhoi_chieu)d; // 1 nhoi khi AM · 2 khi DUONG · 0 tat
input double QT_ChotRoTien = %(chot_tien)s;  // >0: dong ro khi tong lai >= X USD
input double QT_ChotRoAtr  = %(chot_atr)s;
input double QT_CatHoaTu   = %(cat_hoa)s;    // >0: dong cap lai+lo khi tong >=0
input double QT_HedgeTu    = %(hedge_tu)s;
input double QT_HedgeLotX  = %(hedge_lotx)s;
input int    QT_TranViThe  = %(tran_vt)d;
input double QT_TranLot    = %(tran_lot)s;
input double QT_TranLoTien = %(tran_lo)s;    // >0: dong het khi lo ro >= X USD
input int    QT_TranTuoiGio= %(tran_tuoi)d;
input double QT_LotGoc     = %(lot_goc)s;

int    g_qt_atr    = INVALID_HANDLE;
bool   g_qt_be     = false;
double g_qt_dinh   = 0.0;
int    g_qt_sonhoi = 0;
double g_qt_ynhoi  = 0.0;      // khoi luong cho nhoi
int    g_qt_ydong  = 0;        // 1 = dong het
double g_qt_ytia   = 0.0;      // khoi luong cho tia
int    g_qt_tia_hong = 0;      // dem lan tia bi tu choi vi duoi min lot
bool   g_qt_datia  = false;

void QT_Khoi()
  {
   g_qt_atr = iATR(_Symbol, PERIOD_%(khung)s, 14);
  }

double QT_Atr()
  {
   double b[];
   if(g_qt_atr == INVALID_HANDLE) return(0.0);
   if(CopyBuffer(g_qt_atr, 0, 1, 1, b) != 1) return(0.0);
   return(b[0]);
  }

bool QT_CuaTa(ulong tk)
  {
   if(PositionGetString(POSITION_SYMBOL) != _Symbol) return(false);
   if(QT_Magic == 0) return(true);
   return(PositionGetInteger(POSITION_MAGIC) == QT_Magic);
  }

int QT_SoViThe()
  {
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     { ulong tk = PositionGetTicket(i); if(tk && QT_CuaTa(tk)) n++; }
   return(n);
  }

double QT_LaiRo()
  {
   double v = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk && QT_CuaTa(tk))
         v += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
     }
   return(v);
  }

double QT_LotTong()
  {
   double v = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     { ulong tk = PositionGetTicket(i);
       if(tk && QT_CuaTa(tk)) v += PositionGetDouble(POSITION_VOLUME); }
   return(v);
  }

//--- Gia trung binh theo KHOI LUONG (dung cho luoi/DCA: khoang cach do tu day)
double QT_GiaTB()
  {
   double tv = 0, tg = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(!tk || !QT_CuaTa(tk)) continue;
      double v = PositionGetDouble(POSITION_VOLUME);
      tv += v; tg += PositionGetDouble(POSITION_PRICE_OPEN) * v;
     }
   return(tv > 0 ? tg / tv : 0.0);
  }

int QT_ChieuRo()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk && QT_CuaTa(tk))
         return(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? 1 : -1);
     }
   return(0);
  }

datetime QT_MoSomNhat()
  {
   datetime t = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(!tk || !QT_CuaTa(tk)) continue;
      datetime x = (datetime)PositionGetInteger(POSITION_TIME);
      if(t == 0 || x < t) t = x;
     }
   return(t);
  }

//--- Loi hien tai cua ro theo DON VI GIA (khong theo tien: tien phu thuoc lot)
double QT_LoiGia()
  {
   int c = QT_ChieuRo();
   if(c == 0) return(0.0);
   double tb = QT_GiaTB();
   if(tb <= 0) return(0.0);
   double gia = (c > 0) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                        : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   return((c > 0) ? (gia - tb) : (tb - gia));
  }

//--- CAT HOA: dong CAP vi the lai+lo khi tong cua cap >= 0. Giam so vi the ma
//--- khong hien thuc hoa lo rong - day la co che rieng, khong phai dong het.
void QT_CatHoa()
  {
   ulong tot = 0, xau = 0;
   double lt = 0, lx = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(!tk || !QT_CuaTa(tk)) continue;
      double p = PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
      if(p > lt) { lt = p; tot = tk; }
      if(p < lx) { lx = p; xau = tk; }
     }
   if(tot && xau && (lt + lx) >= 0)
     { qt_trade.PositionClose(tot); qt_trade.PositionClose(xau); }
  }

void QT_DongHet()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     { ulong tk = PositionGetTicket(i); if(tk && QT_CuaTa(tk)) qt_trade.PositionClose(tk); }
   g_qt_be = false; g_qt_dinh = 0; g_qt_sonhoi = 0; g_qt_datia = false;
  }

//--- Tia: PositionClosePartial duoi min lot THAT BAI IM LANG -> dem lai de biet
void QT_DongMotPhan(double ty_le)
  {
   double b  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double mn = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(!tk || !QT_CuaTa(tk)) continue;
      double vol = PositionGetDouble(POSITION_VOLUME) * ty_le;
      if(b > 0) vol = MathFloor(vol / b) * b;
      if(vol < mn || vol <= 0) { g_qt_tia_hong++; continue; }
      qt_trade.PositionClosePartial(tk, vol);
     }
  }

//--- MOI NEN: chi TINH va ghi Y DINH. Khong dat lenh o day.
void QT_MoiNen()
  {
   int n = QT_SoViThe();
   if(n == 0)
     { g_qt_be = false; g_qt_dinh = 0; g_qt_sonhoi = 0; g_qt_datia = false;
       g_qt_ynhoi = 0; g_qt_ydong = 0; g_qt_ytia = 0; return; }
   double atr = QT_Atr();
   double lai = QT_LaiRo();
   double loi = QT_LoiGia();

   // 1. CHAN - tran cung, xet truoc moi thu
   if(QT_TranLoTien > 0 && lai <= -QT_TranLoTien) { g_qt_ydong = 1; return; }
   if(QT_TranTuoiGio > 0)
     {
      datetime t0 = QT_MoSomNhat();
      if(t0 > 0 && (TimeCurrent() - t0) >= (datetime)(QT_TranTuoiGio * 3600))
        { g_qt_ydong = 1; return; }
     }
   // 2. CHOT RO
   if(QT_ChotRoTien > 0 && lai >= QT_ChotRoTien) { g_qt_ydong = 1; return; }
   if(QT_ChotRoAtr > 0 && atr > 0 && loi >= QT_ChotRoAtr * atr)
     { g_qt_ydong = 1; return; }
   // 3. CAT HOA
   if(QT_CatHoaTu > 0 && atr > 0 && n >= 2 && loi <= -QT_CatHoaTu * atr)
      QT_CatHoa();
   // 4. DAT HUE
   if(QT_DatHue > 0 && atr > 0)
     {
      if(!g_qt_be && loi >= QT_DatHue * atr) g_qt_be = true;
      if(g_qt_be && loi <= 0) { g_qt_ydong = 1; return; }
     }
   // 5. TRAILING
   if(QT_TrailKhoang > 0 && atr > 0)
     {
      int c = QT_ChieuRo();
      double gia = (c > 0) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                           : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      if(c > 0) { if(gia > g_qt_dinh) g_qt_dinh = gia; }
      else      { if(g_qt_dinh == 0 || gia < g_qt_dinh) g_qt_dinh = gia; }
      bool bat = (loi >= QT_TrailBatDau * atr);
      if(bat && c > 0 && gia <= g_qt_dinh - QT_TrailKhoang * atr) { g_qt_ydong = 1; return; }
      if(bat && c < 0 && gia >= g_qt_dinh + QT_TrailKhoang * atr) { g_qt_ydong = 1; return; }
     }
   // 6. TIA
   if(QT_TiaTu > 0 && atr > 0 && !g_qt_datia && loi >= QT_TiaTu * atr)
      g_qt_ytia = QT_TiaTyLe;
   // 7. NHOI - chi khi khong co lenh dong nao o tren
   if(QT_NhoiChieu > 0 && QT_NhoiKhoang > 0 && atr > 0 && g_qt_ydong == 0)
     {
      bool con_cho = (QT_TranViThe <= 0 || n < QT_TranViThe) &&
                     (QT_TranLot <= 0 || QT_LotTong() < QT_TranLot) &&
                     (QT_NhoiMax <= 0 || g_qt_sonhoi < QT_NhoiMax);
      double can = (g_qt_sonhoi + 1) * QT_NhoiKhoang * atr;
      bool dat = (QT_NhoiChieu == 1) ? (loi <= -can) : (loi >= can);
      if(con_cho && dat)
        {
         double vol = QT_LotGoc * MathPow(QT_NhoiLotX, g_qt_sonhoi + 1);
         double b = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
         double mn = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
         if(b > 0) vol = MathRound(vol / b) * b;
         if(vol < mn) vol = mn;
         g_qt_ynhoi = vol;
        }
     }
  }

//--- KHOP Y DINH: chi cho khi phien MO. Xem bay 1 trong docstring.
void QT_KhopYDinh()
  {
   if((ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE)
      != SYMBOL_TRADE_MODE_FULL) return;
   if(g_qt_ydong == 1) { QT_DongHet(); g_qt_ydong = 0; g_qt_ynhoi = 0; g_qt_ytia = 0; return; }
   if(g_qt_ytia > 0)   { QT_DongMotPhan(g_qt_ytia); g_qt_datia = true; g_qt_ytia = 0; }
   if(g_qt_ynhoi > 0)
     {
      int c = QT_ChieuRo();
      if(c != 0)
        {
         if(QT_Magic != 0) qt_trade.SetExpertMagicNumber(QT_Magic);
         bool ok = (c > 0) ? qt_trade.Buy(g_qt_ynhoi, _Symbol)
                           : qt_trade.Sell(g_qt_ynhoi, _Symbol);
         if(ok) g_qt_sonhoi++;
        }
      g_qt_ynhoi = 0;
     }
  }
//================= HET QUAN TRI VI THE ============================
"""


def sinh_khoi(spec: dict, khung: str = "D1", magic: int = 0) -> str:
    """Sinh khoi MQL5 quan tri de CHEN vao mot EA co san.

    EA chu phai co: `CTrade qt_trade;` va goi `QT_Khoi()` trong OnInit,
    `QT_KhopYDinh()` dau OnTick, `QT_MoiNen()` khi co nen moi.
    """
    nh = spec.get("nhoi") or {}
    chan = spec.get("chan") or {}
    if nh and not (chan.get("so_vi_the_toi_da") or chan.get("lot_toi_da")):
        raise KhongDichDuoc(
            "co 'nhoi' ma khong co tran - tu choi dich (cong thuc chay tai khoan)")
    dh = spec.get("dat_hue") or {}
    tr = spec.get("trailing") or {}
    tia = spec.get("tia") or {}
    chot = spec.get("chot") or {}
    ch = spec.get("cat_hoa") or {}
    hg = spec.get("hedge") or {}
    luat = [k for k in ("dat_hue", "trailing", "tia", "nhoi", "chot", "cat_hoa",
                        "hedge", "chan") if spec.get(k)]
    return KHOI % {
        "ten": str(spec.get("ten", "?"))[:60], "lop": spec.get("lop", "don"),
        "luat": "+".join(luat) or "khong", "khung": khung, "magic": magic,
        "dat_hue": "%.4f" % _atr(dh.get("tu"), 0),
        "tr_khoang": "%.4f" % _atr(tr.get("khoang"), 0),
        "tr_batdau": "%.4f" % _atr(tr.get("bat_dau"), 0),
        "tia_tu": "%.4f" % _atr(tia.get("tu"), 0),
        "tia_ty": "%.2f" % float(tia.get("ty_le", 0.5) or 0.5),
        "nhoi_khoang": "%.4f" % _atr(nh.get("khoang"), 0),
        "nhoi_lotx": "%.2f" % float(nh.get("lot_x", 1.0) or 1.0),
        "nhoi_max": int(chan.get("so_vi_the_toi_da") or 0),
        "nhoi_chieu": int(nh.get("chieu", 1) or 1) if nh else 0,
        "chot_tien": "%.2f" % _so(chot.get("tien"), 0),
        "chot_atr": "%.4f" % _atr(chot.get("muc"), 0) if chot.get("muc") else "0",
        "cat_hoa": "%.4f" % _atr(ch.get("tu"), 0),
        "hedge_tu": "%.4f" % _atr(hg.get("tu"), 0),
        "hedge_lotx": "%.2f" % float(hg.get("lot_x", 1.0) or 1.0),
        "tran_vt": int(chan.get("so_vi_the_toi_da") or 0),
        "tran_lot": "%.2f" % float(chan.get("lot_toi_da") or 0),
        "tran_lo": "%.2f" % _so(chan.get("lo_toi_da"), 0),
        "tran_tuoi": int(_so(chan.get("tuoi_gio_toi_da"), 0)),
        "lot_goc": "%.2f" % float(spec.get("lot_goc") or 0.1),
    }


EA_GIAM_SAT = r"""//+------------------------------------------------------------------+
//| %(ten)s - EA GIAM SAT: khong co tin hieu vao nao.
//| Doc vi the dang mo tren symbol (theo QT_Magic, 0 = moi magic) roi ap
//| luat quan tri. Dung de DE LEN mot EA khac khi chay THAT.
//|
//| KHONG backtest duoc cung EA ngoai: MT5 tester chi chay MOT EA. Muon do
//| thi dung ban `nhung` cua cung khai bao nay.
//+------------------------------------------------------------------+
#property copyright "The Brain"
#include <Trade\Trade.mqh>
CTrade qt_trade;
%(khoi)s
datetime g_qt_nen = 0;

int OnInit() { QT_Khoi(); return(INIT_SUCCEEDED); }

void OnTick()
  {
   QT_KhopYDinh();
   datetime t = (datetime)SeriesInfoInteger(_Symbol, PERIOD_%(khung)s,
                                            SERIES_LASTBAR_DATE);
   if(t == g_qt_nen) return;
   g_qt_nen = t;
   QT_MoiNen();
  }
//+------------------------------------------------------------------+
"""


def sinh_ea_giam_sat(spec: dict, ten: str = "GiamSatViThe",
                     khung: str = "D1", magic: int = 0) -> str:
    """EA doc lap de DE LEN EA khac khi chay that (khong backtest duoc cung nhau)."""
    return EA_GIAM_SAT % {"ten": ten, "khung": khung,
                          "khoi": sinh_khoi(spec, khung=khung, magic=magic)}
