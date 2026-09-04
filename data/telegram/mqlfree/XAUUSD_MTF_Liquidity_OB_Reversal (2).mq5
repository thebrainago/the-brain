//+------------------------------------------------------------------+
//| XAUUSD_MTF_LIQUIDITY_OB_REVERSAL.mq5                            |
//| Multi-TF Liquidity + Order Block + M5 Reversal/Breakout         |
//| Previous Day / H4 / M30 / M15 / M5 + M1 Swing Trade Levels      |
//+------------------------------------------------------------------+
#property strict
#property indicator_chart_window
#property indicator_plots 0
#property version   "1.00"

input ENUM_TIMEFRAMES InpExecutionTF = PERIOD_M5;
input ENUM_TIMEFRAMES InpSwingTF     = PERIOD_M1;

input int      InpLookbackPD         = 20;
input int      InpLookbackH4         = 80;
input int      InpLookbackM30        = 100;
input int      InpLookbackM15        = 120;
input int      InpLookbackM5         = 150;

input int      InpPivotStrength      = 2;
input int      InpM1PivotStrength    = 2;
input int      InpOBLookback         = 30;
input int      InpDisplacementBars   = 2;

input double   InpMatchDistance      = 1.50;   // price distance for XAUUSD
input bool     InpUseATRMatch        = true;
input double   InpATRMatchMultiplier  = 0.20;
input int      InpATRPeriod          = 14;

input bool     InpRequireSweep       = true;
input bool     InpRequireClose       = true;
input bool     InpRequireDisplace    = true;
input bool     InpAllowBreakout      = true;

input int      InpMaxZonesPerSide    = 2;
input int      InpZoneForwardBars    = 80;

input bool     InpShowPDLevels       = true;
input bool     InpShowHTFLevels      = false;
input bool     InpShowOBZones        = true;
input bool     InpShowSweepLines     = true;
input bool     InpShowPositionTools  = true;
input bool     InpShowPriceText      = true;

input bool     InpAlerts             = true;
input bool     InpPushNotification   = false;
input bool     InpSound              = true;
input string   InpSoundFile          = "alert.wav";

input color    InpZoneColor          = clrLightGray;
input color    InpBuyColor           = clrLimeGreen;
input color    InpSellColor          = clrTomato;
input color    InpEntryColor         = clrDodgerBlue;
input color    InpSLColor            = clrRed;
input color    InpTPColor            = clrLimeGreen;
input color    InpSweepColor         = clrGold;

input int      InpLineWidth          = 1;
input ENUM_LINE_STYLE InpLineStyle   = STYLE_DOT;

input string   InpObjectPrefix       = "MTF_LQ_OB_";

//---------------------------- structures ----------------------------//
struct LevelInfo
{
   double price;
   ENUM_TIMEFRAMES tf;
   bool   buySide;     // true = buy-side liquidity / highs
   int    strength;
   string source;
};

struct ZoneInfo
{
   double high;
   double low;
   double mid;
   bool   buySide;     // true = buy-side zone, false = sell-side
   int    strength;
   string text;
};

struct TradeSetup
{
   bool   valid;
   bool   isBuy;
   datetime signalTime;
   double entry;
   double sl;
   double tp1;
   double tp2;
   double tp3;
   string reason;
};

//---------------------------- globals --------------------------------//
datetime g_lastM5Bar = 0;
datetime g_lastSignalBar = 0;
int      g_signalCounter = 0;

ZoneInfo g_buyZones[2];
ZoneInfo g_sellZones[2];
int g_buyZoneCount = 0;
int g_sellZoneCount = 0;

double g_pdh=0, g_pdl=0;
double g_h4High=0, g_h4Low=0;
double g_m30High=0, g_m30Low=0;
double g_m15High=0, g_m15Low=0;
double g_m5High=0, g_m5Low=0;

bool g_buyRunning=false;
bool g_sellRunning=false;
bool g_buyTP1=false;
bool g_sellTP1=false;
double g_activeBuyEntry=0, g_activeBuySL=0, g_activeBuyTP1=0;
double g_activeSellEntry=0, g_activeSellSL=0, g_activeSellTP1=0;

string g_status="WAITING";

//+------------------------------------------------------------------+
//| Utility                                                          |
//+------------------------------------------------------------------+
string TFName(ENUM_TIMEFRAMES tf)
{
   switch(tf)
   {
      case PERIOD_M1:  return "M1";
      case PERIOD_M5:  return "M5";
      case PERIOD_M15: return "M15";
      case PERIOD_M30: return "M30";
      case PERIOD_H1:  return "H1";
      case PERIOD_H4:  return "H4";
      case PERIOD_D1:  return "D1";
   }
   return EnumToString(tf);
}

string PriceStr(double p)
{
   return DoubleToString(p,_Digits);
}

double NormalizePrice(double p)
{
   return NormalizeDouble(p,_Digits);
}

double MatchDistance()
{
   if(!InpUseATRMatch)
      return InpMatchDistance;

   double atr=GetATR(_Symbol,InpExecutionTF,InpATRPeriod,1);
   if(atr<=0)
      return InpMatchDistance;

   double d=atr*InpATRMatchMultiplier;
   return MathMax(d,SymbolInfoDouble(_Symbol,SYMBOL_POINT)*20.0);
}

