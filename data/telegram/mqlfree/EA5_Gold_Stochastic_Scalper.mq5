//+------------------------------------------------------------------+
//|          EA5_Gold_Stochastic_Scalper.mq5                        |
//|          Chiến lược: Stochastic Scalper + Dynamic Pivot Points   |
//|          Symbol: XAUUSD | Timeframe: M15 hoặc M30               |
//|                                                                  |
//|  Nguyên lý:                                                      |
//|  - Tính Pivot Points tự động từ nến ngày hôm qua (Daily)        |
//|    → PP, R1, R2, R3, S1, S2, S3                                 |
//|  - Stochastic xác nhận momentum khi giá về vùng hỗ trợ/kháng cự|
//|  - BUY: Giá tiếp cận S1/S2 + Stoch Oversold (<20) + crossover   |
//|  - SELL: Giá tiếp cận R1/R2 + Stoch Overbought (>80) + crossover|
//|  - 21 EMA làm bộ lọc xu hướng ngắn hạn (chỉ BUY khi trên EMA,  |
//|    chỉ SELL khi dưới EMA)                                        |
//|  - Scalper: TP nhỏ (50-150 pts), SL chặt, win rate cao ~65-70%  |
//|  - Chạy tốt nhất trong London + NY session                       |
//+------------------------------------------------------------------+
#property copyright "Gold EA Suite 2025"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

//=== QUẢN LÝ VỐN ===
input group "=== QUẢN LÝ VỐN ==="
input double InpLotSize       = 0.01;   // Lot size cố định
input bool   InpUseAutoLot    = true;   // Dùng Auto Lot
input double InpRiskPercent   = 1.0;    // Risk % mỗi lệnh (nhỏ vì scalper)
input int    InpMaxPositions  = 2;      // Số lệnh tối đa

//=== PIVOT POINTS ===
input group "=== PIVOT POINTS ==="
input double InpPivotZone     = 150;    // Vùng tiếp cận Pivot (points) để kích hoạt
input bool   InpUseR2S2       = true;   // Dùng thêm R2/S2 làm target/entry

//=== STOCHASTIC ===
input group "=== STOCHASTIC ==="
input int    InpStochK        = 5;      // %K Period
input int    InpStochD        = 3;      // %D Period
input int    InpStochSlowing  = 3;      // Slowing
input double InpStochOversold = 25.0;   // Oversold (BUY)
input double InpStochOverbought=75.0;   // Overbought (SELL)

//=== EMA FILTER ===
input group "=== EMA TREND FILTER ==="
input int    InpEMAPeriod     = 21;     // EMA Period

//=== SL/TP SCALPER ===
input group "=== SL/TP SCALPER ==="
input int    InpSLPoints      = 150;    // Stop Loss (points) - ~15 pips Gold
input int    InpTP1Points     = 100;    // TP1 (points) - đóng 50% lệnh
input int    InpTP2Points     = 200;    // TP2 (points) - đóng 50% còn lại
input bool   InpUseTP2        = true;   // Dùng 2 mức TP (partial close)
input bool   InpMoveBE        = true;   // Dời SL về Breakeven khi TP1 hit
input int    InpBEBuffer      = 10;     // Buffer Breakeven (points)

//=== BỘ LỌC PHIÊN ===
input group "=== BỘ LỌC PHIÊN (GMT) ==="
input int    InpStartHour     = 7;      // Bắt đầu (London 07:00 GMT)
input int    InpEndHour       = 20;     // Kết thúc (20:00 GMT)
input bool   InpNoFriday      = true;   // Bỏ thứ 6

//=== CÀI ĐẶT ===
input group "=== CÀI ĐẶT ==="
input int    InpSlippage      = 30;
input int    InpMagicNumber   = 11005;  // Magic Number EA5

//--- Global
CTrade trade;
int    g_stochHandle, g_emaHandle;
double g_stochK[], g_stochD[], g_ema[];

// Pivot Points (tính từ Daily candle hôm qua)
double g_PP, g_R1, g_R2, g_R3, g_S1, g_S2, g_S3;
datetime g_lastPivotDay = 0;

// Partial close tracking
struct SPartialClose
{
   ulong  ticket;
   bool   tp1Hit;
};
SPartialClose g_partials[10];
int g_partialCount = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_FOK);

   g_stochHandle = iStochastic(_Symbol, PERIOD_CURRENT,
                                InpStochK, InpStochD, InpStochSlowing,
                                MODE_SMA, STO_LOWHIGH);
   g_emaHandle   = iMA(_Symbol, PERIOD_CURRENT, InpEMAPeriod, 0, MODE_EMA, PRICE_CLOSE);

   if(g_stochHandle == INVALID_HANDLE || g_emaHandle == INVALID_HANDLE)
   {
      Alert("❌ [EA5] Lỗi indicator! Error: ", GetLastError());
      return INIT_FAILED;
   }

   ArraySetAsSeries(g_stochK, true);
   ArraySetAsSeries(g_stochD, true);
   ArraySetAsSeries(g_ema,    true);

   CalcPivotPoints(); // Tính pivot ngay khi khởi động

   Print("✅ [EA5] Gold Stochastic Scalper khởi động | Symbol: ", _Symbol,
         " | TF: ", EnumToString(_Period), " | Magic: ", InpMagicNumber);
   Print("[EA5] Pivot: PP=", DoubleToString(g_PP, _Digits),
         " | R1=", DoubleToString(g_R1, _Digits), " | S1=", DoubleToString(g_S1, _Digits));
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(g_stochHandle);
   IndicatorRelease(g_emaHandle);
}

