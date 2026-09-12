# -*- coding: utf-8 -*-
"""MOT LENH de vao phien: in ban ban giao + trang thai SONG cua he.

Chay:  b vao        (hoac: python BAN_GIAO.py, hoac bam doi BAN_GIAO.cmd)

Vi sao co file nay: moi phien truoc deu mat 10-20 phut dau chi de tim thu muc,
mo dung file ban giao, roi hoi lai CSDL xem hang doi con gi. Ba viec do la tat
dinh - mot lenh lam duoc het.

Tu 30/08 no doc so qua `nhip_song.py` — cung mot phep dem voi `KET_PHIEN.py`,
nen cot "doi" so voi moc chot hom qua la so THAT chu khong phai uoc luong.

Nguyen tac: **chi DOC, khong sua gi**, va phai chay xong duoi 5 giay. Khong
import pandas, khong goi `kho()`, khong chay test.
"""
from __future__ import annotations

import time
from pathlib import Path

import nhip_song as NS

LAB = NS.LAB
GOC = NS.GOC

NHAN = {
    "ham_test": "ham test (lab)", "test_ds": "file test (ds/)",
    "bang_gia": "bang gia .parquet", "fdr": "dong so FDR",
    "ung_vien": "ung vien xep hang", "tai_lieu": "ban doc da thu",
    "co_che": "co che trong thu vien", "van_de_mo": "van de con mo",
    "van_de_nang": "  muc NANG", "viec_cho_tong": "viec dang CHO",
}


def main() -> int:
    t0 = time.time()
    print("=" * 78)
    print("THE BRAIN — VAO PHIEN")
    print("=" * 78)
    print(f"lab        : {LAB}")
    print(f"ds (kho DS): {GOC / 'ds'}" + ("" if (GOC / "ds").exists() else "  [KHONG THAY]"))
    bao_cao = sorted(GOC.glob("BAO_CAO_*.md"))
    if bao_cao:
        print(f"bao cao gan nhat : {bao_cao[-1].name}")

    t = NS.doc()
    cu = NS.anh_cu()
    d = NS.chenh(t, cu)

    print("\n--- TRANG THAI SONG ---" +
          (f"  (doi so voi moc {cu.get('ngay')})" if cu else "  (chua co moc de so)"))
    for k, nhan in NHAN.items():
        v = t.get(k)
        if v is None:
            continue
        print(f"  {nhan:22s}: {v}" + (f"   ({d[k]:+d})" if k in d else ""))
    print(f"  {'viec CHO theo loai':22s}: " +
          (", ".join(f"{a}={b}" for a, b in t["viec_cho"].items()) or "khong con"))
    print(f"  {'co DUNG_LAI':22s}: " +
          ("CO (he dang nam im)" if t["dung_lai"] else "KHONG (he duoc phep chay)"))

    if NS.co_git():
        doi = [l for l in NS.git(["status", "--short"]).splitlines() if l.strip()]
        print(f"  {'git':22s}: {NS.git(['log', '--oneline', '-1'])}")
        if doi:
            print(f"  {'':22s}  {len(doi)} file dang doi CHUA commit")
    else:
        print(f"  {'git':22s}: CHUA CO — khong co duong lui khi sua hong")

    # EVO: mot dong suc khoe + dung cai dang XAU. Doc tu bao cao DA CO, khong
    # chay lai phep do nao - vao phien phai duoi 3 giay.
    #
    # Vi sao de o day: hom 12/09/2026 toi ghi lai mot bai hoc rang bo do "rau
    # nen hong" DA dem duoc 154 bar hong cua GBPZAR tu truoc ma khong ai doc -
    # roi suyt lap lai y het voi EVO. Mot bo giam sat khong nam tren duong vao
    # phien thi bang khong co.
    try:
        import json as _js
        _ev = LAB / "reports" / "EVO_SUC_KHOE.md"
        _js_ev = LAB / "reports" / "EVO_SUC_KHOE.json"
        if _ev.exists():
            _d = _ev.read_text(encoding="utf-8").splitlines()
            _tom = next((x for x in _d if x.startswith("TOT ")), "")
            print(f"\n--- EVO (suc khoe module) ---   {_tom}")
            for _l in _d:
                if _l.startswith("### `"):
                    print("  XAU: " + _l[5:].replace("` — ", " — ").rstrip())
            print("  chi tiet: b evo    (tuoi bao cao: %.1f gio)"
                  % ((time.time() - _ev.stat().st_mtime) / 3600))
        else:
            print("\n--- EVO --- chua co bao cao. Chay: b evo")
    except Exception as _e:
        print(f"\n--- EVO --- khong doc duoc bao cao: {_e}")

    f = LAB / "TIEP_TUC_MAI.md"
    print("\n" + "=" * 78)
    print(f"BAN GIAO — {f.name}")
    print("=" * 78)
    print(f.read_text(encoding="utf-8") if f.exists()
          else "(KHONG TIM THAY TIEP_TUC_MAI.md)")
    print(f"\n[doc xong trong {time.time() - t0:.1f}s]   Chot phien: b ket \"tom tat\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
