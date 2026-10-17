//+------------------------------------------------------------------+
//| BRAIN_XuLiLenh.mq5 - BO MAY XU LI LENH theo cach chu du an danh (17/10/2026)
//|
//| Chu du an: "phi giao dich, tinh diem gia chay, spread, cac cach entry, dca xu li lenh khi sai,
//| trailing vi the co loi, hedging can bang lenh" - day la phan quyet dinh tien, phai chay tren MT5
//| de CHINH SAN tinh diem / spread / swap / hoa hong (Python tung doan sai point o 214/407 ma XM).
//|
//| Mot RO lenh moi chieu (ro MUA, ro BAN), quan li bang GIA (don vi gia cua ma, vd US500 "5 gia")
//| hoac boi so ATR cua khung tin hieu:
//|   VAO       tin hieu nen DA DONG (MRZ z-score / RSI / Donchian) hoac KHONG tin hieu (PMG: luon co ro)
//|   DCA       nhoi NGHICH khi gia di nguoc 1 buoc (buoc gian dan x g), hoac nhoi THUAN theo chieu gia chay
//|   LOT       deu / tang tuyen tinh / nhan he so r theo tang
//|   TP RO     gia von binh quan +/- TP (gia hoac ATR)
//|   TRAILING  khi gia vuot gia von + kich hoat: bam dinh, tra lai 'khoang' thi dong ca ro
//|   HEDGE     ro lo tha noi >= X % so du: mo lenh NGUOC cung khoi luong x ti le (khoa) - mo khoa khi
//|             gia hoi tu cuc tri - GO: tong ro + hedge >= muc tien thi dong het
//|   BAO VE    khong nhoi/hedge khi margin level < muc; khong mo lenh trong gio cam (doi ngay spread gian)
//|             hoac khi spread > tran; cat lo ro tuy chon (0 = khong SL, dung cach chu du an danh)
//| Ghi log CSV (Common\Files) cung dinh dang BRAIN_V24 -> do_phi_xm.py doc duoc phi that.
//| BACKTEST / DEMO. Khong phai loi khuyen dau tu.
//+------------------------------------------------------------------+
#property copyright "brain2"
#property version   "1.00"
#include <Trade/Trade.mqh>

enum ENUM_VAO   { VAO_KHONG = 0, VAO_MRZ = 1, VAO_RSI = 2, VAO_DONCHIAN = 3 };
enum ENUM_NHOI  { NHOI_TAT = 0, NHOI_NGHICH = 1, NHOI_THUAN = 2 };
enum ENUM_LOT   { LOT_DEU = 0, LOT_TUYEN_TINH = 1, LOT_NHAN = 2 };

input group "VAO LENH"
input ENUM_VAO        InpVao          = VAO_MRZ;   // tin hieu vao (nen DA DONG cua InpTF)
input ENUM_TIMEFRAMES InpTF           = PERIOD_D1; // khung tin hieu + ATR
input int             InpN            = 50;        // chu ky MRZ / Donchian
input double          InpNguongZ      = 2.0;       // MRZ: |z| vao lenh
input double          InpRsiThap      = 30;        // RSI: mua khi <
input double          InpRsiCao       = 70;        // RSI: ban khi >
input int             InpChieuKhongTin = 1;        // VAO_KHONG: 1 chi mua, -1 chi ban, 0 ca hai
input int             InpChoNen       = 0;         // so nen InpTF cho sau khi dong ro moi mo ro moi
input double          InpLot0         = 0.01;      // lot tang dau

input group "DCA / NHOI"
input ENUM_NHOI       InpNhoi         = NHOI_NGHICH;
input double          InpBuocGia      = 0;         // buoc nhoi (don vi GIA); 0 -> dung InpBuocATR
input double          InpBuocATR      = 1.0;       // buoc nhoi (x ATR14 luc mo ro)
input double          InpGianBuoc     = 1.0;       // buoc tang k = buoc x g^k (1 = deu)
input ENUM_LOT        InpKieuLot      = LOT_DEU;
input double          InpHeSoLot      = 1.5;       // LOT_NHAN: lot_k = lot0 x r^k
input int             InpMaxTang      = 5;         // so lenh toi da moi ro (ke ca lenh dau)

