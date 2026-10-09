// ea_gia_lap.cpp - VO CHAY THU cho EA MQL5 tren cloud / may khong co MT5 (04/10/2026).
//
// Bien dich CHINH ma nguon .mq5 (nhan/ea_gia_lap.py bo dong #property / #include, GIU nguyen so dong) cung mot lop gia lap
// API MQL5 + mot SAN GIA (tai khoan HEDGING) chay theo tung tick:
//   - moi tick: cap nhat BID / ASK -> kiem TP / SL may chu (MUA: TP khi Bid >= TP, SL khi Bid <= SL; BAN: TP khi Ask <= TP, SL khi
//     Ask >= SL; khop DUNG muc TP / SL, hoac gia thi truong cua tick neu bat `--sl-thi-truong` cho SL) -> OnTick()
//   - MUA khop o ASK, BAN khop o BID; khong truot gia, khong swap, khong margin / stop-out (EA khong dung cac thu do)
// KHONG phai MT5: lenh `PositionGet*`, `CTrade`... chi mo phong hanh vi MT5 ma EA dung. No tra loi "logic EA co dung y khong"
// (so lenh, gia mo, lot, tia, TP khop engine nhan/luoi.py), KHONG tra loi "MT5 that se cho gi" - viec do cua tester o may nha.
//
// Dung:  ea_gia_lap <ticks.bin> <lenh.csv> <von> [--netting] [--contract=N] [--vmin=X] [--vmax=X] [--vstep=X] [--sl-thi-truong]
//                   [Ten=gia_tri ...]
//   --contract=N: kich thuoc hop dong (mac dinh 100000 = FX; vang XAUUSD = 100). --vmin / --vmax / --vstep: gioi han lot cua ma.
//   --sl-thi-truong: SL khop o GIA TICK (truot gia neu tick nhay qua SL); mac dinh khop DUNG muc SL (tester MT5 do duoc cho vang: 09/10).
//   ticks.bin = int64 n, roi 4 mang float64 do dai n: bid, spread (don vi GIA), thoi gian (giay), thoi gian bat dau nen.
//   --digits=N: so chu so thap phan cua ma (mac dinh 5; point = 10^-N). Dung N lon (7-8) khi chuoi tick min hon point that,
//   de lam tron TP cua EA khong lam lech quyet dinh so voi engine tinh bang so thuc.
//   Bien dich: -DEA_FILE="duong dan ma da bo #property" ; them -DGIA_LAP_CHI_CU_PHAP de bien `input` thanh const (bat loi
//   gan gia tri cho input - MQL5 cam) va bo bang gan ten.
#include <algorithm>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#define ulong unsigned long long
typedef long long datetime;
typedef std::string string;

// ---------------------------------------------------------------- hang so + kieu cua MQL5
enum ENUM_POSITION_TYPE { POSITION_TYPE_BUY = 0, POSITION_TYPE_SELL = 1 };
enum ENUM_POSITION_PROPERTY_INTEGER { POSITION_TICKET, POSITION_TIME, POSITION_TYPE, POSITION_MAGIC };
enum ENUM_POSITION_PROPERTY_DOUBLE { POSITION_VOLUME, POSITION_PRICE_OPEN, POSITION_SL, POSITION_TP, POSITION_PROFIT };
enum ENUM_POSITION_PROPERTY_STRING { POSITION_SYMBOL, POSITION_COMMENT };
enum ENUM_SYMBOL_INFO_DOUBLE { SYMBOL_BID, SYMBOL_ASK, SYMBOL_VOLUME_MIN, SYMBOL_VOLUME_MAX, SYMBOL_VOLUME_STEP,
                               SYMBOL_TRADE_CONTRACT_SIZE };
enum ENUM_SYMBOL_INFO_INTEGER { SYMBOL_DIGITS };
enum ENUM_ACCOUNT_INFO_INTEGER { ACCOUNT_MARGIN_MODE };
enum ENUM_ACCOUNT_MARGIN_MODE { ACCOUNT_MARGIN_MODE_RETAIL_NETTING, ACCOUNT_MARGIN_MODE_EXCHANGE,
                                ACCOUNT_MARGIN_MODE_RETAIL_HEDGING };
