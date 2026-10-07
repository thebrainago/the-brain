# -*- coding: utf-8 -*-
"""may_nha.py - QUET + DO + KET LUAN may nha: biet may CO GI, DANG LAM GI, GIOI HAN o dau, can BAO GI.

## Vi sao (03/10/2026)

Chu du an: *"lo toi uu khau giam sat may nha, phan claudecode tren may nha can quet may va biet bao cao gi cho hop li.
May nha 10 nhan 20 luong nhung ram 32GB chi co 1 thanh nen khong dung het toc luc... Do dac va tinh toan ky toc do va
nguong gioi han phan cung toi da co the khai thac (toi van cho hoat dong 75-80% cpu)... can tao them tk mt5 thi bao toi
toi da bao nhieu."*

Truoc do he co cac manh roi rac: `do_tai_nguyen` (tab Chrome, RAM), `ngan_sach` (cho phep viec theo RAM trong va so
tien trinh python), `dieu_toc` (CPU), `slot_tester` (lan MT5), nhip tim `viec/may/<ten>.json` (song/chet). KHONG ai tra loi:
  (1) may nay GIOI HAN o dau - CPU, bang thong RAM, dung luong cam ket (RAM+pagefile), hay dia?
  (2) o 75-80% CPU ta duoc bao nhieu phan tram toc do toi da?
  (3) nen chay toi da bao nhieu viec song song MOI LOAI (viec nhe nam trong cache vs viec doc nhieu bo nho)?
  (4) can bao gi cho chu du an: DEN XANH thi im lang, VANG/DO thi mot dong ly do + viec chu du an can lam.

## Bon thu duoc do (khong doan)

  quet      phan cung that: CPU, thanh RAM (loai/toc do/ECC/khe trong), o dia (SSD/HDD), pagefile, ke hoach dien, MT5
  mau       mot mau tai nguyen: CPU, RAM trong, DUNG LUONG CAM KET (commit), pagefile, dia, tien trinh MT5/python
  do        DO CO GIAN: cung mot viec chay 1,2,4...N tien trinh -> toc do tong; ba loai viec:
              cpu_nho   vong lap Python nam gon trong cache (kieu quet D1: tuyet doi doc lap)
              luoi      CHINH engine luoi (`luoi_nhan`: nhan C neu co, khong thi Python)
              bang_thong  doc/ghi mang lon (kieu quet M1 nhieu nam, agent MT5) -> cham tran KENH RAM
              dia       ghi tuan tu + ghi ngau nhien co fsync tren tung o
  giam_sat  lap `mau` nhieu phut -> phan bo CPU (bao nhieu % thoi gian trong dai 75-80%), RAM/commit thap nhat, dia

Moi con so deu an danh (khong so serial, ten nguoi dung, IP) vi repo la PUBLIC.

## Nguyen tac

  - CHI DOC tru khi chay `do` (tao file tam trong thu muc tam cua tung o, xoa ngay). KHONG doi cai dat Windows nao:
    moi de xuat (pagefile, ke hoach dien, tran CPU) chi IN RA kem lenh; chu du an quyet.
  - Khong do duoc -> `None` + ly do, KHONG tra 0 (0 la mot con so that: "0 khe trong").
  - Windows la dich that (PowerShell/CIM, ctypes); Linux chi la du phong de chay thu trong cloud.
    Moi lenh he thong di qua MOT `runner` co the thay bang gia lap (test_may_nha.py).
  - `do` chi chay khi may RANH (CPU nen < 35%): do luc may dang ban cho so lieu dep nhung SAI. Muon do dang ban: `--ep`,
    ket qua tu gan `nhieu_nen=True` va khong duoc dung de chot so luong.
"""
from __future__ import annotations

import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))

NHAT_KY = GOC / "nhat_ky" / "may_nha_mau.jsonl"     # cuc bo, bi gitignore (khong dua vao `reports/`: `tep_moi` se mang theo)
BAO_CAO = GOC / "reports"

LA_WINDOWS = os.name == "nt"

# ---- cac nguong (mot cho, doc bang mat thuong) ----------------------------------------------------------------
DAI_CPU = (75.0, 80.0)            # chu du an: "van cho hoat dong 75-80% cpu"
NGUONG = {
    "dia_do_gb": 5.0,             # o he thong con it hon -> DO  (13/09: con 233 MB, ENOMEM)
    "dia_vang_gb": 20.0,
    "commit_do_gb": 3.0,          # cam ket con lai (RAM + pagefile) it hon -> DO  (13/09: ENOMEM voi 17 GB RAM trong)
    "commit_vang_gb": 8.0,
    "ram_do_gb": 1.5,             # RAM vat ly trong
    "ram_vang_gb": 3.0,           # = ngan_sach.RAM_TOI_THIEU_GB
    "chuan_ghi_tre_ms_hdd": 4.0,  # fsync 4 KiB cham hon muc nay -> kieu HDD
    "ngau_nhien_iops_hdd": 500,
    "ngau_nhien_iops_nhanh": 5000,
}
#: "Bao hoa" = tu n nay tro di, them tien trinh nao nua cung chi them < 10% tong toc do
DOC_BAO_HOA = 0.10
#: Cac kernel do co gian (thu tu chay): xem docstring dau file
LOAI_DO = ("cpu_nho", "luoi", "luoi_dai", "bang_thong", "dia")
#: Chuoi `luoi_dai`: 1 trieu nen (5 mang x 8 MB = 40 MB/tien trinh, lon hon cache) - nhu quet M1 nhieu nam
SO_BAR_DAI = 1_000_000
#: GIA DINH (chua do duoc tren MT5 that): mot agent tester chay mo hinh tick doc ~2 GB/s bo nho. Dung de doi
#: "bang thong do duoc" thanh "bao nhieu agent nang nuoi noi". Do that: chay 1 agent roi doc cpu/RAM, thay con so nay.
BANG_THONG_MOI_AGENT_GBS = 2.0
#: Chi phi Windows + he thong + chu du an dung may: RAM chua cho MT5 / viec lab
RAM_DE_DANH_GB = 6.0
#: GIA DINH (khong do duoc luc khong co agent MT5 chay): RAM moi agent tester (GB). Do that thi thay.
RAM_AGENT_GB = {"model_1": 1.0, "model_0_4": 2.5}

GUID_DIEN = {
    "381b4222-f694-41f0-9685-ff5bb260df2e": "Balanced",
    "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c": "High performance",
    "a1841308-3541-4fab-bc81-f71556f20b4a": "Power saver",
    "e9a42b02-d5df-448d-aa00-03f14749eb61": "Ultimate Performance",
}
LOAI_RAM = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 34: "DDR5"}      # SMBIOS Memory Device Type
MA_LOI_ECC = {3: "khong", 4: "parity", 5: "ECC 1 bit", 6: "ECC nhieu bit", 7: "CRC"}


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _gb(n) -> float | None:
    try:
        return round(float(n) / 2 ** 30, 2)
    except (TypeError, ValueError):
        return None


def _ds(x) -> list:
    """PowerShell `ConvertTo-Json` tra DOI TUONG khi chi co 1 phan tu, MANG khi nhieu: gop ve list."""
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _so(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


# ================================================================ RUNNER (dau vao he thong, thay duoc khi test)
def chay_lenh(args: list[str], han: float = 40.0) -> tuple[str | None, str | None]:
    """(stdout, loi). Khong nem. Loi = ten loi ngan hoac stderr cuoi."""
    try:
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=han)
    except FileNotFoundError:
        return None, "khong co lenh %s" % args[0]
    except subprocess.TimeoutExpired:
        return None, "qua han %.0fs" % han
    except OSError as e:
        return None, "%s: %s" % (type(e).__name__, e)
    if r.returncode != 0 and not r.stdout.strip():
        return None, (r.stderr or "ma thoat %d" % r.returncode).strip().splitlines()[-1][:200]
    return r.stdout, None


#: MOT lan goi PowerShell lay het (moi lan khoi dong PowerShell ~0,5-1 s: gop de quet ~3 s thay vi ~12 s).
#: `SilentlyContinue`: lop WMI nao vang (vd MSAcpi_ThermalZoneTemperature) -> khoa do thanh null, khong lam hong ca bo.
_PS_QUET = r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$ErrorActionPreference='SilentlyContinue'
$o=[ordered]@{}
$o.cpu=@(Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,CurrentClockSpeed,L2CacheSize,L3CacheSize,SocketDesignation)
$o.ram_thanh=@(Get-CimInstance Win32_PhysicalMemory | Select-Object BankLabel,DeviceLocator,Capacity,Speed,ConfiguredClockSpeed,SMBIOSMemoryType,FormFactor,Manufacturer,PartNumber,DataWidth,TotalWidth,TypeDetail)
$o.ram_mang=@(Get-CimInstance Win32_PhysicalMemoryArray | Select-Object MemoryDevices,MaxCapacity,MaxCapacityEx,MemoryErrorCorrection)
$o.bo_mach=@(Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer,Product)
$o.bios=@(Get-CimInstance Win32_BIOS | Select-Object Manufacturer,SMBIOSBIOSVersion,@{n='Ngay';e={$_.ReleaseDate.ToString('yyyy-MM-dd')}})
$o.dia_vat_ly=@(Get-PhysicalDisk | Select-Object FriendlyName,MediaType,BusType,Size,HealthStatus,SpindleSpeed)
$o.o_dia=@(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID,Size,FreeSpace,FileSystem)
$o.pagefile_dung=@(Get-CimInstance Win32_PageFileUsage | Select-Object Name,AllocatedBaseSize,CurrentUsage,PeakUsage)
$o.pagefile_cai=@(Get-CimInstance Win32_PageFileSetting | Select-Object Name,InitialSize,MaximumSize)
$o.he_thong=@(Get-CimInstance Win32_ComputerSystem | Select-Object AutomaticManagedPagefile,TotalPhysicalMemory,NumberOfProcessors,NumberOfLogicalProcessors)
$o.he_dieu_hanh=@(Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture)
$o.gpu=@(Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion,CurrentHorizontalResolution)
$o.defender_loai_tru=@((Get-MpPreference).ExclusionPath).Count
$o.opencl=[bool](Test-Path "$env:windir\System32\OpenCL.dll")
$o.cuda=[bool](Test-Path "$env:windir\System32\nvcuda.dll")
$o.nhiet=@(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature | Select-Object CurrentTemperature)
$o.dien=(powercfg /getactivescheme | Out-String)
$o | ConvertTo-Json -Depth 4 -Compress
"""

#: Do HIEU NANG tuc thoi (cho `giam_sat`): lop WMI trung tinh ngon ngu (khong phu thuoc Windows tieng Viet/Anh nhu Get-Counter)
_PS_MAU = r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$ErrorActionPreference='SilentlyContinue'
$o=[ordered]@{}
$o.bo_nho=@(Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory | Select-Object CommittedBytes,CommitLimit,AvailableBytes,PagesPersec,PageReadsPersec,PageFaultsPersec)
$o.dia=@(Get-CimInstance Win32_PerfFormattedData_PerfDisk_PhysicalDisk | Select-Object Name,PercentDiskTime,AvgDiskQueueLength,DiskReadBytesPersec,DiskWriteBytesPersec)
$o | ConvertTo-Json -Depth 3 -Compress
"""


