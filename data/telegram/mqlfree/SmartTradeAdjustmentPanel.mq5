//+------------------------------------------------------------------+
//|                                SmartTradeAdjustmentPanel.mq5     |
//|                                  Copyright 2026, Professional    |
//|                                       https://www.mql5.com       |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026"
#property link      "https://www.mql5.com"
#property version   "1.00"
#property description "Professional On-Chart Trade Management Panel for MQL5."
#property description "Manages existing manual and EA positions without opening new trades."

#include <Trade\Trade.mqh>

//--- Enums for Filtering Options
enum ENUM_SYMBOL_FILTER
  {
   FILTER_CURRENT_SYMBOL, // Current Symbol Only
   FILTER_ALL_SYMBOLS     // All Symbols
  };

enum ENUM_DIRECTION_FILTER
  {
   FILTER_BOTH_DIRECTIONS,// Buy and Sell
   FILTER_BUY_ONLY,       // Buy Only
   FILTER_SELL_ONLY       // Sell Only
  };

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                 |
//+------------------------------------------------------------------+
input group "=== Trade Management Defaults ==="
input int    InpBEPointOffset      = 10;   // Break-Even Offset (Points)
input int    InpTrailingStopDist   = 200;  // Trailing Stop Distance (Points)
input int    InpLockProfitPoints   = 50;   // Lock-in Profit Amount (Points)

input group "=== Risk : Reward Ratios ==="
input double InpRR_1               = 1.0;  // Take Profit Multiple 1 (1R)
input double InpRR_2               = 2.0;  // Take Profit Multiple 2 (2R)
input double InpRR_3               = 3.0;  // Take Profit Multiple 3 (3R)

input group "=== Safety & Panel Setup ==="
input bool   InpConfirmActions     = true; // Show Confirmation Dialogs
input int    InpPanelX             = 20;   // Panel Initial X Position
input int    InpPanelY             = 50;   // Panel Initial Y Position

//+------------------------------------------------------------------+
//| CLASS: CTradeManager (Handles Execution & Validations)          |
//+------------------------------------------------------------------+
class CTradeManager
  {
private:
   CTrade            m_trade;

   bool              PassesFilter(const ulong ticket, const ENUM_SYMBOL_FILTER symFilter, const ENUM_DIRECTION_FILTER dirFilter);
   bool              ValidateStopLevels(const string symbol, const double price, const double sl, const double tp);

public:
                     CTradeManager() {}
                    ~CTradeManager() {}

   // Core Trade Operations
   void              MoveToBreakEven(ENUM_SYMBOL_FILTER symFilter, ENUM_DIRECTION_FILTER dirFilter, int offsetPoints = 0);
   void              LockProfit(ENUM_SYMBOL_FILTER symFilter, ENUM_DIRECTION_FILTER dirFilter, int profitPoints);
   void              ApplyTrailingStop(ENUM_SYMBOL_FILTER symFilter, ENUM_DIRECTION_FILTER dirFilter, int trailPoints);
   void              SetTakeProfitRR(ENUM_SYMBOL_FILTER symFilter, ENUM_DIRECTION_FILTER dirFilter, double rrMultiple);
   void              PartiallyClose(ENUM_SYMBOL_FILTER symFilter, ENUM_DIRECTION_FILTER dirFilter, double percentage);
  };

//--- Filter check for symbol & direction
bool CTradeManager::PassesFilter(const ulong ticket, const ENUM_SYMBOL_FILTER symFilter, const ENUM_DIRECTION_FILTER dirFilter)
  {
   if(!PositionSelectByTicket(ticket))
      return false;

   string symbol = PositionGetString(POSITION_SYMBOL);
   long type     = PositionGetInteger(POSITION_TYPE);

   if(symFilter == FILTER_CURRENT_SYMBOL && symbol != _Symbol)
      return false;
   if(dirFilter == FILTER_BUY_ONLY && type != POSITION_TYPE_BUY)
      return false;
   if(dirFilter == FILTER_SELL_ONLY && type != POSITION_TYPE_SELL)
      return false;

   return true;
  }

