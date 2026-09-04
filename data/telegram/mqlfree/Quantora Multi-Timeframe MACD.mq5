//+------------------------------------------------------------------+
//|         Quantora Multi-Timeframe MACD Dashboard MT5              |
//|              Professional Momentum Monitor v1.00                 |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026 Quantora"
#property link      "https://www.mql5.com/en/users/quantora/seller"
#property version   "1.00"
#property strict
#property indicator_chart_window
#property indicator_plots 0
#property description "Professional multi-timeframe MACD dashboard for MetaTrader 5."
#property description "Analyzes MACD across M1, M5, M15, M30, H1, H4 and D1."

input group "========== MACD SETTINGS =========="
input int InpFastEMA      = 12;
input int InpSlowEMA      = 26;
input int InpSignalPeriod = 9;

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
#define Q_PURPLE  C'156,39,176'
#define Q_BORDER  C'62,76,89'

#define TF_COUNT 7

string g_prefix="QMTMACD5_";

ENUM_TIMEFRAMES g_tf[TF_COUNT];
string g_tf_name[TF_COUNT];
int g_macd_handle[TF_COUNT];

double g_main[TF_COUNT];
double g_signal[TF_COUNT];
double g_hist[TF_COUNT];
string g_state[TF_COUNT];
int g_tf_score[TF_COUNT];

int g_total_score=0;
int g_strong_bull=0;
int g_bull=0;
int g_neutral=0;
int g_bear=0;
int g_strong_bear=0;
int g_hist_positive=0;
int g_hist_negative=0;

string g_bias="NEUTRAL";

double g_bid=0.0;
double g_ask=0.0;
double g_spread=0.0;

void InitTimeframes()
{
   g_tf[0]=PERIOD_M1;  g_tf_name[0]="M1";
   g_tf[1]=PERIOD_M5;  g_tf_name[1]="M5";
   g_tf[2]=PERIOD_M15; g_tf_name[2]="M15";
   g_tf[3]=PERIOD_M30; g_tf_name[3]="M30";
   g_tf[4]=PERIOD_H1;  g_tf_name[4]="H1";
   g_tf[5]=PERIOD_H4;  g_tf_name[5]="H4";
   g_tf[6]=PERIOD_D1;  g_tf_name[6]="D1";

   for(int i=0;i<TF_COUNT;i++)
   {
      g_macd_handle[i]=INVALID_HANDLE;
      g_main[i]=0.0;
      g_signal[i]=0.0;
      g_hist[i]=0.0;
      g_state[i]="WAITING";
      g_tf_score[i]=0;
   }
}

string ClassifyMACD(double main_value,double signal_value,double hist_value,int &score)
{
   score=0;

   if(main_value>signal_value && hist_value>0.0)
   {
      if(main_value>0.0)
      {
         score=2;
         return "STRONG BULLISH";
      }

      score=1;
      return "BULLISH";
   }

   if(main_value<signal_value && hist_value<0.0)
   {
      if(main_value<0.0)
      {
         score=-2;
         return "STRONG BEARISH";
      }

      score=-1;
      return "BEARISH";
   }

   return "NEUTRAL";
}

color StateColor(string state)
{
   if(state=="STRONG BULLISH") return Q_GREEN;
   if(state=="BULLISH") return Q_BLUE;
   if(state=="NEUTRAL") return Q_YELLOW;
   if(state=="BEARISH") return Q_ORANGE;
   if(state=="STRONG BEARISH") return Q_RED;
   return Q_GRAY;
}

color BiasColor()
{
   if(g_bias=="STRONG BULLISH") return Q_GREEN;
   if(g_bias=="BULLISH") return Q_BLUE;
   if(g_bias=="STRONG BEARISH") return Q_RED;
   if(g_bias=="BEARISH") return Q_ORANGE;
   return Q_YELLOW;
}

