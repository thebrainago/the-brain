# -*- coding: utf-8 -*-
"""doi_khung.py - CHUYEN MOT CO CHE SANG KHUNG KHAC MA NO VAN LA CHINH NO.

Chu du an 07/09/2026: *"Sau nay chuyen khung can sua co che... do nhieu lon hon
se can phai nang thong so len cao hon."* Va: *"Khi nao xay duoc bo chuyen doi
timeframe muot va hieu qua thi thoi."*

## VI SAO BAN CU HONG

`_da_khung.doi_khung` chi nhan tham so CHU KY theo ti le bar. Do 07/09, be 36
chan chon tren D1 sang khung khac chi bang phep do:

    W1  12/36 chan duong, tong lai  -1.471
    H4  21/36,             tong lai  +6.420
    H1   6/36,             tong lai  -4.739

Nhan chu ky giu duoc **khoang THOI GIAN** (`sma(5)` tren D1 = mot tuan, tren H4
la `sma(30)` = cung mot tuan) nhung khong giu duoc **do HIEM cua su kien**. Nhieu
tren khung nho lon hon, nen cung nguong `zscore < -1,0` kich hoat nhieu hon han
va phan lon la nhieu.

## HAI TRUC, HAI PHEP KHAC NHAU

    tham so CHU KY  (`n`, `giu`)  ->  nhan theo TI LE BAR DO DUOC
    tham so NGUONG  (`hang`)      ->  KHOP PHAN VI

Ti le bar **do tu chinh du lieu**, khong gia dinh: D1 -> H4 tren US100Cash la
5,95 chu khong phai 6 (nen D1 cua CFD om ~23 gio, va lich phien khong deu).

Khop phan vi la phep dung cho nguong: neu `zscore(5) < -1,0` xay ra o **19,6%**
so nen tren D1, thi tren H4 ta tim `h'` sao cho `zscore(30) < h'` cung xay ra o
19,6% so nen. Khong can biet tham so mang y nghia gi, nen no chay duoc cho MOI
chi bao - va do la cung mot nguyen tac `ngoai_sinh.chuyen` dung khi doi TAI SAN
(**giu ty le kich hoat, khong giu con so**), chi khac truc.

## VI SAO PHAI CO BUOC HAI: HIEU CHINH GOP

Khop tung ve giu duoc xac suat BIEN cua moi ve, nhung co che nhieu dieu kien thi
cai quyet dinh la xac suat **DONG THOI**, va no khong bang tich cac bien. Do
07/09 tren `rsi_mua_qua_ban` (hai ve): ty le goc 0,0318 -> chi nhan chu ky
**0,0053** (hut 6 lan) -> khop tung ve **0,0897** (vot 2,8 lan). Ca hai deu sai,
theo hai huong nguoc nhau.

Buoc hai: **do mot he so chung `d` len xac suat cua MOI ve** roi do nhi phan `d`
sao cho ty le kich hoat GOP khop ban goc. Ty le gop don dieu theo `d`, va vi
`d` la MOT so nen phep hieu chinh khong them bac tu do dang ke - khac han voi
viec do tim tung nguong (do la khop tham so tra hinh).

## BA CHOT CHAN

1. **Do phan vi tren TRAIN cua ca hai ben.** Do tren ca chuoi la nhin truoc.
2. **Chuyen KHONG phai mot PASS moi.** He chuyen sang khung khac la mot GIA
   THUYET MOI, phai di lai tu dau qua cong.
3. **Bao ca ty le kich hoat TRUOC va SAU.** Neu sau khi doi ma ty le lech xa
   thi phep chuyen that bai - phai noi ra chu khong tra ve mot spec im lang.
"""
from __future__ import annotations

import copy
import math

import numpy as np
import pandas as pd

from . import du_lieu, ngu_phap as NP

#: Ten trong kho parquet vs ten trong MT5. `du_lieu.kho()` goi la
#: `XM_US100CASH`, MT5 goi la `US100Cash` - va kho parquet **khong co H4/H1**
#: cho ma nay (chi D1 va M5 1,4 nam), trong khi MT5 co H4/H1 tu 2016. Nen bo doi
#: khung phai lay duoc tu CA HAI nguon, khong the phu thuoc mot cai.
_MT5_KHUNG = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 16385, "H4": 16388,
              "D1": 16408, "W1": 32769, "MN1": 49153}


