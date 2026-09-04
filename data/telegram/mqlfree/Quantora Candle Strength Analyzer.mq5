//+------------------------------------------------------------------+
//|             Quantora Candle Strength Analyzer MT5                |
//|          Professional Candle Pressure Monitor v1.00              |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026 Quantora"
#property link      "https://www.mql5.com/en/users/quantora/seller"
#property version   "1.00"
#property strict
#property indicator_chart_window
#property indicator_plots 0
#property description "Analyzes candle body, upper/lower wick and buyer/seller pressure."
#property description "Professional candle strength dashboard for MetaTrader 5."

input group "========== ANALYSIS SETTINGS =========="
input int    InpLookbackBars       = 20;
input double InpStrongBodyPercent  = 65.0;
input double InpWeakBodyPercent    = 30.0;
input double InpDominantWickRatio  = 45.0;
input bool   InpUseCurrentCandle   = true;

input group "========== DASHBOARD =========="
input bool             InpShowPanel    = true;
input ENUM_BASE_CORNER InpPanelCorner  = CORNER_LEFT_UPPER;
input int              InpPanelX       = 15;
input int              InpPanelY       = 145;
input int              InpTimerSeconds = 2;

#define Q_BG      C'8,23,38'
#define Q_GOLD    C'212,175,55'
#define Q_WHITE   C'245,245,245'
#define Q_GRAY    C'169,176,184'
#define Q_GREEN   C'0,200,83'
#define Q_YELLOW  C'255,193,7'
#define Q_ORANGE  C'255,152,0'
#define Q_RED     C'255,82,82'
#define Q_BLUE    C'32,93,145'
#define Q_BORDER  C'62,76,89'

string g_prefix="QCSA5_";

double g_open=0.0,g_high=0.0,g_low=0.0,g_close=0.0;
double g_range=0.0,g_body=0.0,g_upper=0.0,g_lower=0.0;
double g_body_pct=0.0,g_upper_pct=0.0,g_lower_pct=0.0;
double g_buy_pressure=50.0,g_sell_pressure=50.0;
double g_avg_range=0.0,g_range_ratio=0.0;
double g_bid=0.0,g_ask=0.0,g_spread=0.0;

string g_direction="NEUTRAL";
string g_strength="NEUTRAL";
string g_wick_signal="BALANCED";
string g_pressure="BALANCED";
string g_range_state="NORMAL";
int g_score=0;

color StateColor(string s)
{
   if(StringFind(s,"BULL")>=0 || StringFind(s,"BUY")>=0) return Q_GREEN;
   if(StringFind(s,"BEAR")>=0 || StringFind(s,"SELL")>=0) return Q_RED;
   if(StringFind(s,"REJECTION")>=0) return Q_ORANGE;
   return Q_YELLOW;
}

