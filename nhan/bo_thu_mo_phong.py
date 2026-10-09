# -*- coding: utf-8 -*-
"""bo_thu_mo_phong.py - BO THU CAC PHUONG AN MO PHONG tren Linux, so TUNG LENH voi MT5 tester that (chu du an 09/10/2026).

Chu du an: *"chay thu cac phuong an tren linux cua ban so voi nhung doan mt5 da biet truoc de ta co duoc phuong an giai quyet o phan
gia lap voi mt5"* va *"ve du lieu mt5 can gi thi giao may nha chay mau roi day len de so sanh"*.

VI SAO CO: 125 o hieu chuan chi cho cloud thay vai con so tong (lai / DD / so lenh). Biet engine lech tester bao nhieu, KHONG biet lech
O DAU (khung nen, thu tu cao / thap trong nen, spread, lam tron lot, lenh nao lech truoc), ma moi cach sua phai chay lai tester
(5-30 phut mot o, may nha chi co MOT tester). Nay may nha day len git hai thu (cung nhom viec `viec/cho/00*-xuat-*`):
  (1) gia M1 that cua cac cua so da hieu chuan  - `b xuat-gia MA M1 --tu .. --den ..`   -> `du_lieu_gia/<MA>_M1*.csv.gz`
  (2) BANG LENH cua tester tung o               - `b xuat-lenh`                         -> `du_lieu_gia/mau_tester/<khoa>_lenh.csv.gz`
Co hai thu do cloud chay MOI phuong an mo phong tren Linux va so voi tester tung lenh, khong ton mot phut tester nao.

## MOT CA = MOT O HIEU CHUAN
`Ca` doc tu bao cao `reports/hieu_chuan/*.json` (nam trong `tep_moi` cua don `viec/xong`): ma, cua so, von, he so quy doi tien (f), tham so
luoi, khoa bang lenh tester, chat luong lich su tester. Mac dinh CHI lay o SACH (chat luong >= `NGUONG_CHAT_LUONG` = 95%): o nhiem (tester
tu doan phan lich su thieu - 2018-H1 chi 1% la that) khong noi gi ve engine (xem `doi_chieu_mo_phong`).

## MOT BIEN THE = MOT CACH MO PHONG CUA CUNG CA
  kieu "bar"  engine `luoi.chay_mang` tren nen gop tu M1: khung M1 / M5 / M15..., mo hinh khop lenh `duong_di` | `cuc_tri`, nhan spread
              (0 = bo spread, 2 = gap doi), cach lay spread khi gop nen (dau | cuoi | max | tb). Nhanh (mili-giay moi nghin nen).
  kieu "ea"   CHINH van ban `ea_LuoiDayDu.mq5` tren san gia C++ (`ea_gia_lap`), chuoi tick SINH TU M1 theo 4 thu tu cao / thap trong nen
              (theo_nen | thap_truoc | cao_truoc | xen_ke): day la "MT5 tester model 0" lam lai tren Linux; cai chua biet DUY NHAT la
              cach tester sinh tick tu M1, nen thu tu nao khop bang lenh tester nhat thi la thu tu gan thuc te nhat. Cham hon (giay -> phut).
Them bien the = them mot dong trong `bien_the_mac_dinh`; ten PHAI duy nhat.

## SO SANH (chi lai TRUOC swap: MT5 tester khong ghi swap; ca hai ben cung tru spread)
Moi lenh tester va moi lenh bien the duoc quy ve GIA BID (lenh MUA mo o ASK / BAN dong o ASK: tru spread cua nen M1 luc do), roi ghep
1-1 theo CHIEU + gio mo (dung sai = 1,5 nen cua khung bien the) + gia mo (dung sai ~ 1/4 buoc luoi). Tra ve:
  - lai nam %, DD, so lenh, ty le khop lenh, lech gia / gio mo trung vi cua cac cap khop, ty le dong cung nhau
  - PHAN RA LECH TONG: cap khop (do gia khac) + lenh chi co o bien the - lenh chi co o tester (cong lai = lech tong; hai ve cung don vi %/nam)
  - LENH LECH DAU TIEN (ben nao, luc nao, chieu, gia, lot) va ty le cua so da khop truoc khi lech: sau lenh lech dau, chuoi ladder rẽ nhanh nen ty
    le khop chung thap la binh thuong - lenh lech dau moi chi ra nguyen nhan
  - lai theo thang (sai so tuyet doi trung binh %von, tuong quan)
Cac bien the xep hang theo sai so tuyet doi trung binh cua lai nam % tren cac ca sach.

## GIOI HAN (doc truoc khi tin ket qua)
  - Xep hang chi noi bien the nao BAM tester nhat tren cac o da co (AUDCAD / NZDCAD / EURCAD, 2019, cau hinh luoi/tia): KHONG chung minh cho ma khac,
    don bay khac, hay nam khac. Khong doi `PHIEN_BAN_ENGINE`, khong ghi so tay, khong tinh phep thu: day la CONG CU DO.
  - Lich su M1 xuat tu may nha PHAI trung voi lich su tester dung (cung nha mo gioi, cung khoang thoi gian): kiem nhat quan `kiem_nhat_quan`
    so tong lai cua bang lenh voi bao cao; lech > 0,5% thi canh bao (khoa sai hoac bang bi cat).
  - Bien the "ea" mo phong tester THEO TICK SINH TU M1 voi buoc 1 point: tester model 0 co cach sinh tick rieng (chua biet), nen khop
    100% la khong bat buoc - nhung neu M1 + thu_tu nao do khop >= 95% lenh thi do la "MT5 tester tren Linux" co bang chung.

## KIEM CO DAP AN (`tao_ca_tong_hop`, `--tu-kiem`)
Khi chua co gia that: random walk 1 tick / giay -> M1 -> chay EA that (san gia) tren chuoi tick theo MOT thu tu da biet lam "tester" -> bo thu phai
tim lai dung thu tu do va do bien the "bar" lech bao nhieu (khop voi bang `kiem_do_phan_giai`). Test: `test_bo_thu_mo_phong.py`.

Dung:
  python3 -m nhan.bo_thu_mo_phong --tu-kiem                       # kiem co dap an, khong can du lieu that
  python3 -m nhan.bo_thu_mo_phong [--bien-the bar|ea|tat_ca|ten1,ten2] [--toi-da N] [--ma AUDCAD] [--ca-nhiem] [--luong 4] [--ghi]
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import multiprocessing as mp
import re
import statistics as S
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from nhan import doi_chieu_mo_phong as DC
from nhan import ea_gia_lap as G
from nhan import hieu_chuan_luoi as HC
from nhan import luoi as LU
from nhan import xuat_gia as XG
from nhan import xuat_lenh_tester as XL

GOC = Path(__file__).resolve().parent.parent
NGUONG_CHAT_LUONG = DC.NGUONG_CHAT_LUONG
EA_MAC_DINH = HC.EA_MAC_DINH

KHUNG_GIAY = {"M1": 60.0, "M5": 300.0, "M15": 900.0, "M30": 1800.0, "H1": 3600.0, "H4": 14400.0, "D1": 86400.0}
_QUY_TAC = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h", "H4": "4h", "D1": "1D"}
SPREAD_GOP = ("dau", "cuoi", "max", "tb")
THU_TU_TICK = ("theo_nen", "thap_truoc", "cao_truoc", "xen_ke")

#: Sai lech cho phep giua tong lai bang lenh tester va bao cao (tuong doi): vuot = bang lenh khong phai cua bao cao nay (hoac bi cat).
DUNG_SAI_NHAT_QUAN = 0.005
#: Nen M1 toi thieu trong cua so va so ngay bien duoc phep thieu o hai dau (giong `hieu_chuan_luoi.nua_engine`).
NEN_TOI_THIEU = 50
NGAY_THIEU_BIEN = 7
_RE_KHOA = re.compile(r"([0-9a-f]{16})_lenh\.csv\.gz$")
COT_LENH = ["mo", "dong", "chieu", "lot", "gia_mo", "gia_dong", "lai", "ly"]


# ============================================================ 1. CA = MOT O HIEU CHUAN
@dataclass(frozen=True, eq=False)
class Ca:
    """Mot o hieu chuan: cung cua so, cung tham so, cung von nhu lan chay tester."""
    ten: str                      # ten bao cao (khoa duy nhat)
    ma: str
    khung: str                    # khung engine cua bao cao goc (khong lien quan den khung cua bien the)
    tu: pd.Timestamp              # 00:00 ngay dau
    den_het: pd.Timestamp         # 23:59:59 ngay cuoi
    ngay: int
    von: float                    # tien TAI KHOAN
    f: float                      # don vi bao gia / 1 don vi tien tai khoan
    ts: dict                      # tham so luoi (truong cua `luoi.ThamSo`)
    khoa: str | None              # 16 hex cua bang lenh tester; None neu bao cao khong ghi
    q: float | None               # chat luong lich su tester (%)
    qc: dict                      # phi qua dem engine da dung (phi_nam_mua / phi_nam_ban), de trong neu bao cao khong ghi
    so_khoa: tuple | None         # (engine, tester, dd_e, dd_t, n_e, n_t) cua bao cao goc
    t_truoc: float | None = None  # lai tester TRUOC swap, tien tai khoan (bao cao ghi)
    n_t: int | None = None        # so lenh tester (bao cao ghi)
    e_truoc_nam: float | None = None   # lai engine goc TRUOC swap %/nam (de kiem tai lap)
    pb: int | None = None         # phien ban engine cua bao cao goc

    @property
    def nam(self) -> float:
        return self.ngay / 365.25


def _ngay_mt5(s) -> pd.Timestamp:
    return pd.Timestamp(str(s).strip().replace(".", "-"))


def ca_tu_bao_cao(bc: dict, ten: str = "") -> Ca:
    """Bao cao `reports/hieu_chuan/*.json` (da parse) -> `Ca`. Thieu truong bat buoc -> ValueError neu ro truong nao."""
    if not isinstance(bc, dict):
        raise ValueError("bao cao khong phai object JSON")
    thieu = [k for k in ("ma", "khung", "cua_so", "von", "tham_so", "he_so_quy_doi", "tester") if bc.get(k) in (None, {}, "")]
    if thieu:
        raise ValueError("bao cao thieu truong %s" % thieu)
    cs = bc["cua_so"]
    try:
        tu, den = _ngay_mt5(cs["tu"]), _ngay_mt5(cs["den"])
        ngay = int(cs.get("ngay") or ((den - tu).days + 1))
        f = float(bc["he_so_quy_doi"]["dung"])
        von = float(bc["von"])
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError("bao cao co cua_so / he_so_quy_doi / von khong doc duoc: %s" % e) from e
    if not (math.isfinite(f) and f > 0 and math.isfinite(von) and von > 0 and ngay > 0):
        raise ValueError("bao cao co he so quy doi / von / so ngay khong hop le: f=%r von=%r ngay=%r" % (f, von, ngay))
    t = bc["tester"] if isinstance(bc["tester"], dict) else {}
    m = _RE_KHOA.search(str(t.get("bang_lenh") or ""))
    es = bc.get("engine") if isinstance(bc.get("engine"), dict) else {}
    qc = (es.get("qc") or {}) if isinstance(es.get("qc"), dict) else {}
    sk = bc.get("so_khoa")
    nam = ngay / 365.25
    return Ca(ten=ten or "%s_%s_%s_%s" % (bc["ma"], bc["khung"], cs["tu"], cs["den"]), ma=str(bc["ma"]).upper(), khung=str(bc["khung"]).upper(),
              tu=tu, den_het=den + pd.Timedelta(days=1) - pd.Timedelta(seconds=1), ngay=ngay, von=von, f=f, ts=dict(bc["tham_so"]),
              khoa=m.group(1) if m else None, q=t.get("chat_luong_pct"),
              qc={k: qc[k] for k in ("phi_nam_mua", "phi_nam_ban") if qc.get(k) is not None},
              so_khoa=tuple(float(x) for x in sk) if isinstance(sk, list) and len(sk) == 6 else None,
              t_truoc=_so(t.get("thong_ke"), "lai_chua_swap"), n_t=_so_nguyen((t.get("thong_ke") or {}).get("so_lenh_mo") if isinstance(t.get("thong_ke"), dict) else None),
              e_truoc_nam=DC._pct_nam(es.get("thong_ke"), von, nam), pb=bc.get("phien_ban_engine"))


def _so(d, khoa):
    try:
        v = float(d[khoa])
        return v if math.isfinite(v) else None
    except (KeyError, TypeError, ValueError):
        return None


def _so_nguyen(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def doc_cac_ca(thu_muc: str = "viec/xong", chi_sach: bool = True, nguong: float = NGUONG_CHAT_LUONG) -> tuple[list[Ca], dict]:
    """Moi bao cao hieu chuan (khong trung; chay hai lan thi lay lan moi nhat) trong cac don `viec/xong` thanh mot `Ca`.
    Tra (cac_ca, bo_qua {ten: ly do}). `chi_sach`: bo o co chat luong lich su tester < `nguong` (hoac khong ro)."""
    don = []
    for f in Path(thu_muc).glob("*.json"):
        try:
            don.append(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    cac, bo = {}, {}
    for d in sorted((x for x in don if isinstance(x, dict)), key=lambda x: str(x.get("luc") or "")):
        b = d.get("bang_chung") or {}
        if "hieu_chuan_luoi" not in " ".join(map(str, b.get("lenh") or [])):
            continue
        vb = "".join(b.get("dong_cuoi") or [])
        m = DC._RE_BAO_CAO.search(vb)
        if not m:
            continue
        duong = m.group(1)
        bc = DC._bao_cao(b.get("tep_moi"), duong)
        if not bc:
            bo[duong] = "khong doc duoc bao cao trong don %s" % d.get("ma")
            continue
        try:
            ca = ca_tu_bao_cao(bc, duong)
        except ValueError as e:
            bo[duong] = str(e)
            continue
        bo.pop(duong, None)
        cac[duong] = ca                                       # ban sau (luc moi hon) ghi de
    ra = []
    for duong, ca in cac.items():
        if chi_sach and (ca.q is None or ca.q < nguong):
            bo[duong] = "chat luong lich su tester %s%% < %s%% (o nhiem)" % (ca.q, nguong)
        elif not ca.khoa:
            bo[duong] = "bao cao khong ghi duong bang lenh tester"
        else:
            ra.append(ca)
    return sorted(ra, key=lambda c: (c.ma, c.tu, c.ten)), bo


# ============================================================ 2. GIA M1 + BANG LENH TESTER
def nap_m1(ma: str, thu_muc: Path | None = None) -> pd.DataFrame:
    """Ghep moi file M1 da xuat cua `ma` (xem `xuat_gia.doc_het`). Khong co file -> FileNotFoundError."""
    d = XG.doc_het(ma, "M1", thu_muc)
    thieu = [c for c in ("open", "high", "low", "close") if c not in d.columns]
    if thieu:
        raise ValueError("file gia M1 %s thieu cot %s" % (ma, thieu))
    return d


def cat_cua_so(m1: pd.DataFrame, ca: Ca) -> pd.DataFrame:
    return m1.loc[ca.tu:ca.den_het]


def kiem_phu(seg: pd.DataFrame, ca: Ca) -> str | None:
    """None neu M1 phu dung cua so cua `ca`; khong thi ly do (khong chay tren nua cua so roi bao nhu da du)."""
    if len(seg) < NEN_TOI_THIEU:
        return "gia M1 chi co %d nen trong cua so %s .. %s" % (len(seg), ca.tu.date(), ca.den_het.date())
    bien = pd.Timedelta(days=NGAY_THIEU_BIEN)
    if seg.index[0] > ca.tu + bien or seg.index[-1] < ca.den_het - bien:
        return "gia M1 chi phu %s .. %s, khong phu cua so %s .. %s" % (seg.index[0].date(), seg.index[-1].date(), ca.tu.date(), ca.den_het.date())
    if seg[["open", "high", "low", "close"]].isna().any().any():
        return "gia M1 co o trong (NaN) trong cua so"
    return None


def gop_khung(m1: pd.DataFrame, khung: str, spread: str = "dau") -> pd.DataFrame:
    """Gop nen M1 thanh khung `khung` (M1 tra nguyen). Nen rong (cuoi tuan / khong co tick) bi bo. `spread`: lay spread cua nen M1 dau / cuoi /
    lon nhat / trung binh trong nen gop (cach MT5 gan spread cho nen lon chua ro - la mot bien the)."""
    khung = str(khung).upper()
    if khung not in _QUY_TAC:
        raise ValueError("khung %r khong hop le (co %s)" % (khung, list(_QUY_TAC)))
    if spread not in SPREAD_GOP:
        raise ValueError("cach gop spread %r khong hop le (co %s)" % (spread, SPREAD_GOP))
    if khung == "M1":
        return m1
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "tick_volume" in m1.columns:
        agg["tick_volume"] = "sum"
    if "spread" in m1.columns:
        agg["spread"] = {"dau": "first", "cuoi": "last", "max": "max", "tb": "mean"}[spread]
    r = m1.resample(_QUY_TAC[khung], label="left", closed="left").agg(agg)
    return r.dropna(subset=["close"])


def serie_spread(seg: pd.DataFrame, qc: LU.QuyCach) -> np.ndarray:
    """Spread theo GIA tung nen M1 (cot POINT x point); nen bang 0 / thieu cot thay bang trung vi (giong `luoi.chuan_bi`)."""
    if "spread" not in seg.columns:
        return np.full(len(seg), float(qc.spread_du_phong))
    sp = seg["spread"].to_numpy(float) * qc.point
    duong = sp[sp > 0]
    return np.where(sp > 0, sp, float(np.median(duong)) if duong.size else float(qc.spread_du_phong))


def quy_cach_ca(ca: Ca, gia_dien_hinh: float | None = None) -> LU.QuyCach:
    """`QuyCach` cua ma theo lop, cong phi qua dem engine da dung trong bao cao (neu co) va he so quy doi cua o."""
    qc, ly = LU.quy_cach_cho(ca.ma, gia_dien_hinh, None)
    if qc is None:
        raise ValueError(ly)
    return dataclasses.replace(qc, von_quy_doi=float(ca.f), **{k: float(v) for k, v in ca.qc.items()})


def kiem_nhat_quan(ca: Ca, bang: pd.DataFrame) -> list[str]:
    """Bang lenh tester co dung la cua bao cao nay khong: tong lai va so lenh phai trung voi bao cao. Tra danh sach canh bao (rong = khop)."""
    cb = []
    lai = float(pd.to_numeric(bang["lai"], errors="coerce").fillna(0.0).sum())
    if ca.t_truoc is not None and abs(lai - ca.t_truoc) > DUNG_SAI_NHAT_QUAN * max(abs(ca.t_truoc), 0.01 * ca.von):
        cb.append("tong lai bang lenh %.2f khac bao cao %.2f (bang cat hoac sai khoa)" % (lai, ca.t_truoc))
    if ca.n_t is not None and len(bang) != ca.n_t:
        cb.append("bang lenh co %d lenh, bao cao ghi %d" % (len(bang), ca.n_t))
    return cb


# ============================================================ 3. QUY VE GIA BID + GHEP LENH
def _giay_epoch(t) -> np.ndarray:
    """Chuoi thoi gian -> giay epoch float (NaT -> NaN)."""
    ix = pd.DatetimeIndex(pd.to_datetime(t))
    return np.where(ix.isna(), np.nan, ix.as_unit("ns").asi8.astype(np.float64) / 1e9)


def them_bid(bang: pd.DataFrame, dang_gia: str, idx=None, sp_gia=None) -> pd.DataFrame:
    """Them cot `bid_mo`, `bid_dong` = gia quy ve chuoi BID.
    dang_gia='san'  bang theo gia san/tester: MUA mo o ASK, BAN dong o ASK -> tru spread (GIA) cua nen `idx` chua thoi diem do.
    dang_gia='bid'  engine: moi gia da nam tren chuoi BID (spread tinh rieng thanh chi phi) -> giu nguyen."""
    b = bang.reset_index(drop=True).copy()
    gm = pd.to_numeric(b["gia_mo"], errors="coerce").to_numpy(float)
    gd = pd.to_numeric(b["gia_dong"], errors="coerce").to_numpy(float)
    if dang_gia == "bid":
        b["bid_mo"], b["bid_dong"] = gm, gd
        return b
    if dang_gia != "san":
        raise ValueError("dang_gia phai la 'san' hoac 'bid', nhan %r" % (dang_gia,))
    if idx is None or sp_gia is None or len(idx) != len(sp_gia):
        raise ValueError("dang_gia='san' can idx va sp_gia cung do dai")
    t_idx, sp = _giay_epoch(idx), np.asarray(sp_gia, float)

    def spread_tai(cot):
        t = _giay_epoch(b[cot])
        co = ~np.isnan(t)
        p = np.zeros(len(t), np.int64)
        p[co] = np.clip(np.searchsorted(t_idx, t[co], side="right") - 1, 0, len(t_idx) - 1)
        return np.where(co, sp[p], np.nan)

    ch = pd.to_numeric(b["chieu"], errors="coerce").to_numpy(float)
    b["bid_mo"] = gm - np.where(ch > 0, spread_tai("mo"), 0.0)
    b["bid_dong"] = gd - np.where(ch < 0, spread_tai("dong"), 0.0)
    return b


def _mang(b: pd.DataFrame) -> dict:
    return {"t_mo": _giay_epoch(b["mo"]), "t_dong": _giay_epoch(b["dong"]), "chieu": pd.to_numeric(b["chieu"]).to_numpy(float),
            "lot": pd.to_numeric(b["lot"]).to_numpy(float), "bid_mo": b["bid_mo"].to_numpy(float), "bid_dong": b["bid_dong"].to_numpy(float),
            "lai": pd.to_numeric(b["lai"]).fillna(0.0).to_numpy(float)}


def ghep_lenh(a: pd.DataFrame, b: pd.DataFrame, tol_giay: float, tol_gia: float) -> dict:
    """Ghep 1-1 lenh bien the `a` voi lenh tester `b`: cung CHIEU, gio mo cach <= `tol_giay`, gia BID luc mo cach <= `tol_gia` (don vi gia).
    Duyet `a` theo gio mo, moi lenh nhan lenh `b` CHUA DUNG gan nhat ve gia (hoa thi gan nhat ve gio). Tra {cap: [(ia, ib)], chi_a: [...], chi_b: [...]}
    (chi so hang cua `a` / `b`). Hai bang can cot `bid_mo` (xem `them_bid`)."""
    A, B = _mang(a), _mang(b)
    dung_b = np.zeros(len(B["t_mo"]), bool)
    cap, chi_a = [], []
    for c in (1.0, -1.0):
        ia = np.flatnonzero(A["chieu"] == c)
        ib = np.flatnonzero(B["chieu"] == c)
        ia = ia[np.argsort(A["t_mo"][ia], kind="stable")]
        ib = ib[np.argsort(B["t_mo"][ib], kind="stable")]
        tb = B["t_mo"][ib]
        for i in ia:
            lo = int(np.searchsorted(tb, A["t_mo"][i] - tol_giay, side="left"))
            hi = int(np.searchsorted(tb, A["t_mo"][i] + tol_giay, side="right"))
            tot, khoa_tot = None, None
            for k in range(lo, hi):
                j = int(ib[k])
                if dung_b[j]:
                    continue
                d = abs(A["bid_mo"][i] - B["bid_mo"][j])
                if d > tol_gia:
                    continue
                khoa = (d, abs(B["t_mo"][j] - A["t_mo"][i]))
                if tot is None or khoa < khoa_tot:
                    tot, khoa_tot = j, khoa
            if tot is None:
                chi_a.append(int(i))
            else:
                dung_b[tot] = True
                cap.append((int(i), tot))
    chi_b = [int(j) for j in np.flatnonzero(~dung_b)]
    return {"cap": sorted(cap), "chi_a": sorted(chi_a), "chi_b": chi_b}


def _trung_vi(x):
    x = [v for v in x if v == v]
    return round(float(np.median(x)), 4) if x else None


def so_sanh_bang(a: pd.DataFrame, b: pd.DataFrame, *, tol_giay: float, tol_gia: float, pip: float, von: float, ngay: float,
                 t0: pd.Timestamp | None = None, t1: pd.Timestamp | None = None) -> dict:
    """So bang lenh bien the `a` voi bang tester `b` (hai bang da co `bid_mo` / `bid_dong`, lai TRUOC swap, TIEN TAI KHOAN). Cac truong:
    n_a / n_b / n_khop / ti_le_khop, lech_gia_mo_pip, lech_gio_mo_giay (trung vi cap khop), khop_dong, khac_lot, khop_den (ty le cua so truoc lenh lech
    dau), lech_dau, phan_ra {cap, chi_bien_the, chi_tester} (%/nam, cong = lech tong), lai_thang {mae_pct_von, tuong_quan, n_thang}."""
    g = ghep_lenh(a, b, tol_giay, tol_gia)
    A, B = _mang(a), _mang(b)
    cap = g["cap"]
    ia = np.array([p[0] for p in cap], int)
    ib = np.array([p[1] for p in cap], int)
    n_a, n_b = len(a), len(b)
    out = {"n_a": n_a, "n_b": n_b, "n_khop": len(cap), "n_chi_a": len(g["chi_a"]), "n_chi_b": len(g["chi_b"]),
           "ti_le_khop": round(len(cap) / max(n_a, n_b), 4) if max(n_a, n_b) else 1.0}
    he_so = 100.0 / von / (ngay / 365.25)
    out["phan_ra"] = {"cap": round(float((A["lai"][ia] - B["lai"][ib]).sum()) * he_so, 4) if len(cap) else 0.0,
                      "chi_bien_the": round(float(A["lai"][g["chi_a"]].sum()) * he_so, 4),
                      "chi_tester": round(-float(B["lai"][g["chi_b"]].sum()) * he_so, 4)}
    if len(cap):
        out["lech_gia_mo_pip"] = _trung_vi(np.abs(A["bid_mo"][ia] - B["bid_mo"][ib]) / pip)
        out["lech_gio_mo_giay"] = _trung_vi(np.abs(A["t_mo"][ia] - B["t_mo"][ib]))
        co_ca_hai = ~np.isnan(A["t_dong"][ia]) & ~np.isnan(B["t_dong"][ib])
        if co_ca_hai.any():
            ok = (np.abs(A["t_dong"][ia][co_ca_hai] - B["t_dong"][ib][co_ca_hai]) <= tol_giay) & \
                 (np.abs(A["bid_dong"][ia][co_ca_hai] - B["bid_dong"][ib][co_ca_hai]) <= tol_gia)
            out["khop_dong"] = round(float(ok.mean()), 4)
        else:
            out["khop_dong"] = None
        out["khac_lot"] = int((np.abs(A["lot"][ia] - B["lot"][ib]) > 1e-9 + 1e-6 * B["lot"][ib]).sum())
    else:
        out.update(lech_gia_mo_pip=None, lech_gio_mo_giay=None, khop_dong=None, khac_lot=0)
    # lenh lech DAU TIEN (theo gio mo, hai ben)
    ung = [("bien_the", A, i) for i in g["chi_a"]] + [("tester", B, j) for j in g["chi_b"]]
    if ung:
        ben, X, k = min(ung, key=lambda u: (u[1]["t_mo"][u[2]], u[0]))
        out["lech_dau"] = {"ben": ben, "mo": str(pd.Timestamp(X["t_mo"][k], unit="s")), "chieu": int(X["chieu"][k]),
                           "bid_mo": float(X["bid_mo"][k]), "lot": float(X["lot"][k])}
        if t0 is not None and t1 is not None and t1 > t0:
            out["khop_den"] = round(float(np.clip((X["t_mo"][k] - t0.timestamp()) / (t1 - t0).total_seconds(), 0.0, 1.0)), 4)
        else:
            out["khop_den"] = None
    else:
        out["lech_dau"], out["khop_den"] = None, 1.0
    out["lai_thang"] = _lai_thang(a, b, von, t1)
    return out


def _lai_thang(a: pd.DataFrame, b: pd.DataFrame, von: float, het: pd.Timestamp | None) -> dict:
    """Lai theo thang DONG lenh (lenh con mo luc het tinh vao thang cuoi cua cua so)."""
    def theo_thang(x):
        dong = pd.to_datetime(x["dong"])
        if het is not None:
            dong = dong.fillna(het)
        s = pd.Series(pd.to_numeric(x["lai"]).to_numpy(float), index=pd.DatetimeIndex(dong).to_period("M"))
        return s.groupby(level=0).sum()
    if len(a) == 0 and len(b) == 0:
        return {"mae_pct_von": 0.0, "tuong_quan": None, "n_thang": 0}
    sa, sb = theo_thang(a) if len(a) else pd.Series(dtype=float), theo_thang(b) if len(b) else pd.Series(dtype=float)
    u = sa.index.union(sb.index)
    if not len(u):                                    # toan lenh con mo va khong biet gio het: khong xep duoc vao thang nao
        return {"mae_pct_von": None, "tuong_quan": None, "n_thang": 0}
    va, vb = sa.reindex(u, fill_value=0.0).to_numpy(float), sb.reindex(u, fill_value=0.0).to_numpy(float)
    tq = None
    if len(u) >= 3 and np.std(va) > 0 and np.std(vb) > 0:
        tq = round(float(np.corrcoef(va, vb)[0, 1]), 4)
    return {"mae_pct_von": round(float(np.mean(np.abs(va - vb))) / von * 100.0, 4), "tuong_quan": tq, "n_thang": int(len(u))}


# ============================================================ 4. BIEN THE
@dataclass(frozen=True)
class BienThe:
    """Mot cach mo phong. `kieu`: 'bar' (engine tren nen gop tu M1) | 'ea' (EA that tren tick sinh tu M1)."""
    ten: str
    kieu: str = "bar"
    khung: str = "M1"
    khop_bar: str = "duong_di"
    nhan_spread: float = 1.0
    spread_gop: str = "dau"
    thu_tu: str = "theo_nen"

    def __post_init__(self):
        if not self.ten or not isinstance(self.ten, str):
            raise ValueError("bien the can co ten")
        if self.kieu not in ("bar", "ea"):
            raise ValueError("kieu phai la 'bar' hoac 'ea', nhan %r" % (self.kieu,))
        if self.khung not in KHUNG_GIAY:
            raise ValueError("khung %r khong hop le (co %s)" % (self.khung, list(KHUNG_GIAY)))
        if self.khop_bar not in LU.MO_HINH_BAR:
            raise ValueError("khop_bar %r khong hop le (co %s)" % (self.khop_bar, LU.MO_HINH_BAR))
        if self.spread_gop not in SPREAD_GOP:
            raise ValueError("spread_gop %r khong hop le (co %s)" % (self.spread_gop, SPREAD_GOP))
        if self.thu_tu not in THU_TU_TICK:
            raise ValueError("thu_tu %r khong hop le (co %s)" % (self.thu_tu, THU_TU_TICK))
        if not (isinstance(self.nhan_spread, (int, float)) and math.isfinite(self.nhan_spread) and self.nhan_spread >= 0):
            raise ValueError("nhan_spread phai la so >= 0, nhan %r" % (self.nhan_spread,))
        if self.kieu == "ea" and self.khung != "M1":
            raise ValueError("bien the 'ea' sinh tick tu M1: khung phai la M1, nhan %s" % self.khung)


def bien_the_mac_dinh() -> list[BienThe]:
    ds = []
    for kh in ("M1", "M5", "M15"):
        for kb in ("duong_di", "cuc_tri"):
            ds.append(BienThe("bar_%s_%s" % (kh.lower(), kb), "bar", kh, kb))
    ds.append(BienThe("bar_m1_duong_di_sp0", "bar", "M1", "duong_di", nhan_spread=0.0))
    ds.append(BienThe("bar_m1_duong_di_sp2", "bar", "M1", "duong_di", nhan_spread=2.0))
    ds.append(BienThe("bar_m15_duong_di_spmax", "bar", "M15", "duong_di", spread_gop="max"))
    for tt in THU_TU_TICK:
        ds.append(BienThe("ea_m1_" + tt, "ea", "M1", thu_tu=tt))
    return ds


def chon_bien_the(mo_ta: str | None) -> list[BienThe]:
    """'bar' | 'ea' | 'tat_ca' (hoac rong) | danh sach ten cach nhau dau phay. Ten la -> ValueError (khong bo qua am tham)."""
    tat = bien_the_mac_dinh()
    if not mo_ta or mo_ta == "tat_ca":
        return tat
    if mo_ta in ("bar", "ea"):
        return [b for b in tat if b.kieu == mo_ta]
    theo_ten = {b.ten: b for b in tat}
    ra = []
    for t in (x.strip() for x in mo_ta.split(",") if x.strip()):
        if t not in theo_ten:
            raise ValueError("bien the %r khong co (co: %s)" % (t, ", ".join(theo_ten)))
        ra.append(theo_ten[t])
    return ra


@dataclass
class KetQuaBT:
    """Ket qua mot bien the tren mot ca. `bang` co `bid_mo` / `bid_dong`; `lai` = TRUOC swap, tien tai khoan, ke ca lenh con mo luc het cua so."""
    ten: str
    bang: pd.DataFrame | None = None
    lai: float = 0.0
    lai_nam_pct: float = 0.0
    dd_pct: float = 0.0
    chay: bool = False
    giay: float = 0.0
    canh_bao: list = field(default_factory=list)
    loi: str | None = None


def chay_bar(ca: Ca, seg: pd.DataFrame, bt: BienThe) -> KetQuaBT:
    """Engine `luoi.chay_mang` tren nen gop tu M1 (cung duong `hieu_chuan_luoi.nua_engine`: chuan_bi -> chay_mang -> bang_lenh_engine)."""
    t = time.time()
    bars = gop_khung(seg, bt.khung, bt.spread_gop)
    qc = quy_cach_ca(ca, float(np.nanmedian(bars["close"].to_numpy(float))))
    ts = LU.ThamSo(**dict(ca.ts, khop_bar=bt.khop_bar))
    dl = LU.chuan_bi(bars, qc)
    if bt.nhan_spread != 1.0:
        dl = dataclasses.replace(dl, sp=dl.sp * float(bt.nhan_spread))
    von_q = ca.von * ca.f
    kq = LU.chay_mang(dl, ts, von_q, ghi_lenh=True)
    chi = LU.chi_so(kq, von_q)
    b, kiem = HC.bang_lenh_engine(kq, dl, ca.f, ts.khop_bar)
    cb = [] if kiem["khop"] else ["bang lenh engine khong cong lai bang tong cua engine (kiem['khop'] = False)"]
    b = them_bid(b, "bid")
    lai = float(pd.to_numeric(b["lai"]).sum())
    return KetQuaBT(bt.ten, b, lai, lai / ca.von / ca.nam * 100.0, abs(float(chi["maxdd_pct"])), bool(kq.chay), time.time() - t, cb)


def bang_tu_ea(lenh: pd.DataFrame, tk: dict, qc: LU.QuyCach, f: float) -> pd.DataFrame:
    """Bang lenh cua san gia EA (`ea_gia_lap.chay()['lenh']`) -> bang chung (theo gia san: MUA mo o ASK / dong o BID, BAN nguoc lai). Lenh con mo luc
    het chuoi tick dong tam o gia tick cuoi (BAN dong o ASK) - tester cung dong not cuoi cua so ('end of test')."""
    if lenh is None or len(lenh) == 0:
        return pd.DataFrame({c: pd.Series(dtype=object) for c in COT_LENH})
    t_tick = np.asarray(tk["time"], float)
    tm = lenh["tick_mo"].to_numpy(int)
    td = pd.to_numeric(lenh["tick_dong"], errors="coerce").to_numpy(float)
    co = ~np.isnan(td)
    mo = pd.to_datetime(t_tick[tm], unit="s")
    dong = pd.to_datetime(np.where(co, t_tick[np.where(co, td, 0).astype(int)], np.nan), unit="s")
    chieu = np.where(lenh["type"].to_numpy() == 0, 1, -1)
    lot = lenh["vol"].to_numpy(float)
    gm = lenh["open"].to_numpy(float)
    gd = pd.to_numeric(lenh["close"], errors="coerce").to_numpy(float)
    bid_cuoi, sp_cuoi = float(np.asarray(tk["bid"], float)[-1]), float(np.asarray(tk["spread"], float)[-1])
    gia_ra = np.where(co, gd, np.where(chieu > 0, bid_cuoi, bid_cuoi + sp_cuoi))
    lai = chieu * (gia_ra - gm) * lot * qc.hop_dong / float(f)
    return pd.DataFrame({"mo": mo, "dong": dong, "chieu": chieu, "lot": lot, "gia_mo": gm, "gia_dong": np.where(co, gd, np.nan), "lai": lai,
                         "ly": np.where(co, lenh["ly_do"].astype(str).to_numpy(), "het_gio")})


def chay_ea(ca: Ca, seg: pd.DataFrame, bt: BienThe, exe, han_giay: int = 1800) -> KetQuaBT:
    """CHINH `ea_LuoiDayDu.mq5` tren san gia, tick sinh tu M1 theo `bt.thu_tu` (buoc 1 point, giay_bar = 60). `exe`: file da bien dich."""
    t = time.time()
    qc = quy_cach_ca(ca, float(np.nanmedian(seg["close"].to_numpy(float))))
    ts = LU.ThamSo(**dict(ca.ts, khop_bar="duong_di"))          # chi de dich tham so luoi sang input EA
    ps = G.tham_so_ea_tu_luoi(ts)
    ps["InpPipSize"] = qc.pip
    gia = seg if bt.nhan_spread == 1.0 else seg.assign(spread=seg["spread"] * float(bt.nhan_spread))
    tk = G.tick_tu_bar(gia, bt.thu_tu, point=qc.point, giay_bar=60.0, paso=qc.point)
    r = G.chay(exe, tk, ca.von * ca.f, ps, digits=int(round(-math.log10(qc.point))), han_giay=han_giay)
    if not r["ok"]:
        raise RuntimeError("EA tren san gia khong chay duoc: %s %s" % (str(r["loi"])[-300:], r["log"][-3:]))
    b = bang_tu_ea(r["lenh"], tk, qc, ca.f)
    b = them_bid(b, "san", seg.index, serie_spread(gia, qc))
    lai = float(pd.to_numeric(b["lai"]).sum()) if len(b) else 0.0
    return KetQuaBT(bt.ten, b, lai, lai / ca.von / ca.nam * 100.0, float(r["kq"].get("max_dd_pct", 0.0)), False, time.time() - t)


def chay_bien_the(ca: Ca, seg: pd.DataFrame, bt: BienThe, exe=None) -> KetQuaBT:
    """Chay mot bien the; loi ha tang (tham so la, gia hong, khong co EA...) -> `KetQuaBT.loi` co ly do, KHONG nem ra ngoai va KHONG tinh nhu 'am'."""
    try:
        if bt.kieu == "ea":
            if exe is None:
                raise RuntimeError("bien the 'ea' can file EA da bien dich (exe)")
            return chay_ea(ca, seg, bt, exe)
        return chay_bar(ca, seg, bt)
    except Exception as e:                                      # noqa: BLE001 - mot ca hong khong duoc lam sap ca lo
        return KetQuaBT(bt.ten, loi="%s: %s" % (type(e).__name__, str(e)[:300]))


def dung_sai_cua(ca: Ca, bt: BienThe, pip: float | None = None) -> tuple[float, float]:
    """(tol_giay, tol_gia): gio mo lech toi da = 1,5 nen cua khung (it nhat 2 phut); gia mo lech toi da ~ 1/4 buoc luoi, trong [0,3; 1,0] pip."""
    pip = quy_cach_ca(ca).pip if pip is None else pip
    buoc = float(ca.ts.get("buoc") or 20.0)
    return max(120.0, 1.5 * KHUNG_GIAY[bt.khung]), float(np.clip(0.25 * buoc, 0.3, 1.0)) * pip


# ============================================================ 5. QUET
def chay_mot_ca(ca: Ca, cac_bt: list[BienThe], thu_muc_gia=None, thu_muc_lenh=None, exe=None, m1=None, bang_tester=None) -> list[dict]:
    """Moi bien the tren mot ca -> danh sach dong ket qua (mot dong / bien the). `m1` / `bang_tester` co san thi khong doc lai tu dia (test)."""
    nen = {"ca": ca.ten, "ma": ca.ma, "khung_goc": ca.khung, "tu": str(ca.tu.date()), "den": str(ca.den_het.date()), "q": ca.q}
    try:
        if m1 is None:
            m1 = nap_m1(ca.ma, thu_muc_gia)
        seg = cat_cua_so(m1, ca)
        ly = kiem_phu(seg, ca)
        if ly:
            return [dict(nen, bien_the=bt.ten, loi=ly) for bt in cac_bt]
        bang_t = bang_tester if bang_tester is not None else XL.doc(ca.khoa, thu_muc_lenh)
        miss = [c for c in XL.COT_BAT_BUOC if c not in bang_t.columns]
        if miss:
            raise ValueError("bang lenh tester thieu cot %s" % miss)
        qc = quy_cach_ca(ca, float(np.nanmedian(seg["close"].to_numpy(float))))
        canh_bao = kiem_nhat_quan(ca, bang_t)
        bang_t = them_bid(bang_t, "san", seg.index, serie_spread(seg, qc))
    except (FileNotFoundError, ValueError, OSError, KeyError) as e:
        return [dict(nen, bien_the=bt.ten, loi="%s: %s" % (type(e).__name__, str(e)[:200])) for bt in cac_bt]
    lai_t = float(pd.to_numeric(bang_t["lai"]).fillna(0.0).sum())
    nen.update(lai_nam_tester=lai_t / ca.von / ca.nam * 100.0, dd_tester=ca.so_khoa[3] if ca.so_khoa else None,
               n_tester=len(bang_t), lai_nam_goc_engine=ca.e_truoc_nam, canh_bao=canh_bao)
    rows = []
    for bt in cac_bt:
        kq = chay_bien_the(ca, seg, bt, exe)
        if kq.loi:
            rows.append(dict(nen, bien_the=bt.ten, loi=kq.loi))
            continue
        tg, tp = dung_sai_cua(ca, bt, qc.pip)
        so = so_sanh_bang(kq.bang, bang_t, tol_giay=tg, tol_gia=tp, pip=qc.pip, von=ca.von, ngay=ca.ngay, t0=ca.tu, t1=ca.den_het)
        rows.append(dict(nen, bien_the=bt.ten, lai_nam_pct=kq.lai_nam_pct, dd_pct=kq.dd_pct, chay=kq.chay, giay=round(kq.giay, 2),
                         canh_bao_bt=kq.canh_bao, **so))
    return rows


def _tac_vu(args):
    ca, cac_bt, tg, tl, exe = args
    return chay_mot_ca(ca, cac_bt, tg, tl, exe)


def quet(cac_ca: list[Ca], cac_bt: list[BienThe], thu_muc_gia=None, thu_muc_lenh=None, exe=None, luong: int = 1, ra=None) -> list[dict]:
    """Chay moi bien the tren moi ca. `luong` > 1: moi ca mot tien trinh (fork; moi tien trinh tu doc M1 tu dia). Tra danh sach dong."""
    ra = ra or (lambda *_: None)
    if any(b.kieu == "ea" for b in cac_bt) and exe is None:
        exe = bien_dich_ea()
    rows = []
    viec = [(ca, cac_bt, thu_muc_gia, thu_muc_lenh, exe) for ca in cac_ca]
    if luong <= 1 or len(viec) <= 1:
        for k, v in enumerate(viec, 1):
            rows += _tac_vu(v)
            ra("[%d/%d] %s" % (k, len(viec), v[0].ten))
    else:
        with ProcessPoolExecutor(max_workers=min(luong, len(viec)), mp_context=mp.get_context("fork")) as p:
            for k, kq in enumerate(p.map(_tac_vu, viec), 1):
                rows += kq
                ra("[%d/%d] %s" % (k, len(viec), viec[k - 1][0].ten))
    return rows


def bien_dich_ea(duong=None, thu_muc=None):
    """Bien dich `ea_LuoiDayDu.mq5` ra san gia C++ (khong co g++ / clang++ -> RuntimeError ro rang)."""
    if G.trinh_bien_dich() is None:
        raise RuntimeError("khong co g++ / clang++ de bien dich EA tren san gia (bien the 'ea')")
    return G.bien_dich(duong or EA_MAC_DINH, thu_muc=thu_muc or tempfile.mkdtemp(prefix="bo_thu_ea_"))


# ============================================================ 6. TONG HOP
def tong_hop(rows: list[dict]) -> list[dict]:
    """Gop cac dong theo bien the (bo dong loi) va xep theo sai so tuyet doi trung binh cua lai nam % (tot nhat truoc)."""
    theo = {}
    for r in rows:
        if r.get("loi") or r.get("lai_nam_pct") is None:
            continue
        theo.setdefault(r["bien_the"], []).append(r)
    ra = []
    for ten, g in theo.items():
        lech = [r["lai_nam_pct"] - r["lai_nam_tester"] for r in g]
        tl_lenh = [r["n_a"] / r["n_b"] for r in g if r["n_b"]]
        tl_dd = [r["dd_pct"] / r["dd_tester"] for r in g if r.get("dd_tester") and r["dd_tester"] > 1]
        kd = [r["khop_den"] for r in g if r.get("khop_den") is not None]
        ra.append({"bien_the": ten, "n": len(g), "lech_trung_vi": round(S.median(lech), 3), "sai_so_tb": round(S.mean(abs(x) for x in lech), 3),
                   "cung_dau": sum((r["lai_nam_pct"] > 0) == (r["lai_nam_tester"] > 0) for r in g),
                   "ti_le_lenh_trung_vi": round(S.median(tl_lenh), 3) if tl_lenh else None,
                   "ti_le_dd_trung_vi": round(S.median(tl_dd), 3) if tl_dd else None,
                   "khop_lenh_tb": round(S.mean(r["ti_le_khop"] for r in g), 4),
                   "khop_den_trung_vi": round(S.median(kd), 4) if kd else None,
                   "giay_tb": round(S.mean(r["giay"] for r in g), 2)})
    return sorted(ra, key=lambda d: (d["sai_so_tb"], -d["khop_lenh_tb"], d["bien_the"]))


def in_bang(tong: list[dict], out=print) -> None:
    out("%-26s %3s %9s %8s %7s %6s %6s %7s %8s %7s" % ("bien the", "n", "lech_tv", "sai_tb", "cung_dau", "lenh", "dd", "khop", "khop_den", "giay"))
    for d in tong:
        out("%-26s %3d %+9.2f %8.2f %4d/%-3d %6s %6s %7.3f %8s %7.1f" % (
            d["bien_the"], d["n"], d["lech_trung_vi"], d["sai_so_tb"], d["cung_dau"], d["n"],
            "-" if d["ti_le_lenh_trung_vi"] is None else "%.3f" % d["ti_le_lenh_trung_vi"],
            "-" if d["ti_le_dd_trung_vi"] is None else "%.2f" % d["ti_le_dd_trung_vi"], d["khop_lenh_tb"],
            "-" if d["khop_den_trung_vi"] is None else "%.3f" % d["khop_den_trung_vi"], d["giay_tb"]))


# ============================================================ 7. KIEM CO DAP AN (du lieu tong hop)
CAU_HINH_NHAY = dict(buoc=1.5, tp=1.2, tran_tang=6, che_do="hai_chieu", lot=0.01, tia_lenh=True, bien_cap=1.0)


def m1_tong_hop(seed: int = 1, ngay: float = 2.0, spread_pts: int = 20, gia0: float = 0.9, sigma_pip: float = 0.25,
                bat_dau: str = "2019-01-02") -> pd.DataFrame:
    """M1 tong hop: random walk 1 tick / giay (sigma `sigma_pip` pip) gop 60 tick / nen, gia tren luoi 5 chu so, open = close nen truoc."""
    from nhan import kiem_do_phan_giai as K
    p = np.round(K.duong_gia(seed, ngay, sigma_pip=sigma_pip, gia0=gia0), 5)
    n = (len(p) - 1) // 60
    m = p[1:1 + n * 60].reshape(n, 60)
    o = np.r_[p[0], m[:-1, -1]]
    return pd.DataFrame(dict(open=o, high=np.maximum(m.max(1), o), low=np.minimum(m.min(1), o), close=m[:, -1], tick_volume=60,
                             spread=int(spread_pts)), index=pd.date_range(bat_dau, periods=n, freq="1min", name="time"))


def tao_ca_tong_hop(exe, seed: int = 1, ngay: float = 2.0, thu_tu_that: str = "cao_truoc", ts: dict | None = None, von: float = 10000.0,
                    f: float = 1.0, spread_pts: int = 20) -> tuple[Ca, pd.DataFrame, pd.DataFrame]:
    """(ca, m1, bang_tester): 'tester' tong hop = EA that (`exe`) chay tren tick sinh tu M1 theo `thu_tu_that` - dap an da biet de thu bo thu."""
    ts = dict(CAU_HINH_NHAY if ts is None else ts)
    m1 = m1_tong_hop(seed, ngay, spread_pts)
    ca0 = Ca(ten="tong_hop_s%d_%s" % (seed, thu_tu_that), ma="AUDCAD", khung="M15", tu=m1.index[0], den_het=m1.index[-1], ngay=max(1, int(round(ngay))),
             von=von, f=f, ts=ts, khoa=None, q=100.0, qc={}, so_khoa=None)
    kq = chay_ea(ca0, m1, BienThe("that", "ea", "M1", thu_tu=thu_tu_that), exe)
    b = kq.bang.drop(columns=["bid_mo", "bid_dong"])
    b["mo"] = pd.to_datetime(b["mo"]).dt.floor("s")
    b["dong"] = pd.to_datetime(b["dong"]).dt.floor("s")
    b["swap"] = 0.0
    ca = dataclasses.replace(ca0, t_truoc=float(b["lai"].sum()), n_t=len(b), so_khoa=(0.0, kq.lai_nam_pct, 0.0, kq.dd_pct, 0.0, float(len(b))))
    return ca, m1, b


def tu_kiem(exe=None, ra=print, thu_tu_that: str = "cao_truoc", seeds=(1, 2, 3), ngay: float = 2.0) -> list[dict]:
    """Chay moi bien the tren du lieu tong hop co dap an (`thu_tu_that`); in bang xep hang va tra cac dong tong hop."""
    exe = exe or bien_dich_ea()
    rows = []
    for s in seeds:
        ca, m1, b = tao_ca_tong_hop(exe, s, ngay, thu_tu_that)
        rows += chay_mot_ca(ca, bien_the_mac_dinh(), exe=exe, m1=m1, bang_tester=b)
    tong = tong_hop(rows)
    ra("tu kiem: dap an = EA tren tick sinh tu M1 theo thu tu '%s' (%d hat x %.0f ngay, cau hinh nhay: %s)" % (thu_tu_that, len(seeds), ngay, CAU_HINH_NHAY))
    in_bang(tong, ra)
    return tong


# ============================================================ 8. DONG LENH
def viet_bao_cao(rows: list[dict], tong: list[dict], duong: Path, bo_qua: dict | None = None) -> None:
    """`reports/bo_thu_mo_phong.md`: bang xep hang + lenh lech dau tien moi ca (mot dong / ca, lay bien the tot nhat)."""
    L = ["# Bo thu mo phong - ket qua (%s)" % time.strftime("%Y-%m-%d %H:%M"), "",
         "Lai TRUOC swap, %/nam. lech_tv = bien the - tester (trung vi); sai_tb = sai so tuyet doi trung binh; khop = ty le lenh ghep duoc.", "",
         "```"]
    in_bang(tong, L.append)
    L.append("```")
    tot = tong[0]["bien_the"] if tong else None
    if tot:
        L += ["", "## Lenh lech dau tien cua bien the tot nhat (%s)" % tot, ""]
        for r in rows:
            if r.get("bien_the") == tot and not r.get("loi"):
                L.append("- %s: khop den %s cua cua so; lech dau = %s; phan ra lech %s" % (
                    r["ca"], r.get("khop_den"), json.dumps(r.get("lech_dau"), ensure_ascii=False), json.dumps(r.get("phan_ra"))))
    loi = [r for r in rows if r.get("loi")]
    if loi:
        L += ["", "## Dong loi (%d)" % len(loi), ""] + ["- %s / %s: %s" % (r["ca"], r["bien_the"], r["loi"]) for r in loi[:30]]
    if bo_qua:
        L += ["", "## Ca bi bo qua (%d)" % len(bo_qua), ""] + ["- %s: %s" % (k, v) for k, v in list(bo_qua.items())[:30]]
    Path(duong).parent.mkdir(parents=True, exist_ok=True)
    Path(duong).write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Bo thu mo phong: so cac phuong an mo phong voi bang lenh MT5 tester that.")
    ap.add_argument("--tu-kiem", action="store_true", help="kiem co dap an tren du lieu tong hop (khong can du lieu that)")
    ap.add_argument("--xong", default="viec/xong")
    ap.add_argument("--gia", default=None, help="thu muc du_lieu_gia (mac dinh: hop thu runner / du_lieu_gia)")
    ap.add_argument("--lenh", default=None, help="thu muc bang lenh tester (mac dinh: <gia>/mau_tester)")
    ap.add_argument("--bien-the", default="tat_ca")
    ap.add_argument("--toi-da", type=int, default=0, help="chi lay N ca dau tien (0 = het)")
    ap.add_argument("--ma", default=None)
    ap.add_argument("--ca-nhiem", action="store_true", help="lay ca o nhiem (chat luong lich su tester < 95%%) - chi de xem, KHONG dung de ket luan")
    ap.add_argument("--luong", type=int, default=1)
    ap.add_argument("--ghi", action="store_true", help="ghi reports/bo_thu_mo_phong.md")
    a = ap.parse_args(argv)
    if a.tu_kiem:
        tu_kiem()
        return 0
    cac, bo = doc_cac_ca(a.xong, chi_sach=not a.ca_nhiem)
    if a.ma:
        cac = [c for c in cac if c.ma == a.ma.upper()]
    thu_gia = Path(a.gia) if a.gia else None
    thu_lenh = Path(a.lenh) if a.lenh else (thu_gia / "mau_tester" if thu_gia else None)
    san_sang = []
    for c in cac:
        try:
            m1 = nap_m1(c.ma, thu_gia)
        except FileNotFoundError:
            bo[c.ten] = "chua co gia M1 cua %s" % c.ma
            continue
        ly = kiem_phu(cat_cua_so(m1, c), c)
        if ly:
            bo[c.ten] = ly
        elif not (thu_lenh or XL.thu_muc_mac_dinh()).joinpath("%s_lenh.csv.gz" % c.khoa).exists():
            bo[c.ten] = "chua co bang lenh tester %s" % c.khoa
        else:
            san_sang.append(c)
    if a.toi_da:
        san_sang = san_sang[:a.toi_da]
    print("ca san sang: %d / %d (bo qua %d)" % (len(san_sang), len(cac), len(bo)))
    for k, v in list(bo.items())[:15]:
        print("  bo qua %s: %s" % (k, v))
    if not san_sang:
        print("chua co ca nao du gia M1 + bang lenh tester: cho may nha day `du_lieu_gia/` (xem viec/cho/00*-xuat-*)")
        return 2
    rows = quet(san_sang, chon_bien_the(a.bien_the), thu_gia, thu_lenh, luong=a.luong, ra=print)
    tong = tong_hop(rows)
    in_bang(tong)
    if a.ghi:
        viet_bao_cao(rows, tong, GOC / "reports" / "bo_thu_mo_phong.md", bo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