// Gia tri THAT cua MQL5 (M1 = 1 ... H1 = 16385 ... D1 = 16408). W1 / MN1 co tinh KHONG khai bao: EA dung chung -> loi bien dich, khong im lang sai.
enum ENUM_TIMEFRAMES { PERIOD_CURRENT = 0, PERIOD_M1 = 1, PERIOD_M2 = 2, PERIOD_M3 = 3, PERIOD_M4 = 4, PERIOD_M5 = 5, PERIOD_M6 = 6,
                       PERIOD_M10 = 10, PERIOD_M12 = 12, PERIOD_M15 = 15, PERIOD_M20 = 20, PERIOD_M30 = 30, PERIOD_H1 = 16385,
                       PERIOD_H2 = 16386, PERIOD_H3 = 16387, PERIOD_H4 = 16388, PERIOD_H6 = 16390, PERIOD_H8 = 16392,
                       PERIOD_H12 = 16396, PERIOD_D1 = 16408 };
enum { INIT_SUCCEEDED = 0, INIT_FAILED = 1, INIT_PARAMETERS_INCORRECT = 2 };

// ---------------------------------------------------------------- trang thai san gia
struct Pos
  {
   ulong ticket;
   int type;
   double vol, open, sl, tp, spread_mo;
   string comment;
   long long magic, tick_mo;
   datetime time_mo;                            // gio tick luc mo (POSITION_TIME)
  };

static string g_sym = "AUDCAD";
static double g_point = 1e-5;
static int g_digits = 5;
static double g_contract = 100000.0;
static double g_vmin = 0.01, g_vmax = 100.0, g_vstep = 0.01;
static double g_bid = 0.0, g_ask = 0.0;
static datetime g_time = 0, g_bar_time = 0;
static long long g_tick = 0;
static bool g_netting = false;

static std::vector<Pos> g_pos;
static ulong g_next_ticket = 1;
static int g_sel = -1;
static double g_balance = 0.0, g_von = 0.0, g_peak = 0.0, g_maxdd = 0.0, g_min_eq = 1e300;
static long long g_n_mo = 0, g_n_dong = 0, g_n_tp = 0, g_n_ea = 0, g_n_sl = 0;
static bool g_sl_thi_truong = false;           // SL khop o gia tick (true) hay dung muc SL (false, mac dinh)
static int g_max_open = 0;
static double g_max_lot_open = 0.0;
static FILE *g_csv = nullptr;

#define _Symbol g_sym
#define _Point g_point
#define _Digits g_digits

// ---------------------------------------------------------------- ham toan hoc / chuoi cua MQL5
static inline double MathAbs(double x) { return std::fabs(x); }
static inline double MathPow(double a, double b) { return std::pow(a, b); }
static inline double MathFloor(double x) { return std::floor(x); }
static inline double MathRound(double x) { return std::round(x); }
static inline double MathMax(double a, double b) { return a > b ? a : b; }
static inline double MathMin(double a, double b) { return a < b ? a : b; }
static inline double NormalizeDouble(double v, int d)
  {
   const double k = std::pow(10.0, d);
   return std::round(v * k) / k;
  }
static inline int StringLen(const string &s) { return (int)s.size(); }
static inline string StringSubstr(const string &s, int pos, int len = -1)
  {
   if(pos < 0 || pos > (int)s.size())
      return string();
   return len < 0 ? s.substr(pos) : s.substr(pos, len);
  }
static inline double StringToDouble(const string &s) { return std::atof(s.c_str()); }
static inline string DoubleToString(double v, int d)
  {
   char b[64];
   std::snprintf(b, sizeof b, "%.*f", d, v);
   return b;
  }
static inline string IntegerToString(long long v) { return std::to_string(v); }

static inline const char *fm(const string &s) { return s.c_str(); }
template <class T> static inline T fm(T v) { return v; }
static inline void Print(const string &s) { std::printf("LOG %s\n", s.c_str()); }
template <class... A> static inline void PrintFormat(const char *f, A... a)
  {
   char b[1024];
   std::snprintf(b, sizeof b, f, fm(a)...);
   std::printf("LOG %s\n", b);
  }

static inline datetime TimeCurrent() { return g_time; }
// iTime(.., PERIOD_CURRENT, 0) = nen cua khung bieu do (do chuoi tick quyet: `bar`). Khung ro (M1..D1) = gio tick cat xuong boi so cua khung
// (gio may chu coi nhu epoch giay, D1 mo luc 00:00 may chu). shift != 0 KHONG ho tro -> dung chuong trinh (truoc 09/10 tra nen hien tai im lang).
static inline long long giay_khung(ENUM_TIMEFRAMES tf)
  {
   if(tf < 16384)
      return 60LL * (long long)tf;
   return tf < 32768 ? 3600LL * (long long)(tf - 16384) : 86400LL;
  }
