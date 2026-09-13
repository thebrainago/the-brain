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

## BON BAY DA SAP THAT, DA BIT TRONG MA SINH RA

1. **Hanh dong sinh Y DINH, khong dat lenh thang.** Nen khung tin hieu doi luc
   00:00 nam NGOAI phien CFD -> dat thang o do thi "Market closed", khong dau
   vet [[tester-cfd-chi-so-3-bay]]. Moi lenh di qua `QT_KhopYDinh()`.
2. **`PositionClosePartial` duoi min lot that bai IM LANG** -> `QT_DongMotPhan`
   kiem `SYMBOL_VOLUME_MIN` va **bao ra bien dem** thay vi im.
3. **Nhoi khong tran = chay tai khoan** (do 07/09: lot_x 1,5 -> DD 99,98% ngay
   trong mau). `sinh_khoi` **TU CHOI** spec co nhoi ma khong co tran.
4. **Bang NHIEU luat (`sinh_khoi_nhieu`) im lang ve 0 neu bo qua `sang_atr`.**
   Do 11/09: `_atr0` cu tra 0.0 cho MOI dict khac `{'atr': x}`, va 141/146 gia
   tri trong kho la don vi `pip` - ca 14 luat sinh ra GIONG HET moc (1759 lenh
   / -108,76 / DD 1,3121), bang tester doc nham thanh "AM". Tu 12/09:
   `sinh_khoi_nhieu` **BAT BUOC** `atr`/`gia_diem` that (khong nhan mac dinh,
   tu quy doi bang `quan_tri_dsl.sang_atr` truoc khi rut so) va **TU CHOI**
   qua cong `kiem_bang_luat` neu mot luat toan 0 hoac moi luat giong het nhau.
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


NHIEU = r"""
//============ KHO QUAN TRI: %(k)d luat, chon bang QT_MaLuat ================
//  Sinh tu nhan/dich_mq5_qtvt.py. KHONG SUA TAY.
//  QT_MaLuat = 0 la MOC: tat het quan tri. Bat buoc co, va phai nam trong
//  CUNG lan chay - so hai lan boot khac nhau la so hai thu khac nhau.
input int    QT_MaLuat = 0;   // 0..%(max)d
input long   QT_Magic  = %(magic)d;
input double QT_LotGoc = %(lot_goc)s;

double QT_A_DatHue[], QT_A_TrKhoang[], QT_A_TrBatDau[], QT_A_TiaTu[];
double QT_A_TiaTy[], QT_A_NhoiKh[], QT_A_NhoiLx[], QT_A_ChotTien[];
double QT_A_ChotAtr[], QT_A_CatHoa[], QT_A_TranLot[], QT_A_TranLo[];
int    QT_A_NhoiChieu[], QT_A_TranVT[], QT_A_TranTuoi[];

double QT_DatHue, QT_TrailKhoang, QT_TrailBatDau, QT_TiaTu, QT_TiaTyLe;
double QT_NhoiKhoang, QT_NhoiLotX, QT_ChotRoTien, QT_ChotRoAtr, QT_CatHoaTu;
double QT_TranLot, QT_TranLoTien;
int    QT_NhoiChieu, QT_NhoiMax, QT_TranViThe, QT_TranTuoiGio;

void QT_NapBang()
  {
%(nap)s
  }

void QT_ChonLuat(int k)
  {
   if(k < 0 || k >= %(k)d) k = 0;
   QT_DatHue      = QT_A_DatHue[k];
   QT_TrailKhoang = QT_A_TrKhoang[k];
   QT_TrailBatDau = QT_A_TrBatDau[k];
   QT_TiaTu       = QT_A_TiaTu[k];
   QT_TiaTyLe     = QT_A_TiaTy[k];
   QT_NhoiKhoang  = QT_A_NhoiKh[k];
   QT_NhoiLotX    = QT_A_NhoiLx[k];
   QT_NhoiChieu   = QT_A_NhoiChieu[k];
   QT_ChotRoTien  = QT_A_ChotTien[k];
   QT_ChotRoAtr   = QT_A_ChotAtr[k];
   QT_CatHoaTu    = QT_A_CatHoa[k];
   QT_TranViThe   = QT_A_TranVT[k];
   QT_TranLot     = QT_A_TranLot[k];
   QT_TranLoTien  = QT_A_TranLo[k];
   QT_TranTuoiGio = QT_A_TranTuoi[k];
   QT_NhoiMax     = QT_TranViThe;
  }
"""