input group "CHOT RO"
input double          InpTPGia        = 0;         // TP tu gia von binh quan (GIA); 0 -> InpTPATR
input double          InpTPATR        = 0.5;       // TP (x ATR14 luc mo ro); 0 = tat (chi trailing/go)
input double          InpTrailKichGia = 0;         // trailing bat khi gia vuot gia von + X (GIA); 0 -> ATR
input double          InpTrailKichATR = 1.0;       // (x ATR); 0 = tat trailing
input double          InpTrailKhoangGia = 0;       // tra lai X tu dinh thi dong ro (GIA); 0 -> ATR
input double          InpTrailKhoangATR = 0.5;     // (x ATR)
input int             InpGiuToiDaNen  = 0;         // dong ro sau N nen InpTF (0 = gong vo han)

input group "HEDGE / GO LENH"
input double          InpHedgeKhiLoPct = 0;        // ro lo tha noi >= X % so du -> khoa (0 = tat hedge)
input double          InpHedgeTiLe    = 1.0;       // khoi luong hedge = tong lot ro x ti le
input double          InpMoKhoaGia    = 0;         // mo khoa: dong hedge khi gia hoi X tu cuc tri (GIA); 0 -> ATR
input double          InpMoKhoaATR    = 1.0;       // (x ATR); 0 = khong tu mo khoa
input double          InpGoTien       = 0;         // GO: ro + hedge >= X (tien te tk) -> dong het
input int             InpHedgeMaxLan  = 3;         // so lan khoa toi da moi ro

input group "BAO VE TAI KHOAN"
input double          InpMarginMin    = 300;       // khong nhoi / hedge khi margin level < X % (0 = tat)
input double          InpCatLoPct     = 0;         // cat ca ro (+hedge) khi lo >= X % so du (0 = khong SL)
input int             InpGioCamTu     = 23;        // gio server bat dau cam MO lenh (doi ngay, spread gian)
input int             InpGioCamDen    = 2;         // ... den gio nay (cam tu <= gio < den, vong qua 0h)
input double          InpSpreadMaxGia = 0;         // khong mo lenh khi spread > X (GIA); 0 = tat
input long            InpMagic        = 2026101701;
input string          InpFileLog      = "brain2_xu_li_lenh_log.csv";
input bool            InpLogChung     = true;      // ghi vao Common\Files (lay duoc ca khi chay Tester)

CTrade   trade;
int      h_atr = INVALID_HANDLE, h_rsi = INVALID_HANDLE, h_ma = INVALID_HANDLE, h_sd = INVALID_HANDLE;
datetime g_nen = 0;
bool     g_hedging = false;
// thong ke cuoi ky (in ra log + Journal)
int      g_n_cu[2] = {0, 0};   // so lenh ro lan doc truoc (de biet ro vua dong het)
int      g_so_ro = 0, g_tang_max = 0, g_so_khoa = 0, g_so_go = 0, g_so_cat = 0, g_so_trail = 0, g_so_tp = 0, g_so_het_gio = 0;

struct Ro
{
   int      n;          // so lenh ro
   double   lot;        // tong lot
   double   gia_tb;     // gia von binh quan (theo lot)
   double   loi;        // lai/lo tha noi (profit + swap)
   double   gia_cuoi;   // gia lenh moi nhat
   datetime t_dau;      // gio lenh dau
   int      n_hedge;    // so lenh hedge dang mo cua ro nay
   double   lot_hedge;
   double   loi_hedge;
};

string Tag(int chieu)   { return chieu > 0 ? "XL_B" : "XL_S"; }     // lenh ro
string TagH(int chieu)  { return chieu > 0 ? "XL_HB" : "XL_HS"; }   // lenh hedge CUA ro do (chieu nguoc)
string GV(int chieu, string k) { return StringFormat("xl_%I64d_%s_%s_%s", InpMagic, _Symbol, chieu > 0 ? "B" : "S", k); }
double GVLay(string ten, double mac_dinh) { return GlobalVariableCheck(ten) ? GlobalVariableGet(ten) : mac_dinh; }

void GhiLog(string s)
{
   int co = FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_SHARE_READ | (InpLogChung ? FILE_COMMON : 0);
   int h = FileOpen(InpFileLog, co, ';');
   if(h == INVALID_HANDLE) return;
   FileSeek(h, 0, SEEK_END);
   FileWriteString(h, s + "\r\n");
   FileClose(h);
}

