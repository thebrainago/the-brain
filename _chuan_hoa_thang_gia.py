# -*- coding: utf-8 -*-
"""_chuan_hoa_thang_gia.py - 75 co che chet oan tren FX -> ban `k x ATR`.

    python _chuan_hoa_thang_gia.py --xem     # chi in, khong ghi kho
    python _chuan_hoa_thang_gia.py --ghi     # dua vao kho qua `them_co_che`

Vi sao: `b thang-gia` chi BAO. Bao xong thi 75 co che van nam do, chet tren moi
cap FX - ma FX lai dung la cho hai he dang song lam viec. Xem `nhan/thang_gia.py`.

VAO KHO QUA CUA CHINH. `them_co_che` chay `kiem_khai_bao`, kiem NHIN TRUOC, khu
trung theo VAN TAY DIEU KIEN va do ty le kich hoat. Mot ban chuan hoa trung dieu
kien voi co che da co thi bi tu choi o do - dung y muon.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))


def main() -> int:
    from nhan import du_lieu as DL
    from nhan import ngu_phap as NP
    from nhan import thang_gia as TG

    ghi = "--ghi" in sys.argv
    d = TG.kho_xep_loai()
    if not d:
        print("chua co config/thang_gia.json - chay `b thang-gia` truoc")
        return 1
    can = [t for t, h in d.items() if h.get("xep_loai") == "PHU_THUOC_THANG_GIA"]
    kho = {c.get("ten"): c for c in NP.doc_kho()}
    ds = TG.chuoi()
    print("%d co che PHU_THUOC_THANG_GIA, dang viet lai sang `k x ATR`\n" % len(can))

    moi, hong = [], Counter()
    for t in can:
        c = kho.get(t)
        if c is None:
            hong["khong con trong kho"] += 1
            continue
        try:
            m = TG.chuan_hoa(c, ds)
        except Exception as e:
            hong["loi: %s" % type(e).__name__] += 1
            continue
        if m is None:
            hong["khong co hang so don vi gia de doi"] += 1
            continue
        sau = TG.do_theo_thang(m, ds)
        loai = TG.xep_loai(sau)
        m["_xep_loai_sau"] = loai
        m["_ty_le_sau"] = {k: (None if v is None else round(v, 4))
                           for k, v in sau.items()}
        moi.append(m)

    cuu = [m for m in moi if m["_xep_loai_sau"] == "ON_DINH"]
    print("viet lai duoc %d; trong do %d thanh ON_DINH tren ca sau bac gia"
          % (len(moi), len(cuu)))
    for k, n in hong.most_common():
        print("   bo %3d  %s" % (n, k))
    print("\n%-44s %s" % ("co che (ban ATR)",
                          "  ".join(t.split(".")[0][:7] for t, _, _ in ds)))
    for m in cuu[:15]:
        print("%-44s %s" % (m["ten"][:44], "  ".join(
            "  .  " if m["_ty_le_sau"][t] is None else "%5.3f" % m["_ty_le_sau"][t]
            for t, _, _ in ds)))

    ra = LAB / "reports" / "CHUAN_HOA_THANG_GIA.json"
    ra.parent.mkdir(exist_ok=True)
    ra.write_text(json.dumps({"so": len(cuu), "co_che": cuu},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> %s" % ra.name)

    if not ghi:
        print("(chi XEM. Them `--ghi` de dua vao kho qua `them_co_che`)")
        return 0

    df_kiem = DL.nap("AUDCAD", "H1")
    nhan, tu_choi = 0, Counter()
    for m in cuu:
        s = {k: v for k, v in m.items() if not k.startswith("_")}
        s["_chuan_hoa_tu"] = m.get("_chuan_hoa_tu")
        k = NP.them_co_che(s, df_kiem)
        if k.get("nhan"):
            nhan += 1
        else:
            tu_choi[str((k.get("ly_do") or ["?"])[0])[:70]] += 1
    print("\nvao kho: %d nhan / %d tu choi" % (nhan, sum(tu_choi.values())))
    for ly, n in tu_choi.most_common(8):
        print("   %4d  %s" % (n, ly))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
