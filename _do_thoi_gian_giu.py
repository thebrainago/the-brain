# -*- coding: utf-8 -*-
"""_do_thoi_gian_giu.py - CHAN NAO GIU LENH LAU? Quan tri chi song o do.

Do 07/09: tren cap `mean_reversion_z5` + `quantora_ma_dashboard_sell`, quan tri
vi the gan nhu **vo hieu** - 504 cau hinh chi co 72 cai lam doi duoc ket qua, va
tat ca deu la dat hue 0,05 x ATR. Ly do khong phai co che quan tri kem ma la
**hai chan giu lenh qua ngan**: quantora giu dung 1 nen D1, z5 thoat khi z-score
hoi. Mot lop phu can lai 0,5 x ATR moi kich hoat thi khong bao gio toi luot.

=> Viec dung khong phai ha nguong nho nua, ma la **chon chan giu lenh DAI** roi
moi phu trailing / dat hue len.

## DO BANG DU LIEU DA CO, KHONG CHAY LAI TESTER

`_bo_ba.py` da cho EA ghi duong von + co `mo` (dang mo hay khong) cua **tung
chan theo tung nen** ra `Common/Files/LO<n>_<MA>.csv`. Tu do rut duoc:

    phoi nhiem   = so nen dang mo / tong so nen
    so cum       = so lan chuyen 0 -> 1        (= so LENH)
    giu trung binh = so nen dang mo / so cum   (= so NEN moi lenh)

Khong ton mot lan boot nao.

## HAI CHO DE SAI

- **Thu tu cot phai dung thu tu `dat` cua `sinh_ea_ghep`**: `[__mua_giu__] + lo`.
  Lay nham thu tu thi bang van "hop ly" - do la kieu sai im lang te nhat.
- **So cum khong phai so lenh cua tester** khi co nhoi lenh: mot cum co the co
  nhieu vi the. O day EA chay khong nhoi nen hai so trung nhau.

Chay: python _do_thoi_gian_giu.py [SYMBOL]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bo_ba as BB          # noqa: E402
import _dem_ghep as DG       # noqa: E402
import _ghep_he as GH        # noqa: E402

LAB = Path(__file__).resolve().parent
BC = LAB / "reports"
MA = sys.argv[1] if len(sys.argv) > 1 else "US100Cash"


def doc_lo(chan: list[dict]) -> dict:
    """Tra {ten: (von, mo)} bang cach ghep lai tung lo theo dung thu tu slot."""
    ra = {}
    for lo in range((len(chan) + DG.SLOT_MOI_LAN - 1) // DG.SLOT_MOI_LAN):
        f = GH.CHUNG / ("LO%d_%s.csv" % (lo, MA))
        if not f.exists():
            print("thieu %s" % f.name)
            continue
        tg, von, mo, gia = GH.doc_csv(f)
        phan = chan[lo * DG.SLOT_MOI_LAN:(lo + 1) * DG.SLOT_MOI_LAN]
        # slot 0 la __mua_giu__, slot i+1 ung voi phan[i]
        for i, c in enumerate(phan):
            if i + 1 < len(von):
                ra[c["ten"]] = (von[i + 1], mo[i + 1])
    return ra


def main() -> int:
    chan = BB.lay_chan()
    d = doc_lo(chan)
    if not d:
        print("chua co CSV duong von - chay _bo_ba.py truoc")
        return 1
    hang = []
    for t, (von, mo) in d.items():
        n = len(mo)
        cum = sum(1 for j in range(n) if mo[j] and (j == 0 or not mo[j - 1]))
        mo_tong = sum(mo)
        if cum == 0 or mo_tong == 0:
            continue
        dd = GH._sut_giam(von)
        hang.append({"ten": t, "lai": round(von[-1], 2), "dd": round(dd, 3),
                     "lenh": cum, "phoi_nhiem": round(mo_tong / n * 100, 2),
                     "giu_tb": round(mo_tong / cum, 2),
                     "loi_tren_dd": round(von[-1] / dd, 1) if dd > 0 else 0.0})
    duong = [x for x in hang if x["lai"] > 0]
    duong.sort(key=lambda x: -x["giu_tb"])
    print("%s: %d chan, %d chan duong\n" % (MA, len(hang), len(duong)))
    print("--- 15 chan DUONG giu lenh LAU nhat ---")
    print("%-46s %7s %7s %9s %9s %8s"
          % ("chan", "giu_tb", "lenh", "phoinhiem", "lai", "lai/DD"))
    for x in duong[:15]:
        print("%-46s %7.2f %7d %8.2f%% %9.2f %8.1f"
              % (x["ten"][:46], x["giu_tb"], x["lenh"], x["phoi_nhiem"],
                 x["lai"], x["loi_tren_dd"]))
    print("\n--- 5 chan duong giu NGAN nhat (de doi chieu) ---")
    for x in duong[-5:]:
        print("%-46s %7.2f %7d %8.2f%% %9.2f %8.1f"
              % (x["ten"][:46], x["giu_tb"], x["lenh"], x["phoi_nhiem"],
                 x["lai"], x["loi_tren_dd"]))

    #: Cap de thu quan tri: hai chan GIU LAU nhat ma van co lai/DD kha, va
    #: **tuong quan thap** - neu khong thi ta chi do quan tri tren mot he nhan doi.
    dv = {x["ten"]: [d[x["ten"]][0][j] - d[x["ten"]][0][j - 1]
                     for j in range(1, len(d[x["ten"]][0]))] for x in duong}
    lau = [x for x in duong if x["giu_tb"] >= 5 and x["loi_tren_dd"] > 50][:12]
    cap = []
    for i in range(len(lau)):
        for j in range(i + 1, len(lau)):
            a, b = lau[i]["ten"], lau[j]["ten"]
            r = GH._tuong_quan(dv[a], dv[b])
            t = [d[a][0][k] + d[b][0][k] for k in range(len(d[a][0]))]
            dd = GH._sut_giam(t)
            cap.append({"a": a, "b": b, "r": round(r, 3),
                        "giu_a": lau[i]["giu_tb"], "giu_b": lau[j]["giu_tb"],
                        "lai": round(t[-1], 2), "dd": round(dd, 3),
                        "loi_tren_dd": round(t[-1] / dd, 1) if dd > 0 else 0})
    cap.sort(key=lambda c: -c["loi_tren_dd"])
    print("\n--- CAP GIU LAU tot nhat (ca hai chan giu >= 5 nen) ---")
    print("%-28s %-28s %6s %6s %6s %9s %8s"
          % ("chan A", "chan B", "r", "giuA", "giuB", "lai", "lai/DD"))
    for c in cap[:8]:
        print("%-28s %-28s %+6.2f %6.1f %6.1f %9.2f %8.1f"
              % (c["a"][:28], c["b"][:28], c["r"], c["giu_a"], c["giu_b"],
                 c["lai"], c["loi_tren_dd"]))
    DG.ghi("THOI_GIAN_GIU_%s.json" % MA, {"chan": hang, "cap_giu_lau": cap[:40]})
    if cap:
        print("\n=> thu quan tri tren: %s + %s" % (cap[0]["a"], cap[0]["b"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
