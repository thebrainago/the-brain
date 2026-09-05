# -*- coding: utf-8 -*-
"""LUCKY CAT SONG BAO LAU - khong hoi "co SL khong", hoi "song bao lau, rut kip khong".

Chu du an 04/09: *"toi khong ngai viec dca khong cat"*. Dung. Cau hoi dung cho
lop he nay la ba cai: song bao lau, kiem duoc bao nhieu trong thoi gian do, va
lich rut co dua tay ve bo truoc khi duoi den khong.

BAN 04/09 SAI BA CHO (do 05/09, sua tai day):

  1. Lay `so[i+1]` cua risk-json lam "loi/ngay". Nhom 5 so do la
     (luc, LAI, MFE, LO, MAE): phan tu 1 chi la NHANH LAI, luon >= 0. Nen mau
     ra 0/118 ngay am, TB +5,445%/ngay, von cuoi x1,4e28. Net that = LAI + LO.
  2. Coi don vi risk-json la % von. Ngay MAE -71,22% (14/07/2026) doi chieu
     chuoi equity thi lo treo that chi 7,6% von. Hai thang do khac don vi.
  3. Goi day la "luoi FX". Lucky Cat danh XAUUSD, giu trung binh 59 phut,
     631 lenh, long/short 50/50 - scalping vang, khong phai luoi FX.

NGUON SO DUNG (do 05/09, khong doan):
  - Chuoi `growth` nhung trong trang signal: 317 moc theo SO LENH (khong phai
    ngay), DA HIEU CHINH nap/rut. Sut giam sau nhat tinh ra -28,09%, khop voi
    "Drawdown By Balance: 28.61%" trang cong bo -> dung chuoi nay.
  - Chuoi `balance/equity` co timestamp DINH nap/rut (mot buoc -398,59 USD),
    khong dung de tinh loi suat.
  - Chuoi `muc tai`: 713 moc, 46% thoi gian co vi the, tai trung vi 1,38%,
    dinh 12,54% (khop "Max deposit load 12.58%").

HAI CHANG, VI MOT CHANG KHONG TRA LOI DUOC:
  A. Bootstrap khoi tren chuoi growth. Cho CHAN DUOI cua ty le chay - vi mau
     6,5 thang KHONG chua bien co giet tai khoan, nen bootstrap tu no gan nhu
     bat buoc ra 0%. Bao cao 0% o day la ket qua VO NGHIA neu doc mot minh.
  B. Mo hinh CAU TRUC. Tu muc tai + don bay suy ra cu vang di nguoc bao nhieu
     dollar thi het von, roi quet 12,5 nam M5 vang xem cu do bao lau mot lan
     trong cua so giu 60 phut. Day moi la cau tra loi "song bao lau".
"""
from __future__ import annotations

import re
import sys
import warnings

sys.path.insert(0, r"C:\Users\SV STORE\Downloads\Research SP500\lab")
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import requests

from nhan import du_lieu as DL

SID = 2359404
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
H = {"User-Agent": UA, "Referer": "https://www.mql5.com/en/signals",
     "X-Requested-With": "XMLHttpRequest"}
VANG = r"C:\Users\SV STORE\Downloads\Research SP500\data\XAUUSDm_M5_day_du.parquet"

#: Mang so dai nhung trong trang signal, theo thu tu: growth, balance,
#: (luc, balance, equity), (luc, muc_tai).
_RX_MANG = re.compile(r"\[((?:[-\d.]+,){40,}[-\d.]+)\]")


def mang_trong_trang(sid: int) -> list[np.ndarray]:
    h = requests.get("https://www.mql5.com/en/signals/%d" % sid,
                     timeout=30, headers=H).text
    return [np.array([float(x) for x in m.group(1).split(",")])
            for m in _RX_MANG.finditer(h)]


def chuoi_growth(mang: list[np.ndarray]) -> np.ndarray:
    """Loi suat theo BUOC LENH, da hieu chinh nap/rut."""
    g = mang[0].reshape(-1, 2)
    v = 1.0 + g[:, 1] / 100.0
    return np.diff(v) / v[:-1]


