
//| ---------------------------------------
//| Breakout1.mq5
//| Copyright 2018, getYourNet.ch
//| ---------------------------------------

#property version   "1.00"

#include <Trade\Trade.mqh>

enum REVERSAL_MODE {
   PIPS,       // In pips
   PERCENT     // In percentage
};

enum REVERSAL {
   TO_DOWN = -1,
   NO_CHANGE = 0,
   TO_UP = 1
};

input REVERSAL_MODE  InpReversal = PERCENT;  // Reversal
input double         InpDelta = 1.0;         // Delta
input int            InpNegatives = 1;       // Number of negative signals
input double         InpStopLoss = 1.0;      // Stop Loss
input double         InpTakeProfit = 4.0;    // Take Profit
input double         InpLot = 1.0;           // Lot
input int            BOMargin = 0;           // Breakout Margin
input double         TPFactor = 1;           // TP/SL Factor

double               delta;
double               stopLoss;
double               takeProfit;
//int                  bbtHandle;
int                  MaHandle;
int                  negatives;
int lastupday;
int lastdownday;


int OnInit() {
   QT_Khoi(); QT_NapBang(); QT_ChonLuat(QT_MaLuat);

   if ( negatives < 0 ) {
      negatives = 0;
      printf("The \"InpNegatives\" parameter is specified incorrectly: %d. the: %d. value will be used",
         InpNegatives, negatives);
   } else {
      negatives = InpNegatives;
   }
   checkParameter(InpDelta, delta);
   checkParameter(InpStopLoss, stopLoss);
   checkParameter(InpTakeProfit, takeProfit);
   //bbtHandle = iCustom(_Symbol, _Period, "Development\\Breakout\\BreakoutBarsTrend_v2", InpReversal, delta, false, false, 0);
   //if ( bbtHandle == INVALID_HANDLE ) {
   //   Print("Failed to create the BreakoutBarsTrend_v2 indicator. Error code: ", GetLastError());
   //   return(-1);
   //}
   
   MaHandle = iMA(NULL,0,50,0,MODE_SMA,PRICE_CLOSE);
   
   return(0);
}


void OnDeinit(const int reason) {
   //IndicatorRelease(bbtHandle);
   IndicatorRelease(MaHandle);
}


void checkParameter(double inpValue, double &parameter) {
   if ( inpValue < 0.0 ) {
      if ( InpReversal == PIPS ) {
         parameter = 1000;
      } else {
         parameter = 1.0;
      }
      printf("The parameter is specified incorrectly: %f. the: %f. value will be used",
         inpValue, parameter);
   } else {
      parameter = inpValue;
   }
}


double checkVolumeValue(double volume) {
   double minVolume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxVolume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double volumeStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if ( volume < minVolume ) {
      volume = minVolume;
   } else if ( volume > maxVolume ) {
      volume = maxVolume;
   }
   int digits = (int)MathCeil(MathLog10(1/volumeStep));
   return(NormalizeDouble(volume, digits));
}

datetime getCurrentTime() {
   datetime time[1];
   CopyTime(_Symbol, _Period, 0, 1, time);
   return(time[0]);
}


double calculateDistance(double price, double distance) {
   //if ( InpReversal == PIPS ) {
      return(NormalizeDouble(distance*_Point, _Digits));
   //}
   //return(NormalizeDouble((price/100)*distance, _Digits));
}