double ChuanLot(double v)
{
   double st = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP), mn = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), mx = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(st > 0) v = MathFloor(v / st + 1e-9) * st;
   return MathMax(mn, MathMin(mx, v));
}

double Lay1(int h, int buf = 0)
{
   double b[];
   if(h == INVALID_HANDLE || CopyBuffer(h, buf, 1, 1, b) != 1) return EMPTY_VALUE;
   return b[0];
}

bool DocRo(int chieu, Ro &r)
{
   r.n = 0; r.lot = 0; r.gia_tb = 0; r.loi = 0; r.gia_cuoi = 0; r.t_dau = 0; r.n_hedge = 0; r.lot_hedge = 0; r.loi_hedge = 0;
   datetime t_moi = 0; double tong = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      string c = PositionGetString(POSITION_COMMENT);
      double v = PositionGetDouble(POSITION_VOLUME), p = PositionGetDouble(POSITION_PRICE_OPEN);
      double l = PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
      datetime tt = (datetime)PositionGetInteger(POSITION_TIME);
      if(StringFind(c, TagH(chieu)) == 0) { r.n_hedge++; r.lot_hedge += v; r.loi_hedge += l; continue; }
      if(StringFind(c, Tag(chieu)) != 0) continue;
      r.n++; r.lot += v; tong += v * p; r.loi += l;
      if(tt >= t_moi) { t_moi = tt; r.gia_cuoi = p; }
      if(r.t_dau == 0 || tt < r.t_dau) r.t_dau = tt;
   }
   if(r.lot > 0) r.gia_tb = tong / r.lot;
   return r.n > 0;
}

void DongHet(int chieu, bool ca_hedge, string ly_do)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      string c = PositionGetString(POSITION_COMMENT);
      bool la_ro = StringFind(c, Tag(chieu)) == 0, la_h = StringFind(c, TagH(chieu)) == 0;
      if(la_ro || (ca_hedge && la_h)) trade.PositionClose(t);
   }
   GhiLog(StringFormat("%s;%s;dong_ro_%s;0;0;%.5f;%.5f;%d;0;0;0;%s", TimeToString(TimeCurrent()), _Symbol, chieu > 0 ? "mua" : "ban",
          SymbolInfoDouble(_Symbol, SYMBOL_BID), SymbolInfoDouble(_Symbol, SYMBOL_ASK), (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD), ly_do));
}

void DongHedge(int chieu)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      if(StringFind(PositionGetString(POSITION_COMMENT), TagH(chieu)) == 0) trade.PositionClose(t);
   }
}

bool GioCam()
{
   if(InpGioCamTu == InpGioCamDen) return false;
   MqlDateTime d; TimeToStruct(TimeCurrent(), d);
   if(InpGioCamTu < InpGioCamDen) return d.hour >= InpGioCamTu && d.hour < InpGioCamDen;
   return d.hour >= InpGioCamTu || d.hour < InpGioCamDen;       // vong qua 0h, vd 23 -> 2
}

bool DuocMo()
{
   if(GioCam()) return false;
   double sp = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(InpSpreadMaxGia > 0 && sp > InpSpreadMaxGia) return false;
   return true;
}

bool MarginDu()
{
   if(InpMarginMin <= 0) return true;
   double ml = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
   return ml <= 0 || ml >= InpMarginMin;            // 0 = chua dung margin
}

bool Mo(int chieu, double lot, string tag)
{
   lot = ChuanLot(lot);
   bool ok = chieu > 0 ? trade.Buy(lot, _Symbol, 0, 0, 0, tag) : trade.Sell(lot, _Symbol, 0, 0, 0, tag);
   return ok && (trade.ResultRetcode() == TRADE_RETCODE_DONE || trade.ResultRetcode() == TRADE_RETCODE_PLACED);
}

double LotTang(int k)          // k = 0 la lenh dau
{
   if(InpKieuLot == LOT_TUYEN_TINH) return InpLot0 * (k + 1);
   if(InpKieuLot == LOT_NHAN)       return InpLot0 * MathPow(InpHeSoLot, k);
   return InpLot0;
}

