# -*- coding: utf-8 -*-
"""dich_mq5_ghep.py - MOT EA CHAY NHIEU CO CHE CUNG LUC (ghep he thong).

Chu du an, cuoi phien 06/09/2026: *"He thong ban hay day, co chieu ban rat hop
li de can bang cho cac he thong khac. Mai ta se thu ca su ket hop he thong."*

`dich_mq5.sinh_ea` gop nhieu co che vao mot EA nhung chay **mot cai moi luot**
(`switch(InpMaCoChe)`) - do la cong cu de QUET. Bai ghep can thu khac: nhieu co
che chay **dong thoi**, moi cai giu vi the rieng, tren cung mot tai khoan.

## VI SAO PHAI CHUNG MOT EA, KHONG PHAI CONG HAI DUONG VON O PYTHON

Cong hai duong von rieng le bo mat ba thu co that: von chung (hai he cung mo
mot luc thi ky quy cong don), phi qua dem tinh tren tong vi the, va gio khop
that. [[v6-doi-chieu-dung-cach]]: moc so sanh chi co nghia neu di qua DUNG MOT
bo thuc thi.

## TAI KHOAN PHAI LA HEDGING

z5 chieu MUA, quantora chieu BAN - tren tai khoan NETTING hai lenh nguoc chieu
tu triet tieu nhau va moi phep do tach he tro thanh vo nghia. EA tu kiem
`ACCOUNT_MARGIN_MODE` va dung lai neu khong phai hedging, chu khong chay tiep
roi ghi mot bao cao trong ma doc nhu that.

## MOI SLOT MOT MAGIC

`magic = InpMagic + chi_so_slot`. Tat ca phep tach (vi the cua ai, lai cua ai)
deu di qua magic chu khong doan theo chieu lenh - z5 va `__mua_giu__` cung
chieu MUA nen doan theo chieu la sai.

## LOT = 0 NGHIA LA TAT SLOT

De quet `lot_A x lot_B` trong MOT luot optimization: pass co `lot_B = 0` chinh
la "he A chay mot minh", di qua dung bo thuc thi do. Khong can lan chay rieng.
"""
from __future__ import annotations

from .dich_mq5 import SPEC_MUA_GIU, BoDich, KhongDichDuoc  # noqa: F401

MAU = r"""//+------------------------------------------------------------------+
//| %(ten)s - SINH TU DONG boi nhan/dich_mq5_ghep.py. KHONG SUA TAY.
//| %(n)d co che chay DONG THOI, moi co che mot magic rieng.
//+------------------------------------------------------------------+
#property copyright "The Brain"
#include <Trade\Trade.mqh>

#define N_SLOT %(n)d
#define KHUNG PERIOD_%(khung)s

%(input_lot)s
input long   InpMagic = %(magic)d;
input int    InpGhi   = 0;            // 1 = ghi duong von tung nen ra CSV
input string InpTep   = "%(tep)s";

%(khai_bao)s

CTrade   trade;
datetime g_nen_cuoi = 0;
int      g_bar_vao[N_SLOT];
int      g_y_dinh[N_SLOT];
double   g_thuc[N_SLOT];           // lai da chot cua rieng slot
double   g_lot[N_SLOT];
int      g_quet = 0;               // so deal da cong vao g_thuc
int      g_tep  = INVALID_HANDLE;

double Chi(int h, int s)
  {
   if(h == INVALID_HANDLE) return(0.0);
   double b[];
   if(CopyBuffer(h, 0, s, 1, b) != 1) return(0.0);
   return(b[0]);
  }

%(ham)s

//--- vao/ra cua tung slot
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
      Print("DUNG LAI: tai khoan KHONG phai hedging - hai chieu se triet tieu.");
      return(INIT_FAILED);
     }
   trade.SetTypeFillingBySymbol(_Symbol);
%(gan_lot)s
   for(int i = 0; i < N_SLOT; i++)
     { g_bar_vao[i] = 0; g_y_dinh[i] = 0; g_thuc[i] = 0.0; }
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
  {
   if(g_tep != INVALID_HANDLE) { FileClose(g_tep); g_tep = INVALID_HANDLE; }
  }

bool DangMo(int slot)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic + slot) return(true);
     }
   return(false);
  }

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

//--- Cong lai DA CHOT vao dung slot. Quet TANG DAN: deal chi duoc them vao
//--- cuoi lich su nen chi so da quet khong bao gio lech.
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

//--- Khop y dinh o nen dau tien CO THE giao dich: nen khung tin hieu doi luc
//--- 00:00 nam NGOAI phien cua CFD chi so, hanh dong ngay tai do thi moi lenh
//--- tra "Market closed" va bao cao ghi 0 lenh.
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
      if(!DangMo(slot)) { g_bar_vao[slot] = 0; g_y_dinh[slot] = 0; }
      return;
     }
   if(DangMo(slot)) { g_y_dinh[slot] = 0; return; }
   bool ok = (Chieu(slot) > 0) ? trade.Buy(g_lot[slot], _Symbol)
                               : trade.Sell(g_lot[slot], _Symbol);
   if(ok) { g_bar_vao[slot] = 0; g_y_dinh[slot] = 0; }
  }

void OnTick()
  {
   for(int i = 0; i < N_SLOT; i++) KhopYDinh(i);

   datetime t = (datetime)SeriesInfoInteger(_Symbol, KHUNG, SERIES_LASTBAR_DATE);
   if(t == g_nen_cuoi) return;
   g_nen_cuoi = t;
   CapNhatThuc();

   for(int i = 0; i < N_SLOT; i++)
     {
      if(g_lot[i] <= 0.0) { g_y_dinh[i] = 0; continue; }
      if(DangMo(i))
        {
         g_bar_vao[i]++;
         bool ra = CoDieuKienRa(i) ? CoRa(i, 1) : (g_bar_vao[i] >= Giu(i));
         g_y_dinh[i] = (ra || g_bar_vao[i] >= 500) ? -1 : 0;
        }
      else
         g_y_dinh[i] = CoVao(i, 1) ? 1 : 0;
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


def sinh_ea_ghep(cac_spec: list[dict], ten: str = "GhepHe", khung: str = "D1",
                 magic: int = 26090701, tep: str = "GHEP_VON.csv"
                 ) -> tuple[str, list[dict]]:
    """Sinh MOT EA cho N co che chay DONG THOI. Tra (ma nguon, spec da dich).

    Khac `dich_mq5.sinh_ea`: o day `slot` == chi so co che, va tat ca cac slot
    cung song trong mot lan chay. Co che nao khong dich duoc thi NEM loi chu
    khong bo im lang - danh sach slot o day la do nguoi chon, khong phai ca kho.
    """
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