void AnalyzeCandle()
{
   int shift=(InpUseCurrentCandle ? 0 : 1);

   double o[1],h[1],l[1],c[1];
   if(CopyOpen(_Symbol,(ENUM_TIMEFRAMES)_Period,shift,1,o)!=1 ||
      CopyHigh(_Symbol,(ENUM_TIMEFRAMES)_Period,shift,1,h)!=1 ||
      CopyLow(_Symbol,(ENUM_TIMEFRAMES)_Period,shift,1,l)!=1 ||
      CopyClose(_Symbol,(ENUM_TIMEFRAMES)_Period,shift,1,c)!=1)
      return;

   g_open=o[0]; g_high=h[0]; g_low=l[0]; g_close=c[0];
   g_range=g_high-g_low;
   g_body=MathAbs(g_close-g_open);

   if(g_close>=g_open)
   {
      g_upper=g_high-g_close;
      g_lower=g_open-g_low;
      g_direction=(g_close>g_open ? "BULLISH" : "NEUTRAL");
   }
   else
   {
      g_upper=g_high-g_open;
      g_lower=g_close-g_low;
      g_direction="BEARISH";
   }

   g_upper=MathMax(0.0,g_upper);
   g_lower=MathMax(0.0,g_lower);

   if(g_range>0.0)
   {
      g_body_pct=(g_body/g_range)*100.0;
      g_upper_pct=(g_upper/g_range)*100.0;
      g_lower_pct=(g_lower/g_range)*100.0;

      // Close location in candle range = simple buyer/seller pressure proxy.
      g_buy_pressure=((g_close-g_low)/g_range)*100.0;
      g_buy_pressure=MathMax(0.0,MathMin(100.0,g_buy_pressure));
      g_sell_pressure=100.0-g_buy_pressure;
   }
   else
   {
      g_body_pct=0.0;
      g_upper_pct=0.0;
      g_lower_pct=0.0;
      g_buy_pressure=50.0;
      g_sell_pressure=50.0;
   }

   if(g_body_pct>=InpStrongBodyPercent)
      g_strength=(g_direction=="BULLISH" ? "STRONG BULLISH" :
                  g_direction=="BEARISH" ? "STRONG BEARISH" : "NEUTRAL");
   else if(g_body_pct<=InpWeakBodyPercent)
      g_strength="WEAK / INDECISION";
   else
      g_strength=(g_direction=="BULLISH" ? "MODERATE BULLISH" :
                  g_direction=="BEARISH" ? "MODERATE BEARISH" : "NEUTRAL");

   if(g_upper_pct>=InpDominantWickRatio && g_upper_pct>g_lower_pct)
      g_wick_signal="UPPER REJECTION";
   else if(g_lower_pct>=InpDominantWickRatio && g_lower_pct>g_upper_pct)
      g_wick_signal="LOWER REJECTION";
   else
      g_wick_signal="BALANCED";

   if(g_buy_pressure>=65.0)
      g_pressure="BUYERS DOMINANT";
   else if(g_sell_pressure>=65.0)
      g_pressure="SELLERS DOMINANT";
   else
      g_pressure="BALANCED";

   // Average range over completed candles.
   g_avg_range=0.0;
   int valid=0;
   for(int i=1;i<=InpLookbackBars;i++)
   {
      double hi[1],lo[1];
      if(CopyHigh(_Symbol,(ENUM_TIMEFRAMES)_Period,i,1,hi)==1 &&
         CopyLow(_Symbol,(ENUM_TIMEFRAMES)_Period,i,1,lo)==1)
      {
         double r=hi[0]-lo[0];
         if(r>0.0)
         {
            g_avg_range+=r;
            valid++;
         }
      }
   }
   if(valid>0) g_avg_range/=valid;

   g_range_ratio=(g_avg_range>0.0 ? (g_range/g_avg_range)*100.0 : 0.0);

   if(g_range_ratio>=150.0) g_range_state="EXPANSION";
   else if(g_range_ratio<=60.0) g_range_state="COMPRESSION";
   else g_range_state="NORMAL";

   g_score=0;
   if(g_direction=="BULLISH") g_score++;
   else if(g_direction=="BEARISH") g_score--;

   if(g_strength=="STRONG BULLISH") g_score+=2;
   else if(g_strength=="MODERATE BULLISH") g_score++;
   else if(g_strength=="STRONG BEARISH") g_score-=2;
   else if(g_strength=="MODERATE BEARISH") g_score--;

   if(g_pressure=="BUYERS DOMINANT") g_score++;
   else if(g_pressure=="SELLERS DOMINANT") g_score--;

   if(g_wick_signal=="LOWER REJECTION") g_score++;
   else if(g_wick_signal=="UPPER REJECTION") g_score--;

   g_score=MathMax(-5,MathMin(5,g_score));

   MqlTick tick;
   if(SymbolInfoTick(_Symbol,tick))
   {
      g_bid=tick.bid;
      g_ask=tick.ask;
      double point=SymbolInfoDouble(_Symbol,SYMBOL_POINT);
      g_spread=(point>0.0 ? (g_ask-g_bid)/point : 0.0);
   }
}