//--- Ensure SL/TP satisfy broker StopLevel restrictions
bool CTradeManager::ValidateStopLevels(const string symbol, const double price, const double sl, const double tp)
  {
   long stopLevel = SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   double minDistance = stopLevel * point;

   if(sl > 0 && MathAbs(price - sl) < minDistance)
      return false;
   if(tp > 0 && MathAbs(price - tp) < minDistance)
      return false;

   return true;
  }

//--- Break Even / Offset execution
void CTradeManager::MoveToBreakEven(ENUM_SYMBOL_FILTER symFilter, ENUM_DIRECTION_FILTER dirFilter, int offsetPoints = 0)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(!PassesFilter(ticket, symFilter, dirFilter))
         continue;

      string symbol   = PositionGetString(POSITION_SYMBOL);
      long type       = PositionGetInteger(POSITION_TYPE);
      double openPrice= PositionGetDouble(POSITION_PRICE_OPEN);
      double currentSL= PositionGetDouble(POSITION_SL);
      double currentTP= PositionGetDouble(POSITION_TP);
      double point    = SymbolInfoDouble(symbol, SYMBOL_POINT);
      int digits      = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

      double newSL = 0.0;
      if(type == POSITION_TYPE_BUY)
        {
         newSL = NormalizeDouble(openPrice + (offsetPoints * point), digits);
         double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
         if(bid <= newSL || (currentSL >= newSL && currentSL != 0))
            continue;
        }
      else
         if(type == POSITION_TYPE_SELL)
           {
            newSL = NormalizeDouble(openPrice - (offsetPoints * point), digits);
            double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
            if(ask >= newSL || (currentSL <= newSL && currentSL != 0))
               continue;
           }

      if(ValidateStopLevels(symbol, (type == POSITION_TYPE_BUY ? SymbolInfoDouble(symbol, SYMBOL_BID) : SymbolInfoDouble(symbol, SYMBOL_ASK)), newSL, currentTP))
        {
         if(m_trade.PositionModify(ticket, newSL, currentTP))
            PrintFormat("Ticket #%d BreakEven updated to %.*f", ticket, digits, newSL);
         else
            PrintFormat("Error updating BreakEven for #%d: %d", ticket, m_trade.ResultRetcode());
        }
     }
  }

//--- Lock In Specified Profit Points
void CTradeManager::LockProfit(ENUM_SYMBOL_FILTER symFilter, ENUM_DIRECTION_FILTER dirFilter, int profitPoints)
  {
   MoveToBreakEven(symFilter, dirFilter, profitPoints);
  }

//--- Trailing Stop Execution
void CTradeManager::ApplyTrailingStop(ENUM_SYMBOL_FILTER symFilter, ENUM_DIRECTION_FILTER dirFilter, int trailPoints)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(!PassesFilter(ticket, symFilter, dirFilter))
         continue;

      string symbol   = PositionGetString(POSITION_SYMBOL);
      long type       = PositionGetInteger(POSITION_TYPE);
      double currentSL= PositionGetDouble(POSITION_SL);
      double currentTP= PositionGetDouble(POSITION_TP);
      double point    = SymbolInfoDouble(symbol, SYMBOL_POINT);
      int digits      = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

      if(type == POSITION_TYPE_BUY)
        {
         double price = SymbolInfoDouble(symbol, SYMBOL_BID);
         double newSL = NormalizeDouble(price - (trailPoints * point), digits);

         if(newSL > currentSL && ValidateStopLevels(symbol, price, newSL, currentTP))
           {
            m_trade.PositionModify(ticket, newSL, currentTP);
           }
        }
      else
         if(type == POSITION_TYPE_SELL)
           {
            double price = SymbolInfoDouble(symbol, SYMBOL_ASK);
            double newSL = NormalizeDouble(price + (trailPoints * point), digits);

            if((newSL < currentSL || currentSL == 0) && ValidateStopLevels(symbol, price, newSL, currentTP))
              {
               m_trade.PositionModify(ticket, newSL, currentTP);
              }
           }
     }
  }

