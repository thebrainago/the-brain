# -*- coding: utf-8 -*-
"""nguong.py - MOT CHO DUY NHAT doc nguong cua chu du an (config/nguong.json).

18/10/2026 (chu du an): truoc day cap 80/10 nam o 4 cho khong dung chung mot nguon (cong.py doc json; cham_diem.py,
sinh_viec.py, chay_lai_tren_san.py viet cung). Nay moi noi goi `nguong.tang(...)`.

Hai tang (khoa `nguong_chuoi` trong json):
  - "loc_python": sut giam < 65 % VA lai > 15 %/nam, sau phi, DO O LOT THAT (co ky quy, stop-out) -> loc ung vien Python
    truoc khi dua sang MT5. So sanh CHAT (<, >).
  - "cuoi": sut giam <= 80 % VA lai >= 10 %/nam (chuan goc 17/10) -> phan xu cuoi (MT5 / demo). So sanh LONG (<=, >=).
  - "cot_loi": ten cu cua tang cuoi (khoa goc `lai_nam_toi_thieu_pct` / `sut_giam_toi_da_pct`, cong.py van doc).

NHAN LOT TUYEN TINH (`lai_o_dd`) chi la NHAN THAM KHAO: phep nhan lot sai voi DCA, martingale, khong SL vi ky quy,
stop-out va lot_max doi phi tuyen. Khong dung no de loai hay chon.
"""
from __future__ import annotations

import json
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
TEP = GOC / "config" / "nguong.json"

MAC_DINH = {
    "loc_python": {"sut_giam_toi_da_pct": 65.0, "lai_nam_toi_thieu_pct": 15.0, "kieu_do": "lot_that",
                   "cam_stop_out": True, "so_sanh": "chat"},
    "cuoi": {"sut_giam_toi_da_pct": 80.0, "lai_nam_toi_thieu_pct": 10.0, "kieu_do": "lot_that",
             "cam_stop_out": True, "so_sanh": "long"},
}
_DEM: dict = {}


def doc(tep: Path | None = None) -> dict:
    """Ca file json (dem theo mtime). File hong / thieu -> {} (dung MAC_DINH)."""
    p = Path(tep or TEP)
    try:
        k = (str(p), p.stat().st_mtime_ns)
    except OSError:
        return {}
    if k not in _DEM:
        try:
            _DEM.clear()
            _DEM[k] = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return _DEM[k]


def tang(ten: str = "cuoi", tep: Path | None = None) -> dict:
    """-> {sut_giam_toi_da_pct, lai_nam_toi_thieu_pct, kieu_do, cam_stop_out, so_sanh}."""
    d = doc(tep)
    if ten == "cot_loi":
        ten = "cuoi"
    ra = dict(MAC_DINH.get(ten) or MAC_DINH["cuoi"])
    ra.update(((d.get("nguong_chuoi") or {}).get(ten) or {}))
    if ten == "cuoi" and "nguong_chuoi" not in d:
        # file cu chi co hai khoa goc
        if "lai_nam_toi_thieu_pct" in d:
            ra["lai_nam_toi_thieu_pct"] = float(d["lai_nam_toi_thieu_pct"])
        if "sut_giam_toi_da_pct" in d:
            ra["sut_giam_toi_da_pct"] = float(d["sut_giam_toi_da_pct"])
    ra["ten"] = ten
    return ra


def lai_toi_thieu(ten: str = "cuoi") -> float:
    return float(tang(ten)["lai_nam_toi_thieu_pct"])


def sut_giam_toi_da(ten: str = "cuoi") -> float:
    return float(tang(ten)["sut_giam_toi_da_pct"])


def dat(lai_pct_nam: float | None, sut_giam_pct: float | None, ten: str = "loc_python",
        so_stop_out: int = 0, chay: bool = False) -> dict:
    """Phan xu O LOT THAT. -> {dat, ly_do[], tang}. Thieu so -> dat=False, ly_do CHUA_DO_DUOC."""
    t = tang(ten)
    ly = []
    if lai_pct_nam is None or sut_giam_pct is None:
        return {"dat": False, "ly_do": ["CHUA_DO_DUOC"], "tang": t["ten"]}
    dd, lai = abs(float(sut_giam_pct)), float(lai_pct_nam)
    chat = t.get("so_sanh") == "chat"
    ok_dd = dd < t["sut_giam_toi_da_pct"] if chat else dd <= t["sut_giam_toi_da_pct"]
    ok_lai = lai > t["lai_nam_toi_thieu_pct"] if chat else lai >= t["lai_nam_toi_thieu_pct"]
    if not ok_dd:
        ly.append("sut giam %.1f%% %s %.0f%%" % (dd, ">=" if chat else ">", t["sut_giam_toi_da_pct"]))
    if not ok_lai:
        ly.append("lai %.1f%%/nam %s %.0f%%" % (lai, "<=" if chat else "<", t["lai_nam_toi_thieu_pct"]))
    if chay:
        ly.append("CHAY TAI KHOAN")
    if t.get("cam_stop_out", True) and so_stop_out:
        ly.append("cham stop-out %d lan" % so_stop_out)
    return {"dat": not ly, "ly_do": ly, "tang": t["ten"]}


def lai_o_dd(lai_pct_nam: float, sut_giam_pct: float, ten: str = "cuoi") -> float | None:
    """NHAN THAM KHAO: lai %/nam neu nhan lot TUYEN TINH toi muc sut giam cua tang. Sai voi DCA / khong SL."""
    if not sut_giam_pct:
        return None
    return float(lai_pct_nam) * sut_giam_toi_da(ten) / abs(float(sut_giam_pct))


def dat_tuyen_tinh(net: float, lai_pct_nam: float, sut_giam_pct: float | None, ten: str = "cuoi") -> bool:
    """Cach cu (17/10) cho so MT5 lot co dinh: lai > 0 va lai o muc lot cho sut giam = tran >= muc. NHAN, khong phai lot that."""
    o = lai_o_dd(lai_pct_nam, sut_giam_pct, ten) if sut_giam_pct else None
    return bool(net > 0 and (o is None or o >= lai_toi_thieu(ten)))
