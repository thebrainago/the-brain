# -*- coding: utf-8 -*-
"""_gop_khong_chon.py - BO HAN KHAU CHON: gop DEU moi chan duong tren train.

Viec so 3 cua khoi 7. Hai phep thu truoc deu AM va chung chi ra cung mot thu:

  `_placebo_quan_tri.py`  ho trailing truot placebo (p = 0,596)
  `_placebo_ghep.py`      xep hang cap tren train KHONG mang thong tin (0/3 ma),
                          va 77-93% cap BAT KY hon he don o holdout

Cai thu hai quan trong hon: no noi rang **phep cong co tac dung that** (cong cac
duong von tuong quan khong hoan hao thi sut giam giam theo so hoc), chi rieng
viec CHON la vo nghia. Vay phien ban trung thuc cua "ghep" khong phai chon cap
dep ma la: **lay HET chan duong tren train, chia deu, khong xep hang gi ca.**

## HAI LOI DA MAC O BAN DAU CUA FILE NAY - GHI LAI DE KHONG LAP

1. **`_ghep_he._sut_giam` nhan LAI USD tren tai khoan co `VON`, khong nhan chuoi
   phan tram.** Dua chuoi % vao thi no coi "+103,7" la "+103,70 USD tren 10.000
   USD" -> sut giam mua-giu cua US100 giai doan 2021-2026 ra **0,4%** trong khi
   that la **35,5%**. Dau hieu nhan ra: mot con so rui ro nho den muc vo ly.

2. **Diem `lai/sut_giam` dung khap cac script ghep la USD CHIA CHO PHAN TRAM.**
   No van XEP HANG dung (ti le thuan voi Calmar that khi `VON` co dinh) nhung
   **khong phai Calmar**, va dem so sanh voi mot moc tinh bang don vi khac thi sai.
   Calmar that = diem x 100 / VON. File nay quy het ve **Calmar that**.

## BA MOC PHAI CO TRONG CUNG MOT BANG

  1. he don dau bang train
  2. gop DEU N chan (khong chon)
  3. **MUA-GIU cung cua so** - quy tac cua du an, thieu no thi mot so duong
     khong noi len dieu gi

Chay:  python _gop_khong_chon.py [SYMBOL]
Ra:    reports/GOP_KHONG_CHON_<SYMBOL>.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import numpy as np  # noqa: E402

import _ghep_he as GH  # noqa: E402
from nhan import du_lieu as DL  # noqa: E402

BC = LAB / "reports"
CAT = "2021.06.01"
#: Ten trong `DEM_VON_*` la ten SLOT cua EA; kho gia luu duoi tien to XM_.
MAP = {"US100Cash": "XM_US100CASH", "US30Cash": "XM_US30CASH",
       "US500Cash": "XM_US500CASH"}


def calmar_he(pnl: list[float]) -> tuple[float, float, float]:
    """pnl = lai luy ke USD tren tai khoan `GH.VON` -> (loi %, sut giam %, Calmar)."""
    von = GH.VON
    dinh, xau = von + pnl[0], 0.0
    for p in pnl:
        v = von + p
        dinh = max(dinh, v)
        xau = max(xau, dinh - v)
    loi = pnl[-1] / von
    return 100 * loi, 100 * xau / von, (loi / (xau / von) if xau > 0 else 0.0)


def calmar_gia(c) -> tuple[float, float, float]:
    """Mua-giu tren chuoi GIA -> (loi %, sut giam %, Calmar). Khong dung
    `_sut_giam` o day: ham do doi don vi USD."""
    c = np.asarray(c, dtype=float)
    dinh = np.maximum.accumulate(c)
    dd = float(np.max((dinh - c) / dinh))
    loi = float(c[-1] / c[0] - 1.0)
    return 100 * loi, 100 * dd, (loi / dd if dd > 0 else 0.0)


def mot_ma(ma: str) -> dict | None:
    f = BC / ("DEM_VON_%s.json" % ma)
    if not f.exists():
        return None
    d = json.load(open(f, encoding="utf-8"))
    tg, von = d["tg"], d["von"]
    i = next((k for k, x in enumerate(tg) if x[:10] >= CAT), len(tg) // 2)
    tr = {t: [v[j] - v[0] for j in range(0, i)] for t, v in von.items()}
    ho = {t: [v[j] - v[i] for j in range(i, len(tg))] for t, v in von.items()}

    thay, giu = {}, []
    for t in sorted(tr):
        k = tuple(round(x, 2) for x in tr[t])
        if k in thay:
            continue
        thay[k] = t
        giu.append(t)
    dd_tr = {t: GH._sut_giam(tr[t]) for t in giu}
    duong = [t for t in giu if tr[t][-1] > 0 and dd_tr[t] > 0]
    if len(duong) < 4:
        return None

    # MOI chan sau khu trung deu duong tren train (do 12/09: 73/73, 67/67, 52/52)
    # -> buoc loc "duong tren train" KHONG loai ai. Kho chan da bi loc tu truoc,
    # nen khong the dung no lam null cho chinh no.
    loc_vo_hieu = len(duong) == len(giu)

    don = max(duong, key=lambda t: tr[t][-1] / dd_tr[t])
    gop = [sum(ho[x][k] for x in duong) / len(duong)
           for k in range(len(ho[duong[0]]))]

    sub = DL.nap(MAP[ma], "D1").loc[tg[i][:10].replace(".", "-"):
                                    tg[-1][:10].replace(".", "-")]
    hang = [("he don dau bang train", calmar_he(ho[don])),
            ("GOP DEU %d chan" % len(duong), calmar_he(gop)),
            ("MUA-GIU %s" % MAP[ma], calmar_gia(sub["close"].to_numpy(float)))]

    print("  %s   (%d chan -> %d sau khu trung -> %d duong tren train%s)"
          % (ma, len(von), len(giu), len(duong),
             ", LOC VO HIEU" if loc_vo_hieu else ""))
    print("     %-26s %9s %10s %8s" % ("", "loi %", "sutgiam %", "Calmar"))
    for ten, (l, s, c) in hang:
        print("     %-26s %9.1f %10.1f %8.2f" % (ten, l, s, c))
    c_gop, c_bh = hang[1][1][2], hang[2][1][2]
    print("     -> gop / mua-giu = %.2f lan  => %s"
          % ((c_gop / c_bh) if c_bh else 0,
             "GOP THANG" if c_gop > c_bh else "MUA-GIU THANG"))
    return {"symbol": ma, "cat": CAT, "so_chan": len(von),
            "sau_khu_trung": len(giu), "so_duong_train": len(duong),
            "loc_duong_train_vo_hieu": loc_vo_hieu,
            "bang": {ten: {"loi_pct": round(l, 2), "sut_giam_pct": round(s, 2),
                           "calmar": round(c, 3)} for ten, (l, s, c) in hang},
            "gop_tren_mua_giu": round((c_gop / c_bh) if c_bh else 0, 3),
            "phan_quyet": "GOP THANG" if c_gop > c_bh else "MUA-GIU THANG"}


def main(argv: list[str]) -> int:
    ds = argv or list(MAP)
    print("GOP DEU, KHONG XEP HANG - doc ket qua o HOLDOUT, co moc MUA-GIU")
    print("=" * 74)
    ket = [r for r in (mot_ma(m) for m in ds) if r]
    for r in ket:
        (BC / ("GOP_KHONG_CHON_%s.json" % r["symbol"])).write_text(
            json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print("=" * 74)
    print("GOP thang mua-giu o %d/%d ma"
          % (sum(1 for r in ket if r["phan_quyet"] == "GOP THANG"), len(ket)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