def chay_ps(script: str, runner=None, han: float = 60.0) -> tuple[dict | None, str | None]:
    """Chay mot doan PowerShell tra JSON. (dict, loi)."""
    run = runner or chay_lenh
    ra, loi = run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script], han)
    if ra is None:
        return None, loi
    try:
        i = ra.index("{")
        d = json.loads(ra[i:])
        return (d if isinstance(d, dict) else None), None
    except ValueError as e:
        return None, "JSON hong: %s" % e


# ================================================================ AN DANH
def _nguoi_dung() -> list[str]:
    ten = set()
    for k in ("USERNAME", "USER", "LOGNAME"):
        if os.environ.get(k):
            ten.add(os.environ[k])
    try:
        ten.add(Path.home().name)
    except (RuntimeError, OSError):
        pass
    ten.add(platform.node())
    return sorted((t for t in ten if t and len(t) >= 3), key=len, reverse=True)


def an_danh(x, ten: list[str] | None = None):
    """De quy: thay ten nguoi dung / ten may bang <user>/<may>, bo khoa kieu serial. Repo la PUBLIC."""
    ten = _nguoi_dung() if ten is None else ten
    if isinstance(x, dict):
        return {k: an_danh(v, ten) for k, v in x.items() if "serial" not in str(k).lower()}
    if isinstance(x, list):
        return [an_danh(v, ten) for v in x]
    if isinstance(x, str):
        for t in ten:
            x = re.sub(re.escape(t), "<user>", x, flags=re.I)
        return x
    return x


# ================================================================ QUET PHAN CUNG
def _doc_cpu(ps: dict | None) -> dict:
    d = {"ten": None, "so_o_cam": None, "nhan_vat_ly": None, "luong": None, "mhz_toi_da": None, "mhz_hien_tai": None,
         "l3_mb": None, "nguon": "psutil"}
    ds = _ds((ps or {}).get("cpu"))
    if ds:
        d["nguon"] = "wmi"
        d["ten"] = " ".join(str(ds[0].get("Name") or "").split()) or None
        d["so_o_cam"] = len(ds)
        d["nhan_vat_ly"] = sum(_so(x.get("NumberOfCores")) or 0 for x in ds) or None
        d["luong"] = sum(_so(x.get("NumberOfLogicalProcessors")) or 0 for x in ds) or None
        d["mhz_toi_da"] = _so(ds[0].get("MaxClockSpeed"))
        d["mhz_hien_tai"] = _so(ds[0].get("CurrentClockSpeed"))
        l3 = _so(ds[0].get("L3CacheSize"))
        d["l3_mb"] = round(l3 / 1024, 1) if l3 else None
    try:
        import psutil
        d["nhan_vat_ly"] = d["nhan_vat_ly"] or psutil.cpu_count(logical=False)
        d["luong"] = d["luong"] or psutil.cpu_count(logical=True)
        f = psutil.cpu_freq()
        if f:
            d["mhz_toi_da"] = d["mhz_toi_da"] or (int(f.max) if f.max else None)
            d["mhz_hien_tai"] = d["mhz_hien_tai"] or int(f.current)
    except Exception:                                                               # noqa: BLE001
        d["nhan_vat_ly"] = d["nhan_vat_ly"] or None
        d["luong"] = d["luong"] or (os.cpu_count() or None)
    if not d["ten"]:
        d["ten"] = platform.processor() or None
    return d


def _kenh_tu_ten_khe(loc: str, bank: str = "") -> str | None:
    """Ten kenh nho tu `DeviceLocator`: DIMM_A1 / DIMMA1 / P0_DIMMA1 / ChannelA-DIMM0 ... None neu khong doan duoc."""
    s = ("%s %s" % (loc or "", bank or "")).upper()
    for mau in (r"CHANNEL[\s_-]*([A-H])\b", r"DIMM[\s_-]*([A-H])[\s_-]?\d", r"(?:^|[\s_-])([A-H])[\s_-]?\d(?:$|\s)"):
        m = re.search(mau, s)
        if m:
            return m.group(1)
    return None


def _kenh_toi_da(ten: str | None, so_o_cam: int | None = 1) -> int:
    """So kenh RAM toi da cua nen tang, doan tu ten CPU: Xeon E5/E7 = 4 moi o cam, Xeon E3 / Core / Ryzen = 2, Xeon Scalable = 6,
    EPYC = 8. Khong nhan ra -> 4 (nen tang may nha da biet: Xeon E5 v4). Chi de tinh 'nang RAM duoc toi dau', khong de chan gi."""
    s = (ten or "").upper()
    if "EPYC" in s:
        moi = 8
    elif re.search(r"XEON.*(BRONZE|SILVER|GOLD|PLATINUM)", s):
        moi = 6
    elif re.search(r"\bE3-", s) or re.search(r"CORE|RYZEN|PENTIUM|CELERON|ATHLON", s):
        moi = 2
    else:
        moi = 4
    return moi * max(1, so_o_cam or 1)


def _doc_ram(ps: dict | None, tong_vat_ly_gb: float | None) -> dict:
    thanh = []
    for t in _ds((ps or {}).get("ram_thanh")):
        td = _so(t.get("TypeDetail")) or 0
        dw, tw = _so(t.get("DataWidth")), _so(t.get("TotalWidth"))
        thanh.append({
            "khe": " ".join(str(t.get("DeviceLocator") or "").split()) or None,
            "kenh": _kenh_tu_ten_khe(str(t.get("DeviceLocator") or ""), str(t.get("BankLabel") or "")),
            "gb": _gb(t.get("Capacity")),
            "mt_s": _so(t.get("ConfiguredClockSpeed")) or _so(t.get("Speed")),
            "mt_s_toi_da": _so(t.get("Speed")),
            "loai": LOAI_RAM.get(_so(t.get("SMBIOSMemoryType")), "SMBIOS %s" % t.get("SMBIOSMemoryType")),
            "ecc": (tw > dw) if (tw and dw) else None,
            "registered": bool(td & 8192),
            "unbuffered": bool(td & 16384),
            "lrdimm": bool(td & 32768),
            "hang": " ".join(str(t.get("Manufacturer") or "").split())[:20] or None,
            "ma_hang": " ".join(str(t.get("PartNumber") or "").split())[:32] or None,
        })
    mang = _ds((ps or {}).get("ram_mang"))
    khe_tong = sum(_so(m.get("MemoryDevices")) or 0 for m in mang) or None
    toi_da = None
    for m in mang:
        v = _so(m.get("MaxCapacityEx")) or _so(m.get("MaxCapacity")) or 0                  # CA HAI deu tinh bang KB (Ex dung khi > 2 TB)
        toi_da = (toi_da or 0) + v
    toi_da_gb = round(toi_da / 2 ** 20, 0) if toi_da else None                              # KB -> GB
    kenh = {t["kenh"] for t in thanh if t["kenh"]}
    d = {"tong_gb": round(sum(t["gb"] or 0 for t in thanh), 1) or tong_vat_ly_gb, "thanh": thanh,
         "so_thanh": len(thanh) or None, "khe_tong": khe_tong,
         "khe_trong": (khe_tong - len(thanh)) if (khe_tong is not None and thanh) else None,
         "toi_da_ho_tro_gb": toi_da_gb,
         "kenh_dang_dung": (len(kenh) if kenh else (len(thanh) or None)),
         "kenh_suy_tu_ten_khe": bool(kenh)}
    mhz = [t["mt_s"] for t in thanh if t["mt_s"]]
    d["mt_s"] = min(mhz) if mhz else None
    # Ly thuyet: moi kenh 64 bit = 8 byte moi chu ky -> MT/s * 8 / 1000 GB/s moi kenh
    d["bang_thong_ly_thuyet_gbs"] = round(d["kenh_dang_dung"] * d["mt_s"] * 8 / 1000, 1) if (d["kenh_dang_dung"] and d["mt_s"]) else None
    d["ly_thuyet_neu_du_kenh_gbs"] = None
    return d


def _doc_dia(ps: dict | None) -> dict:
    vat_ly = [{"ten": " ".join(str(x.get("FriendlyName") or "").split())[:40],
               "loai": {3: "HDD", 4: "SSD", 5: "SCM"}.get(_so(x.get("MediaType")), x.get("MediaType") or None),
               "bus": {11: "SATA", 17: "NVMe", 7: "USB", 8: "RAID", 10: "SAS"}.get(_so(x.get("BusType")), x.get("BusType")),
               "gb": round((_so(x.get("Size")) or 0) / 1e9, 0) or None,
               "suc_khoe": x.get("HealthStatus"), "vong_phut": _so(x.get("SpindleSpeed"))}
              for x in _ds((ps or {}).get("dia_vat_ly"))]
    o = [{"o": x.get("DeviceID"), "tong_gb": _gb(x.get("Size")), "trong_gb": _gb(x.get("FreeSpace")),
          "fs": x.get("FileSystem")} for x in _ds((ps or {}).get("o_dia"))]
    if not o:                                                                       # du phong psutil (Linux / PS hong)
        try:
            import psutil
            for p in psutil.disk_partitions(all=False):
                if p.fstype and "cdrom" not in (p.opts or ""):
                    try:
                        u = psutil.disk_usage(p.mountpoint)
                    except OSError:
                        continue
                    o.append({"o": p.mountpoint, "tong_gb": _gb(u.total), "trong_gb": _gb(u.free), "fs": p.fstype})
        except Exception:                                                           # noqa: BLE001
            pass
    return {"vat_ly": vat_ly, "o": o}


def _doc_pagefile(ps: dict | None) -> dict:
    dung = [{"o": str(x.get("Name") or "")[:2].upper(), "cap_phat_mb": _so(x.get("AllocatedBaseSize")),
             "dang_dung_mb": _so(x.get("CurrentUsage")), "dinh_mb": _so(x.get("PeakUsage"))}
            for x in _ds((ps or {}).get("pagefile_dung"))]
    cai = [{"o": str(x.get("Name") or "")[:2].upper(), "dau_mb": _so(x.get("InitialSize")),
            "toi_da_mb": _so(x.get("MaximumSize"))} for x in _ds((ps or {}).get("pagefile_cai"))]
    hs = _ds((ps or {}).get("he_thong"))
    tu_dong = hs[0].get("AutomaticManagedPagefile") if hs else None
    return {"dang_dung": dung, "cai_dat_tay": cai, "he_thong_tu_quan_ly": tu_dong,
            "tong_cap_phat_gb": round(sum(x["cap_phat_mb"] or 0 for x in dung) / 1024, 1) if dung else None}


