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

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
GOC = LAB.parent
# DATA / CACHE doi cho duoc - `nhan/duong_dan.py` la MOT cho duy nhat quyet
# dinh. 12/09/2026: o C day 100% va moi khau ghi that bai AM (SQLite nem
# "disk is full", ham boc tra ve rong, hang doi thay rc=0 nen bao "XONG").
# `data_khung` la CACHE (tai tao duoc tu `data/`) nen day sang o F truoc tien.
from nhan import duong_dan as _DD          # noqa: E402
DATA = _DD.kho_gia()
CACHE = _DD.cache_khung()

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

    # ANH CHUP (khoi 3, 11/09/2026). Phep chon o tren la "ban .parquet TO NHAT
    # thang", nen chi can them mot file vao `data/` la ban duoc chon cua ca mot
    # ma doi - khong mot loi canh bao nao. Voi mot he lay holdout lam trong tai,
    # dieu do nghia la ket qua cu khong tai lap duoc.
    #
    # O day chi TON TRONG ghim, KHONG nem loi: nem loi trong `kho()` se lam sap
    # moi duong chay chi vi mot file phu bi sua. Viec keu len la cua
    # `anh_chup.kiem()`, va no chan o cho cham holdout.
    try:
        from . import anh_chup as AC
        for ma, g in AC.ghim_theo_ma().items():
            goc = ra.get(ma)
            if not goc:
                continue
            for b in goc.get("cac_ban", []):
                if str(b["file"]) == g["file"]:
                    b_ghim = dict(b)
                    b_ghim["cac_ban"] = goc["cac_ban"]
                    b_ghim["lop_nguon"] = goc["lop_nguon"]
                    b_ghim["khung_min"] = goc["khung_min"]
                    b_ghim["uoc_so_nam"] = goc["uoc_so_nam"]
                    b_ghim["da_ghim"] = True
                    ra[ma] = b_ghim
                    break
    except Exception:
        pass  # so anh chup hong KHONG duoc chan viec nap du lieu

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


# ------------------------------------------------- DOAN DAU DO PHAN GIAI THAP
#: Ty le bar/ngay toi thieu (so voi ky vong cua khung) de mot NAM duoc coi la
#: co du lieu THAT o khung do.
#:
#: VI SAO CAN (do that 01/09/2026, khi hieu chuan cong bang V6). `khung_that()`
#: lay TRUNG VI khoang cach bar tren CA chuoi, nen mot chuoi lai tap - vai nam
#: dau la bar NGAY duoc terminal don vao, phan con lai la bar gio that - van
#: qua duoc cua: trung vi cua 61.030 bar US500CASH la 60 phut trong khi
#: 1.299 bar dau (2011-2015) moi bar la MOT NGAY.
#:
#: Do tren ca kho: 5 ma dinh, va khong phai ma le nao ca -
#:   EURUSD  H1/H4  1971-1998  (28 nam bar ngay deo nhan bar gio)
#:   USDJPY  H1/H4  1971-1998  (28 nam)
#:   GBPUSD  H1/H4  1993-1998  (6 nam)
#:   US500CASH H1/H4 2011-2015 (5 nam)
#:   XAUUSDM H1/H4  2014-2016  (3 nam)
#: Ba trong so do la cap FX duoc quet nhieu nhat cua du an.
#:
#: Vi sao no lam hong ket qua chu khong chi lam ban: mot bar NGAY deo nhan H1
#: co bien do ca ngay. Moi chi bao dua tren bien do bar (IBS, ATR, Donchian,
#: Bollinger) doc doan do nhu mot gio bien dong gap ~5 lan binh thuong, va moi
#: quy tac "giu N bar" giu sai don vi thoi gian 24 lan.
TY_LE_BAR_TOI_THIEU = 0.35

#: Ghi nhan cac lan cat, de `chan_doan_do_phan_giai()` bao cao duoc
#: ngay ca khi `nap()` tra ket qua tu cache.
_CAT_DOAN: dict[tuple, dict] = {}


def _bar_moi_ngay(index: pd.DatetimeIndex) -> "pd.Series":
    """So bar trung binh moi NGAY CO GIAO DICH, theo tung nam."""
    ngay = pd.Series(index.normalize())
    nam = pd.Series(index.year)
    so_bar = nam.groupby(nam).size()
    so_ngay = ngay.groupby(nam.to_numpy()).nunique()
    return (so_bar / so_ngay).dropna()