void checkForClose() {
   //double profit=PositionGetDouble(POSITION_PROFIT);
   //if(profit>=10)
   //{
   //   CTrade trade;
   //   trade.PositionClose(_Symbol);
   //}
   //return;
   
   datetime curTime = getCurrentTime();
   static datetime prevTime;
   if ( curTime == prevTime ) {
      return;
   }

   double highs[], lows[], MaValues[];
   if(CopyHigh(_Symbol,_Period,1,3,highs)==-1)
      return;
   if(CopyLow(_Symbol,_Period,1,3,lows)==-1)
      return;
   //if(CopyBuffer(MaHandle,0,0,10,MaValues)<10)
   //   return;

   double highrange=highs[ArrayMaximum(highs)];
   double lowrange=lows[ArrayMinimum(lows)];

   long posType = PositionGetInteger(POSITION_TYPE);

   double sl = PositionGetDouble(POSITION_SL);

   //lowrange=MaValues[1];
   //highrange=MaValues[1];

   //double profit=PositionGetDouble(POSITION_PROFIT);
   //if(profit>=10)
   //   sl=PositionGetDouble(POSITION_PRICE_OPEN);

   CTrade trade;
   if(posType==POSITION_TYPE_BUY)
   {
      sl = MathMax(sl,lowrange);
      trade.PositionModify(_Symbol,sl,PositionGetDouble(POSITION_TP));
   }
   if(posType==POSITION_TYPE_SELL)
   {
      sl = MathMin(sl,highrange);
      trade.PositionModify(_Symbol,sl,PositionGetDouble(POSITION_TP));
   }
   
   //if(posType==POSITION_TYPE_SELL)
   //{
   //   CTrade trade;
   //   ResetLastError();
   //   if ( !trade.PositionClose(_Symbol) ) {
   //      Print("Failed to close position. Error #", GetLastError());
   //      return;
   //   }
   //}
   prevTime = curTime;
}


void checkForOpen() {
   datetime curTime = getCurrentTime();
   static datetime prevTime;
   
   if ( curTime == prevTime ) {
      return;
   }

   MqlDateTime dt;
   TimeToStruct(curTime,dt);
   if(dt.hour<9||dt.hour>17)
      return;

   dt.hour=5;
   dt.min=0;
   dt.sec=0;
   datetime starttime = StructToTime(dt);
   datetime endtime = starttime+14399;

   double highs[], lows[], MaValues[];
   MqlRates current[];
   if(CopyHigh(_Symbol,_Period,starttime,endtime,highs)==-1)
      return;
   if(CopyLow(_Symbol,_Period,starttime,endtime,lows)==-1)
      return;
   if(CopyRates(_Symbol,_Period,0,1,current)==-1)
      return;
   if(CopyBuffer(MaHandle,0,0,10,MaValues)<10)
      return;

   double highrange=highs[ArrayMaximum(highs)];
   double lowrange=lows[ArrayMinimum(lows)];

   int margin=BOMargin;
   bool upbreakout=current[0].high-(_Point*margin)>highrange;
   bool downbreakout=current[0].low+(_Point*margin)<lowrange;

   if(upbreakout&&current[0].close<MaValues[0])
      return;
   if(downbreakout&&current[0].close>MaValues[0])
      return;

   //if((upbreakout&&lastupday==dt.day) || (downbreakout&&lastdownday==dt.day))
   //   return;
   //if(downbreakout&&lastdownday==dt.day)
   //   return;
   if(lastupday==dt.day || lastdownday==dt.day)
      return;

   if(upbreakout||downbreakout)
   {
      ENUM_ORDER_TYPE type=ORDER_TYPE_BUY;
      double price=0, sl=0, tp=0, volume=0;
      double stopLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
      CTrade trade;

      if(upbreakout)
      {
         type = ORDER_TYPE_BUY;
         price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         sl = lowrange;
         //sl = price-calculateDistance(price, 200);
         //tp = price+calculateDistance(price, 15000);
         tp = price+((price-lowrange)*TPFactor);
         //tp = price+calculateDistance(price, 300);
      }
   
      if(downbreakout)
      {
         Print("Short Breakout");
         type = ORDER_TYPE_SELL;
         price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         sl = highrange;
         //sl = price+calculateDistance(price, 200);
         //tp = price-calculateDistance(price, 15000);
         tp = price-((highrange-price)*TPFactor);
         //tp = price-calculateDistance(price, 300);
      }

      volume = 0.1;
      if ( !trade.PositionOpen(_Symbol, type, volume, price, sl, tp) )
      {
         Print("Failed to open the order. Error #", GetLastError());
         return;
      }
      if(upbreakout)
         lastupday=dt.day;
      if(downbreakout)
         lastdownday=dt.day;
   }
   else
      return;

   //int reverse = checkTrendChange();
   //if ( reverse == NO_CHANGE ) {
   //   prevTime = curTime;
   //   return;
   //}
   //if ( negatives == 0 || (negatives > 0 && isNegativeSeries()) ) {
   //   ENUM_ORDER_TYPE type;
   //   double price, sl, tp, volume;
   //   double stopLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
   //   CTrade trade;
   //   if ( reverse == TO_UP ) {
   //      type = ORDER_TYPE_BUY;
   //      price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   //      sl = MathMin(price-calculateDistance(price, stopLoss), SymbolInfoDouble(_Symbol, SYMBOL_BID)-stopLevel);
   //      tp = MathMax(price+calculateDistance(price, takeProfit), price+stopLevel);
   //   } else {
   //      type = ORDER_TYPE_SELL;
   //      price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   //      sl = MathMax(price+calculateDistance(price, stopLoss), SymbolInfoDouble(_Symbol, SYMBOL_ASK)+stopLevel);
   //      tp = MathMin(price-calculateDistance(price, takeProfit), price-stopLevel);
   //   }
   //   volume = checkVolumeValue(InpLot);
   //   if ( !trade.PositionOpen(_Symbol, type, volume, price, sl, tp) ) {
   //      Print("Failed to open the order. Error #", GetLastError());
   //      return;
   //   }
   //}
   prevTime = curTime;
}

