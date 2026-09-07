# -*- coding: utf-8 -*-
"""_stop_hai_dau.py - HE THANG BANG QUAN LY LENH: dat stop hai dau, cai nao khop
thi chot cuc nhanh.

Chu du an 07/09/2026: *"Toi con biet gio nguoi ta se co co che danh lenh stop 2
dau. Khi gia chay 1 dau gia se khop lenh va ho chot cuc nhanh. Nghia la 1 he
thong thang chi nho quan li lenh."*

Dung - va day la loai he **khong co tin hieu vao nao ca**. No khong doan huong;
no dat hai lenh cho o hai phia roi de thi truong chon, va toan bo ket qua nam o
bon con so: khoang cach dat lenh · chot · dung lo · han lenh cho.

## VI SAO BAI NAY PHAI CHAY `Model=0`, VA VI SAO PHAI DOI CHIEU `Model=4`

Day la dung cai ho hang ma du an da sap bay mot lan: `Model=1` che ra lai gia
**12 lan** khi TP nho hon 2x bien do nen M1 [[model1-che-ra-lai-gia]]. Ly do:
mo hinh nen gia dinh mot duong di O->H->L->C, nen mot TP nam gon trong nen
**luon** duoc "khop" o chan thuan loi.

He stop hai dau la truong hop XAU NHAT cua bay do:
  - lenh cho khop trong nen, khong phai o gia mo;
  - "chot cuc nhanh" nghia la TP nho hon bien do nen;
  - va ca hai dau deu co the bi cham trong CUNG mot nen (whipsaw) - thu ma mo
    hinh nen khong bao gio the hien.

Nen: chay `Model=0` (every tick), va neu ket qua duong thi **bat buoc chay lai
`Model=4` (tick THAT cua san)** truoc khi tin. Hai mo hinh khop nhau thi tin;
lech nhau thi con so la cua mo hinh, khong phai cua thi truong.

## BON CAU HOI, LA BON CHIEU TOI UU HOA

    InpKhoang   dat lenh cach gia bao nhieu ATR
    InpTP       chot o bao nhieu ATR          <- "chot cuc nhanh"
    InpSL       dung lo o bao nhieu ATR
    InpHan      lenh cho song bao nhieu nen roi huy

Va mot cong tac quan trong: `InpHuyDauKia` - khi mot dau khop thi huy dau con
lai hay giu no. Giu no lai bien he thanh **hedge hai chieu**, khac han.

Chay: python _stop_hai_dau.py [SYMBOL] [KHUNG]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _dem_ghep as DG          # noqa: E402
import _ghep_he as GH           # noqa: E402
import chay_tester_kho as C     # noqa: E402

LAB = Path(__file__).resolve().parent
MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
KHUNG = sys.argv[2] if len(sys.argv) > 2 else "H1"
TEN_EA = "StopHaiDau"
VON = GH.VON
NAM = DG.NAM

EA = r"""//+------------------------------------------------------------------+
//| StopHaiDau - dat BuyStop va SellStop hai phia, cai nao khop thi
//| chay theo TP/SL. KHONG co tin hieu vao: he nay thang hay thua
//| hoan toan do QUAN LY LENH.
//+------------------------------------------------------------------+
#property copyright "The Brain"
#include <Trade\Trade.mqh>

#define KHUNG PERIOD_%(khung)s

input double InpKhoang    = 0.5;   // dat lenh cach gia bao nhieu ATR
input double InpTP        = 0.5;   // chot o bao nhieu ATR
input double InpSL        = 1.0;   // dung lo o bao nhieu ATR
input int    InpHan       = 3;     // lenh cho song bao nhieu nen
input int    InpHuyDauKia = 1;     // 1 = huy dau con lai khi mot dau khop
input double InpLot       = 0.10;
input long   InpMagic     = 26091400;

int      h_atr = INVALID_HANDLE;
CTrade   trade;
datetime g_nen = 0;
datetime g_dat = 0;                // luc dat cap lenh cho gan nhat

