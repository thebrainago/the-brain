# -*- coding: utf-8 -*-
"""dich_mq5_quan_tri.py - EA GHEP CO QUAN TRI VI THE.

Chu du an 07/09/2026: *"Ta co toi da loi nhuan bang cach dung trailing stop, tia
lenh, hold lenh cua 1 chan den toi da cho toi khi co entry cua chan con lai
khong? Hoac bat ky kieu quan li lenh kieu gi ma ta co the tao ra."*

Ba ly do bai nay dang lam, deu la so da do cua chinh du an:

- **`trailing` la co che manh nhat tung do duoc**: lai holdout x4,8, sut giam
  giam 15 lan [[trailing-la-co-che-manh-nhat-do-duoc]].
- **Quan tri vi the LON HON entry**: entry co tinh SAI van cho 92-97%/nam, va
  loc "dung chieu" con TE HON loc dao nguoc [[quan-tri-vi-the-lon-hon-entry]].
- **Kho co 262 co che toan la tin hieu VAO, 0 co che quan tri**
  [[quan-tri-la-ho-co-che-thu-hai]] — tuc ca mot ho con trong.

Va EA ghep hom nay **khong co mot dong quan tri nao**: chi giu du `giu` nen roi
thoat. Do la cho trong lon nhat con lai.

## BON KIEU RA, LA THAM SO TOI UU HOA

    InpKieuRa = 0   nhu cu: `ra` cua co che, hoac du `giu` nen
                1   GIU DEN KHI CHAN KIA CO TIN HIEU VAO  <-- y cua chu du an
                2   trailing k x ATR tu dinh loi
                3   ca 1 va 2 (cai nao den truoc)

`InpTrailATR` (so lan ATR) va `InpTiaATR` (tia mot nua vi the o k x ATR loi) la
tham so rieng. Tat ca deu la chieu toi uu hoa, nen **mot lan boot tra loi ca cau
"quan tri nao dang tien"** [[tester-nhoi-het-vao-mot-lan-boot]].

## VI SAO "GIU DEN KHI CHAN KIA VAO" CHI LAM DUOC O DAY

Hai co che nam trong CUNG mot EA, nen luc chan A dang mo thi `CoVao(B)` co san
trong tay. Kien truc chay hai EA roi cong duong von o Python khong bao gio hoi
duoc cau do.

## BAY

- **Tia lenh o lot toi thieu**: `PositionClosePartial` voi khoi luong nho hon
  `SYMBOL_VOLUME_MIN` **that bai im lang**. Phai kiem truoc, khong thi bang so
  se giong het ban khong tia va ta se ket luan "tia khong an thua".
- **Trailing tren nen KHUNG, khong phai tung tick**: bai nay do co che, khong do
  toc do khop. Trailing tung tick can Model=4 va se doi ca ket luan
  [[model1-che-ra-lai-gia]].
"""
from __future__ import annotations

from .dich_mq5 import SPEC_MUA_GIU, BoDich, KhongDichDuoc  # noqa: F401

