//+------------------------------------------------------------------+
//|          EA3_Gold_London_Breakout.mq5                           |
//|          Chiến lược: Asian Range Breakout → London Session       |
//|          Symbol: XAUUSD | Timeframe: M15 hoặc H1                |
//|                                                                  |
//|  Nguyên lý:                                                      |
//|  - Phiên Châu Á (00:00-07:00 GMT): Gold đi ngang → xác định     |
//|    High/Low của phiên này làm vùng kháng cự/hỗ trợ quan trọng   |
//|  - Khi London mở cửa (07:00 GMT): nếu giá break qua High →BUY  |
//|    nếu giá break qua Low → SELL                                  |
//|  - Đây là chiến lược cực kỳ hiệu quả cho Gold vì Gold thường    |
//|    tạo xu hướng rõ ràng khi phiên London bắt đầu               |
//|  - Chỉ vào 1 lệnh mỗi ngày, đặt lệnh Pending Stop Order        |
//+------------------------------------------------------------------+
#property copyright "Gold EA Suite 2025"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

//=== QUẢN LÝ VỐN ===
input group "=== QUẢN LÝ VỐN ==="
input double InpLotSize       = 0.01;   // Lot size cố định
input bool   InpUseAutoLot    = true;   // Dùng Auto Lot
input double InpRiskPercent   = 2.0;    // Risk % mỗi lệnh
input int    InpMaxTradesDay  = 1;      // Số lệnh tối đa mỗi ngày

//=== PHIÊN CHÂU Á (Range) ===
input group "=== PHIÊN CHÂU Á - XÁC ĐỊNH RANGE (GMT) ==="
input int    InpAsianStart    = 0;      // Giờ bắt đầu phiên Á (GMT 0:00)
input int    InpAsianEnd      = 7;      // Giờ kết thúc phiên Á (GMT 7:00)
input int    InpMinRangePoints= 150;    // Range tối thiểu (points) để valid

//=== LONDON BREAKOUT ===
input group "=== LONDON BREAKOUT (GMT) ==="
input int    InpLondonOpen    = 7;      // Giờ mở London (GMT)
input int    InpLondonClose   = 12;     // Đóng phiên + hủy pending
input int    InpBreakBuffer   = 10;     // Buffer vào lệnh phía trên/dưới range (points)

//=== SL/TP ===
input group "=== STOP LOSS / TAKE PROFIT ==="
input bool   InpSLAtOpposite  = true;   // SL tại mức đối diện của range
input int    InpSLBuffer      = 50;     // Buffer thêm cho SL (points)
input double InpRRRatio       = 2.0;    // Risk:Reward ratio cho TP
input bool   InpUseTrailing   = true;   // Dùng Trailing Stop
input int    InpTrailPoints   = 200;    // Trailing (points)
input int    InpTrailStep     = 50;     // Step trailing (points)

//=== CÀI ĐẶT ===
input group "=== CÀI ĐẶT ==="
input int    InpSlippage      = 30;
input int    InpMagicNumber   = 11003;  // Magic Number EA3

//--- Global
CTrade  trade;
double  g_asianHigh  = 0;
double  g_asianLow   = DBL_MAX;
bool    g_rangeReady = false;     // Range đã sẵn sàng chưa
bool    g_tradedToday= false;     // Đã vào lệnh hôm nay chưa
bool    g_pendingSet = false;     // Đã đặt lệnh pending chưa
datetime g_lastRangeDay = 0;      // Ngày cuối tính range
ulong   g_buyStopTicket  = 0;
ulong   g_sellStopTicket = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_FOK);

   Print("✅ [EA3] Gold London Breakout khởi động | Symbol: ", _Symbol,
         " | TF: ", EnumToString(_Period), " | Magic: ", InpMagicNumber);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Xóa lệnh pending nếu còn
   CancelPendingOrders();
   Print("[EA3] Đã tắt. Reason: ", reason);
}