#include <Trade\Trade.mqh>
CTrade qt_trade;

//============ KHO QUAN TRI: 13 luat, chon bang QT_MaLuat ================
//  Sinh tu nhan/dich_mq5_qtvt.py. KHONG SUA TAY.
//  QT_MaLuat = 0 la MOC: tat het quan tri. Bat buoc co, va phai nam trong
//  CUNG lan chay - so hai lan boot khac nhau la so hai thu khac nhau.
input int    QT_MaLuat = 0;   // 0..12
input long   QT_Magic  = 20260911;
input double QT_LotGoc = 0.10;

double QT_A_DatHue[], QT_A_TrKhoang[], QT_A_TrBatDau[], QT_A_TiaTu[];
double QT_A_TiaTy[], QT_A_NhoiKh[], QT_A_NhoiLx[], QT_A_ChotTien[];
double QT_A_ChotAtr[], QT_A_CatHoa[], QT_A_TranLot[], QT_A_TranLo[];
int    QT_A_NhoiChieu[], QT_A_TranVT[], QT_A_TranTuoi[];

double QT_DatHue, QT_TrailKhoang, QT_TrailBatDau, QT_TiaTu, QT_TiaTyLe;
double QT_NhoiKhoang, QT_NhoiLotX, QT_ChotRoTien, QT_ChotRoAtr, QT_CatHoaTu;
double QT_TranLot, QT_TranLoTien;
int    QT_NhoiChieu, QT_NhoiMax, QT_TranViThe, QT_TranTuoiGio;