static inline datetime iTime(const string &, ENUM_TIMEFRAMES tf, int shift)
  {
   if(shift != 0)
     {
      std::printf("LOI iTime shift=%d: san gia chi ho tro shift 0\n", shift);
      std::exit(3);
     }
   if(tf == PERIOD_CURRENT)
      return g_bar_time;
   const long long g = giay_khung(tf);
   return (datetime)(((long long)g_time / g) * g);
  }

// ---------------------------------------------------------------- thong tin san / tai khoan
static inline double SymbolInfoDouble(const string &, ENUM_SYMBOL_INFO_DOUBLE p)
  {
   switch(p)
     {
      case SYMBOL_BID: return g_bid;
      case SYMBOL_ASK: return g_ask;
      case SYMBOL_VOLUME_MIN: return g_vmin;
      case SYMBOL_VOLUME_MAX: return g_vmax;
      case SYMBOL_VOLUME_STEP: return g_vstep;
      case SYMBOL_TRADE_CONTRACT_SIZE: return g_contract;
     }
   return 0.0;
  }
static inline long long SymbolInfoInteger(const string &, ENUM_SYMBOL_INFO_INTEGER) { return g_digits; }
static inline long long AccountInfoInteger(ENUM_ACCOUNT_INFO_INTEGER)
  {
   return g_netting ? ACCOUNT_MARGIN_MODE_RETAIL_NETTING : ACCOUNT_MARGIN_MODE_RETAIL_HEDGING;
  }

// ---------------------------------------------------------------- vi the (chon theo chi so, nhu PositionGetTicket cua MT5)
static inline int PositionsTotal() { return (int)g_pos.size(); }
static inline ulong PositionGetTicket(int i)
  {
   if(i < 0 || i >= (int)g_pos.size())
     {
      g_sel = -1;
      return 0;
     }
   g_sel = i;
   return g_pos[i].ticket;
  }
static inline long long PositionGetInteger(ENUM_POSITION_PROPERTY_INTEGER p)
  {
   if(g_sel < 0)
      return 0;
   const Pos &q = g_pos[g_sel];
   switch(p)
     {
      case POSITION_TICKET: return (long long)q.ticket;
      case POSITION_TIME: return q.time_mo;
      case POSITION_TYPE: return q.type;
      case POSITION_MAGIC: return q.magic;
     }
   return 0;
  }
static inline double PositionGetDouble(ENUM_POSITION_PROPERTY_DOUBLE p)
  {
   if(g_sel < 0)
      return 0.0;
   const Pos &q = g_pos[g_sel];
   switch(p)
     {
      case POSITION_VOLUME: return q.vol;
      case POSITION_PRICE_OPEN: return q.open;
      case POSITION_SL: return q.sl;
      case POSITION_TP: return q.tp;
      case POSITION_PROFIT: return 0.0;
     }
   return 0.0;
  }
static inline string PositionGetString(ENUM_POSITION_PROPERTY_STRING p)
  {
   if(g_sel < 0)
      return string();
   return p == POSITION_SYMBOL ? g_sym : g_pos[g_sel].comment;
  }

// ---------------------------------------------------------------- ghi lenh da dong + so lieu
static double lai_lenh(const Pos &q, double gia_dong)
  {
   return (q.type == POSITION_TYPE_BUY ? gia_dong - q.open : q.open - gia_dong) * q.vol * g_contract;
  }

static void dong_vi_the(int idx, double gia_dong, int ly_do)   // ly_do: 0 = TP may chu, 1 = EA, 2 = SL may chu
  {
   const Pos q = g_pos[idx];
   g_balance += lai_lenh(q, gia_dong);
   g_n_dong++;
   if(ly_do == 0)
      g_n_tp++;
   else if(ly_do == 2)
      g_n_sl++;
   else
      g_n_ea++;
   if(g_csv)
      std::fprintf(g_csv, "%llu,%d,%.4f,%.8f,%.8f,%lld,%lld,%s,%.8f,%s\n", q.ticket, q.type, q.vol, q.open, gia_dong,
                   q.tick_mo, g_tick, ly_do == 0 ? "tp" : ly_do == 2 ? "sl" : "ea", q.spread_mo, q.comment.c_str());
   g_pos.erase(g_pos.begin() + idx);
  }

static unsigned int g_retcode = 10009;
static string g_retmsg = "done";