int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetTypeFillingBySymbol(_Symbol);
   h_atr = iATR(_Symbol, KHUNG, 14);
   return(INIT_SUCCEEDED);
  }

double Atr()
  {
   double b[];
   if(h_atr == INVALID_HANDLE) return(0.0);
   if(CopyBuffer(h_atr, 0, 1, 1, b) != 1) return(0.0);
   return(b[0]);
  }

int SoViThe()
  {
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic) n++;
     }
   return(n);
  }

int SoLenhCho()
  {
   int n = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tk = OrderGetTicket(i);
      if(tk == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol &&
         OrderGetInteger(ORDER_MAGIC) == InpMagic) n++;
     }
   return(n);
  }

void HuyHet()
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tk = OrderGetTicket(i);
      if(tk == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol &&
         OrderGetInteger(ORDER_MAGIC) == InpMagic) trade.OrderDelete(tk);
     }
  }

void OnTick()
  {
   // Mot dau da khop -> huy dau kia ngay (khong doi nen moi).
   if(InpHuyDauKia == 1 && SoViThe() > 0 && SoLenhCho() > 0) HuyHet();

   datetime t = (datetime)SeriesInfoInteger(_Symbol, KHUNG, SERIES_LASTBAR_DATE);
   if(t == g_nen) return;
   g_nen = t;

   // Het han lenh cho: huy de khong om mot cap lenh cua tuan truoc.
   if(SoLenhCho() > 0 && g_dat > 0 &&
      (t - g_dat) >= (datetime)(InpHan * PeriodSeconds(KHUNG)))
      HuyHet();

   if(SoViThe() > 0 || SoLenhCho() > 0) return;
   if((ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE)
      != SYMBOL_TRADE_MODE_FULL) return;

   double atr = Atr();
   if(atr <= 0.0) return;
   double diem = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   int    so   = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double dung = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * diem;
   double ask  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double k    = InpKhoang * atr;
   if(k < dung) k = dung;           // duoi stops level thi san TU CHOI lenh

   double gia_mua = NormalizeDouble(ask + k, so);
   double gia_ban = NormalizeDouble(bid - k, so);
   datetime han = t + (datetime)((InpHan + 1) * PeriodSeconds(KHUNG));

   trade.BuyStop(InpLot, gia_mua, _Symbol,
                 NormalizeDouble(gia_mua - InpSL * atr, so),
                 NormalizeDouble(gia_mua + InpTP * atr, so),
                 ORDER_TIME_SPECIFIED, han);
   trade.SellStop(InpLot, gia_ban, _Symbol,
                  NormalizeDouble(gia_ban + InpSL * atr, so),
                  NormalizeDouble(gia_ban - InpTP * atr, so),
                  ORDER_TIME_SPECIFIED, han);
   g_dat = t;
  }
//+------------------------------------------------------------------+
"""


def chay(model: int) -> list[dict]:
    src = C.XM_DATA / "MQL5" / "Experts" / (TEN_EA + ".mq5")
    src.write_text(EA % {"khung": KHUNG}, encoding="utf-8")
    loi = C.bien_dich(src)
    if loi:
        raise SystemExit("bien dich: " + loi)
    nc = "stop2_%s_%s_m%d" % (MA, KHUNG, model)
    (C.XM_DATA / (nc + ".ini")).write_text("""[Tester]
Expert=%s.ex5
Symbol=%s
Period=%s
Model=%d
ExecutionMode=0
Optimization=1
OptimizationCriterion=0
FromDate=%s
ToDate=%s
ForwardMode=0
Deposit=%d
Currency=USD
Leverage=1:500
ProfitInPips=0
Report=%s
ReplaceReport=1
ShutdownTerminal=1