void QT_NapBang()
  {
   ArrayResize(QT_A_DatHue, 13);
   QT_A_DatHue[0] = 0.0000;
   QT_A_DatHue[1] = 0.0000;
   QT_A_DatHue[2] = 0.0135;
   QT_A_DatHue[3] = 0.0000;
   QT_A_DatHue[4] = 1.3470;
   QT_A_DatHue[5] = 0.0000;
   QT_A_DatHue[6] = 0.0000;
   QT_A_DatHue[7] = 0.0000;
   QT_A_DatHue[8] = 0.0000;
   QT_A_DatHue[9] = 0.0000;
   QT_A_DatHue[10] = 0.0000;
   QT_A_DatHue[11] = 0.0000;
   QT_A_DatHue[12] = 0.0000;
   ArrayResize(QT_A_TrKhoang, 13);
   QT_A_TrKhoang[0] = 0.0000;
   QT_A_TrKhoang[1] = 0.0040;
   QT_A_TrKhoang[2] = 0.0000;
   QT_A_TrKhoang[3] = 2.6940;
   QT_A_TrKhoang[4] = 0.0000;
   QT_A_TrKhoang[5] = 0.0000;
   QT_A_TrKhoang[6] = 0.0000;
   QT_A_TrKhoang[7] = 0.0000;
   QT_A_TrKhoang[8] = 0.0000;
   QT_A_TrKhoang[9] = 0.0000;
   QT_A_TrKhoang[10] = 0.0000;
   QT_A_TrKhoang[11] = 0.0000;
   QT_A_TrKhoang[12] = 0.0000;
   ArrayResize(QT_A_TrBatDau, 13);
   QT_A_TrBatDau[0] = 0.0000;
   QT_A_TrBatDau[1] = 0.0000;
   QT_A_TrBatDau[2] = 0.0162;
   QT_A_TrBatDau[3] = 0.0000;
   QT_A_TrBatDau[4] = 0.0000;
   QT_A_TrBatDau[5] = 0.0000;
   QT_A_TrBatDau[6] = 0.0000;
   QT_A_TrBatDau[7] = 0.0000;
   QT_A_TrBatDau[8] = 0.0000;
   QT_A_TrBatDau[9] = 0.0000;
   QT_A_TrBatDau[10] = 0.0000;
   QT_A_TrBatDau[11] = 0.0000;
   QT_A_TrBatDau[12] = 0.0000;
   ArrayResize(QT_A_TiaTu, 13);
   QT_A_TiaTu[0] = 0.0000;
   QT_A_TiaTu[1] = 0.0000;
   QT_A_TiaTu[2] = 0.0000;
   QT_A_TiaTu[3] = 0.0000;
   QT_A_TiaTu[4] = 0.0000;
   QT_A_TiaTu[5] = 0.0000;
   QT_A_TiaTu[6] = 0.0000;
   QT_A_TiaTu[7] = 0.0000;
   QT_A_TiaTu[8] = 0.0000;
   QT_A_TiaTu[9] = 0.0000;
   QT_A_TiaTu[10] = 0.0000;
   QT_A_TiaTu[11] = 0.0000;
   QT_A_TiaTu[12] = 0.0000;
   ArrayResize(QT_A_TiaTy, 13);
   QT_A_TiaTy[0] = 0.5000;
   QT_A_TiaTy[1] = 0.5000;
   QT_A_TiaTy[2] = 0.5000;
   QT_A_TiaTy[3] = 0.5000;
   QT_A_TiaTy[4] = 0.5000;
   QT_A_TiaTy[5] = 0.5000;
   QT_A_TiaTy[6] = 0.5000;
   QT_A_TiaTy[7] = 0.5000;
   QT_A_TiaTy[8] = 0.5000;
   QT_A_TiaTy[9] = 0.5000;
   QT_A_TiaTy[10] = 0.5000;
   QT_A_TiaTy[11] = 0.5000;
   QT_A_TiaTy[12] = 0.5000;
   ArrayResize(QT_A_NhoiKh, 13);
   QT_A_NhoiKh[0] = 0.0000;
   QT_A_NhoiKh[1] = 0.0000;
   QT_A_NhoiKh[2] = 0.0000;
   QT_A_NhoiKh[3] = 0.0000;
   QT_A_NhoiKh[4] = 2.6940;
   QT_A_NhoiKh[5] = 0.0000;
   QT_A_NhoiKh[6] = 0.2290;
   QT_A_NhoiKh[7] = 0.0000;
   QT_A_NhoiKh[8] = 0.0000;
   QT_A_NhoiKh[9] = 0.0000;
   QT_A_NhoiKh[10] = 0.0000;
   QT_A_NhoiKh[11] = 5.2532;
   QT_A_NhoiKh[12] = 0.0000;
   ArrayResize(QT_A_NhoiLx, 13);
   QT_A_NhoiLx[0] = 1.0000;
   QT_A_NhoiLx[1] = 1.0000;
   QT_A_NhoiLx[2] = 1.0000;
   QT_A_NhoiLx[3] = 1.0000;
   QT_A_NhoiLx[4] = 1.0000;
   QT_A_NhoiLx[5] = 1.0000;
   QT_A_NhoiLx[6] = 1.0000;
   QT_A_NhoiLx[7] = 0.1500;
   QT_A_NhoiLx[8] = 1.0000;
   QT_A_NhoiLx[9] = 0.3500;
   QT_A_NhoiLx[10] = 1.0000;
   QT_A_NhoiLx[11] = 1.0000;
   QT_A_NhoiLx[12] = 1.0000;
   ArrayResize(QT_A_NhoiChieu, 13);
   QT_A_NhoiChieu[0] = 0;
   QT_A_NhoiChieu[1] = 0;
   QT_A_NhoiChieu[2] = 0;
   QT_A_NhoiChieu[3] = 0;
   QT_A_NhoiChieu[4] = 1;
   QT_A_NhoiChieu[5] = 0;
   QT_A_NhoiChieu[6] = 1;
   QT_A_NhoiChieu[7] = 1;
   QT_A_NhoiChieu[8] = 0;
   QT_A_NhoiChieu[9] = 1;
   QT_A_NhoiChieu[10] = 0;
   QT_A_NhoiChieu[11] = 1;
   QT_A_NhoiChieu[12] = 0;
   ArrayResize(QT_A_ChotTien, 13);
   QT_A_ChotTien[0] = 0.0000;
   QT_A_ChotTien[1] = 0.0000;
   QT_A_ChotTien[2] = 0.0000;
   QT_A_ChotTien[3] = 0.0000;
   QT_A_ChotTien[4] = 0.0000;
   QT_A_ChotTien[5] = 0.0000;
   QT_A_ChotTien[6] = 1.0000;
   QT_A_ChotTien[7] = 0.0000;
   QT_A_ChotTien[8] = 0.0000;
   QT_A_ChotTien[9] = 0.0000;
   QT_A_ChotTien[10] = 0.0000;
   QT_A_ChotTien[11] = 0.0000;
   QT_A_ChotTien[12] = 0.0000;
   ArrayResize(QT_A_ChotAtr, 13);
   QT_A_ChotAtr[0] = 0.0000;
   QT_A_ChotAtr[1] = 0.0269;
   QT_A_ChotAtr[2] = 0.0000;
   QT_A_ChotAtr[3] = 0.0000;
   QT_A_ChotAtr[4] = 0.0000;
   QT_A_ChotAtr[5] = 0.0000;
   QT_A_ChotAtr[6] = 0.1347;
   QT_A_ChotAtr[7] = 0.0000;
   QT_A_ChotAtr[8] = 0.4041;
   QT_A_ChotAtr[9] = 0.0000;
   QT_A_ChotAtr[10] = 0.0000;
   QT_A_ChotAtr[11] = 0.0000;
   QT_A_ChotAtr[12] = 0.0000;
   ArrayResize(QT_A_CatHoa, 13);
   QT_A_CatHoa[0] = 0.0000;
   QT_A_CatHoa[1] = 0.0000;
   QT_A_CatHoa[2] = 0.0000;
   QT_A_CatHoa[3] = 0.0000;
   QT_A_CatHoa[4] = 0.0000;
   QT_A_CatHoa[5] = 0.5388;
   QT_A_CatHoa[6] = 0.0000;
   QT_A_CatHoa[7] = 0.0000;
   QT_A_CatHoa[8] = 0.0000;
   QT_A_CatHoa[9] = 0.0000;
   QT_A_CatHoa[10] = 0.0000;
   QT_A_CatHoa[11] = 0.0000;
   QT_A_CatHoa[12] = 0.0135;
   ArrayResize(QT_A_TranVT, 13);
   QT_A_TranVT[0] = 0;
   QT_A_TranVT[1] = 2;
   QT_A_TranVT[2] = 0;
   QT_A_TranVT[3] = 0;
   QT_A_TranVT[4] = 15;
   QT_A_TranVT[5] = 0;
   QT_A_TranVT[6] = 10;
   QT_A_TranVT[7] = 4;
   QT_A_TranVT[8] = 0;
   QT_A_TranVT[9] = 4;
   QT_A_TranVT[10] = 0;
   QT_A_TranVT[11] = 0;
   QT_A_TranVT[12] = 0;
   ArrayResize(QT_A_TranLot, 13);
   QT_A_TranLot[0] = 0.0000;
   QT_A_TranLot[1] = 0.0000;
   QT_A_TranLot[2] = 0.0000;
   QT_A_TranLot[3] = 0.0000;
   QT_A_TranLot[4] = 100.0000;
   QT_A_TranLot[5] = 0.0000;
   QT_A_TranLot[6] = 0.1000;
   QT_A_TranLot[7] = 0.0000;
   QT_A_TranLot[8] = 0.0000;
   QT_A_TranLot[9] = 0.0100;
   QT_A_TranLot[10] = 0.0000;
   QT_A_TranLot[11] = 0.0400;
   QT_A_TranLot[12] = 0.0000;
   ArrayResize(QT_A_TranLo, 13);
   QT_A_TranLo[0] = 0.0000;
   QT_A_TranLo[1] = 0.0000;
   QT_A_TranLo[2] = 0.0000;
   QT_A_TranLo[3] = 0.0000;
   QT_A_TranLo[4] = 0.0000;
   QT_A_TranLo[5] = 0.0000;
   QT_A_TranLo[6] = 0.0000;
   QT_A_TranLo[7] = 0.0000;
   QT_A_TranLo[8] = 0.0000;
   QT_A_TranLo[9] = 0.0000;
   QT_A_TranLo[10] = 0.0135;
   QT_A_TranLo[11] = 0.0000;
   QT_A_TranLo[12] = 0.0000;
   ArrayResize(QT_A_TranTuoi, 13);
   QT_A_TranTuoi[0] = 0;
   QT_A_TranTuoi[1] = 0;
   QT_A_TranTuoi[2] = 0;
   QT_A_TranTuoi[3] = 0;
   QT_A_TranTuoi[4] = 0;
   QT_A_TranTuoi[5] = 0;
   QT_A_TranTuoi[6] = 0;
   QT_A_TranTuoi[7] = 0;
   QT_A_TranTuoi[8] = 0;
   QT_A_TranTuoi[9] = 0;
   QT_A_TranTuoi[10] = 0;
   QT_A_TranTuoi[11] = 0;
   QT_A_TranTuoi[12] = 0;

  }

