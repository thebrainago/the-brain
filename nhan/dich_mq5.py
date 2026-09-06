# -*- coding: utf-8 -*-
"""dich_mq5.py - DICH KHAI BAO DSL SANG MQL5 DE TESTER LAM TRONG TAI.

## VI SAO

Chu du an, 06/09/2026: *"Python test rat hay sai, nen no dung de test tho cho
nhanh thoi."* Va quy tac cu: **MT5 tester TRUOC, Python SAU**
[[mt5-tester-truoc-python-sau]]. Nhung tu truoc den nay moi co MOT co che duoc
dua ra tester, bang mot file `.mq5` viet tay. Voi 408 co che trong kho thi
duong do khong bao gio thanh cong.

File nay bien viec do thanh may moc: **mot khai bao DSL -> mot ham MQL5**, va ca
kho -> MOT file EA co `switch` theo ma co che. Chay OPTIMIZATION tren tham so ma
do thi **N co che ton bang mot lan khoi dong terminal** - do 06/09: mot luot
tester ton 138 giay, trong do bai test that chi 0,5 giay; phan con lai la boot
terminal. Nen gop N co che vao mot luot la khac biet giua "chay duoc 100 co che"
va "chay duoc 2".

## KHONG SINH MA TU LLM

Ma o day sinh tu CAY KHAI BAO bang luat co dinh, tat dinh, khong co `exec`,
khong co LLM - dung nguyen tac "kien thuc moi chi vao he qua ngu phap". Cai gi
ngu phap khong noi duoc thi bo dich TU CHOI, chu khong doan.

## HINH DANG MA SINH RA

Moi nut toan hang thanh MOT ham `double F<k>(int s)` - `s` la shift. Nut gop
(`tb`, `do_lech`, `zscore`, `phan_vi`, `cao_nhat`...) lap goi ham CON o
`s..s+n-1`. Cach nay dien duoc long bao nhieu tang cung duoc, va giu dung quy
uoc thoi gian: **khong ham nao doc shift am**.
"""
from __future__ import annotations

from typing import Any

#: Toan hang dich duoc. Cai gi ngoai day -> `KhongDichDuoc`.
CHI_BAO_DICH_DUOC = {
    "gia", "sma", "ema", "rsi", "atr", "tre", "tb", "do_lech", "phuong_sai",
    "zscore", "phan_vi", "cao_nhat", "thap_nhat", "doi", "doi_pct", "tuyet_doi",
    "tong", "bien_do", "than_nen", "ibs", "khoi_luong", "gio", "ngay_trong_tuan",
    "ngay_trong_thang", "thang",
}
PHEP_MQL = {"<": "<", "<=": "<=", ">": ">", ">=": ">=", "==": "==", "!=": "!="}

COT_HAM = {"open": "iOpen", "high": "iHigh", "low": "iLow", "close": "iClose"}
COT_TONG_HOP = {"hl2": ("high", "low"), "hlc3": ("high", "low", "close"),
                "ohlc4": ("open", "high", "low", "close")}


class KhongDichDuoc(Exception):
    """Ngu phap noi duoc nhung bo dich chua noi duoc. Doc ra la mot DANH SACH
    VIEC, khong phai mot loi cua co che."""