def _doc_dien(ps: dict | None) -> dict:
    s = str((ps or {}).get("dien") or "")
    m = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", s)
    guid = m.group(1).lower() if m else None
    return {"guid": guid, "ten": GUID_DIEN.get(guid) if guid else None,
            "can_chuyen_high_performance": bool(guid) and guid in (
                "381b4222-f694-41f0-9685-ff5bb260df2e", "a1841308-3541-4fab-bc81-f71556f20b4a")}


def _quet_linux_cpu_ten() -> str | None:
    try:
        for dong in Path("/proc/cpuinfo").read_text(errors="replace").splitlines():
            if dong.lower().startswith("model name"):
                return " ".join(dong.split(":", 1)[1].split())
    except OSError:
        pass
    return None


def quet_mt5(thu_muc_nhat_ky: Path | None = None, han_giay: float = 6.0) -> dict:
    """Ban cai MT5, thu muc du lieu terminal, tien trinh dang chay. Khong mo, khong sua gi."""
    d = {"ban_cai": [], "thu_muc_du_lieu": [], "dang_chay": {"terminal64": 0, "metatester64": 0},
         "agent_rss_gb_tb": None}
    try:
        import psutil
        agents = []
        for p in psutil.process_iter(["name", "memory_info"]):
            ten = (p.info.get("name") or "").lower()
            if ten == "terminal64.exe":
                d["dang_chay"]["terminal64"] += 1
            elif ten == "metatester64.exe":
                d["dang_chay"]["metatester64"] += 1
                try:
                    agents.append(p.info["memory_info"].rss / 2 ** 30)
                except Exception:                                                   # noqa: BLE001
                    pass
        if agents:
            d["agent_rss_gb_tb"] = round(sum(agents) / len(agents), 2)
    except Exception:                                                               # noqa: BLE001
        pass
    if not LA_WINDOWS:
        return d
    goc_cai = []
    for pf in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if pf:
            goc_cai.append(Path(pf))
    try:
        import psutil
        for p in psutil.disk_partitions(all=False):
            goc_cai.append(Path(p.mountpoint))
    except Exception:                                                               # noqa: BLE001
        pass
    thay = set()
    for g in goc_cai:
        try:
            for q in list(g.glob("*/terminal64.exe")) + list(g.glob("*/*/terminal64.exe")):
                thay.add(q.parent)
        except OSError:
            continue
    d["ban_cai"] = sorted(str(an_danh(str(x))) for x in thay)[:20]
    ap = os.environ.get("APPDATA")
    if ap:
        goc_dl = Path(ap) / "MetaQuotes" / "Terminal"
        try:
            for x in sorted(goc_dl.iterdir()) if goc_dl.exists() else []:
                if not x.is_dir() or len(x.name) < 16:
                    continue
                bases = x / "bases"
                server = []
                try:
                    server = [s.name for s in bases.iterdir() if s.is_dir() and s.name not in ("Default", "Custom")]
                except OSError:
                    pass
                d["thu_muc_du_lieu"].append({"id": x.name[:6], "may_chu_lich_su": server[:6],
                                              "gb_bases": _kich_thuoc_gb(bases, han_giay),
                                              "gb_tester": _kich_thuoc_gb(x / "Tester", han_giay)})
        except OSError:
            pass
    return d


def _kich_thuoc_gb(p: Path, han_giay: float = 6.0) -> float | None:
    """Tong dung luong mot thu muc, co HAN GIO (thu muc cache tester co the co hang trieu file). None neu qua han / khong co."""
    if not p.exists():
        return None
    het, tong, cho = time.time() + han_giay, 0, [str(p)]
    while cho:
        if time.time() > het:
            return None
        try:
            with os.scandir(cho.pop()) as it:
                for e in it:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            cho.append(e.path)
                        else:
                            tong += e.stat(follow_symlinks=False).st_size
                    except OSError:
                        continue
        except OSError:
            continue
    return round(tong / 2 ** 30, 2)


def _nhan_c() -> dict:
    try:
        from nhan import luoi_nhan as LN
        t = LN.trang_thai()
        return {"san_sang": bool(t.get("san_sang")), "trinh_bien": t.get("trinh_bien"), "ly_do": str(t.get("ly_do"))[:160],
                "che_do": t.get("che_do")}
    except Exception as e:                                                          # noqa: BLE001
        return {"san_sang": False, "trinh_bien": None, "ly_do": "%s: %s" % (type(e).__name__, str(e)[:100]), "che_do": None}


def quet(runner=None, voi_mt5: bool = True, voi_nhan_c: bool = True) -> dict:
    """Quet phan cung + cau hinh. ~3-10 giay tren Windows. Khong nem."""
    ps, loi_ps = (None, "khong phai Windows")
    if LA_WINDOWS or runner is not None:
        ps, loi_ps = chay_ps(_PS_QUET, runner)
    try:
        import psutil
        vm = psutil.virtual_memory()
        ram_tong_gb = round(vm.total / 2 ** 30, 1)
    except Exception:                                                               # noqa: BLE001
        ram_tong_gb = None
    hdh = _ds((ps or {}).get("he_dieu_hanh"))
    q = {
        "luc": _ts(),
        "he_dieu_hanh": (" ".join(str(hdh[0].get("Caption") or "").split()) + " " + str(hdh[0].get("Version") or "")).strip()
                        if hdh else platform.platform()[:80],
        "python": sys.version.split()[0],
        "cpu": _doc_cpu(ps),
        "ram": _doc_ram(ps, ram_tong_gb),
        "dia": _doc_dia(ps),
        "pagefile": _doc_pagefile(ps),
        "ke_hoach_dien": _doc_dien(ps),
        "bo_mach": {k: " ".join(str(v or "").split())[:40] for k, v in (_ds((ps or {}).get("bo_mach")) or [{}])[0].items()},
        "bios": {k: " ".join(str(v or "").split())[:40] for k, v in (_ds((ps or {}).get("bios")) or [{}])[0].items()},
        "gpu": [{"ten": " ".join(str(g.get("Name") or "").split())[:60], "vram_gb": round((_so(g.get("AdapterRAM")) or 0) / 2 ** 30, 1)}
                for g in _ds((ps or {}).get("gpu"))],
        "gpu_opencl": bool((ps or {}).get("opencl")),
        "gpu_cuda": bool((ps or {}).get("cuda")),
        "defender_so_thu_muc_loai_tru": (ps or {}).get("defender_loai_tru"),
        "nhiet_c": None,
        "do_duoc_bang_powershell": ps is not None,
        "loi_powershell": loi_ps,
    }
    nh = _ds((ps or {}).get("nhiet"))
    if nh and _so(nh[0].get("CurrentTemperature")):
        q["nhiet_c"] = round(_so(nh[0]["CurrentTemperature"]) / 10.0 - 273.15, 1)       # decikelvin
    if not q["cpu"]["ten"] and sys.platform.startswith("linux"):
        q["cpu"]["ten"] = _quet_linux_cpu_ten()
    q["ram"]["tong_gb"] = q["ram"]["tong_gb"] or ram_tong_gb
    if voi_mt5:
        q["mt5"] = quet_mt5()
    if voi_nhan_c:
        q["nhan_c"] = _nhan_c()
    return an_danh(q)


# ================================================================ MAU TAI NGUYEN
def _commit_windows() -> dict:
    """Dung luong CAM KET qua GlobalMemoryStatusEx (khong can PowerShell): ullTotalPageFile = gioi han cam ket HIEN TAI
    (RAM + pagefile dang cap phat), ullAvailPageFile = con lai. Chinh con so nay het la `ENOMEM`, khong phai RAM trong."""
    import ctypes

    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):               # type: ignore[attr-defined]
        return {}
    return {"gioi_han_gb": _gb(m.ullTotalPageFile), "con_lai_gb": _gb(m.ullAvailPageFile),
            "dung_gb": _gb(m.ullTotalPageFile - m.ullAvailPageFile)}


def _commit_linux() -> dict:
    try:
        kv = {}
        for dong in Path("/proc/meminfo").read_text().splitlines():
            k, _, v = dong.partition(":")
            kv[k] = int(v.split()[0]) * 1024
        gh, da = kv.get("CommitLimit"), kv.get("Committed_AS")
        if gh is None or da is None:
            return {}
        return {"gioi_han_gb": _gb(gh), "con_lai_gb": _gb(gh - da), "dung_gb": _gb(da)}
    except (OSError, ValueError):
        return {}