def _g(x, *duong, md=0.0):
    nut = x
    for k in duong:
        nut = (nut or {}).get(k) if isinstance(nut, dict) else None
    return nut if nut is not None else md


def _atr0(x, *duong):
    """Doc mot truong khoang cach cua bang NHIEU luat - PHAI da qua `sang_atr`.

    Loi goc 12/09: ban cu tra 0.0 IM LANG cho moi dict khac `{'atr': x}` - tuc
    141/146 khai bao trong kho (don vi 'pip') roi thanh 0 het, va ca bang 14
    luat sinh ra GIONG HET moc (1759 lenh / -108,76 / DD 1,3121). Nay: thieu
    truong (path rong, x.get(...) tra None) van la 0.0 HOP LE (luat khong dung
    truong do); nhung CO dict o do ma khong phai `{'atr': x}` (vd van con
    `{'pip': 10}` chua quy doi) la loi va phai NEM ra, khong duoc lang le hoa 0.
    """
    v = _g(x, *duong)
    if isinstance(v, dict):
        if "atr" in v:
            return _atr(v, 0)
        raise KhongDichDuoc(
            "CHUA_DO_DUOC: truong %s con don vi chua quy ve ATR: %s - goi "
            "quan_tri_dsl.sang_atr(spec, atr, gia_diem) TRUOC khi dua vao "
            "sinh_khoi_nhieu" % (".".join(duong), v))
    return 0.0


#: Cac cot cua bang NHIEU luat: ten mang MQL5 -> (ham rut so tu 1 spec, dinh dang).
#: Tach thanh hang so de dung CHUNG cho ca sinh ma (`_hang`) lan cong kiem
#: "bang toan 0" (`kiem_bang_luat`) - hai duong doc phai thay CUNG mot du lieu.
_COT_BANG_NHIEU = (
    ("QT_A_DatHue",    lambda x: _atr0(x, "dat_hue", "tu"), "%.4f"),
    ("QT_A_TrKhoang",  lambda x: _atr0(x, "trailing", "khoang"), "%.4f"),
    ("QT_A_TrBatDau",  lambda x: _atr0(x, "trailing", "bat_dau"), "%.4f"),
    ("QT_A_TiaTu",     lambda x: _atr0(x, "tia", "tu"), "%.4f"),
    ("QT_A_TiaTy",     lambda x: float(_g(x, "tia", "ty_le", md=0.5)), "%.4f"),
    ("QT_A_NhoiKh",    lambda x: _atr0(x, "nhoi", "khoang"), "%.4f"),
    ("QT_A_NhoiLx",    lambda x: float(_g(x, "nhoi", "lot_x", md=1.0)), "%.4f"),
    ("QT_A_NhoiChieu", lambda x: 1 if x.get("nhoi") else 0, "%d"),
    ("QT_A_ChotTien",  lambda x: _so(_g(x, "chot", "tien"), 0), "%.4f"),
    ("QT_A_ChotAtr",   lambda x: _atr0(x, "chot", "muc"), "%.4f"),
    ("QT_A_CatHoa",    lambda x: _atr0(x, "cat_hoa", "tu"), "%.4f"),
    ("QT_A_TranVT",    lambda x: int(_g(x, "chan", "so_vi_the_toi_da", md=0)), "%d"),
    ("QT_A_TranLot",   lambda x: float(_g(x, "chan", "lot_toi_da", md=0)), "%.4f"),
    ("QT_A_TranLo",    lambda x: _so(_g(x, "chan", "lo_toi_da"), 0), "%.4f"),
    ("QT_A_TranTuoi",  lambda x: int(_so(_g(x, "chan", "tuoi_gio_toi_da"), 0)), "%d"),
)


