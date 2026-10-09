# -*- coding: utf-8 -*-
"""MINI-BRAIN CANCUBO (09/10/2026) - dung lai CHUOI LENH cua bot "Can Cu Bu Sieng Nang" (CCBSN) tren vang tu deal tester THAT.

Phieu nay mo xe MOT con bot den cung (chu du an 09/10: "mo xe 1 vai con bot, thu ki tren gia lap va MT5, so sanh de tim quy luat backtest"):

  1. BOC CO CHE   `chuoi_tu_vi_the`: deal tester -> bang CHUOI (lenh dau, so lenh, lot, gia vao, ly do ra, gio ra...).
  2. DUNG LAI     `viet_ea` -> `ea_CanCuBoLai.mq5`: quan ly chuoi theo CO CHE DO DUOC (xem `CO_CHE` ben duoi). Cua vao = PHAT LAI gio mo chuoi
                  cua bot goc (mang `G_VAO`), vi tin hieu vao (InpIndiMode=8) chua biet - cach nay tach "dung lai quan ly lenh" khoi "tim tin hieu".
  3. KIEM         `duong_tu_chuoi` dung duong gia TOI THIEU suy tu chinh cac chuoi that (gia vao, gia DCA, dinh toi thieu, gia thoat) roi cho EA
                  chay tren san gia C++ `ea_gia_lap`: EA phai ra LAI dung tung chuoi (so lenh, lot, gia vao, ly do ra, gio ra, gia ra, lai).
                  Khong can gia M1 - Linux khong co gia. `so_chuoi` so hai bang chuoi (goc <-> dung lai) va liet ke lech.
  4. SO VOI MT5   (can gia M1 vang tu may nha) `tick_ohlc4` + EA tren san gia <-> EA tren tester MT5 (Model 1/0/4) <-> deal bot goc: phan ra sai so
                  thanh "dung lai sai" va "mo hinh backtest sai" (`nhan/so_ea_voi_tester.py`).

CO_CHE (do tu `reports/fixture/tester_cancubo_{kp,xn}_deals.csv.gz`, 1 pip = 0.1 USD, hop dong 100 oz, XM `GOLD.i#`):
  - Chi MUA. Chuoi mo luc giay :00 cua mot nen M1 (tin hieu: chua biet).
  - DCA: ask <= gia mo cua lenh MO SAU CUNG - 100 pip -> lenh moi; lot_n = round(0.01 * 1,05^(n-1), 2).
  - Moi lenh cua chuoi chung MOT TP = gia binh quan co trong so lot + (1 lenh ? 100 : 200) pip.
  - SL truot chung: khi (bid - gia tb) >= 30 pip, SL = gia tb + (15 + 2 * floor((loi_pip - 30) / 2)) pip (chi doi len); khop DUNG muc SL / TP.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from nhan import ea_gia_lap as G

GOC = Path(__file__).resolve().parent.parent
DEAL_KP = GOC / "reports" / "fixture" / "tester_cancubo_kp_deals.csv.gz"
DEAL_XN = GOC / "reports" / "fixture" / "tester_cancubo_xn_deals.csv.gz"
EA_DUONG = GOC / "ea_CanCuBoLai.mq5"

PIP = 0.1                  # gia cua 1 pip vang (10 point cua XM GOLD.i#, digits 2)
HOP_DONG = 100.0           # oz / lot
LOT_VANG = (0.01, 100.0, 0.01)
THAM_SO_GOC = dict(InpLot=0.01, InpLotMult=1.05, InpPipSize=PIP, InpStepPips=100.0, InpTpPips=100.0, InpTpDcaPips=200.0,
                   InpTrailStart=30.0, InpTrailStep=2.0, InpTrailInit=15.0)

# ==================================================================================================================== 1. BOC CHUOI
COT_CHUOI = ["id", "mo", "dong", "n", "lot", "gia_vao", "gia_tb", "gia_thap", "gia_ra", "ly_do", "loi", "lot_cac_lenh", "gia_cac_lenh", "gio_cac_lenh"]


def chuoi_tu_vi_the(v: pd.DataFrame) -> pd.DataFrame:
    """Bang vi the (`lenh_tester.vi_the_tu_tep`: moi dong mot lenh) -> bang CHUOI: mot chuoi = cac lenh chong len nhau; chuoi moi bat dau khi lenh
    dau tien mo SAU khi moi lenh cu da dong. Cot: id, mo (lenh dau), dong (lenh cuoi dong), n, lot (tong), gia_vao (lenh dau), gia_tb (binh quan
    lot), gia_thap (gia mo thap nhat), gia_ra (binh quan lot cua gia dong), ly_do (`ly_do_ra` cua lan dong cuoi: sl | tp | ea), loi (tien),
    lot_cac_lenh / gia_cac_lenh / gio_cac_lenh (list, theo thu tu mo). Lenh chua dong (het cua so) -> ly_do 'het_gio', dong NaT."""
    if v is None or len(v) == 0:
        return pd.DataFrame(columns=COT_CHUOI)
    v = v.sort_values(["mo", "deal_vao"] if "deal_vao" in v.columns else ["mo"], kind="stable").reset_index(drop=True)
    mo = pd.to_datetime(v["mo"]).to_numpy("datetime64[ns]")
    dong = pd.to_datetime(v["dong"]).to_numpy("datetime64[ns]")
    chuoi, cur, het = [], [], None
    for i in range(len(v)):
        if cur and not (het is not None and mo[i] > het):
            cur.append(i)
        else:
            if cur:
                chuoi.append(cur)
            cur = [i]
            het = None
        d = dong[i]
        if np.isnat(d):
            het = np.datetime64("9999-01-01", "ns")
        elif het is None or d > het:
            het = d
    if cur:
        chuoi.append(cur)
    hang = []
    for k, idx in enumerate(chuoi):
        s = v.iloc[idx]
        lot = s["lot"].to_numpy(float)
        gm = s["gia_mo"].to_numpy(float)
        con_mo = s["dong"].isna().any()
        gd = s["gia_dong"].to_numpy(float)
        ly = str(s["ly_do_ra"].iloc[-1]) if "ly_do_ra" in s.columns and not con_mo else "het_gio"
        hang.append(dict(
            id=k, mo=s["mo"].iloc[0], dong=pd.NaT if con_mo else s["dong"].max(), n=len(s), lot=float(lot.sum()), gia_vao=float(gm[0]),
            gia_tb=float((gm * lot).sum() / lot.sum()), gia_thap=float(gm.min()),
            gia_ra=float("nan") if con_mo else float((gd * lot).sum() / lot.sum()), ly_do=ly,
            loi=float(s["loi"].sum()) if "loi" in s.columns else float("nan"),
            lot_cac_lenh=[float(x) for x in lot], gia_cac_lenh=[float(x) for x in gm], gio_cac_lenh=list(pd.to_datetime(s["mo"]))))
    return pd.DataFrame(hang, columns=COT_CHUOI)


def doc_chuoi(duong) -> pd.DataFrame:
    """Tep deal tester (CSV/HTML) -> bang chuoi. Dung doc deal chinh thuc cua du an (`lenh_tester`)."""
    from nhan import lenh_tester as LT
    return chuoi_tu_vi_the(LT.vi_the_tu_tep(duong))


def thoi_diem_vao(ch: pd.DataFrame) -> list[int]:
    """Giay epoch (gio may chu coi nhu UTC) cua nen M1 mo moi chuoi = gio lenh dau cat xuong phut. Tang dan, khong trung."""
    t = pd.to_datetime(ch["mo"]).dt.floor("min")
    return sorted(set(int(x.value // 10 ** 9) for x in t))


# ==================================================================================================================== 2. EA
EA_MAU = r'''//+------------------------------------------------------------------+
//| ea_CanCuBoLai.mq5 - DUNG LAI co che quan ly CHUOI cua bot "Can Cu Bu Sieng Nang" (CCBSN) tren vang.                |
//| Do tu deal tester that (nhan/ea_cancubo_lai.py, 09/10/2026). KHONG chep ma bot goc; chi lam lai hanh vi do duoc:    |
//|   - Chi MUA, 1 chuoi tai mot luc. DCA khi ask <= gia mo cua lenh MO SAU CUNG - InpStepPips; lot_n = round(InpLot * InpLotMult^(n-1), 2). |
//|   - Moi lenh cua chuoi chung MOT TP = gia tb (co trong so lot) + (1 lenh ? InpTpPips : InpTpDcaPips) * pip.        |
//|   - SL truot chung: khi loi >= InpTrailStart pip, SL = tb + (InpTrailInit + InpTrailStep * floor((loi - Start) / Step)) pip, chi doi len. |
//|   - Cua vao InpEntryMode 0 = PHAT LAI gio mo nen M1 dau chuoi cua bot goc (mang G_VAO). Che do 1 (tin hieu) chua co.|
//| Moi phep tinh gia lam tren SO NGUYEN DIEM (point): hoa nua cent (vd. 1314,925 + 3,3) khop dung kieu lam tron 'nua len' cua bot goc |
//| tren 2244 chuoi (kieu so thuc 1314.925 + 3.3 = 1318.2249999 se lam tron xuong, lech 1 cent o 21 chuoi).             |
//+------------------------------------------------------------------+
#property version   "1.10"
#include <Trade/Trade.mqh>

input int    InpEntryMode    = 0;        // 0 = phat lai gio vao cua bot goc (G_VAO), 1 = tin hieu (chua co)
input double InpLot          = 0.01;
input double InpLotMult      = 1.05;
input double InpPipSize      = 0.1;      // gia cua 1 pip (vang XM GOLD.i#: 10 point)
input double InpStepPips     = 100.0;    // khoang DCA tinh tu lenh MO SAU CUNG
input double InpTpPips       = 100.0;    // TP chuoi 1 lenh
input double InpTpDcaPips    = 200.0;    // TP chuoi tu 2 lenh tro len
input double InpTrailStart   = 30.0;
input double InpTrailStep    = 2.0;
input double InpTrailInit    = 15.0;
input int    InpTrailRatchet = 1;        // 1 = SL chi doi len ; 0 = SL bam theo loi hien tai (ca xuong)
input int    InpMaxOrders    = 100;
input int    InpMagic        = 712;

// ---- gio mo nen M1 dau moi chuoi cua bot goc (giay epoch gio may chu, tang dan). Sinh boi nhan/ea_cancubo_lai.py - KHONG sua tay. ----
long     G_VAO[] =
  {
__VAO__
  };

CTrade   g_trade;
int      g_nvao = 0;                      // so gio vao trong mang
int      g_ivao = 0;                      // gio vao tiep theo chua xu ly
datetime g_nen = 0;                       // nen M1 dang xu ly
int      g_qua = 0;                       // so gio vao nam TRUOC cua so kiem (bo qua binh thuong)
int      g_bo_qua = 0;                    // so gio vao bi bo vi chuoi dang mo
int      g_n = 0;                         // so lenh cua chuoi
double   g_tb = 0.0;                      // gia tb co trong so lot, don vi DIEM (so thuc nhung tu / mau nguyen)
long     g_cuoi = 0;                      // gia mo lenh mo sau cung, don vi diem
double   g_sl = 0.0;                      // SL cao nhat dang dat tren cac lenh cua chuoi (gia), 0 = chua co
datetime g_cuoi_gio = 0;
ulong    g_cuoi_tk = 0;

long Pt(const double gia)                 // gia -> so nguyen diem
  {
   return (long)MathRound(gia / _Point);
  }

double Gia(const double diem)             // diem (nua cent tinh len) -> gia 
  {
   return NormalizeDouble(MathFloor(diem + 0.5) * _Point, _Digits);
  }

int OnInit()
  {
   if(InpEntryMode != 0)
     {
      PrintFormat("CCBL: che do vao %d chua co (chi 0 = phat lai gio vao)", InpEntryMode);
      return INIT_PARAMETERS_INCORRECT;
     }
   g_nvao = ArraySize(G_VAO);
   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(100);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   PrintFormat("CCBL: bo qua %d gio vao vi chuoi dang mo; %d gio vao nam truoc cua so", g_bo_qua, g_qua);
  }

// doc lai chuoi tu cac vi the dang mo (khong giu trang thai rieng -> khong lech voi san)
void DocChuoi()
  {
   g_n = 0;
   g_tb = 0.0;
   g_cuoi = 0;
   g_sl = 0.0;
   g_cuoi_gio = 0;
   g_cuoi_tk = 0;
   const double buoc = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double tong = 0.0, bac = 0.0;          // tong (so buoc lot * diem) va tong so buoc lot: SO NGUYEN -> thuong so tron dung
   for(int i = 0; i < PositionsTotal(); i++)
     {
      const ulong tk = PositionGetTicket(i);
      if(tk == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != InpMagic)
         continue;
      const double v = PositionGetDouble(POSITION_VOLUME);
      const long diem = Pt(PositionGetDouble(POSITION_PRICE_OPEN));
      const datetime gio = (datetime)PositionGetInteger(POSITION_TIME);
      const double so_buoc = MathRound(v / buoc);
      g_n++;
      tong += so_buoc * (double)diem;
      bac += so_buoc;
      g_sl = MathMax(g_sl, PositionGetDouble(POSITION_SL));
      if(gio > g_cuoi_gio || (gio == g_cuoi_gio && tk > g_cuoi_tk))
        {
         g_cuoi_gio = gio;
         g_cuoi_tk = tk;
         g_cuoi = diem;
        }
     }
   if(g_n > 0)
      g_tb = tong / bac;
  }

double ChuanLot(const double lot)
  {
   const double buoc = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   const double nho = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   const double lon = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double v = MathFloor(lot / buoc + 0.5) * buoc;
   v = MathMax(nho, MathMin(lon, v));
   return NormalizeDouble(v, 2);
  }

void MoLenh()
  {
   const int muc = g_n + 1;
   const double lot = ChuanLot(NormalizeDouble(InpLot * MathPow(InpLotMult, muc - 1), 2));
   if(!g_trade.Buy(lot, _Symbol, 0.0, 0.0, 0.0, "CCBL|" + IntegerToString(muc)))
      PrintFormat("CCBL: mo lenh %d loi %d %s", muc, (int)g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription());
  }

// dat cung SL / TP cho MOI lenh cua chuoi (chi goi khi co lenh lech)
void DongBo(const double sl, const double tp)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      const ulong tk = PositionGetTicket(i);
      if(tk == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != InpMagic)
         continue;
      if(MathAbs(PositionGetDouble(POSITION_SL) - sl) < _Point * 0.5 && MathAbs(PositionGetDouble(POSITION_TP) - tp) < _Point * 0.5)
         continue;
      if(!g_trade.PositionModify(tk, sl, tp))
         PrintFormat("CCBL: sua SL/TP loi %d %s", (int)g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription());
     }
  }

// nen M1 moi: xu ly cua vao (phat lai)
void XuLyVao(const datetime nen)
  {
   while(g_ivao < g_nvao && G_VAO[g_ivao] < (long)nen)
     {
      g_ivao++;
      g_qua++;
     }
   if(g_ivao < g_nvao && G_VAO[g_ivao] == (long)nen)
     {
      g_ivao++;
      if(g_n > 0)
        {
         g_bo_qua++;
         PrintFormat("CCBL: bo qua gio vao %d vi chuoi dang mo (%d lenh)", (int)nen, g_n);
         return;
        }
      MoLenh();
     }
  }

void OnTick()
  {
   DocChuoi();
   const datetime nen = iTime(_Symbol, PERIOD_M1, 0);
   if(nen != g_nen)
     {
      g_nen = nen;
      XuLyVao(nen);
      DocChuoi();
     }
   if(g_n == 0)
      return;
   const double dpp = MathRound(InpPipSize / _Point);       // diem / pip (vang: 10)
   const long bid = Pt(SymbolInfoDouble(_Symbol, SYMBOL_BID));
   const long ask = Pt(SymbolInfoDouble(_Symbol, SYMBOL_ASK));
   // 1. DCA: ask rot xuong khoang buoc ke tu lenh mo sau cung
   if(g_n < InpMaxOrders && (double)ask <= (double)g_cuoi - InpStepPips * dpp + 1e-9)
     {
      MoLenh();
      DocChuoi();
     }
   // 2. TP chung theo so lenh ; SL truot chung theo loi hien tai
   const double tp = Gia(g_tb + (g_n == 1 ? InpTpPips : InpTpDcaPips) * dpp);
   double sl = g_sl;
   const double loi = (double)bid - g_tb;                    // diem
   const double bd = InpTrailStart * dpp;
   if(loi + 1e-9 >= bd)
     {
      const double k = MathFloor((loi - bd) / (InpTrailStep * dpp) + 1e-9);
      const double s = Gia(g_tb + (InpTrailInit + InpTrailStep * k) * dpp);
      if(InpTrailRatchet == 0 || s > g_sl + _Point * 0.5)
         sl = s;
     }
   DongBo(sl, tp);
  }
'''


def viet_ea(vao: list[int], duong=EA_DUONG, mau: str | None = None) -> Path:
    """Sinh `ea_CanCuBoLai.mq5` voi mang G_VAO = `vao` (giay epoch, tang dan). `mau` thay mau EA (thu dot bien). Tra duong dan."""
    vao = [int(x) for x in vao]
    if any(b <= a for a, b in zip(vao, vao[1:])):
        raise ValueError("gio vao phai tang dan va khong trung")
    mau = EA_MAU if mau is None else mau
    if "__VAO__" not in mau:
        raise ValueError("mau EA thieu cho gan __VAO__")
    dong = []
    for i in range(0, len(vao), 8):
        dong.append("   " + ",".join(str(x) for x in vao[i:i + 8]) + ("," if i + 8 < len(vao) else ""))
    ma = mau.replace("__VAO__", "\n".join(dong) if dong else "   0")
    p = Path(duong)
    p.write_text(ma, encoding="utf-8")
    return p


# ==================================================================================================================== 3. KIEM CO CHE (chi bang deal)
def doc_hai_nguon() -> pd.DataFrame:
    """Chuoi cua ca hai lan chay tester that (kp 2018-2021, xn 2021-2024), them cot `nguon`, xep theo gio mo."""
    ra = []
    for ten, p in (("kp", DEAL_KP), ("xn", DEAL_XN)):
        c = doc_chuoi(p)
        c.insert(0, "nguon", ten)
        ra.append(c)
    ch = pd.concat(ra, ignore_index=True).sort_values("mo", kind="stable").reset_index(drop=True)
    ch["id"] = np.arange(len(ch))          # id DUY NHAT qua hai nguon (moi nguon dem tu 0)
    return ch


def _lot_du_kien(n: int, ts) -> list[float]:
    return [round(ts["InpLot"] * ts["InpLotMult"] ** i + 1e-12, 2) for i in range(n)]


def kiem_co_che(ch: pd.DataFrame, ts=THAM_SO_GOC) -> dict:
    """DUNG co che (CO_CHE) voi TUNG chuoi that: bang chung rang mo ta khop deal, khong can gia. Moi dong tra ve la mot DEM so chuoi vi pham
    (mong doi 0), kem so lieu mo ta. `sl_ngoai_luoi` = lan thoat SL khong nam tren bac thang InpTrailInit + k * InpTrailStep (sai lech > 0,06 pip =
    qua lam tron 0,005 USD); `dca_duoi_buoc` = lenh DCA mo gan hon InpStepPips so voi lenh truoc; `tp_lech` = TP khac gia tb + 100/200 pip;
    `sl_vuot_tp` = lan thoat SL o muc >= muc TP cua chuoi (se la mau thuan: TP phai chot truoc)."""
    pip = ts["InpPipSize"]
    ch = ch[ch["n"] > 0]
    lot_sai = sum(1 for lots in ch["lot_cac_lenh"] if any(abs(a - b) > 1e-9 for a, b in zip(lots, _lot_du_kien(len(lots), ts))))
    khoang = np.array([(g[i - 1] - g[i]) / pip for g in ch["gia_cac_lenh"] for i in range(1, len(g))], float)
    sl = ch[ch["ly_do"] == "sl"]
    tp = ch[ch["ly_do"] == "tp"]
    p_sl = ((sl["gia_ra"] - sl["gia_tb"]) / pip).to_numpy(float)
    k = np.round((p_sl - ts["InpTrailInit"]) / ts["InpTrailStep"])
    du = p_sl - (ts["InpTrailInit"] + ts["InpTrailStep"] * k)
    p_tp = ((tp["gia_ra"] - tp["gia_tb"]) / pip).to_numpy(float)
    muc_tp = np.where(tp["n"].to_numpy() == 1, ts["InpTpPips"], ts["InpTpDcaPips"])
    muc_tp_sl = np.where(sl["n"].to_numpy() == 1, ts["InpTpPips"], ts["InpTpDcaPips"])
    return dict(
        n_chuoi=int(len(ch)), n_lenh=int(ch["n"].sum()), ly_do=ch["ly_do"].value_counts().to_dict(),
        lot_sai=int(lot_sai),
        dca_n=int(len(khoang)), dca_duoi_buoc=int((khoang < ts["InpStepPips"] - 1e-6).sum()),
        dca_min_pip=float(khoang.min()) if len(khoang) else float("nan"),
        dca_trung_vi_pip=float(np.median(khoang)) if len(khoang) else float("nan"),
        dca_p95_pip=float(np.percentile(khoang, 95)) if len(khoang) else float("nan"),
        sl_n=int(len(sl)), sl_ngoai_luoi=int((np.abs(du) > 0.06).sum()), sl_duoi_khoi=int((k < 0).sum()),
        sl_du_max_pip=float(np.abs(du).max()) if len(du) else 0.0,
        sl_vuot_tp=int((p_sl >= muc_tp_sl - 1e-6).sum()),
        tp_n=int(len(tp)), tp_lech=int((np.abs(p_tp - muc_tp) > 0.06).sum()),
        tp_theo_do_sau={int(a): int(b) for a, b in tp["n"].value_counts().sort_index().items()},
        lo=int((ch["loi"] <= 0).sum()), loi_min=float(ch["loi"].min()), loi_tong=float(ch["loi"].sum()),
        do_sau_max=int(ch["n"].max()),
        giay_vao={int(a): int(b) for a, b in pd.Series([t.second for t in ch["mo"]]).value_counts().items()},
        giay_ra={int(a): int(b) for a, b in pd.Series([t.second for t in ch["dong"].dropna()]).value_counts().items()})


# ==================================================================================================================== 4. DUONG GIA TOI THIEU + CHAY EA + SO CHUOI
def _giay(ts) -> int:
    return int(pd.Timestamp(ts).value // 10 ** 9)


def duong_tu_chuoi(ch: pd.DataFrame, ts=THAM_SO_GOC, spread: float = 0.0, them_dinh_pip: float = 15.5, vuot_pip: float = 5.0):
    """Duong gia TOI THIEU suy tu chinh cac chuoi that, de EA dung lai chay duoc tren san gia ma khong can gia M1: moi chuoi = tick tai moi lenh
    (gio, gia mo that), roi - thoat SL: mot tick DINH (lai = bac thang + `them_dinh_pip`, nam giua [bac, bac+2) pip nen EA dat dung bac SL do)
    1 giay truoc gio thoat, roi tick cuoi o `vuot_pip` DUOI muc SL; thoat TP: mot tick cuoi `vuot_pip` TREN muc TP. Chuoi thoat khong phai SL/TP
    (het gio test, EA tu dong) khong dung lai duoc -> bo (tra ve danh sach id bo). `spread` = ask - bid (GIA); 0 = ask = bid.
    Tra (tk, bo): tk = dict cung dang `ea_gia_lap` (bid, spread, time, bar, bar_idx, chuoi_id, loai)."""
    pip = ts["InpPipSize"]
    if ch["id"].duplicated().any():
        raise ValueError("id chuoi phai duy nhat (gop nhieu nguon: danh so lai)")
    bid, tm, cid, loai, bo = [], [], [], [], []

    def them(t, gia_ask, i, kieu):
        bid.append(gia_ask - spread)
        tm.append(float(t))
        cid.append(i)
        loai.append(kieu)

    for r in ch.itertuples():
        if r.ly_do not in ("sl", "tp"):
            bo.append(int(r.id))
            continue
        for t, g in zip(r.gio_cac_lenh, r.gia_cac_lenh):
            them(_giay(t), g, r.id, "vao")
        t_ra = _giay(r.dong)
        t_cuoi = _giay(r.gio_cac_lenh[-1])
        if r.ly_do == "tp":
            them(t_ra, r.gia_ra + vuot_pip * pip, r.id, "tp")
        else:
            s = (r.gia_ra - r.gia_tb) / pip
            t_dinh = t_ra - 1 if t_ra - 1 > t_cuoi else (t_cuoi + t_ra) / 2.0
            them(t_dinh, r.gia_tb + (s + them_dinh_pip) * pip, r.id, "dinh")
            them(t_ra, r.gia_ra - vuot_pip * pip, r.id, "sl")
    tm = np.asarray(tm, float)
    if len(tm) > 1 and (np.diff(tm) < 0).any():
        raise ValueError("duong gia khong tang theo gio: chuoi chong len nhau? (lenh dau chuoi sau mo truoc khi chuoi truoc thoat)")
    return dict(bid=np.asarray(bid, float), spread=np.full(len(bid), float(spread)), time=tm, bar=np.floor(tm / 60.0) * 60.0,
                bar_idx=np.arange(len(bid), dtype=np.int64), chuoi_id=np.asarray(cid), loai=np.asarray(loai)), bo


def vi_the_tu_ket_qua(res: dict, tk: dict) -> pd.DataFrame:
    """Ket qua `ea_gia_lap.chay` -> bang vi the cung dang `lenh_tester.vi_the_tu_tep` (cot dung de gom chuoi): mo, dong (Timestamp tu gio tick),
    lot, gia_mo, gia_dong, loi (USD, hop dong 100), ly_do_ra, deal_vao (ticket)."""
    d = res["lenh"]
    if d is None or len(d) == 0:
        return pd.DataFrame(columns=["mo", "dong", "lot", "gia_mo", "gia_dong", "loi", "ly_do_ra", "deal_vao"])
    t = np.asarray(tk["time"], float)
    mo = pd.to_datetime(t[d["tick_mo"].astype(int).to_numpy()], unit="s")
    dg = d["tick_dong"].astype(float)
    dong = pd.to_datetime(np.where(np.isnan(dg), np.nan, t[np.nan_to_num(dg, nan=0).astype(int)]), unit="s")
    gd = d["close"].astype(float)
    loi = np.where(np.isnan(gd), np.nan, (gd - d["open"]) * d["vol"] * HOP_DONG)
    return pd.DataFrame(dict(mo=mo, dong=dong, lot=d["vol"].astype(float).to_numpy(), gia_mo=d["open"].astype(float).to_numpy(),
                             gia_dong=gd.to_numpy(), loi=loi, ly_do_ra=d["ly_do"].astype(str).to_numpy(),
                             deal_vao=d["ticket"].astype("int64").to_numpy()))


def chay_ea(tk: dict, vao: list[int], tham_so=None, von: float = 100000.0, thu_muc=None, mau: str | None = None, **kw) -> dict:
    """Viet EA voi mang gio vao `vao`, bien dich, chay tren duong gia `tk` voi hop dong vang (100 oz, lot 0,01 / 100 / 0,01, 2 chu so)."""
    with __import__("tempfile").TemporaryDirectory(prefix="ccbl_") as d:
        mq5 = viet_ea(vao, Path(d) / "ea_CanCuBoLai.mq5", mau=mau)
        exe = G.bien_dich(mq5, thu_muc=thu_muc)
        if exe is None:
            raise RuntimeError("khong co trinh bien dich C++ (c++ / g++ / clang++): khong chay duoc san gia")
        res = G.chay(exe, tk, von, tham_so=tham_so, digits=2, hop_dong=HOP_DONG, lot=LOT_VANG, **kw)
    return res


def so_chuoi(goc: pd.DataFrame, lai: pd.DataFrame, tol_gia: float = 0.0051, tol_loi: float = 0.02, tol_giay: float = 1.0, toi_da: int = 12) -> dict:
    """So hai bang chuoi (goc = bot goc tren tester, lai = EA dung lai) theo CUNG phut mo chuoi. Moi chuoi khop khi: cung so lenh, lot tung lenh,
    gia mo tung lenh (+-tol_gia), gio thoat (+-tol_giay), ly do thoat, gia thoat (+-tol_gia), loi (+-tol_loi). Tra dem tung loai lech + `chi_tiet`
    (toi da `toi_da` chuoi lech dau tien, kem cac truong lech)."""
    def khoa(c):
        return {_giay(pd.Timestamp(t).floor("min")): r for r, t in zip(c.itertuples(), c["mo"])}
    kg, kl = khoa(goc), khoa(lai)
    chung = sorted(set(kg) & set(kl))
    dem = dict(so_lenh=0, lot=0, gia_vao=0, gio_ra=0, ly_do=0, gia_ra=0, loi=0)
    chi_tiet, khop = [], 0
    for k in chung:
        a, b = kg[k], kl[k]
        lech = []
        if a.n != b.n:
            lech.append("so_lenh %d != %d" % (a.n, b.n))
            dem["so_lenh"] += 1
        else:
            if any(abs(x - y) > 1e-9 for x, y in zip(a.lot_cac_lenh, b.lot_cac_lenh)):
                lech.append("lot %s != %s" % (a.lot_cac_lenh, b.lot_cac_lenh))
                dem["lot"] += 1
            if any(abs(x - y) > tol_gia for x, y in zip(a.gia_cac_lenh, b.gia_cac_lenh)):
                lech.append("gia_vao %s != %s" % (a.gia_cac_lenh, b.gia_cac_lenh))
                dem["gia_vao"] += 1
        if pd.isna(a.dong) != pd.isna(b.dong) or (not pd.isna(a.dong) and abs((a.dong - b.dong).total_seconds()) > tol_giay):
            lech.append("gio_ra %s != %s" % (a.dong, b.dong))
            dem["gio_ra"] += 1
        if a.ly_do != b.ly_do:
            lech.append("ly_do %s != %s" % (a.ly_do, b.ly_do))
            dem["ly_do"] += 1
        if not (pd.isna(a.gia_ra) and pd.isna(b.gia_ra)) and (pd.isna(a.gia_ra) or pd.isna(b.gia_ra) or abs(a.gia_ra - b.gia_ra) > tol_gia):
            lech.append("gia_ra %.4f != %.4f" % (a.gia_ra, b.gia_ra))
            dem["gia_ra"] += 1
        if not (pd.isna(a.loi) and pd.isna(b.loi)) and (pd.isna(a.loi) or pd.isna(b.loi) or abs(a.loi - b.loi) > tol_loi):
            lech.append("loi %.2f != %.2f" % (a.loi, b.loi))
            dem["loi"] += 1
        if lech:
            if len(chi_tiet) < toi_da:
                chi_tiet.append(dict(gio_vao=str(pd.Timestamp(a.mo)), lech=lech))
        else:
            khop += 1
    return dict(n_goc=len(kg), n_lai=len(kl), chung=len(chung), khop=khop, chi_goc=sorted(set(kg) - set(kl))[:toi_da],
                chi_lai=sorted(set(kl) - set(kg))[:toi_da], dem_lech=dem, chi_tiet=chi_tiet)


def vong_kin(ch: pd.DataFrame, ts=THAM_SO_GOC, spread: float = 0.0, **kw) -> dict:
    """Vong kin tren duong gia TOI THIEU: duong gia suy tu chuoi that -> EA dung lai chay tren san gia -> gom chuoi -> so voi chuoi that.
    Khop het = EA tai tao DUNG co che do duoc (so lenh, lot, gia mo, TP, bac SL, gio / ly do thoat) tren moi chuoi dung lai duoc. KHONG chung minh
    EA ra dung tren gia that (duong gia nay chi co cac diem chuoi di qua) - viec do can gia M1 (xem `nhan/so_ea_voi_tester.py`)."""
    tk, bo = duong_tu_chuoi(ch, ts, spread=spread)
    vao = thoi_diem_vao(ch)
    res = chay_ea(tk, vao, tham_so=kw.pop("tham_so", None), **kw)
    if not res["ok"]:
        raise RuntimeError("EA khong chay duoc: ma thoat %s %s" % (res["ma_thoat"], res["loi"][-400:]))
    lai = chuoi_tu_vi_the(vi_the_tu_ket_qua(res, tk))
    giu = ch[~ch["id"].isin(bo)]
    kq = so_chuoi(giu, lai)
    kq.update(n_bo=len(bo), ea_n_mo=int(res["kq"]["n_mo"]), ea_n_sl=int(res["kq"]["n_sl"]), ea_n_tp=int(res["kq"]["n_tp"]),
              ea_bo_qua=sum(1 for d in res["log"] if "bo qua gio vao" in d), n_tick=int(len(tk["bid"])))
    return kq


# ==================================================================================================================== 5. DONG LENH
def _in_kiem(cc: dict) -> None:
    print("  %d chuoi / %d lenh ; thoat: %s ; sau nhat %d lenh" % (cc["n_chuoi"], cc["n_lenh"], cc["ly_do"], cc["do_sau_max"]))
    print("  lot sai cong thuc %d | DCA %d lan, nho nhat %.2f pip (duoi buoc: %d), trung vi %.1f, p95 %.1f"
          % (cc["lot_sai"], cc["dca_n"], cc["dca_min_pip"], cc["dca_duoi_buoc"], cc["dca_trung_vi_pip"], cc["dca_p95_pip"]))
    print("  SL %d lan: ngoai bac thang %d, duoi 15 pip %d, lech lon nhat %.3f pip, vuot TP %d | TP %d lan (theo do sau %s): lech %d"
          % (cc["sl_n"], cc["sl_ngoai_luoi"], cc["sl_duoi_khoi"], cc["sl_du_max_pip"], cc["sl_vuot_tp"], cc["tp_n"], cc["tp_theo_do_sau"], cc["tp_lech"]))
    print("  chuoi khong lai: %d (lo nhat %.2f USD), tong lai that %.1f USD ; giay vao %s ; giay ra %s"
          % (cc["lo"], cc["loi_min"], cc["loi_tong"], cc["giay_vao"], dict(sorted(cc["giay_ra"].items(), key=lambda x: -x[1])[:4])))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mini-Brain CanCuBo: kiem co che tren deal that, dung lai EA, vong kin tren san gia")
    ap.add_argument("lenh", choices=["kiem", "viet", "vong-kin"])
    a = ap.parse_args(argv)
    ch = doc_hai_nguon()
    if a.lenh == "viet":
        vao = thoi_diem_vao(ch)
        p = viet_ea(vao)
        print("da viet %s voi %d gio vao (%s -> %s)" % (p, len(vao), pd.to_datetime(vao[0], unit="s"), pd.to_datetime(vao[-1], unit="s")))
        return 0
    for ten, g in ch.groupby("nguon"):
        print("[%s]" % ten)
        _in_kiem(kiem_co_che(g))
    if a.lenh == "vong-kin":
        kq = vong_kin(ch)
        print("[vong kin tren duong gia toi thieu] %d tick ; goc %d chuoi, EA ra %d ; khop %d / %d chung ; bo %d chuoi khong dung lai duoc ; lech %s"
              % (kq["n_tick"], kq["n_goc"], kq["n_lai"], kq["khop"], kq["chung"], kq["n_bo"], kq["dem_lech"]))
        for c in kq["chi_tiet"]:
            print("   ", c)
        return 0 if kq["khop"] == kq["chung"] and kq["chung"] == kq["n_goc"] == kq["n_lai"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