void QT_ChonLuat(int k)
  {
   if(k < 0 || k >= 13) k = 0;
   QT_DatHue      = QT_A_DatHue[k];
   QT_TrailKhoang = QT_A_TrKhoang[k];
   QT_TrailBatDau = QT_A_TrBatDau[k];
   QT_TiaTu       = QT_A_TiaTu[k];
   QT_TiaTyLe     = QT_A_TiaTy[k];
   QT_NhoiKhoang  = QT_A_NhoiKh[k];
   QT_NhoiLotX    = QT_A_NhoiLx[k];
   QT_NhoiChieu   = QT_A_NhoiChieu[k];
   QT_ChotRoTien  = QT_A_ChotTien[k];
   QT_ChotRoAtr   = QT_A_ChotAtr[k];
   QT_CatHoaTu    = QT_A_CatHoa[k];
   QT_TranViThe   = QT_A_TranVT[k];
   QT_TranLot     = QT_A_TranLot[k];
   QT_TranLoTien  = QT_A_TranLo[k];
   QT_TranTuoiGio = QT_A_TranTuoi[k];
   QT_NhoiMax     = QT_TranViThe;
  }

//=================== QUAN TRI VI THE: kho gop ======================
//  Sinh tu nhan/dich_mq5_qtvt.py. KHONG SUA TAY.
//  lop = gop | luat = gop

