# -*- coding: utf-8 -*-
"""_ghep_da_tai_san.py - GHEP CHAN TU CAC TAI SAN KHAC NHAU.

Do 07/09: quy trinh ghep song ngoai mau tren D1 (39/45 cap giu hang) nhung
**that bai tren H4** (5/15). Nguyen nhan do duoc: chan H4 tuong quan voi nhau
cao hon co he thong - cap `r > 0,5` gap doi D1, cap `r < 0` it hon 36%
[[ghep-khong-chuyen-sang-h4]]. **Khong phai quy trinh sai, ma la H4 khong du
hang am tuong quan de ghep.**

Suy ra: nguon chan am tuong quan chua khai thac khong nam o khung khac ma o
**TAI SAN khac**. Bai nay do dieu do.

## VI SAO KHONG CAN CHAY TESTER

Duong von tung chan tren tung tai san **da do bang tester** roi va nam trong
`reports/DEM_VON_<MA>.json` (US100 84 chan · US30 77 · US500 58). O day chi
gan theo moc thoi gian roi cong lai.

Phep xap xi duy nhat: **bo qua ky quy chung**. Hai chan tren hai tai san khac
nhau van chiu chi phi cua chinh tai san minh (tester da tinh), chi co ky quy la
cong don - va o muc lot 0,10 tren von 10.000 thi ky quy khong rang buoc (do
07/09: 0,1 lot US100Cash = 2,96 USD ky quy). Neu mot cap nao qua duoc bai nay
thi moi dua vao EA da tai san that de xac nhan.

## HAI CHO PHAI LAM DUNG

1. **CAN BANG RUI RO truoc khi cong.** Hop dong US30 lon hon US500 nhieu lan nen
   cong thang USD la de mot tai san nuot ca danh muc. O day moi chan duoc chia
   cho **sut giam cua chinh no TREN TRAIN** -> moi chan gop dung mot don vi rui
   ro. He so nay quyet dinh **chi tu train**, khong nhin holdout.
2. **Cham tren TRAIN, doc o HOLDOUT.** Bang cham tren toan cua so la in-sample
   doi voi chinh phep chon chan [[ghep-song-o-holdout-he-don-thi-khong]].

Chay: python _ghep_da_tai_san.py
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _dem_ghep as DG      # noqa: E402
import _ghep_he as GH       # noqa: E402

LAB = Path(__file__).resolve().parent
BC = LAB / "reports"
MA = ["US100Cash", "US500Cash", "US30Cash"]
CAT = "2021.06.01"
TOP = 40          # so chan mang di ghep (chon tren TRAIN)


def nap() -> tuple[list, dict]:
    """Tra (moc thoi gian chung, {'MA:ten': chuoi lai luy ke da gan})."""
    goc = None
    tho = {}
    for ma in MA:
        f = BC / ("DEM_VON_%s.json" % ma)
        if not f.exists():
            print("thieu %s" % f.name)
            continue
        d = json.load(open(f, encoding="utf-8"))
        tg, von = d["tg"], d["von"]
        tho[ma] = (tg, von)
        goc = set(t[:10] for t in tg) if goc is None else goc & set(t[:10] for t in tg)
    ngay = sorted(goc or [])
    ra = {}
    for ma, (tg, von) in tho.items():
        # Gan theo NGAY: moi tai san co lich phien rieng, cong theo chi so nen
        # la cong lech ngay - loi im lang vi hai chuoi deu dai 2624.
        vt = {}
        for j, t in enumerate(tg):
            vt[t[:10]] = j
        for ten, v in von.items():
            ra["%s:%s" % (ma, ten)] = [v[vt[n]] for n in ngay if n in vt]
    return ngay, ra


def _dd(v: list[float]) -> float:
    return GH._sut_giam(v)


def main() -> int:
    ngay, tat = nap()
    if not tat:
        return 1
    i = next((k for k, n in enumerate(ngay) if n >= CAT.replace(".", ".")), 0)
    i = next((k for k, n in enumerate(ngay) if n.replace(".", "-") >= "2021-06-01"),
             len(ngay) // 2)
    print("%d chan tu %d tai san | %d ngay chung | cat %s (ngay %d)"
          % (len(tat), len(MA), len(ngay), ngay[i], i))

    def doan(a, b):
        return {t: [v[j] - v[a] for j in range(a, b)] for t, v in tat.items()}

    tr, ho = doan(0, i), doan(i, len(ngay))

    # khu trung theo duong von TRAIN (trong VA giua cac tai san)
    thay, giu = {}, []
    for t in sorted(tr):
        k = tuple(round(x, 2) for x in tr[t])
        if k in thay:
            continue
        thay[k] = t
        giu.append(t)
    print("khu trung: %d -> %d chan" % (len(tat), len(giu)))

    dd_tr = {t: _dd(tr[t]) for t in giu}
    duong = [t for t in giu if tr[t][-1] > 0 and dd_tr[t] > 0]
    #: CAN BANG RUI RO: chia cho sut giam TREN TRAIN. He so quyet dinh chi tu
    #: train - dung he so cua toan cua so la nhin truoc.
    hs = {t: 1.0 / dd_tr[t] for t in duong}
    don = sorted(duong, key=lambda t: -tr[t][-1] / dd_tr[t])[:TOP]
    print("chan duong tren TRAIN: %d | lay top %d" % (len(duong), len(don)))
    from collections import Counter
    print("   phan bo theo tai san:",
          dict(Counter(t.split(":")[0] for t in don)))

    dv = {t: [tr[t][j] - tr[t][j - 1] for j in range(1, len(tr[t]))] for t in don}

    def cham(d, bo):
        v = [sum(d[x][k] * hs[x] for x in bo) for k in range(len(d[bo[0]]))]
        dd = _dd(v)
        return (v[-1] / dd) if dd > 0 else 0.0

    cap = []
    for a in range(len(don)):
        for b in range(a + 1, len(don)):
            x, y = don[a], don[b]
            cap.append({"bo": [x, y], "cheo": x.split(":")[0] != y.split(":")[0],
                        "r": round(GH._tuong_quan(dv[x], dv[y]), 3),
                        "tr": round(cham(tr, [x, y]), 1)})
    for c in cap:
        c["ho"] = round(cham(ho, c["bo"]), 1)

    cung = [c for c in cap if not c["cheo"]]
    cheo = [c for c in cap if c["cheo"]]
    print("\n--- PHAN BO TUONG QUAN (tren TRAIN) ---")
    print("%-16s %6s %11s %10s %10s" % ("lop cap", "so cap", "r trung vi",
                                        "% r>0,5", "% r<0"))
    for ten, ds in (("CUNG tai san", cung), ("KHAC tai san", cheo)):
        if not ds:
            continue
        rs = [c["r"] for c in ds]
        print("%-16s %6d %+11.3f %9.1f%% %9.1f%%"
              % (ten, len(ds), st.median(rs),
                 100 * sum(1 for r in rs if r > 0.5) / len(rs),
                 100 * sum(1 for r in rs if r < 0) / len(rs)))

    moc_ho = cham(ho, [don[0]])
    print("\nhe don dau bang TRAIN: %s" % don[0])
    print("   train %.1f -> holdout %.1f" % (tr[don[0]][-1] / dd_tr[don[0]],
                                             moc_ho))
    print("\n--- TOP 15 CAP CUA TUNG LOP: cham TRAIN, doc HOLDOUT ---")
    ket = {}
    for ten, ds in (("cung", cung), ("cheo", cheo)):
        ds = sorted(ds, key=lambda c: -c["tr"])[:15]
        if not ds:
            continue
        giu_hang = sum(1 for c in ds if c["ho"] > moc_ho)
        tv = sorted(c["ho"] for c in ds)[len(ds) // 2]
        ket[ten] = {"giu_hang": giu_hang, "so": len(ds), "trung_vi_ho": tv,
                    "top": ds[:8]}
        print("\n[%s tai san]  %d/%d cap hon he don o holdout | trung vi "
              "holdout %.1f (he don %.1f)"
              % (ten.upper(), giu_hang, len(ds), tv, moc_ho))
        print("%-34s %-34s %6s %8s %8s" % ("chan A", "chan B", "r", "train",
                                           "holdout"))
        for c in ds[:8]:
            print("%-34s %-34s %+6.2f %8.1f %8.1f"
                  % (c["bo"][0][:34], c["bo"][1][:34], c["r"], c["tr"], c["ho"]))

    DG.ghi("GHEP_DA_TAI_SAN.json",
           {"tai_san": MA, "so_chan": len(tat), "sau_khu_trung": len(giu),
            "don_train_dau_bang": don[0], "don_holdout": round(moc_ho, 1),
            "ket": ket, "cap": sorted(cap, key=lambda c: -c["tr"])[:120]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
