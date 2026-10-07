//+------------------------------------------------------------------+
//| ea_LuoiDayDu.mq5 - EA luoi DAY DU, phan anh TUNG truong cua        |
//| nhan/luoi.py ThamSo (viet 04/10/2026 tren cloud). Da chay CHINH    |
//| van ban nay tren san gia C++ (nhan/ea_gia_lap.py), doi chieu voi   |
//| luoi.chay tung lenh. CHUA bien dich bang MetaEditor / chua chay    |
//| tester that: may nha bien dich F7, loi cu phap rieng cua MQL5 thi  |
//| sua ngay va commit, khong can xin phep.                            |
//+------------------------------------------------------------------+
#property copyright "The Brain"
#property version   "1.00"
#property description "Full grid EA: mirrors nhan/luoi.py (lot kinds, widening steps, pair-closing sparks, wait-pullback, money take-profit)."

// VI SAO CO FILE NAY
//   `ea_LuoiThamChieu.mq5` chi lam duoc luoi TOI THIEU (lot phang / nhan, buoc co dinh, TP theo pip). Khai bao tot nhat cua
//   du an (tn5: AUDCAD M15, buoc 21 x1,2, TP 9, tran 9, lot CONG 0,25, TIA LENH bien 5) can them: lot cong, buoc gian dan,
//   tia lenh, cho gia lui, chot theo tien. File nay co du ca nam de tester MT5 doi chieu va de chay DEMO.
//   `ea_LuoiThamChieu.mq5` van giu nguyen lam EA hieu chuan toi thieu: ten input TRUNG nhau (InpLot ... InpDeviation), bo tham
//   so cu chay duoc y nguyen tren file nay (InpLotKind mac dinh 1 = nhan, nhu `InpLotMult` cua file cu).
//
// QUY UOC (giong nhan/luoi.py - engine chay tren gia BID)
//   - MOI LOGIC tinh theo BID, ca hai huong: them tang, tia lenh, chot tien. Lenh MUA khop o ASK, lenh BAN khop o BID:
//     chenh lech la spread, tra luc MO (dung nhu luoi.py tru spread moi lan mo). Gia mo THEO BID cua tung lenh duoc ghi
//     vao comment ("LDD" + gia) de tinh trung binh / tia dung ke ca khi spread doi giua cac lan mo.
//   - TP may chu: MUA = trung binh BID + tp (MT5 dong lenh MUA khi Bid cham TP); BAN = trung binh BID - tp + spread hien tai
//     (MT5 dong lenh BAN khi Ask cham TP).
//   - Moi huong (mua / ban) la mot RO rieng. Them tang: gia di nguoc >= buoc(k) tu BID MO CUA TANG MO SAU CUNG; toi da
//     InpMaxLevels tang DANG MO. Moi tick toi da MOT tang moi moi huong.
//   - Tang thu k (tinh tu 0): lot = InpLot * he^k (kieu 1) | InpLot * (1 + he*k) (kieu 2) | InpLot (kieu 0); lam tron
//     TOI BUOC LOT GAN NHAT. Buoc tu tang k den k+1 = min(buoc * he_so_buoc^k, tran). k dem so tang DA MO cua ro va KHONG tut
//     khi tia lenh cat bot (giong `so_tang` cua luoi.py). Chon InpLot sao cho lot * he la boi cua buoc lot (0,04 voi he 0,25)
//     thi EA khong lam tron va khop engine tung lenh.
//   - TIA LENH (InpSpark = 1): ghep tang MO SOM NHAT voi tang MO MUON NHAT con lai, dong ca cap khi lai trung binh theo lot cua
//     cap >= InpSparkPips (tinh theo BID). Ro tia het -> mo lai tang 1 ngay (khong cho lui), k ve 0.
//   - CHO LUI (InpWaitBack > 0): ro chot TP / chot tien xong thi KHONG mo lai ngay, cho BID lui InpWaitBack pip nguoc chieu
//     so voi moc chot roi moi mo tang 1.
//   - CHOT THEO TIEN (InpTakeMoney > 0): thay TP theo pip. Dong het ro khi lai noi (theo BID, DON VI TIEN BAO GIA, vi du CAD
//     voi AUDCAD) >= InpTakeMoney * InpLot / 0,01 (dung sai nua point tren tong lot, nhu TP). Khi do KHONG dat TP may chu.
//   - KHONG co cat lo, KHONG co dung-lo-tong (luoi.py cung chua cai dat `dung_lo_tong`). Tai khoan phai la HEDGING.
//   - Khoi dong lai giua chung: k duoc suy lai bang so lenh dang mo (xap xi); moc cho lui mat.
//
// CACH DOI CHIEU (cung ma, cung cua so, cung von; ket qua vao so tay nc.db)
//   MT5   : b nc cc ea_tho_chay '{"ea":"ea_LuoiDayDu.mq5","ma":"AUDCAD","khung":"M15","doan":"kham_pha","gt_id":N,
//             "tham_so":{"InpLot":0.04,"InpStepPips":21,"InpStepMult":1.2,"InpTpPips":9,"InpMaxLevels":9,"InpMode":2,
//                        "InpLotKind":2,"InpLotMult":0.25,"InpSpark":1,"InpSparkPips":5}}'
//   Python: b nc cc thu_luoi '{"ma":"AUDCAD","khung":"M15","doan":"kham_pha","von":10000,
//             "tham_so":{"buoc":21,"tp":9,"tran_tang":9,"che_do":"hai_chieu","lot":0.04,"kieu_lot":"cong","he_so_lot":0.25,
//                        "he_so_buoc":1.2,"tia_lenh":true,"bien_cap":5}}'
//   Bang dich ten: nhan/ea_gia_lap.py BANG_TEN (ThamSo -> input). Chenh lech hop ly vi bar OHLC != tick, spread that doi.
//
// DA KIEM / CHUA KIEM (04/10/2026; tai_lieu/LAN_EA_THO.md muc "EA luoi day du")
//   Da: tren duong tick gia lap, EA khop engine TUNG LENH (chieu, lot, gia mo, tick mo / dong) o 12 cau hinh x 80 duong gia; lai
//   chenh nhau chi do (a) engine tru spread HAI lan o lenh tia, (b) engine mo / dong o muc luoi chinh xac con EA o tick dau vuot muc.
//   Chua: MetaEditor, tester that (tick that, spread doi, swap qua dem, phi), 5 diem hieu chuan. Chay tren bar OHLC thi engine lac
//   quan hon tick EA ~15% voi cau hinh co TIA LENH / chot tien (engine dong cap tia o gia tot nhat cua bar): doc ket qua tester
//   la so THAT, ket qua engine la can tren.