bool IsNewExecutionBar()
{
   datetime t=iTime(_Symbol,InpExecutionTF,0);
   if(t==0) return false;
   if(t!=g_lastM5Bar)
   {
      g_lastM5Bar=t;
      return true;
   }
   return false;
}

void DeleteObjectsByPrefix(string prefix)
{
   int total=ObjectsTotal(0,-1,-1);
   for(int i=total-1;i>=0;i--)
   {
      string n=ObjectName(0,i,-1,-1);
      if(StringFind(n,prefix)==0)
         ObjectDelete(0,n);
   }
}

void DeleteCurrentZoneObjects()
{
   DeleteObjectsByPrefix(InpObjectPrefix+"ZONE_");
   DeleteObjectsByPrefix(InpObjectPrefix+"HTF_");
}

bool CreateHLine(string name,double price,color clr,string text="",ENUM_LINE_STYLE style=STYLE_DOT,int width=1)
{
   if(ObjectFind(0,name)>=0) ObjectDelete(0,name);
   if(!ObjectCreate(0,name,OBJ_HLINE,0,0,price))
      return false;

   ObjectSetDouble(0,name,OBJPROP_PRICE,price);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_STYLE,style);
   ObjectSetInteger(0,name,OBJPROP_WIDTH,width);
   ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,name,OBJPROP_BACK,false);
   ObjectSetString(0,name,OBJPROP_TOOLTIP,text);
   return true;
}

bool CreateText(string name,datetime t,double price,string text,color clr,int size=8)
{
   if(ObjectFind(0,name)>=0) ObjectDelete(0,name);
   if(!ObjectCreate(0,name,OBJ_TEXT,0,t,price))
      return false;

   ObjectSetString(0,name,OBJPROP_TEXT,text);
   ObjectSetString(0,name,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,name,OBJPROP_FONTSIZE,size);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_ANCHOR,ANCHOR_LEFT);
   ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,name,OBJPROP_BACK,false);
   return true;
}

bool CreateRectangle(string name,datetime t1,double p1,datetime t2,double p2,color clr)
{
   if(ObjectFind(0,name)>=0) ObjectDelete(0,name);
   if(!ObjectCreate(0,name,OBJ_RECTANGLE,0,t1,p1,t2,p2))
      return false;

   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_STYLE,STYLE_SOLID);
   ObjectSetInteger(0,name,OBJPROP_WIDTH,1);
   ObjectSetInteger(0,name,OBJPROP_FILL,true);
   ObjectSetInteger(0,name,OBJPROP_BACK,true);
   ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
   return true;
}

bool CreateTrend(string name,datetime t1,double p1,datetime t2,double p2,color clr,
                 ENUM_LINE_STYLE style=STYLE_SOLID,int width=1,bool ray=false)
{
   if(ObjectFind(0,name)>=0) ObjectDelete(0,name);
   if(!ObjectCreate(0,name,OBJ_TREND,0,t1,p1,t2,p2))
      return false;

   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_STYLE,style);
   ObjectSetInteger(0,name,OBJPROP_WIDTH,width);
   ObjectSetInteger(0,name,OBJPROP_RAY_RIGHT,ray);
   ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
   return true;
}

//+------------------------------------------------------------------+
//| ATR                                                              |
//+------------------------------------------------------------------+
double GetATR(string symbol,ENUM_TIMEFRAMES tf,int period,int shift)
{
   int h=iATR(symbol,tf,period);
   if(h==INVALID_HANDLE) return 0;

   double b[];
   ArraySetAsSeries(b,true);
   double v=0;
   if(CopyBuffer(h,0,shift,1,b)==1)
      v=b[0];
   IndicatorRelease(h);
   return v;
}

//+------------------------------------------------------------------+
//| Rates helpers                                                    |
//+------------------------------------------------------------------+
bool GetRates(ENUM_TIMEFRAMES tf,int count,MqlRates &r[])
{
   ArraySetAsSeries(r,true);
   int copied=CopyRates(_Symbol,tf,0,count,r);
   return copied>=MathMin(count,10);
}

double HighestHigh(ENUM_TIMEFRAMES tf,int lookback,int startShift=1)
{
   MqlRates r[];
   int n=lookback+startShift+5;
   if(!GetRates(tf,n,r)) return 0;
   double v=-DBL_MAX;
   int maxIndex=MathMin(lookback+startShift,ArraySize(r)-1);
   for(int i=startShift;i<=maxIndex;i++)
      if(r[i].high>v) v=r[i].high;
   return (v==-DBL_MAX?0:v);
}

double LowestLow(ENUM_TIMEFRAMES tf,int lookback,int startShift=1)
{
   MqlRates r[];
   int n=lookback+startShift+5;
   if(!GetRates(tf,n,r)) return 0;
   double v=DBL_MAX;
   int maxIndex=MathMin(lookback+startShift,ArraySize(r)-1);
   for(int i=startShift;i<=maxIndex;i++)
      if(r[i].low<v) v=r[i].low;
   return (v==DBL_MAX?0:v);
}