void CalculateSummary()
{
   g_total_score=0;
   g_strong_bull=0;
   g_bull=0;
   g_neutral=0;
   g_bear=0;
   g_strong_bear=0;
   g_hist_positive=0;
   g_hist_negative=0;

   for(int i=0;i<TF_COUNT;i++)
   {
      g_total_score+=g_tf_score[i];

      if(g_state[i]=="STRONG BULLISH") g_strong_bull++;
      else if(g_state[i]=="BULLISH") g_bull++;
      else if(g_state[i]=="NEUTRAL") g_neutral++;
      else if(g_state[i]=="BEARISH") g_bear++;
      else if(g_state[i]=="STRONG BEARISH") g_strong_bear++;

      if(g_hist[i]>0.0) g_hist_positive++;
      else if(g_hist[i]<0.0) g_hist_negative++;
   }

   if(g_total_score>=8)
      g_bias="STRONG BULLISH";
   else if(g_total_score>=3)
      g_bias="BULLISH";
   else if(g_total_score<=-8)
      g_bias="STRONG BEARISH";
   else if(g_total_score<=-3)
      g_bias="BEARISH";
   else
      g_bias="NEUTRAL";
}

void UpdateMarketData()
{
   MqlTick tick;

   if(SymbolInfoTick(_Symbol,tick))
   {
      g_bid=tick.bid;
      g_ask=tick.ask;

      double point=SymbolInfoDouble(_Symbol,SYMBOL_POINT);
      g_spread=(point>0.0 ? (g_ask-g_bid)/point : 0.0);
   }
}

void UpdateData()
{
   for(int i=0;i<TF_COUNT;i++)
   {
      double main_buf[1];
      double signal_buf[1];

      bool ok_main=(CopyBuffer(g_macd_handle[i],0,0,1,main_buf)==1);
      bool ok_signal=(CopyBuffer(g_macd_handle[i],1,0,1,signal_buf)==1);

      if(ok_main && ok_signal)
      {
         g_main[i]=main_buf[0];
         g_signal[i]=signal_buf[0];
         g_hist[i]=g_main[i]-g_signal[i];
         g_state[i]=ClassifyMACD(g_main[i],g_signal[i],g_hist[i],g_tf_score[i]);
      }
      else
      {
         g_main[i]=0.0;
         g_signal[i]=0.0;
         g_hist[i]=0.0;
         g_state[i]="WAITING";
         g_tf_score[i]=0;
      }
   }

   CalculateSummary();
   UpdateMarketData();
}

bool Rect(string n,int x,int y,int w,int h,color bg,color br)
{
   if(!ObjectCreate(0,n,OBJ_RECTANGLE_LABEL,0,0,0))
      return false;

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
   if(!ObjectCreate(0,n,OBJ_LABEL,0,0,0))
      return false;

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

      if(StringFind(n,g_prefix)==0)
         ObjectDelete(0,n);
   }
}