def nap_khung(ma: str, khung: str, tu: str | None = None,
              den: str | None = None) -> "pd.DataFrame | None":
    """Nap OHLC: uu tien kho parquet, thieu thi hoi thang MT5.

    Tra `None` neu ca hai deu khong co - de nguoi goi bao "chua do duoc" chu
    khong tra mot khung rong roi ket luan am [[ket-luan-am-phai-phan-biet-chua-do]].
    """
    try:
        df = du_lieu.nap(ma, khung, tu, den)
        if df is not None and len(df) >= 50:
            return df
    except Exception:
        pass
    ten_mt5 = ma.split("_", 1)[1] if ma.startswith("XM_") else ma
    # `XM_US100CASH` -> `US100CASH`; MT5 dung `US100Cash`. Thu ca hai dang.
    ung = [ten_mt5, ten_mt5.title().replace("Cash", "Cash"), ma]
    if ten_mt5.upper().endswith("CASH"):
        ung.insert(0, ten_mt5[:-4].upper() + "Cash")
    try:
        import MetaTrader5 as mt5
    except Exception:
        return None
    if not mt5.initialize():
        return None
    try:
        import datetime as dt
        t0 = pd.Timestamp(tu or "2010-01-01").to_pydatetime()
        t1 = pd.Timestamp(den or "2027-01-01").to_pydatetime()
        tf = _MT5_KHUNG.get(khung)
        for ten in ung:
            if not mt5.symbol_select(ten, True):
                continue
            r = None
            for _ in range(4):
                r = mt5.copy_rates_range(ten, tf, t0, t1)
                if r is not None and len(r) > 50:
                    break
            if r is None or len(r) <= 50:
                continue
            df = pd.DataFrame(r)
            df["time"] = pd.to_datetime(df["time"], unit="s")
            df = df.set_index("time")
            df = df.rename(columns={"tick_volume": "volume"})
            return df[[c for c in ("open", "high", "low", "close", "volume",
                                   "spread") if c in df.columns]]
    finally:
        mt5.shutdown()
    return None

#: Phep so sanh -> huong duoi/tren khi tinh phan vi.
DUOI = {"<", "<="}
TREN = {">", ">="}


def ti_le_bar(df_goc: pd.DataFrame, df_dich: pd.DataFrame) -> float:
    """So bar cua khung dich tren MOT bar khung goc, do tu du lieu that.

    Khong gia dinh D1->H4 = 6: nen D1 cua CFD chi so om ~23 gio va lich phien
    khong deu, do that tren US100Cash ra **5,95**.
    """
    if len(df_goc) < 2 or len(df_dich) < 2:
        return 1.0
    return max(0.05, len(df_dich) / len(df_goc))


def _doi_chu_ky(nut, hs: float):
    """Nhan moi `n` va `giu` theo he so; giu nguyen moi `hang`."""
    if isinstance(nut, dict):
        ra = {}
        for k, v in nut.items():
            if k == "n" and isinstance(v, (int, float)) and not isinstance(v, bool):
                ra[k] = max(2, int(round(v * hs)))
            elif k == "hang":
                ra[k] = v
            else:
                ra[k] = _doi_chu_ky(v, hs)
        return ra
    if isinstance(nut, list):
        return [_doi_chu_ky(x, hs) for x in nut]
    return nut


def _cac_nguong(ds: list) -> list[tuple]:
    """Tra [(dieu_kien, ben_co_hang, ben_kia)] cho moi so sanh co hang so."""
    ra = []
    for d in ds or []:
        if not isinstance(d, dict) or "phep" not in d:
            continue
        for ben, kia in (("phai", "trai"), ("trai", "phai")):
            a, b = d.get(ben), d.get(kia)
            if isinstance(a, dict) and "hang" in a and isinstance(b, dict) \
                    and "hang" not in b:
                ra.append((d, ben, kia))
    return ra


def _chuoi(df: pd.DataFrame, toan: dict) -> np.ndarray | None:
    try:
        s = NP.toan_hang(df, toan)
    except Exception:
        return None
    if s is None:
        return None
    v = pd.Series(s).astype(float).to_numpy()
    v = v[np.isfinite(v)]
    return v if v.size >= 30 else None