def doan_do_phan_giai_that(df: pd.DataFrame, khung: str) -> pd.Timestamp | None:
    """Moc dau tien ma `df` thuc su co do phan giai `khung`.

    Tra None khi ca chuoi da dung do phan giai (khong phai cat gi).

    Chi cat o DAU chuoi: mot nam thua o giua (san dong cua, du lieu ro) la van
    de KHAC va khong duoc lang le vut bo bang cung mot luat.
    """
    if khung not in PHUT_KHUNG or khung in ("D1", "W1") or len(df) < 50:
        return None
    ky_vong = 1440.0 / PHUT_KHUNG[khung]
    bpd = _bar_moi_ngay(df.index)
    if bpd.empty:
        return None
    dat = bpd >= ky_vong * TY_LE_BAR_TOI_THIEU
    if dat.all() or not dat.any():
        return None
    nam_dau = int(dat.idxmax())               # nam DAT dau tien
    if bpd.index.min() >= nam_dau:
        return None
    # Kho co ca bang tz-naive lan tz=UTC; moc phai mang dung mui cua chinh
    # chuoi, neu khong pandas nem TypeError thay vi so sanh.
    return pd.Timestamp(year=nam_dau, month=1, day=1, tz=getattr(df.index, "tz", None))


def cat_doan_tho(df: pd.DataFrame, khung: str) -> tuple[pd.DataFrame, dict | None]:
    """Cat doan dau co do phan giai tho hon `khung`. Tra (df, ghi_chu|None)."""
    moc = doan_do_phan_giai_that(df, khung)
    if moc is None:
        return df, None
    truoc = len(df)
    ra = df[df.index >= moc]
    return ra, {"cat_tu": str(df.index.min().date()), "den": str(moc.date()),
                "bo_bar": truoc - len(ra), "con_bar": len(ra), "khung": khung}


def _ghi_cache(df: pd.DataFrame, dich: Path) -> None:
    """Ghi cache mot cach KHONG BAO GIO de lai file dang do.

    `to_parquet` thang vao `dich` khong phai mot buoc: mot tien trinh khac doc
    dung luc do se thay file 0 byte va nem ArrowInvalid. Do that 01/09/2026 -
    lan dau chay `b test` (8 tien trinh) sau khi doi ten cache, ca 8 cung tao
    mot file va bo test do mot loi khong lien quan gi den thu dang duoc test.

    Ghi ra ten tam mang PID roi doi ten. Tren Windows `os.replace` NEM khi dich
    dang duoc tien trinh khac mo (bai hoc `24-7-chet-vi-lease-windows`), nen
    that bai o buoc doi ten chi co nghia "ai do vua ghi xong ban cua ho" - don
    file tam va di tiep, khong nem len tren.
    """
    tam = dich.with_suffix(f".{os.getpid()}.tmp")
    try:
        df.to_parquet(tam)
        os.replace(tam, dich)
    except Exception:
        try:
            tam.unlink(missing_ok=True)
        except Exception:
            pass


