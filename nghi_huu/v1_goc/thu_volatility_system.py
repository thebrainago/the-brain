# -*- coding: utf-8 -*-
"""KIEM "VOLATILITY SYSTEM" — Wilder (1978), qua freqtrade-strategies (GPL-3.0).

Luat rut nguyen tu `user_data/strategies/futures/VolatilitySystem.py`:
    ATR2 = ATR(14) * 2
    LONG  khi  close[i] - close[i-1]  >  ATR2[i-1]
    SHORT khi  close[i-1] - close[i]  >  ATR2[i-1]
    Dao chieu lien tuc (stop-and-reverse), LUON o trong thi truong.
    Khong cat lo (stoploss = -1), khong chot loi (roi = 100).

MOI THU BAT BUOC CUA DU AN DEU CO O DAY:
  - Vao lenh tai OPEN[i+1], khong bao gio close[i]  (quy tac 1)
  - Chi phi that: spread theo bps + PHI QUA DEM theo so dem giu that  (quy tac 2, 8)
  - Dong MUA-GIU o moi bang, CA HAI ban: co phi va khong phi  (quy tac 3)
  - Placebo hoan vi CHUOI VI THE, khong hoan vi lai/lo  (quy tac 8/19)
  - Gop 28 thi truong theo 7 nhom tuong quan, doc p theo NHOM

Chay: python thu_volatility_system.py
Ra:   reports/BAO_CAO_VOLATILITY_SYSTEM.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import brain_co_che as bc

REPORTS = Path(__file__).parent / "reports"
RA = REPORTS / "BAO_CAO_VOLATILITY_SYSTEM.md"

SPREAD_BPS = 0.7          # CFD chi so, do that tren 168 lenh khop (quy tac 11)
PHI_NAM = 0.04            # phi giu dai ~4%/nam, muc giua cua ban do lien san
HOAN_VI = 2000
HAT = [11, 13, 17, 29, 41]


def vi_the(df, chu_ky=14, he_so=2.0):
    """Chuoi vi the +1/-1 theo dung luat, NHAN QUA hoan toan.

    Tin hieu tinh tu close[i] -> chi duoc dung tu bar i+1. Ham tra ve vi the AP DUNG
    cho tung bar (da dich san), nen loi suat lay bang open[i+1]->open[i+2].
    """
    a = bc.atr(df, chu_ky) * he_so
    dc = df["close"].diff()
    lon = dc > a.shift(1)
    ban = (-dc) > a.shift(1)

    v = np.zeros(len(df))
    cur = 0
    L, B = lon.to_numpy(), ban.to_numpy()
    for i in range(len(df)):
        if L[i]:
            cur = 1
        elif B[i]:
            cur = -1
        v[i] = cur
    return pd.Series(v, index=df.index).shift(1).fillna(0)   # dich: biet tu bar sau


def chay(df, v):
    """Loi suat theo bar, vao/ra tai OPEN. Tinh ca spread lan phi qua dem."""
    o = df["open"].to_numpy()
    r = np.zeros(len(df))
    r[1:] = np.log(o[1:] / o[:-1])          # loi suat open->open cua bar hien tai
    vv = v.to_numpy()

    tho = vv * r
    doi = np.abs(np.diff(np.r_[0.0, vv]))   # 0 / 1 / 2 (dao chieu = 2 lan phi)
    phi_spread = doi * (SPREAD_BPS / 1e4)

    # Phi qua dem: chi ap cho vi the DAI (giu CFD dai tra tien); vi the ngan thuong
    # duoc nhan lai nhung o CFD chi so thuong van am - de 0 cho than trong mot chieu.
    ngay = np.r_[0, np.diff(df.index.values).astype("timedelta64[D]").astype(float)]
    phi_dem = np.where(vv > 0, PHI_NAM * ngay / 365.0, 0.0)

    return tho - phi_spread - phi_dem, tho


def chi_so(r, ngay_index):
    n_nam = (ngay_index[-1] - ngay_index[0]).days / 365.25
    tong = float(np.nansum(r))
    cagr = np.expm1(tong / n_nam) if n_nam > 0 else np.nan
    sd = np.nanstd(r) * np.sqrt(252)
    sharpe = (np.nanmean(r) * 252) / sd if sd > 0 else np.nan
    von = np.nancumsum(r)
    dd = float(np.nanmin(von - np.maximum.accumulate(von)))
    return {"cagr": cagr, "sharpe": sharpe, "maxdd": np.expm1(dd)}


def mot_thi_truong(khoa, df, rng):
    if len(df) < 800:
        return None
    v = vi_the(df)
    if (v != 0).sum() < 200:
        return None
    r_rong, r_tho = chay(df, v)
    idx = df.index

    he = chi_so(r_rong, idx)

    # MUA-GIU: ca hai ban (quy tac 3)
    o = df["open"].to_numpy()
    r_mg = np.zeros(len(df)); r_mg[1:] = np.log(o[1:] / o[:-1])
    ngay = np.r_[0, np.diff(idx.values).astype("timedelta64[D]").astype(float)]
    mg_khong_phi = chi_so(r_mg, idx)
    mg_co_phi = chi_so(r_mg - PHI_NAM * ngay / 365.0, idx)

    # Placebo: hoan vi CHUOI VI THE theo KHOI (giu cum), khong hoan vi lai/lo
    null = []
    kh = 20
    so_kh = len(v) // kh
    for _ in range(HOAN_VI):
        thu_tu = rng.permutation(so_kh)
        vp = np.concatenate([v.to_numpy()[k * kh:(k + 1) * kh] for k in thu_tu])
        vp = np.r_[vp, np.zeros(len(v) - len(vp))]
        rp = vp * (np.r_[0, np.log(o[1:] / o[:-1])])
        rp = rp - np.abs(np.diff(np.r_[0.0, vp])) * (SPREAD_BPS / 1e4) \
             - np.where(vp > 0, PHI_NAM * ngay / 365.0, 0.0)
        null.append(np.nansum(rp))
    null = np.array(null)
    qs = float(np.nansum(r_rong))
    z = (qs - null.mean()) / null.std() if null.std() > 0 else np.nan

    return {"thi_truong": khoa,
            "thong_ke": float(he["sharpe"] - mg_co_phi["sharpe"]),   # DAU = hon mua-giu
            "p": float(((null >= qs).sum() + 1) / (HOAN_VI + 1)),
            "n": int((np.abs(np.diff(np.r_[0.0, v.to_numpy()])) > 0).sum()),
            "cagr": he["cagr"], "sharpe": he["sharpe"], "maxdd": he["maxdd"],
            "mg_cagr": mg_co_phi["cagr"], "mg_sharpe": mg_co_phi["sharpe"],
            "mg0_cagr": mg_khong_phi["cagr"], "mg0_sharpe": mg_khong_phi["sharpe"],
            "z_placebo": z}


def main():
    tt = bc.nap_tap_sang()
    ket = []
    for khoa, df in tt.items():
        gom = []
        for hat in HAT[:3]:
            r = mot_thi_truong(khoa, df, np.random.default_rng(hat))
            if r:
                gom.append(r)
        if not gom:
            continue
        r0 = dict(gom[0])
        r0["p"] = max(g["p"] for g in gom)      # hat XAU NHAT
        ket.append(r0)
        print(f"  {khoa:<12} CAGR {r0['cagr']*100:+6.2f}%  Sharpe {r0['sharpe']:+5.2f} | "
              f"mua-giu {r0['mg_cagr']*100:+6.2f}% / {r0['mg_sharpe']:+5.2f} | "
              f"hieu {r0['thong_ke']:+5.2f} | {r0['n']} lenh")

    if not ket:
        print("khong chay duoc"); return
    gop = bc.gop_thi_truong(ket, "thong_ke")

    md = ["# KIEM 'VOLATILITY SYSTEM' (Wilder 1978)", "",
          f"*Chay {pd.Timestamp.now():%Y-%m-%d %H:%M}. Nguon: freqtrade-strategies "
          f"(GPL-3.0), `futures/VolatilitySystem.py`, dan ve TradingView 3hhs0XbR.*", "",
          "**Luat:** `ATR2 = ATR(14)x2`; LONG khi `close-close[-1] > ATR2[-1]`; SHORT khi "
          "nguoc lai; dao chieu lien tuc, luon o trong thi truong, khong cat lo.", "",
          f"**Chi phi ap dung:** spread {SPREAD_BPS} bps moi chan (do that tren 168 lenh "
          f"khop) + phi qua dem {PHI_NAM*100:.0f}%/nam theo so dem giu that.", "",
          f"**Gop: {gop['so_duong']}/{gop['so_thi_truong']} thi truong hon mua-giu "
          f"({gop['nhom_duong']}/{gop['so_nhom']} NHOM), trung vi hieu Sharpe "
          f"{gop['trung_vi']:+.3f}, p theo nhom = {gop['p_theo_nhom']:.4f}**", "",
          "| thi truong | CAGR he | Sharpe he | maxDD | CAGR mua-giu (co phi) | Sharpe "
          "mua-giu | hieu Sharpe | z placebo | so lenh |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(ket, key=lambda x: -x["thong_ke"]):
        md.append(f"| {r['thi_truong']} | {r['cagr']*100:+.2f}% | {r['sharpe']:+.2f} | "
                  f"{r['maxdd']*100:.1f}% | {r['mg_cagr']*100:+.2f}% | "
                  f"{r['mg_sharpe']:+.2f} | **{r['thong_ke']:+.2f}** | "
                  f"{r['z_placebo']:+.2f} | {r['n']} |")
    md += ["", "> Cot `hieu Sharpe` = Sharpe he tru Sharpe mua-giu CO PHI. Duong = thang "
                "mua-giu. Day la moc bat buoc cua du an: 324 phep thu truoc day, 0 cai "
                "vuot duoc mua-giu.", ""]
    RA.write_text("\n".join(md), encoding="utf-8")
    print(f"\nGOP: {gop['so_duong']}/{gop['so_thi_truong']} hon mua-giu "
          f"({gop['nhom_duong']}/{gop['so_nhom']} nhom), p={gop['p_theo_nhom']:.4f}")
    print(f"-> {RA}")


if __name__ == "__main__":
    main()
