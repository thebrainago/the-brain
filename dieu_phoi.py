# -*- coding: utf-8 -*-
"""Control plane 24/7 cho nam tru hien hanh cua THE BRAIN.

Mot supervisor duy nhat lap lich theo su kien. Cac tru chay trong tien trinh
rieng, song song theo lane va cung nam trong mot ngan sach CPU cap he dieu hanh.
Ket qua cua tru duoc danh gia bang ca exit code, JSON stdout va nhip tim; vi vay
mot wrapper rc=0 nhung tra ve ``loi`` khong con bi ghi nhan la thanh cong.

Chay:
    python dieu_phoi.py
    python dieu_phoi.py --phut 60
    python dieu_phoi.py --trang-thai
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
from nhan import so as SO

try:
    import psutil
except ImportError:  # pragma: no cover - chi xay ra tren VPS chua cai dependency
    psutil = None

PY = sys.executable
KHOA = LAB / "dieu_phoi.lock"
DUNG = LAB / "DUNG_LAI"
LOG = LAB / "reports" / "dieu_phoi.log"
CONTROL = LAB / "reports" / "control_plane.json"


def _env_int(ten: str, mac_dinh: int, thap: int, cao: int) -> int:
    try:
        return min(cao, max(thap, int(os.environ.get(ten, mac_dinh))))
    except (TypeError, ValueError):
        return mac_dinh


def _env_float(ten: str, mac_dinh: float, thap: float, cao: float) -> float:
    try:
        return min(cao, max(thap, float(os.environ.get(ten, mac_dinh))))
    except (TypeError, ValueError):
        return mac_dinh


# CPU cap tuyet doi khong vuot 85%, ke ca khi bien moi truong dat cao hon.
CPU_TOI_DA = _env_float("BRAIN_CPU_LIMIT", 85.0, 10.0, 85.0)
CPU_NGUONG_KHOI_DONG = max(5.0, CPU_TOI_DA - 5.0)
SO_WORKER = _env_int("BRAIN_MAX_WORKERS", 3, 1, 5)
NHIP_DIEU_PHOI_GIAY = 20.0
VONG_DIEU_PHOI_GIAY = 2.0
KHOA_CU_GIAY = 45.0
TY_LE_KHAM_PHA = 0.70

# Moi lane chi chay mot tru mot luc. Gioi han nay tranh hai cong viec cung tranh
# mot profile browser/LLM hoac cung lam bao tri SQLite, trong khi van cho phep ba
# loai tai song song tren may 20 logical CPU.
LAN_GIOI_HAN = {"compute": 1, "external": 1, "maintenance": 1}

# tru -> script, ngan sach, chu ky toi thieu, nhom, lane, uu tien khoi dong.
#
# NGAN SACH DAT THEO SO DO THAT (30/08/2026), khong dat theo cam tinh.
#
# Nguyen tac: `ngan_sach` la LUOI AN TOAN (het thi giet), khong phai muc tieu.
# Mot luot bi giet giua chung la mot luot MAT TRANG - cong da lam khong ghi so.
# Nen dat theo cong thuc:
#
#     ngan_sach ~= 3x thoi gian luot DIEN HINH
#
# de mot ngay cham bat thuong van chay xong, con mot luot treo that su thi van
# bi cat. Con viec giu luot ngan thi phai lam bang TRAN CONG VIEC ben trong tung
# tru (`gioi_han` so tai lieu, so o quet...), khong bang dong ho.
#
# | tru      | do duoc 30/08        | ngan sach |
# |----------|----------------------|-----------|
# | SEEKER   | 60-100 s (15 tai lieu/luot, doc qua trinh duyet)  | 420 |
# | QUANTLAB | quet 1.830 o het 99,7 s sau khi sua hai cho dem   | 600 |
# | NGHI     | 4 s                  | 120 |
# | BANKER   | 27 s                 | 180 |
# | EVO      | 24 s                 | 150 |
#
# CHU KY dat theo TOC DO DOI MOI CUA DAU VAO, khong theo "cang day cang tot":
# nguon RSS ra bai theo ngay nen SEEKER 15 phut la thua; vi mo ra so theo ngay
# nen BANKER 1 gio la thua. Do 16/08: SEEKER ban cu chay 8.719 lan trong 5,3
# gio, moi lan 0,2 giay doc lai mot file tinh - tuc 8.718 lan la vong lap rong.
TRU = {
    "QUANTLAB": {"script": "tru/quantlab.py", "ngan_sach": 600, "chu_ky": 120,
                 "nhom": "kham_pha", "lan": "compute", "uu_tien": 20},
    "NGHI": {"script": "tru/nghi.py", "ngan_sach": 120, "chu_ky": 5400,
             "nhom": "kham_pha", "lan": "external", "uu_tien": 40},
    "SEEKER": {"script": "tru/seeker.py", "ngan_sach": 420, "chu_ky": 900,
               "nhom": "kham_pha", "lan": "external", "uu_tien": 10},
    "BANKER": {"script": "tru/banker.py", "ngan_sach": 180, "chu_ky": 3600,
               "nhom": "bao_tri", "lan": "maintenance", "uu_tien": 30},
    "EVO": {"script": "tru/evolution.py", "ngan_sach": 150, "chu_ky": 900,
            "nhom": "bao_tri", "lan": "maintenance", "uu_tien": 0},
}

#: Ty le canh bao: luot nao thuong xuyen cham hon `ngan_sach * TY_LE_SAT_TRAN`
#: la dau hieu tran dat sai HOAC tru dang phinh viec. EVO doc con so nay.
TY_LE_SAT_TRAN = 0.75

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
_INSTANCE_ID = uuid.uuid4().hex
_STARTED_EPOCH = time.time()
try:
    _PROCESS_CREATED_EPOCH = (psutil.Process(os.getpid()).create_time()
                              if psutil is not None else _STARTED_EPOCH)
except Exception:
    _PROCESS_CREATED_EPOCH = _STARTED_EPOCH
_MUTEX_HANDLE: Any = None
_FALLBACK_LOCK_FD: int | None = None
_PROCESS_LOCK = threading.Lock()
_PROCESS_RUNNING: dict[int, subprocess.Popen] = {}


def ghi(s: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    dong = time.strftime("%Y-%m-%d %H:%M:%S ") + s
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(dong + "\n")
    except Exception:
        pass
    print(dong, flush=True)


def _ghi_json_nguyen_tu(duong: Path, du_lieu: dict) -> None:
    duong.parent.mkdir(parents=True, exist_ok=True)
    tam = duong.with_name(f".{duong.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tam.write_text(json.dumps(du_lieu, ensure_ascii=False, indent=1, default=str),
                   encoding="utf-8")
    os.replace(tam, duong)


def _doc_lease() -> dict:
    try:
        raw = KHOA.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError):
        return {}
    try:
        x = json.loads(raw)
        return x if isinstance(x, dict) else {}
    except json.JSONDecodeError:
        try:
            return {"pid": int(raw), "legacy": True, "updated_epoch": KHOA.stat().st_mtime}
        except (ValueError, OSError):
            return {}


def _pid_song(pid: Any, created_epoch: Any = None) -> bool:
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if psutil is not None:
        try:
            p = psutil.Process(pid)
            if created_epoch is not None and abs(p.create_time() - float(created_epoch)) > 3:
                return False
            return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
        except (psutil.Error, OSError, ValueError):
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _lease_tuoi(lease: dict | None = None) -> float:
    lease = lease or _doc_lease()
    try:
        return max(0.0, time.time() - float(lease.get("updated_epoch")))
    except (TypeError, ValueError):
        try:
            return max(0.0, time.time() - KHOA.stat().st_mtime)
        except OSError:
            return float("inf")


def _lay_named_mutex() -> bool | None:
    """Lay mutex cap OS. Mutex tu duoc nha khi process chet."""
    global _MUTEX_HANDLE
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = kernel32.CreateMutexW(None, False,
                                       r"Global\TheBrain_ResearchSP500_DieuPhoi")
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        ket = kernel32.WaitForSingleObject(handle, 0)
        if ket not in (0x00000000, 0x00000080):  # OBJECT_0, ABANDONED
            kernel32.CloseHandle(handle)
            return False
        _MUTEX_HANDLE = handle
        return True
    except Exception as e:
        ghi(f"named mutex khong dung duoc ({type(e).__name__}: {e}); dung khoa file atomic")
        return None


def _khoa() -> bool:
    """Single instance nguyen tu, dong thoi tuong thich lock PID ban cu."""
    global _FALLBACK_LOCK_FD
    lease = _doc_lease()
    if lease and _lease_tuoi(lease) < KHOA_CU_GIAY and _pid_song(
            lease.get("pid"), lease.get("process_created_epoch")):
        return False
    mutex = _lay_named_mutex()
    if mutex is False:
        return False
    if mutex is None:
        try:
            _FALLBACK_LOCK_FD = os.open(KHOA, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            lease = _doc_lease()
            if _lease_tuoi(lease) < KHOA_CU_GIAY and _pid_song(lease.get("pid")):
                return False
            try:
                KHOA.unlink()
                _FALLBACK_LOCK_FD = os.open(KHOA, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except (FileExistsError, OSError):
                return False
    return True


def _tha_khoa() -> None:
    global _MUTEX_HANDLE, _FALLBACK_LOCK_FD
    lease = _doc_lease()
    if lease.get("instance_id") == _INSTANCE_ID or lease.get("pid") == os.getpid():
        try:
            KHOA.unlink()
        except OSError:
            pass
    if _FALLBACK_LOCK_FD is not None:
        try:
            os.close(_FALLBACK_LOCK_FD)
        except OSError:
            pass
        _FALLBACK_LOCK_FD = None
    if _MUTEX_HANDLE is not None and os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.ReleaseMutex(_MUTEX_HANDLE)
            kernel32.CloseHandle(_MUTEX_HANDLE)
        except Exception:
            pass
        _MUTEX_HANDLE = None


def giu_may_thuc() -> bool:
    try:
        import ctypes
        return bool(ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED))
    except Exception:
        return False


def tha_may_ngu() -> None:
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    except Exception:
        pass


def ghi_gian_doan() -> float:
    n = SO.mot("SELECT luc FROM nhip WHERE tru='DIEU_PHOI'")
    if not n:
        return 0.0
    try:
        cach = (datetime.now() - datetime.strptime(
            n["luc"], "%Y-%m-%d %H:%M:%S")).total_seconds()
    except Exception:
        return 0.0
    gio = cach / 3600.0
    if gio >= 0.5:
        chi_tiet = {"gio": round(gio, 2), "nhip_cuoi": n["luc"],
                    "nguyen_nhan": "khong_xac_dinh"}
        SO.ghi_chi_so("gian_doan_gio", round(gio, 2), chi_tiet)
        SO.ghi_su_kien("DIEU_PHOI", "gian_doan", chi_tiet)
    return gio


class WindowsJob:
    """Job Object gom cay child, hard-cap CPU va kill child khi supervisor chet."""

    def __init__(self, cpu_limit: float):
        self.handle: Any = None
        self.error = ""
        if os.name != "nt":
            self.error = "khong_phai_windows"
            return
        try:
            import ctypes
            from ctypes import wintypes

            ULONG_PTR = ctypes.c_size_t
            SIZE_T = ctypes.c_size_t

            class BASIC_LIMIT(ctypes.Structure):
                _fields_ = [
                    ("PerProcessUserTimeLimit", ctypes.c_longlong),
                    ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", SIZE_T),
                    ("MaximumWorkingSetSize", SIZE_T),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ULONG_PTR),
                    ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD),
                ]

            class IO_COUNTERS(ctypes.Structure):
                _fields_ = [(n, ctypes.c_ulonglong) for n in (
                    "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                    "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

            class EXTENDED_LIMIT(ctypes.Structure):
                _fields_ = [
                    ("BasicLimitInformation", BASIC_LIMIT),
                    ("IoInfo", IO_COUNTERS),
                    ("ProcessMemoryLimit", SIZE_T),
                    ("JobMemoryLimit", SIZE_T),
                    ("PeakProcessMemoryUsed", SIZE_T),
                    ("PeakJobMemoryUsed", SIZE_T),
                ]

            class CPU_RATE(ctypes.Structure):
                _fields_ = [("ControlFlags", wintypes.DWORD),
                            ("CpuRate", wintypes.DWORD)]

            k = ctypes.WinDLL("kernel32", use_last_error=True)
            self._kernel32 = k
            k.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
            k.CreateJobObjectW.restype = wintypes.HANDLE
            k.SetInformationJobObject.argtypes = (
                wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
            k.SetInformationJobObject.restype = wintypes.BOOL
            k.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
            k.AssignProcessToJobObject.restype = wintypes.BOOL
            k.CloseHandle.argtypes = (wintypes.HANDLE,)

            handle = k.CreateJobObjectW(None, None)
            if not handle:
                raise ctypes.WinError(ctypes.get_last_error())
            self.handle = handle
            ext = EXTENDED_LIMIT()
            ext.BasicLimitInformation.LimitFlags = 0x00002000  # KILL_ON_JOB_CLOSE
            if not k.SetInformationJobObject(handle, 9, ctypes.byref(ext), ctypes.sizeof(ext)):
                raise ctypes.WinError(ctypes.get_last_error())
            cpu = CPU_RATE(0x1 | 0x4, int(cpu_limit * 100))  # ENABLE | HARD_CAP
            if not k.SetInformationJobObject(handle, 15, ctypes.byref(cpu), ctypes.sizeof(cpu)):
                raise ctypes.WinError(ctypes.get_last_error())
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"
            try:
                if self.handle:
                    self._kernel32.CloseHandle(self.handle)
            except Exception:
                pass
            self.handle = None

    @property
    def active(self) -> bool:
        return self.handle is not None

    def assign(self, p: subprocess.Popen) -> bool:
        if not self.active or os.name != "nt":
            return False
        try:
            import ctypes
            from ctypes import wintypes
            return bool(self._kernel32.AssignProcessToJobObject(
                self.handle, wintypes.HANDLE(int(p._handle))))
        except Exception as e:
            self.error = f"assign {type(e).__name__}: {e}"
            return False

    def close(self) -> None:
        if self.active:
            try:
                self._kernel32.CloseHandle(self.handle)
            except Exception:
                pass
            self.handle = None


_JOB: WindowsJob | None = None


def _ap_affinity_du_phong(p: subprocess.Popen) -> bool:
    if psutil is None:
        return False
    try:
        logical = psutil.cpu_count(logical=True) or os.cpu_count() or 1
        so_cpu = max(1, int(logical * CPU_TOI_DA / 100.0))
        psutil.Process(p.pid).cpu_affinity(list(range(so_cpu)))
        return True
    except (psutil.Error, OSError, ValueError):
        return False


def _ket_thuc_cay(p: subprocess.Popen) -> None:
    if p.poll() is not None:
        return
    if psutil is not None:
        try:
            root = psutil.Process(p.pid)
            ds = root.children(recursive=True)
            for con in reversed(ds):
                try:
                    con.terminate()
                except psutil.Error:
                    pass
            try:
                root.terminate()
            except psutil.Error:
                pass
            _, song = psutil.wait_procs(ds + [root], timeout=5)
            for con in song:
                try:
                    con.kill()
                except psutil.Error:
                    pass
            return
        except psutil.Error:
            pass
    try:
        p.kill()
    except OSError:
        pass


def _ket_thuc_tat_ca() -> None:
    with _PROCESS_LOCK:
        ds = list(_PROCESS_RUNNING.values())
    for p in ds:
        _ket_thuc_cay(p)


def _trich_json_cuoi(van_ban: str) -> dict | None:
    """Lay object JSON lon nhat trong stdout, chap nhan log truoc/sau JSON."""
    if not van_ban:
        return None
    try:
        x = json.loads(van_ban.strip())
        return x if isinstance(x, dict) else None
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    tot_nhat: tuple[int, dict] | None = None
    for i, ky_tu in enumerate(van_ban):
        if ky_tu != "{":
            continue
        try:
            x, end = decoder.raw_decode(van_ban[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(x, dict):
            do_dai = end
            if tot_nhat is None or do_dai > tot_nhat[0]:
                tot_nhat = (do_dai, x)
    return tot_nhat[1] if tot_nhat else None


def _duong_loi(x: Any, duong: str = "$", gioi_han: int = 12) -> list[str]:
    ra: list[str] = []
    if isinstance(x, dict):
        for k, v in x.items():
            p = f"{duong}.{k}"
            if k == "loi" and v not in (None, "", 0, False, [], {}):
                ra.append(f"{p}={str(v)[:100]}")
            elif k.endswith("_loi") and isinstance(v, (int, float)) and v > 0:
                ra.append(f"{p}={v}")
            if len(ra) >= gioi_han:
                return ra
            ra.extend(_duong_loi(v, p, gioi_han - len(ra)))
            if len(ra) >= gioi_han:
                return ra
    elif isinstance(x, list):
        for i, v in enumerate(x[:30]):
            ra.extend(_duong_loi(v, f"{duong}[{i}]", gioi_han - len(ra)))
            if len(ra) >= gioi_han:
                return ra
    return ra


def danh_gia_ket_qua(rc: int, payload: dict | None, nhip: dict | None,
                      nhip_moi: bool, qua_gio: bool = False) -> dict:
    """Phan loai health doc lap voi exit code de test va quan sat duoc."""
    fatal: list[str] = []
    suy_giam: list[str] = []
    bo_qua = ""
    if qua_gio:
        fatal.append("qua_gio")
    elif rc != 0:
        fatal.append(f"rc={rc}")
    if payload is None:
        suy_giam.append("stdout_khong_co_json")
    else:
        if payload.get("loi") not in (None, "", 0, False, [], {}):
            fatal.append(f"payload.loi={str(payload['loi'])[:120]}")
        if payload.get("bo_qua"):
            bo_qua = str(payload["bo_qua"])[:120]
        nested = [x for x in _duong_loi(payload) if not x.startswith("$.loi=")]
        suy_giam.extend(nested)
    if not nhip_moi:
        fatal.append("nhip_khong_cap_nhat")
    if nhip:
        trang_thai = str(nhip.get("trang_thai") or "").lower()
        if trang_thai in {"loi", "chet", "dung_vi_canary", "khong_san_sang"}:
            fatal.append(f"nhip.trang_thai={trang_thai}")
        chi_tiet = nhip.get("chi_tiet_obj") or {}
        if chi_tiet.get("loi") not in (None, "", 0, False, [], {}):
            fatal.append(f"nhip.loi={str(chi_tiet['loi'])[:120]}")
        if not bo_qua and chi_tiet.get("bo_qua"):
            bo_qua = str(chi_tiet["bo_qua"])[:120]
    fatal = list(dict.fromkeys(fatal))
    suy_giam = list(dict.fromkeys(suy_giam))
    if fatal:
        status = "error"
    elif suy_giam:
        status = "degraded"
    elif bo_qua:
        status = "skipped"
    else:
        status = "ok"
    return {"status": status, "ok": status != "error", "fatal": fatal,
            "degraded": suy_giam, "skip_reason": bo_qua}


def _doc_nhip_tru(ten: str) -> dict | None:
    row = SO.mot("SELECT tru,luc,trang_thai,chi_tiet FROM nhip WHERE tru=?", ten)
    if not row:
        return None
    ra = dict(row)
    try:
        ra["chi_tiet_obj"] = json.loads(ra.get("chi_tiet") or "{}")
    except json.JSONDecodeError:
        ra["chi_tiet_obj"] = {}
    return ra


def _nhip_da_moi(before: dict | None, after: dict | None, bat_dau: float) -> bool:
    if not after:
        return False
    if not before or any(after.get(k) != before.get(k)
                         for k in ("luc", "trang_thai", "chi_tiet")):
        return True
    try:
        luc = datetime.strptime(after["luc"], "%Y-%m-%d %H:%M:%S").timestamp()
        return luc >= bat_dau - 2.0
    except (KeyError, TypeError, ValueError):
        return False


def chay_tru(ten: str) -> dict:
    c = TRU[ten]
    bat_dau = time.time()
    nhip_cu = _doc_nhip_tru(ten)
    lenh = [PY, str(LAB / c["script"])]
    if ten == "QUANTLAB":
        lenh += ["--giay", str(c["ngan_sach"])]
    p: subprocess.Popen | None = None
    out, err, qua_gio = "", "", False
    rc = -1
    gioi_han = c["ngan_sach"] + 600
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        p = subprocess.Popen(
            lenh, cwd=str(LAB), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", creationflags=flags)
        with _PROCESS_LOCK:
            _PROCESS_RUNNING[p.pid] = p
        job_ok = bool(_JOB and _JOB.assign(p))
        affinity_ok = False if job_ok else _ap_affinity_du_phong(p)
        out, err = p.communicate(timeout=gioi_han)
        rc = int(p.returncode or 0)
    except subprocess.TimeoutExpired as e:
        qua_gio = True
        out = (e.stdout or "") if isinstance(e.stdout, str) else ""
        err = (e.stderr or "") if isinstance(e.stderr, str) else ""
        if p is not None:
            _ket_thuc_cay(p)
            try:
                them_out, them_err = p.communicate(timeout=5)
                out += them_out or ""
                err += them_err or ""
            except Exception:
                pass
        rc = -9
        job_ok = False
        affinity_ok = False
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        if p is not None:
            _ket_thuc_cay(p)
        rc = -1
        job_ok = False
        affinity_ok = False
    finally:
        if p is not None:
            with _PROCESS_LOCK:
                _PROCESS_RUNNING.pop(p.pid, None)

    nhip_moi = _doc_nhip_tru(ten)
    payload = _trich_json_cuoi(out)
    danh_gia = danh_gia_ket_qua(
        rc, payload, nhip_moi, _nhip_da_moi(nhip_cu, nhip_moi, bat_dau), qua_gio)
    dt = round(time.time() - bat_dau, 1)
    tail = (err or out or "").strip()[-800:]
    return {
        "tru": ten, "rc": rc, "giay": dt, **danh_gia,
        "stdout_tail": out.strip()[-500:], "stderr_tail": err.strip()[-500:],
        "tail": tail, "payload_keys": sorted(payload.keys()) if payload else [],
        "nhip": {k: nhip_moi.get(k) for k in ("luc", "trang_thai")}
                if nhip_moi else None,
        "resource_guard": "job" if job_ok else ("affinity" if affinity_ok else "none"),
    }


def _cpu_hien_tai() -> float:
    if psutil is None:
        return 0.0
    try:
        return round(float(psutil.cpu_percent(interval=None)), 1)
    except (psutil.Error, OSError, ValueError):
        return 0.0


def _xep_uu_tien(den_han: list[str], da_dung: dict[str, float], ke_tiep: dict[str, float],
                  now: float) -> list[str]:
    tong = sum(da_dung.values()) or 1.0
    ty_le = da_dung["kham_pha"] / tong
    nhom_can = "bao_tri" if ty_le > TY_LE_KHAM_PHA else "kham_pha"

    def khoa(ten: str) -> tuple:
        c = TRU[ten]
        dung_nhom = 0 if c["nhom"] == nhom_can else 1
        tre = max(0.0, now - ke_tiep[ten])
        return dung_nhom, -tre, c["uu_tien"], ten

    return sorted(den_han, key=khoa)


def _cho_rieng(ten: str) -> int:
    try:
        n = SO.mot("SELECT chi_tiet FROM nhip WHERE tru=?", ten)
    except Exception as e:
        ghi(f"khong doc duoc lich rieng {ten}: {type(e).__name__}: {e}")
        return 0
    if not n:
        return 0
    try:
        return max(0, int(json.loads(n["chi_tiet"] or "{}").get("cho_giay") or 0))
    except (TypeError, ValueError, json.JSONDecodeError):
        return 0


def _tong_quan_health(last: dict[str, dict]) -> str:
    if not last:
        return "starting"
    ds = [x.get("status") for x in last.values()]
    if "error" in ds:
        return "unhealthy"
    if "degraded" in ds:
        return "degraded"
    if not set(TRU).issubset(last):
        return "starting"
    return "healthy"


def _guard_mode(job: WindowsJob | None) -> str:
    if job and job.active:
        return "windows_job"
    if psutil is not None:
        return "process_affinity"
    return "none"


def _state_payload(status: str, ready: bool, running: dict[str, dict], pending: list[str],
                   last: dict[str, dict], cpu: float, backpressure: list[str],
                   job: WindowsJob | None) -> dict:
    now = time.time()
    return {
        "schema": 1,
        "instance_id": _INSTANCE_ID,
        "pid": os.getpid(),
        "process_created_epoch": _PROCESS_CREATED_EPOCH,
        "started_epoch": _STARTED_EPOCH,
        "updated_epoch": now,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "live": True,
        "ready": bool(ready),
        "health": _tong_quan_health(last),
        "cpu": {"current_percent": cpu, "hard_limit_percent": CPU_TOI_DA,
                "launch_limit_percent": CPU_NGUONG_KHOI_DONG,
                "guard": _guard_mode(job),
                "guard_error": job.error if job and job.error else ""},
        "workers": {"max": SO_WORKER, "running": {
            ten: {"lane": x["lane"], "started_epoch": x["started_epoch"],
                  "elapsed_seconds": round(now - x["started_epoch"], 1)}
            for ten, x in running.items()}, "pending": pending},
        "backpressure": backpressure,
        "last_results": last,
    }


def _cham_control(payload: dict) -> None:
    _ghi_json_nguyen_tu(CONTROL, payload)
    _ghi_json_nguyen_tu(KHOA, payload)


def trang_thai() -> dict:
    lease = _doc_lease()
    tuoi = _lease_tuoi(lease)
    live = bool(lease and tuoi < KHOA_CU_GIAY and _pid_song(
        lease.get("pid"), lease.get("process_created_epoch")))
    tuoi_out = round(tuoi, 1) if math.isfinite(tuoi) else None
    vh = {"luc": SO.bay_gio(), "nhip": SO.doc_nhip(), "viec": SO.dem_viec(),
          "control_plane": {**lease, "live": live, "lease_age_seconds": tuoi_out}}
    vh["tai_lieu"] = SO.mot("SELECT COUNT(*) n FROM tai_lieu")["n"]
    vh["gia_thuyet"] = SO.mot("SELECT COUNT(*) n FROM gia_thuyet")["n"]
    vh["ket_qua"] = SO.mot("SELECT COUNT(*) n FROM ket_qua")["n"]
    vh["van_de_mo"] = len(SO.van_de_mo())
    vh["dang_chay"] = live
    return vh


def probe(loai: str) -> int:
    lease = _doc_lease()
    tuoi = _lease_tuoi(lease)
    live = bool(lease and tuoi < KHOA_CU_GIAY and _pid_song(
        lease.get("pid"), lease.get("process_created_epoch")))
    ready = bool(live and lease.get("ready"))
    health = str(lease.get("health") or "unknown") if live else "down"
    out = {"probe": loai, "live": live, "ready": ready, "health": health,
           "lease_age_seconds": round(tuoi, 1) if math.isfinite(tuoi) else None}
    print(json.dumps(out, ensure_ascii=False))
    if loai == "live":
        return 0 if live else 1
    if loai == "ready":
        return 0 if ready else 1
    if health == "healthy":
        return 0
    return 2 if health == "degraded" else 1


def _xu_ly_ket_qua(r: dict, fail: dict[str, int], da_dung: dict[str, float]) -> bool:
    ten = r["tru"]
    da_dung[TRU[ten]["nhom"]] += r["giay"]
    status = r["status"]
    ghi(f"{ten:<9} {status:<9} {r['giay']:>6.1f}s guard={r['resource_guard']}")
    try:
        if status == "error":
            fail[ten] += 1
            ghi(f"          | {'; '.join(r['fatal'])[:300]} | {r['tail'][:300]}")
            SO.bao_van_de(f"tru_loi_{ten}", "VUA",
                          f"Tru {ten} khong lanh manh (lan {fail[ten]} lien tiep)", r)
        else:
            fail[ten] = 0
            SO.dong_van_de(f"tru_loi_{ten}", "control plane thay ket qua hop le")
        if status == "degraded":
            SO.bao_van_de(f"tru_suy_giam_{ten}", "NHE",
                          f"Tru {ten} chay xong nhung co loi thanh phan", r)
        elif status in {"ok", "skipped"}:
            SO.dong_van_de(f"tru_suy_giam_{ten}", "khong con loi thanh phan")
        return True
    except Exception as e:
        ghi(f"ledger khong nhan duoc ket qua health {ten}: {type(e).__name__}: {e}")
        return False


def main() -> int:
    global _JOB
    ap = argparse.ArgumentParser()
    ap.add_argument("--phut", type=float, default=0, help="0 = chay mai")
    ap.add_argument("--trang-thai", action="store_true")
    ap.add_argument("--probe", choices=("live", "ready", "health"))
    a = ap.parse_args()

    if a.probe:
        return probe(a.probe)
    SO.khoi_tao()
    if a.trang_thai:
        print(json.dumps(trang_thai(), ensure_ascii=False, indent=1, default=str))
        return 0
    if not _khoa():
        ghi("da co mot dieu phoi khac dang chay - thoat.")
        return 3
    if DUNG.exists():
        DUNG.unlink()

    _JOB = WindowsJob(CPU_TOI_DA)
    guard_san_sang = _guard_mode(_JOB) != "none"
    if psutil is not None:
        psutil.cpu_percent(interval=None)
    n_treo = SO.don_viec_treo()
    mat = ghi_gian_doan()
    thuc = giu_may_thuc()
    ghi(f"=== THE BRAIN control plane. pid={os.getpid()} workers={SO_WORKER} "
        f"cpu<={CPU_TOI_DA:.0f}% job={'OK' if _JOB.active else 'FALLBACK'} | "
        f"don {n_treo} viec treo"
        + (f" | gian doan {mat:.1f} gio (khong ro nguyen nhan)" if mat >= 0.5 else "")
        + f" | giu may thuc: {'OK' if thuc else 'KHONG'} ===")
    SO.ghi_su_kien("DIEU_PHOI", "khoi_dong", {
        "pid": os.getpid(), "instance_id": _INSTANCE_ID, "workers": SO_WORKER,
        "cpu_limit": CPU_TOI_DA, "job_object": _JOB.active,
        "job_error": _JOB.error, "viec_treo_da_don": n_treo,
        "gian_doan_gio": round(mat, 2), "giu_may_thuc": thuc})
    if guard_san_sang:
        SO.dong_van_de("dieu_phoi_khong_cpu_guard", "da co CPU guard")
    else:
        SO.bao_van_de("dieu_phoi_khong_cpu_guard", "NANG",
                      "Khong co Windows Job Object hay psutil affinity; dung nhan viec", {})

    deadline = time.time() + a.phut * 60 if a.phut else None
    ke_tiep = {ten: 0.0 for ten in TRU}
    da_dung = {"kham_pha": 0.0, "bao_tri": 0.0}
    fail = {ten: 0 for ten in TRU}
    last: dict[str, dict] = {}
    running: dict[str, dict] = {}
    pool = ThreadPoolExecutor(max_workers=SO_WORKER, thread_name_prefix="tru")
    stopping = False
    db_ok = True
    last_nhip = 0.0

    try:
        while True:
            now = time.time()
            for ten, info in list(running.items()):
                future: Future = info["future"]
                if not future.done():
                    continue
                try:
                    r = future.result()
                except Exception as e:
                    r = {"tru": ten, "rc": -1, "giay": round(now - info["started_epoch"], 1),
                         "status": "error", "ok": False,
                         "fatal": [f"worker_exception={type(e).__name__}: {e}"],
                         "degraded": [], "skip_reason": "", "tail": str(e),
                         "stdout_tail": "", "stderr_tail": str(e), "payload_keys": [],
                         "nhip": None, "resource_guard": "none"}
                running.pop(ten, None)
                if not _xu_ly_ket_qua(r, fail, da_dung):
                    db_ok = False
                last[ten] = {k: r[k] for k in (
                    "status", "rc", "giay", "fatal", "degraded", "skip_reason",
                    "nhip", "resource_guard", "stdout_tail", "stderr_tail")}
                co_so = max(TRU[ten]["chu_ky"], _cho_rieng(ten))
                cooldown = co_so * min(fail[ten], 4)
                ke_tiep[ten] = time.time() + co_so + cooldown

            if DUNG.exists() or (deadline and now >= deadline):
                if not stopping:
                    ghi("nhan yeu cau dung - khong nhan them viec, doi cac tru hien tai.")
                stopping = True
            if stopping and not running:
                break

            cpu = _cpu_hien_tai()
            den_han = [ten for ten, moc in ke_tiep.items()
                       if now >= moc and ten not in running]
            backpressure: list[str] = []
            if not stopping and den_han:
                con_slot = SO_WORKER - len(running)
                lan_dang = {lan: 0 for lan in LAN_GIOI_HAN}
                for info in running.values():
                    lan_dang[info["lane"]] = lan_dang.get(info["lane"], 0) + 1
                if con_slot <= 0:
                    backpressure.append("worker_pool_day")
                elif not guard_san_sang:
                    backpressure.append("cpu_guard_khong_san_sang")
                elif not db_ok:
                    backpressure.append("ledger_khong_san_sang")
                elif cpu >= CPU_NGUONG_KHOI_DONG:
                    backpressure.append(
                        f"cpu_{cpu:.1f}_vuot_nguong_khoi_dong_{CPU_NGUONG_KHOI_DONG:.1f}")
                else:
                    for ten in _xep_uu_tien(den_han, da_dung, ke_tiep, now):
                        if con_slot <= 0:
                            backpressure.append("worker_pool_day")
                            break
                        lan = TRU[ten]["lan"]
                        if lan_dang.get(lan, 0) >= LAN_GIOI_HAN.get(lan, 1):
                            backpressure.append(f"lane_{lan}_day:{ten}")
                            continue
                        future = pool.submit(chay_tru, ten)
                        running[ten] = {"future": future, "started_epoch": time.time(),
                                        "lane": lan}
                        lan_dang[lan] = lan_dang.get(lan, 0) + 1
                        con_slot -= 1
                        ghi(f"{ten:<9} bat_dau   lane={lan}")

            pending = [ten for ten, moc in ke_tiep.items()
                       if now >= moc and ten not in running]
            payload = _state_payload(
                "stopping" if stopping else "running",
                not stopping and guard_san_sang and db_ok,
                running, pending, last, cpu, list(dict.fromkeys(backpressure)), _JOB)
            _cham_control(payload)
            if now - last_nhip >= NHIP_DIEU_PHOI_GIAY:
                try:
                    SO.nhip_tim("DIEU_PHOI", "dung" if stopping else "song", {
                        "ready": not stopping and guard_san_sang and db_ok,
                        "health": payload["health"], "cpu_percent": cpu,
                        "running": list(running), "pending": pending,
                        "backpressure": payload["backpressure"],
                        "da_dung": {k: round(v) for k, v in da_dung.items()}})
                    db_ok = True
                except Exception as e:
                    db_ok = False
                    ghi(f"ledger heartbeat loi: {type(e).__name__}: {e}")
                last_nhip = now
            time.sleep(VONG_DIEU_PHOI_GIAY)
    except KeyboardInterrupt:
        ghi("CTRL-C - dung va ket thuc cay tien trinh con.")
        _ket_thuc_tat_ca()
    finally:
        _ket_thuc_tat_ca()
        pool.shutdown(wait=True, cancel_futures=True)
        try:
            payload = _state_payload("stopped", False, {}, [], last,
                                     _cpu_hien_tai(), [], _JOB)
            payload["live"] = False
            _ghi_json_nguyen_tu(CONTROL, payload)
        except Exception:
            pass
        try:
            SO.ghi_su_kien("DIEU_PHOI", "dung", {"da_dung_giay": da_dung,
                                                   "instance_id": _INSTANCE_ID})
        except Exception as e:
            ghi(f"khong ghi duoc su kien dung: {type(e).__name__}: {e}")
        finally:
            tha_may_ngu()
            if _JOB:
                _JOB.close()
            _tha_khoa()
            ghi("=== dung dieu phoi ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
