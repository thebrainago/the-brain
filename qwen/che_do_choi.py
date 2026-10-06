# -*- coding: utf-8 -*-
"""che_do_choi.py - MAY NHA THAY CHU DU AN DANG CHOI GAME (LoL) THI HA TRAN, LAM CHAM LAI (chu du an 06/10/2026).

Khi co tien trinh game trong danh sach:
  * KHONG nhan don TESTER (MT5 tester an nhieu nhan + o dia, lam giat game) va don tuong tac man hinh (pyautogui
    chiem chuot / ban phim cua nguoi dang choi) - don do de lai cho khi het game;
  * don con lai van chay nhung o do uu tien THAP NHAT (IDLE) + chi 1 phan nhan (`tran_cpu_choi` % so nhan, toi thieu 1);
  * nghi `nghi_giay` giua hai don, vong lien tuc nghi lau hon.
Game bat dau GIUA luc don dang chay: bo giam sat (moi 5 giay) ha uu tien + gioi han nhan cua don va CAY CON cua no ngay.
Het game: don ke tiep chay binh thuong (don dang chay do giu nguyen muc da ha cho den khi xong - an toan hon doi giua chung).

Cau hinh tuy chon `config/che_do_choi.json` (may-cuc-bo): {"game": ["League of Legends.exe", ...], "tran_cpu_choi": 25, "nghi_giay": 30}.
Mac dinh chi LoL (chu du an chi noi LoL); them game khac = them ten tien trinh vao tep, khong sua code.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
CAU_HINH = LAB / "config" / "che_do_choi.json"

GAME_MAC_DINH = ["League of Legends.exe", "LeagueClient.exe", "LeagueClientUx.exe"]
TRAN_CPU_CHOI = 25          # % so nhan duoc dung khi dang choi
NGHI_GIAY = 30
#: don tuong tac man hinh: khong chay khi dang choi
TU_KHOA_TUONG_TAC = ("lay_export_man_hinh", "man_hinh", "pyautogui", "dang_nhap", "tu_dang_ky", "telegram")
NHIP_GIAM_SAT = 5.0

IDLE = getattr(subprocess, "IDLE_PRIORITY_CLASS", 0x00000040)


def cau_hinh() -> dict:
    c = {"game": list(GAME_MAC_DINH), "tran_cpu_choi": TRAN_CPU_CHOI, "nghi_giay": NGHI_GIAY}
    try:
        c.update(json.loads(CAU_HINH.read_text(encoding="utf-8-sig")))
    except Exception:
        pass
    return c


def _ten_tien_trinh() -> list[str]:
    try:
        import psutil
        return [(p.info.get("name") or "") for p in psutil.process_iter(["name"])]
    except Exception:
        return []


def dang_choi(ten_dang_chay: list[str] | None = None, c: dict | None = None) -> str | None:
    """Ten game dang chay hoac None. `ten_dang_chay` de test."""
    c = c or cau_hinh()
    co = {t.lower() for t in (ten_dang_chay if ten_dang_chay is not None else _ten_tien_trinh())}
    for g in c["game"]:
        if g.lower() in co:
            return g
    return None


def don_tuong_tac(don: dict) -> bool:
    s = " ".join(str(x) for x in (don.get("lenh") or [])).lower()
    return any(k in s for k in TU_KHOA_TUONG_TAC)


def duoc_chay_khi_choi(don: dict) -> tuple[bool, str]:
    """(duoc, ly_do_khong). Dang choi: bo don TESTER va don tuong tac man hinh."""
    if str(don.get("lan") or "NHE").upper() == "TESTER":
        return False, "dang choi game: de don TESTER lai"
    if don_tuong_tac(don):
        return False, "dang choi game: de don tuong tac man hinh lai"
    return True, ""


def so_nhan_cho_phep(c: dict | None = None, so_nhan: int | None = None) -> int:
    c = c or cau_hinh()
    n = so_nhan or os.cpu_count() or 1
    return max(1, int(n * float(c["tran_cpu_choi"]) / 100.0))


def ha_tran(pid: int, c: dict | None = None) -> bool:
    """IDLE + gioi han nhan cho tien trinh va TOAN BO cay con. True neu ap dung duoc."""
    try:
        import psutil
        goc = psutil.Process(pid)
        nhan = list(range(psutil.cpu_count() or 1))[: so_nhan_cho_phep(c, psutil.cpu_count())]
        for p in [goc] + goc.children(recursive=True):
            try:
                if os.name == "nt":
                    p.nice(psutil.IDLE_PRIORITY_CLASS)
                else:
                    p.nice(19)
                if hasattr(p, "cpu_affinity"):
                    p.cpu_affinity(nhan)
            except Exception:
                continue
        return True
    except Exception:
        return False


def chay_co_giam_sat(lenh: list[str], cwd: str, han: float, env: dict, ten_dang_chay=None,
                     ha=ha_tran, nhip: float = NHIP_GIAM_SAT) -> tuple[int, str, str, bool]:
    """Chay lenh, giam sat game moi `nhip` giay. Tra (ma_thoat, stdout, stderr, da_ha_tran). Het han -> TimeoutExpired."""
    flags = IDLE if (dang_choi(ten_dang_chay) and os.name == "nt") else 0
    p = subprocess.Popen([str(x) for x in lenh], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         encoding="utf-8", errors="replace", env=env, creationflags=flags)
    da_ha = False
    t_het = time.time() + han
    if dang_choi(ten_dang_chay):
        da_ha = ha(p.pid)
    while True:
        try:
            ra, loi = p.communicate(timeout=min(nhip, max(0.1, t_het - time.time())))
            return p.returncode, ra, loi, da_ha
        except subprocess.TimeoutExpired:
            if time.time() >= t_het:
                _giet_cay(p.pid)
                p.communicate()
                raise
            if not da_ha and dang_choi(ten_dang_chay):
                da_ha = ha(p.pid)


def _giet_cay(pid: int) -> None:
    try:
        import psutil
        goc = psutil.Process(pid)
        for c in goc.children(recursive=True):
            try:
                c.kill()
            except Exception:
                pass
        goc.kill()
    except Exception:
        pass