bool Rect(string n,int x,int y,int w,int h,color bg,color br)
{
   if(!ObjectCreate(0,n,OBJ_RECTANGLE_LABEL,0,0,0)) return false;
   ObjectSetInteger(0,n,OBJPROP_CORNER,InpPanelCorner);
   ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,n,OBJPROP_XSIZE,w);
   ObjectSetInteger(0,n,OBJPROP_YSIZE,h);
   ObjectSetInteger(0,n,OBJPROP_BGCOLOR,bg);
   ObjectSetInteger(0,n,OBJPROP_BORDER_COLOR,br);
   ObjectSetInteger(0,n,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,n,OBJPROP_HIDDEN,true);
   return true;
}

bool Label(string n,string t,int x,int y,int size,color clr,bool bold=false)
{
   if(!ObjectCreate(0,n,OBJ_LABEL,0,0,0)) return false;
   ObjectSetInteger(0,n,OBJPROP_CORNER,InpPanelCorner);
   ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,n,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,n,OBJPROP_FONTSIZE,size);
   ObjectSetString(0,n,OBJPROP_FONT,bold ? "Arial Bold" : "Arial");
   ObjectSetString(0,n,OBJPROP_TEXT,t);
   ObjectSetInteger(0,n,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,n,OBJPROP_HIDDEN,true);
   return true;
}

void DeletePanel()
{
   for(int i=ObjectsTotal(0)-1;i>=0;i--)
   {
      string n=ObjectName(0,i);
      if(StringFind(n,g_prefix)==0) ObjectDelete(0,n);
   }
}