class CTrade
  {
   ulong m_magic = 0;

   bool mo(int type, double vol, const string &comment)
     {
      const double so_buoc = vol / g_vstep;
      if(!(vol >= g_vmin - 1e-9 && vol <= g_vmax + 1e-9 && std::fabs(so_buoc - std::round(so_buoc)) < 1e-6))
        {
         g_retcode = 10014;
         g_retmsg = "invalid volume";
         return false;
        }
      Pos q;
      q.ticket = g_next_ticket++;
      q.type = type;
      q.vol = vol;
      q.open = type == POSITION_TYPE_BUY ? g_ask : g_bid;
      q.sl = 0.0;
      q.tp = 0.0;
      q.spread_mo = g_ask - g_bid;
      q.comment = comment.substr(0, 31);          // MT5 cat comment o 31 ky tu
      q.magic = (long long)m_magic;
      q.tick_mo = g_tick;
      q.time_mo = g_time;
      g_pos.push_back(q);
      g_n_mo++;
      g_retcode = 10009;
      g_retmsg = "done";
      return true;
     }

public:
   void SetExpertMagicNumber(ulong m) { m_magic = m; }
   void SetDeviationInPoints(ulong) {}
   bool SetTypeFillingBySymbol(const string &) { return true; }
   bool Buy(double vol, const string &, double, double, double, const string &comment)
     {
      return mo(POSITION_TYPE_BUY, vol, comment);
     }
   bool Sell(double vol, const string &, double, double, double, const string &comment)
     {
      return mo(POSITION_TYPE_SELL, vol, comment);
     }
   bool PositionModify(ulong ticket, double sl, double tp)
     {
      for(auto &q : g_pos)
         if(q.ticket == ticket)
           {
            q.sl = sl;
            q.tp = tp;
            g_retcode = 10009;
            g_retmsg = "done";
            return true;
           }
      g_retcode = 10036;
      g_retmsg = "position doesn't exist";
      return false;
     }
   bool PositionClose(ulong ticket)
     {
      for(int i = 0; i < (int)g_pos.size(); i++)
         if(g_pos[i].ticket == ticket)
           {
            dong_vi_the(i, g_pos[i].type == POSITION_TYPE_BUY ? g_bid : g_ask, 1);
            g_retcode = 10009;
            g_retmsg = "done";
            return true;
           }
      g_retcode = 10036;
      g_retmsg = "position doesn't exist";
      return false;
     }
   unsigned int ResultRetcode() const { return g_retcode; }
   string ResultRetcodeDescription() const { return g_retmsg; }
  };

// ---------------------------------------------------------------- MA EA (da bo #property / #include, giu so dong)
#ifdef GIA_LAP_CHI_CU_PHAP
#define input const
#else
#define input
#endif
#include EA_FILE
#undef input