double KhoangGia(double gia, double atr_x, double atr) { return gia > 0 ? gia : atr_x * atr; }

int TinHieu()
{
   if(InpVao == VAO_KHONG) return 2;               // luon co ro (chieu theo InpChieuKhongTin)
   if(InpVao == VAO_RSI)
   {
      double r = Lay1(h_rsi);
      if(r == EMPTY_VALUE) return 0;
      return r < InpRsiThap ? 1 : (r > InpRsiCao ? -1 : 0);
   }
   if(InpVao == VAO_MRZ)
   {
      double m = Lay1(h_ma), s = Lay1(h_sd), c = iClose(_Symbol, InpTF, 1);
      if(m == EMPTY_VALUE || s == EMPTY_VALUE || s <= 0) return 0;
      double z = (c - m) / s;
      return z < -InpNguongZ ? 1 : (z > InpNguongZ ? -1 : 0);
   }
   // DONCHIAN: dong cua nen vua dong pha dinh/day N nen truoc do
   int ic = iHighest(_Symbol, InpTF, MODE_HIGH, InpN, 2), it = iLowest(_Symbol, InpTF, MODE_LOW, InpN, 2);
   if(ic < 0 || it < 0) return 0;
   double c1 = iClose(_Symbol, InpTF, 1);
   if(c1 > iHigh(_Symbol, InpTF, ic)) return 1;
   if(c1 < iLow(_Symbol, InpTF, it)) return -1;
   return 0;
}

// ---- quan li MOT ro, goi moi tick
void QuanLi(int chieu)
{
   Ro r;
   bool co = DocRo(chieu, r);
   if(!co)
   {
      if(r.n_hedge > 0) DongHedge(chieu);          // hedge mo coi (ro da dong) -> dong
      return;
   }
   string ga = GV(chieu, "atr");
   double atr = GlobalVariableCheck(ga) ? GlobalVariableGet(ga) : Lay1(h_atr);
   if(atr == EMPTY_VALUE || atr <= 0) return;
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID), ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double gia_thoat = chieu > 0 ? bid : ask, gia_vao = chieu > 0 ? ask : bid;
   double lai_gia = chieu * (gia_thoat - r.gia_tb);                     // gia da chay co loi tu gia von (don vi gia)
   double tong = r.loi + r.loi_hedge, so_du = AccountInfoDouble(ACCOUNT_BALANCE);
   if(r.n > g_tang_max) g_tang_max = r.n;

   // 1) cat lo tuy chon
   if(InpCatLoPct > 0 && tong <= -InpCatLoPct / 100.0 * so_du) { DongHet(chieu, true, "cat_lo"); g_so_cat++; return; }
   // 2) giu toi da
   if(InpGiuToiDaNen > 0 && iBarShift(_Symbol, InpTF, r.t_dau, false) >= InpGiuToiDaNen) { DongHet(chieu, true, "het_gio"); g_so_het_gio++; return; }

   if(r.n_hedge > 0)
   {
      // 3) dang KHOA: go khi tong >= muc; mo khoa khi gia hoi tu cuc tri
      if(tong >= InpGoTien) { DongHet(chieu, true, "go"); g_so_go++; return; }
      string gx = GV(chieu, "cuc_tri");
      double ct = GVLay(gx, gia_thoat);
      ct = chieu > 0 ? MathMin(ct, gia_thoat) : MathMax(ct, gia_thoat);
      GlobalVariableSet(gx, ct);
      double mk = KhoangGia(InpMoKhoaGia, InpMoKhoaATR, atr);
      if(mk > 0 && chieu * (gia_thoat - ct) >= mk)
      {
         DongHedge(chieu); GlobalVariableDel(gx);
         GlobalVariableSet(GV(chieu, "moc_khoa"), ct);   // chi khoa lai khi gia VUOT cuc tri nay (chong khoa/mo lien tuc)
      }
      return;                                       // khi khoa: khong nhoi, khong TP rieng ro
   }

   // 4) TP ro tu gia von
   double tp = KhoangGia(InpTPGia, InpTPATR, atr);
   if(tp > 0 && lai_gia >= tp) { DongHet(chieu, true, "tp"); g_so_tp++; return; }
   // 5) trailing ro
   double kich = KhoangGia(InpTrailKichGia, InpTrailKichATR, atr);
   if(kich > 0)
   {
      string gd = GV(chieu, "dinh");
      if(lai_gia >= kich || GlobalVariableCheck(gd))
      {
         double dinh = GVLay(gd, gia_thoat);
         dinh = chieu > 0 ? MathMax(dinh, gia_thoat) : MathMin(dinh, gia_thoat);
         GlobalVariableSet(gd, dinh);
         double kh = KhoangGia(InpTrailKhoangGia, InpTrailKhoangATR, atr);
         if(chieu * (dinh - gia_thoat) >= kh) { DongHet(chieu, true, "trailing"); g_so_trail++; return; }
      }
   }
   // 6) khoa (hedge) khi lo sau
   string gm = GV(chieu, "moc_khoa");
   bool vuot_moc = !GlobalVariableCheck(gm) || chieu * (gia_thoat - GlobalVariableGet(gm)) < 0;
   if(InpHedgeKhiLoPct > 0 && g_hedging && MarginDu() && GlobalVariableGet(GV(chieu, "so_khoa")) < InpHedgeMaxLan
      && r.loi <= -InpHedgeKhiLoPct / 100.0 * so_du && vuot_moc)
   {
      if(Mo(-chieu, r.lot * InpHedgeTiLe, TagH(chieu)))
      {
         GlobalVariableSet(GV(chieu, "so_khoa"), GlobalVariableGet(GV(chieu, "so_khoa")) + 1);
         GlobalVariableSet(GV(chieu, "cuc_tri"), gia_thoat);
         g_so_khoa++;
      }
      return;
   }
   // 7) nhoi (DCA nghich / nhoi thuan)
   if(InpNhoi == NHOI_TAT || r.n >= InpMaxTang || !DuocMo() || !MarginDu()) return;
   double buoc = KhoangGia(InpBuocGia, InpBuocATR, atr) * MathPow(InpGianBuoc, r.n - 1);
   if(buoc <= 0) return;
   bool can = InpNhoi == NHOI_NGHICH ? chieu * (r.gia_cuoi - gia_vao) >= buoc : chieu * (gia_vao - r.gia_cuoi) >= buoc;
   if(can) Mo(chieu, LotTang(r.n), Tag(chieu));
}