#include <Trade/Trade.mqh>

input double InpLot         = 0.01;      // lot tang 1 (lot)
input double InpStepPips    = 60.0;      // buoc tang 1 -> 2, pip (buoc)
input double InpTpPips      = 40.0;      // TP tu BID trung binh co trong so lot, pip (tp); bo qua khi InpTakeMoney > 0
input int    InpMaxLevels   = 20;        // toi da tang DANG MO moi ro, 1..60 (tran_tang)
input int    InpMode        = 2;         // 0 = chi mua, 1 = chi ban, 2 = hai chieu (che_do)
input double InpLotMult     = 1.0;       // he so lot (he_so_lot)
input int    InpMagic       = 20261004;  // magic cua EA (khac magic cua ea_LuoiThamChieu.mq5)
input int    InpDeviation   = 30;        // do truot cho phep, point
input int    InpLotKind     = 1;         // 0 phang | 1 nhan lot*he^k | 2 cong lot*(1+he*k) (kieu_lot)
input double InpStepMult    = 1.0;       // he so buoc: buoc(k) = buoc * he^k (he_so_buoc)
input double InpStepCap     = 400.0;     // tran khoang cach giua hai tang, pip (buoc_tran)
input int    InpSpark       = 0;         // 1 = bat tia lenh (tia_lenh)
input double InpSparkPips   = 4.0;       // bien cap tia, pip (bien_cap)
input int    InpSparkPerBar = 999;       // toi da so cap tia moi NEN cua khung hien tai; 999 = day chuyen (cap_moi_bar)
input double InpWaitBack    = 0.0;       // pip cho gia lui truoc khi mo lai tang 1; 0 = mo lai ngay (cho_lui)
input double InpTakeMoney   = 0.0;       // chot ca ro theo tien bao gia tren 0,01 lot; 0 = chot theo pip (chot_tien)
input double InpPipSize     = 0.0;       // kich thuoc 1 pip theo GIA; 0 = tu tinh (FX 3/5 chu so: 10 point)