def nap(ma: str, khung: str = "H1", tu: str | None = None, den: str | None = None,
        cache: bool = True, sua_bar: bool = True) -> pd.DataFrame:
    """Nap bar cua `ma` o `khung`. Tu dong gop tu khung goc + cache ra parquet.

    TU CHOI khi khung yeu cau NHO HON khung that cua du lieu - noi suy nguoc
    la che ra bar khong ton tai.

    `sua_bar=True` (mac dinh tu 12/09/2026): chay `sua_bar_hong` - kep `open` ve
    trong bien do bar va bo bar lech dau thap phan. Dat `False` khi muon DO
    chinh do hong (vi do qua `nap()` da sua thi bao cao se rong, va ta se ket
    luan "khong co van de" tu chinh cai vua sua).
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
    # `v2` trong ten: doi 01/09/2026 khi them `cat_doan_tho`. Khong bump thi
    # cache cu (van moi hon file goc) tiep tuc duoc dung va ban va KHONG BAO GI -
    # tuc ban sua xong ma so khong doi, va ban se tin la "khong anh huong".
    f_cache = CACHE / f"{ma}_{khung}__{goc['file'].stem}__v2.parquet"

    df = None
    if cache and f_cache.exists() and f_cache.stat().st_mtime > goc["file"].stat().st_mtime:
        # Doc co the hong khi mot tien trinh KHAC dang ghi do cache: `b test`
        # chay 8 tien trinh va lan dau sau khi bump ten cache, ca 8 cung dung
        # mot ten file. Cache la thu TANG TOC, hong thi dung lai tu file goc -
        # KHONG duoc de mot phep toi uu lam do vo ca bo test.
        try:
            df = _chuan_hoa(pd.read_parquet(f_cache))
        except Exception:
            df = None
    if df is None:
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
        # Doan dau do phan giai tho (bar NGAY deo nhan bar gio) phai bi cat SAU
        # khi gop: gop khong tao them bar, no chi giu nguyen bar ngay do.
        df, _ghi_chu = cat_doan_tho(df, khung)
        if _ghi_chu:
            _CAT_DOAN[(ma, khung)] = _ghi_chu
        if cache:
            _ghi_cache(df, f_cache)
    if sua_bar:
        df, _sua = sua_bar_hong(df)
        if _sua:
            _DA_SUA[(ma, khung)] = _sua
    if tu:
        df = df[df.index >= pd.Timestamp(tu)]
    if den:
        df = df[df.index <= pd.Timestamp(den)]
    return df


#: (ma, khung) -> bao cao nhung gi `sua_bar_hong` da sua o lan nap gan nhat.
#: De doc duoc khi can, khong de am tham.
_DA_SUA: dict[tuple, dict] = {}


#: Nguong cua CONG DO. Chat hon nguong sua that (0,35) de cong luon nghieng ve
#: phia CHO CHAY - mot lan chay thua ton vai giay, mot lan chan oan lam lot mot
#: bar hong x10 vao backtest.
NGUONG_DO_LECH_BAC = 0.30


def _co_bar_lech_bac(d: dict, n: int) -> bool:
    """Co bar nao dang nghi lech MOT BAC 10 so voi neo truot khong.

    ## Vi sao co ham nay

    Do 15/09/2026 tren EURUSD H1 (171.113 bar):

        nap KHONG sua bar     0,63 s
        rieng `sua_bar_hong`  8,12 s   <- va bao cao sua la {} : KHONG sua gi ca
        nap CO sua bar        8,13 s

    Vong tuan tu ben duoi chay Python thuan tren `n x 4` o, moi o goi
    `np.log10` va moi bar goi `np.median` - 700.000 vong cho mot chuoi khong co
    mot bar hong nao. Va `nap()` chay no SAU cache, nen cache parquet khong cuu
    duoc gi: moi lan goi deu tra gia lai tu dau.

    Hau qua o duong chay that: `ngoai_sinh.chuyen` goi `nap` mot lan cho MOI
    ung vien lan can, nen mot bai test cua no chay **hon 30 phut CPU** va lam
    ca me 10 cua `chay_test_tung_me` qua gio 1800s. Khong ai doc duoc ket qua
    cua me do trong nhieu ngay.

    ## Vi sao cong nay dung

    Neo cua vong tuan tu chi doi khi co bar DUOC SUA. Neu khong bar nao dang
    nghi thi khong bar nao duoc sua, va luc do neo truot bang dung
    `ewm(alpha=0,05)` tren trung vi OHLC tung bar - tinh duoc mot lan bang C.

    Neo cho bar `i` la neo TRUOC khi cap nhat bang bar `i`, nen chuoi ewm phai
    duoc gieo bang `moc` ban dau roi dich mot bar - y het vong lap.

    Nguong 0,30 (so voi 0,35 cua phep sua that) de cong nghieng ve phia cho
    chay. Chan oan mot chuoi co bar hong dat hon nhieu so voi chay thua.
    """
    cot = ("open", "high", "low", "close")
    m = np.vstack([d[k] for k in cot]).astype(float)
    m[~np.isfinite(m) | (m <= 0)] = np.nan
    hop_le = np.isfinite(d["low"]) & (d["low"] > 0)
    if hop_le.sum() < 5 or n < 1:
        return True                      # khong do duoc thi CHO CHAY
    moc0 = float(np.median(np.concatenate([d[k][hop_le][:21] for k in cot])))
    if not np.isfinite(moc0) or moc0 <= 0:
        return True
    with np.errstate(invalid="ignore"):
        giua = np.nanmedian(m, axis=0)   # trung vi OHLC tung bar
    # Neo tai bar i = ewm cua cac bar TRUOC do, gieo bang `moc0`.
    chuoi = pd.Series(np.concatenate([[moc0], giua[:-1]]))
    neo = chuoi.ffill().ewm(alpha=0.05, adjust=False).mean().to_numpy(
        float, copy=True)
    neo[~np.isfinite(neo) | (neo <= 0)] = moc0
    with np.errstate(invalid="ignore", divide="ignore"):
        lech = np.abs(np.log10(m / neo[None, :]))
    return bool(np.nanmax(lech) >= NGUONG_DO_LECH_BAC) if np.isfinite(
        np.nanmax(lech)) else True


def sua_bar_hong(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Sua bar KHONG THE TON TAI. Tra (df, bao cao nhung gi da sua).

    ## CAI DA TIM RA 12/09/2026

    Truy mot ket qua vo ly (GBPZAR "591%/nam" dung dau bang xep hang quan tri)
    ra day. Tren GBPZAR doan 09/2023 - 01/2024:

        ngay          open      high       low     close
        2023-09-20  23.2418  233.2900   23.0767   23.2998      <- high x10
        2023-09-25 228.8610  231.9860   22.8440   23.1779      <- open x10 NUA
        2023-11-05 225.7250  226.5070   22.5124   22.5723

    **Ca cot `high` bi nhan 10 tren toan doan**, va rai rac `open` cung vay.
    Hau qua: duong von mua-giu vot len 9,19 lan roi ve 0,787, sut giam bao ra
    -91,67%, trong khi gia that chi di tu 19,62 den 22,32 suot 11 nam.

    Bay "rau nen hong" (`kiem` BAY 2) DA BAO 154 bar tren ma nay. Khong ai doc.
    Do la ho benh `noi-day-truoc-khi-xay-them`: bo do da co, chi la khong noi
    vao duong chay.

    ## BA PHEP SUA, THEO THU TU

    1. **Khoi phuc thang thap phan**: gia tri lech body dung mot luy thua cua 10
       thi chia/nhan lai. Day la phep sua DUNG - no tra lai gia that, khong doan.
    2. **Kep ve bien**: `open`/`close` nam ngoai [low, high] sau buoc 1 thi kep
       vao. `open` la gia da khop nen phai nam trong bien do bar; nam ngoai thi
       lenh vao o `open[i+1]` khop o mot muc chua tung ton tai.
    3. **Bo bar** con lai khong cuu duoc bang hai buoc tren.

    KHONG dung o day: cat chuoi ve doan open THAT - do van la `cat_theo_chat_luong`.
    """
    if not all(k in df.columns for k in ("open", "high", "low", "close")):
        return df, {}
    bc: dict = {}
    d = {k: df[k].to_numpy(dtype=float).copy() for k in ("open", "high", "low", "close")}
    n = len(df)
    if n < 3:
        return df, {}

    # --- 1) KHOI PHUC THANG THAP PHAN
    # Neo = trung vi cua ba cot con lai tren CUNG bar. Dung neo cung bar chu
    # khong dung bar ben canh: doan hong o day dai lien tuc hang thang, neo
    # theo hang xom se keo theo chinh cai hong.
    da_sua = {}
    for ten in ("open", "high", "low", "close"):
        khac = [d[k] for k in ("open", "high", "low", "close") if k != ten]
        neo = np.median(np.vstack(khac), axis=0)
        tot = neo > 0
        ty = np.ones(n)
        ty[tot] = d[ten][tot] / neo[tot]
        for he in (10.0, 100.0, 0.1, 0.01):
            k = tot & (np.abs(ty / he - 1.0) < 0.25)
            if k.any():
                d[ten][k] = d[ten][k] / he
                da_sua[ten] = da_sua.get(ten, 0) + int(k.sum())
    if da_sua:
        bc["khoi_phuc_thang_x10"] = da_sua

    # --- 1b) NEO TRUOT THEO THOI GIAN
    #
    # Buoc 1 neo vao BA COT CON LAI CUNG BAR, nen no mu khi >=2 cot cung lech.
    # Do la truong hop cua EURMXN (tim ra 12/09/2026, sau khi 120/120 dong dau
    # bang pheu deu la EURMXN voi "CAGR 942%/nam" tren mot ma di ngang 9 nam):
    #
    #     2023-06-26   open 186.86   high 187.57   low 18.65   close 187.24
    #
    # Ba cot x10, mot cot dung -> trung vi ba cot con lai cung x10 -> ty le 1,0
    # -> khong sua gi. 26 bar nhu vay du de sinh ra loi suat gia 2,32 (log).
    #
    # Neo thu hai: GIA THAM CHIEU TRUOT, cap nhat tu chinh cac bar DA SUA. Gia
    # khong nhay 10 lan trong mot bar, nen bat ky cot nao lech dung mot luy
    # thua cua 10 so voi neo deu la loi thang do - khong phai bien dong.
    # Neo trai theo gia that nen tai san tang truong that khong bi dung cham.
    hop_le = np.isfinite(d["low"]) & (d["low"] > 0)
    if hop_le.sum() >= 5 and _co_bar_lech_bac(d, n):
        moc = np.median(np.concatenate([d[k][hop_le][:21]
                                        for k in ("open", "high", "low", "close")]))
        sua_truot = {}
        for i in range(n):
            for ten in ("open", "high", "low", "close"):
                v = d[ten][i]
                if not np.isfinite(v) or v <= 0 or moc <= 0:
                    continue
                # luy thua cua 10 dua `v` ve gan `moc` nhat
                mu = int(round(np.log10(moc / v)))
                if mu and abs(np.log10((v * 10.0 ** mu) / moc)) < 0.35 <= abs(
                        np.log10(v / moc)):
                    d[ten][i] = v * 10.0 ** mu
                    sua_truot[ten] = sua_truot.get(ten, 0) + 1
            gt = [d[k][i] for k in ("open", "high", "low", "close")
                  if np.isfinite(d[k][i]) and d[k][i] > 0]
            if gt:
                # neo di chuyen cham (1/20) - mot bar hong con sot lai khong
                # duoc phep keo neo di theo no.
                moc = 0.95 * moc + 0.05 * float(np.median(gt))
        if sua_truot:
            bc["neo_truot_x10"] = sua_truot

    # --- 2) KEP VE BIEN
    hi = np.maximum.reduce([d["high"], d["open"], d["close"]])
    lo = np.minimum.reduce([d["low"], d["open"], d["close"]])
    kep = int(np.sum((d["open"] > d["high"]) | (d["open"] < d["low"])
                     | (d["close"] > d["high"]) | (d["close"] < d["low"])))
    if kep:
        bc["kep_ve_bien"] = kep
    d["high"], d["low"] = hi, lo

    # --- 3) BO BAR CON LAI KHONG CUU DUOC
    body_tren = np.maximum(d["open"], d["close"])
    body_duoi = np.minimum(d["open"], d["close"])
    xau = (~np.isfinite(body_tren) | (body_duoi <= 0)
           | (d["high"] > body_tren * 3.0) | (d["low"] < body_duoi / 3.0))
    if xau.any():
        bc["bo_bar_khong_cuu_duoc"] = int(xau.sum())

    moi = df.copy()
    for k in ("open", "high", "low", "close"):
        moi[k] = d[k]
    if xau.any():
        moi = moi[~xau]
    return moi, bc


