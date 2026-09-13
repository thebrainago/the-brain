//+------------------------------------------------------------------+
//| ea_QuanTriBench.mq5 - BAN DO HO QUAN TRI VI THE
//|
//| Chu du an, SO_DO_HE_THONG.txt: *"Rieng muc nay can chu y vi no la
//| module quan trong trong toan bo he thong... viec su dung ky thuat
//| quan li lenh tot con hon viec co 1 entry tot"* va *"tet thu tung
//| phuong phap quan li lenh khac nhau de xem hieu qua cung nhu ket qua
//| thay doi ra sao"*.
//|
//| ## VI SAO PHAI CO MOT EA RIENG CHO VIEC NAY
//|
//| Duong cu (`de_quan_tri.py`) chen khoi quan tri vao EA NGOAI roi bat/tat.
//| Do la duong dung de tra loi "quan tri co cai thien EA co san khong".
//| No KHONG tra loi duoc "ho quan tri nao manh hon ho nao", vi hai ly do
//| do duoc 13/09/2026:
//|
//|   1. EA ngoai tu dat TP/SL va tu thoat theo tin hieu cua no. Quan tri
//|      khong con CHO de hanh dong. Do 12/09 tren EA Snippets_Breakout:
//|      14/15 luat cho ket qua GIONG HET NHAU den tung so le.
//|   2. Moi EA ngoai co mot engine vao khac nhau, nen chenh lech giua hai
//|      ho quan tri lan voi chenh lech giua hai engine vao.
//|
//| Ban do nay co dinh ENGINE VAO va chi doi HO QUAN TRI. Do la dieu kien
//| toi thieu de cau "ho A manh hon ho B" co nghia.
//|
//| ## MOC SO SANH NAM TRONG CUNG MOT EA
//|
//| `InpHoQT = 0` = chi co luoi an toan (SL cung + tran so nen giu), khong
//| mot lop quan tri nao. Moi ho khac = luoi an toan DO + mot lop. Nen
//| chenh lech doc duoc chi con mot nguyen nhan. Moc phai nam trong chinh
//| EA nay chu khong tinh rieng: cung spread, cung phi qua dem, cung gio
//| khop, cung lich phien.
//|
//| ## LUOI AN TOAN LA BAT BUOC, KHONG PHAI TUY CHON
//|
//| Khong co no thi ho `luoi_dca` va ho `hedge` chay tai khoan ve 0 va moi
//| con so con lai trong bang thanh vo nghia. Lab da do: martingale tren
//| LOT cho DD 99,98% ngay trong mau.
//+------------------------------------------------------------------+
#property copyright "The Brain"
#include <Trade\Trade.mqh>

//--- HO QUAN TRI
#define QT_MOC          0   // chi luoi an toan (moc so sanh)
#define QT_TP_CO_DINH   1   // TP = P1 x ATR
#define QT_TRAILING     2   // trail P1 x ATR, bat dau khi lai > P2 x ATR
#define QT_DAT_HUE      3   // SL -> hoa von khi lai > P2 x ATR
#define QT_HUE_TRAIL    4   // dat hue roi trailing
#define QT_TIA          5   // dong P1 phan tram khi lai > P2 x ATR, con lai hue von
#define QT_HEDGE        6   // khoa nguoc chieu khi lo > P2 x ATR
#define QT_STOP_2_DAU   7   // buy stop + sell stop hai ben, cai nao khop huy cai kia
#define QT_TT_STOP_DOI  8   // vao thi truong + stop doi dien lot x P2
#define QT_LUOI_DCA     9   // nhoi moi P1 x ATR nguoc, TP chung P2 x ATR tu gia TB
#define QT_THOI_GIAN   10   // dong sau P1 nen, bat ke lai lo
#define QT_SO_HO       11

//--- ENGINE VAO (co dinh trong mot luot do)
#define VAO_DONCHIAN    0   // pha dinh/day N nen
#define VAO_DEU_DAN     1   // vao moi N nen, chieu luan phien
#define VAO_QUAY_VE     2   // dong ngoai bien Bollinger thi vao nguoc