int    g_qt_atr    = INVALID_HANDLE;
bool   g_qt_be     = false;
double g_qt_dinh   = 0.0;
int    g_qt_sonhoi = 0;
double g_qt_ynhoi  = 0.0;      // khoi luong cho nhoi
int    g_qt_ydong  = 0;        // 1 = dong het
double g_qt_ytia   = 0.0;      // khoi luong cho tia
int    g_qt_tia_hong = 0;      // dem lan tia bi tu choi vi duoi min lot
bool   g_qt_datia  = false;

void QT_KhoiThat()
  {
   g_qt_atr = iATR(_Symbol, PERIOD_D1, 14);
  }

double QT_Atr()
  {
   double b[];
   if(g_qt_atr == INVALID_HANDLE) return(0.0);
   if(CopyBuffer(g_qt_atr, 0, 1, 1, b) != 1) return(0.0);
   return(b[0]);
  }

bool QT_CuaTa(ulong tk)
  {
   if(PositionGetString(POSITION_SYMBOL) != _Symbol) return(false);
   if(QT_Magic == 0) return(true);
   return(PositionGetInteger(POSITION_MAGIC) == QT_Magic);
  }

int QT_SoViThe()
  {
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     { ulong tk = PositionGetTicket(i); if(tk && QT_CuaTa(tk)) n++; }
   return(n);
  }

double QT_LaiRo()
  {
   double v = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk && QT_CuaTa(tk))
         v += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
     }
   return(v);
  }

