# -*- coding: utf-8 -*-
"""duong_dan.py - MOT CHO duy nhat giai cac duong dan phu thuoc MAY.

## Vi sao

Chu du an 12/09/2026 chot: he se chuyen len **VPS chay 24/7 nhieu thang**.
Bo kiem `nhan/san_sang_vps.py` do duoc **26 duong dan tuyet doi go cung** trong
ma nguon - va chung se gay ngay khi doi may:

    C:\\Users\\SV STORE\\Downloads\\Research SP500\\lab        52 lan
    C:\\Program Files\\MetaTrader 5\\terminal64.exe            4 lan
    C:\\Users\\SV STORE\\AppData\\Roaming\\MetaQuotes\\Terminal  4 lan
    C:\\Users\\SV STORE\\Desktop                              3 lan

Ba duong sau khong chi khac duong dan - chung khac **theo tung may**: ten nguoi
dung khac, MT5 co the cai o o khac, VPS thuong khong co Desktop.

## Quy tac

Moi duong deu doc theo thu tu: **bien moi truong -> do tu he -> mac dinh**.
Khong cai nao nem loi khi khong tim thay; nguoi goi tu quyet dinh. Ly do: mot
script bao cao khong duoc chet chi vi may khong cai MT5.
"""
from __future__ import annotations

import os
from pathlib import Path

#: Goc cua lab - do TU VI TRI FILE NAY, khong bao gio go cung.
LAB = Path(__file__).resolve().parent.parent
#: Thu muc du an (chua ca `lab/` lan `ds/`).
GOC = LAB.parent


def _tu_bien(ten: str) -> Path | None:
    v = os.environ.get(ten)
    return Path(v) if v else None


def cache_khung() -> Path:
    """Thu muc CACHE bang gia theo khung. Doi cho duoc bang bien `BRAIN_CACHE`.

    Vi sao can doi cho duoc (12/09/2026): o C day 100% (con 177 MB tren 120 GB)
    va moi khau ghi cua he that bai AM - SQLite nem "disk is full", ham boc bat
    Exception roi tra ve rong, hang doi cham theo ma thoat nen bao "XONG rc=0".
    Ba me boc lien tiep khong sinh ra mot co che nao.

    `data_khung` la CACHE - tai tao duoc tu `data/`, nen no la thu dau tien nen
    day sang o khac. Chu du an cho phep luu tam sang o F ngay 12/09.
    """
    b = _tu_bien("BRAIN_CACHE")
    if b:
        return b
    f = Path("F:/TheBrain_luu/data_khung")
    if f.exists():
        return f
    return LAB / "data_khung"


def kho_gia() -> Path:
    """Thu muc du lieu gia goc (`data/`). Doi cho bang bien `BRAIN_DATA`."""
    b = _tu_bien("BRAIN_DATA")
    if b:
        return b
    f = Path("F:/TheBrain_luu/data")
    if f.exists():
        return f
    return LAB / "data"          # 18/09: khong con `<goc>/data` — goc du an
                                 # chi con The Brain, Phase 1 o sp500_phase1/


def python_exe() -> str:
    """Trinh thong dich Python dang chay.

    Vai script go cung `C:\\Users\\SV STORE\\AppData\\Local\\Python\\...` - do
    khong chi la duong dan cua mot may, ma la duong dan cua mot BAN CAI. Doi
    ban Python (hoac dung moi truong ao) la gay, ngay tren chinh may nay.
    `sys.executable` luon dung, va no mien phi.
    """
    import sys as _s
    return _s.executable


def mt5_exe() -> Path | None:
    """`terminal64.exe`. Bien `BRAIN_MT5` -> cac cho cai thong thuong -> None.

    May nay co IT NHAT HAI ban MT5 (MetaTrader 5 mac dinh va XM MT5), va
    CLAUDE.md muc 18 ghi con co toi **5 thu muc du lieu MT5**. Nen danh sach do
    phai co ca hai, va nguoi goi can ban cu the thi truyen `BRAIN_MT5`.
    """
    p = _tu_bien("BRAIN_MT5")
    if p and p.exists():
        return p
    ung_vien = [
        Path(r"C:\Program Files\MetaTrader 5\terminal64.exe"),
        Path(r"C:\Program Files\XM MT5\terminal64.exe"),
        Path(r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe"),
        Path(r"C:\Program Files (x86)\XM MT5\terminal64.exe"),
    ]
    for goc in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432")):
        if goc:
            ung_vien.append(Path(goc) / "XM MT5" / "terminal64.exe")
    for goc in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"),
                os.environ.get("LOCALAPPDATA")):
        if goc:
            ung_vien.append(Path(goc) / "MetaTrader 5" / "terminal64.exe")
    for c in ung_vien:
        if c.exists():
            return c
    return None


def mt5_du_lieu() -> Path | None:
    """Thu muc DU LIEU cua MT5 (`.../AppData/Roaming/MetaQuotes/Terminal`).

    KHONG phai thu muc cai dat. Day la noi chua `MQL5/`, `.set`, bao cao tester.
    May nay tung co **5 thu muc du lieu MT5** (CLAUDE.md muc 18) nen ham tra ve
    thu muc GOC, nguoi goi tu quet cac thu muc con.
    """
    p = _tu_bien("BRAIN_MT5_DATA")
    if p and p.exists():
        return p
    ad = os.environ.get("APPDATA")
    if ad:
        d = Path(ad) / "MetaQuotes" / "Terminal"
        if d.exists():
            return d
    return None


def desktop() -> Path:
    """Desktop cua nguoi dung. VPS thuong khong co - luc do tra ve `LAB`.

    Khong nem loi: mot script bao cao khong duoc chet chi vi may khong co
    Desktop. Noi ghi bao cao la thu co the lui ve cho khac.
    """
    p = _tu_bien("BRAIN_DESKTOP")
    if p:
        return p
    d = Path.home() / "Desktop"
    return d if d.exists() else LAB


def so_dang(ten: str = "nao.db") -> Path:
    """Duong toi mot so SQLite trong lab."""
    return LAB / ten


def tom_tat() -> dict:
    """Bang giai duong dan hien tai - de bo kiem VPS in ra."""
    m, d = mt5_exe(), mt5_du_lieu()
    return {"LAB": str(LAB), "GOC": str(GOC),
            "mt5_exe": str(m) if m else None,
            "mt5_du_lieu": str(d) if d else None,
            "desktop": str(desktop())}


if __name__ == "__main__":
    import json
    print(json.dumps(tom_tat(), ensure_ascii=False, indent=1))