#: Cot LOAI TRU khoi phep thu "toan 0": day la ty le/he so co GIA TRI MAC DINH
#: khac 0 (`ty_le=0.5`, `lot_x=1.0`) du luat co dung co che tuong ung hay khong
#: - tu chung KHONG phai bang chung quan tri "cham" duoc vi the nao. Neu tinh
#: ca hai cot nay thi moi hang deu co gia tri >0, va cong khong bao gio bat
#: duoc mot luat rong that (da do 12/09 khi viet test: luat chi co 'chan.so_vi_
#: the_toi_da=0' van "any(h)=True" vi TiaTy/NhoiLx mac dinh, ket qua la cong MU).
_COT_MAC_DINH_KHAC_0 = ("QT_A_TiaTy", "QT_A_NhoiLx")


def kiem_bang_luat(gia_tri: "dict[str, list[float]]") -> None:
    """Cong (2): tu choi sinh file neu bang luat la 'bo phan im lang'.

    Do 12/09: khi khau quy doi don vi bi bo qua, TOAN BO 14 luat ra CUNG mot bo
    tham so (toan 0.0) - tester bao "14/15 luat GIONG HET nhau" va dieu do bi
    doc NHAM thanh ket luan khoa hoc "AM" thay vi mot loi ky thuat o khau sinh
    bang. Cong nay chan tai NGUON, truoc khi ghi bat ky file .mq5 nao:

        1. mot luat (khac luat 0 - MOC tat quan tri, luon dung la toan 0) co
           TOAN BO cot KICH HOAT bang 0 -> no khong the cham vao vi the nao;
        2. moi luat cho CUNG mot bo tham so -> quy doi da chay nhung khong
           luat nao khac luat nao (dau hieu ATR/gia_diem dau vao sai).

    Ca hai deu la CHUA_DO_DUOC (khau do hong), khong phai AM (he thong te).
    """
    ten_cot = list(gia_tri)
    if not ten_cot:
        return
    n = len(gia_tri[ten_cot[0]])
    cot_kich_hoat = [c for c in ten_cot if c not in _COT_MAC_DINH_KHAC_0]
    hang_kich_hoat = [tuple(gia_tri[c][i] for c in cot_kich_hoat) for i in range(1, n)]
    hang_day_du = [tuple(gia_tri[c][i] for c in ten_cot) for i in range(1, n)]
    if not hang_kich_hoat:
        return
    toan_0 = [i for i, h in enumerate(hang_kich_hoat, start=1) if not any(h)]
    if toan_0:
        raise KhongDichDuoc(
            "CHUA_DO_DUOC: bang luat toan 0 - luat thu %s khong co tham so "
            "kich hoat nao khac 0 sau khi quy ATR, quan tri se KHONG cham vao "
            "vi the nao (kiem lai atr/gia_diem truyen vao sinh_khoi_nhieu)" % toan_0)
    if len(set(hang_day_du)) == 1:
        raise KhongDichDuoc(
            "CHUA_DO_DUOC: bang luat toan 0 - tat ca %d luat cho CUNG mot bo "
            "tham so, khong luat nao khac luat nao sau khi quy ATR (kiem lai "
            "atr/gia_diem dau vao, hoac kho specs dau vao bi trung)" % len(hang_day_du))