CTrade   g_trade;
double   g_pip = 0.0;
int      g_tang[2];                      // so tang DA MO cua ro hien tai (khong tut khi tia). [0] = mua, [1] = ban
double   g_cho[2];                       // != 0: dang cho BID toi muc nay moi mo tang 1
double   g_tp_bid[2];                    // moc chot theo BID cua ro (de tinh moc cho lui)
bool     g_co[2];                        // lan doc truoc ro co lenh mo (phat hien ro vua dong)
datetime g_nen[2];                       // nen hien tai cua bo dem tia
int      g_tia_nen[2];                   // so cap da tia trong nen nay
datetime g_cho_lenh[2];                  // sau lenh hong: doi 60 giay roi moi thu lai (tranh ngap log)
int      g_so_tia = 0;                   // thong ke cho OnDeinit
int      g_tang_max = 0;

struct SRo
  {
   int    n;                             // so tang dang mo
   double lot;                           // tong lot
   double sum_lg;                        // tong lot * gia mo THEO BID
   ulong  tk_dau;                        // lenh mo SOM nhat
   double lot_dau;
   double bid_dau;
   ulong  tk_cuoi;                       // lenh mo MUON nhat
   double lot_cuoi;
   double bid_cuoi;
   double lai_noi;                       // lai noi theo BID, tien bao gia
  };

