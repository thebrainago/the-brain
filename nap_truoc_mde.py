# -*- coding: utf-8 -*-
"""Nap truoc BANG MDE cho ca be mat, thay vi do lazy giua vong quet.

VI SAO. MDE la thuoc tinh cua CAP `(tai san, khung)` - no phu thuoc so bar va
mo hinh chi phi, KHONG phu thuoc ung vien dang xet. Nhung `sang_loc.v3_phan_chung`
goi `do_luc.du_luc_de_kiem` cho tung ung vien, nen mot vong quet 15 co che x
122 tai san co the keo theo hang tram phep do MDE giong het nhau.

Do that 30/08/2026 sau khi sua hai cho dem (`kho()` + `chi_phi._doc_luu`):
**3-4 giay moi cap**, khong phai ~2 phut nhu uoc luong ngay 24/08. Nap truoc
ca 122 cap D1 het khoang 5 phut, MOT lan.

Chay:  b mde-nap            (mac dinh D1)
       b mde-nap H4         khung khac
       b mde-nap D1 --lam-moi   do lai ca nhung cap da co
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nhan import do_luc as L      # noqa: E402
from nhan import pham_vi as PV    # noqa: E402


def nap(khung: str = "D1", lam_moi: bool = False) -> dict:
    cac_ma = list(PV.kho_du_bar(khung))
    cache = L._doc_mde_cache()
    t0 = time.time()
    xong, bo_qua, loi = 0, 0, 0
    tom: list[dict] = []
    for i, ma in enumerate(cac_ma, 1):
        khoa = f"{ma.upper()}|{khung.upper()}"
        if not lam_moi and khoa in cache:
            bo_qua += 1
            continue
        try:
            r = L.mde_cua(ma, khung, lam_moi=lam_moi)
        except Exception as e:
            loi += 1
            print(f"  [{i:3d}/{len(cac_ma)}] {ma:14s} LOI {type(e).__name__}: {str(e)[:60]}",
                  flush=True)
            continue
        if r.get("loi"):
            loi += 1
        else:
            xong += 1
            tom.append(r)
        print(f"  [{i:3d}/{len(cac_ma)}] {ma:14s} mde={str(r.get('mde')):>7s} "
              f"bar={r.get('so_bar', 0):>6d} {r.get('che_do', '')}"
              f"{'  LOI: ' + str(r['loi'])[:50] if r.get('loi') else ''}", flush=True)

    giay = time.time() - t0
    co_so = [t for t in tom if isinstance(t.get("mde"), (int, float))]
    print("\n" + "=" * 70)
    print(f"NAP TRUOC MDE — khung {khung}: do moi {xong}, bo qua (da co) {bo_qua}, "
          f"loi {loi}, {giay:.0f}s")
    if co_so:
        co_so.sort(key=lambda t: t["mde"])
        print(f"  MDE thap nhat (de phat hien nhat):")
        for t in co_so[:8]:
            print(f"    {t['ma']:14s} {t['mde']:6.3f}  ({t['so_bar']} bar, {t.get('che_do')})")
        print(f"  MDE cao nhat (kho phat hien nhat):")
        for t in co_so[-4:]:
            print(f"    {t['ma']:14s} {t['mde']:6.3f}  ({t['so_bar']} bar, {t.get('che_do')})")
    return {"khung": khung, "do_moi": xong, "bo_qua": bo_qua, "loi": loi, "giay": giay}


if __name__ == "__main__":
    kh = next((a for a in sys.argv[1:] if not a.startswith("-")), "D1")
    raise SystemExit(0 if nap(kh, "--lam-moi" in sys.argv) else 0)