def mau(nang: bool = False, runner=None, chu_ky: float | None = None) -> dict:
    """MOT mau tai nguyen. `nang=True` them 2 so tu WMI (trang/giay, hang doi dia) - mat ~1 s tren Windows."""
    try:
        import psutil
    except Exception:                                                               # noqa: BLE001
        return {"luc": _ts(), "loi": "thieu psutil"}
    chu_ky = chu_ky if chu_ky is not None else (1.0 if nang else 0.3)
    io1 = psutil.disk_io_counters()
    t1 = time.time()
    cpu = psutil.cpu_percent(interval=chu_ky, percpu=True)
    io2 = psutil.disk_io_counters()
    dt = max(time.time() - t1, 1e-3)
    vm = psutil.virtual_memory()
    d = {"luc": _ts(),
         "cpu_pct": round(sum(cpu) / len(cpu), 1) if cpu else None,
         "cpu_max_nhan_pct": round(max(cpu), 1) if cpu else None,
         "ram_trong_gb": round(vm.available / 2 ** 30, 2), "ram_dung_pct": vm.percent}
    if nang:
        d["cpu_tung_luong"] = [round(x) for x in cpu]
    try:
        f = psutil.cpu_freq()
        d["cpu_mhz"] = int(f.current) if f else None
    except Exception:                                                               # noqa: BLE001
        d["cpu_mhz"] = None
    cm = _commit_windows() if LA_WINDOWS else _commit_linux()
    d["commit_con_lai_gb"], d["commit_dung_gb"], d["commit_gioi_han_gb"] = cm.get("con_lai_gb"), cm.get("dung_gb"), cm.get("gioi_han_gb")
    try:
        sw = psutil.swap_memory()
        d["swap_dung_gb"] = _gb(sw.used)
    except Exception:                                                               # noqa: BLE001
        d["swap_dung_gb"] = None
    if io1 and io2:
        d["dia_doc_mbs"] = round((io2.read_bytes - io1.read_bytes) / dt / 1e6, 1)
        d["dia_ghi_mbs"] = round((io2.write_bytes - io1.write_bytes) / dt / 1e6, 1)
    o = {}
    try:
        for p in psutil.disk_partitions(all=False):
            if p.fstype and "cdrom" not in (p.opts or ""):
                try:
                    o[p.mountpoint.rstrip("\\/") or p.mountpoint] = round(psutil.disk_usage(p.mountpoint).free / 2 ** 30, 1)
                except OSError:
                    continue
    except Exception:                                                               # noqa: BLE001
        pass
    d["dia_trong_gb"] = o
    tp = {"python": 0, "terminal64": 0, "metatester64": 0, "chrome": 0, "python_rss_gb": 0.0, "mt5_rss_gb": 0.0}
    try:
        for p in psutil.process_iter(["name", "memory_info"]):
            ten = (p.info.get("name") or "").lower()
            rss = 0
            try:
                rss = p.info["memory_info"].rss
            except Exception:                                                       # noqa: BLE001
                pass
            if ten.startswith("python"):
                tp["python"] += 1
                tp["python_rss_gb"] += rss / 2 ** 30
            elif ten in ("terminal64.exe", "metatester64.exe"):
                tp[ten[:-4]] += 1
                tp["mt5_rss_gb"] += rss / 2 ** 30
            elif ten.startswith("chrome"):
                tp["chrome"] += 1
    except Exception:                                                               # noqa: BLE001
        pass
    tp["python_rss_gb"], tp["mt5_rss_gb"] = round(tp["python_rss_gb"], 2), round(tp["mt5_rss_gb"], 2)
    d["tien_trinh"] = tp
    if nang and (LA_WINDOWS or runner is not None):
        ps, loi = chay_ps(_PS_MAU, runner, han=30.0)
        if ps:
            bn = _ds(ps.get("bo_nho"))
            if bn:
                d["trang_doc_moi_giay"] = _so(bn[0].get("PageReadsPersec"))
                d["loi_trang_moi_giay"] = _so(bn[0].get("PageFaultsPersec"))
            dia = [x for x in _ds(ps.get("dia")) if str(x.get("Name")) == "_Total"] or _ds(ps.get("dia"))[:1]
            if dia:
                d["dia_ban_pct"] = _so(dia[0].get("PercentDiskTime"))
                d["dia_hang_doi"] = _so(dia[0].get("AvgDiskQueueLength"))
        else:
            d["loi_wmi"] = loi
    return d


# ================================================================ DEN XANH / VANG / DO
def danh_gia_mau(m: dict) -> dict:
    """Den cua MOT mau. KHONG phat vi CPU cao (chu du an muon 75-80%): chi canh bao cai lam SAP may, khong phai cai lam may BAN.

    DO  = sap hong ngay (het cam ket / het dia / het RAM) - da tung xay ra 13/09.
    VANG = can lam gi do trong ngay (don dia, them pagefile, dung bot viec)."""
    ly, den = [], "XANH"

    def nang(muc, cau):
        nonlocal den
        ly.append(cau)
        if muc == "DO" or den == "XANH":
            den = muc

    cm = m.get("commit_con_lai_gb")
    if cm is not None:
        if cm < NGUONG["commit_do_gb"]:
            nang("DO", "het cho cam ket bo nho (con %.1f GB): sap loi 'khong du bo nho' du RAM con trong" % cm)
        elif cm < NGUONG["commit_vang_gb"]:
            nang("VANG", "cho cam ket bo nho con %.1f GB (RAM + file trang): nen them file trang" % cm)
    r = m.get("ram_trong_gb")
    if r is not None:
        if r < NGUONG["ram_do_gb"]:
            nang("DO", "RAM trong chi con %.1f GB" % r)
        elif r < NGUONG["ram_vang_gb"]:
            nang("VANG", "RAM trong con %.1f GB (duoi %.0f)" % (r, NGUONG["ram_vang_gb"]))
    for o, gb in sorted((m.get("dia_trong_gb") or {}).items()):
        if o.upper().startswith("C") or o in ("/", "/home"):       # o he thong: pagefile + tam + log phinh o do
            if gb < NGUONG["dia_do_gb"]:
                nang("DO", "o %s chi con %.1f GB trong" % (o, gb))
            elif gb < NGUONG["dia_vang_gb"]:
                nang("VANG", "o %s con %.1f GB trong" % (o, gb))
        elif re.fullmatch(r"[A-Za-z]:", o) and gb < 2.0:             # o du lieu khac (F:, E:, HDD moi): het cho thi ghi se hong
            nang("VANG", "o %s con %.1f GB trong" % (o, gb))
    if (m.get("trang_doc_moi_giay") or 0) > 1000:
        nang("VANG", "may dang doc file trang %d trang/giay: dang thieu RAM that, nen giam so viec" % m["trang_doc_moi_giay"])
    return {"den": den, "ly_do": ly or ["on"]}


def ghi_mau_nhe(duong: Path | None = None, toi_da_dong: int = 25_000) -> dict:
    """Mau nhe (khong PowerShell) -> ghi `nhat_ky/may_nha_mau.jsonl` -> tra {den, ly_do, mau}. `b cau chay` goi moi 5 phut
    (khong LLM, khong tra token). KHONG nem: loi thanh den None."""
    try:
        m = mau(nang=False)
        dg = danh_gia_mau(m)
        p = duong or NHAT_KY
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists() and p.stat().st_size > 12_000_000:                           # ~25.000 dong
            p.replace(p.with_suffix(".jsonl.1"))
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({**m, "den": dg["den"]}, ensure_ascii=False, separators=(",", ":")) + "\n")
        return {"den": dg["den"], "ly_do": dg["ly_do"], "mau": m}
    except Exception as e:                                                          # noqa: BLE001
        return {"den": None, "ly_do": ["khong lay duoc mau: %s" % type(e).__name__], "mau": None}


def doc_nhat_ky(gio: float = 24.0, duong: Path | None = None) -> list[dict]:
    p = duong or NHAT_KY
    if not p.exists():
        return []
    han = time.time() - gio * 3600
    ra = []
    try:
        for dong in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                d = json.loads(dong)
                if time.mktime(time.strptime(d["luc"], "%Y-%m-%dT%H:%M:%S")) >= han:
                    ra.append(d)
            except (ValueError, KeyError):
                continue
    except OSError:
        return []
    return ra


def _phan_vi(xs: list[float], q: float) -> float | None:
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))
    return xs[i]


def tom_tat_mau(ds: list[dict]) -> dict:
    """Tom tat mot chuoi mau: bao nhieu % thoi gian trong dai 75-80% CPU, RAM/commit thap nhat, ..."""
    if not ds:
        return {"so_mau": 0}
    cpu = [d.get("cpu_pct") for d in ds if d.get("cpu_pct") is not None]
    lo, hi = DAI_CPU
    n = max(len(cpu), 1)
    return {
        "so_mau": len(ds), "tu": ds[0].get("luc"), "den": ds[-1].get("luc"),
        "cpu_tb": round(sum(cpu) / n, 1) if cpu else None,
        "cpu_p95": _phan_vi(cpu, 0.95),
        "pct_thoi_gian_trong_dai": round(100 * sum(1 for c in cpu if lo <= c <= hi) / n, 1) if cpu else None,
        "pct_thoi_gian_duoi_dai": round(100 * sum(1 for c in cpu if c < lo) / n, 1) if cpu else None,
        "pct_thoi_gian_tren_dai": round(100 * sum(1 for c in cpu if c > hi) / n, 1) if cpu else None,
        "pct_duoi_30": round(100 * sum(1 for c in cpu if c < 30) / n, 1) if cpu else None,
        "ram_trong_thap_nhat_gb": min((d["ram_trong_gb"] for d in ds if d.get("ram_trong_gb") is not None), default=None),
        "commit_con_lai_thap_nhat_gb": min((d["commit_con_lai_gb"] for d in ds if d.get("commit_con_lai_gb") is not None), default=None),
        "dia_c_thap_nhat_gb": min((v for d in ds for k, v in (d.get("dia_trong_gb") or {}).items() if k.upper().startswith("C")), default=None),
        "so_mau_den_do": sum(1 for d in ds if d.get("den") == "DO"),
        "so_mau_den_vang": sum(1 for d in ds if d.get("den") == "VANG"),
        "mt5_chay_pct": round(100 * sum(1 for d in ds if (d.get("tien_trinh") or {}).get("metatester64")
                                         or (d.get("tien_trinh") or {}).get("terminal64")) / len(ds), 1),
        "python_tien_trinh_max": max(((d.get("tien_trinh") or {}).get("python") or 0 for d in ds), default=0),
    }


def giam_sat(phut: float = 10.0, chu_ky: float = 15.0, nang: bool = True, runner=None, in_ra=None) -> dict:
    """Lay mau moi `chu_ky` giay trong `phut` phut, ghi nhat ky, tom tat."""
    het = time.time() + phut * 60
    ds = []
    while True:
        m = mau(nang=nang, runner=runner)
        dg = danh_gia_mau(m)
        m["den"] = dg["den"]
        ds.append(m)
        try:
            NHAT_KY.parent.mkdir(parents=True, exist_ok=True)
            with open(NHAT_KY, "a", encoding="utf-8") as f:
                f.write(json.dumps(m, ensure_ascii=False, separators=(",", ":")) + "\n")
        except OSError:
            pass
        if in_ra:
            in_ra("  %s cpu %s%%  ram trong %s GB  commit con %s GB  den %s" % (
                m.get("luc", "")[-8:], m.get("cpu_pct"), m.get("ram_trong_gb"), m.get("commit_con_lai_gb"), dg["den"]))
        if time.time() + chu_ky >= het:
            break
        time.sleep(chu_ky)
    return {"tom_tat": tom_tat_mau(ds), "so_mau": len(ds)}


# ================================================================ DO CO GIAN (chi khi may RANH)
def _ha_uu_tien() -> None:
    """Tien trinh do chay UU TIEN THAP de may van dung duoc luc do."""
    try:
        import psutil
        if LA_WINDOWS:
            psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            os.nice(5)
    except Exception:                                                               # noqa: BLE001
        pass


def _nhan_cpu_nho(giay: float) -> float:
    """Vong lap Python thuan nam gon trong cache (kieu quet D1: moi o ~128 KB). Tra so TRIEU vong da chay."""
    chunk = 40_000
    het, k = time.perf_counter() + giay, 0
    x = 1.0
    while time.perf_counter() < het:
        s = 0.0
        for i in range(chunk):
            s += ((i * i) % 7) * 0.5 + (i & 3)
        x += s * 1e-12
        k += 1
    return k * chunk / 1e6 + (x * 0.0)