//+------------------------------------------------------------------+
int OnInit()
  {
   if(InpMode < 0 || InpMode > 2 || InpMaxLevels < 1 || InpMaxLevels > 60 || InpStepPips <= 0.0 || InpLot <= 0.0 ||
      InpLotKind < 0 || InpLotKind > 2 || InpLotMult <= 0.0 || InpStepMult <= 0.0 || InpStepCap <= 0.0 ||
      InpSparkPerBar < 1 || InpWaitBack < 0.0 || InpTakeMoney < 0.0 || InpPipSize < 0.0 ||
      (InpTakeMoney <= 0.0 && InpTpPips <= 0.0) || (InpSpark != 0 && InpSparkPips <= 0.0))
     {
      Print("LDD: tham so sai (InpMode 0..2, InpMaxLevels 1..60, InpLotKind 0..2, he so > 0, buoc > 0, lot > 0, TP > 0 hoac chot tien > 0)");
      return INIT_PARAMETERS_INCORRECT;
     }
   if((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      Print("LDD: can tai khoan HEDGING (tai khoan nay la netting/exchange: cac tang cung huong se bi gop mot vi the)");
      return INIT_FAILED;
     }
   const int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   if(InpPipSize > 0.0)
      g_pip = InpPipSize;
   else
      g_pip = (digits == 3 || digits == 5) ? 10.0 * _Point : _Point;     // cung quy uoc pip voi nhan/luoi.py cho cap FX
   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(InpDeviation);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   PrintFormat("LDD: %s pip=%.5f buoc=%.1f x%.2f tran=%.0f tp=%.1f tang_max=%d mode=%d lot=%.2f kieu=%d he=%.2f tia=%d/%.1f",
               _Symbol, g_pip, InpStepPips, InpStepMult, InpStepCap, InpTpPips, InpMaxLevels, InpMode, InpLot, InpLotKind,
               InpLotMult, InpSpark, InpSparkPips);
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   PrintFormat("LDD: ket thuc - so cap tia=%d, so tang dang mo nhieu nhat=%d", g_so_tia, g_tang_max);
  }

//+------------------------------------------------------------------+
int LotDigits()
  {
   const double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   int d = 0;
   double s = step;
   while(d < 8 && MathAbs(s - MathRound(s)) > 1e-9)
     {
      s *= 10.0;
      d++;
     }
   return d;
  }

double ChuanLot(const double lot)
  {
   const double vmin  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   const double vmax  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   const double vstep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double l = MathFloor(lot / vstep + 0.5 + 1e-9) * vstep;              // lam tron TOI GAN NHAT (nua buoc tro len)
   l = MathMax(vmin, MathMin(vmax, l));
   return NormalizeDouble(l, LotDigits());
  }

// lot cua tang thu k (tinh tu 0) - giong `_lot(k)` cua luoi.py
double LotTang(const int k)
  {
   if(InpLotKind == 1)
      return InpLot * MathPow(InpLotMult, k);
   if(InpLotKind == 2)
      return InpLot * (1.0 + InpLotMult * k);
   return InpLot;
  }

// khoang cach (pip) tu tang k den tang k + 1 (k tinh tu 0) - giong `_buoc(k)` cua luoi.py
double BuocTang(const int k)
  {
   if(InpStepMult == 1.0)
      return InpStepPips;
   return MathMin(InpStepPips * MathPow(InpStepMult, k), InpStepCap);
  }

//+------------------------------------------------------------------+
bool LaCuaRo(const ENUM_POSITION_TYPE loai)
  {
   if(PositionGetString(POSITION_SYMBOL) != _Symbol)
      return false;
   if(PositionGetInteger(POSITION_MAGIC) != InpMagic)
      return false;
   return ((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) == loai);
  }

// gia MO THEO BID cua lenh dang chon: doc tu comment "LDD<gia>"; thieu thi suy tu gia khop (MUA khop o ASK nen tru spread)
double BidMo(const ENUM_POSITION_TYPE loai)
  {
   const string c = PositionGetString(POSITION_COMMENT);
   if(StringLen(c) > 3 && StringSubstr(c, 0, 3) == "LDD")
     {
      const double g = StringToDouble(StringSubstr(c, 3));
      if(g > 0.0)
         return g;
     }
   const double mo = PositionGetDouble(POSITION_PRICE_OPEN);
   if(loai == POSITION_TYPE_BUY)
      return mo - (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID));
   return mo;
  }

void DocRo(const ENUM_POSITION_TYPE loai, SRo &r)
  {
   r.n = 0;
   r.lot = 0.0;
   r.sum_lg = 0.0;
   r.tk_dau = 0;
   r.lot_dau = 0.0;
   r.bid_dau = 0.0;
   r.tk_cuoi = 0;
   r.lot_cuoi = 0.0;
   r.bid_cuoi = 0.0;
   r.lai_noi = 0.0;
   const double bid    = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   const double hd     = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
   const double chieu  = (loai == POSITION_TYPE_BUY) ? 1.0 : -1.0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      const ulong tk = PositionGetTicket(i);
      if(tk == 0 || !LaCuaRo(loai))
         continue;
      const double l = PositionGetDouble(POSITION_VOLUME);
      const double g = BidMo(loai);
      r.n++;
      r.lot += l;
      r.sum_lg += l * g;
      r.lai_noi += chieu * (bid - g) * l * hd;
      if(r.tk_dau == 0 || tk < r.tk_dau)
        {
         r.tk_dau = tk;
         r.lot_dau = l;
         r.bid_dau = g;
        }
      if(tk > r.tk_cuoi)
        {
         r.tk_cuoi = tk;
         r.lot_cuoi = l;
         r.bid_cuoi = g;
        }
     }
  }

