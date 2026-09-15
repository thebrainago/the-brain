# -*- coding: utf-8 -*-
"""_audcad_gom_cum.py - 16 he song sot la BAO NHIEU phat hien doc lap?

`16/40 song so voi nen 5,5%` cho p = 1,3e-10 NEU chung doc lap. Chung gan nhu
chac chan khong: phan lon deu la "RSI qua ban -> mua" viet bang nhung cai ten
khac nhau. Neu ca 16 tuong quan hoan toan thi day chi la **MOT** phat hien duoc
lap lai 16 lan, va p that la p cua mot phep thu.

Nen buoc nay bat buoc truoc khi noi con so "16": do tuong quan chuoi VI THE
tung cap, gom cum, roi dem SO CUM.

Tuong quan chuoi vi the (khong phai chuoi lai) vi do la cai quyet dinh hai he
co cung phoi nhiem hay khong - va no khong bi nhieu bien do lam loang.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
_KHUNG = (sys.argv[sys.argv.index("--khung")+1] if "--khung" in sys.argv else "H4")
_MA = (sys.argv[sys.argv.index("--ma")+1] if "--ma" in sys.argv else "AUDCAD")

#: Tren nguong nay coi la CUNG mot phat hien.
NGUONG_CUM = 0.7


def main() -> int:
    from nhan import du_lieu as DL
    from nhan import ngu_phap as NP

    d = json.loads((LAB / "reports" / ("CHON_XAC_NHAN_%s_%s.json" % (_MA,_KHUNG)))
                   .read_text(encoding="utf-8"))
    ten = [x["ten"] for x in d["song"]]
    print("=" * 74)
    print("16 HE SONG SOT LA BAO NHIEU PHAT HIEN DOC LAP?")
    print("=" * 74)
    kho = {c.get("ten"): c for c in NP.doc_kho()}
    df = DL.nap(_MA, _KHUNG, tu="2021-03-19", den="2026-07-29")
    v = {}
    for t in ten:
        c = kho.get(t)
        if c is None:
            continue
        try:
            v[t] = np.asarray(NP.sinh_tu_spec(c, df), float)
        except Exception:
            continue
    ten = [t for t in ten if t in v]
    print("do duoc chuoi vi the cho %d/%d he\n" % (len(ten), len(d["song"])))

    n = len(ten)
    r = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = v[ten[i]], v[ten[j]]
            ok = np.isfinite(a) & np.isfinite(b)
            if ok.sum() < 50 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
                r[i, j] = r[j, i] = 0.0
                continue
            r[i, j] = r[j, i] = float(np.corrcoef(a[ok], b[ok])[0, 1])

    # Gom cum: noi hai he neu |r| >= nguong (lien thong).
    cha = list(range(n))

    def tim(x):
        while cha[x] != x:
            cha[x] = cha[cha[x]]
            x = cha[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if abs(r[i, j]) >= NGUONG_CUM:
                a, b = tim(i), tim(j)
                if a != b:
                    cha[a] = b
    cum: dict = {}
    for i in range(n):
        cum.setdefault(tim(i), []).append(ten[i])

    print("Nguong gom cum |r| >= %.2f  ->  **%d cum** tren %d he\n"
          % (NGUONG_CUM, len(cum), n))
    for i, (_, cac) in enumerate(sorted(cum.items(),
                                        key=lambda x: -len(x[1])), 1):
        print("  CUM %d (%d he): %s" % (i, len(cac), ", ".join(c[:34] for c in cac[:4])))
        if len(cac) > 4:
            print("          ... va %d he nua" % (len(cac) - 4))

    print()
    print("Tuong quan TRUNG VI giua cac cum (dai dien = he dau moi cum):")
    dai = [cac[0] for _, cac in sorted(cum.items(), key=lambda x: -len(x[1]))]
    idx = {t: i for i, t in enumerate(ten)}
    if len(dai) > 1:
        rr = [abs(r[idx[dai[i]], idx[dai[j]]])
              for i in range(len(dai)) for j in range(i + 1, len(dai))]
        print("   |r| giua cac dai dien: trung vi %.3f, cao nhat %.3f"
              % (float(np.median(rr)), float(np.max(rr))))

    from math import comb
    p_nen = d["ty_le_nen"]
    k = len(cum)
    duoi = sum(comb(40, i) * p_nen ** i * (1 - p_nen) ** (40 - i)
               for i in range(k, 41))
    print()
    print("-" * 74)
    print("DOC DUNG:")
    print("  neu dem 16 he  -> p = 1,3e-10  (GIA DINH doc lap - SAI)")
    print("  neu dem %d cum -> p = %.3g  <- con so dung hon" % (k, duoi))
    print("  (van la chan duoi: cac cum chua chac doc lap hoan toan)")

    ra = LAB / "reports" / ("CUM_%s_%s.json" % (_MA,_KHUNG))
    ra.write_text(json.dumps(
        {"so_he": n, "so_cum": len(cum), "nguong": NGUONG_CUM,
         "p_theo_cum": duoi,
         "cum": [{"dai_dien": cac[0], "he": cac}
                 for _, cac in sorted(cum.items(), key=lambda x: -len(x[1]))]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> %s" % ra.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
