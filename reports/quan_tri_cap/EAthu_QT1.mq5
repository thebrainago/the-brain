#property copyright "x"

#include <Trade\Trade.mqh>
CTrade qt_trade;

//=================== QUAN TRI VI THE: AAPL_Pro.mq5 ======================
//  Sinh tu nhan/dich_mq5_qtvt.py. KHONG SUA TAY.
//  lop = ro | luat = trailing+chot+chan
input long   QT_Magic      = 0;   // 0 = quan ly MOI vi the cua symbol
input double QT_DatHue     = 0.0000; // >0: dua SL ve entry sau k x ATR lai
input double QT_TrailKhoang= 0.0040;
input double QT_TrailBatDau= 0.0000;
input double QT_TiaTu      = 0.0000;  // >0: dong mot phan o k x ATR lai
input double QT_TiaTyLe    = 0.50;
input double QT_NhoiKhoang = 0.0000;
input double QT_NhoiLotX   = 1.00;
input int    QT_NhoiMax    = 2;
input int    QT_NhoiChieu  = 0; // 1 nhoi khi AM · 2 khi DUONG · 0 tat
input double QT_ChotRoTien = 0.00;  // >0: dong ro khi tong lai >= X USD
input double QT_ChotRoAtr  = 0.0269;
input double QT_CatHoaTu   = 0.0000;    // >0: dong cap lai+lo khi tong >=0
input double QT_HedgeTu    = 0.0000;
input double QT_HedgeLotX  = 1.00;
input int    QT_TranViThe  = 2;
input double QT_TranLot    = 0.00;
input double QT_TranLoTien = 0.00;    // >0: dong het khi lo ro >= X USD
input int    QT_TranTuoiGio= 0;
input double QT_LotGoc     = 0.10;

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
   g_qt_atr = iATR(_Symbol, PERIOD_D1, 14);
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


datetime g_qt_nen_de = 0;
void QT_DeQuanTri()
  {
   QT_KhopYDinh();
   datetime t = (datetime)SeriesInfoInteger(_Symbol, PERIOD_D1,
                                            SERIES_LASTBAR_DATE);
   if(t == g_qt_nen_de) return;
   g_qt_nen_de = t;
   QT_MoiNen();
  }

int OnInit()
  {
   QT_Khoi(); QT_NapBang(); QT_ChonLuat(QT_MaLuat);
   return(INIT_SUCCEEDED);
  }

void OnTick()
{
   QT_DeQuanTri();

   int a=1;
}