def chan_doan_do_phan_giai(cac_khung=("H1", "H4"), cac_ma=None) -> list[dict]:
    """Quet kho: bang nao co doan dau do phan giai tho hon ten khung cua no.

    Doc TRUC TIEP file goc, khong qua `nap()` - vi `nap()` da cat roi thi bao
    cao se rong va ta se ket luan "khong co van de" tu chinh cai da sua.
    """
    ds = kho()
    ra = []
    for ma in (cac_ma or sorted(ds)):
        for khung in cac_khung:
            ban = ban_cho_khung(ma, khung)
            if not ban:
                continue
            try:
                tho = _chuan_hoa(pd.read_parquet(ban["file"]))
            except Exception:
                continue
            if len(tho) < 200:
                continue
            df = tho if khung_that(tho) >= PHUT_KHUNG[khung] * 0.9 else _gop(tho, khung)
            _, ghi_chu = cat_doan_tho(df, khung)
            if ghi_chu:
                ra.append({"ma": ma, "file": ban["file"].name, **ghi_chu})
    return ra


# ------------------------------------------------------------- BAR THEO PHIEN
#: Cua so phien giao dich noi dia, theo gio DIA PHUONG cua san giao dich do.
#: Dung ten mui gio (khong dung do lech cung) de DST tu dong dung: phien My
#: la 13:30-20:00 UTC vao mua he va 14:30-21:00 UTC vao mua dong - mot con so
#: UTC cung se sai mot tieng trong nua nam.
PHIEN = {
    "my": {"mui": "America/New_York", "mo": (9, 30), "dong": (16, 0)},
    "au": {"mui": "Europe/London", "mo": (8, 0), "dong": (16, 30)},
    "nhat": {"mui": "Asia/Tokyo", "mo": (9, 0), "dong": (15, 0)},
}
#: Ty le bar toi thieu so voi mot phien day du de giu lai ngay do. Nua phien
#: (truoc Le Ta on) la that va nen giu; mot ngay chi co 2 bar thi bien do cua
#: no khong phai bien do phien.
TY_LE_BAR_PHIEN_TOI_THIEU = 0.5