//+------------------------------------------------------------------+
// TP cua ro tu BID trung binh co trong so lot; goi sau MOI lan doi cau truc ro (mo tang, tia)
void DatTP(const ENUM_POSITION_TYPE loai, const SRo &r)
  {
   if(r.n == 0 || r.lot <= 0.0)
      return;
   const int    i    = (loai == POSITION_TYPE_BUY) ? 0 : 1;
   const double tb   = r.sum_lg / r.lot;
   const double moc  = (loai == POSITION_TYPE_BUY) ? tb + InpTpPips * g_pip : tb - InpTpPips * g_pip;
   g_tp_bid[i] = moc;
   if(InpTakeMoney > 0.0)
      return;                                                           // chot theo tien: khong dat TP may chu
   const double sp   = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID);
   const double tp   = NormalizeDouble((loai == POSITION_TYPE_BUY) ? moc : moc + sp, _Digits);
   for(int j = PositionsTotal() - 1; j >= 0; j--)
     {
      const ulong tk = PositionGetTicket(j);
      if(tk == 0 || !LaCuaRo(loai))
         continue;
      if(MathAbs(PositionGetDouble(POSITION_TP) - tp) > 0.5 * _Point)
         g_trade.PositionModify(tk, 0.0, tp);
     }
  }

bool MoTang(const ENUM_POSITION_TYPE loai, const int k)
  {
   const double lot = ChuanLot(LotTang(k));
   const string cm  = "LDD" + DoubleToString(SymbolInfoDouble(_Symbol, SYMBOL_BID), _Digits);
   const bool ok = (loai == POSITION_TYPE_BUY) ? g_trade.Buy(lot, _Symbol, 0.0, 0.0, 0.0, cm)
                                               : g_trade.Sell(lot, _Symbol, 0.0, 0.0, 0.0, cm);
   if(!ok)
     {
      PrintFormat("LDD: mo tang %d that bai lot=%.2f retcode=%u %s", k, lot,
                  g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription());
      g_cho_lenh[(loai == POSITION_TYPE_BUY) ? 0 : 1] = TimeCurrent() + 60;
     }
   return ok;
  }

// dong het ro (chot theo tien); that bai thi cho 60 giay
void DongHet(const ENUM_POSITION_TYPE loai)
  {
   for(int j = PositionsTotal() - 1; j >= 0; j--)
     {
      const ulong tk = PositionGetTicket(j);
      if(tk == 0 || !LaCuaRo(loai))
         continue;
      if(!g_trade.PositionClose(tk))
        {
         PrintFormat("LDD: dong lenh that bai retcode=%u %s", g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription());
         g_cho_lenh[(loai == POSITION_TYPE_BUY) ? 0 : 1] = TimeCurrent() + 60;
        }
     }
  }

// mo tang 1 cua ro MOI. Ro vua dong boi TP may chu / chot tien -> cho lui (neu bat) roi mo; ro tia het (g_co da bo) -> mo ngay.
// Goi o DAU tick (ro dong giua hai tick boi TP may chu) va NGAY SAU khi EA tu dong ro (tia het / chot tien) - engine mo lai
// o chinh bar dong, nen EA khong cho tick sau.
bool MoRoMoi(const ENUM_POSITION_TYPE loai)
  {
   const bool   mua   = (loai == POSITION_TYPE_BUY);
   const int    i     = mua ? 0 : 1;
   const double chieu = mua ? 1.0 : -1.0;
   const double bid   = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(g_co[i])
     {
      g_co[i] = false;
      g_tang[i] = 0;
      if(InpWaitBack > 0.0)
         g_cho[i] = g_tp_bid[i] - chieu * InpWaitBack * g_pip;
     }
   if(g_cho[i] != 0.0)
     {
      const bool toi = mua ? (bid <= g_cho[i] + 0.5 * _Point) : (bid >= g_cho[i] - 0.5 * _Point);
      if(!toi)
         return false;
      g_cho[i] = 0.0;
     }
   if(!MoTang(loai, 0))
      return false;
   g_tang[i] = 1;
   g_co[i] = true;
   SRo r;
   DocRo(loai, r);
   DatTP(loai, r);
   if(r.n > g_tang_max)
      g_tang_max = r.n;
   return true;
  }

