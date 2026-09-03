# -*- coding: utf-8 -*-
"""duyet_nguoi.py - DUYET NHU NGUOI: giu phien, co Referer, nhip khong deu.

Chu du an 03/09/2026: *"mql5 dang la nguon thuc chien nhat, hay thu moi cach
de truy cap duoc nguon nay, mo phong thao tac tay nguoi dung chu dung lam nhu
bot"*.

BA THU DA DO DUOC, theo thu tu phat hien:

  1. **DNS bi dau doc** (xem `nhan/dns_vuot.py`): `www.mql5.com` phan giai ra
     mot IPv6 cua ISP Viet Nam. Sau khi tro sang IP that (203.29.60.247, lay
     qua DNS-over-HTTPS) thi ket noi len duoc.

  2. **Khong phai chuyen header.** Thu bon bo header khac nhau, ket qua xen ke
     200 / 403 / 200 / 403 bat ke bo nao — ke ca bo chi co mot dong
     `User-Agent`. Header khong giai thich duoc mau do.

  3. **La NHIP.** Mot khach that mo trang, doc vai giay, roi moi bam trang
     sau, va luon mang theo `Referer` cua trang vua roi cung mot phien co
     cookie. Bo thu thap cu ban lien tiep 4 yeu cau khong cookie, khong
     Referer, cach nhau dung 1,5 giay — do la dau van cua may.

NEN O DAY:
  - MOT `requests.Session` -> cookie duoc giu qua cac lan goi, dung nhu trinh
    duyet.
  - `Referer` day theo CHUOI trang da di, khong bia.
  - Nhip NGAU NHIEN trong khoang, khong phai hang so. Nhip deu tam tap la thu
    de nhan ra nhat.
  - Vao trang CHU truoc khi vao trang sau (lay cookie phien), giong nguoi go
    dia chi roi bam link.

Day KHONG phai de vuot chan cua chu trang: mql5.com tra 200 cho khach thuong.
Muc dich la khong lam phien may chu bang mot chum yeu cau day dac, va khong bi
bo dem tan suat nham la tan cong.
"""
from __future__ import annotations

import random
import time

from nhan import dns_vuot as DV

def _co_brotli() -> bool:
    for ten in ("brotli", "brotlicffi"):
        try:
            __import__(ten)
            return True
        except ImportError:
            continue
    return False


#: Chi khai `br` khi THAT SU giai nen duoc.
_MA_NEN = "gzip, deflate, br" if _co_brotli() else "gzip, deflate"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")

#: Khoang nghi giua hai lan tai, tinh bang giay. Ngau nhien trong khoang.
NHIP = (4.0, 9.0)

_PHIEN = {}


def _dau_trang(referer: str | None) -> dict:
    h = {
        "User-Agent": UA,
        "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
                   "image/avif,image/webp,image/apng,*/*;q=0.8"),
        "Accept-Language": "en-US,en;q=0.9",
        # KHONG khai `br` khi may khong co bo giai nen brotli: may chu se nen
        # bang brotli va `r.text` tra ve RAC. Do that 03/09/2026: cung mot
        # trang, khai `br` -> 21.245 ky tu / 0 link; bo `br` -> 82.347 ky tu /
        # 40 link. HTTP van 200 ca hai lan, nen loi nay khong hien ra o ma
        # trang thai - no chi hien ra o SO LINK BOC DUOC.
        "Accept-Encoding": _MA_NEN,
        "Upgrade-Insecure-Requests": "1",
    }
    if referer:
        h["Referer"] = referer
    return h


class Khach:
    """Mot 'nguoi dung' voi phien rieng: cookie, lich su, nhip."""

    def __init__(self, goc: str = "https://www.mql5.com/", nhip=NHIP):
        import requests
        DV.bat()
        self.s = requests.Session()
        self.goc = goc
        self.nhip = nhip
        self.truoc: str | None = None
        self.lan_cuoi = 0.0
        self.da_vao_goc = False
        self.so_lan = 0
        self.so_403 = 0

    def _cho(self):
        con = random.uniform(*self.nhip) - (time.time() - self.lan_cuoi)
        if con > 0:
            time.sleep(con)

    def vao_goc(self):
        """Vao trang chu mot lan de nhan cookie phien, nhu nguoi go dia chi."""
        if self.da_vao_goc:
            return
        try:
            self.s.get(self.goc, headers=_dau_trang(None), timeout=30)
        except Exception:
            pass
        self.da_vao_goc = True
        self.lan_cuoi = time.time()

    def lay(self, url: str, thu_lai: int = 2) -> str | None:
        """Tai mot trang. Tra van ban hoac None. Tu nghi giua cac lan."""
        self.vao_goc()
        for lan in range(thu_lai + 1):
            self._cho()
            try:
                r = self.s.get(url, headers=_dau_trang(self.truoc), timeout=30)
            except Exception:
                self.lan_cuoi = time.time()
                continue
            self.lan_cuoi = time.time()
            self.so_lan += 1
            if r.status_code == 200 and r.text:
                self.truoc = url
                return r.text
            if r.status_code == 403:
                self.so_403 += 1
                # Bi dem tan suat -> lui lai lau hon, khong ban tiep ngay.
                time.sleep(8.0 * (lan + 1) + random.uniform(0, 4))
                continue
            return None
        return None

    def thong_ke(self) -> dict:
        return {"so_lan": self.so_lan, "so_403": self.so_403,
                "ty_le_403": round(self.so_403 / max(self.so_lan + self.so_403, 1), 3)}


def khach_cua(ten: str = "mql5") -> Khach:
    """Mot Khach dung chung cho ca phien chay - giu cookie xuyen cac lan goi."""
    if ten not in _PHIEN:
        _PHIEN[ten] = Khach()
    return _PHIEN[ten]
