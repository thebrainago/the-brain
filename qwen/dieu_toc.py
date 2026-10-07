# -*- coding: utf-8 -*-
"""dieu_toc.py - DIEU TOC CHUNG cho nhieu bo chay tren MOT may (chu du an 07/10/2026: "dieu toc va phan chia cong viec de tranh de len nhau va nghen").

Van de do duoc (07/10): 9 bo chay (6 CPU + 3 MT5) moi bo mot hop thu rieng, khong biet nhau -> bat dau cung luc, moi tien trinh tu nap du lieu
vao RAM, bo nho cam ket con ~8 GB, den VANG. Cong nay la MOT cua chung cho moi bo chay tren may:

  1. CHI CHO MOT BO KHOI DONG MOI `cach_giay` (20 s): do tai nguyen CHI CHINH XAC sau khi viec truoc da nap xong du lieu, khong ba bo cung
     thay "con trong" roi cung vao (khoa nguyen tu: tao tep thu muc dung chung, cu thi lay lai).
  2. CPU: dang > `tran_cpu` % (mac dinh 90) thi cho.
  3. RAM: bo nho trong < `ram_trong_toi_thieu_gb` hoac (RAM trong + file trang trong) < `commit_toi_thieu_gb` thi cho.
Cho = `duoc_vao` tra (False, ly do); bo chay nghi roi hoi lai, KHONG bo don. Don TESTER nhan thang (slot_tester dieu tiet 4 slot rieng).
Thu muc dung chung (moi clone `cau_hop_thu_pN` deu thay): bien `THEBRAIN_DIEU_TOC_DIR`, mac dinh %PUBLIC%\\thebrain_dieu_toc (Windows) hoac tmp.
Cau hinh tuy chon `config/dieu_toc.json` {"tran_cpu":90,"ram_trong_toi_thieu_gb":4,"commit_toi_thieu_gb":8,"cach_giay":20}.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
CAU_HINH = LAB / "config" / "dieu_toc.json"
MAC_DINH = {"tran_cpu": 90.0, "ram_trong_toi_thieu_gb": 4.0, "commit_toi_thieu_gb": 8.0, "cach_giay": 20.0}
GB = 1024 ** 3


def thu_muc() -> Path:
    d = os.environ.get("THEBRAIN_DIEU_TOC_DIR")
    if not d:
        goc = os.environ.get("PUBLIC") or tempfile.gettempdir()
        d = str(Path(goc) / "thebrain_dieu_toc")
    p = Path(d)
    p.mkdir(parents=True, exist_ok=True)
    return p


def cau_hinh() -> dict:
    c = dict(MAC_DINH)
    try:
        c.update(json.loads(CAU_HINH.read_text(encoding="utf-8-sig")))
    except Exception:
        pass
    return c


def do_tai_nguyen() -> dict:
    """{cpu_pct, ram_trong_gb, commit_trong_gb} hoac {} neu khong do duoc (khong chan nham)."""
    try:
        import psutil
        vm, sw = psutil.virtual_memory(), psutil.swap_memory()
        return {"cpu_pct": psutil.cpu_percent(interval=0.5), "ram_trong_gb": vm.available / GB,
                "commit_trong_gb": (vm.available + max(0, sw.total - sw.used)) / GB}
    except Exception:
        return {}


def _lay_cua(cach: float, d: Path, bay_gio: float) -> bool:
    k = d / "khoi_dong.lock"
    try:
        if k.exists() and bay_gio - k.stat().st_mtime < cach:
            return False
        k.unlink(missing_ok=True)
        with open(k, "x", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        return True
    except (FileExistsError, OSError):
        return False


def duoc_vao(lan: str = "CPU", c: dict | None = None, do=None, d: Path | None = None, bay_gio: float | None = None) -> tuple[bool, str]:
    """(duoc, ly_do_cho). `do`/`d`/`bay_gio` de test."""
    if str(lan).upper() == "TESTER":
        return True, ""
    c = c or cau_hinh()
    r = (do or do_tai_nguyen)()
    if r:
        if r["cpu_pct"] > c["tran_cpu"]:
            return False, "CPU %.0f%% > tran %.0f%%" % (r["cpu_pct"], c["tran_cpu"])
        if r["ram_trong_gb"] < c["ram_trong_toi_thieu_gb"]:
            return False, "RAM trong %.1f GB < %.1f" % (r["ram_trong_gb"], c["ram_trong_toi_thieu_gb"])
        if r["commit_trong_gb"] < c["commit_toi_thieu_gb"]:
            return False, "bo nho cam ket con %.1f GB < %.1f" % (r["commit_trong_gb"], c["commit_toi_thieu_gb"])
    if not _lay_cua(float(c["cach_giay"]), d or thu_muc(), bay_gio if bay_gio is not None else time.time()):
        return False, "nguoi khac vua khoi dong, cho %ds" % int(c["cach_giay"])
    return True, ""
