# -*- coding: utf-8 -*-
"""_va_duong_dan.py - Thay duong LAB go cung bang `Path(__file__)`.

Bo kiem `nhan/san_sang_vps.py` do duoc 55 lan duong lab duoc go cung trong 50
file. Hai dang chiem 44/55 va ca hai deu sua co hoc duoc an toan:

    sys.path.insert(0, r"C:\\...\\lab")   ->  sys.path.insert(0, str(_GOC_LAB))
    LAB = Path(r"C:\\...\\lab")           ->  LAB = _GOC_LAB

voi `_GOC_LAB = Path(__file__).resolve().parent`. File nam o goc lab nen
`parent` chinh la lab; file trong `nhan/` thi la `parent.parent` - bo va tu do
theo VI TRI THAT cua file.

KHONG sua dang "chuoi khac" (11 lan) - chung nam trong chu thich, thong diep
loi, hoac duong dan dan xuat; sua may se hong nghia.

Moi file deu duoc `ast.parse` lai sau khi sua; hong thi tra lai nguyen ban.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
BO = ("nhat_ky", "backups", "__pycache__", "nghi_huu", ".git")

_TXT = str(LAB)                      # "C:\...\lab"
_KHAI = "_GOC_LAB = Path(__file__).resolve().parent"


def _bao_nhieu_tang(p: Path) -> int:
    """File cach goc lab may tang thu muc."""
    return len(p.resolve().relative_to(LAB).parts) - 1


def va_mot(p: Path) -> tuple[bool, str]:
    try:
        goc = p.read_text(encoding="utf-8-sig")
    except Exception as e:
        return False, "khong doc duoc: %s" % e
    if _TXT not in goc:
        return False, "khong co duong go cung"

    tang = _bao_nhieu_tang(p)
    bieu_thuc = "Path(__file__).resolve().parent" + ".parent" * tang
    s = goc
    n = 0

    # 1) sys.path.insert(0, r"...lab")  /  sys.path.append(...)
    mau_sp = re.compile(
        r'(sys\.path\.(?:insert|append)\(\s*(?:0\s*,\s*)?)[rRuU]?["\']'
        + re.escape(_TXT) + r'["\']')
    s, k = mau_sp.subn(lambda m: m.group(1) + "str(%s)" % bieu_thuc, s)
    n += k

    # 2) <TEN> = Path(r"...lab")
    # Ten bien HOA LAN THUONG. Ban dau toi chi bat `[A-Z_]` va no bo sot dung
    # dang pho bien nhat: `lab=Path(r"C:\...")` trong cac script chien luoc
    # (18 lan). Mot bo va bo sot 18/33 cho thi bao cao "da sua" la sai.
    mau_lab = re.compile(
        r'(\b[A-Za-z_][A-Za-z_0-9]*\s*=\s*)Path\(\s*[rRuU]?["\']'
        + re.escape(_TXT) + r'["\']\s*\)')
    s, k = mau_lab.subn(lambda m: m.group(1) + bieu_thuc, s)
    n += k

    if not n:
        return False, "chi con dang 'chuoi khac' - khong sua may"
    if "from pathlib import Path" not in s and "import pathlib" not in s:
        # Chen import ngay truoc lan dung dau tien, sau khoi docstring
        cay = ast.parse(goc)
        dong = 0
        for nut in cay.body:
            if isinstance(nut, (ast.Import, ast.ImportFrom)):
                dong = nut.lineno
        d = s.splitlines()
        d.insert(max(dong, 0), "from pathlib import Path")
        s = "\n".join(d) + ("\n" if goc.endswith("\n") else "")
    try:
        ast.parse(s)
    except SyntaxError as e:
        return False, "sua xong thi hong cu phap (%s) - GIU NGUYEN" % e
    p.write_text(s, encoding="utf-8")
    return True, "sua %d cho" % n


def main(argv: list[str]) -> int:
    that = "--that" in argv
    xong, bo_qua = [], []
    for p in sorted(LAB.rglob("*.py")):
        if any(x in str(p) for x in BO) or p.name == Path(__file__).name:
            continue
        if _TXT not in p.read_text(encoding="utf-8-sig", errors="ignore"):
            continue
        if not that:
            bo_qua.append((p.name, "(thu kho - them --that de sua that)"))
            continue
        ok, ly_do = va_mot(p)
        (xong if ok else bo_qua).append((p.name, ly_do))
    print("SUA: %d file" % len(xong))
    for t, l in xong[:40]:
        print("  %-30s %s" % (t, l))
    print("\nKHONG SUA: %d file" % len(bo_qua))
    for t, l in bo_qua[:12]:
        print("  %-30s %s" % (t, l))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
