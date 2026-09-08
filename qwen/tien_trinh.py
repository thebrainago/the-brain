# -*- coding: utf-8 -*-
"""tien_trinh.py - Phong mot viec thanh mot TIEN TRINH RIENG, khong phai mot luong.

## Vi sao tien trinh chu khong phai luong

Ba ly do, ca ba deu do duoc tren may nay:

1. **Cach ly khi sap.** He vua sap vi qua tai. Mot viec nghen bo nho hay nem
   ngoai le trong tien trinh rieng thi vong lap dieu phoi van song va van ghi
   duoc so tay; trong mot luong thi no keo ca he di theo.
2. **Do duoc va giet duoc.** Co PID nen `psutil` do duoc CPU that cua no, va
   qua gio thi giet duoc ca cay con (terminal64 de lai tien trinh con).
3. **GIL.** Nua viec trong bang la tinh toan numpy/pandas thuan.

## Do uu tien va tran luong con

Moi tien trinh con chay o BELOW_NORMAL: he nay chay nhieu NGAY nen khong duoc
lam may giat khi chu du an dang dung. Va dat OMP/MKL ve 1 luong cho lan CPU -
neu khong thi 6 tien trinh x 20 luong BLAS = 120 luong tren 20 loi, va do la
cach nhanh nhat de bien 85% thanh 100% nghen.
"""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import psutil

from . import cau_hinh as CH

DUOI_BINH_THUONG = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x00004000)
NHOM_MOI = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)


class Viec:
    """Mot viec dang chay: giu Popen, file log, han gio."""

    def __init__(self, v: dict, c: dict) -> None:
        self.v = v
        self.ma = v["ma"]
        self.lan = v["lan"]
        self.c = c
        self.bat_dau = time.time()
        self.han = self.bat_dau + float(v.get("toi_da_phut", 240)) * 60
        CH.bao_dam_thu_muc()
        self.log = CH.LOG / ("%s.log" % self.ma)
        self.fh = open(self.log, "w", encoding="utf-8", errors="replace")
        self.p = subprocess.Popen(self.lenh(), cwd=str(CH.LAB), env=self.moi_truong(),
                                  stdout=self.fh, stderr=subprocess.STDOUT,
                                  creationflags=DUOI_BINH_THUONG | NHOM_MOI)

    # ------------------------------------------------------------------
    def lenh(self) -> list[str]:
        l = list(self.v["lenh"])
        # ["_x.py", "ARG"] -> python -X utf8 _x.py ARG ; ["-c", "..."] giu nguyen
        return [str(CH.PY), "-X", "utf8", *l]

    def moi_truong(self) -> dict:
        e = dict(os.environ)
        e["PYTHONIOENCODING"] = "utf-8"
        e["PYTHONUTF8"] = "1"
        e["QWEN_VIEC"] = self.ma
        if self.lan in ("CPU", "NHE"):
            for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                      "NUMEXPR_NUM_THREADS"):
                e[k] = "1"
        return e

    # ------------------------------------------------------------------
    def con_chay(self) -> bool:
        return self.p.poll() is None

    def qua_gio(self) -> bool:
        return time.time() > self.han

    def loi_dang_an(self) -> float:
        """CPU that cua ca cay tien trinh, quy ra so LOI."""
        try:
            pr = psutil.Process(self.p.pid)
            pc = pr.cpu_percent(interval=None)
            for con in pr.children(recursive=True):
                try:
                    pc += con.cpu_percent(interval=None)
                except psutil.Error:
                    pass
            return pc / 100.0
        except psutil.Error:
            return 0.0

    def giet(self) -> None:
        """Giet ca cay - terminal64 de lai tien trinh con neu chi giet cha."""
        try:
            pr = psutil.Process(self.p.pid)
            for con in pr.children(recursive=True):
                try:
                    con.kill()
                except psutil.Error:
                    pass
            pr.kill()
        except psutil.Error:
            pass

    def dong(self) -> tuple[int, str]:
        try:
            self.fh.close()
        except Exception:
            pass
        ma_thoat = self.p.poll()
        if ma_thoat is None:
            ma_thoat = -9
        return int(ma_thoat), duoi_log(self.log)


def duoi_log(p: Path, so_ky_tu: int = 6000) -> str:
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return t[-so_ky_tu:]
