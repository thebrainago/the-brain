# -*- coding: utf-8 -*-
"""_va_python_exe.py - Thay duong TRINH THONG DICH go cung bang `sys.executable`.

Do 12/09/2026: 5 lan duong `C:\\Users\\SV STORE\\AppData\\Local\\Python\\...`
duoc go cung trong ma nguon.

Do khong chi la duong cua mot MAY - no la duong cua mot BAN CAI. Ba viec rat
binh thuong deu lam no gay:
    * nang Python 3.14 -> 3.15
    * chuyen sang moi truong ao
    * chuyen VPS (dich da chot 12/09)

`sys.executable` luon dung va khong ton gi.

Chi sua dong MA THAT (gan cho mot bien hoac truyen vao `subprocess`). Dong nam
trong chu thich / docstring thi GIU - sua may se lam hong nghia cua ghi chu.
Moi file deu `ast.parse` lai; hong thi tra ve nguyen ban.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
BO = ("nhat_ky", "backups", "__pycache__", "nghi_huu", ".git")

#: Bat moi duong tro toi python.exe trong AppData cua nguoi dung.
_MAU = re.compile(
    r'Path\(\s*[rRuU]?["\'][A-Za-z]:[\\/]Users[\\/][^"\']*?python\.exe["\']\s*\)'
    r'|[rRuU]?["\'][A-Za-z]:[\\/]Users[\\/][^"\']*?python\.exe["\']')


def _trong_chu_thich(dong: str) -> bool:
    t = dong.lstrip()
    return t.startswith("#")


def va_mot(p: Path) -> tuple[bool, str]:
    try:
        goc = p.read_text(encoding="utf-8-sig")
    except Exception as e:
        return False, "khong doc duoc: %s" % e
    if not _MAU.search(goc):
        return False, "khong co duong python go cung"

    d = goc.splitlines(keepends=True)
    n = 0
    for i, dong in enumerate(d):
        if not _MAU.search(dong) or _trong_chu_thich(dong):
            continue
        moi = _MAU.sub("sys.executable", dong)
        # `Path(...)` -> `Path(sys.executable)` da duoc mau nuot ca vo Path,
        # nen phai boc lai khi ben trai doi mot Path.
        if "Path(" in dong and "Path(sys.executable)" not in moi:
            moi = moi.replace("sys.executable", "Path(sys.executable)", 1)
        d[i] = moi
        n += 1
    if not n:
        return False, "chi xuat hien trong chu thich - giu nguyen"
    s = "".join(d)
    if not re.search(r"^import sys$|^import sys\b", s, re.M):
        cay = ast.parse(goc)
        dong_cuoi = 0
        for nut in cay.body:
            if isinstance(nut, (ast.Import, ast.ImportFrom)):
                dong_cuoi = nut.lineno
        dd = s.splitlines()
        dd.insert(max(dong_cuoi, 0), "import sys")
        s = "\n".join(dd) + ("\n" if goc.endswith("\n") else "")
    try:
        ast.parse(s)
    except SyntaxError as e:
        return False, "sua xong hong cu phap (%s) - GIU NGUYEN" % e
    p.write_text(s, encoding="utf-8")
    return True, "sua %d cho" % n


def main(argv: list[str]) -> int:
    that = "--that" in argv
    xong, bo = [], []
    for p in sorted(LAB.rglob("*.py")):
        if any(x in str(p) for x in BO) or p.name == Path(__file__).name:
            continue
        try:
            if not _MAU.search(p.read_text(encoding="utf-8-sig", errors="ignore")):
                continue
        except Exception:
            continue
        if not that:
            bo.append((p.name, "(thu kho - them --that)"))
            continue
        ok, ly_do = va_mot(p)
        (xong if ok else bo).append((p.name, ly_do))
    print("SUA: %d file" % len(xong))
    for t, l in xong:
        print("  %-30s %s" % (t, l))
    print("\nKHONG SUA: %d file" % len(bo))
    for t, l in bo[:10]:
        print("  %-30s %s" % (t, l))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