//--- Take Profit by Risk-Reward Multipliers
void CTradeManager::SetTakeProfitRR(ENUM_SYMBOL_FILTER symFilter, ENUM_DIRECTION_FILTER dirFilter, double rrMultiple)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(!PassesFilter(ticket, symFilter, dirFilter))
         continue;

      string symbol   = PositionGetString(POSITION_SYMBOL);
      long type       = PositionGetInteger(POSITION_TYPE);
      double openPrice= PositionGetDouble(POSITION_PRICE_OPEN);
      double currentSL= PositionGetDouble(POSITION_SL);
      int digits      = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

      if(currentSL == 0)
        {
         PrintFormat("Ticket #%d has no SL. Cannot compute %G R/R Take Profit.", ticket, rrMultiple);
         continue;
        }

      double riskDistance = MathAbs(openPrice - currentSL);
      double rewardDistance = riskDistance * rrMultiple;
      double newTP = 0.0;

      if(type == POSITION_TYPE_BUY)
         newTP = NormalizeDouble(openPrice + rewardDistance, digits);
      else
         newTP = NormalizeDouble(openPrice - rewardDistance, digits);

      if(ValidateStopLevels(symbol, openPrice, currentSL, newTP))
        {
         if(m_trade.PositionModify(ticket, currentSL, newTP))
            PrintFormat("Ticket #%d TP set to %.*f (%GR)", ticket, digits, newTP, rrMultiple);
        }
     }
  }

//--- Partial Close Logic
void CTradeManager::PartiallyClose(ENUM_SYMBOL_FILTER symFilter, ENUM_DIRECTION_FILTER dirFilter, double percentage)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(!PassesFilter(ticket, symFilter, dirFilter))
         continue;

      string symbol  = PositionGetString(POSITION_SYMBOL);
      double vol     = PositionGetDouble(POSITION_VOLUME);
      double stepVol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
      double minVol  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);

      double rawCloseVol = vol * (percentage / 100.0);
      double closeVol    = MathFloor(rawCloseVol / stepVol) * stepVol;

      if(closeVol < minVol)
        {
         if(percentage >= 100.0 || vol <= minVol)
            closeVol = vol; // Close entirely
         else
           {
            PrintFormat("Calculated volume (%.2f) below broker minimum (%.2f) for #%d.", closeVol, minVol, ticket);
            continue;
           }
        }

      if(m_trade.PositionClosePartial(ticket, closeVol))
         PrintFormat("Closed %.2f lots on Ticket #%d (%.0f%%)", closeVol, ticket, percentage);
      else
         PrintFormat("Failed partial close on Ticket #%d. Code: %d", ticket, m_trade.ResultRetcode());
     }
  }

//+------------------------------------------------------------------+
//| CLASS: CTradePanelGUI (Graphical Interface Logic)               |
//+------------------------------------------------------------------+
class CTradePanelGUI
  {
private:
   string            m_prefix;
   int               m_x, m_y;
   int               m_width, m_height;
   bool              m_isMinimized;
   bool              m_isDragging;
   int               m_dragX, m_dragY;

   // Filter States
   ENUM_SYMBOL_FILTER    m_symFilter;
   ENUM_DIRECTION_FILTER m_dirFilter;

   // Helper GUI Object Creators
   void              CreateLabel(string name, string text, int x, int y, color clr, int size = 8, bool bold = false);
   void              CreateButton(string name, string text, int x, int y, int w, int h, color bgClr, color txtClr = clrWhite);
   void              CreateRect(string name, int x, int y, int w, int h, color bgClr, color borderClr);

public:
                     CTradePanelGUI();
                    ~CTradePanelGUI();

   void              Init(int x, int y);
   void              Destroy();
   void              Render();
   void              OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam, CTradeManager &tradeMgr);

   // Getters for filters
   ENUM_SYMBOL_FILTER    GetSymbolFilter()    { return m_symFilter; }
   ENUM_DIRECTION_FILTER GetDirectionFilter() { return m_dirFilter; }
  };