def sinh_khoi_nhieu(specs: list[dict], khung: str = "D1", magic: int = 0,
                    lot_goc: float = 0.1, atr: float = None,
                    gia_diem: float = 0.01) -> tuple[str, list[dict]]:
    """K luat quan tri trong MOT EA, chon bang `QT_MaLuat`. Tra (ma, luat da nap).

    Vi sao gop: mot luot tester ton ~130 giay boot va gan nhu 0 giay tinh, nen
    **them pass la mien phi con them LAN CHAY moi dat**
    [[tester-nhoi-het-vao-mot-lan-boot]]. K luat x 1 lan boot thay vi K lan.

    **Luat 0 LUON la moc tat het quan tri**, va no nam trong CUNG lan chay - so
    voi moc cua mot lan boot khac la so hai thu khac nhau.

    `atr`/`gia_diem` LA BAT BUOC va phai do tren DU LIEU THAT cua symbol+khung
    se chay (vd `chuoi_quan_tri._atr_cua`) - **khong duoc doan/mac dinh**. Do
    12/09: goi ham nay ma khong quy doi don vi truoc lam ca 14 luat GIONG HET
    moc [[cong-pass-phai-hieu-chuan-hai-chieu]].
    """
    if not (isinstance(atr, (int, float)) and atr > 0):
        raise KhongDichDuoc(
            "CHUA_DO_DUOC: thieu atr thuc do (nhan %r) - goi voi atr>0 do tren "
            "du lieu that cua symbol+khung se chay, khong duoc mac dinh 0" % (atr,))
    from . import quan_tri_dsl as QD
    dat = [{"ten": "__tat_quan_tri__", "lop": "moc"}]
    for s in specs:
        nh = s.get("nhoi") or {}
        chan = s.get("chan") or {}
        if nh and not (chan.get("so_vi_the_toi_da") or chan.get("lot_toi_da")):
            continue          # nhoi khong tran = cong thuc chay tai khoan
        dat.append(QD.sang_atr(s, atr, gia_diem))
    if len(dat) < 2:
        raise KhongDichDuoc("khong luat nao dich duoc")

    def _hang(ten, gia, dinh="%.4f"):
        d = ["   ArrayResize(%s, %d);" % (ten, len(gia))]
        for i, v in enumerate(gia):
            d.append("   %s[%d] = %s;" % (ten, i, dinh % v))
        return "\n".join(d) + "\n"

    gia_tri = {ten: [lay(x) for x in dat] for ten, lay, _ in _COT_BANG_NHIEU}
    kiem_bang_luat(gia_tri)          # cong (2): tu choi neu bang la "im lang"

    nap = "".join(_hang(ten, gia_tri[ten], dinh) for ten, _, dinh in _COT_BANG_NHIEU)
    ma = NHIEU % {"k": len(dat), "max": len(dat) - 1, "magic": magic,
                  "lot_goc": "%.2f" % lot_goc, "nap": nap}
    than = KHOI % {"ten": "kho gop", "lop": "gop", "luat": "gop", "khung": khung,
                   "magic": magic, "dat_hue": "0", "tr_khoang": "0",
                   "tr_batdau": "0", "tia_tu": "0", "tia_ty": "0",
                   "nhoi_khoang": "0", "nhoi_lotx": "1", "nhoi_max": 0,
                   "nhoi_chieu": 0, "chot_tien": "0", "chot_atr": "0",
                   "cat_hoa": "0", "hedge_tu": "0", "hedge_lotx": "1",
                   "tran_vt": 0, "tran_lot": "0", "tran_lo": "0",
                   "tran_tuoi": 0, "lot_goc": "%.2f" % lot_goc}
    # Bo cac dong `input` cua ban MOT luat: o ban gop chung da thanh BANG.
    than = "\n".join(d for d in than.splitlines() if not d.startswith("input "))
    than = than.replace("void QT_Khoi()", "void QT_KhoiThat()")
    ma += than + """
void QT_Khoi()
  {
   QT_KhoiThat();
   QT_NapBang();
   QT_ChonLuat(QT_MaLuat);
  }
"""
    return ma, dat
