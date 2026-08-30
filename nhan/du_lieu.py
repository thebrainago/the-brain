# -*- coding: utf-8 -*-
"""du_lieu.py - NAP DU LIEU TU CHINH CONG CU SE GIAO DICH.

Bo yfinance khoi duong kiem dinh. Ly do (CLAUDE.md muc 15): tuong quan V6
nikkei-sp500 la 0,17 tren bar Yahoo (phien noi dia) nhung 0,58 tren bar CFD
24h cua XM. Moi phep tinh phai dung du lieu CUA CHINH cong cu se giao dich.

Nguon: `data/*_M1_mq.parquet` (5 trieu bar/cap - tran cua terminal MetaQuotes),
co cot `spread` THAT tung bar. Gop len khung lon co CACHE.

Bay da biet, da chan o day:
  - `open` bia truoc 2006 (memory `open-bia-truoc-2006`): kiem ty le
    open[i] == close[i-1]; > 90% thi bao dong, quy tac open[i+1] vo hieu.
  - Bar co rau hong (CLAUDE.md muc 48): low < min(open,close)*0,90.
  - Gop khung phai lay `spread` bang TRUNG VI, khong phai trung binh.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
GOC = LAB.parent
DATA = GOC / "data"
CACHE = LAB / "data_khung"

QUY_KHUNG = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min",
             "H1": "1h", "H4": "4h", "D1": "1D"}
PHUT_KHUNG = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
BAR_MOI_NAM = {"M1": 372_000, "M5": 74_400, "M15": 24_800, "M30": 12_400,
               "H1": 6_200, "H4": 1_550, "D1": 260}
# Duoi ten file -> khung goc. Doc theo thu tu, cai dai truoc.
DUOI_KHUNG = [("_m1_mq", "M1"), ("_m1", "M1"), ("_m5_day_du", "M5"), ("_m5", "M5"),
              ("_m15", "M15"), ("_m30", "M30"), ("_h1_dai", "H1"), ("_h1", "H1"),
              ("_h4", "H4"), ("_d1_xm", "D1"), ("_d1", "D1"), ("_daily_dai", "D1"),
              ("_mt5_daily", "D1"), ("_xm_daily", "D1"), ("_daily", "D1"), ("_w1", "W1")]


#: Duoi ten file cua bang XUAT TU TERMINAL MT5 (nguon "san"). Doc TRUOC `_daily`
#: vi `xxx_mt5_daily` cung ket thuc bang `_daily`.
DUOI_SAN = ("_m1_mq", "_d1_xm", "_mt5_daily", "_xm_daily", "_m1", "_m5", "_m15",
            "_m30", "_h1", "_h4", "_h1_dai", "_m5_day_du")
#: Tien to / duoi cua bang lay tu NGUON NGOAI (Yahoo, ETF, chuoi chi so dai).
TIEN_TO_NGOAI = ("yh_", "etf_")
DUOI_NGOAI = ("_daily", "_daily_dai")

#: Tien to cua bang XUAT TU TERMINAL, doc TRUOC `DUOI_NGOAI`.
#:
#: Vi sao can (do 24/08): `xm_us500cash_daily` va `us500cash_xm_daily` la CUNG
#: MOT chuoi - lech trung vi 0,0000% va tuong quan loi suat ngay 1,0000 - nhung
#: luat duoi ten xep cai thu nhat vao `ngoai` (vi ket thuc bang `_daily`) va cai
#: thu hai vao `san`. Cung mot cong cu ma hai lop nguon thi hai nguong open bia
#: khac nhau (0,20 va 0,60) va mot ben bi `cat_theo_chat_luong` con ben kia
#: khong. Do la ly do XM_EURUSD chi con 2006-2016 trong khi file co du 2006-2026.
#:
#: Bang chung do duoc: 11 bang `xm_*` co ty le `open[i]==close[i-1]` la
#: 0,000-0,151 - tuc chung la BAO GIA LIEN TUC cua san, khong phai gia dong
#: phien cua so giao dich. Nguong phien 0,20 danh cho chung la ap sai co che.
TIEN_TO_SAN = ("xm_",)


def nguon_cua(ten_file: str) -> str:
    """`san` = xuat tu terminal MT5 | `ngoai` = feed ben ngoai (Yahoo/ETF).

    Vi sao phai biet: hai nguon co CO CHE TAO BAR khac han nhau, va moi phep
    kiem chat luong deu phai doi nguong theo co che do (xem `NGUONG_OPEN_BIA`).
    Feed MT5 la bao gia LIEN TUC 24/5 - `open[i] == close[i-1]` o 20-60% bar la
    binh thuong. Feed ngay cua chi so la gia DONG CUA PHIEN - phai co gap, ty le
    that do duoc la 0,1-3%; 20% da la dau hieu bia.

    Suy tu duoi ten file chu khong tu ten tai san: `us500m_m1` la MT5 du khong
    co chu MT5 nao, con `sp500_daily` thi khong.
    """
    t = ten_file.lower()
    if any(t.startswith(x) for x in TIEN_TO_NGOAI):
        return "ngoai"
    if any(t.startswith(x) for x in TIEN_TO_SAN):
        return "san"
    for d in DUOI_SAN:
        if t.endswith(d):
            return "san"
    for d in DUOI_NGOAI:
        if t.endswith(d):
            return "ngoai"
    return "san"


def cot_goc(f) -> list[str]:
    """Ten cot cua mot parquet, doc tu SCHEMA - khong nap mot dong nao.

    Kho co 189 bang nhung `VIX` chi co `vix_close`, `ETF_*` chi co `close`,
    `COT_TFF` la bang vi the. Nap ca file roi moi biet la ton vai giay moi bang;
    doc schema het vai mili giay.
    """
    try:
        import pyarrow.parquet as pq
        return [str(c).lower() for c in pq.ParquetFile(f).schema_arrow.names]
    except Exception:
        try:
            return [str(c).lower() for c in pd.read_parquet(f).columns]
        except Exception:
            return []


def so_dong_goc(f) -> int:
    """So dong cua parquet, doc tu metadata."""
    try:
        import pyarrow.parquet as pq
        return int(pq.ParquetFile(f).metadata.num_rows)
    except Exception:
        return 0


#: Bo nho dem cua `kho()` trong MOT tien trinh.
#:
#: `kho()` doc schema cua 189 parquet, mat ~0,34 giay. No duoc goi tu
#: `nguon_tai_san`, `_khung_cua`, `nam_dung_duoc`, `nap` - tuc vai lan cho MOI
#: tai san trong moi vong quet. Do 22/08: mot vong `_cap_ke_tiep` tren 29 tai
#: san goi `kho()` 80 lan = 27 giay khong lam gi ca.
#:
#: Van tay de xa cache: (so file, tong mtime). Them/bot/ghi de mot file la doi.
_DEM_KHO: dict = {}

#: Bao lau moi cho phep tinh lai VAN TAY (giay).
#:
#: Do that bang cProfile 30/08/2026 tren mot vong pheu 20 tai san D1:
#: `_van_tay_kho` bi goi **936 lan trong 60 giay** va moi lan `stat()` ca 253
#: file parquet -> **243.286 lenh `nt.stat`, chiem 42% TOAN BO thoi gian chay**.
#: Tuc phep KIEM cache dat hon han thu no bao ve.
#:
#: TTL 5 giay: trong mot vong quet, `data/` khong doi; neu co doi that thi cham
#: nhat 5 giay sau la thay. Muon chinh xac tuyet doi thi goi `kho(lam_moi=True)`.
_TTL_VAN_TAY = 5.0


def _van_tay_kho() -> tuple:
    if not DATA.exists():
        return (0, 0.0)
    n, t = 0, 0.0
    for p in DATA.glob("*.parquet"):
        n += 1
        t += p.stat().st_mtime
    return (n, round(t, 3))


def kho(lam_moi: bool = False) -> dict[str, dict]:
    """Liet ke tai san co san + khung goc + nguon + co du OHLC khong.

    `lam_moi=True` bo qua TTL va tinh lai van tay ngay. Dung khi vua ghi them
    file vao `data/` trong cung tien trinh va can thay ngay lap tuc.
    """
    bay_gio = time.monotonic()
    if (not lam_moi and "ds" in _DEM_KHO
            and bay_gio - _DEM_KHO.get("luc", -1e18) < _TTL_VAN_TAY):
        return _DEM_KHO["ds"]
    vt = _van_tay_kho()
    if _DEM_KHO.get("van_tay") == vt and "ds" in _DEM_KHO:
        _DEM_KHO["luc"] = bay_gio
        return _DEM_KHO["ds"]
    ra: dict[str, dict] = {}
    if not DATA.exists():
        _DEM_KHO.update({"van_tay": vt, "ds": ra, "luc": bay_gio})
        return ra
    ban_theo_ma: dict[str, list[dict]] = {}
    for p in sorted(DATA.glob("*.parquet")):
        ten = p.stem
        thap = ten.lower()
        khung_goc, ma = "?", ten
        for duoi, k in DUOI_KHUNG:
            if thap.endswith(duoi):
                ma, khung_goc = ten[: -len(duoi)], k
                break
        ma = ma.upper()
        cot = cot_goc(p)
        so_dong = so_dong_goc(p)
        ban = {"ma": ma, "file": p, "khung_goc": khung_goc,
               "kich_thuoc": p.stat().st_size,
               "nguon": nguon_cua(ten), "cot": cot,
               "du_ohlc": all(c in cot for c in ("open", "high", "low", "close")),
               "co_spread": "spread" in cot,
               "so_dong": so_dong,
               "uoc_so_nam": round(so_dong / BAR_MOI_NAM[khung_goc], 2)
               if khung_goc in BAR_MOI_NAM and so_dong else 0.0}
        ban_theo_ma.setdefault(ma, []).append(ban)
        cu = ra.get(ma)
        if cu is None or p.stat().st_size > cu["kich_thuoc"]:
            ra[ma] = ban

    for ma, cac in ban_theo_ma.items():
        goc = ra[ma]
        goc["cac_ban"] = cac
        goc["lop_nguon"] = lop_nguon_cua(cac)
        cung_lop = [b for b in cac if b["nguon"] == goc["lop_nguon"] and b["du_ohlc"]]
        # `khung_min` = khung GOC MIN NHAT con dung duoc, khong phai khung cua
        # ban to nhat. Bo loc "khung goc co min hon khung yeu cau khong" phai
        # hoi ca kho cua mot ma, neu khong thi XM_US500CASH (ban to nhat la M5,
        # ban D1 co 4.028 bar) bi loai khoi moi phep quet D1 vi ban M5 chi phu
        # 367 ngay.
        hop_le = [b["khung_goc"] for b in cung_lop if b["khung_goc"] in PHUT_KHUNG]
        goc["khung_min"] = (min(hop_le, key=lambda k: PHUT_KHUNG[k])
                            if hop_le else goc["khung_goc"])
        # `uoc_so_nam` = do phu DAI NHAT trong kho cua ma nay. Dung ban to nhat
        # thi US500CASH bao 8,06 nam (file M30) trong khi ban D1 co 15,5 nam.
        goc["uoc_so_nam"] = max([b["uoc_so_nam"] for b in cung_lop] or
                                [goc["uoc_so_nam"]])
    _DEM_KHO.update({"van_tay": vt, "ds": ra, "luc": bay_gio})
    return ra


def lop_nguon_cua(cac_ban: list[dict]) -> str:
    """Lop nguon CUA MOT MA khi cac ban khong dong nhat.

    Luat: co MOT ban `san` thi ma do la cong cu cua SAN, va moi ban `ngoai`
    mang cung ten la nhan SAI - phai loai, khong duoc dung lam "ban dai hon".

    Do 24/08 tren ba truong hop that trong kho nay:
      - `us500cash_daily.parquet` khop **0,000** voi Yahoo ^GSPC (`sp500_daily`)
        va lech 0,073% voi CFD cua XM. No la CHI SO, khong phai CFD - dung no
        cho ma US500CASH vua doi cong cu vua nhan ban SP500 thanh hai tai san.
      - `AUDCAD_daily_dai` / `AUDNZD_daily_dai` / `NZDCAD_daily_dai` cung muc
        gia voi ban broker (lech 0,24-0,36%) nhung **tuong quan loi suat ngay
        chi 0,08-0,14**: nen ngay cat o gio khac. Ghep hai chuoi nay lai la
        ghep hai chuoi khac nhau.
      - nguoc lai `xm_us500cash_daily` va `us500cash_xm_daily` lech 0,0000% va
        tuong quan 1,0000 - cung mot chuoi, va do la ly do `TIEN_TO_SAN` phai
        xep `xm_*` vao `san` truoc khi luat nay chay.
    """
    return "san" if any(b["nguon"] == "san" for b in cac_ban) else "ngoai"


#: Khung TO NHAT ma van con giu duoc spread that khi gop tu ban min hon.
#: Gop len H1 giu lai ~83.000 mau spread cho mot chuoi FX 25 nam - du de lay
#: trung vi theo gio - ma khong phai nap 5 trieu dong M1 moi lan hoi chi phi.
KHUNG_DO_SPREAD_MIN = "H1"


def khung_do_spread(ma: str) -> str | None:
    """Khung NEN DUNG de DO CHI PHI cua `ma` - tach khoi khung chay backtest.

    Vi sao phai tach (do 24/08, ngay sau khi `ban_cho_khung` di vao hoat dong):
    ban D1 dai nhat cua mot ma thuong la ban KHONG co cot spread, con ban M1
    ngan hon lai co spread that tung bar. Chon ban theo do phu la dung cho BAR,
    nhung neu do chi phi tren chinh ban do thi:

        AUDCAD  D1 khong co cot spread -> 1,00 bps KHAI BAO
                H1 co 82.811 bar spread -> **1,90 bps DO DUOC**
        EURCAD  D1 co spread o 2.480/6.672 bar -> 1,70 bps
                H1 co spread o 83.354/83.524 bar -> 1,22 bps

    Bon ma (AUDCAD, EURGBP, AUDNZD, AUDCHF) tut tu `do_tin=SAN` xuong `KHAI` va
    an mot spread bia 1,00 bps - thap hon muc do duoc 1,9-2,75 lan. Chi phi la
    DAI LUONG RIENG, phai lay tu nguon TOT NHAT cho no, khong phai tu nguon
    tinh co dang cap bar.

    Nguoc lai US500CASH chi co spread o ban D1 (`us500cash_xm_daily`), khong co
    o H1 - nen luat khong duoc la "luon dung H1" ma phai la "ban min nhat CO
    cot spread".
    """
    goc = kho().get((ma or "").upper())
    if goc is None:
        return None
    lop = goc.get("lop_nguon") or goc.get("nguon")
    co = [b for b in (goc.get("cac_ban") or [])
          if b.get("co_spread") and b.get("du_ohlc") and b["nguon"] == lop
          and b.get("khung_goc") in PHUT_KHUNG]
    if not co:
        return None
    min_nhat = min(co, key=lambda b: PHUT_KHUNG[b["khung_goc"]])["khung_goc"]
    if PHUT_KHUNG[min_nhat] < PHUT_KHUNG[KHUNG_DO_SPREAD_MIN]:
        return KHUNG_DO_SPREAD_MIN
    return min_nhat


def _uoc_bar_o_khung(ban: dict, khung: str) -> int:
    """So bar UOC TINH khi dua `ban` ve `khung`. 0 = khong dung duoc.

    Khong nap file: uoc tu so dong va ty le khung. Uoc nay chi dung de XEP HANG
    giua cac ban, con so bar that thi `nap` tra ve.
    """
    kg = ban.get("khung_goc")
    if kg not in PHUT_KHUNG or khung not in PHUT_KHUNG:
        return 0
    if PHUT_KHUNG[kg] > PHUT_KHUNG[khung]:
        return 0                      # min hon khung yeu cau - khong noi suy nguoc
    if kg == khung:
        return int(ban.get("so_dong") or 0)
    return int((ban.get("so_dong") or 0) * PHUT_KHUNG[kg] / PHUT_KHUNG[khung])


def ban_cho_khung(ma: str, khung: str) -> dict | None:
    """Ban du lieu NEN DUNG cho `(ma, khung)` - chon theo DO PHU, khong theo byte.

    Day la cho `kho()` chon nham suot tu dau du an: no giu MOT ban moi ma, ban
    to nhat theo byte. File phut luon to hon file ngay, nen moi yeu cau D1 deu
    di duong "gop file phut len ngay" va nhan doan lich su NGAN nhat co trong
    kho. Do 24/08 tren 11 ma:

        US500CASH     m30 -> D1  2.642 bar (2018+)   | ban D1 co 4.027 (2011+)
        XM_US500CASH  m5  -> D1    367 bar           | ban D1 co 4.028
        XM_US100CASH  m5  -> D1    367 bar           | ban D1 co 3.995
        8 cap FX      M1  -> D1  ~3.495 bar          | ban D1 co 6.672-8.612

    367 bar la duoi nguong 1.500 cua `nha_may_null.duong_cong_luc`, nen hai ma
    chi so cua XM khong he co mat trong bat ky vong quet D1 nao - va khong cho
    nao bao loi.

    Thu tu chon: (1) do phu o khung do; (2) trong pham vi 90% do phu tot nhat
    thi uu tien ban CO COT SPREAD (mat cot spread la tut do tin chi phi tu SAN
    xuong KHAI); (3) ban dung khung goc; (4) file to hon; (5) ten - de tat dinh.
    """
    goc = kho().get((ma or "").upper())
    if goc is None:
        return None
    cac = goc.get("cac_ban") or [goc]
    lop = goc.get("lop_nguon") or goc.get("nguon")
    ung = [b for b in cac
           if b["du_ohlc"] and b["nguon"] == lop and _uoc_bar_o_khung(b, khung) > 0]
    if not ung:
        return goc if goc.get("du_ohlc") else None
    tot_nhat = max(_uoc_bar_o_khung(b, khung) for b in ung)
    gan_nhat = [b for b in ung if _uoc_bar_o_khung(b, khung) >= 0.9 * tot_nhat]
    return max(gan_nhat, key=lambda b: (b.get("co_spread", False),
                                        b["khung_goc"] == khung,
                                        b["kich_thuoc"], b["file"].name))


#: Hau to thang giao hang cua HOP DONG TUONG LAI. Ba bang trong kho co dang
#: nay: XM_US500_SEP26, XM_US100_SEP26, XM_US30_SEP26.
#:
#: **CAM BACKTEST** (memory `xm-co-futures-cfd`): chuoi futures ma MT5 tra ve la
#: chuoi DA NOI - khi hop dong dao han, terminal noi hop dong ke tiep vao cung
#: mot bieu do, va buoc noi la mot buoc nhay gia KHONG GIAO DICH DUOC. Backtest
#: tren do sinh ra loi/lo tu nhung buoc nhay khong ai kiem hay mat duoc.
#: Da lot vao ro gop lop ngay 22/08 truoc khi bi bat.
import re as _re
_HAU_TO_FUTURES = _re.compile(
    r"_(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{2}$", _re.I)


def la_futures(ma: str) -> bool:
    """True neu ma la mot HOP DONG futures co thang giao hang."""
    return bool(_HAU_TO_FUTURES.search(ma or ""))


def bang_ohlc(toi_thieu_nam: float = 0.0, cho_futures: bool = False) -> dict[str, dict]:
    """Chi nhung bang backtest OHLC duoc, loc o muc schema.

    Loai hop dong futures tru khi goi ro rang `cho_futures=True` - xem
    `la_futures`. Loai o DAY chu khong o tung noi goi: bo loc dat o mot cho thi
    moi duong di deu duoc bao ve, dat o tung noi goi thi chi duong nao nho moi
    duoc.
    """
    return {m: v for m, v in kho().items()
            if v["du_ohlc"] and v["uoc_so_nam"] >= toi_thieu_nam
            and (cho_futures or not la_futures(m))}


def nguon_tai_san(ma: str) -> str:
    """`san` / `ngoai` cua mot ma da co trong kho."""
    return (kho().get(ma.upper()) or {}).get("nguon", "san")


def _chuan_hoa(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=str.lower)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
        df = df.dropna(subset=["time"]).set_index("time")
    elif not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
        df = df[df.index.notna()]
    can = [c for c in ("open", "high", "low", "close", "spread", "tick_volume") if c in df.columns]
    df = df[can].astype("float64", errors="ignore")
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def _gop(df: pd.DataFrame, khung: str) -> pd.DataFrame:
    """Gop len khung lon hon. spread lay TRUNG VI (duoi lech phai)."""
    quy = QUY_KHUNG[khung]
    ham = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "tick_volume" in df.columns:
        ham["tick_volume"] = "sum"
    ra = df.resample(quy, label="left", closed="left").agg(ham)
    if "spread" in df.columns:
        ra["spread"] = df["spread"].where(df["spread"] > 0).resample(
            quy, label="left", closed="left").median()
    return ra.dropna(subset=["open", "high", "low", "close"])


def khung_that(df: pd.DataFrame) -> float:
    """Khoang cach bar THAT (phut), do bang trung vi. Khong tin ten file.

    Day la cai bat bay so 32: MT5 don bar NGAY vao yeu cau khung M5 cho giai
    doan khong co du lieu phut, KHONG bao loi. Dau hieu duy nhat la so bar/nam.
    """
    if len(df) < 10:
        return float("nan")
    d = np.diff(df.index.to_numpy()).astype("timedelta64[s]").astype(float) / 60.0
    d = d[d > 0]
    return float(np.median(d)) if len(d) else float("nan")


def nap(ma: str, khung: str = "H1", tu: str | None = None, den: str | None = None,
        cache: bool = True) -> pd.DataFrame:
    """Nap bar cua `ma` o `khung`. Tu dong gop tu khung goc + cache ra parquet.

    TU CHOI khi khung yeu cau NHO HON khung that cua du lieu - noi suy nguoc
    la che ra bar khong ton tai.
    """
    ma = ma.upper()
    khung = khung.upper()
    if khung not in QUY_KHUNG:
        raise ValueError(f"khung khong ho tro: {khung}")
    ds = kho()
    if ma not in ds:
        raise FileNotFoundError(f"khong co du lieu cho {ma}. Co: {', '.join(sorted(ds))}")
    goc = ban_cho_khung(ma, khung) or ds[ma]
    CACHE.mkdir(parents=True, exist_ok=True)
    # Ten cache mang theo TEN FILE NGUON. Neu chi dat theo `{ma}_{khung}` thi
    # khi ban duoc chon doi (vi them file, vi sua luat chon) cache cu van "moi
    # hon file goc" va duoc dung tiep - tuc doi nguon xong van doc du lieu cu.
    f_cache = CACHE / f"{ma}_{khung}__{goc['file'].stem}.parquet"

    if cache and f_cache.exists() and f_cache.stat().st_mtime > goc["file"].stat().st_mtime:
        df = _chuan_hoa(pd.read_parquet(f_cache))
    else:
        tho = _chuan_hoa(pd.read_parquet(goc["file"]))
        phut_goc = khung_that(tho)
        if np.isfinite(phut_goc) and phut_goc > PHUT_KHUNG[khung] * 1.5:
            raise ValueError(
                f"{ma}: du lieu goc cach nhau ~{phut_goc:.0f} phut, khong the tao "
                f"khung {khung} ({PHUT_KHUNG[khung]} phut). Khong noi suy nguoc.")
        if np.isfinite(phut_goc) and phut_goc >= PHUT_KHUNG[khung] * 0.9:
            df = tho          # da dung khung, khong gop
        else:
            df = _gop(tho, khung)
        if cache:
            try:
                df.to_parquet(f_cache)
            except Exception:
                pass
    if tu:
        df = df[df.index >= pd.Timestamp(tu)]
    if den:
        df = df[df.index <= pd.Timestamp(den)]
    return df


# --------------------------------------------------------------- KIEM SUC KHOE
#: Ty le `open[i] == close[i-1]` toi da con chap nhan duoc.
#:
#: KHONG duoc dat thap. Do that tren kho nay:
#:   FX broker H1/H4      33-44%  <- BINH THUONG (thi truong lien tuc, nen ke
#:                                   tiep mo dung o gia dong nen truoc rat hay)
#:   FX broker D1         12%
#:   US500M CFD 24h D1    28%
#:   XAUUSDM              2,6%
#: va o phia BIA:
#:   YH_DAX D1            0,1%    <- san co phien, open that PHAI gap
#:   YH_NIKKEI D1         0,8%
#:   YH_FTSE100 D1        68%     <- BIA
#:   SP500 D1 nam 1967-99 93-97%  <- BIA theo mang
#:
#: Nguong 0,30 tung loai nham 18 chuoi FX/CFD hop le. 0,60 tach dung hai nhom.
#: Khe gia tai MOC DAO NGAY. Do 30/08/2026 tren FX H4 cua kho nay:
#:
#:      gio    khe(bps)   than(bps)
#:        0      -3,158      +5,784   <- EURGBP
#:        4      +0,009      +0,070
#:       20      +0,001      -2,080
#:
#: Bar 00:00 MO THAP gia tao roi "hoi" trong than bar. Moi gio khac khe ~0.
#: Cung hinh dang tren EURCAD (-2,47) va AUDCAD (-4,61). Do la bao gia luc dao
#: ngay - thanh khoan mong, chenh mua/ban gian rong.
#:
#: Ai om dung bar do thi MUA O GIA MO BIA va BAN O GIA DONG THAT: +5,78 bps
#: moi ngay ~ **14%/nam hien vat thuan**, lon hon moi edge that. Da lam mot
#: ung vien dat t_alpha = 14,52 va di het cong re.
#:
#: Hai nguong phai dat CUNG LUC:
#:  - san tuyet doi 1 bps: duoi muc do khe khong du de che ra edge, va moi
#:    chuoi that deu co khe nho khac 0.
#:  - gap 10 lan trung vi cac gio khac: tren mot chuoi sach thi moi gio deu
#:    nho nhu nhau, khong gio nao noi len.
#: Doi mot nguong thoi thi mot chuoi sach se bi bao dong gia (chi co san) hoac
#: mot chuoi ban se lot (chi co ty le).
KHE_GIO_SAN_BPS = 1.0
KHE_GIO_BOI = 10.0


def khe_gio_bat_thuong(df, san_bps: float = KHE_GIO_SAN_BPS,
                       boi: float = KHE_GIO_BOI) -> dict:
    """Gio nao co khe gia bat thuong giua bar truoc va bar nay?

    Tra `{"gio": [...], "khe_bps": {gio: bps}, "do_duoc": bool}`.

    `do_duoc=False` khi khong du bar de ket luan - va luc do `gio` la danh
    sach RONG vi "chua do duoc", khong phai vi "sach". Nguoi goi phai phan
    biet hai cau do.
    """
    import numpy as _np
    ra = {"gio": [], "khe_bps": {}, "do_duoc": False}
    try:
        o = _np.asarray(df["open"], dtype=float)
        c = _np.asarray(df["close"], dtype=float)
        gio = _np.asarray(df.index.hour)
    except Exception:
        return ra
    if len(o) < 200:
        return ra
    khe = _np.full(len(o), _np.nan)
    khe[1:] = o[1:] / c[:-1] - 1.0
    tb = {}
    for h in sorted(set(gio.tolist())):
        x = khe[gio == h]
        x = x[_np.isfinite(x)]
        if len(x) >= 30:
            tb[int(h)] = float(_np.mean(x) * 1e4)
    if len(tb) < 2:
        return ra
    ra["do_duoc"] = True
    ra["khe_bps"] = tb
    do_lon = sorted(abs(v) for v in tb.values())
    trung_vi = do_lon[len(do_lon) // 2]
    for h, v in tb.items():
        if abs(v) >= san_bps and abs(v) >= boi * max(trung_vi, 1e-9):
            ra["gio"].append(h)
    ra["gio"].sort()
    return ra


NGUONG_OPEN_BIA = 0.60

#: Nguong cho thi truong CO PHIEN DONG CUA (chi so, ETF - nguon `ngoai`).
#:
#: 0,60 la nguong cua thi truong LIEN TUC va dung o day thi qua long den muc vo
#: dung. Do that tren 33 chuoi chi so cua kho nay (nam sach / tong so nam):
#:      nguong 0,60   nguong 0,20
#:   YH_FTSE100   17/43        9/43   <- 8 nam bia van lot qua 0,60
#:   YH_RUSSELL   27/40       20/40
#:   YH_ASX200    23/35       18/35
#:   YH_BOVESPA   31/34        9/34
#: con cac chuoi SACH thi khong mat gi khi siet: DAX 39/39, NASDAQ 56/56,
#: NIKKEI 57/57, CAC40 37/37, KOSPI 31/31 o CA HAI nguong.
#:
#: Ly do co che: gia mo phien la ket qua cua phien khop lenh mo cua sau 17 gio
#: dong cua - no PHAI khac gia dong hom truoc. Bang nhau la loi ghi du lieu.
#: Voi bao gia lien tuc 24/5 thi bang nhau la chuyen thuong (nen ke tiep mo
#: dung o gia dong nen truoc khi khong co tick xen giua).
NGUONG_OPEN_BIA_PHIEN = 0.20


def nguong_open_bia(ma: str = "", co_phien: bool | None = None) -> float:
    """Nguong open bia dung cho `ma`. `co_phien=None` -> suy tu nguon du lieu."""
    if co_phien is None:
        co_phien = bool(ma) and nguon_tai_san(ma) == "ngoai"
    return NGUONG_OPEN_BIA_PHIEN if co_phien else NGUONG_OPEN_BIA


def _gom_doan(cac_nam: list[int]) -> list[tuple[int, int]]:
    """[1927,1928,1930] -> [(1927,1928),(1930,1930)]."""
    ra: list[tuple[int, int]] = []
    for n in sorted(cac_nam):
        if ra and n == ra[-1][1] + 1:
            ra[-1] = (ra[-1][0], n)
        else:
            ra.append((n, n))
    return ra


def doan_dai_nhat(cua_so: list[tuple[int, int]]) -> tuple[int, int] | None:
    """Doan lien tuc dai nhat trong danh sach cua so nam."""
    return max(cua_so, key=lambda d: d[1] - d[0], default=None) if cua_so else None


def cat_theo_chat_luong(df: pd.DataFrame, ma: str = "",
                       co_phien: bool | None = None) -> tuple:
    """Cat df ve doan co open THAT dai nhat. Tra (df_da_cat, bao_cao).

    Dung khi mot chuoi dai co mang bi nhiem: SP500 co 98,6 nam nhung open chi
    that o 1927-1959 va 2007-2026. Lay ca chuoi la backtest tren gia bia.
    """
    bc = kiem(df, ma, co_phien=co_phien)
    cua_so = bc.get("cua_so_open_that") or []
    doan = doan_dai_nhat(cua_so)
    if not doan:
        return df.iloc[0:0], bc
    tu, den = doan
    da_cat = df[(df.index.year >= tu) & (df.index.year <= den)]
    bc["da_cat_ve"] = (tu, den)
    bc["so_bar_sau_cat"] = int(len(da_cat))
    return da_cat, bc


def kiem(df: pd.DataFrame, ma: str = "", co_phien: bool | None = None) -> dict:
    """Kiem cac bay da biet TRUOC khi backtest. Tra bao cao + co `dung_duoc`.

    `co_phien`: thi truong co phien dong cua (chi so) hay bao gia lien tuc (FX/
    CFD). Quyet dinh nguong open bia. `None` -> suy tu nguon du lieu cua `ma`.
    """
    nguong = nguong_open_bia(ma, co_phien)
    bc: dict = {"ma": ma, "so_bar": int(len(df)), "canh_bao": [],
                "dung_duoc": True, "nguong_open_bia": nguong}
    if len(df) < 200:
        bc["canh_bao"].append(f"chi {len(df)} bar - qua ngan")
        bc["dung_duoc"] = False
        return bc
    bc["tu"] = str(df.index.min())
    bc["den"] = str(df.index.max())
    bc["so_nam"] = round((df.index.max() - df.index.min()).days / 365.25, 2)

    # BAY 0: thieu cot. Truoc day cho nay doc thang df["open"] nen mot bang chi
    # co cot `close` (ETF_SPY) hoac RONG hoan toan (VIX) lam ham nem KeyError
    # thay vi tra ve "khong dung duoc". Loi im la loi nguy nhat.
    thieu = [k for k in ("open", "high", "low", "close") if k not in df.columns]
    if thieu:
        bc["cot_thieu"] = thieu
        bc["canh_bao"].append(f"thieu cot {thieu} - khong backtest OHLC duoc")
        bc["dung_duoc"] = False
        return bc

    o, c = df["open"].to_numpy(), df["close"].to_numpy()
    # BAY 1: open bia (open[i] == close[i-1])
    if len(df) > 1:
        bia = np.isclose(o[1:], c[:-1], rtol=0, atol=1e-12)
        trung = float(np.mean(bia))
        bc["ty_le_open_bang_close_truoc"] = round(trung, 4)

        # Trung binh TOAN CHUOI giau mat mang bi nhiem. Do that:
        #   SP500  toan chuoi 39,9% -> "dat", nhung 1967-1999 la 93-97% bia
        #   FTSE100 toan chuoi 68,0% -> "dat", va 2016-2024 la 100% bia
        # Vi vay phai xet theo TUNG NAM va bao ra cua so con dung duoc.
        theo_nam = pd.Series(bia, index=df.index[1:]).groupby(
            df.index[1:].year).mean()
        nam_sach = [int(y) for y, v in theo_nam.items() if v <= nguong]
        bc["nam_open_that"] = nam_sach
        bc["cua_so_open_that"] = _gom_doan(nam_sach)
        bc["ty_le_nam_open_that"] = round(
            len(nam_sach) / max(len(theo_nam), 1), 4)

        if trung > nguong:
            bc["canh_bao"].append(
                f"open[i]==close[i-1] o {trung:.1%} bar - open la BIA o phan lon "
                "chuoi, quy tac vao lenh open[i+1] VO HIEU")
            bc["dung_duoc"] = False
        elif len(nam_sach) < len(theo_nam):
            ban = _gom_doan([int(y) for y, v in theo_nam.items()
                             if v > nguong])
            bc["canh_bao"].append(
                f"open BIA o cac nam {ban} - phai CAT bo truoc khi backtest, "
                f"chi dung {bc['cua_so_open_that']}")

    # BAY 2: rau nen hong
    lo, hi = df["low"].to_numpy(), df["high"].to_numpy()
    than_duoi = np.minimum(o, c)
    than_tren = np.maximum(o, c)
    hong = (lo < than_duoi * 0.90) | (hi > than_tren * 1.10)
    bc["so_bar_rau_hong"] = int(hong.sum())
    if hong.sum() > 0:
        bc["canh_bao"].append(f"{int(hong.sum())} bar co rau > 10% (kiem tay: "
                              "SNB 2015-01-15, Brexit 2016-06-24 la THAT, phai giu)")

    # BAY 3: spread
    if "spread" in df.columns:
        s = df["spread"].to_numpy(dtype=float)
        ty_le_0 = float(np.mean(~(s > 0)))
        bc["ty_le_spread_0"] = round(ty_le_0, 4)
        if ty_le_0 > 0.5:
            bc["canh_bao"].append(f"{ty_le_0:.0%} bar spread=0 - khung nay khong co "
                                  "spread that (bar D1 cua XM la vay)")
    else:
        bc["canh_bao"].append("khong co cot spread - chi phi se phai KHAI BAO")

    # BAY 4: lo hong du lieu
    if len(df) > 10:
        b = np.diff(df.index.to_numpy()).astype("timedelta64[m]").astype(float)
        dien_hinh = float(np.median(b))
        lo_hong = int(np.sum(b > max(dien_hinh * 50, 4 * 24 * 60)))
        bc["so_lo_hong_lon"] = lo_hong
        if lo_hong > 0:
            bc["canh_bao"].append(f"{lo_hong} lo hong > 4 ngay")

    # BAY 5: so bar/nam - phat hien MT5 don bar NGAY vao yeu cau khung nho
    nam = bc.get("so_nam") or 1
    bar_nam = len(df) / max(nam, 0.1)
    bc["bar_moi_nam"] = int(bar_nam)
    return bc


#: Cache do chat luong: nap lai 33 chuoi chi so moi lan xep hang la lang phi,
#: va ket qua chi doi khi FILE goc doi.
_CACHE_CHAT_LUONG = CACHE / "_chat_luong.json"


def _doc_cache_chat_luong() -> dict:
    try:
        import json
        return json.loads(_CACHE_CHAT_LUONG.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def nam_dung_duoc(ma: str, khung: str = "D1") -> dict:
    """So nam THAT SU dung duoc = doan lien tuc dai nhat co open THAT.

    Vi sao khong dung tong so nam: xep hang be mat kham pha theo do dai THO thi
    YH_FTSE100 (41,4 nam, 34/43 nam la gia bia) va SP500 (95,2 nam, 46/99 nam
    bia) day YH_DAX (37,6 nam, 39/39 nam sach) ra khoi danh sach. Do la xep
    hang theo do dai cua RAC.
    """
    ma = ma.upper()
    goc = kho().get(ma)
    if not goc:
        return {"ma": ma, "nam": 0.0, "loi": "khong co trong kho"}
    khoa = f"{ma}|{khung}"
    mtime = goc["file"].stat().st_mtime
    cache = _doc_cache_chat_luong()
    cu = cache.get(khoa)
    if cu and abs(float(cu.get("mtime", 0)) - mtime) < 1e-6:
        return cu
    ra = {"ma": ma, "khung": khung, "mtime": mtime, "nam": 0.0}
    try:
        df = nap(ma, khung)
        da_cat, bc = cat_theo_chat_luong(df, ma)
        ra["nam"] = round((da_cat.index.max() - da_cat.index.min()).days / 365.25, 2)             if len(da_cat) > 1 else 0.0
        ra["nam_tho"] = bc.get("so_nam")
        ra["so_bar"] = int(len(da_cat))
        ra["cua_so"] = list(bc.get("da_cat_ve") or ())
        ra["dung_duoc"] = bool(bc.get("dung_duoc"))
    except Exception as e:
        ra["loi"] = f"{type(e).__name__}: {str(e)[:80]}"
    cache[khoa] = ra
    try:
        import json
        CACHE.mkdir(parents=True, exist_ok=True)
        _CACHE_CHAT_LUONG.write_text(json.dumps(cache, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    except Exception:
        pass
    return ra


def hai_nua(df: pd.DataFrame, ty_le: float = 0.6) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chia train / holdout theo THOI GIAN.

    THIET_KE muc 3: tang sinh gia thuyet dung toan bo `train`; tang xac nhan
    dung phan CHUA TUNG dung de sinh gia thuyet. Khong uoc luong lai gi tren holdout.
    """
    n = int(len(df) * ty_le)
    return df.iloc[:n], df.iloc[n:]