double QT_LotTong()
  {
   double v = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     { ulong tk = PositionGetTicket(i);
       if(tk && QT_CuaTa(tk)) v += PositionGetDouble(POSITION_VOLUME); }
   return(v);
  }

//--- Gia trung binh theo KHOI LUONG (dung cho luoi/DCA: khoang cach do tu day)
double QT_GiaTB()
  {
   double tv = 0, tg = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(!tk || !QT_CuaTa(tk)) continue;
      double v = PositionGetDouble(POSITION_VOLUME);
      tv += v; tg += PositionGetDouble(POSITION_PRICE_OPEN) * v;
     }
   return(tv > 0 ? tg / tv : 0.0);
  }

int QT_ChieuRo()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk && QT_CuaTa(tk))
         return(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? 1 : -1);
     }
   return(0);
  }

datetime QT_MoSomNhat()
  {
   datetime t = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(!tk || !QT_CuaTa(tk)) continue;
      datetime x = (datetime)PositionGetInteger(POSITION_TIME);
      if(t == 0 || x < t) t = x;
     }
   return(t);
  }

//--- Loi hien tai cua ro theo DON VI GIA (khong theo tien: tien phu thuoc lot)
double QT_LoiGia()
  {
   int c = QT_ChieuRo();
   if(c == 0) return(0.0);
   double tb = QT_GiaTB();
   if(tb <= 0) return(0.0);
   double gia = (c > 0) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                        : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   return((c > 0) ? (gia - tb) : (tb - gia));
  }

//--- CAT HOA: dong CAP vi the lai+lo khi tong cua cap >= 0. Giam so vi the ma
//--- khong hien thuc hoa lo rong - day la co che rieng, khong phai dong het.
void QT_CatHoa()
  {
   ulong tot = 0, xau = 0;
   double lt = 0, lx = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(!tk || !QT_CuaTa(tk)) continue;
      double p = PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
      if(p > lt) { lt = p; tot = tk; }
      if(p < lx) { lx = p; xau = tk; }
     }
   if(tot && xau && (lt + lx) >= 0)
     { qt_trade.PositionClose(tot); qt_trade.PositionClose(xau); }
  }

void QT_DongHet()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     { ulong tk = PositionGetTicket(i); if(tk && QT_CuaTa(tk)) qt_trade.PositionClose(tk); }
   g_qt_be = false; g_qt_dinh = 0; g_qt_sonhoi = 0; g_qt_datia = false;
  }

//--- Tia: PositionClosePartial duoi min lot THAT BAI IM LANG -> dem lai de biet
void QT_DongMotPhan(double ty_le)
  {
   double b  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double mn = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(!tk || !QT_CuaTa(tk)) continue;
      double vol = PositionGetDouble(POSITION_VOLUME) * ty_le;
      if(b > 0) vol = MathFloor(vol / b) * b;
      if(vol < mn || vol <= 0) { g_qt_tia_hong++; continue; }
      qt_trade.PositionClosePartial(tk, vol);
     }
  }