class BoDich:
    """Sinh cac ham `double F<k>(int s)` cho mot cay toan hang."""

    def __init__(self, tien_to: str = "F"):
        self.tien_to = tien_to
        self.ham: list[str] = []
        self._dem = 0

    def _moi(self) -> str:
        self._dem += 1
        return "%s%d" % (self.tien_to, self._dem)

    # ---------------------------------------------------------------- toan hang
    def toan_hang(self, t: Any) -> str:
        """Tra ve TEN HAM MQL5 tinh toan hang nay tai shift `s`."""
        if not isinstance(t, dict):
            raise KhongDichDuoc("toan hang khong phai dict: %r" % (t,))
        if "hang" in t:
            return self._hang(float(t["hang"]))
        if "toan_hang" in t:
            raise KhongDichDuoc("chua dich duoc nhom '%s'"
                                % t.get("chi_bao", "toan_hang"))
        cb = str(t.get("chi_bao", "")).lower()
        if cb not in CHI_BAO_DICH_DUOC:
            raise KhongDichDuoc("chua dich duoc chi bao '%s'" % cb)
        return getattr(self, "_cb_" + cb)(t)

    def _than(self, than: str) -> str:
        ten = self._moi()
        self.ham.append("double %s(int s)\n  {\n%s\n  }\n" % (ten, than))
        return ten

    def _hang(self, v: float) -> str:
        return self._than("   return(%.10g);" % v)

    # --- gia ---
    def _cb_gia(self, t: dict) -> str:
        cot = str(t.get("cot", "close")).lower()
        n = int(t.get("n", 0) or 0)          # `n` o nut gia = lui n bar
        if cot in COT_TONG_HOP:
            phan = COT_TONG_HOP[cot]
            bt = " + ".join("%s(_Symbol, KHUNG, s+%d)" % (COT_HAM[c], n)
                            for c in phan)
            return self._than("   return((%s) / %d.0);" % (bt, len(phan)))
        if cot not in COT_HAM:
            raise KhongDichDuoc("cot gia khong biet: '%s'" % cot)
        return self._than("   return(%s(_Symbol, KHUNG, s+%d));"
                          % (COT_HAM[cot], n))

    def _nguon(self, t: dict) -> str:
        """Chuoi nguon cua mot chi bao: `cua` neu co, khong thi close."""
        return self.toan_hang(t.get("cua") or {"chi_bao": "gia", "cot": "close"})

    # --- chi bao co san cua MT5 ---
    def _cb_sma(self, t: dict) -> str:
        return self._ma(t, "MODE_SMA")

    def _cb_ema(self, t: dict) -> str:
        return self._ma(t, "MODE_EMA")

    def _ma(self, t: dict, che_do: str) -> str:
        n = int(t.get("n", 20) or 20)
        if t.get("cua"):
            # MA cua mot bieu thuc BAT KY -> tu tinh, khong dung iMA.
            f = self.toan_hang(t["cua"])
            if che_do == "MODE_SMA":
                return self._gop_tb(f, n)
            raise KhongDichDuoc("ema cua bieu thuc long chua dich duoc")
        return self._than(
            "   return(Chi(h_ma%d, s));" % self._dang_ky_ma(n, che_do))

    def _cb_rsi(self, t: dict) -> str:
        if t.get("cua"):
            raise KhongDichDuoc("rsi cua bieu thuc long chua dich duoc")
        n = int(t.get("n", 14) or 14)
        return self._than("   return(Chi(h_rsi%d, s));" % self._dang_ky_rsi(n))

    def _cb_atr(self, t: dict) -> str:
        n = int(t.get("n", 14) or 14)
        return self._than("   return(Chi(h_atr%d, s));" % self._dang_ky_atr(n))

    # --- bien doi ---
    def _cb_tre(self, t: dict) -> str:
        f = self._nguon(t)
        n = int(t.get("n", 1) or 1)
        return self._than("   return(%s(s+%d));" % (f, n))

    def _cb_tuyet_doi(self, t: dict) -> str:
        f = self._nguon(t)
        return self._than("   return(MathAbs(%s(s)));" % f)

    def _cb_doi(self, t: dict) -> str:
        f = self._nguon(t)
        n = int(t.get("n", 1) or 1)
        return self._than("   return(%s(s) - %s(s+%d));" % (f, f, n))

    def _cb_doi_pct(self, t: dict) -> str:
        f = self._nguon(t)
        n = int(t.get("n", 1) or 1)
        return self._than(
            "   double a = %s(s+%d);\n"
            "   if(a == 0.0) return(0.0);\n"
            "   return((%s(s) - a) / a);" % (f, n, f))

    # --- gop tren cua so ---
    def _gop(self, f: str, n: int, than: str) -> str:
        return self._than(
            "   double v[]; ArrayResize(v, %d);\n"
            "   for(int i = 0; i < %d; i++) v[i] = %s(s+i);\n%s" % (n, n, f, than))

    def _gop_tb(self, f: str, n: int) -> str:
        return self._gop(f, n, "   double t = 0; for(int i=0;i<%d;i++) t += v[i];\n"
                               "   return(t / %d.0);" % (n, n))

    def _cb_tb(self, t: dict) -> str:
        return self._gop_tb(self._nguon(t), int(t.get("n", 20) or 20))

    def _cb_tong(self, t: dict) -> str:
        n = int(t.get("n", 20) or 20)
        return self._gop(self._nguon(t), n,
                         "   double t = 0; for(int i=0;i<%d;i++) t += v[i];\n"
                         "   return(t);" % n)

    def _cb_cao_nhat(self, t: dict) -> str:
        n = int(t.get("n", 20) or 20)
        return self._gop(self._nguon(t), n,
                         "   double m = v[0]; for(int i=1;i<%d;i++) if(v[i]>m) m=v[i];\n"
                         "   return(m);" % n)

    def _cb_thap_nhat(self, t: dict) -> str:
        n = int(t.get("n", 20) or 20)
        return self._gop(self._nguon(t), n,
                         "   double m = v[0]; for(int i=1;i<%d;i++) if(v[i]<m) m=v[i];\n"
                         "   return(m);" % n)

    #: `ddof = 0` - chia n, khop `pandas.std(ddof=0)` ma `ngu_phap.toan_hang`
    #: goi. Lech ddof la lech nguong, va nguong thuong nam dung o ranh.
    _SD = ("   double t=0; for(int i=0;i<%d;i++) t+=v[i]; double m=t/%d.0;\n"
           "   double q=0; for(int i=0;i<%d;i++) q+=(v[i]-m)*(v[i]-m);\n"
           "   double sd = MathSqrt(q/%d.0);\n")

    def _cb_do_lech(self, t: dict) -> str:
        n = int(t.get("n", 20) or 20)
        return self._gop(self._nguon(t), n,
                         (self._SD % (n, n, n, n)) + "   return(sd);")

    def _cb_phuong_sai(self, t: dict) -> str:
        n = int(t.get("n", 20) or 20)
        return self._gop(self._nguon(t), n,
                         (self._SD % (n, n, n, n)) + "   return(sd*sd);")

    def _cb_zscore(self, t: dict) -> str:
        n = int(t.get("n", 20) or 20)
        return self._gop(self._nguon(t), n,
                         (self._SD % (n, n, n, n)) +
                         "   if(sd <= 0.0) return(0.0);\n"
                         "   return((v[0]-m)/sd);")

    def _cb_phan_vi(self, t: dict) -> str:
        """Thu hang cua gia tri hien tai trong N bar gan nhat, 0..1."""
        n = int(t.get("n", 100) or 100)
        return self._gop(self._nguon(t), n,
                         "   int d = 0; for(int i=1;i<%d;i++) if(v[i] <= v[0]) d++;\n"
                         "   return((double)d / %d.0);" % (n, n - 1))

    # --- dac trung nen ---
    def _cb_bien_do(self, t: dict) -> str:
        return self._than("   return(iHigh(_Symbol,KHUNG,s) - iLow(_Symbol,KHUNG,s));")

    def _cb_than_nen(self, t: dict) -> str:
        return self._than("   return(MathAbs(iClose(_Symbol,KHUNG,s) "
                          "- iOpen(_Symbol,KHUNG,s)));")

    def _cb_ibs(self, t: dict) -> str:
        return self._than(
            "   double h=iHigh(_Symbol,KHUNG,s), l=iLow(_Symbol,KHUNG,s);\n"
            "   if(h - l <= 0.0) return(0.5);\n"
            "   return((iClose(_Symbol,KHUNG,s) - l) / (h - l));")

    def _cb_khoi_luong(self, t: dict) -> str:
        return self._than("   return((double)iTickVolume(_Symbol,KHUNG,s));")

    # --- lich ---
    def _lich(self, truong: str) -> str:
        return self._than(
            "   MqlDateTime d; TimeToStruct(iTime(_Symbol,KHUNG,s), d);\n"
            "   return((double)d.%s);" % truong)

    def _cb_gio(self, t: dict) -> str:
        return self._lich("hour")

    def _cb_ngay_trong_tuan(self, t: dict) -> str:
        return self._lich("day_of_week")

    def _cb_ngay_trong_thang(self, t: dict) -> str:
        return self._lich("day")

    def _cb_thang(self, t: dict) -> str:
        return self._lich("mon")

    # ------------------------------------------------------------ chi bao MT5
    def __post(self):
        pass

    _ma_da_co: dict
    _rsi_da_co: dict
    _atr_da_co: dict

    def _dang_ky_ma(self, n: int, che_do: str) -> int:
        d = getattr(self, "_ma_da_co", None)
        if d is None:
            d = self._ma_da_co = {}
        k = (n, che_do)
        if k not in d:
            d[k] = len(d)
        return d[k]

    def _dang_ky_rsi(self, n: int) -> int:
        d = getattr(self, "_rsi_da_co", None)
        if d is None:
            d = self._rsi_da_co = {}
        if n not in d:
            d[n] = len(d)
        return d[n]

    def _dang_ky_atr(self, n: int) -> int:
        d = getattr(self, "_atr_da_co", None)
        if d is None:
            d = self._atr_da_co = {}
        if n not in d:
            d[n] = len(d)
        return d[n]

    def khai_bao_chi_bao(self) -> tuple[str, str]:
        """(khai bao handle, ma khoi tao). Rong neu khong dung chi bao MT5 nao."""
        kb, kt = [], []
        for (n, che_do), i in sorted(getattr(self, "_ma_da_co", {}).items(),
                                     key=lambda x: x[1]):
            kb.append("int h_ma%d = INVALID_HANDLE;" % i)
            kt.append('   h_ma%d = iMA(_Symbol, KHUNG, %d, 0, %s, PRICE_CLOSE);'
                      % (i, n, che_do))
        for n, i in sorted(getattr(self, "_rsi_da_co", {}).items(),
                           key=lambda x: x[1]):
            kb.append("int h_rsi%d = INVALID_HANDLE;" % i)
            kt.append('   h_rsi%d = iRSI(_Symbol, KHUNG, %d, PRICE_CLOSE);' % (i, n))
        for n, i in sorted(getattr(self, "_atr_da_co", {}).items(),
                           key=lambda x: x[1]):
            kb.append("int h_atr%d = INVALID_HANDLE;" % i)
            kt.append('   h_atr%d = iATR(_Symbol, KHUNG, %d);' % (i, n))
        return "\n".join(kb), "\n".join(kt)

    # -------------------------------------------------------------------- VUNG
    #: Tran so vung song cung luc. Cung y nghia `ngu_phap.TRAN_VUNG_SONG`: chan
    #: an toan cho truong hop `tao` suy bien thanh luon dung.
    TRAN_VUNG = 64

    #: Quan he -> bieu thuc, voi `a` = bien duoi, `b` = bien tren, `dg` = dong
    #: cua nen dang xet, `dgt` = dong cua nen truoc.
    QH_BT = {
        "cham": "true",
        "trong": "(dg >= a && dg <= b)",
        "bat_len": "(dg > b)",
        "bat_xuong": "(dg < a)",
        "xuyen_len": "(dg > b && dgt <= b)",
        "xuyen_xuong": "(dg < a && dgt >= a)",
    }

    def vung(self, d: dict) -> str:
        """Mot ve `vung` -> ten ham `bool V<k>(int s)`.

        Dich NGUYEN VAN ngu nghia cua `ngu_phap._vung`, ke ca chi tiet quan
        trong nhat: **vung song tu nen SAU nen sinh**. Bo qua chi tiet do thi
        voi hinh hoc FVG nen sinh luon tu cham chinh no, moi vung song dung mot
        nen, va `song` lan `huy` thanh nut chet - dung cai loi da phai sua trong
        ban Python [[doi-tham-so-ma-khong-doi-ket-qua]].

        Khac ban Python o MOT diem, va la khac biet BAT BUOC: Python duyet ca
        chuoi mot lan va mang trang thai theo; MQL5 duoc hoi tai MOT shift. Nen
        ham nay DUNG LAI cac vung bang cach lui ve qua khu toi da `song` nen roi
        kiem tung cai. Cung ket qua, chi ton hon.
        """
        kb = d.get("vung") or {}
        qh = str(d.get("quan_he", "cham"))
        if qh not in self.QH_BT:
            raise KhongDichDuoc("quan he vung '%s' chua dich duoc" % qh)
        song = int(kb.get("song", 20) or 20)
        huy = str(kb.get("huy", "cham"))
        if huy not in ("cham", "dong_ngoai", "het_han"):
            raise KhongDichDuoc("cach huy vung '%s' chua dich duoc" % huy)

        tao = self._theo_i(self.dieu_kien(kb.get("tao") or []))
        tren = self.toan_hang(kb["tren"])
        duoi = self.toan_hang(kb["duoi"])

        # `huy=cham`: vung chet o LAN CHAM DAU, nen no chi con hieu luc tai `s`
        # neu khong nen nao GIUA nen sinh va `s` da cham no.
        if huy == "cham":
            chan = ("      bool da = false;\n"
                    "      for(int j = i - 1; j > s && !da; j--)\n"
                    "         if(iLow(_Symbol,KHUNG,j) <= b && "
                    "iHigh(_Symbol,KHUNG,j) >= a) da = true;\n"
                    "      if(da) continue;\n")
        elif huy == "dong_ngoai":
            chan = ("      bool da = false;\n"
                    "      for(int j = i - 1; j > s && !da; j--)\n"
                    "        {\n"
                    "         double c = iClose(_Symbol,KHUNG,j);\n"
                    "         if(c > b || c < a) da = true;\n"
                    "        }\n"
                    "      if(da) continue;\n")
        else:
            chan = ""

        self._dem += 1
        ten = "V%d" % self._dem
        than = [
            "bool %s(int s)" % ten,
            "  {",
            "   double dg  = iClose(_Symbol,KHUNG,s);",
            "   double dgt = iClose(_Symbol,KHUNG,s+1);",
            "   int dem = 0;",
            "   for(int i = s + 1; i <= s + %d; i++)" % song,
            "     {",
            "      if(!(%s)) continue;" % tao,
            "      if(++dem > %d) break;" % self.TRAN_VUNG,
            "      double x = %s(i), y = %s(i);" % (tren, duoi),
            "      double a = MathMin(x, y), b = MathMax(x, y);",
            "      if(!MathIsValidNumber(a) || !MathIsValidNumber(b)) continue;",
            "      if(!(iLow(_Symbol,KHUNG,s) <= b && "
            "iHigh(_Symbol,KHUNG,s) >= a)) continue;",
            chan.rstrip("\n"),
            "      if(%s) return(true);" % self.QH_BT[qh],
            "     }",
            "   return(false);",
            "  }",
            "",
        ]
        self.ham.append("\n".join(x for x in than if x != ""))
        return ten

    @staticmethod
    def _theo_i(bt: str) -> str:
        """`dieu_kien` sinh bieu thuc theo shift `s`; `tao` can no theo `i`."""
        return bt.replace("(s+1)", "(i+1)").replace("(s)", "(i)")

    # ---------------------------------------------------------------- dieu kien
    def dieu_kien(self, ds: list) -> str:
        """Danh sach dieu kien (VA voi nhau) -> bieu thuc bool tai shift `s`."""
        if not ds:
            return "false"
        ve = []
        for d in ds:
            if isinstance(d, dict) and "vung" in d:
                ve.append("%s(s)" % self.vung(d))
                continue
            if not isinstance(d, dict):
                raise KhongDichDuoc("ve khong phai dict")
            a = self.toan_hang(d["trai"])
            b = self.toan_hang(d["phai"])
            p = d.get("phep", ">")
            if p in PHEP_MQL:
                ve.append("(%s(s) %s %s(s))" % (a, PHEP_MQL[p], b))
            elif p == "cheo_len":
                ve.append("(%s(s) > %s(s) && %s(s+1) <= %s(s+1))" % (a, b, a, b))
            elif p == "cheo_xuong":
                ve.append("(%s(s) < %s(s) && %s(s+1) >= %s(s+1))" % (a, b, a, b))
            else:
                raise KhongDichDuoc("phep '%s' chua dich duoc" % p)
        return " && ".join(ve)