//+------------------------------------------------------------------+
//| Previous day                                                     |
//+------------------------------------------------------------------+
void CalculatePreviousDay()
{
   MqlRates d[];
   ArraySetAsSeries(d,true);
   if(CopyRates(_Symbol,PERIOD_D1,0,3,d)<3) return;
   g_pdh=d[1].high;
   g_pdl=d[1].low;
}

//+------------------------------------------------------------------+
//| Pivot tests                                                       |
//+------------------------------------------------------------------+
bool IsSwingHigh(MqlRates &r[],int i,int strength)
{
   int n=ArraySize(r);
   if(i-strength<0 || i+strength>=n) return false;
   for(int k=1;k<=strength;k++)
   {
      if(r[i].high<=r[i-k].high) return false;
      if(r[i].high<=r[i+k].high) return false;
   }
   return true;
}

bool IsSwingLow(MqlRates &r[],int i,int strength)
{
   int n=ArraySize(r);
   if(i-strength<0 || i+strength>=n) return false;
   for(int k=1;k<=strength;k++)
   {
      if(r[i].low>=r[i-k].low) return false;
      if(r[i].low>=r[i+k].low) return false;
   }
   return true;
}

double LastSwingHigh(ENUM_TIMEFRAMES tf,int strength,int startShift=2,int maxBars=300)
{
   MqlRates r[];
   if(!GetRates(tf,maxBars,r)) return 0;
   int last=MathMin(maxBars-strength-1,ArraySize(r)-strength-1);
   for(int i=startShift;i<=last;i++)
      if(IsSwingHigh(r,i,strength))
         return r[i].high;
   return 0;
}

double LastSwingLow(ENUM_TIMEFRAMES tf,int strength,int startShift=2,int maxBars=300)
{
   MqlRates r[];
   if(!GetRates(tf,maxBars,r)) return 0;
   int last=MathMin(maxBars-strength-1,ArraySize(r)-strength-1);
   for(int i=startShift;i<=last;i++)
      if(IsSwingLow(r,i,strength))
         return r[i].low;
   return 0;
}

// Find next swing highs/lows after entry in chronological/price search
int FindSwingTargets(bool isBuy,double entry,double &targets[],int maxTargets=3)
{
   ArrayResize(targets,maxTargets);
   for(int j=0;j<maxTargets;j++) targets[j]=0;

   MqlRates r[];
   if(!GetRates(InpSwingTF,500,r)) return 0;

   double vals[];
   ArrayResize(vals,0);

   // Start from most recent closed candle and search confirmed pivots.
   for(int i=InpM1PivotStrength+1;i<ArraySize(r)-InpM1PivotStrength;i++)
   {
      if(isBuy)
      {
         if(IsSwingHigh(r,i,InpM1PivotStrength) && r[i].high>entry)
         {
            int n=ArraySize(vals);
            ArrayResize(vals,n+1);
            vals[n]=r[i].high;
         }
      }
      else
      {
         if(IsSwingLow(r,i,InpM1PivotStrength) && r[i].low<entry)
         {
            int n=ArraySize(vals);
            ArrayResize(vals,n+1);
            vals[n]=r[i].low;
         }
      }
      if(ArraySize(vals)>=maxTargets+8) break;
   }

   // Sort nearest-to-entry first.
   int n=ArraySize(vals);
   for(int a=0;a<n-1;a++)
      for(int b=a+1;b<n;b++)
      {
         bool swap=false;
         if(isBuy && vals[b]<vals[a]) swap=true;
         if(!isBuy && vals[b]>vals[a]) swap=true;
         if(swap)
         {
            double tmp=vals[a]; vals[a]=vals[b]; vals[b]=tmp;
         }
      }

   int out=0;
   double last=0;
   for(int i=0;i<n && out<maxTargets;i++)
   {
      if(last==0 || MathAbs(vals[i]-last)>SymbolInfoDouble(_Symbol,SYMBOL_POINT)*5)
      {
         targets[out]=NormalizePrice(vals[i]);
         last=vals[i];
         out++;
      }
   }
   return out;
}

//+------------------------------------------------------------------+
//| Build level lists                                                |
//+------------------------------------------------------------------+
void AddLevel(LevelInfo &arr[],double price,ENUM_TIMEFRAMES tf,bool buySide,string source)
{
   if(price<=0) return;
   int n=ArraySize(arr);
   ArrayResize(arr,n+1);
   arr[n].price=price;
   arr[n].tf=tf;
   arr[n].buySide=buySide;
   arr[n].strength=1;
   arr[n].source=source;
}

void AddExtremeLevels(ENUM_TIMEFRAMES tf,int lookback,LevelInfo &buy[],LevelInfo &sell[])
{
   MqlRates r[];
   if(!GetRates(tf,lookback+20,r)) return;

   int maxI=MathMin(lookback,ArraySize(r)-InpPivotStrength-2);
   int foundH=0,foundL=0;

   for(int i=InpPivotStrength+1;i<=maxI;i++)
   {
      if(IsSwingHigh(r,i,InpPivotStrength))
      {
         AddLevel(buy,r[i].high,tf,true,TFName(tf)+" Swing High");
         foundH++;
         if(foundH>=6) break;
      }
   }

   for(int i=InpPivotStrength+1;i<=maxI;i++)
   {
      if(IsSwingLow(r,i,InpPivotStrength))
      {
         AddLevel(sell,r[i].low,tf,false,TFName(tf)+" Swing Low");
         foundL++;
         if(foundL>=6) break;
      }
   }
}