input int    InpHoQT      = 0;      // ho quan tri (0..10)
input double InpP1        = 1.0;    // tham so 1 (y nghia theo ho)
input double InpP2        = 1.0;    // tham so 2 (y nghia theo ho)
input int    InpVaoKieu   = VAO_DONCHIAN;
input int    InpVaoN      = 20;     // chu ky engine vao
input double InpLot       = 0.10;
input long   InpMagic     = 26091301;
input int    InpATRKy     = 14;
input double InpSLCung    = 3.0;    // luoi an toan: SL cung, boi ATR
input int    InpGiuToiDa  = 120;    // luoi an toan: tran so nen giu
input int    InpNhoiMax   = 5;      // tran so vi the cho ho luoi/dca
input double InpLoRongPct = 25.0;   // luoi an toan: tran LO TROI, %% von

CTrade   trade;
int      h_atr = INVALID_HANDLE;
int      h_bbt = INVALID_HANDLE, h_bbd = INVALID_HANDLE;
datetime g_nen_cuoi = 0;
int      g_bar_vao  = 0;            // so nen da giu vi the dau tien
int      g_chieu    = 0;            // chieu cua vi the goc: +1 mua, -1 ban
double   g_gia_tot  = 0.0;          // gia tot nhat da cham (cho trailing)
double   g_atr_vao  = 0.0;          // ATR luc vao - DONG BANG, xem ghi chu duoi
int      g_da_tia   = 0;
int      g_da_hedge = 0;
int      g_so_nhoi  = 0;
int      g_nen_dem  = 0;
int      g_phien    = 0;            // luan phien chieu cho VAO_DEU_DAN
bool     g_hedging  = false;
//--- BO DEM CHAN DOAN. Khong phai trang tri: 13/09 ho `tia` ra ket qua Y HET
//--- ho `dat_hue` hai luot lien, va khong cach nao biet la "tia khong co tac
//--- dung" hay "tia khong chay" neu khong dem. In o OnDeinit.
int      g_dem_thu_tia = 0;   // so lan dieu kien tia duoc thoa
int      g_dem_tia_ok  = 0;   // so lan PositionClosePartial tra ve true
int      g_dem_tia_nho = 0;   // so lan bo vi lot khong du
int      g_dem_tia_loi = 0;   // so lan goi that bai
int      g_ma_loi_tia  = 0;

//+------------------------------------------------------------------+
//| ATR PHAI DONG BANG LUC VAO, khong doc lai moi nen.
//|
//| Neu doc lai, thi khi bien dong no ra, nguong "lai > P2 x ATR" tu dong
//| lui ra xa va trailing nha dan - tuc tham so cua ta doi giua chung mot
//| lenh. Hai ho se khac nhau vi ly do do chu khong vi luat cua chung.
//+------------------------------------------------------------------+
double ATR(int s = 1)
  {
   if(h_atr == INVALID_HANDLE) return(0.0);
   double b[];
   if(CopyBuffer(h_atr, 0, s, 1, b) != 1) return(0.0);
   return(b[0]);
  }

double Diem() { return(SymbolInfoDouble(_Symbol, SYMBOL_POINT)); }

//--- Khoang cach toi thieu san cho phep dat SL/TP. Bo qua no thi lenh
//--- `PositionModify` that bai IM LANG va quan tri doc y het "khong lam gi".
double DungToiThieu()
  {
   long mucs = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   return((double)mucs * Diem());
  }

double Chuan(double gia) { return(NormalizeDouble(gia, _Digits)); }