# ============================================================== SINH CA MOT EA
MAU_EA = r"""//+------------------------------------------------------------------+
//| %(ten)s - SINH TU DONG boi nhan/dich_mq5.py. KHONG SUA TAY.
//| %(so)d co che tu config/co_che_dsl.json, chon bang InpMaCoChe.
//|
//| Gop nhieu co che vao MOT EA co chu dich: mot luot tester ton ~138 giay
//| ma bai test that chi 0,5 giay - phan con lai la boot terminal. Chay
//| OPTIMIZATION tren InpMaCoChe thi N co che ton bang MOT lan boot.
//+------------------------------------------------------------------+
#property copyright "The Brain"
#include <Trade\Trade.mqh>

input int    InpMaCoChe = 0;      // ma co che (0..%(max)d)
input double InpLot     = 0.10;
input long   InpMagic   = 26090601;

#define KHUNG PERIOD_%(khung)s

%(khai_bao)s

CTrade   trade;
datetime g_nen_cuoi = 0;
int      g_bar_vao  = 0;
int      g_y_dinh   = 0;          // 0 khong, 1 mo, -1 dong

double Chi(int h, int s)
  {
   if(h == INVALID_HANDLE) return(0.0);
   double b[];
   if(CopyBuffer(h, 0, s, 1, b) != 1) return(0.0);
   return(b[0]);
  }

%(ham)s

//--- vao/ra cua tung co che
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
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetTypeFillingBySymbol(_Symbol);
%(khoi_tao)s
   return(INIT_SUCCEEDED);
  }

bool DangMo()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic) return(true);
     }
   return(false);
  }

void DongHet()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic) trade.PositionClose(tk);
     }
  }

//--- Khop y dinh o nen dau tien CO THE giao dich.
//--- Nen cua khung tin hieu doi luc 00:00, ma 00:00 nam NGOAI phien cua CFD chi
//--- so -> hanh dong ngay tai do thi moi lenh tra "Market closed" va bao cao ghi
//--- 0 lenh, doc y het mot he khong bao gio vao lenh.
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
   bool ok = (Chieu(InpMaCoChe) > 0) ? trade.Buy(InpLot, _Symbol)
                                     : trade.Sell(InpLot, _Symbol);
   if(ok) { g_bar_vao = 0; g_y_dinh = 0; }
  }

void OnTick()
  {
   KhopYDinh();

   datetime t = (datetime)SeriesInfoInteger(_Symbol, KHUNG, SERIES_LASTBAR_DATE);
   if(t == g_nen_cuoi) return;
   g_nen_cuoi = t;

   int k = InpMaCoChe;
   if(DangMo())
     {
      g_bar_vao++;
      bool ra = CoDieuKienRa(k) ? CoRa(k, 1) : (g_bar_vao >= Giu(k));
      g_y_dinh = (ra || g_bar_vao >= 500) ? -1 : 0;
     }
   else
      g_y_dinh = CoVao(k, 1) ? 1 : 0;
  }
//+------------------------------------------------------------------+
"""


