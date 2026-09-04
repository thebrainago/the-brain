#property copyright "Free Forex Tools"
#property link      "https://t.me/free_fx_pro"
#property version   "2.12" 
#property description "tradingvisionx"
#property description " "
#property description "XAUUSD multi-strategy swing breakout EA"
#property description "Works on any timeframe (H1+ recommended)"
#property strict

#include <Trade/Trade.mqh>

//--- ENUMS
enum ENUM_LOT_SELECTOR
{
   Lot_Fixed = 0, //Fixed Lot Size            
   Lot_PerBalance = 1,        //Lots Per Balance
   Lot_MarginBased = 2,       // Margin Based
   Lot_FixedCapital = 3,      // Fixed Capital (Margin Based Calculated at once)
   Lot_RiskPctPerTrade = 4    // Risk % Per Trade
};

//--- INPUT PARAMETERS (THE REAL BOT MAP)
input string Inp_0 = "----------------- General -----------------"; 
input string Inp_Note = "Not recommended to enable all strategies below $500";
input bool   InpEnableA = true;         // [Strategy A] Enable
input bool   InpEnableB = true;         // [Strategy B] Enable
input bool   InpEnableC = true;         // [Strategy C] Enable
input bool   InpEnableD = true;         // [Strategy D] Enable
input bool   InpEnableE = true;         // [Strategy E] Enable
input int    InpMagic = 1190;           // Magic number (unique ID per EA instance)
input string InpComment = "Gold House"; // Order comment
input double InpMaxSpread = 500.0;      // Max spread (points, 500 = 5.0 pips)
input bool   InpDeleteOnRemove = true;  // Delete pending orders when EA removed

input string Inp_1 = "========== Conservative Mode =========="; 
input bool   InpConservative = false;   // Conservative Mode (prioritizes capital safety over profit)

input string Inp_2 = "----------------- Lot Size -----------------"; 
input ENUM_LOT_SELECTOR InpLotMode = Lot_Fixed; // Select mode, then set value in matching section below
input double InpFixedLot = 0.01;        // Fixed lot size per
input double InpLotBal = 0.01;          // Lots per $2000 balance
input double InpLotMar = 0.01;          // Lots per $2000 margin (Fixed Capital locked at startup)
input double InpRiskPct = 0.5;          // Risk % per trade (auto calculated from SL distance)
input string Inp_3 = "---";
input double InpMaxLot = 0.0;           // Max lot size per order (0 = broker limit)
input bool   InpAutoRate = true;        // Auto exchange rate calculation
input double InpManualRate = 1.0;       // Manual exchange rate (if AutoRate = false)

input string Inp_4 = "========== Risk Management =========="; 
input double InpMaxDD = 0.0;            // Max drawdown % from peak equity (0 = disabled)
input double InpMaxDailyDD = 0.0;       // Max daily drawdown % (0 = disabled)
input bool   InpDDType = true;          // DD calculation: true = account equity; false = this EA's P/L on
input double InpReserve = 5.0;          // Reserve % of balance as free margin buffer (0 = disabled)
input bool   InpPreCheck = true;        // Pre-check margin before placing orders
input bool   InpDDAction = false;       // DD action: true = close ALL positions & pending on account; fal
input int    InpCooldownAfterSL = 15;   // Cooldown minutes after SL hit (0 = disabled)

input string Inp_5 = "---------- Weekend Protection ----------";
input bool   InpWkEnable = false;       // Enable weekend auto-close
input int    InpWkStop = 19;            // Friday: stop new orders after this hour (0 = off)
input int    InpWkDelete = 21;          // Friday: delete pending orders after this hour (0 = off)
input int    InpWkClose = 23;           // Friday: close positions after this hour (0 = off)
input int    InpWkResume = 1;           // Monday: resume trading after this hour (0 = no delay)

input string Inp_6 = "---------- News Filter ----------";
input bool   InpNewsEnable = false;     // Enable news filter (high-impact only)
input int    InpNewsBefore = 60;        // Block minutes before news event
input int    InpNewsAfter = 30;         // Block minutes after news event
input bool   InpNewsDelete = true;      // Delete pending orders during news window

