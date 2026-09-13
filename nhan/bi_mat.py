# -*- coding: utf-8 -*-
"""bi_mat.py - MOT CUA doc khoa. Khong module nao tu mo file khoa.

Khoa nam o `config/tai_khoan.json` - da trong `.gitignore` tu truoc
(`**/tai_khoan.json`) va **chua tung vao lich su git** (kiem 13/09: 0 commit
cham vao no).

Vi sao can mot cua: neu moi module tu doc file khoa thi som muon co module
in no ra log, ghi vao `reports/`, hay dua vao mot thong bao loi. O day chi co
mot cho lay, va cho do KHONG BAO GIO tra ve gia tri de in - ham `co()` de hoi
"co khoa chua" ma khong lo ra khoa.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))

KHO = GOC / "config" / "tai_khoan.json"


def _doc() -> dict:
    try:
        return json.loads(KHO.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def lay(*duong: str, mac_dinh=None):
    """`lay("github", "token")`. Tra `mac_dinh` neu khong co."""
    d = _doc()
    for k in duong:
        if not isinstance(d, dict) or k not in d:
            return mac_dinh
        d = d[k]
    return d if d not in ("", None) else mac_dinh


def co(*duong: str) -> bool:
    """Hoi co khoa chua MA KHONG lo ra khoa - dung cho bao cao/mach dap."""
    return lay(*duong) is not None


def token_github() -> str | None:
    """Token GitHub: uu tien bien moi truong, roi den kho khoa.

    Do 13/09/2026: khong token = **60 luot API/GIO**, co token = 5.000. Voi
    1.013 repo lien quan trong kho thi do la 17 gio so voi mot luot.
    """
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")         or lay("github", "token")


def dau_github() -> dict:
    """Header `Authorization` neu co token, rong neu khong."""
    t = token_github()
    return {"Authorization": "Bearer " + t} if t else {}


def khoi_common_ini(san: str = "XM") -> str:
    """Khoi `[Common]` cho file `.ini` cua tester - de terminal TU dang nhap.

    ## VI SAO PHAI O DAY CHU KHONG PHAI BAM TAY

    Do 13/09/2026: sau khi dang nhap bang dong lenh (`terminal64.exe /login:
    /password: /server:`), thu muc `bases/XM.COM-MT5/` DUOC TAO - nhin nhu da
    dang nhap. Nhung luot tester ngay sau do chet voi:

        tester not started because the account is not specified

    Tuc dang nhap dong lenh KHONG luu tai khoan vao ho so terminal. Cach dung
    la khai tai khoan NGAY TRONG `.ini` cua luot chay - moi luot tu dang nhap,
    khong phu thuoc trang thai truoc do va khong can ai bam File -> Login.

    Do la dieu kien de he chay hang thang tren VPS ma khong co nguoi.
    """
    d = lay("mt5", san) or {}
    if not d.get("login") or not d.get("mat_khau"):
        return ""
    sv = d.get("server_chay_duoc") or (d.get("servers") or [""])[0]
    dong = ["[Common]", "Login=%s" % d["login"],
            "Password=%s" % d["mat_khau"], "Server=%s" % sv, "", ""]
    return chr(10).join(dong)