//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetTypeFillingBySymbol(_Symbol);
   h_atr = iATR(_Symbol, PERIOD_CURRENT, InpATRKy);
   h_bbt = iBands(_Symbol, PERIOD_CURRENT, InpVaoN, 0, 2.0, PRICE_CLOSE);
   h_bbd = h_bbt;
   if(h_atr == INVALID_HANDLE) return(INIT_FAILED);

   long che_do = AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   g_hedging = (che_do == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING);
   //--- Ho HEDGE va ho STOP_2_DAU can tai khoan hedging. Tren tai khoan
   //--- netting, lenh nguoc chieu DONG bot vi the thay vi mo khoa - ket qua
   //--- doc duoc nhung no la mot co che KHAC. Tu choi chay con hon tra ve
   //--- mot con so sai ma khong ai biet.
   if(!g_hedging && (InpHoQT == QT_HEDGE || InpHoQT == QT_STOP_2_DAU ||
                     InpHoQT == QT_TT_STOP_DOI))
     {
      Print("CHUA_DO_DUOC: ho ", InpHoQT, " can tai khoan HEDGING, tai khoan nay NETTING");
      return(INIT_FAILED);
     }
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Duyet vi the cua ta
//+------------------------------------------------------------------+
int SoViThe()
  {
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic) n++;
     }
   return(n);
  }

double LaiRong()
  {
   double s = 0.0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      s += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
     }
   return(s);
  }

//--- Gia trung binh co trong so khoi luong, tinh RIENG tung chieu.
double GiaTB(int chieu, double &tong_lot)
  {
   double tv = 0.0, tl = 0.0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      long lo = PositionGetInteger(POSITION_TYPE);
      int c = (lo == POSITION_TYPE_BUY) ? 1 : -1;
      if(c != chieu) continue;
      double v = PositionGetDouble(POSITION_VOLUME);
      tv += PositionGetDouble(POSITION_PRICE_OPEN) * v;
      tl += v;
     }
   tong_lot = tl;
   return(tl > 0 ? tv / tl : 0.0);
  }

void DongHet()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic) trade.PositionClose(tk);
     }
   HuyLenhCho();
  }

void HuyLenhCho()
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tk = OrderGetTicket(i);
      if(tk == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol &&
         OrderGetInteger(ORDER_MAGIC) == InpMagic) trade.OrderDelete(tk);
     }
  }

int SoLenhCho()
  {
   int n = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tk = OrderGetTicket(i);
      if(tk == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol &&
         OrderGetInteger(ORDER_MAGIC) == InpMagic) n++;
     }
   return(n);
  }

//+------------------------------------------------------------------+
//| ENGINE VAO - co dinh trong mot luot do
//+------------------------------------------------------------------+
int TinHieuVao()
  {
   int n = InpVaoN;
   if(InpVaoKieu == VAO_DEU_DAN)
     {
      if(g_nen_dem % n != 0) return(0);
      g_phien++;
      return((g_phien % 2 == 0) ? 1 : -1);
     }
   if(InpVaoKieu == VAO_QUAY_VE)
     {
      double tr[], du[];
      if(CopyBuffer(h_bbt, 1, 1, 1, tr) != 1) return(0);
      if(CopyBuffer(h_bbt, 2, 1, 1, du) != 1) return(0);
      double c = iClose(_Symbol, PERIOD_CURRENT, 1);
      if(c > tr[0]) return(-1);
      if(c < du[0]) return(1);
      return(0);
     }
   //--- VAO_DONCHIAN: pha dinh/day n nen (khong ke nen 1)
   double dinh = -DBL_MAX, day = DBL_MAX;
   for(int i = 2; i <= n + 1; i++)
     {
      double h = iHigh(_Symbol, PERIOD_CURRENT, i);
      double l = iLow(_Symbol, PERIOD_CURRENT, i);
      if(h > dinh) dinh = h;
      if(l < day)  day = l;
     }
   double c1 = iClose(_Symbol, PERIOD_CURRENT, 1);
   if(c1 > dinh) return(1);
   if(c1 < day)  return(-1);
   return(0);
  }