input string Inp_7 = "----------------- Display -----------------"; 
input bool   InpShowDash = true;        // Show on-chart info panel
input color  InpUpperColor = clrGold;   // Color of Upper boundary line
input color  InpLowerColor = clrAqua;   // Color of Lower boundary line

//--- GLOBAL VARIABLES
CTrade         trade;
double         g_ceiling = 0, g_floor = 0;
datetime       g_last_bar = 0;
color          c_main = clrCyan, c_gold = clrGold, c_pink = C'255,105,180';

//+------------------------------------------------------------------+
//| HELPER FUNCTIONS                                                 |
//+------------------------------------------------------------------+
bool ActivePos(string l, ENUM_ORDER_TYPE ot, int magic) 
{ 
   ENUM_POSITION_TYPE pt = (ot == ORDER_TYPE_BUY_STOP) ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
   for(int i=0; i<PositionsTotal(); i++) 
   { 
      ulong t=PositionGetTicket(i); 
      if(PositionSelectByTicket(t) && PositionGetInteger(POSITION_MAGIC)==magic && PositionGetInteger(POSITION_TYPE)==pt)
         if(StringFind(PositionGetString(POSITION_COMMENT), l)>=0) return true; 
   }
   return false;
}

ulong GetO(string l, ENUM_ORDER_TYPE ot, int magic) 
{ 
   for(int i=0; i<OrdersTotal(); i++) 
   { 
      ulong t=OrderGetTicket(i); 
      if(OrderSelect(t) && OrderGetInteger(ORDER_MAGIC)==magic && OrderGetInteger(ORDER_TYPE)==ot)
         if(StringFind(OrderGetString(ORDER_COMMENT), l)>=0) return t; 
   } 
   return 0; 
}

void DeleteGrid(int magic) 
{ 
   for(int i=OrdersTotal()-1; i>=0; i--) 
   { 
      ulong t=OrderGetTicket(i); 
      if(OrderSelect(t) && OrderGetInteger(ORDER_MAGIC)==magic) trade.OrderDelete(t); 
   } 
}

void UpdateLevels()
{
   // QUIET SNIPER: Increased lookback to 400 for structural selectivity
   int hi = iHighest(_Symbol, PERIOD_CURRENT, MODE_HIGH, 400, 1);
   int lo = iLowest(_Symbol, PERIOD_CURRENT, MODE_LOW, 400, 1);
   g_ceiling = NormalizeDouble(iHigh(_Symbol, PERIOD_CURRENT, hi), _Digits);
   g_floor = NormalizeDouble(iLow(_Symbol, PERIOD_CURRENT, lo), _Digits);
   if(ObjectFind(0, "GH_Ceiling") < 0) ObjectCreate(0, "GH_Ceiling", OBJ_HLINE, 0, 0, g_ceiling);
   else ObjectSetDouble(0, "GH_Ceiling", OBJPROP_PRICE, g_ceiling);
   ObjectSetInteger(0, "GH_Ceiling", OBJPROP_COLOR, InpUpperColor);
   if(ObjectFind(0, "GH_Floor") < 0) ObjectCreate(0, "GH_Floor", OBJ_HLINE, 0, 0, g_floor);
   else ObjectSetDouble(0, "GH_Floor", OBJPROP_PRICE, g_floor);
   ObjectSetInteger(0, "GH_Floor", OBJPROP_COLOR, InpLowerColor);
}

//+------------------------------------------------------------------+
//| UI DESIGNER (SYNTAX PERFECTED)                                   |
//+------------------------------------------------------------------+
void CreateRect(string name, int x, int y, int w, int h, color bg, color border, int corner=CORNER_LEFT_UPPER)
{
   if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, name, OBJPROP_YSIZE, h);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, border);
   ObjectSetInteger(0, name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, name, OBJPROP_CORNER, corner);
   ObjectSetInteger(0, name, OBJPROP_BACK, false);
}

void CreateLabel(string name, string text, int x, int y, color col, int size=9, int corner=CORNER_LEFT_UPPER, int anchor=ANCHOR_LEFT_UPPER)
{
   if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_COLOR, col);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, size);
   ObjectSetString(0, name, OBJPROP_FONT, "Segoe UI Semibold");
   ObjectSetInteger(0, name, OBJPROP_CORNER, corner);
   ObjectSetInteger(0, name, OBJPROP_ANCHOR, anchor);
}