// tra true khi KHONG can thu lai trong nen nay (da mo, da co ro, dang cho InpChoNen); false = thu lai tick sau
bool MoRoMoi(int chieu)
{
   Ro r;
   if(DocRo(chieu, r)) return true;
   if(!DuocMo()) return false;
   if(InpChoNen > 0)
   {
      double t_dong = GVLay(GV(chieu, "t_dong"), 0);
      if(t_dong > 0 && iBarShift(_Symbol, InpTF, (datetime)(long)t_dong, false) < InpChoNen) return true;
   }
   double atr = Lay1(h_atr);
   if(atr == EMPTY_VALUE || atr <= 0) return true;
   if(!Mo(chieu, LotTang(0), Tag(chieu))) return false;   // vd [Market closed] luc 00h -> thu lai
   GlobalVariableSet(GV(chieu, "atr"), atr);       // buoc / TP co dinh theo ATR LUC MO RO (khong nhin truoc)
   GlobalVariableDel(GV(chieu, "dinh")); GlobalVariableDel(GV(chieu, "cuc_tri")); GlobalVariableDel(GV(chieu, "moc_khoa"));
   GlobalVariableSet(GV(chieu, "so_khoa"), 0);
   g_so_ro++;
   return true;
}

int OnInit()
{
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(50);
   g_hedging = AccountInfoInteger(ACCOUNT_MARGIN_MODE) == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING;
   if(InpHedgeKhiLoPct > 0 && !g_hedging) Print("CANH BAO: tai khoan NETTING -> khong hedge duoc, tat hedge");
   h_atr = iATR(_Symbol, InpTF, 14);
   if(InpVao == VAO_RSI) h_rsi = iRSI(_Symbol, InpTF, 14, PRICE_CLOSE);
   if(InpVao == VAO_MRZ) { h_ma = iMA(_Symbol, InpTF, InpN, 0, MODE_SMA, PRICE_CLOSE); h_sd = iStdDev(_Symbol, InpTF, InpN, 0, MODE_SMA, PRICE_CLOSE); }
   if(h_atr == INVALID_HANDLE) return INIT_FAILED;
   for(int c = -1; c <= 1; c += 2)
   {
      Ro r;
      if(!DocRo(c, r)) { GlobalVariableDel(GV(c, "atr")); GlobalVariableDel(GV(c, "dinh")); GlobalVariableDel(GV(c, "cuc_tri")); GlobalVariableDel(GV(c, "so_khoa")); GlobalVariableDel(GV(c, "moc_khoa")); }
      g_n_cu[c > 0 ? 0 : 1] = r.n;
   }
   GhiLog("thoi_gian;ma;su_kien;khoi_luong;gia;bid;ask;spread_point;swap;hoa_hong;loi;phu");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   string s = StringFormat("so_ro=%d tang_max=%d tp=%d trailing=%d khoa=%d go=%d cat_lo=%d het_gio=%d hedging=%s",
                           g_so_ro, g_tang_max, g_so_tp, g_so_trail, g_so_khoa, g_so_go, g_so_cat, g_so_het_gio, g_hedging ? "co" : "khong");
   Print("BRAIN_XuLiLenh ", _Symbol, " ", s);
   GhiLog(StringFormat("%s;%s;tong_ket;0;0;0;0;0;0;0;0;%s", TimeToString(TimeCurrent()), _Symbol, s));
}