//+------------------------------------------------------------------+
//| Cluster matching                                                 |
//+------------------------------------------------------------------+
void BuildZones()
{
   g_buyZoneCount=0;
   g_sellZoneCount=0;

   LevelInfo buy[],sell[];
   ArrayResize(buy,0);
   ArrayResize(sell,0);

   // Previous day exact levels
   AddLevel(buy,g_pdh,PERIOD_D1,true,"PDH");
   AddLevel(sell,g_pdl,PERIOD_D1,false,"PDL");

   AddExtremeLevels(PERIOD_H4,InpLookbackH4,buy,sell);
   AddExtremeLevels(PERIOD_M30,InpLookbackM30,buy,sell);
   AddExtremeLevels(PERIOD_M15,InpLookbackM15,buy,sell);
   AddExtremeLevels(PERIOD_M5,InpLookbackM5,buy,sell);

   double dist=MatchDistance();

   // Cluster each level with other TF levels.
   for(int i=0;i<ArraySize(buy);i++)
   {
      int score=0;
      string src=buy[i].source;
      double sum=buy[i].price;

      for(int j=0;j<ArraySize(buy);j++)
      {
         if(i==j) continue;
         if(MathAbs(buy[i].price-buy[j].price)<=dist)
         {
            score++;
            sum+=buy[j].price;
            src+="+"+buy[j].source;
         }
      }

      buy[i].strength=score+1;
      buy[i].price=NormalizePrice(sum/(score+1));
   }

   for(int i=0;i<ArraySize(sell);i++)
   {
      int score=0;
      string src=sell[i].source;
      double sum=sell[i].price;

      for(int j=0;j<ArraySize(sell);j++)
      {
         if(i==j) continue;
         if(MathAbs(sell[i].price-sell[j].price)<=dist)
         {
            score++;
            sum+=sell[j].price;
            src+="+"+sell[j].source;
         }
      }

      sell[i].strength=score+1;
      sell[i].price=NormalizePrice(sum/(score+1));
   }

   // Sort descending strength
   for(int i=0;i<ArraySize(buy)-1;i++)
      for(int j=i+1;j<ArraySize(buy);j++)
         if(buy[j].strength>buy[i].strength)
         {
            LevelInfo t=buy[i]; buy[i]=buy[j]; buy[j]=t;
         }

   for(int i=0;i<ArraySize(sell)-1;i++)
      for(int j=i+1;j<ArraySize(sell);j++)
         if(sell[j].strength>sell[i].strength)
         {
            LevelInfo t=sell[i]; sell[i]=sell[j]; sell[j]=t;
         }

   // Keep unique strongest clusters
   for(int i=0;i<ArraySize(buy) && g_buyZoneCount<InpMaxZonesPerSide;i++)
   {
      bool unique=true;
      for(int j=0;j<g_buyZoneCount;j++)
         if(MathAbs(buy[i].price-g_buyZones[j].mid)<=dist*0.75)
            unique=false;

      if(!unique) continue;

      g_buyZones[g_buyZoneCount].mid=buy[i].price;
      g_buyZones[g_buyZoneCount].high=buy[i].price+dist*0.45;
      g_buyZones[g_buyZoneCount].low =buy[i].price-dist*0.45;
      g_buyZones[g_buyZoneCount].buySide=true;
      g_buyZones[g_buyZoneCount].strength=buy[i].strength;
      g_buyZones[g_buyZoneCount].text=buy[i].source;
      g_buyZoneCount++;
   }

   for(int i=0;i<ArraySize(sell) && g_sellZoneCount<InpMaxZonesPerSide;i++)
   {
      bool unique=true;
      for(int j=0;j<g_sellZoneCount;j++)
         if(MathAbs(sell[i].price-g_sellZones[j].mid)<=dist*0.75)
            unique=false;

      if(!unique) continue;

      g_sellZones[g_sellZoneCount].mid=sell[i].price;
      g_sellZones[g_sellZoneCount].high=sell[i].price+dist*0.45;
      g_sellZones[g_sellZoneCount].low =sell[i].price-dist*0.45;
      g_sellZones[g_sellZoneCount].buySide=false;
      g_sellZones[g_sellZoneCount].strength=sell[i].strength;
      g_sellZones[g_sellZoneCount].text=sell[i].source;
      g_sellZoneCount++;
   }
}

