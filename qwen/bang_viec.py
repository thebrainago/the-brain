# -*- coding: utf-8 -*-
"""bang_viec.py - Doc NHIEM_VU.json, giai phu thuoc, chon viec de phong.

## Vi sao la BANG chu khong phai mot prompt dai

Neu de qwen tu nghi ra viec tiep theo moi vong thi hai chuyen xay ra: no lap lai
viec da lam (khong co bo nho), va no tu nghi ra viec de lam thay vi viec quan
trong. Bang viec la BO NHO NGOAI cua no - thu tu, phu thuoc, va cong da co san,
qwen chi con phai DOC KET QUA va VIET.

## Uu tien: so nho lam truoc, va phu thuoc thang uu tien

Mot viec chi SAN SANG khi moi `phu_thuoc` cua no da XONG. Neu mot phu thuoc bi
LOI hay CHUA_DO_DUOC thi viec sau KHONG duoc coi la san sang - vi chay no se cho
ra mot con so dua tren dau vao hong, va do la cach mot ket qua sai di vao bao cao.
"""
from __future__ import annotations

import json
import time

from . import cau_hinh as CH


class BangViec:
    def __init__(self, duong=None) -> None:
        self.duong = duong or CH.BANG
        self.ds: list[dict] = []
        self.nap()

    def nap(self) -> list[dict]:
        d = json.loads(self.duong.read_text(encoding="utf-8-sig"))
        ds = d["viec"] if isinstance(d, dict) else d
        thay = {}
        for v in ds:
            if v["ma"] in thay:
                raise SystemExit("!! bang viec co hai viec trung ma: %s" % v["ma"])
            v.setdefault("lan", "NHE")
            v.setdefault("uu_tien", 5)
            v.setdefault("ngay", 1)
            v.setdefault("phu_thuoc", [])
            v.setdefault("lap", 1)
            v.setdefault("can_nguoi", False)
            v.setdefault("toi_da_phut", CH.nap()["toi_da_phut_mac_dinh"])
            thay[v["ma"]] = v
        # phu thuoc tro toi ma khong ton tai la loi cua nguoi viet bang
        for v in ds:
            for p in v["phu_thuoc"]:
                if p not in thay:
                    raise SystemExit("!! viec %s phu thuoc %s - khong co trong bang"
                                     % (v["ma"], p))
        self.ds = ds
        self.chi_muc = thay
        return ds

    def viec(self, ma: str) -> dict | None:
        return self.chi_muc.get(ma)

    # --------------------------------------------------------------- chon
    def san_sang(self, so_tay) -> list[dict]:
        """Viec du dieu kien phong, xep theo (uu_tien, ngay, thu tu file)."""
        xong = so_tay.da_xong()
        dang = so_tay.dang_chay()
        ra = []
        for i, v in enumerate(self.ds):
            ma = v["ma"]
            if ma in dang:
                continue
            if v.get("can_nguoi"):
                continue
            tt = so_tay.trang_thai(ma)
            da_chay = (so_tay.d["viec"].get(ma) or {}).get("so_lan_chay", 0)
            if tt == "XONG" and da_chay >= int(v["lap"]):
                continue
            if tt in ("LOI", "QUA_GIO"):
                if da_chay >= max(2, int(v["lap"])):
                    continue      # thu 2 lan roi thi thoi, de nguoi xem
                # Cho nguoi mot khoang truoc khi thu lai. Khong co khoang nay thi
                # mot viec hong 2 giay se chay lai ngay trong CUNG mot vong, va
                # hai dong log giong het nhau doc nhu he bi ket.
                luc_hong = (so_tay.d["viec"].get(ma) or {}).get("xong") or 0
                if time.time() - luc_hong < 180:
                    continue
            if not v.get("lenh"):
                continue          # viec soan_ma / can nguoi - khong tu chay
            if any(p not in xong for p in v["phu_thuoc"]):
                continue
            ra.append((v["uu_tien"], v["ngay"], i, v))
        ra.sort(key=lambda t: t[:3])
        return [t[3] for t in ra]

    def ket_treo(self, so_tay) -> list[dict]:
        """Viec dang cho NGUOI - in ra de chu du an thay, khong tu chay."""
        return [v for v in self.ds
                if v.get("can_nguoi") and so_tay.trang_thai(v["ma"]) != "XONG"]

    def chan_boi(self, ma: str, so_tay) -> list[str]:
        v = self.viec(ma) or {}
        xong = so_tay.da_xong()
        return [p for p in v.get("phu_thuoc", []) if p not in xong]

    # --------------------------------------------------------------- in
    def bang_chu(self, so_tay) -> str:
        bieu = {"XONG": "[x]", "DANG_CHAY": "[>]", "LOI": "[!]",
                "QUA_GIO": "[t]", "GIAN_DOAN": "[~]", "CHUA": "[ ]"}
        d = []
        for v in sorted(self.ds, key=lambda x: (x["ngay"], x["uu_tien"])):
            tt = so_tay.trang_thai(v["ma"])
            g = so_tay.d["viec"].get(v["ma"]) or {}
            cong = (g.get("cong") or {}).get("ket", "")
            chan = self.chan_boi(v["ma"], so_tay)
            ghi = ""
            if v.get("can_nguoi"):
                ghi = "  <- CAN NGUOI"
            elif chan and tt != "XONG":
                ghi = "  <- cho %s" % ", ".join(chan)
            elif g.get("giay"):
                ghi = "  %ss" % int(g["giay"])
            d.append("%s ngay%d uu%d %-6s %-22s %-9s %s%s" % (
                bieu.get(tt, "[ ]"), v["ngay"], v["uu_tien"], v["lan"],
                v["ma"], cong, v["ten"][:48], ghi))
        return "\n".join(d)
