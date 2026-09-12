# -*- coding: utf-8 -*-
"""quy_luat_song.py - TU TIM QUY LUAT trong chuoi song, da khung.

Muc "QUANTLAB noi sinh" cua `SO_DO_HE_THONG.txt`:

    "Dao sau vao 1 cap tai san bang phuong phap suy nguoc, vi du nhu truoc 1 cu
     tang hay giam cua tai san A se co dau hieu gi... Nghia la quantlab phai tim
     duoc logic va tien hanh nghien cuu de tim edge"

`ho_so_song.py` MO TA song (bien do day/hoi, tan suat). File nay di mot buoc xa
hon: hoi **song co QUY LUAT khong** - tuc mot dieu kien tren song truoc co du
bao duoc song sau khong. Mot quy luat dung duoc se thanh mot co che.

## SAU CAU HOI, MOI CAU MOT QUY LUAT UNG VIEN

  L1  HOI THEO CO DAY      song day cang lon thi hoi cang sau hay cang nong?
  L2  NHO GIUA CAC SONG    ti le hoi lan truoc co du bao lan sau khong?
  L3  BEN HUONG            sau mot day len, day ke tiep co xu huong len khong?
  L4  CUM BIEN DO          song lon di voi nhau khong (vol clustering muc song)?
  L5  HOI DUNG O MOC       hoi co dung gan moc chu ky hon muc ngau nhien khong?
  L6  GIO TRONG NGAY       song hay BAT DAU vao khung gio nao?

## HAI CHOT CHAN - thieu mot cai la tu lua

**(1) MOI QUY LUAT PHAI CO NULL.** Xao tron chuoi song (giu nguyen phan bo bien
do, pha thu tu) roi tinh lai. Mot "quy luat" ma ban xao tron cung cho ra thi
khong phai quy luat. Khong co buoc nay thi sau cau hoi tren se ra sau "phat
hien", vi chuoi nao cung co cau truc khi nhin du ky.

**(2) PHAI DUNG TREN NHIEU KHUNG.** Day la bo loc manh hon ca p-value o day:
mot quy luat chi hien tren M15 rat co the la nhieu cua M15; mot quy luat hien
tren M15 + H1 + H4 + D1 la tinh chat CAU TRUC cua tai san. Rang buoc nay khong
ton them phep thu nao - chi can chay cung ham tren nhieu khung.

## KHONG PHAI TIN HIEU

Moi so o day tinh tren dinh/day DA XAC NHAN. `ho_so_song` do duoc tre xac nhan
trung vi 3 bar (toi da 5). Bat ky co che nao xay tu day phai lui dung tung do.

Chay:  python -m nhan.quy_luat_song [MA] [KHUNG,KHUNG,...]
       python -m nhan.quy_luat_song AUDCAD D1,H4,H1,M30,M15
Ra:    reports/QUY_LUAT_SONG_<MA>.json
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

from nhan import ho_so_song as HSS  # noqa: E402

#: Bao nhieu lan xao tron de lam null.
SO_XAO = 400
#: Duoi so cap day/hoi nay thi khong ket luan gi.
CAP_TOI_THIEU = 60
HAT = 20260912


def _chuoi_song(df: pd.DataFrame, boi_atr: float = HSS.BOI_ATR) -> pd.DataFrame:
    """-> bang mot dong mot DOAN song: bien do %, so bar, huong, chi so ket thuc."""
    z = HSS.zigzag(df, boi_atr)
    if "loi" in z or len(z.get("moc", [])) < 8:
        return pd.DataFrame()
    moc = z["moc"]
    hang = []
    for a, b in zip(moc, moc[1:]):
        hang.append({
            "bien": 100 * abs(b["gia"] - a["gia"]) / max(a["gia"], 1e-12),
            "bar": b["i"] - a["i"],
            "len": 1 if b["loai"] == "dinh" else -1,   # doan di LEN ket thuc o dinh
            "i_dau": a["i"], "i_cuoi": b["i"],
            "gia_dau": a["gia"], "gia_cuoi": b["gia"],
        })
    return pd.DataFrame(hang)


def _cap_day_hoi(s: pd.DataFrame) -> pd.DataFrame:
    """Cap (day, hoi): doan sau NHO HON doan truoc thi goi la hoi cua doan truoc."""
    if len(s) < 3:
        return pd.DataFrame()
    t, k = s.iloc[:-1].reset_index(drop=True), s.iloc[1:].reset_index(drop=True)
    m = k["bien"] <= t["bien"]
    return pd.DataFrame({
        "day_bien": t["bien"][m].to_numpy(), "day_bar": t["bar"][m].to_numpy(),
        "day_len": t["len"][m].to_numpy(),
        "hoi_bien": k["bien"][m].to_numpy(), "hoi_bar": k["bar"][m].to_numpy(),
        "hoi_i_cuoi": k["i_cuoi"][m].to_numpy(),
        "hoi_gia_cuoi": k["gia_cuoi"][m].to_numpy(),
        "ty_hoi": 100 * k["bien"][m].to_numpy() / np.maximum(t["bien"][m].to_numpy(), 1e-12),
    })


def _p_hai_phia(that: float, null: np.ndarray) -> float:
    """p mot phia theo huong lech, kieu hoan vi. +1 de khong bao gio tra 0."""
    n = len(null)
    if n == 0 or not np.isfinite(that):
        return float("nan")
    tv = float(np.nanmedian(null))
    vuot = np.sum(null >= that) if that >= tv else np.sum(null <= that)
    return float((vuot + 1) / (n + 1))


def quy_luat(df: pd.DataFrame, khung: str, boi_atr: float = HSS.BOI_ATR) -> dict:
    s = _chuoi_song(df, boi_atr)
    if s.empty:
        return {"khung": khung, "loi": "khong tach duoc song"}
    c = _cap_day_hoi(s)
    if len(c) < CAP_TOI_THIEU:
        return {"khung": khung, "loi": "chi %d cap day/hoi, can >= %d"
                % (len(c), CAP_TOI_THIEU)}

    r = np.random.default_rng(HAT)
    ra = {"khung": khung, "so_doan": len(s), "so_cap": len(c),
          "bar": len(df), "luat": {}}

    # ---- L1: hoi theo CO cua day. Chia day lam 3 phan, so ty le hoi.
    q = np.quantile(c["day_bien"], [1 / 3, 2 / 3])
    nho = c["ty_hoi"][c["day_bien"] <= q[0]]
    lon = c["ty_hoi"][c["day_bien"] > q[1]]
    if len(nho) > 20 and len(lon) > 20:
        that = float(np.median(lon) - np.median(nho))
        null = np.array([
            (lambda p: float(np.median(p[-len(lon):]) - np.median(p[:len(nho)])))(
                r.permutation(c["ty_hoi"].to_numpy()))
            for _ in range(SO_XAO)])
        ra["luat"]["L1_hoi_theo_co_day"] = {
            "hoi_khi_day_NHO_pct": round(float(np.median(nho)), 2),
            "hoi_khi_day_LON_pct": round(float(np.median(lon)), 2),
            "chenh": round(that, 2), "p": round(_p_hai_phia(that, null), 4)}

    # ---- L2: ty le hoi co NHO khong (tu tuong quan bac 1)
    x = c["ty_hoi"].to_numpy()
    if len(x) > 40:
        that = float(np.corrcoef(x[:-1], x[1:])[0, 1])
        null = np.array([(lambda p: float(np.corrcoef(p[:-1], p[1:])[0, 1]))(
            r.permutation(x)) for _ in range(SO_XAO)])
        ra["luat"]["L2_nho_ty_le_hoi"] = {
            "tu_tuong_quan": round(that, 4), "p": round(_p_hai_phia(that, null), 4)}

    # ---- L3: ben huong - day ke tiep co cung chieu khong
    d = c["day_len"].to_numpy()
    if len(d) > 40:
        that = float(np.mean(d[:-1] == d[1:]))
        null = np.array([(lambda p: float(np.mean(p[:-1] == p[1:])))(
            r.permutation(d)) for _ in range(SO_XAO)])
        ra["luat"]["L3_ben_huong"] = {
            "ty_le_cung_chieu_pct": round(100 * that, 2),
            "null_pct": round(100 * float(np.median(null)), 2),
            "p": round(_p_hai_phia(that, null), 4)}

    # ---- L4: cum bien do
    b = c["day_bien"].to_numpy()
    if len(b) > 40:
        that = float(np.corrcoef(b[:-1], b[1:])[0, 1])
        null = np.array([(lambda p: float(np.corrcoef(p[:-1], p[1:])[0, 1]))(
            r.permutation(b)) for _ in range(SO_XAO)])
        ra["luat"]["L4_cum_bien_do"] = {
            "tu_tuong_quan": round(that, 4), "p": round(_p_hai_phia(that, null), 4)}

    # ---- L5: hoi co dung gan MOC CHU KY hon ngau nhien khong
    try:
        moc = HSS._moc_theo_ky(df, "thang")
        muc = moc.get("dong_thang_truoc")
        gia = df["close"].to_numpy(float)
        i = c["hoi_i_cuoi"].to_numpy().astype(int)
        gh = c["hoi_gia_cuoi"].to_numpy()
        ok = np.isfinite(muc[i]) & np.isfinite(gh)
        if ok.sum() > 40:
            kc = np.abs(gh[ok] - muc[i][ok]) / np.maximum(gia[i][ok], 1e-12)
            # NULL: lay diem KET THUC HOI ngau nhien trong cung chuoi
            null = np.array([
                float(np.median(np.abs(r.choice(gia, ok.sum()) - muc[i][ok])
                                / np.maximum(gia[i][ok], 1e-12)))
                for _ in range(min(SO_XAO, 120))])
            that = float(np.median(kc))
            ra["luat"]["L5_hoi_dung_o_moc_thang"] = {
                "kc_trung_vi_pct": round(100 * that, 4),
                "null_pct": round(100 * float(np.median(null)), 4),
                "gan_hon_lan": round(float(np.median(null)) / max(that, 1e-12), 3),
                "p": round(_p_hai_phia(that, null), 4)}
    except Exception as e:
        ra["luat"]["L5_hoi_dung_o_moc_thang"] = {"loi": str(e)[:60]}

    # ---- L6: song hay BAT DAU vao gio nao (chi khung co gio)
    try:
        idx = pd.DatetimeIndex(df.index)
        if len(set(idx.hour)) > 1:
            gio = idx.hour.to_numpy()[c["day_bien"].index.to_numpy() * 0
                                      + s["i_dau"].to_numpy()[:len(c)]]
            dem = np.bincount(gio, minlength=24).astype(float)
            deu = dem.sum() / 24.0
            that = float(np.max(dem) / max(deu, 1e-9))
            null = np.array([
                float(np.max(np.bincount(r.integers(0, 24, len(gio)),
                                         minlength=24)) / max(deu, 1e-9))
                for _ in range(SO_XAO)])
            ra["luat"]["L6_gio_bat_dau_song"] = {
                "gio_dong_nhat": int(np.argmax(dem)),
                "dam_hon_deu_lan": round(that, 3),
                "null_lan": round(float(np.median(null)), 3),
                "p": round(_p_hai_phia(that, null), 4)}
    except Exception as e:
        ra["luat"]["L6_gio_bat_dau_song"] = {"loi": str(e)[:60]}
    return ra


def quet(ma: str, khung: list[str] | None = None, in_ra=print) -> dict:
    from nhan import du_lieu as DL
    khung = khung or ["D1", "H4", "H1", "M30", "M15"]
    t0 = time.time()
    ket = {"ma": ma, "khung": {}}
    for k in khung:
        try:
            ket["khung"][k] = quy_luat(DL.nap(ma, k), k)
        except Exception as e:
            ket["khung"][k] = {"khung": k, "loi": "%s: %s" % (type(e).__name__, str(e)[:60])}

    # ---- BO LOC DA KHUNG: luat nao dat tren NHIEU khung
    dem, tong = {}, {}
    for k, v in ket["khung"].items():
        for ten, l in (v.get("luat") or {}).items():
            p = l.get("p")
            tong[ten] = tong.get(ten, 0) + 1
            if isinstance(p, float) and p <= 0.05:
                dem[ten] = dem.get(ten, 0) + 1
    ket["dat_tren_may_khung"] = {t: "%d/%d" % (dem.get(t, 0), n) for t, n in tong.items()}
    ket["giay"] = round(time.time() - t0, 1)

    if in_ra:
        in_ra("=" * 88)
        in_ra("QUY LUAT SONG: %s  (%s)" % (ma, ", ".join(khung)))
        in_ra("=" * 88)
        for k, v in ket["khung"].items():
            if "loi" in v:
                in_ra("  %-5s LOI: %s" % (k, v["loi"][:60]))
                continue
            in_ra("  %-5s %d doan · %d cap · %d bar" % (k, v["so_doan"], v["so_cap"], v["bar"]))
            for ten, l in (v.get("luat") or {}).items():
                if "loi" in l:
                    continue
                p = l.get("p")
                sao = " ***" if isinstance(p, float) and p <= 0.05 else ""
                so = {kk: vv for kk, vv in l.items() if kk != "p"}
                in_ra("        %-26s p=%-7s %s%s" % (ten, p, json.dumps(so, ensure_ascii=False)[:58], sao))
        in_ra("\n  DAT TREN MAY KHUNG (day la bo loc manh nhat o day):")
        for t, x in sorted(ket["dat_tren_may_khung"].items(), key=lambda kv: -int(kv[1][0])):
            in_ra("        %-26s %s" % (t, x))
    ra = LAB / "reports" / ("QUY_LUAT_SONG_%s.json" % ma)
    ra.parent.mkdir(exist_ok=True)
    ra.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float),
                  encoding="utf-8")
    if in_ra:
        in_ra("\n-> %s  (%.0fs)" % (ra, ket["giay"]))
    return ket


# --------------------------------------------------------------- QUET NHIEU MA
def _mot_ma(args):
    ma, khung = args
    try:
        return quet(ma, list(khung), in_ra=None)
    except Exception as e:
        return {"ma": ma, "loi": "%s: %s" % (type(e).__name__, str(e)[:60])}


def quet_nhieu(cac_ma: list[str], khung: list[str] | None = None,
               so_tien_trinh: int = 8, in_ra=print) -> dict:
    """Chay `quet` cho nhieu ma SONG SONG roi gop bang 'dat may khung'.

    Bo loc thuc su nam o day: mot quy luat dat tren NHIEU MA x NHIEU KHUNG moi
    la tinh chat cau truc. Dat tren mot o thi la nhieu cua o do.
    """
    from collections import Counter
    from concurrent.futures import ProcessPoolExecutor
    khung = khung or ["D1", "H4", "H1"]
    t0 = time.time()
    ket = []
    with ProcessPoolExecutor(max_workers=so_tien_trinh) as ex:
        for r in ex.map(_mot_ma, ((m, tuple(khung)) for m in cac_ma)):
            ket.append(r)
    tong, mau = Counter(), Counter()
    for r in ket:
        if "loi" in r:
            continue
        for t, x in (r.get("dat_tren_may_khung") or {}).items():
            a, b = x.split("/")
            tong[t] += int(a)
            mau[t] += int(b)
    bang = {t: {"dat": tong[t], "tong": mau[t],
                "ty_le_pct": round(100 * tong[t] / max(mau[t], 1), 1)}
            for t in mau}
    if in_ra:
        n_ok = len([r for r in ket if "loi" not in r])
        in_ra("=" * 72)
        in_ra("QUY LUAT SONG tren %d ma x %d khung  (%.0fs)"
              % (n_ok, len(khung), time.time() - t0))
        in_ra("=" * 72)
        in_ra("  %-28s %10s  %s" % ("luat", "dat/tong", "ty le"))
        for t, v in sorted(bang.items(), key=lambda kv: -kv[1]["ty_le_pct"]):
            in_ra("  %-28s %5d/%-4d %6.1f%%" % (t, v["dat"], v["tong"], v["ty_le_pct"]))
        for r in ket:
            if "loi" in r:
                in_ra("  [!] %s: %s" % (r["ma"], r["loi"][:50]))
    ra = LAB / "reports" / "QUY_LUAT_SONG_TONG_HOP.json"
    ra.write_text(json.dumps({"ma": cac_ma, "khung": khung, "bang": bang,
                              "chi_tiet": ket}, ensure_ascii=False, indent=1,
                             default=float), encoding="utf-8")
    if in_ra:
        in_ra("\n-> %s" % ra)
    return {"bang": bang, "chi_tiet": ket}


def main(argv: list[str]) -> int:
    if argv and argv[0] == "nhieu":
        ma = argv[1].split(",") if len(argv) > 1 else [
            "AUDCAD", "EURUSD", "GBPUSD", "XAUUSD", "USDJPY", "EURGBP",
            "XM_US500CASH", "XM_US100CASH"]
        kh = argv[2].split(",") if len(argv) > 2 else None
        quet_nhieu(ma, kh, so_tien_trinh=int(argv[3]) if len(argv) > 3 else 8)
        return 0
    ma = argv[0] if argv else "AUDCAD"
    kh = argv[1].split(",") if len(argv) > 1 else None
    quet(ma, kh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
