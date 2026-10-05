# -*- coding: utf-8 -*-
"""guong_dsl.py - lat khai bao MUA thanh BAN BANG MAY (khong de LLM lat: 05/10 model re lat sai nghia, giu nguyen dieu kien).
Chi lat khi MOI dieu kien thuoc dang an toan; con lai tra None (khong doan). Khong chay engine."""
from __future__ import annotations

import copy

_PHEP = {"<": ">", ">": "<", "<=": ">=", ">=": "<=", "cheo_len": "cheo_xuong", "cheo_xuong": "cheo_len"}
_DOI_TEN = {"cao_nhat_cua_cac": "thap_nhat_cua_cac", "thap_nhat_cua_cac": "cao_nhat_cua_cac", "cao_nhat": "thap_nhat", "thap_nhat": "cao_nhat"}
# chi bao co khoang co dinh: hang c -> (cuc - c); doi dau neu khong bien
_LAT_HANG = {"rsi": lambda c: 100 - c, "stochastic": lambda c: 100 - c, "ibs": lambda c: 1 - c, "zscore": lambda c: -c, "cci": lambda c: -c,
             "dong_luong": lambda c: -c, "doi": lambda c: -c, "doi_pct": lambda c: -c, "do_lech": None}
_AN_TOAN_VE = {"gia", "ema", "sma", "wma", "smma", "tb", "supertrend", "donchian", "vwap", "cao_nhat_cua_cac", "thap_nhat_cua_cac",
               "cao_nhat", "thap_nhat"}   # keltner / bollinger / ichimoku: kenh tren hay duoi khong nam trong khai bao -> khong lat
_KHONG_LAT = {"adx", "atr", "bien_do", "phan_vi", "phuong_sai", "obv", "khoi_luong", "mau_nen", "heiken", "fibo", "gann_sq9", "goc", "duong_xu_huong",
              "macd", "tuyen_tinh", "tuong_quan", "than_nen", "moc_ky", "dem_lien_tiep", "trang_thai_lat"}


# dieu kien khong co huong (bien dong / luc xu huong / lich): giu NGUYEN khi lat
_TRUNG_TINH = {"adx", "atr", "bien_do", "phuong_sai", "phan_vi", "tb", "tre", "gio", "ngay_trong_tuan", "ngay_trong_thang", "thang", "tuyet_doi"}


def _ten_chi_bao(x) -> set:
    ra = set()
    if isinstance(x, dict):
        if "chi_bao" in x:
            ra.add(x["chi_bao"])
        for v in x.values():
            ra |= _ten_chi_bao(v)
    elif isinstance(x, list):
        for v in x:
            ra |= _ten_chi_bao(v)
    return ra


def _goc(x):
    return x.get("chi_bao") if isinstance(x, dict) else None


def _lat_dk(d: dict):
    t, p = d.get("trai"), d.get("phai")
    if d["phep"] not in _PHEP and d["phep"] not in ("==", "!="):
        return None
    cb = _ten_chi_bao(d)
    if cb and cb <= _TRUNG_TINH:
        return copy.deepcopy(d)
    if d["phep"] not in _PHEP:
        return None
    ct, cp = _goc(t), _goc(p)
    # (chi bao co khoang) vs hang
    if ct in _LAT_HANG and _LAT_HANG[ct] and isinstance(p, dict) and "hang" in p and ct and not _co_khong_lat(t):
        return {"trai": t, "phep": _PHEP[d["phep"]], "phai": {"hang": _LAT_HANG[ct](p["hang"])}}
    # gia / duong vs gia / duong (khong co hang): lat phep + doi ten kenh
    if ct in _AN_TOAN_VE and cp in _AN_TOAN_VE and not _co_khong_lat(t) and not _co_khong_lat(p):
        return {"trai": _doi(t), "phep": _PHEP[d["phep"]], "phai": _doi(p)}
    return None


def _co_khong_lat(x) -> bool:
    if isinstance(x, dict):
        return _goc(x) in _KHONG_LAT or any(_co_khong_lat(v) for v in x.values())
    if isinstance(x, list):
        return any(_co_khong_lat(v) for v in x)
    return False


def _doi(x):
    x = copy.deepcopy(x)
    if isinstance(x, dict) and x.get("chi_bao") in _DOI_TEN:
        x["chi_bao"] = _DOI_TEN[x["chi_bao"]]
        c = x.get("cua")
        if isinstance(c, dict) and c.get("chi_bao") == "gia" and c.get("cot") in ("high", "low"):
            c["cot"] = "low" if c["cot"] == "high" else "high"   # kenh cao -> kenh thap lay cot doi
    return x


def guong(spec: dict) -> dict | None:
    """Tra khai bao BAN tu khai bao MUA (hoac nguoc lai), hoac None neu co dieu kien khong lat duoc an toan."""
    ra = copy.deepcopy(spec)
    for khoa in ("vao", "ra"):
        moi = []
        for d in spec.get(khoa, []):
            m = _lat_dk(d)
            if m is None:
                return None
            moi.append(m)
        ra[khoa] = moi
    ra["chieu"] = -int(spec.get("chieu", 1))
    ten = str(spec.get("ten", "x"))
    ra["ten"] = ten[:-4] + "_ban" if ten.endswith("_mua") else ten + "_guong"
    return ra
