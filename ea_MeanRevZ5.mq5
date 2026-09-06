//+------------------------------------------------------------------+
//| MeanRevZ5.mq5 - he DA PASS ca hai cong, dua ra tick THAT           |
//|                                                                    |
//| Gia thuyet trong so cai: XM_US100CASH.D1.mean_reversion_z5         |
//|   plan_hash 55d17325924c27b5, dang ky 2026-09-05 12:39:09          |
//|                                                                    |
//| LUAT (nguyen van tu config/co_che_dsl.json, khong them bot):        |
//|   vao : zscore(close, 5) <  -1.0                                   |
//|   ra  : zscore(close, 5) >= -1.0                                   |
//|   chieu 1 (chi MUA), giu toi da 500 nen                            |
//|                                                                    |
//| zscore(close,n) = (close - TB(close,n)) / DoLech(close,n)          |
//| DoLech dung mau THEO DAN SO (chia n), dung y het `pandas.std(ddof=0)|
//| ma `ngu_phap.toan_hang` goi - lech ddof la lech nguong, va nguong   |
//| la -1,0 dung o ranh.                                               |
//|                                                                    |
//| QUY UOC THOI GIAN. Python tinh tin hieu tai close[i] roi `mo_phong` |
//| tu dich mot bar -> vao lenh o OPEN[i+1]. EA nay chi hanh dong khi   |
//| co NEN MOI, va doc chi so tu shift 1 (nen VUA DONG), nen no vao o   |
//| open cua nen dang mo - dung mot moc voi Python.                     |
//+------------------------------------------------------------------+
#property copyright "The Brain"
#property version   "1.00"

#include <Trade\Trade.mqh>

input ENUM_TIMEFRAMES InpKhungTinHieu = PERIOD_D1; // khung tinh z-score
input int    InpN          = 5;      // chu ky z-score
input double InpNguongVao  = -1.0;   // vao khi z < nguong nay
input double InpNguongRa    = -1.0;  // ra khi z >= nguong nay
input int    InpGiuToiDa   = 500;    // tran so nen giu mot vi the
input double InpLot        = 0.10;   // lot CO DINH - xem ghi chu duoi
input long   InpMagic      = 20260906;

//--- Vi sao LOT CO DINH chu khong theo % von:
//--- bai nay de DOI CHIEU voi Python, ma `mo_phong.chay` tinh tren chuoi loi
//--- suat voi phoi nhiem 0/1 (khong lai kep theo lot). Lot bien thien se lam
//--- hai ben lech nhau vi mot ly do khong lien quan gi den co che.
//--- [[model1-che-ra-lai-gia]] khong dinh o day (khong co TP/SL nho), nhung
//--- van chay Model=0 va Model=4 de doi chieu.

CTrade   trade;
datetime g_nen_cuoi = 0;
int      g_bar_vao   = 0;   // dem so nen da giu

//--- Y DINH CHO KHOP. 0 = khong co, 1 = mua, -1 = dong.
//---
//--- VI SAO CAN (do 06/09/2026): nen D1 doi luc 00:00, ma 00:00 nam NGOAI phien
//--- cua CFD chi so. EA hanh dong ngay tai moc do thi 460/463 lenh tra
//--- "Market closed" va bao cao ghi 3 lenh - doc y het mot he gan nhu khong bao
//--- gio vao lenh. Nay EA GHI NHO y dinh roi khop o nen H1 dau tien co the giao
//--- dich trong ngay. Do cung la cach mot bot that phai chay
//--- [[v6-van-hanh-thuc-te]], khong phai mot meo cua tester.
int      g_y_dinh   = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetTypeFillingBySymbol(_Symbol);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| z-score cua close tai `shift`, tinh tren n nen KET THUC o shift.  |
//| Tra false neu khong du du lieu - KHONG tra 0, vi z=0 la mot gia   |
//| tri co nghia va se lam EA hanh dong tren mot con so bia ra.       |
//+------------------------------------------------------------------+
bool ZScore(int shift, int n, double &z)
{
   if(n < 2) return(false);
   double c[];
   if(CopyClose(_Symbol, InpKhungTinHieu, shift, n, c) != n) return(false);

   double tong = 0.0;
   for(int i = 0; i < n; i++) tong += c[i];
   double tb = tong / n;

   double sq = 0.0;
   for(int i = 0; i < n; i++) sq += (c[i] - tb) * (c[i] - tb);
   double sd = MathSqrt(sq / n);          // ddof = 0, khop pandas
   if(sd <= 0.0) return(false);

   z = (c[n - 1] - tb) / sd;
   return(true);
}

//+------------------------------------------------------------------+
bool DangMo()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic)
         return(true);
   }
   return(false);
}

//+------------------------------------------------------------------+
void DongHet()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic)
         trade.PositionClose(tk);
   }
}

//+------------------------------------------------------------------+
void OnTick()
{
   KhopYDinh();          // y dinh cua hom truoc, khop khi thi truong mo

   // CHI HANH DONG KHI CO NEN MOI TREN KHUNG TIN HIEU (mac dinh D1). Khong co
   // chan nay thi EA doc lai cung mot z-score hang nghin lan trong mot nen va
   // dat lai lenh lien tuc - ket qua se khong con lien quan gi den luat.
   //
   // VI SAO CHAY EA TREN H1 MA TIN HIEU LAY TU D1 (sua 06/09/2026):
   // Chay thang tren khung D1 voi Model=2 thi MT5 dat tick o OPEN cua nen D1,
   // tuc 00:00 - NGOAI phien giao dich cua CFD chi so. Ket qua: 463 lenh deu
   // tra "Market closed", bao cao ghi 0 lenh. Con Model=1/0 thi phai SINH tick
   // M1 cho 15 nam va chet vi het dia (20.480 MB cache).
   // Chay tren H1: moi nen H1 deu nam trong phien, va EA hanh dong o nen H1 dau
   // tien SAU khi nen D1 dong - dung mot moc voi Python (`mo_phong` dich mot
   // bar: tin hieu tai close[i] -> vao o dau bar i+1).
   datetime t = (datetime)SeriesInfoInteger(_Symbol, InpKhungTinHieu,
                                            SERIES_LASTBAR_DATE);
   if(t == g_nen_cuoi) return;
   g_nen_cuoi = t;

   double z;
   if(!ZScore(1, InpN, z)) return;        // shift 1 = nen VUA DONG

   if(DangMo())
   {
      g_bar_vao++;
      g_y_dinh = (z >= InpNguongRa || g_bar_vao >= InpGiuToiDa) ? -1 : 0;
   }
   else
      g_y_dinh = (z < InpNguongVao) ? 1 : 0;
}

//+------------------------------------------------------------------+
//| Khop y dinh o nen dau tien CO THE giao dich. Goi moi tick.        |
//+------------------------------------------------------------------+
void KhopYDinh()
{
   if(g_y_dinh == 0) return;
   if((ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE)
      != SYMBOL_TRADE_MODE_FULL) return;

   if(g_y_dinh < 0)
   {
      if(!DangMo()) { g_y_dinh = 0; return; }
      DongHet();
      if(!DangMo()) { g_bar_vao = 0; g_y_dinh = 0; }
      return;
   }
   if(DangMo()) { g_y_dinh = 0; return; }
   if(trade.Buy(InpLot, _Symbol)) { g_bar_vao = 0; g_y_dinh = 0; }
}
//+------------------------------------------------------------------+
