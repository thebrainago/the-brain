//+------------------------------------------------------------------+
//|                                   Didi Index Signals in Time.mq4 |
//+------------------------------------------------------------------+
#property link      "http://www.financewave.com"


#property indicator_chart_window
#property indicator_buffers 6
#property indicator_color1 Blue//wick
#property indicator_color2 Red//wick
#property indicator_color3 Blue//candle
#property indicator_color4 Red//candle
#property indicator_width1 3
#property indicator_width2 3
#property indicator_width3 5
#property indicator_width4 5
#property indicator_color5 Blue//arrow
#property indicator_color6 Red//arrow

double ExtMapBuffer1[];
double ExtMapBuffer2[];

int	BarWidth			= 3,
      CandleWidth		= 5;
      
double Bar1[],
		 Bar2[],
		 Candle1[],
		 Candle2[];

string PatternText[500000];

input int times = 5;
		 
//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int init()
{
  IndicatorShortName("Didi 3Ö");  
  IndicatorBuffers(6);
  SetIndexBuffer(0,Bar1);
  SetIndexBuffer(1,Bar2);				
  SetIndexBuffer(2,Candle1);
  SetIndexBuffer(3,Candle2);
  SetIndexStyle(0,DRAW_HISTOGRAM,0,BarWidth);
  SetIndexStyle(1,DRAW_HISTOGRAM,0,BarWidth);
  SetIndexStyle(2,DRAW_HISTOGRAM,0,CandleWidth);
  SetIndexStyle(3,DRAW_HISTOGRAM,0,CandleWidth);
  SetIndexStyle(4,DRAW_ARROW);
  SetIndexArrow(4,221);
  SetIndexStyle(5,DRAW_ARROW);
  SetIndexArrow(5,222);
  SetIndexBuffer(4,ExtMapBuffer1);
  SetIndexBuffer(5,ExtMapBuffer2);

  return(0);
}
//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
int deinit() {
   ObjectsDeleteAll(0, OBJ_TEXT);
   return(0);
}
//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int start()
{

string period;

   switch (Period()) {
      case 1:
         period = "M1";
         break;
      case 5:
         period = "M5";
         break;
      case 15:
         period = "M15";
         break;
      case 30:
         period = "M30";
         break;      
      case 60:
         period = "H1";
         break;
      case 240:
         period = "H4";
         break;
      case 1440:
         period = "D1";
         break;
      case 10080:
         period = "W1";
         break;
      case 43200:
         period = "MN";
         break;
   }

   for (int j = 0; j < Bars; j++)
    { 
         PatternText[j] = "pattern-" + j;
    }



	for(int i = MathMax(Bars-1-IndicatorCounted(),1); i>=0; i--)
	{
int dip=0;
int din=0;

double timef=1;
for(timef=1;timef<=times;timef++)
{
double di11 = iMA(NULL,0,timef*3,0,MODE_EMA,PRICE_CLOSE,i);
double di12 = iMA(NULL,0,timef*3,0,MODE_EMA,PRICE_CLOSE,i+timef);
double di21 = iMA(NULL,0,timef*8,0,MODE_EMA,PRICE_CLOSE,i);
double di22 = iMA(NULL,0,timef*8,0,MODE_EMA,PRICE_CLOSE,i+timef);
double di31 = iMA(NULL,0,timef*20,0,MODE_EMA,PRICE_CLOSE,i);
double di32 = iMA(NULL,0,timef*20,0,MODE_EMA,PRICE_CLOSE,i+timef);
double OAnt = iOpen(NULL,0,i+timef);
double CAnt = iClose(NULL,0,i+timef);
double O = iOpen(NULL,0,i);
double C = iClose(NULL,0,i);
double ATR = iATR(NULL,14,i,0);

if(di11<=MathMax(O,C) && di12>=MathMin(OAnt,CAnt) && 
di21<=MathMax(O,C) && di22>=MathMin(OAnt,CAnt) &&
di31<=MathMax(O,C) && di32>=MathMin(OAnt,CAnt) &&
di11>di21 && di21>di31 &&
di12<di22 && di22<di32)

{
dip++;
}

if(di11>=MathMin(O,C) && di12<=MathMax(OAnt,CAnt) &&
di21>=MathMin(O,C) && di22<=MathMax(OAnt,CAnt) &&
di31>=MathMin(O,C) && di32<=MathMax(OAnt,CAnt) &&
di11<di21 && di21<di31 &&
di12>di22 && di22>di32)

{
din--;
}

if(dip>=times)
{
ObjectCreate(PatternText[i], OBJ_TEXT, 0, Time[i], Low[i]-ATR);
ObjectSetText(PatternText[i], times, 10, "Mistral", Gray);
Alert("Buy ", Symbol(), " ", times, " Signals", period, " ",  TimeToStr(iTime(NULL,0,i),TIME_SECONDS)," ",TimeToStr(iTime(NULL,0,i),TIME_DATE));
ExtMapBuffer1[i]=Low[i]-ATR;
SetCandleColor(1,i);
}
if(din<=-times)
{
ObjectCreate(PatternText[i], OBJ_TEXT, 0, Time[i], High[i]+ATR);
ObjectSetText(PatternText[i], times, 10, "Mistral", Gray);
Alert("Sell ", Symbol(), " ", times, " Signals", period, " ", TimeToStr(iTime(NULL,0,i),TIME_SECONDS)," ",TimeToStr(iTime(NULL,0,i),TIME_DATE));
ExtMapBuffer2[i]=High[i]+ATR;
SetCandleColor(2,i);
}

}

}

	return(0);
}
//+------------------------------------------------------------------+

void SetCandleColor(int col, int i)
{
	double high,low,bodyHigh,bodyLow;


	{
		bodyHigh = MathMax(Open[i],Close[i]);
		bodyLow  = MathMin(Open[i],Close[i]);
		high		= High[i];
		low		= Low[i];
	}

	Bar1[i] = low;	Candle1[i] = bodyLow;
	Bar2[i] = low;	Candle2[i] = bodyLow;
	

	switch(col)
	{
		case 1: 	Bar1[i] = high;	Candle1[i] = bodyHigh;	break;
		case 2: 	Bar2[i] = high;	Candle2[i] = bodyHigh;	break;
	
	}
}

//+------------------------------------------------------------------+
