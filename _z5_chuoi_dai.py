# -*- coding: utf-8 -*-
"""_z5_chuoi_dai.py - z5 TREN 22 NAM: co che that hay hien tuong cua mot thoi ky?

Viec so 4 cua khoi 7.

## VI SAO PHEP THU NAY LA PHEP THU QUYET DINH

`mean_reversion_z5` la ung vien manh nhat du an tung co: tren XM_US100CASH D1
no cho Sharpe 1,158 · Calmar 1,04 · alpha 10,36%/nam (t = 2,85) · placebo
p = 0,01, va DA qua FDR (dong 1836, p 0,0045 < nguong 0,0197).

Nhung do 12/09: **MDE do duoc cua XM_US100CASH|D1 la 1,135** tren 1.598 bar.

    Sharpe 1,158 / MDE 1,135 = **1,02 lan**

Tuc no nam DUNG TREN SAN PHAT HIEN cua chinh chuoi do. Mot hieu ung o sat san
phat hien thi khong phan biet duoc "nho ma that" voi "khong co ma may".

Chuoi dai hon co san giai quyet duoc chuyen nay:

    YH_NASDAQ|D1   5.598 bar (~22,2 nam)   MDE 0,541
    cung Sharpe do -> 1,158 / 0,541 = **2,14 lan**

Neu co che la that thi no phai hien ra tren 22 nam. Neu no bien mat thi con so
6,3 nam la mot cuc tri cua giai doan.

## BA CAU HOI, KHONG PHAI MOT

1. **Co che con khong tren 22 nam?** Sharpe, alpha so voi mua-giu.
2. **Cao nguyen hay cai gai?** Quet (n, nguong z) TREN CHUOI DAI. Ban do 6 nam
   de ra cao nguyen gia vi moi o deu nhieu nhu nhau.
3. **Co phai hien tuong cua MOT THOI KY?** Tach theo thap ky. Du an da gap dung
   viec nay voi IBS: edge chi ton tai sau 2000. Neu z5 cung vay thi 22 nam
   "duong" chi la trung binh cua mot nua song va mot nua chet.

## CHE DO NGHIEN CUU

YH_NASDAQ la chuoi CHI SO, khong mua duoc. `cong.xet(che_do="nghien_cuu")` sinh
ra dung cho truong hop nay: verdict cao nhat la CO_CO_CHE, khong bao gio PASS.
Muc dich o day khong phai lay PASS ma la hoi **co che co ton tai khong**.

Chay:  python _z5_chuoi_dai.py [MA]
Ra:    reports/Z5_CHUOI_DAI.json
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

from nhan import bien_don_bay as B  # noqa: E402
from nhan import chi_phi as CP  # noqa: E402
from nhan import do_luc as DLUC  # noqa: E402
from nhan import du_lieu as DL  # noqa: E402
from nhan import mo_phong as MP  # noqa: E402
from nhan import ngu_phap as NP  # noqa: E402

RA = LAB / "reports" / "Z5_CHUOI_DAI.json"
MA = sys.argv[1] if len(sys.argv) > 1 else "YH_NASDAQ"
KHUNG = "D1"


def spec_voi(n: int, nguong: float) -> dict:
    return {"ten": "z%d_duoi_%.2f" % (n, nguong), "ho": "quay_ve_trung_binh",
            "chieu": 1, "giu": 500,
            "co_che": "Mua khi gia giam sau duoi trung binh %d ngay, ky vong hoi phuc." % n,
            "vao": [{"trai": {"chi_bao": "zscore",
                              "cua": {"chi_bao": "gia", "cot": "close"}, "n": n},
                     "phep": "<", "phai": {"hang": float(nguong)}}],
            "ra": [{"trai": {"chi_bao": "zscore",
                             "cua": {"chi_bao": "gia", "cot": "close"}, "n": n},
                    "phep": ">=", "phai": {"hang": float(nguong)}}]}


def _cp(d, ma):
    c = CP.tu_du_lieu(ma, d)
    return c[0] if isinstance(c, tuple) else c


def do_mot(d, spec, cp, ma, don_bay=1.0):
    v = np.asarray(NP.sinh_tu_spec(spec, d), float)
    kq = MP.chay(d, v, cp, ma=ma, khung=KHUNG, don_bay=don_bay, gop="so_hoc")
    c = B._chi_so(kq)
    c["so_lenh"] = int(kq.so_lenh)
    c["phoi_nhiem_vao"] = float(np.mean(v > 0))
    return c


def mua_giu(d, cp, ma):
    v = np.ones(len(d), float)
    kq = MP.chay(d, v, cp, ma=ma, khung=KHUNG, don_bay=1.0, gop="so_hoc")
    return B._chi_so(kq)


def main() -> int:
    df = DL.nap(MA, KHUNG)
    nam = (df.index[-1] - df.index[0]).days / 365.25
    cp = _cp(df, MA)
    mde = (DLUC._doc_mde_cache().get("%s|%s" % (MA, KHUNG)) or {}).get("mde")

    print("=" * 78)
    print("z5 TREN CHUOI DAI: %s %s" % (MA, KHUNG))
    print("=" * 78)
    print("%d bar · %s -> %s · %.1f nam · MDE do duoc: %s"
          % (len(df), df.index[0].date(), df.index[-1].date(), nam,
             ("%.3f" % mde) if mde else "chua do"))

    # ------------------------------------------------ 1. co che con khong?
    goc = spec_voi(5, -1.0)
    he = do_mot(df, goc, cp, MA)
    bh = mua_giu(df, cp, MA)
    ti = (he["sharpe"] / mde) if mde else None
    print("\n--- 1. CO CHE CON KHONG TREN %.1f NAM ---" % nam)
    print("  %-14s %9s %9s %9s %9s %8s" % ("", "CAGR%", "Sharpe", "Calmar", "maxDD%", "lenh"))
    print("  %-14s %9.2f %9.3f %9.3f %9.1f %8d"
          % ("z5", he["cagr"] * 100, he["sharpe"], he.get("calmar", 0),
             he["maxdd"] * 100, he["so_lenh"]))
    print("  %-14s %9.2f %9.3f %9.3f %9.1f %8s"
          % ("MUA-GIU", bh["cagr"] * 100, bh["sharpe"], bh.get("calmar", 0),
             bh["maxdd"] * 100, "-"))
    print("  phoi nhiem %.1f%% so bar" % (100 * he["phoi_nhiem_vao"]))
    if ti:
        print("  Sharpe / MDE = %.3f / %.3f = **%.2f lan**  (tren XM_US100CASH la 1,02)"
              % (he["sharpe"], mde, ti))

    # ------------------------------------------------ 2. cao nguyen hay cai gai
    print("\n--- 2. CAO NGUYEN HAY CAI GAI (tren ca %.1f nam) ---" % nam)
    ns = [3, 4, 5, 6, 8, 10, 15, 20]
    ngs = [-0.5, -0.75, -1.0, -1.25, -1.5, -2.0]
    print("  So la SHARPE. Cot = nguong z, hang = cua so n.")
    print("  %-5s" % "n" + "".join("%9.2f" % g for g in ngs))
    bang = {}
    for n in ns:
        hang = []
        for g in ngs:
            try:
                hang.append(do_mot(df, spec_voi(n, g), cp, MA)["sharpe"])
            except Exception:
                hang.append(float("nan"))
        bang[str(n)] = [None if not np.isfinite(x) else round(x, 3) for x in hang]
        print("  %-5d" % n + "".join(
            ("%9.2f" % x) if np.isfinite(x) else "        -" for x in hang))
    arr = np.array([[x if x is not None else np.nan for x in bang[str(n)]]
                    for n in ns], float)
    tren_mde = int(np.nansum(arr > (mde or 0)))
    print("  o co Sharpe > MDE (%.3f): %d/%d   | tot nhat %.2f | trung vi %.2f"
          % (mde or 0, tren_mde, arr.size, np.nanmax(arr), np.nanmedian(arr)))
    print("  >> Nhieu o lien nhau cung tren MDE = cao nguyen. Mot o = cai gai.")

    # ------------------------------------------------ 3. hien tuong cua thoi ky?
    print("\n--- 3. CO PHAI HIEN TUONG CUA MOT THOI KY ---")
    print("  (du an da gap: IBS chi song sau 2000. Neu z5 cung vay thi trung binh"
          " 22 nam chi la mot nua song cong mot nua chet.)")
    print("  %-12s %8s %9s %9s %9s %7s" % ("giai doan", "bar", "z5 CAGR%",
                                           "z5 Sharpe", "BH CAGR%", "lenh"))
    theo_ky = []
    moc = [(str(y), str(y + 4)) for y in range(df.index[0].year, df.index[-1].year, 5)]
    for a, b in moc:
        sub = df.loc[a:b]
        if len(sub) < 250:
            continue
        cps = _cp(sub, MA)
        try:
            h = do_mot(sub, goc, cps, MA)
            m = mua_giu(sub, cps, MA)
        except Exception:
            continue
        theo_ky.append({"tu": a, "den": b, "bar": len(sub),
                        "z5_cagr": round(h["cagr"] * 100, 2),
                        "z5_sharpe": round(h["sharpe"], 3),
                        "bh_cagr": round(m["cagr"] * 100, 2),
                        "so_lenh": h["so_lenh"]})
        print("  %-12s %8d %9.2f %9.3f %9.2f %7d"
              % ("%s-%s" % (a, b), len(sub), h["cagr"] * 100, h["sharpe"],
                 m["cagr"] * 100, h["so_lenh"]))
    duong = sum(1 for x in theo_ky if x["z5_cagr"] > 0)
    print("  giai doan DUONG: %d/%d" % (duong, len(theo_ky)))

    ket = {"ma": MA, "khung": KHUNG, "so_bar": len(df), "so_nam": round(nam, 2),
           "mde": mde, "z5": {k: (round(v, 4) if isinstance(v, float) else v)
                              for k, v in he.items()},
           "mua_giu": {k: (round(v, 4) if isinstance(v, float) else v)
                       for k, v in bh.items()},
           "sharpe_tren_mde": round(ti, 3) if ti else None,
           "ban_do_sharpe": {"n": ns, "nguong": ngs, "bang": bang,
                             "o_tren_mde": tren_mde, "tong_o": int(arr.size)},
           "theo_giai_doan": theo_ky, "giai_doan_duong": duong,
           "so_giai_doan": len(theo_ky)}
    RA.parent.mkdir(exist_ok=True)
    RA.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float),
                  encoding="utf-8")
    print("\n-> %s" % RA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