def _lam_tron(x: float, mau: float) -> float:
    """Lam tron theo do lon cua chinh no - de spec doc duoc, khong ra 1,0000003."""
    if not math.isfinite(x):
        return float(mau)
    d = abs(x)
    if d >= 1000:
        return round(x, 0)
    if d >= 10:
        return round(x, 1)
    if d >= 1:
        return round(x, 2)
    return round(x, 4)


def doi(spec: dict, ma: str, khung_goc: str, khung_dich: str,
        tu: str | None = None, den: str | None = None,
        df_goc=None, df_dich=None) -> dict:
    """Tra {'spec': spec moi, 'hs': ti le bar, 'nguong': [...], 'kich_hoat': {...}}.

    `tu`/`den` phai la doan TRAIN. Do phan vi tren ca chuoi la nhin truoc.

    `df_goc`/`df_dich`: truyen san khung du lieu de doi CA KHO ma khong nap lai
    - 84 co che x 2 lan nap tu MT5 la vai phut, con nap mot lan la vai giay.
    """
    df_g = df_goc if df_goc is not None else nap_khung(ma, khung_goc, tu, den)
    df_d = df_dich if df_dich is not None else nap_khung(ma, khung_dich, tu, den)
    if df_g is None or df_d is None or len(df_g) < 50 or len(df_d) < 50:
        return {"loi": "thieu du lieu %s %s/%s" % (ma, khung_goc, khung_dich)}
    hs = ti_le_bar(df_g, df_d)

    moi = copy.deepcopy(spec)
    for phan in ("vao", "ra"):
        if moi.get(phan):
            moi[phan] = _doi_chu_ky(moi[phan], hs)
    g = spec.get("giu")
    if isinstance(g, int) and not isinstance(g, bool):
        moi["giu"] = max(1, int(round(g * hs)))

    bao = []
    for phan in ("vao", "ra"):
        goc_ds = spec.get(phan) or []
        moi_ds = moi.get(phan) or []
        for k, (d_moi, ben, kia) in enumerate(_cac_nguong(moi_ds)):
            # Cap dieu kien tuong ung ben GOC: cung thu tu, vi `_doi_chu_ky`
            # giu nguyen cau truc cay.
            cap_goc = _cac_nguong(goc_ds)
            if k >= len(cap_goc):
                continue
            d_goc, ben_g, kia_g = cap_goc[k]
            h = d_goc[ben_g].get("hang")
            if not isinstance(h, (int, float)) or isinstance(h, bool):
                continue
            sg = _chuoi(df_g, d_goc[kia_g])
            sd = _chuoi(df_d, d_moi[kia])
            if sg is None or sd is None:
                bao.append({"phan": phan, "chi_so": k, "cu": h, "moi": h,
                            "vi_sao": "khong danh gia duoc ve kia"})
                continue
            phep = d_goc.get("phep")
            # Ve co HANG nam ben `phai` thi so sanh la `kia phep hang`;
            # nam ben `trai` thi la `hang phep kia` -> dao huong.
            duoi = (phep in DUOI) if ben_g == "phai" else (phep in TREN)
            p = float((sg < h).mean() if duoi else (sg > h).mean())
            p = min(max(p, 0.001), 0.999)
            h2 = float(np.quantile(sd, p if duoi else 1.0 - p))
            h2 = _lam_tron(h2, h)
            d_moi[ben]["hang"] = h2
            bao.append({"phan": phan, "chi_so": k, "phep": phep,
                        "_chuoi": sd, "_duoi": duoi,
                        "cu": h, "moi": h2, "p_goc": round(p, 4),
                        "p_moi": round(float((sd < h2).mean() if duoi
                                             else (sd > h2).mean()), 4)})

    kh_g = NP._ty_le_kich_hoat(spec, df_g)
    kh_d_tho = NP._ty_le_kich_hoat(_doi_chu_ky_spec(spec, hs), df_d)
    kh_bien = NP._ty_le_kich_hoat(moi, df_d)

    moi, he_so_gop, kh_d = _hieu_chinh_gop(moi, df_d, bao, kh_g, kh_bien)
    return {"spec": moi, "hs": round(hs, 3), "nguong": bao,
            "he_so_gop": he_so_gop,
            # Co che khong co hang so nguong nao thi bo doi chi lam duoc NUA
            # viec (nhan chu ky); phai noi ra chu khong de nguoi doc tuong da
            # hieu chinh xong.
            "khong_co_nguong": not bao,
            "kich_hoat": {"goc": kh_g, "chi_nhan_chu_ky": kh_d_tho,
                          "khop_tung_ve": kh_bien, "sau_khop_phan_vi": kh_d},
            "bar": {"goc": len(df_g), "dich": len(df_d)}}