def muc_tai(mang: list[np.ndarray]) -> np.ndarray:
    v = mang[3].reshape(-1, 2)[:, 1]
    return v[v > 0]


# ---------------------------------------------------------------- chang A
def chang_a(r: np.ndarray, buoc_nam: float, nam: int = 5,
            khoi: int = 10, lan: int = 4000, seed: int = 20260905) -> dict:
    """Bootstrap khoi. Nguong chay: mat 90% von (stop-out thuc te den truoc 100%)."""
    rng = np.random.default_rng(seed)
    can = int(nam * buoc_nam)
    n = len(r)
    so_khoi = can // khoi + 1
    dau = rng.integers(0, max(n - khoi, 1), size=(lan, so_khoi))
    lay = (dau[:, :, None] + np.arange(khoi)[None, None, :]).reshape(lan, -1)[:, :can]
    M = np.cumprod(1.0 + r[lay % n], axis=1)
    day = np.minimum.accumulate(M, axis=1)
    chet = day[:, -1] <= 0.10
    return {"lan": lan, "can": can, "chay": int(chet.sum()),
            "cuoi_song": M[~chet, -1] if (~chet).any() else np.array([])}


def chang_a_rut(r: np.ndarray, buoc_nam: float, chu_ky: int, ty_le: float,
                nam: int = 5, khoi: int = 10, lan: int = 1500,
                seed: int = 20260905) -> tuple[float, float | None]:
    """Rut `ty_le` phan lai moi `chu_ky` BUOC. Tra (ty le hoan von, trung vi nam)."""
    rng = np.random.default_rng(seed + 1)
    can = int(nam * buoc_nam)
    n = len(r)
    hoa = []
    for _ in range(lan):
        dau = rng.integers(0, max(n - khoi, 1), size=can // khoi + 1)
        chuoi = r[((dau[:, None] + np.arange(khoi)[None, :]).ravel())[:can] % n]
        tk, tui, khi = 1.0, 0.0, None
        for j, x in enumerate(chuoi):
            tk *= (1.0 + x)
            if tk <= 0.10:
                break
            if j and j % chu_ky == 0 and tk > 1.0:
                lay_ra = (tk - 1.0) * ty_le
                tk -= lay_ra
                tui += lay_ra
                if tui >= 1.0 and khi is None:
                    khi = j
        hoa.append(khi)
    co = [x for x in hoa if x is not None]
    return len(co) / lan, (float(np.median(co)) / buoc_nam if co else None)


# ---------------------------------------------------------------- chang B
def nap_vang() -> pd.DataFrame:
    """Vang M5 SACH. File "M5" nhet 1.963 dong bar NGAY o dau (2014-01 ->
    2017-04); de nguyen thi mot cu "13,4% trong 60 phut" hien ra, that ra la
    bien do mot bar NGAY.

    KHONG cat bang so cung: du an da co `du_lieu.cat_doan_tho` cho dung viec
    nay (chot chan them 01/09 sau khi 5 ma dinh loi lai tap do phan giai).
    Viet lai mot ban cat rieng o day la dung lai thu he da co - va ban rieng
    do se khong duoc sua khi chot chan chung duoc sua.
    """
    d = pd.read_parquet(VANG)[["time", "open", "high", "low", "close"]]
    d["time"] = pd.to_datetime(d["time"])
    d = d.dropna().set_index("time").sort_index()
    d, ghi_chu = DL.cat_doan_tho(d, "M5")
    if ghi_chu:
        print("  [cat doan tho] bo %d bar %s -> %s, con %d"
              % (ghi_chu["bo_bar"], ghi_chu["cat_tu"], ghi_chu["den"],
                 ghi_chu["con_bar"]))
    d = d.reset_index()
    b = d["time"].diff().dt.total_seconds()
    assert (b == 300).mean() > 0.99, "doan M5 van khong sach"
    return d


def phoi_nhiem_do_duoc(mang: list[np.ndarray], d: pd.DataFrame) -> pd.DataFrame:
    """% von tai khoan mat tren 1% vang di nguoc - DO, khong doan don bay.

    Voi moi ngay: lo treo lon nhat cua tai khoan (balance - equity) doi voi cu
    di nguoc 60 phut lon nhat cua vang ngay do. Ty so la phoi nhiem hieu dung.
    """
    e = mang[2].reshape(-1, 3)
    ee = pd.DataFrame({"t": pd.to_datetime(e[:, 0], unit="s"),
                       "bal": e[:, 1], "eq": e[:, 2]})
    ee["ngay"] = ee["t"].dt.date
    ee["treo"] = (ee["bal"] - ee["eq"]) / ee["bal"] * 100.0
    hi = d["high"].rolling(12).max()
    lo = d["low"].rolling(12).min()
    op = d["open"].shift(11)
    v = d.assign(adv=np.maximum(op - lo, hi - op) / op * 100.0,
                 ngay=d["time"].dt.date)
    j = pd.concat([ee.groupby("ngay")["treo"].max().rename("treo"),
                   v.groupby("ngay")["adv"].max().rename("vang")],
                  axis=1).dropna()
    j = j[j["vang"] > 0]
    j["he_so"] = j["treo"] / j["vang"]
    return j


def cu_giet_pct(he_so: float) -> float:
    """Vang phai di nguoc bao nhieu % (trong cua so giu) thi mat 90% von."""
    return 90.0 / he_so if he_so > 0 else float("inf")


def tan_suat_pct(d: pd.DataFrame, nguong_pct: float, bar_giu: int) -> dict:
    """Bao lau mot lan vang di nguoc >= nguong% trong `bar_giu` bar M5.

    Cua so TRUOT chong nhau: mot cu soc bi dem lai toi `bar_giu` lan (ca ngay =
    288 lan). Phai gop chuoi True lien tiep thanh MOT DOT, va bo qua tiep
    `bar_giu` bar sau do vi chung con nhin thay chinh cu soc ay.
    """
    hi = d["high"].rolling(bar_giu).max().to_numpy()
    lo = d["low"].rolling(bar_giu).min().to_numpy()
    op = d["open"].shift(bar_giu - 1).to_numpy()
    ok = ~np.isnan(op)
    adv = np.maximum(op - lo, hi - op)[ok] / op[ok] * 100.0
    nam = (d["time"].iloc[-1] - d["time"].iloc[0]).days / 365.25
    hit = np.flatnonzero(adv >= nguong_pct)
    dot, chan = 0, -1
    for i in hit:
        if i > chan:
            dot += 1
            chan = i + bar_giu
    return {"so_lan": dot, "tho": int(hit.size), "moi_nam": dot / nam,
            "lon_nhat": float(adv.max()), "nam_dl": nam}


def chay():
    mang = mang_trong_trang(SID)
    r = chuoi_growth(mang)
    tai = muc_tai(mang)
    e = mang[2].reshape(-1, 3)
    ngay_lich = (e[-1, 0] - e[0, 0]) / 86400.0
    buoc_nam = len(r) / (ngay_lich / 365.25)

    v = np.cumprod(1.0 + r)
    dd = v / np.maximum.accumulate(v) - 1.0
    print("=" * 78)
    print("LUCKY CAT (signal #%d) - XAUUSD, giu TB 59 phut, 631 lenh" % SID)
    print("=" * 78)
    print("chuoi growth : %d buoc lenh tren %.0f ngay lich = %.0f buoc/nam"
          % (len(r), ngay_lich, buoc_nam))
    print("loi suat/buoc: TB %+.3f%%  lech %.3f%%  am %d/%d"
          % (r.mean() * 100, r.std() * 100, int((r < 0).sum()), len(r)))
    print("gop nhan     : x%.2f trong %.2f nam = %.0f%%/nam ngoai suy"
          % (v[-1], ngay_lich / 365.25, (v[-1] ** (365.25 / ngay_lich) - 1) * 100))
    print("sut giam     : %.2f%%  (trang cong bo 28,61%% - khop)" % (dd.min() * 100))
    print("muc tai      : trung vi %.2f%%  bp90 %.2f%%  dinh %.2f%%"
          % (np.median(tai) * 100, np.percentile(tai, 90) * 100, tai.max() * 100))
    print()

    print("--- CHANG A: bootstrap khoi tren chinh mau (CHAN DUOI) ---")
    a = chang_a(r, buoc_nam)
    print("  %d duong chay x 5 nam (%d buoc), khoi 10 buoc" % (a["lan"], a["can"]))
    print("  chay tai khoan (mat >=90%% von): %d/%d = %.2f%%"
          % (a["chay"], a["lan"], a["chay"] / a["lan"] * 100))
    if len(a["cuoi_song"]):
        s = a["cuoi_song"]
        print("  neu song: von cuoi trung vi x%.3g (bp10 x%.3g, bp90 x%.3g)"
              % (np.median(s), np.percentile(s, 10), np.percentile(s, 90)))
    print("  >> DOC KEM CANH BAO: mau 6,5 thang khong chua bien co giet tai khoan.")
    print("     Con so nay la CHAN DUOI, khong phai uoc luong.")
    print()

    print("--- LICH RUT: bao lau hoan von goc (tren cung mau) ---")
    thang = buoc_nam / 12.0
    for ten, chu_ky, ty_le in (("moi thang, rut 50% lai", int(thang), 0.5),
                               ("moi quy,  rut 50% lai", int(3 * thang), 0.5),
                               ("moi quy,  rut 100% lai", int(3 * thang), 1.0),
                               ("moi 6 thang, rut 100% lai", int(6 * thang), 1.0)):
        ty, tv = chang_a_rut(r, buoc_nam, max(chu_ky, 1), ty_le)
        print("  %-26s: hoan von %6.1f%% duong chay%s"
              % (ten, ty * 100, (", trung vi %.2f nam" % tv) if tv else ""))
    print()

    print("--- CHANG B: cu vang nao giet tai khoan, bao lau mot lan ---")
    d = nap_vang()
    ph = phoi_nhiem_do_duoc(mang, d)
    print("  kho vang M5 sach: %s bar, %s -> %s (%.1f nam)"
          % (format(len(d), ","), d["time"].iloc[0].date(),
             d["time"].iloc[-1].date(),
             (d["time"].iloc[-1] - d["time"].iloc[0]).days / 365.25))
    print("  %d ngay trung de do phoi nhiem (%s -> %s)"
          % (len(ph), ph.index.min(), ph.index.max()))
    print("  phoi nhiem (%% von mat / 1%% vang): trung vi %.2f  bp90 %.2f  DINH %.2f"
          % (ph["he_so"].median(), ph["he_so"].quantile(0.9), ph["he_so"].max()))
    print("  -> khong can gia dinh don bay. He so nay DO tu lo treo that.")
    print()
    print("  %-38s %7s %9s %9s %14s"
          % ("phoi nhiem / cua so giu", "he so", "cu giet", "lan/nam", "song TB"))
    for ten, hs in (("ngay thuong (trung vi)", float(ph["he_so"].median())),
                    ("ngay tai (bp90)", float(ph["he_so"].quantile(0.9))),
                    ("dinh da tung cham", float(ph["he_so"].max()))):
        for W, tw in ((12, "giu 60 phut"), (288, "ket ca ngay")):
            ng = cu_giet_pct(hs)
            ts = tan_suat_pct(d, ng, W)
            song = ("%.2f nam" % (1 / ts["moi_nam"])) if ts["moi_nam"] > 0                 else ">%.0f nam (chua tung)" % ts["nam_dl"]
            print("  %-38s %7.2f %8.1f%% %9.2f %14s"
                  % (ten + " / " + tw, hs, ng, ts["moi_nam"], song))
    print()
    for W, tw in ((12, "60 phut"), (48, "4 gio"), (288, "1 ngay")):
        ts = tan_suat_pct(d, 1e9, W)
        mat = ts["lon_nhat"] * ph["he_so"].max()
        print("  cu di nguoc %-8s lon nhat %.1f nam qua: %5.2f%%  "
              "-> o phoi nhiem dinh mat %.0f%% von"
              % (tw, ts["nam_dl"], ts["lon_nhat"], min(mat, 100.0)))
    print()
    print("  Doc bang: cot 'song TB' gia dinh vi the mo dung luc va giu het cua so.")
    print("  He co cat lo/chot som thi song lau hon; he nhoi them khi lo thi ngan hon.")


if __name__ == "__main__":
    chay()