//+------------------------------------------------------------------+
//| MO VI THE GOC theo ho
//+------------------------------------------------------------------+
void MoGoc(int chieu)
  {
   double atr = ATR(1);
   if(atr <= 0) return;
   g_atr_vao = atr;
   g_chieu   = chieu;
   g_bar_vao = 0;
   g_gia_tot = 0.0;
   g_da_tia  = 0;
   g_da_hedge = 0;
   g_so_nhoi = 0;

   double mua = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double ban = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double toi_thieu = MathMax(DungToiThieu(), 2 * Diem());

   //--- HO LENH CHO: khong vao thi truong, dat hai stop hai ben.
   if(InpHoQT == QT_STOP_2_DAU)
     {
      double kc = MathMax(InpP1 * atr, toi_thieu);
      double sl_kc = MathMax(InpP2 * atr, toi_thieu);
      double gmua = Chuan(mua + kc), gban = Chuan(ban - kc);
      trade.BuyStop(InpLot, gmua, _Symbol, Chuan(gmua - sl_kc), 0,
                    ORDER_TIME_GTC, 0);
      trade.SellStop(InpLot, gban, _Symbol, Chuan(gban + sl_kc), 0,
                     ORDER_TIME_GTC, 0);
      return;
     }

   double sl_cung = MathMax(InpSLCung * atr, toi_thieu);
   double sl = (chieu > 0) ? Chuan(mua - sl_cung) : Chuan(ban + sl_cung);
   double tp = 0.0;
   if(InpHoQT == QT_TP_CO_DINH)
     {
      double tp_kc = MathMax(InpP1 * atr, toi_thieu);
      tp = (chieu > 0) ? Chuan(mua + tp_kc) : Chuan(ban - tp_kc);
     }
   if(InpHoQT == QT_LUOI_DCA)
     {
      //--- Luoi khong dung SL tung lenh: TP chung tinh tu gia trung binh,
      //--- luoi an toan la TRAN SO NHOI + tran so nen giu.
      sl = 0.0;
     }

   bool ok = (chieu > 0) ? trade.Buy(InpLot, _Symbol, 0, sl, tp)
                         : trade.Sell(InpLot, _Symbol, 0, sl, tp);
   if(!ok) return;

   //--- HO THI TRUONG + STOP DOI DIEN: dat ngay lenh cho nguoc chieu.
   if(InpHoQT == QT_TT_STOP_DOI)
     {
      double kc = MathMax(InpP1 * atr, toi_thieu);
      double lot2 = NormalizeDouble(InpLot * MathMax(InpP2, 0.1), 2);
      double b = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
      if(b > 0) lot2 = MathMax(b, MathRound(lot2 / b) * b);
      if(chieu > 0)
        {
         double g = Chuan(ban - kc);
         trade.SellStop(lot2, g, _Symbol, 0, 0, ORDER_TIME_GTC, 0);
        }
      else
        {
         double g = Chuan(mua + kc);
         trade.BuyStop(lot2, g, _Symbol, 0, 0, ORDER_TIME_GTC, 0);
        }
     }
  }

