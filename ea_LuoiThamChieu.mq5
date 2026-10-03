//+------------------------------------------------------------------+
//| ea_LuoiThamChieu.mq5 - EA luoi TOI THIEU de DOI CHIEU nhan/luoi.py |
//| voi MT5 tester (viet 03/10/2026 tren cloud: CHUA bien dich, CHUA   |
//| chay - may nha bien dich bang MetaEditor F7, loi cu phap thi sua   |
//| ngay va commit, khong can xin phep).                               |
//+------------------------------------------------------------------+
#property copyright "The Brain"
#property version   "1.00"
#property description "Reference grid EA: mirrors nhan/luoi.py _mot_ro (flat or geometric lots, no hedge tricks)."

// VI SAO CO FILE NAY
//   `LuoiDoiXung.mq5` (EA ma `luoi.py` duoc boc ra tu do) da MAT cung VPS 02/10, nen `luoi.py` chua tung duoc
//   doi chieu voi MT5 o ma nao. File nay lam DUNG nhung gi `luoi._mot_ro` mo phong, khong them gi:
//     - moi huong (mua / ban) la mot RO rieng; ro rong -> mo tang 1 ngay
//     - them tang khi gia di nguoc >= InpStepPips tu GIA MO CUA TANG CUOI
//     - TP chung cua ro = gia trung binh CO TRONG SO LOT +/- InpTpPips; ro chot -> mo lai tang 1 ngay
//     - toi da InpMaxLevels tang moi ro; KHONG SL, KHONG tia lenh, KHONG cho-lui, KHONG chot-tien
//   QUY UOC SPREAD giong luoi.py: gia vao tinh theo BID va spread tru rieng luc mo lenh. Vi vay TP dat o
//   tb + tp - spread (mua) / tb - tp + spread (ban) de ro dong khi BID cham tb +/- tp (tb = trung binh gia MO).
//
// CACH DOI CHIEU (cung ma, cung cua so, cung von; ket qua vao so tay nc.db)
//   MT5   : b nc cc ea_tho_chay '{"ea":"ea_LuoiThamChieu.mq5","ma":"AUDCAD","khung":"M15","doan":"kham_pha",
//             "tham_so":{"InpStepPips":60,"InpTpPips":40,"InpMaxLevels":10,"InpMode":2,"InpLot":0.01}}'
//   Python: b nc cc thu_luoi '{"ma":"AUDCAD","khung":"M15","doan":"kham_pha","von":10000,
//             "tham_so":{"buoc":60,"tp":40,"tran_tang":10,"che_do":"hai_chieu","lot":0.01}}'
//   (InpLotMult > 1 <=> kieu_lot "nhan" + he_so_lot; InpMode 0/1/2 <=> che_do mua/ban/hai_chieu.)
//   So voi nhau: loi suat %/nam, maxDD %, so lenh (Python so_lenh ~ tong lenh MT5), ro chot. Chenh lech
//   hop ly vi bar OHLC != tick; DONG CHI SO ghi vao tai_lieu/NGUON_NGUOI_THANG.md muc 9.
//   Tai khoan phai la HEDGING khi InpMode = 2 (XM demo mac dinh la hedging).

#include <Trade/Trade.mqh>

input double InpLot       = 0.01;      // lot tang 1 (luoi.ThamSo.lot)
input double InpStepPips  = 60.0;      // buoc giua cac tang, pip (buoc)
input double InpTpPips    = 40.0;      // TP tu gia trung binh co trong so lot, pip (tp)
input int    InpMaxLevels = 20;        // toi da tang moi ro (tran_tang)
input int    InpMode      = 2;         // 0 = chi mua, 1 = chi ban, 2 = hai chieu (che_do)
input double InpLotMult   = 1.0;       // lot tang k (tu 0) = InpLot * InpLotMult^k; 1 = phang (he_so_lot)
input int    InpMagic     = 20261003;  // magic cua EA
input int    InpDeviation = 30;        // do truot cho phep, point

CTrade   g_trade;
double   g_pip      = 0.0;
datetime g_cho_mua  = 0;               // sau lenh hong: doi 60 giay roi moi thu lai (tranh ngap log)
datetime g_cho_ban  = 0;

struct SRo
  {
   int    n;                           // so tang dang mo
   double lot;                         // tong lot
   double sum_lg;                      // tong lot * gia mo
   double cuc;                         // gia mo cua tang CUOI (mua: thap nhat; ban: cao nhat)
  };

