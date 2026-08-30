# -*- coding: utf-8 -*-
"""MOT LENH de vao phien: in ban ban giao + trang thai SONG cua he.

Chay:  python "Downloads/Research SP500/lab/BAN_GIAO.py"
Hoac:  bam doi vao BAN_GIAO.cmd cung thu muc.

Vi sao co file nay: moi phien truoc deu mat 10-20 phut dau chi de tim thu muc,
mo dung file ban giao, roi hoi lai CSDL xem hang doi con gi. Ba viec do la tat
dinh - mot lenh lam duoc het.

Nguyen tac: **chi DOC, khong sua gi**, va phai chay xong duoi 5 giay. Khong
import pandas, khong goi `kho()`, khong chay test.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
GOC = LAB.parent


def _dem(db: Path, cau: str, mac_dinh="?"):
    if not db.exists():
        return mac_dinh
    try:
        cn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3)
        try:
            return cn.execute(cau).fetchone()[0]
        finally:
            cn.close()
    except Exception as e:
        return f"loi: {type(e).__name__}"


def _bang(db: Path, cau: str) -> list:
    if not db.exists():
        return []
    try:
        cn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3)
        try:
            return list(cn.execute(cau))
        finally:
            cn.close()
    except Exception:
        return []


def main() -> int:
    t0 = time.time()
    nao, thu_vien = LAB / "nao.db", LAB / "thu_vien.db"

    print("=" * 78)
    print("THE BRAIN — VAO PHIEN")
    print("=" * 78)
    print(f"lab        : {LAB}")
    bao_cao = sorted(GOC.glob("BAO_CAO_*.md"))
    if bao_cao:
        print(f"bao cao gan nhat : {bao_cao[-1].name}")
    print(f"DUNG_LAI   : {'CO (he dang nam im)' if (LAB / 'DUNG_LAI').exists() else 'KHONG'}")

    print("\n--- TRANG THAI SONG ---")
    so_test = sum(1 for f in LAB.glob("test_*.py")
                  for l in f.read_text(encoding="utf-8", errors="ignore").splitlines()
                  if l.strip().startswith("def test_"))
    print(f"  file test        : {len(list(LAB.glob('test_*.py')))}  ({so_test} ham test)")
    print(f"  bang gia (parquet): {len(list((GOC / 'data').glob('*.parquet')))}")
    print(f"  fdr (so quyet dinh): {_dem(nao, 'SELECT COUNT(*) FROM fdr')}")
    print(f"  ung vien xep hang : {_dem(nao, 'SELECT COUNT(*) FROM candidate_queue')}")
    print(f"  ban doc (tai_lieu): {_dem(nao, 'SELECT COUNT(*) FROM tai_lieu')}")
    print(f"  co che (thu_vien) : {_dem(thu_vien, 'SELECT COUNT(*) FROM co_che')}")
    viec = _bang(nao, "SELECT loai, trang_thai, COUNT(*) FROM viec "
                      "WHERE trang_thai='CHO' GROUP BY 1,2 ORDER BY 3 DESC")
    if viec:
        print("  viec dang CHO    : " + ", ".join(f"{a}={c}" for a, _b, c in viec))
    else:
        print("  viec dang CHO    : khong con")

    f = LAB / "TIEP_TUC_MAI.md"
    print("\n" + "=" * 78)
    print(f"BAN GIAO — {f.name}")
    print("=" * 78)
    print(f.read_text(encoding="utf-8") if f.exists()
          else "(KHONG TIM THAY TIEP_TUC_MAI.md)")
    print(f"\n[doc xong trong {time.time() - t0:.1f}s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