//+------------------------------------------------------------------+
//| QUAN TRI - chay moi nen khi dang co vi the
//+------------------------------------------------------------------+
void QuanTri()
  {
   double atr = (g_atr_vao > 0 ? g_atr_vao : ATR(1));
   if(atr <= 0) return;
   double toi_thieu = MathMax(DungToiThieu(), 2 * Diem());
   double mua = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double ban = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   //--- HO LUOI/DCA: nhoi theo khoang cach, TP chung tu gia trung binh.
   if(InpHoQT == QT_LUOI_DCA)
     {
      double tong_lot = 0.0;
      double gtb = GiaTB(g_chieu, tong_lot);
      if(tong_lot <= 0) return;
      double gia_hien = (g_chieu > 0) ? ban : mua;
      double lai_kc = (gia_hien - gtb) * g_chieu;
      if(lai_kc >= MathMax(InpP2 * atr, toi_thieu)) { DongHet(); return; }
      double nguoc = -lai_kc;
      if(nguoc >= MathMax(InpP1 * atr, toi_thieu) * (g_so_nhoi + 1) &&
         g_so_nhoi < InpNhoiMax - 1)
        {
         bool ok = (g_chieu > 0) ? trade.Buy(InpLot, _Symbol)
                                 : trade.Sell(InpLot, _Symbol);
         if(ok) g_so_nhoi++;
        }
      return;
     }

   //--- HO HEDGE: khoa nguoc chieu khi lo vuot nguong, thao khi ve hoa.
   if(InpHoQT == QT_HEDGE)
     {
      double tong_lot = 0.0;
      double gtb = GiaTB(g_chieu, tong_lot);
      if(tong_lot <= 0) return;
      double gia_hien = (g_chieu > 0) ? ban : mua;
      double lai_kc = (gia_hien - gtb) * g_chieu;
      if(g_da_hedge == 0 && -lai_kc >= MathMax(InpP2 * atr, toi_thieu))
        {
         double lot2 = NormalizeDouble(InpLot * MathMax(InpP1, 0.1), 2);
         double b = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
         if(b > 0) lot2 = MathMax(b, MathRound(lot2 / b) * b);
         bool ok = (g_chieu > 0) ? trade.Sell(lot2, _Symbol)
                                 : trade.Buy(lot2, _Symbol);
         if(ok) g_da_hedge = 1;
        }
      //--- Thao khoa khi CA RO ve duong. Do la dinh nghia cua "recovery
      //--- zone": khong phai cuu tung chan ma cuu tong.
      if(g_da_hedge == 1 && LaiRong() > 0) DongHet();
      return;
     }

   //--- CAC HO MOT VI THE
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;

      long lo = PositionGetInteger(POSITION_TYPE);
      int  c  = (lo == POSITION_TYPE_BUY) ? 1 : -1;
      double vao = PositionGetDouble(POSITION_PRICE_OPEN);
      double sl_ht = PositionGetDouble(POSITION_SL);
      double tp_ht = PositionGetDouble(POSITION_TP);
      double gia = (c > 0) ? ban : mua;
      double lai_kc = (gia - vao) * c;

      if(g_gia_tot == 0.0) g_gia_tot = gia;
      if((gia - g_gia_tot) * c > 0) g_gia_tot = gia;

      double sl_moi = sl_ht;

      if(InpHoQT == QT_DAT_HUE || InpHoQT == QT_HUE_TRAIL || InpHoQT == QT_TIA)
        {
         if(lai_kc >= MathMax(InpP2 * atr, toi_thieu))
           {
            double hue = Chuan(vao + c * toi_thieu);
            if(sl_ht == 0.0 || (hue - sl_ht) * c > 0) sl_moi = hue;
           }
        }
      if(InpHoQT == QT_TRAILING || InpHoQT == QT_HUE_TRAIL)
        {
         if(lai_kc >= MathMax(InpP2 * atr, toi_thieu))
           {
            double kc = MathMax(InpP1 * atr, toi_thieu);
            double tr = Chuan(g_gia_tot - c * kc);
            if(sl_ht == 0.0 || (tr - sl_ht) * c > 0) sl_moi = tr;
           }
        }
      if(InpHoQT == QT_TIA && g_da_tia == 0)
        {
         if(lai_kc >= MathMax(InpP2 * atr, toi_thieu))
           {
            double v = PositionGetDouble(POSITION_VOLUME);
            double b = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
            double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
            //--- Ty le cat tran o 0,8 chu khong 0,9. Do 13/09: voi lot 1,00,
            //--- vmin 0,10 va ty le 0,9 thi phan CON LAI = 1,00 - 0,90 =
            //--- 0,09999999... < vmin trong so hoc dau phay dong, nen lenh tia
            //--- bi bo va ho `tia` chay Y HET ho `dat_hue`. Bang ket qua khi do
            //--- doc nhu "tia khong co tac dung" - trong khi that ra o tham so
            //--- do tia KHONG BAO GIO DUOC GOI.
            double ty = MathMin(MathMax(InpP1, 0.1), 0.8);
            double tia = NormalizeDouble(v * ty, 2);
            if(b > 0) tia = MathFloor(tia / b + 1e-8) * b;
            //--- `PositionClosePartial` that bai IM LANG khi phan dong nho hon
            //--- lot toi thieu, HOAC khi phan CON LAI nho hon lot toi thieu.
            //--- Ca hai deu doc y het "tia khong co tac dung".
            g_dem_thu_tia++;
            if(tia >= vmin - 1e-8 && (v - tia) >= vmin - 1e-8)
              {
               if(trade.PositionClosePartial(tk, tia))
                 { g_da_tia = 1; g_dem_tia_ok++; }
               else
                 { g_dem_tia_loi++; g_ma_loi_tia = (int)trade.ResultRetcode(); }
              }
            else
              {
               g_da_tia = -1;   // khong tia duoc - ghi lai, dung im lang
               g_dem_tia_nho++;
              }
           }
        }

      if(sl_moi != sl_ht && sl_moi != 0.0)
         trade.PositionModify(tk, sl_moi, tp_ht);
     }
  }