//+------------------------------------------------------------------+
int OnInit()
  {
   if(InpMode < 0 || InpMode > 2 || InpMaxLevels < 1 || InpStepPips <= 0.0 || InpTpPips <= 0.0 || InpLot <= 0.0)
     {
      Print("LTC: tham so sai (InpMode 0..2, InpMaxLevels >= 1, InpStepPips > 0, InpTpPips > 0, InpLot > 0)");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(InpMode == 2 && (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      Print("LTC: InpMode = 2 can tai khoan HEDGING (tai khoan nay la netting/exchange)");
      return INIT_FAILED;
     }
   const int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   g_pip = (digits == 3 || digits == 5) ? 10.0 * _Point : _Point;       // cung quy uoc pip voi nhan/luoi.py cho cap FX
   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(InpDeviation);
   PrintFormat("LTC: %s pip=%.5f buoc=%.1f tp=%.1f tang_max=%d mode=%d lot=%.2f x%.2f",
               _Symbol, g_pip, InpStepPips, InpTpPips, InpMaxLevels, InpMode, InpLot, InpLotMult);
   return INIT_SUCCEEDED;
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
   double l = MathFloor(lot / vstep + 1e-9) * vstep;
   l = MathMax(vmin, MathMin(vmax, l));
   return NormalizeDouble(l, LotDigits());
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

void DocRo(const ENUM_POSITION_TYPE loai, SRo &r)
  {
   r.n = 0;
   r.lot = 0.0;
   r.sum_lg = 0.0;
   r.cuc = 0.0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      const ulong tk = PositionGetTicket(i);
      if(tk == 0 || !LaCuaRo(loai))
         continue;
      const double l = PositionGetDouble(POSITION_VOLUME);
      const double g = PositionGetDouble(POSITION_PRICE_OPEN);
      if(r.n == 0)
         r.cuc = g;
      else
         r.cuc = (loai == POSITION_TYPE_BUY) ? MathMin(r.cuc, g) : MathMax(r.cuc, g);
      r.n++;
      r.lot += l;
      r.sum_lg += l * g;
     }
  }

//+------------------------------------------------------------------+
void DatTP(const ENUM_POSITION_TYPE loai, const SRo &r)
  {
   if(r.n == 0 || r.lot <= 0.0)
      return;
   const double tb = r.sum_lg / r.lot;
   const double sp = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID);
   const double tp = NormalizeDouble((loai == POSITION_TYPE_BUY) ? tb + InpTpPips * g_pip - sp
                                                                 : tb - InpTpPips * g_pip + sp, _Digits);
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      const ulong tk = PositionGetTicket(i);
      if(tk == 0 || !LaCuaRo(loai))
         continue;
      if(MathAbs(PositionGetDouble(POSITION_TP) - tp) > 0.5 * _Point)
         g_trade.PositionModify(tk, 0.0, tp);
     }
  }

//+------------------------------------------------------------------+
bool MoTang(const ENUM_POSITION_TYPE loai, const int k)
  {
   const double lot = ChuanLot(InpLot * MathPow(InpLotMult, k));
   const bool ok = (loai == POSITION_TYPE_BUY) ? g_trade.Buy(lot, _Symbol, 0.0, 0.0, 0.0, "LTC")
                                               : g_trade.Sell(lot, _Symbol, 0.0, 0.0, 0.0, "LTC");
   if(!ok)
     {
      PrintFormat("LTC: mo tang %d that bai lot=%.2f retcode=%u %s", k, lot,
                  g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription());
      if(loai == POSITION_TYPE_BUY)
         g_cho_mua = TimeCurrent() + 60;
      else
         g_cho_ban = TimeCurrent() + 60;
     }
   return ok;
  }

void XuLy(const ENUM_POSITION_TYPE loai)
  {
   const bool mua = (loai == POSITION_TYPE_BUY);
   if(TimeCurrent() < (mua ? g_cho_mua : g_cho_ban))
      return;
   SRo r;
   DocRo(loai, r);
   const double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   const double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(r.n == 0)                                   // ro rong -> tang 1
     {
      if(MoTang(loai, 0))
        {
         DocRo(loai, r);
         DatTP(loai, r);
        }
      return;
     }
   if(r.n >= InpMaxLevels)
      return;
   const double nguoc = mua ? (r.cuc - ask) : (bid - r.cuc);   // gia di nguoc bao xa tu tang cuoi
   if(nguoc >= InpStepPips * g_pip - 0.5 * _Point)
     {
      if(MoTang(loai, r.n))
        {
         DocRo(loai, r);
         DatTP(loai, r);
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
