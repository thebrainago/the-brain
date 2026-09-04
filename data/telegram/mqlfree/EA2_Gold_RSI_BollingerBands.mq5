//+------------------------------------------------------------------+
//|          EA2_Gold_RSI_BollingerBands.mq5                        |
//|          Chiến lược: RSI + Bollinger Bands Mean Reversion        |
//|          Symbol: XAUUSD | Timeframe: H1                          |
//|                                                                  |
//|  Nguyên lý:                                                      |
//|  - Bollinger Bands xác định vùng giá quá cao / quá thấp         |
//|  - RSI xác nhận điều kiện overbought / oversold                  |
//|  - BUY khi giá chạm BB Lower + RSI < 35 (Gold đang oversold)    |
//|  - SELL khi giá chạm BB Upper + RSI > 65 (Gold đang overbought) |
//|  - Dùng BB Middle (MA20) làm TP target                           |
//|  - Phù hợp khi Gold sideway hoặc nhịp pullback trong trend       |
//+------------------------------------------------------------------+
#property copyright "Gold EA Suite 2025"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

//=== QUẢN LÝ VỐN ===
input group "=== QUẢN LÝ VỐN ==="
input double InpLotSize      = 0.01;    // Lot size cố định
input bool   InpUseAutoLot   = true;    // Dùng Auto Lot
input double InpRiskPercent  = 1.5;     // Risk % mỗi lệnh
input int    InpMaxPositions = 1;       // Số lệnh tối đa

//=== BOLLINGER BANDS ===
input group "=== BOLLINGER BANDS ==="
input int    InpBBPeriod     = 20;      // BB Period
input double InpBBDeviation  = 2.0;     // BB Deviation
input int    InpBBShift      = 0;       // BB Shift

//=== RSI ===
input group "=== RSI ==="
input int    InpRSIPeriod    = 14;      // RSI Period
input double InpRSIOversold  = 35.0;    // RSI Oversold (BUY)
input double InpRSIOverbought= 65.0;    // RSI Overbought (SELL)

//=== SL/TP ===
input group "=== STOP LOSS / TAKE PROFIT ==="
input int    InpSLPoints     = 300;     // Stop Loss (points) - ~30 pips Gold
input bool   InpTPAtBBMiddle = true;    // TP tại BB Middle (dynamic)
input int    InpTPPoints     = 500;     // TP (points) nếu không dùng BB Middle
input bool   InpUseBreakeven = true;    // Dùng Breakeven
input int    InpBEPoints     = 200;     // Kích hoạt Breakeven sau N points

//=== BỘ LỌC PHIÊN ===
input group "=== BỘ LỌC PHIÊN ==="
input int    InpStartHour    = 8;       // Giờ bắt đầu (GMT)
input int    InpEndHour      = 20;      // Giờ kết thúc (GMT)
input bool   InpTradeFriday  = false;   // Giao dịch thứ 6

//=== CÀI ĐẶT CHUNG ===
input group "=== CÀI ĐẶT CHUNG ==="
input int    InpSlippage     = 30;
input int    InpMagicNumber  = 11002;   // Magic Number EA2

//--- Global
CTrade trade;
int    g_bbHandle, g_rsiHandle;
double g_bbUpper[], g_bbMiddle[], g_bbLower[], g_rsi[];

//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_FOK);

   g_bbHandle  = iBands(_Symbol, PERIOD_CURRENT, InpBBPeriod, InpBBShift, InpBBDeviation, PRICE_CLOSE);
   g_rsiHandle = iRSI(_Symbol, PERIOD_CURRENT, InpRSIPeriod, PRICE_CLOSE);

   if(g_bbHandle == INVALID_HANDLE || g_rsiHandle == INVALID_HANDLE)
   {
      Alert("❌ [EA2] Lỗi khởi tạo indicator! Error: ", GetLastError());
      return INIT_FAILED;
   }

   ArraySetAsSeries(g_bbUpper,  true);
   ArraySetAsSeries(g_bbMiddle, true);
   ArraySetAsSeries(g_bbLower,  true);
   ArraySetAsSeries(g_rsi,      true);

   Print("✅ [EA2] Gold RSI+BB Mean Reversion khởi động | Symbol: ", _Symbol,
         " | TF: ", EnumToString(_Period), " | Magic: ", InpMagicNumber);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(g_bbHandle);
   IndicatorRelease(g_rsiHandle);
}

//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastBar = 0;
   datetime curBar = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(curBar == lastBar)
   {
      if(InpUseBreakeven) CheckBreakeven();
      return;
   }
   lastBar = curBar;

   if(!LoadData())          return;
   if(!IsTradingAllowed())  return;

   int signal = GetSignal();
   if(signal == 1 && CountMyPositions() < InpMaxPositions)
      OpenBuy();
   else if(signal == -1 && CountMyPositions() < InpMaxPositions)
      OpenSell();
}

