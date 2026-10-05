# -*- coding: utf-8 -*-
"""cham.py - MAY CHAM cho dau ra cua agent (code chan, LLM khong tu cham). Moi bo cham: (noi_dung, cau_hinh, boi_canh) -> (du lieu | None, [loi]).
Them bo cham: dang ky vao BO_CHAM hoac dung kieu 'module:ham' (ham(noi_dung, cau_hinh, boi_canh) -> (du_lieu, [loi]))."""
from __future__ import annotations

import ast
import importlib
import json
import re


def _json(nd: str):
    m = re.search(r"(\{.*\}|\[.*\])", nd, re.S)
    if not m:
        return None, ["khong thay JSON"]
    try:
        return json.loads(m.group(0)), []
    except Exception as e:                      # noqa: BLE001
        return None, ["JSON hong: %s" % e]


def cham_json(nd, ch, bc):
    d, loi = _json(nd)
    if loi:
        return None, loi
    ra = []
    if isinstance(d, dict):
        ra += ["thieu khoa '%s'" % k for k in ch.get("khoa", []) if k not in d]
    return d, ra


def cham_khong_rong(nd, ch, bc):
    return nd, [] if len(nd.strip()) >= ch.get("toi_thieu", 50) else ["qua ngan (< %d ky tu)" % ch.get("toi_thieu", 50)]


def cham_py(nd, ch, bc):
    m = re.search(r"```(?:python)?\n(.*?)```", nd, re.S)
    code = m.group(1) if m else nd
    try:
        ast.parse(code)
    except SyntaxError as e:
        return None, ["loi cu phap python dong %s: %s" % (e.lineno, e.msg)]
    return code, []


def cham_phat_hien_ma(nd, ch, bc):
    """Rà soát ma nguon: moi phat hien phai tro dung ham / lop CO THAT trong tep (chong bia), co muc do va de xuat."""
    d, loi = _json(nd)
    if loi:
        return None, loi
    ds = d.get("phat_hien") if isinstance(d, dict) else d
    if not isinstance(ds, list):
        return None, ["can {\"phat_hien\": [...]}"]
    ten = {n.name for n in ast.walk(ast.parse(bc["tep_nguon"][ch["tep"]])) if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))}
    ra = []
    if not (ch.get("it_nhat", 2) <= len(ds) <= ch.get("nhieu_nhat", 8)):
        ra.append("so phat hien phai tu %d den %d (co %d)" % (ch.get("it_nhat", 2), ch.get("nhieu_nhat", 8), len(ds)))
    for i, p in enumerate(ds):
        if not isinstance(p, dict):
            ra.append("phat_hien[%d] khong phai doi tuong" % i)
            continue
        if p.get("ham") not in ten and p.get("ham") != "(toan_tep)":
            ra.append("phat_hien[%d]: ham '%s' KHONG co trong tep (chi tro ten ham/lop that, hoac '(toan_tep)')" % (i, p.get("ham")))
        if p.get("muc_do") not in ("CAO", "TB", "THAP"):
            ra.append("phat_hien[%d]: muc_do phai CAO|TB|THAP" % i)
        if len(str(p.get("van_de", ""))) < 40 or len(str(p.get("de_xuat", ""))) < 30:
            ra.append("phat_hien[%d]: van_de >= 40 ky tu, de_xuat >= 30 ky tu, noi cu the" % i)
    return d, ra


BO_CHAM = {"json": cham_json, "khong_rong": cham_khong_rong, "py": cham_py, "phat_hien_ma": cham_phat_hien_ma}


def cham(nd: str, ch: dict, bc: dict):
    k = ch.get("kieu", "khong_rong")
    if k in BO_CHAM:
        return BO_CHAM[k](nd, ch, bc)
    if ":" in k:
        mod, ham = k.split(":", 1)
        return getattr(importlib.import_module(mod), ham)(nd, ch, bc)
    return None, ["kieu cham khong biet: %s" % k]