def _ap_he_so(spec: dict, bao: list, df_d, d: float) -> dict:
    """Ban spec voi xac suat cua MOI ve nhan `d` roi lay lai phan vi."""
    ra = copy.deepcopy(spec)
    for phan in ("vao", "ra"):
        cap = _cac_nguong(ra.get(phan) or [])
        cua_phan = [b for b in bao if b["phan"] == phan]
        for b in cua_phan:
            k = b["chi_so"]
            if k >= len(cap) or "p_goc" not in b or "_chuoi" not in b:
                continue
            dk, ben, kia = cap[k]
            duoi = b["_duoi"]
            p = min(max(b["p_goc"] * d, 0.0005), 0.9995)
            v = b["_chuoi"]
            dk[ben]["hang"] = _lam_tron(
                float(np.quantile(v, p if duoi else 1.0 - p)), b["cu"])
    return ra


def _hieu_chinh_gop(spec: dict, df_d, bao: list, muc: float | None,
                    hien: float | None) -> tuple[dict, float, float]:
    """Do nhi phan mot he so chung sao cho ty le kich hoat GOP khop ban goc."""
    co = [b for b in bao if "_chuoi" in b]
    if not muc or not co:
        return spec, 1.0, hien
    lo, hi = 0.05, 20.0
    tot, tot_d, tot_kh = spec, 1.0, hien
    for _ in range(18):
        d = (lo + hi) / 2
        s2 = _ap_he_so(spec, bao, df_d, d)
        kh = NP._ty_le_kich_hoat(s2, df_d) or 0.0
        if tot_kh is None or abs(kh - muc) < abs(tot_kh - muc):
            tot, tot_d, tot_kh = s2, d, kh
        if kh < muc:
            lo = d
        else:
            hi = d
    # Bao cao phai khop voi spec TRA VE: sau hieu chinh gop thi nguong da doi
    # so voi buoc khop tung ve, neu khong cap nhat thi bang bao mot dang con
    # spec chay mot dang - kieu lech im lang te nhat.
    for phan in ("vao", "ra"):
        cap = _cac_nguong(tot.get(phan) or [])
        for b in bao:
            if b["phan"] != phan or b["chi_so"] >= len(cap):
                continue
            dk, ben, _ = cap[b["chi_so"]]
            b["moi"] = dk[ben].get("hang", b.get("moi"))
    for b in bao:
        b.pop("_chuoi", None)
        b.pop("_duoi", None)
    return tot, round(tot_d, 3), tot_kh


def _doi_chu_ky_spec(spec: dict, hs: float) -> dict:
    """Ban CHI nhan chu ky - de doi chieu voi ban da khop phan vi."""
    moi = copy.deepcopy(spec)
    for phan in ("vao", "ra"):
        if moi.get(phan):
            moi[phan] = _doi_chu_ky(moi[phan], hs)
    g = spec.get("giu")
    if isinstance(g, int) and not isinstance(g, bool):
        moi["giu"] = max(1, int(round(g * hs)))
    return moi


def dat(bao: dict, bien: float = 0.35) -> bool:
    """Phep chuyen co DAT khong: ty le kich hoat sau khi doi phai gan ban goc.

    `bien` la sai so tuong doi cho phep. Mac dinh 0,35 - rong, vi dieu kien gop
    nhieu ve thi khop tung ve khong bao gio cho ty le GOP y het.
    """
    k = (bao or {}).get("kich_hoat") or {}
    a, b = k.get("goc"), k.get("sau_khop_phan_vi")
    if not a or not b or a <= 0:
        return False
    return abs(b - a) / a <= bien