//+------------------------------------------------------------------+
//| Order block finder                                               |
//+------------------------------------------------------------------+
bool FindOrderBlock(bool bullish,double reference,double &obHigh,double &obLow)
{
   MqlRates r[];
   if(!GetRates(InpExecutionTF,InpOBLookback+10,r)) return false;

   double atr=GetATR(_Symbol,InpExecutionTF,InpATRPeriod,1);
   if(atr<=0) atr=MatchDistance();

   // Search recent opposite candle near reference.
   for(int i=2;i<InpOBLookback && i<ArraySize(r)-2;i++)
   {
      double body=MathAbs(r[i].close-r[i].open);
      bool opposite = bullish ? (r[i].close<r[i].open) : (r[i].close>r[i].open);

      if(!opposite) continue;

      if(MathAbs(r[i].high-reference)<=atr*3.0 ||
         MathAbs(r[i].low-reference)<=atr*3.0)
      {
         // Require following candle displacement in intended direction.
         bool displacement=false;
         if(bullish)
            displacement=(r[i-1].close>r[i].high && MathAbs(r[i-1].close-r[i-1].open)>=body*0.8);
         else
            displacement=(r[i-1].close<r[i].low && MathAbs(r[i-1].close-r[i-1].open)>=body*0.8);

         if(displacement || !InpRequireDisplace)
         {
            obHigh=r[i].high;
            obLow=r[i].low;
            return true;
         }
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| Draw current zones                                               |
//+------------------------------------------------------------------+
void DrawZones()
{
   DeleteCurrentZoneObjects();

   datetime t1=iTime(_Symbol,InpExecutionTF,InpLookbackM5);
   if(t1==0) t1=iTime(_Symbol,InpExecutionTF,InpMaxZonesPerSide);
   datetime t2=iTime(_Symbol,InpExecutionTF,0)+PeriodSeconds(InpExecutionTF)*InpZoneForwardBars;

   double dist=MatchDistance();

   for(int i=0;i<g_buyZoneCount;i++)
   {
      string base=InpObjectPrefix+"ZONE_BUY_"+IntegerToString(i);
      double hi=g_buyZones[i].high;
      double lo=g_buyZones[i].low;

      CreateRectangle(base,t1,hi,t2,lo,InpZoneColor);

      if(InpShowPriceText)
      {
         string txt="BUY-SIDE STRONG "+IntegerToString(g_buyZones[i].strength)+
                    " | "+PriceStr(g_buyZones[i].mid);
         CreateText(base+"_TXT",TimeCurrent(),g_buyZones[i].mid,txt,InpBuyColor,8);
      }

      double oh,ol;
      if(InpShowOBZones && FindOrderBlock(true,g_buyZones[i].mid,oh,ol))
      {
         CreateRectangle(base+"_OB",t1,oh,t2,ol,InpZoneColor);
         if(InpShowPriceText)
            CreateText(base+"_OBTXT",TimeCurrent(),(oh+ol)/2,
                       "BULLISH OB "+PriceStr((oh+ol)/2),InpBuyColor,8);
      }
   }

   for(int i=0;i<g_sellZoneCount;i++)
   {
      string base=InpObjectPrefix+"ZONE_SELL_"+IntegerToString(i);
      double hi=g_sellZones[i].high;
      double lo=g_sellZones[i].low;

      CreateRectangle(base,t1,hi,t2,lo,InpZoneColor);

      if(InpShowPriceText)
      {
         string txt="SELL-SIDE STRONG "+IntegerToString(g_sellZones[i].strength)+
                    " | "+PriceStr(g_sellZones[i].mid);
         CreateText(base+"_TXT",TimeCurrent(),g_sellZones[i].mid,txt,InpSellColor,8);
      }

      double oh,ol;
      if(InpShowOBZones && FindOrderBlock(false,g_sellZones[i].mid,oh,ol))
      {
         CreateRectangle(base+"_OB",t1,oh,t2,ol,InpZoneColor);
         if(InpShowPriceText)
            CreateText(base+"_OBTXT",TimeCurrent(),(oh+ol)/2,
                       "BEARISH OB "+PriceStr((oh+ol)/2),InpSellColor,8);
      }
   }

   if(InpShowPDLevels)
   {
      CreateHLine(InpObjectPrefix+"ZONE_PDH",g_pdh,InpSellColor,"PDH "+PriceStr(g_pdh),InpLineStyle,1);
      CreateHLine(InpObjectPrefix+"ZONE_PDL",g_pdl,InpBuyColor,"PDL "+PriceStr(g_pdl),InpLineStyle,1);

      if(InpShowPriceText)
      {
         CreateText(InpObjectPrefix+"ZONE_PDH_TXT",TimeCurrent(),g_pdh,
                    "PDH BSL "+PriceStr(g_pdh),InpSellColor,8);
         CreateText(InpObjectPrefix+"ZONE_PDL_TXT",TimeCurrent(),g_pdl,
                    "PDL SSL "+PriceStr(g_pdl),InpBuyColor,8);
      }
   }

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| M5 signal candle logic                                           |
//+------------------------------------------------------------------+
bool BullishDisplacement(MqlRates &r[])
{
   if(ArraySize(r)<5) return false;
   double atr=GetATR(_Symbol,InpExecutionTF,InpATRPeriod,1);
   double body=MathAbs(r[1].close-r[1].open);
   if(r[1].close<=r[1].open) return false;
   if(!InpRequireDisplace) return true;
   return (body>=atr*0.45 && r[1].close>r[2].high);
}

bool BearishDisplacement(MqlRates &r[])
{
   if(ArraySize(r)<5) return false;
   double atr=GetATR(_Symbol,InpExecutionTF,InpATRPeriod,1);
   double body=MathAbs(r[1].close-r[1].open);
   if(r[1].close>=r[1].open) return false;
   if(!InpRequireDisplace) return true;
   return (body>=atr*0.45 && r[1].close<r[2].low);
}

bool GetSignal(TradeSetup &sig)
{
   sig.valid=false;
   sig.entry=0; sig.sl=0; sig.tp1=0; sig.tp2=0; sig.tp3=0;
   sig.reason="";

   MqlRates r[];
   if(!GetRates(InpExecutionTF,20,r)) return false;

   double c=r[1].close;
   double h=r[1].high;
   double l=r[1].low;

   // SELL reversal: sweep buy-side then close below it.
   for(int z=0;z<g_buyZoneCount;z++)
   {
      double level=g_buyZones[z].mid;
      bool sweep=(h>level && c<level);
      bool closeOK=(c<level);
      bool disp=BearishDisplacement(r);

      if((InpRequireSweep && !sweep) || (InpRequireClose && !closeOK)) continue;
      if(InpRequireDisplace && !disp) continue;

      sig.isBuy=false;
      sig.entry=c;
      sig.signalTime=r[1].time;
      sig.reason="SELL REVERSAL: BSL SWEEP";
      sig.valid=true;
      break;
   }

   // BUY reversal: sweep sell-side then close above it.
   if(!sig.valid)
   {
      for(int z=0;z<g_sellZoneCount;z++)
      {
         double level=g_sellZones[z].mid;
         bool sweep=(l<level && c>level);
         bool closeOK=(c>level);
         bool disp=BullishDisplacement(r);

         if((InpRequireSweep && !sweep) || (InpRequireClose && !closeOK)) continue;
         if(InpRequireDisplace && !disp) continue;

         sig.isBuy=true;
         sig.entry=c;
         sig.signalTime=r[1].time;
         sig.reason="BUY REVERSAL: SSL SWEEP";
         sig.valid=true;
         break;
      }
   }

   // Breakout fallback.
   if(!sig.valid && InpAllowBreakout)
   {
      for(int z=0;z<g_buyZoneCount;z++)
      {
         double level=g_buyZones[z].mid;
         if(c>level && r[2].close<=level && BullishDisplacement(r))
         {
            sig.isBuy=true;
            sig.entry=c;
            sig.signalTime=r[1].time;
            sig.reason="BUY BREAKOUT: BSL CLOSE";
            sig.valid=true;
            break;
         }
      }

      if(!sig.valid)
      {
         for(int z=0;z<g_sellZoneCount;z++)
         {
            double level=g_sellZones[z].mid;
            if(c<level && r[2].close>=level && BearishDisplacement(r))
            {
               sig.isBuy=false;
               sig.entry=c;
               sig.signalTime=r[1].time;
               sig.reason="SELL BREAKOUT: SSL CLOSE";
               sig.valid=true;
               break;
            }
         }
      }
   }

   if(!sig.valid) return false;

   // M1 swing SL
   if(sig.isBuy)
      sig.sl=LastSwingLow(InpSwingTF,InpM1PivotStrength,2,400);
   else
      sig.sl=LastSwingHigh(InpSwingTF,InpM1PivotStrength,2,400);

   if(sig.sl<=0) return false;

   // Ensure SL is on correct side.
   if(sig.isBuy && sig.sl>=sig.entry) return false;
   if(!sig.isBuy && sig.sl<=sig.entry) return false;

   double targets[];
   int n=FindSwingTargets(sig.isBuy,sig.entry,targets,3);

   // If insufficient M1 swings, use R multiples as fallback.
   double risk=MathAbs(sig.entry-sig.sl);
   if(risk<=SymbolInfoDouble(_Symbol,SYMBOL_POINT)*2) return false;

   if(n>=1) sig.tp1=targets[0];
   else sig.tp1=sig.isBuy ? sig.entry+risk : sig.entry-risk;

   if(n>=2) sig.tp2=targets[1];
   else sig.tp2=sig.isBuy ? sig.entry+risk*2.0 : sig.entry-risk*2.0;

   if(n>=3) sig.tp3=targets[2];
   else sig.tp3=sig.isBuy ? sig.entry+risk*3.0 : sig.entry-risk*3.0;

   // Validate targets; fallback to R if invalid.
   if(sig.isBuy)
   {
      if(sig.tp1<=sig.entry) sig.tp1=sig.entry+risk;
      if(sig.tp2<=sig.tp1)  sig.tp2=sig.entry+risk*2.0;
      if(sig.tp3<=sig.tp2)  sig.tp3=sig.entry+risk*3.0;
   }
   else
   {
      if(sig.tp1>=sig.entry) sig.tp1=sig.entry-risk;
      if(sig.tp2>=sig.tp1)  sig.tp2=sig.entry-risk*2.0;
      if(sig.tp3>=sig.tp2)  sig.tp3=sig.entry-risk*3.0;
   }

   sig.entry=NormalizePrice(sig.entry);
   sig.sl=NormalizePrice(sig.sl);
   sig.tp1=NormalizePrice(sig.tp1);
   sig.tp2=NormalizePrice(sig.tp2);
   sig.tp3=NormalizePrice(sig.tp3);

   return true;
}

//+------------------------------------------------------------------+
//| Position tool                                                     |
//+------------------------------------------------------------------+
void DrawPositionTool(TradeSetup &s)
{
   if(!InpShowPositionTools) return;

   g_signalCounter++;
   string id=IntegerToString((int)s.signalTime)+"_"+IntegerToString(g_signalCounter);
   string base=InpObjectPrefix+(s.isBuy?"BUY_":"SELL_")+id;

   datetime t1=s.signalTime;
   datetime t2=t1+PeriodSeconds(InpExecutionTF)*InpZoneForwardBars;

   color entryClr=InpEntryColor;
   color slClr=InpSLColor;
   color tpClr=InpTPColor;

   CreateTrend(base+"_ENTRY",t1,s.entry,t2,s.entry,entryClr,STYLE_SOLID,2,false);
   CreateTrend(base+"_SL",t1,s.sl,t2,s.sl,slClr,STYLE_DASH,1,false);
   CreateTrend(base+"_TP1",t1,s.tp1,t2,s.tp1,tpClr,STYLE_DOT,1,false);
   CreateTrend(base+"_TP2",t1,s.tp2,t2,s.tp2,tpClr,STYLE_DOT,1,false);
   CreateTrend(base+"_TP3",t1,s.tp3,t2,s.tp3,tpClr,STYLE_DOT,1,false);

   if(InpShowPriceText)
   {
      string side=s.isBuy?"BUY":"SELL";

      CreateText(base+"_ENTRY_TXT",t1,s.entry,
                 side+" ENTRY "+PriceStr(s.entry),entryClr,9);
      CreateText(base+"_SL_TXT",t1,s.sl,
                 "SL "+PriceStr(s.sl),slClr,9);
      CreateText(base+"_TP1_TXT",t1,s.tp1,
                 "TP1 "+PriceStr(s.tp1),tpClr,9);
      CreateText(base+"_TP2_TXT",t1,s.tp2,
                 "TP2 "+PriceStr(s.tp2),tpClr,9);
      CreateText(base+"_TP3_TXT",t1,s.tp3,
                 "TP3 "+PriceStr(s.tp3),tpClr,9);

      CreateText(base+"_REASON_TXT",t1,
                 s.isBuy?s.entry:s.entry,
                 side+" | "+s.reason, s.isBuy?InpBuyColor:InpSellColor,8);
   }

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Sweep line                                                       |
//+------------------------------------------------------------------+
void DrawSweepLine(bool buySide,double level,datetime when,string reason)
{
   if(!InpShowSweepLines) return;

   g_signalCounter++;
   string base=InpObjectPrefix+"SWEEP_"+IntegerToString((int)when)+"_"+IntegerToString(g_signalCounter);

   datetime t2=when+PeriodSeconds(InpExecutionTF)*InpZoneForwardBars;
   CreateTrend(base,when,level,t2,level,InpSweepColor,STYLE_DASHDOT,2,false);

   if(InpShowPriceText)
   {
      string txt=buySide ? "BSL SWEPT " : "SSL SWEPT ";
      txt+=PriceStr(level);
      CreateText(base+"_TXT",when,level,txt,InpSweepColor,8);
   }
}

//+------------------------------------------------------------------+
//| Alert                                                             |
//+------------------------------------------------------------------+
void SendSignalAlert(TradeSetup &s)
{
   if(!InpAlerts) return;

   string side=s.isBuy?"BUY":"SELL";
   string msg=StringFormat("%s %s %s\nENTRY: %s\nSL: %s\nTP1: %s\nTP2: %s\nTP3: %s\n%s",
                           _Symbol,TFName(InpExecutionTF),side,
                           PriceStr(s.entry),PriceStr(s.sl),
                           PriceStr(s.tp1),PriceStr(s.tp2),PriceStr(s.tp3),
                           s.reason);

   Alert(msg);
   if(InpSound) PlaySound(InpSoundFile);
   if(InpPushNotification) SendNotification(msg);
}

//+------------------------------------------------------------------+
//| Dashboard                                                        |
//+------------------------------------------------------------------+
void DrawDashboard()
{
   string bg=InpObjectPrefix+"DASH_BG";
   string tx=InpObjectPrefix+"DASH_TXT";

   if(ObjectFind(0,bg)>=0) ObjectDelete(0,bg);
   if(ObjectFind(0,tx)>=0) ObjectDelete(0,tx);

   ObjectCreate(0,bg,OBJ_RECTANGLE_LABEL,0,0,0);
   ObjectSetInteger(0,bg,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,bg,OBJPROP_XDISTANCE,10);
   ObjectSetInteger(0,bg,OBJPROP_YDISTANCE,20);
   ObjectSetInteger(0,bg,OBJPROP_XSIZE,300);
   ObjectSetInteger(0,bg,OBJPROP_YSIZE,220);
   ObjectSetInteger(0,bg,OBJPROP_BGCOLOR,clrBlack);
   ObjectSetInteger(0,bg,OBJPROP_COLOR,clrDimGray);
   ObjectSetInteger(0,bg,OBJPROP_BACK,false);
   ObjectSetInteger(0,bg,OBJPROP_SELECTABLE,false);

   string status=g_status;
   string s=
      "MTF LIQUIDITY + OB\n"+
      _Symbol+" | "+TFName(InpExecutionTF)+"\n"+
      "------------------------------\n"+
      "PDH BSL : "+PriceStr(g_pdh)+"\n"+
      "PDL SSL : "+PriceStr(g_pdl)+"\n"+
      "BUY ZONES  : "+IntegerToString(g_buyZoneCount)+"\n"+
      "SELL ZONES : "+IntegerToString(g_sellZoneCount)+"\n"+
      "MATCH DIST : "+DoubleToString(MatchDistance(),_Digits)+"\n"+
      "------------------------------\n"+
      "STATUS : "+status+"\n"+
      "BUY RUN  : "+(g_buyRunning?"YES":"NO")+"\n"+
      "SELL RUN : "+(g_sellRunning?"YES":"NO")+"\n"+
      "------------------------------\n"+
      "5M RESET : ACTIVE\n"+
      "M1 SL/TP : ACTIVE";

   ObjectCreate(0,tx,OBJ_LABEL,0,0,0);
   ObjectSetInteger(0,tx,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,tx,OBJPROP_XDISTANCE,20);
   ObjectSetInteger(0,tx,OBJPROP_YDISTANCE,28);
   ObjectSetString(0,tx,OBJPROP_TEXT,s);
   ObjectSetString(0,tx,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,tx,OBJPROP_FONTSIZE,9);
   ObjectSetInteger(0,tx,OBJPROP_COLOR,clrWhite);
   ObjectSetInteger(0,tx,OBJPROP_SELECTABLE,false);
}

//+------------------------------------------------------------------+
//| Check running setup TP1 / SL                                     |
//+------------------------------------------------------------------+
void UpdateRunningStates()
{
   double bid=SymbolInfoDouble(_Symbol,SYMBOL_BID);
   double ask=SymbolInfoDouble(_Symbol,SYMBOL_ASK);

   if(g_buyRunning)
   {
      if(bid<=g_activeBuySL)
      {
         g_buyRunning=false;
         g_buyTP1=false;
         g_status="BUY SL HIT";
      }
      else if(bid>=g_activeBuyTP1)
      {
         g_buyTP1=true;
         g_buyRunning=false;
         g_status="BUY TP1 HIT";
      }
   }

   if(g_sellRunning)
   {
      if(ask>=g_activeSellSL)
      {
         g_sellRunning=false;
         g_sellTP1=false;
         g_status="SELL SL HIT";
      }
      else if(ask<=g_activeSellTP1)
      {
         g_sellTP1=true;
         g_sellRunning=false;
         g_status="SELL TP1 HIT";
      }
   }
}

//+------------------------------------------------------------------+
//| Process signal                                                    |
//+------------------------------------------------------------------+
void ProcessNewM5Signal()
{
   TradeSetup s;
   if(!GetSignal(s))
   {
      g_status="WAITING FOR SWEEP / BREAKOUT";
      return;
   }

   if(s.signalTime==g_lastSignalBar)
      return;

   g_lastSignalBar=s.signalTime;

   // Draw sweep line when applicable.
   MqlRates r[];
   GetRates(InpExecutionTF,10,r);

   if(s.isBuy)
   {
      // Find swept sell zone nearest the candle.
      for(int z=0;z<g_sellZoneCount;z++)
      {
         if(r[1].low<g_sellZones[z].mid && r[1].close>g_sellZones[z].mid)
         {
            DrawSweepLine(false,g_sellZones[z].mid,s.signalTime,"SSL");
            break;
         }
      }
   }
   else
   {
      for(int z=0;z<g_buyZoneCount;z++)
      {
         if(r[1].high>g_buyZones[z].mid && r[1].close<g_buyZones[z].mid)
         {
            DrawSweepLine(true,g_buyZones[z].mid,s.signalTime,"BSL");
            break;
         }
      }
   }

   // Keep historical position tools.
   DrawPositionTool(s);
   SendSignalAlert(s);

   // State management: opposite signal is allowed and gets its own tool.
   if(s.isBuy)
   {
      g_buyRunning=true;
      g_activeBuyEntry=s.entry;
      g_activeBuySL=s.sl;
      g_activeBuyTP1=s.tp1;
      g_status="BUY SIGNAL";
   }
   else
   {
      g_sellRunning=true;
      g_activeSellEntry=s.entry;
      g_activeSellSL=s.sl;
      g_activeSellTP1=s.tp1;
      g_status="SELL SIGNAL";
   }
}

//+------------------------------------------------------------------+
//| Initialization                                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   IndicatorSetString(INDICATOR_SHORTNAME,"MTF Liquidity OB Reversal");

   CalculatePreviousDay();
   BuildZones();
   DrawZones();
   DrawDashboard();

   g_lastM5Bar=iTime(_Symbol,InpExecutionTF,0);

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Deinitialization                                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Do NOT delete historical position tools or sweep lines.
   // Delete only live dashboard/current zone objects.
   DeleteObjectsByPrefix(InpObjectPrefix+"ZONE_");
   DeleteObjectsByPrefix(InpObjectPrefix+"HTF_");
   DeleteObjectsByPrefix(InpObjectPrefix+"DASH_");
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Main calculation                                                 |
//+------------------------------------------------------------------+
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
   UpdateRunningStates();

   if(IsNewExecutionBar())
   {
      // Recalculate steps 1-6 every new M5 candle.
      CalculatePreviousDay();
      BuildZones();
      DrawZones();
      DrawDashboard();

      // Signal is based on the newly closed M5 candle.
      ProcessNewM5Signal();
   }

   DrawDashboard();
   return rates_total;
}
//+------------------------------------------------------------------+