def nap_phien(ma: str, phien: str = "my", khung: str = "M30",
              toi_thieu_ty_le: float = TY_LE_BAR_PHIEN_TOI_THIEU
              ) -> tuple[pd.DataFrame, dict]:
    """Bar NGAY dung nghia mot PHIEN GIAO DICH, gop tu bar trong ngay.

    VI SAO CAN (van de `hieu_chuan_v6`, mo tu 15/08/2026). V6 duoc dung tren
    `sp500_daily` - bar cua PHIEN TIEN MAT 09:30-16:00 gio New York. Trong lab,
    cung ma do la mot CFD chi so chay gan 23 gio, nen bar D1 cua no om ca phien
    A va phien Au. `ibs` = vi tri gia dong cua TRONG BIEN DO BAR, nen hai bar
    do khong cung mot dai luong: bien do 23 gio rong hon han bien do 6,5 gio va
    gia dong cua phien My nam o cho khac trong do.
    
    Do that tren US500CASH 2018-2026: bien do bar D1 CFD rong hon bien do phien
    tien mat, va IBS tinh tren hai bar do chi tuong quan mot phan. Vi vay
    "V6 tren D1 cua CFD" KHONG phai V6 - va do la dieu bai thu 15/08 chua biet.

    Tra `(df, ghi_chu)`. `ghi_chu` noi ro cua so phien, khung nguon, so ngay bi
    bo va - quan trong nhat - `xap_xi` khi khung nguon khong chia dung moc mo
    cua (H1 khong the bat dau luc 09:30).

    Index tra ve la NGAY phien (naive, da chuan hoa) de gong duoc voi lop vi mo
    va voi cac bang D1 khac.
    """
    df = nap(ma, khung)
    if df.empty:
        return df, {"loi": "khong co du lieu"}
    return gop_theo_phien(df, phien, khung, toi_thieu_ty_le)


