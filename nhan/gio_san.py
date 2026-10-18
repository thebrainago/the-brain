# -*- coding: utf-8 -*-
"""gio_san.py - GIO MAY CHU theo san (sua D8, 18/10/2026).

XM: gio server = EET/EEST (NY + 7), doi ngay / rollover luc 00:00 server.
Exness: gio server = GMT+0 (khong doi gio mua he), rollover luc 17:00 New York = 21:00 GMT (mua he My) / 22:00 GMT (mua dong).
Code cu gia dinh moi san la gio XM (cam lenh 23h-02h, do gian doi ngay o 23/0/1h) -> tren Exness cua so do lech 2-3 tieng.
"""
from __future__ import annotations

#: (gio_cam_tu, gio_cam_den) gio SERVER, cam tu <= gio < den (vong qua 0h duoc), bao trum rollover ca mua he lan mua dong.
CAM_DOI_NGAY = {"XM": (23, 2), "EXNESS": (20, 0), "MAC_DINH": (23, 2)}
#: Gio server dung de do do gian spread doi ngay.
GIO_DOI_NGAY = {"XM": (23, 0, 1), "EXNESS": (20, 21, 22, 23), "MAC_DINH": (23, 0, 1)}


def ten_san(server_hoac_san: str | None) -> str:
    s = (server_hoac_san or "").upper()
    if "EXNESS" in s:
        return "EXNESS"
    if "XM" in s:
        return "XM"
    return "MAC_DINH"


def cam_doi_ngay(server_hoac_san: str | None) -> tuple[int, int]:
    return CAM_DOI_NGAY[ten_san(server_hoac_san)]


def gio_doi_ngay(server_hoac_san: str | None) -> tuple[int, ...]:
    return GIO_DOI_NGAY[ten_san(server_hoac_san)]