//+------------------------------------------------------------------+
bool LoadData()
{
   if(CopyBuffer(g_bbHandle,  BASE_LINE,  0, 3, g_bbMiddle) < 3) return false;
   if(CopyBuffer(g_bbHandle,  UPPER_BAND, 0, 3, g_bbUpper)  < 3) return false;
   if(CopyBuffer(g_bbHandle,  LOWER_BAND, 0, 3, g_bbLower)  < 3) return false;
   if(CopyBuffer(g_rsiHandle, 0,          0, 3, g_rsi)       < 3) return false;
   return true;
}

//+------------------------------------------------------------------+
bool IsTradingAllowed()
{
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return false;
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))           return false;

   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(dt.day_of_week == 5 && !InpTradeFriday) return false;
   if(dt.hour < InpStartHour || dt.hour >= InpEndHour) return false;

   return true;
}

//+------------------------------------------------------------------+
// BUY:  Nến trước chạm BB Lower VÀ RSI oversold VÀ nến hiện đóng trên BB Lower
// SELL: Nến trước chạm BB Upper VÀ RSI overbought VÀ nến hiện đóng dưới BB Upper
//+------------------------------------------------------------------+
int GetSignal()
{
   double low1   = iLow(_Symbol,  PERIOD_CURRENT, 1);
   double high1  = iHigh(_Symbol, PERIOD_CURRENT, 1);
   double close1 = iClose(_Symbol, PERIOD_CURRENT, 1);
   double rsi1   = g_rsi[1];
   double bbL1   = g_bbLower[1];
   double bbU1   = g_bbUpper[1];

   // BUY: giá chạm dưới BB Lower + RSI oversold + đóng cửa phục hồi lên
   bool buySetup  = (low1 <= bbL1 && close1 > bbL1 && rsi1 < InpRSIOversold);
   // SELL: giá chạm trên BB Upper + RSI overbought + đóng cửa quay xuống
   bool sellSetup = (high1 >= bbU1 && close1 < bbU1 && rsi1 > InpRSIOverbought);

   if(buySetup)  return 1;
   if(sellSetup) return -1;
   return 0;
}

//+------------------------------------------------------------------+
void OpenBuy()
{
   double ask      = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double sl       = NormalizeDouble(ask - InpSLPoints * _Point, _Digits);
   double bbMid    = g_bbMiddle[1];
   double tp       = InpTPAtBBMiddle
                     ? NormalizeDouble(bbMid, _Digits)
                     : NormalizeDouble(ask + InpTPPoints * _Point, _Digits);

   // TP phải lớn hơn ask ít nhất
   if(tp <= ask) tp = NormalizeDouble(ask + InpTPPoints * _Point, _Digits);

   double slPoints = (ask - sl) / _Point;
   double lot      = InpUseAutoLot ? CalcAutoLot(slPoints) : InpLotSize;
   lot = NormalizeLot(lot);

   if(trade.Buy(lot, _Symbol, ask, sl, tp, "EA2-RSI+BB-BUY"))
      Print("✅ [EA2] BUY | Lot:", lot, " | SL:", sl, " | TP:", tp,
            " | RSI:", DoubleToString(g_rsi[1], 1), " | BB_L:", DoubleToString(g_bbLower[1], _Digits));
   else
      Print("❌ [EA2] BUY thất bại | Error:", GetLastError());
}

//+------------------------------------------------------------------+
void OpenSell()
{
   double bid      = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double sl       = NormalizeDouble(bid + InpSLPoints * _Point, _Digits);
   double bbMid    = g_bbMiddle[1];
   double tp       = InpTPAtBBMiddle
                     ? NormalizeDouble(bbMid, _Digits)
                     : NormalizeDouble(bid - InpTPPoints * _Point, _Digits);

   if(tp >= bid) tp = NormalizeDouble(bid - InpTPPoints * _Point, _Digits);

   double slPoints = (sl - bid) / _Point;
   double lot      = InpUseAutoLot ? CalcAutoLot(slPoints) : InpLotSize;
   lot = NormalizeLot(lot);

   if(trade.Sell(lot, _Symbol, bid, sl, tp, "EA2-RSI+BB-SELL"))
      Print("✅ [EA2] SELL | Lot:", lot, " | SL:", sl, " | TP:", tp,
            " | RSI:", DoubleToString(g_rsi[1], 1), " | BB_U:", DoubleToString(g_bbUpper[1], _Digits));
   else
      Print("❌ [EA2] SELL thất bại | Error:", GetLastError());
}

//+------------------------------------------------------------------+
void CheckBreakeven()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC)  != InpMagicNumber) continue;

      ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double curSL     = PositionGetDouble(POSITION_SL);
      double curTP     = PositionGetDouble(POSITION_TP);
      double buffer    = 10 * _Point; // buffer nhỏ

      if(type == POSITION_TYPE_BUY)
      {
         double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         if(bid >= openPrice + InpBEPoints * _Point && curSL < openPrice)
            trade.PositionModify(ticket,
               NormalizeDouble(openPrice + buffer, _Digits), curTP);
      }
      else if(type == POSITION_TYPE_SELL)
      {
         double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         if(ask <= openPrice - InpBEPoints * _Point && curSL > openPrice)
            trade.PositionModify(ticket,
               NormalizeDouble(openPrice - buffer, _Digits), curTP);
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