void BuildPanel()
{
   if(!InpShowPanel)
      return;

   DeletePanel();

   int x=InpPanelX;
   int y=InpPanelY;

   Rect(g_prefix+"BG",x,y,720,640,Q_BG,Q_GOLD);

   Label(g_prefix+"TITLE","QUANTORA",x+18,y+14,14,Q_GOLD,true);
   Label(g_prefix+"SUB","MULTI-TIMEFRAME MACD DASHBOARD MT5",x+18,y+38,11,Q_WHITE,true);
   Label(g_prefix+"VER","v1.00",x+650,y+18,9,Q_GRAY);

   Label(g_prefix+"SYMBOL","SYMBOL: "+_Symbol,x+18,y+78,10,Q_WHITE);
   Label(g_prefix+"SPREAD","SPREAD: 0.0 pts",x+450,y+78,10,Q_GRAY);

   Rect(g_prefix+"SEP1",x+18,y+112,684,2,Q_BORDER,Q_BORDER);

   Label(g_prefix+"BIAS","OVERALL MACD BIAS: NEUTRAL",x+18,y+136,13,Q_YELLOW,true);
   Label(g_prefix+"SCORE","MOMENTUM SCORE: 0 / 14",x+450,y+136,11,Q_GOLD,true);

   Label(g_prefix+"COUNTS1","STRONG BULL: 0   BULL: 0   NEUTRAL: 0",x+18,y+174,9,Q_WHITE);
   Label(g_prefix+"COUNTS2","BEAR: 0   STRONG BEAR: 0",x+18,y+198,9,Q_WHITE);
   Label(g_prefix+"HISTCOUNT","HIST +: 0   HIST -: 0",x+450,y+186,9,Q_WHITE);

   Rect(g_prefix+"SEP2",x+18,y+230,684,2,Q_BORDER,Q_BORDER);

   Label(g_prefix+"HDR_TF","TIMEFRAME",x+18,y+252,9,Q_GOLD,true);
   Label(g_prefix+"HDR_MAIN","MACD MAIN",x+135,y+252,9,Q_GOLD,true);
   Label(g_prefix+"HDR_SIGNAL","SIGNAL",x+270,y+252,9,Q_GOLD,true);
   Label(g_prefix+"HDR_HIST","HISTOGRAM",x+385,y+252,9,Q_GOLD,true);
   Label(g_prefix+"HDR_STATE","STATE",x+510,y+252,9,Q_GOLD,true);
   Label(g_prefix+"HDR_SCORE","SCORE",x+650,y+252,9,Q_GOLD,true);

   int row=288;

   for(int i=0;i<TF_COUNT;i++)
   {
      string k=IntegerToString(i);

      Label(g_prefix+"TF_"+k,g_tf_name[i],x+18,y+row,10,Q_WHITE,true);
      Label(g_prefix+"MAIN_"+k,"0.00000",x+135,y+row,9,Q_WHITE);
      Label(g_prefix+"SIGNAL_"+k,"0.00000",x+270,y+row,9,Q_BLUE);
      Label(g_prefix+"HIST_"+k,"0.00000",x+385,y+row,9,Q_PURPLE);
      Label(g_prefix+"STATE_"+k,"WAITING",x+510,y+row,9,Q_GRAY,true);
      Label(g_prefix+"SCORE_"+k,"0",x+650,y+row,9,Q_GRAY,true);

      row+=40;
   }

   Rect(g_prefix+"SEP3",x+18,y+576,684,2,Q_BORDER,Q_BORDER);

   Label(g_prefix+"BID","BID: 0",x+18,y+596,9,Q_GREEN);
   Label(g_prefix+"ASK","ASK: 0",x+210,y+596,9,Q_RED);
   Label(g_prefix+"PARAMS","MACD "+IntegerToString(InpFastEMA)+"/"+
         IntegerToString(InpSlowEMA)+"/"+IntegerToString(InpSignalPeriod),
         x+400,y+596,9,Q_GOLD);

   Label(g_prefix+"FOOT","mql5.com/en/users/quantora/seller",x+18,y+620,9,Q_GOLD);

   ChartRedraw();
}

