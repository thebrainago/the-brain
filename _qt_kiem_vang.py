# -*- coding: utf-8 -*-
"""_qt_kiem_vang.py - KIEM cai dau hieu "trailing tren vang" cho den khi no chet
hoac song.

## Dau hieu dang kiem

Bang 11 ho quan tri (14/09/2026, 61 ma co chi phi do duoc, D1) sau khi bo hai ao
giac (cap chet + xep hang thuong cho duong von sat 0) con lai mot thu:

    XAUUSD  trailing 1,5/2,0   5,87%/nam  sut giam -23,2%  hon mua-giu +4,70%
    XAUUSD  trailing 1,0/2,0   4,85%/nam  sut giam -27,3%  hon mua-giu +3,68%
    XM_GOLD trailing 1,0/2,0   4,78%/nam  sut giam -26,0%  hon mua-giu +3,76%
    ... vang chiem 8/12 o sach tot nhat

Do moi la DAU HIEU. File nay hoi ba cau con thieu, va moi cau deu co the giet no:

    1. NUA SAU  - luat chon tren nua dau co con dung o nua sau khong?
    2. PLACEBO  - tren gia DAO DAU va gia XAO KHOI no co con lai khong?
                  (neu con -> no khong khai thac gi cua vang, no an drift)
    3. HANG XOM - vang co that su khac cac tai san khac, hay moi tai san deu vay
                  va ta chi dang nhin mot cai gai?

Ba cau nay deu tra loi bang chinh `dap_quan_tri` + `vao_lenh`, khong dung engine
moi nao - co y, de ket qua doi chieu duoc voi bang goc.

Chay:  python _qt_kiem_vang.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import dap_quan_tri as DQ     # noqa: E402
from nhan import du_lieu as DU          # noqa: E402
from _quet_quan_tri_python import tin_hieu_donchian, SL_CUNG, GIU_TOI_DA  # noqa: E402

#: Vang + anh em ho. Va mot nhom DOI CHUNG khac lop tai san hoan toan.
VANG = ["XAUUSD", "XM_GOLD", "XAUUSDM", "XM_SILVER"]
DOI_CHUNG = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XM_US500CASH",
             "XM_US100CASH", "XM_GER40CASH", "AUDCAD", "EURGBP", "NZDCAD"]

#: Luoi quanh cac o dan dau. Giu nho: day la buoc KIEM, khong phai buoc do.
LUOI = {}
for x in (0.5, 1.0, 1.5, 2.0):
    for y in (0.5, 1.0, 2.0):
        LUOI["trailing|%.1f|%.1f" % (x, y)] = {
            "sl_atr": SL_CUNG, "trail_tu_atr": x, "trail_buoc": y}


# ------------------------------------------------------------------ PLACEBO
def gia_dao_dau(df: pd.DataFrame) -> pd.DataFrame:
    """Doi dau loi suat, phan chieu hinh hoc tung nen. Giet DRIFT, giu phan con lai."""
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float);  c = df["close"].to_numpy(float)
    tren = h / np.maximum(o, c) - 1.0
    duoi = 1.0 - l / np.minimum(o, c)
    moi_c = c[0] * np.exp(np.cumsum(-np.diff(np.log(c), prepend=np.log(c[0]))))
    moi_o = np.r_[o[0], moi_c[:-1]]
    tran, san = np.maximum(moi_o, moi_c), np.minimum(moi_o, moi_c)
    return pd.DataFrame({"open": moi_o, "high": tran * (1 + duoi),
                         "low": san * (1 - tren), "close": moi_c}, index=df.index)


def gia_xao_khoi(df: pd.DataFrame, hat: int = 4242) -> pd.DataFrame:
    """Xao khoi loi suat: giet tu tuong quan, GIU cum bien dong."""
    rng = np.random.default_rng(hat)
    c = df["close"].to_numpy(float)
    lr = np.diff(np.log(c))
    n = len(lr)
    k = max(10, int(round(n ** (1 / 3))))
    dau = rng.integers(0, max(1, n - k), size=int(np.ceil(n / k)))
    idx = (dau[:, None] + np.arange(k)[None, :]).reshape(-1)[:n]
    moi_c = np.r_[c[0], c[0] * np.exp(np.cumsum(lr[np.clip(idx, 0, n - 1)]))]
    moi_o = np.r_[df["open"].to_numpy(float)[0], moi_c[:-1]]
    ban_do = np.nan_to_num(((df["high"] - df["low"]) / df["close"]).to_numpy(float))
    nua = moi_c * ban_do / 2.0
    giua = (moi_o + moi_c) / 2.0
    return pd.DataFrame({"open": moi_o,
                         "high": np.maximum(np.maximum(moi_o, moi_c), giua + nua),
                         "low": np.minimum(np.minimum(moi_o, moi_c), giua - nua),
                         "close": moi_c}, index=df.index)


# ------------------------------------------------------------------- MOT MA
def do_mot(ma: str, khung: str = "D1", doan: str = "het") -> list[dict]:
    """`doan`: het | train (60% dau) | holdout (40% sau)."""
    try:
        df = DU.nap(ma, khung)
    except Exception:
        return []
    if len(df) < 900:
        return []
    if doan == "train":
        df = df.iloc[: int(len(df) * 0.6)]
    elif doan == "holdout":
        df = df.iloc[int(len(df) * 0.6):]
    th = tin_hieu_donchian(df)
    if abs(th).sum() < 30:
        return []
    try:
        ds = DQ.so_luat(df, th, ma, khung, LUOI, giu_toi_da=GIU_TOI_DA)
    except Exception:
        return []
    for r in ds:
        r["doan"] = doan
        r["hon_moc_diem"] = round(r["cagr_dd20"] - r["moc_dd20"], 3)
    return ds


def do_placebo(ma: str, khung: str = "D1") -> dict:
    try:
        df = DU.nap(ma, khung)
    except Exception:
        return {}
    if len(df) < 900:
        return {}
    ra = {}
    for ten, ham in (("that", lambda d: d), ("dao_dau", gia_dao_dau),
                     ("xao_khoi", gia_xao_khoi)):
        dg = ham(df)
        th = tin_hieu_donchian(dg)
        if abs(th).sum() < 30:
            continue
        try:
            ds = DQ.so_luat(dg, th, ma, khung, LUOI, giu_toi_da=GIU_TOI_DA)
        except Exception:
            continue
        if ds:
            ra[ten] = float(np.median([r["hon_moc_diem"] if "hon_moc_diem" in r
                                       else r["cagr_dd20"] - r["moc_dd20"]
                                       for r in ds]))
    return ra


def _tv(ds, khoa="hon_moc_diem"):
    v = [r[khoa] for r in ds]
    return float(np.median(v)) if v else float("nan")


def main() -> int:
    t0 = time.time()
    khung = "D1"
    ra: dict = {"khung": khung, "luoi": list(LUOI), "vang": {}, "doi_chung": {}}

    print("=" * 96)
    print("CAU 1 + 3 — nua dau / nua sau, va vang co khac hang xom khong")
    print("=" * 96)
    print(f"{'ma':<16}{'nhom':<10}{'het':>10}{'nua dau':>10}{'nua sau':>10}"
          f"{'o duong':>10}{'so o':>7}")
    print("-" * 96)
    for nhom, cac_ma in (("VANG", VANG), ("doi chung", DOI_CHUNG)):
        for ma in cac_ma:
            het = do_mot(ma, khung, "het")
            if not het:
                continue
            tr = do_mot(ma, khung, "train")
            ho = do_mot(ma, khung, "holdout")
            d = {"het": _tv(het), "train": _tv(tr), "holdout": _tv(ho),
                 "so_o": len(het),
                 "ty_le_duong": round(sum(1 for r in het
                                          if r["hon_moc_diem"] > 0) / len(het), 3)}
            ra["vang" if nhom == "VANG" else "doi_chung"][ma] = d
            print(f"{ma:<16}{nhom:<10}{d['het']:>9.2f}%{d['train']:>9.2f}%"
                  f"{d['holdout']:>9.2f}%{100*d['ty_le_duong']:>9.0f}%{d['so_o']:>7}")

    print()
    print("=" * 96)
    print("CAU 2 — PLACEBO: tren gia gia no co con lai khong")
    print("=" * 96)
    print(f"{'ma':<16}{'that':>10}{'dao dau':>10}{'xao khoi':>10}  ket luan")
    print("-" * 96)
    for ma in VANG + DOI_CHUNG[:4]:
        p = do_placebo(ma, khung)
        if not p or "that" not in p:
            continue
        ra.setdefault("placebo", {})[ma] = p
        ban = [v for k, v in p.items() if k != "that"]
        # PHAI DUONG DA roi moi xet chuyen tach. Khong co ve dau nay thi mot ma
        # LO (-0,52%) van "tach khoi placebo" chi vi placebo con lo hon - va
        # bang se ghi PASS cho mot thu dang mat tien. Da sap dung vay voi GBPUSD.
        tach = bool(ban) and p["that"] > 0 and all(p["that"] > v for v in ban)
        print(f"{ma:<16}{p['that']:>9.2f}%"
              f"{p.get('dao_dau', float('nan')):>9.2f}%"
              f"{p.get('xao_khoi', float('nan')):>9.2f}%"
              f"  {'TACH khoi placebo' if tach else 'khong tach - nghi an drift'}")

    ra["giay"] = round(time.time() - t0, 1)
    (LAB / "reports" / "QT_KIEM_VANG.json").write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> reports/QT_KIEM_VANG.json ({ra['giay']:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