#: Co che MUA-GIU, chen vao chinh EA sinh ra.
#:
#: VI SAO PHAI NAM TRONG CUNG MOT EA chu khong tinh rieng: moc so sanh chi co
#: nghia neu no di qua **dung mot bo thuc thi** - cung spread, cung phi qua dem,
#: cung gio khop, cung lot, cung lich phien. Mot con so mua-giu lay tu chuoi gia
#: (hoac tu Python) la mot moc KHAC [[v6-doi-chieu-dung-cach]].
#:
#: `vao` luon dung (`high >= low`), khong co `ra`, `giu` = 500 -> vao mot lan roi
#: nam im. Ve nay CO Y hien nhien; no khong di qua `kiem_khai_bao` va khong bao
#: gio duoc ghi vao kho.
SPEC_MUA_GIU = {
    "ten": "__mua_giu__", "ho": "moc", "chieu": 1, "giu": 500,
    "co_che": "MOC SO SANH - khong phai co che.",
    "vao": [{"trai": {"chi_bao": "gia", "cot": "high"}, "phep": ">=",
             "phai": {"chi_bao": "gia", "cot": "low"}}],
}


def sinh_ea(cac_spec: list[dict], ten: str = "KhoCoChe", khung: str = "D1",
            them_mua_giu: bool = True) -> tuple[str, list[dict]]:
    """Sinh MOT EA cho nhieu co che. Tra (ma nguon, danh sach da dich duoc).

    Co che nao khong dich duoc thi BI BO KHOI EA va duoc ghi ly do - do la mot
    danh sach viec cho bo dich, khong phai mot phan quyet ve co che.
    """
    bd = BoDich()
    dat, dk_ma, sw_vao, sw_ra, sw_chieu, sw_giu, sw_cora = [], [], [], [], [], [], []
    if them_mua_giu:
        cac_spec = [dict(SPEC_MUA_GIU)] + list(cac_spec)
    for c in cac_spec:
        try:
            bt_vao = bd.dieu_kien(c.get("vao") or [])
            co_ra = bool(c.get("ra"))
            bt_ra = bd.dieu_kien(c["ra"]) if co_ra else "false"
        except KhongDichDuoc as e:
            c["_khong_dich"] = str(e)
            continue
        k = len(dat)
        # `_dich`: danh gia dieu kien tai bar s+K thay vi s.
        #
        # Day la PLACEBO dung cach cho duong tester. Giu NGUYEN chuoi tin hieu -
        # cung ty le kich hoat, cung do dai cum, cung tu tuong quan - chi pha
        # cai duy nhat dang tra loi: su khop thoi diem voi loi suat phia sau.
        # Hoan vi lai/lo thi giu nguyen phan phoi va luon ra ~50%, do la loi da
        # mac 29/07 [[v6-doi-chieu-dung-cach]]; con dich chuoi tin hieu thi
        # khong dung vao phan phoi loi suat mot ly nao.
        kk = int(c.get("_dich", 0) or 0)
        d_s = "s+%d" % kk if kk else "s"
        dk_ma.append("bool VAO%d(int s) { return(%s); }"
                     % (k, bt_vao.replace("(s)", "(%s)" % d_s)
                        .replace("(s+1)", "(%s+1)" % d_s) if kk else bt_vao))
        dk_ma.append("bool RA%d(int s)  { return(%s); }"
                     % (k, bt_ra.replace("(s)", "(%s)" % d_s)
                        .replace("(s+1)", "(%s+1)" % d_s) if kk else bt_ra))
        sw_vao.append("      case %d: return(VAO%d(s));" % (k, k))
        sw_ra.append("      case %d: return(RA%d(s));" % (k, k))
        sw_chieu.append("case %d: return(%d);"
                        % (k, int(c.get("chieu", 1) or 1)))
        sw_giu.append("case %d: return(%d);" % (k, int(c.get("giu", 1) or 1)))
        sw_cora.append("case %d: return(%s);" % (k, "true" if co_ra else "false"))
        dat.append(c)

    if not dat:
        raise KhongDichDuoc("khong co che nao dich duoc")
    kb, kt = bd.khai_bao_chi_bao()
    ma = MAU_EA % {
        "ten": ten, "so": len(dat), "max": len(dat) - 1, "khung": khung,
        "khai_bao": kb, "khoi_tao": kt,
        "ham": "\n".join(bd.ham), "dieu_kien": "\n".join(dk_ma),
        "sw_vao": "\n".join(sw_vao), "sw_ra": "\n".join(sw_ra),
        "sw_chieu": " ".join(sw_chieu), "sw_giu": " ".join(sw_giu),
        "sw_cora": " ".join(sw_cora),
    }
    return ma, dat
