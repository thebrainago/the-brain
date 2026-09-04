//+------------------------------------------------------------------+
//|          EA4_Gold_MACD_200EMA.mq5                               |
//|          Chiến lược: MACD Crossover + 200 EMA Trend Filter       |
//|          Symbol: XAUUSD | Timeframe: H4 hoặc H1                 |
//|                                                                  |
//|  Nguyên lý:                                                      |
//|  - 200 EMA xác định xu hướng tổng thể (BULL/BEAR macro)          |
//|  - MACD Crossover (đường MACD cắt Signal) → tín hiệu vào lệnh   |
//|  - BUY: Giá trên 200 EMA + MACD cross up Signal + Histogram > 0 |
//|  - SELL: Giá dưới 200 EMA + MACD cross down Signal + Hist < 0   |
//|  - 50 EMA làm bộ lọc phụ (trend trung hạn)                      |
//|  - Đây là chiến lược trend-following cổ điển, Win Rate ~55-65%   |
//|    nhưng R:R cao (1:2.5 đến 1:3) → Expectancy rất tốt           |
//+------------------------------------------------------------------+
#property copyright "Gold EA Suite 2025"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

//=== QUẢN LÝ VỐN ===
input group "=== QUẢN LÝ VỐN ==="
input double InpLotSize       = 0.01;   // Lot size cố định
input bool   InpUseAutoLot    = true;   // Dùng Auto Lot
input double InpRiskPercent   = 1.5;    // Risk % mỗi lệnh
input int    InpMaxPositions  = 1;      // Số lệnh tối đa

//=== EMA FILTERS ===
input group "=== EMA TREND FILTERS ==="
input int    InpEMA50Period   = 50;     // EMA 50 (trend trung hạn)
input int    InpEMA200Period  = 200;    // EMA 200 (trend dài hạn)

//=== MACD ===
input group "=== MACD PARAMETERS ==="
input int    InpMACDFast      = 12;     // MACD Fast EMA
input int    InpMACDSlow      = 26;     // MACD Slow EMA
input int    InpMACDSignal    = 9;      // MACD Signal
input bool   InpRequireHist   = true;   // Yêu cầu Histogram đổi chiều

//=== ATR STOPLOSS ===
input group "=== ATR-BASED SL/TP ==="
input int    InpATRPeriod     = 14;     // ATR Period
input double InpSLATR         = 2.0;    // SL = ATR x hệ số
input double InpTPATR         = 4.0;    // TP = ATR x hệ số (R:R = 1:2)
input bool   InpTrailingStop  = true;   // Trailing Stop
input double InpTrailATR      = 1.5;    // Trailing = ATR x hệ số

//=== BỘ LỌC PHIÊN ===
input group "=== BỘ LỌC PHIÊN (GMT) ==="
input int    InpTradeStart    = 7;      // Giờ bắt đầu (GMT)
input int    InpTradeEnd      = 20;     // Giờ kết thúc (GMT)
input bool   InpNoFriday      = true;   // Không trade thứ 6
input bool   InpNoMonday      = false;  // Không trade thứ 2

//=== CÀI ĐẶT ===
input group "=== CÀI ĐẶT ==="
input int    InpSlippage      = 30;
input int    InpMagicNumber   = 11004;  // Magic Number EA4

//--- Global
CTrade  trade;
int     g_ema50Handle, g_ema200Handle, g_macdHandle, g_atrHandle;
double  g_ema50[], g_ema200[];
double  g_macdMain[], g_macdSignal[], g_macdHist[];
double  g_atr[];

//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_FOK);

   g_ema50Handle  = iMA(_Symbol, PERIOD_CURRENT, InpEMA50Period,  0, MODE_EMA, PRICE_CLOSE);
   g_ema200Handle = iMA(_Symbol, PERIOD_CURRENT, InpEMA200Period, 0, MODE_EMA, PRICE_CLOSE);
   g_macdHandle   = iMACD(_Symbol, PERIOD_CURRENT, InpMACDFast, InpMACDSlow, InpMACDSignal, PRICE_CLOSE);
   g_atrHandle    = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);

   if(g_ema50Handle  == INVALID_HANDLE || g_ema200Handle == INVALID_HANDLE ||
      g_macdHandle   == INVALID_HANDLE || g_atrHandle    == INVALID_HANDLE)
   {
      Alert("❌ [EA4] Lỗi indicator! Error: ", GetLastError());
      return INIT_FAILED;
   }

   ArraySetAsSeries(g_ema50,      true);
   ArraySetAsSeries(g_ema200,     true);
   ArraySetAsSeries(g_macdMain,   true);
   ArraySetAsSeries(g_macdSignal, true);
   ArraySetAsSeries(g_macdHist,   true);
   ArraySetAsSeries(g_atr,        true);

   Print("✅ [EA4] Gold MACD+200EMA khởi động | Symbol: ", _Symbol,
         " | TF: ", EnumToString(_Period), " | Magic: ", InpMagicNumber);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(g_ema50Handle);
   IndicatorRelease(g_ema200Handle);
   IndicatorRelease(g_macdHandle);
   IndicatorRelease(g_atrHandle);
}

//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastBar = 0;
   datetime curBar = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(curBar == lastBar)
   {
      if(InpTrailingStop) ManageTrailing();
      return;
   }
   lastBar = curBar;

   if(!LoadData())         return;
   if(!IsTradingAllowed()) return;

   int signal = GetSignal();
   if(signal == 1 && CountMyPositions() < InpMaxPositions)
      OpenBuy();
   else if(signal == -1 && CountMyPositions() < InpMaxPositions)
      OpenSell();
}