MAU = r"""//+------------------------------------------------------------------+
//| %(ten)s - SINH TU DONG boi nhan/dich_mq5_quan_tri.py. KHONG SUA TAY.
//| %(n)d co che chay DONG THOI + quan tri vi the (kieu ra la tham so).
//+------------------------------------------------------------------+
#property copyright "The Brain"
#include <Trade\Trade.mqh>

#define N_SLOT %(n)d
#define KHUNG PERIOD_%(khung)s

%(input_lot)s
input long   InpMagic    = %(magic)d;
//--- 0 nhu cu · 1 giu den khi chan kia vao · 2 trailing ATR · 3 ca hai
input int    InpKieuRa   = 0;
input double InpTrailATR = 2.0;    // khoang trailing, so lan ATR (kieu 2/3)
input double InpTrailTu  = 0.0;    // chi bat dau trailing sau khi loi >= k x ATR
input double InpBE       = 0.0;    // >0: dat hue (dong o entry) sau k x ATR loi
input double InpTiaATR   = 0.0;    // >0: tia mot nua vi the o k x ATR loi
//--- 0 = phai cho tin hieu TAT roi moi duoc vao lai (tranh vao lai ngay o nen
//--- ke tiep sau khi vua bi dat hue quet ra); 1 = duoc vao lai ngay.
input int    InpVaoLai   = 1;
//--- 0 tat · 1 nhoi khi AM (DCA) · 2 nhoi khi DUONG (kim tu thap)
input int    InpNhoi     = 0;
input double InpNhoiATR  = 1.0;    // khoang cach moi lan nhoi, so lan ATR
input double InpNhoiHeSo = 1.0;    // he so lot moi lan nhoi
input int    InpNhoiMax  = 2;      // so lan nhoi toi da
input int    InpGhi      = 0;
input string InpTep      = "%(tep)s";

%(khai_bao)s

int      h_atr_qt = INVALID_HANDLE;
CTrade   trade;
datetime g_nen_cuoi = 0;
int      g_bar_vao[N_SLOT];
int      g_y_dinh[N_SLOT];
double   g_thuc[N_SLOT];
double   g_lot[N_SLOT];
double   g_dinh[N_SLOT];          // gia tot nhat ke tu luc vao (theo chieu)
double   g_gia_vao[N_SLOT];       // gia vao cua lenh dau tien cua slot
bool     g_da_tia[N_SLOT];
bool     g_be_bat[N_SLOT];        // da tung dat nguong dat hue chua
bool     g_cho_tat[N_SLOT];       // dang cho tin hieu TAT truoc khi vao lai
int      g_so_nhoi[N_SLOT];
int      g_quet = 0;
int      g_tep  = INVALID_HANDLE;

double Chi(int h, int s)
  {
   if(h == INVALID_HANDLE) return(0.0);
   double b[];
   if(CopyBuffer(h, 0, s, 1, b) != 1) return(0.0);
   return(b[0]);
  }

%(ham)s

%(dieu_kien)s

bool CoVao(int k, int s)
  {
   switch(k)
     {
%(sw_vao)s
     }
   return(false);
  }

bool CoRa(int k, int s)
  {
   switch(k)
     {
%(sw_ra)s
     }
   return(false);
  }

int Chieu(int k) { switch(k) { %(sw_chieu)s } return(1); }
int Giu(int k)   { switch(k) { %(sw_giu)s } return(1); }
bool CoDieuKienRa(int k) { switch(k) { %(sw_cora)s } return(false); }

//+------------------------------------------------------------------+
int OnInit()
  {
   if((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE)
      != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      Print("DUNG LAI: tai khoan KHONG phai hedging.");
      return(INIT_FAILED);
     }
   trade.SetTypeFillingBySymbol(_Symbol);
   h_atr_qt = iATR(_Symbol, KHUNG, 14);
%(gan_lot)s
   for(int i = 0; i < N_SLOT; i++)
     { g_bar_vao[i]=0; g_y_dinh[i]=0; g_thuc[i]=0.0; g_dinh[i]=0.0;
       g_gia_vao[i]=0.0; g_da_tia[i]=false; g_be_bat[i]=false;
       g_cho_tat[i]=false; g_so_nhoi[i]=0; }
%(khoi_tao)s
   if(InpGhi == 1)
     {
      g_tep = FileOpen(InpTep, FILE_WRITE | FILE_CSV | FILE_COMMON, ',');
      if(g_tep != INVALID_HANDLE)
        {
         string d = "thoi_gian,gia";
         for(int i = 0; i < N_SLOT; i++)
            d += ",von" + IntegerToString(i) + ",mo" + IntegerToString(i);
         FileWrite(g_tep, d);
        }
     }
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int ly_do)
  { if(g_tep != INVALID_HANDLE) { FileClose(g_tep); g_tep = INVALID_HANDLE; } }

ulong VeCua(int slot)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic + slot) return(tk);
     }
   return(0);
  }

bool DangMo(int slot) { return(VeCua(slot) != 0); }

//--- Dong HET vi the cua slot: co nhoi lenh thi mot slot giu nhieu vi the.
void DongSlot(int slot)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic + slot)
         trade.PositionClose(tk);
     }
  }

int SoViThe(int slot)
  {
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic + slot) n++;
     }
   return(n);
  }

double NoiTai(int slot)
  {
   double v = 0.0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic + slot) continue;
      v += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
     }
   return(v);
  }

void CapNhatThuc()
  {
   if(!HistorySelect(0, TimeCurrent())) return;
   int tong = HistoryDealsTotal();
   for(int i = g_quet; i < tong; i++)
     {
      ulong tk = HistoryDealGetTicket(i);
      if(tk == 0) continue;
      int s = (int)(HistoryDealGetInteger(tk, DEAL_MAGIC) - InpMagic);
      if(s < 0 || s >= N_SLOT) continue;
      g_thuc[s] += HistoryDealGetDouble(tk, DEAL_PROFIT)
                 + HistoryDealGetDouble(tk, DEAL_SWAP)
                 + HistoryDealGetDouble(tk, DEAL_COMMISSION);
     }
   g_quet = tong;
  }

void KhopYDinh(int slot)
  {
   if(g_y_dinh[slot] == 0 || g_lot[slot] <= 0.0) return;
   if((ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE)
      != SYMBOL_TRADE_MODE_FULL) return;
   trade.SetExpertMagicNumber(InpMagic + slot);
   if(g_y_dinh[slot] < 0)
     {
      if(!DangMo(slot)) { g_y_dinh[slot] = 0; return; }
      DongSlot(slot);
      if(!DangMo(slot)) { g_bar_vao[slot]=0; g_y_dinh[slot]=0;
                          g_dinh[slot]=0.0; g_da_tia[slot]=false; }
      return;
     }
   if(DangMo(slot)) { g_y_dinh[slot] = 0; return; }
   bool ok = (Chieu(slot) > 0) ? trade.Buy(g_lot[slot], _Symbol)
                               : trade.Sell(g_lot[slot], _Symbol);
   if(ok)
     {
      g_bar_vao[slot] = 0; g_y_dinh[slot] = 0; g_da_tia[slot] = false;
      g_be_bat[slot] = false; g_so_nhoi[slot] = 0;
      g_dinh[slot] = (Chieu(slot) > 0) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                                       : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      ulong tk = VeCua(slot);
      g_gia_vao[slot] = (tk != 0 && PositionSelectByTicket(tk))
                        ? PositionGetDouble(POSITION_PRICE_OPEN) : g_dinh[slot];
     }
  }

//--- Loi hien tai cua slot, do bang DON VI GIA tren lenh dau tien (khong dung
//--- tien: tien phu thuoc lot, ma quan tri thi phai doc theo bien dong gia).
double LoiGia(int slot)
  {
   if(g_gia_vao[slot] <= 0.0) return(0.0);
   double gia = (Chieu(slot) > 0) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                                  : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   return((Chieu(slot) > 0) ? (gia - g_gia_vao[slot])
                            : (g_gia_vao[slot] - gia));
  }

//--- DAT HUE: sau khi da loi >= InpBE x ATR thi dong ngay khi gia quay ve entry.
//--- Day la "dua SL ve entry" o do phan giai NEN. Chu du an uu tien cai nay de
//--- bao toan, va no CO gia: lenh bi quet ra roi gia di tiep thi ta mat ca doan
//--- sau - do la ly do phai co `InpVaoLai`.
bool DatHueCham(int slot, double atr)
  {
   if(InpBE <= 0.0 || atr <= 0.0) return(false);
   double loi = LoiGia(slot);
   if(!g_be_bat[slot] && loi >= InpBE * atr) g_be_bat[slot] = true;
   return(g_be_bat[slot] && loi <= 0.0);
  }

//--- NHOI LENH. Canh bao tu chinh du an: "nhoi lenh theo chieu + chot khi tong
//--- lai" da do 18/18 cau hinh AM [[khung-ngan-va-orderflow]]. Nen o day nhoi
//--- la mot THAM SO de do lai tren nen nay, khong phai mot gia dinh.
void Nhoi(int slot, double atr)
  {
   if(InpNhoi == 0 || atr <= 0.0 || g_so_nhoi[slot] >= InpNhoiMax) return;
   if(g_gia_vao[slot] <= 0.0) return;
   double loi = LoiGia(slot);
   double can = (g_so_nhoi[slot] + 1) * InpNhoiATR * atr;
   bool dat = (InpNhoi == 1) ? (loi <= -can) : (loi >= can);
   if(!dat) return;
   double vol = g_lot[slot] * MathPow(InpNhoiHeSo, g_so_nhoi[slot] + 1);
   double b  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double mn = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   if(b > 0) vol = MathRound(vol / b) * b;
   if(vol < mn) vol = mn;
   trade.SetExpertMagicNumber(InpMagic + slot);
   bool ok = (Chieu(slot) > 0) ? trade.Buy(vol, _Symbol)
                               : trade.Sell(vol, _Symbol);
   if(ok) g_so_nhoi[slot]++;
  }

//--- Chan KIA co tin hieu vao khong. `slot` la chan dang mo.
bool ChanKiaVao(int slot)
  {
   for(int j = 1; j < N_SLOT; j++)      // slot 0 la moc mua-giu, bo qua
     {
      if(j == slot || g_lot[j] <= 0.0) continue;
      if(CoVao(j, 1)) return(true);
     }
   return(false);
  }

//--- Tia MOT NUA vi the o k x ATR loi. `PositionClosePartial` voi khoi luong
//--- duoi min volume THAT BAI IM LANG - kiem truoc, khong thi bang so se giong
//--- het ban khong tia.
void Tia(int slot, double atr)
  {
   if(InpTiaATR <= 0.0 || g_da_tia[slot] || atr <= 0.0) return;
   ulong tk = VeCua(slot);
   if(tk == 0 || !PositionSelectByTicket(tk)) return;
   double vao = PositionGetDouble(POSITION_PRICE_OPEN);
   double gia = PositionGetDouble(POSITION_PRICE_CURRENT);
   double loi = (Chieu(slot) > 0) ? (gia - vao) : (vao - gia);
   if(loi < InpTiaATR * atr) return;
   double vol = PositionGetDouble(POSITION_VOLUME) / 2.0;
   double b   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double mn  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   if(b > 0) vol = MathFloor(vol / b) * b;
   if(vol < mn) return;               // khong tia duoc - de nguyen, khong gia vo
   trade.SetExpertMagicNumber(InpMagic + slot);
   if(trade.PositionClosePartial(tk, vol)) g_da_tia[slot] = true;
  }

//--- Trailing tren NEN khung tin hieu (khong phai tung tick).
bool TrailingCham(int slot, double atr)
  {
   if(atr <= 0.0) return(false);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   // `InpTrailTu`: chua loi du muc do thi CHUA trailing - van cap nhat dinh.
   bool bat = (LoiGia(slot) >= InpTrailTu * atr);
   if(Chieu(slot) > 0)
     {
      if(bid > g_dinh[slot]) g_dinh[slot] = bid;
      return(bat && bid <= g_dinh[slot] - InpTrailATR * atr);
     }
   if(g_dinh[slot] == 0.0 || ask < g_dinh[slot]) g_dinh[slot] = ask;
   return(bat && ask >= g_dinh[slot] + InpTrailATR * atr);
  }

void OnTick()
  {
   for(int i = 0; i < N_SLOT; i++) KhopYDinh(i);

   datetime t = (datetime)SeriesInfoInteger(_Symbol, KHUNG, SERIES_LASTBAR_DATE);
   if(t == g_nen_cuoi) return;
   g_nen_cuoi = t;
   CapNhatThuc();
   double atr = Chi(h_atr_qt, 1);

   for(int i = 0; i < N_SLOT; i++)
     {
      if(g_lot[i] <= 0.0) { g_y_dinh[i] = 0; continue; }
      if(DangMo(i))
        {
         g_bar_vao[i]++;
         bool ra;
         // Slot 0 (moc mua-giu) KHONG chiu quan tri - moc phai giu nguyen y
         // nghia "mua roi nam im", neu khong thi khong con la moc nua.
         if(i == 0 || InpKieuRa == 0)
            ra = CoDieuKienRa(i) ? CoRa(i, 1) : (g_bar_vao[i] >= Giu(i));
         else
           {
            ra = false;
            if(InpKieuRa == 1 || InpKieuRa == 3) ra = ra || ChanKiaVao(i);
            if(InpKieuRa == 2 || InpKieuRa == 3) ra = ra || TrailingCham(i, atr);
            ra = ra || DatHueCham(i, atr);
            Tia(i, atr);
            if(!ra) Nhoi(i, atr);
           }
         if(ra || g_bar_vao[i] >= 500)
           { g_y_dinh[i] = -1; g_cho_tat[i] = (InpVaoLai == 0); }
         else
            g_y_dinh[i] = 0;
        }
      else
        {
         bool vao = CoVao(i, 1);
         // `InpVaoLai=0`: sau khi bi dat hue/trailing quet ra, phai cho tin
         // hieu TAT mot lan roi moi duoc vao lai - neu khong he se vao lai
         // ngay o nen ke tiep va dat hue thanh mot cai may dot phi.
         if(g_cho_tat[i])
           {
            if(!vao) g_cho_tat[i] = false;
            vao = false;
           }
         g_y_dinh[i] = vao ? 1 : 0;
        }
     }

   if(g_tep != INVALID_HANDLE)
     {
      string d = TimeToString(t, TIME_DATE | TIME_MINUTES) + "," +
                 DoubleToString(iClose(_Symbol, KHUNG, 1), 2);
      for(int i = 0; i < N_SLOT; i++)
         d += "," + DoubleToString(g_thuc[i] + NoiTai(i), 2) +
              "," + (DangMo(i) ? "1" : "0");
      FileWrite(g_tep, d);
     }
  }
//+------------------------------------------------------------------+
"""


