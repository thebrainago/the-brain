# -*- coding: utf-8 -*-
"""Tham chieu TREO giua cac module (10/10/2026): `ALIAS.ten` ma module dich khong dinh nghia `ten`.

Vi sao co bai nay: 07/10 `qwen/dieu_toc.py` bi viet lai (commit 4b2bd29e), lop `DieuToc` va ham `do_nhanh` mat, nhung `qwen/chay.py` (bo chay `q`) va 3 test van
goi chung -> `q` chet ngay khi khoi dong ma khong bai nao bao trong 3 ngay. Hai cho khac cung kieu NHUNG bi `except Exception` nuot nen khong ai thay:
`ho_so_symbol` goi `du_lieu.bar_moi_nam` (khong co, la `do_luong`) -> luon 252 bar/nam; `do_im_lang` goi `doc_trinh_duyet.dang_chay` (khong co) -> luon "CDP TAT".
Phep quet TINH (khong chay ma, khong can gia / nao.db) nen chay duoc o moi may. Cho phep truy cap co `hasattr(ALIAS, "ten")` / `getattr(ALIAS, "ten", ..)`
o cung tep (cach viet co chu dich). Tep khong parse duoc bang Python dang chay (cu phap moi hon) bi bo qua, khong lam do."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent
GOI = ("nhan", "tru", "qwen")


def _doc_nguon(goc: Path, goi=GOI) -> dict:
    """{ten module cham: (duong dan, cay AST)} cho `*.py` o goc va trong cac goi."""
    ra = {}
    cac_tep = list(goc.glob("*.py"))
    for g in goi:
        cac_tep += list((goc / g).glob("*.py"))
    for p in sorted(cac_tep):
        phan = p.relative_to(goc).with_suffix("").parts
        ten = ".".join(phan[:-1] if phan[-1] == "__init__" else phan)
        try:
            ra[ten] = (p, ast.parse(p.read_text(encoding="utf-8-sig")))
        except (SyntaxError, ValueError):
            continue
    return ra


def _ten_cap_module(cay: ast.Module, nut: list) -> tuple[set, bool]:
    """(cac ten gan o cap module, co the con ten nua?) - `from x import *` hoac `__getattr__` thi khong the khang dinh la thieu."""
    ten, mo = set(), False

    def dich(t):
        if isinstance(t, ast.Name):
            ten.add(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for e in t.elts:
                dich(e)
        elif isinstance(t, ast.Starred):
            dich(t.value)

    def duyet(ds):
        nonlocal mo
        for s in ds:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                ten.add(s.name)
                mo = mo or s.name == "__getattr__"
            elif isinstance(s, ast.Assign):
                for t in s.targets:
                    dich(t)
            elif isinstance(s, (ast.AnnAssign, ast.AugAssign)):
                dich(s.target)
            elif isinstance(s, ast.Import):
                ten.update((a.asname or a.name).split(".")[0] for a in s.names)
            elif isinstance(s, ast.ImportFrom):
                for a in s.names:
                    if a.name == "*":
                        mo = True
                    else:
                        ten.add(a.asname or a.name)
            elif isinstance(s, (ast.If, ast.While)):
                duyet(s.body), duyet(s.orelse)
            elif isinstance(s, ast.For):
                dich(s.target), duyet(s.body), duyet(s.orelse)
            elif isinstance(s, ast.With):
                for it in s.items:
                    if it.optional_vars is not None:
                        dich(it.optional_vars)
                duyet(s.body)
            elif isinstance(s, ast.Try):
                duyet(s.body), duyet(s.orelse), duyet(s.finalbody)
                for h in s.handlers:
                    ten.add(h.name) if h.name else None
                    duyet(h.body)
    duyet(cay.body)
    ten.update(n for x in nut if isinstance(x, ast.Global) for n in x.names)      # `global X` gan trong ham
    return ten, mo


def _bi_danh(ten: str, p: Path, nut: list, cac_mod: dict) -> dict:
    """{bi danh trong tep: {module dich | None}} - None = khong phai module trong repo (hoac mo ho) -> khong kiem."""
    ra = {}
    goi = ten if p.name == "__init__.py" else (ten.rsplit(".", 1)[0] if "." in ten else "")
    for n in nut:
        if isinstance(n, ast.ImportFrom):
            phan = goi.split(".") if goi else []
            goc = ".".join((phan[:len(phan) - (n.level - 1)] if n.level > 1 else phan) + ([n.module] if n.module else [])) \
                if n.level else (n.module or "")
            for a in n.names:
                if a.name != "*":
                    day_du = f"{goc}.{a.name}" if goc else a.name
                    ra.setdefault(a.asname or a.name, set()).add(day_du if day_du in cac_mod else None)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.asname:
                    ra.setdefault(a.asname, set()).add(a.name if a.name in cac_mod else None)
                elif a.name in cac_mod and "." not in a.name:
                    ra.setdefault(a.name, set()).add(a.name)
    return ra


def quet(goc: Path = LAB, goi=GOI) -> list[tuple]:
    """[(tep, dong, bi danh, module, ten)] cho moi `BI_DANH.ten` ma module dich khong co `ten`."""
    cac_mod = _doc_nguon(goc, goi)
    nut_cua = {m: list(ast.walk(cay)) for m, (_, cay) in cac_mod.items()}                  # di cay MOT lan / module (tiet kiem ~10 s)
    tren = {m: _ten_cap_module(cay, nut_cua[m]) for m, (_, cay) in cac_mod.items()}
    ra = set()
    for ten_mod, (p, cay) in cac_mod.items():
        nut = nut_cua[ten_mod]
        bd = _bi_danh(ten_mod, p, nut, cac_mod)
        gan_lai = {n.arg for n in nut if isinstance(n, ast.arg)} | \
                  {n.id for n in nut if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        co_bao_ve = {(c.args[0].id, c.args[1].value) for c in nut
                     if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in ("hasattr", "getattr")
                     and len(c.args) >= 2 and isinstance(c.args[0], ast.Name)
                     and isinstance(c.args[1], ast.Constant) and isinstance(c.args[1].value, str)}
        for n in nut:
            if not (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and isinstance(n.ctx, ast.Load)):
                continue
            al = n.value.id
            dich = bd.get(al)
            if not dich or len(dich) != 1 or None in dich or al in gan_lai or (al, n.attr) in co_bao_ve:
                continue
            d = next(iter(dich))
            ten, mo = tren[d]
            if not mo and n.attr not in ten and not n.attr.startswith("__"):
                ra.add((str(p.relative_to(goc)).replace("\\", "/"), n.lineno, al, d, n.attr))
    return sorted(ra)


def test_phep_quet_bat_duoc_tham_chieu_treo_va_khong_bao_nham(tmp_path):
    """Hieu chuan HAI CHIEU: phai BAT cai thieu that, va KHONG bao nham cac cach viet co chu dich."""
    pk = tmp_path / "pk"
    pk.mkdir()
    (pk / "__init__.py").write_text("", encoding="utf-8")
    (pk / "a.py").write_text("def ok():\n    return 1\nX = 1\nif X:\n    Y = 2\ntry:\n    import json as J\nexcept ImportError:\n    J = None\n", encoding="utf-8")
    (pk / "dong.py").write_text("def __getattr__(ten):\n    return ten\n", encoding="utf-8")
    (pk / "sao.py").write_text("from os.path import *\n", encoding="utf-8")
    (pk / "b.py").write_text(
        "from . import a as A\nfrom . import dong as D\nfrom . import sao as S\n"
        "A.ok(); A.X; A.Y; A.J\n"                                   # co that -> khong bao
        "A.mat\n"                                                   # THIEU THAT -> dung 1 bao cao, dong 5
        "hasattr(A, 'co_chu_dich') and A.co_chu_dich\n"             # co bao ve -> khong bao
        "D.gi_cung_duoc; S.gi_cung_duoc\n", encoding="utf-8")       # module co __getattr__ / import * -> khong the khang dinh la thieu
    (pk / "c.py").write_text("from . import a as A\n\ndef f(A):\n    return A.zzz\n", encoding="utf-8")    # bi danh bi gan lai -> khong kiem
    assert quet(tmp_path, ("pk",)) == [("pk/b.py", 5, "A", "pk.a", "mat")]


@pytest.mark.cham                                                                           # parse ~670 module: ~12 s
def test_khong_module_nao_goi_ten_ma_module_dich_khong_co():
    treo = quet()
    assert not treo, "tham chieu treo (tep:dong bi_danh.ten):\n  " + "\n  ".join(
        f"{t}:{d} {b}.{n}  (module {m} khong co `{n}`)" for t, d, b, m, n in treo)
