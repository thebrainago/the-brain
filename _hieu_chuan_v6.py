# -*- coding: utf-8 -*-
"""_hieu_chuan_v6.py - CONG PASS CO CHO MOT HE TA BIET LA TOT DI QUA KHONG?

O so 1 cua `KE_HOACH_HOAN_THIEN.md`. Van de `hieu_chuan_v6` mo tu 15/08/2026.

## VI SAO PHAI CO

Cong da co HAI phep hieu chuan: `null_ty_le_lot` (thu khong co edge co lot
khong) va `thu_luc_cong` (thu co edge nhan tao co qua khong). Ca hai deu dung
tin hieu NHAN TAO. Thieu phep thu ba: **mot he THAT ma du an tin la tot** -
neu cong danh truot no thi 14 PASS hien co khong doc duoc.

Ban thu 15/08 dung IBS < 0,2 don gian tren US500M/US500CASH D1 va bi FAIL:

    US500M_D1     sharpe_he 0,173 vs mua-giu 0,378   FAIL
    US500CASH_D1  sharpe_he 0,269 vs mua-giu 0,330   FAIL

Nhung do CHUA phai V6. Ba thu con thieu, ghi trong chinh van de:
  (a) lop `bias > 0`
  (b) danh muc chi so My thay vi mot ma
  (c) **bar D1 theo PHIEN My**, khong phai bar UTC cua CFD

## CACH LAM: THEO BAC, MOI BAC THEM DUNG MOT MANH

Xay lai ca V6 roi doc mot con so "dat/khong dat" thi khong biet manh nao dong
gop bao nhieu. Nen:

    bac 1  IBS tren CFD, bar UTC, mot ma        <- moc, phai khop ban thu 15/08
    bac 2  IBS tren chuoi CASH DAILY, mot ma    <- co lap manh (c)
    bac 3  bac 2 + danh muc                     <- co lap manh (b)
    bac 4  bac 3 + lop bias                     <- manh (a), LAM SAU neu can

Neu bac 3 da qua cong thi khong can dung toi (a), va cau hoi hieu chuan da co
loi dap.

## RANG BUOC DU LIEU DA DO (12/09)

Chuoi CASH DAILY cua chi so My trong kho chi co **HAI**: `SP500` (1927-2026) va
`YH_NASDAQ` (1971-2026). Khong co Dow. Van de `hieu_chuan_v6` viet "danh muc 3
chi so My" - **khong dung duoc 3, chi dung duoc 2**. Ghi ra day thay vi lang le
lam 2 roi bao la 3.

`XM_US30CASH` khong co du lieu trong ngay, `XM_US500CASH`/`XM_US100CASH` chi co
M30 tu 2025 - nen KHONG the dung `nap_phien` gop bar phien cho danh muc.

## KHONG CHIEM SUAT FDR

`ghi_so=False` o moi loi goi. Day la DO HIEU CHUAN, khong phai dang ky phep thu.

Chay:  python _hieu_chuan_v6.py
Ra:    reports/HIEU_CHUAN_V6.json
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402

from nhan import chi_phi as CP  # noqa: E402
from nhan import cong as CONG  # noqa: E402
from nhan import du_lieu as DL  # noqa: E402
from nhan import mo_phong as MP  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402

RA = LAB / "reports" / "HIEU_CHUAN_V6.json"

#: V6 = mua khi gia dong cua nam o 20% DUOI cua bien do ngay, giu 1 ngay.
NGUONG_IBS = 0.2


def spec_v6() -> dict:
    return {
        "ten": "v6_ibs_bat_day", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
        "co_che": ("V6 cua chinh du an: mua khi gia dong cua nam o 20%% duoi bien do "
                   "ngay (IBS < 0,2), giu mot ngay. Dung lam MOC HIEU CHUAN cong, "
                   "khong phai mot gia thuyet moi."),
        "vao": [{"trai": {"chi_bao": "ibs"}, "phep": "<",
                 "phai": {"hang": NGUONG_IBS}}],
        "ra": [],
    }


def _cp(ma, d):
    c = CP.tu_du_lieu(ma, d)
    return c[0] if isinstance(c, tuple) else c


def mot_ma(ma: str, nhan: str) -> dict:
    """Chay V6 tren mot ma, cham cong, tra bao cao."""
    df = DL.nap(ma, "D1")
    cp = _cp(ma, df)
    th = np.asarray(NP.sinh_tu_spec(spec_v6(), df), float)
    kq = MP.chay(df, th, cp, ma=ma, khung="D1", gop="so_hoc")
    bh = MP.mua_giu(df, cp, ma=ma, khung="D1")
    che_do = "giao_dich" if getattr(cp, "do_tin", "") == "SAN" else "nghien_cuu"
    kt = CONG.xet(df, kq, bh, cp, gt_ma=f"HIEUCHUAN_V6.{ma}.D1",
                  ho="hieu_chuan", che_do=che_do, ghi_so=False)
    ss = kt["so_sanh"]
    dk = kt["dieu_kien"]
    return {"bac": nhan, "ma": ma, "so_bar": len(df),
            "tu": str(df.index[0].date()), "den": str(df.index[-1].date()),
            "che_do": che_do, "chi_phi_do_tin": getattr(cp, "do_tin", "?"),
            "verdict": kt["verdict"],
            "he_sharpe": round(ss["he"]["sharpe"], 4),
            "bh_sharpe": round(ss["mua_giu_net"]["sharpe"], 4),
            "he_cagr_pct": round(ss["he"]["cagr_pct"], 3),
            "bh_cagr_pct": round(ss["mua_giu_net"]["cagr_pct"], 3),
            "phoi_nhiem": round(ss["he"].get("phoi_nhiem", 0), 4),
            "truot": [k for k, v in dk.items() if not v],
            "_kq": kq, "_bh": bh, "_df": df, "_cp": cp}


def danh_muc(cac: list[dict], nhan: str) -> dict:
    """Gop CHUOI LOI SUAT cua nhieu ma, chia deu, roi cham cong tren ma dai nhat.

    Gop o muc loi suat chu khong o muc tin hieu: hai chi so co lich giao dich
    hoi khac nhau, gop tin hieu se lam lech hang ngay.
    """
    import pandas as pd
    lo_he, lo_bh = [], []
    for c in cac:
        idx = c["_df"].index
        lo_he.append(pd.Series(np.asarray(c["_kq"].loi, float), index=idx))
        lo_bh.append(pd.Series(np.asarray(c["_bh"].loi, float), index=idx))
    he = pd.concat(lo_he, axis=1).dropna().mean(axis=1)
    bh = pd.concat(lo_bh, axis=1).dropna().mean(axis=1)
    if len(he) < 300:
        return {"bac": nhan, "loi": "chong lan chi %d bar" % len(he)}

    goc = cac[0]
    df = goc["_df"].loc[he.index]
    def _kq(loi, vi_the, so_lenh, so_lan_doi, phoi_nhiem):
        return MP.KetQua(
            ma="DANH_MUC", khung="D1", index=loi.index,
            vi_the=vi_the, loi=loi.to_numpy(), loi_tho=loi.to_numpy(), r=None,
            chi_phi_spread=0.0, chi_phi_truot=0.0, chi_phi_giu=0.0,
            so_lan_doi=so_lan_doi, so_lenh=so_lenh, phoi_nhiem=phoi_nhiem,
            canh_bao=[], che_do_gop="so_hoc", don_bay=1.0,
            chay_tai_khoan=False, bar_chay=len(loi), ngay_chay="")

    kq = _kq(he, np.ones(len(he)),
             sum(int(c["_kq"].so_lenh) for c in cac),
             sum(int(c["_kq"].so_lan_doi) for c in cac),
             float(np.mean([c["phoi_nhiem"] for c in cac])))
    bhq = _kq(bh, np.ones(len(bh)), 1, 1, 1.0)
    kt = CONG.xet(df, kq, bhq, goc["_cp"], gt_ma="HIEUCHUAN_V6.DANH_MUC.D1",
                  ho="hieu_chuan", che_do="nghien_cuu", ghi_so=False)
    ss = kt["so_sanh"]
    dk = kt["dieu_kien"]
    return {"bac": nhan, "ma": " + ".join(c["ma"] for c in cac),
            "so_bar": len(he), "tu": str(he.index[0].date()),
            "den": str(he.index[-1].date()), "verdict": kt["verdict"],
            "he_sharpe": round(ss["he"]["sharpe"], 4),
            "bh_sharpe": round(ss["mua_giu_net"]["sharpe"], 4),
            "he_cagr_pct": round(ss["he"]["cagr_pct"], 3),
            "bh_cagr_pct": round(ss["mua_giu_net"]["cagr_pct"], 3),
            "truot": [k for k, v in dk.items() if not v]}


def main() -> int:
    print("=" * 92)
    print("HIEU CHUAN CONG BANG V6 - cong co cho mot he TA TIN LA TOT di qua khong?")
    print("=" * 92)
    bac = []

    print("\n--- BAC 1: IBS tren CFD, bar UTC, mot ma (moc, phai khop ban thu 15/08) ---")
    for ma in ("XM_US500CASH", "US500CASH"):
        try:
            bac.append(mot_ma(ma, "1_cfd_utc"))
        except Exception as e:
            bac.append({"bac": "1_cfd_utc", "ma": ma, "loi": f"{type(e).__name__}: {e}"})

    print("\n--- BAC 2: IBS tren chuoi CASH DAILY (= bar phien My), mot ma ---")
    for ma in ("SP500", "YH_NASDAQ"):
        try:
            bac.append(mot_ma(ma, "2_cash_phien"))
        except Exception as e:
            bac.append({"bac": "2_cash_phien", "ma": ma, "loi": f"{type(e).__name__}: {e}"})

    print("\n%-16s %-14s %7s %9s %9s %9s %9s  %s"
          % ("bac", "ma", "bar", "he Sharpe", "BH Sharpe", "he CAGR%", "BH CAGR%", "verdict"))
    print("-" * 104)
    for b in bac:
        if "loi" in b:
            print("%-16s %-14s  LOI: %s" % (b["bac"], b["ma"], b["loi"][:60]))
            continue
        print("%-16s %-14s %7d %9.3f %9.3f %9.2f %9.2f  %s"
              % (b["bac"], b["ma"][:14], b["so_bar"], b["he_sharpe"], b["bh_sharpe"],
                 b["he_cagr_pct"], b["bh_cagr_pct"], b["verdict"]))
        if b.get("truot"):
            print("%-32s truot: %s" % ("", ", ".join(b["truot"])[:70]))

    print("\n--- BAC 3: DANH MUC cash daily (SP500 + NASDAQ, chia deu) ---")
    cac = [b for b in bac if b["bac"] == "2_cash_phien" and "loi" not in b]
    dm = None
    if len(cac) >= 2:
        dm = danh_muc(cac, "3_danh_muc")
        if "loi" in dm:
            print("  ", dm["loi"])
        else:
            print("  %-28s %7d bar %s -> %s"
                  % (dm["ma"], dm["so_bar"], dm["tu"], dm["den"]))
            print("  he Sharpe %.3f vs mua-giu %.3f | he CAGR %.2f%% vs %.2f%% | %s"
                  % (dm["he_sharpe"], dm["bh_sharpe"], dm["he_cagr_pct"],
                     dm["bh_cagr_pct"], dm["verdict"]))
            if dm.get("truot"):
                print("  truot:", ", ".join(dm["truot"]))
        bac.append(dm)

    for b in bac:
        for k in ("_kq", "_bh", "_df", "_cp"):
            b.pop(k, None)
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps({"nguong_ibs": NGUONG_IBS, "bac": bac},
                             ensure_ascii=False, indent=1, default=str),
                  encoding="utf-8")
    print("\n-> %s" % RA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