#ifndef GIA_LAP_CHI_CU_PHAP
static bool gan_input(const string &n, double v)
  {
#define X(ten) \
   if(n == #ten) \
     { \
      ten = (decltype(ten))v; \
      return true; \
     }
#include REGISTRY_FILE
#undef X
   return false;
  }
#endif

// ---------------------------------------------------------------- vong tick
static void theo_doi_von()
  {
   double eq = g_balance;
   double lot = 0.0;
   for(const Pos &q : g_pos)
     {
      eq += (q.type == POSITION_TYPE_BUY ? g_bid - q.open : q.open - g_ask) * q.vol * g_contract;
      lot += q.vol;
     }
   if(eq > g_peak)
      g_peak = eq;
   if(g_peak > 0.0)
      g_maxdd = std::max(g_maxdd, (g_peak - eq) / g_peak);
   g_min_eq = std::min(g_min_eq, eq);
   g_max_open = std::max(g_max_open, (int)g_pos.size());
   g_max_lot_open = std::max(g_max_lot_open, lot);
  }

static void sl_tp_may_chu()
  {
   for(int i = (int)g_pos.size() - 1; i >= 0; i--)
     {
      const Pos &q = g_pos[i];
      const double eps = g_point * 1e-6;                   // nhieu dau phay dong khi gia = TP / SL dung tung chu so
      const bool mua = q.type == POSITION_TYPE_BUY;
      // TP truoc, roi SL. Mot lenh khong the cham ca hai tren cung mot tick (TP va SL nam hai phia gia mo), tru khi EA dat sai phia
      // (SL tren gia cho lenh MUA...) - khi do TP duoc uu tien nhu truoc day.
      if(q.tp > 0.0 && (mua ? g_bid + eps >= q.tp : g_ask <= q.tp + eps))
        {
         dong_vi_the(i, q.tp, 0);
         continue;
        }
      if(q.sl > 0.0 && (mua ? g_bid <= q.sl + eps : g_ask >= q.sl - eps))
         dong_vi_the(i, g_sl_thi_truong ? (mua ? g_bid : g_ask) : q.sl, 2);
     }
  }

int main(int argc, char **argv)
  {
   if(argc < 4)
     {
      std::fprintf(stderr, "dung: ea_gia_lap ticks.bin lenh.csv von [--netting] [Ten=gia_tri ...]\n");
      return 2;
     }
   g_von = g_balance = g_peak = std::atof(argv[3]);
#ifndef GIA_LAP_CHI_CU_PHAP
   for(int i = 4; i < argc; i++)
     {
      if(!std::strcmp(argv[i], "--netting"))
        {
         g_netting = true;
         continue;
        }
      if(!std::strncmp(argv[i], "--digits=", 9))
        {
         g_digits = std::atoi(argv[i] + 9);
         g_point = std::pow(10.0, -g_digits);
         continue;
        }
      if(!std::strncmp(argv[i], "--contract=", 11))
        {
         g_contract = std::atof(argv[i] + 11);
         continue;
        }
      if(!std::strncmp(argv[i], "--vmin=", 7))
        {
         g_vmin = std::atof(argv[i] + 7);
         continue;
        }
      if(!std::strncmp(argv[i], "--vmax=", 7))
        {
         g_vmax = std::atof(argv[i] + 7);
         continue;
        }
      if(!std::strncmp(argv[i], "--vstep=", 8))
        {
         g_vstep = std::atof(argv[i] + 8);
         continue;
        }
      if(!std::strcmp(argv[i], "--sl-thi-truong"))
        {
         g_sl_thi_truong = true;
         continue;
        }
      const char *e = std::strchr(argv[i], '=');
      if(!e || !gan_input(string(argv[i], e - argv[i]), std::atof(e + 1)))
        {
         std::fprintf(stderr, "input la: %s\n", argv[i]);
         return 2;
        }
     }
#endif
   FILE *f = std::fopen(argv[1], "rb");
   if(!f)
     {
      std::fprintf(stderr, "khong mo duoc %s\n", argv[1]);
      return 2;
     }
   long long n = 0;
   if(std::fread(&n, 8, 1, f) != 1 || n <= 0)
      return 2;
   std::vector<double> bid(n), spr(n), tm(n), bar(n);
   for(std::vector<double> *v : {&bid, &spr, &tm, &bar})
      if(std::fread(v->data(), 8, n, f) != (size_t)n)
         return 2;
   std::fclose(f);
   g_csv = std::fopen(argv[2], "w");
   if(g_csv)
      std::fprintf(g_csv, "ticket,type,vol,open,close,tick_mo,tick_dong,ly_do,spread_mo,comment\n");

   if(OnInit() != INIT_SUCCEEDED)
     {
      std::printf("RES init_ok 0\n");
      return 3;
     }
   for(long long i = 0; i < n; i++)
     {
      g_tick = i;
      g_bid = bid[i];
      g_ask = bid[i] + spr[i];
      g_time = (datetime)tm[i];
      g_bar_time = (datetime)bar[i];
      sl_tp_may_chu();
      OnTick();
      theo_doi_von();
     }
   OnDeinit(0);

   double eq = g_balance, chi_phi_con_mo = 0.0, sp_con_mo = 0.0, lot_con_mo = 0.0;
   for(const Pos &q : g_pos)
     {
      eq += (q.type == POSITION_TYPE_BUY ? g_bid - q.open : q.open - g_ask) * q.vol * g_contract;
      sp_con_mo += q.spread_mo * q.vol * g_contract;
      lot_con_mo += q.vol;
      if(g_csv)
         std::fprintf(g_csv, "%llu,%d,%.4f,%.8f,,%lld,,open,%.8f,%s\n", q.ticket, q.type, q.vol, q.open, q.tick_mo,
                      q.spread_mo, q.comment.c_str());
     }
   (void)chi_phi_con_mo;
   if(g_csv)
      std::fclose(g_csv);
   std::printf("RES init_ok 1\nRES n_tick %lld\nRES n_mo %lld\nRES n_dong %lld\nRES n_tp %lld\nRES n_ea %lld\nRES n_sl %lld\n", n,
               g_n_mo, g_n_dong, g_n_tp, g_n_ea, g_n_sl);
   std::printf("RES balance %.6f\nRES equity %.6f\nRES con_mo %d\nRES lot_con_mo %.4f\nRES spread_con_mo %.6f\n", g_balance, eq,
               (int)g_pos.size(), lot_con_mo, sp_con_mo);
   std::printf("RES max_open %d\nRES max_lot_open %.4f\nRES max_dd_pct %.6f\nRES min_equity %.6f\n", g_max_open, g_max_lot_open,
               g_maxdd * 100.0, g_min_eq);
   return 0;
  }