if __name__ == "__main__":
    ds = kho()
    print(f"{len(ds)} tai san trong kho:\n")
    for ma, v in sorted(ds.items()):
        print(f"  {ma:<12} {v['khung_goc']:<3} {v['kich_thuoc']/1e6:7.1f} MB  {v['file'].name}")
    if ds:
        ma = "EURCAD" if "EURCAD" in ds else sorted(ds)[0]
        print(f"\nthu nap {ma} H1 ...")
        df = nap(ma, "H1")
        import json
        print(json.dumps(kiem(df, ma), ensure_ascii=False, indent=1))


def chuan_hoa_index(index):
    """Dua mot DatetimeIndex ve dang KHONG timezone de ghep duoc voi bang khac.

    Kho hien co 14 bang tz-naive (nguon broker, tu 2013) va 6 bang tz=UTC
    (nguon dai han/MT5). `pd.concat` hai loai nay nem thang:
        TypeError: Cannot join tz-naive with tz-aware DatetimeIndex

    Da kiem truoc khi chuan hoa: CA HAI nhom nam tren cung luoi gio H4
    [0, 4, 8, 12, 16, 20], nen bo timezone khong lam lech hang gia. Khac biet
    duy nhat la nhom UTC co them nen Chu nhat (phien mo cua MT5).

    KHONG duoc dung ham nay neu hai nguon nam tren luoi gio KHAC nhau - luc do
    phai quy doi that, khong phai go nhan.
    """
    if getattr(index, "tz", None) is not None:
        return index.tz_convert("UTC").tz_localize(None)
    return index


def cung_luoi_gio(cac_index) -> bool:
    """True neu moi index deu roi vao cung mot tap gio trong ngay."""
    tap = [frozenset(chuan_hoa_index(i).hour) for i in cac_index if len(i)]
    return len(set(tap)) <= 1