//+------------------------------------------------------------------+
void XuLy(const ENUM_POSITION_TYPE loai)
  {
   const bool   mua    = (loai == POSITION_TYPE_BUY);
   const int    i      = mua ? 0 : 1;
   const double chieu  = mua ? 1.0 : -1.0;
   if(TimeCurrent() < g_cho_lenh[i])
      return;
   SRo r;
   DocRo(loai, r);
   const double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   // ---- ro rong: vua dong (TP may chu) -> cho lui hoac mo tang 1 ----
   if(r.n == 0)
     {
      MoRoMoi(loai);
      return;
     }
   if(!g_co[i])                                   // khoi dong lai khi dang co lenh: suy k tu so lenh dang mo
     {
      g_co[i] = true;
      if(g_tang[i] < r.n)
         g_tang[i] = r.n;
     }

   // ---- 1. BAT LOI TRUOC: them tang khi BID di nguoc >= buoc(k) tu BID MO CUA TANG SAU CUNG ----
   if(r.n < InpMaxLevels)
     {
      const double moc = r.bid_cuoi - chieu * BuocTang(g_tang[i] - 1) * g_pip;
      const bool cham = mua ? (bid <= moc + 0.5 * _Point) : (bid >= moc - 0.5 * _Point);
      if(cham && MoTang(loai, g_tang[i]))
        {
         g_tang[i]++;
         DocRo(loai, r);
         DatTP(loai, r);
         if(r.n > g_tang_max)
            g_tang_max = r.n;
        }
     }

   // ---- 2. TIA LENH: ghep tang MO SOM NHAT voi tang MO MUON NHAT ----
   if(InpSpark != 0)
     {
      const datetime nen = iTime(_Symbol, PERIOD_CURRENT, 0);
      if(nen != g_nen[i])
        {
         g_nen[i] = nen;
         g_tia_nen[i] = 0;
        }
      bool da_tia = false;
      while(r.n >= 2 && g_tia_nen[i] < InpSparkPerBar)
        {
         const double lai_cap = chieu * (bid - r.bid_cuoi) * r.lot_cuoi + chieu * (bid - r.bid_dau) * r.lot_dau;
         const double lot_cap = r.lot_dau + r.lot_cuoi;
         if(lai_cap + 0.5 * _Point * lot_cap < InpSparkPips * g_pip * lot_cap)      // dung sai nua point: cham DUNG muc la trung
            break;
         const bool ok1 = g_trade.PositionClose(r.tk_dau);
         const bool ok2 = g_trade.PositionClose(r.tk_cuoi);
         if(!ok1 || !ok2)
           {
            PrintFormat("LDD: tia cap that bai (%d,%d) retcode=%u %s", ok1, ok2, g_trade.ResultRetcode(),
                        g_trade.ResultRetcodeDescription());
            g_cho_lenh[i] = TimeCurrent() + 60;
           }
         g_tia_nen[i]++;
         g_so_tia++;
         da_tia = true;
         DocRo(loai, r);
         if(!(ok1 && ok2))
            break;
        }
      if(da_tia)
        {
         if(r.n == 0)                             // tia het ca ro: k ve 0, mo lai tang 1 NGAY o tick nay (khong cho lui), nhu luoi.py
           {
            g_co[i] = false;
            g_tang[i] = 0;
            g_cho[i] = 0.0;
            MoRoMoi(loai);
            return;
           }
         DatTP(loai, r);
        }
     }

   // ---- 3. chot ca ro theo TIEN (thay TP theo pip) ----
   if(InpTakeMoney > 0.0 && r.n > 0)
     {
      const double hd = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
      if(r.lai_noi + 0.5 * _Point * r.lot * hd >= InpTakeMoney * (InpLot / 0.01))      // dung sai nua point, nhu hai cho tren
        {
         g_tp_bid[i] = bid;
         DongHet(loai);
         DocRo(loai, r);
         if(r.n == 0)                                 // dong het that thi mo lai ngay (hoac cho lui) - engine mo lai o bar dong
            MoRoMoi(loai);
        }
     }
  }

void OnTick()
  {
   if(InpMode != 1)
      XuLy(POSITION_TYPE_BUY);
   if(InpMode != 0)
      XuLy(POSITION_TYPE_SELL);
  }
//+------------------------------------------------------------------+
