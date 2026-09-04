//+------------------------------------------------------------------+
//|          EA1_Gold_MultiEMA_ATR.mq5                              |
//|          Chiến lược: Triple EMA Trend + ATR Dynamic SL/TP       |
//|          Symbol: XAUUSD | Timeframe: H1 hoặc H4                 |
//|                                                                  |
//|  Nguyên lý:                                                      |
//|  - 3 EMA (21, 55, 200) phải cùng chiều → xác nhận trend mạnh   |
//|  - ATR tính SL/TP động theo biến động thực tế của Gold          |
//|  - Trailing Stop bằng ATR để bắt xu hướng dài                   |
//|  - Bộ lọc phiên London + New York (giờ vàng của Gold)           |
//+------------------------------------------------------------------+
#property copyright "Gold EA Suite 2025"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

//=== QUẢN LÝ VỐN ===
input group "=== QUẢN LÝ VỐN ==="
input double InpLotSize       = 0.01;    // Lot size cố định
input bool   InpUseAutoLot    = true;    // Tự động tính lot theo % risk
input double InpRiskPercent   = 1.5;     // Risk % mỗi lệnh (nếu AutoLot)
input int    InpMaxPositions  = 1;       // Số lệnh tối đa cùng lúc

//=== CHỈ SỐ EMA ===
input group "=== CHỈ SỐ EMA ==="
input int    InpFastEMA       = 21;      // EMA nhanh
input int    InpMedEMA        = 55;      // EMA giữa
input int    InpSlowEMA       = 200;     // EMA chậm (trend chính)

//=== ATR CHO SL/TP ===
input group "=== ATR DYNAMIC SL/TP ==="
input int    InpATRPeriod     = 14;      // ATR Period
input double InpSLMultiplier  = 1.5;     // SL = ATR x hệ số này
input double InpTPMultiplier  = 3.0;     // TP = ATR x hệ số này
input bool   InpUseTrailing   = true;    // Dùng Trailing Stop
input double InpTrailATR      = 1.0;     // Trailing = ATR x hệ số này

//=== BỘ LỌC PHIÊN ===
input group "=== BỘ LỌC PHIÊN GIAO DỊCH (GMT) ==="
input int    InpLondonOpen    = 7;       // Mở phiên London (GMT)
input int    InpNYClose       = 21;      // Đóng phiên New York (GMT)
input bool   InpTradeMonday   = true;    // Giao dịch thứ 2
input bool   InpTradeFriday   = false;   // Giao dịch thứ 6 (tránh close tuần)

//=== CÀI ĐẶT CHUNG ===
input group "=== CÀI ĐẶT CHUNG ==="
input int    InpSlippage      = 30;      // Slippage tối đa (points)
input int    InpMagicNumber   = 11001;   // Magic Number EA1

//--- Global
CTrade  trade;
int     g_fastEMAHandle, g_medEMAHandle, g_slowEMAHandle, g_atrHandle;
double  g_fastEMA[], g_medEMA[], g_slowEMA[], g_atr[];

//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_FOK);

   g_fastEMAHandle = iMA(_Symbol, PERIOD_CURRENT, InpFastEMA, 0, MODE_EMA, PRICE_CLOSE);
   g_medEMAHandle  = iMA(_Symbol, PERIOD_CURRENT, InpMedEMA,  0, MODE_EMA, PRICE_CLOSE);
   g_slowEMAHandle = iMA(_Symbol, PERIOD_CURRENT, InpSlowEMA, 0, MODE_EMA, PRICE_CLOSE);
   g_atrHandle     = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);

   if(g_fastEMAHandle == INVALID_HANDLE || g_medEMAHandle == INVALID_HANDLE ||
      g_slowEMAHandle == INVALID_HANDLE || g_atrHandle == INVALID_HANDLE)
   {
      Alert("❌ [EA1] Lỗi khởi tạo indicator! Error: ", GetLastError());
      return INIT_FAILED;
   }

   ArraySetAsSeries(g_fastEMA, true);
   ArraySetAsSeries(g_medEMA,  true);
   ArraySetAsSeries(g_slowEMA, true);
   ArraySetAsSeries(g_atr,     true);

   Print("✅ [EA1] Gold Triple EMA + ATR khởi động | Symbol: ", _Symbol,
         " | TF: ", EnumToString(_Period), " | Magic: ", InpMagicNumber);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(g_fastEMAHandle);
   IndicatorRelease(g_medEMAHandle);
   IndicatorRelease(g_slowEMAHandle);
   IndicatorRelease(g_atrHandle);
   Print("[EA1] Đã tắt. Reason: ", reason);
}

//+------------------------------------------------------------------+
void OnTick()
{
   // Bộ lọc bar mới (tránh xử lý nhiều lần trong 1 nến)
   static datetime lastBar = 0;
   datetime curBar = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(curBar == lastBar)
   {
      if(InpUseTrailing) ManageTrailing();
      return;
   }
   lastBar = curBar;

   // Lấy dữ liệu indicator
   if(!LoadIndicatorData()) return;
   if(!IsTradingAllowed())  return;

   // Kiểm tra signal
   int signal = GetSignal();

   if(signal == 1 && CountMyPositions() < InpMaxPositions)
      OpenBuy();
   else if(signal == -1 && CountMyPositions() < InpMaxPositions)
      OpenSell();
}

