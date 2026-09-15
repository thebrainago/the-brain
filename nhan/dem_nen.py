# -*- coding: utf-8 -*-
"""dem_nen.py - BO DEM NEN: mot tai san co hinh dang nen nhu the nao.

Chu du an 15/09/2026: *"dem mau nen (nen co 1 bo dem nen thuong va 1 bo nen Ha
va cac loai nen khac)"*, trong muc *"ngay khi so vao 1 loai tai san nao it nhat
toi phai biet no co tinh chat sw hay trend"*.

## Vi sao dem nen noi duoc dieu do

Ba con so o day tra loi thang cau hoi HOI QUY hay XU HUONG, va chung doc duoc
ma khong can mot mo hinh nao:

  **chuoi lien tiep** - so nen cung mau lien nhau. Mot tai san xu huong keo
  chuoi dai hon dang ke so voi tung dong xu; mot tai san hoi quy thi chuoi
  ngan hon (mau doi lien tuc). So sanh voi ky vong cua chuoi ngau nhien cung ty
  le tang/giam la phep thu, khong phai cam giac.

  **ty le than/bien do** - nen than day la nen di dut khoat; nen than mong
  nhieu rau la nen do du. Ty le nay tren HA cao hon han tren nen thuong o tai
  san xu huong.

  **doji / dao chieu** - mat do nen than gan bang khong.

## HEIKIN-ASHI: CHI DE DOC HINH DANG

`nhan/nen.py` da chot: **gia HA khong phai gia mua ban duoc**. O day ta chi DEM
chung de mo ta tinh cach - khong mot con so nao trong file nay duoc dung lam
gia vao/ra. HA lam muot nen chuoi HA luon DAI HON chuoi thuong; do la dac tinh
cua phep bien doi, khong phai cua thi truong, nen hai bo dem luon di CUNG NHAU
va khong bao gio so cheo.

## MOC NGAU NHIEN, khong phai cam giac

Chuoi trung binh cua mot chuoi Bernoulli doc lap voi ty le tang `p` la
`1/(1-p)` cho chuoi tang. In ca hai de doc duoc "dai hon ngau nhien bao nhieu".
Khong co moc do thi mot con so nhu "chuoi tang trung binh 2,1 nen" khong noi
len dieu gi.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))


def _chuoi_lien_tiep(dau: np.ndarray) -> dict:
    """Do dai cac chuoi cung dau. `dau` la mang -1/0/+1."""
    ra = {"tang": [], "giam": []}
    hien, dai = 0, 0
    for x in dau:
        if x == 0:
            # NEN THAN BANG KHONG CAT CHUOI, khong phai bo qua.
            #
            # Ban dau toi cho `continue` - tuc mot doji o giua noi lien hai
            # chuoi cung mau thanh mot chuoi dai. Nhung cau hoi la "may nen
            # CUNG MAU lien nhau", va doji khong mang mau nao. Bo qua no lam
            # chuoi dai len mot cach he thong tren dung nhung tai san nhieu
            # doji - tuc lam lech chinh phep so sanh giua cac ma.
            if hien:
                ra["tang" if hien > 0 else "giam"].append(dai)
            hien, dai = 0, 0
            continue
        if x == hien:
            dai += 1
        else:
            if hien:
                ra["tang" if hien > 0 else "giam"].append(dai)
            hien, dai = x, 1
    if hien:
        ra["tang" if hien > 0 else "giam"].append(dai)
    return ra


def _tk(a: list) -> dict:
    v = np.asarray(a, float)
    if not len(v):
        return {"so": 0}
    return {"so": int(len(v)), "trung_binh": round(float(np.mean(v)), 3),
            "trung_vi": float(np.median(v)), "p90": float(np.percentile(v, 90)),
            "dai_nhat": int(np.max(v))}


def dem(df: pd.DataFrame, kieu: str = "thuong") -> dict:
    """Bo dem cho MOT loai nen. `kieu`: "thuong" | "ha"."""
    from nhan import nen as NEN
    k = NEN.bien_doi(df, kieu)
    o = k["open"].to_numpy(float)
    h = k["high"].to_numpy(float)
    l = k["low"].to_numpy(float)
    c = k["close"].to_numpy(float)
    than = c - o
    bien = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        ty_than = np.where(bien > 0, np.abs(than) / bien, np.nan)
    dau = np.sign(than)
    n = int(np.sum(dau != 0))
    p_tang = float(np.sum(dau > 0)) / max(n, 1)

    ch = _chuoi_lien_tiep(dau)
    # Moc ngau nhien: chuoi trung binh cua Bernoulli doc lap.
    moc_tang = 1.0 / max(1.0 - p_tang, 1e-9)
    moc_giam = 1.0 / max(p_tang, 1e-9)
    tk_t, tk_g = _tk(ch["tang"]), _tk(ch["giam"])
    return {
        "kieu": kieu, "so_nen": int(len(k)),
        "ty_le_tang_pct": round(100 * p_tang, 2),
        "than_tren_bien_do": {
            "trung_vi": round(float(np.nanmedian(ty_than)), 4),
            "p75": round(float(np.nanpercentile(ty_than, 75)), 4)},
        "doji_pct": round(100 * float(np.nanmean(ty_than < 0.1)), 2),
        "chuoi_tang": tk_t, "chuoi_giam": tk_g,
        "chuoi_tang_ngau_nhien": round(moc_tang, 3),
        "chuoi_giam_ngau_nhien": round(moc_giam, 3),
        # >1 = chuoi DAI HON ngau nhien -> nghieng XU HUONG.
        # <1 = chuoi NGAN HON ngau nhien -> nghieng HOI QUY (mau doi lien tuc).
        "hon_ngau_nhien_tang": round(tk_t.get("trung_binh", 0) / moc_tang, 3)
                               if tk_t.get("so") else None,
        "hon_ngau_nhien_giam": round(tk_g.get("trung_binh", 0) / moc_giam, 3)
                               if tk_g.get("so") else None,
    }


def ho_so(ma: str, khung: str = "D1") -> dict:
    from nhan import du_lieu as DL
    df = DL.nap(ma, khung)
    ra = {"ma": ma, "khung": khung, "so_bar": int(len(df)),
          "tu": str(df.index[0].date()), "den": str(df.index[-1].date()),
          "bo_dem": {k: dem(df, k) for k in ("thuong", "ha")}}
    t = ra["bo_dem"]["thuong"]
    x = [t["hon_ngau_nhien_tang"], t["hon_ngau_nhien_giam"]]
    x = [v for v in x if v is not None]
    tb = float(np.mean(x)) if x else 1.0
    ra["nghieng"] = ("XU_HUONG" if tb >= 1.05 else
                     "HOI_QUY" if tb <= 0.95 else "TRUNG_TINH")
    ra["hon_ngau_nhien_tb"] = round(tb, 3)
    return ra


def in_ra(h: dict) -> str:
    d = ["=== DEM NEN %s (%s) - %d bar, %s -> %s ==="
         % (h["ma"], h["khung"], h["so_bar"], h["tu"], h["den"])]
    for k in ("thuong", "ha"):
        b = h["bo_dem"][k]
        d.append("  nen %-7s tang %5.2f%% | than/bien do %.3f | doji %.2f%%"
                 % (k, b["ty_le_tang_pct"], b["than_tren_bien_do"]["trung_vi"],
                    b["doji_pct"]))
        for chieu in ("tang", "giam"):
            t = b["chuoi_" + chieu]
            if not t.get("so"):
                continue
            d.append("     chuoi %-4s tb %.2f nen (ngau nhien %.2f -> **%.3f "
                     "lan**) | dai nhat %d"
                     % (chieu, t["trung_binh"], b["chuoi_%s_ngau_nhien" % chieu],
                        b["hon_ngau_nhien_" + chieu] or 0, t["dai_nhat"]))
    d.append("  -> nghieng **%s** (chuoi dai hon ngau nhien %.3f lan)"
             % (h["nghieng"], h["hon_ngau_nhien_tb"]))
    d.append("  (nen HA luon cho chuoi DAI HON - do la dac tinh cua phep bien "
             "doi, khong phai cua thi truong. Dung so cheo hai bo dem.)")
    return "\n".join(d)


if __name__ == "__main__":
    ma = sys.argv[1] if len(sys.argv) > 1 else "AUDCAD"
    khung = sys.argv[2] if len(sys.argv) > 2 else "D1"
    print(in_ra(ho_so(ma, khung)))
