# -*- coding: utf-8 -*-
"""chi_phi.py - MO HINH CHI PHI DO DUOC, khong phai go tay.

Vi sao co file nay (bao cao 15/08): `lab/quant/metrics.py` go tay
`swap_pip_per_day=0.5` -> 0,30 %/nam, trong khi du an DA DO THAT 6,0 %/nam
o muc index 7.100 (CLAUDE.md muc 13). Thap hon 20 lan. Moi chien luoc giu dai
duoc tang khong ~4-5 %/nam alpha gia.

Nguyen tac:
  1. SPREAD lay tu cot `spread` THAT trong bar MT5 (don vi POINT), theo GIO
     trong ngay. Khong dung mot so vo huong cho ca lich su (CLAUDE.md muc 7).
     Bo bar spread=0 (bar hong) va bar cuoi tuan (bi thoi 2-6 lan - memory
     `bay-do-luong-mt5-xm`).
  2. PHI QUA DEM mo hinh theo CO CHE: lai_suat_thuc(t) + markup.
     TUYET DOI KHONG `swap_tuyet_doi * 365 / gia` (CLAUDE.md muc 14 - chinh
     chu du an da mac lai bay nay ngay 28/07).
     markup = swap_quan_sat_hom_nay - lai_suat_hom_nay, gia dinh markup on dinh.
  3. Luu VECTOR DO NHAY theo TUNG thanh phan (THIET_KE_DAY_CHUYEN muc 7), de
     doi tham so chi phi thi chi tai kiem cai lung lay, khong quet lai tat ca.
  4. Moi mo hinh mang theo `do_tin`: DO (do tu du lieu) / SAN (doc tu MT5) /
     KHAI (khai bao tay). KHAI khong bao gio duoc PASS - chi EXPLORATORY.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
CAU_HINH = LAB / "config" / "chi_phi_do.json"

# THE HE MO HINH CHI PHI. Tang len khi doi CAU TRUC (khong phai doi tham so).
# THIET_KE muc 7: doi tham so -> dung do nhay, chi tai kiem cai lung lay;
#                 doi CAU TRUC -> gradient vo hieu, BAT BUOC quet lai toan bo.
# Ket qua cua the he cu khong so sanh duoc voi the he moi, va chuoi FDR phai
# tach ra - neu khong thi chuoi quyet dinh tron hai thuoc do khac nhau.
#   1 (15/08 sang): spread do tu bar; phi qua dem KHAI BAO theo lop tai san.
#   2 (15/08 toi) : phi qua dem DO tu MT5 tung san, quy doi theo dung swap_mode,
#                   tra cuu theo phoi nhiem chuan hoa + san uu tien (khong lay demo).
#   3 (16/08 toi) : can thoi gian phi giu theo interval open[i] -> open[i+1].
#                   Ban cu gan diff vao bar i+1, lam thieu phi cuoi tuan/interval
#                   moi khi vi the dong o bar ke tiep.
THE_HE = 3

# Kich thuoc point theo dang tai san. FX 5 so: 1e-5; cap JPY: 1e-3.
POINT_MAC_DINH = {"fx5": 1e-5, "fx3": 1e-3, "chi_so": 0.01, "vang": 0.01}

# Gio (UTC theo bar MT5) bi loai khi do spread: quanh roll-over 23:00-01:00
# spread gian ra hang chuc lan, khong dai dien cho gio giao dich.
GIO_LOAI = {23, 0}

# Muc phi giu quan sat duoc cua du an, dung lam moc doi chieu va lam du phong.
# Nguon: CLAUDE.md muc 13 + memory ban-do-chi-phi-lien-san / xm-chi-phi-that-theo-lop.
PHI_QUAN_SAT = {
    "chi_so_my": {"phi_nam_mua": 0.055, "phi_nam_ban": -0.005, "nguon": "XM US500Cash 2026"},
    "vang":      {"phi_nam_mua": 0.075, "phi_nam_ban": -0.020, "nguon": "XAUUSD XM 2026"},
    "fx":        {"phi_nam_mua": 0.015, "phi_nam_ban": 0.015,  "nguon": "uoc tu chenh lai suat"},
    # Hang hoa: chua DO tren san nao. So nay la uoc THAN TRONG tu contango dien
    # hinh cua dau + phi giu vi the CFD, va no chi duoc dung o che do nghien cuu
    # (do_tin = KHAI thi khong bao gio PASS). KHONG duoc chuyen thanh so quyet
    # dinh truoc khi do that bang `do_moi_san`.
    "hang_hoa":  {"phi_nam_mua": 0.090, "phi_nam_ban": 0.010,
                  "nguon": "UOC - chua do tren san nao"},
}


# ------------------------------------------------------- BO NHO DEM HINH HOC BAR
# Do 16/08: mot luot `MP.chay` mat 89 ms, trong do 85 ms nam trong `phi_giu_mang`
# vi no tinh LAI `np.diff(index)` tren DatetimeIndex moi lan goi (numpy.diff 21 ms
# + astype 10 ms + pandas datetime __iter__ 605.560 luot). Trong mot lan placebo
# (995 luot chay tren CUNG mot index) thi 99,9% cong do la lam lai viec cu.
# Hinh hoc cua bar KHONG doi theo chien luoc -> tinh mot lan, dung lai.
_BO_NHO_HINH_HOC: dict = {}
_TRAN_BO_NHO = 32


def _khoa_index(index) -> tuple:
    """Van tay RE cua mot index: (so bar, moc dau, moc cuoi). O(1).

    Hai index khac nhau ma trung ca ba la truong hop khong ton tai trong day
    chuyen nay (cung tai san + cung khung + cung cua so = cung index).
    """
    n = len(index)
    if n == 0:
        return (0, 0, 0)
    v = index.values
    return (n, int(v[0].astype("int64")), int(v[-1].astype("int64")))


def hinh_hoc(index) -> tuple:
    """(so_ngay_toi_bar_ke_tiep, gio_cua_bar) - tinh mot lan moi index.

    Engine gan `v[i]` cho loi suat open[i] -> open[i+1], nen phi giu cua v[i]
    cung phai dung dung interval do. Bar cuoi khong con interval va co phi 0.
    """
    k = _khoa_index(index)
    hh = _BO_NHO_HINH_HOC.get(k)
    if hh is None:
        ngay = np.zeros(len(index), dtype=float)
        if len(index) > 1:
            ngay[:-1] = (np.diff(index.to_numpy()).astype("timedelta64[s]")
                         .astype(float) / 86400.0)
        try:
            gio = index.hour.to_numpy()
        except Exception:
            gio = np.zeros(len(index), dtype=int)
        hh = (ngay, gio)
        if len(_BO_NHO_HINH_HOC) >= _TRAN_BO_NHO:
            _BO_NHO_HINH_HOC.clear()
        _BO_NHO_HINH_HOC[k] = hh
    return hh


#: Manh ten cho biet day la chi so co phieu / ETF co phieu, khong phai ty gia.
#:
#: Bo sung 21-22/08: kho co 33 chuoi chi so DAI (Yahoo, 20-56 nam) va ban cu
#: xep NIKKEI, SP500, KOSPI, ASX200, SENSEX, TSX... vao "fx" vi khong manh ten
#: nao khop. Hau qua khong nam o mo hinh chi phi (chuoi nay khong mua duoc) ma
#: nam o `nhan/pham_vi.py`: nhom DOI CHUNG "fx" bi nhet day chi so co phieu, nen
#: phep thu phan chung - thu duy nhat phan biet duoc co che voi fit - mat y nghia.
_DAU_CHI_SO = ("US500", "US100", "SPX", "NAS", "DOW", "US30", "JP225", "DAX",
               "HANGSENG", "HSI", "FTSE", "UK100", "STOXX", "EUSTX", "CAC",
               "RUSSELL", "US2000", "BOVESPA", "ETF_", "QQQ", "SPY", "DIA", "IWM",
               "NIKKEI", "SP500", "KOSPI", "ASX", "AEX", "IBEX", "SMI", "SENSEX",
               "TAIWAN", "TSX", "DE40", "US2000", "NDX", "SPX500")

#: Ten day du cua nhung chuoi HANG HOA trong kho (dat ten tieng Viet o nguon
#: Yahoo). Phai khop CA TEN chu khong phai manh ten: "NGO" (ngo/corn) la manh
#: ten dai ba ky tu, tha vao `in` la no khop bat ky ma nao chua "ngo".
_TEN_HANG_HOA = {"YH_DAUWTI", "YH_KHIDOT", "YH_DONG", "YH_DAUTUONG", "YH_NGO"}
_DAU_HANG_HOA = ("WTI", "BRENT", "CRUDE", "NGAS", "NATGAS", "COPPER", "CORN",
                 "SOYBEAN", "USOIL", "UKOIL")
#: Chuoi kim loai quy dat ten tieng Viet.
_TEN_KIM_LOAI_QUY = {"YH_VANG", "YH_BAC"}


def _loai_tai_san(ma: str) -> str:
    """Phan loai tai san de chon quy uoc chi phi va de gom nhom nghien cuu.

    Ban cu chi co ba dong va nhanh cuoi `return "fx"` BAT HET, nen `ETF_QQQ`,
    `YH_HANGSENG` deu thanh "fx"; `XM_XAUEUR` cung thanh "fx" vi no chua "XAU"
    nhung khong BAT DAU bang "XAU". Voi chi phi thi `point_cua` co nhanh du
    phong theo do lon gia nen phan lon duoc cuu, nhung voi phep thu phan chung
    theo lop tai san (`nhan/pham_vi.py`) thi mot nhom doi chung lan ETF va chi
    so vao se lam hong ket luan.
    """
    m = ma.upper()
    if m in _TEN_KIM_LOAI_QUY or "XAU" in m or "GOLD" in m or "XAG" in m or "SILVER" in m:
        return "vang"
    if m in _TEN_HANG_HOA or any(k in m for k in _DAU_HANG_HOA):
        return "hang_hoa"
    if any(k in m for k in _DAU_CHI_SO):
        return "chi_so_my"
    return "fx"


def point_cua(ma: str, gia_dien_hinh: float) -> float:
    """Suy kich thuoc point. Uu tien bang do lon gia de khong phu thuoc ten."""
    m = ma.upper()
    lt = _loai_tai_san(m)
    if lt == "chi_so_my":
        return 0.01
    if lt == "vang":
        # Vang ~2.000 USD/oz bao gia 2 chu so thap phan -> point 0,01.
        # Bac ~25 USD/oz bao gia 3 chu so -> point 0,001. Dung chung 0,01 cho ca
        # hai thi chi phi cua bac bi thoi len 10 lan.
        return 0.01 if gia_dien_hinh >= 100 else 0.001
    if m.endswith("JPY") or "JPY" in m:
        return 1e-3
    # cap FX thuong: gia ~0,5-2,0 -> 5 chu so thap phan
    return 1e-5 if gia_dien_hinh < 20 else 0.01


@dataclass
class MoHinhChiPhi:
    """Chi phi cho MOT tai san. Tat ca don vi la PHAN CUA GIA (frac), khong phai pip."""
    ma: str
    spread_frac_theo_gio: dict = field(default_factory=dict)  # gio -> frac (mot chieu)
    spread_frac_chung: float = 0.0
    truot_gia_frac: float = 0.0
    phi_nam_mua: float = 0.0       # phi giu qua dem, chieu mua, ty le/nam
    phi_nam_ban: float = 0.0       # chieu ban (co the AM = duoc nhan)
    do_tin: str = "KHAI"           # DO | SAN | KHAI
    nguon: str = ""
    do_luc: str = ""
    canh_bao: list = field(default_factory=list)

    # ---- ap vao mot chuoi bar --------------------------------------------
    def spread_mang(self, index: pd.DatetimeIndex) -> np.ndarray:
        """Spread MOT CHIEU theo tung bar (frac). Dung gio cua bar khi co."""
        if self.spread_frac_theo_gio:
            gio = hinh_hoc(index)[1]
            mac = self.spread_frac_chung
            bang = np.full(24, mac, dtype=float)
            for g, v in self.spread_frac_theo_gio.items():
                bang[int(g)] = v
            return bang[gio]
        return np.full(len(index), self.spread_frac_chung, dtype=float)

    def phi_giu_mang(self, index: pd.DatetimeIndex, huong: np.ndarray,
                     lai_suat_nam: np.ndarray | None = None) -> np.ndarray:
        """Phi giu qua dem tinh theo SO NGAY THAT giua cac bar, va theo CHIEU.
        huong: mang -1/0/+1. Tra ve frac phai TRU khoi loi suat moi bar.

        Bat doi xung mua/ban la co chu y: day la loi that #1 ngay 09/08
        (phi chi tinh cho chieu mua -> tang 2 %/nam alpha gia cho chien luoc
        co chieu ban). Canary `luon ban 100%` gac dung cho nay.
        """
        ngay = hinh_hoc(index)[0]
        mua = np.clip(huong, 0, 1)
        ban = np.clip(-huong, 0, 1)
        if lai_suat_nam is not None:
            # mo hinh theo co che: lai suat thuc tung ngay + markup co dinh
            markup_mua = self.phi_nam_mua - float(np.nanmean(lai_suat_nam))
            markup_ban = self.phi_nam_ban + float(np.nanmean(lai_suat_nam))
            pm = lai_suat_nam + markup_mua
            pb = -lai_suat_nam + markup_ban
        else:
            pm = np.full(len(index), self.phi_nam_mua)
            pb = np.full(len(index), self.phi_nam_ban)
        return (mua * pm + ban * pb) * ngay / 365.0

    def thanh_phan(self) -> dict:
        """Vector thanh phan chi phi - dung de tinh do nhay (THIET_KE muc 7)."""
        return {"spread": self.spread_frac_chung, "truot_gia": self.truot_gia_frac,
                "phi_mua": self.phi_nam_mua, "phi_ban": self.phi_nam_ban}

    def bien_the(self, **doi) -> "MoHinhChiPhi":
        """Ban sao voi mot thanh phan bi day lech - de do dao ham rieng."""
        d = asdict(self)
        d.pop("canh_bao", None)
        m = MoHinhChiPhi(**{k: v for k, v in d.items() if k != "canh_bao"})
        m.canh_bao = list(self.canh_bao)
        for k, v in doi.items():
            if k == "spread":
                m.spread_frac_chung = v
                m.spread_frac_theo_gio = {g: x * (v / self.spread_frac_chung)
                                          for g, x in self.spread_frac_theo_gio.items()} \
                    if self.spread_frac_chung > 0 else {}
            elif k == "truot_gia":
                m.truot_gia_frac = v
            elif k == "phi_mua":
                m.phi_nam_mua = v
            elif k == "phi_ban":
                m.phi_nam_ban = v
        return m


# ------------------------------------------------------------------- DO SPREAD
def do_spread(ma: str, df: pd.DataFrame) -> tuple[dict, float, list]:
    """Do spread THAT tu cot `spread` (POINT) cua bar MT5.

    Tra (frac_theo_gio, frac_chung, canh_bao).
    Dung TRUNG VI, khong dung trung binh: duoi spread rat lech phai.
    """
    canh_bao: list[str] = []
    if "spread" not in df.columns:
        return {}, 0.0, ["khong co cot spread"]
    gia = float(np.nanmedian(df["close"].to_numpy()))
    pt = point_cua(ma, gia)
    s = df["spread"].to_numpy(dtype=float)
    idx = df.index
    tot = (s > 0) & np.isfinite(s)
    if tot.sum() < 500:
        return {}, 0.0, [f"chi {int(tot.sum())} bar co spread > 0"]
    # bo cuoi tuan + gio roll-over
    dow = idx.dayofweek.to_numpy()
    gio = idx.hour.to_numpy()
    dung = tot & (dow < 5) & ~np.isin(gio, list(GIO_LOAI))
    if dung.sum() < 500:
        dung = tot
        canh_bao.append("khong du bar trong gio giao dich - dung ca chuoi")
    chung = float(np.median(s[dung])) * pt / gia
    theo_gio: dict[int, float] = {}
    for g in range(24):
        m = dung & (gio == g)
        if m.sum() >= 200:
            theo_gio[g] = float(np.median(s[m])) * pt / gia
    ty_le_0 = 1.0 - float(tot.mean())
    if ty_le_0 > 0.10:
        canh_bao.append(f"{ty_le_0:.1%} bar co spread=0 (bar hong)")
    return theo_gio, chung, canh_bao


SAN_UU_TIEN = ["XM", "Exness", "FXCE", "Ultima"]     # thu tu san se giao dich that


def do_spread_tu_bar_mt5(ma: str, so_bar: int = 6000, khung_mt5=None) -> dict | None:
    """Do spread tu BAR H1 CUA CHINH SAN, khi file parquet khong co cot spread.

    Vi sao can (do 16/08): `us500m_m1.parquet` va `us500cash_m30.parquet` deu
    KHONG co cot `spread` - chung duoc fetch truoc khi du an biet phai giu cot
    do. Hau qua: `do_tin` tut ve KHAI cho US500M va US500CASH, ma dieu kien 7
    cua cong doi `do_tin in (DO, SAN)`, nen HAI TAI SAN LOI CUA DU AN khong bao
    gio PASS duoc - bat ke ket qua the nao. Day chuyen mu dung cho no soi ky nhat.

    Bar H1 cua MT5 CO cot spread that (da kiem 16/08: XM US500Cash 500/500 bar
    co spread > 0, Exness US500m 500/500). Do la BAR, khong phai tick cuoi tuan
    - nen khong dinh bay "tick cuoi tuan bi thoi 2-6 lan".

    Han che phai ghi ro: chi phu duoc GIAI DOAN GAN DAY ma terminal con giu bar,
    khong phai ca lich su. Vi vay danh dau `do_tin='SAN'` chu khong phai 'DO'.
    """
    try:
        import MetaTrader5 as mt5
    except Exception:
        return None
    chuan = chuan_hoa_phoi_nhiem(ma)
    luu = _doc_luu()
    for san in SAN_UU_TIEN:
        dd = TERMINAL.get(san)
        if not dd or not Path(dd).exists():
            continue
        # tim ten symbol cua san do ung voi cung phoi nhiem
        ten_san = None
        for k in (luu.get("_theo_san", {}).get(san) or {}):
            if chuan_hoa_phoi_nhiem(k) == chuan:
                ten_san = k
                break
        if not ten_san:
            continue
        try:
            if not mt5.initialize(path=dd):
                continue
            # Ten trong config da bi `.upper()` khi luu (`US500CASH`) nhung MT5
            # PHAN BIET HOA THUONG: ten that la `US500Cash` / `US500m`. Goi bang
            # ten hoa toan bo tra ve None va khong bao loi gi - phai doi chieu
            # lai voi danh sach symbol that cua terminal.
            if mt5.symbol_info(ten_san) is None:
                that = next((s.name for s in (mt5.symbols_get() or [])
                             if s.name.upper() == ten_san.upper()), None)
                if that:
                    ten_san = that
            khung = khung_mt5 if khung_mt5 is not None else mt5.TIMEFRAME_H1
            r = None
            for _ in range(4):        # goi dau sau symbol_select hay thieu bar
                mt5.symbol_select(ten_san, True)
                r = mt5.copy_rates_from_pos(ten_san, khung, 0, so_bar)
                if r is not None and len(r) >= 500:
                    break
                time.sleep(1.5)
            si = mt5.symbol_info(ten_san)
            pt = float(si.point) if si else None
        except Exception:
            r, pt = None, None
        finally:
            try:
                mt5.shutdown()
            except Exception:
                pass
        if r is None or len(r) < 500 or not pt:
            continue
        import pandas as _pd
        d = _pd.DataFrame(r)
        d["time"] = _pd.to_datetime(d["time"], unit="s")
        gia = float(np.nanmedian(d["close"].to_numpy()))
        s = d["spread"].to_numpy(dtype=float)
        tot = (s > 0) & np.isfinite(s)
        gio = d["time"].dt.hour.to_numpy()
        dow = d["time"].dt.dayofweek.to_numpy()
        dung = tot & (dow < 5) & ~np.isin(gio, list(GIO_LOAI))
        if dung.sum() < 300:
            dung = tot
        if dung.sum() < 300:
            continue
        theo_gio = {}
        for g in range(24):
            m = dung & (gio == g)
            if m.sum() >= 50:
                theo_gio[int(g)] = float(np.median(s[m])) * pt / gia
        return {
            "chung": float(np.median(s[dung])) * pt / gia,
            "theo_gio": theo_gio,
            "san": san, "symbol": ten_san, "so_bar": int(dung.sum()),
            "tu": str(d["time"].min())[:16], "den": str(d["time"].max())[:16],
            "do_luc": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    return None


def _spread_da_luu(ma: str) -> dict | None:
    """Doc ban spread da do tu bar MT5 (cache trong config/chi_phi_do.json)."""
    d = _doc_luu().get("_spread_bar_mt5") or {}
    return d.get(chuan_hoa_phoi_nhiem(ma))


def _ghi_cau_hinh(d: dict) -> None:
    """Ghi NGUYEN TU: ghi ra file tam roi doi ten de.

    `write_text` thang len file dang duoc doc la mot cua so vai chuc mili giay
    trong do file KHONG phai JSON hop le. Bang nay 1.644 symbol, ~1 MB, va
    `dieu_phoi` chay nhieu tien trinh cung luc - mot lan doc trung cua so do thi
    `_doc_luu` nuot JSONDecodeError va tra `{}`, tuc TOAN BO phi qua dem tut ve
    KHAI trong im lang. Doi ten tren cung o dia la thao tac nguyen tu.
    """
    CAU_HINH.parent.mkdir(parents=True, exist_ok=True)
    tam = CAU_HINH.with_suffix(".json.tam")
    tam.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tam, CAU_HINH)
    _DEM_LUU.clear()


def _luu_spread(ma: str, r: dict) -> None:
    d = _doc_luu()
    d.setdefault("_spread_bar_mt5", {})[chuan_hoa_phoi_nhiem(ma)] = r
    _ghi_cau_hinh(d)


def bao_dam_spread(ma: str, toi_da_gio: float = 168.0) -> dict | None:
    """Lay spread do tu bar MT5, do lai neu ban cu qua han."""
    cu = _spread_da_luu(ma)
    if cu:
        try:
            tuoi = (time.time() -
                    time.mktime(time.strptime(cu["do_luc"], "%Y-%m-%d %H:%M:%S"))) / 3600.0
            if tuoi < toi_da_gio:
                return cu
        except Exception:
            return cu
    moi = do_spread_tu_bar_mt5(ma)
    if moi:
        _luu_spread(ma, moi)
        return moi
    return cu


def phi_cua(ma: str, san_uu_tien: list[str] | None = None) -> dict | None:
    """Tim phi qua dem cua MOT phoi nhiem, theo thu tu san UU TIEN.

    Tra cuu theo ten symbol THO la sai va sai am tham: EURCAD chi ton tai dung
    ten do tren MetaQuotes-Demo (Exness goi la EURCADM, XM goi la EURCADMICRO),
    nen tra cuu tho se lang le lay phi cua may chu DEMO - noi khong ai phai kiem
    tien nen phi luon re nhat. Da sap that ngay 15/08.
    """
    d = _doc_luu()
    ts = d.get("_theo_san", {})
    pn = chuan_hoa_phoi_nhiem(ma)
    for san in (san_uu_tien or SAN_UU_TIEN):
        for ten, r in ts.get(san, {}).items():
            if chuan_hoa_phoi_nhiem(ten) == pn:
                return {**r, "san_lay": san, "symbol_lay": ten}
    return None


def tu_du_lieu(ma: str, df: pd.DataFrame, phi_nam_mua: float | None = None,
               phi_nam_ban: float | None = None,
               san_uu_tien: list[str] | None = None) -> MoHinhChiPhi:
    """Dung mo hinh chi phi TU CHINH bar se backtest. Cach trung thuc nhat."""
    theo_gio, chung, cb = do_spread(ma, df)
    lt = _loai_tai_san(ma)
    luu = phi_cua(ma, san_uu_tien) or {}
    pm = phi_nam_mua if phi_nam_mua is not None else luu.get("phi_nam_mua")
    pb = phi_nam_ban if phi_nam_ban is not None else luu.get("phi_nam_ban")
    do_tin = "DO"
    if pm is None:
        pm = PHI_QUAN_SAT[lt]["phi_nam_mua"]
        pb = PHI_QUAN_SAT[lt]["phi_nam_ban"]
        do_tin = "KHAI"
        cb.append(f"phi qua dem KHAI BAO tu lop '{lt}' - chua do duoc tren san nao "
                  f"trong {san_uu_tien or SAN_UU_TIEN}")
    else:
        do_tin = "SAN"
        cb.append(f"phi qua dem do tu {luu['san_lay']}:{luu['symbol_lay']} "
                  f"({luu.get('do_luc','?')}), tin_cay={luu.get('tin_cay','?')}")
        if luu.get("tin_cay") in ("THAP", None):
            do_tin = "KHAI"
            cb.append("swap_mode khong quy doi chac chan -> khong du de PASS")
    if not chung:
        # Bar khong co cot `spread` (US500M/US500CASH cua du an nay la vay: file
        # parquet duoc fetch truoc khi biet phai giu cot spread). Truoc 16/08 day
        # la ngo cut - `do_tin` tut ve KHAI nen dieu kien 7 cua cong LUON sai, tuc
        # HAI TAI SAN LOI CUA DU AN khong bao gio PASS duoc du ket qua the nao.
        # Duong ra: dung spread NIEM YET doc tu chinh san (`spread_point_tick`,
        # da bo mau cuoi tuan vi cuoi tuan bi thoi 2-6 lan). Do la cung hang bang
        # chung voi phi qua dem - bang gia cua san, nen danh dau SAN chu khong DO.
        bar_san = _spread_da_luu(ma)      # ban cache; do lai la viec cua `bao_dam_spread`
        sp_pt = luu.get("spread_point_tick")
        pt_san, gia_san = luu.get("point"), luu.get("gia_luc_do")
        if bar_san and bar_san.get("chung"):
            chung = float(bar_san["chung"])
            theo_gio = {int(g): float(v) for g, v in (bar_san.get("theo_gio") or {}).items()}
            do_tin = "SAN" if do_tin != "KHAI" else "KHAI"
            cb.append(f"spread do tu BAR H1 cua {bar_san['san']}:{bar_san['symbol']} "
                      f"({bar_san['so_bar']} bar {bar_san['tu']}..{bar_san['den']}) "
                      f"= {chung*1e4:.2f} bps. File parquet khong co cot spread nen "
                      "gia tri nay chi phu giai doan gan day, KHONG phai ca lich su.")
        elif sp_pt and pt_san and gia_san:
            chung = float(sp_pt) * float(pt_san) / float(gia_san)
            do_tin = "SAN" if do_tin != "KHAI" else "KHAI"
            cb.append(f"spread lay tu BANG GIA san ({sp_pt} point @ {gia_san}) "
                      f"= {chung*1e4:.2f} bps - bar khong co cot spread. "
                      "Con so nay la HOM NAY, khong phai lich su.")
        else:
            chung = 1.0e-4
            do_tin = "KHAI"
            cb.append("spread KHAI BAO (khong do duoc tu du lieu lan tu san)")
    return MoHinhChiPhi(
        ma=ma.upper(), spread_frac_theo_gio=theo_gio, spread_frac_chung=chung,
        truot_gia_frac=chung * 0.25,     # truot ~1/4 spread, se do lai khi co lenh that
        phi_nam_mua=float(pm), phi_nam_ban=float(pb),
        do_tin=do_tin,
        nguon=f"spread: bar {ma} | phi: {luu.get('san_lay','KHAI BAO')}",
        do_luc=time.strftime("%Y-%m-%d %H:%M:%S"), canh_bao=cb)


# ---------------------------------------------------------------- DOC/LUU SAN
#: Bo nho dem cua `_doc_luu()` trong MOT tien trinh, khoa theo (mtime, size).
#:
#: `config/chi_phi_do.json` nang **1,09 MB** (1.644 symbol) va `_doc_luu()` duoc
#: goi tu `phi_cua`, `_spread_da_luu`, `bang_chenh_lech`... tuc vai lan cho MOI
#: tai san. Do bang cProfile 30/08/2026 tren mot vong pheu 20 tai san:
#: **90 lan doc = 1,46 giay**, tren tong 6-7 giay ca vong.
#:
#: Khoa la (mtime, size) chu khong phai TTL: moi duong ghi deu di qua
#: `_ghi_cau_hinh` (os.replace nguyen tu) nen mtime doi ngay, va `_ghi_cau_hinh`
#: con chu dong xoa dem. Khong co cua so doc du lieu cu.
#:
#: HOP DONG: ham tra ve chinh doi tuong trong dem, khong phai ban sao (sao chep
#: 1 MB moi lan goi thi mat luon cai vua tiet kiem). Ba duong SUA no
#: (`_luu_spread`, `do_moi_san`, muc CLI) deu ghi ngay sau khi sua, va ghi thi
#: xoa dem. Duong nao chi DOC thi khong duoc sua dict tra ve.
_DEM_LUU: dict = {}


def _khoa_cau_hinh() -> tuple | None:
    try:
        st = CAU_HINH.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def _doc_luu() -> dict:
    khoa = _khoa_cau_hinh()
    if khoa is None:
        return {}
    if _DEM_LUU.get("khoa") == khoa:
        return _DEM_LUU["d"]
    try:
        d = json.loads(CAU_HINH.read_text(encoding="utf-8-sig"))
    except Exception:
        # Doc trung cua so ghi -> KHONG dem lai `{}`, de lan sau doc lai.
        return {}
    _DEM_LUU.update({"khoa": khoa, "d": d})
    return d


TERMINAL = {
    "MetaQuotes": r"C:\Program Files\MetaTrader 5\terminal64.exe",
    "XM":         r"C:\Program Files\XM MT5\terminal64.exe",
    "Exness":     r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
    "Ultima":     r"C:\Program Files\Ultima Markets MT5 Terminal\terminal64.exe",
    "FXCE":       r"C:\Program Files\FXCE MT5 Terminal\terminal64.exe",
}


# SYMBOL_SWAP_MODE cua MT5. Quy doi SAI mode la tai lap dung cai bay CLAUDE.md muc 14.
SWAP_MODE = {0: "TAT", 1: "DIEM", 2: "TIEN_SYMBOL", 3: "TIEN_KY_QUY", 4: "TIEN_NAP",
             5: "LAI_SUAT_HIEN_TAI", 6: "LAI_SUAT_MO", 7: "MO_LAI_HIEN_TAI", 8: "MO_LAI_BID"}


def _quy_doi_swap(si, gia: float, pt: float, cs: float):
    """swap_long/short -> ty le %/nam, THEO DUNG swap_mode cua symbol.

    Tra (phi_nam_mua, phi_nam_ban, tin_cay). phi duong = ta TRA; am = ta DUOC nhan.
    Dau nguoc voi swap vi swap duong nghia la duoc cong tien.

    Ba nhom mode, ba cong thuc khac han nhau:
      DIEM (1)          : swap la POINT/dem      -> swap*point*365/gia
      TIEN (2,3,4)      : swap la TIEN/lot/dem   -> swap*365/(contract*gia)
      LAI_SUAT (5,6)    : swap DA LA %/nam       -> lay thang, khong nhan gi
    Mode 0 = khong thu swap. Mode 7,8 khong quy doi duoc -> tra None.
    """
    mode = int(getattr(si, "swap_mode", -1))
    sl, ss = float(si.swap_long), float(si.swap_short)
    if mode == 0:
        return 0.0, 0.0, "TAT"
    if mode == 1:
        return -(sl * pt) * 365.0 / gia, -(ss * pt) * 365.0 / gia, "CAO"
    if mode in (2, 3, 4):
        if not cs or not gia:
            return None, None, "THIEU_CONTRACT"
        gia_tri_lot = cs * gia          # xap xi: bo qua quy doi tien te tai khoan
        return (-sl * 365.0 / gia_tri_lot, -ss * 365.0 / gia_tri_lot, "VUA")
    if mode in (5, 6):
        return -sl / 100.0, -ss / 100.0, "CAO"
    if mode == 9:
        # Mode 9 KHONG CO trong tai lieu MT5 (API chi den 8) nhung mot so san van
        # tra ve - da xac nhan tren dien dan MQL5. Phong doan tot nhat cua cong dong:
        # "swap tinh bang TIEN, theo dong tien YET GIA". Ta quy doi nhu nhom tien
        # nhung danh dau THAP: con so nay CHUA duoc xac minh bang sao ke that.
        if not cs or not gia:
            return None, None, "MODE9_THIEU_CONTRACT"
        gia_tri_lot = cs * gia
        return (-sl * 365.0 / gia_tri_lot, -ss * 365.0 / gia_tri_lot, "THAP")
    return None, None, f"MODE_{mode}_KHONG_QUY_DOI"


def do_tu_mt5(ma_list: list[str] | None = None, san: str | None = None,
              duong_dan: str | None = None) -> dict:
    """Doc swap tu MOT terminal MT5. Ghi vao config theo tung san.

    swap_long/short la POINT/dem cho 1 lot -> quy ra ty le nam THEO GIA LUC DO,
    va ghi ro `gia_luc_do`. Ty le %/nam nay GIAM khi gia tang, nen KHONG duoc
    ap lai cho lich su - do dung la bay CLAUDE.md muc 13-14.

    KHONG luu spread doc tu tick vao cuoi tuan: no bi thoi 2-6 lan.
    Spread that lay tu cot `spread` cua bar lich su (ham `do_spread`).
    """
    try:
        import MetaTrader5 as mt5
    except Exception as e:
        return {"loi": f"khong import duoc MetaTrader5: {e}"}
    kw = {"path": duong_dan} if duong_dan else {}
    if not mt5.initialize(**kw):
        return {"loi": f"khong ket noi duoc MT5 ({san or 'mac dinh'}): {mt5.last_error()}"}
    try:
        tk = mt5.account_info()
        may_chu = tk.server if tk else "?"
        nhan = san or may_chu
        cuoi_tuan = time.localtime().tm_wday >= 5
        ds = ma_list or [s.name for s in (mt5.symbols_get() or [])][:400]
        out = _doc_luu()
        # THAY, khong GOP: neu gop thi ban ghi sai tu lan do truoc (vi du quy doi
        # nham swap_mode) se nam lai trong file va tiep tuc duoc dung. Da sap that
        # ngay 15/08: FXCE mode 9 bi bo qua o lan do 2 nhung so cu van con, va no
        # tao ra mot "chenh lech 5,55 diem %/nam" hoan toan gia.
        out.setdefault("_theo_san", {})[nhan] = {}
        kho_san = out["_theo_san"][nhan]
        dem, bo_qua, khong_quy_doi = 0, 0, {}
        for ma in ds:
            si = mt5.symbol_info(ma)
            if si is None or not (si.bid or si.ask or getattr(si, "last", 0)):
                # symbol chua duoc chon vao Market Watch -> khong co gia. Chon roi doc lai.
                # (Khong lam buoc nay thi XM chi tra 16/1000+ symbol.)
                try:
                    mt5.symbol_select(ma, True)
                    si = mt5.symbol_info(ma)
                except Exception:
                    si = None
            if si is None:
                bo_qua += 1
                continue
            gia = si.bid or si.ask or getattr(si, "last", 0)
            if not gia:
                bo_qua += 1
                continue
            pt = si.point or point_cua(ma, gia)
            cs = float(getattr(si, "trade_contract_size", 0) or 0)
            pm, pb, tin_cay = _quy_doi_swap(si, gia, pt, cs)
            if pm is None:
                bo_qua += 1
                khong_quy_doi[tin_cay] = khong_quy_doi.get(tin_cay, 0) + 1
                continue
            ban_ghi = {
                "phi_nam_mua": round(float(pm), 5), "phi_nam_ban": round(float(pb), 5),
                "tin_cay": tin_cay,
                "gia_luc_do": float(gia), "point": float(pt), "contract_size": cs,
                "swap_mode": int(getattr(si, "swap_mode", -1)),
                "swap_long": float(si.swap_long), "swap_short": float(si.swap_short),
                "nguon": f"MT5:{may_chu}", "san": nhan,
                "do_luc": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            if not cuoi_tuan:
                ban_ghi["spread_point_tick"] = int(si.spread)
            kho_san[ma.upper()] = ban_ghi
            out[ma.upper()] = ban_ghi             # ban mac dinh cho tra cuu nhanh
            dem += 1
        _ghi_cau_hinh(out)
        return {"san": nhan, "may_chu": may_chu, "da_do": dem, "bo_qua": bo_qua,
                "khong_quy_doi_duoc": khong_quy_doi,
                "cuoi_tuan_bo_spread": cuoi_tuan, "file": str(CAU_HINH)}
    finally:
        mt5.shutdown()


def do_moi_san(ma_list: list[str] | None = None) -> dict:
    """Do lan luot moi terminal da cai. Nen tang cua SO CHENH LECH CHI PHI.

    THIET_KE muc 1: cung phoi nhiem, phi giu dai chenh 5,5 diem %/nam giua cac
    san - lon hon gan nhu moi edge qua 324 phep thu. Loai alpha nay KHONG can
    backtest, KHONG can placebo, KHONG ton slot FDR.
    """
    ra = {}
    for san, dd in TERMINAL.items():
        if not Path(dd).exists():
            ra[san] = {"bo_qua": "chua cai"}
            continue
        ra[san] = do_tu_mt5(ma_list, san=san, duong_dan=dd)
        time.sleep(2)
    return ra


import re as _re

# Ten symbol khac nhau tung san cho CUNG MOT phoi nhiem kinh te:
#   XM `US500Cash` = Exness `US500m` = FXCE `SPX500`.
# Khong chuan hoa thi bang chenh lech rong tuech - da sap that lan dau chay 15/08.
BI_DANH = {
    "SPX500": "US500", "SP500": "US500", "US500CASH": "US500", "USA500": "US500",
    "NAS100": "US100", "USTEC": "US100", "US100CASH": "US100", "NDX100": "US100",
    "US30CASH": "US30", "DJ30": "US30", "WS30": "US30",
    "GER40CASH": "GER40", "DE40": "GER40", "DAX40": "GER40", "GER30": "GER40",
    "JP225CASH": "JP225", "JPN225": "JP225",
    "UK100CASH": "UK100", "FRA40CASH": "FRA40", "AUS200CASH": "AUS200",
    "GOLD": "XAUUSD", "SILVER": "XAGUSD",
    "OILCASH": "USOIL", "CRUDOIL": "USOIL", "WTI": "USOIL", "XTIUSD": "USOIL",
    "BRENT": "UKOIL", "XBRUSD": "UKOIL",
    # --- TEN TRONG KHO DU LIEU CUA DU AN (tien to `YH_` da duoc bo o tren) ---
    # Chi so KHONG mua truc tiep duoc; kenh giao dich cua no la CFD cua san.
    # Nen phoi nhiem kinh te cua `YH_NASDAQ` chinh la `US100`, va chi phi phai
    # lay tu do. Truoc 24/08 cac ma nay khong khop duoc gi nen roi ve bang khai
    # bao theo lop - va bang do lai xep chung vao `fx_cheo`.
    "NASDAQ": "US100", "DOWJONES": "US30", "RUSSELL2000": "US2000",
    "DAX": "GER40", "FTSE100": "UK100", "CAC40": "FRA40", "ASX200": "AUS200",
    "NIKKEI": "JP225", "HANGSENG": "HK50", "EUSTOXX50": "EU50",
    "EUSTX50": "EU50", "SMI": "SWI20", "IBEX35": "SPA35", "ESP35": "SPA35",
    "AEX": "NETH25", "TSX": "CA60",
    "VANG": "XAUUSD", "BAC": "XAGUSD", "DAUWTI": "USOIL", "KHIDOT": "NGAS",
}

#: Tien to do KHO DU LIEU cua du an dat them, khong phai cua san.
#:
#: `du_lieu.kho()` dat ten bang theo TEN FILE, nen `yh_nasdaq_daily.parquet`
#: thanh ma `YH_NASDAQ` va `xm_us100cash_m5.parquet` thanh `XM_US100CASH`.
#: Truoc 24/08 khong cho nao bo tien to nay truoc khi tra cuu phi, nen:
#:      XM_US100CASH -> 'XM_US100'  -> khong khop gi
#:      US100CASH    -> 'US100'     -> khop XM:US100CASH
#: tuc CUNG MOT symbol cua CUNG MOT san, chi khac tien to ten file, mot ben co
#: phi do that va mot ben roi ve bang khai bao. Do 24/08: 11 ma `XM_*` va 30 ma
#: `YH_*` deu dang o dien "khong tim thay".
TIEN_TO_KHO = ("XM_", "YH_", "ETF_")
_DUOI = ("MICRO", "CASH", "ECN", "PRO", "STP", "RAW", "_SB", "#", ".A", ".R", ".P",
         ".S", ".ECN", "_I", "-5", "+")


def chuan_hoa_phoi_nhiem(ma: str) -> str:
    """Ten symcua nhieu san -> mot ten phoi nhiem chung."""
    m = ma.upper().strip()
    for t in TIEN_TO_KHO:
        if m.startswith(t):
            m = m[len(t):]
            break
    for d in _DUOI:
        if m.endswith(d):
            m = m[: -len(d)]
    m = _re.sub(r"[._\-#]+$", "", m)
    # hau to 'M' cua Exness (EURUSDM, XAUUSDM) - chi bo khi phan con lai la 6 chu cai
    if len(m) == 7 and m.endswith("M") and m[:6].isalpha():
        m = m[:6]
    # Hau to 'M'/'m' cua Exness tren CHI SO va HANG HOA: `US500m`, `XAUUSDm`.
    # Truoc 16/08 chi bo khi phan con lai la KHOA cua BI_DANH, nen `US500M` giu
    # nguyen trong khi XM `US500Cash` rut ve `US500` -> hai san cung mot phoi
    # nhiem lai thanh hai muc khac nhau, va tra cuu cheo san im lang truot.
    _TEN_CHUAN = set(BI_DANH) | set(BI_DANH.values())
    if m.endswith("M") and m[:-1] in _TEN_CHUAN:
        m = m[:-1]
    return BI_DANH.get(m, m)


# San GIAO DICH DUOC bang tien that. MetaQuotes-Demo la may chu demo cua chinh
# MetaQuotes - KHONG mo tai khoan that duoc, nen dua no vao bang so sanh la tu
# lua: no thuong re nhat vi khong ai phai kiem tien tren do.
SAN_GIAO_DICH_DUOC = {"XM", "Exness", "Ultima", "FXCE"}


def bang_chenh_lech(phoi_nhiem: list[str] | None = None,
                    chi_san_that: bool = True) -> list[dict]:
    """SO CHENH LECH CHI PHI TRIEN KHAI - alpha phep tru.

    Cung mot phoi nhiem kinh te, kenh nao re nhat BAY GIO?
    Khong can backtest, khong can placebo, khong ton slot FDR (THIET_KE muc 1).
    """
    kho_san = _doc_luu().get("_theo_san", {})
    if chi_san_that:
        kho_san = {s: v for s, v in kho_san.items() if s in SAN_GIAO_DICH_DUOC}
    if len(kho_san) < 2:
        return []
    # gom theo PHOI NHIEM CHUNG, khong theo ten symbol
    theo_pn: dict[str, dict] = {}
    for san, v in kho_san.items():
        for ma, d in v.items():
            pn = chuan_hoa_phoi_nhiem(ma)
            theo_pn.setdefault(pn, {})[san] = (ma, d)
    if phoi_nhiem:
        loc = {chuan_hoa_phoi_nhiem(m) for m in phoi_nhiem}
        theo_pn = {k: v for k, v in theo_pn.items() if k in loc}

    ra = []
    for pn, kenh in sorted(theo_pn.items()):
        if len(kenh) < 2:
            continue
        hang = sorted(((san, d["phi_nam_mua"], ma, d.get("tin_cay", "?"))
                       for san, (ma, d) in kenh.items()), key=lambda x: x[1])
        re_, dat = hang[0], hang[-1]
        tin = {h[3] for h in hang}
        ra.append({
            "phoi_nhiem": pn, "so_kenh": len(hang),
            "kenh_re": re_[0], "symbol_re": re_[2], "phi_re_pct_nam": round(re_[1] * 100, 3),
            "kenh_dat": dat[0], "symbol_dat": dat[2], "phi_dat_pct_nam": round(dat[1] * 100, 3),
            "chenh_diem_pct_nam": round((dat[1] - re_[1]) * 100, 3),
            "tat_ca": {s: round(m * 100, 3) for s, m, _, _ in hang},
            "symbol_tung_san": {s: sym for s, _, sym, _ in hang},
            "tin_cay": "CAO" if tin <= {"CAO", "TAT"} else "VUA",
            "co_che": "phi giu qua dem co dinh theo bieu phi tung san",
            "dieu_kien_de_sai": f"{re_[0]} doi bieu phi; rui ro doi tac cua {re_[0]} tang; "
                                "hai symbol khong that su cung phoi nhiem (kiem contract size)",
        })
    ra.sort(key=lambda x: -x["chenh_diem_pct_nam"])
    return ra


if __name__ == "__main__":
    import sys
    if "--do-moi-san" in sys.argv:
        print(json.dumps(do_moi_san(), ensure_ascii=False, indent=1))
    elif "--do-mt5" in sys.argv:
        print(json.dumps(do_tu_mt5(), ensure_ascii=False, indent=1))
    elif "--chenh-lech" in sys.argv:
        tat = "--tat-ca" in sys.argv
        b = bang_chenh_lech(chi_san_that=not tat)
        if not b:
            print("Chua co du lieu 2 san tro len. Chay: python nhan/chi_phi.py --do-moi-san")
        print("SO CHENH LECH CHI PHI TRIEN KHAI - phi giu vi the MUA, %/nam")
        print("(am = duoc tra tien de giu; chi tinh san GIAO DICH DUOC"
              + (" - dang bao gom ca demo" if tat else "") + ")\n")
        for r in b[:40]:
            print(f"  {r['phoi_nhiem']:<10} CHENH {r['chenh_diem_pct_nam']:+7.3f} diem  "
                  f"re: {r['kenh_re']:<8}{r['phi_re_pct_nam']:+7.3f}  "
                  f"dat: {r['kenh_dat']:<8}{r['phi_dat_pct_nam']:+7.3f}  "
                  f"[{r['tin_cay']}] {r['tat_ca']}")
            print(f"             symbol: {r['symbol_tung_san']}")
    else:
        d = _doc_luu()
        print("san da do:", list(d.get("_theo_san", {})))
        print("symbol da co phi:", len([k for k in d if not k.startswith("_")]))
        print("dung: --do-moi-san | --do-mt5 | --chenh-lech")