//+------------------------------------------------------------------+
//| BAO CAO CHAN DOAN. Mot ho "khong co tac dung" va mot ho "khong chay"
//| doc y het nhau trong bang ket qua; chi bo dem phan biet duoc.
//+------------------------------------------------------------------+
void OnDeinit(const int ly_do)
  {
   if(InpHoQT == QT_TIA)
      PrintFormat("QT_TIA: thu=%d ok=%d lot_khong_du=%d loi=%d ma_loi=%d "
                  "vmin=%.2f vstep=%.2f lot=%.2f",
                  g_dem_thu_tia, g_dem_tia_ok, g_dem_tia_nho, g_dem_tia_loi,
                  g_ma_loi_tia, SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN),
                  SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP), InpLot);
  }

//+------------------------------------------------------------------+
void OnTick()
  {
   datetime t = (datetime)SeriesInfoInteger(_Symbol, PERIOD_CURRENT,
                                            SERIES_LASTBAR_DATE);
   if(t == g_nen_cuoi) return;
   g_nen_cuoi = t;
   g_nen_dem++;

   //--- Chi hanh dong khi san dang mo. Nen ngoai phien thi lenh tra
   //--- "Market closed" va bao cao ghi 0 lenh - doc y het mot he khong
   //--- bao gio vao lenh.
   if((ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE)
      != SYMBOL_TRADE_MODE_FULL) return;

   int n_vt = SoViThe();

   if(n_vt > 0)
     {
      g_bar_vao++;
      //--- LUOI AN TOAN, ap cho MOI ho khong tru ho nao.
      if(g_bar_vao >= InpGiuToiDa) { DongHet(); g_bar_vao = 0; return; }
      //--- TANG 3: tran LO TROI. Duy nhat tang nay cham duoc ho `luoi_dca`,
      //--- vi ho do co y khong dat SL tung lenh.
      if(InpLoRongPct > 0.0)
        {
         double von = AccountInfoDouble(ACCOUNT_BALANCE);
         if(von > 0.0 && LaiRong() < -von * InpLoRongPct / 100.0)
           { DongHet(); g_bar_vao = 0; return; }
        }
      if(InpHoQT == QT_THOI_GIAN && g_bar_vao >= (int)MathMax(InpP1, 1.0))
        { DongHet(); g_bar_vao = 0; return; }
      //--- Mot chan khop thi huy chan con lai.
      if(InpHoQT == QT_STOP_2_DAU && SoLenhCho() > 0) HuyLenhCho();
      QuanTri();
      return;
     }

   //--- Khong con vi the: don lenh cho treo lai (tru ho stop 2 dau dang cho).
   if(SoLenhCho() > 0)
     {
      if(InpHoQT == QT_STOP_2_DAU)
        {
         g_bar_vao++;
         //--- Lenh cho khong khop trong `InpGiuToiDa` nen thi huy, khong de
         //--- no treo mai lam moi tin hieu sau bi bo qua.
         if(g_bar_vao >= InpGiuToiDa) { HuyLenhCho(); g_bar_vao = 0; }
         return;
        }
      HuyLenhCho();
     }

   int th = TinHieuVao();
   if(th != 0) MoGoc(th);
  }
//+------------------------------------------------------------------+