def _chuoi_gia(so_bar: int):
    import numpy as np
    rng = np.random.default_rng(7)
    x = np.cumsum(rng.normal(0.0, 0.0004, so_bar)) * 0.2 + 0.9
    cl = np.round(x, 5)
    hi = np.round(cl + np.abs(rng.normal(0.0, 0.0003, so_bar)), 5)
    lo = np.round(cl - np.abs(rng.normal(0.0, 0.0003, so_bar)), 5)
    sp = np.full(so_bar, 0.0001)
    dem = np.zeros(so_bar)
    dem[96::96] = 1.0
    return hi, lo, cl, sp, dem


def _chuan_bi_luoi(so_bar: int):
    """Nap engine + dung chuoi gia lap NGOAI cua so do. Tra `chay(giay) -> trieu nen da chay`.
    Dung CHINH engine luoi that: nhan C neu san sang, khong thi Python."""
    from nhan import luoi as LU
    from nhan import luoi_nhan as LN
    hi, lo, cl, sp, dem = _chuoi_gia(so_bar)
    ts = LU.ThamSo(buoc=30.0, tp=25.0, tran_tang=12)
    qc = LU.QC_AUDCAD
    dung_c = LN.lay_nhan() is not None and LN.che_do() != "py"

    def mot():
        if dung_c and LN.mot_ro(hi, lo, cl, sp, dem, 1, ts, qc) is not None:
            return
        LU._mot_ro(hi, lo, cl, sp, dem, 1, ts, qc)

    mot()                                                                          # khoi dong (nap DLL, tu kiem) NGOAI cua so do

    def chay(giay: float) -> float:
        het, k = time.perf_counter() + giay, 0
        while time.perf_counter() < het:
            mot()
            k += 1
        return k * so_bar / 1e6
    return chay


def _chuan_bi_bang_thong(mb: int):
    """3 mang `mb` MiB (lon hon cache): moi vong `a = b + c` doc 2 + ghi 1 mang (kieu STREAM add). Tra `chay(giay) -> GB da chuyen`."""
    import numpy as np
    n = mb * 2 ** 20 // 8
    a, b, c = np.ones(n), np.full(n, 2.0), np.full(n, 3.0)
    np.add(b, c, out=a)                                                            # cham het trang (page fault) NGOAI cua so do

    def chay(giay: float) -> float:
        het, k = time.perf_counter() + giay, 0
        while time.perf_counter() < het:
            np.add(b, c, out=a)
            k += 1
        return k * 3 * n * 8 / 1e9
    return chay


def _chuan_bi(loai: str, mb: int, so_bar: int):
    if loai == "cpu_nho":
        return _nhan_cpu_nho
    if loai in ("luoi", "luoi_dai"):
        return _chuan_bi_luoi(so_bar)
    if loai == "bang_thong":
        return _chuan_bi_bang_thong(mb)
    raise ValueError(loai)


def _tien_trinh_do(loai, giay, mb, so_bar, hang_rao, hang_ra, chi_so):
    """Chay trong tien trinh con: chuan bi (cap phat, nap thu vien) -> cho vach xuat phat -> do `giay` giay -> tra ket qua."""
    try:
        _ha_uu_tien()
        chay = _chuan_bi(loai, mb, so_bar)
        hang_rao.wait(timeout=180)
        hang_ra.put((chi_so, chay(giay), None))
    except Exception as e:                                                          # noqa: BLE001
        try:
            hang_rao.abort()
        except Exception:                                                           # noqa: BLE001
            pass
        hang_ra.put((chi_so, None, "%s: %s" % (type(e).__name__, str(e)[:120])))


def do_mot_buoc(loai: str, n: int, giay: float, mb: int = 64, so_bar: int = 60_000) -> dict:
    """Chay `n` tien trinh CUNG LUC `giay` giay. Tra toc do TONG + CPU% that + MHz giua cua so."""
    import multiprocessing as mp
    import psutil
    ctx = mp.get_context("spawn")
    rao, ra = ctx.Barrier(n + 1), ctx.Queue()
    ps = [ctx.Process(target=_tien_trinh_do, args=(loai, giay, mb, so_bar, rao, ra, i), daemon=True) for i in range(n)]
    for p in ps:
        p.start()
    cpu, mhz, loi = [], None, None
    try:
        rao.wait(timeout=180)
    except Exception as e:                                                          # noqa: BLE001
        loi = "tien trinh con khong len duoc: %s" % type(e).__name__
    t0 = time.time()
    psutil.cpu_percent(interval=None)
    while time.time() - t0 < giay * 0.85 and loi is None:
        time.sleep(min(0.5, giay / 6))
        c = psutil.cpu_percent(interval=None)
        if time.time() - t0 > giay * 0.2:                                           # bo doan khoi dong cua so
            cpu.append(c)
            if mhz is None and time.time() - t0 > giay * 0.5:
                try:
                    f = psutil.cpu_freq()
                    mhz = int(f.current) if f else None
                except Exception:                                                   # noqa: BLE001
                    mhz = None
    tong, thieu, dau_loi = 0.0, 0, None
    for _ in range(n):
        try:
            _, v, e = ra.get(timeout=giay + 90)
        except Exception:                                                           # noqa: BLE001
            thieu += 1
            continue
        if v is None:
            thieu += 1
            dau_loi = dau_loi or e
        else:
            tong += v
    for p in ps:
        p.join(timeout=5)
        if p.is_alive():
            p.terminate()
    r = {"n": n, "toc_do_tong": round(tong / giay, 4), "cpu_pct": round(sum(cpu) / len(cpu), 1) if cpu else None, "mhz": mhz}
    if loi or thieu:
        r["loi"] = loi or "%d/%d tien trinh khong tra ket qua (%s)" % (thieu, n, dau_loi)
    return r