def sinh_ea_quan_tri(cac_spec: list[dict], ten: str = "GhepQuanTri",
                     khung: str = "D1", magic: int = 26091300,
                     tep: str = "QT.csv") -> tuple[str, list[dict]]:
    """Nhu `dich_mq5_ghep.sinh_ea_ghep` nhung EA co them quan tri vi the."""
    bd = BoDich()
    dat, dk_ma = [], []
    sw_vao, sw_ra, sw_chieu, sw_giu, sw_cora = [], [], [], [], []
    for c in cac_spec:
        bt_vao = bd.dieu_kien(c.get("vao") or [])
        co_ra = bool(c.get("ra"))
        bt_ra = bd.dieu_kien(c["ra"]) if co_ra else "false"
        k = len(dat)
        dk_ma.append("bool VAO%d(int s) { return(%s); }" % (k, bt_vao))
        dk_ma.append("bool RA%d(int s)  { return(%s); }" % (k, bt_ra))
        sw_vao.append("      case %d: return(VAO%d(s));" % (k, k))
        sw_ra.append("      case %d: return(RA%d(s));" % (k, k))
        sw_chieu.append("case %d: return(%d);" % (k, int(c.get("chieu", 1) or 1)))
        sw_giu.append("case %d: return(%d);" % (k, int(c.get("giu", 1) or 1)))
        sw_cora.append("case %d: return(%s);" % (k, "true" if co_ra else "false"))
        dat.append(c)
    if not dat:
        raise KhongDichDuoc("khong co slot nao")
    kb, kt = bd.khai_bao_chi_bao()
    ma = MAU % {
        "ten": ten, "n": len(dat), "khung": khung, "magic": magic, "tep": tep,
        "input_lot": "\n".join(
            "input double InpLot%d  = 0.10;    // %s" % (i, c["ten"][:48])
            for i, c in enumerate(dat)),
        "gan_lot": "\n".join("   g_lot[%d] = InpLot%d;" % (i, i)
                             for i in range(len(dat))),
        "khai_bao": kb, "khoi_tao": kt,
        "ham": "\n".join(bd.ham), "dieu_kien": "\n".join(dk_ma),
        "sw_vao": "\n".join(sw_vao), "sw_ra": "\n".join(sw_ra),
        "sw_chieu": " ".join(sw_chieu), "sw_giu": " ".join(sw_giu),
        "sw_cora": " ".join(sw_cora),
    }
    return ma, dat