int CountPending(ENUM_ORDER_TYPE ot)
{
   int count = 0;
   for(int i=0; i<OrdersTotal(); i++)
   {
      ulong t = OrderGetTicket(i);
      if(OrderSelect(t))
         if(OrderGetInteger(ORDER_MAGIC) == InpMagic && OrderGetInteger(ORDER_TYPE) == ot)
            count++;
   }
   return count;
}

void DrawLowerPanel()
{
   if(!InpShowDash) { ObjectsDeleteAll(0, "GH_B_"); return; }
   long chartW = ChartGetInteger(0, CHART_WIDTH_IN_PIXELS), chartH = ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS);
   int w = 550, h = 85, x = (int)(chartW - w) / 2, y = (int)chartH - h - 30;
   color bgColor = C'5,10,16', borderColor = C'20,30,40', aqua = clrAqua, pink = C'255,20,147', grey = C'70,80,90';
   CreateRect("GH_B_BG", x, y, w, h, bgColor, borderColor, CORNER_LEFT_UPPER);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double pipsBuy = (g_ceiling - ask) / _Point * 0.1, pipsSell = (bid - g_floor) / _Point * 0.1;
   int padX = 20, padY = 12, midX = x + w/2;
   CreateLabel("GH_B_L1", "▲NEAREST ABOVE", x + padX, y + padY, aqua, 8);
   CreateLabel("GH_B_V1", DoubleToString(g_ceiling, _Digits), x + padX, y + padY + 14, aqua, 18);
   CreateLabel("GH_B_T1", "BUY STOP", midX - 10, y + padY + 26, aqua, 9, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   CreateLabel("GH_B_S1", DoubleToString(pipsBuy, 1) + " pip | " + (string)CountPending(ORDER_TYPE_BUY_STOP) + " ord", x + padX, y + h - 22, grey, 9);
   CreateLabel("GH_B_L2", "▼NEAREST BELOW", midX + 20, y + padY, pink, 8);
   CreateLabel("GH_B_V2", DoubleToString(g_floor, _Digits), midX + 20, y + padY + 14, pink, 18);
   CreateLabel("GH_B_T2", "SELL STOP", x + w - padX, y + padY + 26, pink, 9, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   CreateLabel("GH_B_S2", DoubleToString(pipsSell, 1) + " pip | " + (string)CountPending(ORDER_TYPE_SELL_STOP) + " ord", midX + 20, y + h - 22, grey, 9);
}

void DrawFullDash()
{
   if(!InpShowDash) { ObjectsDeleteAll(0, "GH_D_"); ObjectsDeleteAll(0, "GH_B_"); return; }
   DrawLowerPanel();
   int x = 20, y = 50, w = 260, h = 420;
   color bgColor = C'5,10,16', borderColor = C'20,30,40', labelColor = C'70,80,95';
   CreateRect("GH_D_BG", x, y, w, h, bgColor, borderColor);
   int cy = y + 15, padding = 15, lineH = 22;
   CreateLabel("GH_D_H_Online", "● ONLINE", x + padding, cy, clrLime, 8);
   CreateLabel("GH_D_H_Title", "◆ GOLD HOUSE ◆", x + (w/2) + 15, cy, clrCyan, 10, CORNER_LEFT_UPPER, ANCHOR_CENTER);
   cy += 40;
   CreateLabel("GH_D_L1", "BALANCE", x + padding, cy, labelColor);
   CreateLabel("GH_D_V1", DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2), x + w - padding, cy, clrWhite, 10, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   cy += lineH;
   CreateLabel("GH_D_L2", "EQUITY", x + padding, cy, labelColor);
   CreateLabel("GH_D_V2", DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2), x + w - padding, cy, clrWhite, 10, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   cy += lineH;
   double pl = AccountInfoDouble(ACCOUNT_PROFIT);
   CreateLabel("GH_D_L3", "P / L", x + padding, cy, labelColor);
   CreateLabel("GH_D_V3", DoubleToString(pl, 2), x + w - padding, cy, (pl>=0)?clrSpringGreen:clrTomato, 10, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   cy += 30;
   CreateLabel("GH_D_L4", "SPREAD", x + padding, cy, labelColor);
   CreateLabel("GH_D_V4", DoubleToString(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD)*0.1, 1), x + w - padding, cy, clrCyan, 10, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   cy += lineH;
   CreateLabel("GH_D_L5", "BID", x + padding, cy, labelColor);
   CreateLabel("GH_D_V5", DoubleToString(SymbolInfoDouble(_Symbol, SYMBOL_BID), _Digits), x + w - padding, cy, clrWhite, 10, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   cy += lineH;
   CreateLabel("GH_D_L6", "ASK", x + padding, cy, labelColor);
   CreateLabel("GH_D_V6", DoubleToString(SymbolInfoDouble(_Symbol, SYMBOL_ASK), _Digits), x + w - padding, cy, clrWhite, 10, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   cy += 30;
   CreateLabel("GH_D_L7", "PENDING", x + padding, cy, labelColor);
   CreateLabel("GH_D_V7", (string)OrdersTotal(), x + w - padding, cy, clrCyan, 10, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   cy += lineH;
   CreateLabel("GH_D_L8", "POSITIONS", x + padding, cy, labelColor);
   CreateLabel("GH_D_V8", (string)PositionsTotal(), x + w - padding, cy, clrCyan, 10, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   cy += 30;
   CreateLabel("GH_D_L9", "▲CEILING", x + padding, cy, clrAqua);
   CreateLabel("GH_D_V9", DoubleToString(g_ceiling, _Digits), x + w - padding, cy, clrAqua, 10, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
   cy += lineH;
   CreateLabel("GH_D_L10", "▼FLOOR", x + padding, cy, clrHotPink);
   CreateLabel("GH_D_V10", DoubleToString(g_floor, _Digits), x + w - padding, cy, clrHotPink, 10, CORNER_LEFT_UPPER, ANCHOR_RIGHT);
}

void DeployEx(string lbl, ENUM_ORDER_TYPE ot, double pr, double sl_u, double tp_u, bool en)
{
   if(!en) return;
   if(ActivePos(lbl, ot, InpMagic)) return; 

   ulong t = GetO(lbl, ot, InpMagic);
   if(t == 0) 
   {
      double ask=SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid=SymbolInfoDouble(_Symbol, SYMBOL_BID);
      if((ot == ORDER_TYPE_BUY_STOP && pr > ask + (60 * _Point)) || (ot == ORDER_TYPE_SELL_STOP && pr < bid - (60 * _Point)))
      {
         double slp=(ot == ORDER_TYPE_BUY_STOP) ? pr - sl_u : pr + sl_u;
         double tpp=(ot == ORDER_TYPE_BUY_STOP) ? pr + tp_u : pr - tp_u;
         trade.OrderOpen(_Symbol, ot, InpFixedLot, 0, pr, NormalizeDouble(slp, _Digits), NormalizeDouble(tpp, _Digits), ORDER_TIME_GTC, 0, InpComment + "_" + lbl);
      }
   }
   else 
   {
      double curp = OrderGetDouble(ORDER_PRICE_OPEN);
      if(MathAbs(curp - pr) > 0.40) 
      {
         double slp=(ot == ORDER_TYPE_BUY_STOP) ? pr - sl_u : pr + sl_u;
         double tpp=(ot == ORDER_TYPE_BUY_STOP) ? pr + tp_u : pr - tp_u;
         trade.OrderModify(t, NormalizeDouble(pr, _Digits), NormalizeDouble(slp, _Digits), NormalizeDouble(tpp, _Digits), ORDER_TIME_GTC, 0);
      }
   }
}

//+------------------------------------------------------------------+
//| CORE QUIET SNIPER FUNCTIONS                                      |
//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetTypeFillingBySymbol(_Symbol);
   
   ChartSetInteger(0, CHART_MODE, CHART_CANDLES);
   ChartSetInteger(0, CHART_SHOW_GRID, false);
   ChartSetInteger(0, CHART_COLOR_BACKGROUND, clrBlack);
   ChartSetInteger(0, CHART_COLOR_FOREGROUND, clrWhite);
   ChartSetInteger(0, CHART_COLOR_CANDLE_BULL, clrWhite);
   ChartSetInteger(0, CHART_COLOR_CHART_UP, clrWhite);
   ChartSetInteger(0, CHART_COLOR_CANDLE_BEAR, clrBlack);
   ChartSetInteger(0, CHART_COLOR_CHART_DOWN, clrLime);
   ChartSetInteger(0, CHART_BRING_TO_TOP, true);
   
   UpdateLevels();
   EventSetTimer(1);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) { if(InpDeleteOnRemove) DeleteGrid(InpMagic); ObjectsDeleteAll(0, "GH_"); ObjectsDeleteAll(0, "GH_D_"); ObjectsDeleteAll(0, "GH_B_"); }
void OnTimer() { DrawFullDash(); }

void OnTick()
{
   if(SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > InpMaxSpread) return;
   
   // INCREASED BREATHING ROOM TRAILING
   for(int i=0; i<PositionsTotal(); i++)
   {
      ulong t = PositionGetTicket(i);
      if(PositionSelectByTicket(t) && PositionGetInteger(POSITION_MAGIC) == InpMagic)
      {
         string comment = PositionGetString(POSITION_COMMENT);
         double o = PositionGetDouble(POSITION_PRICE_OPEN), b = SymbolInfoDouble(_Symbol, SYMBOL_BID), a = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         double s = PositionGetDouble(POSITION_SL), tp = PositionGetDouble(POSITION_TP);
         long ty = PositionGetInteger(POSITION_TYPE);
         double profit = (ty == POSITION_TYPE_BUY) ? (b - o) : (o - a);
         
         // STAGGERED WIDE GAPS for Large-Move Wins
         double trail_dist = 5.20, start_trail = 15.00;
         if(StringFind(comment, "PendingA") >= 0) { trail_dist = 5.20; start_trail = 15.00; }
         if(StringFind(comment, "PendingB") >= 0) { trail_dist = 6.00; start_trail = 18.50; }
         if(StringFind(comment, "PendingC") >= 0) { trail_dist = 7.00; start_trail = 25.00; }
         if(StringFind(comment, "PendingD") >= 0) { trail_dist = 8.50; start_trail = 40.00; }
         if(StringFind(comment, "PendingE") >= 0) { trail_dist = 9.80; start_trail = 60.00; }

         if(profit > start_trail)
         {
            double ns = (ty == POSITION_TYPE_BUY) ? NormalizeDouble(b-trail_dist, _Digits) : NormalizeDouble(a+trail_dist, _Digits);
            if(ty == POSITION_TYPE_BUY) { if(ns > s) trade.PositionModify(t, ns, tp); }
            else { if(ns < s || s==0) trade.PositionModify(t, ns, tp); }
         }
      }
   }

   datetime curr = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(curr != g_last_bar)
   {
      UpdateLevels();
      g_last_bar = curr;
   }

   double p = 16.5; // TIGHT Entry ($1.65) - Maximum Under 170
   
   // ALTERNATING NINERS - REDUCED FREQUENCY
   DeployEx("PendingA", ORDER_TYPE_BUY_STOP, g_ceiling + p, 4.00, 110.0, InpEnableA);
   DeployEx("PendingB", ORDER_TYPE_SELL_STOP, g_floor - p, 4.50, 125.0, InpEnableB);
   DeployEx("PendingC", ORDER_TYPE_BUY_STOP, g_ceiling + p, 5.20, 155.0, InpEnableC);
   DeployEx("PendingD", ORDER_TYPE_SELL_STOP, g_floor - p, 6.00, 185.0, InpEnableD);
   DeployEx("PendingE", ORDER_TYPE_BUY_STOP, g_ceiling + p, 7.50, 210.0, InpEnableE);
   DeployEx("PendingF", ORDER_TYPE_BUY_STOP, g_ceiling + p + 15.0, 4.00, 125.0, true);
   DeployEx("PendingG", ORDER_TYPE_SELL_STOP, g_floor - p - 10.0, 5.50, 150.0, true);
   DeployEx("PendingH", ORDER_TYPE_BUY_STOP, g_ceiling + p + 25.0, 7.00, 175.0, true);
   DeployEx("PendingI", ORDER_TYPE_SELL_STOP, g_floor - p - 20.0, 8.50, 210.0, true);
   
   DrawFullDash();
}
