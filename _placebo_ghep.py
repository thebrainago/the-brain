# -*- coding: utf-8 -*-
"""_placebo_ghep.py - "CAP GIU HANG O HOLDOUT" LA EDGE, HAY CHI LA PHEP CONG?

Viec so 2 cua khoi 7 (`config/ke_hoach_xay.json`), sau khi ho trailing truot placebo.

## LO HONG PHAI BIT

`_ghep_holdout.py` cham cap bang `lai / sut_giam` cua TONG hai duong von, roi dem
bao nhieu cap dau bang train con hon HE DON o holdout (US100Cash: 14/15).

Nhung cong hai duong von tuong quan khong hoan hao thi sut giam giam **theo so
hoc**, trong khi lai chi cong lai. Tuc `lai/sut_giam` cua mot cap LON HON cua mot
chan **ma khong can edge nao**. Phep so "cap voi he don" thien vi cap ngay tu cau
truc, nen con so 14/15 co the khong noi gi ve viec CHON cap.

## NULL

Rut 15 cap NGAU NHIEN tu dung kho chan do (top 30 theo train, y het ben that),
roi dem bao nhieu cap hon `moc_ho` o holdout. Lap nhieu lan.

  - neu cap ngau nhien cung hon he don ~14/15 lan  -> "giu hang" la PHEP CONG
  - neu chi cap DUOC CHON TREN TRAIN moi hon       -> xep hang train co thong tin

Nhu vay khac biet duy nhat giua that va gia la **viec xep hang tren train**,
dung thu dang duoc hoi.

## SO CUNG CO MAU

Ben that dem tren 15 cap. Ben gia cung phai rut dung 15 cap moi lan roi so PHAN BO
SO DEM - khong duoc dat hai ty le tho canh nhau. Bai hoc 12/09: placebo trailing
lan dau so mot CUC DAI cua 40 voi tung ban gia LE, p ra 0,0249 thay vi 0,5958.

Khong ton mot lan backtest nao: duong von tung chan da co san.

Chay:  python _placebo_ghep.py [SYMBOL] [MOC_CAT]
Ra:    reports/PLACEBO_GHEP_<SYMBOL>.json
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import _ghep_he as GH  # noqa: E402

BC = LAB / "reports"
TOP = 30
N_CAP = 15
N_BOOT = 20000
HAT = 20260912


def doan(von: dict, tu_i: int, den_i: int) -> dict:
    return {t: [v[j] - v[tu_i] for j in range(tu_i, den_i)]
            for t, v in von.items()}


def cham(d: dict, bo: list) -> float:
    t = [sum(d[x][k] for x in bo) for k in range(len(d[bo[0]]))]
    dd = GH._sut_giam(t)
    return (t[-1] / dd) if dd > 0 else 0.0


def mot_ma(ma: str, cat: str) -> dict | None:
    f = BC / ("DEM_VON_%s.json" % ma)
    if not f.exists():
        print("  khong co %s" % f.name)
        return None
    d = json.load(open(f, encoding="utf-8"))
    tg, von = d["tg"], d["von"]
    i = next((k for k, x in enumerate(tg) if x[:10] >= cat), len(tg) // 2)
    tr, ho = doan(von, 0, i), doan(von, i, len(tg))

    # Khu trung + chon top theo TRAIN - sao y `_ghep_holdout` de so duoc.
    thay, giu = {}, []
    for t in sorted(tr):
        k = tuple(round(x, 2) for x in tr[t])
        if k in thay:
            continue
        thay[k] = t
        giu.append(t)
    duong = [t for t in giu if tr[t][-1] > 0]
    dd_tr = {t: GH._sut_giam(tr[t]) for t in duong}
    don = sorted((t for t in duong if dd_tr[t] > 0),
                 key=lambda t: -tr[t][-1] / dd_tr[t])[:TOP]
    if len(don) < 4:
        print("  %s: chi %d chan duong tren train - bo qua" % (ma, len(don)))
        return None
    moc_ho = cham(ho, [don[0]])

    moi = [(don[a], don[b]) for a in range(len(don))
           for b in range(a + 1, len(don))]
    diem_tr = {p: cham(tr, list(p)) for p in moi}
    diem_ho = {p: cham(ho, list(p)) for p in moi}

    that = sorted(moi, key=lambda p: -diem_tr[p])[:N_CAP]
    n_that = sum(1 for p in that if diem_ho[p] > moc_ho)

    r = random.Random(HAT)
    dem_gia = []
    for _ in range(N_BOOT):
        mau = r.sample(moi, N_CAP)
        dem_gia.append(sum(1 for p in mau if diem_ho[p] > moc_ho))
    p = (sum(1 for k in dem_gia if k >= n_that) + 1) / (N_BOOT + 1)
    dem_gia_sx = sorted(dem_gia)

    # Chieu thu hai: ti le cap BAT KY hon he don o holdout. Gan 100% thi "hon he
    # don" la tinh chat cua phep cong, khong phai cua viec chon.
    ty_le_moi_cap = sum(1 for p in moi if diem_ho[p] > moc_ho) / len(moi)

    print("  %-12s chan %3d -> top %2d · %4d cap · moc he don holdout %7.1f"
          % (ma, len(von), len(don), len(moi), moc_ho))
    print("     THAT  %2d/%d cap dau bang train hon he don o holdout" % (n_that, N_CAP))
    print("     GIA   trung vi %2d/%d · 95%% %2d/%d   -> p = %.4f"
          % (dem_gia_sx[N_BOOT // 2], N_CAP, dem_gia_sx[int(.95 * N_BOOT)], N_CAP, p))
    print("     MOI cap bat ky hon he don: %.1f%%  <- cang gan 100%% thi phep so "
          "'cap vs he don' cang vo nghia" % (100 * ty_le_moi_cap))
    print("     PHAN QUYET: %s"
          % ("DAT - xep hang train co thong tin" if p <= 0.05
             else "KHONG DAT - cap ngau nhien cung lam duoc the"))
    return {"symbol": ma, "cat": cat, "so_chan": len(von), "top": len(don),
            "so_cap": len(moi), "moc_he_don_holdout": round(moc_ho, 2),
            "that_giu_hang": n_that, "n_cap": N_CAP,
            "gia_trung_vi": dem_gia_sx[N_BOOT // 2],
            "gia_95": dem_gia_sx[int(.95 * N_BOOT)],
            "p": round(p, 4),
            "ty_le_moi_cap_hon_he_don": round(ty_le_moi_cap, 4),
            "phan_quyet": "DAT" if p <= 0.05 else "KHONG DAT"}


def main(argv: list[str]) -> int:
    if argv:
        ds = [(argv[0], argv[1] if len(argv) > 1 else "2021.06.01")]
    else:
        ds = [(f.stem.replace("DEM_VON_", ""), "2021.06.01")
              for f in sorted(BC.glob("DEM_VON_*.json"))]
    print("PLACEBO GHEP - null la CAP NGAU NHIEN tu cung kho chan")
    print("=" * 78)
    ket = []
    for ma, cat in ds:
        r = mot_ma(ma, cat)
        if r:
            ket.append(r)
            (BC / ("PLACEBO_GHEP_%s.json" % ma)).write_text(
                json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print("=" * 78)
    print("%d/%d ma co xep hang train MANG THONG TIN"
          % (sum(1 for r in ket if r["phan_quyet"] == "DAT"), len(ket)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