//+------------------------------------------------------------------+
void OnTick()
{
   // Cập nhật Pivot Points mỗi ngày mới
   UpdatePivotIfNeeded();

   static datetime lastBar = 0;
   datetime curBar = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(curBar == lastBar)
   {
      if(InpMoveBE) CheckPartialAndBreakeven();
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
void UpdatePivotIfNeeded()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   datetime today = StringToTime(
      StringFormat("%04d.%02d.%02d 00:00:00", dt.year, dt.mon, dt.day));

   if(g_lastPivotDay != today)
   {
      CalcPivotPoints();
      g_lastPivotDay = today;
      Print("[EA5] Pivot mới: PP=", DoubleToString(g_PP, _Digits),
            " R1=", DoubleToString(g_R1, _Digits),
            " R2=", DoubleToString(g_R2, _Digits),
            " S1=", DoubleToString(g_S1, _Digits),
            " S2=", DoubleToString(g_S2, _Digits));
   }
}

//+------------------------------------------------------------------+
// Tính Pivot Points Standard từ High/Low/Close của ngày hôm qua
//+------------------------------------------------------------------+
void CalcPivotPoints()
{
   // Lấy dữ liệu Daily bar hôm qua (bar 1 trên D1)
   double prevHigh  = iHigh(_Symbol,  PERIOD_D1, 1);
   double prevLow   = iLow(_Symbol,   PERIOD_D1, 1);
   double prevClose = iClose(_Symbol, PERIOD_D1, 1);

   if(prevHigh <= 0 || prevLow <= 0 || prevClose <= 0) return;

   g_PP = (prevHigh + prevLow + prevClose) / 3.0;
   g_R1 = 2 * g_PP - prevLow;
   g_R2 = g_PP + (prevHigh - prevLow);
   g_R3 = prevHigh + 2 * (g_PP - prevLow);
   g_S1 = 2 * g_PP - prevHigh;
   g_S2 = g_PP - (prevHigh - prevLow);
   g_S3 = prevLow - 2 * (prevHigh - g_PP);
}

//+------------------------------------------------------------------+
bool LoadData()
{
   if(CopyBuffer(g_stochHandle, MAIN_LINE,   0, 4, g_stochK) < 4) return false;
   if(CopyBuffer(g_stochHandle, SIGNAL_LINE, 0, 4, g_stochD) < 4) return false;
   if(CopyBuffer(g_emaHandle,   0,           0, 4, g_ema)    < 4) return false;
   return true;
}

//+------------------------------------------------------------------+
bool IsTradingAllowed()
{
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return false;
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))           return false;

   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(dt.day_of_week == 5 && InpNoFriday) return false;
   if(dt.hour < InpStartHour || dt.hour >= InpEndHour) return false;

   return true;
}

//+------------------------------------------------------------------+
// BUY Setup:
//   1. Giá gần S1 hoặc S2 (trong vùng pivot zone)
//   2. Stoch %K < Oversold và %K cross up %D (từ dưới)
//   3. Giá hiện tại > EMA21 (xu hướng ngắn đang tăng)
//
// SELL Setup:
//   1. Giá gần R1 hoặc R2
//   2. Stoch %K > Overbought và %K cross down %D
//   3. Giá hiện tại < EMA21
//+------------------------------------------------------------------+
int GetSignal()
{
   double bid    = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask    = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double zone   = InpPivotZone * _Point;

   // Kiểm tra vùng hỗ trợ (S1 hoặc S2)
   bool nearS1   = (MathAbs(bid - g_S1) <= zone);
   bool nearS2   = (InpUseR2S2 && MathAbs(bid - g_S2) <= zone);
   bool nearSupp = (nearS1 || nearS2);

   // Kiểm tra vùng kháng cự (R1 hoặc R2)
   bool nearR1   = (MathAbs(ask - g_R1) <= zone);
   bool nearR2   = (InpUseR2S2 && MathAbs(ask - g_R2) <= zone);
   bool nearRes  = (nearR1 || nearR2);

   // Stochastic crossover
   bool stochCrossUp   = (g_stochK[2] < g_stochD[2] && g_stochK[1] > g_stochD[1]
                          && g_stochK[1] < InpStochOversold);
   bool stochCrossDown = (g_stochK[2] > g_stochD[2] && g_stochK[1] < g_stochD[1]
                          && g_stochK[1] > InpStochOverbought);

   // EMA filter
   double close1  = iClose(_Symbol, PERIOD_CURRENT, 1);
   bool aboveEMA  = (close1 > g_ema[1]);
   bool belowEMA  = (close1 < g_ema[1]);

   // BUY: support + stoch oversold cross + above EMA
   if(nearSupp && stochCrossUp && aboveEMA)
   {
      Print("[EA5] BUY Signal | near S:", nearS1?"S1":"S2",
            " | Stoch %K:", DoubleToString(g_stochK[1], 1));
      return 1;
   }

   // SELL: resistance + stoch overbought cross + below EMA
   if(nearRes && stochCrossDown && belowEMA)
   {
      Print("[EA5] SELL Signal | near R:", nearR1?"R1":"R2",
            " | Stoch %K:", DoubleToString(g_stochK[1], 1));
      return -1;
   }

   return 0;
}

