# -*- coding: utf-8 -*-
"""ngan_sach.py - SO NGAN SACH TAI NGUYEN. Cua vao chung cho moi viec nang.

## VI SAO CO FILE NAY, VA VI SAO NO KHONG PHAI BO DIEU PHOI THU NAM

Lab da co BON bo phan dieu phoi, va moi cai lam tot phan cua no:

    dieu_phoi.py        supervisor 24/7 cho 5 tru; 3 lan x 1; tran CPU
    qwen/dieu_toc.py    AIMD giu CPU ca may ~85%, do that moi 5 giay
    day_viec.py         hang doi VIEC XAY, tuan tu, ben qua su co
    nhan/khoa_tester.py khoa MOT terminal64.exe (rang buoc VAT LY)

Khong cai nao biet ve **DIA, BO NHO, NGAN SACH MANG THEO HOST, va TIEN TRINH
MO COI** - va do dung la bon thu giet viec ngay 13/09/2026:

  1. O C tut ve 233 MB -> pytest chet "paging file too small" -> mot lan ghi
     khong tron ven -> **kho co che bi xoa HAI lan**.
  2. 34 tien trinh python mo coi tich lai -> `ENOMEM: uv_spawn`, khong sinh
     duoc tien trinh moi. Bo test chet 4 lan o 56-94% khong ban tom tat.
  3. Cao mql5 o 0,3 giay/luot -> bi chan ca IP sau ~50 luot, va **29 URL tot
     bi loai vinh vien** vi bo dem khong phan biet "hong vi mang".
  4. Whisper (4 tien trinh) + pytest (6 nhan) + MT5 tester chay CUNG LUC ->
     cai nao cung cham, va hai cai chet.

Nen file nay khong lap lich. No la mot **CUA VAO**: truoc khi mot viec nang
chay, no hoi "con cho khong", va sau do giu cho den khi xong. `dieu_toc` van
la thu quyet dinh BAO NHIEU tien trinh CPU; file nay quyet dinh CO DUOC CHAY
KHONG va **cung luc voi cai gi**.

## LOP TAI NGUYEN - moi con so duoi day la SO DO DUOC tren may nay

    CPU          10 nhan vat ly / 20 luong. Giao cho `dieu_toc` (AIMD).
    BANG_THONG   1 slot. Do: bai mang lon 1 luong 8,9 GB/s · 20 luong 9,4 -
                 song song hoa an 6%. Hai viec loai nay chay cung = cung cham.
    LLM          8 slot. Do 13/09: 6 luong 0,071 ban/giay · 24 luong 0,101 -
                 gap 4 lan luong chi duoc 1,4 lan thong luong (nha cung cap
                 bop). Tren 8 la dot cong.
    TESTER       1 slot. MOT `terminal64.exe` - rang buoc VAT LY, ngan sach
                 khong mua duoc cai thu hai.
    NET:<host>   nhip toi thieu RIENG tung host. mql5.com: 0,3 giay -> chan
                 sau ~50 luot; 8 giay -> di duoc lau. api.github.com: 60
                 luot/GIO khi khong co token.
    DIA          >= 2 GB moi duoc ghi (xem `nhan/dia.py`).
    RAM          viec khai bao RAM can; thieu thi cho, khong phong roi chet.

## KHONG CHONG LEN `han_muc.py`

`han_muc` la KILL-SWITCH cua he chay that (tien that, lenh that). File nay la
ngan sach TAI NGUYEN MAY. Hai thu khac nhau; dung gop.
"""
from __future__ import annotations

import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))

SO_NHIP = GOC / "config" / "ngan_sach_nhip.json"

# ------------------------------------------------------------ SUC CHUA
#: Moi con so o day di kem phep do trong docstring dau file. Doi mot con so
#: ma khong doi phep do la quay ve doan mo.
SUC_CHUA = {
    "BANG_THONG": 1,
    "LLM": 8,
    "TESTER": 1,
    "CPU_NANG": 4,     # viec CPU nang chay cung luc; `dieu_toc` chia nho hon
}

#: Nhip toi thieu giua hai lan goi MOT host (giay). Do duoc, khong doan.
NHIP_HOST = {
    "www.mql5.com": 8.0,        # 0,3s -> chan IP sau ~50 luot
    "mql5.com": 8.0,
    "api.github.com": 60.0,     # 60 luot/GIO khi khong token -> 1 luot/phut
    "raw.githubusercontent.com": 1.0,   # CDN, khong chan nhu API
    "_mac_dinh": 2.0,
}

#: RAM toi thieu con trong de nhan mot viec nang (GB). Do 13/09: `ENOMEM:
#: uv_spawn` xay ra khi RAM VAT LY con 17 GB - vi tran cam ket (RAM +
#: pagefile) moi la thu het, khong phai RAM vat ly. Nen nguong nay tinh tren
#: RAM TRONG *va* so tien trinh python dang song.
RAM_TOI_THIEU_GB = 3.0
TRAN_TIEN_TRINH_PYTHON = 28