CTradePanelGUI::CTradePanelGUI() : m_prefix("STAP_"), m_x(20), m_y(50), m_width(220), m_height(340),
   m_isMinimized(false), m_isDragging(false),
   m_symFilter(FILTER_CURRENT_SYMBOL), m_dirFilter(FILTER_BOTH_DIRECTIONS) {}

CTradePanelGUI::~CTradePanelGUI() { Destroy(); }


void CTradePanelGUI::Init(int x, int y)
  {
   m_x = x;
   m_y = y;
   Render();
  }


void CTradePanelGUI::Destroy()
  {
   ObjectsDeleteAll(0, m_prefix);
   ChartRedraw(0);
  }


void CTradePanelGUI::CreateRect(string name, int x, int y, int w, int h, color bgClr, color borderClr)
  {
   string objName = m_prefix + name;
   ObjectCreate(0, objName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, objName, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, objName, OBJPROP_YSIZE, h);
   ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, bgClr);
   ObjectSetInteger(0, objName, OBJPROP_COLOR, borderClr);
   ObjectSetInteger(0, objName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, objName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
  }


void CTradePanelGUI::CreateLabel(string name, string text, int x, int y, color clr, int size, bool bold)
  {
   string objName = m_prefix + name;
   ObjectCreate(0, objName, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, objName, OBJPROP_TEXT, text);
   ObjectSetInteger(0, objName, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, objName, OBJPROP_FONTSIZE, size);
   ObjectSetString(0, objName, OBJPROP_FONT, bold ? "Arial Bold" : "Arial");
   ObjectSetInteger(0, objName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
  }


void CTradePanelGUI::CreateButton(string name, string text, int x, int y, int w, int h, color bgClr, color txtClr)
  {
   string objName = m_prefix + name;
   ObjectCreate(0, objName, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, objName, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, objName, OBJPROP_YSIZE, h);
   ObjectSetString(0, objName, OBJPROP_TEXT, text);
   ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, bgClr);
   ObjectSetInteger(0, objName, OBJPROP_COLOR, txtClr);
   ObjectSetInteger(0, objName, OBJPROP_FONTSIZE, 8);
   ObjectSetString(0, objName, OBJPROP_FONT, "Arial Bold");
   ObjectSetInteger(0, objName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
  }

//--- Render the entire panel
void CTradePanelGUI::Render()
  {
   Destroy();

// Palette Definitions
   color headerBg    = C'30,34,45';
   color panelBg     = C'20,22,30';
   color borderClr   = C'50,55,70';
   color btnBg       = C'40,46,60';
   color btnAccent   = C'0,122,255';
   color btnWarn     = C'220,53,69';

// 1. Title Bar (Always Visible)
   CreateRect("Header", m_x, m_y, m_width, 26, headerBg, borderClr);
   CreateLabel("Title", "Smart Trade Adjustment Panel", m_x + 8, m_y + 6, clrWhite, 8, true);
   CreateButton("BtnMin", m_isMinimized ? "+" : "_", m_x + m_width - 38, m_y + 3, 16, 18, headerBg, clrSilver);
   CreateButton("BtnClose", "X", m_x + m_width - 20, m_y + 3, 16, 18, headerBg, clrTomato);

   if(m_isMinimized)
      return;

// 2. Main Window Body
   CreateRect("Body", m_x, m_y + 26, m_width, m_height - 26, panelBg, borderClr);

   int y = m_y + 32;

// 3. Section: Filters
   CreateLabel("lbl_Filter", "--- FILTERS ---", m_x + 70, y, clrGray, 7);
   y += 16;
   CreateButton("FltSym", m_symFilter == FILTER_CURRENT_SYMBOL ? "Sym: Current" : "Sym: All", m_x + 10, y, 98, 20, btnBg, clrYellow);
   CreateButton("FltDir", m_dirFilter == FILTER_BOTH_DIRECTIONS ? "Dir: Both" : (m_dirFilter == FILTER_BUY_ONLY ? "Dir: Buy Only" : "Dir: Sell Only"), m_x + 112, y, 98, 20, btnBg, clrYellow);
   y += 26;

// 4. Section: Stop Loss Controls
   CreateLabel("lbl_SL", "--- STOP LOSS CONTROLS ---", m_x + 40, y, clrGray, 7);
   y += 16;
   CreateButton("BtnBE", "Break Even (BE)", m_x + 10, y, 98, 22, btnBg);
   CreateButton("BtnBEOffset", StringFormat("BE + %dP", InpBEPointOffset), m_x + 112, y, 98, 22, btnBg);
   y += 25;
   CreateButton("BtnTrail", StringFormat("Trail Stop (%dP)", InpTrailingStopDist), m_x + 10, y, 98, 22, btnBg);
   CreateButton("BtnLock", StringFormat("Lock Prof (%dP)", InpLockProfitPoints), m_x + 112, y, 98, 22, btnBg);
   y += 28;

// 5. Section: Take Profit R/R
   CreateLabel("lbl_TP", "--- TAKE PROFIT (R/R) ---", m_x + 45, y, clrGray, 7);
   y += 16;
   CreateButton("BtnRR1", StringFormat("%.1f R", InpRR_1), m_x + 10, y, 62, 22, btnBg);
   CreateButton("BtnRR2", StringFormat("%.1f R", InpRR_2), m_x + 78, y, 64, 22, btnBg);
   CreateButton("BtnRR3", StringFormat("%.1f R", InpRR_3), m_x + 146, y, 64, 22, btnBg);
   y += 28;

// 6. Section: Partial Closes
   CreateLabel("lbl_Close", "--- PARTIAL / FULL CLOSE ---", m_x + 35, y, clrGray, 7);
   y += 16;
   CreateButton("BtnClose25", "Close 25%", m_x + 10, y, 98, 22, btnAccent);
   CreateButton("BtnClose50", "Close 50%", m_x + 112, y, 98, 22, btnAccent);
   y += 25;
   CreateButton("BtnClose75", "Close 75%", m_x + 10, y, 98, 22, btnAccent);
   CreateButton("BtnClose100", "Close 100%", m_x + 112, y, 98, 22, btnWarn);

   ChartRedraw(0);
  }

//--- Interactive Chart Events Handler
void CTradePanelGUI::OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam, CTradeManager &tradeMgr)
  {
// --- Window Dragging Logic ---
   if(id == CHARTEVENT_CLICK)
     {
      if(sparam == m_prefix + "Header")
        {
         m_isDragging = true;
         m_dragX = (int)lparam - m_x;
         m_dragY = (int)dparam - m_y;
        }
      else
        {
         m_isDragging = false;
        }
     }

   if(id == CHARTEVENT_MOUSE_MOVE && (uint)dparam == 1) // Left Mouse Button Down
     {
      if(m_isDragging)
        {
         m_x = (int)lparam - m_dragX;
         m_y = (int)dparam - m_dragY;
         Render();
         return;
        }
     }
   else
     {
      m_isDragging = false;
     }

// --- Button Actions Logic ---
   if(id == CHARTEVENT_OBJECT_CLICK)
     {
      // Reset button state visually immediately
      ObjectSetInteger(0, sparam, OBJPROP_STATE, false);

      if(sparam == m_prefix + "BtnMin")
        {
         m_isMinimized = !m_isMinimized;
         Render();
         return;
        }
      if(sparam == m_prefix + "BtnClose")
        {
         Destroy();
         ExpertRemove();
         return;
        }

      // Filter Toggle Switches
      if(sparam == m_prefix + "FltSym")
        {
         m_symFilter = (m_symFilter == FILTER_CURRENT_SYMBOL) ? FILTER_ALL_SYMBOLS : FILTER_CURRENT_SYMBOL;
         Render();
         return;
        }
      if(sparam == m_prefix + "FltDir")
        {
         if(m_dirFilter == FILTER_BOTH_DIRECTIONS)
            m_dirFilter = FILTER_BUY_ONLY;
         else
            if(m_dirFilter == FILTER_BUY_ONLY)
               m_dirFilter = FILTER_SELL_ONLY;
            else
               m_dirFilter = FILTER_BOTH_DIRECTIONS;
         Render();
         return;
        }

      // Action Dialog Confirmation Utility
      if(InpConfirmActions)
        {
         if(MessageBox("Are you sure you want to execute this trade action?", "Smart Panel Action Confirmation", MB_YESNO | MB_ICONQUESTION) != IDYES)
            return;
        }

      // Execute Trade Adjustments
      if(sparam == m_prefix + "BtnBE")
         tradeMgr.MoveToBreakEven(m_symFilter, m_dirFilter, 0);
      if(sparam == m_prefix + "BtnBEOffset")
         tradeMgr.MoveToBreakEven(m_symFilter, m_dirFilter, InpBEPointOffset);
      if(sparam == m_prefix + "BtnTrail")
         tradeMgr.ApplyTrailingStop(m_symFilter, m_dirFilter, InpTrailingStopDist);
      if(sparam == m_prefix + "BtnLock")
         tradeMgr.LockProfit(m_symFilter, m_dirFilter, InpLockProfitPoints);

      if(sparam == m_prefix + "BtnRR1")
         tradeMgr.SetTakeProfitRR(m_symFilter, m_dirFilter, InpRR_1);
      if(sparam == m_prefix + "BtnRR2")
         tradeMgr.SetTakeProfitRR(m_symFilter, m_dirFilter, InpRR_2);
      if(sparam == m_prefix + "BtnRR3")
         tradeMgr.SetTakeProfitRR(m_symFilter, m_dirFilter, InpRR_3);

      if(sparam == m_prefix + "BtnClose25")
         tradeMgr.PartiallyClose(m_symFilter, m_dirFilter, 25.0);
      if(sparam == m_prefix + "BtnClose50")
         tradeMgr.PartiallyClose(m_symFilter, m_dirFilter, 50.0);
      if(sparam == m_prefix + "BtnClose75")
         tradeMgr.PartiallyClose(m_symFilter, m_dirFilter, 75.0);
      if(sparam == m_prefix + "BtnClose100")
         tradeMgr.PartiallyClose(m_symFilter, m_dirFilter, 100.0);
     }
  }

//+------------------------------------------------------------------+
//| GLOBAL OBJECT INSTANCES & EA HANDLERS                            |
//+------------------------------------------------------------------+
CTradeManager g_TradeManager;
CTradePanelGUI g_PanelGUI;
datetime       g_lastRefresh = 0;

//+------------------------------------------------------------------+
//| Expert Initialization Function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   ChartSetInteger(0, CHART_EVENT_MOUSE_MOVE, true);
   g_PanelGUI.Init(InpPanelX, InpPanelY);
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert Deinitialization Function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   g_PanelGUI.Destroy();
  }

//+------------------------------------------------------------------+
//| Expert Tick Function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
// Lightweight refresh logic (Runs at most once every 2 seconds to optimize CPU usage)
   datetime now = TimeCurrent();
   if(now - g_lastRefresh >= 2)
     {
      g_lastRefresh = now;
      // Auto-trailing execution if enabled/required can be driven here
     }
  }

//+------------------------------------------------------------------+
//| ChartEvent Function                                              |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
  {
   g_PanelGUI.OnChartEvent(id, lparam, dparam, sparam, g_TradeManager);
  }
//+------------------------------------------------------------------+
