# -*- coding: utf-8 -*-
"""_quet_chuoi_dai.py - CO CO CHE NAO TRONG KHO VUOT MDE TREN 55/99 NAM KHONG?

Sau khi khoi 7 ra nam ket qua AM, cau hoi con lai la cau rong nhat: **trong ca
1.216 co che cua kho, co cai nao song tren chuoi DAI khong**, hay tat ca deu la
hien tuong che do nhu z5 va quantora.

## THIET KE PHEU - vi sao khong chay ca ba phep cho tat ca

`_thu_chuoi_dai.py` chay ba phep (ca chuoi + ban do 6 o + tach 11-20 giai doan)
= ~18 lan mo phong moi co che. Voi 1.216 co che x 2 chuoi thi la ~44.000 lan
mo phong tren chuoi 14.000 bar - hang chuc gio.

Nen file nay chi chay **phep thu 1** (ca chuoi) cho TAT CA, roi danh sach nao
vuot MDE moi di tiep sang `_thu_chuoi_dai.py` de lam not hai phep con lai.
Chan theo MDE truoc la dung thu tu: mot co che khong vuot noi MDE thi ban do
tham so va tach giai doan cua no khong tra loi cau hoi nao.

## CHAN TREN, KHONG PHAI KET QUA GIAO DICH

Chuoi chi so khong mua duoc, chi phi la KHAI BAO. Con so o day la **chan tren**:
co che nao khong dat o day thi cang khong dat khi co chi phi that. Chieu nguoc
lai KHONG dung - vuot o day mới chi la dieu kien can.

## DO DAC KHONG DUOC CHIEM SUAT FDR

Khong goi `cong.xet` o day, khong ghi so cai. Day la DO, khong phai dang ky.

Chay:  python _quet_chuoi_dai.py [MA] [so_luong] [so_tien_trinh]
Ra:    reports/QUET_CHUOI_DAI_<MA>.json
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402

_DF = None
_CP = None
_MA = None


def _nap(ma: str):
    """Nap mot lan cho moi tien trinh con."""
    global _DF, _CP, _MA
    if _DF is None or _MA != ma:
        from nhan import chi_phi as CP
        from nhan import du_lieu as DL
        _MA = ma
        _DF = DL.nap(ma, "D1")
        c = CP.tu_du_lieu(ma, _DF)
        _CP = c[0] if isinstance(c, tuple) else c
    return _DF, _CP


def mot(args) -> dict:
    ma, spec = args
    import numpy as np
    from nhan import bien_don_bay as B
    from nhan import mo_phong as MP
    from nhan import ngu_phap as NP
    df, cp = _nap(ma)
    ten = str(spec.get("ten", "?"))
    try:
        v = np.asarray(NP.sinh_tu_spec(spec, df), float)
        kh = float(np.mean(np.abs(v) > 0))
        if kh <= 0.0:
            return {"ten": ten, "loi": "khong kich hoat lan nao"}
        kq = MP.chay(df, v, cp, ma=ma, khung="D1", don_bay=1.0, gop="so_hoc")
        c = B._chi_so(kq)
        return {"ten": ten, "ho": spec.get("ho"), "chieu": spec.get("chieu"),
                "sharpe": round(float(c["sharpe"]), 4),
                "_maxdd": float(c["maxdd"]), "_cagr": float(c["cagr"]),
                "cagr_pct": round(float(c["cagr"]) * 100, 3),
                "maxdd_pct": round(float(c["maxdd"]) * 100, 2),
                "calmar": round(float(c.get("calmar", 0)), 4),
                "so_lenh": int(kq.so_lenh), "kich_hoat": round(kh, 4)}
    except Exception as e:
        return {"ten": ten, "loi": "%s: %s" % (type(e).__name__, str(e)[:70])}


def main(argv: list[str]) -> int:
    ma = argv[0] if argv else "YH_NASDAQ"
    gioi_han = int(argv[1]) if len(argv) > 1 else 0
    n_tt = int(argv[2]) if len(argv) > 2 else 4

    from nhan import do_luc as DLUC
    from nhan import du_lieu as DL
    from nhan import ngu_phap as NP

    mde = (DLUC._doc_mde_cache().get("%s|D1" % ma) or {}).get("mde")
    df = DL.nap(ma, "D1")
    nam = (df.index[-1] - df.index[0]).days / 365.25

    kho = NP.doc_kho()
    # Khu trung theo van tay dieu kien: hai ban sao cung mot luat khong phai
    # hai phep thu.
    thay, ds = set(), []
    for s in kho:
        try:
            vt = NP.van_tay_dieu_kien(s)
        except Exception:
            vt = json.dumps(s.get("vao"), sort_keys=True)
        if vt in thay:
            continue
        thay.add(vt)
        ds.append(s)
    if gioi_han:
        ds = ds[:gioi_han]

    print("QUET CA KHO TREN CHUOI DAI: %s D1" % ma)
    print("=" * 76)
    print("%d bar · %.1f nam · MDE %s" % (len(df), nam,
                                          ("%.3f" % mde) if mde else "chua do"))
    print("kho %d co che -> %d sau khu trung dieu kien | %d tien trinh"
          % (len(kho), len(ds), n_tt))

    t0 = time.time()
    ket = []
    with ProcessPoolExecutor(max_workers=n_tt) as ex:
        for i, r in enumerate(ex.map(mot, ((ma, s) for s in ds), chunksize=4), 1):
            ket.append(r)
            if i % 100 == 0:
                ok = [x for x in ket if "loi" not in x]
                tren = sum(1 for x in ok if mde and x["sharpe"] > mde)
                print("  ... %d/%d  (%.0fs)  chay duoc %d · tren MDE %d"
                      % (i, len(ds), time.time() - t0, len(ok), tren), flush=True)

    # MOC MUA-GIU O CUNG RUI RO. Khong co dong nay thi mot bo loc xu huong
    # phoi nhiem 60% tren mot chi so co drift se "vuot MDE" chi vi no LA chi so
    # do. Do 12/09: ba cai dau bang deu phoi nhiem 51-67%.
    from nhan import bien_don_bay as B
    from nhan import chi_phi as CP
    from nhan import mo_phong as MP
    c0 = CP.tu_du_lieu(ma, df)
    cp0 = c0[0] if isinstance(c0, tuple) else c0
    bh = B._chi_so(MP.chay(df, np.ones(len(df), float), cp0, ma=ma, khung="D1",
                           don_bay=1.0, gop="so_hoc"))
    bh_sharpe, bh_dd, bh_cagr = float(bh["sharpe"]), float(bh["maxdd"]), float(bh["cagr"])
    print("MUA-GIU: Sharpe %.3f · CAGR %.2f%% · maxDD %.1f%%"
          % (bh_sharpe, bh_cagr * 100, bh_dd * 100))

    for x in ket:
        if "loi" in x:
            continue
        # Nang don bay he len cung SUT GIAM voi mua-giu roi so CAGR.
        L = (abs(bh_dd) / abs(x["_maxdd"])) if x["_maxdd"] else 0.0
        x["don_bay_khop_dd"] = round(L, 2)
        x["cagr_khop_dd_pct"] = round(x["_cagr"] * L * 100, 2)
        x["hon_mua_giu_cung_dd"] = bool(x["_cagr"] * L > bh_cagr)
        x["hon_mua_giu_sharpe"] = bool(x["sharpe"] > bh_sharpe)
        x.pop("_maxdd", None); x.pop("_cagr", None)

    ok = [x for x in ket if "loi" not in x]
    hong = [x for x in ket if "loi" in x]
    ok.sort(key=lambda x: -x["sharpe"])
    tren = [x for x in ok if mde and x["sharpe"] > mde]
    tren_va_hon = [x for x in tren
                   if x["hon_mua_giu_cung_dd"] and x["hon_mua_giu_sharpe"]]

    print("\n%d chay duoc · %d hong/khong kich hoat" % (len(ok), len(hong)))
    if ok:
        sh = [x["sharpe"] for x in ok]
        print("Sharpe: tot nhat %.3f · phan vi 99%% %.3f · trung vi %.3f · te nhat %.3f"
              % (sh[0], sh[int(0.01 * len(sh))], sh[len(sh) // 2], sh[-1]))
    print("\n>>> VUOT MDE (%.3f): **%d / %d**" % (mde or 0, len(tren), len(ok)))
    if tren:
        print("  %-38s %7s %8s %7s %7s %9s %s"
              % ("ten", "Sharpe", "maxDD%", "kichhoat", "L khop", "CAGR@ddBH", "hon BH"))
        for x in tren[:30]:
            print("  %-38s %7.3f %8.1f %6.1f%% %7.2f %8.2f%%  %s"
                  % (x["ten"][:38], x["sharpe"], x["maxdd_pct"],
                     100 * x["kich_hoat"], x["don_bay_khop_dd"],
                     x["cagr_khop_dd_pct"],
                     "CO" if (x["hon_mua_giu_cung_dd"] and x["hon_mua_giu_sharpe"]) else "-"))
        print("\n>>> VUOT MDE **VA** HON MUA-GIU (ca Sharpe lan CAGR o cung "
              "sut giam): **%d / %d**" % (len(tren_va_hon), len(ok)))
    else:
        print("  khong co cai nao.")

    ra = LAB / "reports" / ("QUET_CHUOI_DAI_%s.json" % ma)
    ra.parent.mkdir(exist_ok=True)
    ra.write_text(json.dumps(
        {"ma": ma, "so_bar": len(df), "so_nam": round(nam, 2), "mde": mde,
         "so_co_che": len(ds), "chay_duoc": len(ok), "hong": len(hong),
         "vuot_mde": len(tren), "vuot_mde_va_hon_mua_giu": len(tren_va_hon),
         "mua_giu": {"sharpe": round(bh_sharpe, 4), "cagr_pct": round(bh_cagr * 100, 3),
                     "maxdd_pct": round(bh_dd * 100, 2)},
         "top": ok[:80], "danh_sach_vuot": tren, "danh_sach_vuot_va_hon": tren_va_hon,
         "giay": round(time.time() - t0, 1)},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> %s  (%.0fs)" % (ra, time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