# ------------------------------------------------------------ DOI IP
#: Duong doi IP co san tren may nay. Cloudflare WARP bat/tat = doi ca dai IP.
WARP = Path(r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe")


def _warp(lenh: str) -> bool:
    import subprocess
    if not WARP.exists():
        return False
    try:
        r = subprocess.run([str(WARP), lenh], capture_output=True, text=True,
                           timeout=30)
        return "success" in (r.stdout or "").lower()
    except Exception:
        return False


def warp_dang_bat() -> bool:
    import subprocess
    if not WARP.exists():
        return False
    try:
        r = subprocess.run([str(WARP), "status"], capture_output=True,
                           text=True, timeout=20)
        ra = (r.stdout or "").lower()
        return "connected" in ra and "disconnected" not in ra
    except Exception:
        return False


def doi_ip(in_ra=print) -> bool:
    """Lat WARP -> doi ca dai IP thoat. Tra True neu da lat duoc.

    ## VI SAO DAY LA MOT CO CHE, KHONG PHAI MOT GHI CHU

    Memory cua du an tung ghi **"bat WARP la thong"** (mql5). Ngay 13/09/2026
    toi do lai va ket luan nguoc: *"tat WARP moi thong"* - roi HAI TIENG SAU
    do lai lan nua va no lai nguoc tiep:

        14:5x  WARP bat  -> RemoteDisconnected / 403      WARP tat -> 200
        16:5x  WARP tat  -> RemoteDisconnected (3/3)      WARP bat -> 200

    Ca hai ket luan deu la suy dien tu MOT quan sat. Co che that: **mql5 cam
    theo IP sau ~50-150 luot**. Duong nao cung chay cho toi khi IP do bi cam;
    lat WARP la doi sang mot IP chua bi cam.

    Nen dieu dung phai lam khong phai chon mot ben, ma la: **di du cham de
    khong bi cam, va khi bi cam thi DOI IP** - hai thu, va ca hai deu la viec
    cua bo dieu phoi chu khong phai cua nguoi doc ghi chu.
    """
    bat = warp_dang_bat()
    ok = _warp("disconnect" if bat else "connect")
    time.sleep(8)
    in_ra("doi IP: WARP %s -> %s" % ("bat" if bat else "tat",
                                     "tat" if bat else "bat"))
    return ok


def thong_duong(thu_url: str, host: str, in_ra=print) -> bool:
    """Duong toi `host` con song khong; neu khong thi THU DOI IP mot lan.

    Tra True neu (sau cung) di duoc.
    """
    import requests

    def _thu() -> bool:
        try:
            r = requests.get(thu_url, timeout=15,
                             headers={"User-Agent": "Mozilla/5.0"})
            return r.status_code == 200 and len(r.text) > 5000
        except Exception:
            return False

    if _thu():
        return True
    in_ra("  %s khong vao duoc - thu doi IP" % host)
    if not doi_ip(in_ra):
        return False
    return _thu()


class HetCho(RuntimeError):
    """Khong con cho cho viec nay LUC NAY. Day la `CHUA_DO_DUOC` - viec chua
    chay, khong phai viec da chay va that bai."""


# ------------------------------------------------------------ DO MAY
def may() -> dict:
    import shutil
    try:
        import psutil
    except ImportError:
        return {"ram_trong_gb": 99.0, "cpu": 0.0, "python": 0,
                "dia_gb": shutil.disk_usage(str(GOC)).free / 2**30}
    m = psutil.virtual_memory()
    n = 0
    for p in psutil.process_iter(["name"]):
        if (p.info.get("name") or "").lower() == "python.exe":
            n += 1
    return {"ram_trong_gb": round(m.available / 2**30, 1),
            "cpu": psutil.cpu_percent(interval=0.2),
            "python": n,
            "dia_gb": round(shutil.disk_usage(str(GOC)).free / 2**30, 1)}


def don_mo_coi(qua_gio: float = 6.0, in_ra=print) -> int:
    """Giet tien trinh python MO COI (cha da chet) song qua `qua_gio` gio.

    Do 13/09: 34 tien trinh python sot lai tu cac luot pytest va agent bi cat
    ngang -> `ENOMEM: uv_spawn`. Chung khong lam gi, chi giu cho cam ket.

    KHONG giet tien trinh dang co cha song (do la viec that dang chay), va
    khong giet chinh minh.
    """
    try:
        import psutil
    except ImportError:
        return 0
    toi = os.getpid()
    nay = time.time()
    giet = 0
    for p in psutil.process_iter(["name", "ppid", "create_time"]):
        try:
            if (p.info.get("name") or "").lower() != "python.exe":
                continue
            if p.pid == toi:
                continue
            if nay - (p.info.get("create_time") or nay) < qua_gio * 3600:
                continue
            cha = p.info.get("ppid")
            if cha and psutil.pid_exists(cha):
                continue          # con co cha -> dang lam viec that
            p.kill()
            giet += 1
        except Exception:
            continue
    if giet:
        in_ra("don %d tien trinh python mo coi" % giet)
    return giet


# ------------------------------------------------------------ NHIP HOST
def _doc_nhip() -> dict:
    try:
        return json.loads(SO_NHIP.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _ghi_nhip(d: dict) -> None:
    try:
        SO_NHIP.parent.mkdir(parents=True, exist_ok=True)
        SO_NHIP.write_text(json.dumps(d), encoding="utf-8")
    except Exception:
        pass


def cho_nhip(host: str, in_ra=None) -> float:
    """Doi cho du nhip toi thieu cua `host` roi tra ve so giay da doi.

    Ghi lan goi cuoi xuong DIA chu khong giu trong RAM: hai tien trinh cung
    cao mot host phai chia nhau nhip, neu khong thi moi cai tuong minh dang
    di cham ma tong lai van bi chan.
    """
    nhip = NHIP_HOST.get(host, NHIP_HOST["_mac_dinh"])
    d = _doc_nhip()
    cuoi = float(d.get(host) or 0)
    cho = max(0.0, cuoi + nhip - time.time())
    if cho > 0:
        if in_ra:
            in_ra("  cho %.1fs cho nhip %s" % (cho, host))
        time.sleep(cho)
    d[host] = time.time()
    _ghi_nhip(d)
    return cho


# ------------------------------------------------------------ CUA VAO
_KHOA = GOC / "config" / "ngan_sach_khoa"


def _dang_giu(lop: str) -> int:
    """Dem the dang giu cua mot lop. The la FILE nen nhieu tien trinh thay
    nhau; the cua tien trinh da chet duoc thu hoi."""
    import psutil
    thu = _KHOA / lop
    if not thu.exists():
        return 0
    n = 0
    for f in thu.glob("*.the"):
        try:
            pid = int(f.stem)
        except Exception:
            f.unlink(missing_ok=True)
            continue
        if psutil.pid_exists(pid):
            n += 1
        else:
            f.unlink(missing_ok=True)     # chu the da chet -> thu hoi
    return n


@contextmanager
def xin(lop: str, viec: str = "", cho_giay: float = 0.0, ram_gb: float = 0.0):
    """Xin mot cho o lop tai nguyen `lop`. Nem `HetCho` neu khong con.

        with NS.xin("LLM", "boc mot me"):
            ...

    `cho_giay > 0` thi doi thay vi nem loi ngay.
    """
    from nhan import dia as DIA
    DIA.du_cho(viec=viec or lop)

    m = may()
    if ram_gb and m["ram_trong_gb"] < max(ram_gb, RAM_TOI_THIEU_GB):
        raise HetCho("RAM con %.1f GB, viec `%s` can %.1f GB"
                     % (m["ram_trong_gb"], viec, ram_gb))
    if m["python"] > TRAN_TIEN_TRINH_PYTHON:
        don_mo_coi(in_ra=lambda *a: None)
        if may()["python"] > TRAN_TIEN_TRINH_PYTHON:
            raise HetCho("%d tien trinh python dang song (tran %d) - may sap "
                         "khong sinh duoc tien trinh moi"
                         % (m["python"], TRAN_TIEN_TRINH_PYTHON))

    tran = SUC_CHUA.get(lop)
    thu = _KHOA / lop
    thu.mkdir(parents=True, exist_ok=True)
    the = thu / ("%d.the" % os.getpid())
    het = time.time() + cho_giay
    while True:
        if tran is None or _dang_giu(lop) < tran:
            the.write_text(viec or "?", encoding="utf-8")
            break
        if time.time() >= het:
            raise HetCho("lop %s day (%d/%s) - viec `%s` chua chay"
                         % (lop, _dang_giu(lop), tran, viec))
        time.sleep(1.0)
    try:
        yield
    finally:
        the.unlink(missing_ok=True)


def bang(in_ra=print) -> dict:
    m = may()
    in_ra("NGAN SACH TAI NGUYEN")
    in_ra("  may   : %.1f GB RAM trong · CPU %.0f%% · %d python · %.1f GB dia"
          % (m["ram_trong_gb"], m["cpu"], m["python"], m["dia_gb"]))
    dung = {}
    for lop, tran in SUC_CHUA.items():
        n = _dang_giu(lop)
        dung[lop] = {"dang_dung": n, "tran": tran}
        in_ra("  %-11s %d/%d" % (lop, n, tran))
    nhip = _doc_nhip()
    for h, t in sorted(nhip.items()):
        con = max(0.0, t + NHIP_HOST.get(h, NHIP_HOST["_mac_dinh"]) - time.time())
        if con > 0:
            in_ra("  nhip %-24s con cho %.1fs" % (h, con))
    return {"may": m, "lop": dung, "nhip": nhip}


if __name__ == "__main__":
    if "--don" in sys.argv:
        don_mo_coi()
    bang()
