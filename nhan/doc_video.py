# -*- coding: utf-8 -*-
"""doc_video.py - VIDEO -> VAN BAN, de video di chung mot duong voi van xuoi.

## Van de

`hethong.txt` neu: *"chuyen doi video thanh co che, hinh anh thanh co che"*.
Do 11/09/2026: khong co khau nao. Va khi nhin ky kho thi lo ra hai chuyen:

  - 109 tai lieu mang nhan `loai='video'` **khong phai video** - chung la trang
    KET QUA TIM KIEM cua YouTube (`/results?search_query=...`). Rut video ID tu
    noi dung da luu: **0**, vi trang tim kiem can JavaScript moi hien ket qua.
  - Nhung **111 tai lieu KHAC lai la trang video that** (`watch?v=`) - chi la
    chung khong duoc gan nhan `video`. Nguyen lieu co san, chi la dem nham cho.

## Cach lam - va vi sao KHONG dung whisper truoc

YouTube da co phu de tu dong cho gan het video. Lay phu de:
  - khong can tai audio, khong can `ffmpeg` (may nay khong co ffmpeg)
  - nhanh hon vai chuc lan
  - va do la CHU cua chinh tac gia hoac cua may Google, deu tot hon whisper
    chay tren mot may khong co GPU

`faster_whisper` co san trong may va duoc giu lam duong LUI cho video khong co
phu de - nhung no can ffmpeg nen hien tai chua bat.

## Ranh gioi

Module nay CHI bien video thanh van ban va ghi vao `noi_dung`. Viec bien van ban
thanh co che van la cua `doc_hieu` - mot duong, mot bo luat, mot cho de sua.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

#: Nhan RIENG cho ban phu de. KHONG dung lai `video`: nhan do da bi cac trang
#: HTML cu chiem (71 ban, deu la trang ket qua tim kiem), va lan chay dau tien
#: cua module nay da bo qua nham 23 video THAT vi tuong chung "da co ban doc".
KIEU = "video_phu_de"

NGON_NGU = ("en", "en-orig", "en-US", "en-GB", "vi")
#: Xin `json3` truoc: no la JSON nen khong phai bo dinh dang, va khong dinh bay
#: cua VTT (the <c> long nhau lam tach cau sai).
UU_TIEN_DINH_DANG = ("json3", "srv3", "srv1", "vtt")


def _yt():
    import yt_dlp
    return yt_dlp.YoutubeDL({
        "skip_download": True, "writesubtitles": True, "writeautomaticsub": True,
        "subtitleslangs": list(NGON_NGU), "quiet": True, "no_warnings": True,
        "socket_timeout": 25, "retries": 2,
    })


def _chon_phu_de(info: dict) -> tuple[str, str] | None:
    """-> (url, dinh_dang). Uu tien phu de NGUOI VIET hon phu de may."""
    for kho in (info.get("subtitles") or {}, info.get("automatic_captions") or {}):
        for lg in NGON_NGU:
            ds = kho.get(lg)
            if not ds:
                continue
            for dd in UU_TIEN_DINH_DANG:
                for f in ds:
                    if f.get("ext") == dd and f.get("url"):
                        return f["url"], dd
    return None


def _doc_json3(vb: str) -> str:
    d = json.loads(vb)
    cau = []
    for e in d.get("events") or []:
        t = "".join(s.get("utf8", "") for s in (e.get("segs") or []))
        t = t.strip()
        if t:
            cau.append(t)
    return " ".join(cau)


def _doc_vtt(vb: str) -> str:
    ra, thay = [], set()
    for dong in vb.splitlines():
        dong = dong.strip()
        if (not dong or "-->" in dong or dong.startswith(("WEBVTT", "Kind:", "Language:"))
                or dong.isdigit()):
            continue
        dong = re.sub(r"<[^>]+>", "", dong).strip()
        # Phu de tu dong lap lai dong truoc de lam hieu ung cuon - bo trung.
        if dong and dong not in thay:
            thay.add(dong)
            ra.append(dong)
    return " ".join(ra)


def phu_de(url: str) -> dict:
    """-> {nhan, van_ban, tieu_de, giay, ly_do}"""
    import requests
    try:
        with _yt() as y:
            info = y.extract_info(url, download=False)
    except Exception as e:
        return {"nhan": False, "ly_do": f"{type(e).__name__}: {str(e)[:140]}"}
    chon = _chon_phu_de(info)
    if not chon:
        return {"nhan": False, "ly_do": "khong co phu de (can duong lui whisper + ffmpeg)",
                "tieu_de": info.get("title"), "giay": info.get("duration")}
    u, dd = chon
    try:
        r = requests.get(u, timeout=30)
        r.raise_for_status()
        vb = _doc_json3(r.text) if dd in ("json3",) else _doc_vtt(r.text)
    except Exception as e:
        return {"nhan": False, "ly_do": f"tai phu de hong: {type(e).__name__}"}
    if len(vb) < 200:
        return {"nhan": False, "ly_do": f"phu de qua ngan ({len(vb)} ky tu)"}
    return {"nhan": True, "ly_do": "", "van_ban": vb, "dinh_dang": dd,
            "tieu_de": info.get("title") or "", "giay": info.get("duration"),
            "kenh": info.get("uploader") or ""}


def _da_co(van_tay: str) -> bool:
    return SO.mot("SELECT id FROM noi_dung WHERE van_tay = ?", van_tay) is not None


def ghi(url: str, kq: dict) -> bool:
    """Ghi ban doc vao `noi_dung` de `doc_hieu` xu ly nhu moi van xuoi khac."""
    vb = f"{kq.get('tieu_de','')}\n\n{kq['van_ban']}"
    vt = SO.van_tay("video", url, vb[:4000])
    if _da_co(vt):
        return False
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,so_ky_tu,"
            "so_ky_tu_goc,van_ban,luc,da_boc) VALUES(NULL,?,?,?,?,?,?,?,?,0)",
            (vt, url, KIEU, f"phu_de:{kq.get('dinh_dang')}", len(vb), len(vb),
             vb, SO.bay_gio()))
    return True


def trang_video_trong_kho(gioi_han: int | None = None) -> list[str]:
    """URL video THAT trong kho. Khong loc theo `loai` - xem docstring dau file."""
    q = ("SELECT DISTINCT url FROM tai_lieu WHERE url LIKE '%watch?v=%' "
         "OR url LIKE '%youtu.be/%' ORDER BY id")
    u = [r["url"] for r in SO.nhieu(q)]
    return u[:gioi_han] if gioi_han else u


def mot_luot(gioi_han: int = 20) -> dict:
    dem = {"thu": 0, "ghi_moi": 0, "da_co": 0, "khong_phu_de": 0, "loi": 0}
    ly_do = []
    for u in trang_video_trong_kho():
        if dem["thu"] >= gioi_han:
            break
        # bo qua nhanh cai da co ban doc
        if SO.mot("SELECT id FROM noi_dung WHERE url = ? AND kieu = ?", u, KIEU):
            dem["da_co"] += 1
            continue
        dem["thu"] += 1
        kq = phu_de(u)
        if kq["nhan"]:
            dem["ghi_moi"] += 1 if ghi(u, kq) else 0
        elif "phu de" in (kq.get("ly_do") or ""):
            dem["khong_phu_de"] += 1
        else:
            dem["loi"] += 1
            if len(ly_do) < 5:
                ly_do.append(kq.get("ly_do"))
    dem["ly_do_loi"] = ly_do
    return dem


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(json.dumps(mot_luot(n), ensure_ascii=False, indent=1))