//+------------------------------------------------------------------+
bool LoadData()
{
   if(CopyBuffer(g_ema50Handle,  0, 0, 4, g_ema50)      < 4) return false;
   if(CopyBuffer(g_ema200Handle, 0, 0, 4, g_ema200)     < 4) return false;
   if(CopyBuffer(g_macdHandle,   MAIN_LINE,   0, 4, g_macdMain)   < 4) return false;
   if(CopyBuffer(g_macdHandle,   SIGNAL_LINE, 0, 4, g_macdSignal) < 4) return false;
   if(CopyBuffer(g_atrHandle,    0, 0, 3, g_atr)        < 3) return false;

   // Tính histogram thủ công
   for(int i = 0; i < ArraySize(g_macdMain); i++)
      g_macdHist[i] = g_macdMain[i] - g_macdSignal[i];

   return true;
}

//+------------------------------------------------------------------+
bool IsTradingAllowed()
{
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return false;
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))           return false;

   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(dt.day_of_week == 5 && InpNoFriday)  return false;
   if(dt.day_of_week == 1 && InpNoMonday)  return false;
   if(dt.hour < InpTradeStart || dt.hour >= InpTradeEnd) return false;

   return true;
}

//+------------------------------------------------------------------+
// Điều kiện BUY mạnh:
//   1. Giá > EMA200 (xu hướng tăng dài hạn)
//   2. EMA50 > EMA200 (xu hướng tăng trung hạn)
//   3. MACD cross up Signal (MACD[2] < Signal[2] và MACD[1] > Signal[1])
//   4. Histogram đang tăng (nếu InpRequireHist)
//
// Điều kiện SELL mạnh:
//   Ngược lại
//+------------------------------------------------------------------+
int GetSignal()
{
   double close1 = iClose(_Symbol, PERIOD_CURRENT, 1);

   bool bullMacro = (close1 > g_ema200[1] && g_ema50[1] > g_ema200[1]);
   bool bearMacro = (close1 < g_ema200[1] && g_ema50[1] < g_ema200[1]);

   // MACD crossover tại bar đã đóng
   bool macdCrossUp   = (g_macdMain[2] < g_macdSignal[2] && g_macdMain[1] > g_macdSignal[1]);
   bool macdCrossDown = (g_macdMain[2] > g_macdSignal[2] && g_macdMain[1] < g_macdSignal[1]);

   bool histBull = !InpRequireHist || (g_macdHist[1] > 0 && g_macdHist[1] > g_macdHist[2]);
   bool histBear = !InpRequireHist || (g_macdHist[1] < 0 && g_macdHist[1] < g_macdHist[2]);

   if(bullMacro && macdCrossUp   && histBull) return 1;
   if(bearMacro && macdCrossDown && histBear) return -1;
   return 0;
}

//+------------------------------------------------------------------+
void OpenBuy()
{
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double atr = g_atr[1];
   double sl  = NormalizeDouble(ask - atr * InpSLATR, _Digits);
   double tp  = NormalizeDouble(ask + atr * InpTPATR, _Digits);
   double slPts = (ask - sl) / _Point;
   double lot = InpUseAutoLot ? CalcAutoLot(slPts) : InpLotSize;
   lot = NormalizeLot(lot);

   if(trade.Buy(lot, _Symbol, ask, sl, tp, "EA4-MACD+EMA-BUY"))
      Print("✅ [EA4] BUY | Lot:", lot, " | SL:", sl, " | TP:", tp,
            " | MACD:", DoubleToString(g_macdMain[1], 5),
            " | EMA200:", DoubleToString(g_ema200[1], _Digits));
   else
      Print("❌ [EA4] BUY thất bại | Error:", GetLastError());
}

//+------------------------------------------------------------------+
void OpenSell()
{
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double atr = g_atr[1];
   double sl  = NormalizeDouble(bid + atr * InpSLATR, _Digits);
   double tp  = NormalizeDouble(bid - atr * InpTPATR, _Digits);
   double slPts = (sl - bid) / _Point;
   double lot = InpUseAutoLot ? CalcAutoLot(slPts) : InpLotSize;
   lot = NormalizeLot(lot);

   if(trade.Sell(lot, _Symbol, bid, sl, tp, "EA4-MACD+EMA-SELL"))
      Print("✅ [EA4] SELL | Lot:", lot, " | SL:", sl, " | TP:", tp,
            " | MACD:", DoubleToString(g_macdMain[1], 5),
            " | EMA200:", DoubleToString(g_ema200[1], _Digits));
   else
      Print("❌ [EA4] SELL thất bại | Error:", GetLastError());
}

//+------------------------------------------------------------------+
void ManageTrailing()
{
   if(!InpTrailingStop) return;
   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(g_atrHandle, 0, 0, 2, atr) < 2) return;

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
         double newSL = NormalizeDouble(bid - atr[1] * InpTrailATR, _Digits);
         if(newSL > curSL + _Point)
            trade.PositionModify(ticket, newSL, curTP);
      }
      else if(type == POSITION_TYPE_SELL)
      {
         double ask   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         double newSL = NormalizeDouble(ask + atr[1] * InpTrailATR, _Digits);
         if(curSL == 0 || newSL < curSL - _Point)
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
double CalcAutoLot(double slPoints)
{
   if(slPoints <= 0) return InpLotSize;
   double balance    = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = balance * InpRiskPercent / 100.0;
   double tickVal    = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSz     = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double pointVal   = tickVal * (_Point / tickSz);
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
