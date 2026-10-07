# -*- coding: utf-8 -*-
"""hang_hoa.py - NHANH HANG HOA (chu du an 05/10/2026: "giao dich hang hoa co chu ky va song ro rang hon").

Cloud KHONG co gia san MT5, nhung gia NGAY hang hoa la du lieu cong khai. Module nay co hai nua:
  1. LAY + NHO (`tai`, `doc`): Stooq (hop dong lien tuc `cl.f`, `ng.f`, `gc.f`, `si.f`, `hg.f`, `zc.f`, `zw.f`, `zs.f`, `kc.f`, `sb.f`, `ct.f`),
     FRED (`DCOILWTICO`, `DHHNGASP`, `GOLDAMGBD228NLBM` ... va chi so kinh te: `CPIAUCSL`, `UNRATE`) -> `du_lieu_hh/<ten>.csv.gz`
     (cong khai, nho, vao git duoc). Mang cloud phai MO ten mien (stooq.com, fred.stlouisfed.org); chua mo thi `tai` bao loi RO, khong im lang.
  2. PHAN TICH (`mua_vu_ngay`, `chu_ky`, `ibs_ngay`): gia THUC hay tong hop deu duoc. Moi phep co NULL hoan vi va ba trang thai (DAT/AM/CHUA_DO_DUOC).
Bay da sap that: gia lien tuc Stooq la hop dong NOI -> khoang trong cuon (roll) KHONG phai loi nhuan; chi dung loi suat log hang ngay, khong dung gia tuyet doi.
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent.parent
THU_MUC = GOC / "du_lieu_hh"
STOOQ = "https://stooq.com/q/d/l/?s=%s&i=d"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s"
HANG_HOA = {"dau_wti": "cl.f", "khi_tu_nhien": "ng.f", "vang": "gc.f", "bac": "si.f", "dong": "hg.f", "ngo": "zc.f",
            "lua_mi": "zw.f", "dau_tuong": "zs.f", "ca_phe": "kc.f", "duong": "sb.f", "bong": "ct.f", "dau_nhien_lieu": "ho.f"}


def tai(ten: str, nguon: str = "stooq", ma: str | None = None, thu_muc: Path = THU_MUC, get=None) -> Path:
    """Tai MOT chuoi ngay ve csv.gz (cot: open high low close volume voi Stooq; `value` voi FRED). Loi mang -> RuntimeError ro ten mien."""
    if get is None:
        import requests

        def get(u):
            r = requests.get(u, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return r.text
    ma = ma or HANG_HOA.get(ten, ten)
    url = (STOOQ if nguon == "stooq" else FRED) % ma
    try:
        txt = get(url)
    except Exception as e:                      # noqa: BLE001
        raise RuntimeError("khong tai duoc %s tu %s (mang cloud co mo ten mien nay chua?): %s" % (ten, url.split("/")[2], e)) from e
    if len(txt) < 50 or "<html" in txt[:200].lower() or txt.lstrip().lower().startswith("no data"):
        raise RuntimeError("%s tra ve khong phai CSV (%d byte): %r" % (url.split("/")[2], len(txt), txt[:60]))
    df = pd.read_csv(io.StringIO(txt))
    df.columns = [c.strip().lower() for c in df.columns]
    cot_ngay = "date" if "date" in df.columns else df.columns[0]
    df[cot_ngay] = pd.to_datetime(df[cot_ngay])
    df = df.set_index(cot_ngay).sort_index()
    df.index.name = "date"
    df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
    thu_muc.mkdir(parents=True, exist_ok=True)
    f = thu_muc / ("%s.csv.gz" % ten)
    df.to_csv(f, compression="gzip", float_format="%.6g")
    return f


YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=0&period2=%d&interval=1d"
YAHOO_MA = {"dau_wti": "CL=F", "khi_tu_nhien": "NG=F", "vang": "GC=F", "bac": "SI=F", "dong": "HG=F", "ngo": "ZC=F", "lua_mi": "ZW=F",
            "dau_tuong": "ZS=F", "ca_phe": "KC=F", "duong": "SB=F", "bong": "CT=F", "dau_nhien_lieu": "HO=F", "dau_brent": "BZ=F"}


def tai_yahoo(ten: str, thu_muc: Path = THU_MUC, get=None, ma: str | None = None) -> Path:
    """Gia NGAY day du (period1=0: `range=max` bi Yahoo gop thanh THANG - bay da gap 05/10) tu Yahoo chart API. Can User-Agent. Loi / 429 -> RuntimeError."""
    import json
    import time
    if get is None:
        import requests

        def get(u):
            for lan in range(4):
                r = requests.get(u, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 429:
                    time.sleep(5 * (lan + 1)); continue
                r.raise_for_status()
                return r.text
            raise RuntimeError("Yahoo 429 lien tuc")
    ma = ma or YAHOO_MA[ten]
    url = YAHOO % (ma, int(time.time()))
    try:
        j = json.loads(get(url))["chart"]["result"][0]
    except Exception as e:                      # noqa: BLE001
        raise RuntimeError("khong tai duoc %s tu query1.finance.yahoo.com: %s" % (ten, e)) from e
    q = j["indicators"]["quote"][0]
    df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close", "volume")},
                      index=pd.to_datetime(j["timestamp"], unit="s").normalize())
    df.index.name = "date"
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["close"]).sort_index()
    thu_muc.mkdir(parents=True, exist_ok=True)
    f = thu_muc / ("%s.csv.gz" % ten)
    df.to_csv(f, compression="gzip", float_format="%.6g")
    return f


def doc(ten: str, thu_muc: Path = THU_MUC) -> pd.DataFrame:
    return pd.read_csv(Path(thu_muc) / ("%s.csv.gz" % ten), index_col="date", parse_dates=True)


def _log_ret(df: pd.DataFrame) -> pd.Series:
    c = df["close"] if "close" in df.columns else df.iloc[:, 0]
    return np.log(c.where(c > 0)).diff().dropna()


def mua_vu_ngay(df: pd.DataFrame, cua_so_ngay: int = 15, so_null: int = 500, hat: int = 0) -> dict:
    """Co MUA VU theo ngay-trong-nam khong? Cua so truot `cua_so_ngay` ngay lich: loi suat trung binh cua tung cua so, qua cac NAM.
    NULL = hoan vi nhan NAM-roi-ngay (xao tron nhan ngay-trong-nam giua cac ngay, giu nguyen phan bo loi suat) -> cuc tri cua ~24 cua so da duoc tinh.
    Tra `tot_nhat` (cua so, loi suat bps/ngay, ti le nam cung dau), `p` (cuc tri), `trang_thai` DAT (p<0,05 va >=70% nam cung dau) / AM / CHUA_DO_DUOC (<8 nam)."""
    r = _log_ret(df)
    nam = r.index.year.nunique()
    if nam < 8:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "chi %d nam (<8)" % nam}
    doy = r.index.dayofyear.values
    bin_ = np.minimum((doy - 1) // cua_so_ngay, 24)
    def cuc_tri(nhan):
        m = pd.Series(r.values).groupby(nhan).mean().values
        return np.abs(m - m.mean()).max()
    thuc = cuc_tri(bin_)
    rng = np.random.default_rng(hat)
    cao = sum(cuc_tri(rng.permutation(bin_)) >= thuc for _ in range(so_null))
    p = (cao + 1) / (so_null + 1)
    m = pd.Series(r.values, index=r.index).groupby(bin_).mean()
    k = int((m - m.mean()).abs().idxmax())
    cung = []
    for _, g in pd.Series(r.values, index=r.index).groupby(r.index.year):
        gb = g[np.minimum((g.index.dayofyear.values - 1) // cua_so_ngay, 24) == k]
        if len(gb) > 2: cung.append(np.sign(gb.mean()) == np.sign(m.loc[k]))
    ty_le = float(np.mean(cung)) if cung else 0.0
    return {"trang_thai": "DAT" if (p < 0.05 and ty_le >= 0.70) else "AM", "cua_so": k, "ngay_bat_dau_nam": k * cua_so_ngay + 1,
            "loi_suat_bps_ngay": round(float(m.loc[k]) * 1e4, 2), "ty_le_nam_cung_dau": round(ty_le, 2), "p": round(p, 4), "so_nam": int(nam)}


def chu_ky(df: pd.DataFrame, chu_ky_toi_thieu: int = 10, chu_ky_toi_da: int = 400, so_null: int = 300, hat: int = 0) -> dict:
    """Co CHU KY ro khong? Pho Fourier cua loi suat log; dinh cao nhat trong [min,max] ngay so voi NULL hoan vi (pha ngau nhien: giu pho
    bien do -> khong, nen null la xao tron thu tu loi suat). DAT = dinh vuot null 95% (da tinh cuc tri qua cac tan so)."""
    r = _log_ret(df).values
    n = len(r)
    if n < 4 * chu_ky_toi_da:
        return {"trang_thai": "CHUA_DO_DUOC", "ly_do": "chi %d ngay (<%d)" % (n, 4 * chu_ky_toi_da)}
    def dinh(x):
        p = np.abs(np.fft.rfft(x - x.mean())) ** 2
        f = np.fft.rfftfreq(len(x))
        ck = np.where(f > 0, 1 / np.maximum(f, 1e-12), np.inf)
        ok = (ck >= chu_ky_toi_thieu) & (ck <= chu_ky_toi_da)
        p = p[ok]; ck = ck[ok]
        i = int(np.argmax(p))
        return p[i] / p.sum(), ck[i]
    thuc, ck = dinh(r)
    rng = np.random.default_rng(hat)
    nul = np.array([dinh(rng.permutation(r))[0] for _ in range(so_null)])
    p = (np.sum(nul >= thuc) + 1) / (so_null + 1)
    return {"trang_thai": "DAT" if p < 0.05 else "AM", "chu_ky_ngay": round(float(ck), 1), "ty_trong_pho": round(float(thuc), 4), "p": round(float(p), 4)}


def ibs_ngay(df: pd.DataFrame, nguong: float = 0.2, giu: int = 1, chi_phi_bps: float = 2.0, huong: int = 1) -> dict:
    """IBS = (close-low)/(high-low). Vao cuoi ngay khi IBS < nguong (huong=1 mua) hoac > 1-nguong (huong=-1 ban), giu `giu` ngay, tru phi 2 chieu.
    Tra so lenh, ky vong bps/lenh, ti le thang, t-stat. KHONG co null o day: dung `nhan/cong.py` / niem phong cho ket luan; day la phep do nhanh."""
    d = df.dropna(subset=["high", "low", "close"])
    rng_ = (d["high"] - d["low"]).replace(0, np.nan)
    ibs = (d["close"] - d["low"]) / rng_
    kich = (ibs < nguong) if huong == 1 else (ibs > 1 - nguong)
    fwd = np.log(d["close"].shift(-giu) / d["close"]) * huong
    x = (fwd[kich].dropna() * 1e4) - chi_phi_bps
    n = int(len(x))
    if n < 30:
        return {"trang_thai": "CHUA_DO_DUOC", "so_lenh": n}
    t = float(x.mean() / (x.std(ddof=1) / np.sqrt(n))) if x.std(ddof=1) > 0 else 0.0
    return {"trang_thai": "DAT" if x.mean() > 0 else "AM", "so_lenh": n, "ky_vong_bps": round(float(x.mean()), 2),
            "ti_le_thang": round(float((x > 0).mean()), 3), "t": round(t, 2)}
