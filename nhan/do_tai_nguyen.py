# -*- coding: utf-8 -*-
"""do_tai_nguyen.py - DO CHI PHI VAN HANH, khong phai chi phi giao dich.

VI SAO CO FILE NAY (30/08/2026). Trong mot phien, ba loi lam dung day chuyen
deu **khong bao mot loi nao**:

  1. `toan_van` khong co duong qua trinh duyet -> 675/1338 tai lieu khong doc
     duoc. Trieu chung: "thieu dau vao".
  2. Loi MOI TRUONG bi ghi thanh "dia chi hong" vinh vien -> 84 dia chi bi khoa
     oan. Trieu chung: khong co.
  3. `doc_gan` mo tab moi moi lan va khong dong -> **Chrome 356 tab**, luot keo
     dung han 10 phut. Trieu chung: "may treo".

Ca ba deu la HONG IM LANG: he van chay, bo test van xanh, khong ngoai le nao.
Voi mot he dinh chay 24/7 khong nguoi truc thi day la loai hong nguy hiem nhat -
no khong dung lai, no chi lang le ngung lam viec.

Cach duy nhat bat duoc chung la DO chu khong doi bao loi. File nay do bon thu,
va EVO doc chung moi luot.

Nguyen tac: chi DOC, khong sua gi, va chay xong duoi 2 giay.
"""
from __future__ import annotations

import json
import urllib.request

CDP_CONG = (9222, 9224)


def so_tab_trinh_duyet(cong=CDP_CONG) -> dict:
    """So tab dang mo tren con Chrome bot. Tang khong gioi han = ro ri."""
    for c in cong:
        try:
            d = json.load(urllib.request.urlopen(
                f"http://127.0.0.1:{c}/json/list", timeout=4))
            return {"cong": c, "so_tab": len([t for t in d if t.get("type") == "page"])}
        except Exception:
            continue
    return {"cong": None, "so_tab": None}


def ram_trinh_duyet(dau_hieu: str = "browser_darwinex") -> dict:
    """RAM con Chrome bot dang chiem, tinh bang GB."""
    try:
        import psutil
    except Exception:
        return {"gb": None, "so_tien_trinh": None}
    tong, n = 0, 0
    for p in psutil.process_iter(["name", "cmdline", "memory_info"]):
        try:
            if "chrome" not in (p.info["name"] or "").lower():
                continue
            if dau_hieu not in " ".join(p.info["cmdline"] or []):
                continue
            tong += p.info["memory_info"].rss
            n += 1
        except Exception:
            continue
    return {"gb": round(tong / 1e9, 2), "so_tien_trinh": n}


def may() -> dict:
    try:
        import psutil
    except Exception:
        return {}
    m = psutil.virtual_memory()
    return {"ram_dung_pct": m.percent, "ram_trong_gb": round(m.available / 1e9, 1),
            "cpu_pct": psutil.cpu_percent(interval=0.3)}


def tat_ca() -> dict:
    ra = {"tab": so_tab_trinh_duyet(), "chrome": ram_trinh_duyet()}
    ra.update(may())
    return ra


if __name__ == "__main__":
    print(json.dumps(tat_ca(), ensure_ascii=False, indent=1))