double OnTester()
{
   return (double)g_tang_max;                       // cot "OnTester result" trong bao cao = so tang sau nhat da dung
}

void OnTick()
{
   QuanLi(1);
   QuanLi(-1);
   datetime t0 = iTime(_Symbol, InpTF, 0);
   if(t0 == 0) return;
   bool nen_moi = t0 != g_nen;
   if(InpVao == VAO_KHONG)
   {
      if(InpChieuKhongTin >= 0) MoRoMoi(1);
      if(InpChieuKhongTin <= 0) MoRoMoi(-1);
      g_nen = t0;
      return;
   }
   if(!nen_moi) return;
   int tin = TinHieu();
   if((tin == 1 || tin == -1) && !MoRoMoi(tin)) return;   // gio cam / spread gian / dong cua: thu lai tick sau CUNG nen
   g_nen = t0;
}

void OnTradeTransaction(const MqlTradeTransaction &tr, const MqlTradeRequest &rq, const MqlTradeResult &rs)
{
   if(tr.type != TRADE_TRANSACTION_DEAL_ADD || !HistoryDealSelect(tr.deal)) return;
   if(HistoryDealGetInteger(tr.deal, DEAL_MAGIC) != InpMagic || HistoryDealGetString(tr.deal, DEAL_SYMBOL) != _Symbol) return;
   long vao = HistoryDealGetInteger(tr.deal, DEAL_ENTRY);
   for(int c = -1; c <= 1; c += 2)            // ro chieu c vua dong het -> ghi gio dong cho InpChoNen
   {
      Ro r; DocRo(c, r);
      int i = c > 0 ? 0 : 1;
      if(r.n == 0 && g_n_cu[i] > 0) GlobalVariableSet(GV(c, "t_dong"), (double)TimeCurrent());
      g_n_cu[i] = r.n;
   }
   GhiLog(StringFormat("%s;%s;%s;%.2f;%.5f;%.5f;%.5f;%d;%.2f;%.2f;%.2f;%s",
          TimeToString(TimeCurrent()), _Symbol, vao == DEAL_ENTRY_IN ? "vao" : "ra",
          HistoryDealGetDouble(tr.deal, DEAL_VOLUME), HistoryDealGetDouble(tr.deal, DEAL_PRICE),
          SymbolInfoDouble(_Symbol, SYMBOL_BID), SymbolInfoDouble(_Symbol, SYMBOL_ASK),
          (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD), HistoryDealGetDouble(tr.deal, DEAL_SWAP),
          HistoryDealGetDouble(tr.deal, DEAL_COMMISSION), HistoryDealGetDouble(tr.deal, DEAL_PROFIT),
          HistoryDealGetString(tr.deal, DEAL_COMMENT)));
}
//+------------------------------------------------------------------+