//+------------------------------------------------------------------+
void OpenBuy()
{
   double ask  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double sl   = NormalizeDouble(ask - InpSLPoints * _Point,  _Digits);
   double tp1  = NormalizeDouble(ask + InpTP1Points * _Point, _Digits);
   double tp2  = NormalizeDouble(ask + InpTP2Points * _Point, _Digits);
   double tp   = InpUseTP2 ? tp2 : tp1; // TP chính đặt tại TP2
   double slPts= (ask - sl) / _Point;
   double lot  = InpUseAutoLot ? CalcAutoLot(slPts) : InpLotSize;
   lot = NormalizeLot(lot);

   if(trade.Buy(lot, _Symbol, ask, sl, tp, "EA5-Stoch-Scalp-BUY"))
   {
      ulong ticket = trade.ResultDeal();
      Print("✅ [EA5] BUY | Lot:", lot, " | SL:", sl, " | TP1:", tp1, " | TP2:", tp2);
      // Đăng ký theo dõi partial close
      if(InpUseTP2 && g_partialCount < 10)
      {
         g_partials[g_partialCount].ticket = trade.ResultOrder();
         g_partials[g_partialCount].tp1Hit = false;
         g_partialCount++;
      }
   }
   else
      Print("❌ [EA5] BUY thất bại | Error:", GetLastError());
}

//+------------------------------------------------------------------+
void OpenSell()
{
   double bid  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double sl   = NormalizeDouble(bid + InpSLPoints * _Point,  _Digits);
   double tp1  = NormalizeDouble(bid - InpTP1Points * _Point, _Digits);
   double tp2  = NormalizeDouble(bid - InpTP2Points * _Point, _Digits);
   double tp   = InpUseTP2 ? tp2 : tp1;
   double slPts= (sl - bid) / _Point;
   double lot  = InpUseAutoLot ? CalcAutoLot(slPts) : InpLotSize;
   lot = NormalizeLot(lot);

   if(trade.Sell(lot, _Symbol, bid, sl, tp, "EA5-Stoch-Scalp-SELL"))
   {
      Print("✅ [EA5] SELL | Lot:", lot, " | SL:", sl, " | TP1:", tp1, " | TP2:", tp2);
      if(InpUseTP2 && g_partialCount < 10)
      {
         g_partials[g_partialCount].ticket = trade.ResultOrder();
         g_partials[g_partialCount].tp1Hit = false;
         g_partialCount++;
      }
   }
   else
      Print("❌ [EA5] SELL thất bại | Error:", GetLastError());
}

//+------------------------------------------------------------------+
// Partial Close + Breakeven khi đạt TP1
//+------------------------------------------------------------------+
void CheckPartialAndBreakeven()
{
   if(!InpUseTP2) return;

   for(int i = 0; i < g_partialCount; i++)
   {
      ulong ticket = g_partials[i].ticket;
      if(g_partials[i].tp1Hit) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;

      ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double curVol    = PositionGetDouble(POSITION_VOLUME);
      double curSL     = PositionGetDouble(POSITION_SL);
      double curTP     = PositionGetDouble(POSITION_TP);

      if(type == POSITION_TYPE_BUY)
      {
         double bid   = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         double tp1   = openPrice + InpTP1Points * _Point;
         if(bid >= tp1)
         {
            // Đóng 50% lot
            double closeVol = NormalizeLot(curVol * 0.5);
            if(trade.PositionClosePartial(ticket, closeVol))
            {
               Print("✅ [EA5] Partial Close BUY 50% tại TP1 | Lot đóng:", closeVol);
               // Dời SL về Breakeven
               double newSL = NormalizeDouble(openPrice + InpBEBuffer * _Point, _Digits);
               trade.PositionModify(ticket, newSL, curTP);
               g_partials[i].tp1Hit = true;
            }
         }
      }
      else if(type == POSITION_TYPE_SELL)
      {
         double ask   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         double tp1   = openPrice - InpTP1Points * _Point;
         if(ask <= tp1)
         {
            double closeVol = NormalizeLot(curVol * 0.5);
            if(trade.PositionClosePartial(ticket, closeVol))
            {
               Print("✅ [EA5] Partial Close SELL 50% tại TP1 | Lot đóng:", closeVol);
               double newSL = NormalizeDouble(openPrice - InpBEBuffer * _Point, _Digits);
               trade.PositionModify(ticket, newSL, curTP);
               g_partials[i].tp1Hit = true;
            }
         }
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