void BuildPanel()
{
   if(!InpShowPanel) return;
   DeletePanel();

   int x=InpPanelX,y=InpPanelY;

   Rect(g_prefix+"BG",x,y,680,600,Q_BG,Q_GOLD);
   Label(g_prefix+"TITLE","QUANTORA",x+18,y+14,14,Q_GOLD,true);
   Label(g_prefix+"SUB","CANDLE STRENGTH ANALYZER MT5",x+18,y+38,11,Q_WHITE,true);
   Label(g_prefix+"VER","v1.00",x+610,y+18,9,Q_GRAY);

   Label(g_prefix+"SYMBOL","SYMBOL: "+_Symbol,x+18,y+78,10,Q_WHITE);
   Label(g_prefix+"TF","TIMEFRAME: "+EnumToString((ENUM_TIMEFRAMES)_Period),x+250,y+78,10,Q_WHITE);
   Label(g_prefix+"SPREAD","SPREAD: 0.0 pts",x+500,y+78,10,Q_GRAY);

   Rect(g_prefix+"SEP1",x+18,y+112,644,2,Q_BORDER,Q_BORDER);

   Label(g_prefix+"STRENGTH","CANDLE STRENGTH: NEUTRAL",x+18,y+136,13,Q_YELLOW,true);
   Label(g_prefix+"SCORE","PRESSURE SCORE: 0 / 5",x+440,y+136,11,Q_GOLD,true);

   Label(g_prefix+"DIR","DIRECTION: NEUTRAL",x+18,y+176,10,Q_WHITE,true);
   Label(g_prefix+"PRESSURE","PRESSURE: BALANCED",x+250,y+176,10,Q_WHITE,true);
   Label(g_prefix+"RANGE_STATE","RANGE: NORMAL",x+500,y+176,10,Q_WHITE,true);

   Rect(g_prefix+"SEP2",x+18,y+212,644,2,Q_BORDER,Q_BORDER);

   Label(g_prefix+"HDR","CURRENT CANDLE STRUCTURE",x+18,y+234,10,Q_GOLD,true);

   Label(g_prefix+"BODY","BODY: 0.00%",x+18,y+272,10,Q_WHITE);
   Label(g_prefix+"UPPER","UPPER WICK: 0.00%",x+230,y+272,10,Q_WHITE);
   Label(g_prefix+"LOWER","LOWER WICK: 0.00%",x+460,y+272,10,Q_WHITE);

   Label(g_prefix+"BUY","BUY PRESSURE: 50.00%",x+18,y+312,10,Q_GREEN,true);
   Label(g_prefix+"SELL","SELL PRESSURE: 50.00%",x+350,y+312,10,Q_RED,true);

   Label(g_prefix+"WICK","WICK ANALYSIS: BALANCED",x+18,y+352,10,Q_ORANGE,true);

   Rect(g_prefix+"SEP3",x+18,y+390,644,2,Q_BORDER,Q_BORDER);

   Label(g_prefix+"OHLC_TITLE","PRICE STRUCTURE",x+18,y+412,10,Q_GOLD,true);
   Label(g_prefix+"OPEN","OPEN: 0",x+18,y+448,9,Q_WHITE);
   Label(g_prefix+"HIGH","HIGH: 0",x+180,y+448,9,Q_WHITE);
   Label(g_prefix+"LOW","LOW: 0",x+340,y+448,9,Q_WHITE);
   Label(g_prefix+"CLOSE","CLOSE: 0",x+500,y+448,9,Q_WHITE);

   Label(g_prefix+"RANGE","CANDLE RANGE: 0",x+18,y+486,9,Q_WHITE);
   Label(g_prefix+"AVG","AVG RANGE: 0",x+250,y+486,9,Q_WHITE);
   Label(g_prefix+"RATIO","RANGE vs AVG: 0.0%",x+470,y+486,9,Q_WHITE);

   Rect(g_prefix+"SEP4",x+18,y+526,644,2,Q_BORDER,Q_BORDER);

   Label(g_prefix+"BID","BID: 0",x+18,y+548,9,Q_GREEN);
   Label(g_prefix+"ASK","ASK: 0",x+190,y+548,9,Q_RED);
   Label(g_prefix+"MODE","MODE: CURRENT CANDLE",x+360,y+548,9,Q_GOLD);

   Label(g_prefix+"FOOT","mql5.com/en/users/quantora/seller",x+18,y+576,9,Q_GOLD);

   ChartRedraw();
}

