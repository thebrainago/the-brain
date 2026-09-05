# -*- coding: utf-8 -*-
"""ho_so_symbol.py - HO SO TAI SAN: tra loi "co gia thuyet nay thi thu tren cai gi".

Chu du an 05/09/2026: *"Bo test tinh chat symbol cung vo cung quan trong, ta biet
duoc tinh chat va bien do 1 cap. Sau nay co chien luoc hoac gia thuyet nao do ta
co the nghi ngay toi ung vien nao phu hop luon"*.

Mot dong moi symbol, gom BON nhom - va chi bon nhom nay, khong them:

  TINH CACH   hoi quy hay xu huong. `nhan/tinh_cach.py` (Hurst du bao tot nhat,
              r = -0,567 tren 157 ma khi doi chieu voi ket qua that).
  BIEN DO     bien dong nam, ATR% ngay, bien do phien. Quyet dinh **buoc luoi**,
              **TP**, **SL** dat bao nhieu - khong doan duoc neu khong co.
  CHI PHI     spread bps THAT + phi qua dem %/nam + do tin. Quyet dinh **vong
              quay toi da** cho phep: mot he 60 vong/nam tren cap 20 bps thi
              chet truoc khi bat dau.
  LICH SU     so nam, so bar, khung min co san. Quyet dinh **do dai kiem dinh**
              kha thi - va tieu chi `song_du` cua cong ra tien.

## DUNG DE LAM GI

`chon_ung_vien(...)` - dua vao mot YEU CAU (kieu co che, buoc luoi mong muon,
tran chi phi...) tra ve danh sach symbol hop, XEP HANG. Do la ca diem cua module:
khi co mot gia thuyet moi, khong phai quet mu 194 ma nua.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent.parent
KHO_HS = LAB / "config" / "ho_so_symbol.json"


def _bien_do(df) -> dict:
    """Bien do - don vi % gia, de so sanh duoc giua cac tai san khac gia."""
    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    ok = np.isfinite(c) & (c > 0)
    r = np.diff(np.log(c[ok]))
    bar_nam = 252.0
    try:
        from nhan import du_lieu as DL
        bar_nam = float(DL.bar_moi_nam(df.index))
    except Exception:
        pass
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)),
                                      np.abs(l - np.roll(c, 1))))[1:]
    atr_pct = float(np.nanmedian(tr / c[1:]) * 100.0)
    return {
        "bien_dong_nam_pct": float(np.std(r, ddof=1) * np.sqrt(bar_nam) * 100.0),
        "atr_pct_bar": atr_pct,
        "bien_do_bar_pct": float(np.nanmedian((h - l) / c) * 100.0),
        "bar_moi_nam": bar_nam,
        # buoc luoi GOI Y: mot buoc nen om duoc ~1 ATR de khong nap tang lien tuc
        "buoc_goi_y_pct": round(atr_pct, 4),
    }


def mot(ma: str, khung: str = "D1") -> dict | None:
    """Ho so day du cua MOT symbol tren MOT khung."""
    from nhan import chi_phi as CP
    from nhan import du_lieu as DL
    from nhan import tinh_cach as TC
    try:
        df = DL.nap(ma, khung)
        if DL.nguon_tai_san(ma) == "ngoai":
            df = DL.cat_theo_chat_luong(df, ma)[0]
        if len(df) < 400:
            return None
        # Khong phai bang nao cung co du OHLC - vai bang trong kho chi co
        # `close`, vai bang doi ten cot. Kiem TRUOC khi tinh, va bo qua yen
        # lang thay vi nem loi lam chet ca tien trinh con (da sap 05/09).
        if "close" not in df.columns:
            return None
        h = TC.ho_so(df["close"].to_numpy(float))
        h["nhan_tinh_cach"] = TC.nhan(h)
        if {"open", "high", "low"} <= set(df.columns):
            h.update(_bien_do(df))
    except Exception:
        return None
    try:
        cp = CP.tu_du_lieu(ma, df)
        cp = cp[0] if isinstance(cp, tuple) else cp
        h.update({"spread_bps": round(cp.spread_frac_chung * 1e4, 4),
                  "phi_nam_mua_pct": round(cp.phi_nam_mua * 100, 4),
                  "phi_nam_ban_pct": round(cp.phi_nam_ban * 100, 4),
                  "chi_phi_do_tin": cp.do_tin})
    except Exception:
        h.update({"spread_bps": None, "chi_phi_do_tin": None})
    h.update({
        "ma": ma, "khung": khung, "so_bar": len(df),
        "so_nam": round((df.index[-1] - df.index[0]).days / 365.25, 2),
        "tu": str(df.index[0].date()), "den": str(df.index[-1].date()),
        "nguon": DL.nguon_tai_san(ma),
    })
    # VONG QUAY TOI DA cho phep: chi phi mot vong = 2 x spread. Neu chap nhan
    # phi an toi 30% lai tho va lai tho/lenh ~30 bps (MDE do duoc cua pheu) thi
    # so vong/nam toi da = 0,30 * 30 / (2 * spread_bps) * so_lenh... quy ve don
    # gian: bao nhieu vong thi phi cham 10%/nam.
    sp = h.get("spread_bps")
    h["vong_quay_toi_da"] = (round(10.0 / (2.0 * sp / 100.0), 1)
                             if sp and sp > 0 else None)
    return h


def quet(cac_ma=None, khung: str = "D1", luong: int = 10, in_ra=print) -> list[dict]:
    """Ho so cho toan bo kho. Ghi cache vao `config/ho_so_symbol.json`."""
    from concurrent.futures import ProcessPoolExecutor, as_completed

    from nhan import du_lieu as DL
    mas = list(cac_ma or sorted(DL.kho()))
    ra = []
    with ProcessPoolExecutor(max_workers=luong) as ex:
        fu = {ex.submit(mot, m, khung): m for m in mas}
        for f in as_completed(fu):
            r = f.result()
            if r:
                ra.append(r)
    ra.sort(key=lambda x: x["ma"])
    KHO_HS.parent.mkdir(parents=True, exist_ok=True)
    KHO_HS.write_text(json.dumps({"do_luc": time.strftime("%Y-%m-%d %H:%M:%S"),
                                  "khung": khung, "ho_so": ra},
                                 ensure_ascii=False, indent=1), encoding="utf-8")
    in_ra("ho so %d/%d symbol -> %s" % (len(ra), len(mas), KHO_HS))
    return ra


def doc() -> list[dict]:
    try:
        return json.loads(KHO_HS.read_text(encoding="utf-8"))["ho_so"]
    except Exception:
        return []


#: Tran spread mac dinh, bps. Ban dau ham nay xep hang THUAN theo Hurst va no
#: day GBPPLN (98,5 bps) va GBPZAR (20,8 bps) len dau - nhung cap ma phi giet
#: moi luoi truoc khi co che kip chay. Tinh cach ma khong tra noi phi thi vo
#: dung, nen phai loc chi phi TRUOC roi moi xep theo tinh cach.
#: 8 bps = khoang gap 8 lan spread chi so CFD do that (0,94-1,04 bps).
TRAN_SPREAD_BPS = 8.0


def chon_ung_vien(kieu: str = "hoi_quy", so_nam_min: float = 8.0,
                  spread_toi_da: float | None = TRAN_SPREAD_BPS,
                  chi_phi_do_duoc: bool = True, tran: int = 15,
                  vong_quay_can: float | None = None,
                  ho_so: list[dict] | None = None) -> list[dict]:
    """Co mot gia thuyet -> nen thu tren nhung symbol nao.

    `kieu`: `hoi_quy` | `xu_huong` | `bat_ky`.
    `vong_quay_can`: he se quay bao nhieu vong/nam. Neu dat, loai symbol co
    `vong_quay_toi_da` thap hon - tuc phi se an qua 10%/nam.

    Loc CHI PHI truoc, roi moi xep theo do manh tinh cach.
    """
    hs = ho_so if ho_so is not None else doc()
    ra = []
    for h in hs:
        if h.get("so_nam", 0) < so_nam_min:
            continue
        if chi_phi_do_duoc and h.get("chi_phi_do_tin") not in ("DO", "SAN"):
            continue
        if spread_toi_da is not None:
            sp = h.get("spread_bps")
            if sp is None or sp > spread_toi_da:
                continue
        if vong_quay_can is not None:
            vq = h.get("vong_quay_toi_da")
            if vq is None or vq < vong_quay_can:
                continue
        if kieu != "bat_ky" and h.get("nhan_tinh_cach") != kieu.upper():
            continue
        ra.append(h)
    dao = kieu == "xu_huong"
    ra.sort(key=lambda h: (h.get("hurst") or 0.5), reverse=dao)
    return ra[:tran]
