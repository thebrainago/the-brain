# -*- coding: utf-8 -*-
"""cau_hinh.py - MOT noi giu moi hang so cua he qwen.

Vi sao khong rai hang so trong tung file: phien 08/09 bat dau bang mot he vua
sap vi qua tai. Muon chinh tai thi phai co MOT cho de chinh, va cho do phai doc
duoc bang mat thuong.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

QWEN = Path(__file__).resolve().parent
LAB = QWEN.parent
GOC = LAB.parent
BAO = LAB / "reports"
LOG = BAO / "qwen_log"
# Hai duong nay cho ghi de bang bien moi truong de chay THU tren bang gia,
# khong dung vao so that. `QWEN_BANG=... QWEN_SO_TAY=... q mot-vong`
SO_TAY = Path(os.environ.get("QWEN_SO_TAY") or (BAO / "qwen_so_tay.json"))
BANG = Path(os.environ.get("QWEN_BANG") or (QWEN / "NHIEM_VU.json"))
CO_DUNG = LAB / "DUNG_QWEN"          # cham file nay -> vong lap thoat em
CAU_HINH_NGOAI = LAB / "config" / "qwen.json"

PY = Path(sys.executable)
if not PY.exists():
    PY = Path(sys.executable)

MAC_DINH = {
    # --- dieu toc CPU ---------------------------------------------------
    "muc_tieu_cpu": 85.0,       # % TONG may, khong phai % cua rieng he nay
    "san_cpu": 55.0,            # duoi muc nay thi cho phep phong slot nhanh
    "chu_ky_do_giay": 5.0,      # nhip do CPU
    "cua_so_do": 6,             # so mau trung binh truot
    "giu_von_giay": 45.0,       # bao lau moi tin phep do thay cho suat dat truoc

    # --- lan (lane) ------------------------------------------------------
    #   nang = so LOI uoc tinh mot viec cua lan do an. Con so nay chi de
    #   CHONG VOT luc vua phong; sau `giu_von_giay` thi phep do that thay the.
    "tran_lan": {"CPU": 8, "LLM": 4, "MANG": 3, "TESTER": 1, "NHE": 6},
    "nang_lan": {"CPU": 2.0, "LLM": 1.2, "MANG": 0.8, "TESTER": 9.0, "NHE": 0.3},

    # --- mo hinh ----------------------------------------------------------
    "cc_switch_provider": "aibox",
    "base_url": "https://api.ai-box.vn/v1",   # THANG, khong qua cau noi 8317
    "model": "qwen3.7-flash",
    "model_du_phong": "qwen3.6-flash",
    "temperature": 0,
    "max_tokens": 4000,
    "timeout_giay": 180,
    "so_lan_thu_lai": 3,

    # --- vong lap ----------------------------------------------------------
    "nhip_vong_giay": 20.0,     # bao lau xet lai bang viec mot lan
    "toi_da_phut_mac_dinh": 240,
    "gio_bao_cao": 23,          # gio sinh bao cao nhap trong ngay
}


def nap() -> dict:
    c = dict(MAC_DINH)
    if CAU_HINH_NGOAI.exists():
        try:
            ngoai = json.loads(CAU_HINH_NGOAI.read_text(encoding="utf-8-sig"))
            for k, v in ngoai.items():
                if isinstance(v, dict) and isinstance(c.get(k), dict):
                    c[k].update(v)
                else:
                    c[k] = v
        except Exception as e:
            print("!! config/qwen.json khong doc duoc (%s) - dung mac dinh" % e)
    # bien moi truong de danh cho luc chay tay: QWEN_CPU=70 q
    if os.environ.get("QWEN_CPU"):
        try:
            c["muc_tieu_cpu"] = float(os.environ["QWEN_CPU"])
        except ValueError:
            pass
    return c


def bao_dam_thu_muc() -> None:
    LOG.mkdir(parents=True, exist_ok=True)
    BAO.mkdir(parents=True, exist_ok=True)