//+------------------------------------------------------------------+
bool LoadIndicatorData()
{
   if(CopyBuffer(g_fastEMAHandle, 0, 0, 4, g_fastEMA) < 4) return false;
   if(CopyBuffer(g_medEMAHandle,  0, 0, 4, g_medEMA)  < 4) return false;
   if(CopyBuffer(g_slowEMAHandle, 0, 0, 4, g_slowEMA) < 4) return false;
   if(CopyBuffer(g_atrHandle,     0, 0, 3, g_atr)     < 3) return false;
   return true;
}

//+------------------------------------------------------------------+
bool IsTradingAllowed()
{
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return false;
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))           return false;

   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(dt.day_of_week == 1 && !InpTradeMonday) return false;
   if(dt.day_of_week == 5 && !InpTradeFriday) return false;
   if(dt.hour < InpLondonOpen || dt.hour >= InpNYClose) return false;

   return true;
}

//+------------------------------------------------------------------+
// Signal: 1=BUY, -1=SELL, 0=chờ
// Điều kiện BUY:  EMA21 > EMA55 > EMA200 VÀ price cross up EMA21
// Điều kiện SELL: EMA21 < EMA55 < EMA200 VÀ price cross down EMA21
//+------------------------------------------------------------------+
int GetSignal()
{
   double close1 = iClose(_Symbol, PERIOD_CURRENT, 1);
   double close2 = iClose(_Symbol, PERIOD_CURRENT, 2);

   bool bullTrend = (g_fastEMA[1] > g_medEMA[1] && g_medEMA[1] > g_slowEMA[1]);
   bool bearTrend = (g_fastEMA[1] < g_medEMA[1] && g_medEMA[1] < g_slowEMA[1]);

   // Giá cross over EMA fast từ dưới lên
   bool buyCross  = (close2 < g_fastEMA[2] && close1 > g_fastEMA[1]);
   // Giá cross under EMA fast từ trên xuống
   bool sellCross = (close2 > g_fastEMA[2] && close1 < g_fastEMA[1]);

   if(bullTrend && buyCross)  return 1;
   if(bearTrend && sellCross) return -1;
   return 0;
}

//+------------------------------------------------------------------+
void OpenBuy()
{
   double ask  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double atr  = g_atr[1];
   double sl   = NormalizeDouble(ask - atr * InpSLMultiplier,  _Digits);
   double tp   = NormalizeDouble(ask + atr * InpTPMultiplier,  _Digits);
   double lot  = InpUseAutoLot ? CalcAutoLot(atr * InpSLMultiplier) : InpLotSize;
   lot = NormalizeLot(lot);

   if(trade.Buy(lot, _Symbol, ask, sl, tp, "EA1-GoldTrend-BUY"))
      Print("✅ [EA1] BUY | Lot:", lot, " | SL:", sl, " | TP:", tp,
            " | ATR:", DoubleToString(atr, _Digits));
   else
      Print("❌ [EA1] BUY thất bại | Error:", GetLastError());
}

//+------------------------------------------------------------------+
void OpenSell()
{
   double bid  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double atr  = g_atr[1];
   double sl   = NormalizeDouble(bid + atr * InpSLMultiplier, _Digits);
   double tp   = NormalizeDouble(bid - atr * InpTPMultiplier, _Digits);
   double lot  = InpUseAutoLot ? CalcAutoLot(atr * InpSLMultiplier) : InpLotSize;
   lot = NormalizeLot(lot);

   if(trade.Sell(lot, _Symbol, bid, sl, tp, "EA1-GoldTrend-SELL"))
      Print("✅ [EA1] SELL | Lot:", lot, " | SL:", sl, " | TP:", tp,
            " | ATR:", DoubleToString(atr, _Digits));
   else
      Print("❌ [EA1] SELL thất bại | Error:", GetLastError());
}

//+------------------------------------------------------------------+
void ManageTrailing()
{
   if(!InpUseTrailing) return;
   if(CopyBuffer(g_atrHandle, 0, 0, 2, g_atr) < 2) return;

   double atr = g_atr[1];

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;

      ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double curSL = PositionGetDouble(POSITION_SL);
      double curTP = PositionGetDouble(POSITION_TP);

      if(type == POSITION_TYPE_BUY)
      {
         double bid   = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         double newSL = NormalizeDouble(bid - atr * InpTrailATR, _Digits);
         if(newSL > curSL + _Point)
            trade.PositionModify(ticket, newSL, curTP);
      }
      else if(type == POSITION_TYPE_SELL)
      {
         double ask   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         double newSL = NormalizeDouble(ask + atr * InpTrailATR, _Digits);
         if(newSL < curSL - _Point || curSL == 0)
            trade.PositionModify(ticket, newSL, curTP);
      }
   }
}

//+------------------------------------------------------------------+
int CountMyPositions()
{
   int count = 0;
   for(int i = 0; i < PositionsTotal(); i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
         count++;
   }
   return count;
}

//+------------------------------------------------------------------+
double CalcAutoLot(double slInPrice)
{
   if(slInPrice <= 0) return InpLotSize;
   double balance    = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = balance * InpRiskPercent / 100.0;
   double tickVal    = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSz     = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double pointVal   = tickVal * (_Point / tickSz);
   double slPoints   = slInPrice / _Point;
   double lot        = riskAmount / (slPoints * pointVal);
   return NormalizeLot(lot);
}

//+------------------------------------------------------------------+
double NormalizeLot(double lot)
{
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lot = MathFloor(lot / stepLot) * stepLot;
   return NormalizeDouble(MathMax(minLot, MathMin(maxLot, lot)), 2);
}
//+------------------------------------------------------------------+
