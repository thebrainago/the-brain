//+------------------------------------------------------------------+
//| GhepHe - SINH TU DONG boi nhan/dich_mq5_ghep.py. KHONG SUA TAY.
//| 3 co che chay DONG THOI, moi co che mot magic rieng.
//+------------------------------------------------------------------+
#property copyright "The Brain"
#include <Trade\Trade.mqh>

#define N_SLOT 3
#define KHUNG PERIOD_D1

input double InpLot0  = 0.10;    // __mua_giu__
input double InpLot1  = 0.10;    // mean_reversion_z5
input double InpLot2  = 0.10;    // quantora_ma_dashboard_sell
input long   InpMagic = 26090701;
input int    InpGhi   = 0;            // 1 = ghi duong von tung nen ra CSV
input string InpTep   = "GHEP_VON.csv";

int h_ma0 = INVALID_HANDLE;
int h_ma1 = INVALID_HANDLE;
int h_ma2 = INVALID_HANDLE;
int h_ma3 = INVALID_HANDLE;

CTrade   trade;
datetime g_nen_cuoi = 0;
int      g_bar_vao[N_SLOT];
int      g_y_dinh[N_SLOT];
double   g_thuc[N_SLOT];           // lai da chot cua rieng slot
double   g_lot[N_SLOT];
int      g_quet = 0;               // so deal da cong vao g_thuc
int      g_tep  = INVALID_HANDLE;

double Chi(int h, int s)
  {
   if(h == INVALID_HANDLE) return(0.0);
   double b[];
   if(CopyBuffer(h, 0, s, 1, b) != 1) return(0.0);
   return(b[0]);
  }

double F1(int s)
  {
   return(iHigh(_Symbol, KHUNG, s+0));
  }

double F2(int s)
  {
   return(iLow(_Symbol, KHUNG, s+0));
  }

double F3(int s)
  {
   return(iClose(_Symbol, KHUNG, s+0));
  }

double F4(int s)
  {
   double v[]; ArrayResize(v, 5);
   for(int i = 0; i < 5; i++) v[i] = F3(s+i);
   double t=0; for(int i=0;i<5;i++) t+=v[i]; double m=t/5.0;
   double q=0; for(int i=0;i<5;i++) q+=(v[i]-m)*(v[i]-m);
   double sd = MathSqrt(q/5.0);
   if(sd <= 0.0) return(0.0);
   return((v[0]-m)/sd);
  }

double F5(int s)
  {
   return(-1);
  }

double F6(int s)
  {
   return(iClose(_Symbol, KHUNG, s+0));
  }

double F7(int s)
  {
   double v[]; ArrayResize(v, 5);
   for(int i = 0; i < 5; i++) v[i] = F6(s+i);
   double t=0; for(int i=0;i<5;i++) t+=v[i]; double m=t/5.0;
   double q=0; for(int i=0;i<5;i++) q+=(v[i]-m)*(v[i]-m);
   double sd = MathSqrt(q/5.0);
   if(sd <= 0.0) return(0.0);
   return((v[0]-m)/sd);
  }

double F8(int s)
  {
   return(-1);
  }

double F9(int s)
  {
   return(iClose(_Symbol, KHUNG, s+0));
  }

double F10(int s)
  {
   return(Chi(h_ma0, s));
  }

double F11(int s)
  {
   return(iClose(_Symbol, KHUNG, s+0));
  }

double F12(int s)
  {
   return(Chi(h_ma1, s));
  }

double F13(int s)
  {
   return(iClose(_Symbol, KHUNG, s+0));
  }

double F14(int s)
  {
   return(Chi(h_ma2, s));
  }

double F15(int s)
  {
   return(iClose(_Symbol, KHUNG, s+0));
  }

double F16(int s)
  {
   return(Chi(h_ma3, s));
  }


//--- vao/ra cua tung slot
bool VAO0(int s) { return((F1(s) >= F2(s))); }
bool RA0(int s)  { return(false); }
bool VAO1(int s) { return((F4(s) < F5(s))); }
bool RA1(int s)  { return((F7(s) >= F8(s))); }
bool VAO2(int s) { return((F9(s) <= F10(s)) && (F11(s) <= F12(s)) && (F13(s) <= F14(s)) && (F15(s) <= F16(s))); }
bool RA2(int s)  { return(false); }

bool CoVao(int k, int s)
  {
   switch(k)
     {
      case 0: return(VAO0(s));
      case 1: return(VAO1(s));
      case 2: return(VAO2(s));
     }
   return(false);
  }

bool CoRa(int k, int s)
  {
   switch(k)
     {
      case 0: return(RA0(s));
      case 1: return(RA1(s));
      case 2: return(RA2(s));
     }
   return(false);
  }

int Chieu(int k) { switch(k) { case 0: return(1); case 1: return(1); case 2: return(-1); } return(1); }
int Giu(int k)   { switch(k) { case 0: return(500); case 1: return(500); case 2: return(1); } return(1); }
bool CoDieuKienRa(int k) { switch(k) { case 0: return(false); case 1: return(true); case 2: return(false); } return(false); }

