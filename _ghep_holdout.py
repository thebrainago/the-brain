# -*- coding: utf-8 -*-
"""_ghep_holdout.py - CHAM CAP TREN TRAIN, DO TREN HOLDOUT. Khong chay tester.

## LO HONG PHAI BIT

Bang xep hang cap cua 07/09 cham tren **toan cua so** 2016-2026, trong khi chinh
cac chan cung duoc chon la "duong o ca train lan holdout" cua cua so do. Tuc bang
cap la **in-sample doi voi phep chon chan**. Voi 30 chan thi co 435 cap - du de
mot cap dep noi len chi vi may.

Bai nay tra loi cau duy nhat dang tra loi: **xep hang cap tren nua DAU roi doc
ket qua o nua SAU**. Neu thu hang khong giu duoc thi "ghep hon he don 1,86 lan"
la mot cuc tri cua giai doan, khong phai mot tinh chat.

Khong ton mot lan boot nao: duong von tung chan da nam trong
`reports/DEM_VON_<MA>.json` (do bang tester voi `InpGhi=1`), o day chi cat theo
moc thoi gian roi cong lai.

## HAI DIEU PHAI GIU DUNG

1. **Cat theo MOC THOI GIAN, khong theo chi so nen.** Bar khong deu.
2. **Lai luy ke phai tru moc dau doan**, neu khong nua sau se mang theo ca lai
   cua nua dau va moi sut giam deu bi lam nho di.

Chay: python _ghep_holdout.py [SYMBOL]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _ghep_he as GH                  # noqa: E402

LAB = Path(__file__).resolve().parent
BC = LAB / "reports"
MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"
CAT = sys.argv[2] if len(sys.argv) > 2 else "2021.06.01"
TOP = 30


def doan(von: dict, tg: list, tu_i: int, den_i: int) -> dict:
    """Cat mot doan va DAT LAI moc 0 o dau doan."""
    return {t: [v[j] - v[tu_i] for j in range(tu_i, den_i)]
            for t, v in von.items()}


def cham(d: dict, bo: list) -> tuple:
    t = [sum(d[x][k] for x in bo) for k in range(len(d[bo[0]]))]
    dd = GH._sut_giam(t)
    return t[-1], dd, (t[-1] / dd) if dd > 0 else 0.0


def main() -> int:
    f = BC / ("DEM_VON_%s.json" % MA)
    if not f.exists():
        print("chua co %s - chay _bo_ba.py truoc" % f)
        return 1
    d = json.load(open(f, encoding="utf-8"))
    tg, von = d["tg"], d["von"]
    i = next((k for k, x in enumerate(tg) if x[:10] >= CAT), len(tg) // 2)
    print("%d chan | %d nen | cat tai %s (nen %d): train %s..%s  holdout %s..%s"
          % (len(von), len(tg), CAT, i, tg[0][:10], tg[i - 1][:10], tg[i][:10],
             tg[-1][:10]))

    tr = doan(von, tg, 0, i)
    ho = doan(von, tg, i, len(tg))

    # Khu trung theo duong von TREN TRAIN (hai chan cung chuoi lenh thi ghep chi
    # la nhan doi lot, va no se dan dau bang mot cach gia).
    thay, giu = {}, []
    for t in sorted(tr):
        k = tuple(round(x, 2) for x in tr[t])
        if k in thay:
            continue
        thay[k] = t
        giu.append(t)
    print("khu trung tren train: %d -> %d chan" % (len(von), len(giu)))

    #: CHI dung so lieu TRAIN de chon. Chan nao am o train thi loai - khong duoc
    #: nhin holdout de quyet dinh bat cu dieu gi.
    duong = [t for t in giu if tr[t][-1] > 0]
    dd_tr = {t: GH._sut_giam(tr[t]) for t in duong}
    don = sorted((t for t in duong if dd_tr[t] > 0),
                 key=lambda t: -tr[t][-1] / dd_tr[t])[:TOP]
    print("chan duong tren TRAIN: %d, lay top %d" % (len(duong), len(don)))

    cap = []
    for a in range(len(don)):
        for b in range(a + 1, len(don)):
            l, dd, s = cham(tr, [don[a], don[b]])
            cap.append({"bo": [don[a], don[b]], "tr": round(s, 1)})
    cap.sort(key=lambda c: -c["tr"])

    for c in cap:
        l, dd, s = cham(ho, c["bo"])
        c["ho"] = round(s, 1)
        c["ho_lai"] = round(l, 2)
        c["ho_dd"] = round(dd, 3)
    don_ho = {t: cham(ho, [t])[2] for t in don}

    tot_don_tr = tr[don[0]][-1] / dd_tr[don[0]]
    # Moc so sanh o HOLDOUT phai la he don duoc chon tren TRAIN, khong phai he
    # don tot nhat cua holdout - nguoc lai la lai nhin truoc.
    moc_ho = don_ho[don[0]]

    print("\n--- 15 CAP dau bang cua TRAIN, doc ket qua o HOLDOUT ---")
    print("%-26s %-26s %9s %9s" % ("chan A", "chan B", "train", "holdout"))
    for c in cap[:15]:
        print("%-26s %-26s %9.1f %9.1f"
              % (c["bo"][0][:26], c["bo"][1][:26], c["tr"], c["ho"]))

    n = 15
    giu_hang = sum(1 for c in cap[:n] if c["ho"] > moc_ho)
    tv_ho = sorted(c["ho"] for c in cap[:n])[n // 2]
    print("\nhe don dau bang TRAIN : %s" % don[0][:44])
    print("   train %.1f  ->  holdout %.1f" % (tot_don_tr, moc_ho))
    print("cap dau bang TRAIN    : %s + %s"
          % (cap[0]["bo"][0][:24], cap[0]["bo"][1][:24]))
    print("   train %.1f  ->  holdout %.1f" % (cap[0]["tr"], cap[0]["ho"]))
    print("\n%d/%d cap dau bang train VAN hon he don do o holdout | trung vi "
          "holdout cua 15 cap dau: %.1f" % (giu_hang, n, tv_ho))

    ra = {"symbol": MA, "cat": CAT, "so_chan": len(von), "sau_khu_trung": len(giu),
          "he_don_train_dau_bang": don[0], "don_train": round(tot_don_tr, 1),
          "don_holdout": round(moc_ho, 1),
          "cap_giu_hang": giu_hang, "trung_vi_holdout_15_cap": tv_ho,
          "cap": cap[:60]}
    (BC / ("GHEP_HOLDOUT_%s.json" % MA)).write_text(
        json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
    print("-> reports/GHEP_HOLDOUT_%s.json" % MA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
