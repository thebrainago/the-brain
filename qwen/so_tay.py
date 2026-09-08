# -*- coding: utf-8 -*-
"""so_tay.py - Bo nho ben ngoai cua he: viec nao xong, cong cham gi, qwen viet gi.

He nay chay NHIEU NGAY va bi tat giua chung la chuyen binh thuong (mat dien, may
khoi dong lai, chu du an bam Ctrl-C). Nen moi thay doi trang thai deu ghi xuong
dia NGAY, va lan chay sau doc lai file nay de biet minh dang o dau.

## Ghi de tren Windows

`os.replace` len mot file dang bi tien trinh khac MO (watchdog, OneDrive, trinh
soan) nem `PermissionError` - va da co mot vong 24/7 chet vi dung chuyen do. Nen
`_ghi()` thu lai 5 lan roi moi chiu thua, va thua thi ghi ra file `.moi` chu
khong lam mat ban cu.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from . import cau_hinh as CH

RONG = {"phien": "", "bat_dau": 0.0, "viec": {}, "nhat_ky": [], "de_xuat": [],
        "moc": {}, "ngay_da_mo": []}


def _ghi(d: dict, dich: Path) -> bool:
    dich.parent.mkdir(parents=True, exist_ok=True)
    # Ten tam phai DUY NHAT theo luong: vong lap chinh va luong nhan xet cua qwen
    # cung ghi so tay. Mot ten tam co dinh thi hai luong dam vao cung mot file va
    # ban ghi ra la ban tron cua hai trang thai - hong im lang, dung kieu hong
    # kho truy nhat.
    tam = dich.with_suffix("%s.%d.tam" % (dich.suffix, threading.get_ident()))
    tam.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    for lan in range(5):
        try:
            os.replace(tam, dich)
            return True
        except PermissionError:
            time.sleep(0.4 * (lan + 1))
    try:
        os.replace(tam, dich.with_suffix(".moi.json"))
    except Exception:
        pass
    return False


class SoTay:
    def __init__(self, duong: Path | None = None) -> None:
        self.duong = duong or CH.SO_TAY
        self.d = dict(RONG)
        # Vong lap chinh ghi trang thai viec; luong nhan xet cua qwen ghi nhat ky.
        # Hai luong, mot file -> phai khoa, khong thi ban ghi ra la ban tron.
        self.khoa = threading.RLock()
        self.nap()

    def nap(self) -> dict:
        if self.duong.exists():
            try:
                cu = json.loads(self.duong.read_text(encoding="utf-8-sig"))
                self.d = {**RONG, **cu}
            except Exception as e:
                print("!! so tay hong (%s) - bat dau so moi, ban cu giu lai" % e)
                try:
                    self.duong.rename(self.duong.with_suffix(".hong.json"))
                except Exception:
                    pass
        if not self.d.get("bat_dau"):
            self.d["bat_dau"] = time.time()
            self.d["phien"] = time.strftime("%Y-%m-%d %H:%M")
        return self.d

    def luu(self) -> None:
        with self.khoa:
            _ghi(self.d, self.duong)

    # ------------------------------------------------------------ viec
    def trang_thai(self, ma: str) -> str:
        return (self.d["viec"].get(ma) or {}).get("trang_thai", "CHUA")

    def dat(self, ma: str, **kw) -> None:
        with self.khoa:
            v = self.d["viec"].setdefault(ma, {"ma": ma, "trang_thai": "CHUA",
                                               "so_lan_chay": 0})
            v.update(kw)
            self.luu()

    def bat_dau(self, ma: str, lan: str, lenh: list) -> None:
        v = self.d["viec"].setdefault(ma, {"ma": ma, "so_lan_chay": 0})
        with self.khoa:
            v.update({"trang_thai": "DANG_CHAY", "lan": lan, "lenh": lenh,
                      "bat_dau": time.time(), "xong": None, "ma_thoat": None})
            v["so_lan_chay"] = v.get("so_lan_chay", 0) + 1
            self.luu()

    def ket_thuc(self, ma: str, ma_thoat: int, cong: dict, log: str) -> None:
        v = self.d["viec"].setdefault(ma, {"ma": ma})
        with self.khoa:
            v.update({"trang_thai": "XONG" if ma_thoat == 0 else "LOI",
                      "xong": time.time(), "ma_thoat": ma_thoat,
                      "cong": cong, "log": log})
            v["giay"] = round((v["xong"] - v.get("bat_dau", v["xong"])), 1)
            self.luu()

    def da_xong(self) -> set:
        return {m for m, v in self.d["viec"].items() if v.get("trang_thai") == "XONG"}

    def dang_chay(self) -> set:
        return {m for m, v in self.d["viec"].items()
                if v.get("trang_thai") == "DANG_CHAY"}

    # ------------------------------------------------------------ nhat ky
    def ghi_nhat_ky(self, ma: str, van: str, ai: str = "qwen") -> None:
        with self.khoa:
            self.d["nhat_ky"].append({"luc": time.strftime("%Y-%m-%d %H:%M:%S"),
                                      "ma": ma, "ai": ai, "van": van})
            self.d["nhat_ky"] = self.d["nhat_ky"][-500:]
            self.luu()

    def de_xuat(self, viec: dict, boi: str = "qwen") -> None:
        viec = dict(viec)
        viec["_boi"] = boi
        viec["_luc"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.khoa:
            self.d["de_xuat"].append(viec)
            self.luu()

    # ------------------------------------------------------------ moc so
    def dat_moc(self, ten: str, gia_tri) -> None:
        with self.khoa:
            self.d["moc"][ten] = {"gia_tri": gia_tri, "luc": time.time()}
            self.luu()

    def moc(self, ten: str, mac_dinh=None):
        return (self.d["moc"].get(ten) or {}).get("gia_tri", mac_dinh)


def don_treo(st: SoTay) -> int:
    """Viec con o DANG_CHAY tu lan chay truoc = tien trinh da chet cung may.

    Khong duoc coi la XONG (se bo qua mat), cung khong duoc coi la CHUA (mat dau
    vet). Danh dau GIAN_DOAN de vong sau chay lai va nguoi doc thay duoc.
    """
    n = 0
    for ma in list(st.dang_chay()):
        st.dat(ma, trang_thai="GIAN_DOAN",
               ghi_chu="con DANG_CHAY khi he khoi dong lai - tien trinh da chet")
        n += 1
    return n