//+------------------------------------------------------------------+
void OnTick()
{
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return;
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))           return;

   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);

   // Reset mỗi ngày mới
   datetime today = StringToTime(
      StringFormat("%04d.%02d.%02d 00:00:00", dt.year, dt.mon, dt.day));
   if(g_lastRangeDay != today)
   {
      g_asianHigh   = 0;
      g_asianLow    = DBL_MAX;
      g_rangeReady  = false;
      g_tradedToday = false;
      g_pendingSet  = false;
      g_lastRangeDay= today;
      g_buyStopTicket  = 0;
      g_sellStopTicket = 0;
      Print("[EA3] Reset ngày mới: ", TimeToString(TimeCurrent()));
   }

   // Thứ 6: không mở lệnh mới
   if(dt.day_of_week == 5) return;

   int hour = dt.hour;

   //--- BƯỚC 1: Tính range phiên Châu Á
   if(hour >= InpAsianStart && hour < InpAsianEnd && !g_rangeReady)
   {
      double high = iHigh(_Symbol, PERIOD_CURRENT, 0);
      double low  = iLow(_Symbol,  PERIOD_CURRENT, 0);
      if(high > g_asianHigh) g_asianHigh = high;
      if(low  < g_asianLow)  g_asianLow  = low;
   }

   //--- BƯỚC 2: London mở cửa → đặt lệnh pending nếu range đủ lớn
   if(hour >= InpLondonOpen && !g_rangeReady && g_asianHigh > 0 && g_asianLow < DBL_MAX)
   {
      double rangeSize = (g_asianHigh - g_asianLow) / _Point;
      if(rangeSize >= InpMinRangePoints)
      {
         g_rangeReady = true;
         Print("[EA3] Range xác nhận | High:", DoubleToString(g_asianHigh, _Digits),
               " | Low:", DoubleToString(g_asianLow, _Digits),
               " | Size:", rangeSize, " points");
      }
      else
      {
         Print("[EA3] ⚠️ Range quá nhỏ (", rangeSize, " pts) → Bỏ qua hôm nay");
         g_tradedToday = true; // Skip hôm nay
      }
   }

   //--- BƯỚC 3: Đặt lệnh pending Stop Order
   if(g_rangeReady && !g_pendingSet && !g_tradedToday &&
      hour >= InpLondonOpen && hour < InpLondonClose)
   {
      PlacePendingOrders();
   }

   //--- BƯỚC 4: Trailing stop lệnh đang chạy
   if(InpUseTrailing && CountMyPositions() > 0)
      ManageTrailing();

   //--- BƯỚC 5: Đóng phiên London → hủy pending chưa kích hoạt
   if(hour >= InpLondonClose && g_pendingSet)
   {
      CancelPendingOrders();
      g_pendingSet = false;
      Print("[EA3] Phiên London đóng → Hủy lệnh pending");
   }
}

//+------------------------------------------------------------------+
void PlacePendingOrders()
{
   double buyPrice  = NormalizeDouble(g_asianHigh + InpBreakBuffer * _Point, _Digits);
   double sellPrice = NormalizeDouble(g_asianLow  - InpBreakBuffer * _Point, _Digits);

   double curAsk    = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double curBid    = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   // Tính SL/TP
   double buySL, buyTP, sellSL, sellTP;

   if(InpSLAtOpposite)
   {
      buySL  = NormalizeDouble(g_asianLow  - InpSLBuffer * _Point, _Digits);
      sellSL = NormalizeDouble(g_asianHigh + InpSLBuffer * _Point, _Digits);
   }
   else
   {
      buySL  = NormalizeDouble(buyPrice  - InpSLBuffer * _Point * 5, _Digits);
      sellSL = NormalizeDouble(sellPrice + InpSLBuffer * _Point * 5, _Digits);
   }

   double buyRisk  = (buyPrice  - buySL)  / _Point;
   double sellRisk = (sellSL - sellPrice) / _Point;
   buyTP   = NormalizeDouble(buyPrice  + buyRisk  * InpRRRatio * _Point, _Digits);
   sellTP  = NormalizeDouble(sellPrice - sellRisk * InpRRRatio * _Point, _Digits);

   double buyLot  = InpUseAutoLot ? CalcAutoLot(buyRisk)  : InpLotSize;
   double sellLot = InpUseAutoLot ? CalcAutoLot(sellRisk) : InpLotSize;
   buyLot  = NormalizeLot(buyLot);
   sellLot = NormalizeLot(sellLot);

   // Chỉ đặt BUY STOP nếu giá hiện tại chưa chạm
   if(curAsk < buyPrice)
   {
      if(trade.BuyStop(buyLot, buyPrice, _Symbol, buySL, buyTP, 0, 0, "EA3-LondonBreak-BUY"))
      {
         g_buyStopTicket = trade.ResultOrder();
         Print("✅ [EA3] BUY STOP đặt @ ", buyPrice, " | SL:", buySL, " | TP:", buyTP);
      }
   }

   // Chỉ đặt SELL STOP nếu giá hiện tại chưa chạm
   if(curBid > sellPrice)
   {
      if(trade.SellStop(sellLot, sellPrice, _Symbol, sellSL, sellTP, 0, 0, "EA3-LondonBreak-SELL"))
      {
         g_sellStopTicket = trade.ResultOrder();
         Print("✅ [EA3] SELL STOP đặt @ ", sellPrice, " | SL:", sellSL, " | TP:", sellTP);
      }
   }

   g_pendingSet  = true;
   g_tradedToday = true;
}

//+------------------------------------------------------------------+
void CancelPendingOrders()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(!OrderSelect(ticket)) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      if(OrderGetInteger(ORDER_MAGIC) != InpMagicNumber) continue;
      trade.OrderDelete(ticket);
      Print("[EA3] Hủy lệnh pending #", ticket);
   }
}

//+------------------------------------------------------------------+
void ManageTrailing()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC)  != InpMagicNumber) continue;

      ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double curSL = PositionGetDouble(POSITION_SL);
      double curTP = PositionGetDouble(POSITION_TP);

      if(type == POSITION_TYPE_BUY)
      {
         double bid   = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         double newSL = NormalizeDouble(bid - InpTrailPoints * _Point, _Digits);
         if(newSL > curSL + InpTrailStep * _Point)
            trade.PositionModify(ticket, newSL, curTP);
      }
      else if(type == POSITION_TYPE_SELL)
      {
         double ask   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         double newSL = NormalizeDouble(ask + InpTrailPoints * _Point, _Digits);
         if(curSL == 0 || newSL < curSL - InpTrailStep * _Point)
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
