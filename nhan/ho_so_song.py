# -*- coding: utf-8 -*-
"""ho_so_song.py - DAC TINH SONG va MOC MAGNETIC cua mot tai san.

Muc Q1 cua `KE_HOACH_HOAN_THIEN.md`. Chu du an yeu cau trong `SO_DO_HE_THONG.txt`:

    "Nghien cuu cac dac diem chung bang zigzac de do cac song, bien do thuong day,
     tan suat day, tan suat hoi, bien do hoi,... cac moc magnetic"

`ho_so_symbol.py` da do TINH CACH (hurst, VR, ac1, nua doi) va CHI PHI. File nay
do phan con thieu: **hinh dang SONG** va **cac moc gia hay bi hut ve**.

## DAY LA HO SO, KHONG PHAI TIN HIEU

Phan biet nay quyet dinh cach viet:

  HO SO   mo ta LICH SU da xong. Duoc phep nhin ca chuoi, vi no khong giao dich.
          "EURUSD D1 co song day trung vi 1,8% va hoi 52% song truoc" la mot cau
          ve qua khu.
  TIN HIEU phai point-in-time. Mot dinh zigzag chi BIET duoc sau khi gia da di
          nguoc `nguong` - truoc do no chua ton tai.

Nen file nay tra ve **`tre_xac_nhan_bar`** cho moi thong ke song: so bar trung
binh tu luc dinh HINH THANH den luc no duoc XAC NHAN. Bat ky co che nao xay tren
so lieu nay phai lui di dung tung do. Khong co con so do thi ho so nay la mot cai
bay nhin truoc dong goi san.

## NGUONG ZIGZAG THEO ATR, KHONG THEO %

Mot nguong 1% tao ra 40 song tren vang va 3 song tren EURUSD - hai con so khong
so sanh duoc. Nguong o day la **boi so cua ATR**, nen "song" co cung y nghia
thong ke tren moi tai san. Cung nguyen tac ma `ngoai_sinh.chuyen` dung: giu TY LE
chu khong giu con so.

## MOC MAGNETIC PHAI CO MOC SO SANH

"Gia cham lai muc mo cua ngay 63% so ngay" tu no khong noi gi - mot muc bat ky
gan gia hien tai cung duoc cham thuong xuyen. Nen moi moc deu duoc so voi
**muc GIA NGAU NHIEN cung khoang cach**, va con so bao ra la `hon_ngau_nhien`.

Cac moc lay theo dung dinh nghia du an da dung (`mau.moc_phien`,
`magnetic_backtest`): mo ky · dong ky truoc · cao/thap ky truoc.

Chay:  python -m nhan.ho_so_song [MA] [KHUNG]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

KHO = LAB / "reports" / "HO_SO_SONG.json"

#: Nguong zigzag = bao nhieu lan ATR. 2,0 chon de mot "song" du lon de khong phai
#: nhieu nen, nhung du nho de mot nam co vai chuc song tren khung ngay.
BOI_ATR = 2.0
#: ATR bao nhieu bar.
ATR_N = 14
#: Duoi so bar nay thi khong do - thong ke song can nhieu song.
BAR_TOI_THIEU = 400


def _atr(df: pd.DataFrame, n: int = ATR_N) -> np.ndarray:
    h, l, c = (df["high"].to_numpy(float), df["low"].to_numpy(float),
               df["close"].to_numpy(float))
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)),
                                      np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    return pd.Series(tr).ewm(alpha=1.0 / n, adjust=False).mean().to_numpy()


def zigzag(df: pd.DataFrame, boi_atr: float = BOI_ATR) -> dict:
    """Tach chuoi thanh SONG bang zigzag nguong ATR.

    Tra ve chi so cac dinh/day theo thu tu thoi gian, kem `tre_xac_nhan` cho
    tung cai: so bar tu luc cuc tri xuat hien den luc no du dieu kien de goi la
    mot dinh (gia da di nguoc `nguong`).

    Thuat toan mot luot, khong nhin lai: giu cuc tri dang chay, khi gia dao
    nguoc qua nguong thi CHOT cuc tri do va doi chieu.
    """
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    atr = _atr(df)
    n = len(df)
    if n < BAR_TOI_THIEU:
        # `moc` phai LUON co mat. Truoc 12/09/2026 nhanh nay tra ve dict chi co
        # khoa `loi`, nen moi nguoi goi `zigzag(df)["moc"]` deu nem KeyError thay
        # vi doc duoc loi - tuc mot ham doi HINH DANG tra ve theo du lieu vao.
        return {"moc": [], "loi": "chi %d bar, can >= %d" % (n, BAR_TOI_THIEU)}

    moc, chieu = [], 0           # chieu: +1 dang tim dinh, -1 dang tim day
    i_cuc, gia_cuc = ATR_N, h[ATR_N]
    for i in range(ATR_N + 1, n):
        ng = boi_atr * atr[i]
        if not np.isfinite(ng) or ng <= 0:
            continue
        if chieu >= 0:
            if h[i] > gia_cuc:
                i_cuc, gia_cuc = i, h[i]
            elif gia_cuc - l[i] >= ng:
                moc.append({"i": i_cuc, "gia": gia_cuc, "loai": "dinh",
                            "tre_xac_nhan": i - i_cuc})
                chieu, i_cuc, gia_cuc = -1, i, l[i]
        else:
            if l[i] < gia_cuc:
                i_cuc, gia_cuc = i, l[i]
            elif h[i] - gia_cuc >= ng:
                moc.append({"i": i_cuc, "gia": gia_cuc, "loai": "day",
                            "tre_xac_nhan": i - i_cuc})
                chieu, i_cuc, gia_cuc = 1, i, h[i]
    return {"moc": moc}


def _pv(a, q):
    return float(np.nanpercentile(a, q)) if len(a) else float("nan")


def dac_tinh_song(df: pd.DataFrame, boi_atr: float = BOI_ATR) -> dict:
    """-> bien do day/hoi, tan suat, ti le hoi, tre xac nhan."""
    z = zigzag(df, boi_atr)
    if "loi" in z:
        return z
    moc = z["moc"]
    if len(moc) < 6:
        return {"loi": "chi %d moc song - khong du de thong ke" % len(moc)}

    # Mot DOAN = tu moc nay sang moc ke tiep. Doan di CUNG chieu xu huong truoc
    # do goi la DAY, doan nguoc lai goi la HOI. Xu huong lay tu doan truoc no.
    doan = []
    for a, b in zip(moc, moc[1:]):
        bien = abs(b["gia"] - a["gia"]) / max(a["gia"], 1e-12)
        doan.append({"bien_pct": 100 * bien, "bar": b["i"] - a["i"],
                     "len": b["loai"] == "dinh"})

    # Phan DAY / HOI: so bien do voi doan LIEN TRUOC. Doan lon hon la day,
    # doan nho hon la hoi. Cach nay khong can biet "xu huong" la gi - no doc
    # truc tiep tu hinh dang, va do dung thu chu du an hoi: "bien do thuong
    # day" va "bien do hoi".
    day, hoi, ty_le_hoi = [], [], []
    for t, s in zip(doan, doan[1:]):
        if s["bien_pct"] <= t["bien_pct"]:
            day.append(t)
            hoi.append(s)
            ty_le_hoi.append(100 * s["bien_pct"] / max(t["bien_pct"], 1e-12))

    b_day = np.array([x["bien_pct"] for x in day], float)
    b_hoi = np.array([x["bien_pct"] for x in hoi], float)
    bar_day = np.array([x["bar"] for x in day], float)
    bar_hoi = np.array([x["bar"] for x in hoi], float)
    tre = np.array([m["tre_xac_nhan"] for m in moc], float)
    nam = max((df.index[-1] - df.index[0]).days / 365.25, 1e-9)

    return {
        "so_moc": len(moc), "so_cap_day_hoi": len(day),
        "bien_do_day_pct": {"p25": _pv(b_day, 25), "trung_vi": _pv(b_day, 50),
                            "p75": _pv(b_day, 75)},
        "bien_do_hoi_pct": {"p25": _pv(b_hoi, 25), "trung_vi": _pv(b_hoi, 50),
                            "p75": _pv(b_hoi, 75)},
        "ty_le_hoi_pct": {"p25": _pv(ty_le_hoi, 25), "trung_vi": _pv(ty_le_hoi, 50),
                          "p75": _pv(ty_le_hoi, 75)},
        "bar_moi_day": {"trung_vi": _pv(bar_day, 50)},
        "bar_moi_hoi": {"trung_vi": _pv(bar_hoi, 50)},
        "song_moi_nam": round(len(moc) / nam, 2),
        # SO NAY QUYET DINH DUNG DUOC HAY KHONG: mot co che xay tren dinh zigzag
        # phai lui di tung nay bar, neu khong la nhin truoc.
        "tre_xac_nhan_bar": {"trung_vi": _pv(tre, 50), "p75": _pv(tre, 75),
                             "toi_da": float(np.max(tre)) if len(tre) else 0.0},
        "boi_atr": boi_atr,
    }


#: Moc MAGNETIC: ten -> ham tra ve muc gia tai moi bar, CHI dung thong tin da
#: xong. Moi ham deu dich mot KY, khong dich mot BAR - cai bay 15/08 trong
#: `mau.py` (`transform("last")` phat gia cuoi ngay cho moi bar trong ngay).
def _moc_theo_ky(df: pd.DataFrame, ky: str) -> dict[str, np.ndarray]:
    idx = pd.DatetimeIndex(df.index)
    # Bo mui gio TRUOC khi `to_period`: pandas canh bao va bo no am tham, ma mot
    # canh bao lap lai hang nghin lan thi khong ai doc nua.
    if idx.tz is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)
    nhom = {"ngay": idx.normalize(), "tuan": idx.to_period("W").start_time,
            "thang": idx.to_period("M").start_time}[ky]
    o = df.groupby(nhom)["open"].first()
    c = df.groupby(nhom)["close"].last()
    hi = df.groupby(nhom)["high"].max()
    lo = df.groupby(nhom)["low"].min()
    s = pd.Series(nhom, index=df.index)
    return {
        # mo ky HIEN TAI: biet ngay tu bar dau ky, khong nhin truoc
        f"mo_{ky}": s.map(o).to_numpy(float),
        # dong/cao/thap ky TRUOC: dich MOT KY
        f"dong_{ky}_truoc": s.map(c.shift(1)).to_numpy(float),
        f"cao_{ky}_truoc": s.map(hi.shift(1)).to_numpy(float),
        f"thap_{ky}_truoc": s.map(lo.shift(1)).to_numpy(float),
    }


def moc_magnetic(df: pd.DataFrame, trong_bar: int = 20) -> dict:
    """Gia co hay bi hut ve cac moc neo khong - va HON MOT MUC NGAU NHIEN bao nhieu?

    Voi moi moc: ti le bar ma gia CHAM moc do trong `trong_bar` bar ke tiep.
    Moc so sanh: mot muc gia ngau nhien dat CUNG KHOANG CACH voi gia hien tai
    nhung ve phia ngau nhien. Khong co moc so sanh thi mot con so 60% khong doc
    duoc - moi muc gan gia deu hay bi cham.
    """
    h, l, c = (df["high"].to_numpy(float), df["low"].to_numpy(float),
               df["close"].to_numpy(float))
    n = len(df)
    if n < BAR_TOI_THIEU:
        return {"loi": "chi %d bar" % n}
    moc = {}
    for ky in ("ngay", "tuan", "thang"):
        try:
            moc.update(_moc_theo_ky(df, ky))
        except Exception:
            pass

    # Cao/thap truot cua `trong_bar` bar ke tiep - dung de hoi "co cham khong".
    hi_t = pd.Series(h).shift(-1).rolling(trong_bar, min_periods=1).max().to_numpy()
    lo_t = pd.Series(l).shift(-1).rolling(trong_bar, min_periods=1).min().to_numpy()

    rng = np.random.default_rng(20260912)
    ra = {}
    for ten, muc in moc.items():
        ok = np.isfinite(muc) & np.isfinite(hi_t) & np.isfinite(lo_t)
        ok[-trong_bar:] = False
        if ok.sum() < 100:
            continue
        cham = (muc >= lo_t) & (muc <= hi_t)
        kc = np.abs(muc - c)                       # khoang cach toi moc
        # MOC SO SANH: cung khoang cach, huong ngau nhien
        dau = rng.choice([-1.0, 1.0], size=n)
        gia_lap = c + dau * kc
        cham_lap = (gia_lap >= lo_t) & (gia_lap <= hi_t)
        p_that, p_lap = float(cham[ok].mean()), float(cham_lap[ok].mean())
        ra[ten] = {
            "ty_le_cham_pct": round(100 * p_that, 2),
            "ngau_nhien_pct": round(100 * p_lap, 2),
            "hon_ngau_nhien_lan": round(p_that / max(p_lap, 1e-9), 3),
            "khoang_cach_trung_vi_pct": round(
                100 * float(np.nanmedian(kc[ok] / np.maximum(c[ok], 1e-12))), 3),
            "so_bar_do": int(ok.sum()),
        }
    if not ra:
        return {"loi": "khong moc nao do duoc"}
    tot = max(ra.items(), key=lambda kv: kv[1]["hon_ngau_nhien_lan"])
    return {"trong_bar": trong_bar, "moc": ra,
            "moc_manh_nhat": {"ten": tot[0], **tot[1]}}


def quet_mot(ma: str, khung: str = "D1") -> dict:
    from nhan import du_lieu as DL
    t0 = time.time()
    df = DL.nap(ma, khung)
    ra = {"ma": ma, "khung": khung, "so_bar": len(df),
          "tu": str(df.index[0].date()), "den": str(df.index[-1].date())}
    ra["song"] = dac_tinh_song(df)
    ra["magnetic"] = moc_magnetic(df)
    ra["giay"] = round(time.time() - t0, 2)
    return ra


# ------------------------------------------------------------------- QUET MẺ
def _mot_goi(args):
    ma, khung = args
    try:
        return quet_mot(ma, khung)
    except Exception as e:
        return {"ma": ma, "khung": khung, "loi": "%s: %s" % (type(e).__name__, str(e)[:70])}


def quet(cac_ma: list[str] | None = None, khung: str = "D1",
         so_tien_trinh: int = 8, in_ra=print) -> dict:
    """Quet ho so song cho nhieu ma, chay SONG SONG. Ghi `reports/HO_SO_SONG.json`.

    Song song duoc vi moi ma doc lap hoan toan - khong dung chung trang thai,
    khong cham tester. Day la dung loai viec ma chu du an muon chay song song
    (nguyen tac 3 trong so do he thong).
    """
    from concurrent.futures import ProcessPoolExecutor
    if cac_ma is None:
        from nhan import ho_so_symbol as HSS
        hs = HSS.doc()
        # `ho_so_symbol.doc()` tra ve LIST cac ban ghi, khong phai dict.
        if isinstance(hs, dict):
            hs = list(hs.values())
        cac_ma = sorted({str(x.get("ma")) for x in hs
                         if isinstance(x, dict) and x.get("ma")})
    t0 = time.time()
    ra = {}
    with ProcessPoolExecutor(max_workers=so_tien_trinh) as ex:
        for i, r in enumerate(ex.map(_mot_goi, ((m, khung) for m in cac_ma),
                                     chunksize=2), 1):
            ra["%s|%s" % (r["ma"], r["khung"])] = r
            if in_ra and i % 20 == 0:
                in_ra("  ... %d/%d (%.0fs)" % (i, len(cac_ma), time.time() - t0))
    KHO.parent.mkdir(exist_ok=True)
    KHO.write_text(json.dumps(ra, ensure_ascii=False, indent=1, default=float),
                   encoding="utf-8")
    ok = [v for v in ra.values() if "loi" not in v and "loi" not in (v.get("song") or {})]
    if in_ra:
        in_ra("do duoc %d/%d ma trong %.0fs -> %s" % (len(ok), len(ra), time.time() - t0, KHO))
    return ra


def doc() -> dict:
    try:
        return json.loads(KHO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main(argv: list[str]) -> int:
    if argv and argv[0] == "quet":
        quet(khung=argv[1] if len(argv) > 1 else "D1",
             so_tien_trinh=int(argv[2]) if len(argv) > 2 else 8)
        return 0
    ma = argv[0] if argv else "EURUSD"
    khung = argv[1] if len(argv) > 1 else "D1"
    print(json.dumps(quet_mot(ma, khung), ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