def danh_sach_n(luong: int, nhan_vat_ly: int | None, nhanh: bool, tran: int | None = None) -> list[int]:
    """Cac muc N de do: day o cac moc co nghia (1, nhan vat ly, 75-80%, het luong, qua tai)."""
    L = max(1, luong)
    if nhanh:
        s = {1, 2, 4, 8, nhan_vat_ly or L // 2, round(L * 0.8), L}
    else:
        s = {1, 2, 3, 4, 6, 8, nhan_vat_ly or L // 2, round(L * 0.5), round(L * 0.65), round(L * 0.75), round(L * 0.8),
             round(L * 0.9), L, round(L * 1.2)}
    tran_tren = L if nhanh else max(L, round(L * 1.2))      # may it luong: khong do 4 lan so luong (chi chia thoi gian, khong co nghia)
    s = sorted(x for x in s if 1 <= x <= tran_tren)
    if tran:
        s = [x for x in s if x <= tran]
    return s


def phan_tich_co_gian(diem: list[dict], luong: int, nhan_vat_ly: int | None) -> dict:
    """Tu cac diem (n, toc_do_tong): diem bao hoa, toc do o ~80% so voi dinh, loi ich hyperthreading, anh huong qua tai.

    Chi cac diem n <= so luong duoc dung de tim dinh / bao hoa: chay nhieu tien trinh hon so luong chi chia thoi gian
    (mot dinh o n > luong thuong la do xep lich, khong phai phan cung) va khong tra loi cau hoi "nen chay may viec cung luc".
    `n_bao_hoa` = n nho nhat ma them tien trinh nao nua cung chi them < DOC_BAO_HOA (10%) tong toc do."""
    tat_ca = sorted((d for d in diem if d.get("toc_do_tong") and not d.get("loi")), key=lambda d: d["n"])
    if not tat_ca:
        return {"du_lieu": False}
    ok = [d for d in tat_ca if d["n"] <= luong] or tat_ca
    qua_tai = [d for d in tat_ca if d["n"] > luong]
    t1 = next((d["toc_do_tong"] for d in ok if d["n"] == 1), ok[0]["toc_do_tong"] / ok[0]["n"])
    dinh = max(ok, key=lambda d: d["toc_do_tong"])
    tren_90 = next(d for d in ok if d["toc_do_tong"] >= 0.9 * dinh["toc_do_tong"])
    bao_hoa = ok[-1]["n"]
    for i, a in enumerate(ok):
        if max(b["toc_do_tong"] for b in ok[i:]) <= a["toc_do_tong"] * (1.0 + DOC_BAO_HOA):
            bao_hoa = a["n"]
            break
    n80 = max(1, round(luong * (DAI_CPU[0] + DAI_CPU[1]) / 200.0))
    gan80 = min(ok, key=lambda d: abs(d["n"] - n80))
    nvl = nhan_vat_ly or max(1, luong // 2)
    gan_vl = min(ok, key=lambda d: abs(d["n"] - nvl))
    gan_ht = min(ok, key=lambda d: abs(d["n"] - luong))
    r = {"du_lieu": True, "toc_do_1": round(t1, 4), "dinh": {"n": dinh["n"], "toc_do_tong": dinh["toc_do_tong"]},
         "n_dat_90pct_dinh": tren_90["n"], "n_bao_hoa": bao_hoa,
         "n_o_80pct_cpu": n80, "n_do_gan_80": gan80["n"], "toc_do_o_80pct": gan80["toc_do_tong"],
         "pct_toc_do_o_80_so_voi_dinh": round(100 * gan80["toc_do_tong"] / dinh["toc_do_tong"], 1),
         "hieu_suat_o_80pct": round(gan80["toc_do_tong"] / (gan80["n"] * t1), 2) if t1 else None,
         "cpu_pct_o_diem_gan_80": gan80.get("cpu_pct"),
         "x_so_voi_1_tien_trinh_o_dinh": round(dinh["toc_do_tong"] / t1, 2) if t1 else None}
    if gan_vl["n"] != gan_ht["n"] and gan_vl["toc_do_tong"] > 0:
        r["loi_ich_hyperthreading_pct"] = round(100 * (gan_ht["toc_do_tong"] / gan_vl["toc_do_tong"] - 1), 1)
    if qua_tai:
        r["qua_tai_pct_so_voi_dinh"] = round(100 * max(d["toc_do_tong"] for d in qua_tai) / dinh["toc_do_tong"], 1)
    mhz = [(d["n"], d["mhz"]) for d in ok if d.get("mhz")]
    if len(mhz) >= 2:
        r["mhz_1_tien_trinh"], r["mhz_nhieu_nhat"] = mhz[0][1], mhz[-1][1]
    return r


def _ghi_dia(thu_muc: Path, mb: int, iops_lan: int) -> dict:
    """Ghi tuan tu `mb` MiB (fsync) + `iops_lan` lan ghi 4 KiB ngau nhien co fsync. File tam xoa ngay."""
    import random
    r = {"thu_muc": str(an_danh(str(thu_muc)))}
    f = None
    try:
        thu_muc.mkdir(parents=True, exist_ok=True)
        fd, ten = tempfile.mkstemp(prefix="may_nha_do_", suffix=".bin", dir=str(thu_muc))
        f = Path(ten)
        blk = os.urandom(1 << 20)
        t0 = time.perf_counter()
        with os.fdopen(fd, "wb", buffering=0) as fh:
            for _ in range(mb):
                fh.write(blk)
            os.fsync(fh.fileno())
        dt = time.perf_counter() - t0
        r["ghi_tuan_tu_mbs"] = round(mb / dt, 1)
        rnd = random.Random(1)
        buf = os.urandom(4096)
        lat = []
        with open(f, "r+b", buffering=0) as fh:
            for _ in range(iops_lan):
                fh.seek(rnd.randrange(0, mb * 256) * 4096)
                t1 = time.perf_counter()
                fh.write(buf)
                os.fsync(fh.fileno())
                lat.append(time.perf_counter() - t1)
        r["ghi_ngau_nhien_4k_iops"] = round(len(lat) / max(sum(lat), 1e-9), 0)
        r["tre_fsync_ms_tb"] = round(1000 * sum(lat) / len(lat), 2)
        r["tre_fsync_ms_p95"] = round(1000 * (_phan_vi(lat, 0.95) or 0), 2)
    except OSError as e:
        r["loi"] = "%s: %s" % (type(e).__name__, str(e)[:100])
    finally:
        if f is not None:
            try:
                f.unlink()
            except OSError:
                pass
    return r


def phan_loai_dia(d: dict) -> str | None:
    iops = d.get("ghi_ngau_nhien_4k_iops")
    if iops is None:
        return None
    if iops < NGUONG["ngau_nhien_iops_hdd"]:
        return "cham (kieu HDD)"
    if iops < NGUONG["ngau_nhien_iops_nhanh"]:
        return "vua (SSD SATA / HDD co bo dem)"
    return "nhanh (SSD)"


def _thu_muc_do(goc: str) -> Path:
    """Thu muc tam de do o `goc` (vd `C:` hay `/`): uu tien thu muc tam cua Windows neu no nam tren o do (quyen ghi chac chan),
    khong thi mot thu muc con rieng o goc o (tao thu muc o goc o duoc phep, tao FILE thang o goc C: thi khong)."""
    tmp = Path(tempfile.gettempdir())
    if LA_WINDOWS and tmp.drive and tmp.drive.rstrip(":").upper() == goc.rstrip(":\\/").upper()[:1]:
        return tmp / "_may_nha_do_tam"
    return (Path(goc + "\\") if LA_WINDOWS and len(goc) == 2 else Path(goc)) / "_may_nha_do_tam"


def do_dia(o_dia: list[dict] | None = None, mb: int = 256, iops_lan: int = 300) -> list[dict]:
    """Do tung o co du cho. Chi ghi file tam vao thu muc tam rieng cua tung o, xoa ngay."""
    ra = []
    ds = o_dia if o_dia is not None else (quet(voi_mt5=False, voi_nhan_c=False)["dia"]["o"])
    for o in ds[:6]:
        goc = str(o.get("o") or "")
        if not goc or (o.get("trong_gb") or 0) < (mb / 1024 * 3 + 2.0):
            ra.append({"o": goc, "loi": "khong du cho trong de do an toan"})
            continue
        thu = _thu_muc_do(goc)
        d = _ghi_dia(thu, mb, iops_lan)
        try:
            thu.rmdir()
        except OSError:
            pass
        d["o"] = goc
        d["loai_do_duoc"] = phan_loai_dia(d)
        ra.append(d)
    return ra


def may_ranh(nguong_pct: float = 35.0, giay: float = 3.0) -> tuple[bool, float | None]:
    try:
        import psutil
        c = psutil.cpu_percent(interval=giay)
        return c < nguong_pct, round(c, 1)
    except Exception:                                                               # noqa: BLE001
        return True, None


def do(nhanh: bool = False, ep: bool = False, tran: int | None = None, giay: float | None = None,
       loai: tuple = LOAI_DO, q: dict | None = None, in_ra=None) -> dict:
    """DO CO GIAN. Tra {trang_thai, ...}. `CHUA_DO_DUOC` neu may ban (tru khi `ep`).

    Bon kernel (xem docstring dau file): `cpu_nho`, `luoi` (chuoi 60k nen: nam trong cache), `luoi_dai` (chuoi 1 trieu nen:
    nam o RAM - chinh cai quet M1 nhieu nam dung), `bang_thong`. `luoi_dai` chi do khi co nhan C (Python 3 giay/lan: khong do duoc)."""
    in_ra = in_ra or (lambda *_a, **_k: None)
    q = q or quet(voi_mt5=False, voi_nhan_c=True)
    luong = (q["cpu"].get("luong") or os.cpu_count() or 1)
    nvl = q["cpu"].get("nhan_vat_ly")
    ranh, c_nen = may_ranh()
    ra = {"luc": _ts(), "trang_thai": "DAT", "luong": luong, "nhan_vat_ly": nvl, "cpu_nen_pct": c_nen,
          "nhieu_nen": False, "nhanh": nhanh}
    if not ranh:
        if not ep:
            ra.update(trang_thai="CHUA_DO_DUOC",
                      ly_do="may dang ban (CPU nen %s%% >= 35%%): do luc nay cho so SAI. Dung `q dung`, dong tester roi chay lai, "
                            "hoac them --ep (ket qua se gan nhieu_nen)." % c_nen)
            return ra
        ra["nhieu_nen"] = True
    ns = danh_sach_n(luong, nvl, nhanh, tran)
    ra["muc_n"] = ns
    gs = giay or (2.0 if nhanh else 4.0)
    ra["giay_moi_buoc"] = gs
    try:
        import psutil
        trong_mb = psutil.virtual_memory().available / 2 ** 20
    except Exception:                                                               # noqa: BLE001
        trong_mb = 4096.0
    ngan_sach_mb = min(6144.0, 0.35 * trong_mb)
    nhan_c_ok = bool((q.get("nhan_c") or {}).get("san_sang"))
    for ten in loai:
        if ten == "dia":
            in_ra("do dia ...")
            ra["dia"] = do_dia(q["dia"]["o"])
            continue
        if ten == "luoi_dai" and not nhan_c_ok:
            ra[ten] = {"bo_qua": "chua co nhan C: chuoi 1 trieu nen o Python ~3 giay/lan, khong do duoc (cai `pip install ziglang`)"}
            continue
        so_bar = SO_BAR_DAI if ten == "luoi_dai" else 60_000
        diem = []
        for n in ns:
            mb = int(max(32, min(64, ngan_sach_mb / (3 * n))))                      # san 32 MB: duoi nua mang se lot vao cache
            d = do_mot_buoc(ten, n, gs, mb=mb, so_bar=so_bar)
            if ten == "bang_thong":
                d["mb_moi_mang"] = mb
            diem.append(d)
            in_ra("  %-10s n=%-3d toc do %s  cpu %s%%" % (ten, n, d.get("toc_do_tong"), d.get("cpu_pct")))
        ra[ten] = {"diem": diem, "phan_tich": phan_tich_co_gian(diem, luong, nvl)}
        if ten == "bang_thong":
            ly = (q.get("ram") or {}).get("bang_thong_ly_thuyet_gbs")
            ra[ten]["ly_thuyet_gbs"] = ly
            pt = ra[ten]["phan_tich"]
            if ly and pt.get("du_lieu"):
                pt["pct_so_voi_ly_thuyet"] = round(100 * pt["dinh"]["toc_do_tong"] / ly, 1)
    return ra


# ================================================================ KET LUAN (so lieu -> quyet dinh)
def _pt(d: dict, ten: str) -> dict:
    """Phan tich cua mot kernel, hoac {} neu chua do / khong du lieu."""
    p = (d.get(ten) or {}).get("phan_tich") or {}
    return p if p.get("du_lieu") else {}


def so_mt5_toi_da(q: dict, d: dict, model: str = "model_0_4") -> dict:
    """Toi da bao nhieu terminal / tai khoan MT5 demo la CO ICH. Khong phai 'chay duoc bao nhieu' - la 'them nua cung khong nhanh hon'.

    Bon tran, lay MIN:
      cpu         so tien trinh o ~78% CPU (do duoc: diem gan 80% cua kernel `cpu_nho`)
      ram         (RAM trong - du tru Windows) / RAM moi agent (do that neu co agent dang chay, khong thi GIA DINH)
      bang_thong  dinh bang thong RAM do duoc / nhu cau moi agent (GIA DINH BANG_THONG_MOI_AGENT_GBS = 2 GB/s: agent tick doc nhieu bo nho)
      dia         cho trong cac o / dung luong du lieu lich su cua mot terminal
    Hai che do dung khac nhau: TOI UU HOA = MOT terminal tu chia viec cho moi agent cuc bo (1 tai khoan la du, so agent = tran);
    CHAY DON = moi lan thu can mot terminal rieng (thu muc du lieu rieng). Tai khoan: moi terminal 1 tai khoan, TRU KHI thu
    thay XM cho mot tai khoan dang nhap nhieu terminal (chua kiem) - khi do chi can 1."""
    luong = q["cpu"].get("luong") or 1
    cpu_cap = int(_pt(d, "cpu_nho").get("n_o_80pct_cpu") or max(1, round(luong * 0.78)))
    tb = (q.get("mt5") or {}).get("agent_rss_gb_tb")
    ram_agent = tb or RAM_AGENT_GB[model]
    tong = (q.get("ram") or {}).get("tong_gb") or 16.0
    try:
        import psutil
        trong = psutil.virtual_memory().available / 2 ** 30
    except Exception:                                                               # noqa: BLE001
        trong = tong
    nen_ram = max(0.0, min(trong, tong - RAM_DE_DANH_GB) - 2.0)
    ram_cap = max(1, int(nen_ram // ram_agent))
    bp = _pt(d, "bang_thong")
    ly = (q.get("ram") or {}).get("bang_thong_ly_thuyet_gbs")
    if bp:
        bw_gbs, bw_nguon = bp["dinh"]["toc_do_tong"], "do"
    elif ly:
        bw_gbs, bw_nguon = 0.5 * ly, "uoc (50% ly thuyet)"
    else:
        bw_gbs, bw_nguon = None, None
    bw_cap = max(1, int(bw_gbs // BANG_THONG_MOI_AGENT_GBS)) if bw_gbs else None
    mt = q.get("mt5") or {}
    dl = [x.get("gb_bases") or 0 for x in mt.get("thu_muc_du_lieu", [])]
    moi_term_gb = max(dl) if dl and max(dl) > 0.5 else 8.0
    trong_dia = sum((o.get("trong_gb") or 0) for o in (q.get("dia") or {}).get("o", []))
    dia_cap = int(trong_dia // moi_term_gb) if trong_dia else None
    caps = {"cpu": cpu_cap, "ram": ram_cap, "bang_thong": bw_cap, "dia": dia_cap}
    thuc = {k: v for k, v in caps.items() if v}
    gh = min(thuc, key=lambda k: thuc[k])
    tran = max(1, thuc[gh])
    return {"tran": caps, "tran_nho_nhat_do": gh, "agent_toi_da": tran,
            "bang_thong_dung_gbs": bw_gbs, "bang_thong_nguon": bw_nguon, "bang_thong_moi_agent_gia_dinh_gbs": BANG_THONG_MOI_AGENT_GBS,
            "ram_moi_agent_gb": ram_agent, "ram_moi_agent_do_that": tb is not None,
            "gb_moi_terminal": moi_term_gb, "gb_moi_terminal_do_that": bool(dl and max(dl) > 0.5),
            "che_do_toi_uu_hoa": {"terminal": 1, "agent": tran},
            "che_do_chay_don": {"terminal_toi_da": tran},
            "tai_khoan_demo_toi_da": tran,
            "tai_khoan_demo_neu_xm_cho_dung_chung": 1,
            "ly_do": "tran thap nhat la %s (%s); them terminal/tai khoan vuot %d khong nhanh hon vi chi chia nhau cung mot may" % (
                gh, ", ".join("%s=%s" % (k, v) for k, v in thuc.items()), tran)}


def ket_luan(q: dict, d: dict | None = None, m: dict | None = None) -> dict:
    """So lieu -> {den, tom_lai[], tom_tat[], so{}, khuyen_nghi[]}. `d`/`m` co the None (chua do / chua lay mau).

    `tom_lai` = cac cau loi thuong (chu du an doc). `tom_tat` = con so kem theo. `khuyen_nghi` = viec cu the; `ai_lam` la
    'chu_du_an' (can tay nguoi: mua RAM, doi cai dat Windows) hay 'may' (lenh `b`, khong doi cai dat Windows)."""
    d = d or {}
    m = m or {}
    tl, tt, kn, so = [], [], [], {}
    den = "XANH"

    def hop(muc):
        nonlocal den
        if muc == "DO" or (muc == "VANG" and den == "XANH"):
            den = muc

    cpu, ram = q.get("cpu", {}), q.get("ram", {})
    tt.append("May: %s, %s nhan / %s luong, RAM %s GB (%s thanh, khe trong %s, %s kenh dang dung)." % (
        cpu.get("ten") or "?", cpu.get("nhan_vat_ly") or "?", cpu.get("luong") or "?", ram.get("tong_gb") or "?",
        ram.get("so_thanh") or "?", ram.get("khe_trong") if ram.get("khe_trong") is not None else "?",
        ram.get("kenh_dang_dung") or "?"))

    if m:
        dg = danh_gia_mau(m)
        hop(dg["den"])
        if dg["den"] != "XANH":
            tl.append("Suc khoe may: %s - %s." % (dg["den"], "; ".join(dg["ly_do"])))
        else:
            tl.append("Suc khoe may: XANH - on (CPU %s%%, RAM trong %s GB, cam ket con lai %s GB)." % (
                m.get("cpu_pct", "?"), m.get("ram_trong_gb", "?"), m.get("commit_con_lai_gb", "?")))

    cp, lp, ld, bp = _pt(d, "cpu_nho"), _pt(d, "luoi"), _pt(d, "luoi_dai"), _pt(d, "bang_thong")
    if not (cp or lp or ld or bp):
        # chua do gi: van tra loi duoc cau 'toi da bao nhieu tai khoan MT5' bang so UOC, ghi ro la uoc
        uoc = so_mt5_toi_da(q, d)
        so["mt5_uoc_tam"] = uoc
        tl.append("Chua do toc do may nen chua co con so chinh thuc. UOC TAM (tu bang thong ly thuyet, CHUA do): tao toi da ~%d tai khoan MT5 demo. "
                  "Chay `b may do --nhanh` luc may ranh (~1 phut; day du `b may do` ~5 phut) de co so that." % uoc["agent_toi_da"])

    # ---- toc do o dai 75-80% CPU
    if cp:
        so.update(luong_o_80pct=cp["n_o_80pct_cpu"], pct_toc_do_o_80pct=cp["pct_toc_do_o_80_so_voi_dinh"],
                  luong_dat_90pct_dinh=cp["n_dat_90pct_dinh"], luong_bao_hoa_cpu=cp["n_bao_hoa"],
                  x_toc_do_toi_da_so_voi_1_nhan=cp["x_so_voi_1_tien_trinh_o_dinh"])
        cau = ("O ~78%% CPU (%d viec song song) may dat %.0f%% toc do toi da; ket qua toi da chi ~x%.1f so voi chay 1 viec."
               % (cp["n_o_80pct_cpu"], cp["pct_toc_do_o_80_so_voi_dinh"], cp["x_so_voi_1_tien_trinh_o_dinh"]))
        if cp.get("loi_ich_hyperthreading_pct") is not None:
            cau += " Luong ao (hyperthreading) cho them %.0f%% so voi chi dung nhan vat ly." % cp["loi_ich_hyperthreading_pct"]
        tl.append(cau)
        if cp["pct_toc_do_o_80_so_voi_dinh"] >= 85:
            tl.append("Giu tran CPU 75-80%% la dung: chay 100%% chi them ~%.0f%% toc do ma may giat." %
                      (100 - cp["pct_toc_do_o_80_so_voi_dinh"]))
    # ---- engine luoi that: cache vs RAM
    if lp:
        # 1 luot = 1 bo tham so tren 1 trieu nen, ma toc do do bang TRIEU nen/giay => luot/giay; nhan 3600 ra luot/gio
        so.update(luot_thu_moi_gio_o_80pct_cache=int(round(lp["toc_do_o_80pct"] * 3600)),
                  luot_thu_moi_gio_dinh_cache=int(round(lp["dinh"]["toc_do_tong"] * 3600)))
        nc = q.get("nhan_c") or {}
        tt.append("Engine luoi (%s, chuoi gia lap 60k nen nam trong cache): o ~80%% CPU ~%s luot thu/gio, toi da ~%s "
                  "(1 luot = 1 bo tham so tren 1 trieu nen; chuoi that co the cham hon 2-3 lan)." % (
                      "nhan C" if nc.get("san_sang") else "Python - CHUA co nhan C", format(so["luot_thu_moi_gio_o_80pct_cache"], ","),
                      format(so["luot_thu_moi_gio_dinh_cache"], ",")))
        if not nc.get("san_sang"):
            hop("VANG")
            kn.append({"viec": "Cai trinh bien dich de bat nhan C (nhanh hon ~100 lan): `pip install ziglang` (~80 MB, mot lan), roi "
                               "`python -m nhan.luoi_nhan` de no tu kiem", "ai_lam": "may", "can_phep": False})
    if ld:
        so.update(luot_thu_moi_gio_o_80pct_ram=int(round(ld["toc_do_o_80pct"] * 3600)), luot_thu_moi_gio_dinh_ram=int(round(ld["dinh"]["toc_do_tong"] * 3600)),
                  engine_dai_n_bao_hoa=ld["n_bao_hoa"], engine_dai_pct_toc_do_o_80=ld["pct_toc_do_o_80_so_voi_dinh"])
        tt.append("Engine luoi tren chuoi DAI (1 trieu nen, nam o RAM - giong quet M1 nhieu nam): dinh ~%s luot/gio, het loi tu ~%d viec song song; "
                  "o ~80%% CPU duoc %.0f%% dinh." % (format(so["luot_thu_moi_gio_dinh_ram"], ","), ld["n_bao_hoa"],
                                                    ld["pct_toc_do_o_80_so_voi_dinh"]))
    # ---- bang thong
    if bp:
        ly = (d.get("bang_thong") or {}).get("ly_thuyet_gbs")
        so.update(bang_thong_dinh_gbs=bp["dinh"]["toc_do_tong"], bang_thong_bao_hoa_o_n=bp["n_bao_hoa"],
                  bang_thong_pct_ly_thuyet=bp.get("pct_so_voi_ly_thuyet"))
        tt.append("Bang thong RAM do duoc: dinh %.1f GB/giay%s, het loi tu ~%d viec song song." % (
            bp["dinh"]["toc_do_tong"],
            (" (%.0f%% cua muc ly thuyet %.1f GB/s)" % (bp["pct_so_voi_ly_thuyet"], ly)) if ly and bp.get("pct_so_voi_ly_thuyet") else "",
            bp["n_bao_hoa"]))
    # ---- gioi han chinh + loi ich neu nang RAM
    kenh, khe = ram.get("kenh_dang_dung"), ram.get("khe_trong")
    kmax = _kenh_toi_da(cpu.get("ten"), cpu.get("so_o_cam"))
    if cp and (ld or bp):
        nen = ld or bp
        nghen_ram = nen["n_bao_hoa"] < 0.6 * max(cp["n_bao_hoa"], 1)
        so["gioi_han_chinh"] = {"viec_nhe_trong_cache": "CPU", "viec_doc_nhieu_RAM": "bang thong RAM" if nghen_ram else "CPU"}
        if nghen_ram:
            cau = ("Cai nghen thuc su: viec doc nhieu bo nho (quet M1 nhieu nam, agent MT5) chi chay hieu qua ~%d viec cung luc "
                   "du may co %s luong; viec nhe nam trong cache thi chay duoc ~%d." % (nen["n_bao_hoa"], cpu.get("luong") or "?", cp["n_bao_hoa"]))
            tl.append(cau)
            if lp and ld and ld["toc_do_o_80pct"] > 0:
                ty = lp["dinh"]["toc_do_tong"] / ld["dinh"]["toc_do_tong"]
                if ty > 1.15:
                    gioi = ty
                    if kenh:
                        gioi = min(ty, float(kmax) / kenh)
                    so["nang_ram_loi_toi_da_x"] = round(gioi, 1)
                    tt.append("Neu RAM het nghen, viec quet chuoi dai co the nhanh toi ~x%.1f (tran do duoc: chuoi cache nhanh gap %.1f lan "
                              "chuoi RAM; nang kenh RAM %s->%d la dieu kien can)." % (gioi, ty, kenh or "?", kmax))
        else:
            tl.append("Cai gioi han la CPU (khong thay nghen RAM o muc do): them RAM cung loai khong lam nhanh hon, "
                      "them nhan CPU hay giam viec thua moi lam.")
    # ---- khuyen nghi nang RAM
    if khe and khe > 0 and kenh and kenh < kmax:
        th = (ram.get("thanh") or [{}])[0]
        them = min(khe, kmax - kenh)
        loai = "%s %s GB, %s MT/s%s%s" % (th.get("loai"), th.get("gb"), th.get("mt_s"), ", ECC" if th.get("ecc") else "",
                                          ", LRDIMM" if th.get("lrdimm") else (", RDIMM" if th.get("registered") else ""))
        buoc = "Them 1 thanh: %d -> %d kenh, bang thong ly thuyet gap %.1f lan" % (kenh, kenh + 1, (kenh + 1) / kenh)
        if them > 1:
            buoc += "; them du %d thanh: %d kenh, gap %.1f lan" % (them, kenh + them, (kenh + them) / kenh)
        kn.append({"viec": "Them RAM CUNG LOAI voi thanh dang co (%s; ma hang %s) vao khe KHAC KENH (xem so tay bo mach: khe vi tri 1 "
                           "cua moi kenh). %s. Khong tron RDIMM voi LRDIMM; chua chac thi gui anh nhan thanh dang co de chon dung loai."
                           % (loai, th.get("ma_hang"), buoc), "ai_lam": "chu_du_an", "can_phep": True})
        so["kenh_ram"] = {"dang_dung": kenh, "toi_da_goi_y": kenh + them, "toi_da_nen_tang": kmax}
    elif ram.get("khe_trong") is None:
        tt.append("Chua doc duoc so khe RAM / loai RAM (PowerShell khong tra ve): xem loi_powershell trong bao cao.")
    # ---- dia + pagefile
    dia, pf = (q.get("dia") or {}), (q.get("pagefile") or {})
    he = [o for o in dia.get("o", []) if str(o.get("o", "")).upper().startswith("C")]
    if he and he[0].get("trong_gb") is not None and he[0]["trong_gb"] < NGUONG["dia_vang_gb"]:
        hop("DO" if he[0]["trong_gb"] < NGUONG["dia_do_gb"] else "VANG")
        kn.append({"viec": "O %s con %.1f GB: don thu muc tam / backups / cache tester (xem muc mt5.gb_tester trong `b may quet`) hoac chuyen "
                           "du lieu sang o khac" % (he[0]["o"], he[0]["trong_gb"]), "ai_lam": "chu_du_an", "can_phep": True})
    hdd = [x for x in (dia.get("vat_ly") or []) if str(x.get("loai")) == "HDD"]
    if hdd and pf.get("tong_cap_phat_gb") is not None:
        kn.append({"viec": "File trang (pagefile): dat 1 file CO DINH tren o HDD moi (goi y %d GB, dau = toi da, khong de Windows tu co gian) "
                           "lam LUOI AN TOAN chong loi het bo nho (da xay ra 13/09). Khong lam bo nho lam viec: HDD cham ~100 lan SSD, neu "
                           "phai doc/ghi lien tuc thi may dung hinh. Giu file trang nho tren SSD. Xem tai_lieu/MAY_NHA_TOI_UU.md" % max(
                               32, min(64, int((hdd[0].get("gb") or 100) * 0.25))), "ai_lam": "chu_du_an", "can_phep": True})
    dd = d.get("dia") or []
    if dd:
        so["dia"] = [{"o": x.get("o"), "ghi_mbs": x.get("ghi_tuan_tu_mbs"), "iops": x.get("ghi_ngau_nhien_4k_iops"),
                      "loai_do_duoc": x.get("loai_do_duoc")} for x in dd if not x.get("loi")]
        cham = [x for x in so["dia"] if x.get("loai_do_duoc") and str(x["loai_do_duoc"]).startswith("cham")]
        if cham:
            tt.append("Dia cham (kieu HDD): %s - khong dat du lieu lich su tester / file trang chinh o day." % ", ".join(str(x["o"]) for x in cham))
    # ---- ke hoach dien
    if (q.get("ke_hoach_dien") or {}).get("can_chuyen_high_performance"):
        kn.append({"viec": "Ke hoach dien dang la %s: doi sang High performance (powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c) "
                           "de CPU khong ha xung / khong ngu nhan" % q["ke_hoach_dien"].get("ten"), "ai_lam": "chu_du_an", "can_phep": True})
    # ---- tran CPU
    kn.append({"viec": "Dat tran CPU cua he = 78 (giua dai 75-80): `b tran-cpu 78` (mac dinh trong code la 85)", "ai_lam": "may", "can_phep": False})
    # ---- MT5
    if cp or bp or ld:
        mt = so_mt5_toi_da(q, d)
        so["mt5"] = mt
        tl.append("MT5: tao toi da %d tai khoan demo (moi terminal 1 tai khoan); nhieu hon khong nhanh hon vi %s. "
                  "Neu XM cho 1 tai khoan dang nhap nhieu terminal thi chi can 1." % (mt["agent_toi_da"], {
                      "cpu": "CPU da day o %d viec" % mt["tran"]["cpu"], "ram": "RAM chi du nuoi %d agent" % mt["tran"]["ram"],
                      "bang_thong": "bang thong RAM chi nuoi noi ~%d agent nang" % (mt["tran"]["bang_thong"] or 0),
                      "dia": "dia chi du cho ~%d ban du lieu" % (mt["tran"]["dia"] or 0)}[mt["tran_nho_nhat_do"]]))
        tt.append("MT5 tran: %s; che do toi uu hoa: 1 terminal dung toi da %d agent. %s%s" % (
            mt["ly_do"], mt["agent_toi_da"],
            "" if mt["ram_moi_agent_do_that"] else "[RAM moi agent la GIA DINH %.1f GB: do lai khi co agent chay]. " % mt["ram_moi_agent_gb"],
            "" if mt["bang_thong_nguon"] == "do" else "[bang thong la uoc]"))
    return {"den": den, "tom_lai": tl, "tom_tat": tt, "so": so, "khuyen_nghi": kn}


def bao_cao_van_ban(q: dict, d: dict | None = None, m: dict | None = None, k: dict | None = None) -> str:
    """Bao cao LOI THUONG (chu du an khong doc duoc thuat ngu): TOM LAI truoc, roi viec can lam, roi con so. Ket qua day du o file json."""
    k = k or ket_luan(q, d, m)
    dong = ["BAO CAO MAY NHA  [%s]  %s" % (k["den"], _ts())]
    if k.get("tom_lai"):
        dong.append("TOM LAI:")
        dong += ["  - " + t for t in k["tom_lai"]]
    cu = [x for x in k["khuyen_nghi"] if x.get("ai_lam") == "chu_du_an"]
    if cu:
        dong.append("CHU DU AN CAN LAM:")
        dong += ["  %d. %s" % (i + 1, x["viec"]) for i, x in enumerate(cu)]
    may = [x for x in k["khuyen_nghi"] if x.get("ai_lam") == "may"]
    if may:
        dong.append("PHIEN NHA / MAY TU LAM:")
        dong += ["  - %s" % x["viec"] for x in may]
    dong.append("SO LIEU:")
    dong += ["  - " + t for t in k["tom_tat"]]
    return "\n".join(dong)


# ================================================================ GHI RA reports/ (an danh) + CLI
def ghi_bao_cao(q: dict | None, d: dict | None, m: dict | None, k: dict | None, thu_muc: Path | None = None) -> dict:
    t = thu_muc or BAO_CAO
    t.mkdir(parents=True, exist_ok=True)
    ra = {}
    for ten, v in (("quet", q), ("do", d), ("tinh_trang", m), ("ket_luan", k)):
        if v is not None:
            p = t / ("may_nha_%s.json" % ten)
            p.write_text(json.dumps(an_danh(v), ensure_ascii=False, indent=1), encoding="utf-8")
            ra[ten] = str(p)
    if q is not None:
        p = t / "may_nha_bao_cao.md"
        p.write_text(bao_cao_van_ban(an_danh(q), d, None, k) + "\n", encoding="utf-8")
        ra["md"] = str(p)
    return ra


def _co(argv: list[str], ten: str, mac_dinh=None):
    if ten in argv:
        i = argv.index(ten)
        if i + 1 < len(argv):
            return argv[i + 1]
    return mac_dinh


def main(argv: list[str]) -> int:
    lenh = argv[0] if argv else "bao-cao"
    con = argv[1:]
    if lenh in ("mau", "m"):
        print(json.dumps(an_danh(mau(nang="--nang" in con)), ensure_ascii=False, indent=1))
        return 0
    if lenh in ("quet", "q"):
        q = quet()
        k = ket_luan(q)
        print(bao_cao_van_ban(q, None, None, k))
        print("\n" + json.dumps(q, ensure_ascii=False, indent=1))
        ghi_bao_cao(q, None, None, k)
        return 0
    if lenh in ("bao-cao", "bc", "report"):
        q = quet()
        m = mau(nang=LA_WINDOWS)
        k = ket_luan(q, None, m)
        print(bao_cao_van_ban(q, None, m, k))
        tt = tom_tat_mau(doc_nhat_ky(24))
        if tt.get("so_mau", 0) > 1:
            print("24 GIO QUA (%d mau): CPU TB %s%% (p95 %s%%); %s%% thoi gian trong dai 75-80%%, %s%% DUOI dai (may ranh), %s%% tren dai; "
                  "RAM trong thap nhat %s GB; cam ket con lai thap nhat %s GB; MT5 chay %s%% thoi gian." % (
                      tt["so_mau"], tt["cpu_tb"], tt["cpu_p95"], tt["pct_thoi_gian_trong_dai"], tt["pct_thoi_gian_duoi_dai"],
                      tt["pct_thoi_gian_tren_dai"], tt["ram_trong_thap_nhat_gb"], tt["commit_con_lai_thap_nhat_gb"], tt["mt5_chay_pct"]))
        ghi_bao_cao(q, None, {"mau": m, "24h": tt}, k)
        return 0
    if lenh in ("giam-sat", "gs"):
        phut = float(con[0]) if con and con[0].replace(".", "").isdigit() else 10.0
        ck = float(con[1]) if len(con) > 1 and con[1].replace(".", "").isdigit() else 15.0
        r = giam_sat(phut, ck, in_ra=print)
        print(json.dumps(r["tom_tat"], ensure_ascii=False, indent=1))
        ghi_bao_cao(None, None, r["tom_tat"], None)
        return 0
    if lenh in ("do", "d", "bench"):
        nhanh = "--nhanh" in con
        tran = _so(_co(con, "--toi-da"))
        q = quet(voi_mt5=True)
        print("DO CO GIAN %s: %s luong, %s nhan vat ly ..." % ("(nhanh)" if nhanh else "", q["cpu"].get("luong"), q["cpu"].get("nhan_vat_ly")))
        d = do(nhanh=nhanh, ep="--ep" in con, tran=tran, q=q, in_ra=print)
        if d.get("trang_thai") != "DAT":
            print(d.get("ly_do"))
            ghi_bao_cao(q, d, None, None)
            return 1
        m = mau(nang=LA_WINDOWS)
        k = ket_luan(q, d, m)
        print(bao_cao_van_ban(q, d, m, k))
        ghi_bao_cao(q, d, {"mau": m}, k)
        return 0
    print("b may [bao-cao|quet|mau|do [--nhanh] [--ep] [--toi-da N]|giam-sat [PHUT] [CHU_KY_GIAY]]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