void UpdatePanel()
{
   if(!InpShowPanel)
      return;

   int digits=(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);

   ObjectSetString(0,g_prefix+"SYMBOL",OBJPROP_TEXT,"SYMBOL: "+_Symbol);
   ObjectSetString(0,g_prefix+"SPREAD",OBJPROP_TEXT,
                   "SPREAD: "+DoubleToString(g_spread,1)+" pts");

   ObjectSetString(0,g_prefix+"BIAS",OBJPROP_TEXT,
                   "OVERALL MACD BIAS: "+g_bias);
   ObjectSetInteger(0,g_prefix+"BIAS",OBJPROP_COLOR,BiasColor());

   ObjectSetString(0,g_prefix+"SCORE",OBJPROP_TEXT,
                   "MOMENTUM SCORE: "+IntegerToString(g_total_score)+" / 14");

   ObjectSetString(0,g_prefix+"COUNTS1",OBJPROP_TEXT,
                   "STRONG BULL: "+IntegerToString(g_strong_bull)+
                   "   BULL: "+IntegerToString(g_bull)+
                   "   NEUTRAL: "+IntegerToString(g_neutral));

   ObjectSetString(0,g_prefix+"COUNTS2",OBJPROP_TEXT,
                   "BEAR: "+IntegerToString(g_bear)+
                   "   STRONG BEAR: "+IntegerToString(g_strong_bear));

   ObjectSetString(0,g_prefix+"HISTCOUNT",OBJPROP_TEXT,
                   "HIST +: "+IntegerToString(g_hist_positive)+
                   "   HIST -: "+IntegerToString(g_hist_negative));

   for(int i=0;i<TF_COUNT;i++)
   {
      string k=IntegerToString(i);

      ObjectSetString(0,g_prefix+"MAIN_"+k,OBJPROP_TEXT,
                      DoubleToString(g_main[i],digits));
      ObjectSetString(0,g_prefix+"SIGNAL_"+k,OBJPROP_TEXT,
                      DoubleToString(g_signal[i],digits));
      ObjectSetString(0,g_prefix+"HIST_"+k,OBJPROP_TEXT,
                      DoubleToString(g_hist[i],digits));

      ObjectSetInteger(0,g_prefix+"HIST_"+k,OBJPROP_COLOR,
                       g_hist[i]>0.0 ? Q_GREEN :
                       g_hist[i]<0.0 ? Q_RED : Q_GRAY);

      ObjectSetString(0,g_prefix+"STATE_"+k,OBJPROP_TEXT,g_state[i]);
      ObjectSetInteger(0,g_prefix+"STATE_"+k,OBJPROP_COLOR,
                       StateColor(g_state[i]));

      string score_text=(g_tf_score[i]>0 ? "+" : "")+IntegerToString(g_tf_score[i]);
      ObjectSetString(0,g_prefix+"SCORE_"+k,OBJPROP_TEXT,score_text);
      ObjectSetInteger(0,g_prefix+"SCORE_"+k,OBJPROP_COLOR,
                       g_tf_score[i]>0 ? Q_GREEN :
                       g_tf_score[i]<0 ? Q_RED : Q_GRAY);
   }

   ObjectSetString(0,g_prefix+"BID",OBJPROP_TEXT,
                   "BID: "+DoubleToString(g_bid,digits));
   ObjectSetString(0,g_prefix+"ASK",OBJPROP_TEXT,
                   "ASK: "+DoubleToString(g_ask,digits));

   ChartRedraw();
}

bool CreateHandles()
{
   for(int i=0;i<TF_COUNT;i++)
   {
      g_macd_handle[i]=iMACD(_Symbol,g_tf[i],
                             InpFastEMA,InpSlowEMA,InpSignalPeriod,
                             PRICE_CLOSE);

      if(g_macd_handle[i]==INVALID_HANDLE)
      {
         Print("Quantora MTF MACD Dashboard: MACD handle error on ",
               g_tf_name[i],". Error ",GetLastError());
         return false;
      }
   }

   return true;
}

void ReleaseHandles()
{
   for(int i=0;i<TF_COUNT;i++)
   {
      if(g_macd_handle[i]!=INVALID_HANDLE)
      {
         IndicatorRelease(g_macd_handle[i]);
         g_macd_handle[i]=INVALID_HANDLE;
      }
   }
}

int OnInit()
{
   if(InpFastEMA<2 ||
      InpSlowEMA<=InpFastEMA ||
      InpSignalPeriod<2 ||
      InpTimerSeconds<1)
      return INIT_PARAMETERS_INCORRECT;

   IndicatorSetString(INDICATOR_SHORTNAME,
                      "Quantora Multi-Timeframe MACD Dashboard MT5 v1.00");

   InitTimeframes();

   if(!CreateHandles())
   {
      ReleaseHandles();
      return INIT_FAILED;
   }

   BuildPanel();
   UpdateData();
   UpdatePanel();

   if(!EventSetTimer(InpTimerSeconds))
   {
      Print("Quantora MTF MACD Dashboard: EventSetTimer error ",GetLastError());
      ReleaseHandles();
      return INIT_FAILED;
   }

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ReleaseHandles();
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
   UpdateData();
   UpdatePanel();
}

//===========================================================
// Developed by Quantora
// More Professional Trading Robots
// https://www.mql5.com/en/users/quantora/seller
//===========================================================