[TesterInputs]
InpKhoang=0.25||0.25||0.25||1.5||Y
InpTP=0.25||0.25||0.25||1.5||Y
InpSL=0.5||0.5||0.5||2.0||Y
InpHan=1||1||1||4||Y
InpHuyDauKia=0||0||1||1||Y
InpLot=0.10||0.10||0||0||N
InpMagic=26091400||26091400||0||0||N
""" % (TEN_EA, MA, KHUNG, model, DG.DAU, DG.CUOI, VON, nc), encoding="utf-16")
    for h in (".xml", ".htm"):
        f = C.XM_DATA / (nc + h)
        if f.exists():
            f.unlink()
    giay = GH._chay_terminal(C.XM_DATA / (nc + ".ini"), tran=7200)
    f = C.XM_DATA / (nc + ".xml")
    if not f.exists():
        print("  Model=%d: khong ra bang (%ss)" % (model, giay), flush=True)
        return []
    ra = []
    for d in C.doc_xml(f):
        lai = C._so(d.get("Profit"))
        ra.append({"khoang": round(C._so(d.get("InpKhoang", 0)), 2),
                   "tp": round(C._so(d.get("InpTP", 0)), 2),
                   "sl": round(C._so(d.get("InpSL", 0)), 2),
                   "han": int(C._so(d.get("InpHan", 0))),
                   "huy": int(C._so(d.get("InpHuyDauKia", 0))),
                   "lenh": int(C._so(d.get("Trades"))), "lai": lai,
                   "pf": C._so(d.get("Profit Factor")),
                   "dd": C._so(d.get("Equity DD %")),
                   "sharpe": C._so(d.get("Sharpe Ratio"))})
    print("  Model=%d: %d pass, %ss" % (model, len(ra), giay), flush=True)
    return ra


def main() -> int:
    gop = {}
    # Model=4 (tick THAT) chi chay khi Model=0 co cau hinh DUONG: no dat gap
    # boi, va neu khong co gi duong o every-tick thi khong co gi de doi chieu.
    for model in (0, 4):
        if model == 4 and not [x for x in gop.get(0, []) if x["lai"] > 0]:
            print("
Model=0 khong co cau hinh duong -> bo qua Model=4",
                  flush=True)
            break
        print("\n### Model=%d (%s)"
              % (model, "every tick" if model == 0 else "tick THAT cua san"),
              flush=True)
        ds = chay(model)
        if not ds:
            continue
        ds.sort(key=lambda x: -x["lai"])
        gop[model] = ds[:20]
        print("%6s %5s %5s %4s %4s %7s %10s %6s %8s"
              % ("khoang", "tp", "sl", "han", "huy", "lenh", "lai", "PF", "DD%"))
        for x in ds[:10]:
            print("%6.2f %5.2f %5.2f %4d %4d %7d %10.2f %6.2f %7.2f%%"
                  % (x["khoang"], x["tp"], x["sl"], x["han"], x["huy"],
                     x["lenh"], x["lai"], x["pf"], x["dd"]))
        duong = [x for x in ds if x["lai"] > 0]
        print("  cau hinh DUONG: %d/%d" % (len(duong), len(ds)))

    # Doi chieu hai mo hinh tren CUNG cau hinh: neu lech thi con so la cua mo
    # hinh chu khong phai cua thi truong [[model1-che-ra-lai-gia]].
    if 0 in gop and 4 in gop:
        m4 = {(x["khoang"], x["tp"], x["sl"], x["han"], x["huy"]): x
              for x in gop[4]}
        print("\n--- doi chieu Model=0 vs Model=4 tren cung cau hinh ---")
        print("%6s %5s %5s %4s %4s %12s %12s"
              % ("khoang", "tp", "sl", "han", "huy", "lai M0", "lai M4"))
        for x in gop[0][:10]:
            k = (x["khoang"], x["tp"], x["sl"], x["han"], x["huy"])
            y = m4.get(k)
            print("%6.2f %5.2f %5.2f %4d %4d %12.2f %12s"
                  % (x["khoang"], x["tp"], x["sl"], x["han"], x["huy"],
                     x["lai"], ("%12.2f" % y["lai"]) if y else "khong co"))
    DG.ghi("STOP_HAI_DAU_%s_%s.json" % (MA, KHUNG),
           {"symbol": MA, "khung": KHUNG, "ket": gop})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