//--- MOI NEN: chi TINH va ghi Y DINH. Khong dat lenh o day.
void QT_MoiNen()
  {
   int n = QT_SoViThe();
   if(n == 0)
     { g_qt_be = false; g_qt_dinh = 0; g_qt_sonhoi = 0; g_qt_datia = false;
       g_qt_ynhoi = 0; g_qt_ydong = 0; g_qt_ytia = 0; return; }
   double atr = QT_Atr();
   double lai = QT_LaiRo();
   double loi = QT_LoiGia();

   // 1. CHAN - tran cung, xet truoc moi thu
   if(QT_TranLoTien > 0 && lai <= -QT_TranLoTien) { g_qt_ydong = 1; return; }
   if(QT_TranTuoiGio > 0)
     {
      datetime t0 = QT_MoSomNhat();
      if(t0 > 0 && (TimeCurrent() - t0) >= (datetime)(QT_TranTuoiGio * 3600))
        { g_qt_ydong = 1; return; }
     }
   // 2. CHOT RO
   if(QT_ChotRoTien > 0 && lai >= QT_ChotRoTien) { g_qt_ydong = 1; return; }
   if(QT_ChotRoAtr > 0 && atr > 0 && loi >= QT_ChotRoAtr * atr)
     { g_qt_ydong = 1; return; }
   // 3. CAT HOA
   if(QT_CatHoaTu > 0 && atr > 0 && n >= 2 && loi <= -QT_CatHoaTu * atr)
      QT_CatHoa();
   // 4. DAT HUE
   if(QT_DatHue > 0 && atr > 0)
     {
      if(!g_qt_be && loi >= QT_DatHue * atr) g_qt_be = true;
      if(g_qt_be && loi <= 0) { g_qt_ydong = 1; return; }
     }
   // 5. TRAILING
   if(QT_TrailKhoang > 0 && atr > 0)
     {
      int c = QT_ChieuRo();
      double gia = (c > 0) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                           : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      if(c > 0) { if(gia > g_qt_dinh) g_qt_dinh = gia; }
      else      { if(g_qt_dinh == 0 || gia < g_qt_dinh) g_qt_dinh = gia; }
      bool bat = (loi >= QT_TrailBatDau * atr);
      if(bat && c > 0 && gia <= g_qt_dinh - QT_TrailKhoang * atr) { g_qt_ydong = 1; return; }
      if(bat && c < 0 && gia >= g_qt_dinh + QT_TrailKhoang * atr) { g_qt_ydong = 1; return; }
     }
   // 6. TIA
   if(QT_TiaTu > 0 && atr > 0 && !g_qt_datia && loi >= QT_TiaTu * atr)
      g_qt_ytia = QT_TiaTyLe;
   // 7. NHOI - chi khi khong co lenh dong nao o tren
   if(QT_NhoiChieu > 0 && QT_NhoiKhoang > 0 && atr > 0 && g_qt_ydong == 0)
     {
      bool con_cho = (QT_TranViThe <= 0 || n < QT_TranViThe) &&
                     (QT_TranLot <= 0 || QT_LotTong() < QT_TranLot) &&
                     (QT_NhoiMax <= 0 || g_qt_sonhoi < QT_NhoiMax);
      double can = (g_qt_sonhoi + 1) * QT_NhoiKhoang * atr;
      bool dat = (QT_NhoiChieu == 1) ? (loi <= -can) : (loi >= can);
      if(con_cho && dat)
        {
         double vol = QT_LotGoc * MathPow(QT_NhoiLotX, g_qt_sonhoi + 1);
         double b = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
         double mn = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
         if(b > 0) vol = MathRound(vol / b) * b;
         if(vol < mn) vol = mn;
         g_qt_ynhoi = vol;
        }
     }
  }

//--- KHOP Y DINH: chi cho khi phien MO. Xem bay 1 trong docstring.
void QT_KhopYDinh()
  {
   if((ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE)
      != SYMBOL_TRADE_MODE_FULL) return;
   if(g_qt_ydong == 1) { QT_DongHet(); g_qt_ydong = 0; g_qt_ynhoi = 0; g_qt_ytia = 0; return; }
   if(g_qt_ytia > 0)   { QT_DongMotPhan(g_qt_ytia); g_qt_datia = true; g_qt_ytia = 0; }
   if(g_qt_ynhoi > 0)
     {
      int c = QT_ChieuRo();
      if(c != 0)
        {
         if(QT_Magic != 0) qt_trade.SetExpertMagicNumber(QT_Magic);
         bool ok = (c > 0) ? qt_trade.Buy(g_qt_ynhoi, _Symbol)
                           : qt_trade.Sell(g_qt_ynhoi, _Symbol);
         if(ok) g_qt_sonhoi++;
        }
      g_qt_ynhoi = 0;
     }
  }
//================= HET QUAN TRI VI THE ============================
void QT_Khoi()
  {
   QT_KhoiThat();
   QT_NapBang();
   QT_ChonLuat(QT_MaLuat);
  }


datetime g_qt_nen_de = 0;
void QT_DeQuanTri()
  {
   QT_KhopYDinh();
   datetime t = (datetime)SeriesInfoInteger(_Symbol, PERIOD_D1,
                                            SERIES_LASTBAR_DATE);
   if(t == g_qt_nen_de) return;
   g_qt_nen_de = t;
   QT_MoiNen();
  }



void OnTick() {
   QT_DeQuanTri();

   if ( PositionSelect(_Symbol) ) {
      checkForClose();
   } else {
      checkForOpen();
   }
}