def gop_theo_phien(df: pd.DataFrame, phien: str = "my", khung: str = "M30",
                   toi_thieu_ty_le: float = TY_LE_BAR_PHIEN_TOI_THIEU
                   ) -> tuple[pd.DataFrame, dict]:
    """Phan THUAN TINH TOAN cua `nap_phien`: gop bar trong ngay thanh bar phien.

    Tach ra de bo test khoa duoc LUAT ma khong phu thuoc kho du lieu that -
    kho co the doi, luat thi khong duoc doi lang le.
    """
    if phien not in PHIEN:
        raise ValueError(f"phien khong biet: {phien}. Co: {', '.join(PHIEN)}")
    ph = PHIEN[phien]
    if df.empty:
        return df, {"loi": "khong co du lieu"}

    idx = pd.DatetimeIndex(df.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    dia_phuong = idx.tz_convert(ph["mui"])

    phut = dia_phuong.hour * 60 + dia_phuong.minute
    mo = ph["mo"][0] * 60 + ph["mo"][1]
    dong = ph["dong"][0] * 60 + ph["dong"][1]
    # Bar duoc dan nhan o DAU bar: bar bat dau tu `mo` va ket thuc truoc `dong`.
    xap_xi = (mo % PHUT_KHUNG[khung]) != 0
    neo = mo - (mo % PHUT_KHUNG[khung]) if xap_xi else mo
    giu = (phut >= neo) & (phut < dong)

    trong = df[giu].copy()
    if trong.empty:
        return trong, {"loi": "khong bar nao roi vao cua so phien"}
    ngay = pd.DatetimeIndex(dia_phuong[giu]).normalize().tz_localize(None)

    ham = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "tick_volume" in trong.columns:
        ham["tick_volume"] = "sum"
    gom = trong.groupby(ngay)
    ra = gom.agg(ham)
    if "spread" in trong.columns:
        ra["spread"] = trong["spread"].where(trong["spread"] > 0).groupby(ngay).median()
    dem = gom.size()

    day_du = int((dong - neo) / PHUT_KHUNG[khung])
    du_bar = dem >= max(1, int(day_du * toi_thieu_ty_le))
    ra = ra[du_bar.to_numpy()]
    ra.index.name = None

    return ra, {"phien": phien, "mui": ph["mui"], "khung_nguon": khung,
                "cua_so": f"{ph['mo'][0]:02d}:{ph['mo'][1]:02d}-{ph['dong'][0]:02d}:{ph['dong'][1]:02d}",
                "bar_mot_phien": day_du, "xap_xi_moc_mo": bool(xap_xi),
                "ngay_giu": int(len(ra)), "ngay_bo_thieu_bar": int((~du_bar).sum()),
                "tu": str(ra.index.min().date()) if len(ra) else None,
                "den": str(ra.index.max().date()) if len(ra) else None}

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
    """O thoi gian nao co khe gia bat thuong giua bar truoc va bar nay?

    Tra `{"gio": [...], "khe_bps": {o: bps}, "theo": "gio"|"thu", "do_duoc": bool}`.

    `do_duoc=False` khi khong du bar de ket luan - va luc do `gio` la danh
    sach RONG vi "chua do duoc", khong phai vi "sach". Nguoi goi phai phan
    biet hai cau do.

    KHUNG NGAY (sua 31/08/2026). Ban dau ham chi biet nhom theo GIO, nen tren
    D1 no thay dung mot gio va tra `do_duoc=False`: **moi ung vien D1 di qua
    cong 11 ma khong bi kiem hien vat nao**, va cong chi ghi mot dong "chua do
    duoc" ma khong ai doc. Tren khung ngay o thoi gian tuong duong la THU
    TRONG TUAN: khe cuoi tuan (thu 2) va khe nghi le nam dung o do, va no la
    cung mot co che - bao gia luc thi truong dong roi mo lai. Vi vay khi chuoi
    chi co mot gio thi tu chuyen sang nhom theo thu, va `theo` noi ro dang do
    theo cai nao. Khoa `gio` giu nguyen ten de duong goi cu khong vo.
    """
    import numpy as _np
    ra = {"gio": [], "khe_bps": {}, "theo": "gio", "do_duoc": False}
    try:
        o = _np.asarray(df["open"], dtype=float)
        c = _np.asarray(df["close"], dtype=float)
        gio = _np.asarray(df.index.hour)
        if len(set(gio.tolist())) < 2:
            gio = _np.asarray(df.index.dayofweek)
            ra["theo"] = "thu"
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


def _giao_cua_so(a: list, b: list) -> list:
    """Giao cua hai danh sach doan nam [(tu, den), ...]. `b` rong = khong rang buoc."""
    if not b:
        return list(a)
    if not a:
        return []
    ra = []
    for t1, d1 in a:
        for t2, d2 in b:
            t, d = max(t1, t2), min(d1, d2)
            if t <= d:
                ra.append((t, d))
    return sorted(ra)


def cat_theo_chat_luong(df: pd.DataFrame, ma: str = "",
                       co_phien: bool | None = None) -> tuple:
    """Cat df ve doan co open THAT **va** rau nen THAT dai nhat.

    Dung khi mot chuoi dai co mang bi nhiem: SP500 co 98,6 nam nhung open chi
    that o 1927-1959 va 2007-2026. Lay ca chuoi la backtest tren gia bia.

    ## HAI TIEU CHI, VA CHUNG CHI VAO HAI GIAI DOAN NGUOC NHAU (do 12/09/2026)

    Truoc hom nay ham nay chi xet mot tieu chi: `open` co that khong. No cat
    SP500 ve cua so **(1928, 1961)** - va cua so do la **100% BAR KHONG RAU**
    (`high` = than tren, `low` = than duoi). Tuc bo du lieu "da lam sach" ma
    `do_luc` va `gop_lop` dung suot la mot doan ma high/low duoc CHE ra tu
    open/close. Moi ATR, moi phep cham SL/TP, moi IBS tren do la hu cau.

        SP500  24.754 bar (35,5% khong rau)  --cat theo open-->  8.508 bar (100%)

    Ly do: `open` bia va `rau` bia la hai TAT KHAC NHAU cua hai thoi ky khac
    nhau, va toi da gia dinh chung di cung nhau.

    Nen gio cat theo GIAO cua hai cua so. Chuoi nao khong con doan nao thoa ca
    hai thi tra ve rong - do la cau tra loi dung: chuoi do khong backtest duoc
    theo kieu co cham high/low.
    """
    bc = kiem(df, ma, co_phien=co_phien)
    cua_so = _giao_cua_so(bc.get("cua_so_open_that") or [],
                          bc.get("cua_so_rau_that") or [])
    bc["cua_so_dung_duoc"] = cua_so
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

    # BAY 4: OPEN NAM NGOAI HIGH/LOW CUA CHINH BAR DO.
    #
    # Mot bar nhu vay khong ton tai duoc: `open` la mot gia da khop trong bar,
    # nen no phai nam trong [low, high]. Do la du lieu hong, khong phai bien dong.
    #
    # VI SAO NGUY: quy tac vao lenh cua du an la `open[i+1]` (CLAUDE.md muc 1).
    # Mot open nam ngoai bien do cho phep he "khop" o mot muc gia chua tung ton
    # tai - va no khong bao loi, chi lam ket qua dep hoac xau len mot chut.
    # Do 12/09/2026: 192 bar tren 12 ma Yahoo (YH_VANG 56, YH_USDJPY 37).
    ngoai = (o > hi * (1 + 1e-4)) | (o < lo * (1 - 1e-4))
    bc["so_bar_open_ngoai_bien"] = int(ngoai.sum())
    if ngoai.sum() > 0:
        bc["canh_bao"].append(
            f"{int(ngoai.sum())} bar co open NAM NGOAI high/low cua chinh no - "
            "bar khong ton tai duoc; vao lenh o open[i+1] se khop gia khong that")

    # BAY 5: LECH DAU THAP PHAN (nhay dung ~10 lan roi tra lai).
    #
    # Do 12/09/2026 tren GBPZAR: 16 bar co |log(o[i+1]/o[i])| = 2,3085 ~ log(10).
    # Gia that di tu 19,6 den 22,3 trong 11 nam, nhung duong von mua-giu vot len
    # **9,19 lan** roi ve 0,787 - va sut giam bao ra la -91,67%. Toan bo bang xep
    # hang quan tri hom do co GBPZAR dung dau voi "591%/nam".
    #
    # Phan biet voi bien dong that: mot cap FX D1 khong the nhay 3 lan trong mot
    # bar. Ke ca SNB 2015 (CHF) cung chi ~30%.
    NHAY = np.log(3.0)
    lech = {}
    for ten in ("open", "close"):
        v = df[ten].to_numpy(dtype=float)
        if not np.all(v > 0) or len(v) < 2:
            continue
        rr = np.abs(np.diff(np.log(v)))
        n = int(np.sum(rr > NHAY))
        if n:
            lech[ten] = n
    if lech:
        bc["so_bar_nhay_phi_ly"] = lech
        bc["canh_bao"].append(
            "nhay > 3 lan trong MOT bar o %s - gan nhu chac chan la LECH DAU "
            "THAP PHAN trong du lieu, khong phai bien dong"
            % ", ".join("%s:%d" % kv for kv in lech.items()))
        bc["dung_duoc"] = False

    # BAY 6: BAR KHONG RAU (high = than tren VA low = than duoi).
    #
    # Mot bar nhu vay noi rang gia chua bao gio ra khoi khoang open-close trong
    # ca phien. Tren D1 do gan nhu khong the - no la dau vet cua bo du lieu chi
    # luu OPEN/CLOSE roi CHE high/low ra tu chung.
    #
    # Do 12/09/2026: **39.681 bar tren 128/159 ma**. Nang nhat: YH_BAC 41,6%,
    # SP500 35,5% (1927-2017), YH_NIKKEI 33,6%, USDJPY 25,7% (1971-2015).
    #
    # VI SAO NGUY: `high`/`low` la hai cot quyet dinh cua moi phep cham SL/TP,
    # cua ATR, cua IBS va cua moi mau nen. Bar khong rau lam ATR THAP hon that
    # (TR = high-low bi thu nho) -> SL/TP tinh theo ATR dat QUA GAN -> so lenh
    # va ket qua deu sai. Khong bao loi.
    #
    # Cung ho voi BAY 1 (open bia): ca hai deu la "mot cot duoc che tu cot khac".
    khong_rau = ((np.abs(hi - np.maximum(o, c)) < 1e-12)
                 & (np.abs(np.minimum(o, c) - lo) < 1e-12))
    bc["so_bar_khong_rau"] = int(khong_rau.sum())
    if khong_rau.sum():
        ty_kr = float(khong_rau.mean())
        bc["ty_le_bar_khong_rau"] = round(ty_kr, 4)
        theo_nam_kr = pd.Series(khong_rau, index=df.index).groupby(
            df.index.year).mean()
        ban_kr = _gom_doan([int(y) for y, v in theo_nam_kr.items() if v > 0.20])
        bc["nam_nhieu_bar_khong_rau"] = ban_kr
        bc["cua_so_rau_that"] = _gom_doan(
            [int(y) for y, v in theo_nam_kr.items() if v <= 0.20])
        if ty_kr > 0.05:
            bc["canh_bao"].append(
                "%.1f%% bar KHONG CO RAU (high=than tren va low=than duoi) - "
                "high/low nhieu kha nang duoc CHE tu open/close. ATR bi thu nho "
                "nen SL/TP theo ATR dat qua gan.%s"
                % (ty_kr * 100,
                   (" Nang nhat cac nam %s." % ban_kr) if ban_kr else ""))
    else:
        bc["cua_so_rau_that"] = _gom_doan(sorted({int(y) for y in df.index.year}))

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
