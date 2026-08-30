# -*- coding: utf-8 -*-
"""Watchdog ngoai tien trinh cho control plane.

Watchdog nay phat hien ca process exit va process con song nhung scheduler khong
cap nhat lease. No duoc goi boi CHAY_NEN.cmd hoac Task Scheduler tai luc boot.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

LAB = Path(__file__).resolve().parent
PY = sys.executable
SUPERVISOR = LAB / "dieu_phoi.py"
KHOA = LAB / "dieu_phoi.lock"
DUNG = LAB / "DUNG_LAI"
LOG = LAB / "reports" / "watchdog.log"
HANG_GIAY = max(60, int(os.environ.get("BRAIN_HANG_SECONDS", "180")))
STARTUP_GRACE_GIAY = max(30, int(os.environ.get("BRAIN_STARTUP_GRACE_SECONDS", "90")))
STOP_GRACE_GIAY = max(60, int(os.environ.get("BRAIN_STOP_GRACE_SECONDS", "1500")))
_MUTEX: Any = None


def ghi(s: str) -> None:
    dong = time.strftime("%Y-%m-%d %H:%M:%S ") + "WATCHDOG " + s
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(dong + "\n")
    except OSError:
        pass
    print(dong, flush=True)


def _doc_lease() -> dict:
    try:
        raw = KHOA.read_text(encoding="utf-8-sig").strip()
        x = json.loads(raw)
        return x if isinstance(x, dict) else {}
    except json.JSONDecodeError:
        try:
            return {"pid": int(raw), "updated_epoch": KHOA.stat().st_mtime,
                    "legacy": True}
        except (ValueError, OSError, UnboundLocalError):
            return {}
    except (OSError, UnicodeError):
        return {}


def _tuoi_lease(lease: dict) -> float:
    try:
        return max(0.0, time.time() - float(lease.get("updated_epoch")))
    except (TypeError, ValueError):
        try:
            return max(0.0, time.time() - KHOA.stat().st_mtime)
        except OSError:
            return float("inf")


def _pid_song(pid: Any) -> bool:
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if psutil is not None:
        try:
            p = psutil.Process(pid)
            return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
        except psutil.Error:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _lay_mutex() -> bool:
    global _MUTEX
    if os.name != "nt":
        return True
    try:
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
        k.CreateMutexW.restype = wintypes.HANDLE
        k.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        k.WaitForSingleObject.restype = wintypes.DWORD
        handle = k.CreateMutexW(None, False,
                                r"Global\TheBrain_ResearchSP500_Watchdog")
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        ket = k.WaitForSingleObject(handle, 0)
        if ket not in (0x00000000, 0x00000080):
            k.CloseHandle(handle)
            return False
        _MUTEX = (k, handle)
        return True
    except Exception as e:
        ghi(f"khong tao duoc named mutex: {type(e).__name__}: {e}")
        return False


def _tha_mutex() -> None:
    global _MUTEX
    if _MUTEX:
        k, handle = _MUTEX
        try:
            k.ReleaseMutex(handle)
            k.CloseHandle(handle)
        except Exception:
            pass
        _MUTEX = None


def _ket_thuc_pid(pid: int) -> None:
    if psutil is not None:
        try:
            root = psutil.Process(pid)
            ds = root.children(recursive=True)
            for p in reversed(ds):
                try:
                    p.terminate()
                except psutil.Error:
                    pass
            try:
                root.terminate()
            except psutil.Error:
                pass
            _, song = psutil.wait_procs(ds + [root], timeout=8)
            for p in song:
                try:
                    p.kill()
                except psutil.Error:
                    pass
            return
        except psutil.Error:
            pass
    try:
        os.kill(pid, 9)
    except OSError:
        pass


def _doi_process_dung(p: subprocess.Popen, grace: int) -> None:
    try:
        p.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        ghi(f"supervisor khong dung sau {grace}s; ket thuc cay process pid={p.pid}")
        _ket_thuc_pid(p.pid)


def main() -> int:
    if not _lay_mutex():
        ghi("da co watchdog khac dang chay - thoat")
        return 3
    so_lan_loi = 0
    try:
        while not DUNG.exists():
            lease = _doc_lease()
            if lease and _tuoi_lease(lease) < HANG_GIAY and _pid_song(lease.get("pid")):
                ghi(f"supervisor pid={lease.get('pid')} da ton tai; theo doi lease hien tai")
                while not DUNG.exists():
                    lease = _doc_lease()
                    if not lease or not _pid_song(lease.get("pid")):
                        break
                    if _tuoi_lease(lease) > HANG_GIAY:
                        ghi(f"lease tre {_tuoi_lease(lease):.0f}s; ket thuc pid={lease.get('pid')}")
                        _ket_thuc_pid(int(lease["pid"]))
                        break
                    time.sleep(5)
                continue

            ghi("khoi dong supervisor")
            p = subprocess.Popen([PY, str(SUPERVISOR)], cwd=str(LAB),
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            bat_dau = time.time()
            bi_treo = False
            while p.poll() is None and not DUNG.exists():
                lease = _doc_lease()
                if time.time() - bat_dau > STARTUP_GRACE_GIAY:
                    tuoi = _tuoi_lease(lease)
                    if not lease or tuoi > HANG_GIAY:
                        ghi(f"supervisor pid={p.pid} khong cap nhat lease ({tuoi:.0f}s); restart")
                        _ket_thuc_pid(p.pid)
                        bi_treo = True
                        break
                time.sleep(5)

            if DUNG.exists():
                ghi("thay DUNG_LAI; cho supervisor dung co trat tu")
                _doi_process_dung(p, STOP_GRACE_GIAY)
                break
            try:
                rc = p.wait(timeout=15)
            except subprocess.TimeoutExpired:
                _ket_thuc_pid(p.pid)
                rc = -9
            if rc == 3:
                ghi("supervisor bao da co instance khac; quay lai theo doi lease")
                time.sleep(5)
                continue
            so_lan_loi = so_lan_loi + 1 if (rc != 0 or bi_treo) else 0
            cho = min(60, max(5, 5 * max(1, so_lan_loi)))
            ghi(f"supervisor thoat rc={rc}; restart sau {cho}s")
            for _ in range(cho):
                if DUNG.exists():
                    break
                time.sleep(1)
    finally:
        _tha_mutex()
    ghi("watchdog dung")
    return 0


if __name__ == "__main__":
    sys.exit(main())
