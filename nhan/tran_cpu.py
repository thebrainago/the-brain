# -*- coding: utf-8 -*-
"""tran_cpu.py - MOT chO khai tran CPU, va moi viec nang deu tu ha theo no.

## Vi sao can

May nay la may CA NHAN cua chu du an, khong phai may chu. Chu du an choi game
tren no. Ngay 12/09 va 14/09 deu phai cat ngang phien lam viec de bao "ha CPU
xuong" - va ca hai lan cach xu li la sua tay: doi so luong, ha muc uu tien,
giet bot tien trinh. Lam tay thi lan sau lai phai lam lai.

File nay bien con so do thanh MOT cho khai bao ma moi viec nang deu doc:

    config/qwen.json -> `muc_tieu_cpu`     (dang co san, he `q` da dung)
    bien moi truong  -> `TRAN_CPU=80`      (ghi de cho mot lan chay)

va cho cac tien trinh con mot cach tu ha: goi `cho_neu_qua()` GIUA cac don vi
viec. Khong phai giua vong tinh - giua cac don vi, de khong bao gio cat ngang
mot phep do dang do dang.

## Vi sao khong dung muc uu tien Windows la du

Ha muc uu tien giup game khong giat, nhung **tong CPU van 95%** - may van nong,
quat van keu, va pin laptop van tut. Chu du an noi "de tran 80" nghia la con so
TONG, khong phai "nhuong khi can". Nen phai co cho do va cho ngu that.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(LAB))

CAU_HINH = LAB / "config" / "qwen.json"
TRAN_MAC_DINH = 80.0

_BO_NHO: dict = {"tran": None, "luc": 0.0}


def tran(lam_moi: bool = False) -> float:
    """Tran CPU hien hanh, %. Bien moi truong thang cau hinh, cau hinh thang mac dinh."""
    mt = os.environ.get("TRAN_CPU")
    if mt:
        try:
            return max(5.0, min(100.0, float(mt)))
        except ValueError:
            pass
    if not lam_moi and _BO_NHO["tran"] is not None and time.time() - _BO_NHO["luc"] < 30:
        return _BO_NHO["tran"]
    v = TRAN_MAC_DINH
    try:
        v = float(json.loads(CAU_HINH.read_text(encoding="utf-8")).get(
            "muc_tieu_cpu", TRAN_MAC_DINH))
    except Exception:
        pass
    v = max(5.0, min(100.0, v))
    _BO_NHO.update(tran=v, luc=time.time())
    return v


def dat_tran(pct: float) -> float:
    """Ghi tran moi vao `config/qwen.json`. Tra ve gia tri da ghi."""
    pct = max(5.0, min(100.0, float(pct)))
    d = {}
    try:
        d = json.loads(CAU_HINH.read_text(encoding="utf-8"))
    except Exception:
        pass
    d["muc_tieu_cpu"] = pct
    CAU_HINH.parent.mkdir(parents=True, exist_ok=True)
    tam = CAU_HINH.with_suffix(".json.tam")
    tam.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tam, CAU_HINH)
    _BO_NHO.update(tran=pct, luc=time.time())
    return pct


def cpu_hien_tai(do_giay: float = 0.3) -> float:
    try:
        import psutil
    except ImportError:
        return 0.0
    return float(psutil.cpu_percent(interval=do_giay))


def cho_neu_qua(nhip: float = 2.0, toi_da_giay: float = 120.0,
                do_giay: float = 0.3) -> float:
    """Ngu cho den khi CPU toan may xuong duoi tran. Tra ve so giay da ngu.

    Goi GIUA cac don vi viec, khong goi giua mot phep do. `nhip` co nhieu ngau
    nhien +-30% de N tien trinh khong cung thuc cung ngu mot luc roi dap manh.
    `toi_da_giay` la chan tren de mot may dang ket khong lam treo ca me viec.
    """
    t = tran()
    if t >= 99.0:
        return 0.0
    da_ngu = 0.0
    while da_ngu < toi_da_giay:
        if cpu_hien_tai(do_giay) <= t:
            return da_ngu
        n = nhip * random.uniform(0.7, 1.3)
        time.sleep(n)
        da_ngu += n
    return da_ngu


def so_luong_goi_y(lan_moi_luong: float = 1.0) -> int:
    """So tien trinh con nen mo de tong CPU khong vuot tran.

    `lan_moi_luong` = so LOI CPU ma mot tien trinh con an (1,0 neu don luong).
    Tru san phan nen dang chay, va luon giu lai it nhat mot luong cho nguoi dung.
    """
    try:
        import psutil
        tong = psutil.cpu_count(logical=True) or 4
    except ImportError:
        tong = os.cpu_count() or 4
    # Do NEN nhieu lan roi lay CAO NHAT, khong lay mot lat cat. Phan nen cua may
    # nay (he 24/7 cua chu du an) dao dong 23-56% - lay dung luc no thap thi tinh
    # ra thua luong, va tong se vuot tran ngay khi no len lai.
    nen = max(cpu_hien_tai(0.4) for _ in range(3))
    # Chua LE AN TOAN 30%: phan nen con dao dong tiep sau khi do xong, va vuot
    # tran mot lan lam nguoi dung giat game thi te hon la chay cham hon mot chut.
    con = max(0.0, tran() - nen) * 0.70 / 100.0 * tong
    return max(1, min(tong - 1, int(con / max(0.2, lan_moi_luong))))


def ha_uu_tien_minh() -> bool:
    """Ha muc uu tien cua CHINH tien trinh nay - de game cua nguoi dung luon thang.

    Tran CPU giu cho may khong nong; muc uu tien giu cho may khong GIAT. Can ca hai.
    """
    try:
        import psutil
        p = psutil.Process()
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 10)
        return True
    except Exception:
        return False


def _cli(argv: list) -> int:
    if argv and argv[0] == "dat":
        print(f"tran CPU -> {dat_tran(float(argv[1])):.0f}%")
        return 0
    print(f"tran CPU dang khai : {tran(lam_moi=True):.0f}%")
    print(f"CPU toan may bay gio: {cpu_hien_tai(1.0):.0f}%")
    print(f"so tien trinh nen mo: {so_luong_goi_y()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