void UpdatePanel()
{
   if(!InpShowPanel) return;
   int d=(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);

   ObjectSetString(0,g_prefix+"SYMBOL",OBJPROP_TEXT,"SYMBOL: "+_Symbol);
   ObjectSetString(0,g_prefix+"TF",OBJPROP_TEXT,"TIMEFRAME: "+EnumToString((ENUM_TIMEFRAMES)_Period));
   ObjectSetString(0,g_prefix+"SPREAD",OBJPROP_TEXT,"SPREAD: "+DoubleToString(g_spread,1)+" pts");

   ObjectSetString(0,g_prefix+"STRENGTH",OBJPROP_TEXT,"CANDLE STRENGTH: "+g_strength);
   ObjectSetInteger(0,g_prefix+"STRENGTH",OBJPROP_COLOR,StateColor(g_strength));

   string score=(g_score>0 ? "+" : "")+IntegerToString(g_score);
   ObjectSetString(0,g_prefix+"SCORE",OBJPROP_TEXT,"PRESSURE SCORE: "+score+" / 5");

   ObjectSetString(0,g_prefix+"DIR",OBJPROP_TEXT,"DIRECTION: "+g_direction);
   ObjectSetInteger(0,g_prefix+"DIR",OBJPROP_COLOR,StateColor(g_direction));

   ObjectSetString(0,g_prefix+"PRESSURE",OBJPROP_TEXT,"PRESSURE: "+g_pressure);
   ObjectSetInteger(0,g_prefix+"PRESSURE",OBJPROP_COLOR,StateColor(g_pressure));

   ObjectSetString(0,g_prefix+"RANGE_STATE",OBJPROP_TEXT,"RANGE: "+g_range_state);

   ObjectSetString(0,g_prefix+"BODY",OBJPROP_TEXT,"BODY: "+DoubleToString(g_body_pct,2)+"%");
   ObjectSetString(0,g_prefix+"UPPER",OBJPROP_TEXT,"UPPER WICK: "+DoubleToString(g_upper_pct,2)+"%");
   ObjectSetString(0,g_prefix+"LOWER",OBJPROP_TEXT,"LOWER WICK: "+DoubleToString(g_lower_pct,2)+"%");

   ObjectSetString(0,g_prefix+"BUY",OBJPROP_TEXT,"BUY PRESSURE: "+DoubleToString(g_buy_pressure,2)+"%");
   ObjectSetString(0,g_prefix+"SELL",OBJPROP_TEXT,"SELL PRESSURE: "+DoubleToString(g_sell_pressure,2)+"%");

   ObjectSetString(0,g_prefix+"WICK",OBJPROP_TEXT,"WICK ANALYSIS: "+g_wick_signal);

   ObjectSetString(0,g_prefix+"OPEN",OBJPROP_TEXT,"OPEN: "+DoubleToString(g_open,d));
   ObjectSetString(0,g_prefix+"HIGH",OBJPROP_TEXT,"HIGH: "+DoubleToString(g_high,d));
   ObjectSetString(0,g_prefix+"LOW",OBJPROP_TEXT,"LOW: "+DoubleToString(g_low,d));
   ObjectSetString(0,g_prefix+"CLOSE",OBJPROP_TEXT,"CLOSE: "+DoubleToString(g_close,d));

   ObjectSetString(0,g_prefix+"RANGE",OBJPROP_TEXT,"CANDLE RANGE: "+DoubleToString(g_range,d));
   ObjectSetString(0,g_prefix+"AVG",OBJPROP_TEXT,"AVG RANGE: "+DoubleToString(g_avg_range,d));
   ObjectSetString(0,g_prefix+"RATIO",OBJPROP_TEXT,"RANGE vs AVG: "+DoubleToString(g_range_ratio,1)+"%");

   ObjectSetString(0,g_prefix+"BID",OBJPROP_TEXT,"BID: "+DoubleToString(g_bid,d));
   ObjectSetString(0,g_prefix+"ASK",OBJPROP_TEXT,"ASK: "+DoubleToString(g_ask,d));
   ObjectSetString(0,g_prefix+"MODE",OBJPROP_TEXT,
                   InpUseCurrentCandle ? "MODE: CURRENT CANDLE" : "MODE: CLOSED CANDLE");

   ChartRedraw();
}

int OnInit()
{
   if(InpLookbackBars<2 ||
      InpStrongBodyPercent<=InpWeakBodyPercent ||
      InpStrongBodyPercent>100.0 ||
      InpWeakBodyPercent<0.0 ||
      InpDominantWickRatio<=0.0 ||
      InpDominantWickRatio>100.0 ||
      InpTimerSeconds<1)
      return INIT_PARAMETERS_INCORRECT;

   IndicatorSetString(INDICATOR_SHORTNAME,"Quantora Candle Strength Analyzer MT5 v1.00");

   BuildPanel();
   AnalyzeCandle();
   UpdatePanel();

   if(!EventSetTimer(InpTimerSeconds))
   {
      Print("Quantora Candle Strength Analyzer: EventSetTimer error ",GetLastError());
      return INIT_FAILED;
   }

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   DeletePanel();
}

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   return rates_total;
}

void OnTimer()
{
   AnalyzeCandle();
   UpdatePanel();
}

//===========================================================
// Developed by Quantora
// More Professional Trading Robots
// https://www.mql5.com/en/users/quantora/seller
//===========================================================
