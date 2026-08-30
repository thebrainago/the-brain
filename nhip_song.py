# -*- coding: utf-8 -*-
"""Mot cho duy nhat doc TRANG THAI SONG cua he — dung chung cho vao/ket phien.

Truoc day `BAN_GIAO.py` tu viet cau SQL cua no, con moi ban giao lai dem tay
mot bo so khac. Hai ban giao canh nhau khong so sanh duoc vi khong cung phep
dem. Gio ca hai goi `doc()` o day, va `KET_PHIEN` ghi lai ket qua ra
`reports/nhip_song.json` de hom sau tinh duoc CHENH LECH.

Rang buoc: chi DOC, khong import pandas, chay xong duoi 3 giay.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

LAB = Path(__file__).resolve().parent
GOC = LAB.parent
ANH = LAB / "reports" / "nhip_song.json"


def _mot(db: Path, cau: str, mac_dinh=None):
    if not db.exists():
        return mac_dinh
    try:
        cn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3)
        try:
            return cn.execute(cau).fetchone()[0]
        finally:
            cn.close()
    except Exception:
        return mac_dinh


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


def doc() -> dict:
    nao, thu_vien = LAB / "nao.db", LAB / "thu_vien.db"
    ham_test = sum(
        1 for f in LAB.glob("test_*.py")
        for l in f.read_text(encoding="utf-8", errors="ignore").splitlines()
        if l.strip().startswith("def test_"))
    viec_cho = {a: c for a, c in _bang(
        nao, "SELECT loai, COUNT(*) FROM viec WHERE trang_thai='CHO' GROUP BY 1")}
    return {
        "file_test": len(list(LAB.glob("test_*.py"))),
        "ham_test": ham_test,
        "test_ds": len(list((GOC / "ds" / "tests").glob("test_*.py"))) if (GOC / "ds" / "tests").exists() else 0,
        "bang_gia": len(list((GOC / "data").glob("*.parquet"))),
        "fdr": _mot(nao, "SELECT COUNT(*) FROM fdr"),
        "fdr_bac_bo": _mot(nao, "SELECT COUNT(*) FROM fdr WHERE bac_bo=1"),
        "ung_vien": _mot(nao, "SELECT COUNT(*) FROM candidate_queue"),
        "tai_lieu": _mot(nao, "SELECT COUNT(*) FROM tai_lieu"),
        "co_che": _mot(thu_vien, "SELECT COUNT(*) FROM co_che"),
        "van_de_mo": _mot(nao, "SELECT COUNT(*) FROM van_de WHERE trang_thai NOT IN ('XONG','DA_SUA')"),
        "van_de_nang": _mot(nao, "SELECT COUNT(*) FROM van_de WHERE muc='NANG' AND trang_thai NOT IN ('XONG','DA_SUA')"),
        "viec_cho": viec_cho,
        "viec_cho_tong": sum(viec_cho.values()),
        "dung_lai": (LAB / "DUNG_LAI").exists(),
        "py_top": len(list(LAB.glob("*.py"))),
    }


def anh_cu() -> dict:
    try:
        return json.loads(ANH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def luu(t: dict, ngay: str) -> None:
    ANH.parent.mkdir(exist_ok=True)
    ANH.write_text(json.dumps({"ngay": ngay, **t}, ensure_ascii=False, indent=1),
                   encoding="utf-8")


def chenh(moi: dict, cu: dict) -> dict:
    """Chi tra ve nhung khoa DOI. Khong doi thi khong dang in ra."""
    ra = {}
    for k, v in moi.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            c = cu.get(k)
            if isinstance(c, (int, float)) and c != v:
                ra[k] = v - c
    return ra


def git(args: list, cwd: Path = GOC) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                           text=True, encoding="utf-8", errors="ignore", timeout=20)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def co_git() -> bool:
    return (GOC / ".git").exists()