//+------------------------------------------------------------------+
int OnInit()
  {
   if((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE)
      != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      Print("DUNG LAI: tai khoan KHONG phai hedging - hai chieu se triet tieu.");
      return(INIT_FAILED);
     }
   trade.SetTypeFillingBySymbol(_Symbol);
   g_lot[0] = InpLot0;
   g_lot[1] = InpLot1;
   g_lot[2] = InpLot2;
   for(int i = 0; i < N_SLOT; i++)
     { g_bar_vao[i] = 0; g_y_dinh[i] = 0; g_thuc[i] = 0.0; }
   h_ma0 = iMA(_Symbol, KHUNG, 20, 0, MODE_EMA, PRICE_CLOSE);
   h_ma1 = iMA(_Symbol, KHUNG, 50, 0, MODE_EMA, PRICE_CLOSE);
   h_ma2 = iMA(_Symbol, KHUNG, 100, 0, MODE_EMA, PRICE_CLOSE);
   h_ma3 = iMA(_Symbol, KHUNG, 200, 0, MODE_EMA, PRICE_CLOSE);
   if(InpGhi == 1)
     {
      g_tep = FileOpen(InpTep, FILE_WRITE | FILE_CSV | FILE_COMMON, ',');
      if(g_tep != INVALID_HANDLE)
        {
         string d = "thoi_gian,gia";
         for(int i = 0; i < N_SLOT; i++)
            d += ",von" + IntegerToString(i) + ",mo" + IntegerToString(i);
         FileWrite(g_tep, d);
        }
     }
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int ly_do)
  {
   if(g_tep != INVALID_HANDLE) { FileClose(g_tep); g_tep = INVALID_HANDLE; }
  }

bool DangMo(int slot)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic + slot) return(true);
     }
   return(false);
  }

void DongSlot(int slot)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic + slot)
         trade.PositionClose(tk);
     }
  }

double NoiTai(int slot)
  {
   double v = 0.0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic + slot) continue;
      v += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
     }
   return(v);
  }

//--- Cong lai DA CHOT vao dung slot. Quet TANG DAN: deal chi duoc them vao
//--- cuoi lich su nen chi so da quet khong bao gio lech.
void CapNhatThuc()
  {
   if(!HistorySelect(0, TimeCurrent())) return;
   int tong = HistoryDealsTotal();
   for(int i = g_quet; i < tong; i++)
     {
      ulong tk = HistoryDealGetTicket(i);
      if(tk == 0) continue;
      int s = (int)(HistoryDealGetInteger(tk, DEAL_MAGIC) - InpMagic);
      if(s < 0 || s >= N_SLOT) continue;
      g_thuc[s] += HistoryDealGetDouble(tk, DEAL_PROFIT)
                 + HistoryDealGetDouble(tk, DEAL_SWAP)
                 + HistoryDealGetDouble(tk, DEAL_COMMISSION);
     }
   g_quet = tong;
  }

//--- Khop y dinh o nen dau tien CO THE giao dich: nen khung tin hieu doi luc
//--- 00:00 nam NGOAI phien cua CFD chi so, hanh dong ngay tai do thi moi lenh
//--- tra "Market closed" va bao cao ghi 0 lenh.
void KhopYDinh(int slot)
  {
   if(g_y_dinh[slot] == 0 || g_lot[slot] <= 0.0) return;
   if((ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE)
      != SYMBOL_TRADE_MODE_FULL) return;
   trade.SetExpertMagicNumber(InpMagic + slot);
   if(g_y_dinh[slot] < 0)
     {
      if(!DangMo(slot)) { g_y_dinh[slot] = 0; return; }
      DongSlot(slot);
      if(!DangMo(slot)) { g_bar_vao[slot] = 0; g_y_dinh[slot] = 0; }
      return;
     }
   if(DangMo(slot)) { g_y_dinh[slot] = 0; return; }
   bool ok = (Chieu(slot) > 0) ? trade.Buy(g_lot[slot], _Symbol)
                               : trade.Sell(g_lot[slot], _Symbol);
   if(ok) { g_bar_vao[slot] = 0; g_y_dinh[slot] = 0; }
  }

void OnTick()
  {
   for(int i = 0; i < N_SLOT; i++) KhopYDinh(i);

   datetime t = (datetime)SeriesInfoInteger(_Symbol, KHUNG, SERIES_LASTBAR_DATE);
   if(t == g_nen_cuoi) return;
   g_nen_cuoi = t;
   CapNhatThuc();

   for(int i = 0; i < N_SLOT; i++)
     {
      if(g_lot[i] <= 0.0) { g_y_dinh[i] = 0; continue; }
      if(DangMo(i))
        {
         g_bar_vao[i]++;
         bool ra = CoDieuKienRa(i) ? CoRa(i, 1) : (g_bar_vao[i] >= Giu(i));
         g_y_dinh[i] = (ra || g_bar_vao[i] >= 500) ? -1 : 0;
        }
      else
         g_y_dinh[i] = CoVao(i, 1) ? 1 : 0;
     }

   if(g_tep != INVALID_HANDLE)
     {
      string d = TimeToString(t, TIME_DATE | TIME_MINUTES) + "," +
                 DoubleToString(iClose(_Symbol, KHUNG, 1), 2);
      for(int i = 0; i < N_SLOT; i++)
         d += "," + DoubleToString(g_thuc[i] + NoiTai(i), 2) +
              "," + (DangMo(i) ? "1" : "0");
      FileWrite(g_tep, d);
     }
  }
//+------------------------------------------------------------------+
